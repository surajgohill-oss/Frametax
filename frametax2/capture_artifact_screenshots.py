#!/usr/bin/env python3
"""Capture the 7 canonical review states of the updated Prototype v1 artifact."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path("/Users/Suraj/cineglobe-frametax/frametax2/frontend/design-review/artifact-current")
BASE = "http://localhost:4173/prototype-v1-updated.html"

async def fresh(page, sn, hashroute):
    # cache-buster query forces a full document load so hash routing re-inits cleanly
    await page.goto(f"{BASE}?s={sn}{hashroute}", wait_until="networkidle")
    await asyncio.sleep(0.7)

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = await ctx.new_page()

        # 1 — Overview with doctrine/status surfaces (full page)
        await fresh(page, 1, "#/production/little-utopia/overview")
        await page.screenshot(path=str(OUT / "01-overview-doctrine.png"), full_page=True)
        print("ok 01-overview-doctrine")

        # 2 — Qualification Assistant (section clip)
        await fresh(page, 2, "#/production/little-utopia/overview")
        el = page.locator(".ovsec", has_text="Qualification assistant").first
        await el.scroll_into_view_if_needed(); await asyncio.sleep(0.2)
        await el.screenshot(path=str(OUT / "02-qualification-assistant.png"))
        print("ok 02-qualification-assistant")

        # 3 — Cultural eligibility blocker (card clip, with section header for context)
        sec = page.locator(".ovsec", has_text="Cultural qualification").first
        await sec.scroll_into_view_if_needed(); await asyncio.sleep(0.2)
        await page.locator(".cq.blocker").first.screenshot(path=str(OUT / "03-cultural-eligibility-blocker.png"))
        print("ok 03-cultural-eligibility-blocker")

        # 4 — Cultural points opportunity (card clip)
        await page.locator(".cq.opportunity").first.screenshot(path=str(OUT / "04-cultural-points-opportunity.png"))
        print("ok 04-cultural-points-opportunity")

        # 5 — Workspace Lanes (full page)
        await fresh(page, 5, "#/production/little-utopia/workspace")
        await page.screenshot(path=str(OUT / "05-workspace-lanes.png"), full_page=True)
        print("ok 05-workspace-lanes")

        # 6 — Allocation Inspector (open a lane, then capture rack + inspector)
        await fresh(page, 6, "#/production/little-utopia/workspace")
        lane = page.locator(".lane[data-lane]").first
        await lane.click()
        await asyncio.sleep(0.6)
        await page.screenshot(path=str(OUT / "06-allocation-inspector.png"), full_page=True)
        print("ok 06-allocation-inspector")

        # 7 — Reference Library (Company Knowledge -> reference segment)
        await fresh(page, 7, "#/knowledge")
        await page.locator('[data-ks="reference"]').click()
        await asyncio.sleep(0.5)
        await page.screenshot(path=str(OUT / "07-reference-library.png"), full_page=True)
        print("ok 07-reference-library")

        await ctx.close(); await b.close()
        print("done")

if __name__ == "__main__":
    asyncio.run(run())
