import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Optional

import httpx
from playwright.async_api import async_playwright

from app.collectors.base import BaseCollector, RawListing
from app.config import Settings

SEATGEEK_OFFICIAL_API = "https://api.seatgeek.com/2/listings"
SEATGEEK_INTERNAL_API = "https://seatgeek.com/api/listings"
NEXTDATA_KEY_PATHS = [
    ["props", "pageProps", "listings"],
    ["props", "pageProps", "event", "listings"],
    ["props", "pageProps", "initialData", "listings"],
]


class SeatGeekCollector(BaseCollector):
    marketplace_slug = "seatgeek"

    def __init__(self, settings: Settings, debug_mode: bool = False, slow_mo_ms: int = 0):
        super().__init__(settings, debug_mode, slow_mo_ms)
        self._client_id = settings.seatgeek_client_id
        self._session_path = Path(settings.browser_data_dir) / "seatgeek"
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        event_id = tracked_event.external_event_id
        if not event_id and tracked_event.external_url:
            event_id = await self._extract_event_id(tracked_event.external_url)
        if not event_id:
            raise ValueError("No SeatGeek event ID")

        if self._client_id:
            skip = await self.should_skip_pattern(SEATGEEK_OFFICIAL_API, "http_failure")
            if not skip:
                async with self.telemetry("official_api", url=SEATGEEK_OFFICIAL_API, event_id=event_id):
                    listings = await self._fetch_official_api(event_id)
                    if listings is not None: return listings

        listings = await self._fetch_internal_api(event_id)
        if listings is not None: return listings

        if tracked_event.external_url:
            listings = await self._fetch_nextdata(tracked_event.external_url, event_id)
            if listings is not None: return listings

        return await self._fetch_via_playwright(tracked_event.external_url or f"https://seatgeek.com/event/{event_id}")

    async def _fetch_official_api(self, event_id: str) -> Optional[list[RawListing]]:
        client = await self._get_http_client()
        params = {"event_id": event_id, "client_id": self._client_id, "per_page": 500}
        if self.settings.seatgeek_client_secret:
            params["client_secret"] = self.settings.seatgeek_client_secret
        try:
            resp = await client.get(SEATGEEK_OFFICIAL_API, params=params)
            if resp.status_code == 200: return self._parse_api_response(resp.json())
            await self.record_failure(SEATGEEK_OFFICIAL_API, "http_failure")
            return None
        except Exception as e:
            self.logger.warning("SeatGeek official API failed: %s", e)
            return None

    async def _fetch_internal_api(self, event_id: str) -> Optional[list[RawListing]]:
        client = await self._get_http_client()
        try:
            resp = await client.get(SEATGEEK_INTERNAL_API, params={"event_id": event_id, "per_page": 500})
            if resp.status_code == 200: return self._parse_api_response(resp.json())
            return None
        except Exception: return None

    async def _fetch_nextdata(self, url: str, event_id: str) -> Optional[list[RawListing]]:
        client = await self._get_http_client()
        try:
            resp = await client.get(url)
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text, re.DOTALL)
            if not match:
                await self.record_failure("__NEXT_DATA__", "selector_failure")
                return None
            page_data = json.loads(match.group(1))
            for path in NEXTDATA_KEY_PATHS:
                path_key = ".".join(path)
                skip = await self.should_skip_pattern(f"nextdata:{path_key}", "parse_error")
                if skip: continue
                node = page_data
                try:
                    for key in path: node = node[key]
                    listings = self._parse_api_response({"listings": node})
                    if listings:
                        await self.record_fallback_success("__NEXT_DATA__", f"nextdata:{path_key}", "selector_failure")
                        return listings
                except (KeyError, TypeError):
                    await self.record_failure(f"nextdata:{path_key}", "parse_error")
            return None
        except Exception: return None

    async def _fetch_via_playwright(self, url: str) -> list[RawListing]:
        self._session_path.mkdir(parents=True, exist_ok=True)
        captured: list[dict] = []
        cdp_url = getattr(self.settings, "cdp_url", None)
        async with async_playwright() as p:
            if cdp_url:
                browser = await p.chromium.connect_over_cdp(cdp_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
            else:
                context = await p.chromium.launch_persistent_context(str(self._session_path), headless=not self.debug_mode, args=["--no-sandbox"])
            page = await context.new_page()
            self._current_page = page
            async def intercept(response):
                if "listings" in response.url and response.status == 200:
                    try:
                        data = await response.json()
                        if "listings" in data: captured.append(data)
                    except Exception: pass
            page.on("response", intercept)
            await page.goto(url, wait_until="networkidle", timeout=30000)
            self._current_page = None
            if not cdp_url: await context.close()
        listings = []
        for data in captured: listings.extend(self._parse_api_response(data))
        return listings

    def _parse_api_response(self, data: dict) -> list[RawListing]:
        listings = []
        for item in data.get("listings", []):
            try:
                price_raw = item.get("price_per_ticket", item.get("retail_price", 0))
                price = Decimal(str(price_raw.get("amount", 0) if isinstance(price_raw, dict) else price_raw))
                fees_raw = item.get("fee_per_ticket")
                fees = Decimal(str(fees_raw.get("amount", 0) if isinstance(fees_raw, dict) else fees_raw)) if fees_raw else None
                listings.append(RawListing(
                    external_listing_id=str(item.get("id", "")), section=str(item.get("section", "Unknown")),
                    row=item.get("row"), quantity=int(item.get("quantity", 1)), price=price, fees=fees,
                    all_in_price=(price + fees) if fees else None, listing_url=item.get("listing_url"),
                ))
            except Exception: pass
        return listings

    async def _extract_event_id(self, url: str) -> Optional[str]:
        m = re.search(r"/(\d+)(?:\?|$|#)", url)
        return m.group(1) if m else None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", "Accept": "application/json", "Referer": "https://seatgeek.com/"},
                follow_redirects=True, timeout=30.0,
            )
        return self._http_client

    def normalize_section(self, raw_section: str) -> str:
        return re.sub(r"^(Section|Sec\.?)\s*", "", raw_section.strip(), flags=re.IGNORECASE).upper()

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
