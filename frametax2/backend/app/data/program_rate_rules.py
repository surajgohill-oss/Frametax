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
        production_types=("feature_film", "television_drama_series"),
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
        verification_status="NOT FOUND in EDB Submission Procedures (31 Jan 2020) "
                            "or MCCI guidance. Requires EDB written confirmation "
                            "before it can be treated as a rule either way.",
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
    "Malta Film Commission Cash Rebate (jurisdiction_comparison.py MALTA "
    "profile, confidence_tier=PARSED; authority: Malta Film Commission, "
    "maltafilmcommission.com)."
)
MT_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-base-25",
        rate=0.25, is_band_ceiling=False,
        production_types=("feature_film",), min_qpe_usd=57_026.20,
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure",
                quote="min_spend_local=EUR 50,000 (jurisdiction_comparison.py MALTA "
                      "profile, PARSED tier)",
                kind="min_qpe_usd", threshold_usd=57_026.20,
            ),
        ),
        confidence_tier="PARSED",
        citation=_MT_CITATION + " Base 25% on all qualifying Malta expenditure for "
                 "non-Maltese productions; no cultural test required for foreign productions.",
        source_ref="jurisdiction_comparison.MALTA",
    ),
    RateRule(
        program_slug="mt_mfc_rebate", tier_id="mt-ceiling-40",
        rate=0.40, is_band_ceiling=True,
        production_types=("feature_film",), min_qpe_usd=57_026.20,
        conditions=(
            RateCondition(
                condition_id="mt-min-spend",
                description="Minimum qualifying Malta expenditure",
                quote="min_spend_local=EUR 50,000 (jurisdiction_comparison.py MALTA "
                      "profile, PARSED tier)",
                kind="min_qpe_usd", threshold_usd=57_026.20,
            ),
            RateCondition(
                condition_id="mt-uplifts",
                description="Maximum rate requires stacking discretionary uplifts, "
                            "not a guaranteed entitlement",
                quote="Uplifts: +3% MFC cultural contribution, +3% VFX/post in Malta, "
                      "+7% small-budget (<EUR 3M). Maximum with all uplifts: ~40%. "
                      "(jurisdiction_comparison.py MALTA profile notes, PARSED tier)",
                kind="discretionary_band",
            ),
        ),
        confidence_tier="PARSED",
        citation=_MT_CITATION + " 40% ceiling requires stacking all three uplifts "
                 "(cultural contribution, VFX/post-in-Malta, small-budget) — the "
                 "guaranteed floor is the base 25% tier.",
        source_ref="jurisdiction_comparison.MALTA",
    ),
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
    "Greece Cash Rebate for International Productions (jurisdiction_"
    "comparison.py GREECE profile, confidence_tier=PARSED; authority: "
    "Enterprise Greece / Greek Film Centre, enterprisegreece.gov.gr)."
)
GR_RATE_RULES: tuple[RateRule, ...] = (
    RateRule(
        program_slug="gr_cash_rebate", tier_id="gr-flat-40",
        rate=0.40, is_band_ceiling=False,
        production_types=("feature_film",), min_qpe_usd=114_052.40,
        conditions=(
            RateCondition(
                condition_id="gr-min-spend",
                description="Minimum qualifying Greek expenditure",
                quote="min_spend_local=EUR 100,000 (jurisdiction_comparison.py "
                      "GREECE profile, PARSED tier)",
                kind="min_qpe_usd", threshold_usd=114_052.40,
            ),
        ),
        confidence_tier="PARSED",
        citation=_GR_CITATION + " Flat 40% rebate (highest headline rate among Tier "
                 "1 comparators); no cultural test required. Annual program "
                 "allocation exists but the specific cap is not publicly confirmed "
                 "(disclosed data gap, not enforced here) — budget oversubscription "
                 "is a real scheduling risk per the source profile's own notes.",
        source_ref="jurisdiction_comparison.GREECE",
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
