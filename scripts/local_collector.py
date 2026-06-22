#!/usr/bin/env python3
"""
Local Mac collector — runs StubHub and TickPick collectors from this machine
(residential IP, no DataDome/403 blocks) and pushes results to Railway.

Usage:
    python3 scripts/local_collector.py [--once] [--event-id EVENT_ID]

Schedule (cron via launchd or crontab):
    */15 * * * *  /usr/local/bin/python3 /path/to/scripts/local_collector.py

Required env vars (set in ~/.zshenv or a .env file in this directory):
    RAILWAY_BASE_URL    https://backend-production-509f.up.railway.app
    LOCAL_COLLECTOR_SECRET   <same value as on Railway>

Optional:
    LOCAL_COLLECTOR_MARKETPLACES  stubhub,tickpick   (default)
    LOCAL_COLLECTOR_DRY_RUN      1   — print listings but don't push
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

# ── Bootstrap: add backend to path so we can import collectors directly ──────
_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Load .env from repo root if present
_env_file = _REPO_ROOT / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("local_collector")

# ── Config ─────────────────────────────────────────────────────────────────────

RAILWAY_BASE = os.environ.get("RAILWAY_BASE_URL", "https://backend-production-509f.up.railway.app")
SECRET = os.environ.get("LOCAL_COLLECTOR_SECRET", "")
DRY_RUN = os.environ.get("LOCAL_COLLECTOR_DRY_RUN", "0") == "1"
TARGET_MARKETPLACES = [
    m.strip()
    for m in os.environ.get("LOCAL_COLLECTOR_MARKETPLACES", "stubhub,tickpick").split(",")
    if m.strip()
]

COLLECTOR_VERSION = "local_mac_v1"
INGEST_URL = f"{RAILWAY_BASE}/api/collect/ingest"
HEARTBEAT_URL = f"{RAILWAY_BASE}/api/collect/heartbeat"
EVENTS_URL = f"{RAILWAY_BASE}/api/events"


# ── Minimal stub TrackedEvent so collectors can run without a DB session ──────

class _FakeTrackedEvent:
    """Minimal stand-in for TrackedEvent that satisfies collector.collect()."""
    def __init__(self, te_id: int, event_id: int, external_event_id: Optional[str],
                 external_url: Optional[str], marketplace_id: int,
                 poll_interval_minutes: int = 60):
        self.id = te_id
        self.event_id = event_id
        self.external_event_id = external_event_id
        self.external_url = external_url
        self.marketplace_id = marketplace_id
        self.poll_interval_minutes = poll_interval_minutes
        self.event = None          # may be set after construction
        # Fields collectors may read
        self.is_active = True
        self.consecutive_zero_inventory_count = 0


# ── Core poll logic ───────────────────────────────────────────────────────────

async def _run_one_marketplace(
    http: httpx.AsyncClient,
    slug: str,
    te_data: dict,
    event_data: dict,
) -> dict:
    """
    Run one marketplace collector for one tracked event.
    Returns a summary dict with listings_found / error / elapsed_s.
    """
    from app.config import get_settings
    from app.collectors.registry import COLLECTOR_REGISTRY

    settings = get_settings()
    collector_cls = COLLECTOR_REGISTRY.get(slug)
    if not collector_cls:
        return {"slug": slug, "te_id": te_data["id"], "error": "no_collector", "listings_found": 0}

    collector = collector_cls(settings)

    te = _FakeTrackedEvent(
        te_id=te_data["id"],
        event_id=te_data.get("event_id") or event_data["id"],
        external_event_id=te_data.get("external_event_id"),
        external_url=te_data.get("external_url"),
        marketplace_id=te_data.get("marketplace_id", 0),
    )

    t0 = time.monotonic()
    try:
        result = await collector.collect(te)
    except Exception as exc:
        logger.exception("Collector %s te=%d raised: %s", slug, te_data["id"], exc)
        return {"slug": slug, "te_id": te_data["id"], "error": str(exc), "listings_found": 0}
    finally:
        await collector.close()

    elapsed = time.monotonic() - t0
    n = len(result.listings)
    logger.info(
        "%s te=%d event=%d listings=%d elapsed=%.1fs err=%s",
        slug, te_data["id"], event_data["id"], n, elapsed, result.error,
    )

    if DRY_RUN:
        logger.info("DRY_RUN: would push %d listings — skipping", n)
        return {"slug": slug, "te_id": te_data["id"], "listings_found": n, "dry_run": True}

    if result.error and n == 0:
        return {"slug": slug, "te_id": te_data["id"], "error": result.error, "listings_found": 0}

    # Push to Railway
    listings_payload = []
    for r in result.listings:
        listings_payload.append({
            "external_listing_id": r.external_listing_id,
            "section": r.section,
            "row": r.row,
            "quantity": r.quantity,
            "price": str(r.price),
            "fees": str(r.fees) if r.fees else None,
            "all_in_price": str(r.all_in_price) if r.all_in_price else None,
            "listing_url": r.listing_url,
            "market_segment": r.market_segment or "secondary_resale",
        })

    push_payload = {
        "te_id": te.id,
        "marketplace_slug": slug,
        "external_event_id": te.external_event_id,
        "listings": listings_payload,
        "collector_version": COLLECTOR_VERSION,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        resp = await http.post(
            INGEST_URL,
            json=push_payload,
            headers={"Authorization": f"Bearer {SECRET}"},
            timeout=30.0,
        )
        resp.raise_for_status()
        rj = resp.json()
        logger.info(
            "PUSHED: %s te=%d listings_accepted=%d poll_run=%s",
            slug, te.id, rj.get("listings_accepted", "?"), rj.get("poll_run_id", "?"),
        )
        return {"slug": slug, "te_id": te.id, "listings_found": n, "poll_run_id": rj.get("poll_run_id")}
    except Exception as exc:
        logger.error("PUSH_FAILED: %s te=%d — %s", slug, te.id, exc)
        return {"slug": slug, "te_id": te.id, "error": f"push_failed:{exc}", "listings_found": n}


async def run_once(target_event_id: Optional[int] = None) -> dict:
    """Fetch active events, poll SH+TP, push results. Returns run summary."""
    if not SECRET:
        logger.error("LOCAL_COLLECTOR_SECRET not set — cannot push to Railway")
        sys.exit(1)

    t_start = time.monotonic()

    async with httpx.AsyncClient(timeout=30.0) as http:
        # Fetch active events from Railway
        try:
            resp = await http.get(EVENTS_URL)
            resp.raise_for_status()
            events = resp.json()
        except Exception as exc:
            logger.error("Failed to fetch events from Railway: %s", exc)
            return {"error": str(exc)}

    active_events = [e for e in events if e.get("is_active")]
    if target_event_id:
        active_events = [e for e in active_events if e["id"] == target_event_id]

    logger.info("Active events: %d%s", len(active_events),
                f" (filtered to id={target_event_id})" if target_event_id else "")

    tasks = []
    results = []
    total_listings = 0
    ok_count = 0
    err_count = 0

    async with httpx.AsyncClient(timeout=60.0) as http:
        for event in active_events:
            for te in event.get("tracked_events", []):
                if not te.get("is_active"):
                    continue
                slug = te.get("marketplace_slug")
                if slug not in TARGET_MARKETPLACES:
                    continue
                # Skip if no external_event_id and no external_url
                if not te.get("external_event_id") and not te.get("external_url"):
                    logger.debug("Skipping te=%d %s — no id/url", te["id"], slug)
                    continue

                summary = await _run_one_marketplace(http, slug, te, event)
                results.append(summary)
                n = summary.get("listings_found", 0)
                total_listings += n
                if summary.get("error"):
                    err_count += 1
                else:
                    ok_count += 1

    elapsed = time.monotonic() - t_start

    heartbeat = {
        "collector_version": COLLECTOR_VERSION,
        "marketplaces_attempted": len(results),
        "marketplaces_ok": ok_count,
        "events_polled": len(set(r.get("te_id") for r in results)),
        "total_listings": total_listings,
        "elapsed_s": round(elapsed, 1),
        "error": None if err_count == 0 else f"{err_count} errors",
    }

    if not DRY_RUN:
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                await http.post(
                    HEARTBEAT_URL,
                    json=heartbeat,
                    headers={"Authorization": f"Bearer {SECRET}"},
                )
        except Exception as exc:
            logger.warning("Heartbeat failed: %s", exc)

    logger.info(
        "RUN COMPLETE: %d marketplaces, %d ok, %d errors, %d total listings, %.1fs",
        len(results), ok_count, err_count, total_listings, elapsed,
    )
    return {**heartbeat, "results": results}


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Local Mac ticket collector")
    parser.add_argument("--once", action="store_true", help="Run once and exit (default)")
    parser.add_argument("--event-id", type=int, help="Only poll this event ID")
    args = parser.parse_args()

    if DRY_RUN:
        logger.info("DRY_RUN mode — listings fetched but not pushed to Railway")

    summary = asyncio.run(run_once(args.event_id))
    if summary.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
