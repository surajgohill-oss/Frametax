"""
artist_profile.py — ArtistProfile computation framework.

Computes per-event intelligence metrics from the combined history source
(event_price_history_agg + listing_snapshots), then aggregates into an
ArtistProfile across all tracked events for an artist.

Entry points:
  compute_event_metrics(event_id, event_dt, db) → EventIntelligence
  build_artist_profile(artist, event_metrics)   → ArtistProfile
  get_artist_profile(artist, db)                → ArtistProfile (full pipeline)

All timing is expressed as hours_before_event (positive = before, 0 = showtime,
negative = after event has started).
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Minimum history (hours) before an event is included in profile averaging.
MIN_ELIGIBLE_HOURS = 24
# Minimum events with ≥MIN_ELIGIBLE_HOURS to produce a profile.
MIN_EVENTS_FOR_PROFILE = 2

# Inventory collapse threshold: inventory must drop to this fraction of peak.
COLLAPSE_THRESHOLD = 0.25


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class TimingPoint:
    value: Optional[float]       # price or ticket count at this moment
    hbe: Optional[float]         # hours before event (positive = before)
    ts: Optional[str]            # ISO timestamp
    label: Optional[str]         # human label: "early" / "within_week" / etc.


@dataclass
class MarketplaceIntel:
    lowest_floor_mp: Optional[str]
    lowest_floor_val: Optional[float]
    steepest_decline_mp: Optional[str]
    steepest_decline_drop: Optional[float]
    all_floors: dict = field(default_factory=dict)


@dataclass
class EventIntelligence:
    event_id: int
    label: str
    event_dt: str
    status: str
    data_quality: str                    # "full" | "agg_only_limited" | "snapshot_only" | "insufficient"
    history_hours: float
    series_points: int

    floor: TimingPoint = field(default_factory=lambda: TimingPoint(None,None,None,None))
    median: TimingPoint = field(default_factory=lambda: TimingPoint(None,None,None,None))
    inventory_peak: TimingPoint = field(default_factory=lambda: TimingPoint(None,None,None,None))
    inventory_collapse: TimingPoint = field(default_factory=lambda: TimingPoint(None,None,None,None))

    largest_price_drop: dict = field(default_factory=dict)
    largest_inv_drop: dict = field(default_factory=dict)

    marketplace: MarketplaceIntel = field(
        default_factory=lambda: MarketplaceIntel(None,None,None,None)
    )
    absorption: str = "unknown"


@dataclass
class ArtistProfile:
    artist: str
    events_analyzed: int
    events_eligible: int
    confidence: str          # "high" (≥5 events) | "medium" (3-4) | "low" (<3)

    # Averaged timing (hours before event)
    avg_floor_hbe: Optional[float]
    avg_median_hbe: Optional[float]
    avg_inv_peak_hbe: Optional[float]
    avg_inv_collapse_hbe: Optional[float]
    avg_largest_price_drop_hbe: Optional[float]
    avg_largest_inv_drop_hbe: Optional[float]

    # Timing labels
    floor_timing_label: str
    median_timing_label: str
    collapse_timing_label: str

    # Demand signature
    avg_peak_inventory: Optional[int]
    avg_floor_price: Optional[float]

    # Marketplace
    dominant_marketplace: Optional[str]
    marketplace_ranking: list = field(default_factory=list)

    # Absorption
    dominant_absorption: str = "unknown"
    absorption_breakdown: dict = field(default_factory=dict)

    # Demand signature
    demand_signature: str = "unknown"  # "ultra_high" | "high" | "medium" | "low"

    # Per-event breakdown for audit
    per_event: list = field(default_factory=list)

    generated_at: str = ""

    def to_dict(self):
        return asdict(self)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _hbe_label(hbe: Optional[float]) -> str:
    if hbe is None: return "unknown"
    if hbe < 0:     return "after_event"
    if hbe < 6:     return "day_of"
    if hbe < 24:    return "day_before"
    if hbe < 72:    return "within_3d"
    if hbe < 168:   return "within_week"
    if hbe < 336:   return "within_2w"
    return "early"


def _hours_before(ts: datetime, event_dt: datetime) -> float:
    return (event_dt - ts).total_seconds() / 3600


def _demand_signature(avg_floor: Optional[float], avg_peak_inv: Optional[int]) -> str:
    if avg_floor is None:
        return "unknown"
    if avg_floor < 100 and (avg_peak_inv or 0) > 10000:
        return "ultra_high"
    if avg_floor < 200:
        return "high"
    if avg_floor < 500:
        return "medium"
    return "low"


# ── Core computation ──────────────────────────────────────────────────────────

async def compute_event_metrics(
    event_id: int,
    event_dt: datetime,
    label: str,
    status: str,
    db: AsyncSession,
) -> EventIntelligence:
    """
    Compute EventIntelligence for one event.
    Pulls combined 1h series (agg + live snapshots, live wins on overlap).
    """
    event_dt = event_dt.replace(tzinfo=timezone.utc) if event_dt.tzinfo is None else event_dt

    # ── Pull 1h agg series ───────────────────────────────────────────────────
    agg_rows = (await db.execute(text("""
        SELECT bucket_ts, low_ask, median_ask, listing_count, ticket_count
        FROM event_price_history_agg
        WHERE railway_event_id = :eid AND bucket_size = '1h'
        ORDER BY bucket_ts ASC
    """), {"eid": event_id})).fetchall()
    agg_map = {r[0]: r for r in agg_rows}

    # ── Pull 1h live snapshot series ─────────────────────────────────────────
    live_rows = (await db.execute(text("""
        SELECT
            to_timestamp(floor(extract(epoch from snapshot_at)/3600)*3600)::timestamp AS bucket,
            MIN(price),
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price),
            COUNT(DISTINCT listing_id),
            SUM(quantity)
        FROM listing_snapshots
        WHERE event_id = :eid AND price > 0
        GROUP BY 1 ORDER BY 1
    """), {"eid": event_id})).fetchall()
    live_map = {r[0]: r for r in live_rows}

    has_live    = len(live_map) > 0
    has_archive = len(agg_map) > 0

    # Merge: live overwrites agg for same bucket
    merged = {**agg_map, **live_map}
    if not merged:
        return EventIntelligence(
            event_id=event_id, label=label, event_dt=event_dt.isoformat(),
            status=status, data_quality="insufficient",
            history_hours=0, series_points=0,
        )

    series = sorted(merged.items())  # list of (naive_datetime, row_tuple)
    ts_list = [ts.replace(tzinfo=timezone.utc) for ts, _ in series]
    history_hours = (max(ts_list) - min(ts_list)).total_seconds() / 3600

    if has_live and has_archive:
        data_quality = "full"
    elif has_archive and not has_live:
        data_quality = "agg_only_limited"
    else:
        data_quality = "snapshot_only"

    # row layout: (bucket_ts, low_ask, median_ask, listing_count, ticket_count)
    low_asks = [(ts.replace(tzinfo=timezone.utc), float(row[1])) for ts, row in series if row[1] and float(row[1]) > 0]
    medians  = [(ts.replace(tzinfo=timezone.utc), float(row[2])) for ts, row in series if row[2] and float(row[2]) > 0]
    tickets  = [(ts.replace(tzinfo=timezone.utc), int(row[4]))   for ts, row in series if row[4] and int(row[4]) > 0]

    intel = EventIntelligence(
        event_id=event_id, label=label, event_dt=event_dt.isoformat(),
        status=status, data_quality=data_quality,
        history_hours=round(history_hours, 1),
        series_points=len(series),
    )

    # ── Floor minimum ────────────────────────────────────────────────────────
    if low_asks:
        min_ts, min_val = min(low_asks, key=lambda x: x[1])
        intel.floor = TimingPoint(
            value=round(min_val, 2),
            hbe=round(_hours_before(min_ts, event_dt), 1),
            ts=min_ts.isoformat(),
            label=_hbe_label(_hours_before(min_ts, event_dt)),
        )

    # ── Median minimum ───────────────────────────────────────────────────────
    if medians:
        min_ts, min_val = min(medians, key=lambda x: x[1])
        intel.median = TimingPoint(
            value=round(min_val, 2),
            hbe=round(_hours_before(min_ts, event_dt), 1),
            ts=min_ts.isoformat(),
            label=_hbe_label(_hours_before(min_ts, event_dt)),
        )

    # ── Inventory peak ───────────────────────────────────────────────────────
    if tickets:
        peak_ts, peak_val = max(tickets, key=lambda x: x[1])
        intel.inventory_peak = TimingPoint(
            value=peak_val,
            hbe=round(_hours_before(peak_ts, event_dt), 1),
            ts=peak_ts.isoformat(),
            label=_hbe_label(_hours_before(peak_ts, event_dt)),
        )

        # ── Inventory collapse (first point ≤25% of peak after peak) ─────────
        threshold = peak_val * COLLAPSE_THRESHOLD
        after_peak = [(ts, v) for ts, v in tickets if ts >= peak_ts]
        for ts, v in after_peak:
            if v <= threshold:
                hbe = _hours_before(ts, event_dt)
                intel.inventory_collapse = TimingPoint(
                    value=v, hbe=round(hbe, 1),
                    ts=ts.isoformat(), label=_hbe_label(hbe),
                )
                break

    # ── Largest price drop (6h rolling window) ───────────────────────────────
    max_drop = max_drop_start = max_drop_end = None
    for i in range(len(low_asks) - 1):
        for j in range(i+1, min(i+7, len(low_asks))):
            drop = low_asks[i][1] - low_asks[j][1]
            window_h = (low_asks[j][0] - low_asks[i][0]).total_seconds() / 3600
            if drop > (max_drop or 0) and window_h <= 6:
                max_drop, max_drop_start, max_drop_end = drop, low_asks[i][0], low_asks[j][0]

    if max_drop_start:
        intel.largest_price_drop = {
            "amount": round(max_drop, 2),
            "from_hbe": round(_hours_before(max_drop_start, event_dt), 1),
            "to_hbe":   round(_hours_before(max_drop_end,   event_dt), 1),
            "from_ts":  max_drop_start.isoformat(),
        }

    # ── Largest inventory drop (6h rolling window) ───────────────────────────
    max_inv_drop = max_inv_start = max_inv_end = None
    for i in range(len(tickets) - 1):
        for j in range(i+1, min(i+7, len(tickets))):
            drop = tickets[i][1] - tickets[j][1]
            window_h = (tickets[j][0] - tickets[i][0]).total_seconds() / 3600
            if drop > (max_inv_drop or 0) and window_h <= 6:
                max_inv_drop, max_inv_start, max_inv_end = drop, tickets[i][0], tickets[j][0]

    if max_inv_start:
        intel.largest_inv_drop = {
            "tickets": round(max_inv_drop),
            "from_hbe": round(_hours_before(max_inv_start, event_dt), 1),
            "to_hbe":   round(_hours_before(max_inv_end,   event_dt), 1),
            "from_ts":  max_inv_start.isoformat(),
        }

    # ── Per-marketplace floors ────────────────────────────────────────────────
    mp_floor_rows = (await db.execute(text("""
        SELECT m.slug, MIN(ls.price)
        FROM listing_snapshots ls
        JOIN marketplaces m ON m.id = ls.marketplace_id
        WHERE ls.event_id = :eid AND ls.price > 0
        GROUP BY m.slug
    """), {"eid": event_id})).fetchall()
    mp_floors = {r[0]: float(r[1]) for r in mp_floor_rows}

    if mp_floors:
        lowest_mp = min(mp_floors, key=mp_floors.get)
        intel.marketplace = MarketplaceIntel(
            lowest_floor_mp=lowest_mp,
            lowest_floor_val=round(mp_floors[lowest_mp], 2),
            steepest_decline_mp=None,
            steepest_decline_drop=None,
            all_floors={k: round(v, 2) for k, v in mp_floors.items()},
        )

        # Steepest decline per marketplace
        mp_price_rows = (await db.execute(text("""
            SELECT m.slug,
                   MIN(ls.price) as min_p,
                   (SELECT price FROM listing_snapshots ls2
                    WHERE ls2.event_id = :eid AND ls2.marketplace_id = ls.marketplace_id
                    ORDER BY ls2.snapshot_at ASC LIMIT 1) as first_p
            FROM listing_snapshots ls
            JOIN marketplaces m ON m.id = ls.marketplace_id
            WHERE ls.event_id = :eid AND ls.price > 0
            GROUP BY m.slug, ls.marketplace_id
        """), {"eid": event_id})).fetchall()
        best_slug = best_drop = None
        for slug, min_p, first_p in mp_price_rows:
            if first_p and min_p:
                drop = float(first_p) - float(min_p)
                if drop > (best_drop or 0):
                    best_drop, best_slug = drop, slug
        intel.marketplace.steepest_decline_mp = best_slug
        intel.marketplace.steepest_decline_drop = round(best_drop, 2) if best_drop else None

    # ── Absorption classification ─────────────────────────────────────────────
    collapse_hbe = intel.inventory_collapse.hbe
    peak_hbe = intel.inventory_peak.hbe

    if data_quality == "agg_only_limited":
        intel.absorption = "data_limited"
    elif collapse_hbe is not None:
        if collapse_hbe > 48:
            intel.absorption = "early_sellout"
        elif collapse_hbe > 12:
            intel.absorption = "pre_event_sellout"
        elif collapse_hbe > 0:
            intel.absorption = "day_of_sellout"
        else:
            intel.absorption = "post_event_ghost"
    elif tickets:
        first_inv = tickets[0][1]
        last_inv  = tickets[-1][1]
        if last_inv < first_inv * 0.50:
            intel.absorption = "partial_absorption"
        elif last_inv > first_inv * 0.90:
            intel.absorption = "stagnant"
        else:
            intel.absorption = "gradual_decline"
    else:
        intel.absorption = "unknown"

    return intel


# ── Profile builder ───────────────────────────────────────────────────────────

def build_artist_profile(artist: str, metrics: list[EventIntelligence]) -> ArtistProfile:
    """Aggregate EventIntelligence list into ArtistProfile."""
    eligible = [
        m for m in metrics
        if m.data_quality != "insufficient"
        and m.history_hours >= MIN_ELIGIBLE_HOURS
        and m.data_quality != "agg_only_limited"
    ]
    # Include agg_only at lower weight if not enough eligible
    if len(eligible) < MIN_EVENTS_FOR_PROFILE:
        eligible = [m for m in metrics if m.history_hours >= MIN_ELIGIBLE_HOURS]

    n_eligible = len(eligible)
    confidence = "high" if n_eligible >= 5 else ("medium" if n_eligible >= 3 else "low")

    def _avg(vals):
        v = [x for x in vals if x is not None]
        return round(sum(v)/len(v), 1) if v else None

    mp_counter = Counter(
        m.marketplace.lowest_floor_mp for m in eligible
        if m.marketplace and m.marketplace.lowest_floor_mp
    )
    absorptions = Counter(
        m.absorption for m in eligible
        if m.absorption not in ("unknown", "data_limited")
    )

    avg_floor_hbe   = _avg([m.floor.hbe for m in eligible])
    avg_median_hbe  = _avg([m.median.hbe for m in eligible])
    avg_peak_hbe    = _avg([m.inventory_peak.hbe for m in eligible])
    avg_collapse_hbe = _avg([m.inventory_collapse.hbe for m in eligible])
    avg_price_drop_hbe = _avg([m.largest_price_drop.get("from_hbe") for m in eligible])
    avg_inv_drop_hbe   = _avg([m.largest_inv_drop.get("from_hbe") for m in eligible])

    avg_peak_inv = None
    peak_vals = [m.inventory_peak.value for m in eligible if m.inventory_peak.value]
    if peak_vals:
        avg_peak_inv = int(sum(peak_vals)/len(peak_vals))

    avg_floor_price = None
    floor_vals = [m.floor.value for m in eligible if m.floor.value and m.floor.value > 30]
    if floor_vals:
        avg_floor_price = round(sum(floor_vals)/len(floor_vals), 2)

    return ArtistProfile(
        artist=artist,
        events_analyzed=len(metrics),
        events_eligible=n_eligible,
        confidence=confidence,

        avg_floor_hbe=avg_floor_hbe,
        avg_median_hbe=avg_median_hbe,
        avg_inv_peak_hbe=avg_peak_hbe,
        avg_inv_collapse_hbe=avg_collapse_hbe,
        avg_largest_price_drop_hbe=avg_price_drop_hbe,
        avg_largest_inv_drop_hbe=avg_inv_drop_hbe,

        floor_timing_label=_hbe_label(avg_floor_hbe),
        median_timing_label=_hbe_label(avg_median_hbe),
        collapse_timing_label=_hbe_label(avg_collapse_hbe),

        avg_peak_inventory=avg_peak_inv,
        avg_floor_price=avg_floor_price,

        dominant_marketplace=mp_counter.most_common(1)[0][0] if mp_counter else None,
        marketplace_ranking=[mp for mp, _ in mp_counter.most_common()],

        dominant_absorption=absorptions.most_common(1)[0][0] if absorptions else "unknown",
        absorption_breakdown=dict(absorptions),

        demand_signature=_demand_signature(avg_floor_price, avg_peak_inv),
        per_event=[asdict(m) for m in metrics],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ── Full pipeline ─────────────────────────────────────────────────────────────

async def get_artist_profile(artist: str, db: AsyncSession) -> ArtistProfile:
    """
    Full pipeline: find all events for artist → compute metrics → build profile.
    """
    rows = (await db.execute(text("""
        SELECT id, title, event_date, status
        FROM events
        WHERE artist ILIKE :artist
        ORDER BY event_date ASC
    """), {"artist": f"%{artist}%"})).fetchall()

    metrics = []
    for event_id, title, event_date, status in rows:
        event_dt = event_date if event_date.tzinfo else event_date.replace(tzinfo=timezone.utc)
        m = await compute_event_metrics(event_id, event_dt, title, status, db)
        metrics.append(m)
        logger.info("artist_profile: event_id=%d label='%s' quality=%s abs=%s",
                    event_id, title, m.data_quality, m.absorption)

    return build_artist_profile(artist, metrics)
