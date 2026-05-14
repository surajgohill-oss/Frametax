#!/usr/bin/env python3
"""CLI for testing collectors directly without the full API stack."""
import asyncio
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.collectors.registry import get_collector, COLLECTOR_REGISTRY
from app.database import AsyncSessionLocal


async def run(marketplace: str, url: str, event_id: int | None):
    print(f"Running {marketplace} collector for URL: {url}")
    collector_cls = get_collector(marketplace)
    if not collector_cls:
        print(f"Unknown marketplace: {marketplace}. Available: {list(COLLECTOR_REGISTRY.keys())}")
        return

    async with AsyncSessionLocal() as session:
        collector = collector_cls(session)
        result = await collector.collect(url=url, event_id=event_id or 0, tracked_event_id=0)

    print(f"\nStatus: {result.status}")
    print(f"Listings collected: {len(result.listings)}")
    if result.error:
        print(f"Error: {result.error}")
    if result.listings:
        print("\nSample listings (first 5):")
        for listing in result.listings[:5]:
            print(f"  Section: {listing.section_name}, Row: {listing.row}, "
                  f"Qty: {listing.quantity}, Price: ${listing.price_each:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Test a collector directly")
    parser.add_argument("marketplace", choices=list(COLLECTOR_REGISTRY.keys()))
    parser.add_argument("url", help="Event URL on the marketplace")
    parser.add_argument("--event-id", type=int, default=0, help="Event ID (optional)")
    args = parser.parse_args()
    asyncio.run(run(args.marketplace, args.url, args.event_id))


if __name__ == "__main__":
    main()
