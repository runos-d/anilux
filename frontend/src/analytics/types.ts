export type ConsentState = "unknown" | "granted" | "denied";

export type ConsentSource = "banner" | "settings" | "server" | "policy_upgrade";

export interface ConsentRecord {
  state: ConsentState;
  policyVersion: string;
  decidedAt: string | null;
  source: ConsentSource;
}

export interface PageView {
  route: string;
}

export interface AnalyticsAdapter {
  readonly name: string;
  initialize(): Promise<void>;
  pageView(view: PageView): void;
  event(name: string, payload: Readonly<Record<string, string | number | boolean>>): void;
  reset(): void;
}
