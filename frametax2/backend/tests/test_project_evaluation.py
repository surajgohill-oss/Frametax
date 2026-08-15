"""
Begin Evaluation runtime closeout — regression tests for the generic
project evaluation orchestrator.

"Begin Evaluation" was a hardcoded-disabled button (DEAD_BUTTON) for any
project other than Little Utopia. These tests lock in the fix:
`app/services/project_evaluation.py::begin_evaluation` connects a
project's CanonicalProductionState to the existing, already-populated,
DB-backed worldwide structures API (app/api/v1/structures.py,
run_full_analysis) — generically, for any project, with no project ever
named in the orchestration code itself.

Same isolation pattern as test_material_routing.py: real Postgres dev DB,
explicit disposable Organization/Project per test, cleaned up in a
finally block (cascades ProductionStructure/StructureCalculationResult).
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.project import Project
from app.models.ingestion_candidate import IngestionCandidate
from app.models.production import ProductionStructure
from app.api.v1.ingestion import discover, commit_candidate, DiscoverRequest
from app.services.project_evaluation import begin_evaluation


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Evaluation Test Org", slug=f"evaluation-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Evaluation Test Project {uuid.uuid4().hex[:8]}")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    project_id = p.id
    try:
        yield p
    finally:
        still_there = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if still_there is not None:
            await db.execute(sa_delete(Project).where(Project.id == project_id))
            await db.commit()


def _write(tmp_path, name: str, content: bytes) -> str:
    path = tmp_path / name
    path.write_bytes(content)
    return str(path)


_SCREENPLAY_TEXT = """THE SALT ROAD
Written by A. Nonymous

FADE IN:

1  EXT. COASTAL HIGHWAY - DAY

A battered pickup truck grinds along a cliff road.

MARA
We're losing daylight.

FADE OUT.
"""

_BUDGET_CSV = (
    "description,amount,department\n"
    "Director fee,50000,Above the Line\n"
    "Camera crew labor,75000,Below the Line\n"
    "Grip equipment rental,25000,Below the Line\n"
)


async def _commit(db: AsyncSession, project: Project, dir_path, filename: str, content: bytes):
    dir_path.mkdir(parents=True, exist_ok=True)
    _write(dir_path, filename, content)
    await discover(DiscoverRequest(source_type="local", source_pointer=str(dir_path), project_id=str(project.id)), db)
    candidate = (await db.execute(
        select(IngestionCandidate).where(
            IngestionCandidate.proposed_project_id == project.id, IngestionCandidate.status == "pending",
        )
    )).scalar_one()
    await commit_candidate(str(candidate.id), db)


async def test_begin_evaluation_reports_budget_required_when_no_budget(
    db: AsyncSession, project: Project, tmp_path
):
    """Script-only project (Test 5/6's own fixture case, revisited one
    layer deeper): Begin Evaluation must never crash, never fabricate a
    budget, and never create a structure it can't honestly price."""
    await _commit(db, project, tmp_path / "script", "Screenplay.txt", _SCREENPLAY_TEXT.encode())

    result = await begin_evaluation(db, project.id)
    assert result["status"] == "BUDGET_REQUIRED_FOR_CURRENT_EVALUATION"
    assert any("BUDGET_MISSING" in b for b in result["blockers"])

    structures = (await db.execute(
        select(ProductionStructure).where(ProductionStructure.project_id == project.id)
    )).scalars().all()
    assert structures == []


async def test_begin_evaluation_derives_home_jurisdiction_from_budget_filename_and_prices_it(
    db: AsyncSession, project: Project, tmp_path
):
    """Generic geography derivation (Step 5): a jurisdiction name present
    in the budget's own filename — here Malta, not Greece — must be
    picked up as the confirmed base and actually priced through the real
    discovery + structures + run_full_analysis chain. Nothing about Malta
    is hardcoded anywhere in the orchestrator; this filename alone drives it."""
    await _commit(db, project, tmp_path / "script", "Screenplay.txt", _SCREENPLAY_TEXT.encode())
    await _commit(db, project, tmp_path / "budget", "Production Budget - Malta Shoot.csv", _BUDGET_CSV.encode())

    result = await begin_evaluation(db, project.id)
    assert result["status"] == "EVALUATION_COMPLETE"
    assert result["gross_budget_usd"] == 150000
    assert result["priced_count"] >= 1
    assert result["baseline"]["name"] == "Malta — production's current base"
    assert result["baseline"]["true_net_cost_usd"] is not None
    assert result["mfni_limitation"]

    await db.refresh(project)
    assert project.leading_structure_id is not None

    from app.models.jurisdiction import Jurisdiction
    home = await db.get(Jurisdiction, project.home_jurisdiction_id)
    assert home.name == "Malta"


async def test_begin_evaluation_is_idempotent_on_repeat_calls(db: AsyncSession, project: Project, tmp_path):
    """Repeated clicks against unchanged inputs must not duplicate
    ProductionStructure rows."""
    await _commit(db, project, tmp_path / "script", "Screenplay.txt", _SCREENPLAY_TEXT.encode())
    await _commit(db, project, tmp_path / "budget", "Budget - Malta.csv", _BUDGET_CSV.encode())

    first = await begin_evaluation(db, project.id)
    assert first["status"] == "EVALUATION_COMPLETE"
    second = await begin_evaluation(db, project.id)
    assert second["status"] == "EVALUATION_REUSED"

    structures = (await db.execute(
        select(ProductionStructure).where(ProductionStructure.project_id == project.id)
    )).scalars().all()
    assert len(structures) == first["priced_count"]


async def test_project_evaluation_module_contains_no_project_specific_code():
    """Regression guard matching test_material_routing.py's own: no
    per-project runner or hardcoded jurisdiction/project branch in the
    orchestration code itself. Checked against function/branch
    definitions only — the module's own docstring legitimately names FVD/
    Little Utopia in prose to explain what it does NOT special-case, same
    convention as test_material_routing.py's equivalent guard."""
    import inspect

    from app.services import project_evaluation as mod

    src = inspect.getsource(mod)
    for banned in (
        "def run_fvd", "def run_little_utopia", "def _route_fvd",
        'code == "GR"', 'code == "MU"', 'jurisdiction_code == "GR"', 'jurisdiction_code == "MU"',
    ):
        assert banned not in src, f"project_evaluation.py must stay project-agnostic; found {banned!r}"
