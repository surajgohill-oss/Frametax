# Final Codex adjudication of AG's four-project calculation audit

Audit date: 2026-10-09. Scope: documentation and independent evidence review only.

**Package disposition: REJECT AS INDEPENDENT ECONOMIC ACCEPTANCE.** The submitted package is usable as an issue submission and a partial census. Its four `PASS` anchors, zero economic residual, exhaustive coverage, stacking proof, and independent selection claims are rejected. The current optimizer is **NOT ACCEPTED** by this review. Claude may begin the bounded corrections in `CODEX_FINAL_AG_ADJUDICATION_CLAUDE_REPAIR_PLAN.md`; AG's proposed golden amounts must not become production constants.

Every material submission claim has a terminal disposition in the companion claim and row registers. `NOT_ESTABLISHED` is an adjudicated evidence limit, not an unfinished calculation disguised as zero. Completing this adjudication does not imply completing the future implementation or certifying unknown qualified expenditure.

## 1. Identity and evidence boundaries

| Item | Pinned identity |
|---|---|
| Implementation branch | `claude/global-optimizer-remediation` |
| Implementation commit | `ee53fb28178907c4f2d234f41ee812a62f926b4b` |
| AG submission branch | `ag/exhaustive-optimizer-audit` |
| AG submission commit | `59ea903c8418534019d86989699924434cbd7b89` |
| Audit branch | `codex/final-ag-calculation-adjudication`, based on implementation commit |
| Current persisted engine | `canonical-1.105.0` |
| Original budget inputs | Four original PDFs, 158 account rows; a separate CFC allocation letter |

The two remote tips were checked directly. AG's branch descends from the pinned implementation. At the final check the implementation remote had advanced to `832905569ece7cd0f6f4207998d7177a55c88a72`; its difference from the audited target is confined to `CompactSidebarGlobe.jsx`, `CompanyGlobe.jsx`, `Sidebar.jsx` and `shell.css`. Calculation owners are unchanged. This review remains pinned to AG's target and grants no new visual acceptance. Claude must preserve the newer visual work when applying the repair plan.

The implementation worktree's pre-existing modified project rules and capability ledger were read as policy and preserved. No evaluator, parser, legal rule, frontend, database row, or generation was changed. No cold evaluation was run. Database inspection used read-only transactions, bounded summaries, and 500-row keyset pages of retained metadata. API GETs that could initiate evaluation or persistence were not used as audit shortcuts.

The evidence JSON records the exact four project IDs, budget document IDs and hashes, current fingerprints, anchor structure IDs, economic identities, engine comparison values, retained denominators, and primary-authority download hashes. Engine traces are comparison evidence. They are not independent inputs for legal eligibility or expected economic amounts.

Bad Hombres' current fingerprint is `ccff05ec483a6567ad40ab9e7bc409e70e33244ea6c9e16da89510d06e9bfecc`. Selecting its newest stored generation instead would pick an unrelated fingerprint. The other three current fingerprints also matched their reconstructed inputs without evaluation.

## 2. Corrected four anchors

### 2.1 What the original documents actually establish

| Production | Gross budget | Account rows | Source incentive | Source net budget | Established source state |
|---|---:|---:|---:|---:|---|
| The Little Utopia | $4,364,393 | 44 | $1,275,411 at a budgeted 35% | $3,088,982 | Producer estimate, 2025-06-03 |
| F#K Valentine's Day | $4,517,687 | 34 | $518,804 at 40% | $3,998,883 | Producer estimate, 2024-04-12 |
| Lips Like Sugar | $11,983,654 | 46 | $1,503,074 at 25% BTL | $10,480,580 | Producer estimate, revised budget dated 2024-02-25 |
| Bad Hombres | $2,482,023 | 34 | Not present | Not present | Undated v2 budget; PDF creation/modification metadata is January 2022 |

Little Utopia's leaf accounts sum to $4,364,395, **$2 above the stated gross**. Preserve this source discrepancy; do not silently alter an account to force balance. The other three account sums match their source gross. AG's stated counts of 36/32/56/34 are wrong even though its CSV's total 158 happens to be right.

Lips Like Sugar also has **CAL #8-053**, dated 2023-03-06, with a $1,470,365 conditional allocation and the **Independent Film $10m & Under** category selected. The signed form warns that the allocation is an estimate subject to final qualified-expenditure verification. Its signature-system audit page is not a tax-credit cost audit or final certificate. The application budget supporting that allocation is absent. A later $11.98m budget cannot be assumed identical to the earlier application budget.

### 2.2 Reverse-inferred bases are not documented schedules

| Value | Arithmetic result | Correct label |
|---|---:|---|
| LU estimate / 35% | $3,644,031.428571… | Implied base only; AG rounds it and labels it independently derived |
| FVD estimate / 40% | $1,297,010 | Implied base only; no local line schedule supplied |
| LLS budget estimate / 25% | $6,012,296 | Implied base only |
| LLS CFC reservation / 25% | $5,881,460 | Implied base only, conditional on no other credit adjustments |
| AG CFC reservation / 20% | $7,351,825 | Rejected: wrong project category/rate and false claim of documented QPE |
| AG BH independent base | $770,271 | Rejected: unsupported residency, vendor, travel and categorical exclusions |

The CFC category supports a 25% Program 3.0 independent-film base rate, not AG's 20%. The $32,709 difference between the later producer estimate and earlier reservation is real arithmetic. Its relationship to the different budget versions is not established.

### 2.3 Current implementation comparison

| Production | Current engine anchor QPE after cap | Floor incentive | Maximum modeled incentive | Floor NPC |
|---|---:|---:|---:|---:|
| LU / `mu_edb_incentive` | $4,355,327 | $1,306,598.10 | $1,742,130.80 | $3,057,794.90 |
| FVD / `gr_cash_rebate` | $3,614,149.60 | $1,445,659.84 | $1,445,659.84 | $3,072,027.16 |
| BH / `us_nm_film_credit` | $2,387,641 | $596,910.25 | $955,056.40 | $1,885,112.75 |
| LLS / `ca_film_30`, currently modeled as Program 4.0 | $9,883,654 | $3,459,278.90 | $3,953,461.60 | $8,524,375.10 |

These are **PERSISTED_OR_SERVED_COMPARISON_ONLY**, not independently accepted entitlements. A floor in the model is not a confirmed government award.

AG's LU final table uses $4,063,264 and $1,218,979.20. That QPE belongs to its cited **Ontario combination**, not LU's Mauritius anchor. The actual Ontario combination `055ff0ea-7c99-46e3-95f0-5ed3eff6837a` has programs OFTTC/OCASE and combined incentive $1,428,418.60. AG's own 400-row scenario file correctly contains the Mauritius anchor's $4,355,327, contradicting its final table. Neither the old $8,126,528 sum of overlapping claim bases nor $4,063,264 may be repurposed as Mauritius's independent QPE.

FVD's current trace first treats $453,583 financing as not applicable and excludes $362,866 contingency, producing **$3,701,238 before the cap**, then applies `min(pre-cap QPE, 80% × gross)` to obtain $3,614,149.60. The cap mechanism is an upper-bound operation, not a literal assignment of 80% regardless of spend. The defect is the unsupported territorial/category base feeding it. AG's old gross-minus-contingency-minus-finance explanation was wrong as a description of the **final capped** amount, but those deductions do describe the present pre-cap trace.

LLS's current trace already removes $1.7m financing and $400,000 contingency. It includes the separate $400,000 residual reserve and all four principal ATL accounts. AG's explanations use invented/misidentified account amounts: actual ATL travel is $60,561, actual insurance is $106,000, and the financing accounts are 6500/6600/6700; residual reserve is 6800 and contingency is 7100. LLS also has two legitimate 4900 rows; account code alone is not a unique source-line key.

### 2.4 Independent legal conclusions and missing facts

**LU:** The EDB guidance supports local expenditure, nonnational labor, travel to Mauritius, local accommodation, and professional insurance. AG's blanket foreign-flight, nonresident-crew and insurance exclusions are rejected. LA post expenditure is explicitly identified in the source; whether each remaining account satisfies territorial/vendor/incurrence requirements needs evidence. The persisted 100% contingency utilization is an approved **planning election recovered from demo state**, not proof of actual incurred expenditure. Removing all $301,131 would change the modeled floor by $90,339.30 and maximum by $120,452.40; those are sensitivity calculations, not certified overstatements. The source's 35% estimate is not proof that EDB approved a statutory 35% award. **Independent exact historical and current QPE/incentive/NPC: NOT_ESTABLISHED.**

**FVD:** Greek authority permits specified production costs subject to local-incurrence requirements, category limits and the 80% worldwide-budget ceiling. Historical Article 26 expressly includes screenplay/director/music costs and constrains specified principal fees; insurance/guarantees have a combined percentage limit. AG's blanket exclusion of all cast, rights, producers, post and bond is unsupported. The budget is a topsheet, not a Greek tax-invoice allocation schedule. The $926,855.84 difference from the producer estimate is an **unexplained economic control gap**, not a proved total engine overstatement. **Independent exact historical and current QPE/incentive/NPC: NOT_ESTABLISHED.**

**LLS:** CFC QEC rules disallow writer/producer/line-producer/director/principal-cast compensation while some assistants, research, duplication and stunt costs can qualify. The source's $300,000 writer fee is a concrete excluded component that the current engine includes: isolated sensitivity is **$105,000 at 35%**, or $75,000 at the historical 25%, before other repairs. Producer and line-producer fees require exclusion too. Do not exclude an entire mixed account merely because it is headed ATL. Production insurance and properly budgeted contingency/completion bond may qualify within CFC limits; AG's categorical exclusions are rejected. A residual reserve cannot be treated as incurred eligible payment merely because it is budgeted. The $1,988,913.90 engine-versus-reservation difference conflates program generation, budget version, QPE and allocation state; it is not the proved total cost of the category defect. **Independent exact historical and prospective current-law QPE/incentive/NPC: NOT_ESTABLISHED.** Preserve the actual $1,470,365 reservation separately.

**BH:** The NM statute and TRD guidance allow nonresident performing-artist payments subject to withholding/tax and other conditions. AG's central exclusion of $1,032,202 cast and asserted $404,342.50 overstatement are rejected. No source proves all producers/director/vendors are nonresident or all travel/insurance foreign. Its $3,618 BTL travel deduction is an unsupported split of the actual $31,260 account. The $60,000 SAG deposit/residual reserve is not evidence of incurred eligible services; full exclusion would change the base-rate model by $15,000, conditional on its being unspent. A feature film cannot earn a TV-series uplift, but facility/location eligibility needs actual facts. A permanent blanket 25% ceiling would erase valid conditional opportunities. **Independent exact historical and current QPE/incentive/NPC: NOT_ESTABLISHED.**

The source-to-engine bridges retain known arithmetic differences and separately label unexplained eligibility/version amounts. None closes an economic residual to zero by treating an inverse-rate estimate as a proved line schedule.

## 3. Temporal adjudication

Historical application/program identity must be recorded separately from a hypothetical current-law opportunity. Budget date alone cannot establish application date, acceptance, or grandfathering.

| Production | Historical evidence | Prospective current-law finding as of 2026-10-09 |
|---|---|---|
| LU | 2025 budget estimate; no EDB registration/approval supplied | EDB's published 2020 framework remains the retrieved primary source; 30% local-QPE base, up to 40% feature band subject to approval. AG's invented 2024–2026 regulation/2027 sunset and 24-month lock are not established. |
| FVD | April 2024 estimate; application status absent | Law 5105/2024 and JMD 607434, amended by 140524, govern the current scheme. Ordinary €8m grant ceiling has a statutory exception. Minimum-spend/budget/category and state-aid gates must be versioned. AG's unpinned $8.64m conversion is rejected. |
| LLS | 2023 Program 3.0 independent conditional allocation; later 2024 budget | Program 4.0 independent base is 35%, with a $20m qualified-expenditure limit, not an unrestricted 40% of the whole budget. Uplifts apply to eligible subsets and predicates. Preserve 3.0 allocation without converting it into a 4.0 award. |
| BH | Undated budget with January 2022 metadata; application date absent | 25% base and eligible additions require their own predicates. HB291 is chaptered in 2026, but its film provisions apply to taxable years beginning 2027-01-01; do not apply them early merely because other sections take effect July 2026. |

Current engine trace cap fields also expose **different concepts conflated**: NM's $140m annual fund amount is put in `incentive_cap_usd`; CA's $120m non-independent qualified-expenditure limit is put there too, while this project's independent category uses a different QE limit. Greece's current ordinary grant cap is absent from the anchor's incentive cap. These are confirmed rule-model defects beyond AG's incorrect four-dollar totals. They do not change the four anchors numerically at their current amounts; blast radius includes sufficiently large projects and affected category/rule pathways. Separate annual appropriation, eligible-base cap, grant cap, category cap and aid-intensity cap.

## 4. Actual coverage

| Project | Retained rows | Priced economic identities | Aggregate candidates | Generated denominator |
|---|---:|---:|---:|---:|
| LU | 977 | 659 | 222,081 | 223,058 |
| FVD | 2,108 | 1,248 | 1,213,792 | 1,215,900 |
| BH | 1,126 | 721 | 10,725 | 11,851 |
| LLS | 2,094 | 1,227 | 1,296,240 | 1,298,334 |
| Total | **6,305** | **3,855** | **2,742,838** | **2,749,143** |

This is an independently counted **persisted census**, not independently repriced economics or a proof of solver completeness. There are 2,274 retained `DOMINATED_WITH_PROOF` rows and 102 co-production opportunity rows; their existence does not establish independent dominance or executable treaty entitlement. No executable official treaty example is established by AG's claimed representative.

AG's 400 scenario IDs all exist in the current retained census, but its file takes exactly the 100 displayed `structures` entries per project. It independently derives **zero complete scenario economics**. For all 396 nonbaseline rows, its generator assigns independent QPE, incentive and NPC directly from engine values and sets discrepancy to zero. The other four expected values are rejected above. The 48 `VERIFIED_MATCH` labels are therefore not economic verification; the 348 conditional labels do not cure the same copied derivation.

The local registry inventory is **230 raw program records plus 67 alias/binding keys**, not 297 distinct legal programs. Aliases must resolve to canonical identities before program denominators are compared. AG's 61 appearances refer to its displayed sample. Its 124 filtered and 112 selective labels do not prove all other valid candidates were excluded by law. The companion program table records observed retained evidence separately from legal acceptance and preserves unresolved reachability as unknown.

Of AG's 12 pathway rows, only eight labels occur in its scenario CSV. The extra counts 15/28/45/35 are not an audited 400-row census. Several representative IDs directly contradict their claimed family/programs: Ontario is labeled UK standalone, Manitoba relocation is labeled CA/local grant stack, a MU–ZA component route is labeled MU–FR treaty, and two-leg hybrids are labeled three/four-leg. Every representative receives a row-specific disposition in the row register. Candidate leg count must come from actual role/component routing, not number of programs or a guessed name.

All **392 stacking rows** are rejected as independent legal/economic proof. The generator assigns parent/child bases and incentives as artificial **70%/30%** splits, unconditionally declares statutory permission and forces zero discrepancy. It truncates to two programs even when a structure contains more. It supplies no combination-specific primary authority, assistance reduction or spend-overlap derivation. Ordinary component splits, federal/provincial assistance-adjusted stacks, mutually exclusive program choices and treaty national-treatment pathways need distinct controls.

All **40 selection rows** are rejected as independent selection acceptance. They reuse earlier expected-JSON selections and engine economics. Their Overview slot names contradict the current contract: **Current Location, Leading Jurisdiction, Optimized Structure, Conditional Upside**. A sample deduplication check may establish identity uniqueness within those sample slots; it cannot establish the correct complete-universe winners. Rank changes cannot be quantified until their underlying economics are repaired and independently checked.

MFNI remains unestablished and separately disclosed. AG's assertion that every relocation/hybrid omits local costs, travel and FX is stale: current canonical hybrid normalization and relocation adjustment traces exist. Their presence is not independent empirical verification. Do not revive a generic NPC multiplier or remove valid alternatives while repairing classification or recommendation eligibility.

## 5. Defect dispositions and blast radius

| AG ID | Terminal disposition | Accepted repair boundary |
|---|---|---|
| DEF-LU-001 | Reject exact dollars, Ontario/Mauritius identity substitution and blanket travel/insurance/contingency exclusion; contingency evidence-state concern retained | Preserve planning election; distinguish expected deployment from incurred/approved claim facts and establish territory per component |
| DEF-FVD-001 | Partially confirm unsupported territorial/category base; reject claimed exact $926,855.84 overstatement and literal cap-assignment story | Derive eligible local spending/category limits first, then cap; retain unexplained source-estimate variance |
| DEF-LLS-001 | Confirm specific disallowed compensation/default inclusion and reserve-state issue; reject blanket ATL/bond/insurance and invented line amounts | CFC category-specific subline qualification, wages/fringes/vendor/territory limits |
| DEF-BH-001 | Reject nonresident-performer prohibition, exact base/dollars and unconditional 25% clamp; retain reserve/nexus/predicate deficiencies | NM withholding/vendor/incurrence conditions, reserve state and mutually exclusive uplift predicates |
| DEF-TEMPORAL-001 | Confirm missing distinction between historical allocation and current opportunity; reject “binding final award overwritten” and claimed exact loss | Explicit timeline/program/application snapshot and separate external-control state |
| DEF-AUDIT-001 | Confirm withdrawn audit artifact; no production dollar defect | Prevent claim-base sums from becoming unique production spend and prohibit circular expected values |
| DEF-AUDIT-002 | Confirm withdrawn wrong final-QPE provenance; corrected pre/post-cap trace above | Store and independently verify both amounts; distinguish arithmetical and economic residual |
| DEF-ENGINE-001 | Partially superseded: calculate route returns 410; unparameterized demo routes remain mounted | Isolate remaining demo read/write exposure and establish actual production routing; do not reimplement a retirement already done |
| DEF-UI-001 | Reject as stale | Current ProductionHero is budget-only and no longer accepts scenario economics; do not bind new incentive/NPC fields into it |

AG's claimed first-introducing commit `f602621d` is a 2026-10-08 frontend stage-color/Blue Marble commit with no calculation changes. It cannot introduce the cited legal/economic bugs. `6b449733` and generations 1.12–1.34 also do not establish introduction of defects in current 1.105. Exact first introduction remains unknown where a bounded history trace does not prove it. The defect table must not invent a commit to satisfy a required field.

Confirmed category/base defects affect every standalone, component, hybrid and lawful stack using the affected rule, then ranking, cached generation and presentation derived from it. They are not restricted to AG's one/five named structures. The companion defect table records affected programs and dependency paths, specific proved components, conditional sensitivities and unknown total impacts. A complete numerical blast radius requires a later isolated replay after correction; this review does not pretend the 400 sampled outputs establish it.

The reported frontend regression was reproduced at the pinned implementation: **11 passed, one failed** in `incentive-potential-presentation.test.mjs`. The failure is a source regex requiring a `hidePotential` expression at the route hover. It is a genuine test failure, not proof of an economic calculation defect. AG's four backend failures remain a reported result requiring an isolated test DB; this read-only review did not execute tests that may write to the shared database.

## 6. Historical reconciliation and invalidation

The recovered **2026-08-09 GLOBAL_THREE_ENGINE_RECONCILIATION** at `7fd21bd` identifies **Codex, Gemini, and Claude/Chat**, not AG as a historical third participant. It reconciled a 262-program inventory, rejected Gemini's 410/415 records, and established a five-jurisdiction implementation pilot. The treaty registry and “not contradicted” operational conclusions were not exhaustive independent four-budget arithmetic acceptance. The earlier gate was NO-GO until fixes, not an unconditional calculation sign-off.

The **2026-09-01 external calculation control audit** at `2a4140070e351582ad9a8248901b51b35ddce0cd`, against `bb4b6a25317e398be628c70a0c6899bff2fd8e44`, examined 50 projects/119 budget documents, 30 independent control families and 18 projects. It found **zero fully reconciled calculations**. FVD's $926,855.84 economic residual was already explicit despite zero arithmetic residual; LLS's conditional reservation used a different budget version. Its LU “no external control” statement is superseded by the recovered $1,275,411 producer estimate. Earlier proposed relationship fixtures were a specification, not proof that permanent controls were installed.

The historical final backend and health documents decided **ONE_CONSOLIDATED_CORRECTION_PASS_REQUIRED**. AG's retrospective “conditionally accepted architecture” summary omits that controlling disposition. The 2026-09-18 current-tip numerical audit likewise decided **OPTIMIZER_NOT_ACCEPTED** and separated arithmetic consistency from legal/base correctness. Old route, hero and selection findings must be checked against current code before being prescribed again.

The companion lineage register corrects dates and actual introduction commits. Examples: location final acceptance is 2026-10-06 (`dac1514`), its remediation is 2026-10-07 (`36844e6`), four-project pricing reconciliation is 2026-10-02 (`c5360d5`), and the final pre-Codex handoff is 2026-10-07 (`a43f59e`), not AG's invented August sequence.

Acceptance must expire by dependency: parser/source/account changes invalidate line inputs; spend/rate/cap/temporal changes invalidate economics; normalization changes invalidate comparable NPC/ranking; solver/retention changes invalidate completeness/dominance; selector changes invalidate slot acceptance; serving/leading changes invalidate surface parity. Relevant subsequent changes include parser remediation, bounded retention (1.90), normalization/recommendation (1.96/1.97), post/VFX bundles (1.98), corrected fingerprint stamp (1.99), floor/max contract (1.101), curation (1.102), four-project default modeling (1.103), and generation/coverage (1.104/1.105). An old green result does not survive them automatically.

## 7. Permanent controls disposition

AG's control objectives are largely appropriate; its document is **a proposal, not twelve installed machine-enforced controls**. Its BH golden fixture encodes a wrong eligibility rule. Its flat `atl_qualified`/`nonresident_qualified` booleans cannot express mixed accounts, tax conditions or eligible subsets. Its no-numeric-literal linter would reject valid independent fixtures while missing copied derivations. Its requirement to force zero unexplained economic residual encourages fabricated evidence.

AG's validator passed its submitted artifacts and **21/21 own negative checks**. In isolated copies, Codex changed separately (a) an independent incentive to $987,654,321, (b) a stack child base to $987,654,321, (c) source QPE to $987,654,321, and (d) the Mauritius base rate to 99%. **All four corruptions were accepted with zero errors.** These are actual executed falsification probes against the artifact validator, not mutations of the production evaluator. The evidence JSON retains the before/after fields and results.

`CODEX_FINAL_AG_ADJUDICATION_CONTROLS.md` replaces the proposal with concrete data owners, dependency hashes, lawful unknown states, independent expected-value derivations, real runtime mutation gates, completeness/dominance proof obligations and exact surface identity comparisons. Controls remain **NOT IMPLEMENTED by this documentation-only task**.

## 8. Completion and implementation gate

This adjudication disposes every submitted CSV row, all nine alleged defects, the final handoff claims, historical claims and twelve control proposals. It accepts independently verified document amounts, bounded census existence and the specific current defects above. It does not accept any complete four-project legal/economic golden amount or certify a full optimizer pathway universe.

**IMPLEMENTATION_MAY_BEGIN: YES, within the ordered repair plan.** Begin with source/temporal state and independent category controls, then repair the canonical kernel and rule cap/predicate types. Use an isolated test database for replay. Preserve valid alternatives, distinguish floor/maximum/award states, keep MFNI's research boundary, and independently verify source → fingerprint → persisted calculation → served identity → actual UI. Production acceptance requires that later evidence; it is not granted here.

## 9. Primary authority and calculation formulas

Downloaded document hashes and page counts are retained in the evidence JSON. Original project PDFs remain in their registered local storage; their names, hashes and independently checked account amounts are in the source register and line table. No private tax identifiers or contact details are reproduced.

| Source ID | Direct primary source | Relevant pinpoint |
|---|---|---|
| MU2020 | [EDB submission procedures](https://edbmauritius.org/wp-content/uploads/2022/10/Guideline-Online-Application-FRS.pdf) | PDF pp.3–4 and 7–8: rate bands, eligible categories, incurred/audited claim requirements |
| CA3REG | [CFC Program 3.0 regulations](https://cdn.film.ca.gov/wp-content/uploads/2023/12/3-0-Current-Regulations.pdf) | Independent-film rate and eligible-budget/application provisions |
| CA3QEC | [CFC Program 3.0 expenditure chart](https://film.ca.gov/wp-content/uploads/2025/07/3-0-QEC2.pdf) | Printed pp.1–5, 32–33: compensation, fringes, insurance, contingency/bond distinctions |
| CA4GUIDE | [CFC current Program 4.0 guidelines](https://cdn.film.ca.gov/wp-content/uploads/2025/08/4.0-Program-Guidelines-1.pdf) | January 2026 document; printed pp.7–8 and 18–19: categories/rates/limits and budget allowances |
| CA4QEC | [CFC current Program 4.0 expenditure chart](https://film.ca.gov/wp-content/uploads/2025/10/Program4.0QEC.pdf) | January 2026 document; qualified services, compensation and category/subset uplift tags |
| NM2019 | [New Mexico enacted SB2](https://www.nmlegis.gov/Sessions/19%20Regular/final/SB0002.pdf) | Qualified direct expenditure and nonresident-performer/tax provisions |
| NMFYI2025 | [TRD FYI-370](https://realfile.tax.newmexico.gov/FYI-370.pdf) | PDF pp.9–13: taxable nexus, artist limit and direct/loanout performer eligibility |
| NM2026 | [Chaptered HB291 final text](https://www.nmlegis.gov/Sessions/26%20Regular/final/HB0291.pdf) | Sections 6–9, 18–19: film amendments and 2027 applicability; [enactment record](https://www.nmlegis.gov/Legislation/Legislation?chamber=H&legno=291&legtype=B&year=26) |
| GR2021 | [Official consolidated Law 4487/2017 text](https://www.ekkomed.gr/wp-content/uploads/2022/12/1.LAW-4487.17.pdf) | Article 26: local expenditure, 80% ceiling, category limits and lending/bank exclusions |
| GR2023 | [Official Law 5043/2023 amendment](https://www.ekkomed.gr/wp-content/uploads/2023/07/LAW-5043_2023-ART-61-63_GGIA91-13.04.2023_en.pdf) | Article 61: foreign-invoice exception for eligible costs over €8m, specified director/leading roles, 20% foreign-invoice limit |
| GR2026 | [JMD 607434](https://www.ekkomed.gr/wp-content/uploads/2026/02/KYA-607434-FTV.pdf) | Articles 4–6 and eligible-cost annex; category/action limits and ordinary grant ceiling |
| GR2026AMEND | [JMD 140524 amendment](https://www.ekkomed.gr/wp-content/uploads/2026/05/%CE%9A%CE%A5%CE%91-140524_-FTV.pdf) | PDF pp.4–5 visually read: amended funding/action/application provisions |

The corrected independent formulas are parametric until their factual leaves exist. `Q` means the independently established eligible cost after applicable category limits, `B` the legally defined worldwide production cost, and `U` an earned addition on its own eligible subset. All program/application/minimum-spend gates must be satisfied before a formula establishes entitlement.

| Production/context | Conditional independent formula |
|---|---|
| MU historical/current retrieved framework | Base `0.30 × Q_MU`; higher approved band capped at `0.40 × Q_MU`. The producer's 35% inverse is an estimate comparison. |
| GR historical | `0.40 × min(Q_GR, 0.80 × B)` subject to historical category, aid-intensity and applicable high-budget exceptions; Q_GR is not the producer inverse. |
| GR current | Same qualified-base ceiling/rate, then applicable €8m ordinary grant limit/exception and aid-intensity limit using evidenced FX; retain current action/category gates. |
| CA historical independent Program 3.0 | `0.25 × min(Q_CA, $10m) + earned eligible-subset additions`, subject to actual allocation/program terms; compare separately to the $1,470,365 conditional allocation. |
| CA prospective independent Program 4.0 | `0.35 × min(Q_CA, $20m) + U` under the current independent category and subset rules; no blanket 40% whole-budget entitlement. |
| NM historical/current applicable law | `0.25 × Q_NM + earned eligible-subset additions`, with performer/crew/tax and lawful nonoverlapping uplift constraints. No $140m annual appropriation used as a per-project cap. |

For each context, NPC is the evidenced comparable production cost minus the independently eligible incentive plus independently evidenced adjustments. A source budget net or hypothetical gross-minus-reservation result is not automatically comparable NPC. The formula table does not supply absent territorial invoices, dates, payroll/tax records, allocation budget or incurred-cost facts.
