"""
maximization_engine.py — Phase F5: Soft money maximization engine.

Compares current production structure against improved and best-case alternatives.
Pure Python, no DB access.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.optimization.structure_generator import (
    GeneratedStructure,
    generate_structures,
)
from app.optimization.qualification_gap_engine import analyse_gaps


@dataclass
class StructureComparison:
    current_structure: GeneratedStructure
    improved_structure: GeneratedStructure
    best_structure: GeneratedStructure
    current_soft_money_usd: float
    potential_soft_money_usd: float
    best_soft_money_usd: float
    incremental_gain_usd: float
    actions_required: list[str]
    qualification_risks: list[str]
    confidence: str


def _pick_best(structures: list[GeneratedStructure]) -> GeneratedStructure:
    return max(structures, key=lambda s: s.estimated_total_incentive_usd)


def _pick_improved(
    structures: list[GeneratedStructure],
    current: GeneratedStructure,
) -> GeneratedStructure:
    candidates = [
        s for s in structures
        if s.qualification_risk in ("LOW", "MEDIUM")
        and s.estimated_total_incentive_usd > current.estimated_total_incentive_usd
    ]
    if candidates:
        return max(candidates, key=lambda s: s.estimated_total_incentive_usd)
    return current


def _generate_actions(
    current: GeneratedStructure,
    improved: GeneratedStructure,
    best: GeneratedStructure,
    project_profile: dict,
    total_budget_usd: float,
) -> list[str]:
    actions = []

    new_jurs = set(improved.secondary_jurisdictions) - set(current.secondary_jurisdictions)
    for jur in list(new_jurs)[:2]:
        actions.append(f"Add co-producer in {jur}")
        actions.append(f"Allocate minimum qualifying spend to {jur}")

    if improved.structure_type in ("treaty_coproduction", "majority_minority"):
        if current.structure_type == "single_country":
            actions.append("Negotiate bilateral co-production agreement")
            actions.append("Apply for official co-production certification")

    new_broadcasters = set(improved.broadcasters_unlocked) - set(current.broadcasters_unlocked)
    for bc in list(new_broadcasters)[:2]:
        actions.append(f"Secure commitment from {bc}")

    if project_profile:
        gap_result = analyse_gaps(
            improved.program_slugs,
            project_profile,
            total_budget_usd,
        )
        for gap in gap_result.blocking_gaps[:3]:
            actions.append(gap.recommendation)

    if not actions:
        actions = ["Optimize spend allocation across jurisdictions"]

    return actions


def _collect_risks(structures: list[GeneratedStructure]) -> list[str]:
    risks = []
    for s in structures:
        if s.qualification_risk == "HIGH":
            risks.append(
                f"High qualification risk for {s.structure_type} structure "
                f"in {s.primary_jurisdiction}"
            )
        for cond in s.required_conditions:
            if cond not in risks:
                risks.append(cond)
    return list(dict.fromkeys(risks))[:5]


def maximize_structure(
    primary_jurisdiction: str,
    secondary_jurisdictions: list[str] | None = None,
    project_profile: dict | None = None,
    total_budget_usd: float = 5_000_000,
    production_type: str = "feature",
) -> StructureComparison:
    """
    Generate current, improved, and best production structures for comparison.

    Returns a StructureComparison with all three structures and the actions
    required to move from current to improved and from improved to best.
    """
    if secondary_jurisdictions is None:
        secondary_jurisdictions = []
    if project_profile is None:
        project_profile = {}

    all_structures = generate_structures(
        primary_jurisdiction=primary_jurisdiction,
        secondary_jurisdictions=secondary_jurisdictions,
        total_budget_usd=total_budget_usd,
        production_type=production_type,
        include_treaty=True,
        include_regional=True,
        include_broadcaster=True,
    )

    if not all_structures:
        placeholder = GeneratedStructure(
            structure_id="fallback",
            structure_type="single_country",
            primary_jurisdiction=primary_jurisdiction,
            secondary_jurisdictions=[],
            program_slugs=[],
            programs_unlocked=[],
            grants_unlocked=[],
            funds_unlocked=[],
            broadcasters_unlocked=[],
            estimated_soft_money_usd=0.0,
            estimated_total_incentive_usd=0.0,
            qualification_risk="HIGH",
            confidence="LOW",
            required_conditions=["No programs found for jurisdiction"],
            notes=f"No programs available for {primary_jurisdiction}",
        )
        return StructureComparison(
            current_structure=placeholder,
            improved_structure=placeholder,
            best_structure=placeholder,
            current_soft_money_usd=0.0,
            potential_soft_money_usd=0.0,
            best_soft_money_usd=0.0,
            incremental_gain_usd=0.0,
            actions_required=["Identify applicable incentive programs for the jurisdiction"],
            qualification_risks=["No incentive programs identified"],
            confidence="LOW",
        )

    # Current = single-country baseline (lowest risk)
    single_country = [s for s in all_structures if s.structure_type == "single_country"]
    current = single_country[0] if single_country else all_structures[-1]

    # Best = highest total incentive
    best = _pick_best(all_structures)

    # Improved = medium step between current and best
    improved = _pick_improved(all_structures, current)
    if improved is current:
        improved = best

    actions = _generate_actions(current, improved, best, project_profile, total_budget_usd)
    risks = _collect_risks([current, improved, best])

    confidence_score = sum(
        1 for s in [current, improved, best]
        if s.confidence == "HIGH"
    )
    confidence = "HIGH" if confidence_score == 3 else ("MEDIUM" if confidence_score >= 1 else "LOW")

    return StructureComparison(
        current_structure=current,
        improved_structure=improved,
        best_structure=best,
        current_soft_money_usd=current.estimated_soft_money_usd,
        potential_soft_money_usd=improved.estimated_soft_money_usd,
        best_soft_money_usd=best.estimated_soft_money_usd,
        incremental_gain_usd=best.estimated_soft_money_usd - current.estimated_soft_money_usd,
        actions_required=actions,
        qualification_risks=risks,
        confidence=confidence,
    )
