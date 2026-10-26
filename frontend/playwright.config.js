import { defineConfig } from "@playwright/test";
import { createArgosReporterOptions } from "@argos-ci/playwright/reporter";

const baseURL = "http://127.0.0.1:4399";

export default defineConfig({
  testDir: "./tests/visual",
  fullyParallel: true,
  timeout: 90_000,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [
    process.env.CI ? ["dot"] : ["list"],
    [
      "@argos-ci/playwright/reporter",
      createArgosReporterOptions({ uploadToArgos: !!process.env.CI }),
    ],
  ],
  webServer: {
    command: "node scripts/run-vite-build.mjs --mode visual && npx vite preview --host=127.0.0.1 --port=4399 --strictPort",
    url: baseURL,
    reuseExistingServer: false,
    timeout: 180_000,
  },
  use: {
    baseURL,
    serviceWorkers: "block",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    launchOptions: {
      args: ["--disable-lcd-text", "--font-render-hinting=none"],
    },
  },
});
