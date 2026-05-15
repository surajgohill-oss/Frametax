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
from typing import Optional

import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TrackedEvent, Event, Marketplace

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
        resolution for each. Returns {resolved, failed, already_set}.
        """
        counts = {"resolved": 0, "failed": 0, "already_set": 0}

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
                counts["already_set"] += 1
                continue

            resolved = await self._resolve_for_marketplace(event, mp.slug)

            if resolved:
                await self._persist(session_factory, te.id, resolved)
                counts["resolved"] += 1
                logger.info(
                    "Resolved %s event ID %s for '%s' (tracked_event %d)",
                    mp.slug, resolved, event.title, te.id,
                )
            else:
                counts["failed"] += 1
                logger.warning(
                    "Could not resolve %s event ID for '%s' (tracked_event %d) — "
                    "will retry next cycle",
                    mp.slug, event.title, te.id,
                )

        if counts["resolved"] or counts["failed"]:
            logger.info(
                "EventResolver cycle complete — resolved=%d failed=%d already_set=%d",
                counts["resolved"], counts["failed"], counts["already_set"],
            )
        return counts

    # ── Marketplace dispatch ──────────────────────────────────────────────────

    async def _resolve_for_marketplace(self, event: Event, slug: str) -> Optional[str]:
        if slug == "stubhub":
            return await self._resolve_stubhub(event)
        if slug == "seatgeek":
            return await self._resolve_seatgeek(event)
        logger.debug("No resolver implemented for marketplace '%s'", slug)
        return None

    # ── StubHub ───────────────────────────────────────────────────────────────

    async def _resolve_stubhub(self, event: Event) -> Optional[str]:
        keywords = _artist_keywords(event)
        if not keywords:
            return None

        date_str = event.event_date.strftime("%Y-%m-%d")
        date_before = (event.event_date - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        date_after = (event.event_date + timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
        kw_solr = keywords.replace(" ", "*")

        client = await self._get_client()
        url = (
            "https://www.stubhub.com/listingCatalog/select"
            f"?q=*:*&fq=event_name:*{kw_solr}*"
            f"&fq=event_date:[{date_before}+TO+{date_after}]"
            "&rows=5&fl=event_id,event_name,event_date_local&wt=json&sort=event_date+asc"
        )
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                docs = resp.json().get("response", {}).get("docs", [])
                if docs:
                    return str(docs[0]["event_id"])
            logger.debug(
                "StubHub SOLR returned %d for '%s' on %s",
                resp.status_code, keywords, date_str,
            )
        except Exception as exc:
            logger.debug("StubHub resolver HTTP error: %s", exc)
        return None

    # ── SeatGeek ──────────────────────────────────────────────────────────────

    async def _resolve_seatgeek(self, event: Event) -> Optional[str]:
        keywords = _artist_keywords(event)
        if not keywords:
            return None

        performer_slug = _to_performer_slug(keywords)
        date_gte = (event.event_date - timedelta(days=1)).strftime("%Y-%m-%d")
        date_lte = (event.event_date + timedelta(days=2)).strftime("%Y-%m-%d")
        client = await self._get_client()

        # Try official API if client_id configured
        if self.settings.seatgeek_client_id:
            result = await self._seatgeek_official_search(
                client, performer_slug, date_gte, date_lte
            )
            if result:
                return result

        # Fall back to internal API (no auth required)
        return await self._seatgeek_internal_search(client, keywords, date_gte, date_lte)

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
    async def _persist(session_factory, tracked_event_id: int, resolved_id: str) -> None:
        from sqlalchemy import update as sa_update
        async with session_factory() as db:
            await db.execute(
                sa_update(TrackedEvent)
                .where(TrackedEvent.id == tracked_event_id)
                .values(external_event_id=resolved_id)
            )
            await db.commit()
