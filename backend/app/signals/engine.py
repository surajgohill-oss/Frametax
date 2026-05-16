"""
Phase 5 Signal Engine.

Reads exclusively from listing_snapshots + events/tracked_events.
Never mutates ingestion tables.
Never references marketplace names — only marketplace_id (integer FK).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.signals.models import (
    EventDecision,
    EventSignalBundle,
    LiquidityPressureSignal,
    MarketDivergenceSignal,
    PriceMomentumSignal,
    ScarcityAccelerationSignal,
)

# ── Decision thresholds ────────────────────────────────────────────────────────

_SCARCITY_DEAL_THRESHOLD     = 1.2    # scarcity_index > 1.2 → supply < 83 % of peak
_LIQUIDITY_DISLOC_THRESHOLD  = -0.10  # liquidity_pressure < -10 %
_DIVERGENCE_DISLOC_THRESHOLD = 0.05   # divergence_index > 5 % price gap
_EPSILON                     = 1e-6   # avoid div/0

# ── Internal query helpers ─────────────────────────────────────────────────────

_PRICE_MOMENTUM_SQL = text("""
SELECT
    AVG(price) FILTER (
        WHERE snapshot_at >= NOW() - INTERVAL '24 hours'
    )                                                    AS avg_p_24h_recent,
    AVG(price) FILTER (
        WHERE snapshot_at >= NOW() - INTERVAL '48 hours'
          AND snapshot_at <  NOW() - INTERVAL '24 hours'
    )                                                    AS avg_p_24h_prior,
    AVG(price) FILTER (
        WHERE snapshot_at >= NOW() - INTERVAL '7 days'
    )                                                    AS avg_p_7d_recent,
    AVG(price) FILTER (
        WHERE snapshot_at >= NOW() - INTERVAL '14 days'
          AND snapshot_at <  NOW() - INTERVAL '7 days'
    )                                                    AS avg_p_7d_prior
FROM listing_snapshots
WHERE event_id = :event_id
  AND snapshot_at >= NOW() - INTERVAL '14 days'
""")

_LIQUIDITY_SQL = text("""
SELECT
    SUM(quantity) FILTER (
        WHERE snapshot_at >= NOW() - INTERVAL '2 hours'
    )                                                    AS qty_now,
    SUM(quantity) FILTER (
        WHERE snapshot_at >= NOW() - INTERVAL '25 hours'
          AND snapshot_at <  NOW() - INTERVAL '23 hours'
    )                                                    AS qty_24h_ago,
    MAX(daily_qty)                                       AS max_qty_30d
FROM (
    SELECT
        date_trunc('hour', snapshot_at) AS hour_bucket,
        SUM(quantity)                   AS daily_qty
    FROM listing_snapshots
    WHERE event_id = :event_id
      AND snapshot_at >= NOW() - INTERVAL '30 days'
    GROUP BY date_trunc('hour', snapshot_at)
) sub
""")

_DIVERGENCE_SQL = text("""
SELECT
    marketplace_id,
    AVG(price) AS avg_price
FROM listing_snapshots
WHERE event_id = :event_id
  AND snapshot_at >= NOW() - INTERVAL '24 hours'
GROUP BY marketplace_id
HAVING COUNT(*) > 0
""")

_SCARCITY_SQL = text("""
SELECT
    SUM(quantity) FILTER (
        WHERE snapshot_at >= NOW() - INTERVAL '2 hours'
    )                                                   AS qty_now,
    SUM(quantity) FILTER (
        WHERE snapshot_at >= NOW() - INTERVAL '25 hours'
          AND snapshot_at <  NOW() - INTERVAL '23 hours'
    )                                                   AS qty_24h_ago,
    MAX(hourly_qty)                                     AS max_qty_30d
FROM (
    SELECT
        date_trunc('hour', snapshot_at) AS h,
        SUM(quantity)                   AS hourly_qty
    FROM listing_snapshots
    WHERE event_id   = :event_id
      AND snapshot_at >= NOW() - INTERVAL '30 days'
    GROUP BY date_trunc('hour', snapshot_at)
) sub
""")

_ACTIVE_EVENT_IDS_SQL = text("""
SELECT DISTINCT te.event_id
FROM tracked_events te
WHERE te.is_active = true
  AND te.external_event_id IS NOT NULL
""")


# ── Signal computation ─────────────────────────────────────────────────────────

async def _compute_price_momentum(db: AsyncSession, event_id: int) -> PriceMomentumSignal:
    row = (await db.execute(_PRICE_MOMENTUM_SQL, {"event_id": event_id})).one()

    p24r = float(row.avg_p_24h_recent) if row.avg_p_24h_recent is not None else None
    p24p = float(row.avg_p_24h_prior)  if row.avg_p_24h_prior  is not None else None
    p7r  = float(row.avg_p_7d_recent)  if row.avg_p_7d_recent  is not None else None
    p7p  = float(row.avg_p_7d_prior)   if row.avg_p_7d_prior   is not None else None

    has_data = all(v is not None for v in [p24r, p24p, p7r, p7p])
    velocity_24h    = (p24r - p24p) if (p24r is not None and p24p is not None) else None
    velocity_7d     = (p7r  - p7p)  if (p7r  is not None and p7p  is not None) else None
    price_momentum  = (velocity_24h - velocity_7d) if (velocity_24h is not None and velocity_7d is not None) else None

    return PriceMomentumSignal(
        velocity_24h=velocity_24h,
        velocity_7d=velocity_7d,
        price_momentum=price_momentum,
        has_data=has_data,
    )


async def _compute_liquidity_pressure(db: AsyncSession, event_id: int) -> LiquidityPressureSignal:
    row = (await db.execute(_LIQUIDITY_SQL, {"event_id": event_id})).one()

    qty_now      = float(row.qty_now)      if row.qty_now      is not None else None
    qty_24h_ago  = float(row.qty_24h_ago)  if row.qty_24h_ago  is not None else None
    max_qty_30d  = float(row.max_qty_30d)  if row.max_qty_30d  is not None else None

    has_data = qty_now is not None and max_qty_30d is not None

    inv_delta    = (qty_now - qty_24h_ago) if (qty_now is not None and qty_24h_ago is not None) else None
    liq_pressure = (inv_delta / (max_qty_30d + _EPSILON)) if (inv_delta is not None and max_qty_30d is not None) else None

    return LiquidityPressureSignal(
        inventory_now=qty_now,
        inventory_24h_ago=qty_24h_ago,
        max_inventory_30d=max_qty_30d,
        inventory_delta_24h=inv_delta,
        liquidity_pressure=liq_pressure,
        has_data=has_data,
    )


async def _compute_market_divergence(db: AsyncSession, event_id: int) -> MarketDivergenceSignal:
    rows = (await db.execute(_DIVERGENCE_SQL, {"event_id": event_id})).all()

    # Keys are integer marketplace_ids — never names
    price_by_mp: dict[int, float] = {
        row.marketplace_id: round(float(row.avg_price), 2)
        for row in rows
    }
    mp_count = len(price_by_mp)

    if mp_count < 2:
        return MarketDivergenceSignal(
            price_by_marketplace=price_by_mp,
            marketplace_count=mp_count,
            divergence_index=None,
            has_data=mp_count > 0,
        )

    prices = list(price_by_mp.values())
    mx, mn = max(prices), min(prices)
    divergence_index = (mx - mn) / (mn + _EPSILON)

    return MarketDivergenceSignal(
        price_by_marketplace=price_by_mp,
        marketplace_count=mp_count,
        divergence_index=round(divergence_index, 6),
        has_data=True,
    )


async def _compute_scarcity(db: AsyncSession, event_id: int) -> ScarcityAccelerationSignal:
    row = (await db.execute(_SCARCITY_SQL, {"event_id": event_id})).one()

    qty_now     = float(row.qty_now)     if row.qty_now     is not None else None
    qty_24h_ago = float(row.qty_24h_ago) if row.qty_24h_ago is not None else None
    max_30d     = float(row.max_qty_30d) if row.max_qty_30d is not None else None

    has_data = qty_now is not None and max_30d is not None

    # scarcity_index = peak / current; >1 means supply is below historical peak
    si_now = (max_30d / (qty_now + _EPSILON))     if (qty_now is not None and max_30d is not None) else None
    si_24h = (max_30d / (qty_24h_ago + _EPSILON)) if (qty_24h_ago is not None and max_30d is not None) else None
    acceleration = (si_now - si_24h) if (si_now is not None and si_24h is not None) else None

    return ScarcityAccelerationSignal(
        scarcity_index_now=round(si_now, 6)       if si_now       is not None else None,
        scarcity_index_24h_ago=round(si_24h, 6)   if si_24h       is not None else None,
        scarcity_acceleration=round(acceleration, 6) if acceleration is not None else None,
        has_data=has_data,
    )


# ── Decision engine ────────────────────────────────────────────────────────────

def _classify(
    pm:  PriceMomentumSignal,
    lp:  LiquidityPressureSignal,
    div: MarketDivergenceSignal,
    sc:  ScarcityAccelerationSignal,
) -> tuple[EventDecision, list[str]]:
    """
    Deterministic classification — evaluated in priority order.
    Returns (decision, reasons).
    """
    any_data = pm.has_data or lp.has_data or div.has_data or sc.has_data
    if not any_data:
        return EventDecision.INSUFFICIENT_DATA, ["no_snapshot_data"]

    reasons: list[str] = []

    # DEAL_FORMING: prices are dropping while supply is tight
    deal_forming = (
        sc.scarcity_index_now is not None
        and sc.scarcity_index_now > _SCARCITY_DEAL_THRESHOLD
        and pm.price_momentum is not None
        and pm.price_momentum < 0
    )
    if deal_forming:
        reasons.append(f"scarcity_index={sc.scarcity_index_now:.3f}>{_SCARCITY_DEAL_THRESHOLD}")
        reasons.append(f"price_momentum={pm.price_momentum:.4f}<0")
        return EventDecision.DEAL_FORMING, reasons

    # MARKET_DISLOCATION: liquidity contracting + significant cross-marketplace gap
    dislocation = (
        lp.liquidity_pressure is not None
        and lp.liquidity_pressure < _LIQUIDITY_DISLOC_THRESHOLD
        and div.divergence_index is not None
        and div.divergence_index > _DIVERGENCE_DISLOC_THRESHOLD
    )
    if dislocation:
        reasons.append(f"liquidity_pressure={lp.liquidity_pressure:.4f}<{_LIQUIDITY_DISLOC_THRESHOLD}")
        reasons.append(f"divergence_index={div.divergence_index:.4f}>{_DIVERGENCE_DISLOC_THRESHOLD}")
        return EventDecision.MARKET_DISLOCATION, reasons

    return EventDecision.STABLE, ["no_signal_thresholds_exceeded"]


# ── Public API ─────────────────────────────────────────────────────────────────

async def compute_signals(db: AsyncSession, event_id: int) -> EventSignalBundle:
    """
    Compute all signals for a single event_id.
    Triggered after each poll_run, resolver update, or snapshot batch.
    """
    pm, lp, div, sc = (
        await _compute_price_momentum(db, event_id),
        await _compute_liquidity_pressure(db, event_id),
        await _compute_market_divergence(db, event_id),
        await _compute_scarcity(db, event_id),
    )
    decision, reasons = _classify(pm, lp, div, sc)

    return EventSignalBundle(
        event_id=event_id,
        computed_at=datetime.utcnow(),
        price_momentum=pm,
        liquidity_pressure=lp,
        market_divergence=div,
        scarcity=sc,
        decision=decision,
        decision_reasons=reasons,
    )


async def compute_signals_all_active(db: AsyncSession) -> list[EventSignalBundle]:
    """
    Compute signals for every currently-active, resolved event.
    Used by the batch endpoint and post-poll-run trigger.
    """
    rows = (await db.execute(_ACTIVE_EVENT_IDS_SQL)).all()
    event_ids = [r.event_id for r in rows]
    return [await compute_signals(db, eid) for eid in event_ids]
