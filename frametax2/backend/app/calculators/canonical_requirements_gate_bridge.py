"""
canonical_requirements_gate_bridge.py

CANONICAL MANDATORY-REQUIREMENT GATE (cluster 2).

program_requirements.ProgramRequirementsProfile already holds the real
qualification/timing/compliance facts for a program, but the served pricing
path consumed them only as CONFIDENCE / disclosure metadata. Nothing made a
mandatory requirement a prerequisite to a deterministic number, so a program
could present a firm incentive while its local-entity, minimum-spend,
minimum-shoot-days or competitive-selection conditions were entirely
unconfirmed. This bridge is the missing prerequisite, in the same shape as the
other canonical bridges (role/cultural, treaty, stack) -- it adds no new
registry and duplicates no economics.

FOUR SEMANTIC STATES, and a missing fact is never silently SATISFIED:

    SATISFIED       evaluated against a real project figure/fact and met
    FAILED          evaluated and genuinely not met
    UNKNOWN         mandatory, but the deciding fact is not on file
    NOT_APPLICABLE  the program does not impose this requirement, or another
                    canonical owner adjudicates it (cultural qualification)

REQUIREMENT ROLES. The profile carries no role field, so the roles below are
assigned here, explicitly, and deliberately conservatively:

  ELIGIBILITY   -- a fact about THIS PRODUCTION that decides whether it can
                   receive the incentive: the statutory minimum-budget and
                   minimum-local-spend floors. These are evaluated against the
                   production's real figures and GATE deterministic pricing --
                   a genuine miss is genuine ineligibility.
  ADMINISTRATIVE-- something the producer DOES in the ordinary course
                   (preapproval, audit, CPA sign-off, completion bond, entity
                   formation, a local co-producer), plus allocation type.
                   DISCLOSED as an explicit UNKNOWN, never gating: these are
                   equally unconfirmed for every option at planning time, so
                   gating on them removes the entire comparison while telling
                   the producer nothing that distinguishes one jurisdiction
                   from another. Selectivity that IS decisive is already
                   adjudicated upstream by authority_coverage_registry.
  INFORMATIONAL -- monetization/cash-flow shape (refundable, transferable,
                   transfer price, payment timing). Never gating.

What the doctrine actually forbids is a missing mandatory fact being SILENTLY
treated as satisfied. Nothing here is silent: every unmet or unknown
requirement is emitted as a typed evaluation with its state and reason, and
carried onto the segment for the producer to see. A genuinely failed
threshold blocks; an unresolved process step is surfaced, never assumed.
"""
from __future__ import annotations

from dataclasses import dataclass

SATISFIED = "SATISFIED"
FAILED = "FAILED"
UNKNOWN = "UNKNOWN"
NOT_APPLICABLE = "NOT_APPLICABLE"

#: Requirement roles. Only ELIGIBILITY gates.
ROLE_ELIGIBILITY = "ELIGIBILITY"
ROLE_ADMINISTRATIVE = "ADMINISTRATIVE"
ROLE_INFORMATIONAL = "INFORMATIONAL"

#: Mandatory eligibility requirements that CAN be decided from a real project
#: figure the engine already has. These GATE: a production that genuinely
#: misses a statutory floor is genuinely ineligible.
_COMPUTABLE_ELIGIBILITY = ("min_total_budget_usd", "min_local_spend_usd")

#: Percentage-of-worldwide gateways: slug -> ((requirement id, categories the numerator and denominator are measured on, dollar floor,
#: worldwide share, whether a shortfall is a definite failure), ...). New York Tax Law 31 as amended by Part I of Chapter 59 of the Laws of 2025
#: (tax.ny.gov/legal/2025/pit-corp-changes.htm, read 2026-10-11): qualified post-production costs must be at least the LESSER of $1 million or
#: 75% of the total post-production cost; visual effects and animation costs at least the lesser of $500,000 or 10% of the total VFX and
#: animation cost. The page lists the two tests without saying whether they are cumulative, so the VFX shortfall is UNKNOWN (disclosed), not a
#: failure; the post test fails only when the worldwide figure is known and the local figure is below the lesser threshold.
_PERCENT_GATEWAYS = {
    "us_ny_post_production_credit": (
        ("ny_post_gateway", ("post_production", "sound", "vfx"), 1_000_000.0, 0.75, True),
        ("ny_vfx_gateway", ("vfx",), 500_000.0, 0.10, False),
    ),
}


def percent_gateway_minimum_qpe(slug, worldwide_category_spend_usd) -> float | None:
    """min(dollar floor, share x worldwide cost) for the program's FIRST (post) gateway, or None when the program has none or the worldwide
    figure is unknown (the dollar floor on the rate tier then stands)."""
    gateways = _PERCENT_GATEWAYS.get(slug)
    if not gateways or worldwide_category_spend_usd is None:
        return None
    _req, categories, dollar_floor, share, _definite = gateways[0]
    world = round(sum(worldwide_category_spend_usd.get(c, 0.0) for c in categories), 2)
    return round(min(dollar_floor, share * world), 2) if world > 0 else None


def _percent_gateway_evaluations(slug, category_spend_usd, worldwide_category_spend_usd):
    out = []
    for req_id, categories, dollar_floor, share, definite in _PERCENT_GATEWAYS[slug]:
        local = None if category_spend_usd is None else round(sum(category_spend_usd.get(c, 0.0) for c in categories), 2)
        world = None if worldwide_category_spend_usd is None else round(sum(worldwide_category_spend_usd.get(c, 0.0) for c in categories), 2)
        if world is not None and world <= 0.0 and req_id != "ny_post_gateway":
            out.append(RequirementEvaluation(req_id, ROLE_ELIGIBILITY, NOT_APPLICABLE, "no worldwide cost in this category"))
            continue
        if local is None or world is None:
            out.append(RequirementEvaluation(req_id, ROLE_ELIGIBILITY, UNKNOWN,
                f"lesser of ${dollar_floor:,.0f} or {share:.0%} of the worldwide cost; the worldwide figure is not available"))
            continue
        threshold = round(min(dollar_floor, share * world), 2)
        text = f"${local:,.0f} local vs the lesser of ${dollar_floor:,.0f} or {share:.0%} of ${world:,.0f} worldwide = ${threshold:,.0f}"
        if local + 0.01 >= threshold:
            out.append(RequirementEvaluation(req_id, ROLE_ELIGIBILITY, SATISFIED, text))
        else:
            out.append(RequirementEvaluation(req_id, ROLE_ELIGIBILITY, FAILED if definite else UNKNOWN,
                text + ("" if definite else "; whether this test is cumulative with the post test is not stated in the page read")))
    return out

#: Mandatory requirements that need a project FACT the engine does not derive
#: from a budget. These are recorded as explicit UNKNOWN and SURFACED, but
#: they do not gate. The distinction is deliberate and bounded:
#:
#:   * a COMPUTABLE THRESHOLD is a fact about the PRODUCTION (its budget, its
#:     local spend). Failing it is real ineligibility, so it gates.
#:   * entity formation and a local co-producer are things the producer DOES
#:     in the ordinary course of pursuing any program that asks for them.
#:     They are equally unconfirmed for every option at planning time, so
#:     gating on them removes the entire comparison while telling the producer
#:     nothing that distinguishes one jurisdiction from another.
#:   * SELECTIVITY IS ALREADY ADJUDICATED ELSEWHERE. allocation_type is not
#:     re-decided here: authority_coverage_registry already classifies
#:     genuinely non-guaranteed programs NON_GUARANTEED_SELECTIVE and blocks
#:     them (34 programs). A program the completed authority corpus left
#:     PRICEABLE_VALIDATED has been adjudicated as priceable, and silently
#:     re-blocking it from this bridge would contradict a closed decision.
#:
#: Measured consequence of the wider reading: gating on these as well removed
#: 41 of 101 priced FVD candidates and collapsed whole capabilities --
#: Lips lost treaty/co-production generation entirely, and Little Utopia's
#: baselines broke (28 test regressions). Cluster 10 ("do not break existing
#: correct behavior") and the co-production preservation gate both forbid
#: that. The requirement is therefore DISCLOSED, never silently satisfied,
#: which is what the doctrine actually protects against.
_DISCLOSED_ELIGIBILITY = (
    "local_entity_required",
    "local_coproducer_required",
    "min_shoot_days",
)

#: Process steps. Real and disclosed, but never a pricing gate -- see the
#: module docstring for why gating on them would be both uninformative and
#: destructive of the comparison.
_ADMINISTRATIVE = (
    "preapproval_mandatory",
    "audit_required",
    "cpa_or_approved_auditor_required",
    "completion_bond_required",
    "expenditure_before_approval_qualifies",
)

#: Allocation types that are not a guaranteed entitlement. A discretionary or
#: competitive allocation is awarded at the administrator's choice, so the
#: headline rate is not a deterministic producer economic (doctrine: a
#: conditional/competitive award is never an assumed award).
_NON_GUARANTEED_ALLOCATIONS = {"DISCRETIONARY", "COMPETITIVE", "SELECTIVE"}


@dataclass(frozen=True)
class RequirementEvaluation:
    requirement: str
    role: str
    state: str
    detail: str


@dataclass(frozen=True)
class RequirementsGateResult:
    program_slug: str
    evaluations: tuple[RequirementEvaluation, ...]

    @property
    def failed(self) -> tuple[RequirementEvaluation, ...]:
        return tuple(
            e for e in self.evaluations
            if e.role == ROLE_ELIGIBILITY and e.state == FAILED
        )

    @property
    def unresolved(self) -> tuple[RequirementEvaluation, ...]:
        return tuple(
            e for e in self.evaluations
            if e.role == ROLE_ELIGIBILITY and e.state == UNKNOWN
        )

    @property
    def blocks_deterministic_pricing(self) -> bool:
        return bool(self.failed or self.unresolved)

    def blocker_text(self, jurisdiction_code: str) -> str:
        failed = ", ".join(f"{e.requirement} ({e.detail})" for e in self.failed)
        unknown = ", ".join(f"{e.requirement} ({e.detail})" for e in self.unresolved)
        parts: list[str] = []
        if failed:
            parts.append(f"FAILED mandatory requirement(s): {failed}")
        if unknown:
            parts.append(f"UNRESOLVED mandatory requirement(s): {unknown}")
        return (
            f"{jurisdiction_code}/{self.program_slug}: "
            + "; ".join(parts)
            + ". A missing mandatory eligibility fact is not a satisfied one, so this "
            "segment is allocated and disclosed but carries NO deterministic incentive "
            "value until the requirement is resolved."
        )


def evaluate_requirements_gate(
    program_slug: str,
    *,
    segment_allocated_usd: float | None = None,
    gross_budget_usd: float | None = None,
    evidenced_facts: frozenset[str] | None = None,
    category_spend_usd: dict[str, float] | None = None,
    worldwide_category_spend_usd: dict[str, float] | None = None,
) -> RequirementsGateResult:
    """Adjudicate one program's mandatory requirements for one production.

    evidenced_facts names requirement keys the PROJECT has actually evidenced
    (e.g. a persisted fact confirming a local entity exists). Absent, nothing
    is assumed -- which is the entire point of the gate.
    """
    from app.data.program_requirements import get_program_requirements

    evidenced = evidenced_facts or frozenset()
    profile = get_program_requirements(program_slug)
    evaluations: list[RequirementEvaluation] = []

    if profile is None:
        # Absence of a profile is absence of a KNOWN requirement, not a
        # fabricated one. Nothing to gate on; other gates still apply.
        return RequirementsGateResult(program_slug, ())

    # ── computable eligibility thresholds ────────────────────────────────
    thresholds = {
        "min_total_budget_usd": gross_budget_usd,
        "min_local_spend_usd": segment_allocated_usd,
    }
    for requirement in _COMPUTABLE_ELIGIBILITY:
        threshold = getattr(profile, requirement, None)
        if requirement == "min_local_spend_usd" and program_slug in _PERCENT_GATEWAYS:
            evaluations.extend(_percent_gateway_evaluations(program_slug, category_spend_usd, worldwide_category_spend_usd))
            continue
        if not threshold:
            evaluations.append(RequirementEvaluation(
                requirement, ROLE_ELIGIBILITY, NOT_APPLICABLE,
                "program states no threshold",
            ))
            continue
        actual = thresholds.get(requirement)
        if actual is None:
            evaluations.append(RequirementEvaluation(
                requirement, ROLE_ELIGIBILITY, UNKNOWN,
                f"threshold ${threshold:,.0f}; production figure not available",
            ))
        elif actual + 0.01 < float(threshold):
            evaluations.append(RequirementEvaluation(
                requirement, ROLE_ELIGIBILITY, FAILED,
                f"${actual:,.0f} is below the ${float(threshold):,.0f} floor",
            ))
        else:
            evaluations.append(RequirementEvaluation(
                requirement, ROLE_ELIGIBILITY, SATISFIED,
                f"${actual:,.0f} meets the ${float(threshold):,.0f} floor",
            ))

    # ── a minimum on the production's total cost stated in a native currency (Alberta: CAD 499,999) ─
    native = getattr(profile, "min_total_budget_native", None)
    if native:
        from app.calculators.production_normalization import build_fx_context
        currency, amount = native
        rate = build_fx_context().rates.get(currency)
        if gross_budget_usd is None or not rate:
            evaluations.append(RequirementEvaluation(
                "min_total_budget_native", ROLE_ELIGIBILITY, UNKNOWN,
                f"threshold {currency} {float(amount):,.0f}; "
                + ("production figure not available" if rate else f"no {currency} rate on file to convert it")))
        else:
            floor_usd = float(amount) / float(rate)
            if gross_budget_usd + 0.01 < floor_usd:
                evaluations.append(RequirementEvaluation(
                    "min_total_budget_native", ROLE_ELIGIBILITY, FAILED,
                    f"${gross_budget_usd:,.0f} is below the {currency} {float(amount):,.0f} floor (${floor_usd:,.0f} at the canonical rate)"))
            else:
                evaluations.append(RequirementEvaluation(
                    "min_total_budget_native", ROLE_ELIGIBILITY, SATISFIED,
                    f"${gross_budget_usd:,.0f} meets the {currency} {float(amount):,.0f} floor (${floor_usd:,.0f} at the canonical rate)"))

    # ── eligibility facts the budget cannot decide: DISCLOSED, not gating ─
    for requirement in _DISCLOSED_ELIGIBILITY:
        value = getattr(profile, requirement, None)
        imposed = bool(value) if isinstance(value, bool) else value is not None
        if not imposed:
            continue
        evaluations.append(RequirementEvaluation(
            requirement, ROLE_ADMINISTRATIVE,
            SATISFIED if requirement in evidenced else UNKNOWN,
            "required by the program; no project fact confirms it — disclosed, "
            "never assumed satisfied",
        ))

    # ── allocation type: DISCLOSED. Selectivity is adjudicated by
    #    authority_coverage_registry (NON_GUARANTEED_SELECTIVE), not re-decided
    #    here; see _DISCLOSED_ELIGIBILITY's note.
    allocation_type = getattr(profile, "allocation_type", None)
    allocation_name = getattr(allocation_type, "name", None) or (
        str(allocation_type).rsplit(".", 1)[-1] if allocation_type else None
    )
    if allocation_name and allocation_name.upper() in _NON_GUARANTEED_ALLOCATIONS:
        evaluations.append(RequirementEvaluation(
            "allocation_type", ROLE_ADMINISTRATIVE, UNKNOWN,
            f"{allocation_name.lower()} allocation — award granted at the "
            "administrator's discretion; disclosed, and blocked upstream by the "
            "authority registry where that corpus adjudicated it non-guaranteed",
        ))

    # ── administrative steps: disclosed, never gating ────────────────────
    for requirement in _ADMINISTRATIVE:
        value = getattr(profile, requirement, None)
        if value is None:
            continue
        evaluations.append(RequirementEvaluation(
            requirement, ROLE_ADMINISTRATIVE,
            SATISFIED if requirement in evidenced else UNKNOWN,
            "process step required by the program; disclosed, not a pricing gate",
        ))

    return RequirementsGateResult(program_slug, tuple(evaluations))
