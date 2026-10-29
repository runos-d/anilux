import { type AnalyticsEventMap, type AnalyticsEventName } from "./catalog";
import { getConsent, onConsentChange } from "./consent";
import { sanitizeEvent } from "./sanitizer";
import type { AnalyticsAdapter } from "./types";
import { noopAdapter } from "./adapters/noop";
import { createYandexAdapter } from "./adapters/yandex";
import { createGoogleAdapter } from "./adapters/google";

let adapters: AnalyticsAdapter[] = [noopAdapter];
let initialized = false;
let initializing: Promise<void> | null = null;
let unsubscribe: (() => void) | null = null;

function configuredAdapters(): AnalyticsAdapter[] {
  const result: AnalyticsAdapter[] = [];
  const yandexId = import.meta.env.VITE_YANDEX_METRIKA_ID?.trim();
  const googleId = import.meta.env.VITE_GOOGLE_ANALYTICS_ID?.trim();
  if (import.meta.env.VITE_YANDEX_METRIKA_ENABLED === "true" && yandexId && /^\d{4,12}$/.test(yandexId)) {
    result.push(createYandexAdapter(yandexId));
  }
  if (import.meta.env.VITE_GOOGLE_ANALYTICS_ENABLED === "true" && googleId && /^G-[A-Z0-9]{6,16}$/.test(googleId)) {
    result.push(createGoogleAdapter(googleId));
  }
  return result.length ? result : [noopAdapter];
}

export async function initialize(): Promise<void> {
  if (initialized || initializing) return initializing || Promise.resolve();
  if (!unsubscribe) unsubscribe = onConsentChange((record) => { void consentChanged(record.state); });
  if (getConsent().state !== "granted") {
    adapters = [noopAdapter];
    initialized = true;
    return;
  }
  initializing = (async () => {
    adapters = configuredAdapters();
    await Promise.all(adapters.map(async (adapter) => {
      try { await adapter.initialize(); } catch { /* isolated */ }
    }));
    initialized = true;
    initializing = null;
  })();
  return initializing;
}

export function pageView(route: string): void {
  if (!initialized || getConsent().state !== "granted" || !/^\/[a-z0-9/_-]{1,96}$/.test(route)) return;
  adapters.forEach((adapter) => { try { adapter.pageView({ route }); } catch { /* isolated */ } });
}

export function event<K extends AnalyticsEventName>(name: K, payload: AnalyticsEventMap[K]): void {
  if (!initialized || getConsent().state !== "granted") return;
  const clean = sanitizeEvent(name, payload);
  if (!clean) return;
  adapters.forEach((adapter) => { try { adapter.event(name, clean); } catch { /* isolated */ } });
}

export async function consentChanged(state = getConsent().state): Promise<void> {
  if (state !== "granted") {
    reset();
    initialized = true;
    return;
  }
  reset();
  await initialize();
}

export function reset(): void {
  adapters.forEach((adapter) => { try { adapter.reset(); } catch { /* isolated */ } });
  adapters = [noopAdapter];
  initialized = false;
  initializing = null;
}

export function analyticsStateForTests() {
  return { initialized, adapters: adapters.map((adapter) => adapter.name) };
}
