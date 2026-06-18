"""
EventResolver — Stage 2 of the ingestion pipeline.

Runs on a schedule, finds TrackedEvents with external_event_id=NULL,
searches each marketplace using event metadata (artist, date, venue),
and persists resolved IDs so the Stage 3 collector can proceed.

Resolution strategy per marketplace:
  StubHub       — SOLR catalog search or page extraction
  SeatGeek      — official API (with client_id) or internal search API
  TickPick      — public search API, no credentials required
  GameTime      — public mobile search API, no credentials required
  VividSeats    — Hermes search API, no credentials required
  Ticketmaster  — Discovery API (requires TICKETMASTER_API_KEY)

  For TickPick/GameTime/VividSeats/Ticketmaster the resolver delegates to each
  collector's own resolve_external_event_id() via a lightweight proxy object so
  resolution logic is not duplicated.

  Demo-prefixed IDs ("demo-*") are treated as unresolved placeholders and will
  be replaced with real marketplace IDs on the first successful resolution cycle.
"""
import logging
import re
from datetime import timedelta
from typing import Optional, Tuple

import httpx
from sqlalchemy import select, and_, or_, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TrackedEvent, Event, Marketplace

_DEMO_ID_PREFIX = "demo-"

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _artist_keywords(event: Event) -> str:
    """Extract searchable artist name from event, stripping tour suffixes."""
    name = event.artist or event.title or ""
    name = re.split(r"\s*[|–—]\s*", name)[0].strip()
    return name


def _to_performer_slug(name: str) -> str:
    """'Dave Matthews Band' → 'dave-matthews-band'"""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class EventResolver:
    """
    Resolves external marketplace event IDs from event metadata.
    Intended to run as a scheduled background job, not inline with polling.
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

    async def resolve_all_pending(self, session_factory) -> dict:
        """
        Find all active TrackedEvents with external_event_id=NULL or a demo-prefixed
        placeholder and attempt resolution for each.
        Returns {resolved, failed, already_set}.
        """
        counts = {"resolved": 0, "failed": 0, "already_set": 0}

        async with session_factory() as db:
            rows = (await db.execute(
                select(TrackedEvent, Event, Marketplace)
                .join(Event, TrackedEvent.event_id == Event.id)
                .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
                .where(and_(
                    TrackedEvent.is_active == True,
                    or_(
                        TrackedEvent.external_event_id.is_(None),
                        TrackedEvent.external_event_id.like(f"{_DEMO_ID_PREFIX}%"),
                    ),
                ))
            )).all()

        for te, event, mp in rows:
            if te.external_event_id and not str(te.external_event_id).startswith(_DEMO_ID_PREFIX):
                counts["already_set"] += 1
                continue
            # NULL and demo-prefixed IDs both fall through to resolution

            resolved, source, resolved_url = await self._resolve_for_marketplace(event, mp.slug, te.external_url)

            if resolved:
                await self._persist(session_factory, te.id, resolved, source, resolved_url)
                counts["resolved"] += 1
                logger.info(
                    "RESOLVER: resolved %s event_id=%s event='%s' tracked_event=%d source=%s",
                    mp.slug, resolved, event.title, te.id, source,
                )
            else:
                counts["failed"] += 1
                logger.warning(
                    "RESOLVER: DATA_GAP — could not resolve %s event_id for '%s' "
                    "(tracked_event=%d) — will retry next cycle",
                    mp.slug, event.title, te.id,
                )

        if counts["resolved"] or counts["failed"]:
            logger.info(
                "RESOLVER: cycle complete resolved=%d failed=%d already_set=%d",
                counts["resolved"], counts["failed"], counts["already_set"],
            )
        return counts

    # ── Marketplace dispatch ──────────────────────────────────────────────────

    async def _resolve_for_marketplace(
        self, event: Event, slug: str, external_url: Optional[str] = None
    ) -> Tuple[Optional[str], str, Optional[str]]:
        """Returns (resolved_id_or_None, source_label, resolved_event_url_or_None)."""
        if slug == "stubhub":
            return await self._resolve_stubhub(event, external_url)
        if slug == "seatgeek":
            id_, src = await self._resolve_seatgeek(event, external_url)
            return id_, src, None

        # Delegate to the collector's own resolver for marketplaces with public
        # search APIs (tickpick, gametime, vividseats). Ticketmaster requires an
        # API key so its collector self-gates and returns None without credentials.
        from app.collectors.registry import get_collector

        collector = get_collector(slug, self.settings)
        if collector is None:
            logger.debug("No resolver or collector for marketplace '%s'", slug)
            return None, "none", None

        class _Proxy:
            __slots__ = ("external_event_id", "external_url", "event", "id")
            def __init__(self, ev, url):
                self.external_event_id = None
                self.external_url = url
                self.event = ev
                self.id = None

        resolved = await collector.resolve_external_event_id(_Proxy(event, external_url))
        if resolved:
            return resolved, "resolved_collector", None
        return None, "none", None

    # ── StubHub ───────────────────────────────────────────────────────────────

    async def _resolve_stubhub(self, event: Event, external_url: Optional[str] = None) -> Tuple[Optional[str], str, Optional[str]]:
        keywords = _artist_keywords(event)
        if not keywords:
            return None, "none", None

        client = await self._get_client()

        # Path 1: SOLR catalog search (legacy — was the primary path; now returns 404.
        # Kept for forward-compatibility in case endpoint is restored.)
        date_before = (event.event_date - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        date_after  = (event.event_date + timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
        kw_solr = keywords.replace(" ", "*")
        solr_url = (
            "https://www.stubhub.com/listingCatalog/select"
            f"?q=*:*&fq=event_name:*{kw_solr}*"
            f"&fq=event_date:[{date_before}+TO+{date_after}]"
            "&rows=5&fl=event_id,event_name,event_date_local&wt=json&sort=event_date+asc"
        )
        try:
            resp = await client.get(solr_url)
            if resp.status_code == 200:
                docs = resp.json().get("response", {}).get("docs", [])
                if docs:
                    return str(docs[0]["event_id"]), "resolved_api", None
        except Exception as exc:
            logger.debug("RESOLVER: StubHub SOLR error: %s", exc)

        # Path 2: StubHub search-page HTML extraction — primary unauthenticated path.
        # The search results page at /search?q=<artist>&category=Concerts embeds event
        # URLs with date slugs (e.g. /kid-cudi-los-angeles-tickets-6-26-2026/event/160354751/)
        # in its HTML body. No auth or cookies required. Parse and match by event date.
        search_result = await self._stubhub_search_page(client, keywords, event.event_date)
        if search_result:
            event_id_str, event_url = search_result
            logger.info(
                "RESOLVER: StubHub search-page matched '%s' %s → event_id=%s url=%s",
                keywords, event.event_date.date(), event_id_str, event_url,
            )
            return event_id_str, "resolved_search", event_url

        # Path 3: Direct event URL page extraction (used when user supplies an event URL
        # via POST /api/events/{id}/marketplace-url, or for URLs from archive imports).
        # Skip performer pages — they return 202 bot challenge and the only ID embedded
        # is the performer_id, which would be misidentified as an event_id.
        if external_url and "/performer/" not in external_url:
            event_id = await self._stubhub_extract_from_page(client, external_url)
            if event_id:
                return event_id, "resolved_page_fetch", None

        if external_url and "/performer/" in external_url:
            logger.debug(
                "RESOLVER: StubHub performer page %s — search-page path also failed; "
                "event not in StubHub catalog or not yet listed",
                external_url,
            )

        return None, "none", None

    async def _stubhub_search_page(
        self,
        client: httpx.AsyncClient,
        artist_name: str,
        event_date,
    ) -> Optional[tuple]:
        """
        Fetch StubHub search results page and extract a matching event ID by date.

        StubHub search embeds event URLs in the format:
            /artist-city-tickets-M-D-YYYY/event/{event_id}/
        These are visible in the HTML without auth. Returns (event_id, event_url) or None.
        """
        import urllib.parse as _urlparse
        import json as _json

        query = _urlparse.quote_plus(artist_name)
        url = f"https://www.stubhub.com/search?q={query}&category=Concerts"

        try:
            resp = await client.get(url, timeout=15)
            if resp.status_code != 200:
                logger.debug("RESOLVER: StubHub search page HTTP %s for '%s'", resp.status_code, artist_name)
                return None
        except Exception as exc:
            logger.debug("RESOLVER: StubHub search page fetch error: %s", exc)
            return None

        text = resp.text
        # Event URLs are embedded as: /some-slug-tickets-M-D-YYYY/event/{id}/
        pattern = re.compile(
            r'(?:href=)?["\']?(/[^"\']+/event/(\d{8,9})/)["\']?'
        )
        # Also capture the date from the slug
        date_slug_re = re.compile(r'tickets-(\d{1,2})-(\d{1,2})-(\d{4})/event/\d{8,9}')

        candidates: list[tuple[int, str, str]] = []  # (delta_days, event_id, full_url)

        seen_ids: set[str] = set()
        for m in re.finditer(r'/event/(\d{8,9})/', text):
            eid = m.group(1)
            if eid in seen_ids:
                continue
            seen_ids.add(eid)

            # Find the URL slug for this event_id in the surrounding text
            idx = m.start()
            chunk = text[max(0, idx - 200): idx + 50]
            slug_m = date_slug_re.search(chunk)
            if not slug_m:
                continue

            try:
                mo, dy, yr = int(slug_m.group(1)), int(slug_m.group(2)), int(slug_m.group(3))
                from datetime import date as _date
                page_date = _date(yr, mo, dy)
                delta = abs((page_date - event_date.date()).days)
                if delta <= 1:
                    # Reconstruct the partial URL
                    slug_start = chunk.rfind("/", 0, slug_m.start()) + 1 if "/" in chunk[:slug_m.start()] else 0
                    event_path = f"https://www.stubhub.com{text[text.rfind('/', 0, m.start()):m.end()]}"
                    candidates.append((delta, eid, event_path))
            except (ValueError, TypeError):
                continue

        if not candidates:
            logger.debug("RESOLVER: StubHub search-page: no date match for '%s' on %s", artist_name, event_date.date())
            return None

        candidates.sort(key=lambda x: x[0])
        best_delta, best_id, best_url = candidates[0]
        return best_id, best_url

    async def _stubhub_extract_from_page(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Fetch StubHub page and extract event ID from embedded script data."""
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            html = resp.text
            # StubHub embeds event data in several patterns
            for pattern in (
                r'"eventId"\s*:\s*"?(\d+)"?',
                r'"id"\s*:\s*(\d{7,})',          # long numeric ID in JSON blob
                r'/event/(\d+)',                   # event URL reference in page
                r'event_id["\s:]+(\d{6,})',
            ):
                m = re.search(pattern, html)
                if m:
                    logger.debug("RESOLVER: StubHub page extraction matched pattern '%s'", pattern)
                    return m.group(1)
        except Exception as exc:
            logger.debug("RESOLVER: StubHub page fetch failed: %s", exc)
        return None

    # ── SeatGeek ──────────────────────────────────────────────────────────────

    async def _resolve_seatgeek(self, event: Event, external_url: Optional[str] = None) -> Tuple[Optional[str], str]:
        keywords = _artist_keywords(event)
        if not keywords:
            return None, "none"

        performer_slug = _to_performer_slug(keywords)
        date_gte = (event.event_date - timedelta(days=1)).strftime("%Y-%m-%d")
        date_lte = (event.event_date + timedelta(days=2)).strftime("%Y-%m-%d")
        client = await self._get_client()

        # Path 1: Official API (requires client_id)
        if self.settings.seatgeek_client_id:
            result = await self._seatgeek_official_search(client, performer_slug, date_gte, date_lte)
            if result:
                return result, "resolved_api"

        # Path 2: Internal API (unauthenticated)
        result = await self._seatgeek_internal_search(client, keywords, date_gte, date_lte)
        if result:
            return result, "resolved_api"

        # Path 3: Fetch external_url page, extract event ID from __NEXT_DATA__
        if external_url:
            page_result = await self._seatgeek_extract_from_page(client, external_url)
            if page_result:
                return page_result, "resolved_page_fetch"

        return None, "none"

    async def _seatgeek_extract_from_page(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Fetch SeatGeek page and extract event ID from __NEXT_DATA__ or HTML patterns."""
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            html = resp.text
            # Path 3a: __NEXT_DATA__ JSON (most reliable)
            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            if m:
                try:
                    page_data = __import__("json").loads(m.group(1))
                    # Walk known paths to event id
                    for path in (
                        ["props", "pageProps", "event", "id"],
                        ["props", "pageProps", "initialData", "event", "id"],
                        ["props", "pageProps", "eventId"],
                    ):
                        node = page_data
                        try:
                            for key in path:
                                node = node[key]
                            if isinstance(node, int):
                                return str(node)
                        except (KeyError, TypeError):
                            continue
                except Exception:
                    pass
            # Path 3b: raw HTML patterns
            for pattern in (r'"id"\s*:\s*(\d{6,})', r'/events?/[^/]+-(\d{5,})'):
                m = re.search(pattern, html)
                if m:
                    return m.group(1)
        except Exception as exc:
            logger.debug("RESOLVER: SeatGeek page fetch failed: %s", exc)
        return None

    async def _seatgeek_official_search(
        self, client: httpx.AsyncClient,
        performer_slug: str, date_gte: str, date_lte: str,
    ) -> Optional[str]:
        try:
            params = {
                "performers.slug": performer_slug,
                "datetime_utc.gte": date_gte,
                "datetime_utc.lte": date_lte,
                "per_page": 5,
                "client_id": self.settings.seatgeek_client_id,
            }
            if self.settings.seatgeek_client_secret:
                params["client_secret"] = self.settings.seatgeek_client_secret
            resp = await client.get("https://api.seatgeek.com/2/events", params=params)
            if resp.status_code == 200:
                events = resp.json().get("events", [])
                if events:
                    return str(events[0]["id"])
        except Exception as exc:
            logger.debug("SeatGeek official API resolver error: %s", exc)
        return None

    async def _seatgeek_internal_search(
        self, client: httpx.AsyncClient,
        keywords: str, date_gte: str, date_lte: str,
    ) -> Optional[str]:
        try:
            resp = await client.get(
                "https://seatgeek.com/api/events",
                params={
                    "q": keywords,
                    "datetime_utc.gte": date_gte,
                    "datetime_utc.lte": date_lte,
                    "per_page": 5,
                },
            )
            if resp.status_code == 200:
                events = resp.json().get("events", [])
                if events:
                    return str(events[0]["id"])
        except Exception as exc:
            logger.debug("SeatGeek internal API resolver error: %s", exc)
        return None

    # ── Persistence ───────────────────────────────────────────────────────────

    @staticmethod
    async def _persist(
        session_factory,
        tracked_event_id: int,
        resolved_id: str,
        source: str = "resolved_api",
        external_url: Optional[str] = None,
    ) -> None:
        values = {"external_event_id": resolved_id, "resolution_source": source}
        if external_url:
            values["external_url"] = external_url
        async with session_factory() as db:
            await db.execute(
                sa_update(TrackedEvent)
                .where(TrackedEvent.id == tracked_event_id)
                .values(**values)
            )
            await db.commit()
