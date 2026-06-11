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

STUBHUB_SOLR_URL = (
    "https://www.stubhub.com/listingCatalog/select"
    "?q=*:*&fq=event_id:{event_id}&rows=500&start=0"
    "&fl=listing_id,section,row,qty,current_price,all_in_price,fees,listing_url&sort=current_price+asc&wt=json"
)


class StubHubCollector(BaseCollector):
    marketplace_slug = "stubhub"

    def __init__(self, settings: Settings, debug_mode: bool = False, slow_mo_ms: int = 0):
        super().__init__(settings, debug_mode, slow_mo_ms)
        self._session_path = Path(settings.browser_data_dir) / "stubhub"
        self._cookies_file = self._session_path / "cookies.json"
        self._http_client: Optional[httpx.AsyncClient] = None

    async def resolve_external_event_id(self, tracked_event) -> Optional[str]:
        eid = tracked_event.external_event_id
        if eid and not eid.startswith("demo-"):
            return eid  # real ID — use it directly

        if tracked_event.external_url:
            extracted = self._extract_event_id_from_url(tracked_event.external_url)
            if extracted:
                self.logger.info("Resolved StubHub event ID %s from URL", extracted)
                return extracted

            slug = self._slug_from_url(tracked_event.external_url)
            if slug:
                resolved = await self._search_event_by_slug(slug)
                if resolved:
                    self.logger.info(
                        "Resolved StubHub event ID %s via search (slug=%s)", resolved, slug
                    )
                    return resolved

        self.logger.warning(
            "Cannot resolve StubHub event ID for tracked_event %d (url=%s)",
            tracked_event.id, tracked_event.external_url,
        )
        return None

    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        event_id = tracked_event.external_event_id

        skip_json = await self.should_skip_pattern(STUBHUB_SOLR_URL, "http_failure")
        listings = None
        if not skip_json:
            async with self.telemetry("solr_api", url=STUBHUB_SOLR_URL, event_id=event_id):
                listings = await self._fetch_via_json_api(event_id)

        if listings is None:
            listings = await self._fetch_via_playwright(event_id, tracked_event.external_url)

        return listings or []

    async def _fetch_via_json_api(self, event_id: str) -> Optional[list[RawListing]]:
        client = await self._get_http_client()
        url = STUBHUB_SOLR_URL.format(event_id=event_id)
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return self._parse_solr_response(resp.json())
            if resp.status_code in (401, 403):
                await self.record_failure(STUBHUB_SOLR_URL, "auth_failure")
                return None
            await self.record_failure(STUBHUB_SOLR_URL, "http_failure")
            return None
        except Exception as e:
            self.logger.warning("StubHub JSON API failed: %s", e)
            await self.record_failure(STUBHUB_SOLR_URL, "http_failure")
            return None

    def _parse_solr_response(self, data: dict) -> list[RawListing]:
        listings = []
        for doc in data.get("response", {}).get("docs", []):
            try:
                raw_id = doc.get("listing_id", "")
                listings.append(RawListing(
                    external_listing_id=f"sh-{raw_id}",
                    section=str(doc.get("section", "Unknown")), row=doc.get("row"),
                    quantity=int(doc.get("qty", 1)), price=Decimal(str(doc.get("current_price", 0))),
                    fees=Decimal(str(doc["fees"])) if doc.get("fees") else None,
                    all_in_price=Decimal(str(doc["all_in_price"])) if doc.get("all_in_price") else None,
                    listing_url=doc.get("listing_url"),
                    market_segment="secondary_resale",
                ))
            except Exception: pass
        return listings

    async def _fetch_via_playwright(self, event_id: str, fallback_url: Optional[str]) -> list[RawListing]:
        self._session_path.mkdir(parents=True, exist_ok=True)
        captured: list[dict] = []
        cdp_url = getattr(self.settings, "cdp_url", None)

        async with async_playwright() as p:
            if cdp_url:
                browser = await p.chromium.connect_over_cdp(cdp_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
            else:
                context = await p.chromium.launch_persistent_context(
                    str(self._session_path), headless=not self.debug_mode,
                    slow_mo=self.slow_mo_ms if self.debug_mode else 0,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                )

            page = await context.new_page()
            self._current_page = page

            async def intercept_response(response):
                if "listingCatalog" in response.url and response.status == 200:
                    try: captured.append(await response.json())
                    except Exception: pass

            page.on("response", intercept_response)
            url = fallback_url or f"https://www.stubhub.com/event/{event_id}"
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            cookies = await context.cookies()
            self._cookies_file.write_text(json.dumps(cookies, indent=2))
            self._current_page = None
            if not cdp_url:
                await context.close()

        listings = []
        for data in captured:
            listings.extend(self._parse_solr_response(data))
        return listings

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            cookies = {}
            if self._cookies_file.exists():
                try: cookies = {c["name"]: c["value"] for c in json.loads(self._cookies_file.read_text())}
                except Exception: pass
            self._http_client = httpx.AsyncClient(
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", "Accept": "application/json", "Referer": "https://www.stubhub.com/"},
                cookies=cookies, follow_redirects=True, timeout=30.0,
            )
        return self._http_client

    def _extract_event_id_from_url(self, url: str) -> Optional[str]:
        m = re.search(r"/event/(\d+)", url)
        if m:
            return m.group(1)
        # also handles stubhub.com/tickets/.../12345 and trailing numeric segment
        m = re.search(r"/(\d{6,})(?:[/?#]|$)", url)
        return m.group(1) if m else None

    def _slug_from_url(self, url: str) -> Optional[str]:
        path = url.rstrip("/").rsplit("/", 1)[-1]
        slug = re.sub(r"-tickets$|-los-angeles$|-la$", "", path, flags=re.IGNORECASE)
        keywords = slug.replace("-", " ").strip()
        return keywords if len(keywords) > 3 else None

    async def _search_event_by_slug(self, keywords: str) -> Optional[str]:
        """Best-effort SOLR keyword search — returns first matching event_id."""
        client = await self._get_http_client()
        search_url = (
            "https://www.stubhub.com/listingCatalog/select"
            f"?q=event_name:*{keywords.replace(' ', '*')}*"
            "&rows=1&fl=event_id&sort=event_date+asc&wt=json"
        )
        try:
            resp = await client.get(search_url)
            if resp.status_code == 200:
                docs = resp.json().get("response", {}).get("docs", [])
                if docs:
                    return str(docs[0]["event_id"])
        except Exception as exc:
            self.logger.debug("StubHub slug search failed: %s", exc)
        return None

    def normalize_section(self, raw_section: str) -> str:
        return re.sub(r"^(Section|Sec\.?)\s*", "", raw_section.strip(), flags=re.IGNORECASE).upper()

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
