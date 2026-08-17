# Global Base Priceability Closeout

**Final gate: `GLOBAL_BASE_PRICEABILITY_RECOVERED`**

Restores base formulaic priceability using only existing authoritative
data, per Codex's optimizer-doctrine/priceability lineage trace
(`docs/validation/CODEX_OPTIMIZER_DOCTRINE_PRICEABILITY_LINEAGE.json`) and
the explicit mid-task correction narrowing scope to global base data +
pricing integrity only. **No optimizer-structure restoration was
performed** — split/component, grant/fund stacks, official treaty
co-production, hybrid/anchor, in-kind/support, and reinvestment all remain
explicitly deferred, per direct instruction, to a later phase.

---

## 1. What Codex found, precisely

The 14-dimension authority-completeness framework does **not** gate served
pricing — `canonical_evaluation.py` never imports it. Served candidacy is:
`authority_coverage_registry.blocks_economic_candidacy()` →
`resolve_program_doctrine()` → `get_rate_rules()` → `resolve_program_rate()`
→ `_price_candidate()`. Three narrower, independently real problems:

1. `canonical_publication_contract.priceability()` was gated on
   VERIFIED-tier consolidation data — not what the served engine actually
   checks. 27 false negatives, 1 false positive (`us_ga_film_credit`).
2. 21 formulaic canonical identities were never bound to a
   `jurisdiction_comparison` profile at all (`jurisdiction_code=""`) —
   structurally invisible to discovery, though none carry a RateRule
   either way.
3. `authority_completeness()`'s `NOT_APPLICABLE`/
   `AUTHORITATIVE_SILENCE_CONFIRMED` states were defined but never
   emitted, producing a universally-MISSING-looking result even for
   dimensions a program genuinely lacks (e.g. Georgia's own citation says
   "No annual cap" — the field was never read for that confirmation).

---

## 2. Task 2 — Georgia: the artificial-schema blocker

**Root cause**: `authority_coverage_registry.py`'s `georgia_eiia`/
`us_ga_film_credit` rows vetoed the program despite it being the *only*
one of the 95 unavailable formulaic programs with a VERIFIED-tier
RateRule contradicting that veto (two VERIFIED tiers, explicit doctrine,
territorial SpendRule — all cited to O.C.G.A. § 48-7-40.26). Every other
`UNPRICEABLE_AUTHORITY_INSUFFICIENT` row was cross-checked and found
consistent (zero VERIFIED RateRules) — this is a one-row data correction,
not a reopening of the veto list.

**Fix**: both rows removed (absence = `PRICEABLE_VALIDATED` by this
registry's own design). `ENGINE_VERSION` bumped `canonical-1.4.0` →
`canonical-1.5.0` so cached `StructureCalculationResult` rows (keyed on
project-input fingerprint, which never covers registry contents) don't
silently keep serving the pre-fix veto to already-evaluated projects.

**Runtime proof**: FVD's US-GA candidate now prices — QPE $4,054,196,
guaranteed floor $810,839.20 (20%), ceiling $1,216,258.80 (30% with
approved-logo uplift), NPC $3,553,553.80 — with its full 37-line
qualification trace and statutory exclusions (legal fees, undeployed
contingency) preserved alongside the number.

**Generalized, not special-cased**: the fix is a registry-data correction
plus the `priceability()` rewrite below, both applied uniformly. Georgia
is evidence the contract works, not a hardcoded exception anywhere in
code.

---

## 3. Task 1 — one coherent priceability contract

`priceability()` rewritten to delegate directly to the same four
predicates the served engine calls: `blocks_economic_candidacy()` →
`resolve_program_doctrine()` → `get_rate_rules()` (any confidence tier)
→ at least one rule with a non-empty `production_types`. It answers
Codex's "intrinsic priceability" question — would some real project stand
a chance here, before any project-specific type/threshold mismatch. No
project-specific `resolve_program_rate()` call (this function has no
project). `PriceabilityResult.blocker` added
(`COVERAGE_REGISTRY_VETO` / `NO_DOCTRINE_RESOLVES` / `NO_RATE_RULES` /
`NO_ELIGIBLE_PRODUCTION_TYPE`) so a caller knows *why* without a second
lookup. `authority_completeness()` untouched — still fully independent,
still never reads the coverage registry (verified structurally by a
narrowed regression test).

---

## 4. Task 3 — program-specific N/A

Added a narrow, evidence-gated `CAP` → `NOT_APPLICABLE` detector: scans a
program's **VERIFIED** RateRule citation text for an explicit confirmed-
absence phrase ("no annual cap", "uncapped", etc.) — never inferred from
a bare missing field. Discovered directly from Georgia's own citation.
`NOT_APPLICABLE` and `PRESENT` rank equally in the upgrade logic, so this
can only ever fill a genuine `MISSING`/`PARTIAL` gap, never override a
real `CAP` rule found elsewhere. `ca_federal_pstc` (no VERIFIED RateRule
at all) correctly stays `MISSING` — regression-tested.

---

## 5. Task 1 (identities) — the 21 disconnected programs

Traced each: `canonical_program_identity.py`'s `_jurisdiction_name_type()`
fell through to a bare coverage-registry row (`jurisdiction_code=""`)
because `global_inventory.ALL_PROGRAMS` carries a real, name-matching
entry (sometimes with a discovery-tier `base_rate`) for 15 of the 21, but
with `program_slug=None` — discovered, never bound. Added a read-only,
unique-exact-normalized-name fallback match (only reached when no
slug-based binding exists at all — purely additive, cannot change an
existing binding). **15 of 21 now carry a real `jurisdiction_code`**; 6
(`au_nsw_screen`, `ca_federal_cptc`, `in_national_film`,
`mx_eficine_incentive`, `on_ofttc`, `qc_film_production`) have no matching
`global_inventory` entry at all and remain honestly unbound.

**Deliberately NOT wired into the live discovery/candidate-generation
loop** (`production_discovery.discover_executable_jurisdictions()`): an
initial attempt to extend that loop to examine multiple programs per
jurisdiction code was written, found to corrupt two downstream
assumptions (`feasibility_by_code`'s per-code dict lookup, and duplicate
`capability_only_jurisdictions` candidate rows for a jurisdiction
examined twice), and **reverted** before being committed. Since none of
the 21 carry any RateRule (confirmed, before and after the identity fix),
none could ever flip to `PRICED` by this binding alone — the concrete
value of touching the live discovery loop was low, the regression risk to
LU/FVD candidate generation was real and demonstrated, and the interrupt
message's stop condition explicitly protects optimizer candidate-
generation structures. The identity-layer fix alone is sufficient to make
their terminal status honestly `ECONOMIC_INPUT_GENUINELY_MISSING` via
`priceability()`, which is what Task 6/7's terminal accounting needs.

---

## 6. Task 4/5 — reassessing the 94 remaining blockers

All 94 programs still `UNPRICEABLE` after the Georgia fix share the exact
same blocker: `COVERAGE_REGISTRY_VETO`. Checked every one, individually,
for a VERIFIED RateRule that would contradict its veto (the same
mechanical check that isolated Georgia) — **zero found**. This is not
"generic AUTHORITY_INSUFFICIENT" concealing a specific fact: the exact
indispensable missing proposition for all 94 is *an authority-adjudicated,
sufficiently-reliable rate/award basis* — some already carry PARSED/
DISCOVERY-tier claims the original curatorial review considered
insufficiently reliable to price from (a deliberate editorial judgment
from an earlier remediation phase, not an oversight); reopening that
judgment per-program, the way Georgia's case was individually proven, is
exactly the next targeted research workload — never a blanket reversal of
73+ editorial calls without new evidence.

---

## 7. Task 6/7 — terminal accounting

126 formulaic programs, exactly two terminal states, sum verified:

| | Count |
|---|---:|
| Formulaic total | 126 |
| PRICED (program-level, `priceability()`) | **32** (was 31 before Georgia) |
| ECONOMIC_INPUT_GENUINELY_MISSING | **94** |
| Unexplained/unclassified | **0** |

Every one of the 94 carries an explicit blocker
(`COVERAGE_REGISTRY_VETO`) and an identifiable missing proposition class
(§6) — never a bare failure.

---

## 8. Task 8 — inventory integrity check

- Re-checked all 65 `PROGRAM_TYPE_UNRESOLVED` identities against every
  richer registry: **0 additional formulaic classifications recoverable**
  beyond the 23 already recovered in the prior Codex-delta-recovery task.
  The jurisdiction_code fix in this task additionally bound 22 of the 65
  to a real code, but their program TYPE remains genuinely ambiguous or
  cross-source-conflicting — a code binding doesn't resolve a type
  ambiguity.
- **0 orphan `global_inventory` programs** found outside the 224 canonical
  identities (every slug-bound `GlobalProgramEntry` maps to a known
  identity).

---

## 9. Requirements survival (Task 6)

Georgia's priced FVD structure retains its complete 37-account-code
qualification trace (why each account qualifies or is excluded, with
statutory citations — e.g. Georgia DOR's legal-fee exclusion, the
undeployed-contingency structural exclusion) and its warnings (MFNI/
relocation-cost normalization not yet generically applied) alongside the
numeric result. Nothing was stripped to make it price. **0** priced
scenarios lost their requirements; **0** requirements incorrectly
suppressed a calculable price.

---

## 10. Runtime verification (Task 9)

| | LU | FVD |
|---|---:|---:|
| Total candidates | 110 | 110 |
| Priced | 31 | 31 |
| Unpriced | 79 | 79 |

**LU baseline (Mauritius) `true_net_cost_usd` = $3,057,794.90 — exact,
unchanged.** This is the single most load-bearing control value in this
entire lineage; regression-tested directly.

**FVD's `us_ga_film_credit`** — the concrete, traced proof the fix reaches
served state, not just the read-only publication layer:
`is_fully_priced=True`, `candidate_status="PRICED"`, `selected_incentive_
usd=810839.20`, `npc_verified_usd=3553553.80`, statutory basis O.C.G.A.
§ 48-7-40.26.

Both projects' priced count moved 30→31 (Georgia, the one repaired false
blocker) — no other candidate's status changed, confirmed by re-running
the full FVD candidate-universe test (`test_fvd_runtime_candidate_
universe_restored`, updated in place with the new, verified counts) and
the existing feasibility-disclosure controls (MN/UZ/AT marine-mismatch
warnings unchanged).

---

## 11. Deferred optimizer ledger (preserved, not touched)

| Structure | Status |
|---|---|
| Split/component | `LOST_OR_DISCONNECTED` — deferred |
| Grant/fund stack | `LOST_OR_DISCONNECTED` — deferred |
| Official treaty co-production | `LOST_OR_DISCONNECTED` — deferred |
| Hybrid/anchor | `LOST_OR_DISCONNECTED` — deferred |
| In-kind/support | `LOST_OR_DISCONNECTED` — deferred |
| Reinvestment | Deferred for later product/economic re-evaluation (per explicit instruction) |

None of these were touched, reopened, or redesigned. This finding stays
on the project ledger for the next phase.

---

## 12. Zero blast radius / scope discipline

- `canonical_program_consolidation.py` / `canonical_publication_
  contract.py` / `canonical_residual_ledger.py`: still imported by no
  pricing/discovery/optimizer path except the identity module's own
  comment references (grep-confirmed) — `priceability()`'s served-
  predicate rewrite is a coincidental *read of the same functions* the
  served engine reads, not a new coupling between the publication layer
  and the served path.
- The only files that touch the actual served pricing chain are
  `authority_coverage_registry.py` (one-row Georgia data correction) and
  `canonical_evaluation.py` (one-line `ENGINE_VERSION` cache-invalidation
  bump, no logic change).
- `production_discovery.py`: attempted change reverted; file unchanged
  from before this task.
- No frontend file touched. No external research performed.

---

## 13. Testing

7 new focused tests, 2 updated (FVD's priced/unpriced counts reflecting
the verified Georgia fix; the publication-contract structural-independence
test narrowed to the correct, permanent invariant — `authority_
completeness()` must never read the coverage registry;
`priceability()` now correctly and intentionally does). **49/49 pass.**
Full suite not rerun (no shared pricing/optimizer logic changed beyond
the two narrow files above).

---

## Final gate rationale

**`GLOBAL_BASE_PRICEABILITY_RECOVERED`**: every existing-data-recoverable
formulaic price is restored (Georgia, proven with real numbers in served
runtime); all 126 formulaic programs terminate as exactly `PRICED` or
`ECONOMIC_INPUT_GENUINELY_MISSING`, summing to 126 with zero unclassified;
the 21 disconnected identities are repaired at the identity layer (their
true state — zero RateRules — is now honestly surfaced, not hidden behind
an empty jurisdiction_code); the 94 remaining unpriced programs each carry
an exact, identified missing-proposition class rather than a generic
label; requirements survive on priced results; LU's control NPC is
unchanged; FVD's Georgia candidate is priced with real, traced numbers.
Optimizer-structure restoration was explicitly and correctly not
attempted — that ledger is preserved for the next phase.
