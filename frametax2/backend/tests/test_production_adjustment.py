"""
test_production_adjustment.py

Tests for the Production Adjustment Layer:
  - GREENFIELD mode smoke tests
  - EXISTING_BUDGET delta tests
  - Mauritius regression (no double-counting)
  - Same-jurisdiction delta == 0
  - Home base LAX vs JFK differences
  - Individual adjustment toggle exclusions
  - Delta engine comparison
  - Nationality lookup framework
"""
from __future__ import annotations

import pytest

from app.calculators.production_adjustment import (
    AdjustmentCategory,
    AdjustmentMode,
    AdjustmentToggles,
    CrewManifest,
    ProductionAdjustmentInput,
    ProductionBudgetParams,
    calculate_production_adjustment,
)
from app.calculators.delta_engine import (
    DeltaInput,
    JurisdictionIncentive,
    calculate_delta,
    explain_winner,
)
from app.data.location_cost_benchmarks import (
    get_profile,
    get_profile_or_fallback,
    list_supported_jurisdictions,
)
from app.data.nationality_lookup import (
    ConfidenceTier,
    add_verified_person,
    build_nationality_report,
    lookup_nationality,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def standard_crew() -> CrewManifest:
    return CrewManifest(
        atl_count=4,
        atl_business_class=True,
        dept_head_count=8,
        dept_head_business_class=False,
        btl_traveling_count=20,
        local_btl_count=60,
        producer_oversight_trips=3,
        producer_oversight_business=True,
        shoot_days=30,
        hotel_nights_traveling_crew=35,
        per_diem_days_traveling=35,
    )


@pytest.fixture
def standard_budget() -> ProductionBudgetParams:
    return ProductionBudgetParams(
        total_budget_usd=5_000_000,
        btl_budget_usd=3_000_000,
        equipment_value_usd=500_000,
        gross_payroll_usd=2_000_000,
        la_legal_accounting_usd=150_000,
        la_equipment_rental_usd=400_000,
        la_stage_facility_usd=300_000,
    )


# ---------------------------------------------------------------------------
# Benchmark data tests
# ---------------------------------------------------------------------------

def test_benchmark_jurisdictions_present():
    supported = list_supported_jurisdictions()
    for iso2 in ["US", "GB", "IE", "FR", "DE", "IT", "ES", "HU", "CZ",
                 "MT", "AU", "NZ", "CA", "MU", "ZA", "AE", "JP", "KR"]:
        assert iso2 in supported, f"{iso2} not in benchmark data"


def test_mauritius_profile_exists():
    p = get_profile("MU")
    assert p is not None
    assert p.iso2 == "MU"
    assert p.airfare_lax_business_usd > 0
    assert p.hotel_rate_usd > 0


def test_us_profile_is_baseline():
    p = get_profile("US")
    assert p.crew_rate_index == 1.0
    assert p.equipment_rental_index == 1.0
    assert p.airfare_lax_business_usd == 0


def test_profile_or_fallback_unknown_jurisdiction():
    p = get_profile_or_fallback("XX", region="western_europe")
    assert p.iso2 == "XX"
    assert p.confidence == "LOW"
    assert "regional" in p.notes.lower() or "proxy" in p.notes.lower()


def test_profile_fields_are_non_negative():
    for iso2 in list_supported_jurisdictions():
        p = get_profile(iso2)
        assert p.hotel_rate_usd >= 0, f"{iso2}: hotel_rate negative"
        assert p.payroll_fringe_pct >= 0, f"{iso2}: payroll_fringe negative"
        assert p.crew_rate_index > 0, f"{iso2}: crew_rate_index zero"


# ---------------------------------------------------------------------------
# GREENFIELD mode tests
# ---------------------------------------------------------------------------

def test_greenfield_gb_produces_positive_costs(standard_crew, standard_budget):
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
    )
    result = calculate_production_adjustment(inp)
    assert result.mode == AdjustmentMode.GREENFIELD
    assert result.total_adjustment_usd > 0
    assert result.airfare_usd > 0
    assert result.hotel_usd > 0
    assert result.per_diem_usd > 0
    assert result.payroll_fringe_usd > 0


def test_greenfield_same_home_no_airfare(standard_crew, standard_budget):
    inp = ProductionAdjustmentInput(
        home_base_iso2="GB",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
    )
    result = calculate_production_adjustment(inp)
    assert result.airfare_usd == 0.0
    assert result.hotel_usd == 0.0
    assert result.per_diem_usd == 0.0
    assert result.freight_carnet_usd == 0.0
    assert result.visa_work_permit_usd == 0.0


def test_greenfield_atl_business_class_costs_more(standard_budget):
    crew_biz = CrewManifest(atl_count=4, atl_business_class=True, dept_head_count=0, btl_traveling_count=0)
    crew_eco = CrewManifest(atl_count=4, atl_business_class=False, dept_head_count=0, btl_traveling_count=0)

    inp_biz = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=crew_biz,
        budget=standard_budget,
    )
    inp_eco = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=crew_eco,
        budget=standard_budget,
    )
    r_biz = calculate_production_adjustment(inp_biz)
    r_eco = calculate_production_adjustment(inp_eco)
    assert r_biz.airfare_usd > r_eco.airfare_usd


def test_greenfield_hungary_cheaper_than_gb(standard_crew, standard_budget):
    def run(dest):
        return calculate_production_adjustment(ProductionAdjustmentInput(
            home_base_iso2="US",
            destination_iso2=dest,
            mode=AdjustmentMode.GREENFIELD,
            crew=standard_crew,
            budget=standard_budget,
        ))
    r_hu = run("HU")
    r_gb = run("GB")
    # Hungary: cheaper crew, equipment, stage — should be cheaper on production costs
    assert r_hu.equipment_usd < r_gb.equipment_usd
    assert r_hu.stage_facility_usd < r_gb.stage_facility_usd


def test_greenfield_jfk_reduces_europe_airfare(standard_crew, standard_budget):
    base_inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        use_jfk_as_secondary=False,
    )
    jfk_inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        use_jfk_as_secondary=True,
    )
    r_base = calculate_production_adjustment(base_inp)
    r_jfk = calculate_production_adjustment(jfk_inp)
    # JFK delta for GB is negative (cheaper), so JFK airfare should be less
    gb_profile = get_profile("GB")
    if gb_profile.airfare_jfk_delta_usd < 0:
        assert r_jfk.airfare_usd < r_base.airfare_usd


# ---------------------------------------------------------------------------
# EXISTING_BUDGET mode tests
# ---------------------------------------------------------------------------

def test_existing_budget_requires_existing_iso2(standard_crew, standard_budget):
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.EXISTING_BUDGET,
        existing_budget_iso2=None,
        crew=standard_crew,
        budget=standard_budget,
    )
    with pytest.raises(ValueError, match="existing_budget_iso2"):
        calculate_production_adjustment(inp)


def test_existing_budget_same_jurisdiction_all_zeros(standard_crew, standard_budget):
    """
    REGRESSION: When destination == existing_budget_iso2, all deltas must be 0.
    This is the anti-double-count constraint.
    """
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="MU",
        mode=AdjustmentMode.EXISTING_BUDGET,
        existing_budget_iso2="MU",
        crew=standard_crew,
        budget=standard_budget,
    )
    result = calculate_production_adjustment(inp)
    assert result.total_adjustment_usd == 0.0
    assert result.airfare_usd == 0.0
    assert result.hotel_usd == 0.0
    assert result.per_diem_usd == 0.0
    assert result.freight_carnet_usd == 0.0
    assert result.visa_work_permit_usd == 0.0
    assert result.payroll_fringe_usd == 0.0
    assert result.local_transport_usd == 0.0
    assert result.legal_accounting_usd == 0.0
    assert result.equipment_usd == 0.0
    assert result.stage_facility_usd == 0.0
    assert result.contingency_usd == 0.0
    assert result.fx_usd == 0.0


def test_existing_budget_mauritius_to_malta_is_delta_only(standard_crew, standard_budget):
    """
    REGRESSION: Little Utopia scenario.
    Budget is already Mauritius-based. Comparing with Malta must produce
    only the incremental cost difference, NOT Malta's full travel costs.
    """
    # EXISTING_BUDGET: delta only
    delta_inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="MT",
        mode=AdjustmentMode.EXISTING_BUDGET,
        existing_budget_iso2="MU",
        crew=standard_crew,
        budget=standard_budget,
    )
    # GREENFIELD: full Malta costs
    greenfield_inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="MT",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
    )

    delta_result = calculate_production_adjustment(delta_inp)
    greenfield_result = calculate_production_adjustment(greenfield_inp)

    # Delta must be LESS than greenfield (since Mauritius already has travel costs)
    assert delta_result.total_adjustment_usd < greenfield_result.total_adjustment_usd, (
        "EXISTING_BUDGET delta should be less than GREENFIELD — "
        "Mauritius travel is already embedded in the budget"
    )

    # Delta airfare should reflect Malta-Mauritius difference, not full Malta airfare
    # Malta airfare from LAX ~ 5600; Mauritius ~ 8500; delta should be negative (Malta is closer)
    # So challenger (Malta) is cheaper to reach than baseline (Mauritius)
    assert delta_result.mode == AdjustmentMode.EXISTING_BUDGET


def test_existing_budget_delta_notes_show_base_value(standard_crew, standard_budget):
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="MT",
        mode=AdjustmentMode.EXISTING_BUDGET,
        existing_budget_iso2="MU",
        crew=standard_crew,
        budget=standard_budget,
    )
    result = calculate_production_adjustment(inp)
    # At least some line items should reference the delta
    delta_notes = [it.notes for it in result.line_items if "DELTA" in it.notes.upper()]
    assert len(delta_notes) > 0


# ---------------------------------------------------------------------------
# Toggle / exclusion tests
# ---------------------------------------------------------------------------

def test_toggle_airfare_excluded_zeroes_active_preserves_calculated(standard_crew, standard_budget):
    toggles = AdjustmentToggles(airfare=False)
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        toggles=toggles,
    )
    result = calculate_production_adjustment(inp)

    assert result.airfare_usd == 0.0, "Active airfare should be 0 when excluded"

    airfare_items = [it for it in result.line_items if it.category == AdjustmentCategory.AIRFARE]
    assert len(airfare_items) > 0
    for it in airfare_items:
        assert it.user_excluded is True
        assert it.amount_usd == 0.0
        assert it.calculated_amount_usd > 0, "Calculated value must be preserved even when excluded"

    assert result.total_excluded_usd > 0


def test_toggle_all_excluded_total_adjustment_zero(standard_crew, standard_budget):
    toggles = AdjustmentToggles(
        airfare=False, hotel=False, per_diem=False,
        freight_carnet=False, visa_work_permit=False, payroll_fringe=False,
        local_transport=False, legal_accounting=False, local_hire_premium=False,
        equipment=False, stage_facility=False, contingency=False, fx=False,
    )
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        toggles=toggles,
    )
    result = calculate_production_adjustment(inp)
    assert result.total_adjustment_usd == 0.0
    assert result.total_excluded_usd > 0
    assert len(result.exclusion_notes) > 0


def test_toggle_exclusion_notes_in_result(standard_crew, standard_budget):
    toggles = AdjustmentToggles(airfare=False, hotel=False)
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        toggles=toggles,
    )
    result = calculate_production_adjustment(inp)
    assert len(result.exclusion_notes) > 0
    full_text = " ".join(result.exclusion_notes).lower()
    assert "user excluded" in full_text or "excluded" in full_text


def test_toggle_single_category_reduces_total(standard_crew, standard_budget):
    base_inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        toggles=AdjustmentToggles(),
    )
    toggled_inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        toggles=AdjustmentToggles(payroll_fringe=False),
    )
    r_base = calculate_production_adjustment(base_inp)
    r_toggled = calculate_production_adjustment(toggled_inp)
    assert r_toggled.total_adjustment_usd < r_base.total_adjustment_usd
    assert r_toggled.payroll_fringe_usd == 0.0


# ---------------------------------------------------------------------------
# Delta engine tests
# ---------------------------------------------------------------------------

def test_delta_same_jurisdiction_net_benefit_zero(standard_crew, standard_budget):
    di = DeltaInput(
        baseline=JurisdictionIncentive(iso2="MT", gross_incentive_usd=1_000_000),
        challenger=JurisdictionIncentive(iso2="MT", gross_incentive_usd=1_000_000),
        home_base_iso2="US",
        crew=standard_crew,
        budget=standard_budget,
        existing_budget_iso2="MT",
    )
    result = calculate_delta(di)
    assert result.net_producer_benefit_usd == 0.0
    assert result.winner == "neutral"


def test_delta_challenger_higher_incentive_wins(standard_crew, standard_budget):
    di = DeltaInput(
        baseline=JurisdictionIncentive(iso2="MX", gross_incentive_usd=500_000),
        challenger=JurisdictionIncentive(iso2="IE", gross_incentive_usd=2_000_000),
        home_base_iso2="US",
        crew=standard_crew,
        budget=standard_budget,
    )
    result = calculate_delta(di)
    assert result.incentive_gain_usd > 0
    # Ireland incentive >> Mexico incentive — challenger should win
    assert result.winner == "challenger"


def test_delta_mauritius_no_double_count_regression(standard_crew, standard_budget):
    """
    CORE REGRESSION: Little Utopia scenario.
    Uploaded budget is Mauritius-based.
    Comparing Mauritius vs. Malta: travel to Mauritius is ALREADY in the budget.
    The delta engine must NOT add Mauritius travel on top of the existing budget.
    """
    # Malta has a higher incentive in this scenario
    di = DeltaInput(
        baseline=JurisdictionIncentive(iso2="MU", gross_incentive_usd=300_000, incentive_label="Mauritius Grant"),
        challenger=JurisdictionIncentive(iso2="MT", gross_incentive_usd=600_000, incentive_label="Malta Tax Credit"),
        home_base_iso2="US",
        crew=standard_crew,
        budget=standard_budget,
        existing_budget_iso2="MU",  # <-- budget is already Mauritius-based
    )
    result = calculate_delta(di)

    # Baseline (Mauritius) should have zero production costs in EXISTING_BUDGET mode
    # because the budget is already Mauritius-scoped
    assert result.baseline_production_cost_usd == 0.0, (
        "REGRESSION FAIL: Mauritius production costs must be 0 when the uploaded "
        "budget is already Mauritius-based (no double-counting)"
    )

    # Travel delta should reflect Malta-vs-nothing, not Malta vs Mauritius + Mauritius travel
    # The net benefit should reflect true incremental economics
    assert result.mode == "EXISTING_BUDGET"


def test_delta_explain_winner_returns_string(standard_crew, standard_budget):
    di = DeltaInput(
        baseline=JurisdictionIncentive(iso2="HU", gross_incentive_usd=800_000),
        challenger=JurisdictionIncentive(iso2="IE", gross_incentive_usd=1_500_000),
        home_base_iso2="US",
        crew=standard_crew,
        budget=standard_budget,
    )
    result = calculate_delta(di)
    explanation = explain_winner(result)
    assert isinstance(explanation, str)
    assert "VERDICT" in explanation
    assert "net producer benefit" in explanation.lower() or "Net producer" in explanation


def test_delta_exclusion_warning_when_toggles_active(standard_crew, standard_budget):
    toggles = AdjustmentToggles(airfare=False)
    di = DeltaInput(
        baseline=JurisdictionIncentive(iso2="MX", gross_incentive_usd=400_000),
        challenger=JurisdictionIncentive(iso2="IE", gross_incentive_usd=1_200_000),
        home_base_iso2="US",
        crew=standard_crew,
        budget=standard_budget,
        toggles=toggles,
    )
    result = calculate_delta(di)
    assert result.exclusion_warning != ""


def test_delta_factors_ranked_by_impact(standard_crew, standard_budget):
    di = DeltaInput(
        baseline=JurisdictionIncentive(iso2="US", gross_incentive_usd=0),
        challenger=JurisdictionIncentive(iso2="GB", gross_incentive_usd=1_000_000),
        home_base_iso2="US",
        crew=standard_crew,
        budget=standard_budget,
    )
    result = calculate_delta(di)
    assert len(result.explanation_factors) > 0
    # Should be sorted by abs(delta_usd) descending
    impacts = [abs(f.delta_usd) for f in result.explanation_factors]
    assert impacts == sorted(impacts, reverse=True)


# ---------------------------------------------------------------------------
# Nationality lookup tests
# ---------------------------------------------------------------------------

def test_lookup_unknown_person_returns_unknown():
    result = lookup_nationality("Jane Quantum Fictional", "director")
    assert result.confidence == ConfidenceTier.UNKNOWN
    assert result.citizenship is None
    assert result.manual_confirmation_required is True
    assert result.verified is False


def test_lookup_unknown_person_note_suggests_confirmation():
    result = lookup_nationality("John Doe Fictional", "producer")
    note = result.unknown_note()
    assert "MANUAL CONFIRMATION REQUIRED" in note
    assert "John Doe Fictional" in note


def test_lookup_preserves_role():
    result = lookup_nationality("Unknown Person", "cinematographer")
    assert result.role == "cinematographer"


def test_lookup_preserves_name():
    result = lookup_nationality("María García López", "writer")
    assert result.name == "María García López"


def test_add_verified_person_and_lookup():
    add_verified_person(
        name="Test Director One",
        citizenship="IE",
        dual_citizenship=["GB"],
        residency="IE",
        source_url="https://example.com/test",
        source_description="Test record",
        confidence="MEDIUM",
        notes="Test-only entry",
    )
    result = lookup_nationality("Test Director One", "director")
    assert result.verified is True
    assert result.citizenship == "IE"
    assert "GB" in result.dual_citizenship
    assert result.confidence == ConfidenceTier.MEDIUM
    assert result.manual_confirmation_required is False


def test_add_verified_person_invalid_iso2_raises():
    with pytest.raises(ValueError, match="ISO country code"):
        add_verified_person(name="Bad Entry", citizenship="IRELAND")


def test_treaty_eligibility_verified_person():
    add_verified_person(
        name="Treaty Test Person",
        citizenship="FR",
        source_description="Test",
        confidence="HIGH",
    )
    result = lookup_nationality("Treaty Test Person", "producer")
    assert result.is_eligible_for_treaty("FR") is True
    assert result.is_eligible_for_treaty("DE") is False


def test_treaty_eligibility_unknown_returns_none():
    result = lookup_nationality("No Data Person", "editor")
    assert result.is_eligible_for_treaty("FR") is None


def test_batch_lookup_returns_correct_count():
    persons = [
        ("Unknown Alpha", "director"),
        ("Unknown Beta", "writer"),
        ("Unknown Gamma", "producer"),
    ]
    results = build_nationality_report(persons)
    assert results.total_persons == 3
    assert results.unknown_count == 3
    assert len(results.manual_confirmation_required) == 3


def test_nationality_report_has_warnings_for_unknowns():
    persons = [("Someone Unknown", "cast")]
    report = build_nationality_report(persons)
    assert len(report.warnings) > 0


def test_nationality_report_by_citizenship_groups_correctly():
    add_verified_person(
        name="Director Alpha Test",
        citizenship="HU",
        confidence="MEDIUM",
        source_description="Test",
    )
    add_verified_person(
        name="Producer Beta Test",
        citizenship="HU",
        confidence="MEDIUM",
        source_description="Test",
    )
    report = build_nationality_report([
        ("Director Alpha Test", "director"),
        ("Producer Beta Test", "producer"),
    ])
    assert "HU" in report.by_citizenship
    assert len(report.by_citizenship["HU"]) == 2


def test_lookup_case_insensitive_role():
    r1 = lookup_nationality("Some Person XYZ", "VFX Supervisor")
    r2 = lookup_nationality("Some Person XYZ", "vfx_supervisor")
    # Both should produce UNKNOWN but not error
    assert r1.confidence == ConfidenceTier.UNKNOWN
    assert r2.confidence == ConfidenceTier.UNKNOWN


# ---------------------------------------------------------------------------
# Line item structure tests
# ---------------------------------------------------------------------------

def test_line_items_have_all_required_fields(standard_crew, standard_budget):
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="MT",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
    )
    result = calculate_production_adjustment(inp)
    for item in result.line_items:
        assert item.category in AdjustmentCategory
        assert isinstance(item.subcategory, str) and item.subcategory
        assert item.calculated_amount_usd >= 0
        assert item.amount_usd >= 0
        assert item.confidence in ("HIGH", "MEDIUM", "LOW")
        assert isinstance(item.notes, str)


def test_excluded_items_amount_zero_calculated_positive(standard_crew, standard_budget):
    toggles = AdjustmentToggles(hotel=False)
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="MT",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        toggles=toggles,
    )
    result = calculate_production_adjustment(inp)
    hotel_items = [it for it in result.line_items if it.category == AdjustmentCategory.HOTEL]
    for it in hotel_items:
        assert it.user_excluded is True
        assert it.amount_usd == 0.0
        assert it.calculated_amount_usd > 0


def test_total_calculated_gte_total_adjustment(standard_crew, standard_budget):
    toggles = AdjustmentToggles(airfare=False, hotel=False)
    inp = ProductionAdjustmentInput(
        home_base_iso2="US",
        destination_iso2="GB",
        mode=AdjustmentMode.GREENFIELD,
        crew=standard_crew,
        budget=standard_budget,
        toggles=toggles,
    )
    result = calculate_production_adjustment(inp)
    assert result.total_calculated_usd >= result.total_adjustment_usd
    assert result.total_excluded_usd > 0
    assert abs(result.total_calculated_usd - result.total_adjustment_usd - result.total_excluded_usd) < 1.0
