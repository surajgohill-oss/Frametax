"""User-selected leading structure (2026-10-08).

The producer's "Set as Leading" choice overrides the canonical leader. Structure rows are re-created for every
evaluation generation, so the choice is persisted by its run-independent economic identity
(Project.leading_selection_identity) and re-resolved against each new generation:

* identity found in the current generation -> that structure keeps leading;
* identity gone after a legitimate regeneration -> fall back to the canonical leader and disclose the selection as
  unavailable; never mapped to a different structure.

Applied on the served read (reconcile_selection, called from canonical_production_view), never inside
canonical_evaluation.py: that module's source bytes feed every project's input fingerprint. No evaluation is ever
triggered from here.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production import ProductionStructure, StructureCalculationResult

_ROW_PREFIX = "structure:"


async def _latest_result(session: AsyncSession, structure_id) -> StructureCalculationResult | None:
    return (await session.execute(
        select(StructureCalculationResult)
        .where(StructureCalculationResult.structure_id == structure_id)
        .order_by(StructureCalculationResult.created_at.desc())
        .limit(1)
    )).scalars().first()


async def selection_identity(session: AsyncSession, structure_id) -> str | None:
    """Stable identity recorded when the producer selects `structure_id` (None clears the selection)."""
    if structure_id is None:
        return None
    result = await _latest_result(session, structure_id)
    return (result.economic_identity if result is not None else None) or f"{_ROW_PREFIX}{structure_id}"


async def resolve_selection(
    session: AsyncSession, project_id, identity: str, *, engine_version: str, fingerprint: str,
) -> uuid.UUID | None:
    """The current-generation structure carrying `identity`, or None when it no longer exists."""
    current = (
        (StructureCalculationResult.engine_version == engine_version)
        & (StructureCalculationResult.input_fingerprint == fingerprint)
    )
    if identity.startswith(_ROW_PREFIX):
        try:
            structure_id = uuid.UUID(identity[len(_ROW_PREFIX):])
        except ValueError:
            return None
        clause = StructureCalculationResult.structure_id == structure_id
    else:
        clause = StructureCalculationResult.economic_identity == identity
    return (await session.execute(
        select(StructureCalculationResult.structure_id)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(ProductionStructure.project_id == project_id, current, clause)
        .limit(1)
    )).scalars().first()


def choose_leading(identity: str | None, user_match_id, canonical_id):
    """(leading_structure_id, unavailable) for one evaluation. Pure, so the contract is testable without a DB."""
    if not identity:
        return canonical_id, False
    if user_match_id is not None:
        return user_match_id, False
    return canonical_id, True


async def reconcile_selection(session: AsyncSession, project, *, engine_version: str, fingerprint: str) -> None:
    """Point leading_structure_id back at the producer's choice in the current generation when it still exists.
    A pointer write only; when the choice is gone the canonical leader the evaluation set is left in place."""
    identity = getattr(project, "leading_selection_identity", None)
    if not identity:
        return
    match = await resolve_selection(session, project.id, identity, engine_version=engine_version, fingerprint=fingerprint)
    target, unavailable = choose_leading(identity, match, project.leading_structure_id)
    if not unavailable and project.leading_structure_id != target:
        project.leading_structure_id = target
        await session.commit()


async def selection_status(session: AsyncSession, project) -> dict:
    """Served disclosure: whether the leader is the producer's choice and whether that choice became unavailable."""
    identity = getattr(project, "leading_selection_identity", None)
    if not identity:
        return {"user_selected": False, "unavailable": False}
    if project.leading_structure_id is None:
        return {"user_selected": True, "unavailable": True}
    held = await selection_identity(session, project.leading_structure_id)
    return {"user_selected": True, "unavailable": held != identity}
