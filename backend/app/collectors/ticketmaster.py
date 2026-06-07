"""
Ticketmaster ingestion adapter.

Ticketmaster is modeled as a SINGLE marketplace_id with TWO market segments:
  primary         — face-value original inventory (offerType DEFAULT/PRESALE/…)
  verified_resale — fan resale inside TM ecosystem (offerType RESALE)

Both segments are fetched in a single Commerce API call and returned as
separate RawListing objects so _process_result stores them independently.
The segments must NEVER be merged or averaged downstream.

API surface used:
  Commerce offers: GET /commerce/v2/events/{event_id}/offers.json
  Discovery search (resolver): GET /discovery/v2/events.json
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional
import logging

import httpx

from app.collectors.base import BaseCollector, RawListing

logger = logging.getLogger("collector.ticketmaster")

_TM_COMMERCE_BASE  = "https://app.ticketmaster.com/commerce/v2"
_TM_DISCOVERY_BASE = "https://app.ticketmaster.com/discovery/v2"

# offerType values that map to primary market
_PRIMARY_OFFER_TYPES = {"DEFAULT", "PRESALE", "VENUE_PRESALE", "FAN_PRESALE", "STANDARD"}


def _to_decimal(value) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _market_segment_for(offer_type: str) -> str:
    return "primary" if offer_type.upper() in _PRIMARY_OFFER_TYPES else "verified_resale"


class TicketmasterCollector(BaseCollector):
    marketplace_slug = "ticketmaster"

    def __init__(self, settings, debug_mode: bool = False, slow_mo_ms: int = 0):
        super().__init__(settings, debug_mode=debug_mode, slow_mo_ms=slow_mo_ms)
        self._api_key: str = getattr(settings, "ticketmaster_api_key", "")
        self._http: Optional[httpx.AsyncClient] = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                headers={"Accept": "application/json"},
            )
        return self._http

    async def close(self):
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    # ── Resolver ──────────────────────────────────────────────────────────────

    async def resolve_external_event_id(self, tracked_event) -> Optional[str]:
        if tracked_event.external_event_id:
            return tracked_event.external_event_id

        if not self._api_key:
            logger.warning("TM resolver: no api_key — cannot auto-resolve")
            return None

        try:
            return await self._search_event(
                title=tracked_event.event.title if hasattr(tracked_event, "event") else "",
                event_date=tracked_event.event.event_date if hasattr(tracked_event, "event") else None,
            )
        except Exception as exc:
            logger.warning("TM resolver: search failed — %s", exc)
            return None

    # Regex patterns for resolver guards
    _PARKING_RE = re.compile(r"\bpark(?:ing)?\b", re.IGNORECASE)
    _TRIBUTE_RE = re.compile(r"\btribute\b|\bcover\b|\bcover\s+band\b", re.IGNORECASE)
    _PUNCT_RE   = re.compile(r"\W+")

    @staticmethod
    def _keyword_candidates(title: str) -> list[str]:
        """Return progressively shorter keyword variants for a title.

        TM event names often differ from our canonical titles
        (e.g. "My Chemical Romance: The Black Parade" → "My Chemical Romance with Special Guest Thrice").
        Trying just the artist/first-segment greatly increases hit rate.
        """
        import re as _re
        punct_re = _re.compile(r"\W+")
        candidates: list[str] = []
        # 1. Full cleaned title
        full = punct_re.sub(" ", title).strip()[:100]
        candidates.append(full)
        # 2. First segment before ":", "&", " vs ", " with ", " feat"
        seg = _re.split(r"[:\|]|\s+(?:&|vs\.?|with|feat\.?)\s+", title, flags=_re.IGNORECASE)[0].strip()
        short = punct_re.sub(" ", seg).strip()[:100]
        if short and short != full:
            candidates.append(short)
        # Deduplicate while preserving order
        seen: set[str] = set()
        return [c for c in candidates if c not in seen and not seen.add(c)]  # type: ignore[func-returns-value]

    async def _search_event(self, title: str, event_date: Optional[datetime]) -> Optional[str]:
        keywords_to_try = self._keyword_candidates(title)

        base_params: dict = {"apikey": self._api_key, "size": "20"}
        if event_date:
            base_params["startDateTime"] = (event_date - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
            base_params["endDateTime"]   = (event_date + timedelta(days=1)).strftime("%Y-%m-%dT23:59:59Z")

        events: list = []
        for kw in keywords_to_try:
            resp = await self._client().get(
                f"{_TM_DISCOVERY_BASE}/events.json",
                params={**base_params, "keyword": kw},
            )
            resp.raise_for_status()
            data = resp.json()
            events = (data.get("_embedded") or {}).get("events") or []
            if events:
                logger.debug("TM resolver: keyword='%s' returned %d result(s) for '%s'", kw, len(events), title)
                break
            logger.debug("TM resolver: keyword='%s' returned 0 results — trying next variant", kw)

        if not events:
            logger.info("TM resolver: no results for '%s' (tried %d keyword variant(s))", title, len(keywords_to_try))
            return None

        # Fix 1: skip parking catalog events that may sort ahead of the concert.
        # Check (a) event name contains "park(ing)" and (b) the event's own
        # classifications list has type.name == "Parking".
        # NOTE: event.products[] are upsell attachments on the concert (e.g. ParkWhiz
        # lots linked to a show) — those must NOT be used to filter the event itself.
        for event in events:
            name = event.get("name") or ""
            if self._PARKING_RE.search(name):
                logger.debug("TM resolver: skipping parking-named event '%s'", name)
                continue
            if self._TRIBUTE_RE.search(name):
                logger.debug("TM resolver: skipping tribute/cover event '%s'", name)
                continue
            own_classifs = event.get("classifications") or []
            is_parking_event = any(
                (c.get("type") or {}).get("name") == "Parking"
                for c in own_classifs
            )
            if is_parking_event:
                logger.debug("TM resolver: skipping parking-classified event '%s'", name)
                continue
            tm_id = event.get("id")
            logger.info("TM resolver: matched '%s' → TM event_id=%s name='%s'", title, tm_id, name)
            return tm_id

        logger.info("TM resolver: no non-parking results for '%s'", title)
        return None

    # ── Listings fetch ────────────────────────────────────────────────────────

    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        event_id = tracked_event.external_event_id
        if not event_id:
            return []

        if not self._api_key:
            logger.warning("TM collector: no api_key — cannot fetch listings for event %s", event_id)
            return []

        listings: list[RawListing] = []

        try:
            offers = await self._fetch_offers(event_id)
            listings.extend(offers)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                logger.warning("TM collector: API auth failure (check TICKETMASTER_API_KEY)")
            elif exc.response.status_code == 404:
                logger.info("TM collector: event %s not found in Commerce API", event_id)
            else:
                logger.warning("TM collector: HTTP %s for event %s", exc.response.status_code, event_id)
        except Exception as exc:
            logger.warning("TM collector: offers fetch failed — %s", exc)

        logger.info(
            "TM collector: event=%s total=%d primary=%d resale=%d",
            event_id,
            len(listings),
            sum(1 for l in listings if l.market_segment == "primary"),
            sum(1 for l in listings if l.market_segment == "verified_resale"),
        )
        return listings

    async def _fetch_offers(self, event_id: str) -> list[RawListing]:
        resp = await self._client().get(
            f"{_TM_COMMERCE_BASE}/events/{event_id}/offers.json",
            params={"apikey": self._api_key},
        )
        resp.raise_for_status()
        data = resp.json()
        return self._parse_offers(event_id, data)

    def _parse_offers(self, event_id: str, data: dict) -> list[RawListing]:
        raw_offers = (data.get("_embedded") or {}).get("offer") or []
        listings: list[RawListing] = []

        for offer in raw_offers:
            offer_id    = offer.get("offerId") or offer.get("id") or ""
            offer_type  = offer.get("offerType") or "DEFAULT"
            offer_name  = offer.get("name") or "General Admission"
            segment     = _market_segment_for(offer_type)
            inventory   = offer.get("inventory") or {}
            available   = inventory.get("available", True)
            qty         = int(inventory.get("quantity") or 1)

            if not available:
                continue

            price_levels = offer.get("priceLevels") or offer.get("prices") or []
            if not price_levels:
                # Offer with no price — skip
                continue

            for idx, pl in enumerate(price_levels):
                face_val  = _to_decimal(pl.get("value") or pl.get("faceValue"))
                total_val = _to_decimal(pl.get("totalValue") or pl.get("allInPrice"))

                if face_val is None:
                    continue

                fees      = (total_val - face_val) if total_val is not None else None
                section   = offer_name
                ext_id    = f"tm-{segment[:3]}-{offer_id}-{idx}"

                listings.append(RawListing(
                    external_listing_id=ext_id,
                    section=section,
                    row=None,
                    quantity=qty,
                    price=face_val,
                    fees=fees if fees and fees > 0 else None,
                    all_in_price=total_val,
                    market_segment=segment,
                    listing_url=f"https://www.ticketmaster.com/event/{event_id}",
                ))

        return listings

    # ── Section normalisation ─────────────────────────────────────────────────

    def normalize_section(self, raw_section: str) -> str:
        if not raw_section:
            return ""
        s = re.sub(r"(?i)^(section|sec\.?)\s*", "", raw_section.strip())
        return s.upper()
