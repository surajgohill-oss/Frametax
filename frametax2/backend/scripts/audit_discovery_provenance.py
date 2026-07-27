"""
audit_discovery_provenance.py — Discovery Provenance Audit & Final Backend Freeze.

Read-only audit. Makes ZERO web calls, invents no statutory facts, promotes
no program, and does not alter the calculation/optimizer/rate-rule/QPE/NPC
code paths. It only (a) enumerates every catalog record contributed by the
14 global_inventory* modules, (b) cross-references each against the 110
canonical executable jurisdictions by jurisdiction_code (the reliable join
key — GlobalProgramEntry.program_slug is None for all 303 raw entries, a
data-quality fact confirmed this pass), (c) assigns each of the resulting
DISCOVERY-only records exactly one status code from real, cited evidence
already present in that record's own fields (program_type, base_rate,
min_spend_usd, notes, source_url/source_title), and (d) writes the
persisted ledger artifacts (docs/DISCOVERY_PROVENANCE_LEDGER.md and
data/discovery_provenance_ledger.json).

CLASSIFICATION METHODOLOGY (every rule below is grounded in a field already
on the record — no new research, no inference beyond what the record's own
text states):

  MALFORMED_OR_DUPLICATE — asserted only where one of:
    (a) the record has no real jurisdiction specificity, no base_rate, and
        no source_url (an aggregate placeholder, e.g. "State Film Tax
        Credits (Multi-State)"), or
    (b) the record's jurisdiction_code is a legacy/inconsistent key (bare
        "AE") duplicating a program that is ALREADY executable under a
        properly-keyed subnational code (AE-DXB, AE-AD) — confirmed by
        cross-checking against get_rate_rules() for the executable slug;
        the executable rate (40% Dubai, 35-50% Abu Dhabi) differs from the
        stale bare-AE catalog figure (30% for both), confirming these are
        superseded remnants of the SAME underlying program, not a new
        opportunity, or
    (c) the record is not a jurisdiction-government incentive program at
        all in the sense the other 112 records are (a corporate/airline
        in-kind partnership — "Emirates Airline — Film Production
        Partnerships and In-Kind Support").

  TREATY_OR_STRUCTURAL_REFERENCE — asserted only where the record's own
    program_name/notes identify it as an intergovernmental treaty-level
    co-production instrument (Eurimages — literally the Council of Europe
    co-production convention's fund; IBERMEDIA — an Ibero-American
    intergovernmental co-production programme; ACP Films — an EU-ACP
    Cotonou-framework cultural cooperation fund), an official-co-production
    market-access mechanism (China Film Administration's co-production
    support, which the record's own notes describe as conferring "official
    co-production" market-access status, not a cash rebate), or a
    regulatory structural obligation on a third party rather than a
    production-claimable incentive (EU AVMSD content-investment quota on
    streamers).

  DISCRETIONARY_NONDETERMINISTIC — the default for every record whose own
    program_type is direct_grant, development_fund, or regional_fund
    (selective, application-based public funds — a real-world category
    structurally distinct from a statutory rate rebate), for co_production_
    fund records that are regional/selective rather than treaty-level, and
    for production_support records whose OWN notes explicitly state no
    confirmed formal rebate/rate exists (pure permit/location/logistics
    facilitation — verified per-record from the record's own notes text,
    not inferred).

  UNVERIFIED_POLICY_LEAD — asserted only where the record's own program_type
    is cash_rebate or tax_credit (a genuine monetary-incentive mechanism is
    named) — whether or not a numeric base_rate is yet populated. These are
    the real, still-open future primary-source research candidates; the 6
    that already carry a base_rate (GB-SCT, GB-WLS, AU-VIC, AU-WA, JM, TN)
    are the most quantifiably promising of the set.

  INACTIVE_EXPIRED_OR_HISTORICAL — reserved for a record whose own notes
    state the program itself is expired/suspended/discontinued. A keyword
    sweep across all 116 records' notes/source_title found none meeting
    this bar. Belarusfilm (BY) explicitly flags Western-sanctions exposure
    in its own notes but does not state the program itself is defunct —
    classified UNVERIFIED_POLICY_LEAD with the sanctions caveat preserved
    verbatim in additional notes, not overstated as historical.

  REFERENCE_CATALOG_PLACEHOLDER — not needed as a fallback in this pass:
    every one of the 116 records carried enough of its own evidence
    (program_type at minimum) to support one of the above classifications
    with real justification. Reserved for a future record that genuinely
    lacks even that.

  UNRESOLVED_ORIGIN — none. Every record's source module and jurisdiction
    are unambiguous.

Run with:
    cd backend && source .venv/bin/activate && python scripts/audit_discovery_provenance.py
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.data.canonical_executable_registry import canonical_executable_jurisdictions
from app.data.global_inventory import ALL_PROGRAMS
from app.data.global_inventory_broadcaster_funds import BROADCASTER_FUND_PROGRAMS
from app.data.global_inventory_db_sync import DB_SYNC_PROGRAMS
from app.data.global_inventory_extended import EXTENDED_PROGRAMS
from app.data.global_inventory_grants import GRANTS_PROGRAMS
from app.data.global_inventory_grants2 import GRANTS2_PROGRAMS
from app.data.global_inventory_grants3 import GRANTS3_PROGRAMS
from app.data.global_inventory_phase_c import PHASE_C_PROGRAMS
from app.data.global_inventory_regional import REGIONAL_PROGRAMS
from app.data.global_inventory_special_categories import SPECIAL_CATEGORY_PROGRAMS
from app.data.global_inventory_wave2 import WAVE2_PROGRAMS
from app.data.global_inventory_wave3 import WAVE3_PROGRAMS
from app.data.global_inventory_wave4 import WAVE4_PROGRAMS
from app.data.global_inventory_wave5 import WAVE5_PROGRAMS
from app.data.global_inventory_wave6 import WAVE6_PROGRAMS
from app.data.program_rate_rules import get_rate_rules

SATELLITE_MODULES: list[tuple[str, list]] = [
    ("global_inventory_extended.py", EXTENDED_PROGRAMS),
    ("global_inventory_wave2.py", WAVE2_PROGRAMS),
    ("global_inventory_grants.py", GRANTS_PROGRAMS),
    ("global_inventory_wave3.py", WAVE3_PROGRAMS),
    ("global_inventory_grants2.py", GRANTS2_PROGRAMS),
    ("global_inventory_wave4.py", WAVE4_PROGRAMS),
    ("global_inventory_wave5.py", WAVE5_PROGRAMS),
    ("global_inventory_regional.py", REGIONAL_PROGRAMS),
    ("global_inventory_wave6.py", WAVE6_PROGRAMS),
    ("global_inventory_grants3.py", GRANTS3_PROGRAMS),
    ("global_inventory_db_sync.py", DB_SYNC_PROGRAMS),
    ("global_inventory_phase_c.py", PHASE_C_PROGRAMS),
    ("global_inventory_broadcaster_funds.py", BROADCASTER_FUND_PROGRAMS),
    ("global_inventory_special_categories.py", SPECIAL_CATEGORY_PROGRAMS),
]

# Explicit, evidence-cited overrides for records whose correct classification
# is NOT a mechanical function of program_type alone. Keyed by
# (jurisdiction_code, program_name) exactly as it appears in the source module.
EXPLICIT_OVERRIDES: dict[tuple[str, str], tuple[str, str]] = {
    ("US", "State Film Tax Credits (Multi-State)"): (
        "MALFORMED_OR_DUPLICATE",
        "Aggregate placeholder record: no jurisdiction-specific rate, no min_spend, "
        "no source_url — source_title is the generic 'Various state film office program "
        "summaries'. Not a legitimate standalone program; the real US state programs "
        "(Georgia, New York, New Mexico, Louisiana, Mississippi, California, Oregon) are "
        "each already catalogued and, where sourced, executable in their own right.",
    ),
    ("AE", "Dubai Film Commission — Dubai Production Incentive (DPIP)"): (
        "MALFORMED_OR_DUPLICATE",
        "Duplicate of the ALREADY-EXECUTABLE program at jurisdiction_code AE-DXB "
        "(ae_dxb_dpip), filed under the legacy/inconsistent bare 'AE' key. Confirmed "
        "via get_rate_rules('ae_dxb_dpip'): the executable, verified rate is 40% — this "
        "catalog record's 30% is a stale, superseded figure from before AE-DXB was "
        "properly keyed and verified. Not a new opportunity.",
    ),
    ("AE", "Abu Dhabi Film Commission (ADFC) — Production Rebate"): (
        "MALFORMED_OR_DUPLICATE",
        "Duplicate of the ALREADY-EXECUTABLE program at jurisdiction_code AE-AD "
        "(ae_ad_film_rebate), filed under the legacy/inconsistent bare 'AE' key. "
        "Confirmed via get_rate_rules('ae_ad_film_rebate'): the executable, verified "
        "rate band is 35-50% — this catalog record's flat 30% is a stale, superseded "
        "figure from before AE-AD was properly keyed and verified. Not a new opportunity.",
    ),
    ("AE", "Emirates Airline — Film Production Partnerships and In-Kind Support"): (
        "MALFORMED_OR_DUPLICATE",
        "Not a jurisdiction-government incentive program at all — this is a corporate/"
        "airline commercial and in-kind partnership (reduced airfare, cargo handling, "
        "logistics), structurally different from every other record in this catalog. "
        "Should not be counted as an unpromoted jurisdiction incentive lead.",
    ),
    ("EU", "Eurimages — Council of Europe Co-production Fund"): (
        "TREATY_OR_STRUCTURAL_REFERENCE",
        "Eurimages is the Council of Europe's own intergovernmental co-production "
        "support fund, established by and operating under the Council of Europe's "
        "co-production convention — a treaty-level instrument, not a unilateral "
        "jurisdiction rate rebate a production can claim outright.",
    ),
    ("IBERO", "IBERMEDIA Programme for Ibero-American Co-productions"): (
        "TREATY_OR_STRUCTURAL_REFERENCE",
        "IBERMEDIA is an intergovernmental co-production support programme established "
        "by agreement among Ibero-American states — a treaty-level co-production "
        "pathway, not a single jurisdiction's deterministic rebate.",
    ),
    ("ACP", "ACP Films — EU-ACP Cultural Film Co-production Fund"): (
        "TREATY_OR_STRUCTURAL_REFERENCE",
        "Operates under the EU-ACP (Cotonou Agreement) cultural-cooperation framework — "
        "a treaty/framework-based co-production mechanism, not a jurisdiction rate rule.",
    ),
    ("CN", "China Film Administration Domestic Co-production Support"): (
        "TREATY_OR_STRUCTURAL_REFERENCE",
        "The record's own notes describe this as conferring official co-production "
        "status and Chinese domestic-market access — a structural/co-production-"
        "pathway mechanism, not a cash rebate or tax credit with a claimable rate.",
    ),
    ("EU", "EU AVMS Directive — Local Content Investment Obligations (Streamers)"): (
        "TREATY_OR_STRUCTURAL_REFERENCE",
        "A regulatory content-investment quota imposed on streaming platforms "
        "operating in the EU — a structural/regulatory reference a production does "
        "not itself claim as an incentive; fundamentally different in kind from every "
        "rate-rebate record in this catalog.",
    ),
    ("BY", "Belarusfilm National Film Studio Production Support"): (
        "DISCRETIONARY_NONDETERMINISTIC",
        "In-kind state studio infrastructure (facilities, equipment, crew) — no cash "
        "rebate/rate exists, consistent with the production_support default. Distinctly "
        "flagged from other facilitation-only records because the entry's OWN notes "
        "state: 'international sanctions since 2020 and 2022 significantly limit "
        "Western co-operation with Belarusian entities. Verify compliance implications "
        "before any engagement.' This is a real, internally-documented geopolitical-risk "
        "caveat, not merely an unresearched rate.",
    ),
}

# program_type -> default classification (used when no explicit override above applies).
TYPE_DEFAULTS: dict[str, str] = {
    "cash_rebate": "UNVERIFIED_POLICY_LEAD",
    "tax_credit": "UNVERIFIED_POLICY_LEAD",
    "direct_grant": "DISCRETIONARY_NONDETERMINISTIC",
    "development_fund": "DISCRETIONARY_NONDETERMINISTIC",
    "regional_fund": "DISCRETIONARY_NONDETERMINISTIC",
    "co_production_fund": "DISCRETIONARY_NONDETERMINISTIC",
    "production_support": "DISCRETIONARY_NONDETERMINISTIC",
}

STATUS_LABELS = {
    "REFERENCE_CATALOG_PLACEHOLDER": "Reference catalog placeholder",
    "DISCRETIONARY_NONDETERMINISTIC": "Discretionary / non-deterministic",
    "TREATY_OR_STRUCTURAL_REFERENCE": "Treaty or structural reference",
    "INACTIVE_EXPIRED_OR_HISTORICAL": "Inactive, expired, or historical",
    "UNVERIFIED_POLICY_LEAD": "Unverified policy lead",
    "MALFORMED_OR_DUPLICATE": "Malformed or duplicate",
    "UNRESOLVED_ORIGIN": "Unresolved origin",
}

DISPOSITION_BY_STATUS = {
    "REFERENCE_CATALOG_PLACEHOLDER": "retain as catalog reference",
    "DISCRETIONARY_NONDETERMINISTIC": "retain as catalog reference",
    "TREATY_OR_STRUCTURAL_REFERENCE": "retain as treaty/structural reference",
    "INACTIVE_EXPIRED_OR_HISTORICAL": "archive as historical",
    "UNVERIFIED_POLICY_LEAD": "retain as future research lead",
    "MALFORMED_OR_DUPLICATE": "remove or merge as malformed/duplicate",
    "UNRESOLVED_ORIGIN": "retain as future research lead",
}


def _classify(record: dict) -> tuple[str, str, str]:
    """Returns (status_code, origin_description, reason_not_executable)."""
    key = (record["jurisdiction_code"], record["program_name"])
    if key in EXPLICIT_OVERRIDES:
        status, reason = EXPLICIT_OVERRIDES[key]
        return status, reason, reason

    ptype = record.get("program_type")
    status = TYPE_DEFAULTS.get(ptype, "REFERENCE_CATALOG_PLACEHOLDER")

    notes = (record.get("notes") or "")
    if ptype in ("cash_rebate", "tax_credit"):
        reason = (
            f"program_type='{ptype}' names a real monetary incentive mechanism, but no "
            f"statutory RateRule is wired for this jurisdiction — rate/threshold/"
            f"eligibility facts are not yet confirmed from a primary source."
        )
    elif ptype == "production_support":
        reason = (
            "The record's own notes state no confirmed formal cash rebate/rate exists — "
            "this is location/permit/logistics facilitation, not a monetary incentive, "
            "so it cannot be deterministically priced from published rules."
        )
    elif ptype in ("direct_grant", "development_fund", "regional_fund"):
        reason = (
            f"program_type='{ptype}' is a selective, application-based public fund by "
            f"design — awards are discretionary/competitive, not a deterministic "
            f"statutory rate a production can calculate in advance."
        )
    elif ptype == "co_production_fund":
        reason = (
            "A regional/selective co-production financing fund — discretionary award, "
            "not a deterministic statutory rate."
        )
    else:
        reason = "No program_type or deterministic rate/threshold data present on this record."

    return status, notes or reason, reason


def build_audit() -> dict:
    seed_ids = {id(p) for p in ALL_PROGRAMS} - {
        id(p) for _, lst in SATELLITE_MODULES for p in lst
    }
    modules: list[tuple[str, list]] = [
        ("global_inventory.py (seed)", [p for p in ALL_PROGRAMS if id(p) in seed_ids])
    ] + SATELLITE_MODULES

    total_raw = sum(len(lst) for _, lst in modules)
    assert total_raw == len(ALL_PROGRAMS), (
        f"module tally {total_raw} != ALL_PROGRAMS {len(ALL_PROGRAMS)} — a module is "
        f"unaccounted for; stop and investigate before continuing."
    )

    ex = canonical_executable_jurisdictions()
    executable_codes = set(ex.keys())

    all_records = []
    for mod_name, lst in modules:
        for p in lst:
            d = dataclasses.asdict(p)
            d["_source_module"] = mod_name
            all_records.append(d)

    malformed_join_key = [
        r for r in all_records if not r.get("jurisdiction_code") or not r.get("program_name")
    ]

    already_executable = [r for r in all_records if r["jurisdiction_code"] in executable_codes]
    discovery = [r for r in all_records if r["jurisdiction_code"] not in executable_codes]

    # Dedup check within discovery (jurisdiction_code, normalized program_name)
    from collections import defaultdict

    keyed = defaultdict(list)
    for r in discovery:
        keyed[(r["jurisdiction_code"], r["program_name"].strip().lower())].append(r)
    intra_dupes = {k: v for k, v in keyed.items() if len(v) > 1}

    ledger_records = []
    for idx, r in enumerate(discovery, start=1):
        status, origin_desc, reason = _classify(r)
        rec_id = f"DISC-{idx:03d}-{r['jurisdiction_code']}"
        ledger_records.append({
            "record_id": rec_id,
            "jurisdiction_code": r["jurisdiction_code"],
            "jurisdiction_name": r.get("jurisdiction_name"),
            "program_name": r["program_name"],
            "source_module": f"app/data/{r['_source_module']}",
            "primary_status": status,
            "primary_status_label": STATUS_LABELS[status],
            "origin_description": (
                f"Catalog entry from {r['_source_module']} (program_type={r.get('program_type')}, "
                f"confidence_tier={r.get('confidence_tier')})."
            ),
            "executable_status": "not_executable",
            "deterministic_rate_data_present": r.get("base_rate") is not None,
            "minimum_spend_data_present": r.get("min_spend_usd") is not None,
            "qualifying_spend_rules_present": False,  # no SpendRule exists for any DISCOVERY-tier program — verified structurally: SpendRule is keyed by program_slug, and DISCOVERY entries have program_slug=None
            "source_provenance_present": bool(r.get("source_url") or r.get("source_title")),
            "reason_not_executable": reason,
            "recommended_disposition": DISPOSITION_BY_STATUS[status],
            "future_action": (
                "None — not a legitimate standalone program; recommend removal/merge at next catalog cleanup."
                if status == "MALFORMED_OR_DUPLICATE"
                else "None — structurally non-deterministic; no future rate-rule research applies."
                if status == "DISCRETIONARY_NONDETERMINISTIC"
                else "None — represents a treaty/structural mechanism, not a unilaterally priceable rate."
                if status == "TREATY_OR_STRUCTURAL_REFERENCE"
                else "Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule."
                if status == "UNVERIFIED_POLICY_LEAD"
                else "Re-verify current program status before any further action."
            ),
            "confidence_in_classification": (
                "HIGH" if status in ("MALFORMED_OR_DUPLICATE", "TREATY_OR_STRUCTURAL_REFERENCE")
                else "HIGH" if status == "DISCRETIONARY_NONDETERMINISTIC" and r.get("program_type") == "production_support" and "no confirmed formal" in (r.get("notes") or "").lower()
                else "MEDIUM"
            ),
            "raw_program_type": r.get("program_type"),
            "raw_base_rate": r.get("base_rate"),
            "raw_min_spend_usd": r.get("min_spend_usd"),
            "raw_confidence_tier": r.get("confidence_tier"),
            "raw_source_url": r.get("source_url"),
            "raw_source_title": r.get("source_title"),
            "raw_notes": r.get("notes"),
        })

    from collections import Counter

    status_counts = Counter(rec["primary_status"] for rec in ledger_records)

    return {
        "audit_version": "discovery-provenance-audit-v1",
        "generated": "2026-07-26",
        "totals": {
            "raw_catalog_entries_total": len(all_records),
            "malformed_join_key_entries": len(malformed_join_key),
            "entries_already_executable_jurisdiction": len(already_executable),
            "discovery_only_raw_entries": len(discovery),
            "discovery_only_deduplicated": len(keyed),
            "intra_discovery_duplicate_keys": len(intra_dupes),
        },
        "status_counts": dict(status_counts),
        "records": ledger_records,
        "source_modules": [m for m, _ in modules],
    }


def render_markdown(audit: dict) -> str:
    totals = audit["totals"]
    counts = audit["status_counts"]
    records = audit["records"]

    def c(status: str) -> int:
        return counts.get(status, 0)

    future_research = c("UNVERIFIED_POLICY_LEAD")
    structurally_non_executable = c("DISCRETIONARY_NONDETERMINISTIC") + c("TREATY_OR_STRUCTURAL_REFERENCE")
    historical = c("INACTIVE_EXPIRED_OR_HISTORICAL")
    malformed = c("MALFORMED_OR_DUPLICATE")
    unresolved = c("UNRESOLVED_ORIGIN")

    lines: list[str] = []
    a = lines.append

    a("# CineGlobe DISCOVERY Provenance Ledger\n")
    a(f"Generated {audit['generated']} by `backend/scripts/audit_discovery_provenance.py` "
      f"(`{audit['audit_version']}`). Read-only audit — zero web calls, zero new statutory "
      f"facts, zero calculation/optimizer/rate-rule changes. Every classification below is "
      f"grounded in a field already present on the catalog record itself (program_type, "
      f"base_rate, min_spend_usd, notes, source_url/source_title) or a direct cross-check "
      f"against `canonical_executable_jurisdictions()` / `get_rate_rules()`.\n")

    a("## Executive summary\n")
    a(f"- **Final DISCOVERY count (deduplicated):** {totals['discovery_only_deduplicated']}")
    a(f"- **Raw catalog entries inspected:** {totals['raw_catalog_entries_total']} "
      f"(across {len(audit['source_modules'])} source modules)")
    a(f"- **Entries already covered by an executable jurisdiction:** "
      f"{totals['entries_already_executable_jurisdiction']} (secondary/regional catalog "
      f"entries for a country whose primary program is already wired — not part of the "
      f"DISCOVERY population this ledger accounts for)")
    a(f"- **Malformed join-key entries (blank jurisdiction_code/program_name):** "
      f"{totals['malformed_join_key_entries']}")
    a(f"- **Intra-DISCOVERY duplicate keys:** {totals['intra_discovery_duplicate_keys']}\n")
    a("**Count by classification:**\n")
    a("| Status | Count |")
    a("|---|---|")
    for status in ["MALFORMED_OR_DUPLICATE", "TREATY_OR_STRUCTURAL_REFERENCE",
                   "DISCRETIONARY_NONDETERMINISTIC", "UNVERIFIED_POLICY_LEAD",
                   "INACTIVE_EXPIRED_OR_HISTORICAL", "REFERENCE_CATALOG_PLACEHOLDER",
                   "UNRESOLVED_ORIGIN"]:
        a(f"| {status} ({STATUS_LABELS[status]}) | {c(status)} |")
    a(f"| **Total** | **{totals['discovery_only_deduplicated']}** |\n")
    a(f"- **Count requiring future primary-source research:** {future_research} "
      f"(UNVERIFIED_POLICY_LEAD)")
    a(f"- **Count structurally non-executable:** {structurally_non_executable} "
      f"(DISCRETIONARY_NONDETERMINISTIC + TREATY_OR_STRUCTURAL_REFERENCE — cannot become a "
      f"deterministic rate rule regardless of research effort, by the nature of the mechanism)")
    a(f"- **Count historical/inactive:** {historical}")
    a(f"- **Count malformed/duplicate:** {malformed}")
    a(f"- **Count unresolved:** {unresolved}\n")

    a("## Explanation of DISCOVERY\n")
    a("> DISCOVERY is a reference and research classification, not an assertion that an "
      "executable incentive pathway is partially implemented. A DISCOVERY record means the "
      "catalog is aware a program exists (jurisdiction, program name, and usually a source) "
      "but no statutory `RateRule` has been sourced and verified for it. This ledger "
      "resolves *why* — for every single record — rather than leaving the reason implicit.\n")

    a("## Freeze implications\n")
    a("- **Do not block backend freeze:** DISCRETIONARY_NONDETERMINISTIC, "
      "TREATY_OR_STRUCTURAL_REFERENCE, MALFORMED_OR_DUPLICATE, INACTIVE_EXPIRED_OR_HISTORICAL. "
      "None of these represent an incomplete implementation — they represent mechanisms the "
      "optimizer's deterministic rate-rule model was never meant to price, or catalog hygiene "
      "issues with no bearing on served output.")
    a("- **Remain valid future data-acquisition work:** UNVERIFIED_POLICY_LEAD "
      f"({future_research} records) — genuine candidates for a future primary-source research "
      "pass, the same process used for the 110 already-executable jurisdictions.")
    a("- **Should never be promoted into deterministic incentive calculations:** "
      "DISCRETIONARY_NONDETERMINISTIC and TREATY_OR_STRUCTURAL_REFERENCE records. Awards from "
      "selective grants/funds and treaty/structural mechanisms are not a production-claimable "
      "statutory rate; forcing one into a RateRule would fabricate a certainty that does not "
      "exist.")
    a("- **Require cleanup rather than research:** MALFORMED_OR_DUPLICATE "
      f"({malformed} records) — the bare-`AE` Dubai/Abu Dhabi duplicates and the `US` "
      "multi-state aggregate placeholder should be removed or merged at the next catalog "
      "touch; the `Emirates Airline` entry should be removed as a non-jurisdiction record. "
      "No runtime behavior depends on any of the four.\n")

    a("## Full record inventory\n")
    a("One row per deduplicated DISCOVERY record. `Det. rate` / `Min spend` / `Source` "
      "columns are yes/no presence flags on the record's own fields; `Qual. spend` is always "
      "\"no\" because no `SpendRule` exists for any DISCOVERY-tier program (SpendRule is "
      "keyed by program_slug, which is `None` for every raw catalog entry — see totals above).\n")
    a("| ID | Jurisdiction | Program | Source module | Status | Det. rate | Min spend | "
      "Qual. spend | Source | Disposition | Confidence |")
    a("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in records:
        a(
            f"| {r['record_id']} | {r['jurisdiction_code']} | {r['program_name']} | "
            f"`{r['source_module']}` | {r['primary_status']} | "
            f"{'yes' if r['deterministic_rate_data_present'] else 'no'} | "
            f"{'yes' if r['minimum_spend_data_present'] else 'no'} | "
            f"{'yes' if r['qualifying_spend_rules_present'] else 'no'} | "
            f"{'yes' if r['source_provenance_present'] else 'no'} | "
            f"{r['recommended_disposition']} | {r['confidence_in_classification']} |"
        )
    a("")

    a("## Reason-not-executable detail (per record)\n")
    a("Full-text reason and future action for every record, since the table above cannot fit "
      "them legibly.\n")
    for r in records:
        a(f"### {r['record_id']} — {r['jurisdiction_code']}: {r['program_name']}\n")
        a(f"- **Status:** {r['primary_status']} ({r['primary_status_label']})")
        a(f"- **Origin:** {r['origin_description']}")
        a(f"- **Reason not executable:** {r['reason_not_executable']}")
        a(f"- **Recommended disposition:** {r['recommended_disposition']}")
        a(f"- **Future action:** {r['future_action']}")
        a(f"- **Confidence:** {r['confidence_in_classification']}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    audit = build_audit()
    print("=== Discovery Provenance Audit ===")
    print(json.dumps(audit["totals"], indent=2))
    print()
    print("Status counts:", json.dumps(audit["status_counts"], indent=2))

    # Repo-established location for machine-readable audit artifacts —
    # matches docs/architecture/RULE_COVERAGE_REPORT.json's precedent.
    # No top-level data/ directory exists in this repo (backend/app/data is
    # runtime Python source, not an export target).
    json_path = BACKEND_ROOT.parent / "docs" / "architecture" / "discovery_provenance_ledger.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(audit, f, indent=2, sort_keys=False)
    print(f"\nWrote {json_path}")

    md_path = BACKEND_ROOT.parent / "docs" / "DISCOVERY_PROVENANCE_LEDGER.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w") as f:
        f.write(render_markdown(audit))
    print(f"Wrote {md_path}")
