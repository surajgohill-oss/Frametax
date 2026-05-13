import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import TrackedEvent, Listing, ListingSnapshot, PollRun, Marketplace
from app.collectors.registry import get_collector

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler: AsyncIOScheduler | None = None


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
    _scheduler.start()
    logger.info("Scheduler started")


async def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


async def _check_due_events():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TrackedEvent).where(
                and_(
                    TrackedEvent.is_active == True,
                    (TrackedEvent.next_poll_at <= datetime.utcnow())
                    | (TrackedEvent.next_poll_at.is_(None)),
                )
            )
        )
        due = result.scalars().all()
    for te in due:
        asyncio.create_task(run_poll_for_tracked_event(te.id))


async def run_poll_for_tracked_event(tracked_event_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TrackedEvent).where(TrackedEvent.id == tracked_event_id))
        te = result.scalar_one_or_none()
        if not te:
            return
        mp_result = await db.execute(select(Marketplace).where(Marketplace.id == te.marketplace_id))
        marketplace = mp_result.scalar_one_or_none()
        if not marketplace:
            return

        poll_run = PollRun(tracked_event_id=te.id, started_at=datetime.utcnow())
        db.add(poll_run)
        await db.flush()
        poll_run_id = poll_run.id
        te.last_polled_at = datetime.utcnow()
        te.next_poll_at = datetime.utcnow() + timedelta(minutes=te.poll_interval_minutes)
        await db.commit()

    collector = get_collector(marketplace.slug, settings)
    if not collector:
        return
    collector._db_session_factory = AsyncSessionLocal

    try:
        result = await collector.collect(te)
        await _process_result(result, te, poll_run_id)
    finally:
        await collector.close()


async def _process_result(result, te: TrackedEvent, poll_run_id: int):
    async with AsyncSessionLocal() as db:
        mp_result = await db.execute(
            select(Marketplace).where(Marketplace.slug == result.marketplace_slug)
        )
        marketplace = mp_result.scalar_one_or_none()
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

        pr_result = await db.execute(select(PollRun).where(PollRun.id == poll_run_id))
        poll_run = pr_result.scalar_one_or_none()
        if poll_run:
            poll_run.completed_at = datetime.utcnow()
            poll_run.listings_found = len(result.listings)
            poll_run.new_listings = new_count
            poll_run.disappeared_listings = disappeared
            poll_run.status = "success" if not result.error else "error"
            poll_run.error_message = result.error

        await db.commit()
        logger.info(
            "Poll done: %d listings, %d new, %d gone",
            len(result.listings), new_count, disappeared,
        )
