import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ProjectAlias(Base):
    """
    A working title, former title, alternate title, or source-material title
    for a Project. Renaming Project.title must never destroy discoverability
    under an old title — e.g. "The Men We Leave Behind" was previously known
    under a different title in its own look book. Purely additive; no rename
    workflow or UI is implemented here.
    """
    __tablename__ = "project_aliases"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str | None] = mapped_column(Text)
    # Free text: e.g. "renamed from" / "found in look book title page" / "working title"

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="aliases")
