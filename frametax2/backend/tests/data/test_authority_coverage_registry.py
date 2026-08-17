"""
Authority coverage registry — Global Data Application verification.

Supersedes the Consolidated Global Remediation version of this file, which
asserted the pre-application state (29 records, `disposition` field). The
canonical corpus (GLOBAL_REMEDIATION_EXECUTABLE_DATA.json) has since been
applied, so these tests assert the APPLIED state and, critically, that the
registry deterministically blocks economic candidacy in the served runtime.
"""
import json
from pathlib import Path

from app.calculators.jurisdiction_comparison import ALL_PROFILES
from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard
from app.data.authority_coverage_registry import (
    BLOCKED_SLUGS,
    BLOCKING_STATES,
    CANONICAL_RUNTIME_SLUG_BINDINGS,
    COVERAGE_REGISTRY,
    blocks_economic_candidacy,
    coverage_state,
    get_coverage_status,
    is_covered_unpriceable,
)

CANONICAL = (
    Path(__file__).resolve().parents[4]
    / "docs" / "validation" / "GLOBAL_REMEDIATION_EXECUTABLE_DATA.json"
)

# Canonical-corpus ids deliberately, individually removed from
# COVERAGE_REGISTRY after this project's Global Priceability Optimizer
# Restoration / Global Economic Data + Base Pricing work found each one
# already had real, cited, primary-sourced RateRule/DoctrineRecord data —
# see authority_coverage_registry.py's module-docstring CORRECTION blocks
# for the full evidentiary trail behind every single one of these. This is
# NOT an unexplained disappearance from the frozen 176-record snapshot;
# GLOBAL_REMEDIATION_EXECUTABLE_DATA.json itself is intentionally left
# untouched (it is the historical audit trail this file is checked
# against), but the registry it seeded is expected to diverge from it by
# exactly this set as evidence accumulates. Any name appearing here MUST
# also appear in a CORRECTION block in authority_coverage_registry.py.
DELIBERATELY_PROMOTED_CANONICAL_IDS = frozenset({
    # Georgia (Global Priceability Optimizer Restoration)
    "georgia_eiia",
    # Batch 1 (8 programs, 8 alias-spelling duplicates)
    "bc_pstc", "hr_cash_rebate", "nz_spg_international", "tt_film_incentive",
    "la_film_production", "us_md_film_credit", "nm_film_production",
    "us_ri_film_credit",
    # Batch 2 (2 programs, 2 alias-spelling duplicates)
    "sa_sfc_rebate", "si_film_incentive",
    # Batch 3 (8 programs, 2 alias-spelling duplicates)
    "on_opstc", "de_dfff", "es_tax_credit_foreign", "fr_trip",
    "hu_hipa_rebate", "no_film_incentive", "us_mn_film_credit", "uk_avec",
    # Batch 4 (3 programs, 1 alias-spelling duplicate). Note:
    # us_ca_film_credit itself was never a canonical-corpus id (the corpus
    # only named the alias "ca_film_30"), so it is not listed here.
    "cy_film_rebate", "ie_section_481", "ca_film_30",
})


def _canonical_records():
    return json.loads(CANONICAL.read_text())["records"]


def test_canonical_payload_still_accounts_for_exactly_176_unique_records():
    recs = _canonical_records()
    assert len(recs) == 176
    assert len({r["canonical_id"] for r in recs}) == 176


def test_every_canonical_non_ready_record_is_represented_in_the_registry():
    """The 134 unpriceable + 2 superseded + 1 duplicate + 1 non-economic must
    all be present, EXCEPT the DELIBERATELY_PROMOTED_CANONICAL_IDS this
    project's recover-before-research batches individually verified and
    removed with real evidence (see that set's own docstring). Nothing
    else may silently disappear."""
    recs = _canonical_records()
    non_ready = [r for r in recs if r["final_disposition"] != "IMPLEMENTATION_READY"]
    assert len(non_ready) == 138
    missing = [
        r["canonical_id"] for r in non_ready
        if r["canonical_id"] not in COVERAGE_REGISTRY
        and r["canonical_id"] not in DELIBERATELY_PROMOTED_CANONICAL_IDS
    ]
    assert missing == [], f"canonical records absent from the registry: {missing}"
    unused_exemptions = DELIBERATELY_PROMOTED_CANONICAL_IDS - {
        r["canonical_id"] for r in non_ready if r["canonical_id"] not in COVERAGE_REGISTRY
    }
    assert unused_exemptions == set(), (
        f"exemptions no longer needed (row is back in the registry?): {unused_exemptions}"
    )


def test_selective_records_are_present_and_carry_zero_guaranteed_value():
    """ENCODE_SELECTIVE_ZERO_GUARANTEED must block deterministic economics --
    a competitive award is never a guaranteed rate."""
    recs = _canonical_records()
    selective = [
        r["canonical_id"] for r in recs
        if r["implementation_action"] == "ENCODE_SELECTIVE_ZERO_GUARANTEED"
    ]
    assert len(selective) == 23
    for cid in selective:
        assert blocks_economic_candidacy(cid), f"{cid} must not price deterministically"


def test_prior_pass_29_records_remain_blocked():
    """The Consolidated Global Remediation's original 25 authority-insufficient
    + 4 non-economic records must not regress."""
    prior = [
        "bh_film_incentive", "bd_film_incentive", "eg_film_incentive", "et_film_commission",
        "ga_film_incentive", "gh_film_incentive", "id_film_incentive", "kz_film_incentive",
        "ke_film_incentive", "kw_film_incentive", "mv_film_incentive", "mn_film_commission",
        "mz_film_incentive", "ng_film_incentive", "om_film_commission", "pk_pfc_rebate",
        "qa_film_incentive", "sn_film_incentive", "sc_film_incentive", "lk_film_incentive",
        "ug_film_commission", "uz_film_incentive", "vn_film_incentive", "zm_film_commission",
        "zw_film_commission",
        "bw_film_commission", "kh_film_incentive", "cn_film_incentive", "tz_film_incentive",
    ]
    assert len(prior) == 29
    for slug in prior:
        assert blocks_economic_candidacy(slug), f"prior-pass exclusion regressed: {slug}"


def test_runtime_slug_bindings_block_both_spellings():
    """The canonical corpus names programs under its own ids; where those are a
    different spelling of a live runtime slug, BOTH must be blocked -- this is
    the defect that left Saudi Arabia pricing at rank 2 and Dubai DPIP at rank 8.

    Exception: DELIBERATELY_PROMOTED_CANONICAL_IDS -- individually verified
    and removed with real primary-source evidence, see that set's docstring."""
    assert len(CANONICAL_RUNTIME_SLUG_BINDINGS) >= 43
    for canonical_id, runtime_slug in CANONICAL_RUNTIME_SLUG_BINDINGS.items():
        if canonical_id in DELIBERATELY_PROMOTED_CANONICAL_IDS:
            continue
        assert blocks_economic_candidacy(canonical_id)
        assert blocks_economic_candidacy(runtime_slug), (
            f"runtime spelling {runtime_slug} of blocked {canonical_id} can still price"
        )
    # the three specific escapes found during this pass
    assert coverage_state("ae_dxb_dpip") == "SUPERSEDED"
    # sa_film_commission_rebate and ca_bc_pstc were later individually
    # promoted (batches 1/2) -- see DELIBERATELY_PROMOTED_CANONICAL_IDS.
    assert coverage_state("sa_film_commission_rebate") == "PRICEABLE_VALIDATED"
    assert coverage_state("ca_bc_pstc") == "PRICEABLE_VALIDATED"


def test_absence_from_the_registry_means_priceable_never_a_default_exclusion():
    assert coverage_state("mu_edb_incentive") == "PRICEABLE_VALIDATED"
    assert blocks_economic_candidacy("mu_edb_incentive") is False
    assert blocks_economic_candidacy("a_program_that_does_not_exist") is False
    assert get_coverage_status(None) is None


def test_calibration_anchors_mu_mt_gr_au_are_untouched():
    """Only uk_avec of the five calibrated anchors was in the canonical 176.
    uk_avec itself was later individually promoted (Global Economic Data +
    Base Pricing, batch 3 -- bfi.org.uk, official, fetched directly, rate
    quoted verbatim) and is now correctly priceable too; see
    DELIBERATELY_PROMOTED_CANONICAL_IDS and
    test_batch3_coverage_veto_removed_including_alias_spellings in
    tests/test_canonical_authority_substrate.py for the runtime proof."""
    for slug in ("mu_edb_incentive", "mt_mfc_rebate", "gr_cash_rebate", "au_location_offset"):
        assert blocks_economic_candidacy(slug) is False, f"{slug} must remain priceable"
    assert blocks_economic_candidacy("uk_avec") is False


def test_no_record_carries_a_synthetic_rate():
    for rec in COVERAGE_REGISTRY.values():
        assert rec.state in BLOCKING_STATES
        assert rec.reason
        assert not hasattr(rec, "base_rate")
        assert not hasattr(rec, "rate")


def test_blocked_slugs_is_consistent_with_the_predicate():
    assert BLOCKED_SLUGS == {s for s in COVERAGE_REGISTRY if blocks_economic_candidacy(s)}


def test_back_compat_alias_still_works():
    assert is_covered_unpriceable("cn_film_incentive") is True
    assert is_covered_unpriceable("mu_edb_incentive") is False


def test_no_blocked_slug_remains_an_accepted_executable_jurisdiction():
    """The forbidden intersection the gate requires to be empty: a blocked
    program may still HOLD a stale profile/doctrine row, but must never be
    accepted for optimization. Proven end-to-end in
    tests/optimization/test_global_data_application_runtime.py."""
    from app.calculators.production_discovery import discover_executable_jurisdictions
    from app.calculators.production_requirements import derive_production_requirements

    reqs = derive_production_requirements([])
    result = discover_executable_jurisdictions(
        requirements=reqs, production_type="feature_film",
        qpe_usd=5_000_000.0, home_code="MU",
    )
    accepted_slugs = {slug for _code, slug in result.accepted_alternatives("MU")}
    overlap = accepted_slugs & BLOCKED_SLUGS
    assert overlap == set(), f"blocked programs accepted for optimization: {overlap}"
