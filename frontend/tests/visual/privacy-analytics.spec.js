import { test, expect } from "@playwright/test";
import { installVisualSession } from "./fixtures.js";

test("analytics consent is accessible on mobile and denial sends no provider requests", async ({ page }) => {
  const providerRequests = [];
  page.on("request", request => {
    if (/mc\.yandex\.(?:ru|com)|googletagmanager\.com|google-analytics\.com/.test(request.url())) {
      providerRequests.push(request.url());
    }
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await installVisualSession(page, "dark", "unknown");
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const dialog = page.getByRole("dialog", { name: "Помочь улучшать AniLux?" });
  await expect(dialog).toBeVisible();
  const deny = dialog.getByRole("button", { name: "Не разрешать" });
  const grant = dialog.getByRole("button", { name: "Разрешить", exact: true });
  await expect(deny).toBeVisible();
  await expect(grant).toBeVisible();
  await deny.focus();
  await expect(deny).toBeFocused();
  expect(providerRequests).toEqual([]);

  await deny.click();
  await expect(dialog).toBeHidden();
  await page.waitForTimeout(100);
  expect(providerRequests).toEqual([]);

  await page.reload({ waitUntil: "domcontentloaded" });
  await expect(dialog).toBeHidden();
  expect(providerRequests).toEqual([]);
});
