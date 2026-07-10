"""
global_scenario_ranker.py

Phase 7B of CineGlobe: the Global Scenario Ranker / Production Structure
Composer.

Phase 7A (opportunity_discovery.py) answers "what candidate optimization
paths exist worldwide?" — 144 Opportunity objects today, unordered
relative to each other and uncomposed into anything a producer could
actually file. This module answers the next question: "which
*combinations* of compatible opportunities form a coherent production
structure, and how do those structures rank by risk-adjusted Net
Production Cost?"

This is composition and ranking only:

- It does not discover new opportunities. Every ProductionStructure is
  built exclusively from the Opportunity objects already present in the
  OpportunityCollection passed in.
- It does not perform legal research or change qualification/authority
  state. Blocking requirements (evidence, approvals, LAAE task
  references) carried on an Opportunity are surfaced on the structure
  that includes it, never resolved here.
- It does not change QPE math, Authority Score math, or
  optimization_engine.py. The only computation this module performs is
  build_risk_cases() — called exactly as any other caller would call it,
  with the same register/grey-area/structuring-path inputs — via the
  existing opportunities_to_structuring_paths() bridge from
  opportunity_discovery.py. A baseline structure with the same evidence
  state as today's Little Utopia run produces byte-identical
  Conservative/Base/Optimistic/Risk-Adjusted figures.

Claim ledger (double-counting prevention):

Every opportunity that names affected_accounts stakes a claim on
(jurisdiction_code, account_code). A candidate structure may not include
two opportunities that claim the same key unless a Pass-3 "known_stack"
Opportunity (opportunity_discovery.OpportunityType.STACKING, subtype
"known_stack" — the one subtype Pass 3 only ever emits from a real
STACKS_WITH edge already present in the Jurisdiction Graph) connects
them. An UNKNOWN/absent stacking-rule opportunity (subtype
"stacking_unknown") never authorizes a claim conflict to be waived —
unknown stacking stays gated, exactly as Pass 3 designed it.

Dependency enforcement:

An opportunity whose dependent_opportunity_ids are not all satisfied
within the same candidate structure is excluded from it, with the
specific unmet dependency recorded — never silently included, never
silently dropped without a reason.

Sparse-data honesty:

Only a structure with a real qualification register/gross budget/rate
(today, Mauritius/Little Utopia) is priced through
optimization_engine.build_risk_cases() and exposes all four risk cases.
Every other candidate structure (e.g. a relocation candidate to a
jurisdiction with no populated register) is marked is_priceable=False
and carries only whatever dollar figures the underlying opportunities
already computed (informational_upside_usd) — never a fabricated NPC.

Deterministic: fixed input ordering (discovery_rank_score descending,
opportunity_id tie-break, matching Phase 7A's own rank_opportunities()),
no wall-clock, no randomness. The same OpportunityCollection composes and
ranks identically on every run.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.calculators.opportunity_discovery import (
    Opportunity,
    OpportunityCollection,
    OpportunityType,
    opportunities_to_structuring_paths,
)
from app.calculators.optimization_engine import (
    CaseResult,
    RiskCase,
    build_risk_cases,
)
from app.calculators.qualification_model import AccountQualification, GreyAreaItem

GLOBAL_SCENARIO_RANKER_VERSION = "1.0.0"


# ── Claim ledger ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StructureClaim:
    """One opportunity's stake on one (jurisdiction, account) budget
    segment within a single candidate structure."""
    claim_key: str
    opportunity_id: str


@dataclass
class ClaimLedger:
    """
    Per-structure record of which opportunity claimed which budget
    segment. Deliberately not shared across structures — the same
    account may be legitimately claimed differently in two competing
    candidate structures (e.g. a structuring lever in the baseline
    structure vs. nothing at all in a relocation structure).
    """
    claims: list[StructureClaim] = field(default_factory=list)

    def claimed_by(self, claim_key: str) -> list[str]:
        return [c.opportunity_id for c in self.claims if c.claim_key == claim_key]

    def record(self, claim_key: str, opportunity_id: str) -> None:
        self.claims.append(StructureClaim(claim_key=claim_key, opportunity_id=opportunity_id))

    def all_keys(self) -> tuple[str, ...]:
        return tuple(sorted({c.claim_key for c in self.claims}))


def _claim_keys_for(opportunity: Opportunity) -> list[str]:
    """(jurisdiction, account) keys an opportunity stakes a claim on. An
    opportunity with no affected_accounts (most treaty/jurisdiction/
    reinvestment/normalization opportunities) claims nothing and can
    never produce a double-counting conflict."""
    if not opportunity.affected_accounts:
        return []
    jurisdiction = opportunity.jurisdiction_codes[0] if opportunity.jurisdiction_codes else "UNSPECIFIED"
    return [f"{jurisdiction}:{account}" for account in opportunity.affected_accounts]


def _stacking_permits(opp_a: Opportunity, opp_b: Opportunity, known_stacks: list[Opportunity]) -> bool:
    """True only if a real known_stack Opportunity's two graph_refs
    connect opp_a and opp_b directly — the STACKS_WITH-evidence
    exception to the claim ledger. A stacking_unknown opportunity (or any
    other subtype) never satisfies this, by construction: known_stacks is
    always pre-filtered to subtype == 'known_stack' by the caller."""
    a_refs, b_refs = set(opp_a.graph_refs), set(opp_b.graph_refs)
    for stack in known_stacks:
        if len(stack.graph_refs) != 2:
            continue
        x, y = stack.graph_refs
        if (x in a_refs and y in b_refs) or (y in a_refs and x in b_refs):
            return True
    return False


# ── Production structure ─────────────────────────────────────────────────

@dataclass
class ProductionStructure:
    """
    One candidate, internally-consistent combination of opportunities. No
    two included opportunities double-claim a budget segment; every
    included opportunity's dependencies are satisfied by other included
    opportunities. Blocking requirements are surfaced, not resolved.
    """
    structure_id: str
    label: str
    baseline_jurisdiction: str
    included_opportunity_ids: tuple[str, ...]
    excluded_opportunity_ids: tuple[str, ...]
    exclusion_reasons: dict[str, str]
    claim_ledger: ClaimLedger
    blocking_requirements: tuple[str, ...]
    is_priceable: bool
    cases: Optional[dict[RiskCase, CaseResult]] = None
    informational_upside_usd: Optional[float] = None
    attributes: dict = field(default_factory=dict)

    @property
    def risk_adjusted_npc_usd(self) -> Optional[float]:
        if not self.cases:
            return None
        return self.cases[RiskCase.RISK_ADJUSTED].net_production_cost_usd


@dataclass(frozen=True)
class StructureRank:
    structure_id: str
    label: str
    is_priceable: bool
    risk_adjusted_npc_usd: Optional[float]
    rank: int


@dataclass
class StructureRankingResult:
    baseline_jurisdiction: str
    structures: list[ProductionStructure]
    ranks: list[StructureRank]

    def best(self) -> Optional[ProductionStructure]:
        """The lowest risk-adjusted NPC among priceable structures, or
        None if nothing in this result is priceable — never a guess at
        which unpriced structure is 'best'."""
        priceable = [s for s in self.structures if s.is_priceable]
        return priceable[0] if priceable else None


# ── Inclusion resolution (dependency + claim ledger) ─────────────────────

def _blocking_requirements(included: list[Opportunity]) -> tuple[str, ...]:
    lines: set[str] = set()
    for opp in included:
        if opp.requires_evidence:
            tasks = ", ".join(opp.acquisition_task_refs) or "no LAAE task recorded"
            evidence = "; ".join(opp.required_evidence) or "unspecified"
            lines.add(f"{opp.opportunity_id}: requires evidence ({evidence}) — LAAE task(s): {tasks}")
        if opp.required_approvals:
            lines.add(f"{opp.opportunity_id}: requires approval — {'; '.join(opp.required_approvals)}")
        if opp.blocking_requirements:
            lines.add(f"{opp.opportunity_id}: blocked on — {'; '.join(opp.blocking_requirements)}")
    return tuple(sorted(lines))


def _resolve_inclusion(
    candidates: list[Opportunity],
    known_stacks: list[Opportunity],
) -> tuple[list[Opportunity], dict[str, str], ClaimLedger]:
    """
    Fixed-point worklist over a fixed, deterministic ordering
    (discovery_rank_score descending, opportunity_id tie-break — the same
    ordering rank_opportunities() uses in Phase 7A). An opportunity is
    included once all of its dependencies are already included and none
    of its claim keys conflict with an already-included opportunity
    (absent qualifying STACKS_WITH evidence). Anything that can never
    satisfy those conditions is excluded with a specific, recorded
    reason — never silently dropped and never silently included.
    """
    by_id = {o.opportunity_id: o for o in candidates}
    ordered = sorted(candidates, key=lambda o: (-o.discovery_rank_score, o.opportunity_id))
    included: dict[str, Opportunity] = {}
    excluded_reasons: dict[str, str] = {}
    ledger = ClaimLedger()

    changed = True
    while changed:
        changed = False
        for opp in ordered:
            if opp.opportunity_id in included or opp.opportunity_id in excluded_reasons:
                continue

            missing_deps = [d for d in opp.dependent_opportunity_ids if d not in included]
            if missing_deps:
                still_resolvable = [d for d in missing_deps if d in by_id and d not in excluded_reasons]
                if still_resolvable:
                    continue  # give dependencies another pass
                excluded_reasons[opp.opportunity_id] = (
                    f"Depends on {tuple(missing_deps)}, not included in this structure."
                )
                changed = True
                continue

            conflict: Optional[tuple[str, str]] = None
            for key in _claim_keys_for(opp):
                for other_id in ledger.claimed_by(key):
                    other = included[other_id]
                    if not _stacking_permits(opp, other, known_stacks):
                        conflict = (key, other_id)
                        break
                if conflict:
                    break
            if conflict:
                key, other_id = conflict
                excluded_reasons[opp.opportunity_id] = (
                    f"Claim conflict on '{key}' with already-included '{other_id}' — "
                    "no STACKS_WITH evidence permits both to be booked."
                )
                changed = True
                continue

            for key in _claim_keys_for(opp):
                ledger.record(key, opp.opportunity_id)
            included[opp.opportunity_id] = opp
            changed = True

    for opp in ordered:
        if opp.opportunity_id not in included and opp.opportunity_id not in excluded_reasons:
            excluded_reasons[opp.opportunity_id] = "Dependency chain could not be resolved (circular or missing)."

    return [included[o.opportunity_id] for o in ordered if o.opportunity_id in included], excluded_reasons, ledger


def _sum_informational_upside(included: list[Opportunity], is_priceable: bool) -> Optional[float]:
    """
    None whenever the structure is priced through build_risk_cases() —
    that computation already reflects every structuring/grey-area dollar
    figure via the register/structuring-path/grey-area inputs, so adding
    each opportunity's own estimated_upside_usd on top would double-count
    it. For non-priceable structures, sums whatever real dollar figures
    the included opportunities already carry; returns None (never 0.0)
    when nothing has a known figure, so "no data" is never confused with
    "zero opportunity".
    """
    if is_priceable:
        return None
    values = [o.estimated_upside_usd for o in included if o.estimated_upside_usd is not None]
    if not values:
        return None
    return round(sum(values), 2)


# ── Composition ───────────────────────────────────────────────────────────

def compose_candidate_structures(
    collection: OpportunityCollection,
    register: Optional[list[AccountQualification]] = None,
    gross_budget_usd: Optional[float] = None,
    rate: Optional[float] = None,
    grey_areas: Optional[list[GreyAreaItem]] = None,
    delay_weeks: int = 39,
    bridge_rate: float = 0.08,
) -> list[ProductionStructure]:
    """
    Builds one baseline ProductionStructure (every opportunity touching
    collection.baseline_jurisdiction) plus one relocation-candidate
    structure per Pass-1 "relocation_candidate" Opportunity rooted at the
    baseline.

    register/gross_budget_usd/rate/grey_areas are the caller's real
    production inputs (the same ones passed to
    optimization_engine.build_risk_cases() directly today). When all of
    register/gross_budget_usd/rate are supplied, the baseline structure
    is priced; when any is omitted, the baseline structure is honestly
    marked non-priceable rather than guessing at figures.

    Only the baseline jurisdiction is ever priced — a relocation
    candidate has no register in this codebase, so pricing it would mean
    inventing one; it stays informational.
    """
    baseline = collection.baseline_jurisdiction
    known_stacks = [
        o for o in collection.opportunities
        if o.opportunity_type == OpportunityType.STACKING and o.subtype == "known_stack"
    ]

    structures: list[ProductionStructure] = []

    baseline_candidates = [o for o in collection.opportunities if baseline in o.jurisdiction_codes]
    included, excluded_reasons, ledger = _resolve_inclusion(baseline_candidates, known_stacks)

    is_priceable = register is not None and gross_budget_usd is not None and rate is not None
    cases: Optional[dict[RiskCase, CaseResult]] = None
    if is_priceable:
        paths = opportunities_to_structuring_paths(
            included, register=register, rate=rate, jurisdiction_code=baseline,
        )
        result = build_risk_cases(
            register=register, gross_budget_usd=gross_budget_usd, rate=rate,
            structuring_paths=paths, grey_areas=grey_areas or [],
            delay_weeks=delay_weeks, bridge_rate=bridge_rate, jurisdiction_code=baseline,
        )
        cases = result.cases

    structures.append(ProductionStructure(
        structure_id=f"STRUCT-BASELINE-{baseline}",
        label=f"{baseline} baseline",
        baseline_jurisdiction=baseline,
        included_opportunity_ids=tuple(o.opportunity_id for o in included),
        excluded_opportunity_ids=tuple(sorted(excluded_reasons)),
        exclusion_reasons=excluded_reasons,
        claim_ledger=ledger,
        blocking_requirements=_blocking_requirements(included),
        is_priceable=is_priceable,
        cases=cases,
        informational_upside_usd=_sum_informational_upside(included, is_priceable),
    ))

    relocation_opps = [
        o for o in collection.opportunities
        if o.opportunity_type == OpportunityType.JURISDICTION
        and o.subtype == "relocation_candidate"
        and o.jurisdiction_codes
        and o.jurisdiction_codes[0] == baseline
    ]
    for reloc in sorted(relocation_opps, key=lambda o: o.opportunity_id):
        target = reloc.jurisdiction_codes[1]
        scoped = [reloc] + [
            o for o in collection.opportunities
            if reloc.opportunity_id in o.dependent_opportunity_ids
        ]
        included_r, excluded_r, ledger_r = _resolve_inclusion(scoped, known_stacks)
        structures.append(ProductionStructure(
            structure_id=f"STRUCT-RELOCATE-{baseline}-{target}",
            label=f"Relocate {baseline} -> {target}",
            baseline_jurisdiction=baseline,
            included_opportunity_ids=tuple(o.opportunity_id for o in included_r),
            excluded_opportunity_ids=tuple(sorted(excluded_r)),
            exclusion_reasons=excluded_r,
            claim_ledger=ledger_r,
            blocking_requirements=_blocking_requirements(included_r),
            is_priceable=False,
            cases=None,
            informational_upside_usd=_sum_informational_upside(included_r, False),
            attributes={"target_jurisdiction": target},
        ))

    return structures


# ── Ranking ───────────────────────────────────────────────────────────────

def rank_production_structures(structures: list[ProductionStructure]) -> StructureRankingResult:
    """
    Priceable structures rank first, ascending by Risk-Adjusted Net
    Production Cost (lower NPC is better) — ties broken by structure_id.
    Non-priceable structures are appended after, in structure_id order,
    each still assigned a rank position but with risk_adjusted_npc_usd
    left None: their relative order carries no cost signal, since none
    exists to compare.
    """
    baseline = structures[0].baseline_jurisdiction if structures else ""
    priceable = sorted(
        (s for s in structures if s.is_priceable and s.cases),
        key=lambda s: (s.risk_adjusted_npc_usd, s.structure_id),
    )
    non_priceable = sorted(
        (s for s in structures if not (s.is_priceable and s.cases)),
        key=lambda s: s.structure_id,
    )

    ranks: list[StructureRank] = []
    for i, s in enumerate(priceable + non_priceable, start=1):
        ranks.append(StructureRank(
            structure_id=s.structure_id,
            label=s.label,
            is_priceable=s.is_priceable and s.cases is not None,
            risk_adjusted_npc_usd=s.risk_adjusted_npc_usd,
            rank=i,
        ))

    return StructureRankingResult(
        baseline_jurisdiction=baseline,
        structures=priceable + non_priceable,
        ranks=ranks,
    )
