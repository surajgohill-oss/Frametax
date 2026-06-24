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

    Only flags missing program/entity/treaty prerequisites — not test requirements,
    which are already evaluated by analyse_qualification.
    """
    outgoing_requires = [
        e for e in get_edges_from(program_slug)
        if e.edge_type == "requires" and e.target_type not in ("test", "cultural_test")
    ]
    gaps = []
    for edge in outgoing_requires:
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


@dataclass
class ActionableRecommendation:
    recommendation_id: str
    recommendation_type: str   # same types as StructureRecommendation
    title: str
    description: str
    specific_actions: list[str]
    estimated_value_unlocked_usd: float
    affected_programs: list[str]
    qualification_impact: str
    confidence: str            # "HIGH" | "MEDIUM" | "LOW"
    implementation_friction: float  # 1-10
    implementation_steps: list[str]
    timeline_weeks: int
    cost_estimate_usd: float
    net_value_usd: float       # estimated_value_unlocked - cost_estimate


def generate_recommendations(
    gap_result: "GapAnalysisResult",  # noqa: F821
    structure_slugs: list[str],
    project_profile: dict[str, Any],
    total_budget_usd: float = 5_000_000,
) -> list[ActionableRecommendation]:
    """
    Convert gap analysis into prioritised, actionable recommendations.
    """
    from app.optimization.qualification_gap_engine import GapAnalysisResult as _GapResult
    from app.data.global_inventory import ALL_PROGRAMS as _ALL

    _slug_map = {p.program_slug: p for p in _ALL}

    def _rate(slug: str) -> float:
        p = _slug_map.get(slug)
        return float(p.base_rate) if p and p.base_rate else 0.0

    recs: list[ActionableRecommendation] = []
    seen: set[str] = set()

    for gap in gap_result.all_gaps:
        rid = f"{gap.program_slug}_{gap.gap_type}"
        if rid in seen:
            continue
        seen.add(rid)

        spend_pct = float(project_profile.get("qualifying_spend_pct", 0.6))
        est_value = gap.estimated_value_unlocked_usd or (_rate(gap.program_slug) * total_budget_usd * spend_pct * 0.5)

        if gap.gap_type == "missing_spend":
            jur = gap.program_slug.split("_")[0].upper()
            steps = [
                f"Review current spend allocation for {jur}",
                f"Shift location, crew, or post-production work to {jur}",
                f"Verify qualifying expenditure definition for {gap.program_slug}",
                "Engage local line producer to plan reallocation",
            ]
            recs.append(ActionableRecommendation(
                recommendation_id=rid,
                recommendation_type="move_spend",
                title=f"Increase {jur} qualifying spend",
                description=gap.description,
                specific_actions=[gap.recommendation],
                estimated_value_unlocked_usd=est_value,
                affected_programs=[gap.program_slug],
                qualification_impact=f"Meets minimum spend threshold for {gap.program_slug}",
                confidence="HIGH",
                implementation_friction=gap.friction_score,
                implementation_steps=steps,
                timeline_weeks=4,
                cost_estimate_usd=0.0,
                net_value_usd=est_value,
            ))

        elif gap.gap_type == "missing_entity":
            steps = [
                "Engage local entertainment lawyer",
                "Register qualifying production company",
                "Open local bank account for qualifying spend",
                "Obtain necessary permits and tax registrations",
            ]
            recs.append(ActionableRecommendation(
                recommendation_id=rid,
                recommendation_type="change_entity",
                title=f"Establish qualifying {gap.program_slug.split('_')[0].upper()} entity",
                description=gap.description,
                specific_actions=[gap.recommendation],
                estimated_value_unlocked_usd=est_value,
                affected_programs=[gap.program_slug],
                qualification_impact=f"Unlocks {gap.program_slug} eligibility",
                confidence="HIGH",
                implementation_friction=gap.friction_score,
                implementation_steps=steps,
                timeline_weeks=6,
                cost_estimate_usd=8_000,
                net_value_usd=est_value - 8_000,
            ))

        elif gap.gap_type == "missing_broadcaster_commitment":
            steps = [
                f"Develop broadcast pitch package for {gap.program_name}",
                "Approach broadcaster development executive",
                "Negotiate co-production or pre-sale licence",
                "Obtain signed term sheet before claiming fund access",
            ]
            recs.append(ActionableRecommendation(
                recommendation_id=rid,
                recommendation_type="add_coproducer",
                title=f"Secure broadcaster licence for {gap.program_name}",
                description=gap.description,
                specific_actions=[gap.recommendation],
                estimated_value_unlocked_usd=est_value,
                affected_programs=[gap.program_slug],
                qualification_impact=f"Unlocks {gap.program_name} access",
                confidence="MEDIUM",
                implementation_friction=gap.friction_score,
                implementation_steps=steps,
                timeline_weeks=12,
                cost_estimate_usd=0.0,
                net_value_usd=est_value,
            ))

        elif gap.gap_type == "missing_co_producer":
            steps = [
                "Identify co-production partners in required territory",
                "Engage co-production lawyer to draft co-production agreement",
                "Apply for official co-production status if required",
                "Allocate minimum spend to each co-producer's territory",
            ]
            recs.append(ActionableRecommendation(
                recommendation_id=rid,
                recommendation_type="add_coproducer",
                title=f"Add co-producer for {gap.program_name}",
                description=gap.description,
                specific_actions=[gap.recommendation],
                estimated_value_unlocked_usd=est_value,
                affected_programs=[gap.program_slug],
                qualification_impact=f"Meets minimum co-producer threshold for {gap.program_name}",
                confidence="MEDIUM",
                implementation_friction=gap.friction_score,
                implementation_steps=steps,
                timeline_weeks=8,
                cost_estimate_usd=15_000,
                net_value_usd=est_value - 15_000,
            ))

        elif gap.gap_type == "missing_cultural_points":
            steps = [
                "Review full cultural test criteria",
                "Identify highest-friction criteria not currently met",
                "Add or replace crew with eligible nationality where possible",
                "Consider setting/subject matter adjustments for automatic criteria",
            ]
            recs.append(ActionableRecommendation(
                recommendation_id=rid,
                recommendation_type="add_crew",
                title=f"Improve cultural test score for {gap.program_name}",
                description=gap.description,
                specific_actions=[gap.recommendation],
                estimated_value_unlocked_usd=est_value,
                affected_programs=[gap.program_slug],
                qualification_impact=f"Passes cultural qualification test for {gap.program_slug}",
                confidence="MEDIUM",
                implementation_friction=gap.friction_score,
                implementation_steps=steps,
                timeline_weeks=4,
                cost_estimate_usd=0.0,
                net_value_usd=est_value,
            ))

        elif gap.gap_type in ("missing_post_spend", "missing_vfx_spend"):
            label = "post-production" if "post" in gap.gap_type else "VFX"
            steps = [
                f"Identify {label} vendors in the qualifying territory",
                f"Get quotes for {label} services locally",
                f"Shift {label} work to qualifying jurisdiction",
                "Confirm qualifying expenditure definition with tax authority",
            ]
            recs.append(ActionableRecommendation(
                recommendation_id=rid,
                recommendation_type="move_post",
                title=f"Move {label} spend to qualify for {gap.program_name}",
                description=gap.description,
                specific_actions=[gap.recommendation],
                estimated_value_unlocked_usd=est_value,
                affected_programs=[gap.program_slug],
                qualification_impact=f"Meets {label} spend threshold for {gap.program_slug}",
                confidence="HIGH",
                implementation_friction=gap.friction_score,
                implementation_steps=steps,
                timeline_weeks=6,
                cost_estimate_usd=0.0,
                net_value_usd=est_value,
            ))

    # Sort: highest net value first, then lowest friction
    recs.sort(key=lambda r: (-r.net_value_usd, r.implementation_friction))
    return recs


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


# ---------------------------------------------------------------------------
# Phase F3: Actionable Recommendation Engine
# ---------------------------------------------------------------------------

@dataclass
class ActionableRecommendation:
    recommendation_id: str
    recommendation_type: str
    title: str
    description: str
    specific_actions: list[str]
    estimated_value_unlocked_usd: float
    affected_programs: list[str]
    qualification_impact: str
    confidence: str  # "HIGH" | "MEDIUM" | "LOW"
    implementation_friction: float  # 1-10
    implementation_steps: list[str]
    timeline_weeks: int
    cost_estimate_usd: float
    net_value_usd: float  # estimated_value - cost_estimate


_RECOMMENDATION_TEMPLATES: list[dict] = [
    {
        "id": "add_canadian_minority_coproducer",
        "type": "add_coproducer",
        "title": "Add Canadian minority co-producer",
        "description": "Attach a Canadian minority co-production partner to unlock Canadian incentives",
        "actions": [
            "Identify a CAVCO-registered Canadian production company",
            "Execute a co-production agreement with minimum 20% Canadian spend",
            "Ensure Canadian co-producer has editorial creative role",
            "Apply for official Canadian co-production certification via CAVCO",
        ],
        "affected_slugs": ["ca_federal_cptc", "ca_cmf"],
        "impact": "Unlocks federal CPTC (25% on Canadian qualifying labour) and CMF funding",
        "confidence": "HIGH",
        "friction": 6.0,
        "steps": [
            "Research CAVCO-registered Canadian production companies",
            "Negotiate minority co-production agreement (6-8 weeks)",
            "Submit certification application to CAVCO",
            "Coordinate Canadian spend plan with co-producer",
        ],
        "timeline_weeks": 12,
        "cost_usd": 15000,
        "value_multiplier": 0.25,
        "spend_pct": 0.20,
    },
    {
        "id": "move_editor_to_ireland",
        "type": "add_crew",
        "title": "Move editor to Ireland",
        "description": "Hire an Irish editor or move post-production editing to Ireland",
        "actions": [
            "Hire Irish-resident film editor",
            "Move editing suite to Dublin or Cork",
            "Ensure editing spend counts as Irish qualifying expenditure",
        ],
        "affected_slugs": ["ie_section_481"],
        "impact": "Adds Irish crew element, increases Section 481 qualifying spend",
        "confidence": "HIGH",
        "friction": 3.0,
        "steps": [
            "Contact IFTN or Screen Ireland for Irish editor roster",
            "Negotiate editor deal with Irish entity",
            "Set up Irish editing facility or use existing post house",
        ],
        "timeline_weeks": 4,
        "cost_usd": 5000,
        "value_multiplier": 0.32,
        "spend_pct": 0.05,
    },
    {
        "id": "move_vfx_to_quebec",
        "type": "move_spend",
        "title": "Move VFX to Quebec",
        "description": "Relocate visual effects work to Quebec to unlock SODEC and OCASE incentives",
        "actions": [
            "Engage Quebec VFX house (e.g., Rodeo FX, Cinesite Montreal)",
            "Ensure minimum 10% of budget spent on Quebec VFX",
            "Verify VFX house is registered for SODEC",
        ],
        "affected_slugs": ["ca_qc_sodec", "ca_on_ocase"],
        "impact": "Unlocks Quebec SODEC VFX credit on qualifying VFX spend",
        "confidence": "MEDIUM",
        "friction": 4.0,
        "steps": [
            "RFP to Quebec VFX vendors",
            "Negotiate VFX agreement with Quebec spend commitment",
            "Verify SODEC eligibility with Quebec production consultant",
        ],
        "timeline_weeks": 8,
        "cost_usd": 8000,
        "value_multiplier": 0.20,
        "spend_pct": 0.10,
    },
    {
        "id": "increase_uk_spend_to_25pct",
        "type": "move_spend",
        "title": "Increase UK spend to 25%",
        "description": "Increase qualifying UK expenditure to 25% to pass BFI AVEC C-section threshold",
        "actions": [
            "Move additional principal photography to UK locations",
            "Hire additional UK crew for UK shoot days",
            "Move post-production facilities to UK",
        ],
        "affected_slugs": ["uk_avec"],
        "impact": "Passes BFI AVEC minimum UK spend threshold, unlocks 34% AVEC rebate",
        "confidence": "HIGH",
        "friction": 5.0,
        "steps": [
            "Review current UK spend allocation",
            "Identify shoots that can be relocated to UK",
            "Hire UK post-production facility",
            "File BFI AVEC application with updated UK spend schedule",
        ],
        "timeline_weeks": 6,
        "cost_usd": 10000,
        "value_multiplier": 0.34,
        "spend_pct": 0.25,
    },
    {
        "id": "add_french_broadcaster",
        "type": "add_broadcaster",
        "title": "Add French broadcaster",
        "description": "Secure pre-sale or co-production deal with French broadcaster",
        "actions": [
            "Pitch to France Televisions or Canal+",
            "Negotiate minimum broadcast license fee",
            "Execute co-production agreement with French broadcaster",
        ],
        "affected_slugs": ["fr_cnc_production", "fr_trip", "canal_plus_fund", "france_televisions_fund"],
        "impact": "Unlocks CNC automatic support and improves French Trip eligibility",
        "confidence": "MEDIUM",
        "friction": 7.0,
        "steps": [
            "Prepare French broadcaster pitch package",
            "Submit to France Televisions/Canal+ development departments",
            "Negotiate license terms (typically 8-12 weeks)",
            "Execute broadcaster agreement",
        ],
        "timeline_weeks": 16,
        "cost_usd": 20000,
        "value_multiplier": 0.30,
        "spend_pct": 0.15,
    },
    {
        "id": "add_regional_spend_bavaria",
        "type": "move_spend",
        "title": "Add regional spend in Bavaria",
        "description": "Commit minimum 10% of budget to Bavarian production expenditure",
        "actions": [
            "Locate at least one principal photography week in Bavaria",
            "Hire Bavarian crew and use Bavarian facilities",
            "Apply to FilmFernsehFonds Bayern for regional support",
        ],
        "affected_slugs": ["bavarian_film_fund", "de_dfff"],
        "impact": "Unlocks FilmFernsehFonds Bayern regional grant (up to 2M EUR) in addition to DFFF",
        "confidence": "HIGH",
        "friction": 4.0,
        "steps": [
            "Review Bavaria location options with production designer",
            "Contact FilmFernsehFonds Bayern for pre-application meeting",
            "Submit regional fund application",
        ],
        "timeline_weeks": 8,
        "cost_usd": 5000,
        "value_multiplier": 0.25,
        "spend_pct": 0.10,
    },
    {
        "id": "establish_irish_company",
        "type": "change_entity",
        "title": "Establish Irish production entity",
        "description": "Incorporate a production company in Ireland to access Section 481",
        "actions": [
            "Incorporate limited company under Irish Companies Act",
            "Register with Revenue Commissioners",
            "Engage Irish production accountant",
        ],
        "affected_slugs": ["ie_section_481"],
        "impact": "Satisfies entity requirement for Section 481 (32% rebate on Irish spend)",
        "confidence": "HIGH",
        "friction": 7.0,
        "steps": [
            "Instruct Irish solicitor to incorporate company (2-3 weeks)",
            "Obtain Revenue registration and PPS numbers",
            "Open Irish bank account",
            "Engage Section 481 specialist accountant",
        ],
        "timeline_weeks": 6,
        "cost_usd": 8000,
        "value_multiplier": 0.32,
        "spend_pct": 0.15,
    },
    {
        "id": "add_australian_broadcaster",
        "type": "add_broadcaster",
        "title": "Add Australian broadcaster",
        "description": "Secure ABC or streaming platform commitment for Australian content",
        "actions": [
            "Pitch to ABC Television or Screen Australia",
            "Negotiate Australian broadcast license",
            "Ensure Australian content classification",
        ],
        "affected_slugs": ["au_producer_offset", "abc_television_fund"],
        "impact": "Strengthens Australian content credentials and improves Producer Offset application",
        "confidence": "MEDIUM",
        "friction": 6.0,
        "steps": [
            "Prepare Australian broadcaster pitch",
            "Submit to ABC or Foxtel",
            "Negotiate license (8-12 weeks)",
        ],
        "timeline_weeks": 12,
        "cost_usd": 15000,
        "value_multiplier": 0.40,
        "spend_pct": 0.15,
    },
]


def generate_recommendations(
    gap_result: "GapAnalysisResult",
    structure_slugs: list[str],
    project_profile: dict,
    total_budget_usd: float = 5_000_000,
) -> list[ActionableRecommendation]:
    """
    Generate actionable recommendations based on gap analysis results.

    Returns a list of ActionableRecommendation objects sorted by net value (descending).
    """
    recommendations: list[ActionableRecommendation] = []

    # Collect all program slugs in gaps
    gap_slugs = {g.program_slug for g in gap_result.all_gaps}

    for template in _RECOMMENDATION_TEMPLATES:
        # Check if any affected slugs are in the structure with gaps
        affected_in_structure = [
            s for s in template["affected_slugs"] if s in structure_slugs
        ]
        affected_with_gaps = [
            s for s in template["affected_slugs"] if s in gap_slugs
        ]

        # Generate recommendation if there are relevant gaps or affected programs in structure
        is_relevant = bool(affected_with_gaps) or bool(affected_in_structure)

        if not is_relevant:
            continue

        estimated_value = (
            template["value_multiplier"]
            * total_budget_usd
            * template["spend_pct"]
        )
        net_value = estimated_value - template["cost_usd"]

        rec = ActionableRecommendation(
            recommendation_id=template["id"],
            recommendation_type=template["type"],
            title=template["title"],
            description=template["description"],
            specific_actions=template["actions"],
            estimated_value_unlocked_usd=estimated_value,
            affected_programs=template["affected_slugs"],
            qualification_impact=template["impact"],
            confidence=template["confidence"],
            implementation_friction=template["friction"],
            implementation_steps=template["steps"],
            timeline_weeks=template["timeline_weeks"],
            cost_estimate_usd=template["cost_usd"],
            net_value_usd=net_value,
        )
        recommendations.append(rec)

    # If no template recommendations triggered but we have gaps, generate generic ones
    if not recommendations and gap_result.all_gaps:
        for gap in gap_result.all_gaps[:3]:  # top 3 gaps
            rec = ActionableRecommendation(
                recommendation_id=f"fix_{gap.program_slug}_{gap.gap_type}",
                recommendation_type=gap.gap_type,
                title=f"Fix {gap.gap_type.replace('_', ' ')} for {gap.program_slug}",
                description=gap.description,
                specific_actions=[gap.recommendation],
                estimated_value_unlocked_usd=gap.estimated_value_unlocked_usd,
                affected_programs=[gap.program_slug],
                qualification_impact=f"Closes {gap.gap_type} gap for {gap.program_slug}",
                confidence="MEDIUM",
                implementation_friction=gap.friction_score,
                implementation_steps=[gap.recommendation],
                timeline_weeks=4,
                cost_estimate_usd=5000,
                net_value_usd=gap.estimated_value_unlocked_usd - 5000,
            )
            recommendations.append(rec)

    # Sort by net value descending
    recommendations.sort(key=lambda r: r.net_value_usd, reverse=True)
    return recommendations
