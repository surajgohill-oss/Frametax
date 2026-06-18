"""Deployment safety: scheduler_heartbeats, event starting_inventory baseline.

Revision ID: 0026
Revises: 0025
Create Date: 2026-06-18
"""
from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade():
    # Scheduler heartbeat persistence (T5E)
    op.execute("""
        CREATE TABLE IF NOT EXISTS scheduler_heartbeats (
            id         SERIAL PRIMARY KEY,
            beat_at    TIMESTAMP NOT NULL DEFAULT NOW(),
            hostname   VARCHAR(255),
            pid        INTEGER,
            jobs_ran   INTEGER DEFAULT 0
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_scheduler_heartbeats_beat_at
        ON scheduler_heartbeats (beat_at DESC)
    """)

    # Starting inventory baseline on events (T7)
    op.execute(
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS starting_inventory INTEGER"
    )
    op.execute(
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS first_snapshot_at TIMESTAMP"
    )

    # Backfill starting_inventory + first_snapshot_at for all existing events
    op.execute("""
        UPDATE events e
        SET
            first_snapshot_at = sub.first_snap,
            starting_inventory = sub.cnt
        FROM (
            SELECT
                ls.event_id,
                MIN(ls.snapshot_at)       AS first_snap,
                COUNT(DISTINCT ls2.listing_id) AS cnt
            FROM listing_snapshots ls
            JOIN listing_snapshots ls2
              ON ls2.event_id = ls.event_id
             AND ls2.snapshot_at = (
                    SELECT MIN(ls3.snapshot_at)
                    FROM listing_snapshots ls3
                    WHERE ls3.event_id = ls.event_id
                 )
            GROUP BY ls.event_id
        ) sub
        WHERE e.id = sub.event_id
          AND e.starting_inventory IS NULL
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS scheduler_heartbeats")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS starting_inventory")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS first_snapshot_at")
