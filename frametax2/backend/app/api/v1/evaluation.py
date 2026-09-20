from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.project import Project
from app.services.canonical_production_view import (
    CANDIDATE_PAGE_DEFAULT_LIMIT,
    CANDIDATE_PAGE_MAX_LIMIT,
    build_production_and_structures,
    decode_candidate_cursor,
)
from app.services.evaluation_contract import apply_evaluation_contract
from app.services.canonical_evaluation import (
    ENGINE_VERSION,
    UNPRICEABLE_PAGE_DEFAULT_LIMIT,
    UNPRICEABLE_PAGE_MAX_LIMIT,
    CANDIDATE_GROUPS_PAGE_DEFAULT_LIMIT,
    CANDIDATE_GROUPS_PAGE_MAX_LIMIT,
    GenerationSummaryUnavailable,
    InvalidPageCursor,
    load_generation_summary,
    summary_totals,
    current_generation_fingerprint,
    evaluate_project,
    candidate_groups_page,
    unpriceable_page,
)

router = APIRouter(prefix="/projects", tags=["evaluation"])


@router.post("/{project_id}/evaluation/begin")
async def begin_project_evaluation(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    """Bounded by construction: the unpriced ("rejection") universe is summarized
    (exact total, counts by disposition/reason, one first page + cursor); the rest
    is read from GET /projects/{id}/evaluation/unpriceable."""
    result = await evaluate_project(db, project_id)
    if result.get("status") == "PROJECT_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Project not found")
    # One served shape for fresh and reused evaluations: only ``status`` may differ.
    return await apply_evaluation_contract(db, project_id, result)


@router.get("/{project_id}/evaluation/unpriceable")
async def list_unpriceable_candidates(
    project_id: uuid.UUID,
    limit: int = Query(UNPRICEABLE_PAGE_DEFAULT_LIMIT, ge=1, le=UNPRICEABLE_PAGE_MAX_LIMIT),
    cursor: str | None = Query(None, description="next_cursor from the previous page; omit for the first page"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Every unpriced candidate of the project's CURRENT evaluation, one bounded page at a
    time, in generation order (generation_ordinal). Read-only: never triggers an
    evaluation. Nothing is dropped: follow ``next_cursor`` while ``has_more`` is true to
    receive every row exactly once. The exact totals (from the evaluation's own summary
    row) accompany the first page (no cursor)."""
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    fingerprint = await current_generation_fingerprint(db, project_id)
    if fingerprint is None:
        return {
            "status": "NO_CURRENT_EVALUATION", "engine_version": ENGINE_VERSION, "input_fingerprint": None,
            "limit": limit, "returned": 0, "has_more": False, "next_cursor": None, "results": [],
        }
    try:
        page = await unpriceable_page(db, project_id, fingerprint, limit=limit, cursor=cursor)
    except InvalidPageCursor as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    response = {"status": "OK", "engine_version": ENGINE_VERSION, "input_fingerprint": fingerprint, **page}
    if cursor is None:
        try:
            totals = summary_totals(await load_generation_summary(db, project_id, fingerprint))
        except GenerationSummaryUnavailable:
            return {**response, "status": "NO_CURRENT_EVALUATION", "results": [], "returned": 0}
        response.update(
            total_unpriceable_count=totals["total"],
            by_disposition=totals["by_disposition"],
            by_reason=totals["by_reason"],
        )
    return response


@router.get("/{project_id}/evaluation/aggregates")
async def list_candidate_aggregates(
    project_id: uuid.UUID,
    limit: int = Query(CANDIDATE_GROUPS_PAGE_DEFAULT_LIMIT, ge=1, le=CANDIDATE_GROUPS_PAGE_MAX_LIMIT),
    cursor: str | None = Query(None, description="next_cursor from the previous page; omit for the first page"),
    detail: bool = Query(False, description="include each group's full representative (structure, trace, warnings)"),
    status: str | None = Query(None, description="only groups of this original candidate status (e.g. PRICED, RULE_REJECTED)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """The AGGREGATE groups of the project's CURRENT evaluation, one bounded page at a time, in
    group_ordinal (first-seen) order. Every generated candidate that is not a retained detailed row
    (plain RULE_REJECTED permutations, PRICED candidates outside the retained top sets, capped statuses)
    is counted exactly in one group per (original status, structure family/type, reason class, primary +
    participant jurisdiction set, program/component/treaty family), with min/max NPC and incentive, the
    best economic identity, the retained dominating structure and one representative. Follow
    ``next_cursor`` while ``has_more`` is true to receive every group exactly once. Exact accounting
    (generated == persisted + aggregated) accompanies the first page. Read-only."""
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    fingerprint = await current_generation_fingerprint(db, project_id)
    if fingerprint is None:
        return {"status": "NO_CURRENT_EVALUATION", "engine_version": ENGINE_VERSION, "input_fingerprint": None,
                "limit": limit, "returned": 0, "has_more": False, "next_cursor": None, "results": []}
    try:
        page = await candidate_groups_page(db, project_id, fingerprint, limit=limit, cursor=cursor, detail=detail, status=status)
    except InvalidPageCursor as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    response = {"status": "OK", "engine_version": ENGINE_VERSION, "input_fingerprint": fingerprint, **page}
    if cursor is None:
        try:
            totals = summary_totals(await load_generation_summary(db, project_id, fingerprint))
        except GenerationSummaryUnavailable:
            return {**response, "status": "NO_CURRENT_EVALUATION", "results": [], "returned": 0}
        response.update(
            generated_candidates=totals["generated"], persisted_rows=totals["persisted_rows"],
            aggregated_candidates=totals["aggregated_candidates"], aggregated_priced=totals["aggregated_priced"],
            group_count=totals["aggregate_groups"],
            accounting_holds=totals["generated"] == totals["persisted_rows"] + totals["aggregated_candidates"],
        )
    return response


@router.get("/{project_id}/evaluation/candidates")
async def list_served_candidates(
    project_id: uuid.UUID,
    limit: int = Query(CANDIDATE_PAGE_DEFAULT_LIMIT, ge=1, le=CANDIDATE_PAGE_MAX_LIMIT),
    cursor: str | None = Query(None, description="next_cursor from the previous page; omit for the first page"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """The DETAILED served candidates (priced, dominated, co-pro, feasibility, unpriceable-authority
    -- everything that is not a plain RULE_REJECTED) of the project's CURRENT evaluation, one bounded
    page (max 100) at a time. The production view returns page 1 of this same sequence; follow
    ``next_cursor`` while ``has_more`` is true to receive every served candidate exactly once. The
    rejection universe is paged separately at /evaluation/unpriceable. Read-only; a cursor minted for
    another evaluation generation is refused (409) rather than silently mis-paged."""
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    fingerprint = await current_generation_fingerprint(db, project_id)
    if fingerprint is None:
        return {"status": "NO_CURRENT_EVALUATION", "engine_version": ENGINE_VERSION, "input_fingerprint": None,
                "limit": limit, "returned": 0, "total": 0, "has_more": False, "next_cursor": None,
                "structures": [], "ranking": []}
    offset = 0
    if cursor is not None:
        try:
            fp16, offset = decode_candidate_cursor(cursor)
        except InvalidPageCursor as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if fp16 != fingerprint[:16]:
            raise HTTPException(
                status_code=409,
                detail="cursor belongs to a different evaluation generation; restart from the first page",
            )
    view = await build_production_and_structures(db, project_id, candidate_limit=limit, candidate_offset=offset)
    allocated = view["structures"]["allocated_structures"]
    return {
        "status": "OK", "engine_version": ENGINE_VERSION, "input_fingerprint": fingerprint,
        **allocated["candidates_page"],
        "structures": allocated["structures"], "ranking": allocated["ranking"],
    }
