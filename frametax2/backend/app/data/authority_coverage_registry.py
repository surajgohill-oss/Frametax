"""
authority_coverage_registry.py

The single deterministic source of truth for WHY a program is or is not
available to CineGlobe's economic optimizer.

CORRECTION (Global Priceability Optimizer Restoration, this task): the
"georgia_eiia"/"us_ga_film_credit" rows were REMOVED. Codex's optimizer
doctrine/priceability lineage trace (docs/validation/CODEX_OPTIMIZER_
DOCTRINE_PRICEABILITY_LINEAGE.json) identified this as the single
"artificial schema requirement" case in the entire 126-program formulaic
universe: two VERIFIED-tier RateRules, an explicit doctrine classification,
and a territorial SpendRule already exist for us_ga_film_credit (O.C.G.A.
Section 48-7-40.26, recovered across the canonical-authority-substrate
tasks), yet this static veto row still blocked it ahead of that executable
substrate — the ONLY formulaic program where the veto contradicted
already-accepted, already-cited runtime data rather than reflecting a
genuine absence of authority. Every other UNPRICEABLE_AUTHORITY_INSUFFICIENT
row in this file was cross-checked against verified_rate_rule_count in the
same trace and found consistent (zero VERIFIED RateRules), so this was a
one-row data correction, not a reopening of the veto list.

CORRECTION (Global Economic Data + Base Pricing, this task): 8 further
rows removed (16 counting alias-spelling duplicates) after individually
re-examining each program's existing RateRule citation in program_rate_
rules_worldwide.py: ca_bc_pstc/bc_pstc, hr_cash_rebate, nz_spg_
international, tt_production_expenditure_rebate/tt_film_incentive,
us_la_film_incentive/la_film_production, us_md_film_production_activity_
credit/us_md_film_credit, us_nm_film_credit/nm_film_production, us_ri_
film_credit. Each already carried a citation that (a) explicitly states
the source was fetched directly from the administering government's own
page, and (b) quotes specific statutory/regulatory rate language rather
than a paraphrase. The corresponding DoctrineRecord.confidence_tier was
promoted PARSED -> VERIFIED to reflect that the underlying research
already met the primary-source bar this project uses for VERIFIED
elsewhere (see program_rate_rules_worldwide.py for each program's full
citation) — the veto in this file was the only remaining reason these
programs did not price, exactly like Georgia. Candidates with a citation
that only cites a secondary/aggregator source, or that discloses an
unresolved conflict ON THE RATE FIGURE ITSELF (not a cap/threshold/sunset
side-detail), were deliberately left PARSED and still vetoed — promotion
requires the SPECIFIC figure being relied on to be primary-sourced, not
just some field on the same program.

CORRECTION (Global Economic Data + Base Pricing, batch 2): 2 more rows
removed (4 counting alias spellings) after fresh primary-source
verification this task: sa_film_commission_rebate/sa_sfc_rebate (film.sa,
official, independently re-fetched directly this task — 60% flat rebate,
min spend SAR 750,000 feature/187,000 doc-animation, confirming a PRIOR
session's own direct fetch of the same page exactly) and si_cash_rebate/
si_film_incentive (filminslovenia.si, official — up to 25%, confirmed via
a fresh search this task reproducing the same quoted figure the existing
citation's own direct fetch had already recorded).

CORRECTION (Global Economic Data + Base Pricing, batch 3): 8 more rows
removed (10 counting alias spellings) after individually re-examining each
program's existing RateRule citation: ca_on_opstc/on_opstc (ontariocreates.ca,
official, fetched directly — 21.5% of all qualifying Ontario QPE), de_dfff
(ffa.de, official, fetched directly — 30% uniform grant), es_tax_credit_
foreign (Ley 27/2014 Art. 36.2, BOE-A-2014-12328 — a direct verbatim
statute quote, the strongest provenance tier this registry recognizes),
fr_trip (cnc.fr, official TRIP page, fetched directly — up to 30%/40%),
hu_hipa_rebate (nfi.hu, official, fetched directly — 30% base), no_film_
incentive (norwegianfilm.com, official — up to 25%, competitive/
discretionary), us_mn_film_production_credit/us_mn_film_credit
(revenue.state.mn.us, official, direct fetch 2026-07-26 — 25% flat), and
uk_avec (bfi.org.uk, official, fetched directly — AVEC, rate quoted
verbatim). Each DoctrineRecord.confidence_tier promoted PARSED -> VERIFIED
on the same bar as batches 1/2. Per the durability clarification received
during this batch, each of these 18 promoted programs (batches 1-3
combined) also now carries a structured SourceProvenance record on its
DoctrineRecord (see program_rate_rules.SourceProvenance and executable_
jurisdiction_registry.get_provenance()) — issuing authority, source URL,
citation detail, effective/verification dates where stated, and any
material interpretation — not just the free-text citation string this
module's veto-removal decisions were originally based on.

CORRECTION (Global Formulaic Economic Completion, batch 4): 3 more rows
removed (4 counting the ca_film_30 alias spelling) after fresh, this-task
primary-source verification via direct WebFetch of the actual
administering authority: cy_film_rebate (film.investcyprus.org.cy,
Cyprus Film Commission, official, independently re-fetched -- "Up to 45%
Tax Rebate", matching the existing citation's figure exactly), ie_section_
481 (revenue.ie, Revenue Commissioners Ireland, official, fetched
directly -- "32% of whichever is the lowest of" eligible expenditure/80%
of costs/an EUR cap, also correcting the cap figure from a flat EUR 70M
to the real certification-date-dependent EUR 70M/125M split), and
us_ca_film_credit/ca_film_30 (AB 1138, California's actual statute,
fetched directly from leginfo.legislature.ca.gov -- "35 percent or 40
percent, whichever is the applicable credit percentage" -- plus the CA
Film Commission's own Program 4.0 page confirming program size/caps).
Each DoctrineRecord/RateRule promoted PARSED -> VERIFIED with structured
SourceProvenance recorded. Several other batch-4 candidates were
web-searched/fetched this task and explicitly held at PARSED because the
official source's page either did not surface the specific rate figure
being relied upon (at_fisa_plus/fisaplus.com, ca_federal_pstc/canada.ca
403, ae_ad_film_rebate/film.gov.ae 403) or confirmed a DIFFERENT figure
than the one modeled (be_tax_shelter/finance.belgium.be describes the
investor-side 310% exemption, not the producer-net 42-44% this engine
models) -- held, not promoted on inconclusive or mismatched evidence.

CORRECTION (Global Formulaic Economic Completion, Path B primary
research): on_ofttc removed. This was one of the 21 genuinely-zero-
evidence programs (see docs/validation/GLOBAL_ECONOMIC_DATA_ZERO_
EVIDENCE_21.json) -- researched from scratch this task via a direct
fetch of ontariocreates.ca/tax-incentives/ofttc (Ontario Creates,
official): base rate "35% of the eligible Ontario labour expenditures".
A new DoctrineRecord was canonicalized (program_rate_rules_worldwide.py)
with structured SourceProvenance, VERIFIED tier. KNOWN LIMITATION,
disclosed not silently worked around: on_ofttc shares jurisdiction_code
CA-ON with the already-priced ca_on_opstc. production_discovery.py's
discover_executable_jurisdictions() maps one examination per
jurisdiction_code (feasibility_by_code = {e.jurisdiction_code: e for e
in examinations}), so on_ofttc does not yet reach its own independent
priced candidate structure in served runtime -- it is shadowed by
ca_on_opstc's structure for the same code. Extending discovery to
support multiple programs per jurisdiction_code was investigated and
explicitly reverted in an earlier task (see CAPABILITY_LEDGER.md) because
it silently corrupts feasibility_by_code and can create duplicate
ProductionStructure rows -- a real fix requires solving both issues
together, deliberately out of scope for this data-only task. on_ofttc is
therefore canonically correct and unblocked at the data layer (removed
from this registry, real VERIFIED RateRule, real provenance) but not yet
independently served -- a genuine, disclosed discovery-layer residual,
not a data/authority gap.

Originally added by the Consolidated Global Remediation for 29 records
(25 authority-insufficient + 4 non-economic). EXPANDED by the Global Data
Application phase to carry every canonical disposition from
docs/validation/GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (176 records).

This module is NOT display metadata. It is consulted deterministically by:
  - app/calculators/production_discovery.py  (STAGE 2 priceability gate)
  - app/calculators/allocation_pricing.py    (price_segment hard block)
so a covered program cannot enter economic candidacy, cannot price, cannot
contribute NPC benefit, and cannot be ranked as an economic candidate by ANY
route -- including a directly-specified StructureSpec.

States
------
PRICEABLE_VALIDATED
    Default for anything ABSENT from this registry. Never stored as a row --
    absence means "not excluded", so a new program is priceable by default and
    this registry can never silently suppress one.
UNPRICEABLE_AUTHORITY_INSUFFICIENT
    Authority exists but the completed corpus captured no defensible rate/award
    basis. NOT a validated zero benefit -- CineGlobe simply cannot price it yet.
NON_GUARANTEED_SELECTIVE
    A real, competitively-awarded program (grant/fund/call). Its headline rate is
    NOT guaranteed absent a project-specific award, so its guaranteed optimizer
    value is ZERO. Canonical action ENCODE_SELECTIVE_ZERO_GUARANTEED.
NON_ECONOMIC
    Facilitation / permits / market access / workforce development. No producer
    economic instrument exists to price.
NO_CURRENT_INCENTIVE
    Confirmed that no current producer incentive exists. (Reserved: no canonical
    record currently carries this state; kept so the distinction stays explicit
    rather than being collapsed into "authority insufficient".)
SUPERSEDED
    Replaced by a current program. Must not price as current.
DUPLICATE
    An alias of another canonical record. Must not create a second candidate.
CANONICAL_DATA_HANDOFF_DEFECT
    The canonical payload marked the record IMPLEMENTATION_READY and supplied
    literal economics, but supplied no runtime identity binding, and the only
    same-jurisdiction runtime program is a demonstrably DIFFERENT statutory
    program. Binding the rate would be a correctness defect, so it is stopped
    and reported rather than guessed. Blocks candidacy (fails safe).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CoverageState = Literal[
    "PRICEABLE_VALIDATED",
    "UNPRICEABLE_AUTHORITY_INSUFFICIENT",
    "NON_GUARANTEED_SELECTIVE",
    "NON_ECONOMIC",
    "NO_CURRENT_INCENTIVE",
    "SUPERSEDED",
    "DUPLICATE",
    "CANONICAL_DATA_HANDOFF_DEFECT",
]

#: Every state EXCEPT PRICEABLE_VALIDATED blocks economic candidacy.
BLOCKING_STATES: frozenset[str] = frozenset({
    "UNPRICEABLE_AUTHORITY_INSUFFICIENT",
    "NON_GUARANTEED_SELECTIVE",
    "NON_ECONOMIC",
    "NO_CURRENT_INCENTIVE",
    "SUPERSEDED",
    "DUPLICATE",
    "CANONICAL_DATA_HANDOFF_DEFECT",
})

STATE_REASON: dict[str, str] = {
    "UNPRICEABLE_AUTHORITY_INSUFFICIENT": (
        "Authority is insufficient to price deterministically: the completed primary-authority "
        "corpus captured no defensible current rate or award basis. Excluded from pricing and "
        "ranking rather than inheriting a stale stored value. This is NOT a validated zero "
        "benefit."
    ),
    "NON_GUARANTEED_SELECTIVE": (
        "Selective/competitive award (grant, fund or call). The headline rate is not guaranteed "
        "absent a project-specific award, so guaranteed optimizer value is zero. May be "
        "surfaced as a pursuable opportunity; never priced as deterministic economics."
    ),
    "NON_ECONOMIC": (
        "Facilitation, permitting, market-access or workforce-development body - no producer "
        "economic instrument exists to price."
    ),
    "NO_CURRENT_INCENTIVE": (
        "Confirmed that no current producer incentive exists."
    ),
    "SUPERSEDED": (
        "Superseded by a current program; must not price as current. Retained for provenance."
    ),
    "DUPLICATE": (
        "Duplicate/alias of another canonical record; must not create a second optimizer "
        "candidate."
    ),
    "CANONICAL_DATA_HANDOFF_DEFECT": (
        "Canonical payload supplied literal economics but no runtime identity binding, and the "
        "only same-jurisdiction runtime program is a demonstrably different statutory program. "
        "Stopped rather than bound to the wrong program. Requires a canonical identity binding."
    ),
}


@dataclass(frozen=True)
class AuthorityCoverageRecord:
    program_slug: str
    state: str
    jurisdiction: str
    program_name: str

    @property
    def reason(self) -> str:
        return STATE_REASON[self.state]

    @property
    def blocks_economic_candidacy(self) -> bool:
        return self.state in BLOCKING_STATES


#: (program_slug, state, jurisdiction, program_name)
_ROWS: tuple[tuple[str, str, str, str], ...] = (
    ("in_nfdc_coproduction", "CANONICAL_DATA_HANDOFF_DEFECT", "India", "NFDC International Co-production Development Fund"),
    ("proposed_canada_british_columbia_film_incentive_bc_fibc", "CANONICAL_DATA_HANDOFF_DEFECT", "Canada / British Columbia", "Film Incentive BC (FIBC)"),
    ("proposed_germany_german_motion_picture_fund_gmpf", "CANONICAL_DATA_HANDOFF_DEFECT", "Germany", "German Motion Picture Fund (GMPF)"),
    ("ccm_tourism_film_facilitation", "DUPLICATE", "Morocco", "CCM Tourism Film Facilitation"),
    ("bw_film_commission", "NON_ECONOMIC", "Botswana", "bw_film_commission"),
    ("cn_film_incentive", "NON_ECONOMIC", "China", "cn_film_incentive"),
    ("kh_film_incentive", "NON_ECONOMIC", "Cambodia", "kh_film_incentive"),
    ("screenskills_production_workforce_development", "NON_ECONOMIC", "United Kingdom", "ScreenSkills Production Workforce Development"),
    ("tz_film_incentive", "NON_ECONOMIC", "Tanzania", "tz_film_incentive"),
    ("IBERMEDIA_MEMBERSHIP_AND_FRAMEWORK", "NON_GUARANTEED_SELECTIVE", "Multinational / cross-regional", "IBERMEDIA membership and framework"),
    ("acpfilms_fund", "NON_GUARANTEED_SELECTIVE", "African, Caribbean and Pacific Group / African, Caribbean and Pacific Group", "ACP Films — EU-ACP Cultural Film Co-production Fund"),
    ("bt_film_incentive", "NON_GUARANTEED_SELECTIVE", "Bhutan", "Bhutan Film Commission / Tourism Council Production Facilitation"),
    ("cm_film_incentive", "NON_GUARANTEED_SELECTIVE", "Cameroon", "Cameroon Centre National de la Cinématographie Film Support"),
    ("hk_film_dev_fund", "NON_GUARANTEED_SELECTIVE", "Hong Kong SAR", "Hong Kong Film Development Fund (FDF)"),
    ("ibermedia_programme", "NON_GUARANTEED_SELECTIVE", "Ibero-American Region (SEGIB) / Ibero-American Region (SEGIB)", "IBERMEDIA Programme for Ibero-American Co-productions"),
    ("il_film_incentive", "NON_GUARANTEED_SELECTIVE", "Israel", "Israel Film Fund / Maslool Incentive"),
    ("jo_rfc_rebate", "NON_GUARANTEED_SELECTIVE", "Jordan", "Royal Film Commission Jordan — Production Rebate"),
    ("jp_film_incentive", "NON_GUARANTEED_SELECTIVE", "Japan", "Japan Film Commission Location Incentive (JLOC)"),
    ("jp_vipo_location_incentive", "NON_GUARANTEED_SELECTIVE", "Japan", "Japan Film Commission Location Incentive (JLOC) [runtime slug of jp_film_incentive]"),
    ("korea_kocca_animation_production_support", "NON_GUARANTEED_SELECTIVE", "South Korea", "Korea KOCCA Animation Production Support"),
    ("kr_film_incentive", "NON_GUARANTEED_SELECTIVE", "South Korea", "Korea Film Council (KOFIC) Location Incentive"),
    ("kr_kofic_location_incentive", "NON_GUARANTEED_SELECTIVE", "South Korea", "Korea Film Council (KOFIC) Location Incentive [runtime slug of kr_film_incentive]"),
    ("na_film_commission", "NON_GUARANTEED_SELECTIVE", "Namibia", "Namibia Film Commission Production Incentive"),
    ("ph_film_incentive", "NON_GUARANTEED_SELECTIVE", "Philippines", "Film Development Council of the Philippines (FDCP) Incentive"),
    ("proposed_united_kingdom_uk_global_screen_fund_international_co_production", "NON_GUARANTEED_SELECTIVE", "United Kingdom", "UK Global Screen Fund — International Co-production"),
    ("qa_dfi_fund", "NON_GUARANTEED_SELECTIVE", "Qatar", "Doha Film Institute — Grants for Filmmakers"),
    ("ru_film_incentive", "NON_GUARANTEED_SELECTIVE", "Russia", "Russian Cinema Fund (Fond Kino) Production Support"),
    ("rw_film_incentive", "NON_GUARANTEED_SELECTIVE", "Rwanda", "Rwanda Development Board Film Production Support"),
    ("sg_imda_film_fund", "NON_GUARANTEED_SELECTIVE", "Singapore", "IMDA Singapore — Feature Film Production Grant"),
    ("singapore_imda_digital_media_development_fund", "NON_GUARANTEED_SELECTIVE", "Singapore", "Singapore IMDA Digital Media Development Fund"),
    ("tn_film_incentive", "NON_GUARANTEED_SELECTIVE", "Tunisia", "Tunisia CNCI Cash Rebate"),
    ("tr_film_incentive", "NON_GUARANTEED_SELECTIVE", "Turkey", "Turkey Cinema General Directorate Production Support"),
    ("vipo_animation_and_content_support", "NON_GUARANTEED_SELECTIVE", "Japan", "VIPO Animation and Content Support"),
    ("za_dac_fund", "NON_GUARANTEED_SELECTIVE", "South Africa", "NFVF South Africa — Development and Production Fund"),
    ("ae_dpip", "SUPERSEDED", "United Arab Emirates", "Dubai Film Commission — Dubai Production Incentive (DPIP)"),
    ("ae_dxb_dpip", "SUPERSEDED", "United Arab Emirates", "Dubai Film Commission — Dubai Production Incentive (DPIP) [runtime slug of ae_dpip]"),
    ("iceland_post_production_visual_effects_and_animation_incentive", "SUPERSEDED", "Iceland", "Iceland Post-Production, Visual Effects and Animation Incentive"),
    ("ae_ad_film_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United Arab Emirates / Abu Dhabi", "Abu Dhabi 35++ Production Rebate [runtime slug of proposed_united_arab_emirates_abu_dhabi_abu_dhabi_35_production_rebate]"),
    ("al_cash_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Albania", "Albanian National Cinema Agency (ANCA) Cash Rebate [runtime slug of al_film_incentive]"),
    ("al_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Albania", "Albanian National Cinema Agency (ANCA) Cash Rebate"),
    ("ar_incaa_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Argentina", "INCAA — Argentine Film Institute Incentives"),
    ("at_fisa_plus", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Austria", "FISA+ Film Production Support Austria"),
    ("au_nsw_screen", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Australia / Australia — New South Wales", "NSW Government Screen Incentive (Create NSW)"),
    ("au_qld_screen_qld", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Australia / Australia — Queensland", "Screen Queensland Production Attraction Strategy"),
    ("au_screen_production", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Australia", "Screen Australia — Production Funding"),
    ("au_vic_vicscreen", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Australia / Australia — Victoria", "VicScreen Production Investment"),
    ("ba_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Bosnia and Herzegovina", "Film Centre Bosnia and Herzegovina Production Support"),
    ("bb_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Barbados", "Barbados Film and Entertainment Production Incentives"),
    ("bc_interactive_digital_media_tax_credit_idmtc", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / British Columbia", "BC Interactive Digital Media Tax Credit (IDMTC)"),
    ("bd_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Bangladesh", "bd_film_incentive"),
    ("be_tax_shelter", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Belgium", "Belgian Tax Shelter"),
    ("bg_film_encouragement_act_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Bulgaria", "Bulgarian Film Commission Cash Rebate [runtime slug of bg_film_incentive]"),
    ("bg_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Bulgaria", "Bulgarian Film Commission Cash Rebate"),
    ("bh_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Bahrain", "bh_film_incentive"),
    ("br_ancine_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Brazil", "ANCINE — Brazilian Film Commission Tax Incentives"),
    ("bs_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Bahamas", "Bahamas Film Commission Production Support"),
    ("by_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Belarus", "Belarusfilm National Film Studio Production Support"),
    ("ca_ab_fttc", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — Alberta", "Alberta Film and Television Tax Credit (FTTC)"),
    ("ca_cmf", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada", "Canada Media Fund (CMF) — Convergent Stream"),
    ("ca_federal_cptc", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada", "Canadian Film or Video Production Tax Credit"),
    ("ca_federal_pstc", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada", "Film or Video Production Services Tax Credit (PSTC) [runtime slug of proposed_canada_film_or_video_production_services_tax_credit_pstc]"),
    ("ca_mb_film_video_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — Manitoba", "Manitoba Film & Video Production Tax Credit [runtime slug of ca_mb_fvptc]"),
    ("ca_mb_fvptc", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — Manitoba", "Manitoba Film & Video Production Tax Credit"),
    ("ca_nb_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — New Brunswick", "New Brunswick Film Tax Credit"),
    ("ca_nb_film_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — New Brunswick", "New Brunswick Film Tax Credit [runtime slug of ca_nb_film_credit]"),
    ("ca_nl_production_fund", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — Newfoundland & Labrador", "Newfoundland & Labrador Film Development Corp Production Incentive"),
    ("ca_ns_pif", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — Nova Scotia", "Nova Scotia Film & Television Production Incentive Fund"),
    ("ca_ns_production_incentive_fund", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — Nova Scotia", "Nova Scotia Film & Television Production Incentive Fund [runtime slug of ca_ns_pif]"),
    ("ca_sk_creative_saskatchewan_grant", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — Saskatchewan", "Creative Saskatchewan Film and TV Production Grant [runtime slug of ca_sk_production_grant]"),
    ("ca_sk_production_grant", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Canada — Saskatchewan", "Creative Saskatchewan Film and TV Production Grant"),
    ("cl_corfo_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Chile", "Chile Corfo Film Incentive"),
    ("co_film_colombia", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Colombia", "Colombia Film Commission — Film In Colombia"),
    ("co_film_in_colombia", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Colombia", "Colombia Film Commission — Film In Colombia [runtime slug of co_film_colombia]"),
    ("cr_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Costa Rica", "Costa Rica Film Commission Production Facilitation"),
    ("cz_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Czech Republic", "Czech Film Incentive"),
    ("de_fff_bayern", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Germany / Germany — Bavaria", "FilmFernsehFonds Bayern (FFF Bayern)"),
    ("de_nrw_filmstiftung", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Germany / Germany — North Rhine-Westphalia", "Film und Medienstiftung NRW"),
    ("dk_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Denmark", "Danish Film Institute Production Support"),
    ("do_film_commission_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Dominican Republic", "Dominican Republic Film Commission Incentive [runtime slug of do_film_incentive]"),
    ("do_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Dominican Republic", "Dominican Republic Film Commission Incentive"),
    ("ec_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Ecuador", "Ecuador Film Commission Production Facilitation"),
    ("ee_film_estonia_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Estonia", "Film Estonia Cash Rebate [runtime slug of ee_film_incentive]"),
    ("ee_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Estonia", "Film Estonia Cash Rebate"),
    ("eg_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Egypt", "eg_film_incentive"),
    ("et_film_commission", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Ethiopia", "et_film_commission"),
    ("eu_media_fund", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "European Union / European Union", "Creative Europe MEDIA Programme"),
    ("fi_business_finland_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Finland", "Business Finland Film Incentive [runtime slug of fi_film_incentive]"),
    ("fi_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Finland", "Business Finland Film Incentive"),
    ("film_i_vast", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Sweden / Sweden — Västra Götaland", "Film i Väst — Regional Co-production Fund"),
    ("fr_cnc_production", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "France", "CNC France — Avances sur Recettes (Cinema Production Aid)"),
    ("ga_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Gabon", "ga_film_incentive"),
    ("gb_bfi_production", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United Kingdom", "BFI Film Fund — Production Funding"),
    ("gb_sct_screen_fund", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United Kingdom / United Kingdom — Scotland", "Screen Scotland Production Growth Fund"),
    ("gb_wls_screen_fund", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United Kingdom / United Kingdom — Wales", "Wales Screen Production Fund (Ffilm Cymru Wales)"),
    ("gh_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Ghana", "gh_film_incentive"),
    ("gt_film_commission", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Guatemala", "Guatemala Film Commission (INGUAT) Production Facilitation"),
    ("gy_film_commission", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Guyana", "Guyana Tourism Authority Film Production Support"),
    ("id_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Indonesia", "id_film_incentive"),
    ("in_national_film", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "India", "India NFDC and State Incentives"),
    ("is_film_reimbursement", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Iceland", "Icelandic Film Reimbursement Scheme"),
    ("is_film_reimbursement_scheme", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Iceland", "Icelandic Film Reimbursement Scheme [runtime slug of is_film_reimbursement]"),
    ("it_tax_credit_foreign", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Italy", "Italian Tax Credit for Foreign Productions"),
    ("jm_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Jamaica", "Jamaica Entertainment Industry Incentive Programme"),
    ("ke_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Kenya", "ke_film_incentive"),
    ("kw_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Kuwait", "kw_film_incentive"),
    ("kz_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Kazakhstan", "kz_film_incentive"),
    ("kz_investment_subsidy", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Kazakhstan", "kz_film_incentive [runtime slug of kz_film_incentive]"),
    ("lk_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Sri Lanka", "lk_film_incentive"),
    ("lt_film_centre_cash_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Lithuania", "Lithuanian Film Centre Production Cash Rebate [runtime slug of lt_film_incentive]"),
    ("lt_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Lithuania", "Lithuanian Film Centre Production Cash Rebate"),
    ("lu_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Luxembourg", "Film Fund Luxembourg — Tax Shelter & Production Rebate"),
    ("lu_filmfund_tax_shelter_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Luxembourg", "Film Fund Luxembourg — Tax Shelter & Production Rebate [runtime slug of lu_film_incentive]"),
    ("lv_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Latvia", "National Film Centre of Latvia Production Incentive"),
    ("lv_national_film_centre_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Latvia", "National Film Centre of Latvia Production Incentive [runtime slug of lv_film_incentive]"),
    ("ma_ccm_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Morocco", "CCM Morocco — Production Rebate"),
    ("me_cash_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Montenegro", "Film Centre of Montenegro Production Incentive [runtime slug of me_film_incentive]"),
    ("me_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Montenegro", "Film Centre of Montenegro Production Incentive"),
    ("mk_cash_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "North Macedonia", "Macedonian Film Agency (MFA) Cash Rebate [runtime slug of mk_film_incentive]"),
    ("mk_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "North Macedonia", "Macedonian Film Agency (MFA) Cash Rebate"),
    ("mn_film_commission", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Mongolia", "mn_film_commission"),
    ("mv_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Maldives", "mv_film_incentive"),
    ("mx_eficine_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Mexico", "Mexico EFICINE (Article 226) and PROCINE Fund"),
    ("mz_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Mozambique", "mz_film_incentive"),
    ("new_zealand_screen_production_grant_—_international_post_vfx", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "New Zealand", "New Zealand Screen Production Grant — International Post/VFX"),
    ("ng_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Nigeria", "ng_film_incentive"),
    ("nl_film_production_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Netherlands", "Netherlands Film Production Incentive (NFPI) [runtime slug of nl_nfpi]"),
    ("nl_hbf", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Netherlands", "Hubert Bals Fund (IFFR) — Development and Production Fund"),
    ("nl_nfpi", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Netherlands", "Netherlands Film Production Incentive (NFPI)"),
    ("nohfc_production_fund", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Ontario", "Northern Ontario Heritage Fund — Production Fund"),
    ("nordic_ftvf", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Nordic Region / Nordic Region", "Nordisk Film & TV Fond"),
    ("om_film_commission", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Oman", "om_film_commission"),
    ("ontario_computer_animation_and_special_effects_tax_credit_ocase", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Ontario", "Ontario Computer Animation and Special Effects Tax Credit (OCASE)"),
    ("or_opif", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / Oregon", "Oregon Production Investment Fund (OPIF)"),
    ("pa_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Panama", "Panama Film Commission Production Facilitation"),
    ("pe_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Peru", "Peru DAFO Film Production Support"),
    ("pk_pfc_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Pakistan", "pk_pfc_rebate"),
    ("pl_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Poland", "Polish Film Institute (PISF) Cash Rebate"),
    ("pl_pisf_cash_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Poland", "Polish Film Institute (PISF) Cash Rebate [runtime slug of pl_film_incentive]"),
    ("proposed_australia_producer_offset_separate_statutory_program", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Australia", "Producer Offset (separate statutory program)"),
    ("proposed_canada_film_or_video_production_services_tax_credit_pstc", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada", "Film or Video Production Services Tax Credit (PSTC)"),
    ("proposed_colombia_cina_audiovisual_investment_certificate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Colombia", "CINA Audiovisual Investment Certificate"),
    ("proposed_netherlands_netherlands_film_production_incentive_high_end_series", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Netherlands", "Netherlands Film Production Incentive — High-End Series"),
    ("proposed_spain_basque_country_basque_provincial_audiovisual_tax_credits", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Spain / Basque Country", "Basque Provincial Audiovisual Tax Credits"),
    ("proposed_spain_canary_islands_canary_islands_foreign_production_tax_deduction", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Spain / Canary Islands", "Canary Islands Foreign Production Tax Deduction"),
    ("proposed_spain_navarre_navarre_audiovisual_production_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Spain / Navarre", "Navarre Audiovisual Production Tax Credit"),
    ("proposed_united_arab_emirates_abu_dhabi_abu_dhabi_35_production_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United Arab Emirates / Abu Dhabi", "Abu Dhabi 35++ Production Rebate"),
    ("proposed_united_kingdom_enhanced_avec_independent_film_tax_credit_iftc", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United Kingdom", "Enhanced AVEC / Independent Film Tax Credit (IFTC)"),
    ("proposed_united_states_arkansas_digital_product_and_motion_picture_industry_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / Arkansas", "Digital Product and Motion Picture Industry Incentive"),
    ("proposed_united_states_missouri_motion_media_production_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / Missouri", "Motion Media Production Tax Credit"),
    ("proposed_united_states_montana_media_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / Montana", "MEDIA Tax Credit"),
    ("proposed_united_states_new_jersey_garden_state_film_and_digital_media_jobs_act_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / New Jersey", "Garden State Film and Digital Media Jobs Act — Film Credit"),
    ("proposed_united_states_new_york_empire_state_independent_film_production_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / New York", "Empire State Independent Film Production Credit"),
    ("proposed_united_states_new_york_film_tax_credit_post_production", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / New York", "Film Tax Credit — Post-Production"),
    ("proposed_united_states_ohio_ohio_motion_picture_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / Ohio", "Ohio Motion Picture Tax Credit"),
    ("proposed_united_states_west_virginia_west_virginia_film_production_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / West Virginia", "West Virginia Film Production Tax Credit"),
    ("pt_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Portugal", "Portugal Film Commission Incentive / IAPMEI"),
    ("qa_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Qatar", "qa_film_incentive"),
    ("qc_film_production", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Canada / Quebec", "Quebec Film and Television Production Tax Credit"),
    ("ro_cnc_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Romania", "Romanian Film Office Cash Rebate"),
    ("ro_film_office_cash_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Romania", "Romanian Film Office Cash Rebate [runtime slug of ro_cnc_rebate]"),
    ("rs_film_commission_cash_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Serbia", "Serbia Film Commission Cash Rebate [runtime slug of rs_film_rebate]"),
    ("rs_film_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Serbia", "Serbia Film Commission Cash Rebate"),
    ("sc_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Seychelles", "sc_film_incentive"),
    ("se_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Sweden", "Sweden Film Commission Production Rebate"),
    ("se_production_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Sweden", "Sweden Film Commission Production Rebate [runtime slug of se_film_incentive]"),
    ("sk_avf_production_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Slovakia", "Slovak Audiovisual Fund (AVF) Production Incentive [runtime slug of sk_film_incentive]"),
    ("sk_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Slovakia", "Slovak Audiovisual Fund (AVF) Production Incentive"),
    ("sn_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Senegal", "sn_film_incentive"),
    ("th_prd_foreign_digital_content_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Thailand", "Foreign Digital Content Production Incentive"),
    ("tourism_ireland___fáilte_ireland_production_support", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Ireland", "Tourism Ireland / Fáilte Ireland Production Support"),
    ("ug_film_commission", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Uganda", "ug_film_commission"),
    ("us_al_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Alabama", "Alabama Film Incentive"),
    ("us_az_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Arizona", "Arizona Motion Picture Production Program"),
    ("us_az_motion_picture_production", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Arizona", "Arizona Motion Picture Production Program [runtime slug of us_az_film_credit]"),
    ("us_co_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Colorado", "Colorado Film Incentive"),
    ("us_ct_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Connecticut", "Connecticut Film Tax Credit"),
    ("us_ct_film_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Connecticut", "Connecticut Film Tax Credit [runtime slug of us_ct_film_credit]"),
    ("us_hi_film_digital_media_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Hawaii", "Hawaii Film and Digital Media Income Tax Credit [runtime slug of us_hi_film_tax_credit]"),
    ("us_hi_film_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Hawaii", "Hawaii Film and Digital Media Income Tax Credit"),
    ("us_il_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Illinois", "Illinois Film Tax Credit"),
    ("us_il_film_production_services_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Illinois", "Illinois Film Tax Credit [runtime slug of us_il_film_credit]"),
    ("us_itvs_fund", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States", "ITVS International Documentary Fund"),
    ("us_ky_keiia", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Kentucky", "Kentucky Entertainment Industry Incentive Act (KEIIA)"),
    ("us_ma_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Massachusetts", "Massachusetts Film Tax Credit"),
    ("us_ma_film_tax_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Massachusetts", "Massachusetts Film Tax Credit [runtime slug of us_ma_film_credit]"),
    ("us_ms_advantage_film_program", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Mississippi", "Mississippi Advantage Film Program [runtime slug of us_ms_film_credit]"),
    ("us_ms_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Mississippi", "Mississippi Advantage Film Program"),
    ("us_nc_film_entertainment_grant", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — North Carolina", "North Carolina Film & Entertainment Grant [runtime slug of us_nc_film_grant]"),
    ("us_nc_film_grant", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — North Carolina", "North Carolina Film & Entertainment Grant"),
    ("us_nv_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Nevada", "Nevada Film Incentive Program [runtime slug of us_nv_film_incentive]"),
    ("us_nv_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Nevada", "Nevada Film Incentive Program"),
    ("us_ok_film_enhancement_rebate", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Oklahoma", "Oklahoma Film Enhancement Rebate [runtime slug of us_ok_ofer]"),
    ("us_ok_ofer", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Oklahoma", "Oklahoma Film Enhancement Rebate"),
    ("us_or_opif", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / Oregon", "Oregon Production Investment Fund (OPIF) [runtime slug of or_opif]"),
    ("us_pa_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Pennsylvania", "Pennsylvania Film Production Tax Credit"),
    ("us_pa_film_production_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Pennsylvania", "Pennsylvania Film Production Tax Credit [runtime slug of us_pa_film_credit]"),
    ("us_pr_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Puerto Rico", "Puerto Rico Film Industry Economic Incentives Act"),
    ("us_pr_film_incentives_act", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Puerto Rico", "Puerto Rico Film Industry Economic Incentives Act [runtime slug of us_pr_film_incentive]"),
    ("us_sc_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — South Carolina", "South Carolina Film Production Credit"),
    ("us_sc_film_production_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — South Carolina", "South Carolina Film Production Credit [runtime slug of us_sc_film_credit]"),
    ("us_sundance_doc", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States", "Sundance Institute — Documentary Fund"),
    ("us_tn_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Tennessee", "Tennessee Film Entertainment Incentives"),
    ("us_tn_performance_grant", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Tennessee", "Tennessee Film Entertainment Incentives [runtime slug of us_tn_film_incentive]"),
    ("us_tx_miip", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Texas", "Texas Moving Image Industry Incentive Program (MIIP)"),
    ("us_ut_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Utah", "Utah Motion Picture Incentive Program"),
    ("us_ut_motion_picture_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Utah", "Utah Motion Picture Incentive Program [runtime slug of us_ut_film_incentive]"),
    ("us_va_film_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Virginia", "Virginia Motion Picture Production Tax Credit"),
    ("us_va_motion_picture_credit", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Virginia", "Virginia Motion Picture Production Tax Credit [runtime slug of us_va_film_credit]"),
    ("us_wa_motion_picture_competitiveness", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Washington", "Washington State Motion Picture Competitiveness Program [runtime slug of us_wa_mpcp]"),
    ("us_wa_mpcp", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "United States / United States — Washington", "Washington State Motion Picture Competitiveness Program"),
    ("uy_xxi_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Uruguay", "Uruguay XXI Film Incentive"),
    ("uz_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Uzbekistan", "uz_film_incentive"),
    ("vn_film_incentive", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Vietnam", "vn_film_incentive"),
    ("zm_film_commission", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Zambia", "zm_film_commission"),
    ("zw_film_commission", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "Zimbabwe", "zw_film_commission"),
)

COVERAGE_REGISTRY: dict[str, AuthorityCoverageRecord] = {
    r[0]: AuthorityCoverageRecord(*r) for r in _ROWS
}

#: Slugs blocked from economic candidacy. Consulted by the served runtime.
BLOCKED_SLUGS: frozenset[str] = frozenset(
    slug for slug, rec in COVERAGE_REGISTRY.items() if rec.blocks_economic_candidacy
)


#: canonical_id -> runtime program_slug, for records the canonical corpus
#: names under a different spelling than the served runtime. Both keys are
#: present in COVERAGE_REGISTRY so neither spelling can price.
CANONICAL_RUNTIME_SLUG_BINDINGS: dict[str, str] = {
    "ae_dpip": "ae_dxb_dpip",
    "al_film_incentive": "al_cash_rebate",
    "bc_pstc": "ca_bc_pstc",
    "bg_film_incentive": "bg_film_encouragement_act_rebate",
    "ca_film_30": "us_ca_film_credit",
    "ca_mb_fvptc": "ca_mb_film_video_credit",
    "ca_nb_film_credit": "ca_nb_film_tax_credit",
    "ca_ns_pif": "ca_ns_production_incentive_fund",
    "ca_sk_production_grant": "ca_sk_creative_saskatchewan_grant",
    "co_film_colombia": "co_film_in_colombia",
    "do_film_incentive": "do_film_commission_incentive",
    "ee_film_incentive": "ee_film_estonia_rebate",
    "fi_film_incentive": "fi_business_finland_incentive",
    "is_film_reimbursement": "is_film_reimbursement_scheme",
    "jp_film_incentive": "jp_vipo_location_incentive",
    "kr_film_incentive": "kr_kofic_location_incentive",
    "kz_film_incentive": "kz_investment_subsidy",
    "la_film_production": "us_la_film_incentive",
    "lt_film_incentive": "lt_film_centre_cash_rebate",
    "lu_film_incentive": "lu_filmfund_tax_shelter_rebate",
    "lv_film_incentive": "lv_national_film_centre_incentive",
    "me_film_incentive": "me_cash_rebate",
    "mk_film_incentive": "mk_cash_rebate",
    "nl_nfpi": "nl_film_production_incentive",
    "nm_film_production": "us_nm_film_credit",
    "on_opstc": "ca_on_opstc",
    "or_opif": "us_or_opif",
    "pl_film_incentive": "pl_pisf_cash_rebate",
    "proposed_canada_film_or_video_production_services_tax_credit_pstc": "ca_federal_pstc",
    "proposed_united_arab_emirates_abu_dhabi_abu_dhabi_35_production_rebate": "ae_ad_film_rebate",
    "ro_cnc_rebate": "ro_film_office_cash_rebate",
    "rs_film_rebate": "rs_film_commission_cash_rebate",
    "sa_sfc_rebate": "sa_film_commission_rebate",
    "se_film_incentive": "se_production_rebate",
    "si_film_incentive": "si_cash_rebate",
    "sk_film_incentive": "sk_avf_production_incentive",
    "tt_film_incentive": "tt_production_expenditure_rebate",
    "us_az_film_credit": "us_az_motion_picture_production",
    "us_ct_film_credit": "us_ct_film_tax_credit",
    "us_hi_film_tax_credit": "us_hi_film_digital_media_credit",
    "us_il_film_credit": "us_il_film_production_services_credit",
    "us_ma_film_credit": "us_ma_film_tax_credit",
    "us_md_film_credit": "us_md_film_production_activity_credit",
    "us_mn_film_credit": "us_mn_film_production_credit",
    "us_ms_film_credit": "us_ms_advantage_film_program",
    "us_nc_film_grant": "us_nc_film_entertainment_grant",
    "us_nv_film_incentive": "us_nv_film_credit",
    "us_ok_ofer": "us_ok_film_enhancement_rebate",
    "us_pa_film_credit": "us_pa_film_production_credit",
    "us_pr_film_incentive": "us_pr_film_incentives_act",
    "us_sc_film_credit": "us_sc_film_production_credit",
    "us_tn_film_incentive": "us_tn_performance_grant",
    "us_ut_film_incentive": "us_ut_motion_picture_incentive",
    "us_va_film_credit": "us_va_motion_picture_credit",
    "us_wa_mpcp": "us_wa_motion_picture_competitiveness",
}


def get_coverage_status(program_slug: str | None) -> AuthorityCoverageRecord | None:
    """None == PRICEABLE_VALIDATED (absence is never an exclusion)."""
    if program_slug is None:
        return None
    return COVERAGE_REGISTRY.get(program_slug)


def blocks_economic_candidacy(program_slug: str | None) -> bool:
    """The single predicate the served runtime calls. True => this program may
    not price, may not contribute NPC benefit, and may not be ranked as an
    economic candidate."""
    rec = get_coverage_status(program_slug)
    return rec is not None and rec.blocks_economic_candidacy


def coverage_state(program_slug: str | None) -> str:
    rec = get_coverage_status(program_slug)
    return rec.state if rec is not None else "PRICEABLE_VALIDATED"


def is_covered_unpriceable(program_slug: str) -> bool:
    """Back-compat alias retained for the Consolidated Global Remediation tests."""
    return blocks_economic_candidacy(program_slug)

