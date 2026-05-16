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
  Search:   GET https://www.vividseats.com/hermes/api/v1/productions/search
              ?searchTerm={query}&rows=5

Pricing note:
  Vivid Seats returns prices in dollars (float). Use as-is.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from typing import Optional
import logging

import httpx

from app.collectors.base import BaseCollector, RawListing

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
                "User-Agent": "Mozilla/5.0",
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

        try:
            title = tracked_event.event.title if hasattr(tracked_event, "event") else ""
            event_date = tracked_event.event.event_date if hasattr(tracked_event, "event") else None
            return await self._search_event(title, event_date)
        except Exception as exc:
            logger.warning("VS resolver: search failed — %s", exc)
            return None

    async def _search_event(self, title: str, event_date: Optional[datetime]) -> Optional[str]:
        params: dict = {"searchTerm": title[:100], "rows": "5"}
        if event_date:
            params["startDate"] = event_date.strftime("%Y-%m-%d")
            params["endDate"]   = (event_date + timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            resp = await self._client().get(
                f"{_VS_API_BASE}/productions/search", params=params
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("VS resolver: HTTP failure — %s", exc)
            return None

        productions = (
            data.get("productions")
            or data.get("results")
            or (data if isinstance(data, list) else [])
        )
        if not productions:
            logger.info("VS resolver: no results for '%s'", title)
            return None

        prod = productions[0]
        vs_id = str(prod.get("id") or prod.get("productionId") or "")
        if not vs_id:
            return None

        logger.info("VS resolver: matched '%s' → VS production_id=%s", title, vs_id)
        return vs_id

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
        logger.info("VS collector: event=%s listings=%d", event_id, len(listings))
        return listings

    def _parse(self, event_id: str, data: dict) -> list[RawListing]:
        raw_listings = (
            data.get("listings")
            or data.get("ticketListings")
            or (data if isinstance(data, list) else [])
        )
        results: list[RawListing] = []

        for item in raw_listings:
            raw_id = item.get("id") or item.get("listingId") or ""
            if not raw_id:
                continue

            raw_price = (
                item.get("pricePerTicket")
                or item.get("price")
                or item.get("amount")
            )
            price = _to_decimal(raw_price)
            if price is None or price <= 0:
                continue

            all_in_raw = item.get("totalPrice") or item.get("allInPrice")
            all_in     = _to_decimal(all_in_raw)
            fees_val   = _to_decimal(item.get("fees") or item.get("serviceFee"))
            if fees_val is None and all_in is not None and all_in > price:
                fees_val = all_in - price

            section = (
                item.get("section")
                or item.get("sectionName")
                or item.get("row", {}).get("section") if isinstance(item.get("row"), dict) else None
                or "General"
            )
            row = (
                item.get("row") if isinstance(item.get("row"), str) else None
            ) or item.get("rowId") or None
            qty = int(item.get("quantity") or item.get("availableCount") or 1)

            results.append(RawListing(
                external_listing_id=f"vs-{raw_id}",
                section=str(section),
                row=str(row) if row else None,
                quantity=qty,
                price=price,
                fees=fees_val if fees_val and fees_val > 0 else None,
                all_in_price=all_in,
                market_segment=_SEGMENT,
                listing_url=(
                    item.get("listingUrl")
                    or f"https://www.vividseats.com/production/{event_id}"
                ),
            ))

        return results

    # ── Section normalisation ─────────────────────────────────────────────────

    def normalize_section(self, raw_section: str) -> str:
        if not raw_section:
            return ""
        s = re.sub(r"(?i)^(section|sec\.?)\s*", "", raw_section.strip())
        return s.upper()
