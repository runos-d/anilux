import { beforeEach, expect, it, vi } from 'vitest';
const api = vi.hoisted(() => ({ get: vi.fn(), patch: vi.fn().mockResolvedValue({}) }));
vi.mock('@/api/client', () => ({ default: api }));
beforeEach(() => { vi.resetModules(); localStorage.clear(); api.get.mockReset(); api.patch.mockClear(); });
it('keeps another account denial and syncs a banner decision exactly once', async () => {
  const consent = await import('./consent');
  consent.setConsent('granted', 'banner');
  const { syncConsent, saveConsentChoice } = await import('./consentSync');
  api.get.mockResolvedValue({ data: { analytics_consent_state: 'denied', analytics_consent_version: consent.ANALYTICS_CONSENT_POLICY_VERSION } });
  await syncConsent(42);
  expect(consent.getConsent().state).toBe('denied');
  expect(api.patch).not.toHaveBeenCalled();
  await saveConsentChoice('granted', 'banner');
  expect(api.patch).toHaveBeenCalledTimes(1);
  expect(api.patch.mock.calls[0]?.[1]).toMatchObject({ analytics_consent_state: 'granted' });
  await syncConsent(null);
  await syncConsent(84);
  expect(consent.getConsent().state).toBe('denied');
  expect(api.patch).toHaveBeenCalledTimes(1);
});
it('does not patch an unchanged account decision on startup', async () => {
  const consent = await import('./consent');
  consent.setConsentAccount(42);
  consent.setConsent('denied', 'settings');
  api.get.mockResolvedValue({ data: { analytics_consent_state: 'denied', analytics_consent_version: consent.ANALYTICS_CONSENT_POLICY_VERSION } });
  const { syncConsent } = await import('./consentSync');
  await syncConsent(42);
  expect(api.patch).not.toHaveBeenCalled();
});
