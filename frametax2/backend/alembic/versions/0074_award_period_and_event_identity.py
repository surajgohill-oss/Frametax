"""Codex final three-program conservation repair (P0-NL-001, fifth pass):
projects.award_period_year and incentive_award_ledger_entries.award_event_id

Adds the explicit Project.award_period_year column (never inferred from
target_shoot_year — a production-planning fact, not a real statement of the
statutory award period) and the ledger's award_event_id column (a stable
identity for one real award decision, letting the read-side collapse
status-transition rows for the SAME award to exactly one counted total).

Both new columns are nullable/backfillable-safe: incentive_award_ledger_entries
was empty in the real dev database at the time of this migration (confirmed
via direct row count before writing this migration), so award_event_id can be
added NOT NULL with no backfill required. If a future environment somehow has
existing rows, the NOT NULL add will fail loudly rather than silently
defaulting every existing row to the same event identity (which would
incorrectly collapse distinct real awards together).

Revision ID: 0074
Revises: 0073
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0074"
down_revision: Union[str, None] = "0073"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("award_period_year", sa.Integer(), nullable=True))
    op.create_index(
        "ix_projects_award_period_year", "projects", ["award_period_year"],
    )

    op.add_column(
        "incentive_award_ledger_entries",
        sa.Column("award_event_id", sa.String(length=255), nullable=False),
    )
    op.create_index(
        "ix_incentive_award_ledger_entries_award_event_id",
        "incentive_award_ledger_entries", ["award_event_id"],
    )
    op.create_index(
        "ix_award_ledger_event",
        "incentive_award_ledger_entries",
        ["production_company_identifier", "award_period_year", "program_slug", "award_event_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_award_ledger_event", table_name="incentive_award_ledger_entries")
    op.drop_index("ix_incentive_award_ledger_entries_award_event_id", table_name="incentive_award_ledger_entries")
    op.drop_column("incentive_award_ledger_entries", "award_event_id")

    op.drop_index("ix_projects_award_period_year", table_name="projects")
    op.drop_column("projects", "award_period_year")
