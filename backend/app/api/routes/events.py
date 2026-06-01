from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import hashlib
import re

from app.database import get_db
from app.models import Event, TrackedEvent, Marketplace, Venue, Listing
from app.models.listing import PollRun
from app.config import get_settings
from app.utils.lineage import trace_event, add_stage, build_event_lineage
from app.utils.event_trace import emit_event_trace
from app.utils.freshness import compute_freshness, is_current

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
    #   a) Last successful poll_run.completed_at per tracked_event
    #   b) Recent poll runs (30 days) for consecutive failure count
    last_success_map: dict[int, datetime] = {}
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

        freshness = compute_freshness(
            marketplace_slug=mp.slug,
            event_date=event.event_date,
            poll_interval_minutes=te.poll_interval_minutes or 1440,
            last_success_at=last_success_map.get(te.id),
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
    event = await _get_event(db, event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    await db.delete(event)
    await db.commit()
