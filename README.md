# LA Concert Watchlist Tracker

Personal-use secondary market ticket intelligence dashboard for LA concerts. Tracks StubHub and SeatGeek listings with section-level venue heatmaps, price history charts, and a self-diagnostic debug system.

## Venues tracked

- Hollywood Bowl
- Kia Forum
- Crypto.com Arena
- Greek Theatre
- SoFi Stadium

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), APScheduler |
| Scraping | Playwright (Chromium), httpx |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, Recharts |
| Infra | Docker Compose |

---

## Quick Start (Docker)

```bash
git clone <repo>
cd la-concert-watchlist
cp .env.example .env

docker compose up -d db redis
docker compose run --rm seed        # seed venues + marketplaces
docker compose up -d backend frontend
```

Open http://localhost:3000

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Start postgres + redis locally (or use docker compose up -d db redis)
cp ../.env.example ../.env

# Apply migrations
alembic upgrade head

# Seed venues
cd ..
python scripts/seed_db.py

# Run backend
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

---

## Adding Events

1. Open http://localhost:3000/events/new
2. Paste the StubHub and/or SeatGeek URLs for the event
3. Set the poll interval (minimum 15 minutes)
4. The scheduler auto-polls at the specified interval

Maximum 30 events tracked simultaneously.

---

## Debug System

### Debug Mode CLI

Run a single collector in headed browser mode with verbose logging:

```bash
cd backend
# Basic debug run
python run_collector.py --marketplace stubhub --event-id 12345678 --debug

# Slow-motion (500ms between actions)
python run_collector.py --marketplace stubhub --event-id 12345678 --debug --slow-mo 500

# Step-through mode (press Enter between each action)
python run_collector.py --marketplace stubhub --event-id 12345678 --debug --step

# View recent errors
python run_collector.py --show-errors --marketplace stubhub

# View failure memory
python run_collector.py --show-memory

# Clear failure memory for a marketplace
python run_collector.py --clear-memory --marketplace stubhub
```

### Chrome Attach Mode (CDP)

Attach Playwright to a running Chrome instance for live DOM inspection:

```bash
# 1. Launch Chrome with remote debugging enabled
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug

# 2. Navigate to the StubHub/SeatGeek event page and log in

# 3. Attach the collector
python run_collector.py \
  --marketplace stubhub \
  --event-id 12345678 \
  --chrome-attach \
  --chrome-port 9222
```

The collector reuses the running browser's cookies and session — no re-login needed.

### Bootstrapping Browser Sessions (for headless polling)

```bash
# StubHub
python scripts/bootstrap_session.py stubhub
# Log in manually, then close the browser

# SeatGeek
python scripts/bootstrap_session.py seatgeek
```

Sessions are saved to `backend/browser_sessions/` and reused by the scheduler.

### Debug Dashboard

Visit http://localhost:3000/debug to see:
- Error log with full details (selector, URL, HTTP status, raw sample, screenshot path)
- Failure memory table (auto-skipped patterns + known-good fallbacks)
- Controls to delete individual memory entries or clear all for a marketplace
- Test Collect button to trigger a headless test scrape from the UI

---

## Architecture

```
backend/
  app/
    api/routes/      FastAPI route handlers
    collectors/      StubHub + SeatGeek scrapers + debug mixin
    models/          SQLAlchemy ORM models
    scheduler.py     APScheduler master job
    config.py        Pydantic settings
  migrations/        Alembic schema migrations
  run_collector.py   Debug CLI tool

frontend/
  src/
    app/             Next.js pages (App Router)
    components/      Reusable UI + charts + venue heatmap
    lib/             API client + utilities

shared/
  venue_maps/        Section geometry JSON for all 5 venues
```

### Failure Memory

The `failure_memory` table records selector patterns that fail. After 3 consecutive failures, `skip_failed` is set to `True` and the pattern is auto-skipped on future runs. When a fallback selector succeeds, it's stored as `fallback_pattern` and used automatically.

This is pure rule-based — no ML or AI inference.
