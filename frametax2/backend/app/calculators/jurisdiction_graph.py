"""
jurisdiction_graph.py

Phase 5A/5B of the CineGlobe Production Intelligence Graph: the
Jurisdiction Graph wiring layer.

This module does not collect new data and does not compute anything. It
is a generic, non-jurisdiction-specific wrapper that reads the jurisdiction
and program facts already modeled elsewhere in this codebase —

  - app/calculators/jurisdiction_comparison.py (ALL_PROFILES, GAP_MATRIX)
  - app/calculators/treaty_engine.py (_BILATERAL, _MULTILATERAL, via its
    public getters)
  - app/calculators/qualification_model.py (REINVESTMENT_REGISTRY)
  - app/calculators/levers.py (Lever / derive_levers, for Little Utopia /
    Mauritius only, the one jurisdiction with a populated qualification
    register in this codebase today)

— and arranges them as graph nodes (Country, NationalProgram,
RegionalProgram, MunicipalProgram, Treaty, Fund, Agency, Requirement,
Restriction, Absence) connected by typed, evidence-capable Relationship
edges (CONTAINS, ADMINISTERED_BY, FUNDED_BY, PARTY_TO, STACKS_WITH,
RESTRICTED_BY, REQUIRES, HAS_REINVESTMENT_PROFILE, COMPARABLE_TO,
HAS_AVAILABLE_LEVER).

No per-jurisdiction custom code: build_jurisdiction_graph() below loops
generically over the existing data structures. There is deliberately no
"if code == 'MU': ..." branch anywhere in this module — every jurisdiction
present in ALL_PROFILES is wired identically. Where a fact is not present
in the source data (e.g. no RegionalProgram/MunicipalProgram is modeled
anywhere yet, or no treaty involves Mauritius), the graph carries an
explicit UNKNOWN or ABSENCE placeholder node/relationship rather than
silently omitting it or inventing a value.

Phase 5B strengthens the Requirement/Restriction wiring so every program
explicitly represents 11 minimum fact categories (minimum spend, eligible
production types, territorial nexus, local entity requirement, cultural
test / local contribution, cap / funding window, stacking rule,
reinvestment treatment, treaty availability, application timing /
deadline, payout timing). Two of `JurisdictionIncentiveProfile`'s own
Optional fields distinguish "field exists, value unknown" (FactStatus.
UNKNOWN, e.g. Mauritius's min_spend_local=None) from "no field for this
fact category exists anywhere in the source data at all" (FactStatus.
ABSENT, e.g. eligible_production_types, territorial_nexus, local_entity_
requirement, stacking_rule, application_timing_deadline — none of which
JurisdictionIncentiveProfile models for any jurisdiction). Both are
queryable via get_program_unknowns() rather than silently dropped.

No optimizer behavior change: optimization_engine.py is not imported and
not modified. This module is purely additive.

No LLM calls.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from app.calculators import jurisdiction_comparison as jc
from app.calculators import treaty_engine as te
from app.calculators.qualification_model import (
    REINVESTMENT_REGISTRY,
    ReinvestmentCategory,
    ReinvestmentProfile,
    build_little_utopia_qualification_register,
    get_reinvestment_profile,
)
from app.calculators.levers import Lever, derive_levers

JURISDICTION_GRAPH_VERSION = "1.0.0"

# Sentinel used wherever a fact has no known value yet. Distinct from
# None-as-a-field-default so callers can tell "this field was never set"
# (a bug) apart from "this field was explicitly recorded as unknown"
# (an honest data gap).
UNKNOWN = "UNKNOWN"


class FactStatus(str, enum.Enum):
    """
    Attached to every Requirement/Restriction/Absence node's attributes
    so a fact's state is queryable without string-matching a node id.

    KNOWN   — the source field exists and carries a real value.
    UNKNOWN — the source field exists but its value is None (an honest
              gap in an otherwise-modeled dimension).
    ABSENT  — no field for this fact category exists anywhere in the
              source data model (a dimension not modeled at all yet).
    """
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    ABSENT = "ABSENT"


# ── Node types ────────────────────────────────────────────────────────────

class NodeType(str, enum.Enum):
    COUNTRY = "country"
    NATIONAL_PROGRAM = "national_program"
    REGIONAL_PROGRAM = "regional_program"
    MUNICIPAL_PROGRAM = "municipal_program"
    TREATY = "treaty"
    FUND = "fund"
    AGENCY = "agency"
    REQUIREMENT = "requirement"
    RESTRICTION = "restriction"
    ABSENCE = "absence"


class RelationshipType(str, enum.Enum):
    CONTAINS = "contains"
    ADMINISTERED_BY = "administered_by"
    FUNDED_BY = "funded_by"
    PARTY_TO = "party_to"
    STACKS_WITH = "stacks_with"
    RESTRICTED_BY = "restricted_by"
    REQUIRES = "requires"
    HAS_REINVESTMENT_PROFILE = "has_reinvestment_profile"
    COMPARABLE_TO = "comparable_to"
    HAS_AVAILABLE_LEVER = "has_available_lever"


@dataclass
class EvidenceRef:
    """
    A pointer into the Evidence Graph (evidence_graph.py). Optional and
    unpopulated for every relationship created in this phase — Phase 5A is
    wiring, not evidence-binding — but every assertive legal relationship
    below is capable of carrying one, per requirement #4.
    """
    graph_rule_id: Optional[str] = None
    graph_absence_id: Optional[str] = None
    citation: Optional[str] = None


@dataclass
class GraphNode:
    node_id: str
    node_type: NodeType
    name: str
    attributes: dict = field(default_factory=dict)
    # Node-level evidence hook (in addition to relationship-level
    # EvidenceRef): a Requirement/Restriction/Absence fact can be cited
    # independently of any one edge pointing at it. Unpopulated by
    # default — Phase 5B is wiring/modeling, not evidence-binding.
    evidence: EvidenceRef = field(default_factory=EvidenceRef)


@dataclass
class Relationship:
    source_id: str
    relationship_type: RelationshipType
    target_id: str
    evidence: EvidenceRef = field(default_factory=EvidenceRef)
    attributes: dict = field(default_factory=dict)


# ── Graph container ──────────────────────────────────────────────────────

class JurisdictionGraph:
    """
    A plain in-memory node/relationship store. No persistence, no query
    language — this phase only wires data into a graph-compatible shape.
    Deterministic: iterating self.nodes / self.relationships always
    reflects insertion order, and build_jurisdiction_graph() inserts in a
    fixed order derived from the sorted keys of its source dicts.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._relationships: list[Relationship] = []

    def add_node(self, node: GraphNode) -> None:
        if node.node_id in self._nodes:
            raise ValueError(f"Node '{node.node_id}' already exists.")
        self._nodes[node.node_id] = node

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def add_relationship(self, relationship: Relationship) -> None:
        if relationship.source_id not in self._nodes:
            raise ValueError(f"Relationship source '{relationship.source_id}' is not a known node.")
        if relationship.target_id not in self._nodes:
            raise ValueError(f"Relationship target '{relationship.target_id}' is not a known node.")
        self._relationships.append(relationship)

    @property
    def nodes(self) -> list[GraphNode]:
        return list(self._nodes.values())

    @property
    def relationships(self) -> list[Relationship]:
        return list(self._relationships)

    def nodes_of_type(self, node_type: NodeType) -> list[GraphNode]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def relationships_of_type(self, relationship_type: RelationshipType) -> list[Relationship]:
        return [r for r in self._relationships if r.relationship_type == relationship_type]

    def relationships_from(self, node_id: str) -> list[Relationship]:
        return [r for r in self._relationships if r.source_id == node_id]

    def relationships_to(self, node_id: str) -> list[Relationship]:
        return [r for r in self._relationships if r.target_id == node_id]


# ── Node ID helpers (deterministic, no per-jurisdiction branching) ─────────

def _country_id(code: str) -> str:
    return f"country:{code}"


def _program_id(program_slug: str) -> str:
    return f"program:{program_slug}"


def _agency_id(agency_name: str) -> str:
    return f"agency:{agency_name}"


def _treaty_id(treaty_slug: str) -> str:
    return f"treaty:{treaty_slug}"


def _requirement_id(program_slug: str, key: str) -> str:
    return f"requirement:{program_slug}:{key}"


def _restriction_id(program_slug: str, key: str) -> str:
    return f"restriction:{program_slug}:{key}"


def _absence_id(program_slug: str, key: str) -> str:
    return f"absence:{program_slug}:{key}"


def _reinvestment_id(country_code: str) -> str:
    return f"reinvestment:{country_code}"


def _lever_id_node(lever_id: str) -> str:
    return f"lever:{lever_id}"


def _fund_id(fund_slug: str) -> str:
    return f"fund:{fund_slug}"


# Fact categories requirement #1's minimum list asks for that have no
# corresponding field on JurisdictionIncentiveProfile at all — every
# instance of these is FactStatus.ABSENT for every jurisdiction, since
# the source data model simply doesn't carry the dimension yet.
_ABSENT_FACT_SPECS: list[tuple[str, RelationshipType, str]] = [
    ("eligible_production_types", RelationshipType.REQUIRES, "eligible production types"),
    ("territorial_nexus", RelationshipType.REQUIRES, "territorial nexus"),
    ("local_entity_requirement", RelationshipType.REQUIRES, "local entity requirement"),
    ("stacking_rule", RelationshipType.RESTRICTED_BY, "stacking rule"),
    ("application_timing_deadline", RelationshipType.REQUIRES, "application timing / deadline"),
]


def _add_fact(
    graph: JurisdictionGraph,
    program_id: str,
    jurisdiction_name: str,
    program_slug: str,
    key: str,
    relationship_type: RelationshipType,
    node_type: NodeType,
    name_suffix: str,
    status: FactStatus,
    value,
    reason: Optional[str] = None,
) -> None:
    """
    Shared constructor for one Requirement/Restriction/Absence fact node
    plus its edge back to the owning program. One code path for every
    fact category and every jurisdiction — no per-jurisdiction or
    per-fact-category special casing beyond the (key, relationship_type,
    node_type) triple each caller supplies.
    """
    node_id = {
        NodeType.REQUIREMENT: _requirement_id,
        NodeType.RESTRICTION: _restriction_id,
        NodeType.ABSENCE: _absence_id,
    }[node_type](program_slug, key)
    attributes = {"kind": key, "value": value, "status": status.value}
    if reason is not None:
        attributes["reason"] = reason
    graph.add_node(GraphNode(
        node_id=node_id,
        node_type=node_type,
        name=f"{jurisdiction_name} {name_suffix}",
        attributes=attributes,
    ))
    graph.add_relationship(Relationship(
        source_id=program_id,
        relationship_type=relationship_type,
        target_id=node_id,
    ))


# ── Wiring: Countries + Programs (from jurisdiction_comparison.py) ─────────

def _add_country_and_program(graph: JurisdictionGraph, profile: "jc.JurisdictionIncentiveProfile") -> None:
    """
    Every profile in ALL_PROFILES becomes one Country node and one
    NationalProgram node, plus an ADMINISTERED_BY edge to an Agency node
    derived from profile.authority_name. This is fully generic — no
    per-jurisdiction-code branch — so it applies identically to Mauritius,
    Malta, Greece, Cyprus, and every secondary-reference jurisdiction
    already modeled in jurisdiction_comparison.py.

    RegionalProgram and MunicipalProgram are the two node types this pass
    scopes narrowly: jurisdiction_comparison.py models one primary program
    per country, not sub-national programs. No RegionalProgram or
    MunicipalProgram node is fabricated here — that data does not exist
    in the repo yet, so it is left absent rather than invented, satisfying
    "do not invent missing facts."
    """
    country_id = _country_id(profile.jurisdiction_code)
    if not graph.has_node(country_id):
        graph.add_node(GraphNode(
            node_id=country_id,
            node_type=NodeType.COUNTRY,
            name=profile.jurisdiction_name,
            attributes={"jurisdiction_code": profile.jurisdiction_code},
        ))

    program_id = _program_id(profile.program_slug)
    graph.add_node(GraphNode(
        node_id=program_id,
        node_type=NodeType.NATIONAL_PROGRAM,
        name=profile.program_name,
        attributes={
            "program_slug": profile.program_slug,
            "jurisdiction_code": profile.jurisdiction_code,
            "incentive_type": profile.incentive_type,
            "base_rate": profile.base_rate,
            "max_rate": profile.max_rate,
            "confidence_tier": profile.confidence_tier,
            "data_gaps": list(profile.data_gaps),
        },
    ))
    graph.add_relationship(Relationship(
        source_id=country_id,
        relationship_type=RelationshipType.CONTAINS,
        target_id=program_id,
    ))

    agency_id = _agency_id(profile.authority_name)
    if not graph.has_node(agency_id):
        graph.add_node(GraphNode(
            node_id=agency_id,
            node_type=NodeType.AGENCY,
            name=profile.authority_name,
            attributes={"authority_url_hint": profile.authority_url_hint},
        ))
    graph.add_relationship(Relationship(
        source_id=program_id,
        relationship_type=RelationshipType.ADMINISTERED_BY,
        target_id=agency_id,
        evidence=EvidenceRef(),  # capable of carrying a citation; not populated this phase
    ))

    # Requirement / Restriction / Absence nodes, generically derived from
    # the profile's own fields — not hand-written per jurisdiction. A
    # value present on the profile becomes a KNOWN fact node; an
    # Optional[...] field that is None becomes an UNKNOWN fact node
    # (field exists, value doesn't); a fact category with no
    # corresponding field anywhere on JurisdictionIncentiveProfile
    # becomes an ABSENT fact node (dimension not modeled at all). See
    # requirement #3/#5 and FactStatus's docstring.
    _add_fact(
        graph, program_id, profile.jurisdiction_name, profile.program_slug,
        key="cultural_test", relationship_type=RelationshipType.REQUIRES,
        node_type=NodeType.REQUIREMENT, name_suffix="cultural test",
        status=FactStatus.KNOWN, value=profile.requires_cultural_test,
    )
    _add_fact(
        graph, program_id, profile.jurisdiction_name, profile.program_slug,
        key="min_spend", relationship_type=RelationshipType.REQUIRES,
        node_type=NodeType.REQUIREMENT, name_suffix="minimum spend",
        status=FactStatus.KNOWN if profile.min_spend_local is not None else FactStatus.UNKNOWN,
        value=profile.min_spend_local if profile.min_spend_local is not None else UNKNOWN,
    )
    _add_fact(
        graph, program_id, profile.jurisdiction_name, profile.program_slug,
        key="cap_funding_window", relationship_type=RelationshipType.RESTRICTED_BY,
        node_type=NodeType.RESTRICTION, name_suffix="annual program cap / funding window",
        status=FactStatus.KNOWN if profile.annual_cap_local is not None else FactStatus.UNKNOWN,
        value=profile.annual_cap_local if profile.annual_cap_local is not None else UNKNOWN,
    )
    _add_fact(
        graph, program_id, profile.jurisdiction_name, profile.program_slug,
        key="payout_timing", relationship_type=RelationshipType.RESTRICTED_BY,
        node_type=NodeType.RESTRICTION, name_suffix="payout timing (cashflow weeks)",
        status=FactStatus.KNOWN if profile.cashflow_timing_weeks is not None else FactStatus.UNKNOWN,
        value=profile.cashflow_timing_weeks if profile.cashflow_timing_weeks is not None else UNKNOWN,
    )

    # is_transferable is explicitly Optional[bool] in the source profile
    # — when None, represent as an UNKNOWN restriction placeholder rather
    # than silently dropping the dimension. (Preserved from Phase 5A
    # exactly: only materialized when the value is unknown, using the
    # original node id, so existing callers/tests keyed on this id are
    # unaffected.)
    if profile.is_transferable is None:
        restr_id = _restriction_id(profile.program_slug, "transferability_unknown")
        graph.add_node(GraphNode(
            node_id=restr_id,
            node_type=NodeType.RESTRICTION,
            name=f"{profile.jurisdiction_name} rebate transferability",
            attributes={"kind": "is_transferable", "value": UNKNOWN, "status": FactStatus.UNKNOWN.value},
        ))
        graph.add_relationship(Relationship(
            source_id=program_id,
            relationship_type=RelationshipType.RESTRICTED_BY,
            target_id=restr_id,
        ))

    # Fact categories with no corresponding field anywhere on
    # JurisdictionIncentiveProfile — every one of these is genuinely
    # ABSENT from the source data model for every jurisdiction, so this
    # loop applies identically to all of them, not just Mauritius. This
    # is the explicit-Absence half of requirement #1 ("no invented
    # facts"): rather than fabricate a value or omit the dimension, the
    # graph states plainly that the source data has no field for it yet.
    for key, relationship_type, name_suffix in _ABSENT_FACT_SPECS:
        _add_fact(
            graph, program_id, profile.jurisdiction_name, profile.program_slug,
            key=key, relationship_type=relationship_type, node_type=NodeType.ABSENCE,
            name_suffix=name_suffix, status=FactStatus.ABSENT,
            value=UNKNOWN, reason="Not modeled anywhere on JurisdictionIncentiveProfile.",
        )


# ── Wiring: Treaties (from treaty_engine.py) ────────────────────────────────

def _add_treaties(graph: JurisdictionGraph) -> None:
    """
    Wraps te._BILATERAL and te._MULTILATERAL via the module's own public
    getters/registries, generically. No treaty involving Mauritius exists
    in treaty_engine.py today — that absence is left as absence (no
    Treaty/PARTY_TO edge is fabricated for MU), which is itself
    representable and checkable by a test, satisfying "do not invent
    missing facts."
    """
    seen_bilateral: set[str] = set()
    for pair, treaty in te._BILATERAL.items():
        if treaty.treaty_slug in seen_bilateral:
            continue
        seen_bilateral.add(treaty.treaty_slug)
        treaty_id = _treaty_id(treaty.treaty_slug)
        graph.add_node(GraphNode(
            node_id=treaty_id,
            node_type=NodeType.TREATY,
            name=treaty.treaty_slug,
            attributes={
                "treaty_type": treaty.treaty_type,
                "confidence_tier": treaty.confidence_tier,
                "majority_min_pct": treaty.majority_min_pct,
                "minority_min_pct": treaty.minority_min_pct,
                "minority_max_pct": treaty.minority_max_pct,
                "cultural_test_required": treaty.cultural_test_required,
            },
        ))
        for code in sorted(pair):
            country_id = _country_id(code)
            if not graph.has_node(country_id):
                graph.add_node(GraphNode(
                    node_id=country_id,
                    node_type=NodeType.COUNTRY,
                    name=code,
                    attributes={"jurisdiction_code": code},
                ))
            graph.add_relationship(Relationship(
                source_id=country_id,
                relationship_type=RelationshipType.PARTY_TO,
                target_id=treaty_id,
            ))

    for slug, treaty in te._MULTILATERAL.items():
        treaty_id = _treaty_id(slug)
        graph.add_node(GraphNode(
            node_id=treaty_id,
            node_type=NodeType.TREATY,
            name=slug,
            attributes={
                "treaty_type": treaty.treaty_type,
                "confidence_tier": treaty.confidence_tier,
                "cultural_test_required": treaty.cultural_test_required,
                "fund_unlocks": list(treaty.fund_unlocks),
            },
        ))
        for fund_slug in treaty.fund_unlocks:
            fund_id = _fund_id(fund_slug)
            if not graph.has_node(fund_id):
                graph.add_node(GraphNode(
                    node_id=fund_id,
                    node_type=NodeType.FUND,
                    name=fund_slug,
                    attributes={},
                ))
            graph.add_relationship(Relationship(
                source_id=treaty_id,
                relationship_type=RelationshipType.FUNDED_BY,
                target_id=fund_id,
            ))


def _treaty_availability_id(program_slug: str) -> str:
    return f"treaty_availability:{program_slug}"


def _add_treaty_availability_facts(graph: JurisdictionGraph) -> None:
    """
    One treaty-availability fact node per NationalProgram, attached via
    REQUIRES. This must run after _add_treaties() so every country's
    PARTY_TO edges already exist.

    Requirement #5: "treaty absence remains distinct from no treaty data
    loaded." A program whose country has zero PARTY_TO edges gets a node
    with status=ABSENT and attributes["checked"]=True — treaty_engine's
    registries were consulted and genuinely contain nothing for this
    jurisdiction, which is not the same claim as "we never loaded treaty
    data for this jurisdiction" (attributes["checked"]=False), a state
    this builder never actually produces since te._BILATERAL/_MULTILATERAL
    are always imported and consulted for every program — but the
    checked/status fields make the two states distinguishable wherever a
    caller constructs or inspects a node, which is what requirement #5
    asks for.
    """
    for program_node in sorted(graph.nodes_of_type(NodeType.NATIONAL_PROGRAM), key=lambda n: n.node_id):
        code = program_node.attributes.get("jurisdiction_code")
        program_slug = program_node.attributes.get("program_slug")
        if not code or not program_slug:
            continue
        country_id = _country_id(code)
        treaty_slugs = sorted(
            r.target_id.split("treaty:", 1)[1]
            for r in graph.relationships_of_type(RelationshipType.PARTY_TO)
            if r.source_id == country_id
        )
        fact_id = _treaty_availability_id(program_slug)
        if treaty_slugs:
            node_type, status, value = NodeType.REQUIREMENT, FactStatus.KNOWN, treaty_slugs
        else:
            node_type, status, value = NodeType.ABSENCE, FactStatus.ABSENT, []
        graph.add_node(GraphNode(
            node_id=fact_id,
            node_type=node_type,
            name=f"{code} treaty availability",
            attributes={
                "kind": "treaty_availability",
                "value": value,
                "status": status.value,
                "checked": True,
                "treaty_slugs": treaty_slugs,
            },
        ))
        graph.add_relationship(Relationship(
            source_id=program_node.node_id,
            relationship_type=RelationshipType.REQUIRES,
            target_id=fact_id,
        ))


# ── Wiring: Reinvestment profiles (from qualification_model.py) ────────────

def _add_reinvestment_profiles(graph: JurisdictionGraph) -> None:
    """
    One HAS_REINVESTMENT_PROFILE edge per country present in
    REINVESTMENT_REGISTRY, plus one for every country already inserted
    into the graph by _add_country_and_program that has NO registry entry
    — represented via get_reinvestment_profile()'s own UNKNOWN fallback,
    so "we have not looked" is explicit and distinct from
    ReinvestmentCategory.NOT_PERMITTED everywhere in the graph, per
    requirement #6.
    """
    country_nodes = graph.nodes_of_type(NodeType.COUNTRY)
    for country_node in sorted(country_nodes, key=lambda n: n.node_id):
        code = country_node.attributes.get("jurisdiction_code")
        if not code:
            continue
        profile = get_reinvestment_profile(code)
        reinvest_id = _reinvestment_id(code)
        is_unknown = profile.category == ReinvestmentCategory.UNKNOWN
        graph.add_node(GraphNode(
            node_id=reinvest_id,
            node_type=NodeType.RESTRICTION,
            name=f"{country_node.name} reinvestment profile",
            attributes={
                "kind": "reinvestment_treatment",
                "category": profile.category.value,
                "value": profile.category.value,
                "evidence": profile.evidence,
                "notes": profile.notes,
                "is_explicit_unknown": is_unknown,
                # UNKNOWN ("we have not looked") is a distinct status from
                # NOT_PERMITTED ("we looked and it's disallowed") for
                # every one of the seven ReinvestmentCategory values —
                # only ReinvestmentCategory.UNKNOWN maps to
                # FactStatus.UNKNOWN; every other category (including
                # NOT_PERMITTED) is a KNOWN determination, per
                # requirement #4.
                "status": FactStatus.UNKNOWN.value if is_unknown else FactStatus.KNOWN.value,
            },
            evidence=EvidenceRef(citation=profile.evidence),
        ))
        graph.add_relationship(Relationship(
            source_id=country_node.node_id,
            relationship_type=RelationshipType.HAS_REINVESTMENT_PROFILE,
            target_id=reinvest_id,
            evidence=EvidenceRef(citation=profile.evidence),
        ))


# ── Wiring: Comparable jurisdictions (from jurisdiction_comparison Tier 1) ──

def _add_comparable_links(graph: JurisdictionGraph) -> None:
    """
    Tier 1 (MU, MT, GR, CY) are the existing, already-modeled comparison
    set in jurisdiction_comparison.py — this wires them as pairwise
    COMPARABLE_TO edges rather than re-deriving a new comparison set.
    Generic double loop, no per-country branch.
    """
    tier1_codes = sorted(jc.TIER1_PROFILES.keys())
    for i, code_a in enumerate(tier1_codes):
        for code_b in tier1_codes[i + 1:]:
            a_id, b_id = _country_id(code_a), _country_id(code_b)
            if not (graph.has_node(a_id) and graph.has_node(b_id)):
                continue
            graph.add_relationship(Relationship(
                source_id=a_id,
                relationship_type=RelationshipType.COMPARABLE_TO,
                target_id=b_id,
                attributes={"comparison_tier": "TIER1", "source": "jurisdiction_comparison.TIER1_PROFILES"},
            ))


# ── Wiring: Available levers (from levers.py, Little Utopia only) ──────────

def _add_available_levers(
    graph: JurisdictionGraph,
    mu_rate: float = 0.40,
    register: Optional[list] = None,
) -> None:
    """
    HAS_AVAILABLE_LEVER edges from Mauritius's NationalProgram node to the
    Lever objects derived from Little Utopia's structuring-path register —
    the only populated qualification register in the codebase today. This
    does not run derive_levers() for any other jurisdiction (none has a
    qualification register to derive from), so no fact is invented for
    Malta/Greece/Cyprus/etc — their absence of Lever nodes is the honest
    state, not an oversight.

    register, when supplied by the caller (Engine Integration Phase 1),
    is the caller's CURRENT derived register — so a facts-changed
    register produces facts-changed lever nodes instead of the default
    build. Omitted, behavior is byte-identical to before.
    """
    mu_program_id = _program_id(jc.TIER1_PROFILES["MU"].program_slug)
    if not graph.has_node(mu_program_id):
        return
    if register is None:
        register = build_little_utopia_qualification_register(mu_rate=mu_rate)
    levers: list[Lever] = derive_levers(register, rate=mu_rate, jurisdiction_code="MU")
    for lever in levers:
        lever_node_id = _lever_id_node(lever.lever_id)
        graph.add_node(GraphNode(
            node_id=lever_node_id,
            # No dedicated "Lever" node type is in this phase's scope
            # (the required node set is Country/Program/Treaty/Fund/
            # Agency/Requirement/Restriction/JurisdictionGraph) — a Lever
            # is represented as a fact node of type RESTRICTION-adjacent
            # opportunity data, distinguishable by its lever_type
            # attribute, not by a new node kind.
            node_type=NodeType.RESTRICTION,
            name=lever.description,
            attributes={
                "lever_type": lever.lever_type.value,
                "affected_accounts": list(lever.affected_accounts),
                "upside_incentive_usd": lever.upside_incentive_usd,
                "confidence": lever.confidence.value,
                "status": lever.status.value,
            },
        ))
        graph.add_relationship(Relationship(
            source_id=mu_program_id,
            relationship_type=RelationshipType.HAS_AVAILABLE_LEVER,
            target_id=lever_node_id,
            evidence=EvidenceRef(),
        ))


# ── Top-level builder ────────────────────────────────────────────────────

def build_jurisdiction_graph(
    mu_rate: float = 0.40,
    register: Optional[list] = None,
) -> JurisdictionGraph:
    """
    Deterministic, generic construction: iterates ALL_PROFILES in a fixed
    (sorted-by-key) order, then wires treaties, reinvestment profiles,
    Tier 1 comparable links, and Little Utopia's available levers. Calling
    this twice with the same mu_rate produces graphs with identical node
    and relationship content in identical order — verified by a
    determinism test.

    register (optional, Engine Integration Phase 1): the caller's current
    derived qualification register, threaded to the lever pass so
    facts-dependent lever nodes track the caller's facts. Default None
    preserves prior behavior exactly.
    """
    graph = JurisdictionGraph()
    for code in sorted(jc.ALL_PROFILES.keys()):
        _add_country_and_program(graph, jc.ALL_PROFILES[code])
    _add_treaties(graph)
    _add_treaty_availability_facts(graph)
    _add_reinvestment_profiles(graph)
    _add_comparable_links(graph)
    _add_available_levers(graph, mu_rate=mu_rate, register=register)
    return graph


# ── Query helpers (Phase 5B) ────────────────────────────────────────────

def get_program_requirements(graph: JurisdictionGraph, program_id: str) -> list[GraphNode]:
    """
    Every node reached from program_id via REQUIRES — Requirement facts
    (known or unknown) and Absence facts wired with REQUIRES semantics
    (e.g. eligible_production_types, territorial_nexus,
    local_entity_requirement, application_timing_deadline,
    treaty_availability, cultural_test, min_spend).
    """
    return [
        graph.get_node(r.target_id)
        for r in graph.relationships_of_type(RelationshipType.REQUIRES)
        if r.source_id == program_id
    ]


def get_program_restrictions(graph: JurisdictionGraph, program_id: str) -> list[GraphNode]:
    """
    Every node reached from program_id via RESTRICTED_BY — Restriction
    facts (known or unknown) and Absence facts wired with
    RESTRICTED_BY semantics (e.g. cap_funding_window, payout_timing,
    transferability, stacking_rule).
    """
    return [
        graph.get_node(r.target_id)
        for r in graph.relationships_of_type(RelationshipType.RESTRICTED_BY)
        if r.source_id == program_id
    ]


def get_program_reinvestment(graph: JurisdictionGraph, program_id: str) -> Optional[GraphNode]:
    """The country-level reinvestment fact node for a program's jurisdiction."""
    program_node = graph.get_node(program_id)
    if program_node is None:
        return None
    code = program_node.attributes.get("jurisdiction_code")
    if not code:
        return None
    return graph.get_node(_reinvestment_id(code))


def get_program_unknowns(graph: JurisdictionGraph, program_id: str) -> list[GraphNode]:
    """
    Every fact attached to this program (requirements, restrictions, and
    its country's reinvestment treatment) whose FactStatus is UNKNOWN or
    ABSENT — the queryable "what remains unknown for this program" view
    requirement #3 asks for.
    """
    facts = get_program_requirements(graph, program_id) + get_program_restrictions(graph, program_id)
    reinvestment = get_program_reinvestment(graph, program_id)
    if reinvestment is not None:
        facts.append(reinvestment)
    return [f for f in facts if f is not None and f.attributes.get("status") in (
        FactStatus.UNKNOWN.value, FactStatus.ABSENT.value,
    )]


def get_program_known_facts(graph: JurisdictionGraph, program_id: str) -> list[GraphNode]:
    """The complement of get_program_unknowns(): every KNOWN fact attached to this program."""
    facts = get_program_requirements(graph, program_id) + get_program_restrictions(graph, program_id)
    reinvestment = get_program_reinvestment(graph, program_id)
    if reinvestment is not None:
        facts.append(reinvestment)
    return [f for f in facts if f is not None and f.attributes.get("status") == FactStatus.KNOWN.value]
