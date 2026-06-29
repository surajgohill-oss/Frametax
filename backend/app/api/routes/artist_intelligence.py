"""
GET /api/intelligence/artist/{artist_name}

Returns ArtistProfile computed from the combined history source
(event_price_history_agg + listing_snapshots).

Events with data_quality "agg_only_limited" or "insufficient" are:
  - included in per_event for full audit transparency
  - excluded from all profile averages
  - listed under excluded_events with reason

No BUY/WAIT/MONITOR signals are emitted here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.services.artist_profile import (
    compute_event_metrics,
    build_artist_profile,
    EventIntelligence,
)

router = APIRouter(prefix="/intelligence", tags=["artist-intelligence"])

_EXCLUDE_QUALITIES = {"agg_only_limited", "insufficient"}


@router.get("/artist/{artist_name}")
async def get_artist_profile_endpoint(
    artist_name: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Compute and return an ArtistProfile for all DB events matching artist_name.

    Returns:
      - profile summary (averages, marketplace ranking, absorption)
      - per_event audit list (all events, including excluded)
      - excluded_events list with reason

    Matching is case-insensitive ILIKE on the events.artist column.
    """
    import re
    normalized_name = re.sub(r"[-_]+", " ", artist_name).strip()

    rows = (await db.execute(text("""
        SELECT id, title, artist, event_date, status
        FROM events
        WHERE artist ILIKE :pattern
        ORDER BY event_date ASC
    """), {"pattern": f"%{normalized_name}%"})).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No events found for artist matching '{artist_name}'",
        )

    metrics: list[EventIntelligence] = []
    for event_id, title, artist, event_date, status in rows:
        event_dt = event_date if event_date.tzinfo else event_date.replace(tzinfo=timezone.utc)
        m = await compute_event_metrics(event_id, event_dt, title, status, db)
        metrics.append(m)

    profile = build_artist_profile(artist_name, metrics)

    # ── Build excluded_events list ────────────────────────────────────────────
    excluded = []
    for m in metrics:
        if m.data_quality in _EXCLUDE_QUALITIES:
            reason = _exclusion_reason(m)
            excluded.append({
                "event_id":    m.event_id,
                "label":       m.label,
                "event_dt":    m.event_dt,
                "data_quality": m.data_quality,
                "history_hours": m.history_hours,
                "reason":      reason,
            })

    # ── Build response ────────────────────────────────────────────────────────
    return {
        "artist":           profile.artist,
        "query":            artist_name,
        "generated_at":     profile.generated_at,
        "events_analyzed":  profile.events_analyzed,
        "events_eligible":  profile.events_eligible,
        "events_excluded":  len(excluded),
        "confidence":       profile.confidence,

        "timing_profile": {
            "avg_floor_hbe":               profile.avg_floor_hbe,
            "avg_median_hbe":              profile.avg_median_hbe,
            "avg_inv_peak_hbe":            profile.avg_inv_peak_hbe,
            "avg_inv_collapse_hbe":        profile.avg_inv_collapse_hbe,
            "avg_largest_price_drop_hbe":  profile.avg_largest_price_drop_hbe,
            "avg_largest_inv_drop_hbe":    profile.avg_largest_inv_drop_hbe,
            "floor_timing_label":          profile.floor_timing_label,
            "median_timing_label":         profile.median_timing_label,
            "collapse_timing_label":       profile.collapse_timing_label,
        },

        "demand": {
            "avg_peak_inventory": profile.avg_peak_inventory,
            "avg_floor_price":    profile.avg_floor_price,
            "demand_signature":   profile.demand_signature,
        },

        "marketplace": {
            "dominant":  profile.dominant_marketplace,
            "ranking":   profile.marketplace_ranking,
        },

        "absorption": {
            "dominant":   profile.dominant_absorption,
            "breakdown":  profile.absorption_breakdown,
        },

        "excluded_events": excluded,

        "per_event": [
            {
                "event_id":      m.event_id,
                "label":         m.label,
                "event_dt":      m.event_dt,
                "status":        m.status,
                "data_quality":  m.data_quality,
                "history_hours": m.history_hours,
                "series_points": m.series_points,
                "floor": {
                    "value": m.floor.value,
                    "hbe":   m.floor.hbe,
                    "label": m.floor.label,
                } if m.floor.value is not None else None,
                "inventory_peak": {
                    "value": m.inventory_peak.value,
                    "hbe":   m.inventory_peak.hbe,
                    "label": m.inventory_peak.label,
                } if m.inventory_peak.value is not None else None,
                "inventory_collapse": {
                    "value": m.inventory_collapse.value,
                    "hbe":   m.inventory_collapse.hbe,
                    "label": m.inventory_collapse.label,
                } if m.inventory_collapse.value is not None else None,
                "marketplace_floors":  m.marketplace.all_floors if m.marketplace else {},
                "lowest_floor_mp":     m.marketplace.lowest_floor_mp if m.marketplace else None,
                "absorption":          m.absorption,
                "largest_price_drop":  m.largest_price_drop,
                "largest_inv_drop":    m.largest_inv_drop,
            }
            for m in metrics
        ],
    }


def _exclusion_reason(m: EventIntelligence) -> str:
    if m.data_quality == "insufficient":
        return f"insufficient data — {m.series_points} series points, {m.history_hours}h history"
    if m.data_quality == "agg_only_limited":
        return (
            "agg_only_limited — no listing_snapshots; marketplace floors unavailable; "
            "absorption classification unreliable (possible UTC timezone artifact)"
        )
    return m.data_quality
