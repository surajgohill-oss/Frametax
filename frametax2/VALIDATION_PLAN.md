# FrameTax 2.0 — Validation Plan

## Purpose

Before any incentive rate is used in a production finance decision,
it must be validated against a primary source document.
This document defines the validation workflow and the test cases
used to verify engine correctness.

---

## Confidence tier promotion workflow

```
1. Rate discovered (DISCOVERY)
   └── base_rate = NULL in database
   └── notes field documents approximate value and source

2. Rate extracted from PDF (PARSED)
   └── LLM or human extracts rate from authority document
   └── source_document_id linked to uploaded PDF
   └── is_llm_extracted = True if LLM extracted
   └── confidence_tier promoted to PARSED
   └── review_status = "under_review"

3. Rate manually verified (VERIFIED)
   └── Human reviewer confirms rate against primary source
   └── review_status = "approved"
   └── confidence_tier promoted to VERIFIED
   └── last_verified_date set

RULE: No rate may be promoted from DISCOVERY to VERIFIED
      without a linked source_document_id and human approval.
```

---

## Synthetic test cases

Eight synthetic test cases in `tests/fixtures/synthetic_projects.py`
and their corresponding tests in `tests/test_full_analysis.py`.

| # | Name | What it tests |
|---|------|---------------|
| 1 | US Domestic — Georgia | Single-state, single program, all-cash, DISCOVERY tier |
| 2 | Canadian Province — Ontario | CAD→USD conversion, 80% jurisdiction spend pct |
| 3 | ATL Cap | Program limits ATL qualifying spend to 25% of budget |
| 4 | BTL Local Labor | 60% jurisdiction spend pct reduces qualifying spend |
| 5 | Deferred Compensation | Deferred and equity items classified correctly |
| 6 | Regional Uplift | Georgia logo +10% uplift applied correctly |
| 7 | Legal Stacking ALLOWED | PSTC + CPTC — no violations |
| 8 | Legal Stacking PROHIBITED | Two programs with PROHIBITED rule — violation flagged |

Run tests:
```bash
cd backend
pytest tests/ -v
```

---

## Data validation before live use

### Jurisdictions that need rate verification

| Program | Approx rate | Authority | Verification source |
|---------|-------------|-----------|-------------------|
| California Film 3.0 | 20-25% | CDTFA / California Film Commission | film.ca.gov |
| Georgia EIIA | 20% + 10% logo | Georgia DOR | georgia.org/film |
| New York State Film | 25% + 5% NYC | Empire State Development | esd.ny.gov |
| New Mexico Film | ~25% | NM Taxation & Revenue | nmfilm.com |
| Louisiana Film | ~25% | Louisiana Entertainment | louisianaentertainment.gov |
| Ontario OPSTC | 21.5% | Ontario Creates | ontario.ca |
| Ontario OFTTC | varies | Ontario Creates | ontario.ca |
| BC PSTC | ~28% | Creative BC | creativbc.com |
| Quebec Film | ~25-35% | SODEC | sodec.gouv.qc.ca |
| Canada Federal CPTC | 25% labor | CRA | canada.ca |
| UK AVEC | ~34% | HMRC | gov.uk/hmrc |

**All rates above are APPROXIMATE and UNVERIFIED.**
Do not use in production finance calculations until promoted to VERIFIED.

---

## Regression test additions (as rates are verified)

When a rate is verified and promoted to VERIFIED tier, add a regression test:

```python
def test_georgia_eiia_base_rate_verified():
    """
    Georgia EIIA base rate is 20% as of [date].
    Source: Georgia DOR, [document title], page [N].
    source_document_id: [UUID of linked PDF].
    """
    prog = load_program_from_db("georgia_eiia")
    assert prog.base_rate == Decimal("0.20")
    assert prog.confidence_tier == "VERIFIED"
    assert prog.source_document_id is not None
```

---

## Production-use checklist

Before using a calculation output in a production finance decision:

- [ ] All claimed programs have `confidence_tier = VERIFIED`
- [ ] All programs have `source_document_id` linked to an uploaded PDF
- [ ] All `LocalCostBenchmark` multipliers are sourced and VERIFIED
- [ ] `has_unverified_inputs = False` on the `StructureCalculationResult`
- [ ] `legal_review_required = False` or legal review has been completed
- [ ] `jurisdiction_spend_pct` assumptions have been reviewed with line producer
- [ ] Any competitive program (`is_competitive = True`) has current allocation status confirmed

---

## Known gaps in v0.1.0

1. **No cost benchmark data** — `local_cost_benchmarks` table is empty.
   BTL rebasing will use multiplier=1.0 (no adjustment) until data is seeded.

2. **QualifyingSpendCategory records not seeded** — Programs exist but have
   no qualifying category rules. Qualifying spend will be $0 until rules are added.

3. **ProgramUplift records not seeded** — Uplifts (Georgia logo, NYC area bonus)
   must be added as `program_uplifts` rows.

4. **LegalStackingRule records not seeded** — OFTTC+CPTC stacking rules
   and other pairwise rules must be added.

5. **Qualification test rules not seeded** — `qualification_test_rules` table
   is empty. UK BFI test scoring uses the hardcoded fallback in
   `evaluate_qualification_tests.py` until rules are seeded from DB.
