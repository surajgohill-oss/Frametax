#!/bin/bash
# NADP v3 — Networked Architecture Debugging Pipeline
# Fail-fast gated execution: each layer must pass before the next runs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NADP_JSON="$REPO_ROOT/.nadp.json"
START_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Initialise output file with running state
cat > "$NADP_JSON" <<EOF
{
  "status": "running",
  "started_at": "$START_TS"
}
EOF

run_layer() {
  local name="$1"
  local script="$SCRIPT_DIR/${name}.sh"

  echo ""
  echo "================================"
  echo "▶  Layer: $name"
  echo "================================"

  if bash "$script"; then
    echo "✅ PASSED: $name"
  else
    local code=$?
    echo "❌ NADP STOPPED AT LAYER: $name"

    cat > "$NADP_JSON" <<EOF
{
  "status": "failed",
  "failed_layer": "$name",
  "exit_code": $code,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    exit $code
  fi
}

echo "🧭 NADP v3 START — $(date -u)"

run_layer 0_system
run_layer 1_transport
run_layer 2_data
run_layer 3_client
run_layer 4_state

cat > "$NADP_JSON" <<EOF
{
  "status": "pass",
  "layer_0": "pass",
  "layer_1": "pass",
  "layer_2": "pass",
  "layer_3": "pass",
  "layer_4": "pass",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo ""
echo "🎯 NADP COMPLETE — ALL LAYERS VALID"
echo "   Written: $NADP_JSON"
