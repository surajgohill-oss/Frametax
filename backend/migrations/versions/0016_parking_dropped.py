"""Add parking_dropped column to poll_runs.

Part of Phase 1E-C: global parking filter.  Records how many listings
were silently discarded by is_parking_listing() during each poll so
operators can verify the filter is working post-deploy.

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Guard: only add if the column doesn't already exist (idempotent)
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'poll_runs' AND column_name = 'parking_dropped'
    """))
    if result.fetchone() is not None:
        return  # already present — nothing to do

    conn.execute(text("""
        ALTER TABLE poll_runs
        ADD COLUMN parking_dropped INTEGER NOT NULL DEFAULT 0
    """))


def downgrade() -> None:
    op.drop_column("poll_runs", "parking_dropped")
