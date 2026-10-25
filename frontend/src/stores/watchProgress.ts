import { defineStore } from "pinia";
import { ref } from "vue";

export interface WatchProgressEntry {
  status: string | null;
  current_season: number;
  current_episode: number;
  episodes_watched: number;
  real_episodes_watched: number;
  progress_percentage: number;
  total_episodes: number;
  updatedAt?: number;
}

export interface AnimeProgressSummary {
  anime_id: number;
  total: number;
  watched_count: number;
  percent: number;
  episodes: EpisodeProgressItem[];
}

export interface EpisodeProgressItem {
  season_number?: number;
  episode_number: number;
  status: string;
  last_position: number;
  duration: number | null;
  progress_percent: number;
  is_manually_marked: boolean;
  watched_at: string | null;
}

export const useWatchProgressStore = defineStore("watchProgress", () => {
  const progressMap = ref<Map<number, WatchProgressEntry>>(new Map());

  function setProgress(animeId: number, data: Partial<WatchProgressEntry>) {
    const existing = progressMap.value.get(animeId);
    progressMap.value.set(animeId, {
      ...existing,
      ...data,
    } as WatchProgressEntry);
  }

  function getProgress(animeId: number): WatchProgressEntry | undefined {
    return progressMap.value.get(animeId);
  }

  function clearProgress(animeId: number) {
    progressMap.value.delete(animeId);
  }

  function hydrateFromEpisodeSummary(animeId: number, summary: AnimeProgressSummary) {
    const currentStatus = progressMap.value.get(animeId)?.status;
    const watchedCount = summary.episodes.filter(
      (ep) => ep.status === "watched" || ep.status === "skipped",
    ).length;

    let lastSeason = 0;
    let lastWatched = 0;
    for (const ep of summary.episodes) {
      if (ep.status !== "watched" && ep.status !== "skipped") continue;
      const season = ep.season_number ?? 1;
      if (
        season > lastSeason ||
        (season === lastSeason && ep.episode_number > lastWatched)
      ) {
        lastSeason = season;
        lastWatched = ep.episode_number;
      }
    }

    setProgress(animeId, {
      status: currentStatus ?? (
        watchedCount === 0
          ? "planned"
          : watchedCount >= summary.total
            ? "completed"
            : "started"
      ),
      current_season: lastSeason || 1,
      current_episode: lastWatched || 0,
      episodes_watched: watchedCount,
      real_episodes_watched: watchedCount,
      progress_percentage: summary.percent,
      total_episodes: summary.total,
    });
  }

  return {
    progressMap,
    setProgress,
    getProgress,
    clearProgress,
    hydrateFromEpisodeSummary,
  };
});
