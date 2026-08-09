# Canonical Rule Adjudication — Little Utopia — MU / MT / GR / GB / AU

**Status:** Research/specification only. No code, rule data, project data, or optimizer output was
modified to produce this document.
**Inputs used:** `docs/validation/gemini_authoritative_qpe_validation.md` (repo root, "FULL SECOND
PASS", most current committed version — HEAD `16072a9`); the five packages' `responses/openai.json`
(the completed Codex authoritative research — no separate narrative artifact exists in the tracked
repo, so the Bridge `ReviewResponse` files are the located, completed Codex output per this task's own
fallback instruction); the five packages' `responses/claude.json` and `responses/gemini.json`, and
`reconciliation.json`, used as supporting diagnostic context only, never as authority; and direct,
targeted inspection of the actual served calculation code under `frametax2/backend/app/calculators/`
and `frametax2/backend/app/data/`.
**A repo-layout note that matters for anyone re-running this:** the CineGlobe app lives at
`frametax2/` as a plain subdirectory of this git repository (`/Users/Suraj/cineglobe-frametax`) — it
has no `.git` of its own. `docs/validation/` (this file's own directory) is a repo-root-level
directory, a sibling of `frametax2/`, not nested inside it. All file paths below that start with
`frametax2/backend/...` are relative to repo root; the Bridge run directories referenced are
gitignored and live at `frametax2/backend/.bridge_runs/`.

---

## 0. Root-cause classification key

Every item below is tagged **VERIFIED** (confirmed by direct reading of the actual served code/data —
not inferred), **LIKELY** (strong circumstantial evidence, one more direct check would close it), or
**UNVERIFIED** (a reviewer claim not yet checked against CineGlobe's own stored data or a primary
source). Layer tags follow the taxonomy this task specified: RULE/DATABASE DATA, QUALIFICATION/GATING,
QPE CLASSIFICATION, RATE/UPLIFT, CAP/THRESHOLD, TERRITORIALITY, CALCULATOR, NPC/ECONOMICS, STRUCTURE
GENERATION, OPTIMIZER/RANKING, TRACE/PACKAGE ONLY.

---

## 1. Systemic findings (apply across jurisdictions — read this section first)

### 1.1 The $9,066/$9,068 gross-budget-vs-QPE-trace gap — **FALSE POSITIVE / EXPLAINED — VERIFIED**

All three reviewers, and the prior Claude/Bridge reconciliation, flagged an unexplained difference
between `economics.gross_budget_usd` ($4,364,393.00) and the sum of every `budget_qpe_trace` line
(uniformly $4,355,327.00) in all five packages. This task's brief predicted the cause: an
"LA-designated budget line intentionally excluded as non-local spend." **Confirmed true, with primary
evidence from the production's own real budget document.**

- `frametax2/backend/app/data/little_utopia_real_budget.py` lines 99–107: account codes `5000
  EDITORIAL ($9,068.00)`, `5100 EDITORIAL - USA`, `5200 SOUND POST PRODUCTION`, `5300 PICTURE POST
  PRODUCTION`, `5400 GRAPHICS/TITLES/STOCK FOOTAGE`, `5500 DELIVERABLES`, `6500 USA ADMIN COSTS`. The
  code comments quote the production's own budget-document headers directly: `5000` "budget header
  states 'PICTURE EDIT: LA'"; `5200` "header states 'SOUND EDIT: LA'"; `5100`/`6500` state "USA" in
  their own account names.
- These seven accounts are allocated, by the production's own real budget, to a non-claiming `US`
  segment (`allocated_usd=$9,068.00`, `claims_incentive=False`, `qpe_usd=$0.00`) — confirmed directly
  against the served `ALLOC-BASELINE-MU` structure's second segment. This segment is real and correct;
  it is simply never surfaced into the exported Bridge package's `budget_qpe_trace` (which only carries
  the claiming jurisdiction's own segment).
- Residual: $9,068.00 (real) vs. $9,066.00 (the gap as observed from `gross_budget_usd −
  sum(trace)`) — a $2.00 difference, consistent with ordinary sub-line rounding across 44 accounts.
  Immaterial.

**Action required: none on the calculation.** This also retroactively explains an item from the prior
independent Claude review (no post-production category anywhere in the 37-line trace) — post-production
exists in the real budget and is deliberately excluded because it is designated to occur in
Los Angeles/USA, not in any of the five candidate jurisdictions. **Genuinely worth fixing: package
export completeness** — `frametax2/backend/app/bridge/package_builder.py`'s `build_package()` does not
surface non-claiming segments (or even their existence) into the exported package at all, which is why
every external reviewer had to treat this as a mystery. Layer: **TRACE/PACKAGE ONLY**.

### 1.2 Development (1000, $0.00) and Marketing (7300, $0.00) — **FALSE POSITIVE for THIS production — VERIFIED**

Both the Gemini and Codex authoritative reports treat "Development included" and "Marketing included"
as the most severe systemic defects across all five jurisdictions, each estimating a QPE overstatement.
**Both accounts are budgeted at exactly $0.00 in Little Utopia's real budget**
(`little_utopia_real_budget.py` lines 72, 111). Whatever the correct RULE is for these categories in
each jurisdiction (a genuine, separate question — see §7 ledger), **applying it changes Little Utopia's
QPE by $0.00 in every one of the five jurisdictions.** This is not "missing evidence treated as an
error" in reverse — it is a real rule question with zero dollar consequence for this specific,
already-served result. Layer: **QPE CLASSIFICATION (rule question, financially inert for this
production)**.

Note for completeness: `7100 PUBLICITY` ($24,348.00) is *not* the same thing as `7300 MARKETING` and
should not be conflated with it. The real line-item detail behind `7100` (Stills Photographer + EPK
crew/equipment/edit — see `little_utopia_real_budget.py` lines 176–183) is production crew and
equipment, not audience-facing marketing; CineGlobe deliberately classifies it as `btl_crew_labor`, not
as a marketing/publicity spend category, with the reasoning documented inline. No reviewer specifically
flagged 7100, but if a future pass conflates "Publicity" with "Marketing" by label alone, that would be
a new, real classification error — flagged here pre-emptively.

### 1.3 NPC omits local-cost/travel/in-kind deltas — **RESOLVED: package-export bug only, NOT a calculator or optimizer defect — VERIFIED**

The prior Claude/OpenAI reconciliation classified this as a likely-to-confirmed calculator defect
(UK $487,020, AU $367,540, GR $426,340, MT $133,120 of local-cost+travel deltas allegedly missing from
NPC). **Direct code inspection shows the calculator computes both figures correctly, and the real
ranking/optimizer already uses the correct one. The defect is a single line in the Bridge package
export, not in the deterministic engine.**

- `frametax2/backend/app/calculators/allocation_pricing.py` (`price_allocated_structure`, lines
  505–509): `npc_verified_usd = gross_budget − selected_incentive + financing + implementation` (no
  deltas); `npc_with_adjustments_usd = npc_verified + (travel + fx + inkind_replacement +
  local_cost)`. **Both are computed and stored** on `AllocatedStructurePricing` — this is not an
  omission, it is two deliberately distinct figures.
- `frametax2/backend/app/calculators/allocation_pricing.py` (`rank_allocated_structures`, line 710):
  the REAL ranking — the one that actually produces `structures_considered[].rank` and drives the
  served UI — sorts on `p.npc_with_adjustments_usd` as its documented primary key ("Financial ranking
  over FULLY PRICED structures only (verified NPC with adjustments, ascending)"). **The optimizer is
  already correct.**
- `frametax2/backend/app/bridge/package_builder.py` line 139: `npc_usd=structure.get("npc_verified_usd")`
  — **this is the actual, sole, one-line defect.** The Bridge package export picks the pre-adjustment
  figure for its single `economics.npc_usd` field, discarding the already-computed, already-correct
  `npc_with_adjustments_usd`. External reviewers, who can only see the exported package, correctly
  detected the exported number looked wrong; they had no way to know the real calculator and the real
  ranking never made this mistake.
- A secondary, cosmetic finding: `economics.ranking_basis` (`"lowest_defensible_net_production_cost"`)
  is a **static pydantic field default** in `frametax2/backend/app/bridge/schema.py` line 215, not a
  live description of the real ranking algorithm. It happens to describe the real ranking accurately
  (`rank_allocated_structures` genuinely does rank on lowest NPC-with-adjustments), but it is not wired
  to verify that description — a future change to the real ranking key would not update this string.

**Action required:** fix `package_builder.py` line 139 to use `npc_with_adjustments_usd` (or expose
both, clearly labeled). **Do not touch `allocation_pricing.py` or the ranking function — they are
already correct.** Layer: **TRACE/PACKAGE ONLY**, not OPTIMIZER/RANKING, not CALCULATOR.

### 1.4 Rate-band ceiling is always served, without checking whether the uplift condition is met — **CONFIRMED, systemic — VERIFIED**

`allocation_pricing.py`'s `price_allocated_structure` (comment above line 494): "Canonical
optimization contract (Phase 5): rank/serve on the BEST-SUPPORTED modeled incentive (`total_ceiling =
rr.modeled_rate`)... not the conservative floor." This is a deliberate, documented design choice — the
floor-rate NPC is preserved separately as `npc_conservative_usd` for "uncertainty," but the number
actually served and ranked always assumes every discretionary/conditional uplift is granted.

This is financially inert where the underlying rate is genuinely **flat** (Greece: `gr-flat-40`,
`is_band_ceiling=False` — no condition at all) or where the uplift's own stated condition is
objectively satisfied by Little Utopia's known facts (Mauritius's 40% tier: `min_qpe_usd=$1,000,000`,
feature film — Little Utopia's MU-segment QPE is $4,355,327 and it is a feature film, so the condition
IS met; see §2). It is **not** inert where the uplift condition is a *discretionary, unscored*
determination CineGlobe has no fact to evaluate — confirmed concretely for Malta (§3) and (for a
different, unconfirmed-source reason) the UK's VFX uplift (§5).

Layer: **RATE/UPLIFT (systemic design pattern; correct in some cases, wrong in others depending on
whether the jurisdiction's specific condition is a checkable fact or an unscored discretionary
judgment)**.

### 1.5 Contingency architecture already exists — do not build a new one

Section 5 of this task's brief asks for the "correct architecture" separating (A) budgeted reserve, (B)
expected draw, (C) actual incurred contingency-funded expenditure, and (D) jurisdiction-qualified
portion of that expenditure. **This architecture is already fully built and already correct** —
`frametax2/backend/app/calculators/contingency_treatment.py` (`ContingencyAllocation`,
`ContingencyDeployment`, `expand_contingency_lines`). A producer-recorded `ContingencyDeployment` moves
part of a contingency reserve into a real destination account; the deployed amount then "inherits the
RECEIVING line's own eligibility, cap, residency, location, and exclusion treatment — priced exactly as
if it had always been native spend in that destination category." The undeployed remainder keeps its
own default (or program-specific override) contingency treatment. No blanket include/exclude switch
exists anywhere in the module; every dollar's fate is either the per-program statutory rule for
`spend_category="contingency"` or the per-program rule for the deployment's destination category.

**This is the correct architecture already. It is simply never exercised for Little Utopia** — no
`ContingencyAllocation`/deployment records exist for this production, so its one $301,131.00 contingency
line is priced entirely under each jurisdiction's own DEFAULT contingency rule (see §2–§6 per
jurisdiction). This is a **STRUCTURE-DISCOVERY / feature-adoption gap** (a real, already-shipped
capability that isn't being offered to the user for this production), not a missing architecture. Per
this task's explicit instruction, no UI/controls are specified or built here.

### 1.6 Territoriality is enforced structurally (by allocation), not by vendor-level verification

`allocation_pricing.py`'s `price_segment` constructs `ProductionFacts(... accounts_outside_jurisdiction
=frozenset())` with the comment: "By construction every allocated line is incurred IN this segment's
jurisdiction — the allocation, not a fact set, is what keeps other jurisdictions' spend out of this
register." Confirmed: no line in any of the five packages' `budget_qpe_trace` carries a populated
`component` field (vendor location, import/local split, etc. — all 185 lines across the five packages
are `component: null`), matching what every external reviewer already flagged as a local/non-local
evidence gap. This is a genuine, real limitation: the system's territoriality guarantee currently rests
on "this account was allocated to jurisdiction X" as a modeling proxy for "this money was spent in
jurisdiction X," with no independent vendor/component check. **Per this task's explicit instruction, no
assumption is made here that routing payment through a local entity by itself legitimizes foreign
spend** — this is recorded as an open architectural gap, not resolved either way. Layer:
**TERRITORIALITY**, status **VERIFIED gap** (the absence of vendor-level data is directly confirmed;
whether it produces an actual wrong dollar for Little Utopia is **UNVERIFIED** — no evidence either way).

### 1.7 Structure-discovery: no treaty/co-production or hybrid structures generated — CONFIRMED gap, map only

Direct query of the 177 real structures generated for Little Utopia (`build_allocated_structures`):
`{'full_relocation': 88, 'component_relocation': 88, 'single_country': 1}`. **Zero**
`treaty_coproduction`, `majority_minority`, `multi_party`, or `hybrid` structures were generated, even
though `allocation_pricing.py`'s `_treaty_requirements()` explicitly supports pricing all four of those
`structure_type`s once one exists. The 88 `component_relocation` structures are all
post-production-only relocations of the MU baseline (`ALLOC-COMPONENT-POST-*`), confirming that
component-level (not just whole-production) restructuring IS already modeled — just never as a
treaty/co-production or hybrid/anchor structure. This is a real, verified STRUCTURE GENERATION gap.
**Per this task's explicit instruction, not investigated further and not fixed in this pass** — flagged
for a dedicated future structure-generation task. No Script Analyzer or invented script-derived input is
implicated; this is about known production variables (jurisdiction, budget, treaty eligibility) already
available to CineGlobe.

---

## 2. Mauritius (MU) — program `mu_edb_incentive`

| Question | Authoritative rule (as already verified in CineGlobe's own data) | CineGlobe stored rule/data | Calculator/gating code | Served Little Utopia result | Status |
|---|---|---|---|---|---|
| Base vs. conditional 40% | EDB Film Rebate Scheme: 30% general tier (`min_qpe_usd=$100,000`); 40% tier requires **feature film production company AND minimum QPE $1,000,000** (`program_rate_rules.py` `mu_frs_40_feature`, `confidence_tier` implied VERIFIED via primary EDB Submission Procedures text) | `MU_RATE_RULES`: two `RateRule`s, `mu_frs_30_general` (0.30) and `mu_frs_40_feature` (0.40, `is_band_ceiling=True`) | `allocation_pricing.price_segment` → `resolve_program_rate(..., qpe_usd=qpe)` selects the ceiling tier when its `min_qpe_usd` is met | MU segment QPE = $4,355,327.00, feature film → 40% condition **is objectively satisfied**; served rate = 40% | **CONFIRMED CORRECT — VERIFIED.** Not a defect. Contradicts Codex/Gemini's generic "assumes max rate without checking uplift" claim as applied to MU specifically. |
| Unverified 90%-local-filming claim | A secondary (non-government) source claims the 40% tier additionally requires 90% of filming in Mauritius | `MU_UNVERIFIED_CLAIMS` in `program_rate_rules.py`: explicitly logged as "NOT FOUND in EDB Submission Procedures... or MCCI guidance," status unresolved | Not enforced (correctly — no primary-source support exists to enforce it) | 40% served without this condition checked | **UNRESOLVED / project-dependent — see §7 ledger.** Not a defect: CineGlobe's own default-inclusion doctrine correctly does not invent an unconfirmed gate. |
| Contingency (8300, $301,131.00) | No clause in the primary EDB source (31 Jan 2020 Submission Procedures, the "33-item illustrative list") excludes a contingency reserve; the document's express exclusion clause applies **only to Digital Animation projects**, not Motion Pictures | `program_spend_rules.py` `_MU_CONTINGENCY_NOTE`, `confidence_tier="VERIFIED"`, `source_ref="EDB-2020-QPE-List"` — explicit, reasoned, already-cited INCLUDE | `qualification_derivation.py` ladder applies the per-program override (INCLUDE) ahead of the general default-exclude-by-`structural_definition` rule | Included at full value, $301,131.00 → $120,452.40 incentive contribution | **CONFIRMED CORRECT — VERIFIED.** Gemini's Bridge-review recommendation to exclude MU contingency is a **FALSE POSITIVE** — it cites general reasoning ("unspent reserve"), not Mauritius-specific statutory text, and CineGlobe already has the specific, cited, reasoned Mauritius answer. **Per this task's explicit instruction, Gemini's recommendation must NOT become a rule — confirmed here as the correct outcome, not merely deferred.** |
| Completion bond (8200, $0.00) | Same reasoning as contingency — no exclusion found in the primary source; category match itself flagged as uncertain | `_MU_COMPLETION_BOND_NOTE`, `VERIFIED`, included | Same ladder | $0.00 — financially inert | **CONFIRMED CORRECT (financially inert).** |
| Development (1000, $0.00) | Genuine open question (see §1.2) | `atl_writer` category, `explicit_statute` (via the labor/crew QPE category, per `_MU_LABOR_NOTE`) | Included | $0.00 | **FALSE POSITIVE for this production — see §1.2.** |
| Budget-evidenced 35% rate | Little Utopia's own real budget document line states "EDB Rebate at 35%: $(1,275,411)" | `MU_BUDGET_EVIDENCED_RATES` in `program_rate_rules.py` — logged as budget-evidenced, explicitly NOT statute-verified | Not used by the calculator (statutory 30%/40% tiers are used instead) | Served rate is 40%, not the production's own assumed 35% | **UNRESOLVED / project-dependent — see §7 ledger.** A genuine three-way discrepancy (guaranteed floor 30%, production's own budget assumption 35%, CineGlobe's statutory ceiling 40%) worth disclosing to the user, not silently resolved either way. |
| Territoriality | QPE must be incurred "locally" (quoted directly in `mu30-qpe-local` condition) | Structural — see §1.6 | Same | No vendor-level local/foreign split exists for MU's segment | **Same systemic gap as §1.6 — not MU-specific.** |

---

## 3. Malta (MT) — program `mt_mfc_rebate`

| Question | Authoritative rule | CineGlobe stored rule/data | Calculator/gating code | Served result | Status |
|---|---|---|---|---|---|
| Base vs. conditional 40% | MFC Cash Rebate Guidelines (Jan 2019), S.3.2.1: general base 30%; **"The Commissioner has the discretion to award an additional [uplift] based on the Maltese cultural elements and on the maximisation of local resources. Maximum Rebate: 40%"** — an explicitly discretionary, criteria-based uplift, not automatic | `MT_RATE_RULES`: `mt-general-30` (0.30, not a ceiling) and `mt-general-ceiling-40` (0.40, `is_band_ceiling=True`, `RateCondition(kind="discretionary_band", ...)` quoting the Commissioner-discretion language verbatim) | Same "select the ceiling" contract as §1.4 — the discretionary condition is recorded as data but never evaluated before selecting the ceiling | Served rate = 40%, unconditionally | **CONFIRMED DEFECT — VERIFIED.** Unlike Mauritius, Malta's uplift condition is genuinely discretionary and criteria-based (cultural elements + local-resource maximization), and CineGlobe's own Bridge package for Malta shows `cultural_test_points=null` — the fact needed to evaluate it does not exist. Serving 40% as settled fact overstates the incentive; the guaranteed base is 30%. Layer: **RATE/UPLIFT.** Financial exposure: $1,621,678.40 (served, 40%) vs. $1,216,258.80 (guaranteed floor, 30%) — a **$405,419.60** overstatement if the uplift is not actually granted. |
| Contingency (8300) | MFC guidance has no MT-specific SpendRule override located in this pass (general default applies) | `structural_definition` default (undeployed reserve = not incurred expenditure) applies — same general-default reasoning as every non-MU jurisdiction | Ladder default | Excluded | **LIKELY CORRECT** (consistent, reasonable default; not independently confirmed against a Malta-specific citation in this pass — see §7 ledger for the general-default-vs.-jurisdiction-statute distinction). |
| Cultural test / minimum spend | S.2.3: min Malta spend EUR 100,000 ($113,000), overall budget > EUR 200,000; cultural test required, 40-pt threshold named in `qualification.cultural_test_criteria` | `min_qpe_usd=113,000` on both tiers; `cultural_test_required=True` (per `program_requirements.py`) | Minimum-spend condition is checkable and met ($4.05M ≫ $113,000); cultural test scoring itself is not run (no `cast_writer_director_facts`/`script_treatment_metadata` populated for Little Utopia) | `cultural_test_points=null` | **CONFIRMED GAP — VERIFIED absence of input data, not a rule defect.** See §7 ledger — project-dependent (needs real cast/crew/nationality/content facts). |
| Development/Marketing | Same as §1.2 | — | — | $0.00 both | **FALSE POSITIVE for this production.** |

---

## 4. Greece (GR) — program `gr_cash_rebate`

| Question | Authoritative rule | CineGlobe stored rule/data | Calculator/gating code | Served result | Status |
|---|---|---|---|---|---|
| 40% rate | Flat 40% cash rebate — `GR_RATE_RULES` has **exactly one** tier, `gr-flat-40`, `is_band_ceiling=False`, no discretionary condition | `min_qpe_usd=114,052.40` (EUR 100,000) | Rate resolves directly, no ceiling-selection ambiguity applies | Served rate = 40% | **CONFIRMED CORRECT — VERIFIED.** Unlike MU/MT, Greece's rate is genuinely unconditional once minimum spend is met (comfortably true: $4.05M ≫ $114,052.40). The §1.4 "ceiling served without checking the condition" pattern does **not** apply here because there is no condition to check. |
| 80% eligible-spend cap | Codex's and Gemini's narrative reports both assert an "80% of total production budget" cap on eligible spend | **Not located in this pass.** `GR_RATE_RULES`' own citation states only that "annual program allocation exists but the specific cap is not publicly confirmed" — a different thing (a government-wide annual pool ceiling, not a per-production 80%-of-budget spend cap) | No 80%-of-budget cap mechanism exists anywhere in the calculator for any jurisdiction (confirmed absent generally — see GB below, where an equivalent cap IS confirmed and is explicitly disclosed as "not modeled") | No cap applied | **EVIDENCE/AUTHORITY GAP — UNVERIFIED.** Per this task's explicit instruction not to perform a broad web review of all five programs, this was not independently re-researched from scratch. Enters §7 ledger. If the 80% cap is real, financial exposure is bounded by the gap between $4,054,196.00 (current QPE) and 80% of $4,364,393.00 gross budget ($3,491,514.40) — a possible **$562,681.60** QPE overstatement, pending confirmation. |
| Development (1000) | Genuine open question | `CORRECT` per the Gemini narrative report itself (development costs held eligible under Greek rules, distinguishing Greece from MU/MT/GB in that report) | Included | $0.00 | **FALSE POSITIVE for this production regardless (§1.2).** |
| Marketing (7300) | Both authoritative reports agree: strictly ineligible | No GR-specific override located; falls to the same doctrine-default handling as MU's Marketing line | Behavior not independently re-derived in this pass (would require reading the GR segment's own qualification trace line-by-line, which the Bridge package does carry) | $0.00 | **FALSE POSITIVE for this production regardless (§1.2).** |

---

## 5. United Kingdom (GB) — program `uk_avec`

| Question | Authoritative rule | CineGlobe stored rule/data | Calculator/gating code | Served result | Status |
|---|---|---|---|---|---|
| Standard AVEC rate | bfi.org.uk, fetched directly: "a taxable credit at a rate of 34% (equivalent to 25.5% under the previous system)" — net effective 25.5% after UK corporation tax, independently arithmetic-verified in-code (34% × (1−25%) = 25.5%) | `gb-avec-net-2550`, rate 0.255, `is_band_ceiling=False` | Correct base tier | — | **CONFIRMED CORRECT — VERIFIED.** |
| 80% core-expenditure cap | bfi.org.uk, quoted directly in-code: **"AVEC is available on qualifying UK production expenditure, which is the lower of either 80% of total core expenditure or the actual UK core expenditure incurred"** | Citation captured verbatim in `_GB_CITATION`, with an explicit code comment: **"(QPE-eligibility cap, not a rate cap — not modeled, no such mechanism exists in this engine)"** | **No 80%-cap mechanism exists anywhere in `allocation_pricing.py`, `qpe_calculator.py`, or `apply_caps_floors_exclusions.py`** for this or any program | QPE served at 100% of allocated GB spend, no cap applied | **CONFIRMED DEFECT — VERIFIED, and already disclosed in CineGlobe's own code comments.** This matches Codex's and Gemini's finding exactly, and CineGlobe's own authors already knew about it. Layer: **CAP/THRESHOLD.** GB's QPE is currently $4,054,196.00; 80% of GB's own core expenditure would need to be computed from GB's actual core-expenditure total (not simply 80% of gross budget, since "core expenditure" is itself a defined AVEC term) — financial impact is **not precisely calculable without first defining "core expenditure" as a CineGlobe field**, flagged for the remediation spec. |
| 10%-of-total-budget ratio condition | "at least 10% of costs spent on UK qualifying production expenditure" | `RateCondition(kind="min_spend_pct_of_total_budget")`, explicitly noted: "a ratio condition this engine has no fact to pre-evaluate (no total-worldwide-budget comparison fact available)" | Not evaluated | Assumed met | **CONFIRMED GAP — VERIFIED, disclosed in-code.** For a full relocation structure (100% of the budget in GB), this condition is almost certainly satisfied in practice, but CineGlobe has no explicit check. Low practical risk for this specific structure type; genuine gap in general. |
| VFX Additional Credit / IFTC (29.25% ceiling) | +3.75% VFX uplift effective 1 Jan 2025, reaching 29.25% net — sourced from a **secondary** source (Entertainment Partners), explicitly "NOT independently confirmed from the BFI text fetched" by this session | `gb-vfx-ceiling-2925`, `is_band_ceiling=True`, condition explicitly flagged `PARSED not VERIFIED` with the sourcing caveat in-code | Same §1.4 ceiling-always-selected contract | Served rate = 29.25%, not the VERIFIED 25.5% base | **CONFIRMED DEFECT — VERIFIED.** Two independent problems stack here: (1) the uplift's own source is admittedly unconfirmed against a primary document, and (2) even if the uplift rule itself is correct, CineGlobe has no fact confirming Little Utopia actually qualifies for VFX-uplift-eligible expenditure. Financial exposure: $1,185,852.33 (served, 29.25%) vs. $1,036,320.00 (VERIFIED base, 25.5%) — a **$149,532.33** overstatement if the uplift does not apply. This task's brief separately asked about IFTC (Independent Film Tax Credit) — **not located anywhere in the codebase in this pass**; if IFTC is a real, separate, currently-higher-rate regime for lower-budget independent films (as both authoritative reports assert), CineGlobe has not modeled it at all. Enters §7 ledger as a possible missing program, not merely a missing rate tier. |
| Cultural test | Must pass BFI cultural test or qualify as an official co-production | `requires_cultural_test=True`; `cultural_test_criteria=["GB: cultural test required"]`, `cultural_test_points=null` | Not scored (no facts) | Assumed passed | **Same pattern as Malta — see §7 ledger.** |
| Territoriality ("UK Use" rule) | AVEC replaced "UK spend" with "used or consumed in the UK" | Not independently located as a distinct modeled rule in this pass | Structural allocation only (§1.6) | — | **UNVERIFIED — not independently checked in this pass; folded into the general §1.6 territoriality gap.** |

---

## 6. Australia (AU) — program `au_location_offset`

This is the single clearest, most fully root-caused defect in the whole adjudication.

| Question | Authoritative rule | CineGlobe stored rule/data | Calculator/gating code | Served result | Status |
|---|---|---|---|---|---|
| A$20,000,000 minimum QAPE threshold | screenaustralia.gov.au (primary, official) via a corroborating secondary (c21media.net): **"A$20 million for a film"** minimum QAPE, confirmed and quoted directly in-code | **Recorded in two places, inconsistently.** `program_requirements.py` `au_location_offset` profile: `min_local_spend_usd=None` (deliberately, per the profile's own comment: *"Left min_local_spend_usd as None to avoid a false-precision FX conversion; the authoritative figure is AUD 20,000,000 (recorded in additional_facts)"*) — the real figure sits only in a free-text `additional_facts["min_qape_threshold"]` string, never in a structured, enforceable field. `program_rate_rules_worldwide.py` `AU_DOCTRINE`: `min_spend_usd=None`, same reasoning, same root cause: **"No AUD/USD FX rate exists in this project's FX_RATE_SNAPSHOTS table... the AUD $20M minimum spend threshold is NOT converted to USD (would require fabricating an unsourced FX rate); min_spend_usd is left None, disclosed explicitly."** | `resolve_program_rate(..., qpe_usd=qpe)` in the pricing kernel **does** enforce minimum-QPE gates when a `RateCondition(kind="min_qpe_usd", threshold_usd=...)` exists — proven by the ~25 OTHER jurisdictions in Little Utopia's own structure set that are correctly blocked with "statutory rate did not resolve... minimum-spend or eligibility conditions unmet" (e.g. CA-ON, CY, FR, MA, MT-post, SE, several US states). **The gating mechanism itself works.** It simply has no threshold value to check for `au_location_offset`, because that value was never populated, because of the missing FX rate. | AU is priced and ranked as a valid, fully-priced, 30%-rate structure — QPE $4,054,196.00, nowhere near AUD 20,000,000 (≈USD 13,000,000+ at any plausible AUD/USD rate) | **CONFIRMED DEFECT — fully VERIFIED, root cause fully traced.** This is a single, precise, well-understood chain: **missing AUD/USD FX rate in `FX_RATE_SNAPSHOTS` → `min_spend_usd=None` on `AU_DOCTRINE` (and `min_local_spend_usd=None` on the requirements profile) → the minimum-QPE `RateCondition` that would otherwise correctly block this segment (the same mechanism already blocking ~25 other jurisdictions) is never created → AU is priced as if fully qualified.** Layer: **RATE/CAP/THRESHOLD (data gap, not a code gap)** — the gating CODE is already correct and proven working elsewhere; only the DATA POINT is missing, and only because of one further missing data point (the FX rate) upstream of it. Little Utopia is very likely genuinely **ineligible** for the Location Offset at its current budget. Financial impact: the entire AU incentive, $1,216,258.80, and the entire AU structure's validity as a rankable candidate. |
| No cultural/content test for Location Offset (distinct from Producer Offset) | Confirmed: "Location Offset specifically has none — that's the separate Producer Offset" | `requires_cultural_test=False` (correct) | Correctly not gated | Correctly not gated | **CONFIRMED CORRECT.** |
| Training/skills obligation | "the reformed offset also carries a skills-and-training obligation" | Recorded only in `additional_facts["skills_training_obligation"]`, free text, no structured field or gate | Not enforced | Not enforced | **CONFIRMED GAP — VERIFIED absence, same free-text-only pattern as the $20M threshold.** Not independently financially quantifiable without further primary-source detail on what the obligation actually requires. Enters §7 ledger. |
| Location Offset / PDV Offset / Producer Offset mutual exclusivity | "These three offsets are mutually exclusive" (Screen Australia, official, directly fetched) | Recorded as a `RateCondition(condition_id="au-mutually-exclusive")` | Only `au_location_offset` is modeled as a claimable program for Little Utopia's AU structures — no double-claim risk exists in the served result | — | **CONFIRMED CORRECT (no violation possible in the current served result).** |
| Territoriality (QAPE = Australian-incurred spend) | Standard | Structural (§1.6) | Same systemic gap | — | **Same as §1.6 — not AU-specific.** |
| FX delta = $0.00 | — | Same missing-AUD-rate root cause as the threshold above | `compute_fx_normalization` returns no delta when no rate is on file — correctly disclosed, not fabricated | `fx_delta_usd=$0.00` | **CONFIRMED CORRECT BEHAVIOR given the missing input — not a separate defect, same root cause as the threshold gap above.** Fixing the missing AUD/USD FX rate resolves both this and the threshold gap simultaneously. |

---

## 7. Layer summary — verified defects only

| # | Jurisdiction | Defect | Layer | Status | Highest-dollar exposure |
|---|---|---|---|---|---|
| 1 | AU | Missing AUD/USD FX rate → `min_spend_usd=None` on `au_location_offset` → $20M QAPE minimum never enforced | RATE/CAP/THRESHOLD (data) | VERIFIED | Entire AU incentive: **$1,216,258.80** |
| 2 | GB | 80% core-expenditure cap on QPE eligibility — quoted in evidence, explicitly "not modeled" in code | CAP/THRESHOLD | VERIFIED | Not precisely calculable without a "core expenditure" field; bounded above by the GB incentive itself |
| 3 | GB | 29.25% VFX-uplift ceiling served without confirming (a) the uplift's own primary-source support or (b) Little Utopia's VFX-uplift eligibility | RATE/UPLIFT | VERIFIED | **$149,532.33** (served 29.25% vs. verified-base 25.5%) |
| 4 | MT | 40% Commissioner-discretion ceiling served without evaluating the named discretionary criteria (cultural elements, local-resource maximization) | RATE/UPLIFT | VERIFIED | **$405,419.60** (served 40% vs. guaranteed-floor 30%) |
| 5 | All 5 | Bridge package export exposes `npc_verified_usd` instead of the already-correct `npc_with_adjustments_usd` | TRACE/PACKAGE ONLY | VERIFIED | Presentation-only; real ranking is already correct. Largest misrepresented figure: GB, $487,020 delta |
| 6 | All 5 | Bridge package never surfaces non-claiming segments (the real $9,068 US/LA post-production spend) | TRACE/PACKAGE ONLY | VERIFIED | $0 (calculation is correct; only visibility is missing) |
| — | GR | Possible 80% eligible-spend cap | CAP/THRESHOLD | UNVERIFIED | Up to $562,681.60 if real — unresolved, see ledger |
| — | GB | Possible separate IFTC program not modeled at all | RATE/UPLIFT or missing program | UNVERIFIED | Not calculable — unresolved, see ledger |

**Highest-dollar CONFIRMED (VERIFIED) defect: Australia's unenforced A$20,000,000 minimum-QAPE gate,
invalidating the entire $1,216,258.80 AU incentive and the AU structure's validity as a ranked
candidate.**

**Structure-generation defect found:** zero treaty/co-production or hybrid/anchor structures generated
for Little Utopia despite the pricing engine already supporting them (§1.7). Mapped, not investigated
further, per this task's instruction.

---

## 8. Hard gating order — current runtime vs. specification

Requested order: **QUALIFICATION/HARD GATES → QPE → RATE/CAP/UPLIFT → INCENTIVE → LOCAL/RELOCATION/
TRAVEL/IN-KIND ECONOMICS → NPC → RANKING.**

Traced against `price_segment`/`price_allocated_structure`/`rank_allocated_structures`:

1. **QPE is computed before qualification/hard-gate resolution is complete** for minimum-spend-style
   gates: `price_segment` calls `derive_qualification_register(...)` (line-by-line QPE
   classification) and computes `qpe = sum(...)` **before** calling `resolve_program_rate(...,
   qpe_usd=qpe)`, which is where a minimum-QPE hard gate (when its data exists) is actually checked.
   This is not strictly a violation of the requested order in outcome — QPE genuinely must be known
   before a QPE-denominated gate (like "$1,000,000 minimum QPE") can be evaluated — but it does mean
   the "hard gate" step is really interleaved with QPE, not cleanly prior to it, for any gate defined
   in terms of the QPE amount itself (as MU's and MT's minimum-QPE gates are, and as AU's minimum-QAPE
   gate would be if it were populated).
2. **RATE/CAP/UPLIFT**: resolved immediately after, via `resolve_program_rate`. Confirmed this is
   where AU's missing gate and MT's/GB's un-evaluated discretionary uplifts fail to block, per §2–§6.
   **No CAP mechanism exists in this step or anywhere else** — confirmed absent for GB's 80% cap (§5),
   and not confirmed present for GR (§4).
3. **INCENTIVE**: `floor_case`/`ceiling_case` via `build_risk_cases`, immediately after rate resolution.
   Correct position.
4. **LOCAL/RELOCATION/TRAVEL/IN-KIND ECONOMICS**: computed by the caller
   (`little_utopia_state.py`, `compute_travel_normalization`/`compute_local_cost_normalization`/
   `compute_fx_normalization`) and passed into `price_allocated_structure` as deltas — correctly
   positioned after per-segment incentive resolution, before NPC.
5. **NPC**: computed last inside `price_allocated_structure`, correctly incorporating the deltas from
   step 4 into `npc_with_adjustments_usd` (see §1.3 — the calculator gets this right).
6. **RANKING**: `rank_allocated_structures`, correctly keyed on `npc_with_adjustments_usd` (§1.3).

**A jurisdiction failing a hard gate does NOT currently appear as INELIGIBLE/CONDITIONAL with a
disclosed reason in every case** — this is true for the ~25 jurisdictions whose rate rules DO carry a
`min_qpe_usd` `RateCondition` (they correctly show `is_fully_priced=False` with an explicit blocker
string), but it is **false for Australia specifically**, which should be gated ineligible and is not,
solely because its threshold datum is missing (§6). This is the one place in the current runtime where
the ordering's intent ("a jurisdiction failing a hard gate must NOT appear as a valid priced/ranked
scenario") is violated in practice, and it traces to the same single root cause already identified in
§6 — not a new ordering defect.

**Conclusion: the deterministic engine's ordering is architecturally correct and matches the
specification.** The AU violation is a data-completeness failure inside step 2, not a structural
ordering defect.

---

## 9. What NOT to touch (per this task's explicit scope)

No code, jurisdiction rule data, evidence tables, project data, UI, Script Analyzer, artwork, ingestion,
or historical-evidence integration was modified to produce this document. The remediation items above
are specifications for a future implementation pass, not changes made now.
