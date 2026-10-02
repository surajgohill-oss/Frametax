"""Recurrence guard: a live FX refresh only fetches ALL_TRACKED_CURRENCIES (derived from
_JURISDICTION_CURRENCY). Native-currency incentive caps (cz_film_incentive CZK450m,
za_nfvf_rebate ZAR25m) need their currency tracked, or a successful refresh yields a snapshot
without it and every such candidate silently fails closed to PRICING_BLOCKED."""
from __future__ import annotations

from app.calculators import production_normalization as pn


def test_czk_and_zar_are_tracked_so_a_live_refresh_always_fetches_them():
    assert pn._JURISDICTION_CURRENCY["CZ"] == "CZK"
    assert pn._JURISDICTION_CURRENCY["ZA"] == "ZAR"
    assert {"CZK", "ZAR"} <= pn.ALL_TRACKED_CURRENCIES


def test_czech_cap_converts_under_a_snapshot_built_from_the_tracked_set():
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.calculators.apply_fx_rates import CanonicalFXContext

    rates = {c: 1.5 for c in pn.ALL_TRACKED_CURRENCIES}
    rates["CZK"] = 21.0
    ctx = CanonicalFXContext(snapshot_date="2026-10-02", rates=rates, source="test", freshness_status="fresh")
    cap_usd, _t, _b, fx_error, unresolved = _resolve_incentive_dollar_cap("cz_film_incentive", ctx, {}, frozenset())
    assert fx_error is None and unresolved is None
    assert cap_usd is not None and abs(cap_usd - 450_000_000 / 21.0) < 1.0
