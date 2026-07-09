"""
test_qualification_model.py

Targeted tests for the CineAtlas qualification-state model.

Covers:
- ATL accounts are explicit GREY_AREA_REQUIRES_AUTHORITY, never silently
  collapsed to EXCLUDED
- Imported-crew accounts are STRUCTURING_OPPORTUNITY with a mechanism
- Deterministic exclusions remain EXCLUDED with correct authority basis
- Off-budget in-kind is never present in the register / never deducted
- Register reconciles exactly against the real fixture's gross budget
- Reinvestment UNKNOWN is distinct from NOT_PERMITTED
"""
from __future__ import annotations

import pytest

from app.calculators.qualification_model import (
    QUALIFICATION_MODEL_VERSION,
    AccountQualification,
    AuthorityBasis,
    GreyAreaStatus,
    LITTLE_UTOPIA_INKIND_FMV_USD,
    QualificationConfidence,
    QualificationState,
    REINVESTMENT_REGISTRY,
    ReinvestmentCategory,
    ReinvestmentProfile,
    apply_grey_area_resolution,
    build_little_utopia_evidence_graph,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
    get_reinvestment_profile,
    grey_area_terminus,
    resolve_grey_area,
    summarize_register,
)
from tests.fixtures.little_utopia_sanitized import GROSS_BUDGET_USD, computed_qpe


@pytest.fixture(scope="module")
def register() -> list[AccountQualification]:
    return build_little_utopia_qualification_register()


def _get(register, code) -> AccountQualification:
    matches = [a for a in register if a.account_code == code]
    assert matches, f"Account {code} not found in register"
    return matches[0]


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert QUALIFICATION_MODEL_VERSION == "1.0.0"

    def test_five_states(self):
        assert len(QualificationState) == 5
        names = {s.value for s in QualificationState}
        assert names == {
            "qualifies", "excluded", "structuring_opportunity",
            "grey_area_requires_authority", "not_applicable",
        }

    def test_seven_reinvestment_categories(self):
        assert len(ReinvestmentCategory) == 7


# ── ATL: unknown must not silently become excluded ──────────────────────────

class TestATLGreyArea:
    @pytest.mark.parametrize("code", ["10-00", "11-00", "12-00"])
    def test_state_is_grey_area_not_excluded(self, register, code):
        a = _get(register, code)
        assert a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY
        assert a.state != QualificationState.EXCLUDED

    @pytest.mark.parametrize("code", ["10-00", "11-00", "12-00"])
    def test_authority_basis_is_absence_not_fabricated(self, register, code):
        a = _get(register, code)
        assert a.authority_basis == AuthorityBasis.ABSENCE_OF_AUTHORITY

    @pytest.mark.parametrize("code", ["10-00", "11-00", "12-00"])
    def test_has_resolving_evidence_and_upside(self, register, code):
        a = _get(register, code)
        assert a.resolving_evidence is not None
        assert a.incentive_upside_usd == pytest.approx(a.amount_usd * 0.40, abs=0.01)

    def test_atl_grey_area_total(self, register):
        total = sum(_get(register, c).amount_usd for c in ["10-00", "11-00", "12-00"])
        assert total == pytest.approx(408_444.0, abs=0.01)


# ── Imported crew: structuring opportunity, not exclusion ───────────────────

class TestImportedCrewStructuring:
    @pytest.mark.parametrize("code", ["21-00", "23-00", "42-00"])
    def test_state_is_structuring_opportunity(self, register, code):
        a = _get(register, code)
        assert a.state == QualificationState.STRUCTURING_OPPORTUNITY
        assert a.state != QualificationState.EXCLUDED

    @pytest.mark.parametrize("code", ["21-00", "23-00", "42-00"])
    def test_authority_basis_is_structuring_dependent(self, register, code):
        a = _get(register, code)
        assert a.authority_basis == AuthorityBasis.STRUCTURING_DEPENDENT

    @pytest.mark.parametrize("code", ["21-00", "23-00", "42-00"])
    def test_has_mechanism_and_upside(self, register, code):
        a = _get(register, code)
        assert a.structuring_mechanism is not None
        assert "route" in a.structuring_mechanism.lower() or "rout" in a.structuring_mechanism.lower()
        assert a.incentive_upside_usd == pytest.approx(a.amount_usd * 0.40, abs=0.01)

    def test_structuring_opportunity_total(self, register):
        total = sum(_get(register, c).amount_usd for c in ["21-00", "23-00", "42-00"])
        assert total == pytest.approx(208_000.0, abs=0.01)
        upside = sum(_get(register, c).incentive_upside_usd for c in ["21-00", "23-00", "42-00"])
        assert upside == pytest.approx(83_200.0, abs=0.01)


# ── Deterministic exclusions remain excluded ─────────────────────────────────

class TestDeterministicExclusions:
    @pytest.mark.parametrize("code,basis", [
        ("39-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("50-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("51-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("52-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("53-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("54-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("55-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("60-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
        ("70-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
        ("71-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
        ("80-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
        ("81-00", AuthorityBasis.STRUCTURAL_DEFINITION),
        ("13-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
    ])
    def test_excluded_with_correct_basis(self, register, code, basis):
        a = _get(register, code)
        assert a.state == QualificationState.EXCLUDED
        assert a.authority_basis == basis

    def test_post_production_exclusion_total(self, register):
        total = sum(_get(register, c).amount_usd for c in ["50-00", "51-00", "52-00", "53-00", "54-00", "55-00"])
        assert total == pytest.approx(363_000.0, abs=0.01)

    def test_not_applicable_accounts(self, register):
        fc = _get(register, "82-00")
        assert fc.state == QualificationState.NOT_APPLICABLE
        assert fc.amount_usd == 0.0
        vat = _get(register, "44-00")
        assert vat.state == QualificationState.NOT_APPLICABLE
        assert vat.amount_usd == pytest.approx(92_439.0, abs=0.01)


# ── Off-budget in-kind: never in the register, never deducted ───────────────

class TestOffBudgetInkind:
    def test_inkind_amount_constant(self):
        assert LITTLE_UTOPIA_INKIND_FMV_USD == 625_000.0

    def test_inkind_not_present_as_any_account_code(self, register):
        assert not any(a.amount_usd == 625_000.0 for a in register)

    def test_inkind_not_double_counted_in_totals(self, register):
        summary = summarize_register(register)
        total_all_states = sum(summary["amounts_by_state"].values())
        # Register total must equal gross budget WITHOUT the in-kind figure —
        # in-kind is off-budget and must never inflate this sum.
        assert total_all_states == pytest.approx(GROSS_BUDGET_USD, abs=0.01)
        assert total_all_states != pytest.approx(GROSS_BUDGET_USD + LITTLE_UTOPIA_INKIND_FMV_USD, abs=0.01)


# ── Register reconciliation ──────────────────────────────────────────────────

class TestRegisterReconciliation:
    def test_register_covers_every_fixture_account(self, register):
        assert len(register) == 41  # 40 non-memo + 1 memo (44-00)

    def test_total_reconciles_to_gross_budget(self, register):
        total = sum(a.amount_usd for a in register)
        assert total == pytest.approx(GROSS_BUDGET_USD, abs=0.01)

    def test_qualifies_state_matches_calculator_base_scenario_minus_reclassified(self, register):
        """QUALIFIES-state accounts are the calculator's base-scenario qualifying
        set minus the three accounts reclassified as STRUCTURING_OPPORTUNITY
        (21-00, 23-00, 42-00 were base_qualifies=False in the calculator, so
        they were never part of base QPE — this just confirms no double count)."""
        qualifies_total = sum(a.amount_usd for a in register if a.state == QualificationState.QUALIFIES)
        assert qualifies_total == pytest.approx(computed_qpe("base"), abs=0.01)

    def test_no_account_appears_twice(self, register):
        codes = [a.account_code for a in register]
        assert len(codes) == len(set(codes))

    def test_summarize_register_states_sum_to_gross(self, register):
        summary = summarize_register(register)
        assert sum(summary["amounts_by_state"].values()) == pytest.approx(GROSS_BUDGET_USD, abs=0.01)


# ── Reinvestment: UNKNOWN distinct from NOT_PERMITTED ────────────────────────

class TestReinvestmentModel:
    def test_mu_profile_is_unknown(self):
        profile = get_reinvestment_profile("MU")
        assert profile.category == ReinvestmentCategory.UNKNOWN

    def test_unknown_is_not_not_permitted(self):
        assert ReinvestmentCategory.UNKNOWN != ReinvestmentCategory.NOT_PERMITTED
        profile = get_reinvestment_profile("MU")
        assert profile.category != ReinvestmentCategory.NOT_PERMITTED

    def test_mu_profile_has_no_fabricated_evidence(self):
        profile = get_reinvestment_profile("MU")
        assert profile.evidence is None
        assert "no reinvestment" in profile.notes.lower() or "absence" in profile.notes.lower()

    def test_unregistered_jurisdiction_defaults_to_unknown_not_not_permitted(self):
        profile = get_reinvestment_profile("ZZ")
        assert profile.category == ReinvestmentCategory.UNKNOWN
        assert profile.category != ReinvestmentCategory.NOT_PERMITTED

    def test_registry_contains_mu(self):
        assert "MU" in REINVESTMENT_REGISTRY
        assert isinstance(REINVESTMENT_REGISTRY["MU"], ReinvestmentProfile)


# ── P3: Grey Area / Evidence Graph migration ─────────────────────────────────

@pytest.fixture()
def grey_areas():
    return build_little_utopia_grey_areas()


@pytest.fixture()
def evidence_graph():
    return build_little_utopia_evidence_graph()


def _make_fully_chained_rule(graph, rule_id="R-ATL-RULING", jurisdiction_code="MU"):
    """Helper: seed `graph` with a real, fully-chained Rule and return its id."""
    from app.calculators.evidence_graph import AuthoritySource, AuthorityTier, Citation, Document, DocumentVersion, Evidence, Rule
    graph.add_document(Document(document_id="doc-ruling", jurisdiction_code=jurisdiction_code, title="EDB Ruling FRS-2026-0412"))
    graph.add_document_version(DocumentVersion(
        version_id="v-ruling", document_id="doc-ruling", version_label="2026",
        effective_date="2026-07-15", publication_date="2026-07-15",
    ))
    graph.add_authority_source(AuthoritySource(
        source_id="src-ruling", jurisdiction_code=jurisdiction_code, tier=AuthorityTier.BINDING_RULING,
        authority_body="Economic Development Board Mauritius", title="FRS-2026-0412",
        document_version_id="v-ruling",
    ))
    graph.add_rule(Rule(rule_id=rule_id, jurisdiction_code=jurisdiction_code, description="ATL fees qualify as QPE"))
    graph.add_citation(Citation(
        citation_id="cit-ruling", authority_source_id="src-ruling", document_version_id="v-ruling",
        pinpoint="para 3", citation_text="ATL fees paid through a Mauritius entity qualify as QPE.",
    ))
    graph.add_evidence(Evidence(evidence_id="ev-ruling", rule_id=rule_id, citation_id="cit-ruling", description="ruling"))
    return rule_id


class TestGreyAreaEvidenceGraphMigration:
    def test_atl_grey_area_links_to_absence_of_authority(self, grey_areas, evidence_graph):
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        assert atl.graph_absence_id == "ABS-ATL-SCOPE"
        assert grey_area_terminus(atl, evidence_graph) == "absence_of_authority"

    def test_inkind_grey_area_links_to_absence_of_authority(self, grey_areas, evidence_graph):
        inkind = next(g for g in grey_areas if g.item_id == "GA-INKIND-FMV")
        assert inkind.graph_absence_id == "ABS-INKIND-FMV"
        assert grey_area_terminus(inkind, evidence_graph) == "absence_of_authority"
        assert inkind.off_budget is True  # unaffected by the migration

    def test_absence_of_authority_actually_exists_in_graph(self, evidence_graph):
        # both referenced absence IDs must resolve to real nodes, not dangling strings
        assert evidence_graph.get_absence_of_authority("ABS-ATL-SCOPE").jurisdiction_code == "MU"
        assert evidence_graph.get_absence_of_authority("ABS-INKIND-FMV").jurisdiction_code == "MU"

    def test_unlinked_item_has_no_dead_end_disguised_as_resolved(self, evidence_graph):
        from app.calculators.qualification_model import GreyAreaItem
        orphan = GreyAreaItem(
            item_id="GA-ORPHAN", account_codes=(), amount_usd=1.0, jurisdiction_code="MU",
            authority_to_ask="nobody", resolving_evidence="nothing",
        )
        assert grey_area_terminus(orphan, evidence_graph) == "unlinked"

    def test_resolving_without_graph_evidence_still_requires_citation(self, grey_areas):
        """Legacy path (no graph): unchanged behavior — citation alone required."""
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        with pytest.raises(ValueError):
            resolve_grey_area(atl, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation=None)

    def test_resolving_with_graph_but_no_rule_id_fails(self, grey_areas, evidence_graph):
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        with pytest.raises(ValueError, match="resolving_rule_id"):
            resolve_grey_area(
                atl, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation="EDB-2026-0412",
                graph=evidence_graph, resolving_rule_id=None,
            )

    def test_resolving_with_unchained_rule_fails(self, grey_areas, evidence_graph):
        from app.calculators.evidence_graph import Rule
        evidence_graph.add_rule(Rule(rule_id="R-EMPTY", jurisdiction_code="MU", description="no evidence"))
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        with pytest.raises(ValueError, match="not fully chained"):
            resolve_grey_area(
                atl, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation="EDB-2026-0412",
                graph=evidence_graph, resolving_rule_id="R-EMPTY",
            )

    def test_resolving_with_fully_chained_rule_succeeds(self, grey_areas, evidence_graph):
        rule_id = _make_fully_chained_rule(evidence_graph)
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        resolved = resolve_grey_area(
            atl, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation="EDB-2026-0412",
            graph=evidence_graph, resolving_rule_id=rule_id,
        )
        assert resolved.status == GreyAreaStatus.RESOLVED_INCLUDE
        assert resolved.graph_rule_id == rule_id
        assert grey_area_terminus(resolved, evidence_graph) == "rule"
        assert atl.status == GreyAreaStatus.OPEN  # original untouched — pure function

    def test_resolved_accounts_upgrade_authority_basis(self, register, grey_areas, evidence_graph):
        rule_id = _make_fully_chained_rule(evidence_graph)
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        resolved = resolve_grey_area(
            atl, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation="EDB-2026-0412",
            graph=evidence_graph, resolving_rule_id=rule_id,
        )
        new_register = apply_grey_area_resolution(register, resolved)
        for code in ("10-00", "11-00", "12-00"):
            acct = next(a for a in new_register if a.account_code == code)
            assert acct.state == QualificationState.QUALIFIES
            assert acct.authority_basis == AuthorityBasis.EXPLICIT_STATUTE
            assert acct.confidence == QualificationConfidence.HIGH
            assert "EDB-2026-0412" in acct.reason
        # original register is untouched (pure function)
        original_10 = next(a for a in register if a.account_code == "10-00")
        assert original_10.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY

    def test_inkind_resolution_never_reclassifies_register_accounts(self, register, grey_areas, evidence_graph):
        """In-kind stays off-budget additive only — applying its resolution
        must be a no-op on the register (its value enters via inkind_fmv_usd
        in the optimizer, never by rewriting a register account)."""
        rule_id = _make_fully_chained_rule(evidence_graph, rule_id="R-INKIND-RULING")
        inkind = next(g for g in grey_areas if g.item_id == "GA-INKIND-FMV")
        resolved = resolve_grey_area(
            inkind, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation="EDB-2026-0500",
            graph=evidence_graph, resolving_rule_id=rule_id,
        )
        new_register = apply_grey_area_resolution(register, resolved)
        assert [a.account_code for a in new_register] == [a.account_code for a in register]
        for old, new in zip(register, new_register):
            assert old.state == new.state
            assert old.amount_usd == new.amount_usd

    def test_apply_resolution_requires_actually_resolved_item(self, register, grey_areas):
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        with pytest.raises(ValueError):
            apply_grey_area_resolution(register, atl)  # still OPEN

    def test_register_total_unchanged_after_resolution(self, register, grey_areas, evidence_graph):
        """No calculation output changes: reclassifying accounts moves
        dollars between states, never creates or destroys them."""
        rule_id = _make_fully_chained_rule(evidence_graph)
        atl = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        resolved = resolve_grey_area(
            atl, GreyAreaStatus.RESOLVED_INCLUDE, ruling_citation="EDB-2026-0412",
            graph=evidence_graph, resolving_rule_id=rule_id,
        )
        new_register = apply_grey_area_resolution(register, resolved)
        assert sum(a.amount_usd for a in new_register) == pytest.approx(sum(a.amount_usd for a in register), abs=0.01)

    def test_default_register_is_unaffected_by_p3_additions(self, register):
        """P3 is purely additive: the baseline register construction and
        its figures are identical to before migration."""
        qpe = sum(a.amount_usd for a in register if a.state == QualificationState.QUALIFIES)
        assert qpe == pytest.approx(1_979_913.0, abs=0.01)
