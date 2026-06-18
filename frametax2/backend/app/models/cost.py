import uuid
from sqlalchemy import String, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ConfidenceTier, SpendCategory


class LocalCostBenchmark(Base):
    """
    BTL cost multipliers and absolute benchmarks for a jurisdiction
    relative to a baseline (default: Los Angeles, US union rates).
    Drives BTL rebasing in net cost calculations.
    """
    __tablename__ = "local_cost_benchmarks"

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    baseline_jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=True
    )
    # Multipliers vs baseline (1.000 = same cost as baseline)
    crew_rate_multiplier: Mapped[float | None] = mapped_column(Numeric(8, 6))
    equipment_rental_multiplier: Mapped[float | None] = mapped_column(Numeric(8, 6))
    stage_facility_multiplier: Mapped[float | None] = mapped_column(Numeric(8, 6))
    location_fees_multiplier: Mapped[float | None] = mapped_column(Numeric(8, 6))
    post_production_multiplier: Mapped[float | None] = mapped_column(Numeric(8, 6))
    vfx_multiplier: Mapped[float | None] = mapped_column(Numeric(8, 6))
    catering_multiplier: Mapped[float | None] = mapped_column(Numeric(8, 6))
    # Key-crew relocation cost (average daily USD to move non-local crew in)
    key_crew_daily_travel_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    # Additional per-category overrides
    category_overrides_json: Mapped[dict | None] = mapped_column(JSONB)
    data_source: Mapped[str | None] = mapped_column(String(512))
    as_of_date: Mapped[str | None] = mapped_column(String(20))
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    jurisdiction: Mapped["Jurisdiction"] = relationship(
        back_populates="local_cost_benchmarks", foreign_keys=[jurisdiction_id]
    )


class UnionFringeRule(Base):
    """
    Union/guild-specific payroll fringe rates and applicability rules.
    Applied on top of gross labor to compute fully-loaded labor cost.
    """
    __tablename__ = "union_fringe_rules"

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False, index=True
    )
    union_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # "SAG-AFTRA", "IATSE", "Teamsters", "ACTRA", "DGC", etc.
    fringe_rate: Mapped[float] = mapped_column(Numeric(7, 6), nullable=False)
    # e.g. 0.38 for 38% on top of gross
    applies_to_categories: Mapped[list | None] = mapped_column(JSONB)
    # list of SpendCategory strings
    cap_per_employee_usd: Mapped[float | None] = mapped_column(Numeric(12, 2))
    # annual fringe cap per employee
    effective_from: Mapped[str | None] = mapped_column(String(20))
    effective_until: Mapped[str | None] = mapped_column(String(20))
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=True
    )
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )
    notes: Mapped[str | None] = mapped_column(Text)
