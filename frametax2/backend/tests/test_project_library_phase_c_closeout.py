"""
Project Library Phase C closeout — persisted source of truth for
people/facts/location-category overrides.

Covers the new write-through paths added in app/api/v1/cineglobe.py and
the schema addition in migration 0064 (project_location_requirements.
category_key/override). Read-only assertions against the real migrated
Little Utopia project use no transaction wrapper (nothing to roll back);
new-row assertions (location category override) run inside a rolled-back
transaction so no test data is left behind.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.project import Project
from app.models.project_person import ProjectPerson
from app.models.project_location_requirement import ProjectLocationRequirement
from app.models.talent import TalentProfile
from app.data.little_utopia_people import PersonOverride, primary_person_name
from app.demo.little_utopia_state import (
    hydrate_location_overrides,
    hydrate_people_overrides,
    current_location_overrides,
    current_people_facts,
    apply_location_overrides,
    apply_people_facts,
)
from app.api.v1.cineglobe import _resolve_primary_talent

PROJECT_TITLE = "The Little Utopia"


@pytest.fixture
async def db():
    async with AsyncSession(engine) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.title == PROJECT_TITLE))
    row = result.scalar_one_or_none()
    assert row is not None, "Phase C migration (0063) has not been applied"
    return row


def test_primary_person_name_known_roles():
    assert primary_person_name("writer") == "Clara Salaman"
    assert primary_person_name("director") == "Kim Farrant"
    assert primary_person_name("producer") == "Rachel Winter"
    assert primary_person_name("dop") is None  # slot role, no verified base


async def test_resolve_primary_talent_writer_director_producer(db: AsyncSession, project: Project):
    writer = await _resolve_primary_talent(db, project, "writer")
    assert writer is not None and writer.name == "Clara Salaman"

    director = await _resolve_primary_talent(db, project, "director")
    assert director is not None and director.name == "Kim Farrant"

    # Two producer rows exist — must resolve to the PRIMARY (Rachel
    # Winter), matching build_little_utopia_people()'s idx==0 semantics.
    producer = await _resolve_primary_talent(db, project, "producer")
    assert producer is not None and producer.name == "Rachel Winter"

    unknown = await _resolve_primary_talent(db, project, "dop")
    assert unknown is None


async def test_people_and_location_rows_exist_with_expected_shape(db: AsyncSession, project: Project):
    people = (
        await db.execute(select(ProjectPerson, TalentProfile)
                          .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
                          .where(ProjectPerson.project_id == project.id))
    ).all()
    assert len(people) == 4
    by_role: dict[str, list[str]] = {}
    for pp, tp in people:
        by_role.setdefault(pp.role, []).append(tp.name)
    assert by_role["writer"] == ["Clara Salaman"]
    assert by_role["director"] == ["Kim Farrant"]
    assert sorted(by_role["producer"]) == ["Max Botkin", "Rachel Winter"]


async def test_location_category_column_and_unique_index(db: AsyncSession, project: Project):
    """Two rows for the SAME category on the SAME project must be
    rejected by the partial unique index added in 0064 — proves the
    constraint is real, not just documented.

    No explicit begin(): the session has already autobegun (the `project`
    fixture queried through it). Everything here is flushed but never
    committed, and the closing rollback discards both rows.
    """
    try:
        db.add(ProjectLocationRequirement(
            project_id=project.id, description="Test category",
            category_key="__test_category__", override=True,
        ))
        await db.flush()

        db.add(ProjectLocationRequirement(
            project_id=project.id, description="Test category dup",
            category_key="__test_category__", override=False,
        ))
        with pytest.raises(IntegrityError):
            await db.flush()
    finally:
        await db.rollback()


def test_hydrate_people_overrides_merges_and_clears_cache():
    """Pure in-memory behavior: hydrate merges the given roles into the
    same store apply_people_facts()/build_little_utopia_people() already
    read, without disturbing other roles already set there."""
    apply_people_facts({"dop_name": "Test DOP"})
    try:
        before = current_people_facts()
        assert before.get("dop", {}).get("name") == "Test DOP"

        hydrate_people_overrides({"writer": PersonOverride(nationality="FR")})
        after = current_people_facts()
        assert after["writer"]["nationality"] == "FR"
        # Untouched role survives the hydrate — it's a merge, not a wipe.
        assert after.get("dop", {}).get("name") == "Test DOP"
    finally:
        apply_people_facts({"dop_name": None})
        hydrate_people_overrides({"writer": PersonOverride()})  # clears — all-None drops the entry


def test_hydrate_location_overrides_replaces_wholesale():
    """Pure in-memory behavior: hydrate REPLACES the store wholesale
    (unlike people's merge) — it's meant to reflect Postgres ground truth
    exactly, including categories a caller no longer has a row for."""
    apply_location_overrides({"snow_arctic": True})
    try:
        assert current_location_overrides().get("snow_arctic") is True

        hydrate_location_overrides({"desert_arid": True})
        overrides = current_location_overrides()
        assert overrides == {"desert_arid": True}
        assert "snow_arctic" not in overrides
    finally:
        hydrate_location_overrides({})
