import apiClient from '@/api/client';
import { ANALYTICS_CONSENT_POLICY_VERSION, getConsent, onConsentChange, setConsent, setConsentAccount } from './consent';
import type { ConsentSource, ConsentState } from './types';

let owner: number | null = null;
let generation = 0;
let controller: AbortController | undefined;
let pending: Promise<void> = Promise.resolve();
let applying = false;
let listening = false;

function queueChoice(): void {
  const id = owner;
  const epoch = generation;
  const record = getConsent();
  if (!id || record.state === 'unknown' || applying) return;
  pending = pending.catch(() => undefined).then(async () => {
    if (epoch !== generation || owner !== id) return;
    await apiClient.patch('/users/privacy-settings/me/', {
      analytics_consent_state: record.state,
      analytics_consent_version: ANALYTICS_CONSENT_POLICY_VERSION,
      analytics_consent_source: record.source,
    }, { _accountId: String(id), signal: controller?.signal });
  });
  void pending.catch(() => undefined);
}

export async function syncConsent(accountId: number | null): Promise<void> {
  const epoch = ++generation;
  controller?.abort();
  controller = new AbortController();
  owner = accountId;
  applying = true;
  setConsentAccount(accountId);
  applying = false;
  if (!listening) {
    listening = true;
    onConsentChange(record => { if (record.source !== 'server') queueChoice(); });
  }
  if (!accountId) return;
  const before = JSON.stringify(getConsent());
  try {
    const { data } = await apiClient.get('/users/privacy-settings/me/', {
      _accountId: String(accountId), signal: controller.signal,
    });
    if (epoch !== generation || JSON.stringify(getConsent()) !== before) return;
    const local = getConsent();
    const serverKnown = data.analytics_consent_version === ANALYTICS_CONSENT_POLICY_VERSION &&
      (data.analytics_consent_state === 'granted' || data.analytics_consent_state === 'denied');
    if (serverKnown && (local.state === 'unknown' || !local.decidedAt ||
        Date.parse(data.analytics_consent_updated_at || '') > Date.parse(local.decidedAt || ''))) {
      applying = true;
      setConsent(data.analytics_consent_state, 'server');
      applying = false;
    } else if (local.state !== 'unknown' && (!serverKnown || local.state !== data.analytics_consent_state)) {
      queueChoice();
      await pending;
    }
  } catch { /* Local consent still applies during an outage. */ }
}

export async function saveConsentChoice(state: ConsentState, source: ConsentSource): Promise<void> {
  setConsent(state, source);
  await pending;
}
