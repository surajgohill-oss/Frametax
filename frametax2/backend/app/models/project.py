import uuid
from sqlalchemy import String, Text, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    logline: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str | None] = mapped_column(String(100))
    format: Mapped[str | None] = mapped_column(String(100))   # "feature", "series", "documentary"
    total_budget_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    home_jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=True
    )
    target_shoot_year: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="projects")
    owner: Mapped["User"] = relationship(back_populates="projects")
    budget_documents: Mapped[list["BudgetDocument"]] = relationship(back_populates="project")
    screenplay_documents: Mapped[list["ScreenplayDocument"]] = relationship(back_populates="project")
    production_structures: Mapped[list["ProductionStructure"]] = relationship(back_populates="project")
    contributions: Mapped[list["ProductionContribution"]] = relationship(back_populates="project")
