.PHONY: up down reset logs status build verify debug-snapshot

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
		grep -iE "resolver|STAGE_GATE|ERROR|WARNING|Cannot resolve" | tail -20 || true
	@echo ""
	@echo "── Invariant violations ──────────────────"
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'Stage 2 pending: ' || COUNT(*) || ' tracked_event(s) have no external_event_id' \
		 FROM tracked_events WHERE external_event_id IS NULL AND is_active = true;" | grep -v "^$$" || true
	@docker compose exec -T db psql -U concert -d concert_tracker -t -c \
		"SELECT 'Stage 3 empty: ' || COUNT(DISTINCT e.id) || ' event(s) have 0 active listings' \
		 FROM events e WHERE NOT EXISTS \
		   (SELECT 1 FROM listings l WHERE l.event_id = e.id AND l.is_active = true);" | grep -v "^$$" || true
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
