#!/usr/bin/env python3
"""
Verify backend production closeout.

Exits 0 only if ALL checks pass.
Exits 1 with a detailed failure report otherwise.

Usage:
    python3 scripts/verify_backend_closeout.py [--base-url https://backend-production-509f.up.railway.app]
"""
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

DEFAULT_BASE = "https://backend-production-509f.up.railway.app"

CHECKS: list[tuple[str, bool]] = []   # (message, passed)
FAILURES: list[str] = []


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    line = f"  [{status}] {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    CHECKS.append((label, passed))
    if not passed:
        FAILURES.append(label + (f": {detail}" if detail else ""))
    return passed


def get(url: str, timeout: int = 10) -> dict | None:
    try:
        req = urllib.request.urlopen(url, timeout=timeout)
        return json.loads(req.read().decode())
    except urllib.error.HTTPError as e:
        print(f"    HTTP {e.code} for {url}")
        return None
    except Exception as e:
        print(f"    Error fetching {url}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    print(f"\n=== AwardRadar Backend Closeout Verification ===")
    print(f"Target: {base}")
    print(f"Time:   {datetime.now(timezone.utc).isoformat()}\n")

    # ── 1. Basic health ────────────────────────────────────────────────────────
    print("1. Basic health")
    h = get(f"{base}/api/health")
    check("GET /api/health returns 200", h is not None)
    check("/api/health status ok", (h or {}).get("status") == "ok",
          detail=(h or {}).get("status", "no response"))
    check("/api/health db ok", (h or {}).get("db") == "ok",
          detail=(h or {}).get("db", "no response"))

    # ── 2. Reliability endpoint ────────────────────────────────────────────────
    print("\n2. Reliability endpoint")
    rel = get(f"{base}/api/system/reliability")
    check("GET /api/system/reliability returns 200", rel is not None)
    if rel:
        status = rel.get("status", "?")
        check("reliability status is ok or degraded",
              status in ("ok", "degraded"),
              detail=f"status={status}")

        sig = rel.get("active_crash_signature")
        check("no active crash signature",
              not sig,
              detail=sig[:100] if sig else "none")

        failed_24h = rel.get("failed_polls_24h", 0)
        check("failed_polls_24h < 50",
              failed_24h < 50,
              detail=f"failed_polls_24h={failed_24h}")

        last_success = rel.get("scheduler_last_success_at")
        if last_success:
            try:
                ts = datetime.fromisoformat(last_success.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
                check("last successful poll within 2h",
                      age_h < 2,
                      detail=f"{age_h:.1f}h ago")
            except Exception as e:
                check("last successful poll within 2h", False, detail=f"parse error: {e}")
        else:
            check("last successful poll within 2h", False, detail="no successful poll recorded yet")

    # ── 3. Recent snapshot written ─────────────────────────────────────────────
    print("\n3. Snapshot recency")
    if rel and rel.get("latest_snapshot_at"):
        snap_ts_raw = rel["latest_snapshot_at"]
        try:
            snap_ts = datetime.fromisoformat(snap_ts_raw.replace("Z", "+00:00"))
            if snap_ts.tzinfo is None:
                snap_ts = snap_ts.replace(tzinfo=timezone.utc)
            snap_age_h = (datetime.now(timezone.utc) - snap_ts).total_seconds() / 3600
            check("latest snapshot within 4h",
                  snap_age_h < 4,
                  detail=f"{snap_age_h:.1f}h ago — {snap_ts_raw}")
        except Exception as e:
            check("latest snapshot within 4h", False, detail=f"parse error: {e}")
    else:
        check("latest snapshot within 4h", False, detail="reliability endpoint missing latest_snapshot_at")

    # ── 4. Other health endpoints ──────────────────────────────────────────────
    print("\n4. Supporting health endpoints")
    for path in ["/api/events", "/api/venues"]:
        r = get(f"{base}{path}")
        check(f"GET {path} returns 200", r is not None)

    # ── 5. Event alerts surface backend failures ───────────────────────────────
    print("\n5. Event alerts (spot check first event)")
    evts = get(f"{base}/api/events")
    if evts and isinstance(evts, list) and len(evts) > 0:
        eid = evts[0].get("id")
        if eid:
            al = get(f"{base}/api/events/{eid}/alerts")
            check(f"GET /api/events/{eid}/alerts returns 200", al is not None)
            if al:
                types = [a.get("type") for a in al.get("alerts", [])]
                # If there's a crash, it should show POLL_TASK_CRASH
                if rel and rel.get("active_crash_signature"):
                    check("POLL_TASK_CRASH alert present when crash active",
                          "POLL_TASK_CRASH" in types,
                          detail=f"found types: {types[:5]}")
                else:
                    check("alert endpoint responsive (no crash to verify)", True)
        else:
            check("events list has id field", False)
    else:
        check("events list non-empty", False, detail="no events returned")

    # ── Summary ────────────────────────────────────────────────────────────────
    total = len(CHECKS)
    passed = sum(1 for _, p in CHECKS if p)
    failed = total - passed

    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")

    if FAILURES:
        print("\nFailed checks:")
        for f in FAILURES:
            print(f"  • {f}")
        print("\nPRODUCTION RELIABILITY CLOSED: NO")
        sys.exit(1)
    else:
        print("\nPRODUCTION RELIABILITY CLOSED: YES")
        sys.exit(0)


if __name__ == "__main__":
    main()
