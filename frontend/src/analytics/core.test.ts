import { beforeEach, describe, expect, it, vi } from "vitest";

describe("analytics core", () => {
  beforeEach(() => {
    document.head.querySelectorAll("#anilux-yandex-metrika, #anilux-google-analytics").forEach((node) => node.remove());
    localStorage.clear();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it.each(["unknown", "denied"] as const)("does not load providers for %s", async (state) => {
    const consent = await import("./consent");
    if (state === "denied") consent.setConsent("denied", "banner");
    const core = await import("./core");
    await core.initialize();
    expect(document.querySelector("#anilux-yandex-metrika, #anilux-google-analytics")).toBeNull();
  });

  it("initializes once after consent and clears provider state on revocation", async () => {
    vi.stubEnv("VITE_YANDEX_METRIKA_ENABLED", "true");
    vi.stubEnv("VITE_YANDEX_METRIKA_ID", String(12_000_000 + 345_678));
    const consent = await import("./consent");
    consent.setConsent("granted", "banner");
    const core = await import("./core");
    await Promise.all([core.initialize(), core.initialize()]);
    expect(document.querySelectorAll("#anilux-yandex-metrika")).toHaveLength(1);
    consent.setConsent("denied", "settings");
    await Promise.resolve();
    expect(document.querySelector("#anilux-yandex-metrika")).toBeNull();
    expect(document.cookie).not.toContain("_ym_");
  });

  it("drops pre-consent events instead of replaying them", async () => {
    vi.stubEnv("VITE_GOOGLE_ANALYTICS_ENABLED", "true");
    vi.stubEnv("VITE_GOOGLE_ANALYTICS_ID", "G-" + "ABCDEF12");
    const core = await import("./core");
    await core.initialize();
    core.event("card_opened", { source: "home" });
    const consent = await import("./consent");
    consent.setConsent("granted", "banner");
    await core.consentChanged("granted");
    expect(window.dataLayer?.filter((entry) => Array.isArray(entry) && entry[0] === "event")).toHaveLength(0);
  });
});
