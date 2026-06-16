"""
GET /api/collection-health

Single-call production health check.  Returns:
  - overall status (ok | degraded | critical)
  - per-marketplace freshness
  - scheduler backlog (overdue TEs, stuck runs)
  - Mac collector heartbeat (derived from last listings_found>0 for StubHub/TickPick)
  - stale marketplace warnings with recommended action

All reads are against existing tables (poll_runs, tracked_events, events,
marketplaces).  No new tables or background tasks.

Mac heartbeat logic:
  Railway's StubHub/TickPick schedulers always produce listings_found=0 (bot
  detection).  Therefore last PR with listings_found>0 for those slugs reliably
  identifies the last successful Mac collector run.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.database import get_db
from app.models import Event, TrackedEvent, Marketplace
from app.models.listing import PollRun

router = APIRouter(prefix="/collection-health", tags=["health"])

# ── thresholds ────────────────────────────────────────────────────────────────
_MAC_STALE_MINUTES   = 120   # StubHub/TickPick Mac collector expected every 30 min
_SCHEDULER_STALE_MIN = 90    # Railway scheduler expected every 1 min
_STUCK_RUN_MINUTES   = 30    # poll_run stuck in "running" beyond this → stuck

# Marketplaces fully managed by Railway scheduler (no Mac needed)
_RAILWAY_ONLY   = {"gametime", "vividseats"}
# Marketplaces where Mac provides real data; Railway scheduler always returns 0
_MAC_COLLECTORS = {"stubhub", "tickpick"}


@router.get("")
async def collection_health(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()

    # ── 1. Overdue tracked events (upcoming only) ─────────────────────────────
    overdue_q = await db.execute(
        select(func.count())
        .select_from(TrackedEvent)
        .join(Event, TrackedEvent.event_id == Event.id)
        .where(
            TrackedEvent.is_active == True,
            Event.status == "upcoming",
            TrackedEvent.next_poll_at <= now,
        )
    )
    overdue_count: int = overdue_q.scalar_one()

    # ── 2. Stuck poll_runs ────────────────────────────────────────────────────
    stuck_q = await db.execute(
        select(func.count())
        .select_from(PollRun)
        .where(
            PollRun.status == "running",
            PollRun.started_at < now - timedelta(minutes=_STUCK_RUN_MINUTES),
        )
    )
    stuck_count: int = stuck_q.scalar_one()

    # ── 3. Per-marketplace: last success, listings_found, freshness ───────────
    slugs_of_interest = {"gametime", "vividseats", "stubhub", "tickpick"}

    mp_q = await db.execute(
        select(Marketplace.slug, Marketplace.id)
        .where(Marketplace.slug.in_(slugs_of_interest))
    )
    mp_map: dict[str, int] = {row.slug: row.id for row in mp_q.all()}

    mp_status: dict[str, dict[str, Any]] = {}

    for slug, mp_id in sorted(mp_map.items()):
        # Last successful PR for this marketplace across all events
        last_ok_q = await db.execute(
            select(
                func.max(PollRun.started_at).label("last_run"),
                func.max(PollRun.listings_found).label("max_found"),
            )
            .select_from(PollRun)
            .join(TrackedEvent, PollRun.tracked_event_id == TrackedEvent.id)
            .where(
                TrackedEvent.marketplace_id == mp_id,
                PollRun.status == "success",
                PollRun.started_at >= now - timedelta(hours=48),
            )
        )
        last_ok = last_ok_q.one()
        last_run: datetime | None = last_ok.last_run

        # For Mac-collected slugs: heartbeat = last PR with listings_found > 0
        mac_last_run: datetime | None = None
        mac_mins_ago: int | None = None
        if slug in _MAC_COLLECTORS:
            mac_q = await db.execute(
                select(func.max(PollRun.started_at))
                .select_from(PollRun)
                .join(TrackedEvent, PollRun.tracked_event_id == TrackedEvent.id)
                .where(
                    TrackedEvent.marketplace_id == mp_id,
                    PollRun.status == "success",
                    PollRun.listings_found > 0,
                    PollRun.started_at >= now - timedelta(hours=48),
                )
            )
            mac_last_run = mac_q.scalar_one()
            if mac_last_run:
                mac_mins_ago = int((now - mac_last_run).total_seconds() / 60)

        mins_ago: int | None = (
            int((now - last_run).total_seconds() / 60) if last_run else None
        )

        # Freshness classification
        if slug in _MAC_COLLECTORS:
            threshold = _MAC_STALE_MINUTES
            age_for_status = mac_mins_ago
        else:
            threshold = _SCHEDULER_STALE_MIN
            age_for_status = mins_ago

        if age_for_status is None:
            freshness = "dead"
        elif age_for_status <= threshold:
            freshness = "fresh"
        elif age_for_status <= threshold * 3:
            freshness = "late"
        elif age_for_status <= threshold * 10:
            freshness = "stale"
        else:
            freshness = "dead"

        entry: dict[str, Any] = {
            "freshness": freshness,
            "last_success_utc": last_run.isoformat() if last_run else None,
            "mins_since_last_success": mins_ago,
        }
        if slug in _MAC_COLLECTORS:
            entry["mac_last_data_utc"] = mac_last_run.isoformat() if mac_last_run else None
            entry["mac_mins_since_data"] = mac_mins_ago
            entry["collection_source"] = "mac_collector → railway_ingest"
        else:
            entry["collection_source"] = "railway_scheduler"

        mp_status[slug] = entry

    # ── 4. Stale VividSeats events (no external_event_id → never collected) ──
    vs_never_q = await db.execute(
        select(func.count())
        .select_from(TrackedEvent)
        .join(Event, TrackedEvent.event_id == Event.id)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(
            TrackedEvent.is_active == True,
            Event.status == "upcoming",
            Marketplace.slug == "vividseats",
            or_(
                TrackedEvent.external_event_id.is_(None),
                TrackedEvent.external_event_id == "",
            ),
        )
    )
    vs_no_id_count: int = vs_never_q.scalar_one()

    # ── 5. Overall status ─────────────────────────────────────────────────────
    warnings: list[str] = []
    recommended_actions: list[str] = []

    critical = False
    degraded = False

    if overdue_count > 20:
        critical = True
        warnings.append(f"SCHEDULER_STORM: {overdue_count} overdue TEs — DB pool saturation risk")
        recommended_actions.append("Run: UPDATE tracked_events SET next_poll_at = NOW()+INTERVAL '1440 min' WHERE is_active=true AND next_poll_at < NOW()")
    elif overdue_count > 0:
        degraded = True
        warnings.append(f"{overdue_count} tracked events overdue for polling (normal if <10, transient)")

    if stuck_count > 0:
        degraded = True
        warnings.append(f"{stuck_count} poll_run(s) stuck in 'running' >30 min")
        recommended_actions.append("Run: UPDATE poll_runs SET status='timeout' WHERE status='running' AND started_at < NOW()-INTERVAL '30 minutes'")

    for slug in _MAC_COLLECTORS:
        info = mp_status.get(slug, {})
        mac_age = info.get("mac_mins_since_data")
        if mac_age is None:
            critical = True
            warnings.append(f"MAC_DEAD: {slug} — no data in last 48h (Mac collector may be down)")
            recommended_actions.append(f"Check launchd: launchctl list com.concerttracker.{slug}-collect")
        elif mac_age > _MAC_STALE_MINUTES:
            degraded = True
            warnings.append(f"MAC_STALE: {slug} — last data {mac_age}min ago (threshold {_MAC_STALE_MINUTES}min)")

    for slug in _RAILWAY_ONLY:
        info = mp_status.get(slug, {})
        freshness = info.get("freshness", "dead")
        if freshness in ("dead",):
            critical = True
            warnings.append(f"RAILWAY_DEAD: {slug} — no successful collection in 48h")
        elif freshness == "stale":
            degraded = True
            warnings.append(f"RAILWAY_STALE: {slug} — collection overdue")

    if vs_no_id_count > 0:
        warnings.append(f"VIVIDSEATS_NO_ID: {vs_no_id_count} upcoming events have no VividSeats external_event_id (CONFIRMED_NOT_RESOLVED)")

    if critical:
        overall = "critical"
    elif degraded:
        overall = "degraded"
    else:
        overall = "ok"

    return {
        "generated_at": now.isoformat(),
        "overall_status": overall,
        "scheduler": {
            "overdue_tracked_events": overdue_count,
            "stuck_poll_runs": stuck_count,
            "status": "critical" if overdue_count > 20 or stuck_count > 0 else
                      "degraded" if overdue_count > 0 else "ok",
        },
        "marketplaces": mp_status,
        "warnings": warnings,
        "recommended_actions": recommended_actions,
        "known_limitations": {
            "vividseats_missing_ext_id_count": vs_no_id_count,
            "stubhub_railway_scheduler_always_zero": True,
            "tickpick_railway_scheduler_always_zero": True,
        },
    }
