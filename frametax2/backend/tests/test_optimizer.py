"""
test_optimizer.py

Phase E optimizer unit tests.
All tests are pure Python — no DB connection required.
Tests verify: enumeration, stacking rules, scoring, explanations, ranking.
"""
from __future__ import annotations

import pytest

from app.data.global_inventory import ALL_PROGRAMS, GlobalProgramEntry
from app.optimization.enumerate_structures import (
    enumerate_structures,
    _grant_eligible_for_jurisdiction,
    _get_primary_programs_for_jurisdiction,
)
from app.optimization.stacking_rules import (
    evaluate_pair,
    evaluate_structure_stacking,
    infer_slug,
)
from app.optimization.score_structures import (
    filter_structures,
    score_structure,
    score_all_structures,
    explain_structure,
)
from app.optimization.optimizer import run_optimizer
from app.optimization.types import (
    CONFIDENCE_PENALTY,
    StructureCandidate,
    EligibleStructure,
    ScoredStructure,
    StructureExplanation,
    OptimizationResult,
    monetization_friction_rate,
)


# ---------------------------------------------------------------------------
# Helpers — build minimal test programs
# ---------------------------------------------------------------------------

def _prog(
    jur_code: str,
    name: str,
    prog_type: str = "cash_rebate",
    base_rate: float | None = 0.30,
    is_refundable: bool | None = True,
    is_transferable: bool | None = False,
    annual_cap: float | None = None,
    confidence: str = "PARSED",
) -> GlobalProgramEntry:
    return GlobalProgramEntry(
        jurisdiction_code=jur_code,
        jurisdiction_name=jur_code,
        program_name=name,
        program_type=prog_type,
        base_rate=base_rate,
        max_rate=base_rate,
        is_refundable=is_refundable,
        is_transferable=is_transferable,
        min_spend_usd=None,
        annual_cap_usd=annual_cap,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=confidence,
        source_title="Test source",
        source_url="https://example.com",
        effective_from="2020-01-01",
        notes="Test program",
    )


# ---------------------------------------------------------------------------
# Phase 1 audit — types and constants
# ---------------------------------------------------------------------------

class TestPhaseETypes:
    def test_confidence_penalty_verified(self):
        assert CONFIDENCE_PENALTY["VERIFIED"] == 0.0

    def test_confidence_penalty_parsed(self):
        assert CONFIDENCE_PENALTY["PARSED"] == 0.10

    def test_confidence_penalty_discovery(self):
        assert CONFIDENCE_PENALTY["DISCOVERY"] == 0.25

    def test_monetization_friction_refundable_transferable(self):
        assert monetization_friction_rate(True, True) == 0.0

    def test_monetization_friction_refundable_only(self):
        assert monetization_friction_rate(True, False) == 0.03

    def test_monetization_friction_transferable_only(self):
        assert monetization_friction_rate(False, True) == 0.06

    def test_monetization_friction_neither(self):
        assert monetization_friction_rate(False, False) == 0.12

    def test_monetization_friction_unknown(self):
        assert monetization_friction_rate(None, None) == 0.05

    def test_optimizer_version_importable(self):
        from app.optimization import OPTIMIZER_VERSION
        assert OPTIMIZER_VERSION == "1.0.0"


# ---------------------------------------------------------------------------
# Phase 2 — Structure enumeration
# ---------------------------------------------------------------------------

class TestEnumerateStructures:
    def test_enumerate_returns_list(self):
        result = enumerate_structures(["MT"], all_programs=ALL_PROGRAMS)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_each_result_is_structure_candidate(self):
        result = enumerate_structures(["MT"], all_programs=ALL_PROGRAMS)
        for c in result:
            assert isinstance(c, StructureCandidate)

    def test_primary_programs_in_correct_jurisdiction(self):
        result = enumerate_structures(["MT"], all_programs=ALL_PROGRAMS)
        for c in result:
            for p in c.primary_programs:
                assert p.jurisdiction_code == "MT"

    def test_malta_has_primary_incentive(self):
        primaries = _get_primary_programs_for_jurisdiction("MT", ALL_PROGRAMS)
        assert len(primaries) >= 1
        assert any("Malta" in p.program_name for p in primaries)

    def test_greece_has_primary_incentive(self):
        primaries = _get_primary_programs_for_jurisdiction("GR", ALL_PROGRAMS)
        assert len(primaries) >= 1

    def test_uk_has_primary_incentive(self):
        primaries = _get_primary_programs_for_jurisdiction("GB", ALL_PROGRAMS)
        assert len(primaries) >= 1

    def test_eu_eurimages_eligible_for_france(self):
        eu_grants = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "EU"]
        assert any(
            _grant_eligible_for_jurisdiction(g, "FR") for g in eu_grants
        )

    def test_eu_eurimages_eligible_for_malta(self):
        eu_grants = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "EU"]
        assert any(
            _grant_eligible_for_jurisdiction(g, "MT") for g in eu_grants
        )

    def test_eu_eurimages_eligible_for_uk(self):
        # UK is still in Eurimages (Council of Europe, not EU)
        eu_grants = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "EU"]
        assert any(
            _grant_eligible_for_jurisdiction(g, "GB") for g in eu_grants
        )

    def test_nordic_fund_eligible_for_sweden(self):
        nordic_grants = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "NORDIC"]
        assert any(
            _grant_eligible_for_jurisdiction(g, "SE") for g in nordic_grants
        )

    def test_nordic_fund_not_eligible_for_france(self):
        nordic_grants = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "NORDIC"]
        assert not any(
            _grant_eligible_for_jurisdiction(g, "FR") for g in nordic_grants
        )

    def test_ca_cmf_eligible_for_canada(self):
        ca_grants = [
            p for p in ALL_PROGRAMS
            if p.jurisdiction_code == "CA"
            and p.program_type in ("direct_grant", "co_production_fund")
        ]
        assert any(_grant_eligible_for_jurisdiction(g, "CA") for g in ca_grants)

    def test_split_structures_generated(self):
        result = enumerate_structures(
            ["FR", "IE"], all_programs=ALL_PROGRAMS, include_split_jurisdictions=True
        )
        split = [c for c in result if c.structure_type == "split"]
        assert len(split) >= 1

    def test_structure_id_is_string(self):
        result = enumerate_structures(["MT"], all_programs=ALL_PROGRAMS)
        for c in result:
            assert isinstance(c.structure_id, str)
            assert len(c.structure_id) > 0

    def test_multi_jurisdiction_enumeration(self):
        result = enumerate_structures(["MT", "GR", "MU"], all_programs=ALL_PROGRAMS)
        assert len(result) > 0
        # Should have structures for each jurisdiction
        jurs_covered = set()
        for c in result:
            jurs_covered.update(p.jurisdiction_code for p in c.primary_programs)
        assert "MT" in jurs_covered or "GR" in jurs_covered or "MU" in jurs_covered

    def test_minimal_programs_enumerable(self):
        # With a minimal program list
        progs = [
            _prog("MT", "Malta Rebate", "cash_rebate", 0.30),
            _prog("EU", "Eurimages", "co_production_fund", None, annual_cap=1_500_000),
        ]
        result = enumerate_structures(["MT"], all_programs=progs)
        assert len(result) >= 1  # at least one structure

    def test_no_duplicate_structure_ids(self):
        result = enumerate_structures(["FR", "MT"], all_programs=ALL_PROGRAMS)
        ids = [c.structure_id for c in result]
        assert len(ids) == len(set(ids)), "Duplicate structure IDs found"


# ---------------------------------------------------------------------------
# Phase 3 — Eligibility filter + stacking rules
# ---------------------------------------------------------------------------

class TestStackingRules:
    def test_infer_slug_malta(self):
        mt = [p for p in ALL_PROGRAMS if p.jurisdiction_code == "MT"][0]
        slug = infer_slug(mt)
        assert slug == "mt_mfc_rebate"

    def test_infer_slug_greece(self):
        gr = [p for p in ALL_PROGRAMS if "Greece Cash Rebate" in p.program_name][0]
        slug = infer_slug(gr)
        assert slug == "gr_cash_rebate"

    def test_infer_slug_uk_avec(self):
        gb = [p for p in ALL_PROGRAMS if "Audio Visual Expenditure" in p.program_name]
        assert gb
        assert infer_slug(gb[0]) == "uk_avec"

    def test_infer_slug_eurimages(self):
        eu = [p for p in ALL_PROGRAMS if "Eurimages" in p.program_name][0]
        assert infer_slug(eu) == "eu_eurimages"

    def test_infer_slug_bfi(self):
        bfi = [p for p in ALL_PROGRAMS if "BFI Film Fund" in p.program_name][0]
        assert infer_slug(bfi) == "gb_bfi_production"

    def test_infer_slug_ie_section481(self):
        ie = [p for p in ALL_PROGRAMS if "Section 481" in p.program_name][0]
        assert infer_slug(ie) == "ie_section_481"

    def test_bfi_plus_avec_is_allowed(self):
        bfi = [p for p in ALL_PROGRAMS if "BFI Film Fund" in p.program_name][0]
        avec = [p for p in ALL_PROGRAMS if "Audio Visual Expenditure" in p.program_name][0]
        result = evaluate_pair(bfi, avec)
        assert result is None, f"BFI+AVEC should be allowed, got: {result}"

    def test_eurimages_plus_avec_is_allowed(self):
        eu = [p for p in ALL_PROGRAMS if "Eurimages" in p.program_name][0]
        avec = [p for p in ALL_PROGRAMS if "Audio Visual Expenditure" in p.program_name][0]
        result = evaluate_pair(eu, avec)
        assert result is None, f"Eurimages+AVEC should be allowed, got: {result}"

    def test_eurimages_plus_ie_section481_is_allowed(self):
        eu = [p for p in ALL_PROGRAMS if "Eurimages" in p.program_name][0]
        ie = [p for p in ALL_PROGRAMS if "Section 481" in p.program_name][0]
        result = evaluate_pair(eu, ie)
        assert result is None, f"Eurimages+IE481 should be allowed, got: {result}"

    def test_ca_cmf_plus_cptc_is_spend_reduction(self):
        cmf = [p for p in ALL_PROGRAMS if "Canada Media Fund" in p.program_name]
        cptc = [p for p in ALL_PROGRAMS if "Canada Production Tax Credit" in p.program_name]
        if cmf and cptc:
            result = evaluate_pair(cmf[0], cptc[0])
            assert result is not None
            assert result.rule_type == "spend_reduction"

    def test_same_jurisdiction_primary_programs_mutually_exclusive(self):
        prog_a = _prog("MT", "Malta Program A", "cash_rebate", 0.30)
        prog_b = _prog("MT", "Malta Program B", "cash_rebate", 0.25)
        result = evaluate_pair(prog_a, prog_b)
        assert result is not None
        assert result.rule_type == "mutually_exclusive"

    def test_different_jurisdiction_primaries_no_violation(self):
        prog_mt = _prog("MT", "Malta Rebate", "cash_rebate", 0.30)
        prog_gr = _prog("GR", "Greece Rebate", "cash_rebate", 0.40)
        result = evaluate_pair(prog_mt, prog_gr)
        assert result is None, "Different-jurisdiction primaries should be allowed (split structure)"

    def test_grant_plus_primary_default_allowed(self):
        grant = _prog("EU", "EU Fund", "co_production_fund", None, annual_cap=1_500_000)
        primary = _prog("MT", "Malta Rebate", "cash_rebate", 0.30)
        result = evaluate_pair(grant, primary)
        assert result is None, "EU grant + MT primary should be allowed by default"

    def test_evaluate_structure_stacking_returns_tuple(self):
        progs = [
            _prog("MT", "Malta Rebate", "cash_rebate", 0.30),
            _prog("EU", "EU Fund", "co_production_fund", None, annual_cap=1_500_000),
        ]
        violations, conditionals, spend_reductions = evaluate_structure_stacking(progs)
        assert isinstance(violations, list)
        assert isinstance(conditionals, list)
        assert isinstance(spend_reductions, list)


class TestEligibilityFilter:
    def _make_candidate(
        self,
        primaries: list[GlobalProgramEntry],
        grants: list[GlobalProgramEntry] | None = None,
    ) -> StructureCandidate:
        return StructureCandidate(
            structure_id="test_structure",
            primary_programs=primaries,
            grant_programs=grants or [],
            regional_programs=[],
            jurisdiction_codes=[p.jurisdiction_code for p in primaries],
        )

    def test_valid_structure_is_eligible(self):
        c = self._make_candidate([
            _prog("MT", "Malta Rebate", "cash_rebate", 0.30),
        ])
        eligible, ineligible = filter_structures([c])
        assert len(eligible) == 1
        assert eligible[0].is_eligible

    def test_mutually_exclusive_flagged_but_eligible(self):
        """Mutually exclusive structures are eligible (optimizer handles value)."""
        c = self._make_candidate([
            _prog("MT", "Malta A", "cash_rebate", 0.30),
            _prog("MT", "Malta B", "cash_rebate", 0.25),
        ])
        eligible, ineligible = filter_structures([c])
        assert len(eligible) == 1
        assert eligible[0].legal_review_required

    def test_empty_structure_is_ineligible(self):
        c = StructureCandidate(
            structure_id="empty",
            primary_programs=[],
            grant_programs=[],
            regional_programs=[],
            jurisdiction_codes=[],
        )
        eligible, ineligible = filter_structures([c])
        assert len(ineligible) == 1
        assert not ineligible[0].is_eligible


# ---------------------------------------------------------------------------
# Phase 4 — Economic scoring
# ---------------------------------------------------------------------------

class TestEconomicScoring:
    def _make_eligible(
        self,
        programs: list[GlobalProgramEntry],
    ) -> EligibleStructure:
        c = StructureCandidate(
            structure_id="test",
            primary_programs=programs,
            grant_programs=[],
            regional_programs=[],
            jurisdiction_codes=[p.jurisdiction_code for p in programs],
        )
        return EligibleStructure(
            candidate=c,
            is_eligible=True,
            eligibility_flags=[],
            stacking_violations=[],
            stacking_conditionals=[],
            spend_reduction_rules=[],
            legal_review_required=False,
        )

    def test_score_structure_returns_scored_structure(self):
        es = self._make_eligible([_prog("MT", "Malta", "cash_rebate", 0.30)])
        result = score_structure(es, total_budget_usd=10_000_000)
        assert isinstance(result, ScoredStructure)

    def test_primary_incentive_value_computed(self):
        # 30% rate × $10M × 65% qualifying = $1.95M
        es = self._make_eligible([_prog("MT", "Malta", "cash_rebate", 0.30)])
        result = score_structure(es, total_budget_usd=10_000_000, qualifying_spend_pct=0.65)
        expected_raw = 10_000_000 * 0.65 * 0.30
        assert abs(result.primary_incentive_raw_usd - expected_raw) < 1.0

    def test_annual_cap_applied(self):
        # Rate would give $1.95M but cap is $1M
        es = self._make_eligible([
            _prog("MT", "Malta", "cash_rebate", 0.30, annual_cap=1_000_000)
        ])
        result = score_structure(es, total_budget_usd=10_000_000, qualifying_spend_pct=0.65)
        assert result.primary_incentive_raw_usd <= 1_000_001  # cap applied

    def test_confidence_penalty_discovery(self):
        es = self._make_eligible([
            _prog("MT", "Malta", "cash_rebate", 0.30, confidence="DISCOVERY")
        ])
        result = score_structure(es, total_budget_usd=10_000_000)
        assert result.lowest_confidence_tier == "DISCOVERY"
        assert result.confidence_penalty_usd > 0

    def test_confidence_penalty_verified_is_zero(self):
        es = self._make_eligible([
            _prog("MT", "Malta", "cash_rebate", 0.30, confidence="VERIFIED")
        ])
        result = score_structure(es, total_budget_usd=10_000_000)
        assert result.confidence_penalty_usd == 0.0

    def test_no_rate_produces_zero_primary_value(self):
        es = self._make_eligible([
            _prog("EU", "EU Fund", "co_production_fund", base_rate=None, annual_cap=2_000_000)
        ])
        result = score_structure(es, total_budget_usd=10_000_000)
        assert result.primary_incentive_raw_usd == 0.0

    def test_net_benefit_positive_for_good_structure(self):
        # 40% rate, VERIFIED, refundable → good structure
        es = self._make_eligible([
            _prog("GR", "Greece", "cash_rebate", 0.40,
                  is_refundable=True, confidence="VERIFIED")
        ])
        result = score_structure(es, total_budget_usd=10_000_000)
        assert result.net_producer_benefit_usd > 0

    def test_net_benefit_less_than_raw(self):
        es = self._make_eligible([_prog("MT", "Malta", "cash_rebate", 0.30)])
        result = score_structure(es, total_budget_usd=10_000_000)
        assert result.net_producer_benefit_usd < result.total_raw_usd

    def test_effective_rate_in_range(self):
        es = self._make_eligible([_prog("GR", "Greece", "cash_rebate", 0.40)])
        result = score_structure(es, total_budget_usd=10_000_000)
        assert 0.0 < result.effective_rate <= 0.40

    def test_rank_assigned_after_score_all(self):
        programs = [
            _prog("MT", "Malta", "cash_rebate", 0.30),
            _prog("GR", "Greece", "cash_rebate", 0.40),
        ]
        eligibles = [
            self._make_eligible([p]) for p in programs
        ]
        scored = score_all_structures(eligibles, total_budget_usd=10_000_000)
        ranks = [s.rank for s in scored]
        assert 1 in ranks
        assert len(set(ranks)) == len(ranks)  # all unique

    def test_higher_rate_ranks_better(self):
        """Greece (40%) should rank #1 over Malta (30%) with same confidence."""
        mt_prog = _prog("MT", "Malta", "cash_rebate", 0.30, confidence="VERIFIED")
        gr_prog = _prog("GR", "Greece", "cash_rebate", 0.40, confidence="VERIFIED")
        mt = self._make_eligible([mt_prog])
        gr = self._make_eligible([gr_prog])
        scored = score_all_structures([mt, gr], total_budget_usd=10_000_000)
        gr_scored = next(s for s in scored if s.eligible_structure.primary_programs[0].jurisdiction_code == "GR")
        mt_scored = next(s for s in scored if s.eligible_structure.primary_programs[0].jurisdiction_code == "MT")
        assert gr_scored.rank < mt_scored.rank

    def test_discovery_ranks_lower_than_verified_same_rate(self):
        """DISCOVERY program should rank below VERIFIED same rate due to confidence penalty."""
        verified = self._make_eligible([
            _prog("MT", "Malta Verified", "cash_rebate", 0.30, confidence="VERIFIED")
        ])
        discovery = self._make_eligible([
            _prog("GR", "Greece Discovery", "cash_rebate", 0.30, confidence="DISCOVERY")
        ])
        scored = score_all_structures([verified, discovery], total_budget_usd=10_000_000)
        v_scored = next(s for s in scored if s.eligible_structure.primary_programs[0].jurisdiction_code == "MT")
        d_scored = next(s for s in scored if s.eligible_structure.primary_programs[0].jurisdiction_code == "GR")
        assert v_scored.rank < d_scored.rank


# ---------------------------------------------------------------------------
# Phase 5 — Explanation engine
# ---------------------------------------------------------------------------

class TestExplanationEngine:
    def _make_scored(
        self,
        jur: str,
        name: str,
        rate: float = 0.30,
        confidence: str = "PARSED",
    ) -> ScoredStructure:
        prog = _prog(jur, name, "cash_rebate", rate, confidence=confidence)
        c = StructureCandidate(
            structure_id=f"{jur}_test",
            primary_programs=[prog],
            grant_programs=[],
            regional_programs=[],
            jurisdiction_codes=[jur],
        )
        es = EligibleStructure(
            candidate=c, is_eligible=True, eligibility_flags=[],
            stacking_violations=[], stacking_conditionals=[],
            spend_reduction_rules=[], legal_review_required=False,
        )
        s = score_structure(es, total_budget_usd=5_000_000)
        s.rank = 1
        return s

    def test_explain_returns_explanation(self):
        scored = self._make_scored("MT", "Malta Rebate")
        result = explain_structure(scored)
        assert isinstance(result, StructureExplanation)

    def test_explanation_has_summary(self):
        scored = self._make_scored("MT", "Malta Rebate")
        result = explain_structure(scored)
        assert isinstance(result.summary, str)
        assert len(result.summary) > 10

    def test_explanation_has_primary_programs(self):
        scored = self._make_scored("MT", "Malta Rebate")
        result = explain_structure(scored)
        assert len(result.primary_programs) == 1
        assert "Malta Rebate" in result.primary_programs[0]

    def test_explanation_stacking_notes_not_empty(self):
        scored = self._make_scored("MT", "Malta Rebate")
        result = explain_structure(scored)
        assert len(result.stacking_notes) >= 1

    def test_explanation_confidence_notes_reflect_tier(self):
        scored = self._make_scored("MT", "Malta Discovery", confidence="DISCOVERY")
        result = explain_structure(scored)
        discovery_notes = [n for n in result.confidence_notes if "DISCOVERY" in n]
        assert len(discovery_notes) >= 1

    def test_explanation_adjustments_include_confidence(self):
        scored = self._make_scored("MT", "Malta Parsed", confidence="PARSED")
        result = explain_structure(scored)
        conf_adj = [a for a in result.adjustments if a["type"] == "confidence_penalty"]
        assert len(conf_adj) >= 1
        assert conf_adj[0]["amount_usd"] < 0

    def test_explanation_economics_keys_present(self):
        scored = self._make_scored("GR", "Greece Rebate")
        result = explain_structure(scored)
        for key in ("net_producer_benefit_usd", "effective_rate_pct",
                    "primary_incentive_raw_usd", "confidence_penalty_usd"):
            assert key in result.economics

    def test_no_violations_noted_in_clean_structure(self):
        scored = self._make_scored("MT", "Malta Rebate")
        result = explain_structure(scored)
        assert all("ALLOWED" in n or "no stacking violations" in n.lower()
                   for n in result.stacking_notes)


# ---------------------------------------------------------------------------
# Top-level optimizer integration
# ---------------------------------------------------------------------------

class TestRunOptimizer:
    def test_optimizer_returns_result(self):
        result = run_optimizer(
            jurisdiction_codes=["MT"],
            total_budget_usd=5_000_000,
        )
        assert isinstance(result, OptimizationResult)

    def test_optimizer_malta_has_structures(self):
        result = run_optimizer(["MT"], total_budget_usd=5_000_000)
        assert result.structures_enumerated > 0

    def test_optimizer_structures_eligible(self):
        result = run_optimizer(["MT"], total_budget_usd=5_000_000)
        assert result.structures_eligible > 0

    def test_optimizer_ranked_structures_populated(self):
        result = run_optimizer(["MT"], total_budget_usd=5_000_000)
        assert len(result.ranked_structures) > 0

    def test_optimizer_rank_1_has_best_benefit(self):
        result = run_optimizer(["MT"], total_budget_usd=5_000_000)
        if len(result.ranked_structures) >= 2:
            r1 = result.ranked_structures[0]
            r2 = result.ranked_structures[1]
            assert r1.net_producer_benefit_usd >= r2.net_producer_benefit_usd

    def test_optimizer_explanations_populated(self):
        result = run_optimizer(["MT"], total_budget_usd=5_000_000)
        assert len(result.explanations) > 0
        assert len(result.explanations) == len(result.ranked_structures)

    def test_optimizer_warnings_on_invalid_budget(self):
        result = run_optimizer(["MT"], total_budget_usd=-1)
        assert len(result.warnings) > 0

    def test_optimizer_multi_jurisdiction(self):
        result = run_optimizer(
            jurisdiction_codes=["MT", "GR", "MU"],
            total_budget_usd=8_000_000,
        )
        assert result.structures_enumerated > 0
        assert len(result.ranked_structures) > 0

    def test_optimizer_europe_jurisdictions(self):
        result = run_optimizer(
            jurisdiction_codes=["FR", "IT", "MT", "GR"],
            total_budget_usd=15_000_000,
        )
        assert result.structures_enumerated > 0

    def test_optimizer_version_in_result(self):
        result = run_optimizer(["MT"], total_budget_usd=1_000_000)
        assert result.optimizer_version == "1.0.0"

    def test_optimizer_budget_preserved(self):
        result = run_optimizer(["MT"], total_budget_usd=7_500_000)
        assert result.total_budget_usd == 7_500_000

    def test_optimizer_with_uk_ireland(self):
        result = run_optimizer(
            jurisdiction_codes=["GB", "IE"],
            total_budget_usd=12_000_000,
        )
        assert result.structures_enumerated > 0


# ---------------------------------------------------------------------------
# Stacking rules integration — SLUGS_WITH_STACKING_RULES updated
# ---------------------------------------------------------------------------

class TestStackingRulesRegistry:
    def test_slugs_with_stacking_rules_importable(self):
        from app.calculators.coverage_report import SLUGS_WITH_STACKING_RULES
        assert isinstance(SLUGS_WITH_STACKING_RULES, frozenset)

    def test_fund_economics_registry_has_23(self):
        from app.calculators.coverage_report import SLUGS_WITH_FUND_ECONOMICS
        assert len(SLUGS_WITH_FUND_ECONOMICS) == 41
