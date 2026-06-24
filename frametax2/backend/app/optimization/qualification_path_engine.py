"""
qualification_path_engine.py — Phase D3: Qualification deficit and path analysis.

Given a production profile and a target program/test, returns:
  - current qualification score
  - deficits (what's missing)
  - surplus (what exceeds requirements)
  - lowest-friction paths to qualification

No DB access. Pure Python. No optimization scoring.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Production profile schema
# ---------------------------------------------------------------------------

# All keys are optional — engine uses None-safe checks throughout.
# Boolean keys: True = criterion met, False = explicitly not met, None = unknown
PRODUCTION_PROFILE_SCHEMA: dict[str, str] = {
    # Crew nationality (boolean per role for UK/CA/AU etc.)
    "director_uk": "bool", "director_ca": "bool", "director_au": "bool",
    "director_fr": "bool", "director_ie": "bool", "director_de": "bool",
    "director_eea": "bool", "director_treaty": "bool",
    "writer_uk": "bool", "writer_ca": "bool", "writer_au": "bool",
    "writer_fr": "bool", "writer_ie": "bool", "writer_de": "bool",
    "writer_eea": "bool", "writer_treaty": "bool",
    "producer_uk": "bool", "producer_ca": "bool", "producer_au": "bool",
    "producer_fr": "bool", "producer_ie": "bool",
    "lead_cast_uk": "bool", "lead_cast_ca": "bool", "lead_cast_au": "bool",
    "second_lead_uk": "bool", "second_lead_ca": "bool",
    "composer_uk": "bool", "composer_ca": "bool",
    "dop_ca": "bool", "editor_ca": "bool",
    "art_director_ca": "bool",
    # Spend percentages (float 0.0–1.0)
    "uk_shoot_pct": "float", "ca_spend_pct": "float", "au_spend_pct": "float",
    "fr_spend_pct": "float", "ie_spend_pct": "float", "de_spend_pct": "float",
    "it_spend_pct": "float",
    # British crew percentage
    "british_cast_days_pct": "float", "british_crew_days_pct": "float",
    "ca_cast_days_pct": "float", "au_cast_days_pct": "float",
    # Content flags
    "uk_setting": "bool", "lead_characters_british": "bool",
    "british_subject_matter": "bool", "english_language_variant": "bool",
    "british_cultural_contribution": "bool",
    "uk_vfx": "bool", "ca_vfx": "bool",
    # Entity flags
    "has_irish_entity": "bool", "has_canadian_entity": "bool",
    "has_uk_entity": "bool", "has_french_entity": "bool",
    "has_australian_entity": "bool",
    # Co-production structure
    "is_coproduction": "bool",
    "coproduction_country_count": "int",
    "majority_pct": "float",
    "minority_pct": "float",
    "all_coproducers_eurimages_members": "bool",
    "all_coproducers_ibermedia_members": "bool",
    "all_coproducers_european_convention_signatories": "bool",
    # Qualifying expenditure
    "total_qualifying_spend_usd": "float",
    "irish_qualifying_spend_usd": "float",
    # Production type
    "production_type": "str",   # feature | tv_series | documentary | animation
    # Post-production
    "post_production_uk": "bool", "post_production_ca": "bool",
    "post_production_au": "bool", "post_production_fr": "bool",
    # VFX jurisdiction
    "vfx_uk": "bool", "vfx_ca": "bool", "vfx_au": "bool",
    # Australian content
    "australian_underlying_rights": "bool",
}


# ---------------------------------------------------------------------------
# Qualification path types
# ---------------------------------------------------------------------------

@dataclass
class QualificationDeficit:
    criterion_code: str
    description: str
    current_value: Any
    required_value: Any
    friction_score: float  # 1.0 = easy fix, 10.0 = very hard
    recommendation: str


@dataclass
class QualificationSurplus:
    criterion_code: str
    description: str
    current_value: Any
    required_value: Any
    surplus_amount: Any


@dataclass
class QualificationPath:
    path_id: str
    description: str
    friction_score: float    # lower = easier
    actions: list[str]       # ordered list of concrete actions
    estimated_impact: str    # qualitative description
    unlocks_programs: list[str]  # program slugs this path would unlock
    notes: str | None = None


@dataclass
class QualificationAnalysis:
    program_slug: str
    test_slug: str
    production_profile: dict[str, Any]

    is_currently_qualifying: bool
    current_score: int | None
    required_score: int | None
    score_gap: int | None

    deficits: list[QualificationDeficit]
    surpluses: list[QualificationSurplus]
    paths: list[QualificationPath]   # sorted by friction_score ascending

    disqualifying_factors: list[str]
    unknown_factors: list[str]

    engine_version: str = "0.1.0"


# ---------------------------------------------------------------------------
# Internal criterion evaluators
# ---------------------------------------------------------------------------

def _pct(val: Any) -> float:
    """Safely coerce to float pct."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _bool(val: Any) -> bool:
    return bool(val) if val is not None else False


def _int(val: Any) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Per-test deficit analysis functions
# ---------------------------------------------------------------------------

def _analyse_bfi(p: dict) -> tuple[list[QualificationDeficit], list[QualificationSurplus], list[str]]:
    deficits: list[QualificationDeficit] = []
    surpluses: list[QualificationSurplus] = []
    unknowns: list[str] = []

    # Quick score from evaluate_qualification_tests
    try:
        from app.calculators.evaluate_qualification_tests import (
            score_uk_bfi_cultural_test, UK_BFI_RULES_HARDCODED,
        )
        result = score_uk_bfi_cultural_test(p)
        if result.passes_overall:
            return [], [], []

        for cr in result.criterion_results:
            if not cr.passed and cr.input_value is None:
                unknowns.append(cr.input_key)
            elif not cr.passed:
                deficit = QualificationDeficit(
                    criterion_code=cr.criterion_code,
                    description=cr.description,
                    current_value=cr.input_value,
                    required_value=cr.max_points,
                    friction_score=_bfi_friction(cr.criterion_code),
                    recommendation=_bfi_recommendation(cr.criterion_code),
                )
                deficits.append(deficit)
            elif cr.awarded_points >= cr.max_points:
                surpluses.append(QualificationSurplus(
                    criterion_code=cr.criterion_code,
                    description=cr.description,
                    current_value=cr.input_value,
                    required_value=cr.max_points,
                    surplus_amount=0,
                ))
    except ImportError:
        unknowns.append("bfi_test_module_unavailable")

    return deficits, surpluses, unknowns


def _bfi_friction(code: str) -> float:
    # Lower = easier to fix
    frictions = {
        "D1": 3.0,  # Director British — replace or contract is hard
        "D2": 3.0,  # Writer British
        "D3": 3.0,  # Producer British
        "D4": 2.0,  # Composer British — relatively easy to change
        "D5": 4.0,  # Lead actor British
        "D6": 3.0,  # Second lead British
        "D7": 4.0,  # 50% British cast days
        "D8": 3.0,  # 50% British crew days
        "C1": 5.0,  # 50% UK shoot — structural
        "C2": 1.5,  # UK VFX — move VFX work to UK
        "A1": 7.0,  # Set in UK — story change
        "A2": 7.0,  # Lead characters British — story change
        "A3": 7.0,  # British subject matter — story change
        "A4": 2.0,  # English language — usually easy
        "B1": 6.0,  # British cultural contribution
    }
    return frictions.get(code, 5.0)


def _bfi_recommendation(code: str) -> str:
    recs = {
        "D1": "Engage a British or UK-resident director, or restructure to ensure director qualifies.",
        "D2": "Engage a British or UK-resident screenwriter.",
        "D3": "Engage a British or UK-resident producer.",
        "D4": "Commission the score from a British or UK-resident composer (lowest friction change).",
        "D5": "Cast a British national or UK-resident in the lead role.",
        "D6": "Cast a British national or UK-resident in the second lead role.",
        "D7": "Increase UK-cast days to ≥50% of total cast days through UK casting.",
        "D8": "Move department heads or increase UK crew engagement to reach ≥50% crew days.",
        "C1": "Relocate principal photography to UK to reach ≥50% UK shoot days.",
        "C2": "Move VFX and/or post-production work to a qualifying UK VFX facility.",
        "A1": "Relocate or adapt the story setting to the United Kingdom.",
        "A2": "Make lead characters British citizens or UK residents.",
        "A3": "Base the film on British underlying material, history, or subject matter.",
        "A4": "Ensure original dialogue is recorded mainly in English (or Welsh/Scottish Gaelic/Irish).",
        "B1": "Strengthen British cultural contribution, heritage, or diversity elements in the script.",
    }
    return recs.get(code, "Review this criterion against current production parameters.")


def _analyse_canadian_content(p: dict) -> tuple[list[QualificationDeficit], list[QualificationSurplus], list[str]]:
    deficits = []
    surpluses = []
    unknowns = []
    score = 0
    max_pts = 10

    criteria = [
        ("CA_D1", "director_ca", 2, "Director Canadian",
         "Engage a Canadian director (2 pts). Required — director OR writer must score.", 2.5),
        ("CA_D2", "writer_ca", 2, "Screenwriter Canadian",
         "Engage a Canadian screenwriter (2 pts). Required — writer OR director must score.", 2.5),
        ("CA_D3", "lead_cast_ca", 1, "Lead performer Canadian",
         "Cast a Canadian national in the lead role (1 pt).", 3.5),
        ("CA_D4", "second_lead_ca", 1, "Second lead Canadian",
         "Cast a Canadian in the second lead role (1 pt).", 3.0),
        ("CA_D5", "dop_ca", 1, "Director of Photography Canadian",
         "Engage a Canadian Director of Photography (1 pt).", 2.5),
        ("CA_D6", "art_director_ca", 1, "Art Director Canadian",
         "Engage a Canadian Art Director (1 pt).", 2.0),
        ("CA_D7", "composer_ca", 1, "Music Director/Composer Canadian",
         "Commission score from a Canadian composer (1 pt).", 1.5),
        ("CA_D8", "editor_ca", 1, "Picture Editor Canadian",
         "Engage a Canadian picture editor (1 pt).", 2.0),
    ]

    director_score = 0
    writer_score = 0

    for code, key, pts, desc, rec, friction in criteria:
        val = p.get(key)
        if val is None:
            unknowns.append(key)
        elif _bool(val):
            score += pts
            surpluses.append(QualificationSurplus(code, desc, True, True, pts))
            if code == "CA_D1":
                director_score = pts
            if code == "CA_D2":
                writer_score = pts
        else:
            deficits.append(QualificationDeficit(code, desc, False, True, friction, rec))

    if score < 6:
        deficits.append(QualificationDeficit(
            "CA_TOTAL", "Total Canadian content points ≥6/10",
            score, 6, 4.0,
            f"Current score {score}/10. Need {6 - score} more points. "
            "Prioritise director (2pts) or writer (2pts) first."
        ))

    if director_score == 0 and writer_score == 0:
        deficits.append(QualificationDeficit(
            "CA_DIR_OR_WRT", "Director OR Writer must be Canadian",
            "neither", "at least one",
            5.0,
            "Either the director or screenwriter MUST be Canadian. Engage at least one."
        ))

    return deficits, surpluses, unknowns


def _analyse_section_481(p: dict) -> tuple[list[QualificationDeficit], list[QualificationSurplus], list[str]]:
    deficits = []
    surpluses = []
    unknowns = []

    # Irish entity
    has_ie = p.get("has_irish_entity")
    if has_ie is None:
        unknowns.append("has_irish_entity")
    elif not _bool(has_ie):
        deficits.append(QualificationDeficit(
            "IE_ENTITY", "Irish-resident or EEA qualifying production company",
            False, True, 4.0,
            "Establish an Irish-resident company or partner with an Irish qualifying producer. "
            "EEA company with Irish qualifying production also acceptable."
        ))

    # Irish qualifying spend
    ie_spend = p.get("irish_qualifying_spend_usd")
    if ie_spend is None:
        unknowns.append("irish_qualifying_spend_usd")
    else:
        if float(ie_spend) < 125_000:
            deficits.append(QualificationDeficit(
                "IE_MIN_SPEND", "Minimum €125,000 Irish qualifying expenditure",
                ie_spend, 125_000, 3.5,
                "Increase Irish qualifying expenditure to at least €125,000. "
                "Shift post-production, crew, or location work to Ireland."
            ))

    # Qualifying production type
    prod_type = p.get("production_type")
    if prod_type is None:
        unknowns.append("production_type")

    return deficits, surpluses, unknowns


def _analyse_eurimages(p: dict) -> tuple[list[QualificationDeficit], list[QualificationSurplus], list[str]]:
    deficits = []
    surpluses = []
    unknowns = []

    country_count = p.get("coproduction_country_count")
    if country_count is None:
        unknowns.append("coproduction_country_count")
    elif _int(country_count) < 2:
        deficits.append(QualificationDeficit(
            "EUR_COUNTRIES", "At least 2 Eurimages member country co-producers",
            country_count, 2, 5.0,
            "Add a co-producer from a second Eurimages member country. "
            "See eurimages.coe.int for full member list."
        ))

    all_members = p.get("all_coproducers_eurimages_members")
    if all_members is None:
        unknowns.append("all_coproducers_eurimages_members")
    elif not _bool(all_members):
        deficits.append(QualificationDeficit(
            "EUR_MEMBERS", "All co-producers from Eurimages member states",
            False, True, 4.0,
            "Ensure all co-producers are from Council of Europe / Eurimages member states."
        ))

    majority_pct = p.get("majority_pct")
    if majority_pct is None:
        unknowns.append("majority_pct")
    elif _pct(majority_pct) > 0.80:
        deficits.append(QualificationDeficit(
            "EUR_MAX", "No single country exceeds 80% of budget",
            majority_pct, 0.80, 4.0,
            "Reduce majority co-producer share below 80% by increasing minority co-producer contributions."
        ))

    minority_pct = p.get("minority_pct")
    if minority_pct is None:
        unknowns.append("minority_pct")
    elif _pct(minority_pct) < 0.10:
        deficits.append(QualificationDeficit(
            "EUR_MIN", "Each co-producer must have at least 10% share",
            minority_pct, 0.10, 3.5,
            "Increase minority co-producer share to at least 10% of total budget."
        ))

    return deficits, surpluses, unknowns


def _analyse_australian_content(p: dict) -> tuple[list[QualificationDeficit], list[QualificationSurplus], list[str]]:
    deficits = []
    surpluses = []
    unknowns = []
    score = 0
    max_pts = 16
    threshold = 8

    criteria = [
        ("AU_A", "australian_underlying_rights", 3, "Australian script/underlying rights",
         "Acquire Australian underlying rights or commission Australian screenplay (3 pts).", 4.0),
        ("AU_B", "director_au", 3, "Director Australian",
         "Engage an Australian director (3 pts).", 3.5),
        ("AU_C", "producer_au", 3, "Producer Australian",
         "Engage an Australian producer (3 pts).", 3.5),
        ("AU_D", "lead_cast_uk", 2, "Lead actor Australian",
         "Cast an Australian national in the lead role (2 pts).", 4.0),
        ("AU_E", "au_cast_days_pct", 2, "≥50% Australian cast days",
         "Ensure at least 50% of cast days are Australian (2 pts).", 3.0),
        ("AU_F", "composer_au" if "composer_au" in p else "composer_uk", 1, "Australian music/composer",
         "Commission score from an Australian composer (1 pt).", 2.0),
        ("AU_G", "post_production_au", 2, "Post-production in Australia",
         "Perform principal post-production in Australia (2 pts).", 2.5),
    ]

    for code, key, pts, desc, rec, friction in criteria:
        val = p.get(key)
        if val is None:
            unknowns.append(key)
        elif _bool(val) or (isinstance(val, float) and val >= 0.50):
            score += pts
            surpluses.append(QualificationSurplus(code, desc, val, True, pts))
        else:
            deficits.append(QualificationDeficit(code, desc, val, True, friction, rec))

    if score < threshold:
        deficits.append(QualificationDeficit(
            "AU_TOTAL", f"Total Australian content points ≥{threshold}/{max_pts}",
            score, threshold, 3.0,
            f"Current score {score}/{max_pts}. Need {threshold - score} more points. "
            "Prioritise director (3pts), producer (3pts), or underlying rights (3pts)."
        ))

    return deficits, surpluses, unknowns


# Test slug → analyser mapping
_ANALYSERS = {
    "uk_bfi_cultural_test": _analyse_bfi,
    "ca_content_test": _analyse_canadian_content,
    "ie_section_481_test": _analyse_section_481,
    "eu_eurimages_test": _analyse_eurimages,
    "au_content_test": _analyse_australian_content,
}

# Program slug → test slug mapping
_PROGRAM_TEST_MAP: dict[str, str] = {
    "uk_avec": "uk_bfi_cultural_test",
    "gb_bfi_production": "uk_bfi_cultural_test",
    "ca_federal_cptc": "ca_content_test",
    "ca_cmf": "ca_content_test",
    "ca_bell_fund": "ca_content_test",
    "ie_section_481": "ie_section_481_test",
    "eu_eurimages": "eu_eurimages_test",
    "ibermedia_programme": "ibermedia_test",
    "au_producer_offset": "au_content_test",
}


# ---------------------------------------------------------------------------
# Qualification path recommendations
# ---------------------------------------------------------------------------

_PATHS_BY_TEST: dict[str, list[QualificationPath]] = {
    "uk_bfi_cultural_test": [
        QualificationPath(
            "bfi_composer_vfx",
            "Add British composer + UK VFX (lowest friction, +2 pts)",
            2.5,
            ["Contract a British or UK-resident composer for the score",
             "Move VFX work to a qualifying UK VFX facility"],
            "Gains 2 points from Section C/D — enough to close a small deficit",
            ["uk_avec"],
        ),
        QualificationPath(
            "bfi_crew_shift",
            "Shift crew to UK nationals to reach 50% crew days",
            4.0,
            ["Review crew list and replace non-UK crew with UK-resident equivalents",
             "Target HoDs first (DoP, Editor, Production Designer) for maximum point efficiency"],
            "D8 criterion (50% UK crew days, 1pt) and individual HoD points",
            ["uk_avec"],
        ),
        QualificationPath(
            "bfi_vfx_post",
            "Move post-production and VFX to UK",
            3.5,
            ["Engage a UK post-production facility for editing, colour, and audio",
             "Move VFX work to a qualifying UK VFX company"],
            "C2 criterion (1pt VFX) plus potential D8 crew days from UK post crew",
            ["uk_avec"],
        ),
        QualificationPath(
            "bfi_uk_shoot",
            "Relocate primary shoot location to UK (≥50% principal photography)",
            8.0,
            ["Identify UK locations equivalent to current locations",
             "Move ≥50% of principal photography shoot days to UK",
             "This will also gain D8 crew days as crew becomes UK-based"],
            "C1 (2pts) + likely D8 (1pt) = structural improvement of 3pts",
            ["uk_avec"],
            "High friction — significant production redesign required",
        ),
    ],
    "ca_content_test": [
        QualificationPath(
            "ca_director_writer",
            "Engage Canadian director AND writer (+4 pts — highest impact)",
            3.0,
            ["Engage a Canadian director (2pts)",
             "Engage a Canadian screenwriter or WGA/DGC-qualifying writer (2pts)"],
            "Director + writer = 4/10 points; most efficient single path",
            ["ca_federal_cptc", "ca_cmf"],
        ),
        QualificationPath(
            "ca_crew_stack",
            "Stack Canadian HoDs to reach 6/10 via crew roles",
            3.5,
            ["Engage Canadian director (2pts)",
             "Engage Canadian DoP (1pt)",
             "Engage Canadian editor (1pt)",
             "Engage Canadian composer (1pt)",
             "Engage Canadian art director (1pt)"],
            "6 points via crew — achieves minimum without star cast change",
            ["ca_federal_cptc"],
        ),
        QualificationPath(
            "ca_cast_upgrade",
            "Add Canadian lead + second lead to reach threshold",
            5.0,
            ["Cast a Canadian national in the lead role (1pt)",
             "Cast a Canadian in the second lead (1pt)",
             "Combine with Canadian director/writer for full qualification"],
            "Cast-level changes required; 2pts from cast",
            ["ca_federal_cptc"],
        ),
    ],
    "ie_section_481_test": [
        QualificationPath(
            "ie_entity_setup",
            "Establish Irish qualifying entity",
            4.0,
            ["Incorporate an Irish-resident special purpose vehicle (SPV)",
             "Or partner with an Irish qualifying production company as co-producer",
             "Ensure Irish QE exceeds €125,000"],
            "Irish entity is the gating requirement — without it Section 481 is unavailable",
            ["ie_section_481"],
        ),
        QualificationPath(
            "ie_spend_shift",
            "Increase Irish qualifying expenditure above €125,000",
            3.0,
            ["Move location filming to Ireland to generate Irish spend",
             "Engage Irish crew for qualifying phases",
             "Move post-production to an Irish facility"],
            "Increases Irish QE and strengthens Section 481 eligibility",
            ["ie_section_481"],
        ),
    ],
    "eu_eurimages_test": [
        QualificationPath(
            "eurimages_second_producer",
            "Add minority co-producer from second Eurimages member state",
            5.0,
            ["Identify a co-production partner in a second Eurimages member country",
             "Ensure minority co-producer receives ≥10% and ≤80% of budget",
             "File formal co-production agreement"],
            "Adds second qualifying country — mandatory for Eurimages",
            ["eu_eurimages"],
        ),
        QualificationPath(
            "eurimages_rebalance",
            "Rebalance co-production shares to meet 10-80% band",
            3.0,
            ["Reduce majority co-producer share to ≤80%",
             "Increase minority co-producer share to ≥10%"],
            "Budget rebalancing — contractual change required",
            ["eu_eurimages"],
        ),
    ],
    "au_content_test": [
        QualificationPath(
            "au_director_producer",
            "Engage Australian director + producer (+6 pts combined)",
            3.5,
            ["Engage an Australian director (3pts)",
             "Engage an Australian producer (3pts)"],
            "Highest-impact path — 6/8 pts needed in single step",
            ["au_producer_offset"],
        ),
        QualificationPath(
            "au_post_rights",
            "Australian underlying rights + Australian post-production",
            4.0,
            ["Acquire Australian underlying rights or commission Australian screenplay (3pts)",
             "Perform principal post-production in Australia (2pts)"],
            "5pts without changing director or cast",
            ["au_producer_offset"],
        ),
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_test_slug_for_program(program_slug: str) -> str | None:
    """Return the test slug associated with a program, if any."""
    return _PROGRAM_TEST_MAP.get(program_slug)


def analyse_qualification(
    program_slug: str,
    production_profile: dict[str, Any],
    test_slug: str | None = None,
) -> QualificationAnalysis:
    """
    Analyse qualification status for a program given a production profile.

    Returns deficits, surpluses, and recommended paths sorted by friction.
    """
    resolved_test = test_slug or _PROGRAM_TEST_MAP.get(program_slug) or "unknown"

    analyser = _ANALYSERS.get(resolved_test)
    deficits: list[QualificationDeficit] = []
    surpluses: list[QualificationSurplus] = []
    unknowns: list[str] = []

    if analyser:
        deficits, surpluses, unknowns = analyser(production_profile)

    is_qualifying = len(deficits) == 0 and analyser is not None

    # Pull test score if possible
    score, required, gap = None, None, None
    if resolved_test == "uk_bfi_cultural_test":
        try:
            from app.calculators.evaluate_qualification_tests import score_uk_bfi_cultural_test
            r = score_uk_bfi_cultural_test(production_profile)
            score = r.total_score
            required = r.minimum_required
            gap = max(0, required - score)
            is_qualifying = r.passes_overall
        except ImportError:
            pass

    paths = _PATHS_BY_TEST.get(resolved_test, [])
    if deficits:
        paths = sorted(paths, key=lambda p: p.friction_score)

    return QualificationAnalysis(
        program_slug=program_slug,
        test_slug=resolved_test,
        production_profile=production_profile,
        is_currently_qualifying=is_qualifying,
        current_score=score,
        required_score=required,
        score_gap=gap,
        deficits=deficits,
        surpluses=surpluses,
        paths=paths,
        disqualifying_factors=[d.description for d in deficits],
        unknown_factors=unknowns,
    )


def get_lowest_friction_path(
    program_slug: str,
    production_profile: dict[str, Any],
) -> QualificationPath | None:
    """Return the single easiest path to qualification, or None if already qualifying."""
    analysis = analyse_qualification(program_slug, production_profile)
    if analysis.is_currently_qualifying:
        return None
    if analysis.paths:
        return analysis.paths[0]
    return None


def summarise_deficits(analysis: QualificationAnalysis) -> list[str]:
    """Return human-readable deficit summary lines."""
    lines = []
    if analysis.score_gap and analysis.score_gap > 0:
        lines.append(
            f"Score gap: {analysis.score_gap} points below threshold "
            f"({analysis.current_score}/{analysis.required_score})"
        )
    for d in analysis.deficits:
        lines.append(f"[{d.criterion_code}] {d.description}: {d.recommendation}")
    for u in analysis.unknown_factors:
        lines.append(f"[UNKNOWN] {u} not provided — cannot evaluate this criterion")
    return lines
