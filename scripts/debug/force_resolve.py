#!/usr/bin/env python3
"""
force_resolve.py
Force one resolver cycle — upgrades demo-prefixed + NULL external_event_ids.
Run inside backend container: python3 /shared_scripts/debug/force_resolve.py
"""
import asyncio
import logging
import sys

sys.path.insert(0, "/app")

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s — %(message)s",
)

from app.collectors.resolver import EventResolver
from app.config import get_settings
from app.database import AsyncSessionLocal


async def main() -> None:
    settings = get_settings()
    resolver = EventResolver(settings)
    try:
        counts = await resolver.resolve_all_pending(AsyncSessionLocal)
        print(
            f"\nRESOLVER RESULT: resolved={counts['resolved']} "
            f"failed={counts['failed']} already_set={counts['already_set']}"
        )
        if counts["resolved"] == 0 and counts["failed"] > 0:
            print(
                "  → All resolution attempts failed.\n"
                "  → Likely EXTERNAL_BLOCK (no credentials / network).\n"
                "  → Demo listings remain in DB — ENRICH will still show them."
            )
    finally:
        await resolver.close()


asyncio.run(main())
