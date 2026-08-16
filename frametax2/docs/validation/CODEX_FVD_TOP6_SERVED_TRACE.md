# Codex FVD Top-6 Served-Output Trace

**Trace date:** 2026-08-16

**Mode:** diagnosis only; no production implementation

**Project:** F#K Valentine's Day (`6c6f1c13-2d49-4bbc-bafb-2a12efa93112`)

**Canonical engine:** `canonical-1.2.1`

**Evaluation fingerprint:** `bb48c6e76623545f7718ebff65cfd14bfd8ff47ea4c6cbd07ec6a5b7473ae79f`

## Final gate

`FVD_TOP6_DEFECT_LOCALIZED`

The current canonical FVD evaluation persists **30 PRICED structures**. All 30 survive into the served project state with their QPE, incentive, NPC, priceability, and comparability fields intact. The first divergence is the Overview selector: it admits only directly comparable structures, which reduces the 30 displayable priced results to Greece alone. Workspace receives all 30 but orders null-ranked review candidates by generation/served order instead of NPC. Scenarios also receives all priced results but partitions and orders them by comparability and served order rather than presenting the priced universe in NPC order.

This is a served-output selection defect, not an economics or numeric-handoff defect.

## Trace boundary

| Layer | Observed result | Status | Defect classification |
|---|---|---:|---|
| Persisted canonical evaluation | 110 current structures: 30 `PRICED`, 80 unpriceable. All 30 priced records have QPE, incentive, and NPC. Persisted `rank_by_net_cost` is null on all 30. Greece is directly comparable; the 29 alternatives require review. | PASS | — |
| Served `GET /api/v1/cineglobe/projects/{id}/state` | 110 structures: the same 30 remain `is_fully_priced=true`; Greece remains directly comparable; 29 remain priced but non-comparable/review-required. Numeric fields match persistence. | PASS | — |
| Overview `productionOptions.js::selectTopOptions` | `allocated.ranking` is filtered through `isDirectlyComparable`. Only Greece survives, so Overview cannot produce the required six best displayable priced structures. | **FIRST FAIL** | `OVERVIEW_SELECTION_DEFECT` |
| Workspace `Workspace.jsx::visibleStructures` | All 30 priced structures are available, but ordering uses ranking `rank`; null rank becomes infinity. Stable order therefore follows served/generation order for the 29 review rows, placing materially higher-NPC Australian structures ahead of cheaper alternatives. | FAIL | `WORKSPACE_SELECTION_DEFECT` |
| Scenarios `Scenarios.jsx` | Greece is the sole comparable row. All 29 priced review rows are visible, but `reviewOrdered` retains served order instead of NPC order. | FAIL | `SCENARIOS_SELECTION_DEFECT` |

No `PERSISTENCE_STATUS_DEFECT`, `SERVED_ADAPTER_DEFECT`, or `STALE_MIXED_RESULT_DEFECT` was found. The served adapter scopes the response to the current engine version and leading fingerprint.

## Persisted PRICED universe

Rows below are in persisted creation/served order. `Persisted rank` is null for every row. Classification is the current product classification, not a new economic determination.

| # | Structure ID | Class | Jurisdiction / program | QPE | Incentive | NPC | Persisted status | Directly comparable |
|---:|---|---|---|---:|---:|---:|---|---:|
| 1 | `e8649797-b143-40d7-978b-35bf7ca07cc1` | CURRENT | GR / `gr_cash_rebate` | $3,614,149.60 | $1,445,659.84 | $3,072,027.16 | PRICED; rank null | Yes |
| 2 | `4910c93d-2db6-40bc-ad82-c650d9a1718b` | ALTERNATIVE | AU-NSW / `au_nsw_pdv_rebate` | $4,154,821.00 | $415,482.10 | $4,102,204.90 | PRICED; rank null | No |
| 3 | `1d5ec4a0-61eb-4d3a-8bee-9f29fe1145b9` | ALTERNATIVE | AU-QLD / `au_qld_pdv_rebate` | $4,154,821.00 | $623,223.15 | $3,894,463.85 | PRICED; rank null | No |
| 4 | `03eb93be-25a0-44a7-ba88-da4f4462af96` | ALTERNATIVE | AU-SA / `au_sa_pdv_rebate` | $4,154,821.00 | $415,482.10 | $4,102,204.90 | PRICED; rank null | No |
| 5 | `2eb322f2-4f4d-4fad-b122-a39ffdb27e7e` | ALTERNATIVE | CA-NL / `ca_nl_all_spend_credit` | $4,154,821.00 | $1,661,928.40 | $2,855,758.60 | PRICED; rank null | No |
| 6 | `94842aac-7326-4bf8-a16f-fb0d75b32da9` | ALTERNATIVE | CA-QC / `ca_qc_pstc` | $4,154,821.00 | $1,038,705.25 | $3,478,981.75 | PRICED; rank null | No |
| 7 | `57ee5758-8578-4d8e-8e8c-a21132bbe022` | ALTERNATIVE | CH / `ch_pics_national_rebate` | $4,154,821.00 | $830,964.20 | $3,686,722.80 | PRICED; rank null | No |
| 8 | `93355954-cd00-4793-86d6-8341e7a4811a` | ALTERNATIVE | CR / `cr_tax_return_incentive` | $4,154,821.00 | $486,114.06 | $4,031,572.94 | PRICED; rank null | No |
| 9 | `b4f24bce-b042-4f40-83e8-8da3ff07960c` | ALTERNATIVE | DK / `dk_production_rebate` | $4,154,821.00 | $1,038,705.25 | $3,478,981.75 | PRICED; rank null | No |
| 10 | `13e43bdc-2bdb-486a-8e43-0fd61d5383ff` | ALTERNATIVE | EG / `eg_empc_cashback` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 | PRICED; rank null | No |
| 11 | `45b9dc19-e250-4fea-8588-9a1f42d55b59` | ALTERNATIVE | FJ / `fj_film_rebate` | $4,154,821.00 | $830,964.20 | $3,686,722.80 | PRICED; rank null | No |
| 12 | `2be85ba1-7251-4b2b-8463-eec2a1146cba` | ALTERNATIVE | GE / `ge_film_rebate` | $4,154,821.00 | $830,964.20 | $3,686,722.80 | PRICED; rank null | No |
| 13 | `48f0f211-95eb-46a2-9892-8fd9ce42a700` | ALTERNATIVE | GH / `gh_film_tax_incentive` | $4,154,821.00 | $830,964.20 | $3,686,722.80 | PRICED; rank null | No |
| 14 | `faf44809-628c-4a35-a680-aa7741146c51` | ALTERNATIVE | IL / `il_foreign_production_fund` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 | PRICED; rank null | No |
| 15 | `c17c5468-ae58-4d25-9fe3-d3ff327bdf6a` | ALTERNATIVE | MN / `mn_production_incentive` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 | PRICED; rank null | No |
| 16 | `1e95b5ae-77a4-49aa-afe0-1aa8fcacfaad` | ALTERNATIVE | MT / `mt_mfc_rebate` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 | PRICED; rank null | No |
| 17 | `16685d4c-83e3-43a5-8447-2d563cbde5f5` | ALTERNATIVE | MU / `mu_edb_incentive` | $1,132,056.00 | $339,616.80 | $4,178,070.20 | PRICED; rank null | No |
| 18 | `c608b1ff-9560-43e9-93d1-48043a2ffac3` | ALTERNATIVE | MX / `mx_federal_film_incentive_2026` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 | PRICED; rank null | No |
| 19 | `0f798172-fe82-4938-848e-0534d4cf8ebd` | ALTERNATIVE | MY / `my_finas_rebate` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 | PRICED; rank null | No |
| 20 | `929ddd0f-c363-4152-8dda-7b33c4e74519` | ALTERNATIVE | PA / `pa_film_rebate` | $4,154,821.00 | $1,038,705.25 | $3,478,981.75 | PRICED; rank null | No |
| 21 | `d5b287e8-9bb5-442f-8357-16a8b1e33bb3` | ALTERNATIVE | PH / `ph_fdcp_flip` | $4,154,821.00 | $830,964.20 | $3,686,722.80 | PRICED; rank null | No |
| 22 | `fdb9c061-a47c-451c-8336-a0ec44dcc221` | ALTERNATIVE | PT / `pt_scri_pt_cash_rebate` | $4,154,821.00 | $1,038,705.25 | $3,478,981.75 | PRICED; rank null | No |
| 23 | `d1c0d66b-aa5c-4c3b-b81b-b845a5920070` | ALTERNATIVE | QA / `qa_screen_production_incentive` | $4,154,821.00 | $1,661,928.40 | $2,855,758.60 | PRICED; rank null | No |
| 24 | `cc2d0f1b-6682-4e49-9dc5-fa0812e32db4` | ALTERNATIVE | SG / `sg_made_with_singapore_rebate` | $4,154,821.00 | $1,661,928.40 | $2,855,758.60 | PRICED; rank null | No |
| 25 | `43827738-6da5-40a6-b267-7be13c7df74d` | ALTERNATIVE | TH / `th_boi_incentive` | $4,154,821.00 | $623,223.15 | $3,894,463.85 | PRICED; rank null | No |
| 26 | `8c04e2c2-8e2d-4563-b6ab-5b7a092a8f88` | ALTERNATIVE | TW / `tw_bamid_rebate` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 | PRICED; rank null | No |
| 27 | `b294937f-91bb-40a8-9876-ac4242f5c39c` | ALTERNATIVE | UA / `ua_cash_rebate` | $4,154,821.00 | $1,038,705.25 | $3,478,981.75 | PRICED; rank null | No |
| 28 | `4e31d420-02c0-41bb-9f46-cc8369fb720b` | ALTERNATIVE | US-NY / `us_ny_film_credit` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 | PRICED; rank null | No |
| 29 | `cbfbb762-2f47-47b7-857b-927030001ecb` | ALTERNATIVE | UZ / `uz_film_rebate` | $4,154,821.00 | $415,482.10 | $4,102,204.90 | PRICED; rank null | No |
| 30 | `9436930e-ccd6-4812-9fed-1305e4035cb7` | ALTERNATIVE | ZA / `za_dtic_foreign_film` | $4,154,821.00 | $1,038,705.25 | $3,478,981.75 | PRICED; rank null | No |

## Expected Top 6 from current persisted data

Sorted by NPC ascending. For exact NPC ties, this trace preserves persisted/served order; that is a trace tie-break only and does not assert an economic distinction between tied programs.

| Rank | Class | Jurisdiction / program | QPE | Incentive | NPC |
|---:|---|---|---:|---:|---:|
| 1 | ALTERNATIVE | CA-NL / `ca_nl_all_spend_credit` | $4,154,821.00 | $1,661,928.40 | $2,855,758.60 |
| 2 | ALTERNATIVE | QA / `qa_screen_production_incentive` | $4,154,821.00 | $1,661,928.40 | $2,855,758.60 |
| 3 | ALTERNATIVE | SG / `sg_made_with_singapore_rebate` | $4,154,821.00 | $1,661,928.40 | $2,855,758.60 |
| 4 | CURRENT | GR / `gr_cash_rebate` | $3,614,149.60 | $1,445,659.84 | $3,072,027.16 |
| 5 | ALTERNATIVE | EG / `eg_empc_cashback` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 |
| 6 | ALTERNATIVE | IL / `il_foreign_production_fund` | $4,154,821.00 | $1,246,446.30 | $3,271,240.70 |

There are two material ties:

- CA-NL, QA, and SG tie exactly at $2,855,758.60 and occupy positions 1–3.
- EG, IL, MN, MT, MX, MY, TW, and US-NY tie exactly at $3,271,240.70. EG and IL occupy positions 5–6 only because persisted/served order is preserved. Any two members of this tie group satisfy the primary NPC contract at the cutoff; the product should retain a stable documented secondary order rather than imply an economic difference.

## Numeric integrity: expected Top 6

| Candidate | Persisted QPE = served QPE | Persisted incentive = served incentive | Persisted NPC = served NPC |
|---|---:|---:|---:|
| CA-NL | PASS | PASS | PASS |
| QA | PASS | PASS | PASS |
| SG | PASS | PASS | PASS |
| GR | PASS | PASS | PASS |
| EG | PASS | PASS | PASS |
| IL | PASS | PASS | PASS |

`NUMERIC_HANDOFF = PASS`

No persisted canonical arithmetic contradiction was encountered within this bounded handoff check.

## Current presentation comparison

### Overview current

`[GR]` — there is no current six.

- Missing expected candidates: CA-NL, QA, SG, EG, IL.
- Incorrectly included candidates: none; Greece belongs in the expected six but should be fourth, not the sole result.
- Status/filter error: priced non-comparable/review-required candidates are incorrectly removed from the displayable Top-6 universe.

### Workspace current default six

`[GR, AU-NSW, AU-QLD, AU-SA, CA-NL, CA-QC]`

- Missing expected candidates: QA, SG, EG, IL.
- Incorrectly included candidates: AU-NSW, AU-QLD, AU-SA, CA-QC.
- Ordering error: GR appears before cheaper CA-NL; three high-NPC Australian candidates appear before CA-NL and the other lower-NPC alternatives.
- Workspace can replace the sixth slot through its swap state, but that does not correct the initial selection/order defect.

### Scenarios current presentation

- Comparable section: `[GR]`.
- First six review rows in current served order: `[AU-NSW, AU-QLD, AU-SA, CA-NL, CA-QC, CH]`.
- First six rendered rows across the comparable section followed by review rows: `[GR, AU-NSW, AU-QLD, AU-SA, CA-NL, CA-QC]`.
- All 29 priced review-required rows remain available, so this is not a disappearance defect at the Scenarios boundary. It is a partition/order defect: the review list is not NPC-sorted, and the two sections do not expose one overall NPC-ascending presentation.
- If Scenarios is ordered by NPC under the approved contract, its first six are the same expected six listed above, subject to the exact-tie note.

## First divergence and root cause

**First divergence:** `OVERVIEW_SELECTION_DEFECT` in `frontend/src/lib/productionOptions.js::selectTopOptions`.

**Root cause:** the selector gates the ranking universe on direct comparability instead of displayable priceability. The served state correctly distinguishes `is_fully_priced=true` from `is_directly_comparable=false`, but Overview treats non-comparability as a reason to exclude a priced candidate. This leaves only Greece. Workspace and Scenarios then independently use rank/comparability partitions and served order, so they do not restore the approved global NPC ordering.

The absence of persisted ranks is not itself a priceability failure. The UI must order the displayable priced universe from served NPC values even when comparability/MFNI review is outstanding.

## Claude repair check

Closed by the attempted served-wiring repair:

- All 30 persisted FVD priced structures survive into served state.
- Priceability remains distinct from comparability: all 30 are fully priced; Greece is directly comparable; 29 are review-required/non-comparable.
- QPE, incentive, NPC, segment traces, and structure identity survive the served handoff.
- Workspace receives all 30 priced structures.
- Scenarios receives Greece plus all 29 priced review rows.

Remaining:

- Overview still hides the 29 priced non-comparable candidates.
- Workspace still chooses/orders its default six by rank-null/served order rather than NPC.
- Scenarios still partitions the universe and retains served order for review rows instead of NPC ordering.

## Little Utopia regression control

| Control | Result |
|---|---:|
| Budget = $4,364,393.00 | PASS |
| Mauritius NPC = $3,057,794.90 | PASS |
| Normal project navigation resolves through the mature project UI | PASS |

The bounded navigation regression suite passed 7/7 checks. No Little Utopia economics were reopened.

`LU_REGRESSION = PASS`

## Smallest repair boundary

No repair was implemented. The smallest production repair is confined to these frontend selection functions:

1. `frontend/src/lib/productionOptions.js::selectTopOptions`
   - Build the Top-6 universe from displayable `is_fully_priced` structures.
   - Sort by served `npc_with_adjustments_usd` ascending and preserve stable served order for exact ties (or document one deterministic non-economic secondary key).
   - Do not gate Top-6 inclusion on `is_directly_comparable`, review/MFNI status, or the existing treaty-slot rule; retain classification/status as presentation metadata.
2. `frontend/src/screens/production/Workspace.jsx::visibleStructures`
   - Use the same priced/NPC selector for the default visible six instead of sorting null ranking values to infinity.
3. `frontend/src/screens/production/Scenarios.jsx` presentation ordering
   - NPC-sort priced candidates while retaining their comparable/review labels; do not hide priced review-required rows.

To prevent drift, the priced/NPC ordering should be implemented once in `frontend/src/lib/productionOptions.js` and consumed by Overview, Workspace, and Scenarios. Contract coverage belongs in `frontend/tests/overview-options.test.mjs` plus focused Workspace and Scenarios selection tests. No backend, optimizer, rule, or economics changes are indicated by this trace.
