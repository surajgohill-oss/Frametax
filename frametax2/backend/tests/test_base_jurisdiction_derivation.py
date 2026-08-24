"""
Fresh Project Ingestion, final continuation — base-jurisdiction derivation.

Canonical rule: the base jurisdiction is the jurisdiction in which the
production budget is set, unless an explicit project-level fact overrides
it. _resolve_home_jurisdiction (app/services/canonical_project_economics.py)
is the ONE resolver for the live Evaluate path, precedence:
  1. project.home_jurisdiction_id already confirmed (explicit override).
  2. A jurisdiction NAME in the budget filename -- reuses project_
     evaluation._derive_home_jurisdiction unchanged (already existed,
     already generic, was simply disconnected from the live path).
  3. The currency the budget is denominated in -- new, minimal,
     deterministic, only resolves when genuinely unambiguous.
Never fabricated: an ambiguous/shared currency (EUR alone) stays
unresolved, exactly like a document with no currency marker at all.
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
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_project_economics import (
    _infer_jurisdiction_code_from_currency,
    _resolve_home_jurisdiction,
    build_project_economic_inputs,
)


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def us_jurisdiction(db: AsyncSession):
    row = (await db.execute(select(Jurisdiction).where(Jurisdiction.code == "US"))).scalars().first()
    assert row is not None, "US jurisdiction must already be seeded — not created by this test"
    return row


@pytest.fixture
async def gb_jurisdiction(db: AsyncSession):
    row = (await db.execute(select(Jurisdiction).where(Jurisdiction.code == "GB"))).scalars().first()
    assert row is not None
    return row


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Base Jurisdiction Test Org", slug=f"base-jur-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Base Jurisdiction Test {uuid.uuid4().hex[:8]}")
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
        storage_dir = Path(get_settings().LOCAL_STORAGE_PATH) / f"base-jur-test-{project_id}"
        if storage_dir.exists():
            shutil.rmtree(storage_dir)


def _write_film_budget_pdf(path: Path, account_lines: list[tuple[str, str, int]], currency_marker: str = "$") -> None:
    lines = ["TEST PRODUCTION", "Account", "Description", "Total"]
    for code, desc, amt in account_lines:
        lines += [code, desc, f"{currency_marker}{amt:,}"]
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "\n".join(lines), fontsize=10)
    doc.save(str(path))
    doc.close()


async def _seed_budget(
    db: AsyncSession, project: Project, filename: str, account_lines, currency_marker: str = "$",
) -> DocumentVersion:
    settings = get_settings()
    storage_dir = Path(settings.LOCAL_STORAGE_PATH) / f"base-jur-test-{project.id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = storage_dir / filename
    _write_film_budget_pdf(pdf_path, account_lines, currency_marker)

    doc = Document(id=uuid.uuid4(), project_id=project.id, category="budget", title=f"{project.title} — Budget")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=doc.id, original_filename=filename,
        storage_path=f"base-jur-test-{project.id}/{filename}", is_current=True,
    )
    db.add(version)
    await db.flush()
    doc.current_version_id = version.id
    await db.commit()
    await db.refresh(version)
    return version


# ── unit: the currency inferencer itself ─────────────────────────────────

def test_bare_dollar_sign_alone_infers_us():
    assert _infer_jurisdiction_code_from_currency("Total: $1,200,000") == "US"


def test_pound_sterling_infers_gb():
    assert _infer_jurisdiction_code_from_currency("Total: £1,200,000") == "GB"


def test_explicit_cad_code_infers_ca():
    assert _infer_jurisdiction_code_from_currency("Budget currency: CAD. Total: $500,000") == "CA"


def test_euro_alone_stays_ambiguous():
    assert _infer_jurisdiction_code_from_currency("Total: €1,200,000") is None


def test_mixed_symbols_stay_ambiguous():
    assert _infer_jurisdiction_code_from_currency("Total: $1,200,000 (£900,000)") is None


def test_no_currency_marker_returns_none():
    assert _infer_jurisdiction_code_from_currency("Total: 1,200,000") is None


# ── 1: explicit project override takes precedence over derived budget ────

async def test_explicit_project_jurisdiction_overrides_derived_budget(
    db: AsyncSession, project: Project, us_jurisdiction: Jurisdiction, gb_jurisdiction: Jurisdiction,
):
    project.home_jurisdiction_id = gb_jurisdiction.id
    await db.commit()
    await _seed_budget(db, project, "Test Budget.pdf", [("1100", "SCRIPT", 50_000)], currency_marker="$")

    from app.models.budget import BudgetDocument
    from app.services.material_routing import ensure_current_budget_routed
    budget_doc = await ensure_current_budget_routed(db, project.id)

    resolved = await _resolve_home_jurisdiction(db, project, budget_doc)
    assert resolved.code == "GB"  # explicit override wins over the $ -> US inference


# ── 2: deterministic derivation when no explicit fact exists ─────────────

async def test_currency_derives_jurisdiction_when_no_override(db: AsyncSession, project: Project, us_jurisdiction: Jurisdiction):
    await _seed_budget(db, project, "Test Budget.pdf", [("1100", "SCRIPT", 50_000)], currency_marker="$")
    from app.services.material_routing import ensure_current_budget_routed
    budget_doc = await ensure_current_budget_routed(db, project.id)

    resolved = await _resolve_home_jurisdiction(db, project, budget_doc)
    assert resolved is not None
    assert resolved.code == "US"
    assert project.home_jurisdiction_id == resolved.id


# ── 3: ambiguous shared currency remains unresolved ───────────────────────

async def test_ambiguous_euro_budget_remains_unresolved(db: AsyncSession, project: Project):
    await _seed_budget(db, project, "Test Budget.pdf", [("1100", "SCRIPT", 50_000)], currency_marker="€")
    from app.services.material_routing import ensure_current_budget_routed
    budget_doc = await ensure_current_budget_routed(db, project.id)

    resolved = await _resolve_home_jurisdiction(db, project, budget_doc)
    assert resolved is None
    assert project.home_jurisdiction_id is None  # never fabricated


# ── 4: derived jurisdiction persists with source provenance ──────────────

async def test_derived_jurisdiction_persists_with_extracted_provenance(db: AsyncSession, project: Project, us_jurisdiction: Jurisdiction):
    await _seed_budget(db, project, "Test Budget.pdf", [("1100", "SCRIPT", 50_000)], currency_marker="$")
    from app.services.material_routing import ensure_current_budget_routed
    budget_doc = await ensure_current_budget_routed(db, project.id)

    await _resolve_home_jurisdiction(db, project, budget_doc)

    fact = (await db.execute(
        select(ProjectFact).where(ProjectFact.project_id == project.id, ProjectFact.fact_key == "home_jurisdiction_code")
    )).scalars().first()
    assert fact is not None
    assert fact.value == "US"
    assert str(fact.source_type) == "extracted"  # never user_override for a derived fact
    assert fact.source_document_version_id == budget_doc.document_version_id


# ── real regression found via runtime evidence: re-deriving after a
#    prior derivation fact already exists must UPDATE it, never insert a
#    second row (ProjectFact's own unique-per-key constraint) ────────────

async def test_re_derivation_updates_existing_fact_not_duplicates(db: AsyncSession, project: Project, us_jurisdiction: Jurisdiction):
    await _seed_budget(db, project, "Test Budget.pdf", [("1100", "SCRIPT", 50_000)], currency_marker="$")
    from app.services.material_routing import ensure_current_budget_routed
    budget_doc = await ensure_current_budget_routed(db, project.id)

    first = await _resolve_home_jurisdiction(db, project, budget_doc)
    assert first.code == "US"

    # Simulate the fact already existing from a prior derivation (e.g. a
    # reverted/replayed evaluation) while home_jurisdiction_id was reset —
    # the exact real scenario a re-ingested/re-derived project can hit.
    project.home_jurisdiction_id = None
    await db.commit()

    second = await _resolve_home_jurisdiction(db, project, budget_doc)  # must not raise IntegrityError
    assert second.code == "US"

    facts = (await db.execute(
        select(ProjectFact).where(ProjectFact.project_id == project.id, ProjectFact.fact_key == "home_jurisdiction_code")
    )).scalars().all()
    assert len(facts) == 1  # updated in place, never duplicated


# ── 5: the live prerequisite resolver (build_project_economic_inputs)
#      consumes the derived jurisdiction ─────────────────────────────────

async def test_prerequisite_resolver_consumes_derived_jurisdiction(db: AsyncSession, project: Project, us_jurisdiction: Jurisdiction):
    await _seed_budget(db, project, "Test Budget.pdf", [
        ("1100", "SCRIPT", 500_000), ("1400", "CAST", 800_000),
    ], currency_marker="$")

    result = await build_project_economic_inputs(db, project.id)
    assert not any("BASE_JURISDICTION_UNKNOWN" in b for b in result.blockers), result.blockers
    if result.ok:
        assert result.inputs.jurisdiction_code == "US"


# ── 6/7: Evaluate continues automatically past ingestion+derivation,
#         reaching script ingestion, in ONE call — no second click ───────

async def test_evaluate_project_continues_through_script_ingestion_after_derivation(
    db: AsyncSession, project: Project, us_jurisdiction: Jurisdiction,
):
    from app.models.screenplay import ScreenplayDocument

    await _seed_budget(db, project, "Test Budget.pdf", [
        ("1100", "SCRIPT", 500_000), ("1400", "CAST", 800_000),
    ], currency_marker="$")

    # A minimal real screenplay-category document, seeded the same
    # "predates commit-time routing" way as the budget.
    settings = get_settings()
    storage_dir = Path(settings.LOCAL_STORAGE_PATH) / f"base-jur-test-{project.id}"
    script_path = storage_dir / "Test Script.pdf"
    script_doc_pdf = fitz.open()
    script_doc_pdf.new_page().insert_text((72, 72), "INT. ROOM - DAY\n\nA test scene.\n", fontsize=12)
    script_doc_pdf.save(str(script_path))
    script_doc_pdf.close()
    sdoc = Document(id=uuid.uuid4(), project_id=project.id, category="screenplay", title="Screenplay")
    db.add(sdoc)
    await db.flush()
    sversion = DocumentVersion(
        id=uuid.uuid4(), document_id=sdoc.id, original_filename="Test Script.pdf",
        storage_path=f"base-jur-test-{project.id}/Test Script.pdf", is_current=True,
    )
    db.add(sversion)
    await db.flush()
    sdoc.current_version_id = sversion.id
    await db.commit()

    before = (await db.execute(
        select(ScreenplayDocument).where(ScreenplayDocument.project_id == project.id)
    )).scalars().first()
    assert before is None

    result = await evaluate_project(db, project.id)
    assert result.get("status") not in ("PROJECT_NOT_FOUND",)
    assert not any("BASE_JURISDICTION_UNKNOWN" in b for b in (result.get("blockers") or [])), result

    after = (await db.execute(
        select(ScreenplayDocument).where(ScreenplayDocument.project_id == project.id)
    )).scalars().first()
    assert after is not None, "a single evaluate_project call must reach script ingestion once budget+jurisdiction resolve"


# ── 9: an already-normalized mature project is not destructively changed ─

async def test_mature_project_with_confirmed_jurisdiction_is_untouched(
    db: AsyncSession, project: Project, gb_jurisdiction: Jurisdiction,
):
    project.home_jurisdiction_id = gb_jurisdiction.id
    await db.commit()
    await _seed_budget(db, project, "Test Budget.pdf", [("1100", "SCRIPT", 50_000)], currency_marker="$")
    from app.services.material_routing import ensure_current_budget_routed
    budget_doc = await ensure_current_budget_routed(db, project.id)

    resolved = await _resolve_home_jurisdiction(db, project, budget_doc)
    assert resolved.id == gb_jurisdiction.id  # untouched, never overridden by budget currency

    fact = (await db.execute(
        select(ProjectFact).where(ProjectFact.project_id == project.id, ProjectFact.fact_key == "home_jurisdiction_code")
    )).scalars().first()
    assert fact is None  # no derivation fact written when nothing was derived
