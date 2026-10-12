# Evidence-Gap Closure Addendum (NA + ROW) — PARTIAL, NOT 100% VERIFIED

Engine baseline frozen: `canonical-1.122.0` (`59566fd1`). No canonical code changed.
This addendum **supersedes** conflicting statements in the earlier ROW/NA handoffs and registers.

## 1. Withdrawals / corrections (supersede prior claims)

| ID | Prior claim | Disposition | Basis |
|---|---|---|---|
| W-01 | Australia Producer Offset has an 80% QAPE / 20% ATL cap (ROW-DEF-006 text; Producer Offset ceiling in matrix) | **WITHDRAWN – unsupported.** Matrix script no longer applies it (rerun). | Screen Australia guidance retrieved 2026-10-11 describes: 40% feature/30% other on QAPE; SAC test or official co-production; min QAPE A$500,000 feature. No 80% cap found. The 20% ATL figure I cited (s.376-170(4)(b)) was not retrieved and is unverified. |
| W-02 | `au_qld_pdv_rebate` is stale at 10%; true rate 15% (ROW-DEF-002 sub-claim; PDV tables using 15%) | **WITHDRAWN – engine is correct.** | Engine source (`program_rate_rules_worldwide.py` ~L7559-7583) cites Screen Queensland official page: 15%→10% effective 4/9/2026, min A$250,000. QLD PDV figures in the register using 15% (and QLD stack 45%) are superseded; use 10% (stack 40%). The 15% figure is only a possible historical rate. |
| W-03 | Engine enforces 80% territorial QPE cap for DE/FR/GR/HU/IE/IS/IT/LV/ME/RS/SK/UK/UY ("universal territorial caps"; Italy/Hungary 80% statements) | **WITHDRAWN.** | Engine `QPE_CAP_RULES` contains only `uk_avec`, `gr_cash_rebate`, `ca_federal_cptc`, `cz_film_incentive(_animation)`. Snapshot confirms `de_dfff`, `it_tax_credit_foreign`, `hu_hipa_rebate`, `fr_trip`, `ie_section_481` run uncapped (QPE = $4,054,196 on LU). I have **no retrieved primary authority** for 80% caps on those programs; the 80%-capped column and Italy/Hungary sub-cap prose in the handoff are unsupported. |
| W-04 | Spain Category 2 base includes all `miscellaneous`/`production_sound`/`general_administration`; "department labels = technical industries" | **DOWNGRADED to conditional.** | Eligibility is by supplier/spend nature in Spain (Art. 36.2 LIS), not budget department label. `miscellaneous` holds mixed accounts (crew labour, props, wardrobe, locations). FVD's Cat-2 figure ($1,724,759) and "false rejection" are therefore **conditional on a Spanish-spend/supplier split** (not retained). The engine omission of those categories is a coverage observation, not a proven USD defect. Note: FVD result also depends on territorial inclusion of travel ($271,080) and insurance. |
| W-05 | PDV strict spend identified from department/category labels (ROW-DEF-002 amounts) | **DOWNGRADED to conditional.** | PDV eligibility is activity-based and Australian-location-based (retrieved: creation/editing/mixing of effects, related staff, facilities). Music, titles, deliverables and post fringes inclusion is unverified; amounts are bounds, not expectations. Qualitative defect (all-production base for PDV-only programs) stands as engine classification vs. retrieved scope. |
| W-06 | "$X ATL cap EUR100k/person", Cyprus 30% ATL cap, Hungary 50% payroll, Italy 30% EU ATL, Morocco 90% cap, Greece Annex B.3 | **UNVERIFIED in this addendum.** | No primary URL retrieved in this session. Retained: engine's own citation text only (engine ≠ legal authority). Treat ROW-DEF-003/-005 and DISCLOSED-LIMITATION-001 as *hypotheses pending authority*. |
| W-07 | CAVCO/CPTC handling | **Kept distinct, unchanged**: domestic CPTC (CAVCO, points test), treaty CPTC (co-production, no domestic point test), service PSTC (no CPTC points). Domestic 6/10 points not applied to treaty routes. |

## 2. Authority register actually retrieved this session (2026-10-11)

| Rule | Source retrieved | Pinpoint / status |
|---|---|---|
| AU Producer Offset 40%/30%, SAC or co-pro, min A$500k feature | screenaustralia.gov.au (Producer Offset pages); ausfilm.com.au; ATO | ITAA 1997 Div 376. Section-level pinpoints not retrieved (search summary only; page fetch not performed). Status: **secondary-summary of official site – partially supported** |
| AU PDV Offset 30%, min A$500k PDV QAPE, eligible activities, stackable with state incentives, exclusive with Producer/Location | ausfilm.com.au; arts.gov.au (Office for the Arts) | Section pinpoints not retrieved. Status: **partially supported** |
| AU QLD PDV 10% from 4/9/2026, min A$250k | Engine citation to screenqueensland.com.au (not re-fetched by me) | **Engine comparison evidence only; re-fetch pending** |

All other rules in the earlier packages (EU, NA state/provincial) **lack URLs/pinpoints in my packages**; engine citations are comparison evidence only. Retrieval attempts this session: 2 web searches (above). Remaining gap is large and is **not closed**.

## 3. Inventory reconciliation status (unresolved)
- NA universe (45 programs from snapshot keys) and ROW universe (81 RateRules + 90 canonical identities) were **not** reconciled against retained official inventories in this session. I listed the retained inventory modules (`backend/app/data/global_inventory*.py`, `program_slug_aliases.py`, `authority_coverage_registry.py`) but did not complete the comparison. Additions/aliases/exclusions: **not delivered**.
- The "9 omitted official programs" and Spanish foral/Canary rates (54%/45%, 35–60%, 45–50%) in the register were **not source-verified**; mark as `UNVERIFIED_CANDIDATE`, not findings.
- The earlier NA package's CPTC/Quebec and NY items remain as in prior adjudication; nothing re-verified here.

## 4. Net status
Completed: removal of unsupported Producer Offset cap from calculator; withdrawals above; partial AU authority retrieval.
Not completed: full source-URL/pinpoint register for every rule; universe reconciliation to official inventories; NA re-adjudication; recomputation of PDV/stack figures under QLD 10%. These remain open; **do not treat either package as verified.**
