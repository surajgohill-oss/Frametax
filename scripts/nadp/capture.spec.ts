/**
 * NADP Playwright Capture
 *
 * Generates the 4 artifacts required by the kernel:
 *   .artifacts/api.json        — canonical backend truth
 *   .artifacts/dom.json        — structural DOM snapshot
 *   .artifacts/console.json    — runtime + hydration errors
 *   .artifacts/screenshot.png  — visual verification
 *
 * Run: npx playwright test --config scripts/nadp/playwright.config.ts
 */
import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

const BACKEND = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const OUT = path.join(__dirname, ".artifacts");
fs.mkdirSync(OUT, { recursive: true });

test("capture nadp artifacts", async ({ page, request }) => {

  // ── api.json — canonical backend truth ──────────────────────────────────────
  const apiResponse = await request.get(`${BACKEND}/api/events/`);
  expect(apiResponse.status(), "backend /api/events/ must return 200").toBe(200);
  const apiData = await apiResponse.json();
  fs.writeFileSync(
    path.join(OUT, "api.json"),
    JSON.stringify(apiData, null, 2)
  );

  // ── console.json — capture runtime errors before navigation ─────────────────
  const consoleEntries: { type: string; text: string; url: string }[] = [];
  const pageErrors: { message: string; stack: string }[] = [];

  page.on("console", (msg) => {
    consoleEntries.push({
      type: msg.type(),
      text: msg.text(),
      url: msg.location().url || "",
    });
  });

  page.on("pageerror", (err) => {
    pageErrors.push({ message: err.message, stack: err.stack || "" });
  });

  // ── Navigate and wait for hydration ─────────────────────────────────────────
  await page.goto("/", { waitUntil: "networkidle" });

  // Wait for event cards or empty state — whichever appears first
  await Promise.race([
    page.waitForSelector("[data-testid='event-card']", { timeout: 10_000 }).catch(() => null),
    page.waitForSelector("text=No events tracked yet", { timeout: 10_000 }).catch(() => null),
  ]);

  // ── dom.json — structural snapshot ──────────────────────────────────────────
  const eventCards = await page.$$eval("[data-testid='event-card']", (nodes) =>
    nodes.map((el) => ({
      eventId: el.getAttribute("data-event-id"),
      canonicalId: el.getAttribute("data-canonical-id"),
      titleText: el.querySelector("h3")?.textContent?.trim() ?? null,
      hasPrice: !!el.querySelector("p"),
      hasViewButton: !!el.querySelector("a[href^='/events/']"),
    }))
  );

  const sections = await page.$$eval("section", (nodes) =>
    nodes.map((el) => ({
      heading: el.querySelector("h2")?.textContent?.trim() ?? null,
      cardCount: el.querySelectorAll("[data-testid='event-card']").length,
    }))
  );

  const emptyState = await page.$("text=No events tracked yet") !== null;

  fs.writeFileSync(
    path.join(OUT, "dom.json"),
    JSON.stringify({ eventCards, sections, emptyState, url: page.url() }, null, 2)
  );

  // ── screenshot.png ───────────────────────────────────────────────────────────
  await page.screenshot({
    path: path.join(OUT, "screenshot.png"),
    fullPage: true,
  });

  // ── console.json ─────────────────────────────────────────────────────────────
  fs.writeFileSync(
    path.join(OUT, "console.json"),
    JSON.stringify({ consoleEntries, pageErrors }, null, 2)
  );

  // Soft assertion: log artifact summary, don't fail the capture on mismatch
  // (kernel.py does the analysis — capture only collects evidence)
  const apiCount = Array.isArray(apiData) ? apiData.length : 0;
  const domCount = eventCards.length;
  console.log(`\nCapture complete:`);
  console.log(`  api.json        : ${apiCount} events`);
  console.log(`  dom.json        : ${domCount} event cards`);
  console.log(`  console errors  : ${pageErrors.length} page errors, ` +
              `${consoleEntries.filter(e => e.type === "error").length} console errors`);
  console.log(`  screenshot.png  : written`);
  console.log(`\nRun analysis: python3 scripts/nadp/kernel.py`);
});
