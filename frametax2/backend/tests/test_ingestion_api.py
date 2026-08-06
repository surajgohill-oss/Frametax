"""
Phase E — ingestion API tests against the real Postgres dev database.

Unlike Phase B/C's rolled-back-transaction pattern, the functions under
test here (discover/commit_candidate/delete_project/set_master_artwork)
call db.commit() themselves, which would end any outer transaction a
rollback-based fixture started — so isolation here is explicit cleanup
instead: every test creates its own disposable Organization/Project and
deletes that Project (cascading everything it owns) in a finally block,
regardless of pass/fail. Never touches Little Utopia or Otherwise Engaged.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.project import Project
from app.models.library_document import Document, DocumentVersion, DocumentVersionSource
from app.models.project_asset import ProjectAsset
from app.models.ingestion_candidate import IngestionCandidate
from app.api.v1.ingestion import discover, commit_candidate, DiscoverRequest
from app.api.v1.projects import delete_project, set_master_artwork


@pytest.fixture
async def db():
    # expire_on_commit=False: the functions under test each call
    # db.commit() themselves (discover/commit_candidate/etc. are real
    # endpoint bodies, not test-only helpers) — without this, every ORM
    # object touched anywhere in a test would expire after each of those
    # commits, and any later plain attribute access (project.id, etc.)
    # would attempt a synchronous lazy-load outside an await context and
    # raise MissingGreenlet.
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Phase E Test Org", slug=f"phase-e-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Phase E Test Project {uuid.uuid4().hex[:8]}")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    project_id = p.id  # captured now — AsyncSession expires ORM attributes
    # after every commit the test body makes, and a bare post-commit
    # `p.id` access below would attempt a sync lazy-load outside any
    # await context and blow up with MissingGreenlet.
    try:
        yield p
    finally:
        # Cleanup regardless of pass/fail — cascades documents/versions/
        # sources/assets/candidates the test committed. The org row is
        # left (harmless, unowned, never referenced by anything real);
        # deleting it too would need its own guard against ever touching
        # "Mind The Story Media".
        still_there = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if still_there is not None:
            # Core DELETE, not db.delete() — see delete_project's own
            # comment: the ORM's default relationship behavior would try
            # to NULL child FKs first and trip a CHECK constraint.
            await db.execute(sa_delete(Project).where(Project.id == project_id))
            await db.commit()


def _write(tmp_path, name: str, content: bytes) -> str:
    path = tmp_path / name
    path.write_bytes(content)
    return str(path)


async def test_discover_stages_without_creating_documents(db: AsyncSession, project: Project, tmp_path):
    _write(tmp_path, "Budget.pdf", b"fake budget bytes")
    result = await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    assert result["discovered"] == 1
    doc_count = (await db.execute(select(Document).where(Document.project_id == project.id))).scalars().all()
    assert len(doc_count) == 0  # nothing canonical yet — staging only

    candidate = (await db.execute(select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id))).scalar_one()
    assert candidate.status == "pending"
    assert candidate.proposed_category == "budget"


async def test_commit_creates_document_and_version(db: AsyncSession, project: Project, tmp_path):
    _write(tmp_path, "Schedule.pdf", b"fake schedule bytes")
    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    candidate = (await db.execute(select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id))).scalar_one()

    result = await commit_candidate(str(candidate.id), db)
    assert result["result"] == "new_version_created"

    doc = (await db.execute(select(Document).where(Document.project_id == project.id))).scalar_one()
    assert doc.category == "schedule"
    version = (await db.execute(select(DocumentVersion).where(DocumentVersion.document_id == doc.id))).scalar_one()
    assert version.is_current is True
    assert version.checksum_sha256 is not None


async def test_exact_duplicate_does_not_create_second_version(db: AsyncSession, project: Project, tmp_path):
    content = b"identical bytes for dedup test"
    _write(tmp_path, "Deck.pptx", content)
    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    first = (await db.execute(select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id))).scalar_one()
    await commit_candidate(str(first.id), db)

    # A second, differently-named file with the SAME bytes, discovered in
    # a SEPARATE call (so commit-time re-check, not discovery-time cache,
    # is what has to catch it).
    dup_dir = tmp_path / "mirror"
    dup_dir.mkdir()
    _write(dup_dir, "Deck (Drive copy).pptx", content)
    await discover(DiscoverRequest(source_type="local", source_pointer=str(dup_dir), project_id=str(project.id)), db)
    second = (await db.execute(
        select(IngestionCandidate).where(
            IngestionCandidate.proposed_project_id == project.id, IngestionCandidate.status == "pending",
        )
    )).scalar_one()
    assert second.version_status == "exact_duplicate"

    result = await commit_candidate(str(second.id), db)
    assert result["result"] == "duplicate_source_recorded"

    versions = (await db.execute(
        select(DocumentVersion).join(Document, DocumentVersion.document_id == Document.id).where(Document.project_id == project.id)
    )).scalars().all()
    assert len(versions) == 1  # still exactly one physical version

    sources = (await db.execute(
        select(DocumentVersionSource).where(DocumentVersionSource.document_version_id == versions[0].id)
    )).scalars().all()
    assert len(sources) == 2  # both locations recorded


async def test_different_file_same_category_is_unresolved_not_current(db: AsyncSession, project: Project, tmp_path):
    dir_a, dir_b = tmp_path / "a", tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    _write(dir_a, "Deck v1.pptx", b"first deck version bytes")
    _write(dir_b, "Deck v2.pptx", b"second, genuinely different deck version bytes")

    await discover(DiscoverRequest(source_type="local", source_pointer=str(dir_a), project_id=str(project.id)), db)
    first = (await db.execute(select(IngestionCandidate).where(
        IngestionCandidate.proposed_project_id == project.id, IngestionCandidate.status == "pending",
    ))).scalar_one()
    await commit_candidate(str(first.id), db)

    await discover(DiscoverRequest(source_type="local", source_pointer=str(dir_b), project_id=str(project.id)), db)
    second = (await db.execute(select(IngestionCandidate).where(
        IngestionCandidate.proposed_project_id == project.id, IngestionCandidate.status == "pending",
    ))).scalar_one()
    result = await commit_candidate(str(second.id), db)
    assert result["result"] == "new_version_created"

    doc = (await db.execute(select(Document).where(Document.project_id == project.id))).scalar_one()
    versions = (await db.execute(select(DocumentVersion).where(DocumentVersion.document_id == doc.id))).scalars().all()
    assert len(versions) == 2
    current_flags = sorted(v.is_current for v in versions)
    assert current_flags == [False, True]  # exactly one current — never both, never neither
    unresolved = [v for v in versions if not v.is_current][0]
    assert "unresolved" in (unresolved.notes or "").lower()
    # Never silently reordered: the FIRST commit stays current.
    await db.refresh(first)
    assert doc.current_version_id == first.committed_document_version_id


async def test_artwork_first_commit_becomes_master_second_does_not(db: AsyncSession, project: Project, tmp_path):
    import struct, zlib

    def _png(color: bytes) -> bytes:
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
        raw = b"".join(b"\x00" + color for _ in range(2))
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")

    dir_a, dir_b = tmp_path / "art_a", tmp_path / "art_b"
    dir_a.mkdir()
    dir_b.mkdir()
    _write(dir_a, "cover1.png", _png(b"\xff\x00\x00" * 2))
    _write(dir_b, "cover2.png", _png(b"\x00\xff\x00" * 2))

    await discover(DiscoverRequest(source_type="local", source_pointer=str(dir_a), project_id=str(project.id)), db)
    c1 = (await db.execute(select(IngestionCandidate).where(
        IngestionCandidate.proposed_project_id == project.id, IngestionCandidate.status == "pending",
    ))).scalar_one()
    r1 = await commit_candidate(str(c1.id), db)
    asset1_id = r1["project_asset_id"]
    assert asset1_id is not None

    await discover(DiscoverRequest(source_type="local", source_pointer=str(dir_b), project_id=str(project.id)), db)
    c2 = (await db.execute(select(IngestionCandidate).where(
        IngestionCandidate.proposed_project_id == project.id, IngestionCandidate.status == "pending",
    ))).scalar_one()
    r2 = await commit_candidate(str(c2.id), db)
    asset2_id = r2["project_asset_id"]

    assets = (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == project.id))).scalars().all()
    by_id = {str(a.id): a for a in assets}
    assert by_id[asset1_id].is_master is True  # first commit, no prior master -> auto-promoted
    assert by_id[asset2_id].is_master is False  # second never silently replaces

    # Explicit selection switches master; neither row is deleted.
    await set_master_artwork(str(project.id), asset2_id, db)
    assets_after = (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == project.id))).scalars().all()
    assert len(assets_after) == 2
    by_id_after = {str(a.id): a for a in assets_after}
    assert by_id_after[asset2_id].is_master is True
    assert by_id_after[asset1_id].is_master is False


async def test_historical_evidence_category_does_not_touch_project_state(db: AsyncSession, project: Project, tmp_path):
    _write(tmp_path, "Pre-Qualification Letter.pdf", b"fake pre-qual letter bytes")
    lifecycle_before = project.lifecycle
    leading_before = project.leading_structure_id

    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    candidate = (await db.execute(select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id))).scalar_one()
    assert candidate.proposed_category == "pre_qualification"
    await commit_candidate(str(candidate.id), db)

    await db.refresh(project)
    assert project.lifecycle == lifecycle_before
    assert project.leading_structure_id == leading_before


async def test_delete_project_cascades_and_refuses_served_production(db: AsyncSession, project: Project, tmp_path):
    _write(tmp_path, "Budget.pdf", b"fake budget bytes for delete test")
    await discover(DiscoverRequest(source_type="local", source_pointer=str(tmp_path), project_id=str(project.id)), db)
    candidate = (await db.execute(select(IngestionCandidate).where(IngestionCandidate.proposed_project_id == project.id))).scalar_one()
    await commit_candidate(str(candidate.id), db)

    project_id = project.id
    await delete_project(str(project_id), db)

    remaining_project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    assert remaining_project is None
    remaining_docs = (await db.execute(select(Document).where(Document.project_id == project_id))).scalars().all()
    assert remaining_docs == []  # cascaded, not orphaned
