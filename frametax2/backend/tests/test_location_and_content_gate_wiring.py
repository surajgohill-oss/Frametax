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
    consumed = {r["chip"] for r in matrix if r["disposition"] == "CANONICAL_AND_CONSUMED"}
    assert consumed == {"beach_coast", "marine_open_water", "studio_stage"}
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


# ── distinct served fit statuses ────────────────────────────────────────────────────────────────────────────────────
def test_confirmed_match_unknown_data_and_confirmed_mismatch_are_three_distinct_statuses():
    assert pf.classify_jurisdiction_fit("GR", _reqs("beach_coast"))[0] in pf.FIT_CONFIRMED_STATUSES        # confirmed match
    status, reasons = pf.classify_jurisdiction_fit("GR", _reqs("desert"))                                    # no structured data
    assert status == pf.FIT_UNKNOWN and reasons == ["DESERT_ENVIRONMENTS_NOT_ASSESSABLE"]
    status, reasons = pf.classify_jurisdiction_fit("AT", _reqs("beach_coast"))                               # landlocked: mismatch
    assert status == pf.FIT_WEAK and reasons == ["MARINE_MISMATCH"]
    assert pf.classify_jurisdiction_fit("XX", _reqs("beach_coast"))[0] == pf.FIT_UNKNOWN                    # no profile at all


def test_missing_capability_data_is_never_unsuitable_for_any_data_missing_chip():
    for row in location_category_matrix():
        if row["disposition"] == "CANONICAL_DATA_MISSING":
            status, reasons = pf.classify_jurisdiction_fit("GR", _reqs(row["category"]))
            assert status == pf.FIT_UNKNOWN and reasons == [f"{row['capability_tokens'][0].upper()}_NOT_ASSESSABLE"], row["chip"]


def test_service_only_routed_components_inherit_no_location_penalty_but_physical_legs_do():
    reqs = _reqs("beach_coast")
    service = {"anchor_jurisdiction": "GR", "component_allocations": [
        {"component": "principal_production", "jurisdiction_code": "GR"}, {"component": "vfx", "jurisdiction_code": "AT"},
        {"component": "post_vfx_package", "jurisdiction_code": "AT"}]}
    assert pf.classify_entry_fit(service, reqs)["production_fit_status"] in pf.FIT_CONFIRMED_STATUSES
    physical = {"anchor_jurisdiction": "GR", "component_allocations": [{"component": "principal_production", "jurisdiction_code": "AT"}]}
    assert pf.classify_entry_fit(physical, reqs)["production_fit_status"] == pf.FIT_WEAK


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
