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

NATIONAL_CULTURAL_STATUS_VERSION = "1.2.0"
# 1.1.0 -- Final Worldwide Qualification/Cultural/Co-production Completion:
# adds Queue C (official co-production COVERAGE, distinct from national/
# cultural STATUS) -- CoproductionCoverageStatus / get_coproduction_
# coverage_status(), covering the 13 countries treaty_engine.py's own
# registry had no bilateral/multilateral entry for. Real country-level
# partner facts recovered via targeted primary/secondary research this
# pass; genuinely missing bilateral TERMS (contribution %, roles) are
# NOT fabricated -- only existence is confirmed where cited.
# 1.2.0 -- Continuation from checkpoint adc5cba (2026-08-19): Israel
# added to _CONFIRMED_SEPARATE_PATHWAY (Film Law 'Israeli film'
# definition). CoproductionCoverageStatus gains a new additive field,
# partner_contribution_terms (dict[str, str]), for Queue D's explicit
# requirement: a confirmed route must never be silently treated as
# though it doesn't exist merely because one operational term (usually
# the exact contribution percentage) is unknown -- ROUTE EXISTS +
# SPECIFIC TERM UNRESOLVED is now a first-class, disclosed state, never
# silent omission or fabrication. Populated for KR (5 partners -- real
# Canada floor found via Telefilm Canada, 4 others explicitly fail
# closed), JP-IT, and PH-FR. Taiwan gains its first confirmed
# co-production route (New Zealand, via the real ANZTEC treaty's
# dedicated Film and Television Co-Production chapter) -- previously
# AUTHORITY_UNRESOLVED, now COPRO_ROUTE_EXISTS. AE/SG/TW national-status
# hard-blocker documentation upgraded with additional real, cited
# research (still genuinely unresolved, now more deeply researched).

# ── Queue C: official co-production COVERAGE terminal states ────────────
COPRO_ROUTE_EXISTS = "OFFICIAL_COPRO_ROUTE_EXISTS"
COPRO_MULTILATERAL_EXISTS = "OFFICIAL_MULTILATERAL_COVERAGE_EXISTS"
COPRO_NO_RELEVANT_ROUTE = "NO_RELEVANT_OFFICIAL_COPRO_ROUTE_CONFIRMED"
COPRO_AUTHORITY_UNRESOLVED = "AUTHORITY_UNRESOLVED_EXACT_PROPOSITION"

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
CONSEQUENCE_ENABLES_OFFICIAL_COPRODUCTION_ROUTE = "ENABLES_OFFICIAL_COPRODUCTION_ROUTE"

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
        legal_basis="Income Tax Act (Canada) s. 125.4 (CPTC) vs s. 125.5 (PSTC)",
        linked_program_slug="ca_federal_cptc",
        base_program_slug="ca_federal_pstc",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        # Task 5 correction (2026-08-19): CPTC and PSTC are legally TWO
        # SEPARATE programs under different Income Tax Act sections --
        # different certificates, different applications, different
        # eligible-expenditure bases (CPTC: all Canadian labour; PSTC:
        # Canadian labour on service productions) -- a production claims
        # ONE OR THE OTHER, never a rate bump on one shared program.
        # Previously misclassified UNLOCKS_ENHANCED_RATE (implying a
        # single program with a floor/ceiling, like uk_avec's structure)
        # -- corrected to UNLOCKS_SEPARATE_INCENTIVE, the same real
        # relationship as Australia's Producer Offset vs Location Offset.
        economic_consequence=CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE,
        consequence_detail="CPTC (s.125.4) and PSTC (s.125.5) are two separate federal programs, not one "
                            "program with an uplifted rate -- CPTC 25% of qualified Canadian labour vs "
                            "PSTC 16%, confirmed via canada.ca (primary) and corroborated by "
                            "hellodarwin.com/Saturation.io/truenorthtaxes.ca.",
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
            "https://vitrina.ai/blog/official-co-production-treaties-guide/",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="JP",
        status=STATUS_NO_RELEVANT_REGIME_CONFIRMED,
        regime_name=None,
        administering_authority=None,
        legal_basis=None,
        linked_program_slug=None,
        base_program_slug="jp_vipo_location_incentive",
        pathway_type=PATHWAY_NO_ECONOMIC_DIFFERENCE,
        economic_consequence=CONSEQUENCE_NO_INCREMENTAL_BENEFIT,
        consequence_detail="Japan's METI/VIPO/Japan Film Commission incentive (launched 2023, up to 50% "
                            "rebate) is a single, unified scheme for international productions -- multiple "
                            "independent trade sources (Deadline, Screen, Variety) describe only this one "
                            "program, with no separate 'Japanese content' certification or domestic-status "
                            "regime found.",
        sources=(
            "https://deadline.com/2023/09/japan-incentive-program-offshore-production-vipo-meti-1235542659/",
            "https://www.vipo.or.jp/en/location-project/",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="NL",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Dutch Film Fund / HBF (Holland Film Meeting) national creative-element requirement",
        administering_authority="Nederlands Filmfonds (Dutch Film Fund)",
        legal_basis=None,
        linked_program_slug="nl_hbf",
        base_program_slug="nl_film_production_incentive",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        economic_consequence=CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE,
        consequence_detail="Recovered from EXISTING internal data (cultural_qualification_model.py already "
                            "carries real nl_hbf director/writer/producer NationalityRequirement rows -- "
                            "Task 4 discipline, not re-researched this pass), distinct from "
                            "nl_film_production_incentive's own confirmed no-cultural-test service pathway.",
        sources=(),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="SE",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Sweden Göteborg Fund (regional/national creative-element requirement)",
        administering_authority="Göteborg Film Fund",
        legal_basis=None,
        linked_program_slug="se_goteborg_fund",
        base_program_slug="se_production_rebate",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        economic_consequence=CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE,
        consequence_detail="Recovered from EXISTING internal data (cultural_qualification_model.py already "
                            "carries real se_goteborg_fund director/writer/producer NationalityRequirement "
                            "rows -- Task 4 discipline, not re-researched this pass), distinct from "
                            "se_production_rebate's own confirmed no-cultural-test service pathway.",
        sources=(),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="KR",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Korean national-film qualification (corporate registration + creative/financial "
                     "contribution) via official co-production treaty framework / KOFIC Co-production Fund",
        administering_authority="Korean Film Council (KOFIC)",
        legal_basis=None,
        linked_program_slug=None,  # KOFIC Co-production Fund is not itself a program_requirements.py record this pass
        base_program_slug="kr_kofic_location_incentive",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        economic_consequence=CONSEQUENCE_ENABLES_OFFICIAL_COPRODUCTION_ROUTE,
        consequence_detail="Korea bases film nationality on corporate registration plus creative/"
                            "financial contribution for its OWN public-support schemes (distinct from "
                            "kr_kofic_location_incentive, the confirmed no-personnel-cultural-test "
                            "foreign-production rebate). KOFIC administers a real, separate Co-production "
                            "Fund (koreanfilm.or.kr/eng/coProduction/coProdFund.jsp) for productions "
                            "qualifying under Korea's own real co-production treaty framework.",
        coproduction_relationship="Confirmed via KOFIC's own official treaty list (koreanfilm.or.kr): "
                                   "real bilateral agreements with Canada, UK, Singapore, New Zealand, "
                                   "France (plus China/India/EU outside the current 49-country universe) "
                                   "-- see CoproductionCoverageStatus for KR.",
        sources=(
            "https://www.koreanfilm.or.kr/eng/coProduction/coProdFund.jsp",
            "https://www.koreanfilm.or.kr/eng/coProduction/treaties.jsp",
            "https://stephenfollows.com/p/how-film-nationality-is-determined",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="PH",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Philippines official co-production treaty framework (FDCP)",
        administering_authority="Film Development Council of the Philippines (FDCP)",
        legal_basis=None,
        linked_program_slug=None,
        base_program_slug=None,  # no service-only PH program in the current 71-program universe
        pathway_type=CONSEQUENCE_ENABLES_OFFICIAL_COPRODUCTION_ROUTE,
        economic_consequence=CONSEQUENCE_ENABLES_OFFICIAL_COPRODUCTION_ROUTE,
        consequence_detail="FDCP signed a real film co-production treaty with France (confirmed via "
                            "Philippine news reporting of the official signing) and operates an "
                            "International Co-Production Fund (ICOF) for qualifying Filipino/foreign "
                            "co-productions -- a real, separate national/co-production pathway; no "
                            "service-only Philippine program exists in the current 71-program universe "
                            "to contrast it against.",
        coproduction_relationship="FDCP-France co-production treaty confirmed; ICOF is the real, cited "
                                   "national fund unlocked by treaty co-production status.",
        sources=(
            "https://www.sunstar.com.ph/davao/feature/fdcp-france-sign-film-co-production-treaty",
            "https://filmphilippines.com/co-production-treaty",
            "https://fdcp.ph/programs/film-philippines-office/international-co-production-fund",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="ZA",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="South African Film Criteria (points test: production/post-production location, "
                     "national work, official co-production status)",
        administering_authority="Department of Trade, Industry and Competition (DTIC) / National Film "
                                 "and Video Foundation (NFVF)",
        legal_basis=None,
        linked_program_slug="za_dtic_foreign_film",  # same program, genuinely uplifted -- not a separate program
        base_program_slug="za_dtic_foreign_film",
        pathway_type=PATHWAY_CULTURAL_UPLIFT,
        # A GENUINE rate uplift (contrast with the corrected Canada case,
        # which is NOT an uplift) -- the SAME rebate program's rate rises
        # from a base tier to a higher tier for national work/official
        # co-production, per a real points-based "South African Film
        # Criteria" test.
        economic_consequence=CONSEQUENCE_UNLOCKS_UPLIFT,
        consequence_detail="Confirmed via NFVF/DTIC sources: the South African production rebate is 20% "
                            "base, rising to 35% of eligible SA expenses 'for a national work or an "
                            "official co-production' -- a real, quantified 15pp UPLIFT on the SAME "
                            "za_dtic_foreign_film program (genuinely different from Canada's CPTC/PSTC, "
                            "which are two separate programs, not an uplift on one).",
        coproduction_relationship="Official co-production status is an explicit ALTERNATIVE route to "
                                   "the points test for reaching the 35% uplifted rate.",
        sources=(
            "https://www.nfvf.co.za/incentives/",
            "https://filmcapetown.com/incentives/",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="EE",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Estonian creative-staff residency rate tiers (Film Estonia rebate)",
        administering_authority="Film Estonia",
        legal_basis=None,
        linked_program_slug="ee_film_estonia_rebate",
        base_program_slug="ee_film_estonia_rebate",
        pathway_type=PATHWAY_CULTURAL_UPLIFT,
        economic_consequence=CONSEQUENCE_UNLOCKS_UPLIFT,
        consequence_detail="Confirmed via filmestonia.eu: support intensity is 30% if at least 2 "
                            "creative employees are Estonian tax residents, or 25% if at least 1 is -- "
                            "a real, quantified rate tier gated on personnel residency within the SAME "
                            "program, distinct from the base rebate percentage. This is a personnel-"
                            "residency uplift, a materially different real mechanism from Canada's "
                            "separate-program relationship or South Africa's national-work uplift.",
        sources=("https://filmestonia.eu/film-estonia-funding/guidelines-and-how-to-apply/",),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="ES",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Spanish Nationality Certificate + Cultural Character Certificate (ICAA, Art. 36.1 LIS)",
        administering_authority="Instituto de la Cinematografia y de las Artes Audiovisuales (ICAA) / Ministerio de Cultura",
        legal_basis="Ley del Impuesto sobre Sociedades (LIS), Art. 36.1 (Spanish productions) vs Art. 36.2 (foreign productions)",
        linked_program_slug=None,  # the Spanish-nationality Art. 36.1 credit is not itself a program_requirements.py record this pass
        base_program_slug="es_tax_credit_foreign",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        economic_consequence=CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE,
        consequence_detail="Confirmed via the official Spanish Ministry of Culture/ICAA page: Art. 36.1 "
                            "(Spanish productions, requires BOTH a Spanish nationality certificate AND a "
                            "separate cultural character certificate from ICAA) is a genuinely SEPARATE "
                            "tax framework from Art. 36.2 (es_tax_credit_foreign, the confirmed no-"
                            "cultural-test foreign-production rebate) -- same real relationship as "
                            "Canada CPTC/PSTC and Australia Producer Offset/Location Offset.",
        sources=(
            "https://www.cultura.gob.es/en/cultura/areas/cine/industria-cine/coproducir-espa/incentivos-fiscales.html",
            "https://www.cultura.gob.es/en/cultura/areas/cine/industria-cine/certificado-nacionalidad-espanola.html",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="CH",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="PICS (Production Incentive Switzerland) official Swiss co-production gate",
        administering_authority="Federal Office of Culture (FOC), Berne",
        legal_basis=None,
        linked_program_slug="ch_pics_national_rebate",
        base_program_slug="ch_pics_national_rebate",
        pathway_type=BASE_INCENTIVE_REQUIRED,
        economic_consequence=CONSEQUENCE_IS_BASE_PROGRAM,
        consequence_detail="Switzerland's own canonical program (ch_pics_national_rebate) already "
                            "correctly records treaty_or_official_coproduction_required=True -- PICS is "
                            "a co-production instrument, not a general service rebate, and can only be "
                            "claimed by an independent Swiss production company on a project recognized "
                            "as an official Swiss co-production. This is a materially DIFFERENT model "
                            "from a personnel-points cultural test: qualification runs on official "
                            "co-production STATUS, not a nationality point table. Cross-country service-"
                            "only rebates exist only at the CANTONAL level (Geneva, Neuchatel, Locarno "
                            "region) -- none are in the current 71-program canonical universe.",
        coproduction_relationship="PICS eligibility IS official-co-production status -- the clearest "
                                   "real example in the current universe of ENABLES_OFFICIAL_COPRODUCTION_"
                                   "ROUTE as the qualification mechanism itself, not a secondary benefit.",
        sources=(
            "https://www.swissinfo.ch/eng/culture/small-country-deep-pockets-how-to-make-and-fund-films-in-switzerland/79771691",
            "https://www.mediadesk.ch/a-propos-coproducing-en/",
        ),
        retrieved_date="2026-08-19",
    ),
    JurisdictionNationalStatus(
        jurisdiction_code="IL",
        status=STATUS_REGIME_CONFIRMED,
        regime_name="Israeli Film Law definition of an 'Israeli film' (Israel Film Fund domestic support)",
        administering_authority="Israel Film Fund (Kranot HaKolnoa); Israel Ministry of Culture and Sport",
        legal_basis="Israeli Film Law (Chok HaKolnoa) and its Regulations",
        linked_program_slug=None,  # Israel Film Fund's domestic support scheme is not yet a program_requirements.py record in the current 71-program universe
        base_program_slug="il_foreign_production_fund",
        pathway_type=PATHWAY_DOMESTIC_NATIONAL,
        economic_consequence=CONSEQUENCE_UNLOCKS_DOMESTIC_PROGRAM,
        consequence_detail="Continuation pass 2026-08-19 (Worldwide Program Qualification Completion, "
                            "Queue A): the Israel Film Fund's own eligibility criteria require a "
                            "feature script (>=70 minutes, or >=60 for animation) that 'complies with "
                            "the criteria for defining an Israeli film in the Film Law and the "
                            "Regulations thereunder' -- a real, distinct national-content legal "
                            "definition, separate from il_foreign_production_fund (the confirmed "
                            "no-cultural-test foreign/international production incentive, a different, "
                            "newer incentive-law framework). Same real structural pattern as Canada "
                            "CPTC/PSTC and Spain Art. 36.1/36.2 -- a domestic national-content "
                            "certification unlocking access to Israel's own domestic film funds "
                            "(Israel Film Fund, Rabinovich Foundation/Israel Cinema Project, Gesher "
                            "Multicultural Film Fund, Makor Foundation), materially distinct from the "
                            "foreign-production service rebate.",
        coproduction_relationship="Israel's own confirmed bilateral co-production treaties (France "
                                   "1970, Germany, Italy, UK, Australia, New Zealand, Sweden -- see "
                                   "CoproductionCoverageStatus for IL) separately confer national "
                                   "treatment for co-produced works.",
        sources=(
            "https://www.filmfund.org.il/Upload/Media/Tinymce/Files/IFF%20en2024.pdf",
            "https://izzy.streamisrael.tv/inside-the-6-film-funds-putting-israeli-entertainment-on-the-map/",
        ),
        exact_unresolved_propositions=(
            "IL_DOMESTIC_FUND_POINT_STRUCTURE_UNCONFIRMED -- the Film Law's own definitional criteria "
            "for 'Israeli film' (personnel/language/subject-matter thresholds) were not independently "
            "read from the statute itself this pass; the domestic funds are also not yet program_"
            "requirements.py records, so no exact percentage/rate is asserted.",
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
    default_proposition = (
        "NATIONAL_CULTURAL_STATUS_REGIME_EXISTENCE_UNCONFIRMED_BEYOND_BASE_INCENTIVE_CULTURAL_TEST_FIELD "
        f"-- {code}'s own served incentive(s) do not require a cultural test, but no primary-authority "
        "research was performed this pass to confirm whether a SEPARATE national/domestic-content "
        "certification regime exists (as it does for Canada, Australia, and New Zealand)."
    )
    return JurisdictionNationalStatus(
        jurisdiction_code=code,
        status=STATUS_AUTHORITY_UNRESOLVED,
        exact_unresolved_propositions=_UNRESOLVED_PROPOSITION_OVERRIDES.get(code, (default_proposition,)),
    )


#: Countries where this pass's research produced a real, more specific
#: lead than the generic default proposition, but not enough to reach a
#: confident CONFIRMED/NO_RELEVANT determination -- disclosed exactly,
#: never silently upgraded to a confident claim.
_UNRESOLVED_PROPOSITION_OVERRIDES: dict[str, tuple[str, ...]] = {
    "MA": (
        "MOROCCO_CCM_NATIONAL_FILM_STATUS_VS_MA_CCM_REBATE_RELATIONSHIP_UNCONFIRMED -- this pass "
        "confirmed a real UK-Morocco bilateral co-production treaty (via UK's own listed treaty "
        "partners), which would confer national treatment for co-produced works, but could not confirm "
        "whether the Centre Cinematographique Marocain (CCM) also operates a separate domestic/national "
        "certification distinct from ma_ccm_rebate (the confirmed no-cultural-test rebate). CCM's own "
        "treaty-list and domestic-fund pages were not independently fetched this pass. Requires: CCM's "
        "own official guidelines (typically published in French/Arabic).",
    ),
    "SG": (
        "SINGAPORE_IMDA_NATIONAL_CONTENT_CLASSIFICATION_VS_SG_MADE_WITH_SINGAPORE_RELATIONSHIP_UNCONFIRMED "
        "-- this pass confirmed a real Korea-Singapore FTA cultural-cooperation co-production route, but "
        "could not confirm whether Singapore's Infocomm Media Development Authority (IMDA) also "
        "operates a separate 'Singapore content' classification/fund distinct from "
        "sg_made_with_singapore_rebate (the confirmed no-cultural-test program). Continuation pass "
        "2026-08-19: two real, distinct IMDA mechanisms were investigated and both RULED OUT as the "
        "match. (1) The New Talent Feature Grant (NTFG) is real and IMDA-administered, but is an "
        "INDIVIDUAL grant restricted to Singapore citizens/PRs directing their first or second feature "
        "(up to S$250,000), not a company-facing national-content certification comparable to CAVCO/"
        "SAC/ICAA -- too structurally different to encode as the same CONFIRMED_SEPARATE_PATHWAY "
        "pattern without overclaiming the match. (2) IMDA's 'Content Standards and Classification' "
        "system was also checked and confirmed to be a censorship/age-rating framework (Films Act, "
        "Broadcasting Act) for public exhibition, not a funding-eligibility cultural test. Neither is "
        "the right mechanism. IMDA's own domestic-content FUNDING criteria pages (as opposed to talent "
        "grants or classification) were still not independently located this pass.",
    ),
    "TH": (
        "THAILAND_SEPARATE_NATIONAL_FUND_VS_TH_BOI_INCENTIVE_RELATIONSHIP_UNCONFIRMED -- Film Thailand's "
        "own page (filmthailand.org, confirmed primary for the co-production-coverage question -- "
        "Thailand has NO official co-production treaties) does not separately address whether a "
        "domestic/national Thai-content fund exists distinct from th_boi_incentive (the confirmed "
        "no-cultural-test BOI incentive). Requires: Thailand Film Office / Department of Tourism's own "
        "domestic-fund criteria, not located at the depth searched this pass.",
    ),
    "TW": (
        "TAIWAN_TAICCA_OFFICIAL_COPRODUCTION_TREATY_VS_FUNDING_SCHEME_DISTINCTION_UNCONFIRMED -- this "
        "pass found TAICCA (Taiwan Creative Content Agency) operates co-FINANCING schemes (e.g. TICP "
        "2.0) with international partners including Japan, but could not confirm whether these rise to "
        "the level of an OFFICIAL GOVERNMENT co-production TREATY (conferring national treatment) as "
        "opposed to a co-funding/investment program -- a real, disclosed ambiguity, not a confident "
        "finding either way. Sources checked: Screen Global Production, Deadline, TAICCA's own English-"
        "language press materials. Requires: TAICCA's own treaty/agreement register (not located in "
        "English at the depth searched). Continuation pass 2026-08-19: the France relationship "
        "specifically was checked and CONFIRMED NOT to be a formal treaty -- Deadline and TAICCA's own "
        "site both directly quote/confirm the CNC-TAICCA agreement (signed November 2023, TCCF) as a "
        "'memorandum of understanding designing joint priorities for...cooperation', explicitly NOT a "
        "co-production treaty with national-treatment or contribution-percentage terms. This "
        "corroborates, for one concrete named partner, the ambiguity already flagged for TAICCA's "
        "arrangements generally -- MOU-level industry cooperation, not confirmed treaty status, "
        "consistent with Taiwan's unusual formal-treaty-capacity constraints internationally.",
    ),
    "AE": (
        "UAE_TWOFOUR54_OFFICIAL_GOVERNMENT_TREATY_VS_INDUSTRY_COOPERATION_UNCONFIRMED -- this pass found "
        "real evidence of INDUSTRY-LEVEL cooperation between twofour54 (Abu Dhabi), the Doha Film "
        "Institute, and Dubai International Film Festival (described as the 'Gulf industrial axis') and "
        "individual co-produced projects, but no evidence of a formal GOVERNMENT-TO-GOVERNMENT co-"
        "production treaty. Sources checked: Screen Daily, GCC Business News, twofour54's own site, "
        "UAE Embassy news page. Requires: UAE Ministry of Culture's own treaty register, not located in "
        "English at the depth searched this pass.",
    ),
    "QA": (
        "QATAR_DOHA_FILM_INSTITUTE_OFFICIAL_TREATY_VS_INDUSTRY_COOPERATION_UNCONFIRMED -- same finding "
        "as UAE: real regional industry cooperation (Doha Film Institute as part of the 'Gulf industrial "
        "axis') confirmed, but no formal government co-production treaty found. Qatar's OWN new "
        "production-incentive program structure (up to 25% of spend may occur in neighbouring Arab "
        "countries while still qualifying) was found but not fully characterized as a separate national-"
        "status regime distinct from a service incentive. Sources checked: The National, Variety, "
        "Cineuropa. Requires: Doha Film Institute's own official program guidelines, not located at the "
        "depth searched this pass.",
    ),
    "SA": (
        "SAUDI_ARABIA_OFFICIAL_TREATY_AND_NATIONAL_FUND_UNCONFIRMED -- Saudi Arabia appears in industry-"
        "cooperation reporting (Gulf industrial axis, individual co-produced projects with Saudi "
        "producers) but this pass found no confirmation of either a formal government co-production "
        "treaty or a separate national-content certification distinct from sa_film_commission_rebate "
        "(the confirmed no-cultural-test program). Sources checked: Screen Daily, GCC Business News. "
        "Requires: Saudi Film Commission's own official criteria, not located in English at the depth "
        "searched this pass.",
    ),
    "FJ": (
        "FIJI_OFFICIAL_TREATY_AND_NATIONAL_FUND_UNCONFIRMED -- no evidence found this pass of either an "
        "official Fiji co-production treaty or a separate domestic-content fund distinct from "
        "fj_film_rebate (already AUTHORITY_UNRESOLVED at the program-qualification level for its own "
        "cultural-test applicability -- see WORLDWIDE_PROGRAM_QUALIFICATION_COMPLETION.md). Sources "
        "checked: film-fiji.com, Hoodlum, Entertainment Partners. Requires: Fiji Film Authority's own "
        "treaty register, not located this pass.",
    ),
    "MU": (
        "MAURITIUS_OFFICIAL_TREATY_AND_SEPARATE_NATIONAL_FUND_UNCONFIRMED -- consistent with the "
        "program-level residual already disclosed for mu_edb_incentive (2 sessions prior): the only "
        "specific national/cultural claims found for Mauritius (a 90%-filming condition, a dialogue-"
        "mention/logo/testimonial condition) were EITHER already investigated and REJECTED by a prior "
        "cross-verification (the 90% claim, National Assembly Hansard 14 May 2019) OR sourced only to "
        "non-government production-services sites. A 2013-era source describes co-production treaties "
        "with UK/France/South Africa/India as PLANNED, never confirmed signed. EDB Mauritius's own "
        "'Bilateral Agreements' page (edbmauritius.org/bilateral-agreements) appeared in search results "
        "but was not independently fetched this pass. Requires: direct confirmation from EDB Mauritius "
        "or the Mauritius Film Development Corporation of current treaty status.",
    ),
    "CL": (
        "CHILE_CORFO_NATIONAL_STATUS_VS_CL_CORFO_INCENTIVE_RELATIONSHIP_UNCONFIRMED -- Chile is a "
        "confirmed real Ibermedia member (see CoproductionCoverageStatus, resolved via treaty_engine.py's "
        "existing membership data), but this pass did not separately research whether CORFO (Chile's "
        "national economic development agency, administering cl_corfo_incentive) also operates a "
        "separate domestic/national Chilean-content certification. No search performed this pass -- "
        "genuinely not yet attempted, not merely inconclusive.",
    ),
    "IS": (
        "ICELAND_SEPARATE_NATIONAL_FUND_VS_RSK_REBATE_RELATIONSHIP_UNCONFIRMED -- this pass found "
        "Iceland's real rebate structure (25% base / 35% for large productions and children's content) "
        "but this is a PRODUCTION-SCALE/GENRE tier, not evidence of a personnel/cultural national-status "
        "gate distinct from the confirmed program. No separate Icelandic national-content fund "
        "confirmed. Sources checked: filminiceland.com, filmincentive.com. Requires: Iceland Film "
        "Centre's own domestic-fund criteria, not located at the depth searched this pass.",
    ),
    "RO": (
        "ROMANIA_SEPARATE_NATIONAL_FUND_VS_OFIC_REBATE_RELATIONSHIP_UNCONFIRMED -- this pass confirmed "
        "Romania's real OFIC cash-rebate structure (30% of eligible local spend, Ministry of Culture) "
        "but found no separate national/cultural-content certification distinct from it. Romania is a "
        "confirmed real Eurimages member (resolved for co-production coverage via treaty_engine.py's "
        "existing membership data). Sources checked: general film-incentive aggregators, not OFIC's own "
        "official guidelines directly.",
    ),
    "RS": (
        "SERBIA_SEPARATE_NATIONAL_FUND_VS_RS_FILM_COMMISSION_REBATE_RELATIONSHIP_UNCONFIRMED -- no "
        "search performed this pass for Serbia specifically; genuinely not yet attempted. Serbia is a "
        "confirmed real Eurimages member (resolved for co-production coverage via treaty_engine.py's "
        "existing membership data).",
    ),
    "MX": (
        "MEXICO_EFICINE_ARTICLE_226_VS_MX_FEDERAL_FILM_INCENTIVE_RELATIONSHIP_UNCONFIRMED -- EFICINE/"
        "Article 226 (Ley de Estimulo Fiscal, coordinated by IMCINE/SHCP) is a REAL, separate fiscal "
        "incentive for Mexican film investment, structurally distinct from mx_federal_film_incentive_2026 "
        "(the confirmed no-cultural-test service pathway) -- but this pass could not confirm EFICINE's "
        "exact eligibility criteria (Mexican-content/personnel requirements) or its own program identity "
        "with sufficient confidence to encode as CONFIRMED. Sources checked: unesco.org policy monitoring "
        "platform, fisherbroyles.com, redsharknews.com.",
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# Queue C — Official Co-production COVERAGE (distinct from national/
# cultural STATUS above). Answers: does a real official co-production
# route (bilateral or multilateral) exist connecting this country to
# others in the current 49-country universe? Never merged with the
# national-status question -- a country can have real co-pro coverage
# with no separate national INCENTIVE program, or vice versa.
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CoproductionCoverageStatus:
    jurisdiction_code: str
    status: str  # one of COPRO_* constants
    #: Real, cited bilateral partner countries confirmed this pass --
    #: existence only, NOT full contribution/role doctrine (which
    #: requires the treaty's own full text, not researched at this
    #: depth this pass unless already in treaty_engine.py).
    confirmed_bilateral_partners: tuple[str, ...] = ()
    #: Real multilateral frameworks the country is confirmed a member of
    #: (beyond what treaty_engine.py's own membership sets already cover).
    confirmed_multilateral_memberships: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    notes: str | None = None
    exact_unresolved_propositions: tuple[str, ...] = ()
    retrieved_date: str | None = None
    #: Per-confirmed-partner operational-term disclosure (Queue D,
    #: 2026-08-19 continuation). Keyed by the partner's ISO2 code (must be
    #: a member of confirmed_bilateral_partners). Each value is a real,
    #: cited fact string when a contribution/role/timing term WAS found,
    #: or an explicit "TERM_UNRESOLVED: <what remains unknown>" string
    #: when it genuinely was not -- the route's existence is never
    #: silently withdrawn just because one operational parameter remains
    #: unknown (ROUTE EXISTS + SPECIFIC TERM UNRESOLVED, never treated as
    #: though the route does not exist). Additive-only field: empty dict
    #: for every pre-existing record, never required.
    partner_contribution_terms: dict[str, str] = field(default_factory=dict)


#: Real research this pass for the 13 countries treaty_engine.py's own
#: registry had no bilateral/multilateral entry for (the "no_coverage"
#: list computed against the current 49-country universe). Each partner
#: country listed is itself real and cited -- never fabricated -- but
#: full bilateral TERMS (contribution %, role treatment) were not
#: independently re-verified against the treaty's own full legal text at
#: this depth; that remains a genuine, disclosed residual even for
#: CONFIRMED routes.
_COPRO_COVERAGE_OVERRIDES: tuple[CoproductionCoverageStatus, ...] = (
    CoproductionCoverageStatus(
        jurisdiction_code="AE",
        status=COPRO_AUTHORITY_UNRESOLVED,
        confirmed_bilateral_partners=(),
        sources=(
            "https://www.unesco.org/creativity/en/policy-monitoring-platform/film-co-production-agreements",
            "https://mof.gov.ae/en/open-data/international-treaties-dashboard/",
            "https://yousefalotaiba.com/insights/abu-dhabi-israel-sign-major-film-tv-deal/",
        ),
        notes="Continuation pass 2026-08-19 (Worldwide Program Qualification Completion, Queue C): "
              "exhaustive further research performed, still no confirmed official treaty found. The "
              "UAE's own Ministry of Finance International Treaties Dashboard (a real, filterable, "
              "official government treaty database) covers ONLY Double Taxation Avoidance Agreements "
              "and Bilateral Investment Treaties -- no film/media co-production category exists there "
              "at all, ruling out that specific database as the wrong instrument rather than proving "
              "absence. UNESCO's Policy Monitoring Platform (a real, authoritative, global "
              "multilateral film-co-production-agreement registry) did not surface the UAE among "
              "countries with listed agreements in the record retrieved (though the platform's full "
              "country-filtered index was not independently confirmed empty for UAE specifically). "
              "The one concrete UAE international film arrangement found -- the 2020 Abu Dhabi Film "
              "Commission / Israel Film Fund agreement -- is confirmed, via direct primary-adjacent "
              "quote, to be a goodwill/cultural-exchange 'cooperation agreement' for training, "
              "workshops and festival programming, NOT a formal treaty conferring national-treatment "
              "or majority/minority co-production status.",
        exact_unresolved_propositions=(
            "AE_OFFICIAL_COPRODUCTION_TREATY_EXISTENCE_UNCONFIRMED -- no UAE Ministry of Culture/"
            "Creative Media Authority own treaty register was located in English despite checking the "
            "UAE's own MOF treaty dashboard (wrong treaty category), UNESCO's multilateral film-"
            "co-production registry, and the one concrete UAE-Israel arrangement (confirmed to be "
            "cultural-exchange cooperation, not a co-production treaty). Required fact type: the UAE "
            "Ministry of Culture and Youth or Creative Media Authority's own official treaty register, "
            "not located at the depth searched.",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="KR",
        status=COPRO_ROUTE_EXISTS,
        confirmed_bilateral_partners=("CA", "GB", "SG", "NZ", "FR"),
        sources=("https://www.koreanfilm.or.kr/eng/coProduction/treaties.jsp",),
        notes="Official KoBiz/KOFIC treaty list (primary): Canada (Agreement on Cooperation in "
              "Audiovisual Coproduction), UK (Korea-UK FTA Cultural Cooperation Protocol), Singapore "
              "(Korea-Singapore FTA), New Zealand (2 agreements), France (2006) -- 5 real partners in "
              "the current 49-country universe (also lists China/India/EU, not individually in this "
              "universe). NOT yet added to treaty_engine.py's own _BILATERAL registry as new entries "
              "this pass (a real, disclosed connection gap -- see FINAL closeout) to avoid touching "
              "that module's own tested internals without full bilateral-term verification. "
              "Continuation pass 2026-08-19 (Queue D): the Canada route's contribution terms WERE "
              "found this pass via Telefilm Canada's own official treaty page -- see "
              "partner_contribution_terms['CA']. GB/SG/NZ/FR contribution terms were not independently "
              "retrieved this pass and fail closed explicitly rather than being silently omitted.",
        partner_contribution_terms={
            "CA": (
                "Minimum participation 30% for bipartite co-productions, 20% for multipartite "
                "co-productions (Telefilm Canada's own official treaty summary, "
                "telefilm.ca/en/traites/korea; treaty signed 25 April 1995). Maximum contribution "
                "percentage not stated in the summary retrieved -- TERM_UNRESOLVED for the ceiling "
                "specifically (the floor IS confirmed)."
            ),
            "GB": "TERM_UNRESOLVED: existence confirmed (Korea-UK FTA Cultural Cooperation Protocol) via koreanfilm.or.kr, but exact contribution percentages not independently retrieved this pass.",
            "SG": "TERM_UNRESOLVED: existence confirmed (Korea-Singapore FTA) via koreanfilm.or.kr, but exact contribution percentages not independently retrieved this pass.",
            "NZ": "TERM_UNRESOLVED: existence confirmed (2 agreements, per koreanfilm.or.kr and independently via NZFC's own co-production partner list) but exact contribution percentages not independently retrieved this pass.",
            "FR": "TERM_UNRESOLVED: existence confirmed (2006 agreement) via koreanfilm.or.kr, but exact contribution percentages not independently retrieved this pass.",
        },
        exact_unresolved_propositions=(
            "KR_GB_KR_SG_KR_NZ_KR_FR_BILATERAL_TERMS_UNCONFIRMED -- existence confirmed via "
            "koreanfilm.or.kr (primary) for all 5 partners; exact majority/minority contribution "
            "percentages confirmed only for Canada this pass (30% bipartite / 20% multipartite "
            "minimum, ceiling unstated) -- see partner_contribution_terms for the per-partner detail.",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="IL",
        status=COPRO_ROUTE_EXISTS,
        confirmed_bilateral_partners=("FR", "DE", "IT", "GB", "AU", "NZ", "SE"),
        sources=(
            "http://intl.filmfund.org.il/index.asp?id=8",
            "https://thereactionlab.com/blog/israel-france-film-co-production-agreement-connecting-cultures-and-fostering-creative-exchange",
        ),
        notes="Israel Film Fund's own page confirms 'over 20 co-production treaties, mostly with "
              "European countries' (primary-adjacent). Cross-corroborated via Australia's own listed "
              "treaty partners (includes Israel) and the UK's own listed treaty partners (includes "
              "Israel); France treaty independently dated to 1970. Exact full partner list beyond "
              "these 7 real, cited countries not independently enumerated this pass.",
        exact_unresolved_propositions=(
            "IL_COMPLETE_BILATERAL_PARTNER_LIST_AND_TERMS_UNCONFIRMED -- Israel Film Fund's own "
            "dedicated treaty-list page returned 404 on direct fetch this pass; the 7 partners above "
            "are corroborated via secondary/cross-listing sources, not Israel's own complete official "
            "enumeration.",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="TW",
        status=COPRO_ROUTE_EXISTS,
        confirmed_bilateral_partners=("NZ",),
        sources=(
            "https://www.nzcio.com/assets/NZCIO-documents/ANZTEC-film-and-tv.pdf",
            "https://en.mofa.gov.tw/News_Content.aspx?n=1386&s=34624",
            "https://www.nzfilm.co.nz/resources/co-production-agreement-summary-sheets",
        ),
        notes="Continuation pass 2026-08-19 (Worldwide Program Qualification Completion, Queue D): a "
              "REAL, RATIFIED, formal bilateral economic treaty was found and read directly -- the "
              "Agreement between New Zealand and the Separate Customs Territory of Taiwan, Penghu, "
              "Kinmen and Matsu on Economic Cooperation (ANZTEC), in force 1 December 2013, contains a "
              "dedicated Chapter 18 (Film and Television Co-Production). The Implementing Arrangement "
              "to Chapter 18 was read in full: competent authorities are the New Zealand Film "
              "Commission (NZFC) and Taiwan's Bureau of Audiovisual and Music Industry Development "
              "(BAMID, Ministry of Culture); a two-stage approval process (provisional then final "
              "approval before distribution); a required co-producer contract covering IP ownership, "
              "cost liability, receipts division, contribution completion dates, and festival-"
              "nationality designation. This is a materially STRONGER finding than the earlier-"
              "confirmed France relationship (a mere MOU) -- ANZTEC is a real, signed, in-force "
              "international economic agreement with a dedicated co-production chapter, not an "
              "industry MOU. Directly upgrades Taiwan's Queue A/C status from 'no confirmed treaty' to "
              "'one confirmed real treaty route'.",
        partner_contribution_terms={
            "NZ": (
                "TERM_UNRESOLVED: the exact minority/majority co-producer contribution percentage "
                "(referenced as Article 4 of Chapter 18 in the Implementing Arrangement itself) was NOT "
                "independently retrieved this pass -- only the Implementing Arrangement (the "
                "administrative/procedural annex governing the co-producer contract's required "
                "contents) was located as a separate readable document; ANZTEC's main treaty text "
                "(Chapter 18 itself, which states the percentages) was not found as a separately "
                "fetchable document at the depth searched. ROUTE EXISTS AND IS REAL -- competent "
                "authorities, approval process, and required contract terms are all confirmed -- but "
                "this one specific operational parameter fails closed rather than being fabricated or "
                "silently assumed from an unrelated treaty by analogy."
            ),
        },
        exact_unresolved_propositions=(
            "TW_NZ_CONTRIBUTION_PERCENTAGE_UNCONFIRMED -- see partner_contribution_terms['NZ'] for the "
            "exact disclosure. Required fact type: ANZTEC's own main treaty text, Chapter 18, Article 4 "
            "(not located as a separately fetchable document this pass -- treaties.mfat.govt.nz hosts "
            "the full ANZTEC text and should be the next source checked).",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="MA",
        status=COPRO_ROUTE_EXISTS,
        confirmed_bilateral_partners=("GB",),
        sources=("https://www.ep.com/blog/curious-about-co-productions-what-you-need-to-know/",),
        notes="UK's own listed treaty partners include Morocco -- confirmed via secondary aggregation "
              "of UK's real treaty list, not Morocco's own CCM (Centre Cinematographique Marocain) "
              "site directly.",
        exact_unresolved_propositions=(
            "MA_TREATY_TERMS_AND_ADDITIONAL_PARTNERS_UNCONFIRMED -- CCM's own treaty-list page not "
            "independently fetched this pass.",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="MY",
        status=COPRO_ROUTE_EXISTS,
        confirmed_bilateral_partners=("AU",),
        sources=("https://www.malaymail.com/news/malaysia/2021/07/09/malaysia-australia-film-collaboration-stimulates-local-creative-industrys-g/1988599",),
        notes="Australia's own listed treaty partners include Malaysia; corroborated by a real 2021 "
              "Malaysia-Australia film collaboration news report.",
        exact_unresolved_propositions=(
            "MY_TREATY_TERMS_AND_ADDITIONAL_PARTNERS_UNCONFIRMED -- FINAS's (Malaysia's national film "
              "authority) own treaty-list page not independently fetched this pass.",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="SG",
        status=COPRO_ROUTE_EXISTS,
        confirmed_bilateral_partners=("KR",),
        sources=("https://www.koreanfilm.or.kr/eng/coProduction/treaties.jsp",),
        notes="Korea-Singapore FTA cultural-cooperation provisions, confirmed via KOFIC's own official "
              "treaty list.",
        exact_unresolved_propositions=(
            "SG_ADDITIONAL_PARTNERS_UNCONFIRMED -- IMDA's (Singapore's own media authority) treaty "
              "list not independently fetched this pass.",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="JP",
        status=COPRO_ROUTE_EXISTS,
        confirmed_bilateral_partners=("IT",),
        sources=(
            "https://deadline.com/2024/11/how-japan-italy-producers-leverage-co-production-agreement-1236169017/",
            "https://www.mofa.go.jp/erp/we/it/pagewe_000001_00076.html",
        ),
        notes="Japan-Italy Film Co-production Treaty, signed June 2024, activated August 2024 -- "
              "Japan's second bilateral film treaty (after China, not in the current 49-country "
              "universe). Corroborated by Japan's own Ministry of Foreign Affairs (MOFA) page.",
        partner_contribution_terms={
            "IT": "TERM_UNRESOLVED: route existence confirmed via Japan's own MOFA page and Deadline's "
                  "reporting, but exact minority/majority contribution percentages were not "
                  "independently retrieved from the treaty's own full text this pass. ROUTE EXISTS "
                  "AND IS REAL (signed June 2024, activated August 2024, government-corroborated) -- "
                  "this one operational parameter fails closed rather than being fabricated or "
                  "assumed by analogy from Italy's other bilateral treaties.",
        },
        exact_unresolved_propositions=(
            "JP_IT_CONTRIBUTION_PERCENTAGE_UNCONFIRMED -- see partner_contribution_terms['IT'].",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="PH",
        status=COPRO_ROUTE_EXISTS,
        confirmed_bilateral_partners=("FR",),
        sources=("https://www.sunstar.com.ph/davao/feature/fdcp-france-sign-film-co-production-treaty",),
        notes="FDCP-France film co-production treaty, officially signed (Philippine news reporting of "
              "the signing) -- see also the matching national_cultural_status.py PH record.",
        partner_contribution_terms={
            "FR": "TERM_UNRESOLVED: route existence confirmed via Philippine news reporting of the "
                  "official FDCP-France signing ceremony, but exact minority/majority contribution "
                  "percentages were not independently retrieved from the treaty's own full text this "
                  "pass. ROUTE EXISTS AND IS REAL (officially signed, government-body-corroborated) -- "
                  "this one operational parameter fails closed rather than being fabricated or "
                  "assumed by analogy from France's other bilateral treaties.",
        },
        exact_unresolved_propositions=(
            "PH_FR_CONTRIBUTION_PERCENTAGE_UNCONFIRMED -- see partner_contribution_terms['FR'].",
        ),
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="US",
        status=COPRO_NO_RELEVANT_ROUTE,
        sources=("https://vitrina.ai/blog/official-co-production-treaties-guide/",),
        notes="Confirmed (prior continuation, this same arc): the US has negotiated fewer co-production "
              "treaties than any other industrialized country and has none with Canada or Mexico; its "
              "only treaty (China) is not broad and is not in the current 49-country universe. A "
              "genuine, real, primary-adjacent confirmed-absent finding for the countries in our "
              "universe, not merely 'not found'.",
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="TH",
        status=COPRO_NO_RELEVANT_ROUTE,
        sources=("https://filmthailand.org/co-production/",),
        notes="Film Thailand (Thailand's own official film office) directly states Thailand has not "
              "entered into any formal co-production treaties, and is currently EVALUATING the "
              "possibility -- a genuine, current, primary-sourced confirmed-absent finding, not "
              "merely 'not found'.",
        retrieved_date="2026-08-19",
    ),
    CoproductionCoverageStatus(
        jurisdiction_code="MU",
        status=COPRO_AUTHORITY_UNRESOLVED,
        sources=("https://www.polity.org.za/article/ecdc-mauritius-film-development-corporation-indicates-interest-in-growing-eastern-cape-film-sector-2019-08-28",),
        notes="A 2013-era source describes Mauritius PLANNING (not having signed) co-production "
              "treaties with UK/France/South Africa/India; a 2019 report describes only exploratory "
              "MFDC-ECDC (South Africa) interest, not a concluded treaty. No current source confirms "
              "any treaty was ever finalized -- genuinely unresolved, not confidently NO_RELEVANT "
              "(the 2013 evidence is real but stale, and does not rule out a later signing this pass "
              "could not locate).",
        exact_unresolved_propositions=(
            "MU_COPRODUCTION_TREATY_CURRENT_STATUS_UNCONFIRMED -- last concrete evidence found is from "
            "2013 (planned, not signed); EDB Mauritius's own 'Bilateral Agreements' page "
            "(edbmauritius.org/bilateral-agreements) was found in search results but not independently "
            "fetched for content this pass.",
        ),
        retrieved_date="2026-08-19",
    ),
)


def get_coproduction_coverage_status(jurisdiction_code: str) -> CoproductionCoverageStatus:
    """Queue C's one canonical lookup. For the 36 countries treaty_engine.py's
    own registry (bilateral pairs or multilateral membership) already
    covers, returns COPRO_ROUTE_EXISTS / COPRO_MULTILATERAL_EXISTS computed
    directly from that real, existing data -- never re-researched. For the
    13 countries that registry had no entry for, returns this pass's real,
    cited override where researched, or a genuine AUTHORITY_UNRESOLVED
    otherwise (never silently defaulted)."""
    code = jurisdiction_code.split("-")[0].upper()
    for rec in _COPRO_COVERAGE_OVERRIDES:
        if rec.jurisdiction_code == code:
            return rec

    from app.calculators import treaty_engine as te
    bilateral_partners = tuple(sorted(
        (b if a == code else a)
        for fs in te._BILATERAL.keys()
        for a, b in (tuple(fs) if len(fs) == 2 else (list(fs)[0], list(fs)[0]),)
        if code in fs
    ))
    multilateral = tuple(sorted(
        name for name, members in (
            ("eurimages", te._EURIMAGES_MEMBERS),
            ("ibermedia", te._IBERMEDIA_MEMBERS),
        ) if code in members
    ))
    if bilateral_partners and multilateral:
        return CoproductionCoverageStatus(
            jurisdiction_code=code, status=COPRO_ROUTE_EXISTS,
            confirmed_bilateral_partners=bilateral_partners,
            confirmed_multilateral_memberships=multilateral,
            notes="Computed directly from treaty_engine.py's existing real registry.",
        )
    if multilateral:
        return CoproductionCoverageStatus(
            jurisdiction_code=code, status=COPRO_MULTILATERAL_EXISTS,
            confirmed_multilateral_memberships=multilateral,
            notes="Computed directly from treaty_engine.py's existing real registry.",
        )
    if bilateral_partners:
        return CoproductionCoverageStatus(
            jurisdiction_code=code, status=COPRO_ROUTE_EXISTS,
            confirmed_bilateral_partners=bilateral_partners,
            notes="Computed directly from treaty_engine.py's existing real registry.",
        )
    return CoproductionCoverageStatus(
        jurisdiction_code=code, status=COPRO_AUTHORITY_UNRESOLVED,
        exact_unresolved_propositions=(
            f"{code}_OFFICIAL_COPRODUCTION_COVERAGE_UNCONFIRMED -- no bilateral or multilateral route "
            "found in treaty_engine.py's existing registry, and no primary/secondary research was "
            "performed for this country this pass.",
        ),
    )
