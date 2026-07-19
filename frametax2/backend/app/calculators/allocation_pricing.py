"""
allocation_pricing.py

Multi-register pricing over an account->jurisdiction allocation — the
canonical composer path's extension for structures that place spend in
more than one jurisdiction (production_allocation.py supplies the
partition; this module prices it).

For each jurisdiction segment it derives ONE PARTIAL qualification
register over ONLY that segment's allocated accounts, through the SAME
generic ladder every register already uses
(qualification_derivation.derive_qualification_register), against that
jurisdiction's own doctrine + statutory rate rules — then prices the
segment with the SAME kernel (optimization_engine.build_risk_cases).
No new qualification or rate math is introduced anywhere.

Combination:

    gross cash budget
      - sum of lawful segment incentives (verified/floor)
      + travel incremental adjustment (applied ONCE, structure level)
      + FX adjustment                (applied ONCE, structure level)
      + financing/implementation costs (explicit input; defaults 0 —
        never a silent 8%/39wk assumption)
      = complete structure NPC

Structural guarantees (tested):
  - full-budget register reuse is impossible: a segment register is
    built ONLY from that segment's allocated lines, so QPE/incentive
    can never be double-counted across segments;
  - travel and FX enter once, at structure level, never per segment;
  - stacking: exactly one incentive program per segment is priced;
    additional-program combinations are enumerated only through
    enumerate_segment_program_stacks() (which delegates to the existing
    generate_structure_scenarios engine) and only when real multi-
    program knowledge exists for that jurisdiction — never fabricated;
  - the off-budget in-kind post FMV is NEVER added to any segment here.
    It remains exclusively the Mauritius economics controls' selected
    treatment (mauritius_economics) — a non-Mauritius segment can never
    carry it, and even the Mauritius segment carries it only as a note.

A structure is FULLY PRICED only when: the allocation is complete and
conserving; every incentive-claiming segment has executable doctrine +
rate rules that actually resolve; treaty/ownership requirements (if the
structure claims treaty status) pass against the real treaty registry;
and no CONDITIONAL assignment remains unresolved. Otherwise it is
excluded from financial ranking with the exact blockers stated.

No LLM calls. Deterministic and testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculators import treaty_engine as te
from app.calculators.optimization_engine import RiskCase, build_risk_cases
from app.calculators.production_allocation import (
    AccountAllocation,
    AllocationResult,
    AssignmentKind,
    StructureSpec,
)
from app.calculators.qualification_derivation import (
    BudgetLine,
    ProductionFacts,
    derive_qualification_register,
)
from app.calculators.qualification_model import (
    MU_TERRITORIAL_TEXT,
    QualificationState,
    _ALTERNATIVE_TERRITORIAL_TEXT,
)
from app.data.program_rate_rules import get_rate_rules, resolve_program_rate
from app.data.program_slug_aliases import canonical_slug
from app.data.program_spend_rules import get_program_doctrine

ALLOCATION_PRICING_VERSION = "1.0.0"

# Territorial-nexus text per executable program — reused from the same
# sourced texts the register derivation already uses, never invented.
_TERRITORIAL_TEXT_BY_SLUG: dict[str, str] = {
    "mu_edb_incentive": MU_TERRITORIAL_TEXT,
    **_ALTERNATIVE_TERRITORIAL_TEXT,
}


# ── Result objects ───────────────────────────────────────────────────────────

@dataclass
class SegmentEconomics:
    jurisdiction_code: str
    program_slug: str | None            # None = non-incentive segment
    claims_incentive: bool
    allocated_usd: float
    account_codes: tuple[str, ...]
    executable: bool
    qpe_usd: float = 0.0
    excluded_usd: float = 0.0
    unresolved_usd: float = 0.0         # grey/structuring states within the segment
    rate_floor: float | None = None
    rate_ceiling: float | None = None
    is_band_ceiling: bool = False
    statutory_basis: str | None = None
    incentive_floor_usd: float = 0.0
    incentive_ceiling_usd: float = 0.0
    doctrine: str | None = None
    blockers: tuple[str, ...] = ()
    register_trace: tuple[dict, ...] = ()   # per-account state/reason for the UI
    notes: tuple[str, ...] = ()


@dataclass
class StructureRecommendation:
    """Cloud-recommendation-engine concepts (gated action, approval
    chain, reversibility, dependency group, deterministic identity)
    applied to an allocated structure — merged capability, not a merged
    branch; every dollar figure comes from this module's own pricing."""
    recommendation_id: str              # deterministic: REC-STRUCT-<structure_id>
    action: str
    gated: bool
    approval_chain: tuple[str, ...]     # ordered roles that must approve
    reversibility: str                  # "reversible_before_execution" | "hard_to_reverse"
    dependency_group: tuple[str, ...]   # requirement/blocker ids this action depends on
    explanation: dict = field(default_factory=dict)


@dataclass
class AllocatedStructurePricing:
    pricing_version: str
    structure_id: str
    structure_type: str
    label: str
    primary_jurisdiction: str
    participants: tuple[str, ...]
    allocation: AllocationResult
    segments: tuple[SegmentEconomics, ...]
    gross_budget_usd: float
    total_incentive_floor_usd: float
    total_incentive_ceiling_usd: float
    travel_incremental_delta_usd: float | None
    fx_delta_usd: float | None
    financing_cost_usd: float
    implementation_cost_usd: float
    npc_verified_usd: float | None           # gross - floor incentives (+ financing)
    npc_with_adjustments_usd: float | None   # + travel + fx (each applied once)
    is_fully_priced: bool
    blockers: tuple[str, ...]
    stacking_note: str = ""
    inkind_note: str = ""
    recommendation: StructureRecommendation | None = None
    ownership_shares: dict[str, float] = field(default_factory=dict)
    treaty_slug: str | None = None
    notes: tuple[str, ...] = ()


# ── Segment pricing ──────────────────────────────────────────────────────────

def _segment_lines(
    allocations: list[AccountAllocation],
    spend_category_by_code: dict[str, str],
) -> list[BudgetLine]:
    """The segment's allocated accounts as BudgetLines. Split portions
    carry their split amount — the register derivation sees exactly the
    dollars allocated here and nothing else (the structural guarantee
    against double-counting)."""
    return [
        BudgetLine(
            account_code=a.account_code,
            description=a.description,
            amount_usd=a.amount_usd,
            spend_category=spend_category_by_code.get(a.account_code),
            is_memo=False,
        )
        for a in sorted(allocations, key=lambda a: a.account_code)
    ]


def price_segment(
    jurisdiction_code: str,
    program_slug: str | None,
    allocations: list[AccountAllocation],
    spend_category_by_code: dict[str, str],
    offshore_payroll_accounts: frozenset[str],
    production_type: str = "feature_film",
) -> SegmentEconomics:
    """Derive this segment's PARTIAL register and price it with the
    existing kernel. A non-incentive segment (program_slug None) is
    located spend only — no register, no incentive, never a blocker."""
    allocated = round(sum(a.amount_usd for a in allocations), 2)
    codes = tuple(sorted({a.account_code for a in allocations}))

    if program_slug is None:
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=None,
            claims_incentive=False, allocated_usd=allocated,
            account_codes=codes, executable=False,
            notes=(
                f"Spend located in {jurisdiction_code} claims no incentive in "
                "this structure — allocated, disclosed, unpriced for incentive.",
            ),
        )

    slug = canonical_slug(program_slug)
    doctrine = get_program_doctrine(slug)
    has_rate = len(get_rate_rules(slug)) > 0
    if doctrine is None or not has_rate:
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            blockers=(
                f"{jurisdiction_code}/{slug}: "
                + ("no classified qualification doctrine" if doctrine is None else "")
                + (" and " if doctrine is None and not has_rate else "")
                + ("no statutory rate rules" if not has_rate else "")
                + " — segment is not executable; never priced at a guessed rate.",
            ),
        )

    lines = _segment_lines(allocations, spend_category_by_code)
    facts = ProductionFacts(
        jurisdiction_code=jurisdiction_code,
        # By construction every allocated line is incurred IN this
        # segment's jurisdiction — the allocation, not a fact set, is
        # what keeps other jurisdictions' spend out of this register.
        accounts_outside_jurisdiction=frozenset(),
        offshore_payroll_accounts=frozenset(
            c for c in offshore_payroll_accounts if c in {l.account_code for l in lines}
        ),
    )
    register = derive_qualification_register(
        lines, program_slug=slug, facts=facts, rate=0.0,
        program_territorial_text=_TERRITORIAL_TEXT_BY_SLUG.get(slug),
    )
    qpe = round(sum(a.amount_usd for a in register
                    if a.state == QualificationState.QUALIFIES), 2)
    excluded = round(sum(a.amount_usd for a in register
                         if a.state == QualificationState.EXCLUDED), 2)
    unresolved = round(sum(
        a.amount_usd for a in register
        if a.state in (QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
                       QualificationState.STRUCTURING_OPPORTUNITY)
    ), 2)

    rr = resolve_program_rate(slug, production_type=production_type, qpe_usd=qpe)
    if rr is None:
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
            doctrine=doctrine.value,
            blockers=(
                f"{jurisdiction_code}/{slug}: statutory rate did not resolve for "
                f"this production type / segment QPE (${qpe:,.0f}) — minimum-"
                "spend or eligibility conditions unmet; excluded rather than guessed.",
            ),
        )

    # Same pricing kernel as everything else — no new math. Financing
    # is zero here by policy (explicit structure-level input only).
    floor_case = build_risk_cases(
        register=register, gross_budget_usd=allocated, rate=rr.floor_rate,
        structuring_paths=[], delay_weeks=0, bridge_rate=0.0,
        jurisdiction_code=jurisdiction_code,
    ).cases[RiskCase.CONSERVATIVE]
    ceiling_case = build_risk_cases(
        register=register, gross_budget_usd=allocated, rate=rr.modeled_rate,
        structuring_paths=[], delay_weeks=0, bridge_rate=0.0,
        jurisdiction_code=jurisdiction_code,
    ).cases[RiskCase.CONSERVATIVE]

    trace = tuple(
        {
            "account_code": a.account_code,
            "description": a.description,
            "amount_usd": a.amount_usd,
            "state": a.state.value,
            "authority_basis": a.authority_basis.value,
            "reason": a.reason,
        }
        for a in register
    )

    return SegmentEconomics(
        jurisdiction_code=jurisdiction_code, program_slug=slug,
        claims_incentive=True, allocated_usd=allocated,
        account_codes=codes, executable=True,
        qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
        rate_floor=rr.floor_rate, rate_ceiling=rr.modeled_rate,
        is_band_ceiling=rr.is_band_ceiling, statutory_basis=rr.basis,
        incentive_floor_usd=floor_case.incentive_usd,
        incentive_ceiling_usd=ceiling_case.incentive_usd,
        doctrine=doctrine.value,
        register_trace=trace,
    )


# ── Treaty / ownership legality ──────────────────────────────────────────────

def _treaty_requirements(
    spec: StructureSpec,
    allocation: AllocationResult,
) -> tuple[list[str], str | None]:
    """Blockers arising from a claimed treaty/co-production status,
    evaluated against the REAL treaty registry (treaty_engine) and the
    allocation's own spend shares. Never forces a result: absence of an
    instrument is a blocker, not a fabricated unlock."""
    if spec.structure_type not in ("treaty_coproduction", "majority_minority",
                                   "multi_party", "hybrid"):
        return [], None

    blockers: list[str] = []
    codes = tuple(sorted(spec.participants))
    treaty_slug: str | None = None

    pairs = [(a, b) for i, a in enumerate(codes) for b in codes[i + 1:]]
    covered_pairs = 0
    for a, b in pairs:
        treaty = te.get_bilateral_treaty(a, b)
        if treaty is not None:
            covered_pairs += 1
            treaty_slug = treaty.treaty_slug
        elif te.is_european_convention_signatory(a) and te.is_european_convention_signatory(b):
            covered_pairs += 1
            treaty_slug = treaty_slug or "european_convention"
    if covered_pairs < len(pairs):
        blockers.append(
            f"No co-production treaty instrument is registered covering {codes} "
            "(treaty_engine registry) — official co-production status is not "
            "available; each jurisdiction's spend must qualify independently."
        )

    # Ownership/participation shares against the allocation's real spend
    # shares — a claimed share that the allocation contradicts is a blocker.
    if spec.ownership_shares:
        share_total = round(sum(spec.ownership_shares.values()), 6)
        if abs(share_total - 1.0) > 1e-6:
            blockers.append(
                f"Ownership shares must sum to 1.0 (got {share_total}) — "
                "participation structure is not internally consistent."
            )
        by_jur = allocation.allocated_by_jurisdiction()
        cash_total = allocation.total_budget_lines_usd or 1.0
        for jur, share in sorted(spec.ownership_shares.items()):
            spend_share = round(by_jur.get(jur, 0.0) / cash_total, 4)
            if share >= 0.5 and spend_share < 0.2:
                blockers.append(
                    f"{jur} claims majority participation ({share:.0%}) but the "
                    f"allocation places only {spend_share:.1%} of spend there — "
                    "co-production certification typically requires participation "
                    "to be reflected in real spend; resolve before claiming."
                )
    return blockers, treaty_slug


# ── Structure pricing ────────────────────────────────────────────────────────

def price_allocated_structure(
    spec: StructureSpec,
    allocation: AllocationResult,
    spend_category_by_code: dict[str, str],
    offshore_payroll_accounts: frozenset[str],
    gross_budget_usd: float,
    travel_incremental_delta_usd: float | None = None,
    fx_delta_usd: float | None = None,
    financing_cost_usd: float = 0.0,
    implementation_cost_usd: float = 0.0,
    production_type: str = "feature_film",
) -> AllocatedStructurePricing:
    """Price a complete structure from its allocation. Travel and FX
    deltas are structure-level, computed ONCE by the caller (for the
    primary jurisdiction against the original geography) and applied
    ONCE here. Financing/implementation default to zero — explicit
    inputs only, never a silent assumption."""
    blockers: list[str] = list()
    notes: list[str] = []

    if not allocation.is_complete:
        if allocation.unallocated_account_codes:
            blockers.append(
                "Unallocated accounts "
                f"{allocation.unallocated_account_codes} — every cash dollar "
                "must be allocated exactly once before this structure can be priced."
            )
        if allocation.duplicate_account_codes:
            blockers.append(
                f"Duplicate account allocations {allocation.duplicate_account_codes} "
                "— an account may not be counted in two jurisdictions without an "
                "explicit lawful split."
            )
        if not allocation.conserves:
            blockers.append(
                f"Allocation total ${allocation.total_allocated_usd:,.2f} does not "
                f"conserve the cash budget ${allocation.total_budget_lines_usd:,.2f}."
            )

    conditional = [
        a for a in allocation.assignments
        if a.assignment_kind == AssignmentKind.CONDITIONAL
    ]
    if conditional:
        blockers.append(
            f"{len(conditional)} conditional assignment(s) unresolved — "
            "the governing requirements must resolve before pricing."
        )

    treaty_blockers, treaty_slug = _treaty_requirements(spec, allocation)
    blockers.extend(treaty_blockers)

    # ── segments ──
    by_jur: dict[str, list[AccountAllocation]] = {}
    for a in allocation.assignments:
        by_jur.setdefault(a.jurisdiction_code, []).append(a)

    segments: list[SegmentEconomics] = []
    for jur in sorted(by_jur):
        seg = price_segment(
            jurisdiction_code=jur,
            program_slug=spec.incentive_programs.get(jur),
            allocations=by_jur[jur],
            spend_category_by_code=spend_category_by_code,
            offshore_payroll_accounts=offshore_payroll_accounts,
            production_type=production_type,
        )
        segments.append(seg)
        blockers.extend(seg.blockers)

    total_floor = round(sum(s.incentive_floor_usd for s in segments), 2)
    total_ceiling = round(sum(s.incentive_ceiling_usd for s in segments), 2)

    fully_priced = not blockers

    npc_verified = None
    npc_adjusted = None
    if fully_priced:
        npc_verified = round(
            gross_budget_usd - total_floor
            + financing_cost_usd + implementation_cost_usd, 2,
        )
        npc_adjusted = round(
            npc_verified
            + (travel_incremental_delta_usd or 0.0)
            + (fx_delta_usd or 0.0), 2,
        )

    unresolved_reqs = sorted({
        r for a in allocation.assignments for r in a.unresolved_requirements
    })

    stacking_note = (
        "Exactly one incentive program is priced per jurisdiction segment — "
        "no unlawful stacking is possible by construction. Additional-program "
        "combinations enter only via enumerate_segment_program_stacks() when "
        "real multi-program knowledge exists for a segment's jurisdiction."
    )
    inkind_note = (
        "The $625,000 off-budget in-kind post FMV is NOT included in any "
        "segment here. It remains exclusively governed by the Mauritius "
        "economics controls' selected treatment (/economics) and can never "
        "attach to a non-Mauritius segment."
    )
    if travel_incremental_delta_usd is None:
        notes.append(
            "Travel adjustment not modeled for this structure (no fabricated "
            "figure) — see notes on the serving builder."
        )
    if financing_cost_usd == 0.0:
        notes.append("Financing cost is $0 by default — explicit producer input only.")

    pricing = AllocatedStructurePricing(
        pricing_version=ALLOCATION_PRICING_VERSION,
        structure_id=spec.structure_id,
        structure_type=spec.structure_type,
        label=spec.label,
        primary_jurisdiction=spec.primary_jurisdiction,
        participants=spec.participants,
        allocation=allocation,
        segments=tuple(segments),
        gross_budget_usd=gross_budget_usd,
        total_incentive_floor_usd=total_floor,
        total_incentive_ceiling_usd=total_ceiling,
        travel_incremental_delta_usd=travel_incremental_delta_usd,
        fx_delta_usd=fx_delta_usd,
        financing_cost_usd=financing_cost_usd,
        implementation_cost_usd=implementation_cost_usd,
        npc_verified_usd=npc_verified,
        npc_with_adjustments_usd=npc_adjusted,
        is_fully_priced=fully_priced,
        blockers=tuple(dict.fromkeys(blockers)),  # dedupe, order-preserving
        stacking_note=stacking_note,
        inkind_note=inkind_note,
        ownership_shares=dict(spec.ownership_shares),
        treaty_slug=treaty_slug or spec.treaty_slug,
        notes=tuple(notes),
    )
    pricing.recommendation = build_structure_recommendation(pricing, unresolved_reqs)
    return pricing


# ── Gated structure recommendation (cloud-engine concepts, merged) ──────────

def build_structure_recommendation(
    pricing: AllocatedStructurePricing,
    unresolved_requirements: list[str],
) -> StructureRecommendation:
    """Deterministic identity (REC-STRUCT-<structure_id>), gated action,
    ordered approval chain, reversibility, and a dependency group —
    the capabilities merged from the recovered cloud Recommendation
    Engine (branch cloud-session-recovery-recommendation-engine), with
    every figure sourced from THIS pricing (stale cloud fixtures never
    enter)."""
    approval_chain: list[str] = ["producer"]
    if any(a.assignment_kind == AssignmentKind.USER_ELECTED
           for a in pricing.allocation.assignments):
        pass  # producer approval already first in chain
    if pricing.treaty_slug or pricing.structure_type in (
        "treaty_coproduction", "majority_minority", "multi_party", "hybrid",
        "service_production",
    ):
        approval_chain.append("counsel")
    if pricing.blockers or unresolved_requirements:
        approval_chain.append("authority")

    reversibility = (
        "hard_to_reverse"
        if pricing.treaty_slug or pricing.structure_type in (
            "treaty_coproduction", "majority_minority", "multi_party")
        else "reversible_before_execution"
    )

    dependency_group = tuple(
        list(pricing.blockers) + list(unresolved_requirements)
    )

    explanation = {
        "structure": {
            "structure_id": pricing.structure_id,
            "structure_type": pricing.structure_type,
            "participants": list(pricing.participants),
            "treaty_slug": pricing.treaty_slug,
            "ownership_shares": pricing.ownership_shares,
        },
        "allocated_budget_lines": [
            {
                "account_code": a.account_code,
                "amount_usd": a.amount_usd,
                "jurisdiction_code": a.jurisdiction_code,
                "component": a.component,
                "assignment_kind": a.assignment_kind.value,
                "governing_decision": a.governing_decision,
            }
            for a in pricing.allocation.assignments
        ],
        "authority": [
            {
                "jurisdiction_code": s.jurisdiction_code,
                "program_slug": s.program_slug,
                "statutory_basis": s.statutory_basis,
                "doctrine": s.doctrine,
            }
            for s in pricing.segments if s.claims_incentive
        ],
        "production_facts": sorted({
            f for a in pricing.allocation.assignments for f in a.supporting_facts
        }),
        "assumptions": [
            "Financing cost $0 unless explicitly supplied.",
            "One incentive program priced per jurisdiction segment.",
            pricing.inkind_note,
        ],
        "calculations": {
            "gross_budget_usd": pricing.gross_budget_usd,
            "segment_incentives_floor_usd": {
                s.jurisdiction_code: s.incentive_floor_usd for s in pricing.segments
            },
            "total_incentive_floor_usd": pricing.total_incentive_floor_usd,
            "travel_incremental_delta_usd": pricing.travel_incremental_delta_usd,
            "fx_delta_usd": pricing.fx_delta_usd,
            "npc_verified_usd": pricing.npc_verified_usd,
            "npc_with_adjustments_usd": pricing.npc_with_adjustments_usd,
        },
        "approvals_and_actions": unresolved_requirements + list(pricing.blockers),
    }

    return StructureRecommendation(
        recommendation_id=f"REC-STRUCT-{pricing.structure_id}",
        action=(
            f"Adopt structure '{pricing.label}'"
            if pricing.is_fully_priced
            else f"Resolve blockers before structure '{pricing.label}' can be adopted"
        ),
        gated=bool(pricing.blockers or unresolved_requirements),
        approval_chain=tuple(dict.fromkeys(approval_chain)),
        reversibility=reversibility,
        dependency_group=dependency_group,
        explanation=explanation,
    )


# ── Ranking ──────────────────────────────────────────────────────────────────

def rank_allocated_structures(
    pricings: list[AllocatedStructurePricing],
) -> list[dict]:
    """Financial ranking over FULLY PRICED structures only (verified NPC
    with adjustments, ascending). Unpriced structures are listed after,
    unranked, with their exact blockers — never silently dropped and
    never ranked on a partial number."""
    priced = sorted(
        (p for p in pricings if p.is_fully_priced),
        key=lambda p: (p.npc_with_adjustments_usd, p.structure_id),
    )
    unpriced = sorted(
        (p for p in pricings if not p.is_fully_priced),
        key=lambda p: p.structure_id,
    )
    ranking: list[dict] = []
    for i, p in enumerate(priced, start=1):
        ranking.append({
            "rank": i,
            "structure_id": p.structure_id,
            "label": p.label,
            "is_fully_priced": True,
            "npc_verified_usd": p.npc_verified_usd,
            "npc_with_adjustments_usd": p.npc_with_adjustments_usd,
        })
    for p in unpriced:
        ranking.append({
            "rank": None,
            "structure_id": p.structure_id,
            "label": p.label,
            "is_fully_priced": False,
            "excluded_from_ranking_because": list(p.blockers),
        })
    return ranking


# ── Per-segment program-stack enumeration (existing engine, delegated) ──────

def enumerate_segment_program_stacks(
    jurisdiction: dict,
    line_items: list[dict],
    candidate_programs: list[dict],
    stacking_rules: list[dict],
    max_combination_size: int = 3,
) -> list:
    """Delegates multi-program combination enumeration for ONE segment's
    jurisdiction to the EXISTING generate_structure_scenarios engine
    (canonical owner of program/stack combinatorics + the existing
    stacking math via run_full_analysis). Invoked only when a segment's
    jurisdiction genuinely has more than one executable program with
    real program data — with a single program there is nothing to
    combine and this returns []. Nothing here re-implements the engine."""
    if len(candidate_programs) < 2:
        return []
    from app.calculators.generate_structure_scenarios import generate_structure_scenarios
    return generate_structure_scenarios(
        jurisdiction=jurisdiction,
        line_items=line_items,
        candidate_programs=candidate_programs,
        stacking_rules=stacking_rules,
        max_combination_size=max_combination_size,
    )
