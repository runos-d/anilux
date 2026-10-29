import { onScopeDispose } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { queryClient } from '@/lib/queryClient';
import { publicCacheReady } from '@/lib/publicReadCache';
const handledInvalidations = new WeakSet<object>();

/** Subscribe legacy ref-based screens to the same cache used by Vue Query. */
export function useCachedReads(visible: () => boolean = () => true) {
  const auth = useAuthStore();
  let disposed = false;
  const observers = new Map<string, { group: string; scope: string; queryKey: readonly unknown[]; assign: (data: unknown) => void; refresh: () => Promise<unknown> }>();
  const unsubscribe = queryClient.getQueryCache().subscribe(event => {
    const observer = observers.get(event.query.queryHash);
    if (!observer || event.type !== 'updated' || !visible()) return;
    const scope = String(auth.user?.id ?? 'guest');
    if (observer.scope !== 'public' && observer.scope !== scope) return;
    if (event.action.type === 'success') observer.assign(event.query.state.data);
    if (event.action.type === 'invalidate') {
      if (handledInvalidations.has(event)) return;
      handledInvalidations.add(event);
      const cancelled = queryClient.cancelQueries({ queryKey:event.query.queryKey, exact:true });
      void cancelled.then(observer.refresh).catch(() => undefined);
    }
  });
  onScopeDispose(() => { disposed = true; observers.clear(); unsubscribe(); });
  return async function read<T>(key: readonly unknown[], fn: (signal?: AbortSignal) => Promise<T>, assign: (data: T) => void, isPublic = false): Promise<T> {
    const scope = isPublic ? 'public' : String(auth.user?.id ?? 'guest');
    const queryKey = ['read', scope, ...key];
    const group = JSON.stringify(key[0]);
    if (isPublic) await publicCacheReady;
    const query = queryClient.getQueryCache().build(queryClient, { queryKey, queryFn: ({ signal }) => fn(signal) });
    const refresh = () => disposed || !visible()
      ? Promise.reject(new DOMException('Screen closed', 'AbortError'))
      : queryClient.fetchQuery({ queryKey, queryFn: ({ signal }) => fn(signal), staleTime: 0 });
    for (const [hash, observer] of observers) if (observer.group === group && hash !== query.queryHash) {
      observers.delete(hash);
      await queryClient.cancelQueries({ queryKey:observer.queryKey, exact:true });
    }
    if (disposed) throw new DOMException('Screen closed', 'AbortError');
    observers.set(query.queryHash, { group, scope, queryKey, assign: data => { if (!disposed && (isPublic || scope === String(auth.user?.id ?? 'guest'))) assign(data as T); }, refresh });
    const cached = queryClient.getQueryData<T>(queryKey);
    if (cached !== undefined) {
      assign(cached);
      if (query.isStaleByTime(60_000)) void refresh().catch(() => undefined);
      return cached;
    }
    return refresh();
  };
}
