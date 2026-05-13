import statistics
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional

from app.database import get_db
from app.models import Event, Listing, ListingSnapshot, Marketplace, ScraperErrorLog

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def global_summary(db: AsyncSession = Depends(get_db)):
    total_listings = (await db.execute(
        select(func.count()).select_from(Listing).where(Listing.is_active == True)
    )).scalar_one()
    avg_ask_result = (await db.execute(
        select(func.avg(Listing.price)).where(Listing.is_active == True)
    )).scalar_one()
    since = datetime.utcnow() - timedelta(hours=24)
    recent_errors = (await db.execute(
        select(func.count()).select_from(ScraperErrorLog).where(ScraperErrorLog.timestamp >= since)
    )).scalar_one()
    return {
        "total_listings": total_listings,
        "avg_lowest_ask": float(avg_ask_result) if avg_ask_result else None,
        "recent_errors": recent_errors,
    }


@router.get("/events/{event_id}/summary")
async def event_summary(
    event_id: int,
    marketplace: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    mp_list = await _get_marketplaces(db, marketplace)
    summaries = []
    for mp in mp_list:
        result = await db.execute(
            select(Listing).where(
                and_(Listing.event_id == event_id, Listing.marketplace_id == mp.id, Listing.is_active == True)
            )
        )
        listings = result.scalars().all()
        if not listings:
            continue
        prices = [float(l.price) for l in listings]
        section_map: dict[str, list] = {}
        for l in listings:
            key = l.section_id or l.section or "unknown"
            section_map.setdefault(key, []).append(l)

        summaries.append({
            "event_id": event_id,
            "marketplace_slug": mp.slug,
            "total_listings": len(listings),
            "total_inventory": sum(l.quantity for l in listings),
            "lowest_ask": min(prices),
            "median_price": statistics.median(prices),
            "sections": [
                {
                    "section_id": sec_id,
                    "display_name": sec_listings[0].section or sec_id,
                    "listing_count": len(sec_listings),
                    "total_inventory": sum(l.quantity for l in sec_listings),
                    "lowest_ask": min(float(l.price) for l in sec_listings),
                    "median_price": statistics.median(float(l.price) for l in sec_listings),
                    "highest_price": max(float(l.price) for l in sec_listings),
                    "marketplace_slug": mp.slug,
                }
                for sec_id, sec_listings in section_map.items()
            ],
            "snapshot_at": datetime.utcnow().isoformat(),
        })
    return summaries


@router.get("/events/{event_id}/price-history")
async def price_history(
    event_id: int,
    hours: int = Query(168, ge=1, le=2160),
    marketplace: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=hours)
    mp_filter = []
    if marketplace:
        mp_result = await db.execute(select(Marketplace).where(Marketplace.slug == marketplace))
        mp = mp_result.scalar_one_or_none()
        if mp:
            mp_filter = [ListingSnapshot.marketplace_id == mp.id]

    result = await db.execute(
        select(ListingSnapshot).where(
            and_(ListingSnapshot.event_id == event_id, ListingSnapshot.snapshot_at >= since, *mp_filter)
        ).order_by(ListingSnapshot.snapshot_at)
    )
    snapshots = result.scalars().all()
    mp_names = await _mp_id_map(db)

    buckets: dict[tuple, list[float]] = {}
    inv: dict[tuple, int] = {}
    for s in snapshots:
        mp_slug = mp_names.get(s.marketplace_id, "unknown")
        ts = s.snapshot_at.replace(minute=0, second=0, microsecond=0).isoformat()
        k = (ts, mp_slug)
        buckets.setdefault(k, []).append(float(s.price))
        inv[k] = inv.get(k, 0) + s.quantity

    return [
        {
            "ts": ts,
            "lowest_ask": min(prices),
            "inventory": inv.get((ts, mp_slug), 0),
            "marketplace_slug": mp_slug,
        }
        for (ts, mp_slug), prices in sorted(buckets.items())
    ]


@router.get("/events/{event_id}/heatmap")
async def heatmap_data(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Listing).where(and_(Listing.event_id == event_id, Listing.is_active == True))
    )
    listings = result.scalars().all()
    mp_names = await _mp_id_map(db)

    section_data: dict[str, dict] = {}
    for l in listings:
        key = l.section_id or l.section or "unknown"
        if key not in section_data:
            section_data[key] = {"prices": [], "inventory": 0, "by_marketplace": {}}
        section_data[key]["prices"].append(float(l.price))
        section_data[key]["inventory"] += l.quantity
        mp_slug = mp_names.get(l.marketplace_id, "unknown")
        mp_entry = section_data[key]["by_marketplace"].setdefault(mp_slug, {"prices": [], "inventory": 0})
        mp_entry["prices"].append(float(l.price))
        mp_entry["inventory"] += l.quantity

    return [
        {
            "section_id": sid,
            "lowest_ask": min(d["prices"]) if d["prices"] else None,
            "median_price": statistics.median(d["prices"]) if d["prices"] else None,
            "inventory": d["inventory"],
            "by_marketplace": {
                mp_slug: {
                    "lowest_ask": min(mp["prices"]) if mp["prices"] else None,
                    "inventory": mp["inventory"],
                }
                for mp_slug, mp in d["by_marketplace"].items()
            },
        }
        for sid, d in section_data.items()
    ]


@router.get("/events/{event_id}/compare")
async def compare_marketplaces(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Listing).where(and_(Listing.event_id == event_id, Listing.is_active == True))
    )
    listings = result.scalars().all()
    mp_names = await _mp_id_map(db)

    rows = []
    for l in listings:
        rows.append({
            "section_id": l.section_id or l.section or "unknown",
            "display_name": l.section or l.section_id or "Unknown",
            "marketplace": mp_names.get(l.marketplace_id, "unknown"),
            "lowest_ask": float(l.price),
            "listing_count": 1,
            "inventory": l.quantity,
        })

    agg: dict[tuple, dict] = {}
    for r in rows:
        k = (r["section_id"], r["marketplace"])
        if k not in agg:
            agg[k] = {**r, "prices": [r["lowest_ask"]], "listing_count": 0, "inventory": 0}
        agg[k]["prices"].append(r["lowest_ask"])
        agg[k]["listing_count"] += 1
        agg[k]["inventory"] += r["inventory"]

    return [
        {
            "section_id": k[0],
            "marketplace": k[1],
            "display_name": v["display_name"],
            "lowest_ask": min(v["prices"]),
            "listing_count": v["listing_count"],
            "inventory": v["inventory"],
        }
        for k, v in agg.items()
    ]


async def _get_marketplaces(db, marketplace_slug=None):
    result = await db.execute(select(Marketplace).where(Marketplace.is_active == True))
    mps = result.scalars().all()
    if marketplace_slug:
        mps = [m for m in mps if m.slug == marketplace_slug]
    return mps


async def _mp_id_map(db) -> dict[int, str]:
    result = await db.execute(select(Marketplace))
    return {m.id: m.slug for m in result.scalars().all()}
