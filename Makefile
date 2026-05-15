.PHONY: up down reset logs status build verify

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
