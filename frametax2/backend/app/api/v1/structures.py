"""
Production structure generation and calculation endpoints.

POST /projects/{id}/structures/generate    — create a candidate structure
POST /projects/{id}/structures/{sid}/calculate — run the engine
GET  /projects/{id}/structure-results      — list calculated results
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.incentive import IncentiveProgram, QualifyingSpendCategory
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.schemas.production import (
    ProductionStructureCreate,
    ProductionStructureRead,
    StructureCalculationResultRead,
)

router = APIRouter(prefix="/projects/{project_id}/structures", tags=["structures"])


@router.post("", response_model=ProductionStructureRead, status_code=201)
async def generate_structure(
    project_id: str,
    body: ProductionStructureCreate,
    db: AsyncSession = Depends(get_db),
) -> ProductionStructure:
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    structure = ProductionStructure(
        id=uuid.uuid4(),
        project_id=project_id,
        name=body.name,
        description=body.description,
        jurisdiction_allocations=body.jurisdiction_allocations,
        claimed_program_ids=[str(pid) for pid in (body.claimed_program_ids or [])],
        talent_arrangements=body.talent_arrangements,
        assumed_jurisdiction_spend_pcts=body.assumed_jurisdiction_spend_pcts,
        uses_georgia_logo=body.uses_georgia_logo,
        is_official_coproduction=body.is_official_coproduction,
        coproduction_treaty=body.coproduction_treaty,
        notes=body.notes,
    )
    db.add(structure)
    await db.commit()
    await db.refresh(structure)
    return structure


@router.post("/{structure_id}/calculate", response_model=StructureCalculationResultRead)
async def calculate_structure(
    project_id: str,
    structure_id: str,
    db: AsyncSession = Depends(get_db),
) -> StructureCalculationResult:
    """RETIRED production route (OH-003, CODEX_FINAL_OPTIMIZER_HEALTH_AUDIT).

    This route persisted `engine_version="0.1.0"` `StructureCalculationResult`
    rows via the legacy `run_full_analysis` engine — a genuinely different,
    uncanonical calculation lineage from `canonical_evaluation.py`
    (`ENGINE_VERSION`). It structurally cannot become a project's
    `leading_structure_id` or satisfy the canonical served query (which
    requires an exact `engine_version == ENGINE_VERSION` match), and no
    frontend code calls it — but a second, live, persisting calculation API
    is exactly the "multiple production-capable engine lineages" defect
    Codex found, independent of whether it currently has a caller. The one
    real internal caller (`project_evaluation.begin_evaluation`) was
    already unreachable from any route (see `api/v1/evaluation.py`'s own
    docstring); this was the one remaining reachable path to the same
    uncanonical engine.

    Retired rather than deleted: `calculate_structure_impl` and
    `run_full_analysis` remain importable for historical/test reference,
    per this project's own "do not delete historical code merely because
    it exists" discipline — only the ability to reach and persist through
    them from a live route is removed. The canonical, single served path
    for structure/project economics is `POST /api/v1/projects/{project_id}
    /evaluation/begin` (`canonical_evaluation.evaluate_project`)."""
    raise HTTPException(
        status_code=410,
        detail=(
            "This endpoint is retired. It used a legacy, uncanonical "
            "calculation engine (engine_version=0.1.0) that never fed the "
            "canonical served evaluation. Use "
            "POST /api/v1/projects/{project_id}/evaluation/begin instead."
        ),
    )


async def calculate_structure_impl(
    project_id: str,
    structure_id: str,
    db: AsyncSession,
    *,
    extra_warnings: list[str] | None = None,
    has_unverified_inputs_override: bool | None = None,
    input_fingerprint: str | None = None,
) -> StructureCalculationResult:
    """
    Run the full deterministic engine against a production structure.
    Assembles inputs from DB, calls run_full_analysis, persists result.

    Importable so other orchestrators (e.g. the generic project evaluation
    entry point behind "Begin Evaluation") can reuse this exact assembly
    and persistence logic rather than duplicating it — the same pattern
    used for `_commit_candidate_impl` in ingestion.py. The route handler
    above is now a thin wrapper.

    `extra_warnings` / `has_unverified_inputs_override` / `input_fingerprint`
    are additive, optional hooks a caller can use to attach provenance
    (e.g. an MFNI/regional-cost-normalization limitation notice, or the
    CanonicalProductionState fingerprint that produced this run) without
    this function or `run_full_analysis` itself knowing anything about
    the caller's context.
    """
    from app.calculators.run_full_analysis import run_full_analysis

    # Load structure
    struct_result = await db.execute(
        select(ProductionStructure).where(ProductionStructure.id == structure_id)
    )
    structure = struct_result.scalar_one_or_none()
    if not structure:
        raise HTTPException(status_code=404, detail="Structure not found")

    # Load project
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Resolve primary jurisdiction from allocations
    allocations = structure.jurisdiction_allocations or []
    primary_jid = allocations[0].get("jurisdiction_id") if allocations else None
    if not primary_jid:
        raise HTTPException(
            status_code=422,
            detail="Structure must have at least one jurisdiction_allocation with jurisdiction_id",
        )

    jur_result = await db.execute(select(Jurisdiction).where(Jurisdiction.id == primary_jid))
    jurisdiction = jur_result.scalar_one_or_none()
    if not jurisdiction:
        raise HTTPException(status_code=422, detail=f"Jurisdiction {primary_jid} not found")

    # Load claimed programs
    claimed_ids = structure.claimed_program_ids or []
    programs_result = await db.execute(
        select(IncentiveProgram).where(IncentiveProgram.id.in_(claimed_ids))
    )
    programs = list(programs_result.scalars().all())

    # Load qualifying spend categories per program
    programs_with_categories = []
    assumed_pcts = structure.assumed_jurisdiction_spend_pcts or {}
    for prog in programs:
        cats_result = await db.execute(
            select(QualifyingSpendCategory).where(
                QualifyingSpendCategory.program_id == prog.id
            )
        )
        qualifying_categories = [
            {"spend_category": c.spend_category, "qualifies": c.qualifies,
             "jurisdiction_spend_only": c.jurisdiction_spend_only}
            for c in cats_result.scalars().all()
        ]
        jurisdiction_spend_pct = float(assumed_pcts.get(str(prog.id), 1.0))
        programs_with_categories.append({
            "program": {
                "id": str(prog.id),
                "slug": prog.slug,
                "program_type": prog.program_type,
                "base_rate": float(prog.base_rate) if prog.base_rate else None,
                "max_rate": float(prog.max_rate) if prog.max_rate else None,
                "is_refundable": prog.is_refundable,
                "is_transferable": prog.is_transferable,
                "transferable_value_pct": float(prog.transferable_value_pct) if prog.transferable_value_pct else None,
                "is_competitive": prog.is_competitive,
                "annual_cap_local": float(prog.annual_cap_local) if prog.annual_cap_local else None,
                "confidence_tier": prog.confidence_tier,
            },
            "qualifying_categories": qualifying_categories,
            "uplifts": [],  # TODO: load ProgramUplift records
            "jurisdiction_spend_pct": jurisdiction_spend_pct,
        })

    # Load budget line items for this project
    bdoc_result = await db.execute(
        select(BudgetDocument).where(
            BudgetDocument.project_id == project_id,
            BudgetDocument.is_active == True,
        )
    )
    budget_docs = list(bdoc_result.scalars().all())

    line_items: list[dict] = []
    if budget_docs:
        latest_doc = budget_docs[-1]
        items_result = await db.execute(
            select(BudgetLineItem).where(BudgetLineItem.budget_document_id == latest_doc.id)
        )
        line_items = [
            {
                "description": li.description,
                "department": li.department,
                "amount_usd": float(li.amount_usd) if li.amount_usd else 0.0,
                "spend_category": li.spend_category,
                "atl_btl": li.atl_btl,
                "is_labor": li.is_labor,
                "is_fixed": li.is_fixed,
                "compensation_type": li.compensation_type,
            }
            for li in items_result.scalars().all()
        ]

    jurisdiction_dict = {
        "id": str(jurisdiction.id),
        "name": jurisdiction.name,
        "currency_code": jurisdiction.currency_code,
        "country_code": jurisdiction.country_code,
    }

    production_details: dict = {}
    if structure.uses_georgia_logo:
        production_details["uses_georgia_logo"] = True
    if structure.is_official_coproduction:
        production_details["is_official_coproduction"] = True

    analysis = run_full_analysis(
        structure_id=structure_id,
        jurisdiction=jurisdiction_dict,
        line_items=line_items,
        programs_with_categories=programs_with_categories,
        stacking_rules=[],  # TODO: load LegalStackingRule records
        qualification_tests_with_rules=[],  # TODO: load QualificationTest records
        cost_benchmark=None,  # TODO: load LocalCostBenchmark
        union_fringe_rules=[],
        fx_rates=None,
        production_details=production_details,
        home_jurisdiction_id=str(project.home_jurisdiction_id) if project.home_jurisdiction_id else None,
    )

    # Determine if any programs are unverified
    has_unverified = any(
        r.get("confidence_tier", "DISCOVERY") != "VERIFIED"
        for r in analysis.incentive_results
    )
    total_qs = sum(
        r.get("qualifying_spend_usd", 0.0) for r in analysis.qualified_spend_results
    )
    effective_rate = (
        analysis.total_incentive_economic_value_usd / total_qs if total_qs > 0 else None
    )

    calc_result = StructureCalculationResult(
        id=uuid.uuid4(),
        structure_id=structure_id,
        engine_version=analysis.engine_version,
        total_budget_usd=analysis.total_input_budget_usd,
        rebase_btl_usd=analysis.rebase_btl_usd,
        fixed_atl_usd=analysis.fixed_atl_usd,
        total_qualifying_spend_usd=total_qs,
        total_incentive_value_usd=analysis.total_incentive_economic_value_usd,
        total_travel_cost_usd=analysis.travel_cost_usd,
        true_net_cost_usd=analysis.true_net_cost_usd,
        risk_adjusted_net_cost_usd=analysis.risk_adjusted_net_cost_usd,
        effective_incentive_rate=effective_rate,
        program_results=analysis.incentive_results,
        calculation_trace_json=analysis.calculation_trace,
        has_unverified_inputs=(
            has_unverified if has_unverified_inputs_override is None else has_unverified_inputs_override
        ),
        legal_review_required=analysis.stacking_legal_review_required,
        stacking_violations=analysis.stacking_violations,
        warnings=list(extra_warnings or []),
        optimization_opportunities=[],
        input_fingerprint=input_fingerprint,
    )
    db.add(calc_result)
    await db.commit()
    await db.refresh(calc_result)
    return calc_result


@router.get("/results", response_model=list[StructureCalculationResultRead])
async def list_structure_results(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[StructureCalculationResult]:
    """List all calculation results for structures in this project."""
    structs_result = await db.execute(
        select(ProductionStructure.id).where(ProductionStructure.project_id == project_id)
    )
    struct_ids = [row[0] for row in structs_result.all()]

    if not struct_ids:
        return []

    results = await db.execute(
        select(StructureCalculationResult).where(
            StructureCalculationResult.structure_id.in_(struct_ids)
        ).order_by(StructureCalculationResult.created_at.desc())
    )
    return list(results.scalars().all())
