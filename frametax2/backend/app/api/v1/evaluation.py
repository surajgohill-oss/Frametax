from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.project import Project
from app.services.canonical_evaluation import (
    ENGINE_VERSION,
    UNPRICEABLE_PAGE_DEFAULT_LIMIT,
    UNPRICEABLE_PAGE_MAX_LIMIT,
    GenerationSummaryUnavailable,
    InvalidPageCursor,
    load_generation_summary,
    summary_totals,
    current_generation_fingerprint,
    evaluate_project,
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
    return result


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
