"""
listing_lifecycle.py — Listing Lifecycle Intelligence V1

Lifecycle states (per-listing):
  ACTIVE                    is_active=true, no price changes
  REPRICED                  is_active=true OR was active, multiple distinct prices in snapshots
  DISAPPEARED_ASSUMED_SOLD  is_active=false, no relist match found
  RELISTED                  is_active=false, matched to a new listing in same section/row at similar price
  UNKNOWN                   insufficient data

Relist Detection (Task D):
  Matches a disappeared listing to a new listing by:
    1. Same marketplace
    2. Same section (exact or fuzzy)
    3. Same or adjacent row (±2 numerically, or exact string)
    4. Price similarity (within configurable threshold)
  Confidence:
    HIGH   — exact section + row, price within 10%
    MEDIUM — exact section + row, price within 30%
    LOW    — same section, different row, price within 30%
  Time is NOT required for matching. Delay hours are tracked as context.

User rule: "A disappeared listing is assumed sold.
            If it later reappears: classify as RELISTED."

Entry points:
  compute_lifecycle(event_id, db, hours_window=168) → full lifecycle dict
  get_relist_candidates(event_id, marketplace_id, db) → list of relist matches
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _f(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _round(v, n=2) -> Optional[float]:
    f = _f(v)
    return round(f, n) if f is not None else None


def _rows_similar(section_a: Optional[str], row_a: Optional[str],
                  section_b: Optional[str], row_b: Optional[str]) -> tuple[bool, bool]:
    """
    Returns (section_match, row_match).
    Row match = exact string OR adjacent integer (±2).
    """
    sec_match = (section_a or "").strip().upper() == (section_b or "").strip().upper()

    row_a_clean = (row_a or "").strip()
    row_b_clean = (row_b or "").strip()
    if row_a_clean == row_b_clean:
        row_match = True
    else:
        try:
            row_match = abs(int(row_a_clean) - int(row_b_clean)) <= 2
        except (ValueError, TypeError):
            row_match = False

    return sec_match, row_match


def _relist_confidence(
    sec_match: bool,
    row_match: bool,
    price_diff_pct: float,
) -> Optional[str]:
    """
    HIGH   — exact section + row, price within 10%
    MEDIUM — exact section + row OR (same section, row ±2), price within 30%
    LOW    — same section, price within 30%
    None   — doesn't qualify as relist
    """
    if price_diff_pct > 30:
        return None
    if sec_match and row_match and price_diff_pct <= 10:
        return "HIGH"
    if sec_match and row_match and price_diff_pct <= 30:
        return "MEDIUM"
    if sec_match and price_diff_pct <= 30:
        return "LOW"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main lifecycle computation
# ─────────────────────────────────────────────────────────────────────────────

async def compute_lifecycle(
    event_id: int,
    db: AsyncSession,
    hours_window: int = 168,
) -> dict:
    """
    Full lifecycle analysis for one event.
    Returns summary + by_marketplace + by_section + top_repriced + relist_matches.
    """
    now_utc   = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)
    since_24h = now_naive - timedelta(hours=24)

    # ── 1. Per-listing lifecycle state with relist matching ─────────────────
    #
    # Cross-marketplace matching is included: a listing can be relisted on a
    # different marketplace (same section+row+price, different marketplace_id).
    #
    lifecycle_rows = (await db.execute(text("""
        WITH inactive AS (
            SELECT l.id, l.event_id, l.marketplace_id, m_orig.slug AS orig_mp_slug,
                   l.section, l.row,
                   l.price AS last_price,
                   l.first_seen_at, l.last_seen_at,
                   EXTRACT(EPOCH FROM (l.last_seen_at - l.first_seen_at)) / 3600 AS lifetime_hours,
                   e.event_date::timestamp AS event_date
            FROM listings l
            JOIN events e ON e.id = l.event_id
            JOIN marketplaces m_orig ON m_orig.id = l.marketplace_id
            WHERE l.event_id = :eid AND l.is_active = false
              AND l.last_seen_at IS NOT NULL
        ),
        relist_candidates AS (
            SELECT
                inact.id                                                  AS inactive_id,
                newl.id                                                   AS new_listing_id,
                newl.marketplace_id                                       AS relist_marketplace_id,
                m_new.slug                                                AS relist_mp_slug,
                (inact.marketplace_id != newl.marketplace_id)             AS cross_marketplace,
                newl.section                                              AS new_section,
                newl.row                                                  AS new_row,
                newl.price                                                AS new_price,
                newl.is_active                                            AS new_is_active,
                newl.first_seen_at                                        AS reappeared_at,
                EXTRACT(EPOCH FROM (newl.first_seen_at - inact.last_seen_at)) / 3600
                                                                          AS relist_delay_hours,
                CASE WHEN inact.last_price > 0
                     THEN ABS(newl.price - inact.last_price) / inact.last_price * 100
                     ELSE NULL END                                        AS price_diff_pct,
                CASE
                    WHEN inact.section = newl.section
                         AND (inact.row = newl.row OR
                              (inact.row ~ '^[0-9]+$' AND newl.row ~ '^[0-9]+$'
                               AND ABS(inact.row::int - newl.row::int) <= 2))
                         AND ABS(newl.price - inact.last_price) / NULLIF(inact.last_price, 0) * 100 <= 10
                    THEN 'HIGH'
                    WHEN inact.section = newl.section
                         AND (inact.row = newl.row OR
                              (inact.row ~ '^[0-9]+$' AND newl.row ~ '^[0-9]+$'
                               AND ABS(inact.row::int - newl.row::int) <= 2))
                         AND ABS(newl.price - inact.last_price) / NULLIF(inact.last_price, 0) * 100 <= 30
                    THEN 'MEDIUM'
                    WHEN inact.section = newl.section
                         AND ABS(newl.price - inact.last_price) / NULLIF(inact.last_price, 0) * 100 <= 30
                    THEN 'LOW'
                    ELSE NULL
                END AS confidence
            FROM inactive inact
            -- Allow cross-marketplace: join on event+section only (not marketplace)
            JOIN listings newl ON
                newl.event_id    = inact.event_id
                AND newl.section = inact.section
                AND newl.first_seen_at > inact.last_seen_at
                AND newl.id     != inact.id
                AND CASE WHEN inact.last_price > 0
                         THEN ABS(newl.price - inact.last_price) / inact.last_price * 100 <= 30
                         ELSE false END
            JOIN marketplaces m_new ON m_new.id = newl.marketplace_id
        )
        SELECT
            i.id, i.marketplace_id, i.orig_mp_slug, i.section, i.row,
            i.last_price AS original_price, i.first_seen_at, i.last_seen_at,
            i.lifetime_hours, i.event_date,
            rc.new_listing_id, rc.relist_marketplace_id, rc.relist_mp_slug,
            rc.cross_marketplace, rc.new_price AS relist_price,
            rc.new_is_active AS relist_still_active,
            rc.reappeared_at, rc.relist_delay_hours,
            rc.price_diff_pct,
            rc.confidence,
            CASE WHEN i.last_price > 0
                 THEN (rc.new_price - i.last_price) / i.last_price * 100
                 ELSE NULL END AS price_delta_pct
        FROM inactive i
        LEFT JOIN (
            SELECT DISTINCT ON (inactive_id)
                inactive_id, new_listing_id, relist_marketplace_id, relist_mp_slug,
                cross_marketplace, new_price, new_is_active, reappeared_at,
                relist_delay_hours, price_diff_pct, confidence
            FROM relist_candidates
            WHERE confidence IS NOT NULL
            ORDER BY inactive_id,
                     CASE confidence WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
                     relist_delay_hours ASC
        ) rc ON rc.inactive_id = i.id
        ORDER BY i.last_seen_at DESC
    """), {"eid": event_id})).fetchall()

    # ── 2. Repricing: listings with multiple distinct prices ─────────────────
    reprice_rows = (await db.execute(text("""
        SELECT
            ls.listing_id, l.section, l.row, l.is_active,
            l.first_seen_at, l.last_seen_at, l.price AS current_price,
            COUNT(DISTINCT ls.price) AS price_changes,
            MIN(ls.price) AS price_min, MAX(ls.price) AS price_max,
            ROUND(((MAX(ls.price) - MIN(ls.price)) / NULLIF(MIN(ls.price), 0) * 100)::numeric, 1) AS price_range_pct
        FROM listing_snapshots ls
        JOIN listings l ON l.id = ls.listing_id
        WHERE ls.event_id = :eid
        GROUP BY ls.listing_id, l.section, l.row, l.is_active, l.first_seen_at, l.last_seen_at, l.price
        HAVING COUNT(DISTINCT ls.price) > 1
        ORDER BY COUNT(DISTINCT ls.price) DESC
        LIMIT 20
    """), {"eid": event_id})).fetchall()

    # ── 3. Summary counts ────────────────────────────────────────────────────
    summary_row = (await db.execute(text("""
        SELECT
            COUNT(*) AS total_tracked,
            SUM(CASE WHEN is_active THEN 1 ELSE 0 END) AS active_listings,
            SUM(CASE WHEN NOT is_active THEN 1 ELSE 0 END) AS inactive_listings,
            SUM(CASE WHEN first_seen_at >= :since_24h THEN 1 ELSE 0 END) AS appeared_24h,
            SUM(CASE WHEN NOT is_active AND last_seen_at >= :since_24h THEN 1 ELSE 0 END) AS disappeared_24h
        FROM listings WHERE event_id = :eid
    """), {"eid": event_id, "since_24h": since_24h})).fetchone()

    # ── 4. Seller scores from recent snapshots ───────────────────────────────
    score_row = (await db.execute(text("""
        WITH snapped AS (
            SELECT DISTINCT listing_id FROM listing_snapshots
            WHERE event_id = :eid AND snapshot_at >= :since_24h
        ),
        reprice_24h AS (
            SELECT listing_id,
                   MAX(price) AS max_p, MIN(price) AS min_p
            FROM listing_snapshots
            WHERE event_id = :eid AND snapshot_at >= :since_24h
            GROUP BY listing_id
            HAVING COUNT(DISTINCT price) > 1
        )
        SELECT
            COUNT(DISTINCT snapped.listing_id)                              AS snapped_listings,
            COUNT(DISTINCT rp.listing_id)                                   AS repriced_listings,
            COUNT(DISTINCT CASE WHEN rp.min_p < rp.max_p THEN rp.listing_id ELSE NULL END) AS drops,
            ROUND(AVG(CASE WHEN rp.max_p > 0
                THEN (rp.max_p - rp.min_p) / rp.max_p * 100
                ELSE NULL END)::numeric, 2)                                 AS avg_drop_pct
        FROM snapped
        LEFT JOIN reprice_24h rp ON rp.listing_id = snapped.listing_id
    """), {"eid": event_id, "since_24h": since_24h})).fetchone()

    # ── 5. By-section lifecycle ──────────────────────────────────────────────
    section_rows = (await db.execute(text("""
        SELECT
            COALESCE(l.section, 'Unknown') AS section,
            SUM(CASE WHEN l.is_active THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN NOT l.is_active THEN 1 ELSE 0 END) AS inactive,
            COUNT(*) AS total,
            SUM(CASE WHEN l.first_seen_at >= :since_24h THEN 1 ELSE 0 END) AS appeared_24h,
            SUM(CASE WHEN NOT l.is_active AND l.last_seen_at >= :since_24h THEN 1 ELSE 0 END) AS disappeared_24h,
            ROUND(AVG(CASE WHEN NOT l.is_active
                THEN EXTRACT(EPOCH FROM (l.last_seen_at - l.first_seen_at)) / 3600
                ELSE NULL END)::numeric, 1) AS avg_inactive_lifetime_hours
        FROM listings l
        WHERE l.event_id = :eid
        GROUP BY l.section
        ORDER BY disappeared_24h DESC, inactive DESC
        LIMIT 25
    """), {"eid": event_id, "since_24h": since_24h})).fetchall()

    # ── 6. By-marketplace lifecycle ──────────────────────────────────────────
    mp_rows = (await db.execute(text("""
        SELECT
            m.slug,
            SUM(CASE WHEN l.is_active THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN NOT l.is_active THEN 1 ELSE 0 END) AS inactive,
            SUM(CASE WHEN l.first_seen_at >= :since_24h THEN 1 ELSE 0 END) AS appeared_24h,
            SUM(CASE WHEN NOT l.is_active AND l.last_seen_at >= :since_24h THEN 1 ELSE 0 END) AS disappeared_24h,
            ROUND(AVG(CASE WHEN NOT l.is_active
                THEN EXTRACT(EPOCH FROM (l.last_seen_at - l.first_seen_at)) / 3600
                ELSE NULL END)::numeric, 1) AS avg_inactive_lifetime_hours
        FROM listings l
        JOIN marketplaces m ON m.id = l.marketplace_id
        WHERE l.event_id = :eid
        GROUP BY m.slug ORDER BY active DESC
    """), {"eid": event_id, "since_24h": since_24h})).fetchall()

    # ── 6b. Post-show state counts (listings seen after event start / post-show window) ─
    postshow_row = None
    try:
        async with db.begin_nested():
            postshow_row = (await db.execute(text("""
                SELECT
                    COUNT(*) FILTER (
                        WHERE l.last_seen_at IS NOT NULL
                          AND e.event_date IS NOT NULL
                          AND l.last_seen_at >= e.event_date
                    ) AS still_active_at_event_start,
                    COUNT(*) FILTER (
                        WHERE l.last_seen_at IS NOT NULL
                          AND e.event_date IS NOT NULL
                          AND l.last_seen_at >= (e.event_date + INTERVAL '4 hours')
                    ) AS still_active_after_postshow
                FROM listings l
                JOIN events e ON e.id = l.event_id
                WHERE l.event_id = :eid
            """), {"eid": event_id})).fetchone()
    except Exception:
        pass

    # ── Assemble lifecycle state counts from per-listing rows ────────────────
    assumed_sales         = 0
    relisted_count        = 0
    sold_after_relist     = 0
    cross_mp_relist_count = 0
    relist_matches        = []

    # Implied sale price accumulators (last-seen price of disappeared listings)
    implied_sale_prices: list[float] = []      # assumed_sold original prices
    sold_after_relist_prices: list[float] = [] # sold_after_relist relist prices

    for row in lifecycle_rows:
        if row.new_listing_id is not None:
            relisted_count += 1
            price_delta = _f(row.relist_price) - _f(row.original_price) if row.relist_price and row.original_price else None
            price_delta_pct = _f(row.price_delta_pct)
            is_cross = bool(row.cross_marketplace) if row.cross_marketplace is not None else False
            if is_cross:
                cross_mp_relist_count += 1
            # relist_still_active=False → the relisted listing also disappeared → SOLD_AFTER_RELIST
            relist_is_sold = (row.relist_still_active is False)
            if relist_is_sold:
                sold_after_relist += 1
                # Use relist_price (price when sold after relist) if available
                if row.relist_price and _f(row.relist_price) and _f(row.relist_price) > 0:
                    sold_after_relist_prices.append(_f(row.relist_price))
                elif row.original_price and _f(row.original_price) and _f(row.original_price) > 0:
                    sold_after_relist_prices.append(_f(row.original_price))
            relist_matches.append({
                "original_listing_id":  row.id,
                "new_listing_id":       row.new_listing_id,
                "marketplace_id":       row.marketplace_id,
                "original_marketplace": row.orig_mp_slug,
                "relist_marketplace":   row.relist_mp_slug,
                "cross_marketplace":    is_cross,
                "lifecycle_state":      "SOLD_AFTER_RELIST" if relist_is_sold else "RELISTED",
                "section":              row.section,
                "row":                  row.row,
                "original_price":       _f(row.original_price),
                "relist_price":         _f(row.relist_price),
                "price_delta":          _round(price_delta),
                "price_delta_pct":      _round(price_delta_pct),
                "first_seen_at":        row.first_seen_at.isoformat() if row.first_seen_at else None,
                "last_seen_at":         row.last_seen_at.isoformat() if row.last_seen_at else None,
                "reappeared_at":        row.reappeared_at.isoformat() if row.reappeared_at else None,
                "relist_delay_hours":   _round(_f(row.relist_delay_hours), 1),
                "time_away_hours":      _round(_f(row.relist_delay_hours), 1),
                "confidence":           row.confidence,
            })
        else:
            assumed_sales += 1
            # Last-seen price of listings assumed sold (no relist detected)
            p = _f(row.original_price)
            if p and p > 0:
                implied_sale_prices.append(p)

    # ── Implied sale price computation ──────────────────────────────────────
    # Average last-seen price for DISAPPEARED_ASSUMED_SOLD listings
    avg_assumed_sale_price = (
        _round(sum(implied_sale_prices) / len(implied_sale_prices), 2)
        if implied_sale_prices else None
    )
    # Blended avg across assumed_sold + sold_after_relist
    all_implied_prices = implied_sale_prices + sold_after_relist_prices
    avg_implied_sale_price = (
        _round(sum(all_implied_prices) / len(all_implied_prices), 2)
        if all_implied_prices else None
    )

    direct_assumed_sales = assumed_sales  # inactive with no relist match at all
    still_at_start  = int(postshow_row.still_active_at_event_start or 0) if postshow_row else 0
    still_postshow  = int(postshow_row.still_active_after_postshow or 0) if postshow_row else 0

    total_tracked   = int(summary_row.total_tracked or 0)
    active_listings = int(summary_row.active_listings or 0)
    inactive_listings = int(summary_row.inactive_listings or 0)
    appeared_24h    = int(summary_row.appeared_24h or 0)
    disappeared_24h = int(summary_row.disappeared_24h or 0)

    repriced_count  = len(reprice_rows)

    # Rates
    absorption_rate = _round(inactive_listings / total_tracked * 100 if total_tracked > 0 else None)
    relist_rate     = _round(relisted_count / inactive_listings * 100 if inactive_listings > 0 else None)
    reprice_total   = (await db.execute(text(
        "SELECT COUNT(DISTINCT listing_id) FROM listing_snapshots WHERE event_id=:eid"
    ), {"eid": event_id})).scalar()
    repricing_rate  = _round(repriced_count / int(reprice_total or 1) * 100)
    churn_rate      = _round((appeared_24h + disappeared_24h) / active_listings * 100
                             if active_listings > 0 else None)

    # Seller scores
    snapped     = _f(score_row.snapped_listings) if score_row else None
    repriced_24 = _f(score_row.repriced_listings) if score_row else None
    drops       = _f(score_row.drops) if score_row else None
    avg_drop    = _f(score_row.avg_drop_pct) if score_row else None

    seller_aggression_score = None
    if snapped and snapped > 0 and repriced_24 is not None:
        seller_aggression_score = _round(repriced_24 / snapped, 3)

    seller_capitulation_score = None
    if repriced_24 and repriced_24 > 0 and drops is not None and avg_drop is not None:
        drop_fraction = drops / repriced_24
        magnitude     = min(1.0, abs(avg_drop) / 20.0)
        seller_capitulation_score = _round(drop_fraction * 0.6 + magnitude * 0.4, 3)

    # Relist delay distribution
    delays = [m["relist_delay_hours"] for m in relist_matches if m["relist_delay_hours"] is not None]
    relist_delay_p50  = _round(sorted(delays)[len(delays) // 2]) if delays else None
    relist_delay_p90  = _round(sorted(delays)[int(len(delays) * 0.9)]) if len(delays) >= 3 else None

    return {
        "event_id":     event_id,
        "computed_at":  now_utc.isoformat(),
        "hours_window": hours_window,
        "summary": {
            "total_tracked":            total_tracked,
            "active_listings":          active_listings,
            "inactive_listings":        inactive_listings,
            "appeared_24h":             appeared_24h,
            "disappeared_24h":          disappeared_24h,
            # Lifecycle state counts
            "assumed_sales":                    assumed_sales,            # DISAPPEARED_ASSUMED_SOLD
            "direct_assumed_sales":             direct_assumed_sales,     # inactive, no relist match
            "relisted_count":                   relisted_count,           # RELISTED (active relist)
            "sold_after_relist_count":          sold_after_relist,        # SOLD_AFTER_RELIST
            "cross_marketplace_relist_count":   cross_mp_relist_count,    # cross-marketplace relists
            "still_active_at_event_start":      still_at_start,           # STILL_ACTIVE_AT_EVENT_START
            "still_active_after_postshow":      still_postshow,           # STILL_ACTIVE_AFTER_POSTSHOW_WINDOW
            "repriced_count":                   repriced_count,           # REPRICED
            # Legacy names kept for backward compat
            "probable_sale":                    assumed_sales,
            "probable_relist":                  relisted_count,
            "probable_pull":                    0,
            "probable_expiration":              0,
            "unknown":                          0,
            # Implied sale price (avg last-seen price of disappeared listings)
            "avg_assumed_sale_price":   avg_assumed_sale_price,   # assumed-sold only
            "avg_implied_sale_price":   avg_implied_sale_price,   # assumed-sold + sold-after-relist
            "implied_sale_count":       len(all_implied_prices),  # denominator
            # Rates
            "absorption_rate":          absorption_rate,
            "relist_rate":              relist_rate,
            "repricing_rate":           repricing_rate,
            "churn_rate":               churn_rate,
            # Seller scores
            "seller_aggression_score":  seller_aggression_score,
            "seller_capitulation_score": seller_capitulation_score,
            # Relist timing
            "relist_delay_p50_hours":   relist_delay_p50,
            "relist_delay_p90_hours":   relist_delay_p90,
        },
        "by_marketplace": [
            {
                "marketplace":          row.slug,
                "active":               int(row.active or 0),
                "inactive":             int(row.inactive or 0),
                "appeared_24h":         int(row.appeared_24h or 0),
                "disappeared_24h":      int(row.disappeared_24h or 0),
                "absorption_rate":      _round(
                    int(row.inactive or 0) / (int(row.active or 0) + int(row.inactive or 0)) * 100
                    if (int(row.active or 0) + int(row.inactive or 0)) > 0 else None
                ),
                "avg_inactive_lifetime_hours": _f(row.avg_inactive_lifetime_hours),
            }
            for row in mp_rows
        ],
        "by_section": [
            {
                "section":              row.section,
                "active":               int(row.active or 0),
                "inactive":             int(row.inactive or 0),
                "total":                int(row.total or 0),
                "appeared_24h":         int(row.appeared_24h or 0),
                "disappeared_24h":      int(row.disappeared_24h or 0),
                "absorption_rate":      _round(int(row.inactive or 0) / int(row.total or 1) * 100),
                "avg_inactive_lifetime_hours": _f(row.avg_inactive_lifetime_hours),
                "liquidity_score":      _round(
                    min(1.0, (int(row.appeared_24h or 0) + int(row.disappeared_24h or 0))
                        / max(1, int(row.total or 1))), 3
                ),
            }
            for row in section_rows
        ],
        "top_repriced": [
            {
                "listing_id":    row.listing_id,
                "section":       row.section,
                "row":           row.row,
                "is_active":     row.is_active,
                "price_changes": int(row.price_changes or 0),
                "price_min":     _f(row.price_min),
                "price_max":     _f(row.price_max),
                "price_range_pct": _f(row.price_range_pct),
                "first_seen_at": row.first_seen_at.isoformat() if row.first_seen_at else None,
                "last_seen_at":  row.last_seen_at.isoformat() if row.last_seen_at else None,
            }
            for row in reprice_rows
        ],
        "relist_matches": relist_matches[:50],  # cap for response size
        "relist_confidence_distribution": {
            "HIGH":   sum(1 for m in relist_matches if m["confidence"] == "HIGH"),
            "MEDIUM": sum(1 for m in relist_matches if m["confidence"] == "MEDIUM"),
            "LOW":    sum(1 for m in relist_matches if m["confidence"] == "LOW"),
        },
    }
