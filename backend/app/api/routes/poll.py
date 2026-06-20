from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from app.database import get_db, AsyncSessionLocal
from app.models import TrackedEvent, PollRun
from app.config import get_settings

router = APIRouter(prefix="/poll", tags=["poll"])
settings = get_settings()


@router.post("/tracked/{te_id}/trigger")
async def trigger_single_te(te_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger a single TrackedEvent poll synchronously. Returns poll_run id and result."""
    from app.scheduler import run_poll_for_tracked_event
    te = (await db.execute(select(TrackedEvent).where(TrackedEvent.id == te_id))).scalar_one_or_none()
    if not te:
        raise HTTPException(404, f"TrackedEvent {te_id} not found")
    await run_poll_for_tracked_event(te_id)
    # Return latest poll_run for this te
    pr = (await db.execute(
        select(PollRun).where(PollRun.tracked_event_id == te_id)
        .order_by(PollRun.started_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not pr:
        return {"te_id": te_id, "status": "ran", "poll_run": None}
    return {
        "te_id": te_id,
        "poll_run_id": pr.id,
        "status": pr.status,
        "listings_found": pr.listings_found,
        "new_listings": pr.new_listings,
        "error_message": pr.error_message,
        "started_at": pr.started_at.isoformat() if pr.started_at else None,
        "completed_at": pr.completed_at.isoformat() if pr.completed_at else None,
    }


@router.post("/events/{event_id}/trigger")
async def trigger_poll(
    event_id: int,
    background_tasks: BackgroundTasks,
    sync: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    from app.scheduler import run_poll_for_tracked_event
    result = await db.execute(select(TrackedEvent).where(TrackedEvent.event_id == event_id, TrackedEvent.is_active == True))
    tracked = result.scalars().all()
    if not tracked: raise HTTPException(404, "No active tracked events")
    if sync:
        await asyncio.gather(*[run_poll_for_tracked_event(te.id) for te in tracked], return_exceptions=True)
        return {"message": f"Completed {len(tracked)} poll(s)", "count": len(tracked), "sync": True}
    for te in tracked:
        background_tasks.add_task(run_poll_for_tracked_event, te.id)
    return {"message": f"Triggered {len(tracked)} poll(s)", "count": len(tracked), "sync": False}


@router.post("/resolve-ids")
async def trigger_resolve_ids(
    background_tasks: BackgroundTasks,
    sync: bool = Query(False),
):
    """Manually trigger the event ID resolution job for all pending TrackedEvents."""
    from app.collectors.resolver import EventResolver
    async def _run():
        resolver = EventResolver(settings)
        try:
            return await resolver.resolve_all_pending(AsyncSessionLocal)
        finally:
            await resolver.close()
    if sync:
        counts = await _run()
        return {"message": "Event ID resolution complete", "sync": True, "counts": counts}
    background_tasks.add_task(_run)
    return {"message": "Event ID resolution triggered", "sync": False}


@router.post("/discovery/trigger")
async def trigger_discovery(background_tasks: BackgroundTasks):
    """Manually trigger the event discovery scan for all active marketplaces."""
    from app.collectors.discovery import EventDiscovery
    async def _run():
        discovery = EventDiscovery(settings)
        try:
            return await discovery.run_discovery(AsyncSessionLocal)
        finally:
            await discovery.close()
    background_tasks.add_task(_run)
    return {"message": "Event discovery scan triggered"}


# ── Manual ingest (Mac-host collectors: TickPick, Gametime, StubHub) ──────────

class ManualIngestListing(BaseModel):
    external_listing_id: str
    section: str
    row: Optional[str] = None
    quantity: int = 1
    price: float
    fees: Optional[float] = None
    all_in_price: Optional[float] = None
    listing_url: Optional[str] = None
    market_segment: Optional[str] = None
    extra: Optional[dict] = None


class ManualIngestRequest(BaseModel):
    tracked_event_id: int
    marketplace_slug: str
    listings: list[ManualIngestListing]
    fetched_at: Optional[str] = None   # ISO timestamp; defaults to now


@router.post("/tracked/{te_id}/manual-ingest")
async def manual_ingest(te_id: int, body: ManualIngestRequest):
    """
    Accept pre-fetched listings from a Mac-host collector script and write
    them to the database exactly as the scheduler's _process_result would.

    Used by: collect_tickpick.py, collect_gametime.py, collect_stubhub.py
    """
    from decimal import Decimal
    from datetime import datetime, timezone

    from app.collectors.base import CollectorResult, RawListing
    from app.scheduler import _process_result

    # ── Resolve TrackedEvent ──────────────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        te = (await db.execute(
            select(TrackedEvent).where(TrackedEvent.id == te_id)
        )).scalar_one_or_none()

    if not te:
        raise HTTPException(status_code=404, detail=f"TrackedEvent {te_id} not found")

    # ── Create PollRun ────────────────────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        poll_run = PollRun(
            tracked_event_id=te_id,
            started_at=datetime.utcnow(),
            status="running",
        )
        db.add(poll_run)
        await db.commit()
        await db.refresh(poll_run)
        poll_run_id = poll_run.id

    # ── Parse fetched_at ──────────────────────────────────────────────────────
    try:
        if body.fetched_at:
            fetched_at = datetime.fromisoformat(body.fetched_at.replace("Z", "+00:00"))
            if fetched_at.tzinfo is not None:
                fetched_at = fetched_at.replace(tzinfo=None)   # _process_result expects naive UTC
        else:
            fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
    except Exception:
        fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # ── Build CollectorResult ─────────────────────────────────────────────────
    raw_listings = [
        RawListing(
            external_listing_id=l.external_listing_id,
            section=l.section,
            row=l.row,
            quantity=l.quantity,
            price=Decimal(str(l.price)),
            fees=Decimal(str(l.fees)) if l.fees is not None else None,
            all_in_price=Decimal(str(l.all_in_price)) if l.all_in_price is not None else None,
            listing_url=l.listing_url,
            market_segment=l.market_segment,
            extra=l.extra or {},
        )
        for l in body.listings
    ]

    result = CollectorResult(
        marketplace_slug=body.marketplace_slug,
        event_id=te.event_id,
        listings=raw_listings,
        fetched_at=fetched_at,
        raw_count=len(raw_listings),
        error=None,
    )

    # ── Process (upsert listings, retire disappeared, update PollRun) ─────────
    await _process_result(result, te, poll_run_id)

    # ── Return summary (read back from DB) ────────────────────────────────────
    async with AsyncSessionLocal() as db:
        poll_run = (await db.execute(
            select(PollRun).where(PollRun.id == poll_run_id)
        )).scalar_one_or_none()

    return {
        "status": poll_run.status if poll_run else "unknown",
        "poll_run_id": poll_run_id,
        "listings_found": poll_run.listings_found if poll_run else len(raw_listings),
        "new_listings": poll_run.new_listings if poll_run else 0,
        "reactivated_listings": 0,    # not tracked separately in _process_result
        "disappeared_listings": poll_run.disappeared_listings if poll_run else 0,
    }


@router.get("/events/{event_id}/runs")
async def poll_runs(event_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PollRun).join(TrackedEvent).where(TrackedEvent.event_id == event_id).order_by(PollRun.started_at.desc()).limit(limit))
    return [{"id": r.id, "tracked_event_id": r.tracked_event_id, "started_at": r.started_at.isoformat() if r.started_at else None, "completed_at": r.completed_at.isoformat() if r.completed_at else None, "listings_found": r.listings_found, "new_listings": r.new_listings, "disappeared_listings": r.disappeared_listings, "status": r.status, "error_message": r.error_message} for r in result.scalars().all()]
