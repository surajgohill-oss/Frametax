"""Phase 2: market intelligence cache table + price history indexes

Creates market_intelligence table for pre-computed per-event intelligence metrics.
Adds a covering index on listing_snapshots for fast price-history queries.

Schema:
  market_intelligence  – one row per (event_id, computed_at) snapshot of metrics
                         Scalar columns for key metrics; JSONB for sub-structures.
                         The compute endpoint populates this; read endpoints serve from it.

Revision ID: 0018
Revises: 0017
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_intelligence",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),

        # ── Current price tiers (all active listings) ─────────────────────────
        sa.Column("current_low_ask",    sa.Numeric(12, 2), nullable=True),
        sa.Column("current_median_ask", sa.Numeric(12, 2), nullable=True),
        sa.Column("current_high_ask",   sa.Numeric(12, 2), nullable=True),
        sa.Column("current_p10_ask",    sa.Numeric(12, 2), nullable=True),
        sa.Column("current_p25_ask",    sa.Numeric(12, 2), nullable=True),
        sa.Column("current_p75_ask",    sa.Numeric(12, 2), nullable=True),
        sa.Column("current_p90_ask",    sa.Numeric(12, 2), nullable=True),

        # ── Current inventory ─────────────────────────────────────────────────
        sa.Column("current_listings", sa.Integer(), nullable=True),
        sa.Column("current_tickets",  sa.Integer(), nullable=True),

        # ── Price deltas (median_now - median_then) ───────────────────────────
        sa.Column("price_delta_24h",     sa.Numeric(12, 2), nullable=True),
        sa.Column("price_delta_7d",      sa.Numeric(12, 2), nullable=True),
        sa.Column("price_delta_14d",     sa.Numeric(12, 2), nullable=True),
        sa.Column("price_delta_30d",     sa.Numeric(12, 2), nullable=True),
        sa.Column("price_delta_pct_24h", sa.Numeric(8, 4),  nullable=True),
        sa.Column("price_delta_pct_7d",  sa.Numeric(8, 4),  nullable=True),

        # ── Inventory deltas (listing count: now - then) ──────────────────────
        sa.Column("inventory_delta_24h", sa.Integer(), nullable=True),
        sa.Column("inventory_delta_7d",  sa.Integer(), nullable=True),
        sa.Column("inventory_delta_14d", sa.Integer(), nullable=True),
        sa.Column("inventory_delta_30d", sa.Integer(), nullable=True),

        # ── Resale-specific rates (0–1 floats) ────────────────────────────────
        sa.Column("reprice_rate",       sa.Numeric(6, 4), nullable=True),  # pct listings repriced in last 24h
        sa.Column("churn_rate",         sa.Numeric(6, 4), nullable=True),  # (new+disapp) / total per poll
        sa.Column("listing_survival",   sa.Numeric(6, 4), nullable=True),  # pct listings still active 24h later
        sa.Column("reappearance_rate",  sa.Numeric(6, 4), nullable=True),  # pct disappeared that reappeared
        sa.Column("relisting_rate",     sa.Numeric(6, 4), nullable=True),  # pct active that have been relisted

        # ── Market character scores (0–1) ─────────────────────────────────────
        sa.Column("market_tightness",     sa.Numeric(6, 4), nullable=True),  # low IQR + low listing count → tight
        sa.Column("market_depth",         sa.Numeric(6, 4), nullable=True),  # spread / median ratio
        sa.Column("inventory_velocity",   sa.Numeric(10, 4), nullable=True), # Δlistings / hour
        sa.Column("seller_aggression",    sa.Numeric(6, 4), nullable=True),  # pct price-changes that are drops
        sa.Column("seller_confidence",    sa.Numeric(6, 4), nullable=True),  # pct price-changes that are raises
        sa.Column("capitulation_score",   sa.Numeric(6, 4), nullable=True),  # high disappear + price drops
        sa.Column("relist_pressure",      sa.Numeric(6, 4), nullable=True),  # relisting + reappearance rate
        sa.Column("opportunity_score",    sa.Numeric(6, 4), nullable=True),  # composite buy-signal score

        # ── Normalized by days-until-event ───────────────────────────────────
        sa.Column("days_until_event", sa.Numeric(6, 2), nullable=True),

        # ── Sub-structure JSONB ───────────────────────────────────────────────
        # marketplace_metrics: list of {name, listings, tickets, low, median, high, share, liquidity_score}
        sa.Column("marketplace_metrics", JSONB(), nullable=True),
        # section_metrics: list of {section_id, display_name, listings, low, median, high, trend, activity_score}
        sa.Column("section_metrics", JSONB(), nullable=True),
        # seller_behavior: {new_24h, removed_24h, repriced_24h, price_increases_24h, price_decreases_24h,
        #                   median_reprice_delta, largest_drops_top5, largest_gains_top5}
        sa.Column("seller_behavior", JSONB(), nullable=True),
        # price_history: {buckets: [{ts, low, median, high, listings}]}  -- last 24h at 1h resolution
        sa.Column("price_history_24h", JSONB(), nullable=True),
        # window_histories: {h24:[], d7:[], d14:[], d30:[]} each with 1h/6h/1d buckets
        sa.Column("window_histories", JSONB(), nullable=True),

        # ── Metadata ─────────────────────────────────────────────────────────
        sa.Column("history_hours", sa.Numeric(6, 1), nullable=True),  # hours of snapshot history available
    )

    op.create_index(
        "ix_market_intelligence_event_computed",
        "market_intelligence",
        ["event_id", "computed_at"],
    )

    # Covering index on listing_snapshots for price-history queries
    # (event_id, snapshot_at, price) — covers the most common pattern
    op.create_index(
        "ix_listing_snapshots_event_time_price",
        "listing_snapshots",
        ["event_id", "snapshot_at", "price"],
    )


def downgrade() -> None:
    op.drop_index("ix_listing_snapshots_event_time_price", table_name="listing_snapshots")
    op.drop_index("ix_market_intelligence_event_computed", table_name="market_intelligence")
    op.drop_table("market_intelligence")
