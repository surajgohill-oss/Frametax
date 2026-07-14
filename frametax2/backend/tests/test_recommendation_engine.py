"""
test_recommendation_engine.py

Targeted tests for Phase 7D-1..7D-4 — the Production Optimization
Recommendation Engine core (recommendation_engine.py). Covers object
validation, the creative guardrail, FINANCIAL/STRUCTURAL generation,
dependency preservation, pricing, two-stage ranking, lifecycle/gates,
and non-mutation of every consumed engine.
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.opportunity_discovery import discover_all_opportunities
from app.calculators.optimization_engine import RiskCase
from app.calculators.qualification_model import (
    QualificationConfidence,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)
from app.calculators.structuring_paths import derive_structuring_paths

from app.calculators.recommendation_engine import (
    RECOMMENDATION_ENGINE_VERSION,
    ApprovalGate,
    CreativeElement,
    CreativeImpact,
    Recommendation,
    RecommendationDomain,
    RecommendationRankingResult,
    RecommendationStatus,
    RecommendationTier,
    RecommendationType,
    Reversibility,
    accept_recommendation,
    classify_tier,
    decline_recommendation,
    generate_financial_recommendations,
    generate_recommendations,
    generate_structural_recommendations,
    price_recommendations,
    rank_recommendations,
    submit_for_review,
    supersede_recommendation,
)

MU_RATE = 0.40
MU_GROSS_BUDGET = 4_364_393.0


@pytest.fixture(scope="module")
def graph():
    return build_jurisdiction_graph(mu_rate=MU_RATE)


@pytest.fixture(scope="module")
def collection(graph):
    return discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE, graph=graph)


@pytest.fixture()
def register():
    return build_little_utopia_qualification_register(mu_rate=MU_RATE)


@pytest.fixture()
def grey_areas():
    return build_little_utopia_grey_areas()


@pytest.fixture()
def structuring_paths(register):
    return derive_structuring_paths(register, rate=MU_RATE)


@pytest.fixture()
def recommendations(collection):
    return generate_recommendations(collection)


@pytest.fixture()
def priced_recommendations(recommendations, register, grey_areas, structuring_paths):
    recs = copy.deepcopy(recommendations)
    price_recommendations(
        recs, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
        all_structuring_paths=structuring_paths, all_grey_areas=grey_areas,
    )
    return recs


def _minimal_financial(**overrides) -> Recommendation:
    defaults = dict(
        recommendation_id="REC-X", recommendation_type=RecommendationType.RESOLVE_GREY_AREA,
        domain=RecommendationDomain.FINANCIAL, headline="h", detail="d",
    )
    defaults.update(overrides)
    return Recommendation(**defaults)


def _valid_creative(**overrides) -> Recommendation:
    defaults = dict(
        recommendation_id="REC-CREATIVE-1", recommendation_type=RecommendationType.KEY_TALENT_NATIONALITY,
        domain=RecommendationDomain.CREATIVE,
        headline="Casting a UK-qualified lead is a trade-off worth stating plainly",
        detail="Improves BFI cultural test points; not a requirement, a trade-off for the producer to weigh.",
        affected_creative_elements=(CreativeElement.LEAD_ACTOR,),
        creative_impact=CreativeImpact.HIGH_IMPACT,
        approval_gate=ApprovalGate.PRODUCER_AND_COUNSEL,
        confidence=QualificationConfidence.MEDIUM,
        required_evidence=("BFI cultural test §1 points criteria",),
        graph_rule_id="RULE-BFI-CULTURAL-TEST",
    )
    defaults.update(overrides)
    return Recommendation(**defaults)


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert RECOMMENDATION_ENGINE_VERSION == "1.0.0"

    def test_four_domains(self):
        assert {d.value for d in RecommendationDomain} == {"financial", "structural", "production", "creative"}

    def test_five_statuses(self):
        assert {s.value for s in RecommendationStatus} == {
            "proposed", "under_review", "accepted", "declined", "superseded",
        }

    def test_three_tiers(self):
        assert {t.value for t in RecommendationTier} == {"actionable", "gated", "informational"}


# ── Object validation ─────────────────────────────────────────────────────────

class TestObjectValidation:
    def test_minimal_financial_constructs(self):
        rec = _minimal_financial()
        assert rec.status == RecommendationStatus.PROPOSED
        assert rec.creative_impact == CreativeImpact.NOT_APPLICABLE

    def test_non_creative_cannot_set_creative_impact(self):
        with pytest.raises(ValueError, match="creative_impact may only be set"):
            _minimal_financial(creative_impact=CreativeImpact.MATERIAL)

    def test_non_creative_cannot_set_creative_elements(self):
        with pytest.raises(ValueError, match="affected_creative_elements may only be set"):
            _minimal_financial(affected_creative_elements=(CreativeElement.DIRECTOR,))

    def test_recommendation_id_required(self):
        with pytest.raises(ValueError, match="recommendation_id is required"):
            _minimal_financial(recommendation_id="")


# ── Creative guardrail ─────────────────────────────────────────────────────────

class TestCreativeGuardrail:
    def test_valid_creative_constructs(self):
        rec = _valid_creative()
        assert rec.domain == RecommendationDomain.CREATIVE

    def test_missing_creative_impact_rejected(self):
        with pytest.raises(ValueError, match="creative_impact other than NOT_APPLICABLE"):
            _valid_creative(creative_impact=CreativeImpact.NOT_APPLICABLE)

    def test_gate_below_producer_rejected(self):
        with pytest.raises(ValueError, match="at least PRODUCER"):
            _valid_creative(approval_gate=ApprovalGate.NONE)

    def test_missing_evidence_graph_ref_rejected(self):
        with pytest.raises(ValueError, match="Evidence Graph reference"):
            _valid_creative(graph_rule_id=None, graph_absence_id=None)

    def test_absence_ref_alone_is_sufficient(self):
        rec = _valid_creative(graph_rule_id=None, graph_absence_id="ABS-CULTURAL-TEST")
        assert rec.graph_absence_id == "ABS-CULTURAL-TEST"

    def test_missing_required_evidence_rejected(self):
        with pytest.raises(ValueError, match="qualification reason"):
            _valid_creative(required_evidence=())

    def test_missing_trade_off_framing_rejected(self):
        with pytest.raises(ValueError, match="trade-off"):
            _valid_creative(
                headline="Cast a UK lead to get more money",
                detail="This will unlock more incentive.",
            )

    def test_trade_off_in_detail_alone_is_sufficient(self):
        rec = _valid_creative(
            headline="Casting consideration for BFI eligibility",
            detail="This is a trade-off the producer should weigh against creative fit.",
        )
        assert rec is not None

    def test_producer_only_gate_permitted(self):
        rec = _valid_creative(approval_gate=ApprovalGate.PRODUCER)
        assert rec.approval_gate == ApprovalGate.PRODUCER

    def test_counsel_only_gate_permitted(self):
        rec = _valid_creative(approval_gate=ApprovalGate.COUNSEL)
        assert rec.approval_gate == ApprovalGate.COUNSEL


# ── Generation: FINANCIAL ─────────────────────────────────────────────────────

class TestFinancialGeneration:
    def test_grey_area_recommendations_generated(self, collection):
        recs = generate_financial_recommendations(collection)
        grey_recs = [r for r in recs if r.recommendation_type == RecommendationType.RESOLVE_GREY_AREA]
        assert len(grey_recs) == 2
        ids = {r.source_opportunity_ids[0] for r in grey_recs}
        assert ids == {"OPP-GREY-GA-ATL-SCOPE", "OPP-GREY-GA-INKIND-FMV"}

    def test_grey_area_recommendation_carries_upside_from_opportunity(self, collection):
        recs = generate_financial_recommendations(collection)
        atl = next(r for r in recs if r.source_opportunity_ids == ("OPP-GREY-GA-ATL-SCOPE",))
        assert atl.estimated_upside_usd == pytest.approx(408_444.0 * MU_RATE)
        assert atl.approval_gate == ApprovalGate.COUNSEL

    def test_reinvestment_unknown_generates_recommendation(self, collection):
        recs = generate_financial_recommendations(collection)
        mu_reinvest = next(
            r for r in recs
            if r.recommendation_type == RecommendationType.PURSUE_REINVESTMENT and "MU" in r.affected_jurisdictions
        )
        assert mu_reinvest.approval_gate == ApprovalGate.COUNSEL
        assert mu_reinvest.acquisition_task_refs == ("TASK-reinvestment:MU",)

    def test_no_dollar_values_invented(self, collection):
        recs = generate_financial_recommendations(collection)
        for r in recs:
            if r.recommendation_type in (RecommendationType.PURSUE_REINVESTMENT, RecommendationType.NORMALIZE_TIMING):
                assert r.estimated_upside_usd is None  # Discovery never set one; none invented here


# ── Generation: STRUCTURAL ────────────────────────────────────────────────────

class TestStructuralGeneration:
    def test_structuring_recommendations_generated(self, collection):
        recs = generate_structural_recommendations(collection)
        struct_recs = [r for r in recs if r.source_opportunity_ids and r.source_opportunity_ids[0].startswith("OPP-STRUCT-")]
        assert len(struct_recs) == 3
        accounts = {r.affected_budget_lines[0] for r in struct_recs}
        assert accounts == {"21-00", "23-00", "42-00"}

    def test_structuring_recommendation_carries_lever_upside(self, collection):
        recs = generate_structural_recommendations(collection)
        dp = next(r for r in recs if r.affected_budget_lines == ("21-00",))
        assert dp.estimated_upside_usd == pytest.approx(38_000.0)
        assert dp.approval_gate == ApprovalGate.PRODUCER

    def test_treaty_recommendations_generated(self, collection):
        recs = generate_structural_recommendations(collection)
        treaty_recs = [r for r in recs if r.recommendation_type == RecommendationType.ADOPT_TREATY_STRUCTURE]
        assert len(treaty_recs) > 0
        assert all(r.approval_gate == ApprovalGate.COUNSEL for r in treaty_recs)

    def test_stacking_unknown_never_becomes_pursue_now(self, collection):
        recs = generate_structural_recommendations(collection)
        stack_recs = [r for r in recs if r.recommendation_type == RecommendationType.PURSUE_STACKING]
        assert all("Investigate" in r.headline for r in stack_recs)  # today's data is all stacking_unknown
        assert all(r.approval_gate == ApprovalGate.COUNSEL for r in stack_recs)

    def test_no_stackability_invented(self, collection):
        recs = generate_structural_recommendations(collection)
        stack_recs = [r for r in recs if r.recommendation_type == RecommendationType.PURSUE_STACKING]
        assert all(r.acquisition_task_refs for r in stack_recs)  # routed to evidence, not asserted


# ── Dependency preservation ────────────────────────────────────────────────────

class TestDependencyPreservation:
    def test_nationality_unlock_depends_on_its_treaty_recommendation(self, collection):
        recs = generate_structural_recommendations(collection)
        by_id = {r.recommendation_id: r for r in recs}
        unlock = next(
            r for r in recs
            if r.source_opportunity_ids and "UNLOCK" in r.source_opportunity_ids[0]
        )
        assert unlock.dependent_recommendation_ids
        for dep_id in unlock.dependent_recommendation_ids:
            assert dep_id in by_id

    def test_normalization_depends_on_relocation_recommendation(self, collection):
        recs = generate_financial_recommendations(collection)
        vat_es = next(r for r in recs if r.source_opportunity_ids == ("OPP-NORM-VAT-MU-ES",))
        # OPP-JUR-RELOCATE-MU-ES is a JURISDICTION opportunity — never
        # turned into a FINANCIAL/STRUCTURAL recommendation in this phase —
        # so its dependency correctly resolves to nothing yet, not invented.
        assert vat_es.dependent_recommendation_ids == ()

    def test_unresolvable_dependency_never_fabricated(self, collection):
        recs = generate_recommendations(collection)
        by_id = {r.recommendation_id: r for r in recs}
        for r in recs:
            for dep in r.dependent_recommendation_ids:
                assert dep in by_id  # every listed dependency actually exists


# ── Pricing ─────────────────────────────────────────────────────────────────

class TestPricing:
    def test_structuring_levers_priced(self, priced_recommendations):
        dp = next(r for r in priced_recommendations if r.affected_budget_lines == ("21-00",))
        assert dp.npc_impact is not None
        assert set(dp.npc_impact.keys()) == set(RiskCase)
        assert dp.npc_impact[RiskCase.RISK_ADJUSTED] > 0  # accepting improves NPC

    def test_grey_areas_priced(self, priced_recommendations):
        atl = next(r for r in priced_recommendations if r.recommendation_id == "REC-OPP-GREY-GA-ATL-SCOPE")
        assert atl.npc_impact is not None
        assert atl.npc_impact[RiskCase.CONSERVATIVE] > 0  # resolving moves it into Conservative

    def test_reinvestment_and_treaty_left_unpriced(self, priced_recommendations):
        for r in priced_recommendations:
            if r.recommendation_type in (RecommendationType.PURSUE_REINVESTMENT, RecommendationType.ADOPT_TREATY_STRUCTURE):
                assert r.npc_impact is None  # no clean accept-toggle exists yet — never guessed


# ── Ranking ───────────────────────────────────────────────────────────────────

class TestRanking:
    def test_result_type(self, priced_recommendations):
        result = rank_recommendations(priced_recommendations)
        assert isinstance(result, RecommendationRankingResult)

    def test_actionable_before_gated_before_informational(self, priced_recommendations):
        result = rank_recommendations(priced_recommendations)
        tier_sequence = [rr.tier for rr in result.ranked]
        # once a tier "closes" it never reopens
        seen_gated = seen_informational = False
        for tier in tier_sequence:
            if tier == RecommendationTier.GATED:
                seen_gated = True
            if tier == RecommendationTier.INFORMATIONAL:
                seen_informational = True
            if tier == RecommendationTier.ACTIONABLE:
                assert not seen_gated and not seen_informational
            if tier == RecommendationTier.GATED:
                assert not seen_informational

    def test_informational_never_ranks_above_priced(self, priced_recommendations):
        result = rank_recommendations(priced_recommendations)
        priced_ranks = [rr.rank for rr in result.ranked if rr.tier != RecommendationTier.INFORMATIONAL]
        informational_ranks = [rr.rank for rr in result.ranked if rr.tier == RecommendationTier.INFORMATIONAL]
        if priced_ranks and informational_ranks:
            assert max(priced_ranks) < min(informational_ranks)

    def test_structuring_levers_are_actionable(self, priced_recommendations):
        result = rank_recommendations(priced_recommendations)
        by_id = {rr.recommendation_id: rr for rr in result.ranked}
        assert by_id["REC-OPP-STRUCT-SP-21-00"].tier == RecommendationTier.ACTIONABLE

    def test_grey_areas_are_gated(self, priced_recommendations):
        result = rank_recommendations(priced_recommendations)
        by_id = {rr.recommendation_id: rr for rr in result.ranked}
        assert by_id["REC-OPP-GREY-GA-ATL-SCOPE"].tier == RecommendationTier.GATED

    def test_ranking_deterministic(self, priced_recommendations):
        r1 = rank_recommendations(priced_recommendations)
        r2 = rank_recommendations(priced_recommendations)
        assert [rr.recommendation_id for rr in r1.ranked] == [rr.recommendation_id for rr in r2.ranked]
        assert [rr.score for rr in r1.ranked] == [rr.score for rr in r2.ranked]

    def test_by_tier_helper(self, priced_recommendations):
        result = rank_recommendations(priced_recommendations)
        actionable = result.by_tier(RecommendationTier.ACTIONABLE)
        assert all(classify_tier(r) == RecommendationTier.ACTIONABLE for r in actionable)


# ── Lifecycle / gates ─────────────────────────────────────────────────────────

class TestLifecycle:
    def test_submit_for_review(self):
        rec = _minimal_financial()
        submit_for_review(rec)
        assert rec.status == RecommendationStatus.UNDER_REVIEW

    def test_gated_cannot_be_accepted(self, priced_recommendations):
        gated = next(r for r in priced_recommendations if classify_tier(r) == RecommendationTier.GATED)
        with pytest.raises(ValueError, match="GATED"):
            accept_recommendation(gated, approver_roles=frozenset({"producer", "counsel"}))
        assert gated.status == RecommendationStatus.PROPOSED  # rejection does not silently change status

    def test_actionable_missing_approval_role_rejected(self, priced_recommendations):
        actionable = next(r for r in priced_recommendations if classify_tier(r) == RecommendationTier.ACTIONABLE)
        assert actionable.approval_gate == ApprovalGate.PRODUCER
        with pytest.raises(ValueError, match="missing"):
            accept_recommendation(actionable, approver_roles=frozenset())

    def test_actionable_accepted_with_correct_approval(self, priced_recommendations):
        actionable = next(r for r in priced_recommendations if classify_tier(r) == RecommendationTier.ACTIONABLE)
        accept_recommendation(actionable, approver_roles=frozenset({"producer"}))
        assert actionable.status == RecommendationStatus.ACCEPTED

    def test_declined_recommendation_retained(self):
        rec = _minimal_financial()
        decline_recommendation(rec, reason="not pursuing this quarter")
        assert rec.status == RecommendationStatus.DECLINED
        assert rec.attributes["decline_reason"] == "not pursuing this quarter"
        assert rec.recommendation_id == "REC-X"  # still present, not deleted

    def test_supersede_retains_object(self):
        rec = _minimal_financial()
        supersede_recommendation(rec, superseded_by="REC-Y")
        assert rec.status == RecommendationStatus.SUPERSEDED
        assert rec.attributes["superseded_by"] == "REC-Y"

    def test_cannot_accept_declined(self):
        rec = _minimal_financial()
        decline_recommendation(rec)
        with pytest.raises(ValueError, match="cannot be accepted"):
            accept_recommendation(rec, approver_roles=frozenset({"producer", "counsel"}))


# ── Non-mutation ────────────────────────────────────────────────────────────────

class TestNonMutation:
    def test_no_mutation_of_opportunity_collection(self, collection):
        ids_before = [o.opportunity_id for o in collection.opportunities]
        generate_recommendations(collection)
        assert [o.opportunity_id for o in collection.opportunities] == ids_before

    def test_no_mutation_of_register_or_grey_areas_or_paths(self, recommendations, register, grey_areas, structuring_paths):
        reg_snapshot = copy.deepcopy(register)
        grey_snapshot = copy.deepcopy(grey_areas)
        paths_snapshot = copy.deepcopy(structuring_paths)
        recs = copy.deepcopy(recommendations)
        price_recommendations(
            recs, register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
            all_structuring_paths=structuring_paths, all_grey_areas=grey_areas,
        )
        assert register == reg_snapshot
        assert grey_areas == grey_snapshot
        assert structuring_paths == paths_snapshot

    def test_no_optimizer_output_change(self, register, grey_areas, structuring_paths):
        from app.calculators.optimization_engine import build_risk_cases
        result = build_risk_cases(
            register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
            structuring_paths=structuring_paths, grey_areas=grey_areas,
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(1_979_913.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(791_965.0, abs=1.0)

    def test_little_utopia_conservative_unchanged_after_pricing_recs(self, priced_recommendations, register, grey_areas, structuring_paths):
        from app.calculators.optimization_engine import build_risk_cases
        result = build_risk_cases(
            register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
            structuring_paths=structuring_paths, grey_areas=grey_areas,
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(1_979_913.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(791_965.0, abs=1.0)

    def test_module_does_not_import_composer_or_ranker(self):
        """7D core operates purely on OpportunityCollection + the
        optimizer's public API — it does not reach into Phase 7B/7C
        modules, keeping this phase additive and independently testable."""
        import ast
        import inspect
        import app.calculators.recommendation_engine as re_module

        tree = ast.parse(inspect.getsource(re_module))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert "app.calculators.global_scenario_ranker" not in imported
        assert "app.calculators.production_structure_composer" not in imported
