# Distributed Final Authority Closure — ChatGPT Lane C

Research cutoff: 2026-08-11
Canonical baseline: `8ddfaaf01a60f1d7597142ac8d5ce3aeffd1b22f`

## Scope

Asia, Africa, Middle East, residual Oceania excluding Australia/New Zealand, multinational/regional records, and broad residual treaty/co-production queues; excludes Lane A and Europe Lane B.

Primary-authority standard: Primary current statute/regulation, government, administering film authority and official manuals only.

## Exact accounting

| Category | Start | Closed | Remaining |
|---|---:|---:|---:|
| Existing programs | 51 | 26 | 25 |
| Missing programs | 0 | 0 | 0 |
| Treaty pathways | 1 | 1 | 0 |
| Multinational/regional | 2 | 2 | 0 |
| **Total** | **54** | **29** | **25** |

Accounting assertion: **PASS**.

## Results

| Canonical ID | Jurisdiction | Status | Authoritative rule / conclusion | Optimizer consequence |
|---|---|---|---|---|
| `acpfilms_fund` | African, Caribbean and Pacific Group | AUTHORITY_CLOSED | Selective delegated ACP-EU grants, not a rebate. Example official Rwanda call requires a local company, ACP director, multi-country ACP co-producers, ACP ownership, confirmed finance, local/ACP expenditure and cumulative award caps. | Store call-specific selective funding, never a universal ACP rate. |
| `ao_film_incentive` | Angola | SUPERSEDED | The ICA identity is outdated. ANICC now administers selective national/CPLP calls including PAV III; no automatic location-spend rebate. | Retire ICA candidate; retain ANICC/PAV as selective funding metadata. |
| `bh_film_incentive` | Bahrain | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `bd_film_incentive` | Bangladesh | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `bt_film_incentive` | Bhutan | AUTHORITY_CLOSED | BICMA selectively funds Bhutanese art films/creative documentaries. Foreign shoots require permits, fees and refundable security deposit; no foreign rebate. | Domestic selective grant only; foreign pathway is facilitation. |
| `bw_film_commission` | Botswana | NO_CURRENT_PRODUCER_INCENTIVE_CONFIRMED | Official parliamentary records describe the Commission/Fund as proposed under a Cinematograph Bill, not an enacted operating incentive. | Suppress pending enacted rules and open process. |
| `kh_film_incentive` | Cambodia | NON_ECONOMIC_CONFIRMED | Official pathway provides permits, coordination and temporary duty-free equipment import/export, not producer cash support. | Keep permit/facilitation metadata only. |
| `cm_film_incentive` | Cameroon | AUTHORITY_CLOSED | MINAC provides call-bound selective writing/development/production grants to Cameroon-established producers with cultural criteria; not a QPE rebate. | Selective domestic grant only. |
| `cn_film_incentive` | China | NON_ECONOMIC_CONFIRMED | Co-production is a licensing and market-access status. Joint productions share investment, work, benefits and risk; prior approval, content review and personnel rules apply. No automatic payment. | Treat solely as structure/approval gate. |
| `eg_film_incentive` | Egypt | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `et_film_commission` | Ethiopia | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `fj_film_incentive` | Fiji | AUTHORITY_CLOSED | 20% cash rebate on Total Fiji Expenditure; FJD250,000 minimum and FJD4m cap. Fiji company, licensed AV agent, provisional approval, Fiji bank account, reporting, insurance, distribution evidence and audit required. TFE means goods/services used in Fiji and paid to a local registered company/individual. Mutually exclusive with F1/F2. | Use 20%, not historical rates; local bank payment alone is insufficient. |
| `ga_film_incentive` | Gabon | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `gh_film_incentive` | Ghana | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `hk_film_incentive` | Hong Kong SAR | DUPLICATE | Generic CreateHK support is not distinct; CreateHK became CCIDA and actual film economics sit in keyed Film Development Fund schemes. | Merge or suppress generic identity. |
| `hk_film_dev_fund` | Hong Kong SAR | AUTHORITY_CLOSED | FPFS 2.0 is selective financing for approved production budgets up to HKD25m: 40% of approved budget capped at HKD10m; 70% disbursed at principal-photography start; investor recoupment priority applies. | Model selective/recoupable financing, not a QPE rebate. |
| `ibermedia_programme` | Ibero-American Region (SEGIB) | AUTHORITY_CLOSED | Intergovernmental selective fund, not territorial rebate. Annual modes include co-production/development/distribution/training. Co-production request caps are USD150k fiction and USD100k documentary; independent member-state producers and Council selection apply. | Selective overlay only; no domestic incentive inference. |
| `in_nfdc_coproduction` | India | AUTHORITY_CLOSED | Official India Cine Hub co-production reimbursement is 30% of India QPE, capped INR300m, annual-budget and first-come limited; Indian co-producer applies after official status. Portal indicates up to 40% with applicable bonuses. Spend accrues after approval/status and claims are audited. | Rename and enforce base/bonus, India QPE, approval, cap and budget gates. |
| `id_film_incentive` | Indonesia | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `il_film_incentive` | Israel | AUTHORITY_CLOSED | Competitive 30% support to an Israeli production company on qualified costs released in Israel; NIS500k minimum. Living/transport capped at 35%; war-zone insurance plus management/general at 12%; finance and fixed equipment excluded. 80%/20% payment milestones. | Encode selective 30% with caps, exclusions and Israeli applicant. |
| `jo_rfc_rebate` | Jordan | AUTHORITY_CLOSED | 25%-45% of expenditure within Jordan based on size and cultural points. Maximum tier requires over USD10m spend and Jordanian cultural content. Approval is selective. | Replace flat rate; tier only after authoritative points/threshold determination. |
| `royal_film_commission_tourism_film_support` | Jordan | DUPLICATE | No distinct stackable tourism payment; current materials describe facilitation and the same RFC rebate package. | Suppress and prohibit stacking. |
| `kz_film_incentive` | Kazakhstan | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `ke_film_incentive` | Kenya | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `kw_film_incentive` | Kuwait | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `my_film_incentive` | Malaysia | AUTHORITY_CLOSED | 30% QMPE rebate. Foreign minimum MYR5m production or MYR1m post-only; FINAS local sponsor/producer and application at least three months before production. Points-based cultural uplift up to 5%, determined at final certificate, unavailable for post-only. | 30% base; conditional uplift; enforce thresholds, preapproval and Malaysia expenditure. |
| `mv_film_incentive` | Maldives | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `mn_film_commission` | Mongolia | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `mz_film_incentive` | Mozambique | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `na_film_commission` | Namibia | AUTHORITY_CLOSED | Selective Film and Video Fund for Namibian-origin development/production/distribution plus separate African co-production calls; no general location rebate. | Selective call metadata only. |
| `ng_film_incentive` | Nigeria | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `om_film_commission` | Oman | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `pk_pfc_rebate` | Pakistan | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `ph_film_incentive` | Philippines | AUTHORITY_CLOSED | FLIP is a selective 20% rebate on audited QPPE, PHP25m cap, with 5% cultural bonus and PHP30m total cap. Minimum spend: PHP20m feature/animation, PHP8m documentary, PHP24m TV/VOD. Registered Philippine service applicant and pre-work Notice of Grant required. QPPE expressly includes rights, payroll/social, technical services, overhead, post, lodging, meals, travel/transport and legal. | Implement rates, caps, thresholds, local applicant, approval and annual-budget gate. |
| `qa_dfi_fund` | Qatar | AUTHORITY_CLOSED | DFI Grants Programme is selective, cycle/region/stage/format dependent cultural funding, not a Qatar-spend rebate. | Keep outside deterministic QPE pricing. |
| `qa_film_incentive` | Qatar | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `rw_film_incentive` | Rwanda | AUTHORITY_CLOSED | Registered film investors receive 0% VAT for locally procured goods/services and 0% WHT for jointly approved foreign specialised services. RFO separately offers selective creative grants. No general cash rebate. | Separate tax treatment from selective grants. |
| `sa_sfc_rebate` | Saudi Arabia | AUTHORITY_CLOSED | Up to 60% eligible spend. Saudi licensed company or formal Saudi co-producer, NOC/preapproval and finance proof required. Minimum SAR750k feature or SAR187k documentary/animation and at least five main-unit shoot days. Listed Saudi ATL/BTL, locations/equipment, services, sets, travel/accommodation to Saudi and post qualify. Unlisted, outside-KSA or non-KSA supplier spend is excluded absent exception. | Update old 40%; encode conditional up-to-60% with territorial/list gates. |
| `sn_film_incentive` | Senegal | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `sc_film_incentive` | Seychelles | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `sg_imda_film_fund` | Singapore | AUTHORITY_CLOSED | TAP selective grant: first features up to SGD300k; Asia co-productions up to SGD600k or 50% SME/30% non-SME qualifying expense; global co-productions up to SGD1.2m or the same percentage ceiling. Singapore company, talent/co-pro credentials, market/finance evidence, call selection and no retrospective funding. | Selective category/SME grant, not automatic rebate. |
| `sg_sfc_production` | Singapore | SUPERSEDED | Legacy SFC Production Assistance is replaced for current film calls by IMDA TAP; archived percentages are not current. | Retire legacy candidate and point to TAP. |
| `za_dac_fund` | South Africa | AUTHORITY_CLOSED | NFVF is selective South African development/production funding under calls; distinct from dtic film incentives and not a fixed spend rebate. | Keep separate selective fund; no automatic stacking with dtic. |
| `kr_film_incentive` | South Korea | AUTHORITY_CLOSED | Selective annual-budget grant up to 30% of Korean QPE. Current route requires more than five Korean shoot days and over KRW400m QPE, Korean registered applicant and audited spend; annual QPE exclusions apply. | Use current gates, not archived 2014 thresholds. |
| `lk_film_incentive` | Sri Lanka | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `tw_film_incentive` | Taiwan | SUPERSEDED | TFAI rebate identity is wrong. Current TAICCA TICP 2.0 is co-investment up to 49% of total budget, generally uncapped (option 2 USD600k), requiring Taiwan elements, international co-finance/production and distribution; committee discretion/profit sharing apply. | Retire rebate identity; later model selective/recoupable TAICCA investment. |
| `tz_film_incentive` | Tanzania | NON_ECONOMIC_CONFIRMED | TFB supplies permits/licensing/coordination. Foreign permit is due at least one month before work; USD1,000 normal/USD3,000 fast-track. No producer payment. | Remove economic candidate; retain costs and lead time. |
| `tn_film_incentive` | Tunisia | AUTHORITY_CLOSED | Annual selective encouragement grants for writing, production and finishing to legally constituted audiovisual producers; not a Tunisia-spend rebate. | Selective cultural grant only. |
| `ug_film_commission` | Uganda | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `uz_film_incentive` | Uzbekistan | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `vn_film_incentive` | Vietnam | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `zm_film_commission` | Zambia | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `zw_film_commission` | Zimbabwe | GENUINELY_UNRESOLVED | Authority, policy, permit/facilitation function or general support mandate is identifiable, but no current complete producer incentive rule set was published at the checked primary-authority surface. | Disable pricing/ranking until the administering authority publishes the complete current rule set. |
| `IBERMEDIA_MEMBERSHIP_AND_FRAMEWORK` | Multinational / cross-regional | AUTHORITY_CLOSED | IBERMEDIA is a 21-state intergovernmental fund, not a treaty and grants no national treatment. Annual awards are separate from domestic co-production certification and incentives. | Separate fund eligibility, official co-production status and domestic incentives. |

## Remaining primary-authority data gaps

### `bh_film_incentive` — Bahrain Film Commission Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://culture.gov.bh/en/) — No complete current operating rule set located

### `bd_film_incentive` — Bangladesh Film Development Corporation (BFDC) Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://moi.gov.bd/) — No complete current operating rule set located

### `eg_film_incentive` — Egypt Film Commission Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://sis.gov.eg/) — No complete current operating rule set located

### `et_film_commission` — Ethiopian Film Commission Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.moc.gov.et/) — No complete current operating rule set located

### `ga_film_incentive` — Gabon Ministry of Culture Film Commission Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.culture.gouv.ga/) — No complete current operating rule set located

### `gh_film_incentive` — Ghana National Film Authority Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://nfa.gov.gh/) — No complete current operating rule set located

### `id_film_incentive` — Indonesian Film Commission Production Facilitation

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.kemenparekraf.go.id/) — No complete current operating rule set located

### `kz_film_incentive` — Kazakhfilm Studios Production Facilitation

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://kazakhcinema.kz/) — No complete current operating rule set located

### `ke_film_incentive` — Kenya Film Commission (KFC) Production Incentive

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://kenyafilmcommission.go.ke/news/kenya-film-commission-awards-ksh-3-million-prize-money-to-the-winners-of-the-10th-edition-of-the-kalasha-international-film-and-tv-awards/) — No complete current operating rule set located

### `kw_film_incentive` — Kuwait Film Committee Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.nccal.gov.kw/) — No complete current operating rule set located

### `mv_film_incentive` — Maldives Marketing and PR Corporation (MMPRC) Film Facilitation

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://corporate.visitmaldives.com/) — No complete current operating rule set located

### `mn_film_commission` — Mongolian Film Commission Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://filmmongolia.gov.mn/) — No complete current operating rule set located

### `mz_film_incentive` — Mozambique Instituto do Cinema Film Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://micultur.gov.mz/) — No complete current operating rule set located

### `ng_film_incentive` — Nigeria NFC / Creative Economy Incentive

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://nfc.gov.ng/) — No complete current operating rule set located

### `om_film_commission` — Oman Film Commission Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://mht.gov.om/) — No complete current operating rule set located

### `pk_pfc_rebate` — Pakistan Film Commission Cash Rebate

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.moib.gov.pk/CinemaDrama/index.html) — No complete current operating rule set located

### `qa_film_incentive` — Qatar Film Commission Production Incentive

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.gco.gov.qa/) — No complete current operating rule set located

### `sn_film_incentive` — Senegal Bureau d'Accueil des Tournages Film Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.culture.gouv.sn/) — No complete current operating rule set located

### `sc_film_incentive` — Seychelles Tourism Board Film Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://tourism.gov.sc/) — No complete current operating rule set located

### `lk_film_incentive` — Sri Lanka Film Commission Production Incentive

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://nfc.gov.lk/) — No complete current operating rule set located

### `ug_film_commission` — Uganda Film Commission Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.ucc.co.ug/) — No complete current operating rule set located

### `uz_film_incentive` — Uzbekkino National Film Support Program

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://gov.uz/en/cinematography) — No complete current operating rule set located

### `vn_film_incentive` — Vietnam Cinema Department Production Facilitation

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://dichvucong.bvhttdl.gov.vn/) — No complete current operating rule set located

### `zm_film_commission` — Zambia Film Commission Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.motac.gov.zm/) — No complete current operating rule set located

### `zw_film_commission` — Zimbabwe Film and Broadcasting Authority Production Support

- Exact question: Does a current open producer-accessible economic program exist for this exact identity and, if so, what instrument, rate/award, cap, minimum spend, applicant/local-entity gate, QPE/territorial predicates, preapproval, audit, payment and stacking rules govern it?
- Why insufficient: A mandate, announcement, policy or facilitation page does not provide an implementable current claim manual.
- Reason: DATA_GAP
- Optimizer consequence: Disable pricing/ranking until the administering authority publishes the complete current rule set.
- Primary sources checked:
  - [Current official authority materials](https://www.mhcc.gov.zw/) — No complete current operating rule set located

## Treaty and multinational conclusions

### `acpfilms_fund` — ACP Films — EU-ACP Cultural Film Co-production Fund

Selective delegated ACP-EU grants, not a rebate. Example official Rwanda call requires a local company, ACP director, multi-country ACP co-producers, ACP ownership, confirmed finance, local/ACP expenditure and cumulative award caps.

### `ibermedia_programme` — IBERMEDIA Programme for Ibero-American Co-productions

Intergovernmental selective fund, not territorial rebate. Annual modes include co-production/development/distribution/training. Co-production request caps are USD150k fiction and USD100k documentary; independent member-state producers and Council selection apply.

### `IBERMEDIA_MEMBERSHIP_AND_FRAMEWORK` — IBERMEDIA membership and framework

IBERMEDIA is a 21-state intergovernmental fund, not a treaty and grants no national treatment. Annual awards are separate from domestic co-production certification and incentives.

- Parties: Argentina, Bolivia, Brazil, Colombia, Costa Rica, Cuba, Chile, Ecuador, El Salvador, Spain, Guatemala, Honduras, Mexico, Panama, Paraguay, Peru, Portugal, Puerto Rico, Dominican Republic, Uruguay, Venezuela
- Instrument: IBERMEDIA intergovernmental programme and annual rules (not a treaty)
- Version: 2026/current 21-member programme
- Contribution rules: Fund mainly from member contributions and loan repayments; selective awards; co-production request maximum USD150k fiction/USD100k documentary.
- National treatment: None automatically.
- Competent authorities: Intergovernmental Council, Technical Unit and designated national cinematographic authorities.
- Domestic incentive interaction: Separate domestic certification and incentive rules always apply.

## Primary sources by identity

### `acpfilms_fund`

- [ACP-EU CLAP-ACP2 call](https://www.acp-ue-culture.eu/wp-content/uploads/2022/09/RFO_CALL-FOR-PROJECTS.pdf) — current rule

### `ao_film_incentive`

- [ANICC PAV III](https://anicc.gov.ao/web/noticias/resultados-finais-do-programa-cplp-audiovisual-3.a-edicao-%28pav-iii%29) — current rule

### `bh_film_incentive`

- [Current official authority materials](https://culture.gov.bh/en/) — No complete current operating rule set located

### `bd_film_incentive`

- [Current official authority materials](https://moi.gov.bd/) — No complete current operating rule set located

### `bt_film_incentive`

- [BICMA grant call](https://www.bicma.gov.bt/?p=8927) — current rule
- [Bhutan Filming Regulation 2025](https://www.bicma.gov.bt/wp-content/uploads/2025/03/Bhutan-Filming-Regulation-2025.pdf) — current rule

### `bw_film_commission`

- [Botswana Parliament Hansard 1 April 2026](https://www.parliament.gov.bw/documents/DAILY-HANSARD--1st-APRIL-2026---Budget-Meeting--2nd-meeting-of-the-2nd-session-of-the-13th-Parliament_01_33_48_08_04_2026.pdf) — current rule

### `kh_film_incentive`

- [Cambodia Film Commission process](https://cambodia-cfc.org/administrative-process/) — current rule

### `cm_film_incentive`

- [MINAC cinema aid](https://www.minac-gouv.com/cinema-audiovisuel/fonds-aide-cinema) — current rule

### `cn_film_incentive`

- [National Film Administration rules](https://www.chinafilm.gov.cn/xxgk/zcfg/bmgz/202112/t20211214_441292.html) — current rule

### `eg_film_incentive`

- [Current official authority materials](https://sis.gov.eg/) — No complete current operating rule set located

### `et_film_commission`

- [Current official authority materials](https://www.moc.gov.et/) — No complete current operating rule set located

### `fj_film_incentive`

- [Film Fiji rebate](https://film-fiji.com/20-film-tax-rebate/) — current rule
- [Film Fiji FAQ](https://film-fiji.com/faqs/) — TFE territoriality

### `ga_film_incentive`

- [Current official authority materials](https://www.culture.gouv.ga/) — No complete current operating rule set located

### `gh_film_incentive`

- [Current official authority materials](https://nfa.gov.gh/) — No complete current operating rule set located

### `hk_film_incentive`

- [CCIDA schemes](https://www.ccidahk.gov.hk/en/funding_n_support.php?industries=film) — current rule

### `hk_film_dev_fund`

- [CCIDA FPFS 2.0](https://www.ccidahk.gov.hk/en/whatsnew_detail.php?id=2025011415221293999) — current rule

### `ibermedia_programme`

- [IBERMEDIA 2026 calls](https://www.programaibermedia.com/nuestras-convocatorias/) — current rule
- [2026 co-production form](https://www.programaibermedia.com/wp-content/uploads/2017/11/FORM_COP_1_2026_ESP.pdf) — current rule

### `in_nfdc_coproduction`

- [India Cine Hub guidelines](https://indiacinehub.gov.in/sites/default/files/2025-03/india-cine-hub-film-incentive-guidelines-2023-ver-feb-2025_0.pdf) — current rule
- [ICH current portal](https://indiacinehub.gov.in/incentive-calcuator-page) — current rule

### `id_film_incentive`

- [Current official authority materials](https://www.kemenparekraf.go.id/) — No complete current operating rule set located

### `il_film_incentive`

- [Israel investment guide](https://www.gov.il/BlobFolder/reports/iia-investment-guide-en/en/pirsomim_iia-investment-guide-en.pdf) — current rule
- [Directive 4.52 English](https://embassies.gov.il/madrid/NewsAndEvents/Pages/Program%20for%20the%20encouragement%20of%20foreign%20films%20and%20series%20in%20Israel.pdf) — current rule

### `jo_rfc_rebate`

- [Invest Jordan creative industries](https://invest.jo/en/investment-sectors/creative-industries) — current rule

### `royal_film_commission_tourism_film_support`

- [Invest Jordan creative industries](https://invest.jo/en/investment-sectors/creative-industries) — current rule

### `kz_film_incentive`

- [Current official authority materials](https://kazakhcinema.kz/) — No complete current operating rule set located

### `ke_film_incentive`

- [Current official authority materials](https://kenyafilmcommission.go.ke/news/kenya-film-commission-awards-ksh-3-million-prize-money-to-the-winners-of-the-10th-edition-of-the-kalasha-international-film-and-tv-awards/) — No complete current operating rule set located

### `kw_film_incentive`

- [Current official authority materials](https://www.nccal.gov.kw/) — No complete current operating rule set located

### `my_film_incentive`

- [FINAS FIMI](https://www.finas.gov.my/services/fimi) — current rule
- [FIMI foreign application](https://www.filminmalaysia.com/incentives/foreign-application/) — current rule

### `mv_film_incentive`

- [Current official authority materials](https://corporate.visitmaldives.com/) — No complete current operating rule set located

### `mn_film_commission`

- [Current official authority materials](https://filmmongolia.gov.mn/) — No complete current operating rule set located

### `mz_film_incentive`

- [Current official authority materials](https://micultur.gov.mz/) — No complete current operating rule set located

### `na_film_commission`

- [Namibia Film Commission funding](https://nfc.na/funding) — current rule

### `ng_film_incentive`

- [Current official authority materials](https://nfc.gov.ng/) — No complete current operating rule set located

### `om_film_commission`

- [Current official authority materials](https://mht.gov.om/) — No complete current operating rule set located

### `pk_pfc_rebate`

- [Current official authority materials](https://www.moib.gov.pk/CinemaDrama/index.html) — No complete current operating rule set located

### `ph_film_incentive`

- [FDCP FLIP](https://fdcp.ph/programs/film-incentives/film-location-incentive-program) — current rule

### `qa_dfi_fund`

- [DFI grants](https://www.dohafilminstitute.com/financing/grants) — current rule

### `qa_film_incentive`

- [Current official authority materials](https://www.gco.gov.qa/) — No complete current operating rule set located

### `rw_film_incentive`

- [Rwanda Investment Code](https://rdb.rw/wp-content/uploads/2021/04/New-Investment-code-2021.pdf) — current rule
- [RFO grants](https://rdb.rw/wp-content/uploads/2024/12/CREATIVE_GRANTS_INITIATIVE_FINAL.pdf) — current rule

### `sa_sfc_rebate`

- [Film Saudi incentive](https://film.sa/incentive-programs/?lang=en) — current rule
- [Film Saudi FAQ](https://film.sa/faq/) — current rule

### `sn_film_incentive`

- [Current official authority materials](https://www.culture.gouv.sn/) — No complete current operating rule set located

### `sc_film_incentive`

- [Current official authority materials](https://tourism.gov.sc/) — No complete current operating rule set located

### `sg_imda_film_fund`

- [IMDA TAP film](https://www.imda.gov.sg/about-imda/research-and-statistics/support-for-industry-sectors/media/tap/film) — current rule

### `sg_sfc_production`

- [IMDA TAP launch](https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/press-releases/2025/talent-accelerator-programme) — current rule

### `za_dac_fund`

- [NFVF strategy 2025-2030](https://www.nfvf.co.za/wp-content/uploads/2025/07/NFVF-STRATEGIC-PLAN-FOR-2025-2030-FINAL-VERSION.pdf) — current rule
- [dtic film incentives](https://www.thedtic.gov.za/financial-and-non-financial-support/incentives/film-incentive/) — current rule

### `kr_film_incentive`

- [KOFIC 2025 call](https://www.kofic.or.kr/kofic/business/prom/promotionBoardDetail.do?seqNo=16592&mode=I) — current rule
- [KoBiz incentive](https://www.koreanfilm.or.kr/eng/coProduction/locIncentive.jsp) — current rule

### `lk_film_incentive`

- [Current official authority materials](https://nfc.gov.lk/) — No complete current operating rule set located

### `tw_film_incentive`

- [TAICCA TICP 2.0](https://en.taicca.tw/grants_investment/detail/5?type_id=2) — current rule

### `tz_film_incentive`

- [Tanzania Film Board](https://www.filmboard.go.tz/pages/film-making) — current rule
- [Foreign permit form](https://filmboard.go.tz/uploads/publications/sw-1752840965-BLANK%20FILM%20PRODUCTION%20PERMIT%20APPLICATION%20FORM%20FOR%20FOREIGNERS.pdf) — current rule

### `tn_film_incentive`

- [CNCI 2025 grants](https://cnci.tn/avis-les-candidatures-pour-les-bourses-dencouragement-a-la-production-cinematographique-2025-sont-desormais-ouvertes/) — current rule

### `ug_film_commission`

- [Current official authority materials](https://www.ucc.co.ug/) — No complete current operating rule set located

### `uz_film_incentive`

- [Current official authority materials](https://gov.uz/en/cinematography) — No complete current operating rule set located

### `vn_film_incentive`

- [Current official authority materials](https://dichvucong.bvhttdl.gov.vn/) — No complete current operating rule set located

### `zm_film_commission`

- [Current official authority materials](https://www.motac.gov.zm/) — No complete current operating rule set located

### `zw_film_commission`

- [Current official authority materials](https://www.mhcc.gov.zw/) — No complete current operating rule set located

### `IBERMEDIA_MEMBERSHIP_AND_FRAMEWORK`

- [IBERMEDIA programme](https://www.programaibermedia.com/el-programa/) — current rule
- [2026 calls](https://www.programaibermedia.com/nuestras-convocatorias/) — current rule

## Additional findings

- Genuine interpretation conflicts: None.
- Bounded additional discoveries: None.
