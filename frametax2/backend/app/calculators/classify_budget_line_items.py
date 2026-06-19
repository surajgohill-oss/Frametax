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
    # --- Above-the-Line (fixed fees) ---
    ClassificationRule(r"director( fee|'s fee|ial fee)?$|dga fee|director fee",
                       ATLBTLCategory.ATL, SpendCategory.ATL_DIRECTOR, True, True),
    ClassificationRule(r"writer|screenplay|script fee|wga",
                       ATLBTLCategory.ATL, SpendCategory.ATL_WRITER, True, True),
    ClassificationRule(r"producer( fee)?$|executive producer|ep fee",
                       ATLBTLCategory.ATL, SpendCategory.ATL_PRODUCER, True, True),
    ClassificationRule(r"lead cast|star( fee)?|cast( fee)?$|actor fee|talent fee|sag",
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
    ClassificationRule(r"finance cost|interest|loan fee|bank fee|gap financ",
                       ATLBTLCategory.OTHER, SpendCategory.FINANCE_COSTS, False, False),
    ClassificationRule(r"insurance|e&o|errors.and.omissions",
                       ATLBTLCategory.OTHER, SpendCategory.INSURANCE, False, False),
    ClassificationRule(r"completion( guarantee| bond)|bond premium",
                       ATLBTLCategory.OTHER, SpendCategory.COMPLETION_BOND, False, False),
    ClassificationRule(r"contingency|reserve",
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

    for pattern, rule in _COMPILED:
        if pattern.search(search_text):
            return ClassificationResult(
                atl_btl=rule.atl_btl,
                spend_category=rule.spend_category,
                is_fixed=rule.is_fixed,
                is_labor=rule.is_labor,
                compensation_type=rule.compensation_type,
                rule_matched=rule.pattern,
            )

    # Default: unclassified BTL labor
    return ClassificationResult(
        atl_btl=ATLBTLCategory.BTL,
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
