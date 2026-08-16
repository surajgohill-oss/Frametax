# Canonical Authority Substrate + Feasibility Boundary Closeout

**Status: `CANONICAL_AUTHORITY_SUBSTRATE_ACCEPTED`**

Implements the narrow architectural closeout specified for this task: (1)
repairs the feasibility/eligibility conflation introduced by the
immediately preceding FVD canonical input assembly repair, and (2) builds
the minimum canonical identity + field-consolidation + residual-question +
publication-contract substrate the next authority-research phase needs, per
Codex's lineage finding (`IDENTITY MANIFEST -> FIELD CONSOLIDATION ->
RESIDUAL-QUESTION LEDGER -> ATOMIC PUBLICATION CONTRACT -> TARGETED
RESEARCH`). No authority data changed. No incentive economics changed. No
frontend file changed. No new research performed.

---

## 1. Feasibility / eligibility boundary

### The regression

The prior FVD canonical input assembly repair correctly wired real,
persisted SA-1 script/location data into `derive_production_requirements()`
— but then passed that same `ProductionRequirements` object into
`discover_executable_jurisdictions()` as **the** gate deciding which
jurisdictions become economic candidates at all. `production_discovery.py`'s
existing (unmodified) classification logic treats a capability mismatch as
outright rejection: `if cap.has_capability_data and not cm.production_capable:
classification = "rejected"` — no structure is ever generated for a
rejected jurisdiction. Because FVD's real script has evidence-backed
Mediterranean sea-shore/beach/harbor scenes, `open_water_filming` became a
genuine HARD capability requirement, and 21 landlocked jurisdictions
(`marine_suitability=NONE` in the existing, unmodified
`jurisdiction_comparison.ALL_PROFILES` data) were silently removed from
structure generation entirely — conflating a soft, informational
PRODUCTION FEASIBILITY signal with a hard ECONOMIC ELIGIBILITY gate.

### The repair

`canonical_evaluation.py::evaluate_project()` now runs **two** discovery
passes, deliberately:

```python
feasibility_discovery = discover_executable_jurisdictions(
    requirements=requirements,           # real, SA-1-derived requirements
    ...
)
feasibility_by_code = {e.jurisdiction_code: e for e in feasibility_discovery.examinations}

discovery = discover_executable_jurisdictions(
    requirements=derive_production_requirements({}),   # the pre-Task-3 empty pass
    ...
)
```

`discovery` (the empty-requirements pass) is the ONLY discovery result
used to decide which jurisdictions enter `candidates` — this is byte-for-
byte the same candidate-generation behavior the canonical engine had
before SA-1 requirements existed. `feasibility_discovery` supplies
DISCLOSURE only: for every candidate (priced, capability-only, or
pricing-blocked), a new `_feasibility_status()` classifies the real
examination into `STRONG` / `WORKABLE` / `WEAK` / `UNKNOWN` with reason
codes (`MARINE_MISMATCH`, `LOCATION_MISMATCH`), persisted alongside —
never consulted for the accept/reject decision. `production_discovery.py`
itself was not modified — it is a pre-existing calculator, out of this
repair's file boundary, and the fix is entirely a handoff-point change in
`canonical_evaluation.py`.

`canonical_production_view.py::_empty_structure_entry()` now also exposes
`feasibility_status`/`feasibility_reasons` on every served structure, so
the disclosure reaches the API response, not just the persisted trace.

### Verified independence

| Jurisdiction | `is_fully_priced` | `candidate_status` | `feasibility_status` | `feasibility_reasons` |
|---|:-:|---|:-:|---|
| GR (baseline) | True | PRICED | STRONG | — |
| MT | True | PRICED | STRONG | — |
| MN | **True** | PRICED | **WEAK** | `MARINE_MISMATCH` |
| UZ | **True** | PRICED | **WEAK** | `MARINE_MISMATCH` |
| AT | False | UNPRICEABLE_AUTHORITY_INSUFFICIENT | **WEAK** | `MARINE_MISMATCH` |
| AU | False | **RULE_REJECTED** | STRONG | — |

MN/UZ prove a candidate can be economically PRICED while feasibility WEAK.
AT proves feasibility WEAK is disclosed even for a candidate blocked for
an entirely unrelated (authority) reason. AU proves a real statutory
threshold failure (Australia's minimum-QPE gate) still correctly
terminates the candidate — the repair removed only the SOFT feasibility
gate, never a real economic one.

**Feasibility ≠ eligibility boundary: PASS.**

---

## 2. FVD candidate accounting — before / after

| | Immediately prior (feasibility used as a hard gate) | After this repair |
|---|---:|---:|
| Generated structures | 89 | **110** |
| Priced | 28 | **30** |
| Directly comparable | 1 | 1 |
| Priced, review-required | 27 | 29 |
| Unpriceable | 61 | **80** |

110/30/80 is exactly the accepted "maximum defensibly priceable within
current generated universe" `CODEX_PRICEABILITY_BLOCKER_RECONCILIATION.md`
established (§E) for FVD — this repair restores that accepted baseline; it
does not invent a new one, and it was NOT hard-coded — every count above
was derived by re-running `evaluate_project()` and reading the live
persisted/served result (`canonical-1.4.0`).

**Previously marine-rejected candidates restored, with feasibility metadata
preserved (three representative jurisdictions):**

- **MN (Mongolia)**: priced=True, NPC computed normally, `feasibility_status=WEAK`,
  `feasibility_reasons=["MARINE_MISMATCH"]`.
- **UZ (Uzbekistan)**: priced=True, `feasibility_status=WEAK`,
  `feasibility_reasons=["MARINE_MISMATCH"]`.
- **AT (Austria)**: unpriceable for an unrelated authority reason
  (`UNPRICEABLE_AUTHORITY_INSUFFICIENT`), `feasibility_status=WEAK`,
  `feasibility_reasons=["MARINE_MISMATCH"]` — proving feasibility
  disclosure is independent of pricing outcome in both directions.

**Distinct QPE/incentive/NPC counts**: unchanged in kind from the prior
input-assembly repair's own finding — 3 distinct QPE values
($4,154,821.00 shared by the OPEN_DEFAULT_INCLUDE-doctrine group,
$3,614,149.60 for GR's 80%-cap, $1,132,056.00 for MU's HYBRID_CONDITIONAL
doctrine), 9 distinct incentive values, 9 distinct NPC values. This repair
did not attempt to resolve that repeated-QPE group — authority
completeness is a separate, larger, explicitly out-of-scope problem (see
§4) — and does not claim to.

---

## 3. Canonical program identity manifest (Task 3)

New: `app/services/canonical_program_identity.py`.

`canonical_program_id` / `canonical_slug` are the program's own existing,
already-stable `program_slug` — CineGlobe has never had two economic
engines disagree about what a program_slug means, so a separate numbering
scheme would add a second identity to reconcile, not remove one. What was
missing was one ADDRESSABLE layer resolving every known alias spelling to
that slug. Built entirely from existing runtime data:

- `jurisdiction_comparison.ALL_PROFILES` (richest per-program profile)
- `global_inventory.ALL_PROGRAMS` (catalog; entries with no `program_slug`
  — "not yet promoted" — are excluded, never assigned an invented identity)
- `authority_coverage_registry.COVERAGE_REGISTRY` / `CANONICAL_RUNTIME_
  SLUG_BINDINGS` (57 known canonical-corpus-spelling aliases)
- `program_slug_aliases.PROGRAM_SLUG_ALIASES` (7 known variant-slug aliases)

`resolve_identity(slug_or_alias)` resolves any known spelling (canonical
or alias) to one `CanonicalProgramIdentity`; unknown spellings return
`None`, never a fabricated identity. `all_canonical_identities()` returns
every distinct program, deduplicated by resolved `canonical_program_id`.

**Verified**: 224 distinct canonical programs (280 raw known slugs before
dedup — the gap is alias spellings that independently appear as rows in
different registries and correctly collapse to the same identity).
`resolve_identity("ae_ad_film_rebate")` and
`resolve_identity("proposed_united_arab_emirates_abu_dhabi_abu_dhabi_35_production_rebate")`
(its canonical-corpus alias spelling) both resolve to the identical
`canonical_program_id`.

**Alias resolution: PASS.**

No authority data migrated, researched, or changed. No existing registry
deleted or modified.

---

## 4. Field-consolidation view (Task 4)

New: `app/services/canonical_program_consolidation.py`.

Given a `canonical_program_id`, `consolidate()` reports the best CURRENTLY
AVAILABLE runtime status — `PRESENT` / `PARTIAL` / `MISSING` — for each of
the 14 required executable dimensions, with an exact provenance `source`
string per dimension. Every value is read verbatim from an existing
registry function already called by the served pricing pipeline
(`get_rate_rules`, `get_program_rules`, `resolve_program_doctrine`,
`get_qpe_cap`) — no new rule, rate, threshold, or cap is computed or
guessed.

**Key finding during construction**: `RateRule.confidence_tier` (VERIFIED
vs. PARSED vs. DISCOVERY) is the exact signal distinguishing a genuinely
executable rate from a real-but-not-yet-accepted one. UK AVEC has TWO real,
cited `RateRule` objects (25.5% AVEC net rate + 29.25% VFX ceiling, sourced
to bfi.org.uk) — but both are `confidence_tier=PARSED`, not `VERIFIED`.
Naively checking "does a RateRule exist" would have wrongly reported UK
AVEC's `RATE_OR_AWARD_BASIS` as `PRESENT`; checking VERIFIED confidence
specifically correctly reports it as `PARTIAL` — matching the documented
reality that this rate exists in the corpus but was never accepted into
the executable layer.

**Missing fields remain MISSING**: confirmed — `APPLICATION_TIMING` has no
runtime field anywhere in the current registries for any program, and is
honestly reported `MISSING` for every program rather than defaulted to
anything else.

**Consolidation exposes field provenance: PASS.**

---

## 5. Residual-question ledger (Task 5)

New: `app/services/canonical_residual_ledger.py`.

`ledger_entry_for(canonical_program_id)` derives, purely from the
consolidation view, the exact list of unresolved required dimensions (any
status other than `PRESENT`) with each dimension's own provenance detail
string. `full_residual_ledger(canonical_program_ids)` runs this over an
explicit, caller-supplied program list — this module invents no program
list of its own; the P0 backlog scope remains exactly what
`CODEX_AUTHORITY_GAP_PROGRAM_INTEGRITY.md` already established.

**Residual-question ledger: PASS.** UK AVEC's ledger reports (among
others) `RATE_OR_AWARD_BASIS` and `TERRITORIALITY` as open questions, each
with a real detail string ("2 RateRule(s) exist with confidence_tier
['PARSED'] ... not yet accepted as executable"). Greece's ledger reports
fewer open questions than UK AVEC's (optional dimensions like
`UPLIFT_RULES` remain open even for a fully priceable program — that is
expected and correct, not a defect).

---

## 6. Atomic publication contract (Task 6)

New: `app/services/canonical_publication_contract.py`.

`executable_completeness(canonical_program_id)` gates `EXECUTABLE_COMPLETE`
on exactly two dimensions, confirmed by reading `program_rate_rules.py::
resolve_program_rate()` to be the TRUE hard blockers for this served
pipeline:

- `RATE_OR_AWARD_BASIS` — without a VERIFIED `RateRule`,
  `resolve_program_rate()` returns `None` outright.
- `ELIGIBLE_PRODUCTION_TYPE` — a `RateRule` with an empty
  `production_types` tuple can never match ANY production (`production_type
  not in rule.production_types` is unconditionally `True` for an empty
  tuple), so it can never resolve either.

`QPE_DEFINITION`, `TERRITORIALITY`, `MINIMUM_SPEND`, and `CAP` are
deliberately NOT required for this specific gate (they remain tracked and
disclosed via the consolidation view and residual ledger): `derive_
qualification_register()` never fails or blocks on their absence — the
canonical QPE rule ("included unless explicitly excluded") and each
program's own doctrine supply a defensible fallback. **Proof**: Greece's
own accepted, `PRICEABLE_VALIDATED`, currently-priced program has zero
explicit category `SpendRule`s (`QPE_DEFINITION=PARTIAL`) and no
`territorial_only` rule (`TERRITORIALITY=MISSING`) today, and prices
correctly in the live served FVD universe regardless — treating those as
hard blockers here would have incorrectly failed this system's own
already-accepted, already-working economics.

### AUTHORITY_CLOSED ≠ EXECUTABLE_COMPLETE — verified two ways

1. **Behaviorally**: `docs/validation/CODEX_AUTHORITY_GAP_PROGRAM_INTEGRITY.json`
   labels `uk_avec`'s `canonical_disposition` as `"AUTHORITY_CLOSED"`.
   `executable_completeness("uk_avec")` independently returns
   `NOT_EXECUTABLE_COMPLETE` with `unresolved_required_dimensions =
   ("RATE_OR_AWARD_BASIS", "ELIGIBLE_PRODUCTION_TYPE")` — read purely from
   runtime executable data.
2. **Structurally**: `canonical_publication_contract.py`'s own imports
   never reference `authority_coverage_registry`, `coverage_state`,
   `blocks_economic_candidacy`, or any validation-artifact loader —
   confirmed by AST inspection in
   `test_publication_contract_never_imports_authority_closed_concept`.
   There is no code path by which a research-closure label could promote
   a program to executable-complete here, by construction, not just by
   current behavior.

**`AUTHORITY_CLOSED` can imply `EXECUTABLE_COMPLETE`: NO.**

---

## 7. Control-program results (Task 8)

| Program | canonical_program_id | Identity | Consolidation dims | Residual questions (open) | Executable completeness |
|---|---|:-:|:-:|:-:|---|
| **Priceable control** — Greece Cash Rebate | `gr_cash_rebate` | PASS | 14/14 reported | 10 (optional dims only — UPLIFT_RULES, MONETIZATION, etc.) | **EXECUTABLE_COMPLETE** |
| **P0 control** — UK AVEC | `uk_avec` | PASS | 14/14 reported | 12 (including RATE_OR_AWARD_BASIS, ELIGIBLE_PRODUCTION_TYPE) | **NOT_EXECUTABLE_COMPLETE** |
| **P0 control** — Canada federal PSTC | `ca_federal_pstc` | PASS | 14/14 reported | 13 | **NOT_EXECUTABLE_COMPLETE** |
| **P0 control** — US California | `us_ca_film_credit` | PASS | 14/14 reported | 12 | **NOT_EXECUTABLE_COMPLETE** |

No missing rule was fixed for any of the three P0 controls — this task
does not attempt to close any authority gap; it proves the substrate can
correctly represent the gap.

---

## 8. Remaining P0 authority backlog

Unchanged from `CODEX_AUTHORITY_GAP_PROGRAM_INTEGRITY.md` — 74 traditional/
formulaic programs remain `CORE_PROGRAM_INCOMPLETE` (1 additional program,
Kazakhstan, remains `PROGRAM_TYPE_UNRESOLVED`). This repair adds no new
research and closes no backlog item; `full_residual_ledger()` now gives
the next research phase one deterministic, machine-readable entry point
into that exact backlog (scoped explicitly by the caller, e.g. the 75
program list Codex already established), instead of requiring a fresh
manual audit of scattered registries each time.

---

## 9. Little Utopia regression (Task 9)

Runtime-verified via `evaluate_project()` and the live served
`/api/v1/cineglobe/projects/{LU}/state` endpoint (LU's own demo path,
`app.demo.little_utopia_state`, entirely untouched by this repair):

- Budget: **$4,364,393** — unchanged.
- Winner/current: **Mauritius** — unchanged.
- NPC: **$3,057,794.90** — unchanged, exact.

**LU regression: PASS.**

---

## 10. FVD runtime verification (Task 10)

Runtime-verified via `evaluate_project()` and the live served
`/api/v1/cineglobe/projects/{FVD}/state` endpoint:

- Generated: **110**
- Priced: **30**
- Unpriceable: **80**
- Distinct QPE values: **3**
- Distinct incentive values: **9**
- Distinct NPC values: **9**

Three previously marine-rejected landlocked jurisdictions (MN, UZ, AT)
confirmed remaining in the economic universe with feasibility mismatch
preserved — see §2 table.

**Repeated QPE values are not claimed solved.** They remain
`LEGITIMATELY_EQUAL_UNDER_CANONICAL_RULES` for the reason established by
the prior FVD canonical input assembly repair (identical
`OPEN_DEFAULT_INCLUDE` doctrine applied to the same real budget-account
universe) — authority completeness (§8) is confirmed here as a separate,
unresolved, explicitly out-of-scope problem, not something this closeout
addresses.

---

## Runtime evidence classification

| Claim | Evidence |
|---|---|
| Feasibility no longer suppresses discovery (MN/UZ restored) | **RUNTIME VERIFIED** — `evaluate_project()` + live `/state` endpoint |
| AT unpriceable-but-feasibility-WEAK independence | **RUNTIME VERIFIED** |
| AU real statutory rejection still works | **RUNTIME VERIFIED** |
| FVD 110/30/80 | **RUNTIME VERIFIED** — re-run, not hard-coded |
| LU exact regression | **RUNTIME VERIFIED** — live served endpoint |
| Canonical identity alias resolution | **RUNTIME VERIFIED** — `resolve_identity()` executed |
| Consolidation confidence-tier distinction (UK AVEC PARSED vs. GR VERIFIED) | **RUNTIME VERIFIED** — read from live `program_rate_rules` registry |
| AUTHORITY_CLOSED ≠ EXECUTABLE_COMPLETE (behavioral) | **RUNTIME VERIFIED** — cross-checked against the real validation JSON |
| AUTHORITY_CLOSED ≠ EXECUTABLE_COMPLETE (structural, no import) | **STATIC VERIFIED** — AST inspection |
| Control program table (§7) | **RUNTIME VERIFIED** |
| No frontend file changed | **STATIC VERIFIED** — `git status` scoped diff |

No claim in this artifact is BLOCKED.

---

## Scope discipline

- **`production_discovery.py` was not modified.** The feasibility/
  eligibility fix is entirely a handoff-point change in
  `canonical_evaluation.py` (calling the existing, unmodified discovery
  function twice with different inputs) plus one small, additive
  disclosure-field addition in `canonical_production_view.py`.
- **No optimizer rewrite, no registry replacement, no LU special-runtime
  deletion, no 74-program migration, no new research, no rate/QPE/
  threshold/cap/monetization/ranking/frontend change.**
- **Files touched**: `canonical_evaluation.py`, `canonical_production_view.py`
  (both already touched by the immediately preceding repair; this is a
  continuation, not new scope), four new `app/services/canonical_program_
  *.py` / `canonical_residual_ledger.py` / `canonical_publication_contract.py`
  modules (Tasks 3-6, purely additive), and targeted tests. No existing
  registry file (`authority_coverage_registry.py`, `program_spend_rules.py`,
  `program_rate_rules.py`, `global_inventory.py`, `jurisdiction_comparison.py`,
  `program_slug_aliases.py`) was modified — all are read-only dependencies
  of the new substrate.

---

## Tests

`pytest` — 4155 passed, 1 pre-existing unrelated failure
(`test_scenarios_and_workspace_both_use_the_canonical_title_formatter`,
`Workspace.jsx` vs `scenarioDisplay()` — predates this session, outside
this repair's scope, previously reported, not re-fixed here), 1 skipped.

New: `tests/test_canonical_authority_substrate.py` (24 tests) — covering
all 14 items in the task's test list (feasibility/eligibility
independence, UNKNOWN feasibility, SA-1/local-entity preservation, alias
resolution, field provenance, missing-fields-stay-missing,
AUTHORITY_CLOSED independence both behavioral and structural, residual
ledger, publication contract for both complete and incomplete programs,
the four control programs, LU exact regression, FVD runtime regression).

Updated: two stale hardcoded FVD counts in `test_canonical_served_wiring_
repair.py` and one inverted test premise in `test_fvd_canonical_input_
assembly_repair.py`, reverted from the immediately preceding repair's
28/61/89 back to the accepted 30/80/110 baseline.

---

## Final gate

**`CANONICAL_AUTHORITY_SUBSTRATE_ACCEPTED`**

Soft feasibility no longer suppresses economic discovery. SA-1
requirements remain preserved (now correctly scoped to feasibility
disclosure, not eligibility rejection). Canonical program identity exists
(224 distinct programs, alias resolution verified). Field consolidation
exists (14 dimensions, confidence-tier-aware, provenance-attributed).
Residual-question ledger exists (deterministic, scoped, non-inventive).
`AUTHORITY_CLOSED` cannot masquerade as executable completeness — verified
both behaviorally and structurally. No authority research was performed.
No incentive economics were changed. LU exact regression passes. FVD
runtime (110/30/80) passes. Frontend untouched. All tests pass.
