#!/usr/bin/env python3
"""
bootstrap_sofi.py — Seed SoFi Stadium venue intelligence data into Railway.

Seeds:
  1. venues row for SoFi Stadium (upsert by slug)
  2. venue_sections rows from SECTIONS catalog (upsert by venue_id+section_id)
  3. venue_section_aliases rows from ALIASES catalog (upsert by venue_section_id+marketplace_id+alias_normalized)

Usage:
  python3 backend/scripts/bootstrap_sofi.py

Requires DATABASE_URL in environment (or .env file in backend/).
"""
import asyncio
import os
import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

# Load .env if present
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

import asyncpg
from sofi_catalog import SECTIONS, ALIASES, VENUE_SLUG, VENUE_NAME, VENUE_CITY, VENUE_STATE, VENUE_CAPACITY


async def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    # asyncpg expects postgresql:// not postgres://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to Railway…")
    conn = await asyncpg.connect(db_url)
    print("Connected ✓")

    try:
        # ── 1. Upsert venue ────────────────────────────────────────────────
        venue_id = await conn.fetchval("""
            INSERT INTO venues (slug, name, city, state, capacity)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (slug) DO UPDATE SET
                name     = EXCLUDED.name,
                city     = EXCLUDED.city,
                state    = EXCLUDED.state,
                capacity = EXCLUDED.capacity
            RETURNING id
        """, VENUE_SLUG, VENUE_NAME, VENUE_CITY, VENUE_STATE, VENUE_CAPACITY)
        print(f"Venue '{VENUE_SLUG}' → id={venue_id} ✓")

        # ── 2. Upsert venue_sections ───────────────────────────────────────
        section_db_ids: dict[str, int] = {}
        inserted = 0
        for s in SECTIONS:
            row_id = await conn.fetchval("""
                INSERT INTO venue_sections (
                    venue_id, section_id, display_name, tier,
                    level, zone, side, quality_score, is_premium, future_map_key
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (venue_id, section_id) DO UPDATE SET
                    display_name  = EXCLUDED.display_name,
                    tier          = EXCLUDED.tier,
                    level         = EXCLUDED.level,
                    zone          = EXCLUDED.zone,
                    side          = EXCLUDED.side,
                    quality_score = EXCLUDED.quality_score,
                    is_premium    = EXCLUDED.is_premium,
                    future_map_key = EXCLUDED.future_map_key
                RETURNING id
            """,
                venue_id,
                s["section_id"],
                s["display_name"],
                s["tier"],
                s["level"],
                s["zone"],
                s["side"],
                s["quality_score"],
                s["is_premium"],
                s["future_map_key"],
            )
            section_db_ids[s["section_id"]] = row_id
            inserted += 1

        print(f"venue_sections: {inserted} sections upserted ✓")

        # ── 3. Upsert venue_section_aliases ───────────────────────────────
        alias_ok = 0
        alias_skip = 0
        for a in ALIASES:
            sid = a["section_id"]
            if sid not in section_db_ids:
                alias_skip += 1
                continue
            vs_id = section_db_ids[sid]
            raw = a["alias"]
            norm = raw.strip().lower()
            import re
            norm = re.sub(r"\s+", " ", norm)
            mp_id = a.get("marketplace_id")  # may be None
            et = a.get("event_type")  # may be None

            if mp_id is not None:
                await conn.execute("""
                    INSERT INTO venue_section_aliases
                        (venue_section_id, marketplace_id, alias, alias_normalized, event_type)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (venue_section_id, marketplace_id, alias_normalized)
                    WHERE marketplace_id IS NOT NULL
                    DO UPDATE SET alias = EXCLUDED.alias, event_type = EXCLUDED.event_type
                """, vs_id, mp_id, raw, norm, et)
            else:
                await conn.execute("""
                    INSERT INTO venue_section_aliases
                        (venue_section_id, marketplace_id, alias, alias_normalized, event_type)
                    VALUES ($1, NULL, $2, $3, $4)
                    ON CONFLICT (venue_section_id, alias_normalized)
                    WHERE marketplace_id IS NULL
                    DO UPDATE SET alias = EXCLUDED.alias, event_type = EXCLUDED.event_type
                """, vs_id, raw, norm, et)
            alias_ok += 1

        print(f"venue_section_aliases: {alias_ok} aliases upserted, {alias_skip} skipped ✓")

        # ── 4. Summary ────────────────────────────────────────────────────
        total_sections = await conn.fetchval(
            "SELECT COUNT(*) FROM venue_sections WHERE venue_id = $1", venue_id
        )
        total_aliases = await conn.fetchval("""
            SELECT COUNT(*) FROM venue_section_aliases vsa
            JOIN venue_sections vs ON vs.id = vsa.venue_section_id
            WHERE vs.venue_id = $1
        """, venue_id)
        print()
        print("─" * 50)
        print(f"SoFi Stadium bootstrap complete")
        print(f"  venue_id      : {venue_id}")
        print(f"  sections      : {total_sections}")
        print(f"  aliases       : {total_aliases}")
        print("─" * 50)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
