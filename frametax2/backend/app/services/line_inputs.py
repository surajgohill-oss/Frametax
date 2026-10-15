"""Line-level producer inputs through the existing canonical owners (NA-RECONCILIATION-24).

Storage is unchanged: ProjectFact rows `line_fact:<budget line id>:<field>` and the JSON row `uplift_basis_subsets`; the budget lines are `BudgetLineItem`. This module adds (1) the field catalogue - which line facts exist, their vocabularies,
which programs and budget categories CONSUME them (read from the canonical registries, so a field is offered only where a rule reads it) - (2) one validated writer that `write_ny_program_facts` calls, and (3) the served picker view.
A fact with no canonical consumer is not offered. Unknown (no row) is never False; a stated False is stored as `false`.

Consumers: Canadian labour basis (CPTC / PSTC / BC / Manitoba qualified labour: role, status, service location, payee type, payment status, look-through wages, PSC profit element, assistance, related party);
per-payee limits (Georgia, Colorado, New Jersey, Arkansas, Illinois, Nova Scotia's per-individual cap, New York's above-the-line limits, Montana's per-person credit caps: payee id + complete compensation); producer position
(Nova Scotia second-position limit, New York producer role); composer portion (New York music accounts); Montana status / withholding / residency; qualifying portion (`uplift_basis_subsets`, Arkansas and every
subset uplift).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.project_fact import ProjectFact

PERSONNEL = frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor"})
CANADIAN_PROGRAMS = ("ca_federal_cptc", "ca_federal_pstc", "ca_bc_pstc", "ca_bc_film_tv_tax_credit", "ca_bc_dave", "ca_mb_film_video_credit")
CANADIAN_PAYEE_TYPES = ("employee", "individual_contractor", "loan_out_corp", "personal_service_corp", "partnership", "non_taxable_canadian_corp", "foreign_corp")
MT = "us_mt_media_act_tax_credit"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str
    kind: str                       # enum | boolean | number | text
    choices: tuple = ()
    programs: tuple = ()            # programs whose rules read it
    categories: frozenset = frozenset()
    consumer: str = ""
    help: str = ""
    max_line_amount: bool = False   # a USD amount that cannot exceed the line


def _payee_programs() -> tuple:
    from app.calculators.per_payee_limits import PAYEE_CAPS
    import app.data.program_rate_rules as r
    return tuple(sorted(set(PAYEE_CAPS) | set(r.SUBSET_INDIVIDUAL_INCENTIVE_CAPS) | {"ny_state_film", MT}))


def field_specs() -> dict[str, FieldSpec]:
    import app.data.program_rate_rules as r
    from app.calculators.canadian_labour_basis import _ELIGIBLE_LABOUR_SPEND_CATEGORIES as LABOUR
    payee = _payee_programs()
    ca, lab = CANADIAN_PROGRAMS, frozenset(LABOUR)
    specs = [
        FieldSpec("payee_id", "Person / payee", "text", programs=payee, categories=PERSONNEL, consumer="per-payee limits and per-person caps",
                  help="A name or id for the individual paid on this line. The same text on several lines is the same person."),
        FieldSpec("payee_compensation_complete", "This line is the person's whole compensation", "boolean", programs=payee, categories=PERSONNEL, consumer="per-payee limits and per-person caps",
                  help="Yes only when no other person is paid from this line. A person's total is then the sum of their lines."),
        FieldSpec("payee_type", "Payee type", "enum", choices=CANADIAN_PAYEE_TYPES, programs=tuple(sorted(set(payee) | set(ca))), categories=PERSONNEL, consumer="payee-type limits and the Canadian labour basis"),
        FieldSpec("producer_role", "Producer position", "enum", choices=("executive", "line", "other"), programs=("ny_state_film", *r.SUBSET_PRODUCER_POSITION_LIMITS), categories=frozenset({"atl_producer"}),
                  consumer="producer position limits (Nova Scotia second position; New York)"),
        FieldSpec("composer_compensation_usd", "Composer compensation inside this music account (USD)", "number", programs=("ny_state_film",), categories=frozenset({"music", "sound"}),
                  consumer="New York above-the-line composer portion", max_line_amount=True),
        FieldSpec("role", "Role", "enum", choices=("director", "writer", "producer", "cast", "other"), programs=ca, categories=lab, consumer="Canadian labour basis"),
        FieldSpec("canadian_status", "Canadian status", "enum", choices=("resident_citizen", "resident_pr", "nonresident"), programs=ca, categories=lab, consumer="Canadian labour basis"),
        FieldSpec("service_location", "Where the service was performed", "enum", choices=("in_canada", "outside_canada"), programs=ca, categories=lab, consumer="Canadian labour basis"),
        FieldSpec("payment_status", "Payment status", "enum", choices=("paid", "payable", "deferred", "contingent"), programs=ca, categories=lab, consumer="Canadian labour basis (deferred and contingent amounts do not count)"),
        FieldSpec("look_through_wages_usd", "Look-through wages (USD)", "number", programs=ca, categories=lab, consumer="Canadian labour basis (T1131 lines 603-607)", max_line_amount=True),
        FieldSpec("psc_profit_element_eligible", "Personal service corporation profit element is eligible", "boolean", programs=ca, categories=lab, consumer="Canadian labour basis (T1131 line 606)"),
        FieldSpec("assistance_usd", "Assistance attributable to this line (USD)", "number", programs=ca, categories=lab, consumer="Canadian labour basis (reduces eligible labour)", max_line_amount=True),
        FieldSpec("related_party", "Related-party payee", "boolean", programs=ca, categories=lab, consumer="Canadian labour basis"),
        FieldSpec("mt_residency", "Montana residency of the person", "enum", choices=("resident", "nonresident"), programs=(MT,), categories=PERSONNEL, consumer="Montana compensation category (MCA 15-31-1007(3)(b))"),
        FieldSpec("mt_tax_withheld", "Montana tax is withheld on this compensation", "boolean", programs=(MT,), categories=PERSONNEL, consumer="Montana non-resident crew and talent credits require withholding"),
        FieldSpec("mt_status", "Student, veteran or tribal member", "enum", choices=("none", "student", "veteran_tribal"), programs=(MT,), categories=PERSONNEL, consumer="Montana student (30%) and veteran / tribal (30%) categories"),
    ]
    return {s.name: s for s in specs}


def applicable_fields(program_slugs, spend_category: str | None) -> list[FieldSpec]:
    programs = set(program_slugs or ())
    return [s for s in field_specs().values() if programs & set(s.programs) and (not s.categories or (spend_category or "") in s.categories)]


def uplift_portions(program_slugs, spend_category: str | None) -> list[dict]:
    """Subset uplifts whose per-line qualifying portion the producer may state for a line of this category (SUBSET_UPLIFT_RULES kind 'subset')."""
    import app.data.program_rate_rules as r
    out = []
    for slug in program_slugs or ():
        for u in r.SUBSET_UPLIFT_RULES.get(slug, ()):
            if u.kind == "subset" and (not u.eligible_categories or (spend_category or "") in u.eligible_categories):
                out.append({"program": slug, "uplift": u.uplift_id, "rate": u.rate, "text": u.source_ref[:240]})
    return out


def _bool_text(v):
    return "true" if v is True else "false" if v is False else None


async def line_amounts(session: AsyncSession, project_id) -> dict[str, dict]:
    rows = (await session.execute(
        select(BudgetLineItem.id, BudgetLineItem.description, BudgetLineItem.spend_category, BudgetLineItem.amount_usd)
        .join(BudgetDocument, BudgetDocument.id == BudgetLineItem.budget_document_id).where(BudgetDocument.project_id == project_id))).all()
    return {str(i): {"description": d or "", "category": getattr(c, "value", c), "amount": float(a or 0.0)} for i, d, c, a in rows}


def validate_line_fact(spec: FieldSpec, value, line_amount: float, line_id: str):
    """The stored text for one value (None clears). ValueError with the reason when invalid."""
    if value is None:
        return None
    if spec.kind == "boolean":
        if value not in (True, False):
            raise ValueError(f"line {line_id}: {spec.name} must be true, false or null (Unknown)")
        return _bool_text(value)
    if spec.kind == "enum":
        if value not in spec.choices:
            raise ValueError(f"line {line_id}: {spec.name} must be one of {list(spec.choices)} or null (Unknown)")
        return value
    if spec.kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"line {line_id}: {spec.name} must be a finite number of at least 0, or null (Unknown); 0 is a real zero")
        if spec.max_line_amount and value > line_amount + 0.005:
            raise ValueError(f"line {line_id}: {spec.name} {value:,.2f} exceeds the line amount {line_amount:,.2f}")
        return repr(float(value))
    text = str(value).strip()
    if not text or len(text) > 120:
        raise ValueError(f"line {line_id}: {spec.name} must be 1 to 120 characters, or null (Unknown)")
    return text


def validate_line_facts(rows: list[dict], lines: dict[str, dict]) -> list[tuple[str, str, str | None, str]]:
    """[(line_id, field, stored text | None, value_type)] after validation of the whole request; nothing is written by this function."""
    specs = field_specs()
    out, seen = [], set()
    for row in rows:
        lid, field = str(row.get("line_id")), row.get("field")
        if lid not in lines:
            raise ValueError(f"line {lid!r} is not a line of this project's budget")
        spec = specs.get(field)
        if spec is None:
            raise ValueError(f"'{field}' is not a line-level fact")
        if (lid, field) in seen:
            raise ValueError(f"line {lid}: {field} is given twice")
        seen.add((lid, field))
        text = validate_line_fact(spec, row.get("value"), lines[lid]["amount"], lid)
        out.append((lid, field, text, {"number": "number", "boolean": "boolean"}.get(spec.kind, "string")))
    # a person marked complete needs an identified person on the same line (in this request or already stored): enforced where the stored rows are known
    return out


async def line_inputs_view(session: AsyncSession, project_id, program_slugs=None) -> dict:
    """The picker: the lines a producer can annotate for the selected programs, each with only the applicable fields, the stored value, the derived budget classification (read-only) and the persons' totals
    reconciled to their lines. Read-only; never evaluates."""
    lines = await line_amounts(session, project_id)
    rows = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key.like("line_fact:%")))).scalars().all()
    stored: dict[str, dict[str, str]] = {}
    for r_ in rows:
        lid, _, field = r_.fact_key[len("line_fact:"):].partition(":")
        if lid in lines and r_.value not in (None, ""):
            stored.setdefault(lid, {})[field] = r_.value
    portions_row = next((r_ for r_ in (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key == "uplift_basis_subsets"))).scalars().all()), None)
    import json
    from app.calculators import line_allocations as la
    stored_allocations = la.parse_rows(rows, set(lines))
    portions = json.loads(portions_row.value) if portions_row is not None and portions_row.value else {}
    out_lines, persons = [], {}
    for lid, info in lines.items():
        fields = applicable_fields(program_slugs, info["category"])
        ups = uplift_portions(program_slugs, info["category"])
        if not fields and not ups:
            continue
        values = stored.get(lid, {})
        entry = {"line_id": lid, "description": info["description"], "category": info["category"], "amount_usd": info["amount"],
                 "derived": {"category": info["category"], "note": "the budget's own classification; a stated fact never overwrites it"},
                 "fields": [{"name": s.name, "label": s.label, "kind": s.kind, "choices": list(s.choices), "consumer": s.consumer, "help": s.help, "max_usd": info["amount"] if s.max_line_amount else None,
                             "value": (None if values.get(s.name) is None else (values[s.name].lower() == "true" if s.kind == "boolean" and values[s.name].lower() in ("true", "false")
                                                                              else float(values[s.name]) if s.kind == "number" else values[s.name])),
                             "state": "UNKNOWN" if values.get(s.name) is None else "STATED"} for s in fields],
                 "portions": [{**u, "amount_usd": ((portions.get(u["program"]) or {}).get(u["uplift"]) or {}).get(lid)} for u in ups]}
        pid, done = values.get("payee_id"), values.get("payee_compensation_complete", "").lower() == "true"
        # the people on the line (only a line a person can be paid from: a rule of the selected programs reads its payee): stored allocations, else the legacy single-person row read as ONE allocation of the whole line when
        # marked complete (unchanged meaning); the rest of the line is explicit and Unknown
        people, legacy = None, False
        if any(f.name == "payee_id" for f in fields):
            people = stored_allocations.get(lid)
            if people is None and pid:
                people = [{"payee_id": pid, "amount_usd": info["amount"] if done else None, **{n: values[n] for n in la.PERSON_FIELDS if n in values and n not in ("producer_role",)}}]
                legacy = True
            assigned = sum(a["amount_usd"] or 0.0 for a in (people or []))
            person_fields = [{"name": n, "label": field_specs()[n].label, "kind": field_specs()[n].kind, "choices": list(field_specs()[n].choices)} for n in la.PERSON_FIELDS if n in {f.name for f in fields}]
            entry["allocations"] = {"people": people or [], "assigned_usd": round(assigned, 2), "unallocated_usd": round(max(info["amount"] - assigned, 0.0), 2), "legacy_single_person": legacy,
                                    "unallocated_state": "UNKNOWN" if info["amount"] - assigned > 0.005 else "NONE", "person_fields": person_fields}
        out_lines.append(entry)
        for a in (people or []):
            p = persons.setdefault(a["payee_id"], {"payee": a["payee_id"], "lines": [], "total_usd": 0.0, "complete": True})
            p["lines"].append(lid)
            p["total_usd"] = round(p["total_usd"] + (a["amount_usd"] or 0.0), 2)
            p["complete"] = p["complete"] and (not legacy or done) and a["amount_usd"] is not None
    return {"lines": out_lines, "persons": sorted(persons.values(), key=lambda x: x["payee"]),
            "note": ("Only lines and fields that a rule of the selected programs reads are offered. Unknown is not No. A person's compensation is the sum of the amounts allocated to them across lines; a line may carry several people whose amounts sum to at most the line, and the remainder is Unknown (never assigned to anyone); a person counts once; exact per-person caps apply only when every line of a category has an identified person with complete compensation, otherwise a lawful range is priced and disclosed.")}
