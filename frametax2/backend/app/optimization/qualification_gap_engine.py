"""
qualification_gap_engine.py — Phase F2: Gap analysis between project profile and program requirements.

For each program in a structure, identify what's missing to qualify.
Pure Python, no DB access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QualificationGap:
    program_slug: str
    program_name: str
    gap_type: str  # "missing_spend" | "missing_crew" | "missing_entity" | "missing_broadcaster" | "missing_co_producer" | "missing_cultural_points" | "missing_post_spend" | "missing_vfx_spend" | "missing_regional_spend" | "missing_broadcaster_commitment" | "blocker"
    description: str
    current_value: Any
    required_value: Any
    gap_magnitude: float  # 0-1, fraction of gap remaining
    estimated_value_unlocked_usd: float
    recommendation: str
    friction_score: float  # 1-10
    is_blocker: bool


@dataclass
class GapAnalysisResult:
    project_profile: dict
    structure_slugs: list[str]
    total_gaps: int
    blocking_gaps: list[QualificationGap]
    addressable_gaps: list[QualificationGap]
    all_gaps: list[QualificationGap]
    total_value_at_risk_usd: float
    total_value_unlockable_usd: float
    gap_summary: str


# ---------------------------------------------------------------------------
# Program rate table (base incentive rates for value estimation)
# ---------------------------------------------------------------------------

_PROGRAM_RATES: dict[str, float] = {
    "uk_avec": 0.34,
    "ie_section_481": 0.32,
    "fr_cnc_production": 0.30,
    "fr_trip": 0.30,
    "ca_federal_cptc": 0.25,
    "ca_cmf": 0.10,
    "ca_cmf_tv": 0.10,
    "au_producer_offset": 0.40,
    "au_location_offset": 0.20,
    "au_pdv_offset": 0.20,
    "de_dfff": 0.25,
    "nz_screen_production_grant": 0.20,
    "sg_film_commission": 0.40,
    "us_georgia_eitc": 0.30,
    "us_new_york_credit": 0.30,
    "eu_eurimages": 0.10,
    "eu_media_fund": 0.05,
    "kr_kofic_rebate": 0.20,
    "hu_nfi_grants": 0.30,
    "cz_czech_film_fund": 0.20,
    "pl_pisf_grants": 0.30,
    "it_tax_credit_domestic": 0.40,
    "it_tax_credit_foreign": 0.25,
    "es_canary_islands_ztlc": 0.50,
    "es_spain_ife": 0.30,
    "mt_mfc_cash_rebate": 0.40,
    "rs_serbia_film_commission": 0.25,
    "be_screen_brussels": 0.29,
    "nl_netherlands_film_fund": 0.30,
    "at_ofi_grants": 0.25,
    "se_sf_production": 0.25,
    "no_nfi_grants": 0.30,
    "fi_ses_grants": 0.25,
    "dk_dfi_support": 0.20,
    "pt_ica_grant": 0.25,
    "gr_ekome_rebate": 0.40,
    "ro_cnc_grant": 0.30,
    "bg_nfc_grant": 0.25,
    "hr_havc_grant": 0.20,
    "za_nfvf_incentive": 0.20,
    "ma_ccm_grant": 0.15,
    "ae_dxb_dpi": 0.30,
    "ae_adfc_rebate": 0.30,
    "il_israel_film_fund": 0.20,
    "jp_jfc_incentive": 0.15,
    "th_thai_incentive": 0.15,
    "in_india_incentive": 0.15,
    "mx_imcine_incentive": 0.20,
    "br_ancine_fsac": 0.20,
    "ar_incaa_incentive": 0.20,
    "cl_cntv_incentive": 0.15,
    "co_focine_incentive": 0.15,
}

# Minimum spend requirements (fraction of total budget)
_MIN_SPEND_PCTS: dict[str, float] = {
    "uk_avec": 0.10,
    "ie_section_481": 0.05,  # min €125k
    "fr_cnc_production": 0.15,
    "fr_trip": 0.15,
    "ca_federal_cptc": 0.15,
    "ca_cmf": 0.10,
    "au_producer_offset": 0.15,
    "de_dfff": 0.10,
    "kr_kofic_rebate": 0.10,
    "nz_screen_production_grant": 0.10,
    "hu_nfi_grants": 0.10,
    "cz_czech_film_fund": 0.10,
    "mt_mfc_cash_rebate": 0.10,
    "gr_ekome_rebate": 0.10,
}

# Jurisdiction spend profile key mapping
_JURISDICTION_SPEND_KEY: dict[str, str] = {
    "uk_avec": "uk_spend_pct",
    "ie_section_481": "ie_spend_pct",
    "fr_cnc_production": "fr_spend_pct",
    "fr_trip": "fr_spend_pct",
    "ca_federal_cptc": "ca_spend_pct",
    "ca_cmf": "ca_spend_pct",
    "ca_cmf_tv": "ca_spend_pct",
    "au_producer_offset": "au_spend_pct",
    "au_location_offset": "au_spend_pct",
    "de_dfff": "de_spend_pct",
    "hu_nfi_grants": "hu_spend_pct",
    "cz_czech_film_fund": "cz_spend_pct",
    "kr_kofic_rebate": "kr_spend_pct",
    "nz_screen_production_grant": "nz_spend_pct",
    "mt_mfc_cash_rebate": "mt_spend_pct",
    "gr_ekome_rebate": "gr_spend_pct",
    "pl_pisf_grants": "pl_spend_pct",
    "rs_serbia_film_commission": "rs_spend_pct",
    "bg_nfc_grant": "bg_spend_pct",
    "ro_cnc_grant": "ro_spend_pct",
}

# Programs requiring local entity
_REQUIRES_LOCAL_ENTITY: dict[str, str] = {
    "ie_section_481": "has_irish_company",
    "fr_cnc_production": "has_french_company",
    "ca_federal_cptc": "has_canadian_company",
    "ca_cmf": "has_canadian_company",
    "uk_avec": "has_uk_company",
}

# Programs requiring broadcaster commitment
_REQUIRES_BROADCASTER: set[str] = {
    "ca_cmf", "ca_cmf_tv", "ca_bell_fund",
    "fr_cnc_production",
    "rte_drama_fund", "bbc_drama_production",
}

# Programs requiring co-producers (min country count)
_REQUIRES_CO_PRODUCER: dict[str, int] = {
    "eu_eurimages": 2,
    "eu_media_fund": 2,
    "ca_cmf": 1,
}


def _estimate_value(program_slug: str, total_budget_usd: float, spend_pct: float) -> float:
    """Estimate incentive value for a program given spend percentage."""
    rate = _PROGRAM_RATES.get(program_slug, 0.20)
    return rate * total_budget_usd * max(spend_pct, 0.10)


def _check_spend_gap(
    program_slug: str,
    profile: dict,
    total_budget_usd: float,
) -> QualificationGap | None:
    """Check if spend requirement is met."""
    spend_key = _JURISDICTION_SPEND_KEY.get(program_slug)
    if spend_key is None:
        return None

    required_pct = _MIN_SPEND_PCTS.get(program_slug, 0.10)
    current_pct = profile.get(spend_key, 0.0) or 0.0

    if current_pct >= required_pct:
        return None

    gap_magnitude = (required_pct - current_pct) / required_pct
    value = _estimate_value(program_slug, total_budget_usd, required_pct)

    return QualificationGap(
        program_slug=program_slug,
        program_name=program_slug.replace("_", " ").title(),
        gap_type="missing_spend",
        description=f"{program_slug}: spend {current_pct:.0%} < required {required_pct:.0%}",
        current_value=current_pct,
        required_value=required_pct,
        gap_magnitude=gap_magnitude,
        estimated_value_unlocked_usd=value,
        recommendation=f"Increase {spend_key.replace('_', ' ')} from {current_pct:.0%} to {required_pct:.0%}",
        friction_score=5.0,
        is_blocker=current_pct == 0.0,
    )


def _check_entity_gap(
    program_slug: str,
    profile: dict,
    total_budget_usd: float,
) -> QualificationGap | None:
    """Check if local entity requirement is met."""
    entity_key = _REQUIRES_LOCAL_ENTITY.get(program_slug)
    if entity_key is None:
        return None

    has_entity = profile.get(entity_key, False)
    if has_entity:
        return None

    value = _estimate_value(program_slug, total_budget_usd, 0.15)

    return QualificationGap(
        program_slug=program_slug,
        program_name=program_slug.replace("_", " ").title(),
        gap_type="missing_entity",
        description=f"{program_slug}: requires local {entity_key.replace('has_', '').replace('_', ' ')} entity",
        current_value=False,
        required_value=True,
        gap_magnitude=1.0,
        estimated_value_unlocked_usd=value,
        recommendation=f"Establish a {entity_key.replace('has_', '').replace('_', ' ')} registered in the required jurisdiction",
        friction_score=7.0,
        is_blocker=True,
    )


def _check_broadcaster_gap(
    program_slug: str,
    profile: dict,
    total_budget_usd: float,
) -> QualificationGap | None:
    """Check if broadcaster commitment is required."""
    if program_slug not in _REQUIRES_BROADCASTER:
        return None

    has_commitment = profile.get("has_broadcaster_commitment", False)
    if has_commitment:
        return None

    value = _estimate_value(program_slug, total_budget_usd, 0.10)

    return QualificationGap(
        program_slug=program_slug,
        program_name=program_slug.replace("_", " ").title(),
        gap_type="missing_broadcaster_commitment",
        description=f"{program_slug}: requires broadcaster commitment/license agreement",
        current_value=False,
        required_value=True,
        gap_magnitude=1.0,
        estimated_value_unlocked_usd=value,
        recommendation="Secure broadcaster license agreement before application",
        friction_score=6.0,
        is_blocker=True,
    )


def _check_co_producer_gap(
    program_slug: str,
    profile: dict,
    total_budget_usd: float,
) -> QualificationGap | None:
    """Check if co-producer country requirement is met."""
    min_count = _REQUIRES_CO_PRODUCER.get(program_slug)
    if min_count is None:
        return None

    current_count = int(profile.get("co_production_country_count", 0) or 0)
    if current_count >= min_count:
        return None

    value = _estimate_value(program_slug, total_budget_usd, 0.10)
    gap_magnitude = (min_count - current_count) / min_count

    return QualificationGap(
        program_slug=program_slug,
        program_name=program_slug.replace("_", " ").title(),
        gap_type="missing_co_producer",
        description=(
            f"{program_slug}: requires {min_count} co-production "
            f"countr{'y' if min_count == 1 else 'ies'}, currently {current_count}"
        ),
        current_value=current_count,
        required_value=min_count,
        gap_magnitude=gap_magnitude,
        estimated_value_unlocked_usd=value,
        recommendation=f"Add {min_count - current_count} qualifying co-production partner(s)",
        friction_score=7.5,
        is_blocker=current_count == 0,
    )


def _check_cultural_points_gap(
    program_slug: str,
    profile: dict,
    total_budget_usd: float,
) -> QualificationGap | None:
    """Check cultural test points for programs that require them."""
    try:
        from app.optimization.qualification_path_engine import analyse_qualification
        analysis = analyse_qualification(program_slug, profile)
        if analysis.is_currently_qualifying:
            return None
        if analysis.current_score is not None and analysis.required_score is not None:
            current = analysis.current_score
            required = analysis.required_score
            if current < required:
                gap_magnitude = (required - current) / required
                value = _estimate_value(program_slug, total_budget_usd, 0.15)
                return QualificationGap(
                    program_slug=program_slug,
                    program_name=program_slug.replace("_", " ").title(),
                    gap_type="missing_cultural_points",
                    description=f"{program_slug}: cultural test score {current}/{required}",
                    current_value=current,
                    required_value=required,
                    gap_magnitude=gap_magnitude,
                    estimated_value_unlocked_usd=value,
                    recommendation=f"Increase cultural test score by {required - current} points",
                    friction_score=4.0,
                    is_blocker=current < (required * 0.5),
                )
    except Exception:
        pass
    return None


def analyse_gaps(
    structure_slugs: list[str],
    project_profile: dict,
    total_budget_usd: float = 5_000_000,
) -> GapAnalysisResult:
    """
    Analyse qualification gaps for all programs in structure_slugs.

    Returns a GapAnalysisResult with blocking and addressable gaps,
    value at risk, and value unlockable.
    """
    all_gaps: list[QualificationGap] = []

    for slug in structure_slugs:
        # Check spend gap
        spend_gap = _check_spend_gap(slug, project_profile, total_budget_usd)
        if spend_gap:
            all_gaps.append(spend_gap)

        # Check entity gap
        entity_gap = _check_entity_gap(slug, project_profile, total_budget_usd)
        if entity_gap:
            all_gaps.append(entity_gap)

        # Check broadcaster gap
        broadcaster_gap = _check_broadcaster_gap(slug, project_profile, total_budget_usd)
        if broadcaster_gap:
            all_gaps.append(broadcaster_gap)

        # Check co-producer gap
        co_producer_gap = _check_co_producer_gap(slug, project_profile, total_budget_usd)
        if co_producer_gap:
            all_gaps.append(co_producer_gap)

        # Check cultural points
        cultural_gap = _check_cultural_points_gap(slug, project_profile, total_budget_usd)
        if cultural_gap:
            all_gaps.append(cultural_gap)

    blocking_gaps = [g for g in all_gaps if g.is_blocker]
    addressable_gaps = [g for g in all_gaps if not g.is_blocker]

    total_value_at_risk = sum(g.estimated_value_unlocked_usd for g in blocking_gaps)
    total_value_unlockable = sum(g.estimated_value_unlocked_usd for g in addressable_gaps)

    if not all_gaps:
        gap_summary = "No qualification gaps detected for the selected programs."
    else:
        blocking_count = len(blocking_gaps)
        addressable_count = len(addressable_gaps)
        gap_summary = (
            f"{len(all_gaps)} gap(s) found: {blocking_count} blocking "
            f"(${total_value_at_risk:,.0f} at risk), "
            f"{addressable_count} addressable "
            f"(${total_value_unlockable:,.0f} unlockable)."
        )

    return GapAnalysisResult(
        project_profile=project_profile,
        structure_slugs=structure_slugs,
        total_gaps=len(all_gaps),
        blocking_gaps=blocking_gaps,
        addressable_gaps=addressable_gaps,
        all_gaps=all_gaps,
        total_value_at_risk_usd=total_value_at_risk,
        total_value_unlockable_usd=total_value_unlockable,
        gap_summary=gap_summary,
    )
