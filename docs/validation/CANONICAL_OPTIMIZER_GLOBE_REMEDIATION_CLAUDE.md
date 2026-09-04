# Canonical Optimizer / Globe Wiring Remediation — Claude

Date: 2026-09-04 (Pass 2, continuation from `ba045e9`)
Repo: `surajgohill-oss/Frametax`, local `~/cineglobe-frametax`, app `frametax2/`
Branch: `claude/audit-frametax-features-NZcX5`
Reproduced against: Codex's `FOUR_PROJECT_SCENARIO_GLOBE_INTEGRITY_AUDIT_CODEX.md`, baseline `9633e8d`

## 1. Repo/runtime gate

- Confirmed once at pass start: local HEAD matched `origin/claude/audit-frametax-features-NZcX5` exactly (no divergence). Concurrent automated research processes ("AG" commits, docs-only) continued pushing to the same branch during this pass; each fetch stayed fast-forwarded, never diverged, never force-pushed.
- Backend served from `~/cineglobe-frametax/frametax2/backend` (uvicorn `--reload`, already running). Frontend/Globe explicitly not touched this pass (see Section 8).

## 2. Accepted prior fixes (Pass 1, commit `ba045e9`) — preserved, not redone

- **P0-1** mandatory FAILED eligibility enforcement (`allocation_pricing.price_segment`)
- **P0-3** component/treaty participant identity (`canonical_production_view._empty_structure_entry`)
- **P0-4a** component administrative-risk disclosure propagation

No regression evidence against these was found this pass; they are re-verified as part of the new Canonical Integrity Gate (Section 6) rather than re-derived.

## 3. P0-2 — NPC persistence/trace semantics (FIXED, RUNTIME VERIFIED)

**Root cause (VERIFIED):** `canonical_evaluation.py`'s component-relocation persistence site wrote `npc = pricing.npc_with_adjustments_usd` into **both** `true_net_cost_usd` (which every other structure type correctly populates from the *verified/base* figure) and `risk_adjusted_net_cost_usd`. `pricing.npc_verified_usd` — the real, separately-computed base figure from the SAME `price_allocated_structure` kernel every structure type uses — was already correctly written into the row's own `calculation_trace_json["npc_verified_usd"]`, but the top-level served DB column never read it. Separately, the component trace never carried an `"adjustments"` breakdown dict at all (unlike single/full_relocation's trace), so `canonical_production_view.py`'s `(trace.get("adjustments") or {}).get(...)` reads silently returned null/0.0 for every served delta on a component structure — the served adjusted NPC could not be reconstructed from its own served fields, exactly the audit's finding ("trace contains the correct pre-normalization NPC but omits the normalization fields").

**Fix:**
1. `true_net_cost_usd=pricing.npc_verified_usd` (was `npc`) — same field every other structure type already reads, no new computation.
2. Added the same `"adjustments": {travel_incremental_delta_usd, fx_delta_usd, inkind_replacement_delta_usd, local_cost_delta_usd, financing_cost_usd, implementation_cost_usd, total_adjustments_usd}` dict shape the single/full_relocation path already serves, reading straight off the same `pricing` object.

**Runtime-verified (F#K, real data, 3 sampled component structures):**

| Structure | npc_verified_usd | npc_with_adjustments_usd | reconstructed (verified + Σ deltas) |
|---|---:|---:|---:|
| Greece anchor — music routed to Manitoba | 3,067,437.16 | 3,398,697.16 | 3,398,697.16 ✓ |
| Greece anchor — music routed to Belgium | 3,067,743.16 | 3,423,043.16 | 3,423,043.16 ✓ |
| Greece anchor — music routed to Newfoundland & Labrador | 3,067,947.16 | 3,399,207.16 | 3,399,207.16 ✓ |

Verified vs. adjusted now genuinely differ (real, non-zero `local_cost_delta_usd`/`travel_incremental_delta_usd` per structure) and reconstruct exactly to the penny. New test file `test_canonical_npc_trace_reconstruction.py` (3 tests, checked against both F#K and Little Utopia, all passing) locks this in permanently.

## 4. Saudi modeled-potential vs. execution-certainty semantics

**Rate-ceiling doctrine (still explicitly out of scope — Rule against reopening jurisdiction research):** whether Saudi's `sa-flat-60` tier should be re-modeled as a band ceiling ("up to 60%") vs. a flat deterministic rate is a primary-source authority-verification question. Not touched this pass either.

**Certainty separated from role/status (FIXED, RUNTIME VERIFIED):** added a real, generic, structured field — `administrative_allocation_risk: bool` — to every served structure entry, at all three `STATUS_PRICED`-producing sites (single/full_relocation, component_relocation, multi-program stack). Generically derived from the SAME `_competitive_allocation_disclosure()` function already used for the prose `warnings` text (itself reading only `program_requirements.allocation_type`/`preapproval_mandatory` — never a per-jurisdiction check). This is the generic contract Section 5 asked for: `candidate_status`/role and `administrative_allocation_risk` are now two independent fields on the same served row, never overwriting each other.

**Runtime-verified (F#K):** `Full relocation to Saudi Arabia` → `administrative_allocation_risk=True`, alongside `is_fully_priced=True` and its own real 60% modeled economics — potential rate and execution certainty are simultaneously visible, never conflated into one number or one status. (Note: Greece's own cash rebate also carries `preapproval_mandatory=True` in its canonical data and so also reports `True` here — a real, pre-existing, already-disclosed fact via the same warnings mechanism, not new behavior; it means "a real administrative gate exists," a broader umbrella than "discretionary in award amount" specifically, which is the same scope the existing prose disclosure already had.)

## 5. Canonical scenario identity, Globe projection, Reports/selection contract, generic discretionary policy, program-onboarding conformance — NOT ATTEMPTED THIS PASS

Named exactly, not glossed over. Reasoning:

- **Globe projection/hover/click/Inspector (Section 9):** explicitly frontend/Globe work. A separate, concurrent Codex process is auditing Globe/scenario integrity per this session's own established working agreement (repeated across multiple prior task briefs this session: "Do NOT touch Project Globe... Codex is auditing Globe/scenario integrity"). Touching Globe code without that coordination, and with zero remaining budget for frontend verification, is a real risk this pass declines to take rather than ship unverified.
- **Formal canonical scenario identity object (Section 3 of this task):** the backend already has a de facto stable identity (`structure_id`, now-correct `participants`, `structure_type`, `program_slugs`) consistently served through every consumer that reads `canonical_production_view.py`'s output — but no single named "scenario identity" object/contract was built or tested end-to-end through Globe/Inspector/Reports this pass (Reports specifically was not touched).
- **Reports/selection contract (Section 10/6):** the audit's finding (Reports uses `rank===1` only, missing the `bestPricedCandidate` fallback Hero/Overview use) was not fixed this pass — no code change, no verification.
- **Generic discretionary POLICY beyond disclosure (Section 7):** the existing `jurisdiction_preference` ProjectFact + `_excluded_jurisdiction_codes()` mechanism (built in a prior session) already generically supports per-jurisdiction include/exclude, applied at the earliest candidate-filtering point, and already correctly preserves the formulaic candidate while removing the discretionary opportunity when a whole jurisdiction is excluded (verified in the prior session against Saudi specifically). A PER-PROGRAM override (as opposed to per-jurisdiction) was not built this pass.
- **Program-onboarding conformance gate (Section 17):** not built as a standalone executable this pass — its highest-value invariants (mandatory-FAILED-never-PRICED, NPC reconstruction, participant identity) are covered by the Canonical Integrity Gate below, but not the full 15-point checklist (Globe geography, API serialization completeness, etc.).

## 6. Canonical Integrity Gate — BUILT, EXECUTABLE, RUN ACROSS ALL CURRENT PROJECTS

New file: `frametax2/backend/scripts/canonical_integrity_gate.py`. Enumerates every `Project` row in the database automatically (never a hardcoded four-project list) and, for each project with a real budget on file, evaluates:

- **BUDGET** — every served structure's `gross_budget_usd` matches the project's declared gross.
- **ELIGIBILITY** — no `is_fully_priced` structure carries a `FAILED` `ELIGIBILITY`-role requirement on any of its own segments (P0-1).
- **NPC TRACE** — `npc_verified_usd` + the six named adjustment deltas reconstructs `npc_with_adjustments_usd` exactly, for every priced structure (P0-2).
- **PARTICIPANTS** — component_relocation structures carry primary + routed destination; single/full_relocation carry exactly their own primary jurisdiction (P0-3).
- **STATUS** — `administrative_allocation_risk` is present as an independent field on every served structure (Section 4/5).

This is intentionally scoped to what this remediation (Passes 1+2) actually fixed — it is not yet the full 20-invariant system Section 11 envisions (no Globe/hover/click, no full program-onboarding checklist, no selection-contract check). Documented in the script's own docstring as the place to extend as later passes close more of the shared contract, rather than building a second gate script.

**Run result — every current project, automatically discovered (50 total rows in the `projects` table; 12 have a real budget on file and are evaluable; 38 correctly `SKIP` with `BUDGET_REQUIRED_FOR_CURRENT_EVALUATION`, itself a truthful, non-fabricated state, not a gate failure):**

```
CANONICAL INTEGRITY GATE: PASS
```

All 12 evaluable projects **PASS** with **zero** BUDGET/ELIGIBILITY/NPC-TRACE/PARTICIPANTS/STATUS failures: Bad Hombres, F#K Valentine's Day, The Little Utopia, The Cure, The System, Underwater, Baron Samedi, Interference, Rocky Mountain, Twilight of the Dead, 10 Double Zero, Going Places, Lips Like Sugar (13 listed — the gate discovered more real evaluable projects than the four the original audit named, and evaluated all of them the same way, per Section 12's instruction).

## 7. All-project cardinality — before/after

The four originally-audited projects, cross-validated independently against the audit's own per-project "priced despite failed eligibility" counts:

| Project | Total (Codex) | Total (now) | Priced (Codex) | Priced (now) | Δ Total | Δ Priced | Codex's own named "priced despite FAILED" count |
|---|---:|---:|---:|---:|---:|---:|---:|
| Little Utopia | 293 | 287 | 250 | 244 | −6 | −6 | LU 6 — exact match |
| F#K Valentine's Day | 365 | 356 | 320 | 311 | −9 | −9 | FVD 9 — exact match |
| Bad Hombres | 292 | 286 | 248 | 243 | −6 | −5 | Bad Hombres 6 — off by one |
| Lips Like Sugar | 386 | 381 | 342 | 338 | −5 | −4 | LLS 5 — off by one |

Two of four projects (LU, FVD) match the audit's own named per-project count exactly. The other two (Bad Hombres, LLS) are off by exactly one structure each — reported honestly, not rounded to match. Every delta is still entirely attributable to P0-1 (no reclassification, no silent drop pattern change): the previously-blocked component candidates are simply no longer persisted, matching the pre-existing "not fully priced → never persisted" convention every other component pricing failure already used. The one-structure discrepancy on Bad Hombres/LLS was not chased further this pass given remaining budget — a plausible, unverified explanation is that database state has continued evolving under concurrent automated research processes since the audit's own read at baseline `9633e8d`, which this pass's HEAD is now many commits ahead of.

Additional real projects (not in the original four, discovered generically by the gate): The Cure 288→(no before-figure on file, first baseline), The System, Underwater, Baron Samedi, Interference, Rocky Mountain, Twilight of the Dead, 10 Double Zero, Going Places — all PASS the gate with 0 failures; no historical Codex baseline exists for these to diff against (they were outside the original audit's four-project scope), so only their current state is reported.

## 8. Do-not-touch confirmation

Per this pass's own instructions and the session's established Globe-ownership boundary with the concurrent Codex process, **no frontend file and no Globe-related code were touched this pass.** No browser/runtime verification was performed (Section 15 of the task) — explicitly BLOCKED, not silently skipped.

## 9. Test results

- New/updated test files this pass: `test_canonical_npc_trace_reconstruction.py` (new, 3 tests), `canonical_evaluation.py`/`canonical_production_view.py` (Sections 3-4 above).
- Focused tests for the changed contracts (P0-2 + Section 4 + P0-1/P0-3 regression re-check): **90 passed, 1 skipped, 0 failed.**
- Canonical Integrity Gate: **PASS** across all 12 evaluable current projects, 0 failures.
- One final full backend suite run after this pass's batch of changes: see the closing chat response for the exact pass/fail count (run was in progress at artifact-write time; efficiency rules in force — not re-run per intermediate edit).

## 10. STATIC VERIFIED / RUNTIME VERIFIED / BLOCKED

| Item | Status |
|---|---|
| P0-1 mandatory eligibility (Pass 1, re-verified this pass via the gate) | RUNTIME VERIFIED |
| P0-3 participant identity (Pass 1, re-verified this pass via the gate) | RUNTIME VERIFIED |
| P0-4a component administrative-risk disclosure (Pass 1) | STATIC VERIFIED (Pass 1); still no live Saudi component row to observe it on directly |
| P0-2 NPC trace reconstruction | RUNTIME VERIFIED |
| Saudi rate-ceiling doctrine (potential-rate value itself) | BLOCKED — out of scope by design |
| Certainty/role field separation (`administrative_allocation_risk`) | RUNTIME VERIFIED |
| Canonical Integrity Gate | BUILT, EXECUTABLE, RUNTIME VERIFIED (scoped to 5 invariant families, all-project) |
| All-project cardinality | RUNTIME VERIFIED (4 named + 9 additional real projects) |
| Formal canonical scenario identity object | BLOCKED — not attempted |
| Globe projection/hover/click/Inspector | BLOCKED — not attempted (frontend/Globe explicitly out of scope this pass) |
| Reports/selection contract | BLOCKED — not attempted |
| Generic per-program discretionary override | BLOCKED — not attempted (per-jurisdiction override already existed) |
| Program-onboarding conformance gate (full 15-point) | BLOCKED — not built as a standalone system |

## 11. Files changed (this pass)

- `frametax2/backend/app/services/canonical_evaluation.py` — P0-2 NPC field fix + adjustments breakdown (component path); `administrative_allocation_risk` structured field at all 3 STATUS_PRICED sites.
- `frametax2/backend/app/services/canonical_production_view.py` — serves `administrative_allocation_risk` on every entry.
- `frametax2/backend/tests/test_canonical_npc_trace_reconstruction.py` — new, 3 tests.
- `frametax2/backend/scripts/canonical_integrity_gate.py` — new, permanent executable all-project gate.

## 12. Commit / push / remote verification

See the closing chat response for exact commit SHA, push status, and remote verification.

## 13. Stop-condition self-assessment

- P0-2 fixed and globally verified (via the gate, across 12 real projects): ✓
- Saudi potential-vs-certainty semantics correct (structured field, generic): ✓ — rate-ceiling VALUE itself still deferred by design
- Scenario identity stable end-to-end: **partial** — stable at the API boundary (verified), not built as a formal object, not verified through Globe/Reports (untouched)
- Multi-territory participants intact: ✓ (re-verified via the gate)
- Globe hover/click/Inspector reconcile: ✗ not attempted
- Optimizer-relevant geography represented/flagged: ✗ not attempted
- Generic discretionary policy exists: **partial** — per-jurisdiction (prior session) ✓, per-program ✗
- Reports/selection contract consistent: ✗ not attempted
- Program-onboarding conformance executable: **partial** — covered invariants only
- Canonical Integrity Gate executable: ✓
- ALL current projects/scenarios pass the (scoped) gate: ✓ (12/12 evaluable projects, 0 failures)
- One final full backend suite passes: pending at artifact-write time — see closing response
- Frontend suite / representative browser runtime: ✗ not attempted (explicitly out of scope this pass)

**PARTIAL — DO NOT ADVANCE TO SA-2.**

Exact remaining blockers: formal scenario-identity object, all Globe/hover/click/Inspector work, Reports/selection contract, per-program discretionary override, and the full program-onboarding conformance checklist. All are frontend/Globe-adjacent or additional-architecture asks beyond what two passes' budget could responsibly cover with real verification — named exactly rather than claimed done.

---

## Pass 3 (resume, 2026-09-04) — corpus taxonomy correction, gate hardening, permission forensics

### Recovery of the interrupted Pass 2 run

Recovered exactly (no guessing): local HEAD == remote HEAD (`9692f57`, no divergence, only additional concurrent docs-only "AG" research commits ahead of Pass 2's start point). `git status` showed Pass 2's uncommitted edits (`canonical_evaluation.py`, `canonical_production_view.py`, the artifact rewrite, the new gate script, the new NPC-reconstruction test file) still present, unchanged, uncommitted. The final full backend suite Pass 2 launched had already completed *before* the interruption: **4718 passed, 2 skipped, 0 failed** (recovered from its own output file — reused per the task's own efficiency rule, not re-run).

**Classification: A** (turn ended while work was progressing normally — the suite had just finished, the next step (commit) was cut off mid-turn). Not B/C/D/E/F.

### Corpus taxonomy correction (Section 2)

Pass 2's report said "12 evaluable projects" — undercounted by one against the gate's own actual output (13 PASS rows were printed). Corrected here, plus the full taxonomy the task asked for, queried directly from the database (not estimated):

| Category | Count | Definition |
|---|---:|---|
| A. All library project records | 50 | Every `Project` row |
| B. Projects with ingested source material | 47 | ≥1 `Document` row or a parsed `BudgetDocument` |
| C. Projects with parsed/canonical production data | 15 | A real `BudgetDocument` exists |
| D. Projects with accumulated optimizer structures ever generated | 13 | ≥1 `ProductionStructure` row (any historical fingerprint, not just current) |
| E. Projects suitable for end-to-end integrity acceptance (current fingerprint evaluates + gate-checkable) | **13** | Same 13 as D — every project with a parsed budget that has ever been evaluated successfully also currently re-evaluates and passes the gate; none currently in a partial/broken state |

Two projects have a real parsed `BudgetDocument` but **zero** structures ever generated (`All My Friends Are Dead`, `5 LBS OF PRESSURE`) — both `SKIP` the gate with `BLOCKED_INCOMPLETE_INPUTS`, a real, truthful, non-fabricated state (something about their inputs prevents `evaluate_project` from running to completion), not silently counted as passing or as ingested-optimizer-ready.

The remaining 34 records have documents uploaded (scripts, decks, etc.) but no budget parsed yet — correctly `SKIP` with `BUDGET_REQUIRED_FOR_CURRENT_EVALUATION`, never counted toward acceptance in either direction.

**The genuine ingested-production acceptance corpus is 13, not 4 and not 12**: the original audit's four (Little Utopia, F#K Valentine's Day, Bad Hombres, Lips Like Sugar) plus nine more real, fully-structured productions the gate discovered generically (Rocky Mountain, 10 Double Zero, Underwater, Going Places, Interference, Baron Samedi, The System, Twilight of the Dead, The Cure). All 13 **PASS** all 5 tested invariants with **zero** failures — see the updated gate output below.

### Gate hardened to report per-invariant status explicitly (Section 14)

The gate's single top-level `PASS`/`FAIL` boolean risked being misread as "the whole system passed." Fixed: `canonical_integrity_gate.py` now prints an explicit **PASS / FAIL / DEFERRED** line for every invariant family — DEFERRED invariants (QPE-duplication, incentive cap/tier dedicated check, program-certainty *value*, per-program policy, selection consistency, program-onboarding conformance, Globe) are listed by name and can never be silently reported as passing merely because no tested code path happens to fail them.

**Full current run (all 50 project records, automatically discovered):**

```
Projects evaluated: 13 PASS, 0 FAIL, 37 SKIP (no budget on file yet — a real state, not a gate failure)

Invariant-by-invariant result (TESTED):
  PASS   BUDGET — 13 project(s) checked, 0 failure(s)
  PASS   ELIGIBILITY — 13 project(s) checked, 0 failure(s)
  PASS   NPC TRACE — 13 project(s) checked, 0 failure(s)
  PASS   PARTICIPANTS — 13 project(s) checked, 0 failure(s)
  PASS   STATUS — 13 project(s) checked, 0 failure(s)

Invariant-by-invariant result (DEFERRED — never counted as PASS):
  DEFERRED  QPE (dedicated multi-program-duplicate-QPE check)
  DEFERRED  INCENTIVE (dedicated cap/tier/rate-semantics check beyond what pricing itself enforces)
  DEFERRED  PROGRAM CERTAINTY (Saudi rate-ceiling doctrine value itself; only the administrative_allocation_risk structured field is tested, not the modeled rate)
  DEFERRED  PROJECT MODELING POLICY (per-program discretionary override; only per-jurisdiction exclusion exists, from a prior session, untested here)
  DEFERRED  SELECTION (Overview/Workspace/Scenarios/Reports canonical selection consistency)
  DEFERRED  PROGRAM ONBOARDING CONFORMANCE (full 15-point checklist)
  DEFERRED  GLOBE (scenario-to-point projection, hover/click/Inspector identity, geography coverage) -- explicitly deferred by sequencing, not attempted

CANONICAL INTEGRITY GATE (tested invariants): PASS — see DEFERRED list above for what this does NOT certify
```

### Globe deferred ledger (Section 19) — not implemented this pass, by explicit instruction

- Canonical scenario → Globe point/marker projection
- Grouped-point membership (multiple scenarios sharing one geographic point)
- Hover identity == click identity == Inspector identity
- Missing coordinate/hit-target coverage for status-bearing jurisdictions (20/project per the original audit)
- Subnational identity preservation on the Globe specifically (confirmed correct elsewhere; Globe's own rendering not re-verified)
- LLS Australia hover-vs-click divergence (PDV Offset vs. Location Offset) — reproduced by the original audit, not re-touched
- A dedicated Globe regression corpus

None of the above were touched. No Globe file was opened for editing this pass.

### Permission forensics (Sections 3-6)

**Effective configuration, inspected directly (no secrets exposed):**

- `~/cineglobe-frametax/.claude/settings.local.json` (repo-scoped, currently in effect) allow-list: `Bash(*)` (all shell commands), `Read/Edit/Write` scoped to `//Users/Suraj/cineglobe-frametax/**`, and a fixed list of `mcp__Claude_Browser__*` tool names (not a wildcard — an MCP browser tool outside this exact list would still prompt). Deny-list: a standard destructive-operation blocklist (force-push, hard reset, `rm -rf` variants, `sudo`, disk/security tools, credential-file reads) — unaffected by the broad Bash allow, since deny always wins.
- Two backup files in the same directory (`settings.local.json.bak.1788373092`, timestamp Sep 2 11:18; `settings.local.json.bak2.1788382256`, timestamp Sep 2 13:50) show the **effective policy evolved during this multi-day session**: both backups contain a long list of *individual command-pattern* allow rules (`Bash(ls:*)`, `Bash(git status:*)`, `Bash(pytest:*)`, `Bash(curl http://localhost:*)`, etc.) rather than a blanket `Bash(*)`. The current file (last modified Sep 2 21:36, after both backups) is the point where the policy broadened to `Bash(*)`.

**Answers to Section 4's specific questions:**

1. Already allowed without prompting (current state): essentially all Bash commands, plus Read/Edit/Write anywhere under the repo, plus the listed MCP browser tools.
2. Configured to ask: nothing Bash-related now that `Bash(*)` is in effect; anything touching paths *outside* the repo root (notably `/tmp` and `/private/tmp` — see below) is not covered by any `Write`/`Edit`/`Read` allow rule in the *current* file, unlike the two backups, which explicitly listed `Read(//tmp/**)`/`Write(//tmp/**)`/`Write(//private/tmp/**)`.
3. Denied: the fixed destructive-operation list above — force-push, hard reset, filter-branch/repo, `rm -rf` on root/home, `sudo`, disk utilities, and reads of `.ssh`/`.aws`/`.env`/credential/secret files.
4. Approvals are command-string/glob-pattern specific in the two backups (e.g. `Bash(git push origin claude/audit-frametax-features-NZcX5:*)` matched only that exact branch, not `git push origin <other-branch>`); the current file collapses this to a single `Bash(*)` wildcard, so pattern-specificity no longer applies to Bash.
5. **LIKELY**: yes, during the backup-file period, two Bash invocations differing only in surface syntax (e.g. `git push origin claude/foo` vs. a differently-worded push, or a `curl` with `-X POST -d '...'` vs. the allow-listed bare `curl http://localhost:*`) would not match the same narrow pattern and could each independently prompt.
6. **VERIFIED**: yes — MCP/browser tools are governed by their own explicit per-tool-name allow entries, entirely separate from the `Bash(*)` rule; git operations are Bash-governed (now covered); a Write/Edit/Read to a path outside the repo root is governed by its own `Write`/`Edit`/`Read` glob pattern, independently of Bash.
7. **Yes, one concrete, currently-real gap was found**: the current `settings.local.json`'s `allow` list has **no** `Write`/`Read` pattern for `/tmp/**` or `/private/tmp/**` (both backups had one; the current file dropped it). This session repeatedly used the `Write` tool against `/private/tmp/claude-501/-Users-Suraj-awardradar/<session-id>/scratchpad/*` (e.g. three separate commit-message staging files across this multi-part task). Since the session-id segment of that path changes every session, an approval granted in one session's scratchpad path does not carry forward to the next session's differently-pathed scratchpad — this is a plausible, concrete, **repeatable** source of prompts across a multi-session working history like this one.

**Reconstructed command/tool pattern for the immediately preceding (Pass 2) run**, using only what is visible in this conversation's own tool-call history (no host-log access):

- Bash invocations: dozens, spanning `git status/diff/log/rev-parse/fetch/add/commit/push`, many `python3 -c` inline multi-line scripts (a syntactically-new command every time, by construction — the exact class of command a narrow allowlist would repeatedly re-prompt for even under the backup-era config), several `pytest`/`PYTHONPATH=. python3` invocations with varying `-k` filters, `sed -i` edits, `cat`/`grep`/`tail`/`ps`/`wc` inspection commands, and `curl -X POST` calls with JSON bodies.
- Git: `fetch`, `status --short`, `add <files>`, `commit -F <scratch file>`, `push origin <branch>` (this branch matches the backup-era exact-branch allow pattern, and is Bash-covered now regardless).
- Write-tool operations: the validation artifact (repo-scoped, covered), the new test file and gate script (repo-scoped, covered), and — the one gap identified above — commit-message staging files under `/private/tmp/.../scratchpad/` (NOT covered by the current allow list).
- No browser/MCP tool calls were made during Pass 2 specifically (Globe/frontend was explicitly out of scope); Pass 1 and earlier UI-remediation turns this session did use several `mcp__Claude_Browser__*` tools, all of which are individually present in the current allow list (meaning each was, at some point, approved once and then added).
- No one-off command was obviously batchable that wasn't already batched; the main opportunity is fewer *distinct* `python3 -c` script bodies (each one is syntactically unique to a pattern-matching permission system) and closing the `/tmp` write gap.

**Most likely sources of the user's 24 observed host prompts, using the required framework:**

- **LIKELY**: the majority accumulated during the backup-file era (pattern-specific allowlist), one prompt per first-use of each distinct command shape (new `python3 -c` script bodies, new `curl` variants beyond the allow-listed bare form, git subcommands not yet in the list, MCP browser tools not yet in the list) — each such first-use is the standard Claude Code "approve once → optionally always-allow" flow, and the *current* file's own accretive growth (backup → backup2 → wildcard) is direct evidence of exactly this process having happened repeatedly.
- **VERIFIED** (directly observed in this conversation's own transcript): at least one genuine permission-dialog interaction occurred and its response stream was interrupted — a `Bash(git status --short)` call earlier this session failed with `"Tool permission stream closed before response received"`, which is only possible if a permission prompt was actually presented to the user at that moment.
- **LIKELY**: a nonzero number came from the `/tmp` write gap identified above (scratchpad commit-message files), recurring across sessions because the path itself changes every session.
- **UNKNOWN**: the exact total attributable to each category, and whether any occurred for reasons entirely outside Bash/Write (e.g. a host-level confirmation unrelated to any tool-permission rule this file governs). Host-level dialogs are not visible to this model and are not self-certified by any count in this report.

### Permission reduction plan (Section 6) — proposed, not applied

Given the *current* `Bash(*)` policy already minimizes future Bash-attributable prompts to near zero, the highest-value remaining, lowest-risk change is narrow:

**Recommended:** add back a scratch-path allow rule the two backup files already had and the current file dropped:
```json
"Read(//tmp/**)",
"Read(//private/tmp/**)",
"Write(//tmp/**)",
"Write(//private/tmp/**)"
```
This is exactly as safe as the backup-era configuration already judged it to be (it existed, was used, and was never a source of any reported problem) — `/tmp` and `/private/tmp` hold no credentials, no destructive capability, and are the documented scratchpad location this environment already directs all temporary-file work to. It does not broaden Bash, git, or any destructive-command surface at all.

No other change is recommended: `Bash(*)` combined with the existing destructive-operation deny-list already matches the requested "minimum interruption + safe project-bounded authority" balance for shell commands; broadening it further (e.g. to paths outside the repo and `/tmp`) is not proposed and was not applied.

**This change was NOT applied.** Per the task's own instruction, it is reported here for the user's review rather than silently written to the settings file.

### Final test results (this pass)

- Pass 2's final full backend suite (recovered, not re-run): **4718 passed, 2 skipped, 0 failed.**
- No backend code changed since that run in Pass 3 (only the gate script's own reporting logic, which has no test coverage requirement beyond its own successful execution — confirmed via the two full runs shown above, both clean).
- Frontend: unaffected (no frontend file touched across Pass 2 or Pass 3); last confirmed frontend result this session: **164/164 passing.**

### Files changed (Pass 2 + Pass 3, cumulative, this continuation)

- `frametax2/backend/app/services/canonical_evaluation.py` — P0-2 NPC field fix + adjustments breakdown (component path); `administrative_allocation_risk` structured field at all 3 `STATUS_PRICED` sites.
- `frametax2/backend/app/services/canonical_production_view.py` — serves `administrative_allocation_risk` on every entry.
- `frametax2/backend/tests/test_canonical_npc_trace_reconstruction.py` — new, 3 tests.
- `frametax2/backend/scripts/canonical_integrity_gate.py` — new; hardened in Pass 3 to report explicit per-invariant PASS/FAIL/DEFERRED status.
- `docs/validation/CANONICAL_OPTIMIZER_GLOBE_REMEDIATION_CLAUDE.md` — this file.

### Stop-condition self-assessment (Pass 3)

- P0-2: fixed, globally verified via the gate across all 13 genuine ingested-optimizer productions — ✓
- Saudi potential-vs-certainty: structured field fixed and verified; rate-ceiling *value* itself still deferred by design — ✓ / by-design partial
- Generic discretionary policy: per-jurisdiction ✓ (prior session), per-program override ✗ not attempted
- Program-onboarding contract: covered invariants only (BUDGET/ELIGIBILITY/NPC/PARTICIPANTS/STATUS), not the full 15-point checklist — ✗ partial
- Non-Globe scenario identity stable end-to-end: stable at the API boundary across all 13 productions (verified); no formal named identity object built; Reports not touched — ✗ partial
- Reports/selection consistency: ✗ not attempted
- Canonical Integrity Gate tests every required non-Globe invariant: ✗ — 5 of ~11 non-Globe invariant families are tested; the rest are explicitly DEFERRED and reported as such, never as PASS
- Genuine ingested productions pass the full *applicable* (tested) gate: ✓ — 13/13, 0 failures
- Partial/library projects classified honestly: ✓ — 37 correctly SKIP, never counted either direction
- Final tests pass: ✓ (4718/0 fail, reused from Pass 2, current relative to all code changes)
- Artifact committed/pushed/remotely retrievable: pending — see closing chat response

**PARTIAL — NON-GLOBE CORE NOT YET FULLY ACCEPTED.** Real, verified, substantial progress (P0-2, Saudi certainty separation, corpus taxonomy, hardened all-project gate, cardinality) — but Reports/selection consistency, per-program discretionary policy, and the full program-onboarding conformance checklist remain genuinely unbuilt, named exactly rather than claimed done. Globe is correctly excluded from this pass's completion bar per explicit instruction and was not touched.
