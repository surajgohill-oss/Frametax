"""
coverage_report.py

Deterministic coverage report for the global incentive inventory.
No DB access. Pure Python — operates on GlobalProgramEntry / CostBenchmarkEntry lists.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.data.global_inventory import (
    ALL_BENCHMARKS,
    ALL_PROGRAMS,
    CostBenchmarkEntry,
    GlobalProgramEntry,
)

REPORT_VERSION = "0.2.0"

# Fields required for a program to be promotable from DISCOVERY to PARSED
_PROMOTABLE_REQUIRED_FIELDS = frozenset([
    "base_rate",
    "is_refundable",
    "requires_local_entity",
    "source_url",
])

# Fields required for a program to be promotable from PARSED to VERIFIED
_VERIFIED_REQUIRED_FIELDS = frozenset([
    "base_rate",
    "max_rate",
    "is_refundable",
    "is_transferable",
    "requires_local_entity",
    "min_spend_usd",
    "requires_cultural_test",
    "effective_from",
    "source_url",
    "source_title",
])


@dataclass
class JurisdictionCoverage:
    jurisdiction_code: str
    jurisdiction_name: str
    program_count: int
    benchmark_count: int
    # Confidence tier counts (across programs + benchmarks combined)
    verified_count: int
    parsed_count: int
    discovery_count: int
    # Unknown fields aggregated from programs in this jurisdiction
    unknown_fields: list[str] = field(default_factory=list)
    # Gaps preventing real-world budget testing
    budget_testing_blockers: list[str] = field(default_factory=list)


@dataclass
class CoverageReport:
    report_version: str
    total_jurisdictions: int
    total_programs: int
    total_benchmarks: int
    verified_programs: int
    parsed_programs: int
    discovery_programs: int
    verified_benchmarks: int
    parsed_benchmarks: int
    discovery_benchmarks: int
    by_jurisdiction: list[JurisdictionCoverage]


_BUDGET_TEST_REQUIRED_PROGRAM_FIELDS = [
    "confirmed_rate",
    "annual_cap",
    "minimum_spend_threshold",
    "processing_timeline",
]

_BUDGET_TEST_REQUIRED_BENCHMARK_FIELDS = [
    "crew_rate_multiplier",
    "equipment_rental_multiplier",
]


def _budget_testing_blockers(
    prog: Optional[GlobalProgramEntry],
    bm: Optional[CostBenchmarkEntry],
) -> list[str]:
    blockers: list[str] = []
    if prog is None:
        blockers.append("no_incentive_program_seeded")
        return blockers
    if prog.confidence_tier == "DISCOVERY":
        blockers.append(f"program_rate_unverified (tier=DISCOVERY, rate={prog.base_rate})")
    if prog.base_rate is None:
        blockers.append("base_rate_unknown")
    if "confirmed_rate" in (prog.unknown_fields or []):
        blockers.append("confirmed_rate_unknown")
    if "annual_cap" in (prog.unknown_fields or []) and prog.annual_cap_usd is None:
        blockers.append("annual_cap_unknown (cannot model oversubscription risk)")
    if "processing_timeline" in (prog.unknown_fields or []):
        blockers.append("processing_timeline_unknown (cannot model finance cost)")
    if bm is None:
        blockers.append("no_cost_benchmark_seeded")
    elif bm.crew_rate_multiplier is None:
        blockers.append("crew_rate_multiplier_unknown")
    return blockers


def build_coverage_report(
    programs: list[GlobalProgramEntry] | None = None,
    benchmarks: list[CostBenchmarkEntry] | None = None,
) -> CoverageReport:
    """
    Build a jurisdiction-level coverage report from the global inventory.
    Defaults to ALL_PROGRAMS and ALL_BENCHMARKS if not supplied.
    """
    if programs is None:
        programs = ALL_PROGRAMS
    if benchmarks is None:
        benchmarks = ALL_BENCHMARKS

    # Index by jurisdiction_code
    bm_by_code: dict[str, list[CostBenchmarkEntry]] = {}
    for bm in benchmarks:
        bm_by_code.setdefault(bm.jurisdiction_code, []).append(bm)

    prog_by_code: dict[str, list[GlobalProgramEntry]] = {}
    for p in programs:
        prog_by_code.setdefault(p.jurisdiction_code, []).append(p)

    all_codes_ordered: list[str] = []
    seen: set[str] = set()
    for p in programs:
        if p.jurisdiction_code not in seen:
            all_codes_ordered.append(p.jurisdiction_code)
            seen.add(p.jurisdiction_code)
    for bm in benchmarks:
        if bm.jurisdiction_code not in seen:
            all_codes_ordered.append(bm.jurisdiction_code)
            seen.add(bm.jurisdiction_code)

    by_jur: list[JurisdictionCoverage] = []
    total_verified_prog = total_parsed_prog = total_discovery_prog = 0
    total_verified_bm = total_parsed_bm = total_discovery_bm = 0

    for code in all_codes_ordered:
        jur_progs = prog_by_code.get(code, [])
        jur_bms = bm_by_code.get(code, [])

        verified = parsed = discovery = 0
        for p in jur_progs:
            if p.confidence_tier == "VERIFIED":
                verified += 1
                total_verified_prog += 1
            elif p.confidence_tier == "PARSED":
                parsed += 1
                total_parsed_prog += 1
            else:
                discovery += 1
                total_discovery_prog += 1

        for bm in jur_bms:
            if bm.confidence_tier == "VERIFIED":
                total_verified_bm += 1
                verified += 1
            elif bm.confidence_tier == "PARSED":
                total_parsed_bm += 1
                parsed += 1
            else:
                total_discovery_bm += 1
                discovery += 1

        # Aggregate unknown fields
        all_unknown: list[str] = []
        for p in jur_progs:
            for uf in (p.unknown_fields or []):
                if uf not in all_unknown:
                    all_unknown.append(uf)

        jur_name = jur_progs[0].jurisdiction_name if jur_progs else code
        first_prog = jur_progs[0] if jur_progs else None
        first_bm = jur_bms[0] if jur_bms else None

        by_jur.append(JurisdictionCoverage(
            jurisdiction_code=code,
            jurisdiction_name=jur_name,
            program_count=len(jur_progs),
            benchmark_count=len(jur_bms),
            verified_count=verified,
            parsed_count=parsed,
            discovery_count=discovery,
            unknown_fields=all_unknown,
            budget_testing_blockers=_budget_testing_blockers(first_prog, first_bm),
        ))

    return CoverageReport(
        report_version=REPORT_VERSION,
        total_jurisdictions=len(all_codes_ordered),
        total_programs=len(programs),
        total_benchmarks=len(benchmarks),
        verified_programs=total_verified_prog,
        parsed_programs=total_parsed_prog,
        discovery_programs=total_discovery_prog,
        verified_benchmarks=total_verified_bm,
        parsed_benchmarks=total_parsed_bm,
        discovery_benchmarks=total_discovery_bm,
        by_jurisdiction=by_jur,
    )


def get_promotable_programs(
    programs: list[GlobalProgramEntry] | None = None,
) -> list[GlobalProgramEntry]:
    """
    Return DISCOVERY programs that have enough data to be promoted to PARSED.
    A program is promotable if all _PROMOTABLE_REQUIRED_FIELDS are non-None/non-empty
    and it is not already PARSED or VERIFIED.
    """
    if programs is None:
        programs = ALL_PROGRAMS
    promotable = []
    for p in programs:
        if p.confidence_tier != "DISCOVERY":
            continue
        missing = _missing_promotable_fields(p)
        if not missing:
            promotable.append(p)
    return promotable


def _missing_promotable_fields(p: GlobalProgramEntry) -> list[str]:
    missing = []
    if p.base_rate is None:
        missing.append("base_rate")
    if p.is_refundable is None:
        missing.append("is_refundable")
    if p.source_url is None:
        missing.append("source_url")
    return missing


def _missing_verified_fields(p: GlobalProgramEntry) -> list[str]:
    missing = []
    if p.base_rate is None:
        missing.append("base_rate")
    if p.max_rate is None:
        missing.append("max_rate")
    if p.is_refundable is None:
        missing.append("is_refundable")
    if p.is_transferable is None:
        missing.append("is_transferable")
    if p.source_url is None:
        missing.append("source_url")
    if p.effective_from is None:
        missing.append("effective_from")
    return missing


@dataclass
class GapAnalysis:
    """High-value gaps blocking database completeness."""
    programs_missing_source_url: list[str]       # jurisdiction_codes
    programs_missing_base_rate: list[str]
    programs_missing_refundability: list[str]
    programs_promotable_to_parsed: list[str]
    jurisdictions_missing_benchmark: list[str]
    total_discovery_programs: int
    total_parsed_programs: int
    total_verified_programs: int


def build_gap_analysis(
    programs: list[GlobalProgramEntry] | None = None,
    benchmarks: list[CostBenchmarkEntry] | None = None,
) -> GapAnalysis:
    """
    Identify the highest-priority gaps in the inventory.
    Returns a structured analysis of what's missing and what's promotable.
    """
    if programs is None:
        programs = ALL_PROGRAMS
    if benchmarks is None:
        benchmarks = ALL_BENCHMARKS

    bm_codes = {bm.jurisdiction_code for bm in benchmarks}

    missing_url = []
    missing_rate = []
    missing_refundability = []
    promotable = []
    discovery = parsed = verified = 0

    for p in programs:
        if p.confidence_tier == "DISCOVERY":
            discovery += 1
        elif p.confidence_tier == "PARSED":
            parsed += 1
        elif p.confidence_tier == "VERIFIED":
            verified += 1

        if p.source_url is None:
            missing_url.append(p.jurisdiction_code)
        if p.base_rate is None:
            missing_rate.append(p.jurisdiction_code)
        if p.is_refundable is None:
            missing_refundability.append(p.jurisdiction_code)
        if p.confidence_tier == "DISCOVERY" and not _missing_promotable_fields(p):
            promotable.append(p.jurisdiction_code)

    # Jurisdictions with programs but no benchmark
    prog_codes = {p.jurisdiction_code for p in programs}
    missing_bm = sorted(prog_codes - bm_codes)

    return GapAnalysis(
        programs_missing_source_url=missing_url,
        programs_missing_base_rate=missing_rate,
        programs_missing_refundability=missing_refundability,
        programs_promotable_to_parsed=promotable,
        jurisdictions_missing_benchmark=missing_bm,
        total_discovery_programs=discovery,
        total_parsed_programs=parsed,
        total_verified_programs=verified,
    )


def format_coverage_table(report: CoverageReport) -> str:
    """Render a plain-text summary table for the coverage report."""
    lines = [
        f"Global Incentive Coverage Report v{report.report_version}",
        f"Jurisdictions: {report.total_jurisdictions}  "
        f"Programs: {report.total_programs}  "
        f"Benchmarks: {report.total_benchmarks}",
        f"Programs — VERIFIED: {report.verified_programs}  "
        f"PARSED: {report.parsed_programs}  "
        f"DISCOVERY: {report.discovery_programs}",
        f"Benchmarks — VERIFIED: {report.verified_benchmarks}  "
        f"PARSED: {report.parsed_benchmarks}  "
        f"DISCOVERY: {report.discovery_benchmarks}",
        "",
        f"{'Code':<6} {'Name':<30} {'Progs':>5} {'Bmarks':>6} {'V':>3} {'P':>3} {'D':>3} {'Blockers':>8}",
        "-" * 72,
    ]
    for jc in report.by_jurisdiction:
        lines.append(
            f"{jc.jurisdiction_code:<6} {jc.jurisdiction_name:<30} "
            f"{jc.program_count:>5} {jc.benchmark_count:>6} "
            f"{jc.verified_count:>3} {jc.parsed_count:>3} {jc.discovery_count:>3} "
            f"{len(jc.budget_testing_blockers):>8}"
        )
    return "\n".join(lines)
