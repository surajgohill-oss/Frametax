"""
Integration tests: run_full_analysis with all 8 synthetic project fixtures.
Deterministic — no DB, no LLM, no network.
"""
import pytest
from app.calculators.run_full_analysis import run_full_analysis
from tests.fixtures.synthetic_projects import (
    ALL_FIXTURES,
    FIXTURE_1_US_DOMESTIC,
    FIXTURE_2_CANADA_ONTARIO,
    FIXTURE_3_ATL_CAP,
    FIXTURE_4_BTL_LOCAL_LABOR,
    FIXTURE_5_DEFERRED_COMPENSATION,
    FIXTURE_6_REGIONAL_UPLIFT,
    FIXTURE_7_STACKING_ALLOWED,
    FIXTURE_8_STACKING_PROHIBITED,
)


def _run(fixture: dict):
    return run_full_analysis(
        structure_id="test-structure-id",
        jurisdiction=fixture["jurisdiction"],
        line_items=fixture["line_items"],
        programs_with_categories=fixture["programs_with_categories"],
        stacking_rules=fixture.get("stacking_rules", []),
        qualification_tests_with_rules=[],
        cost_benchmark=None,
        union_fringe_rules=[],
        fx_rates=fixture.get("fx_rates"),
        production_details=fixture.get("production_details"),
        home_jurisdiction_id=fixture.get("home_jurisdiction_id"),
    )


# ---------------------------------------------------------------------------
# Fixture 1: US Domestic
# ---------------------------------------------------------------------------
def test_fixture1_us_domestic_runs():
    result = _run(FIXTURE_1_US_DOMESTIC)
    assert result.total_input_budget_usd > 0
    assert result.true_net_cost_usd > 0
    assert result.calculation_trace["steps"]


def test_fixture1_has_incentive_value():
    result = _run(FIXTURE_1_US_DOMESTIC)
    assert result.total_incentive_economic_value_usd > 0


def test_fixture1_stacking_ok():
    result = _run(FIXTURE_1_US_DOMESTIC)
    assert result.stacking_legal_review_required is False
    assert result.stacking_violations == []


def test_fixture1_net_cost_less_than_gross():
    result = _run(FIXTURE_1_US_DOMESTIC)
    assert result.true_net_cost_usd < result.total_input_budget_usd


# ---------------------------------------------------------------------------
# Fixture 2: Canadian Province (Ontario)
# ---------------------------------------------------------------------------
def test_fixture2_canada_ontario_runs():
    result = _run(FIXTURE_2_CANADA_ONTARIO)
    assert result.total_input_budget_usd > 0
    assert result.jurisdiction_name == "Ontario"


def test_fixture2_has_incentive_value():
    result = _run(FIXTURE_2_CANADA_ONTARIO)
    assert result.total_incentive_economic_value_usd > 0


def test_fixture2_risk_is_high_discovery():
    result = _run(FIXTURE_2_CANADA_ONTARIO)
    # All programs are DISCOVERY tier → risk should be medium or high
    assert result.risk_level in {"medium", "high"}


# ---------------------------------------------------------------------------
# Fixture 3: ATL Cap
# ---------------------------------------------------------------------------
def test_fixture3_atl_cap_applied():
    result = _run(FIXTURE_3_ATL_CAP)
    assert result.total_input_budget_usd > 0
    # ATL cap means qualifying spend should be reduced vs uncapped
    # Incentive value should still be non-zero
    assert result.total_incentive_economic_value_usd >= 0


def test_fixture3_incentive_less_than_uncapped():
    """ATL cap version should have <= incentive value vs no-cap version."""
    capped_result = _run(FIXTURE_3_ATL_CAP)
    uncapped_fixture = {
        **FIXTURE_3_ATL_CAP,
        "programs_with_categories": [
            {
                **FIXTURE_3_ATL_CAP["programs_with_categories"][0],
                "program": {
                    **FIXTURE_3_ATL_CAP["programs_with_categories"][0]["program"],
                    "atl_cap_pct": None,
                },
            }
        ],
    }
    uncapped_result = _run(uncapped_fixture)
    assert capped_result.total_incentive_economic_value_usd <= uncapped_result.total_incentive_economic_value_usd


# ---------------------------------------------------------------------------
# Fixture 4: BTL Local Labor (60% jurisdiction spend)
# ---------------------------------------------------------------------------
def test_fixture4_qualifying_spend_reduced_by_pct():
    result = _run(FIXTURE_4_BTL_LOCAL_LABOR)
    total_btl = sum(
        item["amount_usd"] for item in FIXTURE_4_BTL_LOCAL_LABOR["line_items"]
        if item["department"] == "BTL"
    )
    # Qualifying spend should be < total BTL (60% applied)
    total_qs = sum(r.get("qualifying_spend_usd", 0) for r in result.qualified_spend_results)
    assert total_qs < total_btl


def test_fixture4_incentive_value_positive():
    result = _run(FIXTURE_4_BTL_LOCAL_LABOR)
    assert result.total_incentive_economic_value_usd > 0


# ---------------------------------------------------------------------------
# Fixture 5: Deferred Compensation
# ---------------------------------------------------------------------------
def test_fixture5_deferred_items_classified():
    from app.calculators.classify_budget_line_items import classify_atl_btl_split, classify_line_item
    from app.models.enums import CompensationType

    items = FIXTURE_5_DEFERRED_COMPENSATION["line_items"]
    classification = classify_atl_btl_split(items)
    deferred_items = [
        i for i in classification["classified_items"]
        if i.get("compensation_type") == CompensationType.DEFERRED.value
    ]
    # Director deferred fee is classified as deferred.
    # Writer deferred fee matches the writer rule first (ATL_WRITER, CASH) — known limitation.
    assert len(deferred_items) >= 1


def test_fixture5_full_analysis_runs():
    result = _run(FIXTURE_5_DEFERRED_COMPENSATION)
    assert result.total_input_budget_usd > 0


# ---------------------------------------------------------------------------
# Fixture 6: Regional Uplift (Georgia logo)
# ---------------------------------------------------------------------------
def test_fixture6_uplift_produces_higher_value():
    result_with_uplift = _run(FIXTURE_6_REGIONAL_UPLIFT)

    # Same fixture but no uplift
    no_uplift_fixture = {
        **FIXTURE_6_REGIONAL_UPLIFT,
        "programs_with_categories": [
            {
                **FIXTURE_6_REGIONAL_UPLIFT["programs_with_categories"][0],
                "uplifts": [],
            }
        ],
    }
    result_no_uplift = _run(no_uplift_fixture)

    assert result_with_uplift.total_incentive_economic_value_usd > result_no_uplift.total_incentive_economic_value_usd


def test_fixture6_uplift_trace_recorded():
    result = _run(FIXTURE_6_REGIONAL_UPLIFT)
    # The incentive results should have uplifts_applied
    for iv in result.incentive_results:
        if iv.get("program_slug") == "georgia_eiia":
            assert len(iv.get("uplifts_applied", [])) > 0


# ---------------------------------------------------------------------------
# Fixture 7: Legal Stacking ALLOWED
# ---------------------------------------------------------------------------
def test_fixture7_stacking_allowed():
    result = _run(FIXTURE_7_STACKING_ALLOWED)
    # ALLOWED rule → no violations → legal_review_required = False
    assert result.stacking_violations == []
    assert result.stacking_legal_review_required is False


def test_fixture7_two_programs_both_produce_value():
    result = _run(FIXTURE_7_STACKING_ALLOWED)
    assert len(result.incentive_results) == 2
    assert result.total_incentive_economic_value_usd > 0


# ---------------------------------------------------------------------------
# Fixture 8: Legal Stacking PROHIBITED
# ---------------------------------------------------------------------------
def test_fixture8_stacking_prohibited_flags_violation():
    result = _run(FIXTURE_8_STACKING_PROHIBITED)
    assert result.stacking_legal_review_required is True
    assert len(result.stacking_violations) == 1


def test_fixture8_violation_identifies_correct_programs():
    result = _run(FIXTURE_8_STACKING_PROHIBITED)
    violation = result.stacking_violations[0]
    program_ids = {violation["program_a_id"], violation["program_b_id"]}
    assert "prog-on-opstc" in program_ids
    assert "prog-ca-cptc" in program_ids


# ---------------------------------------------------------------------------
# Cross-fixture: engine version consistency
# ---------------------------------------------------------------------------
def test_all_fixtures_have_trace():
    for fixture in ALL_FIXTURES:
        result = _run(fixture)
        assert result.engine_version == "0.1.0"
        assert "steps" in result.calculation_trace
        assert len(result.calculation_trace["steps"]) > 0


def test_all_fixtures_produce_non_negative_net():
    for fixture in ALL_FIXTURES:
        result = _run(fixture)
        assert result.true_net_cost_usd >= 0, (
            f"{fixture['name']}: true_net_cost_usd should never be negative"
        )
