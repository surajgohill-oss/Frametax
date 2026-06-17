"""
price_history_agg.py — Continuous writer for event_price_history_agg.

Reads from listing_snapshots and writes bucketed price statistics into
event_price_history_agg.  Called by the scheduler every hour.

Strategy:
  - For each active event, find the latest bucket_ts already in the agg table
    (or the earliest snapshot_at if no agg rows exist yet).
  - Compute 1h, 6h, 12h, and 1d buckets for completed windows only
    (i.e., buckets whose end time is at least 1 bucket_size ago, so we don't
    write a partial bucket that will never be updated).
  - Upsert with ON CONFLICT (railway_event_id, bucket_ts, bucket_size) DO NOTHING
    so pre-imported historical rows are never overwritten.

railway_event_id = events.id  (confirmed from data audit).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Bucket sizes to maintain: label → seconds
_BUCKETS: dict[str, int] = {
    "1h":  3600,
    "6h":  21600,
    "12h": 43200,
    "1d":  86400,
}


async def run_price_history_agg(session_factory) -> dict:
    """
    Aggregate listing_snapshots → event_price_history_agg for all active events.

    Returns summary: {events_processed, buckets_inserted, buckets_skipped, errors}
    """
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC
    totals = {"events_processed": 0, "buckets_inserted": 0, "buckets_skipped": 0, "errors": 0}

    async with session_factory() as db:
        # All active events that have at least one listing_snapshot
        events = (await db.execute(text("""
            SELECT DISTINCT e.id
            FROM events e
            JOIN listing_snapshots ls ON ls.event_id = e.id
            WHERE e.status IN ('upcoming', 'completed')
        """))).fetchall()

    for (event_id,) in events:
        try:
            inserted, skipped = await _aggregate_event(event_id, now_utc, session_factory)
            totals["events_processed"] += 1
            totals["buckets_inserted"] += inserted
            totals["buckets_skipped"]  += skipped
        except Exception as exc:
            logger.warning("price_history_agg: event_id=%d error: %s", event_id, exc)
            totals["errors"] += 1

    logger.info(
        "price_history_agg: processed=%d inserted=%d skipped=%d errors=%d",
        totals["events_processed"], totals["buckets_inserted"],
        totals["buckets_skipped"], totals["errors"],
    )
    return totals


async def _aggregate_event(
    event_id: int,
    now_utc: datetime,
    session_factory,
) -> tuple[int, int]:
    """Aggregate one event across all bucket sizes. Returns (inserted, skipped)."""
    inserted = 0
    skipped = 0

    async with session_factory() as db:
        for bucket_label, bucket_secs in _BUCKETS.items():
            ins, skp = await _aggregate_event_bucket(
                db, event_id, bucket_label, bucket_secs, now_utc
            )
            inserted += ins
            skipped  += skp
        await db.commit()

    return inserted, skipped


async def _aggregate_event_bucket(
    db: AsyncSession,
    event_id: int,
    bucket_label: str,
    bucket_secs: int,
    now_utc: datetime,
) -> tuple[int, int]:
    """
    Compute and upsert agg rows for one (event, bucket_size) pair.
    Only writes completed buckets (bucket_end <= now_utc - bucket_secs).
    """
    # Find the start of the window to aggregate from:
    # Either the latest bucket_ts already written + 1 bucket, or the start
    # of the first snapshot bucket.
    latest_row = (await db.execute(text("""
        SELECT MAX(bucket_ts)
        FROM event_price_history_agg
        WHERE railway_event_id = :eid AND bucket_size = :bkt
    """), {"eid": event_id, "bkt": bucket_label})).scalar()

    if latest_row is not None:
        # Start from the next bucket after the last written one
        agg_from = latest_row + timedelta(seconds=bucket_secs)
    else:
        # No agg rows yet — start from the earliest snapshot floored to bucket
        earliest = (await db.execute(text("""
            SELECT MIN(snapshot_at) FROM listing_snapshots WHERE event_id = :eid
        """), {"eid": event_id})).scalar()
        if not earliest:
            return 0, 0
        agg_from = _floor_ts(earliest, bucket_secs)

    # Only write buckets that have fully completed (end time ≤ now - buffer)
    # Use 1 bucket_size as the completion buffer so we never write a partial bucket.
    cutoff = now_utc - timedelta(seconds=bucket_secs)
    if agg_from > cutoff:
        return 0, 0

    # Aggregate all completed buckets from agg_from to cutoff in one query
    agg_rows = (await db.execute(text(f"""
        SELECT
            to_timestamp(
                floor(extract(epoch from snapshot_at) / :bucket_secs) * :bucket_secs
            )::timestamp WITHOUT TIME ZONE                        AS bucket_ts,
            MIN(price)                                            AS low_ask,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)   AS median_ask,
            PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY price)   AS high_ask,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price)  AS p25_ask,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price)  AS p75_ask,
            COUNT(DISTINCT listing_id)                            AS listing_count,
            SUM(quantity)                                         AS ticket_count,
            COUNT(DISTINCT marketplace_id)                        AS marketplace_count
        FROM listing_snapshots
        WHERE event_id = :eid
          AND snapshot_at >= CAST(:agg_from AS timestamp)
          AND snapshot_at <  CAST(:cutoff   AS timestamp)
          AND price > 0
        GROUP BY bucket_ts
        ORDER BY bucket_ts ASC
    """), {
        "eid": event_id,
        "bucket_secs": bucket_secs,
        "agg_from": agg_from,
        "cutoff": cutoff,
    })).fetchall()

    inserted = 0
    skipped  = 0
    for row in agg_rows:
        result = await db.execute(text("""
            INSERT INTO event_price_history_agg
              (railway_event_id, bucket_ts, bucket_size,
               low_ask, median_ask, high_ask, p25_ask, p75_ask,
               listing_count, ticket_count, marketplace_count)
            VALUES
              (:eid, CAST(:bucket_ts AS timestamp), :bkt,
               :low_ask, :median_ask, :high_ask, :p25_ask, :p75_ask,
               :listing_count, :ticket_count, :marketplace_count)
            ON CONFLICT (railway_event_id, bucket_ts, bucket_size) DO NOTHING
        """), {
            "eid":               event_id,
            "bucket_ts":         row[0],
            "bkt":               bucket_label,
            "low_ask":           float(row[1]) if row[1] is not None else None,
            "median_ask":        float(row[2]) if row[2] is not None else None,
            "high_ask":          float(row[3]) if row[3] is not None else None,
            "p25_ask":           float(row[4]) if row[4] is not None else None,
            "p75_ask":           float(row[5]) if row[5] is not None else None,
            "listing_count":     int(row[6]) if row[6] is not None else None,
            "ticket_count":      int(row[7]) if row[7] is not None else None,
            "marketplace_count": int(row[8]) if row[8] is not None else None,
        })
        if result.rowcount and result.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    return inserted, skipped


def _floor_ts(ts: datetime, bucket_secs: int) -> datetime:
    """Floor a datetime to the nearest bucket boundary."""
    epoch = int(ts.timestamp())
    floored = (epoch // bucket_secs) * bucket_secs
    return datetime.utcfromtimestamp(floored)
