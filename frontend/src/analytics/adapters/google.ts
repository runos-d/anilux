import type { AnalyticsAdapter, PageView } from "../types";

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}

const SCRIPT_ID = "anilux-google-analytics";

function expireCookie(name: string) {
  document.cookie = `${name}=; Max-Age=0; path=/; SameSite=Lax`;
  document.cookie = `${name}=; Max-Age=0; path=/; domain=.${location.hostname}; SameSite=Lax`;
}

export function createGoogleAdapter(measurementId: string): AnalyticsAdapter {
  let initialized = false;
  return {
    name: "google",
    async initialize() {
      if (initialized) return;
      initialized = true;
      window.dataLayer = window.dataLayer || [];
      window.gtag = window.gtag || function (...args: unknown[]) { window.dataLayer?.push(args); };
      window.gtag("consent", "default", { analytics_storage: "denied", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
      const script = document.createElement("script");
      script.id = SCRIPT_ID;
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
      document.head.appendChild(script);
      window.gtag("js", new Date());
      window.gtag("consent", "update", { analytics_storage: "granted" });
      window.gtag("config", measurementId, {
        send_page_view: false,
        anonymize_ip: true,
        allow_google_signals: false,
        allow_ad_personalization_signals: false,
      });
    },
    pageView(view: PageView) {
      try { window.gtag?.("event", "page_view", { page_location: view.route, page_title: view.route }); } catch { /* isolated */ }
    },
    event(name, payload) {
      try { window.gtag?.("event", name, payload); } catch { /* isolated */ }
    },
    reset() {
      try { window.gtag?.("consent", "update", { analytics_storage: "denied", ad_storage: "denied" }); } catch { /* isolated */ }
      initialized = false;
      document.getElementById(SCRIPT_ID)?.remove();
      delete window.gtag;
      delete window.dataLayer;
      document.cookie.split(";").map((part) => part.trim().split("=")[0] || "").filter((name) => name === "_ga" || name.startsWith("_ga_")).forEach(expireCookie);
    },
  };
}
