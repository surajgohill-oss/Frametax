# CineGlobe — Account Transfer Handoff

**Purpose:** hand this repository to a different Claude account that may hold additional CineGlobe engines/artifacts not present here. This document lets that account compare, reconcile, and choose canonical ownership **without prematurely deleting or merging anything**.

> ⚠️ **DO NOT rebuild, delete, merge, or deprecate any engine until the other account's code and artifacts have been inspected.** Nothing here is declared permanently canonical just because it is the only implementation visible in this repo.

---

## 0. Update (2026-07-26) — Production Knowledge Database + Cross-Model Bridge + Stage B Verification Sprint

Everything in §1-§7 below predates this update and describes an earlier state (4 executable jurisdictions: MU/MT/IE/GR; 211 examined; 2967 tests). It is preserved as-is rather than rewritten — the reconciliation procedure (§6) and explicit warning (§7) still govern, and the overlapping-engine analysis in §3/§4 is still the right starting point for comparing this account's optimizer/structuring engines against another account's. This section records what changed since, so a future account does not have to re-derive it.

**Production Knowledge Database (`app/data/program_requirements.py`)**: a structured `ProgramRequirementsProfile` registry — local-entity/cultural-test/preapproval/audit/transferability/timing facts, not just rates — covers **71 of 110 executable jurisdictions** (Stage A complete). Verification tier as of this update: **61 PRIMARY_VERIFIED / 10 SECONDARY_VERIFIED / 0 UNVERIFIED** (up from 49/21/0 at the start of Stage B). `UnknownReasonCode`-tagged Structured Unknowns: 7 (never generic "UNKNOWN"). Original-currency statutory amounts kept separate from any USD normalization (`STATUTORY_AMOUNTS_ORIGINAL_CURRENCY`; currency normalization is explicitly deferred to a future optimizer phase). Full narrative history is in `docs/architecture/CAPABILITY_LEDGER.md` (search "Database Completion Phase" for Stage A, "Stage B" for the verification sprint). Machine-readable coverage: `docs/architecture/RULE_COVERAGE_REPORT.json` (regenerate via `python -m app.optimization.rule_coverage_report --write`).

**Discovery Provenance Audit**: the full 303-entry DISCOVERY catalog (`app/data/global_inventory*.py` + satellites) was individually classified into a 7-status ledger (`docs/DISCOVERY_PROVENANCE_LEDGER.md` + `docs/architecture/discovery_provenance_ledger.json`) — provenance-only, disclosure-only, never consumed by any pricing path.

**Cross-Model Bridge (`app/bridge/`, `/api/v1/bridge/*`)**: a new, separate, internal-only subsystem for multi-provider (Anthropic/OpenAI/Gemini) audit and requirements research — native adapters, SQLite persistence, outbound redaction/confidentiality gating, a rule-provenance matrix, and a CLI (`app/bridge/cli.py`). Not referenced by the frontend, not linked from any producer-facing screen. Setup: `docs/CROSS_MODEL_BRIDGE_SETUP.md`.

**Stage A complete, Stage B in progress**: Stage A populated toward ~65-70 executable jurisdictions (finished at 71/110). Stage B is a Primary Verification Sprint upgrading the SECONDARY_VERIFIED backlog to PRIMARY using administrator-issued guidance — three batches completed so far (9 + 1 + 2 = 12 upgrades), backlog down from 22 to **10**. Continue opportunistically, not as a broad campaign — see §0.2 below for the exact remaining list and each item's classification.

### §0.1 — New permanent engineering rule: Document Retrieval Escalation

**A parser limitation is not evidence that authoritative information is unavailable.** Before leaving any jurisdiction SECONDARY on documentation-access grounds, distinguish precisely between:
- **retrieval failure** (the request genuinely didn't reach the server — DNS, timeout, connection refused)
- **parser failure** (bytes were retrieved successfully but the tool used to read them failed — e.g. a PDF-to-text step producing hallucinated placeholder content instead of the real text)
- **OCR-required document** (a scanned image with no text layer)
- **malformed PDF** (genuinely corrupt or non-standard-encoded)
- **authenticated/blocked resource** (a real bot-detection challenge, e.g. Cloudflare `cf-mitigated: challenge` — do NOT attempt to bypass; this is the one category where SECONDARY is the correct final answer)
- **server-side TLS misconfiguration** (a missing intermediate certificate — `openssl s_client` will show `verify error:num=20/21`; this is a broken-but-non-adversarial chain on the SERVER's end, not a security control, and retrieving public information through it with certificate verification disabled is not the same as bypassing a CAPTCHA or auth wall)
- **genuine absence of an authoritative source**

**"Unparseable PDF" is not, by itself, a completed investigation.** Two confirmed wins this session from applying this doctrine literally:
- **Malta**: a PDF had been successfully downloaded in an earlier session (1.1MB, 28 pages, saved to disk) but the tool used to read it produced hallucinated content. This session located the saved file and extracted the real text directly via `pypdf` (already a project dependency) — recovering the actual, decisive primary source and upgrading the jurisdiction to PRIMARY_VERIFIED, correcting two independently-wrong prior rate structures in the process.
- **Mexico**: `dof.gob.mx` failed with a TLS verification error. `openssl s_client -connect www.dof.gob.mx:443` confirmed `verify error:num=21:unable to verify the first certificate` — a server-side missing-intermediate-cert issue, not a block. `curl -k` (verification disabled) retrieved the real Decree text with a normal HTTP 200, upgrading the jurisdiction to PRIMARY_VERIFIED and correcting an annual-vs-total-envelope mischaracterization.

**When escalation reveals a genuine correctness bug, fix it before committing.** Malta's real Guidelines describe a "Difficult Audiovisual Work" 50% rate tier gated on a maximum-budget CEILING (≤EUR 1.5M) — a condition the `RateRule`/`resolve_program_rate()` schema has no way to express (only minimum thresholds exist). Modeling it as a normal priced tier would have made the engine wrongly select 50% for ANY Malta production above the EUR 50,000 floor, irrespective of actual budget size. Caught during the pre-commit repository consistency audit; the tier was removed from the priced set and kept as a disclosure-only fact with a permanent code comment explaining why — see `program_rate_rules.py`.

### §0.2 — Remaining Stage B backlog (10), classified

| Jurisdiction | Slug | Category | Notes |
|---|---|---|---|
| South Korea | `kr_kofic_location_incentive` | **Authoritative conflict** | 4 independently conflicting characterizations reconciled and documented in full (3744-char writeup in `additional_facts`) — most likely program-version drift over KOFIC's 15-year history. Do not re-research without a genuinely new source. |
| Switzerland | `ch_pics_national_rebate` | Engineering limitation | 3 direct fetches, all 404/generic pages on bak.admin.ch. Not obviously resolvable by the TLS/parser techniques that worked for Mexico/Malta. |
| Taiwan | `tw_bamid_rebate` | Engineering limitation | Official site returned HTTP 522 (origin down) twice — a real server outage, not a block. Retry later. |
| Poland | `pl_pisf_cash_rebate` | Engineering limitation | pisf.pl 403 ×2, polishfilmcommission.pl TLS cert hostname mismatch, cineuropa.org 403. **Try the Mexico-style `curl -k` / UA-header workaround here first** — same class of issue, not yet attempted with the new escalation doctrine. |
| Austria | `at_fisa_plus` | Engineering limitation | fisa-plus.at DNS-unreachable; admin facts already PRIMARY-quality, rate/threshold facts remain secondary. |
| Singapore | `sg_made_with_singapore_rebate` | Engineering limitation | Source is an actual IMDA guidelines PDF (Aug 2020) — **the strongest remaining escalation-doctrine candidate**, same class of issue Malta just resolved. Try `pypdf` extraction directly. |
| UAE/Dubai | `ae_dxb_dpip` | Repository completeness | Decent secondary corroboration; the official DFC guidelines page hasn't been directly fetched yet. |
| Malaysia | `my_finas_rebate` | Repository completeness | Still a thin Pass A migration — no external source attempted at all. |
| Qatar | `qa_screen_production_incentive` | Repository completeness | Solid secondary sourcing (Doha Film Institute press release); the official DFI programme page not yet directly fetched. |
| Sweden | `se_production_rebate` | Repository completeness | Solid secondary sourcing; Tillväxtverket's specific guidelines page (not just its homepage) not yet directly fetched. |

**Recommended first objective for the next account**: apply the Document Retrieval Escalation doctrine to Singapore (`sg_made_with_singapore_rebate`) first — a real PDF is already identified and likely just needs the same `pypdf` treatment that unlocked Malta. Poland is the second-best candidate (retry with `curl -k` / a browser user-agent, per the Mexico precedent) before falling back to broader research on the three repository-completeness jurisdictions (UAE, Qatar, Sweden) or Malaysia (which has no source attempt on record at all).

**Four Material Discrepancies remain open, deliberately unresolved** (rate-rule/calculation logic is frozen — a discrepancy is preserved and disclosed, never silently resolved by editing the rate, UNLESS a direct-primary-source escalation like Malta's/Mexico's decisively resolves it, in which case it's fixed and the ledger records why): Luxembourg AFS (repayable advance vs. modeled flat rebate rate), Washington State (modeled 0.45 vs. verified "up to 30%"), Chile CORFO/IFI Audiovisual (modeled flat 0.40/$1M min vs. verified tiered 30%/$3M cap + 40% region-only uplift, $2M min), South Korea KOFIC (4-way conflict, see §0.2). All are recorded in the affected `ProgramRequirementsProfile.evidence.notes` and `additional_facts` — search `program_requirements.py` for "MATERIAL DISCREPANCY" to find them.

**Git state as of this update**: branch `claude/audit-frametax-features-NZcX5`, working tree clean, pushed to `origin/claude/audit-frametax-features-NZcX5` (check `git log -1` for the current HEAD — this document is updated in the same commit as the work it describes, so its own HEAD reference would be immediately stale). Full suite: **3896 passed, 1 skipped, 0 failures** (venv). See §8-§9 below for the engineering principles and lessons that governed this phase of work — read those, and §0.1 above, before starting Stage B continuation or any new jurisdiction research.

---

## 1. Work completed on this account since the prior transfer

- **Qualification / rate authority / economics / legal / travel / FX / people / script / cultural** brought to served, runtime-verified state (earlier sessions — closed, do not re-audit).
- **Executable jurisdiction knowledge**: MU, MT, IE, GR wired (doctrine + statutory rate rules).
- **Grants/funds** connected on `/economics.available_funds`; **stacking** moved to PARTIALLY CONNECTED (real per-jurisdiction relationship edges surfaced, no fabricated dollar figure).
- **Production-structuring audit** (closeout #3): proved the structuring engine already existed in disconnected pieces; corrected the "unbuilt" assumption.
- **Structuring Advisor generalized + connected** (closeout #4): `structuring_advisor.py` de-hardcoded (identity + 4 amounts → params; signal-gated) and connected live via a factory that derives inputs from the real register/facts/rate; served on `/economics.structuring_advisory`; emits `routing_decisions` (allocation seed). 70 original LU tests unchanged + 7 new.
- **Workspace title/economics wiring fix** (Phase "restore"): scenario cards restored to frozen plain-jurisdiction-name titles (no "Relocate to X" — that wording is NOT canonical); all four displayed economics fields wired to the per-scenario canonical object.
- **Optimizer reconciliation**: confirmed `allocated_structures` (account→jurisdiction allocation + multi-register pricing, commit `bfd6364` "keystone") is the single canonical served optimizer; removed the stale unconsumed Phase 7B `global_scenario_ranker` top-level `ranking` (STRUCT-*) output. Discovery-composer (`composition`/PSC-*) retained — it feeds `/recommendations`, not stale.
- **Phase 5 — canonical optimization contract**: ranking/NPC switched from the conservative statutory floor to the **best-supported modeled incentive** (`selected_incentive_usd`); **"conservative" is retired as a product concept** — the floor-rate figure (`npc_conservative_usd`) is now purely a reference/uncertainty field, never the ranked number. Connected the off-budget Mauritius in-kind post (~$625k) as an **NPC-level replacement-cost normalization** (`inkind_replacement_delta_usd`) — never a budget line, never QPE. Result: Mauritius baseline (not Greece) is now the global optimum for Little Utopia.
- **Phase 6 — global discovery engine**: replaced the private jurisdiction-knowledge-only filter with `app/calculators/production_discovery.py`, which examines **every implemented jurisdiction** (211, from `global_inventory.ALL_PROGRAMS` ∪ `jurisdiction_comparison.ALL_PROFILES`) and returns a full reasoned accept/reject audit + metrics — no hard-coded country list.
- **Phase 7 — production-first discovery** (current, most recent): re-oriented discovery to ask "can this production be MADE here?" before "can this jurisdiction be priced?". New `app/calculators/production_requirements.py`: (a) derives structured production requirements (environments/infrastructure) from the existing `physical_requirements` (script + real-budget signals) — no fabrication; (b) an extensible keyword ontology abstracts any literal location string into reusable production categories (broad categories only, **no literal place-name matching**); (c) a jurisdiction **capability profile is kept structurally separate from its incentive profile** (geography/crew/infra fields vs. rate/doctrine fields) and matched against production requirements independent of pricing. Discovery now classifies every jurisdiction into one of three buckets — `incentive_ready` (production-capable AND priceable, enters optimization), `capability_only` (production-capable, incentive model pending — **retained and visible**, never silently discarded), `rejected` (capability mismatch or no data). See §3 below for runtime numbers.

---

## 2. Repository / branch / runtime (frozen)

| Item | Value |
|---|---|
| Repo root | `/Users/Suraj/cineglobe-frametax/frametax2` |
| Branch | `claude/audit-frametax-features-NZcX5` |
| Local HEAD | see git log (Phase 7 production-first discovery closeout, this session) |
| Remote HEAD | matches local (`git ls-remote` via SSH) |
| Working tree | clean |
| Backend path | `frametax2/backend` |
| Frontend path | `frametax2/frontend` |
| Python env | `backend/.venv/bin/python3` = **3.12.13** (bare `python3` = system 3.9, cannot import models — always use venv) |
| Backend port | `8010` (`api.js` → `127.0.0.1:8010/api/v1/cineglobe`) |
| Frontend port | Vite default `5173` |
| Database | Postgres configured but **UNREACHABLE** in this env (no `frametax` role); served pipeline is in-memory, never touches DB |
| Canonical served routes | `/api/v1/cineglobe/{production,package,recommendations,structures,legal,economics,people,facts,scenarios}` |
| Other mounted routers | `optimization.py` (parametric: `/gap-analysis`,`/generate-structures`,`/maximize`,`/recommendations`,`/travel-cost`); `structures.py` (DB-backed `run_full_analysis`, **not runtime-used**) |
| Recovered script/Drive source | "THE LITTLE UTOPIA" Google Drive folder — synopsis + opening scenes + look book (NOT a full page parse); confirmed facts only |
| Budget source | real Movie Magic PDF → `app/data/little_utopia_real_budget.py` (44 accounts) |
| People sources | `app/data/little_utopia_people.py` (writer GB, director AU, lead cast GB, producer UNKNOWN) |
| FX source | `FX_RATE_SNAPSHOTS` in `production_normalization.py` (live + 1M/6M/12M, manual point-in-time snapshot) |
| Travel source | `travel_model.py` (LA/NYC/London/Toronto home bases + fallbacks) |
| Executable (incentive_ready) jurisdictions | **MU, MT, IE, GR** (4 of 211 examined) |
| Capability-only (incentive pending) jurisdictions | **BE, CY, DE, ES, FR, HR, IT** (7) — production-capable, no priceable incentive model yet; retained, never discarded |
| Production-capable total | **11 of 211** examined jurisdictions (Little Utopia requires marine_filming + open_water_filming; HU rejected on genuine capability mismatch) |
| Test result | **2967 passed, 1 skipped** (venv) |

---

## 3. Currently SERVED engine ownership (runtime call graph)

Served pipeline (`little_utopia_state._build_state`, confirmed at runtime this session):
`build_jurisdiction_graph → build_little_utopia_real_register → resolve_program_rate → build_production_package → discover_all_opportunities → compose_production_structures → generate_production_recommendations → compose_candidate_structures → rank_production_structures → LegalEngine → _build_structuring_advisory`.

| Capability | Current runtime owner | Alt implementations in repo | Alt connected? | Unique to alt | Evidence |
|---|---|---|---|---|---|
| Budget ingestion | `app/ingestion/budget_parser.py` (Movie Magic → `little_utopia_real_budget.py`) | — | — | — | 44 accounts in served register |
| Script/package intelligence | `production_package_intelligence.build_production_package` | — | — | — | served `_build_state` |
| Qualification | `qualification_derivation` + `qualification_model.build_little_utopia_real_register` | — | — | — | 44-account register |
| Legal/evidence | `legal_engine.LegalEngine` + `legal_authority_acquisition` | — | — | — | `/legal` |
| Cultural + threshold qualification | `production_recommendation_engine` (relevance + gates) | — | — | — | served `_build_state` |
| Treaty evaluation | `treaty_engine` (+ composer `_treaty_compositions`) | `optimization/structure_generator` (`treaty_coproduction`, parametric) | Yes (parametric router) | parametric co-pro enumeration | `PSC-FR-MU` composes on election |
| Opportunity discovery | `opportunity_discovery.discover_all_opportunities` | `optimization/qualification_gap_engine` | Yes (opt router) | gap analysis view | opp types at runtime |
| Production structuring advice | **`structuring_advisor` (NEW: connected)** | `production_recommendation_engine` (different layer) | Yes (served) | HOW-to-structure (SPV/in-kind/routing) | `/economics.structuring_advisory`, 6 recs |
| Structure enumeration | `production_structure_composer.compose_production_structures` | `optimization/structure_generator`, `enumerate_structures`, `generate_structure_scenarios` | generator/enumerate: yes (opt router); scenarios: **no** | parametric co-pro types; multi-program stacking combos | composer serves `/structures` |
| Account/component routing | **`structuring_advisor.routing_decisions` (NEW)** | — | served | routing seed (component→jurisdiction) | `routing_decisions` at runtime |
| Qualification registers | `qualification_model` (single baseline register) + `build_little_utopia_register_for_jurisdiction` (per-jurisdiction, relocation) | — | — | — | `/economics.alternative_jurisdictions` |
| QPE | register QUALIFIES sum (served) | — | — | — | `verified_cash_qpe_usd` |
| Incentives | `program_rate_rules.resolve_program_rate` | — | — | — | served rate resolution |
| Travel | `production_normalization` + `travel_model` | `optimization` router `/travel-cost` | Yes (opt router) | standalone travel endpoint | `/economics.normalized_structures` |
| FX | `production_normalization.fx_rate_snapshot` | — | — | — | `/economics.fx_horizons` |
| In-kind | `mauritius_economics` in-kind post model | — | — | — | `/economics.inkind_post_options` |
| Grants/funds | `little_utopia_state.build_available_funds` (+ `fund_economics_model`) | `optimization/structure_generator` (`grant_stack`) | Yes (opt router, parametric) | parametric grant stacks | `/economics.available_funds` |
| Stacking | `build_available_funds.stacking_by_jurisdiction` (relationships only) | `optimization/stacking_rules`, `apply_stacking_adjustments`, `generate_structure_scenarios` | rules: opt-pkg internal; adjustments/scenarios: **no** | full stacking math + combos | IE 24 / GR 1 edges served |
| Economics | `mauritius_economics` + `production_normalization` | — | — | — | `/economics` |
| Scenarios | `production_scenario_engine.compose_candidate_structures` | `generate_structure_scenarios` (disconnected), `production_structure_composer` | scenarios file: **no** | 1/2/3-program stack ranking | served `scenario_structures` |
| Ranking | `rank_production_structures` | `optimization/score_structures`, `maximization_engine` | maximize: yes (opt router) | parametric maximization | served `scenario_ranking` |
| Recommendations | `production_recommendation_engine` (139 recs) | `structuring_advisor` (HOW-to), `optimization/recommendation_engine` | advisor: served; opt: yes (opt router) | producer structuring advice; parametric recs | `/recommendations` |
| Explainability | per-object fields (`authority_reference`/`evidence_reference`/`confidence`; composer constraints; advisor `published_support`/`audit_risk`) | — | — | — | runtime-confirmed on `PSC-FR-MU`, advisor recs |
| API serialization | `cineglobe.py` payload builders (+ `_serialize_structuring_advisory` NEW) | `optimization.py`, `structures.py` serializers | Yes (own routers) | parametric/DB payloads | `/economics` serves advisory |

---

## 4. Overlapping engines requiring other-account comparison

Capability matrix (NOT a ranking — each row is a distinct implementation):

| Module | Data model | Served? | Unique capability | Hardcoded/demo | Production-safe parts |
|---|---|---|---|---|---|
| `production_structure_composer.py` | real register + opportunities | **YES** | register-grounded pricing, treaty/fund/stack composition, honest `priceable_pct` | none | whole module |
| `structuring_advisor.py` | generic params (now state-derived) | **YES (new)** | HOW-to-structure advice: SPV, in-kind FMV, routing, EDB rulings, audit risk | prose still LU-specialized (amounts/gating generic) | inputs layer, gating, routing_decisions |
| `production_scenario_engine.py` | register + opportunities | **YES** | candidate-structure scenarios + notes | none | whole module |
| `generate_structure_scenarios.py` | flat line-items + program list | no | all legal 1/2/3-program **stacking combinations**, ranked | needs full input assembly | stacking-combo generator |
| `optimization/structure_generator.py` | parametric (codes + flat budget) | yes (opt router) | co-pro types: `dual_country`/`majority_minority`/`multi_party`/`split` | `budget × rate` only, not register-grounded | structure-type taxonomy |
| `optimization/optimizer.py` | parametric | **no** (no external caller) | end-to-end parametric optimize loop | parametric | orchestration shape |
| `run_full_analysis.py` | **DB rows** | connected via `structures.py` but **DB unreachable** → not runtime-used | full analysis + stacking math persisted | DB-shaped inputs | stacking math |
| `optimization_engine.py` | register + risk cases | **YES** (used by composer + state) | `RiskCase` math, financing bridge | none | whole module |

**Duplicated capabilities across the above:** structure enumeration (composer vs structure_generator vs generate_structure_scenarios), stacking (build_available_funds vs stacking_rules vs generate_structure_scenarios vs apply_stacking_adjustments), recommendations (production_recommendation_engine vs structuring_advisor vs optimization/recommendation_engine), ranking (rank_production_structures vs score_structures vs maximization_engine).

**Incompatible data models:** register-grounded (composer, scenario_engine, optimization_engine) vs parametric flat-budget (optimization/*) vs DB-row (run_full_analysis). Slug-convention mismatch persists in stacking (`mt_mfc_cash_rebate` vs executable `mt_mfc_rebate`).

**Keystone gap (unchanged):** no budget-allocation model → register-grounded co-production/split pricing blocked (`priceable_pct` caps at 0.5). `structuring_advisor.routing_decisions` is the seed but not yet an allocator.

---

## 5. What to check in the OTHER Claude account before choosing canonical ownership

The other account may hold implementations not present here. **Before declaring any engine canonical, inspect there for:**
- **Cloud artifacts** — any published/hosted engine builds or deploys.
- **Old UI artifacts** — earlier single-file JSX prototypes or a different frontend baseline (this repo's baseline is `frametax2/frontend`, React 19; see `UI_HANDOFF.md`).
- **Alternate repositories or branches** — other CineGlobe/FrameTax/TaxFrame/ReelIncentive repos or branches with divergent engines.
- **Unpublished engine modules** — structuring/optimizer/allocation code not committed here (especially a real budget-allocation model, or a fully-generic structuring engine with non-LU prose).
- **Prior architecture documents** — design docs that may already resolve the register-vs-parametric-vs-DB data-model split, or name a canonical structure engine.

---

## 6. Reconciliation procedure

For each overlapping capability, run this before changing anything:

1. **Locate** the other-account implementation and this repo's owner (§3/§4).
2. **Compare capability** — feature-by-feature; note what each does that the other cannot.
3. **Compare data model** — register-grounded vs parametric vs DB-row. A stronger data model usually wins, but confirm at runtime.
4. **Compare runtime use** — which is actually served/exercised (runtime evidence overrides code review).
5. **Preserve strongest proven parts** — keep the components with runtime proof + the richest correct data model; salvage unique capabilities from the others (e.g. stacking combos, co-pro taxonomy, allocation model if the other account has one).
6. **Choose ONE canonical owner** per capability.
7. **Adapt/deprecate alternatives ONLY after verification** — never before both sides are inspected and the canonical choice is runtime-proven.

---

## 7. Explicit warning

**Do not rebuild, delete, merge, or deprecate any engine until the other account's code and artifacts have been inspected and the reconciliation procedure (§6) has been completed.** The absence of an alternative here is not evidence it does not exist elsewhere.

---

## 8. Engineering principles (permanent — apply to all future work, not just database population)

These govern how work on this repository is done, independent of which Claude account is doing it. They were formalized during the Production Knowledge Database phase but apply everywhere.

- **Repository Discovery First.** Before researching, building, or concluding that something is missing, exhaustively search the current repository state — code, tests, docs, git history, other local branches — not just conversation memory.
- **Connector First.** Treat every connected source (GitHub, configured MCP connectors, cloud artifacts) as part of the repository, not an external system to consult only after local search fails.
- **Reconcile Before Research.** Locate and read every existing artifact touching the topic at hand before doing any external research. External research exists only to verify, fill genuine gaps, resolve contradictions, or update superseded law/facts — never to rebuild what's already recorded.
- **Knowledge Reconciliation.** When external research surfaces a correction or refinement, propagate it to every repository artifact that already relies on the same source or claim — not just the one file you started in. A same-source refinement is not a Material Discrepancy; reconcile it. A genuine conflict between sources is a Material Discrepancy; preserve it (see below).
- **No Duplicate Engineering.** Creation is the last resort, not the first. If an equivalent artifact already exists (even partial or stale), reuse or reconcile it before building a parallel one.
- **Runtime Evidence over Static Assumptions.** When code review and actual runtime behavior disagree, runtime evidence wins. Verify serving/pricing-path claims against the live API, not just the source.
- **Structured Unknowns over Guesses.** An unconfirmed fact is recorded as an explicit Unknown with a reason code, authority searched, and rationale — never silently guessed, never left as a bare `None` with no explanation, never asserted with false confidence.
- **Material Discrepancies remain visible until resolved.** When two trusted sources (or a source and the existing rate rule) genuinely conflict, record both positions and the conflict itself — do not silently pick one, and do not alter frozen calculation logic to make the discrepancy disappear.
- **Questions do not change project direction.** A clarifying question from the user, or an ambiguity discovered mid-research, does not itself authorize a scope change, an architecture change, or a new phase. Answer within the existing plan; only the user redirecting explicitly changes direction.
- **Repository continuously improves.** Every batch of work should leave the repository more complete and more internally consistent than it found it — coverage grows, inconsistencies get reconciled when discovered, but architecture and frozen calculation logic stay untouched absent a genuine defect.
- **Document Retrieval Escalation** (added 2026-07-26, see §0.1 for the full doctrine and worked examples). A parser limitation is not evidence that authoritative information is unavailable. Distinguish retrieval failure / parser failure / OCR-required / malformed PDF / authenticated-blocked resource / server-side TLS misconfiguration / genuine absence of a source before marking a jurisdiction SECONDARY on access grounds — "unparseable PDF" is not a completed investigation. When a byte-successful download exists on disk, try extracting it directly with a real library (e.g. `pypdf`, already a project dependency) before trusting a fetch tool's own summarization of it. When a TLS error blocks a `.gov`-type domain, check with `openssl s_client` whether it's a genuine block or a server-side missing-intermediate-certificate misconfiguration (verify error 20/21) — the latter is safe to route around for public information, the former is not.

---

## 9. Lessons learned (concise, evergreen — append here, do not create a new document)

- **Search before rebuilding.** A failed grep is not proof something doesn't exist — check other file naming patterns, other directories, git log, and git history before concluding an artifact is missing.
- **Reconnect before replacing.** If a prior session already built a subsystem (Bridge, Discovery ledger, Requirements Profiles) and it looks incomplete, look for what's already wired before writing a new version.
- **Repository reconciliation before redesign.** Stale-looking data (an old rate, a guessed field) is often one direct-source fetch away from being correctable in place — don't restructure the schema to work around it.
- **Connectors are part of the repository.** GitHub, and any other configured connector, should be searched with the same rigor as local files before declaring something absent.
- **Unknown is preferable to guessing.** A Structured Unknown with a documented reason code is more valuable — and more honest — than a plausible-looking asserted value with no evidentiary basis.
- **Preserve Material Discrepancies.** Don't let the pressure to "resolve everything" push you into silently picking a side, or into editing frozen calculation logic to make a conflict disappear. Record it, cite both positions, move on.
- **External research improves the repository, not just the current task.** A fact found while researching jurisdiction X often corrects or completes a record for jurisdiction Y, or a shared PARSED-tier artifact — check for that and propagate it before closing out.
- **A huge amount of validated work can sit uncommitted for a long time.** Before assuming the working tree is small or clean, run `git status` in full — this repository once had ~140 files and 9 subsystems' worth of already-tested work sitting uncommitted across many sessions. Commit in coherent, reviewable groups by subsystem rather than one undifferentiated blob, and verify the full test suite both before and after committing.
- **A stash is not lost work, but it is not finished work either.** If a `git stash list` turns up an entry, read its diff before assuming it's safe to drop or safe to apply — a paused reinterpretation of frozen logic (see the "default-inclusion doctrine" stash, `git stash show -p stash@{0}`) needs the regression trace it was paused for, not a blind pop.

---

## Engineering Environment Verification (2026-07-26, pre-account-transfer closeout)

Verification-only pass. No CineGlobe functionality was implemented or modified in this session — this section exists solely to confirm the next account can start working immediately without re-deriving environment state.

**Repository**
| | |
|---|---|
| Path | `/Users/Suraj/cineglobe-frametax` |
| Branch | `claude/audit-frametax-features-NZcX5` |
| HEAD | matches `origin/claude/audit-frametax-features-NZcX5` exactly (confirmed via `git log origin/... -1 --format=%H` == `git rev-parse HEAD`) |
| Working tree | clean, no uncommitted files |
| Detached HEAD | no — on a proper branch ref |
| Remote | `https://github.com/surajgohill-oss/Frametax.git` |

**Runtime**
| Check | Result |
|---|---|
| System `python3` | 3.9.6 (do NOT use — cannot import project models) |
| Backend venv `python3` | 3.12.13, satisfies `pyproject.toml`'s `requires-python>=3.11` |
| `pip check` | No broken requirements |
| Full backend test suite | **3896 passed, 1 skipped, 0 failures** |
| Node | v24.15.0 |
| npm | 11.12.1 |
| Frontend `node_modules` | installed |
| Backend server | already running and healthy at `http://localhost:8010` (`/health` → 200; `/api/v1/cineglobe/structures` → 200) |
| Frontend dev server | confirmed starts cleanly via `.claude/launch.json` config `cineglobe-frontend` (port 5173) — real served data rendered ("State of the Studio", live FX rates, Production Slate), zero console errors. Stopped after verification since it wasn't already running. |

**Connector / MCP status**
| Item | Status | Notes |
|---|---|---|
| GitHub | CONNECTED | `gh` CLI 2.96.0, authenticated as `surajgohill-oss` (repo/workflow/read:org/gist scopes). Git push/fetch also proven working directly this session. |
| Git access | CONNECTED | Multiple commits + pushes succeeded this session. |
| Local filesystem | CONNECTED | Read/write/edit confirmed throughout this session; repository confirmed writable. |
| Google Drive | CONNECTED | `search_files` succeeded and located the real project source material ("THE LITTLE UTOPIA" script folder + PDF drafts) under `surajgohill@gmail.com`. |
| Browser MCP (`mcp__Claude_Browser__*`) | CONNECTED | Started the frontend preview, read live page text, checked console, stopped cleanly. |
| Playwright MCP (`mcp__playwright__*`) | CONNECTED | `browser_navigate` succeeded against the local backend. |
| Perplexity MCP | NOT INSTALLED | No such tool is registered in this environment. |
| Figma | INSTALLED BUT NOT CONNECTED | Tool responds but requires the Figma desktop app's Dev Mode MCP Server to be enabled locally — not currently active. Not used anywhere in this repository (no Figma links/configs found), so this is a non-blocker for CineGlobe work. |
| Other MCPs (Desktop Commander, PDF tools, visualize, etc.) | AVAILABLE | Registered and reachable; not deep-tested since they aren't part of this project's core dev loop. |

**Known environment issues**
- None blocking. The only pre-existing, already-documented issues are the ones already tracked in §0.2 (10 SECONDARY jurisdictions pending further primary-source verification) and the paused `git stash` entry (a default-inclusion-doctrine reinterpretation of Mauritius QPE rules, explicitly not applied — see the Lessons Learned section above).
- Figma has no active Dev Mode bridge; irrelevant unless a future task specifically needs Figma-sourced design specs.
- Perplexity is not installed; `WebSearch` (Claude's built-in tool) and direct `WebFetch`/`curl` cover this project's research needs, as demonstrated throughout the Stage A/B database population work.

**Recommended first command for the next account**
```bash
cd /Users/Suraj/cineglobe-frametax/frametax2/backend && .venv/bin/python3 -m pytest -q
```
This confirms the environment is still in the state this document describes before starting new work. If it passes cleanly (3896/1/0), proceed directly to Globe implementation without further environment setup.

**Globe implementation readiness: YES.** Repository, runtime, and every connector actually required for CineGlobe development (GitHub, Git, filesystem, Browser MCP, Playwright MCP) are confirmed working. Google Drive is connected and can retrieve the original script source material if needed. Figma and Perplexity are not required by this project and their absence/inactivity does not block Globe work.
