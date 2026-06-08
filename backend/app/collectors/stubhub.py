import asyncio
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Optional

import httpx

from app.collectors.base import BaseCollector, RawListing
from app.config import Settings

STUBHUB_SOLR_URL = (
    "https://www.stubhub.com/listingCatalog/select"
    "?q=*:*&fq=event_id:{event_id}&rows=500&start=0"
    "&fl=listing_id,section,row,qty,current_price,all_in_price,fees,listing_url&sort=current_price+asc&wt=json"
)

# Global semaphore: only ONE Playwright instance runs at a time across all
# StubHub collectors.  Chromium under Docker with limited /dev/shm OOM-kills
# when 2+ instances run concurrently (--disable-dev-shm-usage reduces risk but
# does not eliminate it under Railway's memory limits).
_PLAYWRIGHT_SEM: asyncio.Semaphore | None = None


def _get_playwright_sem() -> asyncio.Semaphore:
    global _PLAYWRIGHT_SEM
    if _PLAYWRIGHT_SEM is None:
        _PLAYWRIGHT_SEM = asyncio.Semaphore(1)
    return _PLAYWRIGHT_SEM


class StubHubNoListingPayloadError(Exception):
    """Raised when StubHub Playwright ran but no listing container found in DOM
    (page may have been bot-blocked or redirected).  Caller should preserve
    existing listings rather than overwriting with empty."""


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
            try:
                listings = await self._fetch_via_playwright(event_id, tracked_event.external_url)
            except StubHubNoListingPayloadError as exc:
                # Page loaded but no listing container found — bot-blocked or page error.
                # Return [] so RECONCILE preserves existing active listings rather than
                # overwriting with an empty set.
                self.logger.error(
                    "STUBHUB: %s — preserving existing listings via RECONCILE", exc
                )
                return []

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
        async with _get_playwright_sem():
            return await self._fetch_via_playwright_inner(event_id, fallback_url)

    async def _fetch_via_playwright_inner(self, event_id: str, fallback_url: Optional[str]) -> list[RawListing]:
        self._session_path.mkdir(parents=True, exist_ok=True)
        captured_solr: list[dict] = []

        # Prefer rebrowser-playwright (patches CDP to evade bot detection fingerprinting).
        # Falls back to standard playwright if not installed.
        try:
            from rebrowser_playwright.async_api import async_playwright as _async_playwright
            self.logger.debug("STUBHUB: using rebrowser-playwright")
        except ImportError:
            from playwright.async_api import async_playwright as _async_playwright  # type: ignore
            self.logger.debug("STUBHUB: using standard playwright (rebrowser-playwright not found)")

        cdp_url = getattr(self.settings, "cdp_url", None)

        async with _async_playwright() as p:
            if cdp_url:
                browser = await p.chromium.connect_over_cdp(cdp_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
            else:
                context = await p.chromium.launch_persistent_context(
                    str(self._session_path),
                    headless=True,
                    slow_mo=self.slow_mo_ms if self.debug_mode else 0,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                    ],
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    locale="en-US",
                    timezone_id="America/Los_Angeles",
                    viewport={"width": 1920, "height": 1080},
                    device_scale_factor=1,
                )

            # Inject seed cookies (DataDome + AWS WAF tokens) from PostgreSQL before first nav.
            # Without valid anti-bot cookies, DataDome blocks the React API calls that populate
            # the listings container, resulting in an empty DOM regardless of bot-detection patches.
            seed_cookies = await self._load_seed_cookies()
            if seed_cookies:
                try:
                    await context.add_cookies(seed_cookies)
                    self.logger.info("STUBHUB: injected %d seed cookies into context", len(seed_cookies))
                except Exception as ck_err:
                    self.logger.warning("STUBHUB: seed cookie injection failed: %s", ck_err)
            else:
                self.logger.warning("STUBHUB: no seed cookies found — DataDome may block listings")

            page = await context.new_page()
            self._current_page = page

            # Patch navigator.webdriver and other automation markers that bot detectors check
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            """)

            # Belt-and-suspenders: still intercept listingCatalog if it fires
            async def intercept_response(response):
                if "listingCatalog" in response.url and response.status == 200:
                    try: captured_solr.append(await response.json())
                    except Exception: pass

            page.on("response", intercept_response)

            url = fallback_url or f"https://www.stubhub.com/event/{event_id}"
            self.logger.info("STUBHUB: Playwright navigating to %s", url)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as nav_exc:
                self.logger.warning("STUBHUB: page.goto exception (continuing): %s", nav_exc)
                await asyncio.sleep(3)

            # Wait for the listing container AND at least one listing card inside it.
            # StubHub SSR puts listings directly in the HTML, so [data-listing-id] should
            # appear almost immediately.  If it never appears, DataDome blocked the render.
            container_found = False
            try:
                await page.wait_for_selector('[data-testid="listings-container"]', timeout=20000)
                container_found = True
                self.logger.info("STUBHUB: listings-container found — event_id=%s", event_id)
            except Exception:
                self.logger.warning("STUBHUB: listings-container not found after 20s — event_id=%s", event_id)

            if container_found:
                # Also wait for at least one listing card (confirms SSR data arrived)
                try:
                    await page.wait_for_selector('[data-listing-id]', timeout=10000)
                    self.logger.info("STUBHUB: listing cards present in DOM — event_id=%s", event_id)
                except Exception:
                    self.logger.warning(
                        "STUBHUB: container found but no [data-listing-id] after 10s — "
                        "possible DataDome empty-shell render — event_id=%s", event_id
                    )

            if container_found:
                # Click "Show more" up to 10 times to load more listings (page starts with 10)
                for _ in range(10):
                    try:
                        show_more = await page.query_selector('button:has-text("Show more")')
                        if not show_more:
                            break
                        await show_more.click()
                        await asyncio.sleep(1.5)
                    except Exception:
                        break

            # Save cookies back to PostgreSQL (keeps DataDome/WAF tokens fresh for next run)
            try:
                cookies = await context.cookies()
                self._cookies_file.write_text(json.dumps(cookies, indent=2))
                await self._save_seed_cookies(cookies)
            except Exception:
                pass

            # Extract listings from DOM
            dom_listings: list[RawListing] = []
            if container_found:
                dom_listings = await self._extract_dom_listings(page, event_id)

            self._current_page = None
            if not cdp_url:
                await context.close()

        # Prefer SOLR data if captured (more fields), else use DOM extraction
        if captured_solr:
            self.logger.info("STUBHUB: captured %d SOLR response(s) — parsing", len(captured_solr))
            result = []
            for data in captured_solr:
                result.extend(self._parse_solr_response(data))
            return result

        if dom_listings:
            self.logger.info("STUBHUB: DOM extraction returned %d listings for event_id=%s", len(dom_listings), event_id)
            return dom_listings

        if not container_found:
            # Page did not render the listing container — likely bot-blocked or page error
            raise StubHubNoListingPayloadError(
                f"stubhub_no_listing_payload event_id={event_id} url={url}"
            )

        # Container was found but empty — event may genuinely have 0 listings
        self.logger.warning("STUBHUB: listings-container found but empty for event_id=%s", event_id)
        return []

    # ------------------------------------------------------------------ #
    #  Seed cookie persistence (DataDome / AWS WAF bypass)                #
    # ------------------------------------------------------------------ #

    async def _load_seed_cookies(self) -> list[dict]:
        """Load previously stored anti-bot cookies from PostgreSQL.
        Stored by _save_seed_cookies after each successful Playwright run, and
        bootstrapped manually via the failure_memory row (error_type='session_cookies').
        """
        factory = getattr(self, "_db_session_factory", None)
        if factory is None:
            return []
        try:
            from sqlalchemy import text
            async with factory() as db:
                result = await db.execute(text(
                    "SELECT notes FROM failure_memory "
                    "WHERE marketplace='stubhub' AND error_type='session_cookies' "
                    "AND failed_pattern='playwright_seed' LIMIT 1"
                ))
                row = result.fetchone()
                if row and row[0]:
                    return json.loads(row[0])
        except Exception as e:
            self.logger.warning("STUBHUB: _load_seed_cookies failed: %s", e)
        return []

    async def _save_seed_cookies(self, cookies: list[dict]) -> None:
        """Persist fresh Playwright cookies back to PostgreSQL after a successful run.
        Only retains the anti-bot critical cookies (DataDome, AWS WAF, StubHub session).
        """
        factory = getattr(self, "_db_session_factory", None)
        if factory is None:
            return
        KEEP = {"d", "datadome", "aws-waf-token", "s", "wsso-session", "wsso", "ctattr", "uis"}
        critical = [c for c in cookies if c.get("name") in KEEP]
        if not critical:
            return
        try:
            from sqlalchemy import text
            cookies_json = json.dumps(critical)
            async with factory() as db:
                await db.execute(text(
                    "UPDATE failure_memory SET notes=:notes, last_seen=NOW() "
                    "WHERE marketplace='stubhub' AND error_type='session_cookies' "
                    "AND failed_pattern='playwright_seed'"
                ), {"notes": cookies_json})
                await db.commit()
            self.logger.info("STUBHUB: saved %d seed cookies to PostgreSQL", len(critical))
        except Exception as e:
            self.logger.warning("STUBHUB: _save_seed_cookies failed: %s", e)

    # ------------------------------------------------------------------ #
    #  DOM listing extraction                                              #
    # ------------------------------------------------------------------ #

    async def _extract_dom_listings(self, page, event_id: str) -> list[RawListing]:
        """Extract listing cards from StubHub's SSR DOM.

        StubHub renders listings server-side inside [data-testid="listings-container"].
        Each card exposes data-listing-id, data-price, data-is-sold as data attributes
        on nested elements.  The innerText contains section/row/quantity in plain text.
        No API call is made — the data is already in the initial HTML.
        """
        try:
            raw_cards = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-testid="listings-container"]');
                if (!container) return null;
                const cards = Array.from(container.children);
                return cards.map(el => {
                    // listing_id, price, is_sold are nested data attributes
                    let listing_id = null, price_raw = null, is_sold = '0';
                    for (const c of el.querySelectorAll('*')) {
                        if (!listing_id) listing_id = c.getAttribute('data-listing-id');
                        if (!price_raw)  price_raw  = c.getAttribute('data-price');
                        const sold = c.getAttribute('data-is-sold');
                        if (sold !== null) { is_sold = sold; break; }
                    }
                    return { listing_id, price_raw, is_sold, text: el.innerText || '' };
                }).filter(r => r.listing_id && r.price_raw);
            }
            """)
        except Exception as exc:
            self.logger.warning("STUBHUB: DOM evaluate failed: %s", exc)
            return []

        if not raw_cards:
            return []

        return self._parse_dom_cards(raw_cards, event_id)

    def _parse_dom_cards(self, cards: list[dict], event_id: str) -> list[RawListing]:
        """Parse raw DOM card data into RawListing objects."""
        listings = []
        for card in cards:
            try:
                # Skip sold listings
                if card.get("is_sold") == "1":
                    continue

                listing_id = card["listing_id"]
                price_str = card["price_raw"].replace("$", "").replace(",", "").strip()
                price = Decimal(price_str)

                # Parse section, row, quantity from innerText
                # Example: "Section 213\nRow 20\nSeats 9 - 10\n2 tickets together\nClear view\n$916\nincl. fees"
                lines = [ln.strip() for ln in card.get("text", "").split("\n") if ln.strip()]

                section = "Unknown"
                row: Optional[str] = None
                quantity = 2  # StubHub default filter is 2 tickets

                for line in lines:
                    low = line.lower()
                    if low.startswith("section ") and section == "Unknown":
                        section = line[len("section "):].strip()
                    elif low.startswith("row ") and "row row" not in low and row is None:
                        # "Row 20" or "Row 20 | Seats 9 - 10" → strip seats
                        row_raw = line[len("row "):].strip()
                        row = row_raw.split("|")[0].strip()
                    elif "ticket" in low:
                        m = re.match(r"^(\d+)\s+ticket", low)
                        if m:
                            quantity = int(m.group(1))

                listing_url = f"https://www.stubhub.com/event/{event_id}/?listingId={listing_id}"

                listings.append(RawListing(
                    external_listing_id=f"sh-{listing_id}",
                    section=self.normalize_section(section),
                    row=row,
                    quantity=quantity,
                    price=price,
                    fees=None,
                    all_in_price=price,  # StubHub displays all-in prices
                    listing_url=listing_url,
                    market_segment="secondary_resale",
                ))
            except Exception:
                pass
        return listings

    # ------------------------------------------------------------------ #
    #  HTTP client / helpers                                               #
    # ------------------------------------------------------------------ #

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
