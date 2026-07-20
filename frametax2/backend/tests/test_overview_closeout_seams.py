"""Focused tests for the Overview-closeout backend seams:

1. Person NAME overrides (all roles) + slot roles (lead_cast_2/3, dop,
   editor, composer) accepted by apply_people_facts and served/merged.
2. Slot-role nationalities merge into the cultural-gate role vocabulary
   (_merge_override_role_codes) — dop/editor/composer 1:1, lead_cast_N
   into lead_cast.
3. Major-location taxonomy: script seeds, user override precedence,
   effective resolution, marine_required coupling, clear-on-None.
Every test restores clean state (reset_fact_answers) so ordering never
leaks between tests or into other suites.
"""
import pytest

from app.demo.little_utopia_state import (
    LOCATION_TAXONOMY,
    apply_location_overrides,
    apply_people_facts,
    current_location_overrides,
    current_people_facts,
    get_state,
    reset_fact_answers,
    _merge_override_role_codes,
)


@pytest.fixture(autouse=True)
def _clean_state():
    reset_fact_answers()
    yield
    reset_fact_answers()


# ── People: names + slot roles ──────────────────────────────────────────────

def test_lead_cast_name_override_flows_into_package():
    apply_people_facts({"lead_cast_name": "Test Actor", "lead_cast_nationality": "GB"})
    s = get_state()
    cast0 = s.package.package.cast[0]
    assert cast0.name == "Test Actor"
    assert cast0.nationality.value == "GB"


def test_slot_role_accepts_name_and_nationality():
    apply_people_facts({"lead_cast_2_name": "Second Lead", "lead_cast_2_nationality": "FR"})
    ov = current_people_facts()
    assert ov["lead_cast_2"]["name"] == "Second Lead"
    assert ov["lead_cast_2"]["nationality"] == "FR"


def test_unknown_role_and_bad_values_rejected():
    with pytest.raises(ValueError):
        apply_people_facts({"gaffer_nationality": "GB"})
    with pytest.raises(ValueError):
        apply_people_facts({"writer_name": "   "})
    with pytest.raises(ValueError):
        apply_people_facts({"dop_nationality": "GBR"})


def test_clearing_all_fields_removes_override():
    apply_people_facts({"editor_name": "Cut Person", "editor_nationality": "IE"})
    apply_people_facts({"editor_name": None, "editor_nationality": None})
    assert "editor" not in current_people_facts()


def test_slot_roles_merge_into_cultural_role_codes():
    apply_people_facts({
        "dop_nationality": "GB",
        "composer_nationality": "FR",
        "lead_cast_2_nationality": "DE",
    })
    merged = _merge_override_role_codes({"lead_cast": ("US",), "director": ("AU",)})
    assert merged["dop"] == ("GB",)
    assert merged["composer"] == ("FR",)
    assert set(merged["lead_cast"]) == {"US", "DE"}
    assert merged["director"] == ("AU",)  # untouched


# ── Major-location taxonomy ─────────────────────────────────────────────────

def test_script_seeds_present_and_effective():
    cats = get_state().physical_requirements["location_categories"]
    assert set(cats) == set(LOCATION_TAXONOMY)
    assert cats["marine_open_water"]["effective"] is True
    assert cats["marine_open_water"]["source"] == "script_analysis"
    assert cats["desert_arid"]["effective"] is False
    assert cats["beach_coast"]["script_value"] is True
    # provenance always served
    assert cats["historic_old_world"]["evidence"]


def test_override_wins_and_script_value_preserved():
    apply_location_overrides({"urban_major_city": True})
    cats = get_state().physical_requirements["location_categories"]
    assert cats["urban_major_city"]["effective"] is True
    assert cats["urban_major_city"]["override"] is True
    assert cats["urban_major_city"]["script_value"] is None  # extraction untouched
    assert cats["urban_major_city"]["source"] == "user_override"


def test_marine_override_flips_marine_required_and_territory_match():
    assert get_state().physical_requirements["marine_required"] is True
    assert get_state().territory_physical_match  # populated when marine required
    apply_location_overrides({"marine_open_water": False})
    s = get_state()
    assert s.physical_requirements["marine_required"] is False
    assert s.territory_physical_match == {}  # optimizer matching recomputed
    apply_location_overrides({"marine_open_water": None})  # clear override
    assert get_state().physical_requirements["marine_required"] is True
    assert current_location_overrides() == {}


def test_unknown_category_rejected():
    with pytest.raises(ValueError):
        apply_location_overrides({"volcano": True})
    with pytest.raises(ValueError):
        apply_location_overrides({"beach_coast": "yes"})
