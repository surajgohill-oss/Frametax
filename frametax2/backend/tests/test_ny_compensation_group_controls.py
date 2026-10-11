"""Controls for DR-01 (contradictory durable elections), DR-02 (composer membership of the NY compensation group) and the NY two-producer
limit. Register cases are DB-free and hand-computed; the fact-store cases run on rolled-back synthetic records only."""
from __future__ import annotations

from types import SimpleNamespace as R

import pytest
from sqlalchemy import select

from app.calculators.ny_atl_individual_cap import (
    FACT_COMPOSER_PREFIX, FACT_PAYEE_PREFIX, FACT_PRODUCER_ROLE_PREFIX, composer_portion_from_subaccounts, limits_facts_from_amount_facts, payee_amount_facts,
)
from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.program_spend_rules import get_program_rules, resolve_program_doctrine
from app.models.enums import ProjectFactSourceType, ReviewStatus
from app.models.project_fact import ProjectFact
from app.services.canonical_project_economics import _evidenced_program_facts
from app.services.ny_producer_facts import write_ny_program_facts
from tests.isolated_records import create_synthetic_project, isolated_session

NY = "ny_state_film"
Q, X, G = QualificationState.QUALIFIES, QualificationState.EXCLUDED, QualificationState.GREY_AREA_REQUIRES_AUTHORITY


def _reg(rows, **facts):
    """rows: (category, amount[, source_subaccounts]); line ids L0, L1, ... in order."""
    lines = [BudgetLine(account_code=str(1000 + i), description=r[0].upper(), amount_usd=r[1], spend_category=r[0], is_memo=False, line_id=f"L{i}",
                        source_subaccounts=tuple(r[2]) if len(r) > 2 else ()) for i, r in enumerate(rows)]
    pf = ProductionFacts(jurisdiction_code="US-NY", ny_atl_limits_apply=True, **{k: tuple(v.items()) for k, v in facts.items()})
    return derive_qualification_register(lines, program_slug=NY, facts=pf, rate=0.3, rules=get_program_rules(NY), doctrine=resolve_program_doctrine(NY).doctrine)


def _sum(reg, state, needle="", line=None):
    return round(sum(a.amount_usd for a in reg if a.state == state and needle in a.reason and (line is None or a.line_id == line)), 2)


MUSIC_CHILDREN = ({"account_code": "5001", "description": "Composer fee", "amount_usd": 350_000.0},
                  {"account_code": "5002", "description": "Orchestra and musicians", "amount_usd": 150_000.0},
                  {"account_code": "5003", "description": "Music licensing", "amount_usd": 100_000.0})


# ── DR-02: composer membership ────────────────────────────────────────────────────────────────────────────────────────────

def test_composer_portion_is_recognized_only_from_authored_children_that_name_the_composer():
    assert composer_portion_from_subaccounts(MUSIC_CHILDREN, 600_000.0) == 350_000.0
    assert composer_portion_from_subaccounts(({"account_code": "1", "description": "Composer's license fee", "amount_usd": 100_000.0},), 100_000.0) is None
    assert composer_portion_from_subaccounts(MUSIC_CHILDREN, 650_000.0) is None, "children that do not conserve the account are never used"
    dup = ({"account_code": "5001", "description": "Composer fee", "amount_usd": 300_000.0}, {"account_code": "5001", "description": "Orchestra", "amount_usd": 300_000.0})
    assert composer_portion_from_subaccounts(dup, 600_000.0) is None
    assert composer_portion_from_subaccounts((), 600_000.0) is None


def test_composer_compensation_joins_the_group_and_recording_and_licensing_stay_ordinary_costs():
    # group: director 1.5M + composer 0.35M = 1.85M ; other: crew 4.0M + recording/licensing 0.25M = 4.25M ; limit 40% x 4.25M = 1.70M ; excess 150,000
    reg = _reg([("atl_director", 1_500_000.0), ("btl_crew_labor", 4_000_000.0), ("music", 600_000.0, MUSIC_CHILDREN)])
    assert _sum(reg, X, "forty percent") == 150_000.0
    assert _sum(reg, X, "forty percent", line="L0") == 121_621.62 and _sum(reg, X, "forty percent", line="L2") == 28_378.38     # pro rata 1.5 : 0.35
    assert _sum(reg, Q, line="L2") == 600_000.0 - 28_378.38
    # the same budget with the composer treated as an ordinary cost (no evidence) would show NO excess -- the denominator trap the review named
    blind = _reg([("atl_director", 1_500_000.0), ("btl_crew_labor", 4_000_000.0), ("music", 600_000.0)])
    assert _sum(blind, X, "forty percent") == 0.0
    assert any("UNRESOLVED: whether part of this music account is composer compensation" in a.reason for a in blind if a.line_id == "L2" and a.state == Q), \
        "unresolved mixed music membership must stay visible"


def test_stated_composer_compensation_is_capped_per_identified_payee_but_recording_is_not():
    reg = _reg([("btl_crew_labor", 9_000_000.0), ("music", 900_000.0)], ny_atl_composer_by_line={"L1": 700_000.0}, ny_atl_payee_by_line={"L1": 1})
    assert _sum(reg, X, "per-individual cap", line="L1") == 200_000.0       # composer 700k - 500k
    assert _sum(reg, Q, line="L1") == 700_000.0                            # 500k composer + 200k recording/licensing
    unidentified = _reg([("btl_crew_labor", 9_000_000.0), ("music", 900_000.0)], ny_atl_composer_by_line={"L1": 700_000.0})
    assert _sum(unidentified, X, "per-individual cap") == 0.0
    assert _sum(unidentified, Q, "UNRESOLVED: the $500,000 per-individual cap", line="L1") == 700_000.0


def test_music_with_no_composer_evidence_is_never_capped_or_excluded():
    reg = _reg([("btl_crew_labor", 1_000_000.0), ("music", 5_000_000.0)])
    assert _sum(reg, X) == 0.0 and _sum(reg, Q, line="L1") == 5_000_000.0


# ── two-producer limit ────────────────────────────────────────────────────────────────────────────────────────────────────

def test_only_one_executive_and_one_line_producer_qualify():
    base = [("atl_producer", 200_000.0), ("atl_producer", 150_000.0), ("atl_producer", 90_000.0), ("btl_crew_labor", 9_000_000.0)]
    reg = _reg(base, ny_atl_producer_role_by_line={"L0": 1, "L1": 2, "L2": 3})
    assert _sum(reg, X, "only one executive producer", line="L2") == 90_000.0
    assert _sum(reg, Q, line="L0") == 200_000.0 and _sum(reg, Q, line="L1") == 150_000.0
    unstated = _reg(base)
    assert _sum(unstated, X) == 0.0
    assert all("role is not stated" in a.reason for a in unstated if a.line_id in ("L0", "L1", "L2") and a.state == Q)


def test_two_individuals_stated_for_one_role_is_a_producer_election_not_a_guess():
    rows = [("atl_producer", 200_000.0), ("atl_producer", 180_000.0), ("btl_crew_labor", 9_000_000.0)]
    reg = _reg(rows, ny_atl_producer_role_by_line={"L0": 1, "L1": 1}, ny_atl_payee_by_line={"L0": 1, "L1": 2})
    assert _sum(reg, G, "producer election") == 380_000.0 and _sum(reg, Q, line="L0") == 0.0 and _sum(reg, Q, line="L1") == 0.0
    same_person = _reg(rows, ny_atl_producer_role_by_line={"L0": 1, "L1": 1}, ny_atl_payee_by_line={"L0": 1, "L1": 1})
    assert _sum(same_person, G) == 0.0 and _sum(same_person, Q, line="L0") == 200_000.0


def test_stated_line_facts_become_the_derived_numeric_facts_and_production_facts():
    rows = [R(fact_key="line_fact:a:composer_compensation_usd", value="350000"), R(fact_key="line_fact:a:producer_role", value="line"),
            R(fact_key="line_fact:b:producer_role", value="not-a-role"), R(fact_key="line_fact:c:composer_compensation_usd", value="nan"),
            R(fact_key="line_fact:zz:producer_role", value="executive")]
    got = payee_amount_facts(rows, {"a", "b", "c"})
    assert got == {FACT_COMPOSER_PREFIX + "a": 350_000.0, FACT_PRODUCER_ROLE_PREFIX + "a": 2.0}
    pf = limits_facts_from_amount_facts({**got, FACT_PAYEE_PREFIX + "a": 1.0})
    assert pf["ny_atl_composer_by_line"] == (("a", 350_000.0),) and pf["ny_atl_producer_role_by_line"] == (("a", 2),) and pf["ny_atl_payee_by_line"] == (("a", 1),)


# ── DR-01: sequential saves of mutually exclusive elections ───────────────────────────────────────────────────────────────

PAIRS = (("ny_post_facility_outside_mctd", "ny_post_facility_inside_mctd"), ("ny_production_plus_10pct_tier", "ny_production_plus_5pct_tier"))


async def _stored(db, pid):
    """Cold read: a fresh SELECT of the stored rows, then the same parser the evaluation input assembly uses."""
    rows = (await db.execute(select(ProjectFact).where(ProjectFact.project_id == pid))).scalars().all()
    return rows, _evidenced_program_facts(rows)


@pytest.mark.asyncio
@pytest.mark.parametrize("first,second", PAIRS + tuple((b, a) for a, b in PAIRS))
async def test_a_later_save_replaces_the_contradictory_partner_atomically(first, second):
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU")
        await write_ny_program_facts(db, pid, evidenced={first: True})
        assert (await _stored(db, pid))[1] == {first}
        result = await write_ny_program_facts(db, pid, evidenced={second: True})
        rows, evidenced = await _stored(db, pid)
        assert evidenced == {second} and result["replaced"] == [first], "both contradictory elections must never be stored"
        row = next(r for r in rows if r.fact_key == "evidenced_program_fact:" + second)
        assert row.source_type == ProjectFactSourceType.USER_OVERRIDE.value and row.review_status == ReviewStatus.APPROVED.value, "producer provenance is kept"
        # Reset: null clears to Unknown, and Unknown stays distinct from a stored false (a false is rejected, never stored)
        await write_ny_program_facts(db, pid, evidenced={second: None})
        assert (await _stored(db, pid))[1] == set()
        with pytest.raises(ValueError):
            await write_ny_program_facts(db, pid, evidenced={first: True, second: True})
        with pytest.raises(ValueError):
            await write_ny_program_facts(db, pid, evidenced={first: False})
        assert (await _stored(db, pid))[1] == set(), "a rejected save writes nothing"


@pytest.mark.asyncio
async def test_producer_role_and_composer_portion_saves_validate_and_persist():
    from app.models.budget import BudgetDocument, BudgetLineItem
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU")
        rows = (await db.execute(select(BudgetLineItem.id, BudgetLineItem.amount_usd).join(
            BudgetDocument, BudgetDocument.id == BudgetLineItem.budget_document_id).where(BudgetDocument.project_id == pid).limit(1))).all()
        lid, amount = str(rows[0][0]), float(rows[0][1])
        await write_ny_program_facts(db, pid, producer_roles=[{"line_id": lid, "role": "executive"}], composer_portions=[{"line_id": lid, "amount_usd": amount / 2}])
        stored, _ = await _stored(db, pid)
        by_key = {r.fact_key: r.value for r in stored}
        assert by_key[f"line_fact:{lid}:producer_role"] == "executive" and float(by_key[f"line_fact:{lid}:composer_compensation_usd"]) == amount / 2
        for bad in (dict(producer_roles=[{"line_id": lid, "role": "co-producer"}]), dict(composer_portions=[{"line_id": lid, "amount_usd": amount * 2}]),
                    dict(composer_portions=[{"line_id": "00000000-0000-0000-0000-000000000000", "amount_usd": 1.0}])):
            with pytest.raises(ValueError):
                await write_ny_program_facts(db, pid, **bad)
        await write_ny_program_facts(db, pid, producer_roles=[{"line_id": lid, "role": None}], composer_portions=[{"line_id": lid, "amount_usd": None}])
        assert not [r for r in (await _stored(db, pid))[0] if r.fact_key.startswith("line_fact:")]
