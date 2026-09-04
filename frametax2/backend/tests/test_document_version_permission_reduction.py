"""
Consolidated UI/ingestion/permission closeout (2026-09-03), Batch 5 —
document-version permission reduction.

ROOT CAUSE (confirmed, not guessed): GET /projects/{id}/record's
`current_unresolved` flag (surfaced to producers as "N versions ·
CURRENT UNRESOLVED", a real decision-required signal) fired whenever a
Document had >1 version and no supersedes_version_id chained them --
regardless of category, and regardless of whether the system already
had a confident current pick via DocumentVersion.is_current (a real,
reliably-maintained field -- see its own model docstring). Asking a
producer to re-resolve something CineGlobe already knows is pure
friction, not a genuine decision.

Fixed generically:
  1. AUTOMATIC — any version genuinely marked is_current=True means the
     system has a confident pick; never unresolved, for ANY category,
     regardless of how many other (superseded/historical) versions
     exist.
  2. Only when NO version carries is_current=True does version count
     matter at all -- and even then, restricted to material categories
     (budget, schedule) where a wrong pick could change downstream
     economics. Artwork/deck/screenplay auto-resolve instead of
     blocking on a producer decision that rarely matters for them.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.project import Project
from app.models.library_document import Document, DocumentVersion
from app.api.v1.projects import get_project_record


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Doc Version Test Org", slug=f"doc-version-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Doc Version Test Project {uuid.uuid4().hex[:8]}")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    project_id = p.id
    try:
        yield p
    finally:
        await db.execute(sa_delete(Project).where(Project.id == project_id))
        await db.commit()


def _doc(project_id, category):
    return Document(id=uuid.uuid4(), project_id=project_id, category=category, title=category)


def _version(document_id, *, is_current, filename="v.pdf"):
    return DocumentVersion(
        id=uuid.uuid4(), document_id=document_id, original_filename=filename,
        is_current=is_current,
    )


async def _record_for(db, project, category):
    doc = _doc(project.id, category)
    db.add(doc)
    await db.flush()
    return doc


async def test_multiple_versions_with_a_confident_is_current_pick_are_never_unresolved(db: AsyncSession, project: Project):
    """AUTOMATIC: the system already knows which version is current
    (is_current=True on one of them) -- must never ask the producer to
    re-confirm it, for ANY category, no matter how many other historical
    versions exist."""
    for category in ("artwork", "deck", "screenplay", "budget", "schedule"):
        doc = await _record_for(db, project, category)
        db.add(_version(doc.id, is_current=False, filename="old1.pdf"))
        db.add(_version(doc.id, is_current=False, filename="old2.pdf"))
        db.add(_version(doc.id, is_current=True, filename="current.pdf"))
        await db.commit()

    record = await get_project_record(str(project.id), db=db)
    for d in record["documents"]:
        assert d["current_unresolved"] is False, f"{d['category']}: must not be unresolved when is_current is confidently set"
        assert d["current_version"]["filename"] == "current.pdf"


async def test_artwork_and_deck_auto_resolve_even_with_no_confident_is_current(db: AsyncSession, project: Project):
    """AUTOMATIC / no producer decision: artwork and deck version
    ambiguity should almost never block — even with no is_current flag
    set anywhere, these non-material categories must not be flagged
    current_unresolved."""
    for category in ("artwork", "deck"):
        doc = await _record_for(db, project, category)
        db.add(_version(doc.id, is_current=False, filename="a.pdf"))
        db.add(_version(doc.id, is_current=False, filename="b.pdf"))
        await db.commit()

    record = await get_project_record(str(project.id), db=db)
    for d in record["documents"]:
        if d["category"] in ("artwork", "deck"):
            assert d["current_unresolved"] is False, f"{d['category']} must auto-resolve, never block on a producer decision"


async def test_budget_and_schedule_still_ask_when_genuinely_ambiguous(db: AsyncSession, project: Project):
    """DECISION REQUIRED: budget/schedule are the task's own stricter
    categories — when the system has NO confident current pick (no
    is_current set, no supersedes chain) and real economics could be
    affected, the producer must still be asked."""
    for category in ("budget", "schedule"):
        doc = await _record_for(db, project, category)
        db.add(_version(doc.id, is_current=False, filename="budget_v1.pdf"))
        db.add(_version(doc.id, is_current=False, filename="budget_v2.pdf"))
        await db.commit()

    record = await get_project_record(str(project.id), db=db)
    for d in record["documents"]:
        if d["category"] in ("budget", "schedule"):
            assert d["current_unresolved"] is True, f"{d['category']}: genuine unresolved authority must still ask the producer"


async def test_a_single_version_is_never_unresolved(db: AsyncSession, project: Project):
    """A document with only one version has nothing to resolve."""
    doc = await _record_for(db, project, "budget")
    db.add(_version(doc.id, is_current=False, filename="only.pdf"))
    await db.commit()

    record = await get_project_record(str(project.id), db=db)
    d = next(d for d in record["documents"] if d["category"] == "budget")
    assert d["current_unresolved"] is False
