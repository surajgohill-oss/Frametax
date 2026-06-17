"""
populate_event_marketplaces — shared ingestion pipeline stage 2+3.

Mirrors the logic in POST /api/hydrate but callable from code (not HTTP).
Used by:
  - follow_acquisition.py  (after discovering events via Gametime)
  - hydrate.py             (via the API endpoint — delegates here)

Pipeline:
  1. Run EventResolver → resolve NULL external_event_ids for all pending TEs
  2. Load all TrackedEvents for this event
  3. Fan-out to all marketplace collectors in parallel
  4. Verify DB state (listing counts per marketplace)
  5. Return population_status dict with per-marketplace verdict

Population statuses per marketplace:
  POPULATED   — real listings present in DB
  DEFERRED    — no listings yet, collector ran without error (not listed / on-sale later)
  BLOCKED     — collector blocked by bot detection / auth (known external constraint)
  ERROR       — collector threw an exception
  NO_ID       — external_event_id could not be resolved (resolver returned None)
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Marketplace, TrackedEvent, Listing
from app.models.event import Event

logger = logging.getLogger(__name__)

# Marketplaces known to require auth / browser sessions for listing data.
# Resolution may succeed but collection returns 0 until session is seeded.
_BROWSER_REQUIRED = {"stubhub"}

# Marketplaces where resolution via public search API is reliable.
_PUBLIC_API = {"tickpick", "vividseats", "gametime", "seatgeek"}


async def populate_event_marketplaces(
    event_id: int,
    session_factory,
    settings,
    source: str = "follow",
) -> dict:
    """
    Full population pipeline for a single event.

    Returns:
    {
        "event_id": int,
        "source": str,
        "resolver": {"resolved": N, "failed": N, "already_set": N},
        "marketplaces": {
            "gametime":   {"status": "POPULATED", "listings": N, "floor": 12.50},
            "tickpick":   {"status": "DEFERRED",  "listings": 0, "floor": None, "reason": "..."},
            "stubhub":    {"status": "BLOCKED",   "listings": 0, "floor": None, "reason": "..."},
            "vividseats": {"status": "NO_ID",     "listings": 0, "floor": None, "reason": "..."},
        },
        "population_status": "POPULATED" | "PARTIAL_POPULATION" | "EMPTY",
    }
    """
    # Lazy imports to avoid pulling playwright/scheduler into app startup
    from app.collectors.registry import COLLECTOR_REGISTRY, get_collector
    from app.collectors.resolver import EventResolver
    from app.scheduler import _run_collector_for_event

    # ── Load event ────────────────────────────────────────────────────────────
    async with session_factory() as db:
        event = (await db.execute(
            select(Event).where(Event.id == event_id)
        )).scalar_one_or_none()

    if not event:
        logger.error("populate_event_marketplaces: event_id=%d not found", event_id)
        return {"event_id": event_id, "error": "event_not_found"}

    # ── Step 1: Resolve all pending external IDs ──────────────────────────────
    resolver_counts = {"resolved": 0, "failed": 0, "already_set": 0}
    resolver = EventResolver(settings)
    try:
        resolver_counts = await resolver.resolve_all_pending(session_factory)
        logger.info(
            "POPULATE[%s] event_id=%d resolver: resolved=%d failed=%d already_set=%d",
            source, event_id,
            resolver_counts["resolved"], resolver_counts["failed"], resolver_counts["already_set"],
        )
    except Exception as exc:
        logger.exception("POPULATE[%s] event_id=%d resolver failed: %s", source, event_id, exc)
    finally:
        await resolver.close()

    # ── Step 2: Load TrackedEvents for this event (post-resolution) ───────────
    async with session_factory() as db:
        te_rows = (await db.execute(
            select(TrackedEvent).where(
                TrackedEvent.event_id == event_id,
                TrackedEvent.is_active == True,
            )
        )).scalars().all()

        all_marketplaces = (await db.execute(
            select(Marketplace).where(Marketplace.is_active == True)
        )).scalars().all()
        mp_by_id = {mp.id: mp for mp in all_marketplaces}

    # Build slug → te map (prefer TE with resolved external_event_id)
    te_by_slug: dict[str, TrackedEvent] = {}
    for te in te_rows:
        mp = mp_by_id.get(te.marketplace_id)
        if not mp:
            continue
        existing = te_by_slug.get(mp.slug)
        # Prefer row that already has an external_event_id
        if existing is None or (te.external_event_id and not existing.external_event_id):
            te.event = event
            te_by_slug[mp.slug] = te

    # ── Step 3: Fan-out to all collectors ────────────────────────────────────
    collector_errors: dict[str, Optional[str]] = {}

    async def _run_and_capture(slug: str, te: TrackedEvent):
        collector = get_collector(slug, settings)
        if not collector:
            collector_errors[slug] = "no_collector_registered"
            return
        collector._db_session_factory = session_factory
        try:
            await _run_collector_for_event(slug, te, event)
            collector_errors[slug] = None
        except Exception as exc:
            collector_errors[slug] = str(exc)
            logger.warning(
                "POPULATE[%s] event_id=%d collector=%s error: %s",
                source, event_id, slug, exc,
            )

    # Only run collectors for slugs that have a TrackedEvent for this event
    runnable = {slug: te for slug, te in te_by_slug.items() if slug in COLLECTOR_REGISTRY}
    await asyncio.gather(
        *[_run_and_capture(slug, te) for slug, te in runnable.items()],
        return_exceptions=True,
    )

    # ── Step 4: Verify DB listing state ──────────────────────────────────────
    async with session_factory() as db:
        # Reload TEs to get current external_event_id after resolver ran
        te_rows_fresh = (await db.execute(
            select(TrackedEvent).where(
                TrackedEvent.event_id == event_id,
                TrackedEvent.is_active == True,
            )
        )).scalars().all()
        te_ext_id_by_mp_id = {te.marketplace_id: te.external_event_id for te in te_rows_fresh}

        listing_rows = (await db.execute(
            select(
                Marketplace.slug,
                Marketplace.id,
                func.count(Listing.id).label("total"),
                func.min(Listing.price).label("floor"),
            )
            .join(Listing, and_(
                Listing.marketplace_id == Marketplace.id,
                Listing.event_id == event_id,
                Listing.is_active == True,
            ), isouter=True)
            .where(Marketplace.is_active == True)
            .group_by(Marketplace.slug, Marketplace.id)
        )).all()

    # ── Step 5: Build per-marketplace status ──────────────────────────────────
    mp_status: dict[str, dict] = {}
    total_populated = 0

    for slug, mp_id, total, floor in listing_rows:
        ext_id = te_ext_id_by_mp_id.get(mp_id)
        collector_err = collector_errors.get(slug)
        count = total or 0
        floor_f = float(floor) if floor is not None else None

        if count > 0:
            status = "POPULATED"
            total_populated += 1
            reason = None
        elif ext_id is None:
            status = "NO_ID"
            reason = "resolver could not find marketplace event ID"
        elif slug in _BROWSER_REQUIRED:
            status = "BLOCKED"
            reason = f"{slug} requires auth cookies / browser session for listing data"
        elif collector_err:
            status = "ERROR"
            reason = collector_err
        else:
            status = "DEFERRED"
            reason = "collector ran successfully — event not yet listed or on-sale date in future"

        mp_status[slug] = {
            "status": status,
            "listings": count,
            "floor": floor_f,
            "external_event_id": ext_id,
            **({"reason": reason} if reason else {}),
        }

    # ── Step 6: Overall population status ─────────────────────────────────────
    total_mp = len(mp_status)
    if total_populated == 0:
        population_status = "EMPTY"
    elif total_populated == total_mp:
        population_status = "POPULATED"
    else:
        # Check if ONLY the discovery source (Gametime) is populated
        populated_slugs = {s for s, v in mp_status.items() if v["status"] == "POPULATED"}
        if populated_slugs == {"gametime"} or populated_slugs.issubset({"gametime", "seatgeek"}):
            population_status = "PARTIAL_POPULATION"
        else:
            population_status = "PARTIAL_POPULATION"

    logger.info(
        "POPULATE[%s] event_id=%d '%s' status=%s populated=%d/%d marketplaces=%s",
        source, event_id, event.title,
        population_status, total_populated, total_mp,
        {s: v["status"] for s, v in mp_status.items()},
    )

    return {
        "event_id": event_id,
        "event_title": event.title,
        "source": source,
        "resolver": resolver_counts,
        "marketplaces": mp_status,
        "population_status": population_status,
    }
