"""
structure_generator.py — Phase F4: Production structure generation engine.

Generates candidate production structures based on jurisdiction selection,
budget, and production type. Pure Python, no DB access.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.data.structure_graph_model import get_edges_from, get_edges_by_type


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class GeneratedStructure:
    structure_id: str
    structure_type: str  # "single_country" | "dual_country" | "treaty_coproduction" | "majority_minority" | "broadcaster_supported" | "regional_supported" | "multi_party"
    primary_jurisdiction: str
    secondary_jurisdictions: list[str]
    program_slugs: list[str]
    programs_unlocked: list[str]
    grants_unlocked: list[str]
    funds_unlocked: list[str]
    broadcasters_unlocked: list[str]
    estimated_soft_money_usd: float
    estimated_total_incentive_usd: float
    qualification_risk: str  # "LOW" | "MEDIUM" | "HIGH"
    confidence: str  # "HIGH" | "MEDIUM" | "LOW"
    required_conditions: list[str]
    notes: str


# ---------------------------------------------------------------------------
# Jurisdiction → program mappings
# ---------------------------------------------------------------------------

_JURISDICTION_PROGRAMS: dict[str, list[str]] = {
    "GB": ["uk_avec", "gb_bbc_films", "gb_film4"],
    "IE": ["ie_section_481", "ie_screen_ireland_dev"],
    "FR": ["fr_cnc_production", "fr_trip", "fr_cnc_animation"],
    "DE": ["de_dfff"],
    "CA": ["ca_federal_cptc", "ca_cmf", "ca_cmf_tv"],
    "AU": ["au_producer_offset", "au_pdv_offset"],
    "NZ": ["nz_screen_production_grant"],
    "US": ["us_georgia_eitc", "us_new_york_credit"],
    "HU": ["hu_nfi_grants"],
    "CZ": ["cz_czech_film_fund"],
    "PL": ["pl_pisf_grants"],
    "RS": ["rs_serbia_film_commission"],
    "MT": ["mt_mfc_cash_rebate"],
    "GR": ["gr_ekome_rebate"],
    "IT": ["it_tax_credit_domestic"],
    "ES": ["es_spain_ife", "es_canary_islands_ztlc"],
    "BE": ["be_screen_brussels"],
    "NL": ["nl_netherlands_film_fund"],
    "AT": ["at_ofi_grants"],
    "SE": ["se_sf_production"],
    "NO": ["no_nfi_grants"],
    "FI": ["fi_ses_grants"],
    "DK": ["dk_dfi_support"],
    "PT": ["pt_ica_grant"],
    "RO": ["ro_cnc_grant"],
    "BG": ["bg_nfc_grant"],
    "HR": ["hr_havc_grant"],
    "KR": ["kr_kofic_rebate"],
    "ZA": ["za_nfvf_incentive"],
    "AE": ["ae_dxb_dpi"],
    "JP": ["jp_jfc_incentive"],
    "TH": ["th_thai_incentive"],
    "MX": ["mx_imcine_incentive"],
    "BR": ["br_ancine_fsac"],
    "AR": ["ar_incaa_incentive"],
    "IL": ["il_israel_film_fund"],
    "MA": ["ma_ccm_grant"],
    "SA": [],
}

# Common state-level codes → jurisdiction
_STATE_TO_JURISDICTION: dict[str, str] = {
    "US-GA": "US", "US-NY": "US", "US-CA": "US",
    "US-LA": "US", "US-NM": "US", "US-MA": "US",
}

# Jurisdiction → base incentive rate (for estimation)
_JURISDICTION_RATE: dict[str, float] = {
    "GB": 0.34, "IE": 0.32, "FR": 0.30, "DE": 0.25,
    "CA": 0.40, "AU": 0.40, "NZ": 0.20, "US": 0.30,
    "HU": 0.30, "CZ": 0.20, "PL": 0.30, "RS": 0.25,
    "MT": 0.40, "GR": 0.40, "IT": 0.40, "ES": 0.30,
    "BE": 0.29, "NL": 0.30, "AT": 0.25, "SE": 0.25,
    "NO": 0.25, "FI": 0.25, "DK": 0.20, "PT": 0.25,
    "RO": 0.30, "BG": 0.25, "HR": 0.20, "KR": 0.20,
    "ZA": 0.20, "AE": 0.30, "JP": 0.15, "TH": 0.15,
    "MX": 0.20, "BR": 0.20, "AR": 0.20, "IL": 0.20,
    "MA": 0.15, "SA": 0.0,
}

# Bilateral treaties by jurisdiction pair
_BILATERAL_TREATIES: dict[frozenset, str] = {
    frozenset({"GB", "CA"}): "uk-ca-bilateral",
    frozenset({"GB", "IE"}): "uk-ie-bilateral",
    frozenset({"CA", "FR"}): "ca-fr-bilateral",
    frozenset({"CA", "AU"}): "ca-au-bilateral",
    frozenset({"FR", "DE"}): "fr-de-bilateral",
    frozenset({"GB", "AU"}): "uk-au-bilateral",
    frozenset({"FR", "IT"}): "it-fr-bilateral",
    frozenset({"GB", "NZ"}): "uk-nz-bilateral",
    frozenset({"DE", "AU"}): "de-au-bilateral",
    frozenset({"FR", "BE"}): "fr-be-bilateral",
    frozenset({"CA", "IE"}): "ca-ie-bilateral",
    frozenset({"AU", "NZ"}): "au-nz-bilateral",
}

# Regional fund complements
_REGIONAL_FUNDS: dict[str, list[str]] = {
    "DE": ["bavarian_film_fund", "berlin_mbb_fund"],
    "GB": ["gb_lon_film_london", "gb_sct_screen_production", "gb_wls_film_fund"],
    "CA": ["ca_bc_interactive", "ca_on_ocase"],
    "AU": ["au_vic_film_victoria", "au_tas_screen"],
    "FR": ["fr_regional_funds"],
    "ES": ["es_canary_islands_ztlc"],
    "IT": ["it_regional_fund"],
    "NO": ["no_vgn_viken", "no_rog_vestnorsk"],
    "SE": ["film_i_vast"],
    "DK": ["dk_cph_film_fund"],
}

# Broadcaster funds by jurisdiction
_BROADCASTER_FUNDS: dict[str, list[str]] = {
    "GB": ["gb_bbc_films", "gb_film4", "bbc_drama_production", "sky_uk_drama"],
    "IE": ["rte_drama_fund", "virgin_media_tv_fund"],
    "FR": ["france_televisions_fund", "canal_plus_fund"],
    "CA": ["cbc_original", "bravo_factual", "ca_bell_fund"],
    "AU": ["abc_television_fund"],
    "SE": ["se_svt"],
    "NO": ["no_nrk"],
    "DK": ["dk_dr"],
    "FI": ["fi_yle"],
}


def _normalize_jurisdiction(jur: str) -> str:
    """Normalize state codes to country codes."""
    return _STATE_TO_JURISDICTION.get(jur, jur)


def _get_programs_for_jurisdiction(jur: str) -> list[str]:
    """Get primary program slugs for a jurisdiction."""
    normalized = _normalize_jurisdiction(jur)
    return _JURISDICTION_PROGRAMS.get(normalized, [])


def _get_treaty_for_pair(jur_a: str, jur_b: str) -> str | None:
    """Get bilateral treaty slug for a jurisdiction pair."""
    normalized_a = _normalize_jurisdiction(jur_a)
    normalized_b = _normalize_jurisdiction(jur_b)
    return _BILATERAL_TREATIES.get(frozenset({normalized_a, normalized_b}))


def _estimate_soft_money(
    jurisdictions: list[str],
    total_budget_usd: float,
    structure_type: str,
) -> tuple[float, float]:
    """
    Estimate soft money (incentives only) and total incentive value.
    Returns (soft_money_usd, total_incentive_usd).
    """
    if not jurisdictions:
        return 0.0, 0.0

    normalized = [_normalize_jurisdiction(j) for j in jurisdictions]
    rates = [_JURISDICTION_RATE.get(j, 0.15) for j in normalized]

    # Primary gets largest allocation
    primary_spend_pct = 0.60 if len(jurisdictions) == 1 else 0.40
    secondary_spend_pct = (1.0 - primary_spend_pct) / max(len(jurisdictions) - 1, 1)

    total = 0.0
    for i, rate in enumerate(rates):
        spend_pct = primary_spend_pct if i == 0 else secondary_spend_pct
        total += rate * total_budget_usd * spend_pct

    # Treaty co-productions get bonus for unlocking both sides
    if structure_type in ("treaty_coproduction", "majority_minority") and len(jurisdictions) >= 2:
        total *= 1.15  # 15% bonus for bilateral unlock

    # Regional and broadcaster-supported get modest boost
    if structure_type in ("regional_supported", "broadcaster_supported"):
        total *= 1.05

    soft_money = total * 0.90  # 90% of total is rebatable soft money estimate
    return soft_money, total


def _assess_risk(
    structure_type: str,
    jurisdictions: list[str],
    include_treaty: bool,
) -> str:
    """Assess qualification risk level."""
    if structure_type == "single_country":
        return "LOW"
    if structure_type == "multi_party":
        return "HIGH"
    if include_treaty and len(jurisdictions) >= 2:
        return "MEDIUM"
    return "MEDIUM"


def generate_structures(
    primary_jurisdiction: str,
    secondary_jurisdictions: list[str] | None = None,
    total_budget_usd: float = 5_000_000,
    production_type: str = "feature",  # "feature" | "series" | "documentary" | "animation"
    include_treaty: bool = True,
    include_regional: bool = True,
    include_broadcaster: bool = True,
) -> list[GeneratedStructure]:
    """
    Generate candidate production structures based on jurisdiction selection.

    Returns a list of GeneratedStructure objects ordered by estimated incentive value.
    """
    if secondary_jurisdictions is None:
        secondary_jurisdictions = []

    structures: list[GeneratedStructure] = []
    all_jurisdictions = [primary_jurisdiction] + secondary_jurisdictions
    primary_norm = _normalize_jurisdiction(primary_jurisdiction)

    # 1. Single-country structure
    primary_programs = _get_programs_for_jurisdiction(primary_jurisdiction)
    if primary_programs:
        soft_money, total_incentive = _estimate_soft_money(
            [primary_jurisdiction], total_budget_usd, "single_country"
        )
        regional_grants = _REGIONAL_FUNDS.get(primary_norm, []) if include_regional else []
        broadcaster_funds = _BROADCASTER_FUNDS.get(primary_norm, []) if include_broadcaster else []

        structures.append(GeneratedStructure(
            structure_id=str(uuid.uuid4())[:8],
            structure_type="single_country",
            primary_jurisdiction=primary_jurisdiction,
            secondary_jurisdictions=[],
            program_slugs=primary_programs,
            programs_unlocked=primary_programs,
            grants_unlocked=regional_grants,
            funds_unlocked=[],
            broadcasters_unlocked=broadcaster_funds,
            estimated_soft_money_usd=soft_money,
            estimated_total_incentive_usd=total_incentive,
            qualification_risk="LOW",
            confidence="HIGH",
            required_conditions=[
                f"Must spend minimum qualifying percentage in {primary_jurisdiction}",
                "Must satisfy cultural test if required",
            ],
            notes=f"Baseline {primary_jurisdiction} single-country structure.",
        ))

    # 2. Multi-country / dual-country structures
    for sec_jur in secondary_jurisdictions:
        sec_programs = _get_programs_for_jurisdiction(sec_jur)
        treaty_slug = _get_treaty_for_pair(primary_jurisdiction, sec_jur) if include_treaty else None

        structure_type = "treaty_coproduction" if treaty_slug else "dual_country"
        all_programs = list(set(primary_programs + sec_programs))

        soft_money, total_incentive = _estimate_soft_money(
            [primary_jurisdiction, sec_jur], total_budget_usd, structure_type
        )

        sec_norm = _normalize_jurisdiction(sec_jur)
        regional_grants = (
            _REGIONAL_FUNDS.get(primary_norm, []) + _REGIONAL_FUNDS.get(sec_norm, [])
        ) if include_regional else []
        broadcaster_funds = (
            _BROADCASTER_FUNDS.get(primary_norm, []) + _BROADCASTER_FUNDS.get(sec_norm, [])
        ) if include_broadcaster else []

        required_conditions = [
            f"Must meet minimum spend thresholds in both {primary_jurisdiction} and {sec_jur}",
        ]
        if treaty_slug:
            required_conditions.append(f"Must comply with {treaty_slug} co-production treaty")
            required_conditions.append("Must have registered co-producers in both countries")

        structures.append(GeneratedStructure(
            structure_id=str(uuid.uuid4())[:8],
            structure_type=structure_type,
            primary_jurisdiction=primary_jurisdiction,
            secondary_jurisdictions=[sec_jur],
            program_slugs=all_programs,
            programs_unlocked=all_programs,
            grants_unlocked=regional_grants[:4],  # limit to top 4
            funds_unlocked=[treaty_slug] if treaty_slug else [],
            broadcasters_unlocked=broadcaster_funds[:4],
            estimated_soft_money_usd=soft_money,
            estimated_total_incentive_usd=total_incentive,
            qualification_risk=_assess_risk(structure_type, [primary_jurisdiction, sec_jur], bool(treaty_slug)),
            confidence="HIGH" if treaty_slug else "MEDIUM",
            required_conditions=required_conditions,
            notes=(
                f"{primary_jurisdiction}+{sec_jur} {'treaty' if treaty_slug else 'bilateral'} "
                f"co-production structure."
            ),
        ))

        # Also generate majority/minority variant if treaty exists
        if treaty_slug:
            structures.append(GeneratedStructure(
                structure_id=str(uuid.uuid4())[:8],
                structure_type="majority_minority",
                primary_jurisdiction=primary_jurisdiction,
                secondary_jurisdictions=[sec_jur],
                program_slugs=all_programs,
                programs_unlocked=all_programs,
                grants_unlocked=regional_grants[:3],
                funds_unlocked=[treaty_slug],
                broadcasters_unlocked=broadcaster_funds[:2],
                estimated_soft_money_usd=soft_money * 0.85,  # slight discount for minority complexity
                estimated_total_incentive_usd=total_incentive * 0.85,
                qualification_risk="MEDIUM",
                confidence="MEDIUM",
                required_conditions=[
                    f"Majority producer in {primary_jurisdiction} (min 60% spend)",
                    f"Minority co-producer in {sec_jur} (20-40% spend)",
                    f"Treaty {treaty_slug} certification required",
                ],
                notes=f"Majority/minority treaty structure: {primary_jurisdiction} majority, {sec_jur} minority.",
            ))

    # 3. Multi-party structure (3+ jurisdictions)
    if len(secondary_jurisdictions) >= 2:
        all_programs_multi = list(set(
            [p for j in all_jurisdictions for p in _get_programs_for_jurisdiction(j)]
        ))

        soft_money, total_incentive = _estimate_soft_money(
            all_jurisdictions, total_budget_usd, "multi_party"
        )

        all_regional = [
            g for j in all_jurisdictions
            for g in _REGIONAL_FUNDS.get(_normalize_jurisdiction(j), [])
        ] if include_regional else []
        all_broadcasters = [
            b for j in all_jurisdictions
            for b in _BROADCASTER_FUNDS.get(_normalize_jurisdiction(j), [])
        ] if include_broadcaster else []

        structures.append(GeneratedStructure(
            structure_id=str(uuid.uuid4())[:8],
            structure_type="multi_party",
            primary_jurisdiction=primary_jurisdiction,
            secondary_jurisdictions=secondary_jurisdictions,
            program_slugs=all_programs_multi,
            programs_unlocked=all_programs_multi,
            grants_unlocked=all_regional[:6],
            funds_unlocked=[],
            broadcasters_unlocked=all_broadcasters[:6],
            estimated_soft_money_usd=soft_money,
            estimated_total_incentive_usd=total_incentive,
            qualification_risk="HIGH",
            confidence="LOW",
            required_conditions=[
                f"Registered co-producers required in all {len(all_jurisdictions)} jurisdictions",
                "Eurimages or European Convention co-production framework recommended",
                "Complex spend allocation plan required",
            ],
            notes=f"Multi-party structure across {', '.join(all_jurisdictions)}. High administrative complexity.",
        ))

    # Sort by estimated total incentive descending
    structures.sort(key=lambda s: s.estimated_total_incentive_usd, reverse=True)
    return structures
