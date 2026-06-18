"""
evaluate_qualification_tests.py

Deterministic scoring of qualification tests (e.g. UK BFI Cultural Test).
Each criterion is evaluated against production_details — a dict of intake values.
Returns scored results with pass/fail decision and full trace.

No LLM calls. All scoring logic is explicit and testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ENGINE_VERSION = "0.1.0"


@dataclass
class CriterionResult:
    criterion_code: str
    section: str | None
    description: str
    max_points: int
    awarded_points: int
    input_key: str
    input_value: Any
    scoring_rule: str
    passed: bool


@dataclass
class QualificationTestResult:
    test_slug: str
    total_score: int
    total_available: int
    minimum_required: int
    passes_overall: bool
    passes_section_minimums: bool
    section_scores: dict[str, int]
    criterion_results: list[CriterionResult]
    disqualifying_factors: list[str]
    engine_version: str = ENGINE_VERSION


def score_qualification_test(
    test_rules: list[dict],
    production_details: dict[str, Any],
    minimum_pass_points: int,
    section_minimums: dict[str, int] | None = None,
    test_slug: str = "unknown",
    total_available_points: int | None = None,
) -> QualificationTestResult:
    """
    Evaluate a qualification test against production_details.

    test_rules: list of QualificationTestRule-shaped dicts:
        {criterion_code, section, section_name, description, max_points,
         input_type, input_key, threshold_value, scoring_logic}
    production_details: dict of intake values keyed by input_key
    """
    criterion_results: list[CriterionResult] = []
    section_scores: dict[str, int] = {}
    total_score = 0

    for rule in test_rules:
        input_key = rule["input_key"]
        max_pts = int(rule["max_points"])
        section = rule.get("section")
        input_type = rule.get("input_type", "boolean")
        threshold = rule.get("threshold_value")
        raw_value = production_details.get(input_key)

        awarded = _score_criterion(
            input_type=input_type,
            raw_value=raw_value,
            threshold=threshold,
            max_pts=max_pts,
        )

        result = CriterionResult(
            criterion_code=rule["criterion_code"],
            section=section,
            description=rule["description"],
            max_points=max_pts,
            awarded_points=awarded,
            input_key=input_key,
            input_value=raw_value,
            scoring_rule=rule.get("scoring_logic", ""),
            passed=(awarded == max_pts),
        )
        criterion_results.append(result)
        total_score += awarded

        if section:
            section_scores[section] = section_scores.get(section, 0) + awarded

    passes_overall = total_score >= minimum_pass_points

    passes_sections = True
    disqualifying = []
    if section_minimums:
        for sec, min_pts in section_minimums.items():
            if isinstance(sec, str) and "+" in sec:
                # Combined section minimum (e.g. "C+D")
                parts = sec.split("+")
                combined = sum(section_scores.get(p.strip(), 0) for p in parts)
                if combined < min_pts:
                    passes_sections = False
                    disqualifying.append(
                        f"Combined sections {sec} score {combined} < minimum {min_pts}"
                    )
            else:
                score = section_scores.get(sec, 0)
                if score < min_pts:
                    passes_sections = False
                    disqualifying.append(
                        f"Section {sec} score {score} < minimum {min_pts}"
                    )

    if not passes_overall:
        disqualifying.append(
            f"Total score {total_score} < minimum required {minimum_pass_points}"
        )

    return QualificationTestResult(
        test_slug=test_slug,
        total_score=total_score,
        total_available=total_available_points or sum(r["max_points"] for r in test_rules),
        minimum_required=minimum_pass_points,
        passes_overall=passes_overall and passes_sections,
        passes_section_minimums=passes_sections,
        section_scores=section_scores,
        criterion_results=criterion_results,
        disqualifying_factors=disqualifying,
    )


def _score_criterion(
    input_type: str,
    raw_value: Any,
    threshold: float | None,
    max_pts: int,
) -> int:
    """
    Apply the scoring rule for a single criterion.
    Returns awarded points (0 or max_pts — no partial scoring in v0.1).
    """
    if raw_value is None:
        return 0

    if input_type == "boolean":
        return max_pts if bool(raw_value) else 0

    if input_type == "percentage":
        try:
            val = float(raw_value)
            required = float(threshold) if threshold is not None else 0.5
            return max_pts if val >= required else 0
        except (TypeError, ValueError):
            return 0

    if input_type == "count":
        try:
            val = int(raw_value)
            required = int(threshold) if threshold is not None else 1
            return max_pts if val >= required else 0
        except (TypeError, ValueError):
            return 0

    if input_type == "select":
        # threshold_value not used; any non-empty/non-false value scores
        return max_pts if raw_value else 0

    return 0


# ---------------------------------------------------------------------------
# UK BFI Cultural Test helper (hardcoded for validation testbed)
# Used when database rules are not yet loaded
# ---------------------------------------------------------------------------

UK_BFI_RULES_HARDCODED: list[dict] = [
    # Section A — Cultural Content (max 16 pts)
    {"criterion_code": "A1", "section": "A", "section_name": "Cultural Content",
     "description": "Film set in UK", "max_points": 4,
     "input_type": "boolean", "input_key": "uk_setting",
     "threshold_value": None, "scoring_logic": "Set in UK = 4 pts"},
    {"criterion_code": "A2", "section": "A", "section_name": "Cultural Content",
     "description": "Lead characters British citizens or residents", "max_points": 4,
     "input_type": "boolean", "input_key": "lead_characters_british",
     "threshold_value": None, "scoring_logic": "Lead characters British = 4 pts"},
    {"criterion_code": "A3", "section": "A", "section_name": "Cultural Content",
     "description": "Film based on British subject matter or underlying material", "max_points": 4,
     "input_type": "boolean", "input_key": "british_subject_matter",
     "threshold_value": None, "scoring_logic": "British subject matter = 4 pts"},
    {"criterion_code": "A4", "section": "A", "section_name": "Cultural Content",
     "description": "Original dialogue recorded mainly in English/Welsh/Scottish Gaelic/Irish", "max_points": 4,
     "input_type": "boolean", "input_key": "english_language_variant",
     "threshold_value": None, "scoring_logic": "English language variant = 4 pts"},
    # Section B — Cultural Contribution (max 4 pts)
    {"criterion_code": "B1", "section": "B", "section_name": "Cultural Contribution",
     "description": "Film reflects British creativity, heritage, or diversity", "max_points": 4,
     "input_type": "boolean", "input_key": "british_cultural_contribution",
     "threshold_value": None, "scoring_logic": "British cultural contribution = 4 pts"},
    # Section C — Cultural Hubs (max 3 pts)
    {"criterion_code": "C1", "section": "C", "section_name": "Cultural Hubs",
     "description": "At least 50% of principal photography in UK", "max_points": 2,
     "input_type": "percentage", "input_key": "uk_shoot_pct",
     "threshold_value": 0.50, "scoring_logic": ">=50% UK shoot = 2 pts"},
    {"criterion_code": "C2", "section": "C", "section_name": "Cultural Hubs",
     "description": "VFX work performed in UK", "max_points": 1,
     "input_type": "boolean", "input_key": "uk_vfx",
     "threshold_value": None, "scoring_logic": "UK VFX = 1 pt"},
    # Section D — Cultural Practitioners (max 8 pts)
    {"criterion_code": "D1", "section": "D", "section_name": "Cultural Practitioners",
     "description": "Director British national or resident", "max_points": 1,
     "input_type": "boolean", "input_key": "director_british",
     "threshold_value": None, "scoring_logic": "British director = 1 pt"},
    {"criterion_code": "D2", "section": "D", "section_name": "Cultural Practitioners",
     "description": "Writer British national or resident", "max_points": 1,
     "input_type": "boolean", "input_key": "writer_british",
     "threshold_value": None, "scoring_logic": "British writer = 1 pt"},
    {"criterion_code": "D3", "section": "D", "section_name": "Cultural Practitioners",
     "description": "Producer British national or resident", "max_points": 1,
     "input_type": "boolean", "input_key": "producer_british",
     "threshold_value": None, "scoring_logic": "British producer = 1 pt"},
    {"criterion_code": "D4", "section": "D", "section_name": "Cultural Practitioners",
     "description": "Composer British national or resident", "max_points": 1,
     "input_type": "boolean", "input_key": "composer_british",
     "threshold_value": None, "scoring_logic": "British composer = 1 pt"},
    {"criterion_code": "D5", "section": "D", "section_name": "Cultural Practitioners",
     "description": "Lead actor British national or resident", "max_points": 1,
     "input_type": "boolean", "input_key": "lead_actor_british",
     "threshold_value": None, "scoring_logic": "British lead actor = 1 pt"},
    {"criterion_code": "D6", "section": "D", "section_name": "Cultural Practitioners",
     "description": "Second lead actor British national or resident", "max_points": 1,
     "input_type": "boolean", "input_key": "second_lead_british",
     "threshold_value": None, "scoring_logic": "British second lead = 1 pt"},
    {"criterion_code": "D7", "section": "D", "section_name": "Cultural Practitioners",
     "description": "At least 50% of cast days performed by British nationals or residents", "max_points": 1,
     "input_type": "percentage", "input_key": "british_cast_days_pct",
     "threshold_value": 0.50, "scoring_logic": ">=50% British cast days = 1 pt"},
    {"criterion_code": "D8", "section": "D", "section_name": "Cultural Practitioners",
     "description": "At least 50% of crew days performed by British nationals or residents", "max_points": 1,
     "input_type": "percentage", "input_key": "british_crew_days_pct",
     "threshold_value": 0.50, "scoring_logic": ">=50% British crew days = 1 pt"},
]


def score_uk_bfi_cultural_test(production_details: dict[str, Any]) -> QualificationTestResult:
    """Convenience function using hardcoded BFI rules for validation tests."""
    return score_qualification_test(
        test_rules=UK_BFI_RULES_HARDCODED,
        production_details=production_details,
        minimum_pass_points=18,
        section_minimums={"C+D": 4},
        test_slug="uk_bfi_cultural_test",
        total_available_points=31,
    )
