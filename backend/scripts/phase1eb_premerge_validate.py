"""
Phase 1E-B: Pre-Merge Validation (Task 2)
==========================================
Reconfirms state of all duplicate groups before any reconciliation SQL runs.
Special focus on Ariana Jun13 (Group 1) since both events share identical
external_event_ids across all 4 marketplaces — meaning their listing pools
are from the same actual concert.

Usage:
    python3 scripts/phase1eb_premerge_validate.py
"""

import psycopg2
import psycopg2.extras

DB_URL = (
    "postgresql://postgres:jOhylgsBSCdUhFXUChzNfkEvBAmuGsIP"
    "@switchback.proxy.rlwy.net:43266/railway"
)

GROUPS = {
    "Group 1 — Ariana Jun13": {"survivor": 11, "ghost": 19, "risk": "HIGH"},
    "Group 2 — Diljit":       {"survivor": 25, "ghost": 30, "risk": "LOW"},
    "Group 3 — Chance":       {"survivor": 28, "ghost": 31, "risk": "LOW"},
    "Group 4 — Reggae":       {"survivor": 29, "ghost": 32, "risk": "LOW"},
}


def run(conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    print("=" * 70)
    print("PHASE 1E-B PRE-MERGE VALIDATION")
    print("=" * 70)

    for gname, g in GROUPS.items():
        s, gh = g["survivor"], g["ghost"]
        print(f"\n{'─'*70}")
        print(f"  {gname}  [RISK={g['risk']}]  survivor={s}  ghost={gh}")
        print(f"{'─'*70}")

        # ── Event rows ────────────────────────────────────────────────────
        cur.execute("""
            SELECT e.id, e.title, e.event_date, e.canonical_id, e.artist,
                   v.slug AS venue_slug, e.created_at
            FROM events e
            JOIN venues v ON e.venue_id = v.id
            WHERE e.id = ANY(%s)
            ORDER BY e.id
        """, ([s, gh],))
        for row in cur.fetchall():
            role = "SURVIVOR" if row["id"] == s else "GHOST   "
            print(f"  [{role}] id={row['id']}  date={str(row['event_date'])[:16]}  "
                  f"cid={row['canonical_id']}  title={row['title'][:45]}")

        # ── TrackedEvents ─────────────────────────────────────────────────
        cur.execute("""
            SELECT te.id, te.event_id, m.slug AS mp, te.external_event_id,
                   te.is_active, te.last_polled_at, te.next_poll_at,
                   te.poll_interval_minutes, te.external_url
            FROM tracked_events te
            JOIN marketplaces m ON te.marketplace_id = m.id
            WHERE te.event_id = ANY(%s)
            ORDER BY te.event_id, m.slug
        """, ([s, gh],))
        tes = cur.fetchall()
        print(f"\n  TrackedEvents ({len(tes)} total):")
        for te in tes:
            role = "S" if te["event_id"] == s else "G"
            last = str(te["last_polled_at"])[:16] if te["last_polled_at"] else "never"
            print(f"    [{role}] te_id={te['id']:3d}  event={te['event_id']:2d}  "
                  f"mp={te['mp']:10s}  ext={te['external_event_id']}  "
                  f"active={te['is_active']}  last_poll={last}")

        # ── Active listings per event+marketplace ─────────────────────────
        cur.execute("""
            SELECT l.event_id, m.slug AS mp,
                   COUNT(*) FILTER (WHERE l.is_active) AS active,
                   COUNT(*) FILTER (WHERE NOT l.is_active) AS inactive,
                   MIN(l.price) FILTER (WHERE l.is_active) AS min_price,
                   MAX(l.price) FILTER (WHERE l.is_active) AS max_price
            FROM listings l
            JOIN marketplaces m ON l.marketplace_id = m.id
            WHERE l.event_id = ANY(%s)
            GROUP BY l.event_id, m.slug
            ORDER BY l.event_id, m.slug
        """, ([s, gh],))
        rows = cur.fetchall()
        total_s_active = sum(r["active"] for r in rows if r["event_id"] == s)
        total_gh_active = sum(r["active"] for r in rows if r["event_id"] == gh)
        print(f"\n  Listings by event+marketplace:")
        for r in rows:
            role = "S" if r["event_id"] == s else "G"
            print(f"    [{role}] event={r['event_id']:2d}  mp={r['mp']:10s}  "
                  f"active={r['active']:4d}  inactive={r['inactive']:4d}  "
                  f"min={r['min_price']}  max={r['max_price']}")
        print(f"    TOTAL active: survivor={total_s_active}  ghost={total_gh_active}")

        # ── Listing overlap check (for Ariana — same external event IDs) ──
        cur.execute("""
            SELECT COUNT(*) AS overlap
            FROM listings ls
            JOIN listings lg ON ls.external_listing_id = lg.external_listing_id
                             AND ls.marketplace_id = lg.marketplace_id
            WHERE ls.event_id = %s AND lg.event_id = %s
              AND ls.is_active AND lg.is_active
        """, (s, gh))
        overlap = cur.fetchone()["overlap"]
        print(f"\n  Listing external_id overlap (same listing on both events): {overlap}")
        if overlap > 0:
            print(f"    ⚠ {overlap} listings share external_listing_id between survivor and ghost")
            print(f"    → These are DUPLICATE LISTINGS from same source. Safe to deactivate ghost's.")

        # ── Unique listings on ghost not on survivor ───────────────────────
        cur.execute("""
            SELECT COUNT(*) AS unique_ghost
            FROM listings lg
            WHERE lg.event_id = %s AND lg.is_active
              AND NOT EXISTS (
                  SELECT 1 FROM listings ls
                  WHERE ls.event_id = %s
                    AND ls.external_listing_id = lg.external_listing_id
                    AND ls.marketplace_id = lg.marketplace_id
                    AND ls.is_active
              )
        """, (gh, s))
        unique_ghost = cur.fetchone()["unique_ghost"]
        print(f"  Unique active listings on ghost not on survivor: {unique_ghost}")
        if unique_ghost > 0:
            print(f"    ⚠ {unique_ghost} listings on ghost have no match on survivor")
            print(f"    → These may need re-parenting to survivor before ghost deactivation")
        else:
            print(f"    ✓ No unique inventory on ghost — safe to deactivate")

        # ── PollRun counts ────────────────────────────────────────────────
        cur.execute("""
            SELECT te.event_id,
                   COUNT(pr.id) AS total_poll_runs,
                   MAX(pr.completed_at) FILTER (WHERE pr.status='success') AS last_success,
                   COUNT(pr.id) FILTER (WHERE pr.status='success') AS success_count,
                   COUNT(pr.id) FILTER (WHERE pr.status='error') AS error_count
            FROM tracked_events te
            LEFT JOIN poll_runs pr ON pr.tracked_event_id = te.id
            WHERE te.event_id = ANY(%s)
            GROUP BY te.event_id
            ORDER BY te.event_id
        """, ([s, gh],))
        for r in cur.fetchall():
            role = "SURVIVOR" if r["event_id"] == s else "GHOST   "
            print(f"\n  [{role}] id={r['event_id']}  total_poll_runs={r['total_poll_runs']}  "
                  f"success={r['success_count']}  errors={r['error_count']}  "
                  f"last_success={str(r['last_success'])[:16] if r['last_success'] else 'never'}")

    # ── Overall recommendation summary ────────────────────────────────────
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print(f"{'='*70}")
    for gname, g in GROUPS.items():
        s, gh = g["survivor"], g["ghost"]
        print(f"\n  {gname}: survivor=event_id={s} ✓  ghost=event_id={gh} → DEACTIVATE")

    print(f"\n{'─'*70}")
    print("Strategy per group:")
    print("  Groups 2-4 (LOW RISK):")
    print("    - Ghost has 0 active listings, 0 poll_runs")
    print("    - Ghost's SeatGeek TE has same external_event_id as survivor's TE")
    print("    - Action: deactivate ghost's TE(s), leave ghost Event row in place")
    print()
    print("  Group 1 (HIGH RISK — Ariana):")
    print("    - Ghost has IDENTICAL external_event_ids to survivor on ALL 4 MPs")
    print("    - Ghost has ~737 active listings from same actual sources as survivor's ~781")
    print("    - Listing overlap analysis above determines if re-parenting is needed")
    print("    - Action: deactivate ghost's 4 TEs + deactivate ghost's listings")
    print("             (survivor already has same listings from same sources)")
    print("             (survivor will continue polling all 4 MPs going forward)")

    cur.close()


def main():
    conn = psycopg2.connect(DB_URL)
    conn.set_session(readonly=True, autocommit=True)
    run(conn)
    conn.close()


if __name__ == "__main__":
    main()
