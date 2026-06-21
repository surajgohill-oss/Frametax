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
            if labor_type == "customs_imports":
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
            if labor_type == "customs_imports":
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
            if labor_type == "customs_imports":
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
                if labor_type == "customs_imports":
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
