# Authority Completeness Contract Correction

**Status: `AUTHORITY_COMPLETENESS_CONTRACT_ACCEPTED`**

Narrow semantic correction to commit `770006b`. The publication contract
introduced there (`canonical_publication_contract.py`) conflated "the
current engine can produce a number" with "the authority record is
actually complete." This corrects that conflation without touching
pricing, discovery, the optimizer, the feasibility/eligibility separation,
canonical identity, or the frontend.

---

## The permanent distinction

Two independent questions, now two independent contracts:

1. **Runtime priceability** — `priceability()` → `PRICEABLE` /
   `UNPRICEABLE`. Can the EXISTING engine currently produce a defensible
   number? Gated on the two dimensions confirmed (by reading
   `program_rate_rules.py::resolve_program_rate()`) to be true hard
   blockers: `RATE_OR_AWARD_BASIS`, `ELIGIBLE_PRODUCTION_TYPE` — unchanged
   from commit `770006b`'s logic, renamed for clarity (`EXECUTABLE_COMPLETE`
   → `PRICEABLE`).

2. **Authority completeness** — `authority_completeness()` (new) →
   `AUTHORITY_COMPLETE` / `AUTHORITY_INCOMPLETE`. Has the governing
   incentive authority actually been resolved across ALL 14 tracked
   material dimensions? A dimension only counts as resolved when a human
   has actually closed the question — `PRESENT`, `NOT_APPLICABLE` (primary
   authority confirms the dimension genuinely doesn't apply), or
   `AUTHORITATIVE_SILENCE_CONFIRMED` (a researcher has confirmed the
   source's silence is itself the finding). `PARTIAL`, `MISSING`, and
   `CONFLICT` always leave the program incomplete — including the case
   where the engine's own doctrine fallback (`OPEN_DEFAULT_INCLUDE` /
   canonical QPE rule) still lets it price.

**Default inclusion is not authority completeness.** CineGlobe's canonical
QPE doctrine ("every budget line is included unless authoritative program
language explicitly excludes it") is untouched and still governs pricing —
but a program pricing successfully via that fallback says nothing about
whether its territoriality, caps, cultural test, uplift rules, etc. were
ever actually reviewed.

`PRICEABLE + AUTHORITY_INCOMPLETE` is valid, common, and expected — not a
contradiction.

---

## What changed

- **`canonical_program_consolidation.py`**: added the
  `AUTHORITATIVE_SILENCE_CONFIRMED` status constant (alongside the
  already-existing `PRESENT`/`PARTIAL`/`MISSING`/`NOT_APPLICABLE`/
  `CONFLICT`) and two classification sets,
  `RESOLVED_FOR_AUTHORITY_COMPLETENESS` (`PRESENT`, `NOT_APPLICABLE`,
  `AUTHORITATIVE_SILENCE_CONFIRMED`) and
  `UNRESOLVED_FOR_AUTHORITY_COMPLETENESS` (`PARTIAL`, `MISSING`,
  `CONFLICT`). `consolidate()`'s own field-reading logic is **unchanged**
  — it still only ever produces `PRESENT`/`PARTIAL`/`MISSING` from current
  runtime data, since no primary-source research was performed in this
  task; `NOT_APPLICABLE`/`AUTHORITATIVE_SILENCE_CONFIRMED` remain reserved
  for a future research pass to set, with its own citation.
- **`canonical_publication_contract.py`**: rewritten to expose two
  functions instead of one. `priceability()` preserves the exact prior
  logic and dimension set (renamed constants only:
  `EXECUTABLE_COMPLETE`→`PRICEABLE`, `NOT_EXECUTABLE_COMPLETE`→
  `UNPRICEABLE`, `executable_completeness()`→`priceability()`). New
  `authority_completeness()` evaluates all 14 `REQUIRED_DIMENSIONS`
  against `RESOLVED_FOR_AUTHORITY_COMPLETENESS`. Still imports nothing
  from `authority_coverage_registry` or any validation artifact — same
  structural guarantee as before, now covering both functions.
- **`canonical_residual_ledger.py`**: `_UNRESOLVED_STATUSES` now reuses
  `UNRESOLVED_FOR_AUTHORITY_COMPLETENESS` directly (adds `CONFLICT` to the
  prior `MISSING`/`PARTIAL`-only set) so the ledger and
  `authority_completeness()` can never silently drift apart — verified by
  `test_residual_ledger_is_exact_match_for_authority_incomplete_dimensions`.

No other file changed. No pricing, qualification, QPE, discovery, or
authority-veto code touched. No authority-rule or jurisdiction data
touched. No frontend file touched.

---

## Control program proof

| Program | `priceability()` | `authority_completeness()` | Unresolved material dimensions |
|---|---|---|---|
| **Greece** (`gr_cash_rebate`) | `PRICEABLE` | `AUTHORITY_INCOMPLETE` | 10 of 14 (QPE_DEFINITION, TERRITORIALITY, CULTURAL_OR_CONTENT_TEST, UPLIFT_RULES, RESIDENT_NONRESIDENT_TREATMENT, PAYROLL_TREATMENT, MONETIZATION, REFUNDABILITY, TRANSFERABILITY, APPLICATION_TIMING) |
| **GB AVEC** (`uk_avec`) | `UNPRICEABLE` | `AUTHORITY_INCOMPLETE` | 12 of 14 |
| **Canada federal PSTC** (`ca_federal_pstc`) | `UNPRICEABLE` | `AUTHORITY_INCOMPLETE` | 13 of 14 |
| **US California** (`us_ca_film_credit`) | `UNPRICEABLE` | `AUTHORITY_INCOMPLETE` | 12 of 14 |

Greece proves `PRICEABLE + AUTHORITY_INCOMPLETE` directly: it prices
correctly in the live served FVD/LU universe via doctrine fallback (zero
explicit `QPE_DEFINITION` category rules, no `TERRITORIALITY`
`territorial_only` rule), and is correctly, independently reported
`AUTHORITY_INCOMPLETE` — it was **not** forced to `AUTHORITY_COMPLETE`
merely because it currently prices.

## AUTHORITY_CLOSED ≠ AUTHORITY_COMPLETE

`uk_avec`'s `canonical_disposition` in
`docs/validation/CODEX_AUTHORITY_GAP_PROGRAM_INTEGRITY.json` is
`"AUTHORITY_CLOSED"`. `authority_completeness("uk_avec")` independently
returns `AUTHORITY_INCOMPLETE`, computed entirely from runtime
consolidation data. `canonical_publication_contract.py` imports nothing
from `authority_coverage_registry` or any validation-artifact loader
(re-verified by AST inspection) — there is no code path by which a
research-closure label could promote a program to complete.

---

## Runtime verification

- **LU**: `evaluate_project()` + live `/api/v1/cineglobe/projects/{LU}/state`
  — winner Mauritius, `NPC = $3,057,794.90`, exact, unchanged.
- **FVD**: `evaluate_project()` + live `/api/v1/cineglobe/projects/{FVD}/state`
  — 110 generated, 30 priced, 80 unpriceable, exact, unchanged.

Both economics untouched — this correction is a classification-layer
addition only.

---

## Tests

Focused suite only (`tests/test_canonical_authority_substrate.py`, updated
in place — 32 tests, up from 24), plus the two runtime smoke checks above.
The full 4000+ backend suite was NOT rerun per this task's explicit
scope-limiting instruction; no shared code outside the three named
publication/consolidation/ledger files was touched, so no broader
regression is plausible.

New/updated coverage: `PRESENT`/`NOT_APPLICABLE`/`AUTHORITATIVE_SILENCE_
CONFIRMED` resolve; `PARTIAL`/`MISSING`/`CONFLICT` remain unresolved; the
resolved/unresolved sets are disjoint and exhaustive over all five defined
statuses; `priceability()` and `authority_completeness()` are independent
(Greece proof); the residual ledger exactly matches
`authority_completeness()`'s unresolved-dimension set for all four
controls; `AUTHORITY_CLOSED` cannot promote completeness (behavioral +
structural); all four controls' full identity/consolidation/ledger/
completeness chain.

---

## Final gate

**`AUTHORITY_COMPLETENESS_CONTRACT_ACCEPTED`**

Priceability and authority completeness are permanently independent. All
14 material dimensions participate in authority completeness.
`NOT_APPLICABLE`/`AUTHORITATIVE_SILENCE_CONFIRMED` can close a dimension;
`PARTIAL`/`MISSING`/`CONFLICT` cannot. The residual ledger is exact.
`AUTHORITY_CLOSED` cannot imply completeness. Economics unchanged. FVD
remains 110/30/80. LU Mauritius NPC remains exactly $3,057,794.90. No
frontend, rule, or authority-data change occurred.
