import { ref, computed, readonly } from "vue";
import apiClient, { isRequestCancelled } from "@/api/client";
import { useToast } from "@/composables/useToast";
import { useAuthStore } from "@/stores/auth";
import { useWatchProgressStore } from "@/stores/watchProgress";
import type { PlayerEpisodeGroup } from "@/lib/playerSeasons";

export type EpisodeStatus =
  "not_started" | "in_progress" | "watched" | "skipped";

export interface EpisodeProgressItem {
  season_number: number;
  episode_number: number;
  status: EpisodeStatus;
  last_position: number;
  duration: number | null;
  progress_percent: number;
  is_manually_marked: boolean;
  watched_at: string | null;
}

export interface AnimeProgressSummary {
  anime_id: number;
  total: number;
  watched_count: number;
  percent: number;
  episodes: EpisodeProgressItem[];
}

export interface EpisodeTarget {
  season: number;
  episode: number;
}

const episodeKey = (season: number, episode: number) => `${season}:${episode}`;

const defaultItem = (
  season: number,
  episode: number,
): EpisodeProgressItem => ({
  season_number: season,
  episode_number: episode,
  status: "not_started",
  last_position: 0,
  duration: null,
  progress_percent: 0,
  is_manually_marked: false,
  watched_at: null,
});

export function useEpisodeProgress(animeId: number) {
  const toast = useToast();
  const auth = useAuthStore();
  const progressStore = useWatchProgressStore();

  const episodes = ref<Map<string, EpisodeProgressItem>>(new Map());
  const groups = ref<PlayerEpisodeGroup[]>([]);
  const totalEpisodes = ref(0);
  const loading = ref(false);
  const loaded = ref(false);

  const updateEpisodes = (
    updater: (map: Map<string, EpisodeProgressItem>) => void,
  ) => {
    const newMap = new Map(episodes.value);
    updater(newMap);
    episodes.value = newMap;
  };

  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let lastSavedTime = 0;
  const SAVE_DEBOUNCE = 30_000;
  const POSITION_CHANGE_THRESHOLD = 5;

  const orderedGroups = computed<PlayerEpisodeGroup[]>(() => {
    if (groups.value.length) {
      return [...groups.value].sort((a, b) => {
        const specialA = a.season === 0 ? 1 : 0;
        const specialB = b.season === 0 ? 1 : 0;
        return specialA - specialB || a.season - b.season;
      });
    }
    const total = Math.max(1, totalEpisodes.value);
    return [
      {
        season: 1,
        label: "Сезон 1",
        episodes: Array.from({ length: total }, (_, index) => index + 1),
      },
    ];
  });

  const watchedCount = computed(
    () =>
      [...episodes.value.values()].filter(
        (e) => e.status === "watched" || e.status === "skipped",
      ).length,
  );

  const progressPercent = computed(() => {
    if (!totalEpisodes.value) return 0;
    return Math.min(
      100,
      Math.round((watchedCount.value / totalEpisodes.value) * 100),
    );
  });

  const statusFor = (season: number, episode: number) =>
    episodes.value.get(episodeKey(season, episode))?.status;

  const nextEpisodeToWatch = computed<EpisodeTarget | null>(() => {
    for (const group of orderedGroups.value) {
      for (const episode of group.episodes) {
        const status = statusFor(group.season, episode);
        if (!status || status === "not_started" || status === "in_progress") {
          return { season: group.season, episode };
        }
      }
    }
    return null;
  });

  const lastWatchedEpisode = computed<EpisodeTarget | null>(() => {
    let last: EpisodeTarget | null = null;
    for (const item of episodes.value.values()) {
      if (item.status !== "watched" && item.status !== "skipped") continue;
      if (
        !last ||
        item.season_number > last.season ||
        (item.season_number === last.season &&
          item.episode_number > last.episode)
      ) {
        last = {
          season: item.season_number,
          episode: item.episode_number,
        };
      }
    }
    return last;
  });

  const syncStoreFromCurrentState = () => {
    const watched = watchedCount.value;
    const total = totalEpisodes.value;
    const lastWatched = lastWatchedEpisode.value;
    const currentEp = lastWatched?.episode ?? 0;
    const pct = total
      ? Math.min(100, Math.round((watched / total) * 100))
      : 0;

    let status: string | null = null;
    if (watched === 0) status = "planned";
    else if (total && watched >= total) status = "completed";
    else status = "started";

    progressStore.setProgress(animeId, {
      status,
      current_season: lastWatched?.season ?? 1,
      current_episode: currentEp,
      episodes_watched: watched,
      real_episodes_watched: watched,
      progress_percentage: pct,
      total_episodes: total,
    });
  };

  const getEpisode = (season: number, episode: number): EpisodeProgressItem =>
    episodes.value.get(episodeKey(season, episode)) ??
    defaultItem(season, episode);

  const isWatched = (season: number, episode: number) => {
    const status = statusFor(season, episode);
    return status === "watched" || status === "skipped";
  };

  const isInProgress = (season: number, episode: number) =>
    statusFor(season, episode) === "in_progress";

  const setEpisodeGroups = (nextGroups: PlayerEpisodeGroup[]) => {
    groups.value = nextGroups;
  };

  const loadProgress = async () => {
    if (!auth.isAuthenticated) return;
    try {
      loading.value = true;
      const res = await apiClient.get<AnimeProgressSummary>(
        `/anime/${animeId}/episode-progress/`,
      );
      totalEpisodes.value = res.data.total;

      const map = new Map<string, EpisodeProgressItem>();
      for (const ep of res.data.episodes) {
        const season = ep.season_number ?? 1;
        map.set(episodeKey(season, ep.episode_number), {
          ...ep,
          season_number: season,
        });
      }
      episodes.value = map;
      loaded.value = true;
      progressStore.hydrateFromEpisodeSummary(animeId, res.data);
    } catch (e) {
      if (isRequestCancelled(e)) return;
      console.warn("[EpisodeProgress] Ошибка загрузки:", e);
    } finally {
      loading.value = false;
    }
  };

  const updatePosition = (
    season: number,
    episodeNum: number,
    position: number,
    duration?: number,
  ) => {
    if (!auth.isAuthenticated) return;
    if (isWatched(season, episodeNum)) return;

    const existing = getEpisode(season, episodeNum);
    const prevPosition = existing.last_position || 0;
    if (Math.abs(position - prevPosition) < POSITION_CHANGE_THRESHOLD) return;

    const updated: EpisodeProgressItem = {
      ...existing,
      season_number: season,
      episode_number: episodeNum,
      last_position: position,
      duration: duration ?? existing.duration,
      status:
        existing.status === "not_started" ? "in_progress" : existing.status,
      progress_percent: duration
        ? Math.round((position / duration) * 100)
        : existing.progress_percent,
    };
    if (updated.status !== "watched" && updated.status !== "skipped") {
      updateEpisodes((map) =>
        map.set(episodeKey(season, episodeNum), updated),
      );
    }

    const now = Date.now();
    if (now - lastSavedTime < SAVE_DEBOUNCE) return;
    lastSavedTime = now;

    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      if (isWatched(season, episodeNum)) return;
      try {
        await apiClient.post(`/anime/${animeId}/episode-progress/`, {
          season_number: season,
          episode_number: episodeNum,
          last_position: Math.floor(position),
          duration: duration ? Math.floor(duration) : undefined,
          action: "progress",
        });
      } catch (e) {
        console.warn("[EpisodeProgress] Ошибка сохранения позиции:", e);
      }
    }, 500);
  };

  const autoMarkWatched = async (season: number, episodeNum: number) => {
    if (!auth.isAuthenticated) return;
    if (isWatched(season, episodeNum)) return;

    const existing = getEpisode(season, episodeNum);
    updateEpisodes((map) =>
      map.set(episodeKey(season, episodeNum), {
        ...existing,
        status: "watched",
        progress_percent: 100,
        watched_at: new Date().toISOString(),
        is_manually_marked: false,
      }),
    );

    toast.success(`Серия ${episodeNum} просмотрена`, {
      duration: 5000,
      action: {
        label: "Отменить",
        handler: () => undoMark(season, episodeNum),
      },
    });

    try {
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        season_number: season,
        episode_number: episodeNum,
        action: "mark",
      });
      syncStoreFromCurrentState();
    } catch (e) {
      console.warn("[EpisodeProgress] Ошибка авто-отметки:", e);
      updateEpisodes((map) =>
        map.set(episodeKey(season, episodeNum), existing),
      );
    }
  };

  const markWatched = async (season: number, episodeNum: number) => {
    if (!auth.isAuthenticated) return;
    if (isWatched(season, episodeNum)) return;

    const existing = getEpisode(season, episodeNum);
    updateEpisodes((map) =>
      map.set(episodeKey(season, episodeNum), {
        ...existing,
        status: "watched",
        progress_percent: 100,
        watched_at: new Date().toISOString(),
        is_manually_marked: true,
      }),
    );

    toast.success(`Серия ${episodeNum} отмечена`, {
      duration: 4000,
      action: {
        label: "Отменить",
        handler: () => undoMark(season, episodeNum),
      },
    });

    try {
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        season_number: season,
        episode_number: episodeNum,
        action: "mark",
      });
      syncStoreFromCurrentState();
    } catch (e) {
      console.warn("[EpisodeProgress] Ошибка ручной отметки:", e);
      updateEpisodes((map) =>
        map.set(episodeKey(season, episodeNum), existing),
      );
      toast.error("Не удалось сохранить отметку");
    }
  };

  const skipEpisode = async (season: number, episodeNum: number) => {
    if (!auth.isAuthenticated) return;

    const existing = getEpisode(season, episodeNum);
    updateEpisodes((map) =>
      map.set(episodeKey(season, episodeNum), {
        ...existing,
        status: "skipped",
        is_manually_marked: true,
      }),
    );

    toast.info(`Серия ${episodeNum} пропущена`, {
      duration: 2000,
      action: {
        label: "Отменить",
        handler: () => undoMark(season, episodeNum),
      },
    });

    try {
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        season_number: season,
        episode_number: episodeNum,
        action: "skip",
      });
      syncStoreFromCurrentState();
    } catch (e) {
      console.warn("[EpisodeProgress] Ошибка пропуска:", e);
      updateEpisodes((map) =>
        map.set(episodeKey(season, episodeNum), existing),
      );
      toast.error("Не удалось пропустить серию");
    }
  };

  const undoMark = async (season: number, episodeNum: number) => {
    if (!auth.isAuthenticated) return;

    const existing = getEpisode(season, episodeNum);
    updateEpisodes((map) =>
      map.set(episodeKey(season, episodeNum), {
        ...existing,
        status: "in_progress",
        is_manually_marked: false,
        watched_at: null,
      }),
    );

    try {
      await apiClient.post(
        `/anime/${animeId}/episode-progress/${episodeNum}/undo/`,
        { season_number: season },
      );
      toast.info(`Отметка снята с серии ${episodeNum}`);
      syncStoreFromCurrentState();
    } catch (e) {
      console.warn("[EpisodeProgress] Ошибка отмены:", e);
      updateEpisodes((map) =>
        map.set(episodeKey(season, episodeNum), existing),
      );
    }
  };

  const applyBulkResult = (
    season: number,
    watchedUpTo: number,
    now: string,
  ) => {
    const group = groups.value.find((item) => item.season === season);
    const knownEpisodes = group?.episodes ?? [];
    updateEpisodes((map) => {
      const numbers = new Set(knownEpisodes);
      for (let i = 1; i <= watchedUpTo; i++) numbers.add(i);
      for (const number of numbers) {
        const existing = map.get(episodeKey(season, number));
        if (number <= watchedUpTo) {
          map.set(episodeKey(season, number), {
            ...(existing ?? defaultItem(season, number)),
            status: "watched",
            last_position: 0,
            progress_percent: 100,
            is_manually_marked: true,
            watched_at: now,
          });
        } else if (existing) {
          map.set(episodeKey(season, number), {
            ...existing,
            status: "not_started",
            last_position: 0,
            progress_percent: 0,
            is_manually_marked: false,
            watched_at: null,
          });
        }
      }
    });
  };

  const bulkSyncSeasons = async (
    seasons: { season: number; watchedUpTo: number }[],
    silent = false,
  ) => {
    if (!auth.isAuthenticated) return;
    try {
      loading.value = true;
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        action: "bulk",
        seasons: seasons.map((item) => ({
          season_number: item.season,
          watched_up_to: item.watchedUpTo,
        })),
      });

      const now = new Date().toISOString();
      for (const item of seasons) {
        applyBulkResult(item.season, item.watchedUpTo, now);
      }

      if (!silent) {
        const total = seasons.reduce(
          (sum, item) => sum + item.watchedUpTo,
          0,
        );
        toast.success(`${total} серий отмечено как просмотренных`, {
          duration: 4000,
        });
        syncStoreFromCurrentState();
      }
    } catch (e) {
      console.warn("[EpisodeProgress] Ошибка булк-синхра:", e);
      if (!silent) {
        toast.error("Не удалось сохранить прогресс");
      }
    } finally {
      loading.value = false;
    }
  };

  const bulkSyncUpTo = async (
    watchedUpTo: number,
    season = 1,
    silent = false,
  ) => bulkSyncSeasons([{ season, watchedUpTo }], silent);

  const resetProgress = async () => {
    if (!auth.isAuthenticated) return;
    try {
      loading.value = true;
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        action: "bulk",
        reset: true,
      });
      episodes.value = new Map();
      toast.info("Прогресс сброшен");
      progressStore.clearProgress(animeId);
    } catch (e) {
      console.warn("[EpisodeProgress] Ошибка сброса:", e);
    } finally {
      loading.value = false;
    }
  };

  return {
    episodes: readonly(episodes),
    totalEpisodes: readonly(totalEpisodes),
    loading: readonly(loading),
    loaded: readonly(loaded),

    watchedCount,
    progressPercent,
    nextEpisodeToWatch,
    lastWatchedEpisode,

    getEpisode,
    isWatched,
    isInProgress,
    setEpisodeGroups,

    loadProgress,
    updatePosition,
    autoMarkWatched,
    markWatched,
    skipEpisode,
    undoMark,
    bulkSyncSeasons,
    bulkSyncUpTo,
    resetProgress,
  };
}
