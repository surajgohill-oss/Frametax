"""
Script Analyzer — Full Production Breakdown closeout (location fixes).

Two real, independently-confirmed defects found via runtime audit of the
Lips Like Sugar project's real screenplay:

  1. PARSER: two real, common scene-heading conventions used by Lips Like
     Sugar (a literal clock time, e.g. "2:38 PM", used in place of
     DAY/NIGHT — 82/145 of its own real headings; and "SAME", a standard
     continuity marker — 43/145) were not recognized as trailing
     time-of-day segments, so they were never stripped before the location
     identity was derived. One real location ("Campos Apartment") fragmented
     into dozens of distinct location_key values ("CAMPOS APARTMENT 2 38
     PM", "CAMPOS APARTMENT SAME", ...). Fixed generically in
     screenplay_structural_parser.py (PARSER_VERSION bumped to
     sa1-structural-1.1.0) — never infers DAY/NIGHT from a clock time,
     only strips it from the location tail.

  2. UI EXPOSURE: real, persisted ProjectLocationRequirement rows existed
     the entire time; canonical_production_view.py's generic
     `production["physical_requirements"]` was hardcoded to `{}` for every
     non-demo project, so ProductionDetails.jsx always showed "No script
     analysis available yet" regardless of real data. Fixed by
     canonical_project_economics.build_ui_location_categories(), which
     reads a project's own real rows through the existing, generic
     abstract_location() ontology — the same LOCATION_TAXONOMY/label
     contract the Little Utopia demo path already used.

These are pure-function / DB-round-trip tests, following the same
conventions as test_script_analyzer_sa1.py.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.ingestion.screenplay_structural_parser import (
    PARSER_VERSION,
    parse_structure,
)
from app.services.canonical_project_economics import build_ui_location_categories
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_location_requirement import ProjectLocationRequirement


# ── A. parser: clock-time and SAME headings no longer fragment location ────

def test_clock_time_heading_strips_time_but_never_infers_day_night():
    text = (
        "INT. CAMPOS APARTMENT - 2:38 PM\n\n"
        "Some real action here so the scene has body text.\n\n"
        "INT. CAMPOS APARTMENT - 12:03 PM\n\n"
        "More action.\n"
    )
    r = parse_structure(text)
    assert len(r.scenes) == 2
    # Same real location, one canonical key — not two.
    keys = {s.location_key for s in r.scenes}
    assert keys == {"CAMPOS APARTMENT"}
    for s in r.scenes:
        assert s.scripted_location == "CAMPOS APARTMENT"
        # A bare clock time never gets promoted to DAY or NIGHT — that
        # would be exactly the speculative interpretation SA-1 forbids.
        assert s.time_of_day == "UNKNOWN"


def test_same_heading_normalizes_to_continuous_and_strips_from_location():
    text = (
        "INT. ANDERSON APARTMENT - NIGHT\n\nAction.\n\n"
        "INT. ANDERSON APARTMENT - SAME\n\nMore action.\n"
    )
    r = parse_structure(text)
    assert len(r.scenes) == 2
    keys = {s.location_key for s in r.scenes}
    assert keys == {"ANDERSON APARTMENT"}
    assert r.scenes[1].time_of_day == "CONTINUOUS"


def test_ordinary_day_night_headings_are_unaffected_by_the_fix():
    text = "INT. HOUSE - DAY\n\nAction.\n\nEXT. HOUSE - NIGHT\n\nAction.\n"
    r = parse_structure(text)
    assert [s.time_of_day for s in r.scenes] == ["DAY", "NIGHT"]
    assert [s.location_key for s in r.scenes] == ["HOUSE", "HOUSE"]


def test_distinct_sub_locations_still_remain_distinct():
    # Section 7: normalization must not collapse genuinely distinct
    # locations that happen to share a root name.
    text = (
        "INT. JOHN'S HOUSE - KITCHEN - DAY\n\nAction.\n\n"
        "INT. JOHN'S HOUSE - BEDROOM - NIGHT\n\nAction.\n"
    )
    r = parse_structure(text)
    keys = {s.location_key for s in r.scenes}
    assert len(keys) == 2


def test_parser_version_bumped_for_the_new_normalization_rules():
    assert PARSER_VERSION == "sa1-structural-1.1.0"


# ── B. UI exposure: real persisted rows surface without fabrication ────────

@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Location Normalization Test Org", slug=f"locnorm-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"LocReq Test Project {uuid.uuid4().hex[:8]}")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    project_id = p.id
    try:
        yield p
    finally:
        still_there = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if still_there is not None:
            await db.execute(
                sa_delete(ProjectLocationRequirement).where(ProjectLocationRequirement.project_id == project_id)
            )
            await db.execute(sa_delete(Project).where(Project.id == project_id))
            await db.commit()


async def test_evidence_backed_categories_are_derived_from_real_rows(db: AsyncSession, project: Project):
    db.add_all(
        [
            ProjectLocationRequirement(
                id=uuid.uuid4(),
                project_id=project.id,
                description="Sahara desert dunes at dawn",
                location_key="SAHARA",
            ),
            ProjectLocationRequirement(
                id=uuid.uuid4(),
                project_id=project.id,
                description="Downtown city street, rush hour",
                location_key="DOWNTOWN STREET",
            ),
        ]
    )
    await db.commit()

    cats = await build_ui_location_categories(db, project.id)

    # All 13 taxonomy slugs are always present — never a partial list.
    assert len(cats) == 13
    assert cats["desert_arid"]["script_value"] is True
    assert "Sahara" in cats["desert_arid"]["evidence"]
    assert cats["urban_major_city"]["script_value"] is True
    # A category with no matching evidence stays honestly inactive, not
    # fabricated — matches Section 23's "do not fabricate" requirement.
    assert cats["snow_arctic"]["script_value"] is None
    assert cats["snow_arctic"]["evidence"] == "Not described in the material read."


async def test_no_rows_yields_all_categories_present_and_none_fabricated(db: AsyncSession, project: Project):
    cats = await build_ui_location_categories(db, project.id)
    assert len(cats) == 13
    assert all(v["script_value"] is None for v in cats.values())


async def test_category_override_rows_are_not_treated_as_script_evidence(db: AsyncSession, project: Project):
    # category_key IS NOT NULL rows are the UI's own producer-override
    # write path (Phase C) — they must never be misread as scripted
    # descriptions and fed through abstract_location().
    db.add(
        ProjectLocationRequirement(
            id=uuid.uuid4(),
            project_id=project.id,
            description="producer override note",
            category_key="beach_coast",
            override=True,
        )
    )
    await db.commit()
    cats = await build_ui_location_categories(db, project.id)
    assert cats["beach_coast"]["override"] is True
    assert cats["beach_coast"]["script_value"] is None
