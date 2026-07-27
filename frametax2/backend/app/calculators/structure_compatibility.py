"""
structure_compatibility.py

Optimizer-integration phase: the COMPATIBILITY ENGINE that decides how a
candidate production structure's executable incentives and conditional
(KNOWN BUT NON-PRICEABLE) programs may combine.

This is the layer that turns conditional opportunity nodes from
informational metadata into scenario-generation inputs: for each
(structure, conditional program) pair it returns a verdict and the exact
gates that pair must clear, so a producer can see WHICH funding avenues a
structure genuinely opens and WHAT each one requires.

Every rule is grounded in a fact the system already holds:

- exclusivity: a program's own `mutually_exclusive_alternative_program`
  RateCondition (real statutory evidence in program_rate_rules);
- cultural-test gates: a program's own `cultural_test_required`
  RateCondition;
- co-production eligibility: treaty_engine's real bilateral/multilateral
  registries and each instrument's own min_coproducer_countries;
- stackability: the Jurisdiction Graph's real STACKS_WITH edges — absence
  is reported as UNKNOWN, never as permission and never as prohibition;
- program mechanism: the catalog's own program_type (a broadcaster fund
  requires a broadcaster; a development fund funds development, not
  production spend).

What this engine never does:

- It never assigns a dollar value to a conditional program. A verdict is
  about legal/structural combinability, not economics. Nothing here
  enters Net Production Cost.
- It never upgrades UNKNOWN to permitted. An unevidenced stacking
  relationship stays a disclosed gate.
- It never invents a requirement: every gate names the fact that
  produced it.

Deterministic: fixed iteration over sorted inputs, no wall-clock, no
randomness.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

STRUCTURE_COMPATIBILITY_VERSION = "1.0.0"


class CompatibilityVerdict(str, enum.Enum):
    # No known conflict with this structure; the award itself is still a
    # discretionary application outcome (that is the program's nature,
    # not a compatibility defect).
    PERMITTED_PENDING_APPLICATION = "permitted_pending_application"
    # Combinable only once one or more concrete, named preconditions are
    # met (co-production status, a broadcaster partner, a cultural test).
    GATED = "gated"
    # Real evidence bars combining this with the structure's statutory
    # incentive (a program's own mutual-exclusivity clause).
    PROHIBITED_BY_EVIDENCE = "prohibited_by_evidence"
    # The program funds a different phase/basis than this structure's
    # production spend — it may still be pursued, but it cannot offset
    # this structure's production cost.
    SCOPE_MISMATCH = "scope_mismatch"


@dataclass(frozen=True)
class CompatibilityGate:
    """One concrete precondition, naming the fact that produced it."""
    gate_id: str
    kind: str          # "coproduction" | "broadcaster" | "cultural_test" | "stacking" | "territorial" | "exclusivity"
    description: str
    basis: str         # the registry/condition/mechanism this gate was derived from
    satisfied: Optional[bool] = None  # True/False when the system can evaluate it; None = not evaluable here


@dataclass(frozen=True)
class ConditionalCompatibility:
    """The verdict for one conditional program against one structure."""
    conditional_node_id: str
    program_name: str
    program_type: str
    jurisdiction_code: str
    verdict: CompatibilityVerdict
    gates: tuple[CompatibilityGate, ...]
    rationale: str
    documented_cap_usd: Optional[float] = None
    enters_npc: bool = False  # always False — retained explicitly so the contract is visible


@dataclass
class StructureCompatibilityResult:
    """Every conditional program evaluated against one structure, plus the
    structure-level qualification gates its EXECUTABLE programs impose."""
    version: str
    structure_id: str
    participants: tuple[str, ...]
    conditional: list[ConditionalCompatibility]
    executable_gates: list[CompatibilityGate] = field(default_factory=list)
    exclusivity_findings: list[str] = field(default_factory=list)

    @property
    def pursuable(self) -> list[ConditionalCompatibility]:
        """Conditional avenues not barred by evidence and not scope-
        mismatched — i.e. the ones this structure genuinely opens."""
        return [
            c for c in self.conditional
            if c.verdict in (
                CompatibilityVerdict.PERMITTED_PENDING_APPLICATION,
                CompatibilityVerdict.GATED,
            )
        ]

    @property
    def counts_by_verdict(self) -> dict[str, int]:
        return {
            v.value: sum(1 for c in self.conditional if c.verdict == v)
            for v in CompatibilityVerdict
        }


# ── Fact readers (all read existing registries; none invent) ─────────────────

def _program_conditions(program_slug: str) -> list:
    """Every RateCondition attached to any tier of this program — the real
    statutory conditions already modeled in program_rate_rules."""
    from app.data.program_rate_rules import get_rate_rules

    conditions = []
    for rule in get_rate_rules(program_slug):
        conditions.extend(rule.conditions)
    return conditions


def _has_condition_kind(program_slug: str, kind: str) -> Optional[object]:
    for cond in _program_conditions(program_slug):
        if cond.kind == kind:
            return cond
    return None


def _coproduction_status(participants: tuple[str, ...]) -> tuple[bool, str]:
    """(is_official_coproduction_capable, basis). Reads the real treaty
    registries only — a single-participant structure is never a
    co-production, and a multi-participant one is only co-production
    capable where an instrument actually covers the pair."""
    from app.calculators import treaty_engine as te

    if len(participants) < 2:
        return False, "Single-participant structure — no co-production counterparty."
    ordered = tuple(sorted(participants))
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            treaty = te.get_bilateral_treaty(a, b)
            if treaty is not None:
                return True, f"treaty_engine bilateral treaty '{treaty.treaty_slug}' covers {a}+{b}."
            if te.is_european_convention_signatory(a) and te.is_european_convention_signatory(b):
                return True, (
                    f"Both {a} and {b} are European Convention signatories "
                    "(treaty_engine) — the Convention substitutes as the "
                    "co-production framework."
                )
    return False, (
        f"No bilateral treaty and no shared European Convention membership covers "
        f"{ordered} in treaty_engine — official co-production status is not available."
    )


def _stacking_is_evidenced(program_slug: str, conditional_node_id: str, graph) -> bool:
    """True only where the Jurisdiction Graph holds a real STACKS_WITH
    relationship connecting this structure's statutory program to THIS
    conditional program.

    The Jurisdiction Graph is built from the executable doctrine layer; it
    carries no nodes for catalog conditional programs, so no STACKS_WITH
    relationship can currently connect the two. That makes this correctly
    False today — which the caller reports as an UNKNOWN gate, never as
    prohibition and never as permission. The lookup is written against the
    graph's real API (relationships_of_type / node ids), so it starts
    returning True automatically the day such evidence is modeled, rather
    than silently swallowing an error.
    """
    if graph is None:
        return False
    from app.calculators.jurisdiction_graph import RelationshipType

    program_ref = f"program:{program_slug}"
    conditional_ref = f"conditional:{conditional_node_id}"
    for rel in graph.relationships_of_type(RelationshipType.STACKS_WITH):
        endpoints = {rel.source_id, rel.target_id}
        if program_ref in endpoints and conditional_ref in endpoints:
            return True
    return False


# ── The engine ───────────────────────────────────────────────────────────────

def evaluate_structure_compatibility(
    *,
    structure_id: str,
    participants: tuple[str, ...],
    executable_program_slugs: tuple[str, ...],
    conditional_nodes: list,
    graph=None,
) -> StructureCompatibilityResult:
    """
    Evaluate every conditional program against one candidate structure.

    executable_program_slugs are the structure's own statutory programs
    (one per incentive-claiming segment) — their real RateConditions
    supply the exclusivity and cultural-test gates.
    """
    from app.calculators.conditional_programs import ConditionalProgramNode  # noqa: F401 (typing clarity)

    is_coprod, coprod_basis = _coproduction_status(participants)

    # ── Structure-level gates from the EXECUTABLE programs' own conditions ──
    executable_gates: list[CompatibilityGate] = []
    exclusivity_findings: list[str] = []
    for slug in sorted(set(executable_program_slugs)):
        cultural = _has_condition_kind(slug, "cultural_test_required")
        if cultural is not None:
            executable_gates.append(CompatibilityGate(
                gate_id=f"GATE-CULTURAL-{slug}",
                kind="cultural_test",
                description=(
                    f"{slug} requires a cultural test to be passed before its "
                    "statutory incentive is available."
                ),
                basis=f"program_rate_rules[{slug}] RateCondition kind='cultural_test_required'",
                satisfied=None,
            ))
        exclusive = _has_condition_kind(slug, "mutually_exclusive_alternative_program")
        if exclusive is not None:
            exclusivity_findings.append(
                f"{slug}: {exclusive.description} (basis: {exclusive.quote})"
            )
            executable_gates.append(CompatibilityGate(
                gate_id=f"GATE-EXCLUSIVITY-{slug}",
                kind="exclusivity",
                description=(
                    f"{slug} carries a mutual-exclusivity clause — claiming an "
                    "alternative program in the same jurisdiction is barred by evidence."
                ),
                basis=f"program_rate_rules[{slug}] RateCondition kind='mutually_exclusive_alternative_program'",
                satisfied=None,
            ))

    exclusive_slugs = {
        slug for slug in set(executable_program_slugs)
        if _has_condition_kind(slug, "mutually_exclusive_alternative_program") is not None
    }

    # ── Per-conditional-program verdicts ──
    results: list[ConditionalCompatibility] = []
    for node in conditional_nodes:
        gates: list[CompatibilityGate] = []
        verdict = CompatibilityVerdict.PERMITTED_PENDING_APPLICATION
        rationale_parts: list[str] = []

        # Rule 1 — mechanism scope. A development fund funds DEVELOPMENT,
        # not the production spend this structure prices, so it can never
        # offset this structure's production cost.
        if node.program_type == "development_fund":
            verdict = CompatibilityVerdict.SCOPE_MISMATCH
            rationale_parts.append(
                "Development fund: finances development (script/packaging), not the "
                "production expenditure this structure prices — pursuable, but it "
                "cannot offset this structure's production cost."
            )

        # Rule 2 — co-production funds require official co-production status.
        elif node.program_type == "co_production_fund":
            gates.append(CompatibilityGate(
                gate_id=f"GATE-COPROD-{node.node_id}",
                kind="coproduction",
                description=(
                    "Co-production fund: requires official co-production status "
                    "between the participating jurisdictions."
                ),
                basis=coprod_basis,
                satisfied=is_coprod,
            ))
            if not is_coprod:
                verdict = CompatibilityVerdict.GATED
                rationale_parts.append(
                    "Co-production status is NOT available to this structure — "
                    "the fund cannot be accessed until an eligible co-production "
                    "counterparty and instrument exist."
                )
            else:
                verdict = CompatibilityVerdict.GATED
                rationale_parts.append(
                    "Co-production status IS structurally available; the fund "
                    "remains a competitive application."
                )

        # Rule 3 — broadcaster funds require a broadcaster relationship.
        elif node.program_type == "broadcaster_fund":
            verdict = CompatibilityVerdict.GATED
            gates.append(CompatibilityGate(
                gate_id=f"GATE-BROADCASTER-{node.node_id}",
                kind="broadcaster",
                description=(
                    "Broadcaster fund: requires a commissioning / pre-buy / "
                    "co-production relationship with the broadcaster itself."
                ),
                basis=(
                    "Program mechanism (catalog program_type='broadcaster_fund'); no "
                    "broadcaster relationship is evidenced for this production."
                ),
                satisfied=None,
            ))
            rationale_parts.append(
                "Editorial/broadcaster selection — not an entitlement and not "
                "reachable without a broadcaster partner."
            )

        # Rule 4 — regional/subnational programs require spend in the sub-territory.
        elif node.scope == "subnational" or node.program_type == "regional_fund":
            verdict = CompatibilityVerdict.GATED
            gates.append(CompatibilityGate(
                gate_id=f"GATE-TERRITORIAL-{node.node_id}",
                kind="territorial",
                description=(
                    f"Regional program: requires qualifying spend physically within "
                    f"{node.jurisdiction_code}, not merely within "
                    f"{node.parent_country}."
                ),
                basis=(
                    f"Catalog scope='{node.scope}', jurisdiction_code="
                    f"'{node.jurisdiction_code}' — sub-territory allocation is not "
                    "modeled by this structure's account allocation."
                ),
                satisfied=None,
            ))
            rationale_parts.append(
                "Sub-territory spend placement must be confirmed before this "
                "regional program is reachable."
            )

        else:
            rationale_parts.append(
                "No known structural conflict with this structure; the award "
                "remains a competitive/discretionary decision."
            )

        # Rule 5 — exclusivity against the structure's own statutory program.
        if exclusive_slugs and node.parent_country is not None:
            for slug in sorted(exclusive_slugs):
                gates.append(CompatibilityGate(
                    gate_id=f"GATE-EXCLUSIVITY-{node.node_id}-{slug}",
                    kind="exclusivity",
                    description=(
                        f"This structure claims {slug}, which carries a mutual-"
                        "exclusivity clause — combining it with another program in "
                        "the same jurisdiction requires confirming the clause's scope."
                    ),
                    basis=f"program_rate_rules[{slug}] mutually_exclusive_alternative_program",
                    satisfied=None,
                ))

        # Rule 6 — stackability with the structure's statutory incentive is
        # UNKNOWN unless real STACKS_WITH evidence exists. Never assumed.
        if verdict != CompatibilityVerdict.SCOPE_MISMATCH:
            evidenced = any(
                _stacking_is_evidenced(slug, node.node_id, graph)
                for slug in executable_program_slugs
            )
            if not evidenced:
                gates.append(CompatibilityGate(
                    gate_id=f"GATE-STACKING-{node.node_id}",
                    kind="stacking",
                    description=(
                        "Whether this program may be combined with the structure's "
                        "statutory incentive is NOT evidenced — confirm with the "
                        "awarding authority before assuming either way."
                    ),
                    basis=(
                        "No STACKS_WITH edge in the Jurisdiction Graph connects this "
                        "conditional program to the structure's statutory program; "
                        "absence of evidence is neither permission nor prohibition."
                    ),
                    satisfied=None,
                ))
                if verdict == CompatibilityVerdict.PERMITTED_PENDING_APPLICATION:
                    verdict = CompatibilityVerdict.GATED

        results.append(ConditionalCompatibility(
            conditional_node_id=node.node_id,
            program_name=node.program_name,
            program_type=node.program_type,
            jurisdiction_code=node.jurisdiction_code,
            verdict=verdict,
            gates=tuple(gates),
            rationale=" ".join(rationale_parts),
            documented_cap_usd=node.documented_cap_usd,
        ))

    return StructureCompatibilityResult(
        version=STRUCTURE_COMPATIBILITY_VERSION,
        structure_id=structure_id,
        participants=tuple(participants),
        conditional=results,
        executable_gates=executable_gates,
        exclusivity_findings=exclusivity_findings,
    )


def compatibility_to_dict(result: StructureCompatibilityResult) -> dict:
    """Serving-layer serialization — every field, no computation."""
    return {
        "version": result.version,
        "structure_id": result.structure_id,
        "participants": list(result.participants),
        "counts_by_verdict": result.counts_by_verdict,
        "pursuable_count": len(result.pursuable),
        "executable_gates": [
            {
                "gate_id": g.gate_id, "kind": g.kind, "description": g.description,
                "basis": g.basis, "satisfied": g.satisfied,
            }
            for g in result.executable_gates
        ],
        "exclusivity_findings": list(result.exclusivity_findings),
        "conditional": [
            {
                "conditional_node_id": c.conditional_node_id,
                "program_name": c.program_name,
                "program_type": c.program_type,
                "jurisdiction_code": c.jurisdiction_code,
                "verdict": c.verdict.value,
                "rationale": c.rationale,
                "documented_cap_usd": c.documented_cap_usd,
                "enters_npc": c.enters_npc,
                "gates": [
                    {
                        "gate_id": g.gate_id, "kind": g.kind,
                        "description": g.description, "basis": g.basis,
                        "satisfied": g.satisfied,
                    }
                    for g in c.gates
                ],
            }
            for c in result.conditional
        ],
        "note": (
            "Compatibility is a legal/structural verdict, never an economic one: "
            "no conditional program enters Net Production Cost. GATED means a named "
            "precondition must be cleared; PROHIBITED_BY_EVIDENCE means a real "
            "exclusivity clause bars the combination; SCOPE_MISMATCH means the "
            "program funds a different phase than this structure's production spend. "
            "Unevidenced stackability is reported as a gate — never as permission."
        ),
    }
