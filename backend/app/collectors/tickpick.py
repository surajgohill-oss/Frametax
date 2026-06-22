"""
TickPick ingestion adapter.

TickPick is a no-fee secondary resale marketplace.
market_segment is always "secondary_resale" — TickPick does not carry primary inventory.

API surface:
  Listings: GET https://api.tickpick.com/1.0/listings/event/{event_id}
  Search:   GET https://api.tickpick.com/1.0/performances/search?q={query}

Price units: cents (integer) — divide by 100.
"""
from __future__ import annotations

import json as _json
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

import httpx

from app.collectors.base import BaseCollector, RawListing
from app.collectors.normalize import is_parking_listing as _is_parking_listing

logger = logging.getLogger("collector.tickpick")

_TP_API_BASE = "https://api.tickpick.com/1.0"
_SEGMENT     = "secondary_resale"


def _cents_to_decimal(value) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(int(value))) / 100
    except (InvalidOperation, ValueError, TypeError):
        return None


def _float_to_decimal(value) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(float(value)))
    except (InvalidOperation, ValueError, TypeError):
        return None


class TickPickCollector(BaseCollector):
    marketplace_slug = "tickpick"

    def __init__(self, settings, debug_mode: bool = False, slow_mo_ms: int = 0):
        super().__init__(settings, debug_mode=debug_mode, slow_mo_ms=slow_mo_ms)
        self._api_key: str = getattr(settings, "tickpick_api_key", "")
        self._http: Optional[httpx.AsyncClient] = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            headers = {"Accept": "application/json"}
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

        event_date = getattr(getattr(tracked_event, "event", None), "event_date", None)

        # Path 1: performer/category page URL (e.g. /comedy/morgan-jay-tickets/)
        # TickPick category pages embed MusicEvent JSON-LD with event IDs and dates.
        ext_url = getattr(tracked_event, "external_url", None)
        if ext_url and "tickpick.com" in ext_url:
            result = await self._resolve_from_performer_page(ext_url, event_date)
            if result:
                return result

        # Path 2: title + date search via API (returns 404 as of 2026 — kept as
        # fallback in case the endpoint is restored; silently returns None on 404)
        try:
            title = getattr(getattr(tracked_event, "event", None), "title", "") or ""
            if title:
                return await self._search_event(title, event_date)
        except Exception as exc:
            logger.warning("TP resolver: search failed — %s", exc)
        return None

    async def _resolve_from_performer_page(
        self, page_url: str, event_date: Optional[datetime]
    ) -> Optional[str]:
        """
        Fetch a TickPick performer/category page and extract event ID from
        MusicEvent JSON-LD entries, matching by date (±1 day).
        """
        import json as _json
        import re as _re

        try:
            resp = await self._client().get(page_url)
            if resp.status_code != 200:
                logger.debug("TP performer page: HTTP %s for %s", resp.status_code, page_url)
                return None
        except Exception as exc:
            logger.warning("TP performer page: fetch failed — %s", exc)
            return None

        html = resp.text
        jsonld_blocks = _re.findall(
            r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
            html, _re.DOTALL,
        )
        # Collect candidates with their match quality (lower delta = better)
        candidates: list[tuple[int, str, str]] = []  # (delta_days, tp_id, date_str)

        for block in jsonld_blocks:
            try:
                d = _json.loads(block)
            except Exception:
                continue
            schema_type = d.get("@type", "")
            if not (schema_type == "Event" or schema_type.endswith("Event")):
                continue
            url = d.get("url", "")
            # Extract event ID from URL: /buy-artist-tickets-venue-date/{id}/
            m = _re.search(r"/(\d{5,})/?$", url.rstrip("/"))
            if not m:
                continue
            tp_id = m.group(1)

            if event_date is None:
                return tp_id

            start_date_str = d.get("startDate", "")
            try:
                if "T" in start_date_str:
                    page_dt = datetime.fromisoformat(start_date_str)
                else:
                    page_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                delta = abs((page_dt.date() - event_date.date()).days)
                if delta == 0:  # exact date match only — ±1 day caused cross-event contamination
                    candidates.append((delta, tp_id, start_date_str))
            except Exception:
                continue

        if not candidates:
            logger.debug("TP performer page: no date match on %s for %s", page_url, event_date)
            return None

        # Prefer exact match (delta=0) over ±1 day match
        candidates.sort(key=lambda x: x[0])
        best_delta, best_id, best_date = candidates[0]
        logger.info(
            "TP performer page: matched date=%s id=%s url=%s",
            best_date, best_id, page_url,
        )
        return best_id

    async def _search_event(self, title: str, event_date: Optional[datetime]) -> Optional[str]:
        params: dict = {"q": title[:100], "limit": "5"}
        if event_date:
            params["date"] = event_date.strftime("%Y-%m-%d")

        try:
            resp = await self._client().get(f"{_TP_API_BASE}/performances/search", params=params)
            if resp.status_code == 404:
                # API endpoint removed as of 2026 — performer page path is the fallback
                return None
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("TP resolver: HTTP failure — %s", exc)
            return None

        performances = data.get("performances") or data.get("results") or []
        if not performances:
            logger.info("TP resolver: no results for '%s'", title)
            return None

        perf = performances[0]
        tp_id = str(perf.get("id") or perf.get("performanceId") or "")
        if not tp_id:
            return None

        logger.info("TP resolver: matched '%s' → TP event_id=%s", title, tp_id)
        return tp_id

    # ── Listings fetch ────────────────────────────────────────────────────────

    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        event_id = tracked_event.external_event_id
        if not event_id:
            return []

        # Strategy 1: JSON API — try new event-v2 endpoint first, then legacy
        for api_url in [
            f"{_TP_API_BASE}/listings/internal/event-v2/{event_id}?trackView=true",
            f"{_TP_API_BASE}/listings/event/{event_id}?needidd=true",
        ]:
            try:
                resp = await self._client().get(api_url)
                resp.raise_for_status()
                data = resp.json()
                listings = self._parse(event_id, data)
                logger.info("TP collector: API %s event=%s listings=%d", api_url.split("/")[-1].split("?")[0], event_id, len(listings))
                if listings:
                    return listings
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 403:
                    logger.info("TP collector: API 403 for %s event %s", api_url, event_id)
                elif status == 404:
                    logger.info("TP collector: event %s not found via %s", event_id, api_url)
                else:
                    logger.warning("TP collector: API HTTP %s for event %s url=%s", status, event_id, api_url)
            except Exception as exc:
                logger.warning("TP collector: API fetch failed for event %s — %s", event_id, exc)

        # Strategy 2: HTML page scrape — event page returns 200 from Railway IPs
        ext_url = getattr(tracked_event, "external_url", None) or f"https://www.tickpick.com/buy-tickets/{event_id}/"
        html_listings = await self._fetch_via_html(event_id, ext_url)
        if html_listings is not None:
            logger.info("TP collector: HTML event=%s listings=%d", event_id, len(html_listings))
            if html_listings:
                return html_listings

        # Strategy 3: Playwright — intercept api.tickpick.com response in real browser
        # Always use the event-specific URL, not the performer page URL.
        event_url = f"https://www.tickpick.com/buy-tickets/{event_id}/"
        playwright_listings = await self._fetch_via_playwright(event_id, event_url)
        if playwright_listings is not None:
            logger.info("TP collector: Playwright event=%s listings=%d", event_id, len(playwright_listings))
            return playwright_listings

        return []

    async def _fetch_via_playwright(self, event_id: str, url: str) -> Optional[list]:
        """
        Load the TickPick event page in Playwright and intercept the API response.
        TickPick's SPA makes an authenticated XHR to api.tickpick.com/1.0/listings/event/{id}
        using browser session cookies — this bypasses the 403 that httpx gets.
        Uses the persistent browser session from browser_data_dir/tickpick/.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("TP Playwright: playwright not installed — skipping")
            return None

        from app.config import get_settings
        import asyncio

        session_dir = getattr(get_settings(), "browser_data_dir", "/tmp")
        session_path = str(Path(session_dir) / "tickpick") if session_dir else "/tmp/tickpick"
        Path(session_path).mkdir(parents=True, exist_ok=True)

        captured: list[dict] = []

        try:
            async with async_playwright() as p:
                ctx = await p.chromium.launch_persistent_context(
                    session_path,
                    headless=True,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                )
                page = await ctx.new_page()

                async def on_response(response):
                    if "api.tickpick.com" in response.url and "listings" in response.url:
                        if response.status == 200:
                            try:
                                data = await response.json()
                                captured.append(data)
                                logger.info("TP Playwright: captured %s (%d bytes)", response.url, len(str(data)))
                            except Exception as exc:
                                logger.debug("TP Playwright: JSON parse error — %s", exc)

                page.on("response", on_response)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(8)  # wait for SPA to fire XHR
                await ctx.close()
        except Exception as exc:
            logger.warning("TP Playwright: error for event=%s — %s", event_id, exc)
            return None

        if not captured:
            logger.info("TP Playwright: no API response captured for event=%s", event_id)
            return None

        all_listings = []
        for data in captured:
            all_listings.extend(self._parse(event_id, data))
        return all_listings

    async def _fetch_via_html(self, event_id: str, url: str) -> Optional[list]:
        """
        Scrape TickPick event page HTML for embedded listing JSON.
        The page returns HTTP 200 from Railway IPs even though api.tickpick.com returns 403.
        TickPick embeds listing data in a <script> tag as JSON (window.__INITIAL_STATE__
        or an inline JSON blob with a 'listing' key).
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
        }
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=25.0, headers=headers) as client:
                resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning("TP HTML: HTTP %s for %s", resp.status_code, url)
                return None
        except Exception as exc:
            logger.warning("TP HTML fetch failed: %s", exc)
            return None

        html = resp.text
        logger.info("TP HTML: fetched %d bytes from %s", len(html), url)

        # Try multiple extraction patterns
        # Pattern 1: window.__INITIAL_STATE__ = {...}
        for pattern in (
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});?\s*</script>',
            r'window\.__REDUX_STATE__\s*=\s*(\{.*?\});?\s*</script>',
        ):
            m = re.search(pattern, html, re.DOTALL)
            if m:
                try:
                    data = _json.loads(m.group(1))
                    # Drill for listing data
                    for path in [["listings", "items"], ["event", "listings"], ["listing"]]:
                        node = data
                        try:
                            for key in path: node = node[key]
                            if isinstance(node, list) and node:
                                logger.info("TP HTML: found %d items via window state path=%s", len(node), path)
                                return self._parse(event_id, {"listing": node})
                        except (KeyError, TypeError):
                            pass
                except Exception as exc:
                    logger.debug("TP HTML window state parse error: %s", exc)

        # Pattern 2: NEXT_DATA script
        nd_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if nd_match:
            try:
                nd = _json.loads(nd_match.group(1))
                page_props = nd.get("props", {}).get("pageProps", {}) or {}
                for key in ("listings", "initialListings", "eventListings"):
                    items = page_props.get(key)
                    if isinstance(items, list) and items:
                        logger.info("TP HTML NEXT_DATA: found %d items key=%s", len(items), key)
                        return self._parse(event_id, {"listing": items})
            except Exception as exc:
                logger.debug("TP HTML NEXT_DATA parse error: %s", exc)

        # Pattern 3: Inline JSON blob containing "listing" key with price/section data
        # TickPick React app embeds hydration data as JSON inside <script> tags
        script_re = re.finditer(r'<script[^>]*>(\{[^<]{500,})</script>', html, re.DOTALL)
        for m in script_re:
            try:
                blob = _json.loads(m.group(1))
                raw = blob.get("listing") or blob.get("listings")
                if isinstance(raw, list) and raw and isinstance(raw[0], dict):
                    # Verify it looks like listing data (has price field)
                    if any(k in raw[0] for k in ("p", "price", "pricePerTicket", "currentPrice")):
                        logger.info("TP HTML inline blob: found %d listings", len(raw))
                        return self._parse(event_id, {"listing": raw})
            except Exception:
                pass

        logger.info("TP HTML: no listing data found in %d byte page", len(html))
        return []

    def _parse(self, event_id: str, data: dict) -> list[RawListing]:
        raw_listings = (
            data.get("listing")
            or data.get("listings")
            or []
        )
        results: list[RawListing] = []
        parking_count = 0

        for item in raw_listings:
            raw_id  = item.get("id") or item.get("listingId") or ""
            if not raw_id:
                continue

            # Price may be in cents (int) or dollars (float) — detect by magnitude
            raw_price = item.get("p") or item.get("price") or item.get("pricePerTicket")
            if raw_price is None:
                continue

            # TickPick typically returns price in cents as integer ≥ 100
            if isinstance(raw_price, int) and raw_price > 500:
                price = _cents_to_decimal(raw_price)
            else:
                price = _float_to_decimal(raw_price)

            if price is None or price <= 0:
                continue

            section = (
                item.get("s")
                or item.get("section")
                or item.get("sectionName")
                or "General"
            )
            row = item.get("r") or item.get("row") or None
            qty = int(item.get("q") or item.get("quantity") or 1)

            # ── Parking filter ────────────────────────────────────────────────
            if _is_parking_listing(str(section), str(row) if row else None):
                parking_count += 1
                logger.debug("TP: parking excluded section=%r row=%r price=%s", section, row, price)
                continue

            results.append(RawListing(
                external_listing_id=f"tp-{raw_id}",
                section=str(section),
                row=str(row) if row else None,
                quantity=qty,
                price=price,
                market_segment=_SEGMENT,
                listing_url=item.get("url") or f"https://www.tickpick.com/buy-tickets/{event_id}/",
            ))

        logger.info(
            "TP collector: event=%s raw=%d parking_excluded=%d tickets_retained=%d",
            event_id, len(raw_listings), parking_count, len(results),
        )
        return results

    # ── Section normalisation ─────────────────────────────────────────────────

    def normalize_section(self, raw_section: str) -> str:
        if not raw_section:
            return ""
        s = re.sub(r"(?i)^(section|sec\.?)\s*", "", raw_section.strip())
        return s.upper()
