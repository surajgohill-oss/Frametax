# LA Concert Watchlist Tracker

Personal-use secondary market ticket intelligence dashboard for LA concerts.

## Quick Start

```bash
git clone -b claude/concert-watchlist-tracker-Uia95 https://github.com/surajgohill-oss/Frametax.git la-concert-watchlist
cd la-concert-watchlist
cp .env.example .env
docker compose up -d db redis
sleep 12
docker compose run --rm seed
docker compose up -d backend frontend
open http://localhost:3000
```

## Venues
- Hollywood Bowl
- Kia Forum
- Crypto.com Arena
- Greek Theatre
- SoFi Stadium
