import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Numeric, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import StructureStatus, ConfidenceTier


class ProductionStructure(Base):
    """
    A candidate production structure — a specific combination of:
    - jurisdictions to shoot in
    - how budget is allocated across jurisdictions
    - which incentive programs are claimed
    - talent arrangement for qualification purposes

    The engine generates and ranks multiple structures per project.
    """
    __tablename__ = "production_structures"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StructureStatus] = mapped_column(
        String(20), nullable=False, default=StructureStatus.DRAFT
    )
    # Jurisdiction allocations as JSON: [{jurisdiction_id, shoot_pct, budget_pct, ...}]
    jurisdiction_allocations: Mapped[list | None] = mapped_column(JSONB)
    # Incentive programs claimed: [program_id, ...]
    claimed_program_ids: Mapped[list | None] = mapped_column(JSONB)
    # Talent arrangements for this structure: [{talent_id, role, jurisdiction_id, is_local}]
    talent_arrangements: Mapped[list | None] = mapped_column(JSONB)
    # Structure-level parameters
    assumed_jurisdiction_spend_pcts: Mapped[dict | None] = mapped_column(JSONB)
    # {jurisdiction_id: pct_of_qualifying_budget} — user input; high impact on calculation
    uses_georgia_logo: Mapped[bool | None] = mapped_column(Boolean)
    is_official_coproduction: Mapped[bool | None] = mapped_column(Boolean)
    coproduction_treaty: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    project: Mapped["Project"] = relationship(
        back_populates="production_structures", foreign_keys=[project_id]
    )
    calculation_results: Mapped[list["StructureCalculationResult"]] = relationship(
        back_populates="structure"
    )


class StructureCalculationResult(Base):
    """
    Output of running the deterministic calculation engine against a production structure.
    Stores full trace so every number is auditable.
    """
    __tablename__ = "structure_calculation_results"

    structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("production_structures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # Semantic version of the calculation engine that produced this result

    # Ingestion acceptance closeout, structure_type persistence (2026-09-17):
    # the authoritative structural-family classification for this result
    # (e.g. "hybrid", "full_relocation", "treaty_coproduction",
    # "component_relocation", "multi_program",
    # "same_jurisdiction_distinct_cost_pool_stack",
    # "same_jurisdiction_group_stack"), written by evaluate_project() at
    # the SAME construction site as calculation_trace_json's own
    # "structure_type" (or, for the two candidate families whose trace
    # never carried that key, its "structural_family" synonym) -- never a
    # second, independently-derived value. Previously this was NOT its
    # own column at all: every reader (project_workspace_view.py,
    # canonical_production_view.py) re-derived it at serve time by
    # reading back out of calculation_trace_json, or, when that key was
    # itself absent for a candidate with no jurisdiction_allocations row
    # (an UNPRICEABLE candidate), by parsing it out of the structure's own
    # display NAME string ("Full relocation to X") -- a real, disclosed
    # guess this column removes. Nullable because a handful of historical
    # rows (pre-dating this migration's backfill, or a future candidate
    # family that genuinely never assigns one) may carry no classification.
    structure_type: Mapped[str | None] = mapped_column(String(60), index=True)

    # Top-level outputs
    total_budget_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    rebase_btl_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    fixed_atl_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    total_qualifying_spend_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    total_incentive_value_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    total_travel_cost_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    true_net_cost_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    risk_adjusted_net_cost_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    effective_incentive_rate: Mapped[float | None] = mapped_column(Numeric(8, 6))

    # Rankings
    rank_by_net_cost: Mapped[int | None] = mapped_column(Integer)
    rank_by_incentive_value: Mapped[int | None] = mapped_column(Integer)
    rank_by_optimization_opportunity: Mapped[int | None] = mapped_column(Integer)

    # Per-program results (JSON array, one entry per claimed program)
    program_results: Mapped[list | None] = mapped_column(JSONB)
    # [{program_id, qualified, qualification_test_results, qualifying_spend, credit, ...}]

    # Qualification test scores
    qualification_test_scores: Mapped[dict | None] = mapped_column(JSONB)

    # Full calculation trace — every step must be here for auditability
    calculation_trace_json: Mapped[dict | None] = mapped_column(JSONB)

    # Flags and warnings
    has_unverified_inputs: Mapped[bool] = mapped_column(Boolean, default=False)
    legal_review_required: Mapped[bool] = mapped_column(Boolean, default=False)
    qualification_gaps: Mapped[list | None] = mapped_column(JSONB)
    stacking_violations: Mapped[list | None] = mapped_column(JSONB)
    warnings: Mapped[list | None] = mapped_column(JSONB)
    optimization_opportunities: Mapped[list | None] = mapped_column(JSONB)

    # Calculation-input provenance — added Phase B, additive only. Lets a
    # later reader determine "this result was calculated from an older
    # budget version" without redesigning the optimizer or recalculating
    # anything. input_snapshot_json is an immutable copy of the key
    # facts/budget totals actually used, taken at calculation time — a
    # frozen snapshot, not a live reference, so it stays accurate even if
    # ProjectFact/BudgetDocument rows are edited afterward.
    input_budget_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    input_fingerprint: Mapped[str | None] = mapped_column(String(64))
    input_snapshot_json: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    structure: Mapped["ProductionStructure"] = relationship(back_populates="calculation_results")
    input_budget_document_version: Mapped["DocumentVersion | None"] = relationship()
