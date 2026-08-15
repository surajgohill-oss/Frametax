"""
Project Workspace API — the route behind the generic, project-driven
Overview / World / Script / Budget pages.

    GET /api/v1/projects/{id}/workspace

Thin wrapper over app/services/project_workspace_view.py's view adapter.
Read-only: never triggers evaluation (that's POST /evaluation/begin's job),
never computes economics. Generic — no project ID is ever referenced here.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.project_workspace_view import build_project_workspace_view

router = APIRouter(prefix="/projects", tags=["workspace"])


@router.get("/{project_id}/workspace")
async def get_project_workspace(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    result = await build_project_workspace_view(db, project_id)
    if result.get("status") == "PROJECT_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Project not found")
    return result
