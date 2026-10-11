# LLS Manitoba–California hybrid: independent reconstruction (2026-10-11, corrected after Codex review of de053f69)

Status: IMPLEMENTATION EVIDENCE for LLS-CA-01; not a fresh Lips Like Sugar evaluation and not served acceptance. No revised served NPC is claimed. No real production was evaluated, no database row was written, nothing was regenerated, no server was touched. Retained inputs were read read-only (5-second statement timeout) from the acceptance database: the 46 active budget lines of ab10b319-978e-44d3-9331-af2a5f2cccc2 and saved row 51680824-eb85-4920-b124-04d0b6fce131 (canonical-1.110.0). Executable form: `backend/tests/test_california_project_gate_controls.py` (18 passed).

## Retained inputs
Gross 11,983,654.00. Saved row: Manitoba principal 11,943,654.00 (floor 4,249,644.30), California VFX 40,000.00 (floor 14,000.00), total incentive 4,263,644.30, NPC 7,720,009.70 — arithmetically consistent, which proves nothing about eligibility.

## 1. California eligibility (CFC Program 4.0 Guidelines, Jan 1, 2026, II.A.1) — corrected evidence standard
Dollars do not establish shooting days. Spend branch: 40,000 / 11,983,654 = 0.334% (< 75%). Days branch: no days are stated for LLS; the modeled hybrid places ALL of its principal photography in Manitoba (an explicit modeled scenario), so the days branch fails for THAT MODELED SCENARIO (`PROJECT_ELIGIBILITY_GATE_FAILED`, "not met in this modeled scenario"). This is not a finding about an actual LLS shoot and not an inferred dollar ratio: a mixed or unmodeled shoot would be CONDITIONAL (no guaranteed floor), and a producer-stated share of days (`ca_principal_photography_days_in_california_pct`) overrides any modeled placement. Regime: the saved LLS facts carry a California allocation letter dated 2023-03-06 under Program 3.0 (`reserved_not_final_award`); the 4.0 gate is applied to this relocation scenario on the assumption of a new application after July 1, 2025. That regime assumption is unproven for LLS and is disclosed, not resolved.

## 2. Three distinct artifacts (never mixed)
| # | Artifact | What it is | Manitoba incentive | NPC |
|---|---|---|---|---|
| 1 | Retained hybrid (MB principal 11,943,654 + CA VFX 40,000) | REJECTED in the modeled scenario; not a priced valid candidate | — | none claimed |
| 2 | Same-allocation sensitivity (Manitoba leg on its own 11,943,654, California VFX earns 0) | Arithmetic sensitivity, not a candidate and not certified QPE | 30% × 9,443,654 = 2,833,096.20 | 11,983,654 − 2,833,096.20 = 9,150,557.80 |
| 3 | Relocated all-Manitoba alternative (the 40,000 VFX moved into Manitoba) | A different structure; its own relocation cost is not computed | 30% × 9,483,654 = 2,845,096.20 | 9,138,557.80 |
Artifacts 2 and 3 differ by exactly 30% × 40,000 = 12,000. Common assumptions: the cost-of-production credit (30%) exceeds the labour credit (45% × 2,935,298 = 1,320,884.10) so it is the planning figure; finance costs 1,700,000, the contingency line 400,000 and the residuals reserve 400,000 are outside the Manitoba base; in-Manitoba travel 60,561 is treated as eligible (excluding it lowers each figure by 18,168.30). The stale Manitoba floor (4,249,644.30) was 45% of the 9,443,654 all-spend base, not a labour base or the 30% base; against artifact 2 the stale total incentive is overstated by 1,430,548.10 (against artifact 3, 1,418,548.10).

## 3. Contingency: election versus QPE, reconciled
- **Saved election:** none exists. `contingency_expected_utilization_pct` is not stored for LLS in the acceptance database (its only stored election is Little Utopia's, 100%) or in the shared `frametax2` database. State NOT_STATED: planned cost = original gross 11,983,654.00 (unknown is neither 0% nor 100%). If an election was entered in the running session it has not been persisted to either database; none is assumed.
- **QPE versus planning cost are separate.** Manitoba has no program-specific contingency rule, so the 400,000 contingency line is excluded from Manitoba QPE under every election (the engine's Manitoba credit is 2,845,096.20 for NOT_STATED, 0%, 50% and 100% alike). The earlier reconstruction called the whole reserve "unspent"; that substituted an incurred-cost case for the planning case and is withdrawn.
- **Planning mechanism:** planned cost = gross − reserve × (1 − utilization), applied once to NPC (the reserve is the 400,000 contingency line; the 400,000 residuals reserve is a separate obligation and is not a planning reduction).
| Election | Planned cost | NPC, artifact 2 | NPC, artifact 3 |
|---|---|---|---|
| NOT_STATED (actual LLS state) | 11,983,654.00 | 9,150,557.80 | 9,138,557.80 |
| 0% deployed | 11,583,654.00 | 8,750,557.80 | 8,738,557.80 |
| 50% deployed | 11,783,654.00 | 8,950,557.80 | 8,938,557.80 |
| 100% deployed | 11,983,654.00 | 9,150,557.80 | 9,138,557.80 |
Independent arithmetic (gross − undeployed reserve − incentive) and the engine's `planned_cost_reduction_usd` path agree to the cent.

## Unresolved
Fresh served LLS NPC (needs authorized regeneration; none claimed); LLS's applicable California regime (3.0 allocation letter 2023-03-06 versus 4.0 for a relocation scenario); principal-photography days for any actual LLS shoot (stated by the producer, otherwise conditional); a persisted LLS contingency election (none found); the relocation cost of artifact 3; Manitoba payroll evidence (the residents/non-resident split) on the real budget; the remaining NA obligations in the register.
