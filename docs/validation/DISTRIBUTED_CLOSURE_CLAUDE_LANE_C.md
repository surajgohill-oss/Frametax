# Distributed Closure — Claude Lane C

Date: 2026-08-11
Lane: Asia, Africa, Middle East, multinational/regional programs, and multilateral/cross-region treaty
queues not naturally anchored in Lane A (Americas + Oceania) or Lane B (Europe).
Companion files: `DISTRIBUTED_CLOSURE_CLAUDE_LANE_C_OWNERSHIP.json`, `DISTRIBUTED_CLOSURE_CLAUDE_LANE_C.json`

## Ownership accounting

- lane_existing_start: 55
- lane_missing_start: 0
- lane_treaty_start: 1
- **lane_total_start: 56**

## Closure accounting

- lane_existing_closed: 32 (24 AUTHORITY_CLOSED + 6 NO_CURRENT_PRODUCER_INCENTIVE_CONFIRMED + 2 DUPLICATE)
- lane_existing_remaining: 23 (GENUINELY_UNRESOLVED)
- lane_missing_closed: 0
- lane_missing_remaining: 0
- lane_treaty_closed: 1 (IBERMEDIA_MEMBERSHIP_AND_FRAMEWORK — AUTHORITY_CLOSED)
- lane_treaty_remaining: 0
- **lane_total_closed: 33**
- **lane_total_remaining: 23**

Assertion: 33 + 23 = 56 == lane_total_start. ✓

## Final status distribution (56 identities)

| Final status | Count |
|---|---:|
| AUTHORITY_CLOSED | 25 |
| NO_CURRENT_PRODUCER_INCENTIVE_CONFIRMED | 6 |
| DUPLICATE | 2 |
| GENUINELY_UNRESOLVED | 23 |
| **Total** | **56** |

## Notable material findings

- **Saudi Arabia**: rate raised to up to 60% (from 40%), announced Cannes May 2026 — a material, current correction.
- **Qatar**: the incentive landscape actually comprises TWO distinct active programs — the DFI Grants Program
  (competitive, non-recoupable) and the brand-new Qatar Screen Production Incentive (QSPI, Nov 2025, up to 50%
  = 40% base + 10% uplift, administered by a different body, the Qatar Film Committee). If CineGlobe's stored
  record reflects the old 30% DFI-administered rate, it is stale.
- **Jordan**: cash rebate is a 25%–45% points-based BAND, not a flat rate — matches the discretionary-ceiling
  pattern already implemented for the MU/MT/GB pilot (commit `21af675`) and should be modeled the same way.
- **China**: NO national rebate exists for foreign productions — only city/regional rebates (e.g. Qingdao) and
  the CFCC official co-production pathway. If CineGlobe's stored record models a national rate, it is
  INCORRECT.
- **Indonesia**: NO national incentive for foreign productions; only a city-level (Jakarta), LOCAL-production-only
  rebate and a co-production matching-grant mechanism exist.
- **Nigeria, Ghana, Kenya**: each has an ANNOUNCED incentive rate (30%, 20%, 30% respectively) with credible
  evidence it is NOT yet operational/enacted — Nigeria's is the clearest (multiple sources explicitly confirm
  non-operational status), so it closes as NO_CURRENT_PRODUCER_INCENTIVE_CONFIRMED; Ghana and Kenya remain
  GENUINELY_UNRESOLVED given more ambiguous enactment evidence (flagged AUTHORITY_CONFLICT).
- Two identities MERGE as duplicates: Jordan's "Tourism Film Support" into the RFC cash rebate; Singapore's
  "SFC Production Assistance" into the IMDA fund ecosystem.

## Genuinely unresolved (23) — after reasonable primary-authority exhaustion

Every item below received at least one direct, good-faith primary-authority search this session. None were
declared unresolved without an attempt. Grouped by why they remain open:

**No evidence of any program located** (pure data gap — cannot confirm OR deny): Angola (ao_film_incentive),
Bangladesh (bd_film_incentive), Botswana (bw_film_commission), Cambodia (kh_film_incentive), Cameroon
(cm_film_incentive), Ethiopia (et_film_commission), Gabon (ga_film_incentive), Maldives (mv_film_incentive),
Mozambique (mz_film_incentive), Namibia (na_film_commission), Russia (ru_film_incentive), Senegal
(sn_film_incentive), Seychelles (sc_film_incentive), Tanzania (tz_film_incentive), Zambia (zm_film_commission),
Zimbabwe (zw_film_commission).

**Real program confirmed to exist, but exact rate/mechanism unconfirmed**: Uganda (ug_film_commission — a
real rebate mechanism is described but no percentage found); Vietnam (vn_film_incentive — a statutory tax-
incentive entitlement is legislated, but the implementing rate/formula is still described as unclear even in
current secondary coverage).

**Directly conflicting sources** (AUTHORITY_CONFLICT): Ghana (gh_film_incentive — 20% announced Feb 2024 vs.
later sources stating no formal program is operative); Kenya (ke_film_incentive — 30% given initial approval
in 2020, current enactment status unconfirmed); Kazakhstan (kz_film_incentive — one source says 30%
case-by-case, another says no incentive exists at all); Sri Lanka (lk_film_incentive — one source says no
incentives exist, another says a rebate is offered); Pakistan (pk_pfc_rebate — confirmed duty exemptions and
a grant fund exist, but no percentage rebate was corroborated despite CineGlobe's stored program name implying
one).

## What this does NOT include

Per this task's exact ownership boundary, the following remain explicitly unclaimed by Lane C (see
`DISTRIBUTED_CLOSURE_CLAUDE_LANE_C_OWNERSHIP.json.explicit_gaps_not_claimed_by_lane_c` for full reasoning):
Fiji (existing program); AUSTRALIA_PARTNER_LIST_RECONCILIATION and CANADA_PARTNER_LIST_RECONCILIATION (treaty
queues, naturally Lane A geography); UK_BILATERAL_AND_CONVENTION_RECONCILIATION,
FRANCE_BILATERAL_LIST_RECONCILIATION, EUROPEAN_CONVENTION_PARTICIPANTS_AND_VERSIONS, and
EURIMAGES_MEMBERSHIP_AND_ELIGIBILITY (treaty queues, naturally Lane B/European geography).

## No implementation

No CineGlobe program data, rules, schema, optimizer, calculators, treaty engine, candidate generation,
NPC/ranking, Bridge, Script Analyzer, UI, or tests were modified. This is a research-only closure pass.
