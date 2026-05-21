#!/bin/bash
# Single-entry dev boot + system truth gate for the Ticket App.
# Run from the repo root: bash scripts/dev_boot_gate.sh

set -euo pipefail

echo "======================================="
echo " TICKET APP — SYSTEM BOOT + TRUTH GATE "
echo "======================================="

echo ""
echo "[1] Starting Docker stack..."
docker compose up -d

echo ""
echo "[2] Waiting for backend to become healthy (up to 90s)..."
for i in $(seq 1 18); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' la-concert-watchlist-backend-1 2>/dev/null || echo "missing")
  if [ "$STATUS" = "healthy" ]; then
    echo "    backend healthy after $((i * 5))s"
    break
  fi
  if [ "$i" = "18" ]; then
    echo "    ERROR: backend did not become healthy within 90s"
    docker compose logs --tail=40 backend
    exit 1
  fi
  sleep 5
done

echo ""
echo "[3] Container status (truth layer 0)..."
docker compose ps

echo ""
echo "[4] Backend health check..."
BACKEND_HEALTH_RAW=$(curl -sf http://localhost:8000/api/health 2>/dev/null || echo "")
if echo "$BACKEND_HEALTH_RAW" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='ok'" 2>/dev/null; then
  BACKEND_HEALTH="OK"
else
  BACKEND_HEALTH="FAIL"
fi
echo "    backend health: $BACKEND_HEALTH ($BACKEND_HEALTH_RAW)"

echo ""
echo "[5] Events API — source of truth..."
EVENTS_JSON=$(curl -sf http://localhost:8000/api/events/ 2>/dev/null || echo "FAIL")

if [ "$EVENTS_JSON" = "FAIL" ]; then
  echo "    ERROR: /api/events/ unreachable"
  exit 1
fi

echo ""
echo "[6] Event + listing counts (from DB)..."
docker compose exec -T db psql -U concert -d concert_tracker <<'SQL'
SELECT
  e.id,
  e.canonical_id,
  e.title,
  e.event_date::date AS event_date,
  COUNT(CASE WHEN l.marketplace_id = stub.id AND l.is_active THEN 1 END) AS stubhub_active,
  COUNT(CASE WHEN l.marketplace_id = sg.id   AND l.is_active THEN 1 END) AS seatgeek_active,
  COUNT(l.id) AS total_listings
FROM events e
LEFT JOIN listings l ON l.event_id = e.id
LEFT JOIN marketplaces stub ON stub.slug = 'stubhub'
LEFT JOIN marketplaces sg   ON sg.slug   = 'seatgeek'
GROUP BY e.id, e.canonical_id, e.title, e.event_date
ORDER BY e.event_date;
SQL

echo ""
echo "[7] Duplicate canonical ID check..."
DUPE_COUNT=$(docker compose exec -T db psql -U concert -d concert_tracker -tAc \
  "SELECT COUNT(*) FROM (SELECT canonical_id FROM events GROUP BY canonical_id HAVING COUNT(*) > 1) x;" 2>/dev/null || echo "ERR")
echo "    duplicate canonical_ids: $DUPE_COUNT"
if [ "$DUPE_COUNT" != "0" ]; then
  echo "    INVARIANT VIOLATION: duplicate canonical_ids detected"
fi

echo ""
echo "[8] Listing symmetry check (stubhub vs seatgeek)..."
docker compose exec -T db psql -U concert -d concert_tracker <<'SQL'
SELECT
  m.slug AS marketplace,
  COUNT(l.id) FILTER (WHERE l.is_active) AS active_listings
FROM listings l
JOIN marketplaces m ON m.id = l.marketplace_id
GROUP BY m.slug
ORDER BY m.slug;
SQL

echo ""
echo "======================================="
echo " CLAUDE HANDOFF PACKET "
echo "======================================="

EVENT_COUNT=$(echo "$EVENTS_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "parse_error")

cat <<HANDOFF

COPY EVERYTHING BELOW INTO CLAUDE:

---------------------------------------
SYSTEM STATUS: LIVE SNAPSHOT
BACKEND_HEALTH: $BACKEND_HEALTH
BACKEND_HEALTH_DETAIL: $BACKEND_HEALTH_RAW
EVENT_COUNT_FROM_API: $EVENT_COUNT

RAW_EVENTS_PAYLOAD (truncated to 1200 chars):
$(echo "$EVENTS_JSON" | head -c 1200)

---------------------------------------

CLAUDE INSTRUCTIONS (MANDATORY):
- Treat this snapshot as the ONLY source of truth
- Do NOT assume Docker state outside this snapshot
- Do NOT run seeding unless inconsistency is proven from this snapshot
- Do NOT modify UI or add features unless system is validated stable
- First task: reconcile event count + listing consistency
- Max 3 investigative passes allowed

END SNAPSHOT
=======================================
HANDOFF
