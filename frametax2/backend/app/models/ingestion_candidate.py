"""
ingestion_candidate.py — Phase E staging model.

DISCOVER -> CLASSIFY -> ASSOCIATE all write here, never to the canonical
documents/document_versions tables directly. Only COMMIT (a user action on
a reviewed row) creates a real Document/DocumentVersion/DocumentVersionSource
(and, for artwork, a ProjectAsset). This is the one property that makes
review meaningful: nothing discovered is canonical until a human confirms
it, and an IGNOREd or still-PENDING row can never leak into a Project's
real material.

No file bytes live in Postgres — source_pointer is a filesystem path (or a
future connector's own stable pointer); cached_storage_path is set only
once a candidate is actually committed and its bytes copied under the
durable LOCAL_STORAGE_PATH root, same convention as DocumentVersion.
"""
import uuid
from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import (
    DocumentSourceType, DocumentCategory, IngestionCandidateStatus, MatchConfidence, VersionStatus,
)


class IngestionCandidate(Base):
    __tablename__ = "ingestion_candidates"

    source_type: Mapped[DocumentSourceType] = mapped_column(String(20), nullable=False)
    source_pointer: Mapped[str] = mapped_column(Text, nullable=False)
    # Absolute local path today; a future connector's stable id (e.g. a
    # Drive file id) without changing this column's meaning.
    source_display_path: Mapped[str | None] = mapped_column(Text)
    # Human-readable breadcrumb (e.g. the containing folder), shown in review.

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_extension: Mapped[str | None] = mapped_column(String(20))
    file_size: Mapped[int | None] = mapped_column(Integer)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)

    proposed_category: Mapped[DocumentCategory] = mapped_column(String(30), nullable=False)
    category_confidence: Mapped[MatchConfidence] = mapped_column(String(10), nullable=False)

    proposed_project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    association_confidence: Mapped[MatchConfidence] = mapped_column(String(10), nullable=False)
    association_evidence: Mapped[str | None] = mapped_column(Text)
    # Human-readable reason (e.g. "filename matches project title 'The Dale'")
    # — never silently applied without this being visible in review.

    version_status: Mapped[VersionStatus] = mapped_column(String(30), nullable=False)
    duplicate_of_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[IngestionCandidateStatus] = mapped_column(
        String(20), nullable=False, default=IngestionCandidateStatus.PENDING,
        server_default=IngestionCandidateStatus.PENDING.value,
    )
    cached_storage_path: Mapped[str | None] = mapped_column(String(1024))
    # Set only on commit — the discover/review phase never copies bytes.
    committed_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    committed_project_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_assets.id", ondelete="SET NULL"), nullable=True
    )
    discovered_at: Mapped[str] = mapped_column(String(40), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Phase F — set only for an ARTWORK candidate that was extracted from a
    # cover/title page of another document (a deck, a look book, a
    # screenplay), never for a standalone discovered image file. Read by
    # commit_candidate() to give the resulting ProjectAsset real provenance
    # (which DocumentVersion it came from, and what kind of page) instead
    # of defaulting to a self-referential DISCOVERED_IMAGE.
    extracted_from_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    artwork_extraction_kind: Mapped[str | None] = mapped_column(String(20))  # "deck" | "lookbook" | "screenplay"

    # Relationships
    proposed_project: Mapped["Project | None"] = relationship(foreign_keys=[proposed_project_id])
    duplicate_of_version: Mapped["DocumentVersion | None"] = relationship(foreign_keys=[duplicate_of_version_id])
    committed_document_version: Mapped["DocumentVersion | None"] = relationship(foreign_keys=[committed_document_version_id])
    committed_project_asset: Mapped["ProjectAsset | None"] = relationship(foreign_keys=[committed_project_asset_id])
    extracted_from_document_version: Mapped["DocumentVersion | None"] = relationship(foreign_keys=[extracted_from_document_version_id])
