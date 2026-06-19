"""
GET /api/system/reliability

Returns in-memory + DB-sourced reliability state:
- Scheduler ring-buffer errors (last 50)
- Poll-run failure / success counts for the last 24 h
- Active crash signature
- Affected events and marketplaces
- Remediation hint
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import select, func, text

from app.database import AsyncSessionLocal
from app.models import PollRun, TrackedEvent, Event, Marketplace
from app.scheduler import get_reliability_state

logger = logging.getLogger(__name__)
router = APIRouter()

_24H = timedelta(hours=24)


@router.get("/system/reliability")
async def system_reliability():
    now = datetime.utcnow()
    cutoff = now - _24H

    mem = get_reliability_state()

    # ── DB-sourced poll stats ────────────────────────────────────────────────
    failed_polls_24h = 0
    success_polls_24h = 0
    scheduler_last_success_at_db: str | None = None
    scheduler_last_error_at_db: str | None = None
    affected_events: list[dict] = []
    affected_marketplaces: list[str] = []
    latest_snapshot_at: str | None = None

    try:
        async with AsyncSessionLocal() as db:
            # Count successes / failures in poll_runs in last 24h
            rows = await db.execute(
                select(PollRun.status, func.count().label("cnt"))
                .where(PollRun.started_at >= cutoff)
                .group_by(PollRun.status)
            )
            for row in rows.all():
                if row.status == "success":
                    success_polls_24h += row.cnt
                elif row.status == "error":
                    failed_polls_24h += row.cnt

            # Last successful poll_run timestamp
            last_ok = await db.execute(
                select(PollRun.started_at)
                .where(PollRun.status == "success")
                .order_by(PollRun.started_at.desc())
                .limit(1)
            )
            v = last_ok.scalar_one_or_none()
            scheduler_last_success_at_db = v.isoformat() if v else None

            # Last failed poll_run timestamp
            last_err = await db.execute(
                select(PollRun.started_at)
                .where(PollRun.status == "error")
                .order_by(PollRun.started_at.desc())
                .limit(1)
            )
            v = last_err.scalar_one_or_none()
            scheduler_last_error_at_db = v.isoformat() if v else None

            # Events with ALL polls failing (no success) in 24h — affected events
            bad_te_rows = await db.execute(
                text("""
                    SELECT tracked_event_id,
                           COUNT(*) AS total,
                           SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS ok
                    FROM poll_runs
                    WHERE started_at >= :cutoff
                    GROUP BY tracked_event_id
                    HAVING SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) = 0
                    LIMIT 20
                """),
                {"cutoff": cutoff}
            )
            bad_te_ids = [r[0] for r in bad_te_rows.all() if r[0]]

            for te_id in bad_te_ids[:10]:
                te = (await db.execute(
                    select(TrackedEvent).where(TrackedEvent.id == te_id)
                )).scalar_one_or_none()
                if not te:
                    continue
                ev = (await db.execute(
                    select(Event).where(Event.id == te.event_id)
                )).scalar_one_or_none()
                mp = (await db.execute(
                    select(Marketplace).where(Marketplace.id == te.marketplace_id)
                )).scalar_one_or_none()
                affected_events.append({
                    "tracked_event_id": te_id,
                    "event_id": te.event_id,
                    "event_title": ev.title if ev else None,
                    "marketplace": mp.slug if mp else None,
                })
                if mp and mp.slug not in affected_marketplaces:
                    affected_marketplaces.append(mp.slug)

            # Latest snapshot timestamp
            snap = await db.execute(
                text("SELECT MAX(snapshot_at) FROM listing_snapshots")
            )
            v = snap.scalar_one_or_none()
            latest_snapshot_at = v.isoformat() if v else None

    except Exception as exc:
        logger.error("reliability: DB query failed — %s", exc)

    # ── Derive status ────────────────────────────────────────────────────────
    active_sig = mem.get("active_crash_signature")
    total_fails = failed_polls_24h + mem.get("total_poll_failures_since_start", 0)

    if active_sig:
        status = "critical"
    elif failed_polls_24h > 10:
        status = "degraded"
    elif failed_polls_24h > 0:
        status = "degraded"
    else:
        status = "ok"

    remediation: str | None = None
    if active_sig and "consecutive_zero_inventory_count" in (active_sig or ""):
        remediation = (
            "TrackedEvent.consecutive_zero_inventory_count is missing from the "
            "deployed model. Commit backend/app/models/event.py and redeploy. "
            "Migration 0022 already applied the DB column."
        )
    elif active_sig:
        remediation = f"Investigate crash: {active_sig[:200]}"

    # ── System-level alert list ──────────────────────────────────────────────
    # Alert policy:
    #   RED (email+SMS): outage-level — no successful snapshot for >3h across ALL active events.
    #                    Scheduler crash. Heartbeat gone for >60 min.
    #   YELLOW (log/dashboard only): marketplace-specific degradation, per-event stale,
    #                                benchmark freshness, unresolved IDs.
    #   Never page for transient errors if fresh snapshots are still being written.
    #   30-minute rate-limit prevents alert floods.
    _RED_OUTAGE_H = 3.0   # hours without any snapshot before RED fires
    _RED_STALE_H  = 3.0   # hours without successful poll before RED fires

    system_alerts: list[dict] = []

    if active_sig:
        system_alerts.append({
            "type": "SCHEDULER_CRASH",
            "severity": "RED",
            "message": f"Active scheduler crash: {active_sig[:150]}",
            "remediation": remediation or "Investigate and redeploy.",
        })

    # Global snapshot freshness check — RED only if ALL snapshots are stale >3h.
    # If fresh snapshots are still being written (any marketplace), do NOT page.
    snap_age_h: float | None = None
    if latest_snapshot_at:
        try:
            snap_age_h = (now - datetime.fromisoformat(latest_snapshot_at)).total_seconds() / 3600
            if snap_age_h > _RED_OUTAGE_H:
                system_alerts.append({
                    "type": "SNAPSHOT_OUTAGE",
                    "severity": "RED",
                    "message": (
                        f"No listing snapshot written in {snap_age_h:.1f}h "
                        f"(threshold {_RED_OUTAGE_H}h) — ALL marketplaces may be down"
                    ),
                    "remediation": "Check Railway logs; all collectors may be failing.",
                })
        except Exception:
            pass
    else:
        # No snapshots ever — could be brand-new or total failure
        system_alerts.append({
            "type": "SNAPSHOT_OUTAGE",
            "severity": "YELLOW",
            "message": "No listing snapshots found in database",
            "remediation": "Confirm at least one event is being polled.",
        })

    # Scheduler poll staleness — RED only after _RED_STALE_H with no success.
    # Skip this RED if fresh snapshots exist (snapshots prove polling is working).
    last_succ_str = mem.get("last_success_at") or scheduler_last_success_at_db
    if last_succ_str:
        try:
            ts = datetime.fromisoformat(last_succ_str)
            poll_age_h = (now - ts.replace(tzinfo=None)).total_seconds() / 3600
            # Only RED if snapshots are also stale — avoids false alarm when poll_runs
            # fail but data is still being collected via another path
            snapshots_fresh = snap_age_h is not None and snap_age_h < _RED_OUTAGE_H
            if poll_age_h > _RED_STALE_H and not snapshots_fresh:
                system_alerts.append({
                    "type": "SCHEDULER_STALE",
                    "severity": "RED",
                    "message": (
                        f"No successful poll in {poll_age_h:.1f}h and no fresh snapshots "
                        f"(threshold {_RED_STALE_H}h)"
                    ),
                    "remediation": "Check if scheduler job is running on Railway.",
                })
            elif poll_age_h > _RED_STALE_H:
                system_alerts.append({
                    "type": "SCHEDULER_STALE",
                    "severity": "YELLOW",
                    "message": (
                        f"No successful poll_run recorded in {poll_age_h:.1f}h, "
                        f"but snapshots are fresh — transient poll_run tracking gap"
                    ),
                    "remediation": "Monitor; data collection appears healthy.",
                })
        except Exception:
            pass
    else:
        # No poll success ever recorded in-memory or DB
        # Don't immediately RED — could be first deploy
        system_alerts.append({
            "type": "SCHEDULER_STALE",
            "severity": "YELLOW",
            "message": "No successful poll recorded (may be new deployment)",
            "remediation": "Wait 10 min; if still absent check Railway scheduler logs.",
        })

    # Poll success rate — YELLOW only, and only if snapshots are also stale
    # (transient error bursts with healthy snapshots are not worth paging)
    total_polls = success_polls_24h + failed_polls_24h
    snapshots_healthy = snap_age_h is not None and snap_age_h < _RED_OUTAGE_H
    if total_polls > 20 and not snapshots_healthy:
        rate_pct = 100 * success_polls_24h / total_polls if total_polls else 0
        if rate_pct < 30:
            system_alerts.append({
                "type": "POLL_SUCCESS_RATE_LOW",
                "severity": "YELLOW",
                "message": (
                    f"Poll success rate {rate_pct:.0f}% over last 24h "
                    f"({success_polls_24h}/{total_polls}) and snapshots are stale"
                ),
                "remediation": "Check collector logs for persistent bot detection or auth failures.",
            })

    # Per-event snapshot staleness — YELLOW only, marketplace-specific.
    # This fires even when the global snapshot is fresh (some events may have
    # individual collector failures while others succeed).
    try:
        async with AsyncSessionLocal() as db:
            stale_event_rows = await db.execute(text("""
                SELECT e.id, e.title, MAX(ls.snapshot_at) AS last_snap
                FROM tracked_events te
                JOIN events e ON e.id = te.event_id
                LEFT JOIN listing_snapshots ls ON ls.event_id = e.id
                WHERE e.status = 'upcoming' AND te.is_active = true
                GROUP BY e.id, e.title
                HAVING MAX(ls.snapshot_at) IS NULL
                    OR MAX(ls.snapshot_at) < NOW() - INTERVAL '6 hours'
            """))
            stale_events = stale_event_rows.fetchall()
            if stale_events:
                stale_list = [
                    {"event_id": r[0], "title": r[1],
                     "last_snapshot_at": r[2].isoformat() if r[2] else None}
                    for r in stale_events
                ]
                system_alerts.append({
                    "type": "PER_EVENT_SNAPSHOT_STALE",
                    "severity": "YELLOW",
                    "message": (
                        f"{len(stale_events)} actively-tracked event(s) have no snapshot "
                        f"in the last 6h — marketplace-specific degradation possible"
                    ),
                    "affected_events": stale_list,
                    "remediation": (
                        "Check specific marketplace collector for these events. "
                        "Other events may be healthy. Do not page unless SNAPSHOT_OUTAGE also fires."
                    ),
                })
    except Exception as exc:
        logger.error("reliability: per-event snapshot check failed — %s", exc)

    # Intelligence layer: completed events with no outcome row
    try:
        async with AsyncSessionLocal() as db:
            missing_rows = await db.execute(text("""
                SELECT e.id, e.title
                FROM events e
                LEFT JOIN event_outcomes eo ON eo.event_id = e.id
                WHERE e.status = 'completed' AND eo.id IS NULL
            """))
            missing = missing_rows.fetchall()
            if missing:
                system_alerts.append({
                    "type": "OUTCOME_MISSING",
                    "severity": "YELLOW",
                    "message": (
                        f"{len(missing)} completed event(s) have no outcome row — "
                        f"benchmark pool is incomplete"
                    ),
                    "affected_events": [
                        {"event_id": r[0], "title": r[1]} for r in missing
                    ],
                    "remediation": (
                        "POST /api/intelligence/outcomes/compute-all to recompute. "
                        "Events with no snapshot data will be skipped with NO_SNAPSHOT_DATA status."
                    ),
                })
    except Exception as exc:
        logger.error("reliability: outcome-missing check failed — %s", exc)

    # Intelligence layer: stale benchmark distributions
    try:
        async with AsyncSessionLocal() as db:
            stale_bench = await db.execute(text("""
                SELECT event_type, computed_at,
                       NOW() - computed_at AS age
                FROM event_type_benchmarks
                WHERE computed_at < NOW() - INTERVAL '7 days'
            """))
            stale = stale_bench.fetchall()
            if stale:
                system_alerts.append({
                    "type": "BENCHMARK_STALE",
                    "severity": "YELLOW",
                    "message": (
                        f"{len(stale)} event-type benchmark(s) not recomputed in >7 days"
                    ),
                    "affected_types": [r[0] for r in stale],
                    "remediation": "POST /api/intelligence/benchmarks/event-types/compute",
                })
    except Exception as exc:
        logger.error("reliability: benchmark-stale check failed — %s", exc)

    # Unresolved marketplaces (NEEDS_MARKETPLACE_URL) — system-wide count
    try:
        async with AsyncSessionLocal() as db:
            from app.models import TrackedEvent as TE
            unresolved_count_row = await db.execute(
                text(
                    "SELECT COUNT(*) FROM tracked_events "
                    "WHERE external_event_id IS NULL AND is_active=true"
                )
            )
            unresolved_count = unresolved_count_row.scalar() or 0
            if unresolved_count > 0:
                system_alerts.append({
                    "type": "NEEDS_MARKETPLACE_URL",
                    "severity": "YELLOW",
                    "message": f"{unresolved_count} tracked event(s) have no external_event_id",
                    "remediation": "Use POST /api/events/{id}/marketplace-url to attach direct event URLs.",
                })
    except Exception:
        pass

    # ── Scheduler heartbeat staleness ────────────────────────────────────────
    try:
        async with AsyncSessionLocal() as db:
            hb_row = await db.execute(text(
                "SELECT MAX(beat_at) AS last_beat FROM scheduler_heartbeats"
            ))
            last_beat = hb_row.scalar_one_or_none()
            if last_beat is None:
                system_alerts.append({
                    "type": "HEARTBEAT_NEVER_WRITTEN",
                    "severity": "YELLOW",
                    "message": "No scheduler heartbeat has ever been written (may be new deploy)",
                    "remediation": "Heartbeats write every 10 poll ticks (~10 min). Wait and recheck.",
                })
            else:
                beat_age_min = (now - last_beat.replace(tzinfo=None)).total_seconds() / 60
                if beat_age_min > 15:
                    system_alerts.append({
                        "type": "HEARTBEAT_STALE",
                        "severity": "RED" if beat_age_min > 60 else "YELLOW",
                        "message": (
                            f"Scheduler heartbeat is {beat_age_min:.0f} min old "
                            f"(last: {str(last_beat)[:19]})"
                        ),
                        "remediation": "Check if scheduler is running on Railway.",
                    })
    except Exception as exc:
        logger.error("reliability: heartbeat check failed — %s", exc)

    # ── Alert delivery status ────────────────────────────────────────────────
    from app.services.alert_sender import alert_delivery_status
    delivery = alert_delivery_status()

    # ── Fire RED alerts (outage-class only) ─────────────────────────────────
    # Only fire alerts that represent a genuine outage needing human action.
    # PER_EVENT_SNAPSHOT_STALE and BENCHMARK_STALE are YELLOW — never paged.
    _PAGEABLE_TYPES = {"SCHEDULER_CRASH", "SNAPSHOT_OUTAGE", "SCHEDULER_STALE", "HEARTBEAT_STALE", "OUTCOME_GENERATION_FAILURE"}
    red_alerts = [
        a for a in system_alerts
        if a["severity"] == "RED" and a["type"] in _PAGEABLE_TYPES
    ]
    if red_alerts:
        try:
            from app.services.alert_sender import fire_alert
            for a in red_alerts[:2]:  # max 2 alert types per reliability check
                asyncio.create_task(
                    fire_alert(a["type"], "RED", a["message"])
                )
        except Exception as exc:
            logger.error("reliability: failed to fire RED alert — %s", exc)

    return {
        "status": status,
        "recent_errors": mem.get("recent_errors", []),
        "failed_polls_24h": failed_polls_24h,
        "success_polls_24h": success_polls_24h,
        "scheduler_last_success_at": mem.get("last_success_at") or scheduler_last_success_at_db,
        "scheduler_last_error_at": mem.get("last_error_at") or scheduler_last_error_at_db,
        "active_crash_signature": active_sig,
        "affected_events": affected_events,
        "affected_marketplaces": affected_marketplaces,
        "latest_snapshot_at": latest_snapshot_at,
        "remediation": remediation,
        "alerts": system_alerts,
        "alert_delivery": delivery,
    }
