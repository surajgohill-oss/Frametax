"""
Phase F — focused tests for the two pieces of new logic this phase adds
that Phase E's suite doesn't cover:

  1. classify_file()'s structural screenplay fallback (page count + US
     Letter page size) — real corpus evidence showed most real screenplay
     PDFs have no "script"/"screenplay" keyword in their filename.
  2. artwork_extraction.py — cover-image extraction from a PDF page 1 or
     a PPTX slide 1, and the accept/reject thresholds calibrated against
     real corpus logos vs. real cover photos.
  3. commit's `auto_master` control and extraction provenance wiring —
     the backend enforcement behind "never guess a master when multiple
     legitimate candidates compete" (Section 6).

Same explicit-cleanup fixture pattern as test_ingestion_api.py (the
functions under test call db.commit() themselves, so a rollback-based
fixture can't isolate them).
"""
from __future__ import annotations

import hashlib
import uuid
import zipfile
from pathlib import Path

import fitz
import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_asset import ProjectAsset
from app.models.ingestion_candidate import IngestionCandidate
from app.api.v1.ingestion import discover, commit_candidate, DiscoverRequest, _commit_candidate_impl
from app.services.ingestion_classifier import classify_file
from app.services.artwork_extraction import (
    extract_pdf_cover, extract_pptx_cover, extract_cover_image, render_pdf_page_as_candidate,
)


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Phase F Test Org", slug=f"phase-f-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Phase F Test Project {uuid.uuid4().hex[:8]}")
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
    path = Path(tmp_path) / name
    path.write_bytes(content)
    return str(path)


def _solid_png(w: int, h: int, color=(180, 60, 60)) -> bytes:
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h))
    pix.set_rect(pix.irect, color)
    return pix.tobytes("png")


def _make_pptx(tmp_path, media: list[tuple[str, bytes]]) -> Path:
    path = Path(tmp_path) / "deck.pptx"
    with zipfile.ZipFile(path, "w") as z:
        rels = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        ]
        for i, (name, _data) in enumerate(media, start=1):
            rels.append(
                f'<Relationship Id="rId{i}" '
                f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                f'Target="../media/{name}"/>'
            )
        rels.append("</Relationships>")
        z.writestr("ppt/slides/_rels/slide1.xml.rels", "".join(rels))
        for name, data in media:
            z.writestr(f"ppt/media/{name}", data)
    return path


# ── classify_file structural fallback ──────────────────────────────────

def test_classify_file_screenplay_structural_fallback():
    r = classify_file("MY MOVIE 1-1-26.pdf", page_count=110, page_size=(612, 792))
    assert r.category == "screenplay" and r.confidence == "high"


def test_classify_file_structural_fallback_does_not_override_keyword():
    r = classify_file("My Movie Budget.pdf", page_count=110, page_size=(612, 792))
    assert r.category == "budget"


def test_classify_file_structural_fallback_requires_letter_size():
    r = classify_file("MY MOVIE.pdf", page_count=110, page_size=(1440, 810))
    assert r.category == "other" and r.confidence == "low"


def test_classify_file_structural_fallback_requires_plausible_length():
    r = classify_file("MY MOVIE.pdf", page_count=9, page_size=(612, 792))
    assert r.category == "other"


def test_classify_file_unaffected_without_metadata():
    r = classify_file("MY MOVIE.pdf")
    assert r.category == "other" and r.confidence == "low"


# ── artwork_extraction: PDF ─────────────────────────────────────────────

def test_extract_pdf_cover_accepts_full_bleed_image(tmp_path):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(fitz.Rect(0, 0, 612, 792), stream=_solid_png(1000, 1400))
    path = Path(tmp_path) / "cover.pdf"
    doc.save(path)
    doc.close()

    result = extract_pdf_cover(path)
    assert result is not None
    assert result.width and result.height and result.width * result.height > 0
    assert result.ext in {"png", "jpg", "jpeg"}


def test_extract_pdf_cover_rejects_small_corner_logo(tmp_path):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(fitz.Rect(20, 20, 100, 100), stream=_solid_png(80, 80))
    path = Path(tmp_path) / "logo_only.pdf"
    doc.save(path)
    doc.close()

    assert extract_pdf_cover(path) is None


def test_extract_pdf_cover_rejects_text_only_page(tmp_path):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "FADE IN:")
    path = Path(tmp_path) / "text_only.pdf"
    doc.save(path)
    doc.close()

    assert extract_pdf_cover(path) is None


# ── artwork_extraction: PPTX ─────────────────────────────────────────────

def test_extract_pptx_cover_picks_largest_slide1_image(tmp_path):
    path = _make_pptx(tmp_path, [("logo.png", _solid_png(150, 150)), ("hero.png", _solid_png(1600, 900))])
    result = extract_pptx_cover(path)
    assert result is not None
    assert (result.width, result.height) == (1600, 900)


def test_extract_pptx_cover_rejects_when_only_small_images(tmp_path):
    path = _make_pptx(tmp_path, [("logo1.png", _solid_png(150, 150)), ("logo2.png", _solid_png(200, 196))])
    assert extract_pptx_cover(path) is None


def test_extract_pptx_cover_no_slide1_rels_returns_none(tmp_path):
    path = Path(tmp_path) / "empty.pptx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/presentation.xml", "<x/>")
    assert extract_pptx_cover(path) is None


def test_extract_cover_image_dispatches_by_extension_only(tmp_path):
    other = Path(tmp_path) / "budget.xlsx"
    other.write_bytes(b"not an image container")
    assert extract_cover_image(other) is None


# ── artwork_extraction: Tier 3 whole-page-render fallback ──────────────

def test_render_pdf_page_accepts_composed_color_cover(tmp_path):
    doc = fitz.open()
    page = doc.new_page(width=1920, height=1080)
    page.draw_rect(page.rect, color=(0.7, 0.15, 0.15), fill=(0.7, 0.15, 0.15))
    path = Path(tmp_path) / "cover.pdf"
    doc.save(path)
    doc.close()

    result = render_pdf_page_as_candidate(path)
    assert result is not None
    assert result.ext == "png"
    assert result.width and result.height


def test_render_pdf_page_rejects_plain_text_title_page(tmp_path):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 360), "FADE IN:")
    page.insert_text((72, 380), "EXT. SOMEWHERE - DAY")
    path = Path(tmp_path) / "title_page.pdf"
    doc.save(path)
    doc.close()

    assert render_pdf_page_as_candidate(path) is None


def test_render_pdf_page_rejects_sparse_table_page(tmp_path):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    for row in range(20):
        y = 60 + row * 30
        page.draw_line((50, y), (560, y), color=(0, 0, 0))
        page.insert_text((60, y - 5), f"Line item {row}    $1,234.00")
    path = Path(tmp_path) / "topsheet.pdf"
    doc.save(path)
    doc.close()

    assert render_pdf_page_as_candidate(path) is None


def test_render_pdf_page_out_of_range_index_returns_none(tmp_path):
    doc = fitz.open()
    doc.new_page(width=612, height=792)
    path = Path(tmp_path) / "single_page.pdf"
    doc.save(path)
    doc.close()

    assert render_pdf_page_as_candidate(path, page_index=5) is None


# ── commit_candidate: auto_master + extraction provenance ──────────────

async def test_auto_master_false_never_promotes_a_competing_candidate(db: AsyncSession, project: Project, tmp_path):
    dir1 = Path(tmp_path) / "a"
    dir1.mkdir()
    _write(dir1, "art1.png", _solid_png(800, 600))
    r1 = await discover(DiscoverRequest(source_type="local", source_pointer=str(dir1), project_id=str(project.id)), db)
    result1 = await commit_candidate(r1["candidates"][0]["id"], db)
    asset1_id = uuid.UUID(result1["project_asset_id"])
    asset1 = (await db.execute(select(ProjectAsset).where(ProjectAsset.id == asset1_id))).scalar_one()
    assert asset1.is_master is True  # sole candidate — clear winner

    dir2 = Path(tmp_path) / "b"
    dir2.mkdir()
    path2 = _write(dir2, "art2.png", _solid_png(900, 700))
    cand2 = IngestionCandidate(
        id=uuid.uuid4(), source_type="local", source_pointer=path2, source_display_path=str(dir2),
        filename="art2.png", file_extension=".png", file_size=Path(path2).stat().st_size,
        checksum_sha256=hashlib.sha256(Path(path2).read_bytes()).hexdigest(),
        proposed_category="artwork", category_confidence="high",
        proposed_project_id=project.id, association_confidence="high",
        association_evidence="test: second competing candidate",
        version_status="new_document", status="pending", discovered_at="2026-01-01T00:00:00+00:00",
    )
    db.add(cand2)
    await db.commit()
    await db.refresh(cand2)

    # Simulates the batch-ingestion policy: two candidates, no clear
    # winner -> neither is allowed to auto-become master.
    result2 = await _commit_candidate_impl(str(cand2.id), db, auto_master=False)
    asset2 = (await db.execute(select(ProjectAsset).where(ProjectAsset.id == uuid.UUID(result2["project_asset_id"])))).scalar_one()
    assert asset2.is_master is False

    await db.refresh(asset1)
    assert asset1.is_master is True  # first commit's master is untouched by the second


async def test_extraction_provenance_sets_source_type_and_original_version_link(
    db: AsyncSession, project: Project, tmp_path
):
    deck_dir = Path(tmp_path) / "deck"
    deck_dir.mkdir()
    _write(deck_dir, "Some Deck.pptx", b"fake deck bytes")
    r = await discover(DiscoverRequest(source_type="local", source_pointer=str(deck_dir), project_id=str(project.id)), db)
    deck_result = await commit_candidate(r["candidates"][0]["id"], db)
    deck_version_id = uuid.UUID(deck_result["document_version_id"])

    art_dir = Path(tmp_path) / "art"
    art_dir.mkdir()
    art_path = _write(art_dir, "Some Deck (cover).png", _solid_png(800, 600))
    cand = IngestionCandidate(
        id=uuid.uuid4(), source_type="local", source_pointer=art_path, source_display_path=str(art_dir),
        filename="Some Deck (cover).png", file_extension=".png", file_size=Path(art_path).stat().st_size,
        checksum_sha256=hashlib.sha256(Path(art_path).read_bytes()).hexdigest(),
        proposed_category="artwork", category_confidence="high",
        proposed_project_id=project.id, association_confidence="high",
        association_evidence="extracted from this project's own deck",
        version_status="new_document", status="pending", discovered_at="2026-01-01T00:00:00+00:00",
        extracted_from_document_version_id=deck_version_id, artwork_extraction_kind="deck",
        notes="Extracted from deck cover page (Some Deck.pptx, 800x600).",
    )
    db.add(cand)
    await db.commit()
    await db.refresh(cand)

    result = await _commit_candidate_impl(str(cand.id), db)
    asset = (await db.execute(select(ProjectAsset).where(ProjectAsset.id == uuid.UUID(result["project_asset_id"])))).scalar_one()
    assert asset.source_type == "extracted_from_deck"
    assert asset.source_document_version_id == deck_version_id
    assert asset.notes == "Extracted from deck cover page (Some Deck.pptx, 800x600)."
