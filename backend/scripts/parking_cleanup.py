"""
Phase 1E-C: Retroactive Parking Cleanup (Task 7)
=================================================
Deactivates all currently-active parking listings.

Uses the same is_parking_listing() logic as the ingestion filter so
the cleanup is exactly consistent with what the filter would have
prevented if it had been live from the start.

Safety:
  - Dry-run by default (--execute to commit)
  - Only sets is_active=False — no DELETEs ever
  - Processes in batches; rolls back entire batch on any error

Usage:
    python3 scripts/parking_cleanup.py             # dry-run
    python3 scripts/parking_cleanup.py --execute   # live
"""

import argparse
import sys
import os
from datetime import datetime, timezone

# Allow running from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.collectors.normalize import is_parking_listing

import psycopg2
import psycopg2.extras

DB_URL = (
    "postgresql://postgres:jOhylgsBSCdUhFXUChzNfkEvBAmuGsIP"
    "@switchback.proxy.rlwy.net:43266/railway"
)

BATCH_SIZE = 500


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                        help="Apply changes (default: dry-run)")
    args = parser.parse_args()
    dry_run = not args.execute

    mode = "DRY RUN — NO CHANGES" if dry_run else "LIVE EXECUTION"
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n{'='*70}")
    print(f"  PHASE 1E-C PARKING CLEANUP  [{mode}]")
    print(f"  {ts}")
    print(f"{'='*70}")

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # ── Fetch all active listings ──────────────────────────────────────────
    print("\nFetching all active listings …")
    cur.execute("""
        SELECT l.id, l.section, l.row, m.slug AS marketplace, e.title AS event_title
        FROM listings l
        JOIN marketplaces m ON m.id = l.marketplace_id
        JOIN events e ON e.id = l.event_id
        WHERE l.is_active = true
        ORDER BY l.id
    """)
    all_listings = cur.fetchall()
    print(f"  Total active listings: {len(all_listings)}")

    # ── Classify each listing ──────────────────────────────────────────────
    to_deactivate: list[int] = []
    parking_by_mp: dict[str, int] = {}
    parking_by_event: dict[str, int] = {}

    for l in all_listings:
        if is_parking_listing(l["section"], l["row"]):
            to_deactivate.append(l["id"])
            mp = l["marketplace"]
            parking_by_mp[mp] = parking_by_mp.get(mp, 0) + 1
            key = f"{l['event_title'][:45]}"
            parking_by_event[key] = parking_by_event.get(key, 0) + 1

    print(f"\n  Listings classified as parking: {len(to_deactivate)}")
    print(f"  By marketplace:")
    for mp, cnt in sorted(parking_by_mp.items()):
        print(f"    {mp:12s}: {cnt}")
    print(f"  By event (top 15):")
    for event, cnt in sorted(parking_by_event.items(), key=lambda x: -x[1])[:15]:
        print(f"    {cnt:4d}  {event}")

    if not to_deactivate:
        print("\n  ✅ No parking listings to deactivate")
        conn.close()
        return

    # ── Deactivate in batches ─────────────────────────────────────────────
    try:
        total_deactivated = 0
        for batch_start in range(0, len(to_deactivate), BATCH_SIZE):
            batch = to_deactivate[batch_start:batch_start + BATCH_SIZE]
            if not dry_run:
                cur.execute(
                    "UPDATE listings SET is_active = false WHERE id = ANY(%s)",
                    (batch,)
                )
                total_deactivated += cur.rowcount
            else:
                total_deactivated += len(batch)

        if not dry_run:
            conn.commit()
            print(f"\n  ✅ COMMITTED — deactivated {total_deactivated} parking listings")
        else:
            conn.rollback()
            print(f"\n  ℹ  DRY RUN — would deactivate {total_deactivated} parking listings")

    except Exception as exc:
        conn.rollback()
        print(f"\n  ❌ ERROR: {exc}")
        conn.close()
        sys.exit(1)

    # ── Post-run verification ─────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print("Post-run verification: active parking listings remaining")
    # Re-check after commit (or dry-run using original data)
    if not dry_run:
        cur.execute("""
            SELECT COUNT(*) FROM listings l
            JOIN marketplaces m ON m.id = l.marketplace_id
            WHERE l.is_active = true
              AND (
                  l.section ~* '\\mparking\\M'
               OR l.section ~* '\\mgarage\\M'
               OR l.section ~* '\\blot\\b'
               OR l.section ~* '\\bvalet\\b'
               OR upper(l.row) ~ '^PRK'
               OR upper(l.row) IN ('PARKING', 'PARK')
              )
        """)
        remaining = cur.fetchone()[0]
        print(f"  Active parking listings after cleanup: {remaining}")
        if remaining == 0:
            print("  ✅ Zero parking listings remain active")
        else:
            print(f"  ⚠  {remaining} parking-adjacent listings still active (may be section-name edge cases)")

    conn.close()


if __name__ == "__main__":
    main()
