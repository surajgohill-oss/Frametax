import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_, update

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import TrackedEvent, Event, Listing, ListingSnapshot, PollRun, Marketplace
from app.collectors.registry import get_collector
from app.collectors.resolver import EventResolver

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler: AsyncIOScheduler | None = None


# ── Polling policy ─────────────────────────────────────────────────────────────
# Strict piecewise function. No smoothing, no interpolation.
#
# > 10 days before event  →  1440 min  (24 h)
# 10 days → 2 days        →   240 min  ( 4 h)
# 2 days → 8 hours        →    60 min  ( 1 h)
# 8 hours → event start   →    15 min
# event start → +5 min    →     5 min
# after +5 min            →  None  (deactivate)

def compute_poll_interval_minutes(event_date: datetime) -> int | None:
    seconds = (event_date - datetime.utcnow()).total_seconds()

    if seconds < -5 * 60:              # > 5 min past start → stop
        return None
    if seconds < 0:                    # within 5 min of start
        return 5
    if seconds < 8 * 3600:            # < 8 h
        return 15
    if seconds < 2 * 24 * 3600:      # < 2 days
        return 60
    if seconds < 10 * 24 * 3600:     # < 10 days
        return 240
    return 1440                        # >= 10 days


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
#   in_progress   : event started, within 5 min window
#   completed     : polling stopped (> 5 min past start)

_ADMISSION_DAYS = 21


def compute_lifecycle_phase(event_date: datetime) -> str:
    seconds = (event_date - datetime.utcnow()).total_seconds()
    if seconds < -5 * 60:
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
    _scheduler.start()
    logger.info(
        "Scheduler started — polling_policy=piecewise resolver=active "
        "discovery=6h lifecycle_phase=observability_only"
    )


async def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


# ── Resolver job ───────────────────────────────────────────────────────────────

async def _resolve_pending_event_ids():
    """Enrich TrackedEvents that have no external_event_id by searching marketplaces."""
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

    for te in due:
        asyncio.create_task(run_poll_for_tracked_event(te.id))


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

    try:
        result = await collector.collect(te)
        if result.error:
            logger.warning(
                "COLLECTOR_RESULT: slug=%s event_id=%d listings=%d "
                "error=%r external_event_id=%r",
                collector_slug, te.event_id, len(result.listings),
                result.error, te.external_event_id,
            )
        else:
            logger.info(
                "COLLECTOR_RESULT: slug=%s event_id=%d listings=%d "
                "external_event_id=%r",
                collector_slug, te.event_id, len(result.listings),
                te.external_event_id,
            )
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
        marketplace = (await db.execute(
            select(Marketplace).where(Marketplace.slug == result.marketplace_slug)
        )).scalar_one_or_none()
        if not marketplace:
            return

        existing_result = await db.execute(
            select(Listing).where(
                and_(
                    Listing.event_id == result.event_id,
                    Listing.marketplace_id == marketplace.id,
                    Listing.is_active == True,
                )
            )
        )
        existing: dict[str, Listing] = {
            l.external_listing_id: l for l in existing_result.scalars().all()
        }

        seen_ids: set[str] = set()
        new_count = 0
        snapshots: list[ListingSnapshot] = []
        collector = get_collector(result.marketplace_slug, settings)

        for raw in result.listings:
            try:
                norm_section = collector.normalize_section(raw.section) if collector else raw.section
            except Exception:
                norm_section = raw.section

            seen_ids.add(raw.external_listing_id)

            if raw.external_listing_id in existing:
                l = existing[raw.external_listing_id]
                l.price = raw.price
                l.fees = raw.fees
                l.all_in_price = raw.all_in_price
                l.quantity = raw.quantity
                l.last_seen_at = result.fetched_at
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

        disappeared = 0
        for ext_id, listing in existing.items():
            if ext_id not in seen_ids:
                listing.is_active = False
                disappeared += 1

        db.add_all(snapshots)

        poll_run = (await db.execute(
            select(PollRun).where(PollRun.id == poll_run_id)
        )).scalar_one_or_none()
        if poll_run:
            poll_run.completed_at = datetime.utcnow()
            poll_run.listings_found = len(result.listings)
            poll_run.new_listings = new_count
            poll_run.disappeared_listings = disappeared
            poll_run.status = "success" if not result.error else "error"
            poll_run.error_message = result.error

        await db.commit()
        logger.info(
            "COLLECTOR: poll event=%d %s listings=%d new=%d gone=%d",
            result.event_id, result.marketplace_slug,
            len(result.listings), new_count, disappeared,
        )
