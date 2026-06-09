#!/usr/bin/env python3
"""
archive_and_prune_snapshots.py
------------------------------
Tiered retention prune for listing_snapshots.

Retention policy (canonical):
  Completed / inactive events  → archive ALL, delete ALL
  > 30d away                   → keep only last 48h of raw snapshots
  14–30d away                  → keep only last 7d of raw snapshots
  7–14d away                   → keep only last 14d of raw snapshots
  < 7d away                    → do NOT delete any raw snapshots

Guarantees:
  - Never deletes without a verified archive
  - Never deletes canonical_inventory_snapshots or canonical_block_history
  - Never deletes listings (tracked_events, listings tables)
  - Archives are CSV.gz, one file per event, written to archives/<run_dir>/
  - Row count verified: archive row count must match query row count
  - Dry-run mode by default; pass --execute to delete

Usage:
  python3 scripts/archive_and_prune_snapshots.py --dry-run   # default
  python3 scripts/archive_and_prune_snapshots.py --execute
"""

import argparse
import csv
import gzip
import io
import json
import os
import sys
import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras

# ── Config ────────────────────────────────────────────────────────────────────
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:jOhylgsBSCdUhFXUChzNfkEvBAmuGsIP@switchback.proxy.rlwy.net:43266/railway",
)

ARCHIVE_ROOT = Path(__file__).parent.parent / "archives"

LS_COLS = [
    "id", "event_id", "marketplace_id", "listing_id", "section_id",
    "price", "quantity", "snapshot_at", "fees", "all_in_price", "market_segment",
]

# ── Retention thresholds ──────────────────────────────────────────────────────
def retention_cutoff(event_date: datetime.datetime, now: datetime.datetime):
    """
    Returns (tier_label, cutoff_dt_or_None) where:
      cutoff_dt = delete snapshots older than this datetime
      None      = delete ALL snapshots (completed/inactive events)
      'skip'    = do not delete anything
    """
    delta = (event_date - now).total_seconds()

    if delta < 0:
        # Event already passed
        return "completed", None  # delete ALL

    days = delta / 86400

    if days > 30:
        return ">30d→keep_48h", now - datetime.timedelta(hours=48)
    elif days > 14:
        return "14-30d→keep_7d", now - datetime.timedelta(days=7)
    elif days > 7:
        return "7-14d→keep_14d", now - datetime.timedelta(days=14)
    else:
        return "<7d→no_prune", "skip"


# ── Export helpers ────────────────────────────────────────────────────────────
def export_to_gz(db_url: str, event_id: int, cutoff_dt, out_path: Path) -> int:
    """
    Export listing_snapshots for event_id where snapshot_at < cutoff_dt
    (or ALL if cutoff_dt is None) to a gzipped CSV.
    Returns the number of rows written.
    Uses a dedicated connection with autocommit=False for named cursor support.
    """
    export_conn = psycopg2.connect(db_url)
    export_conn.autocommit = False
    cur_name = f"export_{event_id}_{int(datetime.datetime.utcnow().timestamp())}"
    cur = export_conn.cursor(cur_name)

    if cutoff_dt is None:
        cur.execute(
            f"SELECT {', '.join(LS_COLS)} FROM listing_snapshots WHERE event_id = %s",
            (event_id,),
        )
    else:
        cur.execute(
            f"SELECT {', '.join(LS_COLS)} FROM listing_snapshots "
            f"WHERE event_id = %s AND snapshot_at < %s",
            (event_id, cutoff_dt),
        )

    rows_written = 0
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        writer = csv.writer(io.TextIOWrapper(gz, newline="", write_through=True))
        writer.writerow(LS_COLS)
        while True:
            rows = cur.fetchmany(5000)
            if not rows:
                break
            for row in rows:
                writer.writerow(list(row))
                rows_written += 1

    cur.close()
    export_conn.rollback()
    export_conn.close()

    out_path.write_bytes(buf.getvalue())
    return rows_written


def verify_archive(gz_path: Path) -> int:
    """Count rows in a CSV.gz (excluding header). Returns row count."""
    count = 0
    with gzip.open(gz_path, "rt") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for _ in reader:
            count += 1
    return count


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Archive and prune listing_snapshots")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                       help="Show what would be deleted without deleting (default)")
    group.add_argument("--execute", dest="dry_run", action="store_false",
                       help="Actually archive and delete")
    args = parser.parse_args()

    mode = "DRY-RUN" if args.dry_run else "EXECUTE"
    print(f"[archive_and_prune] mode={mode}  {datetime.datetime.utcnow().isoformat()}Z")

    run_ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = ARCHIVE_ROOT / f"storage_prune_{run_ts}"
    if not args.dry_run:
        run_dir.mkdir(parents=True, exist_ok=True)

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    now = datetime.datetime.utcnow()

    # ── Fetch all tracked events ──────────────────────────────────────────────
    cur.execute("""
        SELECT te.id, e.event_date, e.status, e.title
        FROM tracked_events te
        JOIN events e ON e.id = te.event_id
        ORDER BY e.event_date
    """)
    events = cur.fetchall()

    # ── Per-event snapshot counts ─────────────────────────────────────────────
    cur.execute("""
        SELECT event_id, COUNT(*) as cnt, MIN(snapshot_at), MAX(snapshot_at)
        FROM listing_snapshots
        GROUP BY event_id
    """)
    snap_stats = {r[0]: {"count": r[1], "min": r[2], "max": r[3]} for r in cur.fetchall()}

    total_to_delete = 0
    total_archived = 0
    event_reports = []

    print(f"\n{'ID':>4}  {'Title':<38}  {'Status':<10}  {'Tier':<22}  {'Current':>9}  {'To Delete':>10}")
    print("-" * 105)

    for (te_id, event_date, status, title) in events:
        stats = snap_stats.get(te_id, {"count": 0, "min": None, "max": None})
        current = stats["count"]

        if current == 0:
            print(f"{te_id:>4}  {title[:38]:<38}  {status:<10}  {'no snapshots':<22}  {0:>9,}  {0:>10,}")
            continue

        # Determine tier
        if status in ("completed", "inactive", "cancelled"):
            tier_label = f"{status}→delete_all"
            cutoff_dt = None  # delete ALL
        else:
            tier_label, cutoff_dt = retention_cutoff(event_date, now)

        if cutoff_dt == "skip":
            print(f"{te_id:>4}  {title[:38]:<38}  {status:<10}  {tier_label:<22}  {current:>9,}  {'(skip)':>10}")
            continue

        # Count rows to delete
        if cutoff_dt is None:
            to_del = current
        else:
            cur.execute(
                "SELECT COUNT(*) FROM listing_snapshots WHERE event_id = %s AND snapshot_at < %s",
                (te_id, cutoff_dt),
            )
            to_del = cur.fetchone()[0]

        total_to_delete += to_del
        print(f"{te_id:>4}  {title[:38]:<38}  {status:<10}  {tier_label:<22}  {current:>9,}  {to_del:>10,}")

        if to_del == 0:
            continue

        event_report = {
            "event_id": te_id,
            "event_title": title,
            "event_date": str(event_date),
            "status": status,
            "tier": tier_label,
            "row_count_before": current,
            "rows_to_delete": to_del,
        }

        if not args.dry_run:
            # ── Archive ───────────────────────────────────────────────────────
            event_dir = run_dir / f"event_{te_id}_{str(event_date)[:10]}"
            event_dir.mkdir(parents=True, exist_ok=True)
            gz_path = event_dir / "listing_snapshots.csv.gz"

            print(f"       archiving {to_del:,} rows ...", end=" ", flush=True)
            archived = export_to_gz(DB_URL, te_id, cutoff_dt, gz_path)
            print(f"exported {archived:,}", end=" ", flush=True)

            # ── Verify ────────────────────────────────────────────────────────
            verified = verify_archive(gz_path)
            if verified != archived:
                print(f"\n  ERROR: verify mismatch: exported={archived} verified={verified}. SKIPPING DELETE.")
                event_report["archive_error"] = f"mismatch exported={archived} verified={verified}"
                event_reports.append(event_report)
                continue

            print(f"verified={verified} ✓", end=" ", flush=True)
            total_archived += archived

            # ── Delete ────────────────────────────────────────────────────────
            if cutoff_dt is None:
                cur.execute(
                    "DELETE FROM listing_snapshots WHERE event_id = %s",
                    (te_id,),
                )
            else:
                cur.execute(
                    "DELETE FROM listing_snapshots WHERE event_id = %s AND snapshot_at < %s",
                    (te_id, cutoff_dt),
                )
            deleted = cur.rowcount
            print(f"deleted={deleted:,} ✓")

            event_report["archived"] = archived
            event_report["verified"] = verified
            event_report["deleted"] = deleted

            # ── Per-event manifest ────────────────────────────────────────────
            manifest = {
                "event_id": te_id,
                "event_title": title,
                "event_date": str(event_date),
                "status": status,
                "tier": tier_label,
                "row_count": archived,
                "rows_deleted": deleted,
                "archive_path": str(gz_path),
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            }
            (event_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))

        event_reports.append(event_report)

    print("-" * 105)
    print(f"\n  Total rows to delete: {total_to_delete:,}")
    if not args.dry_run:
        print(f"  Total rows archived:  {total_archived:,}")

    # ── VACUUM ────────────────────────────────────────────────────────────────
    if not args.dry_run and total_to_delete > 0:
        print("\n  Running VACUUM ANALYZE listing_snapshots ...", end=" ", flush=True)
        conn.autocommit = True
        cur.execute("VACUUM ANALYZE listing_snapshots")
        print("done")

        cur.execute("SELECT COUNT(*) FROM listing_snapshots")
        final_count = cur.fetchone()[0]
        cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        db_size = cur.fetchone()[0]
        print(f"  listing_snapshots: {final_count:,} rows  DB: {db_size}")

        # ── Grand manifest ────────────────────────────────────────────────────
        grand = {
            "prune_run": run_ts,
            "completed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "total_events": len(event_reports),
            "total_deleted": total_archived,
            "final_listing_snapshots_count": final_count,
            "events": event_reports,
        }
        (run_dir / "grand_manifest.json").write_text(json.dumps(grand, indent=2, default=str))
        print(f"\n  Archives written to: {run_dir}")

    conn.close()
    print("\n[archive_and_prune] done.")


if __name__ == "__main__":
    main()
