"""
project_workspace_view.py

The VIEW ADAPTER behind the generic Project Workspace UI. Transforms
already-persisted, already-canonical data (ProductionStructure /
StructureCalculationResult from canonical_evaluation.py, BudgetDocument /
BudgetLineItem, the SA-1 script pipeline) into ONE response shape the
frontend's project-scoped pages (Overview / World / Script / Budget)
consume directly.

This module computes NO economics and triggers no evaluation. It reads
what `evaluate_project()` already committed and reshapes it — the same
"adapter, not a second engine" boundary `optimizer_handoff.py` and
`canonical_project_economics.py` already established for the layers below
this one.

Candidate UI status (Part F/G/H's PRICED/REVIEW_REQUIRED/UNPRICEABLE/
RULE_REJECTED distinction) is derived from two fields
`canonical_evaluation.py` already persists on every StructureCalculationResult
(`candidate_status`, `relocation_cost_normalized`) — never a new judgment:

    candidate_status=PRICED, relocation_cost_normalized=True   -> COMPARABLE
    candidate_status=PRICED, relocation_cost_normalized=False  -> REVIEW_REQUIRED
    candidate_status=UNPRICEABLE_AUTHORITY_INSUFFICIENT         -> UNPRICEABLE
    (RULE_REJECTED is reserved; no candidate reaches it generically yet)

REVIEW_REQUIRED is the direct, generic fix for the Abu Dhabi presentation
defect: any full-relocation candidate (not just Abu Dhabi) is honestly
uncertain until relocation costs are modeled, so none of them render as a
confident recommendation — not because Abu Dhabi specifically was singled
out, but because the same rule applies to every non-baseline candidate.
UNPRICEABLE candidates (Abu Dhabi's own actual classification) get their
own, more clearly "not available" state.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services import script_parse_status as sps
from app.services.script_analysis_service import resolve_active_screenplay

UI_COMPARABLE = "COMPARABLE"
UI_REVIEW_REQUIRED = "REVIEW_REQUIRED"
UI_UNPRICEABLE = "UNPRICEABLE"
UI_RULE_REJECTED = "RULE_REJECTED"


def _ui_status(trace: dict) -> str:
    status = trace.get("candidate_status")
    if status == "UNPRICEABLE_AUTHORITY_INSUFFICIENT":
        return UI_UNPRICEABLE
    if status == "RULE_REJECTED":
        return UI_RULE_REJECTED
    if status == "PRICED":
        return UI_COMPARABLE if trace.get("relocation_cost_normalized") else UI_REVIEW_REQUIRED
    return UI_REVIEW_REQUIRED  # never presented as executable without a known status


async def build_project_workspace_view(session: AsyncSession, project_id) -> dict:
    project = await session.get(Project, project_id)
    if project is None:
        return {"status": "PROJECT_NOT_FOUND"}

    # ── evaluation ────────────────────────────────────────────────────────
    evaluation_status = "NOT_BEGUN"
    candidates: list[dict] = []
    fingerprint = None
    engine_version = None
    jurisdiction_code_by_id: dict[str, str] = {}
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

    if fingerprint:
        rows = (await session.execute(
            select(ProductionStructure, StructureCalculationResult)
            .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
            .where(
                ProductionStructure.project_id == project.id,
                StructureCalculationResult.input_fingerprint == fingerprint,
                # A fingerprint alone doesn't distinguish engine versions —
                # an older evaluation's rows can share the same fingerprint
                # (identical budget/jurisdiction inputs) as a freshly
                # regenerated set. Only the leading structure's OWN engine
                # version is "the" current evaluation.
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

        for structure, result in rows:
            trace = result.calculation_trace_json or {}
            allocs = structure.jurisdiction_allocations or []
            code = jurisdiction_code_by_id.get(allocs[0].get("jurisdiction_id")) if allocs else None
            if code is None and structure.name and structure.name.startswith("Full relocation to "):
                # Unpriceable candidates never get an allocation built (no
                # jurisdiction_allocations row to resolve a code from), but
                # the structure's own name already carries the jurisdiction
                # code as text — display-only parsing, no economics.
                code = structure.name.removeprefix("Full relocation to ").strip() or None
            candidates.append({
                "structure_id": str(structure.id),
                "label": structure.name,
                "jurisdiction_code": code,
                "ui_status": _ui_status(trace),
                "candidate_status": trace.get("candidate_status"),
                "is_baseline": bool(trace.get("is_baseline")),
                "true_net_cost_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
                "total_incentive_value_usd": (
                    float(result.total_incentive_value_usd) if result.total_incentive_value_usd is not None else None
                ),
                "reason": trace.get("reason"),
                "warnings": result.warnings or [],
            })
        evaluation_status = "EVALUATION_COMPLETE"
    elif project.total_budget_usd is None:
        budget_present = (await session.execute(
            select(BudgetDocument.id).where(BudgetDocument.project_id == project.id)
        )).scalars().first()
        evaluation_status = "EVALUATION_COMPLETE" if budget_present else "BUDGET_REQUIRED_FOR_CURRENT_EVALUATION"

    baseline = next((c for c in candidates if c["is_baseline"]), None)
    comparable = [c for c in candidates if c["ui_status"] == UI_COMPARABLE]
    review_required = [c for c in candidates if c["ui_status"] == UI_REVIEW_REQUIRED]
    unpriceable = [c for c in candidates if c["ui_status"] == UI_UNPRICEABLE]
    top_result = comparable[0] if comparable else None

    # ── budget ────────────────────────────────────────────────────────────
    budget_doc = (await session.execute(
        select(BudgetDocument)
        .where(BudgetDocument.project_id == project.id)
        .order_by(BudgetDocument.created_at.desc())
    )).scalars().first()
    line_items: list[dict] = []
    if budget_doc is not None:
        items = (await session.execute(
            select(BudgetLineItem).where(BudgetLineItem.budget_document_id == budget_doc.id)
        )).scalars().all()
        line_items = [
            {
                "description": i.description,
                "department": i.department,
                "atl_btl": getattr(i.atl_btl, "value", i.atl_btl),
                "spend_category": getattr(i.spend_category, "value", i.spend_category),
                "amount_usd": float(i.amount_usd) if i.amount_usd is not None else None,
            }
            for i in items
        ]

    # ── script (SA-1, existing pipeline — read-only here) ───────────────────
    screenplay = await resolve_active_screenplay(session, project_id)
    script = {"status": sps.SCRIPT_NOT_PRESENT, "scene_count": 0, "character_count": 0, "filename": None}
    if screenplay is not None:
        from app.models.screenplay import Character, Scene
        scenes = (await session.execute(
            select(Scene).where(Scene.screenplay_id == screenplay.id)
        )).scalars().all()
        characters = (await session.execute(
            select(Character).where(Character.screenplay_id == screenplay.id, Character.is_speaking_role.is_(True))
        )).scalars().all()
        script = {
            "status": screenplay.parse_status,
            "filename": screenplay.filename,
            "scene_count": len(scenes),
            "character_count": len(characters),
            "locations": sorted({s.scripted_location for s in scenes if s.scripted_location}),
        }

    return {
        "status": "OK",
        "project": {
            "id": str(project.id),
            "title": project.title,
            "budget_usd": float(project.total_budget_usd) if project.total_budget_usd is not None else (
                float(budget_doc.total_budget_raw) if budget_doc and budget_doc.total_budget_raw is not None else None
            ),
            "base_jurisdiction_code": jurisdiction_code_by_id.get(
                str(project.home_jurisdiction_id)
            ) if fingerprint and project.home_jurisdiction_id else None,
        },
        "evaluation": {
            "status": evaluation_status,
            "baseline": baseline,
            "top_result": top_result,
            "comparable_count": len(comparable),
            "review_required_count": len(review_required),
            "unpriceable_count": len(unpriceable),
            "comparable": comparable,
            "review_required": review_required,
            "unpriceable": unpriceable,
            "mfni_limitation": (
                "Regional production-cost normalization (MFNI) is not yet applied — "
                "figures use this production's own nominal budget amounts and statutory "
                "incentive rate only."
            ),
        },
        "budget": {
            "total_usd": float(budget_doc.total_budget_raw) if budget_doc and budget_doc.total_budget_raw is not None else None,
            "filename": budget_doc.filename if budget_doc else None,
            "line_items": line_items,
        },
        "script": script,
    }
