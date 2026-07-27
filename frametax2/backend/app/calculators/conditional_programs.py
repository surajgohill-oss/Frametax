"""
conditional_programs.py

Optimizer-integration phase: the KNOWN BUT NON-PRICEABLE layer of the
completed worldwide inventory (discretionary grants, development funds,
co-production funds, broadcaster funds, regional funds) exposed as
CONDITIONAL OPPORTUNITY NODES rather than ignored catalog records.

What this module does:

- Reads global_inventory.ALL_PROGRAMS (the 303-record worldwide master
  list) and selects exactly the program types that were classified
  KNOWN BUT NON-PRICEABLE in the database-completion phase:
  direct_grant / development_fund / co_production_fund /
  broadcaster_fund / regional_fund. These are real, monetary programs
  whose award basis is discretionary/editorial/competitive — they can
  never produce an automatic dollar calculation, but they are genuine
  optimizer inputs: a structure whose participants include Germany
  should surface Medienboard/MOIN/FFF-Bayern as conditional funding
  avenues; one including a broadcaster market should surface the
  broadcaster co-production funds.

- Maps each node to the country whose participation in a production
  structure makes it relevant (subnational "DE-BY" -> "DE"; national
  codes map to themselves; supranational groupings — EU, NORDIC,
  IBERO, ACP — are carried with scope="supranational" and are attached
  to a structure ONLY where a modeled membership registry proves a
  participant's membership (Eurimages via treaty_engine.is_eurimages_
  member, Ibermedia via is_ibermedia_member); all other supranational
  nodes remain in the index, explicitly NOT attached, because no
  modeled registry can prove membership — never guessed).

What this module never does:

- It never invents a dollar value. documented_cap_usd is carried only
  when the catalog record itself states one; expected value is NEVER
  computed (a discretionary award has no defensible expectation
  without an application outcome).
- It never asserts stackability: every node carries
  stacking="unknown_requires_evidence" — whether a discretionary grant
  stacks with a statutory incentive is a per-program legal fact no
  record here evidences.
- It never enters Net Production Cost: conditional nodes annotate
  structures and inform scenario comparison; ranking remains on
  defensible NPC only.

Deterministic throughout: fixed iteration over the catalog's own
order, stable node ids, no wall-clock, no randomness.

production_support-type records are EXCLUDED by design: the
reconciliation classified them NO ACTIVE APPLICABLE PROGRAM
(facilitation/permits only, no monetary mechanism) — there is nothing
conditional to pursue.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

CONDITIONAL_PROGRAMS_VERSION = "1.0.0"

# The exact KNOWN BUT NON-PRICEABLE program types from the worldwide
# reconciliation (see CAPABILITY_LEDGER.md, Batch 10). production_support
# is deliberately absent (classified NO ACTIVE APPLICABLE PROGRAM).
CONDITIONAL_PROGRAM_TYPES: frozenset[str] = frozenset({
    "direct_grant",
    "development_fund",
    "co_production_fund",
    "broadcaster_fund",
    "regional_fund",
})

# Supranational groupings present in the catalog — not countries, so a
# plain participant-code match can never attach them.
_SUPRANATIONAL_CODES: frozenset[str] = frozenset({"EU", "NORDIC", "IBERO", "ACP"})

# How each program type's award is decided — a categorical fact of the
# mechanism itself (what makes it non-priceable), not a per-program claim.
_SELECTION_BASIS: dict[str, str] = {
    "direct_grant": "competitive_discretionary",
    "development_fund": "competitive_discretionary",
    "co_production_fund": "competitive_discretionary",
    "broadcaster_fund": "editorial_broadcaster_selection",
    "regional_fund": "competitive_discretionary",
}


@dataclass(frozen=True)
class ConditionalProgramNode:
    """One non-priceable program as a conditional opportunity node.
    Everything here traces to the catalog record it came from; nothing
    is computed beyond the code->country scope mapping."""
    node_id: str
    jurisdiction_code: str            # the catalog's own code (may be subnational/supranational)
    parent_country: Optional[str]     # ISO country a structure participant matches on (None = supranational)
    scope: str                        # "national" | "subnational" | "supranational"
    jurisdiction_name: str
    program_name: str
    program_type: str
    selection_basis: str
    documented_cap_usd: Optional[float]   # only when the catalog record states one — never estimated
    notes: str
    source_title: Optional[str]
    source_url: Optional[str]
    stacking: str = "unknown_requires_evidence"
    attachment_basis: Optional[str] = None  # set at attach time (why this node attached to a structure)


@dataclass
class ConditionalProgramIndex:
    version: str
    nodes: list[ConditionalProgramNode]
    by_parent_country: dict[str, list[ConditionalProgramNode]] = field(default_factory=dict)
    supranational: list[ConditionalProgramNode] = field(default_factory=list)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _parent_country(code: str) -> tuple[Optional[str], str]:
    """(parent_country, scope) for a catalog jurisdiction code. A
    hyphenated code's prefix is its country (DE-BY -> DE) — the catalog's
    own convention throughout. Supranational codes have no parent."""
    if code in _SUPRANATIONAL_CODES:
        return None, "supranational"
    if "-" in code:
        return code.split("-", 1)[0], "subnational"
    return code, "national"


def build_conditional_program_index() -> ConditionalProgramIndex:
    """The full conditional-opportunity layer of the worldwide inventory,
    derived from global_inventory.ALL_PROGRAMS — read-only, deterministic,
    one node per KNOWN-BUT-NON-PRICEABLE catalog record."""
    from app.data import global_inventory as gi

    nodes: list[ConditionalProgramNode] = []
    for entry in gi.ALL_PROGRAMS:
        if entry.program_type not in CONDITIONAL_PROGRAM_TYPES:
            continue
        parent, scope = _parent_country(entry.jurisdiction_code)
        nodes.append(ConditionalProgramNode(
            node_id=f"COND-{entry.jurisdiction_code}-{_slugify(entry.program_name)}",
            jurisdiction_code=entry.jurisdiction_code,
            parent_country=parent,
            scope=scope,
            jurisdiction_name=entry.jurisdiction_name,
            program_name=entry.program_name,
            program_type=entry.program_type,
            selection_basis=_SELECTION_BASIS[entry.program_type],
            documented_cap_usd=entry.annual_cap_usd,
            notes=entry.notes,
            source_title=entry.source_title or None,
            source_url=entry.source_url,
        ))

    by_parent: dict[str, list[ConditionalProgramNode]] = {}
    supranational: list[ConditionalProgramNode] = []
    for node in nodes:
        if node.parent_country is None:
            supranational.append(node)
        else:
            by_parent.setdefault(node.parent_country, []).append(node)

    return ConditionalProgramIndex(
        version=CONDITIONAL_PROGRAMS_VERSION,
        nodes=nodes,
        by_parent_country=by_parent,
        supranational=supranational,
    )


# Module-level cache: the catalog is immutable at runtime, so the index
# is built once. (Same pattern as the other registry-derived caches.)
_INDEX: Optional[ConditionalProgramIndex] = None


def get_conditional_program_index() -> ConditionalProgramIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = build_conditional_program_index()
    return _INDEX


def _attached(node: ConditionalProgramNode, basis: str) -> ConditionalProgramNode:
    """A copy of the node carrying the reason it attached to this
    structure — provenance for the serving layer."""
    return ConditionalProgramNode(
        node_id=node.node_id,
        jurisdiction_code=node.jurisdiction_code,
        parent_country=node.parent_country,
        scope=node.scope,
        jurisdiction_name=node.jurisdiction_name,
        program_name=node.program_name,
        program_type=node.program_type,
        selection_basis=node.selection_basis,
        documented_cap_usd=node.documented_cap_usd,
        notes=node.notes,
        source_title=node.source_title,
        source_url=node.source_url,
        stacking=node.stacking,
        attachment_basis=basis,
    )


def conditional_nodes_for(participants: tuple[str, ...] | list[str]) -> list[ConditionalProgramNode]:
    """Every conditional node relevant to a structure with these
    participating jurisdictions:

    - national/subnational nodes whose parent country is a participant
      (a participant code like "CA-BC" also matches its own country's
      national nodes via its prefix);
    - Eurimages / Ibermedia supranational nodes ONLY when a modeled
      membership registry (treaty_engine) proves a participant's
      membership — all other supranational nodes are never attached
      (no modeled registry can prove membership; the full index still
      lists them).

    Deterministic: catalog order within each group, national before
    subnational, supranational last.
    """
    from app.calculators import treaty_engine as te

    index = get_conditional_program_index()

    participant_countries: list[str] = []
    for p in participants:
        code = p.upper()
        country = code.split("-", 1)[0] if "-" in code else code
        if country not in participant_countries:
            participant_countries.append(country)

    attached: list[ConditionalProgramNode] = []
    for country in participant_countries:
        for node in index.by_parent_country.get(country, []):
            basis = (
                f"Participant jurisdiction {country} is the node's country."
                if node.scope == "national"
                else f"Subnational program within participant jurisdiction {country}."
            )
            attached.append(_attached(node, basis))

    for node in index.supranational:
        checker = None
        if "eurimages" in node.program_name.lower():
            checker = te.is_eurimages_member
        elif "ibermedia" in node.program_name.lower():
            checker = te.is_ibermedia_member
        if checker is None:
            continue  # membership not provable from any modeled registry — never attached
        members = [c for c in participant_countries if checker(c)]
        if members:
            attached.append(_attached(
                node,
                f"Modeled membership registry (treaty_engine) confirms participant(s) "
                f"{members} as members.",
            ))

    return attached


def node_to_dict(node: ConditionalProgramNode) -> dict:
    """Serving-layer serialization — every field, no computation."""
    return {
        "node_id": node.node_id,
        "jurisdiction_code": node.jurisdiction_code,
        "parent_country": node.parent_country,
        "scope": node.scope,
        "jurisdiction_name": node.jurisdiction_name,
        "program_name": node.program_name,
        "program_type": node.program_type,
        "selection_basis": node.selection_basis,
        "documented_cap_usd": node.documented_cap_usd,
        "stacking": node.stacking,
        "attachment_basis": node.attachment_basis,
        "notes": node.notes,
        "source_title": node.source_title,
        "source_url": node.source_url,
        "status": "conditional_unpriced",
        "pricing_note": (
            "Discretionary/editorial award — no automatic dollar calculation is "
            "possible; never included in Net Production Cost. Documented cap, "
            "where present, is the program's own stated ceiling, not an "
            "expected value."
        ),
    }
