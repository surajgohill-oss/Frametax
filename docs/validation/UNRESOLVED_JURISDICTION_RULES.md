# Unresolved Jurisdiction Rule Ledger — Little Utopia — MU / MT / GR / GB / AU

Companion to `docs/validation/CANONICAL_RULE_ADJUDICATION_MU_MT_GR_GB_AU.md`. Only items genuinely
unresolved after adjudicating the completed Claude, Codex, and Gemini authoritative research against
CineGlobe's own stored rule data and served code appear here. Confirmed defects and confirmed
false-positives are resolved in the canonical document, not repeated here.

User overrides recorded against these items must affect only the specific project/scenario they are
set on. None of them may silently rewrite the canonical jurisdiction rule tables
(`program_rate_rules_worldwide.py`, `program_rate_rules.py`, `program_requirements.py`,
`program_spend_rules.py`) — those remain the shared, cross-project source of truth.

---

## 1. Mauritius — is the 40% tier additionally conditioned on 90% local filming?

- **Exact question:** Beyond the confirmed, VERIFIED conditions (feature film, min. QPE $1,000,000),
  does the EDB Film Rebate Scheme also require at least 90% of principal photography to occur in
  Mauritius before the 40% tier applies?
- **Authoritative sources checked:** EDB "Film Rebate Scheme — Submission Procedures" (31 Jan 2020,
  the primary source already in CineGlobe's evidence base); MCCI Film Rebate Scheme page (corroborating
  secondary). Neither contains this claim.
- **Why unresolved:** The only source for this claim is a production-services/fixer website
  (identicalpictures.com), already logged in CineGlobe's own data
  (`program_rate_rules.py::MU_UNVERIFIED_CLAIMS`) as "NOT FOUND in EDB Submission Procedures... or MCCI
  guidance." No government or regulation-text source has been located confirming or denying it in any
  research pass to date, including this one (an EDB written confirmation would be required, which is
  outside this task's scope).
- **Safe CineGlobe default:** Continue not enforcing this condition (current behavior) — CineGlobe's own
  default-inclusion doctrine correctly declines to invent an unconfirmed exclusion/gate.
- **Allowed project/scenario override:** A producer or CineGlobe operator with direct EDB correspondence
  confirming or denying the 90% rule may record that as a project-level fact (e.g., a documented shoot-day
  location split), which should feed a NEW, EDB-confirmation-sourced `RateCondition` if and when the rule
  itself is verified — not a silent per-project toggle of the 40% rate.
- **Financial impact if the rule is real and unmet:** Little Utopia would drop to the 30% guaranteed
  tier: $1,742,130.80 → $1,306,598.10, a **$435,532.70** reduction.
- **Evidence needed for permanent resolution:** Direct written confirmation from the Mauritius EDB, or
  location of the actual EDB (Film Rebate Scheme) Regulation 2018 full text (only a "Submission
  Procedures" summary document is currently in CineGlobe's evidence base — see the companion item below).

## 2. Mauritius — 40% (statutory ceiling) vs. 35% (production's own budgeted assumption) vs. 30% (guaranteed floor)

- **Exact question:** Little Utopia's own real budget document assumes a 35% EDB rebate
  (`"EDB Rebate at 35%: $(1,275,411)"`, per `program_rate_rules.py::MU_BUDGET_EVIDENCED_RATES`), while
  CineGlobe's statutory reading serves 40% (the ceiling tier, whose stated conditions are met — see
  canonical §2) and the guaranteed floor is 30%. Which figure should be presented as the primary served
  number, and should the other two be surfaced alongside it?
- **Authoritative sources checked:** The same EDB primary source supports the 30%/40% statutory reading.
  No source explains why the production's own budget assumed 35% — it may reflect a real, informal EDB
  Committee indication specific to this production (the Committee process is discretionary per
  `allocation_type=DISCRETIONARY`), or simply an earlier, more conservative producer estimate.
- **Why unresolved:** This is not a rule-text question — it is a question about which of three
  differently-sourced numbers (statute-derived ceiling, guaranteed floor, and this specific production's
  own real-world planning assumption) CineGlobe should treat as authoritative for THIS project. It is
  inherently project-dependent.
- **Safe CineGlobe default:** Continue serving the statutory ceiling (40%) as the primary modeled figure
  (consistent with every other jurisdiction's ceiling-selection behavior), while disclosing the
  guaranteed floor (30%, already computed as `npc_conservative_usd`) prominently, and disclosing the
  production's own 35% budget assumption as a distinct, labeled data point (not silently overwritten or
  discarded).
- **Allowed project/scenario override:** A user may confirm (e.g., via an actual EDB Committee
  determination letter) which rate applies to THIS production specifically; that becomes a project-level
  fact, never a change to the statutory 30%/40% tier data itself.
- **Financial impact:** Between the floor and ceiling, up to **$435,532.70** (same range as item 1,
  since both conditions bear on the same rate band).
- **Evidence needed:** The production's own EDB correspondence, or an EDB Committee determination letter,
  if one exists.

## 3. Malta — what does the production actually score on the Commissioner-discretion uplift criteria?

- **Exact question:** Malta's 40% ceiling requires Commissioner discretion "based on the Maltese
  cultural elements and on the maximisation of local resources" (MFC Cash Rebate Guidelines, Jan 2019,
  S.3.2.1, quoted verbatim in CineGlobe's own data). What score or determination would Little Utopia
  actually receive?
- **Authoritative sources checked:** MFC Cash Rebate Guidelines (Jan 2019) — the guaranteed base (30%)
  and the existence of the discretionary uplift are both confirmed; the guidelines do not (as quoted in
  CineGlobe's evidence) publish a fixed, checkable points table for this specific discretionary
  criterion, unlike the UK's fully-published Cultural Test point system.
- **Why unresolved:** This is a **Commissioner-discretion determination**, not a fixed statutory formula
  — genuinely project-dependent and, per the sourced guidance itself, not fully mechanically
  determinable even in principle without an actual Commissioner decision or a more detailed guidance
  document not yet in CineGlobe's evidence base.
- **Safe CineGlobe default:** Serve the guaranteed 30% base as the primary modeled figure for Malta,
  with the 40% ceiling disclosed as a clearly-labeled upside contingent on Commissioner approval — this
  reverses current behavior (see canonical §3, confirmed defect).
- **Allowed project/scenario override:** A user with an actual MFC provisional certificate or
  Commissioner indication may record the confirmed rate as a project-level fact.
- **Financial impact:** **$405,419.60** (30% vs. 40%, already quantified in the canonical document).
- **Evidence needed:** Either a more detailed MFC guidance document that publishes explicit uplift
  scoring criteria, or an actual Commissioner determination for this production.

## 4. Malta, United Kingdom — unscored cultural tests generally

- **Exact question:** Both Malta (40-point threshold, points system not detailed in CineGlobe's current
  evidence) and the UK (BFI Cultural Test, a full published point system already exists as
  `evaluate_qualification_tests.py`'s UK scoring table) require a passed cultural test as a hard
  qualification gate. Does Little Utopia pass either?
- **Authoritative sources checked:** UK: BFI Cultural Test criteria are already fully modeled in
  `evaluate_qualification_tests.py` (18-point minimum, section minimums, full criteria list) — the
  SCORING MECHANISM exists and is correct; it is simply never invoked for Little Utopia because the
  input facts it needs (`cast_writer_director_facts`, `script_treatment_metadata`,
  `nationality_residency_facts`) are all empty for this project. Malta: no equivalent points table is yet
  in CineGlobe's evidence base at all (see item 3).
- **Why unresolved:** Genuinely project-dependent — requires real facts about Little Utopia's actual
  cast, crew, director, writer nationalities, and subject matter/setting, none of which exist in the
  project's current input data (`inputs.cast_writer_director_facts={}`,
  `inputs.nationality_residency_facts={}` in every one of the five exported packages).
- **Safe CineGlobe default:** Continue disclosing `cultural_test_points=null`/gate-unconfirmed rather
  than assuming a pass. Both segments should arguably show as CONDITIONAL (gate unconfirmed) rather than
  fully priced, pending this task's broader gating-order finding (§8 of the canonical document).
- **Allowed project/scenario override:** Populate the project's real cast/crew/director/writer/subject
  facts; the existing UK scoring engine (`evaluate_qualification_tests.py`) can then run for real.
- **Financial impact:** Up to the full UK ($1,185,852.33) and Malta ($1,621,678.40, or $1,216,258.80 at
  the safe-default 30% per item 3) incentive amounts, if either test is actually failed.
- **Evidence needed:** Real Little Utopia production facts (nationalities, subject matter, shoot-day
  splits) — a data-entry task, not a research task.

## 5. Greece — does an 80%-of-total-budget eligible-spend cap exist?

- **Exact question:** Both the Codex and Gemini authoritative reports assert Greece caps eligible spend
  at 80% of the total production budget, structurally similar to the UK's confirmed 80% core-expenditure
  cap. CineGlobe's own stored Greek rate data does not currently contain this cap.
- **Authoritative sources checked in this pass:** CineGlobe's own `GR_RATE_RULES` citation only confirms
  an unrelated annual-program-wide allocation cap ("not publicly confirmed" as to its specific amount) —
  not a per-production 80%-of-budget spend cap. No fresh primary-source research was performed in this
  pass (explicitly out of scope: "no broad web review of all five programs").
- **Why unresolved:** Two authoritative reviewers agree, but neither cites a verifiable primary Greek
  statute/regulation passage for this specific 80% figure in what was reviewed in this pass, and it was
  not independently re-derived from a primary source here.
- **Safe CineGlobe default:** Do not apply an unconfirmed cap (consistent with the system's own
  default-inclusion, never-fabricate-an-exclusion doctrine) — current behavior (no cap) stands until
  confirmed.
- **Allowed project/scenario override:** None needed unless/until the rule is confirmed; this is a
  jurisdiction-rule question, not a project-fact question.
- **Financial impact if real:** Up to **$562,681.60** QPE overstatement (current QPE $4,054,196.00 vs.
  80% of gross budget $3,491,514.40), translating to up to **$225,072.64** of overstated incentive at
  the 40% rate.
- **Evidence needed:** The actual Greek Law 4487/2017 (or its current successor) text, or an official
  EKOME/Creative Greece guidelines document that states an eligible-spend cap explicitly, with the exact
  percentage and base (total budget vs. total Greek spend vs. something else).

## 6. United Kingdom — does a separate Independent Film Tax Credit (IFTC) apply?

- **Exact question:** Both authoritative reports assert a UK Independent Film Tax Credit at a
  significantly higher rate (asserted range: 53%, or a 39%-nominal/29.25%-net figure depending on the
  report) for lower-budget independent films, as a DISTINCT program from standard AVEC.
- **Authoritative sources checked:** CineGlobe's own `program_rate_rules_worldwide.py` GB doctrine block
  contains no IFTC program at all — only `uk_avec` with its base and VFX-uplift tiers. No independent
  verification of IFTC's existence, rate, or eligibility criteria was performed in this pass.
- **Why unresolved:** If real, this is not a rate-tier correction inside `uk_avec` — it would be an
  entirely separate, currently-unmodeled `program_slug`, which is a larger scope item than adjudicating
  an existing rule.
- **Safe CineGlobe default:** Continue modeling only `uk_avec`'s base/VFX-uplift tiers; do not assume
  IFTC eligibility or invent a rate for it.
- **Allowed project/scenario override:** None appropriate until the program itself is verified and
  modeled as new canonical rule data.
- **Financial impact if real:** Potentially very large — a 53% rate (if accurately reported) vs. the
  current 25.5%/29.25% would roughly double the UK incentive; not precisely calculable without
  confirming both the rate and Little Utopia's eligibility (budget-based, per the reports).
  Not included in the canonical document's confirmed-defect table because it is unverified as to
  existence, not merely as to a detail.
- **Evidence needed:** Primary HMRC or BFI documentation specifically naming and detailing an
  Independent Film Tax Credit as distinct from standard AVEC, including eligibility budget thresholds
  and confirmed rate.

## 7. Systemic — territorial/vendor-level verification for all five jurisdictions

- **Exact question:** For every included, non-zero QPE line in every jurisdiction, was the underlying
  good/service actually rendered/sourced locally, or could some portion be foreign-sourced (imported
  equipment, non-resident vendors, international travel legs) and thus non-qualifying even though the
  account was allocated to the claiming jurisdiction?
- **Authoritative sources checked:** N/A — this is a data-completeness question, not a rule-text
  question. Confirmed via direct code inspection that `component` (vendor-location/import-local split)
  is null on all 185 trace lines across all five packages, and that territoriality is currently enforced
  only structurally, via the allocation step (§1.6 of the canonical document).
- **Why unresolved / project-dependent:** This requires real vendor/procurement-level detail about
  Little Utopia's actual production that does not currently exist anywhere in CineGlobe's data for this
  project.
- **Safe CineGlobe default:** Continue treating "allocated to jurisdiction X" as a proxy for "incurred in
  jurisdiction X" — the existing, disclosed modeling simplification. Per this task's explicit
  instruction, this ledger does **not** assume that routing payment through a local production entity or
  SPV by itself converts foreign-sourced spend into qualifying local spend; that assumption is
  affirmatively NOT made anywhere in this analysis.
- **Allowed project/scenario override:** A vendor/component-level breakdown could be added as project
  data if/when available; this is a data-entry and (potentially) schema-extension item, not a rule
  question.
- **Financial impact:** Not calculable without the underlying vendor data — bounded above by the full
  QPE base of each jurisdiction (~$4.05–4.36M each).
- **Evidence needed:** Real production vendor/procurement records for Little Utopia (out of scope for a
  research task; this is a future data-collection item).
