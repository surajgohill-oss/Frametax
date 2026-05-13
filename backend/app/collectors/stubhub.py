"""
StubHub Collector

Fetch strategy (in order, with FailureMemory routing):
  1. Internal Solr JSON API  → fastest, no JS required
  2. Playwright headed/headless with response interception → intercepts XHR
  3. Last resort: parse page JSON embedded in <script> tags

Session management:
  - Uses Playwright launch_persistent_context() so auth cookies survive restarts
  - On 401/403: emits auth_failure to ScraperErrorLog, sets skip flag

Chrome attach mode:
  - If CDP_URL is set on settings, attaches to running browser via CDP
  - Use: launch Chrome with --remote-debugging-port=9222, then set CDP_URL
"""

import asyncio
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Optional

import httpx
from playwright.async_api import async_playwright, BrowserContext

from app.collectors.base import BaseCollector, RawListing
from app.config import Settings

# Primary internal API — Solr-based listing catalog
STUBHUB_SOLR_URL = (
    "https://www.stubhub.com/listingCatalog/select"
    "?q=*:*&fq=event_id:{event_id}&rows=500&start=0"
    "&fl=listing_id,section,row,qty,current_price,all_in_price,fees,"
    "listing_url&sort=current_price+asc&wt=json"
)


class StubHubCollector(BaseCollector):
    marketplace_slug = "stubhub"

    def __init__(self, settings: Settings, debug_mode: bool = False, slow_mo_ms: int = 0):
        super().__init__(settings, debug_mode, slow_mo_ms)
        self._session_path = Path(settings.browser_data_dir) / "stubhub"
        self._cookies_file = self._session_path / "cookies.json"
        self._http_client: Optional[httpx.AsyncClient] = None
        self._browser_context: Optional[BrowserContext] = None

    # ------------------------------------------------------------------ #
    # Top-level fetch                                                      #
    # ------------------------------------------------------------------ #

    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        event_id = tracked_event.external_event_id
        if not event_id and tracked_event.external_url:
            event_id = self._extract_event_id_from_url(tracked_event.external_url)

        if not event_id:
            raise ValueError("No StubHub event ID — add event ID or URL to tracked event")

        if self.debug_mode:
            self._debug_log(f"Resolved event_id={event_id}")
            await self._debug_pause("before HTTP fetch")

        # Check FailureMemory: should we skip the JSON API?
        skip_json = await self.should_skip_pattern(STUBHUB_SOLR_URL, "http_failure")

        listings = None
        if not skip_json:
            async with self.telemetry("solr_api", url=STUBHUB_SOLR_URL, event_id=event_id):
                listings = await self._fetch_via_json_api(event_id)

        if listings is None:
            if self.debug_mode:
                self._debug_log("JSON API gave no results — falling back to Playwright")
            await self._debug_pause("before Playwright fallback")
            listings = await self._fetch_via_playwright(
                event_id, tracked_event.external_url
            )

        if not listings:
            async with self.telemetry("empty_response", event_id=event_id):
                raise ValueError(f"StubHub returned 0 listings for event {event_id}")

        return listings

    # ------------------------------------------------------------------ #
    # JSON API path                                                        #
    # ------------------------------------------------------------------ #

    async def _fetch_via_json_api(self, event_id: str) -> Optional[list[RawListing]]:
        client = await self._get_http_client()
        url = STUBHUB_SOLR_URL.format(event_id=event_id)
        if self.debug_mode:
            self._debug_log("HTTP GET", url=url)
        try:
            resp = await client.get(url)
            if self.debug_mode:
                self._debug_log(f"HTTP {resp.status_code}", url=url)

            if resp.status_code == 200:
                data = resp.json()
                listings = self._parse_solr_response(data)
                if self.debug_mode:
                    self._debug_log(f"Parsed {len(listings)} listings from Solr")
                return listings

            if resp.status_code in (401, 403):
                await self.record_failure(STUBHUB_SOLR_URL, "auth_failure")
                await self._emit_error(
                    "auth_failure", "solr_api", url, None, event_id,
                    Exception(f"HTTP {resp.status_code}"), resp.status_code
                )
                return None

            await self.record_failure(STUBHUB_SOLR_URL, "http_failure")
            return None
        except Exception as e:
            self.logger.warning("StubHub JSON API failed: %s", e)
            await self.record_failure(STUBHUB_SOLR_URL, "http_failure")
            return None

    def _parse_solr_response(self, data: dict) -> list[RawListing]:
        listings = []
        docs = data.get("response", {}).get("docs", [])
        for doc in docs:
            try:
                listing = RawListing(
                    external_listing_id=str(doc.get("listing_id", "")),
                    section=str(doc.get("section", "Unknown")),
                    row=doc.get("row"),
                    quantity=int(doc.get("qty", 1)),
                    price=Decimal(str(doc.get("current_price", 0))),
                    fees=Decimal(str(doc["fees"])) if doc.get("fees") else None,
                    all_in_price=Decimal(str(doc["all_in_price"])) if doc.get("all_in_price") else None,
                    listing_url=doc.get("listing_url"),
                )
                listings.append(listing)
            except Exception as e:
                self.logger.debug("Skip malformed doc: %s", e)
        return listings

    # ------------------------------------------------------------------ #
    # Playwright path                                                      #
    # ------------------------------------------------------------------ #

    async def _fetch_via_playwright(
        self, event_id: str, fallback_url: Optional[str]
    ) -> list[RawListing]:
        self._session_path.mkdir(parents=True, exist_ok=True)
        captured: list[dict] = []
        listings: list[RawListing] = []

        # Check if we should attach to existing Chrome (CDP mode)
        cdp_url = getattr(self.settings, "cdp_url", None)

        async with async_playwright() as p:
            if cdp_url:
                if self.debug_mode:
                    self._debug_log(f"Attaching to Chrome via CDP: {cdp_url}")
                browser = await p.chromium.connect_over_cdp(cdp_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
            else:
                context = await p.chromium.launch_persistent_context(
                    str(self._session_path),
                    headless=not self.debug_mode,
                    slow_mo=self.slow_mo_ms if self.debug_mode else 0,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                )

            page = await context.new_page()
            self._current_page = page

            async def intercept_response(response):
                if "listingCatalog" in response.url and response.status == 200:
                    try:
                        captured.append(await response.json())
                        if self.debug_mode:
                            self._debug_log(f"Intercepted XHR: {response.url[:80]}")
                    except Exception:
                        pass

            page.on("response", intercept_response)

            url = fallback_url or f"https://www.stubhub.com/event/{event_id}"
            if self.debug_mode:
                self._debug_log(f"Navigating to {url}")

            await page.goto(url, wait_until="networkidle", timeout=30000)
            await self._debug_pause("page loaded — inspect DOM if needed")
            await asyncio.sleep(2)

            # Save cookies for future HTTP client reuse
            cookies = await context.cookies()
            self._cookies_file.write_text(json.dumps(cookies, indent=2))
            if self.debug_mode:
                self._debug_log(f"Saved {len(cookies)} cookies")

            # Screenshot on completion in debug mode
            if self.debug_mode:
                await self._capture_screenshot("playwright_result")
                await self._capture_html("playwright_result")

            self._current_page = None
            if not cdp_url:
                await context.close()

        for data in captured:
            listings.extend(self._parse_solr_response(data))

        if self.debug_mode:
            self._debug_log(f"Playwright captured {len(listings)} listings")

        return listings

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            cookies = self._load_saved_cookies()
            self._http_client = httpx.AsyncClient(
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/json, text/javascript, */*",
                    "Referer": "https://www.stubhub.com/",
                },
                cookies=cookies,
                follow_redirects=True,
                timeout=30.0,
            )
        return self._http_client

    def _load_saved_cookies(self) -> dict:
        if self._cookies_file.exists():
            try:
                raw = json.loads(self._cookies_file.read_text())
                return {c["name"]: c["value"] for c in raw}
            except Exception:
                pass
        return {}

    def _extract_event_id_from_url(self, url: str) -> Optional[str]:
        match = re.search(r"/event/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"[?&]event_id=(\d+)", url)
        if match:
            return match.group(1)
        return None

    def normalize_section(self, raw_section: str) -> str:
        s = re.sub(r"^(Section|Sec\.?)\s*", "", raw_section.strip(), flags=re.IGNORECASE)
        return s.upper()

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        if self._browser_context:
            await self._browser_context.close()
