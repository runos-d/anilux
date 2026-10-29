import { computed, onScopeDispose, onActivated, onDeactivated, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useGlobalWebSocket } from '@/composables/useGlobalWebSocket';
import apiClient from '@/api/client';
import { afterInitialContent } from '@/lib/initialContent';

const interests = new Map<symbol, Set<number>>();
let timer: ReturnType<typeof setInterval> | undefined;
let scheduled: ReturnType<typeof setTimeout> | undefined;
let controller: AbortController | undefined;
let pending: Promise<void> | undefined;
let owner: number | undefined;
let lastSeed = 0;
let publishInterest: (ids: number[]) => void = () => {};

async function seedOnlineUsers() {
  const auth = useAuthStore();
  const account = auth.isAuthenticated ? auth.user?.id : undefined;
  if (owner !== account) {
    controller?.abort(); pending = undefined;
    auth.onlineUsers.clear(); owner = account;
  }
  if (!account || document.hidden || pending) return pending;
  const ids = [...new Set([...interests.values()].flatMap(value => [...value]))];
  if (!ids.length) return;
  const ac = new AbortController(); controller = ac;
  lastSeed = Date.now();
  pending = (async () => {
    for (let offset = 0; offset < ids.length; offset += 200) {
      const batch = ids.slice(offset, offset + 200);
      const before = new Map(batch.map(id => [id, auth.onlineUsers.get(id)]));
      try {
        const { data } = await apiClient.get<{ results: { id: number; is_online: boolean }[] }>('/users/online/', {
          params: { ids: batch.join(',') }, signal: ac.signal, timeout: 5000,
        });
        if (ac.signal.aborted || !auth.isAuthenticated || auth.user?.id !== account) return;
        const states = new Map(data.results.map(row => [row.id, row.is_online]));
        for (const id of batch) if (auth.onlineUsers.get(id) === before.get(id))
          auth.updateUserOnlineStatus(id, states.get(id) ?? false);
      } catch { return; }
    }
  })().finally(() => { if (controller === ac) { controller = undefined; pending = undefined; } });
  return pending;
}

function scheduleSeed() {
  if (scheduled) return;
  scheduled = setTimeout(() => {
    scheduled = undefined;
    publishInterest([...new Set([...interests.values()].flatMap(value => [...value]))].slice(-200));
    void seedOnlineUsers();
  }, 150);
}

export function useOnlineStatus() {
  const key = Symbol('presence'); const ids = new Set<number>(); interests.set(key, ids);
  const auth = useAuthStore();
  const { connect: connectGlobalWs, isConnected, send } = useGlobalWebSocket();
  let disposed = false, active = true;
  publishInterest = ids => send?.({ action: 'subscribe_presence', user_ids: ids });
  onDeactivated(() => { active = false; interests.delete(key); scheduleSeed(); });
  onActivated(() => { active = true; interests.set(key, ids); scheduleSeed(); });
  if (!timer) timer = setInterval(() => {
    if (!document.hidden && (!isConnected.value || Date.now() - lastSeed >= 299_000)) void seedOnlineUsers();
  }, 60_000);
  const foreground = () => { if (!document.hidden) scheduleSeed(); };
  document.addEventListener('visibilitychange', foreground);
  watch([() => auth.isAuthenticated, () => auth.user?.id], () => {
    const account = auth.isAuthenticated ? auth.user?.id : undefined;
    if (owner !== account) { controller?.abort(); pending = undefined; auth.onlineUsers.clear(); owner = account; }
    afterInitialContent(() => {
    if (disposed || !active) return;
    if (auth.isAuthenticated) connectGlobalWs();
    scheduleSeed();
    });
  }, { immediate: true });
  watch(isConnected, connected => { if (connected) scheduleSeed(); });
  onScopeDispose(() => {
    disposed = true; interests.delete(key);
    scheduleSeed();
    document.removeEventListener('visibilitychange', foreground);
    if (!interests.size) {
      publishInterest([]);
      clearInterval(timer); clearTimeout(scheduled); timer = undefined; scheduled = undefined;
      controller?.abort(); controller = undefined; pending = undefined;
    }
  });
  return {
    isUserOnline: (id: number) => {
      if (active && Number.isInteger(id) && id > 0 && !ids.has(id)) {
        ids.add(id); if (ids.size > 200) ids.delete(ids.values().next().value!);
        scheduleSeed();
      }
      return auth.onlineUsers.get(id)?.is_online ?? false;
    },
    getOnlineCount: computed(() => [...auth.onlineUsers.values()].filter(value => value.is_online).length),
    seedOnlineUsers, connectGlobalWs,
  };
}
