from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Venue
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
    if not sections:
        raise HTTPException(404, detail="No sections found for venue or no metrics computed yet. POST /compute first.")

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
        raise HTTPException(404, detail="No sections found. POST /compute first.")

    classifications = get_classifications(sections)
    return {
        "venue_slug": slug,
        "event_id": event_id,
        "classifications": classifications,
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
