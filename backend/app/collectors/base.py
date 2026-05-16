from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
import logging

from app.collectors.debug_mixin import DebugMixin

logger = logging.getLogger(__name__)


@dataclass
class RawListing:
    external_listing_id: str
    section: str
    row: Optional[str]
    quantity: int
    price: Decimal
    fees: Optional[Decimal] = None
    all_in_price: Optional[Decimal] = None
    listing_url: Optional[str] = None
    market_segment: Optional[str] = None   # "primary" | "verified_resale" | None
    extra: dict = field(default_factory=dict)


@dataclass
class CollectorResult:
    marketplace_slug: str
    event_id: int
    listings: list[RawListing]
    fetched_at: datetime
    raw_count: int
    error: Optional[str] = None


class BaseCollector(DebugMixin, ABC):
    marketplace_slug: str = ""

    def __init__(self, settings, debug_mode: bool = False, slow_mo_ms: int = 0):
        self.settings = settings
        self.debug_mode = debug_mode
        self.slow_mo_ms = slow_mo_ms
        self.logger = logging.getLogger(f"collector.{self.marketplace_slug}")
        self._db_session_factory = None

    async def collect(self, tracked_event) -> CollectorResult:
        resolved_id = await self.resolve_external_event_id(tracked_event)

        if resolved_id is None:
            self.logger.info(
                "STAGE_GATE SKIPPED_MISSING_RESOLUTION tracked_event=%d url=%s",
                tracked_event.id, tracked_event.external_url,
            )
            return CollectorResult(
                marketplace_slug=self.marketplace_slug,
                event_id=tracked_event.event_id,
                listings=[], fetched_at=datetime.utcnow(), raw_count=0,
                error="unresolved_event_id",
            )

        if not tracked_event.external_event_id:
            tracked_event.external_event_id = resolved_id
            await self._persist_resolved_event_id(tracked_event.id, resolved_id)

        try:
            listings = await self._fetch_listings(tracked_event)
            return CollectorResult(
                marketplace_slug=self.marketplace_slug, event_id=tracked_event.event_id,
                listings=listings, fetched_at=datetime.utcnow(), raw_count=len(listings),
            )
        except Exception as exc:
            self.logger.exception("COLLECTOR: INTEGRATION_FAILURE %s — %s", self.marketplace_slug, exc)
            return CollectorResult(
                marketplace_slug=self.marketplace_slug, event_id=tracked_event.event_id,
                listings=[], fetched_at=datetime.utcnow(), raw_count=0, error=str(exc),
            )

    async def resolve_external_event_id(self, tracked_event) -> Optional[str]:
        """Subclasses override to add marketplace-specific search resolution."""
        return tracked_event.external_event_id or None

    async def _persist_resolved_event_id(self, tracked_event_id: int, resolved_id: str) -> None:
        if not self._db_session_factory:
            return
        try:
            from sqlalchemy import update as sa_update
            from app.models import TrackedEvent
            async with self._db_session_factory() as db:
                await db.execute(
                    sa_update(TrackedEvent)
                    .where(TrackedEvent.id == tracked_event_id)
                    .values(external_event_id=resolved_id)
                )
                await db.commit()
            self.logger.info(
                "RESOLVER: persisted event_id=%s tracked_event=%d",
                resolved_id, tracked_event_id,
            )
        except Exception as exc:
            self.logger.warning("RESOLVER: failed to persist event_id — %s", exc)

    @abstractmethod
    async def _fetch_listings(self, tracked_event) -> list[RawListing]: ...

    @abstractmethod
    def normalize_section(self, raw_section: str) -> str: ...

    async def close(self):
        pass
