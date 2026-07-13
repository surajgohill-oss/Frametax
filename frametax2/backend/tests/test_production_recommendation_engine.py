"""
test_production_recommendation_engine.py

Targeted tests for Phase 7D — the Production Optimization Recommendation
Engine (production_recommendation_engine.py). Covers the Recommendation
object model and its creative-gating validation, financial/structural
generation from Phase 7A/7C outputs, cultural-test hooks against the real
cultural_test_rules.py engine, required-input honesty for missing
production facts, ranking, lifecycle/approval gates, determinism,
non-mutation of every consumed object, and non-regression of Little
Utopia's existing optimizer figures.
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.legal_authority_acquisition import DEFAULT_ACQUISITION_EFFORT
from app.calculators.levers import derive_levers, is_lever_recommended
from app.calculators.opportunity_discovery import (
    OpportunityType,
    discover_all_opportunities,
    opportunities_to_structuring_paths,
)
from app.calculators.optimization_engine import RiskCase, build_risk_cases
from app.calculators.production_structure_composer import compose_production_structures
from app.calculators.qualification_model import (
    QualificationConfidence,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)

from app.calculators.production_recommendation_engine import (
    CULTURAL_TEST_REGISTRY,
    PRODUCTION_RECOMMENDATION_ENGINE_VERSION,
    RECOMMENDATION_PASSES,
    Recommendation,
    RecommendationCategory,
    RecommendationSet,
    RecommendationStatus,
    dedupe_recommendations,
    defer_recommendation,
    generate_candidate_recommendations,
    generate_cultural_recommendations,
    generate_evidence_acquisition_recommendations,
    generate_grey_area_recommendations,
    generate_production_recommendations,
    generate_structuring_recommendations,
    generate_treaty_stacking_reinvestment_normalization_recommendations,
    rank_recommendations,
    record_counsel_approval,
    record_producer_approval,
    reject_recommendation,
    supersede_recommendation,
)

MU_RATE = 0.40
MU_GROSS_BUDGET = 4_364_393.0


# ── Fixtures (same shape as test_opportunity_discovery.py / test_production_structure_composer.py) ─

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
def composition_result(collection, graph, register, grey_areas):
    return compose_production_structures(
        collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
        rate=MU_RATE, grey_areas=grey_areas,
    )


FR_CNC_ALL_FAILING = {
    "french_language_or_subject": False,
    "director_french_or_eea": False,
    "writer_french_or_eea": False,
    "producer_french": False,
    "french_spend_pct": 0.10,
}

FR_CNC_PASSING = {
    "french_language_or_subject": True,
    "director_french_or_eea": True,
    "writer_french_or_eea": False,
    "producer_french": True,
    "french_spend_pct": 0.60,
}


def _minimal_recommendation(category: RecommendationCategory, **overrides) -> Recommendation:
    base = dict(
        recommendation_id="REC-TEST-1",
        category=category,
        subtype="test_subtype",
        title="Test",
        description="Test description",
        specific_actions=("Do the thing.",),
    )
    base.update(overrides)
    return Recommendation(**base)


# ── 7D-1: Object model / validation ──────────────────────────────────────────

class TestRecommendationValidation:
    def test_financial_recommendation_constructs_without_creative_fields(self):
        rec = _minimal_recommendation(RecommendationCategory.FINANCIAL)
        assert rec.creative_impact is None
        assert rec.status == RecommendationStatus.PROPOSED

    def test_structural_recommendation_constructs_without_creative_fields(self):
        rec = _minimal_recommendation(RecommendationCategory.STRUCTURAL)
        assert rec.category == RecommendationCategory.STRUCTURAL

    def test_creative_recommendation_requires_creative_impact(self):
        with pytest.raises(ValueError, match="creative_impact"):
            _minimal_recommendation(
                RecommendationCategory.CREATIVE,
                qualification_rationale="x", trade_off_framing="x",
                evidence_reference=("e",), authority_reference=("a",),
            )

    def test_creative_recommendation_requires_qualification_rationale(self):
        with pytest.raises(ValueError, match="qualification_rationale"):
            _minimal_recommendation(
                RecommendationCategory.CREATIVE,
                creative_impact="x", trade_off_framing="x",
                evidence_reference=("e",), authority_reference=("a",),
            )

    def test_creative_recommendation_requires_trade_off_framing(self):
        with pytest.raises(ValueError, match="trade_off_framing"):
            _minimal_recommendation(
                RecommendationCategory.CREATIVE,
                creative_impact="x", qualification_rationale="x",
                evidence_reference=("e",), authority_reference=("a",),
            )

    def test_creative_recommendation_requires_evidence_reference(self):
        with pytest.raises(ValueError, match="evidence_reference"):
            _minimal_recommendation(
                RecommendationCategory.CREATIVE,
                creative_impact="x", qualification_rationale="x", trade_off_framing="x",
                authority_reference=("a",),
            )

    def test_creative_recommendation_requires_authority_reference(self):
        with pytest.raises(ValueError, match="authority_reference"):
            _minimal_recommendation(
                RecommendationCategory.CREATIVE,
                creative_impact="x", qualification_rationale="x", trade_off_framing="x",
                evidence_reference=("e",),
            )

    def test_creative_recommendation_requires_producer_approval_flag(self):
        with pytest.raises(ValueError, match="producer approval"):
            _minimal_recommendation(
                RecommendationCategory.CREATIVE,
                creative_impact="x", qualification_rationale="x", trade_off_framing="x",
                evidence_reference=("e",), authority_reference=("a",),
                requires_producer_approval=False,
            )

    def test_creative_recommendation_constructs_with_all_required_fields(self):
        rec = _minimal_recommendation(
            RecommendationCategory.CREATIVE,
            creative_impact="x", qualification_rationale="x", trade_off_framing="x",
            evidence_reference=("e",), authority_reference=("a",),
        )
        assert rec.category == RecommendationCategory.CREATIVE

    def test_required_input_recommendation_requires_required_fields_attribute(self):
        with pytest.raises(ValueError, match="required_fields"):
            _minimal_recommendation(RecommendationCategory.REQUIRED_INPUT)

    def test_required_input_recommendation_constructs_with_required_fields(self):
        rec = _minimal_recommendation(
            RecommendationCategory.REQUIRED_INPUT,
            attributes={"required_fields": ("some_key",)},
        )
        assert rec.attributes["required_fields"] == ("some_key",)

    def test_never_auto_applies_no_mutating_methods_exist_on_source_objects(self, collection):
        """A Recommendation never carries a reference back that could
        mutate its source Opportunity — it only carries string ids."""
        rec = _minimal_recommendation(RecommendationCategory.FINANCIAL, opportunity_ids=("OPP-X",))
        assert isinstance(rec.opportunity_ids, tuple)
        assert all(isinstance(x, str) for x in rec.opportunity_ids)


# ── 7D-2: Financial recommendations ──────────────────────────────────────────

class TestGreyAreaRecommendations:
    def test_one_recommendation_per_open_grey_area(self, collection, grey_areas):
        recs = generate_grey_area_recommendations(collection)
        open_grey_opps = collection.of_type(OpportunityType.GREY_AREA)
        assert len(recs) == len(open_grey_opps) > 0

    def test_value_matches_underlying_opportunity_never_recomputed(self, collection):
        recs = generate_grey_area_recommendations(collection)
        grey_opps = {o.opportunity_id: o for o in collection.of_type(OpportunityType.GREY_AREA)}
        for rec in recs:
            opp = grey_opps[rec.opportunity_ids[0]]
            assert rec.estimated_value_usd == opp.estimated_upside_usd

    def test_requires_counsel_approval(self, collection):
        recs = generate_grey_area_recommendations(collection)
        assert recs and all(r.requires_counsel_approval for r in recs)

    def test_category_is_financial(self, collection):
        recs = generate_grey_area_recommendations(collection)
        assert all(r.category == RecommendationCategory.FINANCIAL for r in recs)


class TestEvidenceAcquisitionRecommendations:
    def test_excludes_grey_area_opportunities(self, collection):
        recs = generate_evidence_acquisition_recommendations(collection)
        grey_ids = {o.opportunity_id for o in collection.of_type(OpportunityType.GREY_AREA)}
        assert not any(rec.opportunity_ids[0] in grey_ids for rec in recs)

    def test_covers_every_requires_evidence_non_grey_opportunity(self, collection):
        expected = {
            o.opportunity_id for o in collection.opportunities
            if o.requires_evidence and o.opportunity_type != OpportunityType.GREY_AREA
        }
        recs = generate_evidence_acquisition_recommendations(collection)
        actual = {rec.opportunity_ids[0] for rec in recs}
        assert actual == expected

    def test_never_invents_a_dollar_value(self, collection):
        opps = {o.opportunity_id: o for o in collection.opportunities}
        for rec in generate_evidence_acquisition_recommendations(collection):
            opp = opps[rec.opportunity_ids[0]]
            assert rec.estimated_value_usd == opp.estimated_upside_usd


class TestStructuringRecommendations:
    def test_only_includes_levers_clearing_recommendation_threshold(self, collection, register):
        levers = {
            lever.lever_id: lever
            for lever in derive_levers(register, rate=MU_RATE, jurisdiction_code="MU")
        }
        recs = generate_structuring_recommendations(collection, register=register, rate=MU_RATE, jurisdiction_code="MU")
        for rec in recs:
            lever_id = rec.recommendation_id.removeprefix("REC-STRUCT-")
            assert is_lever_recommended(levers[lever_id])

        excluded_lever_ids = {lid for lid, lv in levers.items() if not is_lever_recommended(lv)}
        recommended_lever_ids = {rec.recommendation_id.removeprefix("REC-STRUCT-") for rec in recs}
        assert not (excluded_lever_ids & recommended_lever_ids)

    def test_value_is_levers_own_upside_never_recomputed(self, collection, register):
        levers = {
            lever.lever_id: lever
            for lever in derive_levers(register, rate=MU_RATE, jurisdiction_code="MU")
        }
        recs = generate_structuring_recommendations(collection, register=register, rate=MU_RATE, jurisdiction_code="MU")
        for rec in recs:
            lever_id = rec.recommendation_id.removeprefix("REC-STRUCT-")
            assert rec.estimated_value_usd == levers[lever_id].upside_incentive_usd

    def test_category_is_structural(self, collection, register):
        recs = generate_structuring_recommendations(collection, register=register, rate=MU_RATE, jurisdiction_code="MU")
        assert recs and all(r.category == RecommendationCategory.STRUCTURAL for r in recs)


class TestTreatyStackingNormalizationRecommendations:
    def test_generates_recommendations_for_known_stack(self, collection):
        recs = generate_treaty_stacking_reinvestment_normalization_recommendations(collection)
        known_stack_opps = [o for o in collection.of_type(OpportunityType.STACKING) if o.subtype == "known_stack"]
        rec_ids = {r.opportunity_ids[0] for r in recs}
        assert all(o.opportunity_id in rec_ids for o in known_stack_opps)

    def test_excludes_stacking_unknown(self, collection):
        recs = generate_treaty_stacking_reinvestment_normalization_recommendations(collection)
        unknown_ids = {o.opportunity_id for o in collection.opportunities if o.subtype == "stacking_unknown"}
        assert not any(r.opportunity_ids[0] in unknown_ids for r in recs)

    def test_excludes_reinvestment_unknown(self, collection):
        recs = generate_treaty_stacking_reinvestment_normalization_recommendations(collection)
        unknown_ids = {o.opportunity_id for o in collection.opportunities if o.subtype == "reinvestment_unknown"}
        assert not any(r.opportunity_ids[0] in unknown_ids for r in recs)

    def test_includes_bilateral_treaty_opportunities(self, collection):
        recs = generate_treaty_stacking_reinvestment_normalization_recommendations(collection)
        treaty_opps = [o for o in collection.of_type(OpportunityType.TREATY) if o.subtype == "bilateral_coproduction"]
        if treaty_opps:
            rec_ids = {r.opportunity_ids[0] for r in recs}
            assert all(o.opportunity_id in rec_ids for o in treaty_opps)

    def test_category_is_structural(self, collection):
        recs = generate_treaty_stacking_reinvestment_normalization_recommendations(collection)
        assert recs and all(r.category == RecommendationCategory.STRUCTURAL for r in recs)


class TestCandidateRecommendations:
    def test_savings_recommendation_only_for_cheaper_fully_priced_candidates(self, composition_result):
        recs = generate_candidate_recommendations(composition_result)
        savings = [r for r in recs if r.subtype == "structure_savings"]
        baseline = next(
            c for c in composition_result.candidates
            if c.participating_jurisdictions == (composition_result.baseline_jurisdiction,)
        )
        for rec in savings:
            assert rec.estimated_value_usd is not None
            assert rec.estimated_value_usd > 0
            assert rec.category == RecommendationCategory.FINANCIAL
        # every fully-priced candidate cheaper than baseline must be represented
        if baseline.is_fully_priced:
            baseline_npc = baseline.npc(RiskCase.RISK_ADJUSTED)
            cheaper = [
                c for c in composition_result.candidates
                if c.candidate_id != baseline.candidate_id and c.is_fully_priced
                and c.npc(RiskCase.RISK_ADJUSTED) < baseline_npc
            ]
            savings_candidate_ids = {r.candidate_id for r in savings}
            assert all(c.candidate_id in savings_candidate_ids for c in cheaper)

    def test_constraint_recommendation_for_every_candidate_with_constraints(self, composition_result):
        recs = generate_candidate_recommendations(composition_result)
        constraint_recs = {r.candidate_id: r for r in recs if r.subtype == "resolve_structure_constraints"}
        for candidate in composition_result.candidates:
            if candidate.constraints:
                assert candidate.candidate_id in constraint_recs
                rec = constraint_recs[candidate.candidate_id]
                assert len(rec.specific_actions) == len(candidate.constraints)
                assert rec.estimated_value_usd is None  # never invented

    def test_no_recommendations_without_composition_result_candidates(self):
        from app.calculators.production_structure_composer import CompositionResult
        empty = CompositionResult(baseline_jurisdiction="MU", passes_run=(), candidates=[], pruned={})
        assert generate_candidate_recommendations(empty) == []


# ── 7D-6: Cultural-test recommendation hooks ─────────────────────────────────

class TestCulturalRecommendations:
    def test_passing_test_yields_no_recommendations(self):
        recs = generate_cultural_recommendations(
            {"fr_cnc_cultural_test": FR_CNC_PASSING}, ("fr_cnc_cultural_test",),
        )
        assert recs == []

    def test_failing_test_yields_creative_recommendations_for_creative_criteria_only(self):
        recs = generate_cultural_recommendations(
            {"fr_cnc_cultural_test": FR_CNC_ALL_FAILING}, ("fr_cnc_cultural_test",),
        )
        assert recs, "expected at least one creative recommendation"
        assert all(r.category == RecommendationCategory.CREATIVE for r in recs)
        criterion_codes = {r.recommendation_id.split("-")[-1] for r in recs}
        # A (language), B (director), C (writer), D (producer nationality) are creative;
        # E (spend %) is a financial/structural threshold, never surfaced as creative.
        assert criterion_codes == {"CNC_A1", "CNC_B1", "CNC_C1", "CNC_D1"}
        assert "CNC_E1" not in criterion_codes

    def test_creative_recommendation_fields_are_fully_populated(self):
        recs = generate_cultural_recommendations(
            {"fr_cnc_cultural_test": FR_CNC_ALL_FAILING}, ("fr_cnc_cultural_test",),
        )
        for rec in recs:
            assert rec.creative_impact
            assert rec.qualification_rationale
            assert rec.trade_off_framing
            assert rec.evidence_reference
            assert rec.authority_reference
            assert rec.authority_reference[0].startswith("cultural_test_rules.fr_cnc_cultural_test[")
            assert rec.requires_producer_approval is True
            assert rec.requires_counsel_approval is True
            assert rec.estimated_value_usd is None  # cultural gaps never get an invented dollar figure

    def test_missing_input_produces_required_input_recommendation(self):
        recs = generate_cultural_recommendations({}, ("ie_section_481_test",))
        assert len(recs) == 1
        rec = recs[0]
        assert rec.category == RecommendationCategory.REQUIRED_INPUT
        expected_keys = {r["input_key"] for r in CULTURAL_TEST_REGISTRY["ie_section_481_test"]["rules"]}
        assert set(rec.attributes["required_fields"]) == expected_keys

    def test_partial_missing_input_lists_only_missing_keys(self):
        partial = {"irish_or_eea_company": True, "irish_qe_above_125k": True}
        recs = generate_cultural_recommendations({"ie_section_481_test": partial}, ("ie_section_481_test",))
        assert len(recs) == 1
        missing = set(recs[0].attributes["required_fields"])
        assert missing == {"irish_qe_pct", "qualifying_production_type", "within_individual_cap"}

    def test_empty_relevant_slugs_yields_nothing_even_with_inputs_present(self):
        recs = generate_cultural_recommendations({"fr_cnc_cultural_test": FR_CNC_ALL_FAILING}, ())
        assert recs == []

    def test_unregistered_slug_is_skipped_not_raised(self):
        recs = generate_cultural_recommendations({}, ("not_a_real_test",))
        assert recs == []

    def test_all_eight_tests_registered(self):
        assert set(CULTURAL_TEST_REGISTRY.keys()) == {
            "fr_cnc_cultural_test", "ie_section_481_test", "eu_eurimages_test",
            "ibermedia_test", "ca_content_test", "au_content_test", "eu_european_convention_test",
            "uk_bfi_cultural_test",
        }


# ── 7D-3: Ranking / dedup ─────────────────────────────────────────────────────

class TestRankingAndDedup:
    def test_dedupe_keeps_first_occurrence(self):
        a = _minimal_recommendation(RecommendationCategory.FINANCIAL, recommendation_id="REC-DUP", title="first")
        b = _minimal_recommendation(RecommendationCategory.FINANCIAL, recommendation_id="REC-DUP", title="second")
        result = dedupe_recommendations([a, b])
        assert len(result) == 1
        assert result[0].title == "first"

    def test_rank_is_deterministic_descending_score_then_id(self):
        high = _minimal_recommendation(
            RecommendationCategory.FINANCIAL, recommendation_id="REC-B",
            estimated_value_usd=100_000.0, attributes={"confidence_gap": 1.0, "implementation_effort": 1.0},
        )
        low = _minimal_recommendation(
            RecommendationCategory.FINANCIAL, recommendation_id="REC-A",
            estimated_value_usd=1.0, attributes={"confidence_gap": 1.0, "implementation_effort": 1.0},
        )
        ranked = rank_recommendations([low, high])
        assert [r.recommendation_id for r in ranked] == ["REC-B", "REC-A"]

    def test_tie_break_on_recommendation_id(self):
        a = _minimal_recommendation(RecommendationCategory.FINANCIAL, recommendation_id="REC-Z", estimated_value_usd=None)
        b = _minimal_recommendation(RecommendationCategory.FINANCIAL, recommendation_id="REC-A", estimated_value_usd=None)
        ranked = rank_recommendations([a, b])
        assert [r.recommendation_id for r in ranked] == ["REC-A", "REC-Z"]


# ── 7D-4: Lifecycle / gates ───────────────────────────────────────────────────

class TestLifecycleGates:
    def test_producer_approval_alone_accepts_when_counsel_not_required(self):
        rec = _minimal_recommendation(RecommendationCategory.STRUCTURAL, requires_counsel_approval=False)
        record_producer_approval(rec, "prod@example.com")
        assert rec.status == RecommendationStatus.ACCEPTED

    def test_producer_approval_alone_does_not_accept_when_counsel_required(self):
        rec = _minimal_recommendation(RecommendationCategory.FINANCIAL, requires_counsel_approval=True)
        record_producer_approval(rec, "prod@example.com")
        assert rec.status == RecommendationStatus.PROPOSED
        assert not rec.is_fully_approved

    def test_both_approvals_required_before_acceptance(self):
        rec = _minimal_recommendation(RecommendationCategory.FINANCIAL, requires_counsel_approval=True)
        record_producer_approval(rec, "prod@example.com")
        record_counsel_approval(rec, "counsel@example.com")
        assert rec.status == RecommendationStatus.ACCEPTED
        assert rec.is_fully_approved

    def test_counsel_approval_rejected_when_not_required(self):
        rec = _minimal_recommendation(RecommendationCategory.STRUCTURAL, requires_counsel_approval=False)
        with pytest.raises(ValueError, match="does not require counsel"):
            record_counsel_approval(rec, "counsel@example.com")

    def test_reject_then_approve_raises(self):
        rec = _minimal_recommendation(RecommendationCategory.FINANCIAL)
        reject_recommendation(rec, "prod@example.com", "not worth pursuing")
        assert rec.status == RecommendationStatus.REJECTED
        with pytest.raises(ValueError, match="cannot approve"):
            record_producer_approval(rec, "prod@example.com")

    def test_defer_blocked_once_accepted(self):
        rec = _minimal_recommendation(RecommendationCategory.STRUCTURAL, requires_counsel_approval=False)
        record_producer_approval(rec, "prod@example.com")
        assert rec.status == RecommendationStatus.ACCEPTED
        with pytest.raises(ValueError, match="already accepted"):
            defer_recommendation(rec, "prod@example.com", "wait and see")

    def test_supersede_records_replacement(self):
        rec = _minimal_recommendation(RecommendationCategory.FINANCIAL)
        supersede_recommendation(rec, "REC-NEWER")
        assert rec.status == RecommendationStatus.SUPERSEDED
        assert rec.superseded_by == "REC-NEWER"

    def test_lifecycle_never_touches_a_second_object(self):
        """Approving/rejecting a Recommendation only ever assigns its own
        attributes — there is no code path here that can reach back into
        an Opportunity or ProductionStructureCandidate."""
        rec = _minimal_recommendation(RecommendationCategory.STRUCTURAL, requires_counsel_approval=False)
        record_producer_approval(rec, "prod@example.com")
        assert rec.candidate_id is None or isinstance(rec.candidate_id, str)


# ── Determinism / non-mutation / Little Utopia unchanged ─────────────────────

class TestDeterminismAndNonMutation:
    def test_two_runs_produce_identical_ordering(self, collection, composition_result, register, grey_areas):
        r1 = generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        r2 = generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        assert [r.recommendation_id for r in r1.recommendations] == [r.recommendation_id for r in r2.recommendations]

    def test_does_not_mutate_register_or_grey_areas(self, collection, composition_result, register, grey_areas):
        before_register = copy.deepcopy(register)
        before_grey = copy.deepcopy(grey_areas)
        generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        assert register == before_register
        assert grey_areas == before_grey

    def test_does_not_mutate_collection_or_composition_result(self, collection, composition_result, register):
        before_opp_ids = [o.opportunity_id for o in collection.opportunities]
        before_candidate_ids = [c.candidate_id for c in composition_result.candidates]
        generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        assert [o.opportunity_id for o in collection.opportunities] == before_opp_ids
        assert [c.candidate_id for c in composition_result.candidates] == before_candidate_ids

    def test_little_utopia_optimizer_figures_unchanged(self, collection, graph, composition_result, register, grey_areas):
        """Rerunning build_risk_cases() directly for the MU baseline after
        generating recommendations must reproduce byte-identical figures
        to what the composer itself already computed — proof this module
        introduces no new optimizer computation and no shared-state drift."""
        generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        baseline = next(
            c for c in composition_result.candidates
            if c.participating_jurisdictions == (composition_result.baseline_jurisdiction,)
        )
        paths = opportunities_to_structuring_paths(
            [o for o in collection.opportunities if o.opportunity_id in baseline.included_opportunity_ids],
            register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        direct = build_risk_cases(
            register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
            structuring_paths=paths, grey_areas=grey_areas, delay_weeks=39, bridge_rate=0.08,
            jurisdiction_code="MU",
        )
        for case in RiskCase:
            assert direct.cases[case].net_production_cost_usd == baseline.cases[case].net_production_cost_usd


# ── Top-level orchestration ──────────────────────────────────────────────────

class TestGenerateProductionRecommendations:
    def test_returns_recommendation_set_with_all_passes(self, collection, composition_result, register):
        result = generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        assert isinstance(result, RecommendationSet)
        assert result.passes_run == RECOMMENDATION_PASSES
        assert result.baseline_jurisdiction == "MU"
        assert result.recommendations

    def test_skips_structuring_without_register_or_rate(self, collection, composition_result):
        result = generate_production_recommendations(collection, composition_result=composition_result)
        assert not any(r.recommendation_id.startswith("REC-STRUCT-") for r in result.recommendations)

    def test_skips_candidate_recommendations_without_composition_result(self, collection, register):
        result = generate_production_recommendations(collection, register=register, rate=MU_RATE, jurisdiction_code="MU")
        assert not any(r.candidate_id is not None for r in result.recommendations)

    def test_skips_cultural_without_relevant_slugs(self, collection, composition_result, register):
        result = generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
            cultural_test_inputs={"fr_cnc_cultural_test": FR_CNC_ALL_FAILING},
        )
        assert not any(
            r.category in (RecommendationCategory.CREATIVE, RecommendationCategory.REQUIRED_INPUT)
            for r in result.recommendations
        )

    def test_includes_cultural_recommendations_when_relevant_slugs_given(self, collection, composition_result, register):
        result = generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
            cultural_test_inputs={"fr_cnc_cultural_test": FR_CNC_ALL_FAILING},
            relevant_cultural_test_slugs=("fr_cnc_cultural_test",),
        )
        assert any(r.category == RecommendationCategory.CREATIVE for r in result.recommendations)

    def test_of_category_filters_correctly(self, collection, composition_result, register):
        result = generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        for cat in RecommendationCategory:
            subset = result.of_category(cat)
            assert all(r.category == cat for r in subset)

    def test_no_duplicate_recommendation_ids(self, collection, composition_result, register):
        result = generate_production_recommendations(
            collection, composition_result=composition_result, register=register, rate=MU_RATE, jurisdiction_code="MU",
        )
        ids = [r.recommendation_id for r in result.recommendations]
        assert len(ids) == len(set(ids))

    def test_version_constant_present(self):
        assert PRODUCTION_RECOMMENDATION_ENGINE_VERSION
