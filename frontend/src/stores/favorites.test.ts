import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, expect, it, vi } from 'vitest';
const state = vi.hoisted(() => ({ auth: { isAuthenticated: false, user: { id: 42 } }, get: vi.fn().mockResolvedValue({ data: { anime_ids: [1, 2] } }) }));
vi.mock('@/stores/auth', () => ({ useAuthStore: () => state.auth }));
vi.mock('@/api/playlists', () => ({ default: { getFavoriteAnimeIds: state.get } }));
import { useFavoritesStore } from './favorites';
beforeEach(() => { setActivePinia(createPinia()); state.auth.isAuthenticated = false; state.get.mockClear(); });
it('does not request a private favorite list for guests', async () => {
  const store = useFavoritesStore();
  await store.ensureLoaded(); await store.ensureLoaded(true);
  expect(state.get).not.toHaveBeenCalled();
  expect(store.loaded).toBe(false);
});
it('deduplicates authenticated loading and resets on an account switch', async () => {
  state.auth.isAuthenticated = true;
  const store = useFavoritesStore();
  await Promise.all([store.ensureLoaded(), store.ensureLoaded()]);
  expect(state.get).toHaveBeenCalledTimes(1);
  expect(store.isFavorite(1)).toBe(true);
  store.reset(); state.auth.isAuthenticated = false;
  await store.ensureLoaded();
  expect(store.isFavorite(1)).toBe(false);
  expect(state.get).toHaveBeenCalledTimes(1);
});
