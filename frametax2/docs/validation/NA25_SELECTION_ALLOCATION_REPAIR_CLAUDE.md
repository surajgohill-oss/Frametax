# NA25 selection and allocation integrity repair (Claude)

Base: code `516136c3` (live checkout); remote tip `46cd3613` (docs-only difference: audit documents). Final: the commit that contains this file (SHA in the push record). Repository: `cineglobe-claude-global-optimizer-remediation`, branch `claude/global-optimizer-remediation`. Isolated database `frametax2_pytest`; no real production was opened, evaluated, regenerated, mutated or deleted.

## Changed files
| File | Change |
|---|---|
| `backend/app/services/canonical_production_view.py` | `_pinned` also pins the producer's pick (`Project.leading_structure_id`) when it is a served candidate of this generation |
| `backend/app/calculators/line_allocations.py` | `ALLOWED` key set and `_reject_unsupported_keys`; `validate` refuses unknown keys by name |
| `backend/app/services/ny_producer_facts.py` | `line_allocations` entries accept only `line_id` and `allocations` |
| `backend/tests/test_na25_selection_allocation_integrity_controls.py` | 13 controls (new) |
| `frontend/tests/producer-selection-served-page.test.mjs` | 2 controls (new) |

None of the three source modules is in `_SEMANTIC_PRICING_MODULES` (`canonical_runtime_attribution.py`), so the pricing source digest is unchanged: no production is staled by this change, no restart or regeneration is implied.

## Repair 1 - producer-selected structure remains served
- **Symptom.** A pick whose ordinary rank is beyond the first 100 candidates is stored and returned as `leading_structure_id` but is absent from the served page; Overview/Workspace (`activeStructure`) then silently show the baseline.
- **Root cause.** `_pinned` pinned only the canonical selected structure, the leading conditional structure and the baseline.
- **Repair.** Added the producer's pick, de-duplicated, placed after the existing pins, only when it is in this generation's served entries and ranking. An identity that no longer resolves keeps being disclosed by `leading_selection.unavailable` (unchanged) and nothing replaces it. Ranking, thresholds, selection contract and page limits are untouched.
- **Before (pre-fix tree at `516136c3`, same control file):** `test_the_producer_selection_beyond_the_first_page_is_served_and_nothing_else_changes` failed at `assert str(pick) in ids` ("the selected structure is in the served first page"); `served leading id == pick` held, the pick was absent from the page.
- **After:** passes (4.3 s). Asserted in one fixture of 169 candidates, pick at rank index 125: page limit 100 unchanged and total 169 unchanged; every other entry keeps its position (`ids` minus the pick equals the earlier page prefix); pick inside the first five entries; served identity equals stored identity (`selection_identity` of the served structure equals `Project.leading_selection_identity`); pagination returns every candidate exactly once and the pick inside page one; a pick equal to the baseline is not duplicated; an unresolvable identity serves `{user_selected: true, unavailable: true}`, pins nothing and leaves the page equal to the unselected page; another project holding a pointer to this project's structure pins nothing and serves nothing foreign.
- **Browser -> response -> identity** (isolated stack: backend :8011 and Vite :5174 on `frametax2_pytest`, committed synthetic Missouri-home project with a Montana-only pick at rank index 125 of 169; stack stopped and the fixture deleted afterwards). `GET .../state`: `production.leading_structure_id = f88736c9-...` = the stored pick, `leading_selection = {user_selected: true, unavailable: false}`, pick present at index 2 of the 100-entry page (`candidates_page` 100/169). On a cold load of `/overview` and of `/workspace` the app's leading-selection store resolved `structure_id f88736c9-...`, `source: "user"`, `programs: ["us_mt_media_act_tax_credit"]`, equal to the response. This also answers why Montana could not be selected earlier on a Missouri-home fixture: the pick was outside the served page.
- Frontend controls (2): a served pick resolves as `user` through `activeStructure` / `resolveLeadingStructure`; a pick not served is never labelled `user` (resolves to the baseline).
- **Not done / limits.** `activeStructure` still falls back to the baseline when a leading id is absent from the page (now only reachable for an unavailable identity, which is disclosed by `leading_selection`); no UI banner was added (no redesign).

## Repair 2 - allocations never silently discard fields
- **Symptom.** An allocation carrying `canadian_status`, `service_location` or any unknown key was accepted and the key silently dropped.
- **Root cause.** `validate` copied only `PERSON_FIELDS` and ignored the rest.
- **Repair.** Keys outside `{payee_id, amount_usd, evidence} + PERSON_FIELDS` raise `ValueError` naming the keys and the line. Line-level Canadian fact names additionally say they are read per budget line, that Canadian labour eligibility is not computed per person, and to enter residents and non-residents as separate budget lines in the source budget (the app has no line-split editor). Non-object people and extra keys on a `line_allocations` entry are refused. API and internal callers share this single path (`write_ny_program_facts`); the API maps it to HTTP 422 with rollback. All validation precedes the first write.
- **Before (pre-fix tree):** 11 of the 12 DB-free/writer controls failed (unknown keys accepted); the save/reload control passed.
- **After:** 13 of 13 pass. Zero partial writes: a request with a valid line fact plus one allocation with `service_location` raises, leaves every `project_facts` row byte-identical and creates no structure; an entry with an extra row key is refused with the same result. Supported payloads (every `PERSON_FIELDS` member and evidence) validate and read back unchanged; a two-person Montana allocation (resident and non-resident, withheld true/false) survives save, expire and cold reload unchanged, and a Canadian status stays a line fact.
- **Montana / Nova Scotia non-regression:** `test_na_line_allocations_controls.py`, `test_na_fact_parity_controls.py`, `test_na_line_inputs_controls.py`, `test_leading_selection.py`: 49 passed (the only failures in that run were the 6 anchor-corpus controls noted below); the Montana and Nova Scotia one- and two-person results asserted there are unchanged.
- **Persisted payload audit (read-only SELECT on `project_facts`, read-only transactions):** `line_fact:%:allocations` rows = 0 in every `frametax2*` database (7 databases, including the acceptance database). No payload exists, so nothing is unsupported and nothing was rewritten.

## Canadian mixed-payee economics: OPEN
Per-person Canadian eligibility has no pricing consumer. The labour basis reads role, status, service location, payment status, look-through wages, assistance and related-party per budget line only, so a mixed resident/non-resident line remains all-or-nothing. This repair only makes that limit explicit and refuses to pretend otherwise. A search found no in-app line-splitting workflow (only budget import), so lineage-preserving splitting could not be demonstrated; the operator has to split the lines in the source budget. The issue stays OPEN.

## Commands, results, durations (timeouts: 0)
| Command | Result | Time |
|---|---|---|
| `pytest tests/test_na25_selection_allocation_integrity_controls.py` (post-fix) | 13 passed | 4.8 s |
| same file on the pre-fix tree (allocation controls) | 11 failed, 1 passed | 0.9 s |
| same file on the pre-fix tree (selection control) | 1 failed (page absence) | 3.4 s |
| `pytest` allocations, parity, line-inputs, leading-selection, canonical-selection (accidental inclusion of anchor corpus file) | 49 passed, 6 failed | 2.5 s |
| the 6 failures | `tests/test_canonical_selection_consistency.py` locked-corpus controls: "project not found by id" - real anchors are absent from `frametax2_pytest`; not run as acceptance, not caused by this change | - |
| 8 served-view and allocation files, post-fix vs pre-fix | 41 failed / 80 passed in both; failing sets identical (anchor-corpus fixtures absent) | 2.3 s / 4.3 s |
| `node --test tests/*.test.mjs` | 514 passed, 0 failed | - |

Every DB command ran in a bounded foreground process; none timed out. The 41 identical failures are inherited anchor-dependent controls, not passes; this task did not run, and does not claim, the 214 real-anchor controls.

## Real anchors and unrelated work
No anchor id appears in any write; no anchor was opened, evaluated, regenerated, mutated or deleted; the only committed synthetic row (browser fixture) was removed and `frametax2_pytest` again holds only its pre-existing "The Little Utopia" row (not an anchor id). The audit reads were SELECT-only on `project_facts`. Live checkout edits to `PROJECT_RULES.md`, `CAPABILITY_LEDGER.md` and the issue register, and all untracked files, were not touched, staged or committed. The live checkout needs `git pull` (remote is two documentation commits ahead; the issue register differs from the remote's copy and holds the user's uncommitted edit).

## Remaining obligations (unchanged scope)
- The two defects found by the ledger recheck are NOT fixed here and remain OPEN: `per_payee_limits.apply_payee_cap` over-excludes on partial allocations (GA/CO/NJ/AR/IL), and saving allocations deletes the line's `payee_type` (flips a foreign corporation's pay into Canadian qualified labour).
- Per-person Canadian labour facts, locality sources, PSTC labour share, Montana `(13)(b)(vi)`, New Brunswick portal-only worksheets, discretionary approvals, BC documentaries / pre-2016 photography, pre-NA-16 producer-fact controls: as listed in the ledger.
- The 214 real-anchor controls and independent UI verification are the separately authorized acceptance package.
