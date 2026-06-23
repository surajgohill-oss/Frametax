"""
stacking_rules.py — Static stacking rule lookup for the Phase E optimizer.

Rules are encoded from Phase D migrations (0022, 0039, 0044) and from
structural analysis of the global incentive inventory.

No DB access. These rules parallel what is seeded in the DB via migrations
but are expressed in terms of program types and jurisdiction codes so the
optimizer can operate from GlobalProgramEntry without slug lookups.

Rule encoding hierarchy (first match wins):
  1. Named slug-pair rules (from migration data — highest precision)
  2. Structural type rules (government_assistance programs → spend_reduction)
  3. Default rules (grant + primary = allowed; same-type same-jur = mutually_exclusive)
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry
from app.optimization.types import StackingViolation


# ---------------------------------------------------------------------------
# Slug inference: maps name fragments to known slugs for high-precision rules
# ---------------------------------------------------------------------------

_NAME_SLUG_RULES: list[tuple[str, str, str]] = [
    # (jurisdiction_code, name_fragment_lower, slug)
    ("FR",     "trip",                        "fr_trip"),
    ("FR",     "avances sur recettes",        "fr_cnc_production"),
    ("FR",     "cnc france",                  "fr_cnc_production"),
    ("GB",     "audio visual expenditure",    "uk_avec"),
    ("GB",     "avec",                        "uk_avec"),
    ("GB",     "bfi film fund",               "gb_bfi_production"),
    ("IE",     "section 481",                 "ie_section_481"),
    ("MT",     "malta film commission",       "mt_mfc_rebate"),
    ("GR",     "greece cash rebate",          "gr_cash_rebate"),
    ("MU",     "mauritius edb",               "mu_edb_incentive"),
    ("MU",     "edb film rebate",             "mu_edb_incentive"),
    ("CA",     "canada production tax credit","ca_federal_cptc"),
    ("CA",     "cptc",                        "ca_federal_cptc"),
    ("CA",     "canada media fund",           "ca_cmf"),
    ("CA",     "cmf",                         "ca_cmf"),
    ("CA",     "telefilm canada",             "ca_telefilm_dev"),
    ("CA-ON",  "ontario film television",     "on_ofttc"),
    ("CA-ON",  "ontario production services", "on_opstc"),
    ("CA-ON",  "nohfc",                       "nohfc_production_fund"),
    ("CA-ON",  "northern ontario heritage",   "nohfc_production_fund"),
    ("AU",     "screen australia",            "au_screen_production"),
    ("AU",     "location offset",             "au_location_offset"),
    ("AU",     "producer offset",             "au_producer_offset"),
    ("EU",     "eurimages",                   "eu_eurimages"),
    ("EU",     "creative europe media",       "eu_media_fund"),
    ("NORDIC", "nordisk film",                "nordic_ftvf"),
    ("NL",     "hubert bals",                 "nl_hbf"),
    ("DE-BY",  "filmfernsehfonds",            "de_fff_bayern"),
    ("DE-BY",  "fff bayern",                  "de_fff_bayern"),
    ("DE-NW",  "medienstiftung nrw",          "de_nrw_filmstiftung"),
    ("SE-VG",  "film i väst",                 "film_i_vast"),
    ("SE-VG",  "film i vast",                 "film_i_vast"),
    ("IBERO",  "ibermedia",                   "ibermedia_programme"),
    # Wave-6 — Canadian provinces
    ("CA-BC",  "production services tax credit", "ca_bc_pstc"),
    ("CA-BC",  "bc production services",         "ca_bc_pstc"),
    ("CA-ON",  "opstc",                          "ca_on_opstc"),
    ("CA-QC",  "québec production tax",          "ca_qc_qprdp"),
    ("CA-QC",  "quebec production tax",          "ca_qc_qprdp"),
    ("CA-QC",  "qprdp",                          "ca_qc_qprdp"),
    # Wave-6 — Australian states
    ("AU-WA",  "screenwest",                     "au_screenwest"),
    # Wave-6 — US California
    ("US-CA",  "california film",                "us_ca_ftc"),
    # Existing programs: add slug rules for cleaner pair matching
    ("IT",     "italian tax credit for foreign", "it_tax_credit_foreign"),
    ("HR",     "croatia film cash rebate",       "hr_cash_rebate"),
    ("BG",     "bulgarian film industry",        "bg_cash_rebate"),
    ("MT",     "malta film commission",          "mt_mfc_rebate"),  # already in list; harmless duplicate
    # Grants Wave-3 — new grant programs
    ("CA",     "bell fund",                      "ca_bell_fund"),
    ("CA",     "national screen institute",      "ca_nsi_fund"),
    ("CA",     "nsi",                            "ca_nsi_fund"),
    ("DE",     "berlinale world cinema fund",    "de_berlinale_wcf"),
    ("AU",     "miff premiere fund",             "au_miff_premiere"),
    ("SE",     "göteborg film festival",         "se_goteborg_fund"),
    ("NO",     "norwegian film institute",       "no_nfi_grants"),
    ("FI",     "finnish film foundation",        "fi_ses_grants"),
    ("GB",     "creative england",               "gb_creative_england"),
    ("ZA",     "industrial development corporation", "za_idc_film"),
]


def infer_slug(entry: GlobalProgramEntry) -> str | None:
    """Infer the DB slug for a GlobalProgramEntry via name fragment matching."""
    name_lower = entry.program_name.lower()
    for jur, fragment, slug in _NAME_SLUG_RULES:
        if entry.jurisdiction_code == jur and fragment in name_lower:
            return slug
    return None


# ---------------------------------------------------------------------------
# Named slug-pair stacking rules (from DB migrations 0007, 0022, 0044)
# Key: frozenset({slug_a, slug_b})
# ---------------------------------------------------------------------------

_SLUG_PAIR_RULES: dict[frozenset, dict] = {
    # Migration 0007 — NOHFC spend reductions
    frozenset({"nohfc_production_fund", "on_ofttc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "NOHFC grant reduces OFTTC qualifying labour expenditure basis "
            "(OMDC guidelines)."
        ),
    },
    frozenset({"nohfc_production_fund", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "NOHFC grant is government assistance under ITA §125.4; "
            "reduces CPTC qualified labour expenditure (T4283)."
        ),
    },
    # Migration 0044 — Fund/credit interactions
    frozenset({"fr_cnc_production", "fr_trip"}): {
        "rule_type": "allowed",
        "condition_text": (
            "CNC avance and TRIP operate on separate eligibility tracks. "
            "Co-productions may access both under treaty arrangements."
        ),
    },
    frozenset({"gb_bfi_production", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BFI equity investment does not reduce UK qualifying expenditure "
            "for AVEC purposes (co-financing, not government assistance)."
        ),
    },
    frozenset({"eu_eurimages", "uk_avec"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to UK co-producers does not reduce "
            "UK qualifying expenditure for AVEC."
        ),
    },
    frozenset({"eu_eurimages", "ie_section_481"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Irish co-producers does not reduce "
            "Irish qualifying expenditure for Section 481."
        ),
    },
    frozenset({"au_screen_production", "au_location_offset"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screen Australia equity is government financial assistance; "
            "reduces qualifying Australian production expenditure (QAPE) "
            "for Location Offset (ITAA97 §376-170)."
        ),
    },
    frozenset({"au_screen_production", "au_producer_offset"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screen Australia equity is government financial assistance; "
            "reduces QAPE for Producer Offset."
        ),
    },
    frozenset({"ca_cmf", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under ITA §125.4; "
            "reduce qualified labour expenditure before computing CPTC (T4283)."
        ),
    },
    frozenset({"ca_telefilm_dev", "ca_federal_cptc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Telefilm equity constitutes government assistance under ITA §125.4; "
            "reduces CPTC qualified labour expenditure (T4283)."
        ),
    },
    # Wave-6 — Canadian provincial credits stack additively with CPTC
    frozenset({"ca_bc_pstc", "ca_federal_cptc"}): {
        "rule_type": "allowed",
        "condition_text": (
            "BC PSTC and CPTC are both tax credits applied independently to qualifying labour. "
            "They are additive; PSTC does not reduce CPTC qualified labour (ITA §125.4 applies only to grants/assistance)."
        ),
    },
    frozenset({"ca_on_opstc", "ca_federal_cptc"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Ontario OPSTC and CPTC are additive tax credits on qualifying labour. "
            "No spend-reduction interaction; OPSTC is a tax credit, not government assistance under ITA §125.4."
        ),
    },
    frozenset({"ca_qc_qprdp", "ca_federal_cptc"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Quebec QPRDP and federal CPTC are additive. "
            "QPRDP is a provincial tax credit, not a grant; does not reduce CPTC qualified labour basis."
        ),
    },
    # Government assistance (CMF) reduces provincial tax credit qualifying basis too
    frozenset({"ca_cmf", "ca_bc_pstc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under provincial income tax acts; "
            "reduce qualifying BC labour expenditure for PSTC computation."
        ),
    },
    frozenset({"ca_cmf", "ca_on_opstc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under Ontario CTA; "
            "reduce qualifying Ontario labour expenditure for OPSTC computation."
        ),
    },
    frozenset({"nohfc_production_fund", "ca_on_opstc"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "NOHFC is government assistance under Ontario CTA; "
            "reduces qualifying Ontario labour expenditure for OPSTC (OMDC guidelines)."
        ),
    },
    # Eurimages stacks with additional national incentives
    frozenset({"eu_eurimages", "it_tax_credit_foreign"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Italian co-producers does not reduce "
            "Italian qualifying expenditure for the MiC tax credit for foreign productions."
        ),
    },
    frozenset({"eu_eurimages", "mt_mfc_rebate"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Maltese co-producers does not reduce "
            "qualifying expenditure for Malta Film Commission rebate."
        ),
    },
    frozenset({"eu_eurimages", "hr_cash_rebate"}): {
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Croatian co-producers does not reduce "
            "qualifying expenditure for HAVC Croatia cash rebate."
        ),
    },
    # Screenwest (WA) is government assistance → reduces Australian offset QAPE
    frozenset({"au_screenwest", "au_location_offset"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screenwest WA financial assistance is government financial assistance; "
            "reduces qualifying Australian production expenditure (QAPE) for the Location Offset."
        ),
    },
    frozenset({"au_screenwest", "au_screen_production"}): {
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screenwest WA financial assistance reduces qualifying Australian production expenditure "
            "for Screen Australia grant eligibility and matching calculations."
        ),
    },
}


# ---------------------------------------------------------------------------
# Structural rules — applied when no slug-pair rule matches
# ---------------------------------------------------------------------------

# jurisdiction_codes whose grants are "government assistance" → spend_reduction
# when stacked with that jurisdiction's primary incentive
_GOV_ASSISTANCE_JURISDICTIONS: dict[str, str] = {
    # (grant_jur): credit_jur
    "CA": "CA",          # CMF, Telefilm → CPTC
    "CA-ON": "CA",       # NOHFC → CPTC
    "CA-ON_CA-ON": "CA-ON",  # NOHFC → OFTTC
    "AU": "AU",          # Screen Australia → Offsets
}

# program_types that are "primary incentives" (tax credit / rebate)
_PRIMARY_TYPES = frozenset({"tax_credit", "cash_rebate"})

# program_types that are "grant/fund" programs
_GRANT_TYPES = frozenset({
    "direct_grant", "co_production_fund", "development_fund", "discretionary_fund",
})

# program_types that are "regional funds"
_REGIONAL_TYPES = frozenset({"regional_fund", "discretionary_fund"})


def _is_government_assistance_in_jurisdiction(
    grant: GlobalProgramEntry,
    credit: GlobalProgramEntry,
) -> bool:
    """
    True if `grant` is government assistance that reduces `credit`'s qualifying spend.
    Based on the structural rule that government grants from the same
    jurisdiction reduce the qualifying spend basis for national tax credits.
    """
    # Explicit slug-pair rules take precedence (checked before calling this)
    # Structural check: same top-level jurisdiction, grant is a fund type
    grant_jur = grant.jurisdiction_code.split("-")[0]
    credit_jur = credit.jurisdiction_code.split("-")[0]
    if grant_jur != credit_jur:
        return False
    if grant.program_type not in _GRANT_TYPES:
        return False
    if credit.program_type not in _PRIMARY_TYPES:
        return False
    # Only apply for known government assistance jurisdictions
    return grant_jur in ("CA", "AU")


def evaluate_pair(
    prog_a: GlobalProgramEntry,
    prog_b: GlobalProgramEntry,
) -> StackingViolation | None:
    """
    Evaluate stacking compatibility of two programs.
    Returns a StackingViolation if non-trivially interesting, else None (allowed by default).
    """
    slug_a = infer_slug(prog_a)
    slug_b = infer_slug(prog_b)

    # 1. Named slug-pair rules
    if slug_a and slug_b:
        rule = _SLUG_PAIR_RULES.get(frozenset({slug_a, slug_b}))
        if rule:
            rt = rule["rule_type"]
            if rt == "allowed":
                return None  # no violation
            return StackingViolation(
                program_a_name=prog_a.program_name,
                program_b_name=prog_b.program_name,
                rule_type=rt,
                condition_text=rule["condition_text"],
                adjusts_value=(rt == "spend_reduction"),
            )

    # 2. Mutual exclusivity: same jurisdiction + same primary type
    if (
        prog_a.jurisdiction_code == prog_b.jurisdiction_code
        and prog_a.program_type in _PRIMARY_TYPES
        and prog_b.program_type in _PRIMARY_TYPES
    ):
        return StackingViolation(
            program_a_name=prog_a.program_name,
            program_b_name=prog_b.program_name,
            rule_type="mutually_exclusive",
            condition_text=(
                f"Only one primary incentive can be claimed per jurisdiction "
                f"({prog_a.jurisdiction_code}). Higher-value program is retained."
            ),
            adjusts_value=True,
        )

    # 3. Government assistance → spend_reduction
    # Check both directions (grant reduces credit)
    for grant, credit in [(prog_a, prog_b), (prog_b, prog_a)]:
        if _is_government_assistance_in_jurisdiction(grant, credit):
            return StackingViolation(
                program_a_name=grant.program_name,
                program_b_name=credit.program_name,
                rule_type="spend_reduction",
                condition_text=(
                    f"{grant.program_name} is government assistance; reduces "
                    f"qualifying spend basis for {credit.program_name}."
                ),
                adjusts_value=True,
            )

    # 4. Default: allowed
    return None


def evaluate_structure_stacking(
    programs: list[GlobalProgramEntry],
) -> tuple[list[StackingViolation], list[StackingViolation], list[StackingViolation]]:
    """
    Evaluate all pairwise stacking interactions in a structure.

    Returns (prohibited_or_mutually_exclusive, conditionals, spend_reductions).
    """
    violations: list[StackingViolation] = []
    conditionals: list[StackingViolation] = []
    spend_reductions: list[StackingViolation] = []

    for i, prog_a in enumerate(programs):
        for prog_b in programs[i + 1:]:
            v = evaluate_pair(prog_a, prog_b)
            if v is None:
                continue
            if v.rule_type in ("prohibited", "mutually_exclusive"):
                violations.append(v)
            elif v.rule_type == "conditional":
                conditionals.append(v)
            elif v.rule_type == "spend_reduction":
                spend_reductions.append(v)

    return violations, conditionals, spend_reductions
