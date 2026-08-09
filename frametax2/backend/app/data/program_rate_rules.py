"""
program_rate_rules.py

Statutory incentive-RATE rules per program, with the PERMANENT
rate-authority doctrine of this application:

  RULE 1 — Budget documents are never authoritative for incentive rates
           or statutory rules.
  RULE 2 — Any incentive percentage appearing in an uploaded budget or
           financial model is IGNORED for calculation purposes. It may
           be recorded (as data) solely so Rule 5 can report the
           conflict.
  RULE 3 — Incentive rates come only from this module (the incentive
           database's static mirror) and the statutory/guidance
           authority cited on each rule row.
  RULE 4 — Cross-border optimization compares jurisdictions using
           database/statutory rates only (jurisdiction_comparison
           profiles must mirror this module for any program it covers).
  RULE 5 — When the database and a production budget disagree, the
           database rate is used and the conflict is reported, never
           silently swallowed.

The same static-mirror discipline as program_spend_rules.py: nothing
here is invented — every rate, threshold, and condition carries the
verbatim quoted language and document it came from.

── Mauritius primary source (read in full, pdftotext, this repository's
   audit trail) ──
EDB "Film Rebate Scheme — Submission Procedures", 31 January 2020,
https://edbmauritius.org/wp-content/uploads/2022/10/Guideline-Online-Application-FRS.pdf
citing the Economic Development Board (Film Rebate Scheme) Regulation
2018. Corroborated (no additional conditions) by the Mauritius Chamber
of Commerce and Industry's Film Rebate Scheme page (mcci.org).
"""
from __future__ import annotations

from dataclasses import dataclass, field

PROGRAM_RATE_RULES_VERSION = "1.0.0"


@dataclass(frozen=True)
class RateCondition:
    condition_id: str
    description: str
    quote: str           # verbatim language from the cited document
    kind: str            # "production_type" | "min_qpe_usd" | "discretionary_band" |
                         # any other value (e.g. "no_sponsorship_in_qpe",
                         # "cultural_test_required") falls into the generic
                         # fact-dependent branch: satisfied=None, never assumed.
    threshold_usd: float | None = None


@dataclass(frozen=True)
class RateRule:
    """One rate tier of one program. is_band_ceiling=True means the
    source says 'up to' this rate — the exact awarded rate within the
    band is subject to the authority's assessment, so the rate is a
    modeling ceiling, not a guaranteed entitlement.

    graduated_brackets (optional): for a statute-confirmed MARGINAL/
    BRACKETED rate structure (e.g. Spain Art. 36.2: 30% on the first
    EUR 1M, 25% on the excess) — NOT a discretionary approval band like
    MU's 'up to 40%'. A tuple of (bracket_ceiling_usd, rate_in_bracket)
    pairs, applied progressively from 0. `rate` is the FINAL/marginal
    rate applied to any QPE above the last bracket ceiling (kept as a
    real field, not just the top of the tuple, so non-graduated callers
    are unaffected). When set, resolve_program_rate() computes a real
    BLENDED effective rate (total credit / QPE) instead of using `rate`
    flat — this is the maximum-lawful-incentive representation: neither
    the understated flat marginal rate nor an overstated flat top rate.
    """
    program_slug: str
    tier_id: str
    rate: float
    is_band_ceiling: bool
    production_types: tuple[str, ...]
    min_qpe_usd: float | None
    conditions: tuple[RateCondition, ...]
    confidence_tier: str     # DISCOVERY | PARSED | VERIFIED
    citation: str
    source_ref: str
    graduated_brackets: tuple[tuple[float, float], ...] | None = None


@dataclass(frozen=True)
class UnverifiedRateClaim:
    """A condition asserted by a NON-government source that could not be
    confirmed in any primary/government text reviewed. Recorded so the
    engine can disclose it as a risk item — never applied as a rule."""
    program_slug: str
    claim: str
    claimed_by: str
    verification_status: str


@dataclass(frozen=True)
class BudgetEvidencedRate:
    """A rate observed in an uploaded budget/financial model. Per RULE 1
    and RULE 2 this is NEVER an input to any calculation — it exists
    only so RULE 5 can report the conflict against the database rate."""
    program_slug: str
    rate: float
    observed_in: str


@dataclass(frozen=True)
class RateConflict:
    source_kind: str     # "budget_document" | "legacy_db_row"
    claimed_rate: float
    database_rate: float
    resolution: str
    detail: str


@dataclass(frozen=True)
class ConditionEvaluation:
    condition_id: str
    description: str
    quote: str
    satisfied: bool | None   # None = cannot be evaluated from known facts
    note: str


@dataclass(frozen=True)
class RateResolution:
    """The full, explainable outcome of resolving a program's rate for
    one production. modeled_rate is what the engine uses; floor_rate is
    the highest NON-band-ceiling tier the production also satisfies —
    the guaranteed fallback if the authority awards below the ceiling."""
    program_slug: str
    modeled_rate: float
    floor_rate: float
    is_band_ceiling: bool
    tier_id: str
    basis: str
    conditions_evaluated: tuple[ConditionEvaluation, ...]
    unverified_claims: tuple[UnverifiedRateClaim, ...]
    conflicts: tuple[RateConflict, ...]


# ── Mauritius EDB Film Rebate Scheme ────────────────────────────────────────

_MU_CITATION = (
    "EDB 'Film Rebate Scheme — Submission Procedures', 31 Jan 2020, "
    "citing the Economic Development Board (Film Rebate Scheme) "
    "Regulation 2018; corroborated by MCCI Film Rebate Scheme page."
)

MU_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="mu_edb_incentive",
        tier_id="mu_frs_30_general",
        rate=0.30,
        is_band_ceiling=False,
        production_types=(
            "feature_film", "creative_documentary", "digital_animated_film",
            "television_serial", "television_single_drama",
            "factual_television", "natural_history", "lifestyle_magazine",
            "commercial", "music_video", "dubbing",
        ),
        min_qpe_usd=100_000.0,  # foreign production, feature film ($50,000 local)
        conditions=(
            RateCondition(
                condition_id="mu30-qpe-local",
                description="QPE must be incurred locally",
                quote="30% rebate will be applicable on Qualifying Production "
                      "Expenditures (QPE) incurred locally and as described further below",
                kind="min_qpe_usd",
            ),
            RateCondition(
                condition_id="mu-no-sponsorship",
                description="Sponsorships/financial assistance for the Mauritian "
                            "schedule are excluded from the QPE quantum",
                quote="The QPE quantum should not include any forms of sponsorships "
                      "or financial assistance obtained for the Mauritian schedule "
                      "of the project.",
                kind="no_sponsorship_in_qpe",
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MU_CITATION,
        source_ref="EDB-2020-Submission-Procedures",
    ),
    RateRule(
        program_slug="mu_edb_incentive",
        tier_id="mu_frs_40_feature",
        rate=0.40,
        is_band_ceiling=True,   # "Up to 40%" — exact rate within the band is discretionary
        production_types=("feature_film", "tv_series"),
        min_qpe_usd=1_000_000.0,
        conditions=(
            RateCondition(
                condition_id="mu40-feature",
                description="Must be a feature film production company "
                            "(or drama series at $150,000/episode)",
                quote="Up to 40% rebate will be applicable on Qualifying Production "
                      "Expenditures (QPE) incurred locally, and as described further "
                      "below, by a feature film production company, subject to a "
                      "minimum QPE of USD 1,000,000 for feature film; and a minimum "
                      "QPE of USD 150,000 per episode of a drama series.",
                kind="production_type",
            ),
            RateCondition(
                condition_id="mu40-min-qpe",
                description="Minimum QPE of USD 1,000,000 (feature film)",
                quote="Eligible for up to 40% rebate — Feature film (including "
                      "animation): 1,000,000 [Minimum QPE (USD), foreign and local "
                      "production]",
                kind="min_qpe_usd",
                threshold_usd=1_000_000.0,
            ),
            RateCondition(
                condition_id="mu40-band-discretion",
                description="'Up to' 40% — the awarded rate within the band is "
                            "subject to Film Rebate Committee assessment and CEO "
                            "approval; 40% is a modeling ceiling, not an entitlement",
                quote="The purpose of the Film Rebate Committee will be to assess "
                      "projects in terms of its economic benefits ... and provide "
                      "recommendations to the Chief Executive Officer who shall "
                      "approve projects.",
                kind="discretionary_band",
            ),
            RateCondition(
                condition_id="mu-no-sponsorship",
                description="Sponsorships/financial assistance for the Mauritian "
                            "schedule are excluded from the QPE quantum",
                quote="The QPE quantum should not include any forms of sponsorships "
                      "or financial assistance obtained for the Mauritian schedule "
                      "of the project.",
                kind="no_sponsorship_in_qpe",
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MU_CITATION,
        source_ref="EDB-2020-Submission-Procedures",
    ),
)

# Conditions asserted by non-government sources only. Searched for and
# NOT found in the primary Submission Procedures document or MCCI's
# corroborating page (both reviewed verbatim). Disclosed, never applied.
MU_UNVERIFIED_CLAIMS: tuple[UnverifiedRateClaim, ...] = (
    UnverifiedRateClaim(
        program_slug="mu_edb_incentive",
        claim="The 40% tier requires 90% of filming to take place in Mauritius.",
        claimed_by="identicalpictures.com (production-services/fixer site); no "
                   "government source or regulation cited for the claim",
        verification_status="RESOLVED — REJECTED. Incentive/Optimizer Core Closeout "
                            "final rule resolution "
                            "(docs/validation/CODEX_FINAL_RULE_RESOLUTION.md §1.1, "
                            "cross-checked against docs/validation/"
                            "GEMINI_FINAL_RULE_RESOLUTION.md §1 where the two final "
                            "resolutions conflicted): the 90% condition belongs to a "
                            "SEPARATE measure — the Government's 2023/24 Budget "
                            "double deduction available to LOCAL companies "
                            "financing/sponsoring/marketing/distributing an approved "
                            "film — not to the EDB Film Rebate Scheme's 40% uplift, "
                            "per the National Assembly Hansard (14 May 2019) "
                            "explaining Regulations 2018 and the current EDB "
                            "submission guidance, neither of which attaches a 90% "
                            "production test to the rebate uplift. Codex's resolution "
                            "was preferred over Gemini's contrary (unsourced) answer "
                            "because it cites a specific parliamentary record and "
                            "dated primary guidance pages; Gemini's answer cited only "
                            "a generic, non-specific guidelines reference. NOT "
                            "enforced as a gate (confirmed correct, not merely "
                            "un-enforced).",
    ),
    UnverifiedRateClaim(
        program_slug="mu_edb_incentive",
        claim="Remuneration paid to foreign cast and crew must not exceed 40% of "
              "the total production budget allocated to Mauritius.",
        claimed_by="secondary trade sources (search results); no government "
                   "source cited",
        verification_status="NOT FOUND in the primary documents reviewed. Requires "
                            "EDB written confirmation.",
    ),
)

# Rates observed in production documents — Rule 1/2 data, never inputs.
MU_BUDGET_EVIDENCED_RATES: tuple[BudgetEvidencedRate, ...] = (
    BudgetEvidencedRate(
        program_slug="mu_edb_incentive",
        rate=0.35,
        observed_in="Little Utopia production budget line 'EDB Rebate at 35%: "
                    "$(1,275,411)' (also mirrored into migration 0009's "
                    "base_rate=0.35 row, itself budget-evidenced, not "
                    "statute-verified)",
    ),
)


## ── Malta, Ireland, Greece: PARSED-tier conversions ─────────────────────────
#
# Executable Jurisdiction Knowledge phase. Source: jurisdiction_comparison.py's
# own MALTA/IRELAND/GREECE JurisdictionIncentiveProfile records —
# confidence_tier="PARSED" (rates/caps already confirmed from a primary
# source per that module's own discipline: "Do not promote any cell to
# True without a primary-source citation"). This is a CONNECTION of
# already-vetted data to the rate-resolution engine, not new legal
# research — nothing here is invented.
#
# EUR->USD thresholds computed via the EXISTING FX engine
# (apply_fx_rates.convert_to_usd), using the real sourced snapshot rate
# on file (production_normalization.FX_RATE_SNAPSHOTS, EUR=0.87679,
# fetched 2026-07-13) — never a rough/rounded guess.
#   MT min spend  EUR 50,000   -> USD 57,026.20
#   IE min spend  EUR 125,000  -> USD 142,565.49
#   IE cap        EUR 70,000,000 (or 80% of budget, whichever lower) -> USD 79,836,676.97
#   GR min spend  EUR 100,000  -> USD 114,052.40

_MT_CITATION = (
    "CORRECTED 2026-07-26 via Document Retrieval Escalation: the prior "
    "citation here (25% base + three stacked uplifts of +3%/+3%/+7%, "
    "undated, traced only to this repository's own jurisdiction_comparison.py "
    "PARSED-tier notes) is SUPERSEDED. A prior session had downloaded the "
    "real MFC 'Financial Incentives for the Audiovisual Industry: CASH "
    "REBATE GUIDELINES' (Official Document, January 2019, 28 pages) but a "
    "tool parser limitation produced hallucinated placeholder analysis "
    "instead of the real text -- classified precisely as a PARSER FAILURE, "
    "not a retrieval failure, per the Document Retrieval Escalation "
    "doctrine. This session recovered the actual saved PDF and extracted "
    "its real text directly via pypdf, confirming the TRUE rate structure "
    "below. Full detail in app.data.program_requirements mt_mfc_rebate."
)
MT_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-general-30",
        rate=0.30, is_band_ceiling=False,
        production_types=("feature_film", "tv_series", "creative_documentary"),
        min_qpe_usd=113_000.0,  # EUR 100,000
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure (general case); "
                            "overall production budget must additionally exceed EUR 200,000",
                quote="The minimum spend in Malta must be EUR 100,000 with an overall "
                      "budget exceeding EUR 200,000 (MFC Cash Rebate Guidelines, Jan 2019, S.2.3)",
                kind="min_qpe_usd", threshold_usd=113_000.0,
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MT_CITATION + " Category A (all qualifying productions except "
                 "Animation/VFX): 30% base on all eligible expenditure for non-Maltese "
                 "productions (S.3.2.1).",
        source_ref="MFC-Cash-Rebate-Guidelines-2019-01-official",
    ),
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-general-ceiling-40",
        rate=0.40, is_band_ceiling=True,
        production_types=("feature_film", "tv_series", "creative_documentary"),
        min_qpe_usd=113_000.0,
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure (general case)",
                quote="The minimum spend in Malta must be EUR 100,000 with an overall "
                      "budget exceeding EUR 200,000 (MFC Cash Rebate Guidelines, Jan 2019, S.2.3)",
                kind="min_qpe_usd", threshold_usd=113_000.0,
            ),
            RateCondition(
                condition_id="mt-uplift-limb-a-malta-as-malta",
                description="Limb (a), +5%: Malta portrayed as Malta, or local "
                            "usage of facilities — Commissioner-discretionary, "
                            "no published objective points test for this limb",
                quote="Malta features as Malta or local usage of facilities [5%] "
                      "(MFC Cash Rebate Guidelines, Jan 2019, S.3.4; confirmed "
                      "current per Screen Malta Financial Incentives Guidelines "
                      "2024, S.3.4)",
                kind="discretionary_band",
            ),
            RateCondition(
                condition_id="mt-uplift-limb-b-local-resources",
                description="Limb (b), +5%: maximisation of local resources — "
                            "Annex 1 gives objective minimum local-crew "
                            "percentages by department (e.g. Production 80%, "
                            "Direction 60%, Locations & Unit 90%, Camera 50%, "
                            "Transport 90%) as EVIDENCE criteria, not a "
                            "self-executing points formula; final award still "
                            "requires Commissioner assessment and audit at "
                            "final submission",
                quote="Maximisation of local resources [5%] ... Annex 1 "
                      "(Screen Malta Financial Incentives Guidelines 2024, "
                      "S.3.4 and Annex 1)",
                kind="discretionary_band",
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MT_CITATION + " 40% ceiling requires the Commissioner to award both "
                 "independent 5% discretionary limbs on top of the 30% base — the "
                 "guaranteed floor is the 30% base tier. Per the Incentive/Optimizer "
                 "Core Closeout final rule resolution "
                 "(docs/validation/CODEX_FINAL_RULE_RESOLUTION.md §4.1): limb (b) has "
                 "objective department-level local-crew benchmarks (Annex 1) that "
                 "function as evidence, not an automatic-award formula — final "
                 "certificate percentage controls either way.",
        source_ref="MFC-Cash-Rebate-Guidelines-2019-01-official",
    ),
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-animation-25",
        rate=0.25, is_band_ceiling=False,
        production_types=("animation", "digital_animated_film"),
        min_qpe_usd=113_000.0,
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure (general case)",
                quote="The minimum spend in Malta must be EUR 100,000 with an overall "
                      "budget exceeding EUR 200,000 (MFC Cash Rebate Guidelines, Jan 2019, S.2.3)",
                kind="min_qpe_usd", threshold_usd=113_000.0,
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MT_CITATION + " Category B (Animation/VFX): 25% base on all eligible "
                 "expenditure (S.3.2.1) — a DIFFERENT, lower base rate than the general "
                 "Category A tier; scoped as its own record since production_types is "
                 "record-level, not tier-level.",
        source_ref="MFC-Cash-Rebate-Guidelines-2019-01-official",
    ),
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-animation-ceiling-40",
        rate=0.40, is_band_ceiling=True,
        production_types=("animation", "digital_animated_film"),
        min_qpe_usd=113_000.0,
        conditions=(
            RateCondition(
                condition_id="mt-uplifts-animation",
                description="Maximum rate requires Commissioner discretion on the "
                            "combined criteria, not a guaranteed entitlement",
                quote="The Commissioner has the discretion to award an additional 15% "
                      "based on the Maltese cultural elements and on the maximisation "
                      "of local resources. Maximum Rebate: 40% (MFC Cash Rebate "
                      "Guidelines, Jan 2019, S.3.2.1)",
                kind="discretionary_band",
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_MT_CITATION + " 40% ceiling for Animation/VFX requires the full 15% "
                 "Commissioner-discretionary uplift on top of the 25% base.",
        source_ref="MFC-Cash-Rebate-Guidelines-2019-01-official",
    ),
    # NOTE: 'Difficult Audiovisual Work' (up to 50%, MFC Cash Rebate Guidelines
    # Jan 2019 S.3.2.2/S.3.3) is DELIBERATELY NOT modeled as a RateRule tier.
    # It requires a MAXIMUM total budget of EUR 1,500,000 -- a ceiling
    # condition -- but RateRule/resolve_program_rate() only supports MINIMUM
    # thresholds (min_qpe_usd). Modeling it as a normal tier would make
    # resolve_program_rate() select it as the highest-rate match for ANY
    # Malta production above the EUR 50,000 floor, regardless of actual
    # budget size -- a genuine correctness bug caught during the account-
    # handoff repository consistency audit (2026-07-26) and deliberately
    # avoided rather than shipped. Disclosed as additional_facts only, in
    # both app.data.program_requirements (mt_mfc_rebate) and
    # jurisdiction_comparison.py's MALTA profile -- never priced.
)

_IE_CITATION = (
    "Section 481 Film Tax Credit (jurisdiction_comparison.py IRELAND "
    "profile, confidence_tier=PARSED — 'rates and cap confirmed from "
    "Finance Act; cultural test points system unverified'; authority: "
    "Revenue Commissioners Ireland, revenue.ie)."
)
IE_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="ie_section_481", tier_id="ie-flat-32",
        rate=0.32, is_band_ceiling=False,
        production_types=("feature_film",), min_qpe_usd=142_565.49,
        conditions=(
            RateCondition(
                condition_id="ie-min-spend",
                description="Minimum qualifying Irish expenditure",
                quote="min_spend_local=EUR 125,000 (jurisdiction_comparison.py "
                      "IRELAND profile, PARSED tier)",
                kind="min_qpe_usd", threshold_usd=142_565.49,
            ),
            RateCondition(
                condition_id="ie-cultural-test",
                description="Cultural test required (Irish Qualifying Test) — a "
                            "threshold eligibility gate, not a points contribution "
                            "to this rate; passing threshold/points system itself "
                            "unverified from primary source (disclosed data gap)",
                quote="Cultural test required (Irish Qualifying Test). ... cultural "
                      "test points system unverified. (jurisdiction_comparison.py "
                      "IRELAND profile notes, PARSED tier)",
                kind="cultural_test_required",  # falls into resolve_program_rate()'s
                # generic fact-dependent else-branch (any kind other than the three
                # explicitly dispatched ones) — satisfied=None, never silently assumed.
            ),
        ),
        confidence_tier="PARSED",
        citation=_IE_CITATION + " 32% flat refundable tax credit (not tiered — "
                 "base_rate == max_rate in the source profile). Cap: 80% of budget "
                 "or EUR 70,000,000 qualifying spend, whichever is lower — this cap "
                 "is on QUALIFYING SPEND, not on the rate itself, and is NOT enforced "
                 "by this rate-tier model (disclosed, not silently applied); see "
                 "program's data_gaps.",
        source_ref="jurisdiction_comparison.IRELAND",
    ),
)

_GR_CITATION = (
    "Greece Cash Rebate for International Productions. Rate (40%, flat, "
    "no cultural test) sourced via jurisdiction_comparison.py GREECE "
    "profile (Enterprise Greece / Greek Film Centre, enterprisegreece.gov.gr). "
    "Minimum-spend threshold and the 80% eligible-spend cap (see "
    "program_rate_rules.QPE_CAP_RULES['gr_cash_rebate']) updated per the "
    "Incentive/Optimizer Core Closeout final rule resolution "
    "(docs/validation/CODEX_FINAL_RULE_RESOLUTION.md §2), itself sourced to "
    "JMD 607434 (Government Gazette B' 87/14.01.2026, arts. 4-6) as amended "
    "by JMD 140524 (Gazette B' 2204/20.04.2026): fiction film/TV film floor "
    "is EUR 200,000 minimum eligible Greek spend AND EUR 400,000 minimum "
    "total production budget — both floors apply, neither substitutes for "
    "the other."
)
GR_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="gr_cash_rebate", tier_id="gr-flat-40",
        rate=0.40, is_band_ceiling=False,
        production_types=("feature_film",),
        # EUR 200,000 fiction-film floor, converted at the same implied
        # EUR/USD ratio (1.140524) already committed to by this program's
        # prior EUR 100,000 -> USD 114,052.40 figure — not a new/fabricated
        # rate, the program's own existing conversion basis reapplied to
        # the corrected threshold.
        min_qpe_usd=228_104.80,
        conditions=(
            RateCondition(
                condition_id="gr-min-spend",
                description="Minimum qualifying Greek expenditure (fiction film/TV film)",
                quote="Minimum eligible Greek spend EUR 200,000 for fiction film/TV "
                      "film (JMD 607434 art. 6 threshold table, as amended by JMD "
                      "140524)",
                kind="min_qpe_usd", threshold_usd=228_104.80,
            ),
        ),
        confidence_tier="VERIFIED",
        citation=_GR_CITATION,
        source_ref="JMD-607434-art-6-CODEX-final-resolution",
    ),
)


## ── Spain: Article 36.2 LIS foreign-production deduction ────────────────────
#
# Source: Ley 27/2014, de 27 de noviembre, del Impuesto sobre Sociedades
# (BOE-A-2014-12328), Artículo 36.2 — the deduction for foreign productions
# filming in Spain. Verbatim text confirmed from TWO independent legal-
# database reproductions of the consolidated statute (iberley.es and a
# web-search-corroborated summary of the same law), not a raw self-fetched
# BOE.es document — hence PARSED, not VERIFIED, matching this file's own
# tier discipline.
#
# CORRECTION OF A PRIOR DISCOVERY-TIER ERROR: an earlier pass (recorded in
# jurisdiction_comparison.py's ES profile, confidence_tier=DISCOVERY) also
# surfaced a contradicting 15% figure from a partial BOE preamble fetch —
# that figure was not the operative Article 36.2 rate (likely a pre-
# amendment or misattributed figure) and is superseded by the verbatim
# text below.
#
# REAL, STATUTE-QUOTED STRUCTURE (not a flat rate): "Del 30 por ciento
# respecto del primer millón de base de la deducción y del 25 por ciento
# sobre el exceso" — 30% on the first EUR 1,000,000 of the deduction base,
# 25% on any excess. CORRECTED (worldwide population phase, maximum-
# lawful-incentive review): previously modeled at a flat conservative 25%
# because RateRule had no way to represent a graduated bracket. That
# understated the real, confirmed 30% first-bracket benefit — not the
# "narrowest reusable" representation the project now requires. RateRule
# gained an optional `graduated_brackets` field
# (program_rate_rules.py, RateRule docstring) purely additive, every
# other program unaffected — and resolve_program_rate() now computes a
# real BLENDED effective rate (total credit / QPE) for Spain: for Little
# Utopia's ~$4.36M QPE this comes to ~26.3%, correctly between the flat
# 25% (understates) and flat 30% (overstates) figures.
#
# NOT MODELED — genuine disclosed gap, not a guess: the Canary Islands
# enhanced rate (widely reported at 50%/45% by secondary sources and by
# jurisdiction_comparison.py's own prior DISCOVERY-tier notes) does NOT
# appear anywhere in Article 36 — confirmed by requesting the complete,
# all-subsection text of Article 36 (36.1/36.2/36.3) and finding no
# Canary Islands reference. It must derive from Canary Islands' separate
# special economic/fiscal regime (Régimen Económico y Fiscal de
# Canarias), which has not been located or read. Recorded below as an
# UnverifiedRateClaim — never applied as a rule.
#
# Spend-category / QPE doctrine: Article 36.2 names only two enumerated
# cost categories for the deduction base — creative-personnel costs (with
# an EEA/Spain fiscal-residency condition) and technical-industry/
# supplier costs — and defers further qualifying-expense detail to an
# unretrieved Orden Ministerial ("Reglamentariamente se podrán establecer
# otros requisitos..."). This is NOT enough primary-source basis to
# classify a QualificationDoctrine (OPEN_DEFAULT_INCLUDE vs.
# CLOSED_POSITIVE_LIST would both be a guess without that order's text).
# Intentionally left unclassified in program_spend_rules.py — a disclosed
# gap, not a silent default, per that module's own documented behavior
# for an unclassified program_slug.

_ES_CITATION = (
    "Ley 27/2014, de 27 de noviembre, del Impuesto sobre Sociedades "
    "(BOE-A-2014-12328), Artículo 36.2 — deducción por producciones "
    "extranjeras. Verbatim: 'Del 30 por ciento respecto del primer "
    "millón de base de la deducción y del 25 por ciento sobre el "
    "exceso.' Min spend: 'los gastos realizados en territorio español "
    "sean, al menos, de 1 millón de euros ... en el supuesto de "
    "producciones de animación tales gastos serán, al menos, de "
    "200.000 euros.' Cap: 'El importe de esta deducción no podrá ser "
    "superior a 20 millones de euros, por cada producción realizada' "
    "(10 millones de euros por episodio para series). Registration: "
    "productores inscritos en el Registro Administrativo de Empresas "
    "Cinematográficas y Audiovisuales (ICAA)."
)
ES_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="es_tax_credit_foreign", tier_id="es-graduated-30-25",
        rate=0.25, is_band_ceiling=False,
        production_types=("feature_film",), min_qpe_usd=1_140_523.96,
        conditions=(
            RateCondition(
                condition_id="es-min-spend",
                description="Minimum qualifying Spanish expenditure (EUR "
                            "200,000 for animation — not modeled as a "
                            "separate production_type tier here)",
                quote="los gastos realizados en territorio español sean, "
                      "al menos, de 1 millón de euros (Art. 36.2 LIS)",
                kind="min_qpe_usd", threshold_usd=1_140_523.96,
            ),
            RateCondition(
                condition_id="es-bracket-blended",
                description="Statute rate is bracketed (30% first EUR 1M, "
                            "25% excess) — a real, confirmed graduated "
                            "structure, not a discretionary approval band. "
                            "resolve_program_rate() computes a genuine "
                            "blended effective rate from this bracket "
                            "(total credit / QPE), not a flat rate",
                quote="Del 30 por ciento respecto del primer millón de "
                      "base de la deducción y del 25 por ciento sobre "
                      "el exceso (Art. 36.2 LIS)",
                kind="graduated_bracket_applied",
            ),
        ),
        confidence_tier="PARSED",
        citation=_ES_CITATION,
        source_ref="BOE-A-2014-12328-Art36.2",
        graduated_brackets=((1_140_523.96, 0.30),),
    ),
)

ES_UNVERIFIED_CLAIMS: tuple[UnverifiedRateClaim, ...] = (
    UnverifiedRateClaim(
        program_slug="es_tax_credit_foreign",
        claim="Canary Islands enhanced rate of 50% (mainland 30%) / 45% "
              "(mainland 25% excess) applies to productions filming in "
              "the Canary Islands.",
        claimed_by="Secondary trade/production-services sources and this "
                   "project's own prior DISCOVERY-tier jurisdiction_"
                   "comparison.py notes; not found anywhere in Article 36 "
                   "(all subsections 36.1-36.3 requested and reviewed)",
        verification_status="NOT FOUND in Ley 27/2014 Article 36. Almost "
                            "certainly derives from the separate Canary "
                            "Islands Régimen Económico y Fiscal (REF) "
                            "special tax regime, which has not been "
                            "located or read. Requires that regime's "
                            "primary text before it can be treated as a "
                            "rule either way.",
    ),
)


## ── France: CNC TRIP (Tax Rebate for International Productions) ────────────
#
# Source: CNC (Centre national du cinéma et de l'image animée) official TRIP
# page, cnc.fr — fetched directly and quoted verbatim below. Per the
# reconciliation discipline in docs/architecture/CAPABILITY_LEDGER.md: the
# Alembic migration (0008_seed_marine_jurisdictions.py, later bulk-promoted
# to VERIFIED by 0038 on a weak "source URL confirmed" basis, per that
# migration's own docstring) was checked FIRST as a candidate lead — it had
# the base rate (30%) and min spend (EUR 250,000) right, but MISSED the real
# VFX-uplift band (40% when French VFX spend > EUR 2M) and the real EUR 30M
# cap entirely. This is the same lesson as Spain: a migration's own
# confidence-tier label is not a substitute for reading the actual source.
#
# Quoted from cnc.fr: "The TRIP amounts up to 30% (or 40%, if the French VFX
# expenses are more than EUR 2M) ... can total a maximum of EUR 30 million
# per project." Minimum spend: "EUR 250,000 or 50% of their world budgets in
# French expenditures" (the 50%-of-world-budget alternative threshold is not
# representable in this engine's single min_qpe_usd field — disclosed, not
# computed). Live action also requires "at least 5 days of shooting in
# France" (not modeled — no shooting-days fact exists in this engine).
# Cultural test: "must include elements related to the French culture,
# heritage, and territory" — the migration's claimed "2 of 6 French
# elements" points breakdown was NOT found in the fetched cnc.fr text and is
# NOT carried into this rule (unconfirmed, not asserted). Refundable:
# confirmed ("if the amount of the tax rebate exceeds the corporate income
# tax due for this year, the difference will be paid by the French State").

_FR_CITATION = (
    "CNC (Centre national du cinéma et de l'image animée), official TRIP "
    "page (cnc.fr), fetched directly. 'The TRIP amounts up to 30% (or 40%, "
    "if the French VFX expenses are more than EUR 2M) ... can total a "
    "maximum of EUR 30 million per project.' Min spend: 'EUR 250,000 or "
    "50% of their world budgets in French expenditures' (50%-of-budget "
    "alternative not modeled). Live action also requires >=5 shooting days "
    "in France (not modeled — no shooting-days fact exists in this "
    "engine). Refundable: 'the difference will be paid by the French "
    "State' if the rebate exceeds corporate income tax due."
)
FR_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="fr_trip", tier_id="fr-base-30",
        rate=0.30, is_band_ceiling=False,
        production_types=("feature_film",), min_qpe_usd=285_130.99,
        conditions=(
            RateCondition(
                condition_id="fr-min-spend",
                description="Minimum qualifying French expenditure (or 50% "
                            "of world budget, whichever the production "
                            "meets — the 50%-of-budget alternative is not "
                            "computed by this engine)",
                quote="EUR 250,000 or 50% of their world budgets in French "
                      "expenditures (cnc.fr, TRIP page)",
                kind="min_qpe_usd", threshold_usd=285_130.99,
            ),
            RateCondition(
                condition_id="fr-cultural-test",
                description="Cultural test required (French/European "
                            "culture, heritage, territory elements) — "
                            "exact points-based criteria not confirmed "
                            "from the primary source fetched; a migration "
                            "claim of '2 of 6 elements' was NOT found in "
                            "the cnc.fr text and is not asserted here",
                quote="must include elements related to the French "
                      "culture, heritage, and territory (cnc.fr, TRIP page)",
                kind="cultural_test_required",
            ),
        ),
        confidence_tier="PARSED",
        citation=_FR_CITATION,
        source_ref="cnc.fr-TRIP-page",
    ),
    RateRule(
        program_slug="fr_trip", tier_id="fr-vfx-ceiling-40",
        rate=0.40, is_band_ceiling=True,
        production_types=("feature_film",), min_qpe_usd=285_130.99,
        conditions=(
            RateCondition(
                condition_id="fr-min-spend",
                description="Minimum qualifying French expenditure",
                quote="EUR 250,000 or 50% of their world budgets in French "
                      "expenditures (cnc.fr, TRIP page)",
                kind="min_qpe_usd", threshold_usd=285_130.99,
            ),
            RateCondition(
                condition_id="fr-vfx-threshold",
                description="40% rate requires French VFX expenditure "
                            "exceeding EUR 2,000,000 — a real, confirmed "
                            "threshold (not a discretionary approval band "
                            "like MU's 'up to 40%'), but this engine has "
                            "no fact tracking VFX-specific spend split "
                            "from total QPE, so eligibility for this tier "
                            "cannot be pre-evaluated and is modeled as the "
                            "ceiling",
                quote="40%, if the French VFX expenses are more than EUR "
                      "2M (cnc.fr, TRIP page)",
                kind="discretionary_band",
            ),
        ),
        confidence_tier="PARSED",
        citation=_FR_CITATION + " The 40% tier is a real, statute-confirmed "
                 "threshold (VFX spend > EUR 2M), not discretionary "
                 "approval — modeled as the ceiling because this engine "
                 "cannot yet evaluate VFX-specific spend against total QPE; "
                 "the guaranteed floor is the base 30% tier.",
        source_ref="cnc.fr-TRIP-page",
    ),
)


_RULES_BY_PROGRAM: dict[str, tuple[RateRule, ...]] = {}
for _r in MU_RATE_RULES + MT_RATE_RULES + IE_RATE_RULES + GR_RATE_RULES + ES_RATE_RULES + FR_RATE_RULES:
    _RULES_BY_PROGRAM.setdefault(_r.program_slug, ())
    _RULES_BY_PROGRAM[_r.program_slug] = _RULES_BY_PROGRAM[_r.program_slug] + (_r,)

_UNVERIFIED_BY_PROGRAM: dict[str, tuple[UnverifiedRateClaim, ...]] = {
    "mu_edb_incentive": MU_UNVERIFIED_CLAIMS,
    "es_tax_credit_foreign": ES_UNVERIFIED_CLAIMS,
}
_BUDGET_RATES_BY_PROGRAM: dict[str, tuple[BudgetEvidencedRate, ...]] = {
    "mu_edb_incentive": MU_BUDGET_EVIDENCED_RATES,
}


def get_rate_rules(program_slug: str) -> tuple[RateRule, ...]:
    return _RULES_BY_PROGRAM.get(program_slug, ())


# ── QPE eligible-spend caps (Incentive/Optimizer Core Closeout) ─────────────
#
# A cap on ELIGIBLE SPEND (the QPE base itself), distinct from a rate cap
# or an annual program cap. Applied to a segment's own qpe_usd BEFORE rate
# resolution, so a capped QPE also correctly affects which rate tier's
# min_qpe_usd threshold is met. cap_base:
#   "segment_allocated"      — cap is a % of THIS segment's own allocated
#                               total (a proxy for "total core expenditure"
#                               on a full-relocation structure, where the
#                               segment IS effectively the whole production).
#   "total_worldwide_budget" — cap is a % of the STRUCTURE's entire gross
#                               budget, regardless of how much of it is
#                               allocated to this segment.
@dataclass(frozen=True)
class QpeCapRule:
    program_slug: str
    cap_pct: float
    cap_base: str  # "segment_allocated" | "total_worldwide_budget"
    description: str
    quote: str
    source_ref: str


_GB_CAP_QUOTE = (
    "'AVEC is available on qualifying UK production expenditure, which is "
    "the lower of either 80% of total core expenditure or the actual UK "
    "core expenditure incurred' (bfi.org.uk, corroborated by HMRC "
    "CREC061300/CREC060100: 'the lesser of UK relevant global expenditure "
    "and 80% of total relevant global expenditure/core expenditure')."
)
_GR_CAP_QUOTE = (
    "'implemented within the Greek territory and not exceeding eighty "
    "percent (80%) of the total production cost for the entirety of the "
    "audiovisual production work' — the cap base is the production's total "
    "worldwide cost, not Greek spend alone (JMD 607434, Gazette B' 87/"
    "14.01.2026, arts. 4-5, as amended by JMD 140524)."
)

QPE_CAP_RULES: dict[str, QpeCapRule] = {
    "uk_avec": QpeCapRule(
        program_slug="uk_avec", cap_pct=0.80, cap_base="segment_allocated",
        description="Ordinary AVEC qualifying expenditure is capped at the "
                     "lower of actual UK core expenditure or 80% of total "
                     "core expenditure.",
        quote=_GB_CAP_QUOTE, source_ref="HMRC-CREC061300-CREC060100",
    ),
    "gr_cash_rebate": QpeCapRule(
        program_slug="gr_cash_rebate", cap_pct=0.80, cap_base="total_worldwide_budget",
        description="Eligible Greek production expenditure is capped at 80% "
                     "of the production's total (worldwide) production cost.",
        quote=_GR_CAP_QUOTE, source_ref="JMD-607434-arts-4-5",
    ),
}


def get_qpe_cap(program_slug: str) -> QpeCapRule | None:
    return QPE_CAP_RULES.get(program_slug)


def register_rate_rules(rules: tuple[RateRule, ...]) -> None:
    """Registration hook for executable_jurisdiction_registry.py-derived
    RateRule tuples (worldwide jurisdiction population phase) — lets a
    new jurisdiction's rules be built from ONE canonical DoctrineRecord
    (see executable_jurisdiction_registry.py) without a circular import:
    that module imports RateRule/RateCondition FROM this file, so this
    file cannot import it back at module scope. Per-jurisdiction record
    modules call this function instead; see program_rate_rules_worldwide.py."""
    for rule in rules:
        _RULES_BY_PROGRAM.setdefault(rule.program_slug, ())
        _RULES_BY_PROGRAM[rule.program_slug] = _RULES_BY_PROGRAM[rule.program_slug] + (rule,)


# Bottom-of-file import (after register_rate_rules/_RULES_BY_PROGRAM exist)
# — avoids the circular import that would result from importing this at
# the top: program_rate_rules_worldwide.py itself imports RateRule/
# RateCondition/register_rate_rules FROM this module.
from app.data import program_rate_rules_worldwide  # noqa: F401,E402


def _blended_effective_rate(tier: RateRule, qpe_usd: float | None) -> float:
    """Real blended effective rate (total credit / QPE) for a statute-
    confirmed graduated/bracketed tier — e.g. Spain Art. 36.2's 30% first
    EUR 1M / 25% excess. This is the maximum-lawful-incentive
    representation: NOT the flat marginal/excess rate (understates the
    real benefit for a production of any size) and NOT the flat top-
    bracket rate (overstates it for spend beyond the first bracket).
    Falls back to tier.rate unchanged when graduated_brackets is None —
    every existing non-graduated program is unaffected."""
    if not tier.graduated_brackets or qpe_usd is None or qpe_usd <= 0:
        return tier.rate
    total_credit = 0.0
    prev_ceiling = 0.0
    for ceiling, bracket_rate in tier.graduated_brackets:
        span = max(0.0, min(qpe_usd, ceiling) - prev_ceiling)
        total_credit += span * bracket_rate
        prev_ceiling = ceiling
        if qpe_usd <= ceiling:
            break
    else:
        if qpe_usd > prev_ceiling:
            total_credit += (qpe_usd - prev_ceiling) * tier.rate
    return total_credit / qpe_usd


def resolve_program_rate(
    program_slug: str,
    production_type: str,
    qpe_usd: float | None,
) -> RateResolution | None:
    """
    Resolve the modeled rate for one production from database/statutory
    rules ONLY (Rules 1-3). Returns None when the program has no rate
    rules (absence, not an error — callers must not invent a rate).

    Tier selection: the highest-rate tier whose production_types include
    this production and whose min_qpe_usd is met by qpe_usd. A None
    qpe_usd fails every thresholded tier (unknown is not satisfied).
    Budget-evidenced rates are NEVER considered (Rule 2); any that exist
    for the program are reported as conflicts when they differ from the
    resolved rate (Rule 5).
    """
    rules = get_rate_rules(program_slug)
    if not rules:
        return None

    eligible: list[RateRule] = []
    for rule in sorted(rules, key=lambda r: -r.rate):
        if production_type not in rule.production_types:
            continue
        if rule.min_qpe_usd is not None and (qpe_usd is None or qpe_usd < rule.min_qpe_usd):
            continue
        eligible.append(rule)

    if not eligible:
        return None

    tier = eligible[0]
    floor_candidates = [r for r in eligible if not r.is_band_ceiling]
    floor_rate = floor_candidates[0].rate if floor_candidates else tier.rate
    effective_rate = _blended_effective_rate(tier, qpe_usd)

    evaluations: list[ConditionEvaluation] = []
    for cond in tier.conditions:
        if cond.kind == "production_type":
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote,
                satisfied=True,
                note=f"Production type '{production_type}' is within the tier's scope.",
            ))
        elif cond.kind == "min_qpe_usd":
            met = qpe_usd is not None and cond.threshold_usd is not None and qpe_usd >= cond.threshold_usd
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote,
                satisfied=met if cond.threshold_usd is not None else True,
                note=(f"QPE ${qpe_usd:,.0f} vs threshold ${cond.threshold_usd:,.0f}"
                      if qpe_usd is not None and cond.threshold_usd is not None
                      else "Threshold condition evaluated at tier selection."),
            ))
        elif cond.kind == "discretionary_band":
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote,
                satisfied=None,
                note="Cannot be pre-satisfied: the awarded rate within the 'up to' "
                     "band is set by the authority at approval. The engine models "
                     "the ceiling; the guaranteed floor is the non-band tier.",
            ))
        elif cond.kind == "graduated_bracket_applied":
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote,
                satisfied=True,
                note=(f"Statute-confirmed bracket, not discretionary — blended to "
                      f"a real effective rate of {effective_rate:.2%} for QPE "
                      f"${qpe_usd:,.0f}." if qpe_usd is not None
                      else "Bracket structure confirmed; blended rate requires a "
                           "known QPE to compute."),
            ))
        else:  # no_sponsorship_in_qpe and any future fact-dependent kinds
            evaluations.append(ConditionEvaluation(
                cond.condition_id, cond.description, cond.quote,
                satisfied=None,
                note="Production fact not yet evidenced either way — no sponsorship/"
                     "financial assistance is recorded in the budget, but absence "
                     "of a record is not confirmation.",
            ))

    conflicts: list[RateConflict] = []
    for ber in _BUDGET_RATES_BY_PROGRAM.get(program_slug, ()):
        if abs(ber.rate - tier.rate) > 1e-9:
            conflicts.append(RateConflict(
                source_kind="budget_document",
                claimed_rate=ber.rate,
                database_rate=tier.rate,
                resolution="Database/statutory rate used; budget-document figure "
                           "ignored per permanent Rules 1, 2 and 5.",
                detail=ber.observed_in,
            ))

    band_note = (
        " The source says 'up to' this rate — it is a modeling ceiling subject to "
        f"EDB approval; the guaranteed floor tier is {floor_rate:.0%}."
        if tier.is_band_ceiling else ""
    )
    bracket_note = (
        f" Statute-confirmed marginal/bracketed rate: blended to a real effective "
        f"rate of {effective_rate:.2%} for this QPE (not the flat top-bracket "
        f"marginal rate) — see RateRule.graduated_brackets."
        if tier.graduated_brackets else ""
    )
    return RateResolution(
        program_slug=program_slug,
        modeled_rate=effective_rate,
        floor_rate=floor_rate,
        is_band_ceiling=tier.is_band_ceiling,
        tier_id=tier.tier_id,
        basis=f"{tier.citation}{band_note}{bracket_note}",
        conditions_evaluated=tuple(evaluations),
        unverified_claims=_UNVERIFIED_BY_PROGRAM.get(program_slug, ()),
        conflicts=tuple(conflicts),
    )
