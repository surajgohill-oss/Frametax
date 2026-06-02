"""Actually add market_segment column (0006 was skipped via 0013 no-op)

The 0013 no-op migration claimed the schema was already present, but
market_segment was never actually applied to production. This migration
adds it safely using IF NOT EXISTS.

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Add to listings if not exists
    conn.execute(text("""
        ALTER TABLE listings
        ADD COLUMN IF NOT EXISTS market_segment VARCHAR(20)
    """))
    # Add to listing_snapshots if not exists
    conn.execute(text("""
        ALTER TABLE listing_snapshots
        ADD COLUMN IF NOT EXISTS market_segment VARCHAR(20)
    """))


def downgrade() -> None:
    op.drop_column("listing_snapshots", "market_segment")
    op.drop_column("listings", "market_segment")
