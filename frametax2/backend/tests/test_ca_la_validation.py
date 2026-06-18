"""
California and Louisiana end-to-end validation tests.

Sources:
  CA: CA Gov Code § 17053.98 (PARSED)
  LA: LA RS § 47:6007 (PARSED)

Hand-verified expected values documented in tests/fixtures/ca_la_validation.py.
"""
import pytest
from app.calculators.run_full_analysis import run_full_analysis
from tests.fixtures.ca_la_validation import (
    CA_EXPECTED,
    CA_PROGRAM,
    FIXTURE_CA,
    FIXTURE_LA,
    LA_EXPECTED,
    LA_PROGRAM,
)


def _run(fixture: dict):
    return run_full_analysis(
        structure_id="validation-ca-la",
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
# CALIFORNIA — Film & TV Tax Credit Program 3.0
# ===========================================================================

def test_ca_runs():
    result = _run(FIXTURE_CA)
    assert result.total_input_budget_usd == CA_EXPECTED["total_budget_usd"]


def test_ca_program_type_is_tax_credit():
    assert CA_PROGRAM["program_type"] == "tax_credit"


def test_ca_is_competitive():
    """CA Film Commission program has competitive allocation — credit not guaranteed."""
    assert CA_PROGRAM["is_competitive"] is True


def test_ca_is_not_refundable():
    """CA Film & TV credit is non-refundable (against income/franchise tax)."""
    assert CA_PROGRAM["is_refundable"] is False


def test_ca_is_transferable():
    assert CA_PROGRAM["is_transferable"] is True


def test_ca_atl_excluded_from_qualifying_spend():
    """CA credit excludes ATL — directors and cast should produce no qualifying spend."""
    result = _run(FIXTURE_CA)
    for qs in result.qualified_spend_results:
        breakdown = qs.get("category_breakdown", {})
        assert "atl_director" not in breakdown, (
            "atl_director should be EXCLUDED from CA qualifying spend per § 17053.98"
        )
        assert "atl_cast" not in breakdown, (
            "atl_cast should be EXCLUDED from CA qualifying spend per § 17053.98"
        )


def test_ca_qualifying_spend_exact():
    result = _run(FIXTURE_CA)
    qs = _qs(result)
    expected = CA_EXPECTED["qualifying_spend_usd"]
    assert abs(qs - expected) <= expected * 0.01, (
        f"CA qualifying spend: expected ${expected:,.0f}, got ${qs:,.0f}"
    )


def test_ca_positive_incentive_value():
    result = _run(FIXTURE_CA)
    assert result.total_incentive_economic_value_usd > 0


def test_ca_economic_value_exact():
    result = _run(FIXTURE_CA)
    expected = CA_EXPECTED["economic_value_usd"]
    assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.02, (
        f"CA economic value: expected ${expected:,.0f}, "
        f"got ${result.total_incentive_economic_value_usd:,.0f}"
    )


def test_ca_vfx_uplift_is_applied():
    """VFX uplift ($300K * 5% = $15K) must appear in incentive_results trace."""
    result = _run(FIXTURE_CA)
    for iv in result.incentive_results:
        if iv.get("program_slug") == "ca_film_30":
            vfx_uplifts = [u for u in iv.get("uplifts_applied", [])
                           if u.get("name") == "California VFX Uplift"]
            assert len(vfx_uplifts) == 1, "CA VFX uplift must be recorded"
            assert abs(vfx_uplifts[0]["credit_usd"] - CA_EXPECTED["vfx_uplift_usd"]) < 1.0, (
                f"VFX uplift credit: expected ${CA_EXPECTED['vfx_uplift_usd']:,.0f}, "
                f"got ${vfx_uplifts[0]['credit_usd']:,.0f}"
            )


def test_ca_music_uplift_is_applied():
    """Music uplift ($100K * 5% = $5K) must appear in incentive_results trace."""
    result = _run(FIXTURE_CA)
    for iv in result.incentive_results:
        if iv.get("program_slug") == "ca_film_30":
            music_uplifts = [u for u in iv.get("uplifts_applied", [])
                             if u.get("name") == "California Music Recording Uplift"]
            assert len(music_uplifts) == 1, "CA music uplift must be recorded"
            assert abs(music_uplifts[0]["credit_usd"] - CA_EXPECTED["music_uplift_usd"]) < 1.0


def test_ca_indie_uplift_does_not_apply_without_budget_detail():
    """
    Independent uplift requires production_details['total_budget_usd'] <= $10M.
    Fixture has production_details={} (no total_budget_usd key), so condition=False.
    """
    result = _run(FIXTURE_CA)
    for iv in result.incentive_results:
        if iv.get("program_slug") == "ca_film_30":
            indie_uplifts = [u for u in iv.get("uplifts_applied", [])
                             if u.get("name") == "California Independent Film Uplift"]
            assert indie_uplifts == [], (
                "Indie uplift must NOT apply when production_details has no total_budget_usd"
            )


def test_ca_competitive_warning_in_notes():
    """Competitive allocation warning must appear in the incentive notes trace."""
    result = _run(FIXTURE_CA)
    for iv in result.incentive_results:
        if iv.get("program_slug") == "ca_film_30":
            notes = iv.get("notes", [])
            competitive_notes = [n for n in notes if "competitive" in n.lower()]
            assert len(competitive_notes) > 0, (
                "Competitive allocation warning must appear in CA credit notes"
            )


def test_ca_net_cost_less_than_gross():
    result = _run(FIXTURE_CA)
    assert result.true_net_cost_usd < result.total_input_budget_usd


def test_ca_net_cost_non_negative():
    result = _run(FIXTURE_CA)
    assert result.true_net_cost_usd >= 0


def test_ca_net_cost_exact():
    result = _run(FIXTURE_CA)
    expected = CA_EXPECTED["true_net_cost_usd"]
    assert abs(result.true_net_cost_usd - expected) <= expected * 0.02, (
        f"CA true net cost: expected ${expected:,.0f}, "
        f"got ${result.true_net_cost_usd:,.0f}"
    )


def test_ca_confidence_tier_is_parsed():
    assert CA_PROGRAM["confidence_tier"] == "PARSED"
    assert CA_PROGRAM["confidence_tier"] != "VERIFIED"
    assert CA_PROGRAM["confidence_tier"] != "DISCOVERY"


def test_ca_stacking_clean():
    result = _run(FIXTURE_CA)
    assert result.stacking_violations == []


def test_ca_trace_populated():
    result = _run(FIXTURE_CA)
    assert result.engine_version == "0.1.0"
    step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
    assert "classify_budget" in step_names
    assert "incentive_programs" in step_names


# ===========================================================================
# LOUISIANA — Motion Picture Production Tax Credit
# ===========================================================================

def test_la_runs():
    result = _run(FIXTURE_LA)
    assert result.total_input_budget_usd == LA_EXPECTED["total_budget_usd"]


def test_la_program_type_is_tax_credit():
    assert LA_PROGRAM["program_type"] == "tax_credit"


def test_la_is_not_competitive():
    assert LA_PROGRAM["is_competitive"] is False


def test_la_is_refundable():
    """LA credit is refundable — state buyback program exists."""
    assert LA_PROGRAM["is_refundable"] is True


def test_la_atl_qualifies():
    """LA includes ATL in certified expenditures per RS § 47:6007 (PARSED)."""
    result = _run(FIXTURE_LA)
    for qs in result.qualified_spend_results:
        breakdown = qs.get("category_breakdown", {})
        assert "atl_director" in breakdown or "atl_cast" in breakdown, (
            "LA should include ATL director/cast in qualifying spend per RS § 47:6007"
        )


def test_la_qualifying_spend_includes_atl():
    result = _run(FIXTURE_LA)
    qs = _qs(result)
    assert qs >= LA_EXPECTED["qualifying_spend_min_usd"], (
        "LA qualifying spend must be at least BTL+Post"
    )


def test_la_qualifying_spend_exact():
    result = _run(FIXTURE_LA)
    qs = _qs(result)
    expected = LA_EXPECTED["qualifying_spend_usd"]
    assert abs(qs - expected) <= expected * 0.01, (
        f"LA qualifying spend: expected ${expected:,.0f}, got ${qs:,.0f}"
    )


def test_la_resident_labor_classified():
    """'Louisiana Resident Labor' must classify to btl_resident_labor category."""
    result = _run(FIXTURE_LA)
    for qs in result.qualified_spend_results:
        breakdown = qs.get("category_breakdown", {})
        assert "btl_resident_labor" in breakdown, (
            "Louisiana Resident Labor line item must classify to btl_resident_labor"
        )
        assert abs(breakdown["btl_resident_labor"] - LA_EXPECTED["resident_labor_usd"]) < 1.0, (
            f"btl_resident_labor: expected ${LA_EXPECTED['resident_labor_usd']:,.0f}, "
            f"got ${breakdown['btl_resident_labor']:,.0f}"
        )


def test_la_resident_uplift_applied():
    """Resident payroll uplift ($300K * 10% = $30K) must appear in trace."""
    result = _run(FIXTURE_LA)
    for iv in result.incentive_results:
        if iv.get("program_slug") == "la_film_production":
            res_uplifts = [u for u in iv.get("uplifts_applied", [])
                           if u.get("name") == "Louisiana Resident Payroll Uplift"]
            assert len(res_uplifts) == 1, "LA resident payroll uplift must be recorded"
            assert abs(res_uplifts[0]["credit_usd"] - LA_EXPECTED["resident_uplift_usd"]) < 1.0, (
                f"Resident uplift credit: expected ${LA_EXPECTED['resident_uplift_usd']:,.0f}, "
                f"got ${res_uplifts[0]['credit_usd']:,.0f}"
            )


def test_la_positive_incentive_value():
    result = _run(FIXTURE_LA)
    assert result.total_incentive_economic_value_usd > 0


def test_la_economic_value_exact():
    result = _run(FIXTURE_LA)
    expected = LA_EXPECTED["economic_value_usd"]
    assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.02, (
        f"LA economic value: expected ${expected:,.0f}, "
        f"got ${result.total_incentive_economic_value_usd:,.0f}"
    )


def test_la_economic_value_equals_total_credit():
    """Refundable credit → economic value must equal face-value credit."""
    result = _run(FIXTURE_LA)
    for iv in result.incentive_results:
        if iv.get("program_slug") == "la_film_production":
            assert abs(iv["economic_value_usd"] - iv["total_credit_usd"]) < 1.0, (
                "Refundable LA credit: economic_value must equal total_credit"
            )


def test_la_net_cost_less_than_gross():
    result = _run(FIXTURE_LA)
    assert result.true_net_cost_usd < result.total_input_budget_usd


def test_la_net_cost_non_negative():
    result = _run(FIXTURE_LA)
    assert result.true_net_cost_usd >= 0


def test_la_net_cost_exact():
    result = _run(FIXTURE_LA)
    expected = LA_EXPECTED["true_net_cost_usd"]
    assert abs(result.true_net_cost_usd - expected) <= expected * 0.02, (
        f"LA true net cost: expected ${expected:,.0f}, "
        f"got ${result.true_net_cost_usd:,.0f}"
    )


def test_la_confidence_tier_is_parsed():
    assert LA_PROGRAM["confidence_tier"] == "PARSED"
    assert LA_PROGRAM["confidence_tier"] != "VERIFIED"
    assert LA_PROGRAM["confidence_tier"] != "DISCOVERY"


def test_la_stacking_clean():
    result = _run(FIXTURE_LA)
    assert result.stacking_violations == []


def test_la_trace_populated():
    result = _run(FIXTURE_LA)
    assert result.engine_version == "0.1.0"
    step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
    assert "classify_budget" in step_names
    assert "incentive_programs" in step_names


# ===========================================================================
# Cross-jurisdiction: ATL treatment differs between CA and LA
# ===========================================================================

def test_ca_atl_exclusion_vs_la_atl_inclusion():
    """Same ATL budget line produces $0 qualifying in CA but >$0 in LA."""
    result_ca = _run(FIXTURE_CA)
    result_la = _run(FIXTURE_LA)

    ca_atl_qualifying = sum(
        qs.get("category_breakdown", {}).get("atl_director", 0)
        + qs.get("category_breakdown", {}).get("atl_cast", 0)
        for qs in result_ca.qualified_spend_results
    )
    la_atl_qualifying = sum(
        qs.get("category_breakdown", {}).get("atl_director", 0)
        + qs.get("category_breakdown", {}).get("atl_cast", 0)
        for qs in result_la.qualified_spend_results
    )

    assert ca_atl_qualifying == 0, (
        "CA credit excludes ATL — director+cast qualifying spend must be $0"
    )
    assert la_atl_qualifying > 0, (
        "LA credit includes ATL — director+cast qualifying spend must be >$0"
    )


def test_la_refundable_vs_ca_non_refundable():
    """LA refundable credit provides full face-value economic value; CA applies transfer discount."""
    result_ca = _run(FIXTURE_CA)
    result_la = _run(FIXTURE_LA)

    for iv in result_ca.incentive_results:
        if iv.get("program_slug") == "ca_film_30":
            assert iv["economic_value_usd"] < iv["total_credit_usd"], (
                "CA non-refundable credit must be discounted by transfer percentage"
            )

    for iv in result_la.incentive_results:
        if iv.get("program_slug") == "la_film_production":
            assert abs(iv["economic_value_usd"] - iv["total_credit_usd"]) < 1.0, (
                "LA refundable credit economic_value must equal face value"
            )
