"""Claim-base certainty in the served incentive-potential contract (Codex CR-01).

SYNTHETIC ONLY -- invented amounts, no database. A segment whose priced base presumes unevidenced facts (Greek local incurrence,
application date/regime, capped-group membership) keeps its planning numbers but is never served as CONFIRMED economics; the
statutory-rate channel (ceiling_status) stays separate from the claim-base channel (claim_base_*)."""
from __future__ import annotations

import pytest

from app.services.incentive_potential import (
    CERTAINTY_CONDITIONAL, CERTAINTY_CONFIRMED, CEILING_CONFIRMED, build_incentive_potential)

PRESUMED = [
    {"condition_id": "gr-local-incurrence-schedule", "description": "Local incurrence schedule", "state": "USER_FACT_REQUIRED", "note": None},
    {"condition_id": "gr-principal-fee-membership", "description": "Capped-group membership", "state": "CLAIM_BASE_UNRESOLVED",
     "note": None, "exact": False, "unresolved_members": [{"category": "atl_cast", "amount_usd": 900000.0}]},
]


def _segment(presumed):
    return {"jurisdiction_code": "GR", "program_slug": "gr_cash_rebate", "incentive_floor_usd": 400_000.0,
            "incentive_ceiling_usd": 400_000.0, "ceiling_requires_confirmation": False, "rate_floor": 0.4, "rate_ceiling": 0.4,
            "presumed_facts": presumed}


def _served(trace):
    return build_incentive_potential(trace, is_priced=True, selected_incentive_usd=400_000.0, npc_with_adjustments_usd=600_000.0)


def test_missing_base_facts_hold_certainty_at_conditional_without_changing_a_number_or_the_rate_status():
    out = _served({"segments": [_segment(PRESUMED)]})
    assert out["economics_certainty"] == CERTAINTY_CONDITIONAL and out["claim_base_certainty"] == CERTAINTY_CONDITIONAL
    assert out["ceiling_status"] == CEILING_CONFIRMED and out["ceiling_missing_facts"] == []        # the statutory rate is certain
    assert out["confirmed_incentive_floor_usd"] == out["maximum_supported_incentive_usd"] == 400_000.0   # planning numbers intact
    assert out["confirmed_npc_usd"] == out["potential_npc_usd"] == 600_000.0 and out["potential_upside_usd"] == 0.0
    ids = {f["fact_id"] for f in out["claim_base_missing_facts"]}
    assert ids == {"gr-local-incurrence-schedule", "gr-principal-fee-membership"}
    member = next(f for f in out["claim_base_missing_facts"] if f["fact_id"] == "gr-principal-fee-membership")
    assert member["exact"] is False and member["affects_usd"] == 400_000.0 and member["unresolved_members"]


def test_a_segment_with_no_presumed_base_fact_is_still_confirmed():
    out = _served({"segments": [_segment([])]})
    assert out["economics_certainty"] == CERTAINTY_CONFIRMED and out["claim_base_certainty"] == CERTAINTY_CONFIRMED
    assert out["claim_base_missing_facts"] == []


def test_the_hybrid_component_path_carries_the_same_claim_base_disclosure():
    comp = {"jurisdiction_code": "GR", "program_slug": "gr_cash_rebate", "component": "production",
            "guaranteed_incentive_usd": 400_000.0, "incentive_ceiling_usd": 400_000.0, "presumed_facts": PRESUMED}
    out = _served({"component_allocations": [comp]})
    assert out["economics_certainty"] == CERTAINTY_CONDITIONAL and len(out["claim_base_missing_facts"]) == 2
    assert out["ceiling_status"] == CEILING_CONFIRMED and out["maximum_supported_incentive_usd"] == 400_000.0
    clean = _served({"component_allocations": [{**comp, "presumed_facts": []}]})
    assert clean["economics_certainty"] == CERTAINTY_CONFIRMED
