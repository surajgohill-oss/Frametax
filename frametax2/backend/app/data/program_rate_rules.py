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
    modeling ceiling, not a guaranteed entitlement."""
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


_RULES_BY_PROGRAM: dict[str, tuple[RateRule, ...]] = {}
for _r in MU_RATE_RULES + MT_RATE_RULES + IE_RATE_RULES + GR_RATE_RULES:
    _RULES_BY_PROGRAM.setdefault(_r.program_slug, ())
    _RULES_BY_PROGRAM[_r.program_slug] = _RULES_BY_PROGRAM[_r.program_slug] + (_r,)

_UNVERIFIED_BY_PROGRAM: dict[str, tuple[UnverifiedRateClaim, ...]] = {
    "mu_edb_incentive": MU_UNVERIFIED_CLAIMS,
}
_BUDGET_RATES_BY_PROGRAM: dict[str, tuple[BudgetEvidencedRate, ...]] = {
    "mu_edb_incentive": MU_BUDGET_EVIDENCED_RATES,
}


def get_rate_rules(program_slug: str) -> tuple[RateRule, ...]:
    return _RULES_BY_PROGRAM.get(program_slug, ())


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
    return RateResolution(
        program_slug=program_slug,
        modeled_rate=tier.rate,
        floor_rate=floor_rate,
        is_band_ceiling=tier.is_band_ceiling,
        tier_id=tier.tier_id,
        basis=f"{tier.citation}{band_note}",
        conditions_evaluated=tuple(evaluations),
        unverified_claims=_UNVERIFIED_BY_PROGRAM.get(program_slug, ()),
        conflicts=tuple(conflicts),
    )
