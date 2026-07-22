"""
test_canonical_optimization_contract.py

Phase 5 canonical optimization contract: the served optimizer ranks on the
BEST-SUPPORTED modeled incentive (never the conservative floor), normalizes
the off-budget Mauritius in-kind post by replacement cost, and keeps
uncertainty (the floor-rate figure) as a separate field — never the ranked
number.
"""
from __future__ import annotations

import pytest

from app.demo.little_utopia_state import build_allocated_structures, get_state, reset_fact_answers


@pytest.fixture(autouse=True)
def _reset():
    reset_fact_answers()
    yield
    reset_fact_answers()


def _by_id():
    al = build_allocated_structures(get_state())
    return {s["structure_id"]: s for s in al["structures"]}, al


class TestModeledNotFloor:
    def test_mu_uses_best_supported_modeled_incentive_not_floor(self):
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        # MU resolves a 30% floor / 40% modeled band. The served/ranked
        # incentive must be the 40% best-supported figure (== ceiling),
        # strictly greater than the 30% floor.
        assert mu["selected_incentive_usd"] == pytest.approx(mu["total_incentive_ceiling_usd"], abs=0.5)
        assert mu["selected_incentive_usd"] > mu["total_incentive_floor_usd"]

    def test_npc_is_computed_on_modeled_incentive(self):
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        # canonical NPC uses selected (modeled) incentive; conservative NPC
        # uses the floor — and the two differ for a banded jurisdiction.
        assert mu["npc_with_adjustments_usd"] < mu["npc_conservative_usd"]

    def test_ranking_does_not_use_floor(self):
        by, al = _by_id()
        ranked = [r for r in al["ranking"] if r["rank"] is not None]
        # If ranking used the floor, GR (flat 40% floor) would beat MU (30%
        # floor). Under the modeled contract + in-kind normalization, MU
        # baseline is the optimum.
        assert ranked[0]["structure_id"] == "ALLOC-BASELINE-MU"


class TestInKindNormalization:
    def test_mu_baseline_keeps_inkind_zero_delta(self):
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        assert mu["inkind_replacement_delta_usd"] == 0.0

    def test_relocations_absorb_replacement_cost(self):
        by, _ = _by_id()
        for sid in ("ALLOC-RELOC-GR", "ALLOC-RELOC-IE", "ALLOC-RELOC-MT"):
            assert by[sid]["inkind_replacement_delta_usd"] > 0.0

    def test_component_post_routed_out_of_mu_absorbs_replacement(self):
        # MU shoot + post routed to MT → post leaves MU → replacement applies.
        assert _by_id()[0]["ALLOC-COMPONENT-POST-MT"]["inkind_replacement_delta_usd"] > 0.0

    def test_inkind_never_in_qpe_or_budget(self):
        # QPE + gross budget must be unchanged by the normalization: the
        # in-kind is production economics only, never a budget line / QPE.
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        assert mu["gross_budget_usd"] == pytest.approx(4_364_393, abs=5)
        seg = next(s for s in mu["segments"] if s["jurisdiction_code"] == "MU")
        assert seg["qpe_usd"] == pytest.approx(4_355_327, abs=1)

    def test_replacement_enters_npc_additively(self):
        gr = _by_id()[0]["ALLOC-RELOC-GR"]
        assert gr["npc_with_adjustments_usd"] == pytest.approx(
            gr["npc_verified_usd"] + (gr["travel_incremental_delta_usd"] or 0.0)
            + (gr["fx_delta_usd"] or 0.0) + gr["inkind_replacement_delta_usd"], abs=0.5,
        )


class TestUncertaintySeparate:
    def test_conservative_floor_npc_surfaced_separately(self):
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        # both figures present; the floor one is strictly the higher-cost
        # (more conservative) downside of the approval-uncertainty band.
        assert mu["npc_conservative_usd"] is not None
        assert mu["npc_with_adjustments_usd"] is not None
        assert mu["npc_conservative_usd"] >= mu["npc_with_adjustments_usd"]
