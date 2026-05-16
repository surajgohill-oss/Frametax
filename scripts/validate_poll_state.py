#!/usr/bin/env python3
"""
Post-fanout validation script.

Queries live DB state to verify:
  1. Which marketplaces have TrackedEvents (and whether they have external_event_ids)
  2. Which marketplaces have listings in the listings table
  3. Whether external_event_ids on TrackedEvents match their marketplace
     (e.g. a SeatGeek ID used by a non-SeatGeek collector = ID mismatch)
  4. Emits a GATE_REPORT_JSON= line for CI consumption

Run inside the backend container:
  python /shared_scripts/validate_poll_state.py
"""
import asyncio
import json
import sys
import time
from collections import defaultdict

sys.path.insert(0, "/app")

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models import TrackedEvent, Event, Marketplace, Listing, PollRun

DATABASE_URL = "postgresql+asyncpg://concert:concert@db:5432/concert_tracker"

_t0 = time.monotonic()


async def main() -> int:
    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    failures: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    async with Session() as db:
        # ── 1. TrackedEvents by marketplace ──────────────────────────────────
        te_rows = (await db.execute(
            select(TrackedEvent, Marketplace)
            .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        )).all()

        te_by_mp: dict[str, list[dict]] = defaultdict(list)
        for te, mp in te_rows:
            te_by_mp[mp.slug].append({
                "te_id": te.id,
                "event_id": te.event_id,
                "is_active": te.is_active,
                "external_event_id": te.external_event_id,
                "resolution_source": te.resolution_source,
                "lifecycle_phase": te.lifecycle_phase,
                "next_poll_at": te.next_poll_at.isoformat() if te.next_poll_at else None,
            })

        details["tracked_events_by_marketplace"] = {
            mp: {
                "count": len(rows),
                "active": sum(1 for r in rows if r["is_active"]),
                "with_external_id": sum(1 for r in rows if r["external_event_id"]),
                "sample_ids": [r["external_event_id"] for r in rows[:3] if r["external_event_id"]],
            }
            for mp, rows in te_by_mp.items()
        }

        # ── 2. Listings by marketplace ────────────────────────────────────────
        listing_rows = (await db.execute(
            select(Marketplace.slug, func.count(Listing.id).label("cnt"))
            .join(Marketplace, Listing.marketplace_id == Marketplace.id)
            .where(Listing.is_active == True)
            .group_by(Marketplace.slug)
        )).all()

        listings_by_mp = {row.slug: row.cnt for row in listing_rows}
        details["active_listings_by_marketplace"] = listings_by_mp

        # ── 3. Marketplace diversity check ────────────────────────────────────
        distinct_mp_count = len(listings_by_mp)
        details["distinct_marketplaces_with_listings"] = distinct_mp_count

        if distinct_mp_count < 2:
            failures.append(
                f"Only {distinct_mp_count} marketplace(s) have listings — "
                f"expected 2+. Found: {list(listings_by_mp.keys())}"
            )

        # ── 4. ID mismatch probe ──────────────────────────────────────────────
        # Detect TrackedEvents where external_event_id has a prefix belonging to
        # a different marketplace (e.g. "demo-sg-*" on a tickpick TrackedEvent).
        _PREFIX_MAP = {
            "seatgeek": ("demo-sg-",),
            "stubhub":  ("demo-sh-", "sh-"),
            "ticketmaster": ("tm-",),
            "tickpick": ("tp-",),
            "gametime": ("gt-",),
            "vividseats": ("vs-",),
        }

        mismatches: list[str] = []
        for mp_slug, rows in te_by_mp.items():
            expected_prefixes = _PREFIX_MAP.get(mp_slug, ())
            for row in rows:
                eid = row["external_event_id"]
                if not eid:
                    continue
                # If no expected prefixes defined, skip prefix check
                if not expected_prefixes:
                    continue
                # If it's a demo ID for the wrong marketplace
                wrong = any(
                    eid.startswith(p)
                    for other_slug, prefixes in _PREFIX_MAP.items()
                    if other_slug != mp_slug
                    for p in prefixes
                )
                if wrong:
                    mismatches.append(
                        f"te_id={row['te_id']} mp={mp_slug} has foreign external_event_id={eid!r}"
                    )

        details["id_mismatches"] = mismatches
        if mismatches:
            warnings.append(
                f"{len(mismatches)} TrackedEvent(s) carry a foreign marketplace ID — "
                "fan-out will query wrong API endpoints"
            )

        # ── 5. Missing TrackedEvents ──────────────────────────────────────────
        all_active_mp = (await db.execute(
            select(Marketplace.slug).where(Marketplace.is_active == True)
        )).scalars().all()

        mp_without_te = [s for s in all_active_mp if s not in te_by_mp]
        details["marketplaces_without_tracked_events"] = mp_without_te
        if mp_without_te:
            warnings.append(
                f"No TrackedEvents exist for: {mp_without_te} — "
                "these collectors will never be reached via stage gate"
            )

        # ── 6. Recent PollRuns per collector ──────────────────────────────────
        # Approximate: look at recent PollRun rows and their count/status
        poll_rows = (await db.execute(
            select(PollRun)
            .order_by(PollRun.started_at.desc())
            .limit(50)
        )).scalars().all()

        details["recent_poll_runs"] = {
            "total": len(poll_rows),
            "success": sum(1 for p in poll_rows if p.status == "success"),
            "error": sum(1 for p in poll_rows if p.status == "error"),
            "pending": sum(1 for p in poll_rows if p.status is None),
        }

        # ── 7. TrackedEvents blocked at stage gate ────────────────────────────
        blocked = [
            row for row in te_rows
            if row[0].is_active and row[0].external_event_id is None
        ]
        details["stage_gate_blocked"] = len(blocked)
        if blocked:
            warnings.append(
                f"{len(blocked)} active TrackedEvent(s) blocked at stage gate "
                f"(no external_event_id) — marketplaces: "
                f"{list({row[1].slug for row in blocked})}"
            )

    await engine.dispose()

    # ── Print human-readable summary ─────────────────────────────────────────
    print("\n=== POLL STATE VALIDATION ===\n")

    print("TrackedEvents by marketplace:")
    for mp, info in sorted(details["tracked_events_by_marketplace"].items()):
        print(
            f"  {mp:<14}  count={info['count']}  active={info['active']}  "
            f"with_eid={info['with_external_id']}  "
            f"sample_ids={info['sample_ids']}"
        )

    print("\nActive listings by marketplace:")
    if details["active_listings_by_marketplace"]:
        for mp, cnt in sorted(details["active_listings_by_marketplace"].items()):
            print(f"  {mp:<14}  listings={cnt}")
    else:
        print("  (none)")

    print(f"\nDistinct marketplaces with listings: {details['distinct_marketplaces_with_listings']}")
    print(f"Marketplaces without TrackedEvents:  {details['marketplaces_without_tracked_events']}")
    print(f"Stage-gate blocked (no eid):         {details['stage_gate_blocked']}")
    print(f"ID mismatches:                       {len(details['id_mismatches'])}")
    if details["id_mismatches"]:
        for m in details["id_mismatches"]:
            print(f"  MISMATCH: {m}")

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  [WARN] {w}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  [FAIL] {f}")

    status = "FAIL" if failures else "PASS"
    print(f"\nOverall status: {status}")

    report = {
        "gate_name": "post-fanout-poll-state",
        "status": status,
        "duration_ms": int((time.monotonic() - _t0) * 1000),
        "details": details,
        "warnings": warnings,
        "failures": failures,
    }
    print(f"GATE_REPORT_JSON={json.dumps(report)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
