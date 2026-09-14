"""Codex final four-row remediation (P0-NL-001): incentive_award_ledger_entries

Adds the canonical, durable, append-only award ledger table — see
app/models/incentive_award_ledger.py's own module docstring for the full
rationale ("Do not read StructureCalculationResult or any candidate/
scenario output as a prior award"). New table, no existing table altered.

production_company_identifier / award_period_year / program_slug are the
exact (company, period, program) triple canonical_evaluation.py's
company/period cap conservation queries; native_amount/native_currency
carry the real, native-currency award figure; status/evidence_state/
evidence_note carry the real-world decision and its provenance;
project_id is optional traceability only, never read by the cap query.

Revision ID: 0073
Revises: 0072
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0073"
down_revision: Union[str, None] = "0072"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incentive_award_ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("production_company_identifier", sa.String(length=255), nullable=False),
        sa.Column("award_period_year", sa.Integer(), nullable=False),
        sa.Column("program_slug", sa.String(length=255), nullable=False),
        sa.Column("native_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("native_currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("evidence_state", sa.String(length=20), nullable=False),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("recorded_by_note", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_incentive_award_ledger_entries_production_company_identifier",
        "incentive_award_ledger_entries", ["production_company_identifier"],
    )
    op.create_index(
        "ix_incentive_award_ledger_entries_award_period_year",
        "incentive_award_ledger_entries", ["award_period_year"],
    )
    op.create_index(
        "ix_incentive_award_ledger_entries_program_slug",
        "incentive_award_ledger_entries", ["program_slug"],
    )
    op.create_index(
        "ix_incentive_award_ledger_entries_project_id",
        "incentive_award_ledger_entries", ["project_id"],
    )
    op.create_index(
        "ix_award_ledger_company_period_program",
        "incentive_award_ledger_entries",
        ["production_company_identifier", "award_period_year", "program_slug"],
    )


def downgrade() -> None:
    op.drop_index("ix_award_ledger_company_period_program", table_name="incentive_award_ledger_entries")
    op.drop_index("ix_incentive_award_ledger_entries_project_id", table_name="incentive_award_ledger_entries")
    op.drop_index("ix_incentive_award_ledger_entries_program_slug", table_name="incentive_award_ledger_entries")
    op.drop_index("ix_incentive_award_ledger_entries_award_period_year", table_name="incentive_award_ledger_entries")
    op.drop_index(
        "ix_incentive_award_ledger_entries_production_company_identifier",
        table_name="incentive_award_ledger_entries",
    )
    op.drop_table("incentive_award_ledger_entries")
