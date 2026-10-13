"""Production type election (2026-10-13), isolated synthetic records only (rolled back; no real project).

Independent expectations: the stored format maps to the production_type the RateRules are scoped by; the Georgia credit is scoped to feature films (RateRule.production_types), so a stated
documentary type must remove it from the priced candidates and a stated feature must restore it; the type is part of the evaluation fingerprint; null clears to NOT_STATED (priced as a feature
film, and the served view says the default is the engine's, not the producer's answer)."""
from __future__ import annotations

import uuid

import pytest

from app.data.program_rate_rules import get_rate_rules
from app.models.project import Project
from app.services.production_type_election import PRODUCTION_FORMAT_OPTIONS, production_type_view, validate_format, write_production_type
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures


def test_the_options_are_exactly_the_engines_own_mapping():
    from app.services.canonical_project_economics import _FORMAT_TO_PRODUCTION_TYPE
    assert [f for f, _ in PRODUCTION_FORMAT_OPTIONS] == list(_FORMAT_TO_PRODUCTION_TYPE)
    assert {o["format"]: o["production_type"] for o in production_type_view("feature")["options"]} == _FORMAT_TO_PRODUCTION_TYPE


@pytest.mark.parametrize("bad", ["Feature film", "tv", "", 3, ["feature"], "short"])
def test_a_free_form_type_is_refused(bad):
    with pytest.raises(ValueError):
        validate_format(bad)


def test_unknown_is_not_a_type_and_says_so():
    nothing = production_type_view(None)
    assert nothing["state"] == "NOT_STATED" and nothing["format"] is None and nothing["effective_production_type"] == "feature_film"
    assert "No production type is stated" in nothing["note"]
    stated = production_type_view("documentary")
    assert stated["state"] == "STATED" and stated["effective_production_type"] == "creative_documentary"
    assert validate_format(None) is None and validate_format(" Animation ") == "animation"


def test_the_georgia_credit_is_scoped_to_feature_films():
    assert {t for r in get_rate_rules("us_ga_film_credit") for t in r.production_types} == {"feature_film"}


async def _ga_candidate(db, pid):
    from app.services.canonical_evaluation import evaluate_project
    await evaluate_project(db, pid)
    return [e for e in await served_structures(db, pid) if e["program_slugs"] == ["us_ga_film_credit"]]


@pytest.mark.asyncio
async def test_a_stated_documentary_removes_the_feature_only_program_and_a_stated_feature_restores_it():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="US-GA")
        project = (await db.get(Project, uuid.UUID(pid)))
        assert (await _ga_candidate(db, pid)), "a feature film is eligible for the Georgia credit"
        view = await write_production_type(db, project, "documentary")
        await db.commit()
        assert view["state"] == "STATED" and view["effective_production_type"] == "creative_documentary"
        assert not [e for e in await _ga_candidate(db, pid) if e["candidate_status"] == "PRICED"], "the feature-only Georgia credit cannot price a stated documentary"
        await write_production_type(db, project, "feature")
        await db.commit()
        assert [e for e in await _ga_candidate(db, pid) if e["candidate_status"] == "PRICED"], "restoring the feature type restores the candidate"


@pytest.mark.asyncio
async def test_the_type_is_part_of_the_fingerprint_and_clearing_returns_to_the_original():
    from app.services.canonical_evaluation import _compute_fingerprint  # noqa: F401  (the fingerprint builder reads inputs.production_type)
    from app.services.canonical_project_economics import build_project_economic_inputs
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="US-GA")
        project = await db.get(Project, uuid.UUID(pid))
        original = (await build_project_economic_inputs(db, project.id, read_only=True)).inputs.production_type
        await write_production_type(db, project, "animation")
        await db.commit()
        changed = (await build_project_economic_inputs(db, project.id, read_only=True)).inputs.production_type
        await write_production_type(db, project, None)
        await db.commit()
        cleared = (await build_project_economic_inputs(db, project.id, read_only=True)).inputs.production_type
        assert original == "feature_film" and changed == "animation" and cleared == "feature_film"
        assert project.format is None


@pytest.mark.asyncio
async def test_the_route_validates_stores_and_clears_without_evaluating():
    from fastapi import HTTPException

    from app.api.v1.cineglobe import ProductionTypeElection, post_production_type
    from app.services.canonical_evaluation import ENGINE_VERSION  # noqa: F401
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="US-GA")
        await db.commit()   # the route rolls back on a refused request: the project must already be committed (the harness removes it afterwards)
        with pytest.raises(HTTPException) as bad:
            await post_production_type(pid, ProductionTypeElection(format="short"), db)
        assert bad.value.status_code == 422
        with pytest.raises(HTTPException) as missing:
            await post_production_type(str(uuid.uuid4()), ProductionTypeElection(format="series"), db)
        assert missing.value.status_code == 404
        ok = await post_production_type(pid, ProductionTypeElection(format="series"), db)
        assert ok["production_type"]["state"] == "STATED" and ok["production_type"]["effective_production_type"] == "tv_series"
        cleared = await post_production_type(pid, ProductionTypeElection(format=None), db)
        assert cleared["production_type"]["state"] == "NOT_STATED"
