"""
creative_qualification_engine.py

Phase 7 closeout, Part D: the Creative Qualification Engine.

production_recommendation_engine.generate_cultural_recommendations()
(Phase 7D) already turns each individually-failing creative criterion
into a gated Recommendation. What it does not do — and what this module
adds — is answer the combinatorial question a producer actually asks:
"of everything currently unmet, what is the SMALLEST set of changes that
would flip this test from fail to pass, and is there more than one way
to get there?"

This module:

- reuses cultural_test_rules.py's real scoring functions for every
  candidate check. It never reimplements section-minimum or point-
  threshold logic (that logic includes combined-section rules like
  Canadian content's "A+B" key, which is non-trivial to replicate
  correctly) — instead it simulates a candidate set of criteria as
  satisfied in a copy of production_details and calls the SAME score_fn
  cultural_test_rules.py already exposes, then reads its real
  passes_overall / passes_section_minimums fields. Two independent
  implementations of section-minimum logic would be exactly the
  "duplicated model" Phase 7's closeout forbids.
- reuses production_recommendation_engine's creative-vs-non-creative
  classification (is_creative_input_key, CULTURAL_TEST_REGISTRY) rather
  than maintaining a second copy — one source of truth for "what counts
  as a creative attribute" across both modules.
- never constructs a Recommendation object and never touches approval
  gates. QualificationPath is pure analysis: which criteria, not a
  gated instruction to act on them. A caller who wants an actual gated
  Recommendation for a specific criterion still goes through
  production_recommendation_engine.generate_cultural_recommendations() —
  this module does not bypass it, duplicate it, or shortcut its gates.
- never recommends creative-personnel replacement as the only path.
  analyze_creative_qualification_paths() always searches separately for
  a path built ONLY from non-creative-classified criteria (e.g. raising
  a spend percentage) and surfaces it explicitly — even when it costs
  more (a bigger point swing) than a creative path — so "hire someone
  else" is never presented as the sole option when a non-creative
  alternative genuinely exists.
- is bounded and deterministic: path search examines increasing subset
  sizes of the unmet criteria (size 1, then 2, ...) up to
  MAX_PATH_SEARCH_SIZE, stopping at the first size that yields any valid
  path (the "lowest impact" size), and returns every valid path at that
  size — not just one — for "always present alternatives". No
  wall-clock, no randomness; the same test_slug + production_details
  always produces the same paths in the same order.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Optional

from app.calculators.evaluate_qualification_tests import QualificationTestResult
from app.calculators.production_recommendation_engine import (
    CULTURAL_TEST_REGISTRY,
    is_creative_input_key,
)
from app.calculators.qualification_model import QualificationConfidence

CREATIVE_QUALIFICATION_ENGINE_VERSION = "1.0.0"

# Bounding constant for path search — combinations beyond this size are
# never "lowest impact" in any test this codebase models (every
# cultural_test_rules.py test has well under 10 criteria), so searching
# further would only ever be more expensive, never more useful.
MAX_PATH_SEARCH_SIZE = 4


class PathKind:
    CREATIVE_ONLY = "creative_only"
    NON_CREATIVE_ONLY = "non_creative_only"
    MIXED = "mixed"


def _simulate_criteria_satisfied(
    production_details: dict[str, Any],
    rules: list[dict],
    criterion_codes: frozenset[str],
) -> dict[str, Any]:
    """A copy of production_details with exactly the named criteria's
    input_key set to a value that scores full points under
    evaluate_qualification_tests._score_criterion's real comparison rules
    (boolean -> True, percentage/count -> the rule's own threshold_value,
    select -> True) — everything else in production_details is left
    exactly as the caller supplied it. This never asserts what the
    criterion's real-world answer would be; it only asks 'if this were
    satisfied, would the test as a whole pass?'."""
    simulated = dict(production_details)
    for rule in rules:
        if rule["criterion_code"] not in criterion_codes:
            continue
        input_type = rule.get("input_type", "boolean")
        if input_type in ("percentage", "count"):
            simulated[rule["input_key"]] = rule.get("threshold_value")
        else:  # boolean, select, or any future truthy-scored type
            simulated[rule["input_key"]] = True
    return simulated


@dataclass(frozen=True)
class QualificationPath:
    path_id: str
    test_slug: str
    criterion_codes: tuple[str, ...]
    path_kind: str  # PathKind.CREATIVE_ONLY | NON_CREATIVE_ONLY | MIXED
    resulting_score: int
    minimum_required: int
    criteria_count: int
    authority_reference: tuple[str, ...]


@dataclass
class CreativeQualificationAnalysis:
    """
    current qualification status + every viable minimal path to
    qualification, with a creative-only path never presented as the only
    option when a non-creative-only one also exists.
    """
    test_slug: str
    currently_passes: bool
    total_score: int
    minimum_required: int
    missing_criterion_codes: tuple[str, ...]
    lowest_impact_paths: tuple[QualificationPath, ...]
    non_creative_alternative_paths: tuple[QualificationPath, ...]
    confidence: QualificationConfidence

    @property
    def lowest_impact_path(self) -> Optional[QualificationPath]:
        return self.lowest_impact_paths[0] if self.lowest_impact_paths else None

    @property
    def has_non_creative_alternative(self) -> bool:
        return bool(self.non_creative_alternative_paths)

    @property
    def requires_creative_change_only(self) -> bool:
        """True only when EVERY lowest-impact path touches a creative
        criterion AND no non-creative-only path exists at any size —
        i.e. there is genuinely no way to qualify without a creative
        change. Even then, this module never says 'replace the talent':
        it exposes the fact and defers the decision entirely to the
        producer via production_recommendation_engine's gated
        Recommendation objects."""
        if not self.lowest_impact_paths:
            return False
        return (
            all(p.path_kind == PathKind.CREATIVE_ONLY for p in self.lowest_impact_paths)
            and not self.has_non_creative_alternative
        )


def _path_kind(criterion_codes: tuple[str, ...], input_key_by_code: dict[str, str]) -> str:
    creative_flags = [is_creative_input_key(input_key_by_code[code]) for code in criterion_codes]
    if all(creative_flags):
        return PathKind.CREATIVE_ONLY
    if not any(creative_flags):
        return PathKind.NON_CREATIVE_ONLY
    return PathKind.MIXED


def _search_paths(
    test_slug: str,
    rules: list[dict],
    score_fn,
    production_details: dict[str, Any],
    candidate_codes: tuple[str, ...],
    input_key_by_code: dict[str, str],
    max_size: int = MAX_PATH_SEARCH_SIZE,
) -> tuple[QualificationPath, ...]:
    """All valid minimal-size subsets of candidate_codes (drawn only from
    those codes — callers restrict this to all-unmet, or to
    non-creative-unmet-only, as needed) that flip the test to fully
    passing when simulated. Stops at the first size with any hit."""
    found: list[QualificationPath] = []
    for size in range(1, min(max_size, len(candidate_codes)) + 1):
        for combo in itertools.combinations(sorted(candidate_codes), size):
            simulated = _simulate_criteria_satisfied(production_details, rules, frozenset(combo))
            result: QualificationTestResult = score_fn(simulated)
            if result.passes_overall and result.passes_section_minimums:
                found.append(QualificationPath(
                    path_id=f"PATH-{test_slug}-{'-'.join(combo)}",
                    test_slug=test_slug,
                    criterion_codes=combo,
                    path_kind=_path_kind(combo, input_key_by_code),
                    resulting_score=result.total_score,
                    minimum_required=result.minimum_required,
                    criteria_count=len(combo),
                    authority_reference=tuple(f"cultural_test_rules.{test_slug}[{code}]" for code in combo),
                ))
        if found:
            break
    return tuple(sorted(found, key=lambda p: (p.criteria_count, p.resulting_score, p.criterion_codes)))


def analyze_creative_qualification_paths(
    test_slug: str,
    production_details: dict[str, Any],
) -> CreativeQualificationAnalysis:
    """
    Top-level Part D entry point. Requires test_slug to be a real key of
    production_recommendation_engine.CULTURAL_TEST_REGISTRY (raises
    ValueError otherwise — this module never fabricates a test).
    """
    entry = CULTURAL_TEST_REGISTRY.get(test_slug)
    if entry is None:
        raise ValueError(f"'{test_slug}' is not a registered cultural test in CULTURAL_TEST_REGISTRY.")

    rules = entry["rules"]
    score_fn = entry["score_fn"]
    input_key_by_code = {r["criterion_code"]: r["input_key"] for r in rules}

    result: QualificationTestResult = score_fn(production_details)
    unmet = tuple(cr.criterion_code for cr in result.criterion_results if not cr.passed)

    if result.passes_overall and result.passes_section_minimums:
        return CreativeQualificationAnalysis(
            test_slug=test_slug, currently_passes=True, total_score=result.total_score,
            minimum_required=result.minimum_required, missing_criterion_codes=(),
            lowest_impact_paths=(), non_creative_alternative_paths=(),
            confidence=QualificationConfidence.HIGH,
        )

    all_paths = _search_paths(test_slug, rules, score_fn, production_details, unmet, input_key_by_code)
    non_creative_codes = tuple(c for c in unmet if not is_creative_input_key(input_key_by_code[c]))
    non_creative_paths = _search_paths(test_slug, rules, score_fn, production_details, non_creative_codes, input_key_by_code)

    return CreativeQualificationAnalysis(
        test_slug=test_slug,
        currently_passes=False,
        total_score=result.total_score,
        minimum_required=result.minimum_required,
        missing_criterion_codes=unmet,
        lowest_impact_paths=all_paths,
        non_creative_alternative_paths=non_creative_paths,
        confidence=QualificationConfidence.MEDIUM if all_paths else QualificationConfidence.LOW,
    )
