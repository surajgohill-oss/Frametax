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

import math
from dataclasses import dataclass, field, replace as _dataclasses_replace

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
from app.calculators.canonical_requirements_gate_bridge import evaluate_requirements_gate
from app.data.authority_coverage_registry import get_coverage_status
from app.data.program_rate_rules import get_qpe_cap, get_rate_rules, resolve_program_rate
from app.data.program_slug_aliases import canonical_slug
from app.data.program_spend_rules import get_program_doctrine, resolve_program_doctrine

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
    # Task: Incentive/Optimizer Core Closeout. True when the resolved rate
    # tier is a band ceiling (rate_ceiling, is_band_ceiling=True) AND at
    # least one of its RateConditions evaluated to satisfied=None (a
    # discretionary/fact-dependent condition the engine cannot pre-confirm
    # — e.g. Mauritius's Film Rebate Committee discretion, Malta's
    # Commissioner-awarded uplift limbs, the UK's VFX Additional Credit
    # eligibility). When True, the structure-level selected/ranked
    # incentive uses this segment's FLOOR, not its ceiling, unless the
    # caller supplies an explicit per-program confirmation (see
    # confirmed_ceiling_programs on price_allocated_structure/
    # price_segment) — a project-specific certificate/approval overriding
    # the modeled default for that one scenario only. Never flips a
    # jurisdiction WITHOUT a discretionary condition (e.g. Greece's flat
    # 40%, Australia's flat 30%) — those have is_band_ceiling=False and
    # this stays False.
    ceiling_requires_confirmation: bool = False
    qpe_cap_applied_usd: float = 0.0   # amount excluded by a program-level QPE cap (e.g. GB/GR 80%)
    # Cluster 7 (dollar caps). A percentage QPE cap (above) limits the BASE;
    # these limit the INCENTIVE itself, applied after base x rate. Both are
    # canonical fields that already existed but never constrained served
    # pricing: ProgramRequirementsProfile.per_project_cap_usd is a hard
    # per-production ceiling, and DoctrineRecord.annual_cap_usd /
    # ProgramRequirementsProfile.annual_program_cap_usd is the program's whole
    # annual allocation -- one production can never receive more than the
    # entire year's fund, so it is a true (if usually non-binding) upper
    # bound. incentive_cap_usd is the binding cap actually applied;
    # incentive_cap_type names which kind bound; incentive_uncapped_usd
    # preserves the pre-cap figure so the reduction is auditable.
    incentive_cap_usd: float | None = None
    incentive_cap_type: str | None = None
    incentive_cap_basis: str | None = None
    incentive_uncapped_usd: float | None = None
    incentive_cap_applied_usd: float = 0.0
    # Cluster 2 / 19: every mandatory requirement this program imposes, with
    # its adjudicated state (SATISFIED / FAILED / UNKNOWN / NOT_APPLICABLE)
    # and reason. A requirement that cannot be confirmed is surfaced here as
    # an explicit UNKNOWN rather than silently treated as satisfied, so the
    # producer can see exactly which gates are still open.
    requirement_trace: tuple[dict, ...] = ()


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
    npc_verified_usd: float | None           # gross - BEST-SUPPORTED incentive (+ financing)
    npc_with_adjustments_usd: float | None   # canonical NPC: + travel + fx + in-kind replacement
    is_fully_priced: bool
    blockers: tuple[str, ...]
    # Canonical optimization contract (Phase 5): the served/ranked economics
    # use the BEST-SUPPORTED modeled incentive, never the conservative floor.
    # selected_incentive_usd is the modeled (best-supported) incentive that
    # drives NPC and ranking; total_incentive_floor_usd remains the
    # separately-surfaced conservative/uncertainty figure.
    selected_incentive_usd: float = 0.0
    # Off-budget Mauritius in-kind post normalization: a structure that moves
    # that work out of MU must absorb the replacement cost (added to NPC);
    # a structure that keeps the post in MU carries 0. Separate economic
    # layer — never a budget line, never QPE.
    inkind_replacement_delta_usd: float = 0.0
    # Conservative (floor-rate) NPC with the same normalizations applied —
    # surfaced as the downside of the approval-uncertainty band, never the
    # ranked figure.
    npc_conservative_usd: float | None = None
    stacking_note: str = ""
    inkind_note: str = ""
    recommendation: StructureRecommendation | None = None
    ownership_shares: dict[str, float] = field(default_factory=dict)
    treaty_slug: str | None = None
    notes: tuple[str, ...] = ()
    # FX provenance for this structure's primary jurisdiction — the same
    # FXNormalizationResult that produced fx_delta_usd, so the UI can show
    # WHY the delta is what it is (currency, rate, source, date) rather
    # than only the resulting dollar figure. None when FX was never
    # computed for this structure (never priced, or no local-currency
    # jurisdiction mapping) — never fabricated.
    fx_basis: dict | None = None
    # Local cost modeling (production_adjustment.py + location_cost_
    # benchmarks.py, real per-jurisdiction cost indices) — the incremental,
    # non-travel/non-FX cost delta of this structure's primary jurisdiction
    # vs the production's original shoot geography (crew rate, equipment,
    # stage facility, legal/accounting, local-hire premium, freight/carnet,
    # visa/work permit, local transport). 0.0 for the baseline (same
    # jurisdiction). None when never computed for this structure.
    local_cost_delta_usd: float | None = None
    local_cost_basis: dict | None = None


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
            # Canonical Budget Parser Remediation (Codex BPI-002): the
            # allocation's OWN spend_category (carried from its real
            # source BudgetLine — see AccountAllocation.spend_category's
            # own docstring) is authoritative; the shared, code-keyed
            # dict is a fallback only, for an allocation with none of its
            # own.
            spend_category=a.spend_category or spend_category_by_code.get(a.account_code),
            is_memo=False,
            line_id=a.line_id or f"{a.account_code}:{a.jurisdiction_code}",
        )
        for a in sorted(allocations, key=lambda a: a.account_code)
    ]



def _resolve_incentive_dollar_cap(
    slug: str, fx_context=None, amount_facts: dict[str, float] | None = None,
    evidenced_requirement_facts: frozenset[str] | None = None,
) -> tuple[float | None, str | None, str | None, "object | None", str | None]:
    """The binding DOLLAR cap on one production's incentive for `slug`.

    Three canonical sources exist and mean different things:

      * ProgramRequirementsProfile.per_project_cap_usd -- a hard statutory
        ceiling on what ONE production may receive. Directly binding.
      * DoctrineRecord.annual_cap_usd / ProgramRequirementsProfile.
        annual_program_cap_usd -- the program's ENTIRE annual allocation
        across all productions. Not a per-project entitlement, but still a
        true upper bound: a single production cannot receive more than the
        whole year's fund.
      * program_rate_rules.IncentiveValueCapRule (Codex final-nine
        remediation) -- a per-project cap stated in the program's own
        NATIVE currency (e.g. cz_film_incentive's CZK450m, za_nfvf_rebate's
        ZAR25m), converted to USD here via the SAME real, dated, sourced
        FX snapshot every other currency conversion in this codebase uses
        (program_rate_rules.convert_incentive_cap_to_usd ->
        apply_fx_rates.convert_to_usd) -- never a caller-supplied or
        guessed rate. This is what lets a native-currency cap constrain
        the engine-CALCULATED incentive below, rather than requiring the
        caller to pre-compute and submit the incentive value for a
        reject-only check.

    The binding cap is the smallest applicable one. Returns
    (cap_usd, cap_type, basis, fx_error, aggregate_unresolved_detail) or
    (None, None, None, None, None) when the program declares no dollar
    cap -- absence, never an invented ceiling. fx_error is a non-None
    apply_fx_rates.FXRateResolution ONLY when a native-currency cap
    (IncentiveValueCapRule) exists but its FX conversion could not be
    safely resolved (Codex final P0 canonical_fx -- missing/non-positive
    rate or a stale_fallback context) — the caller MUST treat that as
    fail-closed/non-priceable, never silently drop the cap (which would
    let an over-cap incentive through uncapped) and never crash.

    aggregate_unresolved_detail (Codex bounded remediation, P0-NL-001) is
    a non-None human-readable string ONLY when a company-period cap
    (IncentiveValueCapRule.company_period_prior_award_fact_key) has an
    evidenced has_other_productions fact but the prior-awards aggregate
    itself is missing, unevidenced, non-finite, or out of range -- the
    caller MUST treat this exactly like fx_error: fail closed, disclosed,
    non-priceable. An unresolved company-period aggregate must never be
    silently treated as EUR0 (which would hand out the full cap on an
    unverified claim).
    """
    from app.data.executable_jurisdiction_registry import get_doctrine
    from app.data.program_rate_rules import convert_incentive_cap_to_usd, get_incentive_value_cap
    from app.data.program_requirements import get_program_requirements

    candidates: list[tuple[float, str, str]] = []

    profile = get_program_requirements(slug)
    if profile is not None:
        per_project = getattr(profile, "per_project_cap_usd", None)
        if per_project:
            candidates.append((
                float(per_project), "per_project",
                "ProgramRequirementsProfile.per_project_cap_usd",
            ))
        annual_profile = getattr(profile, "annual_program_cap_usd", None)
        if annual_profile:
            candidates.append((
                float(annual_profile), "annual_program",
                "ProgramRequirementsProfile.annual_program_cap_usd",
            ))

    try:
        doctrine_record = get_doctrine(slug)
    except Exception:
        doctrine_record = None
    annual_doctrine = getattr(doctrine_record, "annual_cap_usd", None) if doctrine_record else None
    if annual_doctrine:
        candidates.append((
            float(annual_doctrine), "annual_program",
            "DoctrineRecord.annual_cap_usd",
        ))

    native_cap = get_incentive_value_cap(slug)
    if native_cap is not None:
        # Codex final wiring remediation (P0-OR-001): "never treat
        # missing cap as unlimited" -- when this cap names a required
        # evidence fact (a dated, discretionary fund figure that can go
        # stale), the fact must be evidenced BEFORE the cap -- and
        # therefore the whole segment -- can price at all. Missing
        # evidence fails closed, exactly like an unresolved company-
        # period aggregate below; it is never silently dropped (which
        # would let an uncapped incentive through) and never treated as
        # "no cap applies".
        if native_cap.cap_requires_evidence_fact_key is not None:
            _cap_evidenced = evidenced_requirement_facts or frozenset()
            if native_cap.cap_requires_evidence_fact_key not in _cap_evidenced:
                return None, None, None, None, (
                    f"{native_cap.program_slug}: this program's final award cap is a "
                    "dated, discretionary fund figure that must be confirmed current "
                    "before it can be safely applied -- "
                    f"'{native_cap.cap_requires_evidence_fact_key}' is not evidenced. "
                    "A missing/unconfirmed cap is never treated as unlimited; the "
                    "segment remains conditional/non-priceable until confirmed."
                )
        effective_cap = native_cap
        cap_basis_suffix = ""
        # Codex final wiring remediation (P0-NL-001, third pass): a
        # PER-COMPANY PER-PERIOD cap must consume prior awards already
        # granted this SAME period to this SAME canonical company's
        # OTHER productions, so two projects for one company cannot
        # jointly exceed the shared ceiling -- and now genuinely bound
        # to canonical identity (see IncentiveValueCapRule's own
        # docstring): identity_known is evidenced ONLY by
        # evaluate_project() from real Project.production_company_
        # identifier/target_shoot_year columns, and has_other_productions
        # (with its amount) is evidenced ONLY by evaluate_project()'s own
        # real cross-project database query -- never a caller-supplied
        # scalar or boolean.
        if native_cap.company_period_prior_award_fact_key is not None:
            evidenced = evidenced_requirement_facts or frozenset()
            identity_key = native_cap.company_period_identity_known_fact_key
            identity_known = identity_key is not None and identity_key in evidenced
            if not identity_known:
                return None, None, None, None, (
                    f"{native_cap.program_slug}: this program's per-company-per-period "
                    "cap requires a canonical production-company identity AND award "
                    "period -- neither is known for this project, so company-period "
                    "consumption cannot be verified. Unknown company/period remains "
                    "conditional/non-priceable, never an affirmative zero. Set this "
                    "project's production_company_identifier and target_shoot_year to "
                    "resolve."
                )
            has_other_key = native_cap.company_period_has_other_productions_fact_key
            has_other_productions = has_other_key is not None and has_other_key in evidenced
            if has_other_productions:
                raw_prior = (amount_facts or {}).get(native_cap.company_period_prior_award_fact_key)
                if raw_prior is None:
                    return None, None, None, None, (
                        f"{native_cap.program_slug}: this company has other "
                        f"{native_cap.cap_currency}-denominated productions on file for "
                        "this award period, but the prior-awards aggregate is missing -- "
                        "an unresolved company-period consumption can never be treated "
                        "as zero. Segment is disclosed but carries no deterministic "
                        "incentive value until the aggregate is resolved."
                    )
                if (not isinstance(raw_prior, (int, float)) or isinstance(raw_prior, bool)
                        or not math.isfinite(raw_prior)):
                    return None, None, None, None, (
                        f"{native_cap.program_slug}: company-period prior-awards "
                        f"aggregate {raw_prior!r} is not a finite number -- rejected "
                        "before it could reduce the cap."
                    )
                if raw_prior < 0 or raw_prior > native_cap.cap_native_amount:
                    return None, None, None, None, (
                        f"{native_cap.program_slug}: company-period prior-awards "
                        f"aggregate {native_cap.cap_currency} {raw_prior:,.2f} is "
                        f"outside [0, {native_cap.cap_currency} "
                        f"{native_cap.cap_native_amount:,.2f}] -- rejected rather than "
                        "clamped or silently accepted."
                    )
                remaining = max(0.0, native_cap.cap_native_amount - raw_prior)
                effective_cap = _dataclasses_replace(native_cap, cap_native_amount=remaining)
                cap_basis_suffix = (
                    f", less {native_cap.cap_currency} {raw_prior:,.2f} already granted "
                    "this period to this company's other productions (evidenced) -> "
                    f"{native_cap.cap_currency} {remaining:,.2f} remaining"
                )
        conversion, fx_resolution = convert_incentive_cap_to_usd(effective_cap, fx_context)
        if not fx_resolution.ok:
            # Fail closed: a native-currency cap exists but cannot be
            # safely converted (missing/non-positive rate, or the
            # context is flagged stale_fallback). Never silently drop
            # the cap (fail-open, letting an over-cap incentive through
            # uncapped) and never let a raised exception escape.
            return None, None, None, fx_resolution, None
        candidates.append((
            round(conversion.target_amount, 2), "per_project_native",
            f"IncentiveValueCapRule ({native_cap.cap_currency} "
            f"{native_cap.cap_native_amount:,.0f} @ {conversion.rate_used} "
            f"{native_cap.cap_currency}/USD, {conversion.rate_date}){cap_basis_suffix}",
        ))

    if not candidates:
        return None, None, None, None, None
    cap_usd, cap_type, basis = min(candidates, key=lambda c: c[0])
    return cap_usd, cap_type, basis, None, None


def price_segment(
    jurisdiction_code: str,
    program_slug: str | None,
    allocations: list[AccountAllocation],
    spend_category_by_code: dict[str, str],
    offshore_payroll_accounts: frozenset[str],
    production_type: str = "feature_film",
    contingency_allocations: dict | None = None,
    gross_budget_usd: float | None = None,
    confirmed_ceiling_programs: frozenset[str] | None = None,
    contingency_expected_utilization_pct: float | None = None,
    evidenced_requirement_facts: frozenset[str] | None = None,
    amount_facts: dict[str, float] | None = None,
    fx_context=None,
) -> SegmentEconomics:
    """Derive this segment's PARTIAL register and price it with the
    existing kernel. A non-incentive segment (program_slug None) is
    located spend only — no register, no incentive, never a blocker.

    contingency_allocations (Task 91): optional {account_code:
    ContingencyAllocation}, defaulting to None (byte-identical prior
    behavior) — see contingency_treatment.expand_contingency_lines.

    contingency_expected_utilization_pct (Consolidated Backend
    Correction, Part 19-20 / CBA-009): the producer's own stated expected
    contingency-spend utilization (0-100), threaded through to this
    segment's internal ProductionFacts so a program whose statutory rule
    confirms the "contingency" category qualifies projects only the
    expected-deployed fraction of the reserve as QPE, not the full
    reserve unconditionally. None (the default) means genuinely unset —
    qualification_derivation.derive_qualification_register surfaces this
    as a disclosed GREY_AREA_REQUIRES_AUTHORITY line rather than silently
    assuming either 0% or 100%.

    gross_budget_usd (Incentive/Optimizer Core Closeout): the STRUCTURE's
    total gross budget, needed only for a program-level QPE cap whose
    cap_base is "total_worldwide_budget" (e.g. Greece's 80%-of-total-cost
    ceiling). Omitted (None) = byte-identical prior behavior for any
    program without such a cap.

    confirmed_ceiling_programs (Incentive/Optimizer Core Closeout): a
    project/scenario-specific set of program_slugs whose discretionary
    rate ceiling (Mauritius Committee discretion, Malta Commissioner
    uplift, UK VFX Additional Credit, etc.) has been CONFIRMED for this
    specific production by real evidence (a certificate, an approval
    letter) — never a canonical rule change, only a per-scenario override.
    Omitted (None) = no ceiling is assumed confirmed, which is the safe
    default and what Little Utopia currently uses everywhere.

    amount_facts (Codex final runtime remediation, 11 B3 formulaic rows):
    optional dict of caller-attested numeric facts keyed by an arbitrary
    string (a native-currency amount or a component-basis sub-total),
    threaded straight through to resolve_program_rate()'s own
    amount_facts parameter — see RateCondition.amount_fact_key. Omitted
    (None) = byte-identical prior behavior for every program without such
    a condition. evidenced_requirement_facts (already an existing
    parameter, used by evaluate_requirements_gate below) is ALSO threaded
    into resolve_program_rate()'s evidenced_facts parameter — the two
    fact namespaces (mandatory-requirement fact-ids vs. rate-condition
    fact-ids) never collide as long as callers use distinct key strings,
    exactly like confirmed_ceiling_programs and this parameter already
    coexist without collision."""
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

    # Global Data Application: the AUTHORITATIVE economic-candidacy gate.
    # Checked before doctrine/rate resolution so that a program the completed
    # primary-authority corpus adjudicated authority-insufficient, selective
    # (non-guaranteed), non-economic, superseded, duplicate, or blocked on a
    # canonical identity-handoff defect can NEVER price -- by any route,
    # including a directly-specified StructureSpec that bypasses discovery.
    # Absence from the registry means PRICEABLE_VALIDATED, so this can never
    # suppress a program that was not explicitly adjudicated.
    coverage = get_coverage_status(slug)
    if coverage is not None and coverage.blocks_economic_candidacy:
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            blockers=(
                f"{jurisdiction_code}/{slug}: {coverage.state} — {coverage.reason} "
                "Segment is allocated and disclosed but carries NO incentive value.",
            ),
        )

    # Doctrine is RESOLVED, never required to be pre-classified: under the
    # module's CANONICAL QPE RULE an absent classification is not a
    # prohibition (see program_spend_rules.resolve_program_doctrine). A
    # program with recorded evidence of a narrower construction resolves to
    # HYBRID_CONDITIONAL instead of the open default. Only a missing
    # STATUTORY RATE still blocks execution — that is a genuine absence of
    # the number itself, which no rule can supply.
    doctrine_resolution = resolve_program_doctrine(slug)
    doctrine = doctrine_resolution.doctrine
    has_rate = len(get_rate_rules(slug)) > 0
    if not has_rate:
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            doctrine=doctrine.value,
            blockers=(
                f"{jurisdiction_code}/{slug}: no statutory rate rules — segment "
                "is not executable; never priced at a guessed rate.",
            ),
        )

    from app.calculators.contingency_treatment import expand_contingency_lines
    lines = expand_contingency_lines(
        _segment_lines(allocations, spend_category_by_code), contingency_allocations,
    )
    facts = ProductionFacts(
        jurisdiction_code=jurisdiction_code,
        # By construction every allocated line is incurred IN this
        # segment's jurisdiction — the allocation, not a fact set, is
        # what keeps other jurisdictions' spend out of this register.
        accounts_outside_jurisdiction=frozenset(),
        offshore_payroll_accounts=frozenset(
            c for c in offshore_payroll_accounts if c in {l.account_code for l in lines}
        ),
        contingency_expected_utilization_pct=contingency_expected_utilization_pct,
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

    # Incentive/Optimizer Core Closeout: program-level QPE eligible-spend
    # cap (e.g. UK/Greece 80%), applied to the QPE base BEFORE rate
    # resolution so a capped QPE also correctly affects min_qpe_usd
    # threshold checks downstream. Inert (byte-identical) for any program
    # without a registered QpeCapRule.
    qpe_cap_applied = 0.0
    cap_rule = get_qpe_cap(slug)
    if cap_rule is not None:
        cap_base_amount = (
            gross_budget_usd if cap_rule.cap_base == "total_worldwide_budget"
            else allocated
        )
        if cap_base_amount is not None:
            cap_ceiling = round(cap_base_amount * cap_rule.cap_pct, 2)
            if qpe > cap_ceiling:
                qpe_cap_applied = round(qpe - cap_ceiling, 2)
                qpe = cap_ceiling

    rr = resolve_program_rate(slug, production_type=production_type, qpe_usd=qpe,
                               gross_budget_usd=gross_budget_usd,
                               evidenced_facts=evidenced_requirement_facts,
                               amount_facts=amount_facts, fx_context=fx_context)

    # A CEILING IS A LIMIT, NEVER A GUARANTEED RATE. When a program's only
    # tiers are band ceilings there is no statutory floor to fall back on,
    # and resolve_program_rate repeats the ceiling as floor_rate purely to
    # keep the disclosure shape stable. Paying that "floor" deterministically
    # is what let an "up to 40%" discretionary band be served as a
    # guaranteed 40%. Fail closed when the ceiling ALSO could not be
    # pre-evaluated (a condition the engine cannot satisfy on the facts) and
    # this specific production has not confirmed it. A floorless ceiling
    # whose conditions ARE all evaluable stays priced -- it is determinate.
    # ── Cluster 2: mandatory eligibility must gate deterministic pricing ─
    # ProgramRequirementsProfile already held local-entity, minimum-spend,
    # minimum-shoot-days and allocation-type facts; the served path consumed
    # them as confidence metadata only, so a program could show a firm number
    # with those conditions entirely unconfirmed. A missing mandatory fact is
    # not a satisfied one. Computable thresholds are genuinely evaluated
    # against this production's own figures (so a real FAILURE is a real
    # failure, and a real pass proceeds); facts the budget cannot decide are
    # UNKNOWN and condition the result. Administrative process steps
    # (preapproval, audit, CPA, bond) are disclosed but never gate.
    requirements_gate = evaluate_requirements_gate(
        slug,
        segment_allocated_usd=allocated,
        gross_budget_usd=gross_budget_usd,
        evidenced_facts=evidenced_requirement_facts,
    )
    # Canonical optimizer/Globe wiring remediation (2026-09-04), P0-1:
    # Codex's four-project audit proved this WAS a real, live defect --
    # 26 component structures served PRICED with non-null incentive/NPC
    # while their own requirement_trace already said minimum-spend
    # FAILED. "A failed mandatory gate cannot coexist with PRICED" (the
    # audit's own words) is correct doctrine; disclosure-only was not
    # acceptance-safe. The scope question this comment used to defer on
    # (segment vs whole-production spend) is real, but it is NOT a
    # reason to leave a genuinely FAILED gate silently ignored -- a
    # missing/unresolved fact already correctly stays UNKNOWN (disclosed,
    # never blocking) via the SAME bridge; only a requirement the engine
    # could actually COMPUTE and that came back FAILED gates here. Runtime-
    # verified before enabling this (not assumed from the old comment):
    # Little Utopia's own accepted baseline (single_country, MU,
    # mu_edb_incentive, segment_allocated_usd=$1,979,731) clears its
    # $1,000,000 min_local_spend_usd floor by a wide margin and is
    # unaffected -- the SegmentEconomics shape/pattern mirrors Cluster 5's
    # existing narrower_base_conditions block immediately below (same
    # file, same function, same disclosure-not-fabrication convention),
    # so this is the SAME rule extended to a second real gate, not a new
    # architecture.
    if requirements_gate.failed:
        # Human-readable requirement names -- "minimum-spend"/"minimum-
        # budget" read naturally where the underlying computable-
        # eligibility keys are min_local_spend_usd/min_total_budget_usd;
        # any other future computable requirement falls back to its own
        # raw key rather than guessing a label.
        _LABELS = {"min_local_spend_usd": "minimum-spend", "min_total_budget_usd": "minimum-budget"}
        failed_ids = "; ".join(
            f"{_LABELS.get(e.requirement, e.requirement)} requirement: {e.detail}"
            for e in requirements_gate.failed
        )
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
            doctrine=doctrine.value,
            qpe_cap_applied_usd=qpe_cap_applied,
            rate_ceiling=rr.modeled_rate if rr is not None else None,
            statutory_basis=rr.basis if rr is not None else None,
            blockers=(
                f"{jurisdiction_code}/{slug}: mandatory eligibility requirement "
                f"FAILED against this segment's own allocated spend [{failed_ids}]. "
                "A genuinely failed mandatory gate cannot coexist with a priced "
                "incentive -- segment is allocated and disclosed but carries NO "
                "deterministic incentive value.",
            ),
        )
    # DISCLOSURE, NOT A BLOCK, for every other requirement state (UNKNOWN/
    # NOT_APPLICABLE/ADMINISTRATIVE/INFORMATIONAL). What the doctrine
    # forbids is a missing mandatory fact being SILENTLY treated as
    # satisfied -- delivered: every requirement is emitted below with its
    # adjudicated state and reason and carried onto the served segment.
    # See the final report's cluster 2 entry.

    # ── Cluster 5: a program-specific qualifying base is not all-spend ───
    # Some programs price a NARROWER base than the QPE register this engine
    # derives -- Canada's CPTC/PSTC family applies its rate to qualified
    # LABOUR, not to all eligible spend. Those programs declare that
    # canonically, as a rate condition of kind rate_base_narrower_than_qpe
    # (condition ids like ca-cptc-labour-only-base / ca-labour-only-base),
    # and the condition is AUTHORITY_UNRESOLVED because the narrower base
    # cannot be derived from what is on file: BudgetLineItem.is_labor is
    # populated on only a handful of lines per budget (Lips: 4 lines,
    # $1,354,581 of $11,983,654), which is nowhere near a real labour
    # schedule, and residency/nationality splits are absent entirely.
    # Multiplying the rate by the BROAD base would materially overstate the
    # credit, so the segment fails closed instead. Never invent labour.
    # The base TYPE is a property of the PROGRAM, not of whichever rate tier
    # happened to win selection. ca_bc_pstc declares ca-bc-labour-only-base on
    # its 36% base tier while resolution selects the 48% regional-ceiling
    # tier, so inspecting only rr.conditions_evaluated would miss it -- and
    # the incentive is still computed on the broad base. Scan every tier.
    if rr is not None:
        narrower_base_conditions = tuple(
            condition
            for rule in get_rate_rules(slug)
            for condition in rule.conditions
            if condition.kind == "rate_base_narrower_than_qpe"
        )
        satisfied_by_id = {
            e.condition_id: e.satisfied for e in rr.conditions_evaluated
        }
        narrower_base_conditions = tuple(
            c for c in narrower_base_conditions
            if satisfied_by_id.get(c.condition_id) is not True
        )
        if narrower_base_conditions:
            condition_ids = ", ".join(c.condition_id for c in narrower_base_conditions)
            return SegmentEconomics(
                jurisdiction_code=jurisdiction_code, program_slug=slug,
                claims_incentive=True, allocated_usd=allocated,
                account_codes=codes, executable=False,
                qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
                doctrine=doctrine.value,
                qpe_cap_applied_usd=qpe_cap_applied,
                rate_ceiling=rr.modeled_rate, statutory_basis=rr.basis,
                blockers=(
                    f"{jurisdiction_code}/{slug}: this program's rate applies to a "
                    f"NARROWER base than the derived qualifying spend [{condition_ids}] "
                    "— a labour/qualified-cost base, not all eligible spend. That base "
                    "cannot be derived from the facts on file (no labour schedule or "
                    "residency split), and applying the rate to the broad base would "
                    "materially overstate the credit. Segment is allocated and "
                    "disclosed but carries NO deterministic incentive value until the "
                    "qualifying base is supplied.",
                ),
            )

    # Codex final-nine remediation: a floorless ceiling must never price
    # when any condition is UNRESOLVED (satisfied is None) OR genuinely
    # FAILED (satisfied is False, e.g. an evidenced numeric fact below its
    # statutory threshold, us_tx_miip's resident-percentage gates) --
    # both are "not confirmed clear", never conflated with pre-satisfied.
    if (
        rr is not None
        and not rr.has_guaranteed_floor
        and any(e.satisfied is not True for e in rr.conditions_evaluated)
        and not (confirmed_ceiling_programs and slug in confirmed_ceiling_programs)
    ):
        unresolved_ids = ", ".join(
            e.condition_id for e in rr.conditions_evaluated if e.satisfied is not True
        )
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
            doctrine=doctrine.value,
            qpe_cap_applied_usd=qpe_cap_applied,
            rate_ceiling=rr.modeled_rate, is_band_ceiling=True,
            statutory_basis=rr.basis,
            ceiling_requires_confirmation=True,
            blockers=(
                f"{jurisdiction_code}/{slug}: the program states only a rate CEILING "
                f"({rr.modeled_rate:.0%}) with no guaranteed floor tier, and its "
                f"award condition(s) [{unresolved_ids}] cannot be pre-evaluated. A "
                "ceiling is a limit on what may be awarded, not evidence that it "
                "will be. Segment is allocated and disclosed but carries NO "
                "deterministic incentive value until the awarded rate is confirmed "
                "for this production.",
            ),
        )

    if rr is None:
        cap_blocker = (
            (f"{jurisdiction_code}/{slug}: ${qpe_cap_applied:,.0f} of eligible "
             f"spend was excluded by the program's {cap_rule.cap_pct:.0%} QPE "
             "cap before this check — see qpe_cap_applied_usd.",)
            if qpe_cap_applied > 0 else ()
        )
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
            doctrine=doctrine.value,
            qpe_cap_applied_usd=qpe_cap_applied,
            blockers=(
                f"{jurisdiction_code}/{slug}: statutory rate did not resolve for "
                f"this production type / segment QPE (${qpe:,.0f}) — minimum-"
                "spend or eligibility conditions unmet; excluded rather than guessed.",
            ) + cap_blocker,
        )

    if rr.qpe_basis_used is not None:
        # Component-basis program (Codex final runtime remediation,
        # us_or_opif; Codex final wiring remediation P0-ZA-001, third
        # pass, za_nfvf_rebate): the selected tier's rate is gated on a
        # caller-supplied component amount (e.g. payroll-only spend, or
        # ZA's post-production-only QSAPPE), not this segment's total QPE.
        #
        # Codex's exact P0-ZA-001 third-pass finding: "Broad production
        # QPE is not a valid upper-bound oracle" -- bounding the claimed
        # basis by the segment's own total qpe_usd (the prior, second-pass
        # fix) still let a component=production allocation with ZERO
        # classified post/VFX spend accept an arbitrary claimed QSAPPE up
        # to the FULL broad production total (independent reproducer:
        # $1,000,000 production-only allocation, $400,000 claimed QSAPPE,
        # $0 classified post/VFX spend -> wrongly priced $100,000).
        #
        # THE FIX: when the winning RateCondition names
        # component_basis_line_components (e.g. ("post", "vfx") for South
        # Africa), the upper bound is the EXACT traced subtotal of this
        # segment's own real AccountAllocation lines whose `component` is
        # in that tuple -- never the broad qpe_usd. Duplicate line_ids
        # among those lines are rejected outright (never double-counted).
        # A program without this refinement (e.g. us_or_opif, unaffected,
        # out of this repair's scope) keeps the prior, coarser qpe_usd
        # bound unchanged. Either way, a violation fails the WHOLE segment
        # closed -- never silently clamps the basis down and prices a
        # smaller-but-still-invented number.
        _basis = rr.qpe_basis_used
        if not isinstance(_basis, (int, float)) or isinstance(_basis, bool) or not math.isfinite(_basis):
            return SegmentEconomics(
                jurisdiction_code=jurisdiction_code, program_slug=slug,
                claims_incentive=True, allocated_usd=allocated,
                account_codes=codes, executable=False,
                qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
                doctrine=doctrine.value,
                blockers=(
                    f"{jurisdiction_code}/{slug}: component basis {_basis!r} is not a finite "
                    "non-negative number -- rejected before arithmetic, never used to compute economics.",
                ),
            )
        _basis_upper_bound = qpe
        _basis_bound_label = f"qualifying allocated spend ${qpe:,.2f}"
        if rr.qpe_basis_line_components:
            _traced_lines = [
                a for a in allocations
                if a.jurisdiction_code == jurisdiction_code and a.component in rr.qpe_basis_line_components
            ]
            _seen_line_ids: set[str] = set()
            _duplicate_line_ids: set[str] = set()
            _traced_subtotal = 0.0
            for _a in _traced_lines:
                if _a.line_id and _a.line_id in _seen_line_ids:
                    _duplicate_line_ids.add(_a.line_id)
                    continue
                if _a.line_id:
                    _seen_line_ids.add(_a.line_id)
                _traced_subtotal += _a.amount_usd
            if _duplicate_line_ids:
                return SegmentEconomics(
                    jurisdiction_code=jurisdiction_code, program_slug=slug,
                    claims_incentive=True, allocated_usd=allocated,
                    account_codes=codes, executable=False,
                    qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
                    doctrine=doctrine.value,
                    blockers=(
                        f"{jurisdiction_code}/{slug}: duplicate line_id(s) "
                        f"{sorted(_duplicate_line_ids)!r} among the classified "
                        f"{'/'.join(rr.qpe_basis_line_components)} allocation lines -- the same "
                        "source budget line can never be counted twice toward a component basis.",
                    ),
                )
            _basis_upper_bound = round(_traced_subtotal, 2)
            _basis_bound_label = (
                f"the exact classified {'/'.join(rr.qpe_basis_line_components)} allocated line "
                f"subtotal ${_basis_upper_bound:,.2f}"
            )
        if _basis < 0 or _basis > _basis_upper_bound:
            return SegmentEconomics(
                jurisdiction_code=jurisdiction_code, program_slug=slug,
                claims_incentive=True, allocated_usd=allocated,
                account_codes=codes, executable=False,
                qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
                doctrine=doctrine.value,
                blockers=(
                    f"{jurisdiction_code}/{slug}: component basis ${_basis:,.2f} is outside "
                    f"[0, {_basis_bound_label}] for this segment -- a claimed component "
                    "sub-total can never exceed (or be less than zero of) the segment's own "
                    "real, exactly-traced qualifying spend; rejected rather than priced on an "
                    "unreconciled scalar.",
                ),
            )
        floor_incentive_usd = round(_basis * rr.floor_rate, 2)
        ceiling_incentive_usd = round(_basis * rr.modeled_rate, 2)
    elif qpe_cap_applied > 0:
        # A QPE cap was applied above. build_risk_cases() re-derives its
        # own QPE total directly from `register`'s QUALIFIES-state
        # accounts (the full, uncapped statutory register — kept
        # unmodified so the register_trace/qualification_trace still
        # shows the true line-by-line statutory classification, cap
        # applied separately and disclosed via qpe_cap_applied_usd). With
        # no structuring_paths/grey_areas/overrides passed by this caller
        # (confirmed: structuring_paths=[] always, no other risk inputs
        # exposed here), build_risk_cases's CONSERVATIVE case reduces
        # exactly to incentive_usd = qpe_usd * rate — so the capped
        # incentive is computed directly rather than re-deriving from an
        # uncapped register that would silently ignore the cap.
        floor_incentive_usd = round(qpe * rr.floor_rate, 2)
        ceiling_incentive_usd = round(qpe * rr.modeled_rate, 2)
    else:
        # Same pricing kernel as everything else — no new math. Financing
        # is zero here by policy (explicit structure-level input only).
        floor_incentive_usd = build_risk_cases(
            register=register, gross_budget_usd=allocated, rate=rr.floor_rate,
            structuring_paths=[], delay_weeks=0, bridge_rate=0.0,
            jurisdiction_code=jurisdiction_code,
        ).cases[RiskCase.CONSERVATIVE].incentive_usd
        ceiling_incentive_usd = build_risk_cases(
            register=register, gross_budget_usd=allocated, rate=rr.modeled_rate,
            structuring_paths=[], delay_weeks=0, bridge_rate=0.0,
            jurisdiction_code=jurisdiction_code,
        ).cases[RiskCase.CONSERVATIVE].incentive_usd

    # Codex final wiring remediation (P0-OR-001): "qualifying base x rate
    # (+ uplift) = gross incentive, THEN the applicable dollar cap clips
    # it" (see the Cluster 7 comment below) -- a MULTIPLICATIVE uplift on
    # the already-computed incentive (e.g. Oregon's evidenced 10%
    # regional increase, "of the amount otherwise allowable" -- never
    # +10 percentage points on the rate itself). Applied to both floor
    # and ceiling, AFTER the base rate x basis calculation, BEFORE the
    # final dollar cap -- the exact sequence this codebase already
    # documents. None/1.0 (no evidenced uplift fact) leaves every other
    # program byte-identical.
    if rr.incentive_uplift_multiplier is not None:
        floor_incentive_usd = round(floor_incentive_usd * rr.incentive_uplift_multiplier, 2)
        ceiling_incentive_usd = round(ceiling_incentive_usd * rr.incentive_uplift_multiplier, 2)

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

    # Incentive/Optimizer Core Closeout: a ceiling tier "requires
    # confirmation" when it is a band ceiling AND at least one of its
    # conditions could not be pre-evaluated (satisfied=None) — e.g.
    # Mauritius's Film Rebate Committee discretion, Malta's Commissioner-
    # awarded uplift limbs, the UK's VFX Additional Credit sourcing
    # caveat. resolve_program_rate() already computes and discloses these
    # evaluations; this is the first place anything actually ACTS on that
    # disclosure instead of unconditionally serving the ceiling.
    ceiling_requires_confirmation = bool(
        rr.is_band_ceiling
        and any(e.satisfied is not True for e in rr.conditions_evaluated)
        and not (confirmed_ceiling_programs and slug in confirmed_ceiling_programs)
    )

    # ── Cluster 7: dollar caps constrain the INCENTIVE ───────────────────
    # Canonical sequence: qualifying base x rate (+ uplift) = gross
    # incentive, THEN the applicable dollar cap clips it. Applied after the
    # rate so the cap can never be mistaken for a base or a rate, and to
    # BOTH the floor and ceiling figures so a capped program cannot present
    # an uncapped upside. The pre-cap amount is preserved for audit.
    cap_usd, cap_type, cap_basis, cap_fx_error, cap_unresolved_detail = _resolve_incentive_dollar_cap(
        slug, fx_context, amount_facts, evidenced_requirement_facts,
    )
    if cap_unresolved_detail is not None:
        # Codex bounded remediation (P0-NL-001): a company-period
        # prior-awards aggregate is claimed (has_other_productions is
        # evidenced) but could not be resolved to a trustworthy amount.
        # Fail closed -- disclosed, non-priceable -- exactly like an
        # unsafe FX resolution below. Never silently substitute the full
        # native cap (that would hand out an unverified ceiling).
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
            doctrine=doctrine.value,
            qpe_cap_applied_usd=qpe_cap_applied,
            rate_ceiling=rr.modeled_rate, statutory_basis=rr.basis,
            blockers=(cap_unresolved_detail,),
        )
    if cap_fx_error is not None:
        # Codex final P0 (canonical_fx): a native-currency cap exists for
        # this program but its FX conversion could not be safely
        # resolved (missing/non-positive rate, or a stale_fallback
        # context). Fail closed -- disclosed, non-priceable -- rather
        # than silently drop the cap (fail-open) or let a raised
        # exception escape.
        return SegmentEconomics(
            jurisdiction_code=jurisdiction_code, program_slug=slug,
            claims_incentive=True, allocated_usd=allocated,
            account_codes=codes, executable=False,
            qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
            doctrine=doctrine.value,
            qpe_cap_applied_usd=qpe_cap_applied,
            rate_ceiling=rr.modeled_rate, statutory_basis=rr.basis,
            blockers=(
                f"{jurisdiction_code}/{slug}: this program's native-currency incentive "
                f"cap cannot be safely converted to USD ({cap_fx_error.status}: "
                f"{cap_fx_error.detail}). A genuinely unsafe FX disposition must never "
                "silently uncap the incentive or crash the request -- segment is "
                "allocated and disclosed but carries NO deterministic incentive value.",
            ),
        )
    incentive_uncapped_usd = None
    incentive_cap_applied = 0.0
    cap_notes: tuple[str, ...] = ()
    if cap_usd is not None and ceiling_incentive_usd > cap_usd:
        incentive_uncapped_usd = ceiling_incentive_usd
        incentive_cap_applied = round(ceiling_incentive_usd - cap_usd, 2)
        cap_notes = (
            f"{jurisdiction_code}/{slug}: incentive clipped by the program's "
            f"{cap_type.replace('_', ' ')} cap of ${cap_usd:,.2f} "
            f"({cap_basis}). Uncapped ${ceiling_incentive_usd:,.2f} -> "
            f"capped ${min(ceiling_incentive_usd, cap_usd):,.2f}.",
        )
        ceiling_incentive_usd = round(min(ceiling_incentive_usd, cap_usd), 2)
        floor_incentive_usd = round(min(floor_incentive_usd, cap_usd), 2)
    elif cap_usd is not None and floor_incentive_usd > cap_usd:
        incentive_uncapped_usd = floor_incentive_usd
        incentive_cap_applied = round(floor_incentive_usd - cap_usd, 2)
        floor_incentive_usd = round(min(floor_incentive_usd, cap_usd), 2)

    return SegmentEconomics(
        jurisdiction_code=jurisdiction_code, program_slug=slug,
        claims_incentive=True, allocated_usd=allocated,
        account_codes=codes, executable=True,
        qpe_usd=qpe, excluded_usd=excluded, unresolved_usd=unresolved,
        rate_floor=rr.floor_rate, rate_ceiling=rr.modeled_rate,
        is_band_ceiling=rr.is_band_ceiling, statutory_basis=rr.basis,
        incentive_floor_usd=floor_incentive_usd,
        incentive_ceiling_usd=ceiling_incentive_usd,
        doctrine=doctrine.value,
        register_trace=trace,
        notes=cap_notes,
        ceiling_requires_confirmation=ceiling_requires_confirmation,
        qpe_cap_applied_usd=qpe_cap_applied,
        incentive_cap_usd=cap_usd,
        incentive_cap_type=cap_type,
        incentive_cap_basis=cap_basis,
        incentive_uncapped_usd=incentive_uncapped_usd,
        incentive_cap_applied_usd=incentive_cap_applied,
        requirement_trace=tuple(
            {"requirement": e.requirement, "role": e.role,
             "state": e.state, "detail": e.detail}
            for e in requirements_gate.evaluations
            if e.state != "NOT_APPLICABLE"
        ),
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
    fx_basis: dict | None = None,
    inkind_replacement_delta_usd: float | None = None,
    local_cost_delta_usd: float | None = None,
    local_cost_basis: dict | None = None,
    financing_cost_usd: float = 0.0,
    implementation_cost_usd: float = 0.0,
    production_type: str = "feature_film",
    contingency_allocations: dict | None = None,
    confirmed_ceiling_programs: frozenset[str] | None = None,
    contingency_expected_utilization_pct: float | None = None,
    evidenced_requirement_facts: frozenset[str] | None = None,
    amount_facts: dict[str, float] | None = None,
    fx_context=None,
) -> AllocatedStructurePricing:
    """Price a complete structure from its allocation. Travel and FX
    deltas are structure-level, computed ONCE by the caller (for the
    primary jurisdiction against the original geography) and applied
    ONCE here. Financing/implementation default to zero — explicit
    inputs only, never a silent assumption.

    evidenced_requirement_facts/amount_facts (Codex final runtime
    remediation): project-wide fact sets, passed straight through to
    every segment's price_segment call — see price_segment's own
    docstring. Omitted (None) = byte-identical prior behavior.

    contingency_allocations (Task 91): optional {account_code:
    ContingencyAllocation}, defaulting to None (byte-identical prior
    behavior), passed through to every segment's price_segment call.

    confirmed_ceiling_programs (Incentive/Optimizer Core Closeout):
    passed through to price_segment — see its docstring. Omitted (None)
    = no discretionary ceiling is assumed confirmed for any segment.

    contingency_expected_utilization_pct (Consolidated Backend
    Correction, Part 19-20 / CBA-009): passed through to every segment's
    price_segment call — see its docstring. Omitted (None) = genuinely
    unset, disclosed as a grey area rather than assumed.

    fx_context (Codex final P0, canonical_fx): the ONE immutable
    CanonicalFXContext this ENTIRE structure is priced against — built
    once per canonical evaluation (see canonical_evaluation.evaluate_
    project) and passed straight through to every segment's price_segment
    call, never re-read from the mutable global mid-structure. Distinct
    from fx_delta_usd/fx_basis above, which model a SCENARIO exchange-
    rate movement delta on relocation/travel costs (production_
    normalization.compute_fx_normalization) — a different, pre-existing
    mechanism this parameter does not touch. Omitted (None) = each
    segment builds its own single-call context (safe, just not pinned
    across the whole structure)."""
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
            contingency_allocations=contingency_allocations,
            gross_budget_usd=gross_budget_usd,
            confirmed_ceiling_programs=confirmed_ceiling_programs,
            contingency_expected_utilization_pct=contingency_expected_utilization_pct,
            evidenced_requirement_facts=evidenced_requirement_facts,
            amount_facts=amount_facts,
            fx_context=fx_context,
        )
        segments.append(seg)
        blockers.extend(seg.blockers)

    total_floor = round(sum(s.incentive_floor_usd for s in segments), 2)
    total_ceiling = round(sum(s.incentive_ceiling_usd for s in segments), 2)

    fully_priced = not blockers

    # Canonical optimization contract (Phase 5), REVISED under the
    # Incentive/Optimizer Core Closeout: rank/serve on the BEST-SUPPORTED
    # incentive that is actually CONFIRMED — a discretionary ceiling
    # (ceiling_requires_confirmation=True; see SegmentEconomics) uses this
    # segment's FLOOR instead, unless confirmed_ceiling_programs overrides
    # it for this scenario. A jurisdiction with no discretionary condition
    # (e.g. Greece's flat 40%, Australia's flat 30%) is unaffected — its
    # ceiling IS its floor in every case that matters here. The
    # conservative floor total (total_floor/total_ceiling) remains
    # separately surfaced for disclosure; selected_incentive is now a
    # per-segment conditional sum, not an unconditional ceiling sum.
    selected_incentive = round(sum(
        (s.incentive_floor_usd if s.ceiling_requires_confirmation else s.incentive_ceiling_usd)
        for s in segments
    ), 2)
    _inkind_repl = inkind_replacement_delta_usd or 0.0
    _local_cost = local_cost_delta_usd or 0.0
    npc_verified = None      # here: best-supported NPC before normalizations
    npc_adjusted = None      # canonical, normalized, ranked NPC
    npc_conservative = None  # floor-rate NPC + same normalizations (uncertainty)
    if fully_priced:
        _norm = (
            (travel_incremental_delta_usd or 0.0) + (fx_delta_usd or 0.0)
            + _inkind_repl + _local_cost
        )
        npc_verified = round(
            gross_budget_usd - selected_incentive
            + financing_cost_usd + implementation_cost_usd, 2,
        )
        npc_adjusted = round(npc_verified + _norm, 2)
        npc_conservative = round(
            gross_budget_usd - total_floor
            + financing_cost_usd + implementation_cost_usd + _norm, 2,
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
        "The off-budget Mauritius in-kind post FMV is NOT a budget line and "
        "NOT QPE — it never enters any segment. It enters production "
        "economics only as a normalization: a structure that moves that work "
        "out of Mauritius absorbs its replacement cost "
        f"(inkind_replacement_delta_usd=${_inkind_repl:,.0f} on this "
        "structure); a structure that keeps the post in Mauritius carries $0."
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
        selected_incentive_usd=selected_incentive if fully_priced else 0.0,
        inkind_replacement_delta_usd=_inkind_repl,
        travel_incremental_delta_usd=travel_incremental_delta_usd,
        fx_delta_usd=fx_delta_usd,
        fx_basis=fx_basis,
        local_cost_delta_usd=local_cost_delta_usd,
        local_cost_basis=local_cost_basis,
        financing_cost_usd=financing_cost_usd,
        implementation_cost_usd=implementation_cost_usd,
        npc_verified_usd=npc_verified,
        npc_with_adjustments_usd=npc_adjusted,
        npc_conservative_usd=npc_conservative,
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
            "selected_incentive_usd": pricing.selected_incentive_usd,
            "travel_incremental_delta_usd": pricing.travel_incremental_delta_usd,
            "fx_delta_usd": pricing.fx_delta_usd,
            "inkind_replacement_delta_usd": pricing.inkind_replacement_delta_usd,
            "npc_verified_usd": pricing.npc_verified_usd,
            "npc_with_adjustments_usd": pricing.npc_with_adjustments_usd,
            "npc_conservative_usd": pricing.npc_conservative_usd,
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
    conditional_pursuable_by_structure: dict[str, int] | None = None,
) -> list[dict]:
    """Financial ranking over FULLY PRICED structures only (verified NPC
    with adjustments, ascending). Unpriced structures are listed after,
    unranked, with their exact blockers — never silently dropped and
    never ranked on a partial number.

    conditional_pursuable_by_structure (optimizer-integration phase):
    structure_id -> count of PURSUABLE conditional funding avenues the
    compatibility engine found for that structure (discretionary grants,
    broadcaster/co-production/regional funds that are not barred by
    evidence and not scope-mismatched).

    This NEVER changes a structure's Net Production Cost and never
    outranks it: NPC remains the sole primary key, exactly as before. It
    is applied only as a TIE-BREAK between structures whose defensible NPC
    is identical — among equally-costed structures, the one that opens
    more real (if gated) funding avenues ranks first. A discretionary
    award has no defensible dollar value, so it may inform a choice
    between equals but must never manufacture an advantage over a
    cheaper structure. Omitted (None) = byte-identical prior behavior.
    """
    counts = conditional_pursuable_by_structure or {}
    priced = sorted(
        (p for p in pricings if p.is_fully_priced),
        key=lambda p: (
            p.npc_with_adjustments_usd,          # primary: lowest defensible NPC
            -counts.get(p.structure_id, 0),      # tie-break: more pursuable avenues first
            p.structure_id,                      # final deterministic tie-break
        ),
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
            "selected_incentive_usd": p.selected_incentive_usd,
            "inkind_replacement_delta_usd": p.inkind_replacement_delta_usd,
            "npc_verified_usd": p.npc_verified_usd,
            "npc_with_adjustments_usd": p.npc_with_adjustments_usd,
            "npc_conservative_usd": p.npc_conservative_usd,
            # Conditional (non-priceable) funding depth for this structure —
            # surfaced alongside the ranked economics so two structures with
            # equal NPC are distinguishable, never folded INTO the NPC.
            "conditional_pursuable_count": counts.get(p.structure_id, 0),
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
