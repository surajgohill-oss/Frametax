"""
generate_structure_scenarios.py

Generates and ranks all feasible production structure scenarios from a
candidate set of incentive programs.

For a set of N candidate programs it produces:
  - all single-program structures
  - all legal 2-program stacks
  - all legal 3-program stacks (up to max_combination_size)

Each combination is run through run_full_analysis (including stacking math)
and the results are ranked by three criteria (lexicographic precedence):
  1. true_net_cost_usd          ascending  (lower = better)
  2. stacking_adjusted_economic_value_usd  descending (higher = better)
  3. legal_flag_count           ascending  (fewer flags = better)

Mutually exclusive and prohibited combinations are INCLUDED in the output
(the stacking engine already handles them correctly — e.g. MUTUALLY_EXCLUSIVE
zeroes the lower-value program). They are surfaced with legal_review_required=True
so the caller can choose to filter them.

No LLM calls. Pure deterministic generation and ranking.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any

from app.calculators.run_full_analysis import StructureAnalysisResult, run_full_analysis

ENGINE_VERSION = "0.1.0"


@dataclass
class ScenarioResult:
    scenario_id: str                          # sorted slugs joined by "+"
    program_slugs: list[str]
    program_count: int
    raw_incentive_value_usd: float            # pre-stacking sum
    adjusted_incentive_value_usd: float       # post-stacking sum
    stacking_reduction_usd: float             # raw − adjusted (always ≥ 0)
    true_net_cost_usd: float
    stacking_adjustments: list[dict]
    legal_flags: list[str]                    # human-readable flag strings
    legal_review_required: bool
    stacking_violations: list[dict]
    stacking_conditionals: list[dict]
    rank: int = 0
    rank_by_net_cost: int = 0
    rank_by_incentive_value: int = 0
    rank_by_flags: int = 0
    engine_version: str = ENGINE_VERSION


def generate_structure_scenarios(
    jurisdiction: dict,
    line_items: list[dict],
    candidate_programs: list[dict[str, Any]],
    # each entry: {program, qualifying_categories, uplifts, jurisdiction_spend_pct}
    stacking_rules: list[dict[str, Any]],
    production_details: dict | None = None,
    fx_rates: dict | None = None,
    max_combination_size: int = 3,
    cost_benchmark: dict | None = None,
    union_fringe_rules: list[dict] | None = None,
    qualification_tests_with_rules: list[dict] | None = None,
    home_jurisdiction_id: str | None = None,
    shooting_days: int = 20,
    key_crew_count: int = 12,
    daily_travel_usd: float = 0.0,
) -> list[ScenarioResult]:
    """
    Generate and rank all feasible production structure scenarios.

    Parameters
    ----------
    jurisdiction                Shooting jurisdiction for all scenarios
    line_items                  Budget line items (shared across all scenarios)
    candidate_programs          Programs to combine — each is a run_full_analysis
                                programs_with_categories entry
    stacking_rules              All known stacking rules for this program set;
                                each scenario filters to rules relevant to its combo
    production_details          Passed through to uplift condition evaluation
    fx_rates                    Currency conversion rates
    max_combination_size        Maximum programs per combination (default 3)
    """
    if not candidate_programs:
        return []

    combo_size = min(max_combination_size, len(candidate_programs))
    scenarios: list[ScenarioResult] = []

    for size in range(1, combo_size + 1):
        for combo in itertools.combinations(candidate_programs, size):
            scenario = _run_combo(
                combo=list(combo),
                jurisdiction=jurisdiction,
                line_items=line_items,
                stacking_rules=stacking_rules,
                production_details=production_details,
                fx_rates=fx_rates,
                cost_benchmark=cost_benchmark,
                union_fringe_rules=union_fringe_rules or [],
                qualification_tests_with_rules=qualification_tests_with_rules or [],
                home_jurisdiction_id=home_jurisdiction_id,
                shooting_days=shooting_days,
                key_crew_count=key_crew_count,
                daily_travel_usd=daily_travel_usd,
            )
            scenarios.append(scenario)

    return _rank(scenarios)


def _run_combo(
    combo: list[dict],
    jurisdiction: dict,
    line_items: list[dict],
    stacking_rules: list[dict],
    production_details: dict | None,
    fx_rates: dict | None,
    cost_benchmark: dict | None,
    union_fringe_rules: list[dict],
    qualification_tests_with_rules: list[dict],
    home_jurisdiction_id: str | None,
    shooting_days: int,
    key_crew_count: int,
    daily_travel_usd: float,
) -> ScenarioResult:
    slugs = sorted(e["program"].get("slug", str(e["program"].get("id", ""))) for e in combo)
    scenario_id = "+".join(slugs)

    program_ids = {str(e["program"].get("id", "")) for e in combo}
    relevant_rules = [
        r for r in stacking_rules
        if str(r["program_a_id"]) in program_ids and str(r["program_b_id"]) in program_ids
    ]

    result: StructureAnalysisResult = run_full_analysis(
        structure_id=scenario_id,
        jurisdiction=jurisdiction,
        line_items=line_items,
        programs_with_categories=combo,
        stacking_rules=relevant_rules,
        qualification_tests_with_rules=qualification_tests_with_rules,
        cost_benchmark=cost_benchmark,
        union_fringe_rules=union_fringe_rules,
        fx_rates=fx_rates,
        production_details=production_details,
        home_jurisdiction_id=home_jurisdiction_id,
        shooting_days=shooting_days,
        key_crew_count=key_crew_count,
        daily_travel_usd=daily_travel_usd,
    )

    # Collect human-readable legal flags from all sources
    legal_flags: list[str] = []
    for v in result.stacking_violations:
        legal_flags.append(
            f"PROHIBITED: programs {v['program_a_id']} and {v['program_b_id']} "
            f"cannot be stacked ({v.get('condition_text') or v.get('notes') or 'see stacking rules'})"
        )
    for c in result.stacking_conditionals:
        legal_flags.append(
            f"CONDITIONAL: programs {c['program_a_id']} and {c['program_b_id']} — "
            f"{c.get('condition_text') or 'legal review required'}"
        )
    # stacking_adj legal flags (mutually_exclusive, value_cap with unparseable cap, etc.)
    stacking_step = next(
        (s for s in result.calculation_trace.get("steps", [])
         if s.get("step") == "stacking_adjustments"),
        {},
    )
    for flag in stacking_step.get("legal_review_flags", []):
        legal_flags.append(flag)

    raw = result.total_incentive_economic_value_usd
    adjusted = result.stacking_adjusted_economic_value_usd

    return ScenarioResult(
        scenario_id=scenario_id,
        program_slugs=slugs,
        program_count=len(combo),
        raw_incentive_value_usd=raw,
        adjusted_incentive_value_usd=adjusted,
        stacking_reduction_usd=max(0.0, raw - adjusted),
        true_net_cost_usd=result.true_net_cost_usd,
        stacking_adjustments=result.stacking_adjustments,
        legal_flags=legal_flags,
        legal_review_required=result.stacking_legal_review_required or bool(legal_flags),
        stacking_violations=result.stacking_violations,
        stacking_conditionals=result.stacking_conditionals,
    )


def _rank(scenarios: list[ScenarioResult]) -> list[ScenarioResult]:
    """
    Rank scenarios by:
      1. true_net_cost_usd        ascending
      2. adjusted_incentive_value descending
      3. legal_flag_count         ascending
    """
    if not scenarios:
        return scenarios

    # Individual dimension ranks
    by_net   = sorted(range(len(scenarios)), key=lambda i: scenarios[i].true_net_cost_usd)
    by_value = sorted(range(len(scenarios)),
                      key=lambda i: scenarios[i].adjusted_incentive_value_usd, reverse=True)
    by_flags = sorted(range(len(scenarios)), key=lambda i: len(scenarios[i].legal_flags))

    net_rank   = {i: r + 1 for r, i in enumerate(by_net)}
    value_rank = {i: r + 1 for r, i in enumerate(by_value)}
    flags_rank = {i: r + 1 for r, i in enumerate(by_flags)}

    for i, s in enumerate(scenarios):
        s.rank_by_net_cost       = net_rank[i]
        s.rank_by_incentive_value = value_rank[i]
        s.rank_by_flags          = flags_rank[i]

    # Composite: net cost weighted heaviest
    def composite(i: int) -> float:
        return (
            net_rank[i]   * 0.50
            + value_rank[i] * 0.30
            + flags_rank[i] * 0.20
        )

    sorted_indices = sorted(range(len(scenarios)), key=composite)
    rank_map = {i: r + 1 for r, i in enumerate(sorted_indices)}
    for i, s in enumerate(scenarios):
        s.rank = rank_map[i]

    return sorted(scenarios, key=lambda s: s.rank)
