import type { RouteLocationNormalizedLoaded, Router } from "vue-router";
import { pageView } from "./core";

const excluded = new Set([
  "oauth-callback", "confirm-email", "reset-password", "chat-invite",
  "playlist-shared", "excerpt-shared", "admin", "admin-complaints",
  "admin-franchises", "kodik-import", "moderation", "visual-modal-gallery",
]);

const normalizedNames: Record<string, string> = {
  "chat-by-code": "chats",
  "chat-by-id": "chats",
  "chat-topic": "chats",
  "chat-topic-int": "chats",
  "chats-detail": "chats",
  "user-profile": "user-profile",
  "user-profile-by-nickname": "user-profile",
  "user-short-nickname": "user-profile",
  "post-detail": "post-detail",
  "anime-detail": "anime-detail",
  "anime-canonical": "anime-detail",
  "anime-watch": "anime-watch",
};

export function safeRouteTemplate(route: Pick<RouteLocationNormalizedLoaded, "name" | "matched">): string | null {
  const name = typeof route.name === "string" ? route.name : "";
  if (!name || excluded.has(name) || name.startsWith("admin-")) return null;
  const safeName = normalizedNames[name] || name;
  if (!/^[a-z0-9][a-z0-9-]{0,63}$/.test(safeName)) return null;
  return `/route/${safeName}`;
}

export function installRouterTracking(router: Router): () => void {
  let previous: string | null = null;
  return router.afterEach((to, _from, failure) => {
    if (failure) return;
    const route = safeRouteTemplate(to);
    if (!route || route === previous) return;
    previous = route;
    pageView(route);
  });
}
