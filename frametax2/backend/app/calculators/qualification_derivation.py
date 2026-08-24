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

The behavior for a line whose category has NO explicit rule is governed
by the program's QUALIFICATION DOCTRINE (app.data.program_spend_rules.
QualificationDoctrine), never by the accident that a rule row happens to
be missing. This is the permanent fix for "unknown category defaults to
GREY": a missing rule row is an implementation state, not legal
authority (Rule 4 — the engine evaluates budget lines, never labels).

Decision ladder (ordered; first match wins). Every step is generic —
there is no jurisdiction-specific branch anywhere in this module:

  1. memo line                          -> NOT_APPLICABLE
  2. finance-cost category              -> NOT_APPLICABLE (modeled as a
     cashflow item by the optimizer, never as QPE-account spend)
  3. work/spend incurred outside the jurisdiction (known fact), where the
     program requires territorial spend  -> EXCLUDED / TERRITORIAL_NEXUS
  4. explicit rule for the category:
       qualifies=False -> EXCLUDED / EXPLICIT_STATUTE (the rule's own
         cited exclusion text; never engine-structural)
       qualifies=True  -> QUALIFIES (or STRUCTURING_OPPORTUNITY when a
         labor line is currently routed outside local payroll — a
         restructuring fact, not an authority bar)
  5. explicit rule with qualifies=None (the author recorded a genuine
     gap — the category maps to no clear program category even under a
     broad reading, or a known mixed-account fact gap)
       -> GREY_AREA_REQUIRES_AUTHORITY with a GENUINE reason
          (MIXED_ACCOUNT or REQUIRES_LEGAL_INTERPRETATION)
  6. NO rule for the category -> follow the program DOCTRINE:
       OPEN_DEFAULT_INCLUDE  -> QUALIFIES (silence = inclusion)
       CLOSED_POSITIVE_LIST  -> EXCLUDED (omission = exclusion authority)
       HYBRID_CONDITIONAL    -> GREY (REQUIRES_LEGAL_INTERPRETATION — a
         real question of whether a listed catch-all reaches this line)
       doctrine unclassified -> GREY (PROGRAM_REGIME_UNCLASSIFIED — an
         explicit modeling gap, never a silent include or exclude)

Every GREY_AREA carries a GreyReason (Part 4 A-F). A line is NEVER grey
merely because of a missing rule row, a classifier miss, or an internal
category gap — those follow the doctrine above.

No LLM calls. Deterministic and testable.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.calculators.classify_budget_line_items import classify_line_item
from app.calculators.qualification_model import (
    AccountQualification,
    AuthorityBasis,
    GreyReason,
    QualificationConfidence,
    QualificationState,
)
from app.data.program_spend_rules import (
    QualificationDoctrine,
    SpendRule,
    get_program_doctrine,
    get_program_rules,
    resolve_program_doctrine,
)

QUALIFICATION_DERIVATION_VERSION = "2.0.0"

# Category groups the ladder needs. Grouping only — no qualification
# outcome is decided by these sets alone.
LABOR_CATEGORIES = frozenset({
    "atl_writer", "atl_director", "atl_producer", "atl_cast",
    "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor",
})
POST_CATEGORIES = frozenset({"post_production", "vfx", "music", "sound"})
CASHFLOW_CATEGORIES = frozenset({"finance_costs"})
# Categories where a rule exists but carries qualifies=None because the
# category genuinely maps to no clear program category even under a broad
# reading (a real legal-interpretation question), NOT because a rule row
# is missing. Distinct from the "no rule at all" path, which is governed
# by the program's QualificationDoctrine.
FACT_SPLIT_CATEGORIES = frozenset({"legal_accounting"})


@dataclass(frozen=True)
class BudgetLine:
    """One budget account as the intake provides it. spend_category is
    the chart-of-accounts category when the budget source declares one;
    None means 'classify from the description'.

    account_code is a CLASSIFICATION field (department/category/reporting
    code), never a unique identity — real budgets legitimately reuse a
    code across distinct lines (subtotal/header rows, repeated department
    codes, contingency deployed to multiple destinations under its own
    account code). line_id is the actual per-line identity: it defaults
    to a fresh UUID so every existing caller gets automatic, sufficient
    uniqueness with zero code changes, but a caller backed by persisted
    storage (the real budget-ingestion path) should pass the row's own
    stable primary key instead, for full source traceability."""
    account_code: str
    description: str
    amount_usd: float
    spend_category: str | None = None
    is_memo: bool = False
    line_id: str = field(default_factory=lambda: uuid.uuid4().hex)


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
    #: Consolidated Backend Correction, CBA-009/Part 19-20 — a real, typed,
    #: user-controlled PROJECTED fact, distinct from actual/incurred
    #: contingency deployment (app.calculators.contingency_treatment,
    #: unchanged, still the authority for real, dated deployments). 0-100
    #: (percent). None means the user has not yet stated an expectation —
    #: this is a genuine missing PROJECT FACT, never silently defaulted to
    #: either 0 or 100. Applies GENERICALLY to every program whose own
    #: statutory rule says the contingency CATEGORY qualifies (e.g.
    #: Mauritius's real EDB-2020-QPE-List finding) — it does not change
    #: what the LAW says qualifies, only what fraction of the reserve a
    #: PROJECTION should treat as likely to actually be deployed and
    #: therefore incurred.
    contingency_expected_utilization_pct: float | None = None

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
    doctrine: QualificationDoctrine | None = None,
) -> list[AccountQualification]:
    """Derive the full qualification register for one program from
    budget + rules + facts + the program's qualification DOCTRINE. See
    module docstring for the ladder.

    `doctrine` governs what happens to a line whose category has no
    explicit rule (or a rule.qualifies=None): OPEN -> include, CLOSED ->
    exclude, HYBRID -> genuine legal-interpretation grey. Omitted, it is
    looked up from the program; an unclassified program surfaces as an
    explicit modeling gap, never a silent default."""
    rules = rules if rules is not None else get_program_rules(program_slug)
    # Doctrine is RESOLVED, not merely looked up: an unclassified program
    # falls to the module's CANONICAL QPE RULE (include unless explicitly
    # excluded) rather than being treated as unqualifiable, while a program
    # with recorded evidence of a narrower construction resolves to
    # HYBRID_CONDITIONAL. An explicit caller-supplied doctrine still wins.
    # See program_spend_rules.resolve_program_doctrine for the three tiers.
    doctrine = (
        doctrine if doctrine is not None
        else resolve_program_doctrine(program_slug).doctrine
    )
    jur = facts.jurisdiction_code
    register: list[AccountQualification] = []

    for line in line_items:
        category = line.spend_category or classify_line_item(line.description).spend_category.value
        rule = rules.get(category)
        amt = line.amount_usd

        def _acct(state, confidence, basis, reason, mechanism=None, evidence=None,
                  upside=None, grey_reason=None):
            register.append(AccountQualification(
                account_code=line.account_code, description=line.description,
                amount_usd=amt, state=state, confidence=confidence,
                authority_basis=basis, reason=reason, financial_impact_usd=amt,
                structuring_mechanism=mechanism, resolving_evidence=evidence,
                incentive_upside_usd=upside, grey_reason=grey_reason,
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

        # (No structural override for "contingency" or any other category:
        # canonical QPE rule — an item is included unless authoritative
        # program language explicitly excludes it. Whether an unspent
        # reserve is excluded is a statutory-rule question, answered by
        # step 5's rule.qualifies lookup and the rule's own cited text —
        # never engine-structural, never assumed here.)

        # 3. Territorial nexus (fact-driven).
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

        # 4. Statutory rule.
        qualifies = rule.qualifies if rule is not None else None

        if qualifies is False:
            _acct(QualificationState.EXCLUDED, QualificationConfidence.HIGH,
                  AuthorityBasis.EXPLICIT_STATUTE, rule.notes)
            continue

        # CBA-009/Part 19-20 fix — a program-specific rule confirming the
        # contingency CATEGORY qualifies (e.g. Mauritius's real, cited
        # EDB-2020-QPE-List finding) is a real statutory fact and stays
        # unchanged; what changes is that the FULL reserve is no longer
        # projected as 100% deployed automatically. A real, typed, user-
        # controlled expected-utilization fact scales what fraction of
        # the reserve a PROJECTION treats as likely-incurred, GENERICALLY
        # for any program whose rule says this category qualifies — never
        # hard-coded to Mauritius, never hard-coded to any other program.
        if category == "contingency" and qualifies is True:
            pct = facts.contingency_expected_utilization_pct
            if pct is None:
                # Genuine missing PROJECT FACT — never silently assumed as
                # either 0% (would incorrectly exclude a category the
                # statute confirms qualifies) or 100% (the exact defect
                # this closes). Full amount disclosed as potential upside.
                _acct(QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
                      QualificationConfidence.LOW, AuthorityBasis.FACT_DEPENDENT,
                      f"{rule.notes} Statute confirms the contingency category qualifies, but no "
                      "expected-utilization percentage has been set for this scenario — the fraction "
                      "of this reserve a producer actually expects to deploy into real production "
                      "spend is a project fact, not a legal question, and is not assumed either 0% or "
                      "100% (Consolidated Backend Correction, Part 19-20).",
                      evidence="A project/scenario expected contingency-spend utilization percentage.",
                      upside=round(amt * rate, 2),
                      grey_reason=GreyReason.MISSING_PRODUCTION_FACT)
                continue
            pct_fraction = max(0.0, min(100.0, pct)) / 100.0
            expected_deployed_usd = round(amt * pct_fraction, 2)
            expected_undeployed_usd = round(amt - expected_deployed_usd, 2)
            if expected_deployed_usd > 0:
                register.append(AccountQualification(
                    account_code=line.account_code,
                    description=f"{line.description} (expected deployed, {pct:.0f}% utilization)",
                    amount_usd=expected_deployed_usd, state=QualificationState.QUALIFIES,
                    confidence=QualificationConfidence.MEDIUM, authority_basis=AuthorityBasis.EXPLICIT_STATUTE,
                    reason=f"{rule.notes} Projected expected-deployed amount at the scenario's own "
                           f"{pct:.0f}% expected contingency utilization — priced as qualifying "
                           "category spend, not the full undeployed reserve.",
                    financial_impact_usd=expected_deployed_usd,
                ))
            if expected_undeployed_usd > 0:
                register.append(AccountQualification(
                    account_code=line.account_code,
                    description=f"{line.description} (expected undeployed, {100 - pct:.0f}% headroom)",
                    amount_usd=expected_undeployed_usd, state=QualificationState.EXCLUDED,
                    confidence=QualificationConfidence.MEDIUM, authority_basis=AuthorityBasis.STRUCTURAL_DEFINITION,
                    reason=f"The scenario's own expected utilization ({pct:.0f}%) leaves "
                           f"${expected_undeployed_usd:,.2f} of this reserve not expected to be deployed — "
                           "an undeployed reserve is not incurred production spend regardless of the "
                           "category's own statutory eligibility.",
                    financial_impact_usd=expected_undeployed_usd,
                ))
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

        # 5. A rule exists but is explicitly qualifies=None — the category
        # genuinely maps to no clear program category even under a broad
        # reading (a real legal-interpretation question the rule author
        # recorded), OR a known mixed-account fact gap. This is a GENUINE
        # grey, not the doctrine's no-rule path.
        if rule is not None and rule.qualifies is None:
            if category in FACT_SPLIT_CATEGORIES:
                _acct(QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
                      QualificationConfidence.LOW, AuthorityBasis.FACT_DEPENDENT,
                      rule.notes,
                      evidence="Itemized breakdown of this account separating its "
                               "confirmed-qualifying components from its uncertain "
                               "components.",
                      upside=round(amt * rate, 2),
                      grey_reason=GreyReason.MIXED_ACCOUNT)
            else:
                _acct(QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
                      QualificationConfidence.LOW, AuthorityBasis.ABSENCE_OF_AUTHORITY,
                      rule.notes,
                      evidence=f"{jur} authority confirmation of the QPE treatment of "
                               f"'{category}' spend.",
                      upside=round(amt * rate, 2),
                      grey_reason=GreyReason.REQUIRES_LEGAL_INTERPRETATION)
            continue

        # 5.5 Contingency, absent a program-specific rule (step 4 above
        # already handled MU's verified inclusion and DE's verified
        # exclusion — both keep their own statutory answer, unchanged).
        # Final Global Discovery phase, Objective 4: an undeployed
        # contingency reserve is not actual incurred qualifying
        # expenditure. This is a STRUCTURAL_DEFINITION fact (what "QPE"
        # means), not a doctrine question, so it is answered BEFORE the
        # doctrine dispatch below and does not vary by OPEN/CLOSED/HYBRID.
        # A deployed portion of this same reserve never reaches this
        # branch — app.calculators.contingency_treatment re-tags it with
        # its destination category before this function ever sees it, so
        # it is priced under that category's own rule/doctrine instead.
        if category == "contingency" and rule is None:
            _acct(QualificationState.EXCLUDED, QualificationConfidence.MEDIUM,
                  AuthorityBasis.STRUCTURAL_DEFINITION,
                  f"{jur} program '{program_slug}' has no program-specific "
                  "contingency rule. Canonical default (Objective 4): an "
                  "undeployed contingency reserve is a budgeted amount, not "
                  "incurred production spend, and is excluded from QPE "
                  "until a producer deploys it to a real budget line — at "
                  "which point the deployed amount is priced under that "
                  "line's own category and rule, not this one.")
            continue

        # 6. No rule at all for this category — behavior is governed by the
        # program's QUALIFICATION DOCTRINE, never by the accident that a
        # rule row is missing (that would be an implementation artifact,
        # forbidden by Part 4). The category label itself is never the
        # authority (Rule 4): an unmapped label means "no explicit rule",
        # and the doctrine decides.
        if doctrine == QualificationDoctrine.OPEN_DEFAULT_INCLUDE:
            _acct(QualificationState.QUALIFIES, QualificationConfidence.MEDIUM,
                  AuthorityBasis.EXPLICIT_STATUTE,
                  f"Included by default: {jur} program is OPEN_DEFAULT_INCLUDE — any "
                  "locally-incurred production spend qualifies unless an explicit "
                  f"exclusion clause names it, and none names category '{category}'.")
        elif doctrine == QualificationDoctrine.CLOSED_POSITIVE_LIST:
            _acct(QualificationState.EXCLUDED, QualificationConfidence.HIGH,
                  AuthorityBasis.EXPLICIT_STATUTE,
                  f"Excluded: {jur} program is a CLOSED_POSITIVE_LIST — only the "
                  "enumerated qualifying categories qualify, and category "
                  f"'{category}' is not among them (the omission is the exclusion "
                  "authority).")
        elif doctrine == QualificationDoctrine.HYBRID_CONDITIONAL:
            _acct(QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
                  QualificationConfidence.LOW, AuthorityBasis.ABSENCE_OF_AUTHORITY,
                  f"Genuine legal-interpretation question: {jur} program is "
                  "HYBRID_CONDITIONAL (a positive list with broad/illustrative "
                  f"categories). Whether category '{category}' falls within any "
                  "listed category — including the broad catch-alls — is a real "
                  "interpretive question, not resolvable from the category label "
                  "alone (Rule 4). Neither silently included nor silently excluded.",
                  evidence=f"{jur} authority confirmation of whether '{category}' spend "
                           "falls within a listed qualifying category.",
                  upside=round(amt * rate, 2),
                  grey_reason=GreyReason.REQUIRES_LEGAL_INTERPRETATION)
        else:
            # doctrine is None — the program's legal regime has not been
            # classified. A genuine modeling gap, surfaced explicitly, never
            # a silent include (fabricated qualification) or silent exclude.
            _acct(QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
                  QualificationConfidence.LOW, AuthorityBasis.ABSENCE_OF_AUTHORITY,
                  f"{jur} program '{program_slug}' has no qualification doctrine "
                  "classified yet — its legal regime (open / closed / hybrid) must "
                  "be established before any line can be qualified. Modeling gap, "
                  "surfaced rather than guessed.",
                  evidence=f"Classify the qualification doctrine for program "
                           f"'{program_slug}' from primary authority.",
                  upside=round(amt * rate, 2),
                  grey_reason=GreyReason.PROGRAM_REGIME_UNCLASSIFIED)

    return register
