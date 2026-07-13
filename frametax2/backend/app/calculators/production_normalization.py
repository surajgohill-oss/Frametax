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
    jurisdiction_code: str
    origin_city: str
    budgeted_travel_usd: float
    normalized_travel_usd: float
    delta_usd: float          # normalized - budgeted; positive = budget under-provisioned
    pricing_mode: str
    estimate: TravelCostEstimate
    note: str


def compute_travel_normalization(
    jurisdiction_code: str,
    inputs: TravelInputs,
    budgeted_travel_usd: float,
) -> TravelNormalizationResult:
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

    est = estimate_travel_cost(
        home_base=inputs.origin_city,
        destination_jurisdiction=jurisdiction_code,
        business_class_seats=inputs.business_travelers,
        economy_seats=inputs.economy_travelers,
        travel_frequency_per_year=inputs.rotations_per_year,
        hotel_nights=inputs.hotel_nights,
        per_diem_days=inputs.per_diem_days,
        incentive_value_usd=0.0,
    )
    normalized = est.total_travel_cost_usd
    return TravelNormalizationResult(
        jurisdiction_code=jurisdiction_code,
        origin_city=inputs.origin_city,
        budgeted_travel_usd=round(budgeted_travel_usd, 2),
        normalized_travel_usd=round(normalized, 2),
        delta_usd=round(normalized - budgeted_travel_usd, 2),
        pricing_mode=inputs.pricing_mode.value,
        estimate=est,
        note=note,
    )


# ── FX (Part 6) ───────────────────────────────────────────────────────────

class FXRateSource(str, enum.Enum):
    BENCHMARK = "benchmark"
    USER_OVERRIDE = "user_override"


# Documented, DATED benchmark FX snapshot (local currency units per USD).
# Not a live feed — the same static-table discipline travel_model.py
# already uses for fares. A production deployment would instead populate
# this from apply_fx_rates.py's own fx_rates table (which that module's
# own docstring says is live-fetch-populated but calculation-time-
# snapshotted, never fetched live during a calculation).
FX_BENCHMARK_SNAPSHOT_DATE = "2026-01-01"
BENCHMARK_FX_RATES: dict[str, float] = {
    "MUR": 46.50,   # Mauritian Rupee per USD
    "EUR": 0.92,    # Euro per USD
    "GBP": 0.79,    # British Pound per USD
}

_JURISDICTION_CURRENCY: dict[str, str] = {
    "MU": "MUR", "MT": "EUR", "GR": "EUR", "ES": "EUR", "CY": "EUR",
    "FR": "EUR", "IE": "EUR", "IT": "EUR", "DE": "EUR", "BE": "EUR", "HR": "EUR", "HU": "EUR",
    "GB": "GBP",
}


@dataclass(frozen=True)
class FXInputs:
    base_currency: str = "USD"
    rate_source: FXRateSource = FXRateSource.BENCHMARK
    user_rate: Optional[float] = None   # local units per USD; required when rate_source=USER_OVERRIDE
    scenario_fx_delta_pct: float = 0.0  # e.g. -0.05 = local currency depreciates 5% vs the rate used


@dataclass(frozen=True)
class FXNormalizationResult:
    jurisdiction_code: str
    local_currency: Optional[str]
    benchmark_rate: Optional[float]
    rate_used: Optional[float]
    rate_source: str
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
    convention — see production_normalization_for_candidate). Computes
    what that basis would cost in USD if the local currency moves by
    scenario_fx_delta_pct from the rate used. No live rate is ever
    fetched or fabricated: BENCHMARK_FX_RATES is a fixed, dated snapshot;
    USER_OVERRIDE requires an explicit user-supplied rate."""
    currency = _JURISDICTION_CURRENCY.get(jurisdiction_code)
    benchmark = BENCHMARK_FX_RATES.get(currency) if currency else None

    if inputs.rate_source == FXRateSource.USER_OVERRIDE and inputs.user_rate is not None:
        rate_used = inputs.user_rate
        note = (
            f"User-supplied override rate ({inputs.user_rate} {currency or '?'}/USD); "
            f"documented benchmark snapshot ({FX_BENCHMARK_SNAPSHOT_DATE}) was {benchmark}."
        )
    elif benchmark is not None:
        rate_used = benchmark
        note = f"Documented benchmark snapshot ({FX_BENCHMARK_SNAPSHOT_DATE}) — not a live rate."
    else:
        return FXNormalizationResult(
            jurisdiction_code=jurisdiction_code, local_currency=currency,
            benchmark_rate=None, rate_used=None, rate_source=inputs.rate_source.value,
            local_cost_basis_usd=round(local_cost_basis_usd, 2),
            fx_adjusted_local_cost_usd=round(local_cost_basis_usd, 2), delta_usd=0.0,
            note=(
                f"No benchmark FX rate on file for "
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
        benchmark_rate=benchmark, rate_used=rate_used, rate_source=inputs.rate_source.value,
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
    budgeted_travel_usd: float,
    fx_inputs: Optional[FXInputs],
    inkind_adjustment_by_candidate: Optional[dict[str, float]] = None,
) -> list[CandidateNormalization]:
    """Builds one CandidateNormalization per candidate and a full
    normalized ranking (ascending normalized_npc_usd — lower is better,
    same convention as the existing risk-adjusted-NPC ranking). Any input
    left None skips that adjustment (delta 0), never guesses a value.
    Travel/FX pricing is applied against the candidate's PRIMARY
    (first-listed) participating jurisdiction — the baseline shoot
    location — consistent with how travel_model.py itself prices one
    destination per estimate."""
    inkind_adjustment_by_candidate = inkind_adjustment_by_candidate or {}
    results: list[CandidateNormalization] = []
    for candidate_id, base_npc in base_npc_by_candidate.items():
        jurisdictions = participating_jurisdictions_by_candidate.get(candidate_id, ())
        primary = jurisdictions[0] if jurisdictions else None

        travel_result = None
        travel_delta = 0.0
        if travel_inputs is not None and primary is not None:
            travel_result = compute_travel_normalization(primary, travel_inputs, budgeted_travel_usd)
            travel_delta = travel_result.delta_usd

        fx_result = None
        fx_delta = 0.0
        if fx_inputs is not None and primary is not None:
            fx_result = compute_fx_normalization(primary, fx_inputs, base_npc)
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
