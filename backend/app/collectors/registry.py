from typing import Type
from app.collectors.base import BaseCollector
from app.collectors.stubhub import StubHubCollector
from app.collectors.seatgeek import SeatGeekCollector
from app.collectors.ticketmaster import TicketmasterCollector
from app.collectors.tickpick import TickPickCollector
from app.collectors.gametime import GameTimeCollector
from app.collectors.vividseats import VividSeatsCollector

COLLECTOR_REGISTRY: dict[str, Type[BaseCollector]] = {
    "stubhub":      StubHubCollector,
    "seatgeek":     SeatGeekCollector,
    "ticketmaster": TicketmasterCollector,
    "tickpick":     TickPickCollector,
    "gametime":     GameTimeCollector,
    "vividseats":   VividSeatsCollector,
}


def get_collector(marketplace_slug: str, settings, debug_mode: bool = False, slow_mo_ms: int = 0) -> BaseCollector | None:
    cls = COLLECTOR_REGISTRY.get(marketplace_slug)
    if cls is None:
        return None
    return cls(settings, debug_mode=debug_mode, slow_mo_ms=slow_mo_ms)
