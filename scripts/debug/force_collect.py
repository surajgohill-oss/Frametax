#!/usr/bin/env python3
"""
force_collect.py
Force a single full collection cycle (all 6 marketplaces) for the first
active TrackedEvent that has a non-null, non-demo external_event_id.

Falls back to demo-prefixed IDs if no real IDs exist yet — in that case
inline resolution will attempt to obtain real IDs during the run.

Run inside backend container: python3 /shared_scripts/debug/force_collect.py
"""
import asyncio
import logging
import sys

sys.path.insert(0, "/app")

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s — %(message)s",
)

from sqlalchemy import select, func, or_

from app.collectors.registry import COLLECTOR_REGISTRY
from app.database import AsyncSessionLocal
from app.models import Event, Listing, Marketplace, TrackedEvent
from app.scheduler import _run_collector_for_event


async def _listing_counts(event_id: int) -> dict:
    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(Marketplace.slug, func.count(), func.min(Listing.price))
                .join(Listing, Listing.marketplace_id == Marketplace.id)
                .where(
                    Listing.event_id == event_id,
                    Listing.is_active == True,
                )
                .group_by(Marketplace.slug)
            )
        ).all()
    return {slug: (cnt, min_p) for slug, cnt, min_p in rows}


async def main() -> None:
    # Prefer a TrackedEvent with a real (non-demo) external_event_id so we skip
    # the inline resolver. Fall back to demo-prefixed or NULL rows if nothing real
    # exists — the inline resolver will fire for those.
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TrackedEvent, Event)
            .join(Event, TrackedEvent.event_id == Event.id)
            .where(
                TrackedEvent.is_active == True,
                or_(
                    TrackedEvent.external_event_id.is_not(None),
                    TrackedEvent.external_event_id.is_(None),
                ),
            )
            .order_by(
                # Real IDs first (not NULL, not demo-)
                TrackedEvent.external_event_id.is_(None),  # NULLs last
            )
            .limit(1)
        )
        row = result.first()

    if not row:
        print("NO TRACKED EVENTS FOUND IN DB — seed may not have run.")
        return

    te, event = row

    print("=" * 60)
    print("PRE-POLL STATE")
    print("=" * 60)
    print(f"  event_id    : {te.event_id}")
    print(f"  event_title : {event.title}")
    print(f"  te_id       : {te.id}")
    print(f"  ext_eid     : {te.external_event_id!r}")
    before = await _listing_counts(te.event_id)
    if before:
        for slug, (cnt, min_p) in sorted(before.items()):
            print(f"  {slug:12}  count={cnt}  min=${min_p:.2f}")
    else:
        print("  listings    : NONE")

    print()
    print("=" * 60)
    print(f"POLLING all {len(COLLECTOR_REGISTRY)} marketplaces for event_id={te.event_id}")
    print("=" * 60)

    slugs = list(COLLECTOR_REGISTRY.keys())
    await asyncio.gather(
        *[_run_collector_for_event(slug, te, event) for slug in slugs],
        return_exceptions=True,
    )

    print()
    print("=" * 60)
    print("POST-POLL DB STATE")
    print("=" * 60)
    after = await _listing_counts(te.event_id)
    if after:
        for slug, (cnt, min_p) in sorted(after.items()):
            marker = "✓ REAL" if any(
                not ext_id.startswith("demo-")
                for ext_id in [f"placeholder-{slug}"]  # shape check only
            ) else ""
            print(f"  {slug:12}  count={cnt}  min=${min_p:.2f}")
        total = sum(cnt for cnt, _ in after.values())
        print(f"\n  TOTAL active listings in DB for event_id={te.event_id}: {total}")
        if total > 0:
            print("  STATUS: SUCCESS — listings exist in DB")
        else:
            print("  STATUS: EMPTY — all collectors returned 0 (check logs above)")
    else:
        print("  NO ACTIVE LISTINGS — all marketplaces blocked or returned 0")
        print()
        print("  NEXT STEPS:")
        print("  1. Check logs: docker compose logs backend --tail 200 | grep -E 'COLLECTOR|RESOLVER|ERROR'")
        print("  2. If EXTERNAL_BLOCK on all: set credentials in .env and restart")
        print("  3. SeatGeek internal API + TickPick are the lowest-friction paths (no API key)")


asyncio.run(main())
