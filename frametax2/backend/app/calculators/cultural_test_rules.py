"""
cultural_test_rules.py

D2 Cultural Test Rules.
Implements scoring functions for CNC, Section 481, Eurimages, Ibermedia,
Canadian content, Australian content, UK BFI, and European Convention
tests. All tests reuse the deterministic engine from
evaluate_qualification_tests.py.
"""
from __future__ import annotations

from typing import Any

from app.calculators.evaluate_qualification_tests import (
    UK_BFI_RULES_HARDCODED,
    CriterionResult,
    QualificationTestResult,
    score_qualification_test,
    score_uk_bfi_cultural_test,
)

# ---------------------------------------------------------------------------
# 1. French CNC Qualification Test
# ---------------------------------------------------------------------------

FR_CNC_RULES: list[dict] = [
    {
        "criterion_code": "CNC_A1",
        "section": "A",
        "section_name": "French Language / Subject Matter",
        "description": "Original dialogue in French or French subject matter",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "french_language_or_subject",
        "threshold_value": None,
        "scoring_logic": "French language or subject = 1 pt (qualitative gate)",
    },
    {
        "criterion_code": "CNC_B1",
        "section": "B",
        "section_name": "Director",
        "description": "Director is French national or EEA citizen",
        "max_points": 2,
        "input_type": "boolean",
        "input_key": "director_french_or_eea",
        "threshold_value": None,
        "scoring_logic": "French/EEA director = 2 pts",
    },
    {
        "criterion_code": "CNC_C1",
        "section": "C",
        "section_name": "Writer",
        "description": "Writer is French national or EEA citizen",
        "max_points": 2,
        "input_type": "boolean",
        "input_key": "writer_french_or_eea",
        "threshold_value": None,
        "scoring_logic": "French/EEA writer = 2 pts",
    },
    {
        # Required gate — must be True; no score contribution but checked separately
        "criterion_code": "CNC_D1",
        "section": "D",
        "section_name": "Producer",
        "description": "Producer is a French national / French-registered entity (required)",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "producer_french",
        "threshold_value": None,
        "scoring_logic": "French producer = required gate (1 pt proxy)",
    },
    {
        # Required gate — must be >= 0.50
        "criterion_code": "CNC_E1",
        "section": "E",
        "section_name": "French Qualifying Expenditure",
        "description": "French qualifying expenditure >= 50% of total budget (required)",
        "max_points": 1,
        "input_type": "percentage",
        "input_key": "french_spend_pct",
        "threshold_value": 0.50,
        "scoring_logic": ">=50% French QE = required gate (1 pt proxy)",
    },
]

# Minimum: D (producer_french) + E (french_spend_pct) + at least one of B/C
# Encoded as: total >= 4 AND section D >= 1 AND section E >= 1
# The caller checks section_minimums for D and E; overall >= 4 forces B or C.
_FR_CNC_SECTION_MINIMUMS = {"D": 1, "E": 1}


def score_fr_cnc_cultural_test(production_details: dict[str, Any]) -> QualificationTestResult:
    """
    Score the French CNC cultural qualification test.
    Pass requires: French producer + >=50% French spend + (French/EEA director OR French/EEA writer).
    """
    return score_qualification_test(
        test_rules=FR_CNC_RULES,
        production_details=production_details,
        minimum_pass_points=4,
        section_minimums=_FR_CNC_SECTION_MINIMUMS,
        test_slug="fr_cnc_cultural_test",
        total_available_points=7,
    )


def get_fr_cnc_deficit(
    production_details: dict[str, Any],
    test_result: QualificationTestResult,
) -> list[str]:
    deficits: list[str] = []
    if not production_details.get("producer_french"):
        deficits.append("French producer (or French-registered entity) required but not confirmed.")
    if float(production_details.get("french_spend_pct", 0)) < 0.50:
        deficits.append("French qualifying expenditure must be >= 50% of total budget.")
    if not production_details.get("director_french_or_eea") and not production_details.get("writer_french_or_eea"):
        deficits.append("At least one of director or writer must be French or EEA national.")
    return deficits


# ---------------------------------------------------------------------------
# 2. Irish Section 481 Qualification Checklist
# ---------------------------------------------------------------------------

IE_SECTION_481_RULES: list[dict] = [
    {
        "criterion_code": "IE_A1",
        "section": "A",
        "section_name": "Company Qualification",
        "description": "Production company Irish-resident or EEA qualifying entity",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "irish_or_eea_company",
        "threshold_value": None,
        "scoring_logic": "Irish-resident or EEA entity = required (1 pt proxy)",
    },
    {
        "criterion_code": "IE_B1",
        "section": "B",
        "section_name": "Minimum Irish Qualifying Expenditure",
        "description": "Qualifying Irish expenditure >= EUR 125,000",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "irish_qe_above_125k",
        "threshold_value": None,
        "scoring_logic": "Irish QE >= €125k = required (1 pt proxy)",
    },
    {
        "criterion_code": "IE_C1",
        "section": "C",
        "section_name": "Minimum Irish QE Percentage",
        "description": "Irish qualifying expenditure >= 10% of total budget",
        "max_points": 1,
        "input_type": "percentage",
        "input_key": "irish_qe_pct",
        "threshold_value": 0.10,
        "scoring_logic": ">=10% Irish QE = 1 pt",
    },
    {
        "criterion_code": "IE_D1",
        "section": "D",
        "section_name": "Qualifying Production Type",
        "description": "Production is a qualifying film, TV drama, animation, or creative documentary",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "qualifying_production_type",
        "threshold_value": None,
        "scoring_logic": "Qualifying production type = required (1 pt proxy)",
    },
    {
        "criterion_code": "IE_E1",
        "section": "E",
        "section_name": "Individual Cap Compliance",
        "description": "No individual's Section 481 relief exceeds the statutory cap",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "within_individual_cap",
        "threshold_value": None,
        "scoring_logic": "Within individual cap = 1 pt",
    },
]

# Minimum pass: A + B + D all True = 3 pts
_IE_481_SECTION_MINIMUMS = {"A": 1, "B": 1, "D": 1}


def score_ie_section_481_test(production_details: dict[str, Any]) -> QualificationTestResult:
    """
    Score Irish Section 481 qualification checklist.
    Hard gates: Irish/EEA company + QE >= €125k + qualifying production type.
    """
    return score_qualification_test(
        test_rules=IE_SECTION_481_RULES,
        production_details=production_details,
        minimum_pass_points=3,
        section_minimums=_IE_481_SECTION_MINIMUMS,
        test_slug="ie_section_481_test",
        total_available_points=5,
    )


def get_ie_section_481_deficit(
    production_details: dict[str, Any],
    test_result: QualificationTestResult,
) -> list[str]:
    deficits: list[str] = []
    if not production_details.get("irish_or_eea_company"):
        deficits.append("Production company must be Irish-resident or EEA qualifying entity.")
    if not production_details.get("irish_qe_above_125k"):
        deficits.append("Qualifying Irish expenditure must be >= EUR 125,000.")
    if not production_details.get("qualifying_production_type"):
        deficits.append("Production must be a qualifying film, TV drama, animation, or creative documentary.")
    return deficits


# ---------------------------------------------------------------------------
# 3. Eurimages Co-production Test
# ---------------------------------------------------------------------------

EU_EURIMAGES_RULES: list[dict] = [
    {
        "criterion_code": "EUR_A1",
        "section": "A",
        "section_name": "Minimum Co-producers",
        "description": "At least 2 co-producer countries",
        "max_points": 1,
        "input_type": "count",
        "input_key": "coproducer_country_count",
        "threshold_value": 2,
        "scoring_logic": ">=2 co-producer countries = required (1 pt proxy)",
    },
    {
        "criterion_code": "EUR_B1",
        "section": "B",
        "section_name": "Member State Co-producers",
        "description": "All co-producers are from Eurimages member states",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "all_coproducers_member_states",
        "threshold_value": None,
        "scoring_logic": "All co-producers in member states = required (1 pt proxy)",
    },
    {
        # Percentage is the share of the DOMINANT country; must be < 0.80
        # Stored as inverted flag: True means no single country > 80%
        "criterion_code": "EUR_C1",
        "section": "C",
        "section_name": "Country Concentration Cap",
        "description": "No single country holds > 80% of co-production share",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "no_single_country_over_80pct",
        "threshold_value": None,
        "scoring_logic": "Max country share < 80% = required (1 pt proxy)",
    },
    {
        "criterion_code": "EUR_D1",
        "section": "D",
        "section_name": "Minimum Co-producer Share",
        "description": "Each co-producer holds minimum 10% of co-production",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "each_coproducer_min_10pct",
        "threshold_value": None,
        "scoring_logic": "Each co-producer >= 10% = required (1 pt proxy)",
    },
    {
        "criterion_code": "EUR_E1",
        "section": "E",
        "section_name": "Majority Producer",
        "description": "Majority co-producer is from the applicant/lead country",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "majority_producer_from_applicant_country",
        "threshold_value": None,
        "scoring_logic": "Majority producer from applicant country = 1 pt",
    },
]

_EU_EURIMAGES_SECTION_MINIMUMS = {"A": 1, "B": 1, "C": 1, "D": 1}


def score_eu_eurimages_test(production_details: dict[str, Any]) -> QualificationTestResult:
    """
    Score the Eurimages co-production eligibility test.
    Required: >=2 member-state co-producers, no single country >80%, each co-producer >=10%.
    """
    return score_qualification_test(
        test_rules=EU_EURIMAGES_RULES,
        production_details=production_details,
        minimum_pass_points=4,
        section_minimums=_EU_EURIMAGES_SECTION_MINIMUMS,
        test_slug="eu_eurimages_test",
        total_available_points=5,
    )


def get_eu_eurimages_deficit(
    production_details: dict[str, Any],
    test_result: QualificationTestResult,
) -> list[str]:
    deficits: list[str] = []
    if int(production_details.get("coproducer_country_count", 0)) < 2:
        deficits.append("At least 2 co-producer countries required.")
    if not production_details.get("all_coproducers_member_states"):
        deficits.append("All co-producers must be from Eurimages member states.")
    if not production_details.get("no_single_country_over_80pct"):
        deficits.append("No single country may hold more than 80% of the co-production share.")
    if not production_details.get("each_coproducer_min_10pct"):
        deficits.append("Each co-producer must hold at least 10% of the co-production.")
    return deficits


# ---------------------------------------------------------------------------
# 4. Ibermedia Co-production Test
# ---------------------------------------------------------------------------

IBERMEDIA_RULES: list[dict] = [
    {
        "criterion_code": "IBM_A1",
        "section": "A",
        "section_name": "Minimum Member Countries",
        "description": "At least 2 Ibero-American Ibermedia member countries",
        "max_points": 1,
        "input_type": "count",
        "input_key": "ibermedia_country_count",
        "threshold_value": 2,
        "scoring_logic": ">=2 Ibermedia member countries = required (1 pt proxy)",
    },
    {
        "criterion_code": "IBM_B1",
        "section": "B",
        "section_name": "Member State Co-producers",
        "description": "All co-producers are from Ibermedia member states",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "all_coproducers_ibermedia_members",
        "threshold_value": None,
        "scoring_logic": "All co-producers in Ibermedia member states = required",
    },
    {
        "criterion_code": "IBM_C1",
        "section": "C",
        "section_name": "Country Concentration Cap",
        "description": "No single country holds > 80% of co-production share",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "no_single_country_over_80pct",
        "threshold_value": None,
        "scoring_logic": "Max country share < 80% = required",
    },
    {
        "criterion_code": "IBM_D1",
        "section": "D",
        "section_name": "Minimum Co-producer Share",
        "description": "Each co-producer holds minimum 10% of co-production",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "each_coproducer_min_10pct",
        "threshold_value": None,
        "scoring_logic": "Each co-producer >= 10% = required",
    },
]

_IBERMEDIA_SECTION_MINIMUMS = {"A": 1, "B": 1, "C": 1, "D": 1}


def score_ibermedia_test(production_details: dict[str, Any]) -> QualificationTestResult:
    """
    Score the Ibermedia co-production eligibility test.
    Required: >=2 member countries, all co-producers from member states, no country >80%, each >=10%.
    """
    return score_qualification_test(
        test_rules=IBERMEDIA_RULES,
        production_details=production_details,
        minimum_pass_points=4,
        section_minimums=_IBERMEDIA_SECTION_MINIMUMS,
        test_slug="ibermedia_test",
        total_available_points=4,
    )


def get_ibermedia_deficit(
    production_details: dict[str, Any],
    test_result: QualificationTestResult,
) -> list[str]:
    deficits: list[str] = []
    if int(production_details.get("ibermedia_country_count", 0)) < 2:
        deficits.append("At least 2 Ibermedia member countries required.")
    if not production_details.get("all_coproducers_ibermedia_members"):
        deficits.append("All co-producers must be from Ibermedia member states.")
    if not production_details.get("no_single_country_over_80pct"):
        deficits.append("No single country may hold more than 80% of the co-production share.")
    if not production_details.get("each_coproducer_min_10pct"):
        deficits.append("Each co-producer must hold at least 10% of the co-production.")
    return deficits


# ---------------------------------------------------------------------------
# 5. Canadian Content Test (CRTC/Telefilm 10-point system)
# ---------------------------------------------------------------------------

CA_CONTENT_RULES: list[dict] = [
    {
        "criterion_code": "CA_A1",
        "section": "A",
        "section_name": "Director",
        "description": "Director is Canadian",
        "max_points": 2,
        "input_type": "boolean",
        "input_key": "director_canadian",
        "threshold_value": None,
        "scoring_logic": "Canadian director = 2 pts",
    },
    {
        "criterion_code": "CA_B1",
        "section": "B",
        "section_name": "Screenwriter",
        "description": "Screenwriter is Canadian",
        "max_points": 2,
        "input_type": "boolean",
        "input_key": "writer_canadian",
        "threshold_value": None,
        "scoring_logic": "Canadian writer = 2 pts",
    },
    {
        "criterion_code": "CA_C1",
        "section": "C",
        "section_name": "Lead Performer",
        "description": "Lead performer is Canadian",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "lead_performer_canadian",
        "threshold_value": None,
        "scoring_logic": "Canadian lead performer = 1 pt",
    },
    {
        "criterion_code": "CA_D1",
        "section": "D",
        "section_name": "Second Lead Performer",
        "description": "Second lead performer is Canadian",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "second_lead_canadian",
        "threshold_value": None,
        "scoring_logic": "Canadian second lead = 1 pt",
    },
    {
        "criterion_code": "CA_E1",
        "section": "E",
        "section_name": "Director of Photography",
        "description": "Director of Photography is Canadian",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "dop_canadian",
        "threshold_value": None,
        "scoring_logic": "Canadian DoP = 1 pt",
    },
    {
        "criterion_code": "CA_F1",
        "section": "F",
        "section_name": "Art Director",
        "description": "Art Director is Canadian",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "art_director_canadian",
        "threshold_value": None,
        "scoring_logic": "Canadian Art Director = 1 pt",
    },
    {
        "criterion_code": "CA_G1",
        "section": "G",
        "section_name": "Music Composer",
        "description": "Music Director or Composer is Canadian",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "composer_canadian",
        "threshold_value": None,
        "scoring_logic": "Canadian composer = 1 pt",
    },
    {
        "criterion_code": "CA_H1",
        "section": "H",
        "section_name": "Picture Editor",
        "description": "Picture Editor is Canadian",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "editor_canadian",
        "threshold_value": None,
        "scoring_logic": "Canadian editor = 1 pt",
    },
]

# Minimum 6/10; additionally director (A) OR writer (B) must score
# Enforced via: overall >= 6, and section_minimums check A+B >= 2
# (A+B >= 2 ensures at least one of the two key roles is Canadian)
_CA_CONTENT_SECTION_MINIMUMS = {"A+B": 2}


def score_ca_content_test(production_details: dict[str, Any]) -> QualificationTestResult:
    """
    Score the Canadian content point test (CRTC/Telefilm 10-point system).
    Minimum 6/10 points. Director (2pts) or Writer (2pts) must score — cannot skip both.
    """
    return score_qualification_test(
        test_rules=CA_CONTENT_RULES,
        production_details=production_details,
        minimum_pass_points=6,
        section_minimums=_CA_CONTENT_SECTION_MINIMUMS,
        test_slug="ca_content_test",
        total_available_points=10,
    )


def get_ca_content_deficit(
    production_details: dict[str, Any],
    test_result: QualificationTestResult,
) -> list[str]:
    deficits: list[str] = []
    if test_result.total_score < 6:
        gap = 6 - test_result.total_score
        deficits.append(f"Canadian content score {test_result.total_score}/10; need {gap} more point(s) to reach minimum 6.")
    if not production_details.get("director_canadian") and not production_details.get("writer_canadian"):
        deficits.append("At least the director or the screenwriter must be Canadian (2-pt key role requirement).")
    return deficits


# ---------------------------------------------------------------------------
# 6. Australian Content Test (Producer Offset)
# ---------------------------------------------------------------------------

AU_CONTENT_RULES: list[dict] = [
    {
        "criterion_code": "AU_A1",
        "section": "A",
        "section_name": "Script / Underlying Rights",
        "description": "Australian script or Australian underlying rights",
        "max_points": 3,
        "input_type": "boolean",
        "input_key": "australian_script_or_rights",
        "threshold_value": None,
        "scoring_logic": "Australian script/rights = 3 pts",
    },
    {
        "criterion_code": "AU_B1",
        "section": "B",
        "section_name": "Director",
        "description": "Director is Australian",
        "max_points": 3,
        "input_type": "boolean",
        "input_key": "director_australian",
        "threshold_value": None,
        "scoring_logic": "Australian director = 3 pts",
    },
    {
        "criterion_code": "AU_C1",
        "section": "C",
        "section_name": "Producer",
        "description": "Producer is Australian",
        "max_points": 3,
        "input_type": "boolean",
        "input_key": "producer_australian",
        "threshold_value": None,
        "scoring_logic": "Australian producer = 3 pts",
    },
    {
        "criterion_code": "AU_D1",
        "section": "D",
        "section_name": "Lead Actor",
        "description": "Lead actor is Australian",
        "max_points": 2,
        "input_type": "boolean",
        "input_key": "lead_actor_australian",
        "threshold_value": None,
        "scoring_logic": "Australian lead actor = 2 pts",
    },
    {
        "criterion_code": "AU_E1",
        "section": "E",
        "section_name": "Supporting Cast",
        "description": "50% or more of supporting cast are Australian",
        "max_points": 2,
        "input_type": "percentage",
        "input_key": "supporting_cast_australian_pct",
        "threshold_value": 0.50,
        "scoring_logic": ">=50% Australian supporting cast = 2 pts",
    },
    {
        "criterion_code": "AU_F1",
        "section": "F",
        "section_name": "Music",
        "description": "Music is Australian (composer or production)",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "australian_music",
        "threshold_value": None,
        "scoring_logic": "Australian music = 1 pt",
    },
    {
        "criterion_code": "AU_G1",
        "section": "G",
        "section_name": "Post-Production",
        "description": "Post-production performed in Australia",
        "max_points": 2,
        "input_type": "boolean",
        "input_key": "post_production_in_australia",
        "threshold_value": None,
        "scoring_logic": "Australian post-production = 2 pts",
    },
]


def score_au_content_test(production_details: dict[str, Any]) -> QualificationTestResult:
    """
    Score the Australian content test (Producer Offset).
    Minimum 8 out of 16 points (50%).
    """
    return score_qualification_test(
        test_rules=AU_CONTENT_RULES,
        production_details=production_details,
        minimum_pass_points=8,
        section_minimums=None,
        test_slug="au_content_test",
        total_available_points=16,
    )


def get_au_content_deficit(
    production_details: dict[str, Any],
    test_result: QualificationTestResult,
) -> list[str]:
    deficits: list[str] = []
    if test_result.total_score < 8:
        gap = 8 - test_result.total_score
        deficits.append(
            f"Australian content score {test_result.total_score}/16; need {gap} more point(s) to reach minimum 8."
        )
        # Identify highest-value unscored criteria
        unscored = [
            f"{r.description} (+{r.max_points} pts)"
            for r in test_result.criterion_results
            if r.awarded_points == 0
        ]
        if unscored:
            deficits.append("Unscored criteria: " + "; ".join(unscored))
    return deficits


# ---------------------------------------------------------------------------
# 7. European Convention on Cinematographic Co-production Test
# ---------------------------------------------------------------------------

EU_EUROPEAN_CONVENTION_RULES: list[dict] = [
    {
        "criterion_code": "ECC_A1",
        "section": "A",
        "section_name": "Minimum Signatory Countries",
        "description": "At least 2 Council of Europe signatory countries as co-producers",
        "max_points": 1,
        "input_type": "count",
        "input_key": "signatory_country_count",
        "threshold_value": 2,
        "scoring_logic": ">=2 signatory countries = required (1 pt proxy)",
    },
    {
        "criterion_code": "ECC_B1",
        "section": "B",
        "section_name": "Majority Co-producer Share",
        "description": "Majority co-producer holds at least 50% of co-production",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "majority_coproducer_min_50pct",
        "threshold_value": None,
        "scoring_logic": "Majority co-producer >= 50% = required (Article 9)",
    },
    {
        "criterion_code": "ECC_C1",
        "section": "C",
        "section_name": "Minimum Co-producer Share",
        "description": "Each co-producer holds at least 10% of co-production",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "each_coproducer_min_10pct",
        "threshold_value": None,
        "scoring_logic": "Each co-producer >= 10% = required (Article 9)",
    },
    {
        "criterion_code": "ECC_D1",
        "section": "D",
        "section_name": "Creative Elements",
        "description": "Director or writer is from a signatory state",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "director_or_writer_from_signatory_state",
        "threshold_value": None,
        "scoring_logic": "Director or writer from signatory state = required (Article 9)",
    },
    {
        "criterion_code": "ECC_E1",
        "section": "E",
        "section_name": "Country Concentration Cap",
        "description": "No single country holds more than 80% of the co-production",
        "max_points": 1,
        "input_type": "boolean",
        "input_key": "no_single_country_over_80pct",
        "threshold_value": None,
        "scoring_logic": "Max country share < 80% = required (Article 9)",
    },
]

_ECC_SECTION_MINIMUMS = {"A": 1, "B": 1, "C": 1, "D": 1, "E": 1}


def score_eu_european_convention_test(production_details: dict[str, Any]) -> QualificationTestResult:
    """
    Score the European Convention on Cinematographic Co-production eligibility test (Article 9).
    All five criteria are required gates.
    """
    return score_qualification_test(
        test_rules=EU_EUROPEAN_CONVENTION_RULES,
        production_details=production_details,
        minimum_pass_points=5,
        section_minimums=_ECC_SECTION_MINIMUMS,
        test_slug="eu_european_convention_test",
        total_available_points=5,
    )


def get_eu_european_convention_deficit(
    production_details: dict[str, Any],
    test_result: QualificationTestResult,
) -> list[str]:
    deficits: list[str] = []
    if int(production_details.get("signatory_country_count", 0)) < 2:
        deficits.append("At least 2 Council of Europe signatory countries must be co-producers.")
    if not production_details.get("majority_coproducer_min_50pct"):
        deficits.append("Majority co-producer must hold at least 50% of the co-production.")
    if not production_details.get("each_coproducer_min_10pct"):
        deficits.append("Each co-producer must hold at least 10% of the co-production.")
    if not production_details.get("director_or_writer_from_signatory_state"):
        deficits.append("Director or writer must be from a Council of Europe signatory state.")
    if not production_details.get("no_single_country_over_80pct"):
        deficits.append("No single country may hold more than 80% of the co-production share.")
    return deficits


# ---------------------------------------------------------------------------
# 8. UK BFI Cultural Test
#
# Reuses evaluate_qualification_tests.score_uk_bfi_cultural_test / its
# UK_BFI_RULES_HARDCODED rule table verbatim — this module never
# reimplements that scoring. Section D (Cultural Practitioners) gives
# writer/director/producer/composer/lead-actor/second-lead each an equal
# 1/31 point weight (D1-D6) — the weight is whatever the test's own rule
# table already assigns per role, never a universal hardcoded preference
# for one role.
# ---------------------------------------------------------------------------

UK_BFI_RULES: list[dict] = UK_BFI_RULES_HARDCODED


def score_uk_bfi_test(production_details: dict[str, Any]) -> QualificationTestResult:
    return score_uk_bfi_cultural_test(production_details)


def get_uk_bfi_deficit(
    production_details: dict[str, Any],
    test_result: QualificationTestResult,
) -> list[str]:
    deficits: list[str] = []
    if test_result.total_score < test_result.minimum_required:
        gap = test_result.minimum_required - test_result.total_score
        deficits.append(
            f"UK BFI cultural test score {test_result.total_score}/{test_result.total_available}; "
            f"need {gap} more point(s) to reach minimum {test_result.minimum_required}."
        )
        unscored = [
            f"{r.description} (+{r.max_points} pts)"
            for r in test_result.criterion_results
            if r.awarded_points == 0
        ]
        if unscored:
            deficits.append("Unscored criteria: " + "; ".join(unscored))
    return deficits


# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__ = [
    # Rule lists
    "FR_CNC_RULES",
    "IE_SECTION_481_RULES",
    "EU_EURIMAGES_RULES",
    "IBERMEDIA_RULES",
    "CA_CONTENT_RULES",
    "AU_CONTENT_RULES",
    "EU_EUROPEAN_CONVENTION_RULES",
    "UK_BFI_RULES",
    # Scoring functions
    "score_fr_cnc_cultural_test",
    "score_ie_section_481_test",
    "score_eu_eurimages_test",
    "score_ibermedia_test",
    "score_ca_content_test",
    "score_au_content_test",
    "score_eu_european_convention_test",
    "score_uk_bfi_test",
    # Deficit helpers
    "get_fr_cnc_deficit",
    "get_ie_section_481_deficit",
    "get_eu_eurimages_deficit",
    "get_ibermedia_deficit",
    "get_ca_content_deficit",
    "get_au_content_deficit",
    "get_eu_european_convention_deficit",
    "get_uk_bfi_deficit",
]
