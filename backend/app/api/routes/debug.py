"""
Debug API — exposes ScraperErrorLog and FailureMemory to the frontend dashboard.
Also provides the /api/debug/test-collect endpoint for quick in-browser test runs.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from typing import Optional

from app.database import get_db
from app.models.debug import ScraperErrorLog, FailureMemory

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/errors")
async def list_errors(
    marketplace: Optional[str] = Query(None),
    error_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(ScraperErrorLog).order_by(desc(ScraperErrorLog.timestamp)).limit(limit)
    if marketplace:
        q = q.where(ScraperErrorLog.marketplace == marketplace)
    if error_type:
        q = q.where(ScraperErrorLog.error_type == error_type)
    result = await db.execute(q)
    return [r.to_dict() for r in result.scalars().all()]


@router.get("/errors/summary")
async def error_summary(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    result = await db.execute(
        select(
            ScraperErrorLog.marketplace,
            ScraperErrorLog.error_type,
            func.count().label("count"),
            func.max(ScraperErrorLog.timestamp).label("last_seen"),
        )
        .group_by(ScraperErrorLog.marketplace, ScraperErrorLog.error_type)
        .order_by(func.count().desc())
    )
    rows = result.all()
    return [
        {
            "marketplace": r.marketplace,
            "error_type": r.error_type,
            "count": r.count,
            "last_seen": r.last_seen.isoformat() if r.last_seen else None,
        }
        for r in rows
    ]


@router.get("/memory")
async def list_failure_memory(
    marketplace: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(FailureMemory).order_by(FailureMemory.failure_count.desc())
    if marketplace:
        q = q.where(FailureMemory.marketplace == marketplace)
    result = await db.execute(q)
    return [r.to_dict() for r in result.scalars().all()]


@router.delete("/memory/{memory_id}", status_code=204)
async def delete_memory_entry(memory_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(FailureMemory).where(FailureMemory.id == memory_id))
    await db.commit()


@router.delete("/memory", status_code=204)
async def clear_memory(
    marketplace: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(FailureMemory).where(FailureMemory.marketplace == marketplace))
    await db.commit()


@router.post("/test-collect")
async def test_collect(
    marketplace: str,
    event_id: str,
    background_tasks: BackgroundTasks,
    url: Optional[str] = None,
):
    """
    Trigger a one-off debug collection run from the UI.
    Runs headless (not debug mode) and stores results/errors to DB.
    """
    from app.scheduler import run_poll_for_tracked_event
    from app.collectors.registry import get_collector
    from app.config import get_settings
    from app.collectors.base import RawListing
    from dataclasses import dataclass

    @dataclass
    class FakeTe:
        event_id: int = 0
        marketplace_id: int = 0
        external_event_id: str = event_id
        external_url: str = url or ""
        is_active: bool = True
        poll_interval_minutes: int = 60

    async def _run():
        settings = get_settings()
        collector = get_collector(marketplace, settings)
        if not collector:
            return
        from app.database import AsyncSessionLocal
        collector._db_session_factory = AsyncSessionLocal
        te = FakeTe(event_id=0, external_event_id=event_id, external_url=url or "")
        result = await collector.collect(te)
        await collector.close()
        return result

    background_tasks.add_task(_run)
    return {"message": f"Test collection triggered for {marketplace} event {event_id}"}
