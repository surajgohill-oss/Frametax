"""Lips Like Sugar North American hybrids, reconciled on an ISOLATED COPY of the saved inputs (tests/data/lls_saved_inputs.json, a read-only export; nothing reaches the real project) against
independent arithmetic from the raw budget lines: allocation, eligible spend and labour, the California project gate, stacking assistance, contingency applied once, and NPC.
Expectations are computed here from the lines, never from the engine; the displayed (stale canonical-1.110.0) figures are fixtures only for the displayed-to-corrected bridges.
Assumptions (explicit): the saved LLS facts carry no contingency election (NOT_STATED); every budget line outside finance costs, the contingency line and the residuals reserve is treated
as an eligible Manitoba production expenditure (the cost-of-production base); Manitoba labour excludes payroll fringes (the readings that include them are also tested: the cost credit wins either way)."""
from __future__ import annotations

import dataclasses

import pytest

from app.api.v1.cineglobe import ProjectAssumptions, post_project_assumptions
from app.services import canonical_evaluation as ce
from app.services.canonical_program_identity import alias_memo_scope
from tests.isolated_records import isolated_session, served_structures
from tests.lls_isolated_copy import create_lls_copy, saved_inputs

pytestmark = pytest.mark.asyncio

NA = {"US-CA", "CA-MB", "CA-ON", "CA-BC", "CA-AB", "CA"}
DATA = saved_inputs()
LINES = DATA["lines"]
STALE = DATA["displayed_stale_generation"]
MB_PRINCIPAL_CA_VFX, MB_AB_CA_MUSIC = "9656c441-881e-4667-bec1-8841387408ce", "535cc009-0457-4cde-94d8-608caeb5f6f1"


def usd(x):
    return round(float(x), 2)


def _sum(pred):
    return usd(sum(float(r["amount_usd"]) for r in LINES if pred(r)))


GROSS = _sum(lambda r: True)
FINANCE = _sum(lambda r: r["spend_category"] == "finance_costs")
RESERVE = _sum(lambda r: r["spend_category"] == "contingency")
RESIDUALS = _sum(lambda r: r["spend_category"] == "residuals_reserve")
MB_BASE = usd(GROSS - FINANCE - RESERVE - RESIDUALS)
LABOUR_EXCL_FRINGES = _sum(lambda r: r["is_labor"] and r["spend_category"] != "payroll_fringes")
LABOUR_ALL = _sum(lambda r: r["is_labor"])
VFX = _sum(lambda r: r["spend_category"] == "vfx")
MUSIC = _sum(lambda r: r["spend_category"] == "music")


async def _evaluate(db, monkeypatch, *, election=None):
    real = ce.discover_executable_jurisdictions

    def bounded(*a, **k):
        d = real(*a, **k)
        return dataclasses.replace(d, accepted=tuple((c, sl) for c, sl in d.accepted if c in NA), examinations=tuple(e for e in d.examinations if e.jurisdiction_code in NA))
    monkeypatch.setattr(ce, "discover_executable_jurisdictions", bounded)
    pid = await create_lls_copy(db)
    if election is not None:
        await post_project_assumptions(pid, ProjectAssumptions(answers={"contingency_expected_utilization_pct": election}), db)
    with alias_memo_scope():
        await ce.evaluate_project(db, pid)
    return pid, [e for e in await served_structures(db, pid) if e["candidate_status"] == "PRICED"]


def _find(entries, *, label_starts=None, label_has=None, participants=None, slugs=None):
    hits = [e for e in entries if (label_starts is None or (e.get("label") or "").startswith(label_starts)) and (label_has is None or label_has in (e.get("label") or ""))
            and (participants is None or e.get("participants") == participants)
            and (slugs is None or {s["program_slug"] for s in e.get("segments", [])} == set(slugs))]
    assert len(hits) == 1, (label_starts, label_has, participants, slugs, len(hits))
    return hits[0]


def test_the_independent_inputs_are_the_saved_lls_budget():
    assert (GROSS, FINANCE, RESERVE, RESIDUALS, MB_BASE) == (11_983_654.0, 1_700_000.0, 400_000.0, 400_000.0, 9_483_654.0)
    assert (LABOUR_EXCL_FRINGES, VFX, MUSIC) == (2_935_298.0, 40_000.0, 206_774.0)
    assert not any(f[0].startswith("contingency_expected") for f in DATA["facts"]), "no saved contingency election exists; none is invented"


async def test_displayed_baseline_leader_is_unchanged_and_manitoba_relocation_is_the_cost_of_production_credit(monkeypatch):
    async with isolated_session() as db:
        _, entries = await _evaluate(db, monkeypatch)
    base = next(e for e in entries if e.get("is_baseline"))
    assert usd(base["npc_with_adjustments_usd"]) == STALE["leader_baseline_npc_usd"] == usd(GROSS - STALE["baseline_incentive_usd"]), "the displayed leader is reproduced by the current engine"
    mb = _find(entries, label_starts="Full relocation to Manitoba", participants=["CA-MB"])
    cost_credit, labour_credit = usd(0.30 * MB_BASE), usd(0.45 * LABOUR_EXCL_FRINGES)
    assert labour_credit < cost_credit and usd(0.45 * LABOUR_ALL) < cost_credit, "the cost credit is the election under either labour reading"
    seg = mb["segments"][0]
    assert (usd(seg["qpe_usd"]), usd(seg["incentive_floor_usd"])) == (MB_BASE, cost_credit)
    assert usd(seg["incentive_ceiling_usd"]) == usd(0.38 * MB_BASE), "30% plus the 8% production-company bonus bound"
    assert usd(mb["npc_with_adjustments_usd"]) == usd(GROSS - cost_credit) == 9_138_557.80, "NOT_STATED: planned cost is the full gross"
    assert seg["rate_floor"] == pytest.approx(0.30) and usd(seg["rate_floor"] * seg["qpe_usd"]) == cost_credit, "the floor rate is the elective credit's rate, not the labour credit's 45%"


async def test_manitoba_component_segments_report_the_elective_rate_and_the_dollars_agree(monkeypatch):
    async with isolated_session() as db:
        _, entries = await _evaluate(db, monkeypatch)
    ca_anchor_vfx_to_mb = _find(entries, label_starts="California anchor — vfx routed to Manitoba", participants=["US-CA", "CA-MB"])
    mb_seg = next(s for s in ca_anchor_vfx_to_mb["segments"] if s["jurisdiction_code"] == "CA-MB")
    assert usd(mb_seg["incentive_floor_usd"]) == usd(0.30 * VFX) == 12_000.0
    assert mb_seg["rate_floor"] == pytest.approx(0.30), "a component with no labour reported a 0% floor rate beside a 12,000 floor"
    ca_seg = next(s for s in ca_anchor_vfx_to_mb["segments"] if s["jurisdiction_code"] == "US-CA")
    base = ca_anchor_vfx_to_mb
    assert usd(base["npc_with_adjustments_usd"]) == usd(GROSS - usd(ca_seg["incentive_floor_usd"]) - 12_000.0)


async def test_manitoba_with_vfx_in_alberta_prices_each_leg_on_its_own_allocation(monkeypatch):
    async with isolated_session() as db:
        _, entries = await _evaluate(db, monkeypatch)
    e = next(x for x in entries if (x.get("label") or "").startswith("Manitoba (Manitoba Film & Video Production Tax Credit) + vfx->Alberta") and x.get("participants") == ["CA-MB", "CA-AB"])
    expected = usd(0.30 * (MB_BASE - VFX) + 8_800.0)          # Manitoba on its remaining base; Alberta's own leg on the 40,000 VFX
    assert usd(e["total_incentive_floor_usd"]) == expected == 2_841_896.20
    assert usd(e["npc_with_adjustments_usd"]) == usd(GROSS - expected) == 9_141_757.80


async def test_the_federal_pstc_with_manitoba_nets_the_manitoba_labour_share_and_discloses_the_whole_credit_lower_bound(monkeypatch):
    async with isolated_session() as db:
        _, entries = await _evaluate(db, monkeypatch)
    e = _find(entries, label_starts="Manitoba — Canada Federal Production Services Tax Credit (PSTC)", participants=["CA-MB"], slugs={"ca_federal_pstc", "ca_mb_film_video_credit"})
    mb_credit = usd(0.30 * MB_BASE)
    pstc_original = usd(0.16 * LABOUR_EXCL_FRINGES)
    labour_part = usd(min(mb_credit, 0.30 * LABOUR_EXCL_FRINGES))            # ITA 125.5(1): the part of the credit reasonably in respect of labour = rate x labour, bounded by the credit
    pstc = usd(pstc_original - 0.16 * labour_part)
    whole_credit_pstc = usd(pstc_original - 0.16 * min(mb_credit, LABOUR_EXCL_FRINGES))
    assert (labour_part, pstc, whole_credit_pstc) == (880_589.40, 328_753.38, 14_432.29)
    by_slug = {s["program_slug"]: usd(s["incentive_floor_usd"]) for s in e["segments"]}
    assert by_slug["ca_mb_film_video_credit"] == mb_credit and by_slug["ca_federal_pstc"] == pstc
    assert usd(e["npc_with_adjustments_usd"]) == usd(GROSS - mb_credit - pstc) == 8_809_804.42
    assert any("Apportionment assumption" in w and "$14,432" in w for w in e["warnings"]), "the apportionment is an assumption and the whole-credit lower bound is disclosed"


async def test_the_cptc_legs_keep_their_numbers_and_now_disclose_the_certification_and_control_assumption(monkeypatch):
    async with isolated_session() as db:
        _, entries = await _evaluate(db, monkeypatch)
    cptc_only = _find(entries, label_starts="Full relocation to Canada (Canadian Film or Video Production Tax Credit (CPTC))", participants=["CA"])
    stack = _find(entries, label_starts="Manitoba — Canadian Film or Video Production Tax Credit (CPTC) + Manitoba", participants=["CA-MB"], slugs={"ca_federal_cptc", "ca_mb_film_video_credit"})
    cptc = usd(0.25 * LABOUR_EXCL_FRINGES)
    assert cptc == 733_824.50 and usd(cptc_only["segments"][0]["incentive_floor_usd"]) == cptc
    assert usd(stack["npc_with_adjustments_usd"]) == usd(GROSS - usd(0.30 * MB_BASE) - cptc) == 8_404_733.30
    for e in (cptc_only, stack):
        assert any("Planning assumption, not a certification: the CPTC" in w for w in e["warnings"]), e["label"]
    assert any("the CPTC is the federal credit" in n for n in cptc_only["segments"][0]["notes"])


async def test_manitoba_principal_with_a_california_leg_is_rejected_by_the_california_project_gate_never_priced(monkeypatch):
    async with isolated_session() as db:
        _, entries = await _evaluate(db, monkeypatch)
    priced = [e for e in entries if (e.get("label") or "").startswith("Manitoba (") and "California" in (e.get("label") or "")]
    assert priced == [], "40,000 of 11,983,654 is 0.334% of the budget, and the modeled shoot has no California principal-photography days"


async def test_contingency_is_applied_once_to_every_priced_candidate_and_never_when_not_stated(monkeypatch):
    async with isolated_session() as db:
        _, none = await _evaluate(db, monkeypatch)
    async with isolated_session() as db:
        _, half = await _evaluate(db, monkeypatch, election=50)
    index = {(e["label"], tuple(e["participants"])): e for e in half}
    assert len(none) == len(half) > 50
    for e in none:
        h = index[(e["label"], tuple(e["participants"]))]
        assert usd(e["npc_with_adjustments_usd"]) - usd(h["npc_with_adjustments_usd"]) == pytest.approx(0.5 * RESERVE, abs=0.011), e["label"]
        assert usd(e["selected_incentive_usd"] or 0) == usd(h["selected_incentive_usd"] or 0), "an election never changes an incentive"


def test_the_displayed_to_corrected_bridges_close_to_the_cent():
    s1, s2 = STALE["structures"][MB_PRINCIPAL_CA_VFX], STALE["structures"][MB_AB_CA_MUSIC]
    cost_credit_on = lambda base: usd(0.30 * base)
    # displayed Manitoba-principal / California-VFX hybrid -> same-allocation sensitivity -> relocated all-Manitoba -> with the federal PSTC (whole-credit lower bound 14,432.29; labour-share netting 328,753.38)
    mb_alloc_base = usd(s1["allocations"][0][2] - FINANCE - RESERVE - RESIDUALS)
    assert mb_alloc_base == 9_443_654.0 and s1["component_incentives_usd"]["ca_mb_film_video_credit"] == usd(0.45 * mb_alloc_base) == 4_249_644.30, "the stale generation priced 45% on the all-spend base"
    step_basis = usd(s1["component_incentives_usd"]["ca_mb_film_video_credit"] - cost_credit_on(mb_alloc_base))
    step_ca = usd(s1["component_incentives_usd"]["ca_film_30"])
    sensitivity = usd(s1["npc_usd"] + step_basis + step_ca)
    assert (step_basis, step_ca, sensitivity) == (1_416_548.10, 14_000.0, 9_150_557.80) == (step_basis, step_ca, usd(GROSS - cost_credit_on(mb_alloc_base)))
    assert usd(sensitivity - usd(0.30 * VFX)) == 9_138_557.80 == usd(GROSS - cost_credit_on(MB_BASE))
    assert usd(9_138_557.80 - 14_432.29) == 9_124_125.51 and usd(9_138_557.80 - 328_753.38) == 8_809_804.42
    # displayed Manitoba / Alberta-VFX / California-music hybrid -> same-allocation sensitivity -> music kept in Manitoba
    base2 = usd(s2["allocations"][1][2] - FINANCE - RESERVE - RESIDUALS)
    assert base2 == 9_236_880.0 and usd(s2["component_incentives_usd"]["ca_mb_film_video_credit"]) == usd(0.45 * base2) == 4_156_596.0
    step_basis2, step_music = usd(4_156_596.0 - cost_credit_on(base2)), usd(s2["component_incentives_usd"]["ca_film_30"])
    sensitivity2 = usd(s2["npc_usd"] + step_basis2 + step_music)
    assert (step_basis2, step_music, sensitivity2) == (1_385_532.0, 72_370.90, 9_203_790.0)
    assert usd(sensitivity2 - cost_credit_on(MUSIC)) == 9_141_757.80, "the current engine's Manitoba + Alberta-VFX candidate"
