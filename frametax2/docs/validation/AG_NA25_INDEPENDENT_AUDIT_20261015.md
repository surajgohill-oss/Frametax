# Independent NA audit of Claude commit `516136c3` (2026-10-15)

Auditor: AG-owned record, written by the independent audit pass. Snapshot: a detached worktree at exactly `516136c3` (parent comparisons at `21fc69c6`, AG-count checks at `3455dc95`). The live working copy was not used or modified; all database work ran on `frametax2_pytest` with synthetic projects that were deleted afterwards; no real anchor was opened, evaluated or regenerated. **Fresh execution** below means commands run in this pass; **inherited** means a number copied from an earlier report and not re-run.

## 1. Fresh focused execution (all in the snapshot)

| Check | Result |
|---|---|
| Focused controls: fact parity, persisted facts, line allocations, line inputs, Manitoba wording and arithmetic, stack bridge, payee caps | 89 passed |
| Seven NA suites that AG counted (same files as `NA_42_CONTROL_REPRODUCTION_AND_DISPOSITION.md` section 6) | 197 passed at `516136c3`; 196 passed at `3455dc95` (see section 6) |
| Independent probes (appendix A, written by this audit, not by the author) | 5 passed |
| Full-pipeline probes on synthetic projects (evaluate, then read the served view) | see 2 to 4 |

## 2. Producer facts and allocations on every pricing path - VERIFIED

* **Allocations reach pricing.** A line allocation written through `write_ny_program_facts` appears in `build_project_economic_inputs(...).inputs.amount_facts` (`alloc_n/alloc_ord/alloc_usd:<line>`), and a spy on `line_allocations.allocations_of` saw 309 non-empty reads during one full evaluation.
* **Nova Scotia, full evaluation, every served structure that contains the program** (home MU, crew line 1,000,000, floors in USD): direct `full_relocation` none 575,000.00 / one person holding the line 431,119.56 / two people (700,000 and 300,000) 506,119.56; stack with federal PSTC 767,000.00 / 623,119.56 / 698,119.56; stack with federal CPTC 833,750.00 / 711,451.63 / 775,201.63. The one-person allocation equals the legacy single-payee row on all three paths (identical to the cent), and the two-person reduction equals the one-person reduction minus B's untouched 75,000, so each person is applied once. In the CPTC stack the net movement is 0.85 times the standalone reduction (122,298.37 against 143,880.44) for the legacy row as well; this is explained, not a defect: the Nova Scotia credit is assistance that lowers the CPTC cost base (ledger: CPTC labour cap = 60% x (cost - assistance)), so removing 143,880.44 of Nova Scotia incentive raises the CPTC by 143,880.44 x 25% x 60% = 21,582.07 and the stack total falls by 122,298.37.
* **Montana, full evaluation** (five Montana prerequisite amount facts stated): ceiling none 625,000 / one person 525,000 / two people 600,000 (= 625,000 - 250,000 + 150,000 + 75,000). Without those prerequisite facts the served ceiling is 805,000 in all three cases because the segment never reaches the compensation branch: person caps do not tighten the potential until the Montana prerequisites are stated (observation, not a regression: the unstated case is a conservative upper bound).
* **Producer-fact parity.** BC (home CA-BC): the schedule-derived day fact is identical in all 8 served structures that include `ca_bc_pstc` (1 single, 3 two-program, 3 three-program, 1 four-program stack). Missouri: a stated Yes and a stated No stay PRODUCER_STATED and the scenario fact stays SCENARIO_ASSUMED in the served Missouri structure (only one Missouri structure is served for that fixture, so no Missouri stack was available to compare).

## 3. Multiple people on one line; Montana and Nova Scotia caps - VERIFIED

Appendix A: Montana two people on one line equal the same people on two lines (225,000 both); a person split across lines and shared inside a line is one person once (225,000); Nova Scotia two people on one line equal two lines and a whole-line person equals the cap exactly. Browser (own fixtures, deleted): the Montana editor on a Montana-home project showed per-person Montana status and residency, accepted two people, saved one row (`[{600000 student}, {300000 veteran_tribal}]`), created exactly one generation (1 to 2), restored people and totals on a cold reload, Cancel restored the saved people, and removing everyone and saving deleted the row (generations stayed at 2 because the restored inputs match the first generation).

## 4. Canadian labour facts - an ACTUAL executable gap

`canadian_labour_basis._line_eligible_amount` reads `canadian_status`, `service_location`, `payee_type`, `payment_status`, look-through wages, assistance and related-party only from line-level `line_fact` rows. A line paid 600,000 to a resident and 400,000 to a non-resident can only be stated as all resident (1,000,000 eligible) or all non-resident (0): probe `test_a_line_paid_to_a_resident_and_a_nonresident_has_only_all_or_nothing_representation`. The allocation mechanism does not supply these inputs: `line_allocations.PERSON_FIELDS` omits them, and a `canadian_status` or `service_location` inside an allocation is **accepted and silently dropped** (probe `test_a_canadian_status_inside_an_allocation_is_silently_dropped`). Two repairs are needed: reject unknown allocation fields loudly, and either add per-person Canadian facts with a consumer in the labour basis or keep the line-level fields and require the producer to split the budget line.

## 5. Overview resets the selected structure after evaluation - NOT an NA-25 regression; a real pre-existing defect with a reproducible control

* Backend selection is preserved: with the selection stored as the real PATCH does (`leading_structure_id` plus `leading_selection_identity`), a changed-input evaluation (a stated amount fact, or a line allocation) leaves `production.leading_selection = user_selected, unavailable=false` and `leading_structure_id` equal to the regenerated structure, at both `516136c3` and `21fc69c6`.
* The defect is the served page: `canonical_production_view.py` pins only `canonical_selected_structure_id`, the leading conditional structure and the baseline at the head of the 100-entry candidate page (`_pinned`); the **producer-selected** leading structure is not pinned. Control (appendix B): evaluate a synthetic MU project (169 candidates), store a selection on a candidate beyond page one, read page one: `leading_structure_id` equals the pick and `user_selected` is true, but the pick is **absent from the first page** (identical at `21fc69c6` and `516136c3`). The Overview and Workspace look the structure up in that page (`activeStructure(allocated, leadingStructureId)`), find nothing and silently fall back to the best-priced candidate, which is the reset observed after an evaluation re-ranks the structure past position 100.
* The earlier probe that overwrote `leading_structure_id` without the identity is not evidence either way and was discarded.

## 6. Why Montana could not be selected for browser verification

Same defect, not a fixture defect: on a Missouri-home fixture no Montana structure is inside the first 100 of 169 candidates (probe: Montana present False, `production.leading_structure_id` correct, `user_selected` true after a real PATCH), so the Overview cannot display it, and the Workspace offers a "Set as leading" button only on the cards it renders. On a Montana-home fixture the Montana baseline is pinned into the page, the panel appeared with the people editor on all three personnel lines, and the full Montana flow above passed.

## 7. Manitoba - VERIFIED

Repository search of `app`, `alembic`, `tests` and the ledger finds the withdrawn claim only inside the withdrawal notes and the recurrence control; `test_manitoba_evidence_wording_controls.py` (3) and `test_manitoba_controls.py` pass fresh and the hand-checked arithmetic is unchanged (PSTC 96,000 on labour 600,000 with Manitoba 270,000 gives 43,200; CPTC 109,500).

## 8. Anchor-dependent controls: one deduplicated inventory

Inventory file: `docs/validation/NA_ANCHOR_CONTROL_INVENTORY_20261015.csv`, keyed by exact pytest node id.

* The reconciled set is 42 node ids. The additional-failures document has **178 listing rows but 173 unique node ids**: five nodes appear twice (a call failure plus a teardown error, all five in `test_jurisdiction_preference.py`), so five rows are duplicate listings, not controls. The two sets share no node id.
* **Exact unique denominator: 42 + 173 = 215 controls** in 33 test files.
* Terminal classification (static analysis by the manifest generator, with failure signatures and rollback evidence):

| Terminal class | 42 | 173 | Total |
|---|---|---|---|
| valid read-only retained-result control | 30 | 69 | 99 |
| valid evaluation / idempotence control | 9 | 90 | 99 |
| intentionally generation-creating control | 2 | 1 | 3 |
| mutating control requiring restoration (writes named under an anchor id, restored by finally block or rollback) | 1 | 12 | 13 |
| fixture / setup defect | 0 | 0 | 0 |
| duplicate (as a control) | 0 | 0 | 0 |
| obsolete / superseded, with executable evidence | 0 | 1 | 1 |

* **The one obsolete control** is `test_copro_conditional_pricing_bridge.py::test_conditional_scenario_routes_same_jurisdiction_multi_slug_through_stack_engine`. It is fully synthetic (monkeypatched treaty, no anchor, no database) and asserts `rule_type == "mutually_exclusive"` for `on_opstc + ca_federal_cptc`; `stacking_rules._SLUG_PAIR_RULES` holds `"spend_reduction"` since `a9362921` (NA-CODEX-08, Ontario Creates OPSTC Guidelines s.1.01). It fails identically at `21fc69c6` and `516136c3` without any database, so it was wrongly counted as an anchor-dependent control. It is not rewritten here.
* **Evidence strength and the unproven remainder.** 199 of the 215 fail with a lookup-failure signature on the first anchor read (`PROJECT_NOT_FOUND`, `Project not found`, `KeyError`/`NoneType` from an absent project, DB-name guard, write guard); 15 fail on an assertion whose final frame reads data keyed by the absent project (empty dict, `None`, empty list); 1 is the obsolete control. **No control has been executed against an anchor**, so none can be called a pass: 214 anchor-dependent controls are unverified until the authorized run, and the 15 weaker-signature controls are the part of that remainder where a second defect could still hide. The anchor-less-looking cases (`test_bounded_evaluation_response.py`, `test_bulk_evaluation_persistence.py`) use `BAD_HOMBRES_PROJECT_ID` as a constant inside `uuid.UUID(...)`, which the static analyzer does not resolve.
* Nothing was registered, deselected, weakened or removed. The isolated database holds none of the four anchor ids (a different project titled "The Little Utopia" with another id exists in `frametax2_pytest` and is untouched).

## 9. Corrections to earlier counting statements

AG's `NA_42_CONTROL_REPRODUCTION_AND_DISPOSITION.md` (branch `ag/exhaustive-optimizer-audit`, not edited) states 24 real-anchor-required and 18 synthetic-equivalent controls. Its own node lists contain **23 and 19** numbers (23 + 19 = 42): the correct split by its own lists is **23 / 19**. Its executive summary says the 196 passes took 32.1 seconds while its table sums to 39.01 seconds. It says 41 of 42 controls are strictly read-only; the manifest classification of the same 42 is 30 read-only, 9 evaluate-idempotent, 2 generation-creating, 1 mutating.

Mistaken claims made by Claude in the register entry `NA-AG-COUNT-01` (commit `516136c3`), now corrected there: (a) "196 total versus 197 visible" compared different commits: the seven suites give **196 at `3455dc95` (AG's snapshot) and 197 at `516136c3`** because NA-24 added one test to the Montana/locality suite; AG's 196 is correct for its snapshot. (b) "17 adjudication tests versus 18 passed in the log" is unsupported: AG's table and fresh runs at both commits show 17. Only the 18/19 and 24/23 miscount is a genuine AG error.

## 10. Result summary

* Passed independently: allocation parity on direct, stack and hybrid paths; Montana and Nova Scotia exact-once caps; Manitoba wording and arithmetic; Montana editor flow; producer-fact parity across BC structures.
* Actual regressions in `516136c3`: **two, found on the ledger recheck (section 11): R1 per-payee caps over-exclude on partial allocations; R2 saving allocations deletes the Canadian-labour `payee_type`.** (An earlier version of this line said none.)
* Defects found (pre-existing unless stated): producer-selected leading structure not pinned in the served candidate page (reproducible control, appendix B); allocation fields with no consumer are silently dropped by the writer (introduced in `516136c3`); one obsolete synthetic control (`...multi_slug_through_stack_engine`).
* Remaining NA obligations: see the ledger-derived list in section 11.
* **Next Claude repair:** see section 11 (R1 and R2 first).

## 11. Ledger reconciliation and corrections to sections 2 to 10 (added after review against the production ledger)

This audit first leaned on Claude's own NA-25 ledger section, its manifest generator and its tests. Rechecking against `CAPABILITY_LEDGER.md` (Item 14, NA-18 to NA-25) and executing what the ledger states found **two real regressions that sections 2 to 10 missed**, and corrected three statements.

**R1 - partial allocations over-exclude every per-payee cap (regression in `516136c3`).** `per_payee_limits.apply_payee_cap` divides a person's allocation by the SUM OF THE ALLOCATIONS on the line (`line_total = sum(u ...)`), not by the line amount, although its docstring says the part assigned to nobody is never capped. A person holding part of a line is therefore charged for the whole line. Fresh probe (one person holds 1.2 x cap of a line worth 2 x cap; the rest is assigned to nobody): expected excluded / got - Georgia 100,000 / 500,000; Colorado 200,000 / 1,000,000; New Jersey 150,000 / 750,000; Arkansas 100,000 / 500,000; Illinois 100,000 / 500,000. A full-line allocation and the legacy single-payee row are correct, which is why the author's tests and section 3 did not see it. Georgia example: A holds 400,000 of the 700,000 director line and 300,000 of a writer line (700,000 in all): the cap excludes 200,000; the code excludes 500,000. Nova Scotia and Montana divide by the budget line and are correct (appendix A).

**R2 - saving allocations deletes the line's `payee_type`, which the Canadian labour basis consumes (regression in `516136c3`).** `write_ny_program_facts(line_allocations=...)` clears `payee_type` (with `payee_id`, `payee_compensation_complete`, `mt_*`) on the line, and the editor hides that line field once people exist. But `canadian_labour_basis` reads the line-level `payee_type` (foreign and non-taxable corporations are excluded; loan-out and personal-service corporations need look-through facts); the ledger's NA-24 OPEN item 3 already named the shared payee-type vocabulary. Probe (BC project, crew line 1,000,000 stated `payee_type=foreign_corp`, resident, in Canada): before saving two people the line contributes no qualified labour; after saving the allocation the stored line facts are `allocations, canadian_status, role, service_location` and qualified labour is CPTC 960,000 and PSTC 1,000,000: a foreign corporation's pay became eligible Canadian labour. The allocation's own `payee_type` is read only by the per-payee caps, never by the labour basis. This makes section 4's gap worse than "not represented": the existing line-level fact is destroyed.

**Corrections.** (a) Section 10 said "actual regressions in `516136c3`: none": wrong, R1 and R2. (b) Section 2 called the CPTC-stack 0.85 factor unexplained: it is the ledger's CPTC cost-base netting (above). (c) Sections 2 and 3 said allocations are verified for "caps" generally: only Montana and Nova Scotia had been executed; the per-payee programs had not, and fail partial allocations (R1). (d) The remaining-obligations list in section 10 was thin; the ledger-derived list is below. (e) Where this audit agrees with the ledger: Item 14 (2026-10-08) states the producer's leading choice is stored by economic identity and re-resolved on the served read, which the audit reproduced; the first-page pinning gap in section 5 is not recorded anywhere in the ledger (the older 2026-08 entries calling "Set as Leading" client-side-only are superseded by Item 14). (f) The inventory classification in section 8 rests on Claude's static manifest analyzer plus failure signatures; it is evidence of why each node fails in the isolated database, not evidence that any node passes against an anchor.

**Remaining NA obligations, from the ledger (NA-18 to NA-25), excluding ROW, selective funds and benchmarks:**
1. Repair R1 and R2 above, then re-run the per-payee and Canadian-labour controls with partial and mixed allocations.
2. Per-person Canadian labour facts (section 4).
3. Producer-selected leading structure pinned in the served page (section 5).
4. Locality sources: Missouri rural/blighted method (DED guideline located, text unreadable), the six reference coordinates (Halifax, Fredericton, Moncton, Saint John, Regina, Saskatoon), BC designated-area geometry, Missouri Newton and Franklin counties.
5. PSTC labour share of all-spend provincial credits (no authority states a method; assumed).
6. Montana: the `(13)(b)(vi)` postproduction-expenditure exclusion conflict (safe upper bound applied); person-level compensation is now supported only when entered, and the potential is not cap-refined until the five Montana prerequisite amount facts are stated.
7. New Brunswick Deemed Spend and Bonus Incentive worksheets (portal-only source) and the applicant-eligibility facts.
8. Nova Scotia Administrator approvals and exceptions, and Saskatchewan's exception above CAD 5 million (discretionary, unpriced).
9. BC documentaries and photography before 2016-10-01 / 2008; BC series regional and distant credits on qualifying episodes only.
10. Producer-fact controls still missing for the pre-NA-16 facts (New York post facility, Production Plus, Ontario / Texas / Colorado / Oregon award facts).
11. The authorized acceptance run for 214 anchor-dependent controls and the owner decision on the one obsolete control; independent verification of the Overview and Workspace; the rollout (restart, migrations, bounded regeneration: every digest-module edit in NA-22 to NA-25 stales all four productions until regenerated).

**Next Claude repair (replaces section 10):** fix `apply_payee_cap` to divide by the budget entry amount (never by the allocation sum) and stop `write_ny_program_facts` from deleting `payee_type` (and any other field a different consumer reads); add controls for partial and mixed allocations on all five per-payee programs and for payee_type survival; then pin the producer-selected structure in the served page.

## Appendix A - independent probes (run fresh, 5 passed)

```python
"""Independent audit probes for NA-RECONCILIATION-25 (commit 516136c3). DB-free except where noted."""
import uuid, pytest
from types import SimpleNamespace
from app.calculators import line_allocations as la
from app.calculators.canadian_labour_basis import derive_canadian_labour_basis
from tests.test_na_line_inputs_controls import _price as mt_price
from tests.test_na_policy_formula_controls import _price as ns_price, _cad_per_usd

def facts(by_line, amts):
    names=[a["payee_id"] for al in by_line.values() for a in al]
    return la.amount_facts(by_line, la.person_ordinals(names), amts)

def test_montana_two_people_one_line_equals_the_same_people_on_two_lines():
    one=[("L1","btl_resident_labor",1_000_000.0)]
    two=[("L1","btl_resident_labor",700_000.0),("L2","btl_resident_labor",300_000.0)]
    a=mt_price(one,facts({"L1":[{"payee_id":"A","amount_usd":700_000.0},{"payee_id":"B","amount_usd":300_000.0}]},{"L1":1_000_000.0}))
    b=mt_price(two,{"ny_atl_payee:L1":1.0,"ny_atl_payee:L2":2.0})
    assert a==pytest.approx(b) and a==pytest.approx((225_000.0,225_000.0))

def test_montana_a_person_across_lines_and_inside_a_shared_line_is_one_person_once():
    lines=[("L1","btl_resident_labor",600_000.0),("L2","btl_resident_labor",400_000.0)]
    shared=facts({"L1":[{"payee_id":"A","amount_usd":300_000.0},{"payee_id":"B","amount_usd":300_000.0}],"L2":[{"payee_id":"A","amount_usd":400_000.0}]},{"L1":600_000.0,"L2":400_000.0})
    legacy=mt_price([("L1a","btl_resident_labor",300_000.0),("L1b","btl_resident_labor",300_000.0),("L2","btl_resident_labor",400_000.0)],{"ny_atl_payee:L1a":1.0,"ny_atl_payee:L1b":2.0,"ny_atl_payee:L2":1.0})
    assert mt_price(lines,shared)==pytest.approx(legacy)
    assert legacy==pytest.approx((225_000.0,225_000.0))

def test_nova_scotia_cap_two_people_one_line_equals_two_lines_and_counts_each_person_once():
    cap=150_000.0/_cad_per_usd()
    one=ns_price("ca_ns_production_incentive_fund","CA-NS",[("btl_crew_labor",1_000_000.0)],amounts=facts({"S0":[{"payee_id":"A","amount_usd":700_000.0},{"payee_id":"B","amount_usd":300_000.0}]},{"S0":1_000_000.0}))
    two=ns_price("ca_ns_production_incentive_fund","CA-NS",[("btl_crew_labor",700_000.0),("atl_cast",300_000.0)],amounts={"ny_atl_payee:S0":1.0,"ny_atl_payee:S1":2.0})
    assert one.incentive_floor_usd==pytest.approx(two.incentive_floor_usd)
    assert one.incentive_floor_usd==pytest.approx(0.25*1_000_000.0-(0.25*700_000.0-cap))
    whole=ns_price("ca_ns_production_incentive_fund","CA-NS",[("btl_crew_labor",1_000_000.0)],amounts=facts({"S0":[{"payee_id":"A","amount_usd":1_000_000.0}]},{"S0":1_000_000.0}))
    assert whole.incentive_floor_usd==pytest.approx(cap,rel=1e-4)

def test_a_canadian_status_inside_an_allocation_is_silently_dropped():
    from app.services.line_inputs import field_specs
    out=la.validate("L1",1000.0,[{"payee_id":"A","amount_usd":600.0,"canadian_status":"nonresident","service_location":"outside_canada"}],field_specs())
    assert "canadian_status" not in out[0] and "service_location" not in out[0]   # accepted without error, not stored, not consumed

def _line(i,amt): return SimpleNamespace(line_id=i,amount_usd=amt,spend_category="btl_crew_labor",is_memo=False)
def _row(i,f,v): return SimpleNamespace(fact_key=f"line_fact:{i}:{f}",value=v)

def test_a_line_paid_to_a_resident_and_a_nonresident_has_only_all_or_nothing_representation():
    ln=[_line("L1",1_000_000.0)]
    def eligible(status):
        r=derive_canadian_labour_basis(ln,[_row("L1","canadian_status",status),_row("L1","service_location","in_canada"),_row("L1","role","other")],2_000_000.0)
        return r.evidenced_eligible_labour_usd["ca_federal_pstc"]
    # 600,000 paid to a resident and 400,000 to a non-resident: the line-level fact can only say one or the other
    assert eligible("resident_citizen")==1_000_000.0 and eligible("nonresident")==0.0   # the true figure (600,000) is unreachable

```

## Appendix B - leading-structure page control (fails at `21fc69c6` and `516136c3`)

```python
import asyncio, uuid, sys
sys.path.insert(0,".")
from sqlalchemy import select
from tests.isolated_records import create_synthetic_project, isolated_session
from app.services import canonical_evaluation as ce
from app.services.leading_selection import selection_identity
from app.services.canonical_production_view import build_production_and_structures
from app.models.project import Project
LINES=(("1000","CAST","atl_cast","atl",600_000.0),("3100","CREW","btl_resident_labor","btl",1_000_000.0),("3200","EQUIPMENT","btl_equipment_rental","btl",700_000.0))
async def main():
    async with isolated_session() as db:
        pid=await create_synthetic_project(db,home_code="MU",lines=LINES); u=uuid.UUID(pid)
        await ce.evaluate_project(db,u)
        v1=await build_production_and_structures(db,pid)
        p1={e["structure_id"] for e in v1["structures"]["allocated_structures"]["structures"]}
        v2=await build_production_and_structures(db,pid,candidate_offset=100)
        beyond=[e for e in v2["structures"]["allocated_structures"]["structures"] if e["structure_id"] not in p1][0]
        p=(await db.execute(select(Project).where(Project.id==u))).scalar_one()
        sid=uuid.UUID(beyond["structure_id"]); p.leading_structure_id=sid; p.leading_selection_identity=await selection_identity(db,sid); await db.flush()
        v=await build_production_and_structures(db,pid)
        page={e["structure_id"] for e in v["structures"]["allocated_structures"]["structures"]}
        print("served leading id == pick:",str(v["production"]["leading_structure_id"])==str(sid),"| user_selected:",v["production"]["leading_selection"],"| pick present in first served page:",str(sid) in page, "| programs",beyond["program_slugs"])
asyncio.run(main())

```
Output at both commits: `served leading id == pick: True | user_selected: True | pick present in first served page: False`.

## Appendix C - ledger-recheck probes (R2: payee_type deleted by an allocation save)

```python
import asyncio, uuid, sys
sys.path.insert(0,".")
from sqlalchemy import select
from tests.isolated_records import create_synthetic_project, isolated_session
from app.services import ny_producer_facts as npf
from app.services.line_inputs import line_inputs_view
from app.services.canonical_project_economics import build_project_economic_inputs
from app.models.project_fact import ProjectFact
LINES=(("1000","CAST","atl_cast","atl",600_000.0),("3100","CREW","btl_crew_labor","btl",1_000_000.0))
PROGS=["ca_federal_cptc","ca_federal_pstc","ca_ns_production_incentive_fund"]
async def labour(db,u):
    r=await build_project_economic_inputs(db,u)
    af=r.inputs.amount_facts
    return {k:v for k,v in af.items() if "qualified_labour" in k}
async def main():
    async with isolated_session() as db:
        pid=await create_synthetic_project(db,home_code="CA-BC",lines=LINES); u=uuid.UUID(pid)
        v=await line_inputs_view(db,u,PROGS); lid=next(l["line_id"] for l in v["lines"] if l["category"]=="btl_crew_labor")
        await npf.write_ny_program_facts(db,u,line_facts=[{"line_id":lid,"field":"payee_type","value":"foreign_corp"},{"line_id":lid,"field":"canadian_status","value":"resident_citizen"},{"line_id":lid,"field":"service_location","value":"in_canada"},{"line_id":lid,"field":"role","value":"other"}])
        print("before allocation:",await labour(db,u))
        await npf.write_ny_program_facts(db,u,line_allocations=[{"line_id":lid,"allocations":[{"payee_id":"A","amount_usd":600_000.0},{"payee_id":"B","amount_usd":400_000.0}]}])
        rows=(await db.execute(select(ProjectFact.fact_key,ProjectFact.value).where(ProjectFact.project_id==u,ProjectFact.fact_key.like("line_fact:%")))).all()
        print("stored line facts after:",sorted(k.split(":",2)[2] for k,_ in rows))
        print("after allocation :",await labour(db,u))
asyncio.run(main())
```
Output: `before allocation: {}` then `stored line facts after: ['allocations','canadian_status','role','service_location']` and `after allocation: {'ca_federal_cptc_qualified_labour_usd': 960000.0, 'ca_federal_pstc_qualified_labour_usd': 1000000.0}`.

R1 reproduces with `per_payee_limits.apply_payee_cap` on `ProductionFacts(payee_allocations_by_line=((line, ((ordinal, usd, type_code),)),))` for every program in `PAYEE_CAPS` (one person holding 1.2 x cap of a 2 x cap line returns an exclusion of the full cap instead of 0.2 x cap).
