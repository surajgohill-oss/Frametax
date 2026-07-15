#!/usr/bin/env python3
"""Capture fresh screenshots of every major screen of the refined Prototype v1 artifact."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path("/Users/Suraj/cineglobe-frametax/frametax2/frontend/design-review/artifact-current")
BASE = "http://localhost:4173/prototype-v1-updated.html"
LU = "#/production/little-utopia"

async def fresh(page, sn, hashroute):
    await page.goto(f"{BASE}?s={sn}{hashroute}", wait_until="networkidle")
    await asyncio.sleep(0.7)

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = await ctx.new_page()
        errs = []
        page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(str(e)))

        # ── Production Overview (refined decision band) ──
        await fresh(page, 1, f"{LU}/overview")
        await page.screenshot(path=str(OUT / "01-overview.png"), full_page=True)
        # decision band clip
        await page.locator(".ov2-hero").first.screenshot(path=str(OUT / "02-decision-band.png"))
        # optimization queue clip
        el = page.locator(".ovsec", has_text="Optimization queue").first
        await el.scroll_into_view_if_needed(); await asyncio.sleep(0.2)
        await el.screenshot(path=str(OUT / "03-optimization-queue.png"))
        # cultural qualification clips
        sec = page.locator(".ovsec", has_text="Cultural qualification").first
        await sec.scroll_into_view_if_needed(); await asyncio.sleep(0.2)
        await page.locator(".cq.blocker").first.screenshot(path=str(OUT / "04-cultural-blocker.png"))
        await page.locator(".cq.opportunity").first.screenshot(path=str(OUT / "05-cultural-opportunity.png"))
        print("ok overview set")

        # ── Workspace: Lanes / Map / Split ──
        await fresh(page, 6, f"{LU}/workspace")
        await page.screenshot(path=str(OUT / "06-workspace-lanes.png"), full_page=True)
        await page.click("#tabMap"); await asyncio.sleep(0.9)
        await page.screenshot(path=str(OUT / "07-workspace-map.png"), full_page=True)
        await page.click("#tabSplit"); await asyncio.sleep(0.9)
        await page.screenshot(path=str(OUT / "08-workspace-split.png"), full_page=True)
        print("ok workspace views")

        # ── Allocation Inspector (open a lane) ──
        await fresh(page, 9, f"{LU}/workspace")
        await page.locator(".lane[data-lane]").first.click(); await asyncio.sleep(0.6)
        await page.screenshot(path=str(OUT / "09-allocation-inspector.png"), full_page=True)
        print("ok inspector")

        # ── Production sections ──
        for sn, sec, name in [(10,"scenarios","10-scenarios"),(11,"map","11-project-globe"),
                              (12,"documents","12-documents"),(13,"record","13-record"),
                              (14,"knowledge","14-knowledge"),(15,"reports","15-reports")]:
            await fresh(page, sn, f"{LU}/{sec}")
            await page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
        print("ok production sections")

        # ── Reference Library (refined precedent hierarchy) ──
        await fresh(page, 16, "#/knowledge")
        await page.locator('[data-ks="reference"]').click(); await asyncio.sleep(0.5)
        await page.screenshot(path=str(OUT / "16-reference-library.png"), full_page=True)
        print("ok reference library")

        # ── Company-level screens ──
        await fresh(page, 17, "#/dashboard")
        await page.screenshot(path=str(OUT / "17-today.png"), full_page=True)
        await fresh(page, 18, "#/world")
        await asyncio.sleep(0.8)
        await page.screenshot(path=str(OUT / "18-company-globe.png"), full_page=True)
        await fresh(page, 19, "#/knowledge")
        await page.screenshot(path=str(OUT / "19-company-knowledge.png"), full_page=True)
        await fresh(page, 20, "#/reports")
        await page.screenshot(path=str(OUT / "20-org-reports.png"), full_page=True)
        await fresh(page, 21, "#/settings")
        await page.screenshot(path=str(OUT / "21-settings.png"), full_page=True)
        print("ok company screens")

        await ctx.close(); await b.close()
        print("CONSOLE ERRORS:", errs if errs else "none")

if __name__ == "__main__":
    asyncio.run(run())
