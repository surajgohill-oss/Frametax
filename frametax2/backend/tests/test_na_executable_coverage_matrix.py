"""NA executable-coverage matrix: every North American program has an executable path (discovery -> kernel pricing -> served output -> lawful stacking) or an exact, tested exclusion.

The matrix is built from synthetic evidence only (tests/na_coverage_matrix.py) and compared with the committed artifact docs/validation/NA_EXECUTABLE_COVERAGE_MATRIX_20261013.{json,csv}.
Regenerate after an intended change:  WRITE_NA_COVERAGE_MATRIX=1 pytest tests/test_na_executable_coverage_matrix.py  (isolated database; DATABASE_URL unset).
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

from tests.na_coverage_matrix import EXCLUSIONS, PROFILE_EXCLUSIONS, build

_DOCS = Path(__file__).resolve().parents[2] / "docs" / "validation"
_STEM = "NA_EXECUTABLE_COVERAGE_MATRIX_20261013"
_PROOF = "tests/test_na_executable_coverage_matrix.py"

#: stacking outcome by registered rule type when both members price: the pair composes (True) or is refused (False)
_COMPOSES = {"allowed": True, "spend_reduction": True, "same_cost_prohibited_distinct_costs_allowed": True,
             "mutually_exclusive": False, "conditional": False, "UNRULED": False}


@pytest.fixture(scope="module")
async def matrix():
    return await build()


def _flat(m: dict) -> list[dict]:
    rows = []
    for r in m["programs"]:
        rows.append({**{k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in r.items()}, "proof_test": f"{_PROOF}::test_every_program_has_an_executable_path_or_an_exact_exclusion"})
    for r in m["pairs"]:
        rows.append({**{k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in r.items()}, "proof_test": f"{_PROOF}::test_every_same_scope_pair_composes_or_is_refused_for_its_registered_reason"})
    return rows


@pytest.mark.asyncio
async def test_the_matrix_artifact_is_current_or_rewritten_on_request(matrix):
    m = json.loads(json.dumps(matrix, default=str))
    flat = _flat(matrix)
    cols = list(dict.fromkeys(k for r in flat for k in r))
    if os.environ.get("WRITE_NA_COVERAGE_MATRIX") == "1":
        (_DOCS / f"{_STEM}.json").write_text(json.dumps(m, indent=1, sort_keys=False, default=str) + "\n", encoding="utf-8")
        with open(_DOCS / f"{_STEM}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(flat)
    committed = json.loads((_DOCS / f"{_STEM}.json").read_text(encoding="utf-8"))
    assert committed == m, "the committed matrix is stale (WRITE_NA_COVERAGE_MATRIX=1 regenerates it)"
    with open(_DOCS / f"{_STEM}.csv", newline="", encoding="utf-8") as fh:
        assert len(list(csv.DictReader(fh))) == len(flat)


@pytest.mark.asyncio
async def test_every_program_has_an_executable_path_or_an_exact_exclusion(matrix):
    rate_bearing = [r for r in matrix["programs"] if r["layer"] == "RATE_BEARING"]
    assert len(rate_bearing) == 54 and len(matrix["programs"]) == 62
    for r in matrix["programs"]:
        slug = r["canonical_slug"]
        if r["layer"] == "COVERAGE_ONLY":
            assert r["path"] == "NOT_EXECUTABLE_WITH_REASON" and r["exclusion"] == EXCLUSIONS[slug] and r["served_state"] == "ABSENT"
            continue
        if r["path"] == "NOT_EXECUTABLE_WITH_REASON":
            assert slug in EXCLUSIONS and r["exclusion"] == EXCLUSIONS[slug], f"{slug}: a program without an executable path needs an exact exclusion"
            continue
        assert r["kernel_executable"] and r["discovery"].startswith("incentive_ready"), (slug, r["discovery"])
        assert r["served_state"] in ("RETAINED", "AGGREGATED"), f"{slug}: executable but not accounted in the served output"
        if r["expectation_strength"] == "PINNED":
            assert r["kernel_guaranteed_usd"] == pytest.approx(r["expected_guaranteed_usd"], abs=0.01), slug
            if r["expected_potential_usd"] is not None:
                assert r["kernel_potential_usd"] == pytest.approx(r["expected_potential_usd"], abs=0.01), slug
        assert (r["path"] == "EXECUTABLE_POTENTIAL_ONLY") == ((r["kernel_guaranteed_usd"] or 0.0) == 0.0), f"{slug}: a zero floor is potential only, never guaranteed"
    for (slug, profile), reason in PROFILE_EXCLUSIONS.items():
        row = next(x for x in matrix["programs"] if x["canonical_slug"] == slug)
        assert row["p1_executable"] is False and row["p1_exclusion"] == reason and row["proof_profile"] == "P2" and row["path"].startswith("EXECUTABLE"), slug


@pytest.mark.asyncio
async def test_discretionary_awards_show_potential_with_a_zero_guaranteed_floor_and_visible_conditions(matrix):
    by = {r["canonical_slug"]: r for r in matrix["programs"]}
    for slug in ("ca_nb_film_tax_credit", "us_ar_digital_motion_picture_incentive", "us_mt_media_act_tax_credit", "us_co_film_income_tax_credit", "us_nc_film_entertainment_grant",
                 "us_md_film_production_activity_credit", "us_sc_film_production_credit", "mx_federal_film_incentive_2026", "us_tx_miip"):
        r = by[slug]
        assert r["path"] == "EXECUTABLE_POTENTIAL_ONLY" and r["kernel_guaranteed_usd"] == 0.0 and r["kernel_potential_usd"] > 0, slug
        assert r["unresolved_conditions"], f"{slug}: the unresolved award conditions must stay visible"


@pytest.mark.asyncio
async def test_every_same_scope_pair_composes_or_is_refused_for_its_registered_reason(matrix):
    by = {r["canonical_slug"]: r for r in matrix["programs"]}
    assert matrix["pairs"], "same-scope pairs exist"
    for p in matrix["pairs"]:
        rt = p["rule_type"]
        members_price = all(by[x]["kernel_executable"] or x in ("ca_bc_dave", "ontario_computer_animation_and_special_effects_tax_credit_ocase") for x in (p["program_a"], p["program_b"]))
        if not members_price:
            assert not p["executable"] and any(x == "ca_sk_creative_saskatchewan_grant" for x in (p["program_a"], p["program_b"])), p
            continue
        assert p["executable"] is _COMPOSES[rt], (p["program_a"], p["program_b"], rt, p["reason"])
        if not p["executable"]:
            assert p["reason"], "a refused pair states why"
    # no same-scope pair is silently missing: every pair among the priced NA programs now has a registered rule
    assert not [p for p in matrix["pairs"] if p["rule_type"] == "UNRULED"]
    by = {(p["program_a"], p["program_b"]): p for p in matrix["pairs"]}
    # ESD program page: one program per production (regular vs independent) and no independent + post-production credit for the same project
    for key in (("ny_state_film", "us_ny_empire_state_independent_film_credit"), ("us_ny_empire_state_independent_film_credit", "us_ny_post_production_credit")):
        assert by[key]["rule_type"] == "mutually_exclusive" and not by[key]["executable"]


@pytest.mark.asyncio
async def test_the_six_new_states_are_discovered_priced_and_served_with_mfni_unmodeled(matrix):
    by = {r["canonical_slug"]: r for r in matrix["programs"]}
    for slug in ("us_oh_motion_picture_tax_credit", "us_wv_film_production_tax_credit", "us_nj_garden_state_film_credit", "us_mo_motion_media_production_tax_credit",
                 "us_ar_digital_motion_picture_incentive", "us_mt_media_act_tax_credit"):
        r = by[slug]
        assert r["discovery"].startswith("incentive_ready") and "capability_data=False" in r["discovery"], slug     # unknown capability never rejects
        assert r["served_state"] == "RETAINED" and r["mfni_status"] == "UNMODELED_NO_BENCHMARK", slug


@pytest.mark.asyncio
async def test_the_display_only_discretionary_grant_is_served_as_a_zero_guaranteed_disposition_naming_its_stated_rates(matrix):
    r = next(x for x in matrix["programs"] if x["canonical_slug"] == "ca_sk_creative_saskatchewan_grant")
    assert r["path"] == "NOT_EXECUTABLE_WITH_REASON" and r["disposition_class"] == "DISCRETIONARY_AWARD_ZERO_GUARANTEED"
    assert "zero" in r["disposition_headline"] and "25% to 30%" in r["disposition_headline"]


@pytest.mark.asyncio
async def test_the_bc_domestic_credit_is_executable_exclusive_with_the_services_credit_and_additive_with_dave(matrix):
    by = {(p["program_a"], p["program_b"]): p for p in matrix["pairs"]}
    assert by[("ca_bc_film_tv_tax_credit", "ca_bc_pstc")]["rule_type"] == "mutually_exclusive" and not by[("ca_bc_film_tv_tax_credit", "ca_bc_pstc")]["executable"]
    dave = by[("ca_bc_dave", "ca_bc_film_tv_tax_credit")]
    assert dave["rule_type"] == "allowed" and dave["executable"]
    cptc = by[("ca_bc_film_tv_tax_credit", "ca_federal_cptc")]
    # BC 35% x 2,000,000 = 700,000; CPTC cap 60% x (4,000,000 - 700,000) = 1,980,000 < labour 2,000,000 -> 25% x 1,980,000 = 495,000; total 1,195,000
    assert cptc["rule_type"] == "spend_reduction" and cptc["executable"] and cptc["guaranteed_usd"] == pytest.approx(1_195_000.0)
    # NA-RECONCILIATION-13: ruled spend_reduction from primary text. BC 35% x 2,000,000 = 700,000; PSTC 16% x 2,000,000 = 320,000; the BC credit is labour-only, so the whole 700,000 is assistance:
    # PSTC 320,000 - 700,000 x 16% = 208,000; total 908,000.
    pstc = by[("ca_bc_film_tv_tax_credit", "ca_federal_pstc")]
    assert pstc["rule_type"] == "spend_reduction" and pstc["executable"] and pstc["guaranteed_usd"] == pytest.approx(908_000.0)
