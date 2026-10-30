"""Isolated-synthetic equivalents of two real-corpus controls that cannot run on the four authorized copies.

* test_p0_part_001_non_claiming_primary_excluded_across_broader_corpus needs nine OTHER real productions (not authorized): here the same invariant -- a component relocation's participants are
  exactly its incentive-claiming segments, and a non-claiming primary never appears -- is asserted on every component_relocation structure of an isolated synthetic project.
* test_bilateral_treaty_with_home_as_a_party_includes_home_in_participants skipped because it selected treaties by a label prefix built from the jurisdiction CODE while labels carry the country NAME
  (a predicate that can never match): here a synthetic project whose home is a registered treaty party is checked, selecting by participants and requiring at least one candidate.

Synthetic projects only, rolled back, on ``frametax2_pytest``; no real production is read or evaluated."""
from __future__ import annotations

import uuid

import pytest

from app.services.canonical_evaluation import evaluate_project
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

# One movable component (VFX) keeps the hybrid search small: a budget with VFX, post AND music has three movable units and evaluates for minutes (the real F#K / LLS shape), which is not needed
# to exercise component participants or treaty candidates.
LINES = (("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0), ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
         ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0), ("4000", "VFX", "vfx", "post", 300_000.0))


@pytest.mark.asyncio
async def test_component_relocation_participants_are_exactly_the_claiming_segments_and_a_non_claiming_primary_is_excluded():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="US")
        assert (await evaluate_project(db, uuid.UUID(pid)))["status"] == "EVALUATION_COMPLETE"
        structures = await served_structures(db, pid)
        components = [s for s in structures if s["structure_type"] == "component_relocation"]
        assert components, "the isolated project yields component relocation structures"
        non_claiming_primary_seen = 0
        for s in components:
            expected = {seg["jurisdiction_code"] for seg in (s.get("segments") or []) if seg.get("claims_incentive") is True and seg.get("jurisdiction_code")}
            served = set(s.get("participants") or [])
            assert served == expected, f"{s['structure_id']}: participants {sorted(served)} != claiming segments {sorted(expected)}"
            primary = s["primary_jurisdiction"]
            primary_seg = next((seg for seg in s.get("segments") or [] if seg.get("jurisdiction_code") == primary), None)
            if primary_seg is not None and primary_seg.get("claims_incentive") is False:
                non_claiming_primary_seen += 1
                assert primary not in served, f"{s['structure_id']}: the non-claiming primary {primary} must not be a participant"
        assert non_claiming_primary_seen > 0, "the control must exercise a non-claiming primary (a US-federal home has no claiming primary segment, the shape of the nine real US-primary productions)"


@pytest.mark.asyncio
@pytest.mark.parametrize("home", ["GB", "FR"])
async def test_a_home_jurisdiction_bilateral_treaty_includes_home_and_exactly_two_parties(home):
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code=home)
        assert (await evaluate_project(db, uuid.UUID(pid)))["status"] == "EVALUATION_COMPLETE"
        structures = await served_structures(db, pid)
        # Treaty labels carry the country NAME ("United Kingdom + Australia"), so a home-party bilateral is identified by its participants (the home code among exactly two real parties),
        # never by a label prefix built from the code.
        home_bilateral = [s for s in structures if s["structure_type"] == "treaty_coproduction" and " + " in s["label"] and home in s["participants"]
                          and "Eurimages" not in s["label"] and "European Convention" not in s["label"]]
        assert home_bilateral, f"{home}: the isolated project serves home-party bilateral treaty candidates"
        for s in home_bilateral:
            assert len(s["participants"]) == 2, f"{s['label']}: expected exactly 2 real parties, got {s['participants']}"
            assert s["participants"][0] == home or home in s["participants"], f"{s['label']}: home {home} must be a participant"
