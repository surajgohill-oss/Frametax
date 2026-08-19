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
from app.data.program_requirements import get_program_requirements

OPPORTUNITY_BRIDGE_VERSION = "1.0.0"

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
TYPE_MIN_LOCAL_SPEND_GAP = "MIN_LOCAL_SPEND_GAP"
TYPE_MIN_TOTAL_BUDGET_GAP = "MIN_TOTAL_BUDGET_GAP"
TYPE_CULTURAL_TEST_GAP = "CULTURAL_TEST_GAP"


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
        required_facts=(
            "Writer/director/producer/cast nationality or residency",
            "Story setting and subject matter",
            "Shooting location(s)",
            "Language of production",
            "Post-production activity location",
            "Any other criteria this program's own cultural test scores",
        ),
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
    }
