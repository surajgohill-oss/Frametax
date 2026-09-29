"""
test_canonical_production_view_floor_ceiling.py

Pure unit tests for canonical_production_view._aggregate_segment_incentive_
floor_ceiling — the fix for the confirmed SERVED_FIELD_MAPPING_DEFECT where
total_incentive_floor_usd and total_incentive_ceiling_usd both silently
repeated selected_incentive_usd, discarding the genuinely distinct
per-segment values allocation_pricing.py already computes and
canonical_evaluation.py already persists in
calculation_trace_json["segments"].

No DB, no fixtures beyond hand-built trace dicts — these test the pure
aggregation function in isolation against the EXACT shape
_segment_dicts() (canonical_evaluation.py) actually persists.
"""
from __future__ import annotations

from app.services.canonical_production_view import _aggregate_segment_incentive_floor_ceiling


class TestAggregateSegmentIncentiveFloorCeiling:
    def test_single_segment_unconfirmed_ceiling_real_lu_shape(self):
        # The exact real Little Utopia MU segment shape read from the live
        # acceptance database's calculation_trace_json before this fix.
        trace = {
            "segments": [
                {
                    "jurisdiction_code": "MU",
                    "qpe_usd": 4_355_327.00,
                    "incentive_floor_usd": 1_306_598.10,
                    "incentive_ceiling_usd": 1_742_130.80,
                    "ceiling_requires_confirmation": True,
                },
                {
                    "jurisdiction_code": "US",
                    "qpe_usd": 0.0,
                    "incentive_floor_usd": 0.0,
                    "incentive_ceiling_usd": 0.0,
                    "ceiling_requires_confirmation": False,
                },
            ],
        }
        floor, ceiling, requires_confirmation = _aggregate_segment_incentive_floor_ceiling(trace)
        assert floor == 1_306_598.10
        assert ceiling == 1_742_130.80
        assert floor != ceiling, "the exact defect this fix repairs: floor and ceiling must never collapse to one value"
        assert requires_confirmation is True

    def test_confirmed_ceiling_segment_still_reports_distinct_floor(self):
        # Even when a production-specific approval confirms the ceiling
        # (selected_incentive_usd would equal the ceiling in that case),
        # the floor must still be reported as its own real, distinct value
        # -- never collapsed toward whichever one is currently selected.
        trace = {
            "segments": [
                {"jurisdiction_code": "MU", "incentive_floor_usd": 1_306_598.10,
                 "incentive_ceiling_usd": 1_742_130.80, "ceiling_requires_confirmation": False},
            ],
        }
        floor, ceiling, requires_confirmation = _aggregate_segment_incentive_floor_ceiling(trace)
        assert floor == 1_306_598.10
        assert ceiling == 1_742_130.80
        assert requires_confirmation is False

    def test_multi_segment_structure_sums_each_segments_floor_and_ceiling(self):
        trace = {
            "segments": [
                {"jurisdiction_code": "MU", "incentive_floor_usd": 100_000.0, "incentive_ceiling_usd": 150_000.0, "ceiling_requires_confirmation": True},
                {"jurisdiction_code": "CA-MB", "incentive_floor_usd": 50_000.0, "incentive_ceiling_usd": 50_000.0, "ceiling_requires_confirmation": False},
            ],
        }
        floor, ceiling, requires_confirmation = _aggregate_segment_incentive_floor_ceiling(trace)
        assert floor == 150_000.0
        assert ceiling == 200_000.0
        assert requires_confirmation is True  # any segment requiring confirmation flags the whole structure

    def test_pre_enrichment_row_with_no_segments_falls_back_gracefully(self):
        # A row persisted before per-segment floor/ceiling existed at all
        # must degrade to (None, None, False), never fabricate a value —
        # the caller then falls back to selected_incentive_usd for both,
        # same established backward-compat pattern used throughout this file.
        floor, ceiling, requires_confirmation = _aggregate_segment_incentive_floor_ceiling({"segments": []})
        assert (floor, ceiling, requires_confirmation) == (None, None, False)
        floor, ceiling, requires_confirmation = _aggregate_segment_incentive_floor_ceiling({})
        assert (floor, ceiling, requires_confirmation) == (None, None, False)

    def test_segment_missing_floor_ceiling_keys_entirely_is_not_fabricated(self):
        # A segment dict that predates the floor/ceiling keys (old shape,
        # only e.g. selected_incentive_usd) must not silently contribute a
        # fabricated 0.0 — the whole aggregate stays None so the caller's
        # graceful-degradation fallback applies.
        trace = {"segments": [{"jurisdiction_code": "MU", "selected_incentive_usd": 573_059.70}]}
        floor, ceiling, requires_confirmation = _aggregate_segment_incentive_floor_ceiling(trace)
        assert (floor, ceiling, requires_confirmation) == (None, None, False)


class TestNPCFloorCeilingFormula:
    """The NPC_x = npc_with_adjustments_usd + selected_incentive_usd -
    incentive_x formula used in canonical_production_view.py's
    _empty_structure_entry — verified against Little Utopia's real,
    independently-reconstructed numbers (see
    test_lu_mauritius_economics_reconciliation.py for the QPE/incentive
    derivation these numbers come from)."""

    def test_lu_real_numbers_floor_selected_ceiling_potential(self):
        gross_budget_usd = 4_364_393.00
        floor_incentive = 1_306_598.10
        ceiling_incentive = 1_742_130.80
        selected_incentive = floor_incentive  # ceiling unconfirmed -> floor selected
        npc_with_adjustments = round(gross_budget_usd - selected_incentive, 2)  # no other adjustments for this baseline
        assert npc_with_adjustments == 3_057_794.90

        npc_floor = round(npc_with_adjustments + selected_incentive - floor_incentive, 2)
        npc_ceiling = round(npc_with_adjustments + selected_incentive - ceiling_incentive, 2)
        assert npc_floor == 3_057_794.90  # selected == floor here, so identical
        assert npc_ceiling == 2_622_262.20
        assert npc_ceiling < npc_floor, "a real, larger ceiling incentive must produce a real, lower potential NPC"
