"""
venue_intelligence.py — SoFi Venue Section Intelligence

Responsibilities:
  1. normalize_section()      — raw marketplace string → canonical section_id
  2. compute_section_metrics()— per-event section metrics, stored in venue_section_metrics
  3. get_venue_intelligence() — full section list + metrics for one event
  4. get_classifications()    — ranked classification outputs (best value, highest demand, etc.)

Architecture:
  - Uses in-memory ALIAS_LOOKUP from sofi_catalog for O(1) alias resolution
  - Falls back to DB lookup (venue_section_aliases) if catalog miss
  - All DB writes go to venue_section_metrics (upsert by section+event)
  - Metrics computed from listings table (current active listings on Railway)
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ── Catalog import (in-memory lookup) ────────────────────────────────────────
# data/ lives one level above the app package (backend/data/).
# In Railway the WORKDIR is /app (= backend/), so `data` is importable as a package.
import sys, os as _os
_data_dir = _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "data")
if _os.path.isdir(_os.path.abspath(_data_dir)):
    sys.path.insert(0, _os.path.abspath(_data_dir))
try:
    from data.sofi_catalog import (
        ALIAS_LOOKUP as _SOFI_ALIAS_LOOKUP,
        SECTION_BY_ID as _SOFI_SECTION_BY_ID,
        VENUE_SLUG, SECTIONS as _SOFI_SECTIONS,
    )
    from data.crypto_arena_catalog import (
        ALIAS_LOOKUP as _CRYPTO_ALIAS_LOOKUP,
        SECTION_BY_ID as _CRYPTO_SECTION_BY_ID,
        SECTIONS as _CRYPTO_SECTIONS,
    )
    from data.kia_forum_catalog import (
        ALIAS_LOOKUP as _KIA_ALIAS_LOOKUP,
        SECTION_BY_ID as _KIA_SECTION_BY_ID,
        SECTIONS as _KIA_SECTIONS,
    )
    from data.hollywood_bowl_catalog import (
        ALIAS_LOOKUP as _BOWL_ALIAS_LOOKUP,
        SECTION_BY_ID as _BOWL_SECTION_BY_ID,
        SECTIONS as _BOWL_SECTIONS,
    )
    from data.greek_theatre_catalog import (
        ALIAS_LOOKUP as _GREEK_ALIAS_LOOKUP,
        SECTION_BY_ID as _GREEK_SECTION_BY_ID,
        SECTIONS as _GREEK_SECTIONS,
    )
except ImportError:
    from sofi_catalog import (
        ALIAS_LOOKUP as _SOFI_ALIAS_LOOKUP,
        SECTION_BY_ID as _SOFI_SECTION_BY_ID,
        VENUE_SLUG, SECTIONS as _SOFI_SECTIONS,
    )
    from crypto_arena_catalog import (
        ALIAS_LOOKUP as _CRYPTO_ALIAS_LOOKUP,
        SECTION_BY_ID as _CRYPTO_SECTION_BY_ID,
        SECTIONS as _CRYPTO_SECTIONS,
    )
    from kia_forum_catalog import (
        ALIAS_LOOKUP as _KIA_ALIAS_LOOKUP,
        SECTION_BY_ID as _KIA_SECTION_BY_ID,
        SECTIONS as _KIA_SECTIONS,
    )
    from hollywood_bowl_catalog import (
        ALIAS_LOOKUP as _BOWL_ALIAS_LOOKUP,
        SECTION_BY_ID as _BOWL_SECTION_BY_ID,
        SECTIONS as _BOWL_SECTIONS,
    )
    from greek_theatre_catalog import (
        ALIAS_LOOKUP as _GREEK_ALIAS_LOOKUP,
        SECTION_BY_ID as _GREEK_SECTION_BY_ID,
        SECTIONS as _GREEK_SECTIONS,
    )

# Compatibility aliases for SoFi (used in normalize_section)
ALIAS_LOOKUP = _SOFI_ALIAS_LOOKUP
SECTION_BY_ID = _SOFI_SECTION_BY_ID
SECTIONS = _SOFI_SECTIONS

# Per-venue catalog registry
_VENUE_CATALOGS: dict[str, dict] = {
    "sofi-stadium":  {"alias_lookup": _SOFI_ALIAS_LOOKUP,   "section_by_id": _SOFI_SECTION_BY_ID,   "sections": _SOFI_SECTIONS},
    "crypto-arena":  {"alias_lookup": _CRYPTO_ALIAS_LOOKUP,  "section_by_id": _CRYPTO_SECTION_BY_ID,  "sections": _CRYPTO_SECTIONS},
    "kia-forum":     {"alias_lookup": _KIA_ALIAS_LOOKUP,     "section_by_id": _KIA_SECTION_BY_ID,     "sections": _KIA_SECTIONS},
    "hollywood-bowl":{"alias_lookup": _BOWL_ALIAS_LOOKUP,    "section_by_id": _BOWL_SECTION_BY_ID,    "sections": _BOWL_SECTIONS},
    "greek-theatre": {"alias_lookup": _GREEK_ALIAS_LOOKUP,   "section_by_id": _GREEK_SECTION_BY_ID,   "sections": _GREEK_SECTIONS},
}

def get_catalog(venue_slug: str) -> dict | None:
    """Return the in-memory catalog for a venue slug, or None if not registered."""
    return _VENUE_CATALOGS.get(venue_slug)


# ─────────────────────────────────────────────────────────────────────────────
# Normalization helpers
# ─────────────────────────────────────────────────────────────────────────────

_STRIP_PREFIX = re.compile(
    r"^\s*(section|sections|sec\.?|sect\.?|lower\s+box|upper\s+box|"
    r"club\s+infield|club\s+outfield|view\s+box|field\s+box|"
    r"infield\s+box|outfield\s+box|loge\s+box|"
    r"floor\s+box)\s*",
    re.IGNORECASE,
)

def _norm(raw: str) -> str:
    """Normalize raw section string for alias lookup."""
    s = raw.strip().lower()
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    # Strip common prefix words
    s = _STRIP_PREFIX.sub("", s).strip()
    return s


def normalize_section(
    raw: str,
    marketplace_id: Optional[int] = None,
) -> Optional[str]:
    """
    Map a raw marketplace section string to a canonical section_id.

    Lookup order:
      1. Exact: (marketplace_id, norm_alias) in ALIAS_LOOKUP
      2. Universal: (None, norm_alias) in ALIAS_LOOKUP
      3. Numeric fallback: if norm is a bare integer, check SECTION_BY_ID

    Returns canonical section_id str or None if no match.
    NOTE: This is SoFi-only.  For other venues use normalize_section_generic().
    """
    if not raw:
        return None

    norm = _norm(raw)

    # 1. marketplace-specific exact match
    sid = ALIAS_LOOKUP.get((marketplace_id, norm))
    if sid:
        return sid

    # 2. universal alias
    sid = ALIAS_LOOKUP.get((None, norm))
    if sid:
        return sid

    # 3. bare number → try direct section_id lookup
    if norm.isdigit() and norm in SECTION_BY_ID:
        return norm

    return None


def normalize_section_generic(
    raw: str,
    vs_by_sid: dict,
) -> Optional[str]:
    """
    Generic section normalizer for non-SoFi venues.

    Lookup order:
      1. Direct _norm(raw) == _norm(section_id) in vs_by_sid
      2. Exact raw == section_id (case-insensitive)
      3. Strip 'section ' prefix and try again
    """
    if not raw:
        return None

    norm_raw = _norm(raw)

    # Build normalised lookup once if not already cached
    # Direct match: norm(raw) == norm(section_id)
    for sid in vs_by_sid:
        if _norm(sid) == norm_raw:
            return sid

    # Also try the raw_section_id (already a string integer sometimes)
    if norm_raw in vs_by_sid:
        return norm_raw

    return None


# ─────────────────────────────────────────────────────────────────────────────
# SQL — section metrics from listings table
# ─────────────────────────────────────────────────────────────────────────────

_SECTION_PRICE_SQL = text("""
    SELECT
        l.section_id                                            AS raw_section_id,
        l.marketplace_id                                        AS marketplace_id,
        l.section                                               AS raw_section,
        MIN(l.price)                                            AS low_ask,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY l.price)   AS median_ask,
        MAX(l.price)                                            AS high_ask,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY l.price)  AS p25_ask,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY l.price)  AS p75_ask,
        COUNT(l.id)                                             AS listing_count,
        SUM(l.quantity)                                         AS ticket_count
    FROM listings l
    WHERE l.event_id = :event_id
      AND l.is_active = TRUE
      AND l.price > 0
      AND l.section_id IS NOT NULL
    GROUP BY l.section_id, l.marketplace_id, l.section
    ORDER BY listing_count DESC
""")

_SECTION_TREND_SQL = text("""
    WITH snaps AS (
        SELECT
            ls.listing_id,
            ls.price,
            ls.snapshot_at,
            l.section_id,
            l.marketplace_id,
            LAG(ls.price) OVER (
                PARTITION BY ls.listing_id ORDER BY ls.snapshot_at
            ) AS prev_price
        FROM listing_snapshots ls
        JOIN listings l ON l.id = ls.listing_id
        WHERE ls.event_id = :event_id
          AND ls.snapshot_at >= NOW() - INTERVAL '24 hours'
          AND l.section_id IS NOT NULL
    )
    SELECT
        section_id,
        marketplace_id,
        COUNT(*)  FILTER (WHERE prev_price IS NOT NULL AND price < prev_price) AS price_drops,
        COUNT(*)  FILTER (WHERE prev_price IS NOT NULL AND price > prev_price) AS price_gains,
        AVG(CASE WHEN prev_price IS NOT NULL AND price <> prev_price
                 THEN price - prev_price END)                                  AS avg_delta
    FROM snaps
    WHERE prev_price IS NOT NULL
    GROUP BY section_id, marketplace_id
""")

_VENUE_SECTION_LOOKUP_SQL = text("""
    SELECT vs.id, vs.section_id, vs.tier, vs.quality_score
    FROM venue_sections vs
    JOIN venues v ON v.id = vs.venue_id
    WHERE v.slug = :slug
""")

_UPSERT_METRICS_SQL = text("""
    INSERT INTO venue_section_metrics (
        venue_section_id, event_id, computed_at,
        low_ask, median_ask, high_ask, p25_ask, p75_ask,
        inventory, listing_count, ticket_count,
        inventory_delta_24h, price_delta_24h, price_delta_pct_24h,
        deal_score, demand_score, seller_pressure, value_score,
        price_vs_tier_median, price_vs_venue_median
    ) VALUES (
        :venue_section_id, :event_id, :computed_at,
        :low_ask, :median_ask, :high_ask, :p25_ask, :p75_ask,
        :inventory, :listing_count, :ticket_count,
        :inventory_delta_24h, :price_delta_24h, :price_delta_pct_24h,
        :deal_score, :demand_score, :seller_pressure, :value_score,
        :price_vs_tier_median, :price_vs_venue_median
    )
    ON CONFLICT (venue_section_id, event_id) DO UPDATE SET
        computed_at           = EXCLUDED.computed_at,
        low_ask               = EXCLUDED.low_ask,
        median_ask            = EXCLUDED.median_ask,
        high_ask              = EXCLUDED.high_ask,
        p25_ask               = EXCLUDED.p25_ask,
        p75_ask               = EXCLUDED.p75_ask,
        inventory             = EXCLUDED.inventory,
        listing_count         = EXCLUDED.listing_count,
        ticket_count          = EXCLUDED.ticket_count,
        inventory_delta_24h   = EXCLUDED.inventory_delta_24h,
        price_delta_24h       = EXCLUDED.price_delta_24h,
        price_delta_pct_24h   = EXCLUDED.price_delta_pct_24h,
        deal_score            = EXCLUDED.deal_score,
        demand_score          = EXCLUDED.demand_score,
        seller_pressure       = EXCLUDED.seller_pressure,
        value_score           = EXCLUDED.value_score,
        price_vs_tier_median  = EXCLUDED.price_vs_tier_median,
        price_vs_venue_median = EXCLUDED.price_vs_venue_median
""")


# ─────────────────────────────────────────────────────────────────────────────
# Score helpers
# ─────────────────────────────────────────────────────────────────────────────

def _f(v) -> Optional[float]:
    if v is None: return None
    try: return float(v)
    except (TypeError, ValueError): return None

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def _score_deal(median_ask: Optional[float], tier_median: Optional[float]) -> Optional[int]:
    """Higher = better deal relative to tier peers. 50 = at-market."""
    if median_ask is None or tier_median is None or tier_median == 0:
        return None
    ratio = median_ask / tier_median
    # 1.0 = at market (score 50), 0.8 = 20% below (score ~70), 1.2 = 20% above (score ~30)
    raw = 50 + (1.0 - ratio) * 100
    return int(_clamp(raw, 1, 100))

def _score_demand(listing_count: Optional[int], ticket_count: Optional[int],
                  avg_section_listings: float) -> Optional[int]:
    """Higher = more listings = more demand signal."""
    if listing_count is None or avg_section_listings == 0:
        return None
    ratio = listing_count / avg_section_listings
    raw = _clamp(ratio * 50, 1, 100)
    return int(raw)

def _score_seller_pressure(price_drops: int, price_gains: int) -> Optional[int]:
    """Higher = more downward price pressure (sellers cutting)."""
    total = price_drops + price_gains
    if total == 0:
        return None
    ratio = price_drops / total
    return int(_clamp(ratio * 100, 1, 100))

def _score_value(quality_score: int, deal_score: Optional[int]) -> Optional[int]:
    """Combines section quality with deal score — best bang for the buck."""
    if deal_score is None:
        return None
    # Weighted: 60% deal, 40% quality
    raw = 0.6 * deal_score + 0.4 * quality_score
    return int(_clamp(raw, 1, 100))


# ─────────────────────────────────────────────────────────────────────────────
# Main compute function
# ─────────────────────────────────────────────────────────────────────────────

async def compute_section_metrics(
    event_id: int,
    db: AsyncSession,
    venue_slug: str = VENUE_SLUG,
) -> list[dict]:
    """
    Compute per-section intelligence metrics for event_id at venue_slug.
    Upserts results into venue_section_metrics.
    Returns list of computed metric dicts.
    """
    # 1. Load DB venue sections (id, section_id, tier, quality_score)
    vs_rows = (await db.execute(_VENUE_SECTION_LOOKUP_SQL, {"slug": venue_slug})).fetchall()
    if not vs_rows:
        return []

    # Map: section_id → {db_id, tier, quality_score}
    vs_by_sid: dict[str, dict] = {
        r.section_id: {"db_id": r.id, "tier": r.tier, "quality_score": r.quality_score}
        for r in vs_rows
    }

    # 2. Get current section price data
    price_rows = (await db.execute(_SECTION_PRICE_SQL, {"event_id": event_id})).fetchall()

    # 3. Get 24h trend data
    trend_rows = (await db.execute(_SECTION_TREND_SQL, {"event_id": event_id})).fetchall()
    trend_by_key: dict[tuple, dict] = {
        (r.section_id, r.marketplace_id): {
            "drops": r.price_drops or 0,
            "gains": r.price_gains or 0,
            "avg_delta": _f(r.avg_delta),
        }
        for r in trend_rows
    }

    # 4. Resolve each raw section → canonical section_id + aggregate by canonical
    canonical: dict[str, dict] = {}  # canonical section_id → aggregated data
    _is_sofi = (venue_slug == VENUE_SLUG)
    _catalog = get_catalog(venue_slug)
    _catalog_lookup = _catalog["alias_lookup"] if _catalog else None

    def _resolve_sid(raw_section_id, raw_section, mp_id) -> Optional[str]:
        """Resolve a raw section string to a canonical section_id."""
        raw = raw_section or ""
        if _is_sofi:
            return normalize_section(raw_section_id, mp_id) or normalize_section(raw, mp_id)
        if _catalog_lookup is not None:
            # Use per-venue alias lookup
            norm_raw_id = _norm(raw_section_id or "")
            norm_raw    = _norm(raw)
            # Try marketplace-specific, then universal, for raw_section_id first, then raw_section
            for probe in [raw_section_id, raw]:
                if not probe: continue
                n = _norm(probe)
                sid = _catalog_lookup.get((mp_id, n)) or _catalog_lookup.get((None, n))
                if sid:
                    return sid
        # Fallback: direct section_id matching against DB sections
        return (
            normalize_section_generic(raw_section_id, vs_by_sid)
            or normalize_section_generic(raw, vs_by_sid)
        )

    for row in price_rows:
        raw = row.raw_section or ""
        mp_id = row.marketplace_id
        sid = _resolve_sid(row.raw_section_id, raw, mp_id)
        if sid is None or sid not in vs_by_sid:
            continue

        trend = trend_by_key.get((row.raw_section_id, mp_id), {})

        if sid not in canonical:
            canonical[sid] = {
                "listings": [],
                "tickets": 0,
                "price_drops": 0,
                "price_gains": 0,
                "avg_delta_sum": 0.0,
                "avg_delta_count": 0,
            }
        c = canonical[sid]
        # Collect individual listing prices (low_ask) for accurate stats after merge
        low = _f(row.low_ask)
        med = _f(row.median_ask)
        if low is not None:
            c["listings"].extend([low] * int(row.listing_count or 1))
        c["tickets"] += int(row.ticket_count or 0)
        c["price_drops"] += trend.get("drops", 0)
        c["price_gains"] += trend.get("gains", 0)
        if trend.get("avg_delta") is not None:
            c["avg_delta_sum"] += trend["avg_delta"]
            c["avg_delta_count"] += 1

    if not canonical:
        return []

    # 5. Compute per-tier median for relative scoring
    tier_prices: dict[str, list[float]] = {}
    for sid, c in canonical.items():
        tier = vs_by_sid[sid]["tier"]
        prices = c["listings"]
        if prices:
            tier_prices.setdefault(tier, []).extend(prices)

    def _median(lst: list[float]) -> Optional[float]:
        if not lst: return None
        s = sorted(lst)
        n = len(s)
        return (s[n // 2] + s[(n - 1) // 2]) / 2

    tier_medians: dict[str, Optional[float]] = {t: _median(p) for t, p in tier_prices.items()}

    all_prices: list[float] = []
    for c in canonical.values():
        all_prices.extend(c["listings"])
    venue_median = _median(all_prices)

    avg_listing_count = (
        sum(len(c["listings"]) for c in canonical.values()) / len(canonical)
        if canonical else 1.0
    )

    # 6. Build metric rows + upsert
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    results: list[dict] = []

    for sid, c in canonical.items():
        vs = vs_by_sid[sid]
        prices = c["listings"]
        if not prices:
            continue

        prices_s = sorted(prices)
        n = len(prices_s)
        low_ask = prices_s[0]
        high_ask = prices_s[-1]
        median_ask = _median(prices_s)
        p25_ask = prices_s[max(0, int(n * 0.25))]
        p75_ask = prices_s[min(n - 1, int(n * 0.75))]
        listing_count = n
        ticket_count = c["tickets"] or n

        avg_delta = (
            c["avg_delta_sum"] / c["avg_delta_count"]
            if c["avg_delta_count"] > 0 else None
        )
        price_delta_pct = (
            (avg_delta / median_ask * 100) if avg_delta is not None and median_ask else None
        )

        tier = vs["tier"]
        tier_med = tier_medians.get(tier)
        quality = vs["quality_score"]

        deal_score = _score_deal(median_ask, tier_med)
        demand_score = _score_demand(listing_count, ticket_count, avg_listing_count)
        seller_pressure = _score_seller_pressure(c["price_drops"], c["price_gains"])
        value_score = _score_value(quality, deal_score)

        price_vs_tier = (
            round((median_ask / tier_med - 1) * 100, 2)
            if tier_med and median_ask else None
        )
        price_vs_venue = (
            round((median_ask / venue_median - 1) * 100, 2)
            if venue_median and median_ask else None
        )

        row = {
            "venue_section_id": vs["db_id"],
            "event_id": event_id,
            "computed_at": now,
            "section_id": sid,
            "tier": tier,
            "quality_score": quality,
            "low_ask": round(low_ask, 2),
            "median_ask": round(median_ask, 2),
            "high_ask": round(high_ask, 2),
            "p25_ask": round(p25_ask, 2),
            "p75_ask": round(p75_ask, 2),
            "inventory": listing_count,
            "listing_count": listing_count,
            "ticket_count": ticket_count,
            "inventory_delta_24h": None,
            "price_delta_24h": round(avg_delta, 2) if avg_delta is not None else None,
            "price_delta_pct_24h": round(price_delta_pct, 2) if price_delta_pct is not None else None,
            "deal_score": deal_score,
            "demand_score": demand_score,
            "seller_pressure": seller_pressure,
            "value_score": value_score,
            "price_vs_tier_median": price_vs_tier,
            "price_vs_venue_median": price_vs_venue,
        }
        results.append(row)

        # Upsert (exclude computed-only fields not in the table)
        db_row = {k: v for k, v in row.items() if k not in ("section_id", "tier", "quality_score")}
        await db.execute(_UPSERT_METRICS_SQL, db_row)

    await db.commit()
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Intelligence read — serve computed metrics
# ─────────────────────────────────────────────────────────────────────────────

_READ_METRICS_SQL = text("""
    SELECT
        vs.section_id,
        vs.display_name,
        vs.tier,
        vs.level,
        vs.zone,
        vs.side,
        vs.quality_score,
        vs.is_premium,
        vs.future_map_key,
        vsm.low_ask,
        vsm.median_ask,
        vsm.high_ask,
        vsm.p25_ask,
        vsm.p75_ask,
        vsm.inventory,
        vsm.listing_count,
        vsm.ticket_count,
        vsm.inventory_delta_24h,
        vsm.price_delta_24h,
        vsm.price_delta_pct_24h,
        vsm.deal_score,
        vsm.demand_score,
        vsm.seller_pressure,
        vsm.value_score,
        vsm.price_vs_tier_median,
        vsm.price_vs_venue_median,
        vsm.computed_at
    FROM venue_sections vs
    JOIN venues v ON v.id = vs.venue_id
    LEFT JOIN venue_section_metrics vsm
        ON vsm.venue_section_id = vs.id AND vsm.event_id = :event_id
    WHERE v.slug = :slug
    ORDER BY vs.quality_score DESC
""")


async def get_venue_intelligence(
    event_id: int,
    db: AsyncSession,
    venue_slug: str = VENUE_SLUG,
) -> list[dict]:
    """Return section list with computed metrics for event_id. Read-only."""
    rows = (await db.execute(_READ_METRICS_SQL, {"slug": venue_slug, "event_id": event_id})).fetchall()
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(r) -> dict:
    return {
        "section_id": r.section_id,
        "display_name": r.display_name,
        "tier": r.tier,
        "level": r.level,
        "zone": r.zone,
        "side": r.side,
        "quality_score": r.quality_score,
        "is_premium": r.is_premium,
        "future_map_key": r.future_map_key,
        "metrics": {
            "low_ask": _f(r.low_ask),
            "median_ask": _f(r.median_ask),
            "high_ask": _f(r.high_ask),
            "p25_ask": _f(r.p25_ask),
            "p75_ask": _f(r.p75_ask),
            "inventory": r.inventory,
            "listing_count": r.listing_count,
            "ticket_count": r.ticket_count,
            "inventory_delta_24h": r.inventory_delta_24h,
            "price_delta_24h": _f(r.price_delta_24h),
            "price_delta_pct_24h": _f(r.price_delta_pct_24h),
            "deal_score": r.deal_score,
            "demand_score": r.demand_score,
            "seller_pressure": r.seller_pressure,
            "value_score": r.value_score,
            "price_vs_tier_median": _f(r.price_vs_tier_median),
            "price_vs_venue_median": _f(r.price_vs_venue_median),
            "computed_at": r.computed_at.isoformat() if r.computed_at else None,
        } if r.median_ask is not None else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Classifications
# ─────────────────────────────────────────────────────────────────────────────

def get_classifications(sections: list[dict]) -> dict:
    """
    Given output from get_venue_intelligence(), return classification buckets.
    All classifications are top-N ranked lists (N=5 or fewer).
    """
    with_metrics = [s for s in sections if s["metrics"] is not None]

    def top(lst, key, n=5, reverse=True):
        return sorted(
            [s for s in lst if s["metrics"].get(key) is not None],
            key=lambda s: s["metrics"][key],
            reverse=reverse,
        )[:n]

    def _compact(lst) -> list[dict]:
        return [
            {
                "section_id": s["section_id"],
                "display_name": s["display_name"],
                "tier": s["tier"],
                "quality_score": s["quality_score"],
                **{k: s["metrics"].get(k) for k in (
                    "median_ask", "deal_score", "demand_score",
                    "value_score", "seller_pressure",
                    "price_vs_tier_median", "inventory",
                )},
            }
            for s in lst
        ]

    return {
        "best_value": _compact(top(with_metrics, "value_score")),
        "highest_demand": _compact(top(with_metrics, "demand_score")),
        "fastest_price_drops": _compact(
            top(with_metrics, "seller_pressure")
        ),
        "inventory_building": _compact(
            [s for s in with_metrics
             if (s["metrics"].get("inventory_delta_24h") or 0) > 0][:5]
        ),
        "inventory_depleting": _compact(
            [s for s in with_metrics
             if (s["metrics"].get("inventory_delta_24h") or 0) < 0][:5]
        ),
        "most_active": _compact(top(with_metrics, "listing_count")),
    }
