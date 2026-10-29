import { event } from "./core";

export function reportTechnicalError(code: string, route: string): void {
  event("technical_error", { code, route });
}

function bucket(metric: "navigation" | "lcp" | "cls" | "inp", value: number): "fast" | "moderate" | "slow" {
  const limits: [number, number] = metric === "cls" ? [0.1, 0.25] : metric === "inp" ? [200, 500] : [2500, 4000];
  return value <= limits[0] ? "fast" : value <= limits[1] ? "moderate" : "slow";
}

export function reportPerformance(metric: "navigation" | "lcp" | "cls" | "inp", value: number): void {
  if (!Number.isFinite(value) || value < 0) return;
  event("performance_metric", { metric, bucket: bucket(metric, value) });
}

export function initializeErrorTelemetry(route: () => string | null): () => void {
  const report = (code: string) => {
    const template = route();
    if (template) reportTechnicalError(code, template);
  };
  const onError = () => report("runtime.window_error");
  const onRejection = () => report("runtime.unhandled_rejection");
  window.addEventListener("error", onError);
  window.addEventListener("unhandledrejection", onRejection);
  return () => {
    window.removeEventListener("error", onError);
    window.removeEventListener("unhandledrejection", onRejection);
  };
}

export function initializePerformanceTelemetry(): void {
  if (typeof PerformanceObserver === "undefined") return;
  try {
    const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    if (navigation) reportPerformance("navigation", navigation.duration);
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const last = entries.at(-1);
      if (last) reportPerformance("lcp", last.startTime);
    });
    observer.observe({ type: "largest-contentful-paint", buffered: true });
    const layoutObserver = new PerformanceObserver((list) => {
      const total = list.getEntries().reduce((sum, entry) => {
        const shift = entry as PerformanceEntry & { value?: number; hadRecentInput?: boolean };
        return shift.hadRecentInput ? sum : sum + (shift.value || 0);
      }, 0);
      if (total > 0) reportPerformance("cls", total);
    });
    layoutObserver.observe({ type: "layout-shift", buffered: true });
    const interactionObserver = new PerformanceObserver((list) => {
      const longest = Math.max(0, ...list.getEntries().map((entry) => entry.duration));
      if (longest > 0) reportPerformance("inp", longest);
    });
    interactionObserver.observe({ type: "event", buffered: true, durationThreshold: 40 } as PerformanceObserverInit);
  } catch {
    // Unsupported metrics are simply unavailable.
  }
}
