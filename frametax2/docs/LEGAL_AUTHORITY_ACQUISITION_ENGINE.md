# CineGlobe — Legal Authority Acquisition Engine (LAAE)

**Status:** Approved architecture — implementation not started
**Author role:** Chief Systems Architect
**Scope:** Permanent intake pipeline feeding the Evidence Graph, Authority Score, Jurisdiction Graph, Qualification Model, Grey Areas, Levers, and (indirectly) the Optimizer — with zero changes to optimizer mathematics.
**Doctrine:** *Connectors fetch. The graph decides.* This extends the standing engine doctrine ("LLMs extract, the engine calculates") to external legal sources: no connector output ever becomes authority by virtue of retrieval — only by passing through the staging, verification, and approval pipeline defined here.

---

## 0. Position in the system

Every downstream consumer already exists and is frozen. The LAAE is purely upstream of them:

```
┌──────────────────────────── ACQUISITION LAYER (new) ────────────────────────────┐
│                                                                                 │
│  Docket (prioritized tasks) → Connectors → Staging → Verification → Approval    │
│                                                            │                    │
└────────────────────────────────────────────────────────────┼────────────────────┘
                                                             │ commit (append-only)
                       ┌─────────────────────────────────────▼─────────────┐
                       │  SOURCE-OF-TRUTH LAYER (existing, extended data    │
                       │  only): Evidence Graph · jurisdiction profiles ·   │
                       │  treaty registry · reinvestment registry           │
                       └─────────────────────────────────────┬─────────────┘
                                                             │ deterministic rebuild
                       ┌─────────────────────────────────────▼─────────────┐
                       │  PROJECTION LAYER (existing, unchanged code):      │
                       │  Jurisdiction Graph · Authority Score ·            │
                       │  Qualification register · Grey Areas · Levers      │
                       └─────────────────────────────────────┬─────────────┘
                                                             │ read-only
                       ┌─────────────────────────────────────▼─────────────┐
                       │  OPTIMIZER (frozen — no math changes)              │
                       └───────────────────────────────────────────────────┘
```

**The single most important structural rule:** the LAAE writes only to the source-of-truth layer — Evidence Graph objects (append-only) and the source registries that projections are rebuilt from. It never writes into a projection. The Jurisdiction Graph is rebuilt deterministically from source modules (settled in Phase 5A/5B); if acquisition wrote fact nodes directly into it, the next rebuild would erase them. Acquisition therefore updates the *registries the graph is built from*, attaching `EvidenceRef`s, and the existing rebuild propagates everything downstream with no new coupling.

This one rule answers most of "how does acquisition interact with X without tightly coupling": it doesn't interact with X. It improves X's inputs.

---

## 1. Connector strategy

### 1.1 Connector classes and authority mapping

Connectors are adapters behind one interface (§6, Phase 6C). Each connector is registered with a **connector class**, and each class carries a fixed, deterministic mapping to the maximum `AuthorityTier` its output may claim. A connector can never emit authority above its class ceiling; the Authority Score handles everything below it automatically.

| Class | Sources | Max tier claimable | Role |
|---|---|---|---|
| **A** | Official legislation databases; government statute/gazette portals | 1–3 (primary legislation, regulations, statutory instruments) | Terminal authority |
| **B** | Tax authority publications; film commission official guidance; administrative circulars | 4–6 (administrative guidance) | Terminal authority for guidance-level rules |
| **C** | Published rulings databases; private rulings where lawfully accessible | Ruling tiers per existing hierarchy | Precedent; terminal for ruling-resolved grey areas |
| **D** | Official treaty databases (government / depositary) | Treaty instrument tiers | Fills the treaty registry |
| **E** | Professional legal/tax research databases (Claude legal connectors, accounting research connectors) | Commentary tiers only | **Discovery and triangulation — never terminal** |
| **F** | General web search/fetch | None — not citable | Locating Class A–D documents only |

### 1.2 The discovery-vs-authority rule

Class E and F connectors are the cheapest and broadest, so they run **first** — but their output is treated as a *map*, not as *territory*. A professional-database summary that "Mauritius EDB excludes ATL costs" creates a lead whose job is to locate the Class A/B document that says so. A Rule may only become fully chained (the existing `rule_is_fully_chained` discipline) when its Citation resolves to a Class A–D document. If the primary source is genuinely unobtainable, the rule is committed at its true commentary tier — and the existing Authority Score mathematics automatically confine it to the confidence band it deserves. **We never uprate commentary; we let the existing score tell the truth about it.**

### 1.3 Least-effort ordering

Per task, connectors execute in a fixed escalation ladder, stopping at the first success:

1. Structured official database for the jurisdiction, if registered (Class A/B/D — highest quality per unit effort).
2. Claude legal / tax research connectors (Class E) to *identify* the governing instrument by name and pinpoint.
3. General search/fetch (Class F) to retrieve the identified instrument from its official domain.
4. Bespoke per-jurisdiction adapters — built **only** when docket volume for that jurisdiction justifies it (a maintenance-burden decision, made by demand data, not speculation).

This ordering makes the system viable at 100+ jurisdictions without 100+ custom integrations: the universal path is E-discovers → F-retrieves-from-official-domain → pipeline verifies, and structured Class A connectors are an optimization added per jurisdiction as heat justifies.

### 1.4 Provenance requirements (all classes)

Every fetch produces a `RawAuthorityRecord` carrying, non-optionally: connector id and class, retrieval timestamp, source URL, resolved official domain, content hash, full captured text/binary, and the docket task that triggered it. A record missing any of these cannot enter staging. This is the acquisition-side mirror of the Evidence Graph's append-only discipline.

---

## 2. Research philosophy — the core recommendation

**Recommendation: C — hybrid, with a demand-driven core and a thin freshness perimeter.** Concretely: ~90% of connector spend goes to option B (research the specific unresolved issue blocking optimization), and the remaining ~10% funds a heat-tiered heartbeat that keeps already-acquired authority from silently rotting. Option A (continuously research every jurisdiction) is rejected outright.

### Why demand-driven wins

The decisive fact is that **CineGlobe already knows exactly what it doesn't know, and what each unknown is worth.** This is the payoff of Phases 1–5B:

- Every Grey Area carries `incentive_upside_usd` and a `graph_absence_id` naming precisely which authority is missing.
- Every Jurisdiction Graph fact node carries `FactStatus` (KNOWN/UNKNOWN/ABSENT), so `get_program_unknowns()` is literally a machine-readable research agenda per program.
- Every `AbsenceOfAuthority` node records what was searched and not found.
- The optimizer's confidence weights (HIGH 0.90 / MEDIUM 0.60 / LOW 0.25, grey-area cap 0.50) make the *dollar value of certainty* computable: run the existing optimizer read-only under "as-is" vs "resolved" assumptions and diff the risk-adjusted result. No new math — two calls to frozen code.

A system that can price its own ignorance should buy knowledge in price order. Continuous whole-world research (option A) inverts this: it spends connector budget on jurisdictions no production touches, generates verification/approval workload (the true bottleneck — human approval, not fetching), and produces authority that is stale by the time it's needed anyway. At 100+ jurisdictions, option A's maintenance burden compounds; option B's burden is proportional to actual production activity, which is the only sustainable scaling law.

### Why not pure B

Pure demand-driven has two real failure modes, and the hybrid's perimeter exists solely to cover them:

1. **Silent rot.** Authority acquired for a 2026 production is cited again in 2028. Without any freshness mechanism, supersession goes undetected and the Authority Score's recency/superseded logic never gets the trigger it needs. Fix: the heartbeat (§8) — cheap revalidation of *already-held* documents, not open-ended research.
2. **Cold-start latency.** A producer asks about a never-touched jurisdiction and the system has nothing. Fix: this is not actually solved by option A either (you can't pre-research everything well); it's solved by the escalation ladder (§1.3) being fast, and by the comparison layer (Tier-1-style DISCOVERY profiles) remaining an acceptable *scenario-grade* answer while acquisition tasks spin up for anything that graduates to *commitment-grade*.

### The scenario/commitment threshold

The hybrid needs one governing distinction: **scenario-grade** questions (comparing jurisdictions, exploring structures) are served from existing knowledge at whatever confidence it has — no connector execution. **Commitment-grade** questions (a production is actually qualifying spend, executing a lever, resolving a grey area that changes a state) demand authority and generate docket tasks. This threshold is what keeps connector usage proportional to real economic decisions rather than to curiosity.

---

## 3. Acquisition lifecycle

Every unit of acquisition work is an **AcquisitionTask** moving through a strict lifecycle. States are additive to the system's existing lifecycle vocabulary (PathStatus, GreyAreaStatus) — same discipline, new object.

```
IDENTIFIED → QUEUED → FETCHING → STAGED → VERIFIED → APPROVED → COMMITTED
                │          │         │         │          │
                └──────────┴─────────┴─────────┴──────────┴──→ REJECTED / DEFERRED
                                                               (with recorded reason)
```

Parallel to the task, retrieved material moves through **CandidateAuthority** staging objects. Nothing in staging is visible to any downstream consumer. The Evidence Graph, registries, and therefore every projection see only COMMITTED material. A half-verified statute can never influence a qualification state.

### 3.1 Task origination (what creates tasks)

Tasks are generated deterministically by scanning the existing graph — no human has to ask, satisfying the minimal-human-input rule:

| Trigger | Source of truth scanned | Example (live today) |
|---|---|---|
| Open grey area | `GreyAreaStatus.OPEN` items with `graph_absence_id` | ABS-ATL-SCOPE, ABS-INKIND-FMV (Little Utopia) |
| Unknown program fact | `get_program_unknowns()` — FactStatus UNKNOWN | MU min spend, payout timing, transferability |
| Absent fact category | FactStatus ABSENT nodes | eligible production types, territorial nexus, local entity, stacking rule, application deadline — all 12 programs |
| Unverified rate | `confidence_tier` PARSED/DISCOVERY on a profile feeding real calculations | MU 40% rate (budget-evidenced, statute-unverified) |
| Reinvestment UNKNOWN | `ReinvestmentCategory.UNKNOWN` registry entries | MU |
| Treaty absence unconfirmed | Treaty-availability ABSENT facts | MU (registry has nothing; is that the world, or our data?) |
| Lever evidence gap | Levers with `evidence_bound=False` approaching APPROVED | 21-00 / 23-00 routing paths |
| Supersession suspicion | Heartbeat detects changed hash/date at source | (future) |
| Conflict opened | `mark_conflict` fired during a prior commit | (future) |

### 3.2 Deduplication ledger

Every task carries a **canonical question key**: `(jurisdiction, program_slug, fact_kind, question_hash)`. A permanent resolution ledger maps question keys to their resolving authority (or their `AbsenceOfAuthority`). A new task whose key exists in the ledger with unexpired freshness is closed instantly with the ledger's answer. This is the mechanism by which *every resolved authority improves future productions*: the second production to ask about Mauritius ATL scope pays nothing.

Absence is ledgered too, with a TTL: "searched sources X, Y, Z on date D, found nothing" is permanent knowledge worth not re-buying — until the TTL expires and a cheap re-check is warranted.

---

## 4. Prioritization — the docket algorithm

Deterministic scoring; no LLM judgment in ranking. For each task:

```
priority = (certainty_value_usd × urgency × resolvability) / cost_class
```

- **certainty_value_usd** — computed by running the *existing, frozen* optimizer twice, read-only: once as-is, once with the fact hypothetically resolved (both directions — QUALIFIES and EXCLUDED — averaged by current confidence weighting). The absolute risk-adjusted delta is the dollar value of knowing. This deliberately counts resolution to EXCLUDED as valuable: killing a false $34k upside before a producer structures around it is worth nearly as much as confirming it. Unknowns thus become priced tasks instead of silent value-reducers (the secondary objective, made mechanical).
- **urgency** — multiplier from production calendar proximity: active production in principal photography > pre-production > development > scenario-only. Scenario-only tasks get urgency ≈ 0 unless promoted (the §2 threshold).
- **resolvability** — fixed multiplier by connector class expected to answer it (Class A statute lookup ≈ 1.0; private ruling required ≈ 0.2, since that's a human/legal process the engine can only prepare, not execute).
- **cost_class** — small integer for connector expense + expected human-approval load. Approval load matters because **human review is the scarce resource**; ten cheap fetches that each need an hour of review are more expensive than one structured-database hit that auto-approves.

The docket is the top-K by priority, recomputed on graph change events and on a schedule. Everything below the auto-execution threshold waits; nothing is deleted.

**Grey Area prioritization** is not a separate system — grey areas simply dominate the docket naturally, because they carry the largest certainty deltas (state changes move whole accounts between cases) and the tightest urgency (they block commitment-grade decisions).

---

## 5. Execution policy

### 5.1 Connectors execute automatically when ALL of:

1. The task is in the docket's auto-execution band (top-K and above a priority floor).
2. The connector is Class A/B/D/F against **official public sources** (read-only, no authentication that implies engagement, no cost per query beyond configured budget) — or Class E within a configured entitlement.
3. Per-jurisdiction and global rate/budget limits have headroom.
4. The task's question key is not in cooldown (recent identical fetch failed or was rejected — exponential backoff, no hammering).
5. The system is in a worker context (§6) — never inline with a user request, never inside a calculation.

### 5.2 Connectors NEVER execute:

1. **From inside `app/calculators/`** — the no-network/no-LLM invariant of the deterministic engine is absolute and permanent.
2. **During an optimization run** — the optimizer reads a committed snapshot; acquisition may not mutate the world mid-computation.
3. **To submit anything** — no form submission, no ruling requests, no emails to authorities, no account creation. Private ruling *applications* are human legal actions; the engine's role ends at preparing the evidence package and creating a human task (existing `RULING_REQUESTED` state on grey areas is the handoff point).
4. **Against paywalled/professional sources without an explicitly configured entitlement** — no incidental cost incurrence.
5. **On scenario-grade queries** (§2) — comparison shopping never burns connector budget.
6. **When staging is saturated** — if the human approval queue exceeds a threshold, fetching more is waste; the docket pauses auto-execution and the bottleneck is surfaced. Fetch capacity must track approval capacity.
7. **To re-answer a ledgered question inside its freshness window.**

---

## 6. Orchestration and code placement

- **New package: `app/acquisition/`** — sibling of `app/calculators/`, `app/optimization/`, `app/ingestion/`. It may use connectors and LLM extraction (flagged `is_llm_extracted`, per the existing ingestion convention). `app/calculators/` remains pure and untouched.
- **Runs in the existing worker layer** (the RQ background-worker pattern already established for PDF extraction and FX refresh). Acquisition is background work by nature: docket scan jobs, fetch jobs, verification jobs, heartbeat jobs.
- **One write API into the graph:** a single `commit_candidate()` path performs all Evidence Graph writes using only existing public methods (`add_document`, `add_document_version`, `supersede_document_version`, `add_authority_source`, `add_citation`, `add_rule`, `add_evidence`, `add_absence_of_authority`, `mark_conflict`). No new Evidence Graph capabilities are needed — Phase 1 was built for exactly this consumer. Registry updates (profile fields, treaty entries, reinvestment categories) go through the same commit path so a commit is atomic across graph + registries.
- **LLM's role, precisely bounded:** locate documents (Class E/F assistance), extract candidate rule statements *with verbatim pinpoint quotes*, and summarize for the human approver. LLM output populates *staging* fields only. It never assigns tiers (deterministic class mapping), never scores (Authority Score is frozen math), never approves.

---

## 7. Verification, approval, supersession, conflict, citation lifecycle

### 7.1 Verification (automated, deterministic checks)

Three gates, all recorded on the CandidateAuthority:

1. **Provenance** — retrieved domain matches the per-jurisdiction **official domain registry** (a maintained allowlist: `edbmauritius.org`, `cnc.fr`, etc. — seeded from the `authority_url_hint` fields that already exist on every profile). Class E/F material claiming Class A/B status without an official domain fails here.
2. **Integrity** — content hash recorded; document complete (not a fragment/redirect); publication date and version identifiers extracted; language identified.
3. **Interpretation** — every candidate Rule statement carries a verbatim quote and pinpoint citation into the captured document, mechanically checkable (the quote must literally appear in the captured text). LLM paraphrase without a locatable quote cannot pass.

### 7.2 Approval (impact-classed, human where it matters)

| Impact class | What it changes | Gate |
|---|---|---|
| **1 — Corpus** | New document/version in the graph; no rule, no fact, no state changes | Auto-approve after verification |
| **2 — Facts** | Registry fact promotions (UNKNOWN→KNOWN min spend, cap, timing…), new Rules not bound to any qualification state | Human approval, lightweight (approve/reject with reason) |
| **3 — States** | Resolves a grey area, changes any qualification state, binds a lever's evidence, changes a reinvestment category | Human approval **plus** mandatory passage through the existing state-change machinery: `resolve_grey_area()` with a fully-chained rule, `apply_grey_area_resolution()`, lever lifecycle gates. The LAAE never has its own path to a state change. |

This is the **two-key rule**: machine verification is one key; for anything touching money-bearing state, a human is the second. It also caps maintenance burden honestly — Class 1 volume can scale freely; Class 2/3 scale with human capacity, and §5.2(6) makes that constraint self-regulating.

### 7.3 Supersession

Reuses Phase 1 mechanics wholesale. When a fetch (heartbeat or task-driven) finds a newer version of a held document: stage the successor → on approval, `supersede_document_version()` creates the new version and the SUPERSEDED_BY edge (never mutating the old). Then a deterministic **re-score sweep**: every Rule/Recommendation citing the superseded version is re-scored (the existing 0.5× superseded penalty does the demotion automatically); any that drops a confidence band opens a Class 2/3 re-approval task, and any qualification state that depended on it is flagged — states are never silently downgraded, but the humans who must ratify the downgrade are told immediately.

### 7.4 Conflict resolution

Acquisition **never picks winners**. When a commit would contradict held authority: commit both, `mark_conflict()`, and open a resolution task. The existing hard cap (score ≤ 60 under open conflict) immediately and automatically communicates the situation to every consumer — grey areas stay open, confidence stays ≤ MEDIUM, the optimizer's risk-adjusted case self-protects. Resolution precedence, applied by a human with engine-prepared analysis: (1) higher AuthorityTier governs — the settled "strongest tier governs" rule; (2) same tier → later-in-time and more-specific instrument; (3) genuinely irresolvable → this *is* a grey area; route it into the grey-area machinery (possibly a ruling request) rather than inventing a fourth mechanism.

### 7.5 Citation lifecycle

```
PROPOSED (staging) → ACTIVE (committed, chain intact)
                       ├→ STALE   (cited version superseded; valid for historical evaluation —
                       │           existing historical-evaluation flag already supports this)
                       ├→ RETIRED (instrument repealed/replaced; successor citation linked)
                       └→ BROKEN  (source no longer retrievable at recorded URL; integrity alarm —
                                   content hash + captured full text mean the *evidence* survives;
                                   only the live link is broken. Repair task opened.)
```

Citations are never deleted (append-only discipline). BROKEN is why full-text capture at fetch time is non-optional: CineGlobe's evidence cannot depend on the internet continuing to host it.

---

## 8. Freshness — jurisdiction heat model

Freshness spend follows a three-tier heat model, assigned automatically from production activity:

| Tier | Definition | Policy |
|---|---|---|
| **HOT** | Jurisdiction with a production in active development → delivery | Revalidation of load-bearing documents on a short TTL (~30 days) and before any commitment-grade decision; monitoring of the official domain registry for that jurisdiction |
| **WARM** | Active comparison set (Tier-1-style), or production likely | Quarterly heartbeat: hash/date re-check of held documents only — no new research |
| **COLD** | Everything else | Annual hash/date re-check of held documents; otherwise purely demand-driven |

The heartbeat re-checks *what we hold*; it never expands scope. Recency already feeds the Authority Score's 10% recency dimension, so freshness degradation is visible in every downstream score without new math. At 100+ jurisdictions the steady-state cost is: HOT effort ∝ active productions (a handful), WARM ∝ comparison sets (tens of documents), COLD ∝ corpus size × once a year — sustainable by construction.

---

## 9. Interaction map (deliberately boring)

| System | LAAE interaction | Coupling mechanism |
|---|---|---|
| Evidence Graph | Sole append-only write target, via existing public API | `commit_candidate()` only |
| Authority Score | **None.** Scores recompute over committed graph | Read-only consumer of graph |
| Jurisdiction Graph | **No direct writes.** Registries updated → projection rebuilds; FactStatus promotions fall out | Existing rebuild |
| Requirement/Restriction nodes | Same — fact promotions arrive via registry + rebuild; `EvidenceRef` hooks (built in 5B) get populated | Existing `EvidenceRef` |
| Grey Areas | Resolution *proposals* only; resolution executes through existing `resolve_grey_area()` | Existing function, unchanged signature |
| Levers | Evidence packages for `evidence_bound`; lifecycle gates unchanged | Existing lever fields |
| Reinvestment | Registry category promotions (UNKNOWN → evidenced category) with citation; UNKNOWN ≠ NOT_PERMITTED preserved — only Class 3 approval can move a category | Existing registry |
| Treaties | Registry additions/confirmations; confirmed-absence recorded as `AbsenceOfAuthority` (distinct from unloaded, per 5B) | Existing registry |
| FX / labor / travel normalization | Provenance only: dated official source documents committed as evidence behind existing constants. No math changes | Evidence Graph refs |
| Optimizer | **Zero.** Benefits arrive exclusively as confidence upgrades flowing through existing weights | None |

---

## 10. Implementation phases for Sonnet

Strict phase discipline; each phase independently testable, committed, and verified against the full suite with zero regressions; no connectors touch the network until 6F.

- **Phase 6A — Acquisition data model + docket.** `app/acquisition/` package: AcquisitionTask lifecycle, canonical question keys, resolution ledger, deterministic priority scoring (certainty value computed via read-only double-run of the frozen optimizer). Task generation by scanning grey areas / unknowns / absences / unverified tiers (all triggers in §3.1). Fixture-driven tests; no network, no connectors. Prove the docket ranks Little Utopia's two grey areas and MU's unknowns sensibly.
- **Phase 6B — Staging + commit pipeline.** CandidateAuthority states, three verification gates (provenance/integrity/interpretation with mechanical quote-checking), impact-class approval model, `commit_candidate()` using only existing Evidence Graph public methods, supersession re-score sweep, conflict intake via `mark_conflict`. Fed entirely by fixture payloads simulating connector output.
- **Phase 6C — Connector abstraction.** Adapter interface, connector registry with class→tier ceiling mapping, official domain registry (seeded from existing `authority_url_hint` fields), provenance-complete `RawAuthorityRecord`, rate/budget/cooldown enforcement, escalation ladder. One fully-featured mock connector; still no network.
- **Phase 6D — Execution policy + orchestration.** Auto-execution band, all seven never-execute rules as enforced code, worker-layer job wiring, staging-saturation backpressure, heat-tier assignment from production activity.
- **Phase 6E — Freshness + citation lifecycle.** Heartbeat jobs (hash/date re-checks), STALE/RETIRED/BROKEN transitions, ledger TTLs, absence re-verification.
- **Phase 6F — First live connector, proving case.** One official-source connector (Mauritius EDB / Mauritius legislation portal) run end-to-end against the real docket: attempt to resolve the MU rate verification, min-spend unknown, and prepare evidence packages for ABS-ATL-SCOPE and ABS-INKIND-FMV. Success criterion: material reaches APPROVED staging with a human gate — and Little Utopia's optimizer outputs change **only** when a human ratifies a Class 3 state change through the existing resolution machinery.

Each phase ends with the standing ritual: targeted tests + full backend suite, commit, push, stop.

---

## 11. Settled decisions (do not reopen)

1. Hybrid research philosophy: demand-driven core, heat-tiered freshness perimeter, scenario/commitment threshold gating all connector spend.
2. Acquisition writes to source-of-truth layer only; projections are never written to.
3. Connector class → tier ceiling is a fixed deterministic table; commentary can discover but never terminate a chain that primary authority could.
4. Two-key rule: no machine-only path to any qualification-state, lever-evidence, or reinvestment-category change.
5. All state changes route through the existing machinery (`resolve_grey_area`, lever gates); the LAAE has no private state-change path.
6. `app/calculators/` remains network-free and LLM-free, permanently.
7. Full-text capture at fetch time is mandatory; evidence must survive link rot.
8. Absence of authority is ledgered, permanent (with TTL), and as first-class as presence.
9. Optimizer mathematics untouched — its only relationship to the LAAE is receiving better-evidenced inputs.
