"""Builder for the North America executable-coverage matrix (NA-RECONCILIATION-12, third pass).

One row per canonical NA program (60) and one per same-scope stacking pair. A program row says, from synthetic evidence only:
  discovery   -- what production discovery does with it for a feature film (classification, whether capability data exists);
  kernel      -- the segment pricing kernel (price_segment) on a fixed synthetic budget, compared with an expectation PINNED from the cited source (rate x base), never read back from the code;
  served      -- whether the full pipeline (evaluate_project) serves it: a retained row, or only inside a bounded-retention aggregate group, with its status and certainty;
  stacking    -- every same-scope partner, the registered rule type and the structural generator's outcome for the pair;
  path        -- EXECUTABLE_GUARANTEED | EXECUTABLE_POTENTIAL_ONLY (zero guaranteed, ceiling shown) | NOT_EXECUTABLE_WITH_REASON;
  exclusion   -- the exact reason when a program legitimately has no executable path on the proof budget;
  proof       -- the focused synthetic proof (the test that builds this matrix and asserts every row).
Deterministic: no ids, times or database keys appear in the output.
"""
from __future__ import annotations

import itertools
import uuid

from sqlalchemy import select

from app.calculators.allocation_pricing import price_segment
from app.calculators.canonical_stack_bridge import load_named_pair_rule
from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.calculators.production_discovery import discover_executable_jurisdictions
from app.calculators.production_requirements import derive_production_requirements
from app.calculators.structural_archetype_generator import generate_structural_candidate
from app.data.executable_jurisdiction_registry import get_doctrine
from app.models.production import EvaluationCandidateAggregate
from app.services import na_canonical_reconciliation as na
from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS, evaluate_project
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures
from tests.test_na_stack_and_gate_repairs_controls import _alloc as _salloc, _comp as _scomp

#: (account, description, spend category, atl/btl/post, amount) -- the standard synthetic budget (total 3,000,000: labour 2,000,000 = cast 600,000 + crew 1,400,000).
P1_LINES = (("1000", "ABOVE THE LINE CAST", "atl_cast", "atl", 600_000.0), ("3100", "CREW", "btl_crew_labor", "btl", 1_400_000.0),
            ("3200", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 700_000.0), ("5000", "POST SOUND", "sound", "post", 300_000.0))
#: the animation / effects / post-heavy budget (total 4,400,000): P1 + 500,000 of VFX + 900,000 of post finishing (post total 1,200,000).
P2_LINES = P1_LINES + (("4200", "VISUAL EFFECTS", "vfx", "post", 500_000.0), ("5100", "POST FINISHING", "sound", "post", 900_000.0))
PROFILES = {"P1": P1_LINES, "P2": P2_LINES}
HOME = "US-TX"

#: programs proven on P2 (their base is VFX / post spend that P1 does not hold)
P2_PROGRAMS = frozenset({"ca_bc_dave", "ontario_computer_animation_and_special_effects_tax_credit_ocase", "us_ny_post_production_credit"})

#: PINNED expectations: slug -> (guaranteed USD, potential USD, basis). Each is rate x base from the program's cited source on the fixed budget; None = not pinned (the observed value is
#: recorded and flagged OBSERVED_ONLY). Labour = cast 600,000 + crew 1,400,000 = 2,000,000; "all" = 3,000,000.
EXPECT: dict[str, tuple[float | None, float | None, str]] = {
    "ca_ab_fttc": (660_000.0, 900_000.0, "22% x all 3,000,000; 30% (ownership criteria) potential"),
    # Restated in NA-RECONCILIATION-16 (the potential gained the statutory shooting-day bounds): QLE = 1,800,000; guaranteed 35% = 630,000; potential 40% (photography after 2024, s.80(8)) + regional 12.5% (s.81.1) +
    # distant location 6% (s.81.11) at the day ratio's upper bound of 1 = 58.5% x 1,800,000 = 1,053,000. Training and scriptwriting exist only by application and add nothing until their prerequisite is stated.
    "ca_bc_film_tv_tax_credit": (630_000.0, 1_053_000.0, "35% x min(labour 2,000,000; 60% x cost 3,000,000 = 1,800,000); potential 40% (s.80, s.79(1)) + regional 12.5% (s.81.1) + distant 6% (s.81.11) at ratio 1 on QLE"),
    "ca_bc_pstc": (720_000.0, 960_000.0, "36% x labour 2,000,000; +12% regional/distant potential"),
    "ca_federal_cptc": (450_000.0, 450_000.0, "25% x min(labour 2,000,000; 60% x cost 3,000,000 = 1,800,000)"),
    "ca_federal_pstc": (320_000.0, 320_000.0, "16% x labour 2,000,000"),
    "ca_film_30": (840_000.0, None, "35% x 2,400,000 (above-the-line cast excluded); uplift potential not pinned"),
    "ca_mb_film_video_credit": (900_000.0, 1_300_000.0, "45% x labour 2,000,000; 65% with the three bonuses"),
    # Restated in NA-RECONCILIATION-19: the potential now allows the statutory eligible deemed spend (up to 15% of eligible NB spend added to the base, LIFT 2026/2027 Guidelines): 35% x (3,000,000 x 1.15) = 1,207,500.
    "ca_nb_film_tax_credit": (0.0, 1_207_500.0, "discretionary LIFT grant: guaranteed 0; 35% x 3,000,000 x 1.15 (up to 15% deemed spend) potential"),
    # Saskatchewan (NA-RECONCILIATION-19): out of the B1 display-only ruling; potential-only, bounded at the 40% combined cap (Saskatchewan Stream) = 40% x 3,000,000.
    "ca_sk_creative_saskatchewan_grant": (0.0, 1_200_000.0, "discretionary FFTV grant: guaranteed 0; 25% base + Saskatchewan Stream 5 + bonuses 5/5/10, capped at 40% x 3,000,000"),
    "ca_nl_all_spend_credit": (1_200_000.0, 1_200_000.0, "40% x all 3,000,000"),
    # Restated in NA-RECONCILIATION-17 (the potential gained the Nova Scotia bounds): guaranteed 25% x 3,000,000 = 750,000; potential adds the Location Incentive 2 points and the Distant Location
    # maximum of 10 points on the same 3,000,000 (NSFPIF Guidelines s.6.2) = 37% x 3,000,000 = 1,110,000.
    # Restated again in NA-RECONCILIATION-18: potential 25 + Location 2 + Distant 10 + Stream I 1 + Shooting Length 1 + performers 1.5 + three-of-seven 1.5 = 42% x 3,000,000 = 1,260,000.
    "ca_ns_production_incentive_fund": (750_000.0, 1_260_000.0, "25% x all 3,000,000 (Stream II); potential 42% = +2 Location, +10 Distant Location, +1 Stream I, +1 Shooting Length, +1.5 +1.5 Content"),
    "ca_qc_pstc": (750_000.0, 750_000.0, "25% x all 3,000,000"),
    "mx_federal_film_incentive_2026": (0.0, 900_000.0, "committee-set percentage: guaranteed 0; 30% x all 3,000,000 potential (cap not binding)"),
    "ny_state_film": (900_000.0, 1_200_000.0, "30% x all 3,000,000; 40% with the 10% upstate adder potential"),
    "on_ofttc": (700_000.0, 900_000.0, "35% x labour 2,000,000; +10% regional potential"),
    "on_opstc": (645_000.0, 645_000.0, "21.5% x all 3,000,000"),
    "us_al_film_incentive": (750_000.0, 950_000.0, "25% x all 3,000,000; +10% x labour 2,000,000 (35% resident payroll) potential"),
    "us_ar_digital_motion_picture_incentive": (0.0, 900_000.0, "sole-discretion award: guaranteed 0; 30% x all 3,000,000 potential"),
    "us_az_motion_picture_production": (450_000.0, 600_000.0, "15% x all 3,000,000; 20% potential"),
    "us_co_film_incentive": (600_000.0, 600_000.0, "20% x all 3,000,000"),
    "us_co_film_income_tax_credit": (0.0, 660_000.0, "office-reserved amount: guaranteed 0; 22% x all 3,000,000 potential"),
    "us_ct_film_tax_credit": (900_000.0, 900_000.0, "30% x all 3,000,000 (over USD 1,000,000)"),
    "us_ga_film_credit": (600_000.0, 900_000.0, "20% x all 3,000,000; 30% potential"),
    "us_hi_film_digital_media_credit": (660_000.0, 810_000.0, "22% x all 3,000,000; 27% potential"),
    "us_il_film_production_services_credit": (1_050_000.0, 1_050_000.0, "35% x all 3,000,000"),
    "us_ky_keiia": (900_000.0, 1_050_000.0, "30% x all 3,000,000; 35% potential"),
    "us_la_film_incentive": (750_000.0, 1_200_000.0, "25% x all 3,000,000; 40% potential"),
    "us_ma_film_tax_credit": (750_000.0, 750_000.0, "25% x all 3,000,000"),
    "us_md_film_production_activity_credit": (0.0, 900_000.0, "discretionary ceiling: guaranteed 0; 30% x all 3,000,000 potential"),
    "us_mn_film_production_credit": (750_000.0, 750_000.0, "25% x all 3,000,000"),
    # NA-RECONCILIATION-22: this pin is the KERNEL figure with no scenario (nothing about the shoot stated: 20% guaranteed). The served full-relocation structure prices 750,000 because the scenario places
    # 100% of principal photography in Missouri, so the 50% filming test is scenario-assumed met (25% x 3,000,000); the matrix's PRICED columns record that.
    "us_mo_motion_media_production_tax_credit": (600_000.0, 1_260_000.0, "20% x all 3,000,000; 42% maximum potential"),
    "us_ms_advantage_film_program": (750_000.0, 750_000.0, "25% x all 3,000,000"),
    # Restated in NA-RECONCILIATION-19: compensation is not a 'production expenditure' (MCA 15-31-1003(13)(b)(i)) and earns its own category credits, and every addition is limited to 35% of base investment (15-31-1007(3)(a)):
    # unknown inputs are bounded by that ceiling = 35% x 3,000,000 = 1,050,000 (20% base on 1,000,000 + up to 30% on 2,000,000 compensation + additions, clipped).
    "us_mt_media_act_tax_credit": (0.0, 1_050_000.0, "certification paused, no credit before 2031 expenditures: guaranteed 0; 35% x 3,000,000 combined ceiling potential"),
    "us_nc_film_entertainment_grant": (0.0, 750_000.0, "discretionary ceiling: guaranteed 0; 25% x all 3,000,000 potential"),
    "us_nj_garden_state_film_credit": (900_000.0, 1_050_000.0, "30% x all 3,000,000; 35% outside the radius potential"),
    "us_nm_film_credit": (750_000.0, 1_200_000.0, "25% x all 3,000,000; 40% potential"),
    "us_nv_film_credit": (450_000.0, 750_000.0, "15% x all 3,000,000; 25% potential"),
    "us_ny_empire_state_independent_film_credit": (900_000.0, 1_200_000.0, "30% x all 3,000,000; +10% adders potential"),
    "us_oh_motion_picture_tax_credit": (900_000.0, 900_000.0, "30% x all 3,000,000 (over USD 300,000)"),
    "us_ok_film_enhancement_rebate": (600_000.0, 900_000.0, "20% x all 3,000,000; 30% potential"),
    "us_or_opif": (None, None, "payroll / other split not pinned independently"),
    "us_pa_film_production_credit": (750_000.0, 900_000.0, "25% x all 3,000,000; 30% potential"),
    "us_pr_film_incentives_act": (600_000.0, 1_200_000.0, "20% x all 3,000,000; 40% potential"),
    "us_ri_film_credit": (900_000.0, 900_000.0, "30% x all 3,000,000"),
    "us_sc_film_production_credit": (0.0, 900_000.0, "discretionary ceiling: guaranteed 0; 30% x all 3,000,000 potential"),
    "us_tn_performance_grant": (750_000.0, 750_000.0, "25% x all 3,000,000"),
    "us_tx_miip": (0.0, 930_000.0, "no award stated: guaranteed 0; 31% x all 3,000,000 potential"),
    "us_ut_motion_picture_incentive": (600_000.0, 750_000.0, "20% x all 3,000,000; 25% potential"),
    "us_va_motion_picture_credit": (450_000.0, 450_000.0, "15% x all 3,000,000"),
    "us_wa_motion_picture_competitiveness": (900_000.0, 1_350_000.0, "30% x all 3,000,000; 45% potential"),
    "us_wv_film_production_tax_credit": (810_000.0, 930_000.0, "27% x all 3,000,000; 31% (10 resident hires) potential"),
}
#: P2 expectations (VFX / post heavy; total 4,400,000)
EXPECT_P2: dict[str, tuple[float | None, float | None, str]] = {
    "ca_bc_dave": (80_000.0, 80_000.0, "16% x VFX labour 500,000 (ITA (BC) s.81.2(2): labour directly attributable to animation / visual effects)"),
    "ontario_computer_animation_and_special_effects_tax_credit_ocase": (90_000.0, 90_000.0, "18% x VFX labour 500,000"),
    "us_ny_post_production_credit": (None, None, "35% x post spend (outside the district) / 30% inside; the fact-dependent split is not pinned"),
}

#: exact reasons a program has no executable path on the proof budget (everything else must execute)
EXCLUSIONS: dict[str, str] = {
    "bc_interactive_digital_media_tax_credit_idmtc": "COVERAGE_ONLY: no RateRule (rate, base and cap not established); an interactive-media credit with no film-production base.",
    "ca_cmf": "NON_GUARANTEED_SELECTIVE (NA-RECONCILIATION-13): the CMF Convergent Stream pays through Broadcaster and Distributor Envelopes allocated by past performance (cmf-fmc.ca envelope administration); a producer reaches it "
              "only through a broadcaster or distributor commitment, and no producer-level rate exists, so nothing is priced.",
    "mx_eficine_incentive": "NON_GUARANTEED_SELECTIVE (NA-RECONCILIATION-13): LISR art. 189 (not art. 226) is an INVESTOR credit allocated by an interinstitutional committee within MXN 650 million a year (two periods), MXN 20 million per "
                            "contributor and project, 10% of the prior-year income tax; the producer's benefit is financing. The 30% federal incentive is the canonical Mexico program (mx_federal_film_incentive_2026).",
    "nohfc_production_fund": "NON_GUARANTEED_SELECTIVE (NA-RECONCILIATION-13): competitive intake; a conditional contribution of up to 50% of eligible Northern Ontario costs capped CAD 500,000 (budget under 5 million), 1,000,000 "
                             "(5-10 million) and 2,000,000 (10 million and over); the Board decides and funding is limited, so no guaranteed value.",
    "us_itvs_fund": "NON_GUARANTEED_SELECTIVE (NA-RECONCILIATION-13): ITVS Open Call is a co-production agreement (up to USD 400,000 for features, USD 50,000 for shorts), 'not a grant'; no current ITVS 'International Documentary Fund' page was found.",
    "us_sundance_doc": "NON_GUARANTEED_SELECTIVE (NA-RECONCILIATION-13): annual open call, about 20-30 of 1,300 proposals funded, grants of USD 25,000-40,000 (development) and USD 50,000-100,000 (production and post), non-recoupable.",
    "ca_telefilm_dev": "NON_GUARANTEED_SELECTIVE (NA-RECONCILIATION-13): Telefilm Canada Production Program Guidelines (applicable October 31, 2025) s.4.1 cap financing at the lesser of 49% of eligible Canadian costs or CAD 500,000 (budgets under "
                       "1.5 million), one third (1.5-3.5 million), the lesser of 49% or CAD 3.5 million (French) / 4 million (other) from 3.5 million, and s.8 states compliance does not guarantee funding.",
    "ca_bell_fund": "NON_GUARANTEED_SELECTIVE (NA-RECONCILIATION-13): the Bell Fund Production Program is a Selective stream (and a Major Production Funder stream) for Canadian series in eligible genres; amounts are not stated on the program page.",
}
#: per-profile exclusions: program has no executable path on THAT budget but is proven on the other
PROFILE_EXCLUSIONS: dict[tuple[str, str], str] = {
    ("ca_bc_dave", "P1"): "P1 holds no digital animation or visual effects labour; DAVE's base is BC labour directly attributable to those activities (ITA (BC) s.81.2(2)), so the base is 0. Proven on P2.",
    ("ontario_computer_animation_and_special_effects_tax_credit_ocase", "P1"): "P1 holds no VFX / animation spend; OCASE's base is eligible computer animation and special effects labour, so the base is 0. Proven on P2.",
    ("us_ny_post_production_credit", "P1"): "P1 post spend is 300,000 and the credit's minimum is USD 1,000,000 of post-production costs (Tax Law 31(a)). Proven on P2 (post 1,200,000 + VFX 500,000).",
}


def _is_na(code: str) -> bool:
    return na.is_na_code(code) if hasattr(na, "is_na_code") else code.split("-")[0] in {"US", "CA", "MX"}


def _universe():
    u = na.frozen_universe()
    return sorted(u["rate_bearing"]), sorted(u["coverage_only"])


def _jurisdiction(slug: str) -> str:
    d = get_doctrine(slug)
    return d.jurisdiction_code if d is not None else ""


def _kernel_allocations(lines, code):
    return [AccountAllocation(account_code=a, description=d, amount_usd=amt, component="production", jurisdiction_code=code, assignment_kind=AssignmentKind.FIXED,
                              rationale="NA coverage matrix", governing_decision="na-coverage-matrix", line_id=f"L{a}", spend_category=cat) for a, d, cat, _, amt in lines]


def kernel_standalone(slug: str, lines):
    code = _jurisdiction(slug)
    allocs = _kernel_allocations(lines, code)
    fx = None
    if code == "MX":
        from tests.test_us_ca_mx_scope_integrity_controls import _fx
        fx = _fx(MXN=20.0)
    seg = price_segment(jurisdiction_code=code, program_slug=slug, allocations=allocs, spend_category_by_code={a.account_code: a.spend_category for a in allocs},
                        offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=sum(a.amount_usd for a in allocs), fx_context=fx,
                        evidenced_requirement_facts=frozenset(_PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS))
    return seg


def _r2(x):
    return None if x is None else round(float(x), 2)


async def _evaluate(lines):
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=lines, home_code=HOME)
        await evaluate_project(db, pid)
        rows = await served_structures(db, pid)
        aggs = (await db.execute(select(EvaluationCandidateAggregate).where(EvaluationCandidateAggregate.project_id == uuid.UUID(pid)))).scalars().all()
        agg_rows = [{"slugs": list(a.program_slugs), "status": a.candidate_status, "type": a.structure_type, "count": a.candidate_count} for a in aggs]
    return rows, agg_rows


def _served_summary(slug: str, rows, aggs) -> dict:
    mine = [r for r in rows if slug in r["program_slugs"]]
    alone = [r for r in mine if r["program_slugs"] == [slug]]
    stacks = [r for r in mine if len(r["program_slugs"]) > 1 and r["candidate_status"] == "PRICED"]
    agg = [a for a in aggs if slug in a["slugs"]]
    state = "RETAINED" if mine else ("AGGREGATED" if agg else "ABSENT")
    best = max(alone, key=lambda r: (r.get("confirmed_incentive_floor_usd") or 0.0, r.get("maximum_supported_incentive_usd") or 0.0), default=None)
    return {
        "served_state": state,
        "retained_rows": len(mine), "aggregate_groups": len(agg), "aggregated_candidates": sum(a["count"] for a in agg),
        "standalone_structure_types": sorted({r["structure_type"] for r in alone}),
        "standalone_status": best["candidate_status"] if best else None,
        "served_guaranteed_usd": _r2(best.get("confirmed_incentive_floor_usd")) if best else None,
        "served_potential_usd": _r2(best.get("maximum_supported_incentive_usd")) if best else None,
        "economics_certainty": best.get("economics_certainty") if best else None,
        "mfni_status": ((best or (mine[0] if mine else {})) or {}).get("mfni_status", {}).get("status"),
        "priced_stack_structures": len(stacks),
    }


def _scope(ja: str, jb: str) -> bool:
    return ja == jb or (ja == "CA" and jb.startswith("CA-")) or (jb == "CA" and ja.startswith("CA-"))


def _pair_components(a: str, b: str):
    comps = []
    for i, slug in enumerate((a, b)):
        code = _jurisdiction(slug)
        category = "vfx" if slug in ("ca_bc_dave", "ontario_computer_animation_and_special_effects_tax_credit_ocase") else "btl_crew_labor"
        comps.append(_scomp("principal_production", code, slug, [_salloc(str(i + 1), 2_000_000.0, "principal_production", code, f"P{i}", category)]))
    return comps


#: BC DAVE is claimable only alongside its host credit (ITA (BC) s.81.2(1)(a), s.82.3(1)(a)); a pair that names DAVE and no host gets the BC domestic credit on 200,000 of separate BC labour so the pair is a lawful structure.
_DAVE_HOSTS = ("ca_bc_film_tv_tax_credit", "ca_bc_pstc")


def _dave_host_needed(a: str, b: str) -> bool:
    return "ca_bc_dave" in (a, b) and not ({a, b} & set(_DAVE_HOSTS))


def _pair_structure(a: str, b: str):
    comps = _pair_components(a, b)
    if _dave_host_needed(a, b):
        comps.append(_scomp("principal_production", "CA-BC", "ca_bc_film_tv_tax_credit", [_salloc("9", 200_000.0, "principal_production", "CA-BC", "PH", "btl_crew_labor")]))
    return comps


def pair_rows(rate_bearing: list[str]) -> list[dict]:
    out = []
    jur = {s: _jurisdiction(s) for s in rate_bearing}
    for a, b in itertools.combinations(sorted(rate_bearing), 2):
        if not _scope(jur[a], jur[b]):
            continue
        rule = load_named_pair_rule(a, b)
        rt = rule["rule_type"] if rule else "UNRULED"
        res = generate_structural_candidate(_pair_structure(a, b), gross_budget_usd=4_200_000.0 if _dave_host_needed(a, b) else 4_000_000.0)
        adj = [x for x in res.stacking_adjustments if x.adjustment_usd]
        out.append({
            "row_kind": "PAIR", "program_a": a, "program_b": b, "jurisdictions": f"{jur[a]} + {jur[b]}", "rule_type": rt,
            "host_added": _dave_host_needed(a, b), "executable": bool(res.executable), "guaranteed_usd": _r2(res.total_guaranteed_incentive_usd), "conditional_usd": _r2(res.total_conditional_incentive_usd),
            "netting_adjustments": [{"reducer": x.program_a_id, "reduced": x.program_b_id, "usd": _r2(x.adjustment_usd), "basis": x.description.split(":", 1)[0]} for x in adj],
            "reason": (res.rejection_reason or "")[:240],
        })
    return out


async def build() -> dict:
    rate_bearing, coverage_only = _universe()
    u = na.frozen_universe()
    rec = discover_executable_jurisdictions(requirements=derive_production_requirements({}), production_type="feature_film", qpe_usd=3_000_000.0, home_code=HOME,
                                            evidenced_facts=frozenset(_PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS))
    exam = {(e.jurisdiction_code, e.program_slug): e for e in rec.examinations}
    served = {name: await _evaluate(lines) for name, lines in PROFILES.items()}
    pairs = pair_rows(rate_bearing)
    pair_by_slug: dict[str, list[dict]] = {}
    for p in pairs:
        pair_by_slug.setdefault(p["program_a"], []).append(p)
        pair_by_slug.setdefault(p["program_b"], []).append(p)
    rows = []
    for slug in rate_bearing + coverage_only:
        code = _jurisdiction(slug)
        row = {"row_kind": "PROGRAM", "canonical_slug": slug, "layer": "RATE_BEARING" if slug in rate_bearing else "COVERAGE_ONLY", "jurisdiction": code}
        if slug in coverage_only:
            row.update({"discovery": "NOT_EXAMINED (no RateRule)", "proof_profile": "", "kernel_executable": False, "kernel_guaranteed_usd": None, "kernel_potential_usd": None,
                        "expected_guaranteed_usd": None, "expected_potential_usd": None, "expectation_basis": "", "expectation_strength": "N/A", "served_state": "ABSENT",
                        "path": "NOT_EXECUTABLE_WITH_REASON", "exclusion": EXCLUSIONS[slug], "stack_pairs": []})
            rows.append(row)
            continue
        profile = "P2" if slug in P2_PROGRAMS else "P1"
        ex = exam.get((code, slug))
        row["discovery"] = (f"{ex.classification}; capability_data={ex.has_capability_data}" if ex is not None else "NOT_EXAMINED")
        row["proof_profile"] = profile
        seg = kernel_standalone(slug, PROFILES[profile])
        exp = (EXPECT_P2 if profile == "P2" else EXPECT).get(slug)
        g, p = _r2(seg.incentive_floor_usd) if seg.executable else None, _r2(seg.incentive_ceiling_usd) if seg.executable else None
        row.update({"kernel_executable": bool(seg.executable), "kernel_guaranteed_usd": g, "kernel_potential_usd": p})
        if exp is not None:
            row.update({"expected_guaranteed_usd": exp[0], "expected_potential_usd": exp[1], "expectation_basis": exp[2],
                        "expectation_strength": "PINNED" if exp[0] is not None else "OBSERVED_ONLY"})
        else:
            row.update({"expected_guaranteed_usd": None, "expected_potential_usd": None, "expectation_basis": "", "expectation_strength": "NONE"})
        row.update({k: v for k, v in _served_summary(slug, *served[profile]).items()})
        row["unresolved_conditions"] = sorted({c.get("condition_id", "") for c in (seg.ceiling_conditions or ())})
        row["presumed_facts"] = sorted({str(f.get("fact_key", f)) if isinstance(f, dict) else str(f) for f in (seg.presumed_facts or ())})
        if not seg.executable:
            path, why = "NOT_EXECUTABLE_WITH_REASON", EXCLUSIONS.get(slug) or "; ".join(seg.blockers)[:300]
        elif (g or 0.0) > 0:
            path, why = "EXECUTABLE_GUARANTEED", ""
        else:
            path, why = "EXECUTABLE_POTENTIAL_ONLY", ""
        row["path"], row["exclusion"] = path, why
        if path == "NOT_EXECUTABLE_WITH_REASON":
            from app.services.jurisdiction_disposition import enrich_row_with_program_detail
            _d = enrich_row_with_program_detail({"program_name": slug, "candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT"}, slug, {})
            _bd = _d.get("blocker_detail") or {}
            row["disposition_class"] = _bd.get("reconciliation_class")
            row["disposition_headline"] = _bd.get("headline")
        row["stack_pairs"] = [f"{(x['program_b'] if x['program_a'] == slug else x['program_a'])}:{x['rule_type']}:{'executable' if x['executable'] else 'blocked'}" for x in pair_by_slug.get(slug, [])]
        # the same program on the profile that lacks its base
        for (s, prof), reason in PROFILE_EXCLUSIONS.items():
            if s == slug:
                other = kernel_standalone(slug, PROFILES["P1"])
                row["p1_executable"] = bool(other.executable)
                row["p1_exclusion"] = reason
        rows.append(row)
    return {"profiles": {k: [list(l) for l in v] for k, v in PROFILES.items()}, "home": HOME, "programs": rows, "pairs": pairs,
            "summary": _summary(rows, pairs, len(rate_bearing), len(coverage_only))}


def _summary(rows, pairs, n_rate, n_cov) -> dict:
    prog = [r for r in rows if r["row_kind"] == "PROGRAM"]
    from collections import Counter
    return {
        "programs": len(prog), "rate_bearing": n_rate, "coverage_only": n_cov,
        "paths": dict(Counter(r["path"] for r in prog)),
        "served_state": dict(Counter(r["served_state"] for r in prog)),
        "expectation_strength": dict(Counter(r["expectation_strength"] for r in prog)),
        "pairs": len(pairs), "pair_rule_types": dict(Counter(p["rule_type"] for p in pairs)),
        "pairs_executable": sum(1 for p in pairs if p["executable"]),
    }
