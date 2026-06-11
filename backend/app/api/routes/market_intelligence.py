"""
market_intelligence.py — Phase 2 Market Intelligence API

All endpoints are read-only except POST /compute (writes to market_intelligence cache).

Routes:
  POST /api/intelligence/events/{id}/compute          Recompute and cache metrics
  POST /api/intelligence/compute-all                  Recompute all events
  GET  /api/intelligence/events                       All events summary (from cache)
  GET  /api/intelligence/events/{id}/hero             Hero data contract
  GET  /api/intelligence/events/{id}/market           Market intelligence panel
  GET  /api/intelligence/events/{id}/sections         Section intelligence panel
  GET  /api/intelligence/events/{id}/history          Historical graph-ready data
  GET  /api/intelligence/events/{id}/seller           Seller behavior
  GET  /api/intelligence/events/{id}/full             Full intelligence dump

Design rules:
  - Serve from cache when available (computed_at < 30 min ago)
  - Auto-recompute when cache is stale or missing
  - All windows report data_depth_hours so UI can show "based on Xh of data"
  - NULL fields mean "insufficient history" (not zero)
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Event
from app.services.intelligence_engine import compute_event, get_latest_intelligence

router = APIRouter(prefix="/intelligence", tags=["market-intelligence"])

_CACHE_TTL_MINUTES = 30  # auto-recompute if older than this


async def _get_or_compute(event_id: int, db: AsyncSession, force: bool = False) -> dict:
    """Fetch latest cached intelligence; recompute if stale or missing."""
    cached = await get_latest_intelligence(event_id, db)

    if not force and cached:
        computed_at = datetime.fromisoformat(cached["computed_at"])
        if computed_at.tzinfo is None:
            computed_at = computed_at.replace(tzinfo=timezone.utc)
        age_minutes = (datetime.now(timezone.utc) - computed_at).total_seconds() / 60
        if age_minutes < _CACHE_TTL_MINUTES:
            cached["_cache_age_minutes"] = round(age_minutes, 1)
            cached["_from_cache"] = True
            return cached

    # Compute fresh
    result = await compute_event(event_id, db)
    result["_from_cache"] = False
    result["_cache_age_minutes"] = 0
    return result


async def _require_event(event_id: int, db: AsyncSession) -> Event:
    event_q = await db.execute(select(Event).where(Event.id == event_id))
    event = event_q.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return event


# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE — trigger cache population
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/events/{event_id}/compute")
async def compute_event_intelligence(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Compute and cache full intelligence for one event.
    Forces recomputation regardless of cache freshness.

    Returns the full intelligence result.
    """
    await _require_event(event_id, db)
    result = await compute_event(event_id, db)
    return {"ok": True, "event_id": event_id, "computed_at": result["computed_at"], "result": result}


@router.post("/compute-all")
async def compute_all_events(
    db: AsyncSession = Depends(get_db),
):
    """
    Compute and cache intelligence for ALL active future events.
    Runs sequentially. Use for initial population or scheduled refresh.
    """
    now = datetime.now(timezone.utc)
    events_q = await db.execute(
        select(Event).where(Event.event_date >= now).order_by(Event.event_date)
    )
    events = events_q.scalars().all()

    results = []
    errors = []
    for event in events:
        try:
            r = await compute_event(event.id, db)
            results.append({
                "event_id": event.id,
                "title": event.title,
                "computed_at": r["computed_at"],
                "listings": r["inventory"]["total_listings"],
                "median_ask": r["price"]["median_ask"],
            })
        except Exception as exc:
            errors.append({"event_id": event.id, "title": event.title, "error": str(exc)})

    return {
        "ok": True,
        "computed": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ALL EVENTS SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events")
async def all_events_intelligence(
    db: AsyncSession = Depends(get_db),
):
    """
    Summary intelligence for all future events.
    Returns latest cached row per event; auto-computes if missing.

    Response contract for the events index:
      event_id, title, event_date, days_until_event
      signal, opportunity_score
      price: {low_ask, median_ask, high_ask}
      changes.h24: {price_delta, price_delta_pct, inventory_delta}
      inventory: {total_listings, total_tickets}
      market: {tightness, marketplace_leader, seller_aggression}
      history_hours
    """
    now = datetime.now(timezone.utc)
    events_q = await db.execute(
        select(Event).where(Event.event_date >= now).order_by(Event.event_date)
    )
    events = events_q.scalars().all()

    summary = []
    for event in events:
        intel = await _get_or_compute(event.id, db)
        summary.append({
            "event_id": event.id,
            "title": event.title,
            "event_date": event.event_date.isoformat(),
            "days_until_event": intel.get("days_until_event"),
            "signal": intel.get("signal", "unknown"),
            "opportunity_score": intel.get("market", {}).get("opportunity_score"),
            "price": intel.get("price", {}),
            "changes": {
                "h24": intel.get("changes", {}).get("h24", {}),
            },
            "inventory": intel.get("inventory", {}),
            "market": {
                "tightness": intel.get("market", {}).get("tightness"),
                "marketplace_leader": intel.get("market", {}).get("marketplace_leader"),
                "seller_aggression": intel.get("market", {}).get("seller_aggression"),
            },
            "history_hours": intel.get("history_hours"),
            "_from_cache": intel.get("_from_cache"),
        })

    return {
        "generated_at": now.isoformat(),
        "event_count": len(summary),
        "events": summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 8 — HERO DATA CONTRACT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/hero")
async def hero_data(
    event_id: int,
    refresh: bool = Query(False, description="Force recompute"),
    db: AsyncSession = Depends(get_db),
):
    """
    Hero section data contract.

    Fields:
      signal            — tightening|loosening|stable|capitulating|deepening|mixed|unknown
      price.low_ask     — current lowest ask across all marketplaces
      price.median_ask  — current median ask (p50)
      price.high_ask    — current p90 ask
      price.p25_ask     — p25 (price floor for most buyers)
      price.p75_ask     — p75 (price ceiling for most buyers)
      changes.h24.*     — 24h deltas (price + inventory)
      changes.d7.*      — 7d deltas (null if <7d history)
      inventory.*       — total_listings, total_tickets
      market.tightness  — 0-1 market tightness score
      market.seller_aggression — 0-1 (how aggressively sellers are cutting prices)
      market.opportunity_score — 0-1 composite buy-signal
      market.marketplace_leader — which marketplace has lowest ask
      market.arbitrage  — illustrative buy-low/compare-median across marketplaces
      rates.*           — reprice_rate, churn_rate, listing_survival
      price_vs_median   — current low_ask vs all-time median (ratio)
      history_context   — {hours_available, data_note}
    """
    await _require_event(event_id, db)
    intel = await _get_or_compute(event_id, db, force=refresh)

    price = intel.get("price", {})
    market = intel.get("market", {})

    # Price vs historical median (using 24h history baseline)
    price_vs_median = None
    hist_median = intel.get("changes", {}).get("h24", {}).get("price_delta")
    low = price.get("low_ask")
    median = price.get("median_ask")
    if low and median and median > 0:
        # Simple: low_ask / median — shows how accessible the market is
        price_vs_median = round(low / median, 3)

    hist_hours = intel.get("history_hours") or 0
    data_note = (
        f"Based on {hist_hours:.1f}h of listing history"
        if hist_hours >= 1
        else "Insufficient history — first computation"
    )

    return {
        "event_id": event_id,
        "generated_at": intel.get("computed_at"),
        "_from_cache": intel.get("_from_cache"),
        "_cache_age_minutes": intel.get("_cache_age_minutes"),

        # ── Hero signal ─────────────────────────────────────────────────────
        "signal": intel.get("signal", "unknown"),
        "opportunity_score": market.get("opportunity_score"),
        "days_until_event": intel.get("days_until_event"),

        # ── Price tiers ─────────────────────────────────────────────────────
        "price": price,

        # ── Changes across all windows ───────────────────────────────────────
        "changes": intel.get("changes", {}),

        # ── Inventory ───────────────────────────────────────────────────────
        "inventory": intel.get("inventory", {}),

        # ── Market character ─────────────────────────────────────────────────
        "market": {
            "tightness": market.get("tightness"),
            "seller_aggression": market.get("seller_aggression"),
            "seller_confidence": market.get("seller_confidence"),
            "capitulation_score": market.get("capitulation_score"),
            "opportunity_score": market.get("opportunity_score"),
            "marketplace_leader": market.get("marketplace_leader"),
            "velocity": market.get("velocity"),
            "arbitrage": market.get("arbitrage"),
        },

        # ── Listing survival / churn ─────────────────────────────────────────
        "rates": intel.get("rates", {}),

        # ── Context ──────────────────────────────────────────────────────────
        "price_vs_median": price_vs_median,
        "history_context": {
            "hours_available": hist_hours,
            "data_note": data_note,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 9 — MARKET INTELLIGENCE PANEL
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/market")
async def market_intelligence_panel(
    event_id: int,
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Market intelligence panel.

    Exposes:
      marketplaces[]          — per-marketplace comparison table
        .name, .listings, .tickets
        .low_ask, .median_ask, .high_ask, .p25_ask, .p75_ask
        .share_of_inventory   — fraction of total listings
        .liquidity_score      — 0-1
      price_distribution      — p10/p25/p50/p75/p90 across all marketplaces
      spreads                 — overall range, IQR, arbitrage opportunity
      trends                  — price trend, inventory trend, velocity
      inventory_movement      — new/removed in last 24h
      market_stress           — tightness + capitulation composite
    """
    await _require_event(event_id, db)
    intel = await _get_or_compute(event_id, db, force=refresh)

    price = intel.get("price", {})
    market = intel.get("market", {})
    changes = intel.get("changes", {})
    mp_metrics = intel.get("marketplace_metrics", [])

    # Price distribution summary
    low  = price.get("low_ask")
    p25  = price.get("p25_ask")
    p50  = price.get("median_ask")
    p75  = price.get("p75_ask")
    high = price.get("high_ask")  # p90

    iqr  = round(p75 - p25, 2) if p75 and p25 else None
    rng  = round(high - low, 2) if high and low else None

    # Trend direction
    pd24h = changes.get("h24", {}).get("price_delta")
    inv24h = changes.get("h24", {}).get("inventory_delta")

    price_trend = (
        "rising"  if (pd24h or 0) > 5 else
        "falling" if (pd24h or 0) < -5 else
        "stable"
    )
    inventory_trend = (
        "increasing" if (inv24h or 0) > 10 else
        "decreasing" if (inv24h or 0) < -10 else
        "stable"
    )

    # Market stress composite
    tightness = market.get("tightness") or 0
    capitulation = market.get("capitulation_score") or 0
    aggression = market.get("seller_aggression") or 0
    market_stress = round(0.4 * tightness + 0.3 * capitulation + 0.3 * aggression, 3)

    return {
        "event_id": event_id,
        "generated_at": intel.get("computed_at"),
        "_from_cache": intel.get("_from_cache"),

        # ── Per-marketplace table ────────────────────────────────────────────
        "marketplaces": mp_metrics,

        # ── Price distribution ───────────────────────────────────────────────
        "price_distribution": {
            "p10": price.get("p10_ask"),
            "p25": p25,
            "p50": p50,
            "p75": p75,
            "p90": high,
            "iqr": iqr,
            "range": rng,
        },

        # ── Spreads & arbitrage ──────────────────────────────────────────────
        "spreads": {
            "overall_range": rng,
            "iqr": iqr,
            "relative_iqr": round(iqr / p50, 3) if iqr and p50 and p50 > 0 else None,
            "arbitrage_opportunity": market.get("arbitrage"),
        },

        # ── Trends ──────────────────────────────────────────────────────────
        "trends": {
            "price_trend": price_trend,
            "inventory_trend": inventory_trend,
            "signal": intel.get("signal", "unknown"),
            "velocity_listings_per_hour": market.get("velocity"),
            "price_change_24h": pd24h,
            "price_change_24h_pct": changes.get("h24", {}).get("price_delta_pct"),
            "inventory_change_24h": inv24h,
        },

        # ── Inventory movement ───────────────────────────────────────────────
        "inventory_movement": {
            "current_listings": intel.get("inventory", {}).get("total_listings"),
            "current_tickets":  intel.get("inventory", {}).get("total_tickets"),
            "new_24h":     intel.get("seller_behavior", {}).get("new_24h"),
            "removed_24h": intel.get("seller_behavior", {}).get("removed_24h"),
            "net_change_24h": inv24h,
        },

        # ── Market stress ────────────────────────────────────────────────────
        "market_stress": {
            "composite_score": market_stress,
            "tightness": market.get("tightness"),
            "capitulation": market.get("capitulation_score"),
            "seller_aggression": market.get("seller_aggression"),
            "note": "0=loose/calm, 1=tight/stressed",
        },

        # ── Market depth & liquidity ─────────────────────────────────────────
        "market_depth": {
            "depth_score": market.get("depth"),
            "note": "IQR/median ratio — higher = wider spread relative to median",
        },

        "history_context": {
            "hours_available": intel.get("history_hours"),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 10 — SECTION INTELLIGENCE PANEL
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/sections")
async def section_intelligence(
    event_id: int,
    limit: int = Query(30, ge=5, le=60),
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Section intelligence panel.

    Returns:
      sections[]              — all sections sorted by listings desc
        .section_id, .display_name, .tier (from venue_sections if available)
        .listings, .tickets
        .low_ask, .median_ask, .high_ask
        .price_range          — high - low for this section
        .value_score          — how cheap relative to event median (higher = better value)
        .activity_score       — listings count / total listings (concentration)
      leaderboards:
        .biggest_drops[]      — sections with biggest price drop vs 24h ago
        .fastest_absorption[] — sections with most disappeared listings
        .best_value[]         — sections with lowest median vs event median
        .highest_activity[]   — sections with most listings
    """
    await _require_event(event_id, db)
    intel = await _get_or_compute(event_id, db, force=refresh)

    sections = intel.get("section_metrics", [])
    event_median = intel.get("price", {}).get("median_ask") or 1
    total_listings = max(intel.get("inventory", {}).get("total_listings") or 1, 1)

    # Enrich with venue_sections display info
    vs_rows = (await db.execute(text("""
        SELECT section_id, display_name, tier, quality_score
        FROM venue_sections
        WHERE venue_id = (SELECT venue_id FROM events WHERE id = :eid)
    """), {"eid": event_id})).fetchall()
    vs_map = {r[0]: {"display_name": r[1], "tier": r[2], "quality_score": float(r[3]) if r[3] else None}
              for r in vs_rows}

    enriched = []
    for sec in sections[:limit]:
        sec_id = sec.get("section_id") or sec.get("display_name")
        vs = vs_map.get(sec_id, {})
        median = sec.get("median_ask") or event_median
        low    = sec.get("low_ask")
        high   = sec.get("high_ask")
        listings = sec.get("listings", 0)

        price_range = round(high - low, 2) if high and low else None
        # Value score: how far below event median is this section's median?
        value_score = round(max(0, 1 - median / event_median), 3) if event_median > 0 else None
        # Activity score: share of total listings
        activity_score = round(listings / total_listings, 4) if total_listings > 0 else None

        enriched.append({
            "section_id": sec_id,
            "display_name": vs.get("display_name") or sec.get("display_name") or sec_id,
            "tier": vs.get("tier"),
            "quality_score": vs.get("quality_score"),
            "listings": listings,
            "tickets": sec.get("tickets", 0),
            "low_ask": low,
            "median_ask": median,
            "high_ask": high,
            "price_range": price_range,
            "value_score": value_score,
            "activity_score": activity_score,
        })

    # Leaderboards
    def _top(lst, key, n=5, reverse=True):
        filtered = [s for s in lst if s.get(key) is not None]
        return sorted(filtered, key=lambda x: x[key], reverse=reverse)[:n]

    leaderboards = {
        "best_value": _top(enriched, "value_score", reverse=True),
        "highest_activity": _top(enriched, "listings", reverse=True),
        "lowest_ask": _top(enriched, "low_ask", reverse=False),
        "largest_range": _top(enriched, "price_range", reverse=True),
    }

    return {
        "event_id": event_id,
        "generated_at": intel.get("computed_at"),
        "_from_cache": intel.get("_from_cache"),
        "event_median_ask": event_median,
        "total_sections": len(enriched),
        "sections": enriched,
        "leaderboards": leaderboards,
        "history_context": {"hours_available": intel.get("history_hours")},
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 11 — HISTORICAL GRAPH DATA
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/history")
async def historical_graph_data(
    event_id: int,
    window: str = Query("24h", regex="^(24h|7d|14d|30d|all)$"),
    metric: str = Query("price", regex="^(price|inventory|marketplace|seller)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Historical graph-ready data for one event.

    Parameters:
      window  — 24h | 7d | 14d | 30d | all
      metric  — price | inventory | marketplace | seller

    For 'price':
      Returns time-bucketed series of {ts, low_ask, median_ask, high_ask, listings, tickets}
      Bucket size: 24h=1h, 7d=6h, 14d=12h, 30d=1d, all=auto

    For 'inventory':
      Returns {ts, total_listings, total_tickets, new_listings, disappeared_listings}
      from poll_runs joined with listing_snapshots

    For 'marketplace':
      Returns {ts, by_marketplace: {name: {listings, median_ask}}} per bucket

    For 'seller':
      Returns {ts, new_listings, disappeared_listings, repriced, price_drops, price_gains}
      from poll_runs

    All series sorted ascending by ts (oldest first, ready for charting).
    Includes data_depth_hours so UI can show "based on Xh of data" caveat.
    """
    await _require_event(event_id, db)
    now = datetime.now(timezone.utc)

    # Determine window and bucket size
    window_map = {
        "24h":  (timedelta(hours=24),  "hour"),
        "7d":   (timedelta(days=7),    "6 hours"),
        "14d":  (timedelta(days=14),   "12 hours"),
        "30d":  (timedelta(days=30),   "day"),
        "all":  (None,                 "6 hours"),  # will use actual earliest
    }
    td, bucket_size = window_map[window]
    window_start = (now - td) if td else None

    # Find actual data range
    depth_row = (await db.execute(text("""
        SELECT MIN(snapshot_at), MAX(snapshot_at), COUNT(*)
        FROM listing_snapshots WHERE event_id = :eid
    """), {"eid": event_id})).fetchone()
    actual_oldest = depth_row[0]
    actual_newest = depth_row[1]
    snap_count = depth_row[2] or 0

    if not actual_oldest:
        return {
            "event_id": event_id,
            "window": window,
            "metric": metric,
            "data_depth_hours": 0,
            "bucket_size": bucket_size,
            "series": [],
            "note": "No listing snapshot data available yet",
        }

    effective_start = max(window_start, actual_oldest) if window_start else actual_oldest
    data_hours = (actual_newest - effective_start).total_seconds() / 3600 if actual_newest else 0

    # Auto-adjust bucket for 'all' with limited data
    if window == "all" and data_hours < 24:
        bucket_size = "hour"
    elif window == "all" and data_hours < 72:
        bucket_size = "3 hours"

    series = []

    if metric == "price":
        rows = (await db.execute(text("""
            SELECT
                DATE_TRUNC(:bkt, snapshot_at)                               AS bucket,
                MIN(price)                                                   AS low_ask,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)          AS median_ask,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY price)          AS high_ask,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price)         AS p25_ask,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price)         AS p75_ask,
                COUNT(DISTINCT listing_id)                                   AS listings,
                SUM(quantity)                                                AS tickets
            FROM listing_snapshots
            WHERE event_id = :eid
              AND snapshot_at >= CAST(:win_start AS timestamp)
              AND price > 0
            GROUP BY bucket
            ORDER BY bucket ASC
        """), {"eid": event_id, "bkt": bucket_size, "win_start": effective_start})).fetchall()

        for r in rows:
            series.append({
                "ts": r[0].isoformat() if r[0] else None,
                "low_ask":    round(float(r[1]), 2) if r[1] else None,
                "median_ask": round(float(r[2]), 2) if r[2] else None,
                "high_ask":   round(float(r[3]), 2) if r[3] else None,
                "p25_ask":    round(float(r[4]), 2) if r[4] else None,
                "p75_ask":    round(float(r[5]), 2) if r[5] else None,
                "listings":   int(r[6] or 0),
                "tickets":    int(r[7] or 0),
            })

    elif metric == "inventory":
        # From poll_runs (includes new/disappeared breakdown)
        rows = (await db.execute(text("""
            SELECT
                DATE_TRUNC(:bkt, pr.started_at)           AS bucket,
                SUM(pr.listings_found)                     AS total_found,
                SUM(pr.new_listings)                       AS new_listings,
                SUM(pr.disappeared_listings)               AS disappeared,
                COUNT(pr.id)                               AS poll_count
            FROM poll_runs pr
            JOIN tracked_events te ON te.id = pr.tracked_event_id
            WHERE te.event_id = :eid
              AND pr.status = 'success'
              AND pr.started_at >= CAST(:win_start AS timestamp)
            GROUP BY bucket
            ORDER BY bucket ASC
        """), {"eid": event_id, "bkt": bucket_size, "win_start": effective_start})).fetchall()

        for r in rows:
            series.append({
                "ts": r[0].isoformat() if r[0] else None,
                "total_listings_found": int(r[1] or 0),
                "new_listings": int(r[2] or 0),
                "disappeared_listings": int(r[3] or 0),
                "poll_count": int(r[4] or 0),
            })

    elif metric == "marketplace":
        rows = (await db.execute(text("""
            SELECT
                DATE_TRUNC(:bkt, ls.snapshot_at)                              AS bucket,
                m.slug                                                         AS marketplace,
                COUNT(DISTINCT ls.listing_id)                                 AS listings,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ls.price)        AS median_ask,
                MIN(ls.price)                                                  AS low_ask
            FROM listing_snapshots ls
            JOIN marketplaces m ON m.id = ls.marketplace_id
            WHERE ls.event_id = :eid
              AND ls.snapshot_at >= CAST(:win_start AS timestamp)
              AND ls.price > 0
            GROUP BY bucket, m.slug
            ORDER BY bucket ASC, listings DESC
        """), {"eid": event_id, "bkt": bucket_size, "win_start": effective_start})).fetchall()

        # Group into {ts → {marketplace → data}}
        from collections import defaultdict
        bucket_map: dict[str, dict] = defaultdict(dict)
        for r in rows:
            ts = r[0].isoformat() if r[0] else ""
            bucket_map[ts][r[1]] = {
                "listings": int(r[2] or 0),
                "median_ask": round(float(r[3]), 2) if r[3] else None,
                "low_ask": round(float(r[4]), 2) if r[4] else None,
            }
        series = [{"ts": ts, "by_marketplace": data}
                  for ts, data in sorted(bucket_map.items())]

    elif metric == "seller":
        rows = (await db.execute(text("""
            SELECT
                DATE_TRUNC(:bkt, pr.started_at)  AS bucket,
                SUM(pr.new_listings)              AS new_listings,
                SUM(pr.disappeared_listings)      AS disappeared
            FROM poll_runs pr
            JOIN tracked_events te ON te.id = pr.tracked_event_id
            WHERE te.event_id = :eid
              AND pr.status = 'success'
              AND pr.started_at >= CAST(:win_start AS timestamp)
            GROUP BY bucket
            ORDER BY bucket ASC
        """), {"eid": event_id, "bkt": bucket_size, "win_start": effective_start})).fetchall()

        for r in rows:
            series.append({
                "ts": r[0].isoformat() if r[0] else None,
                "new_listings": int(r[1] or 0),
                "disappeared_listings": int(r[2] or 0),
                "net_change": int((r[1] or 0) - (r[2] or 0)),
            })

    return {
        "event_id": event_id,
        "window": window,
        "metric": metric,
        "bucket_size": bucket_size,
        "window_start": effective_start.isoformat(),
        "window_end": actual_newest.isoformat() if actual_newest else None,
        "data_depth_hours": round(data_hours, 1),
        "total_snapshots": snap_count,
        "point_count": len(series),
        "series": series,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4/6 — SELLER BEHAVIOR
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/seller")
async def seller_behavior(
    event_id: int,
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Seller behavior intelligence.

    Exposes:
      new_listings_24h         — new listings posted in last 24h
      removed_listings_24h     — listings removed in last 24h
      repriced_24h             — listings that changed price in last 24h
      price_drops_24h          — repriced down
      price_gains_24h          — repriced up
      median_reprice_delta     — median $ change (negative = avg cut)
      seller_aggression        — 0-1: how aggressively sellers are cutting
      seller_confidence        — 0-1: how much sellers are raising
      capitulation_score       — 0-1: combined capitulation signal
      relist_pressure          — 0-1: relisting activity
      reprice_rate             — fraction of active listings repriced in 24h
      churn_rate               — (new+removed) / total
      listing_survival         — fraction of 12h-ago listings still active now
      per_marketplace          — breakdown by marketplace
      largest_price_drops[]    — top 5 individual listing price cuts
      largest_price_gains[]    — top 5 individual listing price increases
      aggressive_sellers[]     — sections with most price drops
    """
    await _require_event(event_id, db)
    intel = await _get_or_compute(event_id, db, force=refresh)

    sb = intel.get("seller_behavior", {})
    market = intel.get("market", {})
    rates  = intel.get("rates", {})

    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)

    # Per-marketplace seller behavior (new + disappeared from poll_runs)
    mp_sb = (await db.execute(text("""
        SELECT m.slug, SUM(pr.new_listings), SUM(pr.disappeared_listings),
               COUNT(pr.id) as polls
        FROM poll_runs pr
        JOIN tracked_events te ON te.id = pr.tracked_event_id
        JOIN marketplaces m ON m.id = te.marketplace_id
        WHERE te.event_id = :eid
          AND pr.status = 'success'
          AND pr.started_at >= :since
        GROUP BY m.slug
        ORDER BY SUM(pr.new_listings) DESC
    """), {"eid": event_id, "since": since_24h})).fetchall()

    mp_behavior = []
    for r in mp_sb:
        mp_behavior.append({
            "marketplace": r[0],
            "new_24h": int(r[1] or 0),
            "removed_24h": int(r[2] or 0),
            "net_24h": int((r[1] or 0) - (r[2] or 0)),
            "poll_count_24h": int(r[3] or 0),
        })

    # Top repriced listings (biggest cuts and raises)
    top_changes = (await db.execute(text("""
        WITH changes AS (
            SELECT
                ls.listing_id,
                m.slug AS marketplace,
                l.section,
                l.row,
                l.price AS current_price,
                MIN(ls.price) OVER (PARTITION BY ls.listing_id) AS min_price_seen,
                MAX(ls.price) OVER (PARTITION BY ls.listing_id) AS max_price_seen,
                FIRST_VALUE(ls.price) OVER (
                    PARTITION BY ls.listing_id ORDER BY ls.snapshot_at ASC
                ) AS first_price
            FROM listing_snapshots ls
            JOIN listings l ON l.id = ls.listing_id
            JOIN marketplaces m ON m.id = ls.marketplace_id
            WHERE ls.event_id = :eid
              AND ls.snapshot_at >= :since
        )
        SELECT DISTINCT
            listing_id, marketplace, section, row,
            current_price, first_price,
            (current_price - first_price) AS delta
        FROM changes
        WHERE first_price IS NOT NULL AND first_price <> current_price
        ORDER BY delta ASC
        LIMIT 20
    """), {"eid": event_id, "since": since_24h})).fetchall()

    largest_drops = []
    largest_gains = []
    for r in top_changes:
        lid, mp, section, row, curr, first, delta = r
        entry = {
            "listing_id": lid,
            "marketplace": mp,
            "section": section,
            "row": row,
            "current_price": round(float(curr), 2) if curr else None,
            "first_price_24h": round(float(first), 2) if first else None,
            "delta": round(float(delta), 2) if delta else None,
            "delta_pct": round(float(delta) / float(first) * 100, 1) if first and float(first) != 0 else None,
        }
        if delta and float(delta) < 0:
            largest_drops.append(entry)
        elif delta and float(delta) > 0:
            largest_gains.append(entry)

    # Sections with most price drops (aggressive sections)
    agg_sections = (await db.execute(text("""
        WITH changes AS (
            SELECT
                l.section_id,
                l.section,
                ls.listing_id,
                ls.price,
                LAG(ls.price) OVER (PARTITION BY ls.listing_id ORDER BY ls.snapshot_at) AS prev_price
            FROM listing_snapshots ls
            JOIN listings l ON l.id = ls.listing_id
            WHERE ls.event_id = :eid
              AND ls.snapshot_at >= :since
        )
        SELECT section_id, section,
               COUNT(*) FILTER (WHERE prev_price IS NOT NULL AND price < prev_price) AS drops,
               COUNT(*) FILTER (WHERE prev_price IS NOT NULL AND price > prev_price) AS gains
        FROM changes
        GROUP BY section_id, section
        HAVING COUNT(*) FILTER (WHERE prev_price IS NOT NULL AND price < prev_price) > 0
        ORDER BY drops DESC
        LIMIT 10
    """), {"eid": event_id, "since": since_24h})).fetchall()

    aggressive_sections = []
    for r in agg_sections:
        aggressive_sections.append({
            "section_id": r[0],
            "section": r[1],
            "price_drops_24h": int(r[2] or 0),
            "price_gains_24h": int(r[3] or 0),
            "aggression_ratio": round(int(r[2] or 0) / max(int(r[2] or 0) + int(r[3] or 0), 1), 3),
        })

    return {
        "event_id": event_id,
        "generated_at": intel.get("computed_at"),
        "_from_cache": intel.get("_from_cache"),

        # ── Summary ──────────────────────────────────────────────────────────
        "new_listings_24h":     sb.get("new_24h", 0),
        "removed_listings_24h": sb.get("removed_24h", 0),
        "repriced_24h":         sb.get("repriced_24h", 0),
        "price_drops_24h":      sb.get("price_drops_24h", 0),
        "price_gains_24h":      sb.get("price_gains_24h", 0),
        "median_reprice_delta": sb.get("median_reprice_delta"),

        # ── Scores ───────────────────────────────────────────────────────────
        "seller_aggression":   market.get("seller_aggression"),
        "seller_confidence":   market.get("seller_confidence"),
        "capitulation_score":  market.get("capitulation_score"),
        "relist_pressure":     None,  # requires multi-cycle history

        # ── Rates ────────────────────────────────────────────────────────────
        "reprice_rate":      rates.get("reprice_rate"),
        "churn_rate":        rates.get("churn_rate"),
        "listing_survival":  rates.get("listing_survival"),

        # ── Per-marketplace breakdown ─────────────────────────────────────────
        "by_marketplace": mp_behavior,

        # ── Top movers ────────────────────────────────────────────────────────
        "largest_price_drops": largest_drops[:5],
        "largest_price_gains": largest_gains[:5],

        # ── Aggressive sections ───────────────────────────────────────────────
        "aggressive_sections": aggressive_sections,

        "history_context": {"hours_available": intel.get("history_hours")},
    }


# ─────────────────────────────────────────────────────────────────────────────
# FULL DUMP (development / debugging)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/full")
async def full_intelligence_dump(
    event_id: int,
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Full intelligence dump for one event.
    Returns everything computed by the intelligence engine.
    Intended for development, debugging, and UI prototyping.
    """
    await _require_event(event_id, db)
    return await _get_or_compute(event_id, db, force=refresh)
