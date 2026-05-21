#!/bin/bash
# Layer 0 — System Discovery
# Confirms Docker is running and required services are listening on expected ports.
set -euo pipefail

echo "Checking Docker daemon..."
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker daemon is not running"
  echo "   Fix: start Docker Desktop or 'sudo systemctl start docker'"
  exit 1
fi
echo "  docker daemon  ✓"

echo ""
echo "Checking container health..."
CONTAINERS=$(docker compose -f "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/docker-compose.yml" ps --format json 2>/dev/null || echo "")
if [ -z "$CONTAINERS" ]; then
  echo "❌ No containers found — stack is not up"
  echo "   Fix: make up"
  exit 1
fi

for svc in db redis backend frontend; do
  if docker compose ps "$svc" 2>/dev/null | grep -q "running\|Up"; then
    echo "  $svc  ✓"
  else
    echo "❌ Service not running: $svc"
    echo "   Fix: make up  (or: docker compose up -d $svc)"
    exit 1
  fi
done

echo ""
echo "Checking TCP ports..."
for port in 3000 8000 5432; do
  if lsof -i TCP:"$port" -sTCP:LISTEN -P -n > /dev/null 2>&1 || \
     ss -tlnH "sport = :$port" 2>/dev/null | grep -q "$port"; then
    echo "  :$port  ✓"
  else
    echo "❌ Nothing listening on port $port"
    exit 1
  fi
done
