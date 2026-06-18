"""
Unit tests: individual calculator modules.
Deterministic — no DB, no LLM.
"""
import pytest

from app.calculators.apply_caps_floors_exclusions import apply_caps_and_exclusions
from app.calculators.apply_fx_rates import convert_to_usd, convert_usd_to_local
from app.calculators.calculate_incentive_value import calculate_incentive_value
from app.calculators.calculate_net_budget import calculate_net_budget
from app.calculators.calculate_qualified_spend import calculate_qualified_spend
from app.calculators.calculate_risk_adjusted_net_budget import calculate_risk_adjusted_net
from app.calculators.evaluate_legal_stacking import evaluate_legal_stacking
from app.models.enums import StackingRuleType


# ---------------------------------------------------------------------------
# FX rates
# ---------------------------------------------------------------------------
def test_convert_cad_to_usd():
    fx = {"CAD": 1.36}
    result = convert_to_usd(136_000, "CAD", fx)
    assert abs(result.target_amount - 100_000) < 1.0


def test_usd_passthrough():
    fx = {"CAD": 1.36}
    result = convert_to_usd(100_000, "USD", fx)
    assert result.target_amount == 100_000


def test_convert_usd_to_local():
    fx = {"CAD": 1.36}
    result = convert_usd_to_local(100_000, "CAD", fx)
    assert abs(result.target_amount - 136_000) < 1.0


# ---------------------------------------------------------------------------
# Qualified spend
# ---------------------------------------------------------------------------
def _btl_items():
    return [
        {"description": "Crew labor", "spend_category": "btl_crew_labor",
         "atl_btl": "BTL", "amount_usd": 500_000, "is_fixed": False},
        {"description": "Equipment Rental", "spend_category": "btl_equipment_rental",
         "atl_btl": "BTL", "amount_usd": 100_000, "is_fixed": False},
        {"description": "Insurance", "spend_category": "insurance",
         "atl_btl": "OTHER", "amount_usd": 50_000, "is_fixed": False},
    ]


_QS_CATEGORIES = [
    {"spend_category": "btl_crew_labor", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "insurance", "qualifies": False, "jurisdiction_spend_only": False},
]


def test_qualified_spend_excludes_non_qualifying():
    result = calculate_qualified_spend(
        line_items=_btl_items(),
        qualifying_categories=_QS_CATEGORIES,
        jurisdiction_spend_pct=1.0,
        program_id="prog-test",
        program_slug="test_program",
    )
    assert result.total_qualifying_usd == 600_000
    assert "insurance" in result.excluded_categories


def test_qualified_spend_applies_jurisdiction_pct():
    result = calculate_qualified_spend(
        line_items=_btl_items(),
        qualifying_categories=_QS_CATEGORIES,
        jurisdiction_spend_pct=0.75,
        program_id="prog-test",
        program_slug="test_program",
    )
    assert result.total_qualifying_usd == pytest.approx(450_000)


def test_qualified_spend_cap():
    # Crew labor = $900K; cap = 80% of $1M = $800K → cap triggers
    items = [
        {"description": "Crew labor", "spend_category": "btl_crew_labor",
         "amount_usd": 900_000, "atl_btl": "BTL"},
    ]
    cats = [{"spend_category": "btl_crew_labor", "qualifies": True, "jurisdiction_spend_only": False}]
    result = calculate_qualified_spend(
        line_items=items,
        qualifying_categories=cats,
        jurisdiction_spend_pct=1.0,
        program_id="prog-test",
        program_slug="test",
        spend_cap_pct=0.80,
        total_budget_usd=1_000_000,
    )
    assert result.cap_applied is True
    assert result.total_qualifying_capped_usd == pytest.approx(800_000)  # 80% of 1M


# ---------------------------------------------------------------------------
# Caps and exclusions
# ---------------------------------------------------------------------------
def test_atl_cap_reduces_qualifying_spend():
    result = apply_caps_and_exclusions(
        qualifying_spend_usd=1_000_000,
        total_budget_usd=2_000_000,
        atl_spend_usd=700_000,
        atl_cap_pct=0.25,
    )
    # ATL cap = 25% of 2M = $500K; ATL is $700K → excess $200K removed
    assert result.adjusted_qualifying_spend_usd == pytest.approx(800_000)
    assert len(result.adjustments) == 1


def test_no_cap_passthrough():
    result = apply_caps_and_exclusions(
        qualifying_spend_usd=500_000,
        total_budget_usd=2_000_000,
        atl_spend_usd=200_000,
    )
    assert result.adjusted_qualifying_spend_usd == 500_000
    assert result.adjustments == []


# ---------------------------------------------------------------------------
# Incentive value
# ---------------------------------------------------------------------------
def _basic_program(base_rate: float = 0.20, is_refundable: bool = True):
    return {
        "id": "prog-test",
        "slug": "test_program",
        "program_type": "tax_credit",
        "base_rate": base_rate,
        "is_refundable": is_refundable,
        "is_transferable": False,
        "transferable_value_pct": None,
        "is_competitive": False,
    }


def test_basic_incentive_value():
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=_basic_program(0.20),
        uplifts=[],
    )
    assert result.base_credit_usd == pytest.approx(200_000)
    assert result.economic_value_usd == pytest.approx(200_000)


def test_non_refundable_transferable_discount():
    prog = {**_basic_program(0.20, is_refundable=False), "is_transferable": True, "transferable_value_pct": 0.90}
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=prog,
        uplifts=[],
    )
    assert result.economic_value_usd == pytest.approx(180_000)


def test_uplift_adds_to_credit():
    uplift = {
        "name": "Logo Uplift",
        "additional_rate": 0.10,
        "applies_to": "same_qualifying_spend",
        "condition_type": "uses_logo",
        "condition_threshold": None,
        "condition_text": "",
    }
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=_basic_program(0.20),
        uplifts=[uplift],
        production_details={"uses_georgia_logo": True},
    )
    assert result.total_credit_usd == pytest.approx(300_000)


# ---------------------------------------------------------------------------
# Net budget
# ---------------------------------------------------------------------------
def test_net_budget_no_benchmark():
    result = calculate_net_budget(
        fixed_atl_usd=500_000,
        variable_btl_usd=1_000_000,
        cost_benchmark=None,
        travel_cost_usd=0,
        total_incentive_economic_value_usd=200_000,
    )
    assert result.true_net_cost_usd == pytest.approx(1_300_000)


def test_net_budget_with_benchmark():
    # benchmark multiplier 0.85 = 15% cheaper than LA
    benchmark = {"crew_labor_multiplier": 0.85, "equipment_multiplier": 0.90}
    result = calculate_net_budget(
        fixed_atl_usd=500_000,
        variable_btl_usd=1_000_000,
        cost_benchmark=benchmark,
        travel_cost_usd=0,
        total_incentive_economic_value_usd=200_000,
    )
    avg = (0.85 + 0.90) / 2  # 0.875
    expected_btl = 1_000_000 * avg
    assert result.rebase_btl_usd == pytest.approx(expected_btl)


def test_net_budget_never_negative():
    result = calculate_net_budget(
        fixed_atl_usd=100_000,
        variable_btl_usd=200_000,
        cost_benchmark=None,
        travel_cost_usd=0,
        total_incentive_economic_value_usd=500_000,  # larger than total budget
    )
    assert result.true_net_cost_usd == 0.0


# ---------------------------------------------------------------------------
# Risk-adjusted net
# ---------------------------------------------------------------------------
def test_risk_discovery_adds_25pct():
    programs = [{"program_slug": "test", "total_credit_usd": 200_000,
                 "confidence_tier": "DISCOVERY", "is_competitive": False}]
    result = calculate_risk_adjusted_net(
        true_net_cost_usd=800_000,
        total_incentive_value_usd=200_000,
        program_results=programs,
    )
    # 25% of $200K = $50K added to net
    assert result.risk_adjusted_net_cost_usd == pytest.approx(850_000)


def test_risk_verified_no_discount():
    programs = [{"program_slug": "test", "total_credit_usd": 200_000,
                 "confidence_tier": "VERIFIED", "is_competitive": False}]
    result = calculate_risk_adjusted_net(
        true_net_cost_usd=800_000,
        total_incentive_value_usd=200_000,
        program_results=programs,
    )
    assert result.risk_adjusted_net_cost_usd == pytest.approx(800_000)
    assert result.overall_risk_level == "low"


# ---------------------------------------------------------------------------
# Legal stacking
# ---------------------------------------------------------------------------
def test_stacking_prohibited_flagged():
    rules = [{
        "program_a_id": "prog-a",
        "program_b_id": "prog-b",
        "rule_type": "prohibited",
        "condition_text": None,
        "statutory_reference": None,
        "confidence_tier": "DISCOVERY",
        "notes": None,
    }]
    result = evaluate_legal_stacking(["prog-a", "prog-b"], rules)
    assert result.legal_review_required is True
    assert len(result.violations) == 1


def test_stacking_allowed_no_violation():
    rules = [{
        "program_a_id": "prog-a",
        "program_b_id": "prog-b",
        "rule_type": "allowed",
        "condition_text": None,
        "statutory_reference": None,
        "confidence_tier": "DISCOVERY",
        "notes": None,
    }]
    result = evaluate_legal_stacking(["prog-a", "prog-b"], rules)
    assert result.legal_review_required is False
    assert result.violations == []


def test_stacking_not_applicable_when_one_program():
    rules = [{
        "program_a_id": "prog-a",
        "program_b_id": "prog-b",
        "rule_type": "PROHIBITED",
        "condition_text": None,
        "statutory_reference": None,
        "confidence_tier": "DISCOVERY",
        "notes": None,
    }]
    # Only claiming prog-a, not prog-b — rule doesn't trigger
    result = evaluate_legal_stacking(["prog-a"], rules)
    assert result.violations == []
