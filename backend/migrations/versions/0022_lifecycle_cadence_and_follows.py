"""Lifecycle exhaustion tracking and user_follows table.

Revision ID: 0022
Revises: 0021
Create Date: 2026-06-17

Changes:
  1. tracked_events.consecutive_zero_inventory_count  — INT NOT NULL DEFAULT 0
     Counts consecutive successful-but-empty polls after event_start.
     Reset to 0 when a poll returns > 0 listings.
     Only incremented post-event-start (never for pre-event zero inventory).
     Event completes when this reaches 5 across all active tracked_events.

  2. user_follows table  — persistent follow registry
     Replaces localStorage["awr_follows"].
     scope_anchor is stored as NOW at follow time (not event-relative).
"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add exhaustion counter to tracked_events
    op.execute("""
        ALTER TABLE tracked_events
            ADD COLUMN IF NOT EXISTS consecutive_zero_inventory_count INTEGER NOT NULL DEFAULT 0
    """)

    # 2. Create user_follows (acquisition registry)
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_follows (
            id              SERIAL PRIMARY KEY,
            entity_type     VARCHAR(20)   NOT NULL,   -- 'artist' | 'team'
            entity_key      VARCHAR(255)  NOT NULL,   -- normalized key (lowercase display_name)
            display_name    VARCHAR(500)  NOT NULL,
            scope_type      VARCHAR(20)   NOT NULL,   -- 'next3'|'next5'|'next10'|'all_future'
            scope_anchor    TIMESTAMPTZ   NOT NULL,   -- datetime of follow (NOW)
            status          VARCHAR(20)   NOT NULL DEFAULT 'active',
            created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_user_follows_entity UNIQUE (entity_type, entity_key)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_follows_status
            ON user_follows (status)
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS user_follows")
    op.execute("""
        ALTER TABLE tracked_events
            DROP COLUMN IF EXISTS consecutive_zero_inventory_count
    """)
