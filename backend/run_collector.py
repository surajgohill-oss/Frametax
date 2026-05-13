#!/usr/bin/env python3
"""
Debug CLI for the LA Concert Watchlist collector system.

USAGE:

  # Normal run (headless, non-interactive)
  python run_collector.py --marketplace stubhub --event-id 12345678

  # Full debug mode: headed browser, verbose logs, screenshots, step-through
  python run_collector.py --marketplace stubhub --event-id 12345678 --debug

  # Debug + slow motion (500ms between actions)
  python run_collector.py --marketplace stubhub --event-id 12345678 --debug --slow-mo 500

  # Step-through mode (pause at each stage, press Enter to continue)
  python run_collector.py --marketplace stubhub --event-id 12345678 --debug --step

  # Attach to running Chrome on port 9222 (Chrome Attach Mode)
  python run_collector.py --marketplace stubhub --event-id 12345678 --chrome-attach

  # Full URL instead of event ID
  python run_collector.py --marketplace stubhub --url "https://www.stubhub.com/event/12345678"

  # Show stored error logs
  python run_collector.py --show-errors --marketplace stubhub

  # Show failure memory table
  python run_collector.py --show-memory

  # Clear failure memory for a marketplace (reset learned failures)
  python run_collector.py --clear-memory --marketplace stubhub

CHROME ATTACH MODE:
  1. Launch Chrome with remote debugging enabled:
       /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
         --remote-debugging-port=9222 \\
         --user-data-dir=/tmp/chrome-debug

  2. Navigate to the event page manually in that Chrome window.

  3. In another terminal, run:
       python run_collector.py --marketplace stubhub --event-id 12345678 --chrome-attach

  The collector attaches to the existing Chrome session, intercepts XHR
  responses, and reads live DOM state. You can open DevTools in that Chrome
  window to inspect selectors in real time.
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from app.config import get_settings
from app.collectors.registry import get_collector


@dataclass
class FakeTrackedEvent:
    """Minimal tracked event object for CLI use."""
    event_id: int
    marketplace_id: int = 0
    external_event_id: Optional[str] = None
    external_url: Optional[str] = None
    is_active: bool = True
    poll_interval_minutes: int = 60


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="LA Concert Watchlist — collector debug CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--marketplace", "-m", choices=["stubhub", "seatgeek"],
                   help="Marketplace to run")
    p.add_argument("--event-id", "-e", help="External event ID from the marketplace URL")
    p.add_argument("--url", "-u", help="Full event URL (alternative to --event-id)")
    p.add_argument("--debug", "-d", action="store_true",
                   help="Debug mode: headed browser, verbose logs, screenshots")
    p.add_argument("--slow-mo", type=int, default=0, metavar="MS",
                   help="Milliseconds to slow down Playwright actions (debug only)")
    p.add_argument("--step", "-s", action="store_true",
                   help="Step-through mode: pause at each stage")
    p.add_argument("--chrome-attach", action="store_true",
                   help="Attach to running Chrome on localhost:9222")
    p.add_argument("--chrome-port", type=int, default=9222,
                   help="Chrome remote debugging port (default: 9222)")
    p.add_argument("--show-errors", action="store_true",
                   help="Print recent ScraperErrorLog entries and exit")
    p.add_argument("--show-memory", action="store_true",
                   help="Print FailureMemory table and exit")
    p.add_argument("--clear-memory", action="store_true",
                   help="Clear FailureMemory entries for --marketplace")
    p.add_argument("--limit", type=int, default=20,
                   help="Row limit for --show-errors / --show-memory")
    p.add_argument("--output", "-o", choices=["pretty", "json"], default="pretty",
                   help="Output format")
    return p


# ------------------------------------------------------------------ #
# DB query helpers (sync wrapper for CLI convenience)                 #
# ------------------------------------------------------------------ #

async def show_errors(marketplace: Optional[str], limit: int):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select, desc
    from app.models.debug import ScraperErrorLog
    from app.database import Base

    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        q = select(ScraperErrorLog).order_by(desc(ScraperErrorLog.timestamp)).limit(limit)
        if marketplace:
            q = q.where(ScraperErrorLog.marketplace == marketplace)
        result = await db.execute(q)
        rows = result.scalars().all()

    if not rows:
        print("No error logs found.")
        return

    print(f"\n{'='*70}")
    print(f"  SCRAPER ERROR LOGS  ({len(rows)} rows)")
    print(f"{'='*70}")
    for r in rows:
        ts = r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "?"
        print(f"\n[{r.id}] {ts} · \033[31m{r.error_type}\033[0m · {r.marketplace}")
        if r.event_id:
            print(f"  event_id  : {r.event_id}")
        if r.url:
            print(f"  url       : {r.url[:80]}")
        if r.selector:
            print(f"  selector  : {r.selector}")
        if r.http_status:
            print(f"  http      : {r.http_status}")
        if r.raw_sample:
            print(f"  sample    : {r.raw_sample[:120]}")
        if r.screenshot_path:
            print(f"  screenshot: {r.screenshot_path}")
        if r.html_snapshot_path:
            print(f"  html      : {r.html_snapshot_path}")
    await engine.dispose()


async def show_memory(marketplace: Optional[str], limit: int):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from app.models.debug import FailureMemory

    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        q = select(FailureMemory).order_by(FailureMemory.failure_count.desc()).limit(limit)
        if marketplace:
            q = q.where(FailureMemory.marketplace == marketplace)
        result = await db.execute(q)
        rows = result.scalars().all()

    if not rows:
        print("Failure memory is empty.")
        return

    print(f"\n{'='*70}")
    print(f"  FAILURE MEMORY  ({len(rows)} entries)")
    print(f"{'='*70}")
    for r in rows:
        skip_marker = " \033[31m[SKIP]\033[0m" if r.skip_failed else ""
        print(f"\n[{r.id}] {r.marketplace} · {r.error_type}{skip_marker}")
        print(f"  failed_pattern : {r.failed_pattern[:80]}")
        print(f"  failure_count  : {r.failure_count}")
        if r.fallback_pattern:
            print(f"  \033[32mfallback       : {r.fallback_pattern[:80]}\033[0m")
            print(f"  fallback_wins  : {r.fallback_success_count}")
        first = r.first_seen.strftime("%Y-%m-%d %H:%M") if r.first_seen else "?"
        last = r.last_seen.strftime("%Y-%m-%d %H:%M") if r.last_seen else "?"
        print(f"  first/last     : {first} / {last}")
    await engine.dispose()


async def clear_memory(marketplace: str):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import delete
    from app.models.debug import FailureMemory

    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        result = await db.execute(
            delete(FailureMemory).where(FailureMemory.marketplace == marketplace)
        )
        await db.commit()
        print(f"Cleared {result.rowcount} FailureMemory entries for '{marketplace}'.")
    await engine.dispose()


# ------------------------------------------------------------------ #
# Main collection run                                                  #
# ------------------------------------------------------------------ #

async def run_collection(args: argparse.Namespace):
    settings = get_settings()

    # Apply Chrome attach mode
    if args.chrome_attach:
        settings.__dict__["cdp_url"] = f"http://localhost:{args.chrome_port}"
        print(f"\033[33m[CDP] Attaching to Chrome at localhost:{args.chrome_port}\033[0m")
        print("Make sure Chrome is running with: --remote-debugging-port=9222")

    # Apply step-through mode
    if args.step:
        import app.collectors.debug_mixin as dm
        dm.DebugMixin.debug_mode = True  # will be overridden per-instance below

    slow_mo = args.slow_mo if args.debug else 0
    collector = get_collector(
        args.marketplace,
        settings,
        debug_mode=args.debug or args.chrome_attach,
        slow_mo_ms=slow_mo,
    )
    if collector is None:
        print(f"Unknown marketplace: {args.marketplace}")
        sys.exit(1)

    # Patch step-through if requested
    if args.step:
        collector.debug_mode = True
        # Monkey-patch _debug_pause to actually block
        import asyncio as _aio
        async def _step_pause(label=""):
            print(f"\n\033[35m[STEP] {label} — press Enter to continue...\033[0m", end="", flush=True)
            await _aio.get_event_loop().run_in_executor(None, input)
        collector._debug_pause = _step_pause

    tracked = FakeTrackedEvent(
        event_id=int(args.event_id) if args.event_id else 0,
        external_event_id=args.event_id,
        external_url=args.url,
    )

    print(f"\n\033[36m{'='*60}\033[0m")
    print(f"\033[36m  {args.marketplace.upper()} COLLECTOR\033[0m")
    print(f"\033[36m  event_id : {args.event_id or 'from URL'}\033[0m")
    print(f"\033[36m  debug    : {collector.debug_mode}\033[0m")
    print(f"\033[36m  slow_mo  : {slow_mo}ms\033[0m")
    print(f"\033[36m{'='*60}\033[0m\n")

    start = datetime.utcnow()
    result = await collector.collect(tracked)
    elapsed = (datetime.utcnow() - start).total_seconds()

    await collector.close()

    # Output
    print(f"\n\033[32m{'='*60}\033[0m")
    print(f"\033[32m  RESULT\033[0m")
    print(f"\033[32m{'='*60}\033[0m")

    if result.error:
        print(f"\033[31m  ERROR: {result.error}\033[0m")
    else:
        print(f"  Listings : \033[32m{result.raw_count}\033[0m")
        print(f"  Elapsed  : {elapsed:.2f}s")

    if result.listings:
        if args.output == "json":
            data = [
                {
                    "id": l.external_listing_id,
                    "section": l.section,
                    "row": l.row,
                    "qty": l.quantity,
                    "price": float(l.price),
                    "fees": float(l.fees) if l.fees else None,
                    "all_in": float(l.all_in_price) if l.all_in_price else None,
                    "url": l.listing_url,
                }
                for l in result.listings
            ]
            print(json.dumps(data, indent=2))
        else:
            print(f"\n  {'Section':<20} {'Row':<6} {'Qty':<5} {'Price':>8}  {'All-In':>8}")
            print(f"  {'-'*60}")
            for l in result.listings[:30]:
                row = l.row or "—"
                all_in = f"${l.all_in_price:.0f}" if l.all_in_price else "—"
                print(f"  {l.section:<20} {row:<6} {l.quantity:<5} ${l.price:>7.2f}  {all_in:>8}")
            if len(result.listings) > 30:
                print(f"  ... and {len(result.listings) - 30} more")


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.show_errors:
        asyncio.run(show_errors(args.marketplace, args.limit))
        return

    if args.show_memory:
        asyncio.run(show_memory(args.marketplace, args.limit))
        return

    if args.clear_memory:
        if not args.marketplace:
            print("--clear-memory requires --marketplace")
            sys.exit(1)
        asyncio.run(clear_memory(args.marketplace))
        return

    if not args.marketplace:
        parser.error("--marketplace is required for collection runs")
    if not args.event_id and not args.url:
        parser.error("--event-id or --url is required")

    asyncio.run(run_collection(args))


if __name__ == "__main__":
    main()
