import { defineConfig } from "@playwright/test";
import path from "path";

export default defineConfig({
  testDir: path.join(__dirname),
  testMatch: "capture.spec.ts",
  timeout: 30_000,
  retries: 0,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://localhost:3000",
    headless: true,
    viewport: { width: 1280, height: 720 },
  },
});
