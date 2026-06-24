#!/usr/bin/env python3
"""
Local Mac collector — runs StubHub, TickPick, and SeatGeek collectors from this
machine (residential IP, no DataDome/403 blocks) and pushes results to Railway.

Canonical cadence (mirrors Railway scheduler compute_poll_interval_minutes):
  > 30d    → daily      (1440 min)
  14–30d   → twice/day  ( 720 min)
   7–14d   → 8h         ( 480 min)
   3–7d    → 4h         ( 240 min)
   1–3d    → hourly     (  60 min)
   6–24h   → 30 min
  90m–6h   → 15 min
  30–90m   → 5 min
   0–30m   → 2 min
  post-start until exhaustion → 2 min

Run via cron at */2 * * * * — each invocation checks per-TE cadence and skips
TEs whose next_poll_at has not yet elapsed.  State tracked in local JSON file.

Usage:
    python3 scripts/local_collector.py [--once] [--event-id EVENT_ID] [--force]
    python3 scripts/local_collector.py --status

Required env (in .env.local):
    RAILWAY_BASE_URL
    LOCAL_COLLECTOR_SECRET
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

# ── Bootstrap ─────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv
for _f in [_REPO_ROOT / ".env.local", _REPO_ROOT / ".env"]:
    if _f.exists():
        load_dotenv(_f, override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("local_collector")

# ── Config ────────────────────────────────────────────────────────────────────
RAILWAY_BASE  = os.environ.get("RAILWAY_BASE_URL", "https://backend-production-509f.up.railway.app")
SECRET        = os.environ.get("LOCAL_COLLECTOR_SECRET", "")
DRY_RUN       = os.environ.get("LOCAL_COLLECTOR_DRY_RUN", "0") == "1"
TARGET_MARKETPLACES = [
    m.strip() for m in
    os.environ.get("LOCAL_COLLECTOR_MARKETPLACES", "stubhub,tickpick,seatgeek").split(",")
    if m.strip()
]

COLLECTOR_VERSION = "local_mac_v2"
INGEST_URL    = f"{RAILWAY_BASE}/api/collect/ingest"
HEARTBEAT_URL = f"{RAILWAY_BASE}/api/collect/heartbeat"
EVENTS_URL    = f"{RAILWAY_BASE}/api/events"

# Local cadence state file — tracks last_polled_at per (event_id, marketplace)
_STATE_FILE = _REPO_ROOT / ".local_collector_state.json"

# ── Canonical cadence (mirrors Railway scheduler) ─────────────────────────────

def _compute_interval_minutes(event_date_str: Optional[str]) -> int:
    """Return poll interval in minutes based on time until event."""
    if not event_date_str:
        return 60
    try:
        ed = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
    except Exception:
        return 60
    now = datetime.now(timezone.utc)
    seconds = (ed - now).total_seconds()
    if seconds < 0:             return 2     # post-start, live
    if seconds < 30 * 60:       return 2     # 0–30 min
    if seconds < 90 * 60:       return 5     # 30–90 min
    if seconds < 6 * 3600:      return 15    # 90 min – 6 h
    if seconds < 24 * 3600:     return 30    # 6–24 h
    if seconds < 3 * 86400:     return 60    # 1–3 days
    if seconds < 7 * 86400:     return 240   # 3–7 days
    if seconds < 14 * 86400:    return 480   # 7–14 days
    if seconds < 30 * 86400:    return 720   # 14–30 days
    return 1440                              # > 30 days

# ── Local cadence state ───────────────────────────────────────────────────────

def _load_state() -> dict:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_state(state: dict):
    try:
        _STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as exc:
        logger.warning("Failed to save state: %s", exc)

def _is_due(state: dict, key: str, interval_minutes: int) -> bool:
    last = state.get(key)
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - last_dt).total_seconds() >= interval_minutes * 60
    except Exception:
        return True

def _mark_polled(state: dict, key: str):
    state[key] = datetime.now(timezone.utc).isoformat()

# ── Self-healing: historical baseline tracking ────────────────────────────────

_BASELINE_FILE = _REPO_ROOT / ".local_collector_baselines.json"

def _load_baselines() -> dict:
    if _BASELINE_FILE.exists():
        try:
            return json.loads(_BASELINE_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_baselines(baselines: dict):
    try:
        _BASELINE_FILE.write_text(json.dumps(baselines, indent=2))
    except Exception:
        pass

def _check_and_update_baseline(baselines: dict, key: str, count: int) -> Optional[str]:
    """
    Compare count against historical best.  Returns warning string if regression
    detected (count < 50% of best and best was meaningful).
    Updates baseline if count is new high.
    """
    best = baselines.get(key, {}).get("best", 0)
    if count > best:
        baselines[key] = {"best": count, "at": datetime.now(timezone.utc).isoformat()}
        _save_baselines(baselines)
        return None
    if best >= 10 and count < best * 0.5:
        return f"REGRESSION: {key} got {count} listings vs historical best {best} (< 50%)"
    return None

# ── Fake TrackedEvent ─────────────────────────────────────────────────────────

class _FakeTrackedEvent:
    def __init__(self, te_id, event_id, external_event_id, external_url, marketplace_id,
                 poll_interval_minutes=60):
        self.id = te_id
        self.event_id = event_id
        self.external_event_id = external_event_id
        self.external_url = external_url
        self.marketplace_id = marketplace_id
        self.poll_interval_minutes = poll_interval_minutes
        self.event = None
        self.is_active = True
        self.consecutive_zero_inventory_count = 0

# ── Core poll logic ───────────────────────────────────────────────────────────

async def _run_one_marketplace(
    http: httpx.AsyncClient,
    slug: str,
    te_data: dict,
    event_data: dict,
    baselines: dict,
) -> dict:
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

    # Self-healing: check against historical baseline
    bl_key = f"{slug}:{te_data['id']}"
    regression_warn = _check_and_update_baseline(baselines, bl_key, n)
    if regression_warn:
        logger.warning("SELF-HEAL: %s — triggering retry", regression_warn)
        # One retry with fresh collector
        try:
            collector2 = collector_cls(settings)
            result2 = await collector2.collect(te)
            await collector2.close()
            if len(result2.listings) > n:
                logger.info("SELF-HEAL retry: %s te=%d improved %d → %d", slug, te_data["id"], n, len(result2.listings))
                result = result2
                n = len(result.listings)
        except Exception as exc2:
            logger.warning("SELF-HEAL retry failed: %s", exc2)

    logger.info("%s te=%d event=%d listings=%d elapsed=%.1fs err=%s",
                slug, te_data["id"], event_data["id"], n, elapsed, result.error)

    if DRY_RUN:
        logger.info("DRY_RUN: would push %d listings", n)
        return {"slug": slug, "te_id": te_data["id"], "listings_found": n, "dry_run": True}

    if result.error and n == 0:
        return {"slug": slug, "te_id": te_data["id"], "error": result.error, "listings_found": 0}

    listings_payload = [
        {
            "external_listing_id": r.external_listing_id,
            "section": r.section,
            "row": r.row,
            "quantity": r.quantity,
            "price": str(r.price),
            "fees": str(r.fees) if r.fees else None,
            "all_in_price": str(r.all_in_price) if r.all_in_price else None,
            "listing_url": r.listing_url,
            "market_segment": r.market_segment or "secondary_resale",
        }
        for r in result.listings
    ]

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
        logger.info("PUSHED: %s te=%d listings_accepted=%d poll_run=%s",
                    slug, te.id, rj.get("listings_accepted", "?"), rj.get("poll_run_id", "?"))
        return {"slug": slug, "te_id": te.id, "listings_found": n, "poll_run_id": rj.get("poll_run_id")}
    except Exception as exc:
        logger.error("PUSH_FAILED: %s te=%d — %s", slug, te.id, exc)
        return {"slug": slug, "te_id": te.id, "error": f"push_failed:{exc}", "listings_found": n}

# ── Status display ────────────────────────────────────────────────────────────

def _print_status():
    """Print cadence status for all active events."""
    import urllib.request
    state = _load_state()
    baselines = _load_baselines()
    try:
        events = json.loads(urllib.request.urlopen(EVENTS_URL).read())
    except Exception as exc:
        print(f"Cannot fetch events: {exc}")
        return

    now = datetime.now(timezone.utc)
    print(f"\n{'Event':>6}  {'Phase':>12}  {'Expected':>10}  {'SH last':>12}  {'TP last':>12}  {'Due':>5}")
    print("-" * 75)
    for event in sorted(events, key=lambda e: e.get("event_date") or ""):
        if not event.get("is_active"):
            continue
        ed_str = event.get("event_date")
        interval = _compute_interval_minutes(ed_str)
        if ed_str:
            ed = datetime.fromisoformat(ed_str.replace("Z", "+00:00"))
            diff_h = (ed - now).total_seconds() / 3600
            if diff_h < 0:
                phase = "live"
            elif diff_h < 1:
                phase = "<1h"
            elif diff_h < 24:
                phase = f"{diff_h:.0f}h"
            elif diff_h < 24 * 7:
                phase = f"{diff_h/24:.1f}d"
            else:
                phase = f"{diff_h/24:.0f}d"
        else:
            phase = "?"

        eid = event["id"]
        sh_key = f"stubhub:{eid}"
        tp_key = f"tickpick:{eid}"
        sh_last = state.get(sh_key, "never")[:16] if state.get(sh_key) else "never"
        tp_last = state.get(tp_key, "never")[:16] if state.get(tp_key) else "never"
        due_sh = "Y" if _is_due(state, sh_key, interval) else "N"
        due_tp = "Y" if _is_due(state, tp_key, interval) else "N"
        due = f"{due_sh}/{due_tp}"

        interval_str = f"{interval}m" if interval < 60 else (f"{interval//60}h" if interval % 60 == 0 else f"{interval}m")
        print(f"{eid:>6}  {phase:>12}  {interval_str:>10}  {sh_last:>12}  {tp_last:>12}  {due:>5}")

# ── Main run loop ─────────────────────────────────────────────────────────────

async def run_once(target_event_id: Optional[int] = None, force: bool = False) -> dict:
    if not SECRET:
        logger.error("LOCAL_COLLECTOR_SECRET not set")
        sys.exit(1)

    t_start = time.monotonic()
    state = _load_state()
    baselines = _load_baselines()

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http:
        try:
            resp = await http.get(EVENTS_URL)
            resp.raise_for_status()
            events = resp.json()
        except Exception as exc:
            logger.error("Failed to fetch events: %s", exc)
            return {"error": str(exc)}

    active_events = [e for e in events if e.get("is_active")]
    if target_event_id:
        active_events = [e for e in active_events if e["id"] == target_event_id]

    results = []
    total_listings = 0
    ok_count = 0
    err_count = 0
    skipped_count = 0

    cadence_report = []

    async with httpx.AsyncClient(timeout=90.0) as http:
        for event in active_events:
            ed_str = event.get("event_date")
            interval = _compute_interval_minutes(ed_str)
            eid = event["id"]

            for te in event.get("tracked_events", []):
                if not te.get("is_active"):
                    continue
                slug = te.get("marketplace_slug")
                if slug not in TARGET_MARKETPLACES:
                    continue
                if not te.get("external_event_id") and not te.get("external_url"):
                    continue

                state_key = f"{slug}:{eid}"
                due = force or _is_due(state, state_key, interval)

                # Cadence report entry (always record, even if skipping)
                cadence_report.append({
                    "event_id": eid,
                    "slug": slug,
                    "interval_min": interval,
                    "due": due,
                    "last": state.get(state_key, "never"),
                })

                if not due:
                    skipped_count += 1
                    logger.debug("SKIP: %s event=%d (interval=%dm, not due)", slug, eid, interval)
                    continue

                summary = await _run_one_marketplace(http, slug, te, event, baselines)
                results.append(summary)
                n = summary.get("listings_found", 0)
                total_listings += n

                if summary.get("error"):
                    err_count += 1
                else:
                    ok_count += 1
                    _mark_polled(state, state_key)

    _save_state(state)

    elapsed = time.monotonic() - t_start
    heartbeat = {
        "collector_version": COLLECTOR_VERSION,
        "marketplaces_attempted": len(results),
        "marketplaces_ok": ok_count,
        "events_polled": len({r.get("te_id") for r in results}),
        "total_listings": total_listings,
        "elapsed_s": round(elapsed, 1),
        "skipped": skipped_count,
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
        "RUN COMPLETE: %d polled, %d ok, %d errors, %d skipped, %d listings, %.1fs",
        len(results), ok_count, err_count, skipped_count, total_listings, elapsed,
    )
    return {**heartbeat, "results": results, "cadence": cadence_report}


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--event-id", type=int)
    parser.add_argument("--force", action="store_true", help="Ignore cadence — poll everything now")
    parser.add_argument("--status", action="store_true", help="Print cadence status table")
    args = parser.parse_args()

    if args.status:
        _print_status()
        return

    if DRY_RUN:
        logger.info("DRY_RUN mode")

    summary = asyncio.run(run_once(args.event_id, force=args.force))
    if summary.get("error") and not summary.get("results"):
        sys.exit(1)


if __name__ == "__main__":
    main()
