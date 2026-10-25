import { test, expect } from "@playwright/test";
import { installVisualSession } from "./fixtures.js";
import { assertStableSurface, capturePaletteAudit, captureSurface, themes, waitForVisualReady } from "./visual-utils.js";

const pages = [
  ["home", "/"],
  ["login", "/login"],
  ["register", "/register"],
  ["confirm-email", "/confirm-email?token=visual-token"],
  ["reset-password", "/reset-password?token=visual-token"],
  ["oauth-callback", "/oauth/callback?error=visual-test"],
  ["contacts", "/contacts"],
  ["terms", "/terms"],
  ["privacy", "/privacy"],
  ["license", "/license"],
  ["application", "/app"],
  ["anime-overview", "/anime"],
  ["anime-catalog", "/anime?section=catalog"],
  ["anime-ongoings", "/anime?section=ongoings"],
  ["anime-announcements", "/anime?section=announcements"],
  ["anime-calendar", "/anime?section=calendar"],
  ["anime-recommendations", "/anime?section=recommendations"],
  ["anime-currently-watching", "/anime?section=currently_watching"],
  ["anime-browse", "/anime/browse"],
  ["anime-year", "/anime/year/2024"],
  ["anime-genre", "/anime/genre/drama"],
  ["anime-type", "/anime/type/tv"],
  ["anime-status", "/anime/status/ongoing"],
  ["anime-season", "/anime/season/2024/spring"],
  ["anime-collection", "/anime/collection/quiet-stories"],
  ["anime-detail", "/anime/1-fioletovyy-sad"],
  ["anime-watch", "/anime/1-fioletovyy-sad/watch"],
  ["franchise", "/franchise/fioletovyy-sad"],
  ["roulette", "/roulette"],
  ["people", "/people"],
  ["public-profile", "/@sakura-reader"],
  ["own-profile", "/profile"],
  ["achievements", "/achievements"],
  ["feed", "/feed"],
  ["news", "/news"],
  ["ideas", "/ideas"],
  ["post-detail", "/post/101"],
  ["chats", "/chats"],
  ["chat-private", "/chats/12345678"],
  ["chat-group", "/chats/11111111-1111-4111-8111-111111111111"],
  ["chat-topic", "/chats/11/topic/general"],
  ["chat-groups", "/chats/groups"],
  ["chat-create-group", "/chats/create-group"],
  ["chat-invite", "/chats/invite/visualtest12"],
  ["playlists", "/playlists"],
  ["playlists-public-tab", "/playlists?tab=public"],
  ["playlists-favorites-tab", "/playlists?tab=favorites"],
  ["playlist-detail", "/playlist/12345678"],
  ["playlist-shared", "/playlist/shared/visualtoken"],
  ["playlist-create", "/playlists/create"],
  ["playlist-edit", "/playlists/12345678/edit"],
  ["my-playlists", "/my-playlists"],
  ["public-playlists", "/public-playlists"],
  ["library", "/library"],
  ["stats", "/stats"],
  ["history", "/history"],
  ["notifications", "/notifications"],
  ["notification-settings", "/notifications/settings"],
  ["settings", "/settings"],
  ["excerpts", "/excerpts"],
  ["excerpt", "/excerpts/1"],
  ["excerpt-shared", "/excerpts/s/visualtoken"],
  ["add-anime", "/add-anime"],
  ["announcement", "/announcements/novaya-istoriya"],
  ["donate", "/donate"],
  ["admin", "/admin"],
  ["admin-complaints", "/admin/complaints"],
  ["admin-franchises", "/admin/franchises"],
  ["admin-import", "/admin/kodik-import"],
  ["moderation", "/moderation"],
  ["not-found", "/visual-test-not-found"],
];

test.describe.configure({ mode: "parallel" });

for (const [name, path] of pages) {
  for (const theme of themes) {
    test(`page · ${name} · ${theme}`, async ({ page }) => {
      const runtimeErrors = [];
      const consoleErrors = [];
      page.on("pageerror", (error) => runtimeErrors.push(error.message));
      page.on("console", (message) => {
        if (message.type() === "error" && !message.text().includes("favicon")) consoleErrors.push(message.text());
      });
      await installVisualSession(page, theme);
      const response = await page.goto(path, { waitUntil: "domcontentloaded" });
      expect(response, `${name}: navigation did not produce a response`).not.toBeNull();
      await waitForVisualReady(page);
      await assertStableSurface(page, name);
      await captureSurface(page, `page--${name}--${theme}`);
      await page.setViewportSize({ width: 1440, height: 1000 });
      await capturePaletteAudit(page, `page--${name}--${theme}`, theme);
      expect(runtimeErrors, `${name}: uncaught page errors`).toEqual([]);
      expect(consoleErrors, `${name}: console errors`).toEqual([]);
    });
  }
}
