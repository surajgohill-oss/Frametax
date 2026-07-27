#!/usr/bin/env python3
"""
Capture screenshots of all major screens in FrameTax 2.0 frontend.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, expect

SCREENSHOT_DIR = Path("/Users/Suraj/cineglobe-frametax/frametax2/frontend/design-review/current")
BASE_URL = "http://localhost:5173"

SCREENS = [
    ("01-today", "/company/today"),
    ("02-company-globe", "/company/globe"),
    ("03-company-knowledge", "/company/knowledge"),
    ("04-organization-reports", "/company/reports"),
]

async def capture_screens():
    """Capture screenshots of each screen."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        for filename, path in SCREENS:
            try:
                print(f"Capturing {filename}...")
                url = BASE_URL + path
                await page.goto(url, wait_until="networkidle")
                await asyncio.sleep(1)  # Extra time for any animations

                screenshot_path = SCREENSHOT_DIR / f"{filename}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"✓ Saved {filename}.png ({screenshot_path})")
            except Exception as e:
                print(f"✗ Failed to capture {filename}: {e}")

        await context.close()
        await browser.close()
        print(f"\nAll screenshots saved to {SCREENSHOT_DIR}")

if __name__ == "__main__":
    asyncio.run(capture_screens())
