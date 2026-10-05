"""JURISDICTION ACCOUNTING -- the complete, mutually exclusive FIRST-EXIT waterfall of one evaluation generation
(2026-10-02).

Why this exists. The evaluator persists only a bounded decision set and counts the rest as aggregate groups; the
discovery examinations (which program/jurisdiction was examined, and why it was not priced) are not persisted at all
(`discovery.examinations` is served empty). Result: ~125 of the 231 examined programs of a production vanished
before the Globe with no accounted disposition (17 rule-rejected full relocations only existed inside aggregate groups
and 106 catalog-only jurisdictions were never persisted). This module reconstructs the ledger at SERVING time from
the same pure functions and registries the evaluator used -- it adds no rule, no rate and no pricing path:

  inputs            canonical_project_economics.build_project_economic_inputs()
  discovery         production_discovery.discover_executable_jurisdictions()  (pure; same arguments as the evaluator)
  persisted result  the generation's retained rows + candidate aggregates (exact, fingerprint/engine-scoped)
  blockers          jurisdiction_disposition (the ONE shared classifier / exact-blocker enrichment)
  potential         incentive_potential.build_program_maximum_potential (the ONE maximum-potential contract)
  content gates     program_content_gates

It is a serving-time reader and deliberately lives outside the evaluator's fingerprint-hashed modules: serving it
needs no engine bump and no regeneration.

First-exit stages (every examined program/jurisdiction row exits at EXACTLY ONE, tested in order):

  ALIAS_DUPLICATE            inventory code that is a non-canonical spelling of an existing canonical jurisdiction
  NO_PROGRAM_MODEL           catalog lead only: no rate rule / doctrine -> program/capability data incomplete
  NOT_APPLICABLE             every RateRule tier is scoped to other production types
  SUPERSEDED_OR_DUPLICATE    the canonical registry retired / superseded / duplicated the program
  AUTHORITY_BLOCKED          canonical economic block or coverage state (discretionary, exhausted, unpriceable)
  CONDITIONS_UNMET           rate rules exist but do not resolve (minimum QPE, or project-fact-dependent tiers)
  PRICING_BLOCKED            discovery-ready, but the pricing kernel did not produce a priced segment
  PRICED                     a priced full-relocation / single-country structure exists (retained)
"""
from __future__ import annotations

import dataclasses
import logging
import uuid
from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

# stages
S_ALIAS = "ALIAS_DUPLICATE"
S_NO_MODEL = "NO_PROGRAM_MODEL"
S_NOT_APPLICABLE = "NOT_APPLICABLE"
S_SUPERSEDED = "SUPERSEDED_OR_DUPLICATE"
S_AUTHORITY = "AUTHORITY_BLOCKED"
S_CONDITIONS = "CONDITIONS_UNMET"
S_PRICING = "PRICING_BLOCKED"
S_PRICED = "PRICED"
S_CONTENT_REFUSED = "MANDATORY_APPROVAL_REFUSED"
S_NOT_GENERATED = "NOT_GENERATED"   # discovery-ready but no persisted candidate (must be 0; reported if not)
STAGES = (S_ALIAS, S_NO_MODEL, S_NOT_APPLICABLE, S_SUPERSEDED, S_AUTHORITY, S_CONDITIONS, S_PRICING, S_PRICED, S_NOT_GENERATED, S_CONTENT_REFUSED)

# jurisdiction-level dispositions (the vocabulary the Globe renders)
D_EXECUTABLE = "EXECUTABLE"
D_NEEDS_FACTS = "NEEDS_FACTS"
D_HARD_BLOCK = "HARD_BLOCK"
D_DATA_INCOMPLETE = "DATA_INCOMPLETE"
D_NOT_APPLICABLE = "NOT_APPLICABLE"
D_ALIAS = "ALIAS"
_DISPOSITION_PRECEDENCE = {D_EXECUTABLE: 6, D_NEEDS_FACTS: 5, D_HARD_BLOCK: 4, D_DATA_INCOMPLETE: 3, D_NOT_APPLICABLE: 2, D_ALIAS: 1}

DATA_INCOMPLETE = "DATA_INCOMPLETE"   # served `disposition` value for a catalog-only / no-model jurisdiction

_CACHE: dict[tuple, dict] = {}
_CACHE_MAX = 8


async def _canonical_jurisdictions(session: AsyncSession) -> tuple[dict[str, str], dict[str, str]]:
    """(code -> name, lower(name) -> code) for every canonical (database) jurisdiction."""
    from app.models.jurisdiction import Jurisdiction

    rows = (await session.execute(select(Jurisdiction.code, Jurisdiction.name))).all()
    by_code = {c: n for c, n in rows if c}
    by_name = {str(n).strip().lower(): c for c, n in rows if c and n}
    return by_code, by_name


def _catalog_leads(code: str) -> list[dict]:
    from app.data import global_inventory as gi

    leads = []
    for p in gi.ALL_PROGRAMS:
        if p.jurisdiction_code == code:
            leads.append({
                "program_name": p.program_name, "stated_base_rate": p.base_rate, "stated_max_rate": p.max_rate,
                "confidence_tier": p.confidence_tier,
                "note": "Catalog lead (DISCOVERY tier): not a verified or priceable rate.",
            })
    return leads


def _alias_target(code: str, inventory_name: str | None, by_code: dict, by_name: dict) -> str | None:
    """The canonical jurisdiction a non-canonical inventory spelling denotes (name match), else None."""
    if code in by_code:
        return None
    name = (inventory_name or code or "").strip().lower()
    target = by_name.get(name)
    if target and target != code:
        return target
    return None


async def _persisted_outcomes(session: AsyncSession, project_id, fingerprint: str, engine_version: str) -> dict[tuple, dict]:
    """(jurisdiction, program) -> the generation's exact persisted full-relocation / single-country outcome."""
    from app.models.production import EvaluationCandidateAggregate, StructureCalculationResult

    out: dict[tuple, dict] = {}
    scr = StructureCalculationResult
    rows = (await session.execute(
        select(
            scr.calculation_trace_json["primary_jurisdiction"].astext,
            scr.calculation_trace_json["program_slug"].astext,
            scr.calculation_trace_json["candidate_status"].astext,
            scr.calculation_trace_json["rejection_reason_class"].astext,
            scr.calculation_trace_json["discovery_classification"].astext,
            scr.structure_id,
        ).where(
            scr.input_fingerprint == fingerprint, scr.engine_version == engine_version,
            scr.structure_type.in_(("single_country", "full_relocation")),
        )
    )).all()
    for code, slug, status, cls, disc, sid in rows:
        out[(code, slug)] = {"source": "retained", "candidate_status": status, "rejection_reason_class": cls,
                             "discovery_classification": disc, "structure_id": str(sid)}
    agg = EvaluationCandidateAggregate
    arows = (await session.execute(
        select(agg.primary_jurisdiction, agg.program_slugs, agg.candidate_status, agg.reason_class, agg.candidate_count)
        .where(agg.project_id == project_id, agg.input_fingerprint == fingerprint, agg.engine_version == engine_version,
               agg.structure_type.in_(("single_country", "full_relocation")))
    )).all()
    for code, slugs, status, cls, n in arows:
        if isinstance(slugs, list) and len(slugs) == 1:
            out.setdefault((code, slugs[0]), {
                "source": "aggregate", "candidate_status": status, "rejection_reason_class": cls,
                "discovery_classification": None, "structure_id": None,
            })
    return out


def _qpe_for(inputs, code: str, slug: str) -> float | None:
    """The production's canonical qualifying spend for (jurisdiction, program): the SAME register probe the evaluator's
    pricing preflight uses (rate-independent QPE classification)."""
    try:
        from app.calculators.qualification_derivation import QualificationState, derive_qualification_register
        from app.services.canonical_project_economics import production_facts_for

        facts = production_facts_for(inputs, jurisdiction_code=code)
        register = derive_qualification_register(
            inputs.budget_lines, program_slug=slug, facts=facts, rate=0.0, program_territorial_text=None,
        )
        return round(sum(a.amount_usd for a in register if a.state == QualificationState.QUALIFIES), 2)
    except Exception:  # noqa: BLE001 - a derivation failure must never remove the jurisdiction from the ledger
        log.exception("jurisdiction_accounting: QPE derivation failed for %s/%s", code, slug)
        return None


def _min_qpe_threshold(slug: str, production_type: str) -> float | None:
    from app.data.program_rate_rules import get_rate_rules

    mins = [r.min_qpe_usd for r in get_rate_rules(slug)
            if production_type in (r.production_types or ()) and r.min_qpe_usd is not None]
    return min(mins) if mins else None


def _threshold_unreachable_reason(inputs, slug: str, production_type: str, qpe: float | None) -> str | None:
    """None when the program WOULD resolve for this production once every project fact it names is confirmed; otherwise
    the exact mandatory threshold(s) the production cannot reach even then (a confirmed failed gate, not a missing fact)."""
    from app.data.program_rate_rules import build_discovery_amount_probe, get_rate_rules, resolve_program_rate

    rules = [r for r in get_rate_rules(slug) if production_type in (r.production_types or ())]
    if not rules:
        return None
    confirmed = frozenset(
        c.required_boolean_fact_key for r in rules for c in r.conditions if c.required_boolean_fact_key
    ) | frozenset(inputs.evidenced_program_facts)
    probe = build_discovery_amount_probe(slug, inputs.gross_budget_usd, inputs.amount_facts, inputs.fx_context)
    if resolve_program_rate(
        slug, production_type=production_type, qpe_usd=qpe, gross_budget_usd=inputs.gross_budget_usd,
        evidenced_facts=confirmed, amount_facts=probe, fx_context=inputs.fx_context,
    ) is not None:
        return None
    parts = []
    mins = [r.min_qpe_usd for r in rules if r.min_qpe_usd is not None]
    if mins and (qpe is None or qpe < min(mins)):
        parts.append(f"requires at least ${min(mins):,.2f} of qualifying spend; this production's canonical qualifying "
                     f"spend is ${(qpe or 0):,.2f}")
    for r in rules:
        for c in r.conditions:
            if c.amount_fact_key and (c.amount_fact_min is not None or c.fx_native_threshold_amount is not None):
                parts.append(f"{c.description}")
    if not parts:
        parts.append("its mandatory conditions cannot be met by this production even if every project fact were confirmed")
    return "; ".join(dict.fromkeys(parts)) + " (cannot be met even if every project fact were confirmed)."


def _refused_mandatory(slug: str | None, facts: dict) -> list[dict]:
    from app.services.program_content_gates import content_gates_for_program

    return [g for g in content_gates_for_program(slug, facts) if g["effect"] == "HARD_BLOCK"] if slug else []


def _program_name(slug: str) -> str:
    from app.services.jurisdiction_disposition import _program_label

    return _program_label(slug)


def _min_spend_threshold(slug: str, production_type: str) -> float | None:
    """The program's stated minimum qualifying/local spend (USD): the larger of the requirements profile's
    ``min_local_spend_usd``, the doctrine's ``min_spend_usd`` and the lowest applicable tier ``min_qpe_usd``."""
    from app.data.executable_jurisdiction_registry import get_doctrine
    from app.data.program_requirements import get_program_requirements

    vals = []
    p = get_program_requirements(slug)
    if p is not None and p.min_local_spend_usd:
        vals.append(float(p.min_local_spend_usd))
    d = get_doctrine(slug)
    if d is not None and getattr(d, "min_spend_usd", None):
        vals.append(float(d.min_spend_usd))
    tier_min = _min_qpe_threshold(slug, production_type)
    if tier_min:
        vals.append(float(tier_min))
    return max(vals) if vals else None


def _per_project_cap(slug: str) -> float | None:
    from app.data.program_requirements import get_program_requirements

    p = get_program_requirements(slug)
    return p.per_project_cap_usd if p is not None else None


def _disposition_for(row: dict) -> str:
    d = row.get("disposition")
    if d == "HARD_BLOCK":
        return D_HARD_BLOCK
    if d == "NOT_APPLICABLE":
        return D_NOT_APPLICABLE
    if d == DATA_INCOMPLETE:
        return D_DATA_INCOMPLETE
    return D_NEEDS_FACTS


def _accounting_row(*, code: str, name: str, slug: str | None, outcome: dict | None, reason: str, stage: str) -> dict:
    status = (outcome or {}).get("candidate_status") or "NO_PRICEABLE_PROGRAM_MODEL"
    cls = (outcome or {}).get("rejection_reason_class") or "DATA_INCOMPLETE"
    return {
        "structure_id": f"accounting:{code}:{slug or 'catalog'}",
        "name": f"Full relocation to {name}",
        "generation_ordinal": None,
        "candidate_status": status,
        "rejection_reason_class": cls,
        "true_net_cost_usd": None, "total_incentive_value_usd": None,
        "is_baseline": False, "relocation_cost_normalized": False,
        "reason": reason,
        "primary_jurisdiction": code, "participants": [code],
        "accounting_only": True, "first_exit_stage": stage,
    }


async def build_jurisdiction_accounting(
    session: AsyncSession, project, fingerprint: str, engine_version: str, *, production_type: str,
    served_blocked_rows: list[dict] | None = None,
) -> dict | None:
    """The complete first-exit ledger for one evaluation generation (cached per fingerprint + engine)."""
    key = (str(project.id), fingerprint, engine_version, production_type)
    if key in _CACHE:
        return _CACHE[key]

    from app.calculators.production_discovery import discover_executable_jurisdictions
    from app.calculators.production_normalization import build_fx_context
    from app.calculators.production_requirements import derive_production_requirements
    from app.data.authority_coverage_registry import coverage_state, economic_block_for_program
    from app.data.program_rate_rules import get_rate_rules
    from app.services import canonical_evaluation as ce
    from app.services.canonical_project_economics import build_project_economic_inputs
    from app.services.incentive_potential import build_program_maximum_potential
    from app.services.jurisdiction_disposition import (
        NEEDS_FACTS, annotate_rows, discretionary_award_fact_key, enrich_row_with_program_detail, rate_rule_fact_keys,
    )
    from app.services.program_content_gates import content_gate_summary, content_gates_for_program
    from app.models.project_fact import ProjectFact

    econ = await build_project_economic_inputs(session, project.id)
    if not econ.ok:
        return None
    inputs = dataclasses.replace(econ.inputs, fx_context=build_fx_context())
    requirements = derive_production_requirements(await ce.build_physical_requirements(session, project.id))
    kw = dict(
        production_type=inputs.production_type, qpe_usd=inputs.gross_budget_usd, home_code=inputs.jurisdiction_code,
        evidenced_facts=(inputs.evidenced_program_facts | ce._PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts, fx_context=inputs.fx_context,
    )
    economic = discover_executable_jurisdictions(requirements=derive_production_requirements({}), **kw)
    fit = discover_executable_jurisdictions(requirements=requirements, **kw)
    fit_by_pair = {(e.jurisdiction_code, e.program_slug): e for e in fit.examinations}

    by_code, by_name = await _canonical_jurisdictions(session)
    outcomes = await _persisted_outcomes(session, project.id, fingerprint, engine_version)
    served_pairs = {(r.get("primary_jurisdiction"), r.get("program_slug")) for r in (served_blocked_rows or [])}
    served_by_pair = {(r.get("primary_jurisdiction"), r.get("program_slug")): r for r in (served_blocked_rows or [])}
    all_rows: list[dict] = []

    # stored facts for every program the ledger may need to name (rate-rule facts + content-gate confirmations)
    slugs = {e.program_slug for e in economic.examinations if e.program_slug}
    fact_keys: set[str] = set()
    for s in slugs:
        fact_keys |= rate_rule_fact_keys(s)
        fact_keys.add(discretionary_award_fact_key(s))
        for g in content_gates_for_program(s):
            fact_keys.add("evidenced_program_fact:" + g["fact_key"])
    facts: dict[str, str] = {}
    if fact_keys:
        facts = {k: v for k, v in (await session.execute(
            select(ProjectFact.fact_key, ProjectFact.value)
            .where(ProjectFact.project_id == project.id, ProjectFact.fact_key.in_(fact_keys))
        )).all()}

    programs: list[dict] = []
    new_rows: list[dict] = []
    for e in economic.examinations:
        code, slug = e.jurisdiction_code, e.program_slug
        name = e.jurisdiction_name or by_code.get(code) or code
        outcome = outcomes.get((code, slug))
        rec: dict[str, Any] = {
            "jurisdiction_code": code, "jurisdiction_name": name, "program_slug": slug,
            "discovery_classification": e.classification,
            "production_capable": (fit_by_pair.get((code, slug)).production_capable if fit_by_pair.get((code, slug)) else None),
            "persisted": (outcome or {}).get("source"),
            "persisted_status": (outcome or {}).get("candidate_status"),
        }
        row: dict | None = None
        # ── first exit ──
        alias = _alias_target(code, name, by_code, by_name) if slug is None else None
        rules = get_rate_rules(slug) if slug else []
        block = economic_block_for_program(slug) if slug else None
        state = coverage_state(slug) if slug else None
        applicable = bool(rules) and any(production_type in (r.production_types or ()) for r in rules)
        if alias:
            rec.update(stage=S_ALIAS, disposition=D_DATA_INCOMPLETE, canonical_jurisdiction=alias,
                       catalog_leads=_catalog_leads(code),
                       exit_reason=f"'{code}' is a non-canonical spelling of {alias}; accounted under {alias} "
                                   "(catalog lead only: program/capability data incomplete).")
        elif slug is None or (not rules and block is None):
            leads = _catalog_leads(code)
            rec.update(stage=S_NO_MODEL, disposition=D_DATA_INCOMPLETE, catalog_leads=leads,
                       exit_reason=(
                           "Program/capability data incomplete: the catalog lists "
                           + (f"{len(leads)} lead(s) " if leads else "no program ")
                           + "but no verified rate rule or qualification doctrine exists, so nothing is priced "
                           "(never guessed)."))
            row = _accounting_row(code=code, name=name, slug=slug, outcome=outcome, reason=rec["exit_reason"], stage=S_NO_MODEL)
            row.update(disposition=DATA_INCOMPLETE, blocked_cause="MISSING_LOCATION_CAPABILITY_DATA",
                       disposition_kind="program_data_incomplete", hard_block_reason=None,
                       missing_facts_reason=rec["exit_reason"], program_slug=slug, program_name=None,
                       catalog_leads=leads,
                       blocker_detail={"reconciliation_class": "PROGRAM_DATA_INCOMPLETE", "kind": "NO_PROGRAM_MODEL",
                                       "headline": rec["exit_reason"], "unresolved_propositions": [],
                                       "stored_facts_found": [], "guaranteed_floor": "none (no priceable model)",
                                       "potential_ceiling_rate": None, "ceiling_unlocked_by": [],
                                       "provenance_axis": "Catalog lead only (DISCOVERY tier); no RateRule exists."})
        elif rules and not applicable and block is None:
            rec.update(stage=S_NOT_APPLICABLE, disposition=D_NOT_APPLICABLE,
                       exit_reason=f"Every rate tier is scoped to other production types; this production is {production_type}.")
        elif (block is not None and block.classification == "RETIRED_SUPERSEDED_IDENTITY") or state in ("SUPERSEDED", "DUPLICATE"):
            rec.update(stage=S_SUPERSEDED, disposition=D_HARD_BLOCK,
                       exit_reason="The canonical authority-coverage registry retired / superseded / duplicated this program.")
        elif outcome and outcome["candidate_status"] == "PRICED" and _refused_mandatory(slug, facts):
            # An EXPLICITLY REFUSED mandatory approval makes the program unavailable even where it priced; a missing or
            # advisory gate never does.
            gates = _refused_mandatory(slug, facts)
            msg = (f"{_program_name(slug)}: a mandatory approval was REFUSED on file ("
                   + "; ".join(g["kind"].replace("_", " ").lower() for g in gates) + "); the program is unavailable.")
            rec.update(stage=S_CONTENT_REFUSED, disposition=D_HARD_BLOCK, exit_reason=msg)
            row = _accounting_row(code=code, name=name, slug=slug, outcome=outcome, reason=msg, stage=S_CONTENT_REFUSED)
            row.update(candidate_status="MANDATORY_APPROVAL_REFUSED", rejection_reason_class="MANDATORY_APPROVAL_REFUSED",
                       disposition="HARD_BLOCK", blocked_cause="CONFIRMED_LEGAL_PROGRAM_INELIGIBILITY",
                       disposition_kind="mandatory_approval_refused", hard_block_reason=msg, missing_facts_reason=None,
                       program_slug=slug, program_name=_program_name(slug), content_gates=content_gates_for_program(slug, facts),
                       blocker_detail={"reconciliation_class": "GENUINE_HARD_FAILURE", "kind": "MANDATORY_APPROVAL_REFUSED",
                                       "headline": msg, "unresolved_propositions": [], "stored_facts_found": [],
                                       "guaranteed_floor": "none (program unavailable)", "potential_ceiling_rate": None,
                                       "ceiling_unlocked_by": [], "provenance_axis": "A producer-recorded refusal of a mandatory approval."})
            new_rows.append(row)
            all_rows.append(row)
        elif outcome and outcome["candidate_status"] == "PRICED":
            rec.update(stage=S_PRICED, disposition=D_EXECUTABLE, exit_reason="Priced: a retained executable structure exists.")
        elif outcome is None and e.classification == "incentive_ready":
            rec.update(stage=S_NOT_GENERATED, disposition=D_DATA_INCOMPLETE,
                       exit_reason="Discovery-ready but no candidate was persisted for this generation (accounting defect).")
        else:
            # blocked / unresolved: authority, rule conditions, or pricing
            cand = outcome["candidate_status"] if outcome else "RULE_REJECTED"
            cls = (outcome or {}).get("rejection_reason_class") or "STATUTORY_CONDITIONS_UNMET"
            stage = S_AUTHORITY if (block is not None or state not in (None, "PRICEABLE_VALIDATED")) \
                else S_PRICING if e.classification == "incentive_ready" and cls == "PRICING_BLOCKED" \
                else S_CONDITIONS
            qpe = _qpe_for(inputs, code, slug)
            min_qpe = _min_qpe_threshold(slug, production_type)
            reason = (e.reason if stage != S_CONDITIONS else
                      f"Statutory rate rules exist for this program but do not resolve for this production (QPE ${qpe or 0:,.2f}).")
            base = _accounting_row(code=code, name=name, slug=slug, outcome=outcome, reason=reason, stage=stage)
            base["candidate_status"] = cand
            base["rejection_reason_class"] = cls
            annotate_rows([base])
            enrich_row_with_program_detail(
                base, slug, facts, production_type, qpe_usd=qpe,
                threshold_unreachable_reason=(_threshold_unreachable_reason(inputs, slug, production_type, qpe) if stage == S_CONDITIONS else None),
            )
            disp = _disposition_for(base)
            _refused = _refused_mandatory(slug, facts)
            if _refused and disp != D_HARD_BLOCK:
                _msg = (f"{base.get('program_name') or slug}: a mandatory approval was REFUSED on file ("
                        + "; ".join(g["kind"].replace("_", " ").lower() for g in _refused) + ").")
                base.update(disposition="HARD_BLOCK", blocked_cause="CONFIRMED_LEGAL_PROGRAM_INELIGIBILITY",
                            hard_block_reason=_msg, engine_reason=base.get("missing_facts_reason"), missing_facts_reason=None)
                (base.get("blocker_detail") or {}).update(reconciliation_class="GENUINE_HARD_FAILURE", kind="MANDATORY_APPROVAL_REFUSED", headline=_msg)
                disp = D_HARD_BLOCK
            # A genuine minimum-spend exclusion: the production's canonical qualifying spend is below the program's
            # stated minimum -> confirmed hard failure with the exact numbers (never reached for a program that passes).
            _min_spend = _min_spend_threshold(slug, production_type)
            if disp == D_NEEDS_FACTS and qpe is not None and _min_spend and qpe < _min_spend:
                _msg = (f"{base.get('program_name') or slug}: requires at least ${_min_spend:,.2f} of qualifying spend; "
                        f"this production's canonical qualifying spend is ${qpe:,.2f}.")
                base.update(disposition="HARD_BLOCK", blocked_cause="CONFIRMED_LEGAL_PROGRAM_INELIGIBILITY",
                            hard_block_reason=_msg, engine_reason=base.get("missing_facts_reason"), missing_facts_reason=None)
                (base.get("blocker_detail") or {}).update(reconciliation_class="GENUINE_HARD_FAILURE", kind="MINIMUM_QUALIFYING_SPEND_NOT_MET", headline=_msg)
                disp = D_HARD_BLOCK
            detail = base.get("blocker_detail") or {}
            # SCENARIO local-BTL inference: a resident-crew percentage the producer has not evidenced is inferred for a
            # hypothetical relocation (shared owner: scenario_local_labour); cast residency is never inferred.
            if detail and code != inputs.jurisdiction_code and not inputs.scenario_btl_nonlocal:
                from app.services.scenario_local_labour import apply_scenario_crew_inference

                apply_scenario_crew_inference(detail, inputs.budget_lines)
            gates = content_gates_for_program(slug, facts)
            if gates:
                base["content_gates"] = gates
                base["content_gate_summary"] = content_gate_summary(gates)
            # content / censorship / cultural gates whose confirmation is not on file are UNRESOLVED PROPOSITIONS of the
            # jurisdiction (amber), named exactly -- never inferred from country identity, never a silent discard.
            if disp == D_NEEDS_FACTS and detail:
                for g in gates:
                    if g["status"] == "NOT_ON_FILE":
                        detail.setdefault("unresolved_propositions", []).append({
                            "condition_id": f"content-gate-{g['kind'].lower()}", "kind": "content_gate_" + g["kind"].lower(),
                            "description": g["description"], "fact_key": g["fact_key"], "stored_value": None,
                            "requirement": "confirmed", "category": g["category"],
                            "consumed_by_optimizer": g["consumed_by_optimizer"],
                        })
                detail["ceiling_unlocked_by"] = [p["condition_id"] for p in detail.get("unresolved_propositions", [])]
            # maximum-potential economics for a conditional program (never for a hard block / not applicable)
            if disp == D_NEEDS_FACTS and detail.get("potential_ceiling_rate"):
                missing = [
                    {"fact_key": p.get("fact_key"), "description": p.get("description"), "requirement": p.get("requirement"),
                     "state": "USER_FACT_REQUIRED"}
                    for p in (detail.get("unresolved_propositions") or []) if p.get("stored_value") is None
                ]
                base["incentive_potential"] = build_program_maximum_potential(
                    program_name=base.get("program_name") or slug, ceiling_rate=detail["potential_ceiling_rate"],
                    qpe_usd=qpe, gross_budget_usd=inputs.gross_budget_usd,
                    per_project_cap_usd=_per_project_cap(slug), min_qpe_usd=min_qpe, missing_facts=missing,
                )
            rec.update(stage=stage, disposition=disp, exit_reason=base.get("hard_block_reason") or base.get("missing_facts_reason") or reason,
                       blocked_cause=base.get("blocked_cause"), reconciliation_class=detail.get("reconciliation_class"))
            all_rows.append(base)
            _served = served_by_pair.get((code, slug))
            if outcome and outcome["source"] == "retained" and _served is not None:
                # already served as a retained blocked row: enrich THAT row in place with the shared potential / gates /
                # scenario assumptions / minimum-spend verdict (one owner, never two divergent copies)
                for _k in ("incentive_potential", "content_gates", "content_gate_summary", "blocker_detail", "disposition",
                           "blocked_cause", "hard_block_reason", "missing_facts_reason", "first_exit_stage"):
                    if _k in base:
                        _served[_k] = base[_k]
                row = None
            else:
                row = base
        if row is not None:
            new_rows.append(row)
        programs.append(rec)

    # A canonical jurisdiction that is reachable ONLY through a non-canonical spelling still needs its own accounted
    # row (otherwise it would vanish): serve one slate row under the canonical code.
    _own = {r["jurisdiction_code"] for r in programs if r["stage"] != S_ALIAS}
    _alias_done: set[str] = set()
    for rec in programs:
        tgt = rec.get("canonical_jurisdiction")
        if rec["stage"] == S_ALIAS and tgt and tgt not in _own and tgt not in _alias_done:
            _alias_done.add(tgt)
            tname = by_code.get(tgt) or tgt
            r = _accounting_row(code=tgt, name=tname, slug=None, outcome=None, reason=rec["exit_reason"], stage=S_ALIAS)
            r.update(disposition=DATA_INCOMPLETE, blocked_cause="MISSING_LOCATION_CAPABILITY_DATA",
                     disposition_kind="program_data_incomplete", hard_block_reason=None,
                     missing_facts_reason=rec["exit_reason"], program_slug=None, program_name=None,
                     catalog_leads=rec.get("catalog_leads") or [],
                     blocker_detail={"reconciliation_class": "PROGRAM_DATA_INCOMPLETE", "kind": "NO_PROGRAM_MODEL",
                                     "headline": rec["exit_reason"], "unresolved_propositions": [],
                                     "stored_facts_found": [], "guaranteed_floor": "none (no priceable model)",
                                     "potential_ceiling_rate": None, "ceiling_unlocked_by": [],
                                     "provenance_axis": "Catalog lead only (DISCOVERY tier); no RateRule exists."})
            new_rows.append(r)

    # ── per-jurisdiction roll-up (best disposition among its programs; alias rows count under their target) ──
    juris: dict[str, dict] = {}
    for rec in programs:
        code = rec.get("canonical_jurisdiction") or rec["jurisdiction_code"]
        j = juris.setdefault(code, {"jurisdiction_code": code, "programs": [], "disposition": D_ALIAS})
        j["programs"].append(rec["program_slug"] or rec["jurisdiction_code"])
        if _DISPOSITION_PRECEDENCE[rec["disposition"]] > _DISPOSITION_PRECEDENCE[j["disposition"]]:
            j["disposition"] = rec["disposition"]
            j["first_exit_stage"] = rec["stage"]
    # a jurisdiction whose only rows were aliases is counted by its target
    stage_counts = Counter(r["stage"] for r in programs)
    disp_counts = Counter(j["disposition"] for j in juris.values())
    ledger = {
        "engine_version": engine_version, "fingerprint": fingerprint, "production_type": production_type,
        "home_jurisdiction": inputs.jurisdiction_code, "gross_budget_usd": inputs.gross_budget_usd,
        "programs": programs, "jurisdictions": list(juris.values()),
        "rows": new_rows,
        "all_rows": all_rows + [r for r in new_rows if r not in all_rows],
        "waterfall": {
            "canonical_jurisdictions_database": len(by_code),
            "jurisdiction_codes_examined": len({r["jurisdiction_code"] for r in programs}),
            "program_rows_examined": len(programs),
            "programs_with_rate_rules": sum(1 for r in programs if r["program_slug"] and get_rate_rules(r["program_slug"])),
            "first_exit_stage_counts": {s: stage_counts.get(s, 0) for s in STAGES},
            "program_rows_reconcile": sum(stage_counts.values()) == len(programs),
            "jurisdiction_disposition_counts": dict(disp_counts),
            "jurisdictions_total": len(juris),
            "discovery": {
                "economic_pass": dict(Counter(e.classification for e in economic.examinations)),
                "feasibility_pass": dict(Counter(
                    f"{e.classification}:{'capable' if e.production_capable else 'not_capable'}" for e in fit.examinations)),
            },
            "discovery_ready_without_persisted_outcome": sum(
                1 for r in programs if r["stage"] == S_NOT_GENERATED),
        },
    }
    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = ledger
    return ledger
