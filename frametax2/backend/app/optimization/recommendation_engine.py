"""
recommendation_engine.py — Phase D6: Deterministic qualification recommendations.

Given a production structure (set of program slugs + production profile),
returns:
  - why each program qualifies or fails
  - what changes would qualify it
  - estimated impact of each change
  - lowest-friction overall recommendation

No optimization scoring. No ranking. No budget calculations.
Pure deterministic rule evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.optimization.qualification_path_engine import (
    QualificationAnalysis,
    QualificationPath,
    analyse_qualification,
    get_test_slug_for_program,
    summarise_deficits,
)
from app.data.structure_graph_model import (
    get_edges_from,
    get_incompatibilities,
    get_requirements,
)
from app.data.cultural_qualification_model import (
    get_requirements as get_nationality_requirements,
    has_cultural_test,
)
from app.optimization.financing_interaction_model import (
    get_all_govt_assistance_for_slug,
    get_stacking_ceiling,
)


ENGINE_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ProgramQualificationStatus:
    program_slug: str
    program_name: str
    is_qualifying: bool
    has_cultural_test: bool
    test_slug: str | None
    qualification_analysis: QualificationAnalysis | None
    qualifying_reasons: list[str]
    disqualifying_reasons: list[str]
    unknown_factors: list[str]
    structural_requirements_met: bool  # from structure graph
    structural_gaps: list[str]


@dataclass
class StructureRecommendation:
    recommendation_id: str
    priority: int  # 1 = highest priority
    recommendation_type: str  # add_crew | move_spend | add_coproducer | increase_spend | use_treaty | restructure | move_post | change_entity
    target_program_slug: str
    description: str
    actions: list[str]
    estimated_impact: str
    friction_score: float
    unlocks_programs: list[str]
    notes: str | None = None


@dataclass
class StructureQualificationReport:
    structure_programs: list[str]   # program slugs in structure
    production_profile: dict[str, Any]
    program_statuses: list[ProgramQualificationStatus]
    overall_qualifying: bool        # True if ALL programs qualify
    qualifying_programs: list[str]
    failing_programs: list[str]
    recommendations: list[StructureRecommendation]  # sorted by priority
    financing_notes: list[str]      # govt assistance and ceiling notes
    incompatibilities: list[str]    # structural incompatibility warnings
    engine_version: str = ENGINE_VERSION


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_structural_requirements(program_slug: str) -> tuple[bool, list[str]]:
    """
    Check structure graph requirements for a program.
    Returns (all_met, list_of_gaps).
    """
    req_edges = get_requirements(program_slug)
    gaps = []
    for edge in req_edges:
        if edge.edge_type == "requires":
            gaps.append(
                f"{program_slug} requires {edge.target_slug}: {edge.condition or edge.notes}"
            )
    return len(gaps) == 0, gaps


def _get_qualifying_reasons(program_slug: str, profile: dict) -> list[str]:
    """Build list of reasons a program qualifies."""
    reasons = []
    analysis = analyse_qualification(program_slug, profile)
    if analysis.is_currently_qualifying:
        if analysis.current_score is not None:
            reasons.append(
                f"Passes {analysis.test_slug}: score {analysis.current_score}/"
                f"{analysis.required_score}"
            )
        else:
            reasons.append(f"Meets all qualification requirements for {program_slug}")

    nat_reqs = get_nationality_requirements(program_slug)
    required_roles = [r for r in nat_reqs if r.status == "required"]
    satisfied = [r for r in required_roles
                 if profile.get(f"{r.role}_{r.jurisdiction_code.lower()}" if r.jurisdiction_code else r.role)]
    if satisfied:
        reasons.extend(
            f"{r.role} ({r.jurisdiction_code}) nationality requirement met"
            for r in satisfied
        )
    return reasons


def _get_disqualifying_reasons(program_slug: str, profile: dict) -> list[str]:
    """Build list of reasons a program fails."""
    analysis = analyse_qualification(program_slug, profile)
    return summarise_deficits(analysis)


def _build_financing_notes(structure_programs: list[str]) -> list[str]:
    notes = []
    for slug_b in structure_programs:
        govt_assists = get_all_govt_assistance_for_slug(slug_b)
        sources_in_structure = [ia for ia in govt_assists if ia.slug_a in structure_programs]
        for ia in sources_in_structure:
            if ia.reduction_pct and ia.reduction_pct > 0:
                notes.append(
                    f"[GOVT ASSISTANCE] {ia.slug_a} → {ia.slug_b}: "
                    f"{ia.condition}"
                )

    # Stacking ceilings
    for i, slug_a in enumerate(structure_programs):
        for slug_b in structure_programs[i + 1:]:
            ceiling = get_stacking_ceiling(slug_a, slug_b)
            if ceiling is not None:
                notes.append(
                    f"[CEILING] {slug_a} + {slug_b}: combined max {ceiling:.0%} of budget"
                )
    return notes


def _check_incompatibilities(structure_programs: list[str]) -> list[str]:
    warnings = []
    for slug in structure_programs:
        incompat = get_incompatibilities(slug)
        for other in incompat:
            if other in structure_programs:
                warnings.append(
                    f"[INCOMPATIBLE] {slug} and {other} cannot be combined on the same "
                    f"qualifying expenditure. Review structure for mutual exclusivity."
                )
    return list(dict.fromkeys(warnings))  # dedup while preserving order


def _generate_recommendations(
    failing_statuses: list[ProgramQualificationStatus],
) -> list[StructureRecommendation]:
    recs: list[StructureRecommendation] = []
    priority = 1

    for status in failing_statuses:
        analysis = status.qualification_analysis
        if analysis is None:
            continue

        # Add path-based recommendations
        for path in analysis.paths:
            recs.append(StructureRecommendation(
                recommendation_id=f"{status.program_slug}_{path.path_id}",
                priority=priority,
                recommendation_type=_classify_path(path.path_id),
                target_program_slug=status.program_slug,
                description=f"[{status.program_slug}] {path.description}",
                actions=path.actions,
                estimated_impact=path.estimated_impact,
                friction_score=path.friction_score,
                unlocks_programs=path.unlocks_programs,
                notes=path.notes,
            ))
            priority += 1

        # Add per-deficit recommendations where no path covers them
        for deficit in analysis.deficits:
            already_covered = any(
                deficit.criterion_code in p.path_id or deficit.recommendation in p.description
                for p in analysis.paths
            )
            if not already_covered:
                recs.append(StructureRecommendation(
                    recommendation_id=f"{status.program_slug}_deficit_{deficit.criterion_code}",
                    priority=priority,
                    recommendation_type=_classify_deficit(deficit.criterion_code),
                    target_program_slug=status.program_slug,
                    description=f"[{status.program_slug}] {deficit.description}",
                    actions=[deficit.recommendation],
                    estimated_impact="Closes one qualification gap",
                    friction_score=deficit.friction_score,
                    unlocks_programs=[status.program_slug],
                ))
                priority += 1

        # Structural gap recommendations
        for gap in status.structural_gaps:
            recs.append(StructureRecommendation(
                recommendation_id=f"{status.program_slug}_structural",
                priority=priority,
                recommendation_type="add_coproducer",
                target_program_slug=status.program_slug,
                description=f"[{status.program_slug}] Structural requirement: {gap}",
                actions=[gap],
                estimated_impact="Unlocks required structural prerequisite",
                friction_score=6.0,
                unlocks_programs=[status.program_slug],
            ))
            priority += 1

    # Sort by friction (lowest first within priorities)
    return sorted(recs, key=lambda r: (r.friction_score, r.priority))


def _classify_path(path_id: str) -> str:
    if "crew" in path_id or "director" in path_id or "writer" in path_id or "cast" in path_id:
        return "add_crew"
    if "spend" in path_id or "shoot" in path_id or "post" in path_id or "vfx" in path_id:
        return "move_spend"
    if "entity" in path_id or "company" in path_id:
        return "change_entity"
    if "producer" in path_id or "coproducer" in path_id:
        return "add_coproducer"
    if "treaty" in path_id:
        return "use_treaty"
    return "restructure"


def _classify_deficit(code: str) -> str:
    code_upper = code.upper()
    if any(x in code_upper for x in ["DIR", "WRT", "CAST", "COMP", "CREW", "DOP"]):
        return "add_crew"
    if any(x in code_upper for x in ["SPEND", "PCT", "SHOOT", "POST", "VFX"]):
        return "move_spend"
    if any(x in code_upper for x in ["ENTITY", "COMPANY"]):
        return "change_entity"
    if any(x in code_upper for x in ["COUNTRIES", "MEMBERS", "PRODUCER", "COPRODUCER"]):
        return "add_coproducer"
    return "restructure"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_program_qualification(
    program_slug: str,
    program_name: str,
    production_profile: dict[str, Any],
) -> ProgramQualificationStatus:
    """
    Evaluate whether a single program qualifies given the production profile.
    """
    test_slug = get_test_slug_for_program(program_slug)
    has_test = has_cultural_test(program_slug)

    analysis = analyse_qualification(program_slug, production_profile, test_slug)
    structural_ok, structural_gaps = _check_structural_requirements(program_slug)

    qualifying_reasons = _get_qualifying_reasons(program_slug, production_profile)
    disqualifying_reasons = _get_disqualifying_reasons(program_slug, production_profile)

    is_qualifying = (
        analysis.is_currently_qualifying
        and structural_ok
    )

    return ProgramQualificationStatus(
        program_slug=program_slug,
        program_name=program_name,
        is_qualifying=is_qualifying,
        has_cultural_test=has_test,
        test_slug=test_slug,
        qualification_analysis=analysis,
        qualifying_reasons=qualifying_reasons,
        disqualifying_reasons=disqualifying_reasons,
        unknown_factors=analysis.unknown_factors,
        structural_requirements_met=structural_ok,
        structural_gaps=structural_gaps,
    )


def evaluate_structure(
    structure_programs: list[tuple[str, str]],   # [(slug, name), ...]
    production_profile: dict[str, Any],
) -> StructureQualificationReport:
    """
    Evaluate the qualification status of a full production structure.

    structure_programs: list of (program_slug, program_name) tuples
    production_profile: dict of production facts (see PRODUCTION_PROFILE_SCHEMA)

    Returns a full StructureQualificationReport with recommendations sorted by friction.
    """
    slugs = [s for s, _ in structure_programs]
    statuses: list[ProgramQualificationStatus] = []

    for slug, name in structure_programs:
        status = evaluate_program_qualification(slug, name, production_profile)
        statuses.append(status)

    qualifying = [s.program_slug for s in statuses if s.is_qualifying]
    failing = [s.program_slug for s in statuses if not s.is_qualifying]
    failing_statuses = [s for s in statuses if not s.is_qualifying]

    recommendations = _generate_recommendations(failing_statuses)
    financing_notes = _build_financing_notes(slugs)
    incompatibilities = _check_incompatibilities(slugs)

    return StructureQualificationReport(
        structure_programs=slugs,
        production_profile=production_profile,
        program_statuses=statuses,
        overall_qualifying=len(failing) == 0,
        qualifying_programs=qualifying,
        failing_programs=failing,
        recommendations=recommendations,
        financing_notes=financing_notes,
        incompatibilities=incompatibilities,
    )


def explain_structure(report: StructureQualificationReport) -> dict[str, Any]:
    """
    Convert a StructureQualificationReport into a human-readable explanation dict.
    """
    return {
        "overall_qualifying": report.overall_qualifying,
        "qualifying_programs": report.qualifying_programs,
        "failing_programs": report.failing_programs,
        "program_details": [
            {
                "slug": s.program_slug,
                "name": s.program_name,
                "is_qualifying": s.is_qualifying,
                "qualifying_reasons": s.qualifying_reasons,
                "disqualifying_reasons": s.disqualifying_reasons,
                "unknown_factors": s.unknown_factors,
                "structural_gaps": s.structural_gaps,
            }
            for s in report.program_statuses
        ],
        "recommendations": [
            {
                "priority": r.priority,
                "type": r.recommendation_type,
                "target": r.target_program_slug,
                "description": r.description,
                "actions": r.actions,
                "impact": r.estimated_impact,
                "friction": r.friction_score,
                "unlocks": r.unlocks_programs,
            }
            for r in report.recommendations
        ],
        "financing_notes": report.financing_notes,
        "incompatibilities": report.incompatibilities,
    }
