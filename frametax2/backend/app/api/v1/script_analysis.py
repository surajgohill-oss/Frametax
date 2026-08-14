"""
Script Analyzer SA-1, Part K — the generic project API.

Backend routes only (no frontend work in SA-1). These are deliberately
generic: they take a project ID and work for ANY project with a text-based
screenplay, with no Little Utopia special-casing anywhere in the path.

    POST /api/v1/script-analysis/projects/{id}/parse
         run the deterministic parse and persist scenes/characters/elements

    GET  /api/v1/script-analysis/projects/{id}/script
         parse status, blockers and the persisted structure summary

    GET  /api/v1/script-analysis/projects/{id}/state
         the fingerprinted CanonicalProductionState

    GET  /api/v1/script-analysis/projects/{id}/optimizer-input
         the ProductionOptimizerInput contract, or the blockers explaining
         why the project is not yet priceable

Incomplete input yields deterministic blockers with HTTP 200 — a missing
budget is a legitimate, well-defined state, not a server error.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.project import Project
from app.models.screenplay import Character, Scene
from app.services import script_parse_status as sps
from app.services.canonical_production_state import CanonicalProductionStateBuilder
from app.services.optimizer_handoff import build_optimizer_input
from app.services.script_analysis_service import (
    analyze_project_script,
    resolve_active_screenplay,
)

router = APIRouter(prefix="/script-analysis", tags=["script-analysis"])


async def _require_project(session: AsyncSession, project_id: uuid.UUID) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects/{project_id}/parse")
async def parse_project_script(
    project_id: uuid.UUID, force: bool = False, db: AsyncSession = Depends(get_db)
) -> dict:
    """Run the deterministic parse for the project's active screenplay."""
    await _require_project(db, project_id)
    summary = await analyze_project_script(db, project_id=project_id, force=force)
    await db.commit()
    return summary


@router.get("/projects/{project_id}/script")
async def get_project_script(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> dict:
    """Parse status plus the persisted deterministic structure."""
    await _require_project(db, project_id)
    screenplay = await resolve_active_screenplay(db, project_id)
    if screenplay is None:
        return {
            "project_id": str(project_id),
            "status": sps.SCRIPT_NOT_PRESENT,
            "blocker": sps.blocker_for(sps.SCRIPT_NOT_PRESENT),
            "screenplay": None,
        }

    scenes = (await db.execute(
        select(Scene).where(Scene.screenplay_id == screenplay.id).order_by(Scene.sequence)
    )).scalars().all()
    characters = (await db.execute(
        select(Character).where(Character.screenplay_id == screenplay.id)
        .order_by(Character.canonical_name)
    )).scalars().all()

    return {
        "project_id": str(project_id),
        "status": screenplay.parse_status,
        "blocker": sps.blocker_for(screenplay.parse_status or ""),
        "screenplay": {
            "id": str(screenplay.id),
            "filename": screenplay.filename,
            "document_version_id": (
                str(screenplay.document_version_id) if screenplay.document_version_id else None
            ),
            "parser_version": screenplay.parser_version,
            "input_fingerprint": screenplay.input_fingerprint,
            "page_basis": screenplay.page_basis,
            "page_count": screenplay.page_count,
            "total_eighths": screenplay.total_eighths,
            "parse_error": screenplay.parse_error,
            "warnings": screenplay.parse_warnings or [],
        },
        "scene_count": len(scenes),
        "character_count": len(characters),
        "scenes": [
            {
                "sequence": s.sequence,
                "source_scene_number": s.source_scene_number,
                "heading": s.raw_heading,
                "int_ext": s.int_ext,
                "time_of_day": s.time_of_day,
                "scripted_location": s.scripted_location,
                "location_key": s.location_key,
                "page_start": s.page_start,
                "eighths": s.eighths,
            }
            for s in scenes
        ],
        "characters": [
            {
                "name": c.canonical_name,
                "is_speaking_role": c.is_speaking_role,
                "scene_count": c.scene_count,
                "dialogue_blocks": c.dialogue_block_count,
                "dialogue_words": c.dialogue_word_count,
                "eighths_burden": c.eighths_burden,
            }
            for c in characters
        ],
    }


@router.get("/projects/{project_id}/state")
async def get_canonical_state(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> dict:
    """The fingerprinted CanonicalProductionState for a generic project."""
    await _require_project(db, project_id)
    state = await CanonicalProductionStateBuilder(db).build(project_id)
    return state.as_dict()


@router.get("/projects/{project_id}/optimizer-input")
async def get_optimizer_input(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> dict:
    """The ProductionOptimizerInput contract, or the reason it is blocked."""
    await _require_project(db, project_id)
    state = await CanonicalProductionStateBuilder(db).build(project_id)
    result = build_optimizer_input(state)
    return {
        "project_id": str(project_id),
        "readiness": state.readiness,
        "state_fingerprint": state.input_fingerprint,
        **result.as_dict(),
    }
