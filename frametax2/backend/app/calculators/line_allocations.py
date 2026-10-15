"""Several identified people on ONE budget line (NA-RECONCILIATION-25), through the existing ProjectFact `line_fact` owner.

Storage: one JSON row per line, `line_fact:<line id>:allocations` = a list of person allocations. No new table: a line is one budget row and its people are a small ordered list attached to it. An allocation carries the
person (`payee_id`), the compensation attributable to them on this line (`amount_usd`), and, when relevant, the person-level facts a rule reads from an allocation (payee type, Montana residency, withholding,
student / veteran-tribal status, producer position, composer portion) with their evidence. Rules:
  * the allocations of a line sum to at most the line amount; the remainder is explicit and Unknown (never assigned to anyone);
  * one person appears once per line, and one person is one person across lines (a global ordinal by identity), so a per-person cap applies to the person's total, never twice;
  * a person has exactly one Montana category across the project (student and veteran / tribal are exclusive; one residency; withholding is stated per person);
  * an existing single-person row (`payee_id` + `payee_compensation_complete`) reads as one allocation of the whole line, unchanged; saving allocations for a line replaces it; Reset deletes the allocations row.
Pure functions only; no database.
"""
from __future__ import annotations

import json
import math
from typing import Iterable

FIELD = "allocations"
PERSON_FIELDS = ("payee_type", "mt_residency", "mt_tax_withheld", "mt_status", "producer_role", "composer_compensation_usd")   # only person-level facts a rule reads from an allocation (a fact with no consumer is not offered);
# the Canadian labour-basis facts (role, status, service location, payment status, look-through wages, assistance, related party) are still read per LINE.
EVIDENCE_METHODS = ("PRODUCER_ASSERTED", "PAYROLL_DOCUMENT", "DEAL_MEMO", "AUTHORITY_DETERMINATION")
EVIDENCE_CONFIDENCES = ("STATED", "DOCUMENTED", "AUTHORITATIVE")
_TYPE_CODES = {"employee": 1, "individual_contractor": 2, "loan_out_corp": 3, "personal_service_corp": 4, "partnership": 5}


def parse_rows(fact_rows, line_ids: set[str]) -> dict[str, list[dict]]:
    """{line id: allocations} from the JSON rows; a malformed row is dropped (never repaired)."""
    out: dict[str, list[dict]] = {}
    for row in fact_rows:
        key = getattr(row, "fact_key", "") or ""
        if not key.startswith("line_fact:") or not key.endswith(":" + FIELD):
            continue
        line_id = key[len("line_fact:"):-len(FIELD) - 1]
        if line_id not in line_ids or not getattr(row, "value", None):
            continue
        try:
            data = json.loads(row.value)
        except (TypeError, ValueError):
            continue
        if isinstance(data, list):
            out[line_id] = [a for a in data if isinstance(a, dict) and str(a.get("payee_id") or "").strip()]
    return out


def validate(line_id: str, line_amount: float, allocations: list[dict], specs: dict) -> list[dict]:
    """The stored form of one line's allocations; ValueError with the reason on any invalid entry. `specs` = line_inputs.field_specs()."""
    from app.services.line_inputs import validate_line_fact
    if len(allocations) > 50:
        raise ValueError(f"line {line_id}: at most 50 people on one line")
    seen, total, out = set(), 0.0, []
    for raw in allocations:
        pid = str(raw.get("payee_id") or "").strip()
        if not pid or len(pid) > 120:
            raise ValueError(f"line {line_id}: each person needs a name or id of at most 120 characters")
        if pid.lower() in seen:
            raise ValueError(f"line {line_id}: {pid} appears twice on the line; one person is counted once")
        seen.add(pid.lower())
        amount = raw.get("amount_usd")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
            raise ValueError(f"line {line_id}: {pid}: the compensation on this line must be a finite number of at least 0 (the part of the line not assigned to anyone stays Unknown)")
        total += float(amount)
        entry = {"payee_id": pid, "amount_usd": round(float(amount), 2)}
        for name in PERSON_FIELDS:
            value = raw.get(name)
            if value is None:
                continue
            spec = specs[name]
            text = validate_line_fact(spec, value, float(amount), line_id)
            if text is not None:
                entry[name] = value
        ev = raw.get("evidence") or {}
        if ev:
            if not str(ev.get("source") or "").strip():
                raise ValueError(f"line {line_id}: {pid}: evidence needs its source")
            if ev.get("method") not in EVIDENCE_METHODS or ev.get("confidence") not in EVIDENCE_CONFIDENCES:
                raise ValueError(f"line {line_id}: {pid}: evidence needs a method {EVIDENCE_METHODS} and a confidence {EVIDENCE_CONFIDENCES}")
            entry["evidence"] = {k: ev.get(k) for k in ("source", "method", "confidence", "date") if ev.get(k)}
        out.append(entry)
    if total > line_amount + 0.005:
        raise ValueError(f"line {line_id}: the people carry {total:,.2f}, more than the line amount {line_amount:,.2f}")
    return out


def check_across_lines(all_by_line: dict[str, list[dict]]) -> None:
    """ValueError when one person would sit in two mutually exclusive Montana categories or hold two residencies across lines."""
    seen: dict[str, dict] = {}
    for line_id, allocations in all_by_line.items():
        for a in allocations:
            pid = a["payee_id"].lower()
            for name, label in (("mt_status", "student / veteran-tribal / neither category"), ("mt_residency", "residency")):
                if a.get(name) is None:
                    continue
                prior = seen.setdefault(pid, {}).get(name)
                if prior is not None and prior[0] != a[name]:
                    raise ValueError(f"{a['payee_id']} is stated as '{prior[0]}' on line {prior[1]} and '{a[name]}' on line {line_id}: a person is assigned to exactly one {label}")
                seen[pid][name] = (a[name], line_id)


def person_ordinals(names: Iterable[str]) -> dict[str, float]:
    return {n: float(i + 1) for i, n in enumerate(sorted({n for n in names}))}


def amount_facts(by_line: dict[str, list[dict]], ordinals: dict[str, float], line_amounts: dict[str, float] | None) -> dict[str, float]:
    """Numeric facts the pricing reads: alloc_n:<line>, alloc_ord / alloc_usd / alloc_type / alloc_mtstatus / alloc_withheld / alloc_res : <line>:<k>. When one person holds the whole line, the legacy single-person facts
    are emitted too, so every consumer of the single-person facts (New York above-the-line limits) keeps working unchanged."""
    out: dict[str, float] = {}
    for line_id, allocations in by_line.items():
        if not allocations:
            continue
        out[f"alloc_n:{line_id}"] = float(len(allocations))
        for k, a in enumerate(allocations):
            out[f"alloc_ord:{line_id}:{k}"] = ordinals[a["payee_id"]]
            out[f"alloc_usd:{line_id}:{k}"] = float(a["amount_usd"])
            if a.get("payee_type") in _TYPE_CODES:
                out[f"alloc_type:{line_id}:{k}"] = float(_TYPE_CODES[a["payee_type"]])
            if a.get("mt_status") in ("none", "student", "veteran_tribal"):
                out[f"alloc_mtstatus:{line_id}:{k}"] = {"none": 0.0, "student": 1.0, "veteran_tribal": 2.0}[a["mt_status"]]
            if a.get("mt_tax_withheld") in (True, False):
                out[f"alloc_withheld:{line_id}:{k}"] = 1.0 if a["mt_tax_withheld"] else 0.0
            if a.get("mt_residency") in ("resident", "nonresident"):
                out[f"alloc_res:{line_id}:{k}"] = 1.0 if a["mt_residency"] == "resident" else 2.0
        whole = line_amounts and len(allocations) == 1 and allocations[0]["amount_usd"] + 0.005 >= line_amounts.get(line_id, float("inf"))
        if whole:
            a = allocations[0]
            out[f"ny_atl_payee:{line_id}"] = ordinals[a["payee_id"]]
            if a.get("payee_type") in _TYPE_CODES:
                out[f"payee_type_code:{line_id}"] = float(_TYPE_CODES[a["payee_type"]])
            if a.get("mt_status") in ("none", "student", "veteran_tribal"):
                out[f"mt_status_code:{line_id}"] = {"none": 0.0, "student": 1.0, "veteran_tribal": 2.0}[a["mt_status"]]
            if a.get("mt_tax_withheld") in (True, False):
                out[f"mt_tax_withheld:{line_id}"] = 1.0 if a["mt_tax_withheld"] else 0.0
            if a.get("mt_residency") in ("resident", "nonresident"):
                out[f"mt_residency_code:{line_id}"] = 1.0 if a["mt_residency"] == "resident" else 2.0
            if a.get("composer_compensation_usd") is not None:
                out[f"ny_composer_portion:{line_id}"] = float(a["composer_compensation_usd"])
    return out


def allocations_of(amounts: dict, line_id: str) -> list[dict]:
    """The allocation facts of one line as [{ordinal, usd, type_code, mt_status, withheld, residency}] (empty when the line has none)."""
    n = int(amounts.get(f"alloc_n:{line_id}", 0) or 0)
    return [{"ordinal": int(amounts[f"alloc_ord:{line_id}:{k}"]), "usd": float(amounts[f"alloc_usd:{line_id}:{k}"]), "type_code": amounts.get(f"alloc_type:{line_id}:{k}"),
             "mt_status": amounts.get(f"alloc_mtstatus:{line_id}:{k}"), "withheld": amounts.get(f"alloc_withheld:{line_id}:{k}"), "residency": amounts.get(f"alloc_res:{line_id}:{k}")} for k in range(n)
            if f"alloc_ord:{line_id}:{k}" in amounts]
