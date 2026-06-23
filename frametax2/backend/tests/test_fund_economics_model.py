"""
test_fund_economics_model.py — Phase E4: fund economics model tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.data.fund_economics_model import (
    FundEconomicsEntry,
    get_fund_economics,
    get_typical_max_usd,
    is_government_assistance,
    is_soft_money,
    list_all_slugs,
)


# ---------------------------------------------------------------------------
# Registry coverage
# ---------------------------------------------------------------------------

class TestRegistryCoverage:
    def test_registry_has_at_least_20_programs(self):
        slugs = list_all_slugs()
        assert len(slugs) >= 20, f"Expected ≥20 entries, got {len(slugs)}"

    def test_eurimages_registered(self):
        assert get_fund_economics("eu_eurimages") is not None

    def test_cmf_registered(self):
        assert get_fund_economics("ca_cmf") is not None

    def test_bfi_registered(self):
        assert get_fund_economics("gb_bfi_production") is not None

    def test_screen_australia_registered(self):
        assert get_fund_economics("au_screen_production") is not None

    def test_wallimage_registered(self):
        assert get_fund_economics("be_wal_wallimage") is not None

    def test_vaf_registered(self):
        assert get_fund_economics("be_vlg_vaf") is not None

    def test_nordmedia_registered(self):
        assert get_fund_economics("de_ni_nordmedia") is not None

    def test_nohfc_registered(self):
        assert get_fund_economics("nohfc_production_fund") is not None

    def test_fff_bayern_registered(self):
        assert get_fund_economics("de_fff_bayern") is not None

    def test_unknown_slug_returns_none(self):
        assert get_fund_economics("nonexistent_slug_xyz") is None


# ---------------------------------------------------------------------------
# Government assistance classification
# ---------------------------------------------------------------------------

class TestGovernmentAssistance:
    def test_cmf_is_government_assistance(self):
        assert is_government_assistance("ca_cmf") is True

    def test_telefilm_is_government_assistance(self):
        assert is_government_assistance("ca_telefilm_dev") is True

    def test_nohfc_is_government_assistance(self):
        assert is_government_assistance("nohfc_production_fund") is True

    def test_screen_australia_is_government_assistance(self):
        assert is_government_assistance("au_screen_production") is True

    def test_screenwest_is_government_assistance(self):
        assert is_government_assistance("au_screenwest") is True

    def test_bfi_is_not_government_assistance(self):
        assert is_government_assistance("gb_bfi_production") is False

    def test_eurimages_is_not_government_assistance(self):
        assert is_government_assistance("eu_eurimages") is False

    def test_creative_scotland_is_not_government_assistance(self):
        assert is_government_assistance("gb_scot_creative_scotland") is False

    def test_northern_ireland_screen_is_not_government_assistance(self):
        assert is_government_assistance("gb_nir_northern_ireland") is False

    def test_wallimage_is_not_government_assistance(self):
        assert is_government_assistance("be_wal_wallimage") is False

    def test_fff_bayern_is_not_government_assistance(self):
        assert is_government_assistance("de_fff_bayern") is False


# ---------------------------------------------------------------------------
# Soft money classification
# ---------------------------------------------------------------------------

class TestSoftMoneyClassification:
    def test_eurimages_is_soft_money(self):
        assert is_soft_money("eu_eurimages") is True

    def test_ibermedia_is_soft_money(self):
        assert is_soft_money("ibermedia_programme") is True

    def test_nohfc_is_soft_money(self):
        assert is_soft_money("nohfc_production_fund") is True

    def test_fr_regional_idf_is_soft_money(self):
        assert is_soft_money("fr_idf_regional") is True

    def test_cmf_is_not_soft_money(self):
        assert is_soft_money("ca_cmf") is False

    def test_screen_australia_is_not_soft_money(self):
        assert is_soft_money("au_screen_production") is False

    def test_bfi_is_not_soft_money(self):
        assert is_soft_money("gb_bfi_production") is False


# ---------------------------------------------------------------------------
# Recoupment / repayability
# ---------------------------------------------------------------------------

class TestRecoupmentStructure:
    def test_cmf_is_recoupable(self):
        e = get_fund_economics("ca_cmf")
        assert e.is_recoupable is True

    def test_cmf_pari_passu_recoupment(self):
        e = get_fund_economics("ca_cmf")
        assert e.recoupment_position == "pari_passu"

    def test_eurimages_subordinated_recoupment(self):
        e = get_fund_economics("eu_eurimages")
        assert e.is_recoupable is True
        assert e.recoupment_position == "subordinated"

    def test_bfi_is_repayable(self):
        e = get_fund_economics("gb_bfi_production")
        assert e.is_repayable is True

    def test_nohfc_is_not_repayable(self):
        e = get_fund_economics("nohfc_production_fund")
        assert e.is_repayable is False

    def test_ibermedia_not_repayable(self):
        e = get_fund_economics("ibermedia_programme")
        assert e.is_repayable is False

    def test_nordmedia_subordinated_recoupment(self):
        e = get_fund_economics("de_ni_nordmedia")
        assert e.is_recoupable is True
        assert e.recoupment_position == "subordinated"


# ---------------------------------------------------------------------------
# Equity participation
# ---------------------------------------------------------------------------

class TestEquityParticipation:
    def test_cmf_has_equity(self):
        e = get_fund_economics("ca_cmf")
        assert e.has_equity_participation is True

    def test_bfi_has_equity(self):
        e = get_fund_economics("gb_bfi_production")
        assert e.has_equity_participation is True

    def test_nohfc_no_equity(self):
        e = get_fund_economics("nohfc_production_fund")
        assert e.has_equity_participation is False

    def test_eurimages_no_equity(self):
        e = get_fund_economics("eu_eurimages")
        assert e.has_equity_participation is False

    def test_nordmedia_no_equity(self):
        e = get_fund_economics("de_ni_nordmedia")
        assert e.has_equity_participation is False


# ---------------------------------------------------------------------------
# Typical max awards
# ---------------------------------------------------------------------------

class TestTypicalMaxAwards:
    def test_eurimages_max_award(self):
        max_usd = get_typical_max_usd("eu_eurimages")
        assert max_usd is not None
        assert max_usd >= 1_000_000

    def test_cmf_max_award(self):
        max_usd = get_typical_max_usd("ca_cmf")
        assert max_usd is not None
        assert max_usd >= 1_000_000

    def test_ibermedia_max_award(self):
        max_usd = get_typical_max_usd("ibermedia_programme")
        assert max_usd is not None
        assert max_usd >= 100_000

    def test_unknown_slug_max_award_none(self):
        assert get_typical_max_usd("nonexistent_xyz") is None


# ---------------------------------------------------------------------------
# Classification completeness
# ---------------------------------------------------------------------------

class TestClassificationCompleteness:
    _VALID_CLASSIFICATIONS = {
        "grant", "loan", "equity", "advance", "tax_credit", "rebate", "tax_shelter"
    }

    def test_all_entries_have_valid_classification(self):
        for slug in list_all_slugs():
            e = get_fund_economics(slug)
            assert e.classification in self._VALID_CLASSIFICATIONS, (
                f"{slug}: unexpected classification '{e.classification}'"
            )

    def test_all_entries_have_stackable_flag(self):
        for slug in list_all_slugs():
            e = get_fund_economics(slug)
            assert isinstance(e.stackable_with_incentives, bool), (
                f"{slug}: stackable_with_incentives must be bool"
            )

    def test_all_stackable_with_incentives(self):
        for slug in list_all_slugs():
            e = get_fund_economics(slug)
            assert e.stackable_with_incentives is True, (
                f"{slug}: expected stackable_with_incentives=True"
            )
