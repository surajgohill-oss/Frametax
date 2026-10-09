"""Location-capability + content-gate wiring (2026-10-05). Pure registry tests plus rolled-back project fixtures; no
evaluation is ever executed (evaluate_project is counted, not run)."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.calculators.production_requirements import (
    CHIP_TO_CATEGORY, LOCATION_CAPABILITY_TOKENS, LOCATION_TAXONOMY, derive_production_requirements, location_category_matrix,
)
from app.services import production_fit as pf
from app.services.program_content_gates import (
    ADVISORY, CONFIRMED_MANDATORY, PROJECT_FACT, content_gates_for_program, gate_control_whitelist, gate_effect, gate_fact_key,
    gate_fingerprint_tokens, KIND_SCRIPT_CONTENT_CLEARANCE,
)
from tests.test_production_fit_ranking_and_location_controls import _post, rolled_back_session  # noqa: F401  (fixture)

SA = "sa_film_commission_rebate"


def _reqs(*categories):
    return derive_production_requirements({"location_categories": {c: {"effective": True, "evidence": ["x"]} for c in categories}})


# ── 13 categories ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_all_13_chips_reach_a_canonical_requirement_token_and_none_is_disconnected():
    matrix = location_category_matrix()
    assert [r["chip"] for r in matrix] == list(LOCATION_TAXONOMY) and len(matrix) == 13 == len(CHIP_TO_CATEGORY)
    for r in matrix:
        assert r["changes_effective_requirements"] and r["capability_tokens"], r
        assert set(r["capability_tokens"]) <= LOCATION_CAPABILITY_TOKENS
        assert r["disposition"] in ("CANONICAL_AND_CONSUMED", "CANONICAL_DATA_MISSING")
    # after the 2026-10-06 location census every chip reaches a structured capability field (coverage per cell is census data)
    consumed = {r["chip"] for r in matrix if r["disposition"] == "CANONICAL_AND_CONSUMED"}
    assert consumed == set(LOCATION_TAXONOMY)
    # the four that previously persisted but did nothing are now connected
    for chip in ("jungle_rainforest", "snow_arctic", "small_town_suburban", "studio_stage"):
        assert next(r for r in matrix if r["chip"] == chip)["changes_effective_requirements"]


def test_every_chip_changes_the_fingerprint_inputs_only_when_its_effective_value_changes():
    from app.services.canonical_project_economics import _apply_location_overrides, _TAXONOMY_SLUG_TO_REQUIREMENT_CATEGORY as T

    base = derive_production_requirements({"location_categories": {}})
    for chip in LOCATION_TAXONOMY:
        on = derive_production_requirements({"location_categories": _apply_location_overrides({}, {chip: True})})
        off = derive_production_requirements({"location_categories": _apply_location_overrides({}, {chip: False})})
        assert (on.environments | on.required_capabilities) != (base.environments | base.required_capabilities), chip
        assert (off.environments | off.required_capabilities) == (base.environments | base.required_capabilities), chip
        assert T[chip] == CHIP_TO_CATEGORY[chip]


@pytest.mark.parametrize("chip", list(LOCATION_TAXONOMY))
async def test_each_chip_saves_per_project_and_requests_exactly_one_evaluation(chip, rolled_back_session, monkeypatch):
    from app.services.canonical_project_economics import _location_override_rows, physical_requirement_fingerprint_facts

    session, a, b = rolled_back_session
    calls: list[str] = []
    first = await _post(session, a, {chip: True}, monkeypatch, calls)
    assert first["changed"] and first["evaluation_triggered"] and calls == [str(a.id)]
    assert await physical_requirement_fingerprint_facts(session, a.id)
    again = await _post(session, a, {chip: True}, monkeypatch, calls)
    assert again["evaluation_triggered"] is False and calls == [str(a.id)]
    assert await _location_override_rows(session, b.id) == {} and await physical_requirement_fingerprint_facts(session, b.id) == frozenset()


def test_location_toggles_are_never_jurisdiction_exclusions():
    import inspect
    from app.api.v1 import cineglobe

    src = inspect.getsource(cineglobe.post_project_locations)
    assert "JURISDICTION_PREFERENCE" not in src and "excluded" not in src.lower().replace("never statutory exclusions", "")


# ── hard physical requirements vs soft suitability signals vs missing capability data ───────────────────────────────────
HARD_CHIPS = {"marine_open_water", "desert_arid", "snow_arctic"}


def test_only_the_hard_physical_chips_are_hard_requirements_and_the_rest_are_soft():
    matrix = location_category_matrix()
    assert {r["chip"] for r in matrix if r["suitability_class"] == "HARD"} == HARD_CHIPS
    assert all(r["suitability_class"] == "SOFT" for r in matrix if r["chip"] not in HARD_CHIPS)
    assert all(r["hard_requirement"] == (r["suitability_class"] == "HARD") for r in matrix)


def _with_status(category: str, status: str, *, profile_only: bool = True) -> list[str]:
    from app.calculators import jurisdiction_comparison as jc

    return sorted(c for c in jc.location_census_jurisdictions() if (not profile_only or c in jc.ALL_PROFILES)
                  and jc.location_capability_cells(c)[category].status == status)


def test_urban_rural_and_historic_alone_never_force_an_assessable_jurisdiction_to_unknown():
    for category, chip in (("urban_major_city", "urban"), ("rural_countryside", "rural_countryside"), ("historic_old_world", "historic_old_world")):
        codes = _with_status(category, "UNRESOLVED_NEUTRAL")
        assert codes, category                                         # the census leaves some soft cells unresolved: they stay neutral
        for code in codes:
            status, reasons = pf.classify_jurisdiction_fit(code, _reqs(chip))
            assert status in pf.FIT_CONFIRMED_STATUSES and not any(r.endswith("_NOT_ASSESSABLE") for r in reasons), (code, status, reasons)
    code = _with_status("historic_old_world", "UNRESOLVED_NEUTRAL")[0]
    soft = pf.classify_soft_signals(code, _reqs("historic_old_world"))       # disclosed, non-blocking
    assert soft["unassessed"] == ["historic_architecture"] and not soft["mismatched"]


def test_every_soft_chip_with_missing_data_stays_confirmed_and_never_not_suitable():
    for row in location_category_matrix():
        if row["suitability_class"] == "SOFT":
            for code in ("GR", "AT"):                  # AT is landlocked: coast / island are CONFIRMED soft mismatches
                status, reasons = pf.classify_jurisdiction_fit(code, _reqs(row["category"]))
                assert status in pf.FIT_CONFIRMED_STATUSES and status != pf.FIT_WEAK, (row["chip"], code, status, reasons)


def test_a_confirmed_soft_match_is_disclosed_and_a_confirmed_soft_mismatch_is_disclosed_without_blocking():
    assert pf.classify_soft_signals("GR", _reqs("beach_coast"))["matched"] == ["coastal_environments"]
    assert pf.classify_soft_signals("GR", _reqs("studio"))["matched"] == ["sound_stages"]
    at = pf.classify_soft_signals("AT", _reqs("beach_coast"))
    assert at["mismatched"] == ["coastal_environments"]
    assert pf.classify_jurisdiction_fit("AT", _reqs("beach_coast"))[0] in pf.FIT_CONFIRMED_STATUSES
    unresolved = _with_status("historic_old_world", "UNRESOLVED_NEUTRAL")[0]
    entry = pf.classify_entry_fit({"anchor_jurisdiction": unresolved}, _reqs("urban", "historic_old_world"))
    assert f"{unresolved}:historic_architecture" in entry["production_fit_soft_signals"]["unassessed"]
    assert entry["production_fit_status"] in pf.FIT_CONFIRMED_STATUSES


def test_a_hard_desert_or_snow_requirement_that_the_census_leaves_unresolved_stays_conditional_never_unsuitable():
    for category, chip, token in (("desert_arid", "desert", "DESERT_ENVIRONMENTS"), ("snow_arctic", "snow", "SNOW_ENVIRONMENTS")):
        codes = _with_status(category, "UNRESOLVED_NEUTRAL")
        assert codes, category
        for code in codes:
            assert pf.classify_jurisdiction_fit(code, _reqs(chip)) == (pf.FIT_UNKNOWN, [f"{token}_NOT_ASSESSABLE"])
        # a soft requirement beside it does not change the (hard-driven) status
        assert pf.classify_jurisdiction_fit(codes[0], _reqs(chip, "urban")) == (pf.FIT_UNKNOWN, [f"{token}_NOT_ASSESSABLE"])


def test_marine_open_water_in_a_confirmed_landlocked_jurisdiction_is_not_suitable_and_a_supporting_one_is_fit_confirmed():
    assert pf.classify_jurisdiction_fit("AT", _reqs("marine_open_water")) == (pf.FIT_WEAK, ["MARINE_MISMATCH"])
    status, reasons = pf.classify_jurisdiction_fit("GR", _reqs("marine_open_water"))
    assert status in pf.FIT_CONFIRMED_STATUSES and reasons == []
    # the hard requirement decides even when soft signals are also present
    assert pf.classify_jurisdiction_fit("AT", _reqs("marine_open_water", "urban", "beach_coast"))[0] == pf.FIT_WEAK


def test_no_requirements_on_file_remains_honestly_unconfirmed():
    assert pf.classify_jurisdiction_fit("GR", _reqs()) == (pf.FIT_UNKNOWN, ["NO_REQUIREMENTS_ON_FILE"])
    assert pf.classify_jurisdiction_fit("XX", _reqs("urban"))[0] == pf.FIT_UNKNOWN                          # no profile at all


def test_service_only_routed_components_inherit_no_location_penalty_but_physical_legs_do():
    reqs = _reqs("marine_open_water")
    service = {"anchor_jurisdiction": "GR", "component_allocations": [
        {"component": "principal_production", "jurisdiction_code": "GR"}, {"component": "vfx", "jurisdiction_code": "AT"},
        {"component": "post_vfx_package", "jurisdiction_code": "AT"}]}
    assert pf.classify_entry_fit(service, reqs)["production_fit_status"] in pf.FIT_CONFIRMED_STATUSES
    physical = {"anchor_jurisdiction": "GR", "component_allocations": [{"component": "principal_production", "jurisdiction_code": "AT"}]}
    got = pf.classify_entry_fit(physical, reqs)         # the routed PHYSICAL leg decides
    assert got["production_fit_status"] == pf.FIT_WEAK and got["production_fit_legs"] == ["AT"]


def test_single_jurisdiction_contract_serves_not_suitable_only_for_a_confirmed_mismatch():
    from app.services.program_pricing_crosswalk import build_single_jurisdiction_contract

    ledger = {"jurisdictions": [{"jurisdiction_code": c, "disposition": "EXECUTABLE", "first_exit_stage": "PRICED"} for c in ("GR", "AT", "XX")],
              "rows": [], "programs": []}
    bpj = {c: {"primary_jurisdiction": c, "confirmed_npc_usd": 100.0 + i, "production_fit_status": st, "production_fit_reasons": rs}
           for i, (c, st, rs) in enumerate([("GR", "WORKABLE", []), ("AT", "WEAK", ["MARINE_MISMATCH"]), ("XX", "UNKNOWN", ["CAPABILITY_UNKNOWN"])])}
    got = {r["jurisdiction_code"]: r for r in build_single_jurisdiction_contract(ledger, bpj)}
    assert got["GR"]["category"] == "LEADING_ALTERNATIVE"
    assert got["AT"]["category"] == "NOT_SUITABLE_FOR_THIS_PRODUCTION" and "MARINE_MISMATCH" in got["AT"]["hard_failure_reason"]
    assert got["XX"]["category"] == "CONDITIONAL_ALTERNATIVE" and any("Location fit unconfirmed" in c for c in got["XX"]["missing_conditions"])


def test_contract_serves_the_upside_axis_separately_from_certainty():
    """The Globe/Workspace/Inspector read the unresolved-upside axis (ceiling_status) from the served contract; it is never
    inferred from certainty, so an executable jurisdiction whose floor is confirmed but whose upside needs facts is not
    relabelled wholesale."""
    from app.services.program_pricing_crosswalk import build_single_jurisdiction_contract

    ledger = {"jurisdictions": [{"jurisdiction_code": c, "disposition": "EXECUTABLE", "first_exit_stage": "PRICED"} for c in ("GR", "CZ")],
              "rows": [], "programs": []}
    bpj = {
        "GR": {"primary_jurisdiction": "GR", "confirmed_npc_usd": 100.0, "production_fit_status": "WORKABLE", "production_fit_reasons": [],
               "ceiling_status": "CONDITIONAL", "economics_certainty": "CONDITIONAL"},
        "CZ": {"primary_jurisdiction": "CZ", "confirmed_npc_usd": 101.0, "production_fit_status": "WORKABLE", "production_fit_reasons": [],
               "ceiling_status": "CONFIRMED", "economics_certainty": "CONFIRMED"},
    }
    got = {r["jurisdiction_code"]: r for r in build_single_jurisdiction_contract(ledger, bpj)}
    assert got["GR"]["ceiling_status"] == "CONDITIONAL" and got["CZ"]["ceiling_status"] == "CONFIRMED"
    assert got["GR"]["category"] == "LEADING_ALTERNATIVE"      # category stays the precise structure category


def test_no_requirements_on_file_never_makes_every_executable_jurisdiction_conditional():
    """With no location requirements on file there is nothing to confirm: the precise economic category stands and the basis is
    disclosed, instead of relabelling the whole single-jurisdiction map 'conditional'."""
    from app.services.program_pricing_crosswalk import build_single_jurisdiction_contract

    ledger = {"jurisdictions": [{"jurisdiction_code": c, "disposition": "EXECUTABLE", "first_exit_stage": "PRICED"} for c in ("GR", "AT")],
              "rows": [], "programs": []}
    none = {"production_fit_status": "UNKNOWN", "production_fit_reasons": [], "production_fit_basis": "NO_REQUIREMENTS_ON_FILE"}
    bpj = {c: {"primary_jurisdiction": c, "confirmed_npc_usd": 100.0 + i, **none} for i, c in enumerate(("GR", "AT"))}
    got = {r["jurisdiction_code"]: r for r in build_single_jurisdiction_contract(ledger, bpj)}
    assert got["GR"]["category"] == "LEADING_ALTERNATIVE" and got["AT"]["category"] == "REFERENCE_ALTERNATIVE"
    assert got["GR"]["production_fit_basis"] == "NO_REQUIREMENTS_ON_FILE"
    assert not any("Location fit unconfirmed" in c for r in got.values() for c in r["missing_conditions"])
    # requirements on file but unassessable still reads conditional (needs facts) -- unchanged
    on_file = {"production_fit_status": "UNKNOWN", "production_fit_reasons": ["DESERT_ENVIRONMENTS_NOT_ASSESSABLE"], "production_fit_basis": "REQUIREMENTS_ON_FILE"}
    got = {r["jurisdiction_code"]: r for r in build_single_jurisdiction_contract(
        ledger, {c: {"primary_jurisdiction": c, "confirmed_npc_usd": 100.0, **on_file} for c in ("GR", "AT")})}
    assert got["AT"]["category"] == "CONDITIONAL_ALTERNATIVE"


def test_soft_only_fit_is_never_conditional_and_every_ledger_jurisdiction_stays_visible():
    from app.services.program_pricing_crosswalk import build_single_jurisdiction_contract

    codes = ["GR", "AT", "XX", "SA", "US-TX", "CA-SK"]
    ledger = {"jurisdictions": [{"jurisdiction_code": c, "disposition": "EXECUTABLE" if c in ("GR", "AT", "XX") else "HARD_BLOCK",
                                 "first_exit_stage": "PRICED"} for c in codes], "rows": [], "programs": []}
    reqs = _reqs("urban", "rural_countryside", "historic_old_world")
    bpj = {}
    for i, c in enumerate(("GR", "AT")):
        fit = pf.classify_entry_fit({"anchor_jurisdiction": c}, reqs)
        bpj[c] = {"primary_jurisdiction": c, "confirmed_npc_usd": 100.0 + i, **fit}
    got = {r["jurisdiction_code"]: r for r in build_single_jurisdiction_contract(ledger, bpj)}
    assert set(got) == set(codes)                                                   # nothing is removed
    assert got["GR"]["category"] == "LEADING_ALTERNATIVE" and got["AT"]["category"] != "CONDITIONAL_ALTERNATIVE"
    assert not any("Location fit unconfirmed" in c for r in (got["GR"], got["AT"]) for c in r["missing_conditions"])


def test_complete_contract_applies_location_fit_to_conditional_rows_not_only_executable_winners():
    from app.services.program_pricing_crosswalk import build_single_jurisdiction_contract

    codes = ("CA-SK", "US-TX")
    ledger = {
        "jurisdictions": [
            {"jurisdiction_code": c, "disposition": "NEEDS_FACTS", "first_exit_stage": "PROGRAM_CONDITIONS"}
            for c in codes
        ],
        "rows": [
            {
                "primary_jurisdiction": c, "disposition": "NEEDS_FACTS", "program_slug": "conditional-program",
                "incentive_potential": {}, "blocker_detail": {"unresolved_propositions": []},
            }
            for c in codes
        ],
        "programs": [],
    }
    got = {
        r["jurisdiction_code"]: r
        for r in build_single_jurisdiction_contract(ledger, {}, production_requirements=_reqs("marine_open_water"))
    }
    assert got["CA-SK"]["production_fit_status"] == "WEAK"
    assert got["CA-SK"]["category"] == "NOT_SUITABLE_FOR_THIS_PRODUCTION"
    assert "MARINE_MISMATCH" in got["CA-SK"]["hard_failure_reason"]
    assert got["US-TX"]["production_fit_status"] in pf.FIT_CONFIRMED_STATUSES
    assert got["US-TX"]["category"] == "CONDITIONAL_ALTERNATIVE"


# ── content gates ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_a_confirmation_resolves_the_gate_and_a_refusal_hard_blocks_only_mandatory_gates():
    key = "evidenced_program_fact:" + gate_fact_key(SA, KIND_SCRIPT_CONTENT_CLEARANCE)
    by = lambda facts: {g["kind"]: g for g in content_gates_for_program(SA, facts)}
    assert by({})[KIND_SCRIPT_CONTENT_CLEARANCE]["effect"] == "NEEDS_FACTS"
    assert by({key: "true"})[KIND_SCRIPT_CONTENT_CLEARANCE]["status"] == "CONFIRMED" and by({key: "true"})[KIND_SCRIPT_CONTENT_CLEARANCE]["effect"] == "NONE"
    assert by({key: "refused"})[KIND_SCRIPT_CONTENT_CLEARANCE]["effect"] == "HARD_BLOCK"        # mandatory approval refused
    assert gate_effect(CONFIRMED_MANDATORY, "REFUSED") == "HARD_BLOCK"
    assert gate_effect(PROJECT_FACT, "REFUSED") == "NEEDS_FACTS", "a non-mandatory refusal stays conditional"
    for status in ("NOT_ON_FILE", "REFUSED", "CONFIRMED"):
        assert gate_effect(ADVISORY, status) == "ADVISORY", "advisory censorship / distribution risk never blocks"


def test_only_served_resolvable_gate_keys_are_whitelisted_and_every_key_fits_the_fact_column():
    w = gate_control_whitelist()
    assert len(w) == 113 and gate_fact_key(SA, KIND_SCRIPT_CONTENT_CLEARANCE) in w
    assert "us_tx_miip__arbitrary_confirmed" not in w and "director" not in w
    assert max(len("evidenced_program_fact:" + k) for k in w) <= 100
    assert all(g["resolvable"] for g in w.values())


async def _post_gates(session, project, gates, monkeypatch, counter):
    import app.services.canonical_evaluation as ce
    from app.api.v1.cineglobe import ContentGateResolutions, post_project_content_gates

    async def fake_eval(db, project_id):
        counter.append(str(project_id))
        return {"status": "EVALUATED"}

    monkeypatch.setattr(ce, "evaluate_project", fake_eval)
    return await post_project_content_gates(str(project.id), ContentGateResolutions(gates=gates), session)


async def test_gate_control_persists_per_project_fingerprints_and_evaluates_once(rolled_back_session, monkeypatch):
    from app.models.project_fact import ProjectFact

    session, a, b = rolled_back_session
    calls: list[str] = []
    key = gate_fact_key(SA, KIND_SCRIPT_CONTENT_CLEARANCE)
    first = await _post_gates(session, a, {key: "confirmed"}, monkeypatch, calls)
    assert first["changed"] and first["evaluation_triggered"] and calls == [str(a.id)]
    assert first["recorded"] == [f"content_gate_confirmed:{key}"]
    rows = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == a.id))).scalars().all()
    assert [(r.fact_key, r.value) for r in rows] == [(f"evidenced_program_fact:{key}", "true")]
    again = await _post_gates(session, a, {key: "confirmed"}, monkeypatch, calls)
    assert again["evaluation_triggered"] is False and calls == [str(a.id)], "identical save requests no evaluation"
    refused = await _post_gates(session, a, {key: "refused"}, monkeypatch, calls)
    assert refused["evaluation_triggered"] and calls == [str(a.id)] * 2 and refused["recorded"] == [f"content_gate_refused:{key}"]
    cleared = await _post_gates(session, a, {key: "not_on_file"}, monkeypatch, calls)
    assert cleared["evaluation_triggered"] and cleared["recorded"] == []
    other = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == b.id))).scalars().all()
    assert other == [], "another project is untouched"


async def test_gate_control_rejects_arbitrary_fact_keys_and_bad_values(rolled_back_session, monkeypatch):
    from fastapi import HTTPException
    from app.models.project_fact import ProjectFact

    session, a, _b = rolled_back_session
    for bad in ({"director": "confirmed"}, {"us_tx_miip_award_confirmed": "confirmed"}, {"evidenced_program_fact:x": "confirmed"}):
        with pytest.raises(HTTPException) as exc:
            await _post_gates(session, a, bad, monkeypatch, [])
        assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        await _post_gates(session, a, {gate_fact_key(SA, KIND_SCRIPT_CONTENT_CLEARANCE): "maybe"}, monkeypatch, [])
    assert exc.value.status_code == 422
    assert (await session.execute(select(ProjectFact).where(ProjectFact.project_id == a.id))).scalars().all() == []


def test_gate_tokens_cover_confirmed_and_refused_only():
    from types import SimpleNamespace as N

    rows = [N(fact_key="evidenced_program_fact:p__x_confirmed", value="true"), N(fact_key="evidenced_program_fact:q__y_confirmed", value="refused"),
            N(fact_key="evidenced_program_fact:us_tx_miip_award_confirmed", value="true"), N(fact_key="director", value="x")]
    assert gate_fingerprint_tokens(rows) == {"content_gate_confirmed:p__x_confirmed", "content_gate_refused:q__y_confirmed"}


def test_period_is_a_script_signal_not_a_location_capability_and_never_affects_fit():
    assert "period_environments" not in LOCATION_CAPABILITY_TOKENS
    r = derive_production_requirements({"script_requirements": {"period": {"value": True, "evidence": "p"}}})
    assert "period_environments" in r.environments
    assert pf.classify_jurisdiction_fit("GR", r) == (pf.FIT_UNKNOWN, ["NO_REQUIREMENTS_ON_FILE"]) or pf.classify_jurisdiction_fit("GR", r)[0] in pf.FIT_CONFIRMED_STATUSES


def test_clearing_a_chip_also_clears_the_script_derived_alias_that_feeds_the_same_requirement():
    """Little Utopia regression: the script derived `mediterranean` (a category with no chip) which also requires
    coastal_environments, so clearing Beach / Coast changed nothing. The cleared chip now removes its aliases too."""
    from app.services.canonical_project_economics import _apply_location_overrides

    derived = {"beach_coast": {"effective": True, "evidence": ["x"]}, "mediterranean": {"effective": True, "evidence": ["y"]},
               "island": {"effective": True, "evidence": ["z"]}}
    before = derive_production_requirements({"location_categories": derived})
    assert "coastal_environments" in before.environments and "island_environments" in before.environments
    after = derive_production_requirements({"location_categories": _apply_location_overrides(derived, {"beach_coast": False})})
    assert "coastal_environments" not in after.environments, "clearing Beach / Coast must remove the coastal requirement"
    assert "island_environments" in after.environments, "an unrelated alias is untouched"
    after2 = derive_production_requirements({"location_categories": _apply_location_overrides(derived, {"island_tropical": False})})
    assert "island_environments" not in after2.environments and "coastal_environments" in after2.environments
    # setting a chip ON never clears anything
    on = derive_production_requirements({"location_categories": _apply_location_overrides(derived, {"beach_coast": True})})
    assert on.environments == before.environments
