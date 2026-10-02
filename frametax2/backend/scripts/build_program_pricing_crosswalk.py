"""Builds docs/validation/FOUR_PROJECT_PROGRAM_PRICING_RECONCILIATION_CLAUDE.csv (one canonical program per row).

Read-only: the four acceptance productions' CURRENT generations (no evaluation is run), the accounting ledger
(services/jurisdiction_accounting.py) and the treatment crosswalk (services/program_pricing_crosswalk.py).

    DATABASE_URL=postgresql+psycopg://.../frametax2_claude_optimizer_acceptance_20260919 python scripts/build_program_pricing_crosswalk.py
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
import uuid
from collections import Counter
from pathlib import Path

ACCEPTANCE_DB = "frametax2_claude_optimizer_acceptance_20260919"
assert os.environ.get("DATABASE_URL", "").endswith(ACCEPTANCE_DB), "refusing to run outside the acceptance database"

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.project import Project  # noqa: E402
from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint  # noqa: E402
from app.services.canonical_project_economics import _FORMAT_TO_PRODUCTION_TYPE, build_project_economic_inputs  # noqa: E402
from app.services.jurisdiction_accounting import build_jurisdiction_accounting  # noqa: E402
from app.services.program_pricing_crosswalk import (  # noqa: E402
    all_program_treatments, program_status, reconcile_project_differences,
)

PROJECTS = {
    "LU": "fa5cade5-0669-4816-bfe6-72146f8d3bae",
    "FVD": "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",
    "BH": "4355ae88-a636-4c18-af60-ad73b2646124",
    "LLS": "ab10b319-978e-44d3-9331-af2a5f2cccc2",
}
#: the Codex B1 ruling (e0a8caa) blocked these 25 rate-bearing programs AFTER the accepted two-axis baseline (6b44973)
PRE_RECONCILIATION_B1 = frozenset({
    "ae_ad_film_rebate", "al_cash_rebate", "be_tax_shelter", "ca_sk_creative_saskatchewan_grant", "ch_pics_national_rebate",
    "cr_tax_return_incentive", "de_dfff", "dk_production_rebate", "eg_empc_cashback", "gh_film_tax_incentive",
    "il_foreign_production_fund", "in_national_film", "lu_filmfund_tax_shelter_rebate", "no_film_incentive", "pa_film_rebate",
    "ph_fdcp_flip", "qa_screen_production_incentive", "sa_film_commission_rebate", "se_production_rebate",
    "sg_made_with_singapore_rebate", "tw_bamid_rebate", "us_wa_mpcp", "uy_acau_cash_rebate",
})
REPAIRED = frozenset({
    "ae_ad_film_rebate", "al_cash_rebate", "be_tax_shelter", "ch_pics_national_rebate", "de_dfff", "dk_production_rebate",
    "eg_empc_cashback", "gh_film_tax_incentive", "il_foreign_production_fund", "in_national_film", "pa_film_rebate",
    "ph_fdcp_flip", "qa_screen_production_incentive", "us_wa_mpcp", "uy_acau_cash_rebate",
})

CORRECTED = {
    "DETERMINISTIC_PRICEABLE": "PRICED (confirmed floor + NPC) when project thresholds pass",
    "PRICEABLE_WITH_PROVENANCE_WARNING": "PRICED with an authority/provenance warning (never RECOMMENDED / knowledge-verified)",
    "CONDITIONAL_TIER": "PRICED at the confirmed floor; maximum + exact facts served (Conditional)",
    "DISCRETIONARY_ZERO_GUARANTEED": "Conditional Alternative: confirmed $0, maximum potential from canonical QPE x stored ceiling, award/approval facts named",
    "PROJECT_FACT_REQUIRED": "Conditional Alternative: economics conditional on the named project facts",
    "ECONOMIC_MECHANICS_INCOMPLETE": "Visible with the exact missing mechanic; no invented calculation",
    "SUPERSEDED_DUPLICATE_NOT_APPLICABLE": "Excluded with the specific reason (superseded / duplicate / production type)",
}


async def main(out: Path) -> dict:
    ledgers: dict[str, dict] = {}
    ptypes: dict[str, str] = {}
    homes: dict[str, str] = {}
    cat_spend: dict[str, dict[str, float]] = {}
    async with AsyncSessionLocal() as s:
        for name, pid in PROJECTS.items():
            project = await s.get(Project, uuid.UUID(pid))
            fp = await current_generation_fingerprint(s, uuid.UUID(pid))
            ptype = _FORMAT_TO_PRODUCTION_TYPE.get((project.format or "").lower(), "feature_film")
            ledger = await build_jurisdiction_accounting(s, project, fp, ENGINE_VERSION, production_type=ptype)
            assert ledger is not None, f"{name}: no current generation (regenerate once first)"
            ledgers[name], ptypes[name] = ledger, ptype
            homes[name] = ledger["home_jurisdiction"]
            econ = await build_project_economic_inputs(s, uuid.UUID(pid))
            spend: dict[str, float] = {}
            for line in econ.inputs.budget_lines:
                if not line.is_memo and line.spend_category:
                    spend[line.spend_category] = spend.get(line.spend_category, 0.0) + float(line.amount_usd or 0.0)
            cat_spend[name] = spend
    diffs = {d["program_slug"]: d for d in reconcile_project_differences(ledgers, production_types=ptypes, home_jurisdictions=homes, category_spend=cat_spend)}
    by_slug = {n: {r["program_slug"]: r for r in L["programs"] if r.get("program_slug")} for n, L in ledgers.items()}
    rows = []
    for t in all_program_treatments("feature_film"):
        slug = t["program_slug"]
        row = {
            "canonical_program_slug": slug, "alias_slugs": ";".join(t["alias_slugs"]), "jurisdiction": t["jurisdiction_code"],
            "production_type_applicability": ";".join(t["production_types"]),
            "deterministic_floor_rate": t["deterministic_floor_rate"], "supported_maximum_rate": t["supported_maximum_rate"],
            "minimum_spend_usd": t["minimum_spend_usd"], "per_project_cap_usd": t["per_project_cap_usd"],
            "annual_program_cap_usd": t["annual_program_cap_usd"], "required_project_facts": ";".join(t["required_project_facts"]),
            "authority_coverage_state": t["authority_coverage_state"], "rate_rule_confidence": ";".join(t["rate_rule_confidence"]),
            "provenance_warning": t["provenance_warning"], "current_authority_block": t["authority_block"] or "",
            "prior_accepted_pricing_status": (
                "PRICED at the accepted 6b44973 two-axis baseline; blocked later by the Codex B1 ruling (e0a8caa)"
                if slug in PRE_RECONCILIATION_B1 else "unchanged since the accepted baseline"),
            "economic_treatment": t["treatment"], "treatment_reason": t["treatment_reason"],
        }
        for n in PROJECTS:
            rec = by_slug[n].get(slug)
            row[f"status_{n}"] = program_status(rec) if rec else "NOT_EXAMINED"
            row[f"detail_{n}"] = (rec.get("exit_reason") or "")[:160] if rec else ""
        d = diffs.get(slug)
        row["cross_project_difference_cause"] = d["cause"] if d else "NONE_IDENTICAL"
        row["cross_project_difference_reason"] = d["cause_detail"] if d else ""
        row["unjustified_blocker_repaired"] = "YES (removed from the B1 ruling, engine 1.103.0)" if slug in REPAIRED else ""
        row["required_corrected_disposition"] = CORRECTED[t["treatment"]]
        rows.append(row)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # pairwise exact set differences of the confirmed-priceable / conditional / hard sets
    def sets(n):
        pr = {p["program_slug"] for p in ledgers[n]["programs"] if p.get("program_slug") and p["disposition"] == "EXECUTABLE"}
        co = {p["program_slug"] for p in ledgers[n]["programs"] if p.get("program_slug") and p["disposition"] == "NEEDS_FACTS"}
        hd = {p["program_slug"] for p in ledgers[n]["programs"] if p.get("program_slug") and p["disposition"] == "HARD_BLOCK"}
        return {"priced": pr, "conditional": co, "hard": hd}
    S = {n: sets(n) for n in PROJECTS}
    pair = {}
    names = list(PROJECTS)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pair[f"{a}-vs-{b}"] = {k: {"only_" + a: sorted(S[a][k] - S[b][k]), "only_" + b: sorted(S[b][k] - S[a][k])} for k in S[a]}
    summary = {
        "engine_version": ENGINE_VERSION, "rows": len(rows),
        "treatment_counts": dict(Counter(r["economic_treatment"] for r in rows)),
        "per_project_disposition": {n: ledgers[n]["waterfall"]["jurisdiction_disposition_counts"] for n in PROJECTS},
        "per_project_stage": {n: ledgers[n]["waterfall"]["first_exit_stage_counts"] for n in PROJECTS},
        "differences": list(diffs.values()), "unattributed": [d for d in diffs.values() if not d["attributed"]],
        "pairwise_set_differences_sizes": {k: {kk: {a: len(b) for a, b in vv.items()} for kk, vv in v.items()} for k, v in pair.items()},
    }
    (out.with_suffix(".summary.json")).write_text(json.dumps({**summary, "pairwise": pair}, indent=1, default=str))
    return summary


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "docs/validation/FOUR_PROJECT_PROGRAM_PRICING_RECONCILIATION_CLAUDE.csv"
    print(json.dumps(asyncio.run(main(target)), indent=1, default=str))
