"""0014 — Phase C/D: Program intelligence and historical benchmark tables.

Phase C — Program administration intelligence:
  program_admin_details      : payment timing, audit, assignability, processing timeline
  program_spend_treatments   : per-category QPE treatment with cap support

Phase D — Historical production benchmark infrastructure:
  historical_production_benchmarks : real-world production spend records
  benchmark_spend_items            : per-category spend lines for each benchmark
  benchmark_ingestion_logs         : audit trail for benchmark data ingestion batches

No data seeded in this migration (pure schema).

Revision ID: 0014
Revises: 0013
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Phase C — program_admin_details
    # ------------------------------------------------------------------
    op.create_table(
        "program_admin_details",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("program_id", UUID(as_uuid=True),
                  sa.ForeignKey("incentive_programs.id", ondelete="CASCADE"),
                  nullable=False, unique=True, index=True),
        sa.Column("payment_timing_weeks", sa.Integer, nullable=True),
        sa.Column("payment_timing_notes", sa.String(512), nullable=True),
        sa.Column("audit_required", sa.Boolean, nullable=True),
        sa.Column("audit_authority", sa.String(255), nullable=True),
        sa.Column("audit_cost_estimate_usd", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_assignable", sa.Boolean, nullable=True),
        sa.Column("assignability_notes", sa.Text, nullable=True),
        sa.Column("processing_timeline_weeks", sa.Integer, nullable=True),
        sa.Column("financing_friction_notes", sa.Text, nullable=True),
        sa.Column("first_window_open_relative", sa.String(100), nullable=True),
        sa.Column("final_claim_deadline", sa.String(100), nullable=True),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # ------------------------------------------------------------------
    # Phase C — program_spend_treatments
    # ------------------------------------------------------------------
    op.create_table(
        "program_spend_treatments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("program_id", UUID(as_uuid=True),
                  sa.ForeignKey("incentive_programs.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("labor_type", sa.String(80), nullable=False),
        sa.Column("qualifies", sa.Boolean, nullable=True),
        sa.Column("cap_pct", sa.Numeric(7, 6), nullable=True),
        sa.Column("cap_amount_local", sa.Numeric(18, 2), nullable=True),
        sa.Column("treatment_notes", sa.Text, nullable=True),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.UniqueConstraint("program_id", "labor_type", name="uq_spend_treatment_program_labor"),
    )
    op.create_index("ix_prog_spend_treatment_prog_id", "program_spend_treatments", ["program_id"])

    # ------------------------------------------------------------------
    # Phase D — historical_production_benchmarks
    # ------------------------------------------------------------------
    op.create_table(
        "historical_production_benchmarks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("production_type", sa.String(50), nullable=False),
        sa.Column("release_year", sa.Integer, nullable=True),
        sa.Column("principal_jurisdiction_code", sa.String(20), nullable=False, index=True),
        sa.Column("total_budget_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("qualifying_spend_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("incentive_received_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("effective_rate_achieved", sa.Numeric(7, 6), nullable=True),
        sa.Column("la_equivalent_budget_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("data_source", sa.String(512), nullable=False),
        sa.Column("data_source_url", sa.String(2048), nullable=True),
        sa.Column("is_anonymised", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("confidence_tier", sa.String(20), nullable=False, server_default="DISCOVERY"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # ------------------------------------------------------------------
    # Phase D — benchmark_spend_items
    # ------------------------------------------------------------------
    op.create_table(
        "benchmark_spend_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("benchmark_id", UUID(as_uuid=True),
                  sa.ForeignKey("historical_production_benchmarks.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("amount_local", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency_code", sa.String(3), nullable=True),
        sa.Column("amount_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("pct_of_total_budget", sa.Numeric(7, 6), nullable=True),
        sa.Column("la_equivalent_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("derived_multiplier", sa.Numeric(7, 4), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # ------------------------------------------------------------------
    # Phase D — benchmark_ingestion_logs
    # ------------------------------------------------------------------
    op.create_table(
        "benchmark_ingestion_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("jurisdiction_codes", sa.String(512), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="complete"),
        sa.Column("ingested_by", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("benchmark_ingestion_logs")
    op.drop_table("benchmark_spend_items")
    op.drop_table("historical_production_benchmarks")
    op.drop_index("ix_prog_spend_treatment_prog_id", table_name="program_spend_treatments")
    op.drop_table("program_spend_treatments")
    op.drop_table("program_admin_details")
