"""Production-fit ranking + project-scoped location-control wiring (2026-10-01).

Independent expected-value tests: per-jurisdiction fit is injected (never read from capability
data) so every expectation is stated by the test, not derived from the code under test.
Persistence tests run inside a rolled-back transaction on throwaway projects: no real project
is touched and no evaluation is executed (evaluate_project is counted, not run)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.production_requirements import derive_production_requirements
from app.services import production_fit as pf
from app.services.canonical_production_view import (
    REC_STATUS_EVALUATED_ALTERNATIVE, REC_STATUS_RECOMMENDED, _annotate_optimizer_scenario,
)
from tests.test_canonical_production_view import _projection_candidate

BASELINE_NPC = 1_000_000.0
MARINE_REQS = derive_production_requirements(
    {"location_categories": {"marine_open_water": {"effective": True, "evidence": ["BOAT"]}}}
)
NO_REQS = derive_production_requirements({})


@pytest.fixture
def fake_fit(monkeypatch):
    """Per-jurisdiction fit stated by the test."""
    table: dict[str, tuple[str, list[str]]] = {}
    monkeypatch.setattr(pf, "classify_jurisdiction_fit", lambda code, reqs: table.get(code, (pf.FIT_UNKNOWN, [])))
    return table


def _scenario(identifier, *, npc, anchor="GR", routed="CA-MB", component="post_vfx_package", **extra):
    entry = _projection_candidate(
        identifier, npc=npc, participants=[anchor, routed],
        marginal_jurisdiction_benefits_usd={routed: 250_000.0}, **extra,
    )
    entry["anchor_jurisdiction"] = anchor
    entry["component_allocations"] = [{"component": component, "jurisdiction_code": routed}]
    return entry


def _classify_and_annotate(entry, reqs=MARINE_REQS, cache=None):
    entry.update(pf.classify_entry_fit(entry, reqs, cache if cache is not None else {}))
    out = _annotate_optimizer_scenario(entry, BASELINE_NPC, {}, {})
    out["fit_priority"] = pf.fit_priority(out)
    out["fit_aware_category"] = pf.fit_aware_category(out)
    return out


# ── ranking / category ──────────────────────────────────────────────────────────────────────

def test_lower_npc_weak_candidate_cannot_beat_fit_confirmed_candidate(fake_fit):
    fake_fit.update({"GR": (pf.FIT_STRONG, []), "CA-MB": (pf.FIT_WEAK, ["MARINE_MISMATCH"]), "ES": (pf.FIT_WORKABLE, [])})
    # weak candidate physically shoots in CA-MB (principal production routed) and is CHEAPER
    weak = _scenario("weak", npc=600_000.0, component="principal_production")
    confirmed = _scenario("ok", npc=800_000.0, routed="ES", component="principal_production")
    w, c = _classify_and_annotate(weak), _classify_and_annotate(confirmed)
    assert w["production_fit_status"] == pf.FIT_WEAK and c["production_fit_status"] == pf.FIT_WORKABLE
    assert c["recommendation_status"] == REC_STATUS_RECOMMENDED and c["fit_priority"] == pf.PRIORITY_RECOMMENDED
    assert w["recommendation_status"] == REC_STATUS_EVALUATED_ALTERNATIVE
    assert w["recommendation_reason"] == "LOCATION_FIT_WEAK"
    assert w["is_recommended"] is False
    ordered = sorted([w, c], key=lambda e: e["fit_priority"])
    assert [e["structure_id"] for e in ordered] == ["ok", "weak"]


def test_unknown_fit_stays_visible_with_real_economics_and_review_label(fake_fit):
    fake_fit.update({"GR": (pf.FIT_UNKNOWN, ["CAPABILITY_UNKNOWN"])})
    unk = _classify_and_annotate(_scenario("unk", npc=600_000.0, routed="XX", component="post"))
    assert unk["production_fit_status"] == pf.FIT_UNKNOWN
    assert unk["recommendation_status"] == REC_STATUS_EVALUATED_ALTERNATIVE
    assert unk["recommendation_reason"] == "LOCATION_FIT_UNCONFIRMED"
    assert unk["canonical_recommendation_status"] == REC_STATUS_RECOMMENDED  # financial verdict auditable
    assert unk["npc_with_adjustments_usd"] == 600_000.0 and unk["savings_vs_current_usd"] == 400_000.0
    assert unk["fit_priority"] == pf.PRIORITY_UNCONFIRMED and unk["fit_aware_category"] == pf.CAT_FIT_UNCONFIRMED


def test_weak_fit_stays_visible_as_low_location_fit_reference(fake_fit):
    fake_fit.update({"CA-MB": (pf.FIT_WEAK, ["MARINE_MISMATCH"])})
    weak = _classify_and_annotate(_scenario("weak", npc=500_000.0, component="principal_production"))
    assert weak["fit_priority"] == pf.PRIORITY_WEAK and weak["fit_aware_category"] == pf.CAT_LOW_FIT_REFERENCE
    assert weak["npc_with_adjustments_usd"] == 500_000.0 and weak["is_fully_priced"] is True


def test_legal_rejection_stays_unavailable_and_is_never_a_fit_issue(fake_fit):
    fake_fit.update({"GR": (pf.FIT_STRONG, [])})
    rejected = _scenario("rej", npc=500_000.0)
    rejected.update({"is_fully_priced": False, "candidate_status": "RULE_REJECTED"})
    rejected.update(pf.classify_entry_fit(rejected, MARINE_REQS, {}))
    assert pf.fit_priority(rejected) == pf.PRIORITY_UNAVAILABLE
    assert pf.fit_aware_category(rejected) == pf.CAT_UNAVAILABLE
    assert rejected["candidate_status"] == "RULE_REJECTED"  # fit never rewrites legal status


def test_weak_fit_never_converts_a_priced_scenario_into_a_legal_rejection(fake_fit):
    fake_fit.update({"GR": (pf.FIT_WEAK, ["MARINE_MISMATCH"])})
    e = _classify_and_annotate(_scenario("w", npc=500_000.0, component="principal_production", routed="GR"))
    assert e["is_fully_priced"] is True and e["candidate_status"] == "PRICED"
    assert e["fit_priority"] != pf.PRIORITY_UNAVAILABLE


# ── physical legs ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("component", ["post_vfx_package", "music_package", "post", "vfx", "music", "animation"])
def test_service_only_routing_creates_no_filming_location_penalty(fake_fit, component):
    fake_fit.update({"GR": (pf.FIT_STRONG, []), "CA-MB": (pf.FIT_WEAK, ["MARINE_MISMATCH"])})
    e = _scenario("svc", npc=700_000.0, component=component)
    fit = pf.classify_entry_fit(e, MARINE_REQS, {})
    assert fit["production_fit_legs"] == ["GR"]
    assert fit["production_fit_status"] == pf.FIT_STRONG


def test_hybrid_uses_its_actual_physical_production_legs(fake_fit):
    fake_fit.update({"GR": (pf.FIT_STRONG, []), "CA-MB": (pf.FIT_WEAK, ["MARINE_MISMATCH"]), "ES": (pf.FIT_WORKABLE, [])})
    e = _scenario("h", npc=700_000.0, component="principal_production")
    # principal production routed to CA-MB: the shoot is there, the anchor no longer hosts it
    assert pf.classify_entry_fit(e, MARINE_REQS, {})["production_fit_legs"] == ["CA-MB"]
    assert pf.classify_entry_fit(e, MARINE_REQS, {})["production_fit_status"] == pf.FIT_WEAK
    # mixed: physical leg + service leg -> only the physical leg counts, worst-of among physical legs
    e["component_allocations"] = [
        {"component": "principal_production", "jurisdiction_code": "ES"},
        {"component": "post_vfx_package", "jurisdiction_code": "CA-MB"},
    ]
    fit = pf.classify_entry_fit(e, MARINE_REQS, {})
    assert fit["production_fit_legs"] == ["ES"] and fit["production_fit_status"] == pf.FIT_WORKABLE
    # two physical legs: the worse one governs
    e["component_allocations"].append({"component": "principal_production", "jurisdiction_code": "CA-MB"})
    assert pf.classify_entry_fit(e, MARINE_REQS, {})["production_fit_status"] == pf.FIT_WEAK


def test_non_component_structures_use_segments_with_allocated_spend(fake_fit):
    fake_fit.update({"FR": (pf.FIT_STRONG, []), "DE": (pf.FIT_WEAK, [])})
    e = {"participants": ["FR", "DE"], "primary_jurisdiction": "FR", "segments": [
        {"jurisdiction_code": "FR", "allocated_usd": 900_000.0}, {"jurisdiction_code": "DE", "allocated_usd": 0.0}]}
    assert pf.physical_production_legs(e) == ["FR"]


def test_empty_requirement_set_does_not_manufacture_a_fit_claim():
    status, reasons = pf.classify_jurisdiction_fit("GR", NO_REQS)
    assert status == pf.FIT_UNKNOWN and reasons == ["NO_REQUIREMENTS_ON_FILE"]
    assert pf.requirements_disclosed(NO_REQS) is False and pf.requirements_disclosed(MARINE_REQS) is True


def test_hard_requirement_the_capability_data_cannot_assess_is_unconfirmed_not_weak():
    desert = derive_production_requirements({"location_categories": {"desert": {"effective": True, "evidence": ["DUNES"]}}})
    assert "desert_environments" in desert.required_capabilities
    status, reasons = pf.classify_jurisdiction_fit("GR", desert)
    assert status == pf.FIT_UNKNOWN and reasons == ["DESERT_ENVIRONMENTS_NOT_ASSESSABLE"]
    # an assessable marine requirement is still judged affirmatively
    assert pf.classify_jurisdiction_fit("GR", MARINE_REQS)[0] in (pf.FIT_STRONG, pf.FIT_WORKABLE, pf.FIT_WEAK)


# ── coverage and rank ───────────────────────────────────────────────────────────────────────

def test_every_economic_scenario_remains_and_financial_order_is_still_reconstructible(fake_fit):
    fake_fit.update({"GR": (pf.FIT_STRONG, []), "CA-MB": (pf.FIT_WEAK, []), "ES": (pf.FIT_WORKABLE, []), "IT": (pf.FIT_UNKNOWN, [])})
    scenarios = [
        _classify_and_annotate(_scenario("a", npc=500_000.0, component="principal_production")),               # weak, cheapest
        _classify_and_annotate(_scenario("b", npc=900_000.0, routed="ES", component="principal_production")),  # confirmed rec
        _classify_and_annotate(_scenario("c", npc=1_200_000.0, routed="ES", component="principal_production")),  # confirmed, costs more
        _classify_and_annotate(_scenario("d", npc=650_000.0, routed="IT", component="principal_production")),  # unknown
    ]
    ordered = sorted(scenarios, key=lambda e: e["fit_priority"])
    assert len(ordered) == len(scenarios) == 4
    assert [e["structure_id"] for e in ordered] == ["b", "c", "d", "a"]  # rec, confirmed ref, unconfirmed, weak
    assert [e["fit_priority"] for e in ordered] == [1, 2, 3, 4]
    # canonical financial order untouched / separately reconstructible from the served NPC
    assert [e["structure_id"] for e in sorted(scenarios, key=lambda e: e["npc_with_adjustments_usd"])] == ["a", "d", "b", "c"]
    summary = pf.fit_summary(scenarios, unavailable_total=7)
    assert summary == {
        "fit_confirmed": 2, "fit_confirmed_leading_or_strong": 1, "fit_confirmed_reference": 1,
        "fit_unconfirmed": 1, "weak_fit": 1, "unavailable": 7, "scenario_total": 4,
    }


def test_costs_more_scenario_is_preserved_with_fit_confirmed_priority(fake_fit):
    fake_fit.update({"GR": (pf.FIT_STRONG, []), "ES": (pf.FIT_STRONG, [])})
    e = _classify_and_annotate(_scenario("dear", npc=1_300_000.0, routed="ES", component="principal_production"))
    assert e["recommendation_status"] == "COSTS_MORE" and e["fit_priority"] == pf.PRIORITY_CONFIRMED_REFERENCE


def test_unclassified_entries_are_not_gated_so_legacy_callers_are_unchanged():
    e = _projection_candidate("legacy", npc=600_000.0, marginal_jurisdiction_benefits_usd={"CA-MB": 250_000.0})
    assert _annotate_optimizer_scenario(e, BASELINE_NPC, {}, {})["recommendation_status"] == REC_STATUS_RECOMMENDED


# ── location controls: project-scoped persistence, fingerprint, one evaluation ──────────────

@pytest.fixture
async def rolled_back_session():
    from app.db.session import engine
    from app.models.project import Project

    try:
        conn = await engine.connect()
    except Exception as exc:  # pragma: no cover - no database available
        pytest.skip(f"database unavailable: {exc}")
    trans = await conn.begin()
    session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        org_id = (await session.execute(select(Project.organization_id).limit(1))).scalar_one()
        a = Project(id=uuid.uuid4(), organization_id=org_id, title="fit-test-A")
        b = Project(id=uuid.uuid4(), organization_id=org_id, title="fit-test-B")
        session.add_all([a, b])
        await session.flush()
        yield session, a, b
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()


async def _post(session, project, overrides, monkeypatch, counter):
    import app.services.canonical_evaluation as ce
    from app.api.v1.cineglobe import LocationOverrides, post_project_locations

    async def fake_eval(db, project_id):
        counter.append(str(project_id))
        return {"status": "EVALUATED"}

    monkeypatch.setattr(ce, "evaluate_project", fake_eval)
    return await post_project_locations(str(project.id), LocationOverrides(overrides=overrides), session)


async def test_project_scoped_change_persists_changes_fingerprint_and_evaluates_once(rolled_back_session, monkeypatch):
    from app.services.canonical_evaluation import _compute_fingerprint
    from app.services.canonical_project_economics import physical_requirement_fingerprint_facts
    from tests.test_cache_fingerprint_expansion import _inputs

    session, a, b = rolled_back_session
    calls: list[str] = []
    before = await physical_requirement_fingerprint_facts(session, a.id)
    fp_before = _compute_fingerprint(_inputs(evidenced_program_facts=before))

    first = await _post(session, a, {"marine_open_water": True}, monkeypatch, calls)
    assert first["changed"] is True and first["evaluation_triggered"] is True and calls == [str(a.id)]
    assert first["location_categories"]["marine_open_water"]["effective"] is True

    after = await physical_requirement_fingerprint_facts(session, a.id)
    assert after and after != before
    assert _compute_fingerprint(_inputs(evidenced_program_facts=after)) != fp_before

    # unchanged save: persisted state identical -> no duplicate evaluation
    again = await _post(session, a, {"marine_open_water": True}, monkeypatch, calls)
    assert again["changed"] is False and again["evaluation_triggered"] is False
    assert calls == [str(a.id)]


async def test_one_projects_location_change_cannot_affect_another(rolled_back_session, monkeypatch):
    from app.services.canonical_project_economics import _location_override_rows, physical_requirement_fingerprint_facts

    session, a, b = rolled_back_session
    calls: list[str] = []
    await _post(session, a, {"marine_open_water": True}, monkeypatch, calls)
    assert await _location_override_rows(session, b.id) == {}
    assert await physical_requirement_fingerprint_facts(session, b.id) == frozenset()
    assert calls == [str(a.id)]


async def test_toggle_without_effective_requirement_change_reuses_current_evaluation(rolled_back_session, monkeypatch):
    session, a, _b = rolled_back_session
    calls: list[str] = []
    # An explicit False on an absent requirement derives the identical effective requirements -> stored, but no
    # re-evaluation (every chip, including the four connected on 2026-10-05, changes the effective set only when ON).
    r1 = await _post(session, a, {"marine_open_water": False}, monkeypatch, calls)
    r2 = await _post(session, a, {"studio_stage": False}, monkeypatch, calls)
    assert r1["changed"] is True and r1["evaluation_triggered"] is False
    assert r2["changed"] is True and r2["evaluation_triggered"] is False
    assert calls == []


async def test_unknown_location_slug_is_rejected_and_never_persisted(rolled_back_session, monkeypatch):
    from fastapi import HTTPException
    from app.services.canonical_project_economics import _location_override_rows

    session, a, _b = rolled_back_session
    with pytest.raises(HTTPException) as exc:
        await _post(session, a, {"not_a_category": True}, monkeypatch, [])
    assert exc.value.status_code == 422
    assert await _location_override_rows(session, a.id) == {}


async def test_physical_requirements_honour_producer_overrides_not_just_script(rolled_back_session, monkeypatch):
    from app.services.canonical_project_economics import build_physical_requirements

    session, a, _b = rolled_back_session
    await _post(session, a, {"marine_open_water": True}, monkeypatch, [])
    reqs = derive_production_requirements(await build_physical_requirements(session, a.id))
    assert "open_water_filming" in reqs.required_capabilities
    await _post(session, a, {"marine_open_water": False}, monkeypatch, [])
    reqs = derive_production_requirements(await build_physical_requirements(session, a.id))
    assert "open_water_filming" not in reqs.required_capabilities


def test_legacy_singleton_locations_route_is_not_what_the_ui_calls():
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[2].joinpath("frontend/src/components/ProductionDetails.jsx").read_text()
    assert "postProjectLocations(projectId, locs)" in src


# ── jurisdiction exclusion is a different mechanism and is unchanged ────────────────────────

async def test_jurisdiction_exclusion_is_a_separate_mechanism_and_still_removes_the_jurisdiction(rolled_back_session, monkeypatch):
    from app.models.project_fact import ProjectFact
    from app.services import canonical_evaluation as ce

    import inspect
    evaluate_source = inspect.getsource(ce.evaluate_project)  # before _post() patches it
    session, a, _b = rolled_back_session
    session.add(ProjectFact(
        project_id=a.id, fact_key=f"{ce.JURISDICTION_PREFERENCE_FACT_PREFIX}CA-MB", value="excluded",
        value_type="string", source_type="user_override",
    ))
    await session.flush()
    await _post(session, a, {"marine_open_water": True}, monkeypatch, [])
    # exclusion set comes ONLY from jurisdiction-preference facts; the location control adds none
    assert set(await ce._excluded_jurisdiction_codes(session, a.id)) == {"CA-MB"}
    # and the candidate-universe filter that every family flows through is still wired
    assert "c[0] not in excluded_jurisdiction_codes" in evaluate_source
