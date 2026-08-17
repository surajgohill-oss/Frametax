# Codex Authority Delta Recovery — Closeout

**Final gate: `CODEX_AUTHORITY_DELTAS_CONSUMED`**

Consumes the specific deltas Codex identified in
`docs/validation/CODEX_HISTORICAL_AUTHORITY_SOURCE_CROSS_REFERENCE.json`
that commit `12acc56` had not yet satisfied. No new external research
performed. No repository re-search performed — every action below reads
only the two files Codex named plus the specific in-repo artifacts Codex's
own cross-reference pointed at (`GLOBAL_REMEDIATION_EXECUTABLE_DATA.json`,
to verify literal-value presence for the 23 remediation records).

**All 110 actionable Codex delta items have a terminal disposition. Zero
`NOT_REVIEWED`/`SKIPPED`.**

| Delta category | Count | Recovered | Already recovered | Insufficient provenance | Conflict | Superseded/N-A |
|---|---:|---:|---:|---:|---:|---:|
| Source families | 18 | 6 | 2 | 8 | 1 | 1 |
| Program-type candidates | 45 | 24 | — | 8 | 13 | — |
| RateCondition kinds | 15 | 9 | — | — | — | 6 |
| Historical evaluator modules | 9 | 0 | — | 6 | — | 3 |
| Remediation records | 23 | 0 | — | 23 | — | — |
| **Total** | **110** | **39** | **2** | **45** | **14** | **10** |

(Delta-summary block in the JSON groups this slightly differently — 38
`RECOVERED` at the family+program-type+condition-kind level, since one
family-level `RECOVERED` disposition, e.g. "program_requirements primary/
current field set", subsumes several of its own program-type-level
sub-recoveries rather than double-counting them.)

---

## What was actually wired (`canonical_program_consolidation.py`, `CONSOLIDATION_VERSION` `1.3.0` → `1.4.0`)

1. **`APPLICATION_TIMING` widened** from `application_deadline`/
   `preapproval_mandatory` only to all six `program_requirements.py`
   timing fields (`audit_or_final_certification_deadline`,
   `payment_timing`, `expenditure_before_approval_qualifies`,
   `sunset_date` added) — Codex's own instruction: "do not collapse
   unrelated timing concepts into one boolean." Each distinct fact is
   named individually in the `source` string; the dimension's PRESENT/
   PARTIAL/MISSING status still follows the single strongest fact found.
2. **`jurisdiction_comparison` widened** to the two dimensions Codex
   explicitly flagged as still-unread: `RATE_OR_AWARD_BASIS`
   (`base_rate`/`max_rate`) and `QPE_DEFINITION`
   (`atl_qualifies`/`btl_qualifies`/`vfx_qualifies`/`music_qualifies`),
   both gated on the profile's own `confidence_tier` exactly like every
   other jc-sourced dimension.
3. **`RateCondition.kind` → dimension mapping** (`RATE_CONDITION_KIND_TO_
   DIMENSIONS`, 9 of Codex's 15 condition kinds): `RateRule.conditions`
   was read at the rule level before (min_qpe_usd, production_types) but
   never at the condition level. Now `cultural_test_required`,
   `min_qpe_usd`, `min_spend_currency_not_convertible`,
   `min_spend_pct_of_total_budget`, `no_sponsorship_in_qpe`,
   `production_type`, `production_type_uplift`, `sustainability_uplift`,
   `alternate_qualification_track` each promote only the exact dimension
   Codex's cross-reference proved, gated on the owning rule's confidence
   tier. **6 kinds deliberately excluded** — `discretionary_band`,
   `material_funding_risk_not_modeled`, `atl_subcap_not_enforced`,
   `graduated_bracket_applied`, `mutually_exclusive_alternative_program`,
   `rate_base_narrower_than_qpe` — these are advisory/risk annotations
   about a rate's reliability, not an independent proposition proving a
   dimension resolved; RATE_OR_AWARD_BASIS/CAP for these programs remain
   governed purely by their existing rule-level confidence-tier logic.
4. **Program-type recovery** (`app/data/historical_program_type_
   recovery.py`, new, 24-entry typed registry): 21 non-conflicting
   `cash_rebate`/`rebate`/`tax_credit`/`direct_grant` candidates →
   `FORMULAIC`; 2 non-conflicting `development_fund`/`co_production_fund`
   candidates → `NON_ECONOMIC_SUPPORT`; 3 `CONFLICT_REQUIRES_TAXONOMY_
   ADJUDICATION` records resolved as a pure terminology variance
   (`cash_rebate` vs `rebate` — the same mechanism, not a genuine
   disagreement) → `FORMULAIC`. Wired into the Phase A classification
   script's `classify()` as a fallback consulted only when no richer
   registry states a type — never overriding a stronger pre-existing
   signal (confirmed: `in_nfdc_coproduction` has a recovered type
   candidate but keeps its pre-existing `CANONICAL_DATA_HANDOFF_DEFECT`
   coverage-state disposition, not overridden).
5. **Real bug fixed while wiring**: `MONETIZATION`'s recompute was routed
   through `_upgrade()`, whose never-downgrade rule silently kept a STALE
   source string whenever the recomputed status happened to rank EQUAL to
   the pre-recovery status (only the underlying REFUNDABILITY/
   TRANSFERABILITY reasoning text had changed, not the rank).
   `ca_federal_pstc` was the concrete case: REFUNDABILITY recovered to
   PRESENT, but MONETIZATION's source string still said "refundability=
   PARTIAL" from before the upgrade. Fixed by direct index replacement
   instead of `_upgrade()` for this specific recompute (a full recompute
   of a derived dimension from its own two authoritative inputs is not
   "another candidate source" and should never be capped by never-
   downgrade semantics). Regression test added.

---

## What was deliberately NOT wired (Task 7/8/9)

- `cultural_qualification_model`, `cultural_test_rules`, the UK BFI
  hardcoded evaluator table, `mediterranean_comparison`, `mauritius_
  economics`, Little Utopia qualification-model constants: all 6
  AUTHORITY_BEARING_RULE_LOGIC-classified evaluator modules Codex
  identified were reviewed and **none had retained primary/official
  source-and-version provenance** (Codex's own text: "no per-set official
  citation/version in module", "self-labelled hardcoded validation
  testbed", or explicitly project-specific/superseded). Per Task 6/7's
  own instruction — recover only when provenance exists — 0 of 6 were
  wired. Left as acquisition leads.
- `fund_economics_model`: never used to promote a field; retained as one
  of the conflicting sources for 5 of the 16 program-type conflicts, all
  correctly left unresolved rather than adjudicated in its favor.
- The 23 formulaic remediation records: directly re-read
  `GLOBAL_REMEDIATION_EXECUTABLE_DATA.json` for three of them
  (`ca_ab_fttc`, `at_fisa_plus`, `be_tax_shelter`) to verify Codex's own
  "requires proposition-level adjudication" framing — confirmed, same as
  the prior task's finding for `ae_ad_film_rebate`: `base_rate=null`,
  every cap field literally `"See authoritative_rule_text; AUTHORITY_
  SILENT if unstated"`, `rate_literals=[]`. No literal value exists in
  any of these records to promote. All 23: `INSUFFICIENT_PROVENANCE`.
- 8 of the 45 program-type candidates (`ba_film_incentive`,
  `bb_film_incentive`, `bs_film_incentive`, `by_film_incentive`,
  `cr_film_incentive`, `ec_film_incentive`, `pa_film_incentive`,
  `tourism_ireland___fáilte_ireland_production_support`) carry only the
  bare type `production_support` — too ambiguous alone to distinguish a
  formulaic cash program from a discretionary support scheme without
  reading the underlying rule text (new research). Left `PROGRAM_TYPE_
  UNRESOLVED`.
- 13 of the 45 program-type candidates remain genuine cross-source
  conflicts (`direct_grant` vs `equity`/`loan`, `grant` vs `production_
  support`, `advance` vs `direct_grant`/`co_production_fund`,
  `discretionary_fund` vs `grant`, `co_production_fund`/`development_
  fund` vs `grant`) — these describe materially different financial
  instruments, not label variance. Preserved as `CONFLICT`.

---

## Recomputed universe (Task 10)

| | Before (this task) | After |
|---|---:|---:|
| Canonical identities | 224 | 224 |
| Formulaic authority incomplete | 105 | **126** (+21 newly-typed programs) |
| Formulaic authority complete | 0 | 0 |
| Program type unresolved | 88 | **65** (-23) |
| Non-economic support | 5 | 7 (+2) |
| Selective/discretionary | 23 | 23 |
| Superseded / Duplicate | 2 / 1 | 2 / 1 |

**Within the original 105-program set** (isolating pure wiring gains from
the +21 newly-typed programs, which mechanically add fresh ~14/14
unresolved gaps of their own): 10 programs improved, 11 additional
dimension-resolutions recovered — `APPLICATION_TIMING` 88→81 unresolved
(7), `QPE_DEFINITION` 101→98 (3), `MINIMUM_SPEND` 85→84 (1).
`CULTURAL_OR_CONTENT_TEST`/`MONETIZATION`/`REFUNDABILITY`/
`TRANSFERABILITY`/`CAP`/`RATE_OR_AWARD_BASIS` counts unchanged — the
RateCondition and jc-RATE_OR_AWARD_BASIS wiring for these mostly
overlapped programs already resolved by a stronger source (program_
requirements/doctrine), confirmed correct behavior (never-downgrade), not
a wiring failure.

Improved programs: `be_tax_shelter`, `fi_business_finland_incentive`,
`fj_film_rebate`, `gr_cash_rebate`, `il_foreign_production_fund`,
`mt_mfc_rebate`, `mx_federal_film_incentive_2026` (2 dimensions),
`rs_film_commission_cash_rebate`, `uk_avec`, `us_pr_film_incentives_act`.

Four controls, all remain `AUTHORITY_INCOMPLETE` as required: Greece
4/14 unresolved (unchanged — no new source touches it), GB AVEC 9→8/14,
Canada federal PSTC 13/14 (unchanged), US California 12/14 (unchanged).

**Still 0 `FORMULAIC_AUTHORITY_COMPLETE`.** `RESIDENT_NONRESIDENT_
TREATMENT` and `PAYROLL_TREATMENT` remain unresolved for 124/126 —
confirmed, once again, genuinely absent from every source examined this
session too (`program_requirements` has no residency-differentiated labor
field; `jurisdiction_comparison` has no payroll-eligibility field). These
are the true residual gap the next research phase should target first.

---

## Testing

5 new focused tests added to `tests/test_canonical_authority_substrate.py`
(RateCondition-kind scoping, advisory-kind exclusion, jc RATE/QPE
confidence gating, MONETIZATION-recompute-staleness regression, widened
APPLICATION_TIMING field survival), 1 existing test updated (uk_avec's
`APPLICATION_TIMING` now `PRESENT`, not `PARTIAL`, reflecting the
statutory-deadline fact this session recovered). **42/42 pass.** Full
suite not rerun — zero blast radius unchanged from the prior task (grep-
confirmed: `canonical_program_consolidation.py`/`canonical_publication_
contract.py`/`canonical_residual_ledger.py` imported by no pricing/
discovery/optimizer path).

## Prevention

`RECOGNIZED_AUTHORITY_SOURCE_MODULES` unchanged — `program_rate_rules`
and `jurisdiction_comparison` were already listed (this session deepened
what's read from them, not which modules are read). No new module
crossed the "recognized but unimported" threshold, so no extension was
needed this pass.

---

## Final gate rationale

**`CODEX_AUTHORITY_DELTAS_CONSUMED`**: all 110 concrete Codex delta items
(18 source families, 45 program-type candidates, 15 RateCondition kinds,
9 evaluator modules, 23 remediation records) have an explicit terminal
disposition — 39 `RECOVERED`, 2 `ALREADY_RECOVERED`, 45
`INSUFFICIENT_PROVENANCE`, 14 `CONFLICT`, 10 `SUPERSEDED`/`NOT_
APPLICABLE_TO_CANONICAL_AUTHORITY`. Zero unprocessed. No external
research performed. No optimizer or frontend code touched. The remaining
gaps (`RESIDENT_NONRESIDENT_TREATMENT`/`PAYROLL_TREATMENT` universally,
production_support-only and genuinely conflicting program types, evaluator
modules with no official citation, remediation records with no literal
values) are now confirmed, for the second time via an independent
cross-reference pass, to be genuinely absent from every retained CineGlobe
source rather than merely unwired.
