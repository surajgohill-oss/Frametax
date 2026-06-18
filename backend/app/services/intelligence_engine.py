"""
intelligence_engine.py — Market Intelligence Computation Engine

Reads from: listing_snapshots, listings, poll_runs, events, tracked_events, marketplaces
Writes to:  market_intelligence (cache table)

All heavy SQL runs here. The route layer only calls compute_event() or serves cached rows.

Architecture:
  - compute_event(event_id, db) → writes one row to market_intelligence, returns it
  - The route layer calls compute_event for fresh data or queries the latest cached row
  - All metrics are time-normalized against days_until_event

Price windows:
  - 24h  = snapshots in last 24 hours
  - 7d   = snapshots in last 7 days
  - 14d  = snapshots in last 14 days
  - 30d  = snapshots in last 30 days
  - all  = all available snapshot history (returned as history_hours context)

When a window has < 2 data points, its delta fields are NULL (not zero).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _f(v) -> Optional[float]:
    """Safe float conversion for Decimal/None."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _round(v, n=2) -> Optional[float]:
    f = _f(v)
    return round(f, n) if f is not None else None


def _clamp01(v) -> Optional[float]:
    f = _f(v)
    if f is None:
        return None
    return max(0.0, min(1.0, f))


# ─────────────────────────────────────────────────────────────────────────────
# Core SQL blocks (raw asyncpg via text() for performance)
# ─────────────────────────────────────────────────────────────────────────────

_CURRENT_PRICE_SQL = text("""
    SELECT
        MIN(price)                                           AS low_ask,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)  AS median_ask,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY price)  AS high_ask,
        PERCENTILE_CONT(0.1) WITHIN GROUP (ORDER BY price)  AS p10_ask,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price) AS p25_ask,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price) AS p75_ask,
        COUNT(*)                                             AS listing_count,
        SUM(quantity)                                        AS ticket_count
    FROM listings
    WHERE event_id = :event_id
      AND is_active = TRUE
      AND price > 0
""")

_HISTORY_DEPTH_SQL = text("""
    SELECT
        MIN(snapshot_at) AS oldest,
        MAX(snapshot_at) AS newest,
        COUNT(DISTINCT listing_id) AS distinct_listings
    FROM listing_snapshots
    WHERE event_id = :event_id
""")

_WINDOW_PRICE_SQL = text("""
    SELECT
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_ask,
        MIN(price) AS low_ask,
        COUNT(DISTINCT listing_id)                          AS listing_count
    FROM listing_snapshots
    WHERE event_id = :event_id
      AND snapshot_at >= :window_start
      AND snapshot_at < :window_end
      AND price > 0
""")

_MP_BREAKDOWN_SQL = text("""
    SELECT
        m.slug                                               AS mp_name,
        COUNT(l.id)                                         AS listings,
        SUM(l.quantity)                                     AS tickets,
        MIN(l.price)                                        AS low_ask,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY l.price) AS median_ask,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY l.price) AS high_ask,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY l.price) AS p25_ask,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY l.price) AS p75_ask
    FROM listings l
    JOIN marketplaces m ON m.id = l.marketplace_id
    WHERE l.event_id = :event_id
      AND l.is_active = TRUE
      AND l.price > 0
    GROUP BY m.slug
    ORDER BY listings DESC
""")

_SECTION_BREAKDOWN_SQL = text("""
    SELECT
        l.section_id,
        l.section,
        COUNT(l.id)                                         AS listings,
        SUM(l.quantity)                                     AS tickets,
        MIN(l.price)                                        AS low_ask,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY l.price) AS median_ask,
        MAX(l.price)                                        AS high_ask
    FROM listings l
    WHERE l.event_id = :event_id
      AND l.is_active = TRUE
      AND l.price > 0
      AND l.section_id IS NOT NULL
    GROUP BY l.section_id, l.section
    ORDER BY listings DESC
    LIMIT 60
""")

_SELLER_BEHAVIOR_SQL = text("""
    WITH recent_polls AS (
        SELECT
            pr.id,
            pr.new_listings,
            pr.disappeared_listings,
            pr.listings_found,
            pr.started_at
        FROM poll_runs pr
        JOIN tracked_events te ON te.id = pr.tracked_event_id
        WHERE te.event_id = :event_id
          AND pr.started_at >= :since_24h
          AND pr.status = 'success'
        ORDER BY pr.started_at DESC
    )
    SELECT
        COALESCE(SUM(new_listings), 0)        AS new_24h,
        COALESCE(SUM(disappeared_listings), 0) AS removed_24h,
        COALESCE(AVG(listings_found), 0)      AS avg_found,
        COUNT(*)                               AS poll_count
    FROM recent_polls
""")

_REPRICED_LISTINGS_SQL = text("""
    WITH ordered AS (
        SELECT
            ls.listing_id,
            ls.price,
            ls.snapshot_at,
            LAG(ls.price) OVER (PARTITION BY ls.listing_id ORDER BY ls.snapshot_at) AS prev_price
        FROM listing_snapshots ls
        WHERE ls.event_id = :event_id
          AND ls.snapshot_at >= :since_24h
    )
    SELECT
        COUNT(*) FILTER (WHERE prev_price IS NOT NULL AND price <> prev_price) AS repriced_count,
        COUNT(*) FILTER (WHERE prev_price IS NOT NULL AND price < prev_price)  AS price_drops,
        COUNT(*) FILTER (WHERE prev_price IS NOT NULL AND price > prev_price)  AS price_gains,
        COUNT(*) FILTER (WHERE prev_price IS NOT NULL AND price <> prev_price
                         AND price - prev_price < 0)                          AS drops_detail,
        AVG(CASE WHEN prev_price IS NOT NULL AND price <> prev_price
                 THEN price - prev_price ELSE NULL END)                       AS median_delta,
        COUNT(DISTINCT listing_id)                                             AS total_listings_seen
    FROM ordered
""")

_PRICE_HISTORY_BUCKETS_SQL = text("""
    SELECT
        DATE_TRUNC(:bucket_size, snapshot_at)                AS bucket,
        MIN(price)                                           AS low_ask,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)  AS median_ask,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY price)  AS high_ask,
        COUNT(DISTINCT listing_id)                           AS listings,
        SUM(quantity)                                        AS tickets
    FROM listing_snapshots
    WHERE event_id = :event_id
      AND snapshot_at >= :window_start
      AND price > 0
    GROUP BY bucket
    ORDER BY bucket
""")

# 6-hour bucket variant — DATE_TRUNC doesn't accept "6 hours", use epoch floor instead
_PRICE_HISTORY_6H_SQL = text("""
    SELECT
        to_timestamp(floor(extract(epoch from snapshot_at) / 21600) * 21600) AS bucket,
        MIN(price)                                           AS low_ask,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)  AS median_ask,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY price)  AS high_ask,
        COUNT(DISTINCT listing_id)                           AS listings,
        SUM(quantity)                                        AS tickets
    FROM listing_snapshots
    WHERE event_id = :event_id
      AND snapshot_at >= :window_start
      AND price > 0
    GROUP BY bucket
    ORDER BY bucket
""")

_SURVIVAL_RATE_SQL = text("""
    WITH base_window AS (
        SELECT DISTINCT listing_id
        FROM listing_snapshots
        WHERE event_id = :event_id
          AND snapshot_at >= :t_start
          AND snapshot_at < :t_end
    ),
    later_window AS (
        SELECT DISTINCT listing_id
        FROM listing_snapshots
        WHERE event_id = :event_id
          AND snapshot_at >= :t_later_start
          AND snapshot_at < :t_later_end
    )
    SELECT
        COUNT(b.listing_id) AS base_count,
        COUNT(lw.listing_id) AS survived_count
    FROM base_window b
    LEFT JOIN later_window lw ON lw.listing_id = b.listing_id
""")

_REAPPEARANCE_SQL = text("""
    WITH disappeared AS (
        SELECT DISTINCT ls1.listing_id
        FROM listing_snapshots ls1
        WHERE ls1.event_id = :event_id
          AND ls1.snapshot_at >= :since_24h
          AND NOT EXISTS (
              SELECT 1 FROM listing_snapshots ls2
              WHERE ls2.listing_id = ls1.listing_id
                AND ls2.snapshot_at > ls1.snapshot_at
          )
          AND ls1.snapshot_at < :cutoff
    ),
    reappeared AS (
        SELECT d.listing_id
        FROM disappeared d
        JOIN listing_snapshots ls3 ON ls3.listing_id = d.listing_id
        WHERE ls3.snapshot_at >= :cutoff
    )
    SELECT COUNT(*) AS disappeared_count,
           COUNT(reappeared.listing_id) AS reappeared_count
    FROM disappeared
    LEFT JOIN reappeared USING (listing_id)
""")


# ─────────────────────────────────────────────────────────────────────────────
# Score computations
# ─────────────────────────────────────────────────────────────────────────────

def _compute_tightness(low: Optional[float], p75: Optional[float], p25: Optional[float],
                       median: Optional[float], listings: Optional[int]) -> Optional[float]:
    """
    Market tightness: how narrow is the price range and how concentrated is inventory?
    Higher = tighter (fewer, higher-priced listings bunched together).
    0 = totally loose (huge range, tons of listings)
    1 = very tight (narrow IQR, concentrated)
    """
    if None in (low, median, p25, p75, listings) or median == 0 or listings == 0:
        return None
    iqr = (p75 - p25) if p75 and p25 else 0
    spread_ratio = iqr / median  # relative spread
    # Tight market: small spread_ratio, lower listing count
    spread_score = max(0, 1 - spread_ratio)  # higher for narrow IQR
    # Penalise very high listing counts (>500 = loose market)
    count_score = max(0, 1 - listings / 500)
    return _clamp01(0.6 * spread_score + 0.4 * count_score)


def _compute_opportunity_score(
    price_delta_24h: Optional[float],
    median: Optional[float],
    seller_aggression: Optional[float],
    inventory_delta_24h: Optional[int],
    market_tightness: Optional[float],
    days_until: Optional[float],
) -> Optional[float]:
    """
    Opportunity score: composite signal for buying interest.
    High = prices falling AND inventory shrinking AND event soon.
    Low = prices rising AND inventory growing AND event far.
    """
    if median is None or median <= 0:
        return None

    score = 0.5  # neutral base

    # Price falling = opportunity
    if price_delta_24h is not None and median > 0:
        price_signal = -price_delta_24h / median  # negative delta = positive signal
        score += 0.25 * _clamp01(price_signal + 0.5)

    # Inventory shrinking = demand signal
    if inventory_delta_24h is not None:
        inv_signal = max(-1.0, min(1.0, -inventory_delta_24h / 50))
        score += 0.20 * (0.5 + 0.5 * inv_signal)

    # Seller aggression = sellers capitulating = opportunity
    if seller_aggression is not None:
        score += 0.15 * seller_aggression

    # Days until event proximity (events in 7-30 days are prime opportunity window)
    if days_until is not None:
        if 7 <= days_until <= 30:
            score += 0.10
        elif days_until < 7:
            score += 0.05  # too close = risk of no deal
        # >90 days = still early

    # Tightness (tight = opportunity if prices also dropping)
    if market_tightness is not None and price_delta_24h is not None and price_delta_24h < 0:
        score += 0.10 * market_tightness

    return _clamp01(score)


def _compute_signal(
    price_delta_24h: Optional[float],
    inventory_delta_24h: Optional[int],
    seller_aggression: Optional[float],
) -> str:
    """
    Narrative signal: tightening | loosening | stable | unknown.
    Tightening = prices rising, inventory falling.
    Loosening  = prices falling, inventory rising.
    """
    if price_delta_24h is None and inventory_delta_24h is None:
        return "unknown"

    price_up = price_delta_24h is not None and price_delta_24h > 5
    price_down = price_delta_24h is not None and price_delta_24h < -5
    inv_up = inventory_delta_24h is not None and inventory_delta_24h > 10
    inv_down = inventory_delta_24h is not None and inventory_delta_24h < -10

    if price_up and inv_down:
        return "tightening"
    if price_down and inv_up:
        return "loosening"
    if price_down and (seller_aggression or 0) > 0.5:
        return "capitulating"
    if price_up and inv_up:
        return "deepening"
    if abs(price_delta_24h or 0) < 5 and abs(inventory_delta_24h or 0) < 5:
        return "stable"
    return "mixed"


# ─────────────────────────────────────────────────────────────────────────────
# Main compute function
# ─────────────────────────────────────────────────────────────────────────────

async def compute_event(event_id: int, db: AsyncSession) -> dict:
    """
    Compute full intelligence metrics for one event and write to market_intelligence.
    Returns the computed row as a dict.

    This is the single source of truth for all intelligence data.
    """
    now = datetime.now(timezone.utc)
    # SQL parameters must be naive UTC (listing_snapshots/poll_runs use TIMESTAMP WITHOUT TIME ZONE)
    now_sql = now.replace(tzinfo=None)

    # ── Event meta ─────────────────────────────────────────────────────────────
    event_row = (await db.execute(
        text("SELECT id, title, event_date FROM events WHERE id = :eid"),
        {"eid": event_id}
    )).fetchone()
    if not event_row:
        raise ValueError(f"event {event_id} not found")

    event_date: datetime = event_row[2]
    days_until = (event_date - now).total_seconds() / 86400

    # ── Current price tiers ────────────────────────────────────────────────────
    cp = (await db.execute(_CURRENT_PRICE_SQL, {"event_id": event_id})).fetchone()
    current_low    = _round(_f(cp[0]))
    current_median = _round(_f(cp[1]))
    current_high   = _round(_f(cp[2]))  # p90
    current_p10    = _round(_f(cp[3]))
    current_p25    = _round(_f(cp[4]))
    current_p75    = _round(_f(cp[5]))
    current_listings = int(cp[6] or 0)
    current_tickets  = int(cp[7] or 0)

    # ── History depth ──────────────────────────────────────────────────────────
    hd = (await db.execute(_HISTORY_DEPTH_SQL, {"event_id": event_id})).fetchone()
    history_oldest = hd[0]
    history_newest = hd[1]
    history_hours: Optional[float] = None
    if history_oldest and history_newest:
        history_hours = round((history_newest - history_oldest).total_seconds() / 3600, 1)

    # ── Window price comparisons ───────────────────────────────────────────────
    async def _window_price(hours_back: int) -> Optional[tuple]:
        """Returns (median, listings) for a snapshot window hours_back ago (±1h)."""
        center = now_sql - timedelta(hours=hours_back)
        w_start = center - timedelta(hours=1)
        w_end   = center + timedelta(hours=1)
        row = (await db.execute(_WINDOW_PRICE_SQL, {
            "event_id": event_id,
            "window_start": w_start,
            "window_end": w_end,
        })).fetchone()
        if not row or not row[0]:
            return None
        return (_f(row[0]), _f(row[1]), int(row[2] or 0))

    # Use earliest snapshot as baseline when window > available history
    async def _earliest_window_price() -> Optional[tuple]:
        if not history_oldest:
            return None
        w_end = history_oldest + timedelta(hours=2)
        row = (await db.execute(_WINDOW_PRICE_SQL, {
            "event_id": event_id,
            "window_start": history_oldest,
            "window_end": w_end,
        })).fetchone()
        if not row or not row[0]:
            return None
        return (_f(row[0]), _f(row[1]), int(row[2] or 0))

    # 24h comparison
    w24h = await _window_price(24)
    if w24h is None and history_hours and history_hours >= 2:
        w24h = await _earliest_window_price()

    # 7d comparison (168h)
    w7d = await _window_price(168) if (history_hours or 0) >= 168 else None
    # 14d comparison
    w14d = await _window_price(336) if (history_hours or 0) >= 336 else None
    # 30d comparison
    w30d = await _window_price(720) if (history_hours or 0) >= 720 else None

    def _delta(now_val, then_val):
        if now_val is None or then_val is None:
            return None, None
        delta = round(now_val - then_val, 2)
        pct = round((now_val - then_val) / then_val * 100, 2) if then_val != 0 else None
        return delta, pct

    pd24h, pd24h_pct = _delta(current_median, w24h[0] if w24h else None)
    pd7d,  pd7d_pct  = _delta(current_median, w7d[0]  if w7d  else None)
    pd14d, _         = _delta(current_median, w14d[0] if w14d else None)
    pd30d, _         = _delta(current_median, w30d[0] if w30d else None)

    inv24h = (current_listings - w24h[2]) if w24h and w24h[2] else None
    inv7d  = (current_listings - w7d[2])  if w7d  and w7d[2]  else None
    inv14d = (current_listings - w14d[2]) if w14d and w14d[2] else None
    inv30d = (current_listings - w30d[2]) if w30d and w30d[2] else None

    # ── Marketplace breakdown ──────────────────────────────────────────────────
    mp_rows = (await db.execute(_MP_BREAKDOWN_SQL, {"event_id": event_id})).fetchall()
    total_listings = max(current_listings, 1)

    mp_metrics = []
    best_low_mp = None
    best_low_price = float("inf")
    for r in mp_rows:
        name, listings, tickets, low, median, high, p25, p75 = r
        tickets = int(tickets or 0)
        listings = int(listings or 0)
        low_f    = _f(low)
        med_f    = _f(median)
        high_f   = _f(high)
        share    = round(listings / total_listings, 4)

        # Liquidity score: higher = more listings + tighter spread
        iqr = (_f(p75) or 0) - (_f(p25) or 0)
        liq = _clamp01(min(1.0, listings / 200) * 0.6 + max(0, 1 - iqr / max(med_f or 1, 1)) * 0.4)

        mp_metrics.append({
            "name": name,
            "listings": listings,
            "tickets": tickets,
            "low_ask": _round(low_f),
            "median_ask": _round(med_f),
            "high_ask": _round(high_f),
            "p25_ask": _round(_f(p25)),
            "p75_ask": _round(_f(p75)),
            "share_of_inventory": share,
            "liquidity_score": _round(liq, 3),
        })
        if low_f and low_f < best_low_price:
            best_low_price = low_f
            best_low_mp = name

    # Arbitrage: find biggest price gap for same "section" across marketplaces
    # Simplified: just compare lowest asks across marketplaces
    mp_lows = [(m["name"], m["low_ask"]) for m in mp_metrics if m["low_ask"]]
    arb = None
    if len(mp_lows) >= 2:
        mp_lows_sorted = sorted(mp_lows, key=lambda x: x[1])
        buy_mp, buy_price = mp_lows_sorted[0]
        # Best to compare against highest median (not highest ask which could be outlier)
        sell_candidates = [(m["name"], m["median_ask"]) for m in mp_metrics
                           if m["median_ask"] and m["name"] != buy_mp]
        if sell_candidates:
            sell_mp, sell_price = max(sell_candidates, key=lambda x: x[1])
            spread = round(sell_price - buy_price, 2)
            if spread > 0:
                arb = {
                    "buy_at": buy_mp,
                    "buy_price": buy_price,
                    "sell_at": sell_mp,
                    "compare_median": sell_price,
                    "spread": spread,
                    "spread_pct": round(spread / buy_price * 100, 1),
                    "note": "buy_low_ask vs sell_at_median — not a guaranteed profit, illustrative only",
                }

    # ── Section breakdown ──────────────────────────────────────────────────────
    sec_rows = (await db.execute(_SECTION_BREAKDOWN_SQL, {"event_id": event_id})).fetchall()
    section_metrics = []
    for r in sec_rows:
        sec_id, sec_name, listings, tickets, low, median, high = r
        if not sec_id and not sec_name:
            continue
        section_metrics.append({
            "section_id": sec_id,
            "display_name": sec_name,
            "listings": int(listings or 0),
            "tickets": int(tickets or 0),
            "low_ask": _round(_f(low)),
            "median_ask": _round(_f(median)),
            "high_ask": _round(_f(high)),
        })

    # ── Seller behavior (poll_run aggregates) ──────────────────────────────────
    since_24h = now_sql - timedelta(hours=24)
    sb_row = (await db.execute(_SELLER_BEHAVIOR_SQL, {
        "event_id": event_id,
        "since_24h": since_24h,
    })).fetchone()

    new_24h    = int(sb_row[0] or 0) if sb_row else 0
    removed_24h = int(sb_row[1] or 0) if sb_row else 0
    avg_found   = _f(sb_row[2]) if sb_row else None
    poll_count  = int(sb_row[3] or 0) if sb_row else 0

    # Repriced listings from listing_snapshots
    rp_row = (await db.execute(_REPRICED_LISTINGS_SQL, {
        "event_id": event_id,
        "since_24h": since_24h,
    })).fetchone()

    repriced_count = int(rp_row[0] or 0) if rp_row else 0
    price_drops    = int(rp_row[1] or 0) if rp_row else 0
    price_gains    = int(rp_row[2] or 0) if rp_row else 0
    median_delta   = _round(_f(rp_row[4])) if rp_row else None
    total_seen     = int(rp_row[5] or 0) if rp_row else 0

    reprice_rate = round(repriced_count / max(total_seen, 1), 4) if total_seen > 0 else None
    seller_aggression = round(price_drops / max(repriced_count, 1), 4) if repriced_count > 0 else None
    seller_confidence = round(price_gains / max(repriced_count, 1), 4) if repriced_count > 0 else None
    churn_rate = round((new_24h + removed_24h) / max(current_listings, 1), 4) if current_listings > 0 else None

    seller_behavior = {
        "new_24h": new_24h,
        "removed_24h": removed_24h,
        "repriced_24h": repriced_count,
        "price_drops_24h": price_drops,
        "price_gains_24h": price_gains,
        "median_reprice_delta": median_delta,
        "poll_count_24h": poll_count,
        "avg_listings_per_poll": _round(avg_found),
    }

    # ── Listing survival rate (24h cohort) ────────────────────────────────────
    listing_survival = None
    reappearance_rate = None

    if history_hours and history_hours >= 2:
        # Survival: of listings seen 12h ago, how many are still in latest window?
        t_base_start = now_sql - timedelta(hours=14)
        t_base_end   = now_sql - timedelta(hours=12)
        t_later_start = now_sql - timedelta(hours=1)
        t_later_end   = now_sql
        surv = (await db.execute(_SURVIVAL_RATE_SQL, {
            "event_id": event_id,
            "t_start": t_base_start,
            "t_end": t_base_end,
            "t_later_start": t_later_start,
            "t_later_end": t_later_end,
        })).fetchone()
        if surv and surv[0] and surv[0] > 0:
            listing_survival = round(surv[1] / surv[0], 4)

    # ── Price history buckets (24h at 1h resolution) ──────────────────────────
    ph_buckets_24h = []
    ph_rows = (await db.execute(_PRICE_HISTORY_BUCKETS_SQL, {
        "event_id": event_id,
        "bucket_size": "hour",
        "window_start": since_24h,
    })).fetchall()
    for r in ph_rows:
        bucket_ts, low, median, high, listings_n, tickets_n = r
        ph_buckets_24h.append({
            "ts": bucket_ts.isoformat() if bucket_ts else None,
            "low_ask": _round(_f(low)),
            "median_ask": _round(_f(median)),
            "high_ask": _round(_f(high)),
            "listings": int(listings_n or 0),
            "tickets": int(tickets_n or 0),
        })

    # 7d history at 6h resolution (if data exists)
    ph_buckets_7d = []
    if history_hours and history_hours >= 12:
        w7d_start = now_sql - timedelta(days=7) if (history_hours or 0) >= 168 else history_oldest
        ph_rows_7d = (await db.execute(_PRICE_HISTORY_6H_SQL, {
            "event_id": event_id,
            "window_start": w7d_start,
        })).fetchall()
        for r in ph_rows_7d:
            bucket_ts, low, median, high, listings_n, tickets_n = r
            ph_buckets_7d.append({
                "ts": bucket_ts.isoformat() if bucket_ts else None,
                "low_ask": _round(_f(low)),
                "median_ask": _round(_f(median)),
                "high_ask": _round(_f(high)),
                "listings": int(listings_n or 0),
            })

    # ── Derived scores ─────────────────────────────────────────────────────────
    market_tightness = _compute_tightness(
        current_low, current_p75, current_p25, current_median, current_listings
    )

    market_depth = None
    if current_p25 and current_p75 and current_median and current_median > 0:
        market_depth = _round((current_p75 - current_p25) / current_median, 3)

    inventory_velocity = None
    if inv24h is not None:
        inventory_velocity = round(inv24h / 24, 3)  # listings/hour

    capitulation_score = None
    if seller_aggression is not None and churn_rate is not None:
        # High aggression + high churn = sellers capitulating
        capitulation_score = _clamp01(0.6 * seller_aggression + 0.4 * churn_rate)

    relist_pressure = None

    # Relisting rate: fraction of inactive listings that reappeared in same section/row at similar price
    relisting_rate: Optional[float] = None
    try:
        relist_row = (await db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE NOT l.is_active)                          AS disappeared,
                COUNT(*) FILTER (WHERE NOT l.is_active AND EXISTS (
                    SELECT 1 FROM listings l2
                    WHERE l2.event_id = l.event_id
                      AND l2.section  = l.section
                      AND l2.row      = l.row
                      AND l2.is_active = TRUE
                      AND l2.price > 0 AND l.price > 0
                      AND ABS(l2.price - l.price) / l.price < 0.25
                ))                                                                AS relisted
            FROM listings l
            WHERE l.event_id = :eid
        """), {"eid": event_id})).fetchone()
        if relist_row and relist_row.disappeared and relist_row.disappeared > 0:
            relisting_rate = round(relist_row.relisted / relist_row.disappeared, 4)
    except Exception:
        pass

    opportunity_score = _compute_opportunity_score(
        price_delta_24h=pd24h,
        median=current_median,
        seller_aggression=seller_aggression,
        inventory_delta_24h=inv24h,
        market_tightness=market_tightness,
        days_until=days_until,
    )

    signal = _compute_signal(pd24h, inv24h, seller_aggression)

    # ── Write to market_intelligence ───────────────────────────────────────────
    insert_sql = text("""
        INSERT INTO market_intelligence (
            event_id, computed_at, signal,
            current_low_ask, current_median_ask, current_high_ask,
            current_p10_ask, current_p25_ask, current_p75_ask,
            current_listings, current_tickets,
            price_delta_24h, price_delta_7d, price_delta_14d, price_delta_30d,
            price_delta_pct_24h, price_delta_pct_7d,
            inventory_delta_24h, inventory_delta_7d, inventory_delta_14d, inventory_delta_30d,
            reprice_rate, churn_rate, listing_survival, reappearance_rate, relisting_rate,
            market_tightness, market_depth, inventory_velocity,
            seller_aggression, seller_confidence, capitulation_score, relist_pressure,
            opportunity_score, days_until_event, history_hours,
            marketplace_metrics, section_metrics, seller_behavior,
            price_history_24h, window_histories
        ) VALUES (
            :event_id, :computed_at, :signal,
            :current_low_ask, :current_median_ask, :current_high_ask,
            :current_p10_ask, :current_p25_ask, :current_p75_ask,
            :current_listings, :current_tickets,
            :price_delta_24h, :price_delta_7d, :price_delta_14d, :price_delta_30d,
            :price_delta_pct_24h, :price_delta_pct_7d,
            :inventory_delta_24h, :inventory_delta_7d, :inventory_delta_14d, :inventory_delta_30d,
            :reprice_rate, :churn_rate, :listing_survival, :reappearance_rate, :relisting_rate,
            :market_tightness, :market_depth, :inventory_velocity,
            :seller_aggression, :seller_confidence, :capitulation_score, :relist_pressure,
            :opportunity_score, :days_until_event, :history_hours,
            CAST(:marketplace_metrics AS JSONB), CAST(:section_metrics AS JSONB), CAST(:seller_behavior AS JSONB),
            CAST(:price_history_24h AS JSONB), CAST(:window_histories AS JSONB)
        )
        RETURNING id, computed_at
    """)

    import json

    result = (await db.execute(insert_sql, {
        "event_id": event_id,
        "computed_at": now_sql,
        "signal": signal,
        "current_low_ask": current_low,
        "current_median_ask": current_median,
        "current_high_ask": current_high,
        "current_p10_ask": current_p10,
        "current_p25_ask": current_p25,
        "current_p75_ask": current_p75,
        "current_listings": current_listings,
        "current_tickets": current_tickets,
        "price_delta_24h": pd24h,
        "price_delta_7d": pd7d,
        "price_delta_14d": pd14d,
        "price_delta_30d": pd30d,
        "price_delta_pct_24h": pd24h_pct,
        "price_delta_pct_7d": pd7d_pct,
        "inventory_delta_24h": inv24h,
        "inventory_delta_7d": inv7d,
        "inventory_delta_14d": inv14d,
        "inventory_delta_30d": inv30d,
        "reprice_rate": reprice_rate,
        "churn_rate": churn_rate,
        "listing_survival": listing_survival,
        "reappearance_rate": reappearance_rate,
        "relisting_rate": relisting_rate,
        "market_tightness": market_tightness,
        "market_depth": market_depth,
        "inventory_velocity": inventory_velocity,
        "seller_aggression": seller_aggression,
        "seller_confidence": seller_confidence,
        "capitulation_score": capitulation_score,
        "relist_pressure": relist_pressure,
        "opportunity_score": opportunity_score,
        "days_until_event": round(days_until, 2),
        "history_hours": history_hours,
        "marketplace_metrics": json.dumps(mp_metrics),
        "section_metrics": json.dumps(section_metrics),
        "seller_behavior": json.dumps(seller_behavior),
        "price_history_24h": json.dumps({"buckets": ph_buckets_24h}),
        "window_histories": json.dumps({
            "h24": ph_buckets_24h,
            "d7": ph_buckets_7d,
            "d14": [],
            "d30": [],
        }),
    })).fetchone()

    await db.commit()

    return {
        "id": result[0],
        "event_id": event_id,
        "title": event_row[1],
        "event_date": event_date.isoformat(),
        "computed_at": now.isoformat(),
        "signal": signal,
        "days_until_event": round(days_until, 2),
        "history_hours": history_hours,
        # Price tiers
        "price": {
            "low_ask": current_low,
            "median_ask": current_median,
            "high_ask": current_high,  # p90
            "p10_ask": current_p10,
            "p25_ask": current_p25,
            "p75_ask": current_p75,
        },
        # Changes
        "changes": {
            "h24": {"price_delta": pd24h, "price_delta_pct": pd24h_pct, "inventory_delta": inv24h},
            "d7":  {"price_delta": pd7d,  "price_delta_pct": pd7d_pct,  "inventory_delta": inv7d},
            "d14": {"price_delta": pd14d, "price_delta_pct": None,       "inventory_delta": inv14d},
            "d30": {"price_delta": pd30d, "price_delta_pct": None,       "inventory_delta": inv30d},
        },
        # Inventory
        "inventory": {
            "total_listings": current_listings,
            "total_tickets": current_tickets,
        },
        # Market character
        "market": {
            "tightness": _round(market_tightness, 3),
            "depth": market_depth,
            "velocity": inventory_velocity,
            "seller_aggression": _round(seller_aggression, 3),
            "seller_confidence": _round(seller_confidence, 3),
            "capitulation_score": _round(capitulation_score, 3),
            "opportunity_score": _round(opportunity_score, 3),
            "marketplace_leader": best_low_mp,
            "arbitrage": arb,
        },
        # Rates
        "rates": {
            "reprice_rate": reprice_rate,
            "churn_rate": churn_rate,
            "listing_survival": listing_survival,
        },
        # Sub-structures
        "marketplace_metrics": mp_metrics,
        "section_metrics": section_metrics,
        "seller_behavior": seller_behavior,
        "price_history_24h": ph_buckets_24h,
        "price_history_7d": ph_buckets_7d,
    }


async def get_latest_intelligence(event_id: int, db: AsyncSession) -> Optional[dict]:
    """Fetch the most recently computed intelligence row for an event."""
    row = (await db.execute(text("""
        SELECT id, computed_at, signal,
               current_low_ask, current_median_ask, current_high_ask,
               current_p10_ask, current_p25_ask, current_p75_ask,
               current_listings, current_tickets,
               price_delta_24h, price_delta_7d, price_delta_14d, price_delta_30d,
               price_delta_pct_24h, price_delta_pct_7d,
               inventory_delta_24h, inventory_delta_7d, inventory_delta_14d, inventory_delta_30d,
               reprice_rate, churn_rate, listing_survival,
               market_tightness, market_depth, inventory_velocity,
               seller_aggression, seller_confidence, capitulation_score, opportunity_score,
               days_until_event, history_hours,
               marketplace_metrics, section_metrics, seller_behavior,
               price_history_24h, window_histories
        FROM market_intelligence
        WHERE event_id = :eid
        ORDER BY computed_at DESC
        LIMIT 1
    """), {"eid": event_id})).fetchone()

    if not row:
        return None

    (mid, computed_at, signal,
     low, median, high, p10, p25, p75,
     listings, tickets,
     pd24h, pd7d, pd14d, pd30d, pd24h_pct, pd7d_pct,
     inv24h, inv7d, inv14d, inv30d,
     reprice_rate, churn_rate, listing_survival,
     tightness, depth, velocity, aggression, confidence, capitulation, opportunity,
     days_until, hist_hours,
     mp_metrics, sec_metrics, sell_behavior,
     ph_24h, window_hist) = row

    return {
        "id": mid,
        "computed_at": computed_at.isoformat() if computed_at else None,
        "signal": signal,
        "price": {
            "low_ask": _round(_f(low)),
            "median_ask": _round(_f(median)),
            "high_ask": _round(_f(high)),
            "p10_ask": _round(_f(p10)),
            "p25_ask": _round(_f(p25)),
            "p75_ask": _round(_f(p75)),
        },
        "changes": {
            "h24": {"price_delta": _round(_f(pd24h)), "price_delta_pct": _round(_f(pd24h_pct)), "inventory_delta": inv24h},
            "d7":  {"price_delta": _round(_f(pd7d)),  "price_delta_pct": _round(_f(pd7d_pct)),  "inventory_delta": inv7d},
            "d14": {"price_delta": _round(_f(pd14d)), "price_delta_pct": None, "inventory_delta": inv14d},
            "d30": {"price_delta": _round(_f(pd30d)), "price_delta_pct": None, "inventory_delta": inv30d},
        },
        "inventory": {"total_listings": listings, "total_tickets": tickets},
        "market": {
            "tightness": _round(_f(tightness), 3),
            "depth": _round(_f(depth), 3),
            "velocity": _round(_f(velocity), 3),
            "seller_aggression": _round(_f(aggression), 3),
            "seller_confidence": _round(_f(confidence), 3),
            "capitulation_score": _round(_f(capitulation), 3),
            "opportunity_score": _round(_f(opportunity), 3),
        },
        "rates": {
            "reprice_rate": _round(_f(reprice_rate), 4),
            "churn_rate": _round(_f(churn_rate), 4),
            "listing_survival": _round(_f(listing_survival), 4),
        },
        "days_until_event": _round(_f(days_until)),
        "history_hours": _f(hist_hours),
        "marketplace_metrics": mp_metrics or [],
        "section_metrics": sec_metrics or [],
        "seller_behavior": sell_behavior or {},
        "price_history_24h": (ph_24h or {}).get("buckets", []),
        "window_histories": window_hist or {},
    }
