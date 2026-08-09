# Codex Global Validation Completion Plan

Date: 2026-08-09

## Purpose

Derived only from the completed 285-record Codex validation. No new jurisdiction research and no CineGlobe rule, optimizer, calculator or treaty data changes.

## Canonical handoff

- Repository root: `/Users/Suraj/cineglobe-frametax`
- Canonical directory: repo-root `docs/validation/`
- Completed validation: 262 existing + 23 missing discoveries = 285 records
- Arithmetic: 8 VERIFIED + 15 INCORRECT + 179 INCOMPLETE + 17 STALE + 43 UNRESOLVED = 262

The completed MD/JSON are preserved byte-for-byte at the root path; verified nested duplicates are removed.

## Complete vs incomplete

Complete: all 262 existing rows classified; 23 missing discoveries preserved; 38 treaties and 109 participants inventoried; existing findings and source dispositions preserved.

Incomplete: 254 existing rows need authority completion (15 INCORRECT, 179 INCOMPLETE, 17 STALE, 43 UNRESOLVED). Queue priorities are 167 P0, 25 P1, 62 P2.

## Priority counts

| Priority | Count | Meaning |
|---|---:|---|
| P0 | 167 | Blocks pricing/gating or candidate-universe integrity |
| P1 | 25 | Material NPC/ranking, conditional funds or major treaties |
| P2 | 62 | Secondary completeness/source work |

## Optimizer relevance — 262 existing rows

| Class | Count |
|---|---:|
| A. Economic incentive / optimizer candidate | 124 |
| B. Fund / grant / conditional financing | 87 |
| C. Treaty / co-production pathway program row | 0 |
| D. Non-economic / informational / obligation | 8 |
| E. Unclear — requires research | 43 |
| Total | 262 |

Treaties are separately inventoried; Class C counts only program rows.

## Issue-type counts

| Issue type | Records |
|---|---:|
| rule-data | 254 |
| territoriality | 254 |
| cap/threshold | 252 |
| source provenance | 252 |
| hard gate | 238 |
| QPE | 238 |
| rate/uplift | 213 |
| stacking | 197 |
| monetization | 110 |
| non-economic candidate contamination | 51 |
| treaty | 24 |

## Recommended research batches

1. **P0 (167)** — country-by-country INCORRECT/STALE economic candidates, then incomplete cash/tax programs; capture rates, uplifts, caps, gates, QPE, territoriality, monetization, stacking and dated primary sources. Resolve D/E rows as economic or excluded; never price E pending authority.
2. **P1 (25)** — competitive funds/grants with current call economics, recoupment, gates and windows; complete UK/Australia/Canada/France partner lists, then Convention/Eurimages/Ibermedia.
3. **P2 (62)** — remaining low-confidence fund/source records and other bilateral term refreshes.

## Treaty completion queue

| Queue | Priority | Stored in scope | Required next research |
|---|---|---:|---|
| UK_BILATERAL_AND_CONVENTION_RECONCILIATION | P0 | 11 | Reconcile current bilateral list and both Convention versions; capture texts, formats, contributions, authorities and dates. |
| AUSTRALIA_PARTNER_LIST_RECONCILIATION | P0 | 8 | Reconcile current treaties/MOUs, formats, contribution tests, approval timing and national-treatment consequences. |
| CANADA_PARTNER_LIST_RECONCILIATION | P0 | 13 | Diff complete current Telefilm treaty/MOU list; capture texts, authorities, contribution and nationality rules. |
| FRANCE_BILATERAL_LIST_RECONCILIATION | P0 | 8 | Diff CNC index; capture texts, versions, contributions, formats and national-treatment effects. |
| EUROPEAN_CONVENTION_PARTICIPANTS_AND_VERSIONS | P1 | 1 | Capture signatories/ratifications for CETS 147/220, compatibility, dates and film-only scope. |
| EURIMAGES_MEMBERSHIP_AND_ELIGIBILITY | P1 | 1 | Reconcile membership, contribution/points, rounds, recoupment and national-incentive interaction. |
| IBERMEDIA_MEMBERSHIP_AND_FRAMEWORK | P1 | 1 | Capture members, structures, contribution conditions, calls, caps, recoupment and interactions. |
| OTHER_STORED_BILATERAL_SOURCE_AND_TERM_REFRESH | P2 | 5 | Validate status, text, contributions, formats, nationality/creative tests, authority and timing. |

## Completion gate

A queue item closes only when current primary authority supports every listed canonical field with effective/version date and pinpoint support. Industry convention, local-SPV payment alone, or treaty existence alone is not authority. VERIFIED records remain outside the queue.

