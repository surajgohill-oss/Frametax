"""
Data-health layer — read-only diagnostics derived from existing tables.

Routes:
  GET /api/data-health/catalog
  GET /api/data-health/events/{event_id}
  GET /api/data-health/events/{event_id}/attribution
"""
from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Event, Listing, Marketplace
from app.models.canonical import CanonicalBlockLifecycle, CanonicalInventorySnapshot
from app.models.event import TrackedEvent
from app.models.listing import PollRun

router = APIRouter(prefix="/data-health", tags=["data-health"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coverage_status(
    *,
    poll_count: int,
    recent_error_count: int,  # last N poll runs that errored
    last_poll_age_min: Optional[float],
    poll_interval_min: int,
    active_listings: int,
    snapshot_count: int,
    last_snapshot_age_min: Optional[float],
) -> str:
    if poll_count == 0:
        return "COLLECTION_GAP"
    if recent_error_count >= 3:
        return "ENDPOINT_BROKEN"
    if active_listings == 0:
        return "CONTENT_GAP"
    if (
        last_poll_age_min is not None
        and last_poll_age_min <= poll_interval_min * 1.5
        and active_listings > 0
        and snapshot_count == 0
    ):
        return "POLLING_NOT_SNAPSHOTTING"
    if (
        last_poll_age_min is not None
        and last_poll_age_min <= poll_interval_min * 1.5
        and last_snapshot_age_min is not None
        and last_snapshot_age_min <= poll_interval_min * 2
        and active_listings > 0
    ):
        return "HEALTHY"
    return "COLLECTION_GAP"


def _age_minutes(dt: Optional[datetime]) -> Optional[float]:
    if dt is None:
        return None
    return (datetime.utcnow() - dt).total_seconds() / 60


# ---------------------------------------------------------------------------
# GET /api/data-health/catalog
# ---------------------------------------------------------------------------

@router.get("/catalog")
async def catalog_health(db: AsyncSession = Depends(get_db)):
    """
    Per-event × per-marketplace health summary for all tracked events.

    Returns a list of event objects, each containing a per_marketplace breakdown
    and an overall worst-case coverage_status.
    """
    now = datetime.utcnow()

    # Load all events
    events_q = await db.execute(select(Event).order_by(Event.event_date))
    all_events = events_q.scalars().all()

    # Load all tracked events joined to marketplace slugs
    te_q = await db.execute(
        select(TrackedEvent, Marketplace.slug)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(TrackedEvent.is_active == True)
    )
    te_rows = te_q.all()

    # Index: event_id → list[(TrackedEvent, slug)]
    te_by_event: dict[int, list] = {}
    for te, slug in te_rows:
        te_by_event.setdefault(te.event_id, []).append((te, slug))

    # Active listings: event_id × marketplace_id → count
    al_q = await db.execute(
        select(Listing.event_id, Listing.marketplace_id, func.count())
        .where(Listing.is_active == True)
        .group_by(Listing.event_id, Listing.marketplace_id)
    )
    active_listings: dict[tuple, int] = {(r[0], r[1]): r[2] for r in al_q}

    # Poll runs: tracked_event_id → (total, recent_errors, last_started_at)
    pr_q = await db.execute(
        select(PollRun.tracked_event_id, PollRun.status, PollRun.started_at)
        .order_by(PollRun.tracked_event_id, PollRun.started_at.desc())
    )
    pr_rows = pr_q.all()
    poll_stats: dict[int, dict] = {}
    for te_id, status, started_at in pr_rows:
        if te_id not in poll_stats:
            poll_stats[te_id] = {"total": 0, "errors": [], "last_at": None}
        d = poll_stats[te_id]
        d["total"] += 1
        if d["last_at"] is None:
            d["last_at"] = started_at
        if status == "error" and len(d["errors"]) < 5:
            d["errors"].append(started_at)

    # Recent canonical snapshots: event_id → most recent snapshot_at
    snap_q = await db.execute(
        select(
            CanonicalInventorySnapshot.event_id,
            func.max(CanonicalInventorySnapshot.snapshot_at),
        ).group_by(CanonicalInventorySnapshot.event_id)
    )
    last_snap: dict[int, datetime] = {r[0]: r[1] for r in snap_q}

    # Snapshot count per event
    snap_count_q = await db.execute(
        select(
            CanonicalInventorySnapshot.event_id,
            func.count(),
        ).group_by(CanonicalInventorySnapshot.event_id)
    )
    snap_count: dict[int, int] = {r[0]: r[1] for r in snap_count_q}

    results = []
    for ev in all_events:
        te_list = te_by_event.get(ev.id, [])
        mp_rows = []
        statuses = []

        for te, slug in te_list:
            al_count = active_listings.get((ev.id, te.marketplace_id), 0)
            ps = poll_stats.get(te.id, {"total": 0, "errors": [], "last_at": None})
            last_poll_age = _age_minutes(ps["last_at"])
            snap_age = _age_minutes(last_snap.get(ev.id))
            ev_snap_count = snap_count.get(ev.id, 0)

            # Count consecutive recent errors (last 3)
            recent_errors = len(ps["errors"][:3]) if ps["total"] > 0 else 0

            status = _coverage_status(
                poll_count=ps["total"],
                recent_error_count=recent_errors,
                last_poll_age_min=last_poll_age,
                poll_interval_min=te.poll_interval_minutes,
                active_listings=al_count,
                snapshot_count=ev_snap_count,
                last_snapshot_age_min=snap_age,
            )
            statuses.append(status)

            mp_rows.append({
                "marketplace": slug,
                "poll_count": ps["total"],
                "last_poll_age_minutes": round(last_poll_age, 1) if last_poll_age is not None else None,
                "poll_interval_minutes": te.poll_interval_minutes,
                "active_listings": al_count,
                "coverage_status": status,
            })

        # Overall event status: pick worst-case rank
        STATUS_RANK = {
            "ENDPOINT_BROKEN": 0,
            "COLLECTION_GAP": 1,
            "CONTENT_GAP": 2,
            "POLLING_NOT_SNAPSHOTTING": 3,
            "HEALTHY": 4,
        }
        overall = min(statuses, key=lambda s: STATUS_RANK.get(s, 99)) if statuses else "COLLECTION_GAP"

        results.append({
            "event_id": ev.id,
            "title": ev.title,
            "event_date": ev.event_date.isoformat(),
            "overall_status": overall,
            "last_snapshot_age_minutes": round(_age_minutes(last_snap.get(ev.id)), 1)
                if last_snap.get(ev.id) else None,
            "snapshot_count": snap_count.get(ev.id, 0),
            "per_marketplace": mp_rows,
        })

    return {"generated_at": now.isoformat(), "events": results}


# ---------------------------------------------------------------------------
# GET /api/data-health/events/{event_id}
# ---------------------------------------------------------------------------

@router.get("/events/{event_id}")
async def event_health(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deep health report for a single event.

    Includes: poll timeline per marketplace, canonical snapshot series,
    listing freshness breakdown, and staleness assessment.
    """
    now = datetime.utcnow()

    ev = await db.get(Event, event_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")

    # Tracked events for this event
    te_q = await db.execute(
        select(TrackedEvent, Marketplace.slug, Marketplace.id)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(TrackedEvent.event_id == event_id, TrackedEvent.is_active == True)
    )
    te_rows = te_q.all()

    # Recent poll runs per tracked_event (last 10 each)
    mp_detail = []
    for te, slug, mp_id in te_rows:
        pr_q = await db.execute(
            select(PollRun)
            .where(PollRun.tracked_event_id == te.id)
            .order_by(PollRun.started_at.desc())
            .limit(10)
        )
        polls = pr_q.scalars().all()

        # Active listing stats for this marketplace
        al_q = await db.execute(
            select(func.count(), func.min(Listing.price), func.sum(Listing.quantity))
            .where(
                Listing.event_id == event_id,
                Listing.marketplace_id == mp_id,
                Listing.is_active == True,
            )
        )
        al_count, al_min_price, al_qty = al_q.one()

        # Freshness: listings seen in last 2× poll interval
        fresh_cutoff = now - timedelta(minutes=te.poll_interval_minutes * 2)
        fresh_q = await db.execute(
            select(func.count())
            .where(
                Listing.event_id == event_id,
                Listing.marketplace_id == mp_id,
                Listing.is_active == True,
                Listing.last_seen_at >= fresh_cutoff,
            )
        )
        fresh_count = fresh_q.scalar_one()

        recent_errors = sum(1 for p in polls[:3] if p.status == "error")
        last_poll_age = _age_minutes(polls[0].started_at) if polls else None
        snap_q = await db.execute(
            select(func.count()).where(CanonicalInventorySnapshot.event_id == event_id)
        )
        snap_total = snap_q.scalar_one()
        last_snap_q = await db.execute(
            select(func.max(CanonicalInventorySnapshot.snapshot_at))
            .where(CanonicalInventorySnapshot.event_id == event_id)
        )
        last_snap_at = last_snap_q.scalar_one()

        status = _coverage_status(
            poll_count=len(polls),
            recent_error_count=recent_errors,
            last_poll_age_min=last_poll_age,
            poll_interval_min=te.poll_interval_minutes,
            active_listings=al_count or 0,
            snapshot_count=snap_total,
            last_snapshot_age_min=_age_minutes(last_snap_at),
        )

        mp_detail.append({
            "marketplace": slug,
            "coverage_status": status,
            "poll_interval_minutes": te.poll_interval_minutes,
            "last_polled_at": polls[0].started_at.isoformat() if polls else None,
            "last_poll_age_minutes": round(last_poll_age, 1) if last_poll_age is not None else None,
            "poll_count": len(polls),
            "recent_error_count": recent_errors,
            "active_listings": al_count or 0,
            "fresh_listings": fresh_count,
            "floor_price": float(al_min_price) if al_min_price else None,
            "total_quantity": int(al_qty) if al_qty else 0,
            "recent_polls": [
                {
                    "started_at": p.started_at.isoformat(),
                    "status": p.status,
                    "listings_found": p.listings_found,
                    "error": p.error_message,
                }
                for p in polls[:5]
            ],
        })

    # Canonical snapshot series (last 10)
    snaps_q = await db.execute(
        select(CanonicalInventorySnapshot)
        .where(CanonicalInventorySnapshot.event_id == event_id)
        .order_by(CanonicalInventorySnapshot.snapshot_at.desc())
        .limit(10)
    )
    snaps = snaps_q.scalars().all()

    snapshot_series = [
        {
            "id": s.id,
            "snapshot_at": s.snapshot_at.isoformat(),
            "age_minutes": round(_age_minutes(s.snapshot_at), 1),
            "total_blocks": s.total_canonical_blocks,
            "total_raw_listings": s.total_raw_listings,
            "low_ask": float(s.low_ask) if s.low_ask else None,
            "mirrored_blocks": s.mirrored_block_count,
            "mirrored_ratio": float(s.mirrored_ratio),
            "mean_confidence": float(s.mean_confidence),
            "by_marketplace": s.by_marketplace,
        }
        for s in snaps
    ]

    return {
        "event_id": event_id,
        "title": ev.title,
        "event_date": ev.event_date.isoformat(),
        "generated_at": now.isoformat(),
        "per_marketplace": mp_detail,
        "canonical_snapshots": snapshot_series,
    }


# ---------------------------------------------------------------------------
# GET /api/data-health/events/{event_id}/attribution
# ---------------------------------------------------------------------------

@router.get("/events/{event_id}/attribution")
async def event_attribution(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Heuristic movement attribution for canonical blocks of an event.

    Attribution labels and their epistemic status:
      new               – block first appeared recently            (observed)
      disappeared       – block was active, now gone               (observed)
      likely_sold       – disappeared AND price was at/below p50   (HEURISTIC/INFERRED)
      relisted          – new AND (section,row,qty) fingerprint
                         matches a recently disappeared block       (FINGERPRINT INFERENCE)
      price_changed     – active, price differs from initial ask    (observed)
      stable            – active, no notable movement               (observed)
      unknown_movement  – disappeared, insufficient signal          (observed movement, unknown cause)

    Confidence is noted explicitly in the response; do not treat likely_sold or
    relisted as confirmed facts.
    """
    ev = await db.get(Event, event_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get all lifecycle rows for this event
    lc_q = await db.execute(
        select(CanonicalBlockLifecycle)
        .where(CanonicalBlockLifecycle.event_id == event_id)
    )
    blocks: list[CanonicalBlockLifecycle] = lc_q.scalars().all()

    if not blocks:
        return {
            "event_id": event_id,
            "title": ev.title,
            "attribution_note": (
                "Attribution is heuristic and inferred from inventory movement patterns. "
                "likely_sold is not a confirmed sale. relisted is a fingerprint match only."
            ),
            "generated_at": datetime.utcnow().isoformat(),
            "blocks": [],
            "summary": {label: 0 for label in ["new", "disappeared", "likely_sold", "relisted",
                                                "price_changed", "stable", "unknown_movement"]},
        }

    now = datetime.utcnow()

    # Estimate poll interval from TrackedEvent (use min across marketplaces as freshness window)
    te_q = await db.execute(
        select(func.min(TrackedEvent.poll_interval_minutes))
        .where(TrackedEvent.event_id == event_id, TrackedEvent.is_active == True)
    )
    min_interval = te_q.scalar_one() or 60

    new_window = timedelta(minutes=min_interval * 2)
    disappeared_window = timedelta(minutes=min_interval * 3)

    # Compute p50 of current_low_ask across all active blocks (for likely_sold heuristic)
    active_prices = [float(b.current_low_ask) for b in blocks if b.disappeared_at is None]
    p50 = statistics.median(active_prices) if active_prices else None

    # Build fingerprint index of recently disappeared blocks: (section, row, qty) → block
    recently_disappeared_fp: dict[tuple, CanonicalBlockLifecycle] = {}
    for b in blocks:
        if b.disappeared_at is not None and (now - b.disappeared_at) <= disappeared_window:
            fp = (b.section_id, b.row, b.quantity)
            recently_disappeared_fp[fp] = b

    attributed = []
    summary: dict[str, int] = {
        "new": 0, "disappeared": 0, "likely_sold": 0, "relisted": 0,
        "price_changed": 0, "stable": 0, "unknown_movement": 0,
    }

    for b in blocks:
        is_active = b.disappeared_at is None
        age_since_first = (now - b.first_seen_at).total_seconds() / 60
        is_new = is_active and age_since_first <= new_window.total_seconds() / 60
        price_delta = float(b.current_low_ask) - float(b.initial_low_ask)

        if not is_active:
            # Observed: block is gone
            age_gone = (now - b.disappeared_at).total_seconds() / 60
            if age_gone > disappeared_window.total_seconds() / 60:
                # Too old to attribute meaningfully — skip or mark stable
                label = "stable"
                confidence = "observed"
                note = "disappeared long ago, no recent signal"
            else:
                # Recent disappearance — attribute
                if p50 is not None and float(b.current_low_ask) <= p50:
                    label = "likely_sold"
                    confidence = "heuristic/inferred"
                    note = f"price {float(b.current_low_ask):.0f} ≤ p50 {p50:.0f}; sale is inferred, not confirmed"
                else:
                    label = "unknown_movement"
                    confidence = "observed_movement_unknown_cause"
                    note = "price above p50 or p50 unavailable; cause unknown"
                summary["disappeared"] += 1
        elif is_new:
            # Check for relisting fingerprint
            fp = (b.section_id, b.row, b.quantity)
            if fp in recently_disappeared_fp:
                label = "relisted"
                confidence = "fingerprint_inference"
                prior = recently_disappeared_fp[fp]
                note = (
                    f"(section={b.section_id}, row={b.row}, qty={b.quantity}) "
                    f"matches block {prior.block_id} that disappeared "
                    f"{round((now - prior.disappeared_at).total_seconds()/3600, 1)}h ago; "
                    f"relisting is fingerprint-based inference only"
                )
            else:
                label = "new"
                confidence = "observed"
                note = f"first seen {round(age_since_first, 0):.0f} min ago"
        elif abs(price_delta) >= 1.0:
            label = "price_changed"
            confidence = "observed"
            note = f"initial={float(b.initial_low_ask):.0f} → current={float(b.current_low_ask):.0f} (Δ{price_delta:+.0f})"
        else:
            label = "stable"
            confidence = "observed"
            note = "active with no notable price movement"

        if label in summary:
            summary[label] += 1

        attributed.append({
            "block_id": b.block_id,
            "section": b.section_id,
            "row": b.row,
            "quantity": b.quantity,
            "label": label,
            "confidence": confidence,
            "note": note,
            "first_seen_at": b.first_seen_at.isoformat(),
            "last_seen_at": b.last_seen_at.isoformat(),
            "disappeared_at": b.disappeared_at.isoformat() if b.disappeared_at else None,
            "initial_low_ask": float(b.initial_low_ask),
            "current_low_ask": float(b.current_low_ask),
            "snapshot_count": b.snapshot_count,
            "reappeared_count": b.reappeared_count,
        })

    # Sort: disappeared/likely_sold first, then new/relisted, then price_changed, stable last
    LABEL_ORDER = {
        "likely_sold": 0, "disappeared": 1, "unknown_movement": 2,
        "relisted": 3, "new": 4, "price_changed": 5, "stable": 6,
    }
    attributed.sort(key=lambda x: LABEL_ORDER.get(x["label"], 99))

    return {
        "event_id": event_id,
        "title": ev.title,
        "attribution_note": (
            "Attribution is heuristic and inferred from inventory movement patterns. "
            "likely_sold is not a confirmed sale. relisted is a fingerprint match only. "
            "unknown_movement indicates observed disappearance with insufficient signal to classify cause."
        ),
        "generated_at": now.isoformat(),
        "p50_active_ask": round(p50, 2) if p50 is not None else None,
        "summary": summary,
        "blocks": attributed,
    }
