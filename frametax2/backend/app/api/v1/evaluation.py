"""
Generic project evaluation API — the route behind "Begin Evaluation".

    POST /api/v1/projects/{id}/evaluation/begin
         orchestrate CanonicalProductionState -> optimizer discovery ->
         ProductionStructure/StructureCalculationResult for ANY project,
         idempotent per input fingerprint. See app/services/project_evaluation.py
         for the actual orchestration; this route is a thin wrapper.

Deliberately generic — no project ID is ever referenced in this file.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.project_evaluation import begin_evaluation

router = APIRouter(prefix="/projects", tags=["evaluation"])


@router.post("/{project_id}/evaluation/begin")
async def begin_project_evaluation(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    result = await begin_evaluation(db, project_id)
    if result.get("status") == "PROJECT_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Project not found")
    return result
