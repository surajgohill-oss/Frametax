"""
Vivid Seats ingestion adapter.

Vivid Seats is a broker-heavy secondary resale marketplace.
market_segment is always "secondary_resale".

Market model note:
  Vivid Seats aggregates listings from professional brokers and resellers.
  It carries no primary inventory. Prices tend to include broker markup.
  Do not treat as face-value baseline.

API surface:
  Listings: GET https://www.vividseats.com/hermes/api/v1/listings
              ?productionId={event_id}&qty=1
  Event search: GET https://www.vividseats.com/hermes/api/v1/productions
              ?startDate=YYYY-MM-DD&pageSize=25&pageNumber=N
              (Note: /productions/search requires auth; not used here)

Pricing note:
  Vivid Seats returns prices in dollars (float).
  Ticket fields:
    p   = base price per ticket (before service charges)
    aip = all-in price per ticket (base + all fees, checkout-equivalent)
  showAip=true / defaultAipOn=true on all observed events.
  Stored as: price=p, all_in_price=aip.

Bot protection:
  Standard browser UA triggers PerimeterX challenge page.
  iOS mobile UA bypasses it and receives JSON directly.

Parking:
  parkingPid on the production record is a SEPARATE production.
  Parking tickets are NOT included in the main event's listings response.
  Confirmed: 0 parking tickets observed in listings for all pilot events.
  Scheduler parking choke-point still applied as safety net.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from typing import Optional
import logging

import httpx

from app.collectors.base import BaseCollector, RawListing
from app.collectors.normalize import is_parking_listing as _is_parking_listing

logger = logging.getLogger("collector.vividseats")

_VS_API_BASE = "https://www.vividseats.com/hermes/api/v1"
_SEGMENT     = "secondary_resale"


def _to_decimal(value) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(float(value)))
    except (InvalidOperation, ValueError, TypeError):
        return None


class VividSeatsCollector(BaseCollector):
    marketplace_slug = "vividseats"

    def __init__(self, settings, debug_mode: bool = False, slow_mo_ms: int = 0):
        super().__init__(settings, debug_mode=debug_mode, slow_mo_ms=slow_mo_ms)
        self._api_key: str = getattr(settings, "vividseats_api_key", "")
        self._http: Optional[httpx.AsyncClient] = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            headers = {
                "Accept":     "application/json",
                # iOS mobile UA required — standard browser UA triggers PerimeterX
                # challenge-validation page and returns HTML instead of JSON.
                "User-Agent": "VividSeats-iOS/8.0 (iPhone; iOS 16.0; Scale/3.00)",
            }
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                headers=headers,
            )
        return self._http

    async def close(self):
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    # ── Resolver ──────────────────────────────────────────────────────────────

    async def resolve_external_event_id(self, tracked_event) -> Optional[str]:
        if tracked_event.external_event_id:
            return tracked_event.external_event_id

        # Fast path: if external_url already contains a VividSeats production ID,
        # extract it directly — avoids the catalog scan entirely.
        # Handles URLs like: https://www.vividseats.com/...production-6118266
        #                    https://www.vividseats.com/production/6118266
        ext_url = getattr(tracked_event, "external_url", None) or ""
        if ext_url:
            import re as _re
            _m = _re.search(r"production[/-](\d+)", ext_url, _re.IGNORECASE)
            if _m:
                pid = _m.group(1)
                logger.info(
                    "VS resolver: extracted production_id=%s from external_url for '%s'",
                    pid,
                    getattr(tracked_event, "event", {}).title if hasattr(getattr(tracked_event, "event", None), "title") else "?",
                )
                return pid

        try:
            title = tracked_event.event.title if hasattr(tracked_event, "event") else ""
            event_date = tracked_event.event.event_date if hasattr(tracked_event, "event") else None
            return await self._search_event(title, event_date)
        except Exception as exc:
            logger.warning("VS resolver: search failed — %s", exc)
            return None

    async def _search_event(self, title: str, event_date: Optional[datetime]) -> Optional[str]:
        """
        Search via /productions?query=<title> then filter by date.

        The date-scan approach (?startDate=...&endDate=...) only returns
        popular/featured productions and misses most concerts. The query= param
        returns ALL productions matching the artist/event name and is reliable.
        """
        if not title:
            return None

        date_str = event_date.strftime("%Y-%m-%d") if event_date else None

        import re as _re
        title_lower = title.lower()
        kw_set = {w for w in _re.split(r'\W+', title_lower) if len(w) > 2}

        try:
            resp = await self._client().get(
                f"{_VS_API_BASE}/productions",
                params={"query": title, "pageSize": "50"},
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("productions") or data.get("items") or []
        except Exception as exc:
            logger.warning("VS resolver: query search failed — %s", exc)
            return None

        best_match = None
        for item in items:
            item_date = (item.get("localDate") or "")[:10]
            name = (item.get("name") or "").lower()
            name_words = set(_re.split(r'\W+', name))
            overlap = kw_set & name_words
            if not overlap:
                continue
            vs_id = str(item.get("id") or "")
            if not vs_id:
                continue
            if date_str and item_date == date_str:
                logger.info(
                    "VS resolver: matched '%s' → '%s' id=%s date=%s",
                    title, item.get("name"), vs_id, item_date,
                )
                return vs_id
            # Keep first keyword-match as fallback if no exact date match
            if best_match is None and (not date_str or abs(
                (datetime.strptime(item_date, "%Y-%m-%d") - event_date.replace(tzinfo=None)).days
            ) <= 1 if item_date and date_str else True):
                best_match = (vs_id, item.get("name"), item_date)

        if best_match:
            logger.info(
                "VS resolver: fuzzy-date match '%s' → '%s' id=%s date=%s (expected %s)",
                title, best_match[1], best_match[0], best_match[2], date_str,
            )
            return best_match[0]

        logger.info("VS resolver: no results for '%s' on %s", title, date_str)
        return None

    # ── Listings fetch ────────────────────────────────────────────────────────

    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        event_id = tracked_event.external_event_id
        if not event_id:
            return []

        try:
            resp = await self._client().get(
                f"{_VS_API_BASE}/listings",
                params={"productionId": event_id, "qty": "1"},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                logger.info("VS collector: event %s not found", event_id)
            elif status in (401, 403):
                logger.warning("VS collector: auth failure for event %s", event_id)
            else:
                logger.warning("VS collector: HTTP %s for event %s", status, event_id)
            return []
        except Exception as exc:
            logger.warning("VS collector: fetch failed for event %s — %s", event_id, exc)
            return []

        listings = self._parse(event_id, data)
        raw_count = len(data.get("tickets") or [])
        logger.info(
            "VS collector: event=%s raw=%d retained=%d",
            event_id, raw_count, len(listings),
        )
        return listings

    def _parse(self, event_id: str, data: dict) -> list[RawListing]:
        """
        Parse the /hermes/api/v1/listings response.

        Response shape (confirmed from live API):
          data["tickets"] — list of listing objects
          data["global"]  — event-level metadata (listingCount, lowestAip, etc.)

        Ticket field mapping (abbreviated keys are canonical):
          i / listingId         → external_listing_id
          p                     → price (base, pre-fee, in USD)
          aip / allInPricePerTicket → all_in_price (checkout-equivalent, in USD)
          s / sectionName       → section
          r / row               → row (string)
          q / quantity          → quantity
        """
        raw_listings: list = data.get("tickets") or []
        results: list[RawListing] = []
        parking_count = 0

        for item in raw_listings:
            raw_id = item.get("i") or item.get("listingId") or item.get("id") or ""
            if not raw_id:
                continue

            # Base price — abbreviated key "p" is authoritative
            raw_price = item.get("p") or item.get("pricePerTicket") or item.get("price")
            price = _to_decimal(raw_price)
            if price is None or price <= 0:
                continue

            # All-in price — "aip" or long-form
            all_in_raw = item.get("aip") or item.get("allInPricePerTicket") or item.get("totalPrice")
            all_in = _to_decimal(all_in_raw)

            # Derive fees if both values present
            fees_val: Optional[Decimal] = None
            if all_in is not None and all_in > price:
                fees_val = all_in - price

            section = (
                item.get("sectionName")
                or item.get("s")
                or item.get("section")
                or "General"
            )
            row_raw = item.get("row") or item.get("r") or None
            row = str(row_raw) if row_raw and not isinstance(row_raw, dict) else None

            qty_raw = item.get("quantity") or item.get("q") or item.get("availableCount")
            qty = int(qty_raw) if qty_raw else 1

            # Parking filter — safety net (parking is a separate production on VS,
            # so this should almost never trigger, but apply shared logic anyway)
            if _is_parking_listing(str(section), row):
                parking_count += 1
                logger.debug("VS: parking excluded section=%r row=%r", section, row)
                continue

            results.append(RawListing(
                external_listing_id=f"vs-{raw_id}",
                section=str(section),
                row=row,
                quantity=qty,
                price=price,
                fees=fees_val if fees_val and fees_val > 0 else None,
                all_in_price=all_in,
                market_segment=_SEGMENT,
                listing_url=f"https://www.vividseats.com/production/{event_id}",
            ))

        if parking_count:
            logger.info("VS collector: event=%s parking_excluded=%d", event_id, parking_count)
        return results

    # ── Section normalisation ─────────────────────────────────────────────────

    def normalize_section(self, raw_section: str) -> str:
        if not raw_section:
            return ""
        s = re.sub(r"(?i)^(section|sec\.?)\s*", "", raw_section.strip())
        return s.upper()
