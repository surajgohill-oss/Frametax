"""
canonical_evaluation.py

THE canonical served evaluation runtime — Phase 2 cutover.

Supersedes `app/services/project_evaluation.py`'s run_full_analysis-backed
path (commit 87440df). bca893a proved that engine is the WRONG one for
served project economics: ENGINE_VERSION 0.1.0, zero references to any
canonical layer (program_spend_rules, program_rate_rules,
authority_coverage_registry, qualification_model, production_allocation,
allocation_pricing), and $1.12M off Little Utopia's accepted NPC when run
against its real budget.

This module builds NO new economics. Every calculation step is reused
byte-for-byte from the validated calculators; only the INPUT ASSEMBLY is
new, and only because it was previously hand-written per project
(`app/demo/little_utopia_state.py`) rather than derived from generic
persisted rows.

Pipeline:

    canonical_project_economics.build_project_economic_inputs()  (bca893a)
      -> derive_production_requirements() + discover_executable_jurisdictions()
         (Phase 6, already generic — app.calculators.production_discovery)
      -> per candidate (home baseline + discovered alternatives):
           derive_qualification_register()   (canonical, generic)
           derive_account_allocation()        (canonical, generic)
           price_allocated_structure()        (canonical, generic)
      -> rank_allocated_structures()          (canonical, generic)
      -> persist ProductionStructure / StructureCalculationResult
      -> one response shape, read back by _summarize_evaluation()

The exact two-pass rate-resolution pattern (register at rate=0.0 to get
a rate-independent QPE classification, then `resolve_program_rate` with
that QPE, then reprice at the resolved rate) and `program_territorial_text
=None` for any program without curated territorial-text evidence are both
reused unchanged from `app.demo.little_utopia_state
.build_alternative_jurisdiction_comparisons` / `qualification_model
.build_little_utopia_register_for_jurisdiction` — the established,
already-served pattern for the vast majority of Little Utopia's own
alternative-jurisdiction comparisons (only 3 of ~30 curate territorial
text; the rest already run with None).

MFNI (regional production-cost normalization) is explicitly NOT applied
here — local_cost_delta_usd is always 0.0, and every persisted result
discloses that limitation. Travel/FX normalization are likewise omitted
generically (no per-project travel/FX input exists yet outside Little
Utopia's own hand-built fixtures) and folded into the same disclosure
rather than silently assumed zero without comment.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.allocation_pricing import price_allocated_structure, rank_allocated_structures
from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.calculators.production_discovery import discover_executable_jurisdictions
from app.calculators.production_requirements import (
    derive_production_requirements,
    jurisdiction_capability_profile,
)
from app.calculators.qualification_derivation import derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.authority_coverage_registry import coverage_state as _coverage_state
from app.data.program_rate_rules import (
    RATE_FAILURE_NO_RULES,
    classify_rate_resolution_failure,
    resolve_program_rate,
)
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services.canonical_project_economics import (
    FACT_STATE_UNKNOWN,
    ProjectEconomicInputs,
    build_physical_requirements,
    build_project_economic_inputs,
    production_facts_for,
)

# Global Priceability Optimizer Restoration: bumped so every project's
# persisted StructureCalculationResult rows are treated as stale and
# regenerated. No candidate-generation/allocation/pricing LOGIC changed in
# this file -- the version bump exists purely to invalidate cached results
# from before the authority_coverage_registry.py Georgia veto correction
# (georgia_eiia/us_ga_film_credit rows removed) and the canonical_program_
# identity.py jurisdiction_code binding fix, both of which are read at
# discovery time but are NOT part of `_compute_fingerprint(inputs)` (that
# fingerprint covers project-specific economic inputs, not registry
# contents) and would otherwise silently keep serving pre-fix results.
# Global Economic Data + Base Pricing, batch 1: 8 more programs promoted
# PARSED -> VERIFIED and their coverage vetoes removed (see authority_
# coverage_registry.py's correction note). Cache-invalidation bump only.
# Global Economic Data + Base Pricing, batch 2: sa_film_commission_rebate
# and si_cash_rebate promoted PARSED -> VERIFIED, coverage vetoes
# removed. Cache-invalidation bump only.
ENGINE_VERSION = "canonical-1.12.0"

LIMITATION_NOTE = (
    "Regional production-cost normalization (MFNI) and generic travel/FX "
    "normalization are not yet applied to this comparison — every figure "
    "uses this production's own nominal budget amounts and statutory "
    "incentive rate only."
)

#: Why the baseline structure is always the served "winner" in this phase,
#: never a relocation candidate — see the module-level note below.
RELOCATION_COMPARABILITY_NOTE = (
    "This structure's cost omits real relocation-specific costs (travel, "
    "in-kind post-production replacement) that are not yet computed "
    "generically for any project. Its NPC is therefore NOT a fair, complete "
    "comparison against the production's own base jurisdiction, which needs "
    "no such adjustment by construction. Never treated as beating the "
    "baseline until relocation costs are modeled generically."
)

#: Candidate accounting terminal states (Part N/K).
STATUS_PRICED = "PRICED"
STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT = "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
STATUS_RULE_REJECTED = "RULE_REJECTED"
STATUS_FEASIBILITY_REVIEW_REQUIRED = "FEASIBILITY_REVIEW_REQUIRED"


def _compute_fingerprint(inputs: ProjectEconomicInputs) -> str:
    import hashlib
    import json

    payload = {
        "gross_budget_usd": inputs.gross_budget_usd,
        "jurisdiction_code": inputs.jurisdiction_code,
        "production_type": inputs.production_type,
        "lines": sorted(
            (line.account_code, line.description, line.amount_usd, line.spend_category)
            for line in inputs.budget_lines
        ),
        "accounts_outside_jurisdiction": sorted(inputs.accounts_outside_jurisdiction),
        "offshore_payroll_accounts": sorted(inputs.offshore_payroll_accounts),
    }
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _price_candidate(
    inputs: ProjectEconomicInputs, jurisdiction_code: str, program_slug: str,
):
    """The established two-pass pattern, generalized: build a rate-
    independent register to classify QPE, resolve the program's real
    statutory rate for that QPE, then price at the resolved rate. Returns
    (pricing, register, rate_resolution) or (None, None, None) if the
    program has no rate rules that resolve for this production."""
    facts = production_facts_for(inputs, jurisdiction_code=jurisdiction_code)
    register_probe = derive_qualification_register(
        inputs.budget_lines, program_slug=program_slug, facts=facts,
        rate=0.0, program_territorial_text=None,
    )
    qpe = round(sum(
        a.amount_usd for a in register_probe if a.state == QualificationState.QUALIFIES
    ), 2)

    rr = resolve_program_rate(program_slug, production_type=inputs.production_type, qpe_usd=qpe)
    if rr is None:
        return None, register_probe, None

    register = derive_qualification_register(
        inputs.budget_lines, program_slug=program_slug, facts=facts,
        rate=rr.modeled_rate, program_territorial_text=None,
    )

    spec = StructureSpec(
        structure_id=f"CANON-{jurisdiction_code}",
        structure_type=("single_country" if jurisdiction_code == inputs.jurisdiction_code else "full_relocation"),
        label=(
            f"{jurisdiction_code} — production's current base"
            if jurisdiction_code == inputs.jurisdiction_code
            else f"Full relocation to {jurisdiction_code}"
        ),
        primary_jurisdiction=jurisdiction_code,
        participants=(jurisdiction_code,),
        incentive_programs={jurisdiction_code: program_slug},
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines,
        spend_category_by_code=inputs.spend_category_by_code,
        spec=spec,
        stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    pricing = price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=inputs.spend_category_by_code,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        gross_budget_usd=inputs.gross_budget_usd,
        travel_incremental_delta_usd=0.0,
        fx_delta_usd=None,
        inkind_replacement_delta_usd=0.0,
        local_cost_delta_usd=0.0,
        production_type=inputs.production_type,
    )
    return pricing, register, rr


def _capability_only_status(examination) -> tuple[str, str, str]:
    """Real terminal status for a capability_only candidate (Codex Defect
    4) — reads fields discover_executable_jurisdictions() already computed
    (has_doctrine, has_rate_rules, resolves_for_production, program_slug)
    plus the SAME authority-coverage-registry lookup discovery itself
    already consulted for this program. Never re-evaluates a rule or a
    coverage decision; only classifies the terminal state that was already
    reached. Returns (candidate_status, rejection_reason_class, reason)."""
    if examination is None:
        return (
            STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT, "AUTHORITY_INSUFFICIENT",
            "Incentive model not yet classified for this program.",
        )
    state = _coverage_state(examination.program_slug)
    if state == "UNPRICEABLE_AUTHORITY_INSUFFICIENT":
        # The registry's OWN explicit adjudication of "no defensible
        # authority" for this program — even where discovery's has_doctrine/
        # has_rate_rules still read True from stale classified data (the
        # completed primary-authority audit overrides that staleness).
        # Same terminal status as "no rules classified at all", never a
        # different bucket for the same underlying cause.
        return (STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT, state, examination.reason)
    if state not in ("PRICEABLE_VALIDATED",):
        # NON_GUARANTEED_SELECTIVE / NON_ECONOMIC / SUPERSEDED / DUPLICATE —
        # the completed primary-authority corpus already adjudicated this
        # program as blocked for a reason OTHER than missing data; never
        # flattened into "authority insufficient".
        return (
            STATUS_FEASIBILITY_REVIEW_REQUIRED, state,
            f"{examination.reason} (authority_coverage_registry: {state})",
        )
    if examination.has_doctrine and examination.has_rate_rules and not examination.resolves_for_production:
        # Real statutory rate rules exist for this program; they simply do
        # not resolve for this production's type/QPE (a genuine threshold/
        # rule rejection — e.g. a minimum-QPE gate) — never the same as
        # "no authority data exists".
        return (
            STATUS_RULE_REJECTED, "STATUTORY_CONDITIONS_UNMET",
            examination.reason,
        )
    return (STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT, "AUTHORITY_INSUFFICIENT", examination.reason)


#: Canonical authority substrate + feasibility boundary repair, Task 1/2 —
#: PRODUCTION FEASIBILITY (how suitable a jurisdiction is for the creative/
#: logistical requirements) is a permanently separate concept from ECONOMIC
#: DISCOVERY/ELIGIBILITY (whether a defensible incentive can be priced).
#: The prior FVD canonical input assembly repair correctly wired real SA-1
#: script/location data into `derive_production_requirements()`, but then
#: fed it into `discover_executable_jurisdictions()` AS THE gate that
#: decides whether a jurisdiction even reaches structure generation --
#: conflating a soft, informational production-fit signal (a landlocked
#: jurisdiction cannot host a Mediterranean sea-shore scene) with a hard
#: statutory/program eligibility failure. That is corrected here: a
#: SEPARATE discovery pass with the real requirements supplies feasibility
#: DISCLOSURE only (never used to reject a candidate); economic candidate
#: GENERATION uses the same empty-requirements discovery pass used before
#: SA-1 requirements existed, so nothing is removed from the economic
#: universe on capability grounds alone. See evaluate_project() below.
FEASIBILITY_STRONG = "STRONG"
FEASIBILITY_WORKABLE = "WORKABLE"
FEASIBILITY_WEAK = "WEAK"
FEASIBILITY_UNKNOWN = "UNKNOWN"

#: Capability token -> short feasibility reason code. Deterministic,
#: mechanical labeling of the SAME capability vocabulary
#: production_requirements.py already defines -- no new capability
#: concept, no invented reason.
_CAPABILITY_TO_FEASIBILITY_REASON = {
    "open_water_filming": "MARINE_MISMATCH",
    "marine_filming": "MARINE_MISMATCH",
    "underwater_filming": "MARINE_MISMATCH",
    "water_tanks": "MARINE_MISMATCH",
    "desert_environments": "LOCATION_MISMATCH",
    "snow_environments": "LOCATION_MISMATCH",
}
#: marine_suitability values (jurisdiction_comparison.py, unmodified) that
#: read as a genuinely strong production fit when marine capability is
#: actually required -- distinct from merely "workable."
_STRONG_MARINE_SUITABILITY = {"strong", "excellent"}


def _feasibility_status(examination, requirements) -> tuple[str, list[str]]:
    """Classifies ONE jurisdiction's production feasibility from the
    real-requirements discovery examination. Never used to reject a
    candidate from economic discovery -- see the module note above."""
    if examination is None or not examination.has_capability_data:
        return FEASIBILITY_UNKNOWN, []
    if not examination.production_capable:
        reasons = [
            _CAPABILITY_TO_FEASIBILITY_REASON.get(token, "LOCATION_MISMATCH")
            for token in sorted(requirements.required_capabilities)
        ] or ["CAPABILITY_MISMATCH"]
        # Dedupe while preserving order.
        return FEASIBILITY_WEAK, list(dict.fromkeys(reasons))
    if "open_water_filming" in requirements.required_capabilities:
        profile = jurisdiction_capability_profile(examination.jurisdiction_code)
        if str(profile.marine_suitability or "").lower() in _STRONG_MARINE_SUITABILITY:
            return FEASIBILITY_STRONG, []
    return FEASIBILITY_WORKABLE, []


def _segment_dicts(pricing) -> list[dict]:
    """Full, generic serialization of `pricing.segments` — the SAME
    SegmentEconomics objects `little_utopia_state.build_allocated_structures`
    already serializes via its own `_seg_dict` (byte-identical field set and
    naming, see qualification_trace below). Canonical served wiring repair
    (Codex Defect 3): previously reduced to a handful of fields, silently
    dropping cap/band/confirmation/floor-ceiling/register-trace data the
    calculator already computed — this is serialization only, no new
    economics, every value already existed on `pricing.segments`."""
    return [
        {
            "jurisdiction_code": s.jurisdiction_code,
            "program_slug": s.program_slug,
            "claims_incentive": s.claims_incentive,
            "executable": s.executable,
            "allocated_usd": s.allocated_usd,
            "account_codes": list(s.account_codes),
            "qpe_usd": s.qpe_usd,
            "excluded_usd": s.excluded_usd,
            "unresolved_usd": s.unresolved_usd,
            "rate_floor": s.rate_floor,
            "rate_ceiling": s.rate_ceiling,
            "is_band_ceiling": s.is_band_ceiling,
            "statutory_basis": s.statutory_basis,
            "doctrine": s.doctrine,
            "incentive_floor_usd": s.incentive_floor_usd,
            "incentive_ceiling_usd": s.incentive_ceiling_usd,
            "ceiling_requires_confirmation": s.ceiling_requires_confirmation,
            "qpe_cap_applied_usd": s.qpe_cap_applied_usd,
            "blockers": list(s.blockers),
            "qualification_trace": list(s.register_trace),
            "notes": list(s.notes),
        }
        for s in pricing.segments
    ]


async def evaluate_project(session: AsyncSession, project_id) -> dict:
    """The canonical served evaluation entry point for any project."""
    project = await session.get(Project, project_id)
    if project is None:
        return {"status": "PROJECT_NOT_FOUND"}

    econ = await build_project_economic_inputs(session, project_id)
    if not econ.ok:
        status = (
            "BUDGET_REQUIRED_FOR_CURRENT_EVALUATION"
            if any("BUDGET_MISSING" in b for b in econ.blockers)
            else "BLOCKED_INCOMPLETE_INPUTS"
        )
        return {"status": status, "blockers": econ.blockers}
    inputs = econ.inputs
    fingerprint = _compute_fingerprint(inputs)

    existing = (await session.execute(
        select(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.input_fingerprint == fingerprint,
            # ENGINE_VERSION is part of freshness, not just the fingerprint:
            # a code change that enriches calculation_trace_json (e.g. the
            # 1.1.0 segments addition) must regenerate rows even when the
            # underlying budget/jurisdiction inputs are unchanged — the
            # fingerprint alone can't detect that the SHAPE of what gets
            # persisted changed, only that the ECONOMIC INPUTS didn't.
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
    )).scalars().first()
    if existing is not None:
        return await _summarize_evaluation(session, project, inputs, fingerprint, reused=True)

    # Any prior evaluation for this project (a different fingerprint or an
    # older engine_version — a new budget version, or a stale result from
    # before this phase) is superseded, never left to render as current.
    # Its rows are not destroyed — they simply drop out of the "current"
    # query above, exactly as an unchanged Document/DocumentVersion keeps
    # prior versions rather than deleting them (see is_current elsewhere
    # in this codebase for the same convention).

    # FVD canonical input assembly repair (superseding the prior
    # CANONICAL_SERVED_WIRING_REPAIR.md Defect 1 disclosure-only note
    # below): derive_production_requirements() previously always received
    # {} regardless of real, persisted SA-1 script data. build_physical_
    # requirements() reads SA-1's own persisted ProjectLocationRequirement/
    # ProductionRequirement rows directly (read-only, no side effects) and
    # runs scripted-location text through the existing, generic
    # abstract_location() keyword ontology -- ontology-defined but never
    # wired to any consumer until this repair. No AI interpretation, no
    # invented quantities; a location string with no ontology hit and a
    # project with no SCRIPTED_LOCATION/PERIOD_REFERENCE rows on file both
    # still resolve to the same honest empty signal as before.
    #
    # Canonical authority substrate + feasibility boundary repair, Task 1/2
    # (this is now the ONLY consumer of `requirements` below): an earlier
    # version of this repair fed `requirements` directly into the discovery
    # pass that decides which jurisdictions become economic candidates --
    # conflating a soft production-feasibility signal (a landlocked
    # jurisdiction cannot host a Mediterranean sea-shore scene) with a hard
    # statutory/program eligibility failure, and silently removing 21
    # otherwise economically evaluable jurisdictions. `requirements` is now
    # used ONLY for the separate feasibility_discovery pass below --
    # disclosure, never rejection.
    requirements = derive_production_requirements(
        await build_physical_requirements(session, project_id)
    )
    # Canonical authority substrate + feasibility boundary repair, Task 1/2:
    # TWO discovery passes, deliberately. `feasibility_discovery` runs the
    # real, SA-1-derived requirements through discover_executable_
    # jurisdictions() to obtain each jurisdiction's genuine capability
    # examination (production_capable, capability_reasons) -- disclosure
    # only, NEVER consulted below to decide which jurisdictions become
    # candidates. `discovery` (economic candidate generation) intentionally
    # uses the SAME empty-requirements pass used before real requirements
    # existed, so a soft production-feasibility mismatch can never remove a
    # jurisdiction from the economic universe -- only an actual authority/
    # rate/threshold failure can. discover_executable_jurisdictions() is a
    # pure, side-effect-free function; calling it twice is inexpensive and
    # keeps the two concerns from ever sharing one classification.
    feasibility_discovery = discover_executable_jurisdictions(
        requirements=requirements,
        production_type=inputs.production_type,
        qpe_usd=inputs.gross_budget_usd,
        home_code=inputs.jurisdiction_code,
    )
    feasibility_by_code = {e.jurisdiction_code: e for e in feasibility_discovery.examinations}
    discovery = discover_executable_jurisdictions(
        requirements=derive_production_requirements({}),
        production_type=inputs.production_type,
        qpe_usd=inputs.gross_budget_usd,
        home_code=inputs.jurisdiction_code,
    )

    candidates: list[tuple[str, str, str]] = []  # (code, program_slug, discovery_classification)
    home_program = next((s for c, s in discovery.accepted if c == inputs.jurisdiction_code), None)
    if home_program:
        candidates.append((inputs.jurisdiction_code, home_program, "incentive_ready"))
    for code, slug in discovery.accepted_alternatives(inputs.jurisdiction_code):
        candidates.append((code, slug, "incentive_ready"))
    for code in discovery.metrics.get("capability_only_jurisdictions", []):
        examination = next((e for e in discovery.examinations if e.jurisdiction_code == code), None)
        if examination and examination.program_slug:
            candidates.append((code, examination.program_slug, "capability_only"))

    jurisdiction_rows = (await session.execute(select(Jurisdiction))).scalars().all()
    jurisdiction_by_code = {j.code: j for j in jurisdiction_rows}

    for code, program_slug, classification in candidates:
        jurisdiction = jurisdiction_by_code.get(code)
        structure = ProductionStructure(
            id=uuid.uuid4(),
            project_id=project.id,
            name=(
                f"{code} — production's current base"
                if code == inputs.jurisdiction_code else f"Full relocation to {code}"
            ),
            description=(
                "The production's own confirmed base jurisdiction, priced as-is."
                if code == inputs.jurisdiction_code else
                "Whole production relocated; nominal budget unchanged (no regional "
                "cost normalization applied)."
            ),
            jurisdiction_allocations=(
                [{"jurisdiction_id": str(jurisdiction.id), "shoot_pct": 100, "budget_pct": 100}]
                if jurisdiction else []
            ),
            claimed_program_ids=[],
        )
        session.add(structure)
        await session.flush()

        # Task 1/2 — feasibility disclosure computed once per candidate,
        # from the real-requirements examination, attached to every terminal
        # branch below. Never consulted for the classification/candidates
        # decisions above — see the module note on _feasibility_status().
        feasibility_status, feasibility_reasons = _feasibility_status(
            feasibility_by_code.get(code), requirements,
        )

        if classification == "capability_only":
            # Discovery already knows this program has no priceable route —
            # re-attempting pricing would only rediscover the same fact via
            # a failed derive_qualification_register call. Codex Defect 4:
            # the terminal cause is classified from discovery's own already-
            # computed fields (never re-evaluated), not flattened to a
            # single generic status.
            examination = next((e for e in discovery.examinations if e.jurisdiction_code == code), None)
            candidate_status, rejection_reason_class, reason = _capability_only_status(examination)
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                calculation_trace_json={
                    "candidate_status": candidate_status,
                    "rejection_reason_class": rejection_reason_class,
                    "discovery_classification": classification,
                    "program_slug": examination.program_slug if examination else program_slug,
                    "reason": reason,
                    "structure_type": "single_country" if code == inputs.jurisdiction_code else "full_relocation",
                    "primary_jurisdiction": code,
                    "feasibility_status": feasibility_status,
                    "feasibility_reasons": feasibility_reasons,
                },
                input_fingerprint=fingerprint,
            ))
            continue

        pricing, register, rate_resolution = _price_candidate(inputs, code, program_slug)
        if pricing is None or not pricing.is_fully_priced:
            if pricing is None:
                # Codex Defect 4: resolve_program_rate() returned None for
                # one of two materially different reasons — classify which,
                # by mirroring its own eligibility gate read-only (no rule
                # re-evaluation, no changed outcome).
                qpe_for_probe = round(sum(
                    a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
                ), 2)
                failure = classify_rate_resolution_failure(
                    program_slug, inputs.production_type, qpe_for_probe,
                )
                if failure == RATE_FAILURE_NO_RULES:
                    candidate_status = STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT
                    rejection_reason_class = "AUTHORITY_INSUFFICIENT"
                    reason = "No statutory rate rules exist for this program."
                else:
                    candidate_status = STATUS_RULE_REJECTED
                    rejection_reason_class = "STATUTORY_CONDITIONS_UNMET"
                    reason = (
                        f"Statutory rate rules exist for this program but do not resolve "
                        f"for this production's type/QPE (${qpe_for_probe:,.2f})."
                    )
            else:
                candidate_status = STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT
                rejection_reason_class = "PRICING_BLOCKED"
                reason = "; ".join(pricing.blockers) or "Not fully priced."
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                calculation_trace_json={
                    "candidate_status": candidate_status,
                    "rejection_reason_class": rejection_reason_class,
                    "discovery_classification": classification,
                    "program_slug": program_slug,
                    "reason": reason,
                    "structure_type": "single_country" if code == inputs.jurisdiction_code else "full_relocation",
                    "primary_jurisdiction": code,
                    "feasibility_status": feasibility_status,
                    "feasibility_reasons": feasibility_reasons,
                },
                input_fingerprint=fingerprint,
            ))
            continue

        is_baseline = code == inputs.jurisdiction_code
        warnings = [LIMITATION_NOTE] if is_baseline else [LIMITATION_NOTE, RELOCATION_COMPARABILITY_NOTE]
        # FVD canonical input assembly repair, Task 2 — UNKNOWN territorial
        # facts stay visibly provisional rather than being silently absorbed
        # as though "confirmed none." An absent ProjectFact still resolves
        # to an empty account set for the qualification ladder itself (the
        # only safe input a set-membership check can be given without
        # inventing evidence — see _fact_account_set), but the SERVED result
        # must not read as equivalent to a project that actually confirmed
        # no accounts are stated outside its base jurisdiction. When either
        # territorial fact was never stated at all, this candidate's QPE is
        # flagged has_unverified_inputs=True with an explicit warning —
        # blocking in the sense of requiring confirmation before being
        # treated as final, never blocking the evaluation itself.
        territorial_state_unknown = (
            inputs.accounts_outside_jurisdiction_state == FACT_STATE_UNKNOWN
            or inputs.offshore_payroll_accounts_state == FACT_STATE_UNKNOWN
        )
        if territorial_state_unknown:
            warnings = warnings + [
                "UNKNOWN, not KNOWN EMPTY: no project fact has ever stated which "
                "accounts (if any) are incurred outside the base jurisdiction or "
                "routed through offshore payroll. This QPE assumes none are — the "
                "only input a set-membership check can be given without inventing "
                "evidence — but that assumption is unconfirmed, not verified."
            ]
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd,
            total_incentive_value_usd=pricing.selected_incentive_usd,
            true_net_cost_usd=pricing.npc_verified_usd,
            risk_adjusted_net_cost_usd=pricing.npc_with_adjustments_usd,
            has_unverified_inputs=territorial_state_unknown, warnings=warnings,
            calculation_trace_json={
                "candidate_status": STATUS_PRICED,
                "discovery_classification": classification,
                "modeled_rate": rate_resolution.modeled_rate,
                "rate_basis": rate_resolution.basis,
                "qualifying_spend_usd": round(sum(
                    a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
                ), 2),
                "is_baseline": is_baseline,
                # False for every non-baseline structure in this phase: no
                # relocation cost (travel, in-kind replacement) is computed
                # generically yet, so its NPC is priced but not eligible to
                # be selected as the served "winner" over the baseline —
                # see RELOCATION_COMPARABILITY_NOTE. Baseline needs no such
                # adjustment by construction (no relocation occurs).
                "relocation_cost_normalized": is_baseline,
                # Codex Defect 2 — economic priceability (candidate_status
                # == PRICED, always true here) and regional comparability
                # are two different states. is_directly_comparable is the
                # SAME fact as relocation_cost_normalized under an
                # unambiguous name, so a downstream reader never has to
                # infer "comparable" from a field named for something else.
                # is_fully_priced (this candidate priced successfully) must
                # never be overwritten by this — see canonical_production_view.py.
                "is_directly_comparable": is_baseline,
                "structure_type": pricing.structure_type,
                "primary_jurisdiction": pricing.primary_jurisdiction,
                "selected_incentive_usd": pricing.selected_incentive_usd,
                "npc_verified_usd": pricing.npc_verified_usd,
                "npc_conservative_usd": pricing.npc_verified_usd,
                "gross_budget_usd": pricing.gross_budget_usd,
                "segments": _segment_dicts(pricing),
                # Disclosure (does not change this candidate's own
                # qualification outcome — the ladder still receives the same
                # empty-set input either way; see the has_unverified_inputs/
                # warnings block above for how UNKNOWN is now surfaced as
                # provisional): whether the two territorial ProjectFact keys
                # were ever actually stated for this project, and how many
                # real SA-1 ProductionRequirement rows exist on file.
                # SCRIPTED_LOCATION and PERIOD_REFERENCE rows ARE now
                # consumed generically (build_physical_requirements()) for
                # the feasibility_status/feasibility_reasons disclosure
                # below (never for economic discovery/eligibility — see the
                # canonical authority substrate + feasibility boundary
                # repair module note above _feasibility_status()) — this
                # count still includes CHARACTER/EXPLICIT_VEHICLE/
                # EXPLICIT_ANIMAL/EXPLICIT_WEAPON/EXPLICIT_MINOR rows, which
                # have no corresponding capability vocabulary in
                # derive_production_requirements() and remain unmapped.
                "accounts_outside_jurisdiction_state": inputs.accounts_outside_jurisdiction_state,
                "offshore_payroll_accounts_state": inputs.offshore_payroll_accounts_state,
                "production_requirements_on_file": inputs.production_requirements_on_file,
                # Task 1/2 — production feasibility, disclosed alongside a
                # PRICED result, never used to have prevented it from being
                # priced. A jurisdiction can be economically PRICED and
                # feasibility WEAK at the same time (e.g. a landlocked
                # jurisdiction for a marine-heavy screenplay) — the two
                # concepts are independent by design.
                "feasibility_status": feasibility_status,
                "feasibility_reasons": feasibility_reasons,
            },
            input_fingerprint=fingerprint,
        ))

    await session.commit()
    summary = await _summarize_evaluation(session, project, inputs, fingerprint, reused=False)
    summary["discovery_examined"] = len(discovery.examinations)
    summary["discovery_rejected"] = discovery.metrics.get("rejected_count", 0)
    summary["discovery_capability_only"] = discovery.metrics.get("capability_only_count", 0)
    return summary


async def _summarize_evaluation(
    session: AsyncSession, project: Project, inputs: ProjectEconomicInputs,
    fingerprint: str, *, reused: bool,
) -> dict:
    """Read back the persisted, fingerprint-matched rows and rank them.
    Never recomputes — purely a read + rank of what is already committed."""
    rows = (await session.execute(
        select(ProductionStructure, StructureCalculationResult)
        .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.input_fingerprint == fingerprint,
            # Same freshness rule as the "existing" check above: a
            # fingerprint match alone isn't enough once an older
            # engine_version's rows can coexist with a freshly regenerated
            # set for the SAME inputs — only the current engine's rows are
            # "the" evaluation; older ones are superseded history, still in
            # the table, never queried as current.
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
    )).all()

    priced = [(s, r) for s, r in rows if r.true_net_cost_usd is not None]
    unpriced = [(s, r) for s, r in rows if r.true_net_cost_usd is None]
    priced.sort(key=lambda pair: float(pair[1].true_net_cost_usd))

    def _is_baseline(pair) -> bool:
        return bool((pair[1].calculation_trace_json or {}).get("is_baseline"))

    baseline_pair = next((pair for pair in priced if _is_baseline(pair)), None)
    # The served "winner"/top_result is the baseline whenever it is priced —
    # never a relocation candidate, in this phase, regardless of whether one
    # shows a lower NPC (see RELOCATION_COMPARABILITY_NOTE: that NPC omits
    # real relocation costs no project has generic data for yet, so it is
    # never a fair comparison to declare a winner over the baseline). Only
    # if the baseline itself could not be priced does the top-ranked
    # (still honestly computed, still disclosed) alternative stand in.
    top_pair = baseline_pair or (priced[0] if priced else None)

    # Repoint leading_structure_id whenever it's unset OR currently points
    # at a structure NOT produced by this canonical engine (a stale legacy
    # result — e.g. the run_full_analysis-backed rows from commit 87440df —
    # must never keep rendering as the current evaluation). Never
    # overwrites a CURRENT canonical result on a repeat/idempotent run.
    if top_pair:
        needs_repoint = project.leading_structure_id is None
        if not needs_repoint and project.leading_structure_id != top_pair[0].id:
            current_structure = await session.get(ProductionStructure, project.leading_structure_id)
            current_result = (
                (await session.execute(
                    select(StructureCalculationResult)
                    .where(StructureCalculationResult.structure_id == project.leading_structure_id)
                    .order_by(StructureCalculationResult.created_at.desc())
                )).scalars().first()
                if current_structure is not None else None
            )
            if current_structure is None or current_result is None or current_result.engine_version != ENGINE_VERSION:
                needs_repoint = True
        if needs_repoint:
            project.leading_structure_id = top_pair[0].id
            await session.commit()

    def _entry(structure, result):
        trace = result.calculation_trace_json or {}
        return {
            "structure_id": str(structure.id),
            "name": structure.name,
            "candidate_status": trace.get("candidate_status"),
            "true_net_cost_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
            "total_incentive_value_usd": (
                float(result.total_incentive_value_usd) if result.total_incentive_value_usd is not None else None
            ),
            "is_baseline": trace.get("is_baseline", False),
            "relocation_cost_normalized": trace.get("relocation_cost_normalized", False),
            "reason": trace.get("reason"),
        }

    return {
        "status": "EVALUATION_REUSED" if reused else "EVALUATION_COMPLETE",
        "engine_version": ENGINE_VERSION,
        "state_fingerprint": fingerprint,
        "gross_budget_usd": inputs.gross_budget_usd,
        "base_jurisdiction_code": inputs.jurisdiction_code,
        "priced_count": len(priced),
        "unpriceable_count": len(unpriced),
        "baseline": _entry(*baseline_pair) if baseline_pair else None,
        "top_result": _entry(*top_pair) if top_pair else None,
        "ranked": [_entry(s, r) for s, r in priced],
        "unpriceable": [_entry(s, r) for s, r in unpriced],
        "mfni_limitation": LIMITATION_NOTE,
        "relocation_comparability_limitation": RELOCATION_COMPARABILITY_NOTE,
    }
