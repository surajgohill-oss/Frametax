#!/usr/bin/env python3
"""Bootstrap a Playwright browser session for StubHub to persist cookies/auth."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from playwright.async_api import async_playwright
from app.config import settings


async def bootstrap():
    browser_dir = Path(settings.browser_data_dir)
    browser_dir.mkdir(parents=True, exist_ok=True)

    print("Launching browser for session bootstrap...")
    print("Please complete any CAPTCHA or login required, then press Ctrl+C when done.")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(browser_dir),
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        page = await context.new_page()
        await page.goto("https://www.stubhub.com")
        try:
            await page.wait_for_timeout(300_000)
        except KeyboardInterrupt:
            pass
        finally:
            await context.close()
    print("Session saved to", browser_dir)


if __name__ == "__main__":
    asyncio.run(bootstrap())
