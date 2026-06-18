"""Add event_outcomes and artist_market_profiles tables.

Revision ID: 0024
Revises: 0023
Create Date: 2026-06-18

event_outcomes: persisted post-event outcome metrics computed from
listing_snapshots anchored to event_date. One row per event per compute run.

artist_market_profiles: aggregated profile across completed events for one
artist. Recomputed when any constituent event_outcome changes.
"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS event_outcomes (
            id                          SERIAL PRIMARY KEY,
            event_id                    INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,

            -- Phase 1: Clearance
            total_listings_seen         INTEGER,
            total_tickets_seen          INTEGER,
            listings_at_event_start     INTEGER,
            tickets_at_event_start      INTEGER,
            listings_1h_post            INTEGER,
            tickets_1h_post             INTEGER,
            listings_6h_post            INTEGER,
            tickets_6h_post             INTEGER,
            listings_24h_post           INTEGER,
            tickets_24h_post            INTEGER,
            event_start_clearance_rate  NUMERIC(6,4),
            postshow_clearance_rate     NUMERIC(6,4),
            remaining_inventory_rate    NUMERIC(6,4),

            -- Phase 2: Relist
            total_disappeared           INTEGER,
            total_relisted              INTEGER,
            relist_percentage           NUMERIC(6,4),
            relisted_then_disappeared   INTEGER,
            sold_after_relist_pct       NUMERIC(6,4),
            avg_relist_markup_pct       NUMERIC(8,2),
            avg_relist_discount_pct     NUMERIC(8,2),
            relist_success_rate         NUMERIC(6,4),
            relist_delay_p50_hours      NUMERIC(8,2),

            -- Phase 3: Seller pressure
            price_cuts_count            INTEGER,
            price_increases_count       INTEGER,
            median_price_cut_pct        NUMERIC(8,2),
            median_price_increase_pct   NUMERIC(8,2),
            repricing_frequency         NUMERIC(8,4),
            seller_pressure_score       NUMERIC(6,4),
            seller_strength_score       NUMERIC(6,4),

            -- Phase 4: Section absorption (JSON arrays)
            top_absorbed_sections       JSONB,
            worst_absorbed_sections     JSONB,

            -- Meta
            data_coverage_hours         NUMERIC(8,2),
            has_postshow_data           BOOLEAN DEFAULT false,
            marketplaces_tracked        INTEGER DEFAULT 0,
            computed_at                 TIMESTAMP NOT NULL DEFAULT NOW(),

            UNIQUE (event_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_event_outcomes_event_id
        ON event_outcomes (event_id)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS artist_market_profiles (
            id                          SERIAL PRIMARY KEY,
            artist                      VARCHAR(255) NOT NULL UNIQUE,
            event_count                 INTEGER NOT NULL DEFAULT 0,
            completed_event_ids         JSONB,

            -- Aggregated clearance
            avg_clearance_rate          NUMERIC(6,4),
            min_clearance_rate          NUMERIC(6,4),
            max_clearance_rate          NUMERIC(6,4),
            avg_inventory_remaining     NUMERIC(6,4),

            -- Aggregated relist
            avg_relist_pct              NUMERIC(6,4),
            avg_sold_after_relist_pct   NUMERIC(6,4),
            avg_relist_markup_pct       NUMERIC(8,2),
            avg_relist_discount_pct     NUMERIC(8,2),

            -- Aggregated seller
            avg_seller_pressure         NUMERIC(6,4),
            avg_seller_strength         NUMERIC(6,4),
            avg_repricing_frequency     NUMERIC(8,4),
            avg_price_cut_pct           NUMERIC(8,2),

            -- Evidence metrics (Phase 6)
            market_clearance_signal     VARCHAR(20),
            seller_pressure_signal      VARCHAR(20),
            relist_activity_signal      VARCHAR(20),

            computed_at                 TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS artist_market_profiles")
    op.execute("DROP TABLE IF EXISTS event_outcomes")
