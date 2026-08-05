"""
library_document.py — the universal Document identity/version/source layer.

Canonical hierarchy (Phase B architecture review, §6):

    Project (or Organization)
        v
    Document            -- WHAT the material is ("The Dale screenplay")
        v
    DocumentVersion      -- a particular physical/versioned artifact
        v                   ("Dale TW Rev 1-14-26.pdf")
    DocumentVersionSource -- where a copy of that exact version was found
                             (a version may exist in multiple locations)

A Document belongs to EXACTLY ONE owner scope — a Project or an
Organization, never both, enforced by a CHECK constraint — so company/slate
material (MTS investor decks, financial models) and individual-film material
share the same identity/version/source model instead of a duplicated
"OrganizationDocument" implementation.

Existing rich typed models (BudgetDocument/BudgetLineItem,
ScreenplayDocument/ScreenplayChunk/ExtractedScriptElement) are NOT replaced.
They gain an additive, nullable `document_version_id` link into this layer
(see budget.py, screenplay.py) so a physical DocumentVersion can point to its
typed parsed representation where one exists, without a parser rewrite.

This file builds persistence only. No discovery, classification, or
ingestion pipeline is implemented here (Phase E).
"""
import uuid
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import DocumentCategory, DocumentSourceType, DocumentSourceStatus


class Document(Base):
    """
    A logical document identity — WHAT the material is, independent of any
    particular physical file. Owned by exactly one of Project or
    Organization (CHECK constraint enforces this; never both, never neither).
    """
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "(project_id IS NOT NULL AND organization_id IS NULL) OR "
            "(project_id IS NULL AND organization_id IS NOT NULL)",
            name="ck_documents_exactly_one_owner",
        ),
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    category: Mapped[DocumentCategory] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    # The version currently treated as canonical/current for this document.
    # Nullable + use_alter because DocumentVersion.document_id points back
    # here — a genuine circular table dependency, resolved at the migration
    # level by creating this FK after document_versions exists.
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="SET NULL", use_alter=True, name="fk_documents_current_version"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    project: Mapped["Project | None"] = relationship(back_populates="documents")
    organization: Mapped["Organization | None"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", foreign_keys="DocumentVersion.document_id"
    )
    current_version: Mapped["DocumentVersion | None"] = relationship(
        foreign_keys=[current_version_id], post_update=True,
    )


class DocumentVersion(Base):
    """
    A particular physical/versioned artifact of a Document
    ("Dale TW Rev 1-14-26.pdf"). Never deleted by normal operation — a
    replaced "current" version is marked is_current=False, not removed, so
    history is never destroyed. Version ordering (supersedes_version_id) is
    left null whenever it cannot be confidently determined — never fabricated.
    """
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str | None] = mapped_column(String(512))
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    # Path under the durable local storage root (see core.config.LOCAL_STORAGE_PATH)
    # where CineGlobe's own cached copy lives. Null until actually cached.
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    file_size: Mapped[int | None] = mapped_column(Integer)
    detected_date: Mapped[str | None] = mapped_column(String(20))
    # Best-effort date parsed from filename/metadata — never fabricated
    version_label: Mapped[str | None] = mapped_column(String(255))
    ingested_at: Mapped[str | None] = mapped_column(String(40))
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    supersedes_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    extraction_status: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="versions", foreign_keys=[document_id])
    sources: Mapped[list["DocumentVersionSource"]] = relationship(back_populates="document_version")
    supersedes: Mapped["DocumentVersion | None"] = relationship(remote_side="DocumentVersion.id")


class DocumentVersionSource(Base):
    """
    Where a copy of an exact DocumentVersion was found. A single
    byte-identical file discovered in Drive, a Drive "Downloads" mirror, and
    a local Mac Downloads folder becomes ONE DocumentVersion with THREE
    DocumentVersionSource rows — never three separate Documents.
    """
    __tablename__ = "document_version_sources"
    __table_args__ = (
        UniqueConstraint("document_version_id", "source_pointer", name="uq_docversion_source_pointer"),
    )

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[DocumentSourceType] = mapped_column(String(20), nullable=False, index=True)
    source_pointer: Mapped[str] = mapped_column(String(2048), nullable=False)
    # Stable identifier for this source: absolute local path, Drive file ID,
    # or a future connector's own stable identifier.
    source_path: Mapped[str | None] = mapped_column(Text)
    # Human-readable path/URL at the source, for display — may go stale.
    source_owner: Mapped[str | None] = mapped_column(String(320))
    # e.g. the Drive account email that owns the file, where available.
    source_status: Mapped[DocumentSourceStatus] = mapped_column(
        String(20), nullable=False, default=DocumentSourceStatus.OK, server_default=DocumentSourceStatus.OK.value,
    )
    last_verified_at: Mapped[str | None] = mapped_column(String(40))

    # Relationships
    document_version: Mapped["DocumentVersion"] = relationship(back_populates="sources")
