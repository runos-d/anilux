import { computed, watch, type WatchStopHandle } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useFavoritesStore } from "@/stores/favorites";
import { useProgressSync } from "@/composables/useProgressSync";

export function useFavorite(idGetter: () => number) {
  const favorites = useFavoritesStore();
  const isFavorite = computed(() => favorites.isFavorite(idGetter()));
  const loading = computed(() => favorites.isPending(idGetter()));
  const checkStatus = async () => {
    try {
      await favorites.ensureLoaded();
    } catch {
    }
  };

  const toggleFavorite = async () => {
    const id = idGetter();
    if (!id) return;
    const next = !isFavorite.value;
    try {
      await favorites.setFavorite(id, next);
      useProgressSync().bump();
    } catch {
    }
  };

  let stopWatch: WatchStopHandle | null = null;
  const startWatch = () => {
    stopWatch?.();
    stopWatch = watch(
      () => idGetter(),
      () => {},
      { immediate: true },
    );
  };

  startWatch();
  const auth = useAuthStore();
  watch(() => auth.isAuthenticated, authenticated => { if (authenticated) void checkStatus(); }, { immediate: true });

  return { isFavorite, loading, error: computed(() => null), checkStatus, toggleFavorite };
}
