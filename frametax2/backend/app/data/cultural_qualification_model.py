"""
cultural_qualification_model.py

D1 Cultural Qualification Model.
Nationality/role requirements per program slug.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NationalityRequirement:
    program_slug: str
    role: str          # director | writer | producer | lead_cast | supporting_cast |
                       # editor | composer | dop | vfx_supervisor | post_supervisor | entity
    jurisdiction_code: str | None  # None = "any treaty country", "EU" = any EU country
    status: str        # required | optional | weighted | unknown
    weight: float | None   # contribution to cultural test score (0.0-1.0)
    min_pct: float | None  # minimum % of this role that must satisfy requirement
    notes: str


_REQUIREMENTS: list[NationalityRequirement] = [
    # -------------------------------------------------------------------------
    # UK BFI Cultural Test (Sections C/D practitioners)
    # -------------------------------------------------------------------------
    NationalityRequirement("uk_avec", "director",        "GB", "weighted", 0.032, None,
                           "BFI Section D1: British director = 1/31 pts"),
    NationalityRequirement("uk_avec", "writer",          "GB", "weighted", 0.032, None,
                           "BFI Section D2: British writer = 1/31 pts"),
    NationalityRequirement("uk_avec", "producer",        "GB", "weighted", 0.032, None,
                           "BFI Section D3: British producer = 1/31 pts"),
    NationalityRequirement("uk_avec", "composer",        "GB", "weighted", 0.032, None,
                           "BFI Section D4: British composer = 1/31 pts"),
    NationalityRequirement("uk_avec", "lead_cast",       "GB", "weighted", 0.032, None,
                           "BFI Section D5: British lead actor = 1/31 pts"),
    NationalityRequirement("uk_avec", "supporting_cast", "GB", "weighted", 0.032, None,
                           "BFI Section D6: British second lead = 1/31 pts"),
    NationalityRequirement("uk_avec", "editor",          "GB", "weighted", 0.032, 0.50,
                           "BFI Section D8: >=50% crew days British includes editor"),
    NationalityRequirement("uk_avec", "dop",             "GB", "weighted", 0.032, 0.50,
                           "BFI Section D8: >=50% crew days British includes DoP"),
    NationalityRequirement("uk_avec", "vfx_supervisor",  "GB", "weighted", 0.032, None,
                           "BFI Section C2: VFX work in UK = 1/31 pts"),

    # -------------------------------------------------------------------------
    # Ireland Section 481
    # -------------------------------------------------------------------------
    NationalityRequirement("ie_section_481", "entity",   "IE", "required", None, None,
                           "Irish-resident production company or EEA qualifying entity required"),
    NationalityRequirement("ie_section_481", "producer", "IE", "optional", None, None,
                           "Irish producer preferred but not statutorily required"),
    NationalityRequirement("ie_section_481", "director", "IE", "optional", None, None,
                           "Irish director preferred but not statutorily required"),

    # -------------------------------------------------------------------------
    # France TRIP (Territorial Rebate for International Productions)
    # No nationality test — spend-based only
    # -------------------------------------------------------------------------
    # (no NationalityRequirement rows; has_cultural_test returns False)

    # -------------------------------------------------------------------------
    # France CNC Production Support
    # -------------------------------------------------------------------------
    NationalityRequirement("fr_cnc_production", "director", "EU", "required", None, None,
                           "Director must be French national or EEA citizen; UNKNOWN if 3rd-country treaty applies"),
    NationalityRequirement("fr_cnc_production", "writer",   "EU", "required", None, None,
                           "Writer must be French/EEA; at least director OR writer must be French national"),
    NationalityRequirement("fr_cnc_production", "producer", "FR", "required", None, None,
                           "Producer (société de production) must be French-registered entity"),

    # -------------------------------------------------------------------------
    # Canada Federal CPTC (Canadian Film or Video Production Tax Credit)
    # -------------------------------------------------------------------------
    NationalityRequirement("ca_federal_cptc", "director",        "CA", "required", None, None,
                           "Canadian or treaty director; non-Canadian director kills CPTC eligibility unless treaty co-prod"),
    NationalityRequirement("ca_federal_cptc", "writer",          "CA", "required", None, None,
                           "Canadian or treaty writer required"),
    NationalityRequirement("ca_federal_cptc", "producer",        "CA", "required", None, None,
                           "Canadian producer (key creative control) required"),
    NationalityRequirement("ca_federal_cptc", "lead_cast",       "CA", "required", None, 1.0,
                           "At minimum 1 Canadian lead performer required"),
    NationalityRequirement("ca_federal_cptc", "supporting_cast", "CA", "weighted", 0.1, None,
                           "Canadian supporting cast contributes to 6/10 content point minimum"),

    # -------------------------------------------------------------------------
    # Canada CMF (Canada Media Fund)
    # -------------------------------------------------------------------------
    NationalityRequirement("ca_cmf", "director", "CA", "required", None, None,
                           "Canadian director required for CMF Convergent Stream"),
    NationalityRequirement("ca_cmf", "writer",   "CA", "required", None, None,
                           "Canadian writer required for CMF Convergent Stream"),

    # -------------------------------------------------------------------------
    # Eurimages Co-production Fund
    # -------------------------------------------------------------------------
    NationalityRequirement("eu_eurimages", "producer", None, "required", None, None,
                           "Each co-producer must be from a Eurimages member state; None = any member state"),
    NationalityRequirement("eu_eurimages", "entity",   None, "required", None, None,
                           "Each co-producing entity must be registered in a Eurimages member state"),

    # -------------------------------------------------------------------------
    # Ibermedia Programme
    # -------------------------------------------------------------------------
    NationalityRequirement("ibermedia_programme", "producer", None, "required", None, None,
                           "Producer must be from an Ibermedia member state (Ibero-American country)"),
    NationalityRequirement("ibermedia_programme", "entity",   None, "required", None, None,
                           "Co-producing entity must be from an Ibero-American member country"),

    # -------------------------------------------------------------------------
    # Australia Producer Offset (Australian content test)
    # -------------------------------------------------------------------------
    NationalityRequirement("au_producer_offset", "director",        "AU", "weighted", 0.1875, None,
                           "Australian director = 3/16 pts in Aus content test"),
    NationalityRequirement("au_producer_offset", "writer",          "AU", "weighted", 0.0,    None,
                           "Script/underlying rights Australian = separate criterion; writer nationality not scored directly — UNKNOWN"),
    NationalityRequirement("au_producer_offset", "producer",        "AU", "weighted", 0.1875, None,
                           "Australian producer = 3/16 pts"),
    NationalityRequirement("au_producer_offset", "lead_cast",       "AU", "weighted", 0.125,  None,
                           "Australian lead actor = 2/16 pts"),
    NationalityRequirement("au_producer_offset", "supporting_cast", "AU", "weighted", 0.125,  0.50,
                           ">=50% supporting cast Australian = 2/16 pts"),
    NationalityRequirement("au_producer_offset", "composer",        "AU", "weighted", 0.0625, None,
                           "Australian music = 1/16 pts"),

    # -------------------------------------------------------------------------
    # Australia Location Offset — no cultural test, spend-based only
    # -------------------------------------------------------------------------
    # (no rows)

    # -------------------------------------------------------------------------
    # Italy Tax Credit for Foreign Productions — no cultural test
    # -------------------------------------------------------------------------
    # (no rows)

    # -------------------------------------------------------------------------
    # Germany DFFF (Deutscher Filmförderfonds)
    # -------------------------------------------------------------------------
    NationalityRequirement("de_dfff", "director", "DE", "weighted", None, None,
                           "Director or producer must qualify under DFFF Fachgutachten cultural test; UNKNOWN exact weight"),
    NationalityRequirement("de_dfff", "producer", "DE", "weighted", None, None,
                           "German or EEA producer may satisfy Fachgutachten requirement; UNKNOWN exact weight"),

    # -------------------------------------------------------------------------
    # EU MEDIA Fund (Creative Europe MEDIA)
    # -------------------------------------------------------------------------
    NationalityRequirement("eu_media_fund", "entity",   "EU", "required", None, None,
                           "Applicant entity must be registered in EU/EEA country"),
    NationalityRequirement("eu_media_fund", "director", "EU", "optional", None, None,
                           "EU/EEA director preferred but not strictly required for development grants"),

    # -------------------------------------------------------------------------
    # Netherlands HBF (Holland Film Meeting / Dutch Film Fund co-production)
    # -------------------------------------------------------------------------
    NationalityRequirement("nl_hbf", "director", "NL", "required", None, None,
                           "Dutch national or treaty director (or writer) required; UNKNOWN if both may be non-Dutch"),
    NationalityRequirement("nl_hbf", "writer",   "NL", "required", None, None,
                           "Dutch or treaty writer satisfies creative element requirement alternatively to director"),
    NationalityRequirement("nl_hbf", "producer", "NL", "required", None, None,
                           "Dutch producer required as lead applicant"),

    # -------------------------------------------------------------------------
    # Nordic FTVF (Film- og TV-fonden, Denmark lead, pan-Nordic variant)
    # -------------------------------------------------------------------------
    NationalityRequirement("nordic_ftvf", "director", None, "required", None, None,
                           "Nordic national (DK/SE/NO/FI/IS) director or producer required; None = any Nordic country"),
    NationalityRequirement("nordic_ftvf", "producer", None, "required", None, None,
                           "Nordic producer required"),
    NationalityRequirement("nordic_ftvf", "entity",   None, "required", None, None,
                           "Co-producing entity must be from a Nordic country"),

    # -------------------------------------------------------------------------
    # Denmark DFI Support
    # -------------------------------------------------------------------------
    NationalityRequirement("dk_dfi_support", "director", "DK", "required", None, None,
                           "Danish director or writer required as creative element"),
    NationalityRequirement("dk_dfi_support", "writer",   "DK", "required", None, None,
                           "Danish writer satisfies creative element requirement alternatively to director"),

    # -------------------------------------------------------------------------
    # Norway NFI Grants
    # -------------------------------------------------------------------------
    NationalityRequirement("no_nfi_grants", "director", "NO", "required", None, None,
                           "Norwegian director or writer required"),
    NationalityRequirement("no_nfi_grants", "writer",   "NO", "required", None, None,
                           "Norwegian writer satisfies creative element requirement alternatively to director"),

    # -------------------------------------------------------------------------
    # Finland SES Grants
    # -------------------------------------------------------------------------
    NationalityRequirement("fi_ses_grants", "director", "FI", "required", None, None,
                           "Finnish creative element — director or writer; UNKNOWN if both required"),
    NationalityRequirement("fi_ses_grants", "writer",   "FI", "required", None, None,
                           "Finnish writer satisfies requirement alternatively to director"),

    # -------------------------------------------------------------------------
    # Sweden Göteborg Fund
    # -------------------------------------------------------------------------
    NationalityRequirement("se_goteborg_fund", "director", "SE", "required", None, None,
                           "Swedish/regional creative element required; UNKNOWN specific threshold"),
    NationalityRequirement("se_goteborg_fund", "writer",   "SE", "optional", None, None,
                           "Swedish writer preferred; UNKNOWN if strictly required"),
    NationalityRequirement("se_goteborg_fund", "producer", "SE", "required", None, None,
                           "Swedish producer or regional entity required"),

    # -------------------------------------------------------------------------
    # Film i Väst (Swedish regional fund — Västra Götaland)
    # -------------------------------------------------------------------------
    NationalityRequirement("film_i_vast", "entity",   "SE", "required", None, None,
                           "Production must have meaningful connection to Västra Götaland region; entity or shoot location"),
    NationalityRequirement("film_i_vast", "producer", "SE", "required", None, None,
                           "Producer or co-producer with Västra Götaland ties required; UNKNOWN exact threshold"),

    # -------------------------------------------------------------------------
    # Poland PISF Grants
    # -------------------------------------------------------------------------
    NationalityRequirement("pl_pisf_grants", "director",  "PL", "required", None, None,
                           "Polish director or Polish-language screenplay required"),
    NationalityRequirement("pl_pisf_grants", "writer",    "PL", "required", None, None,
                           "Polish screenplay satisfies requirement alternatively to Polish director"),
    NationalityRequirement("pl_pisf_grants", "producer",  "PL", "required", None, None,
                           "Polish producer required as applicant"),

    # -------------------------------------------------------------------------
    # Czech Film Fund
    # -------------------------------------------------------------------------
    NationalityRequirement("cz_czech_film_fund", "director", "CZ", "required", None, None,
                           "Czech creative element required; UNKNOWN if writer alternatively acceptable"),
    NationalityRequirement("cz_czech_film_fund", "producer", "CZ", "required", None, None,
                           "Czech producer required"),

    # -------------------------------------------------------------------------
    # Hungary NFI Grants
    # -------------------------------------------------------------------------
    NationalityRequirement("hu_nfi_grants", "director", "HU", "required", None, None,
                           "Hungarian creative element required; UNKNOWN exact scope"),
    NationalityRequirement("hu_nfi_grants", "producer", "HU", "required", None, None,
                           "Hungarian producer required as applicant"),

    # -------------------------------------------------------------------------
    # Austria ÖFI Grants
    # -------------------------------------------------------------------------
    NationalityRequirement("at_ofi_grants", "director", "AT", "required", None, None,
                           "Austrian creative element required; UNKNOWN if writer alternatively acceptable"),
    NationalityRequirement("at_ofi_grants", "producer", "AT", "required", None, None,
                           "Austrian producer required"),

    # -------------------------------------------------------------------------
    # Portugal ICA Grants
    # -------------------------------------------------------------------------
    NationalityRequirement("pt_ica_grants", "director", "PT", "required", None, None,
                           "Portuguese creative element required; UNKNOWN exact scope"),
    NationalityRequirement("pt_ica_grants", "producer", "PT", "required", None, None,
                           "Portuguese producer required as applicant"),

    # -------------------------------------------------------------------------
    # Greece GNF Grants
    # -------------------------------------------------------------------------
    NationalityRequirement("gr_gnf_grants", "director", "GR", "required", None, None,
                           "Greek creative element required; UNKNOWN exact scope"),
    NationalityRequirement("gr_gnf_grants", "producer", "GR", "required", None, None,
                           "Greek producer required as applicant"),

    # -------------------------------------------------------------------------
    # Bosnia-Herzegovina Film Centre
    # -------------------------------------------------------------------------
    NationalityRequirement("ba_film_centre", "director", "BA", "required", None, None,
                           "Bosnian creative element required; UNKNOWN if writer alternatively acceptable"),
    NationalityRequirement("ba_film_centre", "producer", "BA", "required", None, None,
                           "Bosnian producer required as applicant"),
]

# Public exports
NATIONALITY_REQUIREMENTS: list[NationalityRequirement] = _REQUIREMENTS


def get_requirements(program_slug: str) -> list[NationalityRequirement]:
    """Return all NationalityRequirement entries for a given program slug."""
    return [r for r in _REQUIREMENTS if r.program_slug == program_slug]


def get_required_roles(program_slug: str) -> list[str]:
    """Return role names where status == 'required' for a given program slug."""
    return [r.role for r in _REQUIREMENTS
            if r.program_slug == program_slug and r.status == "required"]


# Programs that have no nationality/cultural requirements (spend-based only)
_SPEND_ONLY_SLUGS: frozenset[str] = frozenset([
    "fr_trip",
    "au_location_offset",
    "it_tax_credit_foreign",
])


def has_cultural_test(program_slug: str) -> bool:
    """
    Return True if the program has any nationality or cultural test requirements.
    Returns False for spend-only incentives with no cultural gate.
    """
    if program_slug in _SPEND_ONLY_SLUGS:
        return False
    return any(r.program_slug == program_slug for r in _REQUIREMENTS)


# ── Threshold / eligibility gate execution ───────────────────────────────────
#
# Every row above with status == "required" is a hard eligibility GATE, not
# a points contribution: e.g. ca_federal_cptc requires a Canadian-or-treaty
# director AND writer AND producer AND at least one Canadian lead — missing
# any one of these makes the production categorically ineligible for that
# program, regardless of how many points a separate cultural-content test
# might award elsewhere. This is the layer that must run BEFORE any points
# system (cultural_test_rules.py's score_qualification_test) — until now
# this data existed but nothing in the codebase executed it.
#
# jurisdiction_code semantics on a NationalityRequirement:
#   ISO2 code  -> the role must hold that exact citizenship/residency.
#   "EU"       -> requires EU/EEA membership. No EU/EEA membership list
#                 exists anywhere in this codebase (only Eurimages/
#                 Ibermedia/European Convention checks in treaty_engine.py,
#                 which are NOT EU membership) — never fabricated here;
#                 always INDETERMINATE, with a note naming exactly what's
#                 missing.
#   None       -> "any treaty country" — requires knowing the elected
#                 treaty partner (a production_facts input, not a person
#                 fact); INDETERMINATE unless the caller supplies one.

class GateStatus:
    SATISFIED = "satisfied"
    FAILED = "failed"
    INDETERMINATE = "indeterminate"  # not enough verified fact to conclude


@dataclass(frozen=True)
class GateCheck:
    role: str
    required_jurisdiction: str | None
    status: str  # GateStatus
    known_codes: tuple[str, ...]  # the role's actually-known citizenship/residency codes, if any
    notes: str


@dataclass(frozen=True)
class EligibilityGateResult:
    program_slug: str
    checks: tuple[GateCheck, ...]

    @property
    def passes(self) -> bool:
        """True only when every required gate is SATISFIED. A single
        FAILED or INDETERMINATE gate means the production cannot be
        certified eligible yet — indeterminate is not the same as
        passing (never silently assumed satisfied)."""
        return all(c.status == GateStatus.SATISFIED for c in self.checks)

    @property
    def has_failure(self) -> bool:
        """True when at least one gate is definitively FAILED (a known
        fact contradicts the requirement) — distinct from merely
        indeterminate/unanswered."""
        return any(c.status == GateStatus.FAILED for c in self.checks)

    @property
    def indeterminate_roles(self) -> tuple[str, ...]:
        return tuple(c.role for c in self.checks if c.status == GateStatus.INDETERMINATE)


def evaluate_program_eligibility(
    program_slug: str,
    role_known_codes: dict[str, tuple[str, ...]],
    treaty_partner_code: str | None = None,
) -> EligibilityGateResult:
    """
    Evaluate every REQUIRED gate for program_slug against real, known
    facts. role_known_codes: role name -> tuple of citizenship/residency
    ISO2 codes actually on file for that role (empty tuple = no person/
    entity known for that role at all -> INDETERMINATE, never FAILED,
    since absence of a fact is not evidence against it).

    Returns an empty checks tuple (passes=True) for a program with no
    required gates — never fabricates a gate that isn't in the data.
    """
    checks: list[GateCheck] = []
    for req in get_requirements(program_slug):
        if req.status != "required":
            continue
        known = role_known_codes.get(req.role, ())
        if not known:
            checks.append(GateCheck(
                role=req.role, required_jurisdiction=req.jurisdiction_code,
                status=GateStatus.INDETERMINATE, known_codes=known,
                notes=f"No {req.role} is on file yet — cannot determine "
                      f"whether the requirement ('{req.notes}') is met.",
            ))
            continue
        if req.jurisdiction_code is None:
            if treaty_partner_code and treaty_partner_code.upper() in known:
                checks.append(GateCheck(
                    role=req.role, required_jurisdiction=None, status=GateStatus.SATISFIED,
                    known_codes=known, notes=f"{req.role} holds elected treaty partner {treaty_partner_code}.",
                ))
            else:
                checks.append(GateCheck(
                    role=req.role, required_jurisdiction=None, status=GateStatus.INDETERMINATE,
                    known_codes=known,
                    notes="Requirement is 'any treaty country' but no treaty partner is elected yet — "
                          "cannot determine which country would satisfy it.",
                ))
        elif req.jurisdiction_code == "EU":
            checks.append(GateCheck(
                role=req.role, required_jurisdiction="EU", status=GateStatus.INDETERMINATE,
                known_codes=known,
                notes="Requirement is EU/EEA membership — no EU/EEA membership list exists in this "
                      "codebase (only Eurimages/Ibermedia/European Convention signatory checks, which "
                      "are not EU membership); never fabricated. Confirm via official EU/EEA status.",
            ))
        else:
            if req.jurisdiction_code.upper() in known:
                checks.append(GateCheck(
                    role=req.role, required_jurisdiction=req.jurisdiction_code, status=GateStatus.SATISFIED,
                    known_codes=known, notes=req.notes,
                ))
            else:
                checks.append(GateCheck(
                    role=req.role, required_jurisdiction=req.jurisdiction_code, status=GateStatus.FAILED,
                    known_codes=known,
                    notes=f"{req.role} is known to hold {known}, none of which is "
                          f"{req.jurisdiction_code} — required: {req.notes}",
                ))
    return EligibilityGateResult(program_slug=program_slug, checks=tuple(checks))
