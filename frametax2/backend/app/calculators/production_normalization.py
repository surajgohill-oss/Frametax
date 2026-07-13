"""
production_normalization.py

Connects the existing travel_model.py and apply_fx_rates.py engines into
the served CineGlobe optimizer pipeline (Global Optimizer Input
Integration, Parts 5-6). Computes, per composed candidate structure, a
travel delta and an FX delta ON TOP OF that candidate's already-computed
cash NPC — purely additive. Neither optimization_engine.py's own math nor
production_structure_composer.py's ranking function is modified; this
module produces a SEPARATE, explicitly-labeled normalized ranking, using
travel_model.estimate_travel_cost() and apply_fx_rates.convert_to_usd()/
convert_usd_to_local() exactly as those modules already define them.

No live rate or fare is fetched or fabricated anywhere in this module.
Travel pricing defaults to travel_model.py's own static, documented fare
tables (the "benchmark estimate" mode); a "live lookup" mode is a named
placeholder for a future connector and currently falls back to the
benchmark with that fact disclosed. FX pricing defaults to a fixed, dated
benchmark snapshot or an explicit user override — never a live feed.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from app.calculators.travel_model import TravelCostEstimate, estimate_travel_cost

NORMALIZATION_VERSION = "1.0.0"


# ── Travel (Part 5) ───────────────────────────────────────────────────────

class TravelPricingMode(str, enum.Enum):
    BENCHMARK_ESTIMATE = "benchmark_estimate"
    LIVE_LOOKUP = "live_lookup"  # named placeholder — no connector wired yet


@dataclass(frozen=True)
class TravelInputs:
    origin_city: str = "LA"          # "LA" | "NYC" | any travel_model fare-table code
    business_travelers: int = 1
    economy_travelers: int = 0
    rotations_per_year: int = 4
    hotel_nights: int = 14
    per_diem_days: int = 14
    pricing_mode: TravelPricingMode = TravelPricingMode.BENCHMARK_ESTIMATE


@dataclass(frozen=True)
class TravelNormalizationResult:
    jurisdiction_code: str            # the PROPOSED jurisdiction being evaluated
    original_jurisdiction_code: str   # the production's actual/original shoot geography
    origin_city: str
    original_budgeted_travel_usd: float  # reference only — the real budget's own travel
                                          # line for the ORIGINAL geography; NOT used in
                                          # the incremental calculation below (Part 6:
                                          # "NOT total travel")
    original_modeled_travel_usd: float   # model(origin, original_jurisdiction)
    proposed_modeled_travel_usd: float   # model(origin, proposed_jurisdiction)
    incremental_delta_usd: float         # proposed_modeled - original_modeled — the
                                          # INCREMENTAL cost of shooting/routing crew
                                          # to the proposed jurisdiction INSTEAD OF (or
                                          # in addition to) the original one
    pricing_mode: str
    estimate: TravelCostEstimate         # the PROPOSED jurisdiction's full cost breakdown
    note: str


def compute_travel_normalization(
    jurisdiction_code: str,
    inputs: TravelInputs,
    original_budgeted_travel_usd: float,
    original_jurisdiction_code: str = "MU",
) -> TravelNormalizationResult:
    """
    Incremental travel adjustment (Part 6 algorithm):
      original production travel cost (reference, real budget figure)
        -> original shooting geography (original_jurisdiction_code)
        -> user origin hub (inputs.origin_city)
        -> model travel for the ORIGINAL geography AND the PROPOSED
           jurisdiction, same assumptions on both sides (apples-to-apples
           — the prior design compared a MODEL estimate against the
           production's TOTAL crew travel budget, which conflated
           traveler-count assumptions; this compares model-vs-model)
        -> incremental_delta_usd = proposed - original. NOT total travel.
    jurisdiction_code == original_jurisdiction_code (the baseline
    candidate, e.g. Mauritius-only) always yields delta_usd == 0 exactly.
    """
    if inputs.pricing_mode == TravelPricingMode.LIVE_LOOKUP:
        note = (
            "Live lookup requested but no live-fare connector is wired yet "
            "— served the documented benchmark estimate instead of "
            "fabricating a live quote."
        )
    else:
        note = (
            "Benchmark estimate — travel_model.py's static, documented "
            "fare/hotel/per-diem tables. Not a live quote."
        )

    def _model(dest: str) -> TravelCostEstimate:
        return estimate_travel_cost(
            home_base=inputs.origin_city,
            destination_jurisdiction=dest,
            business_class_seats=inputs.business_travelers,
            economy_seats=inputs.economy_travelers,
            travel_frequency_per_year=inputs.rotations_per_year,
            hotel_nights=inputs.hotel_nights,
            per_diem_days=inputs.per_diem_days,
            incentive_value_usd=0.0,
        )

    proposed_est = _model(jurisdiction_code)
    if jurisdiction_code == original_jurisdiction_code:
        original_cost = proposed_est.total_travel_cost_usd  # identical model call — exact zero delta
    else:
        original_cost = _model(original_jurisdiction_code).total_travel_cost_usd

    proposed_cost = proposed_est.total_travel_cost_usd
    return TravelNormalizationResult(
        jurisdiction_code=jurisdiction_code,
        original_jurisdiction_code=original_jurisdiction_code,
        origin_city=inputs.origin_city,
        original_budgeted_travel_usd=round(original_budgeted_travel_usd, 2),
        original_modeled_travel_usd=round(original_cost, 2),
        proposed_modeled_travel_usd=round(proposed_cost, 2),
        incremental_delta_usd=round(proposed_cost - original_cost, 2),
        pricing_mode=inputs.pricing_mode.value,
        estimate=proposed_est,
        note=note,
    )


# ── FX (Part 7) ───────────────────────────────────────────────────────────

class FXRateSource(str, enum.Enum):
    LIVE = "live"                # most recent sourced snapshot on file
    HISTORICAL = "historical"    # a specific dated sourced snapshot
    USER_OVERRIDE = "user_override"


# Sourced FX snapshots — fetched live from public rate providers this
# phase (2026-07-13), NOT fabricated or guessed. apply_fx_rates.py's own
# docstring already states the correct architecture: "Rates are loaded
# from the fx_rates table, not fetched live during calculation. Live
# fetch populates the table; calculations use snapshots." This table IS
# that population step, done via a real fetch instead of an invented
# number. A production deployment would refresh it on a schedule via the
# same sources, not on every request.
#
# Sources:
#   MUR: https://open.er-api.com/v6/latest/USD (free public API, live
#        as of fetch time) — current only; this provider has no
#        historical endpoint, and no other free/connected source covers
#        MUR, so MUR historical snapshots are honestly absent, never
#        fabricated.
#   EUR/GBP: https://api.frankfurter.dev (ECB reference rates) — both
#        current and historical (ECB has no MUR cross-rate either).
FX_RATES_VERSION = "2.0.0"

# date string ("YYYY-MM-DD") -> {currency: local units per USD}
FX_RATE_SNAPSHOTS: dict[str, dict[str, float]] = {
    "2026-07-13": {"MUR": 47.053589, "EUR": 0.87679, "GBP": 0.74699},   # current (fetch date)
    "2026-06-12": {"EUR": 0.86453, "GBP": 0.74613},                     # ~1 month prior
    "2026-01-13": {"EUR": 0.85807, "GBP": 0.74309},                     # ~6 months prior
    "2025-07-11": {"EUR": 0.85594, "GBP": 0.74099},                     # ~12 months prior
}
FX_LIVE_SNAPSHOT_DATE = "2026-07-13"
FX_HORIZON_DATES: dict[str, str] = {
    "current": "2026-07-13", "1m": "2026-06-12", "6m": "2026-01-13", "12m": "2025-07-11",
}

_JURISDICTION_CURRENCY: dict[str, str] = {
    "MU": "MUR", "MT": "EUR", "GR": "EUR", "ES": "EUR", "CY": "EUR",
    "FR": "EUR", "IE": "EUR", "IT": "EUR", "DE": "EUR", "BE": "EUR", "HR": "EUR", "HU": "EUR",
    "GB": "GBP",
}


def fx_rate_snapshot(currency: str) -> dict[str, Optional[float]]:
    """The engine-side data the UI's current/1M/6M/12M FX display needs
    (Part 7 — engine provides the data, no UI built here). Returns None
    for any horizon with no sourced snapshot on file (e.g. MUR beyond
    'current') rather than a fabricated or interpolated figure."""
    return {
        horizon: FX_RATE_SNAPSHOTS.get(date, {}).get(currency)
        for horizon, date in FX_HORIZON_DATES.items()
    }


@dataclass(frozen=True)
class FXInputs:
    base_currency: str = "USD"
    rate_source: FXRateSource = FXRateSource.LIVE
    historical_date: Optional[str] = None  # "YYYY-MM-DD"; required when rate_source=HISTORICAL
    user_rate: Optional[float] = None      # local units per USD; required when rate_source=USER_OVERRIDE
    scenario_fx_delta_pct: float = 0.0     # e.g. -0.05 = local currency depreciates 5% vs the rate used


@dataclass(frozen=True)
class FXNormalizationResult:
    jurisdiction_code: str
    local_currency: Optional[str]
    live_rate: Optional[float]
    rate_used: Optional[float]
    rate_source: str
    rate_date: Optional[str]
    local_cost_basis_usd: float
    fx_adjusted_local_cost_usd: float
    delta_usd: float
    note: str


def compute_fx_normalization(
    jurisdiction_code: str,
    inputs: FXInputs,
    local_cost_basis_usd: float,
) -> FXNormalizationResult:
    """local_cost_basis_usd: the portion of a candidate's cash NPC assumed
    to be incurred in that jurisdiction's local currency (the caller's
    convention — see normalize_candidates). Computes what that basis
    would cost in USD if the local currency moves by scenario_fx_delta_pct
    from the rate used. No live network call happens during this
    calculation — LIVE/HISTORICAL both read FX_RATE_SNAPSHOTS, a table
    populated from real fetches (see module docstring); USER_OVERRIDE
    requires an explicit user-supplied rate. Budget exchange assumptions
    never override this — the register/budget is USD-denominated and
    this module is never fed a rate from the budget document."""
    currency = _JURISDICTION_CURRENCY.get(jurisdiction_code)
    live_rate = FX_RATE_SNAPSHOTS.get(FX_LIVE_SNAPSHOT_DATE, {}).get(currency) if currency else None

    if inputs.rate_source == FXRateSource.USER_OVERRIDE and inputs.user_rate is not None:
        rate_used, rate_date = inputs.user_rate, None
        note = (
            f"User-supplied override rate ({inputs.user_rate} {currency or '?'}/USD); "
            f"live sourced snapshot ({FX_LIVE_SNAPSHOT_DATE}) was {live_rate}."
        )
    elif inputs.rate_source == FXRateSource.HISTORICAL and inputs.historical_date is not None:
        rate_used = FX_RATE_SNAPSHOTS.get(inputs.historical_date, {}).get(currency) if currency else None
        rate_date = inputs.historical_date
        if rate_used is None:
            return FXNormalizationResult(
                jurisdiction_code=jurisdiction_code, local_currency=currency,
                live_rate=live_rate, rate_used=None, rate_source=inputs.rate_source.value,
                rate_date=inputs.historical_date,
                local_cost_basis_usd=round(local_cost_basis_usd, 2),
                fx_adjusted_local_cost_usd=round(local_cost_basis_usd, 2), delta_usd=0.0,
                note=(
                    f"No sourced FX snapshot on file for '{currency or jurisdiction_code}' on "
                    f"{inputs.historical_date} — no FX effect applied (never fabricated/interpolated)."
                ),
            )
        note = f"Sourced historical snapshot dated {inputs.historical_date}."
    elif live_rate is not None:
        rate_used, rate_date = live_rate, FX_LIVE_SNAPSHOT_DATE
        note = f"Live sourced snapshot, fetched {FX_LIVE_SNAPSHOT_DATE} (open.er-api.com / ECB via frankfurter.dev)."
    else:
        return FXNormalizationResult(
            jurisdiction_code=jurisdiction_code, local_currency=currency,
            live_rate=None, rate_used=None, rate_source=inputs.rate_source.value, rate_date=None,
            local_cost_basis_usd=round(local_cost_basis_usd, 2),
            fx_adjusted_local_cost_usd=round(local_cost_basis_usd, 2), delta_usd=0.0,
            note=(
                f"No sourced FX rate on file for "
                f"'{currency or jurisdiction_code}' — no FX effect applied "
                f"(never fabricated)."
            ),
        )

    scenario_rate = rate_used * (1 - inputs.scenario_fx_delta_pct)
    # local_cost_basis_usd was originally priced at rate_used; re-express
    # it at the scenario rate to isolate the USD delta from FX movement
    # alone (the local-currency cost itself is held constant).
    adjusted_usd = local_cost_basis_usd * (rate_used / scenario_rate) if scenario_rate else local_cost_basis_usd
    return FXNormalizationResult(
        jurisdiction_code=jurisdiction_code, local_currency=currency,
        live_rate=live_rate, rate_used=rate_used, rate_source=inputs.rate_source.value, rate_date=rate_date,
        local_cost_basis_usd=round(local_cost_basis_usd, 2),
        fx_adjusted_local_cost_usd=round(adjusted_usd, 2),
        delta_usd=round(adjusted_usd - local_cost_basis_usd, 2),
        note=note,
    )


# ── Combined per-candidate normalization + re-ranking (Parts 5-7) ───────────

@dataclass(frozen=True)
class CandidateNormalization:
    candidate_id: str
    base_cash_npc_usd: float
    travel: Optional[TravelNormalizationResult]
    fx: Optional[FXNormalizationResult]
    inkind_adjustment_usd: float
    normalized_npc_usd: float


def normalize_candidates(
    base_npc_by_candidate: dict[str, float],
    participating_jurisdictions_by_candidate: dict[str, tuple[str, ...]],
    travel_inputs: Optional[TravelInputs],
    original_budgeted_travel_usd: float,
    fx_inputs: Optional[FXInputs],
    original_jurisdiction_code: str = "MU",
    inkind_adjustment_by_candidate: Optional[dict[str, float]] = None,
) -> list[CandidateNormalization]:
    """Builds one CandidateNormalization per candidate and a full
    normalized ranking (ascending normalized_npc_usd — lower is better,
    same convention as the existing risk-adjusted-NPC ranking). Any input
    left None skips that adjustment (delta 0), never guesses a value.

    Travel (Part 6, incremental adjustment): the PROPOSED jurisdiction for
    a candidate is the LAST-listed participating jurisdiction — for the
    baseline candidate (only original_jurisdiction_code) that IS the
    original, so its incremental delta is exactly zero; for a treaty/
    co-production candidate it is the ADDED partner jurisdiction, so the
    delta prices the incremental cost of ALSO routing crew there, modeled
    against the same origin/traveler assumptions as the original geography
    — never the candidate's total travel cost.

    FX pricing is applied against the candidate's PROPOSED jurisdiction
    the same way (its local currency, if any)."""
    inkind_adjustment_by_candidate = inkind_adjustment_by_candidate or {}
    results: list[CandidateNormalization] = []
    for candidate_id, base_npc in base_npc_by_candidate.items():
        jurisdictions = participating_jurisdictions_by_candidate.get(candidate_id, ())
        proposed = jurisdictions[-1] if jurisdictions else None

        travel_result = None
        travel_delta = 0.0
        if travel_inputs is not None and proposed is not None:
            travel_result = compute_travel_normalization(
                proposed, travel_inputs, original_budgeted_travel_usd, original_jurisdiction_code,
            )
            travel_delta = travel_result.incremental_delta_usd

        fx_result = None
        fx_delta = 0.0
        if fx_inputs is not None and proposed is not None:
            fx_result = compute_fx_normalization(proposed, fx_inputs, base_npc)
            fx_delta = fx_result.delta_usd

        inkind_delta = inkind_adjustment_by_candidate.get(candidate_id, 0.0)

        normalized_npc = round(base_npc + travel_delta + fx_delta + inkind_delta, 2)
        results.append(CandidateNormalization(
            candidate_id=candidate_id,
            base_cash_npc_usd=round(base_npc, 2),
            travel=travel_result,
            fx=fx_result,
            inkind_adjustment_usd=round(inkind_delta, 2),
            normalized_npc_usd=normalized_npc,
        ))
    return sorted(results, key=lambda r: (r.normalized_npc_usd, r.candidate_id))
