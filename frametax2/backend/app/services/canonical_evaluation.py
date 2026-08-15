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
from app.calculators.production_requirements import derive_production_requirements
from app.calculators.qualification_derivation import derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.program_rate_rules import resolve_program_rate
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services.canonical_project_economics import (
    ProjectEconomicInputs,
    build_project_economic_inputs,
    production_facts_for,
)

ENGINE_VERSION = "canonical-1.1.0"

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
    facts = production_facts_for(inputs)
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


def _segment_dicts(pricing) -> list[dict]:
    """Light, generic serialization of `pricing.segments` — the SAME
    SegmentEconomics objects `little_utopia_state.build_allocated_structures`
    already serializes via its own `_seg_dict`, reduced to the fields the
    mature UI's Globe/Budget-Rail cross-referencing actually reads
    (jurisdiction_code, qpe_usd, account_codes — see globeData.js and
    BudgetRail.jsx). Exposes more of what price_allocated_structure already
    computed for this call; adds no new economics."""
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
            "rate_floor": s.rate_floor,
            "rate_ceiling": s.rate_ceiling,
            "doctrine": s.doctrine,
            "blockers": list(s.blockers),
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

    requirements = derive_production_requirements({})
    discovery = discover_executable_jurisdictions(
        requirements=requirements,
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

        if classification == "capability_only":
            # Discovery already knows this program has no classified
            # doctrine/rate — re-attempting pricing would only rediscover
            # the same fact via a failed derive_qualification_register
            # call. Recorded directly with discovery's own stated reason,
            # never silently dropped.
            examination = next((e for e in discovery.examinations if e.jurisdiction_code == code), None)
            reason = examination.reason if examination else "Incentive model not yet classified for this program."
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                calculation_trace_json={
                    "candidate_status": STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT,
                    "discovery_classification": classification,
                    "reason": reason,
                    "structure_type": "single_country" if code == inputs.jurisdiction_code else "full_relocation",
                    "primary_jurisdiction": code,
                },
                input_fingerprint=fingerprint,
            ))
            continue

        pricing, register, rate_resolution = _price_candidate(inputs, code, program_slug)
        if pricing is None or not pricing.is_fully_priced:
            candidate_status = STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT
            reason = (
                "Statutory rate rules did not resolve for this production/QPE."
                if pricing is None else "; ".join(pricing.blockers) or "Not fully priced."
            )
            session.add(StructureCalculationResult(
                id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
                total_budget_usd=inputs.gross_budget_usd, total_incentive_value_usd=None,
                true_net_cost_usd=None, risk_adjusted_net_cost_usd=None,
                has_unverified_inputs=True, warnings=[LIMITATION_NOTE],
                calculation_trace_json={
                    "candidate_status": candidate_status,
                    "discovery_classification": classification, "reason": reason,
                    "structure_type": "single_country" if code == inputs.jurisdiction_code else "full_relocation",
                    "primary_jurisdiction": code,
                },
                input_fingerprint=fingerprint,
            ))
            continue

        is_baseline = code == inputs.jurisdiction_code
        warnings = [LIMITATION_NOTE] if is_baseline else [LIMITATION_NOTE, RELOCATION_COMPARABILITY_NOTE]
        session.add(StructureCalculationResult(
            id=uuid.uuid4(), structure_id=structure.id, engine_version=ENGINE_VERSION,
            total_budget_usd=inputs.gross_budget_usd,
            total_incentive_value_usd=pricing.selected_incentive_usd,
            true_net_cost_usd=pricing.npc_verified_usd,
            risk_adjusted_net_cost_usd=pricing.npc_with_adjustments_usd,
            has_unverified_inputs=False, warnings=warnings,
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
                "structure_type": pricing.structure_type,
                "primary_jurisdiction": pricing.primary_jurisdiction,
                "selected_incentive_usd": pricing.selected_incentive_usd,
                "npc_verified_usd": pricing.npc_verified_usd,
                "npc_conservative_usd": pricing.npc_verified_usd,
                "gross_budget_usd": pricing.gross_budget_usd,
                "segments": _segment_dicts(pricing),
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
