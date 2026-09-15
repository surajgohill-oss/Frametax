# COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION

Workstream: `COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION`
Repository: `~/cineglobe-frametax` (worktree `/Users/Suraj/cineglobe-frametax-claude-remediation`)
Branch: `claude/audit-frametax-features-NZcX5`
Required starting HEAD: `7adaa4c1f6447cf1b1e27e4bff6b8f28e4443e92` (confirmed before any edit)

## Prior closeout (`7adaa4c1`): accepted narrowly, rejected broadly

The narrow correction in `7adaa4c1` (personnel-gate `NOT_APPLICABLE` labeling,
threading personnel facts into conditional pricing) was itself correct and
is retained unmodified. The broader claim that co-production wiring was
"closed out" is rejected by this workstream's own findings below — not
because the mechanism is broken, but because **the underlying treaty
registry data makes every one of the four real productions' own home
jurisdiction structurally unable to be a bilateral-treaty party at all.**
This is a real, pre-existing, disclosed data gap, not a code defect this or
any prior workstream introduced — but it was never previously surfaced or
proven, and it is the actual, complete answer to all four contradictions
this workstream was asked to resolve.

## The central finding (proven, not asserted)

```
te.get_bilateral_treaty('MU', 'GB')    -> None
te.get_bilateral_treaty('US', 'CA')    -> None
te.get_bilateral_treaty('US-NM', 'CA') -> None
te.get_bilateral_treaty('GR', 'FR')    -> None
any bilateral treaty keyed to MU: []
any bilateral treaty keyed to US (any US-* code): []
any bilateral treaty keyed to GR: []
total bilateral treaties in the registry: 26
```

**Mauritius (Little Utopia), Greece (F#K Valentine's Day), and the United
States (Bad Hombres, Lips Like Sugar — served under their state-level codes
`US-NM`/`US-CA`) are not a party to a single one of the 26 registered
bilateral co-production treaties.** This is real, pre-existing treaty-
registry data (`app/calculators/treaty_engine.py`'s `_BILATERAL` dict,
untouched by this workstream — confirmed via `git diff` showing zero lines
changed in the registry's own treaty entries), not a bug this workstream
introduced or is asked to fix (`SCOPE EXCLUSIONS: no new treaty-rule
population`).

**The direct consequence**: `evaluate_project()`'s home-anchored bilateral
loop (`find_real_bilateral_partners(home_code, candidate_codes)`, scoped to
treaties where `home_code` IS a party) produces **zero** opportunities for
all four productions. **Every single treaty_coproduction opportunity ever
served for any of these four productions — 100 of 100, across every
workstream this multi-month project has run — comes exclusively from the
NON-home-anchored loop**, which by its own explicit design
(`if home_code in (majority_code, minority_code): continue`) enumerates
real, registered bilateral treaties between two OTHER countries entirely,
completely independent of the project's own jurisdiction, nationality
facts, or location. Eurimages/European Convention/Ibermedia (multilateral)
opportunities ARE genuinely home-anchored (confirmed: Greece is a real
Eurimages member and European Convention signatory — `te.is_eurimages_
member('GR') == True`), but multilateral has no conditional-pricing
mechanism at all, so it can never progress past a bare registry disclosure.

This single fact fully and precisely explains all four contradictions in
the objective:

1. **"GB writer/AU director reach the evaluator but affect zero real
   treaty outcomes"** — because MU (Little Utopia's own jurisdiction) is
   party to zero real treaties, none of LU's 25 opportunities are even
   ABOUT Mauritius's own co-production potential. GB and AU do appear as
   parties in several of the 25 (GB in 8, AU in 6) — but those pairings
   (e.g. `GB+AU`, `AU+DE`) are globally-enumerated third-country treaty
   pairs, structurally disconnected from Little Utopia's own anchor. The
   personnel gate correctly processes the fact every time
   (`personnel_gate_state` is computed, never skipped) but resolves
   `NOT_APPLICABLE` because no real treaty anywhere has a researched
   personnel rule — this is `FACT_TRANSPORTED_NOT_RULE_CONSUMED` (Section
   B below), never "facts consumed."
2. **"All four productions return nearly identical treaty populations"**
   — because all four productions' opportunities come from the exact same
   mechanism: `find_bilateral_treaty_pairs_among_candidates(candidate_codes)`,
   which enumerates the SAME registry-wide set of real bilateral pairs,
   filtered only by each project's own worldwide `candidate_codes`
   discovery universe (itself driven mostly by which jurisdictions have
   ANY priced program at all — a largely project-independent set). None
   of these pairs are geographically tied to any of the four productions'
   own anchor jurisdiction.
3. **F#K Valentine's Day's multilateral `personnel_gate_state=None`** —
   fixed (Section D below): the three multilateral adapters never called
   the personnel gate at all before this workstream, leaving the
   dataclass default of `None`. Now genuinely computed, resolving
   `NOT_APPLICABLE` (never blocking, never a bare `None`).
4. **Little Utopia and F#K Valentine's Day have no `leading_structure_id`**
   — proven (Section D below) to be entirely unrelated to co-production:
   each production's own SINGLE-JURISDICTION baseline program has a
   genuinely unresolved cultural-test qualification state
   (`AUTHORITY_UNRESOLVED` for Mauritius's `mu_edb_incentive`,
   `USER_FACT_REQUIRED` for Greece's `gr_cash_rebate`) from real, dated,
   pre-existing research (2026-08-19), predating and unrelated to any
   co-production/personnel workstream. Bad Hombres and Lips Like Sugar's
   baseline programs have no cultural test at all (`NOT_APPLICABLE`,
   which correctly admits Recommended) and DO receive a real
   `leading_structure_id` pointing at their own baseline.

## A. Opportunity relevance — exact inclusion source and classification

A new, read-only, additive classification is now computed and served for
every treaty/co-production opportunity (`app/services/canonical_evaluation.py`,
`_classify_opportunity_relevance()`), using only fields the evaluation
already computes — no new eligibility math, no invented fact:

| Served field | Meaning |
|---|---|
| `opportunity_inclusion_source` | `home_anchored_bilateral_treaty_registry` \| `global_bilateral_treaty_registry_enumeration` \| `multilateral_membership_registry` |
| `project_anchored` | `True` only if the project's own home/service jurisdiction is a real party to this treaty/framework |
| `opportunity_relevance` | `AVAILABLE` \| `COMPATIBLE` \| `CONDITIONAL` \| `EXECUTABLE` \| `EXCLUDED` \| `AUTHORITY_OR_RULE_DATA_INCOMPLETE` |

Classification rule (exact, from `_classify_opportunity_relevance`'s own
docstring):
- `resolution_state == ELIGIBLE` (a real, evidenced contribution-share
  project fact cleared every threshold) → **EXECUTABLE**, regardless of
  anchoring — real facts are real facts. Does not currently occur for any
  real treaty on any of the four productions (none has an evidenced
  contribution-share fact on file).
- `resolution_state == INELIGIBLE` → **EXCLUDED**.
- `project_anchored is False` → **AVAILABLE**, unconditionally, **even
  when the conditional-pricing scenario internally reaches a modeled
  ELIGIBLE state** — the exact guard the objective required ("a globally
  enumerated treaty must not be presented as project-compatible merely
  because contribution shares can be assumed").
- `project_anchored is True` and the conditional scenario resolved a real
  priced structure from the treaty's own registered minimum contribution
  (a disclosed, producer-actionable `PROPOSED_CHANGE` assumption, never a
  verified fact) → **CONDITIONAL**.
- `project_anchored is True` and the conditional scenario failed for a
  data-completeness reason (no canonical rate rule, an unresolved
  same-jurisdiction stacking group) → **AUTHORITY_OR_RULE_DATA_INCOMPLETE**.
- Anything else while anchored (e.g. a real, unresolvable cultural-test
  fact) → **AVAILABLE**.

**Result, proven live against all four real productions (see the CSV for
the full table)**: **every one of the 100 real treaty_coproduction
opportunities across all four productions classifies `AVAILABLE`.** Zero
classify `CONDITIONAL`, `COMPATIBLE`, or `EXECUTABLE` — because zero of
them are home-anchored (Section: central finding, above). This is the
semantically correct, non-misleading result given the real registry data,
not a defect in the classifier — proven by
`test_classify_opportunity_relevance_labels_anchored_assumption_priced_scenario_conditional`,
which demonstrates the classifier DOES correctly return `CONDITIONAL` for
a synthetic home-anchored case; the real productions simply have none.

## B. Little Utopia — proven, fact by fact

- **Registered treaty/framework participants connected to GB or AU**: GB
  is a party in 8 of LU's 25 real opportunities (`uk-ie`, `uk-in`, `uk-ca`,
  `uk-au`, `uk-fr`, `uk-de`, `uk-nz`, `uk-za`); AU is a party in 6
  (`ca-au`, `au-de`, `au-ie`, `au-it`, `au-kr`, `uk-au`). None of these 14
  pairs includes MU. `te.get_bilateral_treaty('AU', 'GB')` **does**
  resolve a real registered treaty (`uk-au-bilateral`) — so a genuine
  GB–AU treaty exists in the registry, but it is not anchored at Little
  Utopia's own jurisdiction either; it is one of the 25 globally-
  enumerated `AVAILABLE` entries, same as the other 24.
- **Does the GB writer or AU director change discovery, compatibility,
  cultural qualification, or ranking anywhere?** No. Proven live: with the
  writer/director facts present exactly as stored, `personnel_gate_state`
  is `NOT_APPLICABLE` for all 25 opportunities (`personnel_facts_rule_
  consumed_count: 0` in the CSV) — the facts are genuinely fetched and
  genuinely threaded into every evaluator call (`role_attachment_facts_
  from_project` returns real, non-empty `GB`/`AU` data, confirmed by
  `test_little_utopia_gb_writer_and_au_director_are_transported_not_rule_
  consumed_for_every_real_treaty`), but change zero discovery counts, zero
  resolution states, zero cultural qualification results, and zero
  ranking outcomes, because no real treaty anywhere has a researched
  personnel rule to apply them to. **This is
  `FACT_TRANSPORTED_NOT_RULE_CONSUMED`.**
- **Is an AU–GB treaty registered?** Yes (`uk-au-bilateral`) — but it is
  not anchored at MU, so it is `AVAILABLE`, not project-compatible.
- **Why do the UK/France/Germany/Belgium cultural-test blockers appear?**
  `uk-fr-bilateral`, `fr-de-bilateral`, and `fr-be-bilateral` are three of
  the 25 globally-enumerated pairs; each requires an explicit cultural
  test this engine cannot solve numerically (`solve_bilateral_minimum_
  contribution`'s own `deterministically_solvable=False` branch). They are
  real, registered treaties (none involves MU), correctly disclosed with
  a `blocking_reason`, correctly classified `AVAILABLE` (not `EXCLUDED` —
  no fact has been confirmed FALSE, only unconfirmed).
- **Project-relevant or only globally available?** Only globally
  available — proven: zero of LU's 25 opportunities have `project_anchored
  == True`; the classifier never returns anything but `AVAILABLE` for
  them regardless of GB/AU personnel facts or assumed contribution shares.

## C. Conditional pricing safety

For the 22-of-25-per-production rows where the conditional-pricing
scenario (`_build_conditional_bilateral_scenario`, pre-existing) resolves
`CONDITIONAL_PROJECT_FACT_DEPENDENT`:
- **The treaty relationship exists**: confirmed via `te.get_bilateral_
  treaty(majority_code, minority_code) is not None` before any scenario is
  built (function returns `None` immediately otherwise).
- **Contribution ranges come from the registered treaty**: `solved.
  majority_pct`/`minority_pct` are `treaty.majority_min_pct`/`minority_
  min_pct` read directly off the real `TreatyData` row — never invented
  (proven by `test_missing_contribution_shares_default_to_a_priced_
  modeled_assumption_not_a_permanent_block` in the prior workstream, still
  passing).
- **Applicable incentive economics come from canonical programs**: priced
  through the identical `_price_candidate()` kernel every ordinary
  candidate uses (no separate co-pro pricing math).
- **Modeled assumptions are disclosed**: `assumption_fact_classification:
  "PROPOSED_CHANGE"` on every such scenario — the codebase's existing,
  pre-established "producer-actionable assumption, not verified fact"
  vocabulary entry.
- **No missing hard legal gate is silently treated as satisfied**: a
  required cultural test can never be "solved" (`deterministically_
  solvable=False` whenever `cultural_test_required`); a real, confirmed-
  wrong personnel fact is a genuine `HARD_FAIL`, folded into the scenario's
  own `NOT_FEASIBLE` status (proven:
  `test_explicit_locked_personnel_contradiction_blocks_the_conditional_
  scenario`, prior workstream, still passing).
- **It cannot become a verified recommendation while conditional**:
  structurally proven, not just asserted — every treaty_coproduction
  `StructureCalculationResult` row's OWN `total_incentive_value_usd`/
  `true_net_cost_usd` are `None` (the conditional number lives only inside
  the nested `conditional_scenario` dict); `top_pair`/`leading_structure_
  id` selection only ever reads `true_net_cost_usd is not None` rows
  (`priced`) or the project's own `is_baseline` row — a treaty_
  coproduction row is neither, by construction, on every real project
  (proven live: `test_no_treaty_coproduction_row_ever_carries_priced_
  economics_on_its_own_result_row`, checked against Little Utopia AND Bad
  Hombres).
- **This workstream's correction**: because none of these 22-per-
  production rows is home-anchored, `opportunity_relevance` now correctly
  reports `AVAILABLE` for all of them, not `CONDITIONAL` — retaining the
  priced modeling as a disclosed capability scenario, never presented as
  project-compatible, exactly as the objective required.

## D. Contract consistency

- **`personnel_gate_state` is never `None` merely because no rule
  exists.** Fixed: all three multilateral adapters
  (`evaluate_eurimages_coproduction_opportunity`,
  `evaluate_european_convention_coproduction_opportunity`,
  `evaluate_ibermedia_coproduction_opportunity`,
  `app/calculators/canonical_treaty_bridge.py`) now call the SAME
  `evaluate_treaty_personnel_gate()` the bilateral path already uses,
  reading the framework's own real `personnel_requirement` (`treaty_
  engine.get_multilateral_treaty()`, a new read-only accessor — no new
  doctrine, no invented requirement). Every real multilateral entry
  carries `personnel_requirement=None` today (same as every bilateral
  entry), so this resolves `QUAL_NOT_APPLICABLE`, never a bare `None`.
  Proven live for F#K Valentine's Day's real Eurimages/European
  Convention entries.
- **Little Utopia / F#K Valentine's Day `leading_structure_id`**: proven
  correct, not a defect. Each project's OWN baseline single-jurisdiction
  program has a genuine, real, pre-existing (2026-08-19 research)
  unresolved cultural-test qualification state
  (`AUTHORITY_UNRESOLVED`/`USER_FACT_REQUIRED`) — neither is in
  `_QUALIFICATION_ADMITS_RECOMMENDED = {QUALIFIES, NOT_APPLICABLE}`, so
  `top_pair` is correctly `None`, and `leading_structure_id` is correctly
  never set. Bad Hombres and Lips Like Sugar's baseline programs require
  no cultural test at all (`NOT_APPLICABLE`, which DOES admit
  Recommended) and correctly DO have a real `leading_structure_id`
  pointing at their own baseline, at their own frozen economics — proven
  live for both states (`test_bad_hombres_no_cultural_test_baseline_
  receives_a_real_leading_structure`,
  `test_little_utopia_and_fvd_baselines_are_genuinely_unresolved_not_a_
  ranking_defect`). No ranking/served-winner code change was needed or
  made.
- No conditional structure was, or can be, promoted into a verified
  winner (Section C above).

## E. Real runtime acceptance

See `docs/validation/FOUR_PROJECT_COPRO_RELEVANCE_CLAUDE.csv` for the full
per-production table (total opportunities, relevance-bucket counts,
inclusion-source counts, cultural blockers, personnel facts transported
vs. rule-consumed, priced-conditional count, leading structure or exact
reason none exists). All four evaluated fresh at `ENGINE_VERSION
canonical-1.59.0` (bumped from `1.58.0` to force every cached row through
the new multilateral personnel wiring and relevance classification).
Summary: 100 total treaty opportunities across the four productions, 100
`AVAILABLE`, 0 `CONDITIONAL`/`COMPATIBLE`/`EXECUTABLE`, 0 `EXCLUDED`, 12
cultural blockers (3 per production, all genuine), 0 personnel facts
rule-consumed anywhere, 2 of 4 productions have a real `leading_structure_
id` (Bad Hombres, Lips Like Sugar — both correct), 2 do not (Little
Utopia, F#K Valentine's Day — both correct, both proven, both unrelated to
co-production).

## Tests

New file `tests/test_copro_opportunity_relevance_claude.py` (16 tests, all
passing):
- global availability never mislabeled project-compatible (unit +
  live-DB proof against Little Utopia's real 25 opportunities);
- the classifier's positive control (a genuinely home-anchored synthetic
  case correctly returns `CONDITIONAL`) — proving the real productions'
  100% `AVAILABLE` result is a fact about the data, not a broken
  classifier;
- `FACT_TRANSPORTED_NOT_RULE_CONSUMED` proven both as a synthetic
  mechanism test and live against Little Utopia's real GB/AU facts;
- multilateral `personnel_gate_state` is `NOT_APPLICABLE`, never `None`
  (unit tests for all three frameworks, plus a live F#K Valentine's Day
  proof);
- conditional structures structurally cannot carry priced economics on
  their own result row, proven live for two real projects;
- a real, executable (no-cultural-test) baseline receives a real
  `leading_structure_id` (Bad Hombres, live);
- Little Utopia's and F#K Valentine's Day's missing `leading_structure_id`
  is proven to be their own baseline's genuine unresolved qualification
  state, not a ranking defect;
- Lips Like Sugar's two unconfirmed, nationality-NULL `ProjectPerson` rows
  are proven never credited anywhere in the real served view.

Regression: 286 passed / 0 failed / 0 timeout across the full 14-file
treaty/co-production/production-view batch (26.5s, foreground).

## What remains a genuine, disclosed gap (not fixed, out of scope)

- **No bilateral treaty in the registry lists Mauritius, Greece, or the
  United States as a party.** This is the root cause of the "near-
  identical populations" and "facts transported but never consumed"
  findings. Fixing it requires populating real, primary-source-cited
  bilateral treaty entries for these countries — genuine external
  research, explicitly out of scope (`SCOPE EXCLUSIONS: no external
  research, no new treaty-rule population`).
- **No real treaty (bilateral or multilateral) carries a researched
  `personnel_requirement`.** The mechanism to consume one is fully wired
  and proven (discovery, conditional pricing, and now multilateral too);
  populating one requires the same out-of-scope research.
- **Multilateral opportunities have no conditional-pricing mechanism at
  all** (unlike bilateral's `_build_conditional_bilateral_scenario`) — a
  real, disclosed limitation (`AVAILABLE`, never anything stronger),
  not addressed here (would be new optimizer logic, out of scope for a
  validation-only workstream).
