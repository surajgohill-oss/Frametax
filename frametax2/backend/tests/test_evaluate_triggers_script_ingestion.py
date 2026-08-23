"""
Fresh Project Source-Document Ingestion — script ingestion reconnection.

Root cause (mirrors the budget case): material_routing._route_screenplay
already runs analyze_project_script automatically for every NEW commit --
already connected, not a gap. But a project whose screenplay Document/
DocumentVersion predates that commit-time wiring (bulk-seeded/imported
before routing existed -- confirmed, via direct trace, to be Lips Like
Sugar's own real state) has an attached screenplay that was simply never
analyzed.

canonical_evaluation.evaluate_project now calls analyze_project_script
(the existing, unchanged SA-1 pipeline) once budget+base-jurisdiction are
resolved and before role_known_codes/script_facts are read -- the same
retroactive-trigger pattern as ensure_current_budget_routed, reusing the
existing script analyzer, never a second implementation.
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
from app.models.jurisdiction import Jurisdiction
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.models.screenplay import ScreenplayDocument
from app.services.canonical_evaluation import evaluate_project


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def mu_jurisdiction(db: AsyncSession):
    row = (await db.execute(select(Jurisdiction).where(Jurisdiction.code == "MU"))).scalars().first()
    assert row is not None, "MU jurisdiction must already be seeded — not created by this test"
    return row


@pytest.fixture
async def project(db: AsyncSession, mu_jurisdiction: Jurisdiction):
    org = Organization(name="Script Ingestion Test Org", slug=f"script-ingest-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(
        id=uuid.uuid4(), organization_id=org.id, title=f"Script Ingestion Test {uuid.uuid4().hex[:8]}",
        home_jurisdiction_id=mu_jurisdiction.id, format="feature_film",
    )
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
        storage_dir = Path(get_settings().LOCAL_STORAGE_PATH) / f"script-ingest-test-{project_id}"
        if storage_dir.exists():
            shutil.rmtree(storage_dir)


def _write_film_budget_pdf(path: Path, account_lines: list[tuple[str, str, int]]) -> None:
    lines = ["TEST PRODUCTION", "Account", "Description", "Total"]
    for code, desc, amt in account_lines:
        lines += [code, desc, f"${amt:,}"]
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "\n".join(lines), fontsize=10)
    doc.save(str(path))
    doc.close()


def _write_screenplay_pdf(path: Path) -> None:
    text = (
        "TEST SCRIPT\n\n"
        "INT. WAREHOUSE - NIGHT\n\n"
        "JORDAN stands alone.\n\n"
        "                    JORDAN\n"
        "          This is a test screenplay.\n\n"
        "EXT. STREET - DAY\n\n"
        "JORDAN walks away.\n"
    )
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()


async def _seed_unrouted_document(
    db: AsyncSession, project: Project, category: str, filename: str, write_fn,
) -> DocumentVersion:
    """Simulates a pre-existing Library production whose material predates
    material_routing.py's commit-time wiring -- created WITHOUT going
    through commit_candidate, matching Lips Like Sugar's real observed
    state for both its budget AND its screenplay."""
    settings = get_settings()
    storage_dir = Path(settings.LOCAL_STORAGE_PATH) / f"script-ingest-test-{project.id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / filename
    write_fn(file_path)

    doc = Document(id=uuid.uuid4(), project_id=project.id, category=category, title=f"{project.title} — {category}")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=doc.id, original_filename=filename,
        storage_path=f"script-ingest-test-{project.id}/{filename}", is_current=True,
    )
    db.add(version)
    await db.flush()
    doc.current_version_id = version.id
    await db.commit()
    await db.refresh(version)
    return version


async def test_evaluate_project_triggers_retroactive_script_analysis(db: AsyncSession, project: Project):
    """The exact live-path proof: once budget+jurisdiction are resolved,
    evaluate_project must trigger real script analysis for a screenplay
    that predates commit-time routing -- without any manual trigger."""
    await _seed_unrouted_document(
        db, project, "budget", "Test Budget.pdf",
        lambda p: _write_film_budget_pdf(p, [("1100", "SCRIPT", 500_000), ("1400", "CAST", 800_000)]),
    )
    await _seed_unrouted_document(db, project, "screenplay", "Test Script.pdf", _write_screenplay_pdf)

    before = (await db.execute(
        select(ScreenplayDocument).where(ScreenplayDocument.project_id == project.id)
    )).scalars().first()
    assert before is None  # confirms the simulated legacy/unrouted state

    result = await evaluate_project(db, project.id)
    assert result.get("status") != "PROJECT_NOT_FOUND"

    after = (await db.execute(
        select(ScreenplayDocument).where(ScreenplayDocument.project_id == project.id)
    )).scalars().first()
    assert after is not None, (
        "evaluate_project must trigger analyze_project_script for a "
        "legacy-imported screenplay once budget/jurisdiction resolve"
    )
