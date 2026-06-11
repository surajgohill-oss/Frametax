"""Fix extra columns in listings that exist in production but not in model.

The production DB has additional columns from a prior codebase. This migration
makes those columns nullable so INSERTs from the current codebase succeed.

The extra columns identified from 500 errors:
  - source_type: NOT NULL, no default → make nullable with default

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Get current columns in listings table
    result = conn.execute(text("""
        SELECT column_name, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'listings'
        ORDER BY ordinal_position
    """))
    columns = [(r[0], r[1], r[2]) for r in result]
    
    # Known model columns — anything NOT in this set came from the prior codebase
    known_model_cols = {
        'id', 'event_id', 'marketplace_id', 'external_listing_id',
        'section', 'section_id', 'row', 'quantity', 'price', 'fees',
        'all_in_price', 'listing_url', 'is_active', 'market_segment',
        'first_seen_at', 'last_seen_at', 'extra'
    }
    
    extra_not_null = []
    for col_name, is_nullable, col_default in columns:
        if col_name not in known_model_cols and is_nullable == 'NO' and col_default is None:
            extra_not_null.append(col_name)
    
    # Make each one nullable so our INSERTs don't fail
    for col_name in extra_not_null:
        conn.execute(text(f"ALTER TABLE listings ALTER COLUMN {col_name} DROP NOT NULL"))
    
    # Same for listing_snapshots
    result2 = conn.execute(text("""
        SELECT column_name, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'listing_snapshots'
        ORDER BY ordinal_position
    """))
    snap_known = {
        'id', 'listing_id', 'event_id', 'marketplace_id', 'section_id',
        'quantity', 'price', 'fees', 'all_in_price', 'market_segment', 'snapshot_at'
    }
    for col_name, is_nullable, col_default in result2:
        if col_name not in snap_known and is_nullable == 'NO' and col_default is None:
            conn.execute(text(f"ALTER TABLE listing_snapshots ALTER COLUMN {col_name} DROP NOT NULL"))


def downgrade() -> None:
    pass  # Not reversible — do not re-add NOT NULL constraints
