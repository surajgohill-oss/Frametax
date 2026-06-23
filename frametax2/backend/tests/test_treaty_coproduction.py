"""
test_treaty_coproduction.py — Phase A+B validation.

Tests cover:
  - Phase C: ALL_PROGRAMS count == 240 (229 + 3 DB-sync + 8 Phase C)
  - Phase C: all 8 new regional programs are present and correct
  - Phase C: slug inference for Phase C programs
  - Phase D.5: new stacking pairs exist in _SLUG_PAIR_RULES
  - Structural: treaty migration data integrity checks (static validation of migration module)
  - Structural: multilateral treaty participant list lengths
  - Structural: co-production structure treaty_slug references are consistent
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import importlib.util
from unittest.mock import MagicMock

import pytest

# Ensure backend is on path
_BACKEND = Path(__file__).parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load_migration(filename: str):
    """Load an Alembic migration module outside of an Alembic context.

    Stubs out ``alembic.op`` so the module-level imports succeed, but
    upgrade()/downgrade() are NOT called (and would fail without a real DB).
    Only module-level constants (revision, down_revision, _TREATIES, etc.)
    are accessed.
    """
    alembic_mock = MagicMock()
    alembic_mock.op = MagicMock()
    saved = {}
    for key in ("alembic", "alembic.op"):
        saved[key] = sys.modules.get(key)
        sys.modules[key] = alembic_mock

    try:
        spec = importlib.util.spec_from_file_location(
            f"_migration_{filename}",
            _BACKEND / "alembic" / "versions" / filename,
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for key, val in saved.items():
            if val is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = val

from app.data.global_inventory import ALL_PROGRAMS, GlobalProgramEntry
from app.optimization.stacking_rules import _SLUG_PAIR_RULES, infer_slug


# ---------------------------------------------------------------------------
# Phase C program presence
# ---------------------------------------------------------------------------

class TestPhaseCInventory:
    """Phase C adds 8 regional programs; total should be 240."""

    def test_total_program_count_240(self):
        assert len(ALL_PROGRAMS) == 240, (
            f"Expected 240 programs (229 original + 3 DB-sync + 8 Phase C), "
            f"got {len(ALL_PROGRAMS)}"
        )

    def test_fr_idf_present(self):
        matches = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "FR-IDF"]
        assert len(matches) >= 1, "FR-IDF (Île-de-France) not found in ALL_PROGRAMS"

    def test_fr_naq_present(self):
        matches = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "FR-NAQ"]
        assert len(matches) >= 1, "FR-NAQ (Nouvelle-Aquitaine) not found in ALL_PROGRAMS"

    def test_fr_ara_present(self):
        matches = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "FR-ARA"]
        assert len(matches) >= 1, "FR-ARA (Auvergne-Rhône-Alpes) not found in ALL_PROGRAMS"

    def test_fr_occ_present(self):
        matches = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "FR-OCC"]
        assert len(matches) >= 1, "FR-OCC (Occitanie) not found in ALL_PROGRAMS"

    def test_be_wal_present(self):
        matches = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "BE-WAL"]
        assert len(matches) >= 1, "BE-WAL (Wallimage) not found in ALL_PROGRAMS"

    def test_be_vlg_present(self):
        matches = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "BE-VLG"]
        assert len(matches) >= 1, "BE-VLG (VAF Flanders) not found in ALL_PROGRAMS"

    def test_be_bru_present(self):
        matches = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "BE-BRU"]
        assert len(matches) >= 1, "BE-BRU (Screen.Brussels) not found in ALL_PROGRAMS"

    def test_de_ni_present(self):
        matches = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "DE-NI"]
        assert len(matches) >= 1, "DE-NI (nordmedia) not found in ALL_PROGRAMS"

    def test_phase_c_programs_are_regional_fund_type(self):
        phase_c_jurs = {"FR-IDF", "FR-NAQ", "FR-ARA", "FR-OCC",
                        "BE-WAL", "BE-VLG", "BE-BRU", "DE-NI"}
        phase_c = [p for p in ALL_PROGRAMS if p.jurisdiction_code in phase_c_jurs]
        for p in phase_c:
            assert p.program_type == "regional_fund", (
                f"{p.program_name} ({p.jurisdiction_code}) should be regional_fund, "
                f"got {p.program_type}"
            )

    def test_phase_c_programs_have_annual_cap(self):
        phase_c_jurs = {"FR-IDF", "FR-NAQ", "FR-ARA", "FR-OCC",
                        "BE-WAL", "BE-VLG", "BE-BRU", "DE-NI"}
        phase_c = [p for p in ALL_PROGRAMS if p.jurisdiction_code in phase_c_jurs]
        for p in phase_c:
            assert p.annual_cap_usd is not None, (
                f"{p.program_name} missing annual_cap_usd"
            )
            assert p.annual_cap_usd > 0, (
                f"{p.program_name} annual_cap_usd must be > 0"
            )

    def test_phase_c_programs_are_discovery_tier(self):
        phase_c_jurs = {"FR-IDF", "FR-NAQ", "FR-ARA", "FR-OCC",
                        "BE-WAL", "BE-VLG", "BE-BRU", "DE-NI"}
        phase_c = [p for p in ALL_PROGRAMS if p.jurisdiction_code in phase_c_jurs]
        for p in phase_c:
            assert p.confidence_tier == "DISCOVERY", (
                f"{p.program_name} should be DISCOVERY tier, got {p.confidence_tier}"
            )


# ---------------------------------------------------------------------------
# Phase C slug inference
# ---------------------------------------------------------------------------

class TestPhaseCSlugInference:
    """Slug inference rules added for Phase C programs."""

    def test_wallimage_slug_inference(self):
        p = next(
            (p for p in ALL_PROGRAMS if p.jurisdiction_code == "BE-WAL"),
            None,
        )
        assert p is not None, "BE-WAL not in ALL_PROGRAMS"
        slug = infer_slug(p)
        assert slug == "be_wal_wallimage", (
            f"Expected be_wal_wallimage, got {slug}"
        )

    def test_vaf_slug_inference(self):
        p = next(
            (p for p in ALL_PROGRAMS if p.jurisdiction_code == "BE-VLG"),
            None,
        )
        assert p is not None, "BE-VLG not in ALL_PROGRAMS"
        slug = infer_slug(p)
        assert slug == "be_vlg_vaf", f"Expected be_vlg_vaf, got {slug}"

    def test_nordmedia_slug_inference(self):
        p = next(
            (p for p in ALL_PROGRAMS if p.jurisdiction_code == "DE-NI"),
            None,
        )
        assert p is not None, "DE-NI not in ALL_PROGRAMS"
        slug = infer_slug(p)
        assert slug == "de_ni_nordmedia", f"Expected de_ni_nordmedia, got {slug}"


# ---------------------------------------------------------------------------
# Phase D.5 stacking pairs
# ---------------------------------------------------------------------------

class TestPhasD5StackingPairs:
    """New stacking pairs added in Phase D.5 must be present in _SLUG_PAIR_RULES."""

    def _pair_exists(self, slug_a: str, slug_b: str) -> bool:
        return frozenset({slug_a, slug_b}) in _SLUG_PAIR_RULES

    def _pair_rule_type(self, slug_a: str, slug_b: str) -> str | None:
        rule = _SLUG_PAIR_RULES.get(frozenset({slug_a, slug_b}))
        return rule["rule_type"] if rule else None

    def test_fff_bayern_dfff_allowed(self):
        assert self._pair_exists("de_fff_bayern", "de_dfff"), (
            "FFF Bayern + DFFF pair missing from _SLUG_PAIR_RULES"
        )
        assert self._pair_rule_type("de_fff_bayern", "de_dfff") == "allowed"

    def test_nrw_dfff_allowed(self):
        assert self._pair_exists("de_nrw_filmstiftung", "de_dfff"), (
            "Filmstiftung NRW + DFFF pair missing"
        )
        assert self._pair_rule_type("de_nrw_filmstiftung", "de_dfff") == "allowed"

    def test_nordmedia_dfff_allowed(self):
        assert self._pair_exists("de_ni_nordmedia", "de_dfff"), (
            "nordmedia + DFFF pair missing"
        )
        assert self._pair_rule_type("de_ni_nordmedia", "de_dfff") == "allowed"

    def test_be_tax_shelter_wallimage_allowed(self):
        assert self._pair_exists("be_tax_shelter", "be_wal_wallimage"), (
            "BE tax shelter + Wallimage pair missing"
        )
        assert self._pair_rule_type("be_tax_shelter", "be_wal_wallimage") == "allowed"

    def test_be_tax_shelter_vaf_allowed(self):
        assert self._pair_exists("be_tax_shelter", "be_vlg_vaf"), (
            "BE tax shelter + VAF pair missing"
        )
        assert self._pair_rule_type("be_tax_shelter", "be_vlg_vaf") == "allowed"

    def test_be_tax_shelter_screen_brussels_allowed(self):
        assert self._pair_exists("be_tax_shelter", "be_bru_screen"), (
            "BE tax shelter + Screen.Brussels pair missing"
        )
        assert self._pair_rule_type("be_tax_shelter", "be_bru_screen") == "allowed"

    def test_eurimages_dfff_allowed(self):
        assert self._pair_exists("eu_eurimages", "de_dfff"), (
            "Eurimages + DFFF pair missing"
        )
        assert self._pair_rule_type("eu_eurimages", "de_dfff") == "allowed"

    def test_eurimages_be_tax_shelter_allowed(self):
        assert self._pair_exists("eu_eurimages", "be_tax_shelter"), (
            "Eurimages + BE tax shelter pair missing"
        )
        assert self._pair_rule_type("eu_eurimages", "be_tax_shelter") == "allowed"

    def test_fr_cnc_idf_allowed(self):
        assert self._pair_exists("fr_cnc_production", "fr_idf_regional"), (
            "FR CNC + IDF regional pair missing"
        )
        assert self._pair_rule_type("fr_cnc_production", "fr_idf_regional") == "allowed"

    def test_fr_cnc_naq_allowed(self):
        assert self._pair_exists("fr_cnc_production", "fr_naq_regional"), (
            "FR CNC + NAQ regional pair missing"
        )

    def test_fr_cnc_ara_allowed(self):
        assert self._pair_exists("fr_cnc_production", "fr_ara_regional"), (
            "FR CNC + ARA regional pair missing"
        )

    def test_fr_cnc_occ_allowed(self):
        assert self._pair_exists("fr_cnc_production", "fr_occ_regional"), (
            "FR CNC + OCC regional pair missing"
        )

    def test_uk_devolved_avec_pairs_exist(self):
        devolved_slugs = [
            "gb_scot_creative_scotland",
            "gb_wls_creative_wales",
            "gb_nir_northern_ireland",
            "gb_yrk_screen_yorkshire",
        ]
        for slug in devolved_slugs:
            assert self._pair_exists(slug, "uk_avec"), (
                f"{slug} + uk_avec pair missing from _SLUG_PAIR_RULES"
            )
            assert self._pair_rule_type(slug, "uk_avec") == "allowed", (
                f"{slug} + uk_avec should be allowed"
            )


# ---------------------------------------------------------------------------
# Migration 0047 static integrity checks
# ---------------------------------------------------------------------------

class TestMigration0047Schema:
    """Validate that migration 0047 module is importable and well-formed."""

    def test_revision_chain(self):
        mod = _load_migration("0047_treaty_coproduction_schema.py")
        assert mod.revision == "0047"
        assert mod.down_revision == "0046"


# ---------------------------------------------------------------------------
# Migration 0048 static integrity checks
# ---------------------------------------------------------------------------

class TestMigration0048BilateralTreaties:
    """Validate static data in migration 0048 (bilateral treaty seed)."""

    @pytest.fixture(scope="class")
    def treaties(self):
        return _load_migration("0048_seed_bilateral_treaties.py")._TREATIES

    def test_revision_chain(self):
        mod = _load_migration("0048_seed_bilateral_treaties.py")
        assert mod.revision == "0048"
        assert mod.down_revision == "0047"

    def test_at_least_20_bilateral_treaties(self, treaties):
        assert len(treaties) >= 20, (
            f"Expected at least 20 bilateral treaties, got {len(treaties)}"
        )

    def test_all_treaties_have_required_fields(self, treaties):
        required = {"treaty_name", "treaty_slug", "treaty_type", "status",
                    "jurisdiction_a_code", "confidence_tier"}
        for t in treaties:
            for field in required:
                assert field in t and t[field], (
                    f"Treaty {t.get('treaty_slug', '?')} missing required field: {field}"
                )

    def test_all_slugs_unique(self, treaties):
        slugs = [t["treaty_slug"] for t in treaties]
        assert len(slugs) == len(set(slugs)), (
            f"Duplicate treaty slugs found: {[s for s in slugs if slugs.count(s) > 1]}"
        )

    def test_all_treaties_are_bilateral_type(self, treaties):
        for t in treaties:
            assert t["treaty_type"] == "bilateral", (
                f"Treaty {t['treaty_slug']} has type {t['treaty_type']}, expected bilateral"
            )

    def test_bilateral_treaties_have_both_jurisdiction_codes(self, treaties):
        for t in treaties:
            assert t.get("jurisdiction_a_code"), (
                f"Treaty {t['treaty_slug']} missing jurisdiction_a_code"
            )
            assert t.get("jurisdiction_b_code"), (
                f"Treaty {t['treaty_slug']} missing jurisdiction_b_code"
            )

    def test_contribution_pcts_are_reasonable(self, treaties):
        for t in treaties:
            maj = t.get("majority_min_contribution_pct")
            mn = t.get("minority_min_contribution_pct")
            if maj is not None:
                assert float(maj) >= 10.0, (
                    f"Treaty {t['treaty_slug']}: majority_min_contribution_pct < 10%"
                )
            if mn is not None:
                assert float(mn) >= 10.0, (
                    f"Treaty {t['treaty_slug']}: minority_min_contribution_pct < 10%"
                )

    def test_uk_ca_bilateral_present(self, treaties):
        slugs = {t["treaty_slug"] for t in treaties}
        assert "uk-ca-bilateral" in slugs

    def test_uk_ie_bilateral_present(self, treaties):
        slugs = {t["treaty_slug"] for t in treaties}
        assert "uk-ie-bilateral" in slugs

    def test_ca_fr_bilateral_present(self, treaties):
        slugs = {t["treaty_slug"] for t in treaties}
        assert "ca-fr-bilateral" in slugs

    def test_fr_de_bilateral_present(self, treaties):
        slugs = {t["treaty_slug"] for t in treaties}
        assert "fr-de-bilateral" in slugs


# ---------------------------------------------------------------------------
# Migration 0049 static integrity checks
# ---------------------------------------------------------------------------

class TestMigration0049MultilateralTreaties:
    """Validate static data in migration 0049 (multilateral treaties + structures)."""

    @pytest.fixture(scope="class")
    def mod(self):
        return _load_migration("0049_seed_multilateral_treaties_and_structures.py")

    def test_revision_chain(self, mod):
        assert mod.revision == "0049"
        assert mod.down_revision == "0048"

    def test_three_multilateral_treaties(self, mod):
        assert len(mod._MULTILATERAL_TREATIES) == 3

    def test_eurimages_slug(self, mod):
        slugs = {t["treaty_slug"] for t in mod._MULTILATERAL_TREATIES}
        assert "eurimages-multilateral" in slugs

    def test_european_convention_slug(self, mod):
        slugs = {t["treaty_slug"] for t in mod._MULTILATERAL_TREATIES}
        assert "european-convention-coproduction" in slugs

    def test_ibermedia_slug(self, mod):
        slugs = {t["treaty_slug"] for t in mod._MULTILATERAL_TREATIES}
        assert "ibermedia-multilateral" in slugs

    def test_eurimages_members_count(self, mod):
        assert len(mod._EURIMAGES_MEMBERS) >= 40, (
            f"Expected ≥40 Eurimages members, got {len(mod._EURIMAGES_MEMBERS)}"
        )

    def test_ibermedia_members_count(self, mod):
        assert len(mod._IBERMEDIA_MEMBERS) >= 20, (
            f"Expected ≥20 Ibermedia members, got {len(mod._IBERMEDIA_MEMBERS)}"
        )

    def test_eurimages_gb_member(self, mod):
        codes = {code for code, _ in mod._EURIMAGES_MEMBERS}
        assert "GB" in codes, "UK (GB) should be a Eurimages member"

    def test_eurimages_de_member(self, mod):
        codes = {code for code, _ in mod._EURIMAGES_MEMBERS}
        assert "DE" in codes, "Germany (DE) should be a Eurimages member"

    def test_ibermedia_br_member(self, mod):
        codes = {code for code, _ in mod._IBERMEDIA_MEMBERS}
        assert "BR" in codes, "Brazil should be an Ibermedia member"

    def test_ibermedia_es_member(self, mod):
        codes = {code for code, _ in mod._IBERMEDIA_MEMBERS}
        assert "ES" in codes, "Spain should be an Ibermedia member"

    def test_at_least_10_structures(self, mod):
        assert len(mod._STRUCTURES) >= 10, (
            f"Expected ≥10 co-production structures, got {len(mod._STRUCTURES)}"
        )

    def test_all_structure_slugs_unique(self, mod):
        slugs = [s["structure_slug"] for s in mod._STRUCTURES]
        assert len(slugs) == len(set(slugs)), (
            f"Duplicate structure slugs: {[s for s in slugs if slugs.count(s) > 1]}"
        )

    def test_all_structures_reference_known_treaty_slugs(self, mod):
        m48 = _load_migration("0048_seed_bilateral_treaties.py")
        bilateral_slugs = {t["treaty_slug"] for t in m48._TREATIES}
        multilateral_slugs = {t["treaty_slug"] for t in mod._MULTILATERAL_TREATIES}
        all_known = bilateral_slugs | multilateral_slugs

        for s in mod._STRUCTURES:
            ts = s.get("treaty_slug")
            assert ts in all_known, (
                f"Structure {s['structure_slug']} references unknown treaty_slug: {ts}"
            )

    def test_uk_ca_bilateral_structure_present(self, mod):
        slugs = {s["structure_slug"] for s in mod._STRUCTURES}
        assert "uk-ca-bilateral-uk-majority" in slugs

    def test_eurimages_trilateral_structure_present(self, mod):
        slugs = {s["structure_slug"] for s in mod._STRUCTURES}
        assert "eurimages-trilateral-standard" in slugs

    def test_uk_ie_structure_present(self, mod):
        slugs = {s["structure_slug"] for s in mod._STRUCTURES}
        assert "uk-ie-bilateral-uk-majority" in slugs


# ---------------------------------------------------------------------------
# Migration chain continuity
# ---------------------------------------------------------------------------

class TestMigrationChain:
    """Verify down_revision chain 0047→0052 is unbroken."""

    def test_0047_down_revision(self):
        assert _load_migration("0047_treaty_coproduction_schema.py").down_revision == "0046"

    def test_0048_down_revision(self):
        assert _load_migration("0048_seed_bilateral_treaties.py").down_revision == "0047"

    def test_0049_down_revision(self):
        assert _load_migration("0049_seed_multilateral_treaties_and_structures.py").down_revision == "0048"

    def test_0050_down_revision(self):
        assert _load_migration("0050_seed_phase_c_regional_funds.py").down_revision == "0049"

    def test_0051_down_revision(self):
        assert _load_migration("0051_phase_d_fund_economics_completion.py").down_revision == "0050"

    def test_0052_down_revision(self):
        assert _load_migration("0052_phase_d5_stacking_graph_expansion.py").down_revision == "0051"
