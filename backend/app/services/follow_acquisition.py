"""
Follow Acquisition Service

Reads active user_follows and ensures the scope count of future events
is satisfied for each followed entity.

Discovery source: Gametime mobile API (no auth required).
  - Performer search: GET /v1/performers?q={name}
  - Performer events: GET /v1/events?performer_id={id}&per_page=50
  - Venue resolution: redirect from gametime.co/events/{id} → URL slug contains
    date, city, state, venue name.

Scope semantics:
  next3/next5/next10 → N next future events from NOW across all venues
  all_future         → every discoverable future event

Deduplication: canonical_id = sha256(venue_slug|date|title.lower())[:16]
If a matching Event row already exists (any canonical_id collision or same
Gametime event_id in tracked_events), the existing event is used and only
missing TrackedEvent rows are added.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import Marketplace, TrackedEvent, Venue
from app.models.event import Event
from app.models.follow import UserFollow
from app.scheduler import compute_poll_interval_minutes

logger = logging.getLogger(__name__)

_GT_API   = "https://mobile.gametime.co/v1"
_GT_WEB   = "https://gametime.co"
_UA_MOBILE = "GameTime/5.0 (iPhone; iOS 16.0; Scale/3.00)"

_SCOPE_COUNTS = {
    "next3":      3,
    "next5":      5,
    "next10":    10,
    "all_future": 9999,
}


# ── Canonical ID (same logic as discovery.py) ─────────────────────────────────

def _canonical_id(title: str, venue_slug: str, event_date: datetime) -> str:
    raw = f"{venue_slug}|{event_date.date()}|{title.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Slug helpers ──────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _parse_gt_redirect_url(url: str) -> Optional[dict]:
    """
    Parse a Gametime SEO redirect URL into structured venue info.

    Example:
      .../morgan-jay-tickets/9-12-2026-los-angeles-ca-greek-theatre/events/{id}
      → date=2026-09-12, city=Los Angeles, state=CA, venue_slug=greek-theatre,
        venue_name=Greek Theatre
    """
    # Match the date-city-state-venue segment
    m = re.search(
        r"/(\d+)-(\d+)-(\d{4})-([a-z0-9-]+)-([a-z]{2})-([a-z0-9-]+)/events/",
        url,
        re.IGNORECASE,
    )
    if not m:
        return None

    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    city_slug  = m.group(4)
    state_code = m.group(5).upper()
    venue_slug = m.group(6)

    # city slug → display city
    city = " ".join(w.capitalize() for w in city_slug.split("-"))
    # venue slug → display name
    venue_name = " ".join(w.capitalize() for w in venue_slug.split("-"))

    try:
        event_date = datetime(year, month, day)
    except ValueError:
        return None

    return {
        "event_date": event_date,
        "city":       city,
        "state":      state_code,
        "venue_slug": venue_slug,
        "venue_name": venue_name,
    }


# ── HTTP client ───────────────────────────────────────────────────────────────

def _make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"Accept": "application/json", "User-Agent": _UA_MOBILE},
        follow_redirects=False,
        timeout=15.0,
    )


# ── Gametime search ───────────────────────────────────────────────────────────

async def _gt_performer_id_from_event(
    client: httpx.AsyncClient, gt_event_id: str
) -> Optional[str]:
    """
    Extract the primary performer ID from a known GT event.
    Used when we already have a GT event ID tracked in our DB.
    """
    try:
        r = await client.get(f"{_GT_API}/events/{gt_event_id}")
        r.raise_for_status()
        ev = r.json()
        performers = ev.get("performers", [])
        # Primary performer first; fall back to first entry
        for p in performers:
            if p.get("primary"):
                return p.get("id")
        if performers:
            return performers[0].get("id")
    except Exception as exc:
        logger.debug("GT performer_id lookup failed for event %s: %s", gt_event_id, exc)
    return None


async def _gt_find_performer_id(
    client: httpx.AsyncClient,
    artist: str,
    seed_gt_event_id: Optional[str] = None,
) -> Optional[str]:
    """
    Resolve a Gametime performer ID for the given artist.

    Strategy (in order):
      1. If a seed GT event ID is provided (from existing tracked_events), extract
         performer ID directly from that event — reliable, no ranking dependency.
      2. Keyword search via /v1/performers — only works for popular artists in top results.
    """
    # Strategy 1: derive from a known GT event we already track
    if seed_gt_event_id:
        perf_id = await _gt_performer_id_from_event(client, seed_gt_event_id)
        if perf_id:
            logger.debug(
                "GT performer_id for '%s' resolved from existing event %s → %s",
                artist, seed_gt_event_id, perf_id,
            )
            return perf_id

    # Strategy 2: keyword search (works for top-100 artists by sales rank)
    try:
        r = await client.get(f"{_GT_API}/performers", params={"q": artist, "per_page": 25})
        r.raise_for_status()
        performers = r.json().get("performers", [])
        artist_lower = artist.lower()
        for p in performers:
            name = (p.get("name") or "").lower()
            if name == artist_lower:
                return p.get("id")
        for p in performers:
            name = (p.get("name") or "").lower()
            if artist_lower in name or name in artist_lower:
                return p.get("id")
    except Exception as exc:
        logger.warning("GT performer keyword search failed for '%s': %s", artist, exc)

    return None


async def _gt_performer_events(
    client: httpx.AsyncClient, performer_id: str
) -> list[dict]:
    """
    Fetch all future Gametime events for a performer.
    Returns list of dicts with 'gt_id', 'datetime_local', 'venue_id'.
    """
    try:
        r = await client.get(
            f"{_GT_API}/events",
            params={"performer_id": performer_id, "per_page": 50},
        )
        r.raise_for_status()
        raw = r.json().get("events", [])
    except Exception as exc:
        logger.warning("GT performer events failed for %s: %s", performer_id, exc)
        return []

    now_str = datetime.utcnow().strftime("%Y-%m-%d")
    future = []
    for item in raw:
        ev = item.get("event", item)
        dt_local = ev.get("datetime_local", "")
        if dt_local[:10] < now_str:
            continue
        future.append({
            "gt_id":        ev.get("id"),
            "datetime_local": dt_local,
            "venue_id_gt":  ev.get("venue_id"),
        })
    return sorted(future, key=lambda x: x["datetime_local"])


async def _gt_resolve_venue(client: httpx.AsyncClient, gt_event_id: str) -> Optional[dict]:
    """
    Resolve venue info for a GT event by following the redirect from the web URL.
    Returns dict with event_date, city, state, venue_slug, venue_name or None.
    """
    try:
        r = await client.get(f"{_GT_WEB}/events/{gt_event_id}")
        location = r.headers.get("location", "")
        if location:
            return _parse_gt_redirect_url(location)
    except Exception as exc:
        logger.debug("GT venue resolve failed for %s: %s", gt_event_id, exc)
    return None


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _upsert_venue(db: AsyncSession, slug: str, name: str, city: str, state: str) -> Venue:
    """Get or create a venue row by slug."""
    existing = (await db.execute(
        select(Venue).where(Venue.slug == slug)
    )).scalar_one_or_none()
    if existing:
        return existing
    venue = Venue(slug=slug, name=name, city=city, state=state)
    db.add(venue)
    await db.flush()
    logger.info("Created new venue slug=%s name='%s' %s, %s", slug, name, city, state)
    return venue


async def _get_or_create_event(
    db: AsyncSession,
    title: str,
    artist: str,
    venue: Venue,
    event_date: datetime,
    gt_id: str,
) -> tuple[Event, bool]:
    """
    Find existing event by canonical_id OR by GT external_event_id match.
    Returns (event, is_new).
    """
    canonical = _canonical_id(title, venue.slug, event_date)

    # 1. Canonical match
    ev = (await db.execute(
        select(Event).where(Event.canonical_id == canonical)
    )).scalar_one_or_none()
    if ev:
        return ev, False

    # 2. GT external_event_id match (event already tracked under a different title variant)
    te_match = (await db.execute(
        select(TrackedEvent).where(TrackedEvent.external_event_id == gt_id)
    )).scalar_one_or_none()
    if te_match:
        ev = (await db.execute(
            select(Event).where(Event.id == te_match.event_id)
        )).scalar_one_or_none()
        if ev:
            return ev, False

    # 3. Same venue + date match (near-dup)
    nearby = (await db.execute(
        select(Event).where(
            Event.venue_id == venue.id,
            func.date(Event.event_date) == event_date.date(),
        )
    )).scalars().all()
    if nearby:
        # Return first match (same venue, same day = same event)
        return nearby[0], False

    # 4. Create new
    ev = Event(
        canonical_id=canonical,
        title=title,
        artist=artist,
        venue_id=venue.id,
        event_date=event_date,
        status="upcoming",
    )
    db.add(ev)
    await db.flush()
    logger.info("Created event id=%d '%s' at '%s' on %s", ev.id, title, venue.name, event_date.date())
    return ev, True


async def _ensure_tracked_events(
    db: AsyncSession,
    event: Event,
    gt_id: str,
    gt_marketplace: Marketplace,
    all_marketplaces: list[Marketplace],
) -> list[str]:
    """
    Ensure TrackedEvent rows exist for all active marketplaces.
    For Gametime: set external_event_id from GT ID.
    For others: create with null external_event_id (resolver fills in later).
    Returns list of newly created marketplace slugs.
    """
    existing = (await db.execute(
        select(TrackedEvent.marketplace_id).where(
            TrackedEvent.event_id == event.id
        )
    )).scalars().all()
    existing_mp_ids = set(existing)

    now = datetime.utcnow()
    interval = compute_poll_interval_minutes(
        event.event_date.replace(tzinfo=timezone.utc)
        if event.event_date.tzinfo is None
        else event.event_date
    )
    added = []

    for mp in all_marketplaces:
        if mp.id in existing_mp_ids:
            continue
        is_gt = (mp.id == gt_marketplace.id)
        db.add(TrackedEvent(
            event_id=event.id,
            marketplace_id=mp.id,
            external_event_id=gt_id if is_gt else None,
            external_url=(
                f"https://gametime.co/events/{gt_id}" if is_gt else None
            ),
            resolution_source="resolved_api" if is_gt else None,
            is_active=True,
            poll_interval_minutes=interval,
            next_poll_at=now + timedelta(minutes=interval),
            consecutive_zero_inventory_count=0,
        ))
        added.append(mp.slug)

    if added:
        await db.flush()
        logger.info(
            "Added tracked_events for event_id=%d: %s",
            event.id, added,
        )
    return added


# ── Count future tracked events for an artist ─────────────────────────────────

async def _count_future_tracked(db: AsyncSession, artist: str) -> list[Event]:
    """Return all future active tracked events matching the artist name."""
    now_naive = datetime.utcnow()
    # Use subquery to avoid async ORM join loading issues
    active_event_ids = select(TrackedEvent.event_id).where(
        TrackedEvent.is_active == True
    )
    result = await db.execute(
        select(Event)
        .where(
            and_(
                Event.id.in_(active_event_ids),
                Event.event_date > now_naive,
                Event.artist.ilike(f"%{artist}%"),
            )
        )
        .order_by(Event.event_date)
    )
    return result.scalars().all()


# ── Main acquisition function ─────────────────────────────────────────────────

async def run_follow_acquisition(session_factory=None) -> dict:
    """
    For each active follow, check if scope is satisfied.
    If not, discover and enroll missing future events via Gametime.

    Returns a summary dict per entity_key.
    """
    if session_factory is None:
        session_factory = AsyncSessionLocal

    summary: dict[str, dict] = {}

    async with session_factory() as db:
        follows = (await db.execute(
            select(UserFollow).where(UserFollow.status == "active")
        )).scalars().all()

        if not follows:
            logger.info("follow_acquisition: no active follows")
            return {}

        marketplaces = (await db.execute(
            select(Marketplace).where(Marketplace.is_active == True)
        )).scalars().all()

        gt_mp = next((m for m in marketplaces if m.slug == "gametime"), None)
        if not gt_mp:
            logger.warning("follow_acquisition: gametime marketplace not found — skipping")
            return {}

    async with _make_client() as client:
        for follow in follows:
            key = follow.entity_key
            artist = follow.display_name
            scope_count = _SCOPE_COUNTS.get(follow.scope_type, 5)

            logger.info(
                "follow_acquisition: processing follow=%d entity='%s' scope=%s (max=%d)",
                follow.id, artist, follow.scope_type, scope_count,
            )

            # ── Count existing future tracked events ──────────────────────────
            async with session_factory() as db:
                existing = await _count_future_tracked(db, artist)

            already_count = len(existing)
            needed = max(0, scope_count - already_count)

            summary[key] = {
                "entity": artist,
                "scope": follow.scope_type,
                "scope_count": scope_count,
                "already_tracked": already_count,
                "existing_event_ids": [e.id for e in existing],
                "needed": needed,
                "added": [],
                "errors": [],
            }

            if needed == 0:
                logger.info(
                    "follow_acquisition: '%s' scope satisfied (%d/%d events tracked)",
                    artist, already_count, scope_count,
                )
                continue

            # ── Gametime performer search ─────────────────────────────────────
            # Seed from an existing GT tracked event for this artist so we don't
            # depend on the keyword search (which only covers top-100 by sales).
            # Use subqueries to avoid async ORM join issues.
            async with session_factory() as db:
                artist_event_ids = select(Event.id).where(
                    Event.artist.ilike(f"%{artist}%")
                )
                gt_mp_id = (await db.execute(
                    select(Marketplace.id).where(Marketplace.slug == "gametime")
                )).scalar_one_or_none()

                seed_gt_id: Optional[str] = None
                if gt_mp_id is not None:
                    seed_gt_id = (await db.execute(
                        select(TrackedEvent.external_event_id).where(
                            and_(
                                TrackedEvent.event_id.in_(artist_event_ids),
                                TrackedEvent.marketplace_id == gt_mp_id,
                                TrackedEvent.external_event_id.isnot(None),
                            )
                        ).limit(1)
                    )).scalar_one_or_none()

            perf_id = await _gt_find_performer_id(client, artist, seed_gt_event_id=seed_gt_id)
            if not perf_id:
                msg = f"Gametime: performer '{artist}' not found"
                logger.warning("follow_acquisition: %s", msg)
                summary[key]["errors"].append(msg)
                continue

            gt_events = await _gt_performer_events(client, perf_id)
            logger.info(
                "follow_acquisition: '%s' GT performer_id=%s future_events=%d",
                artist, perf_id, len(gt_events),
            )

            if not gt_events:
                msg = "Gametime: no future events found"
                summary[key]["errors"].append(msg)
                continue

            # ── Skip already-tracked GT IDs ───────────────────────────────────
            async with session_factory() as db:
                known_gt_ids = set((await db.execute(
                    select(TrackedEvent.external_event_id).where(
                        TrackedEvent.external_event_id.in_(
                            [e["gt_id"] for e in gt_events if e["gt_id"]]
                        )
                    )
                )).scalars().all())

            new_events = [e for e in gt_events if e["gt_id"] not in known_gt_ids]
            logger.info(
                "follow_acquisition: '%s' %d GT events, %d already tracked, %d new candidates",
                artist, len(gt_events), len(gt_events) - len(new_events), len(new_events),
            )

            enrolled = 0
            for gt_ev in new_events:
                if enrolled >= needed:
                    break

                gt_id = gt_ev["gt_id"]
                if not gt_id:
                    continue

                # Resolve venue via redirect URL
                venue_info = await _gt_resolve_venue(client, gt_id)
                if not venue_info:
                    logger.debug(
                        "follow_acquisition: '%s' GT %s — could not resolve venue, skipping",
                        artist, gt_id,
                    )
                    summary[key]["errors"].append(f"venue-resolve-failed:{gt_id}")
                    continue

                event_date  = venue_info["event_date"]
                venue_slug  = venue_info["venue_slug"]
                venue_name  = venue_info["venue_name"]
                city        = venue_info["city"]
                state       = venue_info["state"]

                # Derive a clean title (strip "(21+ Event)" etc. for canonical matching)
                clean_title = re.sub(
                    r"\s*\(\d+\+\s*Event\)|\s*\(Rescheduled.*?\)", "", artist, flags=re.IGNORECASE
                ).strip() or artist

                try:
                    async with session_factory() as db:
                        # Reload marketplaces inside session
                        all_mp = (await db.execute(
                            select(Marketplace).where(Marketplace.is_active == True)
                        )).scalars().all()
                        gt_mp_inner = next((m for m in all_mp if m.slug == "gametime"), None)
                        if not gt_mp_inner:
                            break

                        venue = await _upsert_venue(db, venue_slug, venue_name, city, state)
                        event, is_new = await _get_or_create_event(
                            db, clean_title, artist, venue, event_date, gt_id
                        )
                        added_slugs = await _ensure_tracked_events(
                            db, event, gt_id, gt_mp_inner, all_mp
                        )
                        await db.commit()

                    if is_new or added_slugs:
                        enrolled += 1
                        event_summary = {
                            "event_id":    event.id,
                            "title":       clean_title,
                            "date":        str(event_date.date()),
                            "venue":       venue_name,
                            "city":        city,
                            "state":       state,
                            "is_new":      is_new,
                            "marketplaces_created": added_slugs,
                        }

                        # ── Full marketplace population pipeline ──────────────
                        # Mirrors POST /api/hydrate: resolve IDs → run all
                        # collectors → verify listings. Gametime discovery alone
                        # is NOT full ingestion.
                        try:
                            from app.services.event_population import populate_event_marketplaces
                            pop_result = await populate_event_marketplaces(
                                event_id=event.id,
                                session_factory=session_factory,
                                settings=get_settings(),
                                source="follow",
                            )
                            event_summary["population"] = {
                                "status":     pop_result.get("population_status"),
                                "marketplaces": {
                                    slug: {
                                        "status":   v["status"],
                                        "listings": v["listings"],
                                        "floor":    v["floor"],
                                        **({"reason": v["reason"]} if v.get("reason") else {}),
                                    }
                                    for slug, v in pop_result.get("marketplaces", {}).items()
                                },
                            }
                            pop_status = pop_result.get("population_status", "UNKNOWN")
                            logger.info(
                                "follow_acquisition: populated event_id=%d '%s' → %s",
                                event.id, clean_title, pop_status,
                            )
                            # ── GUARDRAIL: flag partial population explicitly ──
                            if pop_status == "PARTIAL_POPULATION":
                                logger.warning(
                                    "follow_acquisition: PARTIAL_POPULATION event_id=%d '%s' "
                                    "— only discovery source populated; "
                                    "SH/TP/VS resolution incomplete",
                                    event.id, clean_title,
                                )
                                summary[key].setdefault("warnings", []).append(
                                    f"PARTIAL_POPULATION:event_id={event.id}:{clean_title}"
                                )
                        except Exception as pop_exc:
                            logger.exception(
                                "follow_acquisition: population pipeline failed for "
                                "event_id=%d '%s': %s", event.id, clean_title, pop_exc
                            )
                            event_summary["population"] = {
                                "status": "ERROR",
                                "error": str(pop_exc),
                            }

                        summary[key]["added"].append(event_summary)
                        logger.info(
                            "follow_acquisition: enrolled event_id=%d '%s' %s %s,%s  "
                            "markets_created=%s",
                            event.id, clean_title, event_date.date(), city, state, added_slugs,
                        )
                    else:
                        logger.debug(
                            "follow_acquisition: GT %s already fully tracked, skipping",
                            gt_id,
                        )

                except Exception as exc:
                    logger.warning(
                        "follow_acquisition: error enrolling GT event %s for '%s': %s",
                        gt_id, artist, exc,
                    )
                    summary[key]["errors"].append(f"enroll-error:{gt_id}:{exc}")

            summary[key]["enrolled"] = enrolled
            summary[key]["total_after"] = already_count + enrolled

            logger.info(
                "follow_acquisition: '%s' done — added=%d total=%d",
                artist, enrolled, already_count + enrolled,
            )

    return summary
