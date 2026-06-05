from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete, func, update
from typing import Optional, List

from app.database import get_db
from app.models.debug import ScraperErrorLog, FailureMemory
from app.models.listing import Listing

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/errors")
async def list_errors(marketplace: Optional[str] = Query(None), error_type: Optional[str] = Query(None), limit: int = Query(50, le=200), db: AsyncSession = Depends(get_db)):
    q = select(ScraperErrorLog).order_by(desc(ScraperErrorLog.timestamp)).limit(limit)
    if marketplace: q = q.where(ScraperErrorLog.marketplace == marketplace)
    if error_type: q = q.where(ScraperErrorLog.error_type == error_type)
    result = await db.execute(q)
    return [r.to_dict() for r in result.scalars().all()]


@router.get("/errors/summary")
async def error_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScraperErrorLog.marketplace, ScraperErrorLog.error_type, func.count().label("count"), func.max(ScraperErrorLog.timestamp).label("last_seen"))
        .group_by(ScraperErrorLog.marketplace, ScraperErrorLog.error_type).order_by(func.count().desc())
    )
    return [{"marketplace": r.marketplace, "error_type": r.error_type, "count": r.count, "last_seen": r.last_seen.isoformat() if r.last_seen else None} for r in result.all()]


@router.get("/memory")
async def list_failure_memory(marketplace: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    q = select(FailureMemory).order_by(FailureMemory.failure_count.desc())
    if marketplace: q = q.where(FailureMemory.marketplace == marketplace)
    result = await db.execute(q)
    return [r.to_dict() for r in result.scalars().all()]


@router.delete("/memory/{memory_id}", status_code=204)
async def delete_memory_entry(memory_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(FailureMemory).where(FailureMemory.id == memory_id))
    await db.commit()


@router.delete("/memory", status_code=204)
async def clear_memory(marketplace: str = Query(...), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(FailureMemory).where(FailureMemory.marketplace == marketplace))
    await db.commit()


@router.get("/vivid-search")
async def vivid_search_probe(date: str, q: Optional[str] = None, pages: int = 2):
    """
    Probe the Vivid Seats /productions API from Railway server.
    Returns raw items so we can verify response structure + event presence.
    date=YYYY-MM-DD, q=optional title filter, pages=how many to scan
    """
    import httpx
    _VS_API_BASE = "https://www.vividseats.com/hermes/api/v1"
    headers = {
        "Accept": "application/json",
        "User-Agent": "VividSeats-iOS/8.0 (iPhone; iOS 16.0; Scale/3.00)",
    }
    results = []
    raw_pages = []
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
        for page in range(1, pages + 1):
            try:
                resp = await client.get(
                    f"{_VS_API_BASE}/productions",
                    params={"startDate": date, "endDate": date, "pageSize": "50", "pageNumber": str(page)},
                )
                ct = resp.headers.get("content-type", "")
                if "json" not in ct:
                    raw_pages.append({"page": page, "status": resp.status_code, "error": "non-json", "preview": resp.text[:200]})
                    break
                data = resp.json()
                top_keys = list(data.keys())[:10]
                items = data.get("items") or data.get("productions") or (data if isinstance(data, list) else [])
                raw_pages.append({"page": page, "status": resp.status_code, "top_keys": top_keys, "item_count": len(items)})
                for item in items:
                    item_date = (item.get("localDate") or "")[:10]
                    name = item.get("name", "")
                    if q and q.lower() not in name.lower():
                        continue
                    results.append({"id": item.get("id"), "name": name, "localDate": item_date, "venue": item.get("venue", {}).get("name", "") if isinstance(item.get("venue"), dict) else str(item.get("venue", ""))})
                if len(items) < 50:
                    break
            except Exception as e:
                raw_pages.append({"page": page, "error": str(e)})
                break
    return {"date": date, "query": q, "pages_fetched": raw_pages, "matches": results}


@router.post("/deactivate-parking")
async def deactivate_parking_listings(
    event_id: int = Query(..., description="Event ID to scope the cleanup"),
    dry_run: bool = Query(True, description="Set false to actually deactivate"),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate (is_active=False) listings whose section matches known parking-only
    patterns that slipped past the ingest filter (e.g. WILLIAM KELSO ELEMENTARY SCHOOL).
    Does NOT delete rows — marks is_active=False and sets a note in extra JSON.

    Always dry_run=True by default. Pass ?dry_run=false to commit.
    """
    from app.collectors.normalize import is_parking_listing

    rows = await db.execute(
        select(Listing.id, Listing.section, Listing.row)
        .where(Listing.event_id == event_id, Listing.is_active == True)
    )
    to_deactivate: List[int] = []
    for lid, sec, row in rows.all():
        if is_parking_listing(sec, row):
            to_deactivate.append(lid)

    if not to_deactivate:
        return {"event_id": event_id, "dry_run": dry_run, "deactivated": 0, "ids": []}

    if not dry_run:
        await db.execute(
            update(Listing)
            .where(Listing.id.in_(to_deactivate))
            .values(is_active=False)
        )
        await db.commit()

    return {
        "event_id": event_id,
        "dry_run": dry_run,
        "deactivated": len(to_deactivate),
        "ids": to_deactivate,
    }


@router.post("/ensure-tracked-event")
async def ensure_tracked_event(
    event_id: int = Query(...),
    marketplace_slug: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Ensure a TrackedEvent row exists for (event_id, marketplace_slug).
    Creates one with external_event_id=NULL if missing, so the resolver
    can then fill it in.  Safe to call multiple times (idempotent).
    """
    from app.models import Marketplace, TrackedEvent, Event

    event = (await db.execute(select(Event).where(Event.id == event_id))).scalar_one_or_none()
    if not event:
        return {"error": f"event {event_id} not found"}

    mp = (await db.execute(select(Marketplace).where(Marketplace.slug == marketplace_slug))).scalar_one_or_none()
    if not mp:
        return {"error": f"marketplace {marketplace_slug!r} not found"}

    te = (await db.execute(
        select(TrackedEvent).where(TrackedEvent.event_id == event_id, TrackedEvent.marketplace_id == mp.id)
    )).scalar_one_or_none()

    if te:
        return {
            "created": False,
            "te_id": te.id,
            "external_event_id": te.external_event_id,
            "is_active": te.is_active,
        }

    te = TrackedEvent(
        event_id=event_id,
        marketplace_id=mp.id,
        external_event_id=None,
        is_active=True,
        poll_interval_minutes=60,
    )
    db.add(te)
    await db.commit()
    await db.refresh(te)
    return {"created": True, "te_id": te.id, "external_event_id": None}


@router.post("/test-collect")
async def test_collect(marketplace: str, event_id: str = "", background_tasks: BackgroundTasks = None, url: Optional[str] = None):
    async def _run():
        from app.collectors.registry import get_collector
        from app.config import get_settings
        from app.database import AsyncSessionLocal
        from dataclasses import dataclass
        @dataclass
        class FakeTe:
            event_id: int = 0
            marketplace_id: int = 0
            external_event_id: str = event_id
            external_url: str = url or ""
            is_active: bool = True
            poll_interval_minutes: int = 60
        settings = get_settings()
        collector = get_collector(marketplace, settings)
        if not collector: return
        collector._db_session_factory = AsyncSessionLocal
        result = await collector.collect(FakeTe())
        await collector.close()
    if background_tasks:
        background_tasks.add_task(_run)
    return {"message": f"Test collection triggered for {marketplace}"}
