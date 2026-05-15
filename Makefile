.PHONY: up down reset logs status build verify debug-snapshot verify-seed-code bootstrap-status \
        e2e-discovery-test discovery-dedupe-test lifecycle-time-sim-test

up:
	docker compose up --build -d
	@$(MAKE) --no-print-directory _wait
	@$(MAKE) --no-print-directory status

down:
	docker compose down

reset:
	docker compose down -v --remove-orphans
	rm -rf frontend/.next
	docker compose up --build -d
	@$(MAKE) --no-print-directory _wait
	@$(MAKE) --no-print-directory verify
	@$(MAKE) --no-print-directory status

logs:
	docker compose logs -f --tail=100

logs-%:
	docker compose logs -f --tail=100 $*

verify:
	@echo "── Dependency check ──────────────────────"
	@docker compose exec -T frontend sh -c \
		"[ -f /deps/node_modules/.bin/next ] && echo '  next binary  ✓ (/deps)' || (echo '  next binary  ✗ MISSING'; exit 1)"
	@docker compose exec -T frontend node -e \
		"try{require('tailwindcss');console.log('  tailwindcss  ✓')}catch(e){console.error('  tailwindcss  ✗',e.message);process.exit(1)}"
	@docker compose exec -T frontend sh -c \
		"[ -f /app/tailwind.config.js ] && echo '  tailwind cfg ✓' || (echo '  tailwind cfg ✗ missing'; exit 1)"
	@docker compose exec -T frontend sh -c \
		"[ -f /app/postcss.config.js ] && echo '  postcss cfg  ✓' || (echo '  postcss cfg  ✗ missing'; exit 1)"
	@echo ""

status:
	@echo "── Services ──────────────────────────────"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker compose ps
	@echo ""
	@echo "── Health ────────────────────────────────"
	@docker compose exec -T db pg_isready -U concert -q 2>/dev/null \
		&& echo "  db        ✓" || echo "  db        ✗ not ready"
	@docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG \
		&& echo "  redis     ✓" || echo "  redis     ✗ not ready"
	@curl -sf http://localhost:8000/api/health -o /dev/null 2>/dev/null \
		&& echo "  backend   ✓  http://localhost:8000" || echo "  backend   ✗ not responding"
	@curl -sf http://localhost:3000 -o /dev/null 2>/dev/null \
		&& echo "  frontend  ✓  http://localhost:3000" || echo "  frontend  ✗ not responding"
	@echo ""

# ── verify-seed-code ───────────────────────────────────────────────────────────
# Proves that the running container has the latest seed code and demo IDs.
# Does NOT check DB state — use bootstrap-status for that.
verify-seed-code:
	@echo "══════════════════════════════════════════"
	@echo "  SEED CODE PRESENCE CHECK"
	@echo "══════════════════════════════════════════"
	@echo ""
	@echo "── Script location inside container ──────"
	@docker compose exec -T backend sh -c \
		"ls -la /shared_scripts/seed_db_docker.py && md5sum /shared_scripts/seed_db_docker.py"
	@echo ""
	@echo "── Demo event IDs present ────────────────"
	@docker compose exec -T backend sh -c \
		"grep -c 'demo-sh-' /shared_scripts/seed_db_docker.py && echo 'stubhub demo IDs: ✓' || echo 'stubhub demo IDs: ✗ MISSING'"
	@docker compose exec -T backend sh -c \
		"grep -c 'demo-sg-' /shared_scripts/seed_db_docker.py && echo 'seatgeek demo IDs: ✓' || echo 'seatgeek demo IDs: ✗ MISSING'"
	@echo ""
	@echo "── Backfill logic present ────────────────"
	@docker compose exec -T backend sh -c \
		"grep -c 'phase2 backfill' /shared_scripts/seed_db_docker.py && echo 'backfill logic: ✓' || echo 'backfill logic: ✗ MISSING'"
	@docker compose exec -T backend sh -c \
		"grep -c 'sa_update' /shared_scripts/seed_db_docker.py && echo 'core UPDATE: ✓' || echo 'core UPDATE: ✗ MISSING'"
	@echo ""
	@echo "── Seed version string ───────────────────"
	@docker compose exec -T backend sh -c \
		"grep 'SEED_VERSION' /shared_scripts/seed_db_docker.py || echo 'SEED_VERSION: not found'"
	@echo ""
	@echo "── Host script vs container md5 ──────────"
	@md5sum scripts/seed_db_docker.py 2>/dev/null && \
		docker compose exec -T backend md5sum /shared_scripts/seed_db_docker.py || true
	@echo ""

# ── bootstrap-status ──────────────────────────────────────────────────────────
# Shows the runtime state of the demo seed bootstrap from the DB perspective.
bootstrap-status:
	@echo "══════════════════════════════════════════"
	@echo "  BOOTSTRAP STATUS"
	@echo "══════════════════════════════════════════"
	@echo ""
	@echo "── Migration head ────────────────────────"
	@docker compose exec -T backend alembic current 2>/dev/null || echo "  alembic not accessible"
	@echo ""
	@echo "── Backend seed log (last restart) ───────"
	@docker compose logs backend --tail=500 2>/dev/null | grep -E "^.*SEED:" | tail -30 || echo "  no SEED: lines found"
	@echo ""
	@echo "── tracked_events resolution state ───────"
	@docker compose exec -T db psql -U concert -d concert_tracker -c \
		"SELECT te.id, m.slug, te.external_event_id, te.resolution_source, e.title \
		 FROM tracked_events te \
		 JOIN events e ON e.id = te.event_id \
		 JOIN marketplaces m ON m.id = te.marketplace_id \
		 ORDER BY e.title, m.slug;"
	@echo ""
	@echo "── Demo ID presence ──────────────────────"
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'demo IDs present:  ' || COUNT(*) || '/' || \
		        (SELECT COUNT(*) FROM tracked_events WHERE is_active=true) || ' tracked_events' \
		 FROM tracked_events WHERE external_event_id LIKE 'demo-%';" | grep -v "^$$"
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'resolution_source: seeded=' || \
		        SUM(CASE WHEN resolution_source='seeded' THEN 1 ELSE 0 END) || \
		        ' api=' || \
		        SUM(CASE WHEN resolution_source LIKE 'resolved_%' THEN 1 ELSE 0 END) || \
		        ' null=' || \
		        SUM(CASE WHEN resolution_source IS NULL THEN 1 ELSE 0 END) \
		 FROM tracked_events WHERE is_active=true;" | grep -v "^$$"
	@echo ""

# ── Validation harness ─────────────────────────────────────────────────────────

e2e-discovery-test:
	@echo "══════════════════════════════════════════"
	@echo "  E2E DISCOVERY PIPELINE TEST"
	@echo "══════════════════════════════════════════"
	@docker compose exec -T backend python /shared_scripts/test_e2e_discovery.py; \
		EXIT=$$?; \
		if [ $$EXIT -eq 0 ]; then \
			echo ""; echo "  ✓ e2e-discovery-test PASSED"; \
		else \
			echo ""; echo "  ✗ e2e-discovery-test FAILED (exit $$EXIT)"; \
		fi; \
		exit $$EXIT

discovery-dedupe-test:
	@echo "══════════════════════════════════════════"
	@echo "  DISCOVERY DEDUPLICATION TEST"
	@echo "══════════════════════════════════════════"
	@docker compose exec -T backend python /shared_scripts/test_discovery_dedupe.py; \
		EXIT=$$?; \
		if [ $$EXIT -eq 0 ]; then \
			echo ""; echo "  ✓ discovery-dedupe-test PASSED"; \
		else \
			echo ""; echo "  ✗ discovery-dedupe-test FAILED (exit $$EXIT)"; \
		fi; \
		exit $$EXIT

lifecycle-time-sim-test:
	@echo "══════════════════════════════════════════"
	@echo "  LIFECYCLE + POLLING POLICY TIME-SIM"
	@echo "══════════════════════════════════════════"
	@docker compose exec -T backend python /shared_scripts/test_lifecycle_time_sim.py; \
		EXIT=$$?; \
		if [ $$EXIT -eq 0 ]; then \
			echo ""; echo "  ✓ lifecycle-time-sim-test PASSED"; \
		else \
			echo ""; echo "  ✗ lifecycle-time-sim-test FAILED (exit $$EXIT)"; \
		fi; \
		exit $$EXIT

debug-snapshot:
	@echo "══════════════════════════════════════════"
	@echo "  PIPELINE INVARIANT SNAPSHOT"
	@echo "══════════════════════════════════════════"
	@echo ""
	@echo "── Stage 1: Events ───────────────────────"
	@docker compose exec -T db psql -U concert -d concert_tracker -c \
		"SELECT id, title, status, event_date::date FROM events ORDER BY event_date;"
	@echo ""
	@echo "── Stage 2: Resolution (external IDs) ────"
	@docker compose exec -T db psql -U concert -d concert_tracker -c \
		"SELECT te.id, m.slug AS marketplace, te.external_event_id, \
		        te.resolution_source, te.lifecycle_phase, \
		        CASE WHEN te.external_event_id IS NULL THEN 'PENDING' ELSE 'RESOLVED' END AS stage2, \
		        e.title \
		 FROM tracked_events te \
		 JOIN events e ON e.id = te.event_id \
		 JOIN marketplaces m ON m.id = te.marketplace_id \
		 ORDER BY e.title, m.slug;"
	@echo ""
	@echo "── Stage 3: Listings ─────────────────────"
	@docker compose exec -T db psql -U concert -d concert_tracker -c \
		"SELECT e.title, m.slug AS marketplace, COUNT(l.id) AS listings, \
		        MIN(l.price) AS lowest_ask \
		 FROM events e \
		 LEFT JOIN listings l ON l.event_id = e.id AND l.is_active = true \
		 LEFT JOIN marketplaces m ON m.id = l.marketplace_id \
		 GROUP BY e.title, m.slug ORDER BY e.title, m.slug;"
	@echo ""
	@echo "── Recent poll runs ──────────────────────"
	@docker compose exec -T db psql -U concert -d concert_tracker -c \
		"SELECT pr.id, e.title, pr.status, pr.listings_found, \
		        pr.started_at::time, pr.error_message \
		 FROM poll_runs pr \
		 JOIN tracked_events te ON te.id = pr.tracked_event_id \
		 JOIN events e ON e.id = te.event_id \
		 ORDER BY pr.started_at DESC LIMIT 15;"
	@echo ""
	@echo "── Collector + resolver log (errors/warns) "
	@docker compose logs backend --tail=200 2>/dev/null | \
		grep -iE "SEED:|resolver|STAGE_GATE|ERROR|WARNING|Cannot resolve" | tail -25 || true
	@echo ""
	@echo "── Stage 3 eligibility + lifecycle ───────"
	@docker compose exec -T db psql -U concert -d concert_tracker -c \
		"SELECT e.title, m.slug, \
		        CASE WHEN te.external_event_id IS NOT NULL THEN 'ELIGIBLE' ELSE 'BLOCKED' END AS stage3, \
		        te.lifecycle_phase, \
		        te.resolution_source, \
		        CASE \
		          WHEN (e.event_date - now()) < interval '-5 minutes'  THEN 'STOP' \
		          WHEN (e.event_date - now()) < interval '0'           THEN '5min' \
		          WHEN (e.event_date - now()) < interval '8 hours'     THEN '15min' \
		          WHEN (e.event_date - now()) < interval '2 days'      THEN '60min' \
		          WHEN (e.event_date - now()) < interval '10 days'     THEN '240min' \
		          ELSE '1440min' \
		        END AS poll_policy, \
		        te.last_polled_at::time, te.next_poll_at::time \
		 FROM tracked_events te \
		 JOIN events e ON e.id = te.event_id \
		 JOIN marketplaces m ON m.id = te.marketplace_id \
		 WHERE te.is_active = true \
		 ORDER BY e.title, m.slug;"
	@echo ""
	@echo "── Invariants ────────────────────────────"
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'Invariant A (Stage 3 only on resolved): ' || \
		 CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL — ' || COUNT(*) || ' poll_run(s) on unresolved events' END \
		 FROM poll_runs pr \
		 JOIN tracked_events te ON te.id = pr.tracked_event_id \
		 WHERE te.external_event_id IS NULL AND pr.status != 'running';" | grep -v "^$$"
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'Invariant B (Stage 2 resolving):          ' || \
		 CASE WHEN COUNT(*) = 0 THEN 'PASS — all active events resolved' \
		      ELSE 'PENDING — ' || COUNT(*) || ' tracked_event(s) awaiting resolution' END \
		 FROM tracked_events WHERE external_event_id IS NULL AND is_active = true;" | grep -v "^$$"
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'Invariant C (No orphan poll_runs):        ' || \
		 CASE WHEN COUNT(*) = 0 THEN 'PASS' \
		      ELSE 'FAIL — ' || COUNT(*) || ' poll_run(s) with error=unresolved_event_id' END \
		 FROM poll_runs WHERE error_message = 'unresolved_event_id';" | grep -v "^$$"
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'Invariant D (Demo seed consistency):      ' || \
		 CASE WHEN COUNT(*) = 0 THEN \
		      'FAIL — 0 demo IDs in tracked_events (seed backfill did not execute)' \
		 WHEN COUNT(*) < 6 THEN \
		      'PARTIAL — ' || COUNT(*) || '/6 demo IDs seeded (check bootstrap-status)' \
		 ELSE 'PASS — ' || COUNT(*) || '/6 demo tracked_events have seeded IDs' END \
		 FROM tracked_events WHERE external_event_id LIKE 'demo-%' AND is_active = true;" | grep -v "^$$"
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'Invariant E (No completed-but-active):    ' || \
		 CASE WHEN COUNT(*) = 0 THEN 'PASS' \
		      ELSE 'FAIL — ' || COUNT(*) || ' tracked_event(s) lifecycle_phase=completed but is_active=true' END \
		 FROM tracked_events WHERE lifecycle_phase = 'completed' AND is_active = true;" | grep -v "^$$"
	@echo ""
	@echo "── Discovery metrics (current log window) ───"
	@docker compose logs backend --tail=1000 2>/dev/null | \
		grep -c "DISCOVERY: cycle complete" 2>/dev/null | \
		xargs -I{} echo "  discovery_run_count (in log window): {}" || echo "  discovery_run_count: 0"
	@docker compose logs backend --tail=1000 2>/dev/null | \
		grep "DISCOVERY: cycle complete" | tail -1 | \
		sed 's/backend-1  | //' | awk '{print "  last_discovery_run_at:              " $$1 " " $$2}' \
		|| echo "  last_discovery_run_at:              (no cycles in log window)"
	@docker compose logs backend --tail=1000 2>/dev/null | \
		grep "DISCOVERY: cycle complete" | \
		grep -oP 'duplicate=\K[0-9]+' | \
		awk '{s+=$$1} END {print "  dedupe_skips_count (duplicates):    " (s ? s : 0)}' \
		|| echo "  dedupe_skips_count: 0"
	@echo ""

build:
	docker compose build --no-cache

_wait:
	@echo "Waiting for db..."
	@for i in $$(seq 1 30); do \
		docker compose exec -T db pg_isready -U concert -q 2>/dev/null && break; \
		sleep 2; \
	done
	@echo "Waiting for backend..."
	@for i in $$(seq 1 45); do \
		curl -sf http://localhost:8000/api/health -o /dev/null 2>/dev/null && echo "  backend ready." && break; \
		sleep 3; \
	done
	@echo "Waiting for frontend (Next.js cold start)..."
	@for i in $$(seq 1 40); do \
		curl -sf http://localhost:3000 -o /dev/null 2>/dev/null && echo "  frontend ready." && break; \
		sleep 5; \
	done
