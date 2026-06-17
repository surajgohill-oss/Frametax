"""
intelligence.py — Data Intelligence Layer
Read-only. No writes to any ingestion table.

Endpoints:
  GET /analytics/freshness                        Task 1: freshness report
  GET /analytics/events/{id}/snapshot-consistency Task 2: historical depth vs live
  GET /analytics/events/{id}/duplicate-analysis   Task 3: duplicate/crossover analytics
  GET /analytics/events/{id}/attribution          Task 4: sales vs relist attribution
  GET /analytics/intelligence/near-term           Combined report for events < 21 days away
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Event, Listing, ListingSnapshot, Marketplace, TrackedEvent, PollRun
from app.services.event_history import get_event_history_depth

router = APIRouter(prefix="/analytics", tags=["intelligence"])

NOW = datetime.utcnow  # callable so each request gets fresh value


# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 — DATA FRESHNESS
# ─────────────────────────────────────────────────────────────────────────────

def _freshness_status(
    last_polled_at: datetime | None,
    next_poll_at: datetime | None,
    poll_interval_min: int,
    is_active: bool,
    has_listings: bool,
    consecutive_errors: int,
) -> str:
    now = NOW()
    if not is_active:
        return "inactive"
    if not has_listings:
        return "not_listed"
    if consecutive_errors >= 3:
        return "broken"
    if last_polled_at is None:
        return "stale"
    age_min = (now - last_polled_at).total_seconds() / 60
    expected = max(poll_interval_min, 15)  # floor at 15 min
    if age_min <= expected * 1.5:
        return "fresh"
    if age_min <= expected * 3:
        return "late"
    return "stale"


@router.get("/freshness")
async def freshness_report(
    days_ahead: int = Query(21, ge=1, le=180),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 1: Per-event × marketplace freshness report.

    freshness_status values:
      fresh      – polled within 1.5× expected interval
      late       – overdue by 1.5×–3× interval
      stale      – overdue >3× interval or never polled
      broken     – 3+ consecutive failures
      inactive   – TrackedEvent.is_active = False
      not_listed – active TE but 0 active listings for this event×marketplace
    """
    now = NOW()
    cutoff = now + timedelta(days=days_ahead)

    # ── 1. Events within window ───────────────────────────────────────────────
    events_q = await db.execute(
        select(Event).where(
            and_(Event.event_date >= now, Event.event_date <= cutoff)
        ).order_by(Event.event_date)
    )
    events = events_q.scalars().all()
    if not events:
        return {"generated_at": now.isoformat(), "events": [], "systemic_issues": []}

    event_ids = [e.id for e in events]
    event_map = {e.id: e for e in events}

    # ── 2. TrackedEvents for these events ────────────────────────────────────
    te_q = await db.execute(
        select(TrackedEvent, Marketplace.slug)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(TrackedEvent.event_id.in_(event_ids))
    )
    te_rows = te_q.all()

    # ── 3. Recent poll_runs per TrackedEvent (last 10 per TE) ────────────────
    poll_sql = text("""
        SELECT tracked_event_id, status, error_message, started_at, completed_at,
               listings_found
        FROM poll_runs
        WHERE tracked_event_id = ANY(:te_ids)
        ORDER BY started_at DESC
    """)
    te_ids = [te.id for te, _ in te_rows]
    poll_result = await db.execute(poll_sql, {"te_ids": te_ids})
    all_polls = poll_result.fetchall()

    # Group by tracked_event_id, keep last 10
    polls_by_te: dict[int, list] = defaultdict(list)
    for row in all_polls:
        polls_by_te[row[0]].append(row)

    # ── 4. Active listing counts per event×marketplace ───────────────────────
    listing_q = await db.execute(
        select(Listing.event_id, Marketplace.slug, func.count(Listing.id), func.sum(Listing.quantity))
        .join(Marketplace, Listing.marketplace_id == Marketplace.id)
        .where(and_(Listing.event_id.in_(event_ids), Listing.is_active == True))
        .group_by(Listing.event_id, Marketplace.slug)
    )
    listing_counts: dict[tuple, tuple] = {
        (row[0], row[1]): (row[2], row[3] or 0) for row in listing_q.fetchall()
    }

    # ── 5. Build per-event report ─────────────────────────────────────────────
    event_reports: list[dict] = []
    mp_failure_counts: dict[str, int] = defaultdict(int)
    stale_near_term: list[dict] = []

    for event in events:
        days_until = (event.event_date - now).total_seconds() / 86400
        mp_entries: list[dict] = []

        event_te_rows = [(te, slug) for te, slug in te_rows if te.event_id == event.id]

        for te, slug in event_te_rows:
            polls = polls_by_te.get(te.id, [])
            # Consecutive errors = leading run of error/failed statuses
            consecutive_errors = 0
            for p in polls:
                if p[1] in ("error", "failed", "timeout"):
                    consecutive_errors += 1
                else:
                    break

            listing_c, ticket_c = listing_counts.get((event.id, slug), (0, 0))
            status = _freshness_status(
                last_polled_at=te.last_polled_at,
                next_poll_at=te.next_poll_at,
                poll_interval_min=te.poll_interval_minutes or 60,
                is_active=te.is_active,
                has_listings=listing_c > 0,
                consecutive_errors=consecutive_errors,
            )

            last_success_at = None
            last_success_listings = None
            for p in polls:
                if p[1] == "success":
                    last_success_at = p[3].isoformat() if p[3] else None
                    last_success_listings = p[5]
                    break

            age_min = None
            if te.last_polled_at:
                age_min = round((now - te.last_polled_at).total_seconds() / 60, 1)

            entry: dict[str, Any] = {
                "marketplace": slug,
                "is_active": te.is_active,
                "freshness_status": status,
                "active_listings": listing_c,
                "active_tickets": ticket_c,
                "last_polled_at": te.last_polled_at.isoformat() if te.last_polled_at else None,
                "age_minutes": age_min,
                "next_poll_at": te.next_poll_at.isoformat() if te.next_poll_at else None,
                "poll_interval_minutes": te.poll_interval_minutes,
                "consecutive_errors": consecutive_errors,
                "last_success_at": last_success_at,
                "last_success_listings": last_success_listings,
                "recent_poll_count": len(polls[:10]),
            }
            mp_entries.append(entry)

            if status in ("stale", "broken"):
                mp_failure_counts[slug] += 1

        # Overall event freshness = worst of its marketplace statuses
        status_priority = {"broken": 0, "stale": 1, "late": 2, "not_listed": 3,
                           "inactive": 4, "fresh": 5}
        overall = min(mp_entries, key=lambda x: status_priority.get(x["freshness_status"], 9),
                      default={"freshness_status": "unknown"})["freshness_status"] if mp_entries else "unknown"

        report = {
            "event_id": event.id,
            "title": event.title,
            "event_date": event.event_date.isoformat(),
            "days_until_event": round(days_until, 1),
            "overall_freshness": overall,
            "marketplace_count": len(mp_entries),
            "marketplaces": mp_entries,
        }
        event_reports.append(report)

        if overall in ("stale", "broken") and days_until <= 7:
            stale_near_term.append({
                "event_id": event.id,
                "title": event.title,
                "days_until_event": round(days_until, 1),
                "overall_freshness": overall,
                "broken_mps": [e["marketplace"] for e in mp_entries if e["freshness_status"] in ("stale", "broken")],
            })

    # ── 6. Systemic issues ────────────────────────────────────────────────────
    total_events = len(events)
    systemic_issues = []
    for slug, fail_count in sorted(mp_failure_counts.items(), key=lambda x: -x[1]):
        if fail_count >= 2:
            systemic_issues.append({
                "marketplace": slug,
                "stale_or_broken_events": fail_count,
                "of_total_events": total_events,
                "failure_pct": round(fail_count / total_events * 100, 1),
            })

    return {
        "generated_at": now.isoformat(),
        "window_days": days_ahead,
        "total_events": total_events,
        "stale_near_term": stale_near_term,
        "systemic_issues": systemic_issues,
        "events": event_reports,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 — HISTORICAL DEPTH / SNAPSHOT CONSISTENCY
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/snapshot-consistency")
async def snapshot_consistency(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Task 2: Compare live inventory vs canonical snapshot vs listing_snapshots.

    Returns:
      live_*            – from active listings (real-time)
      snapshot_*        – from canonical_inventory_snapshots (most recent)
      listing_snap_*    – from listing_snapshots (most recent poll window)
      lag_*             – staleness indicators
      verdict           – consistent | lagging | stale | no_snapshots
    """
    now = NOW()

    # ── Live inventory ─────────────────────────────────────────────────────────
    live_q = await db.execute(
        select(
            Marketplace.slug,
            func.count(Listing.id),
            func.sum(Listing.quantity),
            func.min(Listing.price),
            func.max(Listing.last_seen_at),
        )
        .join(Marketplace, Listing.marketplace_id == Marketplace.id)
        .where(and_(Listing.event_id == event_id, Listing.is_active == True))
        .group_by(Marketplace.slug)
    )
    live_rows = live_q.fetchall()
    live_by_mp = {r[0]: {"listings": r[1], "tickets": r[2] or 0,
                         "min_price": float(r[3]) if r[3] else None,
                         "last_seen_at": r[4].isoformat() if r[4] else None}
                  for r in live_rows}
    live_total_listings = sum(v["listings"] for v in live_by_mp.values())
    live_total_tickets = sum(v["tickets"] for v in live_by_mp.values())
    live_min_ask = min((v["min_price"] for v in live_by_mp.values() if v["min_price"]), default=None)
    live_last_seen = max((v["last_seen_at"] for v in live_by_mp.values() if v["last_seen_at"]), default=None)

    # ── Latest canonical snapshot ──────────────────────────────────────────────
    snap_sql = text("""
        SELECT snapshot_at, total_raw_listings, total_canonical_blocks,
               mirrored_ratio, low_ask, by_marketplace
        FROM canonical_inventory_snapshots
        WHERE event_id = :event_id
        ORDER BY snapshot_at DESC
        LIMIT 1
    """)
    snap_result = await db.execute(snap_sql, {"event_id": event_id})
    snap_row = snap_result.fetchone()

    snap_data = None
    snap_lag_hours = None
    if snap_row:
        snap_data = {
            "snapshot_at": snap_row[0].isoformat(),
            "raw_listings": snap_row[1],
            "unique_tickets": snap_row[2],
            "mirror_rate": float(snap_row[3]) if snap_row[3] else None,
            "low_ask": float(snap_row[4]) if snap_row[4] else None,
            "by_marketplace": snap_row[5] or {},
        }
        snap_lag_hours = round((now - snap_row[0]).total_seconds() / 3600, 2)

    # Snapshot count + history depth (combined: listing_snapshots + event_price_history_agg)
    snap_stats_sql = text("""
        SELECT COUNT(*), MIN(snapshot_at), MAX(snapshot_at)
        FROM canonical_inventory_snapshots
        WHERE event_id = :event_id
    """)
    snap_stats = (await db.execute(snap_stats_sql, {"event_id": event_id})).fetchone()
    snapshot_count = snap_stats[0] if snap_stats else 0
    # Use combined history depth (live snapshots + pre-import agg buckets)
    hist_depth = await get_event_history_depth(event_id, db)
    history_depth_days = int(hist_depth.combined_days)
    history_depth_hours = hist_depth.combined_hours
    history_source = hist_depth.source

    # ── Latest listing_snapshots (per marketplace) ─────────────────────────────
    ls_sql = text("""
        WITH latest_mp AS (
            SELECT marketplace_id, MAX(snapshot_at) AS latest_snap
            FROM listing_snapshots
            WHERE event_id = :event_id
            GROUP BY marketplace_id
        )
        SELECT m.slug, COUNT(ls.id), SUM(ls.quantity), MIN(ls.price), MAX(ls.snapshot_at)
        FROM listing_snapshots ls
        JOIN marketplaces m ON m.id = ls.marketplace_id
        JOIN latest_mp lm ON lm.marketplace_id = ls.marketplace_id
        WHERE ls.event_id = :event_id
          AND ls.snapshot_at >= lm.latest_snap - INTERVAL '2 hours'
        GROUP BY m.slug
    """)
    ls_result = await db.execute(ls_sql, {"event_id": event_id})
    ls_rows = ls_result.fetchall()
    ls_by_mp = {r[0]: {"listings": r[1], "tickets": r[2] or 0,
                       "min_price": float(r[3]) if r[3] else None,
                       "latest_snap_at": r[4].isoformat() if r[4] else None}
                for r in ls_rows}
    ls_latest = max((v["latest_snap_at"] for v in ls_by_mp.values() if v["latest_snap_at"]), default=None)
    ls_lag_hours = None
    if ls_latest:
        ls_lag_hours = round((now - datetime.fromisoformat(ls_latest)).total_seconds() / 3600, 2)

    # ── Per-marketplace comparison ─────────────────────────────────────────────
    all_slugs = sorted(set(live_by_mp) | set(ls_by_mp) | (set(snap_data["by_marketplace"]) if snap_data else set()))
    mp_comparison = []
    for slug in all_slugs:
        live = live_by_mp.get(slug, {})
        ls = ls_by_mp.get(slug, {})
        snap_listings = (snap_data["by_marketplace"].get(slug) if snap_data else None)
        live_l = live.get("listings", 0)
        ls_l = ls.get("listings", 0)
        listing_drift = live_l - ls_l if live_l and ls_l else None
        mp_comparison.append({
            "marketplace": slug,
            "live_listings": live_l,
            "live_min_price": live.get("min_price"),
            "snapshot_listings": snap_listings,
            "listing_snap_listings": ls_l,
            "listing_drift_live_vs_snap": listing_drift,
        })

    # ── Poll freshness (to disambiguate snapshot staleness from event staleness) ──
    poll_q = await db.execute(
        select(func.max(TrackedEvent.last_polled_at))
        .where(TrackedEvent.event_id == event_id)
    )
    last_polled_at = poll_q.scalar_one_or_none()
    poll_lag_hours = None
    if last_polled_at:
        poll_lag_hours = round((now - last_polled_at).total_seconds() / 3600, 2)
    poll_is_fresh = poll_lag_hours is not None and poll_lag_hours <= 3

    # ── Verdict ────────────────────────────────────────────────────────────────
    if snapshot_count == 0:
        verdict = "no_snapshots"
    elif snap_lag_hours is not None and snap_lag_hours > 12:
        # snapshot_stale = poll ran recently but canonical snapshot is old (scheduler gap)
        # stale          = both poll and snapshot are old
        verdict = "snapshot_stale" if poll_is_fresh else "stale"
    elif snap_lag_hours is not None and snap_lag_hours > 4:
        verdict = "lagging"
    else:
        # Check for significant drift between live and snapshot
        snap_listings = snap_data["raw_listings"] if snap_data else 0
        drift_pct = abs(live_total_listings - snap_listings) / max(snap_listings, 1) * 100 if snap_listings else 0
        verdict = "drifted" if drift_pct > 20 else "consistent"

    return {
        "event_id": event_id,
        "generated_at": now.isoformat(),
        "verdict": verdict,
        # verdict semantics:
        #   consistent     – snapshot fresh, drift <20%
        #   lagging        – snapshot 4-12h old
        #   snapshot_stale – snapshot >12h old BUT poll ran recently (scheduler gap, not data gap)
        #   stale          – snapshot >12h old AND poll also stale (genuine data gap)
        #   drifted        – snapshot fresh but live/snap diverged >20%
        #   no_snapshots   – canonical_inventory_snapshots has no rows for event
        "poll_lag_hours": poll_lag_hours,
        "poll_is_fresh": poll_is_fresh,
        "snapshot_count": snapshot_count,
        "history_depth_days": history_depth_days,
        "history_depth_hours": history_depth_hours,
        "history_source": history_source,
        "live": {
            "total_listings": live_total_listings,
            "total_tickets": live_total_tickets,
            "min_ask": round(live_min_ask, 2) if live_min_ask else None,
            "last_seen_at": live_last_seen,
            "by_marketplace": live_by_mp,
        },
        "canonical_snapshot": {
            "lag_hours": snap_lag_hours,
            "data": snap_data,
        } if snap_data else None,
        "listing_snapshots": {
            "lag_hours": ls_lag_hours,
            "latest_at": ls_latest,
            "by_marketplace": ls_by_mp,
        },
        "mp_comparison": mp_comparison,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3 — DUPLICATE / CROSSOVER ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/duplicate-analysis")
async def duplicate_analysis(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Task 3: Duplicate / crossover analytics from active listings.

    Uses:
      - mirror_group_id (explicit cross-MP canonical groups when set)
      - (section_id, row, quantity) identity keys for pairwise overlap estimation

    Confidence:
      high   – mirror_group_id assigned (collector confirmed duplicate)
      medium – matching (section_id, row, qty) across 2+ MPs
      low    – matching section+qty but row is null on ≥1 side
    """
    # ── Fetch all active listings with marketplace ────────────────────────────
    q = await db.execute(
        select(Listing, Marketplace.slug)
        .join(Marketplace, Listing.marketplace_id == Marketplace.id)
        .where(and_(Listing.event_id == event_id, Listing.is_active == True))
    )
    rows = q.all()

    if not rows:
        return {"event_id": event_id, "gross_tickets": 0, "net_unique_tickets": 0,
                "duplicate_tickets": 0, "duplicate_share": 0.0, "pairwise_overlap": [],
                "confidence": "n/a", "note": "no active listings"}

    MP_PAIRS = [
        ("stubhub", "tickpick"), ("stubhub", "gametime"), ("stubhub", "vividseats"),
        ("tickpick", "gametime"), ("tickpick", "vividseats"), ("gametime", "vividseats"),
    ]

    gross_tickets = sum(l.quantity for l, _ in rows)

    # ── Strategy A: mirror_group_id ────────────────────────────────────────────
    # Each mirror group = same physical seat block on multiple MPs.
    # Count each group's tickets once (max quantity within group — usually identical).
    mirror_groups: dict[int, list[tuple]] = defaultdict(list)
    no_mirror: list[tuple] = []
    for listing, slug in rows:
        if listing.mirror_group_id is not None:
            mirror_groups[listing.mirror_group_id].append((listing, slug))
        else:
            no_mirror.append((listing, slug))

    mirror_unique_tickets = sum(
        max(l.quantity for l, _ in group)
        for group in mirror_groups.values()
    )
    no_mirror_tickets = sum(l.quantity for l, _ in no_mirror)
    net_unique_a = mirror_unique_tickets + no_mirror_tickets

    # Duplicate tickets from mirror groups = gross within group - max(qty)
    dup_from_mirror = sum(
        sum(l.quantity for l, _ in group) - max(l.quantity for l, _ in group)
        for group in mirror_groups.values()
    )

    # ── Strategy B: (section_id, row, qty) identity keys ─────────────────────
    # Groups listings by identity key across marketplaces.
    # row=None is treated as unknown (lower confidence).
    identity_groups: dict[tuple, dict] = defaultdict(lambda: {"slugs": set(), "qty": 0, "listings": []})
    for listing, slug in rows:
        sec = listing.section_id or listing.section or "?"
        row = listing.row or ""
        qty = listing.quantity
        key = (sec, row, qty)
        identity_groups[key]["slugs"].add(slug)
        identity_groups[key]["qty"] = qty
        identity_groups[key]["listings"].append((listing, slug))

    # Cross-MP groups = key appears on 2+ marketplaces
    cross_mp_groups = {k: v for k, v in identity_groups.items() if len(v["slugs"]) >= 2}

    dup_from_identity = sum(
        (len(v["slugs"]) - 1) * v["qty"]  # each duplicate MP copy is a dup
        for v in cross_mp_groups.values()
    )
    identity_unique_tickets = gross_tickets - dup_from_identity

    # Confidence: if mirror_group_id coverage is high, use strategy A; else B
    mirror_covered_listings = sum(len(g) for g in mirror_groups.values())
    mirror_coverage_pct = mirror_covered_listings / len(rows) if rows else 0

    if mirror_coverage_pct > 0.3:
        chosen_strategy = "mirror_group_id"
        net_unique_tickets = net_unique_a
        duplicate_tickets = gross_tickets - net_unique_a
        confidence = "high"
    else:
        chosen_strategy = "identity_key"
        net_unique_tickets = identity_unique_tickets
        duplicate_tickets = dup_from_identity
        # Lower confidence if many rows are missing section_id or row
        missing_sec = sum(1 for l, _ in rows if not l.section_id and not l.section)
        missing_row = sum(1 for l, _ in rows if not l.row)
        confidence = "medium" if missing_row / len(rows) < 0.5 else "low"

    duplicate_share = round(duplicate_tickets / gross_tickets, 4) if gross_tickets else 0.0

    # ── Pairwise overlap ───────────────────────────────────────────────────────
    # For each MP pair: count seat blocks (section+row+qty keys) appearing on both.
    mp_key_sets: dict[str, set] = defaultdict(set)
    mp_ticket_sums: dict[str, int] = defaultdict(int)
    for listing, slug in rows:
        sec = listing.section_id or listing.section or "?"
        row = listing.row or ""
        qty = listing.quantity
        mp_key_sets[slug].add((sec, row, qty))
        mp_ticket_sums[slug] += qty

    pairwise_overlap = []
    for mp_a, mp_b in MP_PAIRS:
        keys_a = mp_key_sets.get(mp_a, set())
        keys_b = mp_key_sets.get(mp_b, set())
        if not keys_a or not keys_b:
            pairwise_overlap.append({
                "pair": f"{mp_a}↔{mp_b}",
                "mp_a": mp_a, "mp_b": mp_b,
                "overlap_blocks": None,
                "overlap_tickets": None,
                "overlap_pct_of_a": None,
                "overlap_pct_of_b": None,
                "confidence": "n/a",
                "note": "one or both marketplaces not active for this event",
            })
            continue

        shared_keys = keys_a & keys_b
        shared_ticket_sum = sum(qty for _, _, qty in shared_keys)
        # Row-null penalty on confidence
        null_row_count = sum(1 for _, row, _ in shared_keys if row == "")
        pair_confidence = "medium"
        if null_row_count / max(len(shared_keys), 1) > 0.5:
            pair_confidence = "low"

        pairwise_overlap.append({
            "pair": f"{mp_a}↔{mp_b}",
            "mp_a": mp_a, "mp_b": mp_b,
            "mp_a_blocks": len(keys_a),
            "mp_b_blocks": len(keys_b),
            "overlap_blocks": len(shared_keys),
            "overlap_tickets": shared_ticket_sum,
            "overlap_pct_of_a": round(len(shared_keys) / len(keys_a) * 100, 1) if keys_a else None,
            "overlap_pct_of_b": round(len(shared_keys) / len(keys_b) * 100, 1) if keys_b else None,
            "confidence": pair_confidence,
        })

    return {
        "event_id": event_id,
        "gross_tickets": gross_tickets,
        "duplicate_tickets": duplicate_tickets,
        "net_unique_tickets": net_unique_tickets,
        "duplicate_share": duplicate_share,
        "strategy_used": chosen_strategy,
        "confidence": confidence,
        "mirror_group_coverage_pct": round(mirror_coverage_pct * 100, 1),
        "cross_mp_identity_groups": len(cross_mp_groups),
        "pairwise_overlap": pairwise_overlap,
        "note": (
            "mirror_group_id provides high-confidence dedup when coverage > 30%. "
            "Identity-key method uses (section_id, row, qty) matching across marketplaces."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4 — SALES VS RELIST ATTRIBUTION
# ─────────────────────────────────────────────────────────────────────────────

_SOLD_CONF_RULES = """
Sold requires:
  - listing disappears (is_active=False or absent from latest listing_snapshot window)
  - does NOT reappear in next snapshot window (same section+row+qty at similar price)
  - event nearing start date strengthens confidence (≤2d = high, ≤7d = medium)
  - inventory decreases across marketplaces in same window strengthens confidence
"""


def _classify_transition(
    prev_qty: int, curr_qty: int | None,
    prev_price: float, curr_price: float | None,
    days_until: float,
    reappeared: bool,
    mp_inv_decreased: bool,
) -> dict:
    """
    Classify a single listing's state transition between two snapshot windows.
    Returns {classification, confidence, reasoning}.
    """
    if curr_qty is not None:
        # Still present
        if curr_price is not None and abs(curr_price - prev_price) > 0.50:
            change_pct = abs(curr_price - prev_price) / prev_price * 100
            return {
                "classification": "price_changed",
                "confidence": "high",
                "price_delta": round(curr_price - prev_price, 2),
                "price_delta_pct": round(change_pct, 1),
            }
        if curr_qty != prev_qty:
            return {
                "classification": "quantity_changed",
                "confidence": "high",
                "qty_delta": curr_qty - prev_qty,
            }
        return {"classification": "active", "confidence": "high"}

    # Disappeared
    if reappeared:
        return {
            "classification": "likely_relisted",
            "confidence": "medium",
            "reasoning": "same identity key reappeared in next window at different price",
        }

    # Disappeared and NOT reappeared
    # Build confidence score
    score = 0
    reasons = []
    if days_until <= 2:
        score += 3
        reasons.append("event ≤2 days away")
    elif days_until <= 7:
        score += 2
        reasons.append("event ≤7 days away")
    elif days_until <= 14:
        score += 1
        reasons.append("event ≤14 days away")

    if mp_inv_decreased:
        score += 2
        reasons.append("cross-mp inventory also decreased this window")

    if score >= 4:
        conf = "high"
        cls = "likely_sold"
    elif score >= 2:
        conf = "medium"
        cls = "likely_sold"
    elif days_until > 14:
        conf = "medium"
        cls = "withdrawn"   # disappeared >14d before event — likely seller withdrawal, not a sale
    else:
        conf = "low"
        cls = "disappeared"  # not enough evidence to call sold

    return {"classification": cls, "confidence": conf, "reasoning": "; ".join(reasons) or "insufficient_evidence"}


@router.get("/events/{event_id}/attribution")
async def sales_attribution(
    event_id: int,
    windows: int = Query(5, ge=2, le=20),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 4: Sales vs relist attribution from listing_snapshots.

    Analyzes consecutive snapshot windows to classify each listing's movement.
    Only runs on events where listing_snapshot data exists (≥2 windows).

    Classifications:
      active          – present and unchanged
      price_changed   – present, price shifted
      quantity_changed – present, quantity shifted
      likely_sold     – disappeared, not reappeared, near event
      disappeared     – disappeared, insufficient evidence to call sold
      likely_relisted – disappeared then reappeared with different price
      new_listing     – appeared for first time
    """
    now = NOW()

    # ── Event info ─────────────────────────────────────────────────────────────
    event_q = await db.execute(select(Event).where(Event.id == event_id))
    event = event_q.scalar_one_or_none()
    if not event:
        return {"error": "event not found"}

    days_until = (event.event_date - now).total_seconds() / 86400

    # ── Fetch recent snapshot windows ─────────────────────────────────────────
    # Get the last N distinct snapshot windows (hour-bucketed)
    windows_sql = text("""
        SELECT DISTINCT DATE_TRUNC('hour', snapshot_at) AS snap_window
        FROM listing_snapshots
        WHERE event_id = :event_id
        ORDER BY snap_window DESC
        LIMIT :n
    """)
    win_result = await db.execute(windows_sql, {"event_id": event_id, "n": windows})
    snap_windows = sorted([row[0] for row in win_result.fetchall()])

    if len(snap_windows) < 2:
        return {
            "event_id": event_id,
            "title": event.title,
            "days_until_event": round(days_until, 1),
            "verdict": "insufficient_history",
            "note": f"Need ≥2 snapshot windows. Found: {len(snap_windows)}",
        }

    # ── Load all snapshots in these windows ───────────────────────────────────
    win_start = snap_windows[0]
    win_end = snap_windows[-1] + timedelta(hours=1)

    snap_sql = text("""
        SELECT ls.listing_id, ls.marketplace_id, m.slug,
               ls.quantity, ls.price, ls.fees,
               l.section_id, l.row, l.section,
               DATE_TRUNC('hour', ls.snapshot_at) AS snap_window
        FROM listing_snapshots ls
        JOIN marketplaces m ON m.id = ls.marketplace_id
        JOIN listings l ON l.id = ls.listing_id
        WHERE ls.event_id = :event_id
          AND ls.snapshot_at >= CAST(:win_start AS timestamp)
          AND ls.snapshot_at < CAST(:win_end AS timestamp)
        ORDER BY ls.listing_id, snap_window
    """)
    snap_result = await db.execute(snap_sql, {
        "event_id": event_id,
        "win_start": win_start,
        "win_end": win_end,
    })
    snap_rows = snap_result.fetchall()

    # Group by listing_id → {window → snap_data}
    by_listing: dict[int, dict] = defaultdict(dict)
    listing_meta: dict[int, dict] = {}
    for row in snap_rows:
        lid, mp_id, slug, qty, price, fees, sec_id, row_val, sec, win = row
        by_listing[lid][win] = {"qty": qty, "price": float(price), "fees": float(fees) if fees else None}
        if lid not in listing_meta:
            listing_meta[lid] = {
                "marketplace": slug,
                "section_id": sec_id,
                "row": row_val,
                "section": sec,
            }

    # ── Per-window inventory totals (for cross-mp signal) ─────────────────────
    win_totals: dict[datetime, int] = defaultdict(int)
    for lid, wins in by_listing.items():
        for w, data in wins.items():
            win_totals[w] += data["qty"]

    # ── Analyze transitions ────────────────────────────────────────────────────
    # For each consecutive window pair, classify each listing
    transitions: list[dict] = []
    summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for i in range(len(snap_windows) - 1):
        w_prev = snap_windows[i]
        w_curr = snap_windows[i + 1]
        mp_inv_decreased = win_totals[w_curr] < win_totals[w_prev]

        # All listings seen in either window
        all_lids = set(lid for lid, wins in by_listing.items() if w_prev in wins or w_curr in wins)

        for lid in all_lids:
            prev_snap = by_listing[lid].get(w_prev)
            curr_snap = by_listing[lid].get(w_curr)
            meta = listing_meta.get(lid, {})
            mp = meta.get("marketplace", "?")

            if prev_snap is None:
                # New listing
                result = {"classification": "new_listing", "confidence": "high"}
            else:
                # Check if it reappeared after this window
                future_windows = snap_windows[i + 2:]
                reappeared = any(w in by_listing[lid] for w in future_windows)

                result = _classify_transition(
                    prev_qty=prev_snap["qty"],
                    curr_qty=curr_snap["qty"] if curr_snap else None,
                    prev_price=prev_snap["price"],
                    curr_price=curr_snap["price"] if curr_snap else None,
                    days_until=days_until,
                    reappeared=reappeared,
                    mp_inv_decreased=mp_inv_decreased,
                )

            result["listing_id"] = lid
            result["marketplace"] = mp
            result["window_prev"] = w_prev.isoformat()
            result["window_curr"] = w_curr.isoformat()
            result["section"] = meta.get("section_id") or meta.get("section")
            result["row"] = meta.get("row")
            result["prev_qty"] = prev_snap["qty"] if prev_snap else None
            result["prev_price"] = prev_snap["price"] if prev_snap else None
            result["curr_qty"] = curr_snap["qty"] if curr_snap else None
            result["curr_price"] = curr_snap["price"] if curr_snap else None
            transitions.append(result)

            summary[mp][result["classification"]] += 1

    # ── Aggregate counts ───────────────────────────────────────────────────────
    total_by_class: dict[str, int] = defaultdict(int)
    sold_high = 0
    sold_medium = 0
    sold_low = 0
    for t in transitions:
        total_by_class[t["classification"]] += 1
        if t["classification"] == "likely_sold":
            if t.get("confidence") == "high":
                sold_high += 1
            elif t.get("confidence") == "medium":
                sold_medium += 1
            else:
                sold_low += 1

    # ── Top sold/disappeared per marketplace ───────────────────────────────────
    mp_summary = []
    for mp, counts in sorted(summary.items()):
        mp_summary.append({
            "marketplace": mp,
            "active": counts.get("active", 0),
            "price_changed": counts.get("price_changed", 0),
            "new_listing": counts.get("new_listing", 0),
            "likely_sold": counts.get("likely_sold", 0),
            "disappeared": counts.get("disappeared", 0),
            "withdrawn": counts.get("withdrawn", 0),
            "likely_relisted": counts.get("likely_relisted", 0),
            "quantity_changed": counts.get("quantity_changed", 0),
        })

    return {
        "event_id": event_id,
        "title": event.title,
        "event_date": event.event_date.isoformat(),
        "days_until_event": round(days_until, 1),
        "snapshot_windows_analyzed": len(snap_windows),
        "window_range": {
            "from": snap_windows[0].isoformat(),
            "to": snap_windows[-1].isoformat(),
        },
        "total_transitions_analyzed": len(transitions),
        "classification_summary": dict(total_by_class),
        "sold_confidence_breakdown": {
            "high": sold_high,
            "medium": sold_medium,
            "low": sold_low,
        },
        "by_marketplace": mp_summary,
        # Include transitions only if not too large (cap at 500 for readability)
        "transitions": transitions[:500] if len(transitions) <= 500 else None,
        "transitions_truncated": len(transitions) > 500,
        "note": "Sold confidence uses: proximity to event date + cross-marketplace inventory decrease signal",
    }


# ─────────────────────────────────────────────────────────────────────────────
# COMBINED NEAR-TERM INTELLIGENCE REPORT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/intelligence/near-term")
async def near_term_intelligence(
    days_ahead: int = Query(14, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """
    Combined intelligence report for events within `days_ahead` days.
    Runs all four analyses and returns a unified summary per event.
    """
    now = NOW()
    cutoff = now + timedelta(days=days_ahead)

    events_q = await db.execute(
        select(Event)
        .where(and_(Event.event_date >= now, Event.event_date <= cutoff))
        .order_by(Event.event_date)
    )
    events = events_q.scalars().all()

    results = []
    for event in events:
        days_until = (event.event_date - now).total_seconds() / 86400

        # Quick freshness probe: last_polled_at, consecutive errors
        te_q = await db.execute(
            select(TrackedEvent, Marketplace.slug)
            .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
            .where(TrackedEvent.event_id == event.id)
        )
        te_rows = te_q.all()

        mp_freshness = []
        for te, slug in te_rows:
            # Count recent consecutive errors
            recent_polls_q = await db.execute(
                select(PollRun.status)
                .where(PollRun.tracked_event_id == te.id)
                .order_by(PollRun.started_at.desc())
                .limit(5)
            )
            recent_statuses = [r[0] for r in recent_polls_q.fetchall()]
            consecutive_errors = 0
            for s in recent_statuses:
                if s in ("error", "failed", "timeout"):
                    consecutive_errors += 1
                else:
                    break
            listing_count_q = await db.execute(
                select(func.count(Listing.id))
                .where(and_(Listing.event_id == event.id,
                            Listing.marketplace_id == te.marketplace_id,
                            Listing.is_active == True))
            )
            listing_count = listing_count_q.scalar_one() or 0
            status = _freshness_status(
                te.last_polled_at, te.next_poll_at,
                te.poll_interval_minutes or 60, te.is_active,
                listing_count > 0, consecutive_errors,
            )
            age_min = round((now - te.last_polled_at).total_seconds() / 60, 1) if te.last_polled_at else None
            mp_freshness.append({"marketplace": slug, "status": status, "age_minutes": age_min,
                                  "listings": listing_count, "consecutive_errors": consecutive_errors})

        # Quick snapshot probe
        snap_sql = text("""
            SELECT MAX(snapshot_at), COUNT(*) FROM canonical_inventory_snapshots WHERE event_id = :eid
        """)
        snap_r = (await db.execute(snap_sql, {"eid": event.id})).fetchone()
        snap_at = snap_r[0].isoformat() if snap_r and snap_r[0] else None
        snap_count = snap_r[1] if snap_r else 0
        snap_lag_h = round((now - snap_r[0]).total_seconds() / 3600, 1) if snap_r and snap_r[0] else None

        # Quick live inventory probe
        live_q = await db.execute(
            select(func.count(Listing.id), func.sum(Listing.quantity))
            .where(and_(Listing.event_id == event.id, Listing.is_active == True))
        )
        live_row = live_q.fetchone()
        live_listings = live_row[0] or 0
        live_tickets = live_row[1] or 0

        # Quick attribution headline
        win_count_q = await db.execute(text("""
            SELECT COUNT(DISTINCT DATE_TRUNC('hour', snapshot_at))
            FROM listing_snapshots WHERE event_id = :eid
        """), {"eid": event.id})
        win_count = win_count_q.scalar_one() or 0

        overall_freshness = min(
            mp_freshness,
            key=lambda x: {"broken": 0, "stale": 1, "late": 2,
                           "not_listed": 3, "inactive": 4, "fresh": 5}.get(x["status"], 9),
            default={"status": "unknown"},
        )["status"] if mp_freshness else "unknown"

        results.append({
            "event_id": event.id,
            "title": event.title,
            "event_date": event.event_date.isoformat(),
            "days_until_event": round(days_until, 1),
            "freshness": {
                "overall": overall_freshness,
                "by_marketplace": mp_freshness,
            },
            "inventory": {
                "live_listings": live_listings,
                "live_tickets": live_tickets,
            },
            "snapshots": {
                "count": snap_count,
                "latest_at": snap_at,
                "lag_hours": snap_lag_h,
            },
            "attribution_windows_available": win_count,
            "endpoints": {
                "snapshot_consistency": f"/api/analytics/events/{event.id}/snapshot-consistency",
                "duplicate_analysis": f"/api/analytics/events/{event.id}/duplicate-analysis",
                "attribution": f"/api/analytics/events/{event.id}/attribution",
            },
        })

    return {
        "generated_at": now.isoformat(),
        "days_ahead": days_ahead,
        "event_count": len(results),
        "events": results,
    }
