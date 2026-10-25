<template>
  <button
    :class="['btn', 'btn-secondary', 'favorite-btn', { 'is-favorite': isFavorite }]"
    @click.stop="toggleFavorite"
    :disabled="loading"
    type="button"
  >
    <span v-if="loading" class="loading-spinner"></span>
    <svg
      v-else
      width="18"
      height="18"
      viewBox="0 0 24 24"
      :fill="isFavorite ? 'currentColor' : 'none'"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      class="icon"
    >
      <path
        d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
      />
    </svg>
    <span class="text">{{ isFavorite ? "В избранном" : "В избранное" }}</span>
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useFavoritesStore } from "@/stores/favorites";
import playlistsApi from "@/api/playlists";

interface Props {
  animeId: number;
  animeTitle?: string;
  animePoster?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  toggle: [isFavorite: boolean];
  error: [message: string];
}>();

const favorites = useFavoritesStore();
void favorites.ensureLoaded().catch(() => undefined);
const isFavorite = computed(() => favorites.isFavorite(props.animeId));
const loading = computed(() => favorites.isPending(props.animeId));

const toggleFavorite = async () => {
  if (loading.value) return;
  const next = !isFavorite.value;
  try {
    await favorites.setFavorite(props.animeId, next);
    emit("toggle", next);
  } catch (error: unknown) {
    const message = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Ошибка при изменении избранного";
    emit("error", message);
  }
};
</script>

<style scoped>
.favorite-btn {
}

.favorite-btn:hover {
}

.favorite-btn.is-favorite {
  background: var(--accent);
  border-color: transparent;
  color: var(--text-on-accent);
}

.favorite-btn.is-favorite:hover {
  background: var(--accent-hover);
}

.favorite-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.icon {
  flex-shrink: 0;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
