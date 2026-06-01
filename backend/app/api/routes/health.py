"""
GET /api/health/freshness

Returns a full freshness report for every active (marketplace, event) pair.
Use this to:
  - identify stale or dead collectors at a glance
  - build daily health-check digests
  - verify StubHub is correctly classified as STALE/DEAD

Response shape
──────────────
{
  "generated_at": "2026-06-01T04:27:41",
  "summary": {
    "total_tracked_events": 60,
    "fresh": 21,
    "late": 0,
    "stale": 22,
    "dead": 17,
    "by_marketplace": {
      "stubhub":  { "fresh": 0, "late": 0, "stale": 20, "dead": 0 },
      "tickpick": { "fresh": 17, ... },
      "gametime": { "fresh": 4, ..., "dead": 16 }
    }
  },
  "stale_events":  [ { event_id, title, event_date, marketplace, freshness... }, ... ],
  "dead_events":   [ ... ],
  "fresh_events":  [ ... ]   (fresh + late)
}
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Event, TrackedEvent, Marketplace
from app.models.listing import PollRun
from app.utils.freshness import compute_freshness, is_current, FRESH, LATE, STALE, DEAD

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/freshness")
async def freshness_report(db: AsyncSession = Depends(get_db)):
    """Full per-(marketplace, event) freshness report."""

    # ── 1. All active tracked events with event + marketplace info ────────────
    rows_result = await db.execute(
        select(TrackedEvent, Event, Marketplace)
        .join(Event,       TrackedEvent.event_id       == Event.id)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(TrackedEvent.is_active == True)
        .order_by(Event.event_date, Marketplace.slug)
    )
    rows = rows_result.all()

    if not rows:
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_tracked_events": 0,
                FRESH: 0, LATE: 0, STALE: 0, DEAD: 0,
                "by_marketplace": {},
            },
            "stale_events": [],
            "dead_events": [],
            "fresh_events": [],
        }

    te_ids = [te.id for te, _, _ in rows]

    # ── 2. Last successful poll per tracked_event ─────────────────────────────
    lsr = await db.execute(
        select(PollRun.tracked_event_id, func.max(PollRun.completed_at))
        .where(
            PollRun.tracked_event_id.in_(te_ids),
            PollRun.status == "success",
            PollRun.completed_at.isnot(None),
        )
        .group_by(PollRun.tracked_event_id)
    )
    last_success_map: dict[int, datetime] = {row[0]: row[1] for row in lsr.all()}

    # ── 3. Recent runs for consecutive failure count ───────────────────────────
    cutoff = datetime.utcnow() - timedelta(days=30)
    rrr = await db.execute(
        select(PollRun)
        .where(
            PollRun.tracked_event_id.in_(te_ids),
            PollRun.started_at >= cutoff,
        )
        .order_by(PollRun.started_at.desc())
    )
    runs_by_te: dict[int, list] = {}
    for run in rrr.scalars().all():
        runs_by_te.setdefault(run.tracked_event_id, []).append(run)

    # ── 4. Compute freshness for every tracked event ──────────────────────────
    summary_counts: dict[str, int] = {FRESH: 0, LATE: 0, STALE: 0, DEAD: 0}
    by_marketplace: dict[str, dict[str, int]] = {}

    stale_events: list[dict] = []
    dead_events:  list[dict] = []
    fresh_events: list[dict] = []

    for te, event, mp in rows:
        te_runs = runs_by_te.get(te.id, [])
        consecutive_failures = 0
        for run in te_runs:
            if run.status == "error":
                consecutive_failures += 1
            else:
                break

        freshness = compute_freshness(
            marketplace_slug=mp.slug,
            event_date=event.event_date,
            poll_interval_minutes=te.poll_interval_minutes or 1440,
            last_success_at=last_success_map.get(te.id),
            consecutive_failures=consecutive_failures,
        )

        status = freshness["freshness_status"]
        summary_counts[status] = summary_counts.get(status, 0) + 1

        mp_counts = by_marketplace.setdefault(mp.slug, {FRESH: 0, LATE: 0, STALE: 0, DEAD: 0})
        mp_counts[status] = mp_counts.get(status, 0) + 1

        entry = {
            "tracked_event_id": te.id,
            "event_id":         event.id,
            "title":            event.title,
            "event_date":       event.event_date.isoformat(),
            "marketplace":      mp.slug,
            **freshness,
        }

        if status in (STALE,):
            stale_events.append(entry)
        elif status == DEAD:
            dead_events.append(entry)
        else:
            fresh_events.append(entry)

    # Sort by staleness severity: near-event first, then by age desc
    def _sort_key(e: dict):
        return (
            e.get("age_minutes") or 0,
        )

    stale_events.sort(key=_sort_key, reverse=True)
    dead_events.sort(key=_sort_key, reverse=True)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_tracked_events": len(rows),
            **summary_counts,
            "by_marketplace": by_marketplace,
        },
        "stale_events": stale_events,
        "dead_events":  dead_events,
        "fresh_events": fresh_events,
    }
