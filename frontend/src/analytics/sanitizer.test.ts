import { describe, expect, it } from "vitest";
import { AnalyticsPayloadError, sanitizeEvent } from "./sanitizer";

describe("analytics sanitizer", () => {
  it("accepts only catalog fields", () => {
    expect(sanitizeEvent("card_opened", { source: "catalog" })).toEqual({ source: "catalog" });
    expect(() => sanitizeEvent("card_opened", { source: "catalog", email: "person@example.test" } as never)).toThrow(AnalyticsPayloadError);
  });

  it("rejects nested forbidden keys and values before serialization", () => {
    expect(() => sanitizeEvent("technical_error", {
      code: "api.failed",
      route: "/route/home",
      nested: { authorization: "Bearer secret" },
    } as never)).toThrow(AnalyticsPayloadError);
    expect(() => sanitizeEvent("technical_error", {
      code: "api.failed",
      route: "/route/home?token=secret",
    })).toThrow(AnalyticsPayloadError);
  });

  it("rejects unknown events and arbitrary values", () => {
    expect(() => sanitizeEvent("unknown" as never, {} as never)).toThrow(AnalyticsPayloadError);
    expect(() => sanitizeEvent("filter_applied", { filter_group: "catalog", active_filter_count: 999 })).toThrow(AnalyticsPayloadError);
  });
});
