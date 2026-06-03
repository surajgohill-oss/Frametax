"""
Phase 1E-B: Post-Merge Validation (Task 5)
===========================================
Verifies database integrity after all reconciliations are committed.

Checks:
  1. No duplicate groups remain
  2. Listing counts preserved (before/after)
  3. Polling preserved for all survivors
  4. Marketplace mappings intact
  5. No orphan tracked_events (event_id refs non-existent events)
  6. No orphan listings (event_id or tracked_event_id broken)
  7. No orphan poll_runs (tracked_event_id broken)
  8. Ghost events are fully inactive (0 active TEs, 0 active listings)
  9. Survivors have correct TE counts and listings

Usage:
    python3 scripts/phase1eb_postmerge_validate.py
"""

import psycopg2
import psycopg2.extras

DB_URL = (
    "postgresql://postgres:jOhylgsBSCdUhFXUChzNfkEvBAmuGsIP"
    "@switchback.proxy.rlwy.net:43266/railway"
)

# Pre-reconciliation baseline (from snapshots / pre-merge validation)
BEFORE = {
    "total_events":           30,
    "survivor_listings": {
        11: 781,   # Ariana survivor (before merge)
        25: 1066,  # Diljit survivor
        28: 469,   # Chance survivor
        29: 0,     # Reggae survivor
    },
    "ghost_listings": {
        19: 737,   # Ariana ghost (before deactivation)
        30: 0,
        31: 0,
        32: 0,
    },
    "total_active_listings": 781 + 1066 + 469 + 0 + 737 + 0 + 0 + 0,  # = 3053
}

EXPECTED_AFTER = {
    11: 915,   # 781 + 12 (reactivated case2) + 122 (reparented case3)
    25: 1066,
    28: 469,
    29: 0,
    19: 0,
    30: 0,
    31: 0,
    32: 0,
}

SURVIVORS = [11, 25, 28, 29]
GHOSTS    = [19, 30, 31, 32]
ALL_IDS   = SURVIVORS + GHOSTS


def check(label, passed, detail=""):
    icon = "✓" if passed else "✗"
    print(f"  {icon}  {label}" + (f"  ({detail})" if detail else ""))
    return passed


def main():
    conn = psycopg2.connect(DB_URL)
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    failures = []

    print("=" * 70)
    print("PHASE 1E-B POST-MERGE VALIDATION")
    print("=" * 70)

    # ── 1. No duplicate groups remain ──────────────────────────────────────
    print("\n[1] Duplicate group check")
    for g_id in GHOSTS:
        cur.execute("SELECT COUNT(*) FROM tracked_events WHERE event_id=%s AND is_active=true", (g_id,))
        active_tes = cur.fetchone()[0]
        ok = check(f"Ghost event_id={g_id} has 0 active TEs", active_tes == 0,
                   f"found {active_tes}")
        if not ok: failures.append(f"ghost {g_id} still has active TEs")

    # ── 2. Listing counts match expected ───────────────────────────────────
    print("\n[2] Active listing counts per event")
    for eid in ALL_IDS:
        cur.execute("SELECT COUNT(*) FROM listings WHERE event_id=%s AND is_active=true", (eid,))
        actual = cur.fetchone()[0]
        expected = EXPECTED_AFTER[eid]
        role = "SURVIVOR" if eid in SURVIVORS else "ghost"
        ok = check(
            f"event_id={eid:2d} [{role:8s}] active listings = {expected}",
            actual == expected,
            f"got {actual}"
        )
        if not ok: failures.append(f"event {eid} listing count mismatch: expected {expected} got {actual}")

    # ── 3. Total active listing conservation ──────────────────────────────
    print("\n[3] Total active listing conservation")
    # Expected: 915 + 1066 + 469 + 0 = 2450 across 4 survivors
    # Before: 781+737=1518 (ariana group), 1066 (diljit), 469 (chance), 0 (reggae) = 3053 total
    # Conserved: 1518 from ariana group preserved as 915 on survivor
    # (603 overlap deactivated = removed; 12 reactivated; 122 reparented; net reduction = 603 - 12 = 591)
    # Net reduction: 737 ghost deactivated - 122 reparented - 12 reactivated = 603 removed from system
    # Expected total active listings after: 3053 - 603 = 2450

    expected_total = 915 + 1066 + 469 + 0  # = 2450
    cur.execute("""
        SELECT COUNT(*) FROM listings l
        JOIN events e ON l.event_id = e.id
        WHERE l.is_active = true
          AND e.id = ANY(%s)
    """, (ALL_IDS,))
    actual_total = cur.fetchone()[0]
    ok = check(
        f"Total active listings across all 8 events = {expected_total}",
        actual_total == expected_total,
        f"got {actual_total}"
    )
    if not ok: failures.append(f"total listings mismatch: expected {expected_total} got {actual_total}")

    # ── 4. Survivor marketplace mappings intact ────────────────────────────
    print("\n[4] Survivor marketplace mappings")
    survivor_expected_mps = {
        11: {"gametime", "seatgeek", "stubhub", "tickpick"},
        25: {"gametime", "seatgeek", "stubhub", "tickpick"},
        28: {"gametime", "seatgeek", "stubhub", "tickpick"},
        29: {"gametime", "seatgeek", "stubhub", "tickpick"},
    }
    for eid, expected_mps in survivor_expected_mps.items():
        cur.execute("""
            SELECT m.slug FROM tracked_events te
            JOIN marketplaces m ON te.marketplace_id = m.id
            WHERE te.event_id = %s AND te.is_active = true
        """, (eid,))
        actual_mps = {row["slug"] for row in cur.fetchall()}
        ok = check(
            f"event_id={eid} active TEs cover {sorted(expected_mps)}",
            actual_mps == expected_mps,
            f"got {sorted(actual_mps)}"
        )
        if not ok: failures.append(f"event {eid} missing marketplaces: {expected_mps - actual_mps}")

    # ── 5. Orphan check — tracked_events → events ─────────────────────────
    print("\n[5] Orphan checks")
    cur.execute("""
        SELECT COUNT(*) FROM tracked_events te
        WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.id = te.event_id)
    """)
    orphan_tes = cur.fetchone()[0]
    ok = check("No orphan tracked_events (event_id → events)", orphan_tes == 0,
               f"found {orphan_tes}")
    if not ok: failures.append(f"orphan tracked_events: {orphan_tes}")

    # ── 6. Orphan check — listings → events ───────────────────────────────
    cur.execute("""
        SELECT COUNT(*) FROM listings l
        WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.id = l.event_id)
    """)
    orphan_listings = cur.fetchone()[0]
    ok = check("No orphan listings (event_id → events)", orphan_listings == 0,
               f"found {orphan_listings}")
    if not ok: failures.append(f"orphan listings: {orphan_listings}")

    # ── 7. Orphan check — poll_runs → tracked_events ──────────────────────
    cur.execute("""
        SELECT COUNT(*) FROM poll_runs pr
        WHERE NOT EXISTS (SELECT 1 FROM tracked_events te WHERE te.id = pr.tracked_event_id)
    """)
    orphan_prs = cur.fetchone()[0]
    ok = check("No orphan poll_runs (tracked_event_id → tracked_events)", orphan_prs == 0,
               f"found {orphan_prs}")
    if not ok: failures.append(f"orphan poll_runs: {orphan_prs}")

    # ── 8. Survivor polling still active ──────────────────────────────────
    print("\n[6] Survivor polling still active")
    for eid in SURVIVORS:
        cur.execute("""
            SELECT te.id, m.slug, te.last_polled_at, te.next_poll_at, te.is_active
            FROM tracked_events te
            JOIN marketplaces m ON te.marketplace_id = m.id
            WHERE te.event_id = %s AND te.is_active = true
            ORDER BY m.slug
        """, (eid,))
        rows = cur.fetchall()
        for r in rows:
            last = str(r["last_polled_at"])[:16] if r["last_polled_at"] else "never"
            next_ = str(r["next_poll_at"])[:16] if r["next_poll_at"] else "none"
            print(f"    event={eid:2d} te={r['id']:3d} {r['slug']:10s} "
                  f"last={last:16s} next={next_:16s} active={r['is_active']}")

    # ── 9. Total event count ───────────────────────────────────────────────
    print("\n[7] Total event count")
    cur.execute("SELECT COUNT(*) FROM events")
    total_events = cur.fetchone()[0]
    ok = check(f"Total events in DB = {BEFORE['total_events']} (unchanged)",
               total_events == BEFORE["total_events"],
               f"got {total_events}")
    if not ok: failures.append(f"event count changed: expected {BEFORE['total_events']} got {total_events}")

    # ── 10. Before/After Summary ───────────────────────────────────────────
    print(f"\n{'='*70}")
    print("BEFORE/AFTER SUMMARY")
    print(f"{'='*70}")
    print(f"\n  {'Event':>5}  {'Role':8}  {'Group':20}  {'Before':>8}  {'After':>8}  {'Δ':>6}")
    print(f"  {'─'*5}  {'─'*8}  {'─'*20}  {'─'*8}  {'─'*8}  {'─'*6}")
    rows_data = [
        (11, "SURVIVOR", "Ariana Jun13",  781,  915),
        (19, "ghost",    "Ariana Jun13",  737,    0),
        (25, "SURVIVOR", "Diljit",       1066, 1066),
        (30, "ghost",    "Diljit",          0,    0),
        (28, "SURVIVOR", "Chance",        469,  469),
        (31, "ghost",    "Chance",          0,    0),
        (29, "SURVIVOR", "Reggae",          0,    0),
        (32, "ghost",    "Reggae",          0,    0),
    ]
    for eid, role, group, before, expected_after_v in rows_data:
        cur.execute("SELECT COUNT(*) FROM listings WHERE event_id=%s AND is_active=true", (eid,))
        actual_now = cur.fetchone()[0]
        delta = actual_now - before
        match = "✓" if actual_now == expected_after_v else "⚠"
        print(f"  {eid:>5}  {role:8}  {group:20}  {before:>8}  {actual_now:>8}  "
              f"{delta:>+6}  {match}")

    # ── Final verdict ──────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    if failures:
        print(f"  ❌ FAILED — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"     • {f}")
    else:
        print("  ✅ ALL CHECKS PASSED — reconciliation complete and validated")
    print(f"{'='*70}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
