"""
production_allocation.py

The account->jurisdiction ALLOCATION model — the single bounded missing
capability identified by the optimizer reconciliation (see
ACCOUNT_TRANSFER_HANDOFF.md / BACKEND_HANDOFF.md optimizer-reconciliation
delta). It partitions every real budget account across a proposed
production structure so that multi-jurisdiction structures can be priced
from one PARTIAL qualification register per jurisdiction instead of the
whole budget being priced once against a single baseline register.

This module composes EXISTING seams rather than inventing new ones:

  - budget accounts come in as the same BudgetLine tuples
    qualification_derivation consumes;
  - the spend-category vocabulary is app.data.program_spend_rules' own
    (the per-account classification the register derivation already
    uses) — a component is derived from it, never from a label guess;
  - stated-location facts (accounts_outside_jurisdiction — e.g. the
    Little Utopia budget's own "PICTURE EDIT: LA" cover-page fact) are
    honored exactly as the register derivation honors them;
  - structuring_advisor.routing_decisions and opportunity
    affected_accounts/movable-spend enter as routing rationale inputs;
  - producer overrides (component routes, account routes, explicit
    percentage splits) are first-class USER_ELECTED assignments.

Hard rules (enforced, tested):
  - every cash-budget dollar is allocated exactly once;
  - no account is silently omitted (an unassignable account makes the
    allocation incomplete, never disappears);
  - no account lands in two jurisdictions unless an EXPLICIT,
    producer-controlled split exists (real sub-lines or an explicit
    percentage set summing to 1.0) — no invented 60/40 heuristics;
  - an incomplete or non-conserving allocation makes the structure
    unpriceable downstream (allocation_pricing excludes it from
    financial ranking and states the exact blockers).

Budget allocation is DERIVED from the production structure
(StructureSpec), never entered as a generic rebate percentage.

No LLM calls. Deterministic and testable.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field

from app.calculators.qualification_derivation import BudgetLine

PRODUCTION_ALLOCATION_VERSION = "1.0.0"


# ── Assignment vocabulary ────────────────────────────────────────────────────

class AssignmentKind(str, enum.Enum):
    FIXED = "fixed"                # location-bound or stated-location fact
    RECOMMENDED = "recommended"    # engine default, producer can re-route
    CONDITIONAL = "conditional"    # valid only if a named requirement resolves
    USER_ELECTED = "user_elected"  # explicit producer override / split


# Component vocabulary, derived from the SAME spend-category vocabulary
# the qualification register already classifies every account with —
# a component describes WHAT the work is (and therefore whether it is
# physically tied to the shoot), never WHERE it currently sits.
COMPONENT_BY_SPEND_CATEGORY: dict[str, str] = {
    "post_production": "post",
    "sound": "post",
    "vfx": "vfx",
    "music": "music",
    "atl_writer": "above_the_line",
    "atl_director": "above_the_line",
    "atl_producer": "above_the_line",
    "atl_cast": "above_the_line",
    "travel": "travel_and_living",
    "lodging": "travel_and_living",
    "insurance": "overhead",
    "completion_bond": "overhead",
    "contingency": "overhead",
    "legal_accounting": "administration",
    "production_service_fees": "administration",
    "finance_costs": "overhead",
    "vessel_marine": "principal_photography",
}
_DEFAULT_COMPONENT = "principal_photography"  # btl_* and anything unmapped

# Components whose work is NOT physically tied to the shoot location —
# the same semantics production_package_intelligence's movable-spend
# hint uses (VFX / music / sound / post). These may be routed.
MOVABLE_COMPONENTS = frozenset({"post", "vfx", "music"})

# Components physically tied to where the camera rolls.
LOCATION_BOUND_COMPONENTS = frozenset({"principal_photography", "travel_and_living"})

# Pseudo-jurisdiction code for spend whose stated location is outside
# every participating jurisdiction (e.g. the budget's own "PICTURE
# EDIT: LA" fact). A real allocation target — the dollars exist and are
# located — but never an incentive segment.
NON_PARTICIPANT_STATED_LOCATION = "US"


def component_for(spend_category: str | None) -> str:
    if spend_category is None:
        return _DEFAULT_COMPONENT
    return COMPONENT_BY_SPEND_CATEGORY.get(spend_category, _DEFAULT_COMPONENT)


# ── Structure specification (the generic legal-structure model) ─────────────
# One spec expresses every supported structure label through the same
# fields — no bespoke calculator per label (single-jurisdiction service
# production, complete relocation, component relocation, split
# production, treaty co-production, majority/minority, multi-party,
# hybrid, anchor-component are all combinations of primary jurisdiction,
# participants, component routes, explicit splits, ownership shares, and
# an optional treaty instrument).

STRUCTURE_TYPES: tuple[str, ...] = (
    "single_country",
    "full_relocation",
    "component_relocation",   # == anchor-component: primary anchor + routed components
    "split_production",
    "treaty_coproduction",
    "majority_minority",
    "multi_party",
    "service_production",
    "hybrid",
)


@dataclass(frozen=True)
class StructureSpec:
    structure_id: str
    structure_type: str  # one of STRUCTURE_TYPES
    label: str
    primary_jurisdiction: str
    participants: tuple[str, ...]                 # ordered, primary first
    incentive_programs: dict[str, str]            # jurisdiction -> program slug (claiming segments only)
    component_routes: dict[str, str] = field(default_factory=dict)   # component -> jurisdiction
    account_routes: dict[str, str] = field(default_factory=dict)     # account_code -> jurisdiction (producer)
    account_splits: dict[str, dict[str, float]] = field(default_factory=dict)  # explicit producer splits
    ownership_shares: dict[str, float] = field(default_factory=dict)  # jurisdiction -> share (0..1)
    treaty_slug: str | None = None
    notes: str = ""

    def __post_init__(self):
        if self.structure_type not in STRUCTURE_TYPES:
            raise ValueError(f"Unknown structure_type '{self.structure_type}' "
                             f"(known: {STRUCTURE_TYPES})")
        if self.primary_jurisdiction not in self.participants:
            raise ValueError("primary_jurisdiction must be among participants")


# ── Allocation records ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class AccountAllocation:
    """One account's (or explicit sub-portion's) assignment to exactly
    one jurisdiction, with full routing provenance.

    line_id traces this assignment back to the exact source BudgetLine it
    was derived from — required because account_code is a classification
    field, not a unique key (real budgets legitimately reuse a code
    across distinct lines), so account_code alone cannot disambiguate
    which source line a given assignment came from."""
    account_code: str
    description: str
    amount_usd: float
    component: str
    jurisdiction_code: str
    assignment_kind: AssignmentKind
    rationale: str                       # why THIS jurisdiction
    governing_decision: str              # which structure decision governs it
    supporting_facts: tuple[str, ...] = ()
    authority: str | None = None
    unresolved_requirements: tuple[str, ...] = ()
    split_pct: float | None = None       # set only on explicit split portions
    line_id: str = ""                    # traces to the source BudgetLine.line_id


@dataclass
class AllocationResult:
    allocation_version: str
    structure_id: str
    structure_type: str
    participants: tuple[str, ...]
    assignments: tuple[AccountAllocation, ...]
    unallocated_account_codes: tuple[str, ...]
    total_allocated_usd: float
    total_budget_lines_usd: float
    conserves: bool                      # every cash dollar allocated exactly once
    duplicate_account_codes: tuple[str, ...]
    notes: tuple[str, ...] = ()

    @property
    def is_complete(self) -> bool:
        return (
            self.conserves
            and not self.unallocated_account_codes
            and not self.duplicate_account_codes
        )

    def allocated_by_jurisdiction(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for a in self.assignments:
            totals[a.jurisdiction_code] = round(
                totals.get(a.jurisdiction_code, 0.0) + a.amount_usd, 2
            )
        return totals

    def account_codes_for(self, jurisdiction_code: str) -> tuple[str, ...]:
        return tuple(sorted({
            a.account_code for a in self.assignments
            if a.jurisdiction_code == jurisdiction_code
        }))


# ── The allocator ────────────────────────────────────────────────────────────

def derive_account_allocation(
    lines: list[BudgetLine],
    spend_category_by_code: dict[str, str],
    spec: StructureSpec,
    stated_outside_accounts: frozenset[str] = frozenset(),
    stated_location_code: str = NON_PARTICIPANT_STATED_LOCATION,
    stated_location_authority: str | None = None,
    routing_rationales: dict[str, str] | None = None,
) -> AllocationResult:
    """
    Partition every cash budget line across the structure.

    Precedence (first match wins, per account):
      1. explicit producer SPLIT (spec.account_splits) — USER_ELECTED;
         percentages must be > 0 and sum to 1.0 (real sub-lines or an
         explicit producer-controlled percentage; never invented here);
      2. explicit producer ROUTE (spec.account_routes) — USER_ELECTED;
      3. component ROUTE (spec.component_routes) for the account's
         component — USER_ELECTED when the route came from a producer
         fact, RECOMMENDED when it came from an engine routing decision
         (routing_rationales carries the provenance text either way);
         routing a component overrides a stated-location fact — it is a
         producer/engine decision to CHANGE the current plan, recorded
         with an unresolved requirement to confirm the change;
      4. stated-location fact (stated_outside_accounts — e.g. "PICTURE
         EDIT: LA") — FIXED to stated_location_code (a non-participant,
         non-incentive segment; dollars are still allocated, exactly once);
      5. location-bound component -> FIXED to the primary (shoot)
         jurisdiction;
      6. everything else -> RECOMMENDED to the primary jurisdiction
         (overhead/administration follow the production SPV domicile;
         movable components default home until routed).

    Memo lines (is_memo=True) are NOT cash budget and are excluded from
    conservation, with a note — never silently dropped.
    """
    routing_rationales = routing_rationales or {}
    assignments: list[AccountAllocation] = []
    unallocated: list[str] = []
    notes: list[str] = []
    # Identity for dedup is the LINE, never the account code — a real budget
    # may legitimately reuse an account code across distinct lines (e.g. a
    # subtotal/header row, or contingency deployed to multiple destinations
    # under one code). `duplicates` therefore only ever fires when the same
    # BudgetLine (same line_id) is passed into `lines` more than once — a
    # genuine caller bug, not a real-world budget fact.
    seen_line_ids: set[str] = set()
    duplicates: list[str] = []

    # Validate explicit splits up front — a malformed split is a caller
    # error, not a silent fallback.
    for code, portions in spec.account_splits.items():
        total_pct = round(sum(portions.values()), 6)
        if abs(total_pct - 1.0) > 1e-6 or any(p <= 0 for p in portions.values()):
            raise ValueError(
                f"Explicit split for account {code} must use positive "
                f"percentages summing to 1.0 (got {portions}) — splits are "
                "producer-controlled, never engine-invented."
            )
        unknown = [j for j in portions if j not in spec.participants
                   and j != stated_location_code]
        if unknown:
            raise ValueError(
                f"Explicit split for account {code} names non-participant "
                f"jurisdiction(s) {unknown}."
            )

    for line in lines:
        if line.line_id in seen_line_ids:
            duplicates.append(line.account_code)
            continue
        seen_line_ids.add(line.line_id)

        if line.is_memo:
            notes.append(
                f"Account {line.account_code} ({line.description}) is a memo "
                "line — not cash budget; excluded from allocation and "
                "conservation, not silently dropped."
            )
            continue

        category = spend_category_by_code.get(line.account_code, line.spend_category)
        component = component_for(category)

        # 1. explicit producer split
        if line.account_code in spec.account_splits:
            for jur, pct in sorted(spec.account_splits[line.account_code].items()):
                assignments.append(AccountAllocation(
                    account_code=line.account_code,
                    line_id=line.line_id,
                    description=line.description,
                    amount_usd=round(line.amount_usd * pct, 2),
                    component=component,
                    jurisdiction_code=jur,
                    assignment_kind=AssignmentKind.USER_ELECTED,
                    rationale=(
                        f"Explicit producer-controlled split: {pct:.0%} of this "
                        f"account's spend is elected to be incurred in {jur}."
                    ),
                    governing_decision=f"account_split:{line.account_code}",
                    supporting_facts=("Producer-supplied split percentage.",),
                    unresolved_requirements=(
                        f"Producer to evidence the {jur} portion with real "
                        "sub-lines or vendor contracts before filing.",
                    ),
                    split_pct=pct,
                ))
            continue

        # 2. explicit producer account route
        if line.account_code in spec.account_routes:
            jur = spec.account_routes[line.account_code]
            if jur not in spec.participants and jur != stated_location_code:
                unallocated.append(line.account_code)
                notes.append(
                    f"Account {line.account_code} routed to non-participant "
                    f"'{jur}' — unallocatable within this structure."
                )
                continue
            assignments.append(AccountAllocation(
                account_code=line.account_code,
                line_id=line.line_id,
                description=line.description,
                amount_usd=line.amount_usd,
                component=component,
                jurisdiction_code=jur,
                assignment_kind=AssignmentKind.USER_ELECTED,
                rationale=f"Explicit producer election: this account is routed to {jur}.",
                governing_decision=f"account_route:{line.account_code}",
                supporting_facts=("Producer-supplied account route.",),
            ))
            continue

        # 3. component route
        if component in spec.component_routes:
            jur = spec.component_routes[component]
            if jur not in spec.participants:
                unallocated.append(line.account_code)
                notes.append(
                    f"Component '{component}' routed to non-participant '{jur}' "
                    f"— account {line.account_code} unallocatable."
                )
                continue
            provenance = routing_rationales.get(
                component,
                f"Component '{component}' is routed to {jur} by this structure.",
            )
            overrides_stated = line.account_code in stated_outside_accounts
            reqs: list[str] = []
            if overrides_stated:
                reqs.append(
                    f"Confirm relocation of {component} work from its currently "
                    f"stated location ({stated_location_code}) to {jur} — the "
                    "budget's own stated plan is being changed by this structure."
                )
            if component not in MOVABLE_COMPONENTS:
                reqs.append(
                    f"Component '{component}' is location-bound by default — "
                    f"routing it to {jur} requires the physical work plan to move."
                )
            kind = (AssignmentKind.USER_ELECTED
                    if provenance.startswith("Producer")
                    else AssignmentKind.RECOMMENDED)
            assignments.append(AccountAllocation(
                account_code=line.account_code,
                line_id=line.line_id,
                description=line.description,
                amount_usd=line.amount_usd,
                component=component,
                jurisdiction_code=jur,
                assignment_kind=kind,
                rationale=provenance,
                governing_decision=f"component_route:{component}",
                supporting_facts=(
                    ("Budget cover page states current location "
                     f"{stated_location_code} for this account.",)
                    if overrides_stated else ()
                ),
                authority=stated_location_authority if overrides_stated else None,
                unresolved_requirements=tuple(reqs),
            ))
            continue

        # 4. stated-location fact
        if line.account_code in stated_outside_accounts:
            assignments.append(AccountAllocation(
                account_code=line.account_code,
                line_id=line.line_id,
                description=line.description,
                amount_usd=line.amount_usd,
                component=component,
                jurisdiction_code=stated_location_code,
                assignment_kind=AssignmentKind.FIXED,
                rationale=(
                    "The production's own budget states this work is incurred "
                    f"in {stated_location_code} — allocated to that stated "
                    "location; earns no incentive in this structure."
                ),
                governing_decision="stated_location_fact",
                supporting_facts=(
                    "accounts_outside_jurisdiction production fact "
                    "(budget cover page / account name).",
                ),
                authority=stated_location_authority,
            ))
            continue

        # 5. location-bound -> primary
        if component in LOCATION_BOUND_COMPONENTS:
            assignments.append(AccountAllocation(
                account_code=line.account_code,
                line_id=line.line_id,
                description=line.description,
                amount_usd=line.amount_usd,
                component=component,
                jurisdiction_code=spec.primary_jurisdiction,
                assignment_kind=AssignmentKind.FIXED,
                rationale=(
                    f"'{component}' is physically tied to the shoot — it is "
                    f"incurred where the camera rolls ({spec.primary_jurisdiction})."
                ),
                governing_decision=f"primary_shoot_location:{spec.primary_jurisdiction}",
            ))
            continue

        # 6. default -> primary (recommended)
        assignments.append(AccountAllocation(
            account_code=line.account_code,
            line_id=line.line_id,
            description=line.description,
            amount_usd=line.amount_usd,
            component=component,
            jurisdiction_code=spec.primary_jurisdiction,
            assignment_kind=AssignmentKind.RECOMMENDED,
            rationale=(
                f"'{component}' follows the production entity's domicile "
                f"({spec.primary_jurisdiction}) absent a routing decision."
                if component in ("overhead", "administration", "above_the_line")
                else
                f"Movable component '{component}' defaults to the primary "
                f"jurisdiction ({spec.primary_jurisdiction}); a routing "
                "decision may re-route it."
            ),
            governing_decision=f"default_domicile:{spec.primary_jurisdiction}",
        ))

    cash_lines_total = round(sum(l.amount_usd for l in lines if not l.is_memo), 2)
    allocated_total = round(sum(a.amount_usd for a in assignments), 2)
    conserves = abs(allocated_total - cash_lines_total) <= 0.01 and not unallocated

    return AllocationResult(
        allocation_version=PRODUCTION_ALLOCATION_VERSION,
        structure_id=spec.structure_id,
        structure_type=spec.structure_type,
        participants=spec.participants,
        assignments=tuple(assignments),
        unallocated_account_codes=tuple(sorted(unallocated)),
        total_allocated_usd=allocated_total,
        total_budget_lines_usd=cash_lines_total,
        conserves=conserves,
        duplicate_account_codes=tuple(sorted(set(duplicates))),
        notes=tuple(notes),
    )
