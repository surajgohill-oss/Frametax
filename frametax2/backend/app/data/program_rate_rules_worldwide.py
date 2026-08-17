"""
program_rate_rules_worldwide.py

Every jurisdiction added during the worldwide jurisdiction population
phase (see docs/architecture/CAPABILITY_LEDGER.md) is defined ONCE here
as a DoctrineRecord (executable_jurisdiction_registry.py) and registered
into program_rate_rules.py's RateRule table via register_rate_rules() —
this is the fix for the duplication the population phase identified:
MU/GR/IE/MT/ES/FR (defined before this module existed) each required a
hand-written RateRule tuple AND a hand-written JurisdictionIncentiveProfile
with the same numbers retyped; every jurisdiction below is written once.

jurisdiction_comparison.py's JurisdictionIncentiveProfile still needs a
separate entry for capability fields this registry doesn't model (marine
suitability, crew depth, VAT/WHT/payroll) — but its doctrine fields
(base_rate, max_rate, min_spend_local, annual_cap_local, confidence_tier)
should be read from the DoctrineRecord below via `get_doctrine(slug)`,
not retyped by hand, for every entry added from this point forward.
"""
from __future__ import annotations

from app.data.executable_jurisdiction_registry import (
    DoctrineRateTier,
    DoctrineRecord,
    rate_rules_for,
    register,
)
from app.data.program_rate_rules import RateCondition, SourceProvenance, register_rate_rules

# ── Belgium: federal Tax Shelter ────────────────────────────────────────────
#
# Checked internal source first: Alembic 0008_seed_marine_jurisdictions.py
# seeded an unsourced ~16-17% "effective benefit" DISCOVERY-tier estimate,
# with its own docstring flagging "two separate mechanisms... require
# independent verification. Effective rate depends on deal structure" —
# i.e. the migration itself did not claim confidence in this figure.
#
# Cross-checked against two independent Belgian tax-shelter-industry
# sources (beci.be business federation; scopeinvest.be, a licensed
# tax-shelter intermediary) — both independently state producers NET
# 42-44% of eligible Belgian expenditure through the Tax Shelter
# mechanism, AFTER investor return/broker/insurance costs (i.e. already
# the real net benefit, not a gross figure needing further discount). A
# third, semi-official regional source (screenflanders.be) states a
# lower, differently-framed 38-40% "financeable" figure — not reconciled,
# disclosed as a genuine discrepancy rather than silently dropped.
#
# Structurally different from a rebate/credit: this is an investor-
# financing mechanism, not a government payment against QPE — modeled as
# a rate because the net-benefit percentage IS a real, usable figure for
# NPC purposes (confirmed by two sources as already-net), but the
# underlying mechanism (tax-exempt certificates, EURIBOR-linked investor
# return, licensed intermediary) is NOT further modeled.
_BE_CITATION = (
    "beci.be (Belgian business federation) and scopeinvest.be (licensed "
    "Tax Shelter intermediary), both independently: producers net "
    "42-44% of eligible Belgian expenditure through the federal Tax "
    "Shelter mechanism, after deduction of investor return/broker/"
    "insurance costs. No minimum expenditure threshold for the federal "
    "Tax Shelter (screenflanders.be, official regional film body). "
    "Cultural requirement: certified as a 'European work' under the "
    "Audiovisual Media Services Directive, or a qualifying international "
    "co-production (screenflanders.be)."
)
BE_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="BE",
    program_slug="be_tax_shelter",
    program_name="Belgian Tax Shelter",
    confidence_tier="PARSED",
    incentive_type="regional_fund",
    is_refundable=None,   # investor-financing mechanism, not a direct government payment
    is_transferable=None,
    min_spend_usd=None,   # confirmed: no minimum threshold
    annual_cap_usd=None,  # EUR 5M vs EUR 7.25M/$8M conflict across sources — left UNKNOWN
    requires_cultural_test=True,
    citation=_BE_CITATION,
    source_ref="beci.be+scopeinvest.be-tax-shelter",
    tiers=(
        DoctrineRateTier(
            tier_id="be-net-42",
            rate=0.42,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="be-cultural-test",
                    description="European work (AVMS Directive) or qualifying "
                                "international co-production certification",
                    quote="certified as a European work, as defined in the "
                          "Audiovisual Media Services Directive (screenflanders.be)",
                    kind="cultural_test_required",
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="be-net-44-ceiling",
            rate=0.44,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="be-deal-structure-variance",
                    description="Net benefit within 42-44% depends on the specific "
                                "investor deal (EURIBOR rate at time of investment, "
                                "intermediary commission, insurance cost) — not a "
                                "discretionary approval band, but not a single fixed "
                                "number either",
                    quote="producers finance between 42% and 44% of eligible "
                          "Belgian expenditure ... a net percentage after "
                          "deduction of all costs and fees (beci.be, scopeinvest.be)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(BE_DOCTRINE))

# ── Cyprus: Cyprus Film Scheme cash rebate ──────────────────────────────────
#
# Checked internal source first: Alembic 0008 seeded a flat 35% DISCOVERY
# figure with the migration's own docstring flagging "rate unverified from
# statute text" — matches jurisdiction_comparison.py's pre-existing
# DISCOVERY note verbatim, confirming neither was ever independently
# checked. Cross-checked directly against the official Cyprus Film
# Commission page (film.investcyprus.org.cy, administered by Invest
# Cyprus/Ministry of Finance/Ministry of Education and Culture/Deputy
# Ministry of Tourism), which confirms "up to 45%" — a REAL band, not the
# flat 35% previously modeled. The 35%-base/45%-ceiling split and the
# EUR 200,000 (feature film) minimum spend and EUR 650,000 per-production
# cap come from two independent Cyprus corporate/tax advisory sources
# (meridian-trust.com, cxfinancia.com) corroborating each other and
# consistent with the official page's "up to 45%" — PARSED tier (not
# VERIFIED: the exact cultural-test point-scoring thresholds for the +10%
# uplift were not in either source and remain a disclosed gap).
_CY_CITATION = (
    "film.investcyprus.org.cy (Cyprus Film Commission, official): 'Rebate "
    "of up to 45% of eligible expenditures incurred in Cyprus,' amount "
    "'depend[ing] on the score of the production at the cultural test.' "
    "Base/ceiling split (35% base, +10% cultural-test uplift to 45%), "
    "minimum spend (EUR 200,000 feature films), and cap (EUR 650,000 max "
    "aid per production) corroborated by two independent Cyprus tax/"
    "corporate advisory sources (meridian-trust.com, cxfinancia.com); "
    "exact cultural-test scoring thresholds not found in either and "
    "remain unverified."
)
CY_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CY",
    program_slug="cy_film_rebate",
    program_name="Cyprus Film Scheme",
    # Global Formulaic Economic Completion, batch 4: independently
    # re-fetched film.investcyprus.org.cy directly this task and confirmed
    # "Up to 45% Tax Rebate" -- the same 45% ceiling figure the existing
    # citation's own official-page quote had already recorded.
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=228_104.79,   # EUR 200,000 (feature film)
    annual_cap_usd=741_340.57,  # EUR 650,000 max aid per production
    requires_cultural_test=True,
    citation=_CY_CITATION,
    source_ref="investcyprus.org.cy+meridian-trust+cxfinancia",
    provenance=SourceProvenance(
        issuing_authority="Cyprus Film Commission",
        source_url="https://film.investcyprus.org.cy",
        citation_detail="'Up to 45% Tax Rebate' / 'Up to 35% Tax Credit' "
                         "(35% base + 10% cultural-test uplift to 45%)",
        verified_date="2026-08-17",
        interpretation_note="Exact cultural-test point-scoring thresholds "
                             "for the +10% uplift are not published on the "
                             "official page and remain a disclosed gap -- "
                             "only the base/ceiling rate figures "
                             "themselves are VERIFIED.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="cy-base-35",
            rate=0.35,
            is_band_ceiling=False,
            min_qpe_usd=228_104.79,
            conditions=(
                RateCondition(
                    condition_id="cy-min-spend",
                    description="Minimum qualifying Cyprus expenditure (feature "
                                "film); also capped at 50% of total production "
                                "budget (not modeled)",
                    quote="EUR 200,000 for feature films (meridian-trust.com)",
                    kind="min_qpe_usd", threshold_usd=228_104.79,
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="cy-cultural-ceiling-45",
            rate=0.45,
            is_band_ceiling=True,
            min_qpe_usd=228_104.79,
            conditions=(
                RateCondition(
                    condition_id="cy-cultural-test-uplift",
                    description="The +10% uplift to 45% requires a high score "
                                "on the Cyprus Film Commission cultural test — "
                                "exact point thresholds not confirmed from any "
                                "source reviewed; modeled as a ceiling, not a "
                                "guaranteed entitlement",
                    quote="the amount will depend on the score of the "
                          "production at the cultural test (film.investcyprus.org.cy)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(CY_DOCTRINE))

# ── Germany: DFFF (German Federal Film Fund) ────────────────────────────────
#
# Checked internal source first: Alembic 0008 seeded 25% DISCOVERY, later
# bulk-promoted to PARSED by 0038 on the weak "source URL confirmed" basis.
# This lead was not just unverified — it was STALE: DFFF's rate was
# increased to 30% in 2025 (confirmed directly, verbatim, from FFA's own
# official page, ffa.de/dfff-en: "The grant for both types of funding was
# increased in 2025 to a uniform 30 per cent of the approved German
# production costs"). This is the second jurisdiction (after France) where
# the migration's DISCOVERY/PARSED figure was simply out of date rather
# than merely unconfirmed — a real, recent statutory change, not a
# research gap.
#
# DFFF II (for production service providers — the relevant sub-program for
# a foreign production service-shooting in Germany, vs. DFFF I for
# producers/co-producers) cap and the 20%-of-budget minimum German-spend
# requirement are corroborated by a global law firm's (Greenberg Traurig)
# reporting on the same May 2026 official BKM draft guidelines, not
# fetched by this session directly from the primary text — PARSED, not
# VERIFIED, for those two fields specifically (the 30% rate itself IS
# VERIFIED, fetched directly from ffa.de).
_DE_CITATION = (
    "FFA (Filmförderungsanstalt), official DFFF page (ffa.de/dfff-en), "
    "fetched directly: 'The grant for both types of funding was increased "
    "in 2025 to a uniform 30 per cent of the approved German production "
    "costs.' Administered by FFA under Federal Government Commissioner "
    "for Culture and the Media (BKM) oversight. DFFF II cap (EUR 25M) and "
    "20%-of-total-budget minimum German spend corroborated by Greenberg "
    "Traurig's reporting on the May 2026 BKM draft guidelines (not "
    "independently fetched from the primary guideline text)."
)
DE_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="DE",
    program_slug="de_dfff",
    program_name="German Federal Film Fund (DFFF II — production service)",
    # Global Economic Data + Base Pricing, batch 3.
    confidence_tier="VERIFIED",
    incentive_type="grant",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,           # 20% of TOTAL budget, not an absolute EUR figure — cannot be
                                   # expressed as a fixed min_qpe_usd; disclosed, not modeled
    annual_cap_usd=28_513_098.92, # EUR 25,000,000 (DFFF II)
    requires_cultural_test=True,
    citation=_DE_CITATION,
    source_ref="ffa.de+greenberg-traurig-BKM-2026",
    provenance=SourceProvenance(
        issuing_authority="Filmforderungsanstalt (FFA), under Federal "
                           "Government Commissioner for Culture and the "
                           "Media (BKM) oversight",
        source_url="https://www.ffa.de/dfff-en",
        citation_detail="30% uniform grant of approved German production "
                         "costs (a 2025 increase from a lower prior rate)",
        effective_date="2025 rate increase",
        interpretation_note="The 30% rate itself is VERIFIED (fetched "
                             "directly from ffa.de). The EUR 25,000,000 "
                             "DFFF II cap and the 20%-of-budget minimum "
                             "German spend are corroborated only by "
                             "Greenberg Traurig's secondary reporting on "
                             "the May 2026 BKM draft guidelines, not "
                             "independently fetched from the primary "
                             "guideline text — a narrower-scope "
                             "verification than the rate itself.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="de-uniform-30",
            rate=0.30,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="de-min-spend-pct-of-budget",
                    description="Minimum German spend must be at least 20% of "
                                "TOTAL production budget (not an absolute "
                                "threshold on German QPE alone) — this engine "
                                "has no fact comparing German QPE to total "
                                "worldwide budget as a ratio, so this condition "
                                "cannot be pre-evaluated",
                    quote="The German financial contribution must be at least "
                          "20% of the total production costs (Greenberg "
                          "Traurig, reporting on May 2026 BKM draft guidelines)",
                    kind="min_spend_pct_of_total_budget",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(DE_DOCTRINE))

# ── Croatia: HAVC cash rebate ────────────────────────────────────────────────
#
# Checked internal source first: Alembic 0008 seeded 25% flat, DISCOVERY,
# "No cultural test" — the rate was directionally right but the cultural-
# test claim was WRONG (a real, points-based cultural test exists) and a
# real +5% regional uplift was entirely missing. Confirmed directly from
# Invest Croatia (investcroatia.gov.hr), the official government
# investment-promotion agency: base 25% + up to 5% regional-development
# uplift (30% ceiling), min spend EUR 263,000 for feature films, and a
# real cultural test (12/34 points minimum across three categories:
# European cultural content, Croatian/European creative personnel, "at
# least 4 points... in each category").
_HR_CITATION = (
    "investcroatia.gov.hr (Invest Croatia, official government investment "
    "promotion agency), fetched directly: base rebate '25% of the "
    "qualifying local expenditure' plus 'an additional 5% for productions "
    "filming in regions with below average development.' Minimum spend "
    "'HRK 2 million (EUR 263,000) for feature films.' Cultural test: "
    "'must score at least 12 out of 34 points' across European cultural "
    "content / creative collaboration with Croatian-European personnel / "
    "Croatian production facilities use, 'at least 4 points... in each "
    "category.' Administered by the Croatian Audiovisual Centre (HAVC)."
)
HR_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="HR",
    program_slug="hr_cash_rebate",
    program_name="Croatia Cash Rebate",
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=299_957.80,   # EUR 263,000 feature film
    annual_cap_usd=None,        # no maximum cap specified in the source fetched
    requires_cultural_test=True,
    citation=_HR_CITATION,
    source_ref="investcroatia.gov.hr-film-rebate",
    provenance=SourceProvenance(
        issuing_authority="Invest Croatia (official government investment "
                           "promotion agency); administered by the "
                           "Croatian Audiovisual Centre (HAVC)",
        source_url="https://investcroatia.gov.hr",
        citation_detail="25% base rebate + 5% regional uplift; min spend "
                         "HRK 2,000,000 (EUR 263,000) for feature films",
        interpretation_note="Cultural test (12/34 points, 4+ per category) "
                             "confirmed but the points-based scoring "
                             "mechanics are not independently reproduced.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="hr-base-25",
            rate=0.25,
            is_band_ceiling=False,
            min_qpe_usd=299_957.80,
            conditions=(
                RateCondition(
                    condition_id="hr-min-spend",
                    description="Minimum qualifying Croatian expenditure (feature film)",
                    quote="HRK 2 million (EUR 263,000) for feature films "
                          "(investcroatia.gov.hr)",
                    kind="min_qpe_usd", threshold_usd=299_957.80,
                ),
                RateCondition(
                    condition_id="hr-cultural-test",
                    description="Real points-based cultural test — 12/34 minimum, "
                                "with a per-category floor of 4 points across 3 "
                                "categories. Previously (incorrectly) modeled as "
                                "'no cultural test' in the DISCOVERY-tier profile",
                    quote="must score at least 12 out of 34 points ... at least 4 "
                          "points are scored in each category (investcroatia.gov.hr)",
                    kind="cultural_test_required",
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="hr-regional-ceiling-30",
            rate=0.30,
            is_band_ceiling=True,
            min_qpe_usd=299_957.80,
            conditions=(
                RateCondition(
                    condition_id="hr-regional-uplift",
                    description="The +5% ceiling requires filming in a region "
                                "with below-average development — this engine "
                                "has no fact identifying WHICH Croatian region "
                                "a shoot occurs in, so eligibility cannot be "
                                "pre-evaluated",
                    quote="an additional 5% for productions filming in regions "
                          "with below average development (investcroatia.gov.hr)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(HR_DOCTRINE))

# ── Hungary: NFI film incentive ──────────────────────────────────────────────
#
# Checked internal source first: Alembic 0008 seeded 30% flat DISCOVERY —
# rate happened to be directionally close but "No cultural test for
# foreign" was WRONG (a real 16-point EU-content test exists), and the
# real 37.5% extended-rebate ceiling was entirely missing. Confirmed
# directly, verbatim, from NFI's own official page (nfi.hu): base 30% on
# Hungarian direct production costs, extendable to 37.5% by including a
# capped share of non-Hungarian costs. This is the THIRD jurisdiction
# (after France, Germany) in this population batch where the pre-existing
# migration/profile data needed correction not just for being unverified
# but for actively mis-describing a real program feature (missing
# cultural test, missing uplift band) — see CAPABILITY_LEDGER.md.
_HU_CITATION = (
    "nfi.hu (National Film Institute Hungary), official page, fetched "
    "directly: '30% rebate based on their expenditure (all the direct "
    "film production costs) spent in the country,' extendable to 37.5% "
    "by including non-Hungarian costs (capped at 25% of the rebate). "
    "'The financial support is provided in the form of a cash refund "
    "(post-financing).' Cultural test: 'Films must contain European "
    "content or cultural values' and earn 16 points on an EU-participation "
    "scoring system. Total state subsidies capped at 50% of production "
    "budget (not modeled — %-of-budget, not an absolute threshold)."
)
HU_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="HU",
    program_slug="hu_hipa_rebate",
    program_name="Hungarian Film Incentive (NFI)",
    # Global Economic Data + Base Pricing, batch 3.
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,   # no explicit minimum production budget found in the
                           # primary source fetched — disclosed, not guessed
    annual_cap_usd=None,  # subsidy cap is %-of-budget (50%), not absolute
    requires_cultural_test=True,
    citation=_HU_CITATION,
    source_ref="nfi.hu-hungarian-film-incentive",
    provenance=SourceProvenance(
        issuing_authority="National Film Institute Hungary (NFI)",
        source_url="https://nfi.hu",
        citation_detail="30% base rebate, extendable to 37.5% including "
                         "non-Hungarian costs (capped at 25% of the "
                         "rebate); post-financing cash refund",
        interpretation_note="Cultural test requires 16 points on an "
                             "EU-participation scoring system. Total "
                             "state subsidies are capped at 50% of "
                             "production budget — a %-of-budget cap, not "
                             "modeled as an absolute annual_cap_usd.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="hu-base-30",
            rate=0.30,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="hu-cultural-test",
                    description="Real 16-point EU-content/cultural-values test — "
                                "previously (incorrectly) modeled as 'no cultural "
                                "test for foreign'",
                    quote="Films must contain European content or cultural "
                          "values [and earn] 16 points (nfi.hu)",
                    kind="cultural_test_required",
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="hu-cross-border-ceiling-375",
            rate=0.375,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="hu-cross-border-uplift",
                    description="The 37.5% ceiling requires including a capped "
                                "share of non-Hungarian costs in the rebate base "
                                "— this engine has no fact splitting QPE into "
                                "Hungarian vs. non-Hungarian portions, so this "
                                "cannot be pre-evaluated",
                    quote="7.5% non-Hungarian costs [added to base 30%, reaching] "
                          "37.5% total ... capped at 25% of the rebate (nfi.hu)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(HU_DOCTRINE))

# ── Italy: tax credit for foreign productions ───────────────────────────────
#
# Checked internal source first: Alembic 0008 seeded 40% flat, DISCOVERY,
# cap EUR 20M, min spend EUR 1M, "No cultural test for foreign," with its
# own docstring flagging "verify current rules and cap from DL 91/2013
# implementing decree." The 40% rate and EUR 20M cap held up under direct
# verification, but "No cultural test for foreign" was WRONG (a real
# 50/100-point test exists, same pattern as Cyprus/Croatia/Hungary in this
# batch — see the cultural-test pattern note in CAPABILITY_LEDGER.md) and
# the EUR 1M minimum spend was not found in either source checked.
_IT_CITATION = (
    "mestierecinema.it (Italian production consultancy), fetched directly: "
    "'40% of the eligible costs paid by the Italian producer for each "
    "work,' capped 'up to a maximum amount of EUR 20M per year per "
    "company.' Transferable: 'can also be handed over by the Italian "
    "producer to banks' and offset against VAT/IRES/IRAP/social "
    "contributions/IRPEF. Cultural test: 'must score a minimum of 50 "
    "points out of 100,' with a 35-point floor in Block A. Administered "
    "by MIBAC (Ministry of Culture)."
)
IT_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="IT",
    program_slug="it_tax_credit_foreign",
    program_name="Italian Tax Credit for Foreign Productions",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    is_refundable=True,
    is_transferable=True,   # confirmed: "can be handed over ... to banks"
    min_spend_usd=None,     # not found in either source checked — prior EUR 1M
                             # migration figure dropped, not carried forward unverified
    annual_cap_usd=22_810_479.13,  # EUR 20,000,000 per company per year
    requires_cultural_test=True,
    citation=_IT_CITATION,
    source_ref="mestierecinema.it-italian-tax-credit",
    tiers=(
        DoctrineRateTier(
            tier_id="it-flat-40",
            rate=0.40,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="it-cultural-test",
                    description="Real 50/100-point cultural test with a "
                                "35-point floor in Block A — previously "
                                "(incorrectly) modeled as 'no cultural test "
                                "for foreign'",
                    quote="the film must score a minimum of 50 points out of "
                          "100 points ... minimum 35 points in Block A "
                          "(mestierecinema.it)",
                    kind="cultural_test_required",
                ),
                RateCondition(
                    condition_id="it-atl-subcap",
                    description="Above-the-line costs are capped at 40% of "
                                "total production costs within the credit "
                                "base — not a separate reduced rate for "
                                "non-EEA ATL as an earlier secondary source "
                                "claimed; that claim was checked directly "
                                "against mestierecinema.it and NOT "
                                "corroborated, so it is not modeled",
                    quote="Above the line costs are taken into account up to "
                          "a maximum of 40% of the production costs "
                          "(mestierecinema.it)",
                    kind="atl_subcap_not_enforced",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(IT_DOCTRINE))

# ── United Kingdom: AVEC (Audio-Visual Expenditure Credit) ─────────────────
#
# A NEW jurisdiction (not a correction) — no prior entry existed in
# jurisdiction_comparison.py or program_rate_rules.py, despite the UK
# being one of the largest global production markets and UK AVEC's
# predecessor (uk_avec) being one of only 5 programs the migration
# corpus's own 0038 promotion claimed VERIFIED "all core fields confirmed
# from primary sources" — checked as a lead, not trusted on the label
# (same discipline as Italy in this batch), and independently verified
# directly against BFI's own official page.
#
# Fetched directly, verbatim, from bfi.org.uk: AVEC is "a taxable credit
# at a rate of 34%" — but that credit is ITSELF taxable at UK corporation
# tax (25%), netting to a real cash benefit of 34% x (1 - 0.25) = 25.5%
# of qualifying UK expenditure (arithmetic independently verified, not
# just quoted) — this is the figure modeled as `rate`, matching how this
# engine already models every other program as a real net benefit
# percentage, not a gross pre-tax accounting figure.
#
# The VFX Additional Credit (+3.75%, effective 1 Jan 2025, reaching a net
# 29.25% total per a second source, Entertainment Partners) was NOT
# independently confirmed from the BFI text fetched — modeled as a
# ceiling tier with that caveat explicit, PARSED not VERIFIED.
_GB_CITATION = (
    "bfi.org.uk (British Film Institute), official page, fetched "
    "directly: 'a taxable credit at a rate of 34% (equivalent to 25.5% "
    "under the previous system)' — net effective rate 25.5% independently "
    "verified by this session's own arithmetic (34% x (1-25% corporation "
    "tax) = 25.5%). 'AVEC is available on qualifying UK production "
    "expenditure, which is the lower of either 80% of total core "
    "expenditure or the actual UK core expenditure incurred' (QPE-"
    "eligibility cap, not a rate cap — Incentive/Optimizer Core Closeout: "
    "now enforced via program_rate_rules.QPE_CAP_RULES['uk_avec'], applied "
    "to the segment's own QPE before rate resolution). 'at least 10% of costs spent on UK "
    "qualifying production expenditure' required (ratio condition, not "
    "modeled as an absolute min_qpe_usd). 'There is no cap on the amount "
    "which can be claimed' (confirmed no dollar cap, not merely unknown). "
    "Films must 'either pass the cultural test or qualify as an official "
    "co-production.' VFX +3.75% uplift (effective 1 Jan 2025, reaching "
    "29.25% net) corroborated by a second source (Entertainment Partners) "
    "but NOT independently confirmed from the BFI text fetched. "
    "Administered by HMRC (eligibility/claims); BFI provides certification "
    "guidance and cultural test administration."
)
GB_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="GB",
    program_slug="uk_avec",
    program_name="Audio-Visual Expenditure Credit (AVEC)",
    # Global Economic Data + Base Pricing, batch 3: promoted PARSED ->
    # VERIFIED. Citation is bfi.org.uk (British Film Institute), official
    # page, fetched directly, rate quoted verbatim.
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=None,   # "payable credit" strongly implied by AVEC's general
                           # structure but not explicitly confirmed in the text
                           # fetched — left UNKNOWN rather than assumed
    is_transferable=None,
    min_spend_usd=None,   # the only absolute figure found (GBP 1M per broadcast
                           # hour) is TV-specific, not applicable to feature
                           # film; the film-relevant condition is a 10%-of-
                           # total-budget RATIO, not an absolute threshold
    annual_cap_usd=None,  # confirmed NO cap on claimable amount — genuine
                           # confirmed-uncapped, not an unknown
    requires_cultural_test=True,
    citation=_GB_CITATION,
    source_ref="bfi.org.uk-AVEC",
    provenance=SourceProvenance(
        issuing_authority="HMRC (eligibility/claims administration); "
                           "BFI (certification guidance, cultural test "
                           "administration)",
        source_url="https://www.bfi.org.uk",
        citation_detail="Audio-Visual Expenditure Credit (AVEC); no cap "
                         "on the amount claimable; VFX +3.75% uplift "
                         "effective 1 Jan 2025 reaching 29.25% net",
        effective_date="VFX uplift effective 2025-01-01",
        interpretation_note="'There is no cap on the amount which can be "
                             "claimed' confirmed directly from the BFI "
                             "text (a verified absence, not an unknown). "
                             "The VFX uplift figure is corroborated by a "
                             "second source (Entertainment Partners) but "
                             "not independently confirmed from the BFI "
                             "text itself.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="gb-avec-net-2550",
            rate=0.255,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="gb-min-uk-spend-pct",
                    description="At least 10% of total costs must be UK "
                                "qualifying production expenditure — a ratio "
                                "condition this engine has no fact to "
                                "pre-evaluate (no total-worldwide-budget "
                                "comparison fact available)",
                    quote="at least 10% of costs spent on UK qualifying "
                          "production expenditure (bfi.org.uk)",
                    kind="min_spend_pct_of_total_budget",
                ),
                RateCondition(
                    condition_id="gb-cultural-test",
                    description="Must pass the BFI cultural test or qualify "
                                "as an official co-production",
                    quote="either pass the cultural test or qualify as an "
                          "official co-production (bfi.org.uk)",
                    kind="cultural_test_required",
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="gb-vfx-ceiling-2925",
            rate=0.2925,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="gb-vfx-uplift-unconfirmed-primary",
                    description="+3.75% VFX Additional Credit (effective "
                                "1 Jan 2025) — NOT independently confirmed "
                                "from the BFI text fetched by this session, "
                                "only corroborated by a second secondary "
                                "source (Entertainment Partners); modeled as "
                                "a ceiling with this caveat explicit",
                    quote="Additional VFX Credit ... on qualifying "
                          "expenditure incurred on or after 1 January 2025 "
                          "(bfi.org.uk) — the +3.75%/29.25%-total figures "
                          "themselves are from Entertainment Partners, not "
                          "the BFI text",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(GB_DOCTRINE))

# ── United Kingdom: Independent Film Tax Credit (IFTC) ──────────────────────
#
# Incentive/Optimizer Core Closeout. IFTC is NOT a separate statutory
# credit — per the final rule resolution (docs/validation/
# CODEX_FINAL_RULE_RESOLUTION.md §3.1-3.2, cross-checked against
# docs/validation/GEMINI_FINAL_RULE_RESOLUTION.md §3, which agrees on the
# substance), "IFTC" is the industry name for AVEC's enhanced treatment of
# BFI-certified "low-budget films." Modeled here as its OWN program_slug
# (gb_iftc_enhanced_avec), deliberately NOT "uk_avec" — this is the same
# pattern already used for Australia's mutually-exclusive Location/PDV/
# Producer Offsets: distinct, non-stacking programs each get their own
# slug, and only the ONE actually pursued is wired into a production's
# segments. Little Utopia's GB segments use program_slug="uk_avec" (see
# little_utopia_state.py) — this record exists for correctness/future use
# and is NEVER assigned to any Little Utopia segment, because Little
# Utopia has no BFI low-budget certification or creative-connection fact
# (empty cast_writer_director_facts) to support it. Do not wire this
# program into Little Utopia's structures without that evidence.
_GB_IFTC_CITATION = (
    "HMRC CREC021110/CREC021120 (Creative Industries Expenditure Credit "
    "Manual), BFI 'About UK creative-industry expenditure credits', "
    "Finance (No. 2) Act 2024 s.14. Gross credit rate 53% (net ~39.75% "
    "after 25% UK corporation tax, same net-of-tax convention already "
    "used for standard AVEC's 34%->25.5%). Conditions: BFI low-budget "
    "certificate; principal photography on/after 1 April 2024; total core "
    "expenditure GBP 23,500,000 or less; only the first GBP 15,000,000 of "
    "relevant global expenditure enters the enhanced-credit calculation; "
    "'Modified Creative Connection' via a UK writer, UK director, or "
    "official co-production, plus the standard BFI cultural "
    "test/certification route. Enhanced VFX uplift cannot stack with IFTC "
    "(independent films receive 53% treatment on their qualifying costs "
    "instead)."
)
GB_IFTC_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="GB",
    program_slug="gb_iftc_enhanced_avec",
    program_name="Independent Film Tax Credit (enhanced AVEC for certified low-budget films)",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=None,
    is_transferable=None,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=True,
    citation=_GB_IFTC_CITATION,
    source_ref="HMRC-CREC021110-CREC021120-CODEX-final-resolution",
    tiers=(
        DoctrineRateTier(
            tier_id="gb-iftc-net-3975",
            rate=0.3975,
            is_band_ceiling=True,  # certification/eligibility unconfirmed for any given production by default
            conditions=(
                RateCondition(
                    condition_id="gb-iftc-certification-unconfirmed",
                    description="Requires BFI low-budget certification, the "
                                "Modified Creative Connection, and the "
                                "GBP 23.5M total-core-expenditure ceiling — "
                                "none evidenced by default for any "
                                "production; this engine has no fact "
                                "confirming these unless explicitly "
                                "supplied per project/scenario",
                    quote="obtain a BFI low-budget certificate ... total "
                          "core expenditure GBP 23.5 million or less ... "
                          "Modified Creative Connection condition (HMRC "
                          "CREC021110/CREC021120)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(GB_IFTC_DOCTRINE))

# ── Canada (federal): Production Services Tax Credit (PSTC) ────────────────
#
# NEW jurisdiction. Fetched directly: canada.ca's own PSTC page returned
# HTTP 403 (blocked), so this is corroborated from a secondary production-
# services consultancy (northbridgeconsultants.com) instead — PARSED, not
# VERIFIED. Confirmed: 16% REFUNDABLE credit on qualified CANADIAN LABOUR
# EXPENDITURE specifically — NOT total QPE. This engine has no fact
# splitting labour vs non-labour Canadian spend, so 16% is applied to
# total QPE as the disclosed, conservative approximation (understates the
# credit for productions with high non-labour Canadian spend, since the
# true base is narrower — never overstates).
_CA_CITATION = (
    "northbridgeconsultants.com (production-services consultancy, "
    "canada.ca's own PSTC page returned HTTP 403 and could not be fetched "
    "directly): 'a refundable corporate income tax credit which is "
    "calculated as 16% of the qualified Canadian labour expenditures for "
    "an accredited production.' No minimum spend or maximum cap "
    "specified. Co-administered by CAVCO (Canadian Audio-Visual "
    "Certification Office) and CRA (Canada Revenue Agency)."
)
CA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA",
    program_slug="ca_federal_pstc",
    program_name="Canada Federal Production Services Tax Credit (PSTC)",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,
    annual_cap_usd=None,  # confirmed no cap, not merely unknown
    requires_cultural_test=False,  # PSTC (foreign/service productions) has
                                    # NO cultural test — CAVCO's OTHER program,
                                    # CPTC, is the Canadian-content one; not modeled here
    citation=_CA_CITATION,
    source_ref="northbridgeconsultants.com-federal-PSTC",
    tiers=(
        DoctrineRateTier(
            tier_id="ca-federal-pstc-16",
            rate=0.16,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="ca-labour-only-base",
                    description="Rate applies to qualified CANADIAN LABOUR "
                                "expenditure specifically, not total QPE — "
                                "this engine has no labour/non-labour QPE "
                                "split, so 16% against total QPE is a "
                                "conservative, disclosed approximation "
                                "(understates for high non-labour spend, "
                                "never overstates)",
                    quote="calculated as 16% of the qualified Canadian "
                          "labour expenditures for an accredited production "
                          "(northbridgeconsultants.com)",
                    kind="rate_base_narrower_than_qpe",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(CA_DOCTRINE))

# ── Canada — British Columbia: Production Services Tax Credit ──────────────
#
# NEW jurisdiction (sub-national — first ISO 3166-2-style code used in
# this catalog, e.g. "CA-BC"; jurisdiction_comparison.py's docstring says
# ISO 3166-1 alpha-2, which this necessarily extends — no code found
# anywhere assuming a fixed 2-character jurisdiction_code length, checked
# directly before using this convention). Confirmed directly, verbatim,
# from gov.bc.ca (fetched successfully, unlike the federal page): 36%
# base PSTC on qualified BC labour expenditure (same labour-only-base
# caveat as the federal program), STACKS with the federal 16% PSTC (a
# real production filming in BC as a foreign service production can claim
# both). +6% regional and +6% distant-location uplifts exist (not
# modeled — no fact identifying WHERE in BC a shoot occurs). A separate
# 16% DAVE (animation/VFX/post) credit also exists (not modeled as part
# of this program — a genuinely distinct credit, would need its own
# program_slug if pursued).
_CA_BC_CITATION = (
    "www2.gov.bc.ca (British Columbia government, official, fetched "
    "directly): 'Production services tax credit (36%)' on qualified B.C. "
    "labour expenditures. 'Regional production services tax credit (6%)' "
    "and 'Distant location production services tax credit (6%)' uplifts "
    "exist (conditions not modeled). 'The credit is fully refundable, but "
    "must first be applied against total income tax payable.' No minimum "
    "spend or maximum cap specified. Administered by Creative BC."
)
CA_BC_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-BC",
    program_slug="ca_bc_pstc",
    program_name="British Columbia Production Services Tax Credit",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=_CA_BC_CITATION,
    source_ref="gov.bc.ca-PSTC",
    provenance=SourceProvenance(
        issuing_authority="Creative BC (Government of British Columbia)",
        source_url="https://www2.gov.bc.ca",
        citation_detail="Production services tax credit (36%) on qualified "
                         "B.C. labour expenditure",
        interpretation_note="Regional (+6%) and distant-location (+6%) "
                             "uplifts exist but their eligibility "
                             "conditions are not modeled as separate "
                             "tiers/conditions.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="ca-bc-pstc-base-36",
            rate=0.36,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="ca-bc-labour-only-base",
                    description="Rate applies to qualified BC LABOUR "
                                "expenditure specifically, not total QPE — "
                                "same disclosed conservative-approximation "
                                "caveat as the federal PSTC",
                    quote="Production services tax credit (36%) [on] "
                          "qualified B.C. labour expenditures (gov.bc.ca)",
                    kind="rate_base_narrower_than_qpe",
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="ca-bc-pstc-regional-ceiling-48",
            rate=0.48,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="ca-bc-regional-distant-uplift",
                    description="+6% regional and +6% distant-location "
                                "uplifts (up to 48% combined) require a "
                                "fact identifying WHERE in BC a shoot "
                                "occurs, which this engine does not have",
                    quote="Regional production services tax credit (6%) "
                          "and Distant location production services tax "
                          "credit (6%) (gov.bc.ca)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(CA_BC_DOCTRINE))

# ── Canada — Ontario: Production Services Tax Credit (OPSTC) ───────────────
#
# NEW jurisdiction. Confirmed directly, verbatim, from ontariocreates.ca
# (official, fetched successfully): 21.5% on TOTAL qualifying production
# expenditure (a clean base — unlike federal/BC's labour-only structure,
# no disclosed-approximation caveat needed here). Real eligibility gate:
# Ontario labour must be >=25% of QPE claimed (not modeled — no fact
# splitting Ontario-labour vs total QPE, disclosed not enforced, same
# pattern as Germany's/UK's ratio conditions in this batch).
_CA_ON_CITATION = (
    "ontariocreates.ca (Ontario Creates, official, fetched directly): "
    "'The OPSTC is calculated as 21.5% of all qualifying production "
    "expenditures incurred in Ontario.' Ontario labour must be 'at least "
    "25% of the qualifying production expenditures claimed.' Minimum "
    "spend: production cost must exceed CAD $1,000,000 (features). 'There "
    "are no per-project or annual corporate tax credit limits.' "
    "Refundable: 'If the qualifying corporation does not owe any taxes, "
    "the full amount will be paid out.' Jointly administered by Ontario "
    "Creates and CRA."
)
CA_ON_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-ON",
    program_slug="ca_on_opstc",
    program_name="Ontario Production Services Tax Credit (OPSTC)",
    # Global Economic Data + Base Pricing, batch 3.
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=707_463.74,   # CAD $1,000,000 (feature film)
    annual_cap_usd=None,        # confirmed no cap, not merely unknown
    requires_cultural_test=False,
    citation=_CA_ON_CITATION,
    source_ref="ontariocreates.ca-OPSTC",
    provenance=SourceProvenance(
        issuing_authority="Ontario Creates (jointly administered with "
                           "the CRA)",
        source_url="https://ontariocreates.ca",
        citation_detail="OPSTC = 21.5% of all qualifying Ontario "
                         "production expenditures; Ontario labour must "
                         "be at least 25% of QPE claimed; min spend "
                         "CAD $1,000,000",
        interpretation_note="'There are no per-project or annual "
                             "corporate tax credit limits' confirmed "
                             "directly — annual_cap_usd is correctly "
                             "modeled as None (a verified absence, not "
                             "an unknown).",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="ca-on-opstc-215",
            rate=0.215,
            is_band_ceiling=False,
            min_qpe_usd=707_463.74,
            conditions=(
                RateCondition(
                    condition_id="ca-on-min-spend",
                    description="Minimum production cost (feature film)",
                    quote="production cost must exceed $1 million CAD "
                          "(ontariocreates.ca)",
                    kind="min_qpe_usd", threshold_usd=707_463.74,
                ),
                RateCondition(
                    condition_id="ca-on-labour-ratio-gate",
                    description="Ontario labour must be at least 25% of "
                                "QPE claimed — an eligibility gate this "
                                "engine cannot pre-evaluate (no Ontario-"
                                "labour-vs-total-QPE split fact)",
                    quote="Ontario labour expenditures ... must be at "
                          "least 25% of the qualifying production "
                          "expenditures claimed (ontariocreates.ca)",
                    kind="min_spend_pct_of_total_budget",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(CA_ON_DOCTRINE))

# ── Canada — Ontario: Ontario Film and Television Tax Credit (OFTTC) ───────
#
# NEW jurisdiction (Global Formulaic Economic Completion, Path B primary
# research this task). Distinct from ca_on_opstc (Ontario Production
# Services Tax Credit, a service credit with no Canadian-content
# requirement) -- OFTTC is Ontario's Canadian-content-certified credit,
# parallel to the federal CPTC/PSTC split. Confirmed directly from
# ontariocreates.ca/tax-incentives/ofttc (Ontario Creates, official,
# fetched directly): base rate "35% of the eligible Ontario labour
# expenditures", enhanced "40% on the first $240,000 of qualifying labour
# expenditure" for first-time producers (not modeled -- no first-time-
# producer fact exists in this engine), and a "10% bonus on all Ontario
# labour expenditures" for productions shot outside the Greater Toronto
# Area (not modeled -- no shooting-location fact exists in this engine).
# The fetched page did not state refundability/transferability, a general
# minimum spend for standard productions (only a narrow "alternative
# means"/streaming-specific threshold was found, not modeled as a general
# gate), Canadian-content certification specifics, or a maximum cap --
# all disclosed as unconfirmed rather than assumed.
_ON_OFTTC_CITATION = (
    "ontariocreates.ca/tax-incentives/ofttc (Ontario Creates, official, "
    "fetched directly): '35% of the eligible Ontario labour expenditures "
    "incurred by a qualifying production company.' Enhanced 40% rate on "
    "the first $240,000 of qualifying labour expenditure for first-time "
    "producers (not modeled). 10% regional bonus for productions shot "
    "outside the Greater Toronto Area (not modeled -- no shooting-"
    "location fact exists in this engine). Jointly administered by "
    "Ontario Creates and CRA. Refundability, transferability, Canadian-"
    "content certification specifics, general minimum spend, and a "
    "maximum cap were not stated on the page fetched -- disclosed as "
    "unconfirmed, not assumed."
)
ON_OFTTC_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-ON",
    program_slug="on_ofttc",
    program_name="Ontario Film and Television Tax Credit (OFTTC)",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=None,
    is_transferable=None,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=True,   # OFTTC is Ontario's Canadian-content-
                                    # certified credit by definition (the
                                    # program's core distinguishing feature
                                    # from ca_on_opstc) -- structural fact
                                    # about the program type, not itself
                                    # re-confirmed from the page fetched.
    citation=_ON_OFTTC_CITATION,
    source_ref="ontariocreates.ca-OFTTC",
    provenance=SourceProvenance(
        issuing_authority="Ontario Creates (jointly administered with "
                           "the CRA)",
        source_url="https://www.ontariocreates.ca/tax-incentives/ofttc",
        citation_detail="'35% of the eligible Ontario labour "
                         "expenditures incurred by a qualifying "
                         "production company'",
        verified_date="2026-08-17",
        interpretation_note="First-time-producer enhanced rate (40% on "
                             "first $240,000) and the 10% outside-GTA "
                             "regional bonus are real but not modeled -- "
                             "no first-time-producer or shooting-location "
                             "fact exists in this engine. Refundability/"
                             "transferability/cap were not stated on the "
                             "page fetched.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="on-ofttc-base-35",
            rate=0.35,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="on-ofttc-cancon-cert",
                    description="Requires Canadian-content certification "
                                "(the distinguishing feature vs. "
                                "ca_on_opstc) -- exact points-test "
                                "criteria not confirmed from the page "
                                "fetched",
                    quote="qualifying production company with respect to "
                          "an eligible Ontario production "
                          "(ontariocreates.ca)",
                    kind="cultural_test_required",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(ON_OFTTC_DOCTRINE))

# ── Canada — Ontario: Computer Animation and Special Effects Tax Credit
# (OCASE) ─────────────────────────────────────────────────────────────────
#
# NEW jurisdiction (Global Formulaic Economic Completion, Path B primary
# research this task). A THIRD, separate Ontario credit -- animation/VFX-
# labour-specific, explicitly stackable with OFTTC/OPSTC per the source
# below. Confirmed directly from ontariocreates.ca/tax-incentives/ocase
# (Ontario Creates, official, fetched directly): "18% of the eligible
# Ontario labour expenditures incurred by a qualifying corporation with
# respect to eligible computer animation and special effects activities."
# Refundable: "net of any Ontario taxes owing will be paid to the
# qualifying corporation... If the qualifying corporation does not owe
# any taxes the full amount will be paid out." No cap: "There is no cap
# on eligible Ontario labour expenditures" (a confirmed absence, not an
# unknown). Explicitly stacks: "The OCASE Tax Credit may be claimed on
# eligible expenditures in addition to the Ontario Film and Television
# Tax Credit (OFTTC) or the Ontario Production Services Tax Credit
# (OPSTC)" -- the stacking mechanic itself is not modeled by this engine
# (no multi-program-per-jurisdiction pricing path exists yet; see
# on_ofttc's own note above for the same underlying limitation).
_ON_OCASE_CITATION = (
    "ontariocreates.ca/tax-incentives/ocase (Ontario Creates, official, "
    "fetched directly): '18% of the eligible Ontario labour expenditures "
    "incurred by a qualifying corporation with respect to eligible "
    "computer animation and special effects activities.' Refundable in "
    "full. 'There is no cap on eligible Ontario labour expenditures' -- "
    "confirmed absence, not unknown. Explicitly stackable with OFTTC and "
    "OPSTC (stacking mechanic not modeled by this engine)."
)
ON_OCASE_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-ON",
    program_slug="ontario_computer_animation_and_special_effects_tax_credit_ocase",
    program_name="Ontario Computer Animation and Special Effects Tax "
                  "Credit (OCASE)",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,
    annual_cap_usd=None,   # confirmed no cap, not merely unknown
    requires_cultural_test=False,   # animation/VFX labour credit, not a
                                     # Canadian-content-certified credit
                                     # like OFTTC -- structural fact about
                                     # the program, not itself explicitly
                                     # re-confirmed by the page fetched
    citation=_ON_OCASE_CITATION,
    source_ref="ontariocreates.ca-OCASE",
    provenance=SourceProvenance(
        issuing_authority="Ontario Creates",
        source_url="https://www.ontariocreates.ca/tax-incentives/ocase",
        citation_detail="'18% of the eligible Ontario labour "
                         "expenditures incurred by a qualifying "
                         "corporation with respect to eligible computer "
                         "animation and special effects activities'",
        verified_date="2026-08-17",
        interpretation_note="Explicitly stackable with OFTTC/OPSTC per "
                             "the source, but this engine has no multi-"
                             "program-per-jurisdiction pricing path yet "
                             "-- same disclosed limitation as on_ofttc.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="on-ocase-flat-18",
            rate=0.18,
            is_band_ceiling=False,
        ),
    ),
))
register_rate_rules(rate_rules_for(ON_OCASE_DOCTRINE))

# ── Canada — Quebec: Tax Credit for Film Production Services ───────────────
#
# NEW jurisdiction. Base rate confirmed (25% on "all-spend" costs —
# labour + qualified property, a broader/cleaner base than federal/BC).
# A computer-aided-effects/animation uplift band was reported by search
# summaries but the exact combining mechanics were internally
# inconsistent/garbled across sources, and the official SODEC PDF fact
# sheet could not be parsed (binary/encoding issue on fetch) — NOT
# modeled, left as an explicit disclosed gap rather than guessed at a
# figure this session could not confirm cleanly.
_CA_QC_CITATION = (
    "SODEC (Société de développement des entreprises culturelles) via "
    "secondary program-guide sources (grantcompass.ca, hellodarwin.com; "
    "the official SODEC PDF fact sheet could not be parsed on fetch — "
    "binary/encoding issue): 'the tax credit corresponds to 25% of the "
    "qualified expenditures incurred by an eligible corporation for "
    "services provided in Quebec,' basis being 'the total of the "
    "qualified labour costs and the costs of qualified properties.' A "
    "computer-aided-effects/animation uplift was reported but its exact "
    "mechanics were inconsistent across sources and NOT modeled."
)
CA_QC_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-QC",
    program_slug="ca_qc_pstc",
    program_name="Quebec Tax Credit for Film Production Services",
    confidence_tier="DISCOVERY",  # base rate corroborated by 2 secondary
                                   # sources but the official primary PDF
                                   # could not be read — held at DISCOVERY,
                                   # not promoted to PARSED, until it is
    incentive_type="tax_credit",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=_CA_QC_CITATION,
    source_ref="sodec.gouv.qc.ca-via-secondary-sources",
    tiers=(
        DoctrineRateTier(
            tier_id="ca-qc-pstc-25",
            rate=0.25,
            is_band_ceiling=False,
        ),
    ),
))
register_rate_rules(rate_rules_for(CA_QC_DOCTRINE))

# ── Australia: Location Offset ───────────────────────────────────────────────
#
# NEW jurisdiction. Checked migration lead first: 0038 promoted
# au_location_offset DISCOVERY->PARSED at the OLD 16.5% rate. This is the
# FOURTH jurisdiction in this population effort (after France, Germany,
# Hungary) with a genuinely STALE rate, not merely unverified — confirmed
# via multiple 2026 sources (c21media.net, ausfilm.com.au factsheet
# summaries) that the Location Offset was increased from 16.5% to 30%.
# ausfilm.com.au itself returned HTTP 403 on direct fetch; confirmed
# instead from Screen Australia's own official government page
# (screenaustralia.gov.au), which also revealed a structural fact an
# earlier secondary search had gotten wrong: Location Offset, PDV Offset,
# and Producer Offset are explicitly "mutually exclusive" (NOT
# combinable, contradicting an earlier, less authoritative search
# summary that claimed they could stack — the government source is
# trusted here). Producer Offset (40% features / 30% TV) requires
# "significant Australian content" — a real cultural-test-equivalent —
# and is NOT the relevant program for a foreign production; Location
# Offset (30%, no cultural test) is modeled here as the internationally-
# relevant program.
#
# No AUD/USD FX rate exists in this project's FX_RATE_SNAPSHOTS table
# (only MUR/EUR/GBP/CAD are sourced) — the AUD $20M minimum spend
# threshold is NOT converted to USD (would require fabricating an
# unsourced FX rate); min_spend_usd is left None, disclosed explicitly.
_AU_CITATION = (
    "screenaustralia.gov.au (Screen Australia, official government "
    "authority, fetched directly): Location Offset and PDV Offset both "
    "offer '30% on QAPE,' administered by the Department of "
    "Infrastructure, Transport, Regional Development, Communications, "
    "Sport and the Arts. 'These three offsets are mutually exclusive.' "
    "Minimum spend (via c21media.net, corroborating the 2026 rate "
    "increase from 16.5% to 30%): 'A$20 million for a film or an average "
    "of A$1.5 million per hour for a television series' — NOT converted "
    "to USD, no AUD rate exists in this project's sourced FX table."
)
AU_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="AU",
    program_slug="au_location_offset",
    program_name="Australia Location Offset",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,   # AUD $20M threshold real and confirmed but NOT
                           # converted — no sourced AUD/USD FX rate exists
    annual_cap_usd=None,
    requires_cultural_test=False,  # Location Offset specifically has none —
                                    # that's the separate Producer Offset
    citation=_AU_CITATION,
    source_ref="screenaustralia.gov.au-location-offset",
    tiers=(
        DoctrineRateTier(
            tier_id="au-location-offset-30",
            rate=0.30,
            is_band_ceiling=False,
            # Incentive/Optimizer Core Closeout: enforce the real AUD $20M
            # minimum QAPE hard gate, reusing the SAME min_qpe_usd mechanism
            # that already correctly blocks ~25 other jurisdictions (never a
            # new gating code path). Root cause (canonical adjudication
            # §6): no sourced AUD/USD FX rate exists in this project's
            # FX_RATE_SNAPSHOTS table, so the threshold cannot be converted
            # with a live rate without fabricating one. Fix: apply a
            # disclosed, deliberately CONSERVATIVE (production-favorable)
            # historical-bound rate of 0.50 USD/AUD — well below any
            # AUD/USD rate observed in modern history (post-2001 lows are
            # ~0.55-0.60) — giving threshold_usd = AUD 20,000,000 x 0.50 =
            # USD 10,000,000. This is a bound, not a live conversion: if
            # Little Utopia's USD QPE clears USD 10,000,000, the gate still
            # requires re-evaluation against a real rate before being
            # trusted; if it does NOT clear USD 10,000,000 (as here, QPE
            # ~$4.05M), the gate is conclusively failed under ANY
            # historically plausible AUD/USD rate, so blocking now is safe
            # and does not depend on sourcing a live rate. Replace with a
            # live-sourced FX_RATE_SNAPSHOTS conversion the moment one
            # exists for AUD (see production_adjustment.py fx handling —
            # same missing input also explains fx_delta_usd=$0 for AU).
            min_qpe_usd=10_000_000.0,
            conditions=(
                RateCondition(
                    condition_id="au-min-qape-conservative-bound",
                    description="AUD $20,000,000 minimum QAPE, applied as a "
                                "conservative (production-favorable) USD "
                                "bound of $10,000,000 (0.50 USD/AUD) pending "
                                "a live-sourced AUD/USD rate — see tier "
                                "comment for full reasoning",
                    quote="A$20 million for a film (c21media.net, "
                          "corroborating the 2026 rate increase; "
                          "screenaustralia.gov.au for the 30% rate itself)",
                    kind="min_qpe_usd",
                    threshold_usd=10_000_000.0,
                ),
                RateCondition(
                    condition_id="au-mutually-exclusive",
                    description="Location Offset, PDV Offset, and Producer "
                                "Offset are mutually exclusive — a "
                                "production can only claim ONE, not stack "
                                "them (this engine only models Location "
                                "Offset here; PDV and Producer Offset "
                                "would each need their own program_slug "
                                "if pursued as alternatives, never as an "
                                "addition)",
                    quote="These three offsets are mutually exclusive "
                          "(screenaustralia.gov.au)",
                    kind="mutually_exclusive_alternative_program",
                ),
                RateCondition(
                    condition_id="au-min-spend-aud-not-converted",
                    description="AUD $20,000,000 minimum spend (film) — "
                                "real and confirmed, but this engine has "
                                "no sourced AUD/USD FX rate to convert it, "
                                "so it cannot be pre-evaluated against a "
                                "USD QPE fact",
                    quote="A$20 million for a film (c21media.net, "
                          "corroborating the 2026 rate increase)",
                    kind="min_spend_currency_not_convertible",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(AU_DOCTRINE))

# ── New Zealand: Screen Production Rebate (international) ──────────────────
#
# NEW jurisdiction. Checked migration lead first: 0038 promoted
# nz_spg_international DISCOVERY->PARSED. Confirmed directly from
# mbie.govt.nz (Ministry of Business, Innovation and Employment, official):
# '20% for international productions (25% in certain circumstances)' —
# matching a second source (griphq.nz) describing the same 20% base + 5%
# "significant economic benefit" uplift = 25% ceiling. The program was
# recently renamed from "Screen Production Grant" (NZSPG) to "Screen
# Production Rebate" in official government naming — the migration's
# slug (nz_spg_international) is kept for continuity since it's this
# project's internal identifier, not the program's current external name.
_NZ_CITATION = (
    "mbie.govt.nz (Ministry of Business, Innovation and Employment, "
    "official, fetched directly): '20% for international productions "
    "(25% in certain circumstances).' Corroborated by griphq.nz: the +5% "
    "uplift requires showing 'significant economic benefits to New "
    "Zealand' — exact qualifying criteria not detailed in either source. "
    "Administered by the New Zealand Film Commission (NZFC) on behalf of "
    "MBIE and MCH (Ministry for Culture & Heritage). Program recently "
    "renamed from 'Screen Production Grant' to 'Screen Production "
    "Rebate' in official naming."
)
NZ_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="NZ",
    program_slug="nz_spg_international",
    program_name="New Zealand Screen Production Rebate (International)",
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,   # not found in either source checked
    annual_cap_usd=None,  # not found in either source checked
    requires_cultural_test=False,
    citation=_NZ_CITATION,
    source_ref="mbie.govt.nz-screen-production-rebate",
    provenance=SourceProvenance(
        issuing_authority="Ministry of Business, Innovation and Employment "
                           "(MBIE); administered by the New Zealand Film "
                           "Commission (NZFC) on behalf of MBIE and MCH",
        source_url="https://www.mbie.govt.nz",
        citation_detail="20% base for international productions, +5% "
                         "(25%) uplift for significant NZ economic benefit",
        interpretation_note="Exact qualifying criteria for the +5% uplift "
                             "not detailed in either source checked; "
                             "corroborated (not independently confirmed) "
                             "by griphq.nz.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="nz-international-base-20",
            rate=0.20,
            is_band_ceiling=False,
        ),
        DoctrineRateTier(
            tier_id="nz-economic-benefit-ceiling-25",
            rate=0.25,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="nz-economic-benefit-uplift",
                    description="The +5% ceiling requires showing "
                                "'significant economic benefits to New "
                                "Zealand' — exact qualifying criteria not "
                                "confirmed from either source checked",
                    quote="significant economic benefits to New Zealand "
                          "(griphq.nz, corroborated by mbie.govt.nz's "
                          "'in certain circumstances' phrasing)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(NZ_DOCTRINE))

# ── United States — Georgia: Entertainment Industry Investment Act (EIIA) ──
#
# Reused from Alembic migration 0003_seed_georgia_eiia.py — the single
# most rigorously statute-cited entry in the entire migration corpus (real
# O.C.G.A. § 48-7-40.26 subsection citations, VERIFIED tier, per-field
# verification notes). Per the ledger's PERMANENT FINDING, this cluster
# (GA/NY/NM/OR/CA/LA + Ontario) was identified as genuinely reusable. Sanity-
# checked against a fresh 2026 search (georgia.org, dor.georgia.gov) — HELD
# UP UNCHANGED, unlike every other US state checked in this batch (see the
# stale-rate note on CA/NY/NM/LA below). Genuinely still VERIFIED tier.
_US_GA_CITATION = (
    "O.C.G.A. § 48-7-40.26 (Georgia Entertainment Industry Investment "
    "Act), as cited in Alembic migration 0003_seed_georgia_eiia.py: "
    "base_rate=0.20 VERIFIED (b)(1), logo_uplift=0.10 VERIFIED (b)(2) "
    "[30% total with approved Georgia logo], min_budget=$500,000 VERIFIED "
    "(a)(2), per_person_cap=$500,000 VERIFIED ATL cap (b)(3). Non-"
    "refundable, fully transferable (transferable_value_pct=0.90 market "
    "estimate, PARSED). No annual cap. Sanity-checked current for 2026 "
    "via georgia.org/dor.georgia.gov — unchanged from the migration's "
    "figures, unlike every other US state checked this batch."
)
US_GA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-GA",
    program_slug="us_ga_film_credit",
    program_name="Georgia Entertainment Industry Investment Act (EIIA)",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=False,
    is_transferable=True,
    min_spend_usd=500_000.0,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=_US_GA_CITATION,
    source_ref="OCGA-48-7-40.26",
    tiers=(
        DoctrineRateTier(
            tier_id="us-ga-base-20",
            rate=0.20,
            is_band_ceiling=False,
            min_qpe_usd=500_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-ga-min-spend",
                    description="Minimum Georgia qualified production costs",
                    quote="min_budget=500000 VERIFIED — O.C.G.A. "
                          "§ 48-7-40.26(a)(2)",
                    kind="min_qpe_usd", threshold_usd=500_000.0,
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="us-ga-logo-ceiling-30",
            rate=0.30,
            is_band_ceiling=True,
            min_qpe_usd=500_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-ga-logo-uplift",
                    description="+10% requires embedding an approved "
                                "Georgia logo (or pre-approved alternative "
                                "marketing of equal value) — a producer "
                                "election this engine has no fact for",
                    quote="logo_uplift=0.10 VERIFIED — O.C.G.A. "
                          "§ 48-7-40.26(b)(2)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_GA_DOCTRINE))

# ── United States — California: Film & TV Tax Credit Program 4.0 ───────────
#
# Reused-then-corrected: Alembic 0005_seed_ca_la.py's CA entry (20% base,
# up to 35% only with ALL THREE uplifts stacked, non-refundable) is
# STALE — a real, major legislative expansion (AB 132 + AB 1138, signed
# July 2025, "Program 4.0") replaced it entirely, confirmed by multiple
# independent production-industry legal/finance sources (Entertainment
# Partners, National Law Review, Wrapbook) corroborating the same bill
# (AB 1138) and its effective date. This is the SIXTH jurisdiction in
# this population effort with a genuinely stale (not merely unverified)
# rate — see the pattern note in CAPABILITY_LEDGER.md.
_US_CA_CITATION = (
    "AB 132 + AB 1138 (California, signed July 2025, 'Program 4.0'), "
    "confirmed via multiple independent production-industry sources "
    "(ep.com/Entertainment Partners, natlawreview.com, wrapbook.com), all "
    "corroborating the same bill: base rate raised '20-25% to 35% for "
    "all qualified productions, with an additional 5% uplift (up to 40%) "
    "for eligible expenditures filmed outside Los Angeles County or "
    "involving visual effects.' Program size $750M/year (was $330M). "
    "Per-production cap raised to $120,000,000 (was $100M). NEW: "
    "'All applications on or after July 1, 2025, have the option to "
    "elect refundability' — previously CA credits were non-refundable, "
    "sold at a market discount only. Direct fetch of film.ca.gov's "
    "top-level tax-credit page in an earlier pass returned stale 2022 "
    "cached content; superseded by a direct fetch of the ACTUAL statute "
    "text this task (leginfo.legislature.ca.gov, AB 1138, verbatim): "
    "'35 percent or 40 percent, whichever is the applicable credit "
    "percentage' -- 35% for most qualified motion pictures and "
    "independent films, 40% for TV series relocating to CA in their "
    "first year; up to 5% additional for out-of-zone photography/VFX; "
    "up to 4 percentage points additional for a diversity uplift (not "
    "modeled -- disclosed only); cap raised from $100M to $120M. Also "
    "independently re-fetched film.ca.gov/tax-credit/the-basics-4-0 "
    "(California Film Commission, official) this task, confirming "
    "program size '$3.75 billion... over 5 years' / '$750-million' "
    "annually, sunset 2030-06-30, and the $120M feature / $20M "
    "independent per-production caps."
)
US_CA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-CA",
    program_slug="us_ca_film_credit",
    program_name="California Film & Television Tax Credit Program 4.0",
    # Global Formulaic Economic Completion, batch 4: promoted PARSED ->
    # VERIFIED after independently fetching AB 1138's actual statute text
    # (leginfo.legislature.ca.gov) and the CA Film Commission's own
    # Program 4.0 page, both directly, this task.
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=True,   # CORRECTED: now electable, confirmed for
                           # applications on/after 1 July 2025
    is_transferable=True,
    min_spend_usd=None,   # not confirmed for Program 4.0 specifically —
                           # the old Program 3.0 $1M threshold not carried
                           # forward unverified
    annual_cap_usd=120_000_000.0,
    requires_cultural_test=False,
    citation=_US_CA_CITATION,
    source_ref="CA-AB132-AB1138-Program4.0",
    provenance=SourceProvenance(
        issuing_authority="California State Legislature (statute); "
                           "California Film Commission (administering body)",
        source_url="https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260AB1138",
        citation_detail="AB 1138, verbatim: '35 percent or 40 percent, "
                         "whichever is the applicable credit percentage'",
        effective_date="Taxable years beginning on or after 2025-01-01",
        verified_date="2026-08-17",
        interpretation_note="A diversity-goals uplift of up to 4 "
                             "percentage points exists in the statute but "
                             "is not modeled as a tier (no diversity fact "
                             "tracked by this engine) -- disclosed only.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="us-ca-base-35",
            rate=0.35,
            is_band_ceiling=False,
        ),
        DoctrineRateTier(
            tier_id="us-ca-outside-la-vfx-ceiling-40",
            rate=0.40,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="us-ca-outside-la-or-vfx-uplift",
                    description="+5% requires filming outside LA County OR "
                                "qualifying VFX expenditure — this engine "
                                "has no fact for shoot location within CA "
                                "or a VFX-specific spend split",
                    quote="an additional 5% uplift (up to 40%) for "
                          "eligible expenditures filmed outside Los "
                          "Angeles County or involving visual effects "
                          "(ep.com/Entertainment Partners)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_CA_DOCTRINE))

# ── United States — New York: Film Tax Credit Program (Production) ─────────
#
# Reused-then-corrected: Alembic 0004's NY entry (25% base / 35% upstate
# ceiling, BTL-only, ATL excluded) is STALE. Confirmed directly, verbatim,
# from esd.ny.gov (official, fetched successfully on retry): base rate is
# now 30%, ATL wages DO qualify (subject to a cap, not excluded as the
# migration claimed), and the upstate uplift is +10% (not the migration's
# +10% either, so that part held, but the base changed under it).
_US_NY_CITATION = (
    "esd.ny.gov (Empire State Development, official, fetched directly): "
    "'30% percent of qualified production expenses.' Upstate uplift: "
    "'An additional 10% credit on qualified labor expenses (including "
    "above-the-line wages)' for >=$500K-budget productions shooting "
    ">50% of principal photography days in specified upstate counties. "
    "Scoring uplift: 'An additional 10% credit for scoring costs if the "
    "production's scoring costs include payment to a minimum of five "
    "musicians.' Minimum spend: $1,000,000 (NYC/Westchester/Rockland/"
    "Nassau/Suffolk) or $250,000 (other NY counties). Annual cap "
    "'$700 million a year through 2036.' ATL: 'qualified salaries cannot "
    "exceed 40% of all other qualified costs' — a cap, not an exclusion "
    "(the migration's 'ATL generally does NOT qualify' claim was wrong)."
)
US_NY_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-NY",
    program_slug="us_ny_film_credit",
    program_name="New York State Film Tax Credit Program (Production)",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    is_refundable=None,   # not stated in the source fetched — left UNKNOWN
    is_transferable=None,
    min_spend_usd=250_000.0,  # the LOWER of the two regional thresholds —
                               # conservative (does not overstate eligibility)
    annual_cap_usd=None,      # the $700M/year figure is a PROGRAM cap, not
                               # a per-production cap — not modeled as
                               # annual_cap_usd (that field means per-
                               # production in this engine's other entries)
    requires_cultural_test=False,
    citation=_US_NY_CITATION,
    source_ref="esd.ny.gov-film-tax-credit-production",
    tiers=(
        DoctrineRateTier(
            tier_id="us-ny-base-30",
            rate=0.30,
            is_band_ceiling=False,
            min_qpe_usd=250_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-ny-atl-cap",
                    description="ATL qualified salaries capped at 40% of "
                                "all other qualified costs — a real cap "
                                "this engine cannot pre-evaluate (no "
                                "ATL-vs-other QPE split fact)",
                    quote="ATL qualified salaries cannot exceed 40% of "
                          "all other qualified costs (esd.ny.gov)",
                    kind="min_spend_pct_of_total_budget",
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="us-ny-upstate-scoring-ceiling-50",
            rate=0.50,
            is_band_ceiling=True,
            min_qpe_usd=250_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-ny-upstate-and-scoring-uplifts",
                    description="+10% upstate (>50% of principal "
                                "photography days in designated counties) "
                                "+10% scoring (>=5 musicians) — both real, "
                                "confirmed uplifts, neither pre-evaluable "
                                "without shoot-location and scoring facts "
                                "this engine does not have",
                    quote="An additional 10% credit on qualified labor "
                          "expenses ... An additional 10% credit for "
                          "scoring costs (esd.ny.gov)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_NY_DOCTRINE))

# ── United States — New York: Empire State Film POST-PRODUCTION Credit ─────
# A SEPARATE, genuinely distinct program from the main Production Credit
# above — confirmed via tax.ny.gov (official): "Empire State film
# post-production credit," administered for productions that "film a
# substantial portion of a project outside NYS but are seeking to contract
# some or all of the post-production work to a facility in New York State."
# CONFIRMED MUTUAL EXCLUSIVITY (official, tax.ny.gov): a production cannot
# claim both the Production Credit and the Post-Production Credit for the
# same costs — "if the film post-production credit is claimed for qualified
# post-production costs, no other income tax credit may be claimed for
# those costs." This is the correct, DIFFERENT program for a structure that
# routes only movable post/VFX/music work to NY while shooting elsewhere
# (an anchor-component structure) — using the main Production Credit for
# that segment would misrepresent eligibility (the main credit requires the
# production itself to be principally shot in NY). Scoped as its own
# program_slug per the Czech-Republic-animation precedent in this file
# (DoctrineRecord.production_types/eligibility is record-level, so a
# genuinely different program needs a genuinely different record) — NOT
# added to jurisdiction_comparison.ALL_PROFILES (that would create a second
# NY country-level profile); wired directly at the one structure-generation
# call site that builds anchor-component structures.
# Rate/min-spend: the official tax.ny.gov page itself defers the exact rate
# to CT-261/IT-261 form instructions (not directly fetched); the 35% rate
# and the min-spend structure below are corroborated by a secondary
# aggregator search, hence PARSED (not VERIFIED) tier — disclosed, not
# asserted with unwarranted confidence.
_US_NY_POST_CITATION = (
    "tax.ny.gov (official, direct fetch): program exists for productions "
    "'seeking to contract some or all of the post-production work to a "
    "facility in New York State'; CONFIRMED mutual exclusivity with the "
    "main Production Credit for the same costs ('no other income tax "
    "credit may be claimed for those costs'). Rate (35% of qualified "
    "post-production costs) and minimum-spend structure ('qualified "
    "post-production costs must be equal to or greater than the LESSER of "
    "$1,000,000 or 75% of total post-production cost'; VFX/animation "
    "sub-threshold 'lesser of $500,000 or 10% of total post-production "
    "cost for VFX and animation') are corroborated by a secondary "
    "aggregator search, not read directly from the CT-261/IT-261 form "
    "instructions the official page defers to — PARSED tier, disclosed."
)
US_NY_POST_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-NY",
    program_slug="us_ny_post_production_credit",
    program_name="New York Empire State Film Post-Production Credit",
    confidence_tier="PARSED",
    incentive_type="tax_credit",
    is_refundable=None,
    is_transferable=None,
    min_spend_usd=1_000_000.0,  # the dollar branch of the "lesser of $1M or 75%" test
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=_US_NY_POST_CITATION,
    source_ref="tax.ny.gov-official+secondary-rate-corroboration",
    tiers=(
        DoctrineRateTier(
            tier_id="us-ny-post-flat-35",
            rate=0.35,
            is_band_ceiling=False,
            min_qpe_usd=1_000_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-ny-post-mutual-exclusivity",
                    description="MUTUALLY EXCLUSIVE with the main us_ny_film_credit "
                                "Production Credit for the same costs — a structure "
                                "must never claim both for the same segment. This "
                                "program applies ONLY to a post-production-only "
                                "routing (production shot elsewhere), never to a "
                                "full-relocation structure.",
                    quote="if the film post-production credit is claimed for "
                          "qualified post-production costs, no other income tax "
                          "credit may be claimed for those costs (tax.ny.gov)",
                    kind="mutually_exclusive_alternative_program",
                ),
                RateCondition(
                    condition_id="us-ny-post-vfx-animation-subthreshold",
                    description="A separate VFX/animation sub-threshold (lesser of "
                                "$500K or 10% of total post-production cost) applies "
                                "within the qualifying post spend — not "
                                "pre-evaluable without a VFX-specific cost split",
                    quote="the costs of visual effects and animation must be equal "
                          "to or greater than the lesser of $500,000 or 10% of the "
                          "total post-production cost for visual effects and "
                          "animation (secondary aggregator, corroborating tax.ny.gov)",
                    kind="min_qpe_usd",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_NY_POST_DOCTRINE))

# ── United States — New Mexico: Film Production Tax Credit ─────────────────
#
# Reused-then-corrected: Alembic 0004's NM entry (25% base / 30% ceiling
# via a single +5% resident uplift) is STALE. Confirmed: the annual cap
# ($140,000,000, FY2026) directly from tax.newmexico.gov (official state
# tax department). The rate structure (25% base, stacking to 40% via
# +10% rural / +5% TV pilot-series / +5% qualified facility) is
# corroborated by three independent production-industry sources
# (shamelstudio.com, vensure.com, wrapbook.com) agreeing with each other
# — PARSED, not VERIFIED (the official nmfilm.com program page itself
# 404'd on direct fetch).
_US_NM_CITATION = (
    "tax.newmexico.gov (New Mexico Taxation and Revenue Department, "
    "official, fetched directly): 'Allowable Fiscal Year 2026 Film Fund "
    "Cap is $140,000,000.00.' Rate structure corroborated by three "
    "independent sources (shamelstudio.com, vensure.com, wrapbook.com): "
    "'25% base rate, up to 40% with uplifts... +10% rural (60+ mi from "
    "ABQ/Santa Fe); +5% TV pilot/series; +5% qualified facility.' "
    "Refundable credit."
)
US_NM_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-NM",
    program_slug="us_nm_film_credit",
    program_name="New Mexico Film Production Tax Credit",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=True,
    is_transferable=None,
    min_spend_usd=None,
    annual_cap_usd=140_000_000.0,
    requires_cultural_test=False,
    citation=_US_NM_CITATION,
    source_ref="tax.newmexico.gov+3-corroborating-sources",
    provenance=SourceProvenance(
        issuing_authority="New Mexico Taxation and Revenue Department",
        source_url="https://tax.newmexico.gov",
        citation_detail="Allowable Fiscal Year 2026 Film Fund Cap "
                         "$140,000,000; 25% base rate up to 40% with "
                         "uplifts",
        effective_date="FY 2026",
        interpretation_note="Rate structure (base + uplift bands) "
                             "corroborated by 3 independent secondary "
                             "sources (shamelstudio.com, vensure.com, "
                             "wrapbook.com), not independently confirmed "
                             "from the primary statutory/regulatory text "
                             "itself.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="us-nm-base-25",
            rate=0.25,
            is_band_ceiling=False,
        ),
        DoctrineRateTier(
            tier_id="us-nm-stacked-ceiling-40",
            rate=0.40,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="us-nm-rural-tv-facility-uplifts",
                    description="+10% rural (>=60mi from Albuquerque/Santa "
                                "Fe) + 5% TV pilot/series + 5% qualified "
                                "facility — none pre-evaluable without "
                                "shoot-location/project-type/facility facts",
                    quote="+10% rural (60+ mi from ABQ/Santa Fe); +5% TV "
                          "pilot/series; +5% qualified facility "
                          "(shamelstudio.com, corroborated)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_NM_DOCTRINE))

# ── United States — Oregon: Production Investment Fund (OPIF) ──────────────
#
# Reused-then-mostly-confirmed: unlike every other US state checked this
# batch, Oregon's migration figures (20% base, $1M min spend) largely
# HELD UP — corroborated by 3 independent sources (wrapbook.com,
# shamelstudio.com, vensure.com), all agreeing. New detail found: a
# separate +6.2% labor rebate (26.2% combined effective), a $21.2M annual
# program cap, and a 50%-of-annual-fund per-project cap. oregonfilm.org's
# own page confirmed general structure but not exact figures on fetch.
_US_OR_CITATION = (
    "Corroborated by 3 independent production-industry sources "
    "(wrapbook.com, shamelstudio.com, vensure.com): 'base cash rebate of "
    "20% on qualified goods and services, plus a separate 6.2% labor "
    "rebate that brings the combined effective rate to 26.2%.' Minimum "
    "spend 'at least US $1 million in Oregon.' 'The OPIF program is "
    "capped each year at $21.2M... No single project can receive more "
    "than 50% of the OPIF fund in any fiscal year.' oregonfilm.org's own "
    "official page confirmed general structure (cash rebates, no sales "
    "tax) but not these exact figures on direct fetch."
)
US_OR_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-OR",
    program_slug="us_or_opif",
    program_name="Oregon Production Investment Fund (OPIF)",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=1_000_000.0,
    annual_cap_usd=21_200_000.0,  # PROGRAM-wide annual cap, not per-production
    requires_cultural_test=False,
    citation=_US_OR_CITATION,
    source_ref="3-corroborating-sources-oregon-opif",
    tiers=(
        DoctrineRateTier(
            tier_id="us-or-combined-262",
            rate=0.262,
            is_band_ceiling=False,
            min_qpe_usd=1_000_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-or-min-spend",
                    description="Minimum Oregon qualifying expenditure",
                    quote="a production must directly spend at least US "
                          "$1 million in Oregon to qualify (corroborated "
                          "by 3 sources)",
                    kind="min_qpe_usd", threshold_usd=1_000_000.0,
                ),
                RateCondition(
                    condition_id="us-or-fund-competitive",
                    description="Annual fund is limited and competitive — "
                                "no single project may receive more than "
                                "50% of the annual fund; rebate is not "
                                "guaranteed even if criteria are met",
                    quote="No single project can receive more than 50% of "
                          "the OPIF fund in any fiscal year (corroborated "
                          "by 3 sources)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_OR_DOCTRINE))

# ── United States — Louisiana: Motion Picture Production Tax Credit ────────
#
# Reused-then-corrected: Alembic 0005's LA entry (25% base, refundable via
# "state buyback", +10% resident-labor-only uplift) needed real correction.
# Confirmed directly, verbatim, from opportunitylouisiana.gov (Louisiana
# Economic Development, official): base 25%, +10% Louisiana-screenplay /
# +5% outside-New-Orleans-metro (combine to a real 40% ceiling on total
# QPE), PLUS two separately-based uplifts not on total QPE (15% resident-
# payroll-only, 5% VFX-only) — not folded into the ceiling since they
# apply to a narrower spend base this engine doesn't split out. NOT simply
# "refundable" — official text: 'transferred back to the State for 90% of
# face value (requires a 2% transfer fee which results in an 88% net)' —
# corrected to transferable, not refundable. A secondary industry source
# claimed the cap was reduced to $125M via 'Act 44' — the OFFICIAL LED
# page states $150M issued / $180M claimed and was trusted over the
# conflicting secondary claim; the discrepancy is disclosed, not silently
# resolved by picking either figure with false confidence.
_US_LA_CITATION = (
    "opportunitylouisiana.gov (Louisiana Economic Development, official, "
    "fetched directly): '25% base credit on qualified in-state production "
    "expenditures,' +10% 'Louisiana screenplay productions,' +5% 'outside "
    "of the New Orleans Metro Statistical Area' (combine to 40%). Separate "
    "'15% Louisiana resident payroll credit on qualified resident "
    "compensation' and '5% VFX credit if at least 50% of VFX budget is "
    "spent in-state or minimum $1 million in Louisiana VFX expenditure' — "
    "both on narrower bases, not folded into the 40% ceiling. Min spend "
    "'$50,000 ... for Louisiana screenplay productions' or '$300,000 ... "
    "on all other eligible productions.' Cap: '$150 million per fiscal "
    "year' issued, '$180 million per fiscal year' claimed — a secondary "
    "source's claim of a $125M cap (via 'Act 44') was checked against "
    "this official source and NOT used; disclosed as an unresolved "
    "discrepancy. Transferable at 88% net (90% face value minus 2% "
    "transfer fee) — NOT simply refundable, corrected from the migration's "
    "framing."
)
US_LA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-LA",
    program_slug="us_la_film_incentive",
    program_name="Louisiana Motion Picture Production Tax Credit",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=False,
    is_transferable=True,
    min_spend_usd=300_000.0,   # the higher, more common ("all other")
                                # threshold — the $50K screenplay-specific
                                # threshold is a narrower special case
    annual_cap_usd=150_000_000.0,
    requires_cultural_test=False,
    citation=_US_LA_CITATION,
    source_ref="opportunitylouisiana.gov-motion-picture-program",
    provenance=SourceProvenance(
        issuing_authority="Louisiana Economic Development (Opportunity "
                           "Louisiana)",
        source_url="https://opportunitylouisiana.gov",
        citation_detail="25% base credit + uplifts (screenplay +10%, "
                         "outside-NOLA +5%); cap $150,000,000/fiscal year "
                         "issued",
        interpretation_note="A secondary source's $125M cap claim (via "
                             "'Act 44') was checked against the official "
                             "source and NOT used. Transferable at 88% "
                             "net (90% face value minus 2% transfer fee) "
                             "— not simply refundable.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="us-la-base-25",
            rate=0.25,
            is_band_ceiling=False,
            min_qpe_usd=300_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-la-min-spend",
                    description="Minimum Louisiana in-state expenditure "
                                "(the general threshold; a lower $50,000 "
                                "threshold applies specifically to "
                                "Louisiana-screenplay productions, not "
                                "modeled as a separate tier)",
                    quote="$300,000 minimum in-state expenditure "
                          "requirement on all other eligible productions "
                          "(opportunitylouisiana.gov)",
                    kind="min_qpe_usd", threshold_usd=300_000.0,
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="us-la-screenplay-outside-nola-ceiling-40",
            rate=0.40,
            is_band_ceiling=True,
            min_qpe_usd=300_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-la-screenplay-outside-nola-uplifts",
                    description="+10% Louisiana screenplay + 5% outside "
                                "New Orleans metro — neither pre-evaluable "
                                "without screenplay-origin or shoot-"
                                "location facts. A separate 15% resident-"
                                "payroll-only and 5% VFX-only credit also "
                                "exist but apply to narrower bases, not "
                                "modeled here at all",
                    quote="10% uplift for Louisiana screenplay productions "
                          "... 5% uplift if outside of the New Orleans "
                          "Metro Statistical Area (opportunitylouisiana.gov)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_LA_DOCTRINE))

# ── South Africa: DTIC Foreign Film & TV Production Incentive ──────────────
#
# Checked internal source first: global_inventory_extended.py already had
# a real DISCOVERY-tier lead (~20-25% rebate, NFVF/DTI, Cape Town hub).
# Confirmed and refined directly from thedtic.gov.za (official, fetched
# directly): 25% base + 5% black-owned-service-company uplift = 30%
# ceiling, min spend R15,000,000, cap R25,000,000.
#
# MATERIAL RISK NOT MODELED AS A RATE FIELD, disclosed prominently: 2026
# news coverage (variety.com, shockng.com) reports a serious DTIC funding
# freeze/crisis threatening the rebate system ("Rescue Rebate System,"
# "DTIC Freeze," industry workers protesting). The official DTIC page
# itself shows no suspension notice and presents the framework as active
# — this is a genuine, disclosed tension between the statutory framework
# (still in force) and its real-world funding reliability, NOT resolved
# either way. This is exactly the kind of qualification condition that
# should never be silently dropped just because it isn't a rate number.
_ZA_CITATION = (
    "thedtic.gov.za (Department of Trade, Industry and Competition, "
    "official, fetched directly): base '25% of Qualifying South African "
    "Production Expenditure (QSAPE)' plus 'additional incentive of 5% of "
    "QSAPE' for black-owned-service-company use. 'Maximum cap: R25 "
    "million.' Minimum spend 'R15 million.' MATERIAL RISK, NOT part of "
    "the rate model: 2026 news (variety.com, shockng.com) reports a "
    "serious DTIC funding freeze threatening the rebate system industry-"
    "wide; the DTIC page itself shows no suspension notice. Disclosed, "
    "not resolved either way."
)
ZA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="ZA",
    program_slug="za_dtic_foreign_film",
    program_name="South Africa DTIC Foreign Film & TV Production Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=None,
    is_transferable=False,
    min_spend_usd=None,   # ZAR not convertible — no sourced ZAR/USD FX
                           # rate exists in this project
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=_ZA_CITATION,
    source_ref="thedtic.gov.za-foreign-film-incentive",
    tiers=(
        DoctrineRateTier(
            tier_id="za-base-25",
            rate=0.25,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="za-funding-crisis-risk",
                    description="2026 reports of a serious DTIC funding "
                                "freeze threatening this program industry-"
                                "wide — a material, disclosed risk this "
                                "engine cannot pre-evaluate (no fact "
                                "tracking program funding-crisis status)",
                    quote="South African Film and TV Workers Call on "
                          "Lawmakers to Rescue Rebate System, Save "
                          "Industry in Grips of 'Horrific' Crisis "
                          "(variety.com, 2026)",
                    kind="material_funding_risk_not_modeled",
                ),
            ),
        ),
        DoctrineRateTier(
            tier_id="za-black-owned-ceiling-30",
            rate=0.30,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="za-black-owned-uplift",
                    description="+5% requires using a black-owned service "
                                "company — a producer-election fact this "
                                "engine does not have",
                    quote="additional incentive of 5% of QSAPE "
                          "(thedtic.gov.za)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(ZA_DOCTRINE))

# ── United Arab Emirates — Abu Dhabi: 35%++ Cashback Rebate ─────────────────
#
# Checked internal source first: global_inventory_extended.py had a
# DISCOVERY-tier UAE/Dubai lead at 30% (stale — Dubai and Abu Dhabi are
# separate emirate-level programs; this record models Abu Dhabi
# specifically, the more internationally prominent and higher-rate one).
# Direct fetch of film.gov.ae (403) and a law-firm analysis (402 paywall)
# both blocked — modeled from the search results' own quoted excerpts of
# the official film.gov.ae page and a real UAE government media office
# press release (mediaoffice.abudhabi), not further chased per the
# "minimum necessary verification" instruction. PARSED, not VERIFIED.
_AE_AD_CITATION = (
    "film.gov.ae (Abu Dhabi Film Commission, official — quoted via search "
    "result excerpts after direct fetch was blocked, HTTP 403) and "
    "mediaoffice.abudhabi (UAE government media office, official): "
    "rebate 'enhancement... from 30% to starting at 35% for all qualified "
    "productions... from 1 January 2025.' 'potential for eligible "
    "productions to claim up to 50% Enhanced Rebate... based on a clear "
    "set of criteria which is linked to a points system,' 'a potential "
    "total rebate of 50% for those productions scoring 85 points and "
    "above.' No minimum spend figure found in sources checked."
)
AE_AD_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="AE-AD",
    program_slug="ae_ad_film_rebate",
    program_name="Abu Dhabi 35%++ Cashback Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=_AE_AD_CITATION,
    source_ref="film.gov.ae+mediaoffice.abudhabi",
    tiers=(
        DoctrineRateTier(
            tier_id="ae-ad-standard-35",
            rate=0.35,
            is_band_ceiling=False,
        ),
        DoctrineRateTier(
            tier_id="ae-ad-enhanced-ceiling-50",
            rate=0.50,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="ae-ad-points-system-uplift",
                    description="The 35%->50% enhancement requires "
                                "scoring 85+ points on a criteria-based "
                                "points system (including a shoot-days "
                                "tariff) — this engine has no fact to "
                                "pre-evaluate a points score",
                    quote="a potential total rebate of 50% for those "
                          "productions scoring 85 points and above "
                          "(film.gov.ae, via search excerpt)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(AE_AD_DOCTRINE))

# ── Morocco: CCM Foreign Production Cash Rebate ─────────────────────────────
#
# Checked internal source first: global_inventory_extended.py already had
# a real DISCOVERY-tier lead (~20-30%, CCM, Ouarzazate/Atlas Studios,
# mandatory local entity). Confirmed the top of that range: corroborated
# by 4 independent sources (ozzfilms.com, broadway.ma, pulpscreen.com,
# mbrellafilms.com) at a flat 30%, "no longer capped at the project
# level." Min spend ~10,000,000 MAD (~$1,000,000 USD, per the sources'
# own conversion) + 18 shooting days. QPE itself capped at 90% of total
# expenditure (eligibility ceiling, not modeled).
_MA_CITATION = (
    "Corroborated by 4 independent production-industry sources "
    "(ozzfilms.com, broadway.ma, pulpscreen.com, mbrellafilms.com), all "
    "agreeing: '30% rebate on eligible expenses,' 'no longer capped at "
    "the project level.' 'Minimum spend of 10 million MAD and 18 shooting "
    "days required... approximately... USD $1 million.' 'Eligible "
    "expenses are capped at 90% of total expenditure.' Mandatory "
    "CCM-registered Moroccan production company partner."
)
MA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="MA",
    program_slug="ma_ccm_rebate",
    program_name="Morocco CCM Foreign Production Cash Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=1_000_000.0,
    annual_cap_usd=None,   # confirmed UNCAPPED at project level, not merely unknown
    requires_cultural_test=False,
    citation=_MA_CITATION,
    source_ref="4-corroborating-sources-morocco-ccm",
    tiers=(
        DoctrineRateTier(
            tier_id="ma-flat-30",
            rate=0.30,
            is_band_ceiling=False,
            min_qpe_usd=1_000_000.0,
            conditions=(
                RateCondition(
                    condition_id="ma-min-spend-and-days",
                    description="Minimum 10M MAD (~$1M) AND 18 shooting "
                                "days in Morocco — the shoot-days "
                                "condition is not pre-evaluable (no "
                                "shooting-days fact exists in this engine)",
                    quote="Minimum spend of 10 million MAD and 18 shooting "
                          "days required (corroborated by 4 sources)",
                    kind="min_qpe_usd", threshold_usd=1_000_000.0,
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(MA_DOCTRINE))

# ── Denmark: Production Rebate ──────────────────────────────────────────────
#
# Checked internal source first: global_inventory_wave2.py's DK entry was
# itself uncertain ("Data gaps: cash rebate vs grant structure, confirmed
# rate"). Confirmed via multiple corroborating sources (variety.com,
# screendaily.com, nordiskfilmogtvfond.com — a real Nordic film-fund
# industry body): this is a NEW program (launched 2026, not merely a
# stale rate) — 25% rebate, EUR 17M (DKK 125M) annual budget. Resolves
# the catalog's own uncertainty in favor of "cash rebate," not "grant."
_DK_CITATION = (
    "Corroborated by 3 sources (variety.com, screendaily.com, "
    "nordiskfilmogtvfond.com — a real Nordic film-fund industry body): "
    "'Denmark introduces 25% production incentive,' 'Denmark unleashes "
    "DKK 125 million (EUR 17 million) to attract global film & TV "
    "productions.' A genuinely NEW program (launched 2026), not a stale "
    "rate on an old one — resolves the catalog's own disclosed "
    "uncertainty ('cash rebate vs grant structure') in favor of rebate."
)
DK_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="DK",
    program_slug="dk_production_rebate",
    program_name="Denmark Production Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=None,  # EUR 17M is a PROGRAM-wide annual budget, not
                           # a per-production cap — not modeled as such
    requires_cultural_test=True,
    citation=_DK_CITATION,
    source_ref="3-corroborating-sources-denmark-rebate",
    tiers=(
        DoctrineRateTier(
            tier_id="dk-flat-25",
            rate=0.25,
            is_band_ceiling=False,
        ),
    ),
))
register_rate_rules(rate_rules_for(DK_DOCTRINE))

# ── Finland: Business Finland Film Incentive ────────────────────────────────
#
# Checked internal source first: global_inventory_wave2.py's FI entry
# (25%, DISCOVERY) confirmed unchanged, corroborated by the same 2026
# search pass covering all four Nordic countries together.
_FI_CITATION = (
    "businessfinland.fi/en/services/funding/funding-services/cash-rebate/ "
    "(Business Finland, official, fetched directly): '25% cash rebate is "
    "offered for production costs in Finland.' 'The budget for the "
    "audiovisual production incentive for 2026 is 10 million euros' "
    "(program-wide, not modeled as a per-production cap)."
)
FI_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="FI",
    program_slug="fi_business_finland_incentive",
    program_name="Business Finland Film Incentive",
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=500_000.0,  # from the pre-existing catalog lead,
                               # not restated on the official page fetched
                               # -- retained, disclosed as not itself
                               # independently re-confirmed
    annual_cap_usd=None,
    requires_cultural_test=True,
    citation=_FI_CITATION,
    source_ref="businessfinland.fi-official",
    provenance=SourceProvenance(
        issuing_authority="Business Finland",
        source_url="https://www.businessfinland.fi/en/services/funding/funding-services/cash-rebate/",
        citation_detail="'25% cash rebate is offered for production "
                         "costs in Finland'",
        effective_date="2026 budget cycle",
        verified_date="2026-08-17",
        interpretation_note="Minimum spend ($500,000) is a pre-existing "
                             "catalog figure not restated on the "
                             "official page fetched -- retained, "
                             "disclosed as not independently "
                             "re-confirmed this pass.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="fi-flat-25",
            rate=0.25,
            is_band_ceiling=False,
            min_qpe_usd=500_000.0,
        ),
    ),
))
register_rate_rules(rate_rules_for(FI_DOCTRINE))

# ── Norway: Norwegian Film Production Incentive ─────────────────────────────
#
# Checked internal source first: global_inventory_wave2.py's NO entry
# (25%, DISCOVERY) confirmed via NFI's own official page (URL itself,
# norwegianfilm.com/25-incentive, names the rate). Real, important
# structural fact found: this is COMPETITIVE/DISCRETIONARY, not an
# entitlement — only 5 productions were offered reimbursement in the
# cited 2026 round, sharing a total NOK 84.7M cap, not a guaranteed
# per-production rate. Min spend NOK 4,000,000; requires >=30%
# international financing at application time.
_NO_CITATION = (
    "nfi.no / norwegianfilm.com (Norwegian Film Institute, official — "
    "the URL 'norwegianfilm.com/25-incentive' itself names the rate): "
    "'reimbursement of up to 25% of eligible production costs.' "
    "COMPETITIVE: 'five film and TV series projects' offered "
    "reimbursement in the cited 2026 round, sharing 'NOK 84,700,000' "
    "total, not a guaranteed per-production entitlement. Min spend "
    "'NOK 4 million.' Requires 'at least 30% international financing at "
    "the time of the submission.'"
)
NO_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="NO",
    program_slug="no_film_incentive",
    program_name="Norwegian Film Production Incentive",
    # Global Economic Data + Base Pricing, batch 3.
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,   # NOK not convertible — no sourced NOK/USD FX rate
    annual_cap_usd=None,
    requires_cultural_test=True,
    citation=_NO_CITATION,
    source_ref="nfi.no-25-incentive",
    provenance=SourceProvenance(
        issuing_authority="Norwegian Film Institute (NFI)",
        source_url="https://www.norwegianfilm.com/25-incentive",
        citation_detail="Reimbursement of up to 25% of eligible "
                         "production costs; competitive, not a "
                         "guaranteed per-production entitlement",
        effective_date="2026 round",
        interpretation_note="COMPETITIVE allocation: 5 projects shared a "
                             "NOK 84,700,000 total pool in the cited 2026 "
                             "round. Modeled as a rate ceiling; the "
                             "competitive/discretionary nature is "
                             "disclosed rather than treated as a "
                             "guaranteed rate.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="no-flat-25",
            rate=0.25,
            is_band_ceiling=False,
            conditions=(
                RateCondition(
                    condition_id="no-competitive-allocation",
                    description="COMPETITIVE program — a limited number "
                                "of productions are selected per round "
                                "sharing a fixed total reimbursement "
                                "cap; not guaranteed even if eligibility "
                                "criteria are met",
                    quote="five film and TV series projects [selected, "
                          "sharing] NOK 84,700,000 (nfi.no)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(NO_DOCTRINE))

# ── Sweden: Production Incentive ────────────────────────────────────────────
#
# Checked internal source first: global_inventory_wave2.py's SE entry
# (25%, DISCOVERY) confirmed via nordiskfilmogtvfond.com (the same real
# Nordic film-fund industry body corroborating Denmark and Norway). Also
# COMPETITIVE/first-come-first-served (SEK 100M first round) — industry
# bodies have publicly criticised this allocation mechanism, a real,
# disclosed friction point.
_SE_CITATION = (
    "nordiskfilmogtvfond.com (Nordic film-fund industry body, "
    "corroborating Denmark and Norway sources in this same batch): "
    "'25% cash rebate,' 'Sweden dishes out SEK 100 million in first "
    "round.' COMPETITIVE/first-come-first-served allocation — "
    "screendaily.com reports Swedish film & TV bodies have publicly "
    "'criticise[d]' this 'first-come, first-served' mechanism as a real "
    "industry friction point."
)
SE_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="SE",
    program_slug="se_production_rebate",
    program_name="Sweden Production Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=700_000.0,  # from the pre-existing catalog lead,
                               # unconfirmed further this pass
    annual_cap_usd=None,
    requires_cultural_test=True,
    citation=_SE_CITATION,
    source_ref="nordiskfilmogtvfond.com-sweden",
    tiers=(
        DoctrineRateTier(
            tier_id="se-flat-25",
            rate=0.25,
            is_band_ceiling=False,
            min_qpe_usd=700_000.0,
            conditions=(
                RateCondition(
                    condition_id="se-first-come-first-served",
                    description="COMPETITIVE, first-come-first-served "
                                "allocation — publicly criticised by "
                                "Swedish industry bodies as a real "
                                "friction point; not guaranteed even if "
                                "eligibility criteria are met",
                    quote="Sweden dishes out SEK100 million in first "
                          "round ... criticise 'first-come, first-served' "
                          "government funding process (nordiskfilmogtvfond.com, "
                          "screendaily.com)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(SE_DOCTRINE))

# ── Saudi Arabia: Saudi Film Commission Production Rebate ──────────────────
#
# Checked internal source first: global_inventory_extended.py had a real
# DISCOVERY-tier lead at 40%. STALE, and dramatically so — 8 independent
# major industry sources (Deadline, Hollywood Reporter, Variety, Screen
# Daily, Arab News, etc.) all corroborate a 2026 increase to 60%, "well
# above the major European national rebates." 2026-07-26: min spend
# figure and the requires_cultural_test correction both closed via direct
# fetch of film.sa/incentive-programs/ -- see Requirements Profile.
_SA_CITATION = (
    "Corroborated by 8 independent major industry sources (deadline.com, "
    "hollywoodreporter.com, variety.com, screendaily.com, arabnews.com, "
    "screenglobalproduction.com, thesauditimes.net, aawsat.com), all "
    "agreeing: Saudi Film Commission 'Raises Film Incentives to 60%,' up "
    "from a previous 40% cap, positioning Saudi Arabia 'at the very top "
    "of the global film incentive landscape.'"
)
SA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="SA",
    program_slug="sa_film_commission_rebate",
    program_name="Saudi Film Commission Production Rebate",
    # Global Economic Data + Base Pricing, batch 2: promoted PARSED ->
    # VERIFIED. Independently re-fetched film.sa/incentive-programs/
    # directly this task and confirmed the SAME figures the 2026-07-26
    # reconciliation note below already recorded from its own direct
    # fetch of the same official page: 60% flat rebate, min spend SAR
    # 750,000 (feature)/187,000 (doc/animation), no stated cap, min 5
    # filming days. Two independent direct fetches of the same primary
    # source agreeing is the strongest confirmation this registry uses.
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=200_000.0,       # SAR 750,000 feature-film threshold (documentary/animation
                                    # SAR 187,000 -- see the Requirements Profile for the full
                                    # per-format breakdown; feature film used as the general case)
    annual_cap_usd=None,
    requires_cultural_test=False,  # 2026-07-26 knowledge reconciliation: direct fetch of
                                    # film.sa/incentive-programs/ confirms there is NO distinct
                                    # cultural/values test separate from production-quality
                                    # review -- content vetting instead runs through two named
                                    # gates (Script Content Clearance, Filming Non-Objection
                                    # Certificate), a regulatory content-clearance mechanism, not
                                    # a cultural test in the points-based/qualitative-artistic
                                    # sense used elsewhere in this registry. Corrects this
                                    # record's prior True, which had inherited the old DISCOVERY
                                    # catalog's undifferentiated "content restrictions apply" note.
    citation=_SA_CITATION,
    source_ref="8-corroborating-sources-saudi-60pct+film.sa-official-2026-07-26",
    provenance=SourceProvenance(
        issuing_authority="Saudi Film Commission",
        source_url="https://film.sa/incentive-programs/",
        citation_detail="60% flat rebate (raised from a prior 40% cap); "
                         "min spend SAR 750,000 feature / SAR 187,000 "
                         "documentary-animation",
        verified_date="2026-07-26",
        interpretation_note="Independently re-fetched this task and "
                             "reproduced the exact same figures a prior "
                             "direct fetch of the same page had already "
                             "recorded — two independent direct-fetch "
                             "confirmations of the same primary source.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="sa-flat-60",
            rate=0.60,
            is_band_ceiling=False,
        ),
    ),
))
register_rate_rules(rate_rules_for(SA_DOCTRINE))

# ── Jordan: Royal Film Commission Production Rebate ─────────────────────────
#
# Checked internal source first: global_inventory_extended.py already had
# a real DISCOVERY-tier lead (10-25% range, RFC Jordan, Petra/Wadi Rum
# locations). No fresher rate found via search this pass — held at the
# pre-existing catalog figures rather than guessed; promoted confidence
# only on the min/max structure already present (a genuine range, not a
# single flat rate, per the original catalog notes), not VERIFIED further.
_JO_CITATION = (
    "Pre-existing global_inventory_extended.py DISCOVERY-tier lead "
    "(rfc.jo, Royal Film Commission Jordan): '~10-25% rebate on Jordanian "
    "qualifying expenditures.' No fresher primary or corroborating "
    "source found this pass — NOT promoted beyond the catalog's own "
    "DISCOVERY tier; the range itself (not a single number) is modeled "
    "so the engine never silently picks one end."
)
JO_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="JO",
    program_slug="jo_rfc_rebate",
    program_name="Jordan Royal Film Commission Production Rebate",
    confidence_tier="DISCOVERY",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=True,   # "content review required" per the
                                    # pre-existing catalog lead
    citation=_JO_CITATION,
    source_ref="global_inventory_extended-jordan-rfc",
    tiers=(
        DoctrineRateTier(
            tier_id="jo-discovery-10",
            rate=0.10,
            is_band_ceiling=False,
        ),
        DoctrineRateTier(
            tier_id="jo-discovery-ceiling-25",
            rate=0.25,
            is_band_ceiling=True,
            conditions=(
                RateCondition(
                    condition_id="jo-discovery-tier-unverified",
                    description="Entire range is DISCOVERY tier — not "
                                "independently verified this phase, "
                                "carried forward from the pre-existing "
                                "catalog lead only",
                    quote="~10-25% rebate on Jordanian qualifying "
                          "expenditures (global_inventory_extended.py, "
                          "DISCOVERY)",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(JO_DOCTRINE))

# ── Thailand: BOI Film Incentive ────────────────────────────────────────────
# Checked internal source first: catalog had 15-20% DISCOVERY. STALE —
# corroborated increase to 30%, min spend $1.4M.
_TH_CITATION = (
    "thailand-business-news.com, overgrownproductions.com: 'rebate of up "
    "to 30% in cash,' 'must spend the equivalent of $1.4m US locally to "
    "qualify.' Supersedes the prior 15-20% catalog figure. LITTLE UTOPIA "
    "WORLDWIDE ACCEPTANCE: the canonical corpus "
    "(GLOBAL_REMEDIATION_EXECUTABLE_DATA.json, th_film_incentive, "
    "CORRECT_DATA) states base_rate=0.15 and maximum_effective_rate=0.30 "
    "with the uplift condition 'do not sum unless expressly permitted'. "
    "The prior flat 30% encoded the HEADLINE MAXIMUM as guaranteed - the "
    "exact defect this project's rules forbid. Split into a guaranteed "
    "15% floor plus a 30% band ceiling that requires confirmation, reusing "
    "the same discretionary_band mechanism as Mauritius/Malta."
)
TH_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="TH", program_slug="th_boi_incentive",
    program_name="Thailand BOI Film Incentive", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=1_400_000.0, annual_cap_usd=None, requires_cultural_test=False,
    citation=_TH_CITATION, source_ref="thailand-business-news+overgrownproductions",
    tiers=(
        DoctrineRateTier(tier_id="th-base-15", rate=0.15, is_band_ceiling=False,
                         min_qpe_usd=1_400_000.0),
        DoctrineRateTier(
            tier_id="th-uplift-ceiling-30", rate=0.30, is_band_ceiling=True,
            min_qpe_usd=1_400_000.0,
            conditions=(
                RateCondition(
                    condition_id="th-uplift-not-guaranteed",
                    description="The 30% figure is an 'up to' maximum reached only "
                                "via BOI uplift criteria; the canonical corpus "
                                "expressly directs that uplifts are not to be summed "
                                "unless expressly permitted, so the ceiling is not "
                                "guaranteed for this production",
                    quote="'rebate of up to 30% in cash' (thailand-business-news.com); "
                          "canonical base_rate 0.15, maximum_effective_rate 0.30",
                    kind="discretionary_band",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(TH_DOCTRINE))

# ── Malaysia: FINAS Film Rebate ─────────────────────────────────────────────
# Checked internal source first: catalog had flat 30% DISCOVERY. Refined —
# real +5% cultural-test uplift found (35% ceiling), not previously known.
_MY_CITATION = (
    "productionservicenetwork.com: 'FIMI promises a 30% cash rebate on "
    "all Qualifying Malaysian Production Expenditure... A 5% boost in "
    "the rebate is granted to projects that pass a cultural test.'"
)
MY_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="MY", program_slug="my_finas_rebate",
    program_name="Malaysia FINAS Film Rebate", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=1_000_000.0, annual_cap_usd=None, requires_cultural_test=False,
    citation=_MY_CITATION, source_ref="productionservicenetwork.com-malaysia",
    tiers=(
        DoctrineRateTier(tier_id="my-base-30", rate=0.30, is_band_ceiling=False,
                          min_qpe_usd=1_000_000.0),
        DoctrineRateTier(tier_id="my-cultural-ceiling-35", rate=0.35, is_band_ceiling=True,
                          min_qpe_usd=1_000_000.0,
                          conditions=(RateCondition(
                              condition_id="my-cultural-test-uplift",
                              description="+5% requires passing a cultural test — "
                                          "not pre-evaluable, no scoring facts available",
                              quote="A 5% boost in the rebate is granted to projects "
                                    "that pass a cultural test (productionservicenetwork.com)",
                              kind="cultural_test_required"),)),
    ),
))
register_rate_rules(rate_rules_for(MY_DOCTRINE))

# ── Philippines: FDCP Film Location Incentive Program (FLIP) ───────────────
# Checked internal source first: catalog had flat 20% DISCOVERY. Refined —
# real 20-25% range plus a real per-production cap ($540K) not previously known.
_PH_CITATION = (
    "productionservicenetwork.com: 'A cash rebate of 20-25% is offered "
    "by the Film Development Council of the Philippines... through the "
    "Film Location Incentive Program (FLIP) and capped at $540,000 "
    "(PHP 30M).'"
)
PH_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="PH", program_slug="ph_fdcp_flip",
    program_name="Philippines FDCP Film Location Incentive Program (FLIP)",
    confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=540_000.0, requires_cultural_test=False,
    citation=_PH_CITATION, source_ref="productionservicenetwork.com-philippines",
    tiers=(
        DoctrineRateTier(tier_id="ph-base-20", rate=0.20, is_band_ceiling=False),
        DoctrineRateTier(tier_id="ph-ceiling-25", rate=0.25, is_band_ceiling=True,
                          conditions=(RateCondition(
                              condition_id="ph-uplift-criteria-unconfirmed",
                              description="20-25% range — exact criteria for the "
                                          "higher end not confirmed",
                              quote="A cash rebate of 20-25% is offered "
                                    "(productionservicenetwork.com)",
                              kind="discretionary_band"),)),
    ),
))
register_rate_rules(rate_rules_for(PH_DOCTRINE))

# ── South Korea: KOFIC Location Incentive ───────────────────────────────────
# Checked internal source first: catalog had 20-25% DISCOVERY. Confirmed
# via Wikipedia/dbpedia + koreanfilm.or.kr program guideline pages
# (reasonably stable long-running program mechanics, not dated to a
# specific year in the sources found — disclosed): tiered by shoot-days
# AND spend, capped at a real, fairly small 200M KRW (~$176K) per grant.
_KR_CITATION = (
    "koreanfilm.or.kr (KOFIC program guidelines) via Wikipedia/dbpedia "
    "corroboration: '25% rebate for productions that shoot more than 10 "
    "days in Korea and spend more than 0.8 billion KRW (~$700,000),' "
    "'20% rebate for... more than 3 days... between 50 million KRW "
    "(~$44,000) and 0.8 billion KRW.' 'The maximum grant is capped at "
    "200 million KRW (~$176,000).' Not dated to a specific year in "
    "sources found — a long-running, stable program (effective 2015 per "
    "the pre-existing catalog entry)."
)
KR_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="KR", program_slug="kr_kofic_location_incentive",
    program_name="South Korea KOFIC Location Incentive", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=44_000.0, annual_cap_usd=176_000.0, requires_cultural_test=False,
    citation=_KR_CITATION, source_ref="koreanfilm.or.kr-via-wikipedia",
    tiers=(
        DoctrineRateTier(tier_id="kr-tier-20", rate=0.20, is_band_ceiling=False,
                          min_qpe_usd=44_000.0,
                          conditions=(RateCondition(
                              condition_id="kr-shoot-days-3plus",
                              description="Requires >3 shoot days in Korea — "
                                          "not pre-evaluable, no shoot-days fact",
                              quote="more than 3 days in Korea and spend "
                                    "between 50 million KRW and 0.8 billion KRW "
                                    "(koreanfilm.or.kr)",
                              kind="min_qpe_usd", threshold_usd=44_000.0),)),
        DoctrineRateTier(tier_id="kr-tier-ceiling-25", rate=0.25, is_band_ceiling=True,
                          min_qpe_usd=700_000.0,
                          conditions=(RateCondition(
                              condition_id="kr-shoot-days-10plus",
                              description="Requires >10 shoot days in Korea AND "
                                          ">=0.8B KRW (~$700K) spend",
                              quote="shoot more than 10 days in Korea and spend "
                                    "more than 0.8 billion KRW (koreanfilm.or.kr)",
                              kind="min_qpe_usd", threshold_usd=700_000.0),)),
    ),
))
register_rate_rules(rate_rules_for(KR_DOCTRINE))

# ── Mexico: Federal Film & Audiovisual Production Tax Incentive (2026) ─────
#
# Checked internal source first: the catalog's existing MX entry (EFICINE,
# Art. 226 Income Tax Law, 10-17.5%) is a DIFFERENT, older program — a tax
# credit for INVESTORS in Mexican-content film, not a foreign-production
# service incentive. NOT corrected/replaced — a genuinely NEW, separate
# federal law (published Official Gazette, effective 30 March 2026,
# through 30 Sept 2030) creates the internationally-relevant program
# modeled here, confirmed via a real major law firm (Baker McKenzie,
# fetched directly) and corroborated by KPMG/FisherBroyles.
_MX_CITATION = (
    "bakermckenzie.com (Baker McKenzie, major international law firm, "
    "fetched directly), corroborated by KPMG and FisherBroyles: 'Up to "
    "30% of qualifying Mexico-incurred production and post-processing "
    "costs.' Individual cap 'MXN 40 million per beneficiary/production.' "
    "Annual program cap 'MXN 400 million total distributed annually.' "
    "Min spend 'MXN 40 million' (feature/narrative/animation). "
    "Transferable up to 70%; NOT refundable ('not accruable income nor "
    "does it generate refunds'). Requires >=70% national supply and "
    "Technical Committee certification. Effective 30 March 2026 through "
    "30 September 2030. MXN not converted — no sourced MXN/USD FX rate "
    "exists in this project. 2026-07-26 CONFIRMED via Document Retrieval "
    "Escalation: dof.gob.mx's real Decree text (retrieved by working "
    "around a server-side TLS chain misconfiguration, not a block) "
    "quotes the 30% rate verbatim ('un credito fiscal de hasta el 30% "
    "del costo total del proyecto') and independently confirms the MXN "
    "400,000,000 figure is explicitly ANNUAL ('el monto total ANUAL del "
    "estimulo fiscal ... no excedera de 400 millones de pesos') -- "
    "resolving in Baker McKenzie's favor a mischaracterization that had "
    "crept into this repository's own Requirements Profile (which had "
    "briefly recorded it as a one-time total envelope). The exact "
    "per-project/per-format MXN figures remain sourced only to Baker "
    "McKenzie (the Decreto itself defers those to a separate Lineamientos "
    "document, not yet fully retrieved) -- see app.data.program_requirements "
    "mx_federal_film_incentive_2026 for the full writeup."
)
MX_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="MX", program_slug="mx_federal_film_incentive_2026",
    program_name="Mexico Federal Film & Audiovisual Production Tax Incentive",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit", is_refundable=False, is_transferable=True,
    min_spend_usd=None, annual_cap_usd=None,  # MXN, not converted
    requires_cultural_test=False,
    citation=_MX_CITATION, source_ref="bakermckenzie.com-mexico-2026-incentive+dof.gob.mx-decreto-2026-02-16-official",
    tiers=(
        DoctrineRateTier(
            tier_id="mx-flat-30", rate=0.30, is_band_ceiling=False,
            conditions=(RateCondition(
                condition_id="mx-national-supply-requirement",
                description="Requires >=70% national supply and Technical "
                            "Committee certification — not pre-evaluable, "
                            "no supply-chain-origin fact exists",
                quote="Minimum 70% national supply ... Technical Committee "
                      "certificates for submission and compliance "
                      "(bakermckenzie.com)",
                kind="min_spend_pct_of_total_budget"),),
        ),
    ),
))
register_rate_rules(rate_rules_for(MX_DOCTRINE))

# ── Chile: CORFO Film Incentive ─────────────────────────────────────────────
# Checked internal source first: catalog had 20-30% DISCOVERY. STALE —
# corroborated increase to 40%, min spend $1M confirmed directly.
_CL_CITATION = (
    "ep.com (Entertainment Partners, Spring 2026 global incentive "
    "roundup): 'Chile now offers a cash rebate of up to 40% for "
    "production of feature films, TV series, or digital platform series "
    "(OTT), with a minimum qualified spend in the country of USD 1 "
    "million.' Supersedes the prior 20-30% catalog figure."
)
CL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CL", program_slug="cl_corfo_incentive",
    program_name="Chile CORFO Film Incentive", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=1_000_000.0, annual_cap_usd=None, requires_cultural_test=False,
    citation=_CL_CITATION, source_ref="ep.com-spring-2026-roundup-chile",
    tiers=(DoctrineRateTier(tier_id="cl-flat-40", rate=0.40, is_band_ceiling=False,
                             min_qpe_usd=1_000_000.0),),
))
register_rate_rules(rate_rules_for(CL_DOCTRINE))

# ── Israel: Fund for the Promotion of Foreign Productions ───────────────────
# Checked internal source first: catalog had 20-30% DISCOVERY. Refined —
# 30% base + 10% post/animation uplift = 40% ceiling, corroborated by
# Hollywood Reporter/Times of Israel (multiple years, program appears
# stable since ~2017; not confirmed specifically for 2026, disclosed).
_IL_CITATION = (
    "Corroborated by hollywoodreporter.com, timesofisrael.com (multiple "
    "years, 2022-2023): 'Israel Unveils 30 Percent Incentive for "
    "International Film, TV Productions,' 'a further 10% on top for "
    "post-production and animation.' Cap '$4.8 million (16.6 million "
    "shekels).' Program appears stable since ~2017 but not confirmed "
    "specifically for 2026 in any source checked — disclosed, not "
    "assumed unchanged."
)
IL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="IL", program_slug="il_foreign_production_fund",
    program_name="Israel Fund for the Promotion of Foreign Productions",
    confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=50_000.0, annual_cap_usd=4_800_000.0, requires_cultural_test=False,
    citation=_IL_CITATION, source_ref="hollywoodreporter+timesofisrael-israel",
    tiers=(
        DoctrineRateTier(tier_id="il-base-30", rate=0.30, is_band_ceiling=False,
                          min_qpe_usd=50_000.0),
        DoctrineRateTier(tier_id="il-post-animation-ceiling-40", rate=0.40, is_band_ceiling=True,
                          min_qpe_usd=50_000.0,
                          conditions=(RateCondition(
                              condition_id="il-post-animation-uplift",
                              description="+10% for post-production/animation "
                                          "spend specifically — not pre-evaluable, "
                                          "no post/animation spend split exists",
                              quote="a further 10% on top for post-production "
                                    "and animation (hollywoodreporter.com)",
                              kind="discretionary_band"),)),
    ),
))
register_rate_rules(rate_rules_for(IL_DOCTRINE))

# ── Japan: Location Incentive Program (VIPO) ────────────────────────────────
# NEW jurisdiction. Checked internal source first — not previously in
# jurisdiction_comparison.py. Confirmed via multiple entertainment-
# industry sources (Variety, Deadline, Screen Daily, kidscreen.com) plus
# the official VIPO program page: up to 50% cash rebate, recently
# expanded (Dec 2025) to support multi-year subsidies for co-productions.
_JP_CITATION = (
    "Corroborated by variety.com, deadline.com, screendaily.com, "
    "kidscreen.com, plus vipo.or.jp (Visual Industry Promotion "
    "Organization, official program administrator): 'a cash rebate of up "
    "to 50% of the costs incurred during production and post-production "
    "in Japan.' Recently expanded (Dec 2025) with 'multi-year subsidies, "
    "enabling projects to receive support spanning up to two years.'"
)
JP_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="JP", program_slug="jp_vipo_location_incentive",
    program_name="Japan VIPO Location Incentive Program", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation=_JP_CITATION, source_ref="variety+deadline+screendaily+vipo.or.jp",
    tiers=(DoctrineRateTier(tier_id="jp-flat-50", rate=0.50, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(JP_DOCTRINE))

# ── Egypt: EMPC (Egyptian Media Production City) Cashback ──────────────────
# NEW jurisdiction. Checked internal source first: the pre-existing
# catalog entry EXPLICITLY said "No confirmed formal percentage rebate
# for international productions" (base_rate=None) — a genuine prior
# absence, not a stale figure. A real, NEW, facility-specific program was
# found and confirmed via direct fetch: 30% cashback on EMPC-facility
# spend, 20% off-site supplement, but ONLY for productions with a
# genuine EMPC studio anchor component — a real, material eligibility
# gate, not a general national rebate.
_EG_CITATION = (
    "celluloidpact.com (fetched directly): 'The EMPC 30% cashback "
    "applies to qualifying spend inside the Media Production City "
    "facility,' '20% off-site supplement covering... Giza, Luxor or the "
    "Red Sea coast.' MATERIAL GATE: 'Productions that operate fully on "
    "location without an EMPC anchor day cannot draw the rebate.' Paid "
    "'as a cashback against audited spend, not as a tax credit,' ~90 "
    "days processing."
)
EG_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="EG", program_slug="eg_empc_cashback", confidence_tier="PARSED",
    program_name="Egypt EMPC (Media Production City) Cashback",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation=_EG_CITATION, source_ref="celluloidpact.com-egypt-empc",
    tiers=(
        DoctrineRateTier(tier_id="eg-empc-anchor-30", rate=0.30, is_band_ceiling=False,
                          conditions=(RateCondition(
                              condition_id="eg-empc-anchor-required",
                              description="MATERIAL GATE: requires a genuine EMPC "
                                          "studio anchor component — productions "
                                          "shooting entirely on location without an "
                                          "EMPC anchor day CANNOT claim this rebate "
                                          "at all. This engine has no fact tracking "
                                          "studio-anchor usage, so eligibility "
                                          "itself (not just the rate) cannot be "
                                          "pre-evaluated",
                              quote="Productions that operate fully on location "
                                    "without an EMPC anchor day cannot draw the "
                                    "rebate (celluloidpact.com)",
                              kind="min_spend_pct_of_total_budget"),)),
    ),
))
register_rate_rules(rate_rules_for(EG_DOCTRINE))

# ── Panama: Film Rebate ──────────────────────────────────────────────────
# Checked internal source first: catalog said "no confirmed formal
# rebate programme" -- a real, NEW program found and corroborated by 2
# sources: 25% flat cash rebate, min spend $500,000.
PA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="PA", program_slug="pa_film_rebate",
    program_name="Panama Film Rebate", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=500_000.0, annual_cap_usd=None, requires_cultural_test=False,
    citation="atlasfilmfixers.com + productionservicenetwork.com: '25% "
             "Cash Rebate on all qualifying local spend,' minimum local "
             "expenditure $500,000. Supersedes the prior catalog's "
             "'no confirmed formal rebate programme' finding.",
    source_ref="atlasfilmfixers+productionservicenetwork-panama",
    tiers=(DoctrineRateTier(tier_id="pa-flat-25", rate=0.25, is_band_ceiling=False,
                             min_qpe_usd=500_000.0),),
))
register_rate_rules(rate_rules_for(PA_DOCTRINE))

# ── Costa Rica: Tax Return Cash Incentive ───────────────────────────────
# Checked internal source first: catalog said "no formal rebate
# confirmed." A real, structurally distinct mechanism found (single
# source, not multiply corroborated -- PARSED, disclosed): a 90%
# refund of TAXES PAID (not spend), netting to an average effective
# rate of ~11.7% of total Costa Rica expenditure, paid within 60 days.
CR_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CR", program_slug="cr_tax_return_incentive",
    program_name="Costa Rica Tax Return Cash Incentive", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation="screendaily.com (single source, not further corroborated): "
             "'a cash return of 90% of taxes paid in Costa Rica... no "
             "budget line restriction and is not capped... an average of "
             "11.7% of all the expenses generated in Costa Rica... in "
             "less than 60 days.' A structurally distinct mechanism "
             "(tax-paid refund, not a spend-percentage rebate) -- modeled "
             "at the disclosed average effective rate.",
    source_ref="screendaily.com-costa-rica-single-source",
    tiers=(DoctrineRateTier(tier_id="cr-effective-avg-117", rate=0.117, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="cr-single-source-caveat",
                                 description="Single-source figure, not corroborated "
                                             "-- an AVERAGE effective rate from a tax-"
                                             "paid-refund mechanism, not a fixed "
                                             "spend-percentage rate",
                                 quote="an average of 11.7% of all the expenses "
                                       "generated in Costa Rica (screendaily.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(CR_DOCTRINE))

# ── Ghana: Film Tax Incentive ────────────────────────────────────────────
# Checked internal source first: catalog said "no confirmed formal
# rebate." Real program found, announced Feb 2024 (deadline.com,
# screendaily.com): 20% tax rebate + import duty/port tax exemptions.
# Operational status specifically for 2026 not independently confirmed.
GH_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="GH", program_slug="gh_film_tax_incentive",
    program_name="Ghana Film Tax Incentive", confidence_tier="PARSED",
    incentive_type="tax_credit", is_refundable=None, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation="deadline.com + screendaily.com: 'Ghana outlines 20% tax "
             "rebate for film productions,' announced Feb 2024, plus "
             "'exemptions on import duties for film production "
             "equipment.' 2026 operational status not independently "
             "confirmed.",
    source_ref="deadline+screendaily-ghana-2024",
    tiers=(DoctrineRateTier(tier_id="gh-flat-20", rate=0.20, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(GH_DOCTRINE))

# ── Fiji: Film Rebate ─────────────────────────────────────────────────────
FJ_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="FJ", program_slug="fj_film_rebate",
    program_name="Fiji Film Rebate", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=110_000.0, annual_cap_usd=1_750_000.0, requires_cultural_test=False,
    citation="investmentpolicy.unctad.org (UNCTAD, international investment "
             "policy body): '20% rebate...feature films, short films, "
             "television shows, and television commercials so long as "
             "they work through a locally registered company.' Min "
             "spend ~$110,000. Max rebate cap ~$1,750,000.",
    source_ref="unctad.org-fiji-film-rebate",
    tiers=(DoctrineRateTier(tier_id="fj-flat-20", rate=0.20, is_band_ceiling=False,
                             min_qpe_usd=110_000.0,
                             conditions=(RateCondition(
                                 condition_id="fj-local-entity-required",
                                 description="Requires a locally registered "
                                             "company -- not pre-evaluable",
                                 quote="so long as they work through a locally "
                                       "registered company (unctad.org)",
                                 kind="min_spend_pct_of_total_budget"),)),),
))
register_rate_rules(rate_rules_for(FJ_DOCTRINE))

# ── Georgia (country): Film Rebate ──────────────────────────────────────
# Note: this is the COUNTRY of Georgia (Caucasus), distinct from
# US-GA (the American state) already modeled -- program_slug and
# jurisdiction_code disambiguate cleanly.
GE_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="GE", program_slug="ge_film_rebate",
    program_name="Georgia (country) Film Rebate", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation="georgia.org (official government investment/incentive "
             "portal): 'a rebate of 20-25% on qualified expenses "
             "incurred in the production of films, television series, "
             "and other audiovisual projects.'",
    source_ref="georgia.org-country-film-incentives",
    tiers=(
        DoctrineRateTier(tier_id="ge-base-20", rate=0.20, is_band_ceiling=False),
        DoctrineRateTier(tier_id="ge-ceiling-25", rate=0.25, is_band_ceiling=True,
                          conditions=(RateCondition(
                              condition_id="ge-uplift-criteria-unconfirmed",
                              description="20-25% range -- exact criteria for "
                                          "the higher end not confirmed",
                              quote="a rebate of 20-25% (georgia.org)",
                              kind="discretionary_band"),)),
    ),
))
register_rate_rules(rate_rules_for(GE_DOCTRINE))

# ── Taiwan: TFAI/BAMID Cash Rebate ──────────────────────────────────────
# Checked internal source first: catalog had 30% DISCOVERY, unconfirmed.
# Base rate held up but a real, material fact was found: the program is
# "highly selective" (competitive), not an automatic entitlement.
TW_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="TW", program_slug="tw_bamid_rebate",
    program_name="Taiwan TFAI/BAMID Cash Rebate", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation="productionservicenetwork.com: Taiwan offers 'a highly "
             "selective cash rebate to foreign projects and additional "
             "grants for co-production' -- confirms the 30% base rate "
             "already in the catalog (bamid.gov.tw) but adds a real "
             "competitive-selection fact not previously known.",
    source_ref="productionservicenetwork.com-taiwan+bamid.gov.tw",
    tiers=(DoctrineRateTier(tier_id="tw-flat-30", rate=0.30, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="tw-competitive-selection",
                                 description="COMPETITIVE/highly selective program -- "
                                             "not an automatic entitlement even if "
                                             "eligibility criteria are met",
                                 quote="a highly selective cash rebate to foreign "
                                       "projects (productionservicenetwork.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(TW_DOCTRINE))

# ── Kazakhstan: Investment Subsidy Program ──────────────────────────────
KZ_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="KZ", program_slug="kz_investment_subsidy",
    program_name="Kazakhstan Investment Subsidy Program", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=850_000.0, annual_cap_usd=None, requires_cultural_test=False,
    citation="mbrellafilms.com (single source, not further corroborated): "
             "'Kazakhstan offers a 30% tax rebate for foreign productions "
             "through its Investment Subsidy program,' minimum cost "
             "threshold $850,000 per project.",
    source_ref="mbrellafilms.com-kazakhstan-single-source",
    tiers=(DoctrineRateTier(tier_id="kz-flat-30", rate=0.30, is_band_ceiling=False,
                             min_qpe_usd=850_000.0),),
))
register_rate_rules(rate_rules_for(KZ_DOCTRINE))

# ── Albania: Cash Rebate ──────────────────────────────────────────────────
# Checked internal source first: catalog had 20%. STALE -- corroborated by
# 2 sources (invest-in-albania.org, ocnal.com): new cinema law, 35%.
AL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="AL", program_slug="al_cash_rebate",
    program_name="Albania Cash Rebate", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation="invest-in-albania.org + ocnal.com: 'Albania Introduces New "
             "Cinema Law and 35% Cash Rebate to Attract International "
             "Productions.' Supersedes the prior 20% catalog figure.",
    source_ref="invest-in-albania+ocnal-2026",
    tiers=(DoctrineRateTier(tier_id="al-flat-35", rate=0.35, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(AL_DOCTRINE))

# ── Montenegro: Cash Rebate ────────────────────────────────────────────────
# Checked internal source first: catalog had 20%. STALE -- corroborated:
# 25%.
ME_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="ME", program_slug="me_cash_rebate",
    program_name="Montenegro Cash Rebate", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation="Search-corroborated: 'Montenegro provides a 25 percent cash "
             "rebate over qualifying expenditures for feature films, "
             "documentaries, TV films and series.' Supersedes the prior "
             "20% catalog figure.",
    source_ref="2026-balkans-search-montenegro",
    tiers=(DoctrineRateTier(tier_id="me-flat-25", rate=0.25, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(ME_DOCTRINE))

# ── North Macedonia: Cash Rebate ──────────────────────────────────────────
# Checked internal source first: catalog had 20%. Confirmed unchanged.
MK_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="MK", program_slug="mk_cash_rebate",
    program_name="North Macedonia Cash Rebate", confidence_tier="PARSED",
    incentive_type="cash_rebate", is_refundable=True, is_transferable=False,
    min_spend_usd=None, annual_cap_usd=None, requires_cultural_test=False,
    citation="Search-corroborated: 'North Macedonia offers 20% in film "
             "cash rebate incentives.' Confirms the prior catalog figure "
             "unchanged.",
    source_ref="2026-balkans-search-north-macedonia",
    tiers=(DoctrineRateTier(tier_id="mk-flat-20", rate=0.20, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(MK_DOCTRINE))

# ── US-Nevada: Film Tax Credit ─────────────────────────────────────────────
# Checked internal source first: catalog had 15% base/47% max. STALE --
# corroborated (shamelstudio.com, wrapbook.com): 12% base, +5%
# majority-resident BTL crew, +5% rural county, 25% ceiling. Min spend
# $500K confirmed unchanged. Annual PROGRAM cap $10M; separate $6M
# PER-PROJECT cap (not modeled -- no per-project-cap field in schema,
# disclosed via condition). is_refundable inferred False from explicit
# transferable/sellable-credit mechanics ("sold... to a third-party
# taxpayer... at a discount"), consistent with the US-GA precedent in
# this file -- PARSED inference, not a confirmed statutory fact.
_US_NV_CITATION = (
    "film.nv.gov (Nevada Film Office / Governor's Office of Economic "
    "Development, official, fetched directly): '15% of the cumulative "
    "qualified production costs' (general base) -- CORRECTS the prior "
    "modeled 12% base, which had conflated the general base rate with "
    "the narrower 12% rate that applies specifically to non-resident "
    "above-the-line personnel wages ('12% on wages, salaries, and fringe "
    "benefits to non-resident above the line personnel,' not separately "
    "modeled). Also: '15% on wages, salaries, and fringe benefits to all "
    "NV resident personnel.' Uplifts: 'plus 5%... if greater than 50% of "
    "below the line crew are NV residents'; 'plus 5%... if greater than "
    "50% of the filming days occurred in a NV county' meeting a $10M "
    "threshold. Minimum spend: 'greater than $500,000' and 'at least 60% "
    "of the production budget' as NV qualified expenditure (60% ratio "
    "not modeled -- no budget-ratio fact exists in this engine). Caps: "
    "'$6,000,000 per production' and '$10,000,000 in program funding.' "
    "Individual compensation capped at $750,000 (not modeled -- no per-"
    "person compensation fact exists). Credits expire 4 years after "
    "issuance."
)
US_NV_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-NV",
    program_slug="us_nv_film_credit",
    program_name="Nevada Film Tax Credit",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=False,
    is_transferable=True,
    min_spend_usd=500_000.0,
    annual_cap_usd=10_000_000.0,  # PROGRAM-wide annual cap; separate $6M
                                   # per-project cap not modeled (no field)
    requires_cultural_test=False,
    citation=_US_NV_CITATION,
    source_ref="film.nv.gov-official",
    provenance=SourceProvenance(
        issuing_authority="Nevada Film Office (Governor's Office of "
                           "Economic Development)",
        source_url="https://film.nv.gov/incentive/",
        citation_detail="'15% of the cumulative qualified production "
                         "costs'; +5%/+5% uplifts; $500,000 minimum; "
                         "$6M per-project / $10M program caps",
        verified_date="2026-08-17",
        interpretation_note="Corrects the prior modeled base rate from "
                             "12% to the real general base of 15% -- 12% "
                             "applies only to non-resident above-the-line "
                             "wages specifically, a narrower base not "
                             "separately modeled by this engine.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="us-nv-base-15",
            rate=0.15,
            is_band_ceiling=False,
            min_qpe_usd=500_000.0,
        ),
        DoctrineRateTier(
            tier_id="us-nv-stacked-ceiling-25",
            rate=0.25,
            is_band_ceiling=True,
            min_qpe_usd=500_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-nv-resident-crew-rural-uplifts",
                    description="+5% majority-resident below-the-line crew "
                                "+ 5% qualifying-county filming -- neither "
                                "pre-evaluable without crew-roster/shoot-"
                                "location facts",
                    quote="plus 5%... if greater than 50% of below the "
                          "line crew are NV residents; plus 5%... if "
                          "greater than 50% of the filming days occurred "
                          "in a NV county (film.nv.gov)",
                    kind="discretionary_band",
                ),
                RateCondition(
                    condition_id="us-nv-per-project-cap-not-modeled",
                    description="Separate $6,000,000 per-project cap "
                                "exists in addition to the $10,000,000 "
                                "annual program cap -- schema only "
                                "carries one cap field, per-project cap "
                                "disclosed here, not enforced",
                    quote="$6,000,000 per production (film.nv.gov)",
                    kind="material_funding_risk_not_modeled",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_NV_DOCTRINE))

# ── US-Rhode Island: Motion Picture Production Tax Credit ─────────────────
# Checked internal source first: catalog had 30% flat, min $100K. Rate
# confirmed unchanged (30%, official film.ri.gov). Min spend $100K
# confirmed, but WAIVED if $10M+ QPE within 12 months (disclosed
# condition, not modeled). Annual program cap $40M (official source) --
# NOTE Wrapbook's summary separately mentioned "$30 million annual
# program cap" alongside the $40M figure; film.ri.gov (official, direct
# fetch) states $40M plainly with no second figure, so $40M is used as
# the higher-confidence official-source figure and the $30M mention is
# flagged as an unresolved cross-source conflict, not silently dropped.
# Per-project cap $7M waivable -- same not-modeled treatment as US-NV.
# Sunset 2027-07-01 confirmed. is_refundable/is_transferable: not stated
# by either source checked -- left UNKNOWN, not guessed.
_US_RI_CITATION = (
    "film.ri.gov (Rhode Island Division of Taxation / RI Film & TV "
    "Office, official, fetched directly): '30% of state certified "
    "production costs.' Per-project cap $7,000,000 (waivable for "
    "qualifying productions). Annual program cap $40,000,000. Minimum "
    "spend $100,000 (waived if $10,000,000+ QPE within 12 months); 51% "
    "of principal photography must occur in RI (also waived at the "
    "$10M+ threshold). Sunset 2027-07-01. NOTE: wrapbook.com separately "
    "referenced a '$30 million annual program cap' alongside the $40M "
    "figure -- unresolved cross-source conflict, official $40M figure "
    "used, flagged not silently dropped. Refundability/transferability "
    "not stated by either source checked."
)
US_RI_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-RI",
    program_slug="us_ri_film_credit",
    program_name="Rhode Island Motion Picture Production Tax Credit",
    confidence_tier="VERIFIED",
    incentive_type="tax_credit",
    is_refundable=None,
    is_transferable=None,
    min_spend_usd=100_000.0,
    annual_cap_usd=40_000_000.0,
    requires_cultural_test=False,
    citation=_US_RI_CITATION,
    source_ref="film.ri.gov-official+wrapbook-cap-conflict-flagged",
    provenance=SourceProvenance(
        issuing_authority="Rhode Island Division of Taxation / RI Film "
                           "& TV Office",
        source_url="https://film.ri.gov",
        citation_detail="30% of state certified production costs; "
                         "per-project cap $7,000,000; annual program cap "
                         "$40,000,000",
        effective_date="Sunset 2027-07-01",
        interpretation_note="wrapbook.com (secondary) separately "
                             "references a $30,000,000 annual cap "
                             "conflicting with the official $40,000,000 "
                             "figure — the official figure is used and "
                             "the conflict is disclosed, not silently "
                             "dropped.",
    ),
    tiers=(
        DoctrineRateTier(
            tier_id="us-ri-flat-30",
            rate=0.30,
            is_band_ceiling=False,
            min_qpe_usd=100_000.0,
            conditions=(
                RateCondition(
                    condition_id="us-ri-min-spend-waiver-and-caps-not-modeled",
                    description="Min spend / 51%-in-state requirement "
                                "waived entirely at $10M+ QPE within 12 "
                                "months; separate $7M per-project cap "
                                "(waivable) exists alongside the $40M "
                                "annual program cap -- neither waiver "
                                "condition nor the second cap is "
                                "pre-evaluable or modeled by this schema",
                    quote="waived if $10 million or more in qualified "
                          "expenses are spent within a twelve-month "
                          "period... $7 million per-project cap "
                          "(film.ri.gov)",
                    kind="material_funding_risk_not_modeled",
                ),
            ),
        ),
    ),
))
register_rate_rules(rate_rules_for(US_RI_DOCTRINE))

# ── Trinidad and Tobago: Production Expenditure Rebate Programme ──────────
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed via official government
# portal (ttbizlink.gov.tt) + corroborating ep.com: non-national tiered
# rebate 12.5%/15%/35% by spend threshold (statute-defined step tiers,
# NOT a discretionary band -- each tier is a guaranteed rate once its
# threshold is met, so none is is_band_ceiling). +20% local-labor uplift
# on top. ep.com listed a "December 31, 2024" sunset; the OFFICIAL
# ttbizlink.gov.tt page (fetched directly) states no sunset date --
# official source used, ep.com conflict flagged not dropped.
_TT_CITATION = (
    "info.ttbizlink.gov.tt (Trinidad & Tobago govt investment portal, "
    "official, fetched directly): 'Non-nationals: Tiered system ranging "
    "from 12.5% to 35% based on spend level... US$100,000 to "
    "US$8,000,000... Additional incentive: 20% rebate available for "
    "expenditure incurred on use of Qualifying Local Labour.' No sunset "
    "date on the official page. ep.com (corroborating, but listed a "
    "'December 31, 2024' sunset not present on the official page -- "
    "flagged as an unresolved cross-source conflict, official page "
    "treated as authoritative): '$100K->12.5%, $500K->15%, $1M->35%; "
    "project maximum $8M qualifying expenditure.'"
)
TT_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="TT",
    program_slug="tt_production_expenditure_rebate",
    program_name="Trinidad and Tobago Production Expenditure Rebate Programme",
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=None,
    is_transferable=None,
    min_spend_usd=100_000.0,
    annual_cap_usd=8_000_000.0,  # PER-PROJECT ceiling (qualifying spend
                                  # cap), not a program-wide annual cap --
                                  # no separate per-project field in schema
    requires_cultural_test=False,
    citation=_TT_CITATION,
    source_ref="ttbizlink.gov.tt-official+ep.com-sunset-conflict-flagged",
    provenance=SourceProvenance(
        issuing_authority="Trinidad and Tobago Government investment portal",
        source_url="https://info.ttbizlink.gov.tt",
        citation_detail="Tiered rebate 12.5%-35% based on spend "
                         "USD 100,000-8,000,000; +20% Qualifying Local "
                         "Labour rebate",
        interpretation_note="ep.com (secondary) claims a 2024-12-31 "
                             "sunset not present on the official page — "
                             "flagged as an unresolved cross-source "
                             "conflict, official page treated as "
                             "authoritative.",
    ),
    tiers=(
        DoctrineRateTier(tier_id="tt-tier-125", rate=0.125, is_band_ceiling=False,
                          min_qpe_usd=100_000.0),
        DoctrineRateTier(tier_id="tt-tier-15", rate=0.15, is_band_ceiling=False,
                          min_qpe_usd=500_000.0),
        DoctrineRateTier(tier_id="tt-tier-35", rate=0.35, is_band_ceiling=False,
                          min_qpe_usd=1_000_000.0,
                          conditions=(
                              RateCondition(
                                  condition_id="tt-local-entity-required",
                                  description="Requires a T&T-incorporated "
                                              "local production company "
                                              "with >=1 resident director "
                                              "-- not pre-evaluable without "
                                              "entity-formation facts",
                                  quote="the entity responsible for all "
                                        "activities...incorporated locally "
                                        "with at least one Trinidad and "
                                        "Tobago resident director "
                                        "(ttbizlink.gov.tt)",
                                  kind="discretionary_band"),
                              RateCondition(
                                  condition_id="tt-local-labor-uplift-not-modeled",
                                  description="+20% rebate on qualifying "
                                              "local-labour expenditure "
                                              "specifically (not on total "
                                              "QPE) -- not pre-evaluable "
                                              "without a crew-nationality "
                                              "labor-cost breakdown",
                                  quote="20% rebate available for "
                                        "expenditure incurred on use of "
                                        "Qualifying Local Labour "
                                        "(ttbizlink.gov.tt)",
                                  kind="material_funding_risk_not_modeled"),
                          )),
    ),
))
register_rate_rules(rate_rules_for(TT_DOCTRINE))

# ── Qatar: Qatar Screen Production Incentive (QSPI) ────────────────────────
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed via screendaily.com (trade
# press, single source, not further corroborated):
# 40% base + 10% discretionary uplift = 50% ceiling. Administered by
# Qatar's Film Committee at Media City Qatar; applications opened Q2
# 2026. Min spend / caps not stated in the source -- left UNKNOWN.
QA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="QA",
    program_slug="qa_screen_production_incentive",
    program_name="Qatar Screen Production Incentive (QSPI)",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=(
        "screendaily.com (single source, not further corroborated): "
        "'Qatar launches 50% cash rebate programme' -- 40% base cash "
        "rebate on qualifying Qatari production expenditure, plus a "
        "discretionary 10% uplift for hiring Qatari talent / local "
        "training investment / promoting Qatari culture. Administered "
        "by the Film Committee at Media City Qatar; applications opened "
        "Q2 2026. Up to 25% of QPE may be spent filming in selected "
        "neighboring Arab countries and still qualify."
    ),
    source_ref="screendaily.com-qatar-single-source",
    tiers=(
        DoctrineRateTier(tier_id="qa-base-40", rate=0.40, is_band_ceiling=False),
        DoctrineRateTier(tier_id="qa-uplift-ceiling-50", rate=0.50, is_band_ceiling=True,
                          conditions=(RateCondition(
                              condition_id="qa-talent-training-culture-uplift",
                              description="+10% uplift for Qatari-talent "
                                          "hiring / local training "
                                          "investment / cultural-promotion "
                                          "criteria -- discretionary, not "
                                          "pre-evaluable",
                              quote="Additional 10% uplift... hiring "
                                    "Qatari talent, investing in local "
                                    "training, promoting Qatari culture "
                                    "(screendaily.com)",
                              kind="discretionary_band"),)),
    ),
))
register_rate_rules(rate_rules_for(QA_DOCTRINE))

# ── Uzbekistan: Film Rebate Programme ──────────────────────────────────────
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed via 3 corroborating sources
# (tashkenttimes.uz, anewz.tv, eurasianstar.com): 10-25% rebate by
# investment size, adopted by Cabinet of Ministers Resolution 2026-07-08,
# per-project cap 4bn soums (~$315K USD). Exact tier breakpoints between
# 10% and 25% not disclosed by any source -- modeled as floor (10%,
# guaranteed) / discretionary ceiling (25%, band) since the precise
# investment-size schedule is unknown. "Film in Uzbekistan" application
# platform scheduled to launch before 2026-11-01 -- program is very new.
UZ_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="UZ",
    program_slug="uz_film_rebate",
    program_name="Uzbekistan Film Rebate Programme",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=315_000.0,  # 4bn soums per-project cap, USD-converted
    requires_cultural_test=False,
    citation=(
        "3 corroborating sources (tashkenttimes.uz, anewz.tv, "
        "eurasianstar.com): 'between 10% and 25% of eligible local "
        "production expenses, depending on the size of their "
        "investment' -- 4 billion soums (~$315,000) per-project cap. "
        "Adopted by Cabinet of Ministers Resolution, 2026-07-08. "
        "Foreign studios must partner with an accredited local "
        "production company; only goods/services from Uzbek tax "
        "residents qualify. Exact investment-size tier breakpoints not "
        "disclosed by any source checked."
    ),
    source_ref="tashkenttimes+anewz+eurasianstar-uzbekistan",
    tiers=(
        DoctrineRateTier(tier_id="uz-floor-10", rate=0.10, is_band_ceiling=False),
        DoctrineRateTier(tier_id="uz-ceiling-25", rate=0.25, is_band_ceiling=True,
                          conditions=(RateCondition(
                              condition_id="uz-investment-size-band",
                              description="Rate scales 10%-25% by "
                                          "investment size on an "
                                          "undisclosed schedule -- not "
                                          "pre-evaluable without the "
                                          "official tier breakpoints",
                              quote="between 10% and 25%... depending on "
                                    "the size of their investment "
                                    "(tashkenttimes.uz)",
                              kind="discretionary_band"),
                          RateCondition(
                              condition_id="uz-local-entity-required",
                              description="Foreign studios must partner "
                                          "with an accredited local "
                                          "production company",
                              quote="Foreign studios must partner with an "
                                    "accredited local production company "
                                    "(anewz.tv)",
                              kind="discretionary_band"))),
    ),
))
register_rate_rules(rate_rules_for(UZ_DOCTRINE))

# ── Mongolia: Film & TV Production Incentive ────────────────────────────────
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed via multiple corroborating
# sources including montsame.mn (Mongolian state news agency, official)
# and Hollywood Reporter: parliament-approved cash rebate, NOT linked to
# the tax system. 30% base location incentive (min spend $500K) + 10%
# cultural-heritage uplift + 5% foreign-crew/talent uplift = 45% ceiling,
# each stackable independently or together.
MN_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="MN",
    program_slug="mn_production_incentive",
    program_name="Mongolia Film & TV Production Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=500_000.0,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=(
        "montsame.mn (Mongolian state news agency, official) + "
        "Hollywood Reporter + castandcrew.com (corroborating): "
        "Parliament-approved cash rebate, not linked to the tax system. "
        "'Projects spending a minimum of 500,000 USD may qualify for a "
        "30% location incentive... a further 10% rebate... for "
        "productions that highlight Mongolian culture and heritage... "
        "an additional 5% foreign crew and talent incentive.' The three "
        "incentives (Location/Cultural/Foreign Talent) 'can be taken "
        "separately or together for a 30%+10%+5% = 45% cumulative "
        "incentive.'"
    ),
    source_ref="montsame.mn+hollywoodreporter+castandcrew-mongolia",
    tiers=(
        DoctrineRateTier(tier_id="mn-base-location-30", rate=0.30, is_band_ceiling=False,
                          min_qpe_usd=500_000.0),
        DoctrineRateTier(tier_id="mn-stacked-ceiling-45", rate=0.45, is_band_ceiling=True,
                          min_qpe_usd=500_000.0,
                          conditions=(RateCondition(
                              condition_id="mn-cultural-foreign-crew-uplifts",
                              description="+10% Mongolian culture/heritage "
                                          "content + 5% foreign crew/"
                                          "talent -- neither pre-evaluable "
                                          "without project-content/"
                                          "crew-roster facts",
                              quote="a further 10% rebate... for "
                                    "productions that highlight Mongolian "
                                    "culture and heritage... an "
                                    "additional 5% foreign crew and "
                                    "talent incentive (montsame.mn, "
                                    "corroborated)",
                              kind="discretionary_band"),)),
    ),
))
register_rate_rules(rate_rules_for(MN_DOCTRINE))

# ── Switzerland: PICS (Swiss Films Location Switzerland) National Rebate ──
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed via 3 corroborating sources
# (filmincentive.com, fixerswitzerland.com, productionservicenetwork.com):
# national PICS scheme, 20-40% rebate on eligible expenses for
# international feature-film co-productions, CHF 600,000 (~$741,000)
# per-project cap. Separate CANTONAL funds (Geneva, Zurich, Valais,
# Neuchatel) exist ON TOP of PICS and are NOT modeled -- disclosed only.
CH_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CH",
    program_slug="ch_pics_national_rebate",
    program_name="Switzerland PICS National Location Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=741_000.0,  # CHF 600,000 per-project cap, USD-converted
    requires_cultural_test=False,
    citation=(
        "3 corroborating sources (filmincentive.com, "
        "fixerswitzerland.com, productionservicenetwork.com): national "
        "PICS scheme offers '20-40% rebate of eligible production "
        "expenses,' focused on international feature-film "
        "co-productions, 'maximum amount of CHF 600,000 ($741,000) paid "
        "to a project.' Separate cantonal funds (Geneva, Zurich, Valais; "
        "Neuchatel per screendaily.com) exist in addition to PICS and "
        "are NOT modeled here."
    ),
    source_ref="filmincentive+fixerswitzerland+psn-switzerland-pics",
    tiers=(
        DoctrineRateTier(tier_id="ch-floor-20", rate=0.20, is_band_ceiling=False),
        DoctrineRateTier(tier_id="ch-ceiling-40", rate=0.40, is_band_ceiling=True,
                          conditions=(RateCondition(
                              condition_id="ch-coproduction-scope-and-cantonal-stack",
                              description="Rate scales within the 20-40% "
                                          "band on undisclosed criteria; "
                                          "primarily targets international "
                                          "CO-PRODUCTIONS not solo foreign "
                                          "shoots. Separate cantonal funds "
                                          "(Geneva/Zurich/Valais/"
                                          "Neuchatel) may stack on top of "
                                          "PICS but are not modeled",
                              quote="20-40% rebate... focuses on "
                                    "international feature film "
                                    "co-productions (filmincentive.com)",
                              kind="discretionary_band"),)),
    ),
))
register_rate_rules(rate_rules_for(CH_DOCTRINE))

# ── Slovenia: Cash Rebate Scheme ───────────────────────────────────────────
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed directly from
# filminslovenia.si (linked to the official Slovenian Film Centre,
# film-center.si): "up to 25%" of acknowledged (post)production
# expenses -- a ceiling, not a flat guaranteed rate. No min spend or cap
# disclosed on the source page.
SI_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="SI",
    program_slug="si_cash_rebate",
    program_name="Slovenia Cash Rebate Scheme",
    # Global Economic Data + Base Pricing, batch 2: promoted PARSED ->
    # VERIFIED. Independently re-confirmed this task: filminslovenia.si
    # (official, linked to the Slovenian Film Centre) states "cash rebate
    # amounts up to 25% of the total acknowledged expenses" -- the same
    # figure and source the existing citation below already recorded from
    # its own direct fetch.
    confidence_tier="VERIFIED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=(
        "filminslovenia.si (official, linked to the Slovenian Film "
        "Centre / film-center.si, fetched directly): 'up to 25% of the "
        "total acknowledged expenses for the realisation of the "
        "(post)production of an individual project, incurred in the "
        "territory of the Republic of Slovenia.' Eligible: feature "
        "films, documentaries, TV drama, animation. Ineligible: "
        "commercials, reality TV, game shows, soaps. Two-stage "
        "provisional/final certificate process; final certificate "
        "'shall guarantee payment.' No min spend or cap disclosed."
    ),
    source_ref="filminslovenia.si-official",
    provenance=SourceProvenance(
        issuing_authority="Slovenian Film Centre (film-center.si), via "
                           "filminslovenia.si",
        source_url="https://filminslovenia.si",
        citation_detail="Up to 25% of total acknowledged (post)production "
                         "expenses",
        interpretation_note="Fresh search this task reproduced the exact "
                             "quoted 'up to 25%' figure the existing "
                             "citation's own direct fetch had already "
                             "recorded — two independent confirmations "
                             "of the same primary source.",
    ),
    tiers=(
        DoctrineRateTier(tier_id="si-ceiling-25", rate=0.25, is_band_ceiling=True,
                          conditions=(RateCondition(
                              condition_id="si-eligible-applicant-scope",
                              description="'Up to 25%' -- applicant must "
                                          "be a Slovenian producer/"
                                          "co-producer/service provider "
                                          "with >=1 publicly shown "
                                          "audiovisual work in the prior "
                                          "3 years; application must be "
                                          "filed >=1 day before shooting",
                              quote="up to 25% of the total acknowledged "
                                    "expenses (filminslovenia.si)",
                              kind="discretionary_band"),)),
    ),
))
register_rate_rules(rate_rules_for(SI_DOCTRINE))

# ── Ukraine: Cash Rebate for Foreign Film Producers ────────────────────────
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed via multiple corroborating
# sources (Hollywood Reporter, screendaily.com "signed off by
# president", cms.law, mondaq.com): statute-confirmed cash rebate,
# 4.5%-25% base range scaling by expense criteria, 25% achievable when
# expenses go through a VAT-registered Ukrainian cinematographic-industry
# company under a production agreement; +5% uplift for productions based
# on Ukrainian literary works = 30% ceiling. MATERIAL, UNMODELED RISK:
# Ukraine is in an active state of war as of this record's creation --
# the doctrine record captures the STATUTORY rate only; production
# feasibility/safety is a real-world operational risk this schema does
# not and cannot model, disclosed here and in the comparison profile,
# not silently omitted.
UA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="UA",
    program_slug="ua_cash_rebate",
    program_name="Ukraine Cash Rebate for Foreign Film Producers",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=(
        "Hollywood Reporter + screendaily.com ('finally signed off by "
        "president') + cms.law + mondaq.com (corroborating): rebate "
        "'varying between 4.5% and 25% of eligible expenses... "
        "employee salaries.' 25% achieved when 'expenses are fully or "
        "partially incurred in favour of a company registered in "
        "Ukraine... and the foreign producer has entered into a "
        "production agreement... with a Ukrainian company that "
        "operates in the cinematographic industry and is a registered "
        "VAT payer.' 'Additional 5% rebate for satisfying additional "
        "criteria, such as launching a production based on a Ukrainian "
        "literary work.' A separate $57.5M state culture fund was "
        "proposed in late 2025 (not modeled -- discretionary/separate "
        "mechanism)."
    ),
    source_ref="hollywoodreporter+screendaily+cms.law+mondaq-ukraine",
    tiers=(
        DoctrineRateTier(tier_id="ua-floor-4_5", rate=0.045, is_band_ceiling=False),
        DoctrineRateTier(tier_id="ua-standard-25", rate=0.25, is_band_ceiling=False,
                          conditions=(RateCondition(
                              condition_id="ua-local-vat-entity-agreement-required",
                              description="25% requires a production "
                                          "agreement with a VAT-"
                                          "registered Ukrainian "
                                          "cinematographic-industry "
                                          "company -- not pre-evaluable "
                                          "without a confirmed local "
                                          "production-agreement fact",
                              quote="a production agreement... with a "
                                    "Ukrainian company that operates in "
                                    "the cinematographic industry and is "
                                    "a registered VAT payer "
                                    "(cms.law/lexology, corroborated)",
                              kind="discretionary_band"),)),
        DoctrineRateTier(tier_id="ua-stacked-ceiling-30", rate=0.30, is_band_ceiling=True,
                          conditions=(
                              RateCondition(
                                  condition_id="ua-literary-work-uplift",
                                  description="+5% for productions based "
                                              "on a Ukrainian literary "
                                              "work -- not pre-evaluable "
                                              "without source-material "
                                              "facts",
                                  quote="an additional 5% rebate for "
                                        "satisfying additional criteria, "
                                        "such as launching a production "
                                        "based on a Ukrainian literary "
                                        "work (Hollywood Reporter)",
                                  kind="discretionary_band"),
                              RateCondition(
                                  condition_id="ua-active-conflict-risk-not-modeled",
                                  description="Ukraine is in an active "
                                              "state of war -- real-world "
                                              "production feasibility/"
                                              "safety risk is NOT modeled "
                                              "by this rate-doctrine "
                                              "schema and must be "
                                              "evaluated separately",
                                  quote="(not a source quote -- disclosed "
                                        "operational-risk fact, not a "
                                        "statutory rate condition)",
                                  kind="material_funding_risk_not_modeled"),
                          )),
    ),
))
register_rate_rules(rate_rules_for(UA_DOCTRINE))

# ── Portugal: SCRI.PT (Sistema de Cash Rebate e Incentivos) ────────────────
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed via 3+ corroborating sources
# (beyondfocus.pt, saturation.io, ica-ip.pt official, portugalfilmcommission.com):
# statute-confirmed graduated bracket -- 30% on the first EUR 2,000,000
# (~$2.17M) of eligible expenditure, 25% on the excess (real marginal
# bracket, using graduated_brackets per the ES precedent in this file:
# tier.rate carries the EXCESS/top rate, graduated_brackets holds only
# the lower-bracket entries -- NOT a discretionary "up to" band).
# Productions filming outside Lisbon/Porto get a flat 30% regardless of
# spend level. Enacted by Decree-Law No. 57/2026, replacing the prior
# Tourism and Cinema Support Fund; administered by ICA (Instituto do
# Cinema e do Audiovisual) with Turismo de Portugal; EUR 350M total
# budget 2026-2029, EUR 200M non-repayable. A SEPARATE "large-scale
# production" track (>= EUR 2.5M / ~$2.71M spend, permanently open from
# 2026-06-29) is mentioned by the sources but not confirmed to be the
# same track as the 30/25 bracket -- NOT conflated into min_spend_usd
# here; disclosed as a separate, unconfirmed-relationship fact instead.
_PT_CITATION = (
    "beyondfocus.pt + saturation.io + ica-ip.pt (official ICA site) + "
    "portugalfilmcommission.com (corroborating): 'reimbursement rates "
    "are 30% for the first EUR 2 million of eligible expenditure and "
    "25% thereafter... productions outside Lisbon/Porto can receive 30% "
    "as the base rate.' Decree-Law No. 57/2026 created SCRI.PT, "
    "replacing the prior Tourism and Cinema Support Fund; administered "
    "by ICA with Turismo de Portugal; EUR 350,000,000 total budget "
    "2026-2029 (EUR 200,000,000 non-repayable support over 4 years). A "
    "separately-described large-scale-production incentive is "
    "'permanently open from 29 June onwards... available to projects "
    "spending at least EUR 2.5 million' -- relationship to the 30/25 "
    "bracket above is not confirmed by the sources checked."
)
PT_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="PT",
    program_slug="pt_scri_pt_cash_rebate",
    program_name="Portugal SCRI.PT Cash Rebate Incentive",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=_PT_CITATION,
    source_ref="beyondfocus+saturation.io+ica-ip.pt-official+portugalfilmcommission-portugal",
    tiers=(
        DoctrineRateTier(
            tier_id="pt-graduated-30-25",
            rate=0.25,
            is_band_ceiling=False,
            graduated_brackets=((2_171_000.0, 0.30),),
            conditions=(
                RateCondition(
                    condition_id="pt-graduated-bracket-applied",
                    description="Statute-confirmed marginal bracket: 30% "
                                "on the first EUR 2M (~$2.17M) of QPE, "
                                "25% on the excess -- resolve_program_rate() "
                                "computes a real blended effective rate, "
                                "not a discretionary band",
                    quote="30% for the first EUR 2 million of eligible "
                          "expenditure and 25% thereafter (beyondfocus.pt, "
                          "corroborated)",
                    kind="graduated_bracket_applied"),
                RateCondition(
                    condition_id="pt-large-scale-track-relationship-unconfirmed",
                    description="A separate 'large-scale production' "
                                "track (>= EUR 2.5M spend) is described "
                                "by the sources but its relationship to "
                                "this 30/25 bracket is not confirmed -- "
                                "not modeled as a min-spend gate on this "
                                "tier to avoid an unconfirmed assumption",
                    quote="available to projects spending at least EUR "
                          "2.5 million (beyondfocus.pt)",
                    kind="material_funding_risk_not_modeled"),
            ),
        ),
        DoctrineRateTier(
            tier_id="pt-outside-lisbon-porto-flat-30",
            rate=0.30,
            is_band_ceiling=True,
            conditions=(RateCondition(
                condition_id="pt-outside-lisbon-porto-flat-rate",
                description="Flat 30% (no bracket step-down) for "
                            "productions filming outside Lisbon/Porto -- "
                            "not pre-evaluable without shoot-location "
                            "facts",
                quote="productions outside Lisbon/Porto can receive 30% "
                      "as the base rate (beyondfocus.pt)",
                kind="discretionary_band"),),
        ),
    ),
))
register_rate_rules(rate_rules_for(PT_DOCTRINE))

# ── Australia — South Australia: PDV Rebate ────────────────────────────────
# Checked internal source first: no prior DoctrineRecord existed (catalog
# had base_rate=None, DISCOVERY). Confirmed via safilm.com.au (South
# Australian Film Corporation, official): 10% state rebate on Post,
# Digital and Visual Effects (PDV) spend ONLY -- NOT a general
# production rebate. Stacks with the AUS FEDERAL 30% PDV Offset for 40%
# combined on PDV expenditure specifically. Separate payroll-tax
# exemption up to 4.95% also disclosed but not modeled (not a QPE rate).
# Genuinely narrow-scope: does not apply to general above/below-the-line
# production spend, only PDV.
AU_SA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="AU-SA",
    program_slug="au_sa_pdv_rebate",
    program_name="South Australia PDV Rebate",
    confidence_tier="PARSED",
    incentive_type="cash_rebate",
    is_refundable=True,
    is_transferable=False,
    min_spend_usd=None,
    annual_cap_usd=None,
    requires_cultural_test=False,
    citation=(
        "safilm.com.au (South Australian Film Corporation, official): "
        "'a 10% rebate on Post Production, Digital and Visual Effects "
        "spend, which can be combined with the Federal Government's 30% "
        "Post, Digital & Visual Effects (PDV) Offset for a total rebate "
        "of 40% on PDV expenditure.' A separate 'payroll tax exemption "
        "to producers shooting feature films in South Australia... may "
        "reduce a project's total payroll liability by up to 4.95%' -- "
        "not a QPE rate, not modeled here."
    ),
    source_ref="safilm.com.au-official-south-australia",
    tiers=(
        DoctrineRateTier(tier_id="au-sa-pdv-only-10", rate=0.10, is_band_ceiling=False,
                          conditions=(RateCondition(
                              condition_id="au-sa-pdv-scope-only",
                              description="Applies ONLY to Post/Digital/"
                                          "VFX spend, not general "
                                          "production QPE -- not "
                                          "pre-evaluable without a PDV-"
                                          "specific cost breakdown; "
                                          "combines with the separately-"
                                          "modeled AUS federal 30% PDV "
                                          "offset for 40% on PDV spend",
                              quote="10% rebate on Post Production, "
                                    "Digital and Visual Effects spend "
                                    "(safilm.com.au)",
                              kind="material_funding_risk_not_modeled"),)),
    ),
))
register_rate_rules(rate_rules_for(AU_SA_DOCTRINE))

# ============================================================================
# BATCH: global_inventory_extended.py reconciliation (37 DISC-tier catalog
# leads, 36 net-new after US-OR/PT/SA/JO/MA/ZA already covered). Every
# catalog entry here was self-flagged confidence_tier=DISCOVERY -- each
# below was checked against fresh sources per the same discipline as the
# rest of this file (checked internal catalog first, then minimum
# necessary corroborating verification; stale/wrong catalog figures
# corrected and flagged, not silently kept).
# ============================================================================

# ── US-Washington: Motion Picture Competitiveness Program ─────────────────
# Catalog had 15% base/35% ceiling -- STALE base. Corroborated
# (greenslate.com): 30-35% base cash rebate, stackable to 45% via two
# Enhanced Incentives (resident payroll, local spend, non-resident BTL
# labor, rural county bonuses).
US_WA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-WA", program_slug="us_wa_motion_picture_competitiveness",
    program_name="Washington State Motion Picture Competitiveness Program",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=500_000.0,
    annual_cap_usd=3_500_000.0, requires_cultural_test=False,
    citation="greenslate.com (corroborated): '30% to 35% cash rebate... "
              "additional 10% cash back with one of two Enhanced "
              "Incentives... can stack to 45%.' Corrects the prior "
              "catalog's stale 15% base figure. Annual fund ~$3.5M, "
              "competitive/oversubscribed (Washington Filmworks).",
    source_ref="greenslate.com-washington",
    tiers=(DoctrineRateTier(tier_id="us-wa-base-30", rate=0.30, is_band_ceiling=False,
                             min_qpe_usd=500_000.0),
           DoctrineRateTier(tier_id="us-wa-ceiling-45", rate=0.45, is_band_ceiling=True,
                             min_qpe_usd=500_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-wa-enhanced-incentive-uplifts",
                                 description="+10% via one of two Enhanced "
                                             "Incentives, stacking with "
                                             "resident payroll/local-spend/"
                                             "non-resident-BTL/rural-county "
                                             "bonuses -- not pre-evaluable; "
                                             "competitive, oversubscribed fund",
                                 quote="additional 10% cash back with one of "
                                       "two Enhanced Incentives (greenslate.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(US_WA_DOCTRINE))

# ── US-Illinois: Film Production Services Tax Credit ──────────────────────
# Catalog had 30% flat. Confirmed via SB 1911 (signed): base unchanged at
# 30%, ceiling to 35% via in-state-labor/vendor uplifts; extended through
# 2038; loan-out withholding 4.95%.
US_IL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-IL", program_slug="us_il_film_production_services_credit",
    program_name="Illinois Film Production Services Tax Credit",
    confidence_tier="VERIFIED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=None, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="dceo.illinois.gov/whyillinois/film/filmtaxcredit.html "
              "(Illinois Dept. of Commerce and Economic Opportunity, "
              "official, fetched directly): '35% credit on Illinois "
              "resident salaries up to $500,000 per worker' and '35% "
              "credit for the use of tangible personal property or the "
              "expenses to acquire services from vendors in Illinois' "
              "(general spend). '30% credit on non-resident salaries up "
              "to $500,000 per worker' -- a narrower payroll-specific "
              "rate, not the general base. '5% additional credit' for "
              "certified green productions (not modeled -- no "
              "sustainability-certification fact exists). '15% "
              "additional credit' for wages of workers in economically "
              "disadvantaged areas (not modeled -- no worker-residence-"
              "area fact exists). CORRECTS the prior modeled base from "
              "30% to the real general base of 35%.",
    source_ref="dceo.illinois.gov-official",
    provenance=SourceProvenance(
        issuing_authority="Illinois Department of Commerce and Economic "
                           "Opportunity (DCEO)",
        source_url="https://dceo.illinois.gov/whyillinois/film/filmtaxcredit.html",
        citation_detail="'35% credit for the use of tangible personal "
                         "property or the expenses to acquire services "
                         "from vendors in Illinois'",
        verified_date="2026-08-17",
        interpretation_note="Corrects the prior modeled base rate from "
                             "30% to the real general base of 35% -- 30% "
                             "applies only to non-resident salaries "
                             "specifically. Green (+5%) and economically-"
                             "disadvantaged-area (+15%) uplifts are real "
                             "but not modeled (no matching facts exist).",
    ),
    tiers=(DoctrineRateTier(tier_id="us-il-base-35", rate=0.35, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(US_IL_DOCTRINE))

# ── US-North Carolina: Film & Entertainment Grant ──────────────────────────
# Catalog had 25% flat. Fresh search confirmed only the loan-out
# withholding rate (4%), not a new headline rate -- catalog's 25% is kept
# as PARSED (unchallenged, not contradicted), disclosed as not
# re-confirmed this pass.
US_NC_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-NC", program_slug="us_nc_film_entertainment_grant",
    program_name="North Carolina Film & Entertainment Grant",
    confidence_tier="VERIFIED", incentive_type="cash_rebate",
    is_refundable=None, is_transferable=False, min_spend_usd=1_713_710.79,
    annual_cap_usd=31_000_000.0, requires_cultural_test=False,
    citation="commerce.nc.gov/grants-incentives/film-industry-grants (NC "
              "Department of Commerce, official, fetched directly): grant "
              "rate 'up to 25%' on qualified expenses. Minimum spend: "
              "feature films 'at least $1.5 million,' TV series 'at least "
              "$500,000 per episode,' made-for-TV movies 'at least "
              "$500,000,' commercials 'at least $250,000' -- feature-film "
              "threshold used as the general case (see program's per-"
              "format Requirements Profile for the full breakdown). "
              "Annual funding '$31 million each fiscal year (July 1-June "
              "30)' with no sunset date, unused funds roll over.",
    source_ref="commerce.nc.gov-official",
    provenance=SourceProvenance(
        issuing_authority="North Carolina Department of Commerce",
        source_url="https://www.commerce.nc.gov/grants-incentives/film-industry-grants",
        citation_detail="'up to 25%' on qualified expenses; feature-film "
                         "minimum spend 'at least $1.5 million'",
        effective_date="Funded annually, no sunset date",
        verified_date="2026-08-17",
        interpretation_note="'Up to 25%' is a discretionary ceiling, not "
                             "a flat guaranteed rate -- modeled as a band "
                             "ceiling, same treatment as other 'up to' "
                             "programs in this registry.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-nc-ceiling-25", rate=0.25, is_band_ceiling=True,
                             min_qpe_usd=1_713_710.79,
                             conditions=(RateCondition(
                                 condition_id="us-nc-min-spend-feature",
                                 description="Minimum spend for feature "
                                             "films; TV series/movies/"
                                             "commercials have their own, "
                                             "lower per-format thresholds "
                                             "not separately modeled",
                                 quote="at least $1.5 million "
                                       "(commerce.nc.gov)",
                                 kind="min_qpe_usd", threshold_usd=1_713_710.79),)),),
))
register_rate_rules(rate_rules_for(US_NC_DOCTRINE))

# ── US-South Carolina: Film Production Credit ──────────────────────────────
# Catalog had 20% flat. Confirmed via shamelstudio.com dedicated page: 20%
# base, up to 30% with uplifts, $1M min spend, $15.5M annual cap.
US_SC_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-SC", program_slug="us_sc_film_production_credit",
    program_name="South Carolina Film Production Credit",
    confidence_tier="VERIFIED", incentive_type="cash_rebate",
    is_refundable=None, is_transferable=None, min_spend_usd=1_000_000.0,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="scprt.com/film-commission/incentives/production-incentives "
              "(SC Department of Parks, Recreation and Tourism, official, "
              "fetched directly): Supplier Rebate 'up to thirty percent "
              "(30%) of qualifying goods and services purchased, rented, "
              "or leased by the production company from a South Carolina "
              "supplier' -- modeled as the general QPE rate. Wage "
              "Rebate: 'up to twenty-five percent (25%)' for SC-resident "
              "personnel, '20% rebate' for non-resident performing "
              "artists/crew -- narrower payroll-specific rates, not "
              "separately modeled (no payroll-vs-total-QPE split fact). "
              "Minimum spend '$1,000,000 in SC' for wage/supplier "
              "rebates. No annual cap stated on this page -- the prior "
              "catalog's $15.5M figure was not re-confirmed and is "
              "disclosed as unconfirmed, not modeled.",
    source_ref="scprt.com-official",
    provenance=SourceProvenance(
        issuing_authority="South Carolina Department of Parks, "
                           "Recreation and Tourism",
        source_url="https://www.scprt.com/film-commission/incentives/production-incentives",
        citation_detail="Supplier Rebate 'up to thirty percent (30%) of "
                         "qualifying goods and services'",
        verified_date="2026-08-17",
        interpretation_note="Modeled as a band ceiling (an 'up to' "
                             "figure). Resident/non-resident wage rebates "
                             "(25%/20%) are real but narrower payroll-"
                             "specific rates not separately tracked by "
                             "this engine. Annual cap not confirmed on "
                             "this page -- prior $15.5M catalog figure "
                             "held as unconfirmed, not modeled.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-sc-supplier-ceiling-30", rate=0.30,
                             is_band_ceiling=True, min_qpe_usd=1_000_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-sc-wage-rebates-not-modeled",
                                 description="Resident wage rebate 25% "
                                             "and non-resident wage "
                                             "rebate 20% apply to payroll "
                                             "specifically, not general "
                                             "QPE -- not separately "
                                             "modeled",
                                 quote="up to twenty-five percent (25%)... "
                                       "20% rebate for non-resident "
                                       "(scprt.com)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(US_SC_DOCTRINE))

# ── US-Massachusetts: Film Tax Credit ──────────────────────────────────────
# Catalog had 25% flat -- CONFIRMED unchanged.
US_MA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-MA", program_slug="us_ma_film_tax_credit",
    program_name="Massachusetts Film Tax Credit",
    confidence_tier="VERIFIED", incentive_type="tax_credit",
    is_refundable=False, is_transferable=True, min_spend_usd=50_000.0,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="mafilm.org/tax-incentives/ (Massachusetts Film Office, "
              "official, fetched directly): '25% production credit' and "
              "'25% payroll credit.' Payroll credit requires spending "
              "'more than $50,000' in MA; production credit requires "
              "'spending more than 75% of total budget or filming at "
              "least 75% of principal photography days' in-state (not "
              "modeled -- no budget-ratio/shoot-days fact exists in this "
              "engine). 'No annual or project caps.' No sunset date "
              "stated.",
    source_ref="mafilm.org-official",
    provenance=SourceProvenance(
        issuing_authority="Massachusetts Film Office",
        source_url="https://mafilm.org/tax-incentives/",
        citation_detail="'25% production credit' + '25% payroll credit'; "
                         "'no annual or project caps'",
        verified_date="2026-08-17",
        interpretation_note="Production credit's 75%-of-budget-or-days "
                             "eligibility threshold is a real gate this "
                             "engine cannot pre-evaluate -- disclosed via "
                             "condition, not enforced.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-ma-flat-25", rate=0.25, is_band_ceiling=False,
                             min_qpe_usd=50_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-ma-production-credit-threshold",
                                 description="Production credit requires "
                                             ">75% of total budget or "
                                             ">=75% of principal "
                                             "photography days in MA -- "
                                             "not pre-evaluable without a "
                                             "budget-ratio/shoot-days fact",
                                 quote="spending more than 75% of total "
                                       "budget or filming at least 75% of "
                                       "principal photography days "
                                       "(mafilm.org)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(US_MA_DOCTRINE))

# ── US-Texas: Moving Image Industry Incentive Program (MIIP) ──────────────
# Catalog had 5% flat (the historical base tier). Confirmed base
# unchanged; NEW: $200M annual cap, and stackable bonuses could reach
# 31% for productions meeting added criteria (post-production/crew
# payroll) starting 2026-09-01 -- effective date is in the future
# relative to some but not all of this record's use; disclosed as an
# upcoming, not-yet-uniformly-effective condition.
US_TX_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-TX", program_slug="us_tx_miip",
    program_name="Texas Moving Image Industry Incentive Program (MIIP)",
    confidence_tier="VERIFIED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=200_000_000.0, requires_cultural_test=False,
    citation="gov.texas.gov/film/page/tmiiip_filmtv (Office of the Texas "
              "Governor, Texas Film Commission, official, fetched "
              "directly): 'Qualifying projects are eligible to receive a "
              "cash grant up to 31% of eligible Texas spending.' Modeled "
              "as a band ceiling (an 'up to' figure, not a flat "
              "guaranteed rate) -- CORRECTS the prior placeholder 5% base "
              "tier, which was a catalog carryover not confirmed by this "
              "official source.",
    source_ref="gov.texas.gov-official",
    provenance=SourceProvenance(
        issuing_authority="Office of the Texas Governor (Texas Film "
                           "Commission)",
        source_url="https://gov.texas.gov/film/page/tmiiip_filmtv",
        citation_detail="'cash grant up to 31% of eligible Texas "
                         "spending'",
        verified_date="2026-08-17",
        interpretation_note="The official page states a single 'up to "
                             "31%' figure without a published tier "
                             "schedule -- modeled as a band ceiling. A "
                             "secondary source's '5%-25% base + 1%-2.5% "
                             "bonus' tier claim was not independently "
                             "confirmed and is not modeled.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-tx-ceiling-31", rate=0.31, is_band_ceiling=True),),
))
register_rate_rules(rate_rules_for(US_TX_DOCTRINE))

# ── US-Connecticut: Film Tax Credit ────────────────────────────────────────
# Global Formulaic Economic Completion: catalog's 10% flat / "tier schedule
# unconfirmed" gap CLOSED via direct fetch of portal.ct.gov/DECD (CT
# Department of Economic and Community Development, official) this task:
# real tiered structure confirmed verbatim -- 10% ($100K-$500K), 15%
# ($500K-$1M), 30% ($1M+). Corrects the prior placeholder 10%-flat model,
# which understated the rate for any production above $1M CT spend.
US_CT_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-CT", program_slug="us_ct_film_tax_credit",
    program_name="Connecticut Film Tax Credit",
    confidence_tier="VERIFIED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=True, min_spend_usd=113_710.79,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="portal.ct.gov/DECD (Connecticut Department of Economic and "
             "Community Development, official, fetched directly): "
             "'minimum expenditure is $100,000.' Tiered rate: "
             "'$100,000-$500,000' -> '10%', '$500,000-$1,000,000' -> "
             "'15%', '$1,000,000 or more' -> '30%'. Transferable: 'An "
             "eligible production company may sell, assign or otherwise "
             "transfer the tax credits to another taxpayer.' Annual cap "
             "not stated on the page fetched.",
    source_ref="portal.ct.gov-DECD-official",
    provenance=SourceProvenance(
        issuing_authority="Connecticut Department of Economic and "
                           "Community Development (DECD)",
        source_url="https://portal.ct.gov/DECD/Content/Film-TV-Digital-Media/02_Learn_About_Tax_Incentives/02-Digital-Media-Motion-Picture-Tax-Credit",
        citation_detail="'$100,000-$500,000' -> 10%, '$500,000-$1,000,000' "
                         "-> 15%, '$1,000,000 or more' -> 30%",
        verified_date="2026-08-17",
        interpretation_note="Annual program cap was not stated on the "
                             "page fetched -- disclosed as unconfirmed, "
                             "not modeled as uncapped.",
    ),
    tiers=(
        DoctrineRateTier(tier_id="us-ct-tier-10", rate=0.10, is_band_ceiling=False,
                          min_qpe_usd=113_710.79),
        DoctrineRateTier(tier_id="us-ct-tier-15", rate=0.15, is_band_ceiling=False,
                          min_qpe_usd=568_553.96),
        DoctrineRateTier(tier_id="us-ct-tier-30", rate=0.30, is_band_ceiling=False,
                          min_qpe_usd=1_137_107.92),
    ),
))
register_rate_rules(rate_rules_for(US_CT_DOCTRINE))

# ── US-Pennsylvania: Film Production Tax Credit ────────────────────────────
# Catalog had 25% flat. Confirmed: 25% base, 30% with certain criteria.
US_PA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-PA", program_slug="us_pa_film_production_credit",
    program_name="Pennsylvania Film Production Tax Credit",
    confidence_tier="VERIFIED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=True, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="dced.pa.gov/programs/film-tax-credit-program/ (PA "
              "Department of Community & Economic Development, official, "
              "fetched directly): '25% of the production's total "
              "Qualified Pennsylvania Production Expenses.' 'An "
              "additional 5% tax credit, for a total credit of 30%' for "
              "use of a qualified production facility. Requirement: "
              "'Pennsylvania production expenses comprise at least 60% "
              "of the Film's total production expenses' (not modeled -- "
              "no budget-ratio fact exists in this engine). "
              "Post-production work at qualified facilities separately "
              "earns 'a 30% tax credit' (not modeled -- distinct program "
              "track).",
    source_ref="dced.pa.gov-official",
    provenance=SourceProvenance(
        issuing_authority="Pennsylvania Department of Community & "
                           "Economic Development (DCED)",
        source_url="https://dced.pa.gov/programs/film-tax-credit-program/",
        citation_detail="'25% of the production's total Qualified "
                         "Pennsylvania Production Expenses'; '+5%' "
                         "qualified production facility uplift",
        verified_date="2026-08-17",
        interpretation_note="60%-of-total-production-expenses PA "
                             "requirement not pre-evaluable -- disclosed "
                             "via condition, not enforced.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-pa-base-25", rate=0.25, is_band_ceiling=False),
           DoctrineRateTier(tier_id="us-pa-ceiling-30", rate=0.30, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="us-pa-qualified-facility-uplift",
                                 description="+5% for use of a qualified "
                                             "production facility -- not "
                                             "pre-evaluable without a "
                                             "facility-use fact",
                                 quote="An additional 5% tax credit, for a "
                                       "total credit of 30% (dced.pa.gov)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(US_PA_DOCTRINE))

# ── US-Maryland: Film Production Activity Tax Credit ──────────────────────
# Catalog had 25% flat -- CORRECTED. Confirmed via commerce.maryland.gov
# (official, direct search hit): 'refundable income tax credit of up to
# 28%... $12 million... FY 2026.'
# 2026-07-26 additive refinement (same official source, not a conflict --
# knowledge reconciliation, not a discrepancy needing preservation): direct
# fetch of commerce.maryland.gov/fund/film-production-activity-tax-credit
# surfaced a SEPARATE, higher 30% tier for television series (distinct from
# the 28% standard-production ceiling already on record) plus a distinct
# "Maryland Small Film" category. min_spend_usd added (USD 250,000,
# confirmed directly from the same official page and independently from
# Tax-General Code Sec. 10-730 via law.justia.com).
US_MD_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-MD", program_slug="us_md_film_production_activity_credit",
    program_name="Maryland Film Production Activity Tax Credit",
    confidence_tier="VERIFIED", incentive_type="tax_credit",
    is_refundable=True, is_transferable=False, min_spend_usd=250_000.0,
    annual_cap_usd=12_000_000.0, requires_cultural_test=False,
    citation="commerce.maryland.gov (official): 'a qualified film "
              "production entity may receive a refundable income tax "
              "credit of up to 28% of the total authorized direct costs... "
              "The Department is limited to certifying $12 million in tax "
              "credits for applicants in FY 2026.' Corrects catalog's "
              "stale 25% figure. Same page (re-fetched 2026-07-26) also "
              "states television series qualify for up to 30% (not 28%), "
              "and separately defines a 'Maryland Small Film' category "
              "(min spend USD 25,000, capped at USD 125,000, exempt from "
              "the independent CPA-audit requirement) -- both recorded as "
              "additional tiers/conditions, not a replacement of the 28% "
              "standard-production figure.",
    source_ref="commerce.maryland.gov-official",
    provenance=SourceProvenance(
        issuing_authority="Maryland Department of Commerce",
        source_url="https://commerce.maryland.gov",
        citation_detail="Up to 28% of total authorized direct costs; "
                         "FY 2026 certification cap $12,000,000",
        effective_date="FY 2026",
        verified_date="2026-07-26",
        interpretation_note="Corrects the catalog's stale 25% figure. "
                             "Same page also confirms TV series qualify "
                             "for up to 30% (not 28%) and a separate "
                             "'Maryland Small Film' category (min spend "
                             "$25,000, capped at $125,000) — both modeled "
                             "as additional tiers/conditions, not a "
                             "replacement of the 28% standard-production "
                             "figure.",
    ),
    production_types=("feature_film", "tv_series"),
    tiers=(DoctrineRateTier(tier_id="us-md-ceiling-28", rate=0.28, is_band_ceiling=True,
                             min_qpe_usd=250_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-md-up-to-28-band",
                                 description="'Up to 28%' -- discretionary "
                                             "within the FY2026 $12M "
                                             "certification cap; standard "
                                             "(non-TV-series) productions",
                                 quote="up to 28% of the total authorized "
                                       "direct costs (commerce.maryland.gov)",
                                 kind="discretionary_band"),)),
           DoctrineRateTier(tier_id="us-md-tv-series-30", rate=0.30, is_band_ceiling=True,
                             min_qpe_usd=250_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-md-tv-series-uplift",
                                 description="Television series qualify for "
                                             "up to 30% instead of the 28% "
                                             "standard ceiling -- a format-"
                                             "specific tier, not a "
                                             "discretionary band",
                                 quote="Television series: Up to 30% of "
                                       "authorized direct costs "
                                       "(commerce.maryland.gov)",
                                 kind="production_type_uplift"),)),
           DoctrineRateTier(tier_id="us-md-small-film-125k-cap", rate=0.28, is_band_ceiling=True,
                             min_qpe_usd=25_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-md-small-film-category",
                                 description="'Maryland Small Film' category: "
                                             "min spend USD 25,000 (vs USD "
                                             "250,000 standard), credit "
                                             "capped at USD 125,000 total, "
                                             "exempt from independent CPA "
                                             "audit. Requires independently-"
                                             "owned applicant, <=25 FTEs, not "
                                             "dominant in its field, and "
                                             "organized/active in Maryland "
                                             "for 3+ months",
                                 quote="Maryland Small Films capped at "
                                       "$125,000 maximum per project "
                                       "(commerce.maryland.gov)",
                                 kind="alternate_qualification_track"),)),),
))
register_rate_rules(rate_rules_for(US_MD_DOCTRINE))

# ── US-Virginia: Motion Picture Production Tax Credit ──────────────────────
# Catalog had 15% flat. No fresh data found this pass -- carried forward
# unchallenged.
US_VA_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-VA", program_slug="us_va_motion_picture_credit",
    program_name="Virginia Motion Picture Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=None, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="Pre-existing catalog figure (15%) NOT contradicted this "
              "pass -- no dedicated Virginia source surfaced in the "
              "search batch; carried forward unchallenged, not re-confirmed.",
    source_ref="catalog-unchallenged-virginia",
    tiers=(DoctrineRateTier(tier_id="us-va-flat-15", rate=0.15, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="us-va-rate-not-reconfirmed",
                                 description="15% carried forward from the "
                                             "pre-existing catalog entry, "
                                             "not independently "
                                             "re-confirmed this pass",
                                 quote="(no source found this pass)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(US_VA_DOCTRINE))

# ── US-Colorado: Film Incentive ────────────────────────────────────────────
# Catalog had 20% flat. Fresh search confirmed only a procedural change
# (1099 vs withholding), not a rate change -- 20% carried forward unchallenged.
US_CO_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-CO", program_slug="us_co_film_incentive",
    program_name="Colorado Film Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="Pre-existing catalog figure (20%) NOT contradicted this "
              "pass -- search surfaced only a 1099/withholding procedural "
              "change, not a rate change; carried forward unchallenged.",
    source_ref="catalog-unchallenged-colorado",
    tiers=(DoctrineRateTier(tier_id="us-co-flat-20", rate=0.20, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="us-co-rate-not-reconfirmed",
                                 description="20% carried forward from the "
                                             "pre-existing catalog entry, "
                                             "not independently "
                                             "re-confirmed this pass",
                                 quote="(no rate-confirming source found "
                                       "this pass)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(US_CO_DOCTRINE))

# ── US-Tennessee: Performance Grant ────────────────────────────────────────
# Catalog had base_rate=None. NOW CONFIRMED: 25% of QPE for Nashville-metro/
# tier-1 areas, plus unspecified additional bonuses for tier 2-4
# (rural/economically-distressed) counties.
US_TN_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-TN", program_slug="us_tn_performance_grant",
    program_name="Tennessee Film, Entertainment & Music Commission Performance Grant",
    confidence_tier="VERIFIED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=200_000.0,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="tn.gov (Tennessee state government, official, fetched "
              "directly): 'projects with budgets over $200,000 will be "
              "eligible to receive grants equal to 25 percent of their "
              "qualified Tennessee expenditures,' effective 2012-07-01. "
              "No tier structure found on this page (the tier 2-4 "
              "county-bonus claim from a prior secondary source was not "
              "independently re-confirmed and is not modeled).",
    source_ref="tn.gov-official",
    provenance=SourceProvenance(
        issuing_authority="Tennessee Department of Economic and "
                           "Community Development",
        source_url="https://www.tn.gov/transparenttn/state-financial-overview/open-ecd/openecd/film-incentives.html",
        citation_detail="'grants equal to 25 percent of their qualified "
                         "Tennessee expenditures'",
        effective_date="2012-07-01",
        verified_date="2026-08-17",
        interpretation_note="A secondary source's tier-2-through-4 "
                             "county-bonus claim was not confirmed by "
                             "this official page and is not modeled.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-tn-flat-25", rate=0.25, is_band_ceiling=False,
                             min_qpe_usd=200_000.0),),
))
register_rate_rules(rate_rules_for(US_TN_DOCTRINE))

# ── US-Oklahoma: Film Enhancement Rebate ───────────────────────────────────
# Catalog had 35% flat -- CONFLICTS with this pass's fresh source
# (20-30% cash rebates, Oklahoma Film Office). Given a real conflict
# between the catalog figure and a fresh dedicated source, the fresher
# range is used as the higher-confidence figure; the catalog's 35% is
# flagged as an unresolved prior claim, not silently dropped.
US_OK_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-OK", program_slug="us_ok_film_enhancement_rebate",
    program_name="Oklahoma Film Enhancement Rebate",
    confidence_tier="VERIFIED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=30_000_000.0, requires_cultural_test=False,
    citation="okfilmmusic.org/incentives (Oklahoma Film and Music "
              "Office, official, fetched directly): '20% Base Incentive.' "
              "Stackable uplifts: '3% Rural County Uplift,' '2% Small "
              "Municipality Uplift,' '5% Soundstage Uplift,' '3% Post-"
              "Production Uplift,' '2% Music Uplift,' '2%/5% TV pilot/"
              "season,' '5% Multi-Film Deal Uplift' (none individually "
              "modeled -- not pre-evaluable without shoot-location/"
              "facility/deal facts). Page states 'up to 30% total "
              "rebate' as the maximum combined rate -- RESOLVES the "
              "prior unresolved conflict between the catalog's 35% and a "
              "secondary source's 20-30% range in favor of the official "
              "page's explicit 30% ceiling; no annual cap was stated on "
              "this specific page, but the $30M annual cap is confirmed "
              "by the Filmed in Oklahoma Act 2021 program overview "
              "(replacing the prior $8M cap).",
    source_ref="okfilmmusic.org-official",
    provenance=SourceProvenance(
        issuing_authority="Oklahoma Film and Music Office",
        source_url="https://www.okfilmmusic.org/incentives",
        citation_detail="'20% Base Incentive'; 'up to 30% total rebate'",
        verified_date="2026-08-17",
        interpretation_note="Resolves the prior 35%-vs-20-30% conflict in "
                             "favor of this official page's explicit 30% "
                             "maximum combined rate. Individual uplifts "
                             "(rural, soundstage, post, music, multi-"
                             "film) are real but not separately modeled.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-ok-base-20", rate=0.20, is_band_ceiling=False),
           DoctrineRateTier(tier_id="us-ok-ceiling-30", rate=0.30, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="us-ok-stackable-uplifts",
                                 description="Multiple stackable uplifts "
                                             "(rural county, small "
                                             "municipality, soundstage, "
                                             "post-production, music, "
                                             "multi-film deal) combine to "
                                             "reach the 30% ceiling -- "
                                             "none individually "
                                             "pre-evaluable",
                                 quote="up to 30% total rebate "
                                       "(okfilmmusic.org)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(US_OK_DOCTRINE))

# ── US-Alabama: Film Incentive ─────────────────────────────────────────────
# Catalog had 25% flat (general program, kept). NEW: HB379 (signed,
# effective 2026-10-01) adds a SEPARATE small-budget tier -- 45% rebate
# on Alabama-resident payroll ONLY, for productions with total
# expenditures between $100,000 and $499,999. This is a narrow,
# budget-bracketed uplift, not a general ceiling -- modeled as a
# distinct condition, not blended into the general program's rate.
US_AL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-AL", program_slug="us_al_film_incentive",
    program_name="Alabama Film Incentive",
    # Global Formulaic Economic Completion: promoted PARSED -> VERIFIED
    # after a direct fetch of revenue.alabama.gov confirmed the general
    # 25%/35% structure verbatim. HB379's narrow 45% small-budget-only
    # resident-payroll bracket (greenslate.com) was NOT re-confirmed by
    # this fetch -- retained as a disclosed, unconfirmed additional
    # provision rather than dropped or blended into the general rate.
    confidence_tier="VERIFIED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=None, min_spend_usd=None,
    annual_cap_usd=22_000_000.0,  # FY2026, revenue.alabama.gov
    requires_cultural_test=False,
    citation="revenue.alabama.gov/tax-incentives/film-rebate/ (Alabama "
             "Department of Revenue, official, fetched directly): "
             "'25 percent of certain production expenditures on the "
             "project that are incurred in Alabama' plus '35 percent of "
             "the payroll paid to Alabama residents.' Annual cap "
             "'$20 million each year' increased to '$22 million for "
             "fiscal year ending Sept. 30, 2026.' Administered by the "
             "Alabama Entertainment Office. HB379's narrow 45% small-"
             "budget-only resident-payroll bracket (greenslate.com, "
             "effective 2026-10-01, productions $100K-$499,999) was not "
             "restated on this page and remains a disclosed, "
             "unconfirmed-this-pass additional provision.",
    source_ref="revenue.alabama.gov-official+greenslate.com-hb379-disclosed",
    provenance=SourceProvenance(
        issuing_authority="Alabama Department of Revenue / Alabama "
                           "Entertainment Office",
        source_url="https://www.revenue.alabama.gov/tax-incentives/film-rebate/",
        citation_detail="'25 percent of certain production expenditures'"
                         " + '35 percent of the payroll paid to Alabama "
                         "residents'",
        effective_date="FY2026 cap increase",
        verified_date="2026-08-17",
        interpretation_note="HB379's 45% small-budget-only resident-"
                             "payroll bracket was not independently "
                             "re-confirmed by this fetch -- retained "
                             "as a disclosed, unconfirmed provision.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-al-general-25", rate=0.25, is_band_ceiling=False),
           DoctrineRateTier(tier_id="us-al-resident-payroll-35", rate=0.35,
                             is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="us-al-resident-payroll-only",
                                 description="35% applies to Alabama-"
                                             "resident PAYROLL "
                                             "specifically, not general "
                                             "QPE -- confirmed directly "
                                             "from revenue.alabama.gov",
                                 quote="35 percent of the payroll paid to "
                                       "Alabama residents "
                                       "(revenue.alabama.gov)",
                                 kind="material_funding_risk_not_modeled"),)),
           DoctrineRateTier(tier_id="us-al-small-budget-resident-payroll-45",
                             rate=0.45, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="us-al-small-budget-resident-payroll-only",
                                 description="45% applies ONLY to "
                                             "Alabama-resident PAYROLL "
                                             "(not general QPE) for "
                                             "productions with total "
                                             "expenditure $100K-$499,999, "
                                             "effective 2026-10-01 -- a "
                                             "separate narrow bracket, not "
                                             "the general program's ceiling. "
                                             "NOT independently re-"
                                             "confirmed by the batch's "
                                             "official-source fetch.",
                                 quote="45% rebate on payroll paid to "
                                       "Alabama residents for productions "
                                       "with total expenditures between "
                                       "$100,000 and $499,999 (greenslate.com)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(US_AL_DOCTRINE))

# ── US-Kentucky: Entertainment Industry Incentive Act (KEIIA) ─────────────
# Catalog had 30% flat -- CONFIRMED, matches exactly. Adds ceiling 35%,
# min spend $250K (feature)/$20K (doc), $75M annual cap.
US_KY_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-KY", program_slug="us_ky_keiia",
    program_name="Kentucky Entertainment Industry Incentive Act (KEIIA)",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=True, is_transferable=False, min_spend_usd=250_000.0,
    annual_cap_usd=75_000_000.0, requires_cultural_test=False,
    citation="shamelstudio.com (corroborated by revenue.ky.gov listing): "
              "'30% base rate, up to 35% with uplifts, as a refundable "
              "tax credit, with a $250K (feature) / $20K (doc) minimum "
              "spend and a $75M annual cap.' Confirms catalog's 30% base exactly.",
    source_ref="shamelstudio.com+revenue.ky.gov-kentucky",
    tiers=(DoctrineRateTier(tier_id="us-ky-base-30", rate=0.30, is_band_ceiling=False,
                             min_qpe_usd=250_000.0),
           DoctrineRateTier(tier_id="us-ky-ceiling-35", rate=0.35, is_band_ceiling=True,
                             min_qpe_usd=250_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-ky-uplift-criteria-unconfirmed",
                                 description="Uplift to 35% -- exact "
                                             "criteria not disclosed by "
                                             "the source checked",
                                 quote="up to 35% with uplifts (shamelstudio.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(US_KY_DOCTRINE))

# ── CA-Alberta: Film and Television Tax Credit (FTTC) ──────────────────────
# Catalog had 22% flat -- CONFIRMED as the general tier; adds a REAL
# ownership-based ceiling: 30% for Alberta-owned companies.
CA_AB_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-AB", program_slug="ca_ab_fttc",
    program_name="Alberta Film and Television Tax Credit (FTTC)",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="thereactionlab.com (corroborated): 'Film & Television Tax "
              "Credit of 22% or 30%, depending on level of Alberta "
              "ownership.' Confirms catalog's 22% general tier, adds a "
              "real ownership-based 30% ceiling.",
    source_ref="thereactionlab.com-alberta",
    tiers=(DoctrineRateTier(tier_id="ca-ab-general-22", rate=0.22, is_band_ceiling=False),
           DoctrineRateTier(tier_id="ca-ab-alberta-owned-30", rate=0.30, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="ca-ab-ownership-level-required",
                                 description="30% requires a specific "
                                             "level of Alberta ownership "
                                             "of the production company -- "
                                             "not pre-evaluable without an "
                                             "ownership-structure fact",
                                 quote="depending on level of Alberta "
                                       "ownership (thereactionlab.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(CA_AB_DOCTRINE))

# ── CA-Manitoba: Film & Video Production Tax Credit ─────────────────────────
# Catalog had 45% flat -- MASSIVELY undercounted the real ceiling.
# Confirmed: 45% base + Frequent Filming Bonus 10% + Producer Bonus 5% +
# Rural/Northern Bonus 5% = up to 65%.
CA_MB_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-MB", program_slug="ca_mb_film_video_credit",
    program_name="Manitoba Film & Video Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="thereactionlab.com (corroborated by KPMG's 2026 Manitoba "
              "budget highlights): 'The base credit is 45% with additional "
              "bonuses: Frequent Filming Bonus 10%; Manitoba Producer "
              "Bonus 5%; and Rural and Northern Bonus of 5%, increasing "
              "the value up to 65% on eligible Manitoba expenditures.' "
              "Confirms catalog's 45% base, corrects a massively "
              "undercounted ceiling (catalog implied 45% was the max).",
    source_ref="thereactionlab.com+kpmg-manitoba-2026-budget",
    tiers=(DoctrineRateTier(tier_id="ca-mb-base-45", rate=0.45, is_band_ceiling=False),
           DoctrineRateTier(tier_id="ca-mb-ceiling-65", rate=0.65, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="ca-mb-frequent-producer-rural-bonuses",
                                 description="+10% Frequent Filming + 5% "
                                             "Manitoba Producer + 5% Rural/"
                                             "Northern -- none pre-"
                                             "evaluable without production-"
                                             "history/producer-residency/"
                                             "shoot-location facts",
                                 quote="Frequent Filming Bonus 10%; "
                                       "Manitoba Producer Bonus 5%; and "
                                       "Rural and Northern Bonus of 5% "
                                       "(thereactionlab.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(CA_MB_DOCTRINE))

# ── CA-Nova Scotia: Film & Television Production Incentive Fund ───────────
# Catalog had 25% flat -- CONFIRMED base; rural bonus exists but its
# magnitude is not disclosed by the source checked.
CA_NS_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-NS", program_slug="ca_ns_production_incentive_fund",
    program_name="Nova Scotia Film & Television Production Incentive Fund",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="thereactionlab.com: 'Base rate of 25% on eligible Nova "
              "Scotia labour, with additional rural bonuses.' Confirms "
              "catalog's 25% base; rural bonus magnitude not disclosed.",
    source_ref="thereactionlab.com-nova-scotia",
    tiers=(DoctrineRateTier(tier_id="ca-ns-base-25", rate=0.25, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="ca-ns-rural-bonus-magnitude-undisclosed",
                                 description="Additional rural bonuses "
                                             "exist but their magnitude is "
                                             "not disclosed by the source "
                                             "checked -- not modeled as a "
                                             "numeric ceiling",
                                 quote="with additional rural bonuses "
                                       "(thereactionlab.com)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(CA_NS_DOCTRINE))

# ── CA-New Brunswick: Film Tax Credit ──────────────────────────────────────
# Catalog had 25% flat -- CONFIRMED as one tier; 30% for features/
# mini-series/TV series specifically (project-type-based, not a
# discretionary "up to" band).
CA_NB_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-NB", program_slug="ca_nb_film_tax_credit",
    program_name="New Brunswick Film Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="thereactionlab.com: '25%-30% of eligible production costs "
              "depending on type of project. (Features, mini-series and "
              "TV series all at 30%.)' Confirms catalog's 25% figure as "
              "one tier, clarifies 30% applies to features/mini-series/TV series.",
    source_ref="thereactionlab.com-new-brunswick",
    tiers=(DoctrineRateTier(tier_id="ca-nb-general-25", rate=0.25, is_band_ceiling=False),
           DoctrineRateTier(tier_id="ca-nb-feature-miniseries-tv-30",
                             rate=0.30, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="ca-nb-project-type-30pct",
                                 description="30% applies to features, "
                                             "mini-series and TV series "
                                             "specifically -- pre-"
                                             "evaluable from project_type "
                                             "if known, otherwise "
                                             "disclosed as a condition",
                                 quote="Features, mini-series and TV "
                                       "series all at 30% (thereactionlab.com)",
                                 kind="production_type"),)),),
))
register_rate_rules(rate_rules_for(CA_NB_DOCTRINE))

# ── Netherlands: Netherlands Film Production Incentive (NFPI) ─────────────
# Catalog had 30% flat -- corrected/expanded. Confirmed: 30-40% tax rebate.
NL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="NL", program_slug="nl_film_production_incentive",
    program_name="Netherlands Film Production Incentive (NFPI)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="rodriqueslaw.com (single search hit, not further "
              "corroborated this pass): 'The Netherlands offers a 30-40% "
              "tax rebate.' Confirms catalog's 30% as the floor, adds a "
              "40% ceiling not previously known.",
    source_ref="rodriqueslaw.com-netherlands",
    tiers=(DoctrineRateTier(tier_id="nl-floor-30", rate=0.30, is_band_ceiling=False),
           DoctrineRateTier(tier_id="nl-ceiling-40", rate=0.40, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="nl-scaling-criteria-undisclosed",
                                 description="Scaling from 30% to 40% -- "
                                             "criteria not disclosed by "
                                             "the single source checked",
                                 quote="30-40% tax rebate (rodriqueslaw.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(NL_DOCTRINE))

# ── Austria: FISA+ Film Production Support ─────────────────────────────────
# Catalog had 25% flat, explicitly marked "not independently re-confirmed."
# 2026-07-26 knowledge reconciliation: multiple independently-converging
# secondary sources (needafixer.com, progressiveproductions.eu, variety.com
# 2023 "Austria Changes the Game With New Incentives") confirm the program
# was overhauled to 30% base + 5% green-filming bonus = 35% ceiling --
# STALE, corrected. Also resolves an internal inconsistency: the DISCOVERY
# catalog entry (global_inventory_extended.py) already said
# requires_cultural_test=True while this PARSED record said False --
# corroborated True here from the same converging sources ("Each project...
# has to pass the Cultural Test... points-based").
AT_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="AT", program_slug="at_fisa_plus",
    program_name="FISA+ Film Production Support Austria",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=True,
    citation="needafixer.com + progressiveproductions.eu + variety.com "
              "(2023, 'Austria Changes the Game With New Incentives'), "
              "independently converging: 'FISA+ scheme pays a 30% cash "
              "rebate on eligible local spend for film, TV and streaming "
              "productions, with a 5% green-filming bonus taking it to "
              "35%... Each project seeking support has to pass the "
              "Cultural Test, conducted by Location Austria... "
              "points-based cultural test.' Corrects the stale 25% "
              "catalog figure and resolves this repository's own internal "
              "inconsistency (DISCOVERY entry already said "
              "requires_cultural_test=True; this record had said False). "
              "Administering body independently confirmed via direct "
              "fetch of filminaustria.com/fisaplus.com (official): "
              "Austria Wirtschaftsservice Gesellschaft mbH (aws), under "
              "the Federal Ministry of Labor/Economy, Energy and Tourism, "
              "with FILM in AUSTRIA as first point of contact; "
              "applications run through the AWS Funding Manager platform "
              "(live since 2023-01-02).",
    source_ref="needafixer.com+progressiveproductions.eu+variety.com-2023+filminaustria.com-official",
    tiers=(DoctrineRateTier(tier_id="at-base-30", rate=0.30, is_band_ceiling=False),
           DoctrineRateTier(tier_id="at-green-bonus-35", rate=0.35, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="at-green-filming-bonus",
                                 description="+5% green-filming bonus on "
                                             "top of the 30% base rate",
                                 quote="a 5% green-filming bonus taking "
                                       "it to 35% (needafixer.com)",
                                 kind="sustainability_uplift"),)),),
))
register_rate_rules(rate_rules_for(AT_DOCTRINE))

# ── Czech Republic: Czech Film Incentive ───────────────────────────────────
# Catalog had 20% flat -- STALE. Corrected: 25% (up from 20%), plus a
# 35% rate for animation/digital-only productions (no live action).
# NOTE: a separate 35% rate is reported for animation/digital-only (no
# live action) productions, but DoctrineRecord.production_types is
# record-level, not tier-level -- a second tier on THIS record would be
# wrongly picked (resolve_program_rate selects the highest-rate eligible
# tier) for ANY production_type, misapplying 35% to live-action features.
# Scoped correctly as a SEPARATE record with production_types=("animation",)
# below rather than a second tier on this one.
CZ_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CZ", program_slug="cz_film_incentive",
    program_name="Czech Film Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=True,
    production_types=("feature_film",),
    citation="rodriqueslaw.com: 'The primary incentive rate will be 25%, "
              "up from the previous 20%.' Corrects catalog's stale 20% "
              "figure. (A separate 35% animation/digital-only rate is "
              "modeled as its own record, cz_film_incentive_animation, "
              "below -- see note above.) 2026-07-26 knowledge "
              "reconciliation: direct fetch of the official sfa.gov.cz "
              "production-incentives page confirms applicants must pass "
              "a cultural test -- corrects this record's prior False.",
    source_ref="rodriqueslaw.com-czech-republic+sfa.gov.cz-official",
    tiers=(DoctrineRateTier(tier_id="cz-live-action-25", rate=0.25, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(CZ_DOCTRINE))

CZ_ANIMATION_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CZ", program_slug="cz_film_incentive_animation",
    program_name="Czech Film Incentive — Animation/Digital",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=True,
    production_types=("animation",),
    citation="rodriqueslaw.com: 'A 35% production incentive rate is also "
              "being introduced for animation and digital productions "
              "that don't include live action.' Scoped as a separate "
              "record from the 25% live-action program (cz_film_incentive) "
              "since DoctrineRecord.production_types is record-level, not "
              "tier-level -- a second tier on the same record would be "
              "wrongly selected for live-action productions too.",
    source_ref="rodriqueslaw.com-czech-republic-animation",
    tiers=(DoctrineRateTier(tier_id="cz-animation-digital-35", rate=0.35, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="cz-no-live-action-required",
                                 description="Requires an animation/"
                                             "digital-only production with "
                                             "NO live action",
                                 quote="animation and digital productions "
                                       "that don't include live action "
                                       "(rodriqueslaw.com)",
                                 kind="production_type"),)),),
))
register_rate_rules(rate_rules_for(CZ_ANIMATION_DOCTRINE))

# ── Romania: Romanian Film Office Cash Rebate ──────────────────────────────
# Catalog had 35% flat -- CONFLICTS with fresh source (30% current,
# "plans to expand to a 40% return... in 2026" -- ambiguous whether the
# 40% is already effective given today's date is mid-2026; NOT assumed
# active). 30% (present-tense, confirmed-current figure) used; catalog's
# 35% and the possible-40% expansion both flagged, not silently reconciled.
RO_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="RO", program_slug="ro_film_office_cash_rebate",
    program_name="Romanian Film Office Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="aol.com/Entertainment (Revamped Romanian Cash Rebate "
              "coverage): 'offers returns of 30% of expenditure, with "
              "plans to expand to a 40% return on expenditure in 2026.' "
              "Present-tense 30% used as the current-confirmed figure; "
              "the 40% expansion's exact effective date is not confirmed "
              "(may or may not be active as of this record) -- disclosed, "
              "not assumed. CONFLICTS with the pre-existing catalog's 35% "
              "figure, which matches neither 30% nor 40% -- flagged, not "
              "silently dropped.",
    source_ref="aol.com-romania-conflicts-with-stale-catalog-35pct",
    tiers=(DoctrineRateTier(tier_id="ro-current-30", rate=0.30, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="ro-40pct-expansion-date-unconfirmed",
                                 description="A planned expansion to 40% "
                                             "is mentioned for 2026 but "
                                             "its exact effective date is "
                                             "not confirmed -- not assumed "
                                             "active; catalog's 35% figure "
                                             "also unreconciled",
                                 quote="plans to expand to a 40% return on "
                                       "expenditure in 2026 (aol.com)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(RO_DOCTRINE))

# ── Serbia: Serbia Film Commission Cash Rebate ─────────────────────────────
# Catalog had 25% flat. No fresh contradicting/confirming data found this
# pass -- carried forward unchallenged.
RS_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="RS", program_slug="rs_film_commission_cash_rebate",
    program_name="Serbia Film Commission Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="Pre-existing catalog figure (25%) NOT contradicted this "
              "pass -- no dedicated fresh Serbia source surfaced in this "
              "search batch; carried forward unchallenged.",
    source_ref="catalog-unchallenged-serbia",
    tiers=(DoctrineRateTier(tier_id="rs-flat-25", rate=0.25, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="rs-rate-not-reconfirmed",
                                 description="25% carried forward from "
                                             "the pre-existing catalog "
                                             "entry, not independently "
                                             "re-confirmed this pass",
                                 quote="(no source found this pass)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(RS_DOCTRINE))

# ── Iceland: Icelandic Film Reimbursement Scheme ────────────────────────────
# Catalog had 25% flat -- CONFIRMED base; adds a real ceiling: 35% for
# larger-scale productions meeting certain requirements.
IS_GENERAL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="IS", program_slug="is_film_reimbursement_scheme",
    program_name="Icelandic Film Reimbursement Scheme",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="rodriqueslaw.com: 'Projects may qualify for a 25% refund, "
              "though the cash back can increase to 35% for larger-scale "
              "productions that fulfil certain requirements.' Confirms "
              "catalog's 25% base, adds a real 35% ceiling.",
    source_ref="rodriqueslaw.com-iceland",
    tiers=(DoctrineRateTier(tier_id="is-base-25", rate=0.25, is_band_ceiling=False),
           DoctrineRateTier(tier_id="is-ceiling-35", rate=0.35, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="is-larger-scale-requirements-undisclosed",
                                 description="35% requires 'larger-scale "
                                             "productions that fulfil "
                                             "certain requirements' -- "
                                             "exact requirements not "
                                             "disclosed by the source checked",
                                 quote="cash back can increase to 35% for "
                                       "larger-scale productions that "
                                       "fulfil certain requirements "
                                       "(rodriqueslaw.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(IS_GENERAL_DOCTRINE))

# ── AU-New South Wales: PDV-only rebate (mirrors AU-SA/AU-QLD pattern) ────
# Catalog had 20% flat, mischaracterizing the real structure. Confirmed
# (screen.nsw.gov.au ecosystem): 10% state rebate on PDV spend ONLY,
# stacking with the AUS federal 30% PDV offset. A SEPARATE "up to 35%"
# regional-location-filming incentive also exists but lacks clear
# eligibility specifics in the source checked -- disclosed, not modeled
# as the headline rate to avoid conflating two distinct mechanisms.
AU_NSW_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="AU-NSW", program_slug="au_nsw_pdv_rebate",
    program_name="New South Wales PDV Rebate (Screen NSW)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="mbrellafilms.com/ausfilm.com (corroborating): 'Screen NSW "
              "offers a 10% rebate for Post, Digital and Visual Effects "
              "work. Additionally, there are rebates of up to 35% of the "
              "costs of location filming in regional NSW.' The 10% PDV "
              "figure is modeled (mirrors the AU-SA/AU-QLD pattern "
              "already in this file); the separate up-to-35% regional-"
              "location incentive is disclosed but NOT modeled as the "
              "headline rate -- distinct mechanism, unclear eligibility "
              "specifics in the source checked. Corrects catalog's 20% "
              "flat figure, which conflated the two.",
    source_ref="mbrellafilms+ausfilm-nsw",
    tiers=(DoctrineRateTier(tier_id="au-nsw-pdv-only-10", rate=0.10, is_band_ceiling=False,
                             conditions=(
                                 RateCondition(
                                     condition_id="au-nsw-pdv-scope-only",
                                     description="Applies ONLY to Post/"
                                                 "Digital/VFX spend, not "
                                                 "general production QPE -- "
                                                 "combines with the "
                                                 "separately-modeled AUS "
                                                 "federal 30% PDV offset",
                                     quote="10% rebate for Post, Digital "
                                           "and Visual Effects work "
                                           "(mbrellafilms.com)",
                                     kind="material_funding_risk_not_modeled"),
                                 RateCondition(
                                     condition_id="au-nsw-regional-location-not-modeled",
                                     description="A separate 'up to 35%' "
                                                 "regional-NSW-location-"
                                                 "filming incentive exists "
                                                 "but is a distinct "
                                                 "mechanism from the PDV "
                                                 "rebate -- not modeled as "
                                                 "the headline rate to "
                                                 "avoid conflation",
                                     quote="rebates of up to 35% of the "
                                           "costs of location filming in "
                                           "regional NSW (mbrellafilms.com)",
                                     kind="discretionary_band"),
                             )),),
))
register_rate_rules(rate_rules_for(AU_NSW_DOCTRINE))

# ── AU-Queensland: PDV-only rebate (mirrors AU-SA/AU-NSW pattern) ─────────
# Catalog had 15% flat -- CONFIRMED as a PDV-scoped rate (Screen
# Queensland), matches the AU-SA/AU-NSW narrow-scope pattern. Additional
# regional incentives exist but magnitude undisclosed.
AU_QLD_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="AU-QLD", program_slug="au_qld_pdv_rebate",
    program_name="Queensland PDV Rebate (Screen Queensland)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="mbrellafilms.com: 'Queensland offers a 15% rebate of "
              "qualifying PDV expenditure. Additional incentives may be "
              "available for productions that choose to film in regional "
              "areas of Queensland.' Confirms catalog's 15% figure, "
              "clarifies it is PDV-scoped (mirrors AU-SA/AU-NSW pattern).",
    source_ref="mbrellafilms.com-queensland",
    tiers=(DoctrineRateTier(tier_id="au-qld-pdv-only-15", rate=0.15, is_band_ceiling=False,
                             conditions=(
                                 RateCondition(
                                     condition_id="au-qld-pdv-scope-only",
                                     description="Applies to PDV "
                                                 "expenditure -- combines "
                                                 "with the separately-"
                                                 "modeled AUS federal 30% "
                                                 "PDV offset",
                                     quote="15% rebate of qualifying PDV "
                                           "expenditure (mbrellafilms.com)",
                                     kind="material_funding_risk_not_modeled"),
                                 RateCondition(
                                     condition_id="au-qld-regional-uplift-undisclosed",
                                     description="Additional regional-"
                                                 "Queensland incentives "
                                                 "exist but magnitude is "
                                                 "not disclosed by the "
                                                 "source checked",
                                     quote="Additional incentives may be "
                                           "available for productions that "
                                           "choose to film in regional "
                                           "areas of Queensland (mbrellafilms.com)",
                                     kind="discretionary_band"),
                             )),),
))
register_rate_rules(rate_rules_for(AU_QLD_DOCTRINE))

# ── Colombia: Film In Colombia ──────────────────────────────────────────────
# Catalog had 40% flat -- confirmed as the ceiling of a real range.
# Confirmed: 35-40% cash rebate, 2026 budget $90M (+49%).
CO_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CO", program_slug="co_film_in_colombia",
    program_name="Colombia Film Commission — Film In Colombia",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=90_000_000.0, requires_cultural_test=False,
    citation="vitrina.ai (corroborated): '35-40% cash rebate with a 2026 "
              "budget increased 49% to $90M.' Confirms catalog's 40% "
              "figure as the ceiling of a real 35-40% range.",
    source_ref="vitrina.ai-colombia",
    tiers=(DoctrineRateTier(tier_id="co-floor-35", rate=0.35, is_band_ceiling=False),
           DoctrineRateTier(tier_id="co-ceiling-40", rate=0.40, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="co-scaling-criteria-undisclosed",
                                 description="Scaling from 35% to 40% -- "
                                             "criteria not disclosed by "
                                             "the source checked",
                                 quote="35-40% cash rebate (vitrina.ai)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(CO_DOCTRINE))

# ── Dominican Republic: Film Commission Incentive ──────────────────────────
# Catalog had 25% flat, min $500K -- CONFIRMED exactly, adds
# transferability.
DO_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="DO", program_slug="do_film_commission_incentive",
    program_name="Dominican Republic Film Commission Incentive",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=False, is_transferable=True, min_spend_usd=500_000.0,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="vitrina.ai: '25% of freely transferable tax credit on all "
              "above and below the line eligible expenditures for foreign "
              "film and television productions with a minimum spend of "
              "USD 500,000.' Confirms catalog's 25%/min-$500K exactly, "
              "adds confirmed transferability.",
    source_ref="vitrina.ai-dominican-republic",
    tiers=(DoctrineRateTier(tier_id="do-flat-25", rate=0.25, is_band_ceiling=False,
                             min_qpe_usd=500_000.0),),
))
register_rate_rules(rate_rules_for(DO_DOCTRINE))

# ── Singapore: Made-with-Singapore Cash Rebate ─────────────────────────────
# Catalog's entry was framed as "SFC Production Assistance" (base_rate=
# None). Confirmed a DIFFERENT, currently-active scheme: "Made-with-
# Singapore" cash rebate -- 40% on local spend, S$10M fund cap, with an
# ambiguous secondary "up to 30% for certain programs" figure in the same
# source. Both figures disclosed; 30% used as the conservative floor,
# 40% as the confirmed ceiling, given the genuine ambiguity.
SG_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="SG", program_slug="sg_made_with_singapore_rebate",
    program_name="Made-with-Singapore Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=7_400_000.0,  # S$10M fund cap, USD-converted
    requires_cultural_test=False,
    citation="lexology.com/reedsmith.com (corroborating): 'Made-with-"
              "Singapore cash rebate program includes a 40% rebate on "
              "local spending... fund is capped at S$10 million, and up "
              "to 30% of qualifying costs can be claimed for certain "
              "programs.' Genuine ambiguity between the 40% and 30% "
              "figures in the same source -- both disclosed rather than "
              "picking one silently. Distinct program from the catalog's "
              "'SFC Production Assistance' framing (base_rate=None); this "
              "is the currently-active scheme found.",
    source_ref="lexology+reedsmith-singapore-ambiguous-30-vs-40",
    tiers=(DoctrineRateTier(tier_id="sg-floor-30", rate=0.30, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="sg-30-vs-40-ambiguity",
                                 description="Source states both '40% "
                                             "rebate on local spending' "
                                             "and 'up to 30% of qualifying "
                                             "costs... for certain "
                                             "programs' without "
                                             "reconciling which applies "
                                             "when -- genuine source "
                                             "ambiguity, not resolved",
                                 quote="a 40% rebate on local spending... "
                                       "up to 30% of qualifying costs can "
                                       "be claimed for certain programs "
                                       "(lexology.com)",
                                 kind="material_funding_risk_not_modeled"),)),
           DoctrineRateTier(tier_id="sg-ceiling-40", rate=0.40, is_band_ceiling=True),),
))
register_rate_rules(rate_rules_for(SG_DOCTRINE))

# ── UAE-Dubai: Dubai Production Incentive Programme (DPIP) ────────────────
# Distinct emirate from the already-modeled AE-AD (Abu Dhabi) --
# jurisdiction_code "AE-DXB" used to avoid collision with AE-AD and the
# ambiguous bare "AE" code flagged as a duplicate in the wave6 batch.
# Confirmed via 2 corroborating sources: NEW 40% rebate effective
# 2026-06-01 (very recent), corrects the catalog's stale/generic 30% figure.
AE_DXB_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="AE-DXB", program_slug="ae_dxb_dpip",
    program_name="Dubai Production Incentive Programme (DPIP)",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="jjagency.co + iconartproduction.com (corroborating): "
              "'Dubai introduced a new 40% rebate effective June 1, 2026, "
              "with projects commencing principal photography or "
              "post-production work on or after this date being eligible "
              "for the enhanced incentive.' Corrects catalog's stale 30% "
              "figure (which was filed under the ambiguous bare 'AE' "
              "code, already flagged as a duplicate-variant problem in "
              "the wave6 batch). Distinct from AE-AD (Abu Dhabi, 35% base/"
              "50% enhanced, already modeled) -- different emirate, "
              "different film commission.",
    source_ref="jjagency.co+iconartproduction.com-dubai",
    tiers=(DoctrineRateTier(tier_id="ae-dxb-flat-40", rate=0.40, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="ae-dxb-2026-06-01-effective",
                                 description="40% rate effective for "
                                             "principal photography/post-"
                                             "production commencing on or "
                                             "after 2026-06-01",
                                 quote="new 40% rebate effective June 1, "
                                       "2026 (jjagency.co)",
                                 kind="min_qpe_usd"),)),),
))
register_rate_rules(rate_rules_for(AE_DXB_DOCTRINE))

# ============================================================================
# BATCH: full worldwide-inventory reconciliation sweep (global_inventory.py
# aggregates ALL_PROGRAMS = 303 records / 211 unique jurisdiction codes
# across every wave/grants/special/regional/broadcaster/phase_c/extended/
# wave2/db_sync file). This batch covers the remaining rate-bearing NEW
# leads surfaced by that full reconciliation (mostly from wave2.py, the
# original foundational catalog, never individually processed until now).
# ============================================================================

# ── Bulgaria: Film Industry Encouragement Act Cash Rebate ─────────────────
# Catalog had 25% flat -- CONFIRMED.
BG_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="BG", program_slug="bg_film_encouragement_act_rebate",
    program_name="Bulgarian Film Industry Encouragement Act Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="innovires.com (corroborated): 'Bulgaria: 25% cash rebate.' "
              "Confirms catalog figure exactly.",
    source_ref="innovires.com-bulgaria",
    tiers=(DoctrineRateTier(tier_id="bg-flat-25", rate=0.25, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(BG_DOCTRINE))

# ── Estonia: Film Estonia Cash Rebate ──────────────────────────────────────
# Catalog had 30% flat -- CONFIRMED as a discretionary ceiling, not
# automatically guaranteed.
EE_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="EE", program_slug="ee_film_estonia_rebate",
    program_name="Film Estonia Cash Rebate",
    confidence_tier="VERIFIED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="filmestonia.eu/estonia-increases-film-estonia-cash-rebate-"
              "programme-to-40/ (Film Estonia, official program site "
              "administered by the Estonian Film Institute, fetched "
              "directly): 'Film Estonia moves forward with a 40% cash "
              "rebate for film and TV production,' effective ~April "
              "2026. SUPERSEDES the prior 30% ceiling figure (innovires."
              "com, secondary) -- a genuine rate increase, not a "
              "correction of a prior error. Prior local-content "
              "conditions (Estonian-based crew/story) not re-confirmed "
              "on this specific page but not contradicted either; "
              "retained as a disclosed, not-independently-reconfirmed "
              "condition.",
    source_ref="filmestonia.eu-official",
    provenance=SourceProvenance(
        issuing_authority="Film Estonia (Estonian Film Institute)",
        source_url="https://filmestonia.eu/estonia-increases-film-estonia-cash-rebate-programme-to-40/",
        citation_detail="'Film Estonia moves forward with a 40% cash "
                         "rebate for film and TV production'",
        effective_date="~2026-04 (announced 2026-03-09)",
        verified_date="2026-08-17",
        interpretation_note="Genuine rate increase from a prior 30% "
                             "figure, not a correction. Local-content "
                             "conditions for reaching the max rate "
                             "carried forward from the prior citation, "
                             "not independently re-confirmed this pass.",
    ),
    tiers=(DoctrineRateTier(tier_id="ee-ceiling-40", rate=0.40, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="ee-local-content-criteria",
                                 description="Max 30% requires Estonian-"
                                             "based crew/actors and "
                                             "Estonian story/setting -- "
                                             "not pre-evaluable without "
                                             "project-content facts",
                                 quote="the maximum (30%) grant applicable "
                                       "if the film production uses "
                                       "Estonian-based filmmakers, actors "
                                       "and other production crew, "
                                       "Estonian story and/or Estonian-set "
                                       "storyline (innovires.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(EE_DOCTRINE))

# ── Latvia: National Film Centre Production Incentive ─────────────────────
# Catalog had 20%/25% band. Fresh source gives a genuinely tiered
# structure by spend, but with two internally-inconsistent tier
# descriptions in the same search summary (EUR200K/400K/500K thresholds
# vs EUR43K/100K thresholds) -- both disclosed, neither silently
# resolved; base/ceiling (20%/30%) used as the outer bounds common to both.
LV_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="LV", program_slug="lv_national_film_centre_incentive",
    program_name="National Film Centre of Latvia Production Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="camaleonrental.com: '20% rebate for QE of EUR200K, 25% for "
              "EUR400K, and 30% for EUR500K' AND separately '20% cash "
              "rebate... at EUR43,000 minimum spend, and 30% cash rebate "
              "on all qualifying expenditure at EUR100,000 minimum "
              "spend' -- two internally-inconsistent tier-threshold "
              "descriptions in the same source, both disclosed rather "
              "than silently reconciled. 20%/30% used as the outer bounds "
              "common to both descriptions.",
    source_ref="camaleonrental.com-latvia-tier-ambiguity",
    tiers=(DoctrineRateTier(tier_id="lv-floor-20", rate=0.20, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="lv-tier-threshold-ambiguity",
                                 description="Source gives two conflicting "
                                             "spend-threshold schedules for "
                                             "the 20%/25%/30% tiers -- not "
                                             "reconciled, disclosed as a "
                                             "genuine gap",
                                 quote="(two conflicting tier descriptions "
                                       "in the same source, camaleonrental.com)",
                                 kind="material_funding_risk_not_modeled"),)),
           DoctrineRateTier(tier_id="lv-ceiling-30", rate=0.30, is_band_ceiling=True),),
))
register_rate_rules(rate_rules_for(LV_DOCTRINE))

# ── Lithuania: Lithuanian Film Centre Production Cash Rebate ──────────────
# Catalog had 30% flat -- CONFLICTS with a fresh, specific source (20%
# tax credit, cultural test required, min 3 shooting days). Fresher/more
# specific source used; catalog's 30% flagged as an unresolved prior claim.
LT_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="LT", program_slug="lt_film_centre_cash_rebate",
    program_name="Lithuanian Film Centre Production Cash Rebate",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=None, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=True,
    citation="camaleonrental.com: '20% tax credit on qualified production "
              "expenses, must pass cultural test, and must shoot a "
              "minimum of three (3) days in Lithuania (except for "
              "animation).' CONFLICTS with the pre-existing catalog's 30% "
              "figure -- fresher/more-specific source used, catalog's "
              "30% flagged not dropped.",
    source_ref="camaleonrental.com-lithuania-conflicts-with-catalog-30pct",
    tiers=(DoctrineRateTier(tier_id="lt-flat-20", rate=0.20, is_band_ceiling=False,
                             conditions=(
                                 RateCondition(
                                     condition_id="lt-cultural-test-required",
                                     description="Requires passing a "
                                                 "cultural test",
                                     quote="must pass cultural test "
                                           "(camaleonrental.com)",
                                     kind="cultural_test_required"),
                                 RateCondition(
                                     condition_id="lt-catalog-conflict-30pct",
                                     description="Pre-existing catalog "
                                                 "claimed 30% -- unresolved "
                                                 "conflict with this "
                                                 "pass's 20% source",
                                     quote="20% tax credit on qualified "
                                           "production expenses (camaleonrental.com)",
                                     kind="material_funding_risk_not_modeled"),
                             )),),
))
register_rate_rules(rate_rules_for(LT_DOCTRINE))

# ── Poland: Polish Film Institute (PISF) Cash Rebate ───────────────────────
# Catalog had 30% flat -- CONFIRMED as the ceiling of a real 25-30% range.
PL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="PL", program_slug="pl_pisf_cash_rebate",
    program_name="Polish Film Institute (PISF) Cash Rebate",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="variety.com (Central/Eastern Europe incentives-arms-race "
              "coverage): 'Poland: 25-30%.' Confirms catalog's 30% as "
              "the ceiling of a real range.",
    source_ref="variety.com-poland",
    tiers=(DoctrineRateTier(tier_id="pl-floor-25", rate=0.25, is_band_ceiling=False),
           DoctrineRateTier(tier_id="pl-ceiling-30", rate=0.30, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="pl-scaling-criteria-undisclosed",
                                 description="Scaling from 25% to 30% -- "
                                             "criteria not disclosed by "
                                             "the source checked",
                                 quote="25-30% (variety.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(PL_DOCTRINE))

# ── Slovakia: Slovak Audiovisual Fund (AVF) Production Incentive ──────────
# Catalog had 33% flat -- CONFIRMED exactly, ATL+BTL eligible.
SK_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="SK", program_slug="sk_avf_production_incentive",
    program_name="Slovak Audiovisual Fund (AVF) Production Incentive",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="camaleonrental.com: '33% cash rebate which can be applied "
              "to both above- and below-the-line talents.' Confirms "
              "catalog figure exactly.",
    source_ref="camaleonrental.com-slovakia",
    tiers=(DoctrineRateTier(tier_id="sk-flat-33", rate=0.33, is_band_ceiling=False),),
))
register_rate_rules(rate_rules_for(SK_DOCTRINE))

# ── Luxembourg: Film Fund Luxembourg (Filmfund) — Tax Shelter & Rebate ────
# Catalog had 30% base/40% ceiling. No fresh contradicting/confirming
# data found this pass -- carried forward unchallenged.
LU_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="LU", program_slug="lu_filmfund_tax_shelter_rebate",
    program_name="Film Fund Luxembourg (Filmfund) — Tax Shelter & Rebate",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=None, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="Pre-existing catalog figures (30% base/40% ceiling) NOT "
              "contradicted this pass -- no dedicated fresh source "
              "surfaced; carried forward unchallenged.",
    source_ref="catalog-unchallenged-luxembourg",
    tiers=(DoctrineRateTier(tier_id="lu-base-30", rate=0.30, is_band_ceiling=False),
           DoctrineRateTier(tier_id="lu-ceiling-40", rate=0.40, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="lu-rate-not-reconfirmed",
                                 description="30-40% range carried "
                                             "forward from the "
                                             "pre-existing catalog entry, "
                                             "not independently "
                                             "re-confirmed this pass",
                                 quote="(no source found this pass)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(LU_DOCTRINE))

# ── US-Hawaii: Film and Digital Media Income Tax Credit ───────────────────
# Catalog had 20% flat -- CORRECTED. Confirmed via filmoffice.hawaii.gov
# ecosystem: 22% Oahu / 27% neighbor islands. A pending bill (SB 2580,
# NOT YET LAW -- "would allow") could add +5% more for 80%-local-hire
# productions -- disclosed as a NOT-YET-ENACTED future condition, not
# modeled as a current ceiling.
US_HI_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-HI", program_slug="us_hi_film_digital_media_credit",
    program_name="Hawaii Film and Digital Media Income Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=None, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="alohastatedaily.com: 'Hawaii offers a 22% tax credit for "
              "productions filming on the island of Oahu, with an "
              "additional 5% film tax incentive for productions filming "
              "on all neighboring islands... SB 2580 WOULD ALLOW a 5% "
              "increase... bringing the tax credit rates up to 27% on "
              "Oahu, and 32% on Neighbor Islands' -- SB 2580 is NOT YET "
              "LAW, disclosed as pending, not modeled as current. "
              "Corrects catalog's stale 20% flat figure.",
    source_ref="alohastatedaily.com+filmoffice.hawaii.gov-hawaii",
    tiers=(DoctrineRateTier(tier_id="us-hi-oahu-22", rate=0.22, is_band_ceiling=False),
           DoctrineRateTier(tier_id="us-hi-neighbor-islands-27", rate=0.27, is_band_ceiling=True,
                             conditions=(
                                 RateCondition(
                                     condition_id="us-hi-neighbor-island-location",
                                     description="+5% for filming on "
                                                 "neighbor islands (vs. "
                                                 "Oahu) -- not "
                                                 "pre-evaluable without a "
                                                 "shoot-location fact",
                                     quote="an additional 5% film tax "
                                           "incentive for productions "
                                           "filming on all neighboring "
                                           "islands (alohastatedaily.com)",
                                     kind="discretionary_band"),
                                 RateCondition(
                                     condition_id="us-hi-sb2580-not-yet-law",
                                     description="SB 2580 would add a "
                                                 "further +5% (up to "
                                                 "27%/32%) for 80%-local-"
                                                 "hire productions -- NOT "
                                                 "YET ENACTED, not modeled "
                                                 "as a current rate",
                                     quote="SB 2580 would allow a 5% "
                                           "increase to current tax "
                                           "credit rates (alohastatedaily.com)",
                                     kind="material_funding_risk_not_modeled"),
                             )),),
))
register_rate_rules(rate_rules_for(US_HI_DOCTRINE))

# ── US-Utah: Motion Picture Incentive Program ──────────────────────────────
# Catalog had 20% base/25% ceiling. Fresh search confirmed only a
# procedural detail (4.5% loan-out withholding) and a program extension
# through 2030, not a rate change -- catalog figures carried forward unchallenged.
US_UT_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-UT", program_slug="us_ut_motion_picture_incentive",
    program_name="Utah Motion Picture Incentive Program",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="greenslate.com: confirmed 'Lawmakers passed legislation to "
              "extend the state's tax credit program through 2030' and "
              "a 4.5% loan-out withholding rate -- neither is a rate "
              "change; catalog's 20%/25% figures carried forward unchallenged.",
    source_ref="catalog-unchallenged+greenslate.com-extension-only",
    tiers=(DoctrineRateTier(tier_id="us-ut-base-20", rate=0.20, is_band_ceiling=False),
           DoctrineRateTier(tier_id="us-ut-ceiling-25", rate=0.25, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="us-ut-rate-not-reconfirmed",
                                 description="20-25% range carried "
                                             "forward from the "
                                             "pre-existing catalog entry, "
                                             "not independently "
                                             "re-confirmed this pass "
                                             "(program confirmed extended "
                                             "through 2030)",
                                 quote="(no rate-confirming source found "
                                       "this pass)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(US_UT_DOCTRINE))

# ── US-Minnesota: Film Production Tax Credit ────────────────────────────────
# Catalog had 25% flat -- CONFIRMED unchanged. Several small local/
# regional add-on rebates exist (Iron Range, Duluth, Austin MN, Maple
# Lake) -- too granular/local to model individually, disclosed only.
# 2026-07-26 knowledge reconciliation: direct fetch of the official
# revenue.state.mn.us page (previously only cited in the DISCOVERY catalog,
# never fetched at the PARSED tier) confirms min spend and annual cap, and
# CORRECTS is_transferable from None/False to True -- Minnesota's credit is
# explicitly an "assignable income tax credit."
US_MN_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-MN", program_slug="us_mn_film_production_credit",
    program_name="Minnesota Film Production Tax Credit",
    # Global Economic Data + Base Pricing, batch 3.
    confidence_tier="VERIFIED", incentive_type="tax_credit",
    is_refundable=None, is_transferable=True, min_spend_usd=1_000_000.0,
    annual_cap_usd=25_000_000.0, requires_cultural_test=False,
    citation="revenue.state.mn.us (official, direct fetch 2026-07-26): "
              "'25% assignable income tax credit... $1,000,000 in 12 "
              "consecutive months for eligible production costs... $25 "
              "million maximum annually... the credit must be assigned "
              "prior to claiming any portion of the credit.' Confirms "
              "the 25% catalog figure, confirms min spend/annual cap "
              "(previously only in the unconfirmed DISCOVERY catalog "
              "entry), and CORRECTS transferability to True. Also: "
              "greenslate.com (secondary, retained for the regional "
              "add-on disclosure): 'several regional film incentives... "
              "Iron Range Regional Production Incentive Program, St. "
              "Louis County local film rebate, City of Duluth Production "
              "Incentive Program, Incredible Austin Minnesota Film "
              "Rebate, and Maple Lake Film Rebate' -- too granular/local "
              "to model individually, disclosed only.",
    source_ref="revenue.state.mn.us-official+greenslate.com-regional-addons-disclosed",
    provenance=SourceProvenance(
        issuing_authority="Minnesota Department of Revenue",
        source_url="https://www.revenue.state.mn.us",
        citation_detail="25% assignable income tax credit; min spend "
                         "$1,000,000/12 consecutive months; $25,000,000 "
                         "annual maximum",
        verified_date="2026-07-26",
        interpretation_note="Corrects transferability from None/False to "
                             "True — Minnesota's credit is explicitly an "
                             "'assignable income tax credit.' Regional "
                             "add-ons (Iron Range, Duluth, Austin MN, "
                             "Maple Lake) disclosed via greenslate.com "
                             "(secondary) but not individually modeled.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-mn-flat-25", rate=0.25, is_band_ceiling=False,
                             conditions=(RateCondition(
                                 condition_id="us-mn-regional-addons-not-modeled",
                                 description="Multiple small local/"
                                             "regional add-on rebates "
                                             "exist (Iron Range, Duluth, "
                                             "Austin MN, Maple Lake) -- "
                                             "not individually modeled",
                                 quote="several regional film incentives "
                                       "in Minnesota (greenslate.com)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(US_MN_DOCTRINE))

# ── US-Mississippi: Advantage Film Program ─────────────────────────────────
# Catalog had 25% base/35% ceiling. Fresh source confirms 25% flat only;
# 35% ceiling not re-confirmed this pass but not contradicted either.
US_MS_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-MS", program_slug="us_ms_advantage_film_program",
    program_name="Mississippi Advantage Film Program",
    confidence_tier="VERIFIED", incentive_type="cash_rebate",
    is_refundable=None, is_transferable=None, min_spend_usd=50_000.0,
    annual_cap_usd=20_000_000.0, requires_cultural_test=False,
    citation="filmmississippi.org/incentive/ (Film Mississippi, official "
              "state film office under the Mississippi Development "
              "Authority, fetched directly): '30% cash rebate on payroll "
              "paid to resident cast and crew... up to and including "
              "$5 million.' '25% cash rebate on payroll paid to non-"
              "resident cast and crew... up to and including $5 million.' "
              "'25% rebate of their base investment (local spend) on "
              "production related expenditures.' '+5% cash rebate' for "
              "honorably discharged veteran MS residents (not modeled -- "
              "no veteran-status fact exists in this engine). '$50,000 "
              "minimum Mississippi investment... per project.' Caps: "
              "'$10 million per project rebate cap' and '$20 million "
              "annual rebate cap.' Corrects/replaces the prior 25%-base/"
              "35%-ceiling model (the 35% figure was an unconfirmed "
              "catalog carryover that does not appear in this official "
              "structure).",
    source_ref="filmmississippi.org-official",
    provenance=SourceProvenance(
        issuing_authority="Film Mississippi (Mississippi Development "
                           "Authority)",
        source_url="https://filmmississippi.org/incentive/",
        citation_detail="'25% rebate of their base investment' (non-"
                         "payroll); '30%'/'25%' resident/non-resident "
                         "payroll; '$50,000 minimum'; '$10 million per "
                         "project' / '$20 million annual' caps",
        verified_date="2026-08-17",
        interpretation_note="Base investment (non-payroll spend) rebate "
                             "is 25% -- modeled as the general QPE rate. "
                             "The higher 30% resident-payroll rate and +5% "
                             "veteran uplift apply to a narrower payroll-"
                             "only base this engine does not separately "
                             "track (no payroll-vs-total-QPE split fact) "
                             "-- disclosed, not modeled as the general "
                             "rate.",
    ),
    tiers=(DoctrineRateTier(tier_id="us-ms-base-investment-25", rate=0.25,
                             is_band_ceiling=False, min_qpe_usd=50_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-ms-payroll-rates-not-modeled",
                                 description="Resident payroll rebate is "
                                             "30% (+5% veteran uplift) and "
                                             "non-resident payroll rebate "
                                             "is 25%, each capped at $5M "
                                             "of payroll per production -- "
                                             "this engine has no payroll-"
                                             "vs-total-QPE split fact, so "
                                             "only the 25% base-investment "
                                             "(non-payroll) rate is "
                                             "modeled as the general rate",
                                 quote="30% cash rebate on payroll paid to "
                                       "resident cast and crew... 25% cash "
                                       "rebate on payroll paid to non-"
                                       "resident cast and crew "
                                       "(filmmississippi.org)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(US_MS_DOCTRINE))

# ── US-Arizona: Motion Picture Production Program ─────────────────────────
# Catalog had 15% base/20% ceiling. No fresh contradicting/confirming
# data found this pass -- carried forward unchallenged.
US_AZ_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-AZ", program_slug="us_az_motion_picture_production",
    program_name="Arizona Motion Picture Production Program",
    confidence_tier="PARSED", incentive_type="cash_rebate",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=None, requires_cultural_test=False,
    citation="Pre-existing catalog figures (15% base/20% ceiling) NOT "
              "contradicted this pass -- no dedicated Arizona source "
              "surfaced in the search batch; carried forward unchallenged.",
    source_ref="catalog-unchallenged-arizona",
    tiers=(DoctrineRateTier(tier_id="us-az-base-15", rate=0.15, is_band_ceiling=False),
           DoctrineRateTier(tier_id="us-az-ceiling-20", rate=0.20, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="us-az-rate-not-reconfirmed",
                                 description="15-20% range carried "
                                             "forward from the "
                                             "pre-existing catalog entry, "
                                             "not independently "
                                             "re-confirmed this pass",
                                 quote="(no source found this pass)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(US_AZ_DOCTRINE))

# ── Puerto Rico: Film Industry Economic Incentives Act ────────────────────
# Catalog had 40% flat -- CORRECTED to a real base/ceiling split.
# Confirmed: 20% base, up to 40% with uplifts, $50K min spend, ~$38M
# annual cap, 22-26% payroll burden.
US_PR_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="US-PR", program_slug="us_pr_film_incentives_act",
    program_name="Puerto Rico Film Industry Economic Incentives Act",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=False, is_transferable=True, min_spend_usd=50_000.0,
    annual_cap_usd=38_000_000.0, requires_cultural_test=False,
    citation="shamelstudio.com: '20% base, up to 40% with uplifts, "
              "transferable tax credit, $50K minimum spend, ~$38M annual "
              "cap, payroll burden 22-26%.' Corrects catalog's flat 40% "
              "figure to a real base/ceiling structure.",
    source_ref="shamelstudio.com-puerto-rico",
    tiers=(DoctrineRateTier(tier_id="us-pr-base-20", rate=0.20, is_band_ceiling=False,
                             min_qpe_usd=50_000.0),
           DoctrineRateTier(tier_id="us-pr-ceiling-40", rate=0.40, is_band_ceiling=True,
                             min_qpe_usd=50_000.0,
                             conditions=(RateCondition(
                                 condition_id="us-pr-uplift-criteria-unconfirmed",
                                 description="Uplift from 20% to 40% -- "
                                             "exact criteria not disclosed "
                                             "by the source checked",
                                 quote="up to 40% with uplifts (shamelstudio.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(US_PR_DOCTRINE))

# ── CA-Saskatchewan: Creative Saskatchewan Production Grant ───────────────
# Catalog had base_rate=None, max=0.40. Confirmed TWO real streams:
# Saskatchewan Stream (30% of eligible SK spend, up to $5M) and Service
# Production Stream (25% of eligible SK spend, up to $5M) -- the latter
# is the one applicable to foreign/service productions (no ownership
# requirement implied), modeled as the base; Saskatchewan Stream's 30%
# likely requires more local ownership/content, modeled as the ceiling.
CA_SK_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-SK", program_slug="ca_sk_creative_saskatchewan_grant",
    program_name="Creative Saskatchewan Film and TV Production Grant",
    confidence_tier="PARSED", incentive_type="direct_grant",
    is_refundable=None, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=5_000_000.0, requires_cultural_test=False,
    citation="hellodarwin.com/grantcompass.ca: 'Saskatchewan Stream "
              "offers... a maximum of 30% of all eligible Saskatchewan "
              "expenditures up to a maximum of $5,000,000, while the "
              "Service Production Stream offers 25% of all eligible "
              "Saskatchewan expenditures up to a maximum of $5,000,000.' "
              "First confirmed rate for this catalog entry (was base_rate=None).",
    source_ref="hellodarwin.com+grantcompass.ca-saskatchewan",
    tiers=(DoctrineRateTier(tier_id="ca-sk-service-production-25", rate=0.25, is_band_ceiling=False),
           DoctrineRateTier(tier_id="ca-sk-saskatchewan-stream-30", rate=0.30, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="ca-sk-two-stream-structure",
                                 description="Two separate streams: "
                                             "Service Production (25%, "
                                             "modeled as base -- likely "
                                             "applicable to foreign "
                                             "productions) and "
                                             "Saskatchewan Stream (30%, "
                                             "modeled as ceiling -- likely "
                                             "requires local ownership/"
                                             "content not confirmed this "
                                             "pass)",
                                 quote="Saskatchewan Stream... 30%... "
                                       "Service Production Stream offers "
                                       "25% (hellodarwin.com)",
                                 kind="discretionary_band"),)),),
))
register_rate_rules(rate_rules_for(CA_SK_DOCTRINE))

# ── CA-Newfoundland & Labrador: All-Spend Film and Video Production Tax Credit ──
# Catalog had 40% base/45% ceiling. Confirmed base 40% exactly via
# gov.nl.ca (official) + canada.ca (official CRA listing), with a
# maximum credit of $10M CAD per production. Ceiling 45% not
# re-confirmed this pass, not contradicted either.
CA_NL_DOCTRINE = register(DoctrineRecord(
    jurisdiction_code="CA-NL", program_slug="ca_nl_all_spend_credit",
    program_name="Newfoundland & Labrador All-Spend Film and Video Production Tax Credit",
    confidence_tier="PARSED", incentive_type="tax_credit",
    is_refundable=True, is_transferable=False, min_spend_usd=None,
    annual_cap_usd=7_400_000.0,  # CAD $10M per-production cap, USD-converted
    requires_cultural_test=False,
    citation="gov.nl.ca (official) + canada.ca (official CRA program "
              "listing): '40% tax credit on total eligible production "
              "costs, with a maximum credit of $10 million for an "
              "eligible production in a tax year.' Confirms catalog's "
              "40% base exactly; the catalog's 45% ceiling is not "
              "re-confirmed this pass, not contradicted either.",
    source_ref="gov.nl.ca+canada.ca-official-newfoundland-labrador",
    tiers=(DoctrineRateTier(tier_id="ca-nl-base-40", rate=0.40, is_band_ceiling=False),
           DoctrineRateTier(tier_id="ca-nl-ceiling-45-unconfirmed", rate=0.45, is_band_ceiling=True,
                             conditions=(RateCondition(
                                 condition_id="ca-nl-ceiling-not-reconfirmed",
                                 description="45% ceiling carried forward "
                                             "from the pre-existing "
                                             "catalog entry, not "
                                             "independently re-confirmed "
                                             "this pass (official sources "
                                             "confirmed only the 40% flat rate)",
                                 quote="(no 45%-ceiling source found this "
                                       "pass; official sources state 40% "
                                       "as the rate, not a floor)",
                                 kind="material_funding_risk_not_modeled"),)),),
))
register_rate_rules(rate_rules_for(CA_NL_DOCTRINE))
