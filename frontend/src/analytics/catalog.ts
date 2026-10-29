export interface AnalyticsEventMap {
  filter_applied: { filter_group: "catalog" | "calendar" | "library"; active_filter_count: number };
  card_opened: { source: "catalog" | "home" | "recommendations" | "library" | "playlist" };
  playback_started: { source: "detail" | "watch" | "continue" | "floating" };
  episode_selected: { selection: "season" | "episode" };
  library_status_changed: { status: "planned" | "watching" | "completed" | "paused" | "dropped" | "removed" };
  playlist_created: { visibility: "public" | "private" | "unlisted" };
  post_published: { attachment_category: "none" | "image" | "video" | "mixed" };
  technical_error: { code: string; route: string };
  performance_metric: { metric: "navigation" | "lcp" | "cls" | "inp"; bucket: "fast" | "moderate" | "slow" };
}

export type AnalyticsEventName = keyof AnalyticsEventMap;

export type FieldRule =
  | { type: "enum"; values: readonly string[] }
  | { type: "integer"; min: number; max: number }
  | { type: "safe_code" }
  | { type: "safe_route" };

export const eventCatalog: { [K in AnalyticsEventName]: { [P in keyof AnalyticsEventMap[K]]: FieldRule } } = {
  filter_applied: {
    filter_group: { type: "enum", values: ["catalog", "calendar", "library"] },
    active_filter_count: { type: "integer", min: 0, max: 20 },
  },
  card_opened: {
    source: { type: "enum", values: ["catalog", "home", "recommendations", "library", "playlist"] },
  },
  playback_started: {
    source: { type: "enum", values: ["detail", "watch", "continue", "floating"] },
  },
  episode_selected: { selection: { type: "enum", values: ["season", "episode"] } },
  library_status_changed: {
    status: { type: "enum", values: ["planned", "watching", "completed", "paused", "dropped", "removed"] },
  },
  playlist_created: { visibility: { type: "enum", values: ["public", "private", "unlisted"] } },
  post_published: { attachment_category: { type: "enum", values: ["none", "image", "video", "mixed"] } },
  technical_error: { code: { type: "safe_code" }, route: { type: "safe_route" } },
  performance_metric: {
    metric: { type: "enum", values: ["navigation", "lcp", "cls", "inp"] },
    bucket: { type: "enum", values: ["fast", "moderate", "slow"] },
  },
};
