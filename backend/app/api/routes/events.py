from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime
import hashlib
import re

from app.database import get_db
from app.models import Event, TrackedEvent, Marketplace, Venue, Listing
from app.config import get_settings
from app.utils.lineage import trace_event, add_stage, build_event_lineage
from app.utils.event_trace import emit_event_trace

router = APIRouter(prefix="/events", tags=["events"])
settings = get_settings()


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
    mp_asks: dict[str, float] = {}
    result = await db.execute(
        select(TrackedEvent, Marketplace)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(TrackedEvent.event_id == event.id)
    )

    if trace:
        add_stage(trace, "marketplace_merge_start")

    tracked_rows = result.all()
    marketplace_ids = [mp.id for _, mp in tracked_rows]

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
        asks_rows = asks_result.all()
        asks_by_marketplace_id = {row[0]: float(row[1]) for row in asks_rows}
        total_listings_count = sum(row[2] for row in asks_rows)
    else:
        asks_by_marketplace_id = {}
        total_listings_count = 0

    for te, mp in tracked_rows:
        ask = asks_by_marketplace_id.get(mp.id)
        if ask is not None:
            mp_asks[mp.slug] = ask

        if trace:
            add_stage(trace, f"{mp.slug}_fetch", {"min_ask": mp_asks.get(mp.slug)})

    # lowest price across all marketplaces
    lowest_price = min(mp_asks.values()) if mp_asks else None

    if trace:
        add_stage(trace, "marketplace_merge_complete", {"slugs": list(mp_asks.keys())})

    tracked = event.tracked_events or []
    stubhub_te = next((te for te in tracked if te.marketplace.slug == "stubhub"), None)
    seatgeek_te = next((te for te in tracked if te.marketplace.slug == "seatgeek"), None)
    times = [te.next_poll_at for te in tracked if te.next_poll_at and te.is_active]

    payload = {
        "id": event.id, "canonical_id": event.canonical_id, "title": event.title,
        "artist": event.artist, "venue_id": event.venue_id,
        "venue_name": event.venue.name if event.venue else None,
        "venue_slug": event.venue.slug if event.venue else None,
        "event_date": event.event_date.isoformat(),
        "is_active": any(te.is_active for te in tracked),
        "stubhub_url": stubhub_te.external_url if stubhub_te else None,
        "seatgeek_url": seatgeek_te.external_url if seatgeek_te else None,
        # Legacy two-marketplace fields (kept for frontend compatibility)
        "lowest_ask_stubhub": mp_asks.get("stubhub"),
        "lowest_ask_seatgeek": mp_asks.get("seatgeek"),
        # Full marketplace price floor (all marketplaces)
        "lowest_price": lowest_price,
        "total_listings": total_listings_count,
        "marketplace_prices": {slug: ask for slug, ask in mp_asks.items()},
        "next_poll_at": min(times).isoformat() if times else None,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "tracked_events": [
            {
                "id": te.id, "marketplace_slug": te.marketplace.slug,
                "external_event_id": te.external_event_id, "external_url": te.external_url,
                "is_active": te.is_active, "poll_interval_minutes": te.poll_interval_minutes,
                "last_polled_at": te.last_polled_at.isoformat() if te.last_polled_at else None,
                "next_poll_at": te.next_poll_at.isoformat() if te.next_poll_at else None,
            } for te in tracked
        ],
    }

    payload["lineage"] = build_event_lineage(event, tracked, marketplace_ids)

    emit_event_trace("ENRICH", event.id, {
        "listings_count": total_listings_count,
        "marketplace_count": len(mp_asks),
        "marketplaces": list(mp_asks.keys()),
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
        ).order_by(Event.event_date)
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
        event = Event(canonical_id=canonical_id, title=data["title"], artist=data.get("artist"), venue_id=venue.id, event_date=event_date)
        db.add(event)
        await db.flush()

    poll_interval = int(data.get("poll_interval_minutes", 60))
    for mp_slug, url_key in [("stubhub", "stubhub_url"), ("seatgeek", "seatgeek_url")]:
        url = data.get(url_key, "").strip()
        if not url: continue
        mp_result = await db.execute(select(Marketplace).where(Marketplace.slug == mp_slug))
        mp = mp_result.scalar_one_or_none()
        if not mp: continue
        existing_te = await db.execute(select(TrackedEvent).where(TrackedEvent.event_id == event.id, TrackedEvent.marketplace_id == mp.id))
        if not existing_te.scalar_one_or_none():
            external_event_id = _extract_external_id_from_url(mp_slug, url)
            db.add(TrackedEvent(event_id=event.id, marketplace_id=mp.id, external_url=url, poll_interval_minutes=poll_interval, external_event_id=external_event_id))
            emit_event_trace("INGEST", event.id, {
                "external_event_id": external_event_id,
                "marketplace": mp_slug,
                "source": "api",
            })

    await db.commit()
    event = await _get_event(db, event.id)
    return await _enrich_event(db, event)


@router.get("/{event_id}")
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await _get_event(db, event_id)
    if not event: raise HTTPException(404, "Event not found")
    return await _enrich_event(db, event)


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await _get_event(db, event_id)
    if not event: raise HTTPException(404, "Event not found")
    await db.delete(event)
    await db.commit()
