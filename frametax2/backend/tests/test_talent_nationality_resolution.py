"""
test_talent_nationality_resolution.py

Person Nationality Resolution closeout.

No mocking library (respx etc.) is installed or used elsewhere in this
repo, so network-dependent behavior is tested by monkeypatching this
module's own async functions at the boundary a real network call would
cross — never asserting against real Wikidata data (non-deterministic,
out of the test's control) and never skipping the real disambiguation/
precedence/persistence logic under test.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile
from app.services import talent_nationality_resolution as tnr


# ── A. identity disambiguation requires more than a loose name match ────────

async def test_multiple_occupation_corroborated_candidates_is_ambiguous_not_guessed(monkeypatch):
    async def fake_search(client, name):
        return [{"id": "Q1"}, {"id": "Q2"}]

    async def fake_entity(client, qid):
        # BOTH candidates corroborate the role — a real, if rare, case:
        # never silently pick the first one.
        return {"labels": {"en": {"value": f"Person {qid}"}},
                "claims": {"P106": [{"mainsnak": {"datavalue": {"value": {"id": "Q28389"}}}}]}}

    monkeypatch.setattr(tnr, "_wikidata_search", fake_search)
    monkeypatch.setattr(tnr, "_wikidata_entity", fake_entity)

    result = await tnr.resolve_person_nationality("Ambiguous Name", "writer")
    assert result.status == tnr.UNRESOLVED_AMBIGUOUS
    assert result.primary_iso2 is None


async def test_candidate_with_wrong_occupation_is_rejected_despite_name_match(monkeypatch):
    async def fake_search(client, name):
        return [{"id": "Q1"}]

    async def fake_entity(client, qid):
        # Real name match, but occupation is "athlete" (Q2066131), not
        # any writer/director/etc. vocabulary — must never be accepted
        # on name alone.
        return {"labels": {"en": {"value": "Same Name Different Person"}},
                "claims": {"P106": [{"mainsnak": {"datavalue": {"value": {"id": "Q2066131"}}}}]}}

    monkeypatch.setattr(tnr, "_wikidata_search", fake_search)
    monkeypatch.setattr(tnr, "_wikidata_entity", fake_entity)

    result = await tnr.resolve_person_nationality("Same Name Different Person", "writer")
    assert result.status == tnr.UNRESOLVED_NO_MATCH
    assert "occupation" in (result.error or "")


# ── B/C. citizenship from structured evidence; birthplace never substitutes ─

async def test_resolved_citizenship_comes_only_from_p27_never_p19_birthplace(monkeypatch):
    async def fake_search(client, name):
        return [{"id": "Q1"}]

    async def fake_entity(client, qid):
        if qid == "Q1":
            return {
                "labels": {"en": {"value": "Real Writer"}},
                "claims": {
                    "P106": [{"mainsnak": {"datavalue": {"value": {"id": "Q28389"}}}}],
                    # P19 (place of birth) present but MUST be ignored —
                    # only P27 (country of citizenship) may populate
                    # nationality.
                    "P19": [{"mainsnak": {"datavalue": {"value": {"id": "Q60"}}}}],  # New York City
                    "P27": [{"mainsnak": {"datavalue": {"value": {"id": "Q30"}}}}],  # USA
                },
            }
        if qid == "Q30":
            return {"labels": {"en": {"value": "United States of America"}},
                    "claims": {"P297": [{"mainsnak": {"datavalue": {"value": "US"}}}]}}
        return None

    monkeypatch.setattr(tnr, "_wikidata_search", fake_search)
    monkeypatch.setattr(tnr, "_wikidata_entity", fake_entity)

    result = await tnr.resolve_person_nationality("Real Writer", "writer")
    assert result.status == tnr.RESOLVED
    assert result.primary_iso2 == "US"
    assert result.citizenships == (tnr.CitizenshipClaim(qid="Q30", label="United States of America", iso2="US"),)


async def test_citizenship_claim_absent_stays_unresolved_even_with_matched_identity(monkeypatch):
    async def fake_search(client, name):
        return [{"id": "Q1"}]

    async def fake_entity(client, qid):
        # Identity matched (occupation corroborates) but NO P27 claim at
        # all — birthplace alone (even if present) must never fill in.
        return {"labels": {"en": {"value": "Matched No Citizenship"}},
                "claims": {"P106": [{"mainsnak": {"datavalue": {"value": {"id": "Q2526255"}}}}]}}

    monkeypatch.setattr(tnr, "_wikidata_search", fake_search)
    monkeypatch.setattr(tnr, "_wikidata_entity", fake_entity)

    result = await tnr.resolve_person_nationality("Matched No Citizenship", "director")
    assert result.status == tnr.UNRESOLVED_NO_MATCH
    assert result.matched_entity_id == "Q1"  # identity WAS established
    assert result.primary_iso2 is None
    assert result.citizenships == ()


# ── D. multiple citizenships are not silently misrepresented ────────────────

async def test_dual_citizenship_all_preserved_only_first_becomes_primary(monkeypatch):
    async def fake_search(client, name):
        return [{"id": "Q1"}]

    async def fake_entity(client, qid):
        if qid == "Q1":
            return {
                "labels": {"en": {"value": "Dual Citizen"}},
                "claims": {
                    "P106": [{"mainsnak": {"datavalue": {"value": {"id": "Q33999"}}}}],
                    "P27": [
                        {"mainsnak": {"datavalue": {"value": {"id": "Q145"}}}},  # UK
                        {"mainsnak": {"datavalue": {"value": {"id": "Q30"}}}},   # USA
                    ],
                },
            }
        if qid == "Q145":
            return {"labels": {"en": {"value": "United Kingdom"}},
                    "claims": {"P297": [{"mainsnak": {"datavalue": {"value": "GB"}}}]}}
        if qid == "Q30":
            return {"labels": {"en": {"value": "United States of America"}},
                    "claims": {"P297": [{"mainsnak": {"datavalue": {"value": "US"}}}]}}
        return None

    monkeypatch.setattr(tnr, "_wikidata_search", fake_search)
    monkeypatch.setattr(tnr, "_wikidata_entity", fake_entity)

    result = await tnr.resolve_person_nationality("Dual Citizen", "lead_cast")
    assert result.status == tnr.RESOLVED
    assert len(result.citizenships) == 2
    assert {c.iso2 for c in result.citizenships} == {"GB", "US"}
    assert result.primary_iso2 == "GB"  # first-listed, per this module's documented rule


# ── F. lookup failure leaves nationality unresolved, never breaks the caller ─

async def test_network_failure_returns_lookup_failed_never_raises(monkeypatch):
    import httpx

    async def failing_search(client, name):
        raise httpx.ConnectTimeout("simulated network failure")

    monkeypatch.setattr(tnr, "_wikidata_search", failing_search)

    result = await tnr.resolve_person_nationality("Anyone", "writer")
    assert result.status == tnr.LOOKUP_FAILED
    assert result.error is not None


# ── DB-backed: persistence, precedence, and Overview-read contract ──────────

@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Nationality Resolution Test Org", slug=f"nat-res-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    p = Project(id=uuid.uuid4(), organization_id=org.id, title=f"Nationality Resolution Test {uuid.uuid4().hex[:8]}")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    project_id = p.id
    try:
        yield p
    finally:
        still_there = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if still_there is not None:
            await db.execute(sa_delete(Project).where(Project.id == project_id))
            await db.commit()


async def test_lookup_failure_persists_disclosed_status_not_a_silent_noop(db: AsyncSession, project: Project, monkeypatch):
    talent = TalentProfile(id=uuid.uuid4(), name="Failure Case", role="writer")
    db.add(talent)
    await db.flush()
    pp = ProjectPerson(id=uuid.uuid4(), project_id=project.id, talent_id=talent.id, role="writer")
    db.add(pp)
    await db.commit()

    async def failing_resolve(name, role):
        return tnr.PersonResolutionResult(status=tnr.LOOKUP_FAILED, error="simulated")
    monkeypatch.setattr(tnr, "resolve_person_nationality", failing_resolve)

    result = await tnr.enrich_talent_nationality(db, project_person=pp, talent=talent)
    await db.commit()
    assert result.status == tnr.LOOKUP_FAILED
    assert talent.nationality_resolution_status == tnr.LOOKUP_FAILED
    assert talent.primary_nationality is None  # no fabricated fallback


# E. explicit project/user nationality overrides enrichment — never touched
async def test_confirmed_person_is_never_touched_by_the_resolver(db: AsyncSession, project: Project, monkeypatch):
    talent = TalentProfile(id=uuid.uuid4(), name="Producer Confirmed", role="writer", primary_nationality="FR")
    db.add(talent)
    await db.flush()
    pp = ProjectPerson(id=uuid.uuid4(), project_id=project.id, talent_id=talent.id, role="writer", is_confirmed=True)
    db.add(pp)
    await db.commit()

    called = {"n": 0}
    async def spy_resolve(name, role):
        called["n"] += 1
        return tnr.PersonResolutionResult(status=tnr.RESOLVED, primary_iso2="US")
    monkeypatch.setattr(tnr, "resolve_person_nationality", spy_resolve)

    result = await tnr.enrich_talent_nationality(db, project_person=pp, talent=talent)
    assert result is None
    assert called["n"] == 0  # resolver never even invoked
    assert talent.primary_nationality == "FR"  # untouched


async def test_resolved_value_never_overwrites_an_existing_explicit_nationality(db: AsyncSession, project: Project, monkeypatch):
    """Even for an unconfirmed row, a real existing value (e.g. entered
    before confirmation, or migrated from prior data) must not be
    clobbered by a fresh enrichment result."""
    talent = TalentProfile(id=uuid.uuid4(), name="Already Has Value", role="director", primary_nationality="MU")
    db.add(talent)
    await db.flush()
    pp = ProjectPerson(id=uuid.uuid4(), project_id=project.id, talent_id=talent.id, role="director", is_confirmed=False)
    db.add(pp)
    await db.commit()

    async def fake_resolve(name, role):
        return tnr.PersonResolutionResult(status=tnr.RESOLVED, matched_entity_id="Q999", primary_iso2="GB")
    monkeypatch.setattr(tnr, "resolve_person_nationality", fake_resolve)

    await tnr.enrich_talent_nationality(db, project_person=pp, talent=talent)
    await db.commit()
    assert talent.primary_nationality == "MU"  # existing value wins
    assert talent.nationality_resolution_status == tnr.RESOLVED  # attempt still recorded


# G. Overview reads persisted canonical data, never invokes the resolver
async def test_overview_people_payload_reads_persisted_status_without_calling_resolver(db: AsyncSession, project: Project, monkeypatch):
    from app.services.canonical_production_view import build_generic_pkg_and_economics

    talent = TalentProfile(
        id=uuid.uuid4(), name="Already Resolved", role="writer", primary_nationality="US",
        nationality_resolution_status=tnr.RESOLVED, nationality_source="wikidata",
    )
    db.add(talent)
    await db.flush()
    db.add(ProjectPerson(id=uuid.uuid4(), project_id=project.id, talent_id=talent.id, role="writer"))
    await db.commit()

    called = {"n": 0}
    async def spy_resolve(name, role):
        called["n"] += 1
        return tnr.PersonResolutionResult(status=tnr.RESOLVED, primary_iso2="XX")
    monkeypatch.setattr(tnr, "resolve_person_nationality", spy_resolve)

    sections = await build_generic_pkg_and_economics(db, project.id)
    writer = sections["people"]["writers"][0]
    assert writer["nationality"] == "US"
    assert writer["nationality_resolution_status"] == "resolved"
    assert called["n"] == 0  # reading Overview state never triggers a lookup
