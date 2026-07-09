"""
evidence_graph.py

Phase 1 of the CineAtlas Authority & Evidence Engine: the foundational
node/edge model that future Authority Scoring (Phase 2), grey-area
resolution migration (Phase 3), jurisdiction intelligence (Phase 5), and
optimizer explanations will consume.

This module introduces no behavior change to existing calculators. It is
a standalone, additive data model — qualification_model.py,
optimization_engine.py, and structuring_paths.py are untouched.

Graph shape (see the Authority & Evidence Engine architecture document):

    Recommendation --DERIVES_FROM--> Rule --SUPPORTED_BY--> Evidence
                                                                |
                                                          CITES v
                                                          AuthoritySource
                                                                |
                                                   HAS_CITATION v
                                                            Citation
                                                                |
                                                     POINTS_TO v
                                                            Document
                                                                |
                                                    HAS_VERSION v
                                                          DocumentVersion

    Rule --CONFLICTS_WITH--> Rule
    Rule --COMPARABLE_TO--> Rule
    Recommendation --(no rule support)--> AbsenceOfAuthority

Design principles enforced here:

1. Append-only version discipline. DocumentVersion is immutable
   (frozen dataclass) — it is never edited in place. Superseding a
   version creates a NEW DocumentVersion and a SUPERSEDED_BY edge
   recorded on the graph (not a field mutated on the old version).
   "Superseded" status is therefore always a graph query, never a
   stored flag that could silently be toggled on a supposedly
   immutable record.

2. Terminal-node discipline. EvidenceGraph.link_recommendation()
   refuses to create a dead end: a Recommendation must resolve either
   to a Rule with at least one fully-chained Evidence -> AuthoritySource
   -> Citation -> DocumentVersion path, or to an explicit
   AbsenceOfAuthority object. There is no third option and no silent
   partial link.

3. Authority hierarchy. AuthorityTier encodes the 14 tiers from the
   architecture document, each with a fixed BindingForce. No numeric
   scoring is implemented here — that is Phase 2.

No LLM calls. No wall-clock dependency — every date is a caller-supplied
ISO string, never auto-stamped, so graphs are fully deterministic and
testable.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

EVIDENCE_GRAPH_VERSION = "1.0.0"


# ── Authority hierarchy (14 tiers) ──────────────────────────────────────────

class AuthorityTier(int, enum.Enum):
    """Ranked 1 (strongest) to 14 (weakest). A lower tier can supplement
    a gap in a higher tier; it can never override one."""
    PRIMARY_LEGISLATION = 1
    REGULATIONS = 2
    BINDING_RULING = 3
    PUBLISHED_RULING = 4
    OFFICIAL_GUIDANCE = 5
    OFFICIAL_FAQ = 6
    AGENCY_MANUAL = 7
    TECHNICAL_BULLETIN = 8
    PRECEDENT_PRODUCTION = 9
    ACCOUNTING_GUIDANCE = 10
    LEGAL_OPINION = 11
    TAX_OPINION = 12
    INDUSTRY_CONVENTION = 13
    OPTIMIZER_ASSUMPTION = 14


class BindingForce(str, enum.Enum):
    BINDING = "binding"
    BINDING_GENERAL = "binding_general"
    PERSUASIVE_STRONG = "persuasive_strong"
    PERSUASIVE = "persuasive"
    EVIDENTIARY = "evidentiary"
    INTERPRETIVE = "interpretive"
    WEAKEST_DEFENSIBLE = "weakest_defensible"
    NOT_AUTHORITY = "not_authority"


# Tier -> binding force. Fixed, not configurable per-instance — binding
# force is a property of the tier, not of any individual source.
TIER_BINDING_FORCE: dict[AuthorityTier, BindingForce] = {
    AuthorityTier.PRIMARY_LEGISLATION: BindingForce.BINDING,
    AuthorityTier.REGULATIONS: BindingForce.BINDING,
    AuthorityTier.BINDING_RULING: BindingForce.BINDING,
    AuthorityTier.PUBLISHED_RULING: BindingForce.BINDING_GENERAL,
    AuthorityTier.OFFICIAL_GUIDANCE: BindingForce.PERSUASIVE_STRONG,
    AuthorityTier.OFFICIAL_FAQ: BindingForce.PERSUASIVE_STRONG,
    AuthorityTier.AGENCY_MANUAL: BindingForce.PERSUASIVE,
    AuthorityTier.TECHNICAL_BULLETIN: BindingForce.PERSUASIVE,
    AuthorityTier.PRECEDENT_PRODUCTION: BindingForce.EVIDENTIARY,
    AuthorityTier.ACCOUNTING_GUIDANCE: BindingForce.EVIDENTIARY,
    AuthorityTier.LEGAL_OPINION: BindingForce.INTERPRETIVE,
    AuthorityTier.TAX_OPINION: BindingForce.INTERPRETIVE,
    AuthorityTier.INDUSTRY_CONVENTION: BindingForce.WEAKEST_DEFENSIBLE,
    AuthorityTier.OPTIMIZER_ASSUMPTION: BindingForce.NOT_AUTHORITY,
}


def binding_force_of(tier: AuthorityTier) -> BindingForce:
    return TIER_BINDING_FORCE[tier]


# ── Node types ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Document:
    """A source document's identity — title, jurisdiction, where it came
    from. Distinct from DocumentVersion: a Document may have many
    versions over time; the Document record itself never changes."""
    document_id: str
    jurisdiction_code: str
    title: str
    source_url: Optional[str] = None
    notes: str = ""


@dataclass(frozen=True)
class DocumentVersion:
    """
    Immutable. Never edited in place. All dates are caller-supplied ISO
    strings (YYYY-MM-DD) — no wall-clock defaults, so graphs are fully
    deterministic and reproducible in tests.

    "Superseded" status is intentionally NOT a field here — see
    EvidenceGraph.supersede_document_version() / is_superseded(). Baking
    a mutable-looking flag onto an immutable record invites exactly the
    silent-edit failure mode this model exists to prevent.
    """
    version_id: str
    document_id: str
    version_label: str
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    retrieved_date: Optional[str] = None
    excerpt: Optional[str] = None


@dataclass(frozen=True)
class AuthoritySource:
    source_id: str
    jurisdiction_code: str
    tier: AuthorityTier
    authority_body: str
    title: str
    document_version_id: str

    @property
    def binding_force(self) -> BindingForce:
        return binding_force_of(self.tier)


@dataclass(frozen=True)
class Citation:
    citation_id: str
    authority_source_id: str
    document_version_id: str
    pinpoint: str            # e.g. "§4.2", "p.4", "Guideline 3.1"
    citation_text: str = ""  # quoted or closely paraphrased text


@dataclass(frozen=True)
class Evidence:
    """Links a Rule to a Citation — the specific textual support for a
    rule's conclusion."""
    evidence_id: str
    rule_id: str
    citation_id: str
    description: str
    supports_inclusion: Optional[bool] = None  # True/False/None (neutral/contextual)


@dataclass
class Rule:
    """
    A jurisdiction-specific rule statement. evidence_ids may be empty at
    creation — a Rule with zero evidence can never be linked to a
    Recommendation directly (see link_recommendation); it must either
    gain evidence or the recommendation must cite AbsenceOfAuthority
    instead. Rule is mutable only in the sense that evidence/conflict/
    comparable edges accumulate on the graph, not that its own fields
    are rewritten.
    """
    rule_id: str
    jurisdiction_code: str
    description: str
    evidence_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AbsenceOfAuthority:
    """
    The explicit terminal node for an unresolved question — the object
    that makes "we looked and found nothing" a first-class, queryable
    fact instead of a silent gap. searched_tiers records which tiers of
    the hierarchy were actually checked, so "absence" is itself
    evidenced, not assumed.
    """
    absence_id: str
    jurisdiction_code: str
    question: str
    searched_tiers: tuple[AuthorityTier, ...]
    notes: str = ""


# ── Graph container ──────────────────────────────────────────────────────

class EvidenceGraph:
    """
    In-memory graph. All mutation happens through explicit methods that
    enforce the append-only and terminal-node disciplines — there is no
    public API to edit a DocumentVersion or to link a Recommendation to
    an evidence-less Rule.
    """

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}
        self._versions: dict[str, DocumentVersion] = {}
        self._sources: dict[str, AuthoritySource] = {}
        self._citations: dict[str, Citation] = {}
        self._evidence: dict[str, Evidence] = {}
        self._rules: dict[str, Rule] = {}
        self._absences: dict[str, AbsenceOfAuthority] = {}
        self._superseded_by: dict[str, str] = {}   # old_version_id -> new_version_id
        self._conflicts: dict[str, set[str]] = {}  # rule_id -> set(rule_id)
        self._comparable: dict[str, set[str]] = {}  # rule_id -> set(rule_id)
        self._recommendation_links: dict[str, dict] = {}  # recommendation_id -> {"rule_id"|"absence_id": ...}

    # ── document / version ──────────────────────────────────────────────

    def add_document(self, doc: Document) -> Document:
        if doc.document_id in self._documents:
            raise ValueError(f"Document '{doc.document_id}' already exists.")
        self._documents[doc.document_id] = doc
        return doc

    def add_document_version(self, version: DocumentVersion) -> DocumentVersion:
        if version.document_id not in self._documents:
            raise ValueError(f"Document '{version.document_id}' does not exist.")
        if version.version_id in self._versions:
            raise ValueError(f"DocumentVersion '{version.version_id}' already exists.")
        self._versions[version.version_id] = version
        return version

    def supersede_document_version(
        self, old_version_id: str, new_version: DocumentVersion
    ) -> DocumentVersion:
        """
        The only sanctioned way to retire a DocumentVersion. Does NOT
        mutate old_version_id's record — it adds the new version and
        records a SUPERSEDED_BY edge. The old version remains exactly as
        it was, forever queryable by anything that already cited it.
        """
        if old_version_id not in self._versions:
            raise ValueError(f"DocumentVersion '{old_version_id}' does not exist.")
        if old_version_id in self._superseded_by:
            raise ValueError(f"DocumentVersion '{old_version_id}' is already superseded.")
        self.add_document_version(new_version)
        self._superseded_by[old_version_id] = new_version.version_id
        return new_version

    def is_superseded(self, version_id: str) -> bool:
        return version_id in self._superseded_by

    def superseding_version_id(self, version_id: str) -> Optional[str]:
        return self._superseded_by.get(version_id)

    def current_version(self, document_id: str) -> Optional[DocumentVersion]:
        """The most recent non-superseded version of a document, walking
        the SUPERSEDED_BY chain forward from every version of it."""
        candidates = [v for v in self._versions.values() if v.document_id == document_id]
        current = [v for v in candidates if not self.is_superseded(v.version_id)]
        return current[0] if len(current) == 1 else (current[-1] if current else None)

    def version_history(self, document_id: str) -> list[DocumentVersion]:
        """Full version history for a document, oldest first, each entry
        annotated with its own immutable fields — nothing recomputed."""
        return sorted(
            (v for v in self._versions.values() if v.document_id == document_id),
            key=lambda v: v.version_id,
        )

    def get_document_version(self, version_id: str) -> DocumentVersion:
        if version_id not in self._versions:
            raise ValueError(f"DocumentVersion '{version_id}' does not exist.")
        return self._versions[version_id]

    # ── authority source / citation ─────────────────────────────────────

    def add_authority_source(self, source: AuthoritySource) -> AuthoritySource:
        if source.document_version_id not in self._versions:
            raise ValueError(
                f"AuthoritySource '{source.source_id}' references unknown "
                f"DocumentVersion '{source.document_version_id}'."
            )
        if source.source_id in self._sources:
            raise ValueError(f"AuthoritySource '{source.source_id}' already exists.")
        self._sources[source.source_id] = source
        return source

    def get_authority_source(self, source_id: str) -> AuthoritySource:
        if source_id not in self._sources:
            raise ValueError(f"AuthoritySource '{source_id}' does not exist.")
        return self._sources[source_id]

    def add_citation(self, citation: Citation) -> Citation:
        if citation.authority_source_id not in self._sources:
            raise ValueError(f"Citation references unknown AuthoritySource '{citation.authority_source_id}'.")
        if citation.document_version_id not in self._versions:
            raise ValueError(f"Citation references unknown DocumentVersion '{citation.document_version_id}'.")
        if citation.citation_id in self._citations:
            raise ValueError(f"Citation '{citation.citation_id}' already exists.")
        self._citations[citation.citation_id] = citation
        return citation

    # ── evidence / rule ──────────────────────────────────────────────────

    def add_rule(self, rule: Rule) -> Rule:
        if rule.rule_id in self._rules:
            raise ValueError(f"Rule '{rule.rule_id}' already exists.")
        self._rules[rule.rule_id] = rule
        return rule

    def get_rule(self, rule_id: str) -> Rule:
        if rule_id not in self._rules:
            raise ValueError(f"Rule '{rule_id}' does not exist.")
        return self._rules[rule_id]

    def add_evidence(self, evidence: Evidence) -> Evidence:
        if evidence.rule_id not in self._rules:
            raise ValueError(f"Evidence references unknown Rule '{evidence.rule_id}'.")
        if evidence.citation_id not in self._citations:
            raise ValueError(f"Evidence references unknown Citation '{evidence.citation_id}'.")
        if evidence.evidence_id in self._evidence:
            raise ValueError(f"Evidence '{evidence.evidence_id}' already exists.")
        self._evidence[evidence.evidence_id] = evidence
        self._rules[evidence.rule_id].evidence_ids.append(evidence.evidence_id)
        return evidence

    def add_absence_of_authority(self, absence: AbsenceOfAuthority) -> AbsenceOfAuthority:
        if absence.absence_id in self._absences:
            raise ValueError(f"AbsenceOfAuthority '{absence.absence_id}' already exists.")
        self._absences[absence.absence_id] = absence
        return absence

    # ── rule relationships ───────────────────────────────────────────────

    def mark_conflict(self, rule_id_a: str, rule_id_b: str) -> None:
        for rid in (rule_id_a, rule_id_b):
            if rid not in self._rules:
                raise ValueError(f"Rule '{rid}' does not exist.")
        self._conflicts.setdefault(rule_id_a, set()).add(rule_id_b)
        self._conflicts.setdefault(rule_id_b, set()).add(rule_id_a)

    def conflicts_of(self, rule_id: str) -> set[str]:
        return set(self._conflicts.get(rule_id, set()))

    def mark_comparable(self, rule_id_a: str, rule_id_b: str) -> None:
        for rid in (rule_id_a, rule_id_b):
            if rid not in self._rules:
                raise ValueError(f"Rule '{rid}' does not exist.")
        self._comparable.setdefault(rule_id_a, set()).add(rule_id_b)
        self._comparable.setdefault(rule_id_b, set()).add(rule_id_a)

    def comparable_to(self, rule_id: str) -> set[str]:
        return set(self._comparable.get(rule_id, set()))

    # ── rule -> full evidence chain resolution ──────────────────────────

    def rule_is_fully_chained(self, rule_id: str) -> bool:
        """
        True only if the rule has at least one Evidence item, and every
        one of those Evidence items resolves through a Citation to an
        AuthoritySource to a DocumentVersion. A rule with evidence_ids
        pointing nowhere real is NOT fully chained — this is the check
        that prevents a dead end from being papered over by an empty
        Evidence stub.
        """
        rule = self._rules.get(rule_id)
        if not rule or not rule.evidence_ids:
            return False
        for eid in rule.evidence_ids:
            ev = self._evidence.get(eid)
            if ev is None:
                return False
            cit = self._citations.get(ev.citation_id)
            if cit is None:
                return False
            if cit.authority_source_id not in self._sources:
                return False
            if cit.document_version_id not in self._versions:
                return False
        return True

    def trace_rule(self, rule_id: str) -> list[dict]:
        """Return the resolved evidence chain for a rule: one dict per
        Evidence item with its full Citation -> AuthoritySource ->
        DocumentVersion -> Document resolution, for display/audit."""
        rule = self._rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule '{rule_id}' does not exist.")
        chain: list[dict] = []
        for eid in rule.evidence_ids:
            ev = self._evidence[eid]
            cit = self._citations[ev.citation_id]
            src = self._sources[cit.authority_source_id]
            ver = self._versions[cit.document_version_id]
            doc = self._documents[ver.document_id]
            chain.append({
                "evidence": ev, "citation": cit, "authority_source": src,
                "document_version": ver, "document": doc,
                "superseded": self.is_superseded(ver.version_id),
            })
        return chain

    # ── recommendation linking (terminal-node discipline) ────────────────

    def link_recommendation(
        self,
        recommendation_id: str,
        rule_id: Optional[str] = None,
        absence_id: Optional[str] = None,
    ) -> dict:
        """
        The single entry point for attaching a Recommendation to the
        graph. Enforces terminal-node discipline: exactly one of
        rule_id / absence_id must be given, and if rule_id is given, the
        rule must be fully chained to a real authority. There is no way
        to call this method and produce a dead end.
        """
        if (rule_id is None) == (absence_id is None):
            raise ValueError(
                "link_recommendation requires exactly one of rule_id or absence_id."
            )
        if rule_id is not None:
            if rule_id not in self._rules:
                raise ValueError(f"Rule '{rule_id}' does not exist.")
            if not self.rule_is_fully_chained(rule_id):
                raise ValueError(
                    f"Rule '{rule_id}' is not fully chained to an authority source — "
                    "cannot link a recommendation to it. Either add evidence that "
                    "resolves to a real AuthoritySource/Citation/DocumentVersion, "
                    "or link the recommendation to an AbsenceOfAuthority instead."
                )
            link = {"rule_id": rule_id}
        else:
            if absence_id not in self._absences:
                raise ValueError(f"AbsenceOfAuthority '{absence_id}' does not exist.")
            link = {"absence_id": absence_id}
        self._recommendation_links[recommendation_id] = link
        return link

    def trace_recommendation(self, recommendation_id: str) -> dict:
        """
        Resolve a Recommendation to its terminus: either the full rule
        evidence chain, or the AbsenceOfAuthority object. Raises if the
        recommendation was never linked — an unlinked recommendation is
        itself a dead end this method refuses to paper over.
        """
        link = self._recommendation_links.get(recommendation_id)
        if link is None:
            raise ValueError(
                f"Recommendation '{recommendation_id}' has no evidence link — "
                "call link_recommendation() first."
            )
        if "rule_id" in link:
            rule_id = link["rule_id"]
            return {
                "recommendation_id": recommendation_id,
                "terminus": "rule",
                "rule": self._rules[rule_id],
                "chain": self.trace_rule(rule_id),
                "conflicts": self.conflicts_of(rule_id),
                "comparable_rules": self.comparable_to(rule_id),
            }
        absence = self._absences[link["absence_id"]]
        return {
            "recommendation_id": recommendation_id,
            "terminus": "absence_of_authority",
            "absence": absence,
        }
