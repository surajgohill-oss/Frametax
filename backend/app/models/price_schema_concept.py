"""
PHASE 4 — ticket_price_snapshots: Conceptual Schema (NOT YET IMPLEMENTED)

This file defines the intended schema for the price intelligence time-series
table. It is NOT registered with SQLAlchemy Base, NOT included in Alembic
migrations, and NOT referenced by any router or service.

Activation requires:
  1. Add to app/models/__init__.py
  2. Generate Alembic migration
  3. Wire collector to write snapshots after each poll

Design decisions:
  - Append-only: no UPDATE or DELETE allowed at application layer
  - Source traceability: source_listing_id links back to listings.id
  - Derived column days_until_event is stored (not computed) to allow
    trend analysis across time even after the event has passed
  - marketplace stored as denormalized slug (not FK) to keep reads fast
    and to survive marketplace table changes without cascade impact
  - all_in_price stored alongside price so fee-inclusive comparisons
    can be made without rejoining listings

SQL DDL (PostgreSQL):

  CREATE TABLE ticket_price_snapshots (
      id                  BIGSERIAL PRIMARY KEY,
      event_id            INTEGER       NOT NULL REFERENCES events(id),
      marketplace         VARCHAR(50)   NOT NULL,
      price               NUMERIC(10,2) NOT NULL,
      all_in_price        NUMERIC(10,2),
      section             VARCHAR(100),
      section_id          VARCHAR(50),
      row                 VARCHAR(20),
      quantity            INTEGER       NOT NULL,
      snapshot_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
      days_until_event    NUMERIC(6,2)  NOT NULL,
      source_listing_id   INTEGER       REFERENCES listings(id)
  );

  CREATE INDEX ix_tps_event_ts   ON ticket_price_snapshots (event_id, snapshot_at);
  CREATE INDEX ix_tps_event_mp   ON ticket_price_snapshots (event_id, marketplace, snapshot_at);
  CREATE INDEX ix_tps_section    ON ticket_price_snapshots (event_id, section_id, snapshot_at);

Relationship to existing tables:
  listing_snapshots — already append-only; covers raw per-listing price history.
  ticket_price_snapshots — aggregated intelligence layer; adds days_until_event
    and denormalized marketplace for fast trend queries without joins.

Extension safety rules (STEP 4):
  1. NEVER issue UPDATE or DELETE against this table — only INSERT
  2. NEVER read from this table inside the ingestion pipeline (scheduler,
     collectors, resolver, discovery) — analytics reads must stay isolated
  3. NEVER write to events, tracked_events, listings, poll_runs, or
     listing_snapshots from the analytics layer — those tables are owned
     by the ingestion pipeline
  4. All time-series queries must use snapshot_at as the primary time axis,
     never event_date, to preserve correct ordering during ingestion lag
  5. Backfilling historical snapshots must happen via a standalone offline
     migration script — never inline inside a collector or scheduler job
  6. Any derived signals (demand_pressure, availability_score) must be
     computed at query time from raw snapshot data, never stored as mutable
     columns in the snapshots table itself
"""

# Intentionally no SQLAlchemy model class defined here.
# No Base registration. No import in __init__.py.
# This file is documentation only until Phase 4 activation.
