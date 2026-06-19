"""
EventDiscovery — Stage 0 of the ingestion pipeline.

Runs every 6 hours. Scans StubHub and SeatGeek for concerts at known LA venues
within the admission window (14–21 days out), deduplicates against existing
events by canonical_id, and creates Event + TrackedEvent rows for new finds.

New tracked_events created here have external_event_id=NULL and
resolution_source=NULL. They enter the Stage 2 resolver on its next cycle.

Admission window:
  min_days = 14   events closer than this are either already tracked or missed
  max_days = 21   events further than this are not yet worth ingesting

Duplicate-prevention guardrails (in addition to canonical_id match):
  1. SeatGeek datetime_utc is converted to venue-local (America/Los_Angeles)
     time before canonical date generation, preventing off-by-one-day duplicates
     when UTC midnight crosses a PDT calendar boundary.
  2. Before creating a new Event, the existing DB is searched for a same-venue /
     same-local-date event whose normalized title matches. If found, the new
     TrackedEvent is attached to the existing Event instead.
  3. If a same-venue/same-date event exists but cannot be confidently matched,
     creation is skipped and NEEDS_REVIEW is logged.

Freeze / cap:
  When settings.discovery_freeze=True, scan runs but no DB rows are written.
  New Event creation is also blocked when the event count reaches
  settings.max_tracked_events.
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select, func

from app.models import Event, Marketplace, TrackedEvent, Venue
from app.utils.event_trace import emit_event_trace

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Discovery admission window bounds (days before event)
_ADMISSION_MIN_DAYS = 14
_ADMISSION_MAX_DAYS = 21

# All tracked venues are in the America/Los_Angeles timezone.
_LA_TZ = ZoneInfo("America/Los_Angeles")

# Venue keyword sets used to match marketplace venue names to local slugs.
# Each entry is (slug, set_of_substrings_any_of_which_match).
_VENUE_KEYWORDS: list[tuple[str, set[str]]] = [
    ("crypto-arena",   {"crypto.com arena", "staples center", "crypto arena"}),
    ("sofi-stadium",   {"sofi stadium", "sofi"}),
    ("hollywood-bowl", {"hollywood bowl"}),
]


# ── Canonical ID ──────────────────────────────────────────────────────────────

def _canonical_id(title: str, venue_slug: str, event_date: datetime) -> str:
    raw = f"{venue_slug}|{event_date.date()}|{title.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Title normalization for duplicate detection ───────────────────────────────

def _normalize_title(title: str) -> str:
    """
    Reduce an event title to its core artist/act name for near-duplicate
    detection.  Strips tour subtitles, featuring credits, and punctuation so
    that title variants of the same show compare equal.

    Examples:
        "Ariana Grande: Eternal Sunshine Tour"  →  "ariana grande"
        "Ariana Grande"                          →  "ariana grande"
        "Rush (Classic Albums Live)"             →  "rush"
        "Foo Fighters & LA Philharmonic"         →  "foo fighters  la philharmonic"
    """
    # Strip tour subtitle after colon (most common pattern)
    title = title.split(":")[0].strip()
    # Strip "with <opener>" / "ft." / "feat." — keep main headliner only
    for sep in (" with ", " ft. ", " feat. ", " featuring "):
        idx = title.lower().find(sep)
        if idx > 0:
            title = title[:idx]
    # Strip parenthetical content: "Rush (Classic Albums Live)" → "Rush"
    title = re.sub(r"\s*\([^)]*\)", "", title)
    # Lowercase, strip punctuation, collapse whitespace
    title = re.sub(r"[^\w\s]", "", title.lower()).strip()
    title = re.sub(r"\s+", " ", title)
    return title


# ── Timezone conversion ───────────────────────────────────────────────────────

def _to_la_local(dt: datetime) -> datetime:
    """
    Convert a datetime to America/Los_Angeles local time, returning a naive
    datetime (no tzinfo).

    - Timezone-aware input: converted to LA local then tz stripped.
    - Naive input: treated as already local and returned unchanged.
    """
    if dt.tzinfo is None:
        return dt  # already naive/local — no conversion needed
    return dt.astimezone(_LA_TZ).replace(tzinfo=None)


# ── Venue slug matcher ────────────────────────────────────────────────────────

def _match_venue_slug(marketplace_venue_name: str) -> Optional[str]:
    """Map a marketplace venue name string to a local venue slug, or None."""
    name_lower = marketplace_venue_name.lower()
    for slug, keywords in _VENUE_KEYWORDS:
        if any(kw in name_lower for kw in keywords):
            return slug
    return None


# ── DiscoveredEvent dataclass ─────────────────────────────────────────────────

@dataclass
class DiscoveredEvent:
    title: str
    artist: str
    venue_name: str          # as returned by marketplace
    venue_slug: str          # matched to local slug
    event_date: datetime     # always venue-local naive datetime
    external_event_id: str
    external_url: str
    marketplace_slug: str
    extra: dict = field(default_factory=dict)


# ── EventDiscovery class ──────────────────────────────────────────────────────

class EventDiscovery:
    """
    Scans marketplaces for new LA events within the 14–21 day admission window.
    Deduplicates by canonical_id (exact) and by venue+date+normalized-title
    (near-match). New events enter the resolver pipeline.
    """

    def __init__(self, settings):
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
                follow_redirects=True,
                timeout=15.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Public entry point ────────────────────────────────────────────────────

    async def run_discovery(self, session_factory) -> dict:
        """
        Scan all active marketplaces. Ingest events within admission window.
        Returns counts per outcome type.
        """
        counts = {
            "new": 0,
            "duplicate": 0,
            "outside_window": 0,
            "no_venue": 0,
            "failed": 0,
            # New outcome types
            "frozen": 0,          # freeze active — scan ran but no DB writes
            "cap_reached": 0,     # event count at max_tracked_events cap
            "duplicate_prevented": 0,  # near-dup detected, TE attached to existing event
            "needs_review": 0,    # same-venue/date but no confident title match — skipped
        }

        async with session_factory() as db:
            mp_result = await db.execute(
                select(Marketplace).where(Marketplace.is_active == True)
            )
            marketplaces = mp_result.scalars().all()

            venue_result = await db.execute(select(Venue))
            venues = {v.slug: v for v in venue_result.scalars().all()}

        window_start = datetime.utcnow() + timedelta(days=_ADMISSION_MIN_DAYS)
        window_end   = datetime.utcnow() + timedelta(days=_ADMISSION_MAX_DAYS)

        if self.settings.discovery_freeze:
            logger.info(
                "EVENT_FREEZE_ACTIVE: discovery scan running in observe-only mode "
                "(window %s → %s) — no Event or TrackedEvent rows will be created",
                window_start.date(), window_end.date(),
            )
        else:
            logger.info(
                "DISCOVERY: scanning window %s → %s",
                window_start.date(), window_end.date(),
            )

        for mp in marketplaces:
            try:
                discovered = await self._scan_marketplace(mp.slug, window_start, window_end)
            except Exception as exc:
                logger.warning("DISCOVERY: scan failed mp=%s — %s", mp.slug, exc)
                counts["failed"] += 1
                continue

            logger.info("DISCOVERY: mp=%s found=%d candidates", mp.slug, len(discovered))

            for item in discovered:
                outcome = await self._ingest(session_factory, mp, item, venues)
                counts[outcome] += 1

        # Log non-zero outcomes for observability
        non_zero = {k: v for k, v in counts.items() if v}
        logger.info("DISCOVERY: cycle complete — %s", non_zero)
        return counts

    # ── Marketplace scan dispatch ─────────────────────────────────────────────

    async def _scan_marketplace(
        self,
        slug: str,
        window_start: datetime,
        window_end: datetime,
    ) -> list[DiscoveredEvent]:
        if slug == "seatgeek":
            return await self._scan_seatgeek(window_start, window_end)
        if slug == "stubhub":
            return await self._scan_stubhub(window_start, window_end)
        logger.debug("DISCOVERY: no scanner for marketplace '%s'", slug)
        return []

    # ── SeatGeek scanner ──────────────────────────────────────────────────────

    async def _scan_seatgeek(
        self, window_start: datetime, window_end: datetime
    ) -> list[DiscoveredEvent]:
        client = await self._get_client()
        discovered: list[DiscoveredEvent] = []

        params: dict = {
            "venue.city": "Los Angeles",
            "datetime_utc.gte": window_start.strftime("%Y-%m-%d"),
            "datetime_utc.lte": window_end.strftime("%Y-%m-%d"),
            "per_page": 100,
            "type": "concert",
        }
        if self.settings.seatgeek_client_id:
            params["client_id"] = self.settings.seatgeek_client_id
            if self.settings.seatgeek_client_secret:
                params["client_secret"] = self.settings.seatgeek_client_secret
            api_url = "https://api.seatgeek.com/2/events"
        else:
            api_url = "https://seatgeek.com/api/events"

        try:
            resp = await client.get(api_url, params=params)
            if resp.status_code != 200:
                logger.warning(
                    "DISCOVERY: SeatGeek scan http=%d — DATA_GAP", resp.status_code
                )
                return []
            events = resp.json().get("events", [])
        except Exception as exc:
            logger.debug("DISCOVERY: SeatGeek scan error — %s", exc)
            return []

        for ev in events:
            try:
                venue_name = ev.get("venue", {}).get("name", "")
                venue_slug = _match_venue_slug(venue_name)
                if not venue_slug:
                    continue  # not a tracked LA venue

                title = ev.get("title", "") or ev.get("short_title", "")
                performers = ev.get("performers", [])
                artist = performers[0].get("name", title) if performers else title

                raw_date = ev.get("datetime_utc") or ev.get("datetime_local")
                if not raw_date:
                    continue

                # ── Timezone fix ──────────────────────────────────────────────
                # SeatGeek returns datetime_utc. An 8 pm PDT show appears as
                # "next day" in UTC (e.g. 2026-06-19T03:00Z for Jun 18 8pm PDT).
                # We convert to venue-local time so the canonical date matches
                # the date printed on the ticket, preventing off-by-one-day
                # duplicate Event rows from being created on separate scans.
                dt_aware = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                event_date = _to_la_local(dt_aware)

                external_event_id = str(ev["id"])
                slug_part = ev.get("slug", "")
                external_url = f"https://seatgeek.com/{slug_part}" if slug_part else ""

                discovered.append(DiscoveredEvent(
                    title=title,
                    artist=artist,
                    venue_name=venue_name,
                    venue_slug=venue_slug,
                    event_date=event_date,
                    external_event_id=external_event_id,
                    external_url=external_url,
                    marketplace_slug="seatgeek",
                    extra={"seatgeek_raw": {k: ev.get(k) for k in ("id", "type", "score")}},
                ))
            except Exception as exc:
                logger.debug("DISCOVERY: SeatGeek parse error — %s", exc)
                continue

        return discovered

    # ── StubHub scanner ───────────────────────────────────────────────────────

    async def _scan_stubhub(
        self, window_start: datetime, window_end: datetime
    ) -> list[DiscoveredEvent]:
        """
        StubHub SOLR requires session auth in most environments.
        Attempt the search; log DATA_GAP gracefully if it fails.
        """
        client = await self._get_client()
        discovered: list[DiscoveredEvent] = []

        date_from = window_start.strftime("%Y-%m-%dT00:00:00Z")
        date_to   = window_end.strftime("%Y-%m-%dT00:00:00Z")
        solr_url = (
            "https://www.stubhub.com/listingCatalog/select"
            f"?q=*:*&fq=city_name:Los+Angeles"
            f"&fq=event_date:[{date_from}+TO+{date_to}]"
            "&rows=100&fl=event_id,event_name,event_date_local,venue_name"
            "&wt=json&sort=event_date+asc"
        )
        try:
            resp = await client.get(solr_url)
            if resp.status_code != 200:
                logger.warning(
                    "DISCOVERY: StubHub SOLR http=%d — DATA_GAP (auth required)",
                    resp.status_code,
                )
                return []
            docs = resp.json().get("response", {}).get("docs", [])
        except Exception as exc:
            logger.debug("DISCOVERY: StubHub SOLR error — %s", exc)
            return []

        for doc in docs:
            try:
                venue_name = doc.get("venue_name", "")
                venue_slug = _match_venue_slug(venue_name)
                if not venue_slug:
                    continue

                title = doc.get("event_name", "")
                raw_date = doc.get("event_date_local", "")
                if not raw_date:
                    continue
                # StubHub provides event_date_local — already in venue-local time.
                event_date = datetime.fromisoformat(raw_date[:19])
                external_event_id = str(doc["event_id"])
                slug_part = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                external_url = f"https://www.stubhub.com/{slug_part}-tickets"

                discovered.append(DiscoveredEvent(
                    title=title,
                    artist=title,
                    venue_name=venue_name,
                    venue_slug=venue_slug,
                    event_date=event_date,
                    external_event_id=external_event_id,
                    external_url=external_url,
                    marketplace_slug="stubhub",
                ))
            except Exception as exc:
                logger.debug("DISCOVERY: StubHub parse error — %s", exc)
                continue

        return discovered

    # ── Ingestion ─────────────────────────────────────────────────────────────

    async def _ingest(
        self,
        session_factory,
        mp: Marketplace,
        item: DiscoveredEvent,
        venues: dict[str, Venue],
    ) -> str:
        """
        Attempt to ingest one discovered event.

        Returns one of:
          'new'                  — new Event + new TrackedEvent created
          'duplicate'            — Event and/or TrackedEvent already existed
          'duplicate_prevented'  — near-dup detected; new TE attached to existing event
          'needs_review'         — same-venue/date with no confident title match; skipped
          'outside_window'       — event date outside admission window
          'no_venue'             — venue slug not found in local DB
          'frozen'               — DISCOVERY_FREEZE active; no DB writes performed
          'cap_reached'          — event count at max_tracked_events; new Event blocked
          'failed'               — unexpected exception
        """
        try:
            # ── 1. Admission window re-check ──────────────────────────────────
            now = datetime.utcnow()
            days_out = (item.event_date - now).total_seconds() / 86400
            if not (_ADMISSION_MIN_DAYS <= days_out <= _ADMISSION_MAX_DAYS):
                return "outside_window"

            # ── 2. Venue check ────────────────────────────────────────────────
            venue = venues.get(item.venue_slug)
            if not venue:
                logger.debug(
                    "DISCOVERY: no local venue for slug='%s' event='%s'",
                    item.venue_slug, item.title,
                )
                return "no_venue"

            # ── 3. EVENT FREEZE CHECK ─────────────────────────────────────────
            # Must happen before any DB write. Scan output is logged above in
            # run_discovery() so operators can see what was found without DB changes.
            if self.settings.discovery_freeze:
                logger.info(
                    "EVENT_FREEZE_ACTIVE: skipped event='%s' marketplace=%s "
                    "venue=%s date=%s reason=frozen",
                    item.title, mp.slug, item.venue_slug, item.event_date.date(),
                )
                return "frozen"

            # ── 4. Canonical ID lookup + near-duplicate check ─────────────────
            canonical = _canonical_id(item.title, item.venue_slug, item.event_date)
            local_date = item.event_date.date()
            norm_title = _normalize_title(item.title)
            is_new_event = False
            attached_to_existing = False

            async with session_factory() as db:

                # 4a. Exact canonical_id match
                ev_result = await db.execute(
                    select(Event).where(Event.canonical_id == canonical)
                )
                event = ev_result.scalar_one_or_none()

                if not event:
                    # 4b. Near-duplicate check: same venue + same local date.
                    # Compare after converting stored event_date to LA local time so
                    # both old events (stored as naive-UTC-wrong) and new events
                    # (stored as proper UTC) resolve to the same local calendar date.
                    nearby_result = await db.execute(
                        select(Event).where(
                            Event.venue_id == venue.id,
                            func.date(
                                func.timezone("America/Los_Angeles", Event.event_date)
                            ) == local_date,
                        )
                    )
                    nearby_events = nearby_result.scalars().all()

                    matched_event = None

                    # Check normalized title match
                    for candidate in nearby_events:
                        if _normalize_title(candidate.title) == norm_title:
                            matched_event = candidate
                            break

                    # Check shared external_event_id (different title but same source ID)
                    if matched_event is None and item.external_event_id:
                        ext_te_result = await db.execute(
                            select(TrackedEvent).where(
                                TrackedEvent.external_event_id == item.external_event_id,
                            )
                        )
                        for te in ext_te_result.scalars().all():
                            if te.event_id:
                                cand_event = (await db.execute(
                                    select(Event).where(
                                        Event.id == te.event_id,
                                        Event.venue_id == venue.id,
                                    )
                                )).scalar_one_or_none()
                                if cand_event:
                                    matched_event = cand_event
                                    break

                    if matched_event is not None:
                        # Near-duplicate detected — attach to existing event
                        logger.info(
                            "DISCOVERY: duplicate_prevented event='%s' venue=%s "
                            "date=%s mp=%s → attaching to existing event_id=%d "
                            "(canonical_id=%s norm_title=%r)",
                            item.title, item.venue_slug, local_date, mp.slug,
                            matched_event.id, matched_event.canonical_id, norm_title,
                        )
                        event = matched_event
                        attached_to_existing = True

                    elif nearby_events:
                        # Same venue + same date but no confident match.
                        # Skip creation to avoid an unconfirmed duplicate.
                        logger.warning(
                            "DISCOVERY: NEEDS_REVIEW event='%s' venue=%s date=%s "
                            "mp=%s — same-venue/date candidates=%s but no "
                            "title/external-id match. Skipping creation.",
                            item.title, item.venue_slug, local_date, mp.slug,
                            [e.id for e in nearby_events],
                        )
                        return "needs_review"

                    else:
                        # Genuinely new event — enforce cap before creating
                        event_count = (await db.execute(
                            select(func.count()).select_from(Event)
                        )).scalar_one()

                        if event_count >= self.settings.max_tracked_events:
                            logger.warning(
                                "EVENT_CAP_REACHED: cannot create event='%s' mp=%s "
                                "(count=%d >= cap=%d)",
                                item.title, mp.slug,
                                event_count, self.settings.max_tracked_events,
                            )
                            return "cap_reached"

                        # Convert naive venue-local datetime to UTC-aware before storing.
                        # item.event_date is a naive LA-local datetime; attaching _LA_TZ
                        # and letting PostgreSQL handle the UTC conversion prevents the
                        # "local time stored as UTC" bug that affected Ariana events 25-28.
                        event_date_utc = item.event_date.replace(tzinfo=_LA_TZ)
                        event = Event(
                            canonical_id=canonical,
                            title=item.title,
                            artist=item.artist,
                            venue_id=venue.id,
                            event_date=event_date_utc,
                        )
                        db.add(event)
                        await db.flush()  # assigns event.id
                        is_new_event = True
                        logger.info(
                            "DISCOVERY: new event='%s' venue='%s' date=%s mp=%s",
                            item.title, item.venue_slug,
                            item.event_date.date(), mp.slug,
                        )

                # ── 5. TrackedEvent check ─────────────────────────────────────
                te_result = await db.execute(
                    select(TrackedEvent).where(
                        TrackedEvent.event_id == event.id,
                        TrackedEvent.marketplace_id == mp.id,
                    )
                )
                existing_te = te_result.scalar_one_or_none()

                if existing_te:
                    await db.commit()
                    return "duplicate"

                # ── 6. Create TrackedEvent ────────────────────────────────────
                db.add(TrackedEvent(
                    event_id=event.id,
                    marketplace_id=mp.id,
                    external_url=item.external_url,
                    external_event_id=item.external_event_id or None,
                    resolution_source="resolved_api" if item.external_event_id else None,
                    is_active=True,
                    poll_interval_minutes=1440,
                    next_poll_at=now + timedelta(minutes=1440),
                ))
                await db.commit()

            logger.info(
                "DISCOVERY: ingested new tracked_event event='%s' mp=%s",
                item.title, mp.slug,
            )
            emit_event_trace("INGEST", event.id, {
                "external_event_id": item.external_event_id or None,
                "marketplace": mp.slug,
                "source": "discovery",
            })

            if attached_to_existing:
                return "duplicate_prevented"
            return "new"

        except Exception as exc:
            logger.warning("DISCOVERY: ingest failed event='%s' — %s", item.title, exc)
            return "failed"
