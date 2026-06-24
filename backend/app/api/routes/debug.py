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
    event_id: Optional[int] = Query(None, description="Scope to one event; omit for all events"),
    dry_run: bool = Query(True, description="Set false to actually deactivate"),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate (is_active=False) listings that are parking passes.
    Uses the price-aware is_parking_listing() filter, catching:
      - all keyword-based patterns (PARKING, LOT, VALET, street addresses, etc.)
      - section='General' with price < $20 (TickPick parking passes)

    Scopes to one event when event_id is supplied; runs across ALL active events
    when omitted. Does NOT delete rows — marks is_active=False.

    Always dry_run=True by default. Pass ?dry_run=false to commit.
    """
    from app.collectors.normalize import is_parking_listing

    q = select(Listing.id, Listing.section, Listing.row, Listing.price).where(Listing.is_active == True)
    if event_id is not None:
        q = q.where(Listing.event_id == event_id)

    rows = await db.execute(q)
    to_deactivate: List[int] = []
    breakdown: dict[str, int] = {}
    for lid, sec, row, price in rows.all():
        price_f = float(price) if price is not None else None
        if is_parking_listing(sec, row, price=price_f):
            to_deactivate.append(lid)
            reason = "general_low_price" if (sec or "").strip().lower() == "general" and price_f is not None and price_f < 20 else "keyword"
            breakdown[reason] = breakdown.get(reason, 0) + 1

    if not to_deactivate:
        return {"event_id": event_id, "dry_run": dry_run, "deactivated": 0, "breakdown": breakdown}

    if not dry_run:
        # Batch in chunks of 500 to avoid query-param limits
        for i in range(0, len(to_deactivate), 500):
            chunk = to_deactivate[i:i + 500]
            await db.execute(
                update(Listing)
                .where(Listing.id.in_(chunk))
                .values(is_active=False)
            )
        await db.commit()

    return {
        "event_id": event_id,
        "dry_run": dry_run,
        "deactivated": len(to_deactivate),
        "breakdown": breakdown,
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


@router.post("/create-event-bypass-freeze")
async def create_event_bypass_freeze(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Create a new event bypassing the discovery_freeze guard.
    Used for manual event ingestion when freeze is active.
    Requires: title, artist, venue_slug, event_date
    Optional: marketplace_urls (dict of slug -> url)
    """
    from datetime import datetime
    from app.models import Event, Venue, Marketplace, TrackedEvent
    import hashlib

    venue_result = await db.execute(select(Venue).where(Venue.slug == data["venue_slug"]))
    venue = venue_result.scalar_one_or_none()
    if not venue:
        return {"error": f"Venue '{data['venue_slug']}' not found"}

    event_date = datetime.fromisoformat(data["event_date"].replace("Z", "+00:00"))
    canonical_src = f"{data['title'].lower().strip()}|{data['venue_slug']}|{event_date.strftime('%Y-%m-%d')}"
    canonical_id = hashlib.sha256(canonical_src.encode()).hexdigest()[:16]

    existing = await db.execute(select(Event).where(Event.canonical_id == canonical_id))
    event = existing.scalar_one_or_none()
    created = False
    if not event:
        event = Event(
            canonical_id=canonical_id,
            title=data["title"],
            artist=data.get("artist"),
            venue_id=venue.id,
            event_date=event_date,
        )
        db.add(event)
        await db.flush()
        created = True

    # Add tracked events for any provided marketplace URLs
    tracked = []
    for mp_slug, url in (data.get("marketplace_urls") or {}).items():
        if not url:
            continue
        mp_res = await db.execute(select(Marketplace).where(Marketplace.slug == mp_slug))
        mp = mp_res.scalar_one_or_none()
        if not mp:
            continue
        te_res = await db.execute(
            select(TrackedEvent).where(TrackedEvent.event_id == event.id, TrackedEvent.marketplace_id == mp.id)
        )
        te = te_res.scalar_one_or_none()
        if not te:
            te = TrackedEvent(
                event_id=event.id,
                marketplace_id=mp.id,
                external_url=url,
                is_active=True,
                poll_interval_minutes=60,
            )
            db.add(te)
        tracked.append(mp_slug)

    await db.commit()
    return {
        "event_id": event.id,
        "canonical_id": canonical_id,
        "created": created,
        "title": event.title,
        "venue": venue.name,
        "event_date": event.event_date.isoformat(),
        "tracked_marketplaces": tracked,
    }


@router.post("/run-collector-for-event-sync")
async def run_collector_for_event_sync(
    te_id: int = Query(..., description="Source TrackedEvent.id (used to get event_id)"),
    slug: str = Query(..., description="Collector slug to run"),
    db: AsyncSession = Depends(get_db),
):
    """
    Directly call _run_collector_for_event(slug, source_te, event) and return
    whether a PollRun was created, what happened, and any exception.
    """
    from app.models import TrackedEvent, Event
    from app.scheduler import _run_collector_for_event
    import traceback

    te = (await db.execute(select(TrackedEvent).where(TrackedEvent.id == te_id))).scalar_one_or_none()
    if not te:
        return {"error": f"TrackedEvent {te_id} not found"}

    event = (await db.execute(select(Event).where(Event.id == te.event_id))).scalar_one_or_none()

    # Count PollRuns for this te_id before
    from app.models.listing import PollRun
    from sqlalchemy import func
    before_count = (await db.execute(
        select(func.count()).where(PollRun.tracked_event_id == te_id)
    )).scalar()

    exc_info = None
    try:
        await _run_collector_for_event(slug, te, event)
    except Exception as e:
        exc_info = {"type": type(e).__name__, "msg": str(e), "tb": traceback.format_exc()[-500:]}

    after_count = (await db.execute(
        select(func.count()).where(PollRun.tracked_event_id == te_id)
    )).scalar()

    return {
        "te_id": te_id,
        "slug": slug,
        "poll_runs_before": before_count,
        "poll_runs_after": after_count,
        "new_runs_created": after_count - before_count,
        "exception": exc_info,
    }


@router.post("/collect-te-sync")
async def collect_te_sync(
    te_id: int = Query(..., description="TrackedEvent.id to collect"),
    db: AsyncSession = Depends(get_db),
):
    """
    Directly invoke the collector for a TrackedEvent and return the result synchronously.
    Used to diagnose why the scheduler fan-out isn't creating PollRuns for a TE.
    """
    from app.models import TrackedEvent, Marketplace, PollRun
    from app.collectors.registry import get_collector
    from app.config import get_settings
    settings = get_settings()

    te = (await db.execute(select(TrackedEvent).where(TrackedEvent.id == te_id))).scalar_one_or_none()
    if not te:
        return {"error": f"TrackedEvent {te_id} not found"}

    mp = (await db.execute(select(Marketplace).where(Marketplace.id == te.marketplace_id))).scalar_one_or_none()
    if not mp:
        return {"error": f"Marketplace id={te.marketplace_id} not found"}

    collector = get_collector(mp.slug, settings)
    if not collector:
        return {"error": f"No collector for slug={mp.slug}"}

    collector._db_session_factory = lambda: db.__class__(bind=db.get_bind())

    try:
        result = await collector.collect(te)
        return {
            "te_id": te_id,
            "marketplace": mp.slug,
            "external_event_id": te.external_event_id,
            "error": result.error,
            "listings_count": len(result.listings),
            "sample": result.listings[:3] if result.listings else [],
        }
    except Exception as e:
        return {"te_id": te_id, "exception": type(e).__name__, "detail": str(e)}


@router.post("/patch-tracked-event")
async def patch_tracked_event(
    te_id: int = Query(..., description="TrackedEvent.id to patch"),
    external_event_id: str = Query(..., description="Marketplace event ID to set"),
    external_url: Optional[str] = Query(None, description="Marketplace event URL to set (optional)"),
    reactivate: bool = Query(False, description="Also reactivate TE, reset zero count, clear next_poll_at"),
    db: AsyncSession = Depends(get_db),
):
    """
    Directly set external_event_id (and optionally external_url) on an existing TrackedEvent.
    Used for manual resolution when the auto-resolver can't find the event.
    Pass reactivate=true to also re-enable polling after exhaustion.
    """
    from app.models import TrackedEvent

    te = (await db.execute(select(TrackedEvent).where(TrackedEvent.id == te_id))).scalar_one_or_none()
    if not te:
        return {"error": f"TrackedEvent {te_id} not found"}

    old_id = te.external_event_id
    old_url = te.external_url
    old_active = te.is_active
    te.external_event_id = external_event_id
    if external_url is not None:
        te.external_url = external_url
    if reactivate:
        te.is_active = True
        te.consecutive_zero_inventory_count = 0
        te.lifecycle_phase = "active"
        te.next_poll_at = None  # poll immediately
    await db.commit()
    return {
        "te_id": te_id,
        "old_external_event_id": old_id,
        "new_external_event_id": external_event_id,
        "old_external_url": old_url,
        "new_external_url": te.external_url,
        "old_is_active": old_active,
        "new_is_active": te.is_active,
        "ok": True,
    }


@router.post("/reactivate-event")
async def reactivate_event(
    event_id: int = Query(..., description="Event.id to reactivate all tracked events for"),
    db: AsyncSession = Depends(get_db),
):
    """
    Reactivate all tracked events for an event.
    Resets consecutive_zero_inventory_count, sets is_active=True,
    sets next_poll_at=NULL (poll on next scheduler tick), lifecycle_phase='active'.

    Use when the exhaustion engine has prematurely deactivated an event
    (e.g. due to event_date timezone mismatch or collector outage).
    """
    from app.models import TrackedEvent
    from datetime import datetime, timezone

    result = await db.execute(
        select(TrackedEvent).where(TrackedEvent.event_id == event_id)
    )
    tes = result.scalars().all()
    if not tes:
        return {"error": f"No TrackedEvents found for event_id={event_id}"}

    reactivated = []
    for te in tes:
        was_active = te.is_active
        te.is_active = True
        te.consecutive_zero_inventory_count = 0
        te.lifecycle_phase = "active"
        te.next_poll_at = None
        reactivated.append({
            "te_id": te.id,
            "marketplace": te.marketplace_id,
            "was_active": was_active,
            "external_event_id": te.external_event_id,
        })

    await db.commit()
    return {
        "event_id": event_id,
        "reactivated_count": len(reactivated),
        "tracked_events": reactivated,
        "ok": True,
    }


@router.post("/fix-event-date")
async def fix_event_date(
    event_id: int = Query(..., description="Event.id to fix"),
    new_date: str = Query(..., description="New event_date as ISO8601 UTC string, e.g. 2026-06-22T03:00:00+00:00"),
    db: AsyncSession = Depends(get_db),
):
    """
    Correct an event's stored event_date timestamp.

    Used to fix the systematic timezone off-by-one issue where events were stored
    as calendar_date + T03:00:00Z (= 8pm PDT the previous day) instead of the
    actual showtime (8pm PDT = T03:00:00Z on the NEXT day).
    """
    from app.models import Event
    from datetime import datetime, timezone

    event = (await db.execute(select(Event).where(Event.id == event_id))).scalar_one_or_none()
    if not event:
        return {"error": f"Event {event_id} not found"}

    try:
        new_dt = datetime.fromisoformat(new_date.replace("Z", "+00:00"))
    except ValueError as e:
        return {"error": f"Invalid date format: {e}"}

    old_date = event.event_date
    event.event_date = new_dt
    await db.commit()
    return {
        "event_id": event_id,
        "old_event_date": old_date.isoformat() if old_date else None,
        "new_event_date": new_dt.isoformat(),
        "ok": True,
    }


@router.post("/import-history-agg")
async def import_history_agg(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Bulk-upsert pre-aggregated historical rows into event_price_history_agg.

    Payload: { "rows": [ {railway_event_id, bucket_ts, bucket_size, low_ask,
                           median_ask, high_ask, p25_ask, p75_ask,
                           listing_count, ticket_count, marketplace_count}, ... ] }

    ON CONFLICT (railway_event_id, bucket_ts, bucket_size) DO NOTHING — safe
    to call multiple times (idempotent).
    """
    from sqlalchemy import text as _text
    rows = payload.get("rows", [])
    if not rows:
        return {"inserted": 0, "skipped": 0, "total": 0}

    inserted = 0
    skipped = 0
    for row in rows:
        result = await db.execute(_text("""
            INSERT INTO event_price_history_agg
              (railway_event_id, bucket_ts, bucket_size,
               low_ask, median_ask, high_ask, p25_ask, p75_ask,
               listing_count, ticket_count, marketplace_count)
            VALUES
              (:railway_event_id, CAST(:bucket_ts AS timestamp), :bucket_size,
               :low_ask, :median_ask, :high_ask, :p25_ask, :p75_ask,
               :listing_count, :ticket_count, :marketplace_count)
            ON CONFLICT (railway_event_id, bucket_ts, bucket_size) DO NOTHING
        """), {
            "railway_event_id": row["railway_event_id"],
            "bucket_ts":        row["bucket_ts"],
            "bucket_size":      row["bucket_size"],
            "low_ask":          row.get("low_ask"),
            "median_ask":       row.get("median_ask"),
            "high_ask":         row.get("high_ask"),
            "p25_ask":          row.get("p25_ask"),
            "p75_ask":          row.get("p75_ask"),
            "listing_count":    row.get("listing_count"),
            "ticket_count":     row.get("ticket_count"),
            "marketplace_count": row.get("marketplace_count"),
        })
        if result.rowcount and result.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    await db.commit()
    return {"inserted": inserted, "skipped": skipped, "total": len(rows)}


@router.get("/probe-marketplace")
async def probe_marketplace(marketplace: str, event_id: str, url: str = ""):
    """
    Probe a marketplace endpoint from Railway's IP with multiple strategies.
    Returns raw status + body size for each strategy so we can identify what works.
    """
    import httpx
    results = {}

    headers_base = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        if marketplace == "stubhub":
            probes = [
                # 1. Solr API with proper headers
                ("solr_json", "GET", f"https://www.stubhub.com/listingCatalog/select?q=*:*&fq=event_id:{event_id}&rows=5&wt=json",
                 {**headers_base, "Referer": "https://www.stubhub.com/", "Origin": "https://www.stubhub.com"}),
                # 2. StubHub internal listings API
                ("internal_listings", "GET", f"https://www.stubhub.com/api/search/listings?eventId={event_id}&rows=5",
                 {**headers_base, "Referer": f"https://www.stubhub.com/event/{event_id}/"}),
                # 3. StubHub mobile API
                ("mobile_api", "GET", f"https://m.stubhub.com/api/search/listings?eventId={event_id}&rows=5",
                 {**headers_base, "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"}),
                # 4. StubHub catalog endpoint
                ("catalog_v2", "GET", f"https://api.stubhub.com/sellers/search/events/v3?id={event_id}",
                 {**headers_base, "Referer": "https://www.stubhub.com/"}),
                # 5. Alternative JSON endpoint
                ("alt_json", "GET", f"https://www.stubhub.com/event/{event_id}/inventoryModule/selection?quantity=2&listingId=0",
                 {**headers_base, "Referer": f"https://www.stubhub.com/event/{event_id}/"}),
                # 6. Event page HTML (check if we get real page or bot wall)
                ("event_html", "GET", url or f"https://www.stubhub.com/event/{event_id}/",
                 {**headers_base, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}),
            ]
        elif marketplace == "tickpick":
            probes = [
                # 1. Original API
                ("api_v1", "GET", f"https://api.tickpick.com/1.0/listings/event/{event_id}?needidd=true", headers_base),
                # 2. www subdomain
                ("www_api", "GET", f"https://www.tickpick.com/api/listings/event/{event_id}", headers_base),
                # 3. TickPick internal event page HTML
                ("event_html", "GET", url or f"https://www.tickpick.com/buy-tickets/{event_id}/",
                 {**headers_base, "Accept": "text/html,application/xhtml+xml"}),
                # 4. TickPick mobile
                ("mobile", "GET", f"https://www.tickpick.com/buy-tickets/{event_id}/",
                 {**headers_base, "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"}),
                # 5. TickPick performers search
                ("search", "GET", f"https://api.tickpick.com/1.0/performances/event/{event_id}", headers_base),
            ]
        else:
            return {"error": f"Unknown marketplace: {marketplace}"}

        for name, method, probe_url, hdrs in probes:
            try:
                resp = await client.request(method, probe_url, headers=hdrs)
                body = resp.text[:500]
                is_json = False
                item_count = None
                try:
                    parsed = resp.json()
                    is_json = True
                    # Try to count items
                    for key in ("docs", "listings", "listing", "events", "data", "results"):
                        val = parsed.get(key) or (parsed.get("response", {}) or {}).get(key)
                        if isinstance(val, list):
                            item_count = len(val)
                            break
                except Exception:
                    pass
                results[name] = {
                    "url": probe_url[:80],
                    "status": resp.status_code,
                    "size": len(resp.content),
                    "is_json": is_json,
                    "item_count": item_count,
                    "preview": body[:200],
                }
            except Exception as exc:
                results[name] = {"url": probe_url[:80], "error": str(exc)[:100]}

    return results


@router.get("/scrape-stubhub-html")
async def scrape_stubhub_html(event_id: str, url: str = ""):
    """Parse StubHub event page HTML for embedded listing/price data."""
    import httpx, re, json as _json
    target_url = url or f"https://www.stubhub.com/event/{event_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "Cache-Control": "no-cache",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        resp = await client.get(target_url, headers=headers)
    html = resp.text
    result = {"status": resp.status_code, "size": len(html), "url": str(resp.url)}
    # Look for all <script> tags with JSON data
    script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    json_scripts = []
    for i, s in enumerate(script_tags):
        s = s.strip()
        if not s or not (s.startswith('{') or s.startswith('[') or '__' in s or 'window.' in s):
            continue
        size = len(s)
        # Try to parse JSON
        json_ok = False
        keys_preview = []
        try:
            parsed = _json.loads(s)
            json_ok = True
            keys_preview = list(parsed.keys())[:10] if isinstance(parsed, dict) else [f"list[{len(parsed)}]"]
        except Exception:
            # Try window.xxx = {...}
            m = re.match(r'window\.(\w+)\s*=\s*(\{.*)', s, re.DOTALL)
            if m:
                try:
                    parsed = _json.loads(m.group(2).rstrip(';'))
                    json_ok = True
                    keys_preview = list(parsed.keys())[:10]
                except Exception:
                    pass
        json_scripts.append({"index": i, "size": size, "json": json_ok, "keys": keys_preview, "preview": s[:150]})
    # Look for listing-related patterns
    patterns = {
        "listing_count": re.findall(r'"listingCount"\s*:\s*(\d+)', html),
        "numFound": re.findall(r'"numFound"\s*:\s*(\d+)', html),
        "totalListings": re.findall(r'"totalListings"\s*:\s*(\d+)', html),
        "currentPrice": re.findall(r'"currentPrice"\s*:\s*([\d.]+)', html)[:5],
        "allInPrice": re.findall(r'"allInPrice"\s*:\s*([\d.]+)', html)[:5],
        "listing_id": re.findall(r'"listing_id"\s*:\s*(\d+)', html)[:3],
        "seatNumber": re.findall(r'"seatNumber"\s*:\s*"([^"]+)"', html)[:3],
    }
    result["patterns"] = {k: v for k, v in patterns.items() if v}
    result["scripts"] = [s for s in json_scripts if s["size"] > 500][:10]
    result["html_head"] = html[:300]
    return result


@router.get("/scrape-tickpick-html")
async def scrape_tickpick_html(event_id: str, url: str = ""):
    """Parse TickPick event page HTML for embedded listing/price data."""
    import httpx, re, json as _json
    target_url = url or f"https://www.tickpick.com/buy-tickets/{event_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        resp = await client.get(target_url, headers=headers)
    html = resp.text
    result = {"status": resp.status_code, "size": len(html), "url": str(resp.url)}
    patterns = {
        "listing_count": re.findall(r'"listingCount"\s*:\s*(\d+)', html),
        "listing_p": re.findall(r'"p"\s*:\s*(\d+)', html)[:10],  # TickPick price field
        "listing_s": re.findall(r'"s"\s*:\s*"([^"]+)"', html)[:5],  # TickPick section field
        "listing_id_tp": re.findall(r'"id"\s*:\s*(\d{7,})', html)[:5],
        "numListings": re.findall(r'numListings["\s:]+(\d+)', html),
        "totalTickets": re.findall(r'totalTickets["\s:]+(\d+)', html),
        "json_ld_price": re.findall(r'"lowPrice"\s*:\s*"?(\d+)', html)[:3],
    }
    result["patterns"] = {k: v for k, v in patterns.items() if v}
    # Look for JSON blobs in script tags
    next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if next_data:
        try:
            nd = _json.loads(next_data.group(1))
            result["next_data_keys"] = list((nd.get("props", {}).get("pageProps", {}) or {}).keys())[:15]
        except Exception as e:
            result["next_data_error"] = str(e)
    # Large script tags
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    large = []
    for s in scripts:
        if len(s) > 1000 and ('"listing"' in s or '"p"' in s or '"price"' in s):
            large.append({"size": len(s), "preview": s[:200]})
    result["large_data_scripts"] = large[:5]
    result["html_head"] = html[:300]
    return result


@router.get("/extract-stubhub-grid")
async def extract_stubhub_grid(event_id: str, url: str = ""):
    """Extract StubHub listing grid data embedded in event page HTML."""
    import httpx, re, json as _json
    target_url = url or f"https://www.stubhub.com/event/{event_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        resp = await client.get(target_url, headers=headers)
    html = resp.text

    # Find the viagogo-event script with grid.items
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    grid_data = None
    for s in scripts:
        s = s.strip()
        if '"appName":"viagogo-event"' in s and '"grid"' in s:
            try:
                grid_data = _json.loads(s)
                break
            except Exception:
                pass

    if not grid_data:
        return {"status": resp.status_code, "size": len(html), "error": "grid script not found",
                "totalListings": re.findall(r'"totalListings"\s*:\s*(\d+)', html)}

    items = (grid_data.get("grid") or {}).get("items", [])
    # Extract listing fields
    sample = []
    for item in items[:5]:
        sample.append({
            "id": item.get("id"),
            "section": item.get("section"),
            "row": item.get("row"),
            "qty": item.get("quantity") or item.get("qty"),
            "currentPrice": item.get("currentPrice") or item.get("current_price"),
            "allInPrice": item.get("allInPrice") or item.get("all_in_price"),
            "listingUrl": str(item.get("listingUrl", ""))[:60],
            "keys": list(item.keys())[:15],
        })
    return {
        "status": resp.status_code,
        "html_size": len(html),
        "total_listings_html": re.findall(r'"totalListings"\s*:\s*(\d+)', html),
        "grid_items_count": len(items),
        "grid_top_keys": list(grid_data.keys())[:15],
        "ticket_classes": list((grid_data.get("ticketClasses") or {}).keys())[:10],
        "sample_items": sample,
        "first_item_keys": list(items[0].keys()) if items else [],
    }


@router.get("/extract-tickpick-listings")
async def extract_tickpick_listings(event_id: str, url: str = ""):
    """Extract TickPick listing data from event page HTML."""
    import httpx, re, json as _json
    target_url = url or f"https://www.tickpick.com/buy-tickets/{event_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        resp = await client.get(target_url, headers=headers)
    html = resp.text

    # TickPick embeds listing data in window.__INITIAL_STATE__ or similar
    # Look for large JSON blobs with listing data
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    listing_data = None
    listing_source = None

    for s in scripts:
        s = s.strip()
        # TickPick typically has: window.__NEXT_DATA__ or window.__INITIAL_STATE__ or inline JSON
        for pattern in [
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*)',
            r'window\.__REDUX_STATE__\s*=\s*(\{.*)',
        ]:
            m = re.match(pattern, s, re.DOTALL)
            if m:
                try:
                    listing_data = _json.loads(m.group(1).rstrip(';'))
                    listing_source = pattern
                    break
                except Exception:
                    pass
        if listing_data: break

    # Also try NEXT_DATA
    next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    next_data = None
    if next_data_match:
        try:
            next_data = _json.loads(next_data_match.group(1))
        except Exception:
            pass

    # Look for JSON-LD structured data with offers
    json_ld_blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
    offers = []
    for block in json_ld_blocks:
        try:
            d = _json.loads(block)
            if "offers" in d:
                o = d["offers"]
                offers.append({"lowPrice": o.get("lowPrice"), "highPrice": o.get("highPrice"), "availability": o.get("availability")})
        except Exception:
            pass

    return {
        "status": resp.status_code,
        "html_size": len(html),
        "url": str(resp.url),
        "has_initial_state": listing_source is not None,
        "has_next_data": next_data is not None,
        "next_data_keys": list((next_data or {}).get("props", {}).get("pageProps", {}).keys())[:20] if next_data else [],
        "json_ld_offers": offers,
        "listing_data_top_keys": list(listing_data.keys())[:15] if listing_data else None,
        "patterns": {
            "listing_p": re.findall(r'"p"\s*:\s*(\d{3,5})', html)[:10],
            "listing_section": re.findall(r'"s"\s*:\s*"([^"]{2,20})"', html)[:5],
            "listing_ids": re.findall(r'"id"\s*:\s*(\d{7,})', html)[:5],
            "numListings": re.findall(r'"numListings"\s*:\s*(\d+)', html),
        }
    }


@router.get("/stubhub-pagination-probe")
async def stubhub_pagination_probe(event_id: str, url: str = ""):
    """
    Deep investigation of StubHub full inventory retrieval.
    1. Fetches the event page HTML and extracts grid metadata (totalListings, pagination tokens, cursor).
    2. Parses out any embedded API endpoint patterns (fetch/XHR URLs).
    3. Attempts paginated fetches via multiple discovered parameter patterns.
    4. Tries the StubHub internal inventory API with discovered tokens.
    """
    import httpx, re, json as _json

    headers_html = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "Cache-Control": "no-cache",
    }
    headers_api = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.stubhub.com/event/{event_id}/",
        "Origin": "https://www.stubhub.com",
    }

    target_url = url or f"https://www.stubhub.com/event/{event_id}/"
    result = {"event_id": event_id, "url": target_url, "steps": {}}

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        # Step 1: Fetch event page HTML
        try:
            resp = await client.get(target_url, headers=headers_html)
            html = resp.text
            result["steps"]["html_fetch"] = {"status": resp.status_code, "size": len(html)}
        except Exception as exc:
            result["steps"]["html_fetch"] = {"error": str(exc)}
            return result

        # Step 2: Extract grid data
        grid_data = None
        for chunk in html.split("</script>"):
            if '"appName":"viagogo-event"' in chunk and '"grid"' in chunk:
                start = chunk.rfind('{"appName":"viagogo-event"')
                if start >= 0:
                    try:
                        grid_data = _json.loads(chunk[start:])
                        break
                    except Exception:
                        pass

        if not grid_data:
            result["steps"]["grid_extract"] = {"error": "no grid found", "total_listings_re": re.findall(r'"totalListings"\s*:\s*(\d+)', html)}
            return result

        grid = grid_data.get("grid") or {}
        items = grid.get("items") or []
        result["steps"]["grid_extract"] = {
            "items_in_page": len(items),
            "total_listings": grid_data.get("totalListings"),
            "grid_keys": list(grid.keys()),
            "grid_data_keys": list(grid_data.keys()),
        }

        # Step 3: Check pagination metadata in grid
        pagination_keys = {k: grid[k] for k in grid if any(x in k.lower() for x in ["page", "cursor", "token", "next", "total", "offset", "size", "limit", "more"])}
        result["steps"]["pagination_meta"] = pagination_keys

        # Step 4: Check for cursor/token in full grid_data
        top_level_pagination = {k: grid_data[k] for k in grid_data if any(x in k.lower() for x in ["page", "cursor", "token", "next", "total", "offset", "size", "limit", "more", "sort", "filter"])}
        result["steps"]["top_level_pagination"] = top_level_pagination

        # Step 5: Extract API URLs embedded in page source
        # Look for fetch() calls, XHR URLs, next-page API patterns
        api_patterns = []
        for pattern in [
            r'https://www\.stubhub\.com/listingCatalog[^\'">\s]+',
            r'https://api\.stubhub\.com/[^\'">\s]+',
            r'/api/[^\'">\s]*listing[^\'">\s]+',
            r'inventoryModule[^\'">\s]+',
            r'selectionModule[^\'">\s]+',
            r'["\']([^"\']+(?:catalog|listing|inventory|selection)[^"\']{10,})["\']',
        ]:
            found = re.findall(pattern, html)[:5]
            if found:
                api_patterns.extend(found[:3])
        result["steps"]["embedded_api_patterns"] = list(set(api_patterns))[:10]

        # Step 6: Look for page/offset parameters in the grid API call pattern
        # StubHub typically uses: start=0&rows=N
        # Try offset-based pagination with the Solr endpoint
        solr_urls_to_try = [
            (f"https://www.stubhub.com/listingCatalog/select?q=*:*&fq=event_id:{event_id}&rows=500&start=0&fl=listing_id,section,row,qty,current_price,all_in_price,listing_url&sort=current_price+asc&wt=json", "solr_500_start0"),
            (f"https://www.stubhub.com/listingCatalog/select?q=*:*&fq=event_id:{event_id}&rows=200&start=0&wt=json", "solr_200_start0"),
        ]
        result["steps"]["api_probes"] = {}
        for probe_url, label in solr_urls_to_try:
            try:
                r = await client.get(probe_url, headers=headers_api, timeout=15.0)
                ct = r.headers.get("content-type", "")
                is_json = "json" in ct
                count = None
                if is_json:
                    try:
                        d = r.json()
                        count = (d.get("response") or {}).get("numFound") or len((d.get("response") or {}).get("docs") or [])
                    except Exception:
                        pass
                result["steps"]["api_probes"][label] = {"status": r.status_code, "size": len(r.content), "is_json": is_json, "count": count, "preview": r.text[:200]}
            except Exception as exc:
                result["steps"]["api_probes"][label] = {"error": str(exc)[:80]}

        # Step 7: Try the internal StubHub inventory API (found in page source of some events)
        # Pattern: /event/{id}/inventoryModule/selection
        internal_urls = [
            f"https://www.stubhub.com/event/{event_id}/inventoryModule/selection?quantity=0&listingId=0&_source=grid",
            f"https://www.stubhub.com/api/listings/v3?eventId={event_id}&rows=200&start=0",
            f"https://www.stubhub.com/api/search/listings?eventId={event_id}&rows=200",
        ]
        result["steps"]["internal_api_probes"] = {}
        for iurl in internal_urls:
            label = iurl.split("/")[-1].split("?")[0] or iurl[30:60]
            try:
                r = await client.get(iurl, headers=headers_api, timeout=15.0)
                is_json = "json" in r.headers.get("content-type", "")
                count = None
                if is_json:
                    try:
                        d = r.json()
                        for key in ("listings", "listing", "docs", "data", "items"):
                            v = d.get(key)
                            if isinstance(v, list): count = len(v); break
                    except Exception:
                        pass
                result["steps"]["internal_api_probes"][label] = {"url": iurl[:80], "status": r.status_code, "size": len(r.content), "is_json": is_json, "count": count, "preview": r.text[:300]}
            except Exception as exc:
                result["steps"]["internal_api_probes"][label] = {"url": iurl[:80], "error": str(exc)[:80]}

        # Step 8: Try fetching with cursor-based pagination if any cursor found in grid
        cursor = grid.get("nextCursor") or grid.get("cursor") or grid_data.get("nextCursor") or grid_data.get("pageToken")
        result["steps"]["cursor_found"] = cursor

        # Step 9: Try the full-page approach with different sort/page URL parameters
        page2_urls = [
            (f"{target_url}?sort=price&page=2", "page2_url_param"),
            (f"https://www.stubhub.com/event/{event_id}/?start=10&rows=50", "start_10_rows_50"),
        ]
        result["steps"]["page2_probes"] = {}
        for p2url, p2label in page2_urls:
            try:
                r = await client.get(p2url, headers=headers_html, timeout=20.0)
                html2 = r.text
                # Check if this page also has a grid
                found_grid = '"appName":"viagogo-event"' in html2 and '"grid"' in html2
                item_count2 = 0
                if found_grid:
                    for chunk in html2.split("</script>"):
                        if '"appName":"viagogo-event"' in chunk and '"items"' in chunk:
                            s2 = chunk.rfind('{"appName":"viagogo-event"')
                            if s2 >= 0:
                                try:
                                    gd2 = _json.loads(chunk[s2:])
                                    item_count2 = len((gd2.get("grid") or {}).get("items") or [])
                                except Exception:
                                    pass
                            break
                result["steps"]["page2_probes"][p2label] = {"status": r.status_code, "size": len(html2), "has_grid": found_grid, "items": item_count2}
            except Exception as exc:
                result["steps"]["page2_probes"][p2label] = {"error": str(exc)[:80]}

    return result


@router.get("/tickpick-full-probe")
async def tickpick_full_probe(event_id: str, url: str = ""):
    """
    Exhaustive TickPick collection path investigation.
    Tries every known data extraction path: API endpoints, SSR data, hydration JSON,
    RSC payloads, mobile endpoints, GraphQL, embedded blobs, and alternate HTML routes.
    """
    import httpx, re, json as _json

    headers_desktop = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
    }
    headers_mobile = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    headers_json = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.tickpick.com/buy-tickets/{event_id}/",
        "Origin": "https://www.tickpick.com",
    }

    result = {"event_id": event_id, "probes": {}}

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:

        # 1. Original JSON API
        try:
            r = await client.get(f"https://api.tickpick.com/1.0/listings/event/{event_id}?needidd=true", headers=headers_json)
            count = None
            if r.status_code == 200:
                try: count = len(r.json().get("listing", []))
                except Exception: pass
            result["probes"]["api_v1_listings"] = {"status": r.status_code, "count": count, "preview": r.text[:200]}
        except Exception as exc:
            result["probes"]["api_v1_listings"] = {"error": str(exc)[:80]}

        # 2. www.tickpick.com/api (internal)
        for api_path in [
            f"/api/listings/event/{event_id}",
            f"/api/v1/listings/event/{event_id}",
            f"/api/event/{event_id}/listings",
        ]:
            try:
                r = await client.get(f"https://www.tickpick.com{api_path}", headers=headers_json, timeout=10.0)
                result["probes"][f"www_api_{api_path.split('/')[2]}"] = {"status": r.status_code, "size": len(r.content), "preview": r.text[:200]}
            except Exception as exc:
                result["probes"][f"www_api{api_path[:20]}"] = {"error": str(exc)[:60]}

        # 3. Next.js RSC (React Server Component) data endpoint
        # Next.js 13+ apps expose /_next/data/{buildId}/... for SSR data
        try:
            # First get build ID from HTML
            r_html = await client.get(f"https://www.tickpick.com/buy-tickets/{event_id}/", headers=headers_desktop, timeout=20.0)
            html = r_html.text
            result["probes"]["html_fetch"] = {"status": r_html.status_code, "size": len(html)}

            build_id = None
            m = re.search(r'"buildId"\s*:\s*"([^"]+)"', html)
            if m:
                build_id = m.group(1)

            # Also look for RSC payload in HTML (self.__next_f.push patterns)
            rsc_payloads = re.findall(r'self\.__next_f\.push\(\[.*?\]\)', html, re.DOTALL)
            result["probes"]["rsc_payloads_count"] = len(rsc_payloads)
            if rsc_payloads:
                result["probes"]["rsc_sample"] = rsc_payloads[0][:300]

            # Listing-related patterns in any format
            all_numbers = re.findall(r'"p"\s*:\s*(\d{4,6})', html)[:20]  # TP price in cents
            section_data = re.findall(r'"s"\s*:\s*"([A-Z0-9 ]{2,15})"', html)[:10]
            listing_ids = re.findall(r'"id"\s*:\s*(\d{7,9})', html)[:10]
            result["probes"]["html_listing_signals"] = {
                "price_fields_p": all_numbers,
                "section_fields_s": section_data,
                "listing_ids": listing_ids,
            }

            # Check for hydration data chunks (Next.js app router embeds RSC as script chunks)
            script_chunks = re.findall(r'<script[^>]*>([^<]{200,})</script>', html)
            for chunk in script_chunks:
                # Look for listing-shaped data: has "id" and "p" (price) and "s" (section)
                if '"p":' in chunk and '"s":' in chunk and '"id":' in chunk and len(chunk) > 1000:
                    result["probes"]["hydration_listing_chunk"] = {"size": len(chunk), "preview": chunk[:400]}
                    break

            # Build ID based Next.js data fetch
            if build_id:
                result["probes"]["build_id"] = build_id
                nxt_url = f"https://www.tickpick.com/_next/data/{build_id}/buy-tickets/{event_id}.json"
                try:
                    r2 = await client.get(nxt_url, headers=headers_json, timeout=15.0)
                    is_json = "json" in r2.headers.get("content-type", "")
                    count2 = None
                    if is_json and r2.status_code == 200:
                        try:
                            d2 = r2.json()
                            pp = (d2.get("pageProps") or {})
                            for key in ("listings", "listing", "initialListings"):
                                v = pp.get(key)
                                if isinstance(v, list): count2 = len(v); break
                        except Exception:
                            pass
                    result["probes"]["nextjs_data_fetch"] = {"url": nxt_url[:80], "status": r2.status_code, "is_json": is_json, "count": count2, "preview": r2.text[:300]}
                except Exception as exc:
                    result["probes"]["nextjs_data_fetch"] = {"error": str(exc)[:80]}

        except Exception as exc:
            result["probes"]["html_phase"] = {"error": str(exc)[:100]}

        # 4. Mobile app API endpoints
        for mob_path in [
            f"https://api.tickpick.com/1.0/listings/event/{event_id}?platform=ios",
            f"https://api.tickpick.com/1.0/event/{event_id}",
            f"https://api.tickpick.com/1.0/performances/event/{event_id}",
        ]:
            label = mob_path.split("/")[-1].split("?")[0]
            try:
                r = await client.get(mob_path, headers={**headers_json, "User-Agent": "TickPick/7.0.0 (iPhone; iOS 17.0; Scale/3.00)"}, timeout=10.0)
                count = None
                if r.status_code == 200:
                    try:
                        d = r.json()
                        for k in ("listing", "listings", "data", "results"):
                            v = d.get(k)
                            if isinstance(v, list): count = len(v); break
                    except Exception:
                        pass
                result["probes"][f"mobile_{label}"] = {"status": r.status_code, "size": len(r.content), "count": count, "preview": r.text[:200]}
            except Exception as exc:
                result["probes"][f"mobile_{label}"] = {"error": str(exc)[:60]}

        # 5. GraphQL probe
        try:
            gql_r = await client.post(
                "https://api.tickpick.com/graphql",
                json={"query": f'{{ event(id: "{event_id}") {{ id listings {{ id price section row }} }} }}'},
                headers={**headers_json, "Content-Type": "application/json"},
                timeout=10.0,
            )
            result["probes"]["graphql"] = {"status": gql_r.status_code, "size": len(gql_r.content), "preview": gql_r.text[:300]}
        except Exception as exc:
            result["probes"]["graphql"] = {"error": str(exc)[:60]}

        # 6. Slug-based HTML URL (if event has one)
        try:
            r_slug = await client.get(url or f"https://www.tickpick.com/buy-tickets/{event_id}/", headers=headers_mobile, timeout=20.0)
            html_mob = r_slug.text
            mob_prices = re.findall(r'"p"\s*:\s*(\d{4,6})', html_mob)[:20]
            mob_sections = re.findall(r'"s"\s*:\s*"([A-Z0-9 ]{2,15})"', html_mob)[:10]
            result["probes"]["mobile_html"] = {"status": r_slug.status_code, "size": len(html_mob), "price_p_fields": mob_prices, "section_s_fields": mob_sections}
        except Exception as exc:
            result["probes"]["mobile_html"] = {"error": str(exc)[:80]}

        # 7. Try slug event URL if available
        if url and "tickpick.com/buy-" in url and "buy-tickets" not in url:
            try:
                r_slug2 = await client.get(url, headers=headers_desktop, timeout=20.0)
                html_slug2 = r_slug2.text
                slug_prices = re.findall(r'"p"\s*:\s*(\d{4,6})', html_slug2)[:20]
                result["probes"]["slug_url_html"] = {"status": r_slug2.status_code, "size": len(html_slug2), "price_p_fields": slug_prices}
            except Exception as exc:
                result["probes"]["slug_url_html"] = {"error": str(exc)[:80]}

    return result


@router.get("/extract-stubhub-grid-v2")
async def extract_stubhub_grid_v2(event_id: str, url: str = ""):
    """Debug: try multiple regex patterns to find the viagogo-event script."""
    import httpx, re, json as _json
    target_url = url or f"https://www.stubhub.com/event/{event_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(target_url, headers=headers)
    html = resp.text

    result = {"status": resp.status_code, "size": len(html)}

    # Try: split on </script> and find the chunk containing the grid
    chunks = html.split("</script>")
    grid_chunk = None
    for chunk in chunks:
        if '"appName":"viagogo-event"' in chunk and '"grid"' in chunk and '"items"' in chunk:
            # Find the JSON start
            start = chunk.rfind('{"appName":"viagogo-event"')
            if start >= 0:
                grid_chunk = chunk[start:]
                break

    if not grid_chunk:
        result["error"] = "grid chunk not found by split"
        # Debug: show all script tag starts
        result["script_starts"] = []
        for i, chunk in enumerate(chunks[:15]):
            if 'appName' in chunk or 'grid' in chunk:
                start = max(chunk.rfind('<script'), 0)
                result["script_starts"].append({"idx": i, "tail": chunk[start:start+100]})
        return result

    result["chunk_size"] = len(grid_chunk)
    result["chunk_preview"] = grid_chunk[:200]

    # Parse the JSON chunk
    try:
        data = _json.loads(grid_chunk)
        items = (data.get("grid") or {}).get("items", [])
        result["items_count"] = len(items)
        result["data_keys"] = list(data.keys())[:15]
        if items:
            item0 = items[0]
            result["item0_keys"] = list(item0.keys())
            result["item0_sample"] = {
                "id": item0.get("id"),
                "section": item0.get("section"),
                "row": item0.get("row"),
                "qty": item0.get("quantity") or item0.get("qty"),
                "currentPrice": item0.get("currentPrice") or item0.get("current_price") or item0.get("price"),
                "allInPrice": item0.get("allInPrice") or item0.get("all_in_price"),
            }
    except Exception as exc:
        result["parse_error"] = str(exc)[:100]
        result["chunk_end"] = grid_chunk[-50:]

    return result
