"""The evaluator persists exactly what the served maximum-potential contract needs
(real Little Utopia fixtures + the real pricing kernel; no DB, no evaluation)."""
from __future__ import annotations

from app.services.canonical_evaluation import _segment_dicts
from app.services.incentive_potential import (
    CEILING_CONDITIONAL,
    CEILING_CONFIRMED,
    build_incentive_potential,
)
from tests.test_incentive_optimizer_core_closeout import _price, _spec


def _mu(**kw):
    return _price(_spec("P-MU", "single_country", ("MU",), {"MU": "mu_edb_incentive"}), **kw)


def test_unconfirmed_ceiling_persists_its_unmet_conditions_verbatim():
    pricing = _mu()
    seg = _segment_dicts(pricing)[0]
    assert seg["ceiling_requires_confirmation"] is True
    conds = seg["ceiling_conditions"]
    assert conds, "an unconfirmed ceiling must retain the conditions that keep it unconfirmed"
    assert all(c["satisfied"] is not True for c in conds)
    assert {"condition_id", "description", "kind", "condition_state", "note"} <= set(conds[0])


def test_served_contract_reconstructs_the_priced_incentive_and_a_real_ceiling():
    pricing = _mu()
    trace = {"segments": _segment_dicts(pricing)}
    c = build_incentive_potential(
        trace, is_priced=True, selected_incentive_usd=pricing.selected_incentive_usd,
        npc_with_adjustments_usd=pricing.npc_verified_usd,
    )
    mu = pricing.segments[0]
    assert c["confirmed_incentive_floor_usd"] == round(pricing.selected_incentive_usd, 2)
    assert c["confirmed_incentive_floor_usd"] == round(mu.incentive_floor_usd, 2)
    assert c["maximum_supported_incentive_usd"] == round(mu.incentive_ceiling_usd, 2)
    assert c["ceiling_status"] == CEILING_CONDITIONAL
    assert c["ceiling_missing_facts"], "conditional maximum must name what is missing"
    assert c["potential_npc_usd"] < c["confirmed_npc_usd"]


def test_project_confirmation_collapses_the_maximum_into_the_confirmed_incentive():
    pricing = _mu(confirmed_ceiling_programs=frozenset({"mu_edb_incentive"}))
    seg = _segment_dicts(pricing)[0]
    assert seg["ceiling_requires_confirmation"] is False and seg["ceiling_conditions"] == []
    c = build_incentive_potential(
        {"segments": _segment_dicts(pricing)}, is_priced=True,
        selected_incentive_usd=pricing.selected_incentive_usd, npc_with_adjustments_usd=pricing.npc_verified_usd,
    )
    assert c["ceiling_status"] == CEILING_CONFIRMED
    assert c["confirmed_incentive_floor_usd"] == c["maximum_supported_incentive_usd"] == round(
        pricing.segments[0].incentive_ceiling_usd, 2)
