"""
SpotifyResolver — resolves Spotify artist metadata for events.

Uses the Spotify Web API (client_credentials flow).
Required env vars: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

Resolution status values:
  RESOLVED             — artist found and persisted
  NOT_FOUND            — no matching artist in Spotify catalog
  AMBIGUOUS            — multiple high-confidence matches, skipped
  API_NOT_CONFIGURED   — credentials not set
  ALREADY_RESOLVED     — spotify_artist_id already set
"""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://accounts.spotify.com/api/token"
_SEARCH_URL = "https://api.spotify.com/v1/search"
_ARTIST_URL = "https://api.spotify.com/v1/artists/{}"


def _normalize(name: str) -> str:
    """Lowercase, strip accents, collapse punctuation/spaces."""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^\w\s]", " ", name.lower())
    return re.sub(r"\s+", " ", name).strip()


class SpotifyResolver:
    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token: Optional[str] = None
        self._token_expires: datetime = datetime.utcnow()
        self._http: Optional[httpx.AsyncClient] = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        return self._http

    async def close(self):
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    async def _ensure_token(self) -> bool:
        if self._access_token and datetime.utcnow() < self._token_expires:
            return True
        try:
            resp = await self._client().post(
                _TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=(self._client_id, self._client_secret),
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            self._token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 60)
            return True
        except Exception as exc:
            logger.error("Spotify: token fetch failed — %s", exc)
            return False

    async def resolve_artist(self, artist_name: str) -> dict:
        """
        Search Spotify for artist_name. Returns:
          {"status": "RESOLVED", "id": "...", "url": "...", "name": "...", "popularity": N}
          {"status": "NOT_FOUND"}
          {"status": "AMBIGUOUS", "candidates": [...]}
          {"status": "API_NOT_CONFIGURED"}
        """
        if not self._client_id or not self._client_secret:
            return {"status": "API_NOT_CONFIGURED"}

        if not await self._ensure_token():
            return {"status": "API_NOT_CONFIGURED"}

        norm_query = _normalize(artist_name)
        try:
            resp = await self._client().get(
                _SEARCH_URL,
                params={"q": artist_name, "type": "artist", "limit": 5},
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
            resp.raise_for_status()
            artists = resp.json().get("artists", {}).get("items", [])
        except Exception as exc:
            logger.error("Spotify: search failed for '%s' — %s", artist_name, exc)
            return {"status": "API_NOT_CONFIGURED"}

        if not artists:
            return {"status": "NOT_FOUND"}

        # Score each result by normalized name match
        scored = []
        for a in artists:
            norm_result = _normalize(a.get("name", ""))
            if norm_result == norm_query:
                score = 2  # exact
            elif norm_query in norm_result or norm_result in norm_query:
                score = 1  # partial
            else:
                score = 0
            scored.append((score, a.get("popularity", 0), a))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_score = scored[0][0]

        if best_score == 0:
            return {"status": "NOT_FOUND"}

        # Check for ambiguity: multiple exact matches with similar popularity
        exact = [s for s in scored if s[0] == best_score]
        if len(exact) > 1 and abs(exact[0][1] - exact[1][1]) < 5:
            return {
                "status": "AMBIGUOUS",
                "candidates": [{"id": s[2]["id"], "name": s[2]["name"]} for s in exact[:3]],
            }

        best = scored[0][2]
        return {
            "status": "RESOLVED",
            "id": best["id"],
            "url": best.get("external_urls", {}).get("spotify", f"https://open.spotify.com/artist/{best['id']}"),
            "name": best["name"],
            "popularity": best.get("popularity", 0),
        }

    async def resolve_all_events(self, session_factory, force: bool = False) -> dict:
        """
        Resolve Spotify artist metadata for all events with artist set
        but no spotify_artist_id. Returns counts dict.
        """
        from app.models.event import Event

        counts = {"resolved": 0, "not_found": 0, "ambiguous": 0, "skipped": 0, "api_not_configured": 0}

        if not self._client_id or not self._client_secret:
            logger.warning("Spotify: SPOTIFY_CLIENT_ID/SECRET not configured — skipping resolution")
            counts["api_not_configured"] = 1
            return counts

        async with session_factory() as db:
            query = select(Event).where(Event.artist.isnot(None))
            if not force:
                query = query.where(Event.spotify_artist_id.is_(None))
            events = (await db.execute(query)).scalars().all()

        for event in events:
            if not event.artist:
                continue
            result = await self.resolve_artist(event.artist)
            status = result["status"]

            if status == "RESOLVED":
                async with session_factory() as db:
                    await db.execute(
                        sa_update(Event)
                        .where(Event.id == event.id)
                        .values(
                            spotify_artist_id=result["id"],
                            spotify_artist_url=result["url"],
                        )
                    )
                    await db.commit()
                logger.info(
                    "Spotify: resolved '%s' → %s (popularity=%s)",
                    event.artist, result["id"], result.get("popularity"),
                )
                counts["resolved"] += 1
            elif status == "API_NOT_CONFIGURED":
                counts["api_not_configured"] += 1
                break
            elif status == "NOT_FOUND":
                logger.debug("Spotify: artist not found — '%s'", event.artist)
                counts["not_found"] += 1
            elif status == "AMBIGUOUS":
                logger.info("Spotify: ambiguous — '%s' candidates=%s", event.artist, result.get("candidates"))
                counts["ambiguous"] += 1
            else:
                counts["skipped"] += 1

        return counts
