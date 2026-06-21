"""
test_extended_inventory.py

Tests for Phase A–E:
  Phase A — Extended global inventory (43 new jurisdictions)
  Phase C/D — ORM model structural integrity
  Phase E — Coverage management (gap analysis, promotable detection)
"""
from __future__ import annotations

import pytest

from app.data.global_inventory import ALL_BENCHMARKS, ALL_PROGRAMS
from app.data.global_inventory_extended import EXTENDED_BENCHMARKS, EXTENDED_PROGRAMS
from app.calculators.coverage_report import (
    build_coverage_report,
    build_gap_analysis,
    get_promotable_programs,
    GapAnalysis,
)


# ---------------------------------------------------------------------------
# Phase A — Extended inventory structure
# ---------------------------------------------------------------------------

class TestExtendedInventoryStructure:
    def test_extended_programs_count(self):
        assert len(EXTENDED_PROGRAMS) == 43

    def test_extended_benchmarks_count(self):
        assert len(EXTENDED_BENCHMARKS) == 43

    def test_all_programs_total(self):
        assert len(ALL_PROGRAMS) == 60

    def test_all_benchmarks_total(self):
        assert len(ALL_BENCHMARKS) == 60

    def test_no_duplicate_jurisdiction_codes(self):
        codes = [p.jurisdiction_code for p in ALL_PROGRAMS]
        assert len(codes) == len(set(codes)), "Duplicate jurisdiction codes in ALL_PROGRAMS"

    def test_no_duplicate_benchmark_codes(self):
        codes = [b.jurisdiction_code for b in ALL_BENCHMARKS]
        assert len(codes) == len(set(codes)), "Duplicate jurisdiction codes in ALL_BENCHMARKS"

    def test_all_extended_programs_are_discovery(self):
        for p in EXTENDED_PROGRAMS:
            assert p.confidence_tier == "DISCOVERY", (
                f"{p.jurisdiction_code} should be DISCOVERY, got {p.confidence_tier}"
            )

    def test_all_extended_benchmarks_are_discovery(self):
        for b in EXTENDED_BENCHMARKS:
            assert b.confidence_tier == "DISCOVERY"

    def test_every_extended_program_has_unknown_fields(self):
        for p in EXTENDED_PROGRAMS:
            assert len(p.unknown_fields) > 0, (
                f"{p.jurisdiction_code} DISCOVERY should have unknown_fields listed"
            )

    def test_every_extended_program_has_source_url(self):
        for p in EXTENDED_PROGRAMS:
            assert p.source_url is not None, (
                f"{p.jurisdiction_code} should have a source_url in extended inventory"
            )

    def test_every_extended_program_has_source_title(self):
        for p in EXTENDED_PROGRAMS:
            assert p.source_title, f"{p.jurisdiction_code} missing source_title"

    def test_every_extended_program_has_notes(self):
        for p in EXTENDED_PROGRAMS:
            assert p.notes, f"{p.jurisdiction_code} missing notes"


class TestExtendedUSStates:
    def _get(self, code: str):
        return next(p for p in EXTENDED_PROGRAMS if p.jurisdiction_code == code)

    def test_us_or_program(self):
        p = self._get("US-OR")
        assert p.program_name == "Oregon Production Investment Fund (OPIF)"
        assert p.base_rate == 0.20
        assert p.is_refundable is True

    def test_us_il_rate(self):
        p = self._get("US-IL")
        assert p.base_rate == 0.30
        assert p.max_rate == 0.30
        assert p.is_transferable is True

    def test_us_ok_high_rate(self):
        p = self._get("US-OK")
        assert p.base_rate == 0.35
        assert p.max_rate == 0.37

    def test_us_ky_refundable(self):
        p = self._get("US-KY")
        assert p.base_rate == 0.30
        assert p.is_refundable is True

    def test_us_tn_unknown_base_rate(self):
        p = self._get("US-TN")
        assert p.base_rate is None, "TN rate is unconfirmed — must remain None"
        assert "base_rate" in p.unknown_fields

    def test_us_tx_low_base_rate(self):
        p = self._get("US-TX")
        assert p.base_rate == 0.05
        assert p.max_rate == 0.225

    def test_us_va_limited_cap(self):
        p = self._get("US-VA")
        assert p.annual_cap_usd == 6_500_000

    def test_us_co_small_cap(self):
        p = self._get("US-CO")
        assert p.annual_cap_usd == 750_000


class TestExtendedCanadaProvinces:
    def _get(self, code: str):
        return next(p for p in EXTENDED_PROGRAMS if p.jurisdiction_code == code)

    def test_ca_mb_high_rate(self):
        p = self._get("CA-MB")
        assert p.base_rate == 0.45
        assert p.max_rate == 0.65

    def test_ca_ns_requires_cultural_test(self):
        p = self._get("CA-NS")
        assert p.requires_cultural_test is True

    def test_ca_ab_refundable(self):
        p = self._get("CA-AB")
        assert p.is_refundable is True
        assert p.base_rate == 0.22


class TestExtendedEurope:
    def _get(self, code: str):
        return next(p for p in EXTENDED_PROGRAMS if p.jurisdiction_code == code)

    def test_nl_requires_cultural_test(self):
        p = self._get("NL")
        assert p.requires_cultural_test is True
        assert p.requires_local_entity is True
        assert p.base_rate == 0.30

    def test_iceland_25pct(self):
        p = self._get("IS")
        assert p.base_rate == 0.25
        assert p.max_rate == 0.25

    def test_romania_high_rate(self):
        p = self._get("RO")
        assert p.base_rate == 0.35
        assert p.max_rate == 0.45

    def test_cz_no_cultural_test(self):
        p = self._get("CZ")
        assert p.requires_cultural_test is False

    def test_gb_sct_requires_cultural_test(self):
        p = self._get("GB-SCT")
        assert p.requires_cultural_test is True

    def test_gb_wls_requires_cultural_test(self):
        p = self._get("GB-WLS")
        assert p.requires_cultural_test is True


class TestExtendedAsiaPacific:
    def _get(self, code: str):
        return next(p for p in EXTENDED_PROGRAMS if p.jurisdiction_code == code)

    def test_sg_unknown_base_rate(self):
        p = self._get("SG")
        assert p.base_rate is None, "Singapore rate is discretionary — must be None"

    def test_au_vic_combined_rate(self):
        p = self._get("AU-VIC")
        assert p.max_rate == 0.335

    def test_au_nsw_max_rate(self):
        p = self._get("AU-NSW")
        assert p.max_rate == 0.35


class TestExtendedLatAm:
    def _get(self, code: str):
        return next(p for p in EXTENDED_PROGRAMS if p.jurisdiction_code == code)

    def test_colombia_rate(self):
        p = self._get("CO")
        assert p.base_rate == 0.40

    def test_argentina_unknown_rate(self):
        p = self._get("AR")
        assert p.base_rate is None
        assert p.requires_local_entity is True

    def test_brazil_requires_local_entity(self):
        p = self._get("BR")
        assert p.requires_local_entity is True


class TestExtendedMiddleEastAfrica:
    def _get(self, code: str):
        return next(p for p in EXTENDED_PROGRAMS if p.jurisdiction_code == code)

    def test_uae_dpip_rate(self):
        p = self._get("AE")
        assert p.base_rate == 0.30
        assert p.is_refundable is True

    def test_saudi_unknown_base_rate(self):
        p = self._get("SA")
        assert p.base_rate is None, "Saudi rate is still evolving — must be None"

    def test_jordan_rate_range(self):
        p = self._get("JO")
        assert p.base_rate == 0.10
        assert p.max_rate == 0.25

    def test_morocco_requires_local_entity(self):
        p = self._get("MA")
        assert p.requires_local_entity is True

    def test_south_africa_cape_town_hub(self):
        p = self._get("ZA")
        assert "Cape Town" in p.notes


class TestExtendedBenchmarks:
    def _get(self, code: str):
        return next(b for b in EXTENDED_BENCHMARKS if b.jurisdiction_code == code)

    def test_iceland_high_crew_cost(self):
        bm = self._get("IS")
        assert bm.crew_rate_multiplier >= 0.90, "Iceland crew is expensive relative to LA"

    def test_romania_low_crew_cost(self):
        bm = self._get("RO")
        assert bm.crew_rate_multiplier <= 0.40

    def test_argentina_very_low_crew_cost(self):
        bm = self._get("AR")
        assert bm.crew_rate_multiplier <= 0.30

    def test_morocco_low_crew_cost(self):
        bm = self._get("MA")
        assert bm.crew_rate_multiplier <= 0.35

    def test_uae_high_travel_cost(self):
        bm = self._get("AE")
        assert bm.key_crew_daily_travel_usd >= 400.0

    def test_us_tx_marine_vessel_none(self):
        bm = self._get("US-TX")
        assert bm.marine_vessel_multiplier is None

    def test_nz_au_high_travel_cost(self):
        nz = next(b for b in ALL_BENCHMARKS if b.jurisdiction_code == "NZ")
        au_qld = self._get("AU-QLD")
        assert nz.key_crew_daily_travel_usd >= 490.0
        assert au_qld.key_crew_daily_travel_usd >= 450.0

    def test_every_extended_benchmark_has_data_source(self):
        for b in EXTENDED_BENCHMARKS:
            assert b.data_source, f"{b.jurisdiction_code} missing data_source"

    def test_every_extended_benchmark_has_notes(self):
        for b in EXTENDED_BENCHMARKS:
            assert b.notes, f"{b.jurisdiction_code} missing notes"


# ---------------------------------------------------------------------------
# Phase C/D — ORM model structural integrity
# ---------------------------------------------------------------------------

class TestProgramAdminDetailsORM:
    def test_model_importable(self):
        from app.models.program_intelligence import ProgramAdminDetails
        assert ProgramAdminDetails.__tablename__ == "program_admin_details"

    def test_model_has_required_columns(self):
        from app.models.program_intelligence import ProgramAdminDetails
        cols = {c.name for c in ProgramAdminDetails.__table__.columns}
        required = {
            "id", "program_id", "payment_timing_weeks", "audit_required",
            "is_assignable", "processing_timeline_weeks", "confidence_tier",
        }
        assert required.issubset(cols), f"Missing columns: {required - cols}"

    def test_program_id_is_unique(self):
        from app.models.program_intelligence import ProgramAdminDetails
        program_id_col = ProgramAdminDetails.__table__.c["program_id"]
        assert program_id_col.unique is True


class TestProgramSpendTreatmentORM:
    def test_model_importable(self):
        from app.models.program_intelligence import ProgramSpendTreatment
        assert ProgramSpendTreatment.__tablename__ == "program_spend_treatments"

    def test_model_has_required_columns(self):
        from app.models.program_intelligence import ProgramSpendTreatment
        cols = {c.name for c in ProgramSpendTreatment.__table__.columns}
        required = {
            "id", "program_id", "labor_type", "qualifies",
            "cap_pct", "cap_amount_local", "confidence_tier",
        }
        assert required.issubset(cols), f"Missing columns: {required - cols}"

    def test_unique_constraint_exists(self):
        from app.models.program_intelligence import ProgramSpendTreatment
        constraint_names = {
            c.name for c in ProgramSpendTreatment.__table__.constraints
        }
        assert "uq_spend_treatment_program_labor" in constraint_names


class TestHistoricalProductionBenchmarkORM:
    def test_model_importable(self):
        from app.models.program_intelligence import HistoricalProductionBenchmark
        assert HistoricalProductionBenchmark.__tablename__ == "historical_production_benchmarks"

    def test_model_has_required_columns(self):
        from app.models.program_intelligence import HistoricalProductionBenchmark
        cols = {c.name for c in HistoricalProductionBenchmark.__table__.columns}
        required = {
            "id", "title", "production_type", "principal_jurisdiction_code",
            "total_budget_usd", "qualifying_spend_usd", "incentive_received_usd",
            "effective_rate_achieved", "la_equivalent_budget_usd",
            "data_source", "is_anonymised", "confidence_tier",
        }
        assert required.issubset(cols), f"Missing: {required - cols}"


class TestBenchmarkSpendItemORM:
    def test_model_importable(self):
        from app.models.program_intelligence import BenchmarkSpendItem
        assert BenchmarkSpendItem.__tablename__ == "benchmark_spend_items"

    def test_has_derived_multiplier_column(self):
        from app.models.program_intelligence import BenchmarkSpendItem
        cols = {c.name for c in BenchmarkSpendItem.__table__.columns}
        assert "derived_multiplier" in cols
        assert "la_equivalent_usd" in cols


class TestBenchmarkIngestionLogORM:
    def test_model_importable(self):
        from app.models.program_intelligence import BenchmarkIngestionLog
        assert BenchmarkIngestionLog.__tablename__ == "benchmark_ingestion_logs"

    def test_has_status_column(self):
        from app.models.program_intelligence import BenchmarkIngestionLog
        cols = {c.name for c in BenchmarkIngestionLog.__table__.columns}
        assert "status" in cols
        assert "ingested_at" in cols
        assert "record_count" in cols


# ---------------------------------------------------------------------------
# Phase E — Coverage management
# ---------------------------------------------------------------------------

class TestGetPromotablePrograms:
    def test_returns_list(self):
        result = get_promotable_programs()
        assert isinstance(result, list)

    def test_no_parsed_or_verified_in_result(self):
        result = get_promotable_programs()
        for p in result:
            assert p.confidence_tier == "DISCOVERY"

    def test_promotable_programs_have_base_rate(self):
        result = get_promotable_programs()
        for p in result:
            assert p.base_rate is not None, (
                f"{p.jurisdiction_code} promotable but missing base_rate"
            )

    def test_promotable_programs_have_source_url(self):
        result = get_promotable_programs()
        for p in result:
            assert p.source_url is not None, (
                f"{p.jurisdiction_code} promotable but missing source_url"
            )

    def test_promotable_programs_have_refundability(self):
        result = get_promotable_programs()
        for p in result:
            assert p.is_refundable is not None, (
                f"{p.jurisdiction_code} promotable but refundability unknown"
            )

    def test_custom_programs_promotable(self):
        from app.data.global_inventory import GlobalProgramEntry
        programs = [
            GlobalProgramEntry(
                jurisdiction_code="XX",
                jurisdiction_name="Test",
                program_name="Test Rebate",
                program_type="cash_rebate",
                base_rate=0.25,
                max_rate=0.25,
                is_refundable=True,
                is_transferable=False,
                min_spend_usd=None,
                annual_cap_usd=None,
                requires_cultural_test=False,
                requires_local_entity=False,
                confidence_tier="DISCOVERY",
                source_title="Test source",
                source_url="https://example.com",
                effective_from="2020-01-01",
                notes="Test notes",
                unknown_fields=["processing_timeline"],
            ),
        ]
        result = get_promotable_programs(programs)
        assert len(result) == 1
        assert result[0].jurisdiction_code == "XX"

    def test_non_promotable_excluded(self):
        from app.data.global_inventory import GlobalProgramEntry
        programs = [
            GlobalProgramEntry(
                jurisdiction_code="YY",
                jurisdiction_name="Test",
                program_name="Unknown Rebate",
                program_type="cash_rebate",
                base_rate=None,          # missing — not promotable
                max_rate=0.25,
                is_refundable=None,
                is_transferable=False,
                min_spend_usd=None,
                annual_cap_usd=None,
                requires_cultural_test=False,
                requires_local_entity=False,
                confidence_tier="DISCOVERY",
                source_title="Unknown",
                source_url=None,         # missing — not promotable
                effective_from=None,
                notes="Unknown",
                unknown_fields=["base_rate", "is_refundable"],
            ),
        ]
        result = get_promotable_programs(programs)
        assert len(result) == 0


class TestBuildGapAnalysis:
    def test_returns_gap_analysis(self):
        result = build_gap_analysis()
        assert isinstance(result, GapAnalysis)

    def test_no_verified_programs(self):
        result = build_gap_analysis()
        assert result.total_verified_programs == 0

    def test_some_parsed_programs(self):
        result = build_gap_analysis()
        assert result.total_parsed_programs >= 5

    def test_many_discovery_programs(self):
        result = build_gap_analysis()
        assert result.total_discovery_programs >= 43

    def test_programs_missing_source_url_is_list(self):
        result = build_gap_analysis()
        assert isinstance(result.programs_missing_source_url, list)

    def test_programs_missing_base_rate_includes_unknowns(self):
        result = build_gap_analysis()
        # US-TN, SG, SA, AR, BR, UY all have None base_rate
        assert "US-TN" in result.programs_missing_base_rate
        assert "SG" in result.programs_missing_base_rate

    def test_no_jurisdictions_missing_benchmark(self):
        result = build_gap_analysis()
        # Every program jurisdiction has a corresponding benchmark
        assert len(result.jurisdictions_missing_benchmark) == 0

    def test_gap_analysis_with_custom_data(self):
        from app.data.global_inventory import GlobalProgramEntry, CostBenchmarkEntry
        programs = [
            GlobalProgramEntry(
                jurisdiction_code="ZZ",
                jurisdiction_name="Test Country",
                program_name="Test Program",
                program_type="cash_rebate",
                base_rate=None,
                max_rate=0.30,
                is_refundable=None,
                is_transferable=False,
                min_spend_usd=None,
                annual_cap_usd=None,
                requires_cultural_test=False,
                requires_local_entity=False,
                confidence_tier="DISCOVERY",
                source_title="TBD",
                source_url=None,
                effective_from=None,
                notes="Placeholder",
                unknown_fields=["base_rate"],
            ),
        ]
        result = build_gap_analysis(programs=programs, benchmarks=[])
        assert "ZZ" in result.programs_missing_source_url
        assert "ZZ" in result.programs_missing_base_rate
        assert "ZZ" in result.jurisdictions_missing_benchmark
        assert result.total_discovery_programs == 1


class TestCoverageReportExpanded:
    def test_total_jurisdictions_60(self):
        report = build_coverage_report()
        assert report.total_jurisdictions == 60

    def test_total_programs_60(self):
        report = build_coverage_report()
        assert report.total_programs == 60

    def test_no_verified_programs(self):
        report = build_coverage_report()
        assert report.verified_programs == 0

    def test_all_extended_jurisdictions_present(self):
        report = build_coverage_report()
        codes = {jc.jurisdiction_code for jc in report.by_jurisdiction}
        # A sample of extended codes
        for code in ["US-OR", "CA-AB", "NL", "SG", "CO", "AE", "MA", "ZA", "IS", "RO"]:
            assert code in codes, f"{code} missing from coverage report"

    def test_original_jurisdictions_present(self):
        report = build_coverage_report()
        codes = {jc.jurisdiction_code for jc in report.by_jurisdiction}
        for code in ["US", "CA", "GB", "IE", "MT", "GR", "CY", "MU", "AU", "NZ"]:
            assert code in codes

    def test_all_benchmarks_discovery(self):
        report = build_coverage_report()
        assert report.discovery_benchmarks == 60

    def test_report_version_updated(self):
        report = build_coverage_report()
        assert report.report_version == "0.3.0"
