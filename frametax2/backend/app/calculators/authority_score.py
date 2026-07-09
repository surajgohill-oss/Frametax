"""
authority_score.py

Phase 2 of the CineGlobe Authority & Evidence Engine: the deterministic
Authority Score computed over the Phase 1 Evidence Graph
(evidence_graph.py). No ML, no probabilistic inference beyond the
documented confidence-band mapping already used elsewhere in the
codebase (qualification_model.QualificationConfidence).

Six weighted dimensions, always exposed together as a breakdown — never
a bare composite number:

    Source Strength        30%   — from AuthorityTier (strongest cited)
    Legal Weight            20%   — from BindingForce (strongest cited)
    Jurisdiction Relevance  20%   — direct match vs. cross-jurisdiction
    Recency                 10%   — decayed against a caller-supplied
                                     as_of_date, never wall-clock
    Completeness            10%   — structural: how many independent
                                     evidence items support the rule
    Citation Quality        10%   — pinpoint + quoted text vs. a bare
                                     document reference

Rules enforced structurally:

- "Lower-tier authority cannot override higher-tier authority": when a
  Rule is backed by evidence from multiple AuthoritySources, Source
  Strength and Legal Weight are taken from the STRONGEST source only
  (min tier value) — never averaged down by weaker corroborating
  sources.
- Unresolved conflict (any CONFLICTS_WITH edge on the rule) caps the
  composite at CONFLICT_CAP (60), regardless of how strong the
  underlying sources are.
- A superseded DocumentVersion lowers confidence — SUPERSEDED_PENALTY
  is applied to the composite — unless the caller explicitly requests a
  historical evaluation (include_superseded=True).
- Absence of authority never manufactures confidence: scoring a
  recommendation whose terminus is AbsenceOfAuthority returns a hard
  composite of 0.0, not a computed partial score.

This module does not modify qualification_model.py, optimization_engine.py,
qpe_calculator.py, structuring_paths.py, or any existing calculator
behavior. It reads the Evidence Graph; it does not write to it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.calculators.evidence_graph import (
    AuthoritySource,
    AuthorityTier,
    BindingForce,
    Citation,
    DocumentVersion,
    EvidenceGraph,
    Rule,
)
from app.calculators.qualification_model import QualificationConfidence

AUTHORITY_SCORE_VERSION = "1.0.0"

# ── Weighted dimensions (sum to 1.0) ─────────────────────────────────────────
SOURCE_STRENGTH_WEIGHT = 0.30
LEGAL_WEIGHT_WEIGHT = 0.20
JURISDICTION_RELEVANCE_WEIGHT = 0.20
RECENCY_WEIGHT = 0.10
COMPLETENESS_WEIGHT = 0.10
CITATION_QUALITY_WEIGHT = 0.10

CONFLICT_CAP = 60.0
SUPERSEDED_PENALTY_MULTIPLIER = 0.5

CONFIDENCE_HIGH_THRESHOLD = 75.0
CONFIDENCE_MEDIUM_THRESHOLD = 40.0

# Tier (1..14) -> normalized strength (1..14 maps to 1.0..~0.071), fixed.
TIER_STRENGTH: dict[AuthorityTier, float] = {
    tier: (len(AuthorityTier) - tier.value + 1) / len(AuthorityTier) for tier in AuthorityTier
}

# BindingForce -> normalized legal weight, fixed.
BINDING_FORCE_WEIGHT: dict[BindingForce, float] = {
    BindingForce.BINDING: 1.00,
    BindingForce.BINDING_GENERAL: 0.85,
    BindingForce.PERSUASIVE_STRONG: 0.65,
    BindingForce.PERSUASIVE: 0.50,
    BindingForce.EVIDENTIARY: 0.35,
    BindingForce.INTERPRETIVE: 0.25,
    BindingForce.WEAKEST_DEFENSIBLE: 0.15,
    BindingForce.NOT_AUTHORITY: 0.00,
}


@dataclass
class AuthorityScoreBreakdown:
    """Every score exposes this in full — a composite is never shown alone."""
    source_strength: float
    legal_weight: float
    jurisdiction_relevance: float
    recency: float
    completeness: Optional[float]     # None only for a bare AuthoritySource score
    citation_quality: Optional[float]  # None only for a bare AuthoritySource score
    conflict_capped: bool
    superseded_penalty_applied: bool
    is_absence_of_authority: bool = False
    notes: str = ""


@dataclass
class AuthorityScore:
    composite: float  # 0-100
    confidence: QualificationConfidence
    breakdown: AuthorityScoreBreakdown
    strongest_tier: Optional[AuthorityTier] = None
    jurisdiction_code: Optional[str] = None
    as_of_date: Optional[str] = None


def confidence_band(composite: float) -> QualificationConfidence:
    if composite >= CONFIDENCE_HIGH_THRESHOLD:
        return QualificationConfidence.HIGH
    if composite >= CONFIDENCE_MEDIUM_THRESHOLD:
        return QualificationConfidence.MEDIUM
    return QualificationConfidence.LOW


# ── Dimension helpers (pure functions, deterministic) ───────────────────────

def _jurisdiction_relevance(source_jurisdiction: str, target_jurisdiction: str) -> float:
    return 1.0 if source_jurisdiction == target_jurisdiction else 0.4


def _recency(version: DocumentVersion, as_of_date: Optional[str]) -> float:
    """
    Decayed against a caller-supplied as_of_date — never wall-clock, so
    scoring is fully deterministic and reproducible. Missing dates (on
    either side) return a neutral 0.5 rather than manufacturing either
    full confidence or zero confidence from an absence of information.
    """
    date_str = version.effective_date or version.publication_date
    if not date_str or not as_of_date:
        return 0.5
    try:
        version_year = int(date_str[:4])
        as_of_year = int(as_of_date[:4])
    except (ValueError, TypeError):
        return 0.5
    years_old = max(0, as_of_year - version_year)
    if years_old <= 2:
        return 1.0
    if years_old <= 5:
        return 0.75
    if years_old <= 10:
        return 0.5
    return 0.25


def _citation_quality(citation: Citation) -> float:
    has_pinpoint = bool(citation.pinpoint)
    has_text = bool(citation.citation_text)
    if has_pinpoint and has_text:
        return 1.0
    if has_pinpoint:
        return 0.65
    if has_text:
        return 0.5
    return 0.2


def _completeness(rule: Rule) -> float:
    """Structural proxy: more independent corroborating evidence items
    raise completeness, capped at 1.0. A rule with one evidence item is
    treated as adequately but not maximally complete."""
    return min(1.0, 0.5 + 0.25 * len(rule.evidence_ids))


def _round_breakdown_values(**kwargs) -> dict:
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in kwargs.items()}


# ── Public scoring functions ──────────────────────────────────────────────

def score_authority_source(
    graph: EvidenceGraph,
    source_id: str,
    target_jurisdiction_code: str,
    as_of_date: Optional[str] = None,
    include_superseded: bool = False,
) -> AuthorityScore:
    """
    Score a single AuthoritySource in isolation, without a specific
    citation/evidence context. Completeness and Citation Quality are not
    applicable at this level (there is no citation to judge) — they are
    set to None in the breakdown and the remaining four dimensions
    (Source Strength, Legal Weight, Jurisdiction Relevance, Recency,
    summing to 0.80) are reweighted to fill 100%, not padded with an
    invented value.
    """
    source = graph.get_authority_source(source_id)
    version = graph.get_document_version(source.document_version_id)

    source_strength = TIER_STRENGTH[source.tier]
    legal_weight = BINDING_FORCE_WEIGHT[source.binding_force]
    jurisdiction_relevance = _jurisdiction_relevance(source.jurisdiction_code, target_jurisdiction_code)
    recency = _recency(version, as_of_date)

    applicable_weight = (
        SOURCE_STRENGTH_WEIGHT + LEGAL_WEIGHT_WEIGHT + JURISDICTION_RELEVANCE_WEIGHT + RECENCY_WEIGHT
    )
    composite = 100.0 * (
        SOURCE_STRENGTH_WEIGHT * source_strength
        + LEGAL_WEIGHT_WEIGHT * legal_weight
        + JURISDICTION_RELEVANCE_WEIGHT * jurisdiction_relevance
        + RECENCY_WEIGHT * recency
    ) / applicable_weight

    superseded_penalty_applied = False
    if graph.is_superseded(version.version_id) and not include_superseded:
        composite *= SUPERSEDED_PENALTY_MULTIPLIER
        superseded_penalty_applied = True

    composite = round(min(100.0, max(0.0, composite)), 2)

    breakdown = AuthorityScoreBreakdown(**_round_breakdown_values(
        source_strength=source_strength, legal_weight=legal_weight,
        jurisdiction_relevance=jurisdiction_relevance, recency=recency,
        completeness=None, citation_quality=None,
        conflict_capped=False, superseded_penalty_applied=superseded_penalty_applied,
        notes="Source-level score: no citation context. Completeness and "
              "citation quality are not applicable; remaining four dimensions "
              "reweighted to 100%.",
    ))
    return AuthorityScore(
        composite=composite, confidence=confidence_band(composite), breakdown=breakdown,
        strongest_tier=source.tier, jurisdiction_code=target_jurisdiction_code, as_of_date=as_of_date,
    )


def score_rule(
    graph: EvidenceGraph,
    rule_id: str,
    target_jurisdiction_code: str,
    as_of_date: Optional[str] = None,
    include_superseded: bool = False,
) -> AuthorityScore:
    """
    Score a Rule from its fully-chained evidence. Raises ValueError if
    the rule is not fully chained — an unresolved rule has no authority
    to score; the caller should be scoring an AbsenceOfAuthority via
    score_recommendation() instead. This reuses
    EvidenceGraph.rule_is_fully_chained() rather than re-implementing
    the check.
    """
    if not graph.rule_is_fully_chained(rule_id):
        raise ValueError(
            f"Rule '{rule_id}' is not fully chained to an authority source — "
            "cannot compute an Authority Score for an unresolved rule. "
            "Score the recommendation's AbsenceOfAuthority instead."
        )
    rule = graph.get_rule(rule_id)
    chain = graph.trace_rule(rule_id)

    # "Lower-tier authority cannot override higher-tier authority":
    # source strength and legal weight are taken from the single
    # strongest cited source, never averaged down by weaker ones.
    strongest_item = min(chain, key=lambda item: item["authority_source"].tier.value)
    strongest_source: AuthoritySource = strongest_item["authority_source"]
    source_strength = TIER_STRENGTH[strongest_source.tier]
    legal_weight = BINDING_FORCE_WEIGHT[strongest_source.binding_force]

    jurisdiction_relevance = max(
        _jurisdiction_relevance(item["authority_source"].jurisdiction_code, target_jurisdiction_code)
        for item in chain
    )
    recency = sum(_recency(item["document_version"], as_of_date) for item in chain) / len(chain)
    completeness = _completeness(rule)
    citation_quality = sum(_citation_quality(item["citation"]) for item in chain) / len(chain)

    composite = 100.0 * (
        SOURCE_STRENGTH_WEIGHT * source_strength
        + LEGAL_WEIGHT_WEIGHT * legal_weight
        + JURISDICTION_RELEVANCE_WEIGHT * jurisdiction_relevance
        + RECENCY_WEIGHT * recency
        + COMPLETENESS_WEIGHT * completeness
        + CITATION_QUALITY_WEIGHT * citation_quality
    )

    conflict_capped = bool(graph.conflicts_of(rule_id))
    if conflict_capped and composite > CONFLICT_CAP:
        composite = CONFLICT_CAP

    superseded_penalty_applied = False
    if any(item["superseded"] for item in chain) and not include_superseded:
        composite *= SUPERSEDED_PENALTY_MULTIPLIER
        superseded_penalty_applied = True

    composite = round(min(100.0, max(0.0, composite)), 2)

    breakdown = AuthorityScoreBreakdown(**_round_breakdown_values(
        source_strength=source_strength, legal_weight=legal_weight,
        jurisdiction_relevance=jurisdiction_relevance, recency=recency,
        completeness=completeness, citation_quality=citation_quality,
        conflict_capped=conflict_capped, superseded_penalty_applied=superseded_penalty_applied,
        notes=f"Source strength/legal weight governed by strongest cited tier "
              f"({strongest_source.tier.name}); {len(chain)} evidence item(s) averaged "
              f"for recency/citation quality.",
    ))
    return AuthorityScore(
        composite=composite, confidence=confidence_band(composite), breakdown=breakdown,
        strongest_tier=strongest_source.tier, jurisdiction_code=target_jurisdiction_code, as_of_date=as_of_date,
    )


def score_recommendation(
    graph: EvidenceGraph,
    recommendation_id: str,
    target_jurisdiction_code: str,
    as_of_date: Optional[str] = None,
    include_superseded: bool = False,
) -> AuthorityScore:
    """
    Score a Recommendation via its linked terminus (see
    EvidenceGraph.link_recommendation / trace_recommendation).

    If the terminus is an AbsenceOfAuthority, this NEVER computes a
    partial score from whatever signals happen to exist — it returns a
    hard composite of 0.0 / LOW confidence. Absence of authority must
    never manufacture confidence.
    """
    trace = graph.trace_recommendation(recommendation_id)
    if trace["terminus"] == "absence_of_authority":
        absence = trace["absence"]
        breakdown = AuthorityScoreBreakdown(
            source_strength=0.0, legal_weight=0.0, jurisdiction_relevance=0.0, recency=0.0,
            completeness=None, citation_quality=None,
            conflict_capped=False, superseded_penalty_applied=False,
            is_absence_of_authority=True,
            notes=f"No authority located for: {absence.question} "
                  f"({len(absence.searched_tiers)} tier(s) searched). "
                  "Composite is a hard 0.0 — never computed from partial signals.",
        )
        return AuthorityScore(
            composite=0.0, confidence=QualificationConfidence.LOW, breakdown=breakdown,
            strongest_tier=None, jurisdiction_code=target_jurisdiction_code, as_of_date=as_of_date,
        )
    rule_id = trace["rule"].rule_id
    return score_rule(graph, rule_id, target_jurisdiction_code, as_of_date, include_superseded)
