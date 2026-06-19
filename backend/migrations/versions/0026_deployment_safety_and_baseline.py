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

    # Backfill first_snapshot_at (simple MIN per event)
    op.execute("""
        UPDATE events e
        SET first_snapshot_at = sub.first_snap
        FROM (
            SELECT event_id, MIN(snapshot_at) AS first_snap
            FROM listing_snapshots
            GROUP BY event_id
        ) sub
        WHERE e.id = sub.event_id
          AND e.first_snapshot_at IS NULL
    """)

    # Backfill starting_inventory: count listings at the first snapshot time
    op.execute("""
        UPDATE events e
        SET starting_inventory = sub.cnt
        FROM (
            SELECT ls.event_id, COUNT(DISTINCT ls.listing_id) AS cnt
            FROM listing_snapshots ls
            INNER JOIN (
                SELECT event_id, MIN(snapshot_at) AS first_snap
                FROM listing_snapshots
                GROUP BY event_id
            ) fs ON fs.event_id = ls.event_id
               AND ls.snapshot_at = fs.first_snap
            GROUP BY ls.event_id
        ) sub
        WHERE e.id = sub.event_id
          AND e.starting_inventory IS NULL
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS scheduler_heartbeats")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS starting_inventory")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS first_snapshot_at")
