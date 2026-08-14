"""
Script Analyzer SA-1 — targeted tests (Part O).

Covers the deterministic parser, the SA-1 taxonomy, derived facts, the
canonical-state fingerprint and the optimizer handoff contract. These are
pure-function tests against the real parser and the real builders; the
DB-backed persistence path is proven separately by the SA-1 runtime
verification recorded in docs/validation/SCRIPT_ANALYZER_SA1_VERIFICATION.json.
"""
from pathlib import Path

import pytest

from app.ingestion.screenplay_structural_parser import (
    PARSER_VERSION,
    SA1_TAXONOMY,
    TAX_CHARACTER,
    TAX_DAY_NIGHT,
    TAX_EXPLICIT_ANIMAL,
    TAX_EXPLICIT_MINOR,
    TAX_EXPLICIT_VEHICLE,
    TAX_EXPLICIT_WEAPON,
    TAX_INT_EXT,
    TAX_PERIOD_REFERENCE,
    TAX_SCRIPTED_LOCATION,
    parse_structure,
)
from app.services import script_parse_status as sps
from app.services.script_analysis_service import derive_core_facts

FIXTURE = Path(__file__).parent / "fixtures" / "sa1_sample_screenplay.txt"


@pytest.fixture(scope="module")
def text() -> str:
    return FIXTURE.read_text()


@pytest.fixture(scope="module")
def result(text: str):
    return parse_structure(text)


# ── scene parsing ──────────────────────────────────────────────────────────

def test_scene_boundaries_and_sequence(result):
    assert len(result.scenes) == 5
    assert [s.sequence for s in result.scenes] == [1, 2, 3, 4, 5]
    assert [s.source_scene_number for s in result.scenes] == ["1", "2", "3", "4", "5"]


def test_int_ext_normalization_including_the_combined_form(result):
    assert [s.int_ext for s in result.scenes] == ["EXT", "INT", "EXT", "INT_EXT", "EXT"]


def test_time_of_day_normalization_keeps_continuous_explicit(result):
    assert [s.time_of_day for s in result.scenes] == [
        "DAY", "NIGHT", "NIGHT", "CONTINUOUS", "DAWN",
    ]


def test_ambiguous_slugline_stays_unknown_never_guessed():
    r = parse_structure("INT. SOMEWHERE\n\nNo time of day is stated at all.\n")
    assert len(r.scenes) == 1
    assert r.scenes[0].time_of_day == "UNKNOWN"


def test_scripted_location_and_recurrence_key(result):
    locs = [s.location_key for s in result.scenes]
    assert locs[0] == "COASTAL HIGHWAY"
    assert locs[2] == "COASTAL HIGHWAY"          # recurs
    assert len({loc for loc in locs if loc}) == 4  # 4 unique of 5 scenes


def test_scene_hash_is_stable_across_identical_parses(text):
    a = parse_structure(text)
    b = parse_structure(text)
    assert [s.scene_hash for s in a.scenes] == [s.scene_hash for s in b.scenes]
    assert a.input_fingerprint == b.input_fingerprint


# ── page / eighths ─────────────────────────────────────────────────────────

def test_no_layout_is_flagged_approximate_not_silently_treated_as_real(result):
    assert result.page_basis == "APPROXIMATE_NO_LAYOUT"
    assert any("APPROXIMATE" in w for w in result.warnings)


def test_form_feed_layout_is_preferred_over_word_count_estimate():
    body = "INT. ROOM A - DAY\n\nAction.\n" + "\f" + "INT. ROOM B - NIGHT\n\nMore action.\n"
    r = parse_structure(body)
    assert r.page_basis == "LAYOUT_FORM_FEED"
    assert r.page_count == 2
    assert r.scenes[0].page_start == 1
    assert r.scenes[1].page_start == 2


def test_every_scene_gets_at_least_one_eighth(result):
    assert all((s.eighths or 0) >= 1 for s in result.scenes)
    assert result.total_eighths == sum(s.eighths for s in result.scenes)


# ── characters / dialogue ──────────────────────────────────────────────────

def test_character_dialogue_linkage_and_speaking_roles(result):
    by_name = {c.canonical_name: c for c in result.characters}
    assert set(by_name) == {"MARA", "DRIVER", "WAITRESS"}
    assert all(c.is_speaking_role for c in result.characters)
    assert by_name["MARA"].dialogue_block_count == 4
    assert by_name["MARA"].scene_sequences == [1, 2, 5]


def test_contd_cue_resolves_to_the_same_character_not_a_new_one(result):
    names = {c.canonical_name for c in result.characters}
    assert not any("CONT" in n for n in names)


def test_transitions_are_never_treated_as_characters(result):
    names = {c.canonical_name for c in result.characters}
    for bogus in ("FADE IN", "FADE OUT", "CUT TO", "CONTINUED"):
        assert bogus not in names


# ── SA-1 taxonomy ──────────────────────────────────────────────────────────

def test_only_sa1_taxonomy_keys_are_emitted(result):
    keys = {e.taxonomy_key for s in result.scenes for e in s.elements}
    assert keys <= SA1_TAXONOMY


def test_objective_elements_are_captured_with_evidence(result):
    found = {e.taxonomy_key for s in result.scenes for e in s.elements}
    for expected in (TAX_SCRIPTED_LOCATION, TAX_CHARACTER, TAX_INT_EXT, TAX_DAY_NIGHT,
                     TAX_EXPLICIT_VEHICLE, TAX_EXPLICIT_ANIMAL, TAX_EXPLICIT_WEAPON,
                     TAX_EXPLICIT_MINOR, TAX_PERIOD_REFERENCE):
        assert expected in found
    for s in result.scenes:
        for e in s.elements:
            assert e.char_start <= e.char_end
            assert e.evidence_hash


def test_presence_is_recorded_but_scale_is_never_inferred(result):
    """The canonical rule: 'a horse appears' must not become '2 horses for 5 days'."""
    for s in result.scenes:
        for e in s.elements:
            assert e.quantity is None
            assert e.unit is None
            assert e.is_interpretation is False


def test_no_interpreted_capability_leaks_into_sa1(result):
    keys = {e.taxonomy_key for s in result.scenes for e in s.elements}
    for deferred in ("STUNT", "VFX", "CROWD", "CONSTRUCTION", "COMPLEXITY", "SET_BUILD"):
        assert not any(deferred in k for k in keys)


# ── derived facts ──────────────────────────────────────────────────────────

def test_derived_core_facts_are_consistent_with_the_parse(result):
    f = derive_core_facts(result)
    assert f["script_total_scenes"] == 5
    assert f["script_int_scene_count"] == 1
    assert f["script_ext_scene_count"] == 3
    assert f["script_int_ext_scene_count"] == 1
    assert f["script_day_scene_count"] == 1
    assert f["script_night_scene_count"] == 2
    assert f["script_unique_scripted_locations"] == 4
    assert f["script_recurring_scripted_locations"] == 1
    assert f["script_speaking_character_count"] == 3
    assert f["script_has_explicit_vehicle"] is True
    assert f["script_has_explicit_animal"] is True
    assert f["script_has_explicit_weapon"] is True
    assert f["script_has_period_reference"] is True
    assert f["script_page_basis"] == "APPROXIMATE_NO_LAYOUT"


def test_top_character_burden_is_ordered_by_dialogue_load(result):
    f = derive_core_facts(result)
    burden = f["script_top_character_burden"]
    assert burden[0]["character"] == "MARA"
    assert burden == sorted(burden, key=lambda b: b["dialogue_blocks"], reverse=True)


# ── failure handling ───────────────────────────────────────────────────────

def test_script_with_no_headings_reports_a_warning_and_no_fabricated_scenes():
    r = parse_structure("Just prose with no screenplay structure whatsoever.\n")
    assert r.scenes == []
    assert any("No scene headings" in w for w in r.warnings)


def test_parse_status_blockers_never_degrade_into_estimates():
    for status in (sps.SCRIPT_PARSE_FAILED, sps.SCRIPT_PARSE_BLOCKED_SCAN_ONLY,
                   sps.SCRIPT_NOT_PRESENT):
        assert not sps.is_analysis_ready(status)
        assert sps.blocker_for(status)
    assert sps.is_analysis_ready(sps.SCRIPT_PARSED)
    assert sps.blocker_for(sps.SCRIPT_PARSED) is None


def test_parser_version_is_recorded_on_every_result(result):
    assert result.parser_version == PARSER_VERSION


# ── canonical state / handoff contract ─────────────────────────────────────

def test_canonical_state_fingerprint_ignores_as_of_but_tracks_inputs():
    from app.services.canonical_production_state import CanonicalProductionState

    def _mk(**kw):
        base = dict(
            state_version="v", as_of="2026-01-01T00:00:00Z", project_id="p",
            project_name="n", script_document_version_id="dv", screenplay_id="sp",
            parser_version=PARSER_VERSION, script_input_fingerprint="fp",
        )
        base.update(kw)
        return CanonicalProductionState(**base)

    a = _mk()
    b = _mk(as_of="2099-12-31T23:59:59Z")   # only the clock differs
    c = _mk(script_input_fingerprint="DIFFERENT")

    assert a.compute_fingerprint() == b.compute_fingerprint()
    assert a.compute_fingerprint() != c.compute_fingerprint()


def test_handoff_refuses_an_incomplete_state_instead_of_defaulting():
    from app.services.canonical_production_state import (
        BLOCKED_INCOMPLETE_INPUTS,
        CanonicalProductionState,
    )
    from app.services.optimizer_handoff import build_optimizer_input

    state = CanonicalProductionState(
        state_version="v", as_of="t", project_id="p", project_name="n",
        script_document_version_id=None, screenplay_id=None,
        parser_version=None, script_input_fingerprint=None,
        readiness=BLOCKED_INCOMPLETE_INPUTS,
        blockers=["BUDGET_MISSING — no budget document is attached."],
    )
    result = build_optimizer_input(state)
    assert result.accepted is False
    assert result.optimizer_input is None
    assert result.blockers
