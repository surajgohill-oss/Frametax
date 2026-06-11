"""
Gap Monitor — lightweight internal alert and self-heal layer.

Routes:
  GET  /api/data-health/gaps         — scan all active events, return alert array (read + async fixes)
  POST /api/data-health/gaps/heal    — same scan, fires self-fixes synchronously, returns what changed

Gap types:
  COLLECTION_GAP    — poll late, repeated failures, or unresolved external_event_id
  PROCESSING_GAP    — poll succeeded with listings, no canonical snapshot followed
  SNAPSHOT_GAP      — canonical snapshot stale relative to poll cadence
  LIVE_STATS_GAP    — snapshot claims inventory > 0 but live listing table shows 0

Self-fix rules (safe recovery only):
  COLLECTION_GAP (late)   → asyncio.create_task(run_poll_for_tracked_event(te_id))
  COLLECTION_GAP (errors) → retry once if error is NOT 403/404/content-based; alert if blocked
  PROCESSING_GAP          → snapshot_canonical_inventory(event_id, db) + commit
  SNAPSHOT_GAP            → snapshot_canonical_inventory(event_id, db) + commit
  LIVE_STATS_GAP          → read-only re-verify, alert only (no mutation)
  Unresolved ID           → alert only (cannot fix without external resolution)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models import Event, Listing, Marketplace
from app.models.canonical import CanonicalInventorySnapshot
from app.models.event import TrackedEvent
from app.models.listing import PollRun

logger = logging.getLogger(__name__)

router = APIRouter(tags=["data-health"])

# ── Constants ────────────────────────────────────────────────────────────────

# Error messages that indicate a blocked marketplace (do not retry)
BLOCKED_ERROR_PATTERNS = ("403", "404", "forbidden", "not found", "content_gap",
                           "no results", "no listings", "unavailable",
                           "unresolved_event_id")

# Minimum overage before self-fix fires (avoid thrashing near-on-time polls)
LATE_THRESHOLD_MULTIPLIER = 1.5

# Self-fix is not attempted for events within this many minutes of their date
# (past-event noise — the data is final anyway)
NEAR_EVENT_SKIP_HOURS = 2


# ── Data structures ──────────────────────────────────────────────────────────

def _make_alert(
    *,
    event_id: int,
    title: str,
    marketplace: str,
    gap_type: str,
    severity: str,
    last_success: Optional[datetime],
    last_failure: Optional[datetime],
    expected_cadence_minutes: int,
    current_age_minutes: Optional[float],
    attempted_self_fix: bool = False,
    fix_action: Optional[str] = None,
    result: str = "alert_only",
    recommended_action: str = "",
    note: Optional[str] = None,
) -> dict:
    return {
        "event_id": event_id,
        "title": title,
        "marketplace": marketplace,
        "gap_type": gap_type,
        "severity": severity,
        "last_success": last_success.isoformat() if last_success else None,
        "last_failure": last_failure.isoformat() if last_failure else None,
        "expected_cadence_minutes": expected_cadence_minutes,
        "current_age_minutes": round(current_age_minutes, 1) if current_age_minutes is not None else None,
        "attempted_self_fix": attempted_self_fix,
        "fix_action": fix_action,
        "result": result,
        "recommended_action": recommended_action,
        "note": note,
    }


def _age_minutes(dt: Optional[datetime]) -> Optional[float]:
    if dt is None:
        return None
    return (datetime.utcnow() - dt).total_seconds() / 60


def _is_blocked_error(msg: Optional[str]) -> bool:
    if not msg:
        return False
    low = msg.lower()
    return any(p in low for p in BLOCKED_ERROR_PATTERNS)


def _severity(age_minutes: Optional[float], interval: int, consecutive_errors: int) -> str:
    if consecutive_errors >= 3:
        return "critical"
    if age_minutes is None:
        return "warning"
    ratio = age_minutes / interval
    if ratio >= 3.0 or consecutive_errors >= 2:
        return "critical"
    if ratio >= 2.0 or consecutive_errors >= 1:
        return "warning"
    return "info"


# ── Core scan logic ──────────────────────────────────────────────────────────

async def _run_gap_scan(db: AsyncSession, *, heal: bool = False) -> dict:
    """
    Scan all active events × marketplaces for gaps.
    If heal=True, fire safe self-fixes (poll trigger async; snapshot sync).
    Returns {"alerts": [...], "summary": {...}, "generated_at": ...}.
    """
    now = datetime.utcnow()
    alerts = []

    # ── Load universe ──────────────────────────────────────────────────────
    ev_q = await db.execute(
        select(Event).where(Event.status.in_(["upcoming", "active"]))
    )
    all_events: list[Event] = ev_q.scalars().all()
    event_map = {e.id: e for e in all_events}

    te_q = await db.execute(
        select(TrackedEvent, Marketplace.slug)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(
            TrackedEvent.event_id.in_(list(event_map.keys())),
            TrackedEvent.is_active == True,
        )
    )
    te_rows = te_q.all()  # [(TrackedEvent, slug), ...]

    # Index: tracked_event_id → (te, slug)
    te_index: dict[int, tuple] = {te.id: (te, slug) for te, slug in te_rows}

    # All poll runs: tracked_event_id → list[PollRun] sorted desc
    pr_q = await db.execute(
        select(PollRun)
        .where(PollRun.tracked_event_id.in_(list(te_index.keys())))
        .order_by(PollRun.tracked_event_id, PollRun.started_at.desc())
    )
    all_poll_runs: list[PollRun] = pr_q.scalars().all()
    poll_runs_by_te: dict[int, list[PollRun]] = {}
    for pr in all_poll_runs:
        poll_runs_by_te.setdefault(pr.tracked_event_id, []).append(pr)

    # Latest canonical snapshot per event
    snap_q = await db.execute(
        select(
            CanonicalInventorySnapshot.event_id,
            func.max(CanonicalInventorySnapshot.snapshot_at).label("latest_at"),
        )
        .where(CanonicalInventorySnapshot.event_id.in_(list(event_map.keys())))
        .group_by(CanonicalInventorySnapshot.event_id)
    )
    last_snap: dict[int, datetime] = {r[0]: r[1] for r in snap_q}

    # Most recent snapshot row per event (for total_raw_listings)
    snap_detail_q = await db.execute(
        select(CanonicalInventorySnapshot)
        .where(
            CanonicalInventorySnapshot.event_id.in_(list(event_map.keys())),
            CanonicalInventorySnapshot.snapshot_at.in_(list(last_snap.values())),
        )
    )
    snap_detail: dict[int, CanonicalInventorySnapshot] = {
        s.event_id: s for s in snap_detail_q.scalars().all()
    }

    # Active listing counts per event
    al_q = await db.execute(
        select(Listing.event_id, func.count())
        .where(
            Listing.event_id.in_(list(event_map.keys())),
            Listing.is_active == True,
        )
        .group_by(Listing.event_id)
    )
    active_listings_by_event: dict[int, int] = {r[0]: r[1] for r in al_q}

    # Snapshots triggered by specific poll run IDs (for PROCESSING_GAP detection)
    snap_poll_q = await db.execute(
        select(CanonicalInventorySnapshot.triggered_by_poll_run_id)
        .where(
            CanonicalInventorySnapshot.event_id.in_(list(event_map.keys())),
            CanonicalInventorySnapshot.triggered_by_poll_run_id.isnot(None),
        )
    )
    snapped_poll_run_ids: set[int] = {r[0] for r in snap_poll_q}

    # Track which events had PROCESSING_GAP self-fix attempted (once per event)
    processing_gap_fixed: set[int] = set()
    # Track which events already have a SNAPSHOT_GAP or LIVE_STATS_GAP alert emitted
    snapshot_gap_alerted: set[int] = set()
    live_stats_alerted: set[int] = set()

    # ── Per tracked event evaluation ───────────────────────────────────────
    for te, slug in te_rows:
        ev = event_map.get(te.event_id)
        if ev is None:
            continue

        # Skip events very close to / past their date
        event_age_hours = (now - ev.event_date.replace(tzinfo=None)).total_seconds() / 3600
        if event_age_hours >= NEAR_EVENT_SKIP_HOURS:
            continue

        interval = te.poll_interval_minutes
        threshold_min = interval * LATE_THRESHOLD_MULTIPLIER
        polls: list[PollRun] = poll_runs_by_te.get(te.id, [])
        last_success_run = next((p for p in polls if p.status == "success"), None)
        last_failure_run = next((p for p in polls if p.status == "error"), None)

        # Consecutive errors = how many of the most recent runs are errors
        consecutive_errors = 0
        for p in polls:
            if p.status == "error":
                consecutive_errors += 1
            else:
                break

        last_success_at = last_success_run.started_at if last_success_run else None
        last_failure_at = last_failure_run.started_at if last_failure_run else None

        # ── 1. COLLECTION_GAP ─────────────────────────────────────────────

        # 1a. No external event ID (never resolved)
        if not te.external_event_id and not polls:
            alerts.append(_make_alert(
                event_id=ev.id, title=ev.title, marketplace=slug,
                gap_type="COLLECTION_GAP",
                severity="warning",
                last_success=None, last_failure=None,
                expected_cadence_minutes=interval,
                current_age_minutes=None,
                result="alert_only",
                recommended_action="Run /api/poll/resolve-ids to attempt external ID resolution.",
                note="No external_event_id and no poll runs. Event cannot be polled until resolved.",
            ))
            continue

        # 1b. No poll runs at all
        if not polls:
            alerts.append(_make_alert(
                event_id=ev.id, title=ev.title, marketplace=slug,
                gap_type="COLLECTION_GAP",
                severity="warning",
                last_success=None, last_failure=None,
                expected_cadence_minutes=interval,
                current_age_minutes=None,
                result="alert_only",
                recommended_action="Trigger /api/poll/events/{event_id}/trigger to start collection.",
                note="TrackedEvent exists with external_event_id but no poll runs recorded.",
            ))
            continue

        # 1c. Consecutive errors (3+) — check if blocked
        if consecutive_errors >= 3:
            blocked = _is_blocked_error(last_failure_run.error_message if last_failure_run else None)
            sev = _severity(None, interval, consecutive_errors)
            fix_action = None
            result = "alert_only"
            if heal and not blocked:
                try:
                    asyncio.create_task(
                        _trigger_poll_background(te.id)
                    )
                    fix_action = "triggered_poll_background"
                    result = "fix_dispatched"
                    logger.info("GAP_MONITOR: self-fix poll dispatched te_id=%d event='%s' mp=%s",
                                te.id, ev.title, slug)
                except Exception as exc:
                    fix_action = "trigger_failed"
                    result = "fix_failed"
                    logger.warning("GAP_MONITOR: self-fix poll failed te_id=%d — %s", te.id, exc)

            alerts.append(_make_alert(
                event_id=ev.id, title=ev.title, marketplace=slug,
                gap_type="COLLECTION_GAP",
                severity=sev,
                last_success=last_success_at, last_failure=last_failure_at,
                expected_cadence_minutes=interval,
                current_age_minutes=_age_minutes(last_failure_at),
                attempted_self_fix=heal and not blocked,
                fix_action=fix_action,
                result=result,
                recommended_action=(
                    f"Marketplace {slug} appears blocked (403/404). Check external_event_id validity and marketplace resolver."
                    if blocked else
                    f"{consecutive_errors} consecutive errors. Self-fix poll dispatched." if result == "fix_dispatched" else
                    f"{consecutive_errors} consecutive errors. Manual intervention may be required."
                ),
                note=f"Last error: {last_failure_run.error_message}" if last_failure_run else None,
            ))
            continue

        # 1d. Poll is overdue
        last_any_poll = polls[0].started_at if polls else None
        age = _age_minutes(last_any_poll)
        if age is not None and age > threshold_min:
            sev = _severity(age, interval, consecutive_errors)
            fix_action = None
            result = "alert_only"
            attempted = False
            if heal:
                attempted = True
                try:
                    asyncio.create_task(_trigger_poll_background(te.id))
                    fix_action = "triggered_poll_background"
                    result = "fix_dispatched"
                    logger.info("GAP_MONITOR: late-poll fix dispatched te_id=%d event='%s' mp=%s age=%.1fmin",
                                te.id, ev.title, slug, age)
                except Exception as exc:
                    fix_action = "trigger_failed"
                    result = "fix_failed"
                    logger.warning("GAP_MONITOR: late-poll fix failed te_id=%d — %s", te.id, exc)

            alerts.append(_make_alert(
                event_id=ev.id, title=ev.title, marketplace=slug,
                gap_type="COLLECTION_GAP",
                severity=sev,
                last_success=last_success_at, last_failure=last_failure_at,
                expected_cadence_minutes=interval,
                current_age_minutes=age,
                attempted_self_fix=attempted,
                fix_action=fix_action,
                result=result,
                recommended_action=(
                    f"Poll dispatched. Expected fresh data within {interval} minutes."
                    if result == "fix_dispatched" else
                    f"Last poll {age:.0f} min ago vs cadence {interval} min. Consider triggering /api/poll/events/{ev.id}/trigger."
                ),
            ))
            # Continue to also check downstream gaps even when poll is late

        # ── 2. PROCESSING_GAP ─────────────────────────────────────────────
        # Most recent successful poll with listings found has no snapshot following it

        recent_success_with_data = next(
            (p for p in polls if p.status == "success" and p.listings_found > 0), None
        )

        if recent_success_with_data:
            poll_snap_at = last_snap.get(ev.id)
            has_snapshot_for_poll = (
                recent_success_with_data.id in snapped_poll_run_ids
                or (
                    poll_snap_at is not None
                    and poll_snap_at >= recent_success_with_data.started_at - timedelta(minutes=1)
                )
            )

            if not has_snapshot_for_poll and ev.id not in processing_gap_fixed:
                fix_action = None
                result = "alert_only"
                attempted = False

                if heal:
                    attempted = True
                    try:
                        snap_id = await _run_snapshot_fix(ev.id)
                        if snap_id:
                            fix_action = f"snapshot_written(id={snap_id})"
                            result = "fix_applied"
                            processing_gap_fixed.add(ev.id)
                            logger.info("GAP_MONITOR: PROCESSING_GAP fixed event=%d snap_id=%d",
                                        ev.id, snap_id)
                        else:
                            fix_action = "snapshot_returned_none"
                            result = "fix_skipped"
                            logger.info("GAP_MONITOR: PROCESSING_GAP snapshot_fn returned None event=%d"
                                        " (0 listings?)", ev.id)
                    except Exception as exc:
                        fix_action = "snapshot_failed"
                        result = "fix_failed"
                        logger.warning("GAP_MONITOR: PROCESSING_GAP snapshot fix failed event=%d — %s",
                                       ev.id, exc)

                alerts.append(_make_alert(
                    event_id=ev.id, title=ev.title, marketplace=slug,
                    gap_type="PROCESSING_GAP",
                    severity="warning",
                    last_success=recent_success_with_data.started_at,
                    last_failure=None,
                    expected_cadence_minutes=interval,
                    current_age_minutes=_age_minutes(recent_success_with_data.started_at),
                    attempted_self_fix=attempted,
                    fix_action=fix_action,
                    result=result,
                    recommended_action=(
                        "Canonical snapshot written successfully."
                        if result == "fix_applied" else
                        "Poll succeeded with listings but no canonical snapshot followed. "
                        "POST /api/data-health/gaps/heal to trigger snapshot write."
                    ),
                    note=f"poll_run_id={recent_success_with_data.id} listings_found={recent_success_with_data.listings_found}",
                ))

        # ── 3. SNAPSHOT_GAP ───────────────────────────────────────────────
        # Canonical snapshot exists but is stale relative to 2× poll cadence

        snap_at = last_snap.get(ev.id)
        snap_age = _age_minutes(snap_at)
        active_for_event = active_listings_by_event.get(ev.id, 0)

        if (
            snap_at is not None
            and snap_age is not None
            and snap_age > interval * 2
            and active_for_event > 0
            and ev.id not in processing_gap_fixed  # don't double-alert if we just fixed PROCESSING_GAP
            and ev.id not in snapshot_gap_alerted   # emit once per event
        ):
            sev = _severity(snap_age, interval, 0)
            fix_action = None
            result = "alert_only"
            attempted = False

            if heal:
                attempted = True
                try:
                    snap_id = await _run_snapshot_fix(ev.id)
                    if snap_id:
                        fix_action = f"snapshot_written(id={snap_id})"
                        result = "fix_applied"
                        processing_gap_fixed.add(ev.id)
                        logger.info("GAP_MONITOR: SNAPSHOT_GAP fixed event=%d snap_id=%d", ev.id, snap_id)
                    else:
                        fix_action = "snapshot_returned_none"
                        result = "fix_skipped"
                except Exception as exc:
                    fix_action = "snapshot_failed"
                    result = "fix_failed"
                    logger.warning("GAP_MONITOR: SNAPSHOT_GAP snapshot fix failed event=%d — %s", ev.id, exc)

            snapshot_gap_alerted.add(ev.id)
            alerts.append(_make_alert(
                event_id=ev.id, title=ev.title, marketplace=slug,
                gap_type="SNAPSHOT_GAP",
                severity=sev,
                last_success=snap_at,
                last_failure=None,
                expected_cadence_minutes=interval,
                current_age_minutes=snap_age,
                attempted_self_fix=attempted,
                fix_action=fix_action,
                result=result,
                recommended_action=(
                    "Snapshot refreshed."
                    if result == "fix_applied" else
                    f"Snapshot is {snap_age:.0f} min old vs cadence {interval} min. "
                    "POST /api/data-health/gaps/heal to refresh."
                ),
            ))

        # ── 4. LIVE_STATS_GAP ─────────────────────────────────────────────
        # Snapshot claims inventory > 0 but live listing table returns 0

        snap_detail_row = snap_detail.get(ev.id)
        if (
            snap_detail_row is not None
            and snap_detail_row.total_raw_listings > 0
            and active_for_event == 0
            and ev.id not in live_stats_alerted  # emit once per event
        ):
            live_stats_alerted.add(ev.id)
            alerts.append(_make_alert(
                event_id=ev.id, title=ev.title, marketplace=slug,
                gap_type="LIVE_STATS_GAP",
                severity="warning",
                last_success=snap_at,
                last_failure=None,
                expected_cadence_minutes=interval,
                current_age_minutes=snap_age,
                result="alert_only",
                recommended_action=(
                    "Snapshot reports listings but live Listing table shows 0 active rows. "
                    "Verify listings were not bulk-deactivated. Trigger a fresh poll to reconcile."
                ),
                note=(
                    f"snapshot.total_raw_listings={snap_detail_row.total_raw_listings} "
                    f"live_active_listings=0"
                ),
            ))

    # ── Summary ────────────────────────────────────────────────────────────
    type_counts: dict[str, int] = {}
    sev_counts: dict[str, int] = {}
    for a in alerts:
        type_counts[a["gap_type"]] = type_counts.get(a["gap_type"], 0) + 1
        sev_counts[a["severity"]] = sev_counts.get(a["severity"], 0) + 1

    return {
        "generated_at": now.isoformat(),
        "heal_mode": heal,
        "total_alerts": len(alerts),
        "summary": {
            "by_type": type_counts,
            "by_severity": sev_counts,
            "critical": sev_counts.get("critical", 0),
            "warning": sev_counts.get("warning", 0),
            "info": sev_counts.get("info", 0),
        },
        "alerts": alerts,
    }


# ── Self-fix helpers ─────────────────────────────────────────────────────────

async def _trigger_poll_background(te_id: int) -> None:
    """Fire-and-forget: run a poll for one tracked event in its own DB session."""
    from app.scheduler import run_poll_for_tracked_event
    try:
        await run_poll_for_tracked_event(te_id)
    except Exception as exc:
        logger.warning("GAP_MONITOR: background poll failed te_id=%d — %s", te_id, exc)


async def _run_snapshot_fix(event_id: int) -> Optional[int]:
    """
    Write a canonical snapshot for event_id using a fresh DB session.
    Returns snapshot_id or None.
    """
    from app.services.canonical_inventory import snapshot_canonical_inventory
    async with AsyncSessionLocal() as fix_db:
        try:
            snap_id = await snapshot_canonical_inventory(event_id=event_id, db=fix_db)
            if snap_id:
                await fix_db.commit()
            return snap_id
        except Exception:
            await fix_db.rollback()
            raise


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/data-health/gaps")
async def get_gaps(db: AsyncSession = Depends(get_db)):
    """
    Scan all active events for collection, processing, snapshot, and live-stats gaps.
    Dispatches async self-fix tasks for safe recoverable gaps.
    Returns full alert array immediately (fixes run in background).
    """
    result = await _run_gap_scan(db, heal=True)
    return result


@router.post("/data-health/gaps/heal")
async def heal_gaps(db: AsyncSession = Depends(get_db)):
    """
    Same gap scan with synchronous self-fixes where possible.
    Snapshot fixes are applied inline (synchronous).
    Poll triggers are still async (backgrounded) to avoid HTTP timeout.
    Returns what changed.
    """
    result = await _run_gap_scan(db, heal=True)
    return result
