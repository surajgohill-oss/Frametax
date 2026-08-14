import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
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

    # Phase C closeout: which canonical LOCATION_TAXONOMY slug (if any) this
    # row backs, and the producer's override value for it — the durable
    # home for the frontend's click-to-toggle location-category chips.
    # NULL/NULL for the free-text script-requirement rows written by 0063;
    # only used by category-override rows written by 0064+.
    category_key: Mapped[str | None] = mapped_column(String(64))
    override: Mapped[bool | None] = mapped_column(Boolean)

    # ── Script Analyzer SA-1 (canonical: LocationRequirement, EXTEND) ──────
    # Scripted-location rows derived deterministically from a screenplay
    # version. The critical separation the architecture demands: the
    # SCRIPTED location is an objective script fact; the PRODUCTION location
    # and the stage-vs-practical approach are producer decisions that neither
    # the parser nor any model may make. Both therefore default to UNKNOWN
    # and are only ever filled by confirmed project data.
    location_key: Mapped[str | None] = mapped_column(String(255), index=True)
    source_screenplay_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screenplay_documents.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    scene_sequences: Mapped[list | None] = mapped_column(JSONB)
    scene_count: Mapped[int | None] = mapped_column(Integer)
    eighths_total: Mapped[int | None] = mapped_column(Integer)
    int_count: Mapped[int | None] = mapped_column(Integer)
    ext_count: Mapped[int | None] = mapped_column(Integer)
    day_count: Mapped[int | None] = mapped_column(Integer)
    night_count: Mapped[int | None] = mapped_column(Integer)
    is_recurring: Mapped[bool | None] = mapped_column(Boolean)

    production_approach: Mapped[str | None] = mapped_column(String(24))
    # UNKNOWN unless a producer confirms STAGE / PRACTICAL. Never inferred.
    production_location: Mapped[str | None] = mapped_column(String(255))
    # UNKNOWN unless user/project data supplies it.
    evidence_state: Mapped[str | None] = mapped_column(String(32))
    parser_version: Mapped[str | None] = mapped_column(String(64))

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="location_requirements")
    source_document_version: Mapped["DocumentVersion | None"] = relationship()
    source_screenplay: Mapped["ScreenplayDocument | None"] = relationship()
