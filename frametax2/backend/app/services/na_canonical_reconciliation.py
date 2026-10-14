"""NORTH AMERICA CANONICAL RECONCILIATION (NA-RECONCILIATION-12, 2026-10-13).

A READ-ONLY derivation over the existing canonical owners; it is not a registry, prices nothing and stores nothing. It freezes the live United States / Canada / Mexico program universe
from the canonical identity layer and the rate registry, deduplicates aliases, and accounts for every member with exactly one finding class and a terminal disposition. Terminal accounting
is NOT verified calculation acceptance: a row can be terminal while its calculation-driving proposition stays OPEN (the ``terminal_disposition`` column says which).

Universe layers (a program appears once, aliases are listed on its row and are never rows):
  RATE_BEARING     an NA program with a RateRule in ``program_rate_rules`` (jurisdiction from its DoctrineRecord)
  COVERAGE_ONLY    an NA canonical identity with no RateRule (authority coverage registry state: selective, non-economic, unpriceable, ...)
  STACK_SPELLING   an NA stacking-registry spelling carrying named pair rules that is neither a canonical identity nor a known alias (rules retained, program not promoted)
  CATALOG_ENTRY    a ``global_inventory`` catalog row with an NA jurisdiction code, linked to the canonical identity (or identities) it describes
  PROPOSITION      one unresolved calculation-driving proposition (project fact, unruled stacking pair, missing profile, provenance, authority conflict, ...)

The finding classes are the project's ten: see ``CLASSES``. A repaired defect keeps the class of the defect it was; a clean program is CANONICAL_AND_CONSUMED.

Terminal vocabulary (no row is labelled CLOSED while a material obligation remains): OPEN_<class> (an unresolved calculation proposition); PRICED_AUTHORITY_DIMENSIONS_OPEN / PRICED_REPAIRED_AUTHORITY_DIMENSIONS_OPEN (the program prices through the canonical path and
its repaired defects hold, but the publication contract's material dimensions are still unresolved); PRICED_REPAIRED / AUTHORITY_COMPLETE_CONSUMED (nothing open); NOT_PRICED_BY_DESIGN (a coverage-only selective, non-economic, superseded or duplicate
identity: not an executable program); LINKED_TO_CANONICAL_PROGRAM (a catalog row resolved to its identity: the link is accounted, the program's own state is on its row); REPAIRED (a repaired proposition); RETIRED_SUPERSEDED.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

AS_OF = "2026-10-13"
RECON_VERSION = "NA-RECONCILIATION-13"

C_CONSUMED = "CANONICAL_AND_CONSUMED"
C_DISCONNECTED = "EXISTS_BUT_DISCONNECTED"
C_DATA_MISSING = "CANONICAL_DATA_MISSING"
C_CAPABILITY = "OPTIMIZER_CAPABILITY_MISSING"
C_PROVENANCE = "PROVENANCE_INCOMPLETE_EXISTING_RECORD"
C_FACT = "PROJECT_FACT_REQUIRED"
C_CONFLICT = "GENUINE_AUTHORITY_CONFLICT"
C_STALE = "STALE_OUTPUT_REQUIRES_AUTHORIZED_REEVALUATION"
C_SUPERSEDED = "SUPERSEDED_AUDIT_CLAIM"
C_DEFECT = "IMPLEMENTATION_DEFECT"
CLASSES = (C_CONSUMED, C_DISCONNECTED, C_DATA_MISSING, C_CAPABILITY, C_PROVENANCE, C_FACT, C_CONFLICT, C_STALE, C_SUPERSEDED, C_DEFECT)

#: open-finding severity for the single class a PROGRAM row carries (a program with several findings has one PROPOSITION row per finding)
_SEVERITY = (C_DEFECT, C_DISCONNECTED, C_CONFLICT, C_CAPABILITY, C_DATA_MISSING, C_PROVENANCE, C_FACT, C_STALE, C_SUPERSEDED, C_CONSUMED)

LAYER_RATE, LAYER_COVERAGE, LAYER_STACK, LAYER_CATALOG, LAYER_PROPOSITION = "RATE_BEARING", "COVERAGE_ONLY", "STACK_SPELLING", "CATALOG_ENTRY", "PROPOSITION"

_NA_TEXT = re.compile(r"^(united states|canada|mexico)\b", re.I)

# ── repairs recorded against rows (the class a repaired defect had; commit/file/test are documentary pointers to the persisted change) ─────────────────────────────────────────────────
#: slug -> list of (class, what was wrong, commit-or-file, focused test)
REPAIRS: dict[str, list[tuple[str, str, str, str]]] = {
    "us_az_motion_picture_production": [
        (C_DEFECT, "structured primary provenance attached 2026-10-12 but the coverage residual row was not deleted, so the served result kept the incomplete-provenance warning and the AUTHORITY_UNRESOLVED downgrade",
         "authority_coverage_registry.py 1.12.0 (NA-RECONCILIATION-11)", "tests/test_na_canonical_reconciliation.py"),
        (C_DEFECT, "22.5% and 25% band ceilings carried no unresolved condition", "program_rate_rules_worldwide.py (2a98e22c)", "tests/test_us_ca_mx_scope_integrity_controls.py")],
    "us_co_film_incentive": [
        (C_DEFECT, "stale coverage residual row (as AZ); mirror-only authority replaced by the official C.R.S. 2024 text; USD 1,000,000 per-payee wage cap not applied",
         "authority_coverage_registry.py 1.12.0; per_payee_limits.py (2a98e22c)", "tests/test_na_authority_closure_controls.py")],
    "us_hi_film_digital_media_credit": [
        (C_DEFECT, "stale coverage residual row (as AZ)", "authority_coverage_registry.py 1.12.0 (NA-RECONCILIATION-11)", "tests/test_na_canonical_reconciliation.py")],
    "ca_bc_dave": [(C_DISCONNECTED, "rate-bearing but absent from the canonical identity layer (no identity, no consolidation view)", "canonical_program_identity.py (NA-RECONCILIATION-11)", "tests/test_na_canonical_reconciliation.py")],
    "ca_federal_cptc": [
        (C_DISCONNECTED, "rate-bearing but absent from the canonical identity layer", "canonical_program_identity.py (NA-RECONCILIATION-11)", "tests/test_na_canonical_reconciliation.py"),
        (C_DEFECT, "claim conditions were not clearable producer facts and stack legs lost them (CPTC + Manitoba served CONFIRMED); cost cap ignored an undeployed contingency",
         "rate rules, canonical_evaluation.py, allocation_pricing.py (2a98e22c)", "tests/test_cptc_net_cost_contingency_controls.py")],
    "on_ofttc": [(C_DISCONNECTED, "rate-bearing but absent from the canonical identity layer", "canonical_program_identity.py (NA-RECONCILIATION-11)", "tests/test_na_canonical_reconciliation.py")],
    "ontario_computer_animation_and_special_effects_tax_credit_ocase": [
        (C_DISCONNECTED, "rate-bearing but absent from the canonical identity layer", "canonical_program_identity.py (NA-RECONCILIATION-11)", "tests/test_na_canonical_reconciliation.py"),
        (C_DEFECT, "claim conditions not clearable producer facts; federal pair rules absent", "rate rules, stacking_rules.py 1.8.0, migration 0084 (60c3a3fa, 2a98e22c)", "tests/test_na_authority_closure_controls.py")],
    "us_ny_post_production_credit": [
        (C_DISCONNECTED, "rate-bearing but absent from the canonical identity layer, and a second blocked identity (proposed_united_states_new_york_film_tax_credit_post_production) described the same program",
         "canonical_program_identity.py; authority_coverage_registry.py binding (NA-RECONCILIATION-11)", "tests/test_na_canonical_reconciliation.py")],
    "ca_federal_pstc": [(C_DEFECT, "no provincial labour-share netting or BC/QC/NL/OCASE pair rules", "canonical_stack_bridge.py, stacking_rules.py 1.8.0-1.9.0, migrations 0084-0085 (60c3a3fa, 2a98e22c)", "tests/test_canonical_stack_bridge.py")],
    "ca_bc_pstc": [(C_DEFECT, "federal PSTC pair rule absent", "stacking_rules.py 1.8.0, migration 0084 (60c3a3fa)", "tests/test_canonical_stack_bridge.py")],
    "ca_qc_pstc": [(C_DEFECT, "federal PSTC pair rule and apportionment disclosure absent", "stacking_rules.py 1.8.0, migration 0084 (60c3a3fa)", "tests/test_canonical_stack_bridge.py")],
    "ca_mb_film_video_credit": [(C_PROVENANCE, "no structured provenance (secondary citation only)", "program_rate_rules_worldwide.py, authority_coverage_registry.py 1.11.0 (2a98e22c)", "tests/test_na_authority_closure_controls.py")],
    "ca_nl_all_spend_credit": [(C_DATA_MISSING, "regulation text unretrieved; federal pair rules, CAD cap and clearable Part I fact absent", "NL Regulation 31/23 persisted; stacking_rules.py 1.9.0; migration 0085; IncentiveValueCapRule (2a98e22c)", "tests/test_na_authority_closure_controls.py")],
    "us_pa_film_production_credit": [(C_DATA_MISSING, "USD 15,000,000 principal-actor cap not modeled (and mis-recorded as per-person)", "per_payee_limits.AGGREGATE_CATEGORY_CAPS (2a98e22c)", "tests/test_na_authority_closure_controls.py")],
    "ca_film_30": [(C_CONSUMED, "prospective planning basis not dated; historical Program 3.0 letter not labelled reference", "allocation_pricing.CALIFORNIA_REGIME_NOTE (2a98e22c)", "tests/test_na_authority_closure_controls.py")],
    "on_opstc": [(C_DEFECT, "25% Ontario-labour gate was an unclearable AUTHORITY_UNRESOLVED condition", "rate rules + program-facts key (2a98e22c)", "tests/test_na_authority_closure_controls.py")],
}

_R12 = "stacking_rules.py 1.10.0, canonical_stack_bridge.py, migration 0086 (NA-RECONCILIATION-12)"
_T12 = "tests/test_na_unruled_stack_pairs_controls.py"
_R12B = "program_rate_rules_worldwide.py, program_rate_rules.py, authority_coverage_registry.py 1.13.0-1.14.0, program_requirements.py (NA-RECONCILIATION-12, second pass)"
REPAIRS.setdefault("ca_nb_film_tax_credit", []).append((C_CONFLICT, "doctrine recorded the 2017-18 THC incentive (25%/30%, CAD 800,000) while the live program is the LIFT 2026/27 grant (up to 25%, bonuses to 35%, company cap CAD 2,000,000); resolved from the LIFT guidelines PDF", _R12B, "tests/test_us_ca_mx_scope_integrity_controls.py"))
REPAIRS.setdefault("ca_nb_film_tax_credit", []).append((C_DATA_MISSING, "no requirements profile", _R12B, "tests/test_na_canonical_reconciliation.py"))
REPAIRS.setdefault("ca_ns_production_incentive_fund", []).append((C_CONFLICT, "doctrine priced 25% of LABOUR from one secondary source; the primary CCTH guidelines price all Eligible Nova Scotia Costs (Stream II 25%); rewritten, CAD 10,000,000 cap rule added, labour-basis control restated, profile CURRENT", _R12B, "tests/test_canada_rate_rules_controls.py"))
REPAIRS.setdefault("ca_sk_creative_saskatchewan_grant", []).append((C_PROVENANCE, "no structured provenance although the 2026/27 guidelines were read; attached as the knowledge axis only (economic axis stays DISPLAY_ONLY_ZERO_GUARANTEED); CAD 5,000,000 par annual_cap_usd replaced by a native cap rule", _R12B, "tests/test_us_ca_mx_scope_integrity_controls.py"))
for _slug, _what in (
        ("ca_bc_film_tv_tax_credit", "'Film Incentive BC' was a coverage-only handoff defect (mis-typed as a direct grant); it is the BC film and television tax credit (ITA (BC) s.80), now rate-bearing with its pairs (mutually exclusive with the BC PSTC by s.83.1, allowed with DAVE, spend_reduction with the CPTC, conditional with the federal PSTC)"),
        ("us_co_film_income_tax_credit", "the separate Colorado income tax credit (39-22-559 as amended by HB 24-1358) had no record; the exclusion against the rebate (24-48.5-116(6)) is now a same-cost pair rule"),
        ("us_oh_motion_picture_tax_credit", "coverage-only: no rate record although ORC 122.85 states the rate, base, threshold and pool"),
        ("us_wv_film_production_tax_credit", "coverage-only: no rate record although the official page states 27% + 4%"),
        ("us_nj_garden_state_film_credit", "coverage-only: no rate record although the Division of Taxation states 35% / 30%"),
        ("us_mo_motion_media_production_tax_credit", "coverage-only: no rate record although the official pages state 20% to 42%"),
        ("us_ar_digital_motion_picture_incentive", "coverage-only: no rate record although the AEDC page states 25% / 30%"),
        ("us_mt_media_act_tax_credit", "coverage-only: no rate record although MCA 15-31-1007 states 20%"),
        ("us_ny_empire_state_independent_film_credit", "coverage-only: no rate record although Tax Law 24-D states 30%")):
    REPAIRS.setdefault(_slug, []).append((C_DISCONNECTED, _what, _R12B, "tests/test_na_canonical_reconciliation.py"))

for _slug, _what in (
        ("ca_ab_fttc", "no named pair rule with the federal CPTC or PSTC (UNRESOLVED_NO_AUTHORITY blocked the stack)"),
        ("ca_nb_film_tax_credit", "no named pair rule with the federal CPTC or PSTC"),
        ("ca_ns_production_incentive_fund", "no named pair rule with the federal CPTC or PSTC"),
        ("ca_sk_creative_saskatchewan_grant", "no named pair rule with the federal PSTC"),
        ("ca_bc_dave", "no named pair rule with the federal PSTC (spend_reduction) or CPTC (conditional, no primary text)")):
    REPAIRS.setdefault(_slug, []).append((C_DEFECT, _what, _R12, _T12))
REPAIRS["on_ofttc"].append((C_DEFECT, "no named pair rule with the federal PSTC (conditional: no primary text)", _R12, _T12))
REPAIRS["ca_federal_cptc"].append((C_DEFECT, "no named pair rule with Alberta, New Brunswick and Nova Scotia (spend_reduction) or BC DAVE (conditional)", _R12, _T12))
REPAIRS["ca_federal_pstc"].append((C_DEFECT, "no named pair rule with Alberta, DAVE, New Brunswick, Nova Scotia, Saskatchewan (spend_reduction) or OFTTC (conditional)", _R12, _T12))
REPAIRS.setdefault("ca_ns_production_incentive_fund", []).append((C_DATA_MISSING, "no requirements profile although the primary guidelines (April 2024) were retrievable", "program_requirements.py profile, status UNCERTAIN (NA-RECONCILIATION-12)", "tests/test_na_canonical_reconciliation.py"))
REPAIRS.setdefault("ca_sk_creative_saskatchewan_grant", []).append((C_DATA_MISSING, "no requirements profile although the 2026/27 guidelines were retrievable", "program_requirements.py profile (NA-RECONCILIATION-12)", "tests/test_na_canonical_reconciliation.py"))

_R13 = "stacking_rules.py 1.15.0, structural_prerequisites.py, canonical_stack_bridge.py, program_rate_rules_worldwide.py, program_requirements.py, program_rate_rules.py, per_payee_limits.py, authority_coverage_registry.py 1.16.0, migration 0089 (NA-RECONCILIATION-13)"
_T13 = "tests/test_na_calculation_closure_controls.py"
for _slug, _cls, _what in (
        ("ca_bc_dave", C_CAPABILITY, "the BC-credit dependency was a blocking 'conditional' with no model: DAVE is now claimable only with its host (s.80 film and television credit, or the s.82.1 services credit), derived from the structure; DAVE with the CPTC is a spend_reduction (no text bars it; DAVE is provincial assistance lowering the CPTC cost cap); rate record rebuilt from ITA (BC) s.81.2 and B.C. Reg. 4/99 ss.10, 10.1, 13, 15 (11% + 5% prescribed from October 1, 2016 = 16%)"),
        ("on_ofttc", C_DATA_MISSING, "OFTTC with the federal PSTC was a blocking 'conditional': O. Reg. 37/09 s.29(4) excludes ITA 125.5 assistance from OFTTC 'relevant assistance' and Reg. 9300 gives the accredited production no Canadian-content test, so no text bars it; the OFTTC is a labour credit that nets the PSTC in full (verified netting)"),
        ("ca_bc_film_tv_tax_credit", C_DATA_MISSING, "the BC film and television credit with the federal PSTC was a blocking 'conditional': ITA (BC) s.79(1) excludes the federal credits from BC assistance and s.80 states no PSTC bar; spend_reduction, verified netting. The regional, distant-location, training and scriptwriting formulas and the s.85(4) 36-month filing limit are now recorded"),
        ("us_mo_motion_media_production_tax_credit", C_DATA_MISSING, "RSMo 135.750 read: the uplift schedule (four 5-point increases and 10% of the base in a second-to-fourth-class county, to 42%), non-refundability, the 2029 sunset, the USD 8 million film and series pools, the apprentice or veteran minimum and the 25% above-the-line limit (now applied as a share cap)"),
        ("us_wv_film_production_tax_credit", C_DATA_MISSING, "W. Va. Code 11-13X read: the credit is nonrefundable (4(a)), carries forward two years, is transferable with approval, sunsets for expenditures after December 31, 2027, and the 4% needs 10 resident full-time employees or apprentices"),
        ("us_nj_garden_state_film_credit", C_DATA_MISSING, "N.J.S.A. 54:10A-5.39b read: first-come approval within USD 100 million a year (not a selective award), seven-year carry-forward, no refund, sunset July 1, 2049 (the Division page said 2039), 60%/USD 1 million gate, 180-day photography start, USD 750,000 per highly compensated individual exclusion (now applied to identified payees), same-cost bar, diversity credit 2% / 4% to 2034"),
        ("us_ar_digital_motion_picture_incentive", C_CONFLICT, "the 25% + 10% + 5% versus 30% 'inconsistency' was an incomplete page: Act 517 of 2023 adds a further 5% for multi-project productions and caps the total at 30% of each expenditure (15-4-2005(f)); selection is discretionary ('may offer'); the USD 500,000 per-employee wage limit is now applied to identified W-2 payees"),
        ("us_mt_media_act_tax_credit", C_DATA_MISSING, "MCA 15-31-1004 to 1010 read: USD 12 million calendar-year cap, allocation first to credits approved before December 31, 2024, base investment threshold USD 350,000, sunset tax year 2045, non-refundable, compensation-based add-ons to 35% of base investment"),
        ("us_oh_motion_picture_tax_credit", C_DATA_MISSING, "ORC 122.85 read in full: no transfer or assignment provision and no sunset (confirmed authoritative silence); non-transferable and open-ended"),
        ("us_ny_empire_state_independent_film_credit", C_DATA_MISSING, "Tax Law 24-D(e) pools and the 0.5% credit reduction (24-D(f)(1)) read; the credit years remain open"),
        ("ca_cmf", C_DATA_MISSING, "reclassified UNPRICEABLE_AUTHORITY_INSUFFICIENT -> NON_GUARANTEED_SELECTIVE: envelopes go to broadcasters and distributors by past performance, with no producer-level rate"),
        ("nohfc_production_fund", C_DATA_MISSING, "reclassified to NON_GUARANTEED_SELECTIVE: competitive intake, conditional contribution up to 50% of eligible Northern Ontario costs, capped CAD 500,000 / 1,000,000 / 2,000,000 by budget"),
        ("us_sundance_doc", C_DATA_MISSING, "reclassified to NON_GUARANTEED_SELECTIVE: open call, about 20-30 of 1,300 proposals funded, USD 25,000-40,000 development and USD 50,000-100,000 production"),
        ("us_itvs_fund", C_DATA_MISSING, "reclassified to NON_GUARANTEED_SELECTIVE: ITVS Open Call is a co-production agreement up to USD 400,000, not a grant; the 'International Documentary Fund' name is not a current ITVS program page"),
        ("mx_eficine_incentive", C_DATA_MISSING, "reclassified to NON_GUARANTEED_SELECTIVE: LISR art. 189 (not 226) is an investor credit allocated by an interinstitutional committee within MXN 650 million a year, MXN 20 million per contributor and project, 10% of prior-year ISR")):
    REPAIRS.setdefault(_slug, []).append((_cls, _what, _R13, _T13))

# ── residual propositions that are not a single program's field (the commissioned residual inventory; frozen, not expanded) ────────────────────────────────────────────────────────
RESIDUALS: list[dict] = [
    {"id": "PA-STATUTE-VS-DCED", "slug": "us_pa_film_production_credit", "cls": C_CONFLICT,
     "what": "Act 84 of 2016 (Appendix A to the Guidelines) caps $15,000,000 in the aggregate of compensation paid to individuals; the DCED Guidelines (10/28/2020) Component A note caps $15 million of principal-actor payments",
     "treatment": "the administering agency's reading is priced (above-the-line cast account over USD 15,000,000 excluded); the wider statutory reading is disclosed, not applied",
     "need": "a DCED determination or an award letter stating which reading applies"},
    {"id": "BH-SAG-RESERVE", "slug": "ca_federal_cptc", "cls": C_FACT,
     "what": "Bad Hombres line 1600 SAG deposit / residual reserve (USD 60,000): RC4164 line 421 names neither residuals nor union deposits; credit effect 9,000.00 on the CPTC cost cap",
     "treatment": "kept in production cost (higher cap) until stated; the contingency part (USD 94,382, effect 11,380.35) is wired to the producer's contingency election",
     "need": "producer statement whether the 60,000 is a paid, non-refundable expenditure or an unfunded reserve; BH is not evaluated here"},
    {"id": "ALLOCATION-QC-MB-NL", "slug": "ca_federal_pstc", "cls": C_DATA_MISSING,
     "what": "ITA 125.5(1) 'qualified Canadian labour expenditure' paragraph (b) nets 'an amount of assistance that can reasonably be considered to be in respect of' the Canadian labour expenditure: a reasonableness test with no formula (read 2026-10-13). The labour share of an ALL-SPEND provincial credit that nets the federal PSTC (Quebec 25%, Manitoba 30% cost-of-production, Newfoundland and Labrador 40%, Alberta 22%, and New Brunswick, Nova Scotia 25% and Saskatchewan when awarded) is therefore taken as rate x PSTC labour basis; RC4385 says only that any provincial credit is assistance. Ontario states its own pro-rata method for its own credits (Taxation Act, 2007 s.90(4)), which is not authority for the federal test",
     "treatment": "kept SEPARATE from verified netting: every adjustment is labelled VERIFIED NETTING (OPSTC s.3.02, BC DAVE, the Ontario OFTTC and the BC film and television credit: labour-only credits) or ASSUMED ALLOCATION, the generator text splits verified and assumed labour assistance, and the whole-credit lower bound is disclosed on every assumed one",
     "need": "a CRA written position, or a certificate or statement from the provincial authority, giving the labour portion of the credit (the statute leaves it to what is reasonable)"},
    {"id": "PRODUCER-FACT-UI", "slug": "ca_federal_cptc", "cls": C_FACT,
     "what": "producer program facts written through POST /projects/{id}/program-facts (OPSTC 25% Ontario labour, OCASE CAD 25,000 labour, Colorado workforce/CPA, Oregon and Texas award facts, Alabama payroll, BC DAVE activity, California independent category, West Virginia 10-resident hires, New Jersey outside-the-30-mile-radius spend, and the older NY/Ontario/BC/Manitoba/Alberta keys) have no Overview/Inspector control and no api.js client; the facts that are also content/approval gates (CPTC certificate and control, NL Part I, Colorado/Arizona pre-approval, OCASE permanent establishment) DO have the Inspector content-gates control",
     "treatment": "Unknown is absence (a false is never stored); the fact enters the evaluation fingerprint; unstated facts hold the program at USER_FACT_REQUIRED and economics CONDITIONAL",
     "need": "a UI stage (Overview + Inspector, one canonical copy) with independent verification"},
    {"id": "AG-45-DENOMINATOR", "slug": "", "cls": C_SUPERSEDED,
     "what": "AG's 45-program completeness denominator was derived from engine snapshot keys",
     "treatment": "retired: the live NA denominator is derived from the canonical identity layer and rate registry (see the universe counts)",
     "need": "none for the denominator; AG artifacts are not accepted as independent proof"},
    {"id": "LLS-CA-01", "slug": "ca_film_30", "cls": C_FACT,
     "what": "Lips Like Sugar California regime (Program 3.0 letter dated before 2025-07-01 versus Program 4.0 prospective), shooting-day share and persisted contingency election are not established",
     "treatment": "prospective planning is dated Program 4.0; the 2023 letter is historical reference only",
     "need": "producer-stated allocation-letter date and regime, shooting days, contingency election"},
    {"id": "STALE-REAL-GENERATIONS", "slug": "", "cls": C_STALE,
     "what": "persisted generations of Little Utopia, F#K Valentine's Day, Lips Like Sugar and Bad Hombres predate engine canonical-1.130.0 and the migrations 0082-0088",
     "treatment": "retained and visible with stale economics disclosed; no cold evaluation was run",
     "need": "explicit authorization per production, then restart, migrations on the acceptance database and bounded regeneration"},
    {"id": "NL-ELIGIBLE-CORPORATION", "slug": "ca_nl_all_spend_credit", "cls": C_FACT,
     "what": "Regulation 31/23 s.4(1) eligible-corporation tests (permanent establishment, primarily film production, no CRTC licence, not tax-exempt) and Part I registration are producer facts",
     "treatment": "Part I registration is a clearable producer fact; the s.4(1) tests are claim follow-ups",
     "need": "producer statements"},
    {"id": "NEW-STATE-CAPABILITY-PROFILES", "slug": "us_oh_motion_picture_tax_credit", "cls": C_DATA_MISSING,
     "what": "Ohio, West Virginia, Missouri, New Jersey, Montana and Arkansas are rate-bearing (statute-read rates and caps, NA-RECONCILIATION-13) but have no jurisdiction capability profile (studio, crew depth, water, post) and no cost benchmark, so production discovery cannot accept them as relocation candidates even with the capability gate off; their Jurisdiction rows are seeded (migration 0088) but only for code, name and USD",
     "treatment": "priced when a production is based in the state or a component is assigned there; never offered as a relocation destination; listed explicitly in the harness oracle so the gap cannot hide",
     "need": "capability facts for each state from a production-services source (not an incentive source) and a cost benchmark, then the profile entries"},
    {"id": "MT-AVAILABILITY", "slug": "us_mt_media_act_tax_credit", "cls": C_DATA_MISSING,
     "what": "MCA 15-31-1010 (read 2026-10-13) fixes the cap (USD 12 million a calendar year) and allocates the whole of it to credits approved before December 31, 2024 until they are claimed; Commerce has paused certification and states the first available credit is 2031. How much of the pre-2025 backlog remains is a figure the Department of Revenue posts (15-31-1010(3)(c)), not statute text",
     "treatment": "20% ceiling with an unresolved availability condition: no guaranteed value; the base investment threshold (USD 350,000), non-refundability and the 2045 sunset are recorded",
     "need": "the Department of Revenue's posted remaining-backlog and available-credit amount for the production year"},
    {"id": "MO-POOL-RATIONING", "slug": "us_mo_motion_media_production_tax_credit", "cls": C_DATA_MISSING,
     "what": "RSMo 135.750 (read in full 2026-10-13) fixes the rates, uplifts, caps (USD 8 million film, USD 8 million series), non-refundability and the 2029 sunset but does not say how the pool is rationed among applicants (first-come, ranking or discretion) and leaves approval to the film commission and the department (subsection 3(7))",
     "treatment": "20% base kept as the guaranteed floor with the annual pool and approval disclosed as allocation risk; the 42% ceiling needs each uplift fact",
     "need": "the Department of Economic Development program guidelines or a rule stating the pool-allocation method"},
    {"id": "NY-IND-YEARS", "slug": "us_ny_empire_state_independent_film_credit", "cls": C_DATA_MISSING,
     "what": "Tax Law 24-D (consolidated text, read 2026-10-13) states the pools (USD 20 million for films under USD 10 million, USD 80 million above, at least two application periods, order of application) and a 0.5% reduction of the credit (24-D(f)(1)), but no start year, end year or transferability; the budget-bill session law that enacted the credit was not located",
     "treatment": "30% floor with qualification and first-come allocation disclosed; both New York pairs are mutually exclusive (ESD page); the 0.5% reduction is disclosed, not applied",
     "need": "the 2025 budget-bill session law (Part and chapter) stating the credit years and transferability, and the current ESD pool status at application time"},
    {"id": "NS-FUND-2026-27", "slug": "ca_ns_production_incentive_fund", "cls": C_DATA_MISSING,
     "what": "the published guidelines (April 1, 2024 edition; the PDF still carries the 2021 cover) say the Fund was renewed for annual funding 'until the 2025-2026 fiscal year' and is to be reviewed no later than 2025-2026; the CCTH program page is current (updated October 2026) and carries the April 2024 changes, but no 2026-27 renewal statement or budget line was found",
     "treatment": "treated as current on the official page with the fiscal-year wording recorded as an unreconciled qualifier; Stream II 25% base priced with its funding risk disclosed",
     "need": "a Nova Scotia 2026-27 budget line or CCTH notice stating the Fund's funding authority for 2026-27"},
    {"id": "BC-ADDITIONAL-CREDITS", "slug": "ca_bc_film_tv_tax_credit", "cls": C_FACT,
     "what": "Income Tax Act (BC) credits that sit on the s.80 credit need facts a topsheet lacks: regional (s.81.1: 12.5% x QLE x RD/TD, at least 5 and more than 50% of BC shooting days outside the designated Vancouver area), distant location (s.81.11: 6% x QLE x DLD/TD), film training (s.82: lesser of 3% of QLE and 30% of net training payments), scriptwriting (s.80.1); the s.85(4) filing limit is 36 months after the taxation year",
     "treatment": "the s.80 35% (40% with the photography fact) is priced; the additional credits are disclosed with their formulas, not priced",
     "need": "producer shooting-day location split (RD, DLD, TD), approved-training payments and BC scriptwriter payments"},
    {"id": "SK-NB-BONUS-FACTS", "slug": "ca_sk_creative_saskatchewan_grant", "cls": C_FACT,
     "what": "the bonus schedules are now exact: Saskatchewan (FY 2026/27) rural 5% (majority of principal photography days 50 km or more outside Regina and Saskatoon), post-production 5% (majority of post spend in Saskatchewan), production volume 10% (two completed eligible projects and CAD 1.5 million combined Saskatchewan spend in the current and three prior fiscal years), to 40% (Saskatchewan Stream) or 35% (Service Production Stream) with 51% of principal photography days in Saskatchewan; New Brunswick (LIFT 2026/27) Heads of Department and Lead Talent +3% (30% NB residents), rural or remote principal photography +3% or +4% (50% of photography; 30-150 km or 151 km and over from Fredericton, Moncton or Saint John city halls), NB Made +3% (two of six content thresholds), to a combined 35%",
     "treatment": "both are discretionary grants held at zero guaranteed with the base rate as the ceiling; the bonuses are disclosed with their thresholds, not priced",
     "need": "producer facts for the days, spend and residency thresholds, and an award letter, because both programs are assessed and ranked"},
    {"id": "DAVE-POST-PRODUCTION-BASE", "slug": "ca_bc_dave", "cls": C_FACT,
     "what": "B.C. Reg. 4/99 s.10.1 (read 2026-10-13) makes prescribed digital post-production labour (post-production carried out primarily with digital technology, excluding re-shooting, mass duplication and promotional material) part of the DAVE base, but the corrected base keeps the VFX/animation lines only",
     "treatment": "VFX/animation labour only (the corrected labour-only base is preserved); post-production labour is not added",
     "need": "a post-production labour category in the budget and the producer's 'primarily digital' statement"},
]

#: catalog rows that are not one-to-one with a canonical identity, with the reason and the targets (explicit; every NA catalog row not auto-linked must be here)
CATALOG_OVERRIDES: dict[tuple[str, str], tuple[str, tuple[str, ...], str]] = {
    ("CA", "film incentive bc (fibc)"): ("LINK", ("ca_bc_film_tv_tax_credit",), "NA-RECONCILIATION-12: Film Incentive BC is the BC film and television tax credit (ITA (BC) s.80), now rate-bearing"),
    ("US", "digital product and motion picture industry incentive"): ("LINK", ("us_ar_digital_motion_picture_incentive",), "NA-RECONCILIATION-12: now rate-bearing"),
    ("US", "garden state film and digital media jobs act \u2014 film credit"): ("LINK", ("us_nj_garden_state_film_credit",), "NA-RECONCILIATION-12: now rate-bearing"),
    ("US", "media tax credit"): ("LINK", ("us_mt_media_act_tax_credit",), "NA-RECONCILIATION-12: now rate-bearing"),
    ("US", "motion media production tax credit"): ("LINK", ("us_mo_motion_media_production_tax_credit",), "NA-RECONCILIATION-12: now rate-bearing"),
    ("CA", "bell fund — broadcast and digital content development"): ("NO_RECORD", (), "broadcaster/digital fund; stack spelling ca_bell_fund (2 rules) has no canonical identity"),
    ("CA", "canada media fund (cmf) / telefilm canada / cptc / pstc"): ("COMPOSITE", ("ca_cmf", "ca_federal_cptc", "ca_federal_pstc"), "composite catalog row; the Telefilm component has no canonical identity (ca_telefilm_dev)"),
    ("CA", "crtc — online streaming act (bill c-11) local content obligations"): ("NOT_INCENTIVE", (), "a regulatory content obligation, not a producer incentive: no economic instrument to price (cf. NON_ECONOMIC)"),
    ("CA", "canada production tax credit (cptc) + provincial credits"): ("COMPOSITE", ("ca_federal_cptc",), "federal credit linked; each provincial credit is its own row"),
    ("CA", "film or video production services tax credit (pstc)"): ("LINK", ("ca_federal_pstc",), "alias proposed_canada_film_or_video_production_services_tax_credit_pstc"),
    ("CA", "refundable tax credit for film production services"): ("LINK", ("ca_qc_pstc",), "alias proposed_canada_quebec_refundable_tax_credit_for_film_production_services"),
    ("CA", "telefilm canada — canada feature film fund (cfff)"): ("NO_RECORD", (), "selective fund; stack spelling ca_telefilm_dev (5 rules) has no canonical identity"),
    ("CA", "telefilm canada — export development program"): ("NO_RECORD", (), "selective fund; stack spelling ca_telefilm_dev has no canonical identity"),
    ("CA-BC", "bc production services tax credit (pstc)"): ("LINK", ("ca_bc_pstc",), "the BC production services credit (stack spelling ca_bc_pstc is the canonical slug)"),
    ("US", "film tax credit — post-production"): ("LINK", ("us_ny_post_production_credit",), "NA-RECONCILIATION-11: the New York Empire State film post-production credit; the duplicate proposal identity is bound to it"),
    ("CA-BC", "bc production services tax credit (pstc) / dave"): ("COMPOSITE", ("ca_bc_pstc", "ca_bc_dave"), "composite catalog row"),
    ("CA-MB", "manitoba film & video production tax credit | manitoba film & music — production support grants"): ("COMPOSITE", ("ca_mb_film_video_credit",), "credit linked; the grants have no canonical identity"),
    ("CA-MB", "manitoba film & music — production support grants"): ("NO_RECORD", (), "selective grants; no canonical identity"),
    ("CA-NL", "newfoundland & labrador film development corp production incentive"): ("LINK", ("ca_nl_all_spend_credit",), "committee ruling: ca_nl_production_fund is a duplicate alias of the all-spend credit (CANONICAL_RUNTIME_SLUG_BINDINGS)"),
    ("CA-ON", "opstc / ocase / nohfc"): ("COMPOSITE", ("on_opstc", "ontario_computer_animation_and_special_effects_tax_credit_ocase", "nohfc_production_fund"), "composite catalog row"),
    ("CA-PE", "film pei — prince edward island production support"): ("NO_RECORD", (), "provincial support program; no canonical identity"),
    ("CA-PE", "pei film production investment fund"): ("NO_RECORD", (), "provincial investment fund; no canonical identity"),
    ("CA-QC", "qprdp / sodec"): ("COMPOSITE", ("ca_qc_pstc",), "Quebec services credit linked; the QPRDP component is an unbound legacy spelling (QPRDP-IDENTITY)"),
    ("CA-QC", "quebec film and television production tax credit (sodec)"): ("LINK", ("ca_qc_pstc",), "committee ruling: qc_film_production is a duplicate alias of ca_qc_pstc"),
    ("CA-QC", "quebec production tax credit — foreign productions (qprdp)"): ("LINK", ("ca_qc_pstc",), "NA-RECONCILIATION-12: 'QPRDP' is an unofficial label; SODEC and Revenu Québec name one foreign-production credit, the refundable tax credit for film or television production services (CO-1029.8.36.SP) = ca_qc_pstc"),
    ("MX", "efica 30% tax credit / imcine discretionary funds"): ("OPEN_IDENTITY", ("mx_federal_film_incentive_2026",), "the 30% federal incentive is canonical; that this catalog label ('EFICA') is that program is not proven by a retained record, and the IMCINE funds have no identity"),
    ("MX", "imcine — instituto mexicano de cinematografía — foprocine / fidecine"): ("NO_RECORD", (), "selective national funds; no canonical identity"),
    ("MX", "mexico eficine (article 226 tax credit) and procine fund"): ("LINK", ("mx_eficine_incentive",), "same program as the coverage record (name differs by '(Article 226)' punctuation)"),
    ("US", "sovereign discretionary grants (sundance/itvs/tribeca)"): ("COMPOSITE", ("us_sundance_doc", "us_itvs_fund"), "composite catalog row; the Tribeca component has no canonical identity"),
    ("CA", "bell fund — broadcast and digital content development"): ("LINK", ("ca_bell_fund",), "NA-RECONCILIATION-13: Bell Fund Production Program Selective stream (coverage NON_GUARANTEED_SELECTIVE)"),
    ("CA", "telefilm canada — canada feature film fund (cfff)"): ("LINK", ("ca_telefilm_dev",), "NA-RECONCILIATION-13: Telefilm Canada Production Program Guidelines (applicable October 31, 2025): financing may not exceed the lesser of 49% of eligible Canadian costs or CAD 500,000 / one third / the lesser of 49% or CAD 3.5-4 million; compliance does not guarantee funding"),
    ("CA", "telefilm canada — export development program"): ("NO_RECORD", (), "a different Telefilm program (export and marketing support); its guidelines were not retrieved"),
    ("CA", "nsi — national screen institute drama prize and development programs"): ("NO_RECORD", (), "the Drama Prize is not on NSI's current program list (TELUS STORYHIVE, Manitoba Directors Lab, Access+ and training programs); identity unverified"),
    ("US", "state film tax credits (multi-state)"): ("AGGREGATE_ROW", (), "catalog aggregate for the individual state programs, each its own row; not a program"),
    ("US", "tribeca film institute — documentary and narrative development grants"): ("NO_RECORD", (), "selective development grants; no canonical identity"),
    ("US-NY", "new york state film tax credit program"): ("LINK", ("ny_state_film",), "alias us_ny_film_credit; the post-production credit is its own row"),
}

# ── helpers ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def is_na_code(code: str | None) -> bool:
    c = (code or "").upper()
    return c in ("US", "CA", "MX") or c.startswith(("US-", "CA-", "MX-"))


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _lower(s: str) -> str:
    return " ".join(s.lower().split())


def _tests_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "tests"


def _test_references(slugs: list[str]) -> dict[str, list[str]]:
    texts = {}
    for f in sorted(_tests_dir().glob("test_*.py")):
        try:
            texts[f.name] = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    out: dict[str, list[str]] = {}
    for s in slugs:
        out[s] = [n for n, t in texts.items() if s in t][:4]
    return out


def _load():
    import app.data.program_rate_rules_worldwide  # noqa: F401  (populates the doctrine registry)
    from app.data import authority_coverage_registry as acr
    from app.data import global_inventory as gi
    from app.data import program_authority_provenance as pa
    from app.data import program_requirements as pr
    from app.data.executable_jurisdiction_registry import get_doctrine
    from app.data.program_rate_rules import _RULES_BY_PROGRAM
    from app.optimization import stacking_rules as sr
    from app.services import canonical_program_consolidation as cpc
    from app.services import canonical_program_identity as cpi
    from app.services import canonical_publication_contract as pub
    from app.services import program_pricing_crosswalk as pc
    return dict(acr=acr, gi=gi, pa=pa, pr=pr, get_doctrine=get_doctrine, rules=_RULES_BY_PROGRAM, sr=sr, cpc=cpc, cpi=cpi, pc=pc, pub=pub)


# ── the frozen universe ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def frozen_universe() -> dict:
    """The NA universe, derived from the live registries. ``rate_bearing`` and ``coverage_only`` are canonical identities; ``stack_spellings`` and ``catalog`` are the other layers."""
    m = _load()
    cpi, acr, rules, gi, sr = m["cpi"], m["acr"], m["rules"], m["gi"], m["sr"]
    identities = {i.canonical_slug: i for i in cpi.all_canonical_identities()}

    def jur(slug: str) -> str:
        d = m["get_doctrine"](slug)
        return (d.jurisdiction_code if d is not None else "") or identities[slug].jurisdiction_code or ""

    def na_identity(slug: str) -> bool:
        if is_na_code(jur(slug)):
            return True
        rec = acr.COVERAGE_REGISTRY.get(slug)
        return bool(rec is not None and (is_na_code(rec.jurisdiction) or _NA_TEXT.match(rec.jurisdiction or "")))

    rate_bearing = sorted(s for s in identities if s in rules and na_identity(s))
    coverage_only = sorted(s for s in identities if s not in rules and na_identity(s))
    known = set(identities) | {a for i in identities.values() for a in i.aliases}
    inferred: dict[str, list] = defaultdict(list)
    for p in gi.ALL_PROGRAMS:
        s = sr.infer_slug(p)
        if s:
            inferred[s].append(p)
    pair_slugs = Counter(s for k in sr._SLUG_PAIR_RULES for s in k)

    def na_stack(s: str) -> bool:
        ps = inferred.get(s, [])
        if ps:
            return any(is_na_code(p.jurisdiction_code) for p in ps)
        return s.startswith(("us_", "ca_", "mx_", "on_", "qc_", "ny_"))

    stack_spellings = sorted(s for s in pair_slugs if s not in known and na_stack(s))
    catalog = sorted(((p.jurisdiction_code, p.program_name) for p in gi.ALL_PROGRAMS if is_na_code(p.jurisdiction_code)))
    return {"identities": identities, "rate_bearing": rate_bearing, "coverage_only": coverage_only, "stack_spellings": stack_spellings,
            "stack_pair_counts": {s: pair_slugs[s] for s in stack_spellings}, "catalog": catalog, "jur": jur}


def independent_denominator() -> dict:
    """A second derivation that shares no code path with ``frozen_universe`` beyond the raw registries: the NA rate-bearing set from the doctrine records and the legacy rate table, the NA
    coverage-only set from the coverage records after alias folding, counted without the identity service."""
    m = _load()
    acr, rules = m["acr"], m["rules"]
    from app.data.executable_jurisdiction_registry import all_doctrine_records
    from app.data.program_slug_aliases import PROGRAM_SLUG_ALIASES

    rb = {r.program_slug for r in all_doctrine_records() if is_na_code(r.jurisdiction_code) and r.program_slug in rules}
    fold = lambda s: PROGRAM_SLUG_ALIASES.get(acr.CANONICAL_RUNTIME_SLUG_BINDINGS.get(s, s), acr.CANONICAL_RUNTIME_SLUG_BINDINGS.get(s, s))
    cov = set()
    for slug, rec in acr.COVERAGE_REGISTRY.items():
        if is_na_code(rec.jurisdiction) or _NA_TEXT.match(rec.jurisdiction or ""):
            c = fold(slug)
            if c not in rules and c == slug:
                cov.add(c)
    return {"rate_bearing": sorted(rb), "coverage_only_from_coverage_records": sorted(cov)}


# ── matrix ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


_COLUMNS = ["canonical_slug", "row_layer", "row_kind", "proposition_id", "aliases", "jurisdiction", "program_name", "program_type", "live_registry_inclusion", "authority_disposition",
            "rate_status", "rate_value_basis", "qpe_territorial_status", "authority_completeness", "qualification_status", "stacking_status", "temporal_status", "canonical_owner", "served_consumer",
            "defect_classification", "repair_commit_or_file", "focused_test", "terminal_disposition", "residual_evidence_needed"]


def columns() -> list[str]:
    return list(_COLUMNS)


def _row(**kw) -> dict:
    r = {c: "" for c in _COLUMNS}
    r.update(kw)
    assert r["defect_classification"] in CLASSES, r["defect_classification"]
    return r


def _temporal(m, slug: str, priced: bool) -> str:
    if not priced:
        return "NOT_APPLICABLE (not priced)"
    prof = m["pr"].get_program_requirements(slug)
    d = m["get_doctrine"](slug)
    parts = []
    sunset = prof.sunset_date if prof is not None else None
    if sunset:
        try:
            parts.append("SUNSET_PASSED " + sunset if date.fromisoformat(str(sunset)[:10]) < date.fromisoformat(AS_OF) else "SUNSET " + str(sunset))
        except ValueError:
            parts.append("SUNSET " + str(sunset))
    else:
        parts.append("NO_SUNSET_RECORDED")
    eff = d.provenance.effective_date if d is not None and d.provenance is not None else None
    parts.append("EFFECTIVE " + str(eff)[:60] if eff else "EFFECTIVE_DATE_NOT_RECORDED")
    return "; ".join(parts)


def _dims(m, slug: str) -> dict:
    return {d.dimension: d.status for d in m["cpc"].consolidate(slug).dimensions}


def _stack_status(m, slug: str) -> tuple[str, list[tuple[str, str]]]:
    """(summary, unruled same-scope pairs) -- pairs among the PRICED NA programs that can be claimed together: same jurisdiction, or the federal 'CA' with a province."""
    cpi, sr = m["cpi"], m["sr"]
    spellings = {slug, *cpi._aliases_for(slug)}
    counts = Counter(v["rule_type"] for k, v in sr._SLUG_PAIR_RULES.items() if k & spellings)
    return ", ".join(f"{t}={n}" for t, n in sorted(counts.items())) or "no named pair rule", []


def _unruled_pairs(m, priced: dict[str, str]) -> list[tuple[str, str]]:
    from app.calculators.canonical_stack_bridge import load_named_pair_rule
    import itertools

    def scope(a: str, b: str) -> bool:
        ja, jb = priced[a], priced[b]
        return ja == jb or (ja == "CA" and jb.startswith("CA-")) or (jb == "CA" and ja.startswith("CA-"))

    return [(a, b) for a, b in itertools.combinations(sorted(priced), 2) if scope(a, b) and load_named_pair_rule(a, b) is None]


def _fact_info(m, slug: str) -> list[dict]:
    """Every stored ProjectFact key the program's rules depend on (rate conditions, awarded-rate keys and the uplift prerequisites), with its persistence owner, Unknown-versus-False
    semantics, fingerprint membership and UI-control status. Uplift facts only affect the MAXIMUM; the floor prices without them."""
    from app.data.program_rate_rules import SUBSET_UPLIFT_RULES, get_rate_rules
    from app.services.jurisdiction_disposition import AMOUNT_PREFIX, EVIDENCED_PREFIX, rate_rule_fact_keys
    from app.services.ny_producer_facts import NY_EVIDENCED_FACTS, PROGRAM_AMOUNT_FACTS
    from app.services.program_content_gates import gate_control_whitelist

    gate_keys = set(gate_control_whitelist())
    component_basis = {c.amount_fact_key for r in get_rate_rules(slug) for c in r.conditions if c.amount_fact_key and c.is_component_basis}
    from app.optimization.structural_prerequisites import STRUCTURAL_PREREQUISITES
    structure_derived = {EVIDENCED_PREFIX + p.fact_key for p in STRUCTURAL_PREREQUISITES.values()}     # derived from the structure (a calculation rule), never a producer fact
    stored = set(rate_rule_fact_keys(slug)) - structure_derived
    uplift_keys: set[str] = set()
    for r in get_rate_rules(slug):
        for c in r.conditions:
            for k in (c.superseded_by_boolean_fact_key, c.regional_uplift_multiplier_fact_key, *c.blocked_by_boolean_fact_keys):
                if k:
                    stored.add(EVIDENCED_PREFIX + k)
    for up in SUBSET_UPLIFT_RULES.get(slug, ()):
        for k in (up.prerequisite_fact, up.whole_base_fact, up.excluded_fact):
            if k:
                stored.add(EVIDENCED_PREFIX + k)
                uplift_keys.add(k)
    out = []
    for st in sorted(stored):
        kind = "evidenced" if st.startswith(EVIDENCED_PREFIX) else "amount"
        key = st.split(":", 1)[1]
        if kind == "evidenced":
            if key in gate_keys and key not in NY_EVIDENCED_FACTS:
                writer, ui = "POST /projects/{id}/content-gates (program_content_gates)", "EXISTS: Inspector content-gates control (frontend/src/shell/Inspector.jsx, api.js)"
            elif key in NY_EVIDENCED_FACTS:
                writer, ui = "POST /projects/{id}/program-facts (ny_producer_facts.write_ny_program_facts)", "NONE: no Overview/Inspector control and no api.js client"
            else:
                writer, ui = "NO WRITER", "NONE"
            unknown = "absence = Unknown; a false is never stored as evidence (true or null only)" if key in NY_EVIDENCED_FACTS else "absence = Unknown; refused is stored false = not evidenced"
            fp = "evidenced_program_facts"
        else:
            if key in component_basis:
                writer, ui = "derived from this segment's own allocation lines (component basis)", "not a producer input"
            elif key in PROGRAM_AMOUNT_FACTS:
                writer, ui = "POST /projects/{id}/program-facts (amounts, validated 0-100)", "NONE: no Overview/Inspector control and no api.js client"
            else:
                writer, ui = "NO WRITER", "NONE"
            unknown = "absence = Unknown (never defaulted to 0)"
            fp = "amount_facts"
        out.append({"key": key, "kind": kind, "scope": "uplift (maximum only)" if key in uplift_keys else "confirmed treatment", "stored_as": st, "writer": writer,
                    "unknown_semantics": unknown, "fingerprint": fp, "ui_control": ui})
    return out


def build_matrix() -> list[dict]:
    m = _load()
    u = frozen_universe()
    ids, jur = u["identities"], u["jur"]
    pc_rows = {r["program_slug"]: r for r in m["pc"].all_program_treatments()}
    all_slugs = list(u["rate_bearing"]) + list(u["coverage_only"])
    refs = _test_references(all_slugs)
    pa, pr, acr, cpi, sr = m["pa"], m["pr"], m["acr"], m["cpi"], m["sr"]
    priced = {s: jur(s) for s in u["rate_bearing"] if not acr.blocks_economic_candidacy(s) and pc_rows[s]["treatment"] != "SUPERSEDED_DUPLICATE_NOT_APPLICABLE"}
    unruled = _unruled_pairs(m, priced)
    unruled_by = defaultdict(list)
    for a, b in unruled:
        unruled_by[a].append(b)
        unruled_by[b].append(a)
    rows: list[dict] = []
    props: list[dict] = []

    def owner(slug: str, rate: bool) -> str:
        bits = ["canonical_program_identity"]
        if rate:
            bits.append("executable_jurisdiction_registry.DoctrineRecord" if m["get_doctrine"](slug) is not None else "program_rate_rules (legacy hand table)")
        bits.append("authority_coverage_registry")
        if pr.get_program_requirements(slug) is not None:
            bits.append("program_requirements")
        if rate:
            bits.append("program_spend_rules")
        return " + ".join(bits)

    # ── RATE_BEARING ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    for slug in u["rate_bearing"]:
        ident, t = ids[slug], pc_rows[slug]
        disp = pa.authority_disposition(slug)
        cov = acr.coverage_state(slug)
        dims = _dims(m, slug)
        prof = pr.get_program_requirements(slug)
        facts = _fact_info(m, slug)
        stack_summary, _ = _stack_status(m, slug)
        findings: list[tuple[str, str, str, str]] = []   # (class, proposition id, what, need)
        for cls, why, where, test in REPAIRS.get(slug, []):
            findings.append((cls, f"REPAIRED:{where}", why, "repaired; see repair column"))
        # open findings
        if t["treatment"] in ("ECONOMIC_MECHANICS_INCOMPLETE",) or cov in ("UNPRICEABLE_AUTHORITY_INSUFFICIENT", "NON_ECONOMIC", "CANONICAL_DATA_HANDOFF_DEFECT"):
            findings.append((C_DATA_MISSING, "RATE-MECHANICS", f"a rate/base/cap mechanic is absent ({t['treatment_reason']})", "primary rate, base, cap and threshold authority"))
        if disp != pa.AUTHORITY_VERIFIED_PRICEABLE:
            findings.append((C_PROVENANCE, "PROVENANCE", "real retained RateRule; structured primary provenance incomplete (production-acceptance warning, never an economic block)",
                             "the issuing authority's own current source for the rate/base/cap propositions, attached as SourceProvenance"))
        for f in facts:
            if f["writer"].startswith("derived from"):
                continue   # a component-basis amount is derived from the budget's own lines: not a producer input
            findings.append((C_FACT, f"FACT:{f['key']}", f"project fact '{f['key']}' ({f['kind']}; {f['scope']}); unstated = Unknown", f"producer statement via {f['writer']}" if f["writer"] != "NO WRITER" else "a producer writer for this key"))
        if prof is None:
            findings.append((C_DATA_MISSING, "QUALIFICATION-PROFILE", "no requirements profile: production-fit stays UNKNOWN (NO_REQUIREMENTS_ON_FILE); economics are unaffected",
                             "primary requirement facts: entity, cultural/content test, preapproval and timing, minimum spend, cap, monetization"))
        for other in sorted(unruled_by.get(slug, [])):
            findings.append((C_DATA_MISSING, f"STACK-PAIR:{other}", f"no named stacking rule for the pair {slug} + {other} (same claim scope): the combination stays UNRESOLVED_NO_AUTHORITY and blocks",
                             "primary text on whether the two credits may be claimed together and how each treats the other as assistance"))
        for r in RESIDUALS:
            if r["slug"] == slug:
                findings.append((r["cls"], f"RESIDUAL:{r['id']}", r["what"], r["need"]))
        ac = m["pub"].authority_completeness(slug)
        dims_open = ac.unresolved_material_dimensions
        if dims_open:
            findings.append((C_DATA_MISSING, "AUTHORITY-DIMENSIONS", "the publication contract's material dimensions not yet resolved by a researcher (PARTIAL/MISSING): " + ", ".join(dims_open)
                             + ". The program still prices through the canonical doctrine default; this is a knowledge-completeness gap, not a pricing block",
                             "per dimension: a primary-source value, a confirmed non-applicability, or a confirmed authoritative silence: " + ", ".join(dims_open)))
        open_findings = [f for f in findings if not f[1].startswith("REPAIRED:")]
        primary_open = [f for f in open_findings if f[1] != "AUTHORITY-DIMENSIONS"]
        repaired = [f for f in findings if f[1].startswith("REPAIRED:")]
        principal = None
        for sev in _SEVERITY:
            if any(f[0] == sev for f in primary_open):
                principal = sev
                break
        if principal is None:
            principal = repaired[0][0] if repaired else C_CONSUMED
        # a repaired defect keeps the class it had only when nothing else is open; authority-dimension gaps are carried as their own proposition and a distinct terminal state
        if primary_open:
            terminal = f"OPEN_{principal}"
        elif repaired:
            terminal = "PRICED_REPAIRED" if not dims_open else "PRICED_REPAIRED_AUTHORITY_DIMENSIONS_OPEN"
        else:
            terminal = "AUTHORITY_COMPLETE_CONSUMED" if not dims_open else "PRICED_AUTHORITY_DIMENSIONS_OPEN"
        need = "; ".join(sorted({f[3] for f in open_findings})) if open_findings else ""
        basis = "primary-source value" if disp == pa.AUTHORITY_VERIFIED_PRICEABLE else "explicit planning assumption (retained rate; primary provenance not established)"
        rate_status = (f"{t['treatment']}: floor {t['deterministic_floor_rate']}, maximum {t['supported_maximum_rate']}, min spend {t['minimum_spend_usd']}, "
                       f"per-project cap {t['per_project_cap_usd']}, annual cap {t['annual_program_cap_usd']}")
        qual = (pr.verification_state(slug).name if prof is not None else "NO_PROFILE")
        refs_s = ", ".join(refs.get(slug, [])) or "NO_FOCUSED_TEST_NAMES_THE_SLUG (generic: test_program_pricing_reconciliation)"
        rows.append(_row(
            canonical_slug=slug, row_layer=LAYER_RATE, row_kind="PROGRAM", aliases=", ".join(ident.aliases), jurisdiction=jur(slug), program_name=ident.program_name,
            program_type=ident.program_type or "", live_registry_inclusion="identity, rate-registry" + (", doctrine" if m["get_doctrine"](slug) else "") + (", coverage" if slug in acr.COVERAGE_REGISTRY else "")
            + (", requirements" if prof is not None else "") + (", stacking" if stack_summary != "no named pair rule" else ""),
            authority_disposition=f"{disp} / coverage {cov}", rate_status=rate_status, rate_value_basis=basis,
            qpe_territorial_status=f"QPE {dims.get('QPE_DEFINITION')}; territoriality {dims.get('TERRITORIALITY')}; min spend {dims.get('MINIMUM_SPEND')}; cap {dims.get('CAP')}; "
                                   f"resident/non-resident {dims.get('RESIDENT_NONRESIDENT_TREATMENT')}; payroll {dims.get('PAYROLL_TREATMENT')}",
            authority_completeness=(f"{ac.gate}" + (f": unresolved {', '.join(dims_open)}" if dims_open else "")),
            qualification_status=qual, stacking_status=stack_summary + (f"; UNRULED same-scope partners: {', '.join(sorted(unruled_by[slug]))}" if slug in unruled_by else ""),
            temporal_status=_temporal(m, slug, True), canonical_owner=owner(slug, True),
            served_consumer="canonical_evaluation -> allocation_pricing.price_segment -> canonical_production_view" + (f" (candidacy blocked: {acr.economic_block_for_program(slug).classification})" if acr.economic_block_for_program(slug) else ""),
            defect_classification=principal, repair_commit_or_file="; ".join(f"{c}: {w}" for c, _y, w, _t in REPAIRS.get(slug, [])), focused_test=refs_s,
            terminal_disposition=terminal, residual_evidence_needed=need))
        for cls, pid, what, nd in findings:
            props.append(_row(canonical_slug=slug, row_layer=LAYER_PROPOSITION, row_kind="PROPOSITION", proposition_id=pid, jurisdiction=jur(slug), program_name=ident.program_name,
                              defect_classification=cls, rate_value_basis="not established" if cls in (C_DATA_MISSING, C_FACT) else "",
                              canonical_owner=owner(slug, True), served_consumer=("producer-facts: " + next((f["writer"] + " | " + f["unknown_semantics"] + " | fingerprint " + f["fingerprint"] + " | UI " + f["ui_control"]
                                                                                                     for f in facts if pid == "FACT:" + f["key"]), "")) if pid.startswith("FACT:") else "",
                              repair_commit_or_file=pid.replace("REPAIRED:", "") if pid.startswith("REPAIRED:") else "", focused_test=refs_s,
                              terminal_disposition=("REPAIRED" if pid.startswith("REPAIRED:") else f"OPEN_{cls}"), residual_evidence_needed=nd, qualification_status=what))

    # ── COVERAGE_ONLY ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    cov_class = {
        "UNPRICEABLE_AUTHORITY_INSUFFICIENT": (C_DATA_MISSING, "OPEN_CANONICAL_DATA_MISSING", "primary rate, base, cap, threshold and timing authority; a RateRule promotes it (a new batch, not a repair)"),
        "NON_GUARANTEED_SELECTIVE": (C_CONSUMED, "NOT_PRICED_BY_DESIGN", ""),
        "NON_ECONOMIC": (C_CONSUMED, "NOT_PRICED_BY_DESIGN", ""),
        "SUPERSEDED": (C_CONSUMED, "NOT_PRICED_BY_DESIGN", ""),
        "DUPLICATE": (C_CONSUMED, "NOT_PRICED_BY_DESIGN", ""),
        "NO_CURRENT_INCENTIVE": (C_CONSUMED, "NOT_PRICED_BY_DESIGN", ""),
        "CANONICAL_DATA_HANDOFF_DEFECT": (C_DISCONNECTED, "OPEN_EXISTS_BUT_DISCONNECTED", "a canonical identity binding (the only same-jurisdiction runtime program is a demonstrably different statutory program)"),
    }
    for slug in u["coverage_only"]:
        ident, cov = ids[slug], acr.coverage_state(slug)
        cls, term, need = cov_class.get(cov, (C_DATA_MISSING, "OPEN_CANONICAL_DATA_MISSING", "classify the coverage state"))
        rec = acr.COVERAGE_REGISTRY.get(slug)
        rows.append(_row(
            canonical_slug=slug, row_layer=LAYER_COVERAGE, row_kind="PROGRAM", aliases=", ".join(ident.aliases), jurisdiction=jur(slug) or (rec.jurisdiction if rec else ""), program_name=ident.program_name,
            program_type=ident.program_type or "", live_registry_inclusion="identity, coverage", authority_disposition=f"coverage {cov}",
            rate_status="no RateRule: not priced (" + acr.STATE_REASON.get(cov, "")[:120] + ")", rate_value_basis="not established", qpe_territorial_status="not applicable (not priced)",
            authority_completeness=m["pub"].authority_completeness(slug).gate,
            qualification_status="NO_PROFILE", stacking_status=_stack_status(m, slug)[0], temporal_status=_temporal(m, slug, False), canonical_owner=owner(slug, False),
            served_consumer="canonical_production_view: visible with its coverage reason" + ("; candidacy blocked" if acr.blocks_economic_candidacy(slug) else "; surfaced as a pursuable opportunity, guaranteed value zero" if cov == "NON_GUARANTEED_SELECTIVE" else ""),
            defect_classification=cls, repair_commit_or_file="; ".join(w for _c, _y, w, _t in REPAIRS.get(slug, [])), focused_test=", ".join(refs.get(slug, [])) or "tests/test_na_canonical_reconciliation.py",
            terminal_disposition=term, residual_evidence_needed=need))

    # ── STACK_SPELLING ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    for s in u["stack_spellings"]:
        n = u["stack_pair_counts"][s]
        if s == "ca_qc_qprdp":
            cls, term, need = C_DISCONNECTED, "OPEN_EXISTS_BUT_DISCONNECTED", "an identity ruling and retirement of the conflicting legacy 'conditional' rule (QPRDP-IDENTITY)"
        else:
            cls, term, need = C_DATA_MISSING, "OPEN_CANONICAL_DATA_MISSING", "a canonical identity and rate/award record for the program (promotion is a separate commissioned batch); its pair rules are retained and consumed only after promotion"
        rows.append(_row(canonical_slug=s, row_layer=LAYER_STACK, row_kind="PROGRAM", jurisdiction="NA (stack registry spelling)", program_name=s,
                         live_registry_inclusion="stacking registry only", authority_disposition="no canonical identity", rate_status="no RateRule", rate_value_basis="not established",
                         stacking_status=f"{n} named pair rule(s) retained, unreachable from canonical programs", canonical_owner="optimization.stacking_rules._SLUG_PAIR_RULES",
                         served_consumer="none (not a priced program); the legacy catalog path may read the rule", defect_classification=cls, focused_test="tests/test_na_canonical_reconciliation.py",
                         terminal_disposition=term, residual_evidence_needed=need))

    # ── CATALOG_ENTRY ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    by_name = defaultdict(list)
    for slug, i in ids.items():
        by_name[_norm(i.program_name)].append(slug)
    by_state: dict[str, list[str]] = defaultdict(list)
    for slug in u["rate_bearing"]:
        by_state[jur(slug)].append(slug)
    gi_entries = {(p.jurisdiction_code, p.program_name): p for p in m["gi"].ALL_PROGRAMS if is_na_code(p.jurisdiction_code)}
    for code, name in u["catalog"]:
        key = (code, _lower(name))
        kind, targets, note = None, (), ""
        if key in CATALOG_OVERRIDES:
            kind, targets, note = CATALOG_OVERRIDES[key]
        elif len(by_name.get(_norm(name), [])) == 1:
            kind, targets, note = "LINK", (by_name[_norm(name)][0],), "exact normalized program-name match"
        elif code.startswith("US-") and len(by_state.get(code, [])) == 1:
            kind, targets, note = "LINK", (by_state[code][0],), "the single rate-bearing program of this state"
        else:
            kind, note = "UNMAPPED", "no canonical identity found by name, override or state"
        p = gi_entries[(code, name)]
        cls = C_CONSUMED
        term = "LINKED_TO_CANONICAL_PROGRAM"
        need = ""
        if kind in ("NO_RECORD", "UNMAPPED"):
            cls, term, need = C_DATA_MISSING, "OPEN_CANONICAL_DATA_MISSING", "a canonical identity and rate/award record (a separate commissioned batch)"
        elif kind == "OPEN_IDENTITY":
            cls, term, need = C_DISCONNECTED, "OPEN_EXISTS_BUT_DISCONNECTED", "an identity binding between the catalog label and the canonical program"
        elif kind == "COMPOSITE" and ("no canonical identity" in note or "unbound" in note):
            cls, term, need = C_DATA_MISSING, "OPEN_CANONICAL_DATA_MISSING", "the component named in the note has no canonical identity"
        else:
            tgt = [t for t in targets]
            if any(acr.coverage_state(t) in ("UNPRICEABLE_AUTHORITY_INSUFFICIENT", "CANONICAL_DATA_HANDOFF_DEFECT") for t in tgt):
                cls, term, need = C_DATA_MISSING, "OPEN_CANONICAL_DATA_MISSING", "the linked canonical program carries no defensible rate or award basis"
        rows.append(_row(canonical_slug=", ".join(targets) or f"catalog:{code}:{_norm(name)[:60]}", row_layer=LAYER_CATALOG, row_kind="CATALOG", jurisdiction=code, program_name=name, program_type=p.program_type,
                         live_registry_inclusion="global_inventory catalog" + (", identity" if targets else ""), authority_disposition=note, rate_status=f"catalog base {p.base_rate} max {p.max_rate} ({p.confidence_tier}); not an economic source",
                         rate_value_basis="not established", canonical_owner="global_inventory (discovery catalog; carries no program_slug)", served_consumer="legacy catalog/discovery path only; the canonical path reads the linked identity",
                         defect_classification=cls, focused_test="tests/test_na_canonical_reconciliation.py", terminal_disposition=term, residual_evidence_needed=need,
                         proposition_id=kind))

    # ── RESIDUAL propositions not attached to a single program's own findings ────────────────────────────────────────────────────────────────────────────────────────────────────
    for r in RESIDUALS:
        if r["slug"] in ids and r["slug"] in u["rate_bearing"]:
            continue   # already a proposition of its program row
        props.append(_row(canonical_slug=r["slug"], row_layer=LAYER_PROPOSITION, row_kind="PROPOSITION", proposition_id="RESIDUAL:" + r["id"], defect_classification=r["cls"],
                          qualification_status=r["what"], served_consumer=r["treatment"], terminal_disposition=("RETIRED_SUPERSEDED" if r["cls"] == C_SUPERSEDED else f"OPEN_{r['cls']}"),
                          residual_evidence_needed=r["need"], canonical_owner="PROJECT_RULES residual inventory (frozen)"))
    return rows + props


def summary(matrix: list[dict] | None = None) -> dict:
    matrix = matrix or build_matrix()
    u = frozen_universe()
    progs = [r for r in matrix if r["row_kind"] == "PROGRAM"]
    return {
        "recon_version": RECON_VERSION, "as_of": AS_OF,
        "denominator": {"canonical_na_programs": len(u["rate_bearing"]) + len(u["coverage_only"]), "rate_bearing": len(u["rate_bearing"]), "coverage_only": len(u["coverage_only"]),
                        "stack_spellings_not_canonical": len(u["stack_spellings"]), "na_catalog_entries": len(u["catalog"]),
                        "canonical_identity_layer_total_all_regions": len(u["identities"])},
        "rows": {"program_rows": len(progs), "catalog_rows": sum(1 for r in matrix if r["row_kind"] == "CATALOG"), "proposition_rows": sum(1 for r in matrix if r["row_kind"] == "PROPOSITION"), "total": len(matrix)},
        "program_class_counts": dict(Counter(r["defect_classification"] for r in matrix if r["row_kind"] == "PROGRAM" and r["row_layer"] in (LAYER_RATE, LAYER_COVERAGE))),
        "program_terminal_counts": dict(Counter(r["terminal_disposition"] for r in matrix if r["row_kind"] == "PROGRAM" and r["row_layer"] in (LAYER_RATE, LAYER_COVERAGE))),
        "authority_completeness_counts": dict(Counter(r["authority_completeness"].split(":")[0] for r in progs if r["row_layer"] == LAYER_RATE)),
        "stack_spelling_class_counts": dict(Counter(r["defect_classification"] for r in matrix if r["row_layer"] == LAYER_STACK)),
        "catalog_class_counts": dict(Counter(r["defect_classification"] for r in matrix if r["row_kind"] == "CATALOG")),
        "proposition_class_counts": dict(Counter(r["defect_classification"] for r in matrix if r["row_kind"] == "PROPOSITION")),
    }
