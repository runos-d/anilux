<template>
  <Teleport to="body">
    <Transition name="psm-anim">
      <div
        v-if="show"
        class="modal-overlay"
        @click.self="handleClose"
        @keydown.esc="handleClose"
      >
        <div class="modal-content playlist-select-modal">
          <div class="modal-header">
            <h2 class="modal-title">Добавить в плейлист</h2>
            <button @click="handleClose" class="modal-close" type="button">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="anime-preview">
              <div
                v-if="animePosterUrl"
                style="
                  width: 80px;
                  height: 112px;
                  flex-shrink: 0;
                  border-radius: 8px;
                  overflow: hidden;
                "
              >
                <img
                  :src="animePosterUrl"
                  :alt="anime.title_ru || anime.title_en"
                  style="width: 100%; height: 100%; object-fit: cover"
                  loading="lazy"
                />
              </div>
              <div v-else class="anime-poster-placeholder">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <rect x="2" y="2" width="20" height="20" rx="2" />
                  <path d="M12 2v20M2 12h20" />
                </svg>
              </div>
              <div class="anime-info">
                <h3 class="anime-title">
                  {{ anime.title_ru || anime.title_en }}
                </h3>
                <p v-if="anime.year" class="anime-year">{{ anime.year }}</p>
              </div>
            </div>

            <div class="playlists-section">
              <div class="playlists-header">
                <h4 class="playlists-title">Выберите плейлисты</h4>
                <button
                  @click="handleCreatePlaylist"
                  class="create-playlist-btn"
                  type="button"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  Создать новый
                </button>
              </div>

              <div v-if="displayedPlaylists.length > 8" class="playlists-search">
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Поиск плейлистов..."
                  class="search-input"
                />
              </div>

              <div class="playlists-list">
                <div v-if="isLoading" class="playlists-loading">
                  <div class="loading-spinner"></div>
                  <span>Загрузка...</span>
                </div>

                <div
                  v-else-if="filteredPlaylists.length === 0"
                  class="playlists-empty"
                >
                  <svg
                    width="40"
                    height="40"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path d="M9 18V5l12-2v13" />
                    <circle cx="6" cy="18" r="3" />
                    <circle cx="18" cy="16" r="3" />
                  </svg>
                  <p>
                    {{
                      searchQuery
                        ? "Плейлисты не найдены"
                        : "У вас пока нет плейлистов"
                    }}
                  </p>
                </div>

                <label
                  v-for="playlist in filteredPlaylists"
                  :key="playlist.id"
                  :class="[
                    'playlist-item',
                    { selected: selectedPlaylists.includes(typeof playlist.id === 'number' ? playlist.id : Number(playlist.id) || 0) },
                  ]"
                >
                  <input
                    type="checkbox"
                    :value="playlist.id"
                    v-model="selectedPlaylists"
                    class="playlist-checkbox"
                  />
                  <div class="playlist-cover">
                    <div class="playlist-mini-posters">
                      <template
                        v-if="playlist.cover_urls && playlist.cover_urls.length"
                      >
                        <div
                          v-for="(url, index) in playlist.cover_urls.slice(
                            0,
                            4,
                          )"
                          :key="index"
                          class="mini-poster"
                        >
                          <img :src="url" alt="" loading="lazy" />
                        </div>
                      </template>
                      <template v-else-if="playlist.items?.length">
                        <div
                          v-for="(item, index) in playlist.items.slice(0, 4)"
                          :key="index"
                          class="mini-poster"
                        >
                          <img
                            v-if="item.anime_poster || item.anime_poster_url"
                            :src="
                              getMediaUrl(item.anime_poster) ||
                              getMediaUrl(item.anime_poster_url) ||
                              undefined
                            "
                            alt=""
                            loading="lazy"
                          />
                        </div>
                      </template>
                      <div v-else class="mini-poster-empty">
                        <svg
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                        >
                          <path d="M9 18V5l12-2v13" />
                          <circle cx="6" cy="18" r="3" />
                          <circle cx="18" cy="16" r="3" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  <div class="playlist-info">
                    <div class="playlist-name">{{ playlist.title }}</div>
                    <div class="playlist-meta">
                      {{ playlist.items_count ?? playlist.items?.length ?? 0 }} аниме
                    </div>
                  </div>
                  <div class="playlist-privacy">
                    <svg
                      v-if="!playlist.is_public"
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                    <svg
                      v-else
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <line x1="2" y1="12" x2="22" y2="12" />
                      <path
                        d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"
                      />
                    </svg>
                  </div>
                </label>
                <button
                  v-if="canLoadMore && !searchQuery"
                  class="load-more-playlists"
                  type="button"
                  :disabled="isLoadingMore"
                  @click="loadMorePlaylists"
                >
                  {{ isLoadingMore ? "Загрузка..." : "Показать ещё" }}
                </button>
              </div>
            </div>

            <div class="note-section">
              <label class="note-label">Заметка (необязательно)</label>
              <textarea
                v-model="note"
                placeholder="Добавьте заметку к аниме..."
                class="note-input"
                rows="2"
                maxlength="150"
              ></textarea>
              <div class="note-counter">{{ note.length }}/150</div>
            </div>
          </div>

          <div class="modal-footer">
            <button
              @click="handleClose"
              class="btn btn-secondary"
              type="button"
            >
              Отмена
            </button>
            <button
              @click="handleSave"
              :disabled="selectedPlaylists.length === 0"
              class="btn btn-primary"
              type="button"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Добавить
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import type { Anime, Playlist } from "@/types";
import { getMediaUrl } from "@/api/client";
import playlistsApi from "@/api/playlists";

const animePosterUrl = computed(() => {
  const a = props.anime;

  const posterFields = [
    a.poster,
    a.poster_file,
    a.poster_image_url,
    a.poster_url,
  ];

  for (const poster of posterFields) {
    if (poster && typeof poster === "string" && poster.trim() !== "") {
      const url = getMediaUrl(poster);
      if (url) return url;
    }
  }
  return null;
});

interface Props {
  show: boolean;
  anime: Anime;
  playlists?: Playlist[];
  isLoading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  playlists: () => [],
  isLoading: false,
});

const emit = defineEmits<{
  close: [];
  save: [data: PlaylistSaveData];
  createPlaylist: [];
}>();

export interface PlaylistSaveData {
  animeId: number;
  playlistIds: number[];
  note?: string;
}

const selectedPlaylists = ref<number[]>([]);
const searchQuery = ref("");
const note = ref("");
const additionalPlaylists = ref<Playlist[]>([]);
const nextPage = ref(2);
const isLoadingMore = ref(false);
const paginationExhausted = ref(false);

const displayedPlaylists = computed(() => {
  const merged = [...props.playlists, ...additionalPlaylists.value];
  return Array.from(new Map(merged.map((playlist) => [String(playlist.id), playlist])).values());
});

const canLoadMore = computed(
  () => !paginationExhausted.value && props.playlists.length >= 20,
);

const filteredPlaylists = computed(() => {
  if (!searchQuery.value) {
    return displayedPlaylists.value;
  }

  const query = searchQuery.value.toLowerCase();
  return displayedPlaylists.value.filter((playlist) =>
    playlist.title.toLowerCase().includes(query),
  );
});

const handleSave = () => {
  const data: PlaylistSaveData = {
    animeId: props.anime.id,
    playlistIds: selectedPlaylists.value,
    note: note.value || undefined,
  };

  emit("save", data);
  resetForm();
};

const handleCreatePlaylist = () => {
  emit("createPlaylist");
};

const handleClose = () => {
  emit("close");
};

const resetForm = () => {
  selectedPlaylists.value = [];
  searchQuery.value = "";
  note.value = "";
  additionalPlaylists.value = [];
  nextPage.value = 2;
  paginationExhausted.value = false;
};

const loadMorePlaylists = async () => {
  if (isLoadingMore.value || paginationExhausted.value) return;
  isLoadingMore.value = true;
  try {
    const response = await playlistsApi.getMyPlaylistsPage(nextPage.value, 20);
    additionalPlaylists.value.push(...response.data.results);
    nextPage.value += 1;
    paginationExhausted.value = !response.data.next;
  } catch (error) {
    console.error("Error loading more playlists:", error);
  } finally {
    isLoadingMore.value = false;
  }
};

watch(() => props.show, (show) => {
  if (show) resetForm();
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--surface-2, var(--surface-3));
  border-radius: 1rem;
  max-width: 500px;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  transform: scale(1);
  opacity: 1;
  transition:
    transform 0.2s ease-out,
    opacity 0.2s ease-out;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle, var(--border-subtle));
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.modal-close:hover {
  background-color: var(--surface-4);
  color: var(--accent-3);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.anime-preview {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: var(--surface-4);
  border-radius: 0.5rem;
  margin-bottom: 1.25rem;
}

.anime-poster {
  width: 48px;
  height: 67px;
  object-fit: cover;
  border-radius: 0.375rem;
  flex-shrink: 0;
}

.anime-poster-placeholder {
  width: 48px;
  height: 67px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--surface-3);
  border-radius: 0.375rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.anime-info {
  flex: 1;
  min-width: 0;
}

.anime-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.anime-year {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin: 0;
}

.playlists-section {
  margin-bottom: 1.25rem;
}

.playlists-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.playlists-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.create-playlist-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background-color: var(--accent);
  border: none;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-on-accent);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.create-playlist-btn:hover {
  background-color: var(--accent-hover);
  transform: translateY(-1px);
}

.playlists-search {
  margin-bottom: 0.75rem;
}

.search-input {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-primary);
  background-color: var(--surface-3);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
}

.search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.playlists-list {
  max-height: 250px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.load-more-playlists {
  width: 100%;
  padding: 0.7rem;
  color: var(--accent);
  background: transparent;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  cursor: pointer;
}

.load-more-playlists:hover:not(:disabled) {
  border-color: var(--accent);
  background: var(--surface-4);
}

.load-more-playlists:disabled {
  cursor: wait;
  opacity: 0.65;
}

.playlists-loading,
.playlists-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem 1rem;
  color: var(--text-tertiary);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.playlists-empty p {
  margin: 0;
  font-size: 0.875rem;
  text-align: center;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  user-select: none;
}

.playlist-item:hover {
  border-color: var(--accent);
  background-color: var(--surface-3);
}

.playlist-item.selected {
  background-color: rgba(58, 134, 255, 0.1);
  border-color: var(--accent);
}

.playlist-checkbox {
  display: none;
}

.playlist-cover {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: 0.375rem;
  overflow: hidden;
  background-color: var(--surface-3);
}

.playlist-mini-posters {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 1px;
  width: 100%;
  height: 100%;
}

.mini-poster {
  background-color: var(--surface-4);
}

.mini-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mini-poster-empty {
  grid-column: span 2;
  grid-row: span 2;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  background-color: var(--surface-4);
  width: 100%;
  height: 100%;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.125rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.playlist-meta {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.playlist-privacy {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.note-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.note-label {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.note-input {
  width: 100%;
  padding: 0.625rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-primary);
  background-color: var(--surface-3);
  outline: none;
  resize: vertical;
  transition: all 0.2s var(--transition-smooth);
  font-family: inherit;
}

.note-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.note-counter {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  text-align: right;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--border-subtle);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid;
}

.btn-primary {
  background-color: var(--accent);
  border-color: var(--accent);
  color: var(--text-on-accent);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--accent-hover);
  border-color: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: transparent;
  border-color: var(--border-strong);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background-color: var(--surface-4);
  border-color: var(--accent);
  color: var(--accent);
}

/* Анимация на overlay (fade) и на modal-content (scale+slide) */
.psm-anim-enter-active {
  transition: opacity 0.22s ease;
}
.psm-anim-leave-active {
  transition: opacity 0.18s ease;
}
.psm-anim-enter-from,
.psm-anim-leave-to {
  opacity: 0;
}

.psm-anim-enter-active .modal-content {
  transition:
    transform 0.25s cubic-bezier(0.34, 1.4, 0.64, 1),
    opacity 0.22s ease;
}
.psm-anim-leave-active .modal-content {
  transition:
    transform 0.18s ease,
    opacity 0.18s ease;
}
.psm-anim-enter-from .modal-content {
  transform: scale(0.9) translateY(20px);
  opacity: 0;
}
.psm-anim-leave-to .modal-content {
  transform: scale(0.95) translateY(8px);
  opacity: 0;
}

@media (max-width: 768px) {
  .modal-content {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .playlists-list {
    max-height: 200px;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }
}
</style>
