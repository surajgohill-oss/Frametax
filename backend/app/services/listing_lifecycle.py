"""
listing_lifecycle.py — Listing Lifecycle Service (skeleton / Phase 2 target)

Defines the shape of listing state transitions observed via repeated
listing_snapshots polling. The full detection model is not yet implemented.

Lifecycle states:
  appeared       — listing first seen in a polling window
  disappeared    — listing absent from a poll that previously captured it
  reappeared     — listing returned after ≥1 missing poll
  likely_sold    — disappeared and did not return within the observation window;
                   no price/quantity change pattern suggesting relist
  likely_relisted — listing disappeared then a new listing appeared at
                   similar price / same section; assumed to be same ticket re-listed
  unknown        — insufficient data to classify (e.g. first poll only)

Not yet implemented:
  - Relist fingerprinting (section + price similarity)
  - Sold vs. relist confidence score
  - Multi-poll sequence analysis
  - Attribution to sales velocity

TODO (Phase 2):
  1. Add listing_lifecycle_events table to track state transitions per listing_id
  2. Implement _detect_transitions(prev_snapshot, curr_snapshot) → list[LifecycleEvent]
  3. Wire into the poll job so transitions are written after each poll completes
  4. Add GET /api/events/{id}/listing-lifecycle for per-event transition history
  5. Use transition data in absorption classification (disappeared ≥ 80% = likely_sold burst)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ListingState(str, Enum):
    appeared        = "appeared"
    disappeared     = "disappeared"
    reappeared      = "reappeared"
    likely_sold     = "likely_sold"
    likely_relisted = "likely_relisted"
    unknown         = "unknown"


@dataclass
class LifecycleEvent:
    listing_id:    int
    event_id:      int
    marketplace_id: int
    state:         ListingState
    detected_at:   datetime
    price:         Optional[float]
    quantity:      Optional[int]
    prior_state:   Optional[ListingState]
    confidence:    float            # 0.0–1.0; always 0.0 until model is implemented
    notes:         Optional[str]


# ── Placeholder detection function ───────────────────────────────────────────

async def detect_lifecycle_transitions(
    event_id: int,
    poll_run_id: int,
    session_factory,
) -> list[LifecycleEvent]:
    """
    TODO: Compare current poll_run snapshots against previous poll_run snapshots
    and emit LifecycleEvent objects for each state change.

    Returns empty list until Phase 2 implementation.
    """
    # Phase 2: implement delta detection across consecutive poll_runs
    return []


async def get_event_lifecycle_summary(
    event_id: int,
    session_factory,
) -> dict:
    """
    TODO: Return aggregate lifecycle stats for an event:
      - total_appeared, total_disappeared, total_likely_sold, total_likely_relisted
      - absorption_rate: likely_sold / appeared (%)
      - relist_rate: likely_relisted / disappeared (%)

    Returns stub until Phase 2 implementation.
    """
    return {
        "event_id":          event_id,
        "status":            "not_implemented",
        "message":           "Listing lifecycle detection not yet implemented. See listing_lifecycle.py TODO notes.",
        "states_defined":    [s.value for s in ListingState],
        "total_appeared":    None,
        "total_disappeared": None,
        "total_likely_sold": None,
        "total_likely_relisted": None,
        "absorption_rate":   None,
        "relist_rate":       None,
    }
