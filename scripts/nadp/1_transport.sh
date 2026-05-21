#!/bin/bash
# Layer 1 — Transport Validation
# Verifies the FastAPI backend responds with JSON, not HTML, and is healthy.
set -euo pipefail

BACKEND="http://localhost:8000"

echo "Checking health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND/api/health")
if [ "$HEALTH_STATUS" != "200" ]; then
  echo "❌ Health endpoint returned HTTP $HEALTH_STATUS (expected 200)"
  echo "   URL: $BACKEND/api/health"
  exit 1
fi

HEALTH_BODY=$(curl -s "$BACKEND/api/health")
DB_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('db','unknown'))" 2>/dev/null || echo "parse_error")
if [ "$DB_STATUS" != "ok" ]; then
  echo "❌ Health check reports DB status: $DB_STATUS"
  echo "   Full response: $HEALTH_BODY"
  echo "   Fix: check postgres container and run 'alembic upgrade head'"
  exit 1
fi
echo "  /api/health  ✓  (db=$DB_STATUS)"

echo ""
echo "Checking events endpoint..."
EVENTS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND/api/events/")
if [ "$EVENTS_HTTP" != "200" ]; then
  echo "❌ /api/events/ returned HTTP $EVENTS_HTTP"
  exit 1
fi

EVENTS_BODY=$(curl -s "$BACKEND/api/events/")

# Hard stop if HTML returned instead of JSON
if echo "$EVENTS_BODY" | grep -qi "<html"; then
  echo "❌ HTML RESPONSE DETECTED — routing failure or reverse proxy misconfiguration"
  echo "   The backend is returning an HTML page instead of JSON."
  echo "   This means the request is hitting Next.js (:3000), not FastAPI (:8000)."
  exit 1
fi

# Validate it parses as JSON array
PARSE_CHECK=$(echo "$EVENTS_BODY" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if not isinstance(d, list):
        print('NOT_LIST')
        sys.exit(1)
    print('OK')
except Exception as e:
    print(f'PARSE_ERROR:{e}')
    sys.exit(1)
" 2>&1)

if [ "$PARSE_CHECK" != "OK" ]; then
  echo "❌ /api/events/ response is not a JSON array: $PARSE_CHECK"
  echo "   Raw (first 500 chars): ${EVENTS_BODY:0:500}"
  exit 1
fi

echo "  /api/events/  ✓  (JSON array)"

echo ""
echo "Checking frontend reachability..."
FRONTEND_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000")
if [ "$FRONTEND_HTTP" != "200" ]; then
  echo "❌ Frontend returned HTTP $FRONTEND_HTTP"
  exit 1
fi
echo "  http://localhost:3000  ✓"
