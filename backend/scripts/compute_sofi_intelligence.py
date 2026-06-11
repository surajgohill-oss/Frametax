#!/usr/bin/env python3
"""
compute_sofi_intelligence.py — Compute venue intelligence for all active SoFi events.

Can be run locally (requires DATABASE_URL in env) or triggered remotely
via the API endpoint POST /api/venues/sofi-stadium/compute?event_id=N.

Usage (local, direct DB):
  DATABASE_URL=... python3 backend/scripts/compute_sofi_intelligence.py

Usage (API):
  python3 backend/scripts/compute_sofi_intelligence.py --api https://backend-production-509f.up.railway.app

Outputs a summary table to stdout.
"""
import argparse
import asyncio
import os
import sys
import urllib.request
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

VENUE_SLUG = "sofi-stadium"


# ── API mode (hit the deployed endpoint) ─────────────────────────────────────

def run_via_api(base_url: str):
    base_url = base_url.rstrip("/")

    # 1. Get active SoFi events
    with urllib.request.urlopen(f"{base_url}/api/events/?limit=200", timeout=30) as r:
        events = json.load(r)

    sofi_events = [e for e in events if e.get("venue_slug") == VENUE_SLUG or
                   (isinstance(e.get("venue"), dict) and e["venue"].get("slug") == VENUE_SLUG)]
    if not sofi_events:
        print(f"No active events found for venue slug '{VENUE_SLUG}'")
        return

    print(f"Found {len(sofi_events)} SoFi event(s). Computing intelligence...")
    print()

    hdr = "{:<8} {:<40} {:<7} {:<13} {:<14} {}"
    print(hdr.format("event_id", "event_name", "total", "with_metrics", "cls_buckets/6", "status"))
    print("-" * 100)

    for e in sorted(sofi_events, key=lambda x: x.get("event_date", "")):
        eid = e["id"]
        ename = e.get("title", "?")

        # Compute
        req = urllib.request.Request(
            f"{base_url}/api/venues/{VENUE_SLUG}/compute?event_id={eid}",
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            compute = json.load(r)
        computed = compute.get("sections_computed", 0)

        # Intelligence
        with urllib.request.urlopen(
            f"{base_url}/api/venues/{VENUE_SLUG}/intelligence?event_id={eid}", timeout=30
        ) as r:
            intel = json.load(r)
        total = intel.get("sections_total", 0)
        with_m = intel.get("sections_with_metrics", 0)

        # Classifications
        with urllib.request.urlopen(
            f"{base_url}/api/venues/{VENUE_SLUG}/classifications?event_id={eid}", timeout=30
        ) as r:
            cls = json.load(r)
        cls_present = sum(1 for v in cls.get("classifications", {}).values() if v)

        status = "OK" if with_m > 0 and cls_present >= 2 else "WARN"
        print(hdr.format(eid, ename[:39], total, with_m, f"{cls_present}/6", status))

    print()
    print("Done.")


# ── DB mode (direct SQLAlchemy, for Railway one-off tasks) ───────────────────

async def run_via_db():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    from app.database import AsyncSessionLocal
    from app.services.venue_intelligence import compute_section_metrics, get_venue_intelligence, get_classifications
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text("""
            SELECT e.id, e.title
            FROM events e
            JOIN venues v ON v.id = e.venue_id
            WHERE v.slug = :slug
              AND e.event_date >= NOW()
              AND e.status != 'cancelled'
            ORDER BY e.event_date
        """), {"slug": VENUE_SLUG})).fetchall()

    if not rows:
        print(f"No upcoming events found for venue '{VENUE_SLUG}'")
        return

    print(f"Found {len(rows)} event(s). Computing...")
    hdr = "{:<8} {:<40} {:<13} {:<14} {}"
    print(hdr.format("event_id", "event_name", "with_metrics", "cls_buckets/6", "status"))
    print("-" * 90)

    for row in rows:
        eid, ename = row.id, row.title
        async with AsyncSessionLocal() as db:
            results = await compute_section_metrics(eid, db, venue_slug=VENUE_SLUG)
            sections = await get_venue_intelligence(eid, db, venue_slug=VENUE_SLUG)
        cls = get_classifications(sections)
        with_m = sum(1 for s in sections if s["metrics"])
        cls_present = sum(1 for v in cls.values() if v)
        status = "OK" if with_m > 0 else "WARN"
        print(hdr.format(eid, ename[:39], with_m, f"{cls_present}/6", status))

    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute SoFi venue intelligence for all active events")
    parser.add_argument("--api", metavar="BASE_URL", help="Use API mode (no local DB needed)")
    args = parser.parse_args()

    if args.api:
        run_via_api(args.api)
    else:
        asyncio.run(run_via_db())
