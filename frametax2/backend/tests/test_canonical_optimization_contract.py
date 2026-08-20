"""
test_canonical_optimization_contract.py

Phase 5 canonical optimization contract, REVISED under the Incentive/
Optimizer Core Closeout: the served optimizer ranks on the BEST-SUPPORTED
*confirmed* incentive. For a rate tier that is NOT a discretionary band
ceiling (flat rate, e.g. Greece), or one whose ceiling has been explicitly
confirmed for this scenario, that is still the modeled/ceiling figure —
never the conservative floor by default. But for a genuine discretionary
band ceiling with an unresolved condition (Mauritius's Film Rebate
Committee discretion, Malta's Commissioner-awarded uplift, the UK's VFX
Additional Credit) — the SAME kind of rate tier this contract always
called "best-supported modeled" — the served figure now correctly falls
back to the guaranteed floor by default, because "best-supported" a
discretionary ceiling is not automatically "confirmed". A project/
scenario-specific confirmed_ceiling_programs override still selects the
ceiling for a specific production with real evidence (a certificate, an
approval letter). The off-budget Mauritius in-kind post replacement-cost
normalization, and floor-rate uncertainty as a separate field, are
unchanged.
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
    def test_mu_ceiling_requires_confirmation_and_serves_floor_by_default(self):
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        # MU's 40% tier is a discretionary band ceiling (Film Rebate
        # Committee discretion) — unconfirmed by default, so the served/
        # ranked incentive is the 30% guaranteed floor, matching
        # total_incentive_floor_usd exactly, strictly less than the
        # (unconfirmed) ceiling.
        assert mu["selected_incentive_usd"] == pytest.approx(mu["total_incentive_floor_usd"], abs=0.5)
        assert mu["selected_incentive_usd"] < mu["total_incentive_ceiling_usd"]

    def test_npc_is_computed_on_the_confirmed_floor_incentive(self):
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        # With the ceiling unconfirmed by default, the canonical
        # (npc_with_adjustments) and conservative (floor-rate) NPCs both
        # use the same 30% floor incentive for Mauritius specifically —
        # they are equal here, not "canonical < conservative" (that
        # relationship only holds when a ceiling IS being served above
        # the floor, which the discretionary MU tier no longer is by
        # default).
        assert mu["npc_with_adjustments_usd"] == pytest.approx(mu["npc_conservative_usd"], abs=0.5)

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
        # CBA-009 Part 19-20: $4,355,327 -> $4,054,196 ($301,131.00 lower —
        # the contingency reserve is now a disclosed grey area by default,
        # not silently 100%-qualifying).
        assert seg["qpe_usd"] == pytest.approx(4_054_196, abs=1)

    def test_replacement_enters_npc_additively(self):
        gr = _by_id()[0]["ALLOC-RELOC-GR"]
        assert gr["npc_with_adjustments_usd"] == pytest.approx(
            gr["npc_verified_usd"] + (gr["travel_incremental_delta_usd"] or 0.0)
            + (gr["fx_delta_usd"] or 0.0) + gr["inkind_replacement_delta_usd"]
            + (gr["local_cost_delta_usd"] or 0.0), abs=0.5,
        )


class TestUncertaintySeparate:
    def test_conservative_floor_npc_surfaced_separately(self):
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        # both figures present; the floor one is strictly the higher-cost
        # (more conservative) downside of the approval-uncertainty band.
        assert mu["npc_conservative_usd"] is not None
        assert mu["npc_with_adjustments_usd"] is not None
        assert mu["npc_conservative_usd"] >= mu["npc_with_adjustments_usd"]


class TestLocalCostModeling:
    """Priority-1 reconnection: production_adjustment.py + location_cost_
    benchmarks.py (real per-jurisdiction cost indices) are threaded into
    every structure's NPC as local_cost_delta_usd — the incremental,
    non-travel/non-FX cost of shooting/routing work in the structure's
    jurisdiction instead of the production's real geography (MU)."""

    def test_baseline_has_zero_local_cost_delta(self):
        # same jurisdiction as itself -> production_adjustment.py's own
        # EXISTING_BUDGET regression constraint: all deltas are 0.0.
        mu = _by_id()[0]["ALLOC-BASELINE-MU"]
        assert mu["local_cost_delta_usd"] == 0.0

    def test_relocated_structures_carry_a_real_nonzero_delta(self):
        by_id, _ = _by_id()
        for code in ("GR", "IE", "MT"):
            s = by_id[f"ALLOC-RELOC-{code}"]
            assert s["local_cost_delta_usd"] is not None
            assert s["local_cost_delta_usd"] != 0.0
            assert s["local_cost_basis"]["jurisdiction_code"] == code
            assert s["local_cost_basis"]["original_jurisdiction_code"] == "MU"

    def test_local_cost_delta_enters_npc(self):
        gr = _by_id()[0]["ALLOC-RELOC-GR"]
        assert gr["npc_with_adjustments_usd"] == pytest.approx(
            gr["npc_verified_usd"] + (gr["travel_incremental_delta_usd"] or 0.0)
            + (gr["fx_delta_usd"] or 0.0) + gr["inkind_replacement_delta_usd"]
            + gr["local_cost_delta_usd"], abs=0.5,
        )

    def test_unpriced_structures_still_carry_a_disclosed_delta(self):
        # Local cost modeling runs BEFORE the pricing gate: a structure that
        # cannot be priced (no statutory rate rules) is still never
        # fabricated, but its local-cost delta is real, sourced data and is
        # disclosed regardless. Asserted over whatever is genuinely unpriced
        # rather than over the capability-only set, which is normally empty
        # now that doctrine resolves under the canonical rule.
        by_id, al = _by_id()
        unpriced = [s for s in al["structures"] if not s["is_fully_priced"]]
        assert unpriced, "fixture must exercise at least one unpriced structure"
        for s in unpriced:
            assert s["local_cost_delta_usd"] is not None, (
                f"{s['structure_id']} is unpriced but discloses no local-cost delta"
            )


class TestSplitProductionElection:
    """Priority-2 reconnection: production_allocation.py's account_splits
    field (explicit producer per-account jurisdiction splits) was fully
    engine-supported and tested in isolation, but no producer-facing
    election ever composed a split_production StructureSpec for Little
    Utopia. The account_splits fact now does — reusing the existing,
    tested explicit-split pricing path verbatim, no new pricing logic."""

    def test_no_election_no_split_structure(self):
        al = build_allocated_structures(get_state())
        assert not [s for s in al["structures"] if s["structure_type"] == "split_production"]

    def test_election_composes_and_prices_a_real_split_structure(self):
        from app.demo.little_utopia_state import apply_fact_answers
        # Incentive/Optimizer Core Closeout: Greece's minimum eligible
        # spend is now the confirmed current EUR 200,000 fiction-film
        # floor ($228,104.80) — the GR split share is raised from 0.4 to
        # 0.5 so it still clears the (now higher) minimum-spend gate.
        apply_fact_answers({"account_splits": {"3400": {"MU": 0.5, "GR": 0.5}}})
        try:
            al = build_allocated_structures(get_state())
            splits = [s for s in al["structures"] if s["structure_type"] == "split_production"]
            assert len(splits) == 1
            s = splits[0]
            assert s["is_fully_priced"] is True
            by_jur = {seg["jurisdiction_code"]: seg for seg in s["segments"]}
            assert by_jur["MU"]["qpe_usd"] > 0
            assert by_jur["GR"]["qpe_usd"] > 0
            # the split account appears in both segments only via its
            # explicit portions — never duplicated, never guessed.
            assert "3400" in by_jur["MU"]["account_codes"]
            assert "3400" in by_jur["GR"]["account_codes"]
        finally:
            apply_fact_answers({"account_splits": None})

    def test_clearing_the_election_restores_the_canonical_baseline(self):
        from app.demo.little_utopia_state import apply_fact_answers
        baseline = build_allocated_structures(get_state())
        apply_fact_answers({"account_splits": {"3400": {"MU": 0.6, "GR": 0.4}}})
        apply_fact_answers({"account_splits": None})
        restored = build_allocated_structures(get_state())
        assert restored["discovery"]["generated_structures"] == baseline["discovery"]["generated_structures"]
        assert not [s for s in restored["structures"] if s["structure_type"] == "split_production"]

    def test_unmodeled_jurisdiction_in_split_is_rejected(self):
        from app.demo.little_utopia_state import apply_fact_answers
        with pytest.raises(ValueError):
            apply_fact_answers({"account_splits": {"3400": {"MU": 0.6, "ZZ": 0.4}}})
        apply_fact_answers({"account_splits": None})
