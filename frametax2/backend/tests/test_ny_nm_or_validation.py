"""
NY, NM, and Oregon end-to-end validation tests.

Sources:
  NY: NY Tax Law § 24 (PARSED)
  NM: NMSA 1978 § 7-2F-1 (PARSED)
  OR: ORS § 284.368 / Oregon OPIF (PARSED)

Hand-verified expected values documented in tests/fixtures/ny_nm_or_validation.py.
"""
import pytest
from app.calculators.run_full_analysis import run_full_analysis
from tests.fixtures.ny_nm_or_validation import (
    FIXTURE_NM,
    FIXTURE_NY_NYC,
    FIXTURE_NY_UPSTATE,
    FIXTURE_OR,
    NM_EXPECTED,
    NY_EXPECTED_NYC,
    NY_EXPECTED_UPSTATE,
    OR_EXPECTED,
)


def _run(fixture: dict):
    return run_full_analysis(
        structure_id="validation-ny-nm-or",
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


def _qs(result) -> float:
    return sum(r.get("qualifying_spend_usd", 0) or 0
               for r in result.qualified_spend_results)


# ===========================================================================
# NEW YORK — NYC area (base 25%)
# ===========================================================================

def test_ny_nyc_runs():
    result = _run(FIXTURE_NY_NYC)
    assert result.total_input_budget_usd == NY_EXPECTED_NYC["total_budget_usd"]


def test_ny_nyc_atl_excluded_from_qualifying_spend():
    """Directors and cast do NOT qualify for NY credit — ATL should show zero qualifying."""
    result = _run(FIXTURE_NY_NYC)
    for qs in result.qualified_spend_results:
        breakdown = qs.get("category_breakdown", {})
        assert "atl_director" not in breakdown, (
            "atl_director should be EXCLUDED from NY qualifying spend per Tax Law § 24"
        )
        assert "atl_cast" not in breakdown, (
            "atl_cast should be EXCLUDED from NY qualifying spend per Tax Law § 24"
        )


def test_ny_nyc_qualifying_spend_is_btl_only():
    result = _run(FIXTURE_NY_NYC)
    qs = _qs(result)
    assert qs == NY_EXPECTED_NYC["qualifying_spend_usd"], (
        f"NY qualifying spend should be BTL+Post only: "
        f"expected ${NY_EXPECTED_NYC['qualifying_spend_usd']:,.0f}, got ${qs:,.0f}"
    )


def test_ny_nyc_positive_incentive_value():
    result = _run(FIXTURE_NY_NYC)
    assert result.total_incentive_economic_value_usd > 0


def test_ny_nyc_economic_value_exact():
    result = _run(FIXTURE_NY_NYC)
    expected = NY_EXPECTED_NYC["economic_value_usd"]
    assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.01, (
        f"NY NYC credit: expected ${expected:,.0f}, "
        f"got ${result.total_incentive_economic_value_usd:,.0f}"
    )


def test_ny_nyc_net_cost_decreases():
    result = _run(FIXTURE_NY_NYC)
    assert result.true_net_cost_usd < result.total_input_budget_usd


def test_ny_nyc_net_cost_exact():
    result = _run(FIXTURE_NY_NYC)
    expected = NY_EXPECTED_NYC["true_net_cost_usd"]
    assert abs(result.true_net_cost_usd - expected) <= expected * 0.02, (
        f"NY true net cost: expected ${expected:,.0f}, "
        f"got ${result.true_net_cost_usd:,.0f}"
    )


def test_ny_nyc_confidence_tier_is_parsed():
    """No DISCOVERY-tier program should appear — NY is promoted to PARSED."""
    from tests.fixtures.ny_nm_or_validation import NY_PROGRAM
    assert NY_PROGRAM["confidence_tier"] == "PARSED"
    assert NY_PROGRAM["confidence_tier"] != "DISCOVERY"


def test_ny_nyc_trace_populated():
    result = _run(FIXTURE_NY_NYC)
    assert result.engine_version == "0.1.0"
    assert len(result.calculation_trace.get("steps", [])) > 0
    step_names = {s["step"] for s in result.calculation_trace["steps"]}
    assert "classify_budget" in step_names
    assert "incentive_programs" in step_names


def test_ny_nyc_stacking_clean():
    result = _run(FIXTURE_NY_NYC)
    assert result.stacking_violations == []


# ===========================================================================
# NEW YORK — Upstate (+10% uplift = 35% total)
# ===========================================================================

def test_ny_upstate_higher_than_nyc():
    result_nyc    = _run(FIXTURE_NY_NYC)
    result_upstate = _run(FIXTURE_NY_UPSTATE)
    assert result_upstate.total_incentive_economic_value_usd > \
           result_nyc.total_incentive_economic_value_usd, (
        "Upstate production (35%) must produce higher economic value than NYC (25%)"
    )


def test_ny_upstate_ratio_is_1_4x():
    """35%/25% = 1.4x economic value ratio."""
    result_nyc    = _run(FIXTURE_NY_NYC)
    result_upstate = _run(FIXTURE_NY_UPSTATE)
    ratio = (result_upstate.total_incentive_economic_value_usd /
             result_nyc.total_incentive_economic_value_usd)
    assert abs(ratio - 1.40) <= 0.02, (
        f"Upstate/NYC ratio should be 1.40 (35%/25%), got {ratio:.4f}"
    )


def test_ny_upstate_economic_value_exact():
    result = _run(FIXTURE_NY_UPSTATE)
    expected = NY_EXPECTED_UPSTATE["economic_value_usd"]
    assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.01, (
        f"NY upstate credit: expected ${expected:,.0f}, "
        f"got ${result.total_incentive_economic_value_usd:,.0f}"
    )


def test_ny_upstate_uplift_recorded_in_trace():
    result = _run(FIXTURE_NY_UPSTATE)
    for iv in result.incentive_results:
        if iv.get("program_slug") == "ny_state_film":
            assert len(iv.get("uplifts_applied", [])) > 0, (
                "Upstate uplift should be recorded in incentive_results trace"
            )


# ===========================================================================
# NEW MEXICO
# ===========================================================================

def test_nm_runs():
    result = _run(FIXTURE_NM)
    assert result.total_input_budget_usd == NM_EXPECTED["total_budget_usd"]


def test_nm_atl_qualifies():
    """NM includes ATL in qualifying spend per NMSA § 7-2F-1 (PARSED)."""
    result = _run(FIXTURE_NM)
    for qs in result.qualified_spend_results:
        breakdown = qs.get("category_breakdown", {})
        assert "atl_director" in breakdown or "atl_cast" in breakdown, (
            "NM should include ATL director/cast in qualifying spend — "
            "PARSED per NMSA § 7-2F-1 broad definition"
        )


def test_nm_qualifying_spend_includes_atl():
    result = _run(FIXTURE_NM)
    qs = _qs(result)
    assert qs >= NM_EXPECTED["qualifying_spend_min_usd"]
    assert qs <= NM_EXPECTED["total_budget_usd"]


def test_nm_qualifying_spend_target():
    result = _run(FIXTURE_NM)
    qs = _qs(result)
    target = NM_EXPECTED["qualifying_spend_target_usd"]
    assert abs(qs - target) <= target * 0.05, (
        f"NM qualifying spend: expected ~${target:,.0f} (±5%), got ${qs:,.0f}"
    )


def test_nm_positive_incentive_value():
    result = _run(FIXTURE_NM)
    assert result.total_incentive_economic_value_usd > 0


def test_nm_economic_value_exact():
    result = _run(FIXTURE_NM)
    expected = NM_EXPECTED["economic_value_usd"]
    assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.05, (
        f"NM credit: expected ${expected:,.0f} (±5%), "
        f"got ${result.total_incentive_economic_value_usd:,.0f}"
    )


def test_nm_net_cost_decreases():
    result = _run(FIXTURE_NM)
    assert result.true_net_cost_usd < result.total_input_budget_usd


def test_nm_net_cost_non_negative():
    result = _run(FIXTURE_NM)
    assert result.true_net_cost_usd >= 0


def test_nm_confidence_tier_is_parsed():
    from tests.fixtures.ny_nm_or_validation import NM_PROGRAM
    assert NM_PROGRAM["confidence_tier"] == "PARSED"
    assert NM_PROGRAM["confidence_tier"] != "DISCOVERY"


def test_nm_trace_populated():
    result = _run(FIXTURE_NM)
    assert result.engine_version == "0.1.0"
    step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
    assert "classify_budget" in step_names
    assert "incentive_programs" in step_names


# ===========================================================================
# OREGON
# ===========================================================================

def test_or_runs():
    result = _run(FIXTURE_OR)
    assert result.total_input_budget_usd == OR_EXPECTED["total_budget_usd"]


def test_or_program_type_is_cash_rebate():
    """Oregon OPIF is a cash rebate, not a tax credit."""
    from tests.fixtures.ny_nm_or_validation import OR_PROGRAM
    assert OR_PROGRAM["program_type"] == "cash_rebate"


def test_or_atl_qualifies():
    """Oregon OPIF applies to Oregon-based expenditures broadly including ATL (PARSED)."""
    result = _run(FIXTURE_OR)
    for qs in result.qualified_spend_results:
        breakdown = qs.get("category_breakdown", {})
        assert "atl_director" in breakdown or "atl_cast" in breakdown, (
            "Oregon OPIF should include Oregon-based ATL spend — PARSED per OPIF guidelines"
        )


def test_or_qualifying_spend_target():
    result = _run(FIXTURE_OR)
    qs = _qs(result)
    target = OR_EXPECTED["qualifying_spend_target_usd"]
    assert abs(qs - target) <= target * 0.05, (
        f"OR qualifying spend: expected ~${target:,.0f} (±5%), got ${qs:,.0f}"
    )


def test_or_positive_incentive_value():
    result = _run(FIXTURE_OR)
    assert result.total_incentive_economic_value_usd > 0


def test_or_economic_value_exact():
    result = _run(FIXTURE_OR)
    expected = OR_EXPECTED["economic_value_usd"]
    assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.05, (
        f"OR rebate: expected ${expected:,.0f} (±5%), "
        f"got ${result.total_incentive_economic_value_usd:,.0f}"
    )


def test_or_net_cost_decreases():
    result = _run(FIXTURE_OR)
    assert result.true_net_cost_usd < result.total_input_budget_usd


def test_or_net_cost_non_negative():
    result = _run(FIXTURE_OR)
    assert result.true_net_cost_usd >= 0


def test_or_confidence_tier_is_parsed():
    from tests.fixtures.ny_nm_or_validation import OR_PROGRAM
    assert OR_PROGRAM["confidence_tier"] == "PARSED"
    assert OR_PROGRAM["confidence_tier"] != "DISCOVERY"


def test_or_trace_populated():
    result = _run(FIXTURE_OR)
    assert result.engine_version == "0.1.0"
    step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
    assert "classify_budget" in step_names
    assert "incentive_programs" in step_names


def test_or_stacking_clean():
    result = _run(FIXTURE_OR)
    assert result.stacking_violations == []


# ===========================================================================
# Cross-jurisdiction: ATL treatment differs between NY and NM/OR
# ===========================================================================

def test_ny_atl_exclusion_vs_nm_atl_inclusion():
    """Same ATL budget line produces $0 qualifying in NY but >$0 in NM."""
    result_ny = _run(FIXTURE_NY_NYC)
    result_nm = _run(FIXTURE_NM)

    ny_atl_qualifying = sum(
        qs.get("category_breakdown", {}).get("atl_director", 0)
        + qs.get("category_breakdown", {}).get("atl_cast", 0)
        for qs in result_ny.qualified_spend_results
    )
    nm_atl_qualifying = sum(
        qs.get("category_breakdown", {}).get("atl_director", 0)
        + qs.get("category_breakdown", {}).get("atl_cast", 0)
        for qs in result_nm.qualified_spend_results
    )

    assert ny_atl_qualifying == 0, (
        "NY credit excludes ATL — director+cast qualifying spend must be $0"
    )
    assert nm_atl_qualifying > 0, (
        "NM credit includes ATL — director+cast qualifying spend must be >$0"
    )
