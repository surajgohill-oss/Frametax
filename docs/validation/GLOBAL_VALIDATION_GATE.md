# Global Validation Gate — Final

Date: 2026-08-09
Supersedes: the prior `GLOBAL_VALIDATION_CLOSEOUT.md` (Codex's own self-assessed closeout, produced before
this three-engine reconciliation). That document's `NO_GO_GLOBAL_VALIDATION_INCOMPLETE` result is **confirmed
current, not stale** — the finished Codex + Gemini + Claude/Chat evidence assembled in this reconciliation
independently reproduces the same material gaps (see §H, §J below), so the prior result is re-affirmed on
fresh, cross-checked grounds rather than carried forward unexamined.

## A. Existing programs

**262**

## B. Original missing

**23** (Codex-discovered)

## C. Starting working universe

**285** (262 + 23)

## D. Original 23 — final disposition

| Bucket | Count | Identities |
|---|---:|---|
| confirmed_additions | 12 | Canada PSTC; US-NJ Garden State; US-NY Post-Production; US-NY Empire State Independent; US-OH Ohio Motion Picture; US-AR Digital Product; US-WV Film Production; US-MT MEDIA Tax Credit; Australia Producer Offset; UK Enhanced AVEC/IFTC; UAE Abu Dhabi 35++; Thailand PRD Foreign Digital Content (resolved ADD despite Gemini's duplicate call — see reconciliation) |
| already_represented | 1 | South Africa "Production/Co-production Incentive" — MERGEs into the existing `za_nfvf_rebate` record (Codex's own remediation text already implied this; not a separate program) |
| duplicates | 0 | — |
| superseded | 0 | — |
| non_economic | 0 | — |
| unsupported | 0 | — |
| unresolved | 10 | Canada-BC FIBC; Canada-Quebec PSTC; US-Missouri; UK Global Screen Fund; Germany GMPF; Colombia CINA; Spain-Canary Islands; Spain-Navarre; Spain-Basque Country (all CONFIRMED_MISSING but not yet source-complete); Netherlands High-End Series (the one TRUE_INTERPRETATION_CONFLICT) |
| other | 0 | — |
| **TOTAL** | **23** | ✓ exact |

## E. Additional post-285 discoveries

**2** (Gemini), both resolved as duplicates — **0 net-new**:

1. **Canary Islands 54%** (Spain) — duplicates Codex's own already-counted "Canary Islands Foreign Production
   Tax Deduction" discovery (same 54%/45% EUR1m-tiered figures). Already inside the 23.
2. **Hungary Base Rebate** — duplicates the existing CineGlobe record "Hungarian Tax Rebate (HIPA)"
   (`hu_hipa_rebate`), already one of the 262.

## F. Final canonical program universe

**284** = 262 (existing) + 22 (net-new distinct programs from the 23 missing discoveries; South Africa's
discovery merges into an existing row rather than adding one) + 0 (Gemini's 2 additional, both duplicates).

## G. Treaties

- Starting stored treaties: **38**
- Starting participant rows: **109**
- Confirmed current (Gemini aggregate): **20**
- Corrected/stale (Gemini aggregate): **18**
- Duplicates/superseded identified: **0**
- New material pathways discovered (Gemini): **5**
- Unresolved (Codex queues, 0 of 8 closed; 7 of 8 are P0/P1): **7**
- **Final canonical treaty/pathway count: NOT YET DETERMINABLE.** Gemini's 20/18 current/stale split could
  not be cross-validated per-record against Codex's 8 structured completion queues — neither engine's output
  shares a per-record key with the other, and Codex closed zero of its own queues. This granularity gap,
  not a disagreement, is itself one of the load-bearing NO-GO reasons.

## H. Three-engine reconciliation

- **Agreements**: 6 category-level findings (existing-program classification totals; QPE default-inclusion /
  no-SPV-alone territoriality; contingency architecture preserved; NPC/ranking-logic-correct-with-Bridge-
  export-defect; treaty/co-production candidate-generation gap; AU Location Offset hard gate)
- **Authority-resolved disagreements**: 2 (South Africa MERGE, Thailand ADD — both settled from evidence
  already in hand, no new research)
- **True interpretation conflicts**: 1 (Netherlands Film Production Incentive — High-End Series)
- **Single-engine-only material findings**: 1 (treaty per-record current/stale calls — Gemini reviewed all 38
  individually in aggregate; Codex structured but did not close any; not cross-checkable at record level)
- **Insufficient-evidence material findings**: 1 (same Netherlands item, doubles as both a conflict and an
  insufficient-evidence case)

## I. Remediation layers

Computed across all 295 reconciled records (262 existing + 23 missing + 2 Gemini-additional + 8 treaty
queues):

| Layer | Count |
|---|---:|
| DATA_ONLY | 208 |
| SCHEMA_AND_DATA | 0 |
| ENGINE_AND_DATA | 0 |
| CANDIDATE_GENERATION_AND_DATA | 0 (conceptually needed for future treaty-partner-driven structure generation once treaty data is current — no specific record required it in this pass) |
| TREATY_STRUCTURE_LOGIC_AND_DATA | 7 |
| EXCLUDE_FROM_OPTIMIZER | 70 |
| NO_CHANGE | 10 |
| **TOTAL** | **295** ✓ |

Zero items required an ENGINE_AND_DATA or SCHEMA_AND_DATA rewrite. Every confirmed correction and every
confirmed addition reuses the existing RateRule / DoctrineRecord / ProgramRequirementsProfile / SpendRule /
QPE_CAP_RULES / min_qpe_usd-gating schema — the same pattern already proven for the MU/MT/GR/GB/AU pilot and
for the GB IFTC addition (commit `21af675`). This directly validates this task's instruction not to turn
research discrepancies into engine rewrites: none of the reconciled evidence required one.

## J. P0-equivalent unresolved items

**167** existing-program items (132 P0 + 25 P1, Codex's own priority tiers — both tiers meet this task's
"can materially alter deterministic pricing/gating/NPC/ranking" bar) + **10** missing-program items + **7**
treaty queues = **184 P0-equivalent unresolved items in total**, bounded to a **19-jurisdiction** material-gap
set (Codex's own `material_gap_jurisdictions`): Australia, Canada, Colombia, Czech Republic, France, Germany,
Iceland, India, Japan, Morocco, Netherlands, New Zealand, Romania, South Africa, Spain, Thailand, United Arab
Emirates, United Kingdom, United States — plus the 4 P0 treaty queues (UK / Australia / Canada / France
bilateral-list reconciliations).

**Optimizer consequence if left unresolved**: for any worldwide (non-pilot) jurisdiction in this list, a
production's served rate, cap, minimum-spend gate, or treaty-partner candidate could be wrong in either
direction (overstated or understated), exactly mirroring the AU Location Offset defect already found and
fixed for the pilot. These jurisdictions collectively represent the large majority of global production
volume (all of the US, Canada, UK, Germany, France, Australia, Japan, India, South Africa) — this is not a
long-tail concern.

## GLOBAL VALIDATION GATE

# **NO_GO_VALIDATION_NOT_CLOSED**

184 P0-equivalent unresolved items (167 existing-program + 10 missing-program + 7 treaty queues), spanning 19
jurisdictions that together represent the large majority of global production volume, remain without
primary-authority resolution. Per this task's own gate criteria, these are squarely the kind of unresolved
issue that CAN materially alter candidate eligibility, QPE, incentive value, hard gates, territoriality,
stacking, NPC, ranking, or treaty/co-production candidate generation for a worldwide (non-pilot) run — this is
not academic-perfection territory, and it is not the deferred, genuinely-non-deterministic P2 fund/grant set
(62 items, correctly excluded from this gate per Codex's own triage and this task's explicit instruction).

This gate result is reached independently in this reconciliation pass, not merely adopted from Codex's own
prior self-assessment — the same underlying record counts were re-verified directly against the source JSON
in this pass, and Gemini's independent worldwide review corroborates rather than contradicts the scale of the
gap (18 of 38 stored treaties independently found stale; the earlier, contradicting 410-program Gemini claim
was independently confirmed worthless by both Codex's rejection and Gemini's own later correction).

**What IS ready and does NOT require further research**: 40 items (27 existing-program corrections + 12
missing-program additions + 1 merge) are fully authority-sourced and may proceed to Step 3 consolidated
remediation as a first, bounded batch, alongside the 8 non-economic exclusions and 62 fund/grant exclusions
already fully and correctly dispositioned. The pilot (MU/MT/GR/GB/AU) remains fully closed and is not
reopened by this gate result.

## Artifacts produced by this reconciliation

- `GLOBAL_THREE_ENGINE_RECONCILIATION.json` / `.md`
- `GLOBAL_CANONICAL_PROGRAM_DISPOSITION.json`
- `GLOBAL_CANONICAL_TREATY_DISPOSITION.json`
- `GLOBAL_REMEDIATION_INPUT.json` (supersedes Codex's own draft of the same name)
- `GLOBAL_RECONCILIATION_EXCEPTIONS.json`
- `GLOBAL_VALIDATION_GATE.md` (this file)
