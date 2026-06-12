from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Venue
from app.models.venue import VenueSection
from app.services.venue_intelligence import (
    compute_section_metrics,
    get_venue_intelligence,
    get_classifications,
)

router = APIRouter(prefix="/venues", tags=["venues"])


# ─────────────────────────────────────────────────────────────────────────────
# Existing CRUD routes
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_venues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Venue).options(selectinload(Venue.sections)).order_by(Venue.name))
    return [_serialize(v) for v in result.scalars().all()]


@router.get("/{slug}/sections")
async def get_venue_sections(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Venue).options(selectinload(Venue.sections)).where(Venue.slug == slug))
    v = result.scalar_one_or_none()
    if not v: raise HTTPException(404, "Venue not found")
    return _serialize(v)["sections"]


@router.get("/{slug}")
async def get_venue(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Venue).options(selectinload(Venue.sections)).where(Venue.slug == slug))
    v = result.scalar_one_or_none()
    if not v: raise HTTPException(404, "Venue not found")
    return _serialize(v)


def _serialize(v: Venue) -> dict:
    return {
        "id": v.id, "slug": v.slug, "name": v.name, "city": v.city, "state": v.state,
        "capacity": v.capacity, "map_width": v.map_width, "map_height": v.map_height,
        "sections": [
            {
                "id": s.id, "venue_id": s.venue_id, "section_id": s.section_id,
                "display_name": s.display_name, "tier": s.tier, "quality_score": s.quality_score,
                "level": s.level, "zone": s.zone, "side": s.side,
                "is_premium": s.is_premium, "future_map_key": s.future_map_key,
                "x": s.x, "y": s.y, "width": s.width, "height": s.height, "shape": s.shape,
                # legacy fields kept for backward compat
                "stubhub_aliases": s.stubhub_aliases, "seatgeek_aliases": s.seatgeek_aliases,
            } for s in v.sections
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Intelligence endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{slug}/intelligence")
async def get_intelligence(
    slug: str,
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Full venue intelligence for one event: all canonical sections with metrics.
    Reads from pre-computed venue_section_metrics (fast).
    Trigger computation first via POST /{slug}/compute?event_id=N.
    """
    sections = await get_venue_intelligence(event_id, db, venue_slug=slug)
    if sections is None:
        raise HTTPException(404, detail="Venue not found.")
    # sections may be empty list [] if venue exists but has no sections — return gracefully
    sections_with_metrics = [s for s in sections if s["metrics"] is not None]
    return {
        "venue_slug": slug,
        "event_id": event_id,
        "sections_total": len(sections),
        "sections_with_metrics": len(sections_with_metrics),
        "sections": sections,
    }


@router.get("/{slug}/intelligence/{section_key}")
async def get_section_intelligence(
    slug: str,
    section_key: str,
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Single section detail + metrics."""
    sections = await get_venue_intelligence(event_id, db, venue_slug=slug)
    match = next((s for s in sections if s["section_id"] == section_key), None)
    if not match:
        raise HTTPException(404, detail=f"Section '{section_key}' not found in venue '{slug}'")
    return match


@router.get("/{slug}/classifications")
async def get_venue_classifications(
    slug: str,
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Section classification outputs:
      - best_value: highest value_score (quality + deal)
      - highest_demand: most listings relative to average
      - fastest_price_drops: highest seller_pressure
      - inventory_building: positive 24h inventory delta
      - inventory_depleting: negative 24h inventory delta
      - most_active: highest listing count
    """
    sections = await get_venue_intelligence(event_id, db, venue_slug=slug)
    if not sections:
        # Return empty classifications gracefully
        empty = {k: [] for k in ["best_value","highest_demand","fastest_price_drops","inventory_building","inventory_depleting","most_active"]}
        return {"venue_slug": slug, "event_id": event_id, "classifications": empty}

    classifications = get_classifications(sections)
    return {
        "venue_slug": slug,
        "event_id": event_id,
        "classifications": classifications,
    }


@router.post("/{slug}/seed-from-listings")
async def seed_sections_from_listings(
    slug: str,
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Auto-seed venue_sections for a non-SoFi venue by inspecting what section
    strings appear in the listings table for a given event.

    This replaces generic placeholder sections with sections that actually
    match the marketplace data, enabling compute_section_metrics to work.

    Algorithm:
      1. Query distinct (section, section_id) from listings for the event
      2. Infer tier from section name patterns
      3. Assign a quality_score based on tier
      4. Delete existing placeholder sections for this venue
      5. Insert proper sections

    Safe to re-run (idempotent by design).
    """
    # Get venue
    result = await db.execute(select(Venue).where(Venue.slug == slug))
    venue = result.scalar_one_or_none()
    if not venue:
        raise HTTPException(404, "Venue not found")

    # Collect all distinct section strings from listings for this event
    rows = (await db.execute(text("""
        SELECT DISTINCT
            COALESCE(l.section_id::text, l.section) AS raw_id,
            l.section                               AS raw_name
        FROM listings l
        WHERE l.event_id = :event_id
          AND l.is_active = TRUE
          AND (l.section IS NOT NULL OR l.section_id IS NOT NULL)
        ORDER BY raw_id
    """), {"event_id": event_id})).fetchall()

    if not rows:
        return {"venue_slug": slug, "event_id": event_id, "sections_seeded": 0, "note": "No listings found"}

    # Infer tier + quality from section name
    def _infer_tier(name: str):
        if name is None: return ("other", 50)
        n = name.strip().lower()
        # Floor / Pit
        if any(k in n for k in ["floor", "pit", "ga ", "general admission"]): return ("floor", 88)
        # Lower numbers typically lower bowl (100s)
        if n.isdigit():
            num = int(n)
            if num < 120: return ("lower", 75)
            if num < 220: return ("upper", 60)
            return ("upper", 55)
        # Named sections
        if n.startswith("section "):
            rest = n[8:].strip()
            if rest.isdigit():
                num = int(rest)
                if num < 120: return ("lower", 75)
                if num < 220: return ("upper", 60)
                return ("upper", 55)
        # Letter-only sections (floor/pit adjacent at many venues)
        if len(n) <= 3 and n.replace(" ", "").isalpha():
            return ("floor", 80)
        # Special labels
        if any(k in n for k in ["vip", "premium", "suite", "box", "club"]): return ("club", 70)
        if any(k in n for k in ["terrace", "reserved a", "reserved b"]): return ("lower", 70)
        if any(k in n for k in ["upper", "rear", "balcony"]): return ("upper", 55)
        return ("other", 50)

    # Build unique sections (deduplicate by raw_id)
    seen: set[str] = set()
    new_sections: list[dict] = []
    for row in rows:
        raw_id = (row.raw_id or "").strip()
        if not raw_id or raw_id.lower() in ("unknown", "none", "") or raw_id in seen:
            continue
        seen.add(raw_id)
        display = row.raw_name or raw_id
        tier, quality = _infer_tier(display)
        new_sections.append({
            "venue_id": venue.id,
            "section_id": raw_id,
            "display_name": display.title() if display == display.upper() else display,
            "tier": tier,
            "quality_score": quality,
            "level": None, "zone": None, "side": None,
            "is_premium": False, "future_map_key": None,
            "stubhub_aliases": None, "seatgeek_aliases": None,
        })

    if not new_sections:
        return {"venue_slug": slug, "event_id": event_id, "sections_seeded": 0, "note": "No valid sections"}

    # Delete existing sections for this venue (placeholder replacement)
    await db.execute(delete(VenueSection).where(VenueSection.venue_id == venue.id))

    # Insert new sections
    for s in new_sections:
        db.add(VenueSection(**s))

    await db.commit()
    return {
        "venue_slug": slug,
        "event_id": event_id,
        "sections_seeded": len(new_sections),
        "sections": [{"section_id": s["section_id"], "tier": s["tier"]} for s in new_sections[:20]],
    }


@router.post("/{slug}/compute")
async def trigger_compute(
    slug: str,
    event_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Compute (or recompute) section metrics for event_id.
    Runs synchronously; returns computed section count.
    """
    results = await compute_section_metrics(event_id, db, venue_slug=slug)
    return {
        "venue_slug": slug,
        "event_id": event_id,
        "sections_computed": len(results),
        "status": "ok",
    }
