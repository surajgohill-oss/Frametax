"""
Overview FX Strip Freshness Architecture — regression coverage.

Root cause this closes: FX_RATE_SNAPSHOTS/FX_LIVE_SNAPSHOT_DATE were pure
static constants, seeded once (2026-07-13) and never refreshed by any
runtime path — "July FX survives into September" because no refresh
mechanism existed at all, not because an existing one broke. This file
protects the real fix: app/services/fx_refresh.py's page-open freshness
check, backed by the pre-existing (previously dormant) `fx_rates` table.

No mocking library (respx etc.) is installed or used elsewhere in this
repo (see test_talent_nationality_resolution.py) — network-dependent
behavior is tested by monkeypatching fx_refresh._fetch_provider_payload,
the one function that ever touches the network.
"""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators import production_normalization as fx_doctrine
from app.db.session import engine
from app.models.fx import FXRate
from app.services import fx_refresh


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture(autouse=True)
def _reset_fx_module_state():
    """Every test gets a clean slate of the module-level FX state and the
    in-process freshness cache/lock — this state is intentionally global
    (it backs every project's request, not a per-project object), so
    tests must not leak it into each other."""
    saved_snapshots = dict(fx_doctrine.FX_RATE_SNAPSHOTS)
    saved_horizon_dates = dict(fx_doctrine.FX_HORIZON_DATES)
    saved_live_date = fx_doctrine.FX_LIVE_SNAPSHOT_DATE
    saved_source = fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE
    saved_status = fx_doctrine.FX_FRESHNESS_STATUS
    saved_error = fx_doctrine.FX_LAST_REFRESH_ERROR
    fx_refresh._last_checked_at = None
    fx_refresh._refresh_lock = asyncio.Lock()
    yield
    fx_doctrine.FX_RATE_SNAPSHOTS.clear()
    fx_doctrine.FX_RATE_SNAPSHOTS.update(saved_snapshots)
    fx_doctrine.FX_HORIZON_DATES.clear()
    fx_doctrine.FX_HORIZON_DATES.update(saved_horizon_dates)
    fx_doctrine.FX_LIVE_SNAPSHOT_DATE = saved_live_date
    fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE = saved_source
    fx_doctrine.FX_FRESHNESS_STATUS = saved_status
    fx_doctrine.FX_LAST_REFRESH_ERROR = saved_error
    fx_refresh._last_checked_at = None


def _fake_provider_payload(rates: dict[str, float] | None = None):
    base = {c: 1.5 for c in fx_doctrine.ALL_TRACKED_CURRENCIES}
    base["USD"] = 1.0
    if rates:
        base.update(rates)
    return {"result": "success", "rates": base}


async def _clear_todays_fx_rows(db: AsyncSession):
    today = fx_refresh._today_str()
    rows = (await db.execute(select(FXRate).where(FXRate.effective_date == today))).scalars().all()
    for r in rows:
        await db.delete(r)
    await db.commit()


async def test_stale_absent_snapshot_triggers_a_refresh_on_open(db, monkeypatch):
    """A: stale/absent snapshot -> canonical refresh, no user action."""
    await _clear_todays_fx_rows(db)
    fx_doctrine.FX_LIVE_SNAPSHOT_DATE = "2026-07-13"  # simulate the real historical staleness
    calls = {"n": 0}

    async def fake_fetch():
        calls["n"] += 1
        return _fake_provider_payload({"SAR": 3.75})

    monkeypatch.setattr(fx_refresh, "_fetch_provider_payload", fake_fetch)
    status = await fx_refresh.ensure_fx_freshness(db)

    assert status.is_fresh is True
    assert status.refreshed_now is True
    assert calls["n"] == 1
    assert fx_doctrine.FX_LIVE_SNAPSHOT_DATE == fx_refresh._today_str()
    assert fx_doctrine.fx_rate_snapshot("SAR")["current"] == 3.75


async def test_fresh_snapshot_is_reused_without_a_second_provider_fetch(db, monkeypatch):
    """B: within-TTL freshness must not refetch the provider."""
    await _clear_todays_fx_rows(db)
    calls = {"n": 0}

    async def fake_fetch():
        calls["n"] += 1
        return _fake_provider_payload()

    monkeypatch.setattr(fx_refresh, "_fetch_provider_payload", fake_fetch)
    first = await fx_refresh.ensure_fx_freshness(db)
    second = await fx_refresh.ensure_fx_freshness(db)

    assert first.refreshed_now is True
    assert second.refreshed_now is False
    assert calls["n"] == 1, "a second ensure_fx_freshness call within the TTL must not hit the provider again"


async def test_missing_required_pair_in_persisted_snapshot_triggers_resolution(db, monkeypatch):
    """C: an incomplete persisted snapshot (missing a tracked currency)
    must not be silently adopted as fresh — it must trigger a real
    refresh to fill the gap."""
    await _clear_todays_fx_rows(db)
    today = fx_refresh._today_str()
    db.add(FXRate(base_currency="USD", quote_currency="EUR", rate=0.9, effective_date=today, source="open.er-api.com"))
    await db.commit()

    calls = {"n": 0}

    async def fake_fetch():
        calls["n"] += 1
        return _fake_provider_payload({"SAR": 3.75})

    monkeypatch.setattr(fx_refresh, "_fetch_provider_payload", fake_fetch)
    status = await fx_refresh.ensure_fx_freshness(db)

    assert calls["n"] == 1, "an incomplete same-day snapshot must not be treated as fresh"
    assert status.refreshed_now is True
    assert fx_doctrine.fx_rate_snapshot("SAR")["current"] == 3.75


async def test_provider_failure_preserves_last_valid_snapshot_and_discloses_stale(db, monkeypatch):
    """D: a failed refresh must never corrupt/delete the last valid
    snapshot, must not fabricate a rate, and must truthfully report
    stale_fallback rather than silently claiming fresh."""
    await _clear_todays_fx_rows(db)
    fx_doctrine.FX_RATE_SNAPSHOTS["2026-07-13"] = {"EUR": 0.87679}
    fx_doctrine.FX_LIVE_SNAPSHOT_DATE = "2026-07-13"

    async def failing_fetch():
        raise ConnectionError("simulated provider outage")

    monkeypatch.setattr(fx_refresh, "_fetch_provider_payload", failing_fetch)
    status = await fx_refresh.ensure_fx_freshness(db)

    assert status.is_fresh is False
    assert status.error is not None
    assert fx_doctrine.FX_LIVE_SNAPSHOT_DATE == "2026-07-13", "the last valid snapshot must not be discarded on failure"
    assert fx_doctrine.FX_RATE_SNAPSHOTS["2026-07-13"]["EUR"] == 0.87679, "the last valid rate must not be corrupted"
    assert fx_doctrine.FX_FRESHNESS_STATUS == "stale_fallback"
    assert fx_doctrine.FX_LAST_REFRESH_ERROR is not None


async def test_concurrent_stale_requests_single_flight_to_one_consistent_snapshot(db, monkeypatch):
    """E: N concurrent page-opens while stale must not each independently
    hit the provider or produce divergent snapshots."""
    await _clear_todays_fx_rows(db)
    calls = {"n": 0}

    async def fake_fetch():
        calls["n"] += 1
        await asyncio.sleep(0.05)  # widen the race window
        return _fake_provider_payload()

    monkeypatch.setattr(fx_refresh, "_fetch_provider_payload", fake_fetch)
    results = await asyncio.gather(*(fx_refresh.ensure_fx_freshness(db) for _ in range(5)))

    assert calls["n"] == 1, f"expected exactly one provider fetch across 5 concurrent opens, got {calls['n']}"
    as_of_values = {r.as_of for r in results}
    assert len(as_of_values) == 1, "every concurrent caller must observe the SAME resolved snapshot"


def test_fingerprint_includes_the_live_fx_snapshot_date():
    """F: DISPLAYED FX == MODEL-CONSUMED FX — a changed live snapshot date
    must change the evaluation fingerprint, so a stale persisted result
    can never keep serving paired with fresh FX metadata."""
    import inspect

    from app.services.canonical_evaluation import _compute_fingerprint
    source = inspect.getsource(_compute_fingerprint)
    assert "fx_live_snapshot_date" in source
    assert "production_normalization.FX_LIVE_SNAPSHOT_DATE" in source


def test_saudi_arabia_sar_is_a_tracked_currency_never_silently_excluded():
    """G: Saudi Arabia's Top Priced candidate must never be structurally
    unable to resolve a SAR rate — SAR must be in the fetched set."""
    assert "SAR" in fx_doctrine.ALL_TRACKED_CURRENCIES
    assert fx_doctrine._JURISDICTION_CURRENCY.get("SA") == "SAR"


def test_reverse_pair_is_never_a_second_stored_rate():
    """H: cross/inverse pairs are derived (1/rate), never a second
    provider observation or a second persisted row — confirmed at the
    persistence boundary: apply_live_fx_snapshot stores exactly the
    currency-per-USD values the provider returned, nothing pre-inverted."""
    fx_doctrine.apply_live_fx_snapshot("2099-01-01", {"EUR": 0.9}, "test")
    try:
        assert fx_doctrine.FX_RATE_SNAPSHOTS["2099-01-01"] == {"EUR": 0.9}
        assert "EUR_inverse" not in fx_doctrine.FX_RATE_SNAPSHOTS["2099-01-01"]
    finally:
        del fx_doctrine.FX_RATE_SNAPSHOTS["2099-01-01"]


async def test_get_project_state_calls_ensure_fx_freshness_before_serving_economics():
    """The actual page-open trigger (GET /projects/{id}/state) must call
    the canonical freshness check — never a component-level or
    frontend-only refresh."""
    import inspect

    from app.api.v1 import cineglobe as route_mod
    source = inspect.getsource(route_mod.get_project_state)
    assert "ensure_fx_freshness" in source
    assert "evaluate_project" in source, (
        "a genuinely new FX day must be able to reprice an existing persisted "
        "evaluation via the canonical idempotent-per-fingerprint path"
    )
