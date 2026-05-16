"""
Phase 4 Analytics Service — read-only intelligence layer.

Reads from: events, tracked_events, poll_runs, listings, listing_snapshots, venues.
NEVER writes to any ingestion table.
All queries are SELECT-only. No side effects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, TrackedEvent, Marketplace, Listing, ListingSnapshot, PollRun
from app.models.venue import Venue


# ── Response models ───────────────────────────────────────────────────────────

@dataclass
class MarketplaceCoverage:
    seatgeek: bool = False
    stubhub: bool = False


@dataclass
class ResolutionInfo:
    source: Optional[str]              # 'seeded' | 'resolved_api' | None
    seatgeek_external_id: Optional[str]
    stubhub_external_id: Optional[str]


@dataclass
class PollActivity:
    total_runs: int
    successful_runs: int
    last_run_at: Optional[datetime]
    listings_found_last_run: int
    new_listings_last_run: int
    disappeared_listings_last_run: int


@dataclass
class EventAnalyticsView:
    event_id: int
    title: str
    artist: Optional[str]
    event_date: datetime
    venue_slug: str
    venue_name: str
    days_until_event: float
    lifecycle_phase: Optional[str]
    marketplace_coverage: MarketplaceCoverage
    resolution: ResolutionInfo
    poll_activity: PollActivity
    poll_interval_minutes: int


@dataclass
class VenueAnalyticsView:
    venue_slug: str
    venue_name: str
    events_tracked: int
    events_stage3_eligible: int
    seatgeek_coverage: int   # events with seatgeek tracked_event
    stubhub_coverage: int    # events with stubhub tracked_event
    poll_runs_total: int
    avg_listings_per_run: Optional[float]


@dataclass
class ResolutionDistribution:
    seeded: int
    resolved_api: int
    pending: int


@dataclass
class PollRunSummary:
    total: int
    successful: int
    by_event: list[dict]     # [{event_title, run_count, total_listings_found}]


@dataclass
class DataAuditSummary:
    total_events: int
    total_tracked_events: int
    stage3_eligible: int
    resolution_distribution: ResolutionDistribution
    poll_runs: PollRunSummary
    marketplace_coverage: dict   # {seatgeek_only, stubhub_only, both, none}
    audit_at: datetime


# ── Service functions ─────────────────────────────────────────────────────────

async def get_data_audit(db: AsyncSession) -> DataAuditSummary:
    """
    STEP 1 audit queries — events, tracked_events, poll_runs only.

    SQL equivalents (for reference):

      -- tracked_events per event
      SELECT e.title, COUNT(te.id)
      FROM events e LEFT JOIN tracked_events te ON te.event_id = e.id
      GROUP BY e.id, e.title;

      -- resolution distribution
      SELECT
        SUM(CASE WHEN resolution_source = 'seeded' THEN 1 ELSE 0 END)       AS seeded,
        SUM(CASE WHEN resolution_source LIKE 'resolved_%' THEN 1 ELSE 0 END) AS resolved_api,
        SUM(CASE WHEN resolution_source IS NULL THEN 1 ELSE 0 END)           AS pending
      FROM tracked_events WHERE is_active = true;

      -- Stage 3 eligible count
      SELECT COUNT(*) FROM tracked_events
      WHERE is_active = true AND external_event_id IS NOT NULL;

      -- poll_runs per event (activity intensity)
      SELECT e.title, COUNT(pr.id), SUM(pr.listings_found)
      FROM events e
      JOIN tracked_events te ON te.event_id = e.id
      JOIN poll_runs pr ON pr.tracked_event_id = te.id
      GROUP BY e.id, e.title
      ORDER BY COUNT(pr.id) DESC;
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    total_events = (await db.execute(
        select(func.count()).select_from(Event)
    )).scalar_one()

    total_te = (await db.execute(
        select(func.count()).select_from(TrackedEvent).where(TrackedEvent.is_active == True)
    )).scalar_one()

    eligible = (await db.execute(
        select(func.count()).select_from(TrackedEvent).where(
            and_(TrackedEvent.is_active == True, TrackedEvent.external_event_id.is_not(None))
        )
    )).scalar_one()

    seeded_count = (await db.execute(
        select(func.count()).select_from(TrackedEvent).where(
            and_(TrackedEvent.is_active == True, TrackedEvent.resolution_source == "seeded")
        )
    )).scalar_one()

    api_count = (await db.execute(
        select(func.count()).select_from(TrackedEvent).where(
            and_(TrackedEvent.is_active == True, TrackedEvent.resolution_source.like("resolved_%"))
        )
    )).scalar_one()

    pending_count = (await db.execute(
        select(func.count()).select_from(TrackedEvent).where(
            and_(TrackedEvent.is_active == True, TrackedEvent.resolution_source.is_(None))
        )
    )).scalar_one()

    total_runs = (await db.execute(select(func.count()).select_from(PollRun))).scalar_one()
    success_runs = (await db.execute(
        select(func.count()).select_from(PollRun).where(PollRun.status == "success")
    )).scalar_one()

    # per-event poll run breakdown
    by_event_rows = (await db.execute(
        select(Event.title, func.count(PollRun.id), func.coalesce(func.sum(PollRun.listings_found), 0))
        .select_from(Event)
        .join(TrackedEvent, TrackedEvent.event_id == Event.id)
        .join(PollRun, PollRun.tracked_event_id == TrackedEvent.id)
        .group_by(Event.id, Event.title)
        .order_by(func.count(PollRun.id).desc())
    )).all()

    by_event = [
        {"event_title": row[0], "run_count": row[1], "total_listings_found": int(row[2])}
        for row in by_event_rows
    ]

    # marketplace coverage per event (seatgeek_only / stubhub_only / both / none)
    mp_rows = (await db.execute(
        select(
            Marketplace.slug,
            func.count(TrackedEvent.event_id.distinct()),
        )
        .select_from(TrackedEvent)
        .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
        .where(TrackedEvent.is_active == True)
        .group_by(Marketplace.slug)
    )).all()
    mp_by_slug = {row[0]: row[1] for row in mp_rows}

    both_count = (await db.execute(
        select(func.count())
        .select_from(
            select(TrackedEvent.event_id)
            .join(Marketplace, TrackedEvent.marketplace_id == Marketplace.id)
            .where(TrackedEvent.is_active == True)
            .group_by(TrackedEvent.event_id)
            .having(func.count(TrackedEvent.id) >= 2)
            .subquery()
        )
    )).scalar_one()

    return DataAuditSummary(
        total_events=total_events,
        total_tracked_events=total_te,
        stage3_eligible=eligible,
        resolution_distribution=ResolutionDistribution(
            seeded=seeded_count,
            resolved_api=api_count,
            pending=pending_count,
        ),
        poll_runs=PollRunSummary(
            total=total_runs,
            successful=success_runs,
            by_event=by_event,
        ),
        marketplace_coverage={
            "seatgeek": mp_by_slug.get("seatgeek", 0),
            "stubhub": mp_by_slug.get("stubhub", 0),
            "both": both_count,
        },
        audit_at=now,
    )


async def get_event_analytics(db: AsyncSession) -> list[EventAnalyticsView]:
    """
    STEP 2 EventAnalyticsView — per-event intelligence read model.
    Joins events → tracked_events → poll_runs → venues.
    No writes. No mutations.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    events = (await db.execute(
        select(Event).order_by(Event.event_date)
    )).scalars().all()

    venues = {
        v.id: v for v in (await db.execute(select(Venue))).scalars().all()
    }
    marketplaces = {
        m.id: m for m in (await db.execute(select(Marketplace))).scalars().all()
    }

    te_by_event: dict[int, list[TrackedEvent]] = {}
    all_te = (await db.execute(
        select(TrackedEvent).where(TrackedEvent.is_active == True)
    )).scalars().all()
    for te in all_te:
        te_by_event.setdefault(te.event_id, []).append(te)

    te_ids = [te.id for te in all_te]
    poll_by_te: dict[int, list[PollRun]] = {}
    if te_ids:
        all_runs = (await db.execute(
            select(PollRun)
            .where(PollRun.tracked_event_id.in_(te_ids))
            .order_by(PollRun.started_at.desc())
        )).scalars().all()
        for run in all_runs:
            poll_by_te.setdefault(run.tracked_event_id, []).append(run)

    views = []
    for event in events:
        venue = venues.get(event.venue_id)
        tes = te_by_event.get(event.id, [])
        days_out = (event.event_date - now).total_seconds() / 86400

        sg_te = next((te for te in tes if marketplaces.get(te.marketplace_id, object()).slug == "seatgeek"), None)
        sh_te = next((te for te in tes if marketplaces.get(te.marketplace_id, object()).slug == "stubhub"), None)

        all_runs_for_event: list[PollRun] = []
        for te in tes:
            all_runs_for_event.extend(poll_by_te.get(te.id, []))
        all_runs_for_event.sort(key=lambda r: r.started_at or datetime.min, reverse=True)

        last_run = all_runs_for_event[0] if all_runs_for_event else None
        successful = [r for r in all_runs_for_event if r.status == "success"]

        # resolution source: prefer resolved_api over seeded
        res_sources = {te.resolution_source for te in tes if te.resolution_source}
        res_source = "resolved_api" if "resolved_api" in res_sources else (res_sources.pop() if res_sources else None)

        poll_interval = min((te.poll_interval_minutes for te in tes), default=1440)
        lifecycle = next((te.lifecycle_phase for te in tes if te.lifecycle_phase), None)

        views.append(EventAnalyticsView(
            event_id=event.id,
            title=event.title,
            artist=event.artist,
            event_date=event.event_date,
            venue_slug=venue.slug if venue else "",
            venue_name=venue.name if venue else "",
            days_until_event=round(days_out, 2),
            lifecycle_phase=lifecycle,
            marketplace_coverage=MarketplaceCoverage(
                seatgeek=sg_te is not None,
                stubhub=sh_te is not None,
            ),
            resolution=ResolutionInfo(
                source=res_source,
                seatgeek_external_id=sg_te.external_event_id if sg_te else None,
                stubhub_external_id=sh_te.external_event_id if sh_te else None,
            ),
            poll_activity=PollActivity(
                total_runs=len(all_runs_for_event),
                successful_runs=len(successful),
                last_run_at=last_run.started_at if last_run else None,
                listings_found_last_run=last_run.listings_found if last_run else 0,
                new_listings_last_run=last_run.new_listings if last_run else 0,
                disappeared_listings_last_run=last_run.disappeared_listings if last_run else 0,
            ),
            poll_interval_minutes=poll_interval,
        ))

    return views


async def get_venue_analytics(db: AsyncSession) -> list[VenueAnalyticsView]:
    """
    STEP 2 VenueAnalyticsView — venue-level rollup of event coverage + polling.
    Read-only. No writes. No mutations.
    """
    venues = (await db.execute(select(Venue).order_by(Venue.name))).scalars().all()
    marketplaces = {m.slug: m.id for m in (await db.execute(select(Marketplace))).scalars().all()}
    sg_id = marketplaces.get("seatgeek")
    sh_id = marketplaces.get("stubhub")

    views = []
    for venue in venues:
        events = (await db.execute(
            select(Event).where(Event.venue_id == venue.id)
        )).scalars().all()

        if not events:
            continue

        event_ids = [e.id for e in events]

        all_te = (await db.execute(
            select(TrackedEvent).where(
                and_(TrackedEvent.event_id.in_(event_ids), TrackedEvent.is_active == True)
            )
        )).scalars().all()

        te_ids = [te.id for te in all_te]
        total_runs = 0
        total_listings = 0
        if te_ids:
            run_agg = (await db.execute(
                select(func.count(PollRun.id), func.coalesce(func.sum(PollRun.listings_found), 0))
                .where(PollRun.tracked_event_id.in_(te_ids))
            )).one()
            total_runs = run_agg[0]
            total_listings = int(run_agg[1])

        eligible = sum(1 for te in all_te if te.external_event_id is not None)
        sg_events = len({te.event_id for te in all_te if te.marketplace_id == sg_id})
        sh_events = len({te.event_id for te in all_te if te.marketplace_id == sh_id})

        views.append(VenueAnalyticsView(
            venue_slug=venue.slug,
            venue_name=venue.name,
            events_tracked=len(events),
            events_stage3_eligible=eligible,
            seatgeek_coverage=sg_events,
            stubhub_coverage=sh_events,
            poll_runs_total=total_runs,
            avg_listings_per_run=round(total_listings / total_runs, 2) if total_runs else None,
        ))

    return views
