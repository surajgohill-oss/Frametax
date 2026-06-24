import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import hashlib
import re

from app.database import get_db
from app.models import Event, TrackedEvent, Marketplace, Venue, Listing
from app.models.listing import PollRun, ListingSnapshot
from app.config import get_settings
from app.utils.lineage import trace_event, add_stage, build_event_lineage
from app.utils.event_trace import emit_event_trace
from app.utils.freshness import compute_freshness, is_current

router = APIRouter(prefix="/events", tags=["events"])
settings = get_settings()
logger = logging.getLogger(__name__)


def _canonical_id(title: str, venue_slug: str, event_date: datetime) -> str:
    raw = f"{venue_slug}|{event_date.date()}|{title.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _extract_external_id_from_url(mp_slug: str, url: str) -> str | None:
    """Extract marketplace event ID from URL without a network call."""
    if mp_slug == "stubhub":
        m = re.search(r"/event/(\d+)", url)
        if m:
            return m.group(1)
        m = re.search(r"/(\d{6,})(?:[/?#]|$)", url)
        return m.group(1) if m else None
    if mp_slug == "seatgeek":
        for pattern in (r"/e/(\d+)", r"--(\d{5,})(?:[/?#]|$)", r"/(\d{5,})(?:[/?#]|$)"):
            m = re.search(pattern, url)
            if m:
                return m.group(1)
    return None


async def _get_event(db, event_id: int):
    result = await db.execute(
        select(Event).options(
            selectinload(Event.venue),
            selectinload(Event.tracked_events).selectinload(TrackedEvent.marketplace),
        ).where(Event.id == event_id)
    )
    return result.scalar_one_or_none()


async def _enrich_event(db, event: Event, trace: dict | None = None) -> dict:
    if trace:
        add_stage(trace, "marketplace_merge_start")

    # ── Step 1: Load tracked rows (TrackedEvent × Marketplace) ───────────────
    result = await db.execute(
        select(TrackedEvent, Marketplace)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(TrackedEvent.event_id == event.id)
    )
    tracked_rows = result.all()
    marketplace_ids = [mp.id for _, mp in tracked_rows]
    te_ids          = [te.id for te, _ in tracked_rows]

    # ── Step 2: Active listing min price + count per marketplace ─────────────
    asks_by_mp_id:  dict[int, float] = {}
    count_by_mp_id: dict[int, int]   = {}

    if marketplace_ids:
        asks_result = await db.execute(
            select(Listing.marketplace_id, func.min(Listing.price), func.count())
            .where(
                Listing.event_id == event.id,
                Listing.marketplace_id.in_(marketplace_ids),
                Listing.is_active == True,
            )
            .group_by(Listing.marketplace_id)
        )
        for mp_id, min_price, cnt in asks_result.all():
            asks_by_mp_id[mp_id]  = float(min_price)
            count_by_mp_id[mp_id] = cnt

    # ── Step 3: Freshness data ───────────────────────────────────────────────
    #   a) Last successful poll_run (any result) per tracked_event
    #   b) Last data-producing poll (listings_found > 0) per tracked_event
    #   c) Recent poll runs (30 days) for consecutive failure count
    last_success_map: dict[int, datetime] = {}
    last_data_map:    dict[int, datetime] = {}   # only polls with listings_found > 0
    runs_by_te:       dict[int, list]     = {}

    if te_ids:
        lsr = await db.execute(
            select(PollRun.tracked_event_id, func.max(PollRun.completed_at))
            .where(
                PollRun.tracked_event_id.in_(te_ids),
                PollRun.status == "success",
                PollRun.completed_at.isnot(None),
            )
            .group_by(PollRun.tracked_event_id)
        )
        last_success_map = {row[0]: row[1] for row in lsr.all()}

        # Data-producing polls only (listings_found > 0 means real ticket data
        # was collected after the parking filter, not just a successful empty run)
        ldr = await db.execute(
            select(PollRun.tracked_event_id, func.max(PollRun.completed_at))
            .where(
                PollRun.tracked_event_id.in_(te_ids),
                PollRun.status == "success",
                PollRun.completed_at.isnot(None),
                PollRun.listings_found > 0,
            )
            .group_by(PollRun.tracked_event_id)
        )
        last_data_map = {row[0]: row[1] for row in ldr.all()}

        cutoff = datetime.utcnow() - timedelta(days=30)
        rrr = await db.execute(
            select(PollRun)
            .where(
                PollRun.tracked_event_id.in_(te_ids),
                PollRun.started_at >= cutoff,
            )
            .order_by(PollRun.started_at.desc())
        )
        for run in rrr.scalars().all():
            runs_by_te.setdefault(run.tracked_event_id, []).append(run)

    # ── Step 4: Build per-marketplace prices + freshness ─────────────────────
    mp_asks:         dict[str, float] = {}   # all active listings (stale-inclusive)
    fresh_mp_asks:   dict[str, float] = {}   # fresh + late only
    freshness_by_mp: dict[str, dict]  = {}
    total_listings_count = sum(count_by_mp_id.values())
    fresh_total          = 0

    for te, mp in tracked_rows:
        ask   = asks_by_mp_id.get(mp.id)
        count = count_by_mp_id.get(mp.id, 0)

        if ask is not None:
            mp_asks[mp.slug] = ask

        # Count consecutive failures at head of recent runs (desc by started_at)
        te_runs = runs_by_te.get(te.id, [])
        consecutive_failures = 0
        for run in te_runs:
            if run.status == "error":
                consecutive_failures += 1
            else:
                break

        te_last_success = last_success_map.get(te.id)
        te_last_data    = last_data_map.get(te.id)
        # polls_ran_no_data: polls succeeded but none produced useful listings
        polls_ran_no_data = (te_last_success is not None) and (te_last_data is None)

        freshness = compute_freshness(
            marketplace_slug=mp.slug,
            event_date=event.event_date,
            poll_interval_minutes=te.poll_interval_minutes or 1440,
            last_success_at=te_last_success,
            last_data_at=te_last_data,
            polls_ran_no_data=polls_ran_no_data,
            consecutive_failures=consecutive_failures,
        )
        freshness_by_mp[mp.slug] = freshness

        if trace:
            add_stage(trace, f"{mp.slug}_fetch", {
                "min_ask":   ask,
                "freshness": freshness["freshness_status"],
            })

        # Only fresh/late data counts toward current price view
        if is_current(freshness) and ask is not None:
            fresh_mp_asks[mp.slug] = ask
            fresh_total += count

    # ── Step 5: Summary prices ───────────────────────────────────────────────
    # lowest_price = fresh/late only   (current market truth)
    # historical_lowest_price          = stale-inclusive (display reference)
    lowest_price            = min(fresh_mp_asks.values()) if fresh_mp_asks else None
    historical_lowest_price = min(mp_asks.values())       if mp_asks       else None

    if trace:
        add_stage(trace, "marketplace_merge_complete", {"slugs": list(mp_asks.keys())})

    # ── Step 6: Build response ───────────────────────────────────────────────
    tracked = event.tracked_events or []
    stubhub_te  = next((te for te in tracked if te.marketplace.slug == "stubhub"),  None)
    seatgeek_te = next((te for te in tracked if te.marketplace.slug == "seatgeek"), None)
    times = [te.next_poll_at for te in tracked if te.next_poll_at and te.is_active]

    def _fresh_ask(slug: str) -> float | None:
        """Return price only when the marketplace has current (fresh/late) data."""
        f = freshness_by_mp.get(slug, {})
        if is_current(f):
            return mp_asks.get(slug)
        return None

    payload = {
        "id":           event.id,
        "canonical_id": event.canonical_id,
        "title":        event.title,
        "artist":       event.artist,
        "venue_id":     event.venue_id,
        "venue_name":   event.venue.name  if event.venue else None,
        "venue_slug":   event.venue.slug  if event.venue else None,
        "event_date":   event.event_date.isoformat(),
        "is_active":    any(te.is_active for te in tracked),
        "stubhub_url":  stubhub_te.external_url  if stubhub_te  else None,
        "seatgeek_url": seatgeek_te.external_url if seatgeek_te else None,

        # Legacy two-marketplace price fields — null when stale (not current market truth)
        "lowest_ask_stubhub":  _fresh_ask("stubhub"),
        "lowest_ask_seatgeek": _fresh_ask("seatgeek"),

        # Price floor (fresh/late marketplaces only — current market truth)
        "lowest_price": lowest_price,
        # Historical floor including stale data (for display context, NOT market truth)
        "historical_lowest_price": historical_lowest_price,

        # Listing counts
        "total_listings":       total_listings_count,  # all active (stale-inclusive, for breakdown)
        "fresh_total_listings": fresh_total,           # fresh+late only (for summary display)

        # Marketplace prices — fresh/late only (current market truth)
        "marketplace_prices": {slug: ask for slug, ask in fresh_mp_asks.items()},
        # All marketplace prices including stale (for historical breakdown display)
        "all_marketplace_prices": {slug: ask for slug, ask in mp_asks.items()},

        # Per-marketplace freshness classification
        "marketplace_freshness": freshness_by_mp,

        "custom_artwork_url": event.custom_artwork_url,

        "next_poll_at": min(times).isoformat() if times else None,
        "created_at":   event.created_at.isoformat() if event.created_at else None,

        "tracked_events": [
            {
                "id":                  te.id,
                "marketplace_slug":    te.marketplace.slug,
                "external_event_id":   te.external_event_id,
                "external_url":        te.external_url,
                "is_active":           te.is_active,
                "poll_interval_minutes": te.poll_interval_minutes,
                "last_polled_at":      te.last_polled_at.isoformat() if te.last_polled_at else None,
                "next_poll_at":        te.next_poll_at.isoformat()   if te.next_poll_at   else None,
                # Freshness fields injected directly into each tracked_event
                **freshness_by_mp.get(te.marketplace.slug, {}),
            }
            for te in tracked
        ],
    }

    payload["lineage"] = build_event_lineage(event, tracked, marketplace_ids)

    emit_event_trace("ENRICH", event.id, {
        "listings_count":       total_listings_count,
        "fresh_listings_count": fresh_total,
        "marketplace_count":    len(mp_asks),
        "marketplaces":         list(mp_asks.keys()),
        "stale_marketplaces":   [
            slug for slug, f in freshness_by_mp.items() if not is_current(f)
        ],
    })

    if trace:
        add_stage(trace, "response_built")
        payload["__trace"] = trace

    return payload


@router.get("/")
async def list_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).options(
            selectinload(Event.venue),
            selectinload(Event.tracked_events).selectinload(TrackedEvent.marketplace),
        ).where(Event.status != "archived").order_by(Event.event_date)
    )
    output = []
    for e in result.scalars().all():
        trace = trace_event(str(e.id))
        add_stage(trace, "db_read", {"canonical_id": e.canonical_id})
        enriched = await _enrich_event(db, e, trace=trace)
        add_stage(trace, "response_appended", {"list_position": len(output)})
        output.append(enriched)
    return output


@router.post("/", status_code=201)
async def create_event(data: dict, db: AsyncSession = Depends(get_db)):
    if settings.discovery_freeze:
        logger.warning(
            "EVENT_FREEZE_ACTIVE: POST /api/events/ rejected — reason=frozen"
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "EVENT_FREEZE_ACTIVE: Event creation is frozen while duplicate "
                "reconciliation is in progress. No new events may be added."
            ),
        )

    count_result = await db.execute(select(func.count()).select_from(Event))
    if count_result.scalar_one() >= settings.max_tracked_events:
        raise HTTPException(400, f"Maximum {settings.max_tracked_events} events reached")

    venue_result = await db.execute(select(Venue).where(Venue.slug == data["venue_slug"]))
    venue = venue_result.scalar_one_or_none()
    if not venue:
        raise HTTPException(404, f"Venue '{data['venue_slug']}' not found")

    event_date = datetime.fromisoformat(data["event_date"].replace("Z", "+00:00"))
    canonical_id = _canonical_id(data["title"], data["venue_slug"], event_date)

    existing = await db.execute(select(Event).where(Event.canonical_id == canonical_id))
    event = existing.scalar_one_or_none()
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

    poll_interval = int(data.get("poll_interval_minutes", 60))
    for mp_slug, url_key in [("stubhub", "stubhub_url"), ("seatgeek", "seatgeek_url")]:
        url = data.get(url_key, "").strip()
        if not url:
            continue
        mp_result = await db.execute(select(Marketplace).where(Marketplace.slug == mp_slug))
        mp = mp_result.scalar_one_or_none()
        if not mp:
            continue
        existing_te = await db.execute(
            select(TrackedEvent).where(
                TrackedEvent.event_id == event.id,
                TrackedEvent.marketplace_id == mp.id,
            )
        )
        if not existing_te.scalar_one_or_none():
            external_event_id = _extract_external_id_from_url(mp_slug, url)
            db.add(TrackedEvent(
                event_id=event.id,
                marketplace_id=mp.id,
                external_url=url,
                poll_interval_minutes=poll_interval,
                external_event_id=external_event_id,
            ))
            emit_event_trace("INGEST", event.id, {
                "external_event_id": external_event_id,
                "marketplace":       mp_slug,
                "source":            "api",
            })

    await db.commit()
    event = await _get_event(db, event.id)
    return await _enrich_event(db, event)


@router.get("/{event_id}")
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await _get_event(db, event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    return await _enrich_event(db, event)


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Soft-delete: mark event status='archived', deactivate all TrackedEvents.
    Hard delete is blocked by FK constraints (listings, tracked_events, snapshots).
    Frontend watchlist remove uses this endpoint.
    """
    event = await _get_event(db, event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    event.status = "archived"
    te_rows = (await db.execute(
        select(TrackedEvent).where(TrackedEvent.event_id == event_id)
    )).scalars().all()
    for te in te_rows:
        te.is_active = False
    await db.commit()


@router.patch("/{event_id}/artwork")
async def set_event_artwork(
    event_id: int,
    url: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Set or clear custom artwork for an event.

    Accepts EITHER:
      - url=<string>  (JSON form field) — persists a remote image URL directly.
      - file=<upload> — stores image locally under /static/uploads/ (dev only;
                        Railway's ephemeral filesystem means this does NOT persist
                        across deploys — wire object storage for production).
      - url=""        — clears custom artwork, restoring auto-detected art.
    """
    event = await _get_event(db, event_id)
    if not event:
        raise HTTPException(404, "Event not found")

    if url is not None:
        # url="" means clear; any non-empty string is stored as-is
        event.custom_artwork_url = url.strip() or None

    elif file is not None:
        # Local file upload — dev/testing only
        ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in ALLOWED:
            raise HTTPException(400, f"Unsupported content type: {file.content_type}")

        upload_dir = Path(__file__).parent.parent.parent.parent / "static" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        ext = {"image/jpeg": ".jpg", "image/png": ".png",
               "image/webp": ".webp", "image/gif": ".gif"}.get(file.content_type, ".jpg")
        filename = f"event_{event_id}_{uuid.uuid4().hex[:8]}{ext}"
        dest = upload_dir / filename

        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10 MB cap
            raise HTTPException(400, "Image too large (max 10 MB)")

        dest.write_bytes(contents)

        backend_url = os.environ.get("BACKEND_PUBLIC_URL", "http://localhost:8080")
        event.custom_artwork_url = f"{backend_url}/uploads/{filename}"

    else:
        raise HTTPException(400, "Provide either url= or file=")

    await db.commit()
    return {"custom_artwork_url": event.custom_artwork_url}


@router.patch("/tracked/{te_id}")
async def patch_tracked_event(te_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    """Update mutable fields on a tracked event (external_url, external_event_id, is_active, poll_interval_minutes)."""
    result = await db.execute(
        select(TrackedEvent)
        .options(selectinload(TrackedEvent.marketplace))
        .where(TrackedEvent.id == te_id)
    )
    te = result.scalar_one_or_none()
    if not te:
        raise HTTPException(404, f"TrackedEvent {te_id} not found")

    allowed = {"external_url", "external_event_id", "is_active", "poll_interval_minutes"}
    updated = {}
    for field in allowed:
        if field in body:
            setattr(te, field, body[field])
            updated[field] = body[field]

    # Auto-extract external_event_id from URL if not explicitly provided
    if "external_url" in updated and "external_event_id" not in body:
        mp_slug = te.marketplace.slug if te.marketplace else ""
        extracted = _extract_external_id_from_url(mp_slug, updated["external_url"])
        if extracted:
            te.external_event_id = extracted
            updated["external_event_id"] = extracted

    await db.commit()
    await db.refresh(te)
    return {"te_id": te_id, "updated": updated, "external_url": te.external_url, "external_event_id": te.external_event_id}


@router.post("/{event_id}/tracked", status_code=201)
async def add_tracked_event(event_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    """Add a new tracked_event for an existing event on a given marketplace.
    Body: { marketplace_slug: str, external_event_id?: str, external_url?: str, poll_interval_minutes?: int }
    """
    event = await _get_event(db, event_id)
    if not event:
        raise HTTPException(404, "Event not found")

    mp_slug = body.get("marketplace_slug", "").strip()
    if not mp_slug:
        raise HTTPException(400, "marketplace_slug required")

    mp_result = await db.execute(select(Marketplace).where(Marketplace.slug == mp_slug))
    mp = mp_result.scalar_one_or_none()
    if not mp:
        raise HTTPException(404, f"Marketplace '{mp_slug}' not found")

    existing = (await db.execute(
        select(TrackedEvent).where(
            TrackedEvent.event_id == event_id,
            TrackedEvent.marketplace_id == mp.id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(409, f"TrackedEvent for {mp_slug} already exists (te_id={existing.id})")

    ext_url = (body.get("external_url") or "").strip() or None
    ext_id  = (body.get("external_event_id") or "").strip() or None
    if not ext_id and ext_url:
        ext_id = _extract_external_id_from_url(mp_slug, ext_url)

    poll_interval = int(body.get("poll_interval_minutes", 60))
    te = TrackedEvent(
        event_id=event_id,
        marketplace_id=mp.id,
        external_url=ext_url,
        external_event_id=ext_id,
        poll_interval_minutes=poll_interval,
        is_active=True,
    )
    db.add(te)
    await db.commit()
    await db.refresh(te)
    return {
        "te_id": te.id,
        "event_id": event_id,
        "marketplace_slug": mp_slug,
        "external_event_id": te.external_event_id,
        "external_url": te.external_url,
        "poll_interval_minutes": te.poll_interval_minutes,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 — URL FALLBACK REPAIR PATH
# POST /api/events/{event_id}/marketplace-url
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel


class MarketplaceUrlPayload(_BaseModel):
    marketplace: str
    url: str


_CORE_MP_SLUGS = {"gametime", "stubhub", "tickpick", "vividseats"}


@router.post("/{event_id}/marketplace-url")
async def attach_marketplace_url(
    event_id: int,
    payload: MarketplaceUrlPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Task 2 — URL Fallback Repair Path.

    Attach a marketplace URL to an existing canonical event.
    Behavior:
      1. Validate event + marketplace exist
      2. Upsert tracked_event: set external_url, attempt ID extraction
      3. Run immediate poll for the marketplace (background)
      4. Return health status: external_id, listings_count, floor, remediation

    Required for SH/TP where automated ID resolution is blocked.
    """
    mp_slug = payload.marketplace.strip().lower()
    if mp_slug not in _CORE_MP_SLUGS:
        raise HTTPException(400, f"marketplace must be one of: {sorted(_CORE_MP_SLUGS)}")

    url = payload.url.strip()
    if not url.startswith("http"):
        raise HTTPException(400, "url must be a valid http/https URL")

    # 1. Validate event
    event = await _get_event(db, event_id)
    if not event:
        raise HTTPException(404, f"Event {event_id} not found")

    # 2. Resolve marketplace row
    mp = (await db.execute(
        select(Marketplace).where(Marketplace.slug == mp_slug)
    )).scalar_one_or_none()
    if not mp:
        raise HTTPException(404, f"Marketplace '{mp_slug}' not found in DB")

    # 3. Upsert tracked_event
    te = (await db.execute(
        select(TrackedEvent).where(
            TrackedEvent.event_id == event_id,
            TrackedEvent.marketplace_id == mp.id,
        )
    )).scalar_one_or_none()

    ext_id = _extract_external_id_from_url(mp_slug, url)

    if te is None:
        te = TrackedEvent(
            event_id=event_id,
            marketplace_id=mp.id,
            external_url=url,
            external_event_id=ext_id,
            poll_interval_minutes=60,
            is_active=True,
            consecutive_zero_inventory_count=0,
        )
        db.add(te)
        action = "created"
    else:
        te.external_url = url
        if ext_id:
            te.external_event_id = ext_id
        if not te.is_active:
            te.is_active = True
        action = "updated"

    await db.commit()
    await db.refresh(te)

    # 4. Run immediate poll (fire-and-forget background task)
    poll_result = None
    poll_error = None
    try:
        from app.database import AsyncSessionLocal
        from app.scheduler import _run_collector_for_event
        te.event = event
        await _run_collector_for_event(mp_slug, te, event)
        # Re-read listings after poll
        from sqlalchemy import func as _func
        count_row = (await db.execute(
            select(
                _func.count(Listing.id).label("cnt"),
                _func.min(Listing.price).label("floor"),
            ).where(
                Listing.event_id == event_id,
                Listing.marketplace_id == mp.id,
                Listing.is_active == True,
            )
        )).fetchone()
        listings_count = int(count_row.cnt or 0)
        floor_price    = float(count_row.floor) if count_row.floor else None
        poll_result = "success"
    except Exception as exc:
        listings_count = 0
        floor_price    = None
        poll_result = "error"
        poll_error  = str(exc)
        logger.warning("URL_FALLBACK: poll failed mp=%s event=%d: %s", mp_slug, event_id, exc)

    # 5. Determine health status
    if listings_count > 0:
        status = "POPULATED"
        remediation = None
    elif ext_id:
        status = "ID_RESOLVED_PENDING_POLL"
        remediation = "ID extracted. Scheduler will poll on next cycle."
    else:
        status = "NEEDS_MANUAL_ID"
        remediation = f"Could not extract external event ID from URL. Check URL format for {mp_slug}."

    return {
        "event_id":       event_id,
        "marketplace":    mp_slug,
        "action":         action,
        "external_url":   te.external_url,
        "external_id":    te.external_event_id,
        "id_extracted":   bool(ext_id),
        "poll_result":    poll_result,
        "poll_error":     poll_error,
        "listings_count": listings_count,
        "floor":          floor_price,
        "status":         status,
        "remediation":    remediation,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 — Marketplace health aliases at /api/events/{id}/...
# Delegates to the canonical service functions already in marketplace_health.py
# ─────────────────────────────────────────────────────────────────────────────

from app.services.marketplace_health import (
    get_event_marketplace_health as _get_mp_health,
    get_event_alerts as _get_mp_alerts,
)


@router.get("/{event_id}/marketplace-health")
async def event_marketplace_health(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Task 1 — Canonical marketplace health for one event.
    Core marketplaces: gametime / stubhub / tickpick / vividseats.
    SeatGeek and Ticketmaster included in response but excluded from core coverage score.
    """
    return await _get_mp_health(event_id, db)


@router.get("/{event_id}/alerts")
async def event_health_alerts(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Health alerts for one event.
    Marketplace alert types: MARKETPLACE_STALE, MARKETPLACE_BLOCKED, MARKETPLACE_PENDING,
                             LOW_COVERAGE, NEEDS_URL, RESOLUTION_FAILED.
    Poll-failure alert types: POLL_TASK_CRASH, COLLECTOR_ERROR, SNAPSHOT_NOT_WRITTEN,
                              POLL_STALE, MARKETPLACE_STALE, NEEDS_MARKETPLACE_URL, BLOCKED.
    """
    base = await _get_mp_alerts(event_id, db)
    poll_alerts = await _poll_failure_alerts(event_id, db)
    if poll_alerts:
        base["alerts"] = poll_alerts + base["alerts"]
        base["alert_count"] = len(base["alerts"])
        base["has_critical"] = any(a["severity"] == "RED" for a in base["alerts"])
    return base


async def _poll_failure_alerts(event_id: int, db: AsyncSession) -> list:
    """Returns poll-failure alert entries for tracked_events belonging to this event."""

    now = datetime.utcnow()
    stale_threshold = now - timedelta(hours=6)
    snapshot_threshold = now - timedelta(hours=24)

    alerts = []

    # All tracked_events for this event
    te_rows = (await db.execute(
        select(TrackedEvent).where(TrackedEvent.event_id == event_id)
    )).scalars().all()

    for te in te_rows:
        mp = (await db.execute(
            select(Marketplace).where(Marketplace.id == te.marketplace_id)
        )).scalar_one_or_none()
        slug = mp.slug if mp else f"marketplace_id={te.marketplace_id}"

        # Most recent poll_run for this tracked_event
        last_poll = (await db.execute(
            select(PollRun)
            .where(PollRun.tracked_event_id == te.id)
            .order_by(PollRun.started_at.desc())
            .limit(1)
        )).scalar_one_or_none()

        if not last_poll:
            # Never polled at all
            if not te.external_url:
                alerts.append({
                    "type": "NEEDS_MARKETPLACE_URL",
                    "marketplace": slug,
                    "severity": "RED",
                    "message": f"{slug}: no external URL and never polled",
                    "remediation": "Set external_url on tracked_event or run discovery.",
                })
            continue

        if last_poll.status == "error":
            msg = last_poll.error_message or "unknown error"
            alerts.append({
                "type": "COLLECTOR_ERROR",
                "marketplace": slug,
                "severity": "RED",
                "message": f"{slug}: last poll failed — {msg[:120]}",
                "remediation": "Check collector logs. Possibly bot detection or auth issue.",
            })

        # Check poll staleness
        if last_poll.started_at < stale_threshold:
            hours_ago = (now - last_poll.started_at).total_seconds() / 3600
            alerts.append({
                "type": "POLL_STALE",
                "marketplace": slug,
                "severity": "YELLOW",
                "message": f"{slug}: last poll {hours_ago:.1f}h ago (threshold 6h)",
                "remediation": "Check if scheduler is running and next_poll_at is being set.",
            })

        # Check snapshot staleness (listing_snapshots uses event_id + marketplace_id, not tracked_event_id)
        last_snap_ts = (await db.execute(
            select(ListingSnapshot.snapshot_at)
            .where(
                ListingSnapshot.event_id == te.event_id,
                ListingSnapshot.marketplace_id == te.marketplace_id,
            )
            .order_by(ListingSnapshot.snapshot_at.desc())
            .limit(1)
        )).scalar_one_or_none()

        if last_snap_ts is None:
            alerts.append({
                "type": "SNAPSHOT_NOT_WRITTEN",
                "marketplace": slug,
                "severity": "YELLOW",
                "message": f"{slug}: no listing snapshot ever written",
                "remediation": "Confirm collector is returning listings and _process_result is writing snapshots.",
            })
        elif last_snap_ts < snapshot_threshold:
            hours_ago = (now - last_snap_ts).total_seconds() / 3600
            alerts.append({
                "type": "SNAPSHOT_NOT_WRITTEN",
                "marketplace": slug,
                "severity": "YELLOW",
                "message": f"{slug}: last snapshot {hours_ago:.1f}h ago (threshold 24h)",
                "remediation": "Check if polls are succeeding and returning non-empty listings.",
            })

    # Global scheduler crash alert from ring buffer (affects all events)
    try:
        from app.scheduler import get_reliability_state
        state = get_reliability_state()
        sig = state.get("active_crash_signature")
        if sig:
            alerts.insert(0, {
                "type": "POLL_TASK_CRASH",
                "marketplace": None,
                "severity": "RED",
                "message": f"Scheduler crash active: {sig[:150]}",
                "remediation": "Fix the root cause in scheduler.py / TrackedEvent model and redeploy.",
            })
    except Exception:
        pass

    return alerts
