# Codex Final Optimizer Independent Acceptance Audit

**Final gate: `OPTIMIZER_REMEDIATION_REQUIRED`**

## Frozen audit identity

- Audited source SHA: `705d368fefcff2f63928d627589ffc069fd1c6d5`
- Required ancestor: `12a0b7060c2fbb07622f65f24fbfd99c4348425e` (confirmed)
- Engine: `canonical-1.64.0`
- Audit database: isolated clone `codex_final_optimizer_audit_20260916`; production database not modified
- Acceptance corpus: Little Utopia, F#K Valentine's Day, Bad Hombres, Lips Like Sugar only
- V-BRAT / Underwater evaluation rows created by final batch: **0 / 0**

## Executive result

The optimizer is not acceptable at this SHA. Two P0 rate-selection defects produce 18 failed independent calculation rows, with a maximum absolute NPC variance of **$988,365.40**. Five of six named stack rules whose two members are executable are absent from fresh four-production candidate generation. Project-scoped residency and official co-production contribution/entity inputs are not fully persisted from the production UI. These are current implementation defects, not reopened historical findings.

The four fresh evaluations persisted **1,191** rows: LU 269, FVD 327, Bad Hombres 267, Lips Like Sugar 328. Persisted NPC arithmetic itself is internally exact (`gross budget - persisted selected incentive`) for all **634** priced rows; the P0 errors are upstream selection of an unsupported incentive amount.

## Program reconciliation

- Canonical executable rate-bearing slugs: **126** (all represented once in `CODEX_EXECUTABLE_PROGRAM_RECONCILIATION.csv`)
- Canonical authority-coverage records observed in repository: **143**
- Runtime disposition totals: `GENUINELY_SELECTIVE_OR_NEGOTIATED` 4, `GENUINE_SCOPE_MISMATCH` 4, `IMPLEMENTATION_DEFECT` 19, `INACTIVE_SUPERSEDED_OR_DUPLICATE` 1, `PRICED_RUNTIME_VERIFIED` 61, `REJECTED_REAL_CULTURAL_TEST` 13, `REJECTED_REAL_SPEND_OR_QPE` 24
- Exact disputed handoff set: **32/32**, unique
- Unresolved after official-source research: **4** — Egypt EMPC, Ghana detailed mechanics, Panama complete threshold/formula, Uruguay ACAU feature-production formula
- Formulaic amount-gated controls: `au_location_offset`, `ca_bc_dave`, `ma_ccm_rebate`, `th_film_incentive` inspected as executable controls; `us_or_opif`, `za_nfvf_rebate`, `cz_film_incentive_animation`, and `nl_film_production_incentive` also traced.

## Input wiring

The budget, production type, home jurisdiction, production locations, nationality, confirmed attachments, labor/QPE facts, application disclosures, incentive references and currency normalization reach evaluation and served traces. Material gaps:

1. Residency edits use a legacy endpoint; the project-scoped endpoint does not persist residency.
2. Several creative slot roles are legacy/in-memory rather than consistently durable `ProjectPerson` state.
3. Official co-production contribution shares and co-producer/company entities lack a complete canonical UI-to-persistence path.
4. Related-party/vendor facts lack complete normalized fingerprint coverage.

Little Utopia's GB writer and AU director are both confirmed and the AU–UK treaty personnel gate correctly reports `QUALIFIES`; its treaty candidate remains conditional only because contribution/cultural-share facts are missing. That partial behavior is correct, but the missing durable fact-entry path prevents acceptance.

## Stacking universe

- Named program-pair rules: **229**
- Pairs with both members executable: **6**
- Generated in fresh real-project universes: **1**
- Missing: **5**
- Generated: `on_ofttc + on_opstc` (precisely rejected as mutually exclusive)
- Missing: `ca_bc_pstc + ca_federal_cptc`, `ca_federal_cptc + on_ofttc`, `ca_federal_cptc + on_opstc`, `ie_section_481 + uk_avec`, `ny_state_film + us_ny_post_production_credit`

The matrix distinguishes allowed, spend-reduction, same-cost prohibition and mutually exclusive rules. No compatible-pair completeness claim is made from row count alone.

## Independent calculation oracle

- Priced rows checked: **634**
- Passed: **616**
- Failed: **18**
- Maximum absolute variance: **$988,365.40**
- Internal NPC identity passed: **634/634**

`fr_trip` incorrectly synthesizes the VFX-specific amount fact from whole French QPE and selects 40% instead of 30%. Latvia guarantees an unresolved 30% ceiling instead of its independently supportable 20% floor. The exact 18 affected structures and dollar deltas are in the oracle CSV.

## Structure-family completeness

Real-project rows prove anchor, full relocation, ordinary component relocation, treaty, formulaic-program, conditional-upside and rejection-accounting families. One Ontario same-jurisdiction multi-program row is generated per production. **No `combined_coproduction_component_stack` row is generated for any acceptance production**, and five executable registered pair combinations are absent. Therefore structure-family completeness fails.

## Four fresh evaluations

| Production | Fingerprint | Candidates | Priced | Anchor incentive | Anchor NPC | Recommended |
|---|---|---:|---:|---:|---:|---|
| Little Utopia | `2fd543c968b5efae66e365b3ab9d07e44b5067bb93f2c1d29ff4fa57a52d2184` | 269 | 136 | $573,059.70 | $3,791,333.30 | None; qualification authority unresolved |
| F#K Valentine's Day | `8f56b3ef034a95787fdfa8722a5d86b0e75c206f2dd1769ffe7a38201717e25b` | 327 | 174 | $1,445,659.84 | $3,072,027.16 | None; cultural fact required |
| Bad Hombres | `becb1348921ab376f1d72efc925d7332d9dc9832ee3e011e4d899465d2565ddb` | 267 | 134 | $596,910.25 | $1,885,112.75 | Anchor |
| Lips Like Sugar | `27bbef42d58b463eae287d4609df35f17178d8e820670f72205e7da6f02738c6` | 328 | 190 | $3,459,278.90 | $8,524,375.10 | Anchor |

All values above were re-read from persisted fresh results. Full IDs, family/status counts, program composition and qualification fields are in `CODEX_FOUR_PRODUCTION_FINAL_RESULTS.csv`.

## Tests and residue

- Bounded tests: **375 passed, 0 failed, 0 skipped, 0 timed out**
- Groups: stack/treaty 127; formulaic amount/program 122; input/view/creative 126
- Fixed hash seed and isolated audit DB used; no overlapping DB-backed batches
- Pre-final exact-four structures/results: **0 / 0** after removal of earlier audit-only rows
- Post-final exact-four structures/results: **1,191 / 1,191**, intentional final evidence in the isolated audit DB
- Unrelated/V-BRAT/Underwater rows from final batch: **0**

Passing tests do not override the independent oracle. Their failure to detect the P0 arithmetic defects and pair omissions is finding `P2-TEST-001`.

## Required remediation gate

Remediation is bounded to the findings CSV: stop aggregate-QPE synthesis of distinct named amount facts; fail Latvia's unresolved ceiling to the supported floor; generate/dispose every executable named pair; make residency and official co-production facts durably project-scoped; correct current QLD/Montenegro/Portugal/Illinois authority implementation; and add independent expected-value/set-equality tests. No production fix was made by this audit.
