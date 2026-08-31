"""Canonical Ingestion/Analysis Propagation: budget_documents.parser_version

Budget parsing/classification had no version marker at all — unlike
screenplay parsing (screenplay_structural_parser.PARSER_VERSION),
material_routing._route_budget's idempotency guard could only ever check
"does a BudgetDocument already exist for this DocumentVersion", never
"was it parsed under the CURRENT parser logic". A real budget-parser fix
(e.g. the netting-line exclusion regex) had no way to mark an
already-routed project's BudgetDocument stale for backfill.

Additive, nullable — existing rows get NULL (a real, honest "parsed
before this column existed" state, never backfilled with a guessed
version) and are treated as stale by the updated guard, which is correct:
they predate this version marker and have never been confirmed current
under it.

Revision ID: 0070
Revises: 0069
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0070"
down_revision: Union[str, None] = "0069"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("budget_documents", sa.Column("parser_version", sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column("budget_documents", "parser_version")
