import { watch, onMounted, onUnmounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import apiClient from "@/api/client";
import { afterInitialContent } from '@/lib/initialContent';

const HEARTBEAT_INTERVAL = 30_000;

let timer: ReturnType<typeof setInterval> | null = null;
let lastHeartbeat = 0;
let lastActive: boolean | null = null;

function sendHeartbeat(isActive: boolean) {
  const token = localStorage.getItem("anilux_access_token_v1");
  if (!token) return;

  const currentTime = Date.now();
  if (lastActive === isActive && currentTime - lastHeartbeat < 5000) {
    return; // Skip if heartbeat was sent within last 5 seconds
  }
  lastHeartbeat = currentTime;
  lastActive = isActive;

  apiClient
    .post("/users/heartbeat/", { is_active: isActive })
    .catch(() => {
      /* тихо игнорируем сетевые ошибки */
    });
}

function start(isAuthenticated: boolean) {
  if (!isAuthenticated) return;

  afterInitialContent(() => { if (localStorage.getItem('anilux_access_token_v1')) sendHeartbeat(!document.hidden); });

  if (timer) clearInterval(timer);
  timer = setInterval(() => {
    const visible = !document.hidden;
    sendHeartbeat(visible);
  }, HEARTBEAT_INTERVAL);

}

function stop() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
  lastHeartbeat = 0;
  lastActive = null;
}

/**
 * Пингует бэкенд, пока страница открыта, чтобы ключ
 * "В сети" в Redis не истекал для активного пользователя.
 */
export function useOnlineHeartbeat() {
  const authStore = useAuthStore();

  const onVisibility = () => {
    if (authStore.isAuthenticated) sendHeartbeat(!document.hidden);
  };

  watch(
    () => authStore.isAuthenticated,
    (isAuth) => {
      if (isAuth) {
        start(true);
      } else {
        stop();
      }
    },
    { immediate: true },
  );

  onMounted(() => {
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("focus", onVisibility);
  });

  onUnmounted(() => {
    stop();
    document.removeEventListener("visibilitychange", onVisibility);
    window.removeEventListener("focus", onVisibility);
  });
}
