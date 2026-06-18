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
from app.services.listing_lifecycle import compute_lifecycle
from app.services.buy_window import compute_buy_signal
from app.services.marketplace_health import get_coverage_audit

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

    event_ids = [e.id for e in events]

    # ── Archive depth: batch-query event_price_history_agg for true oldest date ─
    # history_hours stored in EventIntelligence reflects listing_snapshots only (live window).
    # Archive aggregates can extend the range by weeks. Surface the true combined depth
    # so the dashboard chip shows actual history depth, not just the live window.
    archive_oldest_by_event: dict[int, float | None] = {}
    if event_ids:
        ids_literal_tmp = ", ".join(str(i) for i in event_ids)
        agg_rows = (await db.execute(text(f"""
            SELECT railway_event_id, MIN(bucket_ts)
            FROM event_price_history_agg
            WHERE railway_event_id IN ({ids_literal_tmp})
            GROUP BY railway_event_id
        """))).fetchall()
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        for agg_eid, agg_old in agg_rows:
            if agg_old:
                archive_oldest_by_event[agg_eid] = (now_utc - agg_old).total_seconds() / 3600

    # ── First-tracked median: one batch query for all events ──────────────────
    # Fetches PERCENTILE_CONT(0.5) of price at the earliest snapshot window
    # (first hour of data) from listing_snapshots only. This is the "tracking
    # start" baseline used to compute long-run change %.
    first_tracked_medians: dict[int, float | None] = {}
    if event_ids:
        # Build a literal IN list — safe because event_ids are ints from our own DB
        ids_literal = ", ".join(str(i) for i in event_ids)
        ft_rows = (await db.execute(text(f"""
            WITH first_windows AS (
                SELECT event_id, MIN(snapshot_at) AS first_snap
                FROM listing_snapshots
                WHERE event_id IN ({ids_literal})
                GROUP BY event_id
            )
            SELECT ls.event_id,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ls.price) AS first_median
            FROM listing_snapshots ls
            JOIN first_windows fw
              ON fw.event_id = ls.event_id
             AND ls.snapshot_at BETWEEN fw.first_snap AND fw.first_snap + INTERVAL '1 hour'
            GROUP BY ls.event_id
        """))).fetchall()
        for row in ft_rows:
            first_tracked_medians[row[0]] = float(row[1]) if row[1] else None

    summary = []
    for event in events:
        intel = await _get_or_compute(event.id, db)
        current_median = (intel.get("price") or {}).get("median_ask")
        first_median = first_tracked_medians.get(event.id)
        first_tracked_change: dict | None = None
        if first_median and current_median and first_median > 0:
            delta_pct = round((current_median - first_median) / first_median * 100, 1)
            first_tracked_change = {
                "first_median": round(first_median, 2),
                "price_delta_pct": delta_pct,
            }
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
                "first_tracked": first_tracked_change,
            },
            "inventory": intel.get("inventory", {}),
            "market": {
                "tightness": intel.get("market", {}).get("tightness"),
                "marketplace_leader": intel.get("market", {}).get("marketplace_leader"),
                "seller_aggression": intel.get("market", {}).get("seller_aggression"),
            },
            "history_hours": max(
                intel.get("history_hours") or 0,
                archive_oldest_by_event.get(event.id) or 0,
            ) or None,
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
    now_sql = now.replace(tzinfo=None)  # naive UTC for TIMESTAMP WITHOUT TIME ZONE SQL params

    # Determine window and bucket size
    window_map = {
        "24h":  (timedelta(hours=24),  "1h",   "hour"),
        "7d":   (timedelta(days=7),    "6h",   "6 hours"),
        "14d":  (timedelta(days=14),   "12h",  "12 hours"),
        "30d":  (timedelta(days=30),   "1d",   "day"),
        "all":  (None,                 "6h",   "6 hours"),
    }
    td, agg_bucket_label, bucket_size = window_map[window]
    window_start = (now_sql - td) if td else None

    # ── Find live data range ──────────────────────────────────────────────────
    depth_row = (await db.execute(text("""
        SELECT MIN(snapshot_at), MAX(snapshot_at), COUNT(*)
        FROM listing_snapshots WHERE event_id = :eid
    """), {"eid": event_id})).fetchone()
    live_oldest  = depth_row[0]
    live_newest  = depth_row[1]
    snap_count   = depth_row[2] or 0

    # ── Find archive aggregate range ─────────────────────────────────────────
    agg_row = (await db.execute(text("""
        SELECT MIN(bucket_ts), MAX(bucket_ts), COUNT(*)
        FROM event_price_history_agg
        WHERE railway_event_id = :eid AND bucket_size = :bkt
    """), {"eid": event_id, "bkt": agg_bucket_label})).fetchone()
    agg_oldest   = agg_row[0] if agg_row else None
    agg_newest   = agg_row[1] if agg_row else None
    agg_count    = (agg_row[2] or 0) if agg_row else 0

    # Determine combined range
    candidates_oldest = [x for x in [live_oldest, agg_oldest] if x is not None]
    candidates_newest = [x for x in [live_newest, agg_newest] if x is not None]
    actual_oldest = min(candidates_oldest) if candidates_oldest else None
    actual_newest = max(candidates_newest) if candidates_newest else None

    if not actual_oldest:
        return {
            "event_id": event_id,
            "window": window,
            "metric": metric,
            "data_depth_hours": 0,
            "bucket_size": bucket_size,
            "series": [],
            "source": "none",
            "note": "No listing snapshot data available yet",
        }

    effective_start = max(window_start, actual_oldest) if window_start else actual_oldest
    data_hours = (actual_newest - effective_start).total_seconds() / 3600 if actual_newest else 0

    # Determine data source label
    has_live    = live_oldest is not None
    has_archive = agg_oldest is not None and agg_count > 0
    if has_live and has_archive:
        data_source = "combined"
    elif has_archive:
        data_source = "archive_aggregate"
    else:
        data_source = "live"

    # Auto-adjust bucket for 'all' with limited data
    if window == "all" and data_hours < 24:
        bucket_size = "hour"
        agg_bucket_label = "1h"
    elif window == "all" and data_hours < 72:
        bucket_size = "3 hours"
        agg_bucket_label = "6h"  # closest available

    series = []

    # Build bucket expression: DATE_TRUNC only accepts single-unit strings.
    # For multi-hour buckets use epoch-floor arithmetic instead.
    _MULTI_HOUR_SECONDS = {"3 hours": 10800, "6 hours": 21600, "12 hours": 43200}

    def _bucket_expr(col: str, bkt: str) -> str:
        if bkt in _MULTI_HOUR_SECONDS:
            secs = _MULTI_HOUR_SECONDS[bkt]
            return f"to_timestamp(floor(extract(epoch from {col}) / {secs}) * {secs})"
        return f"DATE_TRUNC('{bkt}', {col})"

    if metric == "price":
        # ── Archive aggregate rows (pre-rebuild history) ──────────────────────
        agg_series: dict = {}
        if has_archive:
            agg_rows = (await db.execute(text("""
                SELECT bucket_ts, low_ask, median_ask, high_ask, p25_ask, p75_ask,
                       listing_count, ticket_count
                FROM event_price_history_agg
                WHERE railway_event_id = :eid
                  AND bucket_size = :bkt
                  AND bucket_ts >= CAST(:win_start AS timestamp)
                ORDER BY bucket_ts ASC
            """), {"eid": event_id, "bkt": agg_bucket_label,
                   "win_start": effective_start})).fetchall()
            for r in agg_rows:
                ts_key = r[0].isoformat()
                agg_series[ts_key] = {
                    "ts": ts_key, "_source": "archive",
                    "low_ask":    round(float(r[1]), 2) if r[1] else None,
                    "median_ask": round(float(r[2]), 2) if r[2] else None,
                    "high_ask":   round(float(r[3]), 2) if r[3] else None,
                    "p25_ask":    round(float(r[4]), 2) if r[4] else None,
                    "p75_ask":    round(float(r[5]), 2) if r[5] else None,
                    "listings":   int(r[6] or 0),
                    "tickets":    int(r[7] or 0),
                }

        # ── Live listing_snapshots rows ───────────────────────────────────────
        live_start = max(window_start, live_oldest) if (window_start and live_oldest) else (live_oldest or window_start)
        if has_live and live_start is not None:
            bkt_sql = _bucket_expr("snapshot_at", bucket_size)
            live_rows = (await db.execute(text(f"""
                SELECT
                    {bkt_sql}                                                        AS bucket,
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
            """), {"eid": event_id, "win_start": live_start})).fetchall()
            for r in live_rows:
                ts_key = r[0].isoformat() if r[0] else None
                if ts_key:
                    # Live data overrides archive for same bucket
                    agg_series[ts_key] = {
                        "ts": ts_key, "_source": "live",
                        "low_ask":    round(float(r[1]), 2) if r[1] else None,
                        "median_ask": round(float(r[2]), 2) if r[2] else None,
                        "high_ask":   round(float(r[3]), 2) if r[3] else None,
                        "p25_ask":    round(float(r[4]), 2) if r[4] else None,
                        "p75_ask":    round(float(r[5]), 2) if r[5] else None,
                        "listings":   int(r[6] or 0),
                        "tickets":    int(r[7] or 0),
                    }

        series = sorted(agg_series.values(), key=lambda x: x["ts"])

    elif metric == "inventory":
        bkt_sql = _bucket_expr("pr.started_at", bucket_size)
        # From poll_runs (includes new/disappeared breakdown)
        rows = (await db.execute(text(f"""
            SELECT
                {bkt_sql}                                  AS bucket,
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
        """), {"eid": event_id, "win_start": effective_start})).fetchall()

        for r in rows:
            series.append({
                "ts": r[0].isoformat() if r[0] else None,
                "total_listings_found": int(r[1] or 0),
                "new_listings": int(r[2] or 0),
                "disappeared_listings": int(r[3] or 0),
                "poll_count": int(r[4] or 0),
            })

    elif metric == "marketplace":
        bkt_sql = _bucket_expr("ls.snapshot_at", bucket_size)
        rows = (await db.execute(text(f"""
            SELECT
                {bkt_sql}                                                      AS bucket,
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
        """), {"eid": event_id, "win_start": effective_start})).fetchall()

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
        bkt_sql = _bucket_expr("pr.started_at", bucket_size)
        rows = (await db.execute(text(f"""
            SELECT
                {bkt_sql}                 AS bucket,
                SUM(pr.new_listings)      AS new_listings,
                SUM(pr.disappeared_listings) AS disappeared
            FROM poll_runs pr
            JOIN tracked_events te ON te.id = pr.tracked_event_id
            WHERE te.event_id = :eid
              AND pr.status = 'success'
              AND pr.started_at >= CAST(:win_start AS timestamp)
            GROUP BY bucket
            ORDER BY bucket ASC
        """), {"eid": event_id, "win_start": effective_start})).fetchall()

        for r in rows:
            series.append({
                "ts": r[0].isoformat() if r[0] else None,
                "new_listings": int(r[1] or 0),
                "disappeared_listings": int(r[2] or 0),
                "net_change": int((r[1] or 0) - (r[2] or 0)),
            })

    # Compute true data depth from combined oldest
    true_oldest = min(x for x in [
        actual_oldest,
        (agg_oldest if has_archive else None),
    ] if x is not None) if actual_oldest or (has_archive and agg_oldest) else effective_start
    true_depth_hours = (actual_newest - true_oldest).total_seconds() / 3600 if (actual_newest and true_oldest) else data_hours
    true_depth_days  = round(true_depth_hours / 24, 1)

    return {
        "event_id": event_id,
        "window": window,
        "metric": metric,
        "bucket_size": bucket_size,
        "window_start": effective_start.isoformat(),
        "window_end": actual_newest.isoformat() if actual_newest else None,
        "data_depth_hours": round(data_hours, 1),
        "data_depth_days":  true_depth_days,
        "total_snapshots": snap_count,
        "archive_bucket_count": agg_count if has_archive else 0,
        "point_count": len(series),
        "source": data_source,           # "live" | "archive_aggregate" | "combined" | "none"
        "oldest_timestamp": true_oldest.isoformat() if true_oldest else None,
        "newest_timestamp": actual_newest.isoformat() if actual_newest else None,
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
    since_24h = (now - timedelta(hours=24)).replace(tzinfo=None)  # naive for TIMESTAMP col

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


# ─────────────────────────────────────────────────────────────────────────────
# INTELLIGENCE PHASE 1A — HISTORICAL CURVE + ABSORPTION
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/event/{event_id}")
async def historical_intelligence(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Historical intelligence for a completed or in-flight event.

    Queries listing_snapshots to build a normalized price/inventory curve
    (one point per hour, sorted oldest→newest), computes key timing markers,
    runs absorption classification on consecutive transitions, and optionally
    cross-references the Ariana Grande aggregate profile when the artist matches.

    Response:
      event_id, title, event_date, is_completed
      tracking_start_hours_before   — how far before event we started collecting
      data_points                   — hourly buckets available
      curve[]                       — {hours_to_event, floor_price, inventory}
      lowest_floor, lowest_floor_hours_to_event
      inventory_peak, inventory_peak_hours_to_event
      inventory_collapse_hours_to_event  — first point after peak where inv < 50% peak (null if not yet)
      marketplace_analysis           — per-mp {min_floor, max_floor, max_inv, floor_trend_pct}
      absorption                     — {transitions[], summary{}, dominant}
      artist_profile                 — Ariana aggregate context (null if not applicable)
    """
    # ── Load event ────────────────────────────────────────────────────────────
    event_row = (await db.execute(
        select(Event).where(Event.id == event_id)
    )).scalar_one_or_none()
    if not event_row:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    now = datetime.now(timezone.utc)
    event_dt = event_row.event_date.replace(tzinfo=timezone.utc) if event_row.event_date.tzinfo is None else event_row.event_date
    is_completed = event_dt < now

    # ── Pull hourly price/inventory from listing_snapshots ────────────────────
    rows = (await db.execute(text("""
        SELECT
            DATE_TRUNC('hour', ls.snapshot_at)               AS bucket,
            MIN(ls.price)                                     AS floor_price,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ls.price) AS median_price,
            COUNT(DISTINCT ls.listing_id)                    AS listings,
            SUM(ls.quantity)                                 AS tickets,
            m.slug                                           AS marketplace
        FROM listing_snapshots ls
        JOIN marketplaces m ON m.id = ls.marketplace_id
        WHERE ls.event_id = :eid
          AND ls.price > 0
        GROUP BY DATE_TRUNC('hour', ls.snapshot_at), m.slug
        ORDER BY bucket ASC
    """), {"eid": event_id})).fetchall()

    if not rows:
        return {
            "event_id": event_id,
            "title": event_row.title,
            "event_date": event_dt.isoformat(),
            "is_completed": is_completed,
            "data_points": 0,
            "note": "No listing snapshot data available",
        }

    # ── Aggregate across marketplaces per hour ────────────────────────────────
    from collections import defaultdict

    hour_data: dict = defaultdict(lambda: {"prices": [], "inventory": 0, "mp": defaultdict(lambda: {"prices": [], "inv": 0})})
    for r in rows:
        bucket, floor, median, listings, tickets, mp = r
        hour_data[bucket]["prices"].append(float(floor))
        hour_data[bucket]["inventory"] += int(tickets or listings or 0)
        hour_data[bucket]["mp"][mp]["prices"].append(float(floor))
        hour_data[bucket]["mp"][mp]["inv"] += int(tickets or listings or 0)

    def _hours_to(bucket_dt, ev_dt):
        b = bucket_dt.replace(tzinfo=timezone.utc) if bucket_dt.tzinfo is None else bucket_dt
        return (ev_dt - b).total_seconds() / 3600

    # Build curve: only include points before event
    curve = sorted([
        {
            "hours_to_event": round(_hours_to(bucket, event_dt), 2),
            "floor_price": min(d["prices"]),
            "inventory": d["inventory"],
        }
        for bucket, d in hour_data.items()
        if _hours_to(bucket, event_dt) >= 0
    ], key=lambda x: x["hours_to_event"], reverse=True)  # oldest first (highest hours)

    if not curve:
        return {
            "event_id": event_id,
            "title": event_row.title,
            "event_date": event_dt.isoformat(),
            "is_completed": is_completed,
            "data_points": 0,
            "note": "No pre-event snapshot data",
        }

    # ── Key timing markers ────────────────────────────────────────────────────
    min_floor_row = min(curve, key=lambda x: x["floor_price"])
    max_inv_row   = max(curve, key=lambda x: x["inventory"])
    peak_idx      = curve.index(max_inv_row)

    # Inventory collapse: first point AFTER peak where inv < 50% of peak
    collapse_row = None
    for pt in curve[peak_idx:]:
        if pt["inventory"] < max_inv_row["inventory"] * 0.5:
            collapse_row = pt
            break

    # ── Marketplace-level analysis ────────────────────────────────────────────
    mp_analysis: dict = {}
    for bucket, d in hour_data.items():
        hrs = _hours_to(bucket, event_dt)
        if hrs < 0:
            continue
        for mp, mpd in d["mp"].items():
            if not mpd["prices"]:
                continue
            floor = min(mpd["prices"])
            inv   = mpd["inv"]
            if mp not in mp_analysis:
                mp_analysis[mp] = {"floors": [], "invs": [], "first_floor": floor, "last_floor": floor}
            mp_analysis[mp]["floors"].append(floor)
            mp_analysis[mp]["invs"].append(inv)
            mp_analysis[mp]["last_floor"] = floor  # rows sorted asc so last = most recent

    mp_summary = {}
    for mp, d in mp_analysis.items():
        start = d["first_floor"]
        end   = d["last_floor"]
        trend_pct = round((end - start) / start * 100, 1) if start else None
        mp_summary[mp] = {
            "min_floor":      round(min(d["floors"]), 2),
            "max_floor":      round(max(d["floors"]), 2),
            "max_inv":        max(d["invs"]),
            "floor_trend_pct": trend_pct,
        }

    # ── Absorption classification ─────────────────────────────────────────────
    def _classify(inv_delta, price_delta):
        inv_down  = inv_delta < -5
        inv_up    = inv_delta > 5
        price_up  = price_delta > 2
        price_down = price_delta < -2
        if inv_down and price_up:    return "demand"
        if inv_up   and price_down:  return "oversupply"
        if inv_down and price_down:  return "capitulation"
        if inv_up   and price_up:    return "repricing"
        return "stable"

    from collections import Counter
    transitions = []
    for i in range(1, len(curve)):
        prev = curve[i - 1]
        curr = curve[i]
        inv_delta   = curr["inventory"] - prev["inventory"]
        price_delta = curr["floor_price"] - prev["floor_price"]
        transitions.append({
            "hours_to_event":   round(curr["hours_to_event"], 1),
            "inv_delta":        inv_delta,
            "price_delta":      round(price_delta, 2),
            "classification":   _classify(inv_delta, price_delta),
        })

    absorption_counts = dict(Counter(t["classification"] for t in transitions))
    dominant = Counter(t["classification"] for t in transitions).most_common(1)

    # ── Ariana profile context (hardcoded from Phase 1A computation) ──────────
    artist_profile = None
    title_lower = (event_row.title or "").lower()
    if "ariana" in title_lower:
        artist_profile = {
            "artist": "ariana_grande",
            "events_analyzed": 2,
            "timing": {
                "avg_lowest_floor_hours_to_event": 50.5,
                "avg_inventory_peak_hours_to_event": 15.0,
                "avg_inventory_collapse_hours_to_event": 13.0,
            },
            "marketplace_findings": {
                "lowest_floor_source": "tickpick",
                "highest_inventory_source": "tickpick",
                "leads_price_decline": "gametime",
                "price_decline_pct": -36.6,
            },
            "absorption_dominant": "stable",
            "note": "Computed from 2 completed SoFi events (June 13-14 2026)",
        }

    return {
        "event_id": event_id,
        "title": event_row.title,
        "event_date": event_dt.isoformat(),
        "is_completed": is_completed,
        "tracking_start_hours_before": round(curve[0]["hours_to_event"], 1),
        "data_points": len(curve),

        # ── Curve ────────────────────────────────────────────────────────────
        "curve": curve,

        # ── Key timing markers ───────────────────────────────────────────────
        "lowest_floor": round(min_floor_row["floor_price"], 2),
        "lowest_floor_hours_to_event": round(min_floor_row["hours_to_event"], 1),
        "inventory_peak": max_inv_row["inventory"],
        "inventory_peak_hours_to_event": round(max_inv_row["hours_to_event"], 1),
        "inventory_collapse_hours_to_event": round(collapse_row["hours_to_event"], 1) if collapse_row else None,

        # ── Marketplace breakdown ────────────────────────────────────────────
        "marketplace_analysis": mp_summary,

        # ── Absorption ───────────────────────────────────────────────────────
        "absorption": {
            "transitions": transitions,
            "summary": absorption_counts,
            "dominant": dominant[0][0] if dominant else "unknown",
        },

        # ── Artist profile context ───────────────────────────────────────────
        "artist_profile": artist_profile,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TASK B — EVENT INTELLIGENCE V1 SNAPSHOT
# ─────────────────────────────────────────────────────────────────────────────

def _classify_market(
    inv24h: Optional[float],
    price_delta_24h: Optional[float],
    price_delta_pct_24h: Optional[float],
    seller_aggression: Optional[float],
    inventory_added: int,
    inventory_removed: int,
) -> tuple[str, float]:
    """
    Classify current market state.

    DEMAND:       Inventory shrinking + price rising (buyers competing)
    OVERSUPPLY:   Inventory growing + price falling (sellers competing)
    CAPITULATION: High seller aggression + significant price drop (panic cuts)
    REPRICING:    Price moving > 3% with minimal inventory change (market reset)
    STABLE:       No significant movement in any dimension
    """
    price_chg = price_delta_pct_24h or 0.0
    inv_chg   = inv24h or 0.0
    aggression = seller_aggression or 0.0

    # CAPITULATION: sellers slashing prices aggressively
    if aggression > 0.6 and price_chg < -3:
        confidence = min(1.0, aggression * 0.7 + abs(price_chg) / 20 * 0.3)
        return "CAPITULATION", round(confidence, 3)

    # DEMAND: inventory falling, price steady or rising
    if inv_chg < -10 and price_chg >= -1:
        confidence = min(1.0, abs(inv_chg) / 50 * 0.6 + max(0, price_chg / 5) * 0.4)
        return "DEMAND", round(confidence, 3)

    # OVERSUPPLY: inventory growing, price falling
    if inv_chg > 10 and price_chg < -1:
        confidence = min(1.0, inv_chg / 50 * 0.5 + abs(price_chg) / 10 * 0.5)
        return "OVERSUPPLY", round(confidence, 3)

    # REPRICING: price moved > 3% but inventory stable
    if abs(price_chg) > 3 and abs(inv_chg) < 5:
        confidence = min(1.0, abs(price_chg) / 15)
        return "REPRICING", round(confidence, 3)

    return "STABLE", 0.5


@router.get("/events/{event_id}/snapshot")
async def event_intelligence_snapshot(
    event_id: int,
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Task B — Event Intelligence V1 Snapshot.

    Returns structured price/inventory/velocity/marketplace/classification
    for one event. Serves from computed intelligence cache.

    Fields:
      price:        floor_now, floor_24h_change, floor_7d_change,
                    median_now, median_24h_change, median_7d_change
      inventory:    inventory_now, inventory_24h_change, inventory_7d_change
      velocity:     inventory_removed_24h, inventory_added_24h, net_inventory_change
      marketplace:  leading_price_drop, leading_inventory_loss, lowest_floor, lowest_floor_mp
      classification: DEMAND | OVERSUPPLY | CAPITULATION | REPRICING | STABLE
    """
    await _require_event(event_id, db)
    intel = await _get_or_compute(event_id, db, force=refresh)

    now_sql = datetime.now(timezone.utc).replace(tzinfo=None)

    # ── Floor deltas from window snapshots ────────────────────────────────────
    # _WINDOW_PRICE_SQL returns (median, low_ask, listing_count)
    # We need to query directly for the floor comparison windows.

    async def _floor_at_window(hours_back: int) -> Optional[float]:
        center = now_sql - timedelta(hours=hours_back)
        row = (await db.execute(text("""
            SELECT MIN(price)
            FROM listing_snapshots
            WHERE event_id = :eid
              AND snapshot_at >= :w_start
              AND snapshot_at < :w_end
              AND price > 0
        """), {
            "eid": event_id,
            "w_start": center - timedelta(hours=1),
            "w_end":   center + timedelta(hours=1),
        })).fetchone()
        return float(row[0]) if row and row[0] else None

    floor_now = intel.get("price", {}).get("low_ask")

    # Try 24h window; fall back to agg table if no live snapshots
    floor_24h_ago = await _floor_at_window(24)
    floor_7d_ago  = await _floor_at_window(168) if (intel.get("history_hours") or 0) >= 168 else None

    # Agg fallback for 24h if live snapshots don't go back that far
    if floor_24h_ago is None:
        agg_row = (await db.execute(text("""
            SELECT low_ask FROM event_price_history_agg
            WHERE railway_event_id = :eid
              AND bucket_ts >= :since
            ORDER BY bucket_ts ASC LIMIT 1
        """), {"eid": event_id, "since": now_sql - timedelta(hours=26)})).fetchone()
        if agg_row and agg_row[0]:
            floor_24h_ago = float(agg_row[0])

    floor_24h_change = round(floor_now - floor_24h_ago, 2) if (floor_now and floor_24h_ago) else None
    floor_7d_change  = round(floor_now - floor_7d_ago, 2)  if (floor_now and floor_7d_ago)  else None

    # ── Median deltas (from stored intelligence) ──────────────────────────────
    changes  = intel.get("changes", {})
    median_now          = intel.get("price", {}).get("median_ask")
    median_24h_change   = changes.get("h24", {}).get("price_delta")
    median_7d_change    = changes.get("d7", {}).get("price_delta")

    # ── Inventory ─────────────────────────────────────────────────────────────
    inventory_now        = intel.get("inventory", {}).get("total_listings")
    inventory_24h_change = changes.get("h24", {}).get("inventory_delta")
    inventory_7d_change  = changes.get("d7", {}).get("inventory_delta")

    # ── Velocity ──────────────────────────────────────────────────────────────
    sb = intel.get("seller_behavior", {})
    inv_added   = int(sb.get("new_24h") or 0)
    inv_removed = int(sb.get("removed_24h") or 0)

    # ── Marketplace leaders ───────────────────────────────────────────────────
    # Per-marketplace 24h activity from poll_runs
    since_24h = now_sql - timedelta(hours=24)
    mp_activity = (await db.execute(text("""
        SELECT m.slug,
               SUM(pr.new_listings)         AS added,
               SUM(pr.disappeared_listings) AS removed
        FROM poll_runs pr
        JOIN tracked_events te ON te.id = pr.tracked_event_id
        JOIN marketplaces m    ON m.id  = te.marketplace_id
        WHERE te.event_id = :eid
          AND pr.status   = 'success'
          AND pr.started_at >= :since
        GROUP BY m.slug
    """), {"eid": event_id, "since": since_24h})).fetchall()

    mp_lead_price_drop = None  # marketplace with most pricing cuts (from repriced SQL)
    mp_lead_inv_loss   = None
    mp_lowest_floor    = None
    mp_lowest_floor_val = float("inf")

    for r in mp_activity:
        slug, added, removed = r[0], int(r[1] or 0), int(r[2] or 0)
        if removed > (int(mp_lead_inv_loss[1]) if mp_lead_inv_loss else -1):
            mp_lead_inv_loss = (slug, removed)

    for mp in (intel.get("marketplace_metrics") or []):
        if mp.get("low_ask") and mp["low_ask"] < mp_lowest_floor_val:
            mp_lowest_floor_val = mp["low_ask"]
            mp_lowest_floor     = mp["name"]

    # Leading price drop: marketplace where most price cuts happened
    # Use existing repriced data from the intelligence cache if available
    mp_price_drops_row = (await db.execute(text("""
        WITH reprice AS (
            SELECT m.slug,
                   COUNT(*) FILTER (
                       WHERE ls2.price < ls1.price
                   ) AS drops
            FROM listing_snapshots ls1
            JOIN listing_snapshots ls2
              ON ls2.listing_id = ls1.listing_id
             AND ls2.snapshot_at > ls1.snapshot_at
            JOIN listings l  ON l.id = ls1.listing_id
            JOIN marketplaces m ON m.id = ls1.marketplace_id
            WHERE ls1.event_id = :eid
              AND ls1.snapshot_at >= :since
            GROUP BY m.slug
        )
        SELECT slug, drops FROM reprice ORDER BY drops DESC LIMIT 1
    """), {"eid": event_id, "since": since_24h})).fetchone()

    if mp_price_drops_row and mp_price_drops_row[1]:
        mp_lead_price_drop = mp_price_drops_row[0]

    # ── Classification ────────────────────────────────────────────────────────
    market = intel.get("market", {})
    classification, classification_confidence = _classify_market(
        inv24h=inventory_24h_change,
        price_delta_24h=median_24h_change,
        price_delta_pct_24h=changes.get("h24", {}).get("price_delta_pct"),
        seller_aggression=market.get("seller_aggression"),
        inventory_added=inv_added,
        inventory_removed=inv_removed,
    )

    # ── Per-marketplace 7d floor trend ────────────────────────────────────────
    hist_hours = intel.get("history_hours") or 0
    mp_7d_trends: dict = {}
    if hist_hours >= 24:
        window_start_7d = now_sql - timedelta(days=min(7, hist_hours / 24))
        # Use the most recent snapshot per marketplace within the last 6h
        # (not 2h — most events poll every 3-4h, so 2h misses most events).
        mp_hist = (await db.execute(text("""
            SELECT m.slug,
                   MIN(ls.price)                                            AS floor_now,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ls.price)   AS median_now,
                   COUNT(DISTINCT ls.listing_id)                            AS listings_now
            FROM listing_snapshots ls
            JOIN marketplaces m ON m.id = ls.marketplace_id
            WHERE ls.event_id = :eid
              AND ls.snapshot_at >= :since_6h
              AND ls.price > 0
            GROUP BY m.slug
        """), {"eid": event_id, "since_6h": now_sql - timedelta(hours=6)})).fetchall()

        mp_hist_old = (await db.execute(text("""
            SELECT m.slug,
                   MIN(ls.price)                                            AS floor_old,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ls.price)   AS median_old,
                   COUNT(DISTINCT ls.listing_id)                            AS listings_old
            FROM listing_snapshots ls
            JOIN marketplaces m ON m.id = ls.marketplace_id
            WHERE ls.event_id = :eid
              AND ls.snapshot_at BETWEEN :w_start AND :w_end
              AND ls.price > 0
            GROUP BY m.slug
        """), {
            "eid": event_id,
            "w_start": window_start_7d - timedelta(hours=1),
            "w_end":   window_start_7d + timedelta(hours=1),
        })).fetchall()

        old_by_mp = {r[0]: r for r in mp_hist_old}

        for r in mp_hist:
            slug = r[0]
            old  = old_by_mp.get(slug)
            floor_now_mp   = float(r[1]) if r[1] else None
            floor_old_mp   = float(old[1]) if old and old[1] else None
            median_now_mp  = float(r[2]) if r[2] else None
            median_old_mp  = float(old[2]) if old and old[2] else None
            listings_now_mp = int(r[3] or 0)
            listings_old_mp = int(old[3] or 0) if old else None

            floor_trend  = round(floor_now_mp  - floor_old_mp,  2) if (floor_now_mp  and floor_old_mp)  else None
            median_trend = round(median_now_mp - median_old_mp, 2) if (median_now_mp and median_old_mp) else None
            inv_trend    = (listings_now_mp - listings_old_mp) if listings_old_mp is not None else None

            mp_7d_trends[slug] = {
                "floor_now":    round(floor_now_mp, 2) if floor_now_mp else None,
                "floor_change": floor_trend,
                "floor_change_pct": round((floor_trend / floor_old_mp) * 100, 1) if (floor_trend and floor_old_mp) else None,
                "median_now":   round(median_now_mp, 2) if median_now_mp else None,
                "median_change": median_trend,
                "listings_now": listings_now_mp,
                "listings_change": inv_trend,
                "window_hours": round(min(7 * 24, hist_hours), 0),
            }

    return {
        "event_id": event_id,
        "computed_at": intel.get("computed_at"),
        "history_hours": hist_hours,
        "price": {
            "floor_now":          floor_now,
            "floor_24h_change":   floor_24h_change,
            "floor_7d_change":    floor_7d_change,
            "median_now":         median_now,
            "median_24h_change":  median_24h_change,
            "median_24h_change_pct": changes.get("h24", {}).get("price_delta_pct"),
            "median_7d_change":   median_7d_change,
            "median_7d_change_pct": changes.get("d7", {}).get("price_delta_pct"),
        },
        "inventory": {
            "inventory_now":         inventory_now,
            "inventory_24h_change":  inventory_24h_change,
            "inventory_7d_change":   inventory_7d_change,
        },
        "velocity": {
            "inventory_removed_24h": inv_removed,
            "inventory_added_24h":   inv_added,
            "net_inventory_change":  inv_added - inv_removed,
        },
        "marketplace": {
            "marketplace_leading_price_drop":    mp_lead_price_drop,
            "marketplace_leading_inventory_loss": mp_lead_inv_loss[0] if mp_lead_inv_loss else None,
            "marketplace_leading_inventory_loss_count": mp_lead_inv_loss[1] if mp_lead_inv_loss else None,
            "marketplace_lowest_floor":          mp_lowest_floor,
            "marketplace_lowest_floor_price":    round(mp_lowest_floor_val, 2) if mp_lowest_floor_val != float("inf") else None,
        },
        "classification": classification,
        "classification_confidence": classification_confidence,
        "per_marketplace_trends": mp_7d_trends,
        # Task E — Lifecycle expansion (computed on demand)
        "lifecycle": None,  # populated below
    }

    # Task E: enrich snapshot with lifecycle intelligence.
    # Use a fresh session to avoid inheriting any aborted transaction state from
    # the many snapshot queries that ran above.
    try:
        from app.database import AsyncSessionLocal as _SessionLocal
        async with _SessionLocal() as fresh_db:
            lifecycle = await compute_lifecycle(event_id, fresh_db)
        lc_summary = lifecycle.get("summary", {})
        resp["lifecycle"] = {
            "assumed_sales":            lc_summary.get("assumed_sales"),
            "relisted_count":           lc_summary.get("relisted_count"),
            "repriced_count":           lc_summary.get("repriced_count"),
            "relist_rate":              lc_summary.get("relist_rate"),
            "repricing_rate":           lc_summary.get("repricing_rate"),
            "seller_aggression_score":  lc_summary.get("seller_aggression_score"),
            "seller_capitulation_score": lc_summary.get("seller_capitulation_score"),
            "churn_rate":               lc_summary.get("churn_rate"),
            "relist_delay_p50_hours":   lc_summary.get("relist_delay_p50_hours"),
        }
    except Exception as _lc_err:
        import logging as _lg
        _lg.getLogger(__name__).warning("lifecycle enrichment failed for event %s: %s", event_id, _lc_err)
        import traceback as _tb
        _lg.getLogger(__name__).warning("lifecycle traceback: %s", _tb.format_exc())
        resp["lifecycle"] = {"error": str(_lc_err)[:200], "type": type(_lc_err).__name__}

    return resp


# ─────────────────────────────────────────────────────────────────────────────
# TASK D — INTELLIGENCE READINESS AUDIT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/readiness")
async def intelligence_readiness_audit(db: AsyncSession = Depends(get_db)):
    """
    Task D — Intelligence Readiness Audit.

    Lists ALL tracked events with:
      - hours_tracked (from listing_snapshots)
      - history_source: live | archive | combined | none
      - intelligence_eligible: yes | partial | insufficient
      - data_note

    Thresholds: <24h = insufficient, 24-72h = partial, 72h+ = eligible
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    rows = (await db.execute(text("""
        SELECT
            e.id,
            e.title,
            e.artist,
            e.event_date::date                             AS event_date,
            e.status,
            MIN(ls.snapshot_at)                            AS snap_oldest,
            MAX(ls.snapshot_at)                            AS snap_newest,
            COUNT(DISTINCT ls.id)                          AS snap_count,
            MIN(agg.bucket_ts)                             AS agg_oldest,
            MAX(agg.bucket_ts)                             AS agg_newest,
            COUNT(DISTINCT agg.id)                         AS agg_count
        FROM events e
        LEFT JOIN listing_snapshots ls ON ls.event_id = e.id
        LEFT JOIN event_price_history_agg agg ON agg.railway_event_id = e.id
        GROUP BY e.id, e.title, e.artist, e.event_date, e.status
        ORDER BY e.event_date ASC
    """))).fetchall()

    events_out = []
    for r in rows:
        (eid, title, artist, event_date, status,
         snap_old, snap_new, snap_count,
         agg_old, agg_new, agg_count) = r

        # Combined oldest = min(snap_oldest, agg_oldest)
        oldest = None
        newest = snap_new
        if snap_old and agg_old:
            oldest = min(snap_old, agg_old)
        elif snap_old:
            oldest = snap_old
        elif agg_old:
            oldest = agg_old
            newest = agg_new

        hours_tracked = 0.0
        if oldest and newest:
            hours_tracked = round((newest - oldest).total_seconds() / 3600, 1)

        # Determine source
        has_live = (snap_count or 0) > 0
        has_agg  = (agg_count  or 0) > 0
        if has_live and has_agg:
            source = "combined"
        elif has_live:
            source = "live"
        elif has_agg:
            source = "archive"
        else:
            source = "none"

        # Eligibility
        if hours_tracked >= 72:
            eligible = "eligible"
            data_note = f"{hours_tracked}h tracked — full intelligence available"
        elif hours_tracked >= 24:
            eligible = "partial"
            data_note = f"{hours_tracked}h tracked — partial (72h needed for full confidence)"
        else:
            eligible = "insufficient"
            data_note = f"{hours_tracked}h tracked — insufficient (<24h)"

        hours_until = None
        if event_date:
            from datetime import date
            days_diff = (event_date - date.today()).days
            hours_until = days_diff * 24

        events_out.append({
            "event_id":         eid,
            "title":            title,
            "artist":           artist,
            "event_date":       str(event_date),
            "status":           status,
            "hours_until_event": hours_until,
            "hours_tracked":    hours_tracked,
            "history_source":   source,
            "snap_count":       int(snap_count or 0),
            "agg_bucket_count": int(agg_count or 0),
            "intelligence_eligible": eligible,
            "data_note":        data_note,
        })

    eligible_count   = sum(1 for e in events_out if e["intelligence_eligible"] == "eligible")
    partial_count    = sum(1 for e in events_out if e["intelligence_eligible"] == "partial")
    insufficient_count = sum(1 for e in events_out if e["intelligence_eligible"] == "insufficient")

    return {
        "audit_at": now.isoformat(),
        "summary": {
            "total":        len(events_out),
            "eligible":     eligible_count,
            "partial":      partial_count,
            "insufficient": insufficient_count,
        },
        "events": events_out,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2B — LISTING LIFECYCLE INTELLIGENCE V1
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/lifecycle")
async def listing_lifecycle_endpoint(
    event_id: int,
    hours_window: int = Query(default=168, ge=24, le=720),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 2B — Listing Lifecycle Intelligence V1.

    Classifies every disappeared listing into:
      probable_sale, probable_relist, probable_pull, probable_expiration, unknown

    Computes at event, marketplace, and section level:
      absorption_rate, relist_rate, repricing_rate, churn_rate,
      seller_aggression_score, seller_capitulation_score

    Returns section-level velocity and liquidity data (Phase 2C).
    API-only; no UI changes.
    """
    await _require_event(event_id, db)
    return await compute_lifecycle(event_id, db, hours_window=hours_window)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2D — BUY WINDOW ENGINE V1
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/buy-signal")
async def buy_signal_endpoint(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 2D — Buy Window Engine V1.

    Generates a BUY / WAIT / MONITOR signal using:
      - Market classification (capitulation_score, price trend, classification)
      - Listing lifecycle (absorption_rate, relist_rate, seller_capitulation)
      - Days until event
      - 7-day price trend from archive

    Every signal includes:
      - signal: BUY | WAIT | MONITOR
      - confidence: 0.0–1.0
      - supporting_metrics: the exact inputs that drove the signal
      - explanation: human-readable reasoning

    No black-box scoring. All weights documented in buy_window.py.
    API-only; no UI changes.
    """
    await _require_event(event_id, db)
    return await compute_buy_signal(event_id, db)


# ─────────────────────────────────────────────────────────────────────────────
# TASK B (also wired here) — COVERAGE AUDIT via intelligence router
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/coverage")
async def intelligence_coverage_audit(
    db: AsyncSession = Depends(get_db),
):
    """
    Task B — Ingestion Coverage Audit for all active future events.
    Also available at GET /api/health/coverage.

    Returns per-event coverage classification:
      FULL (4+), PARTIAL (2-3), LIMITED (1), BROKEN (0)
    with per-marketplace health status for each event.
    """
    return await get_coverage_audit(db)
