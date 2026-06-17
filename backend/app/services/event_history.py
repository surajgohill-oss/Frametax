"""
event_history.py — Shared history accessor for all analytics/intelligence endpoints.

Merges two history sources for any event:
  1. event_price_history_agg — pre-import aggregated buckets (railway_event_id = events.id)
  2. listing_snapshots       — live per-listing snapshots from the scheduler

Call `get_event_history(event_id, db)` to get depth metadata.
Call `get_event_price_series(event_id, db, ...)` to get a merged price series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


@dataclass
class EventHistoryDepth:
    event_id: int
    # Live listing_snapshots
    snap_oldest: Optional[datetime]
    snap_newest: Optional[datetime]
    snap_count: int
    # Aggregated pre-import history
    agg_oldest: Optional[datetime]
    agg_newest: Optional[datetime]
    agg_count: int
    # Combined
    combined_oldest: Optional[datetime]
    combined_newest: Optional[datetime]
    combined_hours: float
    combined_days: float
    source: str  # "live" | "archive_aggregate" | "combined" | "none"


async def get_event_history_depth(
    event_id: int,
    db: AsyncSession,
    agg_bucket_size: str = "1h",
) -> EventHistoryDepth:
    """
    Returns the combined history depth for an event across both data sources.

    agg_bucket_size: which bucket granularity to query from event_price_history_agg.
    Default "1h" gives the finest resolution.
    """
    snap_row = (await db.execute(text("""
        SELECT MIN(snapshot_at), MAX(snapshot_at), COUNT(*)
        FROM listing_snapshots
        WHERE event_id = :eid
    """), {"eid": event_id})).fetchone()

    snap_oldest = snap_row[0] if snap_row else None
    snap_newest = snap_row[1] if snap_row else None
    snap_count = int(snap_row[2] or 0) if snap_row else 0

    agg_row = (await db.execute(text("""
        SELECT MIN(bucket_ts), MAX(bucket_ts), COUNT(*)
        FROM event_price_history_agg
        WHERE railway_event_id = :eid
          AND bucket_size = :bkt
    """), {"eid": event_id, "bkt": agg_bucket_size})).fetchone()

    agg_oldest = agg_row[0] if agg_row and agg_row[0] else None
    agg_newest = agg_row[1] if agg_row and agg_row[1] else None
    agg_count = int(agg_row[2] or 0) if agg_row else 0

    candidates_oldest = [x for x in [snap_oldest, agg_oldest] if x is not None]
    candidates_newest = [x for x in [snap_newest, agg_newest] if x is not None]
    combined_oldest = min(candidates_oldest) if candidates_oldest else None
    combined_newest = max(candidates_newest) if candidates_newest else None

    combined_hours = 0.0
    combined_days = 0.0
    if combined_oldest and combined_newest:
        combined_hours = (combined_newest - combined_oldest).total_seconds() / 3600
        combined_days = combined_hours / 24

    has_live = snap_oldest is not None
    has_archive = agg_oldest is not None and agg_count > 0
    if has_live and has_archive:
        source = "combined"
    elif has_archive:
        source = "archive_aggregate"
    elif has_live:
        source = "live"
    else:
        source = "none"

    return EventHistoryDepth(
        event_id=event_id,
        snap_oldest=snap_oldest,
        snap_newest=snap_newest,
        snap_count=snap_count,
        agg_oldest=agg_oldest,
        agg_newest=agg_newest,
        agg_count=agg_count,
        combined_oldest=combined_oldest,
        combined_newest=combined_newest,
        combined_hours=round(combined_hours, 1),
        combined_days=round(combined_days, 1),
        source=source,
    )
