"""
canonical_production_view.py

The view adapter behind the RESTORED mature CineGlobe production UI
(Overview/Workspace/Scenarios/ProjectGlobe/Reports/Knowledge — the rich
pre-regression component tree, /projects/{id}/overview etc.), generalized
to any project_id.

Reshapes ProductionStructure / StructureCalculationResult — the SAME
canonical-1.1.0 persisted rows canonical_evaluation.py commits, already
proven to reproduce Little Utopia's exact accepted NPC ($3,057,794.90) —
into the `production` / `structures.allocated_structures` shape those
mature components already read (built against
`app/demo/little_utopia_state.py::build_allocated_structures` /
`get_production`). Computes NO economics; every number here is read
straight off an already-committed StructureCalculationResult row.

Fields the persisted engine does not compute generically yet (per-account
allocation assignments, conditional funding programs, structure
compatibility, a written recommendation) are served as honest empty
values (`[]` / `{}` / `null`), never fabricated — the same "if data is
absent, show the appropriate empty state" principle already established
for the Script/Documents tabs in project_workspace_view.py. This is a
disclosed, structural gap (deep per-segment drill-downs render fewer
details generically than Little Utopia's own richer, unchanged
/api/v1/cineglobe/production|structures endpoints), not a defect.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetDocument
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services.canonical_evaluation import ENGINE_VERSION


def _empty_structure_entry(structure, result, jurisdiction_code_by_id: dict[str, str]) -> dict:
    trace = result.calculation_trace_json or {}
    is_priced = trace.get("candidate_status") == "PRICED"
    allocs = structure.jurisdiction_allocations or []
    code = trace.get("primary_jurisdiction") or (
        jurisdiction_code_by_id.get(allocs[0].get("jurisdiction_id")) if allocs else None
    )
    if code is None and structure.name and structure.name.startswith("Full relocation to "):
        # Unpriceable candidates never get a jurisdiction_allocations row
        # (no allocation is built for an authority-insufficient jurisdiction)
        # — same gap and same display-only fix as project_workspace_view.py.
        code = structure.name.removeprefix("Full relocation to ").strip() or None
    # structure_type: rows generated before the 1.1.0 enrichment don't carry
    # this in trace_json — derive the same value generically from is_baseline
    # (present on every engine_version since Phase 2) rather than requiring
    # every already-evaluated project to be re-evaluated first. Display-only,
    # same fact the label itself already encodes ("X — production's current
    # base" vs "Full relocation to X").
    structure_type = trace.get("structure_type") or (
        "single_country" if trace.get("is_baseline") else "full_relocation"
    )
    # selected_incentive_usd: prefer the persisted StructureCalculationResult
    # column (total_incentive_value_usd — always populated for a priced
    # result, on every engine_version) over the trace_json field (only
    # present on rows generated since the segments/incentive enrichment
    # added below) so this renders correctly without requiring every
    # already-evaluated project to be re-evaluated first.
    selected_incentive_usd = (
        float(result.total_incentive_value_usd) if result.total_incentive_value_usd is not None
        else trace.get("selected_incentive_usd")
    ) if is_priced else None
    return {
        "structure_id": str(structure.id),
        "structure_type": structure_type,
        "label": structure.name,
        "primary_jurisdiction": code,
        "participants": [code] if code else [],
        "conditional_programs": [],
        "conditional_compatibility": {"pursuable_count": 0, "counts_by_verdict": {}, "gate_kinds": []},
        "is_fully_priced": is_priced,
        "candidate_status": trace.get("candidate_status"),
        "blockers": [] if is_priced else [trace.get("reason")] if trace.get("reason") else [],
        "gross_budget_usd": trace.get("gross_budget_usd"),
        "total_incentive_floor_usd": selected_incentive_usd,
        "total_incentive_ceiling_usd": selected_incentive_usd,
        "selected_incentive_usd": selected_incentive_usd,
        "travel_incremental_delta_usd": None,
        "fx_delta_usd": None,
        "local_cost_delta_usd": 0.0,
        "inkind_replacement_delta_usd": 0.0,
        "financing_cost_usd": 0.0,
        "implementation_cost_usd": 0.0,
        "npc_verified_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
        "npc_with_adjustments_usd": (
            float(result.risk_adjusted_net_cost_usd) if result.risk_adjusted_net_cost_usd is not None else None
        ),
        "npc_conservative_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
        "treaty_slug": None,
        "ownership_shares": None,
        "stacking_note": None,
        "inkind_note": None,
        "notes": [],
        "segments": trace.get("segments") or [],
        "allocation": {
            "allocation_version": None, "is_complete": None, "conserves": None,
            "total_allocated_usd": None, "total_budget_lines_usd": None,
            "allocated_by_jurisdiction": {}, "unallocated_account_codes": [],
            "duplicate_account_codes": [], "notes": [], "assignments": [],
        },
        "recommendation": None,
        "is_baseline": bool(trace.get("is_baseline")),
        "relocation_cost_normalized": bool(trace.get("relocation_cost_normalized")),
        "reason": trace.get("reason"),
        "warnings": result.warnings or [],
    }


def _ranking_entry(structure, result, entry: dict) -> dict:
    if entry["is_fully_priced"]:
        return {
            "rank": None,  # filled in by caller after sorting
            "structure_id": entry["structure_id"],
            "label": entry["label"],
            "is_fully_priced": True,
            "selected_incentive_usd": entry["selected_incentive_usd"],
            "inkind_replacement_delta_usd": entry["inkind_replacement_delta_usd"],
            "npc_verified_usd": entry["npc_verified_usd"],
            "npc_with_adjustments_usd": entry["npc_with_adjustments_usd"],
            "npc_conservative_usd": entry["npc_conservative_usd"],
            "conditional_pursuable_count": 0,
        }
    return {
        "rank": None,
        "structure_id": entry["structure_id"],
        "label": entry["label"],
        "is_fully_priced": False,
        "excluded_from_ranking_because": entry["blockers"] or [entry.get("reason") or "Not fully priced."],
    }


async def build_production_and_structures(session: AsyncSession, project_id) -> dict:
    """Generic, project_id-driven replacement for GET /cineglobe/production
    + GET /cineglobe/structures, sourced from canonical_evaluation.py's
    persisted rows instead of the Little-Utopia-only in-memory get_state().
    """
    project = await session.get(Project, project_id)
    if project is None:
        return {"status": "PROJECT_NOT_FOUND"}

    fingerprint = None
    engine_version = None
    if project.leading_structure_id is not None:
        leading = await session.get(ProductionStructure, project.leading_structure_id)
        leading_result = (
            (await session.execute(
                select(StructureCalculationResult)
                .where(StructureCalculationResult.structure_id == leading.id)
                .order_by(StructureCalculationResult.created_at.desc())
            )).scalars().first()
            if leading is not None else None
        )
        if leading_result is not None:
            fingerprint = leading_result.input_fingerprint
            engine_version = leading_result.engine_version

    rows: list[tuple] = []
    if fingerprint:
        rows = (await session.execute(
            select(ProductionStructure, StructureCalculationResult)
            .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
            .where(
                ProductionStructure.project_id == project.id,
                StructureCalculationResult.input_fingerprint == fingerprint,
                StructureCalculationResult.engine_version == engine_version,
            )
        )).all()

    jurisdiction_ids = set()
    for structure, _ in rows:
        for alloc in structure.jurisdiction_allocations or []:
            if alloc.get("jurisdiction_id"):
                jurisdiction_ids.add(alloc["jurisdiction_id"])
    jurisdictions = (
        (await session.execute(select(Jurisdiction).where(Jurisdiction.id.in_(jurisdiction_ids)))).scalars().all()
        if jurisdiction_ids else []
    )
    jurisdiction_code_by_id = {str(j.id): j.code for j in jurisdictions}

    structure_entries = [_empty_structure_entry(s, r, jurisdiction_code_by_id) for s, r in rows]

    # Ranking (Part K — never invent regional savings): only structures
    # whose cost is actually comparable on the SAME basis participate in
    # numeric ranking. A relocation candidate's lower NPC omits real
    # relocation costs (travel, in-kind replacement) no project has
    # generic data for yet — a lower number there is not a cheaper
    # option, just an incomplete one. relocation_cost_normalized is False
    # for every candidate except the production's own base jurisdiction
    # (which needs no such adjustment by construction), so this mirrors
    # canonical_evaluation.py's own _summarize_evaluation top_pair rule:
    # the baseline is the winner whenever it is priced, never a relocation
    # candidate on a merely-lower raw number.
    comparable = sorted(
        (e for e in structure_entries if e["is_fully_priced"] and e["relocation_cost_normalized"]),
        key=lambda e: e["npc_with_adjustments_usd"] if e["npc_with_adjustments_usd"] is not None else float("inf"),
    )
    review_required = [e for e in structure_entries if e["is_fully_priced"] and not e["relocation_cost_normalized"]]
    unpriced = [e for e in structure_entries if not e["is_fully_priced"]]

    ranking: list[dict] = []
    for i, e in enumerate(comparable, start=1):
        r = _ranking_entry(None, None, e)
        r["rank"] = i
        ranking.append(r)
    for e in review_required:
        r = _ranking_entry(None, None, e)
        r["is_fully_priced"] = False  # priced, but not eligible to rank — see note above
        r["excluded_from_ranking_because"] = [
            "Priced from a real statutory rate, but this candidate's relocation-specific "
            "costs (travel, in-kind replacement) are not yet modeled generically — its NPC "
            "is not a fair comparison against the base jurisdiction yet. Regional cost "
            "normalization pending."
        ]
        ranking.append(r)
    for e in unpriced:
        ranking.append(_ranking_entry(None, None, e))

    base_code = jurisdiction_code_by_id.get(str(project.home_jurisdiction_id)) if project.home_jurisdiction_id else None
    if base_code is None:
        baseline_entry = next((e for e in structure_entries if e["is_baseline"]), None)
        base_code = baseline_entry["primary_jurisdiction"] if baseline_entry else None

    budget_doc = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
        .order_by(BudgetDocument.created_at.desc())
    )).scalars().first()
    gross_budget_usd = (
        float(project.total_budget_usd) if project.total_budget_usd is not None
        else (float(budget_doc.total_budget_raw) if budget_doc and budget_doc.total_budget_raw is not None else None)
    )

    production = {
        "production_id": str(project.id),
        "production_name": project.title,
        "jurisdiction_code": base_code,
        "project_id": str(project.id),
        "lifecycle": project.lifecycle,
        "leading_structure_id": str(project.leading_structure_id) if project.leading_structure_id else None,
        "gross_budget_usd": gross_budget_usd,
        "rate": None,
        "rate_resolution": None,
        "rate_warnings": [],
        "budget_reconciliation": {
            "authoritative_gross_usd": gross_budget_usd,
            "leaf_account_sum_usd": None,
            "variance_usd": None,
            "note": None,
        },
        "production_structure_default": None,
        "physical_requirements": {},
        "territory_physical_match": {},
        "as_of_date": None,
        "computation": {"version": engine_version or ENGINE_VERSION, "computed_at": None},
    }

    comparable_count = len(comparable)
    review_required_count = len(review_required)

    structures = {
        "candidates": [],
        "pruned": [],
        "allocated_structures": {
            "version": engine_version or ENGINE_VERSION,
            "note": (
                "Generic canonical evaluation (any project) — regional "
                "production-cost normalization (MFNI) and generic travel/FX "
                "normalization are not yet applied; see each structure's "
                "own relocation_cost_normalized flag."
            ),
            "coverage": {
                "executable_jurisdictions": [e["primary_jurisdiction"] for e in structure_entries if e["primary_jurisdiction"]],
                "catalog_only_excluded": None,
                "reachable_treaty_partners": [],
                "categories": [],
                "note": None,
            },
            "discovery": {
                "metrics": {},
                "generated_structures": len(structure_entries),
                "optimized_structures": len(comparable) + len(review_required),
                "final_ranked_structures": len(comparable),
                "production_requirements": {"environments": [], "infrastructure": [], "required_capabilities": []},
                "examinations": [],
            },
            "structures": structure_entries,
            "contingency": {},
            "ranking": ranking,
            "stack_combinations": {},
            "advisor_routing_decisions_input": {},
            # Restoration-phase candidate accounting, matching the earlier
            # generic Workspace's own classification (Part J/K/L/N) so both
            # UIs agree: PRICED + relocation_cost_normalized -> comparable
            # (own base jurisdiction); PRICED, not normalized -> review
            # required (a real economics figure, just not regionally
            # comparable yet); UNPRICEABLE -> authority insufficient.
            "candidate_accounting": {
                "comparable_count": comparable_count,
                "review_required_count": review_required_count,
                "unpriceable_count": len(unpriced),
            },
        },
    }

    return {"status": "OK", "production": production, "structures": structures}
