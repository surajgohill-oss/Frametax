"""PROGRAM PRICING CROSSWALK (2026-10-02) -- one canonical economic TREATMENT per rate-bearing program, and the
Single-Jurisdiction served contract built on the accounting ledger.

This is a DERIVATION over the existing canonical owners (RateRules, doctrine, requirements profile, authority coverage
registry, economic block). It is not a registry and it prices nothing: it classifies what the registries already say
into the eight treatments the project doctrine recognises, so a later authority/discretionary layer can never again
silently turn real economics into "no program":

  DETERMINISTIC_PRICEABLE             complete rate/base/cap mechanics; prices when project thresholds pass
  PRICEABLE_WITH_PROVENANCE_WARNING   real retained RateRule; provenance is incomplete (a production-acceptance warning,
                                      never an economic block -- the two-axis rule)
  CONDITIONAL_TIER                    confirmed floor prices; a higher tier is conditional (maximum + exact facts served)
  DISCRETIONARY_ZERO_GUARANTEED       the award itself is selective: confirmed floor $0, maximum potential served
  PROJECT_FACT_REQUIRED               deterministic economics conditional on named project facts
  ECONOMIC_MECHANICS_INCOMPLETE       a material rate/base/cap mechanic is genuinely absent (never invented)
  SUPERSEDED_DUPLICATE_NOT_APPLICABLE superseded / duplicate / scoped to another production type
  CONFIRMED_HARD_INELIGIBLE           project-specific only: a mandatory gate demonstrably fails (a per-project status)

The first-match order below is the whole policy; ``test_program_pricing_reconciliation`` pins it, including the
Saudi recurrence guarantee (a verified 60% program can never again lose its potential economics to an authority block
or an alias spelling).
"""
from __future__ import annotations

T_DETERMINISTIC = "DETERMINISTIC_PRICEABLE"
T_PROVENANCE = "PRICEABLE_WITH_PROVENANCE_WARNING"
T_CONDITIONAL_TIER = "CONDITIONAL_TIER"
T_DISCRETIONARY = "DISCRETIONARY_ZERO_GUARANTEED"
T_PROJECT_FACT = "PROJECT_FACT_REQUIRED"
T_MECHANICS_INCOMPLETE = "ECONOMIC_MECHANICS_INCOMPLETE"
T_SUPERSEDED_NA = "SUPERSEDED_DUPLICATE_NOT_APPLICABLE"
T_HARD_INELIGIBLE = "CONFIRMED_HARD_INELIGIBLE"
TREATMENTS = (T_DETERMINISTIC, T_PROVENANCE, T_CONDITIONAL_TIER, T_DISCRETIONARY, T_PROJECT_FACT,
              T_MECHANICS_INCOMPLETE, T_SUPERSEDED_NA)  # CONFIRMED_HARD_INELIGIBLE is per project, never per program

#: tier-level conditions that mean the tier's VALUE is a selective / discretionary award
_DISCRETIONARY_CONDITIONS = frozenset({"discretionary_band", "material_funding_risk_not_modeled"})
#: tier-level conditions that are named project facts (the producer can supply them)
_FACT_CONDITIONS = frozenset({
    "project_fact_dependent_eligibility", "project_fact_dependent_uplift", "cultural_test_required",
    "alternate_qualification_track", "mutually_exclusive_alternative_program",
})


def _aliases_of(slug: str) -> list[str]:
    from app.data.program_slug_aliases import PROGRAM_SLUG_ALIASES

    return sorted(a for a, c in PROGRAM_SLUG_ALIASES.items() if c == slug and a != slug)


def program_treatment(slug: str, production_type: str = "feature_film") -> dict:
    """Classify one rate-bearing program into exactly one economic treatment (+ the mechanics columns)."""
    from app.data.authority_coverage_registry import coverage_state, economic_block_for_program
    from app.data.executable_jurisdiction_registry import get_doctrine
    from app.data.program_rate_rules import get_rate_rules
    from app.data.program_requirements import get_program_requirements
    from app.services.jurisdiction_accounting import _min_spend_threshold
    from app.services.jurisdiction_disposition import rate_rule_fact_keys

    rules = get_rate_rules(slug)
    block = economic_block_for_program(slug)
    state = coverage_state(slug)
    req = get_program_requirements(slug)
    doctrine = get_doctrine(slug)
    applicable = [r for r in rules if production_type in (r.production_types or ())]
    floors = [r for r in applicable if not r.is_band_ceiling]
    ceilings = [r for r in applicable if r.is_band_ceiling]
    floor_tiers_cond = {c.kind for r in floors for c in r.conditions}
    all_cond = {c.kind for r in applicable for c in r.conditions}
    allocation = req.allocation_type.name if req is not None and req.allocation_type is not None else None
    provenance_warning = state == "AUTHORITY_UNRESOLVED_NON_PRICEABLE" or any(r.confidence_tier != "VERIFIED" for r in rules)

    treatment, why = None, None
    # The engine's OWN resolver, probed with a generous production and NO project facts (what is deterministic) and with
    # every named boolean fact confirmed (what the facts could unlock). No new pricing path: resolve_program_rate only.
    from app.data.program_rate_rules import build_discovery_amount_probe, resolve_program_rate

    _qpe, _gross = 50_000_000.0, 60_000_000.0
    _probe = build_discovery_amount_probe(slug, _gross, {}, None)
    _confirm = frozenset(c.required_boolean_fact_key for r in applicable for c in r.conditions if c.required_boolean_fact_key)
    try:
        res_none = resolve_program_rate(slug, production_type, _qpe, _gross, evidenced_facts=frozenset(), amount_facts=_probe)
        res_all = resolve_program_rate(slug, production_type, _qpe, _gross, evidenced_facts=_confirm, amount_facts=_probe)
    except Exception:  # noqa: BLE001
        res_none = res_all = None
    # a block makes the resolver return None; probe the RULES directly for the block-free mechanics
    if (block is not None and block.classification in ("RETIRED_SUPERSEDED_IDENTITY",)) or state in ("SUPERSEDED", "DUPLICATE"):
        treatment, why = T_SUPERSEDED_NA, "retired / superseded / duplicate identity per the canonical registry"
    elif rules and not applicable:
        treatment, why = T_SUPERSEDED_NA, "every RateRule tier is scoped to other production types"
    elif state in ("UNPRICEABLE_AUTHORITY_INSUFFICIENT", "NON_ECONOMIC", "CANONICAL_DATA_HANDOFF_DEFECT"):
        treatment, why = T_MECHANICS_INCOMPLETE, (
            f"coverage state {state}: the primary-authority corpus captured no defensible current rate / award basis")
    elif block is not None or state == "NON_GUARANTEED_SELECTIVE":
        treatment, why = T_DISCRETIONARY, (
            f"the award itself is selective (block={block.classification if block else None}, coverage={state})")
    elif res_none is None and res_all is not None:
        treatment, why = T_PROJECT_FACT, "resolves only once named project facts are confirmed"
    elif res_none is None:
        treatment, why = T_MECHANICS_INCOMPLETE, "does not resolve even with every named fact confirmed (a mechanic is absent)"
    elif not res_none.has_guaranteed_floor:
        treatment, why = T_DISCRETIONARY, "only an 'up to' ceiling tier exists; no guaranteed floor tier"
    elif res_none.modeled_rate > res_none.floor_rate + 1e-12 or ceilings:
        treatment, why = T_CONDITIONAL_TIER, "a confirmed floor prices; a higher tier is conditional"
    elif any(ce.satisfied is None for ce in res_none.conditions_evaluated):
        treatment, why = T_PROJECT_FACT, "the floor prices with named project facts still unresolved"
    elif provenance_warning:
        treatment, why = T_PROVENANCE, "real retained RateRule; provenance incomplete (production-acceptance warning only)"
    else:
        treatment, why = T_DETERMINISTIC, "complete formula / rate / base / cap mechanics"

    cap = (req.per_project_cap_usd if req is not None and req.per_project_cap_usd else None)
    annual_cap = doctrine.annual_cap_usd if doctrine is not None else None
    return {
        "program_slug": slug,
        "alias_slugs": _aliases_of(slug),
        "jurisdiction_code": (doctrine.jurisdiction_code if doctrine is not None else None),
        "production_types": sorted({t for r in rules for t in (r.production_types or ())}),
        "applicable_to_production_type": bool(applicable),
        "treatment": treatment, "treatment_reason": why,
        "deterministic_floor_rate": max((r.rate for r in floors), default=None),
        "supported_maximum_rate": max((r.rate for r in applicable), default=None),
        "minimum_spend_usd": _min_spend_threshold(slug, production_type),
        "per_project_cap_usd": cap, "annual_program_cap_usd": annual_cap,
        "required_project_facts": sorted(k.split(":", 1)[-1] for k in rate_rule_fact_keys(slug)),
        "authority_coverage_state": state,
        "authority_block": block.classification if block is not None else None,
        "rate_rule_confidence": sorted({r.confidence_tier for r in rules}),
        "provenance_warning": bool(provenance_warning),
        "allocation_type": allocation,
    }


def all_program_treatments(production_type: str = "feature_film") -> list[dict]:
    from app.data.program_rate_rules import _RULES_BY_PROGRAM

    return [program_treatment(s, production_type) for s in sorted(_RULES_BY_PROGRAM)]


# ── Single-Jurisdiction served contract ────────────────────────────────────────────────────────────────────────────
CAT_LEADING = "LEADING_ALTERNATIVE"
CAT_STRONG = "STRONG_ALTERNATIVE"
CAT_REFERENCE = "REFERENCE_ALTERNATIVE"
CAT_CONDITIONAL = "CONDITIONAL_ALTERNATIVE"
CAT_NOT_SUITABLE = "NOT_SUITABLE_FOR_THIS_PRODUCTION"
CAT_UNAVAILABLE = "UNAVAILABLE"
CAT_DATA_INCOMPLETE = "PROGRAM_DATA_INCOMPLETE"


def build_single_jurisdiction_contract(ledger: dict, best_per_jurisdiction: dict) -> list[dict]:
    """One record per accounted jurisdiction carrying everything the later Single-Jurisdiction UI needs: the category,
    confirmed incentive / NPC, maximum-potential incentive / NPC, economic certainty, the exact missing conditions, the
    authority/provenance warning and the hard-failure reason. Confirmed and potential rankings stay separate."""
    rows_by_juris: dict[str, dict] = {}
    for r in ledger.get("rows") or []:
        code = r.get("primary_jurisdiction")
        prev = rows_by_juris.get(code)
        # keep the strongest accounted row per jurisdiction (needs facts > hard > data incomplete)
        rank = {"NEEDS_FACTS": 3, "HARD_BLOCK": 2, "DATA_INCOMPLETE": 1, "NOT_APPLICABLE": 0}
        if prev is None or rank.get(r.get("disposition"), 0) > rank.get(prev.get("disposition"), 0):
            rows_by_juris[code] = r
    out: list[dict] = []
    confirmed = sorted((e for e in best_per_jurisdiction.values() if e.get("confirmed_npc_usd") is not None),
                       key=lambda e: e["confirmed_npc_usd"])
    leader = confirmed[0]["primary_jurisdiction"] if confirmed else None
    for j in ledger.get("jurisdictions") or []:
        code = j["jurisdiction_code"]
        disp = j["disposition"]
        rec: dict = {"jurisdiction_code": code, "disposition": disp, "first_exit_stage": j.get("first_exit_stage"),
                     "confirmed_incentive_usd": None, "confirmed_npc_usd": None, "potential_incentive_usd": None,
                     "potential_npc_usd": None, "economic_certainty": None, "missing_conditions": [],
                     "authority_warning": None, "hard_failure_reason": None, "difference_reason": None, "program_slug": None}
        if disp == "EXECUTABLE":
            e = best_per_jurisdiction.get(code) or {}
            rec.update(
                confirmed_incentive_usd=e.get("confirmed_incentive_floor_usd", e.get("selected_incentive_usd")),
                confirmed_npc_usd=e.get("confirmed_npc_usd"), potential_incentive_usd=e.get("maximum_supported_incentive_usd"),
                potential_npc_usd=e.get("potential_npc_usd"), economic_certainty=e.get("economics_certainty"),
                missing_conditions=[m.get("description") or m.get("fact_key") for m in (e.get("ceiling_missing_facts") or [])],
                authority_warning=next((w for w in (e.get("warnings") or []) if "Authority provenance incomplete" in w), None),
                program_slug=e.get("program_slug"),
                category=(CAT_LEADING if code == leader else CAT_STRONG if (e.get("savings_vs_current_usd") or 0) > 0 else CAT_REFERENCE),
            )
        else:
            r = rows_by_juris.get(code) or {}
            pot = r.get("incentive_potential") or {}
            detail = r.get("blocker_detail") or {}
            rec.update(
                program_slug=r.get("program_slug"), confirmed_incentive_usd=pot.get("confirmed_incentive_floor_usd"),
                potential_incentive_usd=pot.get("maximum_supported_incentive_usd"), potential_npc_usd=pot.get("potential_npc_usd"),
                economic_certainty=pot.get("economics_certainty"),
                missing_conditions=[p.get("description") or p.get("fact_key") for p in (detail.get("unresolved_propositions") or [])],
                hard_failure_reason=r.get("hard_block_reason"),
                authority_warning=detail.get("provenance_axis") if disp == "NEEDS_FACTS" else None,
            )
            rec["category"] = (CAT_CONDITIONAL if disp == "NEEDS_FACTS" else CAT_UNAVAILABLE if disp == "HARD_BLOCK"
                               else CAT_NOT_SUITABLE if disp == "NOT_APPLICABLE" else CAT_DATA_INCOMPLETE)
        out.append(rec)
    # confirmed and potential rankings are SEPARATE (ascending NPC); a conditional alternative can lead potential only
    for key, field in (("confirmed_rank", "confirmed_npc_usd"), ("potential_rank", "potential_npc_usd")):
        ranked = sorted((r for r in out if r.get(field) is not None), key=lambda r: (r[field], r["jurisdiction_code"]))
        for i, r in enumerate(ranked, start=1):
            r[key] = i
    for r in out:
        r.setdefault("confirmed_rank", None)
        r.setdefault("potential_rank", None)
    return out


# ── Four-project reconciliation ────────────────────────────────────────────────────────────────────────────────────
CAUSE_THRESHOLD = "BUDGET_QPE_THRESHOLD"
CAUSE_PRODUCTION_TYPE = "PRODUCTION_TYPE"
CAUSE_PROJECT_FACT = "PROJECT_FACT"
CAUSE_CULTURAL = "CULTURAL_NATIONALITY_RESIDENCY_FACT"
CAUSE_DATE = "DATE_FUNDING_PERIOD"
CAUSE_USER_EXCLUSION = "USER_EXCLUSION"
CAUSE_COMPOSITION = "BUDGET_CATEGORY_COMPOSITION"
CAUSE_HOME = "PROJECT_HOME_JURISDICTION"
CAUSE_UNATTRIBUTED = "UNATTRIBUTED_DEFECT"
APPROVED_CAUSES = (CAUSE_THRESHOLD, CAUSE_PRODUCTION_TYPE, CAUSE_PROJECT_FACT, CAUSE_CULTURAL, CAUSE_DATE, CAUSE_USER_EXCLUSION,
                   CAUSE_COMPOSITION, CAUSE_HOME)


def program_status(rec: dict) -> str:
    """The comparable per-project status of one examined program row of the accounting ledger."""
    return f"{rec.get('disposition')}:{rec.get('stage')}"


def _component_basis_categories(slug: str) -> frozenset[str]:
    """The spend categories a program's rate is restricted to (RateCondition.component_basis_spend_categories)."""
    from app.data.program_rate_rules import get_rate_rules

    return frozenset(c for r in get_rate_rules(slug) for cond in r.conditions
                     for c in (cond.component_basis_spend_categories or ()))


def reconcile_project_differences(ledgers: dict[str, dict], *, production_types: dict[str, str] | None = None,
                                  home_jurisdictions: dict[str, str] | None = None,
                                  stored_facts: dict[str, frozenset] | None = None,
                                  category_spend: dict[str, dict[str, float]] | None = None) -> list[dict]:
    """For every program whose status is not identical across the projects, name the ONE approved cause. A difference
    with no approved cause is returned as UNATTRIBUTED_DEFECT (and must be repaired, never explained away)."""
    names = sorted(ledgers)
    by_prog: dict[str, dict[str, dict]] = {}
    for n in names:
        for rec in ledgers[n].get("programs") or []:
            key = rec.get("program_slug") or f"catalog:{rec['jurisdiction_code']}"
            by_prog.setdefault(key, {})[n] = rec
    out: list[dict] = []
    for key, per in sorted(by_prog.items()):
        statuses = {n: program_status(per[n]) for n in names if n in per}
        missing = [n for n in names if n not in per]
        if len(set(statuses.values())) <= 1 and not missing:
            continue
        cause, why = CAUSE_UNATTRIBUTED, "no approved cause matches"
        ptypes = {(production_types or {}).get(n) for n in names}
        if missing:
            cause, why = CAUSE_UNATTRIBUTED, f"program absent from the examined universe of {missing}"
        elif len(ptypes - {None}) > 1:
            cause, why = CAUSE_PRODUCTION_TYPE, f"production types differ: {sorted(p for p in ptypes if p)}"
        else:
            texts = " | ".join(str(per[n].get("exit_reason") or "") for n in names).lower()
            homes = {n: (home_jurisdictions or {}).get(n) for n in names}
            if any(per[n]["jurisdiction_code"] == homes.get(n) for n in names):
                cause, why = CAUSE_HOME, "the program's jurisdiction is a project's own home (baseline single-country candidate)"
            elif "qualification gate" in texts or "role_qualification" in texts or "hard_fail" in texts:
                cause, why = CAUSE_CULTURAL, ("a mandatory cultural / nationality / residency qualification (e.g. CAVCO key-creative "
                                              "nationality) fails on this project's evidenced people and passes where none is evidenced")
            elif _component_basis_categories(key) and any(
                not any((category_spend or {}).get(n, {}).get(c, 0.0) > 0 for c in _component_basis_categories(key)) for n in names
            ):
                cause, why = CAUSE_COMPOSITION, (f"the program's rate is restricted to {sorted(_component_basis_categories(key))} spend, which at "
                                                 "least one project's budget does not contain")
            elif "qualifying spend" in texts or "minimum" in texts or "threshold" in texts or "cannot be met" in texts:
                cause, why = CAUSE_THRESHOLD, "a mandatory qualifying-spend / threshold gate passes in one project and fails in another"
            elif len({frozenset((stored_facts or {}).get(n, ())) for n in names}) > 1:
                cause, why = CAUSE_PROJECT_FACT, "the projects store different facts the program names"
        out.append({"program_slug": key, "statuses": statuses, "cause": cause, "cause_detail": why,
                    "attributed": cause in APPROVED_CAUSES})
    return out
