"""
GET  /api/follows          — list all active follows
POST /api/follows          — create or update a follow (upsert by entity_type + entity_key)
DELETE /api/follows/{id}   — remove a follow

Follows are the acquisition registry: each row represents a user intent to
track future events for an entity (artist or team).  The scope_anchor is
stored as the datetime the follow was created (NOW), not event-relative.
scope_type defines how many future events after scope_anchor should be enrolled.
"""
from datetime import datetime, timezone

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.follow import UserFollow

router = APIRouter(prefix="/follows", tags=["follows"])

_VALID_ENTITY_TYPES = {"artist", "team"}
_VALID_SCOPE_TYPES  = {"next3", "next5", "next10", "all_future"}


# ── Request / Response schemas ────────────────────────────────────────────────

class FollowCreate(BaseModel):
    entity_type:  str
    entity_key:   str   # normalized lowercase key (e.g. "morgan jay")
    display_name: str
    scope_type:   str   # "next3" | "next5" | "next10" | "all_future"

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        if v not in _VALID_ENTITY_TYPES:
            raise ValueError(f"entity_type must be one of {_VALID_ENTITY_TYPES}")
        return v

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: str) -> str:
        if v not in _VALID_SCOPE_TYPES:
            raise ValueError(f"scope_type must be one of {_VALID_SCOPE_TYPES}")
        return v

    @field_validator("entity_key")
    @classmethod
    def normalize_key(cls, v: str) -> str:
        return v.strip().lower()


class FollowResponse(BaseModel):
    id:           int
    entity_type:  str
    entity_key:   str
    display_name: str
    scope_type:   str
    scope_anchor: str   # ISO 8601
    status:       str
    created_at:   str
    updated_at:   str

    model_config = {"from_attributes": True}


def _to_response(f: UserFollow) -> FollowResponse:
    def _iso(dt: datetime | None) -> str:
        if dt is None:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    return FollowResponse(
        id=f.id,
        entity_type=f.entity_type,
        entity_key=f.entity_key,
        display_name=f.display_name,
        scope_type=f.scope_type,
        scope_anchor=_iso(f.scope_anchor),
        status=f.status,
        created_at=_iso(f.created_at),
        updated_at=_iso(f.updated_at),
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[FollowResponse])
async def list_follows(db: AsyncSession = Depends(get_db)):
    """Return all active follows (acquisition registry)."""
    result = await db.execute(
        select(UserFollow)
        .where(UserFollow.status == "active")
        .order_by(UserFollow.created_at.desc())
    )
    return [_to_response(f) for f in result.scalars().all()]


@router.post("", response_model=FollowResponse, status_code=201)
async def create_or_update_follow(
    body: FollowCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Upsert a follow by (entity_type, entity_key).

    If the entity is already followed:
      - update display_name, scope_type
      - reset scope_anchor to NOW (new follow intent)
      - set status = 'active'

    scope_anchor is always set to the current time (time-relative, not
    event-relative). scope_type defines how many future events after
    scope_anchor should be enrolled.
    """
    now = datetime.now(timezone.utc)

    existing = (await db.execute(
        select(UserFollow).where(
            UserFollow.entity_type == body.entity_type,
            UserFollow.entity_key  == body.entity_key,
        )
    )).scalar_one_or_none()

    if existing:
        existing.display_name = body.display_name
        existing.scope_type   = body.scope_type
        existing.scope_anchor = now
        existing.status       = "active"
        existing.updated_at   = now
        await db.commit()
        await db.refresh(existing)
        return _to_response(existing)

    follow = UserFollow(
        entity_type=body.entity_type,
        entity_key=body.entity_key,
        display_name=body.display_name,
        scope_type=body.scope_type,
        scope_anchor=now,
        status="active",
        created_at=now,
        updated_at=now,
    )
    db.add(follow)
    await db.commit()
    await db.refresh(follow)
    return _to_response(follow)


@router.post("/acquire", status_code=202)
async def trigger_acquisition(background_tasks: BackgroundTasks):
    """
    Trigger the Follow acquisition job as a background task.
    Reads all active follows, checks scope, discovers and enrolls missing events.
    Returns immediately; acquisition runs asynchronously.
    """
    from app.services.follow_acquisition import run_follow_acquisition
    background_tasks.add_task(run_follow_acquisition)
    return {"status": "acquisition_started"}


@router.post("/acquire/sync")
async def trigger_acquisition_sync():
    """
    Trigger the Follow acquisition job synchronously and return the full summary.
    Use for debugging or one-off runs. May take 10-60s depending on event count.
    """
    from app.services.follow_acquisition import run_follow_acquisition
    summary = await run_follow_acquisition()
    return {"status": "done", "summary": summary}


@router.get("/events")
async def list_follow_events(db: AsyncSession = Depends(get_db)):
    """
    Return all events discovered via Follow, with per-marketplace population status
    and intelligence eligibility.

    Population statuses: POPULATED | PARTIAL_POPULATION | NO_ID | BLOCKED | DEFERRED | ERROR | UNKNOWN
    Eligibility: eligible | partial | not_eligible (by hours tracked)
    """
    from datetime import datetime, timezone
    from sqlalchemy import text

    now = datetime.now(timezone.utc)
    MIN_HOURS_ELIGIBLE  = 72
    MIN_HOURS_PARTIAL   = 24

    # Identify follow-acquired events by matching events.artist against active user_follows.
    # No 'source' column on events table — we use artist name match as the signal.
    rows = (await db.execute(text("""
        SELECT
            e.id          AS event_id,
            e.title,
            e.artist,
            e.event_date,
            e.status,
            uf.display_name AS follow_display_name,
            -- Listing counts per marketplace (to infer population status)
            SUM(CASE WHEN m.slug='gametime'   AND l.id IS NOT NULL THEN 1 ELSE 0 END) AS gt_listings,
            SUM(CASE WHEN m.slug='stubhub'    AND l.id IS NOT NULL THEN 1 ELSE 0 END) AS sh_listings,
            SUM(CASE WHEN m.slug='tickpick'   AND l.id IS NOT NULL THEN 1 ELSE 0 END) AS tp_listings,
            SUM(CASE WHEN m.slug='vividseats' AND l.id IS NOT NULL THEN 1 ELSE 0 END) AS vs_listings,
            -- History depth from listing_snapshots
            MIN(ls.snapshot_at)   AS snap_oldest,
            MAX(ls.snapshot_at)   AS snap_newest,
            COUNT(DISTINCT ls.id) AS snap_count,
            -- Floor price (lowest active listing)
            MIN(l.price)          AS floor_price
        FROM events e
        JOIN user_follows uf ON (
            LOWER(e.artist) = uf.entity_key
            OR LOWER(e.artist) LIKE '%' || uf.entity_key || '%'
            OR uf.entity_key LIKE '%' || LOWER(e.artist) || '%'
        ) AND uf.status = 'active'
        LEFT JOIN tracked_events te ON te.event_id = e.id AND te.is_active = true
        LEFT JOIN marketplaces m ON m.id = te.marketplace_id
        LEFT JOIN listings l ON l.event_id = e.id AND l.marketplace_id = te.marketplace_id AND l.is_active = true
        LEFT JOIN listing_snapshots ls ON ls.event_id = e.id
        GROUP BY e.id, e.title, e.artist, e.event_date, e.status, uf.display_name
        ORDER BY e.event_date ASC
    """))).fetchall()

    events_out = []
    for row in rows:
        (event_id, title, artist, event_date, status, follow_display_name,
         gt_listings, sh_listings, tp_listings, vs_listings,
         snap_oldest, snap_newest, snap_count,
         floor_price) = row

        # ── History depth ─────────────────────────────────────────────────────
        if snap_oldest and snap_newest:
            snap_oldest_tz = snap_oldest.replace(tzinfo=timezone.utc) if snap_oldest.tzinfo is None else snap_oldest
            snap_newest_tz = snap_newest.replace(tzinfo=timezone.utc) if snap_newest.tzinfo is None else snap_newest
            hours_tracked = round((snap_newest_tz - snap_oldest_tz).total_seconds() / 3600, 1)
        else:
            hours_tracked = 0.0

        # ── Hours until event ─────────────────────────────────────────────────
        if event_date:
            event_dt_tz = event_date.replace(tzinfo=timezone.utc) if event_date.tzinfo is None else event_date
            hours_until_event = round((event_dt_tz - now).total_seconds() / 3600, 1)
        else:
            hours_until_event = None

        # ── Intelligence eligibility ──────────────────────────────────────────
        if hours_tracked >= MIN_HOURS_ELIGIBLE:
            eligibility = "eligible"
        elif hours_tracked >= MIN_HOURS_PARTIAL:
            eligibility = "partial"
        else:
            eligibility = "not_eligible"

        hours_until_eligible = max(0, round(MIN_HOURS_ELIGIBLE - hours_tracked, 1)) if eligibility != "eligible" else 0

        # ── Per-marketplace population status ─────────────────────────────────
        def _mp_status(listing_count: int, mp_slug: str) -> str:
            if listing_count and listing_count > 0:
                return "POPULATED"
            if mp_slug == "stubhub":
                return "BLOCKED"   # StubHub requires browser session
            return "NO_ID"

        mp_status = {
            "gametime":   _mp_status(gt_listings or 0, "gametime"),
            "stubhub":    _mp_status(sh_listings or 0, "stubhub"),
            "tickpick":   _mp_status(tp_listings or 0, "tickpick"),
            "vividseats": _mp_status(vs_listings or 0, "vividseats"),
        }

        populated_count = sum(1 for s in mp_status.values() if s == "POPULATED")

        if populated_count >= 3:
            overall_status = "POPULATED"
        elif populated_count >= 1:
            overall_status = "PARTIAL_POPULATION"
        else:
            overall_status = "EMPTY"

        partial_warnings = [
            f"{slug}: {st}" for slug, st in mp_status.items() if st != "POPULATED"
        ] if overall_status == "PARTIAL_POPULATION" else []

        events_out.append({
            "event_id":           event_id,
            "title":              title,
            "artist":             artist,
            "event_date":         event_date.isoformat() if event_date else None,
            "status":             status,
            "hours_until_event":  hours_until_event,
            "follow_display_name": follow_display_name,
            "population": {
                "overall":          overall_status,
                "per_marketplace":  mp_status,
                "partial_warnings": partial_warnings,
            },
            "history": {
                "hours_tracked":   hours_tracked,
                "snap_count":      snap_count or 0,
                "floor_price":     float(floor_price) if floor_price else None,
            },
            "intelligence": {
                "eligibility":          eligibility,
                "hours_until_eligible": hours_until_eligible if eligibility != "eligible" else None,
                "reason": (
                    f"Need {hours_until_eligible}h more tracking for full eligibility"
                    if eligibility == "not_eligible"
                    else f"Partial: {hours_tracked}h tracked (72h needed for full confidence)"
                    if eligibility == "partial"
                    else f"{hours_tracked}h tracked — eligible"
                ),
            },
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    total        = len(events_out)
    populated    = sum(1 for e in events_out if e["population"]["overall"] == "POPULATED")
    partial      = sum(1 for e in events_out if e["population"]["overall"] == "PARTIAL_POPULATION")
    eligible     = sum(1 for e in events_out if e["intelligence"]["eligibility"] == "eligible")
    partial_elig = sum(1 for e in events_out if e["intelligence"]["eligibility"] == "partial")
    not_elig     = sum(1 for e in events_out if e["intelligence"]["eligibility"] == "not_eligible")

    return {
        "summary": {
            "total_events":        total,
            "fully_populated":     populated,
            "partial_population":  partial,
            "empty":               total - populated - partial,
            "intelligence_eligible":         eligible,
            "intelligence_partial":          partial_elig,
            "intelligence_not_eligible":     not_elig,
        },
        "events": events_out,
    }


@router.delete("/{follow_id}", status_code=204)
async def delete_follow(
    follow_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove a follow (sets status = 'inactive')."""
    follow = (await db.execute(
        select(UserFollow).where(UserFollow.id == follow_id)
    )).scalar_one_or_none()

    if not follow:
        raise HTTPException(404, f"Follow {follow_id} not found")

    follow.status = "inactive"
    follow.updated_at = datetime.now(timezone.utc)
    await db.commit()
