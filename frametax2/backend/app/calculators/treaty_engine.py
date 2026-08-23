"""
treaty_engine.py — Phase E2: Treaty & Co-production eligibility engine.

Pure-Python, no DB access. Static treaty data mirrors migrations 0047-0049.

Evaluates:
  - bilateral treaty eligibility (majority/minority % thresholds)
  - multilateral treaty eligibility (Eurimages, European Convention, Ibermedia)
  - cultural-test requirements
  - spend-share requirements
  - producer-share requirements
  - unlocked incentive slugs per party
  - disqualification reasons
"""
from __future__ import annotations

#: OH-001 fix: included in canonical_evaluation._compute_fingerprint()
#: so a treaty/co-production data change invalidates cached served
#: evaluations. Bump on any material change.
# 1.1.0: LU Co-Pro Opportunity Trace fix -- added all_bilateral_treaties(),
# a new read accessor enabling candidate-pair (not just home-anchored)
# bilateral discovery. No treaty DATA changed; bumped because a served
# consumer's candidate SET changes as a direct result.
TREATY_ENGINE_VERSION = "1.1.0"

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class TreatyData:
    treaty_slug: str
    treaty_type: str          # bilateral | multilateral | european_convention | ibermedia | eurimages
    jurisdiction_a: str       # ISO alpha-2 of primary party (or "EU" for multilateral)
    jurisdiction_b: str | None
    majority_min_pct: float   # 0–100
    minority_min_pct: float
    minority_max_pct: float | None
    min_coproducer_countries: int
    cultural_test_required: bool
    majority_unlocks: list[str]   # incentive program slugs
    minority_unlocks: list[str]
    fund_unlocks: list[str]
    confidence_tier: str
    notes: str | None = None
    #: Final Consolidated Backend Correction + Global Structuring
    #: Intelligence Acceptance, Part 10/Gemini P0 pattern SP_004 (Non-
    #: Party Personnel Exception) — the real percentage of budget (or a
    #: specific key-creative allowance) THIS treaty's own article
    #: permits for non-party-country cast/crew without losing official
    #: co-production status, e.g. Canada-UK Treaty Art. 4. None (the
    #: default for every entry below) means genuinely unresolved — this
    #: specific treaty's own non-party-personnel clause has not yet been
    #: individually re-researched. NEVER generalize one treaty's real
    #: percentage to another; a None here must surface as
    #: AUTHORITY_UNRESOLVED, never silently as "no exception exists" or
    #: an invented default percentage.
    non_party_personnel_exception_pct: float | None = None
    non_party_personnel_exception_citation: str | None = None


@dataclass
class TreatyEligibilityResult:
    is_eligible: bool
    treaty: TreatyData | None
    majority_country: str
    minority_country: str | None
    majority_pct: float
    minority_pct: float
    passes_majority_min: bool
    passes_minority_min: bool
    passes_minority_max: bool
    cultural_test_required: bool
    min_countries_met: bool
    unlocked_majority_slugs: list[str] = field(default_factory=list)
    unlocked_minority_slugs: list[str] = field(default_factory=list)
    unlocked_fund_slugs: list[str] = field(default_factory=list)
    disqualification_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence_tier: str = "PARSED"


@dataclass
class MultilateralEligibilityResult:
    is_eligible: bool
    treaty: TreatyData | None
    co_producer_countries: list[str]
    country_pcts: dict[str, float]   # country_code → budget pct
    all_above_min: bool
    min_countries_met: bool
    all_are_members: bool
    non_member_countries: list[str]
    cultural_test_required: bool
    unlocked_fund_slugs: list[str] = field(default_factory=list)
    disqualification_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence_tier: str = "PARSED"


# ---------------------------------------------------------------------------
# Static treaty registry — mirrors migrations 0047/0048/0049
# ---------------------------------------------------------------------------

# Bilateral treaties: keyed by frozenset({country_a, country_b})
_BILATERAL: dict[frozenset, TreatyData] = {}

def _add_bilateral(
    slug: str,
    a: str,
    b: str,
    maj_min: float,
    min_min: float,
    min_max: float,
    cultural_test: bool,
    maj_unlocks: list[str],
    min_unlocks: list[str],
    fund_unlocks: list[str] | None = None,
    notes: str | None = None,
    tier: str = "PARSED",
) -> None:
    _BILATERAL[frozenset({a, b})] = TreatyData(
        treaty_slug=slug,
        treaty_type="bilateral",
        jurisdiction_a=a,
        jurisdiction_b=b,
        majority_min_pct=maj_min,
        minority_min_pct=min_min,
        minority_max_pct=min_max,
        min_coproducer_countries=2,
        cultural_test_required=cultural_test,
        majority_unlocks=maj_unlocks,
        minority_unlocks=min_unlocks,
        fund_unlocks=fund_unlocks or [],
        confidence_tier=tier,
        notes=notes,
    )


# UK bilateral treaties
_add_bilateral("uk-ca-bilateral",  "GB", "CA", 30, 20, 70, False,
               ["uk_avec"], ["ca_federal_cptc", "ca_cmf"])
_add_bilateral("uk-au-bilateral",  "GB", "AU", 20, 20, 80, False,
               ["uk_avec"], ["au_producer_offset"])
_add_bilateral("uk-fr-bilateral",  "GB", "FR", 30, 20, 70, True,
               ["uk_avec"], ["fr_tax_credit_cinema", "fr_cnc_production"])
_add_bilateral("uk-de-bilateral",  "GB", "DE", 30, 20, 70, False,
               ["uk_avec"], ["de_dfff"])
_add_bilateral("uk-nz-bilateral",  "GB", "NZ", 20, 20, 80, False,
               ["uk_avec"], ["nz_spgi"])
_add_bilateral("uk-za-bilateral",  "GB", "ZA", 20, 20, 80, False,
               ["uk_avec"], [])
_add_bilateral("uk-in-bilateral",  "GB", "IN", 20, 20, 80, False,
               ["uk_avec"], [])
_add_bilateral("uk-ie-bilateral",  "GB", "IE", 20, 20, 80, False,
               ["uk_avec"], ["ie_section_481"])

# Canada bilateral treaties
_add_bilateral("ca-fr-bilateral",  "CA", "FR", 30, 20, 70, False,
               ["ca_federal_cptc", "ca_cmf"], ["fr_tax_credit_cinema", "fr_cnc_production"],
               notes="QC majority can also access QPRDP")
_add_bilateral("ca-au-bilateral",  "CA", "AU", 20, 20, 80, False,
               ["ca_federal_cptc", "ca_cmf"], ["au_producer_offset"])
_add_bilateral("ca-de-bilateral",  "CA", "DE", 30, 20, 70, False,
               ["ca_federal_cptc", "ca_cmf"], ["de_dfff"])
_add_bilateral("ca-it-bilateral",  "CA", "IT", 30, 20, 70, False,
               ["ca_federal_cptc", "ca_cmf"], ["it_tax_credit_foreign"])
_add_bilateral("ca-es-bilateral",  "CA", "ES", 30, 20, 70, False,
               ["ca_federal_cptc", "ca_cmf"], [])
_add_bilateral("ca-za-bilateral",  "CA", "ZA", 20, 20, 80, False,
               ["ca_federal_cptc", "ca_cmf"], [])
_add_bilateral("ca-ie-bilateral",  "CA", "IE", 20, 20, 80, False,
               ["ca_federal_cptc", "ca_cmf"], ["ie_section_481"])
_add_bilateral("ca-nz-bilateral",  "CA", "NZ", 20, 20, 80, False,
               ["ca_federal_cptc", "ca_cmf"], ["nz_spgi"])
_add_bilateral("ca-cn-bilateral",  "CA", "CN", 30, 20, 70, False,
               ["ca_federal_cptc", "ca_cmf"], [],
               notes="Primary benefit for CN: quota exemption")
_add_bilateral("ca-ch-bilateral",  "CA", "CH", 30, 20, 70, False,
               ["ca_federal_cptc", "ca_cmf"], [])
_add_bilateral("ca-be-bilateral",  "CA", "BE", 30, 20, 70, False,
               ["ca_federal_cptc", "ca_cmf"], ["be_tax_shelter"])
_add_bilateral("ca-mx-bilateral",  "CA", "MX", 20, 20, 80, False,
               ["ca_federal_cptc", "ca_cmf"], [])

# Australia bilateral treaties
_add_bilateral("au-de-bilateral",  "AU", "DE", 20, 20, 80, False,
               ["au_producer_offset"], ["de_dfff"])
_add_bilateral("au-ie-bilateral",  "AU", "IE", 20, 20, 80, False,
               ["au_producer_offset"], ["ie_section_481"])
_add_bilateral("au-it-bilateral",  "AU", "IT", 20, 20, 80, False,
               ["au_producer_offset"], ["it_tax_credit_foreign"])
_add_bilateral("au-kr-bilateral",  "AU", "KR", 20, 20, 80, False,
               ["au_producer_offset"], [])

# France bilateral treaties
_add_bilateral("fr-de-bilateral",  "FR", "DE", 30, 20, 70, True,
               ["fr_tax_credit_cinema", "fr_cnc_production"], ["de_dfff"])
_add_bilateral("fr-be-bilateral",  "FR", "BE", 30, 20, 70, True,
               ["fr_tax_credit_cinema", "fr_cnc_production"], ["be_tax_shelter"])


# Multilateral treaties
_MULTILATERAL: dict[str, TreatyData] = {}

_MULTILATERAL["eurimages"] = TreatyData(
    treaty_slug="eurimages-multilateral",
    treaty_type="eurimages",
    jurisdiction_a="EU",
    jurisdiction_b=None,
    majority_min_pct=10.0,
    minority_min_pct=10.0,
    minority_max_pct=None,
    min_coproducer_countries=3,
    cultural_test_required=True,
    majority_unlocks=[],
    minority_unlocks=[],
    fund_unlocks=["eu_eurimages"],
    confidence_tier="PARSED",
    notes="Each co-producer independently accesses national incentives on their own spend.",
)

_MULTILATERAL["european_convention"] = TreatyData(
    treaty_slug="european-convention-coproduction",
    treaty_type="european_convention",
    jurisdiction_a="EU",
    jurisdiction_b=None,
    majority_min_pct=30.0,
    minority_min_pct=10.0,
    minority_max_pct=70.0,
    min_coproducer_countries=2,
    cultural_test_required=True,
    majority_unlocks=[],
    minority_unlocks=[],
    fund_unlocks=[],
    confidence_tier="PARSED",
    notes="Framework providing European certification enabling national incentive access.",
)

_MULTILATERAL["ibermedia"] = TreatyData(
    treaty_slug="ibermedia-multilateral",
    treaty_type="ibermedia",
    jurisdiction_a="ES",
    jurisdiction_b=None,
    majority_min_pct=20.0,
    minority_min_pct=10.0,
    minority_max_pct=None,
    min_coproducer_countries=2,
    cultural_test_required=True,
    majority_unlocks=[],
    minority_unlocks=[],
    fund_unlocks=["ibermedia_programme"],
    confidence_tier="PARSED",
)

# Eurimages member states (44)
_EURIMAGES_MEMBERS: frozenset[str] = frozenset({
    "AL", "AM", "AT", "AZ", "BE", "BA", "HR", "CY", "CZ", "DK",
    "EE", "FI", "FR", "GE", "DE", "GR", "HU", "IS", "IE", "IT",
    "LV", "LI", "LT", "LU", "MT", "MD", "ME", "NL", "MK", "NO",
    "PL", "PT", "RO", "SM", "RS", "SK", "SI", "ES", "SE", "CH",
    "TR", "UA", "GB", "VA",
})

# European Convention signatories (same as Eurimages for our purposes)
_EUROPEAN_CONVENTION_MEMBERS: frozenset[str] = _EURIMAGES_MEMBERS

# Ibermedia member states (21)
_IBERMEDIA_MEMBERS: frozenset[str] = frozenset({
    "AR", "BO", "BR", "CL", "CO", "CR", "CU", "DO", "EC", "SV",
    "GT", "HN", "MX", "NI", "PA", "PY", "PE", "PT", "ES", "UY", "VE",
})


# ---------------------------------------------------------------------------
# Bilateral eligibility evaluation
# ---------------------------------------------------------------------------

def get_bilateral_treaty(country_a: str, country_b: str) -> TreatyData | None:
    """Return TreatyData for a country pair, or None if no bilateral treaty exists."""
    return _BILATERAL.get(frozenset({country_a.upper(), country_b.upper()}))


def evaluate_bilateral_eligibility(
    majority_country: str,
    minority_country: str,
    majority_pct: float,
    minority_pct: float,
    cultural_test_passed: bool | None = None,
) -> TreatyEligibilityResult:
    """
    Evaluate whether a bilateral co-production arrangement qualifies under treaty.

    Parameters
    ----------
    majority_country      ISO alpha-2 of the majority co-producer's country
    minority_country      ISO alpha-2 of the minority co-producer's country
    majority_pct          Majority party's % share of total budget (0–100)
    minority_pct          Minority party's % share of total budget (0–100)
    cultural_test_passed  True/False/None — None means not assessed

    Returns
    -------
    TreatyEligibilityResult
    """
    mc = majority_country.upper()
    sc = minority_country.upper()

    treaty = get_bilateral_treaty(mc, sc)

    if treaty is None:
        return TreatyEligibilityResult(
            is_eligible=False,
            treaty=None,
            majority_country=mc,
            minority_country=sc,
            majority_pct=majority_pct,
            minority_pct=minority_pct,
            passes_majority_min=False,
            passes_minority_min=False,
            passes_minority_max=True,
            cultural_test_required=False,
            min_countries_met=False,
            disqualification_reasons=[
                f"No bilateral co-production treaty found between {mc} and {sc}."
            ],
        )

    reasons: list[str] = []
    warnings: list[str] = []

    # Determine which party is majority vs minority relative to the treaty
    # Treaty stores jurisdiction_a and jurisdiction_b — either can be majority
    passes_maj = majority_pct >= treaty.majority_min_pct
    passes_min = minority_pct >= treaty.minority_min_pct
    passes_max = (
        treaty.minority_max_pct is None
        or minority_pct <= treaty.minority_max_pct
    )

    if not passes_maj:
        reasons.append(
            f"Majority contribution {majority_pct:.1f}% < treaty minimum "
            f"{treaty.majority_min_pct:.1f}% ({treaty.treaty_slug})."
        )
    if not passes_min:
        reasons.append(
            f"Minority contribution {minority_pct:.1f}% < treaty minimum "
            f"{treaty.minority_min_pct:.1f}% ({treaty.treaty_slug})."
        )
    if not passes_max:
        reasons.append(
            f"Minority contribution {minority_pct:.1f}% > treaty maximum "
            f"{treaty.minority_max_pct:.1f}% ({treaty.treaty_slug})."
        )

    # Cultural test
    cultural_ok = True
    if treaty.cultural_test_required:
        if cultural_test_passed is False:
            cultural_ok = False
            reasons.append(
                f"Treaty {treaty.treaty_slug} requires cultural test — not passed."
            )
        elif cultural_test_passed is None:
            warnings.append(
                f"Treaty {treaty.treaty_slug} requires cultural test — result not provided."
            )

    # Determine which unlocks apply based on which country is majority
    # The treaty's jurisdiction_a is defined as the first signatory, but
    # either party can be majority — unlocks depend on actual majority role
    if treaty.jurisdiction_a == mc or treaty.jurisdiction_b == mc:
        maj_unlocks = treaty.majority_unlocks
        min_unlocks = treaty.minority_unlocks
    else:
        maj_unlocks = treaty.majority_unlocks
        min_unlocks = treaty.minority_unlocks

    is_eligible = passes_maj and passes_min and passes_max and cultural_ok

    return TreatyEligibilityResult(
        is_eligible=is_eligible,
        treaty=treaty,
        majority_country=mc,
        minority_country=sc,
        majority_pct=majority_pct,
        minority_pct=minority_pct,
        passes_majority_min=passes_maj,
        passes_minority_min=passes_min,
        passes_minority_max=passes_max,
        cultural_test_required=treaty.cultural_test_required,
        min_countries_met=True,
        unlocked_majority_slugs=maj_unlocks if is_eligible else [],
        unlocked_minority_slugs=min_unlocks if is_eligible else [],
        unlocked_fund_slugs=treaty.fund_unlocks if is_eligible else [],
        disqualification_reasons=reasons,
        warnings=warnings,
        confidence_tier=treaty.confidence_tier,
    )


# ---------------------------------------------------------------------------
# Multilateral eligibility evaluation
# ---------------------------------------------------------------------------

def is_eurimages_member(country: str) -> bool:
    return country.upper() in _EURIMAGES_MEMBERS


def is_ibermedia_member(country: str) -> bool:
    return country.upper() in _IBERMEDIA_MEMBERS


def is_european_convention_signatory(country: str) -> bool:
    return country.upper() in _EUROPEAN_CONVENTION_MEMBERS


def evaluate_eurimages_eligibility(
    co_producer_countries: list[str],
    country_pcts: dict[str, float],
) -> MultilateralEligibilityResult:
    """
    Evaluate eligibility for Eurimages co-production support.

    Parameters
    ----------
    co_producer_countries   List of ISO alpha-2 country codes of co-producers
    country_pcts            Dict mapping country_code → budget percentage (0–100)
    """
    treaty = _MULTILATERAL["eurimages"]
    countries = [c.upper() for c in co_producer_countries]
    pcts = {c.upper(): v for c, v in country_pcts.items()}

    reasons: list[str] = []
    warnings: list[str] = []

    non_members = [c for c in countries if c not in _EURIMAGES_MEMBERS]
    all_members = len(non_members) == 0
    if not all_members:
        reasons.append(
            f"Non-Eurimages members: {non_members}. "
            "All co-producers must be from Eurimages member states."
        )

    min_met = len(countries) >= treaty.min_coproducer_countries
    if not min_met:
        reasons.append(
            f"Eurimages requires minimum {treaty.min_coproducer_countries} co-producers; "
            f"only {len(countries)} provided."
        )

    all_above_min = all(
        pcts.get(c, 0) >= treaty.minority_min_pct
        for c in countries
    )
    if not all_above_min:
        below = [
            c for c in countries
            if pcts.get(c, 0) < treaty.minority_min_pct
        ]
        reasons.append(
            f"Co-producers below {treaty.minority_min_pct}% minimum: {below}. "
            "Each Eurimages co-producer must hold ≥10% of budget."
        )

    total_pct = sum(pcts.get(c, 0) for c in countries)
    if abs(total_pct - 100.0) > 1.0:
        warnings.append(
            f"Budget percentages sum to {total_pct:.1f}% (expected ~100%)."
        )

    warnings.append(
        "Cultural test required: project must demonstrate European cultural character."
    )

    is_eligible = all_members and min_met and all_above_min

    return MultilateralEligibilityResult(
        is_eligible=is_eligible,
        treaty=treaty,
        co_producer_countries=countries,
        country_pcts=pcts,
        all_above_min=all_above_min,
        min_countries_met=min_met,
        all_are_members=all_members,
        non_member_countries=non_members,
        cultural_test_required=True,
        unlocked_fund_slugs=treaty.fund_unlocks if is_eligible else [],
        disqualification_reasons=reasons,
        warnings=warnings,
        confidence_tier=treaty.confidence_tier,
    )


def evaluate_ibermedia_eligibility(
    co_producer_countries: list[str],
    country_pcts: dict[str, float],
) -> MultilateralEligibilityResult:
    """Evaluate eligibility for Ibermedia co-production support."""
    treaty = _MULTILATERAL["ibermedia"]
    countries = [c.upper() for c in co_producer_countries]
    pcts = {c.upper(): v for c, v in country_pcts.items()}

    reasons: list[str] = []
    warnings: list[str] = []

    non_members = [c for c in countries if c not in _IBERMEDIA_MEMBERS]
    all_members = len(non_members) == 0
    if not all_members:
        reasons.append(
            f"Non-Ibermedia members: {non_members}. "
            "All co-producers must be from Ibermedia member states."
        )

    min_met = len(countries) >= treaty.min_coproducer_countries
    if not min_met:
        reasons.append(
            f"Ibermedia requires minimum {treaty.min_coproducer_countries} co-producers."
        )

    # Majority must hold ≥20%, minority ≥10%
    sorted_pcts = sorted(
        [(c, pcts.get(c, 0)) for c in countries],
        key=lambda x: x[1],
        reverse=True,
    )
    majority_country, majority_pct_val = sorted_pcts[0] if sorted_pcts else ("?", 0)
    majority_ok = majority_pct_val >= treaty.majority_min_pct
    minority_ok = all(p >= treaty.minority_min_pct for _, p in sorted_pcts[1:])

    all_above_min = majority_ok and minority_ok
    if not majority_ok:
        reasons.append(
            f"Majority co-producer {majority_country} holds {majority_pct_val:.1f}% "
            f"< Ibermedia majority minimum {treaty.majority_min_pct:.1f}%."
        )
    if not minority_ok:
        below = [c for c, p in sorted_pcts[1:] if p < treaty.minority_min_pct]
        reasons.append(
            f"Minor co-producers below {treaty.minority_min_pct}% minimum: {below}."
        )

    warnings.append(
        "Cultural test required: project must reflect Ibero-American cultural identity."
    )

    is_eligible = all_members and min_met and all_above_min

    return MultilateralEligibilityResult(
        is_eligible=is_eligible,
        treaty=treaty,
        co_producer_countries=countries,
        country_pcts=pcts,
        all_above_min=all_above_min,
        min_countries_met=min_met,
        all_are_members=all_members,
        non_member_countries=non_members,
        cultural_test_required=True,
        unlocked_fund_slugs=treaty.fund_unlocks if is_eligible else [],
        disqualification_reasons=reasons,
        warnings=warnings,
        confidence_tier=treaty.confidence_tier,
    )


def evaluate_european_convention_eligibility(
    co_producer_countries: list[str],
    country_pcts: dict[str, float],
) -> MultilateralEligibilityResult:
    """Evaluate eligibility under the European Convention on Cinematographic Co-production."""
    treaty = _MULTILATERAL["european_convention"]
    countries = [c.upper() for c in co_producer_countries]
    pcts = {c.upper(): v for c, v in country_pcts.items()}

    reasons: list[str] = []
    warnings: list[str] = []

    non_members = [c for c in countries if c not in _EUROPEAN_CONVENTION_MEMBERS]
    all_members = len(non_members) == 0
    if not all_members:
        reasons.append(f"Non-signatories to European Convention: {non_members}.")

    min_met = len(countries) >= treaty.min_coproducer_countries
    if not min_met:
        reasons.append(
            f"European Convention requires minimum {treaty.min_coproducer_countries} co-producers."
        )

    sorted_pcts = sorted(
        [(c, pcts.get(c, 0)) for c in countries],
        key=lambda x: x[1],
        reverse=True,
    )
    majority_pct_val = sorted_pcts[0][1] if sorted_pcts else 0
    passes_maj = majority_pct_val >= treaty.majority_min_pct
    all_above_min = passes_maj and all(p >= treaty.minority_min_pct for _, p in sorted_pcts[1:])
    if not passes_maj:
        reasons.append(
            f"Majority contribution {majority_pct_val:.1f}% < Convention minimum {treaty.majority_min_pct:.1f}%."
        )
    below_min = [c for c, p in sorted_pcts[1:] if p < treaty.minority_min_pct]
    if below_min:
        reasons.append(
            f"Minor co-producers below {treaty.minority_min_pct}% minimum: {below_min}."
        )
        all_above_min = False

    # Max check for bilateral: majority cannot exceed 70%
    if len(countries) == 2 and treaty.minority_max_pct and majority_pct_val > treaty.minority_max_pct:
        reasons.append(
            f"Majority contribution {majority_pct_val:.1f}% > Convention bilateral maximum "
            f"{treaty.minority_max_pct:.1f}%."
        )
        all_above_min = False

    warnings.append(
        "Cultural test required: project must demonstrate European cultural character."
    )

    is_eligible = all_members and min_met and all_above_min

    return MultilateralEligibilityResult(
        is_eligible=is_eligible,
        treaty=treaty,
        co_producer_countries=countries,
        country_pcts=pcts,
        all_above_min=all_above_min,
        min_countries_met=min_met,
        all_are_members=all_members,
        non_member_countries=non_members,
        cultural_test_required=True,
        unlocked_fund_slugs=[],
        disqualification_reasons=reasons,
        warnings=warnings,
        confidence_tier=treaty.confidence_tier,
    )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def get_available_bilateral_treaties(country: str) -> list[TreatyData]:
    """Return all bilateral treaties available to a given country."""
    c = country.upper()
    return [
        td for key, td in _BILATERAL.items()
        if c in key
    ]


def all_bilateral_treaties() -> list[TreatyData]:
    """LU Co-Pro Opportunity Trace fix: every registered bilateral treaty,
    unfiltered by any one country. Lets a caller discover a real treaty
    between two CANDIDATE jurisdictions (e.g. two creative-personnel
    nationalities) without requiring the production's own current/service
    jurisdiction to be one of the two parties -- see
    canonical_treaty_bridge.find_bilateral_treaty_pairs_among_candidates,
    the actual consumer of this accessor."""
    return list(_BILATERAL.values())


def get_unlocked_slugs_for_country(
    country: str,
    treaty: TreatyData,
    is_majority: bool,
) -> list[str]:
    """Return incentive slugs unlocked for a country given its role (majority/minority)."""
    return treaty.majority_unlocks if is_majority else treaty.minority_unlocks


def validate_spend_allocation(
    total_budget: float,
    majority_spend: float,
    minority_spend: float,
    treaty: TreatyData,
) -> tuple[bool, list[str]]:
    """
    Validate that spend allocation meets treaty thresholds.

    Returns (passes, list_of_violations).
    """
    violations: list[str] = []
    if total_budget <= 0:
        return False, ["Total budget must be > 0."]

    maj_pct = (majority_spend / total_budget) * 100
    min_pct = (minority_spend / total_budget) * 100

    if maj_pct < treaty.majority_min_pct:
        violations.append(
            f"Majority spend {maj_pct:.1f}% of budget < required {treaty.majority_min_pct:.1f}%."
        )
    if min_pct < treaty.minority_min_pct:
        violations.append(
            f"Minority spend {min_pct:.1f}% of budget < required {treaty.minority_min_pct:.1f}%."
        )
    if treaty.minority_max_pct and min_pct > treaty.minority_max_pct:
        violations.append(
            f"Minority spend {min_pct:.1f}% of budget > maximum {treaty.minority_max_pct:.1f}%."
        )

    return len(violations) == 0, violations
