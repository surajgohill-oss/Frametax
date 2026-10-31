"""The four-anchor allow-list and registered isolated copies gate every operator evaluation (services/evaluation_authorization.py).

DB-free except two controls that connect to the isolated ``frametax2_pytest`` database read-only (it holds no anchor, so they prove the REFUSAL paths); the positive path is exercised by the
rendered isolated-copy runs recorded in the closeout report. No real production is read or evaluated here."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services import bounded_regeneration as br
from app.services.evaluation_authorization import (
    FOUR_ANCHORS, EvaluationNotAuthorized, assert_authorized_evaluation, check_static, load_manifest, restriction_enabled,
)

ANCHORS = sorted(FOUR_ANCHORS)
CLOSEOUT, BASE, SOURCE = "frametax2_four_closeout_20261029", "frametax2_four_closeout_base_20261029", "frametax2_claude_optimizer_acceptance_20260919"


def test_the_allow_list_is_exactly_the_four_anchors_by_canonical_uuid_and_bh_is_bad_hombres():
    assert len(FOUR_ANCHORS) == 4
    assert FOUR_ANCHORS["4355ae88-a636-4c18-af60-ad73b2646124"] == ("BH", "Bad Hombres")
    assert {c for c, _ in FOUR_ANCHORS.values()} == {"LU", "LLS", "FVD", "BH"}
    assert "Bath House" not in {t for _, t in FOUR_ANCHORS.values()}


@pytest.mark.parametrize("pid", ANCHORS)
def test_each_anchor_is_authorized_on_each_registered_evaluation_copy(pid):
    for database in (CLOSEOUT, BASE):
        check_static(pid, database)


def test_a_non_anchor_project_is_refused_even_on_a_registered_copy():
    with pytest.raises(EvaluationNotAuthorized, match="not one of the four"):
        check_static(uuid.uuid4(), CLOSEOUT)
    with pytest.raises(EvaluationNotAuthorized, match="not one of the four"):
        check_static("3519feda-d280-435f-badc-1e4c788a2cb3", CLOSEOUT)  # 10 Double Zero: a real production outside the authorization


@pytest.mark.parametrize("database", ["frametax2", "frametax2_pytest", "frametax2_other_copy"])
def test_an_unregistered_database_is_refused_for_every_anchor(database):
    for pid in ANCHORS:
        with pytest.raises(EvaluationNotAuthorized, match="not registered"):
            check_static(pid, database)


def test_the_read_only_source_is_registered_but_never_evaluable():
    with pytest.raises(EvaluationNotAuthorized, match="read_only_source"):
        check_static(ANCHORS[0], SOURCE)


def test_manifest_traces_every_copy_to_the_source_with_equal_content_hashes():
    manifest = load_manifest()
    by_name = {d["database"]: d for d in manifest["databases"]}
    assert set(by_name) == {SOURCE, CLOSEOUT, BASE}
    assert by_name[SOURCE]["evaluation_allowed"] is False and by_name[SOURCE]["project_count"] > 4
    for name in (CLOSEOUT, BASE):
        entry = by_name[name]
        assert entry["evaluation_allowed"] and entry["source_database"] == SOURCE and entry["project_count"] == 4
        assert entry["differs_from_source"] == {}, f"{name}: a copy's content hash differs from the source: {entry['differs_from_source']}"
        assert set(entry["projects"]) == set(FOUR_ANCHORS)
        for pid, project in entry["projects"].items():
            assert project["title"] == FOUR_ANCHORS[pid][1] == by_name[SOURCE]["projects"][pid]["title"]
            assert project["budget_lines"][0] > 0 and len(project["budget_lines"][1]) == 16


@pytest.mark.asyncio
async def test_the_database_check_refuses_a_database_that_is_not_a_registered_copy():
    async with AsyncSession(engine) as session:
        with pytest.raises(EvaluationNotAuthorized, match="not registered"):
            await assert_authorized_evaluation(session, ANCHORS[0])


@pytest.mark.asyncio
async def test_a_registered_database_holding_other_projects_is_not_an_isolated_four_anchor_copy():
    manifest = load_manifest()
    pytest_entry = {"database": "frametax2_pytest", "role": "evaluation_copy", "evaluation_allowed": True, "projects": {ANCHORS[0]: {}}}
    async with AsyncSession(engine) as session:
        try:
            await assert_authorized_evaluation(session, ANCHORS[0], {**manifest, "databases": [pytest_entry]})
        except EvaluationNotAuthorized as exc:
            assert "outside the four anchors" in str(exc) or "is not present" in str(exc)
        else:
            raise AssertionError("a database with non-anchor projects must be refused")


@pytest.mark.asyncio
async def test_the_operator_path_refuses_before_any_evaluation_work(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"postgresql+psycopg://u:p@h/{CLOSEOUT}")  # passes the database-name assertion; the session below is the pytest database
    with pytest.raises(EvaluationNotAuthorized):
        await br.regenerate_project(uuid.uuid4(), timeout_s=5, session_factory=lambda: AsyncSession(engine))


@pytest.mark.asyncio
async def test_the_product_save_worker_is_gated_only_when_the_restriction_flag_is_set(monkeypatch):
    monkeypatch.delenv("CINEGLOBE_EVALUATION_ALLOWLIST", raising=False)
    assert restriction_enabled() is False
    monkeypatch.setenv("CINEGLOBE_EVALUATION_ALLOWLIST", "four-anchor-copies")
    assert restriction_enabled() is True
    with pytest.raises(EvaluationNotAuthorized):
        await br.regenerate_project(uuid.uuid4(), timeout_s=5, require_isolated_database=False, session_factory=lambda: AsyncSession(engine))
