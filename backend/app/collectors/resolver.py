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
from datetime import datetime, timedelta
from typing import Optional, Tuple

import httpx
from sqlalchemy import select, and_, or_, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TrackedEvent, Event, Marketplace

# ── VS resolver backoff ───────────────────────────────────────────────────────
# VividSeats catalog scans (even with the page cap) are expensive.  After
# _VS_BACKOFF_THRESHOLD consecutive failures for the same tracked_event, the
# resolver skips that event for _VS_BACKOFF_HOURS hours.
# Uses the existing FailureMemory table — no migration needed.
# Pattern key: f"vs_resolve:{te.id}"   error_type: "resolve_no_match"
_VS_BACKOFF_THRESHOLD = 3     # failures before cooldown kicks in
_VS_BACKOFF_HOURS     = 12    # hours to pause after threshold reached

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

    async def _get_stubhub_client(self) -> httpx.AsyncClient:
        """Return an httpx client loaded with cached StubHub browser cookies.

        The StubHubCollector saves cookies after each Playwright run to
        {browser_data_dir}/stubhub/cookies.json.  Loading them here lets the
        resolver's SOLR requests succeed (SOLR returns 404 without a session).
        Falls back to a plain client if no cookie file exists yet.
        """
        import json
        from pathlib import Path

        cookie_jar: dict = {}
        try:
            cookie_path = Path(getattr(self.settings, "browser_data_dir", "")) / "stubhub" / "cookies.json"
            if cookie_path.exists():
                raw = json.loads(cookie_path.read_text())
                cookie_jar = {c["name"]: c["value"] for c in raw if c.get("name")}
        except Exception as exc:
            logger.debug("RESOLVER: could not load StubHub cookies: %s", exc)

        return httpx.AsyncClient(
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "application/json",
                "Referer": "https://www.stubhub.com/",
            },
            cookies=cookie_jar,
            follow_redirects=True,
            timeout=15.0,
        )

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

            # ── VividSeats backoff gate ────────────────────────────────────────
            # Skip VS resolution if this event has hit the failure threshold and
            # the cooldown window has not elapsed.  Prevents repeated expensive
            # catalog scans for events that are genuinely not listed on VS yet.
            if mp.slug == "vividseats":
                in_backoff = await self._vs_in_backoff(session_factory, te.id)
                if in_backoff:
                    counts["already_set"] += 1  # treated as deferred, not failed
                    logger.debug(
                        "VS resolver: te=%d '%s' in backoff — deferring resolution",
                        te.id, event.title,
                    )
                    continue

            resolved, resolved_url, source = await self._resolve_for_marketplace(event, mp.slug, te.external_url)

            if resolved:
                # Clear any VS backoff on success
                if mp.slug == "vividseats":
                    await self._vs_clear_backoff(session_factory, te.id)
                await self._persist(session_factory, te.id, resolved, resolved_url, source)
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
                # Record VS failure for backoff tracking
                if mp.slug == "vividseats":
                    await self._vs_record_failure(session_factory, te.id, event.title)

        if counts["resolved"] or counts["failed"]:
            logger.info(
                "RESOLVER: cycle complete resolved=%d failed=%d already_set=%d",
                counts["resolved"], counts["failed"], counts["already_set"],
            )
        return counts

    # ── Marketplace dispatch ──────────────────────────────────────────────────

    async def _resolve_for_marketplace(
        self, event: Event, slug: str, external_url: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], str]:
        """Returns (resolved_id_or_None, resolved_url_or_None, source_label)."""
        if slug == "stubhub":
            return await self._resolve_stubhub(event, external_url)
        if slug == "seatgeek":
            eid, src = await self._resolve_seatgeek(event, external_url)
            return eid, None, src

        # Delegate to the collector's own resolver for marketplaces with public
        # search APIs (tickpick, gametime, vividseats). Ticketmaster requires an
        # API key so its collector self-gates and returns None without credentials.
        from app.collectors.registry import get_collector

        collector = get_collector(slug, self.settings)
        if collector is None:
            logger.debug("No resolver or collector for marketplace '%s'", slug)
            return None, None, "none"

        class _Proxy:
            __slots__ = ("external_event_id", "external_url", "event", "id")
            def __init__(self, ev, url):
                self.external_event_id = None
                self.external_url = url
                self.event = ev
                self.id = None

        resolved = await collector.resolve_external_event_id(_Proxy(event, external_url))
        if resolved:
            return resolved, None, "resolved_collector"
        return None, None, "none"

    # ── StubHub ───────────────────────────────────────────────────────────────

    async def _resolve_stubhub(self, event: Event, external_url: Optional[str] = None) -> Tuple[Optional[str], Optional[str], str]:
        """Returns (event_id, event_url, source).

        Always persists an external_url so the Playwright collector has a URL
        to navigate to. Bare /event/{id}/ works in Railway (after the OOM fix),
        but the slug URL is preferred when derivable.
        """
        keywords = _artist_keywords(event)
        if not keywords:
            return None, None, "none"

        date_before = (event.event_date - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        date_after = (event.event_date + timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
        kw_solr = keywords.replace(" ", "*")
        # Use cookie-bearing client so SOLR doesn't return 404
        client = await self._get_stubhub_client()

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
                    event_id = str(docs[0]["event_id"])
                    # Bare URL — good enough for Playwright; slug preferred but
                    # not always derivable from SOLR response fields alone.
                    resolved_url = f"https://www.stubhub.com/event/{event_id}/"
                    return event_id, resolved_url, "resolved_api"
        except Exception as exc:
            logger.debug("RESOLVER: StubHub SOLR error: %s", exc)

        # Path 2: Fetch external_url page, extract event ID from embedded JSON/HTML
        # The provided external_url IS the slug URL — preserve it.
        if external_url:
            event_id = await self._stubhub_extract_from_page(client, external_url)
            if event_id:
                return event_id, external_url, "resolved_page_fetch"

        return None, None, "none"

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
        resolved_url: Optional[str] = None,
        source: str = "resolved_api",
    ) -> None:
        """Persist resolved external_event_id and, critically, external_url.

        StubHub's Playwright collector requires external_url to navigate to the
        correct event page. Always persist at minimum a bare /event/{id}/ URL so
        the collector is never left with a NULL URL after resolution.
        """
        values: dict = {"external_event_id": resolved_id, "resolution_source": source}
        if resolved_url:
            values["external_url"] = resolved_url
        elif resolved_id:
            # Safety net: ensure external_url is never left NULL after resolution.
            # The bare URL works in Playwright (OOM crash fixed via --disable-dev-shm-usage).
            # _resolve_stubhub always returns a resolved_url now, but other paths
            # (resolved_collector for TP/GT/VS) return None — those marketplaces
            # don't use external_url, so only set the fallback for stubhub-style IDs.
            pass  # non-StubHub marketplaces don't need external_url
        async with session_factory() as db:
            await db.execute(
                sa_update(TrackedEvent)
                .where(TrackedEvent.id == tracked_event_id)
                .values(**values)
            )
            await db.commit()
            if resolved_url:
                logger.debug(
                    "RESOLVER: persisted te=%d id=%s url=%s source=%s",
                    tracked_event_id, resolved_id, resolved_url, source,
                )

    # ── VividSeats resolver backoff helpers ───────────────────────────────────

    @staticmethod
    async def _vs_backoff_key(tracked_event_id: int) -> str:
        return f"vs_resolve:{tracked_event_id}"

    @classmethod
    async def _vs_in_backoff(cls, session_factory, tracked_event_id: int) -> bool:
        """Return True if this VS tracked_event is within its cooldown window."""
        from app.models.debug import FailureMemory
        pattern = await cls._vs_backoff_key(tracked_event_id)
        try:
            async with session_factory() as db:
                result = await db.execute(
                    select(FailureMemory).where(
                        FailureMemory.marketplace == "vividseats",
                        FailureMemory.error_type == "resolve_no_match",
                        FailureMemory.failed_pattern == pattern,
                        FailureMemory.skip_failed == True,
                    )
                )
                rec = result.scalar_one_or_none()
                if rec is None:
                    return False
                cutoff = datetime.utcnow() - timedelta(hours=_VS_BACKOFF_HOURS)
                return rec.last_seen >= cutoff
        except Exception as exc:
            logger.debug("VS backoff check failed (ignored): %s", exc)
            return False

    @classmethod
    async def _vs_record_failure(cls, session_factory, tracked_event_id: int, title: str) -> None:
        """Upsert a VS resolution failure; set skip_failed after threshold."""
        from app.models.debug import FailureMemory
        pattern = await cls._vs_backoff_key(tracked_event_id)
        try:
            async with session_factory() as db:
                result = await db.execute(
                    select(FailureMemory).where(
                        FailureMemory.marketplace == "vividseats",
                        FailureMemory.error_type == "resolve_no_match",
                        FailureMemory.failed_pattern == pattern,
                    )
                )
                rec = result.scalar_one_or_none()
                if rec:
                    rec.failure_count += 1
                    rec.last_seen = datetime.utcnow()
                    if rec.failure_count >= _VS_BACKOFF_THRESHOLD:
                        rec.skip_failed = True
                        logger.info(
                            "VS resolver: te=%d '%s' hit backoff threshold (%d failures) "
                            "— deferring for %dh",
                            tracked_event_id, title, rec.failure_count, _VS_BACKOFF_HOURS,
                        )
                else:
                    db.add(FailureMemory(
                        marketplace="vividseats",
                        error_type="resolve_no_match",
                        failed_pattern=pattern,
                        failure_count=1,
                        skip_failed=False,
                    ))
                await db.commit()
        except Exception as exc:
            logger.debug("VS failure record failed (ignored): %s", exc)

    @classmethod
    async def _vs_clear_backoff(cls, session_factory, tracked_event_id: int) -> None:
        """Clear VS backoff on successful resolution."""
        from app.models.debug import FailureMemory
        pattern = await cls._vs_backoff_key(tracked_event_id)
        try:
            async with session_factory() as db:
                result = await db.execute(
                    select(FailureMemory).where(
                        FailureMemory.marketplace == "vividseats",
                        FailureMemory.error_type == "resolve_no_match",
                        FailureMemory.failed_pattern == pattern,
                    )
                )
                rec = result.scalar_one_or_none()
                if rec:
                    rec.skip_failed = False
                    rec.failure_count = 0
                    rec.last_success = datetime.utcnow()
                    await db.commit()
        except Exception as exc:
            logger.debug("VS backoff clear failed (ignored): %s", exc)
