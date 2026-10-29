import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

const { pageView } = vi.hoisted(() => ({ pageView: vi.fn() }));
vi.mock("./core", () => ({ pageView }));

import { installRouterTracking, safeRouteTemplate } from "./router";

describe("safe router analytics", () => {
  beforeEach(() => pageView.mockClear());

  it("never includes params, query or fragment", () => {
    expect(safeRouteTemplate({ name: "anime-detail", matched: [] } as never)).toBe("/route/anime-detail");
    expect(safeRouteTemplate({ name: "oauth-callback", matched: [] } as never)).toBeNull();
    expect(safeRouteTemplate({ name: "chat-invite", matched: [] } as never)).toBeNull();
    expect(safeRouteTemplate({ name: "admin-users", matched: [] } as never)).toBeNull();
  });

  it("tracks one final page view for redirects and none for failed duplicates", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: { template: "<div />" } },
        { path: "/old", redirect: "/anime" },
        { path: "/anime", name: "anime-catalog", component: { template: "<div />" } },
      ],
    });
    installRouterTracking(router);
    await router.push("/old?search=private#fragment");
    await router.isReady();
    expect(pageView).toHaveBeenLastCalledWith("/route/anime-catalog");
    expect(pageView).toHaveBeenCalledTimes(1);
    await router.push("/anime");
    expect(pageView).toHaveBeenCalledTimes(1);
  });
});
