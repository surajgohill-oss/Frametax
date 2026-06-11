"""Venue intelligence: section aliases + metrics tables.

Revision ID: 0021
Revises: 0020
Create Date: 2026-06-11

Replaces the per-marketplace JSON alias columns on venue_sections with a
normalised venue_section_aliases table.  Any marketplace can be wired in
by inserting alias rows — no schema changes required.

Also adds:
  - level / zone / side / future_map_key / is_premium columns on venue_sections
  - venue_section_metrics: computed per-section intelligence for each event
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Extend venue_sections with intelligence columns
    op.execute("""
        ALTER TABLE venue_sections
            ADD COLUMN IF NOT EXISTS level       VARCHAR(30),
            ADD COLUMN IF NOT EXISTS zone        VARCHAR(40),
            ADD COLUMN IF NOT EXISTS side        VARCHAR(20),
            ADD COLUMN IF NOT EXISTS future_map_key VARCHAR(80),
            ADD COLUMN IF NOT EXISTS is_premium  BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS row_count   SMALLINT,
            ADD COLUMN IF NOT EXISTS seat_count  SMALLINT
    """)

    # 2. venue_section_aliases — marketplace-agnostic alias registry
    #
    # NOTE: marketplace_id is nullable (NULL = universal alias applies to all marketplaces).
    # PostgreSQL treats NULL != NULL so a plain UNIQUE constraint would allow duplicate
    # universal aliases.  We use two partial unique indexes instead:
    #   - When marketplace_id IS NOT NULL: unique on (section, marketplace, alias)
    #   - When marketplace_id IS NULL:     unique on (section, alias)
    op.execute("""
        CREATE TABLE IF NOT EXISTS venue_section_aliases (
            id                  BIGSERIAL PRIMARY KEY,
            venue_section_id    INTEGER NOT NULL REFERENCES venue_sections(id) ON DELETE CASCADE,
            marketplace_id      INTEGER REFERENCES marketplaces(id) ON DELETE SET NULL,
            alias               VARCHAR(255) NOT NULL,
            alias_normalized    VARCHAR(255) NOT NULL,
            event_type          VARCHAR(20),
            created_at          TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_vsa_section
        ON venue_section_aliases (venue_section_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_vsa_mp_alias
        ON venue_section_aliases (marketplace_id, alias_normalized)
    """)
    # Partial unique indexes to handle NULL marketplace_id correctly
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vsa_section_mp_alias
        ON venue_section_aliases (venue_section_id, marketplace_id, alias_normalized)
        WHERE marketplace_id IS NOT NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vsa_section_universal_alias
        ON venue_section_aliases (venue_section_id, alias_normalized)
        WHERE marketplace_id IS NULL
    """)

    # 3. venue_section_metrics — per-event intelligence rolled up per canonical section
    op.execute("""
        CREATE TABLE IF NOT EXISTS venue_section_metrics (
            id                      BIGSERIAL PRIMARY KEY,
            venue_section_id        INTEGER NOT NULL REFERENCES venue_sections(id) ON DELETE CASCADE,
            event_id                INTEGER NOT NULL,
            computed_at             TIMESTAMP NOT NULL,
            low_ask                 NUMERIC(10,2),
            median_ask              NUMERIC(10,2),
            high_ask                NUMERIC(10,2),
            p25_ask                 NUMERIC(10,2),
            p75_ask                 NUMERIC(10,2),
            inventory               INTEGER,
            listing_count           INTEGER,
            ticket_count            INTEGER,
            inventory_delta_24h     INTEGER,
            price_delta_24h         NUMERIC(10,2),
            price_delta_pct_24h     NUMERIC(6,2),
            deal_score              SMALLINT,
            demand_score            SMALLINT,
            seller_pressure         SMALLINT,
            value_score             SMALLINT,
            price_vs_tier_median    NUMERIC(6,2),
            price_vs_venue_median   NUMERIC(6,2),
            UNIQUE (venue_section_id, event_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_vsm_event
        ON venue_section_metrics (event_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_vsm_section_event
        ON venue_section_metrics (venue_section_id, event_id)
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS venue_section_metrics")
    op.execute("DROP TABLE IF EXISTS venue_section_aliases")
    op.execute("""
        ALTER TABLE venue_sections
            DROP COLUMN IF EXISTS level,
            DROP COLUMN IF EXISTS zone,
            DROP COLUMN IF EXISTS side,
            DROP COLUMN IF EXISTS future_map_key,
            DROP COLUMN IF EXISTS is_premium,
            DROP COLUMN IF EXISTS row_count,
            DROP COLUMN IF EXISTS seat_count
    """)
