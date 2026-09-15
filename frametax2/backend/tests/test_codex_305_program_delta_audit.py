"""Read-only acceptance invariants for the deterministic 305-program delta.

This is an audit harness, not production behavior.  It freezes the population
from the reconciliation ledger, checks the current final manifest's terminal
economic classifications, and independently anchors literal base-rate math.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.data.program_rate_rules import get_rate_rules, resolve_program_rate
from app.optimization.stacking_rules import _SLUG_PAIR_RULES
from app.services.canonical_program_identity import resolve_identity
from app.services.canonical_publication_contract import priceability


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "docs" / "validation"
DELTA_STATUSES = {"AG_ONLY_PROGRAM", "CODEX_ONLY_PROGRAM", "MATERIAL_CONFLICT"}


def _rows(name: str) -> dict[str, dict[str, str]]:
    with (VALIDATION / name).open(newline="", encoding="utf-8") as handle:
        return {row["canonical_program_id"]: row for row in csv.DictReader(handle)}


RECONCILIATION = _rows("GLOBAL_PROGRAM_AG_CODEX_RECONCILIATION.csv")
FINAL_MANIFEST = _rows("CANONICAL_PROGRAM_IMPLEMENTATION_MANIFEST_FINAL_CODEX.csv")
DELTA_IDS = tuple(sorted(
    program_id for program_id, row in RECONCILIATION.items()
    if row["reconciliation_status"] in DELTA_STATUSES
))


def test_delta_population_is_exact_and_manifest_complete():
    assert len(RECONCILIATION) == 586
    assert len(DELTA_IDS) == len(set(DELTA_IDS)) == 305
    assert {RECONCILIATION[i]["reconciliation_status"] for i in DELTA_IDS} == DELTA_STATUSES
    assert sum(RECONCILIATION[i]["reconciliation_status"] == "AG_ONLY_PROGRAM" for i in DELTA_IDS) == 119
    assert sum(RECONCILIATION[i]["reconciliation_status"] == "CODEX_ONLY_PROGRAM" for i in DELTA_IDS) == 166
    assert sum(RECONCILIATION[i]["reconciliation_status"] == "MATERIAL_CONFLICT" for i in DELTA_IDS) == 20
    assert all(i in FINAL_MANIFEST for i in DELTA_IDS)


EXPECTED_PRICEABLE = {
    "ag-bg-bulgarian-film-industry-encouragement-act-cash-rebate": "bg_film_encouragement_act_rebate",
    "ca_bc_dave": "ca_bc_dave",
    "jo_rfc_rebate": "jo_rfc_rebate",
    "mt_mfc_rebate": "mt_mfc_rebate",
    "mu_edb_incentive": "mu_edb_incentive",
    "my_finas_rebate": "my_finas_rebate",
    "nl_nfpi": "nl_film_production_incentive",
    "proposed_united_states_ohio_ohio_motion_picture_tax_credit":
        "proposed_united_states_ohio_ohio_motion_picture_tax_credit",
    "us_ky_keiia": "us_ky_keiia",
    "us_nv_film_credit": "us_nv_film_credit",
    "us_or_opif": "us_or_opif",
    "us_pa_film_credit": "us_pa_film_production_credit",
}


def test_current_final_manifest_has_exactly_twelve_priceable_delta_rows():
    actual = {
        i: (FINAL_MANIFEST[i]["current_database_id"] or i)
        for i in DELTA_IDS
        if FINAL_MANIFEST[i]["authority_status"] == "AUTHORITY_VERIFIED_PRICEABLE"
    }
    assert actual == EXPECTED_PRICEABLE
    assert sum(FINAL_MANIFEST[i]["canonical_treatment"] == "AUTOMATIC_FORMULAIC" for i in actual) == 1
    assert sum(FINAL_MANIFEST[i]["canonical_treatment"] == "CONDITIONAL_FORMULAIC" for i in actual) == 11


# Independent literal oracles: these numbers are intentionally not imported
# from the rate registry under test.  Conditions select the guaranteed floor;
# separate tests exercise the conditional ceilings and Oregon composite.
BASE_RATE_CASES = (
    ("bg_film_encouragement_act_rebate", 2_000_000.0, frozenset(), 0.25, 500_000.0),
    ("jo_rfc_rebate", 2_000_000.0, frozenset(), 0.25, 500_000.0),
    ("mt_mfc_rebate", 2_000_000.0, frozenset(), 0.30, 600_000.0),
    ("mu_edb_incentive", 2_000_000.0, frozenset(), 0.30, 600_000.0),
    ("my_finas_rebate", 2_000_000.0, frozenset(), 0.30, 600_000.0),
    ("nl_film_production_incentive", 2_000_000.0,
     frozenset({"nl_nfpi_points_independence_test_passed", "nl_nfpi_format_threshold_met"}),
     0.35, 700_000.0),
    ("us_ky_keiia", 2_000_000.0, frozenset(), 0.30, 600_000.0),
    ("us_nv_film_credit", 2_000_000.0, frozenset(), 0.15, 300_000.0),
    ("us_pa_film_production_credit", 2_000_000.0, frozenset(), 0.25, 500_000.0),
)


@pytest.mark.parametrize("slug,qpe,facts,expected_rate,expected_value", BASE_RATE_CASES)
def test_literal_guaranteed_floor_oracles(slug, qpe, facts, expected_rate, expected_value):
    resolved = resolve_program_rate(
        slug, production_type="feature_film", qpe_usd=qpe, evidenced_facts=facts,
    )
    assert resolved is not None
    assert resolved.has_guaranteed_floor is True
    assert resolved.floor_rate == expected_rate
    assert qpe * resolved.floor_rate == expected_value


@pytest.mark.parametrize(
    "slug,below_qpe",
    (
        ("mu_edb_incentive", 99_999.99),
        ("my_finas_rebate", 999_999.99),
        ("us_ky_keiia", 249_999.99),
        ("us_nv_film_credit", 499_999.99),
    ),
)
def test_literal_minimum_spend_boundaries_fail_below(slug, below_qpe):
    assert resolve_program_rate(slug, "feature_film", below_qpe) is None


def test_two_manifest_priceable_rows_are_not_canonically_complete():
    # These are acceptance findings, not wished-away assertions: the final
    # manifest says priceable, while the live identity/rate substrate is absent.
    assert resolve_identity("ca_bc_dave") is None
    assert get_rate_rules("ca_bc_dave")
    assert priceability("ca_bc_dave").gate == "UNKNOWN_PROGRAM"

    ohio = "proposed_united_states_ohio_ohio_motion_picture_tax_credit"
    assert resolve_identity(ohio) is not None
    assert get_rate_rules(ohio) == ()
    assert priceability(ohio).is_priceable is False


def test_delta_priceable_stack_rules_are_explicit_and_bounded():
    slugs = set(EXPECTED_PRICEABLE.values())
    relevant = {
        tuple(sorted(pair)): rule["rule_type"]
        for pair, rule in _SLUG_PAIR_RULES.items() if pair & slugs
    }
    assert relevant == {
        ("eu_eurimages", "mt_mfc_rebate"): "allowed",
        ("jo_rfc_rebate", "jo_rfc_tourism"): "conditional",
    }


@pytest.mark.parametrize(
    "budget,incentive,npc",
    (
        (4_364_393.00, 573_059.70, 3_791_333.30),
        (4_517_687.00, 1_445_659.84, 3_072_027.16),
        (2_482_023.00, 596_910.25, 1_885_112.75),
        (11_983_654.00, 3_459_278.90, 8_524_375.10),
    ),
)
def test_four_project_arithmetic_oracles_are_exact(budget, incentive, npc):
    assert round(budget - incentive, 2) == npc
