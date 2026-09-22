# Canonical Stacking and Optimizer Projection Audit

**Audit type:** Read-only. No code, tests, database rows, or evaluation generations were changed to produce this report.
**Repository:** `surajgohill-oss/Frametax`, branch `claude/global-optimizer-remediation`
**SHA audited:** `88a0b965ea5444de04e3221ea9ac52f0b4dcef63` (confirmed: local HEAD == remote HEAD == upstream at audit start)
**Database audited:** `frametax2_claude_optimizer_acceptance_20260919` (confirmed live — see §0)
**Generation basis:** each production's most recent `evaluation_generation_summaries` row, `engine_version = canonical-1.93.0`, read via the running backend's own `GET /api/v1/cineglobe/projects/{id}/state` endpoint and direct read-only SQL against `structure_calculation_results` / `evaluation_candidate_aggregates` / `evaluation_generation_summaries`.
**Productions:** The Little Utopia (LU), Bad Hombres (BH), F#K Valentine's Day (FVD), Lips Like Sugar (LLS).

---

## 0. Starting-gate confirmation

| Check | Result |
|---|---|
| Branch | `claude/global-optimizer-remediation` |
| Local HEAD | `88a0b965ea5444de04e3221ea9ac52f0b4dcef63` |
| Remote HEAD (`origin/claude/global-optimizer-remediation`) | `88a0b965ea5444de04e3221ea9ac52f0b4dcef63` (match) |
| Upstream | `origin/claude/global-optimizer-remediation` |
| Worktree | clean except `.backend_gd_wire.log`, `.frontend_gd_wire.log` (known runtime logs) |
| Database resolution | `frametax2_claude_optimizer_acceptance_20260919` confirmed live: this is the only local database whose schema contains `evaluation_generation_summaries`/`evaluation_candidate_aggregates` at all (the default `frametax2` database lacks these tables entirely), and its most recent generation row for every one of the four productions carries `engine_version = 'canonical-1.93.0'`, matching the `ENGINE_VERSION` constant currently defined in `app/services/canonical_evaluation.py`. The running backend (`uvicorn`, port 8010) and frontend (Vite, port 5173) were confirmed live via `GET /health` (200) and `GET /` (200) and were **not restarted**. |

---

## 1. Executive verdict

**`STACKING_AND_OPTIMIZER_PROJECTION_NOT_ACCEPTED`** (see terminal status at the end of this document).

The canonical engine's underlying stacking and discovery logic is, on the specific evidence gathered, **lawful, economically reconstructable, and free of duplicate structures** in every sample checked. The regression named in the task brief is real and confirmed, but it is **worse than described**: `producer_optimizer_options_total` is **zero for all four productions**, not merely reduced for FVD. The Optimizer surface is presently empty for every production in the acceptance database. The root cause is a hard-inclusion filter (`producer_optimizer_options`) that conflates *recommendation priority* with *visibility*, directly violating the controlling product contract's own point 3 ("Recommendation thresholds affect priority, not visibility"). Family incompleteness (only `HYBRID_ANCHOR_COMPONENT` ever prices) is **not** an engine defect — it traces to a real, verified data gap (no co-production ownership-split facts on file for any of the four productions) — but the previous frontend behavior of disclosing those real, unresolved treaty opportunities was also deleted by the same commit, with nothing replacing it.

Acceptance is withheld because: (a) the served Optimizer projection currently shows zero results in production for all four fixtures, a state the frontend regression tests do not catch because they use synthetic fixtures instead of the live acceptance data; and (b) the complete `optimizer_scenarios` projection this audit was asked to validate as the future restoration source has not yet been re-wired to any UI surface — restoring it is the explicit next step, not yet done.

---

## 2. Four-project count table by family and disposition

All counts read live from each production's current generation (`canonical-1.93.0`).

| Production | Baseline (current-location) NPC | `optimizer_candidates_total` = `optimizer_scenarios_total` | by family (all 4 productions: 100% `HYBRID_ANCHOR_COMPONENT`) | by tier: Practical / Formal / Advanced | `producer_optimizer_options_total` | excluded: `SAVINGS_NOT_ABOVE_100K` | excluded: `NOT_BILATERAL` | disclosed `CO_PRO_OPPORTUNITY` (unpriced) |
|---|---:|---:|---|---|---:|---:|---:|---:|
| Little Utopia | $3,791,333.30 | 171 | HYBRID_ANCHOR_COMPONENT: 171; others: 0 | 93 / 0 / 78 | **0** | 93 | 78 | 25 |
| Bad Hombres | $1,885,112.75 | 267 | HYBRID_ANCHOR_COMPONENT: 267; others: 0 | 94 / 0 / 173 | **0** | 94 | 173 | 25 |
| F#K Valentine's Day | $3,072,027.16 | 411 | HYBRID_ANCHOR_COMPONENT: 411; others: 0 | 107 / 0 / 304 | **0** | 107 | 304 | 27 |
| Lips Like Sugar | $8,524,375.10 | 541 | HYBRID_ANCHOR_COMPONENT: 541; others: 0 | 133 / 0 / 408 | **0** | 133 | 408 | 25 |

`optimizer_candidates_by_family` is `{HYBRID_ANCHOR_COMPONENT: N, OFFICIAL_COPRODUCTION: 0, COMBINED_COPRO_HYBRID_STACK: 0, MULTI_PRINCIPAL_MULTILATERAL: 0}` for all four — identically, not approximately.

**Materiality of what is hidden by `NOT_BILATERAL` alone** (3+‑jurisdiction candidates with real savings, computed directly from each production's own `optimizer_scenarios` and its own baseline NPC):

| Production | Advanced-tier candidates | max single-candidate savings | count saving > $100K | count saving > $200K |
|---|---:|---:|---:|---:|
| Little Utopia | 78 | $1,252,330.70 | 67 | 66 |
| Bad Hombres | 173 | $471,880.30 | 125 | 107 |
| F#K Valentine's Day | 304 | $218,887.26 | 4 | 4 |
| Lips Like Sugar | 408 | $976,026.70 | 112 | 112 |

Little Utopia alone has **66 real, priced, executable structures saving more than $200,000** that are currently invisible to producers.

FVD's own 2-jurisdiction (Practical Hybrid) tier is genuinely close to optimal already: the best of its 107 practical candidates saves only $9,500.76 vs. the Greece baseline, and only 4 of 107 save anything at all (max recorded above $100K: none). This is a real economic fact about FVD's data, not a defect — but it is exactly why an inclusion gate at $100K, rather than a priority signal, zeroes out FVD's Optimizer surface entirely even though FVD's own Advanced tier has 4 real candidates saving up to $218,887.

---

## 3. Same-jurisdiction stacking findings (Question A)

**Verified correct.** `best_per_jurisdiction` is built by `_single_jurisdiction_winners()` (`canonical_production_view.py`), which:
- Filters to `candidate_status == "PRICED"`, `is_fully_priced`, `structure_type` in `LOCAL_STACK_TYPES` (`single_country`, `full_relocation`, `multi_program`, `same_jurisdiction_group_stack`, `same_jurisdiction_distinct_cost_pool_stack`), and requires the candidate's full set of economically-participating jurisdictions to equal exactly `{primary_jurisdiction}` (no accidental multi-jurisdiction leakage into the Jurisdictions layer).
- Sorts by verified NPC ascending, tie-broken by canonical `economic_identity` (not database row order or random UUID).
- Is a Python `dict` keyed by jurisdiction code — structurally guaranteed to produce **at most one card per jurisdiction**, no duplicate-jurisdiction cards possible by construction.

**Independent reconciliation performed** (direct SQL against `structure_calculation_results`, joined to `production_structures.jurisdiction_allocations` → `jurisdictions`):

- **FVD / Manitoba (`CA-MB`):** exactly one persisted local-stack candidate (`full_relocation`, `true_net_cost_usd = $2,852,129.90`, `economic_identity = 78fadae5…`). `best_per_jurisdiction["CA-MB"]` reports the same `economic_identity` (verbatim) with `npc_with_adjustments_usd = $3,183,389.90` — the difference is the later stacking/risk-adjustment pass applied on top of the raw verified NPC, not a discrepancy.
- **FVD / Ontario (`CA-ON`):** six distinct, genuinely different persisted local-stack candidates (`multi_program` ×3, `full_relocation` ×3), each with a **different** `economic_identity` and NPC ranging $2,556,030.86–$3,851,464.16. `best_per_jurisdiction["CA-ON"]` selects `economic_identity = ef6ace7f…`, `npc_with_adjustments_usd = $2,556,030.86` — the exact lowest of the six. **Winner selection is economically correct.**
- **LLS / Ontario (`CA-ON`):** same `economic_identity` (`ef6ace7f…`) wins as the lowest of six candidates ($6,745,317.38 of $6,745,317.38–$10,204,596.28) — matches the live UI figure captured in a prior session verbatim, cross-validating both the database and the served projection.

**Legal stackability verified against source.** The Ontario winner (`ef6ace7f…`) is `on_ofttc` (Ontario Film and Television Tax Credit) + `ontario_computer_animation_and_special_effects_tax_credit_ocase` (OCASE) claimed together. This exact pair is a **documented, sourced** entry in `app/optimization/stacking_rules.py` (`frozenset({"on_ofttc", "ontario_computer_animation_and_special_effects_tax_credit_ocase"})`, `rule_type: "spend_reduction"`), citing Ontario Creates' own official page: *"The OCASE Tax Credit may be claimed on eligible expenditures in addition to the Ontario Film and Television Tax Credit (OFTTC) or the Ontario Production Services Tax Credit (OPSTC)."* The persisted candidate's own `calculation_trace_json.stacking_violations` is `[]` (empty — no violation recorded) and `blocking_pairs` is `[]`.

**QPE/incentive reconciliation (independent arithmetic check).** For `ef6ace7f…`: both segments report `qpe_usd = $3,701,238.00`; `on_ofttc` incentive floor/ceiling = `$1,295,433.30`; OCASE floor/ceiling = `$666,222.84`. **`1,295,433.30 + 666,222.84 = 1,961,656.14`**, which equals the persisted `total_incentive_value_usd` exactly. Both programs computing against the same full QPE base is consistent with the sourced rule text (OCASE stacks "in addition to" OFTTC on the *same* eligible computer-animation/VFX labour, not a reduced remainder) — this is the documented behavior, not an unverified assumption; no double-counting detected in this sample.

**No source-line or cost-pool double-counting was found in the sampled rows.** (Scope note: this is a targeted, representative-row check per the audit's own efficiency rules, not an exhaustive scan of every jurisdiction × program combination across all four productions.)

---

## 4. Multi-jurisdiction stacking findings (Question B)

**FVD's 411 `optimizer_scenarios`:** exactly **411 unique `economic_identity` values** — zero duplicates. `raw_variant_count` is `1` for every one of the 411 entries; `sum(raw_variant_count) == optimizer_candidates_total == 411`. At the current generation, there is **nothing left to collapse** — the earlier session's raw-search-iteration dedup work has no remaining work to do for FVD's hybrid family, at least in this generation.

**Why this is not merely "the dedup hides duplicates" undercounting risk:** the underlying `canonical_economic_identity()` (`app/services/economic_identity.py`) is a SHA-256 over routing/program/treaty fields only — explicitly **excludes** structure UUIDs, timestamps, dollar amounts, and display-name ordering, and is **order-invariant** (every list input is sorted before hashing). It is confirmed sensitive to every real routing dimension (component, jurisdiction, program, treaty) by `tests/test_economic_identity.py` (not re-run in this audit per the read-only mandate; read directly). The one input field that could theoretically introduce spurious splits, `structural_generator_structure_id`, is itself `_structure_id()` from `structural_archetype_generator.py` — **also** a deterministic, order-independent SHA-256 over `(jurisdiction_code, program_slug, sorted(line_ids))` — so identical routings collapse to the same generator ID before ever reaching the outer hash. This is a well-designed, two-layer canonicalization; no evidence of it hiding real duplicates or splitting identical decisions was found.

**Component-routing distinctness verified.** Prior-session live UI testing (cross-checked against this audit's own data) confirmed structures differing only in routed component (`Music → Manitoba` vs. `Post → Manitoba` vs. `Vfx → Manitoba`, same anchor and destination) produce genuinely distinct `economic_identity` values and distinct NPCs — correctly treated as different producer decisions, never collapsed.

**Participant/anchor reconstruction spot-checked.** FVD's advanced-tier sample structures reconstruct cleanly to real (anchor, routed-component, destination-jurisdiction, program, NPC) tuples matching their labels (e.g. `Manitoba, CA: Music → Newfoundland & Labrador, CA · Vfx → Italy`, NPC $2,853,140 — verified against Inspector detail in a prior live session and reproduced here from the same persisted generation).

**Duplicate/redundancy findings:** none found in the sampled rows. Representative IDs for the reconciled examples above: `economic_identity=ef6ace7fb4d5a224850e4c8a232a352f02041c1ace6d34c332aee30f64d5973a` (Ontario OFTTC+OCASE winner, both FVD and LLS), `economic_identity=78fadae54bc99234ae75127a4c33957e9138a3974ac18c9ff0b2da01f98e4f73` (FVD Manitoba full_relocation winner).

---

## 5. QPE/double-counting reconciliation

See §3 for the full worked example (Ontario OFTTC + OCASE, FVD): persisted `incentive_floor_usd` values for both stacked segments sum exactly to `total_incentive_value_usd` ($1,961,656.14), against a shared, sourced-and-documented QPE base ($3,701,238.00 for both programs, per the same eligible labour category). `stacking_violations: []` and `blocking_pairs: []` on the persisted trace. No discrepancy found. This audit did not attempt to independently re-derive QPE from raw budget line items (out of scope for the bounded-query efficiency rules); it reconciled the persisted trace's own internal arithmetic, which is self-consistent.

---

## 6. Family-completeness findings (Question C)

**`OFFICIAL_COPRODUCTION` (0 priced candidates, all four productions): genuinely unavailable from the project's facts — verified, not assumed.**

Direct, read-only inspection of the pure functions that gate this family (no evaluation triggered):

```
find_bilateral_treaty_pairs_among_candidates(FVD's own 76 discovered jurisdiction codes)
  → 15 real, registered bilateral treaty pairs found among FVD's own candidates,
    including CA–IT, GB–CA, GB–AU, GB–IE, CA–AU, CA–FR, CA–MX, AU–IE, AU–IT, …

evaluate_bilateral_coproduction_opportunity('CA', 'IT', majority_pct=None, minority_pct=None, ...)
  → CoproOpportunity(resolution_state='UNRESOLVED_FACTS', treaty_slug='ca-it-bilateral', …)
    (NOT None — the treaty-matching and opportunity-construction logic works correctly)
```

The engine **does** discover real treaty partners and **does** construct a real `CoproOpportunity` for each — it is not a discovery gap. Direct SQL against `structure_calculation_results` confirms this is exactly what happens at generation time: FVD has **27** persisted `candidate_status = 'CO_PRO_OPPORTUNITY'` rows (LU/BH/LLS: 25 each), each a real, named `treaty_coproduction` structure (e.g. `"CA + IT — official co-production opportunity (ca-it-bilateral)"`), each disclosed with the note *"eligibility cannot be resolved from registry presence alone… Disclosed as an opportunity, not a qualified structure."* Every one carries `resolution_state = UNRESOLVED_FACTS` because **no project has an ownership/spend-share fact on file for any treaty pair** — `majority_pct`/`minority_pct` are `None` for all 100+ treaty pairs checked across all four productions. `evaluate_bilateral_coproduction_opportunity()` is deliberately fail-closed: it never invents a percentage split, so these opportunities can never graduate to `PRICED`/`OFFICIAL_COPRODUCTION` classification without a real fact being entered. **This is correct, intended, sourced behavior — a data gap, not an engine defect.**

**`COMBINED_COPRO_HYBRID_STACK` (0, all four): downstream consequence of the same data gap, verified consistent.** This family's construction is explicitly gated on a treaty reaching `RESOLUTION_ELIGIBLE` before a movable component is layered on top (per `canonical_evaluation.py`'s own "gated only on RESOLUTION_ELIGIBLE" comment on the pair-candidate function). Since zero treaties reach `ELIGIBLE` for any of the four productions, zero combined structures is the correct, expected outcome — confirmed by the complete absence of any `combined_*` `structure_type` row, priced or rejected, anywhere in `structure_calculation_results` or `evaluation_candidate_aggregates` for all four productions.

**`MULTI_PRINCIPAL_MULTILATERAL` (0, all four): same root cause inferred, not independently re-verified to the same depth.** Multilateral frameworks (Eurimages, European Convention) require membership + per-participant contribution facts by the same `_multilateral_coproduction_facts()` pattern as the bilateral case; given zero bilateral facts exist, it is very likely the same "genuinely unavailable from the project's facts" disposition applies, but this audit did not independently execute the Eurimages/European-Convention membership check the way it did for the bilateral case, and that omission should be closed before final acceptance of family completeness.

**The regression's interaction with disclosed opportunities.** Before `88a0b96`, `admissibleForMode()` appended every `CONDITIONAL_USER_FACT_REQUIRED`-classified structure to the Optimizer pool, strictly after priced scenarios — i.e. these 25–27 real, disclosed treaty opportunities per production were visible to a producer even though not executable. `88a0b96` deleted that append entirely (`workspaceScenarioMode.js` diff, confirmed above) with nothing replacing it. **Caveat:** this audit confirmed the *existence and count* of the 27 FVD `CO_PRO_OPPORTUNITY` rows and confirmed the pre-regression code's *intent* to surface `CONDITIONAL_USER_FACT_REQUIRED`-classified rows, but did not independently confirm the two labels (`candidate_status=CO_PRO_OPPORTUNITY` vs. `classification=CONDITIONAL_USER_FACT_REQUIRED`) refer to the exact same underlying rows byte-for-byte before drawing a hard conclusion — treat this specific linkage as **plausible, not certain**, pending a direct check of the `classification` field on those 27 rows (they were retrieved via `calculation_trace_json.candidate_status`, not `classification`, in this audit's queries).

---

## 7. Current-tip regression analysis (Question E)

**What the parent commit (`988f6a4`) served:** `admissibleForMode(allocated, MODE_OPTIMIZER)` returned `[...optimizer_scenarios, ...dedupedConditionalOpportunities]` — the complete, canonical 171/267/411/541-entry `optimizer_scenarios` projection (all three tiers: Practical, Formal, Advanced) plus disclosed conditional treaty opportunities appended after.

**What SHA `88a0b96` changed (`fix: wire practical producer optimizer projection`):**
1. Backend (`canonical_production_view.py`, +187 lines): added `MIN_PRODUCER_SAVINGS_USD = 100_000.0`, `_build_producer_optimizer_projection()`, and five new served fields (`producer_optimizer_options[_total/_by_type/_excluded_counts]`, `producer_optimizer_baseline_npc_usd`). The filter requires, simultaneously: `candidate_status == PRICED` and `is_fully_priced`; `len(economic_jurisdictions) == 2` exactly (hard-excludes every 3+‑jurisdiction structure, i.e. the entire Advanced tier and any `COMBINED_COPRO_HYBRID_STACK`/`MULTI_PRINCIPAL_MULTILATERAL` candidate categorically); `classification in {HYBRID_ANCHOR_COMPONENT, OFFICIAL_COPRODUCTION}` only; and `savings_vs_current_usd > 100_000` strictly.
2. Frontend (`workspaceScenarioMode.js`): `_optimizerScenarios()` now returns `allocated?.producer_optimizer_options || []` instead of `allocated?.optimizer_scenarios || []`; `admissibleForMode()` for Optimizer mode now returns *only* that, with the previous `CONDITIONAL_USER_FACT_REQUIRED` opportunity append removed entirely.
3. `productionOptions.js`: `selectMaxPotentialCard()` rewritten to pick from `producer_optimizer_options` instead of the previous fund-cap/treaty-opportunity/upside-gap cascade; the entire cascade (`_hasUpsideGap`, `_dedupedOptimizerPool`, the fund-cap ranking, the treaty-opportunity fallback) was deleted.
4. Tests: `producer-optimizer-projection-ui.test.mjs` (new, 68 lines) and rewrites to `overview-anchor-scenarios.test.mjs` and `workspace-scenario-mode.test.mjs` all construct **synthetic** `allocated` fixtures with a hand-built, always-non-empty `producer_optimizer_options` array (e.g. `candidate("producer")`) — none of the rewritten or new tests exercise a real production's actual generation data, so none of them could have caught that all four real productions currently yield `producer_optimizer_options_total = 0`.

**Which valid structures became unreachable:** every one of the 78/173/304/408 Advanced-tier structures per production (categorically, via the bilateral-only gate); every one of the 93/94/107/133 Practical-tier structures that save ≤ $100K vs. current location (which, per §2, is **all of them**, for every production); and the 25–27 disclosed `CO_PRO_OPPORTUNITY` treaty rows per production (via the deleted append, not the new filter directly).

**What should be preserved vs. reverted.** The backend addition is architecturally sound and should largely be **kept, not reverted**: `MIN_PRODUCER_SAVINGS_USD`, `_producer_decision_key()` (a real, well-designed canonicalization key distinguishing component/category and treaty identity), the exhaustive-fields-untouched discipline (`optimizer_candidates`/`optimizer_scenarios` and their counts are confirmed byte-identical before and after this commit — this audit's own live counts match the pre-regression figures reported in the prior session's closeout exactly: LU 171/93/0/78, BH 267/94/0/173, FVD 411/107/0/304, LLS 541/133/0/408), and the `producer_optimizer_baseline_npc_usd` fail-closed-on-missing-baseline behavior are all consistent with the controlling product contract's future ordering-policy section (§4 of the task brief). What must change is **only** the *consumption* of this projection: it must stop being the *sole* admissible Optimizer pool and instead become a **priority signal layered on top of** the complete `optimizer_scenarios` universe, per §9 below. The `has_master_artwork`/`artwork_url` addition in the same commit is unrelated and orthogonal — no findings against it.

---

## 8. Exact canonical contract for restoring the complete `optimizer_scenarios` projection (Question D)

This section specifies the contract; **no implementation was done** (per the audit's explicit scope).

1. **Inclusion status.** Every entry already in `optimizer_scenarios` (i.e., every `PRICED`, `is_fully_priced` candidate whose `classification` is in the four canonical Optimizer families) remains included, uncapped, regardless of tier, savings, or jurisdiction count. This collection is already correct today and requires no engine change — only re-wiring the frontend back to it.
2. **Executable/qualification requirement.** Unchanged from today's `optimizer_scenarios`: `candidate_status == PRICED`, `is_fully_priced == True`. Disclosed-but-unresolved opportunities (`CO_PRO_OPPORTUNITY`, `CONDITIONAL_USER_FACT_REQUIRED`) are a **separate, clearly labeled** class, never merged into the executable count, but not hidden either — surfaced as "evaluated alternatives requiring more facts," consistent with the controlling contract.
3. **Uniqueness key.** `economic_identity` (`canonical_economic_identity()`), already verified order-invariant and duplicate-free at §4. No change needed.
4. **Topology key** (for the future "genuinely different structures" test, distinct from search-path identity). The existing key already **is** a topology key — it hashes routing/program/treaty/participant fields, not any run-specific identifier except the also-deterministic `structural_generator_structure_id`. No change needed; recommend adding a regression test that asserts two candidates built via different search orders but identical routing collapse to the same `economic_identity` (extending the existing `test_economic_identity.py` coverage to a live-data integration test, not just unit fixtures).
5. **Family coverage.** All four canonical families (`HYBRID_ANCHOR_COMPONENT`, `OFFICIAL_COPRODUCTION`, `COMBINED_COPRO_HYBRID_STACK`, `MULTI_PRINCIPAL_MULTILATERAL`) remain in scope; none should be structurally excluded by any served-contract filter. (The current absence of the latter three in these four productions' *data* is a fact-completeness issue, addressed separately — see §10.)
6. **Stable ordering inputs.** Practical → Formal → Advanced tier (unchanged), then — per the controlling contract's future ordering policy (not yet implemented, correctly deferred) — savings descending within a recommended/evaluated split, NPC ascending, then `economic_identity` as the final deterministic tie-break. This exact ordering is already what `optimizer_scenarios` and `_producer_decision_key`'s sort in `88a0b96` both independently converged on — a good sign the two projections are compatible, not competing.
7. **Fields required by each surface.** All current `optimizer_scenarios` entry fields (component_allocations, participants, primary_jurisdiction, practicality_tier, npc_with_adjustments_usd, economic_identity, treaty_slug, treaty_resolution_state, …) are already sufficient for Workspace (cards, slot-6 dropdown), Overview (optimized card), Full Globe (sectioned list), Map, Split, Lanes, and Inspector — all of these surfaces consumed exactly this shape successfully in the pre-`88a0b96` state (verified live in the prior session's closeout). The `88a0b96` `producer_optimizer_*` fields (`savings_vs_current_usd`, `producer_optimizer_option_type`, `producer_optimizer_baseline_npc_usd`) are a valid **additive annotation** that should be attached to the *same* `optimizer_scenarios` entries (or computed client-side from `npc_with_adjustments_usd` and a served baseline) rather than defining a second, competing, narrower collection.
8. **Recommended vs. evaluated-alternative derivation, without deleting either class.** Do not filter. Instead: (a) compute `savings_vs_current_usd` and `producer_optimizer_option_type`-equivalent tier-aware threshold (`>$100K` for 2-jurisdiction, `>$200K` for 3+) as a boolean `is_recommended` flag on every `optimizer_scenarios` entry; (b) sort the full collection with recommended entries first (Practical → Formal → Advanced within recommended, then the same tier order within not-recommended); (c) let the UI render a visual/section distinction ("Recommended" vs. "Evaluated Alternatives") without ever shrinking the served collection or the six-card/dropdown reachable set. This satisfies "Recommendation thresholds affect priority, not visibility" exactly.

---

## 9. Remediation list

**Canonical engine defects**

1. None found that require a code change to the pricing/discovery/stacking kernel itself. Same-jurisdiction and multi-jurisdiction stacking, QPE reconciliation, and duplicate-detection all checked out correct in every sample audited (§3, §4, §5).
2. (Open item, not confirmed a defect) Verify `MULTI_PRINCIPAL_MULTILATERAL`'s zero-count reason with the same rigor as the bilateral case (§6) — run the equivalent read-only check against `find_eurimages_partners`/`find_european_convention_partners` and the multilateral fact-scoping functions before treating "data gap" as confirmed for this family.

**Retention/served-contract defects**

3. `_build_producer_optimizer_projection()`'s `NOT_BILATERAL` and `SAVINGS_NOT_ABOVE_100K` rejections must stop being **exclusions from the served collection** and become an **annotation** (`is_recommended` / `producer_optimizer_option_type`) on the full `optimizer_scenarios` collection, per §8.
4. `producer_optimizer_options` should either be deprecated in favor of the annotated `optimizer_scenarios`, or redefined as *only* the "Recommended" subset while `optimizer_scenarios` (annotated) becomes the surface every UI actually renders from — either is acceptable, but a collection that goes to zero for every real production in the acceptance database must never be the *sole* thing any UI surface reads.
5. Restore a first-class, clearly-labeled "Evaluated / needs more facts" bucket for `CO_PRO_OPPORTUNITY` (and equivalent) disclosures, since the pre-regression `CONDITIONAL_USER_FACT_REQUIRED` append was deleted with nothing replacing it (§6, §7) — confirm the exact classification/candidate_status linkage first (open item from §6).

**Frontend wiring defects**

6. `workspaceScenarioMode.js::admissibleForMode()` (Optimizer branch), `productionOptions.js::selectMaxPotentialCard()`/`selectAnchorLeadingOptimized()`, `Workspace.jsx`, `Overview.jsx`, `ProjectGlobe.jsx` all need to be re-pointed at the restored, annotated `optimizer_scenarios` projection per §8 — this is a revert-and-reapply of the `88a0b96` frontend diff's *consumption* logic, not a revert of the backend annotation fields, which should be kept and layered on top.
7. `ProjectGlobe.jsx`'s Advanced-tier section (removed by `88a0b96`; the prior session's own sectioned-rack closeout `988f6a4` built the `TIER_SECTIONS`/`Advanced Multi-Jurisdiction` UI this commit then bypassed by emptying its data source) needs re-verification once the data source is restored — the rendering code itself may still be intact and only need its input un-narrowed.

---

## 10. Smallest focused tests required for remediation

1. **Live-data regression guard** (the single most important gap): a test that loads a **real** persisted generation's `allocated_structures` shape (fixture captured from the acceptance database, not hand-built) for at least one production with a small Practical tier and large Advanced tier (e.g., FVD: 107/0/304), and asserts `admissibleForMode(allocated, MODE_OPTIMIZER).length > 0` and specifically `>= optimizer_scenarios_total` bound — this single test would have caught the current regression immediately, since every existing test uses a synthetic, always-populated fixture.
2. A test asserting the four accepted `optimizer_scenarios_total`/`by_tier` counts (LU 171/93/0/78, BH 267/94/0/173, FVD 411/107/0/304, LLS 541/133/0/408) are unchanged by any future annotation-based remediation (mirrors the existing pattern from `workspace-layout-contract.test.mjs`'s scenario-count fixture test).
3. A test that a 3+‑jurisdiction structure with real savings above the $200K three-jurisdiction threshold is present and marked `is_recommended: true` (or equivalent) in the restored projection, not excluded.
4. A test that a 2-jurisdiction structure with savings exactly at or below $100K is present and marked `is_recommended: false`, not excluded (this is the direct "visibility vs. priority" contract test).
5. A test pinning `canonical_economic_identity()`'s invariants already exist (`test_economic_identity.py`) — extend with one integration-level assertion that FVD's real 411-entry `optimizer_scenarios` collection has zero duplicate `economic_identity` values, run against the acceptance database as a periodic data-integrity check (not a unit test), so a future generation with real duplicate search-path artifacts is caught.

---

## 11. Explicit statement

No code, tests, database rows, evaluation generations, or engine version were changed to perform this audit. All findings above are drawn from: (a) direct read-only SQL against `structure_calculation_results`, `evaluation_candidate_aggregates`, `evaluation_generation_summaries`, and `jurisdictions`, using each production's existing, already-persisted current-generation rows; (b) the running backend's own `GET /api/v1/cineglobe/projects/{id}/state` read endpoint (no `evaluate_project()` call, no `POST /evaluation/begin`); (c) direct, read-only invocation of pure, side-effect-free functions (`find_bilateral_treaty_pairs_among_candidates`, `evaluate_bilateral_coproduction_opportunity`, `te.get_bilateral_treaty`, `te.all_bilateral_treaties`) that perform no database access and mutate no state; and (d) static reading of the current source tree and its `git log`/`git show` history. No `evaluate_project()` call, cold generation, fingerprint change, or database write occurred at any point in this audit.

---

## Terminal status

**`STACKING_AND_OPTIMIZER_PROJECTION_NOT_ACCEPTED`**

Stacking itself (same-jurisdiction and multi-jurisdiction) is independently supported as lawful, nonduplicative, and numerically reconstructable in every sample audited. Family completeness for `OFFICIAL_COPRODUCTION`/`COMBINED_COPRO_HYBRID_STACK` is independently supported as a genuine data gap, not an engine defect (with `MULTI_PRINCIPAL_MULTILATERAL` still an open item, §6/§9). Acceptance is withheld because the currently-served producer-facing Optimizer projection is empty for all four productions — a regression this audit independently confirmed and root-caused (§7), not yet remediated, and not detectable from the existing (synthetic-fixture) passing test suite alone.
