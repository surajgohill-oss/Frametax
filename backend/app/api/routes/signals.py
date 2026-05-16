"""
Phase 5 signal API routes.

Read-only. Never mutates any table.
All marketplace references are by integer ID — never by name.
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.signals.engine import compute_signals, compute_signals_all_active

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/")
async def get_all_signals():
    """
    Compute and return EventSignalBundle for every active, resolved event.
    Triggered ad-hoc; call after poll-run completion for real-time updates.
    """
    async with AsyncSessionLocal() as db:
        bundles = await compute_signals_all_active(db)
    return {
        "count":   len(bundles),
        "signals": [b.to_dict() for b in bundles],
    }


@router.get("/{event_id}")
async def get_event_signals(event_id: int):
    """
    Compute and return EventSignalBundle for a single event.
    Call this after each poll_run completion or resolver state update
    to get real-time signal recomputation for the affected event only.
    """
    async with AsyncSessionLocal() as db:
        try:
            bundle = await compute_signals(db, event_id)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    return bundle.to_dict()
