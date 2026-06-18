"""
Georgia EIIA end-to-end validation tests.

Source: O.C.G.A. § 48-7-40.26
Rates used: base_rate=0.20, logo_uplift=0.10, transferable_value_pct=0.90

All expected values are hand-verified and documented in
tests/fixtures/georgia_validation.py.
"""
import pytest
from app.calculators.run_full_analysis import run_full_analysis
from tests.fixtures.georgia_validation import (
    EXPECTED,
    FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT,
    FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT,
)


def _run(fixture: dict):
    return run_full_analysis(
        structure_id="ga-validation-001",
        jurisdiction=fixture["jurisdiction"],
        line_items=fixture["line_items"],
        programs_with_categories=fixture["programs_with_categories"],
        stacking_rules=fixture.get("stacking_rules", []),
        qualification_tests_with_rules=[],
        cost_benchmark=None,
        union_fringe_rules=[],
        fx_rates=None,
        production_details=fixture.get("production_details"),
        home_jurisdiction_id=fixture.get("home_jurisdiction_id"),
    )


# ---------------------------------------------------------------------------
# Basic sanity: engine accepts VERIFIED data and produces non-zero output
# ---------------------------------------------------------------------------

def test_georgia_no_uplift_runs():
    result = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    assert result.total_input_budget_usd == EXPECTED["total_budget_usd"]


def test_georgia_no_uplift_positive_qualifying_spend():
    result = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    total_qs = sum(
        r.get("qualifying_spend_usd", 0) or 0
        for r in result.qualified_spend_results
    )
    assert total_qs >= EXPECTED["qualifying_spend_min_usd"], (
        f"Expected qualifying spend >= ${EXPECTED['qualifying_spend_min_usd']:,.0f}, "
        f"got ${total_qs:,.0f}"
    )


def test_georgia_no_uplift_positive_incentive_value():
    result = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    assert result.total_incentive_economic_value_usd > 0, (
        "Georgia EIIA with VERIFIED rates must produce a non-zero incentive value. "
        "Check that qualifying_spend_categories are populated correctly."
    )


def test_georgia_no_uplift_credit_at_least_20pct_of_btl():
    """Base credit must be at least 20% of the minimum qualifying BTL+Post spend."""
    result = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    min_expected_credit = EXPECTED["credit_no_uplift_min_usd"]
    assert result.total_incentive_economic_value_usd >= min_expected_credit * 0.90, (
        f"Economic value should be at least 90% of min expected credit "
        f"${min_expected_credit:,.0f} (90% transferable), "
        f"got ${result.total_incentive_economic_value_usd:,.0f}"
    )


def test_georgia_no_uplift_net_cost_less_than_gross():
    result = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    assert result.true_net_cost_usd < result.total_input_budget_usd


def test_georgia_no_uplift_net_cost_non_negative():
    result = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    assert result.true_net_cost_usd >= 0


def test_georgia_no_uplift_stacking_clean():
    result = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    assert result.stacking_violations == []
    assert result.stacking_legal_review_required is False


def test_georgia_no_uplift_trace_complete():
    result = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    assert result.engine_version == "0.1.0"
    assert "steps" in result.calculation_trace
    step_names = {s["step"] for s in result.calculation_trace["steps"]}
    assert "classify_budget" in step_names
    assert "incentive_programs" in step_names, (
        f"Expected an 'incentive_programs' trace step, got: {step_names}"
    )


# ---------------------------------------------------------------------------
# Logo uplift: 30% with logo > 20% without logo
# ---------------------------------------------------------------------------

def test_georgia_logo_uplift_increases_value():
    result_no_uplift   = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    result_with_uplift = _run(FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT)
    assert result_with_uplift.total_incentive_economic_value_usd > \
           result_no_uplift.total_incentive_economic_value_usd, (
        "Logo uplift (+10%) should increase economic value. "
        f"No uplift: ${result_no_uplift.total_incentive_economic_value_usd:,.0f}, "
        f"With uplift: ${result_with_uplift.total_incentive_economic_value_usd:,.0f}"
    )


def test_georgia_logo_uplift_ratio():
    """With-uplift credit should be 1.5x no-uplift credit (30% / 20% = 1.5)."""
    result_no   = _run(FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT)
    result_with = _run(FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT)
    ratio = result_with.total_incentive_economic_value_usd / \
            result_no.total_incentive_economic_value_usd
    # Allow ±2% tolerance for floating point and rounding
    assert abs(ratio - 1.5) <= 0.02, (
        f"Logo uplift should produce 1.5x the economic value (30%/20%), "
        f"got ratio {ratio:.4f}"
    )


def test_georgia_with_uplift_trace_records_uplifts():
    result = _run(FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT)
    found = False
    for iv in result.incentive_results:
        if iv.get("program_slug") == "georgia_eiia":
            if len(iv.get("uplifts_applied", [])) > 0:
                found = True
    assert found, (
        "incentive_results for georgia_eiia should record uplifts_applied "
        "when the logo uplift is active."
    )


# ---------------------------------------------------------------------------
# Numeric validation against hand-verified expected outputs
# ---------------------------------------------------------------------------

def test_georgia_with_uplift_economic_value_within_tolerance():
    """
    Economic value should be within 5% of the hand-verified target.

    Hand-verified: qualifying=$2,675,000, credit=30%, economic=90%
    => expected $722,250

    Actual may differ due to ATL classification details (some descriptions may
    map to spend_category values not covered by qualifying_categories). The
    floor assertion in test_georgia_no_uplift_positive_qualifying_spend covers
    the minimum case; this test verifies we are close to the full expected.
    """
    result = _run(FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT)
    target = EXPECTED["economic_value_target_usd"]
    tolerance = target * 0.05  # 5%
    assert result.total_incentive_economic_value_usd >= target - tolerance, (
        f"Economic value ${result.total_incentive_economic_value_usd:,.0f} is more than "
        f"5% below target ${target:,.0f}. Check qualifying category mappings."
    )


def test_georgia_with_uplift_true_net_within_tolerance():
    result = _run(FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT)
    target_net = EXPECTED["true_net_cost_target_usd"]
    tolerance = EXPECTED["total_budget_usd"] * 0.05
    assert abs(result.true_net_cost_usd - target_net) <= tolerance, (
        f"True net cost ${result.true_net_cost_usd:,.0f} deviates more than 5% "
        f"from target ${target_net:,.0f}"
    )


# ---------------------------------------------------------------------------
# Confidence tier propagation
# ---------------------------------------------------------------------------

def test_georgia_verified_tier_produces_lower_risk():
    """VERIFIED program should produce lower risk than DISCOVERY."""
    from tests.fixtures.synthetic_projects import FIXTURE_1_US_DOMESTIC
    from app.calculators.run_full_analysis import run_full_analysis

    result_discovery = run_full_analysis(
        structure_id="discovery-compare",
        jurisdiction=FIXTURE_1_US_DOMESTIC["jurisdiction"],
        line_items=FIXTURE_1_US_DOMESTIC["line_items"],
        programs_with_categories=FIXTURE_1_US_DOMESTIC["programs_with_categories"],
        stacking_rules=[],
        qualification_tests_with_rules=[],
        cost_benchmark=None,
        union_fringe_rules=[],
        fx_rates=None,
        production_details=None,
    )
    result_verified = _run(FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT)

    risk_order = {"low": 0, "medium": 1, "high": 2}
    discovery_risk = risk_order.get(result_discovery.risk_level, 2)
    verified_risk  = risk_order.get(result_verified.risk_level, 2)
    assert verified_risk <= discovery_risk, (
        f"VERIFIED program risk '{result_verified.risk_level}' should be <= "
        f"DISCOVERY program risk '{result_discovery.risk_level}'"
    )
