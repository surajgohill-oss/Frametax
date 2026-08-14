# Script Analyzer SA-1 — Closeout

Date: 2026-08-14
Branch: `claude/audit-frametax-features-NZcX5`
Architecture consumed: `04bb530` — `SCRIPT_ANALYZER_CANONICAL_ARCHITECTURE.json` (controls where sources conflict)
Companion artifact: `SCRIPT_ANALYZER_SA1_VERIFICATION.json`

## What SA-1 set out to prove

A production-grade vertical slice: that a **generic** project — any project with a text-based screenplay — can go from an uploaded document to a fingerprinted optimizer input without any Little Utopia-specific upstream assembly. Not the whole Script Analyzer; the spine of it.

## The chain, end to end

```
DocumentVersion (checksum = identity)
  → ScreenplayDocument (typed projection, version-scoped)
  → deterministic structural parse (no AI)
  → Scene / Character / SceneElement
  → derived ProjectFacts (with provenance)
  → ProductionRequirements + scripted LocationRequirements
  → CanonicalProductionState (immutable, fingerprinted)
  → ProductionOptimizerInput  — or a stated refusal
```

Every step above is **RUNTIME VERIFIED** against a live backend and a real non-Little-Utopia project (`SA1 Generic Test Project`, `fc31e468…`). Full evidence in the verification JSON.

## What was reused rather than rebuilt

The existing `screenplay_parser.py` is untouched and still serves its existing callers; the new `screenplay_structural_parser.py` sits alongside it for the canonical structure. `ScreenplayDocument`, `ExtractedScriptElement` and `ProjectLocationRequirement` were **extended** (all columns additive and nullable), not replaced. `ProjectFact` carries the derived facts. The budget taxonomy, and the entire optimizer — discovery, structure composition, allocation, normalization, incentive evaluation, NPC, ranking and Bridge — were not modified at all.

New: `Scene`, `Character`, `ProductionRequirement`, `ProductionAssumption`, the parse-status enum, the parse/persist service, the state builder and the handoff adapter.

Migration `0067` is additive-only and was proven reversible — downgrade to `0066` and re-upgrade both ran cleanly against the live database.

## The rules this phase had to hold, and how

**Ambiguity stays UNKNOWN.** A slugline the parser cannot normalise yields `INT_EXT=UNKNOWN` / `DAY_NIGHT=UNKNOWN`. Verified by test and by `CONTINUOUS` surviving as its own value rather than being collapsed into DAY or NIGHT.

**Page eighths come from real layout.** Form-feed and ascending page-marker layouts are detected and used. `word_count/200` is the fallback *only* when no layout exists at all, and the result is then stamped `APPROXIMATE_NO_LAYOUT` with an explicit warning — so an approximate page count can never be mistaken for a real one. The test fixture exercises both paths.

**Presence is evidence; scale is not.** This is the rule the architecture states most forcefully, and it is enforced structurally: every SA-1 element and requirement is written with `quantity=NULL`, `unit=NULL`, `is_interpretation=False`. *"A horse appears in scene 5"* is persisted with its source span; *"2 trained horses for 5 days"* is not derivable from anything SA-1 writes.

**Stage vs practical is never chosen by software.** Every scripted `LocationRequirement` is written with `production_approach="UNKNOWN"` and `production_location=NULL`, and the canonical state emits an explicit unknown for each one.

**Territoriality is never inferred from the payer.** Every budget line in the optimizer input carries `territorial_basis="UNKNOWN"` and a null service-performed jurisdiction. A labor line whose residency the source does not state is reported `UNKNOWN` — not assumed resident. The state says so out loud in its unknowns.

**A failed parse never degrades into estimates.** The seven-state parse enum treats `SCRIPT_PARSE_FAILED` and `SCRIPT_PARSE_BLOCKED_SCAN_ONLY` as terminal-until-human. There is no path from a failed parse to a substituted page count.

**Version scoping is real.** Identity comes from `DocumentVersion.checksum_sha256`, never the filename. Re-parsing an unchanged version is a no-op (`reparsed=false`). A revised screenplay became a **second** `ScreenplayDocument` with its own 6 scenes while the original kept its own 5 — nothing overwritten, both lineages intact and independently queryable.

## Optimizer handoff — both paths proven

The adapter translates and refuses; it contains no economics.

- **Script-only project** → `BLOCKED_INCOMPLETE_INPUTS`, `accepted=false`, `optimizer_input=null`, `BUDGET_MISSING` stated. This is the correct SA-1 outcome, not a failure.
- **After attaching a 6-line budget and USER_CONFIRMED assumptions** → `READY_FOR_OPTIMIZER`, `accepted=true`, `ProductionOptimizerInput sa1-1.0.0` emitted with gross $1,720,000, 24 shoot days, base jurisdiction MT, and `provisional=true` because unknowns remain. Provisional output is never labelled actual.

The state fingerprint is a digest of every source version and effective value, deliberately excluding the clock — identical inputs fingerprint identically, so a stored optimizer result can always be traced to exactly the inputs that produced it.

## Little Utopia

Used strictly as a regression fixture. Its upstream assembly was not modified. Served result byte-identical: **177 structures, 48 priced, MU baseline NPC $3,057,794.90, rank-1 `ALLOC-BASELINE-MU`**.

## Tests

23 new focused tests in `tests/test_script_analyzer_sa1.py` — scene/INT-EXT/day-night parsing, ambiguity preservation, form-feed vs approximate paging, eighths, character/dialogue linkage, `(CONT'D)` alias resolution, transition-vs-character rejection, taxonomy containment, the presence-not-scale rule, deferred-capability exclusion, derived-fact consistency, failure handling, fingerprint behaviour and handoff refusal.

Full backend suite: **4054 passed, 1 skipped, 1 pre-existing unrelated failure** (frontend `Workspace.jsx` title-formatter guard, zero local diff on that file).

## Deferred, deliberately

AI extraction and the multi-model Bridge workflow; the full breakdown taxonomy and all complexity/VFX/stunt interpretation; the schedule engine and estimated shoot-day engine; L1/L2/L3 budget estimation; the local rate database and union/CBA data; UI and confirmation UX. Cross-draft scene lineage is left explicitly null rather than inferred.

## Carried forward into SA-2

Two honest limits worth stating: PDF text-layer extraction is not yet wired into the projection helper (the caller supplies `raw_text`; a scan-only source is correctly blocked rather than guessed), and while `ProductionOptimizerInput` is emitted and fingerprinted, it is not yet consumed by a generic end-to-end optimizer run — Little Utopia remains the only production-grade optimizer path.

## Gate

**`GO_FOR_SCRIPT_ANALYZER_SA2`**
