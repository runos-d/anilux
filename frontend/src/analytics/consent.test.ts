import { beforeEach, describe, expect, it, vi } from "vitest";

describe("analytics consent", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetModules();
  });

  it("starts unknown and persists explicit choices", async () => {
    const consent = await import("./consent");
    expect(consent.getConsent().state).toBe("unknown");
    consent.setConsent("denied", "banner");
    expect(consent.getConsent()).toMatchObject({ state: "denied", source: "banner" });
    expect(JSON.parse(localStorage.getItem(consent.consentStorageKeyForTests) || "{}").decidedAt).toBeTruthy();
  });

  it("returns to unknown when the policy version changes", async () => {
    localStorage.setItem("anilux.analytics.consent", JSON.stringify({
      state: "granted", policyVersion: "old", decidedAt: "2025-01-01T00:00:00Z", source: "banner",
    }));
    const consent = await import("./consent");
    expect(consent.getConsent().state).toBe("unknown");
    expect(consent.getConsent().policyVersion).toBe(consent.ANALYTICS_CONSENT_POLICY_VERSION);
  });

  it("clears the local decision for account deletion", async () => {
    const consent = await import("./consent");
    consent.setConsent("granted", "settings");
    consent.clearConsent();
    expect(consent.getConsent()).toMatchObject({ state: "unknown", decidedAt: null });
    expect(localStorage.getItem(consent.consentStorageKeyForTests)).toBeNull();
  });
  it('isolates account choices and applies consent changes from another tab', async () => {
    const consent = await import('./consent');
    consent.setConsentAccount(10);
    consent.setConsent('granted', 'settings');
    consent.setConsentAccount(20);
    expect(consent.getConsent().state).toBe('unknown');
    consent.setConsent('denied', 'settings');
    consent.setConsentAccount(10);
    expect(consent.getConsent().state).toBe('granted');
    const key = 'anilux.analytics.consent.account.10';
    localStorage.setItem(key, JSON.stringify({ ...consent.getConsent(), state: 'denied' }));
    window.dispatchEvent(new StorageEvent('storage', { key }));
    expect(consent.getConsent().state).toBe('denied');
  });

});
