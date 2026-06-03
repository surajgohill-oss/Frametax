"""
Phase 1E-C: Pre-Cleanup Parking Backup Snapshot
================================================
Exports ALL active listings that will be classified as parking by
the new is_parking_listing() filter, before any modification.

Run ONCE before Task 7 (retroactive deactivation).

Output:
    scripts/snapshots/parking_backup_<timestamp>.json
"""

import json
import os
import sys
from datetime import datetime

import psycopg2
import psycopg2.extras

DB_URL = (
    "postgresql://postgres:jOhylgsBSCdUhFXUChzNfkEvBAmuGsIP"
    "@switchback.proxy.rlwy.net:43266/railway"
)

TIMESTAMP = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")


def serialize_row(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif hasattr(v, "__float__"):
            out[k] = float(v)
        else:
            out[k] = v
    return out


def main():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    print(f"Connecting to Railway Postgres … ({TIMESTAMP})")

    conn = psycopg2.connect(DB_URL)
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # ── Broad capture: section-pattern matches OR row indicates parking ───────
    # This intentionally casts a wider net than the 2026-05-31 audit WHERE clause
    # so the backup includes every listing that the new Python filter will drop.
    cur.execute("""
        SELECT
            l.id,
            l.event_id,
            e.title          AS event_title,
            m.slug           AS marketplace,
            l.section,
            l.row,
            l.quantity,
            l.price,
            l.fees,
            l.all_in_price,
            l.external_listing_id,
            l.listing_url,
            l.market_segment,
            l.is_active,
            l.first_seen_at,
            l.last_seen_at
        FROM listings l
        JOIN events e       ON e.id = l.event_id
        JOIN marketplaces m ON m.id = l.marketplace_id
        WHERE l.is_active = true
          AND (
              -- Tier 1: section keyword matches
              l.section ~* '\\mparking\\M'
           OR l.section ~* '\\mgarage\\M'
           OR l.section ~* '\\btailgate\\b'
           OR l.section ~* '\\bpass\\s+only\\b'
           OR l.section ~* '\\blot\\b'
           OR l.section ~* '\\bvalet\\b'
           OR l.section ~* '\\b(blue|green|orange|brown|red|yellow|gold|purple|white|black|silver|gray|grey|flower|retail)\\s+(zone|lot)\\b'
           OR l.section ~* '\\bPS-[0-9]+'
           OR l.section ~* '[0-9]+\\.?[0-9]*\\s+(mi|mile)\\s+(away|from)'
              -- Tier 2: row is an unambiguous parking indicator
           OR upper(l.row) ~ '^PRK'
           OR upper(l.row) IN ('PARKING', 'PARK', 'LOT')
          )
        ORDER BY m.slug, l.event_id, l.id
    """)
    rows = cur.fetchall()

    listings = [serialize_row(dict(r)) for r in rows]

    # Per-marketplace summary
    mp_counts: dict[str, int] = {}
    for l in listings:
        mp_counts[l["marketplace"]] = mp_counts.get(l["marketplace"], 0) + 1

    # Per-event summary
    event_counts: dict[str, int] = {}
    for l in listings:
        key = f"{l['event_id']}:{l['event_title'][:40]}"
        event_counts[key] = event_counts.get(key, 0) + 1

    snapshot = {
        "snapshot_ts":        TIMESTAMP,
        "phase":              "1E-C pre-cleanup",
        "description":        "All active listings that will be deactivated by is_parking_listing()",
        "total_listings":     len(listings),
        "by_marketplace":     mp_counts,
        "by_event":           event_counts,
        "listings":           listings,
    }

    fname  = f"parking_backup_{TIMESTAMP}.json"
    fpath  = os.path.join(SNAPSHOT_DIR, fname)
    with open(fpath, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"  PARKING BACKUP SNAPSHOT")
    print(f"{'='*60}")
    print(f"  Total listings captured: {len(listings)}")
    print(f"  By marketplace:")
    for mp, cnt in sorted(mp_counts.items()):
        print(f"    {mp:12s}: {cnt}")
    print(f"  By event (top 15):")
    for key, cnt in sorted(event_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"    {cnt:4d}  {key}")
    print(f"\n  Snapshot → {fpath}  ({os.path.getsize(fpath):,} bytes)")
    print(f"{'='*60}")

    cur.close()
    conn.close()
    return fpath


if __name__ == "__main__":
    main()
