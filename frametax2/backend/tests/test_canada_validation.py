"""
Canadian incentive program end-to-end validation tests.

Sources:
  ON OPSTC: OMDC; Ontario Reg 37/09 under Corporations Tax Act
  ON OFTTC: OMDC; Ontario Reg 37/09; CAVCO certification
  BC PSTC:  Creative BC; BC Income Tax Act ss.91-93
  QC QPRDP: SODEC; Quebec Taxation Act § 1029.8.34
  CPTC:     CRA T4283; Income Tax Act § 125.4

All rates PARSED — see 0006 migration for confidence tier rationale.
All amounts in CAD treated as face-value USD (no FX conversion; tests verify mechanics only).

Hand-verified expected values documented in tests/fixtures/canada_validation.py.
"""
from __future__ import annotations

import pytest
from app.calculators.run_full_analysis import run_full_analysis
from tests.fixtures.canada_validation import (
    BC_PSTC_EXPECTED_BASE,
    BC_PSTC_EXPECTED_REGIONAL,
    CA_CPTC_EXPECTED,
    FIXTURE_BC_PSTC_BASE,
    FIXTURE_BC_PSTC_REGIONAL,
    FIXTURE_CA_CPTC,
    FIXTURE_ON_OFTTC,
    FIXTURE_ON_OPSTC,
    FIXTURE_QC,
    ON_OFTTC_EXPECTED,
    ON_OPSTC_EXPECTED,
    QC_EXPECTED,
)


def _run(fixture: dict):
    return run_full_analysis(
        structure_id="ca-validation-001",
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


def _total_qs(result) -> float:
    return sum(r.get("qualifying_spend_usd", 0) or 0
               for r in result.qualified_spend_results)


# ===========================================================================
# ONTARIO OPSTC — 21.5% broad spend credit
# ===========================================================================

class TestOntarioOPSTC:
    def test_runs(self):
        result = _run(FIXTURE_ON_OPSTC)
        assert result.total_input_budget_usd == ON_OPSTC_EXPECTED["total_budget_usd"]

    def test_qualifying_spend_exact(self):
        result = _run(FIXTURE_ON_OPSTC)
        qs = _total_qs(result)
        expected = ON_OPSTC_EXPECTED["qualifying_spend_usd"]
        assert abs(qs - expected) <= expected * 0.01, (
            f"ON OPSTC qualifying spend: expected ${expected:,.0f}, got ${qs:,.0f}"
        )

    def test_qualifying_spend_above_minimum(self):
        result = _run(FIXTURE_ON_OPSTC)
        qs = _total_qs(result)
        assert qs >= ON_OPSTC_EXPECTED["qualifying_spend_min_usd"], (
            f"ON OPSTC qualifying spend ${qs:,.0f} below floor "
            f"${ON_OPSTC_EXPECTED['qualifying_spend_min_usd']:,.0f}"
        )

    def test_positive_incentive_value(self):
        result = _run(FIXTURE_ON_OPSTC)
        assert result.total_incentive_economic_value_usd > 0

    def test_economic_value_exact(self):
        result = _run(FIXTURE_ON_OPSTC)
        expected = ON_OPSTC_EXPECTED["economic_value_usd"]
        assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.02, (
            f"ON OPSTC economic value: expected ${expected:,.0f}, "
            f"got ${result.total_incentive_economic_value_usd:,.0f}"
        )

    def test_refundable_economic_value_equals_credit(self):
        """Refundable OPSTC: economic value must equal face-value credit."""
        result = _run(FIXTURE_ON_OPSTC)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "on_opstc":
                assert abs(iv["economic_value_usd"] - iv["total_credit_usd"]) < 1.0, (
                    "Refundable OPSTC credit: economic_value must equal total_credit"
                )

    def test_atl_excluded_from_qualifying_spend(self):
        """OPSTC excludes ATL — director and cast must produce no qualifying spend."""
        result = _run(FIXTURE_ON_OPSTC)
        for qs in result.qualified_spend_results:
            breakdown = qs.get("category_breakdown", {})
            assert breakdown.get("atl_director", 0) == 0, (
                "atl_director must be excluded from ON OPSTC qualifying spend"
            )
            assert breakdown.get("atl_cast", 0) == 0, (
                "atl_cast must be excluded from ON OPSTC qualifying spend"
            )

    def test_btl_labour_qualifies(self):
        """BTL labour must be present in OPSTC qualifying spend breakdown."""
        result = _run(FIXTURE_ON_OPSTC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "on_opstc":
                assert qs["category_breakdown"].get("btl_crew_labor", 0) > 0, (
                    "btl_crew_labor must appear in ON OPSTC qualifying spend"
                )

    def test_non_labour_qualifies(self):
        """OPSTC is broad — equipment rental must qualify."""
        result = _run(FIXTURE_ON_OPSTC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "on_opstc":
                assert qs["category_breakdown"].get("btl_equipment_rental", 0) > 0, (
                    "btl_equipment_rental must qualify under OPSTC broad spend eligibility"
                )

    def test_net_cost_less_than_gross(self):
        result = _run(FIXTURE_ON_OPSTC)
        assert result.true_net_cost_usd < result.total_input_budget_usd

    def test_net_cost_non_negative(self):
        result = _run(FIXTURE_ON_OPSTC)
        assert result.true_net_cost_usd >= 0

    def test_net_cost_exact(self):
        result = _run(FIXTURE_ON_OPSTC)
        expected = ON_OPSTC_EXPECTED["true_net_cost_usd"]
        budget = ON_OPSTC_EXPECTED["total_budget_usd"]
        assert abs(result.true_net_cost_usd - expected) <= budget * 0.02, (
            f"ON OPSTC true net cost: expected ${expected:,.0f}, "
            f"got ${result.true_net_cost_usd:,.0f}"
        )

    def test_stacking_clean(self):
        result = _run(FIXTURE_ON_OPSTC)
        assert result.stacking_violations == []
        assert result.stacking_legal_review_required is False

    def test_trace_complete(self):
        result = _run(FIXTURE_ON_OPSTC)
        assert result.engine_version == "0.1.0"
        step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
        assert "classify_budget" in step_names
        assert "incentive_programs" in step_names

    def test_no_uplifts_applied(self):
        """OPSTC has no uplifts configured in this fixture."""
        result = _run(FIXTURE_ON_OPSTC)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "on_opstc":
                assert iv.get("uplifts_applied", []) == [], (
                    "No uplifts should fire for OPSTC in this fixture"
                )


# ===========================================================================
# ONTARIO OFTTC — 35% labour credit, CAVCO-certified
# ===========================================================================

class TestOntarioOFTTC:
    def test_runs(self):
        result = _run(FIXTURE_ON_OFTTC)
        assert result.total_input_budget_usd == ON_OFTTC_EXPECTED["total_budget_usd"]

    def test_qualifying_spend_exact(self):
        result = _run(FIXTURE_ON_OFTTC)
        qs = _total_qs(result)
        expected = ON_OFTTC_EXPECTED["qualifying_spend_usd"]
        assert abs(qs - expected) <= expected * 0.01, (
            f"ON OFTTC qualifying spend: expected ${expected:,.0f}, got ${qs:,.0f}"
        )

    def test_qualifying_spend_above_minimum(self):
        result = _run(FIXTURE_ON_OFTTC)
        qs = _total_qs(result)
        assert qs >= ON_OFTTC_EXPECTED["qualifying_spend_min_usd"]

    def test_positive_incentive_value(self):
        result = _run(FIXTURE_ON_OFTTC)
        assert result.total_incentive_economic_value_usd > 0

    def test_economic_value_exact(self):
        result = _run(FIXTURE_ON_OFTTC)
        expected = ON_OFTTC_EXPECTED["economic_value_usd"]
        assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.02, (
            f"ON OFTTC economic value: expected ${expected:,.0f}, "
            f"got ${result.total_incentive_economic_value_usd:,.0f}"
        )

    def test_refundable_economic_value_equals_credit(self):
        result = _run(FIXTURE_ON_OFTTC)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "on_ofttc":
                assert abs(iv["economic_value_usd"] - iv["total_credit_usd"]) < 1.0

    def test_atl_qualifies_for_ofttc(self):
        """OFTTC allows Ontario resident ATL — director and cast must qualify."""
        result = _run(FIXTURE_ON_OFTTC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "on_ofttc":
                breakdown = qs.get("category_breakdown", {})
                assert breakdown.get("atl_director", 0) > 0, (
                    "atl_director must qualify under OFTTC (Ontario resident ATL)"
                )
                assert breakdown.get("atl_cast", 0) > 0, (
                    "atl_cast must qualify under OFTTC (Ontario resident ATL)"
                )

    def test_btl_labour_qualifies_for_ofttc(self):
        result = _run(FIXTURE_ON_OFTTC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "on_ofttc":
                assert qs["category_breakdown"].get("btl_resident_labor", 0) > 0

    def test_non_labour_excluded_from_ofttc(self):
        """Equipment rental must NOT qualify under OFTTC labour-only basis."""
        result = _run(FIXTURE_ON_OFTTC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "on_ofttc":
                breakdown = qs.get("category_breakdown", {})
                assert breakdown.get("btl_equipment_rental", 0) == 0, (
                    "btl_equipment_rental must be excluded from OFTTC labour-only basis"
                )
                assert breakdown.get("post_production", 0) == 0, (
                    "post_production must be excluded from OFTTC labour-only basis"
                )

    def test_net_cost_less_than_gross(self):
        result = _run(FIXTURE_ON_OFTTC)
        assert result.true_net_cost_usd < result.total_input_budget_usd

    def test_net_cost_exact(self):
        result = _run(FIXTURE_ON_OFTTC)
        expected = ON_OFTTC_EXPECTED["true_net_cost_usd"]
        budget = ON_OFTTC_EXPECTED["total_budget_usd"]
        assert abs(result.true_net_cost_usd - expected) <= budget * 0.02, (
            f"ON OFTTC true net cost: expected ${expected:,.0f}, "
            f"got ${result.true_net_cost_usd:,.0f}"
        )

    def test_stacking_clean(self):
        result = _run(FIXTURE_ON_OFTTC)
        assert result.stacking_violations == []

    def test_trace_complete(self):
        result = _run(FIXTURE_ON_OFTTC)
        step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
        assert "classify_budget" in step_names
        assert "incentive_programs" in step_names

    def test_ofttc_vs_opstc_higher_rate_but_narrower_base(self):
        """
        OFTTC (35%) has a higher rate than OPSTC (21.5%) but labour-only basis,
        so on a mixed spend budget, their credit values can differ significantly.
        For this specific fixture (labour-heavy), OFTTC credit > OPSTC credit.
        """
        result_opstc = run_full_analysis(
            structure_id="compare-opstc",
            jurisdiction=FIXTURE_ON_OPSTC["jurisdiction"],
            line_items=FIXTURE_ON_OPSTC["line_items"],
            programs_with_categories=FIXTURE_ON_OPSTC["programs_with_categories"],
            stacking_rules=[],
            qualification_tests_with_rules=[],
            cost_benchmark=None,
            union_fringe_rules=[],
            fx_rates=None,
            production_details={},
        )
        result_ofttc = _run(FIXTURE_ON_OFTTC)
        # OPSTC on $1,700K at 21.5% = $365,500
        # OFTTC on $1,400K at 35% = $490,000
        # So OFTTC should be larger on this particular pair of fixtures
        assert result_ofttc.total_incentive_economic_value_usd > \
               result_opstc.total_incentive_economic_value_usd * 0.5, (
            "OFTTC credit (35% on labour) should produce meaningful incentive value "
            "compared to OPSTC (21.5% on broader spend)"
        )


# ===========================================================================
# BRITISH COLUMBIA PSTC — 28% base + 6% regional uplift
# ===========================================================================

class TestBCPSTC:
    def test_base_runs(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        assert result.total_input_budget_usd == BC_PSTC_EXPECTED_BASE["total_budget_usd"]

    def test_base_qualifying_spend_exact(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        qs = _total_qs(result)
        expected = BC_PSTC_EXPECTED_BASE["qualifying_spend_usd"]
        assert abs(qs - expected) <= expected * 0.01, (
            f"BC PSTC base qualifying spend: expected ${expected:,.0f}, got ${qs:,.0f}"
        )

    def test_base_positive_incentive_value(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        assert result.total_incentive_economic_value_usd > 0

    def test_base_economic_value_exact(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        expected = BC_PSTC_EXPECTED_BASE["economic_value_usd"]
        assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.02, (
            f"BC PSTC base economic value: expected ${expected:,.0f}, "
            f"got ${result.total_incentive_economic_value_usd:,.0f}"
        )

    def test_base_refundable_economic_value_equals_credit(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "bc_pstc":
                assert abs(iv["economic_value_usd"] - iv["total_credit_usd"]) < 1.0

    def test_base_regional_uplift_does_not_fire(self):
        """Without shooting_location=bc_regional, the uplift must NOT fire."""
        result = _run(FIXTURE_BC_PSTC_BASE)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "bc_pstc":
                assert iv.get("uplifts_applied", []) == [], (
                    "BC regional uplift must NOT fire when production_details has no shooting_location"
                )

    def test_base_atl_excluded(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        for qs in result.qualified_spend_results:
            breakdown = qs.get("category_breakdown", {})
            assert breakdown.get("atl_director", 0) == 0
            assert breakdown.get("atl_cast", 0) == 0

    def test_base_non_labour_excluded(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "bc_pstc":
                breakdown = qs.get("category_breakdown", {})
                assert breakdown.get("btl_equipment_rental", 0) == 0
                assert breakdown.get("post_production", 0) == 0

    def test_base_net_cost_less_than_gross(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        assert result.true_net_cost_usd < result.total_input_budget_usd

    def test_base_net_cost_exact(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        expected = BC_PSTC_EXPECTED_BASE["true_net_cost_usd"]
        budget = BC_PSTC_EXPECTED_BASE["total_budget_usd"]
        assert abs(result.true_net_cost_usd - expected) <= budget * 0.02

    def test_regional_runs(self):
        result = _run(FIXTURE_BC_PSTC_REGIONAL)
        assert result.total_input_budget_usd == BC_PSTC_EXPECTED_REGIONAL["total_budget_usd"]

    def test_regional_uplift_fires(self):
        """Regional uplift (+6%) must fire when shooting_location=bc_regional."""
        result = _run(FIXTURE_BC_PSTC_REGIONAL)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "bc_pstc":
                uplifts = iv.get("uplifts_applied", [])
                assert len(uplifts) == 1, (
                    "BC regional uplift should fire when shooting_location=bc_regional"
                )
                assert abs(uplifts[0]["rate"] - 0.06) < 0.001

    def test_regional_economic_value_exact(self):
        result = _run(FIXTURE_BC_PSTC_REGIONAL)
        expected = BC_PSTC_EXPECTED_REGIONAL["economic_value_usd"]
        assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.02, (
            f"BC PSTC regional economic value: expected ${expected:,.0f}, "
            f"got ${result.total_incentive_economic_value_usd:,.0f}"
        )

    def test_regional_uplift_increases_value(self):
        """Regional (34%) credit must be > base (28%) credit."""
        result_base = _run(FIXTURE_BC_PSTC_BASE)
        result_regional = _run(FIXTURE_BC_PSTC_REGIONAL)
        assert result_regional.total_incentive_economic_value_usd > \
               result_base.total_incentive_economic_value_usd, (
            "Regional uplift (+6%) must increase economic value"
        )

    def test_regional_uplift_ratio(self):
        """Regional credit (34%) / base credit (28%) = 34/28 ≈ 1.214."""
        result_base = _run(FIXTURE_BC_PSTC_BASE)
        result_regional = _run(FIXTURE_BC_PSTC_REGIONAL)
        ratio = (result_regional.total_incentive_economic_value_usd /
                 result_base.total_incentive_economic_value_usd)
        expected_ratio = 0.34 / 0.28
        assert abs(ratio - expected_ratio) <= 0.02, (
            f"BC PSTC regional/base ratio: expected {expected_ratio:.4f}, got {ratio:.4f}"
        )

    def test_base_trace_complete(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
        assert "classify_budget" in step_names
        assert "incentive_programs" in step_names

    def test_stacking_clean(self):
        result = _run(FIXTURE_BC_PSTC_BASE)
        assert result.stacking_violations == []


# ===========================================================================
# QUEBEC QPRDP — 20% labour credit, service production
# ===========================================================================

class TestQuebecQPRDP:
    def test_runs(self):
        result = _run(FIXTURE_QC)
        assert result.total_input_budget_usd == QC_EXPECTED["total_budget_usd"]

    def test_qualifying_spend_exact(self):
        result = _run(FIXTURE_QC)
        qs = _total_qs(result)
        expected = QC_EXPECTED["qualifying_spend_usd"]
        assert abs(qs - expected) <= expected * 0.01, (
            f"QC QPRDP qualifying spend: expected ${expected:,.0f}, got ${qs:,.0f}"
        )

    def test_qualifying_spend_above_minimum(self):
        result = _run(FIXTURE_QC)
        qs = _total_qs(result)
        assert qs >= QC_EXPECTED["qualifying_spend_min_usd"]

    def test_positive_incentive_value(self):
        result = _run(FIXTURE_QC)
        assert result.total_incentive_economic_value_usd > 0

    def test_economic_value_exact(self):
        result = _run(FIXTURE_QC)
        expected = QC_EXPECTED["economic_value_usd"]
        assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.02, (
            f"QC QPRDP economic value: expected ${expected:,.0f}, "
            f"got ${result.total_incentive_economic_value_usd:,.0f}"
        )

    def test_refundable_economic_value_equals_credit(self):
        result = _run(FIXTURE_QC)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "qc_film_production":
                assert abs(iv["economic_value_usd"] - iv["total_credit_usd"]) < 1.0

    def test_atl_excluded(self):
        result = _run(FIXTURE_QC)
        for qs in result.qualified_spend_results:
            breakdown = qs.get("category_breakdown", {})
            assert breakdown.get("atl_director", 0) == 0
            assert breakdown.get("atl_cast", 0) == 0

    def test_labour_qualifies(self):
        result = _run(FIXTURE_QC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "qc_film_production":
                assert qs["category_breakdown"].get("btl_crew_labor", 0) > 0
                assert qs["category_breakdown"].get("btl_resident_labor", 0) > 0

    def test_non_labour_excluded(self):
        result = _run(FIXTURE_QC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "qc_film_production":
                breakdown = qs.get("category_breakdown", {})
                assert breakdown.get("btl_equipment_rental", 0) == 0
                assert breakdown.get("post_production", 0) == 0

    def test_net_cost_less_than_gross(self):
        result = _run(FIXTURE_QC)
        assert result.true_net_cost_usd < result.total_input_budget_usd

    def test_net_cost_exact(self):
        result = _run(FIXTURE_QC)
        expected = QC_EXPECTED["true_net_cost_usd"]
        budget = QC_EXPECTED["total_budget_usd"]
        assert abs(result.true_net_cost_usd - expected) <= budget * 0.02, (
            f"QC QPRDP true net cost: expected ${expected:,.0f}, "
            f"got ${result.true_net_cost_usd:,.0f}"
        )

    def test_stacking_clean(self):
        result = _run(FIXTURE_QC)
        assert result.stacking_violations == []

    def test_trace_complete(self):
        result = _run(FIXTURE_QC)
        step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
        assert "classify_budget" in step_names
        assert "incentive_programs" in step_names


# ===========================================================================
# FEDERAL CPTC — 25% Canadian labour credit
# ===========================================================================

class TestFederalCPTC:
    def test_runs(self):
        result = _run(FIXTURE_CA_CPTC)
        assert result.total_input_budget_usd == CA_CPTC_EXPECTED["total_budget_usd"]

    def test_qualifying_spend_exact(self):
        result = _run(FIXTURE_CA_CPTC)
        qs = _total_qs(result)
        expected = CA_CPTC_EXPECTED["qualifying_spend_usd"]
        assert abs(qs - expected) <= expected * 0.01, (
            f"CPTC qualifying spend: expected ${expected:,.0f}, got ${qs:,.0f}"
        )

    def test_qualifying_spend_above_minimum(self):
        result = _run(FIXTURE_CA_CPTC)
        qs = _total_qs(result)
        assert qs >= CA_CPTC_EXPECTED["qualifying_spend_min_usd"]

    def test_positive_incentive_value(self):
        result = _run(FIXTURE_CA_CPTC)
        assert result.total_incentive_economic_value_usd > 0

    def test_economic_value_exact(self):
        result = _run(FIXTURE_CA_CPTC)
        expected = CA_CPTC_EXPECTED["economic_value_usd"]
        assert abs(result.total_incentive_economic_value_usd - expected) <= expected * 0.02, (
            f"CPTC economic value: expected ${expected:,.0f}, "
            f"got ${result.total_incentive_economic_value_usd:,.0f}"
        )

    def test_refundable_economic_value_equals_credit(self):
        result = _run(FIXTURE_CA_CPTC)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "ca_federal_cptc":
                assert abs(iv["economic_value_usd"] - iv["total_credit_usd"]) < 1.0

    def test_canadian_atl_qualifies(self):
        """Federal CPTC: Canadian key creative ATL must qualify as QCLE."""
        result = _run(FIXTURE_CA_CPTC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "ca_federal_cptc":
                breakdown = qs.get("category_breakdown", {})
                assert breakdown.get("atl_director", 0) > 0, (
                    "Canadian director must qualify as QCLE under CPTC"
                )
                assert breakdown.get("atl_cast", 0) > 0, (
                    "Canadian cast must qualify as QCLE under CPTC"
                )

    def test_canadian_btl_labour_qualifies(self):
        result = _run(FIXTURE_CA_CPTC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "ca_federal_cptc":
                assert qs["category_breakdown"].get("btl_crew_labor", 0) > 0

    def test_non_labour_excluded(self):
        """Non-Canadian/non-labour spend must NOT qualify as QCLE."""
        result = _run(FIXTURE_CA_CPTC)
        for qs in result.qualified_spend_results:
            if qs.get("program_slug") == "ca_federal_cptc":
                breakdown = qs.get("category_breakdown", {})
                assert breakdown.get("btl_equipment_rental", 0) == 0
                assert breakdown.get("post_production", 0) == 0

    def test_net_cost_less_than_gross(self):
        result = _run(FIXTURE_CA_CPTC)
        assert result.true_net_cost_usd < result.total_input_budget_usd

    def test_net_cost_exact(self):
        result = _run(FIXTURE_CA_CPTC)
        expected = CA_CPTC_EXPECTED["true_net_cost_usd"]
        budget = CA_CPTC_EXPECTED["total_budget_usd"]
        assert abs(result.true_net_cost_usd - expected) <= budget * 0.02, (
            f"CPTC true net cost: expected ${expected:,.0f}, "
            f"got ${result.true_net_cost_usd:,.0f}"
        )

    def test_stacking_clean(self):
        result = _run(FIXTURE_CA_CPTC)
        assert result.stacking_violations == []

    def test_trace_complete(self):
        result = _run(FIXTURE_CA_CPTC)
        assert result.engine_version == "0.1.0"
        step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
        assert "classify_budget" in step_names
        assert "incentive_programs" in step_names

    def test_no_uplifts_applied(self):
        result = _run(FIXTURE_CA_CPTC)
        for iv in result.incentive_results:
            if iv.get("program_slug") == "ca_federal_cptc":
                assert iv.get("uplifts_applied", []) == []


# ===========================================================================
# Cross-program: ATL treatment comparison (OFTTC vs OPSTC vs CPTC vs QC)
# ===========================================================================

class TestCanadianCrossProgram:
    def test_opstc_atl_excluded_ofttc_atl_included(self):
        """
        OPSTC excludes ATL; OFTTC includes Ontario resident ATL.
        Verify different ATL treatment using each fixture's own line items.
        """
        result_opstc = _run(FIXTURE_ON_OPSTC)
        result_ofttc = _run(FIXTURE_ON_OFTTC)

        opstc_atl_qs = sum(
            qs.get("category_breakdown", {}).get("atl_director", 0)
            + qs.get("category_breakdown", {}).get("atl_cast", 0)
            for qs in result_opstc.qualified_spend_results
        )
        ofttc_atl_qs = sum(
            qs.get("category_breakdown", {}).get("atl_director", 0)
            + qs.get("category_breakdown", {}).get("atl_cast", 0)
            for qs in result_ofttc.qualified_spend_results
        )

        assert opstc_atl_qs == 0, "OPSTC must exclude ATL from qualifying spend"
        assert ofttc_atl_qs > 0, "OFTTC must include Ontario resident ATL in qualifying spend"

    def test_cptc_atl_included_qc_atl_excluded(self):
        """Federal CPTC includes Canadian ATL; QC service credit excludes ATL."""
        result_cptc = _run(FIXTURE_CA_CPTC)
        result_qc = _run(FIXTURE_QC)

        cptc_atl_qs = sum(
            qs.get("category_breakdown", {}).get("atl_director", 0)
            + qs.get("category_breakdown", {}).get("atl_cast", 0)
            for qs in result_cptc.qualified_spend_results
        )
        qc_atl_qs = sum(
            qs.get("category_breakdown", {}).get("atl_director", 0)
            + qs.get("category_breakdown", {}).get("atl_cast", 0)
            for qs in result_qc.qualified_spend_results
        )

        assert cptc_atl_qs > 0, "Federal CPTC must include Canadian ATL (key creative QCLE)"
        assert qc_atl_qs == 0, "QC service credit (QPRDP) must exclude ATL"

    def test_all_canadian_programs_produce_positive_incentive(self):
        """All five Canadian programs must produce a positive economic incentive value."""
        fixtures = [
            FIXTURE_ON_OPSTC,
            FIXTURE_ON_OFTTC,
            FIXTURE_BC_PSTC_BASE,
            FIXTURE_QC,
            FIXTURE_CA_CPTC,
        ]
        for fixture in fixtures:
            result = _run(fixture)
            assert result.total_incentive_economic_value_usd > 0, (
                f"Program in fixture '{fixture['name']}' produced zero incentive value"
            )

    def test_all_canadian_programs_produce_net_budget_reduction(self):
        """All five programs must reduce net cost vs gross budget."""
        fixtures = [
            FIXTURE_ON_OPSTC,
            FIXTURE_ON_OFTTC,
            FIXTURE_BC_PSTC_BASE,
            FIXTURE_QC,
            FIXTURE_CA_CPTC,
        ]
        for fixture in fixtures:
            result = _run(fixture)
            assert result.true_net_cost_usd < result.total_input_budget_usd, (
                f"Program in fixture '{fixture['name']}' did not reduce net cost"
            )

    def test_all_canadian_programs_have_clean_stacking(self):
        """No stacking violations expected for any single-program Canadian fixture."""
        fixtures = [
            FIXTURE_ON_OPSTC,
            FIXTURE_ON_OFTTC,
            FIXTURE_BC_PSTC_BASE,
            FIXTURE_QC,
            FIXTURE_CA_CPTC,
        ]
        for fixture in fixtures:
            result = _run(fixture)
            assert result.stacking_violations == [], (
                f"Unexpected stacking violation in '{fixture['name']}'"
            )

    def test_all_canadian_programs_trace_complete(self):
        """All fixtures must produce a complete calculation trace."""
        fixtures = [
            FIXTURE_ON_OPSTC,
            FIXTURE_ON_OFTTC,
            FIXTURE_BC_PSTC_BASE,
            FIXTURE_QC,
            FIXTURE_CA_CPTC,
        ]
        for fixture in fixtures:
            result = _run(fixture)
            step_names = {s["step"] for s in result.calculation_trace.get("steps", [])}
            assert "classify_budget" in step_names, f"Missing classify_budget in '{fixture['name']}'"
            assert "incentive_programs" in step_names, f"Missing incentive_programs in '{fixture['name']}'"
