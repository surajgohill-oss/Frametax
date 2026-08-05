import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ProjectLocationRequirement(Base):
    """
    A PROJECT-specific location requirement (Mediterranean coastal town,
    open sea, a specific city, a non-relocatable story location) — not a
    jurisdiction recommendation. This is the persistent home for what the
    existing frontend Location Requirements chips already represent for the
    Little Utopia demo; script-extraction logic that would populate this
    automatically is out of scope for this phase.
    """
    __tablename__ = "project_location_requirements"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_flexible: Mapped[bool | None] = mapped_column(Boolean)
    # True = relocatable to a similar-looking jurisdiction; False = a fixed,
    # non-relocatable story location; null = not yet assessed.
    source_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="location_requirements")
    source_document_version: Mapped["DocumentVersion | None"] = relationship()
