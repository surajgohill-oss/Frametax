# PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING

Base commit: `ffe6e4822024225a41ede877eb058a48d575ca82`. Worktree
`/Users/Suraj/cineglobe-frametax-claude-remediation`, branch `claude/audit-frametax-features-NZcX5`.

## Objective

Wire real Production Record facts (`ProjectPerson` -> `TalentProfile`) into official co-production
treaty discovery, qualification, conditional structuring, and recomputation — never as a universal
writer/director rule; each treaty/framework's own exact requirements govern.

## What existed before this pass

Research (see prior-turn exploration) confirmed:

- `ProjectPerson.is_confirmed` and `TalentProfile.primary_nationality`/`known_residencies` (a
  genuinely separate field) already existed, but neither `role_known_codes_from_project` nor
  `typed_personnel_facts_from_project` filtered on `is_confirmed` — an unconfirmed attachment was
  read identically to a confirmed one everywhere.
- `canonical_role_qualification_bridge.py` already carried the exact vocabulary this task needed
  (`QUALIFIES/HARD_FAIL/CURABLE_GAP/USER_FACT_REQUIRED/RULE_DATA_INCOMPLETE/...`,
  `CanonicalQualificationResult` with `resolved_facts/missing_facts/failed_requirements/
  curable_requirements/available_levers`) — its own `regime_id` docstring already anticipated
  `"program_slug or treaty_slug"` and `qualification_route` already listed `"bilateral_treaty"` as
  an expected value. **No new vocabulary was introduced.**
- Real personnel facts were read for 24 individual incentive *programs* (cultural point tests) but
  never for treaty-level co-production eligibility. `evaluate_bilateral_coproduction_opportunity`
  and `evaluate_bilateral_eligibility` had no personnel parameter at all, used or unused.
- `TreatyData` (the real registry of 28 bilaterals + 3 multilateral frameworks) had **no per-treaty
  personnel-eligibility data of any kind** — only `non_party_personnel_exception_pct`, always `None`
  for every real entry, with its own docstring already establishing the required discipline: a
  `None` must surface as unresolved, never as "no requirement exists."

## What this pass wired (additive, backward-compatible)

### 1. `treaty_engine.PersonnelRequirement` (new dataclass)

One treaty's/framework's own real, cited rule: `eligible_roles` (e.g. `("director", "writer")`),
`role_mode` (`"any_one_of"` | `"all_of"`), `fact_kind` (`"nationality"` | `"residency"` |
`"either"` — nationality and residency are never merged or substituted for each other), and
`eligible_codes`. `TreatyData.personnel_requirement` defaults to `None` on **every one of the 28
real registered bilaterals and 3 real multilateral frameworks** — none has been individually
researched, and this pass performed no external research (explicitly barred). A `None` here
resolves `RULE_DATA_INCOMPLETE` and **never blocks** a treaty on its own; a real, researched rule
would be added treaty-by-treaty in a future, separately-scoped research pass.

### 2. `canonical_role_qualification_bridge.role_attachment_facts_from_project` (new accessor)

Reads the **same** `ProjectPerson` ⋈ `TalentProfile` rows the two existing accessors already read
— no new person/nationality/treaty model — but additionally filters on `ProjectPerson.is_confirmed`
and distinguishes three real states per role: no attachment at all, an **unconfirmed** attachment
(real, proposed, never credited as current eligibility), and a **confirmed** attachment whose
nationality/residency fact is simply not on file. `role_known_codes_from_project` and
`typed_personnel_facts_from_project` are **untouched** — every existing consumer (the 24-slug
program registry, cultural point tables) behaves identically to before this pass.

### 3. `canonical_role_qualification_bridge.evaluate_treaty_personnel_gate` (new function)

Evaluates one `PersonnelRequirement` against real attachment facts, returning the existing
`CanonicalQualificationResult` contract. Exact required logic, unit-tested directly:

- `requirement is None` -> `RULE_DATA_INCOMPLETE`, never blocking.
- `"any_one_of"`: a single confirmed, satisfying role is immediate `QUALIFIES`, even with every
  other eligible role unattached/unknown/unconfirmed.
- `"all_of"`: every eligible role must independently satisfy.
- A confirmed, **known** fact that does not match `eligible_codes` is a real `HARD_FAIL` — never
  silently skipped.
- Unattached (open slot) -> `CURABLE_GAP` for a pre-filing-castable role, else `USER_FACT_REQUIRED`.
- Unconfirmed, or confirmed-with-unknown-fact -> `USER_FACT_REQUIRED` — a real conditional question
  with an `available_levers` entry and a `reasoning_trace` "next question," never silently dropped,
  never credited.
- `fact_kind` is read as exactly one typed field — a residency fact never satisfies a
  nationality-only rule and vice versa; `"either"` is the only mode that accepts both.

### 4. `canonical_treaty_bridge.evaluate_bilateral_coproduction_opportunity` — wired

Gained `personnel_requirement`/`personnel_attachment_facts` as trailing, keyword-default (`None`)
parameters — every existing caller is byte-identical. When a real requirement + facts are supplied:
`QUALIFIES` contributes nothing further (contribution-share/cultural gates alone still decide
`ELIGIBLE`); a `HARD_FAIL` is folded into `disqualification_reasons` and forces `INELIGIBLE` — a
real, fail-closed disqualification, same treatment as a failed cultural test, and it **cannot be
bypassed** by an otherwise-clearing contribution-share gate (proven directly — see Tests); an
unresolved personnel gate (`CURABLE_GAP`/`USER_FACT_REQUIRED`) keeps the whole opportunity at
`UNRESOLVED_FACTS` even when contribution/cultural facts are fully resolved — never silently
`ELIGIBLE` while a real personnel question remains open, never silently `INELIGIBLE` either.
`CoproOpportunity` gained the served fields: `personnel_gate_state`,
`personnel_satisfied_requirements`, `personnel_failed_requirements`, `personnel_missing_facts`,
`personnel_curable_levers`, `personnel_next_question`.

### 5. `canonical_evaluation.py` — call sites wired

`role_attachment_facts` is fetched once per evaluation (the same one-query-per-project pattern
`role_known_codes`/`typed_personnel_facts` already use) and threaded into **both** bilateral loops
(home-anchored and non-home-anchored), each resolving its own treaty's `personnel_requirement` via
the existing `te.get_bilateral_treaty` lookup. The served `calculation_trace_json` for every
`treaty_coproduction` structure now carries the full personnel-gate contract.
`canonical_production_view.py`'s served entry surfaces the same six fields — additive, `None`/`[]`
for any row persisted before this wiring existed.

**Multilateral frameworks (Eurimages/European Convention/Ibermedia) are NOT wired** — out of this
pass's bounded scope; their opportunities correctly carry `personnel_gate_state=None` (the gate was
never even attempted, distinct from `RULE_DATA_INCOMPLETE`, which means "attempted, no rule on
file").

### 6. Fingerprint — recompute on fact change

`_compute_fingerprint` gained a new `role_attachment_facts` input, included at **both** fingerprint
computation sites (`evaluate_project` and the read-only `current_generation_fingerprint`
reconstruction, kept in lockstep per this codebase's own "two views, two fingerprints" discipline).
This is necessary and distinct from `role_known_codes` (already fingerprinted): confirming a
previously-proposed attachment does not change the underlying nationality/residency *set*
`role_known_codes` tracks, so only the new, confirmed-status-sensitive input reliably invalidates a
cached evaluation when a producer confirms (or un-confirms) an attachment. Proven directly (see
Tests).

### `ENGINE_VERSION`

Bumped `1.56.0` -> `1.57.0`: every row persisted before this pass was generated without the
personnel gate ever being consulted and must be treated as stale.

## Deliberately deferred (per guardrails)

- **No external research.** Every real treaty's `personnel_requirement` stays `None` — genuinely
  unresearched, never a fabricated or generalized rule. Populating real per-treaty personnel clauses
  for 28 bilaterals + 3 frameworks is a legal-research task, explicitly out of this pass's scope.
- **Multilateral wiring** (Eurimages/European Convention/Ibermedia) — the same mechanism could be
  extended to the multilateral evaluators in a future, separately-scoped pass; not attempted here.
- **`typed_personnel_facts_from_project`/`role_known_codes_from_project` unchanged** — mutating them
  to respect `is_confirmed` would silently change the tested, already-accepted 24-slug program
  registry and 13 cultural point tables for every project; deliberately not attempted (a real,
  separate, out-of-scope change per the exploration's own risk assessment).

## Real facts consumed for the four required productions (no facts invented)

| Production | `ProjectPerson` rows on file | Real facts |
|---|---|---|
| Little Utopia | 4, all confirmed | writer Clara Salaman (GB, confirmed), director Kim Farrant (AU, confirmed), 2 producers (US, confirmed) |
| F#K Valentine's Day | 0 | none |
| Bad Hombres | 0 | none |
| Lips Like Sugar | 2, both **unconfirmed** | writer Anthony Tambakis (nationality NULL), director Brantley Gutierrez (nationality NULL) |

## Tests

`tests/test_production_record_copro_wiring_claude.py` (new, 15 tests, all passing) proves every
required scenario directly:

1. A qualifying **writer** satisfies an "writer OR director" rule (immediate `QUALIFIES`).
2. A qualifying **director** satisfies the same rule with no qualifying writer present.
3. Unknown writer/director produces a real conditional question (`CURABLE_GAP`/`USER_FACT_REQUIRED`
   with a real lever and next-question) — never false credit, never disappearance.
4. Unconfirmed personnel are never credited as current eligibility.
5. A nationality-only rule rejects a residency-only fact, and a residency-only rule rejects a
   nationality-only fact (both directions proven); `fact_kind="either"` genuinely accepts both.
6. A mandatory contribution-share gate cannot be bypassed by a satisfying creative-role nationality
   (a genuinely good director does not rescue a treaty whose real ownership shares fail).
7. Changing a Production Record confirmation-status fact changes `_compute_fingerprint`'s output
   (proven directly against Little Utopia's real attachment facts).
8. A served `treaty_coproduction` structure (real project, real budget, a synthetic test-only
   treaty — never a fabricated real-treaty clause) exposes the full personnel-gate contract:
   state, satisfied requirements, and correctly resolves `QUALIFIES` from Little Utopia's own real
   confirmed writer (GB) even though the real confirmed director (AU) does not match the test
   treaty's party codes.

Plus a confirmed, real disqualification proof (a confirmed wrong-nationality role produces a real,
fail-closed `INELIGIBLE`) and a backward-compatibility proof (a caller supplying no
`personnel_requirement` at all behaves byte-identically to before this wiring existed).

## Focused regression

| Suite | Result |
|---|---|
| `tests/test_production_record_copro_wiring_claude.py` (new) | 15 passed |
| Treaty/co-production/stacking/identity/DAVE/NV/engine suite (13 files) | 242 passed |
| Economics integrity + P0 remediation + health audit (3 files) | 90 passed, 1 legitimate skip |
| Optimization contract/inventory/optimizer/page-integrity/import-order/closeout/input-integration (7 files) | 230 passed |
| `tests/test_canonical_role_qualification_bridge.py` | 30 passed (1 pre-existing stale-signature test fixed — `_coproduction_facts` gained `treaty_slug`/`participant_codes` params in an earlier P0-QUAL-001 pass; this test predated that change and was never run since) |
| Four canonical productions (direct fresh recomputation) | 4/4 baseline economics exact, unchanged |

### Pre-existing, unrelated test debt discovered (not caused by this pass, not fixed)

A broader sweep across all 60 test files importing from the modules this pass touched surfaced 6
additional failures, all confirmed pre-existing and unrelated: `program_rate_rules.py` and
`authority_coverage_registry.py` (the data these tests exercise) show **zero diff** against
`ffe6e48` — these tests' expected counts (`ca_bc_dave` rate resolution, B1-blocked-id counts, FVD
candidate/rejection counts) had already drifted out of sync with the live registries before this
pass began, from earlier sessions' work, and were simply never run against this specific test
surface until now. Listed for disclosure, not fixed (fixing arbitrary pre-existing count-assertion
drift across the wider 60-file surface is outside this pass's bounded scope):
`test_b4_authority_exhaustion_gate.py::test_all_46_b1_canonical_ids_are_blocked`,
`test_canonical_authority_substrate.py::test_fvd_runtime_candidate_universe_restored`,
`test_canonical_knowledge_consolidation.py::test_recovered_stranded_program_is_canonically_registered[ca_bc_dave-0.16]`,
`test_canonical_knowledge_consolidation.py::test_recovered_program_cannot_silently_become_recommended[ca_bc_dave]`,
`test_canonical_served_wiring_repair.py::test_fvd_accounting_matches_codex_diagnosis`,
`test_canonical_served_wiring_repair.py::test_fvd_unpriceable_causes_are_differentiated_not_flattened`.

## Guardrails honored

No external research (every real treaty's personnel rule stays `None`, honestly disclosed). No
MFNI/country-cleanup/reinvestment/UI redesign. No mock production substitution — all facts above are
the real, current `ProjectPerson`/`TalentProfile` rows on file, queried directly, never invented.
`ffe6e48`'s optimizer behavior and all four frozen/verified baseline economics are unchanged (none
of the four productions has a real, researched treaty personnel rule, so the new gate resolves
`RULE_DATA_INCOMPLETE` everywhere and never alters resolution state, pricing, or ranking for any of
them — see `FOUR_PROJECT_COPRO_RUNTIME_CLAUDE.csv`).
