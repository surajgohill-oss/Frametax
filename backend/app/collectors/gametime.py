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
            # Prefer event.artist (shorter, cleaner) over full title for performer search.
            # Avoids splitting "NFL: 49ers vs Cowboys" on ':' and querying for just "NFL".
            artist = getattr(getattr(tracked_event, "event", None), "artist", None)
            return await self._search_event(artist or title, event_date)
        except Exception as exc:
            logger.warning("GT resolver: search failed — %s", exc)
            return None

    async def _search_event(self, title: str, event_date: Optional[datetime]) -> Optional[str]:
        """
        Two-step Gametime resolution:
          Step 1: /v1/performers?query=artist → get performer id
          Step 2: /v1/events?performer_id=ID&per_page=100 → match by local date

        The old /v1/events/search endpoint returns HTTP 404.
        The /v1/performers endpoint returns JSON with id, name, slug.
        The /v1/events endpoint supports per_page up to 100.
        """
        import re as _re

        # Extract artist keyword — use artist field (shorter, cleaner) when available
        # For events.title like "BTS World Tour" → performer_query="BTS"
        artist_query = title.strip()

        # Build search queries: try shorter performer name variants
        # Strip " World Tour", ": Eternal ...", "&  LA Phil", etc.
        stripped = _re.split(r'\s*[:|–—&]\s*', artist_query)[0].strip()
        queries = [stripped, artist_query] if stripped != artist_query else [artist_query]

        if not event_date:
            logger.info("GT resolver: no event_date — cannot resolve '%s'", title)
            return None

        target_date = event_date.strftime("%Y-%m-%d")

        for query in queries:
            # Step 1: find performer
            try:
                resp = await self._client().get(
                    f"{_GT_API_BASE}/performers",
                    params={"query": query[:80]},
                )
                resp.raise_for_status()
                perfs = resp.json().get("performers", [])
            except Exception as exc:
                logger.warning("GT resolver: performers search failed for '%s' — %s", query, exc)
                continue

            if not perfs:
                logger.info("GT resolver: no performers for '%s'", query)
                continue

            # Find best matching performer (case-insensitive name match)
            query_lower = query.lower()
            best_perf = None
            for p in perfs:
                pname = (p.get("name") or p.get("medium_name") or "").lower()
                if query_lower in pname or pname in query_lower:
                    best_perf = p
                    break
            if not best_perf:
                # No name match — do NOT fall back to first result (Gametime returns
                # generic popular performers when query is unknown, e.g. "Morgan Jay"
                # returns FIFA World Cup. Using wrong performer is worse than returning None.)
                logger.info("GT resolver: no name-matched performer for '%s' — skipping", query)
                return None

            perf_id = best_perf.get("id") or ""
            if not perf_id:
                continue

            logger.debug("GT resolver: performer '%s' → id=%s", best_perf.get("name"), perf_id)

            # Step 2: get performer's events and match by date
            try:
                resp = await self._client().get(
                    f"{_GT_API_BASE}/events",
                    params={"performer_id": perf_id, "per_page": "100"},
                )
                resp.raise_for_status()
                events_data = resp.json().get("events", [])
            except Exception as exc:
                logger.warning("GT resolver: events fetch failed for perf_id=%s — %s", perf_id, exc)
                continue

            for item in events_data:
                ev = item.get("event", item)
                ev_date = (ev.get("datetime_local") or "")[:10]
                if ev_date == target_date:
                    gt_id = str(ev.get("id") or "")
                    if gt_id:
                        logger.info(
                            "GT resolver: matched '%s' → '%s' id=%s on %s",
                            title, ev.get("name"), gt_id, ev_date,
                        )
                        return gt_id

            logger.info(
                "GT resolver: performer '%s' has no event on %s for '%s'",
                best_perf.get("name"), target_date, title,
            )
            # Don't try next query variant — performer found but event not yet listed
            return None

        logger.info("GT resolver: no match for '%s' on %s", title, target_date)
        return None

    # ── Listings fetch ────────────────────────────────────────────────────────

    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        event_id = tracked_event.external_event_id
        if not event_id:
            return []

        try:
            # GT API v2026: endpoint changed from /events/{id}/listings to
            # /listings?event_id={id}. Old endpoint returns 404 for all events.
            resp = await self._client().get(
                f"{_GT_API_BASE}/listings",
                params={"event_id": event_id},
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

            # Price — GT API v2026: price is now a nested dict with values in cents.
            # prefee = base price per ticket (pre-fee), total = all-in price per ticket.
            # Legacy format (flat float) also handled for backward compatibility.
            raw_price_field = item.get("price")
            if isinstance(raw_price_field, dict):
                # New nested format: values in cents
                prefee_cents = raw_price_field.get("prefee") or raw_price_field.get("face_value")
                total_cents  = raw_price_field.get("total")
                if not prefee_cents and not total_cents:
                    continue
                # Use total as authoritative price if prefee is absent
                price_cents = prefee_cents or total_cents
                try:
                    price  = Decimal(str(price_cents)) / 100
                    all_in = Decimal(str(total_cents)) / 100 if total_cents else None
                except (InvalidOperation, TypeError):
                    continue
            else:
                # Legacy flat-float format
                raw_price = (
                    raw_price_field
                    or item.get("price_per_ticket")
                    or item.get("cost")
                )
                price = _to_decimal(raw_price)
                all_in_raw = item.get("all_in_price") or item.get("total_price")
                all_in = _to_decimal(all_in_raw)

            if price is None or price <= 0:
                continue

            fees = (all_in - price) if (all_in is not None and all_in > price) else None

            # Section — safe default when absent
            section = (
                item.get("section")
                or item.get("section_name")
                or item.get("section_id")
                or "General"
            )

            row = item.get("row") or item.get("row_name") or None

            # Quantity: new API uses "lots" list (one entry per ticket slot).
            # Legacy used "quantity" / "available_quantity" integer.
            lots = item.get("lots")
            if lots and isinstance(lots, list):
                qty = len(lots)
            else:
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
