#!/usr/bin/env python3
"""
Host-side StubHub collector script.

WHY THIS EXISTS
===============
StubHub migrated to Viagogo infrastructure.  The old listingCatalog/select
Solr endpoint returns HTTP 404.  The new Viagogo-powered SPA server-side
renders listing cards in the initial HTML — there is NO separate listing XHR
to intercept.  Instead, listing data is embedded in data-* attributes on each
card DIV in the DOM.

DATA SOURCE
===========
Each listing is a DOM element with:
  data-listing-id="12652822205"   → external_listing_id ("sh-" prefix)
  data-price="$191"               → all-in per-ticket price
  data-is-sold="0"                → skip if "1"

Text content structure (newline-separated):
  Section 209        → section
  Row 27             → row
  2 tickets together → quantity
  Clear view         → badge (ignored)
  Best price         → badge (ignored)
  Hidden gem         → badge (ignored)
  Only 2 left        → badge (ignored)
  $288               → "was" price (optional)
  Now                → discount marker (optional)
  $191               → current all-in price (= data-price)
  incl. fees         → price label
  9.5                → score (ignored)
  Amazing            → label (ignored)

PAGINATION
==========
The page initially renders 10 listings.  A "Show more" button loads 10 more
per click.  The script clicks it in a loop until the button disappears.

BOT DETECTION
=============
StubHub uses CrowdControl (DataDome variant) + AWS WAF.  Standard Playwright
is fingerprinted and may be blocked.  rebrowser-playwright patches CDP to pass
these checks.  A persistent browser profile at ~/.concert-tracker/stubhub/
accumulates session cookies across runs.

CADENCE SELF-THROTTLING
=======================
Without --te-id, the script queries the backend for ALL active StubHub tracked
events and runs a cadence check per event.  Events not yet due are skipped.

With --te-id, cadence is bypassed (always provide --event-url).

USAGE
=====
  # Auto-mode (launchd default)
  python3 scripts/collect_stubhub.py

  # Specific event
  python3 scripts/collect_stubhub.py --te-id 22 \\
    --event-url "https://www.stubhub.com/rush-inglewood-tickets-6-7-2026/event/159558659/"

  # Headed mode (use if headless is blocked after a long gap)
  python3 scripts/collect_stubhub.py --headed --dry-run --te-id 22 \\
    --event-url "https://www.stubhub.com/rush-inglewood-tickets-6-7-2026/event/159558659/"

  # Force + dry-run to test
  python3 scripts/collect_stubhub.py --force --dry-run

  # Custom backend
  python3 scripts/collect_stubhub.py --backend http://localhost:8000

REQUIREMENTS
============
  pip install rebrowser-playwright httpx
  rebrowser-playwright install chromium

Uses the persistent browser profile at ~/.concert-tracker/stubhub/ so that
DataDome / AWS WAF cookies persist across headless runs.
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import httpx

try:
    from rebrowser_playwright.async_api import async_playwright
except ImportError:
    from playwright.async_api import async_playwright  # type: ignore

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULT_BACKEND_URL = "https://backend-production-509f.up.railway.app"
MARKETPLACE_SLUG    = "stubhub"

# Last-run timestamp files — per-event keyed by te_id
_LAST_RUN_DIR = Path.home() / ".concert-tracker"
_LAST_RUN_DIR.mkdir(parents=True, exist_ok=True)


def _last_run_file(te_id: int) -> Path:
    return _LAST_RUN_DIR / f"stubhub_last_run_te{te_id}.txt"


# ── Cadence tier (mirrors scheduler.compute_poll_interval_minutes) ────────────

def _compute_interval_minutes(event_date_iso: str) -> int:
    """Return cadence tier interval in minutes for the given event_date (ISO string)."""
    try:
        ed = datetime.fromisoformat(event_date_iso.replace("Z", "+00:00"))
        if ed.tzinfo is None:
            ed = ed.replace(tzinfo=timezone.utc)
    except Exception:
        return 1440  # safe default if date unparseable
    now = datetime.now(timezone.utc)
    seconds = (ed - now).total_seconds()
    if seconds > 30 * 24 * 3600: return 1440
    if seconds > 14 * 24 * 3600: return 360
    if seconds >  7 * 24 * 3600: return 240
    if seconds >  2 * 24 * 3600: return 60
    if seconds >      24 * 3600: return 30
    if seconds >       6 * 3600: return 15
    if seconds >       2 * 3600: return 5
    if seconds >              0: return 2
    if seconds >    -30 * 60:    return 2    # monitoring: first 30m post-event
    if seconds >    -60 * 60:    return 5    # monitoring: 30m–60m post-event
    return 5                                 # default for events well past end


def _check_cadence_due(te_id: int, event_date_iso: str, verbose: bool = True) -> bool:
    """Return True if enough time has elapsed since last run per the cadence tier."""
    interval_min = _compute_interval_minutes(event_date_iso)
    lrf = _last_run_file(te_id)
    if not lrf.exists():
        if verbose:
            print(f"[stubhub] te={te_id}: cadence: first run — interval {interval_min}m — proceeding")
        return True
    try:
        last_run_str = lrf.read_text().strip()
        last_run = datetime.fromisoformat(last_run_str)
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)
        elapsed_min = (datetime.now(timezone.utc) - last_run).total_seconds() / 60
        if elapsed_min < interval_min:
            remaining = int(interval_min - elapsed_min)
            if verbose:
                print(
                    f"[stubhub] te={te_id}: cadence: last run {elapsed_min:.0f}m ago, "
                    f"interval {interval_min}m — skipping (next in ~{remaining}m)"
                )
            return False
        if verbose:
            print(
                f"[stubhub] te={te_id}: cadence: {elapsed_min:.0f}m since last run, "
                f"interval {interval_min}m — proceeding"
            )
        return True
    except Exception as exc:
        if verbose:
            print(f"[stubhub] te={te_id}: cadence: could not read last-run file ({exc}) — proceeding")
        return True


def _mark_run_complete(te_id: int) -> None:
    """Record the current UTC timestamp as the last successful run for this te_id."""
    lrf = _last_run_file(te_id)
    lrf.parent.mkdir(parents=True, exist_ok=True)
    lrf.write_text(datetime.now(timezone.utc).isoformat())


# ── Browser / session settings ────────────────────────────────────────────────

# Persistent browser profile — DataDome + AWS WAF cookies persist across runs
_SESSION_DIR = Path.home() / ".concert-tracker" / "stubhub"

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_FETCH_TIMEOUT_SECS  = 180   # overall timeout per event
_PAGE_LOAD_WAIT_SECS = 8     # initial wait after domcontentloaded for SSR render
_SHOW_MORE_WAIT_SECS = 3     # wait after each "Show more" click
_MAX_SHOW_MORE_CLICKS = 50   # safety cap (50 × 10 = 500 listings max)


# ── DOM extraction JS ─────────────────────────────────────────────────────────

_EXTRACT_LISTINGS_JS = """
() => {
    // Each listing card has data-listing-id, data-price, data-is-sold attributes
    const cards = [...document.querySelectorAll('[data-listing-id]')];

    const listings = [];
    for (const card of cards) {
        const listingId = card.getAttribute('data-listing-id');
        const isSold    = card.getAttribute('data-is-sold');
        const priceStr  = card.getAttribute('data-price');

        // Skip sold listings
        if (isSold === '1') continue;
        if (!listingId || !priceStr) continue;

        // Parse all-in price from data-price attribute ("$191" → 191.0)
        const priceMatch = priceStr.replace(/[$,]/g, '');
        const allInPrice = parseFloat(priceMatch);
        if (isNaN(allInPrice) || allInPrice <= 0) continue;

        // Parse text content lines
        const lines = (card.innerText || '').split('\\n')
            .map(l => l.trim()).filter(l => l.length > 0);

        // Extract section (first line containing "Section", "Floor", "GA", "Field", "Pit", etc.)
        let section = 'Unknown';
        let row = null;
        let quantity = 1;
        let basePrice = null;  // "was" price before discount (if present)

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            if (section === 'Unknown' && (
                line.startsWith('Section ') || line === 'Floor' ||
                line === 'GA' || line === 'General Admission' ||
                line.startsWith('Field') || line.startsWith('Pit') ||
                line.startsWith('Box ') || line.startsWith('Suite ')
            )) {
                section = line;
                continue;
            }

            if (row === null && line.startsWith('Row ')) {
                row = line.replace('Row ', '').trim();
                continue;
            }

            // Quantity: "N tickets together" or "N ticket(s)"
            const qtyMatch = line.match(/^(\\d+)\\s+ticket/i);
            if (qtyMatch) {
                quantity = parseInt(qtyMatch[1], 10);
                continue;
            }

            // "Was" price: dollar amount NOT preceded by "Now" context
            // If we see a dollar line followed by "Now" → it's the old price
            if (line.match(/^\\$[\\d,]+$/) && i + 1 < lines.length && lines[i+1] === 'Now') {
                const wasVal = parseFloat(line.replace(/[$,]/g, ''));
                if (!isNaN(wasVal) && wasVal > 0) {
                    basePrice = wasVal;
                }
            }
        }

        // Listing URL: try to find <a> wrapping the card or nearest <a>
        const linkEl = card.closest('a') || card.querySelector('a');
        const listingUrl = linkEl ? linkEl.href : null;

        listings.push({
            listingId,
            section,
            row,
            quantity,
            allInPrice,
            basePrice,   // null if no discount shown
            listingUrl,
        });
    }

    return listings;
}
"""

_COUNT_SHOW_MORE_JS = """
() => {
    const btn = [...document.querySelectorAll('button')]
        .find(b => (b.innerText || '').trim() === 'Show more');
    return btn ? true : false;
}
"""

_CLICK_SHOW_MORE_JS = """
() => {
    // Use JS click to bypass overlay pointer-event interception
    const btn = [...document.querySelectorAll('button')]
        .find(b => (b.innerText || '').trim() === 'Show more');
    if (btn) { btn.click(); return true; }
    return false;
}
"""

_DISMISS_MODAL_JS = """
() => {
    // Remove modal-root overlays that intercept pointer events
    const modalRoot = document.getElementById('modal-root');
    if (modalRoot) {
        modalRoot.style.pointerEvents = 'none';
        modalRoot.style.display = 'none';
        return 'dismissed modal-root';
    }
    return 'no modal-root found';
}
"""


# ── Browser fetch ─────────────────────────────────────────────────────────────

async def fetch_stubhub_listings(
    event_url: str,
    headed: bool = False,
    verbose: bool = True,
) -> Tuple[list, int]:
    """
    Navigate the StubHub event page (Viagogo SPA), wait for SSR render,
    then click "Show more" until all listings are extracted from the DOM.

    Returns:
        (raw_listings_list, total_clicked_show_more)

    Each raw listing dict has keys:
        listingId, section, row, quantity, allInPrice, basePrice, listingUrl
    """
    _SESSION_DIR.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"[stubhub] browser profile: {_SESSION_DIR}")
        print(f"[stubhub] navigating → {event_url}")
        print(f"[stubhub] headed={headed}")

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(_SESSION_DIR),
            headless=not headed,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
            user_agent=_BROWSER_UA,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = await ctx.new_page()

        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as exc:
            print(f"[stubhub] WARN: goto error (may be non-fatal): {exc}", file=sys.stderr)

        if verbose:
            print(f"[stubhub] page loaded, waiting {_PAGE_LOAD_WAIT_SECS}s for Viagogo SSR render…")

        if headed:
            print(
                f"[stubhub] HEADED MODE — browser window is open. "
                f"Interact if needed (e.g. accept cookies), then wait.",
                file=sys.stderr,
            )

        await asyncio.sleep(_PAGE_LOAD_WAIT_SECS)

        # Suppress modal overlay that intercepts pointer events
        modal_result = await page.evaluate(_DISMISS_MODAL_JS)
        if verbose:
            print(f"[stubhub] modal dismiss: {modal_result}")

        # Also try Playwright-level dismiss for interactive modals
        await _dismiss_modals(page, verbose=verbose)

        # Click "Show more" via JS (bypasses overlay pointer-event interception)
        clicks = 0
        for _ in range(_MAX_SHOW_MORE_CLICKS):
            has_more = await page.evaluate(_COUNT_SHOW_MORE_JS)
            if not has_more:
                break
            try:
                clicked = await page.evaluate(_CLICK_SHOW_MORE_JS)
                if not clicked:
                    break
                clicks += 1
                await asyncio.sleep(_SHOW_MORE_WAIT_SECS)
                if verbose:
                    count_so_far = await page.evaluate(
                        "() => document.querySelectorAll('[data-listing-id]').length"
                    )
                    print(f"[stubhub] 'Show more' click #{clicks} — {count_so_far} listings loaded")
            except Exception as exc:
                if verbose:
                    print(f"[stubhub] WARN: 'Show more' click failed: {exc}", file=sys.stderr)
                break

        # Extract all listing cards
        raw_listings = await page.evaluate(_EXTRACT_LISTINGS_JS)

        try:
            await ctx.close()
        except Exception:
            pass

    return raw_listings, clicks


async def _dismiss_modals(page, verbose: bool = False) -> None:
    """Click common modal dismiss buttons if present."""
    dismiss_selectors = [
        # Cookie consent
        "button:text('Accept All')",
        "button:text('Accept all')",
        "button:text('Accept cookies')",
        "button:text('Accept')",
        # Sign-in prompt close button
        "button[aria-label='Close']",
        "[data-testid='modal-close-button']",
        "[data-testid='close-button']",
    ]
    for sel in dismiss_selectors:
        try:
            await page.click(sel, timeout=1_500)
            if verbose:
                print(f"[stubhub] dismissed modal: {sel!r}")
            await asyncio.sleep(0.5)
        except Exception:
            pass


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_listings(raw_listings: list) -> Tuple[list, dict]:
    """
    Convert raw DOM listings to ManualIngestRequest wire format.

    Field mapping:
        listingId    → external_listing_id  ("sh-" prefix)
        section      → section
        row          → row
        quantity     → quantity
        allInPrice   → all_in_price  (per-ticket, data-price attribute)
        basePrice    → price         (per-ticket "was" price; fallback = allInPrice)
        listingUrl   → listing_url
        (hardcoded)  → market_segment = "secondary_resale"
    """
    listings = []
    seen: set[str] = set()
    skipped_no_id      = 0
    skipped_zero_price = 0
    skipped_dup        = 0

    for item in raw_listings:
        raw_id = item.get("listingId")
        if not raw_id:
            skipped_no_id += 1
            continue

        external_listing_id = f"sh-{raw_id}"
        if external_listing_id in seen:
            skipped_dup += 1
            continue
        seen.add(external_listing_id)

        all_in = float(item.get("allInPrice") or 0)
        if all_in <= 0:
            skipped_zero_price += 1
            continue

        # Base price: use "was" price if present, otherwise same as all-in
        base_price_raw = item.get("basePrice")
        price = float(base_price_raw) if base_price_raw else all_in

        listings.append({
            "external_listing_id": external_listing_id,
            "section":             str(item.get("section") or "Unknown"),
            "row":                 item.get("row") or None,
            "quantity":            int(item.get("quantity") or 1),
            "price":               price,
            "fees":                None,        # not reliably available from DOM
            "all_in_price":        all_in,
            "listing_url":         item.get("listingUrl") or None,
            "market_segment":      "secondary_resale",
        })

    return listings, {
        "total_raw":           len(raw_listings),
        "skipped_no_id":       skipped_no_id,
        "skipped_zero_price":  skipped_zero_price,
        "skipped_dup":         skipped_dup,
    }


# ── Backend ingest ────────────────────────────────────────────────────────────

def post_to_backend(
    backend_url: str,
    te_id: int,
    marketplace_slug: str,
    listings: list[dict],
    fetched_at: str,
) -> dict:
    url = f"{backend_url.rstrip('/')}/api/poll/tracked/{te_id}/manual-ingest"
    payload = {
        "tracked_event_id": te_id,
        "marketplace_slug": marketplace_slug,
        "listings":         listings,
        "fetched_at":       fetched_at,
    }
    resp = httpx.post(url, json=payload, timeout=120.0)
    resp.raise_for_status()
    return resp.json()


# ── Active event discovery ────────────────────────────────────────────────────

def fetch_active_stubhub_events(backend_url: str) -> list[dict]:
    """Query the backend for all active StubHub tracked events with a URL.

    Returns list of dicts: te_id, external_url, event_date, title
    """
    try:
        resp = httpx.get(
            f"{backend_url.rstrip('/')}/api/events/",
            params={"include_completed": "false"},
            timeout=15.0,
        )
        resp.raise_for_status()
        events = resp.json()
        if not isinstance(events, list):
            events = []
    except Exception as exc:
        print(f"[stubhub] ERROR: cannot fetch events from backend: {exc}", file=sys.stderr)
        return []

    active = []
    for ev in events:
        for te in (ev.get("tracked_events") or []):
            if (
                te.get("marketplace_slug") == "stubhub"
                and te.get("is_active")
                and te.get("external_url")
            ):
                active.append({
                    "te_id":        te["id"],
                    "external_url": te["external_url"],
                    "event_date":   ev.get("event_date", ""),
                    "title":        ev.get("title", ""),
                })
    return active


# ── Single event run ──────────────────────────────────────────────────────────

async def run_one_event(
    te_id: int,
    event_url: str,
    backend_url: str,
    save_raw_dir: str,
    dry_run: bool,
    headed: bool,
    verbose: bool,
) -> bool:
    """Fetch, parse, and ingest listings for one StubHub tracked event.

    Returns True on success, False on failure.
    """
    fetched_at = datetime.now(timezone.utc).isoformat()

    if verbose:
        print(f"[stubhub] te={te_id}: url={event_url}")

    # Step 1: Fetch (DOM extraction)
    try:
        raw_listings, show_more_clicks = await asyncio.wait_for(
            fetch_stubhub_listings(event_url, headed=headed, verbose=verbose),
            timeout=_FETCH_TIMEOUT_SECS,
        )
    except asyncio.TimeoutError:
        print(f"[stubhub] te={te_id}: ERROR: fetch timed out after {_FETCH_TIMEOUT_SECS}s", file=sys.stderr)
        return False

    if verbose:
        print(
            f"[stubhub] te={te_id}: DOM extracted {len(raw_listings)} listing cards "
            f"(Show-more clicks: {show_more_clicks})"
        )

    if not raw_listings:
        print(
            f"[stubhub] te={te_id}: ERROR: 0 listing cards found in DOM.\n"
            f"  Possible causes:\n"
            f"  • Bot detection still active (try --headed to bootstrap session)\n"
            f"  • Event page structure changed\n"
            f"  • Event has no available listings",
            file=sys.stderr,
        )
        return False

    # Step 2: Parse
    listings, skip_stats = parse_listings(raw_listings)
    if verbose:
        print(
            f"[stubhub] te={te_id}: parsed: {len(listings)} valid listings "
            f"(raw={skip_stats['total_raw']}, "
            f"skipped: zero_price={skip_stats['skipped_zero_price']}, "
            f"dup={skip_stats['skipped_dup']}, no_id={skip_stats['skipped_no_id']})"
        )

    if not listings:
        print(f"[stubhub] te={te_id}: ERROR: 0 valid listings after parsing", file=sys.stderr)
        return False

    prices = [l["all_in_price"] for l in listings]
    if verbose:
        print(
            f"[stubhub] te={te_id}: all-in price range: ${min(prices):.2f} – ${max(prices):.2f}  "
            f"avg: ${sum(prices)/len(prices):.2f}"
        )

    # Step 2b: Save raw payload
    raw_body = json.dumps(raw_listings).encode()
    raw_path: Optional[str] = None
    if raw_body:
        ts_compact = fetched_at.replace(":", "").replace("+", "").replace("-", "")[:15]
        raw_path = os.path.join(
            save_raw_dir,
            f"stubhub_raw_te{te_id}_{ts_compact}.json",
        )
        try:
            with open(raw_path, "wb") as fh:
                fh.write(raw_body)
            if verbose:
                print(f"[stubhub] te={te_id}: raw payload saved → {raw_path} ({len(raw_body):,} bytes)")
        except Exception as exc:
            print(f"[stubhub] te={te_id}: WARN: could not save raw payload: {exc}", file=sys.stderr)
            raw_path = "(save failed)"

    if dry_run:
        print(f"\n[stubhub] DRY RUN te={te_id} — {len(listings)} listings parsed, NOT posted to backend")
        print(f"  would POST to: {backend_url}/api/poll/tracked/{te_id}/manual-ingest")
        print("\nSample listings (first 5):")
        for l in listings[:5]:
            print(
                f"  id={l['external_listing_id']}  sec={l['section']!r}  "
                f"row={l['row']!r}  qty={l['quantity']}  "
                f"all_in=${l['all_in_price']:.2f}  "
                f"segment={l['market_segment']}"
            )
        return True

    # Step 3: Ingest
    if verbose:
        print(f"[stubhub] te={te_id}: posting {len(listings)} listings → {backend_url}…")
    try:
        result = post_to_backend(
            backend_url=backend_url,
            te_id=te_id,
            marketplace_slug=MARKETPLACE_SLUG,
            listings=listings,
            fetched_at=fetched_at,
        )
    except httpx.HTTPStatusError as exc:
        print(
            f"[stubhub] te={te_id}: ERROR: backend returned {exc.response.status_code}: "
            f"{exc.response.text[:300]}",
            file=sys.stderr,
        )
        return False
    except httpx.ConnectError:
        print(
            f"[stubhub] te={te_id}: ERROR: cannot connect to backend at {backend_url}",
            file=sys.stderr,
        )
        return False

    poll_run_id = result.get("poll_run_id")

    # Rename raw file to include poll_run_id
    if poll_run_id and raw_path and raw_path != "(save failed)" and os.path.exists(raw_path):
        final_path = raw_path.replace(".json", f"_run{poll_run_id}.json")
        try:
            os.rename(raw_path, final_path)
            raw_path = final_path
        except Exception:
            pass

    print("\n" + "=" * 60)
    print(f"StubHub ingest complete — te={te_id}")
    print("=" * 60)
    print(f"  status            : {result.get('status')}")
    print(f"  poll_run_id       : {poll_run_id}")
    print(f"  listings_found    : {result.get('listings_found')}")
    print(f"  new_listings      : {result.get('new_listings')}")
    print(f"  reactivated       : {result.get('reactivated_listings')}")
    print(f"  disappeared       : {result.get('disappeared_listings')}")
    print(f"  raw_payload       : {raw_path}")
    print(f"  last_run_file     : {_last_run_file(te_id)}")
    print("=" * 60)
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(
        description="Host-side StubHub collector — extracts DOM listings, ingests via backend API",
    )
    parser.add_argument(
        "--te-id",
        type=int,
        default=None,
        help="tracked_event_id to ingest into (default: auto-discover all active StubHub events)",
    )
    parser.add_argument(
        "--event-url",
        default=None,
        help="Full StubHub event page URL (required when --te-id is specified)",
    )
    parser.add_argument(
        "--backend",
        default=DEFAULT_BACKEND_URL,
        help=f"Backend base URL (default: {DEFAULT_BACKEND_URL})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run regardless of cadence (bypass interval check)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Capture and parse listings but do NOT post to backend",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help=(
            "Run browser in headed (visible) mode — use if bot detection has aged out "
            "the persistent session cookies"
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--save-raw",
        metavar="DIR",
        default=None,
        help="Directory to save raw JSON payload (default: /tmp)",
    )
    args = parser.parse_args()
    args.save_raw = args.save_raw or "/tmp"
    verbose = not args.quiet

    # ── Manual single-event mode ──────────────────────────────────────────────
    if args.te_id is not None:
        if not args.event_url:
            print(
                "[stubhub] ERROR: --te-id requires --event-url",
                file=sys.stderr,
            )
            sys.exit(1)
        ok = await run_one_event(
            te_id=args.te_id,
            event_url=args.event_url,
            backend_url=args.backend,
            save_raw_dir=args.save_raw,
            dry_run=args.dry_run,
            headed=args.headed,
            verbose=verbose,
        )
        if ok and not args.dry_run:
            _mark_run_complete(args.te_id)
        sys.exit(0 if ok else 1)

    # ── Auto-mode: discover all active StubHub events from backend ────────────
    active_events = fetch_active_stubhub_events(args.backend)
    if not active_events:
        print("[stubhub] no active StubHub tracked events with a URL — nothing to do")
        sys.exit(0)

    if verbose:
        print(f"[stubhub] auto-mode: found {len(active_events)} active StubHub event(s)")

    ran_any = False
    for ev in active_events:
        te_id      = ev["te_id"]
        event_url  = ev["external_url"]
        event_date = ev["event_date"]
        title      = ev["title"]

        if verbose:
            print(f"\n[stubhub] checking te={te_id}: {title}")

        if not args.force and not _check_cadence_due(te_id, event_date, verbose=verbose):
            continue

        ok = await run_one_event(
            te_id=te_id,
            event_url=event_url,
            backend_url=args.backend,
            save_raw_dir=args.save_raw,
            dry_run=args.dry_run,
            headed=args.headed,
            verbose=verbose,
        )
        if ok and not args.dry_run:
            _mark_run_complete(te_id)
        ran_any = True

    if not ran_any:
        print("[stubhub] all events within cadence — skipping")


if __name__ == "__main__":
    asyncio.run(main())
