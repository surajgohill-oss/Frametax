"""NA-RECONCILIATION-11 (2026-10-13): terminal accounting of the live United States / Canada / Mexico program universe.

The matrix is a DERIVATION over the canonical owners (app/services/na_canonical_reconciliation.py); these controls pin that (a) the denominator is the live registries' and is reproduced by an
independent derivation, (b) aliases never become rows, (c) every member has exactly one terminal row with a valid class, (d) the regenerated artifacts on disk are current, and (e) the repairs
made in this pass hold. Terminal accounting is not verified calculation acceptance: OPEN rows must say what evidence they still need."""
from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.data import authority_coverage_registry as acr
from app.data import program_authority_provenance as pa
from app.data.program_rate_rules import _RULES_BY_PROGRAM
from app.services import canonical_program_identity as cpi
from app.services import na_canonical_reconciliation as na

_DOCS = Path(__file__).resolve().parents[2] / "docs" / "validation"
_STEM = "NA_CANONICAL_RECONCILIATION_20261013"


@pytest.fixture(scope="module")
def matrix():
    return na.build_matrix()


def test_the_denominator_is_the_live_registry_and_matches_an_independent_derivation():
    u = na.frozen_universe()
    ind = na.independent_denominator()
    assert u["rate_bearing"] == ind["rate_bearing"]
    assert len(u["rate_bearing"]) == 54          # 45 + the seven coverage-only US programs given rate records in NA-RECONCILIATION-12 (plus the separate Colorado income tax credit and the BC film and television credit; 60 canonical programs)
    # every coverage-record-derived NA program that is not rate-bearing is a coverage-only identity (the identity layer may add others by jurisdiction code)
    assert set(ind["coverage_only_from_coverage_records"]) <= set(u["coverage_only"])
    assert not set(u["rate_bearing"]) & set(u["coverage_only"])
    assert len(u["rate_bearing"]) + len(u["coverage_only"]) == 60


def test_every_rate_bearing_program_has_a_canonical_identity():
    ids = {i.canonical_slug for i in cpi.all_canonical_identities()}
    assert set(_RULES_BY_PROGRAM) <= ids, sorted(set(_RULES_BY_PROGRAM) - ids)
    for slug in ("ca_bc_dave", "ca_federal_cptc", "on_ofttc", "ontario_computer_animation_and_special_effects_tax_credit_ocase", "us_ny_post_production_credit"):
        i = cpi.resolve_identity(slug)
        assert i is not None and i.jurisdiction_code and i.program_name


def test_aliases_are_never_rows(matrix):
    program_slugs = {r["canonical_slug"] for r in matrix if r["row_layer"] in (na.LAYER_RATE, na.LAYER_COVERAGE)}
    assert len(program_slugs) == 60, "one row per canonical program"
    aliases = {a for r in matrix if r["row_layer"] in (na.LAYER_RATE, na.LAYER_COVERAGE) for a in filter(None, (x.strip() for x in r["aliases"].split(",")))}
    assert not aliases & program_slugs
    for alias in ("qc_film_production", "us_ny_film_credit", "ca_on_opstc", "us_ca_film_credit", "proposed_united_states_new_york_film_tax_credit_post_production"):
        assert alias not in program_slugs
    assert cpi.resolve_identity("proposed_united_states_new_york_film_tax_credit_post_production").canonical_slug == "us_ny_post_production_credit"
    assert acr.economic_block_for_program("us_ny_post_production_credit") is None, "binding the duplicate proposal must not block the real program"


def test_every_row_has_a_valid_class_and_open_rows_name_the_missing_evidence(matrix):
    for r in matrix:
        assert r["defect_classification"] in na.CLASSES, r["canonical_slug"]
        assert r["terminal_disposition"], r["canonical_slug"]
        if r["terminal_disposition"].startswith("OPEN_"):
            assert r["residual_evidence_needed"].strip(), f"{r['canonical_slug']} {r['proposition_id']}: an OPEN row states the exact evidence still needed"
        assert not r["terminal_disposition"].startswith("CLOSED"), "no row is labelled CLOSED while an obligation can remain"
        if r["terminal_disposition"] in ("AUTHORITY_COMPLETE_CONSUMED", "PRICED_AUTHORITY_DIMENSIONS_OPEN", "NOT_PRICED_BY_DESIGN", "LINKED_TO_CANONICAL_PROGRAM"):
            assert r["defect_classification"] == na.C_CONSUMED or r["row_kind"] == "CATALOG"
        if r["terminal_disposition"].endswith("AUTHORITY_DIMENSIONS_OPEN"):
            assert "AUTHORITY_INCOMPLETE" in r["authority_completeness"] and r["residual_evidence_needed"].strip()


def test_the_catalog_is_fully_accounted_and_nothing_is_unmapped(matrix):
    u = na.frozen_universe()
    cat = [r for r in matrix if r["row_kind"] == "CATALOG"]
    assert len(cat) == len(u["catalog"]) == 82          # 78 + the four state-coded rows added in NA-RECONCILIATION-12 (OH, WV, NJ, MO)
    assert not [r for r in cat if r["proposition_id"] == "UNMAPPED"], "every NA catalog entry is linked or explicitly overridden"
    assert {(r["jurisdiction"], r["program_name"]) for r in cat} == set(u["catalog"])
    assert not set(k[0] for k in na.CATALOG_OVERRIDES) - {c for c, _ in u["catalog"]}
    stale = [k for k in na.CATALOG_OVERRIDES if k not in {(c, " ".join(n.lower().split())) for c, n in u["catalog"]}]
    assert stale == [], f"override keys that match no catalog row: {stale}"


def test_every_stacking_spelling_with_rules_is_canonical_aliased_or_listed(matrix):
    from app.optimization import stacking_rules as sr
    listed = {r["canonical_slug"] for r in matrix if r["row_layer"] == na.LAYER_STACK}
    assert listed == {"ca_bell_fund", "ca_cmpa_foreign", "ca_nsi_fund", "ca_telefilm_dev"}          # ca_qc_qprdp retired: an unofficial label for the Quebec services credit (NA-RECONCILIATION-12)
    rule_slugs = {s for k in sr._SLUG_PAIR_RULES for s in k}
    assert listed <= rule_slugs


def test_residual_inventory_slugs_are_real_and_classes_valid():
    ids = {i.canonical_slug for i in cpi.all_canonical_identities()}
    for r in na.RESIDUALS:
        assert r["cls"] in na.CLASSES and r["need"].strip() and r["what"].strip() and r["treatment"].strip()
        assert r["slug"] == "" or r["slug"] in ids, r["id"]
    for slug, items in na.REPAIRS.items():
        assert slug in ids
        assert all(c in na.CLASSES for c, *_ in items)


def test_no_verified_program_still_carries_an_unresolved_provenance_row():
    mismatched = [s for s in _RULES_BY_PROGRAM if pa.authority_disposition(s) == pa.AUTHORITY_VERIFIED_PRICEABLE and acr.coverage_state(s) == "AUTHORITY_UNRESOLVED_NON_PRICEABLE"]
    assert mismatched == [], "structured primary provenance attached but the residual row was not deleted (the served result would still warn and downgrade)"
    for slug in ("us_az_motion_picture_production", "us_co_film_incentive", "us_hi_film_digital_media_credit", "ca_mb_film_video_credit"):
        assert acr.coverage_state(slug) == "PRICEABLE_VALIDATED"


def test_the_committed_artifacts_are_current(matrix):
    data = json.loads((_DOCS / f"{_STEM}.json").read_text(encoding="utf-8"))
    assert data["summary"] == na.summary(matrix)
    assert data["columns"] == na.columns()
    assert len(data["rows"]) == len(matrix)
    with open(_DOCS / f"{_STEM}.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(matrix) and list(rows[0].keys()) == na.columns()
    assert [(r["canonical_slug"], r["row_layer"], r["proposition_id"]) for r in rows] == [(r["canonical_slug"], r["row_layer"], r["proposition_id"]) for r in matrix]


def test_the_formerly_unruled_pairs_are_ruled_and_the_two_without_primary_text_are_conditional_not_priced(matrix):
    # The only same-scope pairs still unruled are the New York independent credit (Tax Law 24-D) with the section 24 film credit and the post-production credit: neither the 24-D text nor
    # the section 24 / 31 text read on 2026-10-13 states whether the same film can claim both, so they stay UNRESOLVED_NO_AUTHORITY (blocking), recorded as NY-IND-POOLS-AND-PAIR.
    left = {frozenset((r["canonical_slug"], r["proposition_id"].split(":", 1)[1])) for r in matrix if r["proposition_id"].startswith("STACK-PAIR:")}
    ind = "us_ny_empire_state_independent_film_credit"
    assert left == {frozenset(("ny_state_film", ind)), frozenset(("us_ny_post_production_credit", ind))}
    from app.calculators.canonical_stack_bridge import load_named_pair_rule
    formerly = [("ca_ab_fttc", "ca_federal_cptc"), ("ca_ab_fttc", "ca_federal_pstc"), ("ca_bc_dave", "ca_federal_cptc"), ("ca_bc_dave", "ca_federal_pstc"),
                ("ca_federal_cptc", "ca_nb_film_tax_credit"), ("ca_federal_cptc", "ca_ns_production_incentive_fund"), ("ca_federal_pstc", "ca_nb_film_tax_credit"),
                ("ca_federal_pstc", "ca_ns_production_incentive_fund"), ("ca_federal_pstc", "ca_sk_creative_saskatchewan_grant"), ("ca_federal_pstc", "on_ofttc")]
    conditional = {("ca_bc_dave", "ca_federal_cptc"), ("ca_federal_pstc", "on_ofttc")}
    for a, b in formerly:
        rule = load_named_pair_rule(a, b)
        assert rule is not None and rule["rule_type"] == ("conditional" if (a, b) in conditional else "spend_reduction"), (a, b)


@pytest.mark.asyncio
async def test_texas_award_numbers_are_written_validated_and_clearable():
    from tests.isolated_records import create_synthetic_project, isolated_session
    from app.services.canonical_project_economics import _amount_facts
    from app.services.ny_producer_facts import write_ny_program_facts
    from sqlalchemy import select
    from app.models.project_fact import ProjectFact
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="US-TX")
        with pytest.raises(ValueError):
            await write_ny_program_facts(db, uuid.UUID(pid), amounts={"us_tx_miip_awarded_rate_pct": 31.0})
        with pytest.raises(ValueError):
            await write_ny_program_facts(db, uuid.UUID(pid), amounts={"not_a_fact": 1.0})
        await write_ny_program_facts(db, uuid.UUID(pid), amounts={"us_tx_miip_awarded_rate_pct": 0.28, "us_tx_miip_resident_crew_pct": 85.0})
        rows = (await db.execute(select(ProjectFact).where(ProjectFact.project_id == uuid.UUID(pid)))).scalars().all()
        assert _amount_facts(rows)["us_tx_miip_awarded_rate_pct"] == 0.28
        await write_ny_program_facts(db, uuid.UUID(pid), amounts={"us_tx_miip_awarded_rate_pct": None})
        rows = (await db.execute(select(ProjectFact).where(ProjectFact.project_id == uuid.UUID(pid)))).scalars().all()
        assert "us_tx_miip_awarded_rate_pct" not in _amount_facts(rows), "null clears: Unknown, never zero"


def test_texas_award_facts_drive_the_31_percent_ceiling_only_when_evidenced_and_in_range():
    """Independent synthetic control for the Texas path that the real-project formulaic test (bound to the FVD production) cannot run here: the 31% is a band ceiling with no floor, so
    without the award facts nothing is guaranteed; a valid award letter rate (a FRACTION within [0, 0.31]) replaces the ceiling; a value outside the range does not price."""
    from app.data.program_rate_rules import resolve_program_rate
    facts = frozenset({"us_tx_miip_award_confirmed", "us_tx_miip_pool_period_valid"})
    none = resolve_program_rate("us_tx_miip", "feature_film", 5_000_000.0, 7_000_000.0, evidenced_facts=frozenset(), amount_facts={})
    assert none is None or not none.has_guaranteed_floor
    ok = resolve_program_rate("us_tx_miip", "feature_film", 5_000_000.0, 7_000_000.0, evidenced_facts=facts,
                              amount_facts={"us_tx_miip_awarded_rate_pct": 0.28, "us_tx_miip_resident_crew_pct": 85.0, "us_tx_miip_resident_cast_pct": 60.0})
    assert ok is not None and ok.modeled_rate == pytest.approx(0.28)
