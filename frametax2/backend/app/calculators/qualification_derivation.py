"""
qualification_derivation.py

Engine Integration Phase 1, Seam A: derives an account-level
qualification register from budget line items + statutory program spend
rules + known production facts, instead of hardcoding each account's
state.

    Budget line items
      -> spend-category classification (explicit chart-of-accounts
         category when the budget source declares one, otherwise
         classify_budget_line_items — the existing Gen-1 classifier)
      -> statutory program rules (app.data.program_spend_rules — the
         pure-Python mirror of migrations 0021/0025, same discipline as
         treaty_engine's migration mirror)
      -> production facts (where work is performed, how labor is routed)
      -> AccountQualification register

The output is the same qualification_model.AccountQualification the
optimizer, Legal Engine, composer, and recommendation engine already
consume — nothing downstream changes shape, and the Legal Engine's
apply_grey_area_resolution() reclassification continues to operate on
the derived register exactly as it did on the hardcoded one.

Decision ladder (ordered; first match wins). Every step is generic —
there is no jurisdiction-specific branch anywhere in this module:

  1. memo line                          -> NOT_APPLICABLE
  2. finance-cost category              -> NOT_APPLICABLE (modeled as a
     cashflow item by the optimizer, never as QPE-account spend)
  3. structural category (contingency)  -> EXCLUDED / STRUCTURAL_DEFINITION
     (only incurred expenditure can qualify — rule-backed where a
     program rule exists, engine-structural otherwise)
  4. work/spend incurred outside the jurisdiction (fact), where the
     program requires territorial spend  -> EXCLUDED / TERRITORIAL_NEXUS
  5. statutory rule lookup by category:
       qualifies=False                  -> EXCLUDED / EXPLICIT_STATUTE
       qualifies=True:
         ATL primary-authority gate: ATL categories are the single most
         contested qualification area across incentive programs, so this
         engine requires VERIFIED (primary) authority before treating
         ATL spend as qualifying — the same evidence bar the Evidence
         Graph / Legal Engine already enforce for grey-area resolution.
         A PARSED (secondary-source) True therefore yields:
           atl_cast     -> EXCLUDED / CROSS_PROGRAM_CONVENTION (the
                           near-universal above-scale-cast exclusion
                           prevails pending contrary primary evidence)
           other atl_*  -> GREY_AREA_REQUIRES_AUTHORITY
         Non-ATL True: labor currently routed outside local payroll
         (fact) -> STRUCTURING_OPPORTUNITY, else QUALIFIES.
       qualifies=None (unconfirmed)     -> convention exclusion for the
         categories excluded under near-universal cross-program
         convention (insurance, completion bond, legal/audit), else
         GREY_AREA_REQUIRES_AUTHORITY (absence of authority is explicit,
         never a silent exclusion).
  6. no rule at all for the category    -> same None-handling as above.

No LLM calls. Deterministic and testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculators.classify_budget_line_items import classify_line_item
from app.calculators.qualification_model import (
    AccountQualification,
    AuthorityBasis,
    QualificationConfidence,
    QualificationState,
)
from app.data.program_spend_rules import SpendRule, get_program_rules

QUALIFICATION_DERIVATION_VERSION = "1.0.0"

# Category groups the ladder needs. Grouping only — no qualification
# outcome is decided by these sets alone.
ATL_CATEGORIES = frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast", "atl_rights"})
LABOR_CATEGORIES = frozenset({
    "atl_writer", "atl_director", "atl_producer", "atl_cast",
    "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor",
})
POST_CATEGORIES = frozenset({"post_production", "vfx", "music", "sound"})
STRUCTURAL_EXCLUSION_CATEGORIES = frozenset({"contingency"})
CASHFLOW_CATEGORIES = frozenset({"finance_costs"})
# Near-universal cross-program convention exclusions, applied only when
# the program itself has no confirmed rule for the category.
CONVENTION_EXCLUDED_CATEGORIES = frozenset({"insurance", "completion_bond", "legal_accounting"})

# The evidence bar for contested ATL categories: primary authority.
ATL_REQUIRED_TIER = "VERIFIED"


@dataclass(frozen=True)
class BudgetLine:
    """One budget account as the intake provides it. spend_category is
    the chart-of-accounts category when the budget source declares one;
    None means 'classify from the description'."""
    account_code: str
    description: str
    amount_usd: float
    spend_category: str | None = None
    is_memo: bool = False


@dataclass(frozen=True)
class ProductionFacts:
    """Production facts that qualification legitimately depends on.
    Absence of a fact is explicit (None / not-in-set), never assumed.

    accounts_outside_jurisdiction — accounts whose work/spend is known
        to be incurred outside the baseline jurisdiction.
    offshore_payroll_accounts — labor accounts currently routed outside
        local payroll (an employer-of-record / SPV routing would fix).
    post_work_in_jurisdiction — production-level answerable fact; when
        set it overrides per-account membership for post categories.
    payroll_routing_localized — production-level answerable fact; True
        (a local routing plan is in place) clears the offshore set.
    treaty_partner_code — an elected co-production partner; consumed by
        the structure composer (extra jurisdiction sets), not here.
    """
    jurisdiction_code: str
    accounts_outside_jurisdiction: frozenset[str] = frozenset()
    offshore_payroll_accounts: frozenset[str] = frozenset()
    post_work_in_jurisdiction: bool | None = None
    payroll_routing_localized: bool | None = None
    treaty_partner_code: str | None = None

    def work_outside(self, account_code: str, category: str) -> bool:
        if category in POST_CATEGORIES and self.post_work_in_jurisdiction is not None:
            return not self.post_work_in_jurisdiction
        return account_code in self.accounts_outside_jurisdiction

    def routed_offshore(self, account_code: str, category: str) -> bool:
        if category not in LABOR_CATEGORIES:
            return False
        if self.payroll_routing_localized:
            return False
        return account_code in self.offshore_payroll_accounts


_CATEGORY_LABELS = {
    "post_production": "Post-production", "vfx": "VFX", "music": "Music scoring",
    "sound": "Sound post", "travel": "International travel",
}


def derive_qualification_register(
    line_items: list[BudgetLine],
    program_slug: str,
    facts: ProductionFacts,
    rate: float,
    program_territorial_text: str | None = None,
    rules: dict[str, SpendRule] | None = None,
) -> list[AccountQualification]:
    """Derive the full qualification register for one program from
    budget + rules + facts. See module docstring for the ladder."""
    rules = rules if rules is not None else get_program_rules(program_slug)
    jur = facts.jurisdiction_code
    register: list[AccountQualification] = []

    for line in line_items:
        category = line.spend_category or classify_line_item(line.description).spend_category.value
        rule = rules.get(category)
        amt = line.amount_usd

        def _acct(state, confidence, basis, reason, mechanism=None, evidence=None, upside=None):
            register.append(AccountQualification(
                account_code=line.account_code, description=line.description,
                amount_usd=amt, state=state, confidence=confidence,
                authority_basis=basis, reason=reason, financial_impact_usd=amt,
                structuring_mechanism=mechanism, resolving_evidence=evidence,
                incentive_upside_usd=upside,
            ))

        # 1. Memo lines are never a qualification question.
        if line.is_memo:
            _acct(QualificationState.NOT_APPLICABLE, QualificationConfidence.NOT_APPLICABLE,
                  AuthorityBasis.NOT_A_QUALIFICATION_QUESTION,
                  "Memo line — reported within gross budget but not a production "
                  "spend qualification question.")
            continue

        # 2. Finance costs are the optimizer's cashflow model, not QPE spend.
        if category in CASHFLOW_CATEGORIES:
            _acct(QualificationState.NOT_APPLICABLE, QualificationConfidence.NOT_APPLICABLE,
                  AuthorityBasis.NOT_A_QUALIFICATION_QUESTION,
                  "Not a qualification question — bridge-finance cost is modeled "
                  "separately as a cashflow item, not as QPE-account spend.")
            continue

        # 3. Structural: only incurred expenditure can qualify.
        if category in STRUCTURAL_EXCLUSION_CATEGORIES:
            reason = (rule.notes if rule is not None and rule.qualifies is False else
                      "QPE requires spend to be incurred. An unspent reserve is not "
                      "incurred cost until drawn down against an actual line item.")
            _acct(QualificationState.EXCLUDED, QualificationConfidence.HIGH,
                  AuthorityBasis.STRUCTURAL_DEFINITION, reason)
            continue

        # 4. Territorial nexus (fact-driven).
        territorial_required = (rule.territorial_only if rule is not None else
                                program_territorial_text is not None)
        if territorial_required and facts.work_outside(line.account_code, category):
            label = _CATEGORY_LABELS.get(category, "This")
            suffix = f" {program_territorial_text}" if program_territorial_text else ""
            _acct(QualificationState.EXCLUDED, QualificationConfidence.HIGH,
                  AuthorityBasis.TERRITORIAL_NEXUS,
                  f"{label} work/spend is incurred outside {jur} — territorial "
                  f"nexus fails.{suffix}")
            continue

        # 5. Statutory rule.
        qualifies = rule.qualifies if rule is not None else None
        tier = rule.confidence_tier if rule is not None else None

        if qualifies is False:
            _acct(QualificationState.EXCLUDED, QualificationConfidence.HIGH,
                  AuthorityBasis.EXPLICIT_STATUTE, rule.notes)
            continue

        if qualifies is True and category in ATL_CATEGORIES and tier != ATL_REQUIRED_TIER:
            # ATL primary-authority gate (see module docstring).
            if category == "atl_cast":
                _acct(QualificationState.EXCLUDED, QualificationConfidence.MEDIUM,
                      AuthorityBasis.CROSS_PROGRAM_CONVENTION,
                      f"No {jur} primary-source rule confirms above-scale cast fees; "
                      "they are excluded from QPE under near-universal "
                      "incentive-program convention, pending contrary primary evidence. "
                      f"Secondary-source position: {rule.notes}")
            else:
                _acct(QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
                      QualificationConfidence.LOW, AuthorityBasis.ABSENCE_OF_AUTHORITY,
                      f"ATL qualifying scope is not confirmed by primary authority — "
                      f"the {rule.confidence_tier}-tier position ({rule.notes}) has "
                      "not been verified from primary statute text.",
                      evidence=f"{jur} authority written clarification on whether "
                               "writer/director/producer fees are within QPE scope.",
                      upside=round(amt * rate, 2))
            continue

        if qualifies is True:
            if facts.routed_offshore(line.account_code, category):
                _acct(QualificationState.STRUCTURING_OPPORTUNITY,
                      QualificationConfidence.MEDIUM, AuthorityBasis.STRUCTURING_DEPENDENT,
                      "No rule bars qualification — blocked by current payroll/vendor "
                      "routing, not by authority.",
                      mechanism=f"Route through {jur} employer-of-record or existing "
                                "production SPV, arm's-length invoicing.",
                      evidence=f"Documented {jur} employer/SPV routing agreement for "
                               "this account's personnel.",
                      upside=round(amt * rate, 2))
            else:
                _acct(QualificationState.QUALIFIES, QualificationConfidence.HIGH,
                      AuthorityBasis.EXPLICIT_STATUTE, rule.notes)
            continue

        # 6. qualifies is None / no rule: convention or explicit grey area.
        if category in CONVENTION_EXCLUDED_CATEGORIES:
            _acct(QualificationState.EXCLUDED, QualificationConfidence.MEDIUM,
                  AuthorityBasis.CROSS_PROGRAM_CONVENTION,
                  f"No {jur}-specific rule located; this category is excluded from "
                  "QPE under near-universal incentive-program convention, pending "
                  "contrary evidence."
                  + (f" Program record: {rule.notes}" if rule is not None else ""))
        else:
            _acct(QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
                  QualificationConfidence.LOW, AuthorityBasis.ABSENCE_OF_AUTHORITY,
                  (rule.notes if rule is not None else
                   f"No {jur} rule for category '{category}' has been located — "
                   "absence of authority, escalated rather than silently excluded."),
                  evidence=f"{jur} authority confirmation of the QPE treatment of "
                           f"'{category}' spend.",
                  upside=round(amt * rate, 2))

    return register
