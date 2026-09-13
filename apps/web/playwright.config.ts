import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: 1,
  use: {
    baseURL: process.env.E2E_WEB_URL ?? "http://localhost:3000",
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
    trace: "off", // Authentication tokens and one-time keys must not enter trace artifacts.
  },
});
