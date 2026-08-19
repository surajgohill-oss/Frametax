"""
canonical_opportunity_bridge.py

Reinvestment + Qualification Opportunity Optimization — the canonical
adapter connecting EXISTING, engine-agnostic legacy machinery
(app/data/program_requirements.py's ProgramRequirementsProfile registry,
app/calculators/inkind_contribution.py's cash/deferred/QPE scenario
model) to the current canonical served evaluation path
(canonical_evaluation.py). No new NPC/pricing engine, no new economics —
every dollar figure here is computed from data already produced by the
canonical qualification register and rate resolution for the SAME
candidate the opportunity is attached to.

Forensic recovery finding: ProgramRequirementsProfile (71 programs
populated, real primary-source-cited fields — atl_cap_pct_of_other_costs,
per_person_cap_usd, min_local_spend_usd, min_total_budget_usd,
cultural_test_points/threshold) and inkind_contribution.py's scenario
model (Scenario A-E: excluded / cash-paid-only / FMV / reduces-QPE /
unknown) both EXIST and are fully engine-agnostic (no dependency on the
superseded 0.1.0 run_full_analysis path) but were never connected to the
canonical served path — EXISTS_BUT_DISCONNECTED, the same pattern as the
optimizer/stacker reconnection before it.

Core discipline (Task 8 of the reinvestment phase spec): NEVER conflate
"incentive increases" with "the production is better off". Every
opportunity below reports incremental_gross_cost_usd, incremental_cash_usd,
incremental_qpe_usd, and incremental_incentive_usd as four SEPARATE
numbers, plus a net_benefit_usd that is only positive when the real cash
outlay is less than the incentive it generates (a genuine reallocation
opportunity) or explicitly zero-new-cash (a pure reclassification).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculators.inkind_contribution import (
    ContributionType,
    InKindContribution,
    QualifyingTreatment,
    SourceConfidence,
    analyse_inkind_contribution,
)
from app.calculators.screen_analyzer_fact_contract import required_fact_descriptions
from app.data.national_cultural_status import (
    STATUS_REGIME_CONFIRMED,
    get_jurisdiction_national_status,
)
from app.data.program_requirements import get_program_requirements

OPPORTUNITY_BRIDGE_VERSION = "1.1.0"
# 1.1.0 — Proactive Opportunity Discovery Reconciliation: adds proactive
# (budget-triggered, not just program-triggered) reinvestment-candidate
# scanning and qualification-lever discovery (movable post/vfx/music
# component relocation as a real, budget-backed lever for closing a real
# min-local-spend gap), plus the Task 8 fact_classification vocabulary and
# a `trigger` provenance field on every opportunity. Additive only — every
# existing field/function signature is unchanged.

# ── Opportunity status vocabulary (Task 9) ──────────────────────────────
STATUS_RESOLVED_PRICEABLE = "RESOLVED_PRICEABLE"
STATUS_CONDITIONAL = "CONDITIONAL_PROJECT_FACT_DEPENDENT"
STATUS_REQUIRES_USER_FACT = "REQUIRES_USER_FACT"
STATUS_REQUIRES_SCREEN_ANALYZER_FACT = "REQUIRES_SCREEN_ANALYZER_FACT"
STATUS_AUTHORITY_UNRESOLVED = "AUTHORITY_UNRESOLVED"
STATUS_NOT_ECONOMICALLY_BENEFICIAL = "NOT_ECONOMICALLY_BENEFICIAL"
STATUS_NOT_FEASIBLE = "NOT_FEASIBLE"

# ── Opportunity type vocabulary ──────────────────────────────────────────
TYPE_FEE_CAP_HEADROOM = "FEE_CAP_HEADROOM"
TYPE_PER_PERSON_CAP_HEADROOM = "PER_PERSON_CAP_HEADROOM"
TYPE_REINVESTMENT_VENDOR_PARTICIPATION = "REINVESTMENT_VENDOR_PARTICIPATION"
TYPE_POTENTIAL_REINVESTMENT = "POTENTIAL_REINVESTMENT_OPPORTUNITY"
TYPE_MIN_LOCAL_SPEND_GAP = "MIN_LOCAL_SPEND_GAP"
TYPE_MIN_TOTAL_BUDGET_GAP = "MIN_TOTAL_BUDGET_GAP"
TYPE_CULTURAL_TEST_GAP = "CULTURAL_TEST_GAP"
TYPE_QUALIFICATION_LEVER = "QUALIFICATION_LEVER"
TYPE_NATIONAL_STATUS_PATHWAY = "NATIONAL_STATUS_PATHWAY"

# ── Task 8 fact-classification vocabulary — never flattened ─────────────
FACT_KNOWN_PROJECT_FACT = "KNOWN_PROJECT_FACT"
FACT_USER_CONFIRMATION_REQUIRED = "USER_CONFIRMATION_REQUIRED"
FACT_SCREEN_ANALYZER_FACT_REQUIRED = "SCREEN_ANALYZER_FACT_REQUIRED"
FACT_PROPOSED_CHANGE = "PROPOSED_CHANGE"
FACT_AUTHORITY_FACT = "AUTHORITY_FACT"

#: Real, primary-source-cited canonical spend categories the movable-
#: component reinvestment/lever scan is allowed to look at — every entry
#: maps to a real production_allocation.component_for() output. Never
#: invents a category not already recognized by the canonical allocator.
_PROACTIVE_REINVESTMENT_COMPONENTS = ("post", "vfx", "music", "above_the_line")

#: Below this real dollar amount a component's spend is not material
#: enough to surface as a proactive vendor-participation candidate — a
#: policy threshold, not a per-project guess.
_MATERIALITY_FLOOR_USD = 50_000.0


@dataclass
class CanonicalOpportunity:
    """Task 2 — the one canonical opportunity model. Every field the
    reinvestment/qualification phase spec requires, no separate economic
    engine: incremental figures are always read off (or trivially derived
    from) the SAME register/rate/QPE the canonical pricing kernel already
    produced for the candidate this opportunity is attached to."""
    opportunity_id: str
    opportunity_type: str
    status: str
    jurisdiction_code: str
    program_slug: str
    title: str
    description: str

    # Source / proposed change
    source_component: str | None = None          # e.g. "above_the_line", "post"
    current_amount_usd: float | None = None
    proposed_amount_usd: float | None = None

    # Economics — kept strictly separate, never conflated (Task 8)
    incremental_gross_cost_usd: float = 0.0       # total budget change
    incremental_cash_usd: float = 0.0             # actual new cash outlay
    deferred_or_reinvested_usd: float = 0.0        # non-cash / deferred consideration
    incremental_qpe_usd: float = 0.0               # qualifying spend change
    incremental_incentive_usd: float = 0.0         # incentive change at the resolved rate
    implementation_cost_usd: float = 0.0
    net_benefit_usd: float | None = None           # None when status prevents a defensible number

    # Qualification-gap specific
    gap_amount_usd: float | None = None
    gap_measure: str | None = None                # e.g. "min_local_spend_usd"

    # Provenance / trace (Task 11)
    authority_basis: str | None = None
    required_facts: tuple[str, ...] = ()
    reasoning_trace: tuple[str, ...] = ()
    risk_notes: tuple[str, ...] = ()

    #: Task 11 — the real, concrete fact/data point that caused this
    #: opportunity to be discovered (e.g. "real ATL spend $200,000 < cap
    #: $600,000" or "post-production budget line total $172,904 >=
    #: materiality floor"). Never "the optimizer looked for opportunities".
    trigger: str | None = None

    #: Task 8 — distinguishes what KIND of fact this opportunity rests on.
    #: Never flattened into a single status field.
    fact_classification: str = "USER_CONFIRMATION_REQUIRED"


def _opp_id(kind: str, jurisdiction_code: str, program_slug: str, suffix: str = "") -> str:
    base = f"OPP-{kind}-{jurisdiction_code}-{program_slug}"
    return f"{base}-{suffix}" if suffix else base


def discover_fee_cap_headroom_opportunity(
    jurisdiction_code: str,
    program_slug: str,
    current_atl_spend_usd: float,
    total_budget_usd: float,
    effective_rate: float,
) -> CanonicalOpportunity | None:
    """Task 4 / Producer-ATL control case. Reads
    ProgramRequirementsProfile.atl_cap_pct_of_other_costs (real,
    primary-source-cited canonical data — never a hardcoded universal
    list) and compares CURRENT ATL spend against the MAXIMUM legitimately
    eligible amount. Returns None when no cap is on file (never invents
    one) or when there is no real headroom.

    Two funding scenarios are reported explicitly (never conflated,
    Task 8): reallocation (budget-neutral — the incremental producer fee
    is funded by reducing a non-qualifying account by the same amount,
    so net_benefit_usd is the incentive gain with zero new cash) is the
    PRIMARY reported scenario since it is the only one with a genuinely
    positive net benefit; the new-cash scenario is disclosed in
    reasoning_trace as a real alternative with a NEGATIVE net benefit
    (spending $1 of new cash to get back less than $1 of credit), so a
    reader is never misled into treating incentive growth as costless.
    """
    profile = get_program_requirements(program_slug)
    if profile is None or profile.atl_cap_pct_of_other_costs is None:
        return None
    if total_budget_usd <= 0:
        return None

    max_eligible_atl = total_budget_usd * profile.atl_cap_pct_of_other_costs
    headroom = max_eligible_atl - current_atl_spend_usd
    if headroom <= 0:
        return None

    incremental_incentive = round(headroom * effective_rate, 2)
    # Reallocation scenario: no new net cash, funded by reducing a
    # non-qualifying account (e.g. contingency) by the same amount.
    net_benefit_reallocation = incremental_incentive
    # New-cash scenario: genuinely spending more — always a net loss
    # unless the production independently needs the higher fee for a
    # non-tax reason (never assumed here).
    net_benefit_new_cash = round(incremental_incentive - headroom, 2)

    return CanonicalOpportunity(
        opportunity_id=_opp_id("ATL-CAP", jurisdiction_code, program_slug),
        opportunity_type=TYPE_FEE_CAP_HEADROOM,
        status=STATUS_CONDITIONAL,
        jurisdiction_code=jurisdiction_code,
        program_slug=program_slug,
        title=f"Unused ATL/producer-fee qualifying headroom ({profile.atl_cap_pct_of_other_costs:.0%} cap)",
        description=(
            f"{program_slug} permits ATL/above-the-line costs to qualify up to "
            f"{profile.atl_cap_pct_of_other_costs:.0%} of total budget "
            f"(${max_eligible_atl:,.0f}). Current ATL spend is "
            f"${current_atl_spend_usd:,.0f} — ${headroom:,.0f} of legitimately "
            "eligible headroom is currently unused."
        ),
        source_component="above_the_line",
        current_amount_usd=current_atl_spend_usd,
        proposed_amount_usd=current_atl_spend_usd + headroom,
        incremental_gross_cost_usd=0.0,  # reallocation scenario: total budget unchanged
        incremental_cash_usd=0.0,
        deferred_or_reinvested_usd=0.0,
        incremental_qpe_usd=headroom,
        incremental_incentive_usd=incremental_incentive,
        net_benefit_usd=net_benefit_reallocation,
        authority_basis=(
            profile.evidence.source_title if profile.evidence else None
        ) or f"{program_slug} ATL cap (canonical program_requirements registry)",
        required_facts=(
            "Confirm which existing non-qualifying budget line would be reduced "
            "to fund the reallocated ATL/producer fee amount (reallocation "
            "scenario) OR confirm the production genuinely needs the additional "
            "cash spend independent of tax treatment (new-cash scenario).",
        ),
        reasoning_trace=(
            f"Cap: {profile.atl_cap_pct_of_other_costs:.0%} of total budget "
            f"(${total_budget_usd:,.0f}) = ${max_eligible_atl:,.0f} maximum "
            "eligible ATL.",
            f"Current ATL spend ${current_atl_spend_usd:,.0f} < maximum — "
            f"headroom ${headroom:,.0f}.",
            f"Reallocation scenario: incremental QPE ${headroom:,.0f} x "
            f"effective rate {effective_rate:.1%} = ${incremental_incentive:,.0f} "
            "incentive, zero new net cash -> net benefit "
            f"${net_benefit_reallocation:,.0f}.",
            f"New-cash scenario (disclosed, NOT recommended): spending "
            f"${headroom:,.0f} new cash to gain ${incremental_incentive:,.0f} "
            f"incentive nets ${net_benefit_new_cash:,.0f} — a LOSS, since the "
            "incentive rate is always less than 100%. Incentive growth alone "
            "is never reported as a benefit (Task 8).",
        ),
        risk_notes=(
            "Reallocation scenario requires a real, identifiable non-qualifying "
            "account with sufficient headroom to reduce — not assumed to exist.",
        ),
        trigger=(
            f"Real ATL spend ${current_atl_spend_usd:,.0f} < real cap "
            f"${max_eligible_atl:,.0f} ({profile.atl_cap_pct_of_other_costs:.0%} "
            f"of ${total_budget_usd:,.0f})."
        ),
        fact_classification=FACT_USER_CONFIRMATION_REQUIRED,
    )


def discover_per_person_cap_headroom_opportunity(
    jurisdiction_code: str,
    program_slug: str,
    high_earner_amounts_usd: list[float],
    effective_rate: float,
) -> CanonicalOpportunity | None:
    """Per-person cap is a CEILING (excess is excluded), never headroom to
    exploit upward — included for completeness/disclosure only when a
    real high earner is already AT or NEAR the cap, so the production
    knows further increases to that person's fee would not generate
    additional incentive. Returns None absent real data."""
    profile = get_program_requirements(program_slug)
    if profile is None or profile.per_person_cap_usd is None or not high_earner_amounts_usd:
        return None
    at_cap = [a for a in high_earner_amounts_usd if a >= profile.per_person_cap_usd * 0.9]
    if not at_cap:
        return None
    return CanonicalOpportunity(
        opportunity_id=_opp_id("PERSON-CAP", jurisdiction_code, program_slug),
        opportunity_type=TYPE_PER_PERSON_CAP_HEADROOM,
        status=STATUS_RESOLVED_PRICEABLE,
        jurisdiction_code=jurisdiction_code,
        program_slug=program_slug,
        title="Per-person qualifying cap reached — no further headroom",
        description=(
            f"{program_slug} caps per-person qualifying compensation at "
            f"${profile.per_person_cap_usd:,.0f}. {len(at_cap)} budgeted "
            "individual(s) are already at or near this cap — additional "
            "compensation to these individuals would NOT generate additional "
            "incentive."
        ),
        incremental_qpe_usd=0.0,
        incremental_incentive_usd=0.0,
        net_benefit_usd=0.0,
        authority_basis=(profile.evidence.source_title if profile.evidence else None),
        reasoning_trace=(
            f"{len(at_cap)} individual(s) at/near the ${profile.per_person_cap_usd:,.0f} cap.",
            "This is disclosure, not an opportunity to pursue — increasing "
            "compensation further would not increase QPE.",
        ),
        trigger=f"{len(at_cap)} real budgeted individual(s) at/near the per-person cap.",
        fact_classification=FACT_KNOWN_PROJECT_FACT,
    )


def discover_qualification_gap_opportunity(
    jurisdiction_code: str,
    program_slug: str,
    actual_local_spend_usd: float | None,
    actual_total_budget_usd: float | None,
) -> list[CanonicalOpportunity]:
    """Task 6 — curable vs impossible qualification gaps for min-spend
    thresholds. Uses ProgramRequirementsProfile's real min_local_spend_usd/
    min_total_budget_usd. A gap is CURABLE (measurable, disclosed, no
    fake solution) whenever the shortfall is a strictly positive,
    finite dollar amount; genuinely impossible cases (e.g. a hard
    structural bar unrelated to spend) are out of this function's scope
    entirely — it only ever reports spend-threshold gaps, never invents
    a cure for a non-spend requirement."""
    profile = get_program_requirements(program_slug)
    if profile is None:
        return []
    opportunities: list[CanonicalOpportunity] = []

    if profile.min_local_spend_usd is not None and actual_local_spend_usd is not None:
        gap = profile.min_local_spend_usd - actual_local_spend_usd
        if gap > 0:
            opportunities.append(CanonicalOpportunity(
                opportunity_id=_opp_id("MIN-LOCAL-SPEND", jurisdiction_code, program_slug),
                opportunity_type=TYPE_MIN_LOCAL_SPEND_GAP,
                status=STATUS_CONDITIONAL,
                jurisdiction_code=jurisdiction_code,
                program_slug=program_slug,
                title="Minimum local-spend threshold shortfall (curable)",
                description=(
                    f"{program_slug} requires minimum local spend of "
                    f"${profile.min_local_spend_usd:,.0f}. Current local spend "
                    f"${actual_local_spend_usd:,.0f} is ${gap:,.0f} short."
                ),
                current_amount_usd=actual_local_spend_usd,
                proposed_amount_usd=profile.min_local_spend_usd,
                gap_amount_usd=round(gap, 2),
                gap_measure="min_local_spend_usd",
                incremental_gross_cost_usd=round(gap, 2),
                incremental_cash_usd=round(gap, 2),
                authority_basis=(profile.evidence.source_title if profile.evidence else None),
                required_facts=(
                    "Confirm whether legitimate additional local spend "
                    f"(local vendors/crew/facilities) of ${gap:,.0f} is "
                    "genuinely achievable for this production without "
                    "inventing spend that would not otherwise occur.",
                ),
                reasoning_trace=(
                    f"Required: ${profile.min_local_spend_usd:,.0f}. "
                    f"Actual: ${actual_local_spend_usd:,.0f}. "
                    f"Gap: ${gap:,.0f} — measurable and, if the production "
                    "can legitimately shift or add local spend of this size, "
                    "curable. Not automatically recommended: the incremental "
                    "cash cost is real (Task 8) and must be weighed against "
                    "the incentive this program's rate would then unlock.",
                ),
                trigger=f"Real local spend ${actual_local_spend_usd:,.0f} < real minimum ${profile.min_local_spend_usd:,.0f}.",
                fact_classification=FACT_PROPOSED_CHANGE,
            ))

    if profile.min_total_budget_usd is not None and actual_total_budget_usd is not None:
        gap = profile.min_total_budget_usd - actual_total_budget_usd
        if gap > 0:
            opportunities.append(CanonicalOpportunity(
                opportunity_id=_opp_id("MIN-TOTAL-BUDGET", jurisdiction_code, program_slug),
                opportunity_type=TYPE_MIN_TOTAL_BUDGET_GAP,
                status=STATUS_CONDITIONAL,
                jurisdiction_code=jurisdiction_code,
                program_slug=program_slug,
                title="Minimum total-budget threshold shortfall (curable)",
                description=(
                    f"{program_slug} requires a minimum total production budget "
                    f"of ${profile.min_total_budget_usd:,.0f}. Current budget "
                    f"${actual_total_budget_usd:,.0f} is ${gap:,.0f} short."
                ),
                current_amount_usd=actual_total_budget_usd,
                proposed_amount_usd=profile.min_total_budget_usd,
                gap_amount_usd=round(gap, 2),
                gap_measure="min_total_budget_usd",
                incremental_gross_cost_usd=round(gap, 2),
                incremental_cash_usd=round(gap, 2),
                authority_basis=(profile.evidence.source_title if profile.evidence else None),
                required_facts=(
                    "This program becomes entirely unavailable below the "
                    "minimum budget threshold — this is a real production-"
                    "scale decision, never a cosmetic budget adjustment.",
                ),
                reasoning_trace=(
                    f"Required: ${profile.min_total_budget_usd:,.0f}. "
                    f"Actual: ${actual_total_budget_usd:,.0f}. Gap: ${gap:,.0f}.",
                ),
                trigger=f"Real total budget ${actual_total_budget_usd:,.0f} < real minimum ${profile.min_total_budget_usd:,.0f}.",
                fact_classification=FACT_PROPOSED_CHANGE,
            ))

    return opportunities


def discover_cultural_test_gap_opportunity(
    jurisdiction_code: str,
    program_slug: str,
) -> CanonicalOpportunity | None:
    """Task 7 — cultural/co-pro opportunity filling, Screen-Analyzer
    boundary respected. This function NEVER scores an actual cultural
    test (no project fact currently exists that could support real
    scoring) — it only discloses, from ProgramRequirementsProfile's real
    cultural_test_points/cultural_test_threshold fields, THAT a points
    gap analysis is possible once script-derived facts exist, and marks
    it REQUIRES_SCREEN_ANALYZER_FACT. Creates no fake answer."""
    profile = get_program_requirements(program_slug)
    if profile is None or profile.cultural_test_threshold is None:
        return None
    return CanonicalOpportunity(
        opportunity_id=_opp_id("CULTURAL-GAP", jurisdiction_code, program_slug),
        opportunity_type=TYPE_CULTURAL_TEST_GAP,
        status=STATUS_REQUIRES_SCREEN_ANALYZER_FACT,
        jurisdiction_code=jurisdiction_code,
        program_slug=program_slug,
        title="Cultural-test points gap analysis unavailable (script facts required)",
        description=(
            f"{program_slug} requires a minimum of {profile.cultural_test_threshold} "
            "cultural-test points"
            + (f" (of {profile.cultural_test_points} available)" if profile.cultural_test_points else "")
            + ". No project fact currently establishes which criteria (writer/"
            "director/cast nationality, shooting location, story setting, "
            "language, post-production activity, etc.) this production "
            "actually satisfies — a real points count cannot be fabricated."
        ),
        gap_measure="cultural_test_threshold",
        authority_basis=(profile.evidence.source_title if profile.evidence else None),
        required_facts=required_fact_descriptions(consumer="discover_cultural_test_gap_opportunity"),
        reasoning_trace=(
            f"Threshold: {profile.cultural_test_threshold} points.",
            "No script-derived project facts exist yet to score actual "
            "points earned — this capability is intentionally deferred to "
            "the future Screen Analyzer phase, which will supply the "
            "structured facts this function is designed to consume without "
            "requiring a rewrite.",
        ),
        risk_notes=(
            "Never automatically scored. Never assumed to pass or fail.",
        ),
        trigger=f"Real cultural_test_threshold={profile.cultural_test_threshold} on file, no script facts on file.",
        fact_classification=FACT_SCREEN_ANALYZER_FACT_REQUIRED,
    )


def discover_reinvestment_opportunity(
    jurisdiction_code: str,
    program_slug: str,
    component: str,
    face_value_usd: float,
    cash_paid_usd: float,
    effective_rate: float,
    base_qpe_usd: float,
) -> CanonicalOpportunity | None:
    """Task 3 — vendor participation / reinvestment / deferred
    consideration. Reuses inkind_contribution.analyse_inkind_contribution
    UNCHANGED (its own scenario model already keeps cash/FMV/QPE
    treatment strictly separate — see that module's own Scenario A-E).
    face_value_usd is the gross/notional value of the service (e.g. a
    post-production deal); cash_paid_usd is what the production actually
    pays; the difference is the deferred/reinvested/non-cash portion.
    Returns None if there is no deferred portion (a fully-cash
    transaction has nothing to model here)."""
    deferred = round(face_value_usd - cash_paid_usd, 2)
    if deferred <= 0:
        return None

    contribution = InKindContribution(
        contribution_type=ContributionType.CASH_REINVESTMENT,
        description=f"{component} — vendor reinvestment/deferred consideration",
        face_value_usd=face_value_usd,
        cash_paid_usd=cash_paid_usd,
        fair_market_value_usd=face_value_usd,
        qualifying_treatment=QualifyingTreatment.UNKNOWN,
        requires_invoice=True,
        requires_payment_proof=True,
        requires_fmv_support=True,
        requires_related_party_disclosure=True,
        source_confidence=SourceConfidence.UNKNOWN,
    )
    result = analyse_inkind_contribution(contribution, effective_rate, base_qpe_usd)

    cash_scenario = next((s for s in result.scenarios if s.scenario_id == "B"), None)
    cash_qpe = cash_scenario.qpe_amount_usd if cash_scenario else cash_paid_usd
    cash_incentive = cash_scenario.rebate_impact_usd if cash_scenario else round(cash_qpe * effective_rate, 2)

    return CanonicalOpportunity(
        opportunity_id=_opp_id("REINVEST", jurisdiction_code, program_slug, component),
        opportunity_type=TYPE_REINVESTMENT_VENDOR_PARTICIPATION,
        status=STATUS_AUTHORITY_UNRESOLVED if result.edb_ruling_required else STATUS_CONDITIONAL,
        jurisdiction_code=jurisdiction_code,
        program_slug=program_slug,
        title=f"Vendor reinvestment/deferred consideration — {component}",
        description=(
            f"{component} has a gross/notional value of ${face_value_usd:,.0f}. "
            f"The production pays ${cash_paid_usd:,.0f} cash; ${deferred:,.0f} "
            "is deferred/reinvested in exchange for vendor consideration "
            "(e.g. profit participation) rather than paid in cash."
        ),
        source_component=component,
        current_amount_usd=face_value_usd,
        proposed_amount_usd=cash_paid_usd,
        incremental_gross_cost_usd=0.0,
        incremental_cash_usd=0.0,
        deferred_or_reinvested_usd=deferred,
        incremental_qpe_usd=round(cash_qpe - base_qpe_usd, 2) if cash_qpe else 0.0,
        incremental_incentive_usd=cash_incentive,
        net_benefit_usd=None,  # never asserted -- authority treatment unresolved (see below)
        authority_basis=None,
        required_facts=(
            f"{program_slug}'s own authority must confirm the qualifying "
            "treatment of deferred/reinvested (non-cash) consideration — "
            "the default, conservative international-standard assumption "
            "(inkind_contribution.py) is that ONLY cash actually paid "
            f"(${cash_paid_usd:,.0f}) qualifies, never the full "
            f"${face_value_usd:,.0f} gross/notional value.",
        ),
        reasoning_trace=tuple(
            f"Scenario {s.scenario_id} ({s.scenario_name}): QPE=${s.qpe_amount_usd:,.0f}, "
            f"incentive impact=${s.rebate_impact_usd:,.0f}"
            for s in result.scenarios
        ) + (
            f"Recommended (international-standard) treatment: Scenario "
            f"{result.recommended_scenario}. Authority ruling required: "
            f"{result.edb_ruling_required}.",
        ),
        risk_notes=tuple(result.international_precedents[:3]),
        trigger=f"Real face value ${face_value_usd:,.0f} != real cash paid ${cash_paid_usd:,.0f}.",
        fact_classification=FACT_AUTHORITY_FACT if result.edb_ruling_required else FACT_USER_CONFIRMATION_REQUIRED,
    )


def discover_potential_reinvestment_candidates(
    jurisdiction_code: str,
    program_slug: str,
    component_spend_usd: dict[str, float],
) -> list[CanonicalOpportunity]:
    """Task 3 — PROACTIVE reinvestment/vendor-participation discovery.
    Unlike discover_reinvestment_opportunity (which requires an ALREADY
    KNOWN face-value/cash-paid split), this scans real, already-summed
    budget-line totals per movable component (post/vfx/music/above_the_line
    — production_allocation.component_for()'s own vocabulary, nothing
    invented) and flags any component whose real spend clears the
    materiality floor as a CANDIDATE worth asking the production about.
    No cash/deferred split is assumed — status is always REQUIRES_USER_FACT
    and proposed_amount_usd/deferred_or_reinvested_usd stay None until a
    real commercial term is supplied (which then flows through
    discover_reinvestment_opportunity for the actual scenario math)."""
    opportunities: list[CanonicalOpportunity] = []
    for component in _PROACTIVE_REINVESTMENT_COMPONENTS:
        amount = component_spend_usd.get(component)
        if not amount or amount < _MATERIALITY_FLOOR_USD:
            continue
        opportunities.append(CanonicalOpportunity(
            opportunity_id=_opp_id("POTENTIAL-REINVEST", jurisdiction_code, program_slug, component),
            opportunity_type=TYPE_POTENTIAL_REINVESTMENT,
            status=STATUS_REQUIRES_USER_FACT,
            jurisdiction_code=jurisdiction_code,
            program_slug=program_slug,
            title=f"Potential vendor participation/reinvestment — {component} (${amount:,.0f} real spend)",
            description=(
                f"This budget's real {component} spend totals ${amount:,.0f} — "
                "a substantial vendor/service category. Some vendors in this "
                "category are willing to defer or reinvest part of their fee "
                "for profit participation or other consideration, which can "
                "change the qualifying/cash treatment of that portion. No "
                "such arrangement is known to exist for this production — "
                "this is a candidate to raise with the vendor, not a modeled "
                "deal."
            ),
            source_component=component,
            current_amount_usd=amount,
            proposed_amount_usd=None,
            deferred_or_reinvested_usd=None,
            incremental_gross_cost_usd=0.0,
            incremental_cash_usd=0.0,
            incremental_qpe_usd=0.0,
            incremental_incentive_usd=0.0,
            net_benefit_usd=None,
            authority_basis=None,
            required_facts=(
                f"Whether the {component} vendor(s) would accept any portion "
                "of their fee as deferred consideration/profit participation "
                "rather than cash, and on what commercial terms.",
                "The production's own willingness to negotiate such terms — "
                "never assumed here.",
            ),
            reasoning_trace=(
                f"Real {component} budget-line total: ${amount:,.0f} "
                f"(>= materiality floor ${_MATERIALITY_FLOOR_USD:,.0f}).",
                "No cash/deferred split is known — this is a candidate for "
                "the production to explore, not a priced opportunity. Once "
                "real face-value/cash-paid terms exist, "
                "discover_reinvestment_opportunity() prices the actual "
                "scenario.",
            ),
            risk_notes=(
                "Never assumes vendor willingness. Never fabricates a "
                "cash/deferred split.",
            ),
            trigger=f"Real {component} spend ${amount:,.0f} >= materiality floor ${_MATERIALITY_FLOOR_USD:,.0f}.",
            fact_classification=FACT_USER_CONFIRMATION_REQUIRED,
        ))
    return opportunities


def discover_qualification_lever_opportunities(
    jurisdiction_code: str,
    program_slug: str,
    gap_opportunities: list[CanonicalOpportunity],
    movable_component_spend_elsewhere_usd: dict[str, float],
) -> list[CanonicalOpportunity]:
    """Task 5 — qualification levers. For a real MIN_LOCAL_SPEND_GAP
    already discovered on this candidate, checks whether a real movable
    component (post/vfx/music — production_allocation.MOVABLE_COMPONENTS)
    currently spent OUTSIDE this jurisdiction has a real dollar total that
    would close the gap if relocated here. Never invents a component or a
    spend amount — both come from the SAME real budget lines the canonical
    allocator already parsed. Always a PROPOSED_CHANGE requiring explicit
    approval, never auto-applied."""
    levers: list[CanonicalOpportunity] = []
    local_spend_gaps = [g for g in gap_opportunities if g.gap_measure == "min_local_spend_usd" and g.gap_amount_usd]
    for gap in local_spend_gaps:
        for component, amount in sorted(movable_component_spend_elsewhere_usd.items()):
            if not amount or amount < gap.gap_amount_usd:
                continue
            levers.append(CanonicalOpportunity(
                opportunity_id=_opp_id("QUAL-LEVER", jurisdiction_code, program_slug, component),
                opportunity_type=TYPE_QUALIFICATION_LEVER,
                status=STATUS_CONDITIONAL,
                jurisdiction_code=jurisdiction_code,
                program_slug=program_slug,
                title=f"Route {component} to {jurisdiction_code} to close local-spend gap",
                description=(
                    f"{program_slug} requires ${gap.gap_amount_usd:,.0f} more "
                    f"local spend. The production's real {component} spend "
                    f"(currently outside {jurisdiction_code}) totals "
                    f"${amount:,.0f} — enough, if genuinely relocatable, to "
                    "close this gap. This is a proposed change requiring "
                    "explicit approval, not an automatic routing."
                ),
                source_component=component,
                current_amount_usd=0.0,
                proposed_amount_usd=gap.gap_amount_usd,
                gap_amount_usd=gap.gap_amount_usd,
                gap_measure="min_local_spend_usd",
                incremental_gross_cost_usd=0.0,
                incremental_cash_usd=0.0,
                authority_basis=gap.authority_basis,
                required_facts=(
                    f"Confirm the {component} work can genuinely be performed "
                    f"in {jurisdiction_code} without disrupting the production "
                    "workflow — this is a real operational decision, not a "
                    "cosmetic budget reallocation.",
                    "Component-relocation pricing (existing canonical "
                    "component/split pathway) must be run separately to "
                    "confirm the net economic effect before this lever is "
                    "acted on.",
                ),
                reasoning_trace=(
                    f"Gap: ${gap.gap_amount_usd:,.0f} local spend required.",
                    f"Real {component} spend elsewhere: ${amount:,.0f} — "
                    "sufficient in principle to close the gap.",
                    "Not automatically recommended: relocating a component "
                    "has its own real cost/feasibility implications, priced "
                    "separately by the existing component-relocation pathway.",
                ),
                risk_notes=(
                    "Never invents a component or an amount not already on "
                    "the production's real budget.",
                ),
                trigger=f"Real {component} spend ${amount:,.0f} >= real gap ${gap.gap_amount_usd:,.0f}.",
                fact_classification=FACT_PROPOSED_CHANGE,
            ))
    return levers


def discover_national_status_opportunity(
    jurisdiction_code: str,
    program_slug: str,
) -> CanonicalOpportunity | None:
    """Worldwide Jurisdiction National/Cultural Status Completion, Task
    10 -- surfaces a real, primary-authority-confirmed national/cultural
    pathway even when the CURRENT candidate is priced under the
    jurisdiction's foreign/service pathway (national_cultural_status.py).
    Returns None when: no confirmed separate pathway exists for this
    jurisdiction, OR the candidate's own program_slug already IS the
    national pathway's program (nothing to surface -- it's already
    priced as such), OR the confirmed regime has no separate
    linked_program_slug to point to.

    Never fabricates an economic figure: this candidate's own real
    pricing is untouched; the opportunity discloses the REAL, cited rate/
    program difference already researched (consequence_detail) as
    context, but reports no incremental_incentive_usd unless a future
    pass wires the linked program into canonical pricing -- Task 10's
    explicit 'calculate ONLY when all necessary economic inputs are
    deterministic' boundary."""
    status = get_jurisdiction_national_status(jurisdiction_code)
    if status.status != STATUS_REGIME_CONFIRMED:
        return None
    if not status.linked_program_slug or status.linked_program_slug == program_slug:
        return None
    if status.base_program_slug != program_slug:
        # This candidate isn't priced under the confirmed foreign/service
        # pathway this regime is paired against -- don't surface a
        # mismatched opportunity.
        return None

    return CanonicalOpportunity(
        opportunity_id=_opp_id("NATIONAL-STATUS", jurisdiction_code, program_slug, status.linked_program_slug),
        opportunity_type=TYPE_NATIONAL_STATUS_PATHWAY,
        status=STATUS_REQUIRES_USER_FACT,
        jurisdiction_code=jurisdiction_code,
        program_slug=program_slug,
        title=f"National/cultural pathway available: {status.regime_name or status.linked_program_slug}",
        description=(
            f"This candidate is priced under {program_slug} (foreign/service pathway, no cultural "
            f"status required). A separate, real national/cultural pathway exists in "
            f"{jurisdiction_code} -- {status.regime_name}, administered by "
            f"{status.administering_authority or 'the relevant authority'} -- unlocking "
            f"{status.linked_program_slug}. {status.consequence_detail or ''}"
        ),
        source_component=None,
        incremental_gross_cost_usd=0.0,
        incremental_cash_usd=0.0,
        incremental_qpe_usd=0.0,
        incremental_incentive_usd=0.0,  # never fabricated -- linked program not wired into canonical pricing this pass
        net_benefit_usd=None,
        authority_basis="; ".join(status.sources) if status.sources else None,
        required_facts=(
            "Confirm the production's writer/director/producer/cast nationality and residency, "
            "ownership/control structure, and actual work locations against "
            f"{status.linked_program_slug}'s real qualification requirements before this pathway "
            "can be priced.",
        ),
        reasoning_trace=(
            f"Confirmed national/cultural status regime: {status.regime_name}.",
            f"Economic consequence: {status.economic_consequence} -- {status.consequence_detail or 'no quantified detail on file'}.",
            f"{status.linked_program_slug} is not yet wired into canonical pricing (outside the "
            "current 71-program served universe) -- this opportunity is disclosure-only, never a "
            "fabricated priced figure.",
        ),
        risk_notes=(
            "Requires real personnel/ownership/entity facts this system does not yet have for this "
            "project -- never assumed satisfied.",
        ),
        trigger=f"Candidate priced under confirmed foreign/service pathway {program_slug}; a real separate national pathway exists for {jurisdiction_code}.",
        fact_classification=FACT_USER_CONFIRMATION_REQUIRED,
    )


def opportunity_to_dict(opp: CanonicalOpportunity) -> dict:
    return {
        "opportunity_id": opp.opportunity_id,
        "opportunity_type": opp.opportunity_type,
        "status": opp.status,
        "jurisdiction_code": opp.jurisdiction_code,
        "program_slug": opp.program_slug,
        "title": opp.title,
        "description": opp.description,
        "source_component": opp.source_component,
        "current_amount_usd": opp.current_amount_usd,
        "proposed_amount_usd": opp.proposed_amount_usd,
        "incremental_gross_cost_usd": opp.incremental_gross_cost_usd,
        "incremental_cash_usd": opp.incremental_cash_usd,
        "deferred_or_reinvested_usd": opp.deferred_or_reinvested_usd,
        "incremental_qpe_usd": opp.incremental_qpe_usd,
        "incremental_incentive_usd": opp.incremental_incentive_usd,
        "implementation_cost_usd": opp.implementation_cost_usd,
        "net_benefit_usd": opp.net_benefit_usd,
        "gap_amount_usd": opp.gap_amount_usd,
        "gap_measure": opp.gap_measure,
        "authority_basis": opp.authority_basis,
        "required_facts": list(opp.required_facts),
        "reasoning_trace": list(opp.reasoning_trace),
        "risk_notes": list(opp.risk_notes),
        "trigger": opp.trigger,
        "fact_classification": opp.fact_classification,
    }
