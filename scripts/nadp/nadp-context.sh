#!/bin/bash
# NADP Auto-Enforcer — Evidence Collector
#
# Runs the mandatory Layer 1 curl probes, captures real output, and writes
# a structured .nadp-context.md file that contains:
#   - verified system state
#   - raw curl evidence (headers + body)
#   - pre-classified NADP layer status
#
# This file is the required input for any Claude/Cursor debug session.
# Without it, no debugging is authorised (NADP-UNVERIFIED: STOP).
#
# Usage:
#   bash scripts/nadp/nadp-context.sh           # writes .nadp-context.md
#   bash scripts/nadp/nadp-context.sh --print   # also prints to stdout
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$REPO_ROOT/.nadp-context.md"
BACKEND="http://localhost:8000"
FRONTEND="http://localhost:3000"
PRINT=0
[[ "${1:-}" == "--print" ]] && PRINT=1

# ── helpers ───────────────────────────────────────────────────────────────────

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

probe_http() {
  local url="$1"
  local label="$2"
  local http_code body content_type

  http_code=$(curl -s -o /tmp/nadp_body -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
  body=$(cat /tmp/nadp_body 2>/dev/null || echo "")
  content_type=$(curl -s -o /dev/null -w "%{content_type}" --max-time 5 "$url" 2>/dev/null || echo "unknown")

  echo "### $label"
  echo '```'
  echo "URL          : $url"
  echo "HTTP status  : $http_code"
  echo "Content-Type : $content_type"
  echo "Body (first 800 chars):"
  echo "${body:0:800}"
  echo '```'
  echo ""

  # Return classification in a global
  if [[ "$http_code" == "000" ]]; then
    PROBE_STATUS="connection_refused"
  elif [[ "$http_code" == "200" ]] && echo "$body" | grep -qi "<html"; then
    PROBE_STATUS="html_200"
  elif [[ "$http_code" == "200" ]]; then
    PROBE_STATUS="json_200"
  else
    PROBE_STATUS="error_${http_code}"
  fi
}

classify_transport() {
  local health_status="$1"
  local events_status="$2"

  if [[ "$health_status" == "connection_refused" || "$events_status" == "connection_refused" ]]; then
    echo "NADP-UNVERIFIED"
    return
  fi
  if [[ "$health_status" == "html_200" || "$events_status" == "html_200" ]]; then
    echo "NADP-A"   # Transport failure: HTML instead of JSON
    return
  fi
  if [[ "$health_status" != "json_200" ]]; then
    echo "NADP-A"
    return
  fi
  if [[ "$events_status" != "json_200" ]]; then
    echo "NADP-A"
    return
  fi
  echo "LAYER1-PASS"
}

# ── collect evidence ───────────────────────────────────────────────────────────

HEALTH_OUTPUT=""
EVENTS_OUTPUT=""
HEALTH_STATUS=""
EVENTS_STATUS=""

echo "🔍 NADP evidence collection — $(ts)" >&2

# Health probe
HEALTH_OUT=$(probe_http "$BACKEND/api/health" "GET /api/health")
HEALTH_STATUS="$PROBE_STATUS"

# Events probe
EVENTS_OUT=$(probe_http "$BACKEND/api/events/" "GET /api/events/")
EVENTS_STATUS="$PROBE_STATUS"

# Frontend probe
FRONTEND_OUT=$(probe_http "$FRONTEND" "GET http://localhost:3000")
FRONTEND_STATUS="$PROBE_STATUS"

# Event count (only if events endpoint passed)
EVENT_COUNT="unknown"
if [[ "$EVENTS_STATUS" == "json_200" ]]; then
  EVENT_COUNT=$(cat /tmp/nadp_body | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "parse_error")
fi

# Docker state
DOCKER_STATE=$(docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "docker_unavailable")

# Classify
LAYER1=$(classify_transport "$HEALTH_STATUS" "$EVENTS_STATUS")

# ── write output ───────────────────────────────────────────────────────────────

cat > "$OUT" <<MDEOF
# NADP Debug Context
Generated: $(ts)
Repo: $REPO_ROOT

---

## Verified Evidence (EVIDENCE LOCK — reasoning must use only this)

### Docker State
\`\`\`
$DOCKER_STATE
\`\`\`

$HEALTH_OUT
$EVENTS_OUT
$FRONTEND_OUT

---

## Layer 1 Classification

| Probe | Status |
|-------|--------|
| /api/health | $HEALTH_STATUS |
| /api/events/ | $EVENTS_STATUS |
| localhost:3000 | $FRONTEND_STATUS |
| event_count | $EVENT_COUNT |
| **Layer 1 verdict** | **$LAYER1** |

---

## NADP Enforcement Rules (Active)

- SINGLE ROOT CAUSE: select exactly one failure layer
- NO INFRA RE-LITIGATION: infrastructure is not re-openable as hypothesis
- EVIDENCE LOCK: reason only from the curl output above
- NO THEORY STACKING: "It is X because [evidence]" — not "could be X or Y"
- STOP CONDITION: if Layer 1 is NADP-UNVERIFIED, do not proceed

## Required Response Prefix

Every Claude/Cursor response to this context MUST begin with exactly one of:

- \`[NADP-A: Transport Failure]\`
- \`[NADP-B: Data Failure]\`
- \`[NADP-C: Client Transformation Failure]\`
- \`[NADP-D: State Failure]\`
- \`[NADP-E: UI Failure]\`
- \`[NADP-UNVERIFIED: STOP]\`

Current Layer 1 result: **$LAYER1**

MDEOF

echo "✅ Written: $OUT" >&2

# Write machine-readable companion
cat > "$REPO_ROOT/.nadp.json" <<JSONEOF
{
  "generated_at": "$(ts)",
  "layer_1": "$LAYER1",
  "health_status": "$HEALTH_STATUS",
  "events_status": "$EVENTS_STATUS",
  "frontend_status": "$FRONTEND_STATUS",
  "event_count": "$EVENT_COUNT",
  "authorised_to_debug": $([ "$LAYER1" != "NADP-UNVERIFIED" ] && echo "true" || echo "false")
}
JSONEOF

echo "✅ Written: $REPO_ROOT/.nadp.json" >&2

[[ $PRINT -eq 1 ]] && cat "$OUT"

# Exit non-zero if not authorised
if [[ "$LAYER1" == "NADP-UNVERIFIED" ]]; then
  echo "" >&2
  echo "🚫 [NADP-UNVERIFIED: STOP] — Layer 1 probes did not pass." >&2
  echo "   Stack is not reachable. Run: make up" >&2
  exit 1
fi

echo "" >&2
echo "Layer 1: $LAYER1  |  Events: $EVENT_COUNT  |  Authorised to proceed." >&2
