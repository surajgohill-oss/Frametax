import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ProjectActivity(Base):
    """
    Immutable provenance log for meaningful Project state changes: lifecycle
    changed, project renamed, alias added, document associated/reassociated,
    canonical document version changed, fact overridden, artwork master
    changed, leading structure changed. Base.created_at is the event
    timestamp — no separate field needed.

    This is provenance infrastructure, not enterprise audit/compliance
    software: normal application code must never UPDATE or DELETE a row in
    this table. There is no code in this phase that writes to it yet — this
    is the persistence model only, ready for later phases to write into.
    """
    __tablename__ = "project_activity"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor: Mapped[str | None] = mapped_column(String(320))
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. "lifecycle_changed", "alias_added", "document_associated",
    # "current_version_changed", "fact_overridden", "master_asset_changed",
    # "leading_structure_changed"
    entity_type: Mapped[str | None] = mapped_column(String(100))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    before_json: Mapped[dict | None] = mapped_column(JSONB)
    after_json: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="activity")
