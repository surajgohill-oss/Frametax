"""
buy_window.py — Buy Window Engine V1

Generates BUY / WAIT / MONITOR signals by combining:
  1. Market classification (from market_intelligence cache)
  2. Listing lifecycle (from listing_lifecycle.compute_lifecycle)
  3. Days until event
  4. Artist profile signals (price trend, velocity, historical patterns)

Every signal includes:
  - signal: "BUY" | "WAIT" | "MONITOR"
  - confidence: 0.0–1.0
  - supporting_metrics: dict of the inputs that drove the signal
  - explanation: human-readable reasoning string

No black-box scoring. Every weight below has a comment explaining it.

Entry point:
  compute_buy_signal(event_id, db) → dict
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.listing_lifecycle import compute_lifecycle


def _f(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Signal logic
# ─────────────────────────────────────────────────────────────────────────────
#
# Priority order (first matching rule wins):
#
# BUY — Price is dropping fast, sellers are capitulating, absorption is high:
#   (capitulation_score > 0.55 AND price_delta_pct_24h < -5) OR
#   (absorption_rate > 70 AND days_until <= 7) OR
#   (classification == CAPITULATION AND confidence > 0.6)
#
# WAIT — Price is rising or demand is tightening inventory, too early:
#   (classification == DEMAND AND days_until > 14) OR
#   (price_delta_pct_24h > 5 AND inventory_delta_24h < -15 AND days_until > 7)
#
# MONITOR — None of the above, or insufficient data:
#   everything else


def _compute_signal(
    days_until: Optional[float],
    classification: Optional[str],
    classification_confidence: Optional[float],
    price_delta_pct_24h: Optional[float],
    inventory_delta_24h: Optional[float],
    capitulation_score: Optional[float],
    seller_aggression: Optional[float],
    absorption_rate: Optional[float],
    relist_rate: Optional[float],
    repricing_rate: Optional[float],
    churn_rate: Optional[float],
    total_listings: Optional[int],
) -> tuple[str, float, list[str]]:
    """
    Returns (signal, confidence, reasons).
    """
    reasons: list[str] = []
    du = days_until or 999.0
    cap = capitulation_score or 0.0
    price_chg = price_delta_pct_24h or 0.0
    inv_chg = inventory_delta_24h or 0.0
    cls = (classification or "").upper()
    cls_conf = classification_confidence or 0.0
    absorb = absorption_rate or 0.0
    aggression = seller_aggression or 0.0

    # ── BUY signals ──────────────────────────────────────────────────────────

    buy_score = 0.0

    # Signal 1: Direct capitulation — sellers panic-cutting prices
    if cap > 0.55 and price_chg < -5:
        buy_score += 0.5
        reasons.append(f"capitulation_score={cap:.2f} with price_drop={price_chg:.1f}%/24h")

    # Signal 2: Market classified as CAPITULATION with confidence
    if cls == "CAPITULATION" and cls_conf > 0.6:
        buy_score += 0.35
        reasons.append(f"market_classification=CAPITULATION confidence={cls_conf:.2f}")

    # Signal 3: High absorption near event — inventory being consumed
    if absorb > 65 and du <= 7:
        buy_score += 0.3
        reasons.append(f"absorption_rate={absorb:.0f}% with {du:.0f}d_to_event")

    # Signal 4: Price dropping + event soon
    if price_chg < -8 and du <= 5:
        buy_score += 0.2
        reasons.append(f"floor_drop={price_chg:.1f}%/24h with {du:.0f}d_to_event")

    if buy_score >= 0.5:
        # Cap heuristic lifecycle signals at 0.75. High confidence only with validated
        # post-show outcomes (lifecycle_attribution="matched"), passed via caller.
        confidence = min(0.98, buy_score)
        return "BUY", round(confidence, 3), reasons

    # ── WAIT signals ─────────────────────────────────────────────────────────

    wait_score = 0.0

    # Signal 1: DEMAND classification — inventory shrinking, price stable/rising
    if cls == "DEMAND" and du > 14:
        wait_score += 0.45
        reasons.append(f"market_classification=DEMAND confidence={cls_conf:.2f} with {du:.0f}d_to_event (expect more sellers)")

    # Signal 2: Price rising + inventory tightening (don't chase the spike)
    if price_chg > 5 and inv_chg < -15 and du > 7:
        wait_score += 0.35
        reasons.append(f"price_rising={price_chg:.1f}%/24h + inventory_falling={inv_chg:.0f} with {du:.0f}d_to_event")

    # Signal 3: High relist rate (sellers repricing, market hasn't cleared)
    if relist_rate and relist_rate > 30 and du > 10:
        wait_score += 0.2
        reasons.append(f"relist_rate={relist_rate:.0f}% suggests sellers still repositioning")

    # Signal 4: OVERSUPPLY — too many listings, prices still falling
    if cls == "OVERSUPPLY" and du > 14:
        wait_score += 0.3
        reasons.append(f"market_classification=OVERSUPPLY with {du:.0f}d_to_event (prices likely still falling)")

    if wait_score >= 0.4:
        confidence = min(0.92, wait_score)
        return "WAIT", round(confidence, 3), reasons

    # ── MONITOR (default) ────────────────────────────────────────────────────

    if not reasons:
        reasons.append("no strong buy or wait signal detected")

    if cls == "STABLE":
        reasons.append("market_classification=STABLE")
    elif cls == "REPRICING":
        reasons.append(f"market_classification=REPRICING — price movement without direction")

    monitor_confidence = 0.5
    if du <= 3:
        monitor_confidence = 0.6
        reasons.append(f"event in {du:.0f}d — watch floor price closely")

    return "MONITOR", monitor_confidence, reasons


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

async def compute_buy_signal(event_id: int, db: AsyncSession) -> dict:
    now_utc = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)

    # ── Fetch event metadata ─────────────────────────────────────────────────
    event_row = (await db.execute(text("""
        SELECT id, title, artist, event_date FROM events WHERE id = :eid
    """), {"eid": event_id})).fetchone()

    if not event_row:
        return {"event_id": event_id, "error": "event not found"}

    event_date = event_row.event_date
    if event_date and hasattr(event_date, "tzinfo") and event_date.tzinfo is not None:
        event_date_naive = event_date.replace(tzinfo=None)
    else:
        event_date_naive = event_date

    days_until = None
    if event_date_naive:
        delta = event_date_naive - now_naive
        days_until = round(delta.total_seconds() / 86400, 1)

    # ── Fetch latest market intelligence ────────────────────────────────────
    intel_row = (await db.execute(text("""
        SELECT signal, current_low_ask, current_median_ask, current_listings,
               price_delta_24h, price_delta_pct_24h, inventory_delta_24h,
               seller_aggression, capitulation_score, opportunity_score,
               marketplace_metrics, section_metrics, seller_behavior
        FROM market_intelligence
        WHERE event_id = :eid
        ORDER BY computed_at DESC
        LIMIT 1
    """), {"eid": event_id})).fetchone()

    # ── Fetch price history for trend context ───────────────────────────────
    history_rows = (await db.execute(text("""
        SELECT bucket_ts, low_ask, median_ask, listing_count
        FROM event_price_history_agg
        WHERE railway_event_id = :eid
          AND bucket_ts >= :since_7d
        ORDER BY bucket_ts DESC
        LIMIT 168
    """), {"eid": event_id, "since_7d": now_naive - timedelta(days=7)})).fetchall()

    # ── Compute lifecycle ────────────────────────────────────────────────────
    lifecycle = await compute_lifecycle(event_id, db)

    # ── Extract metrics ──────────────────────────────────────────────────────
    if intel_row:
        classification = intel_row.signal  # signal from intelligence_engine maps to classification names
        price_delta_pct_24h = _f(intel_row.price_delta_pct_24h)
        inventory_delta_24h = _f(intel_row.inventory_delta_24h)
        capitulation_score = _f(intel_row.capitulation_score)
        seller_aggression = _f(intel_row.seller_aggression)
        current_low_ask = _f(intel_row.current_low_ask)
        current_median_ask = _f(intel_row.current_median_ask)
        current_listings = intel_row.current_listings
        opportunity_score = _f(intel_row.opportunity_score)
    else:
        classification = None
        price_delta_pct_24h = None
        inventory_delta_24h = None
        capitulation_score = None
        seller_aggression = None
        current_low_ask = None
        current_median_ask = None
        current_listings = None
        opportunity_score = None

    lifecycle_summary = lifecycle.get("summary", {})
    absorption_rate = lifecycle_summary.get("absorption_rate")
    relist_rate = lifecycle_summary.get("relist_rate")
    repricing_rate = lifecycle_summary.get("repricing_rate")
    churn_rate = lifecycle_summary.get("churn_rate")
    seller_cap_lifecycle = lifecycle_summary.get("seller_capitulation_score")

    # Lifecycle attribution: "matched" only when SOLD_AFTER_RELIST events exist
    # (post-show validated outcome). Otherwise "assumed" (heuristic only).
    sold_after_relist = lifecycle_summary.get("sold_after_relist_count", 0) or 0
    lifecycle_attribution = "matched" if sold_after_relist > 0 else "assumed"

    # Blend capitulation from market_intelligence + lifecycle
    if capitulation_score is not None and seller_cap_lifecycle is not None:
        blended_cap = capitulation_score * 0.6 + seller_cap_lifecycle * 0.4
    else:
        blended_cap = capitulation_score or seller_cap_lifecycle

    # ── Price trend context from history ────────────────────────────────────
    price_trend_note = None
    if len(history_rows) >= 4:
        recent_prices = [_f(r.low_ask) for r in history_rows[:4] if r.low_ask is not None]
        older_prices = [_f(r.low_ask) for r in history_rows[-4:] if r.low_ask is not None]
        if recent_prices and older_prices:
            recent_avg = sum(recent_prices) / len(recent_prices)
            older_avg = sum(older_prices) / len(older_prices)
            if older_avg > 0:
                trend_pct = (recent_avg - older_avg) / older_avg * 100
                if trend_pct < -10:
                    price_trend_note = f"7d floor trend: -{abs(trend_pct):.0f}% (falling)"
                elif trend_pct > 10:
                    price_trend_note = f"7d floor trend: +{trend_pct:.0f}% (rising)"
                else:
                    price_trend_note = f"7d floor trend: {trend_pct:+.0f}% (stable)"

    # ── Map classification from intelligence signal to buy_window vocabulary ─
    # intelligence_engine signals: loosening/tightening/deepening/stable/capitulating/mixed/unknown
    # buy_window classification: CAPITULATION/DEMAND/OVERSUPPLY/REPRICING/STABLE
    signal_map = {
        "capitulating": "CAPITULATION",
        "loosening":    "OVERSUPPLY",
        "tightening":   "DEMAND",
        "deepening":    "DEMAND",
        "stable":       "STABLE",
        "mixed":        "REPRICING",
        "unknown":      None,
    }
    mapped_classification = signal_map.get((classification or "").lower())

    # For confidence we use the opportunity_score as a proxy
    cls_confidence = opportunity_score or 0.5

    # ── Compute signal ───────────────────────────────────────────────────────
    signal, confidence, reasons = _compute_signal(
        days_until=days_until,
        classification=mapped_classification,
        classification_confidence=cls_confidence,
        price_delta_pct_24h=price_delta_pct_24h,
        inventory_delta_24h=inventory_delta_24h,
        capitulation_score=blended_cap,
        seller_aggression=seller_aggression,
        absorption_rate=absorption_rate,
        relist_rate=relist_rate,
        repricing_rate=repricing_rate,
        churn_rate=churn_rate,
        total_listings=current_listings,
    )

    # ── Apply lifecycle heuristic confidence cap (Task 8) ────────────────────
    # Cap BUY/WAIT confidence at 0.75 when lifecycle data is heuristic-only.
    # High confidence (>0.75) is only valid when SOLD_AFTER_RELIST outcomes exist
    # (lifecycle_attribution="matched"), meaning post-show outcomes validated the model.
    _HEURISTIC_CAP = 0.75
    if lifecycle_attribution == "assumed" and confidence > _HEURISTIC_CAP:
        confidence = _HEURISTIC_CAP

    # ── Build explanation ────────────────────────────────────────────────────
    explanation_parts = []
    if days_until is not None:
        explanation_parts.append(f"Event is {days_until:.1f} days away.")
    if current_low_ask:
        explanation_parts.append(f"Current floor: ${current_low_ask:.0f}.")
    if price_delta_pct_24h is not None:
        direction = "dropped" if price_delta_pct_24h < 0 else "rose"
        explanation_parts.append(f"Floor {direction} {abs(price_delta_pct_24h):.1f}% in 24h.")
    if mapped_classification:
        explanation_parts.append(f"Market is classified as {mapped_classification}.")
    if absorption_rate is not None:
        explanation_parts.append(f"Absorption rate: {absorption_rate:.0f}% of listings have disappeared.")
    if price_trend_note:
        explanation_parts.append(price_trend_note + ".")
    explanation_parts.extend(reasons)

    # State lifecycle attribution in explanation
    lifecycle_note = (
        f"Lifecycle attribution: {lifecycle_attribution} "
        f"({'validated post-show outcomes' if lifecycle_attribution == 'matched' else 'heuristic inference, no validated post-show outcomes'})."
    )
    explanation_parts.append(lifecycle_note)
    explanation = " ".join(explanation_parts)

    return {
        "event_id": event_id,
        "event_title": event_row.title,
        "event_date": event_row.event_date.isoformat() if event_row.event_date else None,
        "days_until_event": days_until,
        "computed_at": now_utc.isoformat(),
        "signal": signal,
        "confidence": confidence,
        "explanation": explanation,
        "supporting_metrics": {
            "classification": mapped_classification,
            "classification_confidence": round(cls_confidence, 3) if cls_confidence else None,
            "price_delta_pct_24h": price_delta_pct_24h,
            "inventory_delta_24h": inventory_delta_24h,
            "capitulation_score": round(blended_cap, 3) if blended_cap is not None else None,
            "seller_aggression": round(seller_aggression, 3) if seller_aggression is not None else None,
            "absorption_rate": absorption_rate,
            "relist_rate": relist_rate,
            "repricing_rate": repricing_rate,
            "churn_rate": churn_rate,
            "current_floor": current_low_ask,
            "current_median": current_median_ask,
            "current_listings": current_listings,
            "price_trend_note": price_trend_note,
        },
        "lifecycle_summary": lifecycle_summary,
        "lifecycle_attribution": lifecycle_attribution,
    }
