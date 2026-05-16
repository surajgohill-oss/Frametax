"""
EventDiscovery — Stage 0 of the ingestion pipeline.

Runs every 6 hours. Scans StubHub and SeatGeek for concerts at known LA venues
within the admission window (14–21 days out), deduplicates against existing
events by canonical_id, and creates Event + TrackedEvent rows for new finds.

New tracked_events created here have external_event_id=NULL and
resolution_source=NULL. They enter the Stage 2 resolver on its next cycle.

Admission window:
  min_days = 14   events closer than this are either already tracked or missed
  max_days = 21   events further than this are not yet worth ingesting
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy import select

from app.models import Event, Marketplace, TrackedEvent, Venue

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Discovery admission window bounds (days before event)
_ADMISSION_MIN_DAYS = 14
_ADMISSION_MAX_DAYS = 21

# Venue keyword sets used to match marketplace venue names to local slugs.
# Each entry is (slug, set_of_substrings_any_of_which_match).
_VENUE_KEYWORDS: list[tuple[str, set[str]]] = [
    ("crypto-arena",   {"crypto.com arena", "staples center", "crypto arena"}),
    ("sofi-stadium",   {"sofi stadium", "sofi"}),
    ("hollywood-bowl", {"hollywood bowl"}),
]


def _canonical_id(title: str, venue_slug: str, event_date: datetime) -> str:
    raw = f"{venue_slug}|{event_date.date()}|{title.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _match_venue_slug(marketplace_venue_name: str) -> Optional[str]:
    """Map a marketplace venue name string to a local venue slug, or None."""
    name_lower = marketplace_venue_name.lower()
    for slug, keywords in _VENUE_KEYWORDS:
        if any(kw in name_lower for kw in keywords):
            return slug
    return None


@dataclass
class DiscoveredEvent:
    title: str
    artist: str
    venue_name: str          # as returned by marketplace
    venue_slug: str          # matched to local slug
    event_date: datetime
    external_event_id: str
    external_url: str
    marketplace_slug: str
    extra: dict = field(default_factory=dict)


class EventDiscovery:
    """
    Scans marketplaces for new LA events within the 14–21 day admission window.
    Deduplicates by canonical_id. New events enter the resolver pipeline.
    """

    def __init__(self, settings):
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
                follow_redirects=True,
                timeout=15.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Public entry point ────────────────────────────────────────────────────

    async def run_discovery(self, session_factory) -> dict:
        """
        Scan all active marketplaces. Ingest events within admission window.
        Returns counts: new / duplicate / outside_window / no_venue / failed.
        """
        counts = {"new": 0, "duplicate": 0, "outside_window": 0, "no_venue": 0, "failed": 0}

        async with session_factory() as db:
            mp_result = await db.execute(
                select(Marketplace).where(Marketplace.is_active == True)
            )
            marketplaces = mp_result.scalars().all()

            venue_result = await db.execute(select(Venue))
            venues = {v.slug: v for v in venue_result.scalars().all()}

        window_start = datetime.utcnow() + timedelta(days=_ADMISSION_MIN_DAYS)
        window_end   = datetime.utcnow() + timedelta(days=_ADMISSION_MAX_DAYS)

        logger.info(
            "DISCOVERY: scanning window %s → %s",
            window_start.date(), window_end.date(),
        )

        for mp in marketplaces:
            try:
                discovered = await self._scan_marketplace(mp.slug, window_start, window_end)
            except Exception as exc:
                logger.warning("DISCOVERY: scan failed mp=%s — %s", mp.slug, exc)
                counts["failed"] += 1
                continue

            logger.info("DISCOVERY: mp=%s found=%d candidates", mp.slug, len(discovered))

            for item in discovered:
                outcome = await self._ingest(session_factory, mp, item, venues)
                counts[outcome] += 1

        return counts

    # ── Marketplace scan dispatch ─────────────────────────────────────────────

    async def _scan_marketplace(
        self,
        slug: str,
        window_start: datetime,
        window_end: datetime,
    ) -> list[DiscoveredEvent]:
        if slug == "seatgeek":
            return await self._scan_seatgeek(window_start, window_end)
        if slug == "stubhub":
            return await self._scan_stubhub(window_start, window_end)
        logger.debug("DISCOVERY: no scanner for marketplace '%s'", slug)
        return []

    # ── SeatGeek scanner ──────────────────────────────────────────────────────

    async def _scan_seatgeek(
        self, window_start: datetime, window_end: datetime
    ) -> list[DiscoveredEvent]:
        client = await self._get_client()
        discovered: list[DiscoveredEvent] = []

        params: dict = {
            "venue.city": "Los Angeles",
            "datetime_utc.gte": window_start.strftime("%Y-%m-%d"),
            "datetime_utc.lte": window_end.strftime("%Y-%m-%d"),
            "per_page": 100,
            "type": "concert",
        }
        if self.settings.seatgeek_client_id:
            params["client_id"] = self.settings.seatgeek_client_id
            if self.settings.seatgeek_client_secret:
                params["client_secret"] = self.settings.seatgeek_client_secret
            api_url = "https://api.seatgeek.com/2/events"
        else:
            api_url = "https://seatgeek.com/api/events"

        try:
            resp = await client.get(api_url, params=params)
            if resp.status_code != 200:
                logger.warning(
                    "DISCOVERY: SeatGeek scan http=%d — DATA_GAP", resp.status_code
                )
                return []
            events = resp.json().get("events", [])
        except Exception as exc:
            logger.debug("DISCOVERY: SeatGeek scan error — %s", exc)
            return []

        for ev in events:
            try:
                venue_name = ev.get("venue", {}).get("name", "")
                venue_slug = _match_venue_slug(venue_name)
                if not venue_slug:
                    continue  # not a tracked LA venue

                title = ev.get("title", "") or ev.get("short_title", "")
                performers = ev.get("performers", [])
                artist = performers[0].get("name", title) if performers else title

                raw_date = ev.get("datetime_utc") or ev.get("datetime_local")
                if not raw_date:
                    continue
                event_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(tzinfo=None)

                external_event_id = str(ev["id"])
                slug_part = ev.get("slug", "")
                external_url = f"https://seatgeek.com/{slug_part}" if slug_part else ""

                discovered.append(DiscoveredEvent(
                    title=title,
                    artist=artist,
                    venue_name=venue_name,
                    venue_slug=venue_slug,
                    event_date=event_date,
                    external_event_id=external_event_id,
                    external_url=external_url,
                    marketplace_slug="seatgeek",
                    extra={"seatgeek_raw": {k: ev.get(k) for k in ("id", "type", "score")}},
                ))
            except Exception as exc:
                logger.debug("DISCOVERY: SeatGeek parse error — %s", exc)
                continue

        return discovered

    # ── StubHub scanner ───────────────────────────────────────────────────────

    async def _scan_stubhub(
        self, window_start: datetime, window_end: datetime
    ) -> list[DiscoveredEvent]:
        """
        StubHub SOLR requires session auth in most environments.
        Attempt the search; log DATA_GAP gracefully if it fails.
        """
        client = await self._get_client()
        discovered: list[DiscoveredEvent] = []

        date_from = window_start.strftime("%Y-%m-%dT00:00:00Z")
        date_to   = window_end.strftime("%Y-%m-%dT00:00:00Z")
        solr_url = (
            "https://www.stubhub.com/listingCatalog/select"
            f"?q=*:*&fq=city_name:Los+Angeles"
            f"&fq=event_date:[{date_from}+TO+{date_to}]"
            "&rows=100&fl=event_id,event_name,event_date_local,venue_name"
            "&wt=json&sort=event_date+asc"
        )
        try:
            resp = await client.get(solr_url)
            if resp.status_code != 200:
                logger.warning(
                    "DISCOVERY: StubHub SOLR http=%d — DATA_GAP (auth required)",
                    resp.status_code,
                )
                return []
            docs = resp.json().get("response", {}).get("docs", [])
        except Exception as exc:
            logger.debug("DISCOVERY: StubHub SOLR error — %s", exc)
            return []

        for doc in docs:
            try:
                venue_name = doc.get("venue_name", "")
                venue_slug = _match_venue_slug(venue_name)
                if not venue_slug:
                    continue

                title = doc.get("event_name", "")
                raw_date = doc.get("event_date_local", "")
                if not raw_date:
                    continue
                event_date = datetime.fromisoformat(raw_date[:19])
                external_event_id = str(doc["event_id"])
                slug_part = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                external_url = f"https://www.stubhub.com/{slug_part}-tickets"

                discovered.append(DiscoveredEvent(
                    title=title,
                    artist=title,
                    venue_name=venue_name,
                    venue_slug=venue_slug,
                    event_date=event_date,
                    external_event_id=external_event_id,
                    external_url=external_url,
                    marketplace_slug="stubhub",
                ))
            except Exception as exc:
                logger.debug("DISCOVERY: StubHub parse error — %s", exc)
                continue

        return discovered

    # ── Ingestion ─────────────────────────────────────────────────────────────

    async def _ingest(
        self,
        session_factory,
        mp: Marketplace,
        item: DiscoveredEvent,
        venues: dict[str, Venue],
    ) -> str:
        """
        Attempt to ingest one discovered event.
        Returns: 'new' | 'duplicate' | 'outside_window' | 'no_venue' | 'failed'
        """
        try:
            # Admission window re-check (race: scan happened at window_start/end)
            now = datetime.utcnow()
            days_out = (item.event_date - now).total_seconds() / 86400
            if not (_ADMISSION_MIN_DAYS <= days_out <= _ADMISSION_MAX_DAYS):
                return "outside_window"

            venue = venues.get(item.venue_slug)
            if not venue:
                logger.debug(
                    "DISCOVERY: no local venue for slug='%s' event='%s'",
                    item.venue_slug, item.title,
                )
                return "no_venue"

            canonical = _canonical_id(item.title, item.venue_slug, item.event_date)

            async with session_factory() as db:
                ev_result = await db.execute(
                    select(Event).where(Event.canonical_id == canonical)
                )
                event = ev_result.scalar_one_or_none()

                if not event:
                    event = Event(
                        canonical_id=canonical,
                        title=item.title,
                        artist=item.artist,
                        venue_id=venue.id,
                        event_date=item.event_date,
                    )
                    db.add(event)
                    await db.flush()
                    logger.info(
                        "DISCOVERY: new event='%s' venue='%s' date=%s mp=%s",
                        item.title, item.venue_slug,
                        item.event_date.date(), mp.slug,
                    )

                # Check for existing tracked_event for this marketplace
                te_result = await db.execute(
                    select(TrackedEvent).where(
                        TrackedEvent.event_id == event.id,
                        TrackedEvent.marketplace_id == mp.id,
                    )
                )
                existing_te = te_result.scalar_one_or_none()

                if existing_te:
                    await db.commit()
                    return "duplicate"

                # New tracked_event — no external_event_id yet; resolver picks it up
                db.add(TrackedEvent(
                    event_id=event.id,
                    marketplace_id=mp.id,
                    external_url=item.external_url,
                    external_event_id=None,
                    resolution_source=None,
                    is_active=True,
                    poll_interval_minutes=1440,
                    next_poll_at=now + timedelta(minutes=1440),
                ))
                await db.commit()

            logger.info(
                "DISCOVERY: ingested new tracked_event event='%s' mp=%s",
                item.title, mp.slug,
            )
            return "new"

        except Exception as exc:
            logger.warning("DISCOVERY: ingest failed event='%s' — %s", item.title, exc)
            return "failed"
