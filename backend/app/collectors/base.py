"""
BaseCollector — abstract contract every marketplace collector must implement.

To add TickPick or Gametime:
  1. Create collectors/tickpick.py
  2. class TickPickCollector(DebugMixin, BaseCollector)
  3. Implement: _fetch_listings, normalize_section
  4. Register in COLLECTOR_REGISTRY
"""

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
        self._db_session_factory = None  # Set by scheduler before each run

    async def collect(self, tracked_event) -> CollectorResult:
        if self.debug_mode:
            self._debug_log(
                f"Starting collection",
                event_id=tracked_event.event_id,
                url=tracked_event.external_url,
            )
        try:
            listings = await self._fetch_listings(tracked_event)
            return CollectorResult(
                marketplace_slug=self.marketplace_slug,
                event_id=tracked_event.event_id,
                listings=listings,
                fetched_at=datetime.utcnow(),
                raw_count=len(listings),
            )
        except Exception as exc:
            self.logger.exception("Collection failed: %s", exc)
            return CollectorResult(
                marketplace_slug=self.marketplace_slug,
                event_id=tracked_event.event_id,
                listings=[],
                fetched_at=datetime.utcnow(),
                raw_count=0,
                error=str(exc),
            )

    @abstractmethod
    async def _fetch_listings(self, tracked_event) -> list[RawListing]:
        ...

    @abstractmethod
    def normalize_section(self, raw_section: str) -> str:
        ...

    async def close(self):
        pass
