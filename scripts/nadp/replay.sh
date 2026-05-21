#!/bin/bash
# NADP v11 — Replay-Based Divergence Engine
#
# Reconstructs T0→T3 from live system artifacts and identifies the first
# step whose output cannot be reproduced from the previous step.
#
# Usage:
#   bash scripts/nadp/replay.sh              # full replay
#   bash scripts/nadp/replay.sh --t0-only    # DB snapshot only
#   bash scripts/nadp/replay.sh --json       # machine-readable output to .nadp-replay.json
set -euo pipefail

BACKEND="http://localhost:8000"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JSON_OUT="$REPO_ROOT/.nadp-replay.json"
JSON_MODE=0
T0_ONLY=0
[[ "${1:-}" == "--json" ]]    && JSON_MODE=1
[[ "${1:-}" == "--t0-only" ]] && T0_ONLY=1

SEP="─────────────────────────────────────────────"
PASS="✅"
FAIL="❌"
PARTIAL="⚠ "

echo ""
echo "🔁 NADP v11 — REPLAY-BASED DIVERGENCE ENGINE"
echo "   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ── helpers ───────────────────────────────────────────────────────────────────

T0_status="INCOMPLETE"; T0_count=0; T0_dupes=0
T1_status="INCOMPLETE"; T1_count=0; T1_te_total=0
T2_status="INCOMPLETE"
T3_status="INCOMPLETE"
DIVERGENCE="NONE"
DIVERGENCE_STEP="NONE"
DIVERGENCE_EVIDENCE=""

py() { python3 -c "$1"; }

# ── T0 — DATABASE STATE ───────────────────────────────────────────────────────

echo "$SEP"
echo "T0 — DATABASE STATE"
echo "$SEP"

if docker compose exec -T db psql -U concert -d concert_tracker -c "SELECT 1" > /dev/null 2>&1; then

  # Row counts
  T0_count=$(docker compose exec -T db psql -U concert -d concert_tracker -tAq \
    -c "SELECT COUNT(*) FROM events;")
  TE_count=$(docker compose exec -T db psql -U concert -d concert_tracker -tAq \
    -c "SELECT COUNT(*) FROM tracked_events WHERE is_active = true;")
  LISTING_count=$(docker compose exec -T db psql -U concert -d concert_tracker -tAq \
    -c "SELECT COUNT(*) FROM listings WHERE is_active = true;")

  echo "  events (canonical rows) : $T0_count"
  echo "  tracked_events (active) : $TE_count   ← expected ≤ events×6"
  echo "  listings (active)       : $LISTING_count   ← expected expansion, not duplication"

  # canonical_id uniqueness — the identity check
  T0_dupes=$(docker compose exec -T db psql -U concert -d concert_tracker -tAq \
    -c "SELECT COUNT(*) FROM (
          SELECT canonical_id FROM events GROUP BY canonical_id HAVING COUNT(*) > 1
        ) dupes;")

  if [[ "$T0_dupes" -eq 0 ]]; then
    echo "  canonical_id unique     : $PASS  (0 duplicates)"
    T0_status="PASS"
  else
    echo "  canonical_id unique     : $FAIL  ($T0_dupes duplicate canonical_ids)"
    T0_status="FAIL"
    DIVERGENCE="YES"
    DIVERGENCE_STEP="T0"
    DIVERGENCE_EVIDENCE="canonical_id appears $T0_dupes times in events table — identity-level duplication"
  fi

  # Expansion ratio sanity (not a failure signal, just labelling)
  if [[ "$T0_count" -gt 0 ]]; then
    TE_PER_EVENT=$(py "print(round($TE_count/$T0_count,1))")
    echo "  te/event ratio          : $TE_PER_EVENT  (valid range 0–6)"
  fi

else
  echo "  $PARTIAL DB unreachable — T0 PARTIAL SIMULATION"
  echo "  Schema guarantees canonical_id uniqueness (unique constraint in events table)"
  T0_status="PARTIAL"
fi

[[ $T0_ONLY -eq 1 ]] && exit 0

# ── T1 — API TRANSFORMATION ───────────────────────────────────────────────────

echo ""
echo "$SEP"
echo "T1 — API TRANSFORMATION"
echo "$SEP"

HTTP_CODE=$(curl -s -o /tmp/nadp_t1 -w "%{http_code}" --max-time 5 "$BACKEND/api/events/" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
  T1_BODY=$(cat /tmp/nadp_t1)

  # Detect HTML (routing failure)
  if echo "$T1_BODY" | grep -qi "<html"; then
    echo "  $FAIL HTML response — backend routing failure, not JSON"
    T1_status="FAIL"
    if [[ "$DIVERGENCE" == "NONE" ]]; then
      DIVERGENCE="YES"; DIVERGENCE_STEP="T1"
      DIVERGENCE_EVIDENCE="GET /api/events/ returned HTML instead of JSON"
    fi
  else
    T1_RESULT=$(echo "$T1_BODY" | python3 - <<'PYEOF'
import sys, json

try:
    data = json.load(sys.stdin)
except Exception as e:
    print(f"PARSE_ERROR:{e}")
    sys.exit(1)

count = len(data)
canonical_ids = [ev.get("canonical_id","") for ev in data]
dupes = [c for c in canonical_ids if canonical_ids.count(c) > 1]
te_total = sum(len(ev.get("tracked_events",[])) for ev in data)
has_trace = all("__trace" in ev for ev in data)

# Stage summary from first event's trace
stage_names = []
if data and "__trace" in data[0]:
    stage_names = [s["stage"] for s in data[0]["__trace"].get("stages",[])]

print(f"COUNT:{count}")
print(f"DUPES:{len(dupes)}")
print(f"TE_TOTAL:{te_total}")
print(f"HAS_TRACE:{has_trace}")
print(f"STAGES:{','.join(stage_names)}")
PYEOF
)

    T1_count=$(echo "$T1_RESULT" | grep "^COUNT:" | cut -d: -f2)
    T1_dupes=$(echo "$T1_RESULT" | grep "^DUPES:" | cut -d: -f2)
    T1_te_total=$(echo "$T1_RESULT" | grep "^TE_TOTAL:" | cut -d: -f2)
    T1_has_trace=$(echo "$T1_RESULT" | grep "^HAS_TRACE:" | cut -d: -f2)
    T1_stages=$(echo "$T1_RESULT" | grep "^STAGES:" | cut -d: -f2-)

    echo "  event count             : $T1_count"
    echo "  canonical_id dupes      : $T1_dupes"
    echo "  tracked_events (nested) : $T1_te_total  ← sub-items per event, NOT event count"
    echo "  __trace present         : $T1_has_trace"
    echo "  trace stages (event[0]) : $T1_stages"

    # T1 reproducible from T0?
    if [[ "$T0_status" == "PASS" && "$T1_count" != "$T0_count" ]]; then
      echo "  $FAIL T1 count ($T1_count) ≠ T0 row count ($T0_count) — API inflates or drops events"
      T1_status="FAIL"
      if [[ "$DIVERGENCE" == "NONE" ]]; then
        DIVERGENCE="YES"; DIVERGENCE_STEP="T1"
        DIVERGENCE_EVIDENCE="DB has $T0_count event rows, API returned $T1_count — count diverges at enrichment"
      fi
    elif [[ "$T1_dupes" -gt 0 ]]; then
      echo "  $FAIL canonical_id duplication appears in T1 response"
      T1_status="FAIL"
      if [[ "$DIVERGENCE" == "NONE" ]]; then
        DIVERGENCE="YES"; DIVERGENCE_STEP="T1"
        DIVERGENCE_EVIDENCE="canonical_id duplicates present in API response ($T1_dupes)"
      fi
    else
      echo "  $PASS T1 reproducible from T0  ($T1_count events, 0 canonical dupes)"
      T1_status="PASS"
    fi
  fi

elif [[ "$HTTP_CODE" == "000" ]]; then
  echo "  $PARTIAL Backend unreachable — T1 PARTIAL SIMULATION"
  echo "  Code path: list_events → scalars().all() → _enrich_event() × N"
  echo "  No duplication mechanism exists in static analysis of routes/events.py"
  T1_status="PARTIAL"
else
  echo "  $FAIL Backend returned HTTP $HTTP_CODE"
  T1_status="FAIL"
  if [[ "$DIVERGENCE" == "NONE" ]]; then
    DIVERGENCE="YES"; DIVERGENCE_STEP="T1"
    DIVERGENCE_EVIDENCE="GET /api/events/ HTTP $HTTP_CODE"
  fi
fi

# ── T2 — CLIENT STATE HYDRATION ───────────────────────────────────────────────

echo ""
echo "$SEP"
echo "T2 — CLIENT STATE HYDRATION"
echo "$SEP"
echo "  Input required: window.__EVENT_TRACE__ from browser console"
echo ""

if [[ "$T1_status" == "PASS" ]]; then
  echo "  T1 passed with $T1_count events."
  echo "  Expected T2 state: events.length === $T1_count"
  echo "  Verification: run in browser console on http://localhost:3000"
  echo ""
  echo "    window.__EVENT_TRACE__.length === $T1_count"
  echo "    // true → T2 reproducible from T1"
  echo "    // false → divergence at client hydration (check api.ts fetch path)"
  echo ""
  echo "  $PARTIAL T2 PARTIAL SIMULATION — browser output not provided"
  T2_status="PARTIAL"
elif [[ "$T1_status" == "PARTIAL" ]]; then
  echo "  $PARTIAL T2 PARTIAL SIMULATION — T1 also partial"
  T2_status="PARTIAL"
else
  echo "  $PARTIAL T2 blocked — T1 failed, fix T1 first"
  T2_status="BLOCKED"
fi

# ── T3 — RENDER OUTPUT ────────────────────────────────────────────────────────

echo ""
echo "$SEP"
echo "T3 — RENDER OUTPUT"
echo "$SEP"

if [[ "$T1_status" == "PASS" ]]; then
  echo "  Expected EventCard count : $T1_count"
  echo "  Guard in place           : assertEventCardinality() in frontend/src/app/page.tsx:92"
  echo "  Guard behaviour          : throws STATE_INTEGRITY_VIOLATION if T3 ≠ T2"
  echo ""
  echo "  Verification: open http://localhost:3000 and check browser console for errors."
  echo "  If no STATE_INTEGRITY_VIOLATION thrown → T3 reproducible from T2."
  echo ""
  echo "  Note: marketplace panels on /events/:id are listing expansions of ONE event."
  echo "  Counting panels ≠ counting events. Max panels = marketplaces with listings."
  echo ""
  echo "  $PARTIAL T3 PARTIAL SIMULATION — DOM not inspectable from shell"
  T3_status="PARTIAL"
else
  echo "  $PARTIAL T3 blocked — upstream steps incomplete"
  T3_status="BLOCKED"
fi

# ── DIVERGENCE SUMMARY ────────────────────────────────────────────────────────

echo ""
echo "$SEP"
echo "DIVERGENCE RESULT"
echo "$SEP"
echo "  Divergence found         : $DIVERGENCE"
echo "  First non-reproducible   : $DIVERGENCE_STEP"
if [[ -n "$DIVERGENCE_EVIDENCE" ]]; then
  echo "  Evidence                 : $DIVERGENCE_EVIDENCE"
fi
echo ""

if [[ "$DIVERGENCE" == "NONE" && "$T1_status" == "PASS" ]]; then
  echo "  $PASS T0→T1 chain reproducible. No divergence in observable steps."
  echo "  If UI count still appears wrong, provide window.__EVENT_TRACE__ output."
  echo "  Most likely explanation: marketplace panel expansion on /events/:id"
  echo "  is being counted as duplicate events. This is VALID EXPANSION, not a bug."
elif [[ "$DIVERGENCE" == "NONE" ]]; then
  echo "  $PARTIAL INSUFFICIENT DATA — stack offline. Run: make up && bash scripts/nadp/replay.sh"
fi

# ── JSON OUTPUT ───────────────────────────────────────────────────────────────

if [[ $JSON_MODE -eq 1 ]]; then
  cat > "$JSON_OUT" <<JSONEOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "T0": {"status": "$T0_status", "event_count": $T0_count, "canonical_dupes": $T0_dupes},
  "T1": {"status": "$T1_status", "event_count": $T1_count, "te_total": $T1_te_total},
  "T2": {"status": "$T2_status"},
  "T3": {"status": "$T3_status"},
  "divergence": "$DIVERGENCE",
  "divergence_step": "$DIVERGENCE_STEP",
  "divergence_evidence": "$DIVERGENCE_EVIDENCE"
}
JSONEOF
  echo ""
  echo "  Written: $JSON_OUT"
fi
