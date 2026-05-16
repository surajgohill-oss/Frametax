"""
GameTime ingestion adapter.

GameTime is a mobile-first aggregated resale marketplace.
market_segment is always "aggregated_resale".

API surface:
  Listings: GET https://mobile.gametime.co/v1/events/{event_id}/listings
  Search:   GET https://mobile.gametime.co/v1/events/search?query={q}

Partial-data tolerance:
  - section_name may be absent → default to "General"
  - price is always required; skip rows where price is missing or non-positive
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from typing import Optional
import logging

import httpx

from app.collectors.base import BaseCollector, RawListing

logger = logging.getLogger("collector.gametime")

_GT_API_BASE = "https://mobile.gametime.co/v1"
_SEGMENT     = "aggregated_resale"


def _to_decimal(value) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(float(value)))
    except (InvalidOperation, ValueError, TypeError):
        return None


class GameTimeCollector(BaseCollector):
    marketplace_slug = "gametime"

    def __init__(self, settings, debug_mode: bool = False, slow_mo_ms: int = 0):
        super().__init__(settings, debug_mode=debug_mode, slow_mo_ms=slow_mo_ms)
        self._api_key: str = getattr(settings, "gametime_api_key", "")
        self._http: Optional[httpx.AsyncClient] = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            headers = {
                "Accept":     "application/json",
                "User-Agent": "GameTime/5.0 (iPhone; iOS 16.0; Scale/3.00)",
            }
            if self._api_key:
                headers["Authorization"] = f"Token {self._api_key}"
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
            logger.warning("GT resolver: search failed — %s", exc)
            return None

    async def _search_event(self, title: str, event_date: Optional[datetime]) -> Optional[str]:
        params: dict = {"query": title[:100], "limit": "5"}
        if event_date:
            params["date"] = event_date.strftime("%Y-%m-%d")

        try:
            resp = await self._client().get(f"{_GT_API_BASE}/events/search", params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("GT resolver: HTTP failure — %s", exc)
            return None

        events = (
            data.get("events")
            or data.get("results")
            or (data if isinstance(data, list) else [])
        )
        if not events:
            logger.info("GT resolver: no results for '%s'", title)
            return None

        event = events[0]
        gt_id = str(event.get("id") or event.get("event_id") or "")
        if not gt_id:
            return None

        logger.info("GT resolver: matched '%s' → GT event_id=%s", title, gt_id)
        return gt_id

    # ── Listings fetch ────────────────────────────────────────────────────────

    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        event_id = tracked_event.external_event_id
        if not event_id:
            return []

        try:
            resp = await self._client().get(
                f"{_GT_API_BASE}/events/{event_id}/listings",
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                logger.info("GT collector: event %s not found", event_id)
            elif status in (401, 403):
                logger.warning("GT collector: auth failure for event %s", event_id)
            else:
                logger.warning("GT collector: HTTP %s for event %s", status, event_id)
            return []
        except Exception as exc:
            logger.warning("GT collector: fetch failed for event %s — %s", event_id, exc)
            return []

        listings = self._parse(event_id, data)
        logger.info("GT collector: event=%s listings=%d", event_id, len(listings))
        return listings

    def _parse(self, event_id: str, data: dict) -> list[RawListing]:
        raw_listings = (
            data.get("listings")
            or data.get("ticket_groups")
            or (data if isinstance(data, list) else [])
        )
        results: list[RawListing] = []

        for item in raw_listings:
            raw_id = item.get("id") or item.get("listing_id") or ""
            if not raw_id:
                continue

            # Price — always required; skip if missing
            raw_price = (
                item.get("price")
                or item.get("price_per_ticket")
                or item.get("cost")
            )
            price = _to_decimal(raw_price)
            if price is None or price <= 0:
                continue

            all_in_raw = item.get("all_in_price") or item.get("total_price")
            all_in     = _to_decimal(all_in_raw)
            fees       = (all_in - price) if (all_in is not None and all_in > price) else None

            # Section — safe default when absent
            section = (
                item.get("section")
                or item.get("section_name")
                or item.get("section_id")
                or "General"
            )

            row = item.get("row") or item.get("row_name") or None
            qty = int(item.get("quantity") or item.get("available_quantity") or 1)

            results.append(RawListing(
                external_listing_id=f"gt-{raw_id}",
                section=str(section),
                row=str(row) if row else None,
                quantity=qty,
                price=price,
                fees=fees if fees and fees > 0 else None,
                all_in_price=all_in,
                market_segment=_SEGMENT,
                listing_url=item.get("url") or f"https://gametime.co/events/{event_id}",
            ))

        return results

    # ── Section normalisation ─────────────────────────────────────────────────

    def normalize_section(self, raw_section: str) -> str:
        if not raw_section:
            return ""
        s = re.sub(r"(?i)^(section|sec\.?)\s*", "", raw_section.strip())
        return s.upper()
