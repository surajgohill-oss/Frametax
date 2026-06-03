"""
Phase 1E-B: Reconciliation Backup Snapshot
===========================================
Exports all data for each duplicate group before any modification.
Run before any reconciliation SQL.

Usage:
    python3 scripts/phase1eb_snapshot.py

Output:
    scripts/snapshots/phase1eb_<group>_<timestamp>.json  (one per group)
    scripts/snapshots/phase1eb_summary_<timestamp>.json  (counts summary)
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

GROUPS = {
    "group1_ariana_jun13": {
        "description": "Ariana Grande Jun13 — title mismatch (HIGH RISK)",
        "survivor_id": 11,
        "ghost_id": 19,
    },
    "group2_diljit": {
        "description": "Diljit Dosanjh — SeatGeek UTC/local date mismatch (LOW RISK)",
        "survivor_id": 25,
        "ghost_id": 30,
    },
    "group3_chance": {
        "description": "Chance the Rapper — SeatGeek UTC/local date mismatch (LOW RISK)",
        "survivor_id": 28,
        "ghost_id": 31,
    },
    "group4_reggae": {
        "description": "Reggae Night XXIV — SeatGeek UTC/local date mismatch (LOW RISK)",
        "survivor_id": 29,
        "ghost_id": 32,
    },
}

TIMESTAMP = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")


def rows_to_dicts(cursor):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def serialize_row(row):
    """Convert non-JSON-serializable types (datetime, Decimal) to strings."""
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif hasattr(v, "__float__"):
            out[k] = float(v)
        else:
            out[k] = v
    return out


def export_group(conn, group_name, group_info):
    survivor_id = group_info["survivor_id"]
    ghost_id    = group_info["ghost_id"]
    event_ids   = [survivor_id, ghost_id]

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    snapshot = {
        "group":       group_name,
        "description": group_info["description"],
        "survivor_id": survivor_id,
        "ghost_id":    ghost_id,
        "snapshot_ts": TIMESTAMP,
        "events":             [],
        "tracked_events":     [],
        "listings":           [],
        "listing_snapshots":  [],
        "poll_runs":          [],
        "venues":             [],
    }

    # Events
    cur.execute("SELECT * FROM events WHERE id = ANY(%s) ORDER BY id", (event_ids,))
    snapshot["events"] = [serialize_row(dict(r)) for r in cur.fetchall()]

    # Venues for these events
    venue_ids = [e["venue_id"] for e in snapshot["events"] if e.get("venue_id")]
    if venue_ids:
        cur.execute("SELECT * FROM venues WHERE id = ANY(%s)", (venue_ids,))
        snapshot["venues"] = [serialize_row(dict(r)) for r in cur.fetchall()]

    # TrackedEvents
    cur.execute(
        "SELECT te.*, m.slug AS marketplace_slug FROM tracked_events te "
        "JOIN marketplaces m ON te.marketplace_id = m.id "
        "WHERE te.event_id = ANY(%s) ORDER BY te.event_id, m.slug",
        (event_ids,),
    )
    snapshot["tracked_events"] = [serialize_row(dict(r)) for r in cur.fetchall()]

    te_ids = [te["id"] for te in snapshot["tracked_events"]]

    # Listings (active and inactive)
    cur.execute(
        "SELECT l.*, m.slug AS marketplace_slug FROM listings l "
        "JOIN marketplaces m ON l.marketplace_id = m.id "
        "WHERE l.event_id = ANY(%s) ORDER BY l.event_id, m.slug, l.id",
        (event_ids,),
    )
    snapshot["listings"] = [serialize_row(dict(r)) for r in cur.fetchall()]

    # PollRuns
    if te_ids:
        cur.execute(
            "SELECT pr.* FROM poll_runs pr "
            "WHERE pr.tracked_event_id = ANY(%s) "
            "ORDER BY pr.tracked_event_id, pr.started_at DESC",
            (te_ids,),
        )
        snapshot["poll_runs"] = [serialize_row(dict(r)) for r in cur.fetchall()]

    # ListingSnapshots (may not exist on all deployments)
    try:
        cur.execute(
            "SELECT ls.* FROM listing_snapshots ls "
            "WHERE ls.event_id = ANY(%s) ORDER BY ls.event_id, ls.id",
            (event_ids,),
        )
        snapshot["listing_snapshots"] = [serialize_row(dict(r)) for r in cur.fetchall()]
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        snapshot["listing_snapshots"] = []
        snapshot["listing_snapshots_note"] = "table does not exist"

    # Summary counts
    snapshot["counts"] = {
        "events":             len(snapshot["events"]),
        "tracked_events":     len(snapshot["tracked_events"]),
        "listings_total":     len(snapshot["listings"]),
        "listings_active":    sum(1 for l in snapshot["listings"] if l.get("is_active")),
        "listings_inactive":  sum(1 for l in snapshot["listings"] if not l.get("is_active")),
        "listing_snapshots":  len(snapshot["listing_snapshots"]),
        "poll_runs":          len(snapshot["poll_runs"]),
    }

    # Per-event breakdown
    for eid in event_ids:
        role = "survivor" if eid == survivor_id else "ghost"
        tes   = [te for te in snapshot["tracked_events"] if te["event_id"] == eid]
        ls    = [l  for l  in snapshot["listings"]       if l["event_id"]  == eid]
        prs   = [pr for pr in snapshot["poll_runs"]
                 if pr["tracked_event_id"] in {te["id"] for te in tes}]
        snapshot[f"{role}_summary"] = {
            "event_id":          eid,
            "tracked_events":    len(tes),
            "marketplaces":      [te["marketplace_slug"] for te in tes],
            "listings_active":   sum(1 for l in ls if l.get("is_active")),
            "listings_inactive": sum(1 for l in ls if not l.get("is_active")),
            "poll_runs":         len(prs),
            "te_external_ids":   {te["marketplace_slug"]: te.get("external_event_id") for te in tes},
        }

    cur.close()
    return snapshot


def main():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    print(f"Connecting to Railway Postgres … ({TIMESTAMP})")

    conn = psycopg2.connect(DB_URL)
    conn.set_session(readonly=True, autocommit=True)

    summary = {"snapshot_ts": TIMESTAMP, "groups": {}}
    files   = []

    for group_name, group_info in GROUPS.items():
        print(f"  Exporting {group_name} …")
        snapshot = export_group(conn, group_name, group_info)

        fname = f"phase1eb_{group_name}_{TIMESTAMP}.json"
        fpath = os.path.join(SNAPSHOT_DIR, fname)
        with open(fpath, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)

        files.append(fpath)
        summary["groups"][group_name] = {
            "file":    fname,
            "counts":  snapshot["counts"],
            "survivor_summary": snapshot["survivor_summary"],
            "ghost_summary":    snapshot["ghost_summary"],
        }
        print(f"    → {fname}  events={snapshot['counts']['events']}  "
              f"te={snapshot['counts']['tracked_events']}  "
              f"listings_active={snapshot['counts']['listings_active']}  "
              f"poll_runs={snapshot['counts']['poll_runs']}")

    conn.close()

    summary_fname = f"phase1eb_summary_{TIMESTAMP}.json"
    summary_fpath = os.path.join(SNAPSHOT_DIR, summary_fname)
    with open(summary_fpath, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    files.append(summary_fpath)

    print(f"\nSnapshot summary → {summary_fname}")
    print(f"\nFiles written:")
    for fp in files:
        size = os.path.getsize(fp)
        print(f"  {fp}  ({size:,} bytes)")

    return summary


if __name__ == "__main__":
    main()
