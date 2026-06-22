"""
POST /api/collect/ingest  — receive normalized listings from local Mac collector.

Local collector fetches StubHub/TickPick (Railway IP is blocked/partial),
normalizes using the same collector code, and pushes results here.
Railway processes them through the normal _process_result pipeline:
snapshot writing, deduplication, exhaustion tracking.

Auth: Bearer token matching LOCAL_COLLECTOR_SECRET env var.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.event import Event, TrackedEvent
from app.models.listing import PollRun

logger = logging.getLogger("collect.ingest")
router = APIRouter(prefix="/collect", tags=["collect"])
settings = get_settings()


# ── Request schema ────────────────────────────────────────────────────────────

class RawListingIn(BaseModel):
    external_listing_id: str
    section: str
    row: Optional[str] = None
    quantity: int = 1
    price: str           # decimal string, e.g. "125.50"
    fees: Optional[str] = None
    all_in_price: Optional[str] = None
    listing_url: Optional[str] = None
    market_segment: str = "secondary_resale"

    @field_validator("price", "fees", "all_in_price", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        return str(v) if v is not None else v


class IngestPayload(BaseModel):
    te_id: int
    marketplace_slug: str
    external_event_id: Optional[str] = None
    listings: list[RawListingIn]
    collector_version: str = "local_mac_v1"
    collected_at: Optional[str] = None   # ISO8601 UTC; defaults to server now


# ── Auth helper ───────────────────────────────────────────────────────────────

def _require_local_secret(authorization: str = Header(default="")):
    secret = settings.local_collector_secret
    if not secret:
        raise HTTPException(403, "LOCAL_COLLECTOR_SECRET not configured on Railway")
    if authorization != f"Bearer {secret}":
        raise HTTPException(401, "Invalid collector secret")


# ── Ingest endpoint ───────────────────────────────────────────────────────────

@router.post("/ingest")
async def ingest_collector_results(
    payload: IngestPayload,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(_require_local_secret),
):
    """
    Accept normalized listings from the local Mac collector and write them to
    the DB through the standard _process_result pipeline.
    """
    try:
        from app.collectors.base import CollectorResult, RawListing
        from app.collectors.normalize import is_parking_listing
        from app.scheduler import _process_result
    except ImportError as exc:
        logger.error("INGEST: import error — %s", exc, exc_info=True)
        raise HTTPException(500, f"Server import error: {exc}")

    # Load TrackedEvent + parent Event
    te = (await db.execute(
        select(TrackedEvent).where(TrackedEvent.id == payload.te_id)
    )).scalar_one_or_none()
    if not te:
        raise HTTPException(404, f"TrackedEvent {payload.te_id} not found")

    event = (await db.execute(
        select(Event).where(Event.id == te.event_id)
    )).scalar_one_or_none()
    if not event:
        raise HTTPException(404, f"Event {te.event_id} not found")

    # Update external_event_id if collector resolved it and we don't have it yet
    if payload.external_event_id and not te.external_event_id:
        te.external_event_id = payload.external_event_id
        await db.commit()
        logger.info(
            "INGEST: te_id=%d resolved external_event_id=%s",
            payload.te_id, payload.external_event_id,
        )

    # Convert payload listings to RawListing objects
    raw_listings: list[RawListing] = []
    skipped_parking = 0
    skipped_price = 0
    for item in payload.listings:
        # Parse price
        try:
            price = Decimal(item.price)
            if price <= 0:
                skipped_price += 1
                continue
        except InvalidOperation:
            skipped_price += 1
            continue

        # Skip parking
        if is_parking_listing(item.section, item.row):
            skipped_parking += 1
            continue

        raw_listings.append(RawListing(
            external_listing_id=item.external_listing_id,
            section=item.section,
            row=item.row,
            quantity=item.quantity,
            price=price,
            fees=Decimal(item.fees) if item.fees else None,
            all_in_price=Decimal(item.all_in_price) if item.all_in_price else None,
            listing_url=item.listing_url,
            market_segment=item.market_segment,
        ))

    fetched_at = (
        datetime.fromisoformat(payload.collected_at.replace("Z", "+00:00"))
        if payload.collected_at
        else datetime.now(timezone.utc)
    )

    result = CollectorResult(
        marketplace_slug=payload.marketplace_slug,
        event_id=te.event_id,
        listings=raw_listings,
        fetched_at=fetched_at,
        raw_count=len(payload.listings),
    )

    # Create poll_run record
    try:
        # poll_runs uses TIMESTAMP WITHOUT TIME ZONE — must pass naive UTC datetimes
        started_naive = fetched_at.replace(tzinfo=None) if fetched_at.tzinfo else fetched_at
        poll_run = PollRun(
            tracked_event_id=te.id,
            started_at=started_naive,
            completed_at=datetime.utcnow(),
            status="success",
            listings_found=len(raw_listings),
        )
        db.add(poll_run)
        await db.flush()
        poll_run_id = poll_run.id
        await db.commit()
    except Exception as exc:
        logger.error("INGEST: poll_run insert failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"PollRun insert failed: {type(exc).__name__}: {exc}")

    # Refresh after commit — SQLAlchemy expires all attributes on commit(),
    # and _process_result opens its own session so it cannot lazy-load through ours.
    await db.refresh(te)
    await db.refresh(event)

    # Attach event so _process_result can do exhaustion checks
    te.event = event

    # Run through the normal pipeline (dedup, snapshot, exhaustion)
    try:
        await _process_result(result, te, poll_run_id, event)
    except Exception as exc:
        logger.error(
            "INGEST: _process_result failed te_id=%d mp=%s: %s",
            payload.te_id, payload.marketplace_slug, exc, exc_info=True,
        )
        raise HTTPException(500, f"_process_result error: {type(exc).__name__}: {exc}")

    logger.info(
        "INGEST: te_id=%d mp=%s event=%d listings=%d skipped_parking=%d "
        "skipped_price=%d poll_run=%d version=%s",
        payload.te_id, payload.marketplace_slug, te.event_id,
        len(raw_listings), skipped_parking, skipped_price,
        poll_run_id, payload.collector_version,
    )

    return {
        "ok": True,
        "te_id": payload.te_id,
        "event_id": te.event_id,
        "marketplace_slug": payload.marketplace_slug,
        "listings_accepted": len(raw_listings),
        "skipped_parking": skipped_parking,
        "skipped_price": skipped_price,
        "poll_run_id": poll_run_id,
    }


# ── Heartbeat endpoint ────────────────────────────────────────────────────────

@router.post("/heartbeat")
async def local_collector_heartbeat(
    payload: dict,
    _auth=Depends(_require_local_secret),
):
    """
    Local collector pings this every run so Railway can detect staleness.
    payload: {collector_version, marketplaces_attempted, marketplaces_ok,
              events_polled, total_listings, elapsed_s, error: null|str}
    """
    logger.info(
        "LOCAL_HEARTBEAT: version=%s marketplaces=%s/%s events=%s listings=%s elapsed=%.1fs err=%s",
        payload.get("collector_version", "?"),
        payload.get("marketplaces_ok", "?"),
        payload.get("marketplaces_attempted", "?"),
        payload.get("events_polled", "?"),
        payload.get("total_listings", "?"),
        float(payload.get("elapsed_s", 0)),
        payload.get("error"),
    )
    return {"ok": True, "server_utc": datetime.now(timezone.utc).isoformat()}
