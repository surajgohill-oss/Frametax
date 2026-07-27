"""
production_structure_composer.py

Phase 7C of CineGlobe: the Multi-Jurisdiction Production Structure
Composer.

Phase 7B (global_scenario_ranker.py) composes opportunities into
single-baseline structures — "stay in MU" vs. "relocate to X". This
module generalizes the shape of a candidate: a production is no longer
mapped to one jurisdiction but to a SET of jurisdictions, each carrying
its own program, with treaties, funds, stacks, levers, and normalization
opportunities composed on top — the full
production -> jurisdictions -> programs -> treaties -> funds -> levers
-> normalization -> risk cases -> ranked structure chain.

Composition only. This module:

- performs no new calculation: pricing is exactly one call to the
  existing optimization_engine.build_risk_cases(), through the existing
  opportunities_to_structuring_paths() bridge, with the same inputs any
  direct caller supplies. Authority Score math, QPE math, discovery
  logic, and the Phase 7B ranker are all untouched.
- invents nothing: a treaty is attached only if treaty_engine's
  registries actually contain it for the participating countries; a fund
  only if every participant is a member of the unlocking multilateral
  AND the participant count meets the treaty's own
  min_coproducer_countries; a stack only via a Pass-3 "known_stack"
  opportunity (real STACKS_WITH evidence) — "stacking_unknown" never
  authorizes anything and instead becomes a visible StructureConstraint
  with its LAAE task reference; routing/structuring only via existing
  Lever-backed STRUCTURING opportunities; qualification and dollar
  values only where an existing engine already computed them.
- prices what it can and says so: a candidate whose jurisdiction set
  includes the one register-backed jurisdiction (Little Utopia / MU
  today) exposes all four risk cases for that portion; every other
  segment is carried unpriced, and the candidate reports its
  priceable_pct / unknown_pct honestly instead of collapsing to a
  fabricated total.

Deterministic throughout: fixed iteration over sorted structures, the
same ordering rule Phase 7A/7B use (discovery_rank_score descending,
opportunity_id tie-break), no wall-clock, no randomness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.calculators import treaty_engine as te
from app.calculators.global_scenario_ranker import ClaimLedger
from app.calculators.jurisdiction_graph import JurisdictionGraph, NodeType
from app.calculators.opportunity_discovery import (
    Opportunity,
    OpportunityCollection,
    OpportunityType,
    opportunities_to_structuring_paths,
)
from app.calculators.optimization_engine import CaseResult, RiskCase, build_risk_cases
from app.calculators.qualification_model import AccountQualification, GreyAreaItem

PRODUCTION_STRUCTURE_COMPOSER_VERSION = "1.0.0"

COMPOSITION_PASSES: tuple[str, ...] = (
    "jurisdiction_composition",
    "treaty_composition",
    "stack_composition",
    "fund_composition",
    "structuring_composition",
    "normalization_composition",
    "constraint_resolution",
    "duplicate_elimination",
    "dominance_pruning",
    "return_survivors",
)


# ── Segment / claim / composition objects ────────────────────────────────────

@dataclass(frozen=True)
class StructureSegment:
    """One traceable component of a candidate structure. kind is the
    composition dimension ('jurisdiction', 'treaty', 'fund', 'stack',
    'lever', 'normalization', 'grey_area'); graph_ref is the Jurisdiction
    Graph node id it resolves to, so every segment remains checkable
    against the graph."""
    segment_id: str
    kind: str
    graph_ref: str
    jurisdiction_codes: tuple[str, ...] = ()
    priceable: bool = False


@dataclass(frozen=True)
class JurisdictionSegment:
    """One participating jurisdiction with its national program, and
    whether a real qualification register backs it (the precondition for
    pricing that segment — never assumed)."""
    jurisdiction_code: str
    program_slug: str
    country_graph_ref: str
    program_graph_ref: str
    has_register: bool


@dataclass(frozen=True)
class IncentiveClaim:
    """One opportunity's booked claim on one (jurisdiction, account)
    budget segment within this candidate — the composer-level record the
    ClaimLedger enforces uniqueness over."""
    claim_key: str  # "<jurisdiction>:<account>"
    opportunity_id: str
    program_slug: str


@dataclass(frozen=True)
class TreatyComposition:
    """A treaty actually registered for the participating countries —
    never synthesized. kind distinguishes a direct bilateral from a
    European Convention composition path from a multilateral
    membership."""
    treaty_slug: str
    kind: str  # "bilateral" | "convention_composition" | "multilateral"
    jurisdiction_codes: tuple[str, ...]
    graph_ref: str
    cultural_test_required: bool
    confidence_tier: str


@dataclass(frozen=True)
class StackComposition:
    """A stack included because real STACKS_WITH evidence exists (a
    Pass-3 'known_stack' opportunity). Unknown stacking never appears
    here — it appears in StructureConstraint instead."""
    stack_opportunity_id: str
    component_graph_refs: tuple[str, ...]
    graph_rule_id: Optional[str]


@dataclass(frozen=True)
class StructureConstraint:
    """A visible, unresolved gate on this structure: evidence to acquire,
    an approval to obtain, an unmet dependency, or unknown authority.
    Constraints are carried, never resolved here and never hidden."""
    constraint_id: str
    kind: str  # "evidence" | "approval" | "dependency" | "authority" | "treaty_absence" | "stacking_unknown"
    description: str
    opportunity_id: Optional[str] = None
    acquisition_task_refs: tuple[str, ...] = ()


@dataclass
class ProductionStructureCandidate:
    """One complete multi-jurisdiction candidate. Everything it
    participates in is exposed as typed segments/compositions that trace
    to graph node ids; everything it is blocked on is exposed as
    StructureConstraints; whatever portion of it the existing engines can
    price is priced, and priceable_pct/unknown_pct state plainly how much
    that is."""
    candidate_id: str
    label: str
    jurisdiction_segments: tuple[JurisdictionSegment, ...]
    treaty_compositions: tuple[TreatyComposition, ...]
    stack_compositions: tuple[StackComposition, ...]
    fund_graph_refs: tuple[str, ...]
    incentive_claims: tuple[IncentiveClaim, ...]
    included_opportunity_ids: tuple[str, ...]
    excluded_opportunity_ids: tuple[str, ...]
    exclusion_reasons: dict[str, str]
    grey_area_opportunity_ids: tuple[str, ...]
    evidence_graph_refs: tuple[str, ...]          # graph_rule_id / graph_absence_id values
    required_approvals: tuple[str, ...]
    required_acquisition_task_refs: tuple[str, ...]
    constraints: tuple[StructureConstraint, ...]
    claim_ledger: ClaimLedger
    cases: Optional[dict[RiskCase, CaseResult]]
    priceable_pct: float
    unknown_pct: float
    attributes: dict = field(default_factory=dict)
    # Real, non-fabricated upside estimate for the NOT-YET-priceable
    # portion of this structure (e.g. a co-production jurisdiction's rate
    # advantage applied to the production's own real movable-spend
    # figure — see opportunity_discovery.discover_jurisdiction_opportunities).
    # Never double-counts .cases: only OpportunityType.STRUCTURING
    # opportunities ever feed .cases (via opportunities_to_structuring_paths),
    # and this sums a disjoint set (JURISDICTION-type opportunities that
    # carry their own estimated_upside_usd). None whenever no included
    # opportunity has a known figure — absence of data, not zero opportunity.
    informational_upside_usd: Optional[float] = None

    @property
    def participating_jurisdictions(self) -> tuple[str, ...]:
        return tuple(s.jurisdiction_code for s in self.jurisdiction_segments)

    @property
    def conditional_opportunity_ids(self) -> tuple[str, ...]:
        """The KNOWN BUT NON-PRICEABLE conditional funding avenues
        (discretionary grants / development / co-production / broadcaster /
        regional funds) this structure surfaces — included because a
        participating jurisdiction is the program's country, never priced
        into NPC. Derived from included_opportunity_ids by the conditional
        pass's deterministic OPP-COND- prefix, so no stored field or
        constructor change is needed."""
        return tuple(i for i in self.included_opportunity_ids if i.startswith("OPP-COND-"))

    @property
    def is_fully_priced(self) -> bool:
        return self.cases is not None and self.priceable_pct >= 1.0

    def npc(self, case: RiskCase) -> Optional[float]:
        if self.cases is None:
            return None
        return self.cases[case].net_production_cost_usd


@dataclass
class CompositionResult:
    baseline_jurisdiction: str
    passes_run: tuple[str, ...]
    candidates: list[ProductionStructureCandidate]
    pruned: dict[str, str]  # candidate_id -> pruning reason (dominance / duplicate)


# ── Inclusion resolution (same discipline as Phase 7B, scoped per candidate) ─

def _claim_keys_for(opportunity: Opportunity) -> list[str]:
    if not opportunity.affected_accounts:
        return []
    jurisdiction = opportunity.jurisdiction_codes[0] if opportunity.jurisdiction_codes else "UNSPECIFIED"
    return [f"{jurisdiction}:{account}" for account in opportunity.affected_accounts]


def _stacking_permits(opp_a: Opportunity, opp_b: Opportunity, known_stacks: list[Opportunity]) -> bool:
    """True only when a real known_stack opportunity's two graph_refs
    connect the pair — identical semantics to Phase 7B; stacking_unknown
    never qualifies because known_stacks is pre-filtered to
    subtype == 'known_stack'."""
    a_refs, b_refs = set(opp_a.graph_refs), set(opp_b.graph_refs)
    for stack in known_stacks:
        if len(stack.graph_refs) != 2:
            continue
        x, y = stack.graph_refs
        if (x in a_refs and y in b_refs) or (y in a_refs and x in b_refs):
            return True
    return False


def _resolve_inclusion(
    candidates: list[Opportunity],
    known_stacks: list[Opportunity],
) -> tuple[list[Opportunity], dict[str, str], ClaimLedger]:
    """Fixed-point worklist identical in discipline to Phase 7B's:
    deterministic ordering, dependencies must be satisfied within the
    same candidate structure, claim conflicts blocked absent real
    STACKS_WITH evidence, every exclusion recorded with its reason."""
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
            missing = [d for d in opp.dependent_opportunity_ids if d not in included]
            if missing:
                if any(d in by_id and d not in excluded_reasons for d in missing):
                    continue
                excluded_reasons[opp.opportunity_id] = (
                    f"Depends on {tuple(missing)}, not included in this structure."
                )
                changed = True
                continue
            conflict = None
            for key in _claim_keys_for(opp):
                for other_id in ledger.claimed_by(key):
                    if not _stacking_permits(opp, included[other_id], known_stacks):
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

    return (
        [included[o.opportunity_id] for o in ordered if o.opportunity_id in included],
        excluded_reasons,
        ledger,
    )


# ── Pass 1: jurisdiction composition ────────────────────────────────────────

def _jurisdiction_sets(
    collection: OpportunityCollection,
    extra_jurisdiction_sets: list[tuple[str, ...]],
) -> list[tuple[str, ...]]:
    """Deterministic candidate jurisdiction sets: the baseline alone,
    baseline + each partner surfaced by a Pass-1 JURISDICTION opportunity
    (relocation candidate or Tier-1 comparable), plus any explicit sets
    the caller supplies (e.g. a three-country Eurimages composition).
    Nothing is enumerated combinatorially — every set traces either to a
    discovered opportunity or to an explicit caller request."""
    baseline = collection.baseline_jurisdiction
    partners: set[str] = set()
    for o in collection.opportunities:
        if o.opportunity_type != OpportunityType.JURISDICTION:
            continue
        if len(o.jurisdiction_codes) == 2 and o.jurisdiction_codes[0] == baseline:
            partners.add(o.jurisdiction_codes[1])
    sets: list[tuple[str, ...]] = [(baseline,)]
    sets += [(baseline, p) for p in sorted(partners)]
    for extra in extra_jurisdiction_sets:
        canonical = tuple(sorted({c.upper() for c in extra}))
        if canonical and canonical not in sets:
            sets.append(canonical)
    return sets


def _jurisdiction_segments(
    codes: tuple[str, ...],
    graph: JurisdictionGraph,
    register_jurisdiction: Optional[str],
) -> tuple[JurisdictionSegment, ...]:
    segments = []
    program_by_code = {
        n.attributes.get("jurisdiction_code"): n
        for n in graph.nodes_of_type(NodeType.NATIONAL_PROGRAM)
    }
    for code in codes:
        program = program_by_code.get(code)
        segments.append(JurisdictionSegment(
            jurisdiction_code=code,
            program_slug=program.attributes.get("program_slug", "") if program else "",
            country_graph_ref=f"country:{code}",
            program_graph_ref=program.node_id if program else "",
            has_register=(code == register_jurisdiction),
        ))
    return tuple(segments)


# ── Pass 2: treaty composition ───────────────────────────────────────────────

def _treaty_compositions(codes: tuple[str, ...]) -> tuple[tuple[TreatyComposition, ...], list[StructureConstraint]]:
    """Attach only treaties the registry actually holds for these
    countries. A multi-jurisdiction set with no treaty coverage at all
    gets a visible treaty_absence constraint — a split shoot without
    co-production status is legal, but the structure must say plainly
    that no treaty backs national treatment across it."""
    compositions: list[TreatyComposition] = []
    constraints: list[StructureConstraint] = []
    ordered = tuple(sorted(codes))

    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            treaty = te.get_bilateral_treaty(a, b)
            if treaty is not None:
                compositions.append(TreatyComposition(
                    treaty_slug=treaty.treaty_slug,
                    kind="bilateral",
                    jurisdiction_codes=(a, b),
                    graph_ref=f"treaty:{treaty.treaty_slug}",
                    cultural_test_required=treaty.cultural_test_required,
                    confidence_tier=treaty.confidence_tier,
                ))
            elif te.is_european_convention_signatory(a) and te.is_european_convention_signatory(b):
                convention = te._MULTILATERAL["european_convention"]
                compositions.append(TreatyComposition(
                    treaty_slug="european_convention",
                    kind="convention_composition",
                    jurisdiction_codes=(a, b),
                    graph_ref="treaty:european_convention",
                    cultural_test_required=convention.cultural_test_required,
                    confidence_tier=convention.confidence_tier,
                ))

    # Collapse repeated compositions of the same instrument (e.g. the
    # European Convention appearing once per country pair in a triple)
    # into one composition covering the union of its pairs' countries.
    by_slug: dict[str, TreatyComposition] = {}
    for comp in compositions:
        existing = by_slug.get(comp.treaty_slug)
        if existing is None:
            by_slug[comp.treaty_slug] = comp
        else:
            by_slug[comp.treaty_slug] = TreatyComposition(
                treaty_slug=comp.treaty_slug,
                kind=comp.kind,
                jurisdiction_codes=tuple(sorted(set(existing.jurisdiction_codes) | set(comp.jurisdiction_codes))),
                graph_ref=comp.graph_ref,
                cultural_test_required=comp.cultural_test_required,
                confidence_tier=comp.confidence_tier,
            )
    compositions = [by_slug[slug] for slug in sorted(by_slug)]

    if len(ordered) > 1 and not compositions:
        constraints.append(StructureConstraint(
            constraint_id=f"CONST-TREATY-ABSENCE-{'-'.join(ordered)}",
            kind="treaty_absence",
            description=(
                f"No co-production treaty covers {ordered} — each jurisdiction's spend "
                "must qualify independently; no national-treatment unlock is available."
            ),
        ))
    return tuple(compositions), constraints


# ── Pass 3: stack composition ────────────────────────────────────────────────

def _stack_compositions(
    codes: tuple[str, ...],
    collection: OpportunityCollection,
) -> tuple[tuple[StackComposition, ...], list[StructureConstraint]]:
    """known_stack opportunities scoped to the participating set become
    StackCompositions; stacking_unknown opportunities become visible
    constraints carrying their LAAE task refs. Stackability is never
    upgraded from unknown to permitted here."""
    code_set = set(codes)
    stacks: list[StackComposition] = []
    constraints: list[StructureConstraint] = []
    for o in sorted(collection.opportunities, key=lambda o: o.opportunity_id):
        if o.opportunity_type != OpportunityType.STACKING:
            continue
        if not set(o.jurisdiction_codes) <= code_set:
            continue
        if o.subtype == "known_stack":
            stacks.append(StackComposition(
                stack_opportunity_id=o.opportunity_id,
                component_graph_refs=o.graph_refs,
                graph_rule_id=o.graph_rule_id,
            ))
        elif o.subtype == "stacking_unknown":
            constraints.append(StructureConstraint(
                constraint_id=f"CONST-{o.opportunity_id}",
                kind="stacking_unknown",
                description=o.description,
                opportunity_id=o.opportunity_id,
                acquisition_task_refs=o.acquisition_task_refs,
            ))
    return tuple(stacks), constraints


# ── Pass 4: fund composition ─────────────────────────────────────────────────

_MULTILATERAL_MEMBERSHIP_CHECKS = (
    ("eurimages", te.is_eurimages_member),
    ("ibermedia", te.is_ibermedia_member),
)


def _fund_compositions(codes: tuple[str, ...], graph: JurisdictionGraph) -> tuple[str, ...]:
    """A fund attaches only when every participating jurisdiction is a
    member of the unlocking multilateral AND the participant count meets
    that treaty's own min_coproducer_countries — both facts read from
    treaty_engine, neither invented. Returns graph fund-node refs, all of
    which must exist in the Jurisdiction Graph."""
    refs: list[str] = []
    for slug, checker in _MULTILATERAL_MEMBERSHIP_CHECKS:
        treaty = te._MULTILATERAL[slug]
        if len(codes) < treaty.min_coproducer_countries:
            continue
        if not all(checker(code) for code in codes):
            continue
        for fund_slug in treaty.fund_unlocks:
            ref = f"fund:{fund_slug}"
            if graph.has_node(ref) and ref not in refs:
                refs.append(ref)
    return tuple(refs)


# ── Passes 5–7: structuring/normalization scoping + constraint resolution ────

def _scoped_opportunities(codes: tuple[str, ...], collection: OpportunityCollection) -> list[Opportunity]:
    """Opportunities whose jurisdiction codes fall entirely within the
    participating set. JURISDICTION-type relocation/comparison
    opportunities are structural inputs to Pass 1, not claims to book, so
    they are only carried when the pair they describe is exactly inside
    the set (which lets their dependents' dependency checks resolve)."""
    code_set = set(codes)
    return [
        o for o in collection.opportunities
        if o.jurisdiction_codes and set(o.jurisdiction_codes) <= code_set
    ]


def _constraints_from_included(included: list[Opportunity]) -> list[StructureConstraint]:
    constraints: list[StructureConstraint] = []
    for o in sorted(included, key=lambda o: o.opportunity_id):
        if o.requires_evidence:
            constraints.append(StructureConstraint(
                constraint_id=f"CONST-EVIDENCE-{o.opportunity_id}",
                kind="evidence",
                description="; ".join(o.required_evidence) or "Evidence required.",
                opportunity_id=o.opportunity_id,
                acquisition_task_refs=o.acquisition_task_refs,
            ))
        for approval in o.required_approvals:
            constraints.append(StructureConstraint(
                constraint_id=f"CONST-APPROVAL-{o.opportunity_id}",
                kind="approval",
                description=approval,
                opportunity_id=o.opportunity_id,
            ))
        if o.authority_score == 0.0:
            constraints.append(StructureConstraint(
                constraint_id=f"CONST-AUTHORITY-{o.opportunity_id}",
                kind="authority",
                description="Terminus is absence of authority (score 0.0) — commitment requires acquired authority.",
                opportunity_id=o.opportunity_id,
                acquisition_task_refs=o.acquisition_task_refs,
            ))
    return constraints


# ── Candidate assembly ───────────────────────────────────────────────────────

def _build_candidate(
    codes: tuple[str, ...],
    collection: OpportunityCollection,
    graph: JurisdictionGraph,
    register: Optional[list[AccountQualification]],
    gross_budget_usd: Optional[float],
    rate: Optional[float],
    grey_areas: Optional[list[GreyAreaItem]],
    delay_weeks: int,
    bridge_rate: float,
) -> ProductionStructureCandidate:
    baseline = collection.baseline_jurisdiction
    register_jurisdiction = baseline if register is not None else None
    known_stacks = [
        o for o in collection.opportunities
        if o.opportunity_type == OpportunityType.STACKING and o.subtype == "known_stack"
    ]

    segments = _jurisdiction_segments(codes, graph, register_jurisdiction)
    treaties, treaty_constraints = _treaty_compositions(codes)
    stacks, stack_constraints = _stack_compositions(codes, collection)
    funds = _fund_compositions(codes, graph)

    scoped = _scoped_opportunities(codes, collection)
    included, excluded_reasons, ledger = _resolve_inclusion(scoped, known_stacks)

    claims = tuple(
        IncentiveClaim(
            claim_key=claim.claim_key,
            opportunity_id=claim.opportunity_id,
            program_slug=next(
                (s.program_slug for s in segments if claim.claim_key.startswith(f"{s.jurisdiction_code}:")),
                "",
            ),
        )
        for claim in ledger.claims
    )

    grey_ids = tuple(
        o.opportunity_id for o in included if o.opportunity_type == OpportunityType.GREY_AREA
    )
    evidence_refs = tuple(sorted({
        ref for o in included for ref in (o.graph_rule_id, o.graph_absence_id) if ref
    }))
    approvals = tuple(sorted({a for o in included for a in o.required_approvals}))
    task_refs = tuple(sorted({t for o in included for t in o.acquisition_task_refs}))

    constraints = tuple(
        sorted(
            list(treaty_constraints) + list(stack_constraints) + _constraints_from_included(included),
            key=lambda c: c.constraint_id,
        )
    )

    # Pricing: only the register-backed jurisdiction's portion is
    # computable, and only when the caller supplied real inputs. The
    # existing engines price it; nothing else is estimated.
    cases: Optional[dict[RiskCase, CaseResult]] = None
    priced_segments = 0
    if (
        register is not None and gross_budget_usd is not None and rate is not None
        and any(s.has_register for s in segments)
    ):
        paths = opportunities_to_structuring_paths(
            included, register=register, rate=rate, jurisdiction_code=baseline,
        )
        result = build_risk_cases(
            register=register, gross_budget_usd=gross_budget_usd, rate=rate,
            structuring_paths=paths, grey_areas=grey_areas or [],
            delay_weeks=delay_weeks, bridge_rate=bridge_rate, jurisdiction_code=baseline,
        )
        cases = result.cases
        priced_segments = sum(1 for s in segments if s.has_register)

    priceable_pct = round(priced_segments / len(segments), 4) if segments else 0.0
    unknown_pct = (
        round(sum(1 for o in included if o.requires_evidence) / len(included), 4)
        if included else 0.0
    )

    # Only JURISDICTION-type (relocation/co-production) upside is summed
    # here — STRUCTURING and GREY_AREA opportunities' estimated_upside_usd
    # is already reflected inside `cases` for the priced (register-backed)
    # portion of this structure (via opportunities_to_structuring_paths()
    # and the grey_areas= input to build_risk_cases()), so including them
    # again here would double-count the already-priced MU portion.
    upside_values = [
        o.estimated_upside_usd for o in included
        if o.estimated_upside_usd is not None and o.opportunity_type == OpportunityType.JURISDICTION
    ]
    informational_upside_usd = round(sum(upside_values), 2) if upside_values else None

    return ProductionStructureCandidate(
        candidate_id=f"PSC-{'-'.join(codes)}",
        label=" + ".join(codes),
        jurisdiction_segments=segments,
        treaty_compositions=treaties,
        stack_compositions=stacks,
        fund_graph_refs=funds,
        incentive_claims=claims,
        included_opportunity_ids=tuple(o.opportunity_id for o in included),
        excluded_opportunity_ids=tuple(sorted(excluded_reasons)),
        exclusion_reasons=excluded_reasons,
        grey_area_opportunity_ids=grey_ids,
        evidence_graph_refs=evidence_refs,
        required_approvals=approvals,
        required_acquisition_task_refs=task_refs,
        constraints=constraints,
        claim_ledger=ledger,
        cases=cases,
        priceable_pct=priceable_pct,
        unknown_pct=unknown_pct,
        informational_upside_usd=informational_upside_usd,
    )


# ── Pass 8: duplicate elimination ────────────────────────────────────────────

def _signature(candidate: ProductionStructureCandidate) -> tuple:
    """Canonical identity of a composed structure: its jurisdiction set,
    booked claims, treaties, funds, and included opportunities. Two
    candidates with identical signatures are the same structure however
    they were generated."""
    return (
        tuple(sorted(candidate.participating_jurisdictions)),
        tuple(sorted(c.claim_key for c in candidate.incentive_claims)),
        tuple(sorted(t.treaty_slug for t in candidate.treaty_compositions)),
        candidate.fund_graph_refs,
        tuple(sorted(candidate.included_opportunity_ids)),
    )


def eliminate_duplicates(
    candidates: list[ProductionStructureCandidate],
) -> tuple[list[ProductionStructureCandidate], dict[str, str]]:
    seen: dict[tuple, str] = {}
    survivors: list[ProductionStructureCandidate] = []
    pruned: dict[str, str] = {}
    for candidate in candidates:
        sig = _signature(candidate)
        if sig in seen:
            pruned[candidate.candidate_id] = f"Duplicate of '{seen[sig]}'."
            continue
        seen[sig] = candidate.candidate_id
        survivors.append(candidate)
    return survivors, pruned


# ── Pass 9: dominance pruning ────────────────────────────────────────────────

def _strictly_dominates(a: ProductionStructureCandidate, b: ProductionStructureCandidate) -> bool:
    """a strictly dominates b iff both are fully priced and a's Net
    Production Cost is strictly lower in ALL FOUR risk cases. Partially
    priced or unpriced candidates are never compared — absence of a price
    is not evidence of inferiority — and equality in any case defeats
    dominance (equal-cost alternatives both survive)."""
    if not (a.is_fully_priced and b.is_fully_priced):
        return False
    return all(a.npc(case) < b.npc(case) for case in RiskCase)


def prune_dominated(
    candidates: list[ProductionStructureCandidate],
) -> tuple[list[ProductionStructureCandidate], dict[str, str]]:
    pruned: dict[str, str] = {}
    survivors: list[ProductionStructureCandidate] = []
    for candidate in candidates:
        dominator = next(
            (
                other for other in candidates
                if other.candidate_id != candidate.candidate_id
                and other.candidate_id not in pruned
                and _strictly_dominates(other, candidate)
            ),
            None,
        )
        if dominator is not None:
            pruned[candidate.candidate_id] = (
                f"Strictly dominated by '{dominator.candidate_id}' across all four risk cases."
            )
        else:
            survivors.append(candidate)
    return survivors, pruned


# ── Top-level composer ───────────────────────────────────────────────────────

def compose_production_structures(
    collection: OpportunityCollection,
    graph: JurisdictionGraph,
    register: Optional[list[AccountQualification]] = None,
    gross_budget_usd: Optional[float] = None,
    rate: Optional[float] = None,
    grey_areas: Optional[list[GreyAreaItem]] = None,
    extra_jurisdiction_sets: Optional[list[tuple[str, ...]]] = None,
    delay_weeks: int = 39,
    bridge_rate: float = 0.08,
) -> CompositionResult:
    """
    Runs all ten passes and returns the surviving candidates,
    deterministically ordered: fully-priced candidates first ascending by
    Risk-Adjusted NPC, then everything else by candidate_id. Pricing of
    the register-backed portion is one build_risk_cases() call per
    candidate — the same inputs, the same math, the same outputs as any
    direct caller of the optimizer.
    """
    sets = _jurisdiction_sets(collection, extra_jurisdiction_sets or [])
    candidates = [
        _build_candidate(
            codes, collection, graph, register, gross_budget_usd, rate,
            grey_areas, delay_weeks, bridge_rate,
        )
        for codes in sets
    ]

    candidates, duplicate_pruned = eliminate_duplicates(candidates)
    candidates, dominance_pruned = prune_dominated(candidates)

    def _order_key(c: ProductionStructureCandidate):
        npc = c.npc(RiskCase.RISK_ADJUSTED)
        return (0, npc, c.candidate_id) if c.is_fully_priced else (1, 0.0, c.candidate_id)

    return CompositionResult(
        baseline_jurisdiction=collection.baseline_jurisdiction,
        passes_run=COMPOSITION_PASSES,
        candidates=sorted(candidates, key=_order_key),
        pruned={**duplicate_pruned, **dominance_pruned},
    )
