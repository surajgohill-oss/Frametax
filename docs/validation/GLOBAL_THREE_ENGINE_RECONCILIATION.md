# Global Three-Engine Validation Reconciliation

Date: 2026-08-09
Companion machine-readable file: `GLOBAL_THREE_ENGINE_RECONCILIATION.json`

## Scope and method

This reconciles three completed, independent workstreams into one authoritative
disposition, per the locked project sequence (Step 2). No new jurisdiction
research was performed except three narrowly bounded checks explicitly permitted
by this task (resolving Gemini's 3 DUPLICATE calls on the 23 missing programs,
and Gemini's 2 additional discoveries, against evidence already gathered by
Codex/CineGlobe's own inventory — no external fetches were needed for any of
these five checks).

## Engine provenance

- **CODEX** — `CODEX_GLOBAL_INCENTIVE_VALIDATION.json/.md`, `CODEX_GLOBAL_VALIDATION_COMPLETION_PLAN.md`,
  `CODEX_GLOBAL_VALIDATION_COMPLETION_QUEUE.json`, `GLOBAL_AUTHORITY_COMPLETION.json/.md`,
  `GLOBAL_AUTHORITY_RESEARCH_LEDGER.json`, `GLOBAL_RECONCILIATION_QUEUE.json`, `GLOBAL_TREATY_COMPLETION.json`,
  `GLOBAL_VALIDATION_CLOSEOUT.md`. Identified by commit history (`4196c6b`, `8060045`/`b86e89a`, `d6136b7`,
  `af1cc35`) and in-file methodology text.
- **GEMINI** — `GEMINI_WORLDWIDE_AUTHORITY_VALIDATION.json/.md` (final, correct-denominator pass),
  `GEMINI_MISSING_PROGRAM_VALIDATION.json`, `GEMINI_TREATY_VALIDATION.json`, `GEMINI_VALIDATION_CLOSEOUT.md`.
  Identified by commit history (`47988e4`/`fc2b7b4`, `018e0ce`) and in-file scope text.
  **One Gemini artifact is explicitly superseded and excluded as evidence**: `GEMINI_GLOBAL_INCENTIVE_VALIDATION.json/.md`
  used a wrong denominator (410 programs, not 262) and was directly inspected and rejected by Codex's own
  completion pass (415 records inspected, 0 salvaged — see `GLOBAL_AUTHORITY_RESEARCH_LEDGER.json`). Gemini's
  own later pass independently re-based on the correct 262-program inventory and reproduces the exact
  8/15/179/17/43 split, confirming the earlier pass was simply wrong, not a genuine second opinion.
- **CLAUDE/CHAT** — this conversation's own prior turns: `CANONICAL_RULE_ADJUDICATION_MU_MT_GR_GB_AU.md`,
  `UNRESOLVED_JURISDICTION_RULES.md`, and commit `21af675` ("Incentive/Optimizer Core Closeout") — the actual
  implementation and runtime verification of the deterministic-rule findings for the 5-jurisdiction pilot
  (MU/MT/GR/GB/AU). No separate global-scope Claude artifact exists or was expected; this stream's evidence is
  scoped to the pilot plus general schema/engine-consumption findings (the Bridge `npc_usd` export bug, the
  AU hard-gate mechanism, the treaty proven-zero surfacing) that generalize to the worldwide universe.

## Findings by category

| Category | Codex | Gemini | Claude/Chat | Classification |
|---|---|---|---|---|
| Existing-program classification (262) | 8/15/179/17/43 | 8/15/179/17/43 (identical) | Not independently re-derived at this scale | **AGREED** |
| 23 missing programs — overall | 23 discovered, 13 self-completed w/ authority, 10 unresolved | 20 CONFIRMED_MISSING, 3 DUPLICATE | Cross-checked Gemini's 3 duplicate calls against Codex's own inventory | **RESOLVED_BY_AUTHORITY** (2 of 3 duplicates); **1 TRUE_INTERPRETATION_CONFLICT** (Netherlands HES) |
| Gemini's 2 additional discoveries | Not assessed (post-dates Codex pass) | 2 additional (Canary Islands 54%, Hungary Base Rebate) | Both resolve to duplicates of already-counted programs | **RESOLVED_BY_AUTHORITY** — 0 net-new |
| Treaty dataset (38 stored / 109 rows) | 8 queues defined, 0 closed | 20 current / 18 stale / 5 new pathways (aggregate) | Confirmed the consuming mechanism (treaty_engine) is real and already correctly proven-zero for MU | **ONLY_ONE_ENGINE_REVIEWED** at per-record granularity; **AGREED** the dataset is materially incomplete |
| QPE default-inclusion / no-SPV-alone territoriality | Systemic finding: no territoriality predicate exists | Confirms SPV-alone insufficient in all 5 pilot jurisdictions | Same rule already implemented and runtime-verified for the pilot | **AGREED** |
| Contingency architecture | Not assessed | Not assessed | Verified established and correct; not rebuilt | **AGREED** (by non-contradiction) |
| NPC/ranking + Bridge export | Not assessed | Not assessed | Ranking logic was correct; Bridge package export was the actual, sole defect — fixed | **AGREED** (by non-contradiction) |
| Treaty/co-production candidate generation | "Seed, not complete universe" | 5 missing material pathways | Pricing support exists; generation gap confirmed and partially connected (proven-zero surfacing) for MU | **AGREED** |
| AU Location Offset hard gate | STALE; split Producer/Location/PDV | Not separately assessed | A$20M minimum-QAPE gate implemented and verified this session | **AGREED** (complementary, not conflicting) |

## The one true interpretation conflict

**Netherlands Film Production Incentive — High-End Series.** Gemini calls it a duplicate of an existing
Netherlands program; Codex's own record describes a "distinct series regulation," and Codex's own scorecard
independently expected exactly one new Netherlands discovery. Unlike the Thailand case (resolved below),
neither engine's already-gathered evidence pins down the administering authority or legal instrument clearly
enough to call it either way. Recorded in `GLOBAL_RECONCILIATION_EXCEPTIONS.json`. Immaterial to the 5-pilot
runtime; blocks only the exact Netherlands worldwide program count (3 vs. 4).

## Two conflicts resolved without new research

- **South Africa** — Gemini says DUPLICATE; Codex's own "missing program" discovery and its own remediation
  note on the *existing* `za_nfvf_rebate` record ("rename to dtic program and encode production/post tiers")
  describe the same program at updated rates. Codex's two documents were internally inconsistent with each
  other; Gemini's duplicate call is correct. Disposition: **MERGE** into the existing record.
- **Thailand** — Gemini says DUPLICATE of the existing BOI-administered `th_film_incentive`; but Codex's own
  source for the "missing" discovery is `thailand.prd.go.th` — Thailand's **Public Relations Department**, a
  different government body from the Board of Investment. Different administering authority is sufficient to
  treat these as genuinely distinct programs. Disposition: **ADD** as a new, separate program.

## What was NOT reopened

Per this task's explicit instruction, the following prior findings were treated as established and were not
re-litigated: the contingency engine, NPC/ranking logic correctness, the Bridge export defect's root cause,
the $9,068 Little Utopia LA/US non-claiming segment, the existence of treaty/hybrid pricing support, the
candidate-generation gap itself, the no-SPV-alone territoriality rule, the AU hard gate requirement, and the
calibrated MU/MT/GR/GB/AU methodology.

## Result

Zero votes were taken; zero findings were averaged. Every classification above rests on either (a) both
engines independently reproducing the same number from the same primary-source-first methodology, (b) a
specific piece of already-gathered evidence (an authority citation, an administering-body name, an existing
CineGlobe record) that settles the question without new research, or (c) an honest declaration that the
evidence in hand does not settle it (the one Netherlands exception). Full per-program and per-treaty-queue
detail is in the companion JSON files listed in `GLOBAL_VALIDATION_GATE.md`.
