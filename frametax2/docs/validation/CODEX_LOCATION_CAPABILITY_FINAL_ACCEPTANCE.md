# Codex Location-Capability Final Acceptance

Date: 2026-10-06
Audited implementation: `de3e8b1972e529588b46fcf537162079434faaff`
Branch: `claude/global-optimizer-remediation`
Disposition: **NOT ACCEPTED**

## Gate summary

| Gate | Result | Evidence |
|---|---|---|
| Census integrity | PASS | 114 jurisdictions × 10 categories = 1,140 unique cells; no duplicates or omissions; CSV, summary JSON, builder, and runtime owner agree. |
| Evidence / derivation | FAIL | Natural Earth is mislabeled as peer-reviewed evidence; at least three rainforest positives do not prove a present-day filmable rainforest; the subnational spatial match also assigns the Nova Scotia Joggins property to New Brunswick. |
| Unresolved-neutral exhaustion | FAIL | Every one of the 235 neutral rows explicitly says national/regional film-commission and agency pages were not queried per cell. The task expressly prohibited accepting that as exhaustion. |
| Canonical wiring | PASS | One runtime owner feeds capability profiles and production fit. All 13 controls persist per project, alter effective fingerprint facts, trigger one evaluation only on a meaningful change, and are served to the shared UI fields. No parallel frontend capability truth was found. |
| Hard / soft semantics | PASS | Supported hard requirements confirm; verified hard denials are weak/not-suitable; unresolved hard requirements are conditional; soft unknown/denial remains disclosure-only; service-only routing ignores physical needs; physical routing uses physical legs. |
| Economic non-regression | PASS | Parent/current order-normalized hashes match exactly for all four projects across scenario IDs, economic IDs, QPE, incentive, NPC, participants, and program segments. |
| Focused tests | PASS | 52 backend wiring/census tests, 5 corrected scenario-accounting tests, and 3 frontend presentation tests passed. The five old assertions were independently reproduced as pre-existing failures; the updated accounting correctly includes curated plus music-suppressed scenarios. |
| Browser acceptance | FAIL | FVD Workspace, complete 217-row panel, and Inspector agreed in the direct browser, but the Project Globe overloaded the browser-control channel before a complete independent whole-polygon hover and four-project surface matrix could be completed. Claude's prior browser report is not independent proof. |

## 1. Independent census reconciliation

- Jurisdictions: **114**
- Categories: **10**
- Rows / unique keys: **1,140 / 1,140**
- Missing / duplicate: **0 / 0**
- Terminal totals: **819 supported, 86 not supported, 235 unresolved neutral**
- Evidence tiers: **551 intergovernmental dataset, 320 `PEER_REVIEWED_OPEN_DATASET`, 31 government dataset, 3 government agency page, 235 unresolved/no tier**
- Runtime treatment: **819 provision, 86 affirmative denial, 235 neutral**
- Source-reference counts: GLC-SHARE 213; Köppen-Geiger 288; Natural Earth 282; UNESCO 236; Natural Earth populated places 76; World Bank/FAO forest 65; UN WUP 207; Australian NHL 4; US NPS 27; NSW NPWS 1; Visit Iceland 1; NZFC 1.

The committed CSV equals the builder output and runtime records, and the summary JSON equals a fresh builder summary. Raw research downloads are not imported by runtime and are not committed application assets.

## 2. Material evidence and derivation defects

### EVD-001 — Natural Earth is not a peer-reviewed scientific authority

The source records `NE` and `NE_PP` use the tier `PEER_REVIEWED_OPEN_DATASET`. Natural Earth is an open/public-domain geospatial dataset maintained by the Natural Earth community/NACIS; the implementation does not establish peer review. The explicit acceptance rule required open geospatial evidence to be distinguished from peer-reviewed scientific evidence. The combined tier is therefore misleading. **164 verified cells rely solely on `NE`/`NE_PP`**, so this is material, not cosmetic.

Required result: use an honest `OPEN_GEOSPATIAL_DATASET` tier (or equivalent), retain Köppen-Geiger as peer-reviewed scientific evidence, and ensure the UI/source summary does not imply government, film-agency, or peer-reviewed authority for Natural Earth.

### EVD-002 — fossil evidence is presented as a current rainforest capability

These supported cells rely on UNESCO's Joggins Fossil Cliffs description mentioning a prehistoric rainforest:

- `CA / jungle_rainforest`
- `CA-NB / jungle_rainforest`
- `CA-NS / jungle_rainforest`

That proposition does not establish a present-day rainforest filming environment. In addition, Joggins is in Nova Scotia; the derivation's `0.05` degree point-buffer assigns it to New Brunswick as well. These are unsupported positives under the UI proposition being served.

Required result: exclude palaeontological/historical references from present-environment keyword matches; prevent buffered point assignment across an admin-1 boundary; then re-derive every affected UNESCO keyword cell and add regression fixtures.

### EVD-003 — national geometry and UNESCO scope are inconsistent

The derivation clips `FR` to metropolitan France in `geoms.py`, but UNESCO matching uses national ISO membership rather than the clipped polygon. `FR / jungle_rainforest` is therefore supported by the Réunion property `Pitons, cirques and remparts of Reunion Island`, outside the deliberately selected geometry. The same scope rule must be used by geometry-derived and UNESCO-derived evidence.

Required result: either define and document the program-relevant national territorial scope consistently, or spatially constrain UNESCO properties to the same geometry. Recheck all clipped/overseas national jurisdictions, not only France.

## 3. Unresolved-neutral exhaustion

All **235** unresolved rows contain this admission: `National/regional film-commission and agency location pages were not queried per cell`. They are neutral at runtime, which is safe, but the declared evidence sequence is not exhausted. No unlimited research is required; remediation is the exact bounded residual set below, using repository evidence first and targeted official sources only where still missing.

Exact residual cells, grouped by jurisdiction:

```text
AE-AD: historic_old_world, mountains_alpine, rural_countryside, small_town_suburban, snow_arctic
AE-DXB: historic_old_world, rural_countryside, small_town_suburban, snow_arctic
AL: desert_arid, island_tropical, jungle_rainforest
AT: desert_arid, jungle_rainforest
AU-QLD: snow_arctic
AU-SA: forest_woodland, jungle_rainforest, snow_arctic
BE: island_tropical, jungle_rainforest, snow_arctic
BG: desert_arid, island_tropical, jungle_rainforest
CA-AB: desert_arid, historic_old_world
CA-BC: desert_arid, historic_old_world, jungle_rainforest, rural_countryside
CA-MB: desert_arid, historic_old_world, island_tropical, mountains_alpine, small_town_suburban
CA-NB: historic_old_world, rural_countryside, urban_major_city
CA-NL: desert_arid, rural_countryside, urban_major_city
CA-NS: mountains_alpine, rural_countryside, small_town_suburban
CA-ON: desert_arid, historic_old_world, island_tropical, rural_countryside
CA-QC: desert_arid
CA-SK: desert_arid, historic_old_world, mountains_alpine, urban_major_city
CH: desert_arid, jungle_rainforest
CR: desert_arid, historic_old_world
CY: desert_arid, historic_old_world, jungle_rainforest, snow_arctic
CZ: jungle_rainforest
DE: desert_arid, jungle_rainforest
DK: jungle_rainforest, mountains_alpine
DO: desert_arid, snow_arctic
EE: mountains_alpine
EG: snow_arctic
ES: jungle_rainforest
FI: desert_arid
FJ: mountains_alpine, snow_arctic
FR: desert_arid
GB: desert_arid, jungle_rainforest
GE: desert_arid, island_tropical
GH: mountains_alpine
GR: desert_arid, jungle_rainforest
HR: jungle_rainforest
HU: jungle_rainforest
IE: historic_old_world, jungle_rainforest, mountains_alpine, snow_arctic
IL: island_tropical, jungle_rainforest
IS: forest_woodland, historic_old_world, jungle_rainforest, rural_countryside
IT: desert_arid, jungle_rainforest
JO: forest_woodland, historic_old_world, island_tropical, jungle_rainforest, snow_arctic
JP: desert_arid
KR: desert_arid, jungle_rainforest
KZ: historic_old_world, jungle_rainforest
LT: island_tropical, mountains_alpine
LU: jungle_rainforest, snow_arctic, urban_major_city
LV: island_tropical, mountains_alpine
MA: island_tropical, jungle_rainforest
ME: desert_arid, island_tropical, jungle_rainforest
MK: desert_arid, historic_old_world, jungle_rainforest
MN: historic_old_world
MT: desert_arid, jungle_rainforest, mountains_alpine, snow_arctic
MU: historic_old_world, mountains_alpine, snow_arctic
MX: snow_arctic
MY: desert_arid, snow_arctic
NL: jungle_rainforest, mountains_alpine, snow_arctic
NO: historic_old_world, jungle_rainforest
NZ: desert_arid, jungle_rainforest
PA: desert_arid
PH: snow_arctic
PL: desert_arid, island_tropical, jungle_rainforest
PT: jungle_rainforest, snow_arctic
QA: historic_old_world, island_tropical, mountains_alpine, snow_arctic
RO: desert_arid, island_tropical, jungle_rainforest
RS: jungle_rainforest
SA: forest_woodland, jungle_rainforest, snow_arctic
SE: desert_arid, jungle_rainforest
SG: historic_old_world, mountains_alpine, rural_countryside, small_town_suburban
SI: desert_arid, historic_old_world, island_tropical, jungle_rainforest
SK: desert_arid, jungle_rainforest
TH: snow_arctic
TT: historic_old_world, mountains_alpine
TW: desert_arid, historic_old_world, snow_arctic
UA: desert_arid, jungle_rainforest
US-AL: jungle_rainforest, snow_arctic
US-AZ: jungle_rainforest, rural_countryside
US-CA: jungle_rainforest
US-CO: jungle_rainforest
US-CT: island_tropical, jungle_rainforest, rural_countryside, small_town_suburban
US-GA: jungle_rainforest, snow_arctic
US-HI: desert_arid
US-IL: jungle_rainforest
US-KY: jungle_rainforest, snow_arctic
US-LA: jungle_rainforest, mountains_alpine, snow_arctic
US-MA: jungle_rainforest, rural_countryside
US-MD: jungle_rainforest
US-MN: mountains_alpine
US-MS: jungle_rainforest, snow_arctic, urban_major_city
US-NC: jungle_rainforest
US-NM: jungle_rainforest
US-NV: jungle_rainforest, rural_countryside
US-NY: jungle_rainforest
US-OK: desert_arid, jungle_rainforest, snow_arctic
US-OR: jungle_rainforest
US-PA: island_tropical, jungle_rainforest
US-PR: mountains_alpine, snow_arctic
US-RI: jungle_rainforest, mountains_alpine, rural_countryside, small_town_suburban
US-SC: jungle_rainforest, snow_arctic
US-TN: jungle_rainforest
US-TX: jungle_rainforest, snow_arctic
US-UT: jungle_rainforest, rural_countryside
US-VA: jungle_rainforest
UY: island_tropical, jungle_rainforest, snow_arctic
UZ: jungle_rainforest
ZA: historic_old_world, jungle_rainforest, snow_arctic
```

## 4. Runtime and fit verification

The traced path is canonical and complete:

`ProductionDetails location chip` → `POST /api/v1/cineglobe/projects/{id}/locations` → project-scoped `ProjectLocationRequirement.override` → `build_physical_requirements` / `derive_production_requirements` → `physical_requirement_fingerprint_facts` → `location_capability_cells` → `jurisdiction_capability_profile` → `classify_jurisdiction_fit` / `classify_entry_fit` → served `production_fit_*` fields → Single-Jurisdiction panel, Workspace, Globe adapter/hover, and Inspector.

The endpoint compares before/after effective facts, calls `evaluate_project` once only when they change, and calls it zero times on an identical effective save. Explicit jurisdiction exclusion uses a separate control/path. The frontend renders served evidence and does not contain capability classifications.

Current served fit counts independently calculated from the acceptance DB, without regeneration:

| Project | Curated | Music-suppressed | Strong | Workable | Weak | Unknown |
|---|---:|---:|---:|---:|---:|---:|
| Little Utopia | 376 | 0 | 196 | 37 | 143 | 0 |
| F#K Valentine's Day | 238 | 443 | 126 | 37 | 75 | 0 |
| Bad Hombres | 61 | 260 | 0 | 0 | 0 | 61 |
| Lips Like Sugar | 247 | 413 | 0 | 104 | 35 | 108 |

The 217-row Single-Jurisdiction universes also reconcile exactly with the served category counts. Texas, Saskatchewan, and Saudi remain present. FVD's direct browser panel showed all 217 jurisdictions and its Inspector showed the same Greece fit/evidence as the Workspace card.

## 5. Economic non-regression

A fresh read-only parent/current comparison ran `build_production_and_structures` from `de3e8b1^` and `de3e8b1` against the same acceptance database. Rows were normalized by `structure_id` so permitted fit-aware ordering changes did not create false differences.

| Project | Complete rows | Parent/current economic hash | Result |
|---|---:|---|---|
| LU | 376 | `1f1764119c8f6a11…` | identical |
| FVD | 681 | `c1eed59c8cde8482…` | identical |
| BH | 321 | `1ddd60b2fc883175…` | identical |
| LLS | 660 | `68eeeb6051dea60d…` | identical |

The snapshot included structure ID, economic identity, gross budget, QPE fields, selected incentive, adjusted NPC, participants, and each segment's jurisdiction/program/QPE/incentive. No project evaluation was invoked.

## 6. Test-correction review

The five old assertions were run against the parent code and current persisted generation and failed before the census change. The old accounting ignored music-suppressed scenarios (for example FVD counted 238 curated rows against 681 raw rows). The corrected tests include curated plus suppressed rows, require exact once-only coverage, preserve distinct economic identities and nested-participant routes, and pass 5/5. The corrections strengthen generic invariants rather than merely deleting assertions.

Focused current results:

- backend census + location/content wiring: **52 passed**
- corrected scenario-accounting nodes: **5 passed**
- frontend capability-evidence presentation: **3 passed**

## 7. Browser evidence and limitation

Verified directly against frontend `localhost:5173`, backend `127.0.0.1:8010`, and database `frametax2_claude_optimizer_acceptance_20260919`:

- FVD rendered real API data and the full 217-row jurisdiction panel.
- Texas and Saskatchewan remained visible as conditional alternatives; Saudi remained visible.
- FVD Greece Workspace and Inspector agreed on Strong fit, physical leg `GR`, supported coastal/rural/urban signals, and UN WUP evidence.
- No project facts were changed.

Not independently completed: the four-project Project Globe whole-polygon hover matrix and fresh console/network matrix. The Project Globe's very large state payload caused the browser-control session to time out. This is an acceptance failure, not proof of a runtime defect; it must be rerun after the evidence remediation with a bounded per-page browser plan.

## Complete replacement Claude remediation prompt

```text
PLATFORM: Claude Code — existing CineGlobe remediation worktree
EFFORT: High
MODE: Bounded location-capability evidence remediation and final runtime/browser closeout

WORKTREE:
/Users/Suraj/cineglobe-claude-global-optimizer-remediation/frametax2

BRANCH:
claude/global-optimizer-remediation

REQUIRED ANCESTRY:
The current remote HEAD must contain de3e8b1972e529588b46fcf537162079434faaff and
docs/validation/CODEX_LOCATION_CAPABILITY_FINAL_ACCEPTANCE.md.

Read PROJECT_RULES.md and the Codex acceptance artifact first. Use applicable installed skills and repository memory automatically. Do not ask routine questions or stop at intermediate checkpoints. Continue through repair, focused verification, browser verification, commit, push, and remote equality unless a legitimate destructive/data-integrity blocker occurs.

OBJECTIVE

Close only the location-capability acceptance defects found by Codex. Do not reopen incentive-program research, optimizer discovery, rates, QPE, stacking, music carve-out, card design, Globe visual design, ocean/atmosphere, or ingestion.

CANONICAL-FIRST RULE

Mine current canonical repository/database evidence first. For the exact 235 residual cells in the Codex artifact, perform targeted official research only where canonical evidence remains insufficient. This is a bounded residual remediation, not a new global audit. Use current government/film-agency/environment/tourism sources or authoritative datasets. Download each structured dataset once into a temporary directory with hard timeouts. Do not commit raw downloads and do not make them runtime dependencies.

REPAIR 1 — EVIDENCE-TIER HONESTY

Separate peer-reviewed scientific evidence from open geospatial evidence. Natural Earth and Natural Earth populated places must not be labeled peer reviewed, government, or film-agency authority. Introduce an honest OPEN_GEOSPATIAL_DATASET tier (or an equally explicit name), keep Köppen-Geiger separately peer-reviewed, rebuild source summaries, and update UI evidence labels/tests. Do not weaken provenance.

REPAIR 2 — SEMANTIC FALSE POSITIVES AND SCOPE

Fix every keyword/spatial derivation that does not prove the actual current UI proposition. At minimum:
- CA/jungle_rainforest, CA-NB/jungle_rainforest, and CA-NS/jungle_rainforest may not use Joggins Fossil Cliffs' prehistoric-rainforest wording as proof of a present rainforest.
- Joggins must not be assigned to New Brunswick through a 0.05-degree boundary buffer.
- FR/jungle_rainforest may not use Réunion evidence while the FR geometry is explicitly metropolitan. Apply one documented territorial scope consistently to geometry and UNESCO evidence.

Audit all UNESCO keyword hits for historical/palaeontological wording, all admin-1 point matches near borders, and every clipped/overseas national geometry. Add deterministic regression fixtures for every corrected class, not only the named examples.

REPAIR 3 — EXACT 235-CELL BOUNDED EXHAUSTION

Use the exact residual list in the Codex artifact. For each cell, record:
- canonical sources recovered;
- targeted official sources checked;
- exact proposition found, or exact missing proposition;
- terminal supported / not-supported / unresolved-neutral result;
- honest tier, URL, publisher, version/check date, and derivation.

Do not mark a cell supported from a related fact; do not infer a negative from silence. If the bounded official sequence still cannot answer a cell, keep it AUTHORITY_UNRESOLVED_NEUTRAL with the actual sources checked. The completion gate is exhaustion and honesty, not forcing zero unresolved rows.

REBUILD AND WIRE

Rebuild the canonical module, CSV, summary JSON, ledger, and account handoff. Preserve one canonical capability owner and the existing 13-control path. Unresolved stays runtime-neutral. Do not introduce frontend capability truth.

ECONOMIC FREEZE

Do not regenerate any real project and do not alter scenario membership, structure IDs, economic identities, QPE, incentives, NPC, participants, program stacks, music suppression, or fingerprinted pricing source. Run a parent/current order-normalized read-only snapshot for LU, FVD, BH, and LLS proving all those fields identical.

FOCUSED VERIFICATION — RUN ONCE

- census/builder/runtime equality and terminal totals;
- source-tier and false-positive regressions;
- every residual cell has a documented exhausted sequence;
- all 13 controls and one-evaluation/zero-identical-save behavior;
- hard/soft/service-only/physical-leg semantics;
- five scenario-accounting tests;
- directly dependent frontend evidence tests.

No broad suite. Ordinary commands 120 seconds, individual test files 300 seconds, grouped focused tests 900 seconds. Do not rerun a green command.

DIRECT BROWSER CLOSEOUT

Use exactly one frontend at localhost:5173 and one backend at 127.0.0.1:8010 on frametax2_claude_optimizer_acceptance_20260919. Do not mutate project facts. Verify all four projects and the three Globe-bearing surfaces (Project Globe, Workspace Map, Workspace Split), including:
- LLS supported, denied, and unresolved desert examples;
- LU/FVD marine-supported and landlocked mismatch examples;
- BH no-requirements honesty;
- all 13 controls render;
- Workspace/Globe hover/Inspector exact agreement for fit, reasons, and evidence;
- Texas, Saskatchewan, Saudi, all 217 jurisdictions, and 25 co-production opportunities remain accessible;
- whole-polygon hover/click, not marker-only;
- fresh console has no app errors and application requests are 200.

Keep each page bounded: load once, verify the required representatives, then move on. Do not repeatedly reload the 35 MB state payload.

COMPLETION / PUBLISH

Update the existing census artifacts, capability ledger, handoff, and tests; commit the bounded remediation; push origin/claude/global-optimizer-remediation; verify local/remote SHA and tree equality. Do not stop for a separate audit or permission checkpoint. If a genuine agency silence remains after the declared bounded sequence, preserve it as unresolved and finish.

RETURN SHORT:
- census totals by terminal state and evidence tier
- residual cells researched / resolved / still neutral
- false positives corrected
- 13 controls wired: YES
- four-project economics unchanged: YES/NO
- focused tests
- browser matrix PASS/FAIL
- commit SHA
- pushed YES/NO
- remote equality PASS/FAIL
- remaining blocker, if any
```

## Final disposition

The runtime architecture and economic freeze are sound. The phase is **not accepted** because the authority/evidence claim is overstated, three concrete positive cells are semantically unsupported, the 235-row official-source sequence is explicitly incomplete, and the independent browser hover matrix did not finish.

Final token: `CODEX_LOCATION_CAPABILITY_NOT_ACCEPTED`
