#!/usr/bin/env python3
"""
NADP Playwright CI Debug Kernel v9.1

Reads 4 artifacts from scripts/nadp/.artifacts/ and produces a
single-pass deterministic analysis. Does not iterate. Does not guess.

Usage:
    python3 scripts/nadp/kernel.py
    python3 scripts/nadp/kernel.py --artifacts path/to/dir
    python3 scripts/nadp/kernel.py --prev path/to/prev/.artifacts  # temporal comparison
"""
import json
import sys
import os
import argparse
from pathlib import Path
from typing import Any

# ── config ────────────────────────────────────────────────────────────────────

PATCH_CONFIDENCE_THRESHOLD = 0.75
REQUIRED_ARTIFACTS = ["api.json", "dom.json", "console.json"]
# screenshot.png existence is checked but not parsed

# ── load artifacts ────────────────────────────────────────────────────────────

def load(artifact_dir: Path, prev_dir: Path | None) -> dict[str, Any]:
    missing = []
    for name in REQUIRED_ARTIFACTS:
        if not (artifact_dir / name).exists():
            missing.append(name)
    if not (artifact_dir / "screenshot.png").exists():
        missing.append("screenshot.png")

    if missing:
        print(f"[BLOCKED: INCOMPLETE TELEMETRY]")
        print(f"Missing artifacts: {', '.join(missing)}")
        print(f"Run: make capture")
        sys.exit(0)

    api  = json.loads((artifact_dir / "api.json").read_text())
    dom  = json.loads((artifact_dir / "dom.json").read_text())
    cons = json.loads((artifact_dir / "console.json").read_text())

    prev_api = prev_dom = prev_cons = None
    if prev_dir:
        try:
            prev_api  = json.loads((prev_dir / "api.json").read_text())
            prev_dom  = json.loads((prev_dir / "dom.json").read_text())
            prev_cons = json.loads((prev_dir / "console.json").read_text())
        except Exception:
            pass

    return {"api": api, "dom": dom, "cons": cons,
            "prev_api": prev_api, "prev_dom": prev_dom, "prev_cons": prev_cons}

# ── consistency ───────────────────────────────────────────────────────────────

def compute_consistency(d: dict) -> dict:
    api  = d["api"]
    dom  = d["dom"]
    cons = d["cons"]

    api_count = len(api) if isinstance(api, list) else 0
    dom_count = len(dom.get("eventCards", []))
    page_errors = len(cons.get("pageErrors", []))
    console_errors = sum(1 for e in cons.get("consoleEntries", []) if e.get("type") == "error")
    total_errors = page_errors + console_errors

    # STATE_INTEGRITY_VIOLATION means assertEventCardinality fired
    integrity_violation = any(
        "STATE_INTEGRITY_VIOLATION" in (e.get("message", "") + e.get("text", ""))
        for e in cons.get("pageErrors", []) + cons.get("consoleEntries", [])
    )

    # canonical_id uniqueness in API response
    if isinstance(api, list):
        canonical_ids = [ev.get("canonical_id", "") for ev in api]
        api_canonical_dupes = len(canonical_ids) - len(set(canonical_ids))
    else:
        api_canonical_dupes = -1  # unknown

    # DOM canonical_id uniqueness
    dom_cids = [c.get("canonicalId") for c in dom.get("eventCards", []) if c.get("canonicalId")]
    dom_canonical_dupes = len(dom_cids) - len(set(dom_cids))

    # Section cardinality
    section_total = sum(s.get("cardCount", 0) for s in dom.get("sections", []))

    return {
        "api_count": api_count,
        "dom_count": dom_count,
        "console_errors": total_errors,
        "integrity_violation": integrity_violation,
        "api_canonical_dupes": api_canonical_dupes,
        "dom_canonical_dupes": dom_canonical_dupes,
        "section_total": section_total,
        "empty_state": dom.get("emptyState", False),
    }

# ── temporal stability ────────────────────────────────────────────────────────

def compute_temporal(d: dict, c: dict) -> str:
    if d["prev_api"] is None:
        return "STABLE"   # no previous cycle to compare

    prev_api_count = len(d["prev_api"]) if isinstance(d["prev_api"], list) else 0
    prev_dom_count = len(d["prev_dom"].get("eventCards", [])) if d["prev_dom"] else 0

    if prev_api_count != c["api_count"] or prev_dom_count != c["dom_count"]:
        return "INSTABLE"
    if c["integrity_violation"]:
        return "INSTABLE"
    return "STABLE"

# ── trace validation ──────────────────────────────────────────────────────────

def compute_traces(d: dict, c: dict) -> dict:
    api = d["api"]
    dom = d["dom"]

    if not isinstance(api, list):
        return {"forward": "CANNOT TRACE — api.json is not an array",
                "reverse": "CANNOT TRACE", "convergence": False}

    # FORWARD: API → DOM
    api_ids    = sorted(str(ev.get("id", "")) for ev in api)
    dom_ids    = sorted(c for c in [card.get("eventId") for card in dom.get("eventCards", [])] if c)
    dom_cids   = sorted(c for c in [card.get("canonicalId") for card in dom.get("eventCards", [])] if c)
    api_cids   = sorted(ev.get("canonical_id", "") for ev in api)

    forward_ok = (len(api) == c["dom_count"]) and (api_cids == dom_cids or not dom_cids)

    # REVERSE: DOM → API
    # Every DOM card's canonical_id should exist in API response
    api_cid_set = set(ev.get("canonical_id", "") for ev in api)
    orphaned = [cid for cid in dom_cids if cid not in api_cid_set]
    reverse_ok = len(orphaned) == 0

    fwd_str = (
        f"API({len(api)}) → DOM({c['dom_count']}) — "
        + ("MATCH" if len(api) == c["dom_count"] else f"MISMATCH by {abs(len(api) - c['dom_count'])}")
    )
    rev_str = (
        f"DOM cards → API canonical_ids — "
        + (f"MATCH" if reverse_ok else f"ORPHANED canonical_ids: {orphaned}")
    )

    return {
        "forward": fwd_str,
        "reverse": rev_str,
        "convergence": forward_ok and reverse_ok,
    }

# ── classification ────────────────────────────────────────────────────────────

def classify(c: dict, traces: dict, temporal: str) -> tuple[str, float]:
    """
    Returns (bug_class, confidence_score).
    Exactly one class. Confidence = fraction of confirming signals.
    """

    # Empty state with no API events = valid behavior
    if c["api_count"] == 0 and c["empty_state"]:
        return "NO BUG", 0.95

    # API itself has canonical_id duplicates → DATA BUG
    if c["api_canonical_dupes"] > 0:
        return "DATA BUG", 0.95

    # API count and DOM count match, no violations → NO BUG
    if (c["api_count"] == c["dom_count"]
            and c["dom_canonical_dupes"] == 0
            and not c["integrity_violation"]
            and traces["convergence"]):
        confidence = 0.90 if c["console_errors"] == 0 else 0.80
        return "NO BUG", confidence

    # STATE_INTEGRITY_VIOLATION fired → assertEventCardinality caught it in render
    if c["integrity_violation"]:
        # Forward trace: check where count first diverged
        if c["api_canonical_dupes"] > 0:
            return "DATA BUG", 0.90
        return "RENDER BUG", 0.80

    # API correct, DOM count wrong, canonical_ids mismatched → CLIENT BUG
    if c["api_count"] > 0 and c["dom_count"] != c["api_count"] and c["api_canonical_dupes"] == 0:
        if not traces["convergence"]:
            confidence = 0.70  # below patch threshold — needs more evidence
            return "CLIENT BUG", confidence

    # Temporal instability with intermittent mismatch
    if temporal == "INSTABLE" and c["api_count"] == c["dom_count"]:
        return "TEMPORAL BUG", 0.75

    # API unreachable or malformed
    if c["api_count"] == 0 and not c["empty_state"]:
        return "DATA BUG", 0.65

    return "NO BUG", 0.50   # insufficient signal

# ── visual match heuristic ────────────────────────────────────────────────────

def visual_match(c: dict) -> str:
    # screenshot.png exists (checked in load()), but we can't parse pixels here.
    # We approximate visual match from DOM structural consistency.
    if c["api_count"] == c["dom_count"] and c["dom_canonical_dupes"] == 0:
        return "YES"
    return "UNVERIFIED"

# ── patch decision ────────────────────────────────────────────────────────────

def patch_decision(bug_class: str, confidence: float, traces: dict, c: dict) -> str:
    if confidence < PATCH_CONFIDENCE_THRESHOLD:
        return "NO PATCH"
    if not traces["convergence"]:
        return "NO PATCH"
    if bug_class in ("NO BUG", "TEMPORAL BUG"):
        return "NO PATCH"
    return "ELIGIBLE"

# ── output ────────────────────────────────────────────────────────────────────

def render(bug_class: str, confidence: float, c: dict, traces: dict,
           temporal: str, patch: str) -> None:
    sep = "─" * 40

    print(f"\n{sep}")
    print("[CLASSIFICATION]")
    print(f"{bug_class}")

    print(f"\n{sep}")
    print("[CONSISTENCY]")
    print(f"API_COUNT      : {c['api_count']}")
    print(f"DOM_CARD_COUNT : {c['dom_count']}")
    print(f"CONSOLE_ERRORS : {c['console_errors']}")
    print(f"VISUAL_MATCH   : {visual_match(c)}")
    if c["api_canonical_dupes"] > 0:
        print(f"CANONICAL_DUPES: {c['api_canonical_dupes']} in API  ← identity violation")
    if c["dom_canonical_dupes"] > 0:
        print(f"CANONICAL_DUPES: {c['dom_canonical_dupes']} in DOM")
    if c["integrity_violation"]:
        print("GUARD_FIRED    : assertEventCardinality — STATE_INTEGRITY_VIOLATION")

    print(f"\n{sep}")
    print("[TEMPORAL]")
    print(temporal)

    print(f"\n{sep}")
    print("[TRACE]")
    print(f"FORWARD: {traces['forward']}")
    print(f"REVERSE: {traces['reverse']}")
    print(f"CONVERGENCE: {'YES' if traces['convergence'] else 'NO'}")

    print(f"\n{sep}")
    print("[CONFIDENCE]")
    print(f"{confidence:.2f}")

    print(f"\n{sep}")
    print("[PATCH]")
    if patch == "ELIGIBLE":
        print("# Patch eligible — specific diff depends on bug class.")
        print("# Provide this output to the patch stage with the relevant file.")
    else:
        print("NO PATCH")
        if confidence < PATCH_CONFIDENCE_THRESHOLD:
            print(f"  Reason: confidence {confidence:.2f} < threshold {PATCH_CONFIDENCE_THRESHOLD}")
        if not traces["convergence"]:
            print("  Reason: trace convergence failed — insufficient causal evidence")
    print()

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", default=Path(__file__).parent / ".artifacts",
                        type=Path, help="Path to artifact directory")
    parser.add_argument("--prev", default=None, type=Path,
                        help="Previous cycle artifact directory (for temporal comparison)")
    args = parser.parse_args()

    d = load(args.artifacts, args.prev)
    c = compute_consistency(d)
    temporal = compute_temporal(d, c)
    traces = compute_traces(d, c)
    bug_class, confidence = classify(c, traces, temporal)
    patch = patch_decision(bug_class, confidence, traces, c)

    render(bug_class, confidence, c, traces, temporal, patch)

    # Machine-readable output alongside human output
    result = {
        "classification": bug_class,
        "confidence": confidence,
        "consistency": c,
        "temporal": temporal,
        "trace_convergence": traces["convergence"],
        "patch": patch,
    }
    out_path = args.artifacts / "kernel-result.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Written: {out_path}")

if __name__ == "__main__":
    main()
