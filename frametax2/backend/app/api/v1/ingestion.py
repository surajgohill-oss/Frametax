"""
Phase E — ingestion foundation: DISCOVER -> CLASSIFY -> ASSOCIATE ->
STAGE -> REVIEW -> COMMIT.

DISCOVER is read-only against the source filesystem and only ever writes
IngestionCandidate staging rows — never a canonical Document. Only COMMIT
(a per-row, user-triggered action on an already-reviewed candidate)
creates real Document/DocumentVersion/DocumentVersionSource rows (and, for
artwork, a ProjectAsset). Nothing here touches optimizer state, facts,
lifecycle, or leading-structure selection.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.models.project import Project
from app.models.project_alias import ProjectAlias
from app.models.library_document import Document, DocumentVersion, DocumentVersionSource
from app.models.project_asset import ProjectAsset
from app.models.ingestion_candidate import IngestionCandidate
from app.models.enums import (
    DocumentSourceType, DocumentSourceStatus, ProjectAssetKind, ProjectAssetSourceType,
    IngestionCandidateStatus, VersionStatus,
)
from app.services.ingestion_classifier import classify_file, associate_file

try:
    import fitz  # PyMuPDF — optional, only used for PDF structural metadata
except ImportError:  # pragma: no cover
    fitz = None

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

# Skipped outright during a folder walk — never staged as candidates.
_SKIP_DIR_NAMES = {".git", "__pycache__", "node_modules", ".DS_Store", ".vite", "dist", "build"}
_SKIP_EXTENSIONS = {".gdoc", ".gsheet", ".gslide", ".gslides", ".gform", ".gdraw"}
# Google Drive shortcut files — zero real bytes, not a document to ingest.
_MAX_WALK_DEPTH = 4
_MAX_FILES_PER_DISCOVER = 200  # a sane bound for a user-triggered, single-folder scan


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk_bounded(root: Path):
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).parts) - root_depth
        if depth >= _MAX_WALK_DEPTH:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR_NAMES and not d.startswith(".")]
        for name in filenames:
            if name.startswith(".") or Path(name).suffix.lower() in _SKIP_EXTENSIONS:
                continue
            yield Path(dirpath) / name


# ── DISCOVER ─────────────────────────────────────────────────────────────

class DiscoverRequest(BaseModel):
    source_type: str = "local"  # "local" is the only source implemented this phase
    source_pointer: str  # absolute local folder path
    project_id: str | None = None  # optional pre-scope hint; never silently applied — still just a proposal


@router.post("/discover")
async def discover(body: DiscoverRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    if body.source_type != "local":
        raise HTTPException(
            status_code=400,
            detail=(
                "Only local filesystem discovery is implemented in this phase. "
                "Google Drive discovery requires a backend Drive connector this "
                "app does not yet have — deferred, not faked."
            ),
        )
    root = Path(body.source_pointer).expanduser()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=400, detail=f"'{body.source_pointer}' is not a readable directory")

    projects = (await db.execute(select(Project.id, Project.title))).all()
    aliases = (await db.execute(select(ProjectAlias.project_id, ProjectAlias.alias))).all()
    # Dedup is scoped PER PROJECT, not global: two unrelated projects that
    # happen to share a byte-identical file (a boilerplate NDA template,
    # say) are not the same logical Document just because their checksums
    # match — only multiple discovered LOCATIONS of the same project's
    # same file should ever merge into one DocumentVersion.
    existing_checksums: dict[tuple, uuid.UUID] = {}
    # project_id -> {category: [DocumentVersion.id, ...]} — used only to
    # decide POSSIBLE_NEW_VERSION vs NEW_DOCUMENT, never to guess ordering.
    existing_by_project_category = {}
    doc_rows = (await db.execute(
        select(Document.project_id, Document.category, DocumentVersion.id, DocumentVersion.checksum_sha256)
        .join(DocumentVersion, DocumentVersion.document_id == Document.id)
    )).all()
    for project_id, category, version_id, checksum in doc_rows:
        existing_by_project_category.setdefault((project_id, category), []).append(version_id)
        if checksum:
            existing_checksums[(project_id, checksum)] = version_id

    already_staged = {
        row[0] for row in (await db.execute(select(IngestionCandidate.source_pointer))).all()
    }

    created: list[IngestionCandidate] = []
    scanned = 0
    for path in _walk_bounded(root):
        if scanned >= _MAX_FILES_PER_DISCOVER:
            break
        pointer = str(path)
        if pointer in already_staged:
            continue  # already discovered in a prior run — discovery never re-stages
        scanned += 1

        page_count, page_size = None, None
        if fitz is not None and path.suffix.lower() == ".pdf":
            try:
                with fitz.open(path) as pdf_doc:
                    page_count = pdf_doc.page_count
                    if page_count:
                        r = pdf_doc[0].rect
                        page_size = (r.width, r.height)
            except Exception:
                pass  # structural metadata is a bonus signal, never required
        classification = classify_file(path.name, page_count=page_count, page_size=page_size)
        association = associate_file(path.name, str(path.parent), list(projects), list(aliases))
        if body.project_id and association.confidence == "none":
            # An explicit scope hint from the caller (e.g. "Add Material"
            # on a specific Project Record) only fills in when NOTHING in
            # the evidence chain found anything — it never overrides real
            # filename/path evidence for a DIFFERENT project.
            association = type(association)(uuid.UUID(body.project_id), "medium", "scoped by caller (Add Material on this project)")

        try:
            checksum = _sha256_of(path)
            size = path.stat().st_size
        except OSError:
            checksum, size = None, None

        duplicate_of = (
            existing_checksums.get((association.project_id, checksum))
            if checksum and association.project_id else None
        )
        if duplicate_of:
            version_status = VersionStatus.EXACT_DUPLICATE.value
        elif association.project_id and existing_by_project_category.get((association.project_id, classification.category)):
            version_status = VersionStatus.POSSIBLE_NEW_VERSION.value
        else:
            version_status = VersionStatus.NEW_DOCUMENT.value

        candidate = IngestionCandidate(
            id=uuid.uuid4(),
            source_type=DocumentSourceType.LOCAL.value,
            source_pointer=pointer,
            source_display_path=str(path.parent),
            filename=path.name,
            file_extension=path.suffix.lower() or None,
            file_size=size,
            checksum_sha256=checksum,
            proposed_category=classification.category,
            category_confidence=classification.confidence,
            proposed_project_id=association.project_id,
            association_confidence=association.confidence,
            association_evidence=association.evidence,
            version_status=version_status,
            duplicate_of_version_id=duplicate_of,
            status=IngestionCandidateStatus.PENDING.value,
            discovered_at=_now_iso(),
        )
        db.add(candidate)
        created.append(candidate)

    await db.commit()
    for c in created:
        await db.refresh(c)
    return {"discovered": len(created), "scanned_root": str(root), "candidates": [_candidate_payload(c) for c in created]}


# ── LIST / REVIEW ────────────────────────────────────────────────────────

def _candidate_payload(c: IngestionCandidate) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "filename": c.filename,
        "source_display_path": c.source_display_path,
        "file_extension": c.file_extension,
        "file_size": c.file_size,
        "checksum_sha256": c.checksum_sha256,
        "proposed_category": c.proposed_category,
        "category_confidence": c.category_confidence,
        "proposed_project_id": str(c.proposed_project_id) if c.proposed_project_id else None,
        "association_confidence": c.association_confidence,
        "association_evidence": c.association_evidence,
        "version_status": c.version_status,
        "duplicate_of_version_id": str(c.duplicate_of_version_id) if c.duplicate_of_version_id else None,
        "status": c.status,
        "discovered_at": c.discovered_at,
    }


@router.get("/candidates")
async def list_candidates(status: str | None = "pending", db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    stmt = select(IngestionCandidate).order_by(IngestionCandidate.discovered_at.desc())
    if status:
        stmt = stmt.where(IngestionCandidate.status == status)
    rows = (await db.execute(stmt)).scalars().all()
    return [_candidate_payload(c) for c in rows]


class CandidateUpdate(BaseModel):
    proposed_category: str | None = None
    proposed_project_id: str | None = None


@router.patch("/candidates/{candidate_id}")
async def update_candidate(candidate_id: str, body: CandidateUpdate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """User correction from review. Marks the field's confidence HIGH —
    a human just confirmed it, which is stronger evidence than any
    heuristic this module has."""
    candidate = (await db.execute(select(IngestionCandidate).where(IngestionCandidate.id == candidate_id))).scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != IngestionCandidateStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Candidate is already {candidate.status}, not pending review")

    if body.proposed_category is not None:
        candidate.proposed_category = body.proposed_category
        candidate.category_confidence = "high"
    if body.proposed_project_id is not None:
        candidate.proposed_project_id = uuid.UUID(body.proposed_project_id) if body.proposed_project_id else None
        candidate.association_confidence = "high" if body.proposed_project_id else "none"
        candidate.association_evidence = "user-confirmed in review"

    await db.commit()
    await db.refresh(candidate)
    return _candidate_payload(candidate)


@router.post("/candidates/{candidate_id}/ignore")
async def ignore_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    candidate = (await db.execute(select(IngestionCandidate).where(IngestionCandidate.id == candidate_id))).scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.status = IngestionCandidateStatus.IGNORED.value
    await db.commit()
    return {"id": str(candidate.id), "status": candidate.status}


# ── COMMIT ───────────────────────────────────────────────────────────────

_CATEGORY_LABELS = {
    "screenplay": "Screenplay", "budget": "Budget", "schedule": "Schedule", "deck": "Deck",
    "lookbook": "Look Book", "finance": "Finance Plan", "cast": "Cast", "crew": "Crew",
    "incentive": "Incentive", "legal": "Legal", "artwork": "Key Art", "other": "Other",
    "pre_qualification": "Pre-Qualification Letter", "incentive_estimate": "Incentive Estimate",
    "incentive_application": "Incentive Application", "incentive_certificate": "Incentive Certificate",
    "cost_report": "Cost Report",
}


def _slugify(title: str) -> str:
    return "-".join("".join(ch if ch.isalnum() else " " for ch in title.lower()).split())


@router.post("/candidates/{candidate_id}/commit")
async def commit_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await _commit_candidate_impl(candidate_id, db)


async def _commit_candidate_impl(candidate_id: str, db: AsyncSession, auto_master: bool = True) -> dict[str, Any]:
    """Creates the real, canonical records. Exact-checksum duplicates
    never create a second physical DocumentVersion — only an additional
    DocumentVersionSource on the existing one. A POSSIBLE_NEW_VERSION
    candidate always becomes its own new DocumentVersion with
    supersedes_version_id left NULL — this endpoint never guesses at
    ordering evidence it doesn't have.

    `auto_master` (Phase F): when an artwork commit would otherwise become
    the project's first/only master by default (no master exists yet),
    the CALLER can suppress that — used by batch ingestion when several
    plausible artwork candidates for the same project are being committed
    together and there is no clear winner (see Section 6: never guess a
    master when multiple legitimate candidates compete; leave all of them
    as candidates and surface the project as needing an explicit
    selection). The interactive review endpoint above always leaves this
    True — a human is committing one row at a time there."""
    candidate = (await db.execute(select(IngestionCandidate).where(IngestionCandidate.id == candidate_id))).scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != IngestionCandidateStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Candidate is already {candidate.status}")
    if candidate.proposed_project_id is None:
        raise HTTPException(status_code=400, detail="Assign a Project before committing (create one if needed)")

    project = (await db.execute(select(Project).where(Project.id == candidate.proposed_project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Assigned project no longer exists")

    source_path = Path(candidate.source_pointer)
    if not source_path.is_file():
        raise HTTPException(status_code=400, detail=f"Source file no longer exists: {candidate.source_pointer}")

    # Re-check dedup against LIVE state at commit time, not the snapshot
    # discovery computed — two candidates discovered in the same batch
    # can't see each other yet, so a batch of N files never knows about
    # sibling N+1..N until each is actually committed in turn.
    duplicate_of_version_id = candidate.duplicate_of_version_id
    if candidate.checksum_sha256 and not duplicate_of_version_id:
        duplicate_of_version_id = (await db.execute(
            select(DocumentVersion.id)
            .join(Document, DocumentVersion.document_id == Document.id)
            .where(
                DocumentVersion.checksum_sha256 == candidate.checksum_sha256,
                Document.project_id == candidate.proposed_project_id,
            )
        )).scalars().first()

    # Exact duplicate: record the additional location, create nothing new.
    if duplicate_of_version_id:
        existing_source = (await db.execute(
            select(DocumentVersionSource).where(
                DocumentVersionSource.document_version_id == duplicate_of_version_id,
                DocumentVersionSource.source_pointer == candidate.source_pointer,
            )
        )).scalar_one_or_none()
        if existing_source is None:
            db.add(DocumentVersionSource(
                id=uuid.uuid4(),
                document_version_id=duplicate_of_version_id,
                source_type=DocumentSourceType.LOCAL.value,
                source_pointer=candidate.source_pointer,
                source_path=candidate.source_display_path,
                source_status=DocumentSourceStatus.OK.value,
                last_verified_at=_now_iso(),
            ))
        candidate.status = IngestionCandidateStatus.COMMITTED.value
        candidate.version_status = VersionStatus.EXACT_DUPLICATE.value
        candidate.duplicate_of_version_id = duplicate_of_version_id
        candidate.committed_document_version_id = duplicate_of_version_id
        await db.commit()
        return {"id": str(candidate.id), "status": candidate.status, "result": "duplicate_source_recorded",
                "document_version_id": str(duplicate_of_version_id)}

    # New Document (find-or-create by project+category so a second
    # committed file of the SAME category becomes a new VERSION of the
    # same logical Document, not a second Document) + new DocumentVersion.
    document = (await db.execute(
        select(Document).where(Document.project_id == project.id, Document.category == candidate.proposed_category)
    )).scalar_one_or_none()
    is_new_document = document is None
    if document is None:
        label = _CATEGORY_LABELS.get(candidate.proposed_category, candidate.proposed_category.title())
        document = Document(
            id=uuid.uuid4(), project_id=project.id, category=candidate.proposed_category,
            title=f"{project.title} — {label}",
        )
        db.add(document)
        await db.flush()

    # Recomputed against LIVE document state at commit time (see the
    # dedup note above — the same same-batch staleness applies here): a
    # sibling version already existing for this Document, with a
    # DIFFERENT checksum, is genuinely ambiguous ordering. Never inferred
    # from filenames/dates — only left unresolved and surfaced as such.
    existing_current = None
    if not is_new_document and document.current_version_id:
        existing_current = (await db.execute(
            select(DocumentVersion).where(DocumentVersion.id == document.current_version_id)
        )).scalar_one_or_none()
    is_ambiguous_version = (
        existing_current is not None
        and existing_current.checksum_sha256 != candidate.checksum_sha256
    )

    project_dir = Path(settings.LOCAL_STORAGE_PATH) / _slugify(project.title)
    project_dir.mkdir(parents=True, exist_ok=True)
    dest_path = project_dir / candidate.filename
    if dest_path.exists() and dest_path.stat().st_size != (candidate.file_size or -1):
        dest_path = project_dir / f"{source_path.stem}-{uuid.uuid4().hex[:8]}{source_path.suffix}"
    shutil.copy2(source_path, dest_path)
    storage_rel_path = str(dest_path.relative_to(settings.LOCAL_STORAGE_PATH))

    version = DocumentVersion(
        id=uuid.uuid4(), document_id=document.id,
        original_filename=candidate.filename, storage_path=storage_rel_path,
        checksum_sha256=candidate.checksum_sha256, file_size=candidate.file_size,
        ingested_at=_now_iso(),
        # An ambiguous sibling never silently BECOMES current — the
        # existing current version stays current until a human resolves
        # the ordering; only a genuinely new (first) Document defaults on.
        is_current=not is_ambiguous_version,
        extraction_status=None,
        notes=(
            "Version order unresolved relative to an existing version of this "
            "document — ingested independently, no supersession claimed."
            if is_ambiguous_version else None
        ),
    )
    db.add(version)
    await db.flush()
    if is_ambiguous_version:
        candidate.version_status = VersionStatus.POSSIBLE_NEW_VERSION.value

    db.add(DocumentVersionSource(
        id=uuid.uuid4(), document_version_id=version.id,
        source_type=DocumentSourceType.LOCAL.value, source_pointer=candidate.source_pointer,
        source_path=candidate.source_display_path, source_status=DocumentSourceStatus.OK.value,
        last_verified_at=_now_iso(),
    ))

    if document.current_version_id is None or not is_ambiguous_version:
        document.current_version_id = version.id

    created_asset_id = None
    if candidate.proposed_category == "artwork":
        has_master = (await db.execute(
            select(ProjectAsset).where(ProjectAsset.project_id == project.id, ProjectAsset.is_master.is_(True))
        )).scalar_one_or_none()
        # Phase F provenance: an artwork candidate EXTRACTED from a deck/
        # lookbook/screenplay cover page carries the original document's
        # own version id + kind (see ingestion_candidate.py) so the asset
        # points at its real source, not at itself. A standalone
        # discovered image file (no extraction kind set) keeps the prior
        # Phase E behavior — self-referential DISCOVERED_IMAGE.
        _EXTRACTION_SOURCE_TYPE = {
            "deck": ProjectAssetSourceType.EXTRACTED_FROM_DECK.value,
            "lookbook": ProjectAssetSourceType.EXTRACTED_FROM_LOOKBOOK.value,
            "screenplay": ProjectAssetSourceType.EXTRACTED_FROM_SCREENPLAY.value,
        }
        asset_source_type = _EXTRACTION_SOURCE_TYPE.get(
            candidate.artwork_extraction_kind, ProjectAssetSourceType.DISCOVERED_IMAGE.value
        )
        asset_source_version_id = candidate.extracted_from_document_version_id or version.id
        asset = ProjectAsset(
            id=uuid.uuid4(), project_id=project.id, kind=ProjectAssetKind.ARTWORK.value,
            source_type=asset_source_type,
            storage_path=storage_rel_path, checksum_sha256=candidate.checksum_sha256,
            file_size=candidate.file_size, is_master=(has_master is None) and auto_master,
            source_document_version_id=asset_source_version_id,
            notes=candidate.notes,
        )
        db.add(asset)
        await db.flush()
        created_asset_id = asset.id

    candidate.status = IngestionCandidateStatus.COMMITTED.value
    candidate.committed_document_version_id = version.id
    candidate.committed_project_asset_id = created_asset_id
    candidate.cached_storage_path = storage_rel_path

    await db.commit()
    return {
        "id": str(candidate.id), "status": candidate.status, "result": "new_version_created",
        "document_id": str(document.id), "document_version_id": str(version.id),
        "project_asset_id": str(created_asset_id) if created_asset_id else None,
    }
