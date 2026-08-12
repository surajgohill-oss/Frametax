"""
Consolidated Global Remediation, Phase D/E verification.

Targeted fixtures proving two canonical CineGlobe rules already enforced by
qualification_derivation.py's decision ladder:

  Phase D — QPE default-inclusion: a budget line with NO explicit program
    spend rule still QUALIFIES when the program's doctrine is
    OPEN_DEFAULT_INCLUDE (silence is not exclusion).

  Phase E — territoriality: work/spend physically incurred outside the
    jurisdiction is EXCLUDED on territorial-nexus grounds even when the
    production reports payroll_routing_localized=True (i.e. paid through
    a local SPV/employer-of-record) -- local-SPV payment alone must not
    manufacture qualifying territorial expenditure.
"""
from app.calculators.qualification_derivation import (
    BudgetLine,
    ProductionFacts,
    derive_qualification_register,
)
from app.calculators.qualification_model import AuthorityBasis, QualificationState
from app.data.program_spend_rules import QualificationDoctrine


def test_open_default_include_qualifies_a_line_with_no_explicit_rule():
    """Phase D: silence in the rule table is not exclusion."""
    line = BudgetLine(
        account_code="9999-00",
        description="Miscellaneous production cost with no explicit rule row",
        amount_usd=10_000.0,
        spend_category="miscellaneous",
    )
    facts = ProductionFacts(jurisdiction_code="ZZ")
    register = derive_qualification_register(
        line_items=[line],
        program_slug="no_such_program_has_rules_for_this_category",
        facts=facts,
        rate=0.30,
        rules={},  # no explicit rule for this category anywhere
        doctrine=QualificationDoctrine.OPEN_DEFAULT_INCLUDE,
    )
    assert len(register) == 1
    assert register[0].state == QualificationState.QUALIFIES


def test_local_spv_payment_alone_does_not_override_territorial_exclusion():
    """Phase E: a labor account whose work is physically outside the
    jurisdiction must stay EXCLUDED on territorial-nexus grounds even when
    payroll_routing_localized=True (paid through a local SPV/EOR)."""
    line = BudgetLine(
        account_code="2100-05",
        description="Crew labor physically performed outside the jurisdiction",
        amount_usd=50_000.0,
        spend_category="btl_crew_labor",
    )
    facts = ProductionFacts(
        jurisdiction_code="ZZ",
        accounts_outside_jurisdiction=frozenset({"2100-05"}),
        payroll_routing_localized=True,  # paid through a local SPV/EOR
    )
    register = derive_qualification_register(
        line_items=[line],
        program_slug="fixture_program",
        facts=facts,
        rate=0.30,
        rules={},
        doctrine=QualificationDoctrine.OPEN_DEFAULT_INCLUDE,
        program_territorial_text="Spend must be incurred in-jurisdiction.",
    )
    assert len(register) == 1
    acct = register[0]
    assert acct.state == QualificationState.EXCLUDED
    assert acct.authority_basis == AuthorityBasis.TERRITORIAL_NEXUS
    assert "outside" in acct.reason.lower()


def test_localized_payroll_routing_only_clears_the_structuring_flag_not_territoriality():
    """A labor account that IS physically in-jurisdiction but was flagged
    offshore-payroll clears to QUALIFIES once routing is localized -- this
    is the one case local-SPV routing legitimately affects, and it never
    reaches the territorial-nexus branch at all because work is in-country."""
    line = BudgetLine(
        account_code="2100-06",
        description="Crew labor physically performed in-jurisdiction, payroll now localized",
        amount_usd=25_000.0,
        spend_category="btl_crew_labor",
    )
    facts = ProductionFacts(
        jurisdiction_code="ZZ",
        offshore_payroll_accounts=frozenset({"2100-06"}),
        payroll_routing_localized=True,
    )
    register = derive_qualification_register(
        line_items=[line],
        program_slug="fixture_program",
        facts=facts,
        rate=0.30,
        rules={},
        doctrine=QualificationDoctrine.OPEN_DEFAULT_INCLUDE,
    )
    assert len(register) == 1
    assert register[0].state == QualificationState.QUALIFIES
