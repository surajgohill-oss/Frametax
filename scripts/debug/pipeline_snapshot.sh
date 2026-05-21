#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# pipeline_snapshot.sh
# One-paste system diagnostic + forced collection cycle.
#
# Usage (from repo root):
#   bash scripts/debug/pipeline_snapshot.sh
# ─────────────────────────────────────────────────────────────────────────────

set -uo pipefail

HR="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── [0] Docker health ──────────────────────────────────────────────────────
echo ""
echo "$HR"
echo " [0] DOCKER STATUS"
echo "$HR"
if ! docker info > /dev/null 2>&1; then
  echo "  DOCKER_UNAVAILABLE — cannot proceed. Start Docker and run again."
  exit 1
fi
docker compose ps

# ── [1] DB: listing counts ─────────────────────────────────────────────────
echo ""
echo "$HR"
echo " [1] DB: LISTING COUNTS (source of truth)"
echo "$HR"
docker compose exec -T db psql -U concert -d concert_tracker <<'SQL'
SELECT
  'total_listings'    AS metric, COUNT(*)::text AS value FROM listings
UNION ALL
SELECT 'active_listings',        COUNT(*)::text FROM listings WHERE is_active = true
UNION ALL
SELECT 'demo_listings_active',   COUNT(*)::text FROM listings
  WHERE is_active = true AND external_listing_id LIKE 'demo-%'
UNION ALL
SELECT 'real_listings_active',   COUNT(*)::text FROM listings
  WHERE is_active = true AND external_listing_id NOT LIKE 'demo-%';
SQL

# ── [2] DB: tracked_events state ──────────────────────────────────────────
echo ""
echo "$HR"
echo " [2] DB: TRACKED EVENTS STATE"
echo "$HR"
docker compose exec -T db psql -U concert -d concert_tracker <<'SQL'
SELECT
  te.id,
  SUBSTRING(e.title, 1, 25) AS event,
  m.slug                     AS marketplace,
  te.external_event_id,
  te.is_active,
  te.next_poll_at::date      AS next_poll
FROM tracked_events te
JOIN events      e ON e.id = te.event_id
JOIN marketplaces m ON m.id = te.marketplace_id
ORDER BY e.title, m.slug;
SQL

# ── [3] DB: per-event listing breakdown ───────────────────────────────────
echo ""
echo "$HR"
echo " [3] DB: LISTINGS PER EVENT × MARKETPLACE"
echo "$HR"
docker compose exec -T db psql -U concert -d concert_tracker <<'SQL'
SELECT
  SUBSTRING(e.title, 1, 25) AS event,
  m.slug                     AS marketplace,
  COUNT(l.id)                AS listing_count,
  MIN(l.price)               AS min_price,
  BOOL_OR(l.is_active)       AS any_active
FROM events e
JOIN tracked_events te ON te.event_id = e.id
JOIN marketplaces    m  ON m.id = te.marketplace_id
LEFT JOIN listings   l  ON l.event_id = e.id AND l.marketplace_id = m.id
GROUP BY e.title, m.slug
ORDER BY e.title, m.slug;
SQL

# ── [4] Force resolver ────────────────────────────────────────────────────
echo ""
echo "$HR"
echo " [4] FORCING RESOLVER CYCLE (demo → real IDs)"
echo "$HR"
docker compose exec -T backend python3 /shared_scripts/debug/force_resolve.py

# ── [5] DB check after resolver ───────────────────────────────────────────
echo ""
echo "$HR"
echo " [5] DB: TRACKED EVENTS AFTER RESOLVER"
echo "$HR"
docker compose exec -T db psql -U concert -d concert_tracker <<'SQL'
SELECT
  te.id,
  SUBSTRING(e.title, 1, 25) AS event,
  m.slug                     AS marketplace,
  te.external_event_id,
  te.resolution_source
FROM tracked_events te
JOIN events      e ON e.id = te.event_id
JOIN marketplaces m ON m.id = te.marketplace_id
ORDER BY e.title, m.slug;
SQL

# ── [6] Force single collection cycle ────────────────────────────────────
echo ""
echo "$HR"
echo " [6] FORCING COLLECTION CYCLE (all marketplaces, first event)"
echo "$HR"
docker compose exec -T backend python3 /shared_scripts/debug/force_collect.py

# ── [7] DB: final listing counts ─────────────────────────────────────────
echo ""
echo "$HR"
echo " [7] DB: FINAL LISTING COUNTS"
echo "$HR"
docker compose exec -T db psql -U concert -d concert_tracker <<'SQL'
SELECT
  SUBSTRING(e.title, 1, 28) AS event,
  m.slug                     AS marketplace,
  COUNT(l.id) FILTER (WHERE l.is_active)                            AS active,
  COUNT(l.id) FILTER (WHERE l.is_active AND l.external_listing_id NOT LIKE 'demo-%') AS real_active,
  MIN(l.price) FILTER (WHERE l.is_active)                           AS min_price
FROM events e
JOIN tracked_events te ON te.event_id = e.id
JOIN marketplaces    m  ON m.id = te.marketplace_id
LEFT JOIN listings   l  ON l.event_id = e.id AND l.marketplace_id = m.id
GROUP BY e.title, m.slug
ORDER BY real_active DESC NULLS LAST, e.title, m.slug;
SQL

# ── [8] Backend log tail (errors + pipeline stages only) ─────────────────
echo ""
echo "$HR"
echo " [8] BACKEND LOG TAIL (errors + pipeline signals)"
echo "$HR"
docker compose logs backend --tail 300 2>&1 \
  | grep -E "COLLECT|RESOLVER|DB_WRITE|ENRICH|INGEST|ERROR|WARNING|EXCEPTION|Traceback|EXTERNAL_BLOCK" \
  | tail -60

echo ""
echo "$HR"
echo " SNAPSHOT COMPLETE"
echo " SUCCESS if [7] shows real_active > 0 for any marketplace."
echo " EXTERNAL_BLOCK if all marketplaces show real_active = 0 (needs .env credentials)."
echo "$HR"
