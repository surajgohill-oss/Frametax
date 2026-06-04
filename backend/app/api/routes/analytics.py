import dataclasses
import statistics
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from typing import Optional

from app.database import get_db
from app.models import Event, Listing, ListingSnapshot, Marketplace, ScraperErrorLog
from app.services.analytics import get_data_audit, get_event_analytics, get_venue_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def global_summary(db: AsyncSession = Depends(get_db)):
    total_listings = (await db.execute(select(func.count()).select_from(Listing).where(Listing.is_active == True))).scalar_one()
    avg_ask = (await db.execute(select(func.avg(Listing.price)).where(Listing.is_active == True))).scalar_one()
    since = datetime.utcnow() - timedelta(hours=24)
    recent_errors = (await db.execute(select(func.count()).select_from(ScraperErrorLog).where(ScraperErrorLog.timestamp >= since))).scalar_one()
    return {"total_listings": total_listings, "avg_lowest_ask": float(avg_ask) if avg_ask else None, "recent_errors": recent_errors}


@router.get("/events/{event_id}/summary")
async def event_summary(event_id: int, marketplace: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Marketplace).where(Marketplace.is_active == True))
    mps = result.scalars().all()
    if marketplace: mps = [m for m in mps if m.slug == marketplace]
    summaries = []
    for mp in mps:
        result = await db.execute(select(Listing).where(and_(Listing.event_id == event_id, Listing.marketplace_id == mp.id, Listing.is_active == True)))
        listings = result.scalars().all()
        if not listings: continue
        prices = [float(l.price) for l in listings]
        section_map: dict[str, list] = {}
        for l in listings: section_map.setdefault(l.section_id or l.section or "unknown", []).append(l)
        summaries.append({
            "event_id": event_id, "marketplace_slug": mp.slug, "total_listings": len(listings),
            "total_inventory": sum(l.quantity for l in listings), "lowest_ask": min(prices),
            "median_price": statistics.median(prices),
            "sections": [{"section_id": sid, "display_name": sl[0].section or sid, "listing_count": len(sl), "lowest_ask": min(float(l.price) for l in sl), "marketplace_slug": mp.slug} for sid, sl in section_map.items()],
        })
    return summaries


@router.get("/events/{event_id}/price-history")
async def price_history(event_id: int, hours: int = Query(168, ge=1, le=2160), marketplace: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    mp_filter = []
    if marketplace:
        mp_result = await db.execute(select(Marketplace).where(Marketplace.slug == marketplace))
        mp = mp_result.scalar_one_or_none()
        if mp: mp_filter = [ListingSnapshot.marketplace_id == mp.id]
    result = await db.execute(select(ListingSnapshot).where(and_(ListingSnapshot.event_id == event_id, ListingSnapshot.snapshot_at >= since, *mp_filter)).order_by(ListingSnapshot.snapshot_at))
    snapshots = result.scalars().all()
    mp_names = {m.id: m.slug for m in (await db.execute(select(Marketplace))).scalars().all()}
    buckets: dict = {}
    inv: dict = {}
    for s in snapshots:
        mp_slug = mp_names.get(s.marketplace_id, "unknown")
        ts = s.snapshot_at.replace(minute=0, second=0, microsecond=0).isoformat()
        k = (ts, mp_slug)
        buckets.setdefault(k, []).append(float(s.price))
        inv[k] = inv.get(k, 0) + s.quantity
    return [{"ts": ts, "lowest_ask": min(prices), "inventory": inv.get((ts, mp_slug), 0), "marketplace_slug": mp_slug} for (ts, mp_slug), prices in sorted(buckets.items())]


@router.get("/events/{event_id}/heatmap")
async def heatmap_data(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(and_(Listing.event_id == event_id, Listing.is_active == True)))
    listings = result.scalars().all()
    mp_names = {m.id: m.slug for m in (await db.execute(select(Marketplace))).scalars().all()}
    section_data: dict = {}
    for l in listings:
        key = l.section_id or l.section or "unknown"
        if key not in section_data: section_data[key] = {"prices": [], "inventory": 0}
        section_data[key]["prices"].append(float(l.price))
        section_data[key]["inventory"] += l.quantity
    return [{"section_id": sid, "lowest_ask": min(d["prices"]) if d["prices"] else None, "inventory": d["inventory"]} for sid, d in section_data.items()]


@router.get("/events/{event_id}/inventory-summary")
async def inventory_summary(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Phase 1E-F: Normalized inventory summary for one event.

    Returns:
      raw_listings              – count of active listing rows across all marketplaces
      raw_tickets               – sum(quantity) before any dedup
      mirror_listings           – raw rows whose (section_id, row, qty) key appears on 2+ MPs
      exclusive_listings        – raw_listings - mirror_listings
      mirror_rate               – mirror_listings / raw_listings
      unique_tickets_available  – primary metric: distinct purchasable seats after
                                  (1) intra-MP sp[]-aware split-option dedup
                                  (2) cross-MP mirror dedup (each seat counted once)
      per_marketplace           – per-slug breakdown
    """
    from collections import defaultdict

    result = await db.execute(
        select(Listing, Marketplace.slug)
        .join(Marketplace, Listing.marketplace_id == Marketplace.id)
        .where(Listing.event_id == event_id, Listing.is_active == True)
    )
    rows = result.all()

    if not rows:
        return {
            "event_id": event_id,
            "raw_listings": 0, "raw_tickets": 0,
            "mirror_listings": 0, "exclusive_listings": 0, "mirror_rate": 0.0,
            "unique_tickets_available": 0,
            "per_marketplace": [],
        }

    def normalized_price(listing: Listing, slug: str) -> float:
        if slug == "tickpick":
            return float(listing.price)
        if slug == "gametime":
            return float(listing.all_in_price) if listing.all_in_price else float(listing.price) * 1.15
        if slug == "stubhub":
            return float(listing.all_in_price) if listing.all_in_price else float(listing.price) * 1.27
        if slug == "seatgeek":
            return float(listing.all_in_price) if listing.all_in_price else float(listing.price) * 1.20
        return float(listing.price) * 1.20

    anchor_groups: dict[tuple, list] = defaultdict(list)
    per_mp_raw: dict[str, dict] = defaultdict(lambda: {"listing_count": 0, "quantity_sum": 0, "prices": []})

    for listing, slug in rows:
        per_mp_raw[slug]["listing_count"] += 1
        per_mp_raw[slug]["quantity_sum"] += listing.quantity
        per_mp_raw[slug]["prices"].append(normalized_price(listing, slug))
        anchor_groups[(slug, listing.section_id or "", listing.row or "")].append(listing)

    def _dedup_anchor(slug: str, listings_at_anchor: list) -> list[tuple[int, float]]:
        """
        Return [(quantity, norm_price)] for each distinct seat block at this anchor.
        Collapses split-option variants where smaller q appears in larger's extra["sp"][].
        If no sp[] data present, every listing is treated as a distinct block.
        """
        ordered = sorted(listings_at_anchor, key=lambda l: -l.quantity)
        kept: list = []
        for candidate in ordered:
            is_variant = False
            for keeper in kept:
                sp: list = ((keeper.extra or {}).get("sp") or []) if keeper.extra else []
                if sp and candidate.quantity in sp:
                    is_variant = True
                    break
            if not is_variant:
                kept.append(candidate)
        return [(l.quantity, normalized_price(l, slug)) for l in kept]

    intra: dict[tuple, float] = {}
    for (slug, sec_id, row), listings_at_anchor in anchor_groups.items():
        for q, np in _dedup_anchor(slug, listings_at_anchor):
            key = (slug, sec_id, row, q)
            if key not in intra or np < intra[key]:
                intra[key] = np

    seat_groups: dict[tuple, dict] = {}
    for (slug, sec_id, row, q), np in intra.items():
        gkey = (sec_id, row, q)
        if gkey not in seat_groups:
            seat_groups[gkey] = {"slugs": set(), "prices": [], "q": q}
        seat_groups[gkey]["slugs"].add(slug)
        seat_groups[gkey]["prices"].append(np)

    raw_listings = len(rows)
    raw_tickets = sum(l.quantity for l, _ in rows)
    mirrored_gkeys: set[tuple] = {gk for gk, g in seat_groups.items() if len(g["slugs"]) >= 2}
    mirror_listings = sum(
        1 for listing, slug in rows
        if (listing.section_id or "", listing.row or "", listing.quantity) in mirrored_gkeys
    )
    exclusive_listings = raw_listings - mirror_listings
    mirror_rate = round(mirror_listings / raw_listings, 4) if raw_listings else 0.0
    unique_tickets_available = sum(g["q"] for g in seat_groups.values())

    per_marketplace = []
    for slug, data in per_mp_raw.items():
        prices = data["prices"]
        per_marketplace.append({
            "marketplace_slug": slug,
            "raw_listings": data["listing_count"],
            "raw_tickets": data["quantity_sum"],
            "normalized_lowest_ask": round(min(prices), 2) if prices else None,
        })
    per_marketplace.sort(key=lambda x: x["marketplace_slug"])

    return {
        "event_id": event_id,
        "raw_listings": raw_listings,
        "raw_tickets": raw_tickets,
        "mirror_listings": mirror_listings,
        "exclusive_listings": exclusive_listings,
        "mirror_rate": mirror_rate,
        "unique_tickets_available": unique_tickets_available,
        "per_marketplace": per_marketplace,
    }


@router.get("/events/{event_id}/compare")
async def compare_marketplaces(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(and_(Listing.event_id == event_id, Listing.is_active == True)))
    listings = result.scalars().all()
    mp_names = {m.id: m.slug for m in (await db.execute(select(Marketplace))).scalars().all()}
    agg: dict = {}
    for l in listings:
        k = (l.section_id or l.section or "unknown", mp_names.get(l.marketplace_id, "unknown"))
        if k not in agg: agg[k] = {"display_name": l.section or k[0], "prices": [], "listing_count": 0, "inventory": 0}
        agg[k]["prices"].append(float(l.price))
        agg[k]["listing_count"] += 1
        agg[k]["inventory"] += l.quantity
    return [{"section_id": k[0], "marketplace": k[1], "display_name": v["display_name"], "lowest_ask": min(v["prices"]), "listing_count": v["listing_count"], "inventory": v["inventory"]} for k, v in agg.items()]


# ── Phase 4: Value Extraction Layer ──────────────────────────────────────────
# Read-only. No writes to any ingestion table.

@router.get("/audit")
async def data_audit(db: AsyncSession = Depends(get_db)):
    """
    STEP 1 audit — totals across events, tracked_events, poll_runs.
    Read-only. Safe to call repeatedly.
    """
    result = await get_data_audit(db)
    return dataclasses.asdict(result)


@router.get("/events/overview")
async def events_overview(db: AsyncSession = Depends(get_db)):
    """
    STEP 2 EventAnalyticsView — per-event coverage, resolution, and poll activity.
    Read-only.
    """
    views = await get_event_analytics(db)
    return [dataclasses.asdict(v) for v in views]


@router.get("/venues/overview")
async def venues_overview(db: AsyncSession = Depends(get_db)):
    """
    STEP 2 VenueAnalyticsView — venue-level rollup of events tracked and polling intensity.
    Read-only.
    """
    views = await get_venue_analytics(db)
    return [dataclasses.asdict(v) for v in views]


# ── Historical Baseline Layer ─────────────────────────────────────────────────
# Source: canonical_inventory_snapshots (append-only, written by scheduler after
# each poll cycle). No writes here. No predictions. Delta computation only.

@router.get("/events/{event_id}/baseline")
async def event_baseline(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Historical baseline for one event computed from canonical_inventory_snapshots.

    Returns current-state values and deltas vs 24h-ago and 7d-ago snapshots.
    Deltas are null when insufficient history exists (reason: insufficient_history).
    No predictions. No buy/wait signals. Read-only.

    Sources:
      canonical_inventory_snapshots — listings, unique_tickets, low_ask, mirror_rate, by_marketplace
      listing_snapshots             — per-marketplace lowest ask (via min(price) at snapshot window)
    """
    now = datetime.utcnow()

    # ── 1. Fetch the anchor snapshots (current, 24h-ago, 7d-ago) ──────────────
    # For each target time, pick the nearest snapshot within a ±4h tolerance.
    # 24h target: now - 24h  |  7d target: now - 168h
    # Window boundaries passed from Python — avoids asyncpg type inference issues
    # with INTERVAL arithmetic in parameterised queries.
    snap_sql = text("""
        SELECT id, snapshot_at, total_raw_listings, total_canonical_blocks,
               mirrored_ratio, low_ask, by_marketplace
        FROM canonical_inventory_snapshots
        WHERE event_id = :event_id
          AND snapshot_at BETWEEN CAST(:win_start AS timestamp) AND CAST(:win_end AS timestamp)
        ORDER BY ABS(EXTRACT(EPOCH FROM (snapshot_at - CAST(:target_ts AS timestamp)))) ASC
        LIMIT 1
    """)

    async def fetch_snap(target_ts: datetime, tolerance_h: int = 12):
        tol = timedelta(hours=tolerance_h)
        result = await db.execute(snap_sql, {
            "event_id": event_id,
            "target_ts": target_ts,
            "win_start": target_ts - tol,
            "win_end":   target_ts + tol,
        })
        row = result.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "snapshot_at": row[1].isoformat(),
            "raw_listings": row[2],
            "unique_tickets": row[3],
            "mirror_rate": float(row[4]) if row[4] is not None else None,
            "low_ask": float(row[5]) if row[5] is not None else None,
            "by_marketplace": row[6] or {},
        }

    # Current = most recent snapshot
    cur_sql = text("""
        SELECT id, snapshot_at, total_raw_listings, total_canonical_blocks,
               mirrored_ratio, low_ask, by_marketplace
        FROM canonical_inventory_snapshots
        WHERE event_id = :event_id
        ORDER BY snapshot_at DESC
        LIMIT 1
    """)
    cur_result = await db.execute(cur_sql, {"event_id": event_id})
    cur_row = cur_result.fetchone()

    if cur_row is None:
        return {
            "event_id": event_id,
            "history_depth_days": 0,
            "reason": "no_snapshots",
            "current": None,
            "deltas_24h": None,
            "deltas_7d": None,
            "per_marketplace": [],
        }

    current_snap_at = cur_row[1]
    current = {
        "snapshot_at": current_snap_at.isoformat(),
        "raw_listings": cur_row[2],
        "unique_tickets": cur_row[3],
        "mirror_rate": float(cur_row[4]) if cur_row[4] is not None else None,
        "low_ask": float(cur_row[5]) if cur_row[5] is not None else None,
        "by_marketplace": cur_row[6] or {},
    }

    # Oldest snapshot for depth calculation
    oldest_sql = text("SELECT MIN(snapshot_at) FROM canonical_inventory_snapshots WHERE event_id = :event_id")
    oldest_row = (await db.execute(oldest_sql, {"event_id": event_id})).fetchone()
    oldest_snap_at = oldest_row[0] if oldest_row else current_snap_at
    history_depth_days = (current_snap_at - oldest_snap_at).days if oldest_snap_at else 0

    snap_24h = await fetch_snap(now - timedelta(hours=24), tolerance_h=12)
    snap_7d  = await fetch_snap(now - timedelta(days=7),  tolerance_h=24)

    # ── 2. Delta helper ────────────────────────────────────────────────────────
    def delta(cur_val, ref_snap, field):
        """
        Returns {absolute, pct, ref_snapshot_at, reason} or {reason: insufficient_history}.
        """
        if ref_snap is None:
            return {"absolute": None, "pct": None, "ref_snapshot_at": None,
                    "reason": "insufficient_history"}
        ref_val = ref_snap.get(field)
        if cur_val is None or ref_val is None:
            return {"absolute": None, "pct": None,
                    "ref_snapshot_at": ref_snap["snapshot_at"], "reason": "null_value"}
        abs_delta = round(cur_val - ref_val, 4)
        pct_delta = round((cur_val - ref_val) / ref_val * 100, 2) if ref_val != 0 else None
        return {
            "absolute": abs_delta,
            "pct": pct_delta,
            "ref_snapshot_at": ref_snap["snapshot_at"],
            "reason": None,
        }

    # ── 3. Top-level deltas ────────────────────────────────────────────────────
    deltas_24h = {
        "raw_listings":   delta(current["raw_listings"],  snap_24h, "raw_listings"),
        "unique_tickets": delta(current["unique_tickets"], snap_24h, "unique_tickets"),
        "low_ask":        delta(current["low_ask"],        snap_24h, "low_ask"),
        "mirror_rate":    delta(current["mirror_rate"],    snap_24h, "mirror_rate"),
    }
    deltas_7d = {
        "raw_listings":   delta(current["raw_listings"],  snap_7d, "raw_listings"),
        "unique_tickets": delta(current["unique_tickets"], snap_7d, "unique_tickets"),
        "low_ask":        delta(current["low_ask"],        snap_7d, "low_ask"),
        "mirror_rate":    delta(current["mirror_rate"],    snap_7d, "mirror_rate"),
    }

    # ── 4. Per-marketplace breakdown ───────────────────────────────────────────
    # current counts from by_marketplace JSON in the latest canonical_inventory_snapshot
    # lowest ask from listing_snapshots (per-mp, at current snapshot window ±30min)
    # Per-marketplace lowest ask: use listing_snapshots near the most recent
    # listing snapshot time (not canonical snapshot time — they may differ by hours
    # if canonical computation lagged behind the latest poll).
    mp_ask_sql = text("""
        WITH latest_mp AS (
            SELECT marketplace_id, MAX(snapshot_at) AS latest_snap
            FROM listing_snapshots
            WHERE event_id = :event_id
            GROUP BY marketplace_id
        )
        SELECT m.slug, MIN(ls.price) AS lowest_ask
        FROM listing_snapshots ls
        JOIN marketplaces m ON m.id = ls.marketplace_id
        JOIN latest_mp lm ON lm.marketplace_id = ls.marketplace_id
        WHERE ls.event_id = :event_id
          AND ls.snapshot_at >= lm.latest_snap - INTERVAL '2 hours'
        GROUP BY m.slug
    """)
    mp_ask_result = await db.execute(mp_ask_sql, {"event_id": event_id})
    mp_lowest_ask_current = {r[0]: float(r[1]) for r in mp_ask_result.fetchall()}

    per_marketplace = []
    all_slugs = set(current["by_marketplace"].keys())
    if snap_24h:
        all_slugs |= set((snap_24h.get("by_marketplace") or {}).keys())
    if snap_7d:
        all_slugs |= set((snap_7d.get("by_marketplace") or {}).keys())

    for slug in sorted(all_slugs):
        cur_count = current["by_marketplace"].get(slug) or 0
        cur_ask = mp_lowest_ask_current.get(slug)

        def mp_delta_count(ref_snap):
            if ref_snap is None:
                return {"absolute": None, "pct": None, "reason": "insufficient_history"}
            ref_count = (ref_snap.get("by_marketplace") or {}).get(slug) or 0
            abs_d = cur_count - ref_count
            pct_d = round(abs_d / ref_count * 100, 2) if ref_count != 0 else None
            return {"absolute": abs_d, "pct": pct_d, "reason": None}

        per_marketplace.append({
            "marketplace_slug": slug,
            "current_listings": cur_count,
            "current_lowest_ask": cur_ask,
            "listings_change_24h": mp_delta_count(snap_24h),
            "listings_change_7d":  mp_delta_count(snap_7d),
        })

    return {
        "event_id": event_id,
        "history_depth_days": history_depth_days,
        "current": {
            "snapshot_at": current["snapshot_at"],
            "raw_listings": current["raw_listings"],
            "unique_tickets": current["unique_tickets"],
            "lowest_ask": current["low_ask"],
            "mirror_rate": current["mirror_rate"],
        },
        "deltas_24h": deltas_24h,
        "deltas_7d": deltas_7d,
        "per_marketplace": per_marketplace,
    }
