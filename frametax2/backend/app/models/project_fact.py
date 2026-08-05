import uuid
from sqlalchemy import String, Text, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ProjectFactSourceType, ReviewStatus


class ProjectFact(Base):
    """
    The canonical structured-fact layer between source/parsed material and
    derived optimizer analysis (director, director nationality, writer,
    cast, shoot duration, currency assumption, etc.). ProjectFact holds
    exactly ONE current row per (project_id, fact_key) — the CURRENT
    canonical value. It is deliberately NOT its own history mechanism: a
    human override does not get a `previous_value` column here (that would
    only remember one edit). The full history of how a fact's value changed
    over time belongs in ProjectActivity, which is append-only.

    No fixed column per possible fact — an extensible key/value shape, so
    this does not need a migration every time a new fact type is needed,
    while remaining fully queryable by fact_key and provenance.
    """
    __tablename__ = "project_facts"
    __table_args__ = (
        UniqueConstraint("project_id", "fact_key", name="uq_project_facts_project_key"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fact_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. "director", "director_nationality", "writer", "shoot_duration_weeks"
    value: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str | None] = mapped_column(String(20))
    # "string" | "number" | "boolean" | "json" — how to interpret `value`

    # Provenance — every fact must be able to answer WHAT/WHERE/HOW CONFIDENT/REVIEWED?
    source_type: Mapped[ProjectFactSourceType] = mapped_column(String(20), nullable=False)
    source_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    source_location: Mapped[str | None] = mapped_column(String(255))
    # Free text page/row/section reference within the source document.
    extraction_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    review_status: Mapped[ReviewStatus] = mapped_column(
        String(20), nullable=False, default=ReviewStatus.PENDING, server_default=ReviewStatus.PENDING.value,
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="facts")
    source_document_version: Mapped["DocumentVersion | None"] = relationship()
