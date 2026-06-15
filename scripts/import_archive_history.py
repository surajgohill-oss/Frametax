#!/usr/bin/env python3
"""
Import pre-aggregated historical data from local archive DB into Railway backend.

Maps old archive event IDs → current Railway event IDs (high-confidence only):
  3  → 37  (NFL Preseason: 49ers at Chargers, 2026-08-20)
  6  → 33  (BTS World Tour, 2026-09-01)
  7  → 34  (BTS World Tour, 2026-09-02)
  8  → 35  (BTS World Tour, 2026-09-05)
  13 → 32  (Foo Fighters & LA Philharmonic, 2026-08-22)
  26 → 29  (Morgan Jay, 2026-09-12)
  27 → 30  (Morgan Jay, 2026-09-17)

Reads from: local concert_tracker_archive PostgreSQL DB
Writes to:  Railway backend via POST /api/debug/import-history-agg
"""

import json
import sys
import urllib.request
import urllib.error
import psycopg2
from datetime import timezone

MAPPING = {3: 37, 6: 33, 7: 34, 8: 35, 13: 32, 26: 29, 27: 30}

RAILWAY_URL = "https://backend-production-509f.up.railway.app"

ARCHIVE_DSN = "dbname=concert_tracker_archive"

BUCKET_SIZES = [
    ("1h",  "date_trunc('hour', snapshot_at)"),
    ("6h",  "to_timestamp(floor(extract(epoch from snapshot_at) / 21600) * 21600)"),
    ("12h", "to_timestamp(floor(extract(epoch from snapshot_at) / 43200) * 43200)"),
    ("1d",  "date_trunc('day', snapshot_at)"),
]

DRY_RUN = "--dry-run" in sys.argv


def compute_agg_rows(conn, old_id: int, new_id: int) -> list[dict]:
    rows = []
    cur = conn.cursor()
    for bucket_label, bucket_expr in BUCKET_SIZES:
        cur.execute(f"""
            SELECT
                {bucket_expr}                                             AS bucket_ts,
                MIN(price)                                                AS low_ask,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)       AS median_ask,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY price)       AS high_ask,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price)      AS p25_ask,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price)      AS p75_ask,
                COUNT(DISTINCT listing_id)                                AS listing_count,
                SUM(quantity)                                             AS ticket_count,
                COUNT(DISTINCT marketplace_id)                            AS marketplace_count
            FROM listing_snapshots_archive
            WHERE event_id = %s
              AND price IS NOT NULL
              AND price > 0
            GROUP BY bucket_ts
            ORDER BY bucket_ts ASC
        """, (old_id,))
        for r in cur.fetchall():
            bucket_ts, low, med, high, p25, p75, lc, tc, mc = r
            if bucket_ts is None:
                continue
            # Normalize to naive UTC ISO string for JSON transport
            if hasattr(bucket_ts, 'tzinfo') and bucket_ts.tzinfo is not None:
                bucket_ts = bucket_ts.astimezone(timezone.utc).replace(tzinfo=None)
            rows.append({
                "railway_event_id": new_id,
                "bucket_ts":        bucket_ts.isoformat(),
                "bucket_size":      bucket_label,
                "low_ask":          float(low) if low is not None else None,
                "median_ask":       float(med) if med is not None else None,
                "high_ask":         float(high) if high is not None else None,
                "p25_ask":          float(p25) if p25 is not None else None,
                "p75_ask":          float(p75) if p75 is not None else None,
                "listing_count":    int(lc) if lc is not None else None,
                "ticket_count":     int(tc) if tc is not None else None,
                "marketplace_count": int(mc) if mc is not None else None,
            })
    cur.close()
    return rows


def post_rows(all_rows: list[dict]) -> dict:
    body = json.dumps({"rows": all_rows}).encode()
    req = urllib.request.Request(
        f"{RAILWAY_URL}/api/debug/import-history-agg",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def main():
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE IMPORT'}")
    print(f"Archive DSN: {ARCHIVE_DSN}")
    print(f"Railway URL: {RAILWAY_URL}")
    print()

    conn = psycopg2.connect(ARCHIVE_DSN)
    all_rows = []

    print(f"{'old_id':>6}  {'new_id':>6}  {'buckets':>8}  {'oldest':^23}  {'newest':^23}")
    print("-" * 80)

    for old_id, new_id in sorted(MAPPING.items()):
        rows = compute_agg_rows(conn, old_id, new_id)
        all_rows.extend(rows)
        if rows:
            oldest = min(r["bucket_ts"] for r in rows)
            newest = max(r["bucket_ts"] for r in rows)
        else:
            oldest = newest = "—"
        print(f"{old_id:>6}  {new_id:>6}  {len(rows):>8}  {oldest[:23]:^23}  {newest[:23]:^23}")

    conn.close()

    print()
    print(f"Total rows to import: {len(all_rows)}")
    print(f"Breakdown by bucket_size:")
    from collections import Counter
    for size, count in sorted(Counter(r["bucket_size"] for r in all_rows).items()):
        print(f"  {size}: {count} rows")

    if DRY_RUN:
        print("\nDRY RUN — no data sent to Railway.")
        print("Run without --dry-run to import.")
        return

    print("\nPosting to Railway...")
    result = post_rows(all_rows)
    print(f"Result: inserted={result['inserted']}  skipped={result['skipped']}  total={result['total']}")


if __name__ == "__main__":
    main()
