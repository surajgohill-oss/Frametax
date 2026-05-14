from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import TrackedEvent, PollRun

router = APIRouter(prefix="/poll", tags=["poll"])


@router.post("/events/{event_id}/trigger")
async def trigger_poll(event_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    from app.scheduler import run_poll_for_tracked_event
    result = await db.execute(select(TrackedEvent).where(TrackedEvent.event_id == event_id, TrackedEvent.is_active == True))
    tracked = result.scalars().all()
    if not tracked: raise HTTPException(404, "No active tracked events")
    for te in tracked:
        background_tasks.add_task(run_poll_for_tracked_event, te.id)
    return {"message": f"Triggered {len(tracked)} poll(s)", "count": len(tracked)}


@router.get("/events/{event_id}/runs")
async def poll_runs(event_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PollRun).join(TrackedEvent).where(TrackedEvent.event_id == event_id).order_by(PollRun.started_at.desc()).limit(limit))
    return [{"id": r.id, "tracked_event_id": r.tracked_event_id, "started_at": r.started_at.isoformat() if r.started_at else None, "completed_at": r.completed_at.isoformat() if r.completed_at else None, "listings_found": r.listings_found, "new_listings": r.new_listings, "disappeared_listings": r.disappeared_listings, "status": r.status, "error_message": r.error_message} for r in result.scalars().all()]
