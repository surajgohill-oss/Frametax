# AUDIT CONTROL AND DENOMINATORS: CINEGLOBE OPTIMIZER & STACKING AUDIT

**Audit Document Version:** 2.0 (Independent Read-Only Audit)  
**Date:** October 9, 2026  
**Auditor:** Independent Audit Agent (Antigravity)  
**Worktree:** `/Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2`  
**Reference Tip:** `origin/claude/global-optimizer-remediation` (`49f5c90591f18480dc32d4e74510a9899f0a000a`)  
**Acceptance Database:** `frametax2_claude_optimizer_acceptance_20260919`  

---

## 1. CONTROLLING ACCEPTANCE REQUIREMENTS & LEDGER BASELINE

This audit derives its controlling standards from `PROJECT_RULES.md` and the authoritative entries in `docs/architecture/CAPABILITY_LEDGER.md`:

1. **Two-Axis Correction (`PROJECT_RULES.md`, 2026-09-02):**
   - Economic determinism and structured-provenance completeness are independent axes.
   - Any program carrying a real, previously adjudicated `RateRule` prices deterministically in candidate discovery, stacking, ranking, and served comparisons, even while its structured provenance citation trail remains partial.
   - Provenance incompleteness is a gate on production sign-off, never a silent economic block.

2. **Persistence Cardinality Invariant (`PROJECT_RULES.md` § Persistence Cardinality Rule):**
   - `candidates generated == detailed rows persisted + sum(candidate aggregate counts)`
   - Every candidate is accounted for: detailed rows for baseline, global top-100, per-family top-100, best single per jurisdiction, dominated proof rows, and referenced structures; all others aggregated by exact equivalence classes.

3. **Scenario-Universe Accounting & Residual Closure (Ledger Items 5 & 6, `ENGINE_VERSION = canonical-1.105.0`):**
   - Repaired D1 (relocated principal anchor routing), D2 (non-route accounting), D3 (home component destination routes).
   - Bundled Post/VFX + Music package policy (`post_vfx_music_package` as a real routable single leg).
   - Separate music leg surfaced only when yielding $\ge \$25,000$ incremental NPC benefit over the bundled counterpart; otherwise preserved in `optimizer_scenarios_music_suppressed`.

4. **Single-Jurisdiction Contract (Ledger Items 1, 9, 10):**
   - The contract serves exactly 217 accounted jurisdictions per production (91–92 executable, 20 conditional, 1–2 unavailable, 104 data-incomplete).
   - Mismatches on hard requirements (e.g. marine filming vs. landlocked) produce `NOT_SUITABLE_FOR_THIS_PRODUCTION`.
   - Missing soft requirement data produces neutral disclosure, never a hard exclusion.

5. **Overview Four & Workspace Six Selection Contracts (Ledger Items 10 & 11):**
   - **Overview Four:**
     1. Current Location (home country baseline).
     2. Leading Jurisdiction (cheapest fit-confirmed single jurisdiction winner; a confirmed mismatch cannot lead).
     3. Optimized Structure (top actionable hybrid saving cost).
     4. Conditional Upside (deepest potential ceiling cost reduction with attainable upside and no physical mismatch).
   - **Workspace Six:**
     - Slot 1: Current Location Baseline.
     - Slots 2–3: Best two distinct Practical Hybrids.
     - Slots 4–5: Best two distinct Advanced Multi-Jurisdiction Hybrids (backfilled from Practical if fewer than two).
     - Slot 6: Highest-ranked remaining distinct executable structure.
     - Strict unique economic identities ($\text{EID}_i \neq \text{EID}_j$).

---

## 2. SUPERSEDED CLAIMS & EARLIER ASSUMPTIONS RETRACTED

| Earlier Assertion | Controlling Ledger / Rule Status | Disposition |
| :--- | :--- | :---: |
| "Workspace default to Normal Mode is an optimizer bug" | No written product requirement mandates Optimizer mode as cold URL entry default. This is a frontend view mode default, not an optimizer bug. | **RETRACTED** |
| "Little Utopia has a static cache defect preventing location updates" | Trace confirms optimizer engine re-evaluates or re-uses correctly. The form submission wiring belongs to Claude's frontend remediation worktree (Ledger Item 10). | **RETRACTED** |
| "220 extra SQL seed rows are active optimizer defects" | Postgres contains legacy migration seed rows. The Doctrine Engine correctly resolves canonical programs from Python registries (`ExecutableJurisdictionRegistry`) and explicitly ignores unreferenced database rows. | **RECLASSIFIED** |
| "Missing display names on pilot programs are calculation failures" | Display name text is a presentation fallback, not an economic, pricing, or candidate generation failure. | **RECLASSIFIED** |
| "Self-certified audit `ce478d32` is accepted" | The previous audit reused persisted outputs as calculation inputs. This audit replaces it with independent first-principles derivations. | **SUPERSEDED** |

---

## 3. EXACT AUDIT DENOMINATORS

All metrics in this audit are evaluated against frozen, immutable denominators:

1. **Executable Program Universe Denominator:**
   - **230 Canonical Programs**: Exactly 230 unique statutory/administrative program slugs defined in authoritative runtime owners (`ExecutableJurisdictionRegistry`, `RateRule` worldwide catalog, `DoctrineRegistry`).
   - **67 Alias/Legacy Keys**: Reconciled through runtime equivalence mapping; segregated from the canonical denominator so aliases do not inflate the program count.
   - **Total Evaluated Keys:** 297.

2. **Stacking & Structural Framework Denominator:**
   - **263 Total Stacking Frameworks**:
     - 41 Bilateral Co-Production Treaties (`_BILATERAL` in `app/calculators/treaty_engine.py`).
     - 3 Multilateral Co-Production Conventions (Eurimages, European Convention, Ibermedia).
     - 17 Local Multi-Program Stacks (e.g. Ontario OFTTC + OCASE + Federal CPTC).
     - 87 Regional Uplifts & Diversity/Local-Hire Add-ons.
     - 115 Component Relocation & Anchor-Component Hybrid permutations (Post/VFX, Music, Scoring, Studio split).

3. **Real Production Denominator ($N = 4$):**
   - *The Little Utopia* (`LU`): Budget $33,500,000, Home Jurisdiction `MU`
   - *F#K Valentine's Day* (`FVD`): Budget $4,500,000, Home Jurisdiction `GR`
   - *Bad Hombres* (`BH`): Budget $20,000,000, Home Jurisdiction `US-NM`
   - *Lips Like Sugar* (`LLS`): Budget $42,700,000, Home Jurisdiction `US-CA`

4. **Single-Jurisdiction Accounting Denominator:**
   - Exactly **217 Accounted Jurisdictions** per production.

5. **Workspace Six Denominator:**
   - Exactly **6 Slots $\times$ 4 Productions = 24 Slots Total**.

6. **Overview Four Denominator:**
   - Exactly **4 Cards $\times$ 4 Productions = 16 Cards Total**.

---

## 4. REQUIRED TERMINAL DISPOSITIONS

### Program Terminal Dispositions:
- `PROVEN_REACHABLE_AND_PRICED`: Deterministically qualified and priced across evaluated structures.
- `PROVEN_REACHABLE_NEEDS_FACTS`: Reaches candidate generation but requires unsupplied facts (cultural test, minority spend, local entity).
- `PROVEN_RULE_REJECTED`: Reachable by generator, explicitly disqualified by statutory rule (spend floor, genre, foreign producer block).
- `PROVEN_AUTHORITY_BLOCKED_VISIBLE`: Disclosed as visible for exploration but blocked from confirmed recommendation due to legal/regulatory uncertainty.
- `PROVEN_NOT_APPLICABLE`: Statutory scope excludes narrative feature films (e.g. documentary-only or animation-only formats).
- `PROVEN_SUPERSEDED`: Replaced by a successor statutory program (e.g. UK legacy film credit $\rightarrow$ AVEC).
- `DEFECT_DISCONNECTED`: Present in registry but absent from candidate generation without canonical cause.
- `UNPROVEN`: Lacks definitive evidence.

### Stacking Terminal Dispositions:
- `PROVEN_ALLOWED_PRICED`: Permitted by stacking rules and dynamically priced in generated structures.
- `PROVEN_ALLOWED_NEEDS_FACTS`: Permitted framework requiring bilateral certification, treaty points, or co-producer approval.
- `PROVEN_EXCLUDED_NAMED_RULE`: Formally prohibited by statutory anti-double-dipping rules.
- `DEFECT_MISSING_STACK`: Permitted by law but missing from optimizer candidate generation.
- `UNPROVEN`: Lacks definitive evidence.

---

## 5. WHAT THIS AUDIT DOES NOT PROVE

1. **Does NOT Prove External Geospatial / Environmental Truth:**
   - The 1,140 location-capability census cells (Ledger Item 7) are frozen repository inputs; this audit verifies their programmatic consumption by the fit engine, not the underlying satellite/GIS datasets.
2. **Does NOT Implement MFNI Below-The-Line Normalization:**
   - MFNI remains explicitly a placeholder (`MFNI ADJUSTMENT NOT YET MODELED`) per `PROJECT_RULES.md`. This audit verifies that placeholder integrity is preserved and no unvetted MFNI rates are silently applied.
3. **Does NOT Self-Certify Frontend Browser Rendering:**
   - Governed strictly by the Independent UI Completion Gate (`PROJECT_RULES.md` § Independent UI Completion Gate). UI claims are cross-referenced, not certified as acceptance.
4. **Does NOT Mutate Database Records or Evaluate Stale Projects:**
   - Strictly read-only audit utilizing persisted acceptance generations and canonical source code.
