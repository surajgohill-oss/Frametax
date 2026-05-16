"""
Phase 5 signal + decision dataclasses.

All values are derived from listing_snapshots and Phase 4 aggregates.
No marketplace names — only marketplace_id (integer FK).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EventDecision(str, Enum):
    DEAL_FORMING       = "DEAL_FORMING"
    MARKET_DISLOCATION = "MARKET_DISLOCATION"
    STABLE             = "STABLE"
    INSUFFICIENT_DATA  = "INSUFFICIENT_DATA"


@dataclass
class PriceMomentumSignal:
    """
    price_momentum = velocity_24h - velocity_7d

    velocity_24h: avg-price change over the last 24-h window vs. the prior 24 h.
    velocity_7d:  avg-price change over the last 7-d window vs. the prior 7 d.

    > 0 = acceleration upward
    < 0 = acceleration downward
    """
    velocity_24h:    Optional[float]
    velocity_7d:     Optional[float]
    price_momentum:  Optional[float]
    has_data:        bool = False


@dataclass
class LiquidityPressureSignal:
    """
    liquidity_pressure = inventory_delta_24h / max_inventory_30d

    inventory_delta_24h: ticket-quantity change vs. 24 h ago (negative = contraction).
    max_inventory_30d:   peak inventory in the trailing 30-day window.

    Large negative value = rapid supply contraction.
    """
    inventory_now:        Optional[float]
    inventory_24h_ago:    Optional[float]
    max_inventory_30d:    Optional[float]
    inventory_delta_24h:  Optional[float]
    liquidity_pressure:   Optional[float]
    has_data:             bool = False


@dataclass
class MarketDivergenceSignal:
    """
    divergence_index = (MAX_price - MIN_price) / MIN_price

    Computed only when marketplace_count >= 2.
    Keys in price_by_marketplace are marketplace_id integers (never names).
    """
    price_by_marketplace: dict[int, float] = field(default_factory=dict)
    marketplace_count:    int   = 0
    divergence_index:     Optional[float] = None
    has_data:             bool  = False


@dataclass
class ScarcityAccelerationSignal:
    """
    scarcity_acceleration = scarcity_index_now - scarcity_index_24h_ago

    scarcity_index = peak_inventory_30d / (current_inventory + ε)
    Values > 1.0 mean supply is below its 30-day peak.
    Strong positive acceleration = rapid tightening.
    """
    scarcity_index_now:      Optional[float]
    scarcity_index_24h_ago:  Optional[float]
    scarcity_acceleration:   Optional[float]
    has_data:                bool = False


@dataclass
class EventSignalBundle:
    event_id:    int
    computed_at: datetime

    price_momentum:      PriceMomentumSignal
    liquidity_pressure:  LiquidityPressureSignal
    market_divergence:   MarketDivergenceSignal
    scarcity:            ScarcityAccelerationSignal

    decision:            EventDecision
    decision_reasons:    list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "event_id":    self.event_id,
            "computed_at": self.computed_at.isoformat(),
            "decision":    self.decision.value,
            "decision_reasons": self.decision_reasons,
            "signals": {
                "price_momentum":     dataclasses.asdict(self.price_momentum),
                "liquidity_pressure": dataclasses.asdict(self.liquidity_pressure),
                "market_divergence":  dataclasses.asdict(self.market_divergence),
                "scarcity":           dataclasses.asdict(self.scarcity),
            },
        }
