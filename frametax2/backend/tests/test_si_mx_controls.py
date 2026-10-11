"""Behavioral controls for the two programs removed from the discretionary ruling whose pricing was queried:
si_cash_rebate (a lone "up to 25%" ceiling) and mx_federal_film_incentive_2026 (30% credit with a native-MXN minimum spend).
Synthetic, rolled-back records only; the FX snapshot below is an explicit TEST scenario, not a sourced rate."""
from __future__ import annotations

import pytest

from app.calculators.apply_fx_rates import CanonicalFXContext
from app.data.program_rate_rules import resolve_program_rate
from app.services.canonical_evaluation import evaluate_project
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

MX = "mx_federal_film_incentive_2026"
TEST_MXN_PER_USD = 20.0   # scenario value for the mechanics only


def _fx():
    return CanonicalFXContext(snapshot_date="2026-10-11", rates={"MXN": TEST_MXN_PER_USD}, source="test scenario", freshness_status="fresh")


def test_mexico_percentage_is_set_by_the_committee_so_30_percent_is_a_ceiling_and_the_minimum_stays_native():
    r = resolve_program_rate(MX, production_type="feature_film", qpe_usd=2_500_000.0, fx_context=_fx())
    assert r is not None and r.modeled_rate == pytest.approx(0.30) and r.is_band_ceiling and r.has_guaranteed_floor is False
    assert any(c.condition_id == "mx-committee-sets-the-percentage" and c.satisfied is None for c in r.conditions_evaluated)
    # MXN 40,000,000 minimum = USD 2,000,000 at the scenario rate: below it nothing resolves at all
    assert resolve_program_rate(MX, production_type="feature_film", qpe_usd=1_500_000.0, fx_context=_fx()) is None
    no_rate = CanonicalFXContext(snapshot_date="2026-10-11", rates={"EUR": 0.9}, source="test scenario", freshness_status="fresh")
    assert resolve_program_rate(MX, production_type="feature_film", qpe_usd=50_000_000.0, fx_context=no_rate) is None


def test_the_engine_fx_table_now_carries_a_sourced_mxn_rate_on_every_snapshot_date():
    from app.calculators import production_normalization as pn
    for date in ("2026-07-13", "2026-06-12", "2026-01-13", "2025-07-11"):
        assert pn.FX_RATE_SNAPSHOTS[date]["MXN"] > 10
    ctx = pn.build_fx_context()
    r = resolve_program_rate(MX, production_type="feature_film", qpe_usd=3_000_000.0, fx_context=ctx)     # 3m USD x 17.4908 = MXN 52.5m >= 40m
    assert r is not None and r.is_band_ceiling


async def test_slovenia_ceiling_only_program_is_visible_with_zero_guaranteed_value_and_a_stated_reason():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU")
        await evaluate_project(db, pid)
        si = [e for e in await served_structures(db, pid) if e["program_slugs"] == ["si_cash_rebate"]]
    assert si, "the Slovenia candidate must stay visible"
    for e in si:
        assert e["is_fully_priced"] is False and not e["selected_incentive_usd"] and not e["confirmed_incentive_floor_usd"]
        assert e["rejection_reason_class"] == "PRICING_BLOCKED" and "rate CEILING (25%) with no guaranteed floor" in e["blockers"][0]


def test_a_lone_ceiling_is_never_described_as_the_guaranteed_floor():
    r = resolve_program_rate("si_cash_rebate", production_type="feature_film", qpe_usd=5_000_000.0)
    assert r is not None and r.is_band_ceiling and r.has_guaranteed_floor is False
    assert "NO guaranteed floor tier is eligible" in r.basis and "guaranteed floor tier is 25%" not in r.basis
