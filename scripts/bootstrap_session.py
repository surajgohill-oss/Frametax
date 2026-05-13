#!/usr/bin/env python3
"""
Bootstrap persistent browser sessions for StubHub / SeatGeek.

Usage:
    python scripts/bootstrap_session.py stubhub
    python scripts/bootstrap_session.py seatgeek

Opens a headed browser. Log in manually, then close it.
Cookies are saved to browser_sessions/<marketplace>/ and reused by the collector.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from playwright.async_api import async_playwright

URLS = {
    "stubhub": "https://www.stubhub.com/login",
    "seatgeek": "https://seatgeek.com/login",
}

BROWSER_DATA_DIR = Path(__file__).parent.parent / "backend" / "browser_sessions"


async def bootstrap(marketplace: str):
    url = URLS.get(marketplace)
    if not url:
        print(f"Unknown marketplace '{marketplace}'. Choices: {list(URLS)}")
        sys.exit(1)

    session_path = BROWSER_DATA_DIR / marketplace
    session_path.mkdir(parents=True, exist_ok=True)

    print(f"\nOpening {marketplace} login at {url}")
    print("Log in, then close the browser window.\n")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(session_path),
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--no-sandbox"],
        )
        page = await context.new_page()
        await page.goto(url)

        print("Waiting for browser close...")
        try:
            await page.wait_for_event("close", timeout=300000)
        except Exception:
            pass

        cookies = await context.cookies()
        cookie_file = session_path / "cookies.json"
        cookie_file.write_text(json.dumps(cookies, indent=2))
        print(f"\nSaved {len(cookies)} cookies to {cookie_file}")
        await context.close()

    print(f"\n✓ {marketplace} session bootstrapped. The collector will reuse this session.")


if __name__ == "__main__":
    mp = sys.argv[1] if len(sys.argv) > 1 else "stubhub"
    asyncio.run(bootstrap(mp))
