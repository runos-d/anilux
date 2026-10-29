import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import playlistsApi from '@/api/playlists';

type FavoriteMessage = { ids?: unknown; owner?: number };

const favoriteChannel = typeof BroadcastChannel !== 'undefined'
  ? new BroadcastChannel('anime_favorites')
  : null;

export const useFavoritesStore = defineStore('favorites', () => {
  const ids = ref<Set<number>>(new Set());
  const pending = ref<Set<number>>(new Set());
  const loaded = ref(false);
  const localOverrides = new Map<number, boolean>();
  let loadPromise: Promise<void> | null = null;
  let generation = 0;

  const isFavorite = (id: number) => ids.value.has(id);
  const isPending = (id: number) => pending.value.has(id);

  function replaceFromServer(animeIds: number[]) {
    const next = new Set(animeIds);
    for (const [animeId, value] of localOverrides) {
      if (value) next.add(animeId);
      else next.delete(animeId);
    }
    ids.value = next;
    loaded.value = true;
  }

  function syncFromIds(animeIds: number[]) {
    replaceFromServer(animeIds);
  }

  function setIdsFavorite(animeIds: number[], value: boolean) {
    const next = new Set(ids.value);
    for (const animeId of animeIds) {
      localOverrides.set(animeId, value);
      if (value) next.add(animeId);
      else next.delete(animeId);
    }
    ids.value = next;
  }

  async function settleIds(animeIds: number[], value: boolean) {
    setIdsFavorite(animeIds, value);
    if (loadPromise) {
      try {
        await loadPromise;
      } catch {
      }
    }
    for (const animeId of animeIds) {
      if (localOverrides.get(animeId) === value) localOverrides.delete(animeId);
    }
    favoriteChannel?.postMessage({ ids: [...ids.value], owner: useAuthStore().user?.id });
  }

  async function add(id: number) {
    if (pending.value.has(id)) return;
    pending.value.add(id);
    setIdsFavorite([id], true);
    try {
      await playlistsApi.addToFavorites(id);
      await settleIds([id], true);
    } catch (e) {
      setIdsFavorite([id], false);
      if (loadPromise) await loadPromise.catch(() => undefined);
      localOverrides.delete(id);
      throw e;
    } finally {
      pending.value.delete(id);
    }
  }

  async function remove(id: number) {
    if (pending.value.has(id)) return;
    pending.value.add(id);
    setIdsFavorite([id], false);
    try {
      await playlistsApi.removeFromFavorites(id);
      await settleIds([id], false);
    } catch (e) {
      setIdsFavorite([id], true);
      if (loadPromise) await loadPromise.catch(() => undefined);
      localOverrides.delete(id);
      throw e;
    } finally {
      pending.value.delete(id);
    }
  }

  async function setFavorite(id: number, value: boolean) {
    if (value) await add(id);
    else await remove(id);
  }

  async function commitIdsFavorite(animeIds: number[], value: boolean) {
    await settleIds(animeIds, value);
  }

  async function ensureLoaded(force = false) {
    if (!useAuthStore().isAuthenticated) return;
    if (loaded.value && !force) return;
    if (!loadPromise) {
      const requestGeneration = generation;
      const request = playlistsApi.getFavoriteAnimeIds()
        .then(({ data }) => {
          if (requestGeneration !== generation) return;
          replaceFromServer(data.anime_ids || []);
        });
      const trackedRequest = request.finally(() => {
        if (loadPromise === trackedRequest) loadPromise = null;
      });
      loadPromise = trackedRequest;
    }
    await loadPromise;
  }

  function reset() {
    generation += 1;
    loadPromise = null;
    localOverrides.clear();
    ids.value = new Set();
    pending.value = new Set();
    loaded.value = false;
  }

  favoriteChannel?.addEventListener('message', (event: MessageEvent<FavoriteMessage>) => {
    if (!useAuthStore().isAuthenticated || event.data?.owner !== useAuthStore().user?.id || !Array.isArray(event.data?.ids)) return;
    syncFromIds(event.data.ids.filter((id): id is number => Number.isInteger(id)));
  });

  if (typeof window !== 'undefined') {
    const refresh = () => {
      if (!localStorage.getItem('anilux_access_token_v1')) return;
      void ensureLoaded(true).catch(() => undefined);
    };
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') refresh();
    });
  }

  return {
    ids,
    pending,
    loaded,
    isFavorite,
    isPending,
    add,
    remove,
    setFavorite,
    syncFromIds,
    setIdsFavorite,
    commitIdsFavorite,
    ensureLoaded,
    reset,
  };
});
