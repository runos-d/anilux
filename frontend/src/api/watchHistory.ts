import apiClient from "./client";

export type WatchHistoryState = "all" | "in_progress" | "watched";

export interface WatchHistoryItem {
  anime_id: number;
  slug?: string | null;
  title: string;
  title_en: string;
  poster: string;
  year?: number | null;
  kind: string;
  kind_label: string;
  score?: number | null;
  genres: string[];
  season_number: number;
  episode: number;
  continue_season: number;
  continue_episode: number;
  total_episodes: number;
  watched_episodes: number;
  episode_status: "not_started" | "in_progress" | "watched" | "skipped";
  position: number;
  duration: number | null;
  episode_percent: number;
  series_percent: number;
  last_watched: string;
  is_series_completed: boolean;
}

export interface WatchHistorySummary {
  total: number;
  in_progress: number;
  watched: number;
}

export interface WatchHistoryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: WatchHistoryItem[];
  summary: WatchHistorySummary;
}

export const watchHistoryApi = {
  async list(params: {
    page?: number;
    page_size?: number;
    search?: string;
    state?: WatchHistoryState;
  } = {}) {
    const response = await apiClient.get<WatchHistoryResponse>("/anime/watch-history/", { params });
    return response.data;
  },

  async hide(animeId: number) {
    await apiClient.delete(`/anime/watch-history/${animeId}/`);
  },

  async restore(animeId: number) {
    await apiClient.post(`/anime/watch-history/${animeId}/`);
  },

  async clear() {
    await apiClient.delete("/anime/watch-history/");
  },

  async restoreAll() {
    await apiClient.post("/anime/watch-history/", { action: "restore" });
  },
};
