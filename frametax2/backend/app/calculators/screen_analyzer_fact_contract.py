"""
screen_analyzer_fact_contract.py

Proactive Opportunity Discovery Reconciliation — Task 7. Screen Analyzer
itself is NOT built in this phase. This module is the structured INPUT
CONTRACT the canonical opportunity-discovery layer (canonical_opportunity_
bridge.py) already needs from it, expressed as fact_key names against the
EXISTING, generic ProjectFact model (app/models/project_fact.py — one
current row per (project_id, fact_key), already extensible key/value,
already carrying source_type/confidence/review_status provenance). No new
table, no new column, no migration: a future Screen Analyzer phase writes
ProjectFact rows under these keys; the opportunity-discovery functions
that already declare a script-derived fact requirement (see
discover_cultural_test_gap_opportunity's required_facts) read directly
from this registry so there is exactly one source of truth for "what does
the optimizer actually need from a script."

Scope discipline: only fact_keys that an EXISTING opportunity/optimizer
consumer already needs are listed here. This is not a speculative full
script-ontology schema — see the Task 7 instruction ("do not overbuild the
schema; only add facts the existing optimizer/opportunity logic actually
consumes or clearly requires").
"""
from __future__ import annotations

from dataclasses import dataclass

SCREEN_ANALYZER_FACT_CONTRACT_VERSION = "1.0.0"


@dataclass(frozen=True)
class ScreenAnalyzerFactSpec:
    fact_key: str
    description: str
    #: Which existing opportunity-discovery function(s) this fact feeds.
    consumed_by: tuple[str, ...]


#: Every entry here maps 1:1 to a real gap already disclosed by an
#: EXISTING discovery function (never a fact nothing currently consumes).
SCREEN_ANALYZER_FACT_CONTRACT: tuple[ScreenAnalyzerFactSpec, ...] = (
    ScreenAnalyzerFactSpec(
        fact_key="script_writer_director_cast_nationality",
        description="Writer/director/producer/cast nationality or residency, as scripted/cast — feeds cultural-test point scoring.",
        consumed_by=("discover_cultural_test_gap_opportunity",),
    ),
    ScreenAnalyzerFactSpec(
        fact_key="script_story_setting_subject",
        description="Story setting and subject matter (where/what the narrative is about) — feeds cultural-test point scoring.",
        consumed_by=("discover_cultural_test_gap_opportunity",),
    ),
    ScreenAnalyzerFactSpec(
        fact_key="script_shooting_locations",
        description="Scripted shooting location(s) (interior/exterior, geography) — feeds cultural-test point scoring and territoriality facts.",
        consumed_by=("discover_cultural_test_gap_opportunity",),
    ),
    ScreenAnalyzerFactSpec(
        fact_key="script_production_language",
        description="Language of production — feeds cultural-test point scoring.",
        consumed_by=("discover_cultural_test_gap_opportunity",),
    ),
    ScreenAnalyzerFactSpec(
        fact_key="script_post_production_activity_location",
        description="Where post-production activity (edit/VFX/sound/music) actually occurs — feeds cultural-test point scoring and component-relocation levers.",
        consumed_by=("discover_cultural_test_gap_opportunity", "discover_qualification_lever_opportunities"),
    ),
    ScreenAnalyzerFactSpec(
        fact_key="script_vfx_animation_practical_effects_scope",
        description="VFX/animation/practical-effects scope implied by the script — feeds qualification levers for movable post/vfx components.",
        consumed_by=("discover_qualification_lever_opportunities",),
    ),
    ScreenAnalyzerFactSpec(
        fact_key="script_coproduction_cultural_contribution",
        description="Story/cultural elements relevant to a treaty co-production's own cultural-contribution requirement.",
        consumed_by=("discover_cultural_test_gap_opportunity",),
    ),
)


def required_fact_descriptions(*, consumer: str | None = None) -> tuple[str, ...]:
    """Human-readable required_facts strings for a discovery function,
    filtered by `consumed_by` when `consumer` is given. Fail-closed by
    construction: if a fact_key is not listed here, no discovery function
    may claim it as a requirement."""
    specs = SCREEN_ANALYZER_FACT_CONTRACT
    if consumer is not None:
        specs = tuple(s for s in specs if consumer in s.consumed_by)
    return tuple(s.description for s in specs)
