export { initialize, pageView, event, consentChanged, reset } from "./core";
export { clearConsent, getConsent, setConsent, ANALYTICS_CONSENT_POLICY_VERSION } from "./consent";
export { syncConsent, saveConsentChoice } from "./consentSync";
export { installRouterTracking, safeRouteTemplate } from "./router";
export { reportTechnicalError, reportPerformance, initializeErrorTelemetry, initializePerformanceTelemetry } from "./telemetry";
export type { AnalyticsEventMap, AnalyticsEventName } from "./catalog";
