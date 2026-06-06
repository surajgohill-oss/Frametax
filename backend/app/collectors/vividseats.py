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

import asyncio
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

# ── OOM guardrails ────────────────────────────────────────────────────────────
# 60-page default caused OOM on Railway (3 000 items scanned per unresolved event,
# 30-minute resolver cycle hitting every unresolved VS event sequentially).
#
# _VS_SEARCH_MAX_PAGES: hard cap on catalog pages per date-search.
#   5 pages × 50 items = 250 events max — covers all but the busiest festival dates.
#   Busy dates (e.g. 2026-09-17) hit 7+ pages before; 5 is sufficient for most matches
#   since strong-match events typically appear in the first 1–2 pages.
#
# _VS_SEARCH_SEMAPHORE: global asyncio semaphore limiting concurrent VS discovery
#   searches. The resolver fires one search per unresolved event sequentially, but
#   concurrent hydrate calls or task fan-out can stack searches. Cap at 2.
#
# _VS_SEARCH_TIMEOUT_S: per-request timeout for /productions search pages only.
#   Listing fetches use the full 30 s client timeout.
_VS_SEARCH_MAX_PAGES   = 5      # was 60 — hard cap, prevents runaway scans
_VS_SEARCH_TIMEOUT_S   = 10.0   # per /productions page request
_VS_SEARCH_SEMAPHORE   = asyncio.Semaphore(2)  # max 2 concurrent VS discovery searches


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
        Search via /productions with startDate filter.
        /productions/search requires auth (returns 400 without token) — not used.

        OOM guardrails (see module-level constants):
          - Hard cap of _VS_SEARCH_MAX_PAGES pages (5) per search call.
          - Per-request timeout of _VS_SEARCH_TIMEOUT_S (10 s).
          - Global semaphore _VS_SEARCH_SEMAPHORE (2 concurrent searches max).
          - Exits immediately on first keyword match (no accumulation).
        """
        if not event_date:
            logger.info("VS resolver: no event_date — cannot resolve '%s'", title)
            return None

        date_str = event_date.strftime("%Y-%m-%d")
        title_lower = title.lower()
        # Build keyword set — all words > 3 chars from title (strips punctuation)
        import re as _re
        kw_set = {w for w in _re.split(r'\W+', title_lower) if len(w) > 3}

        async with _VS_SEARCH_SEMAPHORE:
            try:
                for page in range(1, _VS_SEARCH_MAX_PAGES + 1):
                    try:
                        resp = await asyncio.wait_for(
                            self._client().get(
                                f"{_VS_API_BASE}/productions",
                                params={
                                    "startDate":  date_str,
                                    "endDate":    date_str,   # CRITICAL: without endDate API returns multi-day
                                    "pageSize":   "50",
                                    "pageNumber": str(page),
                                },
                            ),
                            timeout=_VS_SEARCH_TIMEOUT_S,
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            "VS resolver: page %d timed out after %.0fs for '%s' on %s — stopping",
                            page, _VS_SEARCH_TIMEOUT_S, title, date_str,
                        )
                        break
                    resp.raise_for_status()
                    data = resp.json()
                    items = data.get("items") or []
                    if not items:
                        break
                    for item in items:
                        item_date = (item.get("localDate") or "")[:10]
                        if item_date != date_str:
                            continue
                        name = (item.get("name") or "").lower()
                        name_words = set(_re.split(r'\W+', name))
                        if kw_set & name_words:  # any keyword overlap → immediate return
                            vs_id = str(item.get("id") or "")
                            if vs_id:
                                logger.info(
                                    "VS resolver: matched '%s' → '%s' id=%s page=%d (kw=%s)",
                                    title, item.get("name"), vs_id, page,
                                    kw_set & name_words,
                                )
                                return vs_id
                    # Stop early if we've reached the last catalogue page
                    total_pages = data.get("numberOfPages") or 9999
                    if page >= total_pages:
                        logger.info(
                            "VS resolver: exhausted %d/%d page(s) for '%s' on %s — no match",
                            page, total_pages, title, date_str,
                        )
                        break
                    if page == _VS_SEARCH_MAX_PAGES:
                        logger.info(
                            "VS resolver: reached page cap (%d) for '%s' on %s — no match within cap",
                            _VS_SEARCH_MAX_PAGES, title, date_str,
                        )
            except Exception as exc:
                logger.warning("VS resolver: HTTP failure for '%s' on %s — %s", title, date_str, exc)
                return None

        logger.info("VS resolver: no match for '%s' on %s", title, date_str)
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
        s = raw_section.strip()
        # Strip generic "Section"/"Sec." prefix (shared with all other collectors)
        s = re.sub(r"(?i)^(section|sec\.?)\s*", "", s)
        # VividSeats-specific: strip venue-tier qualifiers that other markets omit.
        # e.g. "Lower Bowl 101" → "101", "Upper Level 205" → "205",
        #      "Lower Level GA" → "GA", "Floor GA" → "GA"
        # This aligns VS section IDs with GameTime / StubHub / TickPick for cross-market dedup.
        s = re.sub(
            r"(?i)^(lower bowl|upper bowl|lower level|upper level|lower deck|upper deck"
            r"|lower tier|upper tier|club level|loge level|mezzanine level|mezzanine"
            r"|terrace level|terrace|field level|field|suite level|suite|box)\s+",
            "",
            s,
        )
        return s.upper()
