import type { AnalyticsAdapter } from "../types";

export const noopAdapter: AnalyticsAdapter = {
  name: "noop",
  async initialize() {},
  pageView() {},
  event() {},
  reset() {},
};
