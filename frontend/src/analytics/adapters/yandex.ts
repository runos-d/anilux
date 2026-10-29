import type { AnalyticsAdapter, PageView } from "../types";

declare global {
  interface Window {
    ym?: (...args: unknown[]) => void;
  }
}

const SCRIPT_ID = "anilux-yandex-metrika";

function removeCookie(name: string) {
  document.cookie = `${name}=; Max-Age=0; path=/; SameSite=Lax`;
  document.cookie = `${name}=; Max-Age=0; path=/; domain=.${location.hostname}; SameSite=Lax`;
}

export function createYandexAdapter(counterId: string): AnalyticsAdapter {
  let initialized = false;
  return {
    name: "yandex",
    async initialize() {
      if (initialized) return;
      initialized = true;
      window.ym = window.ym || function (...args: unknown[]) {
        const queue = (window.ym as unknown as { a?: unknown[][] }).a ||= [];
        queue.push(args);
      };
      const script = document.createElement("script");
      script.id = SCRIPT_ID;
      script.async = true;
      script.src = "https://mc.yandex.ru/metrika/tag.js";
      document.head.appendChild(script);
      try {
        window.ym(counterId, "init", {
          clickmap: false,
          trackLinks: false,
          accurateTrackBounce: false,
          webvisor: false,
          defer: true,
        });
      } catch {
        // Provider failures never affect the application.
      }
    },
    pageView(view: PageView) {
      try { window.ym?.(counterId, "hit", view.route, { title: view.route }); } catch { /* isolated */ }
    },
    event(name, payload) {
      try { window.ym?.(counterId, "reachGoal", name, payload); } catch { /* isolated */ }
    },
    reset() {
      if (initialized) {
        try { window.ym?.(counterId, "destruct"); } catch { /* isolated */ }
      }
      initialized = false;
      document.getElementById(SCRIPT_ID)?.remove();
      delete window.ym;
      document.cookie.split(";").map((part) => part.trim().split("=")[0] || "").filter((name) => name.startsWith("_ym_") || name === "_ym_uid" || name === "_ym_d").forEach(removeCookie);
      Object.keys(localStorage).filter((key) => key.startsWith("_ym")).forEach((key) => localStorage.removeItem(key));
    },
  };
}
