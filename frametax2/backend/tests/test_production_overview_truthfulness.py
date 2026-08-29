"""
test_production_overview_truthfulness.py

Production Overview Truthfulness closeout.

Real defects found and fixed by live-screen tracing against Lips Like Sugar
(not assumed): (1) the screenplay's own title page states its writer and
director ("Directed by Brantley Gutierrez" / "Written by Anthony Tambakis")
but nothing connected that already-extracted text to the canonical
ProjectPerson/TalentProfile model; (2) canonical_production_view.py's
pkg["missing_inputs"] was hardcoded to [] for every generic (non-demo)
project, so "Questions Remaining" read 0 even with visibly unresolved
personnel; (3) the Production Facts edit control saved through the legacy
singleton POST /people, which resolves a different (or no) project entirely
for anything besides whichever one the demo engine happens to be pointed at.

No nationality/talent external resolver exists anywhere in this codebase
(confirmed via repository-wide search before writing any code) — nationality
for recovered personnel is left genuinely unresolved, never guessed.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_person import ProjectPerson
from app.models.screenplay import ScreenplayDocument
from app.models.talent import TalentProfile
from app.services.canonical_production_view import build_generic_pkg_and_economics
from app.services.script_analysis_service import (
    derive_title_page_credits,
    persist_title_page_credits,
)


# ── derive_title_page_credits: pure function, no DB ─────────────────────────

def test_derive_title_page_credits_reads_directed_and_written_by():
    text = (
        "LIPS LIKE SUGAR\n"
        "Directed by Brantley Gutierrez\n"
        "Written by Anthony Tambakis\n"
        "Story by Brantley Gutierrez &  Anthony Tambakis\n\n"
        "OVER BLACK\nA synthesizer eerily droning.\n"
    )
    credits = derive_title_page_credits(text)
    assert credits["director"] == ["Brantley Gutierrez"]
    assert credits["writer"] == ["Anthony Tambakis"]


def test_derive_title_page_credits_never_matches_story_by_as_writer():
    """'Story by' is a distinct WGA credit — never conflated with the
    screenplay-authorship 'Written by' credit, to avoid crediting the
    wrong person when the two differ."""
    text = "TITLE\nStory by Someone Else\n"
    credits = derive_title_page_credits(text)
    assert credits["writer"] == []


def test_derive_title_page_credits_ignores_mid_script_prose():
    """Only the title-page region (first ~2000 chars) is scanned, and a
    credit line is a short attribution, never a full sentence — a scene
    action line that happens to start with these words must never match."""
    padding = "X" * 2100
    text = padding + "\nDirected by someone in a very very long line of dialogue that goes on and on and describes an entire scene."
    credits = derive_title_page_credits(text)
    assert credits == {"director": [], "writer": []}


def test_derive_title_page_credits_absent_when_genuinely_not_stated():
    text = "F#K VALENTINE'S DAY\nby\nSteve Bencich\n2/14/2023\n"
    credits = derive_title_page_credits(text)
    assert credits == {"director": [], "writer": []}


# ── persist_title_page_credits + missing_inputs: real DB round-trip ─────────

@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Overview Truthfulness Test Org", slug=f"ovx-truth-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Overview Truthfulness Test {uuid.uuid4().hex[:8]}")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    project_id = p.id
    try:
        yield p
    finally:
        still_there = (await db.execute(
            __import__("sqlalchemy").select(Project).where(Project.id == project_id)
        )).scalar_one_or_none()
        if still_there is not None:
            await db.execute(sa_delete(Project).where(Project.id == project_id))
            await db.commit()


def _fake_screenplay(project_id) -> ScreenplayDocument:
    return ScreenplayDocument(
        id=uuid.uuid4(), project_id=project_id, filename="TEST SCRIPT.pdf", file_type="pdf",
        raw_text="TEST SCRIPT\nDirected by Test Director\nWritten by Test Writer\n",
    )


async def test_persist_title_page_credits_writes_real_project_person_rows(db: AsyncSession, project: Project):
    screenplay = _fake_screenplay(project.id)
    db.add(screenplay)
    await db.flush()
    credits = derive_title_page_credits(screenplay.raw_text)
    written = await persist_title_page_credits(
        db, project_id=project.id, screenplay=screenplay, credits=credits
    )
    await db.commit()
    assert written == 2

    rows = (await db.execute(
        __import__("sqlalchemy").select(ProjectPerson, TalentProfile)
        .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
        .where(ProjectPerson.project_id == project.id)
    )).all()
    by_role = {pp.role: tp.name for pp, tp in rows}
    assert by_role == {"director": "Test Director", "writer": "Test Writer"}
    # provenance is real, not silent
    notes = {pp.role: tp.notes for pp, tp in rows}
    assert "TEST SCRIPT.pdf" in notes["writer"]


async def test_persist_title_page_credits_never_overwrites_an_existing_person(db: AsyncSession, project: Project):
    """Fact precedence (Section 8): existing verified/attached person data
    outranks a fresh derivation — a role that already has a real person
    must never be silently replaced."""
    existing_talent = TalentProfile(id=uuid.uuid4(), name="Existing Writer", role="writer")
    db.add(existing_talent)
    await db.flush()
    db.add(ProjectPerson(id=uuid.uuid4(), project_id=project.id, talent_id=existing_talent.id, role="writer", is_confirmed=True))
    await db.commit()

    screenplay = _fake_screenplay(project.id)
    db.add(screenplay)
    await db.flush()
    credits = derive_title_page_credits(screenplay.raw_text)
    written = await persist_title_page_credits(
        db, project_id=project.id, screenplay=screenplay, credits=credits
    )
    await db.commit()
    assert written == 1  # only director was written; writer already existed

    rows = (await db.execute(
        __import__("sqlalchemy").select(TalentProfile).join(
            ProjectPerson, ProjectPerson.talent_id == TalentProfile.id
        ).where(ProjectPerson.project_id == project.id, ProjectPerson.role == "writer")
    )).scalars().all()
    assert len(rows) == 1
    assert rows[0].name == "Existing Writer"  # untouched


async def test_missing_inputs_reflects_real_unresolved_personnel_generically(db: AsyncSession, project: Project):
    """The exact defect: pkg.missing_inputs (what Overview's 'Questions
    Remaining' actually reads) must be non-empty when real personnel are
    unresolved -- never hardcoded to [] regardless of project identity."""
    talent = TalentProfile(id=uuid.uuid4(), name="Known Writer", role="writer")  # no nationality
    db.add(talent)
    await db.flush()
    db.add(ProjectPerson(id=uuid.uuid4(), project_id=project.id, talent_id=talent.id, role="writer"))
    await db.commit()

    sections = await build_generic_pkg_and_economics(db, project.id)
    identifiers = {m["identifier"] for m in sections["pkg"]["missing_inputs"]}
    assert "MISSING-WRITERS-NATIONALITY" in identifiers  # known name, unresolved nationality
    assert "MISSING-DIRECTORS-NAME" in identifiers  # genuinely no director attached
    assert "MISSING-PRODUCERS-NAME" in identifiers
    assert "MISSING-CAST-NAME" in identifiers
    # optional recurring slots (dop/editor/composer, lead_cast_2/3) do not
    # count merely for being empty
    assert not any("DOP" in i or "EDITOR" in i or "COMPOSER" in i for i in identifiers)


async def test_missing_inputs_empty_when_all_primary_roles_resolved(db: AsyncSession, project: Project):
    for role, name, nat in [
        ("writer", "W", "US"), ("director", "D", "US"),
        ("producer", "P", "US"), ("lead_cast", "C", "US"),
    ]:
        t = TalentProfile(id=uuid.uuid4(), name=name, role=role, primary_nationality=nat)
        db.add(t)
        await db.flush()
        db.add(ProjectPerson(id=uuid.uuid4(), project_id=project.id, talent_id=t.id, role=role))
    await db.commit()

    sections = await build_generic_pkg_and_economics(db, project.id)
    assert sections["pkg"]["missing_inputs"] == []


# ── project-scoped people write (editability) ────────────────────────────

async def test_project_scoped_people_write_creates_a_role_with_no_prior_row(db: AsyncSession, project: Project):
    """The exact editability defect: a role with no persisted person yet
    (e.g. a genuinely-unknown producer) must become settable through the
    Production Facts edit control, scoped to the ACTUAL project being
    viewed -- not the legacy singleton engine's project."""
    from app.api.v1.cineglobe import PeopleAnswers, post_project_people

    result = await post_project_people(
        str(project.id), PeopleAnswers(answers={"producer_name": "New Producer"}), db=db,
    )
    assert result["producers"][0]["name"] == "New Producer"
    assert result["producers"][0]["confirmed"] is True


async def test_project_scoped_people_write_updates_an_existing_row_and_outranks_derivation(db: AsyncSession, project: Project):
    talent = TalentProfile(id=uuid.uuid4(), name="Derived Writer", role="writer")
    db.add(talent)
    await db.flush()
    db.add(ProjectPerson(id=uuid.uuid4(), project_id=project.id, talent_id=talent.id, role="writer", is_confirmed=False))
    await db.commit()

    from app.api.v1.cineglobe import PeopleAnswers, post_project_people
    result = await post_project_people(
        str(project.id), PeopleAnswers(answers={"writer_name": "Corrected Writer", "writer_nationality": "GB"}), db=db,
    )
    assert result["writers"][0]["name"] == "Corrected Writer"
    assert result["writers"][0]["nationality"] == "GB"
    assert result["writers"][0]["confirmed"] is True

    # only one TalentProfile/ProjectPerson row for this role — updated in
    # place, never duplicated
    rows = (await db.execute(
        __import__("sqlalchemy").select(ProjectPerson).where(
            ProjectPerson.project_id == project.id, ProjectPerson.role == "writer",
        )
    )).scalars().all()
    assert len(rows) == 1


async def test_project_scoped_people_write_never_touches_a_different_project(db: AsyncSession, project: Project):
    """Cross-project isolation: writing to project A must never create or
    modify a row visible to project B."""
    org2 = Organization(name="Other Org", slug=f"other-org-{uuid.uuid4().hex[:8]}")
    db.add(org2)
    await db.flush()
    other = Project(id=uuid.uuid4(), organization_id=org2.id, title="Other Project")
    db.add(other)
    await db.commit()
    try:
        from app.api.v1.cineglobe import PeopleAnswers, post_project_people
        await post_project_people(
            str(project.id), PeopleAnswers(answers={"director_name": "Only For This Project"}), db=db,
        )
        other_sections = await build_generic_pkg_and_economics(db, other.id)
        assert other_sections["pkg"]["missing_inputs"] or True  # sanity: call succeeds
        other_rows = (await db.execute(
            __import__("sqlalchemy").select(ProjectPerson).where(ProjectPerson.project_id == other.id)
        )).scalars().all()
        assert other_rows == []
    finally:
        await db.execute(sa_delete(Project).where(Project.id == other.id))
        await db.commit()
