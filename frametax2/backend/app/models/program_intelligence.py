"""
program_intelligence.py

Phase C: Program administration intelligence (payment timing, audit, assignability,
         per-category spend treatment).

Phase D: Historical production benchmark infrastructure (ingested benchmark records,
         spend items per production, ingestion audit log).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, Numeric, String, Text, DateTime
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ConfidenceTier


# ---------------------------------------------------------------------------
# Phase C — Program Administration Intelligence
# ---------------------------------------------------------------------------

class ProgramAdminDetails(Base):
    """
    Operational intelligence for an incentive program: payment timing, audit
    requirements, assignability, and financing friction notes.

    One row per incentive_program (one-to-one via program_id UNIQUE).
    """
    __tablename__ = "program_admin_details"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incentive_programs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    payment_timing_weeks: Mapped[int | None] = mapped_column(
        Integer,
        comment="Typical weeks from qualifying spend certification to cash receipt.",
    )
    payment_timing_notes: Mapped[str | None] = mapped_column(
        String(512),
        comment="Narrative on payment timing variability, batching, or delays.",
    )
    audit_required: Mapped[bool | None] = mapped_column(
        Boolean,
        comment="Whether an independent cost report / audit is required to claim.",
    )
    audit_authority: Mapped[str | None] = mapped_column(
        String(255),
        comment="Body that conducts or certifies the audit (e.g. Big 4 firm, government office).",
    )
    audit_cost_estimate_usd: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        comment="Typical third-party audit cost in USD.",
    )
    is_assignable: Mapped[bool | None] = mapped_column(
        Boolean,
        comment="Whether the credit/rebate can be assigned to a lender/financier.",
    )
    assignability_notes: Mapped[str | None] = mapped_column(
        Text,
        comment="Conditions, restrictions, or mechanics of assignability.",
    )
    processing_timeline_weeks: Mapped[int | None] = mapped_column(
        Integer,
        comment="End-to-end weeks from application submission to final payment.",
    )
    financing_friction_notes: Mapped[str | None] = mapped_column(
        Text,
        comment="Notes on bridge financing availability, lender appetite, discount rates.",
    )
    first_window_open_relative: Mapped[str | None] = mapped_column(
        String(100),
        comment="When application window first opens (e.g. 'before principal photography').",
    )
    final_claim_deadline: Mapped[str | None] = mapped_column(
        String(100),
        comment="Claim submission deadline relative to wrap (e.g. '12 months after delivery').",
    )
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )
    notes: Mapped[str | None] = mapped_column(Text)

    program: Mapped["IncentiveProgram"] = relationship(  # noqa: F821
        "IncentiveProgram", foreign_keys=[program_id]
    )


class ProgramSpendTreatment(Base):
    """
    Per-category spend treatment for a program: whether each labor/spend type
    qualifies, and whether a cap applies.

    Multiple rows per program (one per labor_type / spend_category combination).
    """
    __tablename__ = "program_spend_treatments"
    __table_args__ = (
        UniqueConstraint("program_id", "labor_type", name="uq_spend_treatment_program_labor"),
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incentive_programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    labor_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment=(
            "Category identifier: 'atl_writer', 'atl_director', 'atl_producer', "
            "'atl_cast', 'btl_crew_local', 'btl_crew_foreign', 'equipment', "
            "'stage_facility', 'vfx', 'post', 'music', 'catering', 'travel', "
            "'marine_vessel', 'other'."
        ),
    )
    qualifies: Mapped[bool | None] = mapped_column(
        Boolean,
        comment="True=qualifies, False=excluded, None=unconfirmed.",
    )
    cap_pct: Mapped[float | None] = mapped_column(
        Numeric(7, 6),
        comment="If capped: max this category can represent as fraction of qualifying total.",
    )
    cap_amount_local: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        comment="Hard per-category cap in local currency (if applicable).",
    )
    treatment_notes: Mapped[str | None] = mapped_column(
        Text,
        comment="Source excerpt or notes on treatment basis.",
    )
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )

    program: Mapped["IncentiveProgram"] = relationship(  # noqa: F821
        "IncentiveProgram", foreign_keys=[program_id]
    )


# ---------------------------------------------------------------------------
# Phase D — Historical Production Benchmark Infrastructure
# ---------------------------------------------------------------------------

class HistoricalProductionBenchmark(Base):
    """
    A single historical production's aggregated spend data, used to
    calibrate CostBenchmarkEntry multipliers against real-world actuals.

    Not linked to projects — these are reference/training records only.
    """
    __tablename__ = "historical_production_benchmarks"

    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Working title or anonymised identifier.",
    )
    production_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="feature | tv_series | documentary | animation | vfx_heavy | commercial",
    )
    release_year: Mapped[int | None] = mapped_column(Integer)
    principal_jurisdiction_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Primary filming jurisdiction (e.g. GB, AU-NSW).",
    )
    total_budget_usd: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        comment="Total production budget in USD at time of production.",
    )
    qualifying_spend_usd: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        comment="Qualifying expenditure in USD that applied to incentive claim.",
    )
    incentive_received_usd: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        comment="Actual incentive cash/credit received in USD.",
    )
    effective_rate_achieved: Mapped[float | None] = mapped_column(
        Numeric(7, 6),
        comment="Actual rate = incentive_received / qualifying_spend.",
    )
    la_equivalent_budget_usd: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        comment="Estimated cost of equivalent production filmed entirely in Los Angeles.",
    )
    data_source: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Source of this benchmark data (e.g. 'Producer interview', 'Published budget', 'Film office data').",
    )
    data_source_url: Mapped[str | None] = mapped_column(String(2048))
    is_anonymised: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="True if title or details have been obscured for confidentiality.",
    )
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )
    notes: Mapped[str | None] = mapped_column(Text)

    spend_items: Mapped[list["BenchmarkSpendItem"]] = relationship(
        back_populates="benchmark", cascade="all, delete-orphan"
    )


class BenchmarkSpendItem(Base):
    """
    Individual spend-category line item for a HistoricalProductionBenchmark.
    Used to derive category-level multipliers vs the LA baseline.
    """
    __tablename__ = "benchmark_spend_items"

    benchmark_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("historical_production_benchmarks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="Spend category matching program_spend_treatments.labor_type vocabulary.",
    )
    amount_local: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        comment="Amount spent in local currency.",
    )
    currency_code: Mapped[str | None] = mapped_column(String(3))
    amount_usd: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        comment="Amount in USD at production-period exchange rate.",
    )
    pct_of_total_budget: Mapped[float | None] = mapped_column(
        Numeric(7, 6),
        comment="This category as fraction of total_budget_usd.",
    )
    la_equivalent_usd: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        comment="What this category would cost in LA (used to compute multiplier).",
    )
    derived_multiplier: Mapped[float | None] = mapped_column(
        Numeric(7, 4),
        comment="amount_usd / la_equivalent_usd — the LA-relative cost multiplier.",
    )
    notes: Mapped[str | None] = mapped_column(Text)

    benchmark: Mapped["HistoricalProductionBenchmark"] = relationship(
        back_populates="spend_items"
    )


class BenchmarkIngestionLog(Base):
    """
    Audit log for each batch of historical benchmark data ingested.
    Tracks source, method, record count, and outcome.
    """
    __tablename__ = "benchmark_ingestion_logs"

    source_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of the data source (e.g. 'AICP Bid Survey 2024', 'Producer XYZ interview').",
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="survey | interview | public_filing | film_office_data | academic | estimated",
    )
    source_url: Mapped[str | None] = mapped_column(String(2048))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    record_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    jurisdiction_codes: Mapped[str | None] = mapped_column(
        String(512),
        comment="Comma-separated jurisdiction codes covered by this batch.",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="complete",
        comment="complete | partial | failed | pending_review",
    )
    ingested_by: Mapped[str | None] = mapped_column(
        String(100),
        comment="User or process that performed the ingestion.",
    )
    notes: Mapped[str | None] = mapped_column(Text)
