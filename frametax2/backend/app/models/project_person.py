import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ProjectPerson(Base):
    """
    Links a Project to a TalentProfile in a specific role (writer, director,
    producer, cast, other key personnel). Deliberately a thin join table,
    not a duplicate person model — TalentProfile (app/models/talent.py)
    already owns identity, nationality, residency, and guild-membership
    facts, plus its own per-jurisdiction qualification-attribute machinery.
    This table only answers "who is attached to THIS project, and as what."
    """
    __tablename__ = "project_people"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    talent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    # "director" | "writer" | "producer" | "lead_cast" | "cast" | other
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="people")
    talent: Mapped["TalentProfile"] = relationship()
