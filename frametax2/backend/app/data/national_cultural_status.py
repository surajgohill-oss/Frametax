"""
national_cultural_status.py

Worldwide Jurisdiction National/Cultural Status + Incentive Pathway
Completion — the canonical ontology correction this phase's Task 1
mandates. Distinguishes four related-but-distinct concepts that were
previously conflated:

1. INCENTIVE_PROGRAM        — the actual rebate/credit/grant (already
                               modeled by program_requirements.py).
2. NATIONAL_CULTURAL_STATUS — an official domestic/national/cultural
                               certification or qualification regime,
                               modeled here as JurisdictionNationalStatus.
3. PROGRAM_PATHWAY           — the relationship between status and
                               economics (PathwayType below).
4. OFFICIAL_COPRODUCTION_STATUS — a separate structure (treaty_engine.py),
                               only cross-referenced here, never merged.

Key correction from the prior pass: "no cultural test required for base
incentive X" (program_requirements.py's cultural_test_required=False)
does NOT mean "no national/cultural qualification opportunity exists in
this jurisdiction." Canada and Australia are the confirmed proof: their
own service/foreign incentives (ca_federal_pstc, au_location_offset) both
require no cultural test, while a SEPARATE, real, primary-sourced
national/domestic pathway (ca_federal_cptc / au_producer_offset) exists
alongside it with materially different economics.
"""
from __future__ import annotations

from dataclasses import dataclass, field

NATIONAL_CULTURAL_STATUS_VERSION = "1.0.0"

# ── Jurisdiction terminal states (Task 3/20) ─────────────────────────────
STATUS_REGIME_CONFIRMED = "NATIONAL_STATUS_REGIME_CONFIRMED"
STATUS_NO_RELEVANT_REGIME_CONFIRMED = "NO_RELEVANT_NATIONAL_STATUS_REGIME_CONFIRMED"
STATUS_AUTHORITY_UNRESOLVED = "AUTHORITY_UNRESOLVED_EXACT_PROPOSITION"

# ── Program pathway types (Task 1.C) ─────────────────────────────────────
PATHWAY_FOREIGN_SERVICE = "FOREIGN_SERVICE_PATHWAY"
PATHWAY_DOMESTIC_NATIONAL = "DOMESTIC_NATIONAL_PATHWAY"
PATHWAY_CULTURAL_UPLIFT = "CULTURAL_UPLIFT_PATHWAY"
PATHWAY_ALTERNATIVE_QUALIFICATION = "ALTERNATIVE_QUALIFICATION_PATHWAY"
PATHWAY_STATUS_UNLOCKED_PROGRAM = "STATUS_UNLOCKED_PROGRAM"
PATHWAY_STATUS_UNLOCKED_FUNDING = "STATUS_UNLOCKED_FUNDING"
PATHWAY_NO_ECONOMIC_DIFFERENCE = "NO_ECONOMIC_DIFFERENCE"
PATHWAY_OTHER = "OTHER_AUTHORITY_DEFINED_PATHWAY"

# ── Economic/structural consequence (Task 6) ─────────────────────────────
CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE = "UNLOCKS_SEPARATE_INCENTIVE"
CONSEQUENCE_UNLOCKS_ENHANCED_RATE = "UNLOCKS_ENHANCED_RATE"
CONSEQUENCE_UNLOCKS_UPLIFT = "UNLOCKS_UPLIFT"
CONSEQUENCE_UNLOCKS_GRANT_OR_FUND = "UNLOCKS_GRANT_OR_FUND"
CONSEQUENCE_UNLOCKS_DOMESTIC_PROGRAM = "UNLOCKS_DOMESTIC_PROGRAM"
CONSEQUENCE_CHANGES_ELIGIBLE_QPE = "CHANGES_ELIGIBLE_QPE"
CONSEQUENCE_CHANGES_CAP = "CHANGES_CAP"
CONSEQUENCE_UNLOCKS_OFFICIAL_COPRO_TREATMENT = "UNLOCKS_OFFICIAL_COPRO_TREATMENT"
CONSEQUENCE_QUOTA_OR_NON_ECONOMIC = "QUOTA_OR_NON_ECONOMIC_STATUS_ONLY"
CONSEQUENCE_NO_INCREMENTAL_BENEFIT = "NO_INCREMENTAL_ECONOMIC_BENEFIT"
CONSEQUENCE_OTHER = "OTHER"
CONSEQUENCE_IS_BASE_PROGRAM = "IS_BASE_PROGRAM_ELIGIBILITY_GATE"  # status IS the incentive's own gate, not a separate unlock

# ── Task 2 — corrected base-incentive cultural-test semantics ───────────
# Replaces the ambiguous CULTURAL_TEST_NOT_APPLICABLE with precise states.
# A base incentive can correctly say NOT_REQUIRED_FOR_THIS_INCENTIVE while
# its jurisdiction separately has a real DOMESTIC_NATIONAL_PATHWAY.
BASE_INCENTIVE_NOT_REQUIRED = "NOT_REQUIRED_FOR_THIS_INCENTIVE"
BASE_INCENTIVE_REQUIRED = "REQUIRED_FOR_THIS_INCENTIVE"
BASE_INCENTIVE_REQUIRED_FOR_ENHANCED = "REQUIRED_FOR_ENHANCED_INCENTIVE"
BASE_INCENTIVE_REQUIRED_FOR_NATIONAL_STATUS = "REQUIRED_FOR_NATIONAL_STATUS"
BASE_INCENTIVE_ALTERNATIVE_PATHWAY_EXISTS = "ALTERNATIVE_NATIONAL_PATHWAY_EXISTS"
BASE_INCENTIVE_NO_REGIME_CONFIRMED = "NO_RELEVANT_NATIONAL_STATUS_REGIME_CONFIRMED"
BASE_INCENTIVE_AUTHORITY_UNRESOLVED = "AUTHORITY_UNRESOLVED"


@dataclass(frozen=True)
class JurisdictionNationalStatus:
    """One jurisdiction's (country-level, ISO2) national/cultural status
    determination. Country-level, not sub-national: a US state or
    Canadian province does not have its own separate national-content
    certification regime distinct from the federal government's (a real
    modeling choice, not an oversight -- CA-ON/CA-BC/CA-QC's own programs
    are already covered by their own program_requirements.py records, and
    inherit Canada's federal national-status regime rather than defining
    a competing one)."""
    jurisdiction_code: str          # ISO2 country code
    status: str                     # one of the three terminal states above
    regime_name: str | None = None
    administering_authority: str | None = None
    legal_basis: str | None = None
    #: The program_slug this status regime IS or gates (may be the same
    #: as base_program_slug when status is the incentive's own gate).
    linked_program_slug: str | None = None
    #: The service/foreign-production program_slug that exists WITHOUT
    #: requiring this status, if one exists in the current canonical
    #: universe (proves the two pathways are genuinely separate).
    base_program_slug: str | None = None
    pathway_type: str | None = None
    economic_consequence: str | None = None
    #: Real, quantified consequence detail (e.g. "25% vs 16%") — never
    #: fabricated; None when the consequence is non-economic or unresolved.
    consequence_detail: str | None = None
    #: Task 12 — official co-production's relationship to this status,
    #: ONLY when existing authority already establishes it (never
    #: fabricated country-pair eligibility; the dedicated co-production
    #: doctrine pass follows this one).
    coproduction_relationship: str | None = None
    sources: tuple[str, ...] = ()
    exact_unresolved_propositions: tuple[str, ...] = ()
    retrieved_date: str | None = None


#: Real, primary/secondary-authority-researched jurisdictions this pass.
#: Task 8 (Canada, mandatory) + Task 9 (>=3 materially different models).
_CONFIRMED_SEPARATE_PATHWAY: tuple[JurisdictionNationalStatus, ...] = (
    JurisdictionNationalStatus(
        jurisdiction_code="CA",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Canadian Content Certification (CAVCO 10-point scale)",
        administering_authority="Canadian Audio-Visual Certification Office (CAVCO) / Canada Revenue Agency",
        legal_basis="Income Tax Act (Canada) s. 125.4 (CPTC)",
        linked_program_slug="ca_federal_cptc",
        base_program_slug="ca_federal_pstc",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        economic_consequence=CONSEQUENCE_UNLOCKS_ENHANCED_RATE,
        consequence_detail="CPTC 25% of qualified Canadian labour vs PSTC 16% -- a real, quantified "
                            "~9pp rate difference, confirmed via canada.ca (primary) and corroborated "
                            "by hellodarwin.com/Saturation.io/truenorthtaxes.ca.",
        coproduction_relationship="A production made under an official Canadian co-production treaty "
                                   "is certified without separately passing the 10-point test (existing "
                                   "treaty_engine.py bilateral registry already carries Canada's real "
                                   "treaty partners) -- confirmed via CAVCO's own CPTC guidelines "
                                   "referencing co-production certificates as an alternate route.",
        sources=(
            "https://www.canada.ca/en/canadian-heritage/services/funding/cavco-tax-credits/canadian-film-video-production.html",
            "https://hellodarwin.com/business-aid/programs/canadian-film-or-video-production-tax-credit",
            "https://grantcompass.ca/grants/canadian-film-or-video-production-tax-credit",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="AU",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Significant Australian Content (SAC) test",
        administering_authority="Screen Australia",
        legal_basis="Income Tax Assessment Act 1997 (Cth), Producer Offset provisions",
        linked_program_slug="au_producer_offset",
        base_program_slug="au_location_offset",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        economic_consequence=CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE,
        consequence_detail="Producer Offset 40% (theatrical feature) / 30% (other formats) of QAPE, "
                            "a genuinely SEPARATE program from Location Offset (spend-only, no content "
                            "test) -- confirmed via screenaustralia.gov.au (primary).",
        coproduction_relationship="Confirmed via Screen Australia (primary): 'Official co-productions "
                                   "automatically satisfy the SAC test' -- an explicit, authority-stated "
                                   "relationship, encoded without completing the treaty universe.",
        sources=(
            "https://www.screenaustralia.gov.au/producer-offset/",
            "https://www.screenaustralia.gov.au/funding-and-support/producer-offset/guidelines/eligibility/significant-australian-content",
            "https://www.ausfilm.com.au/incentives/the-producer-offset-and-co-production-treaties/",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="NZ",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Significant New Zealand Content points test (New Zealand Production Grant)",
        administering_authority="New Zealand Film Commission (NZFC) / Ministry for Culture and Heritage",
        legal_basis="New Zealand Screen Production Grant framework",
        linked_program_slug=None,  # the NZ-production 40% grant is not itself a separate program_requirements.py record this pass
        base_program_slug="nz_spg_international",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        economic_consequence=CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE,
        consequence_detail="A 40% grant is available for New Zealand productions (vs the International "
                            "rebate's 20% baseline) -- eligibility requires either significant NZ "
                            "content (points-based test) OR official co-production status. Recovered "
                            "from this same multi-pass arc's own prior research (nzfilm.co.nz, "
                            "beehive.govt.nz), not re-researched.",
        coproduction_relationship="Confirmed via NZFC: official co-production status is an explicit "
                                   "ALTERNATIVE route to the points test for the 40% NZ-production grant.",
        sources=(
            "https://www.nzfilm.co.nz/news/new-zealand-screen-production-grant",
            "https://www.beehive.govt.nz/release/incentive-changes-sustainable-nz-screen-industry",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="US",
        status=STATUS_NO_RELEVANT_REGIME_CONFIRMED,
        regime_name=None,
        administering_authority=None,
        legal_basis=None,
        linked_program_slug=None,
        base_program_slug="us_ca_film_credit",  # representative; all US state programs already False
        pathway_type=PATHWAY_NO_ECONOMIC_DIFFERENCE,
        economic_consequence=CONSEQUENCE_NO_INCREMENTAL_BENEFIT,
        consequence_detail="No current federal film tax credit exists at all (each state operates "
                            "independently, already confirmed cultural_test_required=False for every "
                            "US program in the canonical universe); no federal 'American content' "
                            "certification analogous to Canada's CPTC or Australia's Producer Offset "
                            "was found. A 2026 federal proposal (reported, not enacted) does not "
                            "change the CURRENT confirmed state.",
        sources=(
            "https://www.wrapbook.com/production-incentives/us/federal",
            "https://reedcorp.tax/helpful-guides/film-production-tax-credits-state/",
        ),
        retrieved_date="2026-08-19",
    ),
)

#: Country codes already resolved by the prior pass's cultural_test_
#: required=True finding: their own base incentive's cultural test IS
#: the effective national/cultural status regime (no separate program
#: exists in the canonical universe to unlock) -- computed from
#: program_requirements.py at import time, never hand-duplicated.
def _base_incentive_is_national_status_countries() -> tuple[str, ...]:
    from app.data.program_requirements import all_program_requirements
    profiles = all_program_requirements()
    countries: dict[str, str] = {}
    for slug, p in profiles.items():
        if p.cultural_test_required is True:
            country = p.jurisdiction_code.split("-")[0]
            countries.setdefault(country, slug)
    return tuple(sorted(countries.items()))


def get_jurisdiction_national_status(jurisdiction_code: str) -> JurisdictionNationalStatus:
    """The one canonical lookup. Returns a real, non-fabricated
    determination for every country in the current canonical universe --
    AUTHORITY_UNRESOLVED_EXACT_PROPOSITION (never silently defaulted)
    when this pass did not research/confirm it."""
    code = jurisdiction_code.split("-")[0].upper()
    for rec in _CONFIRMED_SEPARATE_PATHWAY:
        if rec.jurisdiction_code == code:
            return rec
    for country, slug in _base_incentive_is_national_status_countries():
        if country == code:
            return JurisdictionNationalStatus(
                jurisdiction_code=code,
                status=STATUS_REGIME_CONFIRMED,
                regime_name=f"{slug}'s own cultural test (base-incentive-gating)",
                linked_program_slug=slug,
                base_program_slug=slug,
                pathway_type=BASE_INCENTIVE_REQUIRED,
                economic_consequence=CONSEQUENCE_IS_BASE_PROGRAM,
                consequence_detail=(
                    f"{slug}'s own cultural test IS the national/cultural status gate for this "
                    "incentive -- confirmed via program_requirements.py's existing primary/secondary "
                    "citation for this program (see WORLDWIDE_PROGRAM_QUALIFICATION_COMPLETION.md). "
                    "No separate national program exists in the current canonical universe to unlock."
                ),
                sources=(),
            )
    return JurisdictionNationalStatus(
        jurisdiction_code=code,
        status=STATUS_AUTHORITY_UNRESOLVED,
        exact_unresolved_propositions=(
            "NATIONAL_CULTURAL_STATUS_REGIME_EXISTENCE_UNCONFIRMED_BEYOND_BASE_INCENTIVE_CULTURAL_TEST_FIELD "
            f"-- {code}'s own served incentive(s) do not require a cultural test, but no primary-authority "
            "research was performed this pass to confirm whether a SEPARATE national/domestic-content "
            "certification regime exists (as it does for Canada, Australia, and New Zealand).",
        ),
    )
