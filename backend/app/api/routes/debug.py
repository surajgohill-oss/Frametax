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
    external_event_id: str = Query(..., description="VS production ID to set"),
    db: AsyncSession = Depends(get_db),
):
    """
    Directly set external_event_id on an existing TrackedEvent.
    Used for manual resolution when the auto-resolver can't find the event.
    """
    from app.models import TrackedEvent

    te = (await db.execute(select(TrackedEvent).where(TrackedEvent.id == te_id))).scalar_one_or_none()
    if not te:
        return {"error": f"TrackedEvent {te_id} not found"}

    old_id = te.external_event_id
    te.external_event_id = external_event_id
    await db.commit()
    return {"te_id": te_id, "old_external_event_id": old_id, "new_external_event_id": external_event_id, "ok": True}


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
