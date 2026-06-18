"""
Engine hardening regression tests.

Verifies that:
- Unknown uplift condition types are NOT applied (default False safety rule)
- Georgia logo uplift fires ONLY when production_details explicitly satisfies the condition
- Resident labor uplift fires ONLY when resident_labor_pct condition is satisfied
- No jurisdiction silently gains an uplift from bare production_details={}
"""
from __future__ import annotations

import pytest
from app.calculators.calculate_incentive_value import (
    calculate_incentive_value,
    _evaluate_uplift_condition,
)


# ---------------------------------------------------------------------------
# _evaluate_uplift_condition unit tests
# ---------------------------------------------------------------------------

def test_unknown_condition_type_returns_false():
    """SAFETY: Any condition type not in the allowlist must return False."""
    result = _evaluate_uplift_condition(
        condition_type="future_unknown_rule",
        condition_threshold=None,
        condition_text="",
        production_details={"future_unknown_rule": True, "everything": True},
    )
    assert result is False, "Unknown condition types must never activate an uplift"


def test_empty_condition_type_is_unconditional():
    result = _evaluate_uplift_condition(
        condition_type="",
        condition_threshold=None,
        condition_text="",
        production_details={},
    )
    assert result is True


def test_none_condition_type_is_unconditional():
    result = _evaluate_uplift_condition(
        condition_type=None,
        condition_threshold=None,
        condition_text="",
        production_details={},
    )
    assert result is True


def test_always_condition_is_unconditional():
    result = _evaluate_uplift_condition(
        condition_type="always",
        condition_threshold=None,
        condition_text="",
        production_details={},
    )
    assert result is True


def test_unconditional_condition_type():
    result = _evaluate_uplift_condition(
        condition_type="unconditional",
        condition_threshold=None,
        condition_text="",
        production_details={},
    )
    assert result is True


def test_georgia_logo_displayed_key_fires():
    result = _evaluate_uplift_condition(
        condition_type="georgia_logo_displayed",
        condition_threshold=None,
        condition_text="",
        production_details={"georgia_logo_displayed": True},
    )
    assert result is True


def test_uses_logo_key_fires():
    result = _evaluate_uplift_condition(
        condition_type="uses_logo",
        condition_threshold=None,
        condition_text="",
        production_details={"uses_georgia_logo": True},
    )
    assert result is True


def test_georgia_logo_does_not_fire_without_production_details():
    result = _evaluate_uplift_condition(
        condition_type="georgia_logo_displayed",
        condition_threshold=None,
        condition_text="",
        production_details={},
    )
    assert result is False


def test_georgia_logo_does_not_fire_with_false():
    result = _evaluate_uplift_condition(
        condition_type="georgia_logo_displayed",
        condition_threshold=None,
        condition_text="",
        production_details={"georgia_logo_displayed": False},
    )
    assert result is False


def test_resident_labor_pct_fires_at_threshold():
    result = _evaluate_uplift_condition(
        condition_type="resident_labor_pct",
        condition_threshold=0.50,
        condition_text="",
        production_details={"resident_labor_pct": 0.60},
    )
    assert result is True


def test_resident_labor_pct_fails_below_threshold():
    result = _evaluate_uplift_condition(
        condition_type="resident_labor_pct",
        condition_threshold=0.50,
        condition_text="",
        production_details={"resident_labor_pct": 0.40},
    )
    assert result is False


def test_resident_labor_pct_fails_empty_details():
    result = _evaluate_uplift_condition(
        condition_type="resident_labor_pct",
        condition_threshold=0.50,
        condition_text="",
        production_details={},
    )
    assert result is False


def test_shooting_location_fires_on_match():
    result = _evaluate_uplift_condition(
        condition_type="shooting_location",
        condition_threshold=None,
        condition_text="upstate_ny",
        production_details={"shooting_location": "upstate_ny"},
    )
    assert result is True


def test_shooting_location_fails_mismatch():
    result = _evaluate_uplift_condition(
        condition_type="shooting_location",
        condition_threshold=None,
        condition_text="upstate_ny",
        production_details={"shooting_location": "nyc"},
    )
    assert result is False


def test_budget_under_fires_when_under():
    result = _evaluate_uplift_condition(
        condition_type="budget_under",
        condition_threshold=10_000_000,
        condition_text="",
        production_details={"total_budget_usd": 5_000_000},
    )
    assert result is True


def test_budget_under_fails_when_over():
    result = _evaluate_uplift_condition(
        condition_type="budget_under",
        condition_threshold=10_000_000,
        condition_text="",
        production_details={"total_budget_usd": 15_000_000},
    )
    assert result is False


def test_budget_under_fails_when_budget_unknown():
    """Missing total_budget_usd must NOT activate budget_under condition."""
    result = _evaluate_uplift_condition(
        condition_type="budget_under",
        condition_threshold=10_000_000,
        condition_text="",
        production_details={},
    )
    assert result is False


def test_is_independent_fires():
    result = _evaluate_uplift_condition(
        condition_type="is_independent",
        condition_threshold=None,
        condition_text="",
        production_details={"is_independent_film": True},
    )
    assert result is True


def test_is_independent_fails_without_flag():
    result = _evaluate_uplift_condition(
        condition_type="is_independent",
        condition_threshold=None,
        condition_text="",
        production_details={},
    )
    assert result is False


# ---------------------------------------------------------------------------
# calculate_incentive_value integration-level tests
# ---------------------------------------------------------------------------

GEORGIA_PROGRAM = {
    "id": "prog-ga-test",
    "slug": "georgia_eiia",
    "program_type": "tax_credit",
    "base_rate": 0.20,
    "is_refundable": False,
    "is_transferable": True,
    "transferable_value_pct": 0.90,
    "is_competitive": False,
}

GEORGIA_LOGO_UPLIFT = {
    "id": "uplift-ga-logo",
    "name": "Georgia Logo Uplift",
    "additional_rate": 0.10,
    "applies_to": "same_qualifying_spend",
    "condition_type": "georgia_logo_displayed",
    "condition_threshold": None,
    "condition_text": "",
}

UNKNOWN_UPLIFT = {
    "id": "uplift-unknown",
    "name": "Unknown Future Uplift",
    "additional_rate": 0.15,
    "applies_to": "same_qualifying_spend",
    "condition_type": "some_future_unimplemented_condition",
    "condition_threshold": None,
    "condition_text": "",
}


def test_unknown_uplift_does_not_apply():
    """Unknown condition types must not silently inflate the credit."""
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=[UNKNOWN_UPLIFT],
        production_details={"some_future_unimplemented_condition": True},
    )
    assert result.uplifts_applied == [], "Unknown condition must not apply uplift"
    assert result.total_credit_usd == pytest.approx(200_000.0)


def test_georgia_logo_uplift_applies_with_production_details():
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=[GEORGIA_LOGO_UPLIFT],
        production_details={"georgia_logo_displayed": True},
    )
    assert len(result.uplifts_applied) == 1
    assert result.total_credit_usd == pytest.approx(300_000.0)  # 20% + 10%


def test_georgia_logo_uplift_does_not_apply_without_production_details():
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=[GEORGIA_LOGO_UPLIFT],
        production_details={},
    )
    assert result.uplifts_applied == [], "Logo uplift must not fire without explicit production_details"
    assert result.total_credit_usd == pytest.approx(200_000.0)


def test_georgia_logo_uplift_does_not_apply_with_none_production_details():
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=[GEORGIA_LOGO_UPLIFT],
        production_details=None,
    )
    assert result.uplifts_applied == []
    assert result.total_credit_usd == pytest.approx(200_000.0)


def test_vfx_uplift_uses_vfx_spend_basis():
    vfx_uplift = {
        "id": "uplift-vfx",
        "name": "VFX Uplift",
        "additional_rate": 0.05,
        "applies_to": "vfx_spend_only",
        "condition_type": "",
        "condition_threshold": None,
        "condition_text": "",
    }
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=[vfx_uplift],
        production_details={},
        vfx_spend_usd=200_000,
    )
    # base: 1,000,000 * 0.20 = 200,000; vfx uplift: 200,000 * 0.05 = 10,000
    assert result.uplifts_applied[0]["credit_usd"] == pytest.approx(10_000.0)
    assert result.total_credit_usd == pytest.approx(210_000.0)


def test_vfx_uplift_zero_without_vfx_spend():
    vfx_uplift = {
        "id": "uplift-vfx",
        "name": "VFX Uplift",
        "additional_rate": 0.05,
        "applies_to": "vfx_spend_only",
        "condition_type": "",
        "condition_threshold": None,
        "condition_text": "",
    }
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=[vfx_uplift],
        production_details={},
        vfx_spend_usd=0.0,
    )
    assert result.uplifts_applied[0]["credit_usd"] == pytest.approx(0.0)
    assert result.total_credit_usd == pytest.approx(200_000.0)


def test_resident_labor_uplift_uses_resident_labor_basis():
    resident_uplift = {
        "id": "uplift-res",
        "name": "Resident Labor Uplift",
        "additional_rate": 0.10,
        "applies_to": "resident_labor_only",
        "condition_type": "resident_labor_pct",
        "condition_threshold": 0.50,
        "condition_text": "",
    }
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=[resident_uplift],
        production_details={"resident_labor_pct": 0.60},
        resident_labor_usd=300_000,
    )
    # base: 200,000; resident uplift: 300,000 * 0.10 = 30,000
    assert result.uplifts_applied[0]["credit_usd"] == pytest.approx(30_000.0)
    assert result.total_credit_usd == pytest.approx(230_000.0)


def test_resident_labor_uplift_does_not_apply_below_pct_threshold():
    resident_uplift = {
        "id": "uplift-res",
        "name": "Resident Labor Uplift",
        "additional_rate": 0.10,
        "applies_to": "resident_labor_only",
        "condition_type": "resident_labor_pct",
        "condition_threshold": 0.50,
        "condition_text": "",
    }
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=[resident_uplift],
        production_details={"resident_labor_pct": 0.30},
        resident_labor_usd=300_000,
    )
    assert result.uplifts_applied == []
    assert result.total_credit_usd == pytest.approx(200_000.0)


def test_no_silent_uplifts_empty_production_details():
    """Any conditional uplift must produce zero extra credit when production_details={}."""
    conditional_uplifts = [
        GEORGIA_LOGO_UPLIFT,
        {
            "id": "uplift-loc",
            "name": "Upstate Uplift",
            "additional_rate": 0.10,
            "applies_to": "same_qualifying_spend",
            "condition_type": "shooting_location",
            "condition_threshold": None,
            "condition_text": "upstate_ny",
        },
        {
            "id": "uplift-ind",
            "name": "Independent Uplift",
            "additional_rate": 0.05,
            "applies_to": "same_qualifying_spend",
            "condition_type": "is_independent",
            "condition_threshold": None,
            "condition_text": "",
        },
    ]
    result = calculate_incentive_value(
        qualifying_spend_usd=1_000_000,
        program=GEORGIA_PROGRAM,
        uplifts=conditional_uplifts,
        production_details={},
    )
    assert result.uplifts_applied == [], (
        "No conditional uplift should fire when production_details is empty"
    )
    assert result.total_credit_usd == pytest.approx(200_000.0)
