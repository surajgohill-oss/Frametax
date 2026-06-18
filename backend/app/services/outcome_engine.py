"""
outcome_engine.py — Event Outcome Intelligence Engine (Phase 1-6)

Computes persisted outcome metrics for COMPLETED events from stored snapshots.
All calculations are anchored to event_date (not "last 24h"), enabling
post-hoc analysis of how markets cleared.

Phases implemented:
  1. Clearance    — inventory at event_start, 1h/6h/24h post-show
  2. Relist       — total disappeared, relisted, sold_after_relist rates
  3. Seller Pressure — repricing behavior, pressure/strength scores
  4. Section Absorption — per-section clearance, top/worst absorbed
  5. Artist Profile — aggregated across completed events per artist
  6. Evidence Metrics — buy-signal inputs without recommendation logic

Entry points:
  compute_event_outcome(event_id, db)  → dict + upserts event_outcomes row
  build_artist_profile(artist, db)     → dict + upserts artist_market_profiles row
  get_event_outcome(event_id, db)      → read from cache or compute
  get_artist_profile(artist, db)       → read from cache or compute
  compute_all_pending(db)              → processes all completed events without outcomes
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Section normalization
# ─────────────────────────────────────────────────────────────────────────────

_SECTION_PREFIX_RE = re.compile(
    r'^(?:section|sec|upper\s+bowl|lower\s+bowl)\s+',
    re.IGNORECASE,
)


def normalize_section(raw: Optional[str]) -> Optional[str]:
    """
    Strip marketplace-specific prefixes to produce a canonical section identifier.

    Examples:
      "Section 214"    → "214"
      "SEC 214"        → "214"
      "Upper Bowl 214" → "214"
      "Lower Bowl 107" → "107"
      "214"            → "214"      (already canonical)
      "Floor GA"       → "Floor GA" (no prefix to strip)
    """
    if not raw:
        return raw
    return _SECTION_PREFIX_RE.sub("", raw.strip()).strip() or raw.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Event-type classification
# ─────────────────────────────────────────────────────────────────────────────

def _classify_event_type(title: str, venue_name: str) -> str:
    """
    Classify event into benchmark category from title + venue name.
    Returns one of: 'arena_concert', 'stadium_concert',
                    'amphitheater_concert', 'comedy', 'sports'
    """
    t = (title or "").lower()
    v = (venue_name or "").lower()

    # Sports first — most unambiguous
    sports_kw = ["fifa", "world cup", " vs ", "nfl", "nba", "mlb", "nhl", "mls",
                 "championship", "playoff", "super bowl", "soccer", "football"]
    if any(k in t for k in sports_kw):
        return "sports"

    # Comedy
    if any(k in t for k in ["comedy", "stand-up", "stand up", "comedian"]):
        return "comedy"

    # Amphitheater (outdoor)
    if any(k in v for k in ["amphitheater", "amphitheatre", "hollywood bowl",
                             "greek theatre", "shoreline", "cascades"]):
        return "amphitheater_concert"

    # Stadium (capacity > ~50k venues)
    if any(k in v for k in ["stadium", "levi", "sofi", "mercedes-benz",
                             "at&t stadium", "arrowhead", "metlife"]):
        return "stadium_concert"

    # Default: arena
    return "arena_concert"


def _f(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _r(v, n=4) -> Optional[float]:
    f = _f(v)
    return round(f, n) if f is not None else None


def _signal(value: Optional[float], low: float, high: float) -> str:
    if value is None:
        return "UNKNOWN"
    if value >= high:
        return "HIGH"
    if value >= low:
        return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Clearance Engine
# ─────────────────────────────────────────────────────────────────────────────

async def _compute_clearance(event_id: int, event_date: datetime, db: AsyncSession) -> dict:
    """
    Measure market clearance anchored to event_date.

    Windows:
      event_start:  [event_date-1h, event_date+1h]   — listings present at show time
      1h_post:      [event_date+0.5h, event_date+1.5h]
      6h_post:      [event_date+5h, event_date+7h]
      24h_post:     [event_date+22h, event_date+26h]

    We count DISTINCT listing_ids in each window, using the MAX(quantity) per
    listing to avoid inflating ticket counts across multiple snapshots.
    """
    ed = event_date.replace(tzinfo=None)

    windows = {
        "event_start": (ed - timedelta(hours=1),   ed + timedelta(hours=1)),
        "1h_post":     (ed + timedelta(minutes=30), ed + timedelta(hours=1, minutes=30)),
        "6h_post":     (ed + timedelta(hours=5),    ed + timedelta(hours=7)),
        "24h_post":    (ed + timedelta(hours=22),   ed + timedelta(hours=26)),
    }

    results: dict[str, tuple[int, int]] = {}
    for label, (w_start, w_end) in windows.items():
        row = (await db.execute(text("""
            SELECT
                COUNT(DISTINCT listing_id) AS listings,
                COALESCE(SUM(max_qty), 0)  AS tickets
            FROM (
                SELECT listing_id, MAX(quantity) AS max_qty
                FROM listing_snapshots
                WHERE event_id = :eid
                  AND snapshot_at BETWEEN :w_start AND :w_end
                GROUP BY listing_id
            ) sub
        """), {"eid": event_id, "w_start": w_start, "w_end": w_end})).fetchone()
        results[label] = (int(row.listings or 0), int(row.tickets or 0))

    # Total ever
    total_row = (await db.execute(text("""
        SELECT COUNT(*) AS listings, COALESCE(SUM(quantity), 0) AS tickets
        FROM listings WHERE event_id = :eid
    """), {"eid": event_id})).fetchone()

    total_l = int(total_row.listings or 0)
    total_t = int(total_row.tickets or 0)

    at_start_l, at_start_t = results["event_start"]
    post_1h_l, post_1h_t   = results["1h_post"]
    post_6h_l, post_6h_t   = results["6h_post"]
    post_24h_l, post_24h_t = results["24h_post"]

    # clearance = fraction of event_start inventory that disappeared by comparison window
    event_start_clearance = _r(
        (at_start_l - post_1h_l) / at_start_l if at_start_l > 0 else None
    )
    postshow_clearance = _r(
        (at_start_l - post_6h_l) / at_start_l if at_start_l > 0 else None
    )
    remaining_inventory = _r(
        post_6h_l / at_start_l if at_start_l > 0 else None
    )

    # Data coverage (hours from first to last snapshot)
    cov_row = (await db.execute(text("""
        SELECT
            EXTRACT(EPOCH FROM (MAX(snapshot_at) - MIN(snapshot_at))) / 3600 AS hours
        FROM listing_snapshots WHERE event_id = :eid
    """), {"eid": event_id})).fetchone()
    data_coverage_hours = _r(_f(cov_row.hours) if cov_row else None, 2)

    has_postshow = post_1h_l > 0

    return {
        "total_listings_seen":      total_l,
        "total_tickets_seen":       total_t,
        "listings_at_event_start":  at_start_l,
        "tickets_at_event_start":   at_start_t,
        "listings_1h_post":         post_1h_l,
        "tickets_1h_post":          post_1h_t,
        "listings_6h_post":         post_6h_l,
        "tickets_6h_post":          post_6h_t,
        "listings_24h_post":        post_24h_l,
        "tickets_24h_post":         post_24h_t,
        "event_start_clearance_rate": event_start_clearance,
        "postshow_clearance_rate":    postshow_clearance,
        "remaining_inventory_rate":   remaining_inventory,
        "data_coverage_hours":        data_coverage_hours,
        "has_postshow_data":          has_postshow,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Relist Engine
# ─────────────────────────────────────────────────────────────────────────────

async def _compute_relist(event_id: int, db: AsyncSession) -> dict:
    """
    Measures seller relisting behavior for completed events.

    Uses the same relist detection logic as listing_lifecycle.py:
    - Disappeared listing matched to a new listing in same section/row
      with price within 30% appearing after the original disappeared.
    - RELISTED        = new listing still active
    - SOLD_AFTER_RELIST = new listing also disappeared

    For completed events, markup/discount is computed from the relist price
    vs original price.
    """
    relist_row = (await db.execute(text("""
        WITH inactive AS (
            SELECT l.id, l.section, l.row, l.price AS orig_price, l.last_seen_at
            FROM listings l
            WHERE l.event_id = :eid AND l.is_active = false
        ),
        relist_candidates AS (
            SELECT
                i.id             AS orig_id,
                i.orig_price,
                n.id             AS new_id,
                n.price          AS relist_price,
                n.is_active      AS relist_active,
                n.first_seen_at  AS relist_at,
                EXTRACT(EPOCH FROM (n.first_seen_at - i.last_seen_at)) / 3600
                                 AS delay_hours,
                CASE WHEN i.orig_price > 0
                     THEN (n.price - i.orig_price) / i.orig_price * 100
                     ELSE NULL END AS delta_pct
            FROM inactive i
            JOIN listings n ON
                n.event_id   = :eid
                AND n.section = i.section
                AND n.first_seen_at > i.last_seen_at
                AND n.id     != i.id
                AND CASE WHEN i.orig_price > 0
                         THEN ABS(n.price - i.orig_price) / i.orig_price * 100 <= 30
                         ELSE false END
        ),
        best AS (
            SELECT DISTINCT ON (orig_id)
                orig_id, orig_price, new_id, relist_price, relist_active,
                delay_hours, delta_pct
            FROM relist_candidates
            ORDER BY orig_id, delay_hours ASC
        )
        SELECT
            (SELECT COUNT(*) FROM inactive)                          AS total_disappeared,
            COUNT(*)                                                  AS total_relisted,
            COUNT(*) FILTER (WHERE NOT relist_active)                AS relisted_then_disappeared,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_hours) AS delay_p50,
            AVG(delta_pct) FILTER (WHERE delta_pct > 0)              AS avg_markup_pct,
            AVG(delta_pct) FILTER (WHERE delta_pct < 0)              AS avg_discount_pct,
            COUNT(*) FILTER (WHERE NOT relist_active)                AS sold_after_relist
        FROM best
    """), {"eid": event_id})).fetchone()

    total_dis = int(relist_row.total_disappeared or 0)
    total_re  = int(relist_row.total_relisted or 0)
    re_then_dis = int(relist_row.relisted_then_disappeared or 0)

    relist_pct          = _r(total_re / total_dis if total_dis > 0 else None)
    sold_after_re_pct   = _r(re_then_dis / total_re if total_re > 0 else None)
    relist_success_rate = _r((total_re - re_then_dis) / total_re if total_re > 0 else None)

    return {
        "total_disappeared":        total_dis,
        "total_relisted":           total_re,
        "relist_percentage":        relist_pct,
        "relisted_then_disappeared": re_then_dis,
        "sold_after_relist_pct":    sold_after_re_pct,
        "avg_relist_markup_pct":    _r(_f(relist_row.avg_markup_pct), 2),
        "avg_relist_discount_pct":  _r(_f(relist_row.avg_discount_pct), 2),
        "relist_success_rate":      relist_success_rate,
        "relist_delay_p50_hours":   _r(_f(relist_row.delay_p50), 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3: Seller Pressure Engine
# ─────────────────────────────────────────────────────────────────────────────

async def _compute_seller_pressure(event_id: int, clearance_rate: Optional[float], db: AsyncSession) -> dict:
    """
    Seller pressure = downward repricing pressure weighted by remaining inventory.
    Seller strength = upward repricing confidence weighted by low remaining inventory.

    seller_pressure_score: [0,1]
      = (fraction_of_listings_that_cut) * 0.5
        + (median_cut_pct / 50) * 0.3      # normalized to 50% max cut
        + (1 - clearance_rate) * 0.2        # more remaining = more pressure

    seller_strength_score: [0,1]
      = (fraction_that_increased) * 0.4
        + (clearance_rate) * 0.3            # high clearance = sellers had strength
        + (avg_relist_markup / 30) * 0.3   # relists at premium = strength
    """
    reprice_row = (await db.execute(text("""
        WITH price_ranges AS (
            SELECT
                listing_id,
                MIN(price) AS min_p,
                MAX(price) AS max_p,
                COUNT(DISTINCT price) AS cnt
            FROM listing_snapshots
            WHERE event_id = :eid
            GROUP BY listing_id
            HAVING COUNT(DISTINCT price) > 1
        )
        SELECT
            COUNT(*)                                          AS repriced_count,
            COUNT(*) FILTER (WHERE min_p < max_p)            AS had_price_cut,
            COUNT(*) FILTER (WHERE max_p > min_p AND min_p = (
                -- listing had an increase (first price < later price at some point)
                -- simplification: max > initial
                min_p
            ))                                               AS had_price_increase,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY CASE WHEN min_p < max_p
                    THEN (max_p - min_p) / NULLIF(min_p, 0) * 100 ELSE NULL END
            )                                               AS median_cut_pct,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY CASE WHEN max_p > min_p
                    THEN (max_p - min_p) / NULLIF(min_p, 0) * 100 ELSE NULL END
            )                                               AS median_increase_pct,
            (SELECT COUNT(*) FROM listing_snapshots WHERE event_id = :eid) AS total_snaps,
            (SELECT COUNT(DISTINCT listing_id) FROM listing_snapshots WHERE event_id = :eid) AS snap_listings
        FROM price_ranges
    """), {"eid": event_id})).fetchone()

    total_snap_listings = int(reprice_row.snap_listings or 1)
    repriced      = int(reprice_row.repriced_count or 0)
    cuts          = int(reprice_row.had_price_cut or 0)
    increases     = int(reprice_row.had_price_increase or 0)
    median_cut    = _f(reprice_row.median_cut_pct)
    median_inc    = _f(reprice_row.median_increase_pct)

    repricing_freq = _r(repriced / total_snap_listings if total_snap_listings > 0 else None)
    frac_cut       = cuts / repriced if repriced > 0 else 0.0
    frac_inc       = increases / repriced if repriced > 0 else 0.0
    cr             = clearance_rate if clearance_rate is not None else 0.5

    # Pressure: driven by cuts, magnitude, and remaining inventory
    pressure_score = (
        frac_cut * 0.5
        + min(1.0, (median_cut or 0) / 50.0) * 0.3
        + (1.0 - cr) * 0.2
    )
    # Strength: driven by increases, clearance, and upward price moves
    strength_score = (
        frac_inc * 0.4
        + cr * 0.4
        + min(1.0, (median_inc or 0) / 30.0) * 0.2
    )

    return {
        "price_cuts_count":         cuts,
        "price_increases_count":    increases,
        "median_price_cut_pct":     _r(median_cut, 2),
        "median_price_increase_pct": _r(median_inc, 2),
        "repricing_frequency":      repricing_freq,
        "seller_pressure_score":    _r(pressure_score),
        "seller_strength_score":    _r(strength_score),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4: Section Absorption Engine
# ─────────────────────────────────────────────────────────────────────────────

async def _compute_section_absorption(event_id: int, db: AsyncSession) -> dict:
    """
    Per-section: inventory_introduced, absorbed, clearance_rate, relist_rate, repricing_rate.
    Returns top_10 and worst_10 absorbed sections (min 5 listings for statistical floor).
    """
    sec_rows = (await db.execute(text("""
        WITH sec_base AS (
            SELECT
                -- normalize section names: strip "Section ", "SEC ", "Upper Bowl ", "Lower Bowl "
                COALESCE(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(l.section,
                            '^(section|sec) ', '', 'i'),
                        '^(upper bowl|lower bowl) ', '', 'i'),
                    'Unknown') AS section,
                COUNT(*)                        AS inventory_introduced,
                SUM(CASE WHEN NOT l.is_active THEN 1 ELSE 0 END) AS absorbed,
                SUM(CASE WHEN l.is_active THEN 1 ELSE 0 END) AS still_active
            FROM listings l
            WHERE l.event_id = :eid
            GROUP BY COALESCE(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(l.section,
                            '^(section|sec) ', '', 'i'),
                        '^(upper bowl|lower bowl) ', '', 'i'),
                    'Unknown')
            HAVING COUNT(*) >= 5
        ),
        sec_relist AS (
            -- count relisted listings per normalized section
            SELECT COALESCE(
                       REGEXP_REPLACE(
                           REGEXP_REPLACE(l.section, '^(section|sec) ', '', 'i'),
                           '^(upper bowl|lower bowl) ', '', 'i'),
                       'Unknown') AS section,
                   COUNT(*) AS relisted
            FROM listings orig
            JOIN listings l ON l.id = orig.id
            JOIN listings new_l ON
                new_l.event_id = orig.event_id
                AND new_l.section = orig.section
                AND new_l.first_seen_at > orig.last_seen_at
                AND new_l.id != orig.id
                AND CASE WHEN orig.price > 0
                    THEN ABS(new_l.price - orig.price) / orig.price * 100 <= 30
                    ELSE false END
            WHERE orig.event_id = :eid AND orig.is_active = false
            GROUP BY COALESCE(
                       REGEXP_REPLACE(
                           REGEXP_REPLACE(l.section, '^(section|sec) ', '', 'i'),
                           '^(upper bowl|lower bowl) ', '', 'i'),
                       'Unknown')
        ),
        sec_reprice AS (
            SELECT COALESCE(
                       REGEXP_REPLACE(
                           REGEXP_REPLACE(l.section, '^(section|sec) ', '', 'i'),
                           '^(upper bowl|lower bowl) ', '', 'i'),
                       'Unknown') AS section,
                   COUNT(DISTINCT ls.listing_id) AS repriced
            FROM listing_snapshots ls
            JOIN listings l ON l.id = ls.listing_id
            WHERE ls.event_id = :eid
            GROUP BY COALESCE(
                       REGEXP_REPLACE(
                           REGEXP_REPLACE(l.section, '^(section|sec) ', '', 'i'),
                           '^(upper bowl|lower bowl) ', '', 'i'),
                       'Unknown'), ls.listing_id
            HAVING COUNT(DISTINCT ls.price) > 1
        ),
        sec_reprice_agg AS (
            SELECT section, COUNT(*) AS repriced FROM sec_reprice GROUP BY section
        )
        SELECT
            sb.section,
            sb.inventory_introduced,
            sb.absorbed,
            sb.still_active,
            ROUND(sb.absorbed::numeric / NULLIF(sb.inventory_introduced, 0) * 100, 1) AS clearance_rate,
            COALESCE(sr.relisted, 0) AS relisted,
            ROUND(COALESCE(sr.relisted, 0)::numeric / NULLIF(sb.absorbed, 0) * 100, 1) AS relist_rate,
            COALESCE(srp.repriced, 0) AS repriced,
            ROUND(COALESCE(srp.repriced, 0)::numeric / NULLIF(sb.inventory_introduced, 0) * 100, 1) AS repricing_rate
        FROM sec_base sb
        LEFT JOIN sec_relist sr ON sr.section = sb.section
        LEFT JOIN sec_reprice_agg srp ON srp.section = sb.section
        ORDER BY clearance_rate DESC
    """), {"eid": event_id})).fetchall()

    def _row_to_dict(r) -> dict:
        return {
            "section":              r.section,
            "inventory_introduced": int(r.inventory_introduced or 0),
            "absorbed":             int(r.absorbed or 0),
            "still_active":         int(r.still_active or 0),
            "clearance_rate":       _f(r.clearance_rate),
            "relisted":             int(r.relisted or 0),
            "relist_rate":          _f(r.relist_rate),
            "repriced":             int(r.repriced or 0),
            "repricing_rate":       _f(r.repricing_rate),
        }

    all_sections = [_row_to_dict(r) for r in sec_rows]
    top_10  = all_sections[:10]
    worst_10 = list(reversed(all_sections))[:10]

    return {
        "top_absorbed_sections":   top_10,
        "worst_absorbed_sections": worst_10,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main outcome computation
# ─────────────────────────────────────────────────────────────────────────────

async def compute_event_outcome(event_id: int, db: AsyncSession) -> dict:
    """
    Compute all 6 intelligence phases for a completed event.
    Upserts result into event_outcomes table.
    Returns the full outcome dict.
    """
    # Load event
    ev_row = (await db.execute(text(
        "SELECT id, title, artist, event_date, status FROM events WHERE id = :eid"
    ), {"eid": event_id})).fetchone()

    if not ev_row:
        raise ValueError(f"Event {event_id} not found")

    event_date = ev_row.event_date
    if hasattr(event_date, 'tzinfo') and event_date.tzinfo is not None:
        event_date = event_date.replace(tzinfo=None)

    # Snapshot count check
    snap_count = (await db.execute(text(
        "SELECT COUNT(*) FROM listing_snapshots WHERE event_id = :eid"
    ), {"eid": event_id})).scalar()

    if not snap_count:
        return {
            "event_id":   event_id,
            "status":     "NO_SNAPSHOT_DATA",
            "computed_at": datetime.utcnow().isoformat(),
        }

    # Check marketplace count
    mp_count = (await db.execute(text(
        "SELECT COUNT(DISTINCT marketplace_id) FROM listings WHERE event_id = :eid"
    ), {"eid": event_id})).scalar()

    # Phase 1: Clearance
    clearance = await _compute_clearance(event_id, event_date, db)

    # Phase 2: Relist
    relist = await _compute_relist(event_id, db)

    # Phase 3: Seller pressure
    seller = await _compute_seller_pressure(
        event_id, clearance.get("postshow_clearance_rate"), db
    )

    # Phase 4: Section absorption
    sections = await _compute_section_absorption(event_id, db)

    # Assemble full outcome
    outcome = {
        "event_id":    event_id,
        "event_title": ev_row.title,
        "artist":      ev_row.artist,
        "event_date":  event_date.isoformat() if event_date else None,
        "computed_at": datetime.utcnow().isoformat(),
        "marketplaces_tracked": int(mp_count or 0),
        **clearance,
        **relist,
        **seller,
        **sections,
        # Phase 6: Evidence signals (raw inputs for future buy logic)
        "evidence": {
            "market_clearance":  _signal(clearance.get("postshow_clearance_rate"), 0.5, 0.8),
            "seller_pressure":   _signal(seller.get("seller_pressure_score"), 0.3, 0.6),
            "relist_activity":   _signal(relist.get("relist_percentage"), 0.05, 0.15),
            "inventory_remaining": _signal(clearance.get("remaining_inventory_rate"), 0.1, 0.3),
        },
    }

    # Persist to event_outcomes
    await db.execute(text("""
        INSERT INTO event_outcomes (
            event_id,
            total_listings_seen, total_tickets_seen,
            listings_at_event_start, tickets_at_event_start,
            listings_1h_post, tickets_1h_post,
            listings_6h_post, tickets_6h_post,
            listings_24h_post, tickets_24h_post,
            event_start_clearance_rate, postshow_clearance_rate, remaining_inventory_rate,
            total_disappeared, total_relisted, relist_percentage,
            relisted_then_disappeared, sold_after_relist_pct,
            avg_relist_markup_pct, avg_relist_discount_pct, relist_success_rate,
            relist_delay_p50_hours,
            price_cuts_count, price_increases_count,
            median_price_cut_pct, median_price_increase_pct,
            repricing_frequency, seller_pressure_score, seller_strength_score,
            top_absorbed_sections, worst_absorbed_sections,
            data_coverage_hours, has_postshow_data, marketplaces_tracked,
            computed_at
        ) VALUES (
            :event_id,
            :total_listings_seen, :total_tickets_seen,
            :listings_at_event_start, :tickets_at_event_start,
            :listings_1h_post, :tickets_1h_post,
            :listings_6h_post, :tickets_6h_post,
            :listings_24h_post, :tickets_24h_post,
            :event_start_clearance_rate, :postshow_clearance_rate, :remaining_inventory_rate,
            :total_disappeared, :total_relisted, :relist_percentage,
            :relisted_then_disappeared, :sold_after_relist_pct,
            :avg_relist_markup_pct, :avg_relist_discount_pct, :relist_success_rate,
            :relist_delay_p50_hours,
            :price_cuts_count, :price_increases_count,
            :median_price_cut_pct, :median_price_increase_pct,
            :repricing_frequency, :seller_pressure_score, :seller_strength_score,
            CAST(:top_absorbed_sections AS jsonb), CAST(:worst_absorbed_sections AS jsonb),
            :data_coverage_hours, :has_postshow_data, :marketplaces_tracked,
            NOW()
        )
        ON CONFLICT (event_id) DO UPDATE SET
            total_listings_seen           = EXCLUDED.total_listings_seen,
            total_tickets_seen            = EXCLUDED.total_tickets_seen,
            listings_at_event_start       = EXCLUDED.listings_at_event_start,
            tickets_at_event_start        = EXCLUDED.tickets_at_event_start,
            listings_1h_post              = EXCLUDED.listings_1h_post,
            tickets_1h_post               = EXCLUDED.tickets_1h_post,
            listings_6h_post              = EXCLUDED.listings_6h_post,
            tickets_6h_post               = EXCLUDED.tickets_6h_post,
            listings_24h_post             = EXCLUDED.listings_24h_post,
            tickets_24h_post              = EXCLUDED.tickets_24h_post,
            event_start_clearance_rate    = EXCLUDED.event_start_clearance_rate,
            postshow_clearance_rate       = EXCLUDED.postshow_clearance_rate,
            remaining_inventory_rate      = EXCLUDED.remaining_inventory_rate,
            total_disappeared             = EXCLUDED.total_disappeared,
            total_relisted                = EXCLUDED.total_relisted,
            relist_percentage             = EXCLUDED.relist_percentage,
            relisted_then_disappeared     = EXCLUDED.relisted_then_disappeared,
            sold_after_relist_pct         = EXCLUDED.sold_after_relist_pct,
            avg_relist_markup_pct         = EXCLUDED.avg_relist_markup_pct,
            avg_relist_discount_pct       = EXCLUDED.avg_relist_discount_pct,
            relist_success_rate           = EXCLUDED.relist_success_rate,
            relist_delay_p50_hours        = EXCLUDED.relist_delay_p50_hours,
            price_cuts_count              = EXCLUDED.price_cuts_count,
            price_increases_count         = EXCLUDED.price_increases_count,
            median_price_cut_pct          = EXCLUDED.median_price_cut_pct,
            median_price_increase_pct     = EXCLUDED.median_price_increase_pct,
            repricing_frequency           = EXCLUDED.repricing_frequency,
            seller_pressure_score         = EXCLUDED.seller_pressure_score,
            seller_strength_score         = EXCLUDED.seller_strength_score,
            top_absorbed_sections         = EXCLUDED.top_absorbed_sections,
            worst_absorbed_sections       = EXCLUDED.worst_absorbed_sections,
            data_coverage_hours           = EXCLUDED.data_coverage_hours,
            has_postshow_data             = EXCLUDED.has_postshow_data,
            marketplaces_tracked          = EXCLUDED.marketplaces_tracked,
            computed_at                   = NOW()
    """), {
        "event_id": event_id,
        "total_listings_seen":          clearance["total_listings_seen"],
        "total_tickets_seen":           clearance["total_tickets_seen"],
        "listings_at_event_start":      clearance["listings_at_event_start"],
        "tickets_at_event_start":       clearance["tickets_at_event_start"],
        "listings_1h_post":             clearance["listings_1h_post"],
        "tickets_1h_post":              clearance["tickets_1h_post"],
        "listings_6h_post":             clearance["listings_6h_post"],
        "tickets_6h_post":              clearance["tickets_6h_post"],
        "listings_24h_post":            clearance["listings_24h_post"],
        "tickets_24h_post":             clearance["tickets_24h_post"],
        "event_start_clearance_rate":   clearance["event_start_clearance_rate"],
        "postshow_clearance_rate":      clearance["postshow_clearance_rate"],
        "remaining_inventory_rate":     clearance["remaining_inventory_rate"],
        "total_disappeared":            relist["total_disappeared"],
        "total_relisted":               relist["total_relisted"],
        "relist_percentage":            relist["relist_percentage"],
        "relisted_then_disappeared":    relist["relisted_then_disappeared"],
        "sold_after_relist_pct":        relist["sold_after_relist_pct"],
        "avg_relist_markup_pct":        relist["avg_relist_markup_pct"],
        "avg_relist_discount_pct":      relist["avg_relist_discount_pct"],
        "relist_success_rate":          relist["relist_success_rate"],
        "relist_delay_p50_hours":       relist["relist_delay_p50_hours"],
        "price_cuts_count":             seller["price_cuts_count"],
        "price_increases_count":        seller["price_increases_count"],
        "median_price_cut_pct":         seller["median_price_cut_pct"],
        "median_price_increase_pct":    seller["median_price_increase_pct"],
        "repricing_frequency":          seller["repricing_frequency"],
        "seller_pressure_score":        seller["seller_pressure_score"],
        "seller_strength_score":        seller["seller_strength_score"],
        "top_absorbed_sections":        __import__("json").dumps(sections["top_absorbed_sections"]),
        "worst_absorbed_sections":      __import__("json").dumps(sections["worst_absorbed_sections"]),
        "data_coverage_hours":          clearance["data_coverage_hours"],
        "has_postshow_data":            clearance["has_postshow_data"],
        "marketplaces_tracked":         int(mp_count or 0),
    })
    await db.commit()

    logger.info(
        "OUTCOME: computed event_id=%d '%s' clearance=%.1f%% relist=%.1f%%",
        event_id, ev_row.title,
        (clearance.get("postshow_clearance_rate") or 0) * 100,
        (relist.get("relist_percentage") or 0) * 100,
    )
    return outcome


async def get_event_outcome(event_id: int, db: AsyncSession) -> Optional[dict]:
    """Return cached outcome if it exists and is less than 24h old."""
    row = (await db.execute(text("""
        SELECT * FROM event_outcomes WHERE event_id = :eid
    """), {"eid": event_id})).fetchone()

    if not row:
        return None

    # Serve from cache if computed < 24h ago
    age_hours = (datetime.utcnow() - row.computed_at).total_seconds() / 3600
    if age_hours < 24:
        return dict(row._mapping)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5: Artist Market Profile
# ─────────────────────────────────────────────────────────────────────────────

async def build_artist_profile(artist: str, db: AsyncSession) -> dict:
    """
    Aggregate all computed event_outcomes for this artist into a market profile.
    Upserts artist_market_profiles row.
    """
    rows = (await db.execute(text("""
        SELECT eo.*, e.event_date
        FROM event_outcomes eo
        JOIN events e ON e.id = eo.event_id
        WHERE e.artist ILIKE :artist AND e.status = 'completed'
        ORDER BY e.event_date
    """), {"artist": artist})).fetchall()

    if not rows:
        return {"artist": artist, "event_count": 0, "status": "NO_COMPLETED_EVENTS"}

    def _avg(field: str) -> Optional[float]:
        vals = [_f(r._mapping.get(field)) for r in rows if _f(r._mapping.get(field)) is not None]
        return _r(sum(vals) / len(vals)) if vals else None

    def _min(field: str) -> Optional[float]:
        vals = [_f(r._mapping.get(field)) for r in rows if _f(r._mapping.get(field)) is not None]
        return _r(min(vals)) if vals else None

    def _max(field: str) -> Optional[float]:
        vals = [_f(r._mapping.get(field)) for r in rows if _f(r._mapping.get(field)) is not None]
        return _r(max(vals)) if vals else None

    event_ids = [r.event_id for r in rows]
    avg_clearance = _avg("postshow_clearance_rate")
    avg_pressure  = _avg("seller_pressure_score")
    avg_relist    = _avg("relist_percentage")

    profile = {
        "artist":                   artist,
        "event_count":              len(rows),
        "completed_event_ids":      event_ids,
        "avg_clearance_rate":       avg_clearance,
        "min_clearance_rate":       _min("postshow_clearance_rate"),
        "max_clearance_rate":       _max("postshow_clearance_rate"),
        "avg_inventory_remaining":  _avg("remaining_inventory_rate"),
        "avg_relist_pct":           avg_relist,
        "avg_sold_after_relist_pct": _avg("sold_after_relist_pct"),
        "avg_relist_markup_pct":    _avg("avg_relist_markup_pct"),
        "avg_relist_discount_pct":  _avg("avg_relist_discount_pct"),
        "avg_seller_pressure":      avg_pressure,
        "avg_seller_strength":      _avg("seller_strength_score"),
        "avg_repricing_frequency":  _avg("repricing_frequency"),
        "avg_price_cut_pct":        _avg("median_price_cut_pct"),
        # Phase 6: Evidence signals
        "market_clearance_signal":  _signal(avg_clearance, 0.5, 0.8),
        "seller_pressure_signal":   _signal(avg_pressure, 0.3, 0.6),
        "relist_activity_signal":   _signal(avg_relist, 0.05, 0.15),
        "computed_at":              datetime.utcnow().isoformat(),
    }

    await db.execute(text("""
        INSERT INTO artist_market_profiles (
            artist, event_count, completed_event_ids,
            avg_clearance_rate, min_clearance_rate, max_clearance_rate, avg_inventory_remaining,
            avg_relist_pct, avg_sold_after_relist_pct, avg_relist_markup_pct, avg_relist_discount_pct,
            avg_seller_pressure, avg_seller_strength, avg_repricing_frequency, avg_price_cut_pct,
            market_clearance_signal, seller_pressure_signal, relist_activity_signal,
            computed_at
        ) VALUES (
            :artist, :event_count, CAST(:completed_event_ids AS jsonb),
            :avg_clearance_rate, :min_clearance_rate, :max_clearance_rate, :avg_inventory_remaining,
            :avg_relist_pct, :avg_sold_after_relist_pct, :avg_relist_markup_pct, :avg_relist_discount_pct,
            :avg_seller_pressure, :avg_seller_strength, :avg_repricing_frequency, :avg_price_cut_pct,
            :market_clearance_signal, :seller_pressure_signal, :relist_activity_signal,
            NOW()
        )
        ON CONFLICT (artist) DO UPDATE SET
            event_count                 = EXCLUDED.event_count,
            completed_event_ids         = EXCLUDED.completed_event_ids,
            avg_clearance_rate          = EXCLUDED.avg_clearance_rate,
            min_clearance_rate          = EXCLUDED.min_clearance_rate,
            max_clearance_rate          = EXCLUDED.max_clearance_rate,
            avg_inventory_remaining     = EXCLUDED.avg_inventory_remaining,
            avg_relist_pct              = EXCLUDED.avg_relist_pct,
            avg_sold_after_relist_pct   = EXCLUDED.avg_sold_after_relist_pct,
            avg_relist_markup_pct       = EXCLUDED.avg_relist_markup_pct,
            avg_relist_discount_pct     = EXCLUDED.avg_relist_discount_pct,
            avg_seller_pressure         = EXCLUDED.avg_seller_pressure,
            avg_seller_strength         = EXCLUDED.avg_seller_strength,
            avg_repricing_frequency     = EXCLUDED.avg_repricing_frequency,
            avg_price_cut_pct           = EXCLUDED.avg_price_cut_pct,
            market_clearance_signal     = EXCLUDED.market_clearance_signal,
            seller_pressure_signal      = EXCLUDED.seller_pressure_signal,
            relist_activity_signal      = EXCLUDED.relist_activity_signal,
            computed_at                 = NOW()
    """), {
        "artist":                   artist,
        "event_count":              len(rows),
        "completed_event_ids":      __import__("json").dumps(event_ids),
        "avg_clearance_rate":       profile["avg_clearance_rate"],
        "min_clearance_rate":       profile["min_clearance_rate"],
        "max_clearance_rate":       profile["max_clearance_rate"],
        "avg_inventory_remaining":  profile["avg_inventory_remaining"],
        "avg_relist_pct":           profile["avg_relist_pct"],
        "avg_sold_after_relist_pct": profile["avg_sold_after_relist_pct"],
        "avg_relist_markup_pct":    profile["avg_relist_markup_pct"],
        "avg_relist_discount_pct":  profile["avg_relist_discount_pct"],
        "avg_seller_pressure":      profile["avg_seller_pressure"],
        "avg_seller_strength":      profile["avg_seller_strength"],
        "avg_repricing_frequency":  profile["avg_repricing_frequency"],
        "avg_price_cut_pct":        profile["avg_price_cut_pct"],
        "market_clearance_signal":  profile["market_clearance_signal"],
        "seller_pressure_signal":   profile["seller_pressure_signal"],
        "relist_activity_signal":   profile["relist_activity_signal"],
    })
    await db.commit()

    logger.info(
        "ARTIST_PROFILE: %s events=%d avg_clearance=%.1f%% avg_relist=%.1f%%",
        artist, len(rows),
        (avg_clearance or 0) * 100,
        (avg_relist or 0) * 100,
    )
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# Batch processor (used by scheduler)
# ─────────────────────────────────────────────────────────────────────────────

async def compute_all_pending(db: AsyncSession) -> dict:
    """
    Compute outcomes for all completed events that either have no outcome row
    or whose outcome was computed > 24h ago.
    Returns counts.
    """
    pending = (await db.execute(text("""
        SELECT e.id, e.artist
        FROM events e
        LEFT JOIN event_outcomes eo ON eo.event_id = e.id
        WHERE e.status = 'completed'
          AND (eo.id IS NULL OR eo.computed_at < NOW() - INTERVAL '24 hours')
    """))).fetchall()

    counts = {"computed": 0, "failed": 0, "no_data": 0}
    artists_to_update: set[str] = set()

    for row in pending:
        try:
            result = await compute_event_outcome(row.id, db)
            if result.get("status") == "NO_SNAPSHOT_DATA":
                counts["no_data"] += 1
            else:
                counts["computed"] += 1
                if row.artist:
                    artists_to_update.add(row.artist)
        except Exception as exc:
            logger.error("OUTCOME: failed event_id=%d — %s", row.id, exc)
            counts["failed"] += 1

    for artist in artists_to_update:
        try:
            await build_artist_profile(artist, db)
        except Exception as exc:
            logger.error("ARTIST_PROFILE: failed '%s' — %s", artist, exc)

    return counts


# ─────────────────────────────────────────────────────────────────────────────
# Event-type benchmark computation
# ─────────────────────────────────────────────────────────────────────────────

async def compute_event_type_benchmarks(db: AsyncSession) -> dict:
    """
    Group completed event outcomes by event type and compute benchmark distributions.
    Upserts into event_type_benchmarks. Returns dict keyed by event_type.
    """
    rows = (await db.execute(text("""
        SELECT eo.event_id,
               eo.postshow_clearance_rate, eo.remaining_inventory_rate,
               eo.relist_percentage, eo.sold_after_relist_pct,
               eo.seller_pressure_score, eo.seller_strength_score,
               eo.repricing_frequency,
               e.title, e.artist,
               v.name AS venue_name
        FROM event_outcomes eo
        JOIN events e ON e.id = eo.event_id
        JOIN venues v ON v.id = e.venue_id
        WHERE e.status = 'completed' AND eo.postshow_clearance_rate IS NOT NULL
    """))).fetchall()

    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        etype = _classify_event_type(r.title, r.venue_name)
        groups[etype].append(r)

    results = {}
    for etype, events in groups.items():
        def _avg(field: str) -> Optional[float]:
            vals = [_f(r._mapping.get(field)) for r in events if _f(r._mapping.get(field)) is not None]
            return _r(sum(vals) / len(vals)) if vals else None

        def _pN(field: str, n: int) -> Optional[float]:
            vals = sorted(_f(r._mapping.get(field)) for r in events if _f(r._mapping.get(field)) is not None)
            if not vals:
                return None
            idx = max(0, int(len(vals) * n / 100) - 1)
            return _r(vals[idx])

        event_ids = [r.event_id for r in events]
        benchmark = {
            "event_type":              etype,
            "event_count":             len(events),
            "event_ids":               event_ids,
            "avg_clearance_rate":      _avg("postshow_clearance_rate"),
            "p25_clearance_rate":      _pN("postshow_clearance_rate", 25),
            "p50_clearance_rate":      _pN("postshow_clearance_rate", 50),
            "p75_clearance_rate":      _pN("postshow_clearance_rate", 75),
            "avg_relist_pct":          _avg("relist_percentage"),
            "p50_relist_pct":          _pN("relist_percentage", 50),
            "avg_seller_pressure":     _avg("seller_pressure_score"),
            "p50_seller_pressure":     _pN("seller_pressure_score", 50),
            "avg_inventory_remaining": _avg("remaining_inventory_rate"),
            "p50_inventory_remaining": _pN("remaining_inventory_rate", 50),
        }

        await db.execute(text("""
            INSERT INTO event_type_benchmarks (
                event_type, event_count, event_ids,
                avg_clearance_rate, p25_clearance_rate, p50_clearance_rate, p75_clearance_rate,
                avg_relist_pct, p50_relist_pct,
                avg_seller_pressure, p50_seller_pressure,
                avg_inventory_remaining, p50_inventory_remaining,
                computed_at
            ) VALUES (
                :event_type, :event_count, CAST(:event_ids AS jsonb),
                :avg_clearance_rate, :p25_clearance_rate, :p50_clearance_rate, :p75_clearance_rate,
                :avg_relist_pct, :p50_relist_pct,
                :avg_seller_pressure, :p50_seller_pressure,
                :avg_inventory_remaining, :p50_inventory_remaining,
                NOW()
            )
            ON CONFLICT (event_type) DO UPDATE SET
                event_count              = EXCLUDED.event_count,
                event_ids                = EXCLUDED.event_ids,
                avg_clearance_rate       = EXCLUDED.avg_clearance_rate,
                p25_clearance_rate       = EXCLUDED.p25_clearance_rate,
                p50_clearance_rate       = EXCLUDED.p50_clearance_rate,
                p75_clearance_rate       = EXCLUDED.p75_clearance_rate,
                avg_relist_pct           = EXCLUDED.avg_relist_pct,
                p50_relist_pct           = EXCLUDED.p50_relist_pct,
                avg_seller_pressure      = EXCLUDED.avg_seller_pressure,
                p50_seller_pressure      = EXCLUDED.p50_seller_pressure,
                avg_inventory_remaining  = EXCLUDED.avg_inventory_remaining,
                p50_inventory_remaining  = EXCLUDED.p50_inventory_remaining,
                computed_at              = NOW()
        """), {**benchmark, "event_ids": json.dumps(event_ids)})
        results[etype] = benchmark

    await db.commit()
    logger.info("EVENT_TYPE_BENCHMARKS: computed %d categories", len(results))
    return results


async def get_event_type_benchmarks(db: AsyncSession) -> list[dict]:
    """Read event type benchmarks from cache."""
    rows = (await db.execute(text(
        "SELECT * FROM event_type_benchmarks ORDER BY event_type"
    ))).fetchall()
    return [dict(r._mapping) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Active-vs-historical comparison (percentile ranking)
# ─────────────────────────────────────────────────────────────────────────────

async def compute_active_comparison(event_id: int, db: AsyncSession) -> dict:
    """
    Compare an active (upcoming) event's current market metrics to the
    completed-event benchmark pool.

    Returns percentile ranks for seller pressure and relist activity.
    Clearance percentile is deferred (event has not occurred yet).
    No buy/wait signals are generated.
    """
    ev_row = (await db.execute(text(
        "SELECT id, title, artist, event_date, status FROM events WHERE id = :eid"
    ), {"eid": event_id})).fetchone()

    if not ev_row:
        raise ValueError(f"Event {event_id} not found")

    # Load completed benchmark distribution
    bench_rows = (await db.execute(text("""
        SELECT event_id,
               postshow_clearance_rate,
               seller_pressure_score,
               relist_percentage,
               remaining_inventory_rate,
               repricing_frequency
        FROM event_outcomes
        WHERE postshow_clearance_rate IS NOT NULL
        ORDER BY event_id
    """))).fetchall()

    if not bench_rows:
        return {"event_id": event_id, "status": "NO_BENCHMARK_DATA",
                "note": "No completed events with outcomes available for comparison."}

    # Current live market: most recent market_intelligence record
    mi_row = (await db.execute(text("""
        SELECT seller_aggression, capitulation_score, relisting_rate,
               relist_pressure, current_listings, days_until_event
        FROM market_intelligence
        WHERE event_id = :eid
        ORDER BY computed_at DESC
        LIMIT 1
    """), {"eid": event_id})).fetchone()

    # Build distributions from completed events
    def _dist(field: str) -> list[float]:
        return sorted(_f(r._mapping.get(field)) for r in bench_rows
                      if _f(r._mapping.get(field)) is not None)

    def _pct_rank(value: Optional[float], dist: list[float]) -> Optional[float]:
        """Fraction of benchmark values <= value (lower = rarer)."""
        if value is None or not dist:
            return None
        return _r(sum(1 for v in dist if v <= value) / len(dist))

    def _pN(dist: list[float], n: int) -> Optional[float]:
        if not dist:
            return None
        idx = max(0, int(len(dist) * n / 100) - 1)
        return _r(dist[idx])

    pressure_dist = _dist("seller_pressure_score")
    relist_dist   = _dist("relist_percentage")
    remain_dist   = _dist("remaining_inventory_rate")

    current_pressure = _f(mi_row.seller_aggression)   if mi_row else None
    current_relist   = _f(mi_row.relisting_rate)      if mi_row else None
    current_listings = int(mi_row.current_listings or 0) if mi_row else None
    days_until       = _f(mi_row.days_until_event)    if mi_row else None

    # Compute confidence score based on benchmark pool size
    n = len(bench_rows)
    if n >= 10:
        confidence_score = 0.85
        confidence_label = "ADEQUATE"
    elif n >= 5:
        confidence_score = 0.65
        confidence_label = "MARGINAL"
    elif n >= 3:
        confidence_score = 0.45
        confidence_label = "LOW"
    elif n >= 1:
        confidence_score = 0.25
        confidence_label = "INSUFFICIENT"
    else:
        confidence_score = 0.0
        confidence_label = "NO_DATA"

    event_date = ev_row.event_date
    if event_date and hasattr(event_date, 'tzinfo') and event_date.tzinfo:
        event_date = event_date.replace(tzinfo=None)

    # Infer event type for contextual benchmark
    venue_row = (await db.execute(text(
        "SELECT v.name FROM events e JOIN venues v ON v.id=e.venue_id WHERE e.id=:eid"
    ), {"eid": event_id})).fetchone()
    event_type = _classify_event_type(ev_row.title, venue_row.name if venue_row else "")

    return {
        "event_id":          event_id,
        "event_title":       ev_row.title,
        "event_date":        event_date.isoformat() if event_date else None,
        "days_until_event":  days_until,
        "event_type":        event_type,
        "benchmark_pool": {
            "size":             n,
            "event_ids":        [r.event_id for r in bench_rows],
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
        },
        "current_market": {
            "listings_active":  current_listings,
            "seller_aggression": current_pressure,
            "relisting_rate":   current_relist,
        },
        "percentiles": {
            # How does this event's current seller pressure rank vs completed events?
            "seller_pressure_pct": _pct_rank(current_pressure, pressure_dist),
            # How does relisting activity rank?
            "relist_activity_pct": _pct_rank(current_relist, relist_dist),
            # Clearance: not applicable until event occurs
            "clearance_pct": None,
        },
        "benchmark_distribution": {
            "seller_pressure": {
                "p25": _pN(pressure_dist, 25),
                "p50": _pN(pressure_dist, 50),
                "p75": _pN(pressure_dist, 75),
            },
            "relist_activity": {
                "p25": _pN(relist_dist, 25),
                "p50": _pN(relist_dist, 50),
                "p75": _pN(relist_dist, 75),
            },
            "inventory_remaining": {
                "p25": _pN(remain_dist, 25),
                "p50": _pN(remain_dist, 50),
                "p75": _pN(remain_dist, 75),
            },
        },
        "note": (
            "Percentiles rank current market metrics against the completed-event baseline. "
            "Clearance percentile is deferred until after the event. "
            "No buy/wait signals are generated."
        ),
    }
