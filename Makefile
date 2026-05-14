.PHONY: up down reset logs status build

up:
	docker compose up --build -d
	@$(MAKE) --no-print-directory _wait
	@$(MAKE) --no-print-directory status

down:
	docker compose down

reset:
	docker compose down -v --remove-orphans
	docker compose up --build -d
	@$(MAKE) --no-print-directory _wait
	@$(MAKE) --no-print-directory status

logs:
	docker compose logs -f --tail=100

logs-%:
	docker compose logs -f --tail=100 $*

status:
	@echo ""
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
	@echo "Waiting for services to become healthy..."
	@for i in $$(seq 1 30); do \
		docker compose exec -T db pg_isready -U concert -q 2>/dev/null && break; \
		sleep 2; \
	done
	@sleep 3
