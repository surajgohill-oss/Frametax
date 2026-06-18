"""
rank_production_structures.py

Ranks a list of calculated production structures by multiple criteria.
Returns structures sorted by each ranking dimension with an overall composite rank.

No LLM calls. Pure deterministic sorting.
"""
from __future__ import annotations

from dataclasses import dataclass

ENGINE_VERSION = "0.1.0"


@dataclass
class RankedStructure:
    structure_id: str
    name: str
    rank_by_net_cost: int
    rank_by_risk_adjusted_net_cost: int
    rank_by_incentive_value: int
    rank_by_optimization_opportunity: int
    composite_rank: int
    true_net_cost_usd: float | None
    risk_adjusted_net_cost_usd: float | None
    total_incentive_value_usd: float | None
    optimization_opportunity_usd: float | None


def rank_structures(
    structures: list[dict],
) -> list[RankedStructure]:
    """
    structures: list of calculation result dicts, each with:
        {structure_id, name, true_net_cost_usd, risk_adjusted_net_cost_usd,
         total_incentive_value_usd, optimization_opportunities}

    optimization_opportunity = sum of conditional/gap optimization value
    """
    if not structures:
        return []

    def safe_float(v: object) -> float:
        try:
            return float(v) if v is not None else float("inf")
        except (TypeError, ValueError):
            return float("inf")

    def optimization_value(s: dict) -> float:
        opps = s.get("optimization_opportunities") or []
        total = 0.0
        for opp in opps:
            total += float(opp.get("potential_value_usd") or 0.0)
        return total

    sorted_by_net = sorted(structures, key=lambda s: safe_float(s.get("true_net_cost_usd")))
    sorted_by_risk = sorted(structures, key=lambda s: safe_float(s.get("risk_adjusted_net_cost_usd")))
    sorted_by_incentive = sorted(
        structures, key=lambda s: safe_float(s.get("total_incentive_value_usd")), reverse=True
    )
    sorted_by_opp = sorted(structures, key=lambda s: optimization_value(s), reverse=True)

    net_rank = {s["structure_id"]: i + 1 for i, s in enumerate(sorted_by_net)}
    risk_rank = {s["structure_id"]: i + 1 for i, s in enumerate(sorted_by_risk)}
    incentive_rank = {s["structure_id"]: i + 1 for i, s in enumerate(sorted_by_incentive)}
    opp_rank = {s["structure_id"]: i + 1 for i, s in enumerate(sorted_by_opp)}

    # Composite rank: weighted sum (net cost most important)
    def composite(s: dict) -> float:
        sid = s["structure_id"]
        return (
            net_rank.get(sid, 99) * 0.40
            + risk_rank.get(sid, 99) * 0.30
            + incentive_rank.get(sid, 99) * 0.20
            + opp_rank.get(sid, 99) * 0.10
        )

    sorted_by_composite = sorted(structures, key=composite)
    composite_rank_map = {s["structure_id"]: i + 1 for i, s in enumerate(sorted_by_composite)}

    return [
        RankedStructure(
            structure_id=s["structure_id"],
            name=s.get("name", ""),
            rank_by_net_cost=net_rank.get(s["structure_id"], 99),
            rank_by_risk_adjusted_net_cost=risk_rank.get(s["structure_id"], 99),
            rank_by_incentive_value=incentive_rank.get(s["structure_id"], 99),
            rank_by_optimization_opportunity=opp_rank.get(s["structure_id"], 99),
            composite_rank=composite_rank_map.get(s["structure_id"], 99),
            true_net_cost_usd=s.get("true_net_cost_usd"),
            risk_adjusted_net_cost_usd=s.get("risk_adjusted_net_cost_usd"),
            total_incentive_value_usd=s.get("total_incentive_value_usd"),
            optimization_opportunity_usd=optimization_value(s) or None,
        )
        for s in structures
    ]
