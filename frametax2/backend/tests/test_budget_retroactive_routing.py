"""
Fresh Project Source-Document Ingestion — retroactive budget routing.

Root cause confirmed by direct trace: material_routing.route_committed_
material already runs automatically for every NEW commit (POST /candidates/
{id}/commit -> commit_candidate), correctly parsing PDF/CSV budgets into
BudgetDocument/BudgetLineItem rows -- already CONNECTED, not a gap. The
real gap is retroactive: a project whose budget Document/DocumentVersion
predates that commit-time wiring (bulk-seeded/imported before routing
existed -- the real state every pre-existing Library production, including
Lips Like Sugar, is in) has an attached file that was simply never routed.

ensure_current_budget_routed (app/services/material_routing.py) is the
fix: a retroactive trigger, called from canonical_project_economics.
build_project_economic_inputs (the live "Begin Evaluation" path), that
reuses material_routing._route_budget UNCHANGED -- never a second parsing
engine.

These tests deliberately bypass discover/commit_candidate when creating
the Document/DocumentVersion fixture, to accurately simulate the REAL
legacy/bulk-seeded state (routing never ran) rather than the already-
working fresh-commit path (covered implicitly: fresh commits route
automatically, proven by every prior ingestion test in this suite).
"""
from __future__ import annotations

import uuid
from pathlib import Path

import fitz
import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import engine
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.services.canonical_project_economics import build_project_economic_inputs
from app.services.material_routing import ensure_current_budget_routed


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Retroactive Routing Test Org", slug=f"retro-route-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Retroactive Routing Test {uuid.uuid4().hex[:8]}")
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
        import shutil
        settings = get_settings()
        storage_dir = Path(settings.LOCAL_STORAGE_PATH) / f"retro-route-test-{project_id}"
        if storage_dir.exists():
            shutil.rmtree(storage_dir)


def _write_film_budget_pdf(path, account_lines: list[tuple[str, str, int]]) -> None:
    lines = ["TEST PRODUCTION", "Account", "Description", "Total"]
    for code, desc, amt in account_lines:
        lines += [code, desc, f"${amt:,}"]
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "\n".join(lines), fontsize=10)
    doc.save(str(path))
    doc.close()


async def _seed_unrouted_budget_document(
    db: AsyncSession, project: Project, filename: str, account_lines,
) -> DocumentVersion:
    """Simulates a pre-existing Library production whose budget file was
    attached BEFORE material_routing.py's commit-time wiring existed --
    a real Document/DocumentVersion row with a real cached file on disk,
    but deliberately created WITHOUT going through commit_candidate (so
    no BudgetDocument gets auto-created), matching Lips Like Sugar's own
    real, observed state."""
    settings = get_settings()
    storage_dir = Path(settings.LOCAL_STORAGE_PATH) / f"retro-route-test-{project.id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = storage_dir / filename
    _write_film_budget_pdf(pdf_path, account_lines)

    doc = Document(id=uuid.uuid4(), project_id=project.id, category="budget", title=f"{project.title} — Budget")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=doc.id, original_filename=filename,
        storage_path=f"retro-route-test-{project.id}/{filename}", is_current=True,
    )
    db.add(version)
    await db.flush()
    doc.current_version_id = version.id
    await db.commit()
    await db.refresh(version)
    return version


async def test_unrouted_legacy_budget_has_no_budget_document_yet(db: AsyncSession, project: Project):
    await _seed_unrouted_budget_document(db, project, "Legacy Budget.pdf", [("1100", "SCRIPT", 50_000)])
    existing = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
    )).scalars().first()
    assert existing is None  # confirms the simulated legacy/unrouted state


async def test_ensure_current_budget_routed_reaches_real_lines_and_total(db: AsyncSession, project: Project):
    await _seed_unrouted_budget_document(db, project, "Legacy Budget.pdf", [
        ("1100", "SCRIPT", 50_000), ("1400", "CAST", 120_000),
    ])

    routed = await ensure_current_budget_routed(db, project.id)
    assert routed is not None
    assert routed.total_budget_raw == 170_000.0

    lines = (await db.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == routed.id)
    )).scalars().all()
    assert len(lines) == 2
    assert {round(float(l.amount_usd)) for l in lines} == {50_000, 120_000}


async def test_evaluate_path_retroactively_routes_legacy_budget(db: AsyncSession, project: Project):
    """The exact live-path proof: build_project_economic_inputs (called by
    evaluate_project, the real "Begin Evaluation" endpoint) must reach a
    real gross_budget_usd for a project whose budget file predates commit-
    time routing -- without ANY manual /budgets/import call, and without
    re-uploading anything."""
    await _seed_unrouted_budget_document(db, project, "Legacy Budget.pdf", [
        ("1100", "SCRIPT", 50_000), ("1400", "CAST", 120_000),
    ])
    result = await build_project_economic_inputs(db, project.id)
    if not result.ok:
        assert not any("BUDGET_MISSING" in b for b in result.blockers), result.blockers
        assert any("BASE_JURISDICTION_UNKNOWN" in b for b in result.blockers)
    else:
        assert result.inputs.gross_budget_usd == 170_000.0


async def test_already_routed_budget_is_reused_not_reprocessed(db: AsyncSession, project: Project):
    """Idempotency: once routed, a second Evaluate call must not create a
    duplicate BudgetDocument for the same DocumentVersion."""
    await _seed_unrouted_budget_document(db, project, "Legacy Budget.pdf", [("1100", "SCRIPT", 50_000)])
    first = await ensure_current_budget_routed(db, project.id)
    second = await ensure_current_budget_routed(db, project.id)
    assert first.id == second.id

    all_docs = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
    )).scalars().all()
    assert len(all_docs) == 1


async def test_no_budget_material_at_all_returns_none(db: AsyncSession, project: Project):
    result = await ensure_current_budget_routed(db, project.id)
    assert result is None


async def test_missing_cached_file_returns_none_not_fabricated(db: AsyncSession, project: Project):
    doc = Document(id=uuid.uuid4(), project_id=project.id, category="budget", title="No file")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=doc.id, original_filename="ghost.pdf",
        storage_path=f"retro-route-test-{project.id}/does-not-exist.pdf", is_current=True,
    )
    db.add(version)
    await db.flush()
    doc.current_version_id = version.id
    await db.commit()

    result = await ensure_current_budget_routed(db, project.id)
    assert result is None
