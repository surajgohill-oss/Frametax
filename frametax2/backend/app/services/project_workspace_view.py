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
from app.services.canonical_evaluation import ENGINE_VERSION
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
    jurisdiction_code_by_id: dict[str, str] = {}
    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, Part 4/CBA-001 (and in the spirit of
    # Codex's CBA-008) — which rows are "this project's current
    # evaluation" must never depend on leading_structure_id: that field
    # is correctly None whenever no candidate currently admits
    # Recommended (a real, disclosed, priced baseline can still exist
    # with no recommended winner). Read the current fingerprint directly
    # off ANY current-engine result row for this project instead — every
    # row from one evaluation run shares one fingerprint by construction.
    engine_version = ENGINE_VERSION
    # Producer Display Names + Budget Rail User Assumptions closeout —
    # correctness fix, not a doctrine change (same fix, same reasoning,
    # as canonical_production_view.py's identical query): rows are never
    # deleted when a new evaluation runs, so once a producer changes a
    # fingerprint-participating assumption (contingency_expected_
    # utilization_pct, financing_cost_usd, ...) and later reverts it,
    # MULTIPLE real fingerprints legitimately coexist for this project —
    # an unordered `.limit(1)` could pick a stale one. The only correct
    # source for "this project's current fingerprint" is the SAME
    # computation evaluate_project() uses — recomputed here READ-ONLY
    # (no script analysis / artwork extraction / new rows) so this stays
    # a cheap read, never a second evaluation entry point.
    from app.services.canonical_evaluation import (
        _compute_fingerprint, _coproduction_facts, _excluded_jurisdiction_codes,
    )
    from app.services.canonical_project_economics import build_project_economic_inputs
    from app.calculators.canonical_role_qualification_bridge import (
        role_known_codes_from_project, script_facts_from_project,
    )
    fingerprint = None
    # READ PURITY: this is a GET/read builder. read_only=True keeps
    # fingerprint reconstruction side-effect free (no budget routing, no
    # home-jurisdiction persistence, no ProjectFact write, no commit).
    econ = await build_project_economic_inputs(session, project.id, read_only=True)
    if econ.ok:
        role_known_codes = await role_known_codes_from_project(session, str(project.id))
        script_facts = await script_facts_from_project(session, str(project.id))
        coproduction_facts = await _coproduction_facts(session, project.id)
        # Batched producer-control closeout (2026-09-03) — same fix,
        # same reasoning, as canonical_production_view.py's identical
        # call: must reuse the exact same fingerprint inputs
        # evaluate_project() itself uses, including
        # excluded_jurisdiction_codes, or this read-only reconstruction
        # silently diverges from what was actually persisted the moment
        # a project has any jurisdiction exclusion on file.
        excluded_jurisdiction_codes = frozenset(await _excluded_jurisdiction_codes(session, project.id))
        fingerprint = _compute_fingerprint(
            econ.inputs, role_known_codes=role_known_codes, script_facts=script_facts,
            coproduction_facts=coproduction_facts,
            excluded_jurisdiction_codes=excluded_jurisdiction_codes,
        )
    if fingerprint is None:
        fingerprint = (await session.execute(
            select(StructureCalculationResult.input_fingerprint)
            .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
            .where(
                ProductionStructure.project_id == project.id,
                StructureCalculationResult.engine_version == engine_version,
            )
            .order_by(StructureCalculationResult.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

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
