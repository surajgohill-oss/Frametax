"""Retained evaluation history: which generation a read-only view serves when the project has no CURRENT generation.

A project that was evaluated by an older engine (or whose inputs have changed since) keeps its generation rows. Opening its results is a READ: it serves the newest retained
generation, labelled stale, and never evaluates, rebuilds a snapshot, reconciles the saved selection or writes anything. Recalculating is a separate, explicit action.
"""
from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production import EvaluationGenerationSummary


def engine_sort_key(version: str) -> tuple:
    return tuple(int(n) for n in re.findall(r"\d+", version or ""))


async def retained_generation(session: AsyncSession, project_id) -> tuple[str, str] | None:
    """(engine_version, input_fingerprint) of the newest retained complete generation: highest engine version, then most recently written."""
    rows = (await session.execute(
        select(EvaluationGenerationSummary.engine_version, EvaluationGenerationSummary.input_fingerprint, EvaluationGenerationSummary.created_at)
        .where(EvaluationGenerationSummary.project_id == uuid.UUID(str(project_id))))).all()
    if not rows:
        return None
    best = max(rows, key=lambda r: (engine_sort_key(r.engine_version), r.created_at))
    return best.engine_version, best.input_fingerprint
