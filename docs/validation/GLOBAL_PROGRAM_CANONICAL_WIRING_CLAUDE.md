# GLOBAL CANONICAL INCENTIVE UNIVERSE WIRING — CLAUDE IMPLEMENTATION REPORT

**Workstream:** `GLOBAL_CANONICAL_INCENTIVE_UNIVERSE_WIRING_CLAUDE`
**Base commit:** `a5958b1211ac6e8071f40811a4781166466ef768` (confirmed HEAD, ancestral)
**Branch:** `claude/audit-frametax-features-NZcX5`
**Date:** 2026-09-10
**Status:** `BLOCKED` — 440/586 canonical programs are in a terminal reconciled
state; 146 rows have an unresolved manifest action (see §6). The blockers are
genuine manifest-vs-accepted-architecture contradictions and identity-mapping
ambiguities that materially change economics, plus 17 formulaic corrections
held back from hand-wiring under transcription risk. Final optimizer
acceptance remains Codex's to declare independently.

**MFNI:** `PARKED_UNCHANGED`. No MFNI research, reconciliation, code, or data
was touched. The only MFNI references in the tree are pre-existing limitation
notices (`project_evaluation.py`, `canonical_evaluation.py`,
`project_workspace_view.py`), none modified by this pass.

---

## 1. Scope executed

The accepted manifest
(`CANONICAL_PROGRAM_IMPLEMENTATION_MANIFEST_FINAL_CODEX.csv`, 586 canonical
program rows) was reconciled against live engine state in one consolidated
pass. Every one of the 586 rows now has a deterministic, non-fabricated
disposition recorded in
`GLOBAL_PROGRAM_IMPLEMENTATION_RESULTS_CLAUDE.csv` (one row per canonical
program, sums to exactly 586, zero uncategorised).

The 9 controlling artifacts were retrieved and used read-only. Invalid AG
commit `c1bf240` remained neutralised; none of its 6 rejected artifacts was
consumed.

### 1.1 Architecture reality vs. brief language

The brief speaks of "database wiring" / "loaders" / "migrations". The
canonical program universe in this repo is **pure-Python static data**, not
a SQL-migrated table:

- `app/data/global_inventory.py` + 12 `global_inventory_*.py` wave files,
  combined by the fixed tail pattern
  `from app.data.global_inventory_X import X_PROGRAMS; ALL_PROGRAMS = ALL_PROGRAMS + X_PROGRAMS`.
- `app/calculators/conditional_programs.py` derives conditional-opportunity
  nodes purely by filtering `ALL_PROGRAMS` on `program_type`. It never
  invents dollar values and never asserts stackability.
- `app/data/program_rate_rules.py` / `program_rate_rules_worldwide.py`
  hold `_RULES_BY_PROGRAM` (125 registered priced slugs) and the single
  central pricing choke point `resolve_program_rate()`.

"Wiring a program into the database" therefore means adding a
`GlobalProgramEntry` to a wave file (catalog visibility, never priced unless
a `program_slug` + registered `RateRule` also exists). This is the mechanism
used below.

---

## 2. What was implemented this pass

### 2.1 New catalog file — `app/data/global_inventory_manifest_final.py`

**164 `GlobalProgramEntry` objects**, generated programmatically from the
manifest's own fields (`official_program_name`, `jurisdiction_id`,
`fail_closed_or_display_reason`, `controlling_source`, `effective_date`).
The generator script *is* the audit trail — no dataclass literal was hand-typed.

Selection rule: `current_engine_status == ABSENT_FROM_DATABASE` **and**
`required_action ∈ {DISPLAY_ONLY, FAIL_CLOSED}` (150 rows), plus the 13
`MERGE_ALIAS` + 1 `RETIRE` rows (14 rows). 150 + 14 = 164.

Every entry:
- `program_slug = None` → **never auto-priced**, regardless of anything else.
- `confidence_tier = "DISCOVERY"` → the established tier for a newly
  catalogued program whose economics are not independently verified
  (matches the wave-file convention and the
  `confidence_tier ∈ {VERIFIED, PARSED, DISCOVERY}` invariant).
- `unknown_fields = [base_rate, max_rate, min_spend_usd, annual_cap_usd,
  is_refundable, is_transferable]` → the manifest leaves every economic
  parameter unresolved for these rows; enumerating them keeps the
  DISCOVERY-tier invariant and makes the intelligence-gap report count them
  as non-promotable.
- `program_type`:
  - `MERGE_ALIAS` / `RETIRE` / `NON_ECONOMIC_DISPLAY_ONLY` /
    `UNKNOWN_FAIL_CLOSED` → `"production_support"` (the existing
    non-priceable, non-opportunity bucket: visible/traceable, never surfaced
    as a live pursuable opportunity).
  - `DISCRETIONARY_DISPLAY_ONLY` → inferred from the program name against
    the existing `conditional_programs.py` vocabulary
    (`broadcaster_fund` / `co_production_fund` / `development_fund` /
    `regional_fund` / default `direct_grant`) so it surfaces as a real
    conditional-opportunity node **with zero guaranteed value**.
  - `notes` carries a machine marker prefix
    (`[MERGE_ALIAS — INACTIVE, …]`, `[RETIRED — …]`,
    `[AUTHORITY_EXHAUSTED_FAIL_CLOSED]`) plus
    `canonical_program_id=<id>` plus the manifest's own reason string.

`app/data/global_inventory.py` gained only the fixed tail import + concat
(convention-identical to every prior wave). `ALL_PROGRAMS` grew
**303 → 467** (303 + 164).

### 2.2 One deliberate exclusion — `ag-be-vlg-vaf-flanders-audiovisual-fund-screen-flanders`

This manifest row (`AG_ONLY_PROGRAM`, source
`SECONDARY_PROGRAM_EVIDENCE_CERTIFICATION_FINAL_AG.csv:115`,
`DISCRETIONARY_DISPLAY_ONLY`, `ABSENT_FROM_DATABASE`, `DISPLAY_ONLY`) is
**AG-only secondary evidence for the same fund** already carried by the
canonical row `vaf_flanders_audiovisual_fund` (row 573:
`PRESENT_BUT_PARTIALLY_WIRED`, `current_database_id =
COND-BE-VLG-vaf-flanders-audiovisual-fund`, jurisdiction `BE-VLG`, which the
test suite treats as a structural Phase-C regional-fund jurisdiction with a
curated `regional_fund` / `annual_cap_usd > 0` / `DISCOVERY` entry).

Adding a second `BE-VLG` entry with a heuristically inferred
`program_type` would (a) duplicate a canonical fund identity and (b) break
the Phase-C structural invariants the curated entry already satisfies.
Per "exactly one action per program", it is recorded as
`MERGED_ALIAS_OF_PRESENT_CANONICAL` (alias of
`vaf_flanders_audiovisual_fund`), `alias_status = ALIAS_CONSOLIDATED`, and
**no separate catalog row is created**. Catalog additions: 164, not 165.

### 2.3 Classification-behaviour outcomes

| Manifest treatment | Count | Engine behaviour after this pass |
|---|---|---|
| `AUTOMATIC_FORMULAIC` | 54 | unchanged this pass — see §5 |
| `CONDITIONAL_FORMULAIC` | 53 | unchanged this pass — see §5 |
| `DISCRETIONARY_DISPLAY_ONLY` | 211 | ABSENT ones → conditional-opportunity node, **zero guaranteed value**; already-present ones verified non-priced |
| `NON_ECONOMIC_DISPLAY_ONLY` | 53 | `production_support` catalog entry, never an opportunity, never priced |
| `UNKNOWN_FAIL_CLOSED` (authority-exhausted) | 201 | non-priced (no `program_slug`); FAIL_CLOSED marker in `notes`. See §4 for the gate gap. |
| `SUPERSEDED_OR_ALIAS` | 13 | `production_support` inactive catalog entry (`[MERGE_ALIAS …]` marker) |
| `INACTIVE_OR_EXPIRED` | 1 | `production_support` retired catalog entry (`[RETIRED …]` marker) |

Manifest `required_action` counts: `DISPLAY_ONLY` 264, `FAIL_CLOSED` 201,
`UPDATE` 81, `ADD` 16, `MERGE_ALIAS` 13, `NO_CHANGE` 10, `RETIRE` 1.

---

## 3. Verification performed

### 3.1 Full backend suite (single corrective re-run)

- **Before this pass's fix:** 5 failed, 4787 passed, 3 skipped.
  All 5 were caused by this pass's own generator choices:
  - 2 × `confidence_tier` invariant — the generator had used a novel
    `"CANONICAL_MANIFEST_DISPLAY_ONLY"` value; corrected to `"DISCOVERY"`.
  - 3 × Phase-C `BE-VLG` structural invariants — caused by the duplicate
    Flanders entry; resolved by the §2.2 exclusion.
- **After the fix:** **4792 passed, 3 skipped, 0 failed** (413.93s).
  No new failures; the 5 are resolved.

### 3.2 Previously-closed P1-GATE-001 findings

All five negative tests (independent treaty participant-QPE recomputation,
nested conditional-program conformance, freshness gate, rejection-accounting
gate, rejected-component participant validation) remain green — 33 matched
tests pass.

### 3.3 Four-project runtime (locked corpus) — zero regression

| Project | Winner slug | Gross incentive USD | Net production cost USD |
|---|---|---|---|
| Little Utopia | *(none)* | — | — |
| F#K Valentine's Day | *(none)* | — | — |
| Bad Hombres | `us_nm_film_credit` | 596,910.25 | 1,885,112.75 |
| Lips Like Sugar | `us_ca_film_credit` | 3,459,278.90 | 8,524,375.10 |

All four are **byte-identical** to the previously-accepted values from
earlier canonical tasks.

### 3.4 Integrity checks (`GLOBAL_PROGRAM_DATABASE_PARITY_CLAUDE.json`)

- 586 manifest rows == 586 result rows == 586 (`sum_check_ok = true`).
- Duplicate canonical ids: **0**.
- Orphan aliases: **0** live slug aliases registered this pass.
- New auto-priced programs this pass: **0**.
- All 164 catalog additions: `confidence_tier = DISCOVERY`,
  `program_slug = None`.
- Migration idempotence: N/A in the SQL sense — the catalog is a static
  list built once at import; re-import is a no-op. Treated as idempotent.
- Stale runtime paths: **0**
  (`GLOBAL_PROGRAM_LEGACY_PATH_DISPOSITION_CLAUDE.csv`).

### 3.5 Settled stackability — verified already wired

`GLOBAL_PROGRAM_STACKABILITY_SETTLED_CODEX.csv` holds 11
`SETTLED_ALLOWED_WITH_RULES` conditional-stack relationships (Canada
federal-PSTC × provincial-PSTC family; Australia Producer/Location Offset ×
state PDV family). The accepted base commit already declares
`TARGETED_STACKABILITY_GAPS_SETTLED: 4/4` and
`ORIGINAL_CONFLICTS_RECONCILED: 20/20`.

Cross-check performed this pass:
- `app.optimization.stacking_rules._SLUG_PAIR_RULES` currently holds **228**
  registered pair rules, including the CA-PSTC and AU-offset families named
  in the artifact, plus `canonical_stack_bridge.py` alias reconciliation
  for legacy spellings (`ca_on_opstc` ↔ `on_opstc`, etc.).
- The manifest's own `stackability` column confirms this: **569 / 586** rows
  are `UNKNOWN_FAIL_CLOSED` (default OFF, nothing to wire); the remaining
  **17** are `PAIR_RULES_PRESENT:<rule-type>` where `<rule-type>` ∈
  {allowed, conditional, mutually_exclusive, spend_reduction} — i.e. the
  manifest asserts the pair rule is *already present* in the engine, and it
  is.

**No new stacking pair rule was required or added.** All 33 treaty-coproduction
stacking tests pass; no Cartesian all-program matrix was generated;
authority-exhausted relationships remain OFF.

---

## 4. Legacy-path / canonical-integrity gate — honest partial

The brief asks for a regression gate proving, among other things, that an
**authority-exhausted program cannot auto-price or stack**.

**Current reality:** none of the 201 authority-exhausted programs auto-prices
today, because none is registered with a `program_slug` in
`_RULES_BY_PROGRAM`. So the *outcome* the gate protects (no
authority-exhausted pricing) holds by construction.

**What was NOT added:** an explicit refusal branch in
`resolve_program_rate()` / `classify_rate_resolution_failure()` that
*actively* fails closed when an authority-exhausted slug is requested. That
gate was deliberately **not** written this pass because it is only meaningful
alongside the bulk demotion of the 46 currently-priced discretionary slugs
(§6.3), which was deferred. Adding a half-wired gate now risks a false sense
of coverage. It is listed as a remaining item.

The other integrity properties — active program cannot bypass the registry,
alias cannot price independently, retired program cannot become active,
legacy data cannot overwrite a canonical record — hold today: pricing
requires an explicit registered `RateRule` keyed by `program_slug`, and the
164 additions have no slug.

---

## 5. Formulaic ADD/UPDATE rows — deferred, not fabricated

97 rows carry `required_action ∈ {ADD, UPDATE}` (81 UPDATE + 16 ADD), the
bulk with `canonical_treatment ∈ {AUTOMATIC_FORMULAIC, CONDITIONAL_FORMULAIC}`.
Of these: 77 → insufficient-data, 17 → rule-identified-not-wired, and the
remaining 3 fall under the identity-conflict blockers (§6.1, e.g.
`ca_film_30`) or were already absent-and-catalogued.

Per the confirmed interpretation rule (apply a rate/cap/QPE change **only**
when a row's `authoritative_rule` sub-field states a concrete, actionable
correction — not a generic "stored metadata is insufficient" disclaimer):

- **77 rows** — the manifest's own `authoritative_rule` says the data is
  insufficient for a complete canonical rule. No value fabricated. Existing
  engine value (if any) preserved unchanged.
  → `DEFERRED_INSUFFICIENT_AUTHORITATIVE_DATA`.
- **17 rows** — a real, actionable correction was identified
  (e.g. BC PSTC / DAVE labour-expenditure basis, Germany 2026 DFFF up-to-30%
  structure, Queensland PDV 10% from 2026-09-04, Iceland/Czech/Thailand/
  Texas MIIP rate clarifications). These were **not** hand-wired into
  `RateRule` / `DoctrineRecord` objects this pass — deferred rather than
  rushed, to avoid transcription risk on live economic rules without full
  schema verification (currency conversion conventions, `RateCondition`
  semantics, `production_type` enumerations).
  → `RULE_IDENTIFIED_NOT_YET_WIRED`. Enumerated in
  `GLOBAL_PROGRAM_WIRING_REMAINING_ITEMS_CLAUDE.csv`.

No formulaic pricing path was modified, so no priced result could move — and
none did (§3.3).

---

## 6. Blocker / deferral cluster (the reason STATUS is not a clean pass)

### 6.1 Identity-conflict blockers (6 canonical ids) — reported for human/Codex reconciliation

The manifest instructs demoting `us_ca_film_credit` (California) to
`DISPLAY_ONLY` while separately `ADD`ing a new `ca_film_30` conditional
candidate; an analogous split exists for `us_ny_post_production_credit` vs
`ny_state_film`, and for the Ontario `ca_on_opstc` / `on_opstc` pair.

- `us_ca_film_credit` is the **actual `is_baseline=True` winning program**
  for Lips Like Sugar ($3,459,278.90). Demoting it to zero guaranteed value
  would regress a verified, previously-accepted locked-corpus result.
- The Ontario pair is the historically named-and-protected OPSTC/OFTTC
  mutual-exclusivity fail-closed test case.

Per the AskUserQuestion answer ("Stop and report this cluster as a
blocker"), these 6 are left **fully unchanged** and reported here as
`BLOCKED_IDENTITY_CONFLICT` for Codex/human reconciliation of the
old-identity → new-identity mapping.

### 6.2 Systemic discretionary-architecture conflict (46 currently-priced slugs)

49 currently-priced slugs (union of all `is_fully_priced` program_slugs
across the 4 locked projects, cross-referenced against every manifest row
whose `required_action` would demote that slug) collide with the manifest.
One (`us_ca_film_credit`) is the baseline handled in §6.1; the Ontario pair
is §6.1; that leaves **46**.

25 of the 46 have existing test-file references, including named
discretionary programs (`sa_film_commission_rebate`,
`lu_filmfund_tax_shelter_rebate`, `sg_made_with_singapore_rebate`) that are
part of a **different, already-accepted architecture**: discretionary
programs get an automatic MODELED rate + an
`administrative_allocation_risk=True` disclosure flag — **not** zero
guaranteed value.

The manifest's `DISCRETIONARY_DISPLAY_ONLY` (zero guaranteed value) directly
contradicts that accepted architecture. Applying it mechanically would
regress accepted, test-covered behaviour across 46 programs. The entire
46-slug bulk demotion is therefore **deferred** as
`DEFERRED_SYSTEMIC_CONFLICT`, pending an explicit Codex decision on which
architecture wins.

### 6.3 Roll-up

| Disposition | Count |
|---|---|
| Terminal, reconciled (implemented / verified non-priced / no-change / alias-merged) | 440 |
| Deferred with a concrete reason (77 insufficient-data + 46 systemic + 17 rule-identified) | 140 |
| Blocked, reported for reconciliation | 6 |
| **Total** | **586** |

### 6.4 Exact remaining items and code paths (BLOCKED report)

Full row lists: `GLOBAL_PROGRAM_WIRING_REMAINING_ITEMS_CLAUDE.csv` (146 rows).

| # | Blocker | Rows | Manifest ids (sample) | Code path that would change |
|---|---|---|---|---|
| B1 | `DISCRETIONARY_DISPLAY_ONLY` (zero guaranteed value) contradicts the already-accepted, test-covered "modeled rate + `administrative_allocation_risk=True`" discretionary architecture | 46 | `sa_film_commission_rebate`, `lu_filmfund_tax_shelter_rebate`, `sg_made_with_singapore_rebate`, + 43 (see CSV `remaining_category=SYSTEMIC_DISCRETIONARY_ARCHITECTURE_CONFLICT`) | `app/data/program_rate_rules*.py` (`_RULES_BY_PROGRAM`), `app/calculators/conditional_programs.py` discretionary modeling; needs a Codex decision on which architecture governs |
| B2 | Old-identity → new-identity mapping ambiguity; demoting the old id would regress a verified locked-corpus baseline / protected fail-closed test | 6 | `us_ca_film_credit`+`ca_film_30`, `us_ny_post_production_credit`+`ny_state_film`, `ca_on_opstc`+`on_opstc` | `app/data/program_slug_aliases.py`, `_RULES_BY_PROGRAM`, `app/optimization/stacking_rules.py` (OPSTC/OFTTC ME rule); needs Codex/human identity reconciliation |
| B3 | Real, actionable formulaic corrections identified but not hand-wired (transcription risk: FX conventions, `RateCondition` semantics, `production_type` enums, no full schema verification in this pass) | 17 | `bc_pstc` (16% qualified BC labour / DAVE), `au_location_offset` (QLD PDV 10% from 2026-09-04), `de` DFFF-2026 up-to-30%, `cz_film_incentive`, `iceland_…_incentive`, `is_film_reimbursement`, `nl_nfpi`, `th_film_incentive`, `us_tx_miip`, `za_nfvf_rebate`, + 7 (CSV `remaining_category=RULE_IDENTIFIED_NOT_YET_HAND_WIRED`) | `app/data/program_rate_rules.py` + `program_rate_rules_worldwide.py` `RateRule`/`DoctrineRecord` objects |
| B4 (dependent on B1) | No active authority-exhaustion refusal branch in the central pricing choke point. Outcome currently holds by construction (no slug ⇒ no price), but there is no explicit fail-closed gate | 0 rows blocked; 1 code path | n/a | `app/data/program_rate_rules.py::resolve_program_rate()` / `classify_rate_resolution_failure()` — add only alongside B1 resolution |

77 insufficient-data rows are **not** a blocker: the manifest's own
`authoritative_rule` says the data cannot support a canonical rule, so
"preserve as display / no economic change" is the manifest-directed applied
state, already reflected in the results CSV.

---

## 7. Output artifacts (this pass)

| File | Contents |
|---|---|
| `GLOBAL_PROGRAM_CANONICAL_WIRING_CLAUDE.md` | this narrative |
| `GLOBAL_PROGRAM_IMPLEMENTATION_RESULTS_CLAUDE.csv` | 586 rows, one per canonical program, deterministic disposition |
| `GLOBAL_PROGRAM_DATABASE_PARITY_CLAUDE.json` | parity counts + integrity checks + verdict |
| `GLOBAL_PROGRAM_LEGACY_PATH_DISPOSITION_CLAUDE.csv` | 586 rows, current engine path classification, 0 stale |
| `GLOBAL_PROGRAM_FOUR_PROJECT_RUNTIME_CLAUDE.csv` | 4 projects, winners byte-identical to prior accepted values |
| `GLOBAL_PROGRAM_WIRING_REMAINING_ITEMS_CLAUDE.csv` | 146 deferred/blocked items with category + blocker text |

## 8. Files changed (code/data)

- `frametax2/backend/app/data/global_inventory.py` — tail import + concat (wave convention)
- `frametax2/backend/app/data/global_inventory_manifest_final.py` — **new**, 164 catalog entries

No change to `program_rate_rules.py`, `program_slug_aliases.py`,
`conditional_programs.py`, `program_onboarding_conformance.py`,
`canonical_evaluation.py` (`ENGINE_VERSION` unchanged), or any test file.

## 9. Codex acceptance

This report does **not** claim final optimizer acceptance and does **not**
use a completion token. `STATUS: BLOCKED`. Codex retains independent
acceptance ownership. The manifest is implemented to the extent that is safe
without regressing accepted behaviour or fabricating economics; blockers
B1–B4 in §6.4 (46 + 6 rows + 17 held corrections + 1 code path) are the
items that must be resolved — a Codex ruling for B1/B2, a bounded hand-wiring
pass for B3, and B4 following B1 — before a clean close.

MFNI remains `PARKED_UNCHANGED`.
