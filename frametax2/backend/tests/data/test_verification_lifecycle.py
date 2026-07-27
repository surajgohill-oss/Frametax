from __future__ import annotations

"""Verification lifecycle + structured Unknown reason codes.

Engineering rules pinned here (Database Completion phase, 2026-07-26):

  1. "Treat Requirements Profile completion and Evidence Verification as
      separate lifecycle states... Do not represent secondary-source
      information as primary verified."

  2. "Continue recording genuine Unknowns only when justified by evidence.
      Use explicit reason codes... rather than generic UNKNOWN."

The failure mode these guard against is a populated-but-secondary profile
silently reading as authoritative, and an unexplained Unknown creeping in
without an auditable justification.
"""

import pytest

from app.data.program_requirements import (
    UNKNOWN_FIELD_REGISTER,
    SourceType,
    UnknownReasonCode,
    VerificationState,
    _REGISTRY,
    all_unknown_fields_by_reason_code,
    get_unknown_fields,
    profiles_awaiting_primary_verification,
    verification_state,
    verification_summary,
)


class TestVerificationLifecycle:
    def test_every_registered_profile_has_a_lifecycle_state(self):
        for slug in _REGISTRY:
            assert isinstance(verification_state(slug), VerificationState)

    def test_no_registered_profile_is_unverified(self):
        """Every profile carries an EvidenceRecord — a registered profile with
        no evidence at all would be a schema-integrity failure."""
        assert verification_summary()["UNVERIFIED"] == 0

    def test_lifecycle_state_matches_the_underlying_evidence_tier(self):
        """The lifecycle state must be derived from evidence, never asserted
        independently — otherwise the two can silently diverge."""
        for slug, profile in _REGISTRY.items():
            expected = (
                VerificationState.PRIMARY_VERIFIED
                if profile.evidence.source_type == SourceType.PRIMARY
                else VerificationState.SECONDARY_VERIFIED
            )
            assert verification_state(slug) is expected, slug

    def test_summary_counts_sum_to_registry_size(self):
        assert sum(verification_summary().values()) == len(_REGISTRY)

    def test_backlog_lists_exactly_the_secondary_profiles(self):
        backlog = set(profiles_awaiting_primary_verification())
        secondary = {
            slug for slug in _REGISTRY
            if verification_state(slug) is VerificationState.SECONDARY_VERIFIED
        }
        assert backlog == secondary

    def test_known_secondary_profiles_are_not_claimed_as_primary(self):
        """Spot-check the profiles explicitly marked SECONDARY in their own
        evidence notes because the administrator's guidance was not retrieved.

        dk_production_rebate was upgraded to PRIMARY_VERIFIED during the
        Stage B verification sprint (2026-07-26, direct fetch of
        slks.dk) and removed from this list; ch_pics_national_rebate
        substituted in as a still-genuinely-SECONDARY profile (three
        direct primary-source fetch attempts this same session all
        returned 404 or landed on generic pages -- see its evidence
        notes)."""
        for slug in ("ch_pics_national_rebate", "se_production_rebate",
                     "sg_made_with_singapore_rebate", "ae_dxb_dpip"):
            assert verification_state(slug) is VerificationState.SECONDARY_VERIFIED, slug

    def test_directly_fetched_profiles_are_primary(self):
        """ca_bc_pstc was fetched from the Province of BC page directly;
        us_tx_miip from the Texas Governor's office pages."""
        for slug in ("ca_bc_pstc", "us_tx_miip", "za_dtic_foreign_film"):
            assert verification_state(slug) is VerificationState.PRIMARY_VERIFIED, slug


class TestUnknownReasonCodes:
    def test_every_unknown_carries_a_valid_reason_code(self):
        valid = {c.value for c in UnknownReasonCode}
        for slug, fields in UNKNOWN_FIELD_REGISTER.items():
            for field, rec in fields.items():
                assert rec["reason_code"] in valid, f"{slug}.{field}"

    def test_generic_unknown_is_prohibited(self):
        for slug, fields in UNKNOWN_FIELD_REGISTER.items():
            for field, rec in fields.items():
                assert rec["reason_code"] != "UNKNOWN", f"{slug}.{field}"

    def test_every_unknown_documents_authority_documents_and_rationale(self):
        """An Unknown without documented search evidence is indistinguishable
        from a conservative assumption, which the doctrine forbids."""
        for slug, fields in UNKNOWN_FIELD_REGISTER.items():
            for field, rec in fields.items():
                for key in ("authority_searched", "documents_reviewed", "why_undeterminable"):
                    assert rec.get(key), f"{slug}.{field} missing {key}"
                    assert len(rec[key]) > 30, f"{slug}.{field} {key} too thin to be real evidence"

    def test_unknowns_only_recorded_for_registered_programs(self):
        for slug in UNKNOWN_FIELD_REGISTER:
            assert slug in _REGISTRY, slug

    def test_unknown_fields_are_actually_unset_on_the_profile(self):
        """An Unknown must correspond to a field that really is None. If the
        field is populated, the Unknown entry is stale and misleading."""
        field_map = {
            "min_local_spend": "min_local_spend_usd",
            "min_total_budget": "min_total_budget_usd",
            "per_project_cap": "per_project_cap_usd",
            "annual_program_cap": "annual_program_cap_usd",
            "application_deadline": "application_deadline",
        }
        for slug, fields in UNKNOWN_FIELD_REGISTER.items():
            profile = _REGISTRY[slug]
            for field in fields:
                attr = field_map.get(field)
                if attr:
                    assert getattr(profile, attr) is None, (
                        f"{slug}.{field} is recorded Unknown but {attr} is populated"
                    )

    def test_get_unknown_fields_returns_empty_for_clean_program(self):
        assert get_unknown_fields("us_tx_miip") == {}
        assert get_unknown_fields("no_such_slug") == {}

    def test_reason_code_index_covers_every_registered_unknown(self):
        indexed = sum(len(v) for v in all_unknown_fields_by_reason_code().values())
        total = sum(len(f) for f in UNKNOWN_FIELD_REGISTER.values())
        assert indexed == total


class TestDisclosureOnlyGuarantee:
    def test_lifecycle_helpers_are_not_consumed_by_pricing(self):
        import pathlib

        backend = pathlib.Path(__file__).resolve().parents[2]
        for rel in (
            "app/calculators/allocation_pricing.py",
            "app/calculators/qualification_derivation.py",
            "app/calculators/production_allocation.py",
            "app/data/program_rate_rules.py",
        ):
            p = backend / rel
            if p.exists():
                text = p.read_text()
                assert "verification_state" not in text, rel
                assert "UNKNOWN_FIELD_REGISTER" not in text, rel
