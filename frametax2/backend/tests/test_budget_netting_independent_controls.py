"""Synthetic, source-shaped netting controls. No DB or real-project evaluation."""
import io
import unittest
from app.ingestion.budget_parser import parse_budget_csv, parse_budget_xlsx, _parse_amount

class BudgetNettingControls(unittest.TestCase):
    def test_signed_amounts(self):
        for raw in ("-250000", "$-250,000", "-$250,000", "(250,000)"):
            self.assertEqual(_parse_amount(raw), -250000)

    def test_csv_netting_is_separate_from_costs(self):
        result = parse_budget_csv("description,amount\nProduction costs,1000000\nTax Incentive,-250000\nNet Total,750000\n")
        self.assertEqual(result.total_budget_raw, 1000000)
        self.assertEqual(len(result.line_items), 1)
        self.assertEqual(len(result.source_incentive_estimates), 1)
        self.assertEqual(result.source_incentive_estimates[0].amount_usd, -250000)

    def test_xlsx_native_negative_netting_is_separate(self):
        from openpyxl import Workbook
        book = Workbook()
        for row in (("description", "amount"), ("Production costs", 1000000), ("EDB Rebate at 35%", -250000), ("Net Total", 750000)):
            book.active.append(row)
        buf = io.BytesIO()
        book.save(buf)
        result = parse_budget_xlsx(buf.getvalue())
        self.assertEqual(result.total_budget_raw, 1000000)
        self.assertEqual(len(result.line_items), 1)
        self.assertEqual(result.source_incentive_estimates[0].amount_usd, -250000)

    def test_financing_a_credit_remains_a_cost(self):
        # A financing fee is spending even when its description names a credit.
        result = parse_budget_csv("description,amount\nTax credit bridge financing fee,10000\n")
        self.assertEqual(result.total_budget_raw, 10000)
        self.assertEqual(len(result.source_incentive_estimates), 0)


class GreekCapControls(unittest.TestCase):
    def test_ordinary_grant_cap_and_approved_exception_are_distinct(self):
        from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
        from app.data.program_rate_rules import get_incentive_value_cap
        rule = get_incentive_value_cap("gr_cash_rebate")
        self.assertEqual(rule.cap_native_amount, 8000000)
        self.assertEqual(rule.exception_cap_native_amount, 10000000)
        base = _resolve_incentive_dollar_cap("gr_cash_rebate")
        approved = _resolve_incentive_dollar_cap("gr_cash_rebate", evidenced_requirement_facts=frozenset({rule.exception_approval_fact_key}))
        self.assertAlmostEqual(base[0], 8000000 / 0.87679, places=2)
        self.assertAlmostEqual(approved[0], 10000000 / 0.87679, places=2)
        self.assertIn("10,000,000", approved[2])

    def test_applying_for_exception_does_not_raise_cap(self):
        from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
        ordinary = _resolve_incentive_dollar_cap("gr_cash_rebate")
        applied = _resolve_incentive_dollar_cap("gr_cash_rebate", evidenced_requirement_facts=frozenset({"gr_strategic_project_exception_requested"}))
        self.assertEqual(ordinary[0], applied[0])


class QualificationMutationControls(unittest.TestCase):
    def test_category_corruptions_are_detected(self):
        from dataclasses import replace
        from unittest.mock import patch
        import app.calculators.qualification_derivation as qd
        from app.calculators.qualification_model import QualificationState as S
        from app.data.program_spend_rules import get_program_rules
        # Independent rule predicates: CA compensation summaries are mixed,
        # CA residual compensation excluded; unproven NM/MU deposits conditional.
        cases = [("ca_film_30", "US-CA", c, S.GREY_AREA_REQUIRES_AUTHORITY) for c in
                 ("atl_writer", "atl_producer", "atl_director", "atl_cast", "legal_accounting")]
        cases += [("ca_film_30", "US-CA", "residuals_reserve", S.EXCLUDED),
                  ("us_nm_film_credit", "US-NM", "residuals_reserve", S.GREY_AREA_REQUIRES_AUTHORITY),
                  ("mu_edb_incentive", "MU", "residuals_reserve", S.GREY_AREA_REQUIRES_AUTHORITY)]
        killed = 0
        for slug, jurisdiction, category, expected in cases:
            lines = [qd.BudgetLine("1100", "source account", 100000, spend_category=category)]
            def check():
                actual = qd.derive_qualification_register(lines, slug, qd.ProductionFacts(jurisdiction), .35)[0].state
                self.assertEqual(actual, expected)
            check()
            rules = dict(get_program_rules(slug))
            for false_value in (True, False):
                # A CA exclusion is corrupted to qualify or have no explicit rule;
                # mixed and fact-dependent rows are corrupted to qualify/exclude.
                mutated = dict(rules)
                if expected == S.EXCLUDED and false_value is False:
                    mutated.pop(category, None)
                elif category in mutated:
                    mutated[category] = replace(mutated[category], qualifies=false_value)
                else:
                    template = next(iter(get_program_rules("ca_film_30").values()))
                    mutated[category] = replace(template, qualifies=false_value)
                with patch.object(qd, "get_program_rules", return_value=mutated):
                    with self.assertRaises(AssertionError):
                        check()
                killed += 1
        self.assertEqual(killed, 16)


class GreekPricingControls(unittest.TestCase):
    def test_calculated_incentive_is_clipped_after_rate_and_qpe(self):
        from app.calculators.allocation_pricing import price_segment
        from app.calculators.production_allocation import AccountAllocation, AssignmentKind
        from app.data.program_rate_rules import get_incentive_value_cap
        alloc = AccountAllocation(account_code="3100", description="production crew", amount_usd=30000000,
            component="production", jurisdiction_code="GR", assignment_kind=AssignmentKind.FIXED,
            rationale="synthetic cap control", governing_decision="source rule control", line_id="gr-cost-1")
        kwargs = dict(jurisdiction_code="GR", program_slug="gr_cash_rebate", allocations=[alloc],
            spend_category_by_code={"3100":"btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
            production_type="feature_film", gross_budget_usd=40000000)
        ordinary = price_segment(**kwargs)
        self.assertTrue(ordinary.executable)
        self.assertAlmostEqual(ordinary.incentive_floor_usd, 8000000 / .87679, places=2)
        self.assertEqual(ordinary.incentive_uncapped_usd, 12000000)
        rule = get_incentive_value_cap("gr_cash_rebate")
        approved = price_segment(**kwargs, evidenced_requirement_facts=frozenset({rule.exception_approval_fact_key}))
        self.assertAlmostEqual(approved.incentive_floor_usd, 10000000 / .87679, places=2)


class TextNettingControls(unittest.TestCase):
    def test_generic_pdf_retains_estimate_without_counting_net_as_cost(self):
        from app.ingestion.budget_parser import parse_budget_from_text
        result = parse_budget_from_text("Crew $1,000,000\nTax Incentive 25%: ($250,000)\nNet Total $750,000")
        self.assertEqual(result.total_budget_raw, 1000000)
        self.assertEqual(len(result.line_items), 1)
        self.assertEqual(result.source_incentive_estimates[0].amount_usd, -250000)

    def test_explicit_netting_does_not_discard_financing_fee_in_pdf(self):
        from app.ingestion.budget_parser import parse_budget_from_text
        result = parse_budget_from_text("Tax credit bridge financing fee $10,000")
        self.assertEqual(result.total_budget_raw, 10000)
        self.assertEqual(result.source_incentive_estimates, [])


class SubsetUpliftControls(unittest.TestCase):
    def _price(self, slug, jurisdiction, rows, amounts=None, facts=None, kind="feature_film", confirmed=None):
        from app.calculators.allocation_pricing import price_segment
        from app.calculators.production_allocation import AccountAllocation, AssignmentKind
        allocations = [AccountAllocation(account_code=str(3000+i), description=category, amount_usd=amount,
            component="production", jurisdiction_code=jurisdiction, assignment_kind=AssignmentKind.FIXED,
            rationale="independent synthetic subset", governing_decision="primary subset rule",
            line_id=identity, spend_category=category) for i,(identity,category,amount) in enumerate(rows)]
        return price_segment(jurisdiction_code=jurisdiction, program_slug=slug, allocations=allocations,
            spend_category_by_code={}, offshore_payroll_accounts=frozenset(), gross_budget_usd=sum(r[2] for r in rows),
            amount_facts=amounts, evidenced_requirement_facts=facts, production_type=kind, confirmed_ceiling_programs=confirmed)

    def test_nm_rural_excludes_nonresident_btl_and_feature_does_not_add_tv(self):
        result = self._price("us_nm_film_credit", "US-NM", [("crew","btl_crew_labor",1000),("nonresident","btl_nonresident_labor",100),("goods","btl_equipment_rental",200)])
        self.assertTrue(result.executable)
        self.assertEqual(result.incentive_floor_usd, 325)
        # 25% all 1300 + 10% eligible 1200 + 5% facility upper bound 1300.
        self.assertEqual(result.incentive_ceiling_usd, 510)
        self.assertTrue(result.ceiling_requires_confirmation)

    def test_ca_uplifts_use_different_eligible_subsets(self):
        result = self._price("ca_film_30", "US-CA", [("crew","btl_crew_labor",1000),("vfx","vfx",200),("goods","btl_equipment_rental",100)])
        self.assertEqual(result.incentive_floor_usd, 455)
        # 35% all + 5% possible outside-LA + 10% local wages + 5% VFX only.
        self.assertEqual(result.incentive_ceiling_usd, 630)
        self.assertTrue(result.ceiling_requires_confirmation)

    def test_program_wide_ceiling_confirmation_cannot_create_subset_evidence(self):
        result = self._price("ca_film_30", "US-CA", [("crew","btl_crew_labor",1000)], confirmed=frozenset({"ca_film_30"}))
        self.assertEqual(result.incentive_floor_usd, 350)
        self.assertTrue(result.ceiling_requires_confirmation)

    def test_evidenced_partial_line_changes_floor_only_by_its_uplift(self):
        key = "uplift_basis:ca_film_30:outside_la_zone:crew"
        result = self._price("ca_film_30", "US-CA", [("crew","btl_crew_labor",1000)], amounts={key:600}, facts=frozenset({key}))
        self.assertEqual(result.incentive_floor_usd, 380)
        self.assertEqual(result.incentive_ceiling_usd, 480)

    def test_subset_cannot_exceed_qualified_line_or_be_nan(self):
        key = "uplift_basis:ca_film_30:outside_la_zone:crew"
        for amount in (1001, float("nan"), -1):
            result = self._price("ca_film_30", "US-CA", [("crew","btl_crew_labor",1000)], amounts={key:amount}, facts=frozenset({key}))
            self.assertFalse(result.executable)
            self.assertIn("qualified line amount", result.blockers[0])

    def test_tv_and_facility_are_mutually_exclusive(self):
        # The current executable NM registry admits features only. Test the
        # generic subset owner's exclusivity without claiming TV admission.
        from app.calculators.allocation_pricing import _price_subset_uplifts
        from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
        line = BudgetLine("3000", "crew", 1000, spend_category="btl_crew_labor", line_id="crew")
        register = derive_qualification_register([line], "us_nm_film_credit", ProductionFacts("US-NM"), .25)
        keys = {f"uplift_basis:us_nm_film_credit:{kind}:crew":1000 for kind in ("rural_location", "qualified_facility", "qualified_tv")}
        floor, ceiling, conditions = _price_subset_uplifts("us_nm_film_credit", [line], register, 1000, .25, "tv_series", keys, frozenset(keys))
        self.assertEqual(floor, 400)
        self.assertEqual(ceiling, 400)
        self.assertEqual(conditions, ())

    def test_independent_california_category_does_not_receive_vfx_uplift(self):
        result = self._price("ca_film_30", "US-CA", [("vfx","vfx",1000)], facts=frozenset({"ca_film_independent_category"}))
        self.assertEqual(result.incentive_ceiling_usd, 400)


class SourceDetailControls(unittest.TestCase):
    def _register(self, amount, children, category="atl_writer", atl="atl"):
        from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
        return derive_qualification_register([BudgetLine("1100", "SCRIPT", amount, spend_category=category,
            line_id="source-parent", source_subaccounts=tuple(children), source_atl_btl=atl)], "ca_film_30", ProductionFacts("US-CA"), .35)

    def test_writer_publication_research_and_duplication_conserve_parent(self):
        from app.calculators.qualification_model import QualificationState as S
        children=[{"account_code":str(code),"description":description,"amount_usd":amount} for code,description,amount in
            ((1109,"WRITER FEES",300000),(1110,"PUBLICATION",12500),(1124,"RESEARCH",1350),(1150,"DUPLICATION",303))]
        register=self._register(314153,children)
        self.assertEqual(sum(x.amount_usd for x in register),314153)
        self.assertEqual(sum(x.amount_usd for x in register if x.state==S.QUALIFIES),1653)
        self.assertEqual(sum(x.amount_usd for x in register if x.state==S.EXCLUDED),312500)

    def test_incomplete_detail_does_not_silently_qualify_parent_remainder(self):
        from app.calculators.qualification_model import QualificationState as S
        register=self._register(314153,[{"account_code":"1124","description":"RESEARCH","amount_usd":1350}])
        self.assertEqual(len(register),1)
        self.assertEqual(register[0].state,S.GREY_AREA_REQUIRES_AUTHORITY)
        self.assertEqual(register[0].amount_usd,314153)

    def test_line_producer_exception_is_conditional_and_capped(self):
        from app.calculators.qualification_model import QualificationState as S
        register=self._register(151198,[{"account_code":"1215","description":"LINE PRODUCER","amount_usd":151198}],"atl_producer")
        self.assertEqual(sum(x.amount_usd for x in register if x.state==S.EXCLUDED),51198)
        self.assertEqual(sum(x.amount_usd for x in register if x.state==S.GREY_AREA_REQUIRES_AUTHORITY),100000)
        self.assertEqual(sum(x.amount_usd for x in register if x.state==S.QUALIFIES),0)

    def test_atl_fringes_need_underlying_compensation_linkage(self):
        from app.calculators.qualification_model import QualificationState as S
        register=self._register(255291,[],"payroll_fringes")
        self.assertEqual(register[0].state,S.GREY_AREA_REQUIRES_AUTHORITY)
        self.assertEqual(register[0].amount_usd,255291)

    def test_movie_magic_detail_is_metadata_not_another_cost(self):
        from app.ingestion.budget_parser import _movie_magic_subaccounts
        pages=["1100 - SCRIPT\n1109\nWRITER FEES\nTotal\n$300,000\n1110\nPUBLICATION\nTotal\n$12,500\nTotal\n$314,153\n"]
        children=_movie_magic_subaccounts(pages)["1100"]
        self.assertEqual([x["amount_usd"] for x in children],[300000,12500])


class SourcePersistenceControls(unittest.TestCase):
    def test_subaccounts_round_trip_without_creating_more_cost_rows(self):
        # Synthetic temp table on isolated DB; public project rows untouched.
        import uuid
        from sqlalchemy import create_engine, insert, select, text
        from app.models.budget import BudgetLineItem
        engine = create_engine("postgresql+psycopg://frametax:frametax@localhost:5432/frametax2_pytest")
        detail = [{"account_code": "1124", "description": "RESEARCH", "amount_usd": 1350, "page_ref": 3}]
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("select current_database()")).scalar_one(), "frametax2_pytest")
            conn.execute(text("create temporary table budget_line_items (like public.budget_line_items including defaults) on commit drop"))
            conn.execute(insert(BudgetLineItem.__table__).values(budget_document_id=uuid.uuid4(), description="1100 SCRIPT", amount_usd=1350, source_subaccounts=detail))
            rows = conn.execute(select(BudgetLineItem.__table__.c.amount_usd, BudgetLineItem.__table__.c.source_subaccounts)).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(float(rows[0].amount_usd), 1350)
            self.assertEqual(rows[0].source_subaccounts, detail)
            conn.rollback()
        engine.dispose()

    def test_zero_authored_parent_keeps_a_register_identity(self):
        from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
        line = BudgetLine("1100", "SCRIPT", 0, spend_category="atl_writer", source_subaccounts=({"account_code":"1124", "description":"RESEARCH", "amount_usd":0},))
        rows = derive_qualification_register([line], "ca_film_30", ProductionFacts("US-CA"), .35)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].account_code, "1100")


class SourceFingerprintControls(unittest.TestCase):
    def test_changed_detail_and_atl_linkage_invalidate_fingerprint(self):
        from dataclasses import replace
        from app.calculators.qualification_derivation import BudgetLine
        from app.services.canonical_project_economics import ProjectEconomicInputs
        from app.services.canonical_evaluation import _compute_fingerprint
        line = BudgetLine("1100", "SCRIPT", 1000, spend_category="atl_writer")
        inputs = ProjectEconomicInputs("synthetic", "synthetic", "US-CA", "feature_film", 1000, 1000, [line], {"1100":"atl_writer"}, frozenset(), frozenset())
        original = _compute_fingerprint(inputs)
        detailed = replace(inputs, budget_lines=[replace(line, source_subaccounts=({"account_code":"1124", "description":"RESEARCH", "amount_usd":1000},))])
        self.assertNotEqual(original, _compute_fingerprint(detailed))
        self.assertNotEqual(original, _compute_fingerprint(replace(inputs, budget_lines=[replace(line, source_atl_btl="atl")])))


class SourceIdentityControls(unittest.TestCase):
    def test_changed_source_identity_invalidates_line_evidence(self):
        from dataclasses import replace
        from app.calculators.qualification_derivation import BudgetLine
        from app.services.canonical_project_economics import ProjectEconomicInputs
        from app.services.canonical_evaluation import _compute_fingerprint
        line = BudgetLine("1100", "SCRIPT", 1000, spend_category="atl_writer", line_id="source-a")
        inputs = ProjectEconomicInputs("synthetic", "synthetic", "US-CA", "feature_film", 1000, 1000, [line], {"1100":"atl_writer"}, frozenset(), frozenset())
        self.assertNotEqual(_compute_fingerprint(inputs), _compute_fingerprint(replace(inputs, budget_lines=[replace(line, line_id="source-b")])))
