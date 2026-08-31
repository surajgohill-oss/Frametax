"""
New Project Ingestor closeout — material routing regression tests.

`_commit_candidate_impl` (app/api/v1/ingestion.py) never touched facts or
optimizer state, by design. That left every real project's budget total
and script breakdown depending on ad-hoc one-off scripts rather than the
actual product flow — the defect this phase fixes. These tests lock in
the fix: `POST /candidates/{id}/commit` (the `commit_candidate` route
handler) now also routes a committed budget/screenplay DocumentVersion to
the existing budget parser / SA-1 script pipeline, generically, for any
project — not just F#K Valentine's Day or Little Utopia.

Same isolation pattern as test_ingestion_api.py: real Postgres dev DB,
explicit disposable Organization/Project per test, cleaned up in a
finally block regardless of pass/fail.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.project import Project
from app.models.library_document import Document, DocumentVersion
from app.models.ingestion_candidate import IngestionCandidate
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.project_fact import ProjectFact
from app.api.v1.ingestion import discover, commit_candidate, DiscoverRequest
from app.api.v1.projects import get_project_record
from app.ingestion.budget_parser import BUDGET_PARSER_VERSION


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Material Routing Test Org", slug=f"material-routing-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Material Routing Test Project {uuid.uuid4().hex[:8]}")
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

A battered pickup truck grinds along a cliff road. Below, the sea.

MARA
We're losing daylight.

DRIVER
Then stop talking and watch the road.

2  INT. ROADSIDE DINER - NIGHT

Fluorescent hum. A dog sleeps under the counter.

MARA
Two coffees. Black.

FADE OUT.
"""

_BUDGET_CSV = (
    "description,amount,department\n"
    "Director fee,50000,Above the Line\n"
    "Camera crew labor,75000,Below the Line\n"
    "Grip equipment rental,25000,Below the Line\n"
)


async def test_budget_commit_routes_to_budget_document_and_sets_project_total(
    db: AsyncSession, project: Project, tmp_path
):
    _write(tmp_path, "Budget.csv", _BUDGET_CSV.encode())
    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    candidate = (await db.execute(
        select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id)
    )).scalar_one()
    assert candidate.proposed_category == "budget"

    result = await commit_candidate(str(candidate.id), db)
    assert result["material_routing"] == "budget_routed"

    doc = (await db.execute(select(Document).where(Document.project_id == project.id))).scalar_one()
    budget_doc = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.document_version_id == uuid.UUID(result["document_version_id"]))
    )).scalar_one()
    assert budget_doc.total_budget_raw == 150000

    line_items = (await db.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == budget_doc.id)
    )).scalars().all()
    assert len(line_items) == 3

    await db.refresh(project)
    assert project.total_budget_usd == 150000


async def test_budget_commit_is_idempotent_on_recommit(db: AsyncSession, project: Project, tmp_path):
    """Re-routing the same DocumentVersion (e.g. a re-triggered commit) must
    never create a second BudgetDocument for it."""
    from app.services.material_routing import route_committed_material

    _write(tmp_path, "Budget.csv", _BUDGET_CSV.encode())
    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    candidate = (await db.execute(
        select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id)
    )).scalar_one()
    result = await commit_candidate(str(candidate.id), db)
    document_version_id = uuid.UUID(result["document_version_id"])

    await route_committed_material(db, project_id=project.id, category="budget", document_version_id=document_version_id)
    await db.commit()

    budget_docs = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.document_version_id == document_version_id)
    )).scalars().all()
    assert len(budget_docs) == 1


async def test_budget_commit_stamps_the_current_parser_version(db: AsyncSession, project: Project, tmp_path):
    """A. Canonical Ingestion/Analysis Propagation: a fresh budget commit
    must be marked with the CURRENT BUDGET_PARSER_VERSION — the version
    marker screenplay routing already had and budget routing previously
    lacked entirely."""
    _write(tmp_path, "Budget.csv", _BUDGET_CSV.encode())
    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    candidate = (await db.execute(
        select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id)
    )).scalar_one()
    result = await commit_candidate(str(candidate.id), db)
    budget_doc = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.document_version_id == uuid.UUID(result["document_version_id"]))
    )).scalar_one()
    assert budget_doc.parser_version == BUDGET_PARSER_VERSION


async def test_stale_budget_parser_version_triggers_reparse_and_backfills_version(
    db: AsyncSession, project: Project, tmp_path,
):
    """A/B. A BudgetDocument parsed under an OLDER (or, as here, NULL —
    pre-dating the version column) parser version is genuinely stale.
    ensure_current_budget_routed (the same retroactive-trigger pattern
    already used for screenplay/artwork) must reparse it and backfill the
    current version — never leave it stuck forever just because a
    BudgetDocument row already exists."""
    from app.services.material_routing import ensure_current_budget_routed

    local_path = _write(tmp_path, "Budget.csv", _BUDGET_CSV.encode())
    doc = Document(id=uuid.uuid4(), project_id=project.id, category="budget", title="Test Budget")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=doc.id, original_filename="Budget.csv",
        storage_path=local_path, is_current=True,
    )
    db.add(version)
    await db.flush()
    doc.current_version_id = version.id
    # Simulate a pre-existing, already-routed BudgetDocument with NO
    # parser_version (the real state of every project's row before this
    # migration) and stale/incomplete data — one line item, not three.
    stale_doc = BudgetDocument(
        id=uuid.uuid4(), project_id=project.id, filename="Budget.csv", file_type="csv",
        document_version_id=version.id, total_budget_raw=1.0, parser_version=None,
    )
    db.add(stale_doc)
    await db.flush()
    db.add(BudgetLineItem(id=uuid.uuid4(), budget_document_id=stale_doc.id, description="stale line", amount_usd=1.0))
    await db.commit()

    result = await ensure_current_budget_routed(db, project.id)
    assert result is not None

    refreshed = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.document_version_id == version.id)
    )).scalars().all()
    assert len(refreshed) == 1, "must refresh the SAME row, never create a second BudgetDocument for this DocumentVersion"
    assert refreshed[0].parser_version == BUDGET_PARSER_VERSION
    assert refreshed[0].total_budget_raw == 150000

    line_items = (await db.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == refreshed[0].id)
    )).scalars().all()
    assert len(line_items) == 3, "the stale single line item must be replaced by the real reparsed set, not appended to"


async def test_current_parser_version_is_genuinely_idempotent_no_reparse(
    db: AsyncSession, project: Project, tmp_path,
):
    """A BudgetDocument already at the CURRENT parser version must not be
    reparsed again — the version-aware guard's fast path."""
    from app.services.material_routing import ensure_current_budget_routed

    local_path = _write(tmp_path, "Budget.csv", _BUDGET_CSV.encode())
    doc = Document(id=uuid.uuid4(), project_id=project.id, category="budget", title="Test Budget")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=doc.id, original_filename="Budget.csv",
        storage_path=local_path, is_current=True,
    )
    db.add(version)
    await db.flush()
    doc.current_version_id = version.id
    current_doc = BudgetDocument(
        id=uuid.uuid4(), project_id=project.id, filename="Budget.csv", file_type="csv",
        document_version_id=version.id, total_budget_raw=999.0, parser_version=BUDGET_PARSER_VERSION,
    )
    db.add(current_doc)
    await db.commit()

    await ensure_current_budget_routed(db, project.id)

    refreshed = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.document_version_id == version.id)
    )).scalars().first()
    # total_budget_raw is untouched (999.0, not the real CSV's 150000) —
    # proves the reparse never ran at all, not merely that it produced the
    # same number.
    assert refreshed.total_budget_raw == 999.0


async def test_failed_reparse_preserves_last_valid_budget_data(db: AsyncSession, project: Project, tmp_path):
    """E. A reparse attempt against a missing/unreadable source file must
    never wipe out the existing, still-valid parsed data — a failed
    reanalysis leaves the last-known-good state completely untouched."""
    from app.services.material_routing import ensure_current_budget_routed

    doc = Document(id=uuid.uuid4(), project_id=project.id, category="budget", title="Test Budget")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=doc.id, original_filename="Budget.csv",
        storage_path=str(tmp_path / "does-not-exist.csv"), is_current=True,
    )
    db.add(version)
    await db.flush()
    doc.current_version_id = version.id
    stale_doc = BudgetDocument(
        id=uuid.uuid4(), project_id=project.id, filename="Budget.csv", file_type="csv",
        document_version_id=version.id, total_budget_raw=42.0, parser_version=None,
    )
    db.add(stale_doc)
    await db.commit()

    result = await ensure_current_budget_routed(db, project.id)
    assert result is None  # missing-source early exit — same as the pre-existing behavior

    still_there = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.document_version_id == version.id)
    )).scalars().first()
    assert still_there is not None
    assert still_there.total_budget_raw == 42.0, "the last-valid parsed data must survive a failed reparse attempt"


async def test_screenplay_commit_triggers_sa1_pipeline_and_persists_facts(
    db: AsyncSession, project: Project, tmp_path
):
    _write(tmp_path, "Screenplay.txt", _SCREENPLAY_TEXT.encode())
    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    candidate = (await db.execute(
        select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id)
    )).scalar_one()
    assert candidate.proposed_category == "screenplay"

    result = await commit_candidate(str(candidate.id), db)
    assert result["material_routing"] == "screenplay_routed"

    facts = (await db.execute(
        select(ProjectFact).where(ProjectFact.project_id == project.id)
    )).scalars().all()
    fact_keys = {f.fact_key for f in facts}
    assert "script_total_scenes" in fact_keys
    assert "script_unique_scripted_locations" in fact_keys

    scene_count_fact = next(f for f in facts if f.fact_key == "script_total_scenes")
    assert scene_count_fact.value == "2"


async def test_deck_commit_has_no_processor_and_is_a_no_op(db: AsyncSession, project: Project, tmp_path):
    """A category with no routing processor (deck, schedule, artwork, ...)
    must commit successfully with material_routing reported as None — the
    generic commit already fully serves it; there is nothing to route to."""
    _write(tmp_path, "Deck.pptx", b"fake deck bytes")
    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    candidate = (await db.execute(
        select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id)
    )).scalar_one()

    result = await commit_candidate(str(candidate.id), db)
    assert result["result"] == "new_version_created"
    assert result.get("material_routing") is None


async def test_project_record_falls_back_to_budget_document_total_when_unset(
    db: AsyncSession, project: Project, tmp_path
):
    """The pre-existing-data case (e.g. F#K Valentine's Day): a
    BudgetDocument was created before this phase's commit-time routing
    existed, so Project.total_budget_usd was never set and its
    BudgetDocument.document_version_id link was never backfilled either.
    get_project_record must still surface the real total on read, without
    any write to the project row."""
    budget_doc = BudgetDocument(
        id=uuid.uuid4(), project_id=project.id, filename="Legacy Budget.pdf",
        file_type="pdf", total_budget_raw=987654.0, document_version_id=None,
    )
    db.add(budget_doc)
    await db.commit()

    record = await get_project_record(str(project.id), db)
    assert record["project"]["total_budget_usd"] == 987654.0

    await db.refresh(project)
    assert project.total_budget_usd is None  # read-only fallback — column itself untouched


async def test_material_routing_module_contains_no_project_specific_code():
    """Regression guard for the exact anti-pattern this phase's own audit
    found and forbade: a per-project runner function (run_fvd_optimizer.py,
    etc.) standing in for the real, generic product pipeline. Checked
    against function/branch definitions only — the module's own docstring
    legitimately names Little Utopia/FVD in prose to explain what it does
    NOT special-case, same convention as test_real_production_corpus.py's
    equivalent guard."""
    import inspect

    from app.services import material_routing as mod

    src = inspect.getsource(mod)
    for banned in (
        "def run_fvd", "def run_little_utopia", "def _route_fvd", "def _route_little_utopia",
        'proposed_category == "fvd"', "project.title ==",
    ):
        assert banned not in src, f"material_routing.py must stay project-agnostic; found {banned!r}"
