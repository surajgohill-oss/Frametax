import dataclasses
import statistics
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional

from app.database import get_db
from app.models import Event, Listing, ListingSnapshot, Marketplace, ScraperErrorLog
from app.services.analytics import get_data_audit, get_event_analytics, get_venue_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def global_summary(db: AsyncSession = Depends(get_db)):
    total_listings = (await db.execute(select(func.count()).select_from(Listing).where(Listing.is_active == True))).scalar_one()
    avg_ask = (await db.execute(select(func.avg(Listing.price)).where(Listing.is_active == True))).scalar_one()
    since = datetime.utcnow() - timedelta(hours=24)
    recent_errors = (await db.execute(select(func.count()).select_from(ScraperErrorLog).where(ScraperErrorLog.timestamp >= since))).scalar_one()
    return {"total_listings": total_listings, "avg_lowest_ask": float(avg_ask) if avg_ask else None, "recent_errors": recent_errors}


@router.get("/events/{event_id}/summary")
async def event_summary(event_id: int, marketplace: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Marketplace).where(Marketplace.is_active == True))
    mps = result.scalars().all()
    if marketplace: mps = [m for m in mps if m.slug == marketplace]
    summaries = []
    for mp in mps:
        result = await db.execute(select(Listing).where(and_(Listing.event_id == event_id, Listing.marketplace_id == mp.id, Listing.is_active == True)))
        listings = result.scalars().all()
        if not listings: continue
        prices = [float(l.price) for l in listings]
        section_map: dict[str, list] = {}
        for l in listings: section_map.setdefault(l.section_id or l.section or "unknown", []).append(l)
        summaries.append({
            "event_id": event_id, "marketplace_slug": mp.slug, "total_listings": len(listings),
            "total_inventory": sum(l.quantity for l in listings), "lowest_ask": min(prices),
            "median_price": statistics.median(prices),
            "sections": [{"section_id": sid, "display_name": sl[0].section or sid, "listing_count": len(sl), "lowest_ask": min(float(l.price) for l in sl), "marketplace_slug": mp.slug} for sid, sl in section_map.items()],
        })
    return summaries


@router.get("/events/{event_id}/price-history")
async def price_history(event_id: int, hours: int = Query(168, ge=1, le=2160), marketplace: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    mp_filter = []
    if marketplace:
        mp_result = await db.execute(select(Marketplace).where(Marketplace.slug == marketplace))
        mp = mp_result.scalar_one_or_none()
        if mp: mp_filter = [ListingSnapshot.marketplace_id == mp.id]
    result = await db.execute(select(ListingSnapshot).where(and_(ListingSnapshot.event_id == event_id, ListingSnapshot.snapshot_at >= since, *mp_filter)).order_by(ListingSnapshot.snapshot_at))
    snapshots = result.scalars().all()
    mp_names = {m.id: m.slug for m in (await db.execute(select(Marketplace))).scalars().all()}
    buckets: dict = {}
    inv: dict = {}
    for s in snapshots:
        mp_slug = mp_names.get(s.marketplace_id, "unknown")
        ts = s.snapshot_at.replace(minute=0, second=0, microsecond=0).isoformat()
        k = (ts, mp_slug)
        buckets.setdefault(k, []).append(float(s.price))
        inv[k] = inv.get(k, 0) + s.quantity
    return [{"ts": ts, "lowest_ask": min(prices), "inventory": inv.get((ts, mp_slug), 0), "marketplace_slug": mp_slug} for (ts, mp_slug), prices in sorted(buckets.items())]


@router.get("/events/{event_id}/heatmap")
async def heatmap_data(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(and_(Listing.event_id == event_id, Listing.is_active == True)))
    listings = result.scalars().all()
    mp_names = {m.id: m.slug for m in (await db.execute(select(Marketplace))).scalars().all()}
    section_data: dict = {}
    for l in listings:
        key = l.section_id or l.section or "unknown"
        if key not in section_data: section_data[key] = {"prices": [], "inventory": 0}
        section_data[key]["prices"].append(float(l.price))
        section_data[key]["inventory"] += l.quantity
    return [{"section_id": sid, "lowest_ask": min(d["prices"]) if d["prices"] else None, "inventory": d["inventory"]} for sid, d in section_data.items()]


@router.get("/events/{event_id}/compare")
async def compare_marketplaces(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(and_(Listing.event_id == event_id, Listing.is_active == True)))
    listings = result.scalars().all()
    mp_names = {m.id: m.slug for m in (await db.execute(select(Marketplace))).scalars().all()}
    agg: dict = {}
    for l in listings:
        k = (l.section_id or l.section or "unknown", mp_names.get(l.marketplace_id, "unknown"))
        if k not in agg: agg[k] = {"display_name": l.section or k[0], "prices": [], "listing_count": 0, "inventory": 0}
        agg[k]["prices"].append(float(l.price))
        agg[k]["listing_count"] += 1
        agg[k]["inventory"] += l.quantity
    return [{"section_id": k[0], "marketplace": k[1], "display_name": v["display_name"], "lowest_ask": min(v["prices"]), "listing_count": v["listing_count"], "inventory": v["inventory"]} for k, v in agg.items()]


# ── Phase 4: Value Extraction Layer ──────────────────────────────────────────
# Read-only. No writes to any ingestion table.

@router.get("/audit")
async def data_audit(db: AsyncSession = Depends(get_db)):
    """
    STEP 1 audit — totals across events, tracked_events, poll_runs.
    Read-only. Safe to call repeatedly.
    """
    result = await get_data_audit(db)
    return dataclasses.asdict(result)


@router.get("/events/overview")
async def events_overview(db: AsyncSession = Depends(get_db)):
    """
    STEP 2 EventAnalyticsView — per-event coverage, resolution, and poll activity.
    Read-only.
    """
    views = await get_event_analytics(db)
    return [dataclasses.asdict(v) for v in views]


@router.get("/venues/overview")
async def venues_overview(db: AsyncSession = Depends(get_db)):
    """
    STEP 2 VenueAnalyticsView — venue-level rollup of events tracked and polling intensity.
    Read-only.
    """
    views = await get_venue_analytics(db)
    return [dataclasses.asdict(v) for v in views]
