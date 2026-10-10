# Permanent calculation acceptance controls: implementation contract

Status: **SPECIFICATION ACCEPTED FOR IMPLEMENTATION; NOT IMPLEMENTED OR RUNTIME ACCEPTED**.
Authority: final Codex adjudication, 2026-10-09, pinned implementation `ee53fb28`.

## 1. Independent inputs and labels

Maintain a control manifest outside production evaluator output. Each expected value must carry a source document hash, source page/row/subline, currency, production territory/date/payment state, primary-rule snapshot, independent formula and reviewer disposition. Engine rows may be attached only as comparison observations. Allowed labels are `PRIMARY_DOCUMENT_VALUE`, `DOCUMENTED_LINE_SCHEDULE`, `INDEPENDENT_RECONSTRUCTED_FROM_RAW_LINES`, `IMPLIED_FROM_INCENTIVE_AND_RATE`, `IMPLEMENTATION_VALUE_UNDER_AUDIT`, `PERSISTED_OR_SERVED_COMPARISON_ONLY`, `NOT_ESTABLISHED`, and `AUDIT_ARTIFACT_WITHDRAWN`.

No `IMPLIED_FROM_INCENTIVE_AND_RATE` number may be promoted to a documented schedule. No unexplained amount may be given a zero residual. Distinguish arithmetic residual from economic/source-version residual. Exact independent amounts remain null where necessary. A conditional formula and the exact missing facts are valid controls; a fabricated scalar is not.

Source-line identity is `(document_sha256, page, row, ordinal/subline)`, not account code. Preserve LU's $2 mismatch and LLS's two legitimate 4900 rows. Pending/recovered demo facts cannot silently become actual paid/incurred or approved eligibility facts.

## 2. Versioned program and external-control owners

The canonical rule owner must store `program_identity`, canonical aliases, legal snapshot ID/hash, jurisdiction, project category, application/allocation/production dates, effective/transition predicates, primary URL/hash/pinpoint, currency and FX provenance, and review disposition. A snapshot has category/subline predicates and base transformations; blanket ATL/nonresident booleans are insufficient.

Separate `HISTORICAL_AS_OF_APPLICATION`, `HISTORICAL_BUDGET_ESTIMATE`, and `PROSPECTIVE_CURRENT_LAW` calculation contexts. Missing application date is unknown, not the budget date. A current-law opportunity may remain visible with disclosure; it must not replace a historical allocation.

External-control state owner must distinguish producer estimate, official conditional allocation/reservation, final cost-certified certificate, withdrawn/superseded control, and prospective modeled opportunity. CFC CAL #8-053 is an official **conditional allocation**, not a final guaranteed claim. Connect each control to its own budget version and permitted comparison types. UI labels must use those states.

Historical expected controls remain immutable evidence, while their relevance to current implementation is explicitly invalidated. A 180-day review horizon can prompt revalidation but cannot overrule a known amendment, expiry or application transition. Do not expire historical statutes into replacement current rules.

## 3. Qualification before caps

Spend owner must record each category/subline's `eligible`, `ineligible`, `conditional`, `mixed`, or `not_established` state, eligible fraction or amount if proved, territorial/payment/tax predicates, applicable cap family, and source evidence. Apply facts before category limits; apply category limits before overall QPE/aid limits. Preserve pre- and post-cap amounts and the cap that binds. Do not subtract the same cost twice through account and financing adjustments.

Required initial independent controls:

| Control | Required expected relationship |
|---|---|
| CA writer + script duplication | Actual writer compensation excluded; eligible duplication/research tested separately; a mixed account cannot all qualify or all disappear |
| CA producer/line producer + assistants | Producer and line-producer compensation excluded; assistants qualified only on their own facts |
| CA principal cast + stunts/background | Disallowed principal compensation never inherited by qualifying stunt/background sublines or vice versa |
| CA contractual contingency/bond | Application allowances follow 10%/2% limits and budget state; final incurrence/payment state remains distinct |
| CA insurance | Production coverage separated from E&O and territorial/vendor requirements |
| NM resident/nonresident performers | Nonresident direct/loanout payments qualify only with applicable withholding/GRT/service/cap facts; residence alone cannot universally exclude them |
| NM crew and producer/director | Performers, industry crew, vendors and personal-services businesses use their actual statutory predicates |
| Deposits/reserves | Depositing or budgeting money is not proof of an incurred qualified cost; later deployed service expense counted exactly once |
| MU travel/insurance/nonnational labor | Express eligible categories preserved with territory/service facts; no invented airline-nationality restriction |
| GR local-spend ceiling | `min(independently established eligible local spend, 0.8 × eligible worldwide production cost)`; no local schedule means unknown independently, even when a model can price an assumption |
| GR principal fees/guarantees | Historical/current category percentage limits applied to their own base; rights/cast/bond are not all categorically excluded |

Cap owner must distinguish **annual fund budget, project incentive cap, project eligible-base cap, category cap, and cumulative aid-intensity cap**. Store cap currency/FX date and exceptions separately. NM annual $140m is not a per-project incentive ceiling. CA independent $20m and non-independent $120m are QE limits under current CFC guidance. Greece's €8m ordinary grant cap carries its statutory exception. A cap must never create spending evidence.

Uplift owner must compute additions on actual eligible subsets. TV/facility/rural, independent/non-independent, out-of-zone wage/spend and VFX predicates are separate. Mutually exclusive alternatives cannot be added together. Unsupported upside remains visible and labeled conditional; impossible combinations never inflate maximum potential.

## 4. Independent expected derivation and circularity gate

Store a derivation graph: leaves are independent raw source amounts/facts and primary rule clauses; operations are explicit sums, exclusions, eligible fractions, rates, cap transforms and stack assistance reductions. Pin its hash. Expected economics cannot depend on the evaluator, persisted rows, served JSON, presentation selectors or engine classifications. Comparison records may depend on those owners in a separate graph.

CI must reject an expected-value graph that references production-output owners or omits a monetary derivation. Numeric literals are allowed when they cite independent evidence. An AST search for literals or the presence of eight labels alone does not establish independence. Reviewer records must state exactly what was accepted, rejected or unknown and identify source/rule versions; three model names or cryptographic signatures alone do not prove correctness.

## 5. Candidate, pathway and stacking completeness

Derive the candidate universe from canonical source inventory, aliases, project facts and explicit generator families. Inventory count is not legal universality. Keep source canonical identities separate from alias keys. For every candidate route, retain either an independently evaluated result, an exact rule rejection, a proof-carrying safe bound, or an explicit unproven disposition.

Generated = retained + aggregated must hold, but conservation alone does not prove admissible generation or safe pruning. A dominance proof must name the same-context winner, independent lower/upper bounds, eligibility predicates and inequality; aggregated groups must carry sufficient data to independently check each bound. Do not call an absent top-100 row dominated. Rejected/unpriceable candidates need real rule IDs and input evidence.

Pathway manifest must cover single anchor, full relocation, component relocation, ordinary hybrids by actual number of roles/territories, same-jurisdiction multi-program alternatives, federal/provincial assistance-adjusted stacks, official bilateral/multilateral treaty roles, selective nonpriceable funding, minimum-spend/category rejection, overlap exclusion, and retention/dominance decisions. One representative establishes one case, not a family universally. Treaty opportunity visibility is distinct from executable treaty nationality/ownership/financial-share qualification.

Stack controls must specify each participating program, independently assigned spend/role basis, overlap type, lawful combination authority, assistance reduction/order, per-program rate/cap and final total. A lawful common claim base is not necessarily double-counting, while unique production spend is the union of cost identities. Use actual n-program routing; never invent 70/30 bases, truncate extra legs, or treat cross-border component routing as statutory stacking.

## 6. Change-impact invalidation

Manifest dependencies must hash source files/documents, normalized raw lines, typed fact values/states, parser/classifier, canonical rule/snapshot/aliases, cap/stack/qualification logic, travel/local-cost/FX owners, solver/bound/retention logic, and serving/selection contracts. Map each to affected controls and acceptance scopes. A mismatch yields `PENDING_REVALIDATION` for those scopes and blocks claims of completed acceptance.

| Change owner | Minimum invalidated acceptance |
|---|---|
| Document/parser/line keys | Input sum, classification, all dependent economics |
| Facts or payment/application state | Eligibility, timeline, affected incentives/maximum, fingerprints |
| Spend/rate/cap/stack/temporal rule | Dependent anchor/component/hybrid/stack economics and rank |
| Travel/FX/local-cost normalization | Comparable NPC and recommendation rank; no automatic MFNI acceptance |
| Generator/bounds/retention | Candidate completeness, dominance and complete-universe selections |
| View selector/leading identity | Overview/Workspace slots, user-leading resolution and parity |
| API/cache/schema | Persisted-to-served identity/fingerprint and surface parity |

Commit claims and generation IDs do not substitute for hashes. A code-only fingerprint change must invalidate old caches even if the version string was accidentally unchanged. The dependency graph must detect that failure. Evidence of a rerun must include the actual target SHA/input fingerprint and what it tested; no generic `rerun=TRUE` field.

## 7. Mutations that must really fail

Run in an isolated test DB and disposable code checkout. Mutate the **production owner**, then execute independent expected controls and restore it. Preserve mutant, command, actual failure and restoration hashes. Artifact-format rejection is a separate test category.

Required runtime mutants: rate inflation; a CA writer leak; exclusion of a legally qualifying NM nonresident performer; reserve treated as incurred; wrong territorial QPE below/above GR cap; annual fund treated as project cap; CA independent/non-independent limit substitution; unearned/mutually exclusive/subset uplift; assistance double-count; dropped third stack leg; historical 3.0 control evaluated as 4.0; source amount changed without fingerprint invalidation; valid candidate omitted by top-N; false dominance bound; user-leading identity replaced by rank one; stale generation served under current fingerprint.

Required artifact mutants: false source page/hash, implicit inverse-rate base mislabeled documented, fabricated independent amount, wrong leg/family representative, duplicate identity, fake economic zero residual, stale audit acceptance after a dependency change. The four executed Codex probes accepted by AG's current validator are mandatory rejection regressions. A complete integrity suite must independently recompute relationships, not merely reject a few exact strings.

## 8. Serving and UI acceptance

Bind comparisons to `(project_id, budget_version, input_fingerprint, engine_version, structure_id, economic_identity, timeline/snapshot)` and exact cents. Verify persisted row → project state → portfolio aggregate → Inspector → Overview → Workspace → full/corner Globe. No warm-store or different-generation substitution. Preserve maximum-potential NPC primary and model-floor/award states explicitly.

Overview contract: Current Location, Leading Jurisdiction, Optimized Structure, Conditional Upside. Workspace contract: current product's six modes/slots with actual eligibility and complete-universe ordering. Recompute expected slot membership independently from the documented contract and accepted economics; do not import production selector outputs as expected values. Deduplicate by economic identity within a surface without silently discarding legally valid alternatives from discovery.

Retire/isolate actual demo routing still exposed under production namespace. Verify the old calculate endpoint stays 410. ProductionHero remains budget-only; no new scenario-economics binding is warranted by AG's stale finding.

Final UI verification must use actual pointer/leading interaction, cold direct load, required surfaces and console/network inspection. Static source assertions prove only their own narrow contract. MFNI remains `NOT_ESTABLISHED`/not modeled until separately accepted budget-line-to-Inspector empirical work; existing travel/local-cost calculations must be independently tested without replacing them with a generic multiplier.

## 9. Gate outcomes

Gate returns separate source, economic, temporal, completeness, ranking, serving and UI statuses. `ACCEPTED` requires all applicable controls; `PARTIAL` enumerates the exact scope; `NOT_ESTABLISHED` names missing facts without fabricated values; `REJECTED` names contradictory evidence. An honest unknown does not fail arithmetic integrity, but it prevents claiming a confirmed entitlement or exact economic acceptance.

After implementation: commit/push with remote equality, retain bounded command/test results and no process left running, attach actual evidence to the capability ledger, and obtain independent disposition of the changed scope. No future implementation may cite this design document as proof the controls already execute.
