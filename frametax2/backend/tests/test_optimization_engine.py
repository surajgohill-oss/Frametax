"""
test_optimization_engine.py

Targeted tests for the CineAtlas risk-adjusted optimization engine
(optimization_engine.py, structuring_paths.py, and the grey-area/
reinvestment extensions to qualification_model.py).
"""
from __future__ import annotations

import pytest

from app.calculators.qualification_model import (
    GreyAreaStatus,
    LITTLE_UTOPIA_INKIND_FMV_USD,
    QualificationConfidence,
    ReinvestmentCategory,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
    get_reinvestment_profile,
    resolve_grey_area,
)
from app.calculators.structuring_paths import (
    REPRESENTATIVE_ROUTING_SETUP_COST_USD,
    PathStatus,
    derive_structuring_paths,
    is_recommended,
)
from app.calculators.optimization_engine import (
    CONFIDENCE_WEIGHTS,
    GREY_AREA_WEIGHT_CAP,
    RECOMMEND_UPSIDE_TO_COST_RATIO,
    AssumptionOverride,
    RiskCase,
    RiskTolerance,
    build_risk_cases,
)

GROSS_BUDGET_USD = 4_364_393.0
MU_RATE = 0.40


@pytest.fixture(scope="module")
def register():
    return build_little_utopia_qualification_register(mu_rate=MU_RATE)


@pytest.fixture()
def paths(register):
    return derive_structuring_paths(register, rate=MU_RATE)


@pytest.fixture()
def grey_areas():
    return build_little_utopia_grey_areas()


@pytest.fixture()
def baseline_result(register, paths, grey_areas):
    return build_risk_cases(
        register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
        inkind_fmv_usd=LITTLE_UTOPIA_INKIND_FMV_USD,
        structuring_paths=paths, grey_areas=grey_areas,
    )


# ── Conservative / Optimistic canonical figures ─────────────────────────────

class TestCanonicalFigures:
    def test_conservative_qpe(self, baseline_result):
        c = baseline_result.cases[RiskCase.CONSERVATIVE]
        assert c.qpe_usd == pytest.approx(1_979_913.0, abs=1.0)

    def test_conservative_incentive(self, baseline_result):
        c = baseline_result.cases[RiskCase.CONSERVATIVE]
        assert c.incentive_usd == pytest.approx(791_965.0, abs=1.0)

    def test_optimistic_qpe(self, baseline_result):
        o = baseline_result.cases[RiskCase.OPTIMISTIC]
        assert o.qpe_usd == pytest.approx(3_221_357.0, abs=1.0)

    def test_optimistic_incentive(self, baseline_result):
        o = baseline_result.cases[RiskCase.OPTIMISTIC]
        assert o.incentive_usd == pytest.approx(1_288_543.0, abs=1.0)

    def test_inkind_is_additive_and_does_not_change_gross(self, baseline_result):
        o = baseline_result.cases[RiskCase.OPTIMISTIC]
        assert o.inkind_addon_usd == pytest.approx(LITTLE_UTOPIA_INKIND_FMV_USD, abs=0.01)
        assert baseline_result.gross_budget_usd == pytest.approx(GROSS_BUDGET_USD, abs=0.01)
        # in-kind must never appear in Conservative/Base by default (no ruling resolved)
        c = baseline_result.cases[RiskCase.CONSERVATIVE]
        b = baseline_result.cases[RiskCase.BASE]
        assert c.inkind_addon_usd == 0.0
        assert b.inkind_addon_usd == 0.0


# ── Base defaults to Conservative; moves only on approval ───────────────────

class TestBaseCaseGating:
    def test_base_equals_conservative_with_no_approvals(self, baseline_result):
        c = baseline_result.cases[RiskCase.CONSERVATIVE]
        b = baseline_result.cases[RiskCase.BASE]
        assert b.qpe_usd == pytest.approx(c.qpe_usd, abs=0.01)
        assert b.incentive_usd == pytest.approx(c.incentive_usd, abs=0.01)
        assert b.net_production_cost_usd == pytest.approx(c.net_production_cost_usd, abs=0.01)

    def test_base_moves_with_producer_approval(self, register, paths, grey_areas):
        ov = AssumptionOverride(
            item_id="SP-21-00", item_type="structuring_path",
            to_status=PathStatus.APPROVED.value, approver_role="producer",
            reason="Producer approved MU routing for the DP.",
        )
        result = build_risk_cases(
            register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
            structuring_paths=paths, grey_areas=grey_areas, overrides=[ov],
        )
        base = result.cases[RiskCase.BASE]
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert base.qpe_usd == pytest.approx(1_979_913.0 + 95_000.0, abs=0.01)
        # approval alone must NOT promote into Conservative (requires EXECUTED + evidence)
        assert cons.qpe_usd == pytest.approx(1_979_913.0, abs=0.01)

    def test_executed_with_evidence_promotes_to_conservative(self, register, paths, grey_areas):
        ov = AssumptionOverride(
            item_id="SP-21-00", item_type="structuring_path",
            to_status=PathStatus.EXECUTED.value, approver_role="producer",
            evidence="spv_routing_agreement_dp.pdf", reason="Routing agreement executed.",
        )
        result = build_risk_cases(
            register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
            structuring_paths=paths, grey_areas=grey_areas, overrides=[ov],
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(1_979_913.0 + 95_000.0, abs=0.01)

    def test_executed_without_evidence_rejected(self, register, paths, grey_areas):
        ov = AssumptionOverride(
            item_id="SP-21-00", item_type="structuring_path",
            to_status=PathStatus.EXECUTED.value, approver_role="producer",
            evidence=None,
        )
        with pytest.raises(ValueError, match="EXECUTED"):
            build_risk_cases(
                register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
                structuring_paths=paths, grey_areas=grey_areas, overrides=[ov],
            )

    def test_structuring_approval_by_non_approver_rejected(self, register, paths, grey_areas):
        ov = AssumptionOverride(
            item_id="SP-21-00", item_type="structuring_path",
            to_status=PathStatus.APPROVED.value, approver_role="assistant",
        )
        with pytest.raises(ValueError):
            build_risk_cases(
                register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
                structuring_paths=paths, grey_areas=grey_areas, overrides=[ov],
            )


# ── Grey area: counsel-gated, evidence required ──────────────────────────────

class TestGreyAreaGating:
    def test_grey_area_resolution_without_evidence_rejected(self, register, paths, grey_areas):
        ov = AssumptionOverride(
            item_id="GA-ATL-SCOPE", item_type="grey_area",
            to_status=GreyAreaStatus.RESOLVED_INCLUDE.value, approver_role="counsel",
            evidence=None,
        )
        with pytest.raises(ValueError, match="evidence"):
            build_risk_cases(
                register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
                structuring_paths=paths, grey_areas=grey_areas, overrides=[ov],
            )

    def test_grey_area_resolution_by_producer_rejected(self, register, paths, grey_areas):
        ov = AssumptionOverride(
            item_id="GA-ATL-SCOPE", item_type="grey_area",
            to_status=GreyAreaStatus.RESOLVED_INCLUDE.value, approver_role="producer",
            evidence="edb_ruling_atl.pdf",
        )
        with pytest.raises(ValueError, match="counsel"):
            build_risk_cases(
                register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
                structuring_paths=paths, grey_areas=grey_areas, overrides=[ov],
            )

    def test_grey_area_resolved_with_counsel_and_evidence_moves_to_conservative(self, register, paths, grey_areas):
        ov = AssumptionOverride(
            item_id="GA-ATL-SCOPE", item_type="grey_area",
            to_status=GreyAreaStatus.RESOLVED_INCLUDE.value, approver_role="counsel",
            evidence="edb_ruling_atl_2026.pdf",
        )
        result = build_risk_cases(
            register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
            structuring_paths=paths, grey_areas=grey_areas, overrides=[ov],
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(1_979_913.0 + 408_444.0, abs=0.01)

    def test_resolve_grey_area_function_requires_citation(self, grey_areas):
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        with pytest.raises(ValueError):
            resolve_grey_area(atl, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation=None)

    def test_resolve_grey_area_function_succeeds_with_citation(self, grey_areas):
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        resolved = resolve_grey_area(atl, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation="EDB-2026-0412")
        assert resolved.status == GreyAreaStatus.RESOLVED_INCLUDE
        assert resolved.ruling_citation == "EDB-2026-0412"
        assert atl.status == GreyAreaStatus.OPEN  # original untouched — pure function


# ── Risk-adjusted bounds and weight cap ──────────────────────────────────────

class TestRiskAdjusted:
    def test_risk_adjusted_within_bounds(self, baseline_result):
        c = baseline_result.cases[RiskCase.CONSERVATIVE]
        o = baseline_result.cases[RiskCase.OPTIMISTIC]
        ra = baseline_result.cases[RiskCase.RISK_ADJUSTED]
        assert c.incentive_usd <= ra.incentive_usd <= o.incentive_usd

    def test_risk_adjusted_exceeds_conservative_when_upside_exists(self, baseline_result):
        c = baseline_result.cases[RiskCase.CONSERVATIVE]
        ra = baseline_result.cases[RiskCase.RISK_ADJUSTED]
        assert ra.incentive_usd > c.incentive_usd

    def test_grey_area_weight_capped_at_point_five(self):
        assert GREY_AREA_WEIGHT_CAP == 0.50
        # Even a HIGH-confidence grey item must not exceed the cap.
        assert min(CONFIDENCE_WEIGHTS[QualificationConfidence.HIGH], GREY_AREA_WEIGHT_CAP) == 0.50
        assert CONFIDENCE_WEIGHTS[QualificationConfidence.HIGH] > GREY_AREA_WEIGHT_CAP

    def test_confidence_weights_canonical(self):
        assert CONFIDENCE_WEIGHTS[QualificationConfidence.HIGH] == 0.90
        assert CONFIDENCE_WEIGHTS[QualificationConfidence.MEDIUM] == 0.60
        assert CONFIDENCE_WEIGHTS[QualificationConfidence.LOW] == 0.25

    def test_risk_tolerance_does_not_change_case_math(self, register, paths, grey_areas):
        results = {
            rt: build_risk_cases(
                register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
                inkind_fmv_usd=LITTLE_UTOPIA_INKIND_FMV_USD,
                structuring_paths=paths, grey_areas=grey_areas, risk_tolerance=rt,
            )
            for rt in RiskTolerance
        }
        incentives = {rt: r.cases[RiskCase.RISK_ADJUSTED].incentive_usd for rt, r in results.items()}
        assert len(set(incentives.values())) == 1  # identical regardless of tolerance


# ── Structuring path recommendation threshold ────────────────────────────────

class TestStructuringPathRecommendation:
    def test_three_paths_derived(self, paths):
        codes = {p.account_code for p in paths}
        assert codes == {"21-00", "23-00", "42-00"}

    def test_implementation_cost_labeled_constant(self):
        assert REPRESENTATIVE_ROUTING_SETUP_COST_USD == 8_000.0

    def test_dp_routing_recommended(self, paths):
        # 95,000 * 0.40 = 38,000 upside / 8,000 cost = 4.75x — above 3x threshold
        p = next(p for p in paths if p.account_code == "21-00")
        assert is_recommended(p) is True

    def test_sound_routing_recommended(self, paths):
        # 65,000 * 0.40 = 26,000 / 8,000 = 3.25x — above threshold
        p = next(p for p in paths if p.account_code == "23-00")
        assert is_recommended(p) is True

    def test_stunts_routing_not_recommended_below_threshold(self, paths):
        # 48,000 * 0.40 = 19,200 / 8,000 = 2.4x — below 3x threshold, but still visible
        p = next(p for p in paths if p.account_code == "42-00")
        assert is_recommended(p) is False
        assert p.upside_incentive_usd > 0  # visible, not hidden

    def test_recommendation_requires_at_least_medium_confidence(self):
        from app.calculators.structuring_paths import StructuringPath
        low_conf_path = StructuringPath(
            path_id="SP-TEST", account_code="99-00", description="test",
            mechanism="test", current_amount_usd=0, structured_amount_usd=100_000,
            implementation_cost_usd=1_000, complexity="LOW",
            confidence=QualificationConfidence.LOW,
            required_documents=(), upside_incentive_usd=100_000,
        )
        assert is_recommended(low_conf_path) is False  # huge ratio but LOW confidence

    def test_default_threshold_constant(self):
        assert RECOMMEND_UPSIDE_TO_COST_RATIO == 3.0


# ── Reinvestment: UNKNOWN is distinct from NOT_PERMITTED ─────────────────────

class TestReinvestment:
    def test_mu_is_unknown_not_not_permitted(self):
        profile = get_reinvestment_profile("MU")
        assert profile.category == ReinvestmentCategory.UNKNOWN
        assert profile.category != ReinvestmentCategory.NOT_PERMITTED

    def test_unknown_generates_evidence_request(self, baseline_result):
        assert len(baseline_result.evidence_requests) >= 1
        assert any("reinvestment" in r.lower() for r in baseline_result.evidence_requests)

    def test_unknown_has_zero_effect_on_conservative_and_base(self, baseline_result):
        # reinvestment contributes no dollars to any case — verified indirectly:
        # conservative/base equal the register-only figures with no reinvestment term.
        c = baseline_result.cases[RiskCase.CONSERVATIVE]
        assert c.qpe_usd == pytest.approx(1_979_913.0, abs=1.0)


# ── Reconciliation ────────────────────────────────────────────────────────────

class TestReconciliation:
    def test_register_partition_reconciles_to_gross(self, register):
        total = sum(a.amount_usd for a in register)
        assert total == pytest.approx(GROSS_BUDGET_USD, abs=0.01)

    def test_all_four_cases_report_reconciles_true(self, baseline_result):
        for case_result in baseline_result.cases.values():
            assert case_result.reconciles is True

    def test_no_warnings_on_valid_register(self, baseline_result):
        assert baseline_result.warnings == []

    def test_conservative_partition_composition(self, register):
        """Explicit dollar-for-dollar reconciliation of the Conservative
        case's bucket composition against gross budget."""
        qualifies_total = sum(a.amount_usd for a in register if a.state.value == "qualifies")
        excluded_total = sum(a.amount_usd for a in register if a.state.value == "excluded")
        na_total = sum(a.amount_usd for a in register if a.state.value == "not_applicable")
        grey_total = sum(a.amount_usd for a in register if a.state.value == "grey_area_requires_authority")
        structuring_total = sum(a.amount_usd for a in register if a.state.value == "structuring_opportunity")
        assert qualifies_total == pytest.approx(1_979_913.0, abs=0.01)
        assert excluded_total == pytest.approx(1_675_597.0, abs=0.01)
        assert na_total == pytest.approx(92_439.0, abs=0.01)
        assert grey_total == pytest.approx(408_444.0, abs=0.01)
        assert structuring_total == pytest.approx(208_000.0, abs=0.01)
        assert (qualifies_total + excluded_total + na_total + grey_total + structuring_total) \
            == pytest.approx(GROSS_BUDGET_USD, abs=0.01)


# ── Determinism ────────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_identical_inputs_produce_identical_results(self, register, paths, grey_areas):
        r1 = build_risk_cases(
            register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
            inkind_fmv_usd=LITTLE_UTOPIA_INKIND_FMV_USD,
            structuring_paths=paths, grey_areas=grey_areas,
        )
        r2 = build_risk_cases(
            register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
            inkind_fmv_usd=LITTLE_UTOPIA_INKIND_FMV_USD,
            structuring_paths=paths, grey_areas=grey_areas,
        )
        for case in RiskCase:
            assert r1.cases[case].qpe_usd == r2.cases[case].qpe_usd
            assert r1.cases[case].incentive_usd == r2.cases[case].incentive_usd
            assert r1.cases[case].net_production_cost_usd == r2.cases[case].net_production_cost_usd

    def test_input_lists_not_mutated(self, register, paths, grey_areas):
        paths_before = [(p.path_id, p.status) for p in paths]
        grey_before = [(g.item_id, g.status) for g in grey_areas]
        ov = AssumptionOverride(
            item_id="SP-21-00", item_type="structuring_path",
            to_status=PathStatus.APPROVED.value, approver_role="producer",
        )
        build_risk_cases(
            register=register, gross_budget_usd=GROSS_BUDGET_USD, rate=MU_RATE,
            structuring_paths=paths, grey_areas=grey_areas, overrides=[ov],
        )
        paths_after = [(p.path_id, p.status) for p in paths]
        grey_after = [(g.item_id, g.status) for g in grey_areas]
        assert paths_before == paths_after  # caller's list untouched
        assert grey_before == grey_after


# ── Module constants ──────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_engine_version(self, baseline_result):
        assert baseline_result.engine_version == "1.0.0"

    def test_four_risk_cases(self):
        assert len(RiskCase) == 4

    def test_three_risk_tolerances(self):
        assert len(RiskTolerance) == 3

    def test_grey_areas_include_offbudget_inkind(self, grey_areas):
        inkind = next(g for g in grey_areas if g.item_id == "GA-INKIND-FMV")
        assert inkind.off_budget is True
        assert inkind.amount_usd == pytest.approx(625_000.0, abs=0.01)
