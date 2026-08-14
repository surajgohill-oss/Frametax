import uuid
from sqlalchemy import String, Text, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ProjectLifecycle


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

    # Lifecycle — USER-CONTROLLED ONLY. The engine (optimizer, document
    # completeness, incentive qualification, scenario selection) must never
    # write this column. See enums.ProjectLifecycle and CAPABILITY_LEDGER.md
    # "Production Lifecycle Rule". Every newly-created title-only Project
    # defaults to EVALUATION, matching the frontend's existing convention.
    lifecycle: Mapped[ProjectLifecycle] = mapped_column(
        String(20), nullable=False, default=ProjectLifecycle.EVALUATION,
        server_default=ProjectLifecycle.EVALUATION.value,
    )

    # The Project's current leading ProductionStructure, if one has been
    # selected. Deliberately a single nullable column on Project rather than
    # a separate LeadingScenario table — "which structure is leading" is 1:1
    # project state; the history of that selection changing over time is a
    # ProjectActivity entry, not a second table. Ambiguous-FK-safe: Project
    # already has a project_id-based relationship to ProductionStructure
    # (production_structures below), so this second FK path requires explicit
    # foreign_keys= on both sides (see ProductionStructure.leading_for_project).
    leading_structure_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("production_structures.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="projects")
    owner: Mapped["User"] = relationship(back_populates="projects")
    budget_documents: Mapped[list["BudgetDocument"]] = relationship(back_populates="project")
    screenplay_documents: Mapped[list["ScreenplayDocument"]] = relationship(back_populates="project")
    production_structures: Mapped[list["ProductionStructure"]] = relationship(
        back_populates="project", foreign_keys="ProductionStructure.project_id"
    )
    leading_structure: Mapped["ProductionStructure | None"] = relationship(
        foreign_keys=[leading_structure_id], post_update=True,
    )
    contributions: Mapped[list["ProductionContribution"]] = relationship(back_populates="project")
    aliases: Mapped[list["ProjectAlias"]] = relationship(back_populates="project")
    documents: Mapped[list["Document"]] = relationship(back_populates="project")
    assets: Mapped[list["ProjectAsset"]] = relationship(back_populates="project")
    facts: Mapped[list["ProjectFact"]] = relationship(back_populates="project")
    activity: Mapped[list["ProjectActivity"]] = relationship(back_populates="project")
    location_requirements: Mapped[list["ProjectLocationRequirement"]] = relationship(back_populates="project")
    # Script Analyzer SA-1
    production_requirements: Mapped[list["ProductionRequirement"]] = relationship(back_populates="project")
    production_assumptions: Mapped[list["ProductionAssumption"]] = relationship(back_populates="project")
    people: Mapped[list["ProjectPerson"]] = relationship(back_populates="project")
    final_result: Mapped["FinalProductionResult | None"] = relationship(back_populates="project")
