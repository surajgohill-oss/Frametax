"""Intelligence Phase 2 — event_type_benchmarks table.

Revision ID: 0025
Revises: 0024
Create Date: 2026-06-18
"""
from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS event_type_benchmarks (
            id                          SERIAL PRIMARY KEY,
            event_type                  VARCHAR(50) NOT NULL UNIQUE,
            event_count                 INTEGER NOT NULL DEFAULT 0,
            event_ids                   JSONB,

            avg_clearance_rate          NUMERIC(6,4),
            p25_clearance_rate          NUMERIC(6,4),
            p50_clearance_rate          NUMERIC(6,4),
            p75_clearance_rate          NUMERIC(6,4),

            avg_relist_pct              NUMERIC(6,4),
            p50_relist_pct              NUMERIC(6,4),

            avg_seller_pressure         NUMERIC(6,4),
            p50_seller_pressure         NUMERIC(6,4),

            avg_inventory_remaining     NUMERIC(6,4),
            p50_inventory_remaining     NUMERIC(6,4),

            computed_at                 TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS event_type_benchmarks")
