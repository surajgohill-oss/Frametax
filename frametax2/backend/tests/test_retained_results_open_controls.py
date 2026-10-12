"""Retained evaluation history controls opening: a stale evaluated project is OPENED read only from its newest retained generation, labelled stale. Opening never
evaluates, writes a generation, rebuilds a snapshot or touches the saved leading selection; a genuinely unevaluated project stays unevaluated.
SYNTHETIC rolled-back records on the isolated test database only."""
from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import func, select

from app.api.v1.cineglobe import get_project_state
from app.api.v1.projects import get_project_record
from app.models.production import EvaluationGenerationSummary, ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services import canonical_evaluation as ce
from tests.isolated_records import create_synthetic_project, isolated_session

pytestmark = pytest.mark.asyncio


def _summary(project_id, engine, fingerprint):
    return EvaluationGenerationSummary(
        project_id=project_id, input_fingerprint=fingerprint, engine_version=engine, total_rows=0, priced_count=0, unpriced_count=0,
        by_disposition={}, by_reason=[], non_rejected_ordinals=[], persisted_rows=0, aggregated_candidates=0, aggregated_priced=0, aggregate_groups=0)


async def _setup(db):
    stale = uuid.UUID(await create_synthetic_project(db, home_code="MU", title_suffix=" stale"))
    never = uuid.UUID(await create_synthetic_project(db, home_code="MU", title_suffix=" never"))
    db.add(_summary(stale, "canonical-1.50.0", "a" * 64))
    db.add(_summary(stale, "canonical-1.110.0", "b" * 64))
    structure = ProductionStructure(id=uuid.uuid4(), project_id=stale, name="saved leader", jurisdiction_allocations=[], claimed_program_ids=[])
    db.add(structure)
    await db.flush()
    project = await db.get(Project, stale)
    project.leading_structure_id = structure.id
    await db.flush()
    return stale, never, structure.id


async def test_opening_a_stale_projects_results_reads_the_newest_retained_generation_and_never_evaluates(monkeypatch):
    async def forbidden(*a, **k):
        raise AssertionError("opening retained results must not evaluate")
    monkeypatch.setattr(ce, "evaluate_project", forbidden)
    async with isolated_session() as db:
        stale, _never, leader = await _setup(db)
        rows_before = (await db.execute(select(func.count()).select_from(StructureCalculationResult))).scalar_one()
        summaries_before = (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary))).scalar_one()
        response = await get_project_state(str(stale), db)
        body = json.loads(response.body)
        assert body["production"]["evaluation_freshness"] == "STALE"
        assert body["production"]["retained_engine_version"] == "canonical-1.110.0", "the numerically newest retained engine, not the lexicographic maximum"
        assert "structures" in body and "pkg" in body
        assert (await db.execute(select(func.count()).select_from(StructureCalculationResult))).scalar_one() == rows_before
        assert (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary))).scalar_one() == summaries_before
        assert (await db.get(Project, stale)).leading_structure_id == leader, "the saved leading selection is preserved"


async def test_the_record_treats_retained_history_as_evaluated_and_only_a_project_without_history_as_unevaluated():
    async with isolated_session() as db:
        stale, never, _ = await _setup(db)
        a = await get_project_record(str(stale), db)
        assert a["project"]["evaluation_freshness"] == "STALE" and a["project"]["is_served_production"] is False
        assert a["analysis"]["evaluation_begun"] is True and a["analysis"]["retained_evaluation"] is True
        assert a["project"]["retained_engine_version"] == "canonical-1.110.0"
        b = await get_project_record(str(never), db)
        assert b["project"]["evaluation_freshness"] == "NONE" and b["analysis"]["evaluation_begun"] is False and b["analysis"]["retained_evaluation"] is False
