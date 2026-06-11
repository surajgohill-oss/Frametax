"""Add historical aggregate tables for archive bridge.

Revision ID: 0020
Revises: 0019
Create Date: 2026-06-11

Three compact tables store pre-aggregated historical data sourced from the
local archive Postgres. Only aggregate rows are stored here — raw snapshots
stay local. The intelligence /history endpoint queries these tables alongside
live listing_snapshots and merges them transparently.
"""
from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Price history aggregates (1h / 6h / 12h / 1d buckets)
    op.execute("""
        CREATE TABLE IF NOT EXISTS event_price_history_agg (
            id                BIGSERIAL PRIMARY KEY,
            railway_event_id  INTEGER NOT NULL,
            bucket_ts         TIMESTAMP NOT NULL,
            bucket_size       VARCHAR(4) NOT NULL,
            low_ask           NUMERIC(12,2),
            median_ask        NUMERIC(12,2),
            high_ask          NUMERIC(12,2),
            p25_ask           NUMERIC(12,2),
            p75_ask           NUMERIC(12,2),
            listing_count     INTEGER,
            ticket_count      INTEGER,
            marketplace_count SMALLINT,
            UNIQUE (railway_event_id, bucket_ts, bucket_size)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_hist_agg_event_bucket
        ON event_price_history_agg (railway_event_id, bucket_ts)
    """)

    # 2. Marketplace history aggregates (6h buckets)
    op.execute("""
        CREATE TABLE IF NOT EXISTS event_marketplace_history_agg (
            id                BIGSERIAL PRIMARY KEY,
            railway_event_id  INTEGER NOT NULL,
            marketplace_id    SMALLINT NOT NULL,
            bucket_ts         TIMESTAMP NOT NULL,
            bucket_size       VARCHAR(4) NOT NULL,
            low_ask           NUMERIC(12,2),
            median_ask        NUMERIC(12,2),
            high_ask          NUMERIC(12,2),
            p25_ask           NUMERIC(12,2),
            p75_ask           NUMERIC(12,2),
            listing_count     INTEGER,
            ticket_count      INTEGER,
            UNIQUE (railway_event_id, marketplace_id, bucket_ts, bucket_size)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_mp_hist_agg_event_bucket
        ON event_marketplace_history_agg (railway_event_id, bucket_ts)
    """)

    # 3. Section history aggregates (6h and 1d buckets)
    op.execute("""
        CREATE TABLE IF NOT EXISTS event_section_history_agg (
            id                BIGSERIAL PRIMARY KEY,
            railway_event_id  INTEGER NOT NULL,
            section_id        VARCHAR(64) NOT NULL,
            bucket_ts         TIMESTAMP NOT NULL,
            bucket_size       VARCHAR(4) NOT NULL,
            low_ask           NUMERIC(12,2),
            median_ask        NUMERIC(12,2),
            high_ask          NUMERIC(12,2),
            listing_count     INTEGER,
            ticket_count      INTEGER,
            UNIQUE (railway_event_id, section_id, bucket_ts, bucket_size)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sec_hist_agg_event_bucket
        ON event_section_history_agg (railway_event_id, bucket_ts)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sec_hist_agg_event_section
        ON event_section_history_agg (railway_event_id, section_id)
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS event_section_history_agg")
    op.execute("DROP TABLE IF EXISTS event_marketplace_history_agg")
    op.execute("DROP TABLE IF EXISTS event_price_history_agg")
