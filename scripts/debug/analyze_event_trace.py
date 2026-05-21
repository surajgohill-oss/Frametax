#!/usr/bin/env python3
"""
analyze_event_trace.py

Reads backend logs, extracts emit_event_trace JSON lines, normalizes chains
by event_id, and classifies broken pipeline stages.

Usage:
  # docker-compose service name is "backend"; container is <project>-backend-1
  python3 scripts/debug/analyze_event_trace.py --docker $(docker compose ps -q backend)
  python3 scripts/debug/analyze_event_trace.py --file /path/to/backend.log
  docker compose logs backend 2>&1 | python3 scripts/debug/analyze_event_trace.py
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

STAGE_ORDER = ["INGEST", "SCHEDULER", "COLLECT", "ENRICH"]

FAILURE_CLASSES = {
    "INGEST":    ("A", "ingestion failure — TrackedEvent never created"),
    "SCHEDULER": ("B", "scheduler skip — external_event_id missing or gate blocked"),
    "COLLECT":   ("C", "collector empty result — API auth or network block"),
    "ENRICH":    ("D", "enrichment/query drop — listings written but not aggregated"),
    None:        ("E", "no stages recorded — possible frontend/API truncation"),
}


def parse_lines(lines: list[str]) -> list[dict]:
    records = []
    for line in lines:
        line = line.strip()
        idx = line.find('{"stage"')
        if idx == -1:
            idx = line.find('{"stage":')
        if idx == -1:
            continue
        try:
            record = json.loads(line[idx:])
            if "stage" in record and "event_id" in record:
                records.append(record)
        except json.JSONDecodeError:
            continue
    return records


def normalize_chains(records: list[dict]) -> dict[int, list[dict]]:
    chains: dict[int, list[dict]] = defaultdict(list)
    for r in records:
        chains[r["event_id"]].append(r)
    for event_id in chains:
        chains[event_id].sort(key=lambda r: r.get("timestamp", ""))
    return dict(chains)


def classify_chain(stages: list[dict]) -> tuple[bool, str | None, str, str]:
    seen = {s["stage"] for s in stages}
    listings_by_stage = {
        s["stage"]: s.get("listings_count") for s in stages if s.get("listings_count") is not None
    }

    # Healthy: has ENRICH with listings_count >= 0 AND went through full chain
    has_enrich = "ENRICH" in seen
    collect_count = listings_by_stage.get("COLLECT", 0) or 0
    enrich_count = listings_by_stage.get("ENRICH", 0) or 0

    if has_enrich and collect_count > 0 and enrich_count > 0:
        return True, None, "", ""

    # Find last successful stage in canonical order
    last_stage = None
    for stage in STAGE_ORDER:
        if stage in seen:
            last_stage = stage

    # Determine missing next stage
    if last_stage is None:
        missing = None
    else:
        idx = STAGE_ORDER.index(last_stage)
        missing = STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else None

    # Refine: COLLECT present but listings_count == 0 → class C regardless
    if "COLLECT" in seen and collect_count == 0:
        cls, desc = FAILURE_CLASSES["COLLECT"]
        return False, "COLLECT", cls, desc

    cls, desc = FAILURE_CLASSES.get(missing, FAILURE_CLASSES[None])
    return False, missing, cls, desc


def format_listings_progression(stages: list[dict]) -> str:
    parts = []
    for s in stages:
        lc = s.get("listings_count")
        if lc is not None:
            parts.append(f"{s['stage']}:{lc}")
    return " → ".join(parts) if parts else "none"


def read_from_docker(container: str) -> list[str]:
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", "2000", container],
            capture_output=True, text=True, timeout=30,
        )
        return (result.stdout + result.stderr).splitlines()
    except FileNotFoundError:
        print("ERROR: docker CLI not found", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: docker logs timed out", file=sys.stderr)
        sys.exit(1)


def read_from_file(path: str) -> list[str]:
    try:
        with open(path) as f:
            return f.readlines()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def read_from_stdin() -> list[str]:
    return sys.stdin.read().splitlines()


def run(lines: list[str]) -> None:
    records = parse_lines(lines)

    if not records:
        print("NO TRACE RECORDS FOUND")
        print("Ensure emit_event_trace() is active in the backend and the stack is running.")
        return

    chains = normalize_chains(records)
    healthy, broken = [], []

    for event_id, stages in sorted(chains.items()):
        is_healthy, missing_stage, cls, desc = classify_chain(stages)
        if is_healthy:
            healthy.append(event_id)
        else:
            seen_stages = [s["stage"] for s in stages]
            last = seen_stages[-1] if seen_stages else "—"
            ext_id = next(
                (s.get("external_event_id") for s in reversed(stages)
                 if s.get("external_event_id")),
                None,
            )
            broken.append({
                "event_id": event_id,
                "last_stage": last,
                "missing_stage": missing_stage or "—",
                "failure_class": cls,
                "failure_desc": desc,
                "external_event_id": ext_id,
                "listings_progression": format_listings_progression(stages),
                "stages_seen": seen_stages,
            })

    # External block detection: C-class with no external_event_id = API creds
    external_blocks = [b for b in broken if b["failure_class"] == "C"]
    internal_failures = [b for b in broken if b["failure_class"] != "C"]

    print("=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  Total event chains : {len(chains)}")
    print(f"  Healthy            : {len(healthy)}")
    print(f"  Broken (internal)  : {len(internal_failures)}")
    print(f"  Broken (external)  : {len(external_blocks)}")
    print()

    if broken:
        print("=" * 60)
        print("BROKEN CHAINS")
        print("=" * 60)
        for b in broken:
            is_ext = b["failure_class"] == "C"
            print(f"\n  event_id            : {b['event_id']}")
            print(f"  stages_seen         : {' → '.join(b['stages_seen'])}")
            print(f"  last_stage          : {b['last_stage']}")
            print(f"  missing_stage       : {b['missing_stage']}")
            print(f"  failure_class       : {b['failure_class']} — {b['failure_desc']}")
            print(f"  external_event_id   : {b['external_event_id'] or 'NULL'}")
            print(f"  listings_progression: {b['listings_progression']}")
            print(f"  status              : {'EXTERNAL_BLOCK' if is_ext else 'NEEDS_FIX'}")
    else:
        print("All chains HEALTHY — no broken pipelines detected.")

    if healthy:
        print()
        print(f"Healthy event_ids: {healthy}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze emit_event_trace log chains")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--docker", metavar="CONTAINER", help="Docker container name or ID")
    group.add_argument("--file", metavar="PATH", help="Path to log file")
    args = parser.parse_args()

    if args.docker:
        lines = read_from_docker(args.docker)
    elif args.file:
        lines = read_from_file(args.file)
    else:
        lines = read_from_stdin()

    run(lines)


if __name__ == "__main__":
    main()
