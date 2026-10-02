"""SCENARIO LOCAL-LABOUR DEFAULT (2026-10-02) -- the ONE inference every consumer shares.

Project-wide rule: for a HYPOTHETICAL full relocation or routed physical-production leg, below-the-line (BTL) labour
assigned to that jurisdiction is modeled as locally hired unless the project states an override
(ProjectFact ``scenario_btl_nonlocal`` = true).

It is a scenario assumption ONLY:
  * the source budget's residency is never rewritten (the budget lines are read, never changed);
  * it never claims the actual current production already has local labour;
  * cast residency is a separate fact and is NEVER inferred here;
  * producer / director / above-the-line nationality or residency stays separately evidenced (treated as non-resident
    for the crew percentage unless a stored fact says otherwise).

Consumers: ``qualification_derivation.ProductionFacts.scenario_local_btl`` (QPE labour residency, set by
``canonical_project_economics.production_facts_for`` and ``allocation_pricing.price_segment``) and the served accounting
(``jurisdiction_accounting``) for resident-crew-percentage conditions (``RateCondition.local_labour_basis``).
"""
from __future__ import annotations

from app.calculators.qualification_derivation import BTL_LABOR_CATEGORIES

#: above-the-line CREW categories (cast is separate and never inferred)
ATL_CREW_CATEGORIES = frozenset({"atl_writer", "atl_producer", "atl_director"})

SCENARIO_NOTE = (
    "Scenario assumption: BTL labour assigned to this jurisdiction is modeled as locally hired unless a project "
    "override states otherwise. The source budget's residency is unchanged; cast residency and producer / director / "
    "ATL residency remain separately evidenced."
)


def scenario_local_btl_applies(jurisdiction_code: str | None, home_jurisdiction_code: str | None, *, nonlocal_override: bool) -> bool:
    return bool(jurisdiction_code and home_jurisdiction_code and jurisdiction_code != home_jurisdiction_code and not nonlocal_override)


def inferred_crew_resident_pct(budget_lines) -> float | None:
    """The resident share (0-100) of the BTL CREW under the scenario default: every BTL crew labour line assigned to the
    relocated jurisdiction is locally hired, so the BTL crew is 100% resident. None when the budget carries no BTL crew
    labour (nothing to infer from). It is a BTL-crew share, not a dollar-weighted share of ALL crew: producer / director /
    writer residency is separately evidenced and is not netted in (a handful of ATL roles against a BTL crew cannot be
    weighed by pay)."""
    for line in budget_lines:
        if getattr(line, "is_memo", False):
            continue
        if getattr(line, "spend_category", None) in BTL_LABOR_CATEGORIES and float(line.amount_usd or 0.0) > 0:
            return 100.0
    return None


def apply_scenario_crew_inference(detail: dict | None, budget_lines) -> dict | None:
    """For every unresolved resident-CREW percentage proposition (``local_labour_basis == "crew_resident_pct"``) with no
    stored producer value, infer the percentage under the scenario default, record it under ``scenario_assumptions`` and
    drop the proposition when it meets its minimum. Cast and every other proposition are left untouched."""
    if not detail:
        return detail
    assumed = []
    for prop in list(detail.get("unresolved_propositions") or []):
        if prop.get("local_labour_basis") == "crew_resident_pct" and prop.get("stored_value") is None:
            pct = inferred_crew_resident_pct(budget_lines)
            if pct is None:
                continue
            prop["scenario_inferred_value"] = pct
            prop["scenario_note"] = SCENARIO_NOTE
            assumed.append(prop)
            if prop.get("amount_min") is None or pct >= float(prop["amount_min"]):
                detail["unresolved_propositions"].remove(prop)
    if assumed:
        detail["scenario_assumptions"] = [
            {"fact_key": p_["fact_key"], "inferred_value": p_["scenario_inferred_value"],
             "requirement": p_.get("requirement"), "note": p_["scenario_note"]} for p_ in assumed
        ]
        detail["ceiling_unlocked_by"] = [p_["condition_id"] for p_ in detail.get("unresolved_propositions", [])]
    return detail
