# CineGlobe Production Registry

**Canonical catalog of every production and document discoverable on this Mac and in this project.**
Catalog only — no analysis, no optimization, no scenario generation, no incentive calculation.

**Ingestion criterion:** the optimizer's pipeline begins with a *parsed budget* (budget → parser → QPE → qualification → structure generation → optimization → NPC → recommendation). A production is **Ready for optimizer** only once a machine-parseable budget is ingested. Exactly one production (**The Little Utopia**) is currently ingested; every other production is catalogued for future execution.

**Sources searched:** repository assets (`app/data/`, upload storage `/tmp/frametax2/storage`); local Mac folders (`~/Documents/thesystem`, `~/Documents/Deadmanshand`, `~/Downloads`, `~/Desktop`, `~/Documents`); Google Drive `MindtheStory/PROJECTS/`; documents referenced in this project and prior chats. Personal financial/tax records (personal 1040s, 1099s) were excluded as out-of-scope non-production material.

---

## Tier 1 — Ingested (live in the optimizer)

### The Little Utopia
- **Storage:** repo `app/data/little_utopia_real_budget.py` (parsed); source PDFs in Google Drive `MindtheStory/PROJECTS/THE LITTLE UTOPIA/` and `~/Downloads/`
- **Documents found:** `The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf`, `The Little Utopia 1_30_26.pdf` (script), `THE LITTLE UTOPIA LOOK BOOK .pdf`, `TheLittleUtopia_Slide.pptx`
- **Document types:** budget · script · lookbook · slide deck
- **Ingestion status:** ✅ **INGESTED** — budget parsed (44 leaf accounts), wired into served optimizer; anchored to Mauritius
- **Ready for optimizer:** ✅ **YES** (currently the sole live production)
- **Missing artifacts:** none material for optimization

---

## Tier 2 — Budget available, NOT yet ingested (optimizer-ready pending ingestion)

### The System
- **Storage:** `~/Documents/thesystem/`
- **Documents found:** `The System Budget v2.8.pdf`, `The System - Finance Plan v2.8.pdf`, `The System  cashflow v2.8 (1).xlsx`, `THE SYSTEM PROD SCHEDULE .xlsx`, `The System DOOD Schedule v1.0.pdf`, `The System HorC_Schedule.pdf`, `The System - 2021 - production  draft black.pdf` (script), `Content Acquisition Agreement … 20.5.2021.pdf`, `LHP-FR-The System-Dist Agmt-05202021.pdf`, `The System - Distribution Agreement (05.13.21) (3).docx`, `Mississippi Tax Letter.pdf`, `PROJECT SUMMARY – the system.docx`
- **Document types:** budget · finance plan · cashflow · production schedule · DOOD schedule · stripboard/HorC schedule · script · contracts (acquisition + distribution) · **jurisdiction/incentive correspondence (Mississippi Tax Letter)** · project summary
- **Ingestion status:** ❌ not ingested
- **Ready for optimizer:** ⚠️ **Budget available** — awaiting ingestion
- **Missing artifacts:** none material (unusually complete: has budget, schedule, finance plan, and jurisdiction tax correspondence)

### 10DZ (10 Double Zero)
- **Storage:** `~/Downloads/`, `~/Documents/`
- **Documents found:** `10DZ Budget 06242019v1.pdf`, `10DZ Budget 07062019v2.pdf`, `10DZ Budget 081219v1.pdf`, `ProductionBudget_10DZ_GA_15D_6.984MGross_012220.pdf`, `ProductionBudget_10DZ_GA_15D_7.25MGross_022520.pdf`, `10dzfinance*.xlsx` (multiple incl. `10dzfinanceuk.xlsx`), `DRAFT 10dz - Budget Analysis & ProjectionV1.pdf`, `DRAFT 10dz - opinionletter.pdf`, `10 Double Zero - Head Gear loan1.0.xlsx`, `10DZ.pdf`
- **Document types:** budget (multiple versions, incl. Georgia 15-day) · finance model (incl. UK) · budget analysis · **tax/legal opinion letter** · financing/loan doc
- **Ingestion status:** ❌ not ingested
- **Ready for optimizer:** ⚠️ **Budget available** (multiple versions — a canonical one must be selected at ingestion)
- **Missing artifacts:** script/schedule not located in searched folders

### Baron Samedi
- **Storage:** `~/Downloads/`
- **Documents found:** `Baron Samedi Budget v2_9 LA Budget.mbd`
- **Document types:** budget (Movie Magic `.mbd`, Louisiana)
- **Ingestion status:** ❌ not ingested
- **Ready for optimizer:** ⚠️ **Budget available** — note: `.mbd` is Movie Magic native format; confirm the parser accepts `.mbd` or export to PDF/CSV before ingestion
- **Missing artifacts:** script, schedule, finance plan not located

### Going Places
- **Storage:** `~/Downloads/`
- **Documents found:** `GOING PLACES Budget V5.3.pdf`
- **Document types:** budget
- **Ingestion status:** ❌ not ingested
- **Ready for optimizer:** ⚠️ **Budget available**
- **Missing artifacts:** script, schedule, finance plan not located

---

## Tier 3 — No budget located (NOT optimizer-ready)

### 97 Minutes
- **Storage:** `~/Downloads/`
- **Documents found:** `97 Minutes LA Tax Credit Opinion.pdf`, `New Legend Meitav Model - 97 Minutes 01.23.22 v2 (with UK Tax Credit)(abridged).pdf`, `…01.24.22 v3….pdf`, `Sales Estimate-97 Minutes.xlsx`, `ORWO MG - PAR MOVIE LLC (97 Minutes).pdf`, `LHP-FR-97Min-Dist Agmt-11Nov2021-signed.pdf`, `NOA 97 Minutes 001.tiff`
- **Document types:** **tax credit opinion (LA)** · finance model (with UK tax credit) · sales estimate · minimum-guarantee (MG) · distribution agreement · notice of assignment
- **Ingestion status:** ❌ not ingested
- **Ready for optimizer:** ❌ **NO** — a production budget document was not located (finance models are not a parseable line-item budget)
- **Missing artifacts:** **budget**; script; schedule

### Dead Man's Hand
- **Storage:** `~/Documents/Deadmanshand/`
- **Documents found:** `DMH_9302022.pdf` (script), `DMH_SYNOPSIS.pdf`, `Dead Mans Hand FSCA  v1 22-10-22redilne.docx`, `EXECUTIVE PRODUCER AGREEMENT.docx`, `epagreementgohill.pdf`, `Parce_5lbs_Summary and Waterfall Economics_v1.xlsx`, `TPCinvoiceDMH.docx`, `invoiceDMH.docx`
- **Document types:** script · synopsis · financing/services agreement (FSCA) · EP agreements · waterfall economics · invoices
- **Ingestion status:** ❌ not ingested
- **Ready for optimizer:** ❌ **NO**
- **Missing artifacts:** **budget**; schedule

### Other productions with partial materials
| Project | Storage | Documents found | Types | Missing for optimizer |
|---|---|---|---|---|
| Pierre the Pigeon Hawk | `~/Downloads/` | `PIERRE THE PIGEON HAWK- Imira Cashflow.xlsx`, `pierrecashflow.xlsx` | cashflow | budget, script, schedule |
| Safehaven | `~/Downloads/` | `SAFEHAVEN_Cashflow_V4.61.xlsx` | cashflow | budget, script, schedule |
| ASC Season 1 | `~/Downloads/` | `Copy of ASC Season 1 Deck_AG_SD 1.0.pptx(.pdf)` | pitch deck | budget, script, schedule |
| Four Suns and a Moon | `~/Downloads/`, `~/Documents/` | tax-return documents (production LLC) | tax records | budget, script, schedule (no production-planning docs) |
| BTBB | `~/Downloads/` | `2022.2.15 BTBB Opinion Letter v.1.pdf` | legal/tax opinion | budget, script, schedule |
| Wiseguy | `~/Downloads/` | `wiseguytaxletter.pdf` | tax letter | budget, script, schedule |

---

## Tier 4 — Google Drive slate (`MindtheStory/PROJECTS/`) — decks/lookbooks only

23 project folders. **Only THE LITTLE UTOPIA contains a budget** (Tier 1). Every other folder holds decks/lookbooks/scripts only — **no budget → not optimizer-ready**:

ADAM AND EVE · ALMOST PERFECT · ARTISTS OF CINEMA · BRAKING POINT · DeadafterDark · GIVE OR TAKE · Gifted · Hightower · MAGGIE MOVES ON · MODEL WARS · ONE NIGHT STAND · OTHERWISE ENGAGED · SPICE ROUTE · TEREZIN · THE ARRANGEMENT · THE DALE · THE MEN WE LEAVE BEHIND · UNCONDITIONAL LOVE · WHITE LINE HIGHWAY · White Feather

- **Document types present:** pitch decks · lookbooks · treatments · scripts (varies by folder)
- **Ready for optimizer:** ❌ **NO** (all missing budget)
- Slate-level (not a single production): `MTS_DevelopmentDeck.pptx`, `MTS_SlateSummary.pptx`, and `~/Downloads/` MTS/Newco investor decks + `MTS_FinancialModel_v8/v14/v15.xlsx`

---

## Registry summary

| Tier | Productions | Optimizer status |
|---|---|---|
| 1 — Ingested | 1 (The Little Utopia) | ✅ live |
| 2 — Budget available, not ingested | 4 (The System, 10DZ, Baron Samedi, Going Places) | ⚠️ ingestible |
| 3 — No budget located | 6+ (97 Minutes, Dead Man's Hand, Pierre, Safehaven, ASC, BTBB, Wiseguy, …) | ❌ needs budget |
| 4 — Slate decks/lookbooks only | ~20 (Google Drive PROJECTS) | ❌ needs budget |

**The single gating artifact across the corpus is the production budget.** Every production that has one is either ingested (Little Utopia) or ingestion-ready (The System — the most complete, including Mississippi tax correspondence — plus 10DZ, Baron Samedi, Going Places). This is a **content-availability** matter for future ingestion, **not** a backend implementation gap.

**Note on `.mbd`:** Baron Samedi's budget is Movie Magic native (`.mbd`); confirm the ingestion parser accepts it or export to PDF/CSV first.

---

## Full-machine discovery sweep (2026-07-25) — beyond Google Drive

Searched machine-wide for native budget/script formats (`.mbd` Movie Magic, `.fdx` Final Draft, `.celtx`) and production documents across `~/Downloads`, `~/Documents`, `~/Desktop`, `~/Dropbox`, `~/Movies`, iCloud Drive (`~/Library/Mobile Documents/com~apple~CloudDocs`), and the local Mail archive (`~/Library/Mail`). This materially updated several records and discovered additional productions. Catalog only — nothing ingested.

### Reclassified UP (budget now located)
| Project | New budget artifact found | Storage | New status |
|---|---|---|---|
| **97 Minutes** | `97 Minutes-Global_Budget UK_02Dec2021_V1.95-JRT.mbd`, `97 Minutes-Budget UK-LA_v2.71.mbd` (Movie Magic) | Mail archive | ⚠️ **Budget available** (was Tier 3). Also has LA tax-credit opinion, UK tax-credit model, dist. agreement, MG, sales estimate |
| **Dead Man's Hand (DMH)** | `DMH_9132022.mbd`, `DMH_9152022.mbd`, `DMH_9162022.mbd` (Movie Magic) | Mail archive; script/agreements in `~/Documents/Deadmanshand/` | ⚠️ **Budget available** (was Tier 3) |
| **10 Double Zero (10DZ)** | `10 DOUBLE ZERO FINAL DRAFT WSCENE NUMBERS 7-1-19.fdx` (script); `Ten Double Zero-Nevada.xlsx` (NV finance) | Mail archive; iCloud Drive | ⚠️ confirmed script + additional NV finance (already budget-available) |

### Newly discovered productions (not previously in registry)
| Project | Documents found | Types | Storage | Ready for optimizer |
|---|---|---|---|---|
| All My Friends Are Dead (AMFAD) | `4. AMFAD Budget_v4_01.14.2023.mbd`, `All My Friends Are Dead(v3).mbd`, `All_My_Friends_Are_Dead-current_draft…fdx` | budget (MM) · script (FD) | Mail archive | ⚠️ **Budget available** |
| Angel's Peak | `Angel's Peak Budget.mbd`, `Trail Mates.fdx` | budget (MM) · script (FD) | Mail archive | ⚠️ **Budget available** |
| Jade | `Jade-Final- MediaServices.mbd` | budget (MM) | Mail archive | ⚠️ **Budget available** |
| VIPER | `VIPER - MFJM - 2023.09.17.fdx` | script (FD) | Mail archive | ❌ no budget located |
| Sacrament 22 | `Sacrament 22.fdx` | script (FD) | Mail archive | ❌ no budget located |
| Trail Mates | `Trail Mates Final .fdx` | script (FD) | Mail archive | ❌ no budget located |
| Medellín | `Medellín 3.14.2021 - Director's Production Draft.fdx` | script (FD) | Mail archive | ❌ no budget located |
| David | `David by John Michael Kennedy Final Draft 1.pdf` | script | Dropbox | ❌ no budget located |
| Drug Honey | `Drug Honey Final … 2015.pdf`, tear sheet/synopsis | script · synopsis | Dropbox | ❌ no budget located |
| Jane Millen | `JANE MILLEN 3-26-15.pdf` | script | Dropbox | ❌ no budget located |
| Replacements | `Replacements_D5_August16_2015.pdf` | script | Dropbox | ❌ no budget located |
| Serpent Girl | `SERPENT GIRL SCRIPT.pdf` | script | Dropbox | ❌ no budget located |
| Unconditional / Sky (= UNCONDITIONAL LOVE in Drive slate) | `SKY_UNCONDITIONAL SCRIPT_MN COPY.pdf`, `SKY_UNCONDITIONAL_2015_no watermark.pdf` | script | Dropbox | ❌ no budget located |

### Notes
- The Mail archive is an **archival** source (email attachments), not an active project workspace; budgets found there should be confirmed as current before ingestion. `.mbd`/`.fdx` are native Movie Magic/Final Draft binaries — confirm the ingestion parser accepts them or export to PDF/CSV first.
- **Updated corpus tally:** 1 ingested (Little Utopia); **≥8 productions with a locatable budget, not ingested** (The System, 10DZ, Baron Samedi, Going Places, 97 Minutes, Dead Man's Hand, All My Friends Are Dead, Angel's Peak, Jade); the remainder are script-/deck-only. **The single gating artifact remains the production budget**, and ingestion is future execution, not a backend gap.
