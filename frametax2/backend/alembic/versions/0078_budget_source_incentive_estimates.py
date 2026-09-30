"""Budget documents: capture the producer's own stated incentive/rebate estimate line

budget_parser.py's _register() rebate-exclusion guard correctly keeps a source
budget's own "EDB Rebate at 35%" / "Greek Estimate Cash Rebate (40%)" style line out
of spend/QPE totals, but historically discarded the value entirely once excluded --
confirmed live on both Little Utopia ($1,275,411 @ 35%) and F#K Valentine's Day
($518,804 @ 40%), where the production's own stated estimate was invisible
everywhere downstream. BUDGET_PARSER_VERSION bumped to budget-1.4.0 alongside this
column so every existing BudgetDocument is reparsed and this column backfilled via
the existing parser_version staleness check in material_routing._route_budget --
no separate manual repair script required.

Revision ID: 0078
Revises: 0077
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0078"
down_revision: Union[str, None] = "0077"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "budget_documents",
        sa.Column("source_incentive_estimates", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("budget_documents", "source_incentive_estimates")
