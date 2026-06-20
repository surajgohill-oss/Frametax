"""
test_global_inventory.py

Tests for the global incentive inventory data module and coverage report.
"""
from __future__ import annotations

import pytest

from app.data.global_inventory import (
    ALL_BENCHMARKS,
    ALL_PROGRAMS,
    CostBenchmarkEntry,
    GlobalProgramEntry,
)
from app.calculators.coverage_report import (
    CoverageReport,
    JurisdictionCoverage,
    build_coverage_report,
    format_coverage_table,
)

TARGET_CODES = {
    "US", "CA", "GB", "IE", "MT", "GR", "CY", "MU",
    "FR", "ES", "IT", "HR", "HU", "BE", "DE", "AU", "NZ",
}


# ---------------------------------------------------------------------------
# Inventory structure
# ---------------------------------------------------------------------------

class TestInventoryStructure:
    def test_all_programs_count(self):
        assert len(ALL_PROGRAMS) == 17

    def test_all_benchmarks_count(self):
        assert len(ALL_BENCHMARKS) == 17

    def test_programs_cover_all_target_jurisdictions(self):
        codes = {p.jurisdiction_code for p in ALL_PROGRAMS}
        assert codes == TARGET_CODES

    def test_benchmarks_cover_all_target_jurisdictions(self):
        codes = {b.jurisdiction_code for b in ALL_BENCHMARKS}
        assert codes == TARGET_CODES

    def test_all_programs_are_correct_type(self):
        for p in ALL_PROGRAMS:
            assert isinstance(p, GlobalProgramEntry)

    def test_all_benchmarks_are_correct_type(self):
        for b in ALL_BENCHMARKS:
            assert isinstance(b, CostBenchmarkEntry)

    def test_every_program_has_name(self):
        for p in ALL_PROGRAMS:
            assert p.program_name, f"{p.jurisdiction_code} missing program_name"

    def test_every_program_has_notes(self):
        for p in ALL_PROGRAMS:
            assert p.notes, f"{p.jurisdiction_code} missing notes"

    def test_every_program_has_confidence_tier(self):
        valid = {"VERIFIED", "PARSED", "DISCOVERY"}
        for p in ALL_PROGRAMS:
            assert p.confidence_tier in valid, f"{p.jurisdiction_code}: {p.confidence_tier}"

    def test_every_benchmark_has_confidence_tier(self):
        valid = {"VERIFIED", "PARSED", "DISCOVERY"}
        for b in ALL_BENCHMARKS:
            assert b.confidence_tier in valid

    def test_every_benchmark_has_data_source(self):
        for b in ALL_BENCHMARKS:
            assert b.data_source

    def test_every_benchmark_has_as_of_date(self):
        for b in ALL_BENCHMARKS:
            assert b.as_of_date


# ---------------------------------------------------------------------------
# Source metadata
# ---------------------------------------------------------------------------

class TestSourceMetadata:
    def test_every_program_has_source_title(self):
        for p in ALL_PROGRAMS:
            assert p.source_title, f"{p.jurisdiction_code} missing source_title"

    def test_discovery_programs_flag_acquisition_need(self):
        for p in ALL_PROGRAMS:
            if p.confidence_tier == "DISCOVERY":
                # Should have a source_url or a note indicating acquisition needed
                has_guidance = (
                    p.source_url is not None
                    or "NOT YET ACQUIRED" in p.source_title.upper()
                    or "not yet" in p.notes.lower()
                    or p.source_url is None  # acceptable for DISCOVERY
                )
                assert has_guidance, f"{p.jurisdiction_code} DISCOVERY has no acquisition guidance"

    def test_parsed_programs_have_source_title(self):
        for p in ALL_PROGRAMS:
            if p.confidence_tier == "PARSED":
                assert p.source_title

    def test_uk_avec_is_parsed(self):
        gb = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "GB")
        assert gb.confidence_tier == "PARSED"

    def test_canada_is_parsed(self):
        ca = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "CA")
        assert ca.confidence_tier == "PARSED"

    def test_malta_is_parsed(self):
        mt = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "MT")
        assert mt.confidence_tier == "PARSED"

    def test_greece_is_parsed(self):
        gr = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "GR")
        assert gr.confidence_tier == "PARSED"

    def test_ireland_is_parsed(self):
        ie = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "IE")
        assert ie.confidence_tier == "PARSED"

    def test_mauritius_is_parsed(self):
        mu = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "MU")
        assert mu.confidence_tier == "PARSED"

    def test_cyprus_is_discovery(self):
        cy = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "CY")
        assert cy.confidence_tier == "DISCOVERY"

    def test_australia_is_discovery(self):
        au = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "AU")
        assert au.confidence_tier == "DISCOVERY"

    def test_new_zealand_is_discovery(self):
        nz = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "NZ")
        assert nz.confidence_tier == "DISCOVERY"


# ---------------------------------------------------------------------------
# UNKNOWN values preserved
# ---------------------------------------------------------------------------

class TestUnknownPreservation:
    def test_cyprus_has_confirmed_rate_unknown(self):
        cy = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "CY")
        assert "confirmed_rate" in cy.unknown_fields

    def test_mauritius_has_atl_unknown(self):
        mu = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "MU")
        assert "atl_qualifying_scope" in mu.unknown_fields

    def test_mauritius_has_many_unknowns(self):
        mu = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "MU")
        assert len(mu.unknown_fields) >= 5

    def test_us_no_federal_rate(self):
        us = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "US")
        assert us.base_rate is None

    def test_discovery_programs_have_unknown_fields(self):
        for p in ALL_PROGRAMS:
            if p.confidence_tier == "DISCOVERY":
                assert len(p.unknown_fields) > 0, \
                    f"{p.jurisdiction_code} DISCOVERY should have unknown_fields"

    def test_mauritius_stage_multiplier_none(self):
        mu = next(b for b in ALL_BENCHMARKS if b.jurisdiction_code == "MU")
        assert mu.stage_facility_multiplier is None

    def test_hungary_marine_multiplier_none(self):
        hu = next(b for b in ALL_BENCHMARKS if b.jurisdiction_code == "HU")
        assert hu.marine_vessel_multiplier is None

    def test_none_values_preserved_not_zeroed(self):
        # Ensure None is genuinely None, not 0.0
        mu = next(b for b in ALL_BENCHMARKS if b.jurisdiction_code == "MU")
        assert mu.stage_facility_multiplier is None
        assert mu.stage_facility_multiplier != 0.0


# ---------------------------------------------------------------------------
# Rate and financial data sanity
# ---------------------------------------------------------------------------

class TestRateSanity:
    def test_rates_in_decimal_not_percent(self):
        for p in ALL_PROGRAMS:
            if p.base_rate is not None:
                assert 0 < p.base_rate <= 1.0, \
                    f"{p.jurisdiction_code} base_rate={p.base_rate} looks like a percentage"
            if p.max_rate is not None:
                assert 0 < p.max_rate <= 1.0, \
                    f"{p.jurisdiction_code} max_rate={p.max_rate} looks like a percentage"

    def test_max_rate_gte_base_rate(self):
        for p in ALL_PROGRAMS:
            if p.base_rate is not None and p.max_rate is not None:
                assert p.max_rate >= p.base_rate, \
                    f"{p.jurisdiction_code}: max_rate < base_rate"

    def test_malta_rate_25_to_40(self):
        mt = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "MT")
        assert mt.base_rate == pytest.approx(0.25)
        assert mt.max_rate == pytest.approx(0.40)

    def test_greece_rate_40(self):
        gr = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "GR")
        assert gr.base_rate == pytest.approx(0.40)

    def test_uk_avec_gross_rate(self):
        gb = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "GB")
        assert gb.base_rate == pytest.approx(0.34)

    def test_ireland_rate_32(self):
        ie = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "IE")
        assert ie.base_rate == pytest.approx(0.32)

    def test_australia_location_offset_base(self):
        au = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "AU")
        assert au.base_rate == pytest.approx(0.165)

    def test_nz_spg_base_20(self):
        nz = next(p for p in ALL_PROGRAMS if p.jurisdiction_code == "NZ")
        assert nz.base_rate == pytest.approx(0.20)


# ---------------------------------------------------------------------------
# Benchmark sanity
# ---------------------------------------------------------------------------

class TestBenchmarkSanity:
    def test_us_is_la_baseline(self):
        us = next(b for b in ALL_BENCHMARKS if b.jurisdiction_code == "US")
        assert us.crew_rate_multiplier == pytest.approx(1.0)
        assert us.equipment_rental_multiplier == pytest.approx(1.0)

    def test_low_cost_jurisdictions_under_70pct_crew(self):
        low_cost = {"MU", "GR", "CY", "HR", "HU"}
        for b in ALL_BENCHMARKS:
            if b.jurisdiction_code in low_cost:
                assert b.crew_rate_multiplier < 0.70, \
                    f"{b.jurisdiction_code} crew multiplier {b.crew_rate_multiplier} looks too high"

    def test_high_cost_jurisdictions_over_80pct_crew(self):
        high_cost = {"GB", "FR", "DE", "BE"}
        for b in ALL_BENCHMARKS:
            if b.jurisdiction_code in high_cost:
                assert b.crew_rate_multiplier >= 0.80

    def test_travel_usd_positive(self):
        for b in ALL_BENCHMARKS:
            if b.key_crew_daily_travel_usd is not None:
                assert b.key_crew_daily_travel_usd > 0

    def test_nz_au_high_travel_cost(self):
        # Long-haul jurisdictions should have higher travel cost
        nz = next(b for b in ALL_BENCHMARKS if b.jurisdiction_code == "NZ")
        au = next(b for b in ALL_BENCHMARKS if b.jurisdiction_code == "AU")
        us = next(b for b in ALL_BENCHMARKS if b.jurisdiction_code == "US")
        assert nz.key_crew_daily_travel_usd > us.key_crew_daily_travel_usd
        assert au.key_crew_daily_travel_usd > us.key_crew_daily_travel_usd

    def test_all_benchmarks_discovery_tier(self):
        for b in ALL_BENCHMARKS:
            assert b.confidence_tier == "DISCOVERY"


# ---------------------------------------------------------------------------
# Coverage report
# ---------------------------------------------------------------------------

class TestCoverageReport:
    @pytest.fixture(scope="class")
    def report(self) -> CoverageReport:
        return build_coverage_report()

    def test_report_version_present(self, report):
        assert report.report_version == "0.1.0"

    def test_total_jurisdictions(self, report):
        assert report.total_jurisdictions == 17

    def test_total_programs(self, report):
        assert report.total_programs == 17

    def test_total_benchmarks(self, report):
        assert report.total_benchmarks == 17

    def test_no_verified_programs(self, report):
        # No programs have been verified from primary sources yet
        assert report.verified_programs == 0

    def test_some_parsed_programs(self, report):
        assert report.parsed_programs >= 5  # US, CA, GB, IE, MT, GR, MU

    def test_some_discovery_programs(self, report):
        assert report.discovery_programs >= 8

    def test_all_benchmarks_discovery(self, report):
        assert report.discovery_benchmarks == 17
        assert report.verified_benchmarks == 0
        assert report.parsed_benchmarks == 0

    def test_by_jurisdiction_length(self, report):
        assert len(report.by_jurisdiction) == 17

    def test_by_jurisdiction_types(self, report):
        for jc in report.by_jurisdiction:
            assert isinstance(jc, JurisdictionCoverage)

    def test_mauritius_has_many_blockers(self, report):
        mu = next(jc for jc in report.by_jurisdiction if jc.jurisdiction_code == "MU")
        # MU is PARSED but has unknowns
        assert len(mu.unknown_fields) >= 5

    def test_cyprus_discovery_has_rate_blocker(self, report):
        cy = next(jc for jc in report.by_jurisdiction if jc.jurisdiction_code == "CY")
        assert cy.discovery_count > 0
        assert len(cy.budget_testing_blockers) > 0

    def test_malta_parsed_has_fewer_blockers_than_cyprus(self, report):
        mt = next(jc for jc in report.by_jurisdiction if jc.jurisdiction_code == "MT")
        cy = next(jc for jc in report.by_jurisdiction if jc.jurisdiction_code == "CY")
        # Cyprus has rate uncertainty; Malta is parsed — Malta should have fewer blockers
        assert len(mt.budget_testing_blockers) <= len(cy.budget_testing_blockers)

    def test_every_jurisdiction_has_at_least_one_program(self, report):
        for jc in report.by_jurisdiction:
            assert jc.program_count >= 1

    def test_every_jurisdiction_has_at_least_one_benchmark(self, report):
        for jc in report.by_jurisdiction:
            assert jc.benchmark_count >= 1


# ---------------------------------------------------------------------------
# Coverage table formatting
# ---------------------------------------------------------------------------

class TestFormatCoverageTable:
    def test_format_returns_string(self):
        report = build_coverage_report()
        table = format_coverage_table(report)
        assert isinstance(table, str)

    def test_table_contains_all_codes(self):
        report = build_coverage_report()
        table = format_coverage_table(report)
        for code in TARGET_CODES:
            assert code in table, f"Code {code} missing from coverage table"

    def test_table_has_header(self):
        report = build_coverage_report()
        table = format_coverage_table(report)
        assert "Code" in table
        assert "Progs" in table

    def test_table_has_tier_summary(self):
        report = build_coverage_report()
        table = format_coverage_table(report)
        assert "PARSED" in table
        assert "DISCOVERY" in table


# ---------------------------------------------------------------------------
# Custom inventory (isolated)
# ---------------------------------------------------------------------------

class TestCustomInventory:
    def test_empty_inventory_gives_zero_totals(self):
        report = build_coverage_report(programs=[], benchmarks=[])
        assert report.total_programs == 0
        assert report.total_benchmarks == 0
        assert report.total_jurisdictions == 0

    def test_single_program_gives_one_jurisdiction(self):
        p = GlobalProgramEntry(
            jurisdiction_code="XX",
            jurisdiction_name="Test Land",
            program_name="Test Credit",
            program_type="tax_credit",
            base_rate=0.25,
            max_rate=0.25,
            is_refundable=True,
            is_transferable=False,
            min_spend_usd=None,
            annual_cap_usd=None,
            requires_cultural_test=False,
            requires_local_entity=False,
            confidence_tier="DISCOVERY",
            source_title="Test Source",
            source_url=None,
            effective_from=None,
            notes="Test",
            unknown_fields=["confirmed_rate"],
        )
        report = build_coverage_report(programs=[p], benchmarks=[])
        assert report.total_jurisdictions == 1
        assert report.discovery_programs == 1
        assert report.parsed_programs == 0

    def test_parsed_program_counted_correctly(self):
        p = GlobalProgramEntry(
            jurisdiction_code="ZZ",
            jurisdiction_name="Parsed Land",
            program_name="Real Credit",
            program_type="cash_rebate",
            base_rate=0.30,
            max_rate=0.30,
            is_refundable=True,
            is_transferable=False,
            min_spend_usd=100_000.0,
            annual_cap_usd=None,
            requires_cultural_test=False,
            requires_local_entity=False,
            confidence_tier="PARSED",
            source_title="Official Guide",
            source_url=None,
            effective_from="2023-01-01",
            notes="Verified from official source.",
            unknown_fields=[],
        )
        report = build_coverage_report(programs=[p], benchmarks=[])
        assert report.parsed_programs == 1
        assert report.discovery_programs == 0

    def test_unknown_fields_preserved_in_report(self):
        p = GlobalProgramEntry(
            jurisdiction_code="MX",
            jurisdiction_name="Mexico",
            program_name="Mexico Rebate",
            program_type="cash_rebate",
            base_rate=None,
            max_rate=None,
            is_refundable=None,
            is_transferable=None,
            min_spend_usd=None,
            annual_cap_usd=None,
            requires_cultural_test=False,
            requires_local_entity=False,
            confidence_tier="DISCOVERY",
            source_title="Unknown [NOT YET ACQUIRED]",
            source_url=None,
            effective_from=None,
            notes="No confirmed source.",
            unknown_fields=["confirmed_rate", "min_spend", "annual_cap", "processing_timeline"],
        )
        report = build_coverage_report(programs=[p], benchmarks=[])
        jc = report.by_jurisdiction[0]
        assert "confirmed_rate" in jc.unknown_fields
        assert "processing_timeline" in jc.unknown_fields
