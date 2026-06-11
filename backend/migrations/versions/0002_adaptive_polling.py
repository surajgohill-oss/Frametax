"""adaptive polling + event lifecycle + schema fixes

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000

Fixes:
- listing_snapshots was missing fees + all_in_price (caused UndefinedColumnError
  whenever the scheduler wrote a snapshot after a real poll)
- events gets a status field for lifecycle tracking (upcoming/in_progress/completed)
- adds indexes that were defined in ORM models but absent from migration 0001
- adds UniqueConstraint on tracked_events(event_id, marketplace_id)
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Critical column fixes ──────────────────────────────────────────────
    op.add_column("listing_snapshots",
        sa.Column("fees", sa.Numeric(10, 2), nullable=True))
    op.add_column("listing_snapshots",
        sa.Column("all_in_price", sa.Numeric(10, 2), nullable=True))

    # ── Event lifecycle ────────────────────────────────────────────────────
    op.add_column("events",
        sa.Column("status", sa.String(20), server_default="upcoming", nullable=False))

    # ── Integrity constraint missing from 0001 ─────────────────────────────
    op.create_unique_constraint(
        "uq_tracked_event_marketplace", "tracked_events", ["event_id", "marketplace_id"])

    # ── Performance indexes (were in ORM __table_args__ but not migration) ─
    op.create_index("ix_listings_event_mp",    "listings",          ["event_id", "marketplace_id"])
    op.create_index("ix_listings_event_sec",   "listings",          ["event_id", "section_id"])
    op.create_index("ix_snap_event_ts",        "listing_snapshots", ["event_id", "snapshot_at"])
    op.create_index("ix_snap_event_mp_ts",     "listing_snapshots", ["event_id", "marketplace_id", "snapshot_at"])
    op.create_index("ix_events_status_date",   "events",            ["status", "event_date"])
    op.create_index("ix_tracked_active_poll",  "tracked_events",    ["is_active", "next_poll_at"])


def downgrade() -> None:
    op.drop_index("ix_tracked_active_poll")
    op.drop_index("ix_events_status_date")
    op.drop_index("ix_snap_event_mp_ts")
    op.drop_index("ix_snap_event_ts")
    op.drop_index("ix_listings_event_sec")
    op.drop_index("ix_listings_event_mp")
    op.drop_constraint("uq_tracked_event_marketplace", "tracked_events")
    op.drop_column("events", "status")
    op.drop_column("listing_snapshots", "all_in_price")
    op.drop_column("listing_snapshots", "fees")
