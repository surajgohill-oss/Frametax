"""Durable project visibility is separate from calculation freshness (Project Library and Company Globe).

A project whose retained generation is stale (older engine, or inputs changed since) must stay visible and be labelled stale; a project that was
never evaluated stays 'Submitted'. Reading visibility never evaluates, regenerates, writes a generation, reconciles a saved selection, or
changes is_served_production (which stays the CURRENT-generation signal). SYNTHETIC rolled-back records on the isolated test database only."""
from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.api.v1.projects import list_projects
from app.models.production import EvaluationGenerationSummary
from app.models.project import Project
from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint
from app.services.portfolio_globe_view import build_portfolio_globe, evaluation_freshness
from tests.isolated_records import create_synthetic_project, isolated_session

pytestmark = pytest.mark.asyncio
OLD_ENGINE = "canonical-0.0.1"


def _summary(project_id, engine, fingerprint):
    return EvaluationGenerationSummary(
        project_id=project_id, input_fingerprint=fingerprint, engine_version=engine, total_rows=1, priced_count=1, unpriced_count=0,
        by_disposition={}, by_reason=[], non_rejected_ordinals=[0], persisted_rows=1, aggregated_candidates=0, aggregated_priced=0, aggregate_groups=0)


async def _setup(db):
    import uuid
    ids = {}
    for key in ("engine_stale", "input_changed", "current", "never", "archived_stale"):
        ids[key] = await create_synthetic_project(db, home_code="MU", title_suffix=f" {key}")
    org_id = (await db.execute(select(Project.organization_id).where(Project.id == ids["never"]))).scalar_one()
    db.add(_summary(uuid.UUID(ids["engine_stale"]), OLD_ENGINE, "a" * 64))
    db.add(_summary(uuid.UUID(ids["input_changed"]), ENGINE_VERSION, "b" * 64))
    db.add(_summary(uuid.UUID(ids["archived_stale"]), OLD_ENGINE, "c" * 64))
    current_fp = await current_generation_fingerprint(db, uuid.UUID(ids["current"]))
    db.add(_summary(uuid.UUID(ids["current"]), ENGINE_VERSION, current_fp))
    archived = await db.get(Project, uuid.UUID(ids["archived_stale"]))
    archived.lifecycle = "ARCHIVED"
    stale = await db.get(Project, uuid.UUID(ids["engine_stale"]))
    stale.portfolio_globe_snapshot = {"schema": 2, "engine_version": OLD_ENGINE, "fingerprint": "a" * 64, "baseline_jurisdiction": "MU",
                                       "home_code": "MU", "gross_budget_usd": 1_600_000.0, "structures": []}
    await db.flush()
    return ids, org_id


async def test_freshness_distinguishes_current_stale_by_engine_stale_by_inputs_and_never_evaluated():
    import uuid
    async with isolated_session() as db:
        ids, _org = await _setup(db)
        info = await evaluation_freshness(db, [uuid.UUID(v) for v in ids.values()])
    state = {k: (info[uuid.UUID(v)]["state"], info[uuid.UUID(v)]["reason"]) for k, v in ids.items()}
    assert state["current"] == ("CURRENT", None)
    assert state["engine_stale"] == ("STALE", "ENGINE_VERSION")
    assert state["input_changed"] == ("STALE", "INPUT_CHANGED")
    assert state["never"] == ("NONE", None)
    assert info[uuid.UUID(ids["engine_stale"])]["retained_engine_version"] == OLD_ENGINE


async def test_the_retained_engine_version_is_the_numerically_latest_not_the_lexicographic_maximum():
    import uuid
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU")
        for engine in ("canonical-1.99.0", "canonical-1.122.0", "canonical-1.100.0"):
            db.add(_summary(uuid.UUID(pid), engine, engine[-6:].ljust(64, "d")))
        await db.flush()
        info = await evaluation_freshness(db, [uuid.UUID(pid)])
    assert info[uuid.UUID(pid)]["retained_engine_version"] == "canonical-1.122.0"


async def test_the_library_keeps_stale_productions_labelled_and_never_marks_them_served():
    async with isolated_session() as db:
        ids, org_id = await _setup(db)
        cards = {str(c.id): c for c in await list_projects(organization_id=str(org_id), include_fixtures=False, db=db)}
    assert cards[ids["current"]].is_served_production is True and cards[ids["current"]].evaluation_freshness == "CURRENT"
    for key, reason in (("engine_stale", "ENGINE_VERSION"), ("input_changed", "INPUT_CHANGED")):
        card = cards[ids[key]]
        assert card.is_served_production is False, "a stale generation is never read as current"
        assert (card.evaluation_freshness, card.evaluation_stale_reason) == ("STALE", reason)
    assert cards[ids["never"]].evaluation_freshness == "NONE" and cards[ids["never"]].is_served_production is False


async def test_the_company_globe_keeps_stale_productions_without_evaluating_or_writing_anything(monkeypatch):
    # Hermetic (NA-RECONCILIATION-15): the isolated database also holds a pre-existing project whose generation is CURRENT, and the globe rebuilds the derived snapshot cache of a
    # current project (a cache write, never an evaluation). The write guard rightly refuses that write to a non-synthetic row, so this control looks only at its own synthetic projects.
    import app.api.v1.projects as _projects
    monkeypatch.setattr(_projects, "_is_producer_visible", lambda title: bool(title) and title.startswith("SYNTHETIC test project"))
    async with isolated_session() as db:
        ids, org_id = await _setup(db)
        before = (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary))).scalar_one()
        snapshot_before = (await db.get(Project, __import__("uuid").UUID(ids["engine_stale"]))).portfolio_globe_snapshot
        globe = await build_portfolio_globe(db, org_id)
        after = (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary))).scalar_one()
        snapshot_after = (await db.get(Project, __import__("uuid").UUID(ids["engine_stale"]))).portfolio_globe_snapshot
    rows = {r["project_id"]: r for r in globe["projects"]}
    for key, reason in (("engine_stale", "ENGINE_VERSION"), ("input_changed", "INPUT_CHANGED")):
        row = rows[ids[key]]
        assert (row["economics_freshness"], row["economics_stale_reason"], row["is_served_production"]) == ("STALE", reason, False)
        assert row["home_code"] == "MU" and row["baseline_jurisdiction"] == "MU", "drawn at its anchor, never dropped"
        assert row["leading"]["structure"] is None and row["leading"]["source"] == "baseline"
    assert ids["never"] not in rows, "a never-evaluated project is Submitted, not active"
    assert ids["archived_stale"] not in rows, "an archived project stays out even when its retained generation is stale"
    assert globe["stale_economics"] >= 2
    assert before == after and snapshot_before == snapshot_after, "visibility must not evaluate, regenerate or rewrite a snapshot"
