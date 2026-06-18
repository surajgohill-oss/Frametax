"""
calculate_net_budget.py

Computes the true net production budget for a structure:

  true_net_cost = rebase_btl + fixed_atl + travel_cost - total_incentive_economic_value

Where:
  rebase_btl = variable BTL cost rebased to local jurisdiction rates
  fixed_atl  = ATL fixed fees (unchanged — talent is contractually fixed)
  travel_cost = key crew relocation cost
  total_incentive_economic_value = sum of economic values of all claimed incentives
"""
from __future__ import annotations

from dataclasses import dataclass

ENGINE_VERSION = "0.1.0"


@dataclass
class NetBudgetResult:
    total_input_budget_usd: float
    fixed_atl_usd: float
    variable_btl_usd: float
    rebase_btl_usd: float
    rebase_delta_usd: float          # negative = cheaper, positive = more expensive
    travel_cost_usd: float
    total_incentive_economic_value_usd: float
    true_net_cost_usd: float
    savings_vs_no_incentive_usd: float
    engine_version: str = ENGINE_VERSION


def calculate_net_budget(
    fixed_atl_usd: float,
    variable_btl_usd: float,
    cost_benchmark: dict | None,
    travel_cost_usd: float,
    total_incentive_economic_value_usd: float,
) -> NetBudgetResult:
    """
    cost_benchmark: LocalCostBenchmark-shaped dict with multipliers.
    If None, no rebasing is applied (multipliers default to 1.0).
    """
    total_input = fixed_atl_usd + variable_btl_usd

    # Rebase BTL to jurisdiction rates
    if cost_benchmark:
        rebase_btl = _rebase_btl(variable_btl_usd, cost_benchmark)
    else:
        rebase_btl = variable_btl_usd

    rebase_delta = rebase_btl - variable_btl_usd

    true_net = (
        fixed_atl_usd
        + rebase_btl
        + travel_cost_usd
        - total_incentive_economic_value_usd
    )
    true_net = max(true_net, 0.0)

    savings_vs_no_incentive = (
        fixed_atl_usd + rebase_btl + travel_cost_usd
    ) - true_net

    return NetBudgetResult(
        total_input_budget_usd=total_input,
        fixed_atl_usd=fixed_atl_usd,
        variable_btl_usd=variable_btl_usd,
        rebase_btl_usd=rebase_btl,
        rebase_delta_usd=rebase_delta,
        travel_cost_usd=travel_cost_usd,
        total_incentive_economic_value_usd=total_incentive_economic_value_usd,
        true_net_cost_usd=true_net,
        savings_vs_no_incentive_usd=savings_vs_no_incentive,
    )


def _rebase_btl(variable_btl_usd: float, benchmark: dict) -> float:
    """
    Apply weighted cost multipliers from LocalCostBenchmark to rebase BTL spend.
    If no multipliers available, returns variable_btl_usd unchanged.
    """
    # Use simple average of available multipliers as weighted factor
    multipliers = [
        v for k, v in benchmark.items()
        if k.endswith("_multiplier") and v is not None
    ]
    if not multipliers:
        return variable_btl_usd

    avg_multiplier = sum(multipliers) / len(multipliers)
    return variable_btl_usd * float(avg_multiplier)


def calculate_key_crew_travel(
    jurisdiction_id: str,
    home_jurisdiction_id: str,
    shooting_days: int,
    key_crew_count: int = 12,
    daily_travel_usd: float = 0.0,
) -> float:
    """
    Compute key crew relocation cost for a jurisdiction.
    Returns 0 if shooting in home jurisdiction.
    """
    if jurisdiction_id == home_jurisdiction_id:
        return 0.0
    return daily_travel_usd * shooting_days * key_crew_count
