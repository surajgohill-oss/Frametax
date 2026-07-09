"""
test_evidence_graph.py

Targeted tests for the Phase 1 Evidence Graph core (evidence_graph.py).
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.evidence_graph import (
    EVIDENCE_GRAPH_VERSION,
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
    TIER_BINDING_FORCE,
    binding_force_of,
)


@pytest.fixture()
def graph() -> EvidenceGraph:
    return EvidenceGraph()


def _seed_document_and_source(
    graph: EvidenceGraph,
    doc_id="doc-edb-frs",
    version_id="v1",
    tier=AuthorityTier.OFFICIAL_GUIDANCE,
    source_id="src-edb-frs-guidance",
):
    doc = graph.add_document(Document(
        document_id=doc_id, jurisdiction_code="MU",
        title="EDB Film Rebate Scheme Guidelines", source_url="https://edbmauritius.org/frs",
    ))
    version = graph.add_document_version(DocumentVersion(
        version_id=version_id, document_id=doc_id, version_label="2022",
        publication_date="2022-10-01", effective_date="2022-10-01", retrieved_date="2026-07-01",
        excerpt="QPE means Qualifying Production Expenditure incurred and spent in Mauritius.",
    ))
    source = graph.add_authority_source(AuthoritySource(
        source_id=source_id, jurisdiction_code="MU", tier=tier,
        authority_body="Economic Development Board Mauritius", title="Film Rebate Scheme Guidelines",
        document_version_id=version_id,
    ))
    return doc, version, source


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert EVIDENCE_GRAPH_VERSION == "1.0.0"

    def test_fourteen_tiers(self):
        assert len(AuthorityTier) == 14

    def test_tier_ordering_matches_hierarchy(self):
        assert AuthorityTier.PRIMARY_LEGISLATION.value == 1
        assert AuthorityTier.OPTIMIZER_ASSUMPTION.value == 14
        assert AuthorityTier.PRIMARY_LEGISLATION.value < AuthorityTier.REGULATIONS.value
        assert AuthorityTier.INDUSTRY_CONVENTION.value < AuthorityTier.OPTIMIZER_ASSUMPTION.value

    def test_every_tier_has_binding_force(self):
        for tier in AuthorityTier:
            assert tier in TIER_BINDING_FORCE

    def test_optimizer_assumption_is_not_authority(self):
        assert binding_force_of(AuthorityTier.OPTIMIZER_ASSUMPTION) == BindingForce.NOT_AUTHORITY

    def test_primary_legislation_is_binding(self):
        assert binding_force_of(AuthorityTier.PRIMARY_LEGISLATION) == BindingForce.BINDING


# ── Authority sources ─────────────────────────────────────────────────────────

class TestAuthoritySources:
    def test_create_document_and_version(self, graph):
        doc, version, source = _seed_document_and_source(graph)
        assert doc.jurisdiction_code == "MU"
        assert version.document_id == doc.document_id
        assert source.document_version_id == version.version_id

    def test_duplicate_document_rejected(self, graph):
        _seed_document_and_source(graph)
        with pytest.raises(ValueError):
            graph.add_document(Document(document_id="doc-edb-frs", jurisdiction_code="MU", title="dup"))

    def test_authority_source_requires_existing_version(self, graph):
        with pytest.raises(ValueError):
            graph.add_authority_source(AuthoritySource(
                source_id="src-x", jurisdiction_code="MU", tier=AuthorityTier.OFFICIAL_GUIDANCE,
                authority_body="EDB", title="x", document_version_id="does-not-exist",
            ))

    def test_authority_source_carries_tier_and_binding_force(self, graph):
        _, _, source = _seed_document_and_source(graph, tier=AuthorityTier.REGULATIONS)
        assert source.tier == AuthorityTier.REGULATIONS
        assert source.binding_force == BindingForce.BINDING


# ── Document versions: immutability, supersession ────────────────────────────

class TestDocumentVersions:
    def test_document_version_is_frozen(self, graph):
        _, version, _ = _seed_document_and_source(graph)
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError is a subclass of AttributeError
            version.excerpt = "tampered"

    def test_supersede_creates_new_version_without_mutating_old(self, graph):
        doc, v1, _ = _seed_document_and_source(graph)
        v1_snapshot = copy.deepcopy(v1)
        v2 = graph.supersede_document_version(
            "v1",
            DocumentVersion(version_id="v2", document_id=doc.document_id, version_label="2026",
                             publication_date="2026-01-15", effective_date="2026-02-01",
                             excerpt="Updated QPE definition."),
        )
        assert v1 == v1_snapshot  # old record byte-for-byte unchanged
        assert graph.is_superseded("v1") is True
        assert graph.superseding_version_id("v1") == "v2"
        assert graph.is_superseded("v2") is False

    def test_double_supersession_rejected(self, graph):
        doc, _, _ = _seed_document_and_source(graph)
        graph.supersede_document_version(
            "v1", DocumentVersion(version_id="v2", document_id=doc.document_id, version_label="2026"))
        with pytest.raises(ValueError):
            graph.supersede_document_version(
                "v1", DocumentVersion(version_id="v3", document_id=doc.document_id, version_label="2027"))

    def test_current_version_returns_latest_non_superseded(self, graph):
        doc, _, _ = _seed_document_and_source(graph)
        graph.supersede_document_version(
            "v1", DocumentVersion(version_id="v2", document_id=doc.document_id, version_label="2026"))
        current = graph.current_version(doc.document_id)
        assert current.version_id == "v2"

    def test_version_history_preserves_all_versions_oldest_first(self, graph):
        doc, _, _ = _seed_document_and_source(graph)
        graph.supersede_document_version(
            "v1", DocumentVersion(version_id="v2", document_id=doc.document_id, version_label="2026"))
        history = graph.version_history(doc.document_id)
        assert [v.version_id for v in history] == ["v1", "v2"]

    def test_citing_a_superseded_version_still_resolves(self, graph):
        """Old citations must remain fully traceable even after supersession —
        history is never rewritten out from under a past recommendation."""
        doc, v1, source = _seed_document_and_source(graph)
        rule = graph.add_rule(Rule(rule_id="R1", jurisdiction_code="MU", description="test rule"))
        citation = graph.add_citation(Citation(
            citation_id="C1", authority_source_id=source.source_id,
            document_version_id="v1", pinpoint="p.4", citation_text="QPE definition",
        ))
        graph.add_evidence(Evidence(evidence_id="E1", rule_id="R1", citation_id="C1", description="supports"))
        graph.supersede_document_version(
            "v1", DocumentVersion(version_id="v2", document_id=doc.document_id, version_label="2026"))
        chain = graph.trace_rule("R1")
        assert len(chain) == 1
        assert chain[0]["superseded"] is True
        assert chain[0]["document_version"].version_id == "v1"


# ── Full chain: rule -> evidence -> authority -> citation -> document version ──

class TestFullChain:
    def test_rule_evidence_citation_chain(self, graph):
        _, v1, source = _seed_document_and_source(graph)
        graph.add_rule(Rule(rule_id="R-QPE-TERRITORIAL", jurisdiction_code="MU",
                             description="QPE must be incurred and spent in Mauritius."))
        graph.add_citation(Citation(
            citation_id="C1", authority_source_id=source.source_id, document_version_id=v1.version_id,
            pinpoint="Guideline 2.1", citation_text="incurred and spent in Mauritius",
        ))
        graph.add_evidence(Evidence(
            evidence_id="E1", rule_id="R-QPE-TERRITORIAL", citation_id="C1",
            description="Territorial nexus requirement", supports_inclusion=False,
        ))
        assert graph.rule_is_fully_chained("R-QPE-TERRITORIAL") is True
        chain = graph.trace_rule("R-QPE-TERRITORIAL")
        assert len(chain) == 1
        assert chain[0]["authority_source"].tier == AuthorityTier.OFFICIAL_GUIDANCE
        assert chain[0]["document"].jurisdiction_code == "MU"

    def test_rule_with_no_evidence_is_not_fully_chained(self, graph):
        graph.add_rule(Rule(rule_id="R-EMPTY", jurisdiction_code="MU", description="unsupported"))
        assert graph.rule_is_fully_chained("R-EMPTY") is False

    def test_evidence_requires_existing_rule_and_citation(self, graph):
        _, v1, source = _seed_document_and_source(graph)
        graph.add_citation(Citation(citation_id="C1", authority_source_id=source.source_id,
                                     document_version_id=v1.version_id, pinpoint="p.1"))
        with pytest.raises(ValueError):
            graph.add_evidence(Evidence(evidence_id="E1", rule_id="no-such-rule", citation_id="C1", description="x"))


# ── Absence of authority ─────────────────────────────────────────────────────

class TestAbsenceOfAuthority:
    def test_create_absence(self, graph):
        absence = graph.add_absence_of_authority(AbsenceOfAuthority(
            absence_id="ABS-ATL-SCOPE", jurisdiction_code="MU",
            question="Does ATL (writer/director/producer) spend qualify as QPE?",
            searched_tiers=(AuthorityTier.PRIMARY_LEGISLATION, AuthorityTier.REGULATIONS,
                             AuthorityTier.OFFICIAL_GUIDANCE, AuthorityTier.OFFICIAL_FAQ),
            notes="No guidance located across four tiers searched.",
        ))
        assert absence.jurisdiction_code == "MU"
        assert AuthorityTier.OFFICIAL_GUIDANCE in absence.searched_tiers

    def test_duplicate_absence_rejected(self, graph):
        graph.add_absence_of_authority(AbsenceOfAuthority(
            absence_id="ABS-1", jurisdiction_code="MU", question="q",
            searched_tiers=(AuthorityTier.OFFICIAL_GUIDANCE,),
        ))
        with pytest.raises(ValueError):
            graph.add_absence_of_authority(AbsenceOfAuthority(
                absence_id="ABS-1", jurisdiction_code="MU", question="q2",
                searched_tiers=(AuthorityTier.OFFICIAL_GUIDANCE,),
            ))


# ── Terminal-node discipline: no dead ends ────────────────────────────────────

class TestTerminalNodeDiscipline:
    def test_recommendation_links_to_fully_chained_rule(self, graph):
        _, v1, source = _seed_document_and_source(graph)
        graph.add_rule(Rule(rule_id="R1", jurisdiction_code="MU", description="rule"))
        graph.add_citation(Citation(citation_id="C1", authority_source_id=source.source_id,
                                     document_version_id=v1.version_id, pinpoint="p.1"))
        graph.add_evidence(Evidence(evidence_id="E1", rule_id="R1", citation_id="C1", description="x"))
        link = graph.link_recommendation("REC-1", rule_id="R1")
        assert link == {"rule_id": "R1"}
        trace = graph.trace_recommendation("REC-1")
        assert trace["terminus"] == "rule"
        assert len(trace["chain"]) == 1

    def test_recommendation_links_to_absence(self, graph):
        graph.add_absence_of_authority(AbsenceOfAuthority(
            absence_id="ABS-1", jurisdiction_code="MU", question="q",
            searched_tiers=(AuthorityTier.OFFICIAL_GUIDANCE,),
        ))
        graph.link_recommendation("REC-2", absence_id="ABS-1")
        trace = graph.trace_recommendation("REC-2")
        assert trace["terminus"] == "absence_of_authority"
        assert trace["absence"].absence_id == "ABS-1"

    def test_recommendation_cannot_link_to_evidence_less_rule(self, graph):
        """The core dead-end prevention: a rule with no evidence must not
        be linkable to a recommendation — that would be a silent gap."""
        graph.add_rule(Rule(rule_id="R-EMPTY", jurisdiction_code="MU", description="no evidence yet"))
        with pytest.raises(ValueError, match="not fully chained"):
            graph.link_recommendation("REC-3", rule_id="R-EMPTY")

    def test_recommendation_requires_exactly_one_terminus(self, graph):
        with pytest.raises(ValueError):
            graph.link_recommendation("REC-4")  # neither rule_id nor absence_id
        graph.add_absence_of_authority(AbsenceOfAuthority(
            absence_id="ABS-X", jurisdiction_code="MU", question="q",
            searched_tiers=(AuthorityTier.OFFICIAL_GUIDANCE,),
        ))
        graph.add_rule(Rule(rule_id="R-X", jurisdiction_code="MU", description="d"))
        # both given — also rejected, even though absence exists and rule doesn't validate
        with pytest.raises(ValueError):
            graph.link_recommendation("REC-5", rule_id="R-X", absence_id="ABS-X")

    def test_unlinked_recommendation_trace_raises(self, graph):
        with pytest.raises(ValueError):
            graph.trace_recommendation("REC-NEVER-LINKED")

    def test_evidence_pointing_to_missing_citation_blocks_chaining(self, graph):
        """Defense in depth: even if an Evidence row is malformed downstream,
        rule_is_fully_chained must not report success."""
        _, v1, source = _seed_document_and_source(graph)
        graph.add_rule(Rule(rule_id="R1", jurisdiction_code="MU", description="rule"))
        graph.add_citation(Citation(citation_id="C1", authority_source_id=source.source_id,
                                     document_version_id=v1.version_id, pinpoint="p.1"))
        graph.add_evidence(Evidence(evidence_id="E1", rule_id="R1", citation_id="C1", description="x"))
        # Manually corrupt the graph's citation index to simulate a broken chain
        del graph._citations["C1"]
        assert graph.rule_is_fully_chained("R1") is False


# ── Rule relationships: conflicts, comparable jurisdictions ──────────────────

class TestRuleRelationships:
    def test_mark_conflict_is_symmetric(self, graph):
        graph.add_rule(Rule(rule_id="R1", jurisdiction_code="MU", description="a"))
        graph.add_rule(Rule(rule_id="R2", jurisdiction_code="MU", description="b"))
        graph.mark_conflict("R1", "R2")
        assert graph.conflicts_of("R1") == {"R2"}
        assert graph.conflicts_of("R2") == {"R1"}

    def test_conflict_requires_existing_rules(self, graph):
        graph.add_rule(Rule(rule_id="R1", jurisdiction_code="MU", description="a"))
        with pytest.raises(ValueError):
            graph.mark_conflict("R1", "no-such-rule")

    def test_mark_comparable_is_symmetric(self, graph):
        graph.add_rule(Rule(rule_id="R-MU", jurisdiction_code="MU", description="MU rule"))
        graph.add_rule(Rule(rule_id="R-MT", jurisdiction_code="MT", description="MT rule"))
        graph.mark_comparable("R-MU", "R-MT")
        assert graph.comparable_to("R-MU") == {"R-MT"}
        assert graph.comparable_to("R-MT") == {"R-MU"}

    def test_conflicts_and_comparable_are_independent(self, graph):
        graph.add_rule(Rule(rule_id="R1", jurisdiction_code="MU", description="a"))
        graph.add_rule(Rule(rule_id="R2", jurisdiction_code="MT", description="b"))
        graph.mark_comparable("R1", "R2")
        assert graph.conflicts_of("R1") == set()
        assert graph.comparable_to("R1") == {"R2"}

    def test_trace_recommendation_surfaces_conflicts_and_comparables(self, graph):
        _, v1, source = _seed_document_and_source(graph)
        graph.add_rule(Rule(rule_id="R1", jurisdiction_code="MU", description="a"))
        graph.add_rule(Rule(rule_id="R2", jurisdiction_code="MU", description="conflicting"))
        graph.add_rule(Rule(rule_id="R3", jurisdiction_code="MT", description="comparable"))
        graph.add_citation(Citation(citation_id="C1", authority_source_id=source.source_id,
                                     document_version_id=v1.version_id, pinpoint="p.1"))
        graph.add_evidence(Evidence(evidence_id="E1", rule_id="R1", citation_id="C1", description="x"))
        graph.mark_conflict("R1", "R2")
        graph.mark_comparable("R1", "R3")
        graph.link_recommendation("REC-1", rule_id="R1")
        trace = graph.trace_recommendation("REC-1")
        assert trace["conflicts"] == {"R2"}
        assert trace["comparable_rules"] == {"R3"}


# ── Determinism ────────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_identical_construction_produces_identical_traces(self):
        def build():
            g = EvidenceGraph()
            _, v1, source = _seed_document_and_source(g)
            g.add_rule(Rule(rule_id="R1", jurisdiction_code="MU", description="rule"))
            g.add_citation(Citation(citation_id="C1", authority_source_id=source.source_id,
                                     document_version_id=v1.version_id, pinpoint="p.1"))
            g.add_evidence(Evidence(evidence_id="E1", rule_id="R1", citation_id="C1", description="x"))
            g.link_recommendation("REC-1", rule_id="R1")
            return g

        g1, g2 = build(), build()
        t1, t2 = g1.trace_recommendation("REC-1"), g2.trace_recommendation("REC-1")
        assert t1["chain"][0]["citation"] == t2["chain"][0]["citation"]
        assert t1["chain"][0]["document_version"] == t2["chain"][0]["document_version"]

    def test_no_hidden_wall_clock_dependency(self, graph):
        """All dates are caller-supplied; a version created without dates
        must not silently stamp 'now'."""
        doc = graph.add_document(Document(document_id="d1", jurisdiction_code="MU", title="t"))
        version = graph.add_document_version(DocumentVersion(version_id="v1", document_id="d1", version_label="x"))
        assert version.publication_date is None
        assert version.retrieved_date is None
