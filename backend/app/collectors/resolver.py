"""
EventResolver — Stage 2 of the ingestion pipeline.

Runs on a schedule, finds TrackedEvents with external_event_id=NULL,
searches each marketplace using event metadata (artist, date, venue),
and persists resolved IDs so the Stage 3 collector can proceed.

Resolution strategy per marketplace:
  StubHub  — SOLR catalog search filtered by performer keywords + ±1 day date window
  SeatGeek — internal events API search by performer slug + date window
"""
import logging
import re
from datetime import timedelta
from typing import Optional, Tuple

import httpx
from sqlalchemy import select, and_, update as sa_update
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
        Find all active TrackedEvents with external_event_id=NULL and attempt
        resolution for each. Returns {resolved, failed, already_set, demo_skipped}.

        TrackedEvents whose external_event_id already starts with the demo prefix
        are counted as already_set and never sent to marketplace APIs.
        """
        counts = {"resolved": 0, "failed": 0, "already_set": 0, "demo_skipped": 0}

        async with session_factory() as db:
            rows = (await db.execute(
                select(TrackedEvent, Event, Marketplace)
                .join(Event, TrackedEvent.event_id == Event.id)
                .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
                .where(and_(
                    TrackedEvent.is_active == True,
                    TrackedEvent.external_event_id.is_(None),
                ))
            )).all()

        for te, event, mp in rows:
            if te.external_event_id:
                if str(te.external_event_id).startswith(_DEMO_ID_PREFIX):
                    counts["demo_skipped"] += 1
                    logger.debug(
                        "RESOLVER: DEMO_FIXTURE skip te_id=%d mp=%s eid=%s",
                        te.id, mp.slug, te.external_event_id,
                    )
                else:
                    counts["already_set"] += 1
                continue

            resolved, source = await self._resolve_for_marketplace(event, mp.slug, te.external_url)

            if resolved:
                await self._persist(session_factory, te.id, resolved, source)
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

        if counts["resolved"] or counts["failed"] or counts["demo_skipped"]:
            logger.info(
                "RESOLVER: cycle complete resolved=%d failed=%d already_set=%d demo_skipped=%d",
                counts["resolved"], counts["failed"], counts["already_set"], counts["demo_skipped"],
            )
        return counts

    # ── Marketplace dispatch ──────────────────────────────────────────────────

    async def _resolve_for_marketplace(
        self, event: Event, slug: str, external_url: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """Returns (resolved_id_or_None, source_label)."""
        if slug == "stubhub":
            result = await self._resolve_stubhub(event, external_url)
            return result
        if slug == "seatgeek":
            result = await self._resolve_seatgeek(event, external_url)
            return result
        logger.debug("No resolver implemented for marketplace '%s'", slug)
        return None, "none"

    # ── StubHub ───────────────────────────────────────────────────────────────

    async def _resolve_stubhub(self, event: Event, external_url: Optional[str] = None) -> Tuple[Optional[str], str]:
        keywords = _artist_keywords(event)
        if not keywords:
            return None, "none"

        date_before = (event.event_date - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        date_after = (event.event_date + timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
        kw_solr = keywords.replace(" ", "*")
        client = await self._get_client()

        # Path 1: SOLR catalog search (requires auth cookies — often fails unauthenticated)
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
                    return str(docs[0]["event_id"]), "resolved_api"
        except Exception as exc:
            logger.debug("RESOLVER: StubHub SOLR error: %s", exc)

        # Path 2: Fetch external_url page, extract event ID from embedded JSON/HTML
        if external_url:
            event_id = await self._stubhub_extract_from_page(client, external_url)
            if event_id:
                return event_id, "resolved_page_fetch"

        return None, "none"

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
    async def _persist(session_factory, tracked_event_id: int, resolved_id: str, source: str = "resolved_api") -> None:
        async with session_factory() as db:
            await db.execute(
                sa_update(TrackedEvent)
                .where(TrackedEvent.id == tracked_event_id)
                .values(external_event_id=resolved_id, resolution_source=source)
            )
            await db.commit()
