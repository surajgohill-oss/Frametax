# Global Data Application — Closeout

Date: 2026-08-13
Branch: `claude/audit-frametax-features-NZcX5`
Starting HEAD: `fdd62d9`
Starting gate: `GO_FOR_GLOBAL_DATA_APPLICATION`
Canonical input: `docs/validation/GLOBAL_REMEDIATION_EXECUTABLE_DATA.json` (176 records)
Companion artifact: `GLOBAL_DATA_APPLICATION_VERIFICATION.json`

## What this phase was for

The Little Utopia acceptance run correctly stopped at its entry gate: the completed canonical data existed but had never been applied to the served runtime. Its own scope line said so — *"No production code, runtime rule table, optimizer, UI, or project data was changed."* This phase applies it.

## Canonical 176 — full accounting

| Disposition | Count | Applied | Remaining |
|---|---:|---:|---:|
| IMPLEMENTATION_READY | 38 | 35 applied, 3 stopped | 0 unaccounted |
| RECLASSIFIED_UNPRICEABLE_AUTHORITY_INSUFFICIENT | 134 | 134 | 0 |
| RECLASSIFIED_NON_ECONOMIC | 1 | 1 | 0 |
| RECLASSIFIED_DUPLICATE | 1 | 1 | 0 |
| RECLASSIFIED_SUPERSEDED | 2 | 2 | 0 |
| TRUE_DATA_BLOCKER | 0 | — | — |
| **Total** | **176** | | |

`38 + 134 + 1 + 1 + 2 = 176`. Every canonical id is present exactly once; none was dropped or double-counted.

## The 38 implementation-ready records, by their own canonical action

The payload does not treat all 38 as deterministic rate programs, and neither does this implementation:

- **23 `ENCODE_SELECTIVE_ZERO_GUARANTEED`** — competitive grants, funds and calls. Applied as `NON_GUARANTEED_SELECTIVE`: guaranteed optimizer value is **zero**, exactly per the canonical rule that a selective award is not a guaranteed rate. Several carry a headline rate (Israel 30%, Korea 30%, Turkey 30%, Jordan up to 45%); none of those price.
- **6 `UPDATE_TREATY_DATA`** — structural. Applied with no economics, preserving the *treaty exists* / *valid co-production structure* / *domestic incentive eligibility* separation.
- **9 `CORRECT_DATA` / `ADD_PROGRAM`** — the only genuinely deterministic rate programs. **6 reach the runtime**; **3 are stopped**, see below.

## The identity problem, and the largest defect found

The canonical corpus identifies programs by its own `canonical_id`, which is frequently a **different spelling of an existing runtime `program_slug`**. Only `us_ny_film_credit` matched exactly.

This is also what made the entry check's "22 programs still pricing" an **undercount**. That comparison could only catch canonical ids that happened to match a runtime slug verbatim. Programs whose runtime spelling differed escaped entirely — including **Saudi Arabia at rank 2** (`sa_sfc_rebate` vs `sa_film_commission_rebate`), **Dubai DPIP at rank 8** (`ae_dpip` vs `ae_dxb_dpip`) and **BC PSTC at rank 10** (`bc_pstc` vs `ca_bc_pstc`). All three were pricing off programs the canonical corpus had already retired.

54 bindings were established: 43 by normalised program-name identity within the same jurisdiction, 11 by individual manual adjudication (abbreviation or agency-name variants such as *BC* vs *British Columbia*). **Both spellings are blocked**, so neither can price.

Three records could **not** be bound and are recorded as `CANONICAL_DATA_HANDOFF_DEFECT` rather than guessed:

| Canonical record | Why stopped |
|---|---|
| Film Incentive BC (FIBC) | The only CA-BC runtime program is the **Production Services Tax Credit** — a different, mutually exclusive statutory program (FIBC is Canadian-content). |
| German Motion Picture Fund (GMPF) | The only DE runtime program is **DFFF II**, which this same pass disables as authority-insufficient. The remediation input itself says "add *distinct* GMPF". |
| NFDC International Co-production Development Fund | The India profile carries `program_slug=None` — there is no identity to bind to. |

Binding a rate to a demonstrably different program would have been a correctness defect. `program_slug_aliases.py` already states the governing discipline: *"It never invents an equivalence."*

## How exclusion is enforced

`app/data/authority_coverage_registry.py` grew from 29 rows to **247**, and is now **deterministic runtime behaviour, not metadata**. It is consulted at two seams:

1. `production_discovery.py` STAGE 2 — a covered program never becomes `incentive_ready`, so it cannot enter optimization.
2. `allocation_pricing.price_segment()` — the **authoritative** block, checked *before* doctrine and rate resolution. This is what makes the guarantee total: a blocked program cannot price even from a directly-specified `StructureSpec` that bypasses discovery, and even though 19 of them still hold live `DoctrineRecord`s and `RateRule`s (deliberately retained for provenance and reactivation).

States: `PRICEABLE_VALIDATED` (the default for anything absent — so the registry can never silently suppress an unadjudicated program), `UNPRICEABLE_AUTHORITY_INSUFFICIENT` (211), `NON_GUARANTEED_SELECTIVE` (24), `NON_ECONOMIC` (5), `SUPERSEDED` (3), `DUPLICATE` (1), `CANONICAL_DATA_HANDOFF_DEFECT` (3), plus `NO_CURRENT_INCENTIVE` reserved so that distinction is never collapsed into "authority insufficient".

## Material consequences

- Executable jurisdiction profiles: **110 → 33 still priceable**.
- Little Utopia priced structures: **149 → 50** (177 generated, unchanged).
- **Ireland, UK, France, Italy, Spain, Germany, Belgium, Czech, Hungary, Croatia, Cyprus, Austria, Norway, Morocco, California, Georgia, Louisiana, New Mexico, Oregon, Texas and Canada federal/BC/Quebec** are all now authority-insufficient and no longer price. This is a large, deliberate contraction — the canonical corpus disabled them rather than let them inherit stale stored rates.
- The **Mauritius / Malta / Greece / Australia** calibration is untouched: none of those four is among the 176. Only `uk_avec` of the five calibrated anchors was reclassified, and its canonical record carries `rate_literals: []`.
- MU baseline NPC is **byte-identical at $3,057,794.90**, rank-1 unchanged.

## Verification

11/11 runtime checks RUNTIME VERIFIED (detail and evidence in the verification JSON). All three forbidden intersections are empty: accepted-for-optimization ∩ blocked = 0; priced segments ∩ blocked = 0; ranked economic candidates ∩ blocked = 0.

Full backend suite: **4019 passed, 1 skipped, 1 pre-existing unrelated failure** (a frontend `Workspace.jsx` title-formatter guard on a file with zero local diff). 19 new tests added; 6 existing tests updated to encode the new canonical behaviour — each rewritten to preserve its original invariant rather than weakened (the UK band-ceiling and QPE-cap mechanisms, for example, remain covered by the Mauritius, Malta and Greece tests).

## Remaining blockers

- **P1** — the 3 `CANONICAL_DATA_HANDOFF_DEFECT` records. Needs a canonical identity binding (a new runtime program record), not new research. Fails safe: understates benefit, corrupts nothing.
- **P2** — residual canonical↔runtime identity ambiguity in a small named set (Denmark DFI support vs production rebate, Portugal IAPMEI vs SCRI.PT, Panama and Costa Rica facilitation vs rebate, Mexico EFICINE vs the 2026 federal incentive, Thailand PRD digital-content vs BOI). These could not be adjudicated from the payload without inventing an equivalence. None is in Little Utopia's ranked set above rank 10.

Neither is a P0 deterministic correctness defect.

## Gate

**`GO_FOR_LITTLE_UTOPIA_WORLDWIDE`**

No winner is declared and no acceptance is claimed here — Little Utopia was used only as a contamination smoke check, as this phase requires.
