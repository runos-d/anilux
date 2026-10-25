import { test, expect } from "@playwright/test";
import { readdirSync } from "node:fs";
import { relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { installVisualSession } from "./fixtures.js";
import { assertStableSurface, capturePaletteAudit, captureSurface, themes, waitForVisualReady } from "./visual-utils.js";

test.describe.configure({ mode: "parallel" });

const componentsRoot = fileURLToPath(new URL("../../src/components", import.meta.url));

function collectModalKeys(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const absolute = resolve(directory, entry.name);
    if (entry.isDirectory()) return collectModalKeys(absolute);
    if (!/(?:Modal|Dialog)\.vue$/.test(entry.name)) return [];
    return [`../components/${relative(componentsRoot, absolute).replaceAll("\\", "/")}`];
  });
}

const modalKeys = collectModalKeys(componentsRoot).sort((left, right) => left.localeCompare(right, "ru"));

test("modal harness discovers every modal and dialog", async ({ page }) => {
  await installVisualSession(page, "dark");
  await page.goto("/__visual__/modals", { waitUntil: "domcontentloaded" });
  await waitForVisualReady(page);
  const renderedKeys = await page.locator("[data-modal-key]").evaluateAll((nodes) => nodes.map((node) => node.getAttribute("data-modal-key")).filter(Boolean));
  expect(renderedKeys.sort()).toEqual([...modalKeys].sort());
  expect(renderedKeys.length).toBeGreaterThanOrEqual(55);
});

for (const key of modalKeys) {
  const label = key.replace("../components/", "").replace(/\.vue$/, "");
  const slug = label.replaceAll("/", "--").toLowerCase();
  for (const theme of themes) {
    test(`modal · ${label} · ${theme}`, async ({ page }) => {
      const runtimeErrors = [];
      const consoleErrors = [];
      page.on("pageerror", (error) => runtimeErrors.push(error.message));
      page.on("console", (message) => {
        if (message.type() === "error" && !message.text().includes("favicon")) consoleErrors.push(message.text());
      });
      await installVisualSession(page, theme);
      await page.goto(`/__visual__/modals?name=${encodeURIComponent(key)}`, { waitUntil: "domcontentloaded" });
      await waitForVisualReady(page);
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      await page.waitForTimeout(80);
      await assertStableSurface(page, label);
      await captureSurface(page, `modal--${slug}--${theme}`, { fullPage: false });
      await page.setViewportSize({ width: 1440, height: 1000 });
      await capturePaletteAudit(page, `modal--${slug}--${theme}`, theme);
      expect(runtimeErrors, `${label}: uncaught page errors`).toEqual([]);
      expect(consoleErrors, `${label}: console errors`).toEqual([]);
    });
  }
}
