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
    # Scheduler heartbeat persistence (T5E) — DDL only, no data writes
    op.execute(
        "CREATE TABLE IF NOT EXISTS scheduler_heartbeats ("
        "id SERIAL PRIMARY KEY, "
        "beat_at TIMESTAMP NOT NULL DEFAULT NOW(), "
        "hostname VARCHAR(255), "
        "pid INTEGER, "
        "jobs_ran INTEGER DEFAULT 0)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_scheduler_heartbeats_beat_at "
        "ON scheduler_heartbeats (beat_at DESC)"
    )

    # Starting inventory baseline on events (T7) — DDL only
    # Backfill is handled at startup in main.py._backfill_starting_inventory()
    op.execute(
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS starting_inventory INTEGER"
    )
    op.execute(
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS first_snapshot_at TIMESTAMP"
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS scheduler_heartbeats")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS starting_inventory")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS first_snapshot_at")
