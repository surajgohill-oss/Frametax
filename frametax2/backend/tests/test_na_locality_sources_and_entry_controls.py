"""NA-RECONCILIATION-24: the recovered locality authorities, the distance mechanism, and the location-entry rules (duplicates, conservation, supersession).

Isolated synthetic fixtures only. Sources (retrieved 2026-10-15): Missouri Association of Counties 'Counties by Classification' (May 2025); Missouri Secretary of State Official Manual 2025-2026 (printed
'Classification:' lines for Cole and Newton); B.C. Reg. 4/99 s.1(2) and s.11 (consolidation current to 2026-10-06); Metro Vancouver member jurisdictions."""
from __future__ import annotations

import math
import uuid

import pytest
from sqlalchemy import select

from app.calculators import locality as loc
from app.calculators.scenario_facts import SCHEDULE_TOTAL_DAYS_FACT, scenario_derived_facts
from tests.isolated_records import create_synthetic_project, isolated_session

MO = "us_mo_motion_media_production_tax_credit"


def _ev(method="PRODUCER_ASSERTED", confidence="STATED"):
    return {"source": "test source", "method": method, "confidence": confidence}


def _bc(eid, rd, muni, days=None, zone=None):
    attrs = {"bc_regional_district": rd, "bc_municipality": muni}
    evid = {"bc_regional_district": _ev(), "bc_municipality": _ev()}
    if zone:
        attrs["bc_zone"], evid["bc_zone"] = zone, _ev()
    return loc.validate_entry({"id": eid, "label": eid, "jurisdiction_code": "CA-BC", "days": days, "attributes": attrs, "evidence": evid})


# ── Missouri: two sources, one gap filled, two conflicts left Unknown ─────────────────────────────────────────────────────────────────────────

def test_cole_county_is_class_1_from_the_official_manual_and_is_not_qualifying():
    r = loc.resolve(loc.LocationEntry("a", "x", "US-MO", county="Cole County"))
    assert r.resolution["county_class"]["value"] == "1" and r.states["mo_county_qualifying"] is False
    assert "Official Manual" in r.resolution["county_class"]["source"] and r.resolution["county_class"]["version"] == "2025-2026"


@pytest.mark.parametrize("county", ["Newton", "Franklin"])
def test_counties_the_sources_disagree_on_stay_unknown_and_say_why(county):
    res = loc.mo_county_resolution(county)
    r = loc.resolve(loc.LocationEntry("a", "x", "US-MO", county=county))
    assert res["status"] == "CONFLICT" and r.states["mo_county_qualifying"] is None and "county_class" in r.unresolved


def test_the_association_list_and_the_official_manual_agree_everywhere_they_overlap_except_the_recorded_conflicts():
    for name, official in loc._MO_OFFICIAL_VERBATIM.items():
        assoc = loc._MO_INDEX.get(loc._norm_county(name))
        assert assoc is None or assoc == official or name in loc.MO_UNRESOLVED_CONFLICTS, name
    assert set(loc.MO_UNRESOLVED_CONFLICTS) == {"Newton", "Franklin"}


# ── British Columbia: B.C. Reg. 4/99 s.11 and the Metro Vancouver membership ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rd,muni,inside,distant", [
    ("Metro Vancouver Regional District", "City of Surrey", True, False), ("Greater Vancouver Regional District", "Burnaby", True, False), (None, "Township of Langley", True, False),
    ("Cariboo Regional District", "Quesnel", False, True), ("Capital Regional District", "Victoria", False, True), ("Squamish-Lillooet Regional District", "Village of Pemberton", False, True),
    ("Fraser Valley Regional District", "City of Abbotsford", False, False), ("Fraser Valley Regional District", "City of Chilliwack", False, False),
    ("Fraser Valley Regional District", "District of Hope", False, False), ("Fraser Valley Regional District", "The Corporation of the District of Kent", False, False),
    ("Fraser Valley Regional District", "Village of Harrison Hot Springs", False, False), ("Fraser Valley Regional District", "District of Mission", False, False),
    ("Squamish-Lillooet Regional District", "District of Squamish", False, False), ("Squamish-Lillooet Regional District", "Resort Municipality of Whistler", False, False),
    ("Squamish-Lillooet Regional District", "Electoral Area D", False, False),
])
def test_bc_distant_location_follows_regulation_section_11(rd, muni, inside, distant):
    c = loc.bc_classification(rd, muni)
    assert c["inside_metro_vancouver"] is inside and c["distant"] is distant


@pytest.mark.parametrize("rd,muni", [("Fraser Valley Regional District", "Electoral Area H"), ("Fraser Valley Regional District", None), ("Cariboo Regional District", None), (None, None)])
def test_bc_locations_the_regulation_cannot_settle_stay_unknown(rd, muni):
    assert loc.bc_classification(rd, muni)["distant"] is None


def test_every_metro_vancouver_member_is_never_distant_and_the_list_matches_the_published_count():
    assert len(loc.BC_METRO_VANCOUVER["members"]) == 23, "21 municipalities, one electoral area and one treaty First Nation"
    for m in loc.BC_METRO_VANCOUVER["members"]:
        c = loc.bc_classification(None, m)
        assert c["inside_metro_vancouver"] is True and c["distant"] is False, m


def test_outside_the_designated_vancouver_area_is_known_outside_metro_vancouver_and_open_inside_it():
    out = loc.resolve(_bc("a", "Cariboo Regional District", "Quesnel"))
    assert out.states["bc_outside_vancouver"] is True and out.states["bc_distant"] is True
    inside = loc.resolve(_bc("b", "Metro Vancouver Regional District", "City of Burnaby"))
    assert inside.states["bc_outside_vancouver"] is None and inside.states["bc_distant"] is False and "bc_zone" in inside.unresolved, "the DVA boundary inside the regional district is not derived"
    stated = loc.resolve(_bc("c", "Metro Vancouver Regional District", "City of Burnaby", zone="regional"))
    assert stated.states["bc_outside_vancouver"] is True, "an explicit sourced zone fills only what the regulation leaves open"
    conflict = loc.resolve(_bc("d", "Cariboo Regional District", "Quesnel", zone="vancouver"))
    assert conflict.states["bc_distant"] is True and "bc_zone_conflict" in conflict.unresolved, "the regulation wins over a conflicting statement"


def test_bc_regional_and_distant_days_from_municipalities_with_a_mixed_unclassified_location():
    entries = [_bc("v", "Metro Vancouver Regional District", "City of Richmond", 10, zone="vancouver"), _bc("q", "Cariboo Regional District", "Quesnel", 20), _bc("a", "Fraser Valley Regional District", "City of Abbotsford", 10)]
    facts = {SCHEDULE_TOTAL_DAYS_FACT: 40.0, **loc.locality_amount_facts(entries)}
    sf = scenario_derived_facts("ca_bc_pstc", "CA-BC", [("CA-BC", 1.0, "principal_photography", "x")], "CA-BC", amount_facts=facts)
    assert sf.amounts["ca_bc_principal_photography_days_outside_vancouver"] == 30.0 and sf.amounts["ca_bc_principal_photography_days_distant_location"] == 20.0
    mixed = entries + [_bc("u", "Fraser Valley Regional District", "Electoral Area H", 0)]
    sf2 = scenario_derived_facts("ca_bc_pstc", "CA-BC", [("CA-BC", 1.0, "principal_photography", "x")], "CA-BC", amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 40.0, **loc.locality_amount_facts(mixed)})
    assert "ca_bc_principal_photography_days_distant_location" not in sf2.amounts, "an unclassified location leaves the distant days Unknown"


# ── distance mechanism: lower bounds from verified reference points only ──────────────────────────────────────────────────────────────────────

def test_great_circle_distance_is_the_haversine_on_the_iugg_mean_sphere():
    assert loc.great_circle_km(0, 0, 1, 0) == pytest.approx(math.radians(1) * 6371.0088, rel=1e-12)
    assert loc.great_circle_km(10, 20, 10, 20) == 0.0
    assert loc.great_circle_km(0, 0, 0, 180) == pytest.approx(math.pi * 6371.0088, rel=1e-12)


def test_no_reference_point_is_used_until_it_is_verified():
    assert all(p["status"] != "VERIFIED" for p in loc.REFERENCE_POINTS.values()), "no coordinate was recovered from a primary source"
    assert loc.distance_lower_bound_km(46.0, -66.0, "nb") is None
    assert loc.distance_lower_bound_km(46.0, -66.0, "ns") is None


def _with_points(monkeypatch, group, points):
    monkeypatch.setattr(loc, "REFERENCE_POINTS", {f"p{i}": {"group": group, "label": "synthetic", "status": "VERIFIED", "lat": a, "lon": b} for i, (a, b) in enumerate(points)})


def _at_km(km):  # a point on the equator km east of (0, 0)
    return math.degrees(km / loc.EARTH_RADIUS_KM)


def _coords(code, attr_group, lon, lat=0.0):
    return loc.validate_entry({"id": "a", "label": "a", "jurisdiction_code": code, "attributes": {"latitude": lat, "longitude": lon},
                               "evidence": {"latitude": _ev("PRODUCER_MEASURED", "MEASURED"), "longitude": _ev("PRODUCER_MEASURED", "MEASURED")}})


@pytest.mark.parametrize("km,b", [(149.999, None), (150.001, True)])
def test_nova_scotia_distant_band_b_needs_a_lower_bound_above_150_km(monkeypatch, km, b):
    _with_points(monkeypatch, "ns", [(0.0, 0.0)])
    r = loc.resolve(_coords("CA-NS", "ns", _at_km(km)))
    assert r.states["ns_zone_b"] is b and (r.states["ns_zone_a"] is False if b else r.states["ns_zone_a"] is None), "a straight line below the boundary does not rule out a longer driving distance"


@pytest.mark.parametrize("km,remote", [(150.999, None), (151.001, True)])
def test_new_brunswick_remote_needs_a_lower_bound_of_151_km_from_the_nearest_of_three_city_halls(monkeypatch, km, remote):
    _with_points(monkeypatch, "nb", [(0.0, 0.0), (0.0, _at_km(400)), (0.0, _at_km(-400))])
    r = loc.resolve(_coords("CA-NB", "nb", _at_km(km)))
    assert r.states["nb_remote"] is remote and (r.states["nb_rural"] is False if remote else r.states["nb_rural"] is None)


@pytest.mark.parametrize("km,state", [(49.999, None), (50.001, True)])
def test_saskatchewan_rural_needs_a_lower_bound_of_50_km_from_both_cities(monkeypatch, km, state):
    _with_points(monkeypatch, "sk", [(0.0, 0.0), (0.0, _at_km(200))])
    r = loc.resolve(_coords("CA-SK", "sk", _at_km(km)))
    assert r.states["sk_rural50"] is state


def test_a_stated_distance_outranks_the_computed_lower_bound(monkeypatch):
    _with_points(monkeypatch, "sk", [(0.0, 0.0)])
    e = loc.validate_entry({"id": "a", "label": "a", "jurisdiction_code": "CA-SK", "attributes": {"latitude": 0.0, "longitude": _at_km(80), "sk_distance_km": 40.0},
                            "evidence": {"latitude": _ev(), "longitude": _ev(), "sk_distance_km": _ev("PRODUCER_MEASURED", "MEASURED")}})
    assert loc.resolve(e).states["sk_rural50"] is False


# ── entry rules: duplicates, conservation, supersession ───────────────────────────────────────────────────────────────────────────────────────

def _mo(eid, label, days, role="SELECTED", county="Boone", city="Columbia"):
    return loc.validate_entry({"id": eid, "label": label, "jurisdiction_code": "US-MO", "role": role, "city": city, "county": county, "days": days})


def test_the_same_place_in_the_same_role_cannot_be_entered_twice():
    with pytest.raises(ValueError, match="counted twice"):
        loc.check_entries([_mo("a", "Set A", 5), _mo("b", "set a", 5)], None)
    loc.check_entries([_mo("a", "Set A", 5), _mo("b", "Set B", 5)], None)            # two sets in one city are two locations
    loc.check_entries([_mo("a", "Set A", 5), _mo("b", "Set A", 5, role="SCHEDULE")], None)  # a plan and the schedule it replaces are different roles


@pytest.mark.parametrize("days,ok", [(19, True), (20, True), (21, False)])
def test_location_days_cannot_exceed_the_shoot_total(days, ok):
    entries = [_mo("a", "Set A", days)]
    if ok:
        loc.check_entries(entries, 20.0)
    else:
        with pytest.raises(ValueError, match="more than the shoot total"):
            loc.check_entries(entries, 20.0)


def test_selected_planning_locations_supersede_the_schedule_of_the_same_jurisdiction_so_days_are_never_double_counted():
    entries = [_mo("s1", "Old set", 10, role="SCHEDULE"), _mo("p1", "New set", 12, role="SELECTED"),
               loc.validate_entry({"id": "s2", "label": "Home set", "jurisdiction_code": "CA-MB", "role": "SCHEDULE", "days": 8})]
    eff = {e.id for e in loc.effective_entries(entries)}
    assert eff == {"p1", "s2"}
    facts = loc.locality_amount_facts(entries)
    assert facts["locality:days:US-MO"] == 12.0 and facts["locality:days:CA-MB"] == 8.0 and facts["locality:days:ALL"] == 20.0
    loc.check_entries(entries, 20.0)                                                        # 12 + 8 = 20, not 30


# ── database: save / failed save / reset / reload ─────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_a_refused_save_leaves_the_persisted_locations_unchanged_and_reset_returns_to_unknown():
    from app.models.production_requirement import ProductionAssumption
    from app.services.shoot_locations import locations_view, write_shoot_locations
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))
        db.add(ProductionAssumption(id=uuid.uuid4(), project_id=project_id, assumption_key="intended_shoot_days", value="20", value_type="number", evidence_state="ACTUAL"))
        await db.flush()
        good = {"id": "a", "label": "Set A", "jurisdiction_code": "US-MO", "city": "Columbia", "county": "Boone", "days": 12}
        await write_shoot_locations(db, project_id, [good])
        view = await locations_view(db, project_id)
        assert view["total_days"] == 20.0 and view["used_days"] == 12 and view["locations"][0]["classifications"]["county_class"]["value"] == "1"
        with pytest.raises(ValueError, match="more than the shoot total"):
            await write_shoot_locations(db, project_id, [{**good, "days": 21}])
        with pytest.raises(ValueError, match="counted twice"):
            await write_shoot_locations(db, project_id, [good, {**good, "id": "b"}])
        again = await locations_view(db, project_id)
        assert [l["days"] for l in again["locations"]] == [12], "a refused save changes nothing"
        # a producer-supplied classification is stored with its provenance and shown apart from the derived county class
        rural = {**good, "attributes": {"rural_or_blighted": True}, "evidence": {"rural_or_blighted": {"source": "DED determination letter", "method": "AUTHORITY_DETERMINATION", "confidence": "AUTHORITATIVE", "version": "2026-09"}}}
        await write_shoot_locations(db, project_id, [rural])
        shown = (await locations_view(db, project_id))["locations"][0]
        assert shown["classifications"]["mo_rural_or_blighted"]["method"] == "AUTHORITY_DETERMINATION" and shown["classifications"]["county_class"]["method"] == "DATASET_LOOKUP"
        # reset: removing the producer classification returns the location to derived evidence / Unknown
        await write_shoot_locations(db, project_id, [good])
        reset = (await locations_view(db, project_id))["locations"][0]
        assert "mo_rural_or_blighted" not in reset["classifications"] and "rural_or_blighted" in reset["unresolved"] and reset["classifications"]["county_class"]["value"] == "1"
        effects = {e["predicate"]: e for e in (await locations_view(db, project_id))["pricing_effects"]}
        assert effects["mo_rural_or_blighted"]["state"] == "UNKNOWN" and effects["mo_county_qualifying"]["state"] == "NOT_MET"
        assert any("+5 points" in x["text"] for x in effects["mo_rural_or_blighted"]["effects"]) and any("+2 points" in x["text"] for x in effects["mo_county_qualifying"]["effects"])
