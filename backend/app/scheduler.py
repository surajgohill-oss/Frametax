import asyncio
import logging
from datetime import datetime, timedelta, timezone

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

# Number of consecutive successful zero-inventory polls required post-start
# before an event is considered exhausted and marked completed.
_EXHAUSTION_THRESHOLD = 5


# ── Polling cadence ────────────────────────────────────────────────────────────
# Strict piecewise function.  Always returns a positive integer — NEVER None.
# Deactivation is handled exclusively by inventory-exhaustion logic in
# _process_result(), which fires only after event_start has passed.
#
# Pre-event zero inventory does NOT trigger completion — it indicates collector
# failure, marketplace outage, anti-bot blocks, or temporary delisting.
#
#  > 30 days   →  1440 min  (daily)
#  14–30 days  →   720 min  (12 h)
#   7–14 days  →   480 min  ( 8 h)
#    3–7 days  →   240 min  ( 4 h)
#   24h–3d     →    60 min  ( 1 h)
#    6h–24h    →    30 min
#   90m–6h     →    15 min
#   30–90m     →     5 min
#    0–30m     →     2 min
#  post-start  →     2 min  (until exhaustion confirmed)

def compute_poll_interval_minutes(event_date: datetime) -> int:
    seconds = (event_date - datetime.now(timezone.utc)).total_seconds()

    if seconds < 0:                          # post-start  → LIVE polling
        return 2
    if seconds < 30 * 60:                    # 0–30 min
        return 2
    if seconds < 90 * 60:                    # 30–90 min
        return 5
    if seconds < 6 * 3600:                   # 90 min – 6 h
        return 15
    if seconds < 24 * 3600:                  # 6–24 h
        return 30
    if seconds < 3 * 24 * 3600:             # 1–3 days
        return 60
    if seconds < 7 * 24 * 3600:             # 3–7 days
        return 240
    if seconds < 14 * 24 * 3600:            # 7–14 days
        return 480
    if seconds < 30 * 24 * 3600:            # 14–30 days
        return 720
    return 1440                               # > 30 days → daily


# ── Event display status ───────────────────────────────────────────────────────
# events.status drives UI display only.  Uses a 3-hour grace window so the
# event card remains visible after showtime.

def event_status_from_date(event_date: datetime) -> str:
    seconds = (event_date - datetime.now(timezone.utc)).total_seconds()
    if seconds < -3 * 3600:
        return "completed"
    if seconds < 0:
        return "in_progress"
    return "upcoming"


# ── Lifecycle phase ────────────────────────────────────────────────────────────
# tracked_events.lifecycle_phase is observability-only metadata.
# It does NOT gate polling; polling is controlled by is_active.
#
# Phases:
#   pre_admission    — event > 21 days out (discovery not yet admitted)
#   active           — within 21 days, before event_start
#   live             — post-start, inventory still being found
#   exhaustion_pending — post-start, 1–4 consecutive zero cycles
#   completed        — 5 consecutive zero cycles after event_start

_ADMISSION_DAYS = 21


def compute_lifecycle_phase(event_date: datetime, consecutive_zero: int = 0) -> str:
    seconds = (event_date - datetime.now(timezone.utc)).total_seconds()
    if seconds >= 0:
        # Pre-start — zero inventory never advances lifecycle here
        if seconds >= _ADMISSION_DAYS * 24 * 3600:
            return "pre_admission"
        return "active"
    # Post-start
    if consecutive_zero >= _EXHAUSTION_THRESHOLD:
        return "completed"
    if consecutive_zero > 0:
        return "exhaustion_pending"
    return "live"


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
        next_run_time=datetime.now(timezone.utc),
    )
    _scheduler.add_job(
        _resolve_pending_event_ids,
        trigger=IntervalTrigger(minutes=30),
        id="event_id_resolver",
        replace_existing=True,
        max_instances=1,
        next_run_time=datetime.now(timezone.utc),
    )
    _scheduler.add_job(
        _run_event_discovery,
        trigger=IntervalTrigger(hours=6),
        id="event_discovery",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        _run_follow_acquisition,
        trigger=IntervalTrigger(hours=6),
        id="follow_acquisition",
        replace_existing=True,
        max_instances=1,
        next_run_time=datetime.now(timezone.utc),  # run once at startup
    )
    _scheduler.add_job(
        _run_price_history_agg,
        trigger=IntervalTrigger(hours=1),
        id="price_history_agg",
        replace_existing=True,
        max_instances=1,
        next_run_time=datetime.now(timezone.utc),  # backfill immediately at startup
    )
    _scheduler.start()
    logger.info(
        "Scheduler started — cadence=piecewise_2m_to_daily exhaustion_threshold=%d "
        "resolver=active discovery=6h lifecycle_phase=observability_only",
        _EXHAUSTION_THRESHOLD,
    )


async def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


# ── Resolver job ───────────────────────────────────────────────────────────────

async def _resolve_pending_event_ids():
    resolver = EventResolver(settings)
    try:
        counts = await resolver.resolve_all_pending(AsyncSessionLocal)
        if counts["resolved"] or counts["failed"]:
            logger.info(
                "RESOLVER: cycle resolved=%d failed=%d already_set=%d",
                counts["resolved"], counts["failed"], counts["already_set"],
            )
    finally:
        await resolver.close()


# ── Poll gate ──────────────────────────────────────────────────────────────────

async def _check_due_events():
    async with AsyncSessionLocal() as db:
        now_naive = datetime.utcnow()  # next_poll_at is TIMESTAMP WITHOUT TIME ZONE
        result = await db.execute(
            select(TrackedEvent).where(
                and_(
                    TrackedEvent.is_active == True,
                    TrackedEvent.external_event_id.is_not(None),
                    (TrackedEvent.next_poll_at <= now_naive)
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
                "STAGE_GATE: %d tracked_event(s) due for polling — %s",
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
    - Updates events.status (display field only)
    - Updates tracked_events.lifecycle_phase (observability only)
    - Does NOT deactivate tracked_events — that is handled exclusively by
      inventory-exhaustion logic in _process_result() and only after event_start.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event))
        for event in result.scalars().all():
            new_status = event_status_from_date(event.event_date)
            if event.status != new_status:
                event.status = new_status
                logger.info("EVENT: %d '%s' status → %s", event.id, event.title, new_status)

            # Update lifecycle_phase on all active tracked_events for observability
            te_result = await db.execute(
                select(TrackedEvent).where(
                    TrackedEvent.event_id == event.id,
                    TrackedEvent.is_active == True,
                )
            )
            for te in te_result.scalars().all():
                new_phase = compute_lifecycle_phase(event.event_date, te.consecutive_zero_inventory_count)
                if te.lifecycle_phase != new_phase:
                    te.lifecycle_phase = new_phase

        await db.commit()


# ── Discovery job ──────────────────────────────────────────────────────────────

async def _run_event_discovery():
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


async def _run_follow_acquisition():
    from app.services.follow_acquisition import run_follow_acquisition
    try:
        summary = await run_follow_acquisition(AsyncSessionLocal)
        for entity, info in summary.items():
            logger.info(
                "FOLLOW_ACQUISITION: entity='%s' scope=%s already=%d added=%d total=%d errors=%s",
                entity, info.get("scope"), info.get("already_tracked"),
                info.get("enrolled", 0), info.get("total_after", 0),
                info.get("errors", []),
            )
    except Exception as exc:
        logger.exception("FOLLOW_ACQUISITION: cycle failed — %s", exc)


async def _run_price_history_agg():
    from app.services.price_history_agg import run_price_history_agg
    try:
        result = await run_price_history_agg(AsyncSessionLocal)
        logger.info(
            "PRICE_HISTORY_AGG: events=%d inserted=%d skipped=%d errors=%d",
            result["events_processed"], result["buckets_inserted"],
            result["buckets_skipped"], result["errors"],
        )
    except Exception as exc:
        logger.exception("PRICE_HISTORY_AGG: cycle failed — %s", exc)


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

        if event:
            new_status = event_status_from_date(event.event_date)
            if event.status != new_status:
                event.status = new_status
            te.lifecycle_phase = compute_lifecycle_phase(
                event.event_date, te.consecutive_zero_inventory_count
            )

        te.last_polled_at = datetime.utcnow()
        te.poll_interval_minutes = interval
        te.next_poll_at = datetime.utcnow() + timedelta(minutes=interval)
        await db.commit()

    from app.collectors.registry import COLLECTOR_REGISTRY
    collector_slugs = list(COLLECTOR_REGISTRY.keys())
    event_title = event.title if event else str(te.event_id)
    logger.info(
        "POLLING: event_id=%d '%s' dispatching to %d collector(s): [%s]",
        te.event_id, event_title, len(collector_slugs), ", ".join(collector_slugs),
    )
    results = await asyncio.gather(
        *[_run_collector_for_event(slug, te, event) for slug in collector_slugs],
        return_exceptions=True,
    )
    for slug, r in zip(collector_slugs, results):
        if isinstance(r, BaseException):
            logger.error(
                "COLLECTOR_FATAL: slug=%s event_id=%d exc_type=%s — %s",
                slug, te.event_id, type(r).__name__, r,
                exc_info=r,
            )


async def _run_collector_for_event(collector_slug: str, source_te: TrackedEvent, event):
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
                consecutive_zero_inventory_count=0,
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

    te.event = event

    logger.info(
        "COLLECTOR_DISPATCH: slug=%s te_id=%d event_id=%d "
        "mp_id=%d external_event_id=%r",
        collector_slug, te.id, te.event_id,
        te.marketplace_id, te.external_event_id,
    )
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
        await _process_result(result, te, poll_run_id, event)
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

async def _process_result(result, te: TrackedEvent, poll_run_id: int, event=None):
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
                )
            )
        )
        all_known_listings = existing_result.scalars().all()
        existing: dict[str, Listing] = {
            l.external_listing_id: l for l in all_known_listings
        }
        was_active: set[str] = {
            l.external_listing_id for l in all_known_listings if l.is_active
        }

        seen_ids: set[str] = set()
        new_count = 0
        parking_dropped = 0
        snapshots: list[ListingSnapshot] = []
        collector = get_collector(result.marketplace_slug, settings)

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
                l = existing[raw.external_listing_id]
                l.price = raw.price
                l.fees = raw.fees
                l.all_in_price = raw.all_in_price
                l.quantity = raw.quantity
                l.last_seen_at = result.fetched_at
                if not l.is_active:
                    l.is_active = True
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

        _PARTIAL_RATIO_THRESHOLD = 0.20
        _PARTIAL_MIN_ACTIVE = 50
        disappeared = 0
        _partial_result = (
            bool(result.listings)
            and len(was_active) > _PARTIAL_MIN_ACTIVE
            and len(result.listings) < len(was_active) * _PARTIAL_RATIO_THRESHOLD
        )
        if result.listings and not _partial_result:
            for ext_id in was_active:
                if ext_id not in seen_ids:
                    existing[ext_id].is_active = False
                    disappeared += 1
        elif _partial_result:
            logger.warning(
                "RECONCILE: collector=%s event_id=%d returned %d listings vs %d active "
                "(ratio=%.2f < %.2f threshold) — partial result, preserving existing",
                result.marketplace_slug, result.event_id, len(result.listings),
                len(was_active), len(result.listings) / len(was_active),
                _PARTIAL_RATIO_THRESHOLD,
            )
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

        te_row = (await db.execute(
            select(TrackedEvent).where(TrackedEvent.id == te.id)
        )).scalar_one_or_none()
        if te_row and not result.error:
            te_row.last_polled_at = datetime.utcnow()

            # ── Exhaustion logic (post-start only) ─────────────────────────────
            # CRITICAL: Pre-event zero inventory is NEVER a completion signal.
            # It may indicate collector failure, anti-bot blocks, or outage.
            # Only after event_start may exhaustion logic activate.
            event_obj = event or (await db.execute(
                select(Event).where(Event.id == te_row.event_id)
            )).scalar_one_or_none()

            if event_obj:
                event_has_started = event_obj.event_date <= datetime.now(timezone.utc)
                if event_has_started:
                    if len(clean_listings) == 0:
                        te_row.consecutive_zero_inventory_count += 1
                        logger.info(
                            "EXHAUSTION: event=%d %s zero_count=%d/%d",
                            result.event_id, result.marketplace_slug,
                            te_row.consecutive_zero_inventory_count, _EXHAUSTION_THRESHOLD,
                        )
                    else:
                        if te_row.consecutive_zero_inventory_count > 0:
                            logger.info(
                                "EXHAUSTION: event=%d %s inventory restored — resetting zero_count",
                                result.event_id, result.marketplace_slug,
                            )
                        te_row.consecutive_zero_inventory_count = 0

                    te_row.lifecycle_phase = compute_lifecycle_phase(
                        event_obj.event_date, te_row.consecutive_zero_inventory_count
                    )

                    # Check if all active tracked_events for this event have reached threshold
                    if te_row.consecutive_zero_inventory_count >= _EXHAUSTION_THRESHOLD:
                        await _check_event_exhaustion(db, result.event_id, event_obj)
                else:
                    # Pre-event — flag data quality warning if repeated zeros but stay ACTIVE
                    if len(clean_listings) == 0:
                        logger.warning(
                            "DATA_QUALITY_WARNING: event=%d %s returned 0 listings "
                            "BEFORE event_start — keeping ACTIVE (may be collector/outage issue)",
                            result.event_id, result.marketplace_slug,
                        )

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

        try:
            from app.services.canonical_inventory import snapshot_canonical_inventory
            snap_id = await snapshot_canonical_inventory(
                event_id=result.event_id,
                db=db,
                poll_run_id=poll_run_id,
            )
            if snap_id:
                await db.commit()
                logger.info("CANONICAL: event=%d snap_id=%d written", result.event_id, snap_id)
        except Exception as canon_exc:
            await db.rollback()
            logger.warning(
                "CANONICAL: snapshot failed event=%d — %s (poll result unaffected)",
                result.event_id, canon_exc,
            )


async def _check_event_exhaustion(db, event_id: int, event_obj):
    """
    Called after any per-marketplace zero count reaches the threshold.
    Checks whether ALL active tracked_events for the event have hit the
    threshold.  If so, marks the event completed and deactivates all tracking.
    """
    all_te_result = await db.execute(
        select(TrackedEvent).where(
            TrackedEvent.event_id == event_id,
            TrackedEvent.is_active == True,
        )
    )
    all_active_te = all_te_result.scalars().all()

    if not all_active_te:
        return

    exhausted_count = sum(
        1 for te in all_active_te
        if te.consecutive_zero_inventory_count >= _EXHAUSTION_THRESHOLD
    )

    if exhausted_count < len(all_active_te):
        logger.info(
            "EXHAUSTION: event=%d — %d/%d marketplaces exhausted, not completing yet",
            event_id, exhausted_count, len(all_active_te),
        )
        return

    # All active tracked_events exhausted — complete the event
    logger.info(
        "EXHAUSTION: event=%d ALL %d marketplace(s) exhausted — marking COMPLETED",
        event_id, len(all_active_te),
    )
    for te in all_active_te:
        te.is_active = False
        te.lifecycle_phase = "completed"

    event_obj.status = "completed"
    # db.commit() is called by the caller (_process_result) after this returns
