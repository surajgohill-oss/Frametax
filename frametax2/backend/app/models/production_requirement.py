"""
production_requirement.py

Script Analyzer SA-1 (canonical: ProductionRequirement, BUILD_NEW).

An evidence-backed statement that the production NEEDS something, derived
from persisted objective script facts. It connects to — and never replaces —
ProductionPackage's existing facts/questions layer.

The single most important rule here, straight from the canonical
architecture: presence is not a cost assumption.

    "A horse appears in scene 12"

is a requirement with evidence. It does NOT become

    "2 trained horses for 5 days"

That conversion is interpretation plus producer confirmation, and belongs to
a later phase. SA-1 therefore stores quantity/duration as NULL and marks the
requirement's evidence_state so nothing downstream can mistake an observation
for a plan.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# ── evidence / authority states (canonical input_precedence) ───────────────
EVIDENCE_ACTUAL = "ACTUAL"
EVIDENCE_USER_CONFIRMED = "USER_CONFIRMED"
EVIDENCE_DETERMINISTIC_DERIVED = "DETERMINISTIC_DERIVED"
EVIDENCE_MODEL_ESTIMATE = "MODEL_ESTIMATE"
EVIDENCE_GLOBAL_DEFAULT = "GLOBAL_DEFAULT"
EVIDENCE_UNKNOWN = "UNKNOWN"

EVIDENCE_STATES = (
    EVIDENCE_ACTUAL,
    EVIDENCE_USER_CONFIRMED,
    EVIDENCE_DETERMINISTIC_DERIVED,
    EVIDENCE_MODEL_ESTIMATE,
    EVIDENCE_GLOBAL_DEFAULT,
    EVIDENCE_UNKNOWN,
)

#: Precedence order — lower index wins when two sources assert the same field.
EVIDENCE_PRECEDENCE = {state: i for i, state in enumerate(EVIDENCE_STATES)}


class ProductionRequirement(Base):
    """One evidence-backed production requirement for a project."""

    __tablename__ = "production_requirements"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    requirement_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # SCRIPTED_LOCATION | CHARACTER | EXPLICIT_VEHICLE | EXPLICIT_ANIMAL |
    # EXPLICIT_WEAPON | EXPLICIT_MINOR | EXPLICIT_PROP | PERIOD_REFERENCE
    normalized_value: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Quantities stay NULL in SA-1 — presence is evidence, scale is not.
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4))
    quantity_max: Mapped[float | None] = mapped_column(Numeric(18, 4))
    unit: Mapped[str | None] = mapped_column(String(32))

    evidence_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EVIDENCE_DETERMINISTIC_DERIVED, index=True,
    )
    is_interpretation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    requires_confirmation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # Provenance — every requirement must answer "from what, exactly?"
    source_screenplay_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screenplay_documents.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    source_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_scene_sequences: Mapped[list | None] = mapped_column(JSONB)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sample_evidence: Mapped[str | None] = mapped_column(Text)
    parser_version: Mapped[str | None] = mapped_column(String(64))

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="production_requirements")
    source_screenplay: Mapped["ScreenplayDocument | None"] = relationship()


class ProductionAssumption(Base):
    """
    Script Analyzer SA-1 (canonical: ProductionAssumption, BUILD_NEW) —
    minimum shape only.

    Holds the explicit producer inputs a generic project needs before the
    optimizer can price anything (intended shoot days, scale, base
    jurisdiction, stage/location split, pages per day). SA-1 deliberately
    ships NO scheduling engine: nothing here is computed, and an absent
    value stays UNKNOWN rather than defaulting to an invented number.
    """

    __tablename__ = "production_assumptions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    assumption_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # intended_shoot_days | production_scale | primary_unit |
    # base_jurisdiction | stage_location_split | pages_per_day
    value: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str | None] = mapped_column(String(20))
    unit: Mapped[str | None] = mapped_column(String(32))

    evidence_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EVIDENCE_UNKNOWN, index=True,
    )
    source: Mapped[str | None] = mapped_column(String(120))
    lower_bound: Mapped[float | None] = mapped_column(Numeric(18, 4))
    upper_bound: Mapped[float | None] = mapped_column(Numeric(18, 4))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="production_assumptions")
