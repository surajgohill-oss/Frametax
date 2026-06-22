"""
coverage_report.py

Deterministic coverage report for the global incentive inventory.
No DB access. Pure Python — operates on GlobalProgramEntry / CostBenchmarkEntry lists.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.data.global_inventory import (
    ALL_BENCHMARKS,
    ALL_PROGRAMS,
    CostBenchmarkEntry,
    GlobalProgramEntry,
)
from app.data.jurisdiction_search_status import NO_PROGRAM_CODES, NO_PROGRAM_RECORDS

REPORT_VERSION = "0.8.0"

# ---------------------------------------------------------------------------
# Intelligence population registry — tracks which slugs have been seeded
# via migrations. Update this set when new seeding migrations are added.
# Used by build_intelligence_gap_report() to compute what's still missing.
# ---------------------------------------------------------------------------

# Programs that have had ProgramAdminDetails seeded (migrations 0016, 0019, 0020, 0023)
SLUGS_WITH_ADMIN_DETAILS: frozenset[str] = frozenset([
    # 0016
    "georgia_eiia", "ny_state_film", "ca_film_30", "la_film_production",
    "uk_avec", "ie_section_481", "mt_mfc_rebate", "gr_cash_rebate",
    "mu_edb_incentive", "on_opstc", "bc_pstc", "qc_film_production",
    # 0019
    "es_tax_credit_foreign", "be_tax_shelter", "de_dfff",
    "au_location_offset", "nz_spg_international",
    # 0020
    "ca_federal_cptc", "on_ofttc", "or_opif", "nm_film_production",
    "nohfc_production_fund", "fr_trip", "it_tax_credit_foreign",
    "cy_film_rebate", "hr_cash_rebate", "hu_hipa_rebate",
    # 0027 — all 47 wave-2 programs (DISCOVERY tier)
    "us_hi_film_tax_credit", "us_ut_film_incentive", "us_mn_film_credit",
    "us_ms_film_credit", "us_az_film_credit", "us_pr_film_incentive",
    "ca_sk_production_grant", "ca_nl_production_fund",
    "se_film_incentive", "no_film_incentive", "fi_film_incentive", "dk_film_incentive",
    "pl_film_incentive", "bg_film_incentive", "ee_film_incentive", "lt_film_incentive",
    "lv_film_incentive", "sk_film_incentive", "lu_film_incentive", "tr_film_incentive",
    "th_film_incentive", "my_film_incentive", "ph_film_incentive", "kr_film_incentive",
    "in_national_film", "lk_film_incentive",
    "mx_eficine_incentive", "cl_corfo_incentive", "jm_film_incentive", "tt_film_incentive",
    "il_film_incentive", "qa_film_incentive", "tn_film_incentive",
    "ke_film_incentive", "ng_film_incentive",
    "eu_eurimages", "eu_media_fund", "nordic_ftvf",
    "ca_cmf", "ca_telefilm_dev", "gb_bfi_production", "fr_cnc_production",
    "au_screen_production", "nl_hbf", "qa_dfi_fund", "us_sundance_doc", "za_dac_fund",
    # 0030 — all 43 wave-3 programs (DISCOVERY tier)
    "us_ga_film_credit", "us_la_film_incentive", "us_nm_film_credit",
    "us_ny_film_credit", "us_nv_film_incentive", "us_ri_film_credit",
    "bs_film_incentive", "bb_film_incentive", "pa_film_incentive", "cr_film_incentive",
    "pe_film_incentive", "ec_film_incentive",
    "eg_film_incentive", "gh_film_incentive", "rw_film_incentive",
    "tz_film_incentive", "sn_film_incentive",
    "kw_film_incentive", "bh_film_incentive",
    "ge_film_incentive", "kz_film_incentive", "am_film_incentive",
    "vn_film_incentive", "id_film_incentive", "kh_film_incentive",
    "jp_film_incentive", "tw_film_incentive", "hk_film_incentive",
    "al_film_incentive", "me_film_incentive", "mk_film_incentive", "ba_film_incentive",
    "fj_film_incentive",
    "ibermedia_programme", "de_fff_bayern", "de_nrw_filmstiftung", "hk_film_dev_fund",
    "in_nfdc_coproduction", "sg_imda_film_fund", "tw_taicca_fund",
    "film_i_vast", "acpfilms_fund", "us_itvs_fund",
    # 0033 — all 21 wave-4 programs (DISCOVERY tier)
    "az_film_incentive", "uz_film_incentive", "om_film_commission",
    "lb_film_incentive", "ve_cnac_fund", "gy_film_commission",
    "gt_film_commission", "na_film_commission", "bw_film_commission",
    "et_film_commission", "ci_film_incentive", "cm_film_incentive",
    "ao_film_incentive", "ug_film_commission", "mz_film_incentive",
    "zm_film_commission", "zw_film_commission", "cn_film_incentive",
    "mn_film_commission", "mo_film_fund", "bd_film_incentive",
    # 0023 — all 43 extended programs (DISCOVERY tier)
    "us_or_opif", "us_wa_mpcp", "us_il_film_credit", "us_nc_film_grant",
    "us_sc_film_credit", "us_ma_film_credit", "us_tx_miip", "us_ct_film_credit",
    "us_pa_film_credit", "us_md_film_credit", "us_va_film_credit",
    "us_co_film_incentive", "us_tn_film_incentive", "us_ok_ofer",
    "us_al_film_incentive", "us_ky_keiia",
    "ca_ab_fttc", "ca_mb_fvptc", "ca_ns_pif", "ca_nb_film_credit",
    "nl_nfpi", "at_fisa_plus", "cz_film_incentive", "ro_cnc_rebate",
    "pt_film_incentive", "rs_film_rebate", "is_film_reimbursement",
    "gb_sct_screen_fund", "gb_wls_screen_fund",
    "sg_sfc_production", "au_nsw_screen", "au_vic_vicscreen", "au_qld_screen_qld",
    "co_film_colombia", "do_film_incentive", "uy_xxi_incentive",
    "ar_incaa_incentive", "br_ancine_incentive",
    "ae_dpip", "sa_sfc_rebate", "jo_rfc_rebate",
    "ma_ccm_rebate", "za_nfvf_rebate",
])

# Programs that have had ProgramSpendTreatment seeded (migrations 0017-0021, 0024)
SLUGS_WITH_SPEND_TREATMENT: frozenset[str] = frozenset([
    # 0017
    "uk_avec", "ie_section_481", "georgia_eiia", "ca_film_30",
    "mt_mfc_rebate", "gr_cash_rebate", "on_opstc", "ny_state_film",
    # 0018
    "la_film_production", "bc_pstc", "qc_film_production",
    # 0019
    "es_tax_credit_foreign", "be_tax_shelter", "de_dfff",
    "au_location_offset", "nz_spg_international",
    # 0021
    "ca_federal_cptc", "on_ofttc", "fr_trip", "it_tax_credit_foreign",
    "mu_edb_incentive", "nm_film_production", "or_opif",
    "nohfc_production_fund", "cy_film_rebate", "hr_cash_rebate", "hu_hipa_rebate",
    # 0028 — all 47 wave-2 programs (DISCOVERY tier)
    "us_hi_film_tax_credit", "us_ut_film_incentive", "us_mn_film_credit",
    "us_ms_film_credit", "us_az_film_credit", "us_pr_film_incentive",
    "ca_sk_production_grant", "ca_nl_production_fund",
    "se_film_incentive", "no_film_incentive", "fi_film_incentive", "dk_film_incentive",
    "pl_film_incentive", "bg_film_incentive", "ee_film_incentive", "lt_film_incentive",
    "lv_film_incentive", "sk_film_incentive", "lu_film_incentive", "tr_film_incentive",
    "th_film_incentive", "my_film_incentive", "ph_film_incentive", "kr_film_incentive",
    "in_national_film", "lk_film_incentive",
    "mx_eficine_incentive", "cl_corfo_incentive", "jm_film_incentive", "tt_film_incentive",
    "il_film_incentive", "qa_film_incentive", "tn_film_incentive",
    "ke_film_incentive", "ng_film_incentive",
    "eu_eurimages", "eu_media_fund", "nordic_ftvf",
    "ca_cmf", "ca_telefilm_dev", "gb_bfi_production", "fr_cnc_production",
    "au_screen_production", "nl_hbf", "qa_dfi_fund", "us_sundance_doc", "za_dac_fund",
    # 0031 — all 43 wave-3 programs (DISCOVERY tier)
    "us_ga_film_credit", "us_la_film_incentive", "us_nm_film_credit",
    "us_ny_film_credit", "us_nv_film_incentive", "us_ri_film_credit",
    "bs_film_incentive", "bb_film_incentive", "pa_film_incentive", "cr_film_incentive",
    "pe_film_incentive", "ec_film_incentive",
    "eg_film_incentive", "gh_film_incentive", "rw_film_incentive",
    "tz_film_incentive", "sn_film_incentive",
    "kw_film_incentive", "bh_film_incentive",
    "ge_film_incentive", "kz_film_incentive", "am_film_incentive",
    "vn_film_incentive", "id_film_incentive", "kh_film_incentive",
    "jp_film_incentive", "tw_film_incentive", "hk_film_incentive",
    "al_film_incentive", "me_film_incentive", "mk_film_incentive", "ba_film_incentive",
    "fj_film_incentive",
    "ibermedia_programme", "de_fff_bayern", "de_nrw_filmstiftung", "hk_film_dev_fund",
    "in_nfdc_coproduction", "sg_imda_film_fund", "tw_taicca_fund",
    "film_i_vast", "acpfilms_fund", "us_itvs_fund",
    # 0034 — all 21 wave-4 programs (DISCOVERY tier)
    "az_film_incentive", "uz_film_incentive", "om_film_commission",
    "lb_film_incentive", "ve_cnac_fund", "gy_film_commission",
    "gt_film_commission", "na_film_commission", "bw_film_commission",
    "et_film_commission", "ci_film_incentive", "cm_film_incentive",
    "ao_film_incentive", "ug_film_commission", "mz_film_incentive",
    "zm_film_commission", "zw_film_commission", "cn_film_incentive",
    "mn_film_commission", "mo_film_fund", "bd_film_incentive",
    # 0024 — all 43 extended programs (DISCOVERY tier)
    "us_or_opif", "us_wa_mpcp", "us_il_film_credit", "us_nc_film_grant",
    "us_sc_film_credit", "us_ma_film_credit", "us_tx_miip", "us_ct_film_credit",
    "us_pa_film_credit", "us_md_film_credit", "us_va_film_credit",
    "us_co_film_incentive", "us_tn_film_incentive", "us_ok_ofer",
    "us_al_film_incentive", "us_ky_keiia",
    "ca_ab_fttc", "ca_mb_fvptc", "ca_ns_pif", "ca_nb_film_credit",
    "nl_nfpi", "at_fisa_plus", "cz_film_incentive", "ro_cnc_rebate",
    "pt_film_incentive", "rs_film_rebate", "is_film_reimbursement",
    "gb_sct_screen_fund", "gb_wls_screen_fund",
    "sg_sfc_production", "au_nsw_screen", "au_vic_vicscreen", "au_qld_screen_qld",
    "co_film_colombia", "do_film_incentive", "uy_xxi_incentive",
    "ar_incaa_incentive", "br_ancine_incentive",
    "ae_dpip", "sa_sfc_rebate", "jo_rfc_rebate",
    "ma_ccm_rebate", "za_nfvf_rebate",
])

# Programs that have LegalStackingRules seeded (migrations 0007, 0022)
SLUGS_WITH_STACKING_RULES: frozenset[str] = frozenset([
    # 0007 (NOHFC spend_reduction against OFTTC and CPTC)
    "nohfc_production_fund", "on_ofttc", "ca_federal_cptc",
    # 0022
    "on_opstc", "bc_pstc", "qc_film_production",
    "uk_avec", "ie_section_481",
])

# Programs that have had at least one UNKNOWN spend treatment resolved to a
# source-backed value (migrations 0025+). Updated when new resolution batches land.
SLUGS_WITH_RESOLVED_TREATMENTS: frozenset[str] = frozenset([
    # 0025 — source-backed UNKNOWN resolution batch 1
    "ny_state_film",       # ATL all 5 → QUALIFIES
    "mu_edb_incentive",    # ATL 5 + BTL 3 + travel/accommodation/per_diem/marine_vessel → QUALIFIES
    "on_opstc",            # ATL writer/director/producer → QUALIFIES
    "on_ofttc",            # btl_crew_non_resident/foreign → DOES_NOT_QUALIFY
    "qc_film_production",  # ATL writer/director/producer → QUALIFIES
    "bc_pstc",             # atl_writer → QUALIFIES
])

# Fields required for a program to be promotable from DISCOVERY to PARSED
_PROMOTABLE_REQUIRED_FIELDS = frozenset([
    "base_rate",
    "is_refundable",
    "requires_local_entity",
    "source_url",
])

# Fields required for a program to be promotable from PARSED to VERIFIED
_VERIFIED_REQUIRED_FIELDS = frozenset([
    "base_rate",
    "max_rate",
    "is_refundable",
    "is_transferable",
    "requires_local_entity",
    "min_spend_usd",
    "requires_cultural_test",
    "effective_from",
    "source_url",
    "source_title",
])


@dataclass
class JurisdictionCoverage:
    jurisdiction_code: str
    jurisdiction_name: str
    program_count: int
    benchmark_count: int
    # Confidence tier counts (across programs + benchmarks combined)
    verified_count: int
    parsed_count: int
    discovery_count: int
    # Unknown fields aggregated from programs in this jurisdiction
    unknown_fields: list[str] = field(default_factory=list)
    # Gaps preventing real-world budget testing
    budget_testing_blockers: list[str] = field(default_factory=list)


@dataclass
class CoverageReport:
    report_version: str
    total_jurisdictions: int
    total_programs: int
    total_benchmarks: int
    verified_programs: int
    parsed_programs: int
    discovery_programs: int
    verified_benchmarks: int
    parsed_benchmarks: int
    discovery_benchmarks: int
    by_jurisdiction: list[JurisdictionCoverage]


_BUDGET_TEST_REQUIRED_PROGRAM_FIELDS = [
    "confirmed_rate",
    "annual_cap",
    "minimum_spend_threshold",
    "processing_timeline",
]

_BUDGET_TEST_REQUIRED_BENCHMARK_FIELDS = [
    "crew_rate_multiplier",
    "equipment_rental_multiplier",
]


def _budget_testing_blockers(
    prog: Optional[GlobalProgramEntry],
    bm: Optional[CostBenchmarkEntry],
) -> list[str]:
    blockers: list[str] = []
    if prog is None:
        blockers.append("no_incentive_program_seeded")
        return blockers
    if prog.confidence_tier == "DISCOVERY":
        blockers.append(f"program_rate_unverified (tier=DISCOVERY, rate={prog.base_rate})")
    if prog.base_rate is None:
        blockers.append("base_rate_unknown")
    if "confirmed_rate" in (prog.unknown_fields or []):
        blockers.append("confirmed_rate_unknown")
    if "annual_cap" in (prog.unknown_fields or []) and prog.annual_cap_usd is None:
        blockers.append("annual_cap_unknown (cannot model oversubscription risk)")
    if "processing_timeline" in (prog.unknown_fields or []):
        blockers.append("processing_timeline_unknown (cannot model finance cost)")
    if bm is None:
        blockers.append("no_cost_benchmark_seeded")
    elif bm.crew_rate_multiplier is None:
        blockers.append("crew_rate_multiplier_unknown")
    return blockers


def build_coverage_report(
    programs: list[GlobalProgramEntry] | None = None,
    benchmarks: list[CostBenchmarkEntry] | None = None,
) -> CoverageReport:
    """
    Build a jurisdiction-level coverage report from the global inventory.
    Defaults to ALL_PROGRAMS and ALL_BENCHMARKS if not supplied.
    """
    if programs is None:
        programs = ALL_PROGRAMS
    if benchmarks is None:
        benchmarks = ALL_BENCHMARKS

    # Index by jurisdiction_code
    bm_by_code: dict[str, list[CostBenchmarkEntry]] = {}
    for bm in benchmarks:
        bm_by_code.setdefault(bm.jurisdiction_code, []).append(bm)

    prog_by_code: dict[str, list[GlobalProgramEntry]] = {}
    for p in programs:
        prog_by_code.setdefault(p.jurisdiction_code, []).append(p)

    all_codes_ordered: list[str] = []
    seen: set[str] = set()
    for p in programs:
        if p.jurisdiction_code not in seen:
            all_codes_ordered.append(p.jurisdiction_code)
            seen.add(p.jurisdiction_code)
    for bm in benchmarks:
        if bm.jurisdiction_code not in seen:
            all_codes_ordered.append(bm.jurisdiction_code)
            seen.add(bm.jurisdiction_code)

    by_jur: list[JurisdictionCoverage] = []
    total_verified_prog = total_parsed_prog = total_discovery_prog = 0
    total_verified_bm = total_parsed_bm = total_discovery_bm = 0

    for code in all_codes_ordered:
        jur_progs = prog_by_code.get(code, [])
        jur_bms = bm_by_code.get(code, [])

        verified = parsed = discovery = 0
        for p in jur_progs:
            if p.confidence_tier == "VERIFIED":
                verified += 1
                total_verified_prog += 1
            elif p.confidence_tier == "PARSED":
                parsed += 1
                total_parsed_prog += 1
            else:
                discovery += 1
                total_discovery_prog += 1

        for bm in jur_bms:
            if bm.confidence_tier == "VERIFIED":
                total_verified_bm += 1
                verified += 1
            elif bm.confidence_tier == "PARSED":
                total_parsed_bm += 1
                parsed += 1
            else:
                total_discovery_bm += 1
                discovery += 1

        # Aggregate unknown fields
        all_unknown: list[str] = []
        for p in jur_progs:
            for uf in (p.unknown_fields or []):
                if uf not in all_unknown:
                    all_unknown.append(uf)

        jur_name = jur_progs[0].jurisdiction_name if jur_progs else code
        first_prog = jur_progs[0] if jur_progs else None
        first_bm = jur_bms[0] if jur_bms else None

        by_jur.append(JurisdictionCoverage(
            jurisdiction_code=code,
            jurisdiction_name=jur_name,
            program_count=len(jur_progs),
            benchmark_count=len(jur_bms),
            verified_count=verified,
            parsed_count=parsed,
            discovery_count=discovery,
            unknown_fields=all_unknown,
            budget_testing_blockers=_budget_testing_blockers(first_prog, first_bm),
        ))

    return CoverageReport(
        report_version=REPORT_VERSION,
        total_jurisdictions=len(all_codes_ordered),
        total_programs=len(programs),
        total_benchmarks=len(benchmarks),
        verified_programs=total_verified_prog,
        parsed_programs=total_parsed_prog,
        discovery_programs=total_discovery_prog,
        verified_benchmarks=total_verified_bm,
        parsed_benchmarks=total_parsed_bm,
        discovery_benchmarks=total_discovery_bm,
        by_jurisdiction=by_jur,
    )


def get_promotable_programs(
    programs: list[GlobalProgramEntry] | None = None,
) -> list[GlobalProgramEntry]:
    """
    Return DISCOVERY programs that have enough data to be promoted to PARSED.
    A program is promotable if all _PROMOTABLE_REQUIRED_FIELDS are non-None/non-empty
    and it is not already PARSED or VERIFIED.
    """
    if programs is None:
        programs = ALL_PROGRAMS
    promotable = []
    for p in programs:
        if p.confidence_tier != "DISCOVERY":
            continue
        missing = _missing_promotable_fields(p)
        if not missing:
            promotable.append(p)
    return promotable


def _missing_promotable_fields(p: GlobalProgramEntry) -> list[str]:
    missing = []
    if p.base_rate is None:
        missing.append("base_rate")
    if p.is_refundable is None:
        missing.append("is_refundable")
    if p.source_url is None:
        missing.append("source_url")
    return missing


def _missing_verified_fields(p: GlobalProgramEntry) -> list[str]:
    missing = []
    if p.base_rate is None:
        missing.append("base_rate")
    if p.max_rate is None:
        missing.append("max_rate")
    if p.is_refundable is None:
        missing.append("is_refundable")
    if p.is_transferable is None:
        missing.append("is_transferable")
    if p.source_url is None:
        missing.append("source_url")
    if p.effective_from is None:
        missing.append("effective_from")
    return missing


@dataclass
class GapAnalysis:
    """High-value gaps blocking database completeness."""
    programs_missing_source_url: list[str]       # jurisdiction_codes
    programs_missing_base_rate: list[str]
    programs_missing_refundability: list[str]
    programs_promotable_to_parsed: list[str]
    jurisdictions_missing_benchmark: list[str]
    total_discovery_programs: int
    total_parsed_programs: int
    total_verified_programs: int


def build_gap_analysis(
    programs: list[GlobalProgramEntry] | None = None,
    benchmarks: list[CostBenchmarkEntry] | None = None,
) -> GapAnalysis:
    """
    Identify the highest-priority gaps in the inventory.
    Returns a structured analysis of what's missing and what's promotable.
    """
    if programs is None:
        programs = ALL_PROGRAMS
    if benchmarks is None:
        benchmarks = ALL_BENCHMARKS

    bm_codes = {bm.jurisdiction_code for bm in benchmarks}

    missing_url = []
    missing_rate = []
    missing_refundability = []
    promotable = []
    discovery = parsed = verified = 0

    for p in programs:
        if p.confidence_tier == "DISCOVERY":
            discovery += 1
        elif p.confidence_tier == "PARSED":
            parsed += 1
        elif p.confidence_tier == "VERIFIED":
            verified += 1

        if p.source_url is None:
            missing_url.append(p.jurisdiction_code)
        if p.base_rate is None:
            missing_rate.append(p.jurisdiction_code)
        if p.is_refundable is None:
            missing_refundability.append(p.jurisdiction_code)
        if p.confidence_tier == "DISCOVERY" and not _missing_promotable_fields(p):
            promotable.append(p.jurisdiction_code)

    # Jurisdictions with programs but no benchmark
    prog_codes = {p.jurisdiction_code for p in programs}
    missing_bm = sorted(prog_codes - bm_codes)

    return GapAnalysis(
        programs_missing_source_url=missing_url,
        programs_missing_base_rate=missing_rate,
        programs_missing_refundability=missing_refundability,
        programs_promotable_to_parsed=promotable,
        jurisdictions_missing_benchmark=missing_bm,
        total_discovery_programs=discovery,
        total_parsed_programs=parsed,
        total_verified_programs=verified,
    )


@dataclass
class IntelligenceGapReport:
    """
    Cross-references the population registry against known programs to show
    what intelligence layers are still missing.  Pure Python — no DB access.
    """
    # Programs (jurisdiction_codes) missing AdminDetails
    programs_missing_admin_details: list[str]
    # Programs (jurisdiction_codes) missing SpendTreatment
    programs_missing_spend_treatment: list[str]
    # Programs (jurisdiction_codes) missing StackingRules
    programs_missing_stacking_rules: list[str]
    # Programs with any UNKNOWN fields in global inventory
    programs_with_unknown_fields: list[str]
    # Programs at DISCOVERY tier — not yet promoted
    discovery_programs: list[str]
    # Programs at PARSED — candidates for further verification
    parsed_programs: list[str]
    # Programs where AdminDetails and SpendTreatment are both complete
    fully_seeded_programs: list[str]
    # Totals
    total_programs: int
    admin_details_seeded: int
    spend_treatment_seeded: int
    stacking_rules_seeded: int
    # Coverage percentages (0–100, rounded to 1 decimal)
    admin_coverage_pct: float = 0.0
    treatment_coverage_pct: float = 0.0
    stacking_coverage_pct: float = 0.0
    # Programs with at least one UNKNOWN spend treatment resolved to source-backed value
    resolved_treatment_programs: int = 0
    # Grant / fund programs (program_type not tax_credit or cash_rebate)
    grant_fund_programs: int = 0
    # Total unique countries covered (by distinct jurisdiction_code)
    countries_covered: int = 0
    # Non-grant incentive programs (tax_credit, cash_rebate, production_support, etc.)
    total_incentive_programs: int = 0
    # Number of distinct world regions covered
    regions_covered: int = 0
    # Estimated discovery completeness (countries with programs / 195 sovereign nations)
    discovery_completion_pct: float = 0.0
    # v0.8.0 — search coverage fields
    # Countries where at least one program was found (top-level codes only)
    countries_with_program: int = 0
    # Countries explicitly searched with no known program found
    countries_searched_no_program: int = 0
    # Countries not yet researched (195 - countries_with_program - countries_searched_no_program)
    countries_not_yet_searched: int = 0
    # Percentage of 195 sovereign nations that have been searched (either outcome)
    global_search_coverage_pct: float = 0.0
    # Top regions still with many unsearched countries
    top_unsearched_regions: list[str] = field(default_factory=list)


def build_intelligence_gap_report(
    programs: list[GlobalProgramEntry] | None = None,
    slugs_with_admin: frozenset[str] | None = None,
    slugs_with_treatment: frozenset[str] | None = None,
    slugs_with_stacking: frozenset[str] | None = None,
    slugs_with_resolved: frozenset[str] | None = None,
) -> IntelligenceGapReport:
    """
    Build a deterministic intelligence gap report from the global inventory
    and population registry.  Call without arguments to use current registry.
    """
    if programs is None:
        programs = ALL_PROGRAMS
    if slugs_with_admin is None:
        slugs_with_admin = SLUGS_WITH_ADMIN_DETAILS
    if slugs_with_treatment is None:
        slugs_with_treatment = SLUGS_WITH_SPEND_TREATMENT
    if slugs_with_stacking is None:
        slugs_with_stacking = SLUGS_WITH_STACKING_RULES
    if slugs_with_resolved is None:
        slugs_with_resolved = SLUGS_WITH_RESOLVED_TREATMENTS

    # Build a slug → jurisdiction_code map from source_url / notes for labelling.
    # GlobalProgramEntry does not expose .slug, so we label by jurisdiction_code.
    # "missing" sets are jurisdiction_codes of programs whose slugs are not seeded.
    #
    # Strategy: collect all known jurisdiction_codes; map to slugs via the
    # known slug dictionary embedded in migration data. For the gap report
    # we use jurisdiction_code as the identifier since that's what GlobalProgramEntry
    # exposes.

    missing_admin: list[str] = []
    missing_treatment: list[str] = []
    missing_stacking: list[str] = []
    unknown_fields: list[str] = []
    discovery: list[str] = []
    parsed_list: list[str] = []
    fully_seeded: list[str] = []

    # Slug is embedded in source_url for seeded programs or can be inferred.
    # Use a heuristic: check if jurisdiction_code matches any seeded slug pattern.
    # For the gap report, we check programs whose notes/source_url indicate
    # they have an associated slug that should be seeded.
    #
    # Practical approach: the seeded slugs map to specific jurisdiction_codes.
    # We maintain a reverse map here for the gap report.
    _SLUG_TO_JUR: dict[str, str] = {
        # Tier-1 programs
        "uk_avec": "GB", "ie_section_481": "IE", "georgia_eiia": "US-GA",
        "ny_state_film": "US-NY", "ca_film_30": "US-CA", "la_film_production": "US-LA",
        "on_opstc": "CA-ON", "on_ofttc": "CA-ON", "bc_pstc": "CA-BC",
        "qc_film_production": "CA-QC", "ca_federal_cptc": "CA",
        "mu_edb_incentive": "MU", "mt_mfc_rebate": "MT", "gr_cash_rebate": "GR",
        "fr_trip": "FR", "it_tax_credit_foreign": "IT",
        "es_tax_credit_foreign": "ES", "be_tax_shelter": "BE", "de_dfff": "DE",
        "au_location_offset": "AU", "nz_spg_international": "NZ",
        "cy_film_rebate": "CY", "hr_cash_rebate": "HR", "hu_hipa_rebate": "HU",
        "nohfc_production_fund": "CA-ON", "or_opif": "US-OR", "nm_film_production": "US-NM",
        # Wave-2 programs (migration 0026)
        "us_hi_film_tax_credit": "US-HI", "us_ut_film_incentive": "US-UT",
        "us_mn_film_credit": "US-MN", "us_ms_film_credit": "US-MS",
        "us_az_film_credit": "US-AZ", "us_pr_film_incentive": "US-PR",
        "ca_sk_production_grant": "CA-SK", "ca_nl_production_fund": "CA-NL",
        "se_film_incentive": "SE", "no_film_incentive": "NO", "fi_film_incentive": "FI",
        "dk_film_incentive": "DK", "pl_film_incentive": "PL", "bg_film_incentive": "BG",
        "ee_film_incentive": "EE", "lt_film_incentive": "LT", "lv_film_incentive": "LV",
        "sk_film_incentive": "SK", "lu_film_incentive": "LU", "tr_film_incentive": "TR",
        "th_film_incentive": "TH", "my_film_incentive": "MY", "ph_film_incentive": "PH",
        "kr_film_incentive": "KR", "in_national_film": "IN", "lk_film_incentive": "LK",
        "mx_eficine_incentive": "MX", "cl_corfo_incentive": "CL",
        "jm_film_incentive": "JM", "tt_film_incentive": "TT",
        "il_film_incentive": "IL", "qa_film_incentive": "QA", "tn_film_incentive": "TN",
        "ke_film_incentive": "KE", "ng_film_incentive": "NG",
        # Wave-2 grants/funds (migration 0026)
        "eu_eurimages": "EU", "eu_media_fund": "EU", "nordic_ftvf": "NORDIC",
        "ca_cmf": "CA", "ca_telefilm_dev": "CA",
        "gb_bfi_production": "GB", "fr_cnc_production": "FR",
        "au_screen_production": "AU", "nl_hbf": "NL",
        "qa_dfi_fund": "QA", "us_sundance_doc": "US",
        "za_dac_fund": "ZA",
        # Extended programs (migration 0015)
        "us_or_opif": "US-OR", "us_wa_mpcp": "US-WA", "us_il_film_credit": "US-IL",
        "us_nc_film_grant": "US-NC", "us_sc_film_credit": "US-SC",
        "us_ma_film_credit": "US-MA", "us_tx_miip": "US-TX",
        "us_ct_film_credit": "US-CT", "us_pa_film_credit": "US-PA",
        "us_md_film_credit": "US-MD", "us_va_film_credit": "US-VA",
        "us_co_film_incentive": "US-CO", "us_tn_film_incentive": "US-TN",
        "us_ok_ofer": "US-OK", "us_al_film_incentive": "US-AL",
        "us_ky_keiia": "US-KY",
        "ca_ab_fttc": "CA-AB", "ca_mb_fvptc": "CA-MB",
        "ca_ns_pif": "CA-NS", "ca_nb_film_credit": "CA-NB",
        "nl_nfpi": "NL", "at_fisa_plus": "AT", "cz_film_incentive": "CZ",
        "ro_cnc_rebate": "RO", "pt_film_incentive": "PT", "rs_film_rebate": "RS",
        "is_film_reimbursement": "IS", "gb_sct_screen_fund": "GB-SCT",
        "gb_wls_screen_fund": "GB-WLS", "sg_sfc_production": "SG",
        "au_nsw_screen": "AU-NSW", "au_vic_vicscreen": "AU-VIC",
        "au_qld_screen_qld": "AU-QLD",
        "co_film_colombia": "CO", "do_film_incentive": "DO",
        "uy_xxi_incentive": "UY", "ar_incaa_incentive": "AR",
        "br_ancine_incentive": "BR",
        "ae_dpip": "AE", "sa_sfc_rebate": "SA", "jo_rfc_rebate": "JO",
        "ma_ccm_rebate": "MA", "za_nfvf_rebate": "ZA",
        # Wave-3 programs (migration 0029)
        "us_ga_film_credit": "US-GA", "us_la_film_incentive": "US-LA",
        "us_nm_film_credit": "US-NM", "us_ny_film_credit": "US-NY",
        "us_nv_film_incentive": "US-NV", "us_ri_film_credit": "US-RI",
        "bs_film_incentive": "BS", "bb_film_incentive": "BB",
        "pa_film_incentive": "PA", "cr_film_incentive": "CR",
        "pe_film_incentive": "PE", "ec_film_incentive": "EC",
        "eg_film_incentive": "EG", "gh_film_incentive": "GH",
        "rw_film_incentive": "RW", "tz_film_incentive": "TZ",
        "sn_film_incentive": "SN", "kw_film_incentive": "KW",
        "bh_film_incentive": "BH", "ge_film_incentive": "GE",
        "kz_film_incentive": "KZ", "am_film_incentive": "AM",
        "vn_film_incentive": "VN", "id_film_incentive": "ID",
        "kh_film_incentive": "KH", "jp_film_incentive": "JP",
        "tw_film_incentive": "TW", "hk_film_incentive": "HK",
        "al_film_incentive": "AL", "me_film_incentive": "ME",
        "mk_film_incentive": "MK", "ba_film_incentive": "BA",
        "fj_film_incentive": "FJ",
        # Wave-3 grants/funds (migration 0029)
        "ibermedia_programme": "IBERO", "de_fff_bayern": "DE-BY",
        "de_nrw_filmstiftung": "DE-NW", "hk_film_dev_fund": "HK",
        "in_nfdc_coproduction": "IN", "sg_imda_film_fund": "SG",
        "tw_taicca_fund": "TW", "film_i_vast": "SE-VG",
        "acpfilms_fund": "ACP", "us_itvs_fund": "US",
        # Wave-4 programs (migration 0032)
        "az_film_incentive": "AZ", "uz_film_incentive": "UZ",
        "om_film_commission": "OM", "lb_film_incentive": "LB",
        "ve_cnac_fund": "VE", "gy_film_commission": "GY",
        "gt_film_commission": "GT", "na_film_commission": "NA",
        "bw_film_commission": "BW", "et_film_commission": "ET",
        "ci_film_incentive": "CI", "cm_film_incentive": "CM",
        "ao_film_incentive": "AO", "ug_film_commission": "UG",
        "mz_film_incentive": "MZ", "zm_film_commission": "ZM",
        "zw_film_commission": "ZW", "cn_film_incentive": "CN",
        "mn_film_commission": "MN", "mo_film_fund": "MO",
        "bd_film_incentive": "BD",
    }
    # Reverse: jurisdiction_code → slugs (one jur may have multiple slugs)
    _JUR_TO_SLUGS: dict[str, list[str]] = {}
    for slug, jcode in _SLUG_TO_JUR.items():
        _JUR_TO_SLUGS.setdefault(jcode, []).append(slug)

    seeded_admin_jurs: set[str] = set()
    seeded_treatment_jurs: set[str] = set()
    seeded_stacking_jurs: set[str] = set()

    for slug in slugs_with_admin:
        if slug in _SLUG_TO_JUR:
            seeded_admin_jurs.add(_SLUG_TO_JUR[slug])
    for slug in slugs_with_treatment:
        if slug in _SLUG_TO_JUR:
            seeded_treatment_jurs.add(_SLUG_TO_JUR[slug])
    for slug in slugs_with_stacking:
        if slug in _SLUG_TO_JUR:
            seeded_stacking_jurs.add(_SLUG_TO_JUR[slug])

    seen_codes: set[str] = set()
    for p in programs:
        code = p.jurisdiction_code
        if code in seen_codes:
            continue
        seen_codes.add(code)

        if code not in seeded_admin_jurs:
            missing_admin.append(code)
        if code not in seeded_treatment_jurs:
            missing_treatment.append(code)
        if code not in seeded_stacking_jurs:
            missing_stacking.append(code)
        if p.unknown_fields:
            unknown_fields.append(code)
        if p.confidence_tier == "DISCOVERY":
            discovery.append(code)
        elif p.confidence_tier == "PARSED":
            parsed_list.append(code)
        if (code in seeded_admin_jurs and code in seeded_treatment_jurs):
            fully_seeded.append(code)

    total = len(programs)

    def _pct(seeded_count: int) -> float:
        return round(100.0 * seeded_count / total, 1) if total else 0.0

    seeded_admin = total - len(missing_admin)
    seeded_treatment = total - len(missing_treatment)
    seeded_stacking = total - len(missing_stacking)

    # Count programs with at least one resolved UNKNOWN treatment
    resolved_count = len(slugs_with_resolved)

    # Count grant/fund programs and countries covered
    grant_types = {"direct_grant", "co_production_fund", "development_fund"}
    grant_fund_count = sum(1 for p in programs if p.program_type in grant_types)
    incentive_count = total - grant_fund_count
    unique_codes = {p.jurisdiction_code for p in programs}
    countries_covered = len(unique_codes)

    # Estimate discovery completeness: unique top-level country codes / 195 sovereign nations
    top_level_codes = {c for c in unique_codes if "-" not in c and len(c) <= 4
                       and c not in {"EU", "NORDIC", "IBERO", "ACP"}}
    discovery_pct = round(len(top_level_codes) / 195 * 100, 1)

    # Count distinct world regions
    _REGION_MAP: dict[str, str] = {
        # North America
        "US": "North America", "CA": "North America", "MX": "North America",
        # Caribbean & Central America
        "JM": "Caribbean & C.America", "TT": "Caribbean & C.America",
        "DO": "Caribbean & C.America", "BS": "Caribbean & C.America",
        "BB": "Caribbean & C.America", "PA": "Caribbean & C.America",
        "CR": "Caribbean & C.America",
        # South America
        "BR": "South America", "AR": "South America", "CL": "South America",
        "CO": "South America", "UY": "South America", "PE": "South America",
        "EC": "South America",
        # Western Europe
        "GB": "Western Europe", "IE": "Western Europe", "FR": "Western Europe",
        "DE": "Western Europe", "NL": "Western Europe", "BE": "Western Europe",
        "AT": "Western Europe", "LU": "Western Europe", "PT": "Western Europe",
        "ES": "Western Europe", "IT": "Western Europe", "CH": "Western Europe",
        # Northern Europe
        "SE": "Northern Europe", "NO": "Northern Europe", "FI": "Northern Europe",
        "DK": "Northern Europe", "IS": "Northern Europe",
        # Eastern Europe / Balkans
        "PL": "Eastern Europe", "CZ": "Eastern Europe", "SK": "Eastern Europe",
        "HU": "Eastern Europe", "RO": "Eastern Europe", "HR": "Eastern Europe",
        "BG": "Eastern Europe", "RS": "Eastern Europe", "BA": "Eastern Europe",
        "ME": "Eastern Europe", "MK": "Eastern Europe", "AL": "Eastern Europe",
        "EE": "Eastern Europe", "LT": "Eastern Europe", "LV": "Eastern Europe",
        "MT": "Western Europe", "CY": "Western Europe", "GR": "Western Europe",
        # Middle East & Gulf
        "AE": "Middle East & Gulf", "SA": "Middle East & Gulf",
        "QA": "Middle East & Gulf", "JO": "Middle East & Gulf",
        "IL": "Middle East & Gulf", "KW": "Middle East & Gulf",
        "BH": "Middle East & Gulf", "TR": "Middle East & Gulf",
        # Africa
        "MA": "Africa", "TN": "Africa", "EG": "Africa", "SN": "Africa",
        "GH": "Africa", "NG": "Africa", "KE": "Africa", "RW": "Africa",
        "TZ": "Africa", "ZA": "Africa",
        # Africa wave-4
        "NA": "Africa", "BW": "Africa", "ET": "Africa", "CI": "Africa",
        "CM": "Africa", "AO": "Africa", "UG": "Africa",
        "MZ": "Africa", "ZM": "Africa", "ZW": "Africa",
        # Central Asia & Caucasus
        "GE": "Central Asia", "KZ": "Central Asia", "AM": "Central Asia",
        "AZ": "Central Asia", "UZ": "Central Asia",
        # Middle East additions
        "OM": "Middle East & Gulf", "LB": "Middle East & Gulf",
        # South Asia
        "IN": "South & SE Asia", "LK": "South & SE Asia", "BD": "South & SE Asia",
        # Southeast Asia
        "TH": "South & SE Asia", "MY": "South & SE Asia", "PH": "South & SE Asia",
        "SG": "South & SE Asia", "VN": "South & SE Asia", "ID": "South & SE Asia",
        "KH": "South & SE Asia",
        # East Asia
        "KR": "East Asia", "JP": "East Asia", "TW": "East Asia", "HK": "East Asia",
        "CN": "East Asia", "MN": "East Asia", "MO": "East Asia",
        # South America additions
        "VE": "South America", "GY": "South America",
        # Central America
        "GT": "Caribbean & C.America",
        # Oceania & Pacific
        "AU": "Oceania & Pacific", "NZ": "Oceania & Pacific", "FJ": "Oceania & Pacific",
        # Supranational
        "MU": "Indian Ocean",
    }
    regions_hit: set[str] = set()
    for code in unique_codes:
        # For sub-nationals (e.g. US-GA), use the parent country code
        parent = code.split("-")[0]
        region = _REGION_MAP.get(code) or _REGION_MAP.get(parent)
        if region:
            regions_hit.add(region)

    # v0.8.0 — search coverage statistics
    countries_with_prog = len(top_level_codes)
    no_program_count = len(NO_PROGRAM_CODES)
    searched_total = countries_with_prog + no_program_count
    not_yet_searched = max(0, 195 - searched_total)
    global_search_pct = round(searched_total / 195 * 100, 1)

    # Identify top unsearched regions: regions with most remaining UN countries
    _ALL_UN_REGIONS: dict[str, list[str]] = {
        "Sub-Saharan Africa": [
            "DZ", "LY", "SD", "SO", "ER", "DJ", "SS", "CF", "CG", "GQ", "GA",
            "SL", "LR", "GN", "GW", "BF", "NE", "TD", "MR", "CV", "ST", "KM",
            "MG", "MW", "LS", "SZ",
        ],
        "Middle East": ["SA", "JO", "IR", "SY", "PS"],
        "South Asia": ["AF", "MV"],
        "Pacific Islands": [],  # PG, WS, VU, TO, SB now searched
        "Central America": [],  # GT has program; HN, SV, NI searched
    }
    _searched_codes = top_level_codes | NO_PROGRAM_CODES
    top_unsearched: list[str] = []
    for region_name, candidates in _ALL_UN_REGIONS.items():
        remaining = [c for c in candidates if c not in _searched_codes]
        if remaining:
            top_unsearched.append(f"{region_name} ({len(remaining)} unsearched)")
    top_unsearched.sort(key=lambda x: -int(x.split("(")[1].split()[0]))

    return IntelligenceGapReport(
        programs_missing_admin_details=sorted(missing_admin),
        programs_missing_spend_treatment=sorted(missing_treatment),
        programs_missing_stacking_rules=sorted(missing_stacking),
        programs_with_unknown_fields=sorted(unknown_fields),
        discovery_programs=sorted(discovery),
        parsed_programs=sorted(parsed_list),
        fully_seeded_programs=sorted(fully_seeded),
        total_programs=total,
        admin_details_seeded=len(slugs_with_admin),
        spend_treatment_seeded=len(slugs_with_treatment),
        stacking_rules_seeded=len(slugs_with_stacking),
        admin_coverage_pct=_pct(seeded_admin),
        treatment_coverage_pct=_pct(seeded_treatment),
        stacking_coverage_pct=_pct(seeded_stacking),
        resolved_treatment_programs=resolved_count,
        grant_fund_programs=grant_fund_count,
        countries_covered=countries_covered,
        total_incentive_programs=incentive_count,
        regions_covered=len(regions_hit),
        discovery_completion_pct=discovery_pct,
        countries_with_program=countries_with_prog,
        countries_searched_no_program=no_program_count,
        countries_not_yet_searched=not_yet_searched,
        global_search_coverage_pct=global_search_pct,
        top_unsearched_regions=top_unsearched,
    )


def format_coverage_table(report: CoverageReport) -> str:
    """Render a plain-text summary table for the coverage report."""
    lines = [
        f"Global Incentive Coverage Report v{report.report_version}",
        f"Jurisdictions: {report.total_jurisdictions}  "
        f"Programs: {report.total_programs}  "
        f"Benchmarks: {report.total_benchmarks}",
        f"Programs — VERIFIED: {report.verified_programs}  "
        f"PARSED: {report.parsed_programs}  "
        f"DISCOVERY: {report.discovery_programs}",
        f"Benchmarks — VERIFIED: {report.verified_benchmarks}  "
        f"PARSED: {report.parsed_benchmarks}  "
        f"DISCOVERY: {report.discovery_benchmarks}",
        "",
        f"{'Code':<6} {'Name':<30} {'Progs':>5} {'Bmarks':>6} {'V':>3} {'P':>3} {'D':>3} {'Blockers':>8}",
        "-" * 72,
    ]
    for jc in report.by_jurisdiction:
        lines.append(
            f"{jc.jurisdiction_code:<6} {jc.jurisdiction_name:<30} "
            f"{jc.program_count:>5} {jc.benchmark_count:>6} "
            f"{jc.verified_count:>3} {jc.parsed_count:>3} {jc.discovery_count:>3} "
            f"{len(jc.budget_testing_blockers):>8}"
        )
    return "\n".join(lines)
