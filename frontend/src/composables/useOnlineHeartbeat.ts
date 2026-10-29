import { watch, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api/client';
import { globalConnectionReady, sendPresence } from '@/lib/realtimeStatus';

/** HTTP is a recovery path; the open socket carries normal presence updates. */
export function useOnlineHeartbeat() {
  const auth = useAuthStore();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let generation = 0;
  let lastSent = 0;
  let lastActive: boolean | undefined;
  const send = (visibility = false) => {
    const token = localStorage.getItem('anilux_access_token_v1');
    if (!auth.isAuthenticated || !token) return;
    const active = !document.hidden;
    const now = Date.now();
    if (active === lastActive && now - lastSent < 5000) return;
    if (globalConnectionReady.value) {
      if (visibility && sendPresence(active)) { lastSent = now; lastActive = active; }
      return;
    }
    lastSent = now; lastActive = active;
    void apiClient.post('/users/heartbeat/', { is_active: active }).catch(() => undefined);
  };
  const stop = () => { generation++; clearTimeout(timer); timer = undefined; lastSent = 0; lastActive = undefined; };
  const start = () => {
    stop();
    const current = generation;
    const tick = () => {
      if (current !== generation || !auth.isAuthenticated) return;
      send();
      timer = setTimeout(tick, 60_000 + Math.random() * 15_000);
    };
    // Give the WebSocket time to connect, avoiding one redundant HTTP call per login.
    timer = setTimeout(tick, 3000 + Math.random() * 2000);
  };
  watch(() => auth.isAuthenticated, value => { if (value) start(); else stop(); }, { immediate: true });
  const visibility = () => send(true);
  onMounted(() => {
    document.addEventListener('visibilitychange', visibility);
    window.addEventListener('focus', visibility);
  });
  onUnmounted(() => {
    stop();
    document.removeEventListener('visibilitychange', visibility);
    window.removeEventListener('focus', visibility);
  });
}
