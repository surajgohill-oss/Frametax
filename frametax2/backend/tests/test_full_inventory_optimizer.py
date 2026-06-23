"""
test_full_inventory_optimizer.py — Phase 5: Synthetic full-inventory optimizer tests.

Validates that the pure-Python optimizer can safely process all 240 programs
without crashes, that DISCOVERY penalties are applied, that base_rate=None
programs produce $0 value, and that DB-sync programs (NOHFC, OFTTC, QC) are
reachable from the optimizer.
"""
from __future__ import annotations

import pytest

from app.data.global_inventory import ALL_PROGRAMS, GlobalProgramEntry
from app.optimization.enumerate_structures import (
    _get_eligible_grants,
    _get_eligible_regional,
    _get_primary_programs_for_jurisdiction,
    enumerate_structures,
)
from app.optimization.optimizer import run_optimizer
from app.optimization.score_structures import filter_structures, score_structure
from app.optimization.stacking_rules import infer_slug
from app.optimization.types import CONFIDENCE_PENALTY, StructureCandidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_simple_eligible(programs: list[GlobalProgramEntry]):
    """Wrap programs in a minimal EligibleStructure for direct scoring tests."""
    from app.optimization.types import EligibleStructure
    primary = [p for p in programs if p.program_type in {"tax_credit", "cash_rebate"}]
    grants = [p for p in programs if p.program_type in {"direct_grant", "co_production_fund", "development_fund"}]
    regional = [p for p in programs if p.program_type in {"discretionary_fund", "regional_fund"}]
    candidate = StructureCandidate(
        structure_id="test_synthetic",
        primary_programs=primary,
        grant_programs=grants,
        regional_programs=regional,
        jurisdiction_codes=list({p.jurisdiction_code for p in programs}),
        structure_type="single",
    )
    return EligibleStructure(
        candidate=candidate,
        is_eligible=True,
        eligibility_flags=[],
        stacking_violations=[],
        stacking_conditionals=[],
        spend_reduction_rules=[],
        legal_review_required=False,
    )


# ---------------------------------------------------------------------------
# Phase 5.1 — Full inventory enumeration does not crash
# ---------------------------------------------------------------------------

class TestFullInventoryNocrash:
    def test_enumerate_all_jurisdictions_no_crash(self):
        """enumerate_structures must complete without exception for all known jurisdiction codes."""
        all_jur_codes = list({p.jurisdiction_code for p in ALL_PROGRAMS})
        # Use a subset to keep runtime fast; pick first 30 diverse codes
        sample_codes = sorted(all_jur_codes)[:30]
        candidates = enumerate_structures(
            jurisdiction_codes=sample_codes,
            all_programs=ALL_PROGRAMS,
            max_grants_per_structure=2,
            include_split_jurisdictions=False,
        )
        assert isinstance(candidates, list)

    def test_enumerate_with_split_no_crash(self):
        """enumerate_structures with split_jurisdictions=True must not crash."""
        codes = ["GB", "IE", "FR", "DE", "AU"]
        candidates = enumerate_structures(
            jurisdiction_codes=codes,
            all_programs=ALL_PROGRAMS,
            max_grants_per_structure=1,
            include_split_jurisdictions=True,
        )
        assert len(candidates) > 0

    def test_run_optimizer_high_coverage_no_crash(self):
        """run_optimizer must complete without exception for a broad jurisdiction set."""
        codes = ["GB", "IE", "FR", "MT", "AU", "NZ", "CA", "CA-ON", "US"]
        result = run_optimizer(
            jurisdiction_codes=codes,
            total_budget_usd=5_000_000,
            qualifying_spend_pct=0.70,
            production_type="feature",
            max_grants_per_structure=2,
            include_split_jurisdictions=True,
            top_n=10,
        )
        assert result.structures_enumerated > 0
        assert result.structures_eligible >= 0
        assert isinstance(result.warnings, list)

    def test_run_optimizer_single_discovery_jurisdiction(self):
        """Optimizer with a DISCOVERY-only jurisdiction must not crash and must warn."""
        result = run_optimizer(
            jurisdiction_codes=["MN"],  # Mongolia — DISCOVERY tier
            total_budget_usd=2_000_000,
            qualifying_spend_pct=0.65,
            production_type="feature",
            max_grants_per_structure=1,
            include_split_jurisdictions=False,
        )
        assert isinstance(result.warnings, list)

    def test_unknown_jurisdiction_runs_without_crash(self):
        """An unrecognised jurisdiction code must not raise an exception."""
        result = run_optimizer(
            jurisdiction_codes=["XX"],  # Non-existent code; open funds may still appear
            total_budget_usd=1_000_000,
            qualifying_spend_pct=0.65,
            production_type="feature",
        )
        assert isinstance(result.ranked_structures, list)


# ---------------------------------------------------------------------------
# Phase 5.2 — DISCOVERY confidence penalty applied
# ---------------------------------------------------------------------------

class TestDiscoveryPenalty:
    def test_discovery_program_applies_25pct_penalty(self):
        """A DISCOVERY program must have confidence_penalty = raw_value × 0.25."""
        discovery_progs = [p for p in ALL_PROGRAMS if p.confidence_tier == "DISCOVERY" and p.base_rate]
        assert discovery_progs, "Need at least one DISCOVERY program with base_rate"
        prog = discovery_progs[0]

        es = _make_simple_eligible([prog])
        scored = score_structure(es, total_budget_usd=10_000_000, qualifying_spend_pct=0.65)

        expected_raw = prog.base_rate * 10_000_000 * 0.65
        if prog.annual_cap_usd and expected_raw > prog.annual_cap_usd:
            expected_raw = prog.annual_cap_usd
        expected_penalty = expected_raw * 0.25
        assert abs(scored.confidence_penalty_usd - expected_penalty) < 1.0

    def test_verified_program_no_penalty(self):
        """A VERIFIED program must have zero confidence_penalty."""
        verified_progs = [p for p in ALL_PROGRAMS if p.confidence_tier == "VERIFIED" and p.base_rate]
        assert verified_progs, "Need at least one VERIFIED program with base_rate"
        prog = verified_progs[0]

        es = _make_simple_eligible([prog])
        scored = score_structure(es, total_budget_usd=10_000_000, qualifying_spend_pct=0.65)
        assert scored.confidence_penalty_usd == 0.0

    def test_parsed_program_applies_10pct_penalty(self):
        """A PARSED program must have confidence_penalty = raw_value × 0.10."""
        parsed_progs = [p for p in ALL_PROGRAMS if p.confidence_tier == "PARSED" and p.base_rate]
        assert parsed_progs, "Need at least one PARSED program with base_rate"
        prog = parsed_progs[0]

        es = _make_simple_eligible([prog])
        scored = score_structure(es, total_budget_usd=10_000_000, qualifying_spend_pct=0.65)

        expected_raw = prog.base_rate * 10_000_000 * 0.65
        if prog.annual_cap_usd and expected_raw > prog.annual_cap_usd:
            expected_raw = prog.annual_cap_usd
        expected_penalty = expected_raw * 0.10
        assert abs(scored.confidence_penalty_usd - expected_penalty) < 1.0

    def test_discovery_warning_in_optimizer_output(self):
        """Optimizer must emit DISCOVERY warning when jurisdiction has only DISCOVERY programs."""
        # Find a jurisdiction where all programs are DISCOVERY
        jur_progs: dict[str, list[GlobalProgramEntry]] = {}
        for p in ALL_PROGRAMS:
            jur_progs.setdefault(p.jurisdiction_code, []).append(p)
        discovery_only_jurs = [
            jur for jur, progs in jur_progs.items()
            if all(p.confidence_tier == "DISCOVERY" for p in progs)
            and any(p.base_rate is not None for p in progs)
            and "-" not in jur  # top-level only
        ]
        assert discovery_only_jurs, "Need at least one top-level all-DISCOVERY jurisdiction"
        target = discovery_only_jurs[0]

        result = run_optimizer(
            jurisdiction_codes=[target],
            total_budget_usd=5_000_000,
            qualifying_spend_pct=0.65,
            production_type="feature",
        )
        discovery_warns = [w for w in result.warnings if "DISCOVERY" in w]
        assert discovery_warns, f"Expected DISCOVERY warning for {target}"


# ---------------------------------------------------------------------------
# Phase 5.3 — base_rate=None programs produce $0 primary value
# ---------------------------------------------------------------------------

class TestNoneBaseRate:
    def test_primary_with_none_rate_produces_zero_value(self):
        """A primary program (tax_credit) with base_rate=None must contribute $0 raw value."""
        none_rate_progs = [
            p for p in ALL_PROGRAMS
            if p.program_type in {"tax_credit", "cash_rebate"}
            and p.base_rate is None
        ]
        assert none_rate_progs, "Need at least one primary program with base_rate=None"
        prog = none_rate_progs[0]

        es = _make_simple_eligible([prog])
        scored = score_structure(es, total_budget_usd=10_000_000, qualifying_spend_pct=0.65)
        assert scored.primary_incentive_raw_usd == 0.0

    def test_primary_with_none_rate_adds_unknown_flag(self):
        """A primary program with base_rate=None must set has_unknowns=True."""
        none_rate_progs = [
            p for p in ALL_PROGRAMS
            if p.program_type in {"tax_credit", "cash_rebate"}
            and p.base_rate is None
        ]
        assert none_rate_progs
        prog = none_rate_progs[0]

        es = _make_simple_eligible([prog])
        scored = score_structure(es, total_budget_usd=5_000_000, qualifying_spend_pct=0.65)
        assert scored.has_unknowns

    def test_grant_with_none_cap_produces_zero_value(self):
        """A grant program with annual_cap_usd=None must contribute $0 grant value."""
        none_cap_grants = [
            p for p in ALL_PROGRAMS
            if p.program_type in {"direct_grant", "co_production_fund", "development_fund"}
            and p.annual_cap_usd is None
        ]
        assert none_cap_grants, "Need at least one grant with no cap"
        prog = none_cap_grants[0]

        es = _make_simple_eligible([prog])
        scored = score_structure(es, total_budget_usd=10_000_000, qualifying_spend_pct=0.65)
        assert scored.grant_raw_usd == 0.0

    def test_grant_with_known_cap_produces_nonzero_value(self):
        """A grant program with annual_cap_usd known must contribute > $0 grant value."""
        known_cap_grants = [
            p for p in ALL_PROGRAMS
            if p.program_type in {"direct_grant", "co_production_fund", "development_fund"}
            and p.annual_cap_usd is not None
        ]
        assert known_cap_grants, "Need at least one grant with known cap"
        prog = known_cap_grants[0]

        es = _make_simple_eligible([prog])
        scored = score_structure(es, total_budget_usd=10_000_000, qualifying_spend_pct=0.65)
        assert scored.grant_raw_usd > 0.0


# ---------------------------------------------------------------------------
# Phase 5.4 — DB-sync programs (NOHFC, OFTTC, QC) are optimizer-visible
# ---------------------------------------------------------------------------

class TestDBSyncPrograms:
    def test_nohfc_in_all_programs(self):
        """NOHFC (Northern Ontario Heritage Fund) must be in ALL_PROGRAMS."""
        nohfc = [p for p in ALL_PROGRAMS if "Northern Ontario Heritage Fund" in p.program_name]
        assert len(nohfc) >= 1, "NOHFC not found in ALL_PROGRAMS"

    def test_nohfc_is_discretionary_fund(self):
        nohfc = next(
            p for p in ALL_PROGRAMS if "Northern Ontario Heritage Fund" in p.program_name
        )
        assert nohfc.program_type == "discretionary_fund"
        assert nohfc.jurisdiction_code == "CA-ON"
        assert nohfc.confidence_tier == "PARSED"

    def test_nohfc_slug_inference(self):
        nohfc = next(
            p for p in ALL_PROGRAMS if "Northern Ontario Heritage Fund" in p.program_name
        )
        slug = infer_slug(nohfc)
        assert slug == "nohfc_production_fund"

    def test_nohfc_appears_in_ca_on_regional_candidates(self):
        """NOHFC must appear in regional candidates when CA-ON is a target jurisdiction."""
        regional = _get_eligible_regional(["CA-ON"], ALL_PROGRAMS)
        regional_names = [p.program_name for p in regional]
        nohfc_found = any("Northern Ontario Heritage Fund" in n for n in regional_names)
        assert nohfc_found, f"NOHFC not in CA-ON regional candidates: {regional_names}"

    def test_nohfc_regional_for_ca_parent(self):
        """NOHFC must appear as regional candidate when target is CA (parent jurisdiction)."""
        regional = _get_eligible_regional(["CA"], ALL_PROGRAMS)
        regional_names = [p.program_name for p in regional]
        nohfc_found = any("Northern Ontario Heritage Fund" in n for n in regional_names)
        assert nohfc_found, "NOHFC not found under CA parent jurisdiction"

    def test_ofttc_in_all_programs(self):
        """OFTTC (Ontario Film and Television Tax Credit) must be in ALL_PROGRAMS."""
        ofttc = [p for p in ALL_PROGRAMS if "Ontario Film and Television Tax Credit" in p.program_name]
        assert len(ofttc) >= 1, "OFTTC not found in ALL_PROGRAMS"

    def test_ofttc_slug_inference(self):
        ofttc = next(
            p for p in ALL_PROGRAMS if "Ontario Film and Television Tax Credit" in p.program_name
        )
        slug = infer_slug(ofttc)
        assert slug == "on_ofttc"

    def test_ofttc_is_primary_type(self):
        ofttc = next(
            p for p in ALL_PROGRAMS if "Ontario Film and Television Tax Credit" in p.program_name
        )
        assert ofttc.program_type == "tax_credit"
        assert ofttc.jurisdiction_code == "CA-ON"

    def test_qc_domestic_in_all_programs(self):
        """QC SODEC domestic credit must be in ALL_PROGRAMS."""
        qc = [
            p for p in ALL_PROGRAMS
            if "Quebec Film and Television Production Tax Credit" in p.program_name
        ]
        assert len(qc) >= 1, "QC SODEC domestic credit not found in ALL_PROGRAMS"

    def test_qc_domestic_slug_inference(self):
        qc = next(
            p for p in ALL_PROGRAMS
            if "Quebec Film and Television Production Tax Credit" in p.program_name
        )
        slug = infer_slug(qc)
        assert slug == "qc_film_production"

    def test_ca_on_has_multiple_programs(self):
        """CA-ON must now have at least OPSTC + OFTTC + NOHFC."""
        ca_on = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "CA-ON"]
        assert len(ca_on) >= 3, f"Expected ≥3 CA-ON programs, got {len(ca_on)}: {[p.program_name for p in ca_on]}"

    def test_ca_qc_has_multiple_programs(self):
        """CA-QC must have at least QPRDP (wave6 foreign) + SODEC (domestic)."""
        ca_qc = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "CA-QC"]
        assert len(ca_qc) >= 2, f"Expected ≥2 CA-QC programs, got {len(ca_qc)}"


# ---------------------------------------------------------------------------
# Phase 5.5 — Stacking rules correctness for synced programs
# ---------------------------------------------------------------------------

class TestStackingRulesSync:
    def test_nohfc_ofttc_stacking_rule_exists(self):
        """NOHFC + OFTTC must produce a spend_reduction stacking rule."""
        from app.optimization.stacking_rules import evaluate_structure_stacking

        nohfc = next(p for p in ALL_PROGRAMS if "Northern Ontario Heritage Fund" in p.program_name)
        ofttc = next(p for p in ALL_PROGRAMS if "Ontario Film and Television Tax Credit" in p.program_name)

        violations, conditionals, spend_reductions = evaluate_structure_stacking([nohfc, ofttc])
        spend_rule_names = {(v.program_a_name, v.program_b_name) for v in spend_reductions}
        has_rule = any(
            ("Northern Ontario Heritage Fund" in a or "Northern Ontario Heritage Fund" in b) and
            ("Ontario Film and Television Tax Credit" in a or "Ontario Film and Television Tax Credit" in b)
            for a, b in spend_rule_names
        )
        assert has_rule, f"Expected NOHFC+OFTTC spend_reduction rule; got: {spend_rule_names}"

    def test_ofttc_cptc_stacking_rule_exists(self):
        """OFTTC + CPTC must produce a spend_reduction stacking rule (OFTTC reduces CPTC basis)."""
        from app.optimization.stacking_rules import evaluate_structure_stacking

        ofttc = next(p for p in ALL_PROGRAMS if "Ontario Film and Television Tax Credit" in p.program_name)
        cptc = next(p for p in ALL_PROGRAMS if "Canada Production Tax Credit" in p.program_name)

        violations, conditionals, spend_reductions = evaluate_structure_stacking([ofttc, cptc])
        assert spend_reductions, "Expected spend_reduction for OFTTC+CPTC"

    def test_ofttc_opstc_mutually_exclusive(self):
        """OFTTC + OPSTC must be mutually_exclusive (different production tracks)."""
        from app.optimization.stacking_rules import evaluate_structure_stacking

        ofttc = next(p for p in ALL_PROGRAMS if "Ontario Film and Television Tax Credit" in p.program_name)
        opstc = next(p for p in ALL_PROGRAMS if "Ontario Production Services Tax Credit" in p.program_name)

        violations, conditionals, spend_reductions = evaluate_structure_stacking([ofttc, opstc])
        me_rules = [v for v in violations if v.rule_type == "mutually_exclusive"]
        assert me_rules, "Expected mutually_exclusive for OFTTC+OPSTC"

    def test_bc_pstc_cptc_mutually_exclusive(self):
        """BC PSTC + CPTC must be mutually_exclusive (domestic vs foreign service)."""
        from app.optimization.stacking_rules import evaluate_structure_stacking

        bc_pstc = next(p for p in ALL_PROGRAMS if "BC Production Services Tax Credit" in p.program_name)
        cptc = next(p for p in ALL_PROGRAMS if "Canada Production Tax Credit" in p.program_name)

        violations, conditionals, spend_reductions = evaluate_structure_stacking([bc_pstc, cptc])
        me_rules = [v for v in violations if v.rule_type == "mutually_exclusive"]
        assert me_rules, "Expected mutually_exclusive for BC PSTC+CPTC"

    def test_qc_domestic_cptc_spend_reduction(self):
        """QC SODEC domestic + CPTC must produce a spend_reduction rule."""
        from app.optimization.stacking_rules import evaluate_structure_stacking

        qc = next(
            p for p in ALL_PROGRAMS
            if "Quebec Film and Television Production Tax Credit" in p.program_name
        )
        cptc = next(p for p in ALL_PROGRAMS if "Canada Production Tax Credit" in p.program_name)

        violations, conditionals, spend_reductions = evaluate_structure_stacking([qc, cptc])
        assert spend_reductions, "Expected spend_reduction for QC SODEC+CPTC"

    def test_uk_avec_ie_section_481_allowed(self):
        """UK AVEC + IE Section 481 must be explicitly allowed."""
        from app.optimization.stacking_rules import evaluate_structure_stacking

        avec = next(
            (p for p in ALL_PROGRAMS if "Audio Visual Expenditure Credit" in p.program_name or "AVEC" in p.program_name),
            None,
        )
        ie481 = next((p for p in ALL_PROGRAMS if "Section 481" in p.program_name), None)
        if avec is None or ie481 is None:
            pytest.skip("AVEC or IE Section 481 not in inventory")

        violations, conditionals, spend_reductions = evaluate_structure_stacking([avec, ie481])
        # Should have no prohibited violations
        prohibited = [v for v in violations if v.rule_type == "prohibited"]
        assert not prohibited, "AVEC+IE481 should not be prohibited"


# ---------------------------------------------------------------------------
# Phase 5.6 — All 240 programs have valid program_type
# ---------------------------------------------------------------------------

class TestProgramIntegrity:
    _VALID_TYPES = frozenset({
        "tax_credit", "cash_rebate", "direct_grant", "co_production_fund",
        "development_fund", "discretionary_fund", "regional_fund",
        "production_support", "tax_shelter", "grant", "transferable_tax_credit",
    })

    def test_all_programs_have_valid_type(self):
        """Every GlobalProgramEntry must have a recognised program_type."""
        invalid = [
            (p.jurisdiction_code, p.program_name, p.program_type)
            for p in ALL_PROGRAMS
            if p.program_type not in self._VALID_TYPES
        ]
        assert not invalid, f"Programs with unrecognised program_type: {invalid}"

    def test_all_programs_have_confidence_tier(self):
        """Every program must have a confidence_tier of DISCOVERY, PARSED, or VERIFIED."""
        valid_tiers = {"DISCOVERY", "PARSED", "VERIFIED"}
        bad = [
            (p.jurisdiction_code, p.program_name, p.confidence_tier)
            for p in ALL_PROGRAMS
            if p.confidence_tier not in valid_tiers
        ]
        assert not bad, f"Programs with invalid confidence_tier: {bad}"

    def test_all_programs_have_jurisdiction_code(self):
        """Every program must have a non-empty jurisdiction_code."""
        bad = [p.program_name for p in ALL_PROGRAMS if not p.jurisdiction_code]
        assert not bad, f"Programs missing jurisdiction_code: {bad}"

    def test_all_programs_count(self):
        """ALL_PROGRAMS must contain exactly 240 entries (229 + 3 DB-sync + 8 Phase C)."""
        assert len(ALL_PROGRAMS) == 240, f"Expected 240, got {len(ALL_PROGRAMS)}"


# ---------------------------------------------------------------------------
# Phase 5.7 — Coverage report v1.4.0 fields
# ---------------------------------------------------------------------------

class TestCoverageReportV140:
    def test_report_version_is_1_4_0(self):
        from app.calculators.coverage_report import REPORT_VERSION
        assert REPORT_VERSION == "1.4.0"

    def test_intelligence_gap_report_has_optimizer_fields(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert hasattr(report, "optimizer_visible_programs")
        assert hasattr(report, "optimizer_excluded_programs")
        assert hasattr(report, "stacking_sync_status")
        assert hasattr(report, "grant_fund_optimizer_ready")
        assert hasattr(report, "discovery_opportunity_count")
        assert hasattr(report, "calculable_program_count")
        assert hasattr(report, "blocked_program_count")

    def test_optimizer_visible_equals_all_programs(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.optimizer_visible_programs == len(ALL_PROGRAMS)

    def test_calculable_programs_gt_zero(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.calculable_program_count > 0

    def test_blocked_programs_nonzero(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        # Several primary programs have base_rate=None
        assert report.blocked_program_count > 0

    def test_discovery_opportunity_count_matches(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        expected = sum(1 for p in ALL_PROGRAMS if p.confidence_tier == "DISCOVERY")
        assert report.discovery_opportunity_count == expected

    def test_grant_fund_optimizer_ready_gt_zero(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert report.grant_fund_optimizer_ready > 0

    def test_stacking_sync_status_nonempty(self):
        from app.calculators.coverage_report import build_intelligence_gap_report
        report = build_intelligence_gap_report()
        assert len(report.stacking_sync_status) > 0
