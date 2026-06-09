import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_, update

from app.utils.event_trace import emit_event_trace

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import TrackedEvent, Event, Listing, ListingSnapshot, PollRun, Marketplace
from app.collectors.registry import get_collector
from app.collectors.resolver import EventResolver
from app.collectors.normalize import is_parking_listing

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler: AsyncIOScheduler | None = None

# ── In-flight guard ────────────────────────────────────────────────────────────
# Prevents _check_due_events from spawning duplicate poll tasks for the same
# event_id.  Without this guard, each event has N marketplace-specific
# TrackedEvents that all appear "due" simultaneously, causing N full fan-outs
# (N × 6 collector calls) instead of 1.  The guard ensures exactly one poll
# task runs per event_id at a time.
_in_flight_event_ids: set[int] = set()

# ── Concurrency limiter ────────────────────────────────────────────────────────
# Caps simultaneous event polls to prevent thundering-herd OOM on startup.
# Without this, all N events with next_poll_at=None fire at once on the first
# scheduler tick: 27 events × 5 collectors = 135 concurrent calls + 27 large
# VividSeats snapshot batches = memory exhaustion -> SIGKILL.
# 4 concurrent polls × 5 collectors = 20 concurrent calls at peak.
_poll_semaphore: asyncio.Semaphore | None = None


def _get_poll_semaphore() -> asyncio.Semaphore:
    global _poll_semaphore
    if _poll_semaphore is None:
        _poll_semaphore = asyncio.Semaphore(4)
    return _poll_semaphore


# ── Polling policy ─────────────────────────────────────────────────────────────
# Canonical 12-tier cadence. Strict piecewise function. No smoothing.
#
# Countdown       Interval    Notes
# ─────────────   ────────    ──────────────────────────────────────────────────
# > 30 days       1440 min    once per day
# 14–30 days       720 min    twice per day
# 7–14 days        480 min    every 8 h
# 3–7 days         240 min    every 4 h
# 24 h–3 days       60 min    hourly
# 6–24 h             30 min    every 30 min
# 90 min–6 h         15 min    every 15 min
# 30–90 min           5 min    every 5 min
# 0–30 min            2 min    every 2 min
# event → +30 min     2 min    every 2 min (in-progress window)
# after +30 min       None     stop — deactivate tracked_event
#
# DO NOT reintroduce +2h polling. Stop is at +30 min, not +2 h.

def compute_poll_interval_minutes(event_date: datetime) -> int | None:
    seconds = (event_date - datetime.utcnow()).total_seconds()

    # Past the +30 min post-event window → stop polling
    if seconds < -30 * 60:
        return None

    # 0 → +30 min (event in-progress window)
    if seconds < 0:
        return 2

    # 0–30 min before event
    if seconds < 30 * 60:
        return 2

    # 30–90 min before event
    if seconds < 90 * 60:
        return 5

    # 90 min–6 h before event
    if seconds < 6 * 3600:
        return 15

    # 6–24 h before event
    if seconds < 24 * 3600:
        return 30

    # 24 h–3 days before event
    if seconds < 3 * 24 * 3600:
        return 60

    # 3–7 days before event
    if seconds < 7 * 24 * 3600:
        return 240

    # 7–14 days before event
    if seconds < 14 * 24 * 3600:
        return 480

    # 14–30 days before event
    if seconds < 30 * 24 * 3600:
        return 720

    # > 30 days before event
    return 1440


# ── Event status (display) ─────────────────────────────────────────────────────
# events.status is for UI display only. Uses a longer completed window (3 h)
# so the event card doesn't vanish the moment polling stops.

def event_status_from_date(event_date: datetime) -> str:
    seconds = (event_date - datetime.utcnow()).total_seconds()
    if seconds < -3 * 3600:
        return "completed"
    if seconds < 0:
        return "in_progress"
    return "upcoming"


# ── Lifecycle phase (observability) ───────────────────────────────────────────
# tracked_events.lifecycle_phase is observability-only. It does NOT gate
# polling. Polling is exclusively controlled by compute_poll_interval_minutes.
#
# Thresholds:
#   pre_admission : event > 21 days away (discovery hasn't admitted it yet)
#   active        : event within 21 days (being tracked and polled)
#   in_progress   : event started, within +30 min window (mirrors poll stop)
#   completed     : polling stopped (> +30 min past start)

_ADMISSION_DAYS = 21


def compute_lifecycle_phase(event_date: datetime) -> str:
    seconds = (event_date - datetime.utcnow()).total_seconds()
    if seconds < -30 * 60:        # > +30 min past start → completed (matches poll stop)
        return "completed"
    if seconds < 0:
        return "in_progress"
    if seconds < _ADMISSION_DAYS * 24 * 3600:
        return "active"
    return "pre_admission"


# ── Scheduler lifecycle ────────────────────────────────────────────────────────

async def start_scheduler():
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _check_due_events,
        trigger=IntervalTrigger(minutes=1),
        id="master_poll_check",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        _update_event_statuses,
        trigger=IntervalTrigger(minutes=15),
        id="event_status_updater",
        replace_existing=True,
        max_instances=1,
        next_run_time=datetime.utcnow(),  # populate lifecycle_phase immediately on startup
    )
    _scheduler.add_job(
        _resolve_pending_event_ids,
        trigger=IntervalTrigger(minutes=30),
        id="event_id_resolver",
        replace_existing=True,
        max_instances=1,
        next_run_time=datetime.utcnow(),
    )
    _scheduler.add_job(
        _run_event_discovery,
        trigger=IntervalTrigger(hours=6),
        id="event_discovery",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        _run_retention_maintenance,
        trigger=IntervalTrigger(hours=6),
        id="retention_maintenance",
        replace_existing=True,
        max_instances=1,
        next_run_time=datetime.utcnow() + timedelta(minutes=30),  # 30 min after startup
    )
    _scheduler.start()
    logger.info(
        "Scheduler started — polling_policy=piecewise resolver=active "
        "discovery=6h lifecycle_phase=observability_only"
    )


async def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


# ── StubHub cookie bootstrap ───────────────────────────────────────────────────

async def _bootstrap_stubhub_session_if_needed() -> None:
    """Ensure StubHub browser cookies exist before the SOLR resolver runs.

    After a Railway deploy the ephemeral filesystem is wiped, so
    browser_sessions/stubhub/cookies.json is gone.  The StubHub SOLR API
    returns 404 without browser-session cookies, making the resolver useless
    for the first 30-minute cycle.

    This function detects a missing cookies.json and triggers a single minimal
    Playwright navigation against a known, stable upcoming event to re-create
    the session.  The listing results are discarded — only the cookies matter.

    Bootstrap anchor: Rush @ Kia Forum 2026-06-11 / StubHub ID 159580568
    (188 active listings as of 2026-06-07; slug URL confirmed working)
    """
    from pathlib import Path
    cookie_path = Path(settings.browser_data_dir) / "stubhub" / "cookies.json"
    if cookie_path.exists():
        logger.debug("STUBHUB_BOOTSTRAP: cookies.json present — skipping")
        return

    logger.info("STUBHUB_BOOTSTRAP: cookies.json missing after deploy — running bootstrap Playwright navigation")
    try:
        from app.collectors.stubhub import StubHubCollector
        collector = StubHubCollector(settings)
        _BOOTSTRAP_EVENT_ID = "159580568"
        _BOOTSTRAP_URL = "https://www.stubhub.com/rush-inglewood-tickets-6-11-2026/event/159580568/"
        listings = await collector._fetch_via_playwright(_BOOTSTRAP_EVENT_ID, _BOOTSTRAP_URL)
        logger.info(
            "STUBHUB_BOOTSTRAP: complete — %d listing(s) captured; cookies.json written",
            len(listings),
        )
    except Exception as exc:
        logger.warning(
            "STUBHUB_BOOTSTRAP: Playwright navigation failed — %s; "
            "SOLR resolver may return 404 this cycle",
            exc,
        )


# ── Resolver job ───────────────────────────────────────────────────────────────

async def _resolve_pending_event_ids():
    """Enrich TrackedEvents that have no external_event_id by searching marketplaces."""
    await _bootstrap_stubhub_session_if_needed()
    resolver = EventResolver(settings)
    try:
        counts = await resolver.resolve_all_pending(AsyncSessionLocal)
        if counts["resolved"] or counts["failed"]:
            logger.info(
                "RESOLVER: scheduler cycle resolved=%d failed=%d already_set=%d",
                counts["resolved"], counts["failed"], counts["already_set"],
            )
    finally:
        await resolver.close()


# ── Poll gate ──────────────────────────────────────────────────────────────────

async def _check_due_events():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TrackedEvent).where(
                and_(
                    TrackedEvent.is_active == True,
                    TrackedEvent.external_event_id.is_not(None),  # Stage 2 must be complete
                    (TrackedEvent.next_poll_at <= datetime.utcnow())
                    | (TrackedEvent.next_poll_at.is_(None)),
                )
            )
        )
        due = result.scalars().all()

        pending_result = await db.execute(
            select(TrackedEvent).where(
                and_(
                    TrackedEvent.is_active == True,
                    TrackedEvent.external_event_id.is_(None),
                )
            )
        )
        pending = pending_result.scalars().all()
        if pending:
            logger.info(
                "STAGE_GATE: %d tracked_event(s) skipped — awaiting Stage 2 resolution "
                "(ids: %s)",
                len(pending), [te.id for te in pending],
            )

        if due:
            logger.info(
                "STAGE_GATE: %d tracked_event(s) due for polling — "
                "%s",
                len(due),
                [
                    f"te={te.id} event={te.event_id} mp={te.marketplace_id} "
                    f"eid={te.external_event_id!r}"
                    for te in due
                ],
            )

    seen_event_ids: set[int] = set()
    for te in due:
        if te.event_id in _in_flight_event_ids:
            logger.debug(
                "POLL_GATE: event_id=%d already in-flight — skipping duplicate te=%d",
                te.event_id, te.id,
            )
            continue
        if te.event_id in seen_event_ids:
            logger.debug(
                "POLL_GATE: event_id=%d already scheduled this tick — skipping te=%d",
                te.event_id, te.id,
            )
            continue
        seen_event_ids.add(te.event_id)
        _in_flight_event_ids.add(te.event_id)
        asyncio.create_task(_poll_with_inflight_guard(te.id, te.event_id))

    if seen_event_ids:
        logger.info(
            "POLL_GATE: dispatched %d event poll(s) this tick — event_ids=%s",
            len(seen_event_ids), sorted(seen_event_ids),
        )


async def _poll_with_inflight_guard(tracked_event_id: int, event_id: int):
    """Wrapper that rate-limits concurrent polls and releases the in-flight guard."""
    sem = _get_poll_semaphore()
    try:
        async with sem:
            logger.debug("POLL_GATE: event_id=%d acquired semaphore (slot used)", event_id)
            await run_poll_for_tracked_event(tracked_event_id)
    finally:
        _in_flight_event_ids.discard(event_id)
        logger.debug("POLL_GATE: event_id=%d released", event_id)


# ── Status + lifecycle updater ─────────────────────────────────────────────────

async def _update_event_statuses():
    """
    Runs every 15 min.
    - Writes events.status (display)
    - Writes tracked_events.lifecycle_phase (observability)
    - Deactivates tracked_events for completed events (safety net — the poll
      loop deactivates them first via compute_poll_interval_minutes → None)
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event))
        for event in result.scalars().all():
            new_status = event_status_from_date(event.event_date)
            if event.status != new_status:
                event.status = new_status
                logger.info("EVENT: %d '%s' status → %s", event.id, event.title, new_status)

            new_phase = compute_lifecycle_phase(event.event_date)

            if new_phase == "completed":
                # Deactivate any still-active tracked_events (belt + suspenders)
                await db.execute(
                    update(TrackedEvent)
                    .where(
                        TrackedEvent.event_id == event.id,
                        TrackedEvent.is_active == True,
                    )
                    .values(is_active=False, lifecycle_phase="completed")
                )
            else:
                # Write lifecycle_phase for observability
                await db.execute(
                    update(TrackedEvent)
                    .where(TrackedEvent.event_id == event.id)
                    .values(lifecycle_phase=new_phase)
                )

        await db.commit()


# ── Retention maintenance job ──────────────────────────────────────────────────
#
# Runs every 6 h. Enforces tiered raw listing_snapshot retention:
#
#   Completed / inactive events  → archive all raw snapshots to local CSV.gz, delete all
#   > 30d away                   → keep latest 48 h + one daily sample per day, delete rest
#   14–30d away                  → keep last 7d, delete older
#   7–14d away                   → keep last 14d, delete older
#   < 7d away                    → keep all (no deletion)
#
# Never touches: canonical_inventory_snapshots, canonical_block_history, listings.
# Archives written to /tmp/retention_archives/ (ephemeral on Railway — local only).
# The archive step is best-effort: if the filesystem is full, deletion still proceeds
# so storage is never blocked by archival I/O.
#
# "One daily sample" for >30d events: the row whose snapshot_at is closest to midnight
# UTC for each calendar day in the 48h–30d window.

async def _run_retention_maintenance():
    import csv
    import gzip
    import io
    import os
    from pathlib import Path
    import asyncpg

    db_url = settings.database_url  # SQLAlchemy async URL
    # Convert to sync psycopg2 URL for raw bulk operations
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")

    logger.info("RETENTION: starting maintenance cycle")

    try:
        import psycopg2
    except ImportError:
        logger.warning("RETENTION: psycopg2 not available — skipping")
        return

    try:
        conn = psycopg2.connect(sync_url)
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as exc:
        logger.error("RETENTION: DB connect failed — %s", exc)
        return

    now = datetime.utcnow()
    archive_root = Path("/tmp/retention_archives") / now.strftime("%Y%m%d_%H%M%S")

    total_deleted = 0

    try:
        # Fetch all events with snapshots
        cur.execute("""
            SELECT e.id, e.title, e.event_date, e.status,
                   COUNT(ls.id) AS snap_count
            FROM events e
            JOIN listing_snapshots ls ON ls.event_id = e.id
            GROUP BY e.id, e.title, e.event_date, e.status
            HAVING COUNT(ls.id) > 0
            ORDER BY e.event_date
        """)
        events = cur.fetchall()

        for (eid, title, event_date, status, snap_count) in events:
            if isinstance(event_date, str):
                from datetime import datetime as dt
                event_date = dt.fromisoformat(event_date)

            seconds_to_event = (event_date - now).total_seconds()
            days_to_event = seconds_to_event / 86400

            # Determine action
            if status in ("completed", "inactive", "cancelled") or seconds_to_event < 0:
                # Archive all, delete all
                tier = "completed"
                cutoff = None  # delete ALL
            elif days_to_event > 30:
                # Keep last 48h + one sample per day beyond that
                tier = ">30d"
                cutoff = now - timedelta(hours=48)
            elif days_to_event > 14:
                tier = "14-30d"
                cutoff = now - timedelta(days=7)
            elif days_to_event > 7:
                tier = "7-14d"
                cutoff = now - timedelta(days=14)
            else:
                # <7d — keep all
                continue

            # Count rows to delete
            if cutoff is None:
                cur.execute("SELECT COUNT(*) FROM listing_snapshots WHERE event_id = %s", (eid,))
            else:
                if tier == ">30d":
                    # Keep: last 48h (snapshot_at >= cutoff) + one row per calendar day
                    # Delete: rows older than 48h that are NOT the daily representative
                    cur.execute("""
                        SELECT COUNT(*) FROM listing_snapshots ls
                        WHERE ls.event_id = %s
                          AND ls.snapshot_at < %s
                          AND ls.id NOT IN (
                              SELECT DISTINCT ON (DATE(snapshot_at)) id
                              FROM listing_snapshots
                              WHERE event_id = %s AND snapshot_at < %s
                              ORDER BY DATE(snapshot_at), snapshot_at
                          )
                    """, (eid, cutoff, eid, cutoff))
                else:
                    cur.execute(
                        "SELECT COUNT(*) FROM listing_snapshots WHERE event_id = %s AND snapshot_at < %s",
                        (eid, cutoff),
                    )

            to_delete = cur.fetchone()[0]
            if to_delete == 0:
                continue

            # Best-effort archive (write to /tmp — ephemeral on Railway)
            archived = 0
            try:
                archive_root.mkdir(parents=True, exist_ok=True)
                event_dir = archive_root / f"event_{eid}_{str(event_date)[:10]}"
                event_dir.mkdir(exist_ok=True)
                gz_path = event_dir / "listing_snapshots.csv.gz"

                # Use a dedicated connection with autocommit=False for named cursor
                arc_conn = psycopg2.connect(sync_url)
                arc_conn.autocommit = False
                arc_cur_name = f"arc_{eid}_{int(now.timestamp())}"
                arc_cur = arc_conn.cursor(arc_cur_name)

                ls_cols = ["id", "event_id", "marketplace_id", "listing_id", "section_id",
                           "price", "quantity", "snapshot_at", "fees", "all_in_price", "market_segment"]
                if cutoff is None:
                    arc_cur.execute(
                        f"SELECT {', '.join(ls_cols)} FROM listing_snapshots WHERE event_id = %s",
                        (eid,),
                    )
                else:
                    arc_cur.execute(
                        f"SELECT {', '.join(ls_cols)} FROM listing_snapshots WHERE event_id = %s AND snapshot_at < %s",
                        (eid, cutoff),
                    )

                buf = io.BytesIO()
                with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
                    import io as _io
                    wrapper = _io.TextIOWrapper(gz, newline="", write_through=True)
                    writer = csv.writer(wrapper)
                    writer.writerow(ls_cols)
                    while True:
                        rows = arc_cur.fetchmany(5000)
                        if not rows:
                            break
                        for row in rows:
                            writer.writerow(list(row))
                            archived += 1
                    wrapper.detach()

                arc_cur.close()
                arc_conn.rollback()
                arc_conn.close()
                gz_path.write_bytes(buf.getvalue())
            except Exception as arc_exc:
                logger.warning("RETENTION: archive failed event=%d — %s (proceeding with delete)", eid, arc_exc)

            # Delete
            if cutoff is None:
                cur.execute("DELETE FROM listing_snapshots WHERE event_id = %s", (eid,))
            elif tier == ">30d":
                cur.execute("""
                    DELETE FROM listing_snapshots
                    WHERE event_id = %s
                      AND snapshot_at < %s
                      AND id NOT IN (
                          SELECT DISTINCT ON (DATE(snapshot_at)) id
                          FROM listing_snapshots
                          WHERE event_id = %s AND snapshot_at < %s
                          ORDER BY DATE(snapshot_at), snapshot_at
                      )
                """, (eid, cutoff, eid, cutoff))
            else:
                cur.execute(
                    "DELETE FROM listing_snapshots WHERE event_id = %s AND snapshot_at < %s",
                    (eid, cutoff),
                )

            deleted = cur.rowcount
            total_deleted += deleted
            logger.info(
                "RETENTION: event=%d '%s' tier=%s snap_count=%d archived=%d deleted=%d",
                eid, title[:40], tier, snap_count, archived, deleted,
            )

        if total_deleted > 0:
            cur.execute("VACUUM ANALYZE listing_snapshots")
            cur.execute("SELECT COUNT(*) FROM listing_snapshots")
            final_count = cur.fetchone()[0]
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cur.fetchone()[0]
            logger.info(
                "RETENTION: cycle complete total_deleted=%d listing_snapshots=%d db=%s",
                total_deleted, final_count, db_size,
            )
        else:
            logger.info("RETENTION: cycle complete — nothing to prune")

    except Exception as exc:
        logger.exception("RETENTION: maintenance cycle failed — %s", exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ── Discovery job ──────────────────────────────────────────────────────────────

async def _run_event_discovery():
    """Scan marketplaces for new events within the admission window (14–21 days out)."""
    from app.collectors.discovery import EventDiscovery
    discovery = EventDiscovery(settings)
    try:
        counts = await discovery.run_discovery(AsyncSessionLocal)
        logger.info(
            "DISCOVERY: cycle complete new=%d duplicate=%d outside_window=%d "
            "no_venue=%d failed=%d",
            counts["new"], counts["duplicate"], counts["outside_window"],
            counts["no_venue"], counts["failed"],
        )
    except Exception as exc:
        logger.exception("DISCOVERY: cycle failed — %s", exc)
    finally:
        await discovery.close()


# ── Single event poll ──────────────────────────────────────────────────────────

async def run_poll_for_tracked_event(tracked_event_id: int):
    async with AsyncSessionLocal() as db:
        te = (await db.execute(
            select(TrackedEvent).where(TrackedEvent.id == tracked_event_id)
        )).scalar_one_or_none()
        if not te:
            return

        event = (await db.execute(
            select(Event).where(Event.id == te.event_id)
        )).scalar_one_or_none()

        marketplace = (await db.execute(
            select(Marketplace).where(Marketplace.id == te.marketplace_id)
        )).scalar_one_or_none()
        if not marketplace:
            return

        interval = compute_poll_interval_minutes(event.event_date) if event else te.poll_interval_minutes

        if interval is None:
            te.is_active = False
            te.lifecycle_phase = "completed"
            if event:
                event.status = event_status_from_date(event.event_date)
            await db.commit()
            logger.info(
                "POLLING: tracked_event=%d event='%s' deactivated — past cutoff",
                te.id, event.title if event else te.event_id,
            )
            return

        if event:
            new_status = event_status_from_date(event.event_date)
            if event.status != new_status:
                event.status = new_status
            te.lifecycle_phase = compute_lifecycle_phase(event.event_date)

        te.last_polled_at = datetime.utcnow()
        te.poll_interval_minutes = interval
        te.next_poll_at = datetime.utcnow() + timedelta(minutes=interval)
        await db.commit()

    # Fan out to every registered collector — all marketplaces, full isolation.
    from app.collectors.registry import COLLECTOR_REGISTRY
    collector_slugs = list(COLLECTOR_REGISTRY.keys())
    event_title = event.title if event else str(te.event_id)
    logger.info(
        "POLLING: event_id=%d '%s' dispatching to %d collector(s): [%s]",
        te.event_id, event_title, len(collector_slugs), ", ".join(collector_slugs),
    )
    await asyncio.gather(
        *[_run_collector_for_event(slug, te, event) for slug in collector_slugs],
        return_exceptions=True,
    )


async def _run_collector_for_event(collector_slug: str, source_te: TrackedEvent, event):
    """
    Load (or lazily create) the collector's own marketplace-scoped TrackedEvent,
    then run that collector using its own external_event_id.

    Each invocation gets its own PollRun row. A missing external_event_id causes
    the collector's resolve_external_event_id() fallback to fire (marketplace-
    specific search). Exceptions are caught — a failing collector does not block
    sibling collectors.
    """
    collector = get_collector(collector_slug, settings)
    if not collector:
        logger.debug("POLLING: no collector registered for '%s' — skipping", collector_slug)
        return
    collector._db_session_factory = AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        mp = (await db.execute(
            select(Marketplace).where(Marketplace.slug == collector_slug)
        )).scalar_one_or_none()
        if not mp:
            logger.warning(
                "COLLECTOR_DISPATCH: no marketplace row for slug=%s — skipping", collector_slug
            )
            return

        te = (await db.execute(
            select(TrackedEvent).where(
                TrackedEvent.event_id == source_te.event_id,
                TrackedEvent.marketplace_id == mp.id,
            )
        )).scalar_one_or_none()

        if not te:
            te = TrackedEvent(
                event_id=source_te.event_id,
                marketplace_id=mp.id,
                external_url=None,
                external_event_id=None,
                resolution_source=None,
                is_active=True,
                poll_interval_minutes=source_te.poll_interval_minutes,
                next_poll_at=None,
            )
            db.add(te)
            await db.flush()
            logger.info(
                "COLLECTOR_DISPATCH: created TrackedEvent te_id=%d mp=%s event_id=%d",
                te.id, collector_slug, source_te.event_id,
            )

        poll_run = PollRun(tracked_event_id=te.id, started_at=datetime.utcnow())
        db.add(poll_run)
        await db.flush()
        poll_run_id = poll_run.id
        await db.commit()

    # Attach Event object so resolver fallbacks can access event.title / event_date
    te.event = event

    logger.info(
        "COLLECTOR_DISPATCH: slug=%s te_id=%d event_id=%d "
        "mp_id=%d external_event_id=%r",
        collector_slug, te.id, te.event_id,
        te.marketplace_id, te.external_event_id,
    )

    # Guard: StubHub Playwright requires external_url to load the correct event
    # page (bare /event/{id} works but slug URL is preferred).  If external_url
    # is NULL after Stage 2 resolution, synthesize a bare URL so the collector
    # never navigates blind.  Log ONBOARDING_INCOMPLETE so ops can notice.
    if collector_slug == "stubhub" and te.external_event_id and not te.external_url:
        bare_url = f"https://www.stubhub.com/event/{te.external_event_id}/"
        logger.warning(
            "ONBOARDING_INCOMPLETE: StubHub te=%d event_id=%d has external_event_id=%r "
            "but external_url=NULL — synthesizing bare URL %s. "
            "Resolve the slug URL and backfill external_url for best results.",
            te.id, te.event_id, te.external_event_id, bare_url,
        )
        te.external_url = bare_url
    emit_event_trace("SCHEDULER", te.event_id, {
        "tracked_event_id": te.id,
        "external_event_id": te.external_event_id,
        "marketplace": collector_slug,
    })

    try:
        result = await collector.collect(te)
        listings_count = len(result.listings)
        if result.error:
            logger.warning(
                "COLLECTOR_RESULT: slug=%s event_id=%d listings=%d "
                "error=%r external_event_id=%r",
                collector_slug, te.event_id, listings_count,
                result.error, te.external_event_id,
            )
        else:
            logger.info(
                "COLLECTOR_RESULT: slug=%s event_id=%d listings=%d "
                "external_event_id=%r",
                collector_slug, te.event_id, listings_count,
                te.external_event_id,
            )
        emit_event_trace("COLLECT", te.event_id, {
            "tracked_event_id": te.id,
            "external_event_id": te.external_event_id,
            "marketplace": collector_slug,
            "listings_count": listings_count,
            "error": result.error,
        })
        await _process_result(result, te, poll_run_id)
    except Exception as exc:
        logger.exception(
            "COLLECTOR_EXCEPTION: slug=%s event_id=%d "
            "external_event_id=%r exc_type=%s — %s",
            collector_slug, te.event_id,
            te.external_event_id, type(exc).__name__, exc,
        )
    finally:
        await collector.close()


# ── Result processing ──────────────────────────────────────────────────────────

async def _process_result(result, te: TrackedEvent, poll_run_id: int):
    async with AsyncSessionLocal() as db:
        # Resolve this result's marketplace — all reads and writes below are
        # scoped to this marketplace_id. No other marketplace's listings are
        # ever touched by this invocation.
        marketplace = (await db.execute(
            select(Marketplace).where(Marketplace.slug == result.marketplace_slug)
        )).scalar_one_or_none()
        if not marketplace:
            return

        # ── Scope: only listings owned by THIS marketplace ────────────────────
        # Invariant: existing contains ONLY rows where
        #   event_id == result.event_id AND marketplace_id == marketplace.id
        # A collector from any other marketplace cannot affect these rows.
        #
        # Query ALL listings regardless of is_active so that previously-deactivated
        # listings can be reactivated rather than re-inserted.  Inserting a new row
        # for a previously-seen (event_id, marketplace_id, external_listing_id)
        # would violate the UNIQUE constraint added in migration 0001.
        existing_result = await db.execute(
            select(Listing).where(
                and_(
                    Listing.event_id == result.event_id,
                    Listing.marketplace_id == marketplace.id,
                )
            )
        )
        all_known_listings = existing_result.scalars().all()
        existing: dict[str, Listing] = {
            l.external_listing_id: l for l in all_known_listings
        }
        # Track which were active before this poll so the disappeared calculation
        # only deactivates rows that were previously live.
        was_active: set[str] = {
            l.external_listing_id for l in all_known_listings if l.is_active
        }

        # seen_ids is populated exclusively from this collector's returned
        # listings — it never contains IDs from another marketplace.
        seen_ids: set[str] = set()
        new_count = 0
        parking_dropped = 0
        snapshots: list[ListingSnapshot] = []
        collector = get_collector(result.marketplace_slug, settings)

        # ── Parking pre-filter ────────────────────────────────────────────────
        # Drop parking passes before any upsert so they never enter the
        # listings table.  Applied to ALL sources (Railway collectors AND
        # Mac-host manual-ingest scripts that POST to /api/poll/.../manual-ingest)
        # because this is the single shared ingestion choke-point.
        clean_listings = []
        for raw in result.listings:
            if is_parking_listing(raw.section, raw.row):
                parking_dropped += 1
                logger.debug(
                    "PARKING_FILTER: dropped section=%r row=%r event_id=%d %s",
                    raw.section, raw.row, result.event_id, result.marketplace_slug,
                )
            else:
                clean_listings.append(raw)

        if parking_dropped:
            logger.info(
                "PARKING_FILTER: dropped %d parking listing(s) event_id=%d %s",
                parking_dropped, result.event_id, result.marketplace_slug,
            )

        for raw in clean_listings:
            try:
                norm_section = collector.normalize_section(raw.section) if collector else raw.section
            except Exception:
                norm_section = raw.section

            seen_ids.add(raw.external_listing_id)

            if raw.external_listing_id in existing:
                # Update existing row — reactivate if it was previously deactivated.
                l = existing[raw.external_listing_id]
                l.price = raw.price
                l.fees = raw.fees
                l.all_in_price = raw.all_in_price
                l.quantity = raw.quantity
                l.last_seen_at = result.fetched_at
                if not l.is_active:
                    l.is_active = True   # reactivate; do not increment new_count
            else:
                l = Listing(
                    event_id=result.event_id,
                    marketplace_id=marketplace.id,
                    external_listing_id=raw.external_listing_id,
                    section=raw.section,
                    section_id=norm_section,
                    row=raw.row,
                    quantity=raw.quantity,
                    price=raw.price,
                    fees=raw.fees,
                    all_in_price=raw.all_in_price,
                    listing_url=raw.listing_url,
                    market_segment=raw.market_segment,
                    first_seen_at=result.fetched_at,
                    last_seen_at=result.fetched_at,
                    extra=raw.extra,
                )
                db.add(l)
                await db.flush()
                new_count += 1

            snapshots.append(ListingSnapshot(
                listing_id=l.id,
                event_id=result.event_id,
                marketplace_id=marketplace.id,
                section_id=norm_section,
                quantity=raw.quantity,
                price=raw.price,
                fees=raw.fees,
                all_in_price=raw.all_in_price,
                market_segment=raw.market_segment,
                snapshot_at=result.fetched_at,
            ))

        # Retire listings that were active before this poll but absent from it.
        # Use was_active (pre-poll snapshot) rather than existing so that already-
        # inactive rows are not double-counted and inactive rows introduced by
        # concurrent collectors are left alone.
        #
        # Safety rule: only retire when the collector returned real results.
        # An empty result (API failure, unresolvable ID, rate-limit, partial error)
        # is indistinguishable from a genuine "0 listings" response, so we preserve
        # all existing rows rather than bulk-deactivating on ambiguous evidence.
        # Note: we use clean_listings (post-filter) for the retirement check so that
        # a poll returning only parking listings is still treated as a real result.
        disappeared = 0
        if result.listings:
            for ext_id in was_active:
                if ext_id not in seen_ids:
                    existing[ext_id].is_active = False
                    disappeared += 1
        elif existing:
            logger.warning(
                "RECONCILE: collector=%s event_id=%d returned 0 listings — "
                "preserving %d existing listing(s), no deactivation",
                result.marketplace_slug, result.event_id, len(existing),
            )

        db.add_all(snapshots)

        poll_run = (await db.execute(
            select(PollRun).where(PollRun.id == poll_run_id)
        )).scalar_one_or_none()
        if poll_run:
            poll_run.completed_at = datetime.utcnow()
            poll_run.listings_found = len(clean_listings)
            poll_run.new_listings = new_count
            poll_run.disappeared_listings = disappeared
            poll_run.parking_dropped = parking_dropped
            poll_run.status = "success" if not result.error else "error"
            poll_run.error_message = result.error

        await db.commit()
        emit_event_trace("DB_WRITE", result.event_id, {
            "external_event_id": te.external_event_id,
            "tracked_event_id": te.id,
            "marketplace": result.marketplace_slug,
            "listings_count": new_count,
            "total_active": len(clean_listings),
            "parking_dropped": parking_dropped,
            "disappeared": disappeared,
        })
        logger.info(
            "COLLECTOR: poll event=%d %s listings=%d new=%d gone=%d parking_dropped=%d",
            result.event_id, result.marketplace_slug,
            len(clean_listings), new_count, disappeared, parking_dropped,
        )

        # ── Phase 3B: canonical snapshot (runs after listings are committed) ──
        # Writes one row to canonical_inventory_snapshots per successful poll.
        # Failure here is non-fatal — poll result is already committed above.
        try:
            from app.services.canonical_inventory import snapshot_canonical_inventory
            snap_id = await snapshot_canonical_inventory(
                event_id=result.event_id,
                db=db,
                poll_run_id=poll_run_id,
            )
            if snap_id:
                await db.commit()  # flush() inside snapshot_canonical_inventory — must commit here
                logger.info("CANONICAL: event=%d snap_id=%d written", result.event_id, snap_id)
        except Exception as canon_exc:
            await db.rollback()
            logger.warning(
                "CANONICAL: snapshot failed event=%d — %s (poll result unaffected)",
                result.event_id, canon_exc,
            )
