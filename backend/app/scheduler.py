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


# ── Adaptive polling cadence ───────────────────────────────────────────────────
# > 14 days  → 360 min (6h)   prices stable, low value in frequent polling
# 14d → 48h  → 60 min         demand building, moderate tracking
# 48h → 6h   → 30 min         price movement accelerates
# 6h → 0     → 15 min         high volatility, inventory thinning fast
# in progress → 5 min         last-minute drops / inventory surges
# completed   → None           deactivate, stop polling

def compute_poll_interval_minutes(event_date: datetime) -> int | None:
    now = datetime.utcnow()
    seconds = (event_date - now).total_seconds()

    if seconds < -3 * 3600:        # > 3h past start → completed
        return None
    elif seconds < 0:               # past start, within 3h → in progress
        return 5
    elif seconds < 6 * 3600:       # < 6h away
        return 15
    elif seconds < 48 * 3600:      # < 48h away
        return 30
    elif seconds < 14 * 24 * 3600: # < 14 days
        return 60
    else:                           # > 14 days
        return 360


def event_status_from_date(event_date: datetime) -> str:
    seconds = (event_date - datetime.utcnow()).total_seconds()
    if seconds < -3 * 3600:
        return "completed"
    elif seconds < 0:
        return "in_progress"
    return "upcoming"


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
    )
    _scheduler.add_job(
        _resolve_pending_event_ids,
        trigger=IntervalTrigger(minutes=30),
        id="event_id_resolver",
        replace_existing=True,
        max_instances=1,
        next_run_time=datetime.utcnow(),  # run immediately on startup
    )
    _scheduler.start()
    logger.info("Scheduler started — adaptive polling + event ID resolver active")


async def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


# ── Core poll loop ─────────────────────────────────────────────────────────────

async def _resolve_pending_event_ids():
    """Enrich TrackedEvents that have no external_event_id by searching marketplaces."""
    resolver = EventResolver(settings)
    try:
        counts = await resolver.resolve_all_pending(AsyncSessionLocal)
        if counts["resolved"]:
            logger.info("ID resolution: %d resolved, %d failed", counts["resolved"], counts["failed"])
    finally:
        await resolver.close()


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

        # Log any events skipped due to pending Stage 2 resolution
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

    for te in due:
        asyncio.create_task(run_poll_for_tracked_event(te.id))


async def _update_event_statuses():
    """Recalculate event.status every 15 min; deactivate completed events."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event))
        for event in result.scalars().all():
            new_status = event_status_from_date(event.event_date)
            if event.status != new_status:
                event.status = new_status
                logger.info("Event %d '%s' status → %s", event.id, event.title, new_status)
            if new_status == "completed":
                await db.execute(
                    update(TrackedEvent)
                    .where(TrackedEvent.event_id == event.id, TrackedEvent.is_active == True)
                    .values(is_active=False)
                )
        await db.commit()


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
            if event:
                event.status = "completed"
            await db.commit()
            logger.info("Event %d completed — tracked_event %d deactivated", te.event_id, te.id)
            return

        if event:
            new_status = event_status_from_date(event.event_date)
            if event.status != new_status:
                event.status = new_status

        poll_run = PollRun(tracked_event_id=te.id, started_at=datetime.utcnow())
        db.add(poll_run)
        await db.flush()
        poll_run_id = poll_run.id

        te.last_polled_at = datetime.utcnow()
        te.poll_interval_minutes = interval
        te.next_poll_at = datetime.utcnow() + timedelta(minutes=interval)
        await db.commit()

    collector = get_collector(marketplace.slug, settings)
    if not collector:
        logger.warning("No collector registered for '%s'", marketplace.slug)
        return
    collector._db_session_factory = AsyncSessionLocal

    try:
        result = await collector.collect(te)
        await _process_result(result, te, poll_run_id)
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
            "Poll [event=%d %s]: %d listings, %d new, %d gone",
            result.event_id, result.marketplace_slug,
            len(result.listings), new_count, disappeared,
        )
