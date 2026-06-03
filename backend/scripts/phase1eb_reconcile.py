"""
Phase 1E-B: Duplicate Reconciliation (Tasks 3 & 4)
====================================================
Executes reconciliation for all 4 duplicate groups in a single transaction
per group, with dry-run capability and rollback on any error.

Execution order:
  1. Groups 2–4 (LOW RISK): deactivate ghost TrackedEvents only
  2. Group 1 (HIGH RISK):   re-parent unique ghost listings → deactivate ghost TEs

Usage:
    python3 scripts/phase1eb_reconcile.py --dry-run   # preview only, no changes
    python3 scripts/phase1eb_reconcile.py             # execute

Idempotent: safe to re-run (UPDATE with WHERE guards ensure no double-effects).
"""

import argparse
import sys
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

DB_URL = (
    "postgresql://postgres:jOhylgsBSCdUhFXUChzNfkEvBAmuGsIP"
    "@switchback.proxy.rlwy.net:43266/railway"
)

NOW_TS = datetime.now(timezone.utc).isoformat()


def banner(msg):
    print(f"\n{'─'*70}")
    print(f"  {msg}")
    print(f"{'─'*70}")


def reconcile_groups_2_4(cur, dry_run: bool):
    """
    Groups 2, 3, 4: Diljit / Chance / Reggae
    -----------------------------------------
    Ghost events (30, 31, 32) each have exactly 1 active TrackedEvent
    (SeatGeek only), 0 active listings, and 0 poll_runs.

    Action: deactivate ghost TrackedEvent(s). Leave ghost Event rows.
    """
    groups = [
        ("Group 2 — Diljit",         30, 25),
        ("Group 3 — Chance",         31, 28),
        ("Group 4 — Reggae Night",   32, 29),
    ]

    results = {}
    for name, ghost_id, survivor_id in groups:
        banner(f"{name}  ghost={ghost_id}  survivor={survivor_id}")

        # Count what we're about to touch
        cur.execute("""
            SELECT COUNT(*) FROM tracked_events
            WHERE event_id = %s AND is_active = true
        """, (ghost_id,))
        active_te_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM listings
            WHERE event_id = %s AND is_active = true
        """, (ghost_id,))
        active_listing_count = cur.fetchone()[0]

        print(f"  Ghost active TEs:      {active_te_count}")
        print(f"  Ghost active listings: {active_listing_count}")

        if active_listing_count > 0:
            print(f"  ⚠ WARNING: ghost has active listings — halting this group")
            results[name] = {"status": "HALTED", "reason": "unexpected active listings"}
            continue

        if not dry_run:
            cur.execute("""
                UPDATE tracked_events
                SET is_active = false
                WHERE event_id = %s AND is_active = true
            """, (ghost_id,))
            updated = cur.rowcount
            print(f"  ✓ Deactivated {updated} TrackedEvent(s) on ghost event_id={ghost_id}")
            results[name] = {"status": "DONE", "te_deactivated": updated}
        else:
            print(f"  [DRY RUN] Would deactivate {active_te_count} TrackedEvent(s) on ghost event_id={ghost_id}")
            results[name] = {"status": "DRY_RUN", "te_would_deactivate": active_te_count}

    return results


def reconcile_group_1_ariana(cur, dry_run: bool):
    """
    Group 1: Ariana Grande Jun13
    ----------------------------
    Survivor: event_id=11  Ghost: event_id=19
    Both have identical external_event_ids across all 4 marketplaces.
    Ghost has 737 active listings across 3 cases:

      Case 1 — 603 active on BOTH events (exact overlap)
               → deactivate ghost's copy
      Case 2 — 12 active on ghost, INACTIVE on survivor (re-emerged listings)
               → re-activate survivor's copy + deactivate ghost's copy
      Case 3 — 122 active on ghost, NO copy on survivor (truly unique)
               → re-parent to event_id=11  (safe: no constraint conflict)

    Expected survivor active after merge: 781 + 12 (reactivated) + 122 (reparented) = 915

    Steps:
      A. Re-parent 122 truly unique active ghost listings → event_id=11
      B. Re-activate 12 inactive survivor listings (ghost polled them active)
      C. Deactivate all remaining active ghost listings (603 + 12 = 615)
      D. Deactivate the 4 ghost TrackedEvents
    """
    banner("Group 1 — Ariana Jun13  ghost=19  survivor=11")

    survivor_id = 11
    ghost_id    = 19

    # ── Count all three cases ──────────────────────────────────────────────
    cur.execute("""
        SELECT
          COUNT(*) FILTER (WHERE EXISTS (
            SELECT 1 FROM listings s WHERE s.event_id = %s
            AND s.external_listing_id = ghost_l.external_listing_id
            AND s.marketplace_id = ghost_l.marketplace_id AND s.is_active = true))  AS case1_overlap,
          COUNT(*) FILTER (WHERE NOT EXISTS (
            SELECT 1 FROM listings s WHERE s.event_id = %s
            AND s.external_listing_id = ghost_l.external_listing_id
            AND s.marketplace_id = ghost_l.marketplace_id AND s.is_active = true)
            AND EXISTS (
            SELECT 1 FROM listings s WHERE s.event_id = %s
            AND s.external_listing_id = ghost_l.external_listing_id
            AND s.marketplace_id = ghost_l.marketplace_id AND s.is_active = false)) AS case2_inactive_overlap,
          COUNT(*) FILTER (WHERE NOT EXISTS (
            SELECT 1 FROM listings s WHERE s.event_id = %s
            AND s.external_listing_id = ghost_l.external_listing_id
            AND s.marketplace_id = ghost_l.marketplace_id))                         AS case3_truly_unique,
          COUNT(*) AS total_active_ghost
        FROM listings ghost_l
        WHERE ghost_l.event_id = %s AND ghost_l.is_active = true
    """, (survivor_id, survivor_id, survivor_id, survivor_id, ghost_id))
    row = cur.fetchone()
    case1, case2, case3, total_ghost = row[0], row[1], row[2], row[3]

    cur.execute("""
        SELECT COUNT(*) FROM tracked_events WHERE event_id = %s AND is_active = true
    """, (ghost_id,))
    active_te_count = cur.fetchone()[0]

    survivor_before = 781  # known from pre-merge validation
    expected_after  = survivor_before + case2 + case3

    print(f"  Case 1 (active overlap → deactivate ghost):          {case1}")
    print(f"  Case 2 (ghost active, survivor inactive → reactivate): {case2}")
    print(f"  Case 3 (truly unique → re-parent to survivor):        {case3}")
    print(f"  Total active on ghost:                                 {total_ghost}  (should={case1+case2+case3})")
    print(f"  Ghost active TrackedEvents to deactivate:              {active_te_count}")
    print(f"  Expected survivor active after merge:  {survivor_before} + {case2} + {case3} = {expected_after}")

    results = {
        "case3_reparented":          0,
        "case2_survivor_reactivated": 0,
        "ghost_listings_deactivated": 0,
        "te_deactivated":             0,
        "expected_survivor_active":   expected_after,
        "status":                     "DRY_RUN" if dry_run else "PENDING",
    }

    if not dry_run:
        # ── Step A: Re-parent 122 truly unique ghost listings ──────────────
        # Guard: only listings with NO counterpart on survivor (neither active nor inactive)
        cur.execute("""
            UPDATE listings
            SET event_id = %s
            WHERE event_id = %s
              AND is_active = true
              AND NOT EXISTS (
                SELECT 1 FROM listings surv_l
                WHERE surv_l.event_id = %s
                  AND surv_l.external_listing_id = listings.external_listing_id
                  AND surv_l.marketplace_id = listings.marketplace_id
              )
        """, (survivor_id, ghost_id, survivor_id))
        results["case3_reparented"] = cur.rowcount
        print(f"  ✓ Step A: Re-parented {results['case3_reparented']} truly unique listings → event_id={survivor_id}")

        # ── Step B: Re-activate survivor's 12 inactive counterparts ────────
        cur.execute("""
            UPDATE listings surv_l
            SET is_active = true
            FROM listings ghost_l
            WHERE surv_l.event_id = %s
              AND surv_l.is_active = false
              AND ghost_l.event_id = %s
              AND ghost_l.is_active = true
              AND surv_l.external_listing_id = ghost_l.external_listing_id
              AND surv_l.marketplace_id = ghost_l.marketplace_id
        """, (survivor_id, ghost_id))
        results["case2_survivor_reactivated"] = cur.rowcount
        print(f"  ✓ Step B: Re-activated {results['case2_survivor_reactivated']} listings on survivor (case 2)")

        # ── Step C: Deactivate all remaining active ghost listings ─────────
        # After Step A, the ghost has lost its 122 re-parented listings.
        # The remaining active ghost listings (case1=603 + case2=12) get deactivated.
        cur.execute("""
            UPDATE listings SET is_active = false
            WHERE event_id = %s AND is_active = true
        """, (ghost_id,))
        results["ghost_listings_deactivated"] = cur.rowcount
        print(f"  ✓ Step C: Deactivated {results['ghost_listings_deactivated']} remaining active ghost listings")

        # ── Step D: Deactivate ghost TrackedEvents ─────────────────────────
        cur.execute("""
            UPDATE tracked_events SET is_active = false
            WHERE event_id = %s AND is_active = true
        """, (ghost_id,))
        results["te_deactivated"] = cur.rowcount
        print(f"  ✓ Step D: Deactivated {results['te_deactivated']} TrackedEvents on ghost event_id={ghost_id}")

        results["status"] = "DONE"
    else:
        print(f"  [DRY RUN] Step A: Would re-parent {case3} truly unique listings → event_id={survivor_id}")
        print(f"  [DRY RUN] Step B: Would re-activate {case2} inactive survivor listings")
        print(f"  [DRY RUN] Step C: Would deactivate {case1 + case2} remaining active ghost listings")
        print(f"  [DRY RUN] Step D: Would deactivate {active_te_count} ghost TrackedEvents")
        results.update({
            "case3_reparented":            case3,
            "case2_survivor_reactivated":  case2,
            "ghost_listings_deactivated":  case1 + case2,
            "te_deactivated":              active_te_count,
        })

    return results


def post_run_verify(cur):
    """Quick sanity check after reconciliation."""
    banner("Post-reconciliation sanity check")

    ghost_ids    = [19, 30, 31, 32]
    survivor_ids = [11, 25, 28, 29]

    print(f"\n  {'Event':>3}  {'Role':10}  {'Active TEs':>10}  {'Active Listings':>15}  {'Is_Active (derived)':>20}")
    for eid in survivor_ids + ghost_ids:
        role = "SURVIVOR" if eid in survivor_ids else "ghost"

        cur.execute("""
            SELECT COUNT(*) FROM tracked_events WHERE event_id = %s AND is_active = true
        """, (eid,))
        active_tes = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM listings WHERE event_id = %s AND is_active = true
        """, (eid,))
        active_listings = cur.fetchone()[0]

        derived_active = "active" if active_tes > 0 else "INACTIVE"
        flag = "✓" if (
            (role == "SURVIVOR" and active_tes > 0) or
            (role == "ghost"    and active_tes == 0)
        ) else "⚠"
        print(f"  {eid:>3}  {role:10}  {active_tes:>10}  {active_listings:>15}  "
              f"{derived_active:>20}  {flag}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview all changes without executing")
    args = parser.parse_args()
    dry_run = args.dry_run

    mode = "DRY RUN — NO CHANGES WILL BE MADE" if dry_run else "LIVE EXECUTION"
    print(f"\n{'='*70}")
    print(f"  PHASE 1E-B RECONCILIATION  [{mode}]")
    print(f"  {NOW_TS}")
    print(f"{'='*70}")

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False  # explicit transaction control

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # ── Task 3: Groups 2–4 (LOW RISK) ─────────────────────────────────
        print("\n>>> TASK 3: Reconciling Groups 2–4 (Diljit / Chance / Reggae)")
        results_2_4 = reconcile_groups_2_4(cur, dry_run)

        # ── Task 4: Group 1 (HIGH RISK — Ariana) ──────────────────────────
        print("\n>>> TASK 4: Reconciling Group 1 (Ariana Jun13 — HIGH RISK)")
        result_ariana = reconcile_group_1_ariana(cur, dry_run)

        # ── Post-run verification ──────────────────────────────────────────
        post_run_verify(cur)

        if not dry_run:
            conn.commit()
            print(f"\n  ✅ COMMITTED — all reconciliation changes applied")
        else:
            conn.rollback()
            print(f"\n  ℹ  DRY RUN complete — rolled back, no changes persisted")

        cur.close()

    except Exception as exc:
        conn.rollback()
        print(f"\n  ❌ ERROR — rolled back all changes: {exc}")
        conn.close()
        sys.exit(1)

    conn.close()

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  SUMMARY [{mode}]")
    print(f"{'='*70}")
    for name, r in results_2_4.items():
        print(f"  {name}: {r}")
    print(f"  Group 1 — Ariana: {result_ariana}")


if __name__ == "__main__":
    main()
