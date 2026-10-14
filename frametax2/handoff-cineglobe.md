# active-memory handoff: CineGlobe NA executable pricing coverage (NA-RECONCILIATION-12) + prior UI finish

**Handoff #3** · 2026-10-13 (written under time pressure: the account may become unavailable at 3pm) · Lineage: #1 (2026-10-07) optimizer accounting/location capability; #2 (2026-10-08) UI finish locked (preserved in full as Appendix A below); #3 (2026-10-13) North America reconciliation: universe frozen, ten stacks ruled, seven US rate records, NB/NS/SK corrected, QPRDP retired, real-production tests isolated, executable-coverage matrix. Sections 0-13 below describe #3; Appendix A is #2 unchanged.

## 00. HANDOFF #4 DELTA (2026-10-14, resume after the lost final response of the fifth pass) - read before sections 1-13
**What the lost prompt delivered (NA-RECONCILIATION-13, "fifth pass", stacking rules 1.15.0, authority coverage registry 1.16.0, migration 0089), reconstructed from the working tree (files last edited 2026-10-13 22:21-23:02) and verified by ONE focused test run on 2026-10-14 (no rerun needed):**
- VERIFIED by test: 312 passed (79 s) over `test_na_calculation_closure_controls`, `test_na_dave_host_pipeline_controls`, `test_na_unruled_stack_pairs_controls`, `test_na_executable_coverage_matrix`, `test_na_canonical_reconciliation`, `test_na_authority_closure_controls`, `test_canonical_stack_bridge`, `test_legacy_stacking_rule_agreement`, `test_structural_archetype_generator`, `test_knowledge_completion`, `test_canonical_knowledge_consolidation`; plus `test_generic_structural_discovery_final_correction` 24 passed (104 s, load average 15). Isolated DB `frametax2_pytest` is at Alembic head (0089 applied). No failures.
- Stack pairs RULED from primary text (the three formerly `conditional`): BC DAVE + CPTC, OFTTC + federal PSTC, BC film/TV credit + federal PSTC are all `spend_reduction` (O. Reg. 37/09 s.29(4)/s.27.1; Income Tax Regulations s.9300; ITA (BC) s.79(1), s.80, s.81.2(1)(a); CAVCO guidelines bar the PSTC only where the CPTC was received). Provincial labour-only credits net the PSTC labour in full = VERIFIED NETTING.
- DAVE dependency model BUILT: new `backend/app/optimization/structural_prerequisites.py` (`STRUCTURAL_PREREQUISITES`; BC DAVE needs host `ca_bc_film_tv_tax_credit` or `ca_bc_pstc` in the same structure; synthetic fact `ca_bc_dave__structure_host_credit_present` derived by the structural generator / candidate pricing loop in `canonical_evaluation.py`; a path without a structure leaves DAVE potential-only). This closes handoff section 12 question 2 in the "build it" direction; confirm with the user if they disagree.
- `ca_cmpa_foreign` ("CMPA Foreign certificate") retired as a non-instrument: aliased to `ca_federal_pstc`; two legacy `allowed` pairs deleted (premise contradicted by O. Reg. 37/09 s.27.1 para 7). Migration `0089_na_conditional_pairs_ruled_and_cmpa_retired.py` brings legacy DB rows into parity (two 0086 rows to spend_reduction, BC credit + PSTC row inserted, CMPA rows deleted; downgrade does not restore CMPA rows).
- Coverage registry 1.16.0: CMF Convergent, NOHFC, Sundance Documentary Fund, ITVS Open Call, Mexico EFICINE move UNPRICEABLE -> NON_GUARANTEED_SELECTIVE on primary text; `ca_telefilm_dev`, `ca_bell_fund` gain identities. Also edited (not individually re-read this pass): NJ highly-compensated-individual USD 750,000 wage exclusion (N.J.S.A. 54:10A-5.39b), Missouri RSMo 135.750 fact keys, `per_payee_limits.py`, `ny_producer_facts.py`. Matrices `NA_CANONICAL_RECONCILIATION_20261013.*` and `NA_EXECUTABLE_COVERAGE_MATRIX_20261013.*` regenerated at 22:40-22:42 and consistent with the passing matrix tests.
- NOT DONE / still OPEN: (a) the ledger section "NA-RECONCILIATION-12/13, FIFTH PASS" and the register entry were NEVER written (the working-copy ledger/register diffs are only the user's edits); write them with the HEAD-blob method when the user asks; (b) the remaining section-10 OPEN items (3)-(8): labour share of all-spend provincial credits vs PSTC (ASSUMED), NS 2026-27 renewal + Stream I/HOD, NB/SK bonuses, AR add-on arithmetic, MO uplift schedule, MT caps, WV statute, NY independent program years, OH sunset, BC s.85/86, capability profiles + benchmarks for OH/WV/MO/NJ/MT/AR, PA statute vs DCED, BH reserve, LLS-CA-01, NL facts, 44+ producer-fact controls, EFICINE/CMF/NOHFC/ITVS/Sundance rate records beyond the new coverage identities; (c) rollout (restart, acceptance-DB migrations 0082-0089, bounded regeneration, ENGINE_VERSION bump) needs explicit user authorization; (d) no ROW or real-anchor work was done or is in scope.
- Environment now: `uptime` showed the machine up 11 minutes at 00:33 on 2026-10-14, so the user's backend (pid 38530, 8010) and Vite (5173) from section 8 are probably NOT running; `ps` is blocked in the sandbox so this was not confirmed. Nothing of mine is running. `git fetch` is blocked inside the sandbox (use the sandbox-disabled call for network).
- Git: before this delta HEAD was `860edf51` (= remote tracking ref, fetch could not refresh it). The fifth-pass code/tests/artifacts were uncommitted until the commit recorded in commit `ec7574ef` (feat(na) NA-RECONCILIATION-13, 31 files; PROJECT_RULES.md, ledger and register user edits deliberately excluded). The handoff commit sits on top; `git log -1 -- frametax2/handoff-cineglobe.md` gives its hash.
**Next action in ledger order:** write the NA-13 ledger section + register entry (HEAD-blob method) ONLY when the user asks; otherwise continue the section-10 residuals resolvable from primary text (AR add-on arithmetic, MO uplift schedule, NJ/WV/MT statutes, NS 2026-27 renewal, BC s.85/86), then rollout on explicit authorization, then the wiring backlog only on the user's go.

## 0. Instructions for Claude (read first)
1. Read this whole file, then `frametax2/PROJECT_RULES.md` and `frametax2/CLAUDE.md`. This file is the source of truth; the previous chat is gone.
2. Start every reply with exactly "Yes Boss!". Prose is terse (SKINFLINT hook): answer first, then only what the user must act on. No headings or bullets unless the task's return format needs them.
3. Hard rules and corrections are in sections 4-5 and Appendix A section 4; they override defaults.
4. Do not reopen settled dimensions (section 6). Do not start the wiring backlog until the user says so.
5. First reply: at most 5 lines (goal, state, next step); end with "Ready to continue with <next step>?" unless the user's pasted task already tells you what to do, in which case do it.

## 1. Mission
- **Goal:** North America ONLY: prove EXECUTABLE pricing coverage, not just populated records: every applicable NA incentive reaches discovery, standalone/component pricing, lawful stacking and served output, with one coverage matrix and exact explanations for legitimate exclusions. Finish the remaining supported NA repairs BEFORE the producer-input / saved location-stack wiring backlog.
- **Scope limits (user, repeated):** no ROW/worldwide work; no real-anchor regeneration (LU, FVD, BH, LLS); no broad sweeps; no restart; no wiring stage; no UI redesign.
- **Done looks like:** committed code/data/tests + ledger/register entries + pushed branch with local HEAD = remote; unresolved calculation propositions listed exactly with next actions; terminal accounting never presented as calculation acceptance.

## 2. About the user
Product owner of CineGlobe (repo `surajgohill-oss/Frametax`). Pastes long precise prompts; expects exact numbers, honest blockers, primary-source evidence, DB-first recovery, persisted canonical evidence, no inflated "complete" claims. Explicitly authorized (worldwide-closeout prompt, never revoked): commit only intended files and push without further confirmation, then verify local HEAD equals remote.

## 3. Style
English; terse; start with "Yes Boss!"; report outcomes faithfully (failures with output, skipped steps stated); link files as relative markdown paths; shell commands in their own ```bash blocks (one per block).

## 4. Hard rules (word for word where quoted)
1. "Read and follow PROJECT_RULES.md before any CineGlobe incentive, co-production, stacking, optimizer, qualification, or authority-data work." Default is canonical-repository recovery and connection (DB-first), not repeated external research. Research only when retained evidence is absent; persist what it finds canonically; unknown stays unknown (None); never invent a rate, base, cap or eligibility to remove a blocker; if two sources conflict, resolve from primary text or record a precise OPEN with the exact evidence needed.
2. Never warm up, cold-evaluate, delete or write facts of a real production (LU `fa5cade5-0669-4816-bfe6-72146f8d3bae`, FVD `6c6f1c13-2d49-4bbc-bafb-2a12efa93112`, BH `4355ae88-a636-4c18-af60-ad73b2646124`, LLS `ab10b319-978e-44d3-9331-af2a5f2cccc2`) or the acceptance database. `tests/conftest.py` now refuses INSERT/UPDATE/DELETE naming those ids unless `CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS` names them. 51 real-production tests are listed in `backend/tests/real_production_registry.py` and DESELECTED by default (loudly, in the terminal summary).
3. Tests: only on the isolated DB `frametax2_pytest` with `DATABASE_URL` UNSET (`env -u DATABASE_URL`), foreground, ONE process at a time, hard alarm `perl -e 'alarm shift; exec @ARGV' <seconds> <cmd>` (ordinary command 120 s; one test file 300 s; grouped focused tests <= 720 s; push/verify 120 s). pytest/network/git push need `dangerouslyDisableSandbox: true`. Run affected files once after the final edit; never rerun green files; no broad suite. Never run `alembic` directly (an accidental `alembic downgrade` once hit the default shared DB and was refused): use `env -u DATABASE_URL backend/.venv/bin/python backend/scripts/prepare_test_database.py` for the isolated DB.
4. Restate (never weaken) pinned tests only from independently supported expectations (hand arithmetic from the cited source). A pin that conflicts with new primary text is restated in the same commit with the reason in its docstring.
5. One writer per producer fact: content-gate keys (`<slug>__<kind>_confirmed`, Inspector UI exists) versus `program-facts` keys (`ny_producer_facts.NY_EVIDENCED_FACTS`, no UI yet).
6. Update the ledger/register once per pass, only because the user asked: commit them with the HEAD-blob method (below) so the user's uncommitted edits are never committed. Commit messages go in a file (`git commit -F`), ending `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (use the attribution line in the current system reminder).
7. UI work is reported only as `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` or `BLOCKED` (see Appendix A). Do not touch the user's running servers (backend 8010, Vite 5173).
8. Do not copy credentials into any file or reply (DB password is in the user's environment only).

## 5. Corrections (this session)
| # | Claude did | User wanted |
|---|---|---|
| 1 | Called "CLOSED" terminal rows that still had open authority dimensions | Correct "closed" labels where material obligations remain; terminal accounting is not calculation acceptance |
| 2 | Ran tests that evaluate/delete real-project facts | Isolate them (done: registry + conftest guard) and use synthetic fixtures |
| 3 | Attached SK provenance but withheld it, misreading the two-axis contract | Apply the existing discretionary-program policy; provenance alone must not change economics (done) |
| 4 | Mixed assumed allocation with verified netting in one description | Keep them separate (done: VERIFIED NETTING vs ASSUMED ALLOCATION labels and split amounts) |
| 5 | Left discretionary ceiling-only programs unpriced with no figure | Show potential with a ZERO guaranteed floor (done in the pricing kernel) |

## 6. Decisions (settled; do not reopen)
- Stacking registry 1.13.0 (ten formerly unruled pairs ruled from RC4164 lines 421-430 / ITA 125.5(1)(b) / RC4385; DAVE+CPTC and OFTTC+PSTC and BC-domestic+federal-PSTC are `conditional`, i.e. blocking, because no primary text states them; NY independent credit with `ny_state_film` and with the post-production credit are UNRULED, blocking, OPEN).
- All-spend provincial credits net the federal PSTC by an ASSUMED rate x PSTC-labour share (whole credit disclosed as lower bound); labour-only credits (OPSTC s.3.02, BC DAVE) are VERIFIED netting. Only awarded (guaranteed) amounts net; ceilings never.
- Nova Scotia = 25% (Stream II) of ALL eligible cost, CAD 10M cap, status CURRENT on the official page with the "renewed to FY2025-26" wording kept as an unreconciled qualifier. New Brunswick = LIFT 2026/27 discretionary grant (ceilings 25%/35%, company cap CAD 2M, no floor). Saskatchewan = B1 DISPLAY_ONLY_ZERO_GUARANTEED (existing ruling kept; structured provenance attached = knowledge axis only; served as a disposition naming "25% to 30%").
- "QPRDP" is not an official credit: it is the Quebec production services credit `ca_qc_pstc` (migration 0087 deletes the legacy rows). "Film Incentive BC" is the BC film and television tax credit (ITA (BC) s.80) = new `ca_bc_film_tv_tax_credit`: 35% (40% when photography after 2024-12-31) of qualified BC labour trimmed to the 60% cost cap; mutually exclusive with the BC PSTC (s.83.1), allowed with DAVE (s.81.2(1)(a)), spend_reduction with the CPTC, conditional with the federal PSTC.
- BC DAVE base = labour directly attributable to digital animation / visual effects (VFX-category lines) per ITA (BC) s.81.2(2), NOT all labour (the old all-labour base over-granted live-action budgets).
- Unknown capability never rejects: `production_discovery` accepts a priced program whose jurisdiction has no capability profile as `incentive_ready` with production fit UNKNOWN (the six new states OH, WV, MO, NJ, MT, AR). Missing cost benchmarks leave MFNI UNMODELED (served `mfni_status`), never suppress the scenario.
- Floorless ceilings whose award conditions are merely UNRESOLVED are served as POTENTIAL ONLY (executable, guaranteed 0, ceiling kept, `ceiling_requires_confirmation`); a condition that genuinely FAILED (e.g. awarded rate above the ceiling, residency below minimum) stays a refusal.

## 7. Changed / rejected
- NB 2017-18 THC incentive (25%/30%, CAD 800k) -> LIFT 2026/27. NS labour-only secondary basis -> all eligible cost. SK par `annual_cap_usd` -> native CAD cap rule. QPRDP spelling -> retired. DAVE all-labour base -> VFX labour base. Unruled-pair "blocks" for ceiling-only programs -> potential-only.
- Rejected: inventing capability profiles / cost benchmarks for the six new states; moving SK out of the B1 ruling; treating summariser-read pages as raw primary text (those records stay PARSED).

## 8. Data & facts (exact)
**Checkout:** `/Users/Suraj/cineglobe-claude-global-optimizer-remediation` (git root; app in `frametax2/`; backend commands from `frametax2/backend`, venv `.venv`). Branch `claude/global-optimizer-remediation`. Remote `origin` = `https://github.com/surajgohill-oss/Frametax.git`.
**HEAD (updated after the fourth pass was committed):** local = remote after the push in this delivery. Recent: `ed96523c` docs NA-12 fourth pass (ledger + register); `02541351` NY pairs ruled + PSTC pairs narrowed (code/tests/artifacts); `41d264ef` handoff update (third pass); `40919396` docs NA-12 third pass; `4dbb971e` third-pass code/matrix; `0b1fb196` docs second pass; `d10e96e1` NB/NS/US records/profiles/QPRDP/isolation; `3cc0c2e1` ten stacks. The handoff commit (this file only) sits on top; `git log -1 -- frametax2/handoff-cineglobe.md` gives its hash.
**Databases and migration levels:** isolated test DB `frametax2_pytest` is at Alembic head **0088** (0086 ten NA pair rows; 0087 retire QPRDP rows; 0088 seed six state `jurisdictions` rows). Acceptance DB `frametax2_claude_optimizer_acceptance_20260919` (used by the user's running backend): migrations 0082-0088 are NOT applied (exact current revision not re-verified this session; check read-only with the user's own env before any rollout). The default/shared `frametax2` DB: never touch. Org `CURRENT_ORGANIZATION_ID=11381771-5b1c-4980-9117-e3e47a4cb354`.
**Engine:** `ENGINE_VERSION = "canonical-1.130.0"` (not bumped); stacking rules `1.14.0`; authority coverage registry `1.15.0`.
**Running processes (do not kill/restart):** user's backend uvicorn pid 38530 on 127.0.0.1:8010 (acceptance DB, no --reload); user's Vite pid 68712 on 5173 (background task `but042iic`); my last focused pytest run pid 64835 on `frametax2_pytest`, output file `/private/tmp/claude-501/-Users-Suraj-cineglobe-claude-global-optimizer-remediation/1d83c6cd-8aa4-48fa-886d-e5514e73348a/tasks/bykpj9vve.output` (may be gone; if no summary line exists, rerun the focused set ONCE, section 10).

## 9. Names and paths
- Canonical owners: rate doctrine `backend/app/data/program_rate_rules_worldwide.py` (DoctrineRecord + SourceProvenance) and `program_rate_rules.py` (caps, QpeCapRule); qualification/timing `backend/app/data/program_requirements.py` (EvidenceRecord, additional_facts); stacking `backend/app/optimization/stacking_rules.py` consumed by `backend/app/calculators/canonical_stack_bridge.py` (direction table, PSTC assisting/apportioned sets, `netting_basis_label`) and `structural_archetype_generator.py`; coverage `backend/app/data/authority_coverage_registry.py` (`_B1_DISCRETIONARY_RULING`, bindings); discovery `backend/app/calculators/production_discovery.py`; pricing kernel `backend/app/calculators/allocation_pricing.py`; served view `backend/app/services/canonical_production_view.py`; MFNI status `backend/app/services/mfni_status.py` (new); NA reconciliation derivation `backend/app/services/na_canonical_reconciliation.py` + script `backend/scripts/na_canonical_reconciliation.py`.
- Evidence and ledger: `frametax2/docs/architecture/CAPABILITY_LEDGER.md` (sections NA-RECONCILIATION-11, NA-RECONCILIATION-12, NA-RECONCILIATION-12 SECOND PASS), `frametax2/docs/validation/FOUR_ANCHOR_QPE_ISSUE_REGISTER.md` (register entries), matrices `frametax2/docs/validation/NA_CANONICAL_RECONCILIATION_20261013.{csv,json}` (reconciliation, recon NA-RECONCILIATION-12) and `frametax2/docs/validation/NA_EXECUTABLE_COVERAGE_MATRIX_20261013.{csv,json}` (executable coverage; generated by `WRITE_NA_COVERAGE_MATRIX=1 pytest tests/test_na_executable_coverage_matrix.py`). Research downloads live only in the ephemeral scratchpad (`/private/tmp/claude-501/.../scratchpad/`: NB LIFT PDF, NS guidelines, BC ITA text, HB24-1358, NY regs): re-fetch if lost.
- Synthetic proofs: `backend/tests/na_coverage_matrix.py` (builder; P1 = 3.0M US-TX budget, P2 = VFX/post-heavy 4.4M), `test_na_executable_coverage_matrix.py`, `test_na_synthetic_pipeline_controls.py`, `test_na_unruled_stack_pairs_controls.py`, `test_na_us_rate_record_controls.py`, `test_real_production_isolation.py`.

## 10. Work state
**Committed and pushed (HEAD 0b1fb196):** NA universe frozen (60 canonical NA programs); ten stacks ruled; SK/NS/NB/OFTTC/others profiles; seven US rate records (OH, WV, NJ, MO, AR, MT, NY independent) + Colorado income tax credit; QPRDP retired; real-production isolation; ledger/register through the second pass.
**Third and fourth passes are COMMITTED** (`4dbb971e`/`40919396` pushed; `02541351` code/tests/artifacts and `ed96523c` ledger section 'NA-RECONCILIATION-12, FOURTH PASS' + register entry pushed in this delivery). Tests: third-pass focused run 682 passed, 2 failed (Cyprus/Greece dollar-cap, ROW), 2 skipped; fourth pass: matrix test 7 passed and the stack-sensitive set 307 passed with only the ROW cap failures plus HO-013 (`test_generic_structural_discovery_final_correction`), a 60 s timing gate that took 73-95 s under load average 6-7 (load-sensitive, not rerun). Matrix: 37 pairs, 0 unruled (23 spend_reduction, 7 mutually_exclusive, 3 allowed, 3 conditional, 1 same_cost). Other known failures are in the ledger third-pass section. No tests are running; processes: only the user's backend (pid 38530, 8010) and Vite (pid 68712, 5173).
**Uncommitted USER edits (never commit, never revert):** `frametax2/PROJECT_RULES.md` (+55 lines); `frametax2/docs/architecture/CAPABILITY_LEDGER.md` working copy = user's edits (+143 lines, e.g. LEDGER ITEM 16 Company Globe) plus Claude's mirrored NA sections already in HEAD; `frametax2/docs/validation/FOUR_ANCHOR_QPE_ISSUE_REGISTER.md` (+4 lines, user's NA-CODEX-08 entry) plus Claude's mirrored NA entries. Untracked user files: `frametax2/ROW_EUROPE_QPE_AUDIT.md`, `frametax2/docs/validation/{AG_ROW_AUDIT_PROMPT_DEFERRED_20261011.md, CALCULATION_ASSURANCE_DELTA_REVIEW_20261010.md, CODEX_*20261011.*, PROJECT_OPEN_ITEM_RECOVERY.md}`, log files `.backend_gd_wire.log`, `.frontend_gd_wire.log`, `frametax2/.backend_iso_8011.log`, `frametax2/.frontend_iso_5174.log`, `.playwright-mcp/`. To commit a ledger/register change without their edits: `git show HEAD:<path> > tmp; append/replace Claude's section in tmp; blob=$(git hash-object -w tmp); git update-index --cacheinfo 100644,$blob,<path>; git commit -F msgfile`, then apply the same text to the working copy.
**Pending rollout (needs EXPLICIT user authorization; not done):** restart the user's backend (digest modules changed: `canonical_stack_bridge`, `program_rate_rules`, `authority_coverage_registry`, `allocation_pricing`, discovery) which makes all four productions read STALE (opening one cold-evaluates it); apply migrations 0082-0088 to the acceptance DB; bounded regeneration of LU/FVD/BH/LLS via `backend/scripts/regenerate_project_bounded.py` (never `/evaluation/begin`); consider an ENGINE_VERSION bump; then the independent UI/served verification the PROJECT_RULES gate requires.

**COMPLETED NA obligations:** (see sections 6 and the ledger) ten stacks; NB/NS/SK; seven US rate records + CO credit + profiles (18+); UT/VA read from official pages; QPRDP; BC domestic credit record and pairs; DAVE base; six new states discoverable with UNKNOWN fit; MFNI UNMODELED status; potential-only discretionary ceilings; executable-coverage matrix; New York independent-credit pairs ruled from the ESD page (fourth pass); PSTC conditional pairs narrowed to the open provincial side; real-production isolation.
**OPEN NA obligations (exact):** (1) [CLOSED in the fourth pass: NY independent pairs are mutually_exclusive per the ESD page.] (2) DAVE with the CPTC and a DAVE dependency model (DAVE rides on a BC credit; standalone DAVE should require s.80 or s.82.1 eligibility); OFTTC and BC domestic credit with the federal PSTC: federal side verified (CAVCO bars only the CPTC; provincial credits are assistance), open only whether the provincial side allows concurrent eligibility (all three `conditional`). (3) Labour share of all-spend provincial credits vs PSTC (ASSUMED allocation: Quebec, Manitoba, NL, Alberta, Nova Scotia, New Brunswick, Saskatchewan) needs a CRA/provincial statement. (4) NS 2026-27 renewal wording and Stream I/HOD facts; NB bonus facts; SK bonuses. (5) Rate-record gaps: AR add-on arithmetic (25+10+5 vs stated 30%) + statute; MO uplift schedule/RSMo; MT Revenue caps/thresholds; NJ statute/film cap/discretion; WV statute; NY independent program years (pools recorded); OH transferability/sunset; BC domestic regional/distant/training/scriptwriting credits and s.85/86 deadlines. (6) Capability profiles + cost benchmarks for OH, WV, MO, NJ, MT, AR (no data; do not invent; relocation destination offering and real MFNI wait on them). (7) PA statute vs DCED; BH USD 60,000 reserve; LLS-CA-01; NL eligible-corporation facts; 44+ producer-fact propositions needing Overview/Inspector controls (new keys: `wv_ten_resident_hires_confirmed`, `nj_film_spend_outside_nyc_radius_confirmed`, `ca_bc_film_tv_photography_after_2024_confirmed`). (8) Rate/base/cap records for EFICINE, CMF, NOHFC, ITVS, Sundance and the Bell/CMPA/NSI/Telefilm spellings. (9) The four ROW-side/unrelated test failures listed above (not this scope). (10) Stale LU/FVD/BH/LLS generations. (11) Ledger/register: written through the fourth pass.

## 11. Next steps (in order)
1. Passes three and four are done and pushed (section 10). Report the exact unresolved calculation propositions (section 10 OPEN list) to the user BEFORE touching the wiring backlog. The user's latest instruction: continue the existing NA calculation residuals; do not start wiring yet. Next residual candidates resolvable from primary text: AR add-on arithmetic/statute, MO uplift schedule, NJ/WV/MT statutes, NS 2026-27 renewal, BC s.85/86 deadlines; leave precise OPEN where no primary text exists.
2. Then, only on the user's go: DAVE dependency model, capability profiles, then the producer-input / saved location-stack wiring backlog in ledger order.

## 12. Open questions
- Authorization for the rollout (restart, migrations 0082-0088 on acceptance DB, bounded regeneration, ENGINE_VERSION bump)?
- Should the DAVE dependency (requires the BC domestic or services credit in the same structure) be built now or stay a blocking `conditional`?
- Who commits the user's `PROJECT_RULES.md`, ledger Item 16 and the register NA-CODEX-08 edits?

## 13. Re-attach checklist
- Nothing to attach; everything is in the repo. Credentials are in the user's environment only (not recorded here).

<sub>Audit: handoff #3 · secrets removed: none present · generated manually under time pressure; verify section 10 numbers against `git status` and the test output before relying on them.</sub>

---

# APPENDIX A — Handoff #2 (2026-10-08), preserved unchanged (UI finish; rules in its section 4 still apply)

# active-memory handoff: CineGlobe global optimizer remediation + UI finish

**Handoff #2** · 2026-10-08 · Lineage: #1 (2026-10-07): optimizer scenario-universe accounting (1.104.0), music/post-VFX package policy + retention test + suppressed-reference UI (1.105.0), location-capability Codex remediation, final pre-Codex handoff, Workspace card alignment + hero poster styling (then uncommitted); #2 (2026-10-08): UI finish committed and locked (cards, hero, sidebar, Overview four-slot, shared economic well), project-location control wiring proved end to end + precise "conditional" wording, economic card interior hierarchy with MFNI placeholder. Code at `9a69ef6`, pushed.

## 0. Instructions for Claude (read first)

You are continuing work from a previous chat. That chat is gone; this file is the complete context and the source of truth.

1. Read this whole file before replying.
2. Follow sections 3 (Style), 4 (Hard rules) and 5 (Corrections) in every reply, for the rest of this chat. They override your defaults.
3. Use the values in section 8 exactly. Never round, re-estimate, or "correct" them.
4. Do not suggest anything listed in section 7 (Changed / rejected) again unless the user brings it up.
5. Code word: Start every reply with exactly "Yes Boss!"
6. Your first reply: at most 5 lines covering the goal, the current state, and the next step (section 11). Mention any files from section 13 that were not attached. Ask the questions in section 12 if there are any. End with "Ready to continue with <next step>?" Then wait for the user's go.

## 1. Mission
- **Goal:** Bring the CineGlobe film-incentive optimizer (backend engine, location-capability data, served API and Workspace / Overview / Globe UI) to a state that passes independent Codex acceptance; keep the Workspace, Overview and hero UI in the locked finish below.
- **Done looks like:** Codex (independent auditor) accepts the delta range from `611fb723daac05d5d91265172d334c61a37deb9f` through `9a69ef6` plus later commits; UI work stays at `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` until an independent reviewer accepts it; remaining items are classified honestly in the ledger.
- **Why it matters / context:** The user runs multi-model remediation: Claude implements, Codex (and, for UI prompts, Gemini-written briefs) review or direct. Claude never self-certifies UI work.

## 2. About the user (as relevant to this work)
- Product owner of CineGlobe (repo `surajgohill-oss/Frametax`), a film-production incentive / location optimizer.
- Pastes long, precise task prompts (some written by Gemini, later ones by a Codex/chat reviewer) with gates, a "RETURN BRIEFLY" field list, and an explicit commit/push instruction. Prompts sometimes reverse earlier choices or arrive truncated; the user calls the resulting churn "a loop".
- Expects exact numbers, honest blockers, no inflated claims. Uses `/model` to switch Claude models mid-chat.

## 3. Style & communication
- **Language:** English.
- **Tone:** direct, factual, no fluff; plain language a non-engineer can follow.
- **Reply length:** short. End-of-task replies answer every field of the task's "RETURN BRIEFLY" / "RETURN SHORT" list, nothing more. A hook adds "SKINFLINT" (terse prose: answer first; no headings/bullet lists unless the user asks for a report or the task's return format needs them).
- **Formatting:** bullets/tables fine for task reports; code blocks for commands; no emojis except in active-memory checkpoint/handoff outputs. Link files as markdown paths relative to the working directory.
- **Working style:** do the whole task without stopping for routine confirmation; stop only for wrong database/worktree, destructive-data risk or irreconcilable Git lineage. Give a short progress note when a step takes long. Browser checks use the built-in browser pane at `http://localhost:5173`.
- **Avoid:** claiming "complete/verified/accepted" for UI work; broad test suites; repeated regenerations; restarting audits; external research unless authorized; committing the unrelated `PROJECT_RULES.md` change; reversing a locked UI decision silently.

## 4. Hard rules (word for word)
1. "Read and follow PROJECT_RULES.md before any CineGlobe incentive, co-production, stacking, optimizer, qualification, or authority-data work." (`frametax2/CLAUDE.md`)
2. "Claude may report exactly one of two UI/runtime terminal statuses: `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` or `BLOCKED`." (PROJECT_RULES INDEPENDENT UI COMPLETION GATE; own-browser checks are implementation evidence only)
3. "Never warm up or cold-evaluate a real production for test preparation." / "Cold evaluation of Little Utopia, F#K Valentine's Day, Lips Like Sugar, or Bad Hombres requires explicit user authorization for that specific run." (A task that explicitly commissions a changed save, e.g. the location-wiring task, authorizes that targeted evaluation.)
4. Hard timeouts: ordinary command 120 s; individual test file 300 s; grouped focused tests 900 s; single real-project recomputation 720 s max (use `perl -e 'alarm shift; exec @ARGV' <s> <cmd>`; macOS has no `timeout`); push/remote verify 120 s. Foreground only; no background test processes.
5. "Retry at most once, and only after a documented causal correction"; "a second timeout on the same step is final for that step".
6. "Green tests are never rerun." Run the affected frontend/backend tests once after implementation; rerun only failed files/nodes.
7. "Fail closed on the database before any DB-backed test: assert the exact isolated DB name." Backend tests run on `frametax2_pytest` (`env -u DATABASE_URL`), sandbox disabled.
8. "Enumeration cardinality must never define persistence cardinality." Invariant: `candidates generated == detailed rows persisted + sum(candidate aggregate counts)`.
9. "Do not create a parallel registry, optimizer, or calculation path. Extend the existing canonical owner and served bridge."
10. "Do not stop for routine questions. Report a blocker only for wrong database, destructive-data risk, or irreconcilable Git lineage."
11. Browser acceptance: "exactly one frontend process and one backend process" (PROJECT_RULES). Do not start a backend yourself unless the user allows it (it was allowed once on 2026-10-08 and the process is still running).
12. UI tasks: "STYLING / CSS ONLY … DO NOT touch backend APIs, data models, calculation logic, or props" unless the task says markup/wiring is in scope; card exterior footprint, grids and the 3→2→1 Workspace reflow are frozen.
13. Commits end with the `Co-Authored-By:` line named in the session's system reminder (this chat used `Claude Opus 5.5` and later `Claude Sonnet 5.5`; use whatever the reminder says at commit time). PR descriptions end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
14. Never run commands on the shared `frametax2` database or tests on the 4 real productions' data except as a task explicitly permits.
15. "Leave the unrelated uncommitted `PROJECT_RULES.md` change untouched." (someone else's "VISUAL-REVIEW EFFICIENCY AND AGENT ROLE SPLIT" section; Claude is implementation owner, Codex/chat the reviewer.)
16. "Update the ledger and handoff only when the user explicitly requests it" (PROJECT_RULES gate item 13); when a task says "update once at completion", do exactly once.
17. Do not apply the word CONDITIONAL to a whole structure merely because one jurisdiction, uplift or maximum value requires facts; keep the precise category and disclose the unresolved fact separately.
18. No rates, yields or percentages on a default card face (they stay in the Inspector); no Gross Budget inside a card.
19. Never use "locked", "guaranteed" or "statutory entitlement" on a card; "Not Suitable" means a confirmed production-fit mismatch only.
20. Do not invent or calculate MFNI in the card pass; the reserved rows say it is not yet modeled.
21. When a pasted prompt would reverse a locked UI decision (section 6), say so plainly instead of silently flip-flopping.

## 5. Corrections log
| # | Claude did | The user wanted |
|---|---|---|
| 1 | Started web research mid-task (#1) | "STOP ALL EXTERNAL RESEARCH NOW" — canonical repository/database recovery only unless research is explicitly authorized |
| 2 | Kept rerunning / repeating checks (#1) | "EFFICIENCY CORRECTION — DO NOT RESTART THE TASK… Do not rerun any command, evaluation, test family, browser matrix, or reconciliation already completed" |
| 3 | Stopped mid-verification (#1) | "RESUME — FINALIZE CURRENT WORK; DO NOT RESTART OR REGENERATE" |
| 4 | Census cells said film-office pages "were not queried" (#1) | Every unresolved cell must complete and document the bounded official-source sequence |
| 5 | Natural Earth tiered PEER_REVIEWED_OPEN_DATASET (#1) | Use honest `OPEN_GEOSPATIAL_DATASET` |
| 6 | Joggins (fossil) supported present-day rainforest; NB buffer spillover (#1) | Present-day propositions only; one admin-1 unit per point |
| 7 | Ledger called items "closed" beyond evidence (#1) | Classify as READY_FOR_CODEX_ACCEPTANCE / TERMINAL_NEUTRAL / DEFERRED_PRODUCT_WORK / INGESTION_ACCEPTANCE_REQUIRED / COMPANY_GLOBE_REQUIRED |
| 8 | Delivered a preview HTML the user could not see | "i can't see the preview. open a new browser window?" → open it in the browser pane and send the file with SendUserFile; the sandbox blocks `open` |
| 9 | Treated each pasted UI prompt as final, flip-flopping artwork fit (cover/contain/square/dual-layer) and card/hero themes | "you are stuck in a loop i think" → "lock it- hold off on recently viewed files." then summarise all changes; commit once |
| 10 | Reported BLOCKED when the backend was down and would not start it | "its ok for this one time restart back end." (a one-time allowance; the backend is now running) |
| 11 | Cards/Overview labelled whole structures "CONDITIONAL" (Overview status, Inspector "Economics: Conditional", universe row "· conditional") | "Do not apply the word CONDITIONAL to an entire structure merely because one jurisdiction, uplift or maximum value requires facts. Preserve the more precise structure category and disclose the specific unresolved upside/fact separately." |
| 12 | A package was committed while a changed-task commit trailer/model drifted | Use the attribution line in the current system reminder (Opus 5.5 earlier, Sonnet 5.5 later) |
| 13 | An earlier hero used one universal neutral/pale background | "Every project must retain its own key-art-derived color identity… Do not use one universal neutral background"; Bad Hombres alone keeps a neutral slate fallback (no artwork) |

## 6. Decisions
| Decision | Why |
|---|---|
| Engine `canonical-1.104.0` / `1.105.0` unchanged (still current `ENGINE_VERSION = "canonical-1.105.0"`): relocated anchor routes single movable units; `post_vfx_music_package` routable; music split surfaced at NPC benefit ≥ $25,000 | #1 decisions; no engine change in #2 |
| Policy-suppressed references in a collapsed secondary section, never primary cards | user spec (#1) |
| 224 unresolved capability cells stay AUTHORITY_UNRESOLVED_NEUTRAL (TERMINAL_NEUTRAL) | silence ≠ negative (#1) |
| UI finish LOCKED (commit `1d53099`, memory note `workspace-ui-finish-locked`), later refined: hero = one 160px row (back link 72px, 200×112 cover-fit art plate with 24px gap, title + chips, budget/questions bay, icons top-right), a project-specific DARK cinematic bay in both themes (day slightly lifted); per-project palettes hand-curated in `ProductionHero.jsx` `HERO_THEMES` | user's final hero closeout |
| Hero palettes: FVD wine/charcoal + crimson bloom + warm-cream highlight; Little Utopia harbour-blue/charcoal + sunset-gold bloom + sea-blue light; Lips Like Sugar blue-black + cyan/cobalt bloom + twilight violet + faint red bottom rule; Bad Hombres neutral slate + dark slate fallback plate | user spec |
| Overview always four cards in order: Current Location, Leading Jurisdiction, Optimized Structure, Conditional Upside (`selectAnchorLeadingOptimized`); Leading = cheapest fit-confirmed winner (never a confirmed-mismatch one); Optimized = optimizer's top recommended else top evaluated alternative (flagged reference); Upside = lowest potential-NPC structure with `ceiling_status` CONDITIONAL and not WEAK fit; no economic identity repeats | user spec + production fit |
| Overview shows "Production Budget $X USD" once above the grid; Workspace shows Qualified spend once, quietly, after the well | user spec |
| ONE shared interior `components/EconomicWell.jsx` for Workspace and Overview cards; field order: title → structural category → Maximum-potential NPC (dominant) → Confirmed NPC → confirmed + maximum-potential incentive → confirmed/potential bar → MFNI placeholder → attainability + one requirement → actions | user spec (design doc `docs/design/ECONOMIC_CARD_HIERARCHY.md`) |
| Bar: jade = confirmed ÷ maximum, amber = remainder, one separator; all jade if equal; all amber if confirmed 0 and max > 0; empty neutral track if no maximum; labels only confirmed $ and +$delta (served `potential_upside_usd`) | user spec |
| `cardStatus` returns ANCHOR / LEADING / OPTIMIZED / LOW-LOCATION-FIT REFERENCE / LOCATION FIT UNCONFIRMED / REFERENCE ALTERNATIVE; never CONDITIONAL | rule 17 |
| Single-jurisdiction contract serves `ceiling_status` per record; no-requirements-on-file UNKNOWN fit is not a fit claim (BH: LEADING 1 / REFERENCE 90 / CONDITIONAL needs-facts 20); requirements on file but unassessable stay Conditional (needs facts) | wiring task |
| Inspector states `Jurisdiction category` + reason and `Economics: Confirmed floor · maximum needs the facts below` (`economicsStatusText`) | wiring task |
| "Recently Viewed Files" sidebar item ON HOLD (no route/data exists) | user: "hold off on recently viewed files" |
| Sidebar keeps dark-rail colours in both themes (9px/700/0.12em group headers, 12px/500 links, gold `#E5B233` active accent) | rail is dark in both themes |
| Hero/Workspace theme selector is `:root[data-theme="night"]` (day = `data-theme="day"`) | app's own theme attribute |

## 7. Changed / rejected
- Strict `> $25,000` music carve-out → `≥ $25,000`
- Stretched full-art hero → left art plate (108×162 poster → 110×160 contain → cover → 136×136 square → dual-layer → **200×112 landscape cover**, final)
- Pale vellum hero by day (`1d53099`) → dark per-project cinematic bay in both themes (user's later spec)
- Dark-only cards (`#14171D`) → theme-aware cards (light vellum `#FCFAF7`; night gradient `#181C23→#13161C`)
- Fixed 183px card divider / 92px header / 28px rows layout → the economic-card interior v2 (Workspace card still 320×439; divider concept gone)
- Segmented LED risk ladder (`.wsx-range`) → simple jade/amber bar; MFNI placeholder rows added
- Graph-paper gridlines behind the Workspace rack removed
- ❌ Gemini's 136×136 square plate ("obsolete"), Tailwind class specs (project uses plain CSS), `Recently Viewed Files` for now
- ❌ Fixing the card middle area at 54px (would clip served data)
- ❌ Relabelling executable single-jurisdiction rows with unconfirmed fit as REFERENCE (kept CONDITIONAL_ALTERNATIVE / needs-facts; Globe colours depend on it)
- Per-card rows dropped from card faces (still in the Inspector): "Costs more than Current Location", reference explanation (now the badge tooltip), discretionary badge, Overview "Vs. current / base", confidence badge, rate/percentage lines

## 8. Data & facts (exact)
**Repo / env**
- Worktree: `/Users/Suraj/cineglobe-claude-global-optimizer-remediation` (git root; app in `frametax2/`), branch `claude/global-optimizer-remediation`; remote `https://github.com/surajgohill-oss/Frametax.git`.
- HEAD / remote: `9a69ef69013e00d489e699be05beeb0e8e3a4d3b` (pushed; local = remote).
- This chat's commits (oldest → newest): `1d53099` lock card/hero/sidebar finish; `ff7c969` economic hierarchy, contract range bar, project hero tints; `f6839a9` Overview four-slot + curated hero palettes; `b6ab849` Overview on shared well + cinematic heroes; `ba8cfb0` location wiring + precise wording; `9a69ef6` economic card interior v2. Earlier: `40e418c`, `a43f59e`, `36844e6`, `611fb72`, `ec5efcc`, `dac1514`.
- Acceptance DB: `frametax2_claude_optimizer_acceptance_20260919`; isolated test DB: `frametax2_pytest`; org `CURRENT_ORGANIZATION_ID=11381771-5b1c-4980-9117-e3e47a4cb354`.
- Backend (one process, started 2026-10-08, log `frametax2/.backend_gd_wire.log`): `DATABASE_URL="postgresql+psycopg://frametax:[secret removed: re-enter it]@localhost:5432/frametax2_claude_optimizer_acceptance_20260919" CURRENT_ORGANIZATION_ID=… .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010` from `frametax2/backend`; it has no `--reload` (restart to pick up Python changes). Frontend vite on `5173`; open `http://localhost:5173` (`127.0.0.1:5173` fails CORS).
- DB/network/push commands need the sandbox disabled; `curl` to localhost from the shell fails inside the sandbox (use the browser pane).
- Uncommitted/untracked on purpose: `frametax2/PROJECT_RULES.md` (modified, not Claude's), `.backend_gd_wire.log`, `.frontend_gd_wire.log`, `frametax2/.backend_gd_wire.log`, `frametax2/handoff-cineglobe.md`.

**Projects**
| Project | ID | Home |
|---|---|---|
| The Little Utopia (LU) | `fa5cade5-0669-4816-bfe6-72146f8d3bae` | MU |
| F#K Valentine's Day (FVD) | `6c6f1c13-2d49-4bbc-bafb-2a12efa93112` | GR |
| Bad Hombres (BH) | `4355ae88-a636-4c18-af60-ad73b2646124` | US-NM (no artwork: artwork API 404) |
| Lips Like Sugar (LLS) | `ab10b319-978e-44d3-9331-af2a5f2cccc2` | US-CA (portrait 2550×3300 art; plate crops to a dark strip) |

**canonical-1.105.0 snapshot (unchanged this chat)**
| | LU | FVD | BH | LLS |
|---|---:|---:|---:|---:|
| Generated = persisted + aggregated | 223,058 = 977 + 222,081 | 1,215,900 = 2,108 + 1,213,792 | 11,851 = 1,126 + 10,725 | 1,298,334 = 2,094 + 1,296,240 |
| Curated scenarios | 557 | 646 | 275 | 680 |
| Winners / SJ rows | 92 / 217 | 91 / 217 | 91 / 217 | 92 / 217 |
| Fit counts (confirmed / unconfirmed / weak) | 379 / 0 / 178 | 480 / 0 / 166 | 0 / 275 / 0 | 325 / 158 / 197 |
| Evaluation generations (before → after location wiring proof) | 26 | 24 | 20 → 21 (one changed save) | 15 |

- Location census: 1,140 cells = 826 SUPPORTED / 90 NOT_SUPPORTED / 224 UNRESOLVED_NEUTRAL.
- Location wiring proof (BH, `marine_open_water=true`): one POST → `EVALUATION_COMPLETE` in 11.4 s, generations 20 → 21, fit 0/275/0 → 146 confirmed / 129 weak, economic digest identical; same payload resave `changed:false`, no evaluation (17 ms); clearing the override → `EVALUATION_REUSED`, still 21, state back to baseline; other three projects unchanged. A NULL-valued `marine_open_water` override row remains in BH (harmless).
- Real-project card geometry: Workspace card 320×439 (rack columns 320px; 3→2→1 reflow at container widths 1023 / 685); Overview card 190px wide at 1440 (150px at 1280, 454px at 1024), height ~430–450 (up to ~490–540 with an Exclude button / narrow); budgets: FVD $4,517,687, LU $4,364,393, BH $2,482,023, LLS $11,983,654.
- Frontend tests this chat: 181/181 over 14 files (last run); backend focused 103/103 and location set 126/126; command: `cd frametax2/frontend && perl -e 'alarm 300; exec @ARGV' node --test tests/<files>`; backend: `cd frametax2/backend && env -u DATABASE_URL PYTHONUNBUFFERED=1 perl -e 'alarm 720; exec @ARGV' .venv/bin/python -u -m pytest -v -p no:cacheprovider tests/<files>`.

## 9. People, terms & names
- **People:** the user (product owner); Codex (independent auditor/director); Gemini (wrote some UI briefs).
- **Terms:** LU, FVD, BH, LLS; SJ = Single-Jurisdiction mode; NPC = net production cost; QPE = qualified production expenditure; MFNI = regional production-cost normalization (not yet applied anywhere; never expand its meaning); "well" = the economic card interior; attainability = how reachable the maximum is; "needs-facts" = CONDITIONAL_ALTERNATIVE category (jurisdiction level only).
- **Names in use:** `frontend/src/components/EconomicWell.jsx`, `IncentiveIntelligence.jsx` (Overview), `ProductionHero.jsx` (`HERO_THEMES`, `getProjectHeroTheme`), `screens/production/Workspace.jsx` (`ScenarioCard`), `lib/productionOptions.js` (`selectAnchorLeadingOptimized`, `cardStatus`), `lib/incentivePotential.js` (`readIncentivePotential`, `attainability`, `economicsStatusText`), `lib/alternativeLabels.js` (`ALT`), `lib/globeData.js` (`contractStructure`), `components/JurisdictionUniverse.jsx` (`openUniverseRecord`), `shell/Inspector.jsx` (`JurisdictionCategoryDisclosure`), `styles/screens.css` (`.wsx-econ*`, `.wsx-bar*`, `.ii-*`, `.ph-*` in `shell.css`), backend `app/services/program_pricing_crosswalk.py` (`build_single_jurisdiction_contract`), `app/api/v1/cineglobe.py` (`post_project_locations`), `app/services/canonical_project_economics.py` (`physical_requirement_fingerprint_facts`), `app/services/incentive_potential.py`.
- **Docs:** `docs/architecture/CAPABILITY_LEDGER.md` (Items 1-11), `ACCOUNT_TRANSFER_HANDOFF.md`, `docs/design/ECONOMIC_CARD_HIERARCHY.md`, `docs/validation/CODEX_LOCATION_CAPABILITY_FINAL_ACCEPTANCE.md` and the other validation docs listed in #1.
- **Memory:** `/Users/Suraj/.claude/projects/-Users-Suraj-cineglobe-frametax/memory/` holds `workspace-ui-finish-locked.md` + `MEMORY.md` (decisions only up to `b6ab849`).

## 10. Work state
| Item | Status | Version / location | Notes |
|---|---|---|---|
| Optimizer accounting, package policy, retention, suppressed UI | READY_FOR_CODEX_ACCEPTANCE | `611fb72`, engine 1.105.0 | |
| Location capability census/remediation | READY_FOR_CODEX_ACCEPTANCE | `36844e6`, 826/90/224 | |
| Workspace/hero/sidebar finish | IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION | `1d53099`→`b6ab849` | checked by Claude in own browser on FVD/LU/BH/LLS (some only FVD) |
| Overview four-slot + shared well | IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION | `f6839a9`, `b6ab849` | |
| Location control wiring (13/13) + precise wording | IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION | `ba8cfb0`, Ledger Item 10 | Globe canvas checked via data adapter only |
| Economic card interior v2 + MFNI placeholder | IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION | `9a69ef6`, Ledger Item 11 | |
| MFNI field + assumptions editor | not started | — | next MFNI task |
| Recently Viewed Files sidebar item | on hold | — | |
| Company Globe / Project Library / Project Globe colour-atmosphere pass | not started / frozen | — | |
| Build Your Own; real executable co-pro example; budget reparse policy; new-project ingestion | DEFERRED_PRODUCT_WORK / INGESTION_ACCEPTANCE_REQUIRED | — | |
| `PROJECT_RULES.md` edit (VISUAL-REVIEW EFFICIENCY AND AGENT ROLE SPLIT) | uncommitted, not Claude's | `frametax2/PROJECT_RULES.md` | leave untouched |

## 11. Next steps
1. **Next action:** wait for the user's next pasted task; if none, offer: (a) real hover/click verification of the Project Globe canvas on the four productions, (b) the MFNI task (serve an MFNI adjustment, turn the reserved rows into `MFNI ADJUSTMENT −$X` / `NPC AFTER MFNI $Y`, add an assumptions editor), or (c) Bad Hombres artwork.
2. Keep every new UI change inside the locked finish (section 6) and report only `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` or `BLOCKED`.
3. Await Codex acceptance results and fix only the exact defects reported.

## 12. Open questions ⚠️
- "Recently Viewed Files": add as a disabled "coming soon" item, or link it to something that exists (e.g. the last-opened project's Documents)? (currently on hold)
- Natural Earth range-only mountain cells (11, e.g. UY, BE): keep as supported, or make unresolved? (keep — current / make unresolved; never answered)
- Overview card height grew from ~360px to ~430–450px because the mandatory MFNI and attainability rows cannot fit the old height at 190px: accept, or allow a different Overview layout? (accept — current / change layout)
- Should Workspace/Overview badges for a confirmed mismatch use the existing "LOW-LOCATION-FIT REFERENCE" or the "Not Suitable" wording? (keep existing — current / rename)
- Who owns the uncommitted `PROJECT_RULES.md` edit and when should it be committed?

## 13. Re-attach checklist
- Nothing to attach (everything is in the repo at the paths above).

---
<sub>Audit: 13/13 sections · 21 rules · 13 corrections · 80+ data points · secrets removed: yes (DB password) · generated by active-memory</sub>


## Project Globe closeout (2026-10-08)
Commits `2a3d71d` and the follow-up: status colours, selected-structure routes, concise hover, stage/ocean/atmosphere depth, Data Incomplete outline. See CAPABILITY_LEDGER Item 12. Company Globe still deferred.

**Reversion:** ocean/atmosphere back to the 9a69ef6 look (stage bloom kept); Data Incomplete fill #6f7d8c, outline #a5b0bc. See ledger Item 12.

**Company Globe direct-load:** scene built by lib/companyScene.js from the single portfolio payload; territories painted; autoHeight. See ledger Item 13.
