from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete, func
from typing import Optional

from app.database import get_db
from app.models.debug import ScraperErrorLog, FailureMemory

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/errors")
async def list_errors(marketplace: Optional[str] = Query(None), error_type: Optional[str] = Query(None), limit: int = Query(50, le=200), db: AsyncSession = Depends(get_db)):
    q = select(ScraperErrorLog).order_by(desc(ScraperErrorLog.timestamp)).limit(limit)
    if marketplace: q = q.where(ScraperErrorLog.marketplace == marketplace)
    if error_type: q = q.where(ScraperErrorLog.error_type == error_type)
    result = await db.execute(q)
    return [r.to_dict() for r in result.scalars().all()]


@router.get("/errors/summary")
async def error_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScraperErrorLog.marketplace, ScraperErrorLog.error_type, func.count().label("count"), func.max(ScraperErrorLog.timestamp).label("last_seen"))
        .group_by(ScraperErrorLog.marketplace, ScraperErrorLog.error_type).order_by(func.count().desc())
    )
    return [{"marketplace": r.marketplace, "error_type": r.error_type, "count": r.count, "last_seen": r.last_seen.isoformat() if r.last_seen else None} for r in result.all()]


@router.get("/memory")
async def list_failure_memory(marketplace: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    q = select(FailureMemory).order_by(FailureMemory.failure_count.desc())
    if marketplace: q = q.where(FailureMemory.marketplace == marketplace)
    result = await db.execute(q)
    return [r.to_dict() for r in result.scalars().all()]


@router.delete("/memory/{memory_id}", status_code=204)
async def delete_memory_entry(memory_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(FailureMemory).where(FailureMemory.id == memory_id))
    await db.commit()


@router.delete("/memory", status_code=204)
async def clear_memory(marketplace: str = Query(...), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(FailureMemory).where(FailureMemory.marketplace == marketplace))
    await db.commit()


@router.post("/test-collect")
async def test_collect(marketplace: str, event_id: str = "", background_tasks: BackgroundTasks = None, url: Optional[str] = None):
    async def _run():
        from app.collectors.registry import get_collector
        from app.config import get_settings
        from app.database import AsyncSessionLocal
        from dataclasses import dataclass
        @dataclass
        class FakeTe:
            event_id: int = 0
            marketplace_id: int = 0
            external_event_id: str = event_id
            external_url: str = url or ""
            is_active: bool = True
            poll_interval_minutes: int = 60
        settings = get_settings()
        collector = get_collector(marketplace, settings)
        if not collector: return
        collector._db_session_factory = AsyncSessionLocal
        result = await collector.collect(FakeTe())
        await collector.close()
    if background_tasks:
        background_tasks.add_task(_run)
    return {"message": f"Test collection triggered for {marketplace}"}
