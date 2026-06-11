"""
canonical_persistence.py — Phase 3B

Persists canonical inventory snapshots and maintains the block lifecycle table.
Called once per poll run after listings are committed.

Public API
----------
persist_canonical_snapshot(event_id, db, poll_run_id=None)
    → CanonicalInventorySnapshot (committed to DB)
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.canonical import (
    CanonicalInventorySnapshot,
    CanonicalBlockHistory,
    CanonicalBlockLifecycle,
)
from app.services.canonical_inventory import get_canonical_inventory, CanonicalBlock

log = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────────────────

def _decimal(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal("0")


def _unique_slugs(existing: Optional[list], new_slugs: list[str]) -> list[str]:
    """Merge marketplace slug lists, preserving insertion order, no duplicates."""
    seen = set(existing or [])
    result = list(existing or [])
    for slug in new_slugs:
        if slug not in seen:
            seen.add(slug)
            result.append(slug)
    return result


# ── snapshot writer ───────────────────────────────────────────────────────────

async def persist_canonical_snapshot(
    event_id: int,
    db: AsyncSession,
    poll_run_id: Optional[int] = None,
) -> Optional[CanonicalInventorySnapshot]:
    """
    1. Compute canonical view for the event.
    2. Write a CanonicalInventorySnapshot row (event-level summary).
    3. Write CanonicalBlockHistory rows (one per block in this snapshot).
    4. Upsert CanonicalBlockLifecycle rows (lifecycle table — one row per block ever seen).

    Returns the snapshot ORM object, or None if no canonical data.
    """
    try:
        view = await get_canonical_inventory(event_id, db)
    except Exception as exc:
        log.error("canonical_persistence: failed to compute canonical view for event %s: %s", event_id, exc)
        return None

    if not view.canonical_blocks:
        log.debug("canonical_persistence: no canonical blocks for event %s — skipping snapshot", event_id)
        return None

    now = datetime.utcnow()

    # ── 1. snapshot row ───────────────────────────────────────────────────────
    snap = CanonicalInventorySnapshot(
        event_id=event_id,
        snapshot_at=now,
        triggered_by_poll_run_id=poll_run_id,
        total_canonical_blocks=view.total_canonical_blocks,
        total_raw_listings=view.total_raw_listings,
        global_duplicate_ratio=_decimal(view.global_duplicate_ratio),
        mirrored_block_count=view.mirrored_block_count,
        mirrored_ratio=_decimal(view.mirrored_ratio),
        mean_confidence=_decimal(view.mean_confidence),
        high_confidence_blocks=view.high_confidence_blocks,
        low_confidence_blocks=view.low_confidence_blocks,
        low_ask=_decimal(min(b.low_ask for b in view.canonical_blocks)) if view.canonical_blocks else None,
        by_marketplace=view.by_marketplace,
        exact_seat_blocks=view.exact_seat_blocks,
        inferred_seat_blocks=view.inferred_seat_blocks,
        exact_seat_mirrored=view.exact_seat_mirrored,
    )
    db.add(snap)
    await db.flush()  # get snap.id

    # ── 2. block history rows ─────────────────────────────────────────────────
    history_rows = []
    for b in view.canonical_blocks:
        history_rows.append(CanonicalBlockHistory(
            event_id=event_id,
            snapshot_id=snap.id,
            block_id=b.block_id,
            section_id=b.section_id,
            row=b.row,
            quantity=b.quantity,
            low_ask=_decimal(b.low_ask),
            high_ask=_decimal(b.high_ask),
            median_ask=_decimal(b.median_ask),
            seller_count=b.seller_count,
            marketplace_slugs=b.marketplace_slugs,
            confidence_score=_decimal(b.confidence_score),
            confidence_v2=(b.confidence_version == "v2"),
            is_mirrored=b.is_mirrored,
            has_exact_seats=b.has_exact_seats,
            freshness_label=b.freshness_label,
        ))
    if history_rows:
        db.add_all(history_rows)

    # ── 3. lifecycle upsert ───────────────────────────────────────────────────
    await _upsert_lifecycle(event_id, view.canonical_blocks, now, db)

    await db.commit()
    log.info(
        "canonical_persistence: event=%s snap_id=%s blocks=%s exact=%s mirrored=%s",
        event_id, snap.id, view.total_canonical_blocks,
        view.exact_seat_blocks, view.mirrored_block_count,
    )
    return snap


async def _upsert_lifecycle(
    event_id: int,
    blocks: list[CanonicalBlock],
    now: datetime,
    db: AsyncSession,
) -> None:
    """
    PostgreSQL upsert into canonical_block_lifecycle.
    • New block  → INSERT with first_seen_at = last_seen_at = now, disappeared_at = NULL
    • Seen again → UPDATE last_seen_at, current_* fields, price evolution, marketplace_ever
                   If disappeared_at was set (block had vanished) → clear it, bump reappeared_count
    • Missing from this snapshot → mark disappeared_at = now (handled by separate pass below)
    """
    if not blocks:
        return

    # Build upsert values
    values = []
    for b in blocks:
        slugs = b.marketplace_slugs or []
        values.append({
            "event_id":            event_id,
            "block_id":            b.block_id,
            "section_id":          b.section_id,
            "row":                 b.row,
            "quantity":            b.quantity,
            "seat_identity":       b.seat_identity,
            "has_exact_seats":     b.has_exact_seats,
            "first_seen_at":       now,          # only used on INSERT
            "last_seen_at":        now,
            "disappeared_at":      None,
            "reappeared_count":    0,
            "snapshot_count":      1,
            "initial_low_ask":     float(b.low_ask),   # only used on INSERT
            "current_low_ask":     float(b.low_ask),
            "min_low_ask":         float(b.low_ask),
            "max_low_ask":         float(b.low_ask),
            "marketplace_ever":    slugs,
            "current_confidence":  float(b.confidence_score),
            "current_is_mirrored": b.is_mirrored,
            "current_seller_count": b.seller_count,
        })

    # PostgreSQL INSERT … ON CONFLICT DO UPDATE
    # Chunk into batches of 1500 rows (1500 × ~20 params = 30000 < PG limit of 32767)
    _LIFECYCLE_BATCH = 1500
    for chunk_start in range(0, len(values), _LIFECYCLE_BATCH):
        chunk = values[chunk_start: chunk_start + _LIFECYCLE_BATCH]
        stmt = pg_insert(CanonicalBlockLifecycle.__table__).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_lifecycle_event_block",
            set_={
                # Always update current state
                "last_seen_at":         stmt.excluded.last_seen_at,
                "current_low_ask":      stmt.excluded.current_low_ask,
                "current_confidence":   stmt.excluded.current_confidence,
                "current_is_mirrored":  stmt.excluded.current_is_mirrored,
                "current_seller_count": stmt.excluded.current_seller_count,
                "section_id":           stmt.excluded.section_id,
                "row":                  stmt.excluded.row,
                "seat_identity":        stmt.excluded.seat_identity,
                "has_exact_seats":      stmt.excluded.has_exact_seats,
                # Increment snapshot count
                "snapshot_count": CanonicalBlockLifecycle.__table__.c.snapshot_count + 1,
                # Price evolution — track min/max via LEAST/GREATEST
                "min_low_ask": func.least(
                    CanonicalBlockLifecycle.__table__.c.min_low_ask,
                    stmt.excluded.min_low_ask,
                ),
                "max_low_ask": func.greatest(
                    CanonicalBlockLifecycle.__table__.c.max_low_ask,
                    stmt.excluded.max_low_ask,
                ),
                # Marketplace exposure — union of all slugs ever seen
                "marketplace_ever": text(
                    "(SELECT jsonb_agg(DISTINCT val) "
                    "FROM jsonb_array_elements_text("
                    "COALESCE(canonical_block_lifecycle.marketplace_ever, '[]'::jsonb) || "
                    "COALESCE(EXCLUDED.marketplace_ever, '[]'::jsonb)) AS t(val))"
                ),
                # Reappearance detection: if disappeared_at was set, increment counter and clear it
                "reappeared_count": text(
                    "CASE WHEN canonical_block_lifecycle.disappeared_at IS NOT NULL "
                    "THEN canonical_block_lifecycle.reappeared_count + 1 "
                    "ELSE canonical_block_lifecycle.reappeared_count END"
                ),
                "disappeared_at": None,   # clear on reappearance
            },
        )
        await db.execute(stmt)

    # ── mark blocks that vanished from this snapshot ──────────────────────────
    # asyncpg requires array syntax (= ANY($n)) rather than IN ($n) for tuple params
    present_block_ids = list({b.block_id for b in blocks})
    if present_block_ids:
        await db.execute(
            text("""
                UPDATE canonical_block_lifecycle
                   SET disappeared_at = :now
                 WHERE event_id       = :event_id
                   AND disappeared_at IS NULL
                   AND block_id       != ALL(:present_ids)
            """),
            {
                "now":         now,
                "event_id":    event_id,
                "present_ids": present_block_ids,
            },
        )
