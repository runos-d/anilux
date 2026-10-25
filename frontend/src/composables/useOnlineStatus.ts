import { computed, onScopeDispose, watch } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useGlobalWebSocket } from "@/composables/useGlobalWebSocket";
import { reconcilePresence } from "@/lib/onlinePresence";
import apiClient from "@/api/client";
import { afterInitialContent } from '@/lib/initialContent';

let subscribers = 0;
let timer: ReturnType<typeof setInterval> | null = null;
let accountId: number | null = null;
let pending: Promise<void> | null = null;
let controller: AbortController | null = null;

async function seedOnlineUsers() {
  const store = useAuthStore();
  const owner = store.isAuthenticated ? store.user?.id ?? null : null;
  if (owner !== accountId) {
    controller?.abort();
    pending = null;
    store.onlineUsers.clear();
    accountId = owner;
  }
  if (!owner) return;
  if (pending) return pending;
  const ac = new AbortController();
  controller = ac;
  const before = new Map(store.onlineUsers);
  pending = (async () => {
    try {
      const { data } = await apiClient.get<{ results: { id: number }[] }>("/users/online/", {
        signal: ac.signal, timeout: 10000,
      });
      if (ac.signal.aborted || !store.isAuthenticated || store.user?.id !== owner) return;
      reconcilePresence(store.onlineUsers, before, data.results.map(user => user.id), store.updateUserOnlineStatus, owner);
    } catch {
    } finally {
      if (controller === ac) { controller = null; pending = null; }
    }
  })();
  return pending;
}

export function useOnlineStatus() {
  let disposed = false;
  const authStore = useAuthStore();
  const { connect: connectGlobalWs, isConnected } = useGlobalWebSocket();
  subscribers++;
  if (!timer) timer = setInterval(() => { void seedOnlineUsers(); }, 15000);
  watch(() => [authStore.isAuthenticated, authStore.user?.id], () => {
    afterInitialContent(() => {
      if (disposed) return;
      if (authStore.isAuthenticated) connectGlobalWs();
      void seedOnlineUsers();
    });
  }, { immediate: true });
  watch(isConnected, connected => { if (connected) void seedOnlineUsers(); });
  onScopeDispose(() => {
    disposed = true;
    if (--subscribers === 0) {
      if (timer) clearInterval(timer);
      timer = null;
      controller?.abort();
      controller = null;
      pending = null;
    }
  });
  return {
    isUserOnline: (id: number) => authStore.onlineUsers.get(id)?.is_online ?? false,
    getOnlineCount: computed(() => [...authStore.onlineUsers.values()].filter(value => value.is_online).length),
    seedOnlineUsers, connectGlobalWs,
  };
}
