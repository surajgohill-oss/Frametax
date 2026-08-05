import uuid
from sqlalchemy import String, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import FinalResultStatus


class FinalProductionResult(Base):
    """
    Separates the MODELED result (StructureCalculationResult — a
    projection) from WHAT ACTUALLY HAPPENED. Essential future input to
    Company Knowledge (realized incentive rates, actual vs. modeled
    variance) — not built or populated in this phase.

    One row per Project (1:1) — the architecture review's own documented
    choice: nothing in the current corpus demonstrates a real need for
    multiple final results per project (re-shoots/reboots), and modeling
    that speculatively would be over-engineering. If that need is ever
    demonstrated, this is the seam to revisit, not something to guess at now.

    modeled_economics_snapshot is a frozen JSON copy of the leading
    structure's calculation result AT DECISION TIME — deliberately not a
    live reference, so the historical decision stays accurate even if the
    underlying StructureCalculationResult is later recalculated from a
    different budget version.
    """
    __tablename__ = "final_production_results"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    leading_structure_id_at_decision: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("production_structures.id", ondelete="SET NULL"), nullable=True
    )
    modeled_economics_snapshot: Mapped[dict | None] = mapped_column(JSONB)

    final_incentive_expected_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    final_incentive_applied_for_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    final_incentive_approved_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    final_incentive_realized_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    final_local_cost_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    final_production_cost_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    variance_notes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[FinalResultStatus] = mapped_column(
        String(20), nullable=False, default=FinalResultStatus.NOT_STARTED,
        server_default=FinalResultStatus.NOT_STARTED.value,
    )
    recorded_at: Mapped[str | None] = mapped_column(String(30))
    recorded_by: Mapped[str | None] = mapped_column(String(320))

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="final_result")
    leading_structure_at_decision: Mapped["ProductionStructure | None"] = relationship()
