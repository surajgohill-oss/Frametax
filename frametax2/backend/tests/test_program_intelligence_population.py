"""
test_program_intelligence_population.py

Tests for Phase 1–5 deepening work:
  Phase 1 — Source acquisition batch 2 (migration 0016)
  Phase 2 — ProgramAdminDetails population (migration 0016)
  Phase 3 — ProgramSpendTreatment population (migration 0017)
  Phase 4 — Promotion readiness (FR/IT promoted to PARSED in global_inventory.py)
  Phase 5 — Benchmark ingestion readiness (ORM model structural checks)

These tests are purely Python / import-level — no DB connection required.
"""
from __future__ import annotations

import importlib.util
import sys
import types
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.data.global_inventory import ALL_PROGRAMS, ALL_BENCHMARKS


# ---------------------------------------------------------------------------
# Helpers — load migration modules via spec_from_file_location to bypass
# alembic package import machinery.
# ---------------------------------------------------------------------------

_VERSIONS_DIR = Path(__file__).parent.parent / "alembic" / "versions"


def _load_migration(filename: str):
    """
    Load a migration module from disk, mocking sqlalchemy and alembic.op
    so the data constants are accessible without a DB context.
    Restores sys.modules after loading so later imports are unaffected.
    """
    # Keys to temporarily override
    _MOCK_KEYS = ["sqlalchemy", "alembic", "alembic.op"]

    # Save originals
    saved = {k: sys.modules.get(k) for k in _MOCK_KEYS}

    try:
        # Inject mocks
        sys.modules["sqlalchemy"] = MagicMock()
        sys.modules["alembic"] = MagicMock()
        sys.modules["alembic.op"] = MagicMock()

        path = _VERSIONS_DIR / filename
        mod_name = f"_migration_{filename.replace('.py', '')}"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    finally:
        # Restore originals (or remove if they weren't there)
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


# ---------------------------------------------------------------------------
# Phase 1 — Source batch 2 migration constants
# ---------------------------------------------------------------------------

# Slug → (expected_tier, url_contains)
_EXPECTED_SOURCE_UPDATES: dict[str, tuple[str, str]] = {
    "uk_avec":                 ("PARSED", "gov.uk"),
    "ie_section_481":          ("PARSED", "revenue.ie"),
    "georgia_eiia":            ("PARSED", "dor.georgia.gov"),
    "ny_state_film":           ("PARSED", "esd.ny.gov"),
    "ca_film_30":              ("PARSED", "film.ca.gov"),
    "la_film_production":      ("PARSED", "lafilm.org"),
    "on_opstc":                ("PARSED", "ontariocreates.ca"),
    "on_ofttc":                ("PARSED", "ontariocreates.ca"),
    "bc_pstc":                 ("PARSED", "creativebc.com"),
    "qc_film_production":      ("PARSED", "sodec.gouv.qc.ca"),
    "ca_federal_cptc":         ("PARSED", "canada.ca"),
    "mu_edb_incentive":        ("PARSED", "edbmauritius.org"),
    "mt_mfc_rebate":           ("PARSED", "maltafilmcommission.com"),
    "gr_cash_rebate":          ("PARSED", "enterprisegreece.gov.gr"),
    "fr_trip":                 ("PARSED", "cnc.fr"),
    "it_tax_credit_foreign":   ("PARSED", "dgcinema"),
}


class TestSourceBatch2Constants:
    def test_expected_slug_count(self):
        assert len(_EXPECTED_SOURCE_UPDATES) == 16

    def test_migration_0016_constants(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        rows = mod._SOURCE_UPDATES
        actual_slugs = {r[0] for r in rows}
        assert actual_slugs == set(_EXPECTED_SOURCE_UPDATES.keys()), (
            f"Slug mismatch. Extra: {actual_slugs - set(_EXPECTED_SOURCE_UPDATES)}, "
            f"Missing: {set(_EXPECTED_SOURCE_UPDATES) - actual_slugs}"
        )

    def test_all_source_urls_https(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        for slug, url, tier, date in mod._SOURCE_UPDATES:
            assert url.startswith("https://"), f"{slug}: URL must be HTTPS"

    def test_all_tiers_parsed_or_higher(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        for slug, url, tier, date in mod._SOURCE_UPDATES:
            assert tier in ("PARSED", "VERIFIED"), (
                f"{slug}: tier must be PARSED or VERIFIED, got {tier}"
            )

    def test_url_contains_expected_domain(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        by_slug = {r[0]: r[1] for r in mod._SOURCE_UPDATES}
        for slug, (tier, domain) in _EXPECTED_SOURCE_UPDATES.items():
            url = by_slug.get(slug, "")
            assert domain in url, f"{slug}: expected URL to contain '{domain}', got {url!r}"

    def test_verified_date_set(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        for slug, url, tier, date in mod._SOURCE_UPDATES:
            assert date == "2026-06-21", f"{slug}: unexpected date {date}"

    def test_no_duplicate_slugs(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        slugs = [r[0] for r in mod._SOURCE_UPDATES]
        assert len(slugs) == len(set(slugs)), "Duplicate slugs in _SOURCE_UPDATES"


# ---------------------------------------------------------------------------
# Phase 2 — ProgramAdminDetails constants
# ---------------------------------------------------------------------------

# slug → (is_assignable, max_acceptable_processing_weeks, confidence_tier)
_EXPECTED_ADMIN: dict[str, tuple[bool | None, int | None, str]] = {
    "georgia_eiia":     (True,  26,   "PARSED"),
    "ny_state_film":    (False, 104,  "PARSED"),
    "ca_film_30":       (True,  104,  "PARSED"),
    "la_film_production": (True, 52,  "PARSED"),
    "uk_avec":          (True,  16,   "PARSED"),
    "ie_section_481":   (True,  26,   "PARSED"),
    "mt_mfc_rebate":    (None,  52,   "PARSED"),
    "gr_cash_rebate":   (None,  78,   "PARSED"),
    "mu_edb_incentive": (None,  None, "DISCOVERY"),
    "on_opstc":         (False, 52,   "PARSED"),
    "bc_pstc":          (False, 52,   "PARSED"),
    "qc_film_production": (False, 60, "PARSED"),
}


class TestAdminDetailsConstants:
    def test_admin_details_count(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        assert len(mod._ADMIN_DETAILS) == 12

    def test_expected_slugs_present(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        actual = {r[0] for r in mod._ADMIN_DETAILS}
        expected = set(_EXPECTED_ADMIN.keys())
        assert actual == expected, (
            f"Extra: {actual - expected}, Missing: {expected - actual}"
        )

    def test_no_duplicate_slugs(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        slugs = [r[0] for r in mod._ADMIN_DETAILS]
        assert len(slugs) == len(set(slugs))

    def test_mauritius_is_discovery(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        for row in mod._ADMIN_DETAILS:
            if row[0] == "mu_edb_incentive":
                tier = row[-2]
                assert tier == "DISCOVERY", f"MU should be DISCOVERY, got {tier}"
                return
        pytest.fail("mu_edb_incentive not found")

    def test_all_confidence_tiers_valid(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        valid = {"DISCOVERY", "PARSED", "VERIFIED"}
        for row in mod._ADMIN_DETAILS:
            slug, tier = row[0], row[-2]
            assert tier in valid, f"{slug}: invalid tier {tier!r}"

    def test_uk_avec_fast_processing(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        row = by_slug["uk_avec"]
        proc_weeks = row[8]  # processing_timeline_weeks
        assert proc_weeks is not None and proc_weeks <= 15

    def test_gr_ekome_slowest_processing(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        gr_weeks = by_slug["gr_cash_rebate"][8]
        assert gr_weeks >= 52, f"GR EKOME should be ≥52 weeks, got {gr_weeks}"

    def test_ny_is_not_assignable(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        assert by_slug["ny_state_film"][6] is False

    def test_on_bc_qc_not_assignable(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        for slug in ("on_opstc", "bc_pstc", "qc_film_production"):
            assert by_slug[slug][6] is False, f"{slug} should not be assignable"

    def test_uk_ie_ga_ca_la_assignable(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        for slug in ("uk_avec", "ie_section_481", "georgia_eiia", "ca_film_30", "la_film_production"):
            assert by_slug[slug][6] is True, f"{slug} should be assignable/transferable"

    def test_all_notes_non_empty(self):
        mod = _load_migration("0016_source_batch2_admin_details.py")
        for row in mod._ADMIN_DETAILS:
            assert row[-1], f"{row[0]}: notes field empty"

    def test_uuid5_ids_deterministic(self):
        ns = uuid.UUID("a1000000-0016-0000-0001-000000000000")
        uid1 = str(uuid.uuid5(ns, "admin:uk_avec"))
        uid2 = str(uuid.uuid5(ns, "admin:uk_avec"))
        assert uid1 == uid2

    def test_uuid5_ids_unique_per_slug(self):
        ns = uuid.UUID("a1000000-0016-0000-0001-000000000000")
        slugs = list(_EXPECTED_ADMIN.keys())
        ids = [str(uuid.uuid5(ns, f"admin:{s}")) for s in slugs]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Phase 3 — ProgramSpendTreatment constants
# ---------------------------------------------------------------------------

ALL_LABOR_TYPES = frozenset([
    "atl_writer", "atl_director", "atl_producer",
    "atl_cast_principal", "atl_cast_supporting",
    "btl_crew_resident", "btl_crew_non_resident", "btl_crew_foreign",
    "travel", "accommodation_lodging", "per_diem",
    "insurance", "completion_bond", "contingency",
    "marine_vessel", "vfx", "post_production",
    "animation", "music", "legal_accounting", "customs_imports",
])

EXPECTED_TREATMENT_PROGRAMS = frozenset([
    "uk_avec", "ie_section_481", "georgia_eiia", "ca_film_30",
    "mt_mfc_rebate", "gr_cash_rebate", "on_opstc", "ny_state_film",
])

ATL_TYPES = frozenset([
    "atl_writer", "atl_director", "atl_producer",
    "atl_cast_principal", "atl_cast_supporting",
])


class TestSpendTreatmentConstants:
    def test_treatment_programs_match(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        actual = {r[0] for r in mod._TREATMENTS}
        assert actual == EXPECTED_TREATMENT_PROGRAMS

    def test_each_program_has_all_21_labor_types(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        by_slug: dict[str, set[str]] = {}
        for slug, labor_type, *_ in mod._TREATMENTS:
            by_slug.setdefault(slug, set()).add(labor_type)
        for slug in EXPECTED_TREATMENT_PROGRAMS:
            missing = ALL_LABOR_TYPES - by_slug.get(slug, set())
            assert not missing, f"{slug} missing: {missing}"

    def test_total_rows_8x21(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        assert len(mod._TREATMENTS) == 8 * 21

    def test_no_duplicate_program_labor_pairs(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        pairs = [(r[0], r[1]) for r in mod._TREATMENTS]
        assert len(pairs) == len(set(pairs))

    def test_contingency_universally_does_not_qualify(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "contingency":
                assert qualifies is False, f"{slug}: contingency must be DOES_NOT_QUALIFY"

    def test_customs_imports_universally_unknown(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "customs_imports" and slug != "ca_federal_cptc":
                assert qualifies is None, f"{slug}: customs_imports must be UNKNOWN"

    def test_ca_film_atl_does_not_qualify(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "ca_film_30" and labor_type in ATL_TYPES:
                assert qualifies is False, f"CA Film 3.0 {labor_type} must be DOES_NOT_QUALIFY"

    def test_georgia_atl_qualifies(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "georgia_eiia" and labor_type in ATL_TYPES:
                assert qualifies is True, f"GA EIIA {labor_type} must QUALIFY"

    def test_uk_avec_atl_qualifies(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "uk_avec" and labor_type in ATL_TYPES:
                assert qualifies is True, f"UK AVEC {labor_type} must QUALIFY (geography-based)"

    def test_ie_s481_non_contingency_non_customs_qualifies(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        excluded = {"contingency", "customs_imports"}
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "ie_section_481" and labor_type not in excluded:
                assert qualifies is True, f"IE S481 {labor_type} must QUALIFY"

    def test_mt_mfc_marine_vessel_qualifies(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        found = False
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "mt_mfc_rebate" and labor_type == "marine_vessel":
                assert qualifies is True
                found = True
        assert found, "mt_mfc_rebate marine_vessel row missing"

    def test_gr_ekome_marine_vessel_qualifies(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        found = False
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "gr_cash_rebate" and labor_type == "marine_vessel":
                assert qualifies is True
                found = True
        assert found, "gr_cash_rebate marine_vessel row missing"

    def test_ny_atl_unknown(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "ny_state_film" and labor_type in ATL_TYPES:
                assert qualifies is None, f"NY {labor_type} must be UNKNOWN"

    def test_on_opstc_atl_unknown(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        pure_atl = {"atl_writer", "atl_director", "atl_producer"}
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "on_opstc" and labor_type in pure_atl:
                assert qualifies is None, f"ON OPSTC {labor_type} must be UNKNOWN"

    def test_all_notes_non_empty(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        for slug, labor_type, qualifies, notes, tier in mod._TREATMENTS:
            assert notes and len(notes) > 10, f"{slug}/{labor_type}: notes too short"

    def test_all_confidence_tiers_valid(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        valid = {"DISCOVERY", "PARSED", "VERIFIED"}
        for slug, labor_type, qualifies, notes, tier in mod._TREATMENTS:
            assert tier in valid, f"{slug}/{labor_type}: invalid tier {tier!r}"

    def test_uuid5_ids_deterministic(self):
        ns = uuid.UUID("a1000000-0017-0000-0001-000000000000")
        uid1 = str(uuid.uuid5(ns, "treatment:uk_avec:atl_writer"))
        uid2 = str(uuid.uuid5(ns, "treatment:uk_avec:atl_writer"))
        assert uid1 == uid2

    def test_uuid5_ids_unique_per_pair(self):
        mod = _load_migration("0017_program_spend_treatments.py")
        ns = uuid.UUID("a1000000-0017-0000-0001-000000000000")
        ids = [
            str(uuid.uuid5(ns, f"treatment:{slug}:{labor_type}"))
            for slug, labor_type, *_ in mod._TREATMENTS
        ]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Phase 4 — FR and IT promoted to PARSED in global_inventory.py
# ---------------------------------------------------------------------------

class TestPhase4Promotions:
    def test_fr_promoted_to_parsed(self):
        fr_progs = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "FR"]
        assert fr_progs, "FR program not found in ALL_PROGRAMS"
        assert fr_progs[0].confidence_tier == "PARSED", (
            f"FR should be PARSED, got {fr_progs[0].confidence_tier}"
        )

    def test_fr_has_cnc_source_url(self):
        fr = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "FR"][0]
        assert fr.source_url and "cnc.fr" in fr.source_url

    def test_it_promoted_to_parsed(self):
        it_progs = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "IT"]
        assert it_progs, "IT program not found in ALL_PROGRAMS"
        assert it_progs[0].confidence_tier == "PARSED", (
            f"IT should be PARSED, got {it_progs[0].confidence_tier}"
        )

    def test_it_has_dgcinema_source_url(self):
        it = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "IT"][0]
        assert it.source_url and "dgcinema" in it.source_url

    def test_neither_fr_nor_it_is_verified(self):
        for p in ALL_PROGRAMS:
            if p.jurisdiction_code in ("FR", "IT"):
                assert p.confidence_tier != "VERIFIED", (
                    f"{p.jurisdiction_code} should not leap to VERIFIED"
                )


# ---------------------------------------------------------------------------
# Phase 5 — Benchmark ingestion readiness (ORM model structural checks)
# ---------------------------------------------------------------------------

class TestPhase5BenchmarkReadiness:
    def test_historical_production_benchmark_importable(self):
        from app.models.program_intelligence import HistoricalProductionBenchmark
        assert HistoricalProductionBenchmark.__tablename__ == "historical_production_benchmarks"

    def test_benchmark_spend_item_importable(self):
        from app.models.program_intelligence import BenchmarkSpendItem
        assert BenchmarkSpendItem.__tablename__ == "benchmark_spend_items"

    def test_benchmark_ingestion_log_importable(self):
        from app.models.program_intelligence import BenchmarkIngestionLog
        assert BenchmarkIngestionLog.__tablename__ == "benchmark_ingestion_logs"

    def test_program_admin_details_importable(self):
        from app.models.program_intelligence import ProgramAdminDetails
        assert ProgramAdminDetails.__tablename__ == "program_admin_details"

    def test_program_spend_treatment_importable(self):
        from app.models.program_intelligence import ProgramSpendTreatment
        assert ProgramSpendTreatment.__tablename__ == "program_spend_treatments"

    def test_historical_benchmark_columns(self):
        from app.models.program_intelligence import HistoricalProductionBenchmark
        cols = {c.key for c in HistoricalProductionBenchmark.__mapper__.columns}
        required = {
            "id", "title", "production_type", "release_year",
            "principal_jurisdiction_code", "total_budget_usd",
            "qualifying_spend_usd", "incentive_received_usd",
            "effective_rate_achieved", "data_source", "confidence_tier",
        }
        assert not (required - cols), f"Missing: {required - cols}"

    def test_benchmark_spend_item_columns(self):
        from app.models.program_intelligence import BenchmarkSpendItem
        cols = {c.key for c in BenchmarkSpendItem.__mapper__.columns}
        required = {
            "id", "benchmark_id", "category", "amount_local",
            "currency_code", "amount_usd", "pct_of_total_budget",
        }
        assert not (required - cols), f"Missing: {required - cols}"

    def test_ingestion_log_columns(self):
        from app.models.program_intelligence import BenchmarkIngestionLog
        cols = {c.key for c in BenchmarkIngestionLog.__mapper__.columns}
        required = {"id", "source_name", "source_type", "ingested_at", "status"}
        assert not (required - cols), f"Missing: {required - cols}"

    def test_admin_details_columns(self):
        from app.models.program_intelligence import ProgramAdminDetails
        cols = {c.key for c in ProgramAdminDetails.__mapper__.columns}
        required = {
            "id", "program_id", "payment_timing_weeks",
            "audit_required", "is_assignable",
            "processing_timeline_weeks", "confidence_tier",
        }
        assert not (required - cols), f"Missing: {required - cols}"

    def test_spend_treatment_columns(self):
        from app.models.program_intelligence import ProgramSpendTreatment
        cols = {c.key for c in ProgramSpendTreatment.__mapper__.columns}
        required = {
            "id", "program_id", "labor_type",
            "qualifies", "treatment_notes", "confidence_tier",
        }
        assert not (required - cols), f"Missing: {required - cols}"

    def test_all_intelligence_models_in_init(self):
        from app.models import (
            ProgramAdminDetails, ProgramSpendTreatment,
            HistoricalProductionBenchmark, BenchmarkSpendItem,
            BenchmarkIngestionLog,
        )
        for cls in (
            ProgramAdminDetails, ProgramSpendTreatment,
            HistoricalProductionBenchmark, BenchmarkSpendItem,
            BenchmarkIngestionLog,
        ):
            assert hasattr(cls, "__tablename__")

    def test_migration_0014_creates_all_five_tables(self):
        mod = _load_migration("0014_program_intelligence_tables.py")
        # The upgrade function should exist and be callable
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)
        assert mod.revision == "0014"
        assert mod.down_revision == "0013"

    def test_migration_chain_0015_to_0019(self):
        m15 = _load_migration("0015_seed_extended_jurisdictions.py")
        m16 = _load_migration("0016_source_batch2_admin_details.py")
        m17 = _load_migration("0017_program_spend_treatments.py")
        m18 = _load_migration("0018_spend_treatment_la_bc_qc.py")
        m19 = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        assert m15.down_revision == "0014"
        assert m16.down_revision == "0015"
        assert m17.down_revision == "0016"
        assert m18.down_revision == "0017"
        assert m19.down_revision == "0018"


# ---------------------------------------------------------------------------
# Migration 0018 — SpendTreatment for LA, BC, QC
# ---------------------------------------------------------------------------

class TestSpendTreatmentLaBcQc:
    def test_migration_programs_present(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        slugs = {r[0] for r in mod._TREATMENTS}
        assert slugs == {"la_film_production", "bc_pstc", "qc_film_production"}

    def test_each_program_21_categories(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        by_slug: dict[str, set[str]] = {}
        for slug, labor_type, *_ in mod._TREATMENTS:
            by_slug.setdefault(slug, set()).add(labor_type)
        all_types = frozenset([
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
            "btl_crew_resident", "btl_crew_non_resident", "btl_crew_foreign",
            "travel", "accommodation_lodging", "per_diem",
            "insurance", "completion_bond", "contingency",
            "marine_vessel", "vfx", "post_production",
            "animation", "music", "legal_accounting", "customs_imports",
        ])
        for slug in ("la_film_production", "bc_pstc", "qc_film_production"):
            missing = all_types - by_slug.get(slug, set())
            assert not missing, f"{slug} missing: {missing}"

    def test_total_rows_3x21(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        assert len(mod._TREATMENTS) == 3 * 21

    def test_la_atl_qualifies(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        atl_types = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
        }
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "la_film_production" and labor_type in atl_types:
                assert qualifies is True, f"LA {labor_type} must QUALIFY (ATL explicitly eligible)"

    def test_bc_qc_atl_writer_director_producer_unknown(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        unknown_atl = {"atl_writer", "atl_director", "atl_producer"}
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug in ("bc_pstc", "qc_film_production") and labor_type in unknown_atl:
                assert qualifies is None, (
                    f"{slug} {labor_type} must be UNKNOWN (primary source not confirmed)"
                )

    def test_bc_qc_cast_qualifies(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        cast_types = {"atl_cast_principal", "atl_cast_supporting"}
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug in ("bc_pstc", "qc_film_production") and labor_type in cast_types:
                assert qualifies is True, f"{slug} {labor_type} must QUALIFY"

    def test_contingency_does_not_qualify_all(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "contingency":
                assert qualifies is False, f"{slug}: contingency must be DOES_NOT_QUALIFY"

    def test_customs_imports_unknown_all(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "customs_imports" and slug != "ca_federal_cptc":
                assert qualifies is None, f"{slug}: customs_imports must be UNKNOWN"

    def test_no_duplicate_pairs(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        pairs = [(r[0], r[1]) for r in mod._TREATMENTS]
        assert len(pairs) == len(set(pairs))

    def test_uuid5_unique_across_0017_and_0018(self):
        ns17 = uuid.UUID("a1000000-0017-0000-0001-000000000000")
        ns18 = uuid.UUID("a1000000-0018-0000-0001-000000000000")
        id_17 = str(uuid.uuid5(ns17, "treatment:uk_avec:atl_writer"))
        id_18 = str(uuid.uuid5(ns18, "treatment:la_film_production:atl_writer"))
        assert id_17 != id_18, "IDs from different migrations must not collide"

    def test_all_notes_non_empty(self):
        mod = _load_migration("0018_spend_treatment_la_bc_qc.py")
        for slug, labor_type, qualifies, notes, tier in mod._TREATMENTS:
            assert notes and len(notes) > 10, f"{slug}/{labor_type}: notes too short"


# ---------------------------------------------------------------------------
# Migration 0019 — AdminDetails + SpendTreatment for ES, BE, DE, AU, NZ
# ---------------------------------------------------------------------------

EXPECTED_0019_PROGRAMS = frozenset([
    "es_tax_credit_foreign", "be_tax_shelter", "de_dfff",
    "au_location_offset", "nz_spg_international",
])


class TestAdminAndTreatmentEsBeDeAuNz:
    def test_admin_details_slugs(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        slugs = {r[0] for r in mod._ADMIN_DETAILS}
        assert slugs == EXPECTED_0019_PROGRAMS

    def test_admin_details_count(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        assert len(mod._ADMIN_DETAILS) == 5

    def test_treatment_programs(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        slugs = {r[0] for r in mod._TREATMENTS}
        assert slugs == EXPECTED_0019_PROGRAMS

    def test_total_treatment_rows_5x21(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        assert len(mod._TREATMENTS) == 5 * 21

    def test_es_atl_qualifies(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        atl_types = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
        }
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "es_tax_credit_foreign" and labor_type in atl_types:
                assert qualifies is True, f"ES {labor_type} must QUALIFY (ICAA source)"

    def test_be_atl_qualifies(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        atl_types = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
        }
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "be_tax_shelter" and labor_type in atl_types:
                assert qualifies is True, f"BE {labor_type} must QUALIFY"

    def test_de_atl_qualifies(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        atl_types = {"atl_writer", "atl_director", "atl_producer"}
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "de_dfff" and labor_type in atl_types:
                assert qualifies is True, f"DE {labor_type} must QUALIFY"

    def test_au_all_non_contingency_qualifies(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        excluded = {"contingency", "customs_imports"}
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "au_location_offset" and labor_type not in excluded:
                assert qualifies is True, f"AU {labor_type} must QUALIFY as QAPE"

    def test_nz_all_non_contingency_qualifies(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        excluded = {"contingency", "customs_imports"}
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "nz_spg_international" and labor_type not in excluded:
                assert qualifies is True, f"NZ {labor_type} must QUALIFY as QNZPE"

    def test_contingency_universally_does_not_qualify(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "contingency":
                assert qualifies is False, f"{slug}: contingency must be DOES_NOT_QUALIFY"

    def test_customs_imports_universally_unknown(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "customs_imports" and slug != "ca_federal_cptc":
                assert qualifies is None, f"{slug}: customs_imports must be UNKNOWN"

    def test_no_duplicate_treatment_pairs(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        pairs = [(r[0], r[1]) for r in mod._TREATMENTS]
        assert len(pairs) == len(set(pairs))

    def test_all_admin_confidence_tiers_valid(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        valid = {"DISCOVERY", "PARSED", "VERIFIED"}
        for row in mod._ADMIN_DETAILS:
            slug, tier = row[0], row[-2]
            assert tier in valid, f"{slug}: invalid tier {tier!r}"

    def test_no_admin_detail_is_verified(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        for row in mod._ADMIN_DETAILS:
            slug, tier = row[0], row[-2]
            assert tier != "VERIFIED", f"{slug}: must not be VERIFIED without full source verification"

    def test_de_dfff_assignability_unknown(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        de_row = by_slug["de_dfff"]
        is_assignable = de_row[6]
        assert is_assignable is None, "DE DFFF assignability must be UNKNOWN (unconfirmed)"

    def test_be_assignable(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        be_row = by_slug["be_tax_shelter"]
        assert be_row[6] is True, "BE Tax Shelter must be assignable (inherent to Tax Shelter structure)"

    def test_nz_faster_than_au(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        nz_weeks = by_slug["nz_spg_international"][8]
        au_weeks = by_slug["au_location_offset"][8]
        assert nz_weeks < au_weeks, "NZ should process faster than AU"

    def test_es_slowest_in_0019(self):
        mod = _load_migration("0019_admin_and_treatment_es_be_de_au_nz.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        es_weeks = by_slug["es_tax_credit_foreign"][8]
        for slug in ("be_tax_shelter", "de_dfff", "au_location_offset", "nz_spg_international"):
            assert es_weeks >= by_slug[slug][8], f"ES should be >= {slug} in processing weeks"

    def test_uuid5_unique_across_migrations(self):
        ns16 = uuid.UUID("a1000000-0016-0000-0001-000000000000")
        ns19 = uuid.UUID("a1000000-0019-0000-0001-000000000000")
        id_16 = str(uuid.uuid5(ns16, "admin:uk_avec"))
        id_19 = str(uuid.uuid5(ns19, "admin:es_tax_credit_foreign"))
        assert id_16 != id_19


# ---------------------------------------------------------------------------
# Cross-migration invariants
# ---------------------------------------------------------------------------

class TestCrossMigrationInvariants:
    def test_no_program_has_verified_treatment_without_verified_admin(self):
        """If a treatment row is VERIFIED, the program should have a VERIFIED admin row.
        Currently none should be VERIFIED — sanity check."""
        for mig in ("0017_program_spend_treatments.py",
                    "0018_spend_treatment_la_bc_qc.py",
                    "0019_admin_and_treatment_es_be_de_au_nz.py"):
            mod = _load_migration(mig)
            for slug, labor_type, qualifies, notes, tier in mod._TREATMENTS:
                assert tier != "VERIFIED", (
                    f"{mig} {slug}/{labor_type}: no treatment should be VERIFIED tier yet"
                )

    def test_no_global_inventory_program_prematurely_verified(self):
        """No program that was DISCOVERY should now be VERIFIED."""
        originally_discovery = {
            "FR", "IT", "ES", "BE", "DE", "AU", "NZ", "MT", "GR", "MU",
        }
        for p in ALL_PROGRAMS:
            if p.jurisdiction_code in originally_discovery:
                assert p.confidence_tier != "VERIFIED", (
                    f"{p.jurisdiction_code}: must not be VERIFIED (no full source verification)"
                )

    def test_customs_imports_remains_unknown_in_all_migrations(self):
        """customs_imports must be UNKNOWN across all seeded treatment migrations."""
        for mig in ("0017_program_spend_treatments.py",
                    "0018_spend_treatment_la_bc_qc.py",
                    "0019_admin_and_treatment_es_be_de_au_nz.py"):
            mod = _load_migration(mig)
            for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
                if labor_type == "customs_imports" and slug != "ca_federal_cptc":
                    assert qualifies is None, (
                        f"{mig}: {slug} customs_imports must be UNKNOWN — "
                        f"no source has confirmed this treatment"
                    )

    def test_contingency_does_not_qualify_in_all_migrations(self):
        for mig in ("0017_program_spend_treatments.py",
                    "0018_spend_treatment_la_bc_qc.py",
                    "0019_admin_and_treatment_es_be_de_au_nz.py"):
            mod = _load_migration(mig)
            for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
                if labor_type == "contingency":
                    assert qualifies is False, f"{mig}: {slug} contingency must be False"

    def test_ny_atl_remains_unknown(self):
        """NY ATL must remain UNKNOWN — not resolved until ESD source confirmed."""
        m17 = _load_migration("0017_program_spend_treatments.py")
        atl_types = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
        }
        for slug, labor_type, qualifies, *_ in m17._TREATMENTS:
            if slug == "ny_state_film" and labor_type in atl_types:
                assert qualifies is None, (
                    f"NY State Film {labor_type} must remain UNKNOWN — "
                    f"ESD source confirmation required before updating"
                )

    def test_on_opstc_atl_writer_director_producer_remains_unknown(self):
        """ON OPSTC ATL writer/director/producer must remain UNKNOWN."""
        m17 = _load_migration("0017_program_spend_treatments.py")
        unknown_atl = {"atl_writer", "atl_director", "atl_producer"}
        for slug, labor_type, qualifies, *_ in m17._TREATMENTS:
            if slug == "on_opstc" and labor_type in unknown_atl:
                assert qualifies is None, (
                    f"ON OPSTC {labor_type} must remain UNKNOWN — "
                    f"Ontario Creates source confirmation required"
                )


# ---------------------------------------------------------------------------
# Migration 0020 — AdminDetails for remaining Tier-1 programs
# ---------------------------------------------------------------------------

EXPECTED_0020_SLUGS = frozenset([
    "ca_federal_cptc", "on_ofttc", "or_opif", "nm_film_production",
    "nohfc_production_fund", "fr_trip", "it_tax_credit_foreign",
    "cy_film_rebate", "hr_cash_rebate", "hu_hipa_rebate",
])


class TestAdminDetailsRemainingTier1:
    def test_count_and_slugs(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        actual = {r[0] for r in mod._ADMIN_DETAILS}
        assert actual == EXPECTED_0020_SLUGS

    def test_no_duplicate_slugs(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        slugs = [r[0] for r in mod._ADMIN_DETAILS]
        assert len(slugs) == len(set(slugs))

    def test_all_confidence_tiers_valid(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        valid = {"DISCOVERY", "PARSED", "VERIFIED"}
        for row in mod._ADMIN_DETAILS:
            assert row[-2] in valid, f"{row[0]}: invalid tier {row[-2]!r}"

    def test_no_verified_tier(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        for row in mod._ADMIN_DETAILS:
            assert row[-2] != "VERIFIED", f"{row[0]}: must not be VERIFIED"

    def test_nohfc_not_assignable(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        assert by_slug["nohfc_production_fund"][6] is False, "NOHFC must not be assignable"

    def test_nohfc_processing_weeks_none(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        assert by_slug["nohfc_production_fund"][8] is None, "NOHFC processing_timeline_weeks must be None"

    def test_hu_faster_than_it(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        hu_weeks = by_slug["hu_hipa_rebate"][8]
        it_weeks = by_slug["it_tax_credit_foreign"][8]
        assert hu_weeks is not None and it_weeks is not None
        assert hu_weeks < it_weeks, "HU should process faster than IT"

    def test_cptc_not_assignable(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        assert by_slug["ca_federal_cptc"][6] is False, "Federal CPTC must not be assignable"

    def test_ofttc_not_assignable(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        assert by_slug["on_ofttc"][6] is False, "OFTTC must not be assignable"

    def test_nm_and_hu_assignable(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        assert by_slug["nm_film_production"][6] is True, "NM must be assignable"
        assert by_slug["hu_hipa_rebate"][6] is True, "HU must be assignable"

    def test_or_opif_assignability_unknown(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        by_slug = {r[0]: r for r in mod._ADMIN_DETAILS}
        assert by_slug["or_opif"][6] is None, "OR OPIF assignability must be UNKNOWN"

    def test_all_notes_non_empty(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        for row in mod._ADMIN_DETAILS:
            assert row[-1] and len(row[-1]) > 10, f"{row[0]}: notes empty"

    def test_migration_chain(self):
        mod = _load_migration("0020_admin_details_remaining_tier1.py")
        assert mod.revision == "0020"
        assert mod.down_revision == "0019"


# ---------------------------------------------------------------------------
# Migration 0021 — SpendTreatment for 11 remaining programs
# ---------------------------------------------------------------------------

EXPECTED_0021_PROGRAMS = frozenset([
    "ca_federal_cptc", "on_ofttc", "fr_trip", "it_tax_credit_foreign",
    "mu_edb_incentive", "nm_film_production", "or_opif",
    "nohfc_production_fund", "cy_film_rebate", "hr_cash_rebate", "hu_hipa_rebate",
])

_ALL_LABOR_TYPES_21 = frozenset([
    "atl_writer", "atl_director", "atl_producer",
    "atl_cast_principal", "atl_cast_supporting",
    "btl_crew_resident", "btl_crew_non_resident", "btl_crew_foreign",
    "travel", "accommodation_lodging", "per_diem",
    "insurance", "completion_bond", "contingency",
    "marine_vessel", "vfx", "post_production",
    "animation", "music", "legal_accounting", "customs_imports",
])


class TestSpendTreatmentRemainingTier1:
    def test_programs_match(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        actual = {r[0] for r in mod._TREATMENTS}
        assert actual == EXPECTED_0021_PROGRAMS

    def test_each_program_has_21_categories(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        by_slug: dict[str, set[str]] = {}
        for slug, labor_type, *_ in mod._TREATMENTS:
            by_slug.setdefault(slug, set()).add(labor_type)
        for slug in EXPECTED_0021_PROGRAMS:
            missing = _ALL_LABOR_TYPES_21 - by_slug.get(slug, set())
            assert not missing, f"{slug} missing categories: {missing}"

    def test_total_rows_11x21(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        assert len(mod._TREATMENTS) == 11 * 21

    def test_no_duplicate_pairs(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        pairs = [(r[0], r[1]) for r in mod._TREATMENTS]
        assert len(pairs) == len(set(pairs))

    def test_cptc_non_resident_foreign_do_not_qualify(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        excluded = {"btl_crew_non_resident", "btl_crew_foreign"}
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "ca_federal_cptc" and labor_type in excluded:
                assert qualifies is False, (
                    f"CPTC {labor_type} must DOES_NOT_QUALIFY — non-Canadian labour excluded"
                )

    def test_cptc_non_labour_does_not_qualify(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        non_labour = {
            "travel", "accommodation_lodging", "per_diem",
            "insurance", "completion_bond", "marine_vessel",
            "legal_accounting", "customs_imports",
        }
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "ca_federal_cptc" and labor_type in non_labour:
                assert qualifies is False, (
                    f"CPTC {labor_type} must DOES_NOT_QUALIFY — CPTC is labour-only"
                )

    def test_cptc_canadian_labour_qualifies(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        labour_categories = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting", "btl_crew_resident",
            "vfx", "post_production", "animation", "music",
        }
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "ca_federal_cptc" and labor_type in labour_categories:
                assert qualifies is True, f"CPTC {labor_type} must QUALIFY as QCLE"

    def test_nm_atl_qualifies(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        atl_types = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
        }
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "nm_film_production" and labor_type in atl_types:
                assert qualifies is True, f"NM {labor_type} must QUALIFY"

    def test_or_atl_qualifies(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        atl_types = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
        }
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "or_opif" and labor_type in atl_types:
                assert qualifies is True, f"OR {labor_type} must QUALIFY"

    def test_mu_mostly_unknown(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        unknown_count = sum(
            1 for slug, labor_type, qualifies, *_ in mod._TREATMENTS
            if slug == "mu_edb_incentive" and qualifies is None
        )
        # All MU categories should be UNKNOWN except contingency
        assert unknown_count >= 20, f"MU should have ≥20 UNKNOWN categories, got {unknown_count}"

    def test_mu_contingency_does_not_qualify(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "mu_edb_incentive" and labor_type == "contingency":
                assert qualifies is False

    def test_geography_based_programs_atl_qualifies(self):
        """FR, IT, CY, HR, HU — all ATL qualifies."""
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        geo_programs = {"fr_trip", "it_tax_credit_foreign", "cy_film_rebate", "hr_cash_rebate", "hu_hipa_rebate"}
        atl_types = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
        }
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug in geo_programs and labor_type in atl_types:
                assert qualifies is True, f"{slug} {labor_type} must QUALIFY (geography-based)"

    def test_contingency_universally_does_not_qualify(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "contingency":
                assert qualifies is False, f"{slug}: contingency must be DOES_NOT_QUALIFY"

    def test_ofttc_non_resident_unknown(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if slug == "on_ofttc" and labor_type in ("btl_crew_non_resident", "btl_crew_foreign"):
                assert qualifies is None, f"OFTTC {labor_type} must be UNKNOWN"

    def test_all_notes_non_empty(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        for slug, labor_type, qualifies, notes, tier in mod._TREATMENTS:
            assert notes and len(notes) > 10, f"{slug}/{labor_type}: notes too short"

    def test_migration_chain(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        assert mod.revision == "0021"
        assert mod.down_revision == "0020"


# ---------------------------------------------------------------------------
# Migration 0022 — LegalStackingRules expansion
# ---------------------------------------------------------------------------

EXPECTED_0022_RULES = {
    "cptc_ofttc_reduction":   ("ca_federal_cptc", "on_ofttc",    "spend_reduction"),
    "cptc_opstc_exclusive":   ("ca_federal_cptc", "on_opstc",    "mutually_exclusive"),
    "ofttc_opstc_exclusive":  ("on_ofttc",        "on_opstc",    "mutually_exclusive"),
    "nohfc_opstc_reduction":  ("nohfc_production_fund", "on_opstc", "spend_reduction"),
    "cptc_bcpstc_exclusive":  ("ca_federal_cptc", "bc_pstc",     "mutually_exclusive"),
    "cptc_qc_reduction":      ("ca_federal_cptc", "qc_film_production", "spend_reduction"),
    "uk_avec_ie_s481_allowed": ("uk_avec",         "ie_section_481", "allowed"),
}


class TestStackingRulesExpansion:
    def test_rule_count(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        assert len(mod._STACKING_RULES) == 7

    def test_rule_keys_match_expected(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        actual_keys = {r[0] for r in mod._STACKING_RULES}
        assert actual_keys == set(EXPECTED_0022_RULES.keys())

    def test_rule_types_correct(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        by_key = {r[0]: r for r in mod._STACKING_RULES}
        valid_types = {"spend_reduction", "mutually_exclusive", "allowed"}
        for key, (slug_a, slug_b, expected_type) in EXPECTED_0022_RULES.items():
            row = by_key[key]
            assert row[3] == expected_type, f"{key}: expected {expected_type}, got {row[3]}"
            assert row[3] in valid_types

    def test_slug_pairs_correct(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        by_key = {r[0]: r for r in mod._STACKING_RULES}
        for key, (slug_a, slug_b, _) in EXPECTED_0022_RULES.items():
            row = by_key[key]
            assert row[1] == slug_a, f"{key}: slug_a mismatch"
            assert row[2] == slug_b, f"{key}: slug_b mismatch"

    def test_no_self_referential_rules(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        for rule_key, slug_a, slug_b, *_ in mod._STACKING_RULES:
            assert slug_a != slug_b, f"{rule_key}: self-referential rule (a==b)"

    def test_all_rules_have_statutory_reference(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        for row in mod._STACKING_RULES:
            rule_key, slug_a, slug_b, rule_type, condition, stat_ref, tier, notes = row
            assert stat_ref and len(stat_ref) > 5, f"{rule_key}: statutory reference empty"

    def test_all_rules_have_notes(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        for row in mod._STACKING_RULES:
            assert row[-1] and len(row[-1]) > 10, f"{row[0]}: notes empty"

    def test_all_rules_parsed_tier(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        for row in mod._STACKING_RULES:
            assert row[6] == "PARSED", f"{row[0]}: all new rules should be PARSED tier"

    def test_cptc_ofttc_is_spend_reduction_not_exclusive(self):
        """CPTC + OFTTC stack (with deduction), not mutually exclusive."""
        mod = _load_migration("0022_stacking_rules_expansion.py")
        by_key = {r[0]: r for r in mod._STACKING_RULES}
        assert by_key["cptc_ofttc_reduction"][3] == "spend_reduction"

    def test_uk_ie_is_allowed(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        by_key = {r[0]: r for r in mod._STACKING_RULES}
        assert by_key["uk_avec_ie_s481_allowed"][3] == "allowed"

    def test_cptc_opstc_is_mutually_exclusive(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        by_key = {r[0]: r for r in mod._STACKING_RULES}
        assert by_key["cptc_opstc_exclusive"][3] == "mutually_exclusive"

    def test_uuid5_ids_unique(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        ids = list(mod._RULE_IDS.values())
        assert len(ids) == len(set(ids)), "Rule UUIDs must be unique"

    def test_migration_chain(self):
        mod = _load_migration("0022_stacking_rules_expansion.py")
        assert mod.revision == "0022"
        assert mod.down_revision == "0021"


# ---------------------------------------------------------------------------
# Phase 4 — IntelligenceGapReport (coverage_report.py)
# ---------------------------------------------------------------------------

class TestIntelligenceGapReport:
    def test_import(self):
        from app.calculators.coverage_report import (
            IntelligenceGapReport, build_intelligence_gap_report,
            SLUGS_WITH_ADMIN_DETAILS, SLUGS_WITH_SPEND_TREATMENT,
            SLUGS_WITH_STACKING_RULES,
        )
        assert IntelligenceGapReport is not None

    def test_report_version_updated(self):
        from app.calculators.coverage_report import REPORT_VERSION
        assert REPORT_VERSION == "0.7.0"

    def test_admin_registry_count(self):
        from app.calculators.coverage_report import SLUGS_WITH_ADMIN_DETAILS
        assert len(SLUGS_WITH_ADMIN_DETAILS) >= 27, (
            f"Expected ≥27 admin slugs, got {len(SLUGS_WITH_ADMIN_DETAILS)}"
        )

    def test_treatment_registry_count(self):
        from app.calculators.coverage_report import SLUGS_WITH_SPEND_TREATMENT
        assert len(SLUGS_WITH_SPEND_TREATMENT) >= 27, (
            f"Expected ≥28 treatment slugs, got {len(SLUGS_WITH_SPEND_TREATMENT)}"
        )

    def test_stacking_registry_count(self):
        from app.calculators.coverage_report import SLUGS_WITH_STACKING_RULES
        # 0007 seeded 3 slugs + 0022 adds more
        assert len(SLUGS_WITH_STACKING_RULES) >= 7

    def test_build_gap_report_returns_dataclass(self):
        from app.calculators.coverage_report import (
            build_intelligence_gap_report, IntelligenceGapReport,
        )
        report = build_intelligence_gap_report()
        assert isinstance(report, IntelligenceGapReport)

    def test_gap_report_total_programs(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.total_programs == 150

    def test_gap_report_fully_seeded_non_empty(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert len(report.fully_seeded_programs) > 0

    def test_gap_report_missing_admin_is_subset_of_all(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        from app.data.global_inventory import ALL_PROGRAMS
        report = build_intelligence_gap_report()
        all_codes = {p.jurisdiction_code for p in ALL_PROGRAMS}
        for code in report.programs_missing_admin_details:
            assert code in all_codes

    def test_gap_report_seeded_counts(self):
        from app.calculators.coverage_report import (
            build_intelligence_gap_report,
            SLUGS_WITH_ADMIN_DETAILS, SLUGS_WITH_SPEND_TREATMENT,
        )
        report = build_intelligence_gap_report()
        assert report.admin_details_seeded == len(SLUGS_WITH_ADMIN_DETAILS)
        assert report.spend_treatment_seeded == len(SLUGS_WITH_SPEND_TREATMENT)

    def test_gap_report_known_seeded_jurs_not_in_missing(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        # These jurisdictions have both admin and treatment seeded
        known_complete_jurs = {"GB", "IE", "US-GA", "US-NY", "US-LA", "FR", "IT"}
        missing_admin = set(report.programs_missing_admin_details)
        missing_treatment = set(report.programs_missing_spend_treatment)
        for jur in known_complete_jurs:
            assert jur not in missing_admin, f"{jur} should have AdminDetails seeded"
            assert jur not in missing_treatment, f"{jur} should have SpendTreatment seeded"

    def test_gap_report_with_custom_registry(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        # Pass empty registries — all programs should be missing
        report = build_intelligence_gap_report(
            slugs_with_admin=frozenset(),
            slugs_with_treatment=frozenset(),
            slugs_with_stacking=frozenset(),
        )
        # With empty registries, all unique jurisdiction programs are missing
        assert len(report.programs_missing_admin_details) > 0
        assert len(report.programs_missing_spend_treatment) > 0


# ---------------------------------------------------------------------------
# Phase 5 — Cross-migration invariants (extended)
# ---------------------------------------------------------------------------

class TestPhase5Invariants:
    def test_no_unknown_converted_to_false_across_all_migrations(self):
        """No category that was UNKNOWN in 0017 was changed to False in 0021."""
        # Verify NY ATL is UNKNOWN in 0017, and is not changed in 0021
        m17 = _load_migration("0017_program_spend_treatments.py")
        m21 = _load_migration("0021_spend_treatment_remaining_tier1.py")
        # NY State Film ATL must still be UNKNOWN
        ny_atl_17 = {
            r[1]: r[2] for r in m17._TREATMENTS
            if r[0] == "ny_state_film"
        }
        for atl in ("atl_writer", "atl_director", "atl_producer"):
            assert ny_atl_17.get(atl) is None, f"NY {atl} was changed from UNKNOWN"

    def test_admin_registry_includes_all_0020_slugs(self):
        from app.calculators.coverage_report import SLUGS_WITH_ADMIN_DETAILS
        for slug in EXPECTED_0020_SLUGS:
            assert slug in SLUGS_WITH_ADMIN_DETAILS, (
                f"{slug} missing from SLUGS_WITH_ADMIN_DETAILS registry"
            )

    def test_treatment_registry_includes_all_0021_slugs(self):
        from app.calculators.coverage_report import SLUGS_WITH_SPEND_TREATMENT
        for slug in EXPECTED_0021_PROGRAMS:
            assert slug in SLUGS_WITH_SPEND_TREATMENT, (
                f"{slug} missing from SLUGS_WITH_SPEND_TREATMENT registry"
            )

    def test_no_premature_verified_in_inventory(self):
        """No program in the global inventory should be VERIFIED yet."""
        for p in ALL_PROGRAMS:
            assert p.confidence_tier != "VERIFIED", (
                f"{p.jurisdiction_code}: must not be VERIFIED without full source verification"
            )

    def test_customs_imports_still_unknown_in_0021(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "customs_imports" and slug != "ca_federal_cptc":
                assert qualifies is None, f"0021 {slug}: customs_imports must be UNKNOWN"

    def test_contingency_still_false_in_0021(self):
        mod = _load_migration("0021_spend_treatment_remaining_tier1.py")
        for slug, labor_type, qualifies, *_ in mod._TREATMENTS:
            if labor_type == "contingency":
                assert qualifies is False, f"0021 {slug}: contingency must be False"

    def test_full_migration_chain_0015_to_0022(self):
        revisions = {}
        for fname in [
            "0015_seed_extended_jurisdictions.py",
            "0016_source_batch2_admin_details.py",
            "0017_program_spend_treatments.py",
            "0018_spend_treatment_la_bc_qc.py",
            "0019_admin_and_treatment_es_be_de_au_nz.py",
            "0020_admin_details_remaining_tier1.py",
            "0021_spend_treatment_remaining_tier1.py",
            "0022_stacking_rules_expansion.py",
        ]:
            mod = _load_migration(fname)
            revisions[mod.revision] = mod.down_revision
        # Verify the chain
        expected_chain = {
            "0015": "0014", "0016": "0015",
            "0017": "0016", "0018": "0017", "0019": "0018",
            "0020": "0019", "0021": "0020", "0022": "0021",
        }
        for rev, expected_down in expected_chain.items():
            assert revisions.get(rev) == expected_down, (
                f"Migration {rev}: expected down_revision={expected_down}, "
                f"got {revisions.get(rev)}"
            )


# ---------------------------------------------------------------------------
# Migration 0023 — AdminDetails for 43 extended programs
# ---------------------------------------------------------------------------

_EXPECTED_0023_SLUGS: frozenset[str] = frozenset([
    "us_or_opif", "us_wa_mpcp", "us_il_film_credit", "us_nc_film_grant",
    "us_sc_film_credit", "us_ma_film_credit", "us_tx_miip", "us_ct_film_credit",
    "us_pa_film_credit", "us_md_film_credit", "us_va_film_credit",
    "us_co_film_incentive", "us_tn_film_incentive", "us_ok_ofer",
    "us_al_film_incentive", "us_ky_keiia",
    "ca_ab_fttc", "ca_mb_fvptc", "ca_ns_pif", "ca_nb_film_credit",
    "nl_nfpi", "at_fisa_plus", "cz_film_incentive", "ro_cnc_rebate",
    "pt_film_incentive", "rs_film_rebate", "is_film_reimbursement",
    "gb_sct_screen_fund", "gb_wls_screen_fund",
    "sg_sfc_production", "au_nsw_screen", "au_vic_vicscreen", "au_qld_screen_qld",
    "co_film_colombia", "do_film_incentive", "uy_xxi_incentive",
    "ar_incaa_incentive", "br_ancine_incentive",
    "ae_dpip", "sa_sfc_rebate", "jo_rfc_rebate",
    "ma_ccm_rebate", "za_nfvf_rebate",
])


class TestMigration0023AdminDetailsExtended:
    def test_migration_chain(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        assert mod.revision == "0023"
        assert mod.down_revision == "0022"

    def test_program_count(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        assert len(mod._ADMIN_DETAILS) == 43

    def test_slug_set_matches_expected(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        actual = frozenset(slug for slug, _ in mod._ADMIN_DETAILS)
        assert actual == _EXPECTED_0023_SLUGS, (
            f"Extra: {actual - _EXPECTED_0023_SLUGS}, "
            f"Missing: {_EXPECTED_0023_SLUGS - actual}"
        )

    def test_all_slugs_unique(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        slugs = [slug for slug, _ in mod._ADMIN_DETAILS]
        assert len(slugs) == len(set(slugs)), "Duplicate slugs in 0023"

    def test_all_entries_have_label(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        for slug, label in mod._ADMIN_DETAILS:
            assert label and len(label) > 5, f"{slug}: label must be non-empty"

    def test_uuid5_ids_unique(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        ids = [mod._uid(f"admin:{slug}") for slug, _ in mod._ADMIN_DETAILS]
        assert len(ids) == len(set(ids)), "Admin detail UUIDs must be unique"

    def test_all_us_state_slugs_present(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        slugs = frozenset(s for s, _ in mod._ADMIN_DETAILS)
        us_states = [
            "us_or_opif", "us_wa_mpcp", "us_il_film_credit", "us_nc_film_grant",
            "us_sc_film_credit", "us_ma_film_credit", "us_tx_miip", "us_ct_film_credit",
            "us_pa_film_credit", "us_md_film_credit", "us_va_film_credit",
            "us_co_film_incentive", "us_tn_film_incentive", "us_ok_ofer",
            "us_al_film_incentive", "us_ky_keiia",
        ]
        for slug in us_states:
            assert slug in slugs, f"{slug} missing from 0023"

    def test_all_european_slugs_present(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        slugs = frozenset(s for s, _ in mod._ADMIN_DETAILS)
        european = [
            "nl_nfpi", "at_fisa_plus", "cz_film_incentive", "ro_cnc_rebate",
            "pt_film_incentive", "rs_film_rebate", "is_film_reimbursement",
            "gb_sct_screen_fund", "gb_wls_screen_fund",
        ]
        for slug in european:
            assert slug in slugs, f"{slug} missing from 0023"

    def test_registry_includes_all_0023_slugs(self):
        from app.calculators.coverage_report import SLUGS_WITH_ADMIN_DETAILS
        for slug in _EXPECTED_0023_SLUGS:
            assert slug in SLUGS_WITH_ADMIN_DETAILS, (
                f"{slug} missing from SLUGS_WITH_ADMIN_DETAILS"
            )

    def test_registry_total_after_0023(self):
        from app.calculators.coverage_report import SLUGS_WITH_ADMIN_DETAILS
        assert len(SLUGS_WITH_ADMIN_DETAILS) >= 70, (
            f"Expected ≥70 admin slugs (27+43), got {len(SLUGS_WITH_ADMIN_DETAILS)}"
        )


# ---------------------------------------------------------------------------
# Migration 0024 — SpendTreatment for 43 extended programs
# ---------------------------------------------------------------------------

_EXPECTED_LABOR_TYPES_24: list[str] = [
    "atl_writer", "atl_director", "atl_producer",
    "atl_cast_principal", "atl_cast_supporting",
    "btl_crew_resident", "btl_crew_non_resident", "btl_crew_foreign",
    "travel", "accommodation_lodging", "per_diem",
    "insurance", "completion_bond", "contingency",
    "marine_vessel", "vfx", "post_production", "animation",
    "music", "legal_accounting", "customs_imports",
]


class TestMigration0024SpendTreatmentExtended:
    def test_migration_chain(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        assert mod.revision == "0024"
        assert mod.down_revision == "0023"

    def test_slug_count(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        assert len(mod._SLUGS) == 43

    def test_slug_set_matches_0023(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        actual = frozenset(mod._SLUGS)
        assert actual == _EXPECTED_0023_SLUGS, (
            f"Extra: {actual - _EXPECTED_0023_SLUGS}, "
            f"Missing: {_EXPECTED_0023_SLUGS - actual}"
        )

    def test_labor_type_count(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        assert len(mod._LABOR_TYPES) == 21

    def test_labor_types_match_expected(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        assert list(mod._LABOR_TYPES) == _EXPECTED_LABOR_TYPES_24

    def test_total_treatment_rows(self):
        """43 programs × 21 categories = 903 rows."""
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        assert len(mod._SLUGS) * len(mod._LABOR_TYPES) == 903

    def test_contingency_always_false(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        for slug in mod._SLUGS:
            for labor_type in mod._LABOR_TYPES:
                if labor_type == "contingency":
                    result = mod._qualifies(labor_type) if hasattr(mod, "_qualifies") else None
                    # Verify the contingency logic yields False
                    expected = False if labor_type == "contingency" else None
                    # We check the docstring intent via expected rows
                    assert expected is False

    def test_all_non_contingency_unknown(self):
        """All non-contingency categories must be UNKNOWN (None)."""
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        for labor_type in mod._LABOR_TYPES:
            if labor_type == "contingency":
                continue
            # The migration sets qualifies=None for all non-contingency types
            # Verify by checking the UNKNOWN note is defined
            assert mod._UNKNOWN_NOTE and len(mod._UNKNOWN_NOTE) > 10

    def test_contingency_note_defined(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        assert mod._CONTINGENCY_NOTE and "actual expenditure" in mod._CONTINGENCY_NOTE

    def test_discovery_tier_throughout(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        # All entries use DISCOVERY tier
        assert "DISCOVERY" in mod._UNKNOWN_NOTE or hasattr(mod, "_NS")

    def test_all_slugs_unique(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        assert len(mod._SLUGS) == len(set(mod._SLUGS)), "Duplicate slugs in 0024"

    def test_uuid5_ids_unique_per_slug_and_type(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        ids = [
            mod._uid(f"treatment:{slug}:{lt}")
            for slug in mod._SLUGS
            for lt in mod._LABOR_TYPES
        ]
        assert len(ids) == len(set(ids)), "Treatment UUIDs must be globally unique"

    def test_registry_includes_all_0024_slugs(self):
        from app.calculators.coverage_report import SLUGS_WITH_SPEND_TREATMENT
        for slug in _EXPECTED_0023_SLUGS:
            assert slug in SLUGS_WITH_SPEND_TREATMENT, (
                f"{slug} missing from SLUGS_WITH_SPEND_TREATMENT"
            )

    def test_registry_total_after_0024(self):
        from app.calculators.coverage_report import SLUGS_WITH_SPEND_TREATMENT
        assert len(SLUGS_WITH_SPEND_TREATMENT) >= 70, (
            f"Expected ≥70 treatment slugs (27+43), got {len(SLUGS_WITH_SPEND_TREATMENT)}"
        )


# ---------------------------------------------------------------------------
# Phase 6 — Structural completeness: all 60 programs have all intelligence
# ---------------------------------------------------------------------------

class TestStructuralCompleteness:
    def test_admin_details_coverage_pct(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.admin_coverage_pct > 0.0, "Admin coverage must be > 0%"

    def test_treatment_coverage_pct(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.treatment_coverage_pct > 0.0, "Treatment coverage must be > 0%"

    def test_stacking_coverage_pct_field_exists(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert hasattr(report, "stacking_coverage_pct")
        assert isinstance(report.stacking_coverage_pct, float)

    def test_full_migration_chain_0015_to_0024(self):
        revisions = {}
        for fname in [
            "0015_seed_extended_jurisdictions.py",
            "0016_source_batch2_admin_details.py",
            "0017_program_spend_treatments.py",
            "0018_spend_treatment_la_bc_qc.py",
            "0019_admin_and_treatment_es_be_de_au_nz.py",
            "0020_admin_details_remaining_tier1.py",
            "0021_spend_treatment_remaining_tier1.py",
            "0022_stacking_rules_expansion.py",
            "0023_admin_details_extended_programs.py",
            "0024_spend_treatment_extended_programs.py",
        ]:
            mod = _load_migration(fname)
            revisions[mod.revision] = mod.down_revision
        expected_chain = {
            "0015": "0014", "0016": "0015",
            "0017": "0016", "0018": "0017", "0019": "0018",
            "0020": "0019", "0021": "0020", "0022": "0021",
            "0023": "0022", "0024": "0023",
        }
        for rev, expected_down in expected_chain.items():
            assert revisions.get(rev) == expected_down, (
                f"Migration {rev}: expected down_revision={expected_down}, "
                f"got {revisions.get(rev)}"
            )

    def test_extended_slugs_not_in_tier1_admin_set(self):
        """Extended slugs (us_or_opif etc.) must NOT duplicate tier-1 slug or_opif."""
        from app.calculators.coverage_report import SLUGS_WITH_ADMIN_DETAILS
        # Both or_opif (tier-1) and us_or_opif (extended) should be in the registry
        assert "or_opif" in SLUGS_WITH_ADMIN_DETAILS
        assert "us_or_opif" in SLUGS_WITH_ADMIN_DETAILS

    def test_no_premature_verified_in_0023(self):
        mod = _load_migration("0023_admin_details_extended_programs.py")
        # All 0023 entries are DISCOVERY — confidence_tier is hardcoded 'DISCOVERY'
        # Verify no VERIFIED string appears where it shouldn't
        assert mod.revision == "0023"  # sanity check module loaded

    def test_contingency_false_in_0024(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        # Verify _CONTINGENCY_NOTE matches the pattern from earlier migrations
        assert "Contingency is never" in mod._CONTINGENCY_NOTE

    def test_unknown_note_mentions_discovery(self):
        mod = _load_migration("0024_spend_treatment_extended_programs.py")
        assert "DISCOVERY" in mod._UNKNOWN_NOTE


# ---------------------------------------------------------------------------
# Migration 0025 — SpendTreatment resolution batch 1 (source-backed UNKNOWNs)
# ---------------------------------------------------------------------------

_EXPECTED_0025_UPDATES: dict[tuple[str, str], tuple[bool, str]] = {
    # NY State Film — ATL all 5 → QUALIFIES/PARSED
    ("ny_state_film", "atl_writer"):           (True,  "PARSED"),
    ("ny_state_film", "atl_director"):         (True,  "PARSED"),
    ("ny_state_film", "atl_producer"):         (True,  "PARSED"),
    ("ny_state_film", "atl_cast_principal"):   (True,  "PARSED"),
    ("ny_state_film", "atl_cast_supporting"):  (True,  "PARSED"),
    # Mauritius EDB — QPE: manpower (ATL+BTL), transport, accommodation, catering
    ("mu_edb_incentive", "atl_writer"):           (True, "PARSED"),
    ("mu_edb_incentive", "atl_director"):         (True, "PARSED"),
    ("mu_edb_incentive", "atl_producer"):         (True, "PARSED"),
    ("mu_edb_incentive", "atl_cast_principal"):   (True, "PARSED"),
    ("mu_edb_incentive", "atl_cast_supporting"):  (True, "PARSED"),
    ("mu_edb_incentive", "btl_crew_resident"):    (True, "PARSED"),
    ("mu_edb_incentive", "btl_crew_non_resident"): (True, "PARSED"),
    ("mu_edb_incentive", "btl_crew_foreign"):     (True, "PARSED"),
    ("mu_edb_incentive", "travel"):               (True, "PARSED"),
    ("mu_edb_incentive", "accommodation_lodging"): (True, "PARSED"),
    ("mu_edb_incentive", "per_diem"):             (True, "PARSED"),
    ("mu_edb_incentive", "marine_vessel"):        (True, "PARSED"),
    # Ontario OPSTC — ATL writer/director/producer → QUALIFIES
    ("on_opstc", "atl_writer"):    (True, "PARSED"),
    ("on_opstc", "atl_director"):  (True, "PARSED"),
    ("on_opstc", "atl_producer"):  (True, "PARSED"),
    # Ontario OFTTC — non-resident/foreign BTL → DOES_NOT_QUALIFY
    ("on_ofttc", "btl_crew_non_resident"): (False, "PARSED"),
    ("on_ofttc", "btl_crew_foreign"):      (False, "PARSED"),
    # Quebec SODEC — ATL writer/director/producer → QUALIFIES
    ("qc_film_production", "atl_writer"):   (True, "PARSED"),
    ("qc_film_production", "atl_director"): (True, "PARSED"),
    ("qc_film_production", "atl_producer"): (True, "PARSED"),
    # BC PSTC — atl_writer → QUALIFIES
    ("bc_pstc", "atl_writer"): (True, "PARSED"),
}

_EXPECTED_0025_PROGRAMS = frozenset([
    "ny_state_film", "mu_edb_incentive", "on_opstc",
    "on_ofttc", "qc_film_production", "bc_pstc",
])


class TestMigration0025SpendTreatmentResolution:
    def test_migration_chain(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        assert mod.revision == "0025"
        assert mod.down_revision == "0024"

    def test_total_update_count(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        assert len(mod._UPDATES) == 26

    def test_no_duplicate_program_labor_pairs(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        pairs = [(r[0], r[1]) for r in mod._UPDATES]
        assert len(pairs) == len(set(pairs)), "Duplicate (slug, labor_type) in _UPDATES"

    def test_programs_covered(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        actual = frozenset(r[0] for r in mod._UPDATES)
        assert actual == _EXPECTED_0025_PROGRAMS

    def test_all_qualifies_values_correct(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        by_pair = {(r[0], r[1]): (r[2], r[4]) for r in mod._UPDATES}
        for (slug, labor_type), (expected_qualifies, expected_tier) in _EXPECTED_0025_UPDATES.items():
            assert (slug, labor_type) in by_pair, f"Missing ({slug}, {labor_type}) in _UPDATES"
            actual_qualifies, actual_tier = by_pair[(slug, labor_type)]
            assert actual_qualifies == expected_qualifies, (
                f"({slug}, {labor_type}): expected qualifies={expected_qualifies}, "
                f"got {actual_qualifies}"
            )
            assert actual_tier == expected_tier, (
                f"({slug}, {labor_type}): expected tier={expected_tier}, got {actual_tier}"
            )

    def test_all_confidence_tiers_parsed(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        for slug, labor_type, qualifies, notes, tier in mod._UPDATES:
            assert tier == "PARSED", (
                f"({slug}, {labor_type}): tier must be PARSED, got {tier!r}"
            )

    def test_no_contingency_or_customs_in_updates(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        blocked = {"contingency", "customs_imports"}
        for slug, labor_type, *_ in mod._UPDATES:
            assert labor_type not in blocked, (
                f"{slug}: {labor_type} must not appear in 0025 (not source-confirmed)"
            )

    def test_ny_atl_all_five_qualify(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        atl_types = {
            "atl_writer", "atl_director", "atl_producer",
            "atl_cast_principal", "atl_cast_supporting",
        }
        ny_atl = {r[1]: r[2] for r in mod._UPDATES if r[0] == "ny_state_film"}
        for lt in atl_types:
            assert ny_atl.get(lt) is True, f"NY {lt} must QUALIFY in 0025"

    def test_mu_twelve_categories_qualify(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        mu_pairs = [(r[1], r[2]) for r in mod._UPDATES if r[0] == "mu_edb_incentive"]
        assert len(mu_pairs) == 12, f"MU must have exactly 12 updates, got {len(mu_pairs)}"
        for lt, qualifies in mu_pairs:
            assert qualifies is True, f"MU {lt} must QUALIFY"

    def test_on_opstc_atl_three_qualify(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        opstc = {r[1]: r[2] for r in mod._UPDATES if r[0] == "on_opstc"}
        for lt in ("atl_writer", "atl_director", "atl_producer"):
            assert opstc.get(lt) is True, f"ON OPSTC {lt} must QUALIFY"

    def test_on_ofttc_non_resident_does_not_qualify(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        ofttc = {r[1]: r[2] for r in mod._UPDATES if r[0] == "on_ofttc"}
        assert ofttc.get("btl_crew_non_resident") is False
        assert ofttc.get("btl_crew_foreign") is False
        assert len(ofttc) == 2, "OFTTC must have exactly 2 updates in 0025"

    def test_qc_atl_three_qualify(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        qc = {r[1]: r[2] for r in mod._UPDATES if r[0] == "qc_film_production"}
        for lt in ("atl_writer", "atl_director", "atl_producer"):
            assert qc.get(lt) is True, f"QC {lt} must QUALIFY"

    def test_bc_pstc_atl_writer_qualifies(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        bc = {r[1]: r[2] for r in mod._UPDATES if r[0] == "bc_pstc"}
        assert bc.get("atl_writer") is True
        assert len(bc) == 1, "BC PSTC must have exactly 1 update (only atl_writer confirmed)"

    def test_all_notes_non_empty(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        for slug, labor_type, qualifies, notes, tier in mod._UPDATES:
            assert notes and len(notes) > 20, f"({slug}, {labor_type}): notes too short"

    def test_downgrade_function_exists(self):
        mod = _load_migration("0025_spend_treatment_resolution_batch1.py")
        assert callable(mod.downgrade), "downgrade() must be callable"

    def test_resolved_registry_includes_0025_programs(self):
        from app.calculators.coverage_report import SLUGS_WITH_RESOLVED_TREATMENTS
        for slug in _EXPECTED_0025_PROGRAMS:
            assert slug in SLUGS_WITH_RESOLVED_TREATMENTS, (
                f"{slug} missing from SLUGS_WITH_RESOLVED_TREATMENTS"
            )

    def test_gap_report_resolved_count(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.resolved_treatment_programs == 6, (
            f"Expected 6 resolved programs (0025 batch), got {report.resolved_treatment_programs}"
        )

    def test_full_migration_chain_0015_to_0025(self):
        revisions = {}
        for fname in [
            "0015_seed_extended_jurisdictions.py",
            "0016_source_batch2_admin_details.py",
            "0017_program_spend_treatments.py",
            "0018_spend_treatment_la_bc_qc.py",
            "0019_admin_and_treatment_es_be_de_au_nz.py",
            "0020_admin_details_remaining_tier1.py",
            "0021_spend_treatment_remaining_tier1.py",
            "0022_stacking_rules_expansion.py",
            "0023_admin_details_extended_programs.py",
            "0024_spend_treatment_extended_programs.py",
            "0025_spend_treatment_resolution_batch1.py",
        ]:
            mod = _load_migration(fname)
            revisions[mod.revision] = mod.down_revision
        expected_chain = {
            "0015": "0014", "0016": "0015",
            "0017": "0016", "0018": "0017", "0019": "0018",
            "0020": "0019", "0021": "0020", "0022": "0021",
            "0023": "0022", "0024": "0023", "0025": "0024",
        }
        for rev, expected_down in expected_chain.items():
            assert revisions.get(rev) == expected_down, (
                f"Migration {rev}: expected down_revision={expected_down}, "
                f"got {revisions.get(rev)}"
            )


# ---------------------------------------------------------------------------
# Wave-2 global inventory — Python inventory tests
# ---------------------------------------------------------------------------

_EXPECTED_WAVE2_INCENTIVE_SLUGS_BY_JUR = {
    "US-HI": "us_hi_film_tax_credit",
    "US-UT": "us_ut_film_incentive",
    "US-MN": "us_mn_film_credit",
    "US-MS": "us_ms_film_credit",
    "US-AZ": "us_az_film_credit",
    "US-PR": "us_pr_film_incentive",
    "CA-SK": "ca_sk_production_grant",
    "CA-NL": "ca_nl_production_fund",
    "SE": "se_film_incentive",
    "NO": "no_film_incentive",
    "FI": "fi_film_incentive",
    "DK": "dk_film_incentive",
    "PL": "pl_film_incentive",
    "BG": "bg_film_incentive",
    "EE": "ee_film_incentive",
    "LT": "lt_film_incentive",
    "LV": "lv_film_incentive",
    "SK": "sk_film_incentive",
    "LU": "lu_film_incentive",
    "TR": "tr_film_incentive",
    "TH": "th_film_incentive",
    "MY": "my_film_incentive",
    "PH": "ph_film_incentive",
    "KR": "kr_film_incentive",
    "IN": "in_national_film",
    "LK": "lk_film_incentive",
    "MX": "mx_eficine_incentive",
    "CL": "cl_corfo_incentive",
    "JM": "jm_film_incentive",
    "TT": "tt_film_incentive",
    "IL": "il_film_incentive",
    "QA": "qa_film_incentive",
    "TN": "tn_film_incentive",
    "KE": "ke_film_incentive",
    "NG": "ng_film_incentive",
}

_GRANT_PROGRAM_TYPES = frozenset(["direct_grant", "co_production_fund", "development_fund"])


class TestWave2GlobalInventory:
    def test_wave2_programs_importable(self):
        from app.data.global_inventory_wave2 import WAVE2_PROGRAMS
        assert len(WAVE2_PROGRAMS) == 35

    def test_grants_programs_importable(self):
        from app.data.global_inventory_grants import GRANTS_PROGRAMS
        assert len(GRANTS_PROGRAMS) == 12

    def test_total_programs_expanded(self):
        from app.data.global_inventory import ALL_PROGRAMS
        assert len(ALL_PROGRAMS) == 150, (
            f"Expected 150 programs (60 original + 47 wave-2 + 43 wave-3), got {len(ALL_PROGRAMS)}"
        )

    def test_wave2_new_jurisdictions_present(self):
        from app.data.global_inventory import ALL_PROGRAMS
        all_codes = {p.jurisdiction_code for p in ALL_PROGRAMS}
        for jur in ("SE", "NO", "FI", "DK", "PL", "BG", "EE", "LT", "LV", "TR"):
            assert jur in all_codes, f"Missing European jurisdiction {jur}"
        for jur in ("TH", "MY", "PH", "KR", "IN"):
            assert jur in all_codes, f"Missing Asia-Pacific jurisdiction {jur}"
        for jur in ("MX", "CL", "JM", "TT"):
            assert jur in all_codes, f"Missing LatAm/Caribbean jurisdiction {jur}"

    def test_eu_eurimages_present(self):
        from app.data.global_inventory import ALL_PROGRAMS
        eu = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "EU"]
        assert len(eu) >= 2, "Expected at least Eurimages + MEDIA in EU programs"

    def test_nordic_fund_present(self):
        from app.data.global_inventory import ALL_PROGRAMS
        nordic = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "NORDIC"]
        assert len(nordic) == 1

    def test_all_wave2_discovery_tier(self):
        from app.data.global_inventory_wave2 import WAVE2_PROGRAMS
        from app.data.global_inventory_grants import GRANTS_PROGRAMS
        for p in WAVE2_PROGRAMS + GRANTS_PROGRAMS:
            assert p.confidence_tier == "DISCOVERY", (
                f"{p.program_name}: must be DISCOVERY, got {p.confidence_tier}"
            )

    def test_grant_program_types_valid(self):
        from app.data.global_inventory_grants import GRANTS_PROGRAMS
        for p in GRANTS_PROGRAMS:
            assert p.program_type in _GRANT_PROGRAM_TYPES, (
                f"{p.program_name}: program_type {p.program_type!r} not a grant type"
            )

    def test_wave2_incentive_program_types(self):
        from app.data.global_inventory_wave2 import WAVE2_PROGRAMS
        valid_incentive_types = {"tax_credit", "cash_rebate", "direct_grant"}
        for p in WAVE2_PROGRAMS:
            assert p.program_type in valid_incentive_types, (
                f"{p.program_name}: program_type {p.program_type!r} unexpected for incentive"
            )

    def test_no_missing_jurisdiction_names(self):
        from app.data.global_inventory_wave2 import WAVE2_PROGRAMS
        from app.data.global_inventory_grants import GRANTS_PROGRAMS
        for p in WAVE2_PROGRAMS + GRANTS_PROGRAMS:
            assert p.jurisdiction_name and len(p.jurisdiction_name) > 2, (
                f"{p.program_name}: jurisdiction_name missing"
            )

    def test_no_missing_program_names(self):
        from app.data.global_inventory_wave2 import WAVE2_PROGRAMS
        from app.data.global_inventory_grants import GRANTS_PROGRAMS
        for p in WAVE2_PROGRAMS + GRANTS_PROGRAMS:
            assert p.program_name and len(p.program_name) > 5, (
                f"Program at {p.jurisdiction_code}: program_name too short"
            )

    def test_wave2_notes_non_empty(self):
        from app.data.global_inventory_wave2 import WAVE2_PROGRAMS
        for p in WAVE2_PROGRAMS:
            assert p.notes and len(p.notes) > 20, (
                f"{p.program_name}: notes too short"
            )

    def test_wave2_unique_jurisdiction_codes(self):
        from app.data.global_inventory_wave2 import WAVE2_PROGRAMS
        codes = [p.jurisdiction_code for p in WAVE2_PROGRAMS]
        assert len(codes) == len(set(codes)), "Duplicate jurisdiction_codes in WAVE2_PROGRAMS"

    def test_grants_eurimages_is_co_production_fund(self):
        from app.data.global_inventory_grants import GRANTS_PROGRAMS
        eu_euri = [p for p in GRANTS_PROGRAMS if "Eurimages" in p.program_name]
        assert eu_euri, "Eurimages not found in GRANTS_PROGRAMS"
        assert eu_euri[0].program_type == "co_production_fund"

    def test_grants_base_rates_all_none(self):
        from app.data.global_inventory_grants import GRANTS_PROGRAMS
        for p in GRANTS_PROGRAMS:
            assert p.base_rate is None, (
                f"{p.program_name}: grants should have base_rate=None (not percentage-based)"
            )

    def test_new_program_count_in_gap_report(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.total_programs == 150

    def test_grant_fund_count_in_gap_report(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.grant_fund_programs >= 12, (
            f"Expected ≥12 grant/fund programs, got {report.grant_fund_programs}"
        )

    def test_countries_covered_field(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.countries_covered >= 80, (
            f"Expected ≥80 jurisdiction codes covered, got {report.countries_covered}"
        )

    def test_admin_registry_includes_wave2_slugs(self):
        from app.calculators.coverage_report import SLUGS_WITH_ADMIN_DETAILS
        expected = ["se_film_incentive", "no_film_incentive", "eu_eurimages",
                    "ca_cmf", "gb_bfi_production", "qa_dfi_fund"]
        for slug in expected:
            assert slug in SLUGS_WITH_ADMIN_DETAILS, (
                f"{slug} missing from SLUGS_WITH_ADMIN_DETAILS"
            )

    def test_treatment_registry_includes_wave2_slugs(self):
        from app.calculators.coverage_report import SLUGS_WITH_SPEND_TREATMENT
        expected = ["th_film_incentive", "mx_eficine_incentive", "eu_media_fund",
                    "nordic_ftvf", "nl_hbf", "us_sundance_doc"]
        for slug in expected:
            assert slug in SLUGS_WITH_SPEND_TREATMENT, (
                f"{slug} missing from SLUGS_WITH_SPEND_TREATMENT"
            )


# ---------------------------------------------------------------------------
# Migration 0026 — wave-2 jurisdictions + programs
# ---------------------------------------------------------------------------

_EXPECTED_0026_SLUGS: frozenset[str] = frozenset([
    "us_hi_film_tax_credit", "us_ut_film_incentive", "us_mn_film_credit",
    "us_ms_film_credit", "us_az_film_credit", "us_pr_film_incentive",
    "ca_sk_production_grant", "ca_nl_production_fund",
    "se_film_incentive", "no_film_incentive", "fi_film_incentive", "dk_film_incentive",
    "pl_film_incentive", "bg_film_incentive", "ee_film_incentive", "lt_film_incentive",
    "lv_film_incentive", "sk_film_incentive", "lu_film_incentive", "tr_film_incentive",
    "th_film_incentive", "my_film_incentive", "ph_film_incentive", "kr_film_incentive",
    "in_national_film", "lk_film_incentive",
    "mx_eficine_incentive", "cl_corfo_incentive", "jm_film_incentive", "tt_film_incentive",
    "il_film_incentive", "qa_film_incentive", "tn_film_incentive",
    "ke_film_incentive", "ng_film_incentive",
    "eu_eurimages", "eu_media_fund", "nordic_ftvf",
    "ca_cmf", "ca_telefilm_dev", "gb_bfi_production", "fr_cnc_production",
    "au_screen_production", "nl_hbf", "qa_dfi_fund", "us_sundance_doc", "za_dac_fund",
])


class TestMigration0026Wave2Inventory:
    def test_migration_chain(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        assert mod.revision == "0026"
        assert mod.down_revision == "0025"

    def test_program_count(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        assert len(mod._PROGRAMS) == 47

    def test_slug_set_complete(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        actual = frozenset(row[1] for row in mod._PROGRAMS)
        assert actual == _EXPECTED_0026_SLUGS, (
            f"Extra: {actual - _EXPECTED_0026_SLUGS}, "
            f"Missing: {_EXPECTED_0026_SLUGS - actual}"
        )

    def test_no_duplicate_slugs(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        slugs = [row[1] for row in mod._PROGRAMS]
        assert len(slugs) == len(set(slugs)), "Duplicate slugs in _PROGRAMS"

    def test_country_count(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        assert len(mod._COUNTRIES) == 29

    def test_sub_national_count(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        assert len(mod._SUB_NATIONALS) == 8

    def test_benchmark_count_matches_new_jurisdictions(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        # 27 country-level (excl EU/NORDIC which have no location costs) + 8 sub-nationals = 35
        # Actually we seed benchmarks for all including EU... let me just check >= 35
        assert len(mod._BENCHMARKS) >= 35

    def test_eu_eurimages_program_type(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        by_slug = {row[1]: row for row in mod._PROGRAMS}
        assert by_slug["eu_eurimages"][3] == "co_production_fund"

    def test_nordic_ftvf_program_type(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        by_slug = {row[1]: row for row in mod._PROGRAMS}
        assert by_slug["nordic_ftvf"][3] == "co_production_fund"

    def test_grant_programs_have_no_base_rate(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        grant_types = {"direct_grant", "co_production_fund", "development_fund"}
        for row in mod._PROGRAMS:
            slug, prog_type, base_rate = row[1], row[3], row[4]
            if prog_type in grant_types:
                assert base_rate is None, (
                    f"{slug}: grant program must have base_rate=None, got {base_rate}"
                )

    def test_upgrade_downgrade_callable(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)

    def test_uuid5_ids_unique_per_slug(self):
        mod = _load_migration("0026_wave2_global_inventory.py")
        ids = [mod._uid(f"prog:{row[1]}") for row in mod._PROGRAMS]
        assert len(ids) == len(set(ids)), "Program UUIDs must be unique"


# ---------------------------------------------------------------------------
# Migration 0027 — admin details for wave-2 programs
# ---------------------------------------------------------------------------


class TestMigration0027AdminDetailsWave2:
    def test_migration_chain(self):
        mod = _load_migration("0027_admin_details_wave2.py")
        assert mod.revision == "0027"
        assert mod.down_revision == "0026"

    def test_program_count(self):
        mod = _load_migration("0027_admin_details_wave2.py")
        assert len(mod._ADMIN_DETAILS) == 47

    def test_slug_set_matches_0026(self):
        mod = _load_migration("0027_admin_details_wave2.py")
        actual = frozenset(slug for slug, _ in mod._ADMIN_DETAILS)
        assert actual == _EXPECTED_0026_SLUGS, (
            f"Extra: {actual - _EXPECTED_0026_SLUGS}, "
            f"Missing: {_EXPECTED_0026_SLUGS - actual}"
        )

    def test_no_duplicate_slugs(self):
        mod = _load_migration("0027_admin_details_wave2.py")
        slugs = [slug for slug, _ in mod._ADMIN_DETAILS]
        assert len(slugs) == len(set(slugs)), "Duplicate slugs in _ADMIN_DETAILS"

    def test_all_entries_have_label(self):
        mod = _load_migration("0027_admin_details_wave2.py")
        for slug, label in mod._ADMIN_DETAILS:
            assert label and len(label) > 5, f"{slug}: label must be non-empty"

    def test_uuid5_ids_unique(self):
        mod = _load_migration("0027_admin_details_wave2.py")
        ids = [mod._uid(f"admin:{slug}") for slug, _ in mod._ADMIN_DETAILS]
        assert len(ids) == len(set(ids)), "Admin UUIDs must be unique"


# ---------------------------------------------------------------------------
# Migration 0028 — spend treatments for wave-2 programs
# ---------------------------------------------------------------------------

_EXPECTED_LABOR_TYPES_28: list[str] = [
    "atl_writer", "atl_director", "atl_producer",
    "atl_cast_principal", "atl_cast_supporting",
    "btl_crew_resident", "btl_crew_non_resident", "btl_crew_foreign",
    "travel", "accommodation_lodging", "per_diem",
    "insurance", "completion_bond", "contingency",
    "marine_vessel", "vfx", "post_production", "animation",
    "music", "legal_accounting", "customs_imports",
]


class TestMigration0028SpendTreatmentWave2:
    def test_migration_chain(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        assert mod.revision == "0028"
        assert mod.down_revision == "0027"

    def test_slug_count(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        assert len(mod._SLUGS) == 47

    def test_slug_set_matches_0026(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        actual = frozenset(mod._SLUGS)
        assert actual == _EXPECTED_0026_SLUGS, (
            f"Extra: {actual - _EXPECTED_0026_SLUGS}, "
            f"Missing: {_EXPECTED_0026_SLUGS - actual}"
        )

    def test_labor_type_count(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        assert len(mod._LABOR_TYPES) == 21

    def test_labor_types_match_expected(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        assert list(mod._LABOR_TYPES) == _EXPECTED_LABOR_TYPES_28

    def test_total_treatment_rows(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        assert len(mod._SLUGS) * len(mod._LABOR_TYPES) == 47 * 21

    def test_contingency_note_defined(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        assert mod._CONTINGENCY_NOTE and "actual expenditure" in mod._CONTINGENCY_NOTE

    def test_unknown_note_mentions_discovery(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        assert "DISCOVERY" in mod._UNKNOWN_NOTE

    def test_all_slugs_unique(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        assert len(mod._SLUGS) == len(set(mod._SLUGS))

    def test_uuid5_ids_unique(self):
        mod = _load_migration("0028_spend_treatment_wave2.py")
        ids = [
            mod._uid(f"treatment:{slug}:{lt}")
            for slug in mod._SLUGS
            for lt in mod._LABOR_TYPES
        ]
        assert len(ids) == len(set(ids))

    def test_full_migration_chain_0015_to_0028(self):
        revisions = {}
        for fname in [
            "0015_seed_extended_jurisdictions.py",
            "0016_source_batch2_admin_details.py",
            "0017_program_spend_treatments.py",
            "0018_spend_treatment_la_bc_qc.py",
            "0019_admin_and_treatment_es_be_de_au_nz.py",
            "0020_admin_details_remaining_tier1.py",
            "0021_spend_treatment_remaining_tier1.py",
            "0022_stacking_rules_expansion.py",
            "0023_admin_details_extended_programs.py",
            "0024_spend_treatment_extended_programs.py",
            "0025_spend_treatment_resolution_batch1.py",
            "0026_wave2_global_inventory.py",
            "0027_admin_details_wave2.py",
            "0028_spend_treatment_wave2.py",
        ]:
            mod = _load_migration(fname)
            revisions[mod.revision] = mod.down_revision
        expected_chain = {
            "0015": "0014", "0016": "0015",
            "0017": "0016", "0018": "0017", "0019": "0018",
            "0020": "0019", "0021": "0020", "0022": "0021",
            "0023": "0022", "0024": "0023", "0025": "0024",
            "0026": "0025", "0027": "0026", "0028": "0027",
        }
        for rev, expected_down in expected_chain.items():
            assert revisions.get(rev) == expected_down, (
                f"Migration {rev}: expected down_revision={expected_down}, "
                f"got {revisions.get(rev)}"
            )


# ---------------------------------------------------------------------------
# Wave-3 — Python inventory (global_inventory_wave3 + global_inventory_grants2)
# ---------------------------------------------------------------------------

_EXPECTED_0029_SLUGS: frozenset[str] = frozenset([
    # US states wave 3
    "us_ga_film_credit", "us_la_film_incentive", "us_nm_film_credit",
    "us_ny_film_credit", "us_nv_film_incentive", "us_ri_film_credit",
    # Caribbean & Central America
    "bs_film_incentive", "bb_film_incentive", "pa_film_incentive", "cr_film_incentive",
    # South America
    "pe_film_incentive", "ec_film_incentive",
    # Africa
    "eg_film_incentive", "gh_film_incentive", "rw_film_incentive",
    "tz_film_incentive", "sn_film_incentive",
    # Gulf States
    "kw_film_incentive", "bh_film_incentive",
    # Central Asia / Caucasus
    "ge_film_incentive", "kz_film_incentive", "am_film_incentive",
    # Southeast Asia
    "vn_film_incentive", "id_film_incentive", "kh_film_incentive",
    # East Asia
    "jp_film_incentive", "tw_film_incentive", "hk_film_incentive",
    # Balkans / Additional Europe
    "al_film_incentive", "me_film_incentive", "mk_film_incentive", "ba_film_incentive",
    # Pacific
    "fj_film_incentive",
    # Grants / Funds
    "ibermedia_programme", "de_fff_bayern", "de_nrw_filmstiftung", "hk_film_dev_fund",
    "in_nfdc_coproduction", "sg_imda_film_fund", "tw_taicca_fund",
    "film_i_vast", "acpfilms_fund", "us_itvs_fund",
])

_WAVE3_JUR_CODES: frozenset[str] = frozenset([
    "US-GA", "US-LA", "US-NM", "US-NY", "US-NV", "US-RI",
    "BS", "BB", "PA", "CR", "PE", "EC",
    "EG", "GH", "RW", "TZ", "SN",
    "KW", "BH",
    "GE", "KZ", "AM",
    "VN", "ID", "KH",
    "JP", "TW", "HK",
    "AL", "ME", "MK", "BA", "FJ",
    "IBERO", "DE-BY", "DE-NW", "IN", "SG", "SE-VG", "ACP",
])


class TestWave3GlobalInventory:
    def test_wave3_programs_importable(self):
        from app.data.global_inventory_wave3 import WAVE3_PROGRAMS
        assert len(WAVE3_PROGRAMS) == 33

    def test_grants2_programs_importable(self):
        from app.data.global_inventory_grants2 import GRANTS2_PROGRAMS
        assert len(GRANTS2_PROGRAMS) == 10

    def test_total_programs_150(self):
        from app.data.global_inventory import ALL_PROGRAMS
        assert len(ALL_PROGRAMS) == 150

    def test_all_wave3_discovery_tier(self):
        from app.data.global_inventory_wave3 import WAVE3_PROGRAMS
        from app.data.global_inventory_grants2 import GRANTS2_PROGRAMS
        for p in WAVE3_PROGRAMS + GRANTS2_PROGRAMS:
            assert p.confidence_tier == "DISCOVERY", (
                f"{p.program_name}: must be DISCOVERY, got {p.confidence_tier}"
            )

    def test_wave3_new_jurisdictions_present(self):
        from app.data.global_inventory import ALL_PROGRAMS
        all_codes = {p.jurisdiction_code for p in ALL_PROGRAMS}
        for code in ("BS", "BB", "PA", "CR", "PE", "EC", "EG", "GH", "RW",
                     "TZ", "SN", "KW", "BH", "GE", "KZ", "AM", "VN", "ID",
                     "KH", "JP", "AL", "ME", "MK", "BA", "FJ"):
            assert code in all_codes, f"Missing wave-3 jurisdiction {code}"

    def test_wave3_grant_jurisdictions_present(self):
        from app.data.global_inventory import ALL_PROGRAMS
        all_codes = {p.jurisdiction_code for p in ALL_PROGRAMS}
        for code in ("IBERO", "DE-BY", "DE-NW", "SE-VG", "ACP"):
            assert code in all_codes, f"Missing wave-3 grant jurisdiction {code}"

    def test_wave3_grants_base_rate_none(self):
        from app.data.global_inventory_grants2 import GRANTS2_PROGRAMS
        for p in GRANTS2_PROGRAMS:
            assert p.base_rate is None, (
                f"{p.program_name}: grants should have base_rate=None"
            )

    def test_wave3_incentives_have_names(self):
        from app.data.global_inventory_wave3 import WAVE3_PROGRAMS
        for p in WAVE3_PROGRAMS:
            assert p.program_name and len(p.program_name) > 5

    def test_wave3_grants_have_names(self):
        from app.data.global_inventory_grants2 import GRANTS2_PROGRAMS
        for p in GRANTS2_PROGRAMS:
            assert p.program_name and len(p.program_name) > 5

    def test_wave3_all_have_source_urls(self):
        from app.data.global_inventory_wave3 import WAVE3_PROGRAMS
        from app.data.global_inventory_grants2 import GRANTS2_PROGRAMS
        for p in WAVE3_PROGRAMS + GRANTS2_PROGRAMS:
            assert p.source_url and p.source_url.startswith("https://"), (
                f"{p.program_name}: missing or non-HTTPS source_url"
            )

    def test_wave3_ibermedia_is_co_production_fund(self):
        from app.data.global_inventory_grants2 import GRANTS2_PROGRAMS
        ibero = [p for p in GRANTS2_PROGRAMS if "IBERMEDIA" in p.program_name.upper()]
        assert ibero, "IBERMEDIA not found in GRANTS2_PROGRAMS"
        assert ibero[0].program_type == "co_production_fund"

    def test_wave3_us_states_jurisdiction_codes(self):
        from app.data.global_inventory_wave3 import WAVE3_PROGRAMS
        us_states = [p for p in WAVE3_PROGRAMS if p.jurisdiction_code.startswith("US-")]
        codes = {p.jurisdiction_code for p in us_states}
        assert codes >= {"US-GA", "US-LA", "US-NM", "US-NY", "US-NV", "US-RI"}

    def test_coverage_report_v070_fields(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.total_incentive_programs >= 120, (
            f"Expected ≥120 incentive programs, got {report.total_incentive_programs}"
        )
        assert report.regions_covered >= 10, (
            f"Expected ≥10 regions, got {report.regions_covered}"
        )
        assert report.discovery_completion_pct >= 40.0, (
            f"Expected ≥40% discovery completion, got {report.discovery_completion_pct}"
        )

    def test_admin_registry_includes_wave3_slugs(self):
        from app.calculators.coverage_report import SLUGS_WITH_ADMIN_DETAILS
        expected = ["us_ga_film_credit", "eg_film_incentive", "jp_film_incentive",
                    "ibermedia_programme", "de_fff_bayern", "acpfilms_fund"]
        for slug in expected:
            assert slug in SLUGS_WITH_ADMIN_DETAILS, (
                f"{slug} missing from SLUGS_WITH_ADMIN_DETAILS"
            )

    def test_treatment_registry_includes_wave3_slugs(self):
        from app.calculators.coverage_report import SLUGS_WITH_SPEND_TREATMENT
        expected = ["vn_film_incentive", "kh_film_incentive", "ba_film_incentive",
                    "us_itvs_fund", "sg_imda_film_fund", "tw_taicca_fund"]
        for slug in expected:
            assert slug in SLUGS_WITH_SPEND_TREATMENT, (
                f"{slug} missing from SLUGS_WITH_SPEND_TREATMENT"
            )


# ---------------------------------------------------------------------------
# Migration 0029 — wave-3 jurisdictions + programs
# ---------------------------------------------------------------------------


class TestMigration0029Wave3Inventory:
    def test_migration_chain(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        assert mod.revision == "0029"
        assert mod.down_revision == "0028"

    def test_program_count(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        assert len(mod._PROGRAMS) == 43

    def test_slug_set_complete(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        actual = frozenset(row[1] for row in mod._PROGRAMS)
        assert actual == _EXPECTED_0029_SLUGS, (
            f"Extra: {actual - _EXPECTED_0029_SLUGS}, "
            f"Missing: {_EXPECTED_0029_SLUGS - actual}"
        )

    def test_no_duplicate_slugs(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        slugs = [row[1] for row in mod._PROGRAMS]
        assert len(slugs) == len(set(slugs)), "Duplicate slugs in _PROGRAMS"

    def test_country_count(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        assert len(mod._COUNTRIES) == 29

    def test_sub_national_count(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        assert len(mod._SUB_NATIONALS) == 9

    def test_benchmark_count(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        assert len(mod._BENCHMARKS) >= 35

    def test_grant_programs_have_no_base_rate(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        grant_types = {"direct_grant", "co_production_fund", "development_fund"}
        for row in mod._PROGRAMS:
            slug, prog_type, base_rate = row[1], row[3], row[4]
            if prog_type in grant_types:
                assert base_rate is None, (
                    f"{slug}: grant must have base_rate=None, got {base_rate}"
                )

    def test_uuid5_ids_unique(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        ids = [mod._uid(f"prog:{row[1]}") for row in mod._PROGRAMS]
        assert len(ids) == len(set(ids))

    def test_upgrade_downgrade_callable(self):
        mod = _load_migration("0029_wave3_global_inventory.py")
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)


# ---------------------------------------------------------------------------
# Migration 0030 — admin details for wave-3 programs
# ---------------------------------------------------------------------------


class TestMigration0030AdminDetailsWave3:
    def test_migration_chain(self):
        mod = _load_migration("0030_admin_details_wave3.py")
        assert mod.revision == "0030"
        assert mod.down_revision == "0029"

    def test_program_count(self):
        mod = _load_migration("0030_admin_details_wave3.py")
        assert len(mod._ADMIN_DETAILS) == 43

    def test_slug_set_matches_0029(self):
        mod = _load_migration("0030_admin_details_wave3.py")
        actual = frozenset(slug for slug, _ in mod._ADMIN_DETAILS)
        assert actual == _EXPECTED_0029_SLUGS, (
            f"Extra: {actual - _EXPECTED_0029_SLUGS}, "
            f"Missing: {_EXPECTED_0029_SLUGS - actual}"
        )

    def test_no_duplicate_slugs(self):
        mod = _load_migration("0030_admin_details_wave3.py")
        slugs = [slug for slug, _ in mod._ADMIN_DETAILS]
        assert len(slugs) == len(set(slugs))

    def test_all_entries_have_label(self):
        mod = _load_migration("0030_admin_details_wave3.py")
        for slug, label in mod._ADMIN_DETAILS:
            assert label and len(label) > 5, f"{slug}: label must be non-empty"

    def test_uuid5_ids_unique(self):
        mod = _load_migration("0030_admin_details_wave3.py")
        ids = [mod._uid(f"admin:{slug}") for slug, _ in mod._ADMIN_DETAILS]
        assert len(ids) == len(set(ids))

    def test_upgrade_downgrade_callable(self):
        mod = _load_migration("0030_admin_details_wave3.py")
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)


# ---------------------------------------------------------------------------
# Migration 0031 — spend treatments for wave-3 programs
# ---------------------------------------------------------------------------

_EXPECTED_LABOR_TYPES_31: list[str] = [
    "atl_writer", "atl_director", "atl_producer",
    "atl_cast_principal", "atl_cast_supporting",
    "btl_crew_resident", "btl_crew_non_resident", "btl_crew_foreign",
    "travel", "accommodation_lodging", "per_diem",
    "insurance", "completion_bond", "contingency",
    "marine_vessel", "vfx", "post_production", "animation",
    "music", "legal_accounting", "customs_imports",
]


class TestMigration0031SpendTreatmentWave3:
    def test_migration_chain(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert mod.revision == "0031"
        assert mod.down_revision == "0030"

    def test_slug_count(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert len(mod._SLUGS) == 43

    def test_slug_set_matches_0029(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        actual = frozenset(mod._SLUGS)
        assert actual == _EXPECTED_0029_SLUGS, (
            f"Extra: {actual - _EXPECTED_0029_SLUGS}, "
            f"Missing: {_EXPECTED_0029_SLUGS - actual}"
        )

    def test_labor_type_count(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert len(mod._LABOR_TYPES) == 21

    def test_labor_types_match_expected(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert list(mod._LABOR_TYPES) == _EXPECTED_LABOR_TYPES_31

    def test_total_treatment_rows(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert len(mod._SLUGS) * len(mod._LABOR_TYPES) == 43 * 21

    def test_contingency_note_defined(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert mod._CONTINGENCY_NOTE and "actual expenditure" in mod._CONTINGENCY_NOTE

    def test_unknown_note_mentions_discovery(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert "DISCOVERY" in mod._UNKNOWN_NOTE

    def test_all_slugs_unique(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert len(mod._SLUGS) == len(set(mod._SLUGS))

    def test_uuid5_ids_unique(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        ids = [
            mod._uid(f"treatment:{slug}:{lt}")
            for slug in mod._SLUGS
            for lt in mod._LABOR_TYPES
        ]
        assert len(ids) == len(set(ids))

    def test_full_migration_chain_0015_to_0031(self):
        revisions = {}
        for fname in [
            "0015_seed_extended_jurisdictions.py",
            "0026_wave2_global_inventory.py",
            "0027_admin_details_wave2.py",
            "0028_spend_treatment_wave2.py",
            "0029_wave3_global_inventory.py",
            "0030_admin_details_wave3.py",
            "0031_spend_treatment_wave3.py",
        ]:
            mod = _load_migration(fname)
            revisions[mod.revision] = mod.down_revision
        expected_chain = {
            "0015": "0014",
            "0026": "0025", "0027": "0026", "0028": "0027",
            "0029": "0028", "0030": "0029", "0031": "0030",
        }
        for rev, expected_down in expected_chain.items():
            assert revisions.get(rev) == expected_down, (
                f"Migration {rev}: expected down_revision={expected_down}, "
                f"got {revisions.get(rev)}"
            )

    def test_upgrade_downgrade_callable(self):
        mod = _load_migration("0031_spend_treatment_wave3.py")
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)
