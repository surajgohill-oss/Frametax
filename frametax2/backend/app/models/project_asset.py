import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ProjectAssetKind, ProjectAssetSourceType


class ProjectAsset(Base):
    """
    Project artwork (and other project assets). Replaces the current
    hardcoded-per-production frontend import pattern with real persistence.
    Exactly one ProjectAsset per Project should have is_master=True at a
    time (enforced at the application level in a later phase, not by a DB
    constraint here — a partial unique index would be the natural future
    tightening once real selection logic exists). Extraction/generation
    logic is not implemented in this phase; only the model that will hold
    the results.
    """
    __tablename__ = "project_assets"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[ProjectAssetKind] = mapped_column(
        String(20), nullable=False, default=ProjectAssetKind.ARTWORK, server_default=ProjectAssetKind.ARTWORK.value,
    )
    source_type: Mapped[ProjectAssetSourceType] = mapped_column(String(30), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    file_size: Mapped[int | None] = mapped_column(Integer)
    is_master: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # Provenance — if this asset was extracted from a document (a deck cover,
    # a look book page), link back to the exact version it came from.
    source_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="assets")
    source_document_version: Mapped["DocumentVersion | None"] = relationship()
