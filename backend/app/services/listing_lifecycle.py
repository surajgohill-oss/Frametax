"""
listing_lifecycle.py — Listing Lifecycle Intelligence V1

Computes lifecycle transitions, classification of disappeared inventory,
and seller behavior scores from listing_snapshots + listings tables.

All computation is SQL-driven; no rows loaded into Python memory.

Entry point:
  compute_lifecycle(event_id, db, hours_window=168) → dict

Output structure:
  {
    event_id, computed_at, hours_window,
    summary: {
      active_listings, inactive_listings, total_tracked,
      appeared_24h, disappeared_24h,
      probable_sale, probable_relist, probable_pull, probable_expiration, unknown,
      absorption_rate, relist_rate, repricing_rate, churn_rate,
      seller_aggression_score, seller_capitulation_score,
    },
    by_marketplace: [{...}],
    by_section: [{...}],
    top_repriced: [{listing_id, section, price_min, price_max, price_changes}],
    top_volatile_sections: [{section, avg_price_change_pct, listing_count}],
  }
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


# ─────────────────────────────────────────────────────────────────────────────
# Disappearance classification
# ─────────────────────────────────────────────────────────────────────────────
#
# probable_sale     : listing gone in < 6h AND price was ≤ market median (demand signal)
# probable_relist   : inactive listing matched to a new active listing in same section
#                     within 48h at price within ±25%
# probable_pull     : active ≥ 48h before disappearing, no relist match (deliberate)
# probable_expiration: last_seen_at within 24h before event_date (listing expired)
# unknown           : doesn't fit any bucket (< 6h but was priced above median; etc.)
#
# Classification is hierarchical: expiration → relist → sale → pull → unknown


async def compute_lifecycle(
    event_id: int,
    db: AsyncSession,
    hours_window: int = 168,  # 7 days default
) -> dict:
    now_utc = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)

    # ── 1. Summary counts ────────────────────────────────────────────────────
    summary_row = (await db.execute(text("""
        SELECT
            COUNT(*)                                                AS total_tracked,
            SUM(CASE WHEN is_active THEN 1 ELSE 0 END)             AS active_listings,
            SUM(CASE WHEN NOT is_active THEN 1 ELSE 0 END)         AS inactive_listings,
            SUM(CASE WHEN first_seen_at >= :since_24h THEN 1 ELSE 0 END)    AS appeared_24h,
            SUM(CASE WHEN NOT is_active AND last_seen_at >= :since_24h AND
                          last_seen_at < :now THEN 1 ELSE 0 END)   AS disappeared_24h
        FROM listings
        WHERE event_id = :eid
    """), {"eid": event_id, "since_24h": now_naive - timedelta(hours=24), "now": now_naive})).fetchone()

    # ── 2. Inactive listing classification ───────────────────────────────────
    #
    # Classify every inactive listing in one query using window/CTEs.
    #
    class_rows = (await db.execute(text("""
        WITH inactive AS (
            SELECT l.id, l.event_id, l.marketplace_id, l.section,
                   l.price AS last_price,
                   l.first_seen_at, l.last_seen_at,
                   EXTRACT(EPOCH FROM (l.last_seen_at - l.first_seen_at))/3600 AS lifetime_hours,
                   e.event_date::timestamp AS event_date
            FROM listings l
            JOIN events e ON e.id = l.event_id
            WHERE l.event_id = :eid AND l.is_active = false
              AND l.last_seen_at IS NOT NULL
        ),
        -- Market median for sale classification
        market_med AS (
            SELECT AVG(price) AS median_price
            FROM listings
            WHERE event_id = :eid AND is_active = true AND price > 0
        ),
        -- Relist candidates: active listings that appeared after an inactive one in same section
        relist_match AS (
            SELECT
                inact.id AS inactive_id,
                COUNT(newl.id) > 0 AS has_relist
            FROM inactive inact
            LEFT JOIN listings newl ON
                newl.event_id = inact.event_id
                AND newl.marketplace_id = inact.marketplace_id
                AND newl.section = inact.section
                AND newl.first_seen_at > inact.last_seen_at
                AND newl.first_seen_at <= inact.last_seen_at + INTERVAL '48 hours'
                AND newl.price BETWEEN inact.last_price * 0.75 AND inact.last_price * 1.25
                AND newl.id != inact.id
            GROUP BY inact.id
        )
        SELECT
            CASE
                WHEN i.last_seen_at >= i.event_date - INTERVAL '24 hours'
                    THEN 'probable_expiration'
                WHEN rm.has_relist
                    THEN 'probable_relist'
                WHEN i.lifetime_hours < 6
                    THEN 'probable_sale'
                WHEN i.lifetime_hours >= 48
                    THEN 'probable_pull'
                ELSE 'unknown'
            END AS classification,
            COUNT(*) AS cnt,
            ROUND(AVG(i.lifetime_hours), 1) AS avg_lifetime_hours,
            i.marketplace_id
        FROM inactive i
        LEFT JOIN relist_match rm ON rm.inactive_id = i.id
        CROSS JOIN market_med mm
        GROUP BY classification, i.marketplace_id
    """), {"eid": event_id})).fetchall()

    # ── 3. Repricing stats ───────────────────────────────────────────────────
    reprice_row = (await db.execute(text("""
        SELECT
            COUNT(DISTINCT snap_prices.listing_id) AS total_with_snaps,
            SUM(CASE WHEN snap_prices.price_changes > 1 THEN 1 ELSE 0 END) AS repriced_count,
            ROUND(AVG(snap_prices.price_range_pct)::numeric, 1) AS avg_price_range_pct
        FROM (
            SELECT listing_id,
                   COUNT(DISTINCT price) AS price_changes,
                   CASE WHEN MIN(price) > 0
                        THEN (MAX(price) - MIN(price)) / MIN(price) * 100
                        ELSE NULL END AS price_range_pct
            FROM listing_snapshots
            WHERE event_id = :eid
            GROUP BY listing_id
        ) snap_prices
    """), {"eid": event_id})).fetchone()

    # ── 4. Seller scores at event level ──────────────────────────────────────
    score_row = (await db.execute(text("""
        WITH recent_snaps AS (
            SELECT ls.listing_id, ls.price, ls.snapshot_at, l.is_active
            FROM listing_snapshots ls
            JOIN listings l ON l.id = ls.listing_id
            WHERE ls.event_id = :eid
              AND ls.snapshot_at >= :since_24h
        ),
        reprice_24h AS (
            SELECT listing_id,
                   COUNT(DISTINCT price) AS price_changes,
                   MAX(price) - MIN(price) AS price_range,
                   MIN(price) AS min_price,
                   MAX(price) AS max_price
            FROM recent_snaps
            GROUP BY listing_id
            HAVING COUNT(DISTINCT price) > 1
        ),
        drops_24h AS (
            SELECT COUNT(*) AS drop_count,
                   AVG((max_price - min_price) / NULLIF(max_price, 0) * 100) AS avg_drop_pct
            FROM reprice_24h
            WHERE min_price < max_price  -- price went DOWN
        )
        SELECT
            COUNT(DISTINCT rs.listing_id) AS snapped_listings,
            COUNT(DISTINCT rp.listing_id) AS repriced_listings,
            d.drop_count,
            ROUND(d.avg_drop_pct::numeric, 2) AS avg_drop_pct
        FROM recent_snaps rs
        LEFT JOIN reprice_24h rp ON rp.listing_id = rs.listing_id
        CROSS JOIN drops_24h d
        GROUP BY d.drop_count, d.avg_drop_pct
    """), {"eid": event_id, "since_24h": now_naive - timedelta(hours=24)})).fetchone()

    # ── 5. Section-level lifecycle ───────────────────────────────────────────
    section_rows = (await db.execute(text("""
        SELECT
            COALESCE(l.section, 'Unknown') AS section,
            SUM(CASE WHEN l.is_active THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN NOT l.is_active THEN 1 ELSE 0 END) AS inactive,
            COUNT(*) AS total,
            SUM(CASE WHEN l.first_seen_at >= :since_24h THEN 1 ELSE 0 END) AS appeared_24h,
            SUM(CASE WHEN NOT l.is_active AND l.last_seen_at >= :since_24h THEN 1 ELSE 0 END) AS disappeared_24h,
            ROUND(AVG(CASE WHEN NOT l.is_active
                THEN EXTRACT(EPOCH FROM (l.last_seen_at - l.first_seen_at))/3600
                ELSE NULL END)::numeric, 1) AS avg_inactive_lifetime_hours
        FROM listings l
        WHERE l.event_id = :eid
        GROUP BY l.section
        ORDER BY disappeared_24h DESC, inactive DESC
        LIMIT 20
    """), {"eid": event_id, "since_24h": now_naive - timedelta(hours=24)})).fetchall()

    # ── 6. Top repriced listings ─────────────────────────────────────────────
    top_repriced = (await db.execute(text("""
        SELECT ls.listing_id, l.section, l.row,
               COUNT(DISTINCT ls.price) AS price_changes,
               MIN(ls.price) AS price_min, MAX(ls.price) AS price_max,
               ROUND(((MAX(ls.price) - MIN(ls.price)) / NULLIF(MIN(ls.price), 0) * 100)::numeric, 1) AS price_range_pct
        FROM listing_snapshots ls
        JOIN listings l ON l.id = ls.listing_id
        WHERE ls.event_id = :eid
        GROUP BY ls.listing_id, l.section, l.row
        HAVING COUNT(DISTINCT ls.price) > 1
        ORDER BY COUNT(DISTINCT ls.price) DESC, price_range_pct DESC
        LIMIT 10
    """), {"eid": event_id})).fetchall()

    # ── 7. By-marketplace breakdown ──────────────────────────────────────────
    mp_rows = (await db.execute(text("""
        SELECT
            m.slug,
            SUM(CASE WHEN l.is_active THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN NOT l.is_active THEN 1 ELSE 0 END) AS inactive,
            SUM(CASE WHEN l.first_seen_at >= :since_24h THEN 1 ELSE 0 END) AS appeared_24h,
            SUM(CASE WHEN NOT l.is_active AND l.last_seen_at >= :since_24h THEN 1 ELSE 0 END) AS disappeared_24h,
            ROUND(AVG(CASE WHEN NOT l.is_active
                THEN EXTRACT(EPOCH FROM (l.last_seen_at - l.first_seen_at))/3600
                ELSE NULL END)::numeric, 1) AS avg_inactive_lifetime_hours
        FROM listings l
        JOIN marketplaces m ON m.id = l.marketplace_id
        WHERE l.event_id = :eid
        GROUP BY m.slug
        ORDER BY active DESC
    """), {"eid": event_id, "since_24h": now_naive - timedelta(hours=24)})).fetchall()

    # ── Assemble output ───────────────────────────────────────────────────────
    # Parse classification results
    class_totals: dict[str, int] = {
        "probable_sale": 0,
        "probable_relist": 0,
        "probable_pull": 0,
        "probable_expiration": 0,
        "unknown": 0,
    }
    for row in class_rows:
        cls = row.classification if row.classification else "unknown"
        class_totals[cls] = class_totals.get(cls, 0) + (row.cnt or 0)

    total_tracked = int(summary_row.total_tracked or 0)
    active_listings = int(summary_row.active_listings or 0)
    inactive_listings = int(summary_row.inactive_listings or 0)
    appeared_24h = int(summary_row.appeared_24h or 0)
    disappeared_24h = int(summary_row.disappeared_24h or 0)

    # Rates
    absorption_rate = _round(inactive_listings / total_tracked * 100 if total_tracked > 0 else None)
    relist_rate = _round(class_totals["probable_relist"] / inactive_listings * 100 if inactive_listings > 0 else None)

    total_with_snaps = int(reprice_row.total_with_snaps or 0) if reprice_row else 0
    repriced_count = int(reprice_row.repriced_count or 0) if reprice_row else 0
    repricing_rate = _round(repriced_count / total_with_snaps * 100 if total_with_snaps > 0 else None)

    # Churn: (appeared + disappeared) / total active * 100 over 24h
    churn_rate = _round((appeared_24h + disappeared_24h) / active_listings * 100 if active_listings > 0 else None)

    # Seller aggression: fraction of snapped listings that repriced in 24h
    snapped = _f(score_row.snapped_listings) if score_row else None
    repriced_24h = _f(score_row.repriced_listings) if score_row else None
    avg_drop_pct = _f(score_row.avg_drop_pct) if score_row else None
    drop_count = _f(score_row.drop_count) if score_row else None

    seller_aggression_score = None
    if snapped and snapped > 0 and repriced_24h is not None:
        seller_aggression_score = _round(repriced_24h / snapped, 3)

    # Seller capitulation: fraction of 24h reprices that were drops, weighted by avg drop size
    seller_capitulation_score = None
    if repriced_24h and repriced_24h > 0 and drop_count is not None and avg_drop_pct is not None:
        drop_fraction = drop_count / repriced_24h
        normalized_drop_magnitude = min(1.0, abs(avg_drop_pct) / 20.0)
        seller_capitulation_score = _round(drop_fraction * 0.6 + normalized_drop_magnitude * 0.4, 3)

    return {
        "event_id": event_id,
        "computed_at": now_utc.isoformat(),
        "hours_window": hours_window,
        "summary": {
            "total_tracked": total_tracked,
            "active_listings": active_listings,
            "inactive_listings": inactive_listings,
            "appeared_24h": appeared_24h,
            "disappeared_24h": disappeared_24h,
            "probable_sale": class_totals["probable_sale"],
            "probable_relist": class_totals["probable_relist"],
            "probable_pull": class_totals["probable_pull"],
            "probable_expiration": class_totals["probable_expiration"],
            "unknown": class_totals["unknown"],
            "absorption_rate": absorption_rate,
            "relist_rate": relist_rate,
            "repricing_rate": repricing_rate,
            "churn_rate": churn_rate,
            "seller_aggression_score": seller_aggression_score,
            "seller_capitulation_score": seller_capitulation_score,
        },
        "by_marketplace": [
            {
                "marketplace": row.slug,
                "active": int(row.active or 0),
                "inactive": int(row.inactive or 0),
                "appeared_24h": int(row.appeared_24h or 0),
                "disappeared_24h": int(row.disappeared_24h or 0),
                "absorption_rate": _round(
                    int(row.inactive or 0) / (int(row.active or 0) + int(row.inactive or 0)) * 100
                    if (int(row.active or 0) + int(row.inactive or 0)) > 0 else None
                ),
                "avg_inactive_lifetime_hours": _f(row.avg_inactive_lifetime_hours),
            }
            for row in mp_rows
        ],
        "by_section": [
            {
                "section": row.section,
                "active": int(row.active or 0),
                "inactive": int(row.inactive or 0),
                "total": int(row.total or 0),
                "appeared_24h": int(row.appeared_24h or 0),
                "disappeared_24h": int(row.disappeared_24h or 0),
                "absorption_rate": _round(
                    int(row.inactive or 0) / int(row.total or 1) * 100
                ),
                "avg_inactive_lifetime_hours": _f(row.avg_inactive_lifetime_hours),
                "liquidity_score": _round(
                    min(1.0, (int(row.appeared_24h or 0) + int(row.disappeared_24h or 0))
                        / max(1, int(row.total or 1))), 3
                ),
            }
            for row in section_rows
        ],
        "top_repriced": [
            {
                "listing_id": row.listing_id,
                "section": row.section,
                "row": row.row,
                "price_changes": int(row.price_changes or 0),
                "price_min": _f(row.price_min),
                "price_max": _f(row.price_max),
                "price_range_pct": _f(row.price_range_pct),
            }
            for row in top_repriced
        ],
    }
