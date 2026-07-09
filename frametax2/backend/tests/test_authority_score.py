"""
test_authority_score.py

Targeted tests for the Phase 2 Authority Score (authority_score.py).
"""
from __future__ import annotations

import pytest

from app.calculators.evidence_graph import (
    AbsenceOfAuthority,
    AuthoritySource,
    AuthorityTier,
    BindingForce,
    Citation,
    Document,
    DocumentVersion,
    Evidence,
    EvidenceGraph,
    Rule,
    binding_force_of,
)
from app.calculators.qualification_model import QualificationConfidence
from app.calculators.authority_score import (
    AUTHORITY_SCORE_VERSION,
    BINDING_FORCE_WEIGHT,
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    CONFLICT_CAP,
    SUPERSEDED_PENALTY_MULTIPLIER,
    TIER_STRENGTH,
    confidence_band,
    score_authority_source,
    score_recommendation,
    score_rule,
)


def _build_graph_with_rule(
    graph: EvidenceGraph,
    rule_id="R1",
    tier=AuthorityTier.OFFICIAL_GUIDANCE,
    jurisdiction_code="MU",
    effective_date="2022-10-01",
    pinpoint="Guideline 2.1",
    citation_text="incurred and spent in Mauritius",
    doc_suffix="",
):
    doc_id = f"doc{doc_suffix}"
    ver_id = f"v{doc_suffix}"
    src_id = f"src{doc_suffix}"
    cit_id = f"cit{doc_suffix}"
    ev_id = f"ev{doc_suffix}"
    graph.add_document(Document(document_id=doc_id, jurisdiction_code=jurisdiction_code, title="doc"))
    graph.add_document_version(DocumentVersion(
        version_id=ver_id, document_id=doc_id, version_label="2022",
        effective_date=effective_date, publication_date=effective_date,
    ))
    graph.add_authority_source(AuthoritySource(
        source_id=src_id, jurisdiction_code=jurisdiction_code, tier=tier,
        authority_body="Agency", title="src", document_version_id=ver_id,
    ))
    if rule_id not in graph._rules:
        graph.add_rule(Rule(rule_id=rule_id, jurisdiction_code=jurisdiction_code, description="rule"))
    graph.add_citation(Citation(
        citation_id=cit_id, authority_source_id=src_id, document_version_id=ver_id,
        pinpoint=pinpoint, citation_text=citation_text,
    ))
    graph.add_evidence(Evidence(evidence_id=ev_id, rule_id=rule_id, citation_id=cit_id, description="ev"))
    return doc_id, ver_id, src_id, cit_id, ev_id


@pytest.fixture()
def graph() -> EvidenceGraph:
    return EvidenceGraph()


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert AUTHORITY_SCORE_VERSION == "1.0.0"

    def test_weights_sum_to_one(self):
        from app.calculators.authority_score import (
            SOURCE_STRENGTH_WEIGHT, LEGAL_WEIGHT_WEIGHT, JURISDICTION_RELEVANCE_WEIGHT,
            RECENCY_WEIGHT, COMPLETENESS_WEIGHT, CITATION_QUALITY_WEIGHT,
        )
        total = (SOURCE_STRENGTH_WEIGHT + LEGAL_WEIGHT_WEIGHT + JURISDICTION_RELEVANCE_WEIGHT
                 + RECENCY_WEIGHT + COMPLETENESS_WEIGHT + CITATION_QUALITY_WEIGHT)
        assert total == pytest.approx(1.0)

    def test_conflict_cap_value(self):
        assert CONFLICT_CAP == 60.0

    def test_superseded_penalty_value(self):
        assert SUPERSEDED_PENALTY_MULTIPLIER == 0.5

    def test_confidence_thresholds(self):
        assert CONFIDENCE_HIGH_THRESHOLD == 75.0
        assert CONFIDENCE_MEDIUM_THRESHOLD == 40.0


# ── Every AuthorityTier + hierarchy/binding-force ordering ──────────────────

class TestTierAndBindingForceOrdering:
    def test_every_tier_has_strength(self):
        for tier in AuthorityTier:
            assert tier in TIER_STRENGTH

    def test_strength_strictly_decreasing_with_weaker_tier(self):
        tiers_in_order = sorted(AuthorityTier, key=lambda t: t.value)
        strengths = [TIER_STRENGTH[t] for t in tiers_in_order]
        assert strengths == sorted(strengths, reverse=True)
        assert len(set(strengths)) == len(strengths)  # strictly distinct, no ties

    def test_primary_legislation_strongest_optimizer_assumption_weakest(self):
        assert TIER_STRENGTH[AuthorityTier.PRIMARY_LEGISLATION] == 1.0
        assert TIER_STRENGTH[AuthorityTier.OPTIMIZER_ASSUMPTION] == pytest.approx(1 / 14)

    def test_every_binding_force_has_weight(self):
        for force in BindingForce:
            assert force in BINDING_FORCE_WEIGHT

    def test_binding_weight_ordering(self):
        assert BINDING_FORCE_WEIGHT[BindingForce.BINDING] > BINDING_FORCE_WEIGHT[BindingForce.BINDING_GENERAL]
        assert BINDING_FORCE_WEIGHT[BindingForce.BINDING_GENERAL] > BINDING_FORCE_WEIGHT[BindingForce.PERSUASIVE_STRONG]
        assert BINDING_FORCE_WEIGHT[BindingForce.PERSUASIVE_STRONG] > BINDING_FORCE_WEIGHT[BindingForce.PERSUASIVE]
        assert BINDING_FORCE_WEIGHT[BindingForce.EVIDENTIARY] > BINDING_FORCE_WEIGHT[BindingForce.INTERPRETIVE]
        assert BINDING_FORCE_WEIGHT[BindingForce.INTERPRETIVE] > BINDING_FORCE_WEIGHT[BindingForce.WEAKEST_DEFENSIBLE]
        assert BINDING_FORCE_WEIGHT[BindingForce.NOT_AUTHORITY] == 0.0

    @pytest.mark.parametrize("tier", list(AuthorityTier))
    def test_score_authority_source_runs_for_every_tier(self, graph, tier):
        _build_graph_with_rule(graph, rule_id="RX", tier=tier)
        score = score_authority_source(graph, "srcunused" if False else "src", "MU", as_of_date="2026-07-01")
        assert 0.0 <= score.composite <= 100.0
        assert score.strongest_tier == tier


# ── Lower tier cannot override higher tier ────────────────────────────────────

class TestTierNonOverride:
    def test_strong_and_weak_evidence_governed_by_strongest(self, graph):
        _build_graph_with_rule(graph, rule_id="R1", tier=AuthorityTier.PRIMARY_LEGISLATION, doc_suffix="-a")
        _build_graph_with_rule(graph, rule_id="R1", tier=AuthorityTier.INDUSTRY_CONVENTION, doc_suffix="-b")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        # Source strength must reflect the STRONGEST tier, not an average
        assert score.strongest_tier == AuthorityTier.PRIMARY_LEGISLATION
        assert score.breakdown.source_strength == TIER_STRENGTH[AuthorityTier.PRIMARY_LEGISLATION]

    def test_weak_only_evidence_does_not_borrow_strength(self, graph):
        _build_graph_with_rule(graph, rule_id="R-weak", tier=AuthorityTier.INDUSTRY_CONVENTION)
        score = score_rule(graph, "R-weak", "MU", as_of_date="2026-07-01")
        assert score.strongest_tier == AuthorityTier.INDUSTRY_CONVENTION
        assert score.breakdown.source_strength == pytest.approx(TIER_STRENGTH[AuthorityTier.INDUSTRY_CONVENTION], abs=1e-3)


# ── Jurisdiction specificity ──────────────────────────────────────────────────

class TestJurisdictionRelevance:
    def test_direct_jurisdiction_scores_full(self, graph):
        _build_graph_with_rule(graph, jurisdiction_code="MU")
        score = score_rule(graph, "R1", target_jurisdiction_code="MU", as_of_date="2026-07-01")
        assert score.breakdown.jurisdiction_relevance == 1.0

    def test_cross_jurisdiction_scores_lower(self, graph):
        _build_graph_with_rule(graph, jurisdiction_code="MT")
        score = score_rule(graph, "R1", target_jurisdiction_code="MU", as_of_date="2026-07-01")
        assert score.breakdown.jurisdiction_relevance == 0.4
        assert score.breakdown.jurisdiction_relevance < 1.0

    def test_direct_jurisdiction_composite_exceeds_cross_jurisdiction(self, graph):
        g1, g2 = EvidenceGraph(), EvidenceGraph()
        _build_graph_with_rule(g1, jurisdiction_code="MU")
        _build_graph_with_rule(g2, jurisdiction_code="MT")
        s1 = score_rule(g1, "R1", "MU", as_of_date="2026-07-01")
        s2 = score_rule(g2, "R1", "MU", as_of_date="2026-07-01")
        assert s1.composite > s2.composite


# ── Recency ──────────────────────────────────────────────────────────────────

class TestRecency:
    def test_recent_source_scores_full_recency(self, graph):
        _build_graph_with_rule(graph, effective_date="2025-01-01")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.recency == 1.0

    def test_old_source_scores_lower_recency(self, graph):
        _build_graph_with_rule(graph, effective_date="2010-01-01")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.recency == 0.25

    def test_missing_dates_score_neutral(self, graph):
        _build_graph_with_rule(graph, effective_date=None)
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.recency == 0.5

    def test_missing_as_of_date_scores_neutral(self, graph):
        _build_graph_with_rule(graph, effective_date="2025-01-01")
        score = score_rule(graph, "R1", "MU", as_of_date=None)
        assert score.breakdown.recency == 0.5


# ── Completeness ───────────────────────────────────────────────────────────────

class TestCompleteness:
    def test_single_evidence_item_partial_completeness(self, graph):
        _build_graph_with_rule(graph)
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.completeness == 0.75

    def test_two_evidence_items_full_completeness(self, graph):
        _build_graph_with_rule(graph, rule_id="R1", doc_suffix="-a")
        _build_graph_with_rule(graph, rule_id="R1", doc_suffix="-b")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.completeness == 1.0

    def test_completeness_none_for_bare_source_score(self, graph):
        _build_graph_with_rule(graph)
        score = score_authority_source(graph, "src", "MU", as_of_date="2026-07-01")
        assert score.breakdown.completeness is None
        assert score.breakdown.citation_quality is None


# ── Citation quality ───────────────────────────────────────────────────────────

class TestCitationQuality:
    def test_pinpoint_and_text_scores_full(self, graph):
        _build_graph_with_rule(graph, pinpoint="§4.2", citation_text="quoted text")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.citation_quality == 1.0

    def test_pinpoint_only_scores_partial(self, graph):
        _build_graph_with_rule(graph, pinpoint="§4.2", citation_text="")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.citation_quality == 0.65

    def test_neither_scores_low(self, graph):
        _build_graph_with_rule(graph, pinpoint="", citation_text="")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.citation_quality == 0.2


# ── Conflict cap ─────────────────────────────────────────────────────────────

class TestConflictCap:
    def test_unresolved_conflict_caps_at_60(self, graph):
        _build_graph_with_rule(graph, rule_id="R1", tier=AuthorityTier.PRIMARY_LEGISLATION,
                                effective_date="2025-01-01", pinpoint="§1", citation_text="text")
        graph.add_rule(Rule(rule_id="R2", jurisdiction_code="MU", description="conflicting"))
        graph.mark_conflict("R1", "R2")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.conflict_capped is True
        assert score.composite <= CONFLICT_CAP

    def test_no_conflict_not_capped(self, graph):
        _build_graph_with_rule(graph, tier=AuthorityTier.PRIMARY_LEGISLATION,
                                effective_date="2025-01-01", pinpoint="§1", citation_text="text")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.breakdown.conflict_capped is False

    def test_strong_source_would_exceed_cap_without_conflict(self, graph):
        """Sanity check that the cap is actually binding, not coincidental —
        an uncapped identical rule scores meaningfully higher."""
        g1, g2 = EvidenceGraph(), EvidenceGraph()
        for g in (g1, g2):
            _build_graph_with_rule(g, tier=AuthorityTier.PRIMARY_LEGISLATION,
                                    effective_date="2025-01-01", pinpoint="§1", citation_text="text")
        g2.add_rule(Rule(rule_id="R2", jurisdiction_code="MU", description="c"))
        g2.mark_conflict("R1", "R2")
        s_uncapped = score_rule(g1, "R1", "MU", as_of_date="2026-07-01")
        s_capped = score_rule(g2, "R1", "MU", as_of_date="2026-07-01")
        assert s_uncapped.composite > CONFLICT_CAP
        assert s_capped.composite == CONFLICT_CAP


# ── Superseded documents ───────────────────────────────────────────────────────

class TestSupersededPenalty:
    def test_superseded_source_lowers_confidence(self, graph):
        _build_graph_with_rule(graph, effective_date="2025-01-01")
        unpenalized = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        graph.supersede_document_version("v", DocumentVersion(version_id="v2", document_id="doc", version_label="2027"))
        penalized = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert penalized.breakdown.superseded_penalty_applied is True
        assert penalized.composite < unpenalized.composite
        assert penalized.composite == pytest.approx(unpenalized.composite * SUPERSEDED_PENALTY_MULTIPLIER, abs=0.5)

    def test_include_superseded_skips_penalty_for_historical_evaluation(self, graph):
        _build_graph_with_rule(graph, effective_date="2025-01-01")
        graph.supersede_document_version("v", DocumentVersion(version_id="v2", document_id="doc", version_label="2027"))
        historical = score_rule(graph, "R1", "MU", as_of_date="2026-07-01", include_superseded=True)
        assert historical.breakdown.superseded_penalty_applied is False


# ── Absence of authority ─────────────────────────────────────────────────────

class TestAbsenceOfAuthority:
    def test_absence_never_manufactures_confidence(self, graph):
        graph.add_absence_of_authority(AbsenceOfAuthority(
            absence_id="ABS-1", jurisdiction_code="MU", question="q",
            searched_tiers=(AuthorityTier.OFFICIAL_GUIDANCE,),
        ))
        graph.link_recommendation("REC-1", absence_id="ABS-1")
        score = score_recommendation(graph, "REC-1", "MU", as_of_date="2026-07-01")
        assert score.composite == 0.0
        assert score.confidence == QualificationConfidence.LOW
        assert score.breakdown.is_absence_of_authority is True

    def test_score_recommendation_delegates_to_rule_when_chained(self, graph):
        _build_graph_with_rule(graph)
        graph.link_recommendation("REC-2", rule_id="R1")
        score = score_recommendation(graph, "REC-2", "MU", as_of_date="2026-07-01")
        assert score.breakdown.is_absence_of_authority is False
        assert score.composite > 0.0

    def test_score_rule_raises_for_unchained_rule(self, graph):
        graph.add_rule(Rule(rule_id="R-empty", jurisdiction_code="MU", description="no evidence"))
        with pytest.raises(ValueError):
            score_rule(graph, "R-empty", "MU", as_of_date="2026-07-01")


# ── Deterministic scoring ─────────────────────────────────────────────────────

class TestDeterminism:
    def test_identical_inputs_produce_identical_scores(self):
        def build_and_score():
            g = EvidenceGraph()
            _build_graph_with_rule(g)
            return score_rule(g, "R1", "MU", as_of_date="2026-07-01")

        s1, s2 = build_and_score(), build_and_score()
        assert s1.composite == s2.composite
        assert s1.confidence == s2.confidence
        assert s1.breakdown == s2.breakdown


# ── Confidence mapping ─────────────────────────────────────────────────────────

class TestConfidenceMapping:
    def test_high_band(self):
        assert confidence_band(75.0) == QualificationConfidence.HIGH
        assert confidence_band(100.0) == QualificationConfidence.HIGH

    def test_medium_band(self):
        assert confidence_band(74.99) == QualificationConfidence.MEDIUM
        assert confidence_band(40.0) == QualificationConfidence.MEDIUM

    def test_low_band(self):
        assert confidence_band(39.99) == QualificationConfidence.LOW
        assert confidence_band(0.0) == QualificationConfidence.LOW

    def test_strong_rule_reaches_high_confidence(self, graph):
        _build_graph_with_rule(graph, tier=AuthorityTier.PRIMARY_LEGISLATION,
                                effective_date="2025-01-01", pinpoint="§1", citation_text="text")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.confidence == QualificationConfidence.HIGH

    def test_weak_rule_reaches_low_confidence(self, graph):
        _build_graph_with_rule(graph, jurisdiction_code="MT", tier=AuthorityTier.INDUSTRY_CONVENTION,
                                effective_date="2005-01-01", pinpoint="", citation_text="")
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        assert score.confidence == QualificationConfidence.LOW


# ── Score breakdown completeness ─────────────────────────────────────────────

class TestBreakdownCompleteness:
    def test_rule_score_exposes_all_dimensions(self, graph):
        _build_graph_with_rule(graph)
        score = score_rule(graph, "R1", "MU", as_of_date="2026-07-01")
        b = score.breakdown
        for field in ("source_strength", "legal_weight", "jurisdiction_relevance", "recency",
                      "completeness", "citation_quality", "conflict_capped", "superseded_penalty_applied"):
            assert hasattr(b, field)
        assert b.completeness is not None
        assert b.citation_quality is not None
        assert b.notes != ""

    def test_source_score_exposes_all_dimensions_with_notes_explaining_na(self, graph):
        _build_graph_with_rule(graph)
        score = score_authority_source(graph, "src", "MU", as_of_date="2026-07-01")
        assert score.breakdown.notes != ""
        assert "not applicable" in score.breakdown.notes.lower()

    def test_absence_breakdown_has_zeroed_dimensions_and_flag(self, graph):
        graph.add_absence_of_authority(AbsenceOfAuthority(
            absence_id="ABS-1", jurisdiction_code="MU", question="q",
            searched_tiers=(AuthorityTier.PRIMARY_LEGISLATION,),
        ))
        graph.link_recommendation("REC-1", absence_id="ABS-1")
        score = score_recommendation(graph, "REC-1", "MU")
        assert score.breakdown.source_strength == 0.0
        assert score.breakdown.is_absence_of_authority is True
