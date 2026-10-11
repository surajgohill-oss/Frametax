# LLS Manitoba–California hybrid: independent reconstruction (2026-10-11)

Status: IMPLEMENTATION EVIDENCE for LLS-CA-01; not a fresh Lips Like Sugar evaluation and not served acceptance. No real production was evaluated, no database row was written, nothing was regenerated, no server was touched. Retained inputs were read once, read-only, with a 5-second statement timeout, from the acceptance database (budget lines of the active document of ab10b319-978e-44d3-9331-af2a5f2cccc2 and saved row 51680824-eb85-4920-b124-04d0b6fce131, canonical-1.110.0). Executable form: `backend/tests/test_california_project_gate_controls.py`.

## Retained inputs
46 active lines, gross 11,983,654.00 (category totals are in the test). Saved row: Manitoba principal 11,943,654.00 (floor 4,249,644.30), California VFX 40,000.00 (floor 14,000.00), total incentive 4,263,644.30, NPC 7,720,009.70. Arithmetic is consistent (gross − incentive = NPC; allocations conserve gross) and proves nothing about eligibility.

## 1. California eligibility (CFC Program 4.0 Guidelines, Jan 1, 2026, section II.A.1)
- Spend branch: 40,000 / 11,983,654 = 0.334% (< 75%).
- Principal-photography branch: every location-bound account (miscellaneous 2,385,314; fringes 1,346,714; set construction 808,296; transportation 547,205; production sound 87,067; crew labour 76,175) is routed to Manitoba, so California holds 0% (< 75%). Assumption: shooting days are proxied by the dollar share of those accounts; the producer can state the actual percentage (`ca_principal_photography_days_in_california_pct`), which replaces the proxy.
- Result: the gate fails, the California credit (14,000 floor / 18,000 ceiling) is not claimable, and the candidate is persisted RULE_REJECTED / PROJECT_ELIGIBILITY_GATE_FAILED. Regime assumption: allocation letter dated on or after July 1, 2025 (a prospective evaluation).

## 2. Manitoba allocated spend, incentive and NPC (hand reconstruction)
- Cost-of-salaries credit: 45% × labour 2,935,298 (producer, cast, writer, director, crew; fringes and the unclassified "miscellaneous" account excluded) = 1,320,884.10.
- Cost-of-production alternative: 30% × eligible 9,483,654 (gross − finance 1,700,000 − contingency 400,000 − residuals reserve 400,000; in-Manitoba travel 60,561 assumed eligible because the budget does not separate per diems and living expenses) = 2,845,096.20. Sensitivity excluding travel: 2,826,927.90 (−18,168.30).
- One credit is claimed, so the planning figure is 2,845,096.20; NPC = 11,983,654 − 2,845,096.20 = 9,138,557.80.
- The current engine, run DB-free on the same inputs as one all-Manitoba candidate, reproduces both figures to the cent.

## 3. Comparison with the stale saved row
| | Stale row (1.110.0) | Reconstruction / current engine |
|---|---|---|
| California credit | 14,000 floor | 0 (gate fails; candidate rejected) |
| Manitoba incentive | 4,249,644.30 (45% of a 9,443,654 all-spend base) | 2,845,096.20 |
| Total incentive | 4,263,644.30 | 2,845,096.20 (−1,418,548.10) |
| NPC | 7,720,009.70 | 9,138,557.80 (+1,418,548.10) |

The stale Manitoba floor is not the cost-of-salaries base (labour) nor the cost-of-production base (30%); it predates the 1.115.0 labour-base repair and the 1.117.0 election repair. The 1,418,548.10 gap is therefore Manitoba base error plus the failed California gate (14,000), not a California-only effect. A fresh served figure requires an authorized regeneration; none is claimed.

## Remaining North American calculation obligations (for Codex's next review)
1. Fresh LLS total not established (no regeneration authorized); the reconstruction covers only the Manitoba–California hybrid and the all-Manitoba baseline, not every NA alternative.
2. The Codex acceptance gate items not independently closed here: California claim type, minimums and cost subsets (including the VFX uplift tests), Manitoba resident-labour evidence and the non-resident limit on real LLS payroll, lawful inter-territory combination for every NA pair, assistance only where applicable, overlap, planned contingency applied once, and potential certainty across the retained NA rows.
3. Principal-photography days are a dollar proxy unless the producer states the share; no Overview/Inspector control for that fact (backend path only).
4. The slow `GET /state` load (evaluate_project awaited inside get_project_state, CPU-bound hybrid search) is a separate owner-diagnostic item; the bounded cardinality evidence (docs/validation/diagnostics/two_component_slowdown_20261011.txt) shows the evaluation is CPU-bound and about 251 s for a two-component budget; no change was made to the request path.
5. Quebec above-the-line residency and federal-assistance netting, New Brunswick current guidelines, Mexico's minimum-spend table, Massachusetts statute text, Illinois SB 1911 rates (see the register).
6. Served-data verification, stack/location toggles and producer UI stay at their gates.
