from __future__ import annotations

"""Canonical currency rule (Database Completion phase, 2026-07-26).

"Store every statutory monetary value exactly as published by the governing
authority. The database is the legal source of truth. Do not normalize
statutory values into USD, EUR, or any other common currency during this
phase. Never replace or overwrite an authoritative local-currency value with
a converted value."

These tests pin the register that makes the rule auditable, and guard the two
ways it could silently rot: a program's authoritative original disappearing,
or a new profile quietly introducing a fresh FX conversion.
"""

import pytest

from app.data.program_requirements import (
    STATUTORY_AMOUNTS_ORIGINAL_CURRENCY,
    get_statutory_amounts,
    profiles_with_legacy_currency_conversions,
)


class TestRegisterIntegrity:
    def test_every_entry_records_amount_currency_basis_and_source(self):
        for slug, fields in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY.items():
            for name, rec in fields.items():
                assert isinstance(rec.get("amount"), (int, float)), f"{slug}.{name}"
                assert rec.get("currency"), f"{slug}.{name} missing currency"
                assert rec.get("basis"), f"{slug}.{name} missing basis"
                assert rec.get("source"), f"{slug}.{name} missing source"
                assert "effective_date" in rec, f"{slug}.{name} missing effective_date key"

    def test_currency_codes_are_iso_style_uppercase(self):
        for slug, fields in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY.items():
            for name, rec in fields.items():
                cur = rec["currency"]
                assert cur.isupper() and len(cur) == 3, f"{slug}.{name}: {cur!r}"

    def test_amounts_are_positive(self):
        for slug, fields in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY.items():
            for name, rec in fields.items():
                assert rec["amount"] > 0, f"{slug}.{name}"

    def test_get_statutory_amounts_returns_empty_for_unknown_program(self):
        assert get_statutory_amounts("no_such_program_slug") == {}


class TestLegacyConversionsAreDeclaredNotHidden:
    """A converted USD figure is permitted to REMAIN on a profile only if the
    authoritative original is recorded here and the conversion is explicitly
    flagged. Silent conversions are the thing the rule forbids."""

    def test_known_converted_programs_are_all_declared(self):
        legacy = profiles_with_legacy_currency_conversions()
        # Every program the audit found carrying a non-USD statutory amount
        # behind a USD field must appear here.
        expected = {
            "cy_film_rebate", "es_tax_credit_foreign", "hr_cash_rebate", "de_dfff",
            "it_tax_credit_foreign", "ie_section_481", "fr_trip", "ca_on_opstc",
            "mt_mfc_rebate", "gr_cash_rebate", "ma_ccm_rebate",
            "kr_kofic_location_incentive",
        }
        assert set(legacy) == expected

    def test_natively_usd_programs_are_not_flagged_as_conversions(self):
        """Mauritius and Israel publish in USD themselves — their USD values
        are authoritative, not conversions, and must not be mislabelled."""
        legacy = profiles_with_legacy_currency_conversions()
        assert "mu_edb_incentive" not in legacy
        assert "il_foreign_production_fund" not in legacy
        for slug in ("mu_edb_incentive", "il_foreign_production_fund"):
            for rec in get_statutory_amounts(slug).values():
                assert rec["currency"] == "USD"
                assert rec["legacy_usd_value"] is None

    @pytest.mark.parametrize("slug,field,amount,currency", [
        ("fr_trip", "min_local_spend", 250_000, "EUR"),
        ("fr_trip", "per_project_cap", 30_000_000, "EUR"),
        ("ca_on_opstc", "min_total_budget", 1_000_000, "CAD"),
        ("ma_ccm_rebate", "min_local_spend", 10_000_000, "MAD"),
        ("kr_kofic_location_incentive", "min_local_spend", 800_000_000, "KRW"),
        ("ie_section_481", "per_project_cap", 125_000_000, "EUR"),
    ])
    def test_authoritative_originals_are_exact(self, slug, field, amount, currency):
        rec = get_statutory_amounts(slug)[field]
        assert rec["amount"] == amount
        assert rec["currency"] == currency


class TestDisclosureOnlyGuarantee:
    def test_currency_register_is_not_consumed_by_any_pricing_path(self):
        """The register must stay disclosure-only. If a calculation module ever
        imports it, currency normalization has leaked into pricing — which this
        phase explicitly defers to the optimizer phase."""
        import pathlib

        backend = pathlib.Path(__file__).resolve().parents[2]
        pricing_paths = [
            backend / "app" / "calculators" / "allocation_pricing.py",
            backend / "app" / "calculators" / "qualification_derivation.py",
            backend / "app" / "calculators" / "production_allocation.py",
            backend / "app" / "data" / "program_rate_rules.py",
        ]
        for p in pricing_paths:
            if p.exists():
                assert "STATUTORY_AMOUNTS_ORIGINAL_CURRENCY" not in p.read_text(), p
