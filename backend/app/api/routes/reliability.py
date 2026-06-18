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
    system_alerts: list[dict] = []

    if active_sig:
        system_alerts.append({
            "type": "SCHEDULER_CRASH",
            "severity": "RED",
            "message": f"Active scheduler crash: {active_sig[:150]}",
            "remediation": remediation or "Investigate and redeploy.",
        })

    # No successful poll within last 2h
    last_succ_str = mem.get("last_success_at") or scheduler_last_success_at_db
    if last_succ_str:
        try:
            ts = datetime.fromisoformat(last_succ_str)
            age_h = (now - ts.replace(tzinfo=None)).total_seconds() / 3600
            if age_h > 2:
                system_alerts.append({
                    "type": "SCHEDULER_STALE",
                    "severity": "RED",
                    "message": f"No successful poll in {age_h:.1f}h (threshold 2h)",
                    "remediation": "Check if scheduler job is running on Railway.",
                })
        except Exception:
            pass
    else:
        system_alerts.append({
            "type": "SCHEDULER_STALE",
            "severity": "RED",
            "message": "No successful poll recorded",
            "remediation": "Scheduler may not have started. Check Railway logs.",
        })

    # Poll success rate
    total_polls = success_polls_24h + failed_polls_24h
    if total_polls > 10 and success_polls_24h / total_polls < 0.5:
        rate_pct = 100 * success_polls_24h / total_polls
        system_alerts.append({
            "type": "POLL_SUCCESS_RATE_LOW",
            "severity": "RED" if rate_pct < 20 else "YELLOW",
            "message": f"Poll success rate {rate_pct:.0f}% over last 24h ({success_polls_24h}/{total_polls})",
            "remediation": "Check collector logs for bot detection or auth failures.",
        })

    # Latest snapshot stale > 8h
    if latest_snapshot_at:
        try:
            snap_age_h = (now - datetime.fromisoformat(latest_snapshot_at)).total_seconds() / 3600
            if snap_age_h > 8:
                system_alerts.append({
                    "type": "SNAPSHOT_STALE",
                    "severity": "YELLOW",
                    "message": f"Latest listing snapshot {snap_age_h:.1f}h old (threshold 8h)",
                    "remediation": "Confirm at least one collector is writing snapshots.",
                })
        except Exception:
            pass

    # Per-event snapshot staleness (genuine gap: global check misses event-specific failures)
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
                    OR MAX(ls.snapshot_at) < NOW() - INTERVAL '4 hours'
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
                        f"in the last 4h while system-level polling is running"
                    ),
                    "affected_events": stale_list,
                    "remediation": (
                        "Check the specific marketplace collector for these events. "
                        "May indicate a collector crash or auth failure for specific event."
                    ),
                })
    except Exception as exc:
        logger.error("reliability: per-event snapshot check failed — %s", exc)

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

    # ── Email-ready payload ──────────────────────────────────────────────────
    # Callers check status; if EMAIL_DELIVERY_NOT_CONFIGURED they know to configure SMTP/SendGrid.
    critical_alerts = [a for a in system_alerts if a["severity"] == "RED"]
    pending_email_alerts: dict = {
        "delivery_status": "EMAIL_DELIVERY_NOT_CONFIGURED",
        "would_send": len(critical_alerts) > 0,
        "recipient": "surajgohill@gmail.com",
        "subject": f"[Concert Tracker] {len(critical_alerts)} critical alert(s)" if critical_alerts else None,
        "alerts": critical_alerts,
    }

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
        "pending_email_alerts": pending_email_alerts,
    }
