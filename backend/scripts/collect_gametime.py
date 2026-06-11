#!/usr/bin/env python3
"""
Host-side Gametime collector script.

WHY THIS EXISTS
===============
Gametime uses Cloudflare WAF on gametime.co.  The Docker container IP is
blocked for browser fingerprinting checks.  The host Mac's residential IP
passes Cloudflare permissively.

No DataDome — rebrowser-playwright is NOT required.  Standard Playwright with
a real browser UA and a persistent profile (for cf_clearance cookie) works.

DATA SOURCE
===========
Gametime is a Vite React SPA.  It does NOT fire a v1/listings XHR on page load.
Instead, the full listing inventory is embedded in window.__data at page boot.
Specifically: window.__data.redux.listings.listings (array of ~200-400 listings).

Prices are in cents (divide by 100 for USD).
Section numbers are already bare integers (e.g. "542") — no normalization needed.

CADENCE SELF-THROTTLING
=======================
When run WITHOUT --te-id/--event-id/--event-url overrides, the script queries the
backend for ALL active Gametime tracked events and runs a cadence check per event:
the interval tier is computed from each event's event_date and compared against
the last recorded run time.  Events not yet due are skipped.

When run WITH explicit --te-id, the corresponding --event-id and --event-url are
required; cadence is bypassed (use --force to override when running via launchd).

USAGE
=====
  # Auto-mode: runs all active Gametime events that are cadence-due (launchd default)
  python3 scripts/collect_gametime.py

  # Specific tracked_event_id (bypasses cadence check)
  python3 scripts/collect_gametime.py --te-id 46 \\
    --event-id 697938ec70cc8b989bc38369 \\
    --event-url "https://gametime.co/nfl-football/..."

  # Force run regardless of cadence
  python3 scripts/collect_gametime.py --force

  # Dry run — capture and parse listings without posting to backend
  python3 scripts/collect_gametime.py --dry-run

  # Custom backend URL
  python3 scripts/collect_gametime.py --backend http://localhost:8000

REQUIREMENTS
============
  pip install playwright httpx
  playwright install chromium

Uses the persistent browser profile at ~/.concert-tracker/gametime/ so that
the cf_clearance Cloudflare cookie accumulates across runs and warms up.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import httpx
from playwright.async_api import async_playwright

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULT_BACKEND_URL = "https://backend-production-509f.up.railway.app"
MARKETPLACE_SLUG    = "gametime"

# Last-run timestamp files — per-event keyed by te_id (mirrors TickPick cadence pattern)
_LAST_RUN_DIR = Path.home() / ".concert-tracker"
_LAST_RUN_DIR.mkdir(parents=True, exist_ok=True)


def _last_run_file(te_id: int) -> Path:
    return _LAST_RUN_DIR / f"gametime_last_run_te{te_id}.txt"


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
    """Return True if enough time has elapsed since last run per the cadence tier.

    Reads ~/.concert-tracker/gametime_last_run_te{te_id}.txt (ISO timestamp).
    Returns True if the file doesn't exist (first run) or if the elapsed
    time meets or exceeds the current tier interval.
    """
    interval_min = _compute_interval_minutes(event_date_iso)
    lrf = _last_run_file(te_id)
    if not lrf.exists():
        if verbose:
            print(f"[gametime] te={te_id}: cadence: first run — interval {interval_min}m — proceeding")
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
                    f"[gametime] te={te_id}: cadence: last run {elapsed_min:.0f}m ago, "
                    f"interval {interval_min}m — skipping (next in ~{remaining}m)"
                )
            return False
        if verbose:
            print(
                f"[gametime] te={te_id}: cadence: {elapsed_min:.0f}m since last run, "
                f"interval {interval_min}m — proceeding"
            )
        return True
    except Exception as exc:
        if verbose:
            print(f"[gametime] te={te_id}: cadence: could not read last-run file ({exc}) — proceeding")
        return True


def _mark_run_complete(te_id: int) -> None:
    """Record the current UTC timestamp as the last successful run for this te_id."""
    lrf = _last_run_file(te_id)
    lrf.parent.mkdir(parents=True, exist_ok=True)
    lrf.write_text(datetime.now(timezone.utc).isoformat())


# ── Browser / SPA settings ────────────────────────────────────────────────────

# Persistent browser profile — reuses cf_clearance cookie across runs
_SESSION_DIR = Path.home() / ".concert-tracker" / "gametime"

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_FETCH_TIMEOUT_SECS = 120
_PAGE_WAIT_SECS     = 12   # wait for Vite SPA to hydrate and embed window.__data


# ── Browser fetch ─────────────────────────────────────────────────────────────

async def fetch_gametime_listings(
    event_url: str,
    event_id: str,
    verbose: bool = True,
) -> Tuple[list, Optional[bytes]]:
    """
    Navigate the Gametime event page, wait for the Vite SPA to hydrate,
    then read listing data from window.__data.redux.listings.listings.

    Gametime does NOT fire a v1/listings XHR on page load.  All listing
    inventory is embedded in window.__data at boot time.  Prices are in cents.

    Returns:
        (raw_items, raw_body_bytes)
    """
    _SESSION_DIR.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"[gametime] browser profile: {_SESSION_DIR}")
        print(f"[gametime] navigating → {event_url}")

    raw_items: list = []
    raw_body: Optional[bytes] = None

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(_SESSION_DIR),
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
            user_agent=_BROWSER_UA,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = await context.new_page()

        # Track Cloudflare status codes for diagnostics
        cf_blocked = False

        async def on_response(response):
            nonlocal cf_blocked
            if response.status in (403, 429, 503) and "gametime" in response.url:
                cf_blocked = True

        page.on("response", on_response)

        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as exc:
            print(f"[gametime] WARN: goto error (may be non-fatal): {exc}", file=sys.stderr)

        if verbose:
            print(f"[gametime] page loaded, waiting {_PAGE_WAIT_SECS}s for SPA hydration…")
        await asyncio.sleep(_PAGE_WAIT_SECS)

        if cf_blocked:
            print(
                "[gametime] ERROR: Cloudflare blocked — got 403/429/503.\n"
                "Run once in headed mode to solve the challenge: --headed\n"
                "Then re-run headless after cf_clearance cookie is set.",
                file=sys.stderr,
            )

        # Read window.__data.redux.listings.listings
        if verbose:
            print("[gametime] reading window.__data.redux.listings.listings…")

        try:
            result = await page.evaluate("""
                () => {
                    try {
                        const listings = window.__data &&
                                         window.__data.redux &&
                                         window.__data.redux.listings &&
                                         window.__data.redux.listings.listings;
                        if (listings && Array.isArray(listings)) {
                            return { ok: true, listings: listings };
                        }
                        // Fallback: return top-level keys for diagnostics
                        return {
                            ok: false,
                            topKeys: window.__data ? Object.keys(window.__data) : null,
                            reduxKeys: (window.__data && window.__data.redux)
                                       ? Object.keys(window.__data.redux) : null,
                        };
                    } catch (e) {
                        return { ok: false, error: String(e) };
                    }
                }
            """)
        except Exception as exc:
            print(f"[gametime] ERROR: page.evaluate() failed: {exc}", file=sys.stderr)
            await context.close()
            return [], None

        try:
            await context.close()
        except Exception:
            pass

    if not result.get("ok"):
        print(
            f"[gametime] ERROR: window.__data.redux.listings.listings not found.\n"
            f"  topKeys: {result.get('topKeys')}\n"
            f"  reduxKeys: {result.get('reduxKeys')}\n"
            f"  error: {result.get('error')}",
            file=sys.stderr,
        )
        return [], None

    raw_items = result["listings"]
    if verbose:
        print(f"[gametime] raw listings in window.__data: {len(raw_items)}")

    # Filter to this event_id (sanity check — window.__data should only have this event's listings)
    event_items = [l for l in raw_items if l.get("eventId") == event_id]
    if len(event_items) < len(raw_items):
        if verbose:
            print(
                f"[gametime] filtered by eventId={event_id}: "
                f"{len(event_items)} / {len(raw_items)} listings match"
            )
        raw_items = event_items

    raw_body = json.dumps(raw_items).encode()
    return raw_items, raw_body


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_listings(raw_items: list) -> Tuple[list, dict]:
    """
    Convert raw Gametime window.__data listing objects to ManualIngestRequest wire format.

    Confirmed field mapping (from live window.__data inspection 2026-05-24):
      id                     → external_listing_id  (24-char hex ObjectId)
      spot.section           → section              (bare number, e.g. "542")
      spot.row               → row
      len(seats)             → quantity             (== max(availableLots) always)
      price.prefee / 100     → price                (display price in USD, fees excluded)
      price.total / 100      → all_in_price         (all-in USD, same as preTaxTotal)
      seats (non-"*")        → extra.seat_numbers   (actual seat numbers when known)
      spot.sectionGroup      → extra.zone           (e.g. "100 Level", "Club", "VIP")
      ticketType             → extra.listing_type
      availableLots          → extra.available_lots (purchasable quantities)

    Prices are in CENTS in the raw data — divide by 100 for USD.
    """
    listings = []
    seen: set[str] = set()
    skipped_zero_price = 0
    skipped_dup        = 0
    skipped_no_id      = 0
    skipped_no_spot    = 0

    for item in raw_items:
        listing_id = str(item.get("id") or "")
        if not listing_id:
            skipped_no_id += 1
            continue
        if listing_id in seen:
            skipped_dup += 1
            continue
        seen.add(listing_id)

        # Location
        spot = item.get("spot") or {}
        if not spot:
            skipped_no_spot += 1
            continue
        section = str(spot.get("section") or "Unknown")
        row     = spot.get("row") or None

        # Quantity: len(seats) == max(availableLots) in all observed data
        seats_list = item.get("seats") or []
        quantity   = max(len(seats_list), 1)

        # Prices are in CENTS
        price_obj = item.get("price") or {}
        prefee_cents = price_obj.get("prefee") or 0
        total_cents  = price_obj.get("total") or price_obj.get("preTaxTotal") or 0

        price  = prefee_cents / 100.0
        all_in = total_cents  / 100.0 if total_cents else None

        if price <= 0:
            skipped_zero_price += 1
            continue

        # Seat numbers: omit wildcard placeholders
        real_seats = [s for s in seats_list if s != "*"]

        # Extra metadata
        extra: dict = {}
        if real_seats:
            extra["seat_numbers"] = real_seats
        if spot.get("sectionGroup"):
            extra["zone"] = spot["sectionGroup"]
        if item.get("ticketType"):
            extra["listing_type"] = item["ticketType"]
        if item.get("availableLots"):
            extra["available_lots"] = item["availableLots"]
        if item.get("deliveryType"):
            extra["delivery_type"] = item["deliveryType"]

        listings.append({
            "external_listing_id": listing_id,
            "section":             section,
            "row":                 row,
            "quantity":            quantity,
            "price":               price,
            "fees":                None,           # fees baked into all_in
            "all_in_price":        all_in,
            "listing_url":         None,
            "extra":               extra if extra else None,
        })

    return listings, {
        "skipped_zero_price": skipped_zero_price,
        "skipped_dup":        skipped_dup,
        "skipped_no_id":      skipped_no_id,
        "skipped_no_spot":    skipped_no_spot,
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

def fetch_active_gametime_events(backend_url: str) -> list[dict]:
    """Query the backend for all active, validated Gametime tracked events.

    Returns list of dicts with keys: te_id, external_event_id, external_url, event_date, title
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
        print(f"[gametime] ERROR: cannot fetch events from backend: {exc}", file=sys.stderr)
        return []

    active = []
    for ev in events:
        for te in (ev.get("tracked_events") or []):
            if (
                te.get("marketplace_slug") == "gametime"
                and te.get("is_active")
                and te.get("external_event_id")
                and te.get("external_url")
            ):
                active.append({
                    "te_id":             te["id"],
                    "external_event_id": te["external_event_id"],
                    "external_url":      te["external_url"],
                    "event_date":        ev.get("event_date", ""),
                    "title":             ev.get("title", ""),
                })
    return active


# ── Single event run ──────────────────────────────────────────────────────────

async def run_one_event(
    te_id: int,
    event_id: str,
    event_url: str,
    backend_url: str,
    save_raw_dir: str,
    dry_run: bool,
    verbose: bool,
) -> bool:
    """Fetch, parse, and ingest listings for one Gametime tracked event.

    Returns True on success, False on failure.
    """
    fetched_at = datetime.now(timezone.utc).isoformat()

    if verbose:
        print(f"[gametime] te={te_id}: navigating → {event_url}")

    # Step 1: Fetch
    try:
        raw_items, raw_body = await asyncio.wait_for(
            fetch_gametime_listings(event_url, event_id, verbose=verbose),
            timeout=_FETCH_TIMEOUT_SECS,
        )
    except asyncio.TimeoutError:
        print(f"[gametime] te={te_id}: ERROR: fetch timed out after {_FETCH_TIMEOUT_SECS}s", file=sys.stderr)
        return False

    if not raw_items:
        print(f"[gametime] te={te_id}: ERROR: 0 raw listings from window.__data", file=sys.stderr)
        return False

    # Step 2: Parse
    listings, skip_stats = parse_listings(raw_items)
    if verbose:
        print(
            f"[gametime] te={te_id}: parsed: {len(listings)} listings "
            f"(skipped: zero_price={skip_stats['skipped_zero_price']}, "
            f"dup={skip_stats['skipped_dup']}, no_id={skip_stats['skipped_no_id']}, "
            f"no_spot={skip_stats['skipped_no_spot']})"
        )

    if not listings:
        print(f"[gametime] te={te_id}: ERROR: 0 valid listings after parsing", file=sys.stderr)
        return False

    prices = [l["price"] for l in listings]
    if verbose:
        print(
            f"[gametime] te={te_id}: price range: ${min(prices):.2f} – ${max(prices):.2f}  "
            f"avg: ${sum(prices)/len(prices):.2f}"
        )

    # Step 2b: Save raw payload
    raw_path: Optional[str] = None
    if raw_body:
        ts_compact = fetched_at.replace(":", "").replace("+", "").replace("-", "")[:15]
        raw_path = os.path.join(
            save_raw_dir,
            f"gametime_raw_te{te_id}_{event_id[:8]}_{ts_compact}.json",
        )
        try:
            with open(raw_path, "wb") as fh:
                fh.write(raw_body)
            if verbose:
                print(f"[gametime] te={te_id}: raw payload saved → {raw_path} ({len(raw_body):,} bytes)")
        except Exception as exc:
            print(f"[gametime] te={te_id}: WARN: could not save raw payload: {exc}", file=sys.stderr)
            raw_path = "(save failed)"

    if dry_run:
        print(f"\n[gametime] DRY RUN te={te_id} — {len(listings)} listings parsed, NOT posted to backend")
        print(f"  would POST to: {backend_url}/api/poll/tracked/{te_id}/manual-ingest")
        print("\nSample listings (first 5):")
        for l in listings[:5]:
            extra_info = (
                f" seats={l['extra']['seat_numbers']}"
                if l.get("extra") and l["extra"].get("seat_numbers") else ""
            )
            print(
                f"  id={l['external_listing_id']}  sec={l['section']}  "
                f"row={l['row']}  qty={l['quantity']}  "
                f"price=${l['price']:.2f}  all_in=${l.get('all_in_price') or 0:.2f}"
                f"{extra_info}"
            )
        return True

    # Step 3: Ingest
    if verbose:
        print(f"[gametime] te={te_id}: posting {len(listings)} listings → {backend_url}…")
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
            f"[gametime] te={te_id}: ERROR: backend returned {exc.response.status_code}: "
            f"{exc.response.text[:300]}",
            file=sys.stderr,
        )
        return False
    except httpx.ConnectError:
        print(
            f"[gametime] te={te_id}: ERROR: cannot connect to backend at {backend_url}",
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
    print(f"Gametime ingest complete — te={te_id}")
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
        description="Host-side Gametime collector — fetches listings and ingests via backend API",
    )
    parser.add_argument(
        "--te-id",
        type=int,
        default=None,
        help="tracked_event_id to ingest into (default: auto-discover all active GT events)",
    )
    parser.add_argument(
        "--event-id",
        default=None,
        help="Gametime 24-char hex event ID (required when --te-id is specified)",
    )
    parser.add_argument(
        "--event-url",
        default=None,
        help="Full Gametime event page URL (required when --te-id is specified)",
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
        if not args.event_id or not args.event_url:
            print(
                "[gametime] ERROR: --te-id requires --event-id and --event-url",
                file=sys.stderr,
            )
            sys.exit(1)
        ok = await run_one_event(
            te_id=args.te_id,
            event_id=args.event_id,
            event_url=args.event_url,
            backend_url=args.backend,
            save_raw_dir=args.save_raw,
            dry_run=args.dry_run,
            verbose=verbose,
        )
        if ok and not args.dry_run:
            _mark_run_complete(args.te_id)
        sys.exit(0 if ok else 1)

    # ── Auto-mode: discover all active Gametime events from backend ───────────
    active_events = fetch_active_gametime_events(args.backend)
    if not active_events:
        print("[gametime] no active Gametime tracked events found — nothing to do")
        sys.exit(0)

    if verbose:
        print(f"[gametime] auto-mode: found {len(active_events)} active Gametime event(s)")

    ran_any = False
    for ev in active_events:
        te_id      = ev["te_id"]
        event_id   = ev["external_event_id"]
        event_url  = ev["external_url"]
        event_date = ev["event_date"]
        title      = ev["title"]

        if verbose:
            print(f"\n[gametime] checking te={te_id}: {title}")

        if not args.force and not _check_cadence_due(te_id, event_date, verbose=verbose):
            continue

        ok = await run_one_event(
            te_id=te_id,
            event_id=event_id,
            event_url=event_url,
            backend_url=args.backend,
            save_raw_dir=args.save_raw,
            dry_run=args.dry_run,
            verbose=verbose,
        )
        if ok and not args.dry_run:
            _mark_run_complete(te_id)
        ran_any = True

    if not ran_any:
        print("[gametime] all events within cadence — skipping")


if __name__ == "__main__":
    asyncio.run(main())
