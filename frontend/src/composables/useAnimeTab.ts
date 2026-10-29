import { ref, onUnmounted, getCurrentInstance } from "vue";
import apiClient from "@/api/client";
import { useAuthStore } from "@/stores/auth";

const PLAYER_PING_INTERVAL = 90 * 1000;
const WATCHING_PING_INTERVAL = 3 * 60 * 1000;

export function useAnimeTab(animeId: number) {
  const authStore = useAuthStore();

  const activityType = ref<"watching" | "player">("watching");
  const currentEpisode = ref<number | null>(null);
  let started = false;
  let _interval: ReturnType<typeof setInterval> | null = null;

  const sendPing = async () => {
    if (!started || !authStore.isAuthenticated || !animeId) return;
    try {
      await apiClient.post("/anime/active-tab/", {
        anime_id: animeId,
        activity_type: activityType.value,
        current_episode: currentEpisode.value,
      });
    } catch {}
  };

  const removeTab = async () => {
    if (!authStore.isAuthenticated || !animeId) return;
    try {
      await apiClient.delete("/anime/active-tab/", {
        params: { anime_id: animeId },
      });
    } catch {
    }
  };

  const resetInterval = () => {
    if (!started) return;
    if (_interval) {
      clearInterval(_interval);
      _interval = null;
    }
    const ms =
      activityType.value === "player"
        ? PLAYER_PING_INTERVAL
        : WATCHING_PING_INTERVAL;
    _interval = setInterval(() => {
      if (!document.hidden || activityType.value === "player") {
        sendPing();
      }
    }, ms);
  };

  const setPlayerActive = (active: boolean, episode?: number) => {
    if (episode !== undefined) currentEpisode.value = episode;
    const newType = active ? "player" : "watching";
    if (activityType.value !== newType) {
      activityType.value = newType;
      sendPing();
      resetInterval();
    }
  };

  const setEpisode = (episode: number) => {
    currentEpisode.value = episode;
    sendPing();
  };

  const onVisibilityChange = () => {
    if (!document.hidden) sendPing();
  };

  const stop = () => {
    if (!started) return;
    started = false;
    if (_interval) clearInterval(_interval);
    _interval = null;
    document.removeEventListener("visibilitychange", onVisibilityChange);
    removeTab();
  };

  if (getCurrentInstance()) onUnmounted(stop);

  const start = () => {
    if (started) return;
    started = true;
    sendPing();
    resetInterval();
    document.addEventListener("visibilitychange", onVisibilityChange);
  };

  return {
    activityType,
    currentEpisode,
    setPlayerActive,
    setEpisode,
    sendPing,
    stop,
    start,
  };
}
