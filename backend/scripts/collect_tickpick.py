#!/usr/bin/env python3
"""
Host-side TickPick collector script.

WHY THIS EXISTS
===============
TickPick's listing API (api.tickpick.com) uses DataDome bot detection that blocks
the Docker container's IP address.  The host Mac's IP is NOT blocked — confirmed by
capturing 2,694 listings for the 49ers event in testing.

This script runs Playwright on the HOST machine (using rebrowser-playwright to bypass
DataDome), intercepts the listing API response that TickPick's own JavaScript fires
automatically on page load, parses the listings, and POSTs them to the backend's
manual-ingest endpoint.  The backend then runs the same _process_result() pipeline
that any other collector would trigger.

CADENCE SELF-THROTTLING
=======================
When run WITHOUT --te-id/--event-id/--event-url overrides, the script queries the
backend for ALL active TickPick tracked events and runs a cadence check per event:
the interval tier is computed from each event's event_date and compared against
the last recorded run time.  Events not yet due are skipped.

When run WITH explicit --te-id, cadence is bypassed (use --force to override even
when run via launchd without explicit overrides).

USAGE
=====
  # Auto-mode: runs all active TickPick events that are cadence-due (launchd default)
  python3 scripts/collect_tickpick.py

  # Specific tracked_event_id (bypasses cadence check)
  python3 scripts/collect_tickpick.py --te-id 45

  # Force run regardless of cadence
  python3 scripts/collect_tickpick.py --force

  # Dry run — capture and parse listings without posting to backend
  python3 scripts/collect_tickpick.py --dry-run

  # Custom backend URL
  python3 scripts/collect_tickpick.py --backend http://localhost:8000

REQUIREMENTS
============
  pip install playwright httpx
  playwright install chromium

The script uses the system's default Playwright installation and a fresh browser
context (no persistent session needed — TickPick's listing API doesn't require auth).
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional, Tuple

import httpx

try:
    from rebrowser_playwright.async_api import async_playwright
    _USING_REBROWSER = True
except ImportError:
    from playwright.async_api import async_playwright  # type: ignore[assignment]
    _USING_REBROWSER = False

# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_BACKEND_URL = "https://backend-production-509f.up.railway.app"
MARKETPLACE_SLUG = "tickpick"

# Last-run timestamp file — per-event keyed by te_id (mirrors Gametime cadence pattern)
_LAST_RUN_DIR = Path.home() / ".concert-tracker"
_LAST_RUN_DIR.mkdir(parents=True, exist_ok=True)


def _last_run_file(te_id: int) -> Path:
    return _LAST_RUN_DIR / f"tickpick_last_run_te{te_id}.txt"


def _compute_interval_minutes(event_date_iso: str) -> int:
    """Return cadence tier interval in minutes for the given event_date (ISO string)."""
    from datetime import datetime, timezone
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
    """Return True if this event is due for a poll based on its cadence tier."""
    interval_min = _compute_interval_minutes(event_date_iso)
    path = _last_run_file(te_id)
    if not path.exists():
        if verbose:
            print(f"[tickpick] cadence te={te_id}: first run — interval {interval_min}m — proceeding")
        return True
    try:
        last_run_str = path.read_text().strip()
        from datetime import datetime, timezone
        last_run = datetime.fromisoformat(last_run_str)
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)
        elapsed_min = (datetime.now(timezone.utc) - last_run).total_seconds() / 60
        due = elapsed_min >= interval_min
        if verbose:
            if due:
                print(f"[tickpick] cadence te={te_id}: last run {elapsed_min:.0f}m ago, interval {interval_min}m — proceeding")
            else:
                print(f"[tickpick] cadence te={te_id}: last run {elapsed_min:.0f}m ago, interval {interval_min}m — skipping (next in ~{interval_min - elapsed_min:.0f}m)")
        return due
    except Exception as exc:
        if verbose:
            print(f"[tickpick] cadence te={te_id}: could not read last-run file ({exc}) — proceeding")
        return True


def _mark_run_complete(te_id: int) -> None:
    """Record the current timestamp as the last successful run for this te_id."""
    from datetime import datetime, timezone
    try:
        _last_run_file(te_id).write_text(datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        print(f"[tickpick] WARN: could not write last-run file for te={te_id}: {exc}", file=sys.stderr)

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_FETCH_TIMEOUT_SECS = 90   # full Playwright session timeout
_PAGE_WAIT_SECS = 8        # wait after DOMContentLoaded for the XHR to fire


# ── Browser fetch ─────────────────────────────────────────────────────────────

async def fetch_tickpick_listings(
    event_url: str,
    event_id: str,
    verbose: bool = True,
) -> Tuple[list, Optional[bytes]]:
    """Navigate the TickPick event page and intercept the listing API response.

    Returns:
        (raw_items, raw_body_bytes)
        raw_items — list of dicts from data["listings"]
        raw_body_bytes — the raw JSON bytes for forensic purposes
    """
    captured_body: list[bytes] = []
    api_pattern = f"listings/internal/event-v2/{event_id}"

    if verbose:
        print(f"[tickpick] opening browser → {event_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            user_agent=_BROWSER_UA,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = await context.new_page()

        async def on_response(response):
            if api_pattern in response.url:
                status = response.status
                if verbose:
                    print(f"[tickpick] API response: [{status}] {response.url}")
                if status == 200:
                    try:
                        body = await response.body()
                        captured_body.append(body)
                        if verbose:
                            print(f"[tickpick] captured {len(body):,} bytes")
                    except Exception as exc:
                        print(f"[tickpick] WARN: response.body() error: {exc}", file=sys.stderr)
                elif status == 403:
                    print(
                        "[tickpick] ERROR: 403 from api.tickpick.com — "
                        "DataDome is blocking this IP.\n"
                        "This host IP may have been flagged since the last test. "
                        "Try again from a different network.",
                        file=sys.stderr,
                    )
                else:
                    print(f"[tickpick] WARN: unexpected status {status}", file=sys.stderr)

        page.on("response", on_response)

        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as exc:
            print(f"[tickpick] WARN: page.goto error (may be non-fatal): {exc}", file=sys.stderr)

        if verbose:
            print(f"[tickpick] page loaded, waiting {_PAGE_WAIT_SECS}s for XHR…")
        await asyncio.sleep(_PAGE_WAIT_SECS)

        try:
            await browser.close()
        except Exception:
            pass

    if not captured_body:
        return [], None

    raw_body = captured_body[0]
    data = json.loads(raw_body)
    raw_items = data.get("listings", [])
    return raw_items, raw_body


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_listings(raw_items):
    """Convert raw TickPick API items to ManualIngestRequest listing dicts.

    Confirmed field mapping (2026-05-23 from live response):
      id  → external_listing_id  (string)
      sid → section              (string, e.g. "529", "112 FIELD INFIELD")
      r   → row                  (string; None for GA)
      q   → quantity             (int)
      p   → price / all_in_price (float, all-in — no hidden fees)
      a   → available            (bool; skip if False)

    TickPick pricing model: p == all_in_price; fees = None.
    """
    listings = []
    seen = set()
    skipped_unavailable = 0
    skipped_zero_price = 0
    skipped_dup = 0

    for item in raw_items:
        # Skip unavailable listings
        if not item.get("a", True):
            skipped_unavailable += 1
            continue

        listing_id = str(item.get("id") or "")
        if not listing_id:
            continue

        if listing_id in seen:
            skipped_dup += 1
            continue
        seen.add(listing_id)

        section = str(item.get("sid") or "Unknown")
        row = item.get("r") or None
        quantity = int(item.get("q") or 1)
        price = float(item.get("p") or 0)

        if price <= 0:
            skipped_zero_price += 1
            continue

        listings.append({
            "external_listing_id": listing_id,
            "section": section,
            "row": row,
            "quantity": quantity,
            "price": price,
            "fees": None,
            "all_in_price": price,   # TickPick is all-in; p IS the all-in price
            "listing_url": None,
        })

    return listings, {
        "skipped_unavailable": skipped_unavailable,
        "skipped_zero_price": skipped_zero_price,
        "skipped_dup": skipped_dup,
    }


# ── Backend ingest ────────────────────────────────────────────────────────────

def post_to_backend(
    backend_url: str,
    te_id: int,
    marketplace_slug: str,
    listings: list[dict],
    fetched_at: str,
) -> dict:
    """POST listings to the manual-ingest endpoint."""
    url = f"{backend_url.rstrip('/')}/api/poll/tracked/{te_id}/manual-ingest"
    payload = {
        "tracked_event_id": te_id,
        "marketplace_slug": marketplace_slug,
        "listings": listings,
        "fetched_at": fetched_at,
    }
    resp = httpx.post(url, json=payload, timeout=120.0)
    resp.raise_for_status()
    return resp.json()


# ── Active event discovery ────────────────────────────────────────────────────

def fetch_active_tickpick_events(backend_url: str) -> list[dict]:
    """Query the backend for all active, validated TickPick tracked events.

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
        print(f"[tickpick] ERROR: cannot fetch events from backend: {exc}", file=sys.stderr)
        return []

    active = []
    for ev in events:
        for te in (ev.get("tracked_events") or []):
            if (
                te.get("marketplace_slug") == "tickpick"
                and te.get("is_active")
                and te.get("external_event_id")
                and te.get("external_url")
            ):
                active.append({
                    "te_id": te["id"],
                    "external_event_id": te["external_event_id"],
                    "external_url": te["external_url"],
                    "event_date": ev.get("event_date", ""),
                    "title": ev.get("title", ""),
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
    """Fetch, parse, and ingest listings for one TickPick tracked event.

    Returns True on success, False on failure.
    """
    import os
    fetched_at = datetime.now(timezone.utc).isoformat()

    if verbose:
        print(f"[tickpick] te={te_id}: navigating → {event_url}")

    # Step 1: Fetch
    try:
        raw_items, raw_body = await asyncio.wait_for(
            fetch_tickpick_listings(event_url, event_id, verbose=verbose),
            timeout=_FETCH_TIMEOUT_SECS,
        )
    except asyncio.TimeoutError:
        print(f"[tickpick] te={te_id}: ERROR: fetch timed out after {_FETCH_TIMEOUT_SECS}s", file=sys.stderr)
        return False

    if not raw_items:
        print(f"[tickpick] te={te_id}: ERROR: 0 raw listings captured", file=sys.stderr)
        return False

    # Step 2: Parse
    listings, skip_stats = parse_listings(raw_items)
    if verbose:
        print(
            f"[tickpick] te={te_id}: parsed: {len(listings)} listings "
            f"(skipped: unavailable={skip_stats['skipped_unavailable']}, "
            f"zero_price={skip_stats['skipped_zero_price']}, "
            f"dup={skip_stats['skipped_dup']})"
        )

    if not listings:
        print(f"[tickpick] te={te_id}: ERROR: 0 valid listings after parsing", file=sys.stderr)
        return False

    prices = [l["price"] for l in listings]
    if verbose:
        print(f"[tickpick] te={te_id}: price range: ${min(prices):.2f} – ${max(prices):.2f}  avg: ${sum(prices)/len(prices):.2f}")

    # Step 2b: Save raw payload
    ts_compact = fetched_at.replace(":", "").replace("+", "").replace("-", "")[:15]
    raw_path = os.path.join(save_raw_dir, f"tickpick_raw_te{te_id}_event{event_id}_{ts_compact}.json")
    try:
        with open(raw_path, "wb") as fh:
            fh.write(raw_body)
        if verbose:
            print(f"[tickpick] te={te_id}: raw payload saved → {raw_path} ({len(raw_body):,} bytes)")
    except Exception as exc:
        print(f"[tickpick] WARN: could not save raw payload: {exc}", file=sys.stderr)
        raw_path = "(save failed)"

    if dry_run:
        print(f"\n[tickpick] DRY RUN te={te_id} — {len(listings)} listings parsed, NOT posted to backend")
        return True

    # Step 3: Ingest
    if verbose:
        print(f"[tickpick] te={te_id}: posting {len(listings)} listings → {backend_url}…")
    try:
        result = post_to_backend(
            backend_url=backend_url,
            te_id=te_id,
            marketplace_slug=MARKETPLACE_SLUG,
            listings=listings,
            fetched_at=fetched_at,
        )
    except httpx.HTTPStatusError as exc:
        print(f"[tickpick] te={te_id}: ERROR: backend returned {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
        return False
    except httpx.ConnectError:
        print(f"[tickpick] te={te_id}: ERROR: cannot connect to backend at {backend_url}", file=sys.stderr)
        return False

    poll_run_id = result.get("poll_run_id")
    if poll_run_id and os.path.exists(raw_path):
        final_path = raw_path.replace(".json", f"_run{poll_run_id}.json")
        try:
            os.rename(raw_path, final_path)
            raw_path = final_path
        except Exception:
            pass

    print("\n" + "=" * 60)
    print(f"TickPick ingest complete — te={te_id}")
    print("=" * 60)
    print(f"  status            : {result.get('status')}")
    print(f"  poll_run_id       : {poll_run_id}")
    print(f"  listings_found    : {result.get('listings_found')}")
    print(f"  new_listings      : {result.get('new_listings')}")
    print(f"  reactivated       : {result.get('reactivated_listings')}")
    print(f"  disappeared       : {result.get('disappeared_listings')}")
    print(f"  raw_payload       : {raw_path}")
    print("=" * 60)
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(
        description="Host-side TickPick collector — fetches listings and ingests via backend API",
    )
    parser.add_argument(
        "--te-id",
        type=int,
        default=None,
        help="tracked_event_id to ingest into (default: auto-discover all active TP events)",
    )
    parser.add_argument(
        "--event-id",
        default=None,
        help="TickPick internal event ID (required when --te-id is specified)",
    )
    parser.add_argument(
        "--event-url",
        default=None,
        help="Full TickPick event page URL (required when --te-id is specified)",
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
        help="Directory to save raw API JSON (default: /tmp)",
    )
    args = parser.parse_args()
    args.save_raw = args.save_raw or "/tmp"
    verbose = not args.quiet

    # ── Manual single-event mode ──────────────────────────────────────────────
    if args.te_id is not None:
        if not args.event_id or not args.event_url:
            print(
                "[tickpick] ERROR: --te-id requires --event-id and --event-url",
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

    # ── Auto-mode: discover all active TickPick events from backend ───────────
    active_events = fetch_active_tickpick_events(args.backend)
    if not active_events:
        print("[tickpick] no active TickPick tracked events found — nothing to do")
        sys.exit(0)

    if verbose:
        print(f"[tickpick] auto-mode: found {len(active_events)} active TickPick event(s)")

    ran_any = False
    for ev in active_events:
        te_id       = ev["te_id"]
        event_id    = ev["external_event_id"]
        event_url   = ev["external_url"]
        event_date  = ev["event_date"]
        title       = ev["title"]

        if verbose:
            print(f"\n[tickpick] checking te={te_id}: {title}")

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
        print("[tickpick] all events within cadence — skipping")


if __name__ == "__main__":
    asyncio.run(main())
