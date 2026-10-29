import type { ConsentRecord, ConsentSource, ConsentState } from "./types";

export const ANALYTICS_CONSENT_POLICY_VERSION = "2026-10-27.1";
const STORAGE_KEY = "anilux.analytics.consent";
const listeners = new Set<(record: ConsentRecord) => void>();

const unknownRecord = (source: ConsentSource = "policy_upgrade"): ConsentRecord => ({
  state: "unknown",
  policyVersion: ANALYTICS_CONSENT_POLICY_VERSION,
  decidedAt: null,
  source,
});

let account: number | null = null;
const storageKey = () => account === null ? STORAGE_KEY : `${STORAGE_KEY}.account.${account}`;

function parseStored(): ConsentRecord {
  if (typeof localStorage === "undefined") return unknownRecord();
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey()) || "null") as Partial<ConsentRecord> | null;
    if (!parsed || parsed.policyVersion !== ANALYTICS_CONSENT_POLICY_VERSION) return unknownRecord();
    if (!(["unknown", "granted", "denied"] as const).includes(parsed.state as ConsentState)) return unknownRecord();
    return {
      state: parsed.state as ConsentState,
      policyVersion: ANALYTICS_CONSENT_POLICY_VERSION,
      decidedAt: typeof parsed.decidedAt === "string" ? parsed.decidedAt : null,
      source: parsed.source || "policy_upgrade",
    };
  } catch {
    return unknownRecord();
  }
}

let current = parseStored();

export function getConsent(): ConsentRecord {
  return { ...current };
}

export function setConsent(state: ConsentState, source: ConsentSource): ConsentRecord {
  current = {
    state,
    policyVersion: ANALYTICS_CONSENT_POLICY_VERSION,
    decidedAt: state === "unknown" ? null : new Date().toISOString(),
    source,
  };
  try {
    if (typeof localStorage !== "undefined") localStorage.setItem(storageKey(), JSON.stringify(current));
  } catch {
    // The in-memory decision still applies when browser storage is unavailable.
  }
  listeners.forEach((listener) => listener(getConsent()));
  return getConsent();
}

export function clearConsent(): ConsentRecord {
  current = unknownRecord("policy_upgrade");
  try {
    if (typeof localStorage !== "undefined") localStorage.removeItem(storageKey());
  } catch {
    // In-memory reset is sufficient for the current page lifecycle.
  }
  listeners.forEach((listener) => listener(getConsent()));
  return getConsent();
}

export function onConsentChange(listener: (record: ConsentRecord) => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export const consentStorageKeyForTests = STORAGE_KEY;

export function setConsentAccount(id: number | null): void {
  if (account === id) return;
  account = id;
  current = parseStored();
  listeners.forEach(listener => listener(getConsent()));
}

if (typeof window !== 'undefined') window.addEventListener('storage', event => {
  if (event.key !== null && event.key !== storageKey()) return;
  current = { ...parseStored(), source: 'server' };
  listeners.forEach(listener => listener(getConsent()));
});
