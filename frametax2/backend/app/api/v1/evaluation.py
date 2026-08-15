"""
Generic project evaluation API — the route behind "Begin Evaluation".

    POST /api/v1/projects/{id}/evaluation/begin
         the canonical served evaluation entry point for ANY project,
         idempotent per input fingerprint. See
         app/services/canonical_evaluation.py for the actual
         orchestration; this route is a thin wrapper.

Phase 2 cutover: this route now calls `canonical_evaluation.evaluate_project`
(the validated qualification/allocation/pricing stack), not
`project_evaluation.begin_evaluation` (which called `run_full_analysis` —
proven in bca893a to be the wrong engine for served project economics:
zero canonical-layer references, $1.12M off Little Utopia's accepted NPC).
`project_evaluation.py` is retained only as historical/test reference; it
must never be reachable from this route again.

Deliberately generic — no project ID is ever referenced in this file.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.canonical_evaluation import evaluate_project

router = APIRouter(prefix="/projects", tags=["evaluation"])


@router.post("/{project_id}/evaluation/begin")
async def begin_project_evaluation(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    result = await evaluate_project(db, project_id)
    if result.get("status") == "PROJECT_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Project not found")
    return result
