"""
POST /api/hydrate?event_id={id}

Unified single-call pipeline:
  1. Force resolve all demo/NULL external_event_ids for this event
  2. Run all marketplace collectors synchronously
  3. Commit listings to DB before returning
  4. Query final DB state
  5. Return atomic truth response

No background tasks. No scheduler dependency. No time delays.
DB state at response time is ground truth.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import Listing, Marketplace, TrackedEvent
from app.models.event import Event

# NOTE: app.collectors.registry and app.scheduler are imported lazily (inside
# the route handler) so they don't pull in the full collector chain (playwright
# etc.) at module-level during app startup.  Module-level imports of those
# packages prevented uvicorn from starting on Railway.

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hydrate", tags=["hydrate"])
settings = get_settings()


@router.post("")
async def hydrate(event_id: int = Query(..., description="DB events.id to hydrate")):
    """
    Synchronous end-to-end pipeline: resolve → collect → commit → verify.
    Returns atomic truth about DB listing state after execution.

    When env_mode=mock: returns deterministic synthetic listings instantly,
    no external calls made. Production path is completely unmodified.
    """
    # ── Validate event exists ─────────────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        event = (await db.execute(
            select(Event).where(Event.id == event_id)
        )).scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    # ── MOCK MODE: write to DB first, then query back (listings table = truth) ─
    if settings.env_mode != "prod":
        from app.mock_marketplaces import write_mock_listings

        await write_mock_listings(event_id, AsyncSessionLocal)

        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(
                    Marketplace.slug,
                    func.count(Listing.id).label("total"),
                    func.count(Listing.id).filter(
                        ~Listing.external_listing_id.like("demo-%")
                    ).label("real"),
                    func.min(Listing.price).label("min_price"),
                )
                .join(Listing, and_(
                    Listing.marketplace_id == Marketplace.id,
                    Listing.event_id == event_id,
                    Listing.is_active == True,
                ), isouter=True)
                .where(Marketplace.is_active == True)
                .group_by(Marketplace.slug)
            )).all()

        by_marketplace = {
            slug: {
                "total": total or 0,
                "real": real or 0,
                "demo": (total or 0) - (real or 0),
                "min_price": float(min_price) if min_price is not None else None,
            }
            for slug, total, real, min_price in rows
        }
        total_listings = sum(v["total"] for v in by_marketplace.values())
        total_real = sum(v["real"] for v in by_marketplace.values())
        verdict = "POPULATED" if total_real > 0 else "EMPTY"

        logger.info(
            "HYDRATE: mock mode event_id=%d total=%d real=%d verdict=%s",
            event_id, total_listings, total_real, verdict,
        )
        return {
            "event_id": event_id,
            "event_title": event.title,
            "mode": "mock",
            "status": "LIVE" if total_real > 0 else "EMPTY",
            "resolver": {
                "resolved": sum(1 for v in by_marketplace.values() if v["total"] > 0),
                "failed": 0,
                "already_set": 0,
            },
            "collector": {"success": list(by_marketplace.keys()), "failed": []},
            "db": {
                "total_listings": total_listings,
                "real_listings": total_real,
                "by_marketplace": by_marketplace,
            },
            "external_blockers": [],
            "final_verdict": verdict,
        }

    # ── Lazy imports (kept out of module-level to avoid pulling playwright etc. ──
    # into app startup — see module docstring note above).
    from app.collectors.registry import COLLECTOR_REGISTRY, get_collector  # noqa: PLC0415
    from app.collectors.resolver import EventResolver  # noqa: PLC0415
    from app.scheduler import _run_collector_for_event  # noqa: PLC0415

    # ── STEP 1: Force resolver ────────────────────────────────────────────────
    resolver_counts = {"resolved": 0, "failed": 0, "already_set": 0}
    try:
        resolver = EventResolver(settings)
        try:
            resolver_counts = await resolver.resolve_all_pending(AsyncSessionLocal)
        finally:
            await resolver.close()
    except Exception as exc:
        logger.exception("HYDRATE: resolver error — %s", exc)

    # ── STEP 2: Load all TrackedEvents for this event (post-resolution) ───────
    async with AsyncSessionLocal() as db:
        te_rows = (await db.execute(
            select(TrackedEvent).where(
                TrackedEvent.event_id == event_id,
                TrackedEvent.is_active == True,
            )
        )).scalars().all()

    # If no TrackedEvents exist yet, create them for all known marketplaces —
    # unless the event freeze is active.
    if not te_rows:
        if settings.discovery_freeze:
            logger.warning(
                "EVENT_FREEZE_ACTIVE: hydrate blocked from creating new TrackedEvents "
                "for event_id=%d — reason=frozen",
                event_id,
            )
            raise HTTPException(
                status_code=503,
                detail=(
                    "EVENT_FREEZE_ACTIVE: TrackedEvent creation is frozen while "
                    "duplicate reconciliation is in progress."
                ),
            )
        async with AsyncSessionLocal() as db:
            marketplaces = (await db.execute(
                select(Marketplace).where(Marketplace.is_active == True)
            )).scalars().all()
            for mp in marketplaces:
                te = TrackedEvent(
                    event_id=event_id,
                    marketplace_id=mp.id,
                    is_active=True,
                    poll_interval_minutes=60,
                )
                db.add(te)
            await db.commit()

        async with AsyncSessionLocal() as db:
            te_rows = (await db.execute(
                select(TrackedEvent).where(
                    TrackedEvent.event_id == event_id,
                    TrackedEvent.is_active == True,
                )
            )).scalars().all()

    # Attach event object so collector resolver fallbacks can access event metadata
    for te in te_rows:
        te.event = event

    # ── STEP 3: Run all collectors synchronously (fan-out, gather results) ────
    # _run_collector_for_event owns its own DB session and commits internally.
    # Each collector is isolated — a failure in one does not abort others.
    collector_results: dict[str, Optional[str]] = {}  # slug → error or None

    async def _run_and_capture(slug: str, te: TrackedEvent):
        collector = get_collector(slug, settings)
        if not collector:
            collector_results[slug] = "no_collector_registered"
            return
        collector._db_session_factory = AsyncSessionLocal
        try:
            await _run_collector_for_event(slug, te, event)
            collector_results[slug] = None  # success (error detail in PollRun)
        except Exception as exc:
            collector_results[slug] = str(exc)

    # Use one TrackedEvent per marketplace slug — prefer the one that already has
    # a resolved external_event_id, fall back to any active row.
    te_by_slug: dict[str, TrackedEvent] = {}
    async with AsyncSessionLocal() as db:
        for slug in COLLECTOR_REGISTRY:
            mp = (await db.execute(
                select(Marketplace).where(Marketplace.slug == slug)
            )).scalar_one_or_none()
            if not mp:
                continue
            te = (await db.execute(
                select(TrackedEvent).where(
                    TrackedEvent.event_id == event_id,
                    TrackedEvent.marketplace_id == mp.id,
                    TrackedEvent.is_active == True,
                )
            )).scalar_one_or_none()
            if te:
                te.event = event
                te_by_slug[slug] = te

    await asyncio.gather(
        *[_run_and_capture(slug, te) for slug, te in te_by_slug.items()],
        return_exceptions=True,
    )

    # ── STEP 4: Verify DB state ───────────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(
                Marketplace.slug,
                func.count(Listing.id).label("total"),
                func.count(Listing.id).filter(
                    ~Listing.external_listing_id.like("demo-%")
                ).label("real"),
                func.min(Listing.price).label("min_price"),
            )
            .join(Listing, and_(
                Listing.marketplace_id == Marketplace.id,
                Listing.event_id == event_id,
                Listing.is_active == True,
            ), isouter=True)
            .where(Marketplace.is_active == True)
            .group_by(Marketplace.slug)
        )).all()

    by_marketplace: dict[str, dict] = {}
    total_listings = 0
    total_real = 0
    for slug, total, real, min_price in rows:
        by_marketplace[slug] = {
            "total": total or 0,
            "real": real or 0,
            "demo": (total or 0) - (real or 0),
            "min_price": float(min_price) if min_price is not None else None,
        }
        total_listings += total or 0
        total_real += real or 0

    # ── STEP 5: Classify outcome ──────────────────────────────────────────────
    collector_success = [s for s, err in collector_results.items() if err is None]
    collector_failed = [
        {"marketplace": s, "error": err}
        for s, err in collector_results.items() if err is not None
    ]
    external_blockers = [
        s for s, v in by_marketplace.items()
        if v["total"] == 0 and s in collector_results and collector_results[s] is None
    ]

    if total_real > 0:
        status = "LIVE"
        final_verdict = "POPULATED"
        failure_class = None
    elif total_listings > 0:
        # Demo listings present — resolver didn't obtain real IDs
        status = "PARTIAL"
        final_verdict = "NOT_POPULATED"
        failure_class = {
            "code": "B",
            "label": "RESOLVER_FAILURE",
            "detail": (
                f"resolver resolved={resolver_counts['resolved']} "
                f"failed={resolver_counts['failed']} — "
                "demo IDs remain; real marketplace IDs not obtained"
            ),
            "fix": (
                "Set SeatGeek/TickPick/StubHub credentials in .env. "
                "TickPick and SeatGeek internal API require no key."
            ),
        }
    elif resolver_counts["failed"] > 0 and resolver_counts["resolved"] == 0:
        status = "BLOCKED"
        final_verdict = "NOT_POPULATED"
        failure_class = {
            "code": "D",
            "label": "EXTERNAL_BLOCK",
            "detail": (
                f"All {resolver_counts['failed']} resolution attempt(s) failed. "
                "No external marketplace API reachable without credentials."
            ),
            "fix": (
                "Add SEATGEEK_CLIENT_ID, TICKPICK credentials, or STUBHUB_API_KEY "
                "to .env and restart backend."
            ),
        }
    elif collector_failed and not collector_success:
        status = "BLOCKED"
        final_verdict = "NOT_POPULATED"
        failure_class = {
            "code": "A",
            "label": "COLLECT_FAILURE",
            "detail": f"All {len(collector_failed)} collector(s) raised exceptions",
            "fix": "Check backend logs for INTEGRATION_FAILURE entries",
        }
    else:
        status = "BLOCKED"
        final_verdict = "NOT_POPULATED"
        failure_class = {
            "code": "D",
            "label": "EXTERNAL_BLOCK",
            "detail": (
                "Collectors ran without exception but returned 0 listings. "
                "External APIs unreachable or require authentication."
            ),
            "fix": (
                "TickPick and SeatGeek internal APIs are credential-free. "
                "If they also return 0, the event may not be listed yet."
            ),
        }

    response = {
        "event_id": event_id,
        "event_title": event.title,
        "status": status,
        "resolver": resolver_counts,
        "collector": {
            "success": collector_success,
            "failed": collector_failed,
        },
        "db": {
            "total_listings": total_listings,
            "real_listings": total_real,
            "by_marketplace": by_marketplace,
        },
        "external_blockers": external_blockers,
        "final_verdict": final_verdict,
        **({"failure_class": failure_class} if failure_class else {}),
    }

    logger.info(
        "HYDRATE: event_id=%d status=%s total=%d real=%d verdict=%s",
        event_id, status, total_listings, total_real, final_verdict,
    )
    return response
