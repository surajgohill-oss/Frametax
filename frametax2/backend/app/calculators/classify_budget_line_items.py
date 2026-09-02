"""
classify_budget_line_items.py

Deterministic classification of budget line items into:
- ATL / BTL / POST / OTHER
- SpendCategory (btl_crew_labor, atl_director, post_production, etc.)
- is_fixed (ATL fixed fee vs. BTL variable cost)
- is_labor / is_resident_labor
- compensation_type (cash / deferred / equity / in_kind)

Rules are keyword-based with explicit priority ordering.
No LLM calls here — LLM extracts raw data; this module classifies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import NamedTuple

from app.models.enums import ATLBTLCategory, CompensationType, SpendCategory


ENGINE_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Classification rules (ordered — first match wins)
# ---------------------------------------------------------------------------

@dataclass
class ClassificationRule:
    pattern: str  # regex applied to description.lower()
    atl_btl: ATLBTLCategory
    spend_category: SpendCategory
    is_fixed: bool
    is_labor: bool
    compensation_type: CompensationType = CompensationType.CASH


_RULES: list[ClassificationRule] = [
    # --- Obligations that NAME a guild but are not that guild's fee ---
    # A residuals reserve is a funded guild obligation, NOT contingency and
    # NOT the guild's above-the-line fee. Real top sheets write it as "SAG
    # residuals accrual" / "WGA residuals", so it must be matched BEFORE the
    # ATL guild-name rules below, which would otherwise claim it as cast,
    # writer or director compensation.
    ClassificationRule(r"residual",
                       ATLBTLCategory.OTHER, SpendCategory.RESIDUALS_RESERVE, False, False),

    # --- Above-the-Line (fixed fees) ---
    # A real top sheet names ATL DEPARTMENTS ("SCRIPT", "PRODUCING",
    # "DIRECTING", "CAST"), not fee-style labels ("director fee"). The
    # fee-style spellings are kept; the department spellings are added, so
    # source account semantics classify without a per-production rule.
    ClassificationRule(r"director( fee|'s fee|ial fee)?$|dga fee|director fee|directing",
                       ATLBTLCategory.ATL, SpendCategory.ATL_DIRECTOR, True, True),
    ClassificationRule(r"writer|screenplay|script fee|wga|(^|\s)script(\s|$)|story",
                       ATLBTLCategory.ATL, SpendCategory.ATL_WRITER, True, True),
    ClassificationRule(r"producer( fee)?$|executive producer|ep fee|producing",
                       ATLBTLCategory.ATL, SpendCategory.ATL_PRODUCER, True, True),
    ClassificationRule(r"lead cast|star( fee)?|cast( fee)?$|actor fee|talent fee|sag|(^|\s)cast(\s|$)",
                       ATLBTLCategory.ATL, SpendCategory.ATL_CAST, True, True),
    ClassificationRule(r"rights|option|underlying|book right|life rights|remake",
                       ATLBTLCategory.ATL, SpendCategory.ATL_RIGHTS, True, False),

    # --- Deferred / Equity / In-kind compensation (any ATL/BTL role) ---
    ClassificationRule(r"deferred|deferral|deferment",
                       ATLBTLCategory.ATL, SpendCategory.ATL_CAST, True, True,
                       CompensationType.DEFERRED),
    ClassificationRule(r"equity participation|net profit point|backend",
                       ATLBTLCategory.ATL, SpendCategory.ATL_CAST, True, True,
                       CompensationType.EQUITY),
    ClassificationRule(r"in[- ]kind|reinvestment",
                       ATLBTLCategory.BTL, SpendCategory.IN_KIND, False, False,
                       CompensationType.IN_KIND),

    # --- Post-production ---
    ClassificationRule(r"vfx|visual effects|cgi|animation",
                       ATLBTLCategory.POST, SpendCategory.VFX, False, False),
    ClassificationRule(r"music( score)?|composer|score|soundtrack",
                       ATLBTLCategory.POST, SpendCategory.MUSIC, False, False),
    ClassificationRule(r"sound( mix| design| edit|ing)?|adr|dubbing|foley",
                       ATLBTLCategory.POST, SpendCategory.SOUND, False, False),
    ClassificationRule(r"post[ -]prod|editing|color|grade|deliverables|dcp|mastering",
                       ATLBTLCategory.POST, SpendCategory.POST_PRODUCTION, False, False),

    # --- BTL Non-labor ---
    # Vessel/marine must precede generic equipment so "marine equipment" routes correctly
    ClassificationRule(r"vessel|yacht|charter boat|boat (hire|charter|rental)|marine (equip|gear|support|unit)|dive boat|underwater camera|speedboat|speed boat",
                       ATLBTLCategory.BTL, SpendCategory.VESSEL_MARINE, False, False),
    ClassificationRule(r"equipment( rental)?|camera rental|lighting rental|grip",
                       ATLBTLCategory.BTL, SpendCategory.BTL_EQUIPMENT_RENTAL, False, False),
    ClassificationRule(r"stage|studio rental|backlot|sound stage",
                       ATLBTLCategory.BTL, SpendCategory.BTL_STAGE_FACILITY, False, False),
    ClassificationRule(r"location fee|location permit|location rental",
                       ATLBTLCategory.BTL, SpendCategory.BTL_LOCATION_FEES, False, False),
    ClassificationRule(r"set( dressing)?|construction|art department|props",
                       ATLBTLCategory.BTL, SpendCategory.BTL_SET_CONSTRUCTION, False, False),
    ClassificationRule(r"transport|truck|vehicle rental|shuttle|van",
                       ATLBTLCategory.BTL, SpendCategory.BTL_TRANSPORTATION, False, False),
    ClassificationRule(r"cater|meals|craft service|catering",
                       ATLBTLCategory.BTL, SpendCategory.BTL_CATERING, False, False),

    # --- BTL Labor ---
    ClassificationRule(r"resident.*labor|resident.*crew|local.*hire|local.*labor",
                       ATLBTLCategory.BTL, SpendCategory.BTL_RESIDENT_LABOR, False, True),
    ClassificationRule(r"nonresident.*labor|non.?resident.*labor|out.?of.?state.*labor",
                       ATLBTLCategory.BTL, SpendCategory.BTL_NONRESIDENT_LABOR, False, True),
    ClassificationRule(r"crew|dp|cinematographer|gaffer|key grip|production design|costum|makeup|hair",
                       ATLBTLCategory.BTL, SpendCategory.BTL_CREW_LABOR, False, True),
    ClassificationRule(r"payroll|fringe|pension|health|iatse|teamster|guild",
                       ATLBTLCategory.BTL, SpendCategory.PAYROLL_FRINGES, False, True),

    # --- Travel / Lodging ---
    ClassificationRule(r"travel|airfare|flight|airfare",
                       ATLBTLCategory.BTL, SpendCategory.TRAVEL, False, False),
    ClassificationRule(r"hotel|lodging|accommodation|per diem",
                       ATLBTLCategory.BTL, SpendCategory.LODGING, False, False),

    # --- Finance / Insurance / Bond (excluded from most incentive programs) ---
    # Real film budgets name these as departments, not as "finance cost":
    # "FINANCING FEES", "BRIDGE", "BANKING FEE". The stem "financ" covers
    # finance/financing/financial; bridge and banking are named explicitly.
    # These are production FINANCING charges, never miscellaneous spend.
    ClassificationRule(r"financ|interest|loan fee|bank fee|banking|bridge",
                       ATLBTLCategory.OTHER, SpendCategory.FINANCE_COSTS, False, False),
    ClassificationRule(r"insurance|e&o|errors.and.omissions",
                       ATLBTLCategory.OTHER, SpendCategory.INSURANCE, False, False),
    ClassificationRule(r"completion( guarantee| bond)|bond premium|bond fee|completion fee",
                       ATLBTLCategory.OTHER, SpendCategory.COMPLETION_BOND, False, False),
    # Little Utopia Economic Reconciliation: "conting?ency" tolerates the
    # real, common misspelling "Contigency" (missing the 'n') found in
    # Little Utopia's own real source budget PDF (account 8300) — a real,
    # generic gap independently proven by two facts: (1) the SAME account
    # is hand-classified "contingency" in app/data/little_utopia_real_
    # budget.py's own account-code-keyed map, confirming the doctrine
    # intends this exact line to be a contingency reserve; (2) the
    # category's own display name uses the correct spelling, so a typo in
    # ANY production's real budget PDF would silently defeat this rule
    # the same way. Not new doctrine — this is the SAME existing rule,
    # made robust to a real spelling variant, exactly like "conting?ency"
    # already tolerates both "contingency" and "reserve" as synonyms.
    ClassificationRule(r"contin?gency|reserve",
                       ATLBTLCategory.OTHER, SpendCategory.CONTINGENCY, False, False),
]

# Compile patterns for performance
_COMPILED: list[tuple[re.Pattern, ClassificationRule]] = [
    (re.compile(r.pattern, re.IGNORECASE), r) for r in _RULES
]


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class ClassificationResult(NamedTuple):
    atl_btl: ATLBTLCategory
    spend_category: SpendCategory
    is_fixed: bool
    is_labor: bool
    compensation_type: CompensationType
    rule_matched: str | None  # the pattern that triggered this classification


def classify_line_item(description: str, department: str | None = None) -> ClassificationResult:
    """
    Deterministically classify a budget line item by description and optional department.
    Returns a ClassificationResult with the matched rule's pattern for audit trace.
    """
    search_text = f"{description} {department or ''}".lower().strip()

    # SOURCE ACCOUNT SEMANTICS DECIDE ATL/BTL.
    # The budget parser already derives `department` from the source
    # document's own account-code convention (1000s = Above The Line, and so
    # on -- see budget_parser._dept_for_acct). A description-pattern table
    # cannot know that convention, so a real ATL department whose name is not
    # fee-shaped ("SCRIPT", "PRODUCING", "DIRECTING", "CAST", "ATL TRAVEL &
    # LIVING", "Total Fringes") fell through to the default BTL branch and the
    # whole above-the-line block was reported below the line. The source
    # document already stated the answer; honour it rather than re-deriving
    # it from prose.
    department_text = (department or "").lower()
    department_atl = "above the line" in department_text or department_text.strip() == "atl"

    for pattern, rule in _COMPILED:
        if pattern.search(search_text):
            return ClassificationResult(
                atl_btl=(
                    ATLBTLCategory.ATL
                    if department_atl and rule.atl_btl is ATLBTLCategory.BTL
                    else rule.atl_btl
                ),
                spend_category=rule.spend_category,
                is_fixed=rule.is_fixed,
                is_labor=rule.is_labor,
                compensation_type=rule.compensation_type,
                rule_matched=rule.pattern,
            )

    # Default: unclassified BTL labor -- unless the source account convention
    # already placed this line above the line.
    return ClassificationResult(
        atl_btl=ATLBTLCategory.ATL if department_atl else ATLBTLCategory.BTL,
        spend_category=SpendCategory.MISCELLANEOUS,
        is_fixed=False,
        is_labor=False,
        compensation_type=CompensationType.CASH,
        rule_matched=None,
    )


def classify_atl_btl_split(
    line_items: list[dict],
) -> dict:
    """
    Classify a list of line item dicts and return summary totals.
    Each dict must have at least: description, amount_usd.
    Optional: department.

    Returns a trace-ready dict with classified items and subtotals.
    """
    classified = []
    totals = {
        "atl_total_usd": 0.0,
        "btl_total_usd": 0.0,
        "post_total_usd": 0.0,
        "other_total_usd": 0.0,
        "fixed_atl_usd": 0.0,
        "variable_btl_usd": 0.0,
        "labor_usd": 0.0,
        "non_labor_usd": 0.0,
    }

    for item in line_items:
        result = classify_line_item(
            description=item.get("description", ""),
            department=item.get("department"),
        )
        amount = float(item.get("amount_usd") or 0.0)

        classified.append({
            **item,
            "atl_btl": result.atl_btl.value,
            "spend_category": result.spend_category.value,
            "is_fixed": result.is_fixed,
            "is_labor": result.is_labor,
            "compensation_type": result.compensation_type.value,
            "classification_rule": result.rule_matched,
        })

        if result.atl_btl == ATLBTLCategory.ATL:
            totals["atl_total_usd"] += amount
            if result.is_fixed:
                totals["fixed_atl_usd"] += amount
        elif result.atl_btl == ATLBTLCategory.BTL:
            totals["btl_total_usd"] += amount
            totals["variable_btl_usd"] += amount
        elif result.atl_btl == ATLBTLCategory.POST:
            totals["post_total_usd"] += amount
        else:
            totals["other_total_usd"] += amount

        if result.is_labor:
            totals["labor_usd"] += amount
        else:
            totals["non_labor_usd"] += amount

    return {
        "engine_version": ENGINE_VERSION,
        "classified_items": classified,
        "totals": totals,
    }
