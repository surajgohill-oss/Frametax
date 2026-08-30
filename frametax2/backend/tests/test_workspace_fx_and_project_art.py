"""
Workspace Data Completeness — FX pipeline + Project Key Art closeout.

Two real, independently-confirmed served-data gaps, both traced to the
same defect shape: real, sourced data already existed but was never wired
to the generic (non-demo) project path.

  1. FX: production_normalization.py's fx_rate_snapshot()/FX_RATE_SNAPSHOTS
     (real ECB/open.er-api.com sourced rates, already correctly wired into
     the legacy cineglobe.py _economics_payload()) was never reused by
     canonical_production_view.build_generic_pkg_and_economics() — the
     function that actually serves every project's real /state route.
     Fixed by reusing the SAME fx_rate_snapshot()/_JURISDICTION_CURRENCY
     the legacy route already used, never a second FX provider.

  2. Art: app.services.artwork_extraction.extract_pdf_cover() (Phase F,
     built, never wired to any trigger) is now called from a screenplay's
     commit-time routing AND a retroactive Evaluate-time trigger, the same
     established pattern as ensure_current_budget_routed. Never generates
     or researches art — only extracts a real embedded cover image already
     present in the project's own screenplay PDF, and only when no master
     artwork already exists for the project.
"""
from __future__ import annotations

import uuid
from pathlib import Path

# Pre-existing module-graph ordering quirk (see prior CAPABILITY_LEDGER
# entries): importing app.data.program_rate_rules first forces the
# correct registration order so canonical_production_view's own import of
# executable_jurisdiction_registry doesn't hit a circular-import error.
import app.data.program_rate_rules  # noqa: F401

import fitz
import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import engine
from app.models.enums import DocumentCategory
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_asset import ProjectAsset
from app.calculators.production_normalization import (
    fx_rate_snapshot, FX_RATE_SNAPSHOTS, FX_LIVE_SNAPSHOT_DATE, _JURISDICTION_CURRENCY,
)
from app.services.canonical_production_view import build_generic_pkg_and_economics
from app.services.material_routing import ensure_screenplay_artwork_extracted
from app.services.artwork_extraction import extract_pdf_cover


# ── FX: canonical source + wiring ───────────────────────────────────────────

def test_a_canonical_fx_source_is_the_real_sourced_snapshot_table():
    # No live per-request fetch, no hardcoded number outside the sourced
    # table — every horizon comes from FX_RATE_SNAPSHOTS, keyed by a real
    # retrieval date.
    eur = fx_rate_snapshot("EUR")
    assert eur["current"] == FX_RATE_SNAPSHOTS[FX_LIVE_SNAPSHOT_DATE]["EUR"]
    assert eur["current"] is not None and eur["1m"] is not None


def test_d_unmapped_currency_is_non_fatal_and_honestly_unavailable():
    # No hardcoded rate fallback — an unmapped currency returns every
    # horizon as None, never a guessed number, and never raises.
    result = fx_rate_snapshot("XXX")
    assert result == {"current": None, "1m": None, "6m": None, "12m": None}


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="FX/Art Test Org", slug=f"fx-art-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"FX Art Test Project {uuid.uuid4().hex[:8]}")
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


async def test_b_and_c_workspace_payload_receives_real_rates(db: AsyncSession, project: Project):
    sections = await build_generic_pkg_and_economics(db, project.id)
    econ = sections["economics"]
    for code in ("EUR", "CAD", "GBP"):
        h = econ["fx_horizons"][code]
        assert h["current"] == FX_RATE_SNAPSHOTS[FX_LIVE_SNAPSHOT_DATE][code]
    assert econ["jurisdiction_currency"] == dict(_JURISDICTION_CURRENCY)
    assert econ["fx_horizon_dates"]["current"] == FX_LIVE_SNAPSHOT_DATE
    assert econ["fx_source"]


async def test_e_no_project_specific_fx_branch(db: AsyncSession, project: Project):
    # The same canonical snapshot serves any project — never a per-project
    # override or a second hardcoded table.
    sections = await build_generic_pkg_and_economics(db, project.id)
    econ = sections["economics"]
    assert econ["fx_horizons"]["EUR"]["current"] == fx_rate_snapshot("EUR")["current"]


# ── Art: extraction, precedence, provenance, isolation ──────────────────────

def _make_pdf_with_full_page_cover(path: Path) -> None:
    """A real embedded raster image covering the whole page — the same
    shape a designed screenplay title page / poster cover has."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    cover = fitz.open()
    cpage = cover.new_page(width=612, height=792)
    cpage.draw_rect(cpage.rect, color=(0.8, 0.1, 0.1), fill=(0.8, 0.1, 0.1))
    pix = cpage.get_pixmap()
    img_bytes = pix.tobytes("png")
    cover.close()
    page.insert_image(page.rect, stream=img_bytes)
    doc.save(str(path))
    doc.close()


def _make_plain_text_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 100), "A SCREENPLAY\n\nby Nobody", fontsize=18)
    doc.save(str(path))
    doc.close()


def test_h_plain_text_pdf_never_becomes_key_art(tmp_path):
    p = tmp_path / "plain.pdf"
    _make_plain_text_pdf(p)
    assert extract_pdf_cover(p) is None


def test_extract_pdf_cover_finds_a_real_full_page_image(tmp_path):
    p = tmp_path / "cover.pdf"
    _make_pdf_with_full_page_cover(p)
    image = extract_pdf_cover(p)
    assert image is not None
    assert image.width and image.height


async def _seed_screenplay_document(db: AsyncSession, project: Project, pdf_path: Path) -> DocumentVersion:
    project_dir = Path(settings.LOCAL_STORAGE_PATH) / f"test-{project.id}"
    project_dir.mkdir(parents=True, exist_ok=True)
    dest = project_dir / pdf_path.name
    dest.write_bytes(pdf_path.read_bytes())

    doc = Document(id=uuid.uuid4(), project_id=project.id, category=DocumentCategory.SCREENPLAY.value, title="Test Screenplay")
    db.add(doc)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=doc.id, original_filename=pdf_path.name,
        storage_path=str(dest.relative_to(settings.LOCAL_STORAGE_PATH)),
        is_current=True,
    )
    db.add(version)
    await db.flush()
    doc.current_version_id = version.id
    await db.commit()
    return version


async def test_j_extracted_artwork_outranks_neutral_fallback(db: AsyncSession, project: Project, tmp_path):
    src = tmp_path / "cover.pdf"
    _make_pdf_with_full_page_cover(src)
    version = await _seed_screenplay_document(db, project, src)

    result = await ensure_screenplay_artwork_extracted(db, project.id)
    assert result == "extracted"

    asset = (await db.execute(
        select(ProjectAsset).where(ProjectAsset.project_id == project.id)
    )).scalars().first()
    assert asset is not None
    assert asset.is_master is True  # no prior master -> extracted art becomes master
    # G: provenance retained
    assert asset.source_document_version_id == version.id
    assert asset.project_id == project.id


async def test_idempotent_second_call_does_not_duplicate(db: AsyncSession, project: Project, tmp_path):
    src = tmp_path / "cover.pdf"
    _make_pdf_with_full_page_cover(src)
    await _seed_screenplay_document(db, project, src)

    await ensure_screenplay_artwork_extracted(db, project.id)
    second = await ensure_screenplay_artwork_extracted(db, project.id)
    assert second == "already_extracted"

    count = len((await db.execute(
        select(ProjectAsset).where(ProjectAsset.project_id == project.id)
    )).scalars().all())
    assert count == 1


async def test_h2_plain_text_screenplay_produces_no_project_asset(db: AsyncSession, project: Project, tmp_path):
    src = tmp_path / "plain.pdf"
    _make_plain_text_pdf(src)
    await _seed_screenplay_document(db, project, src)

    result = await ensure_screenplay_artwork_extracted(db, project.id)
    assert result == "no_usable_artwork"
    assets = (await db.execute(
        select(ProjectAsset).where(ProjectAsset.project_id == project.id)
    )).scalars().all()
    assert assets == []


async def test_i_explicit_master_outranks_extracted_artwork(db: AsyncSession, project: Project, tmp_path):
    # Simulate an explicit user-assigned master (e.g. via set-master) that
    # already exists BEFORE extraction ever runs.
    explicit = ProjectAsset(
        id=uuid.uuid4(), project_id=project.id, kind="artwork", source_type="uploaded",
        storage_path=None, is_master=True,
    )
    db.add(explicit)
    await db.commit()

    src = tmp_path / "cover.pdf"
    _make_pdf_with_full_page_cover(src)
    await _seed_screenplay_document(db, project, src)

    result = await ensure_screenplay_artwork_extracted(db, project.id)
    assert result == "extracted"

    rows = (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == project.id))).scalars().all()
    assert len(rows) == 2
    masters = [r for r in rows if r.is_master]
    assert len(masters) == 1
    assert masters[0].id == explicit.id  # explicit selection never displaced


async def test_f_project_a_cannot_receive_project_b_artwork(db: AsyncSession, tmp_path):
    org = Organization(name="Isolation Test Org", slug=f"iso-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    project_a = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Project A {uuid.uuid4().hex[:6]}")
    project_b = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Project B {uuid.uuid4().hex[:6]}")
    db.add_all([project_a, project_b])
    await db.commit()
    await db.refresh(project_a)
    await db.refresh(project_b)

    try:
        src = tmp_path / "cover.pdf"
        _make_pdf_with_full_page_cover(src)
        await _seed_screenplay_document(db, project_a, src)
        # project_b has no screenplay at all.

        await ensure_screenplay_artwork_extracted(db, project_a.id)
        b_result = await ensure_screenplay_artwork_extracted(db, project_b.id)
        assert b_result is None

        a_assets = (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == project_a.id))).scalars().all()
        b_assets = (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == project_b.id))).scalars().all()
        assert len(a_assets) == 1
        assert b_assets == []
    finally:
        await db.execute(sa_delete(Project).where(Project.id.in_([project_a.id, project_b.id])))
        await db.commit()
