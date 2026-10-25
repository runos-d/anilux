<template>
  <div class="attach-modal" @click.self="$emit('close')">
    <div class="attach-modal-overlay" @click.stop></div>
    <div class="attach-modal-content">
      <div class="attach-modal-header">
        <span class="attach-modal-title">{{ title }}</span>
        <button class="attach-modal-close" @click="$emit('close')" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button>
      </div>
      <div class="attach-modal-tabs">
        <!-- <button :class="{ active: modelValue === 'excerpt' }" @click="$emit('update:modelValue', 'excerpt')">Отрывки</button> -->
        <button
          :class="{ active: modelValue === 'anime' }"
          @click="$emit('update:modelValue', 'anime')"
        >
          <SakuraIcon name="anime-tv" /> Аниме
          <span v-if="selectedAnimes.length > 0" class="attach-tab-count">
            {{ selectedAnimes.length }}
          </span>
        </button>
        <button
          :class="{ active: modelValue === 'playlist' }"
          @click="$emit('update:modelValue', 'playlist')"
        >
          <SakuraIcon name="list" /> Плейлист
          <span v-if="selectedPlaylists.length > 0" class="attach-tab-count">
            {{ selectedPlaylists.length }}
          </span>
        </button>
        <button
          :class="{ active: modelValue === 'media' }"
          @click="$emit('update:modelValue', 'media')"
        >
          <SakuraIcon name="image" /> Фото/Видео
          <span v-if="selectedMediaFiles.length > 0" class="attach-tab-count">
            {{ selectedMediaFiles.length }}
          </span>
        </button>
      </div>
      <div class="attach-modal-body">
        <div v-if="modelValue === 'anime'" class="attach-tab-content">
          <div class="anime-search">
            <input
              :value="animeSearch"
              @input="onAnimeSearchInput"
              placeholder="Поиск аниме..."
              class="anime-search-input"
            />
            <div v-if="animeLoading" class="anime-loading">Загрузка...</div>
            <div v-else-if="animeResults.length === 0" class="anime-no-results">
              Введите название для поиска
            </div>
            <div
              v-for="a in animeResults"
              :key="a.id"
              class="anime-result"
              @click="toggleAnime(a)"
            >
              <OptimizedImage :src="getAnimePoster(a)" :alt="a.title_ru" :width="48" :height="72" sizes="48px" layout="fixed" class="attach-result-poster" />
              <div class="attach-result-info">
                <span class="anime-title">{{ a.title_ru }}</span>
                <span class="anime-desc">{{ a.title_en }}</span>
              </div>
              <span v-if="selectedAnimes.some((x) => x.id === a.id)" class="check-icon"><SakuraIcon name="check" :size="16" /></span>
            </div>
            <div v-if="animePage < animeTotalPages && !animeLoadingMore" class="anime-load-more">
              <button @click="loadMoreAnime" class="attach-load-more-btn">
                <SakuraIcon name="chevron-down" :size="14" /> Загрузить ещё
              </button>
            </div>
            <div v-if="animeLoadingMore" class="anime-load-more">
              <span class="attach-load-more-btn loading">
                <SakuraIcon name="spinner" :size="14" class="spin" /> Загрузка...
              </span>
            </div>
          </div>
        </div>
        <div v-if="modelValue === 'playlist'" class="attach-tab-content">
          <div class="playlist-search">
            <input
              :value="playlistSearch"
              @input="onPlaylistSearchInput"
              placeholder="Поиск плейлистов..."
              class="playlist-search-input"
            />
            <div v-if="playlistsLoading" class="playlist-loading">Загрузка...</div>
            <div v-else-if="playlists.length === 0" class="playlist-no-results">
              У вас пока нет плейлистов
            </div>
            <div
              v-for="p in playlists"
              :key="p.id"
              class="playlist-result"
              @click="togglePlaylist(p)"
            >
              <OptimizedImage :src="getPlaylistPoster(p)" :alt="p.title" :width="48" :height="72" sizes="48px" layout="fixed" class="attach-result-poster" />
              <div class="attach-result-info">
                <span class="playlist-title">{{ p.title }}</span>
                <span class="playlist-anime-count">{{ p.anime_count || p.items_count || 0 }} аниме</span>
              </div>
              <span v-if="selectedPlaylists.some((x) => x.id === p.id)" class="check-icon"><SakuraIcon name="check" :size="16" /></span>
            </div>
          </div>
        </div>
        <ExcerptPicker v-if="modelValue === 'excerpt'" :selected="selectedExcerpts" @update:selected="$emit('update:selectedExcerpts', $event)" />
        <div v-if="modelValue === 'media'" class="attach-tab-content">
          <div class="media-upload-area" @click="triggerMediaPick">
            <div class="upload-icon"><SakuraIcon name="camera" /></div>
            <div class="upload-text">Нажмите для выбора фото или видео</div>
            <div class="upload-hint">Поддерживается мультивыбор</div>
          </div>
          <input
            ref="mediaInput"
            type="file"
            accept="image/*,video/*,.jpg,.jpeg,.png,.gif,.webp,.mp4,.webm,.mov,.mkv,.avi,.m4v"
            multiple
            class="hidden-input"
            @change="onMediaSelected"
          />
          <div v-if="selectedMediaFiles.length > 0" class="selected-media-preview">
            <div class="selected-media-label">Выбрано файлов: {{ selectedMediaFiles.length }}</div>
            <div class="media-preview-grid">
              <div
                v-for="(m, idx) in selectedMediaFiles"
                :key="idx"
                class="media-preview-item"
              >
                <img v-if="m.type === 'image'" :src="m.url" alt="" />
                <video v-else :src="m.url" muted></video>
                <button class="remove-thumb-btn" @click="removeMediaFile(idx)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="attach-modal-footer">
        <div class="attach-modal-footer-left">
          <span v-if="modelValue === 'anime' && animeTotalCount > 0" class="attach-modal-total">
            {{ animePage }}/{{ animeTotalPages }} · {{ animeTotalCount }} найдено
          </span>
        </div>
        <div class="attach-modal-footer-right">
          <button class="attach-modal-btn-cancel" @click="$emit('close')">Отмена</button>
          <button class="attach-modal-btn-confirm" @click="confirm">
            Подтвердить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import ExcerptPicker from "@/components/excerpts/ExcerptPicker.vue";
import type { Excerpt } from "@/api/excerpts";
import apiClient from "@/api/client";
import animeApi from "@/api/anime";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import OptimizedImage from "@/components/common/OptimizedImage.vue";
import type { AnimeCard, PlaylistCard } from "@/api/feed";
import { getMediaUrl } from "@/api/client";
import { prepareMediaFiles } from "@/lib/clientMediaConversion";

const props = defineProps<{
  modelValue: "anime" | "playlist" | "media" | "excerpt";
  selectedExcerpts?: Excerpt[];
  title?: string;
  selectedAnimes: AnimeCard[];
  selectedPlaylists: PlaylistCard[];
  selectedMediaFiles: { type: string; url: string; file: File }[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: "anime" | "playlist" | "media" | "excerpt"];
  "update:selectedAnimes": [value: AnimeCard[]];
  "update:selectedPlaylists": [value: PlaylistCard[]];
  "update:selectedMediaFiles": [value: { type: string; url: string; file: File }[]];
  "update:selectedExcerpts": [value: Excerpt[]];
  close: [];
  confirm: [];
}>();

const animeSearch = ref("");
const animeResults = ref<AnimeCard[]>([]);
const animeLoading = ref(false);
const animeLoadingMore = ref(false);
const animePage = ref(1);
const animeTotalPages = ref(1);
const animeTotalCount = ref(0);
let animeSearchTimeout: ReturnType<typeof setTimeout> | null = null;

const playlistSearch = ref("");
const playlists = ref<PlaylistCard[]>([]);
const playlistsLoading = ref(false);
let playlistSearchTimeout: ReturnType<typeof setTimeout> | null = null;

const mediaInput = ref<HTMLInputElement | null>(null);

const getAnimePoster = (anime: AnimeCard): string => {
  if (!anime) return "";
  if (anime.poster) return getMediaUrl(anime.poster) || anime.poster_url || "";
  return anime.poster_url ? getMediaUrl(anime.poster_url) || anime.poster_url : "";
};

const getPlaylistPoster = (playlist: PlaylistCard): string => {
  if (!playlist) return "";
  if (playlist.cover_image) return getMediaUrl(playlist.cover_image) || "";
  return playlist.poster_url ? getMediaUrl(playlist.poster_url) || "" : "";
};

const searchAnime = () => {
  if (animeSearchTimeout) clearTimeout(animeSearchTimeout);
  animeSearchTimeout = setTimeout(async () => {
    const q = animeSearch.value.trim();
    if (!q) {
      animeResults.value = [];
      animePage.value = 1;
      animeTotalPages.value = 1;
      animeTotalCount.value = 0;
      return;
    }
    animePage.value = 1;
    animeLoading.value = true;
    try {
      const response = await animeApi.list({
        search: q,
        page: 1,
        page_size: 10,
        ordering: "-score",
      });
      animeResults.value = response.results || [];
      animeTotalPages.value = response.total_pages || 1;
      animeTotalCount.value = response.count || 0;
    } catch {
      animeResults.value = [];
      animeTotalPages.value = 1;
      animeTotalCount.value = 0;
    } finally {
      animeLoading.value = false;
    }
  }, 300);
};

const onAnimeSearchInput = (e: Event) => {
  animeSearch.value = (e.target as HTMLInputElement).value;
  searchAnime();
};

const loadMoreAnime = async () => {
  if (animeLoadingMore.value || animePage.value >= animeTotalPages.value) return;
  animeLoadingMore.value = true;
  animePage.value++;
  try {
    const q = animeSearch.value.trim();
    const response = await animeApi.list({
      search: q,
      page: animePage.value,
      page_size: 10,
      ordering: "-score",
    });
    animeResults.value.push(...(response.results || []));
    animeTotalPages.value = response.total_pages || 1;
    animeTotalCount.value = response.count || 0;
  } catch {
    animePage.value--;
  } finally {
    animeLoadingMore.value = false;
  }
};

const toggleAnime = (a: AnimeCard) => {
  const idx = props.selectedAnimes.findIndex((x) => x.id === a.id);
  if (idx >= 0) {
    emit("update:selectedAnimes", props.selectedAnimes.filter((x) => x.id !== a.id));
  } else {
    emit("update:selectedAnimes", [...props.selectedAnimes, a]);
  }
};

const searchPlaylists = async () => {
  if (playlistSearchTimeout) clearTimeout(playlistSearchTimeout);
  playlistSearchTimeout = setTimeout(async () => {
    playlistsLoading.value = true;
    try {
      const { data } = await apiClient.get("/playlists/playlists/my/");
      const list: PlaylistCard[] = Array.isArray(data)
        ? data
        : (data && typeof data === "object" && (data as { results?: PlaylistCard[] }).results) || [];
      const q = playlistSearch.value.trim().toLowerCase();
      playlists.value = q
        ? list.filter(
            (p) =>
              (p.title || "").toLowerCase().includes(q) ||
              (p.description || "").toLowerCase().includes(q),
          )
        : list;
    } catch {
      playlists.value = [];
    } finally {
      playlistsLoading.value = false;
    }
  }, 200);
};

watch(() => props.modelValue, val => {
  if (val === 'playlist') searchPlaylists();
}, { immediate: true });

const onPlaylistSearchInput = (e: Event) => {
  playlistSearch.value = (e.target as HTMLInputElement).value;
  searchPlaylists();
};

const togglePlaylist = (p: PlaylistCard) => {
  const idx = props.selectedPlaylists.findIndex((x) => x.id === p.id);
  if (idx >= 0) {
    emit("update:selectedPlaylists", props.selectedPlaylists.filter((x) => x.id !== p.id));
  } else {
    emit("update:selectedPlaylists", [...props.selectedPlaylists, p]);
  }
};

const triggerMediaPick = () => mediaInput.value?.click();

const onMediaSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  if (!input.files) return;
  const originals = Array.from(input.files);
  input.value = "";
  const prepared = await prepareMediaFiles(originals);
  const newFiles = prepared.filter(item => item.kind !== "file").map(({ file, kind }) => ({
    type: kind,
    url: URL.createObjectURL(file),
    file,
  }));
  emit("update:selectedMediaFiles", [...props.selectedMediaFiles, ...newFiles]);
};

const removeMediaFile = (idx: number) => {
  const m = props.selectedMediaFiles[idx];
  if (m && m.url && m.url.startsWith("blob:")) {
    URL.revokeObjectURL(m.url);
  }
  emit("update:selectedMediaFiles", props.selectedMediaFiles.filter((_, i) => i !== idx));
};

const confirm = () => {
  emit("confirm");
  emit("close");
};
</script>

<style scoped>
.attach-modal {
  position: fixed;
  inset: var(--viewport-top, 0px) 0 auto;
  height: var(--viewport-height, 100dvh);
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  padding: 1rem;
}

.attach-modal-overlay {
  position: absolute;
  inset: 0;
}

.attach-modal-content {
  position: relative;
  background: var(--surface-1, #0a0a0a);
  border-radius: 14px;
  border: 1px solid var(--border-subtle, #1a1a1a);
  width: 100%;
  max-width: 520px;
  max-height: calc(var(--viewport-height, 100dvh) * 0.85);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
}

.attach-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid var(--border-subtle, #1a1a1a);
}

.attach-modal-title {
  color: var(--text-primary, #fff);
  font-weight: 600;
  font-size: 0.95rem;
}

.attach-modal-close {
  background: none;
  border: none;
  color: var(--text-tertiary, #555);
  font-size: 1rem;
  cursor: pointer;
  padding: 0.2rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.attach-modal-close:hover {
  color: var(--text-primary, #fff);
  background: var(--surface-3, #1a1a1a);
}

.attach-modal-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle, #1a1a1a);
}

.attach-modal-tabs button {
  flex: 1;
  background: none;
  border: none;
  color: #777;
  padding: 0.75rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
}

.attach-modal-tabs button:hover {
  color: #aaa;
}

.attach-modal-tabs button.active {
  color: #fff;
  border-bottom: 2px solid var(--accent, #7c5cfc);
}

.attach-tab-count {
  background: var(--accent-subtle, rgba(124, 92, 252, 0.2));
  color: var(--accent, #7c5cfc);
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  font-weight: 600;
}

.attach-modal-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.attach-tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
}

.anime-search,
.playlist-search {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.anime-search-input,
.playlist-search-input {
  width: 100%;
  background: var(--surface-3, #141414);
  border: 1px solid var(--border-default, #252525);
  color: var(--text-primary, #e0e0e0);
  padding: 0.6rem 0.875rem;
  border-radius: 8px;
  font-size: 0.875rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.anime-search-input:focus,
.playlist-search-input:focus {
  outline: none;
  border-color: var(--accent, #7c5cfc);
}

.anime-loading,
.playlist-loading,
.anime-no-results,
.playlist-no-results {
  color: var(--text-tertiary, #555);
  font-size: 0.875rem;
  text-align: center;
  padding: 1.5rem;
}

.anime-result,
.playlist-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--surface-3);
  border: 1px solid rgba(34, 34, 34, 0.4);
  margin-bottom: 0.5rem;
}

.anime-result:hover,
.playlist-result:hover {
  background: var(--surface-2);
  border-color: rgba(124, 92, 252, 0.3);
}

.attach-result-poster {
  width: 48px;
  height: 72px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.attach-result-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.anime-title,
.playlist-title {
  color: var(--text-primary, #fff);
  font-size: 0.9rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anime-desc,
.playlist-anime-count {
  color: var(--text-tertiary, #777);
  font-size: 0.78rem;
}

.check-icon {
  color: var(--accent, #7c5cfc);
  font-size: 1.1rem;
  font-weight: 700;
  min-width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.anime-load-more,
.playlist-load-more {
  text-align: center;
  padding: 0.75rem;
}

.attach-load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--surface-3, #141414);
  border: 1px solid var(--border-default, #252525);
  color: var(--text-secondary, #aaa);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.attach-load-more-btn:hover {
  border-color: var(--accent, #7c5cfc);
  color: var(--text-primary, #fff);
}

.attach-load-more-btn.loading {
  opacity: 0.7;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.media-upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  margin: 0.75rem;
  background: var(--surface-3, #141414);
  border: 2px dashed var(--border-default, #252525);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.media-upload-area:hover {
  background: var(--surface-4, #1f1f1f);
  border-color: var(--border-strong, #333);
}

.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.upload-text {
  color: var(--text-secondary, #aaa);
  font-size: 0.95rem;
  font-weight: 500;
}

.upload-hint {
  color: var(--text-tertiary, #555);
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

.hidden-input {
  display: none;
}

.selected-media-preview {
  margin: 0.75rem;
  padding: 0.875rem;
  background: var(--surface-3);
  border: 1px solid rgba(34, 34, 34, 0.6);
  border-radius: 10px;
}

.selected-media-label {
  color: var(--accent, #7c5cfc);
  font-size: 0.82rem;
  margin-bottom: 0.625rem;
  font-weight: 500;
}

.media-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 0.5rem;
}

.media-preview-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: var(--surface-2, #0e0e0e);
  border: 1px solid var(--border-subtle, #1a1a1a);
  transition: all 0.2s;
}

.media-preview-item:hover {
  border-color: rgba(124, 92, 252, 0.4);
  transform: scale(1.05);
}

.media-preview-item img,
.media-preview-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.media-preview-item:hover img,
.media-preview-item:hover video {
  transform: scale(1.05);
}

.remove-thumb-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  border: none;
  width: 22px;
  height: 22px;
  min-width: 22px;
  min-height: 22px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 2;
}

.media-preview-item:hover .remove-thumb-btn {
  opacity: 1;
}

.remove-thumb-btn:hover {
  background: var(--danger, #ef4444);
  transform: scale(1.1);
}

.attach-modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.875rem 1.25rem;
  border-top: 1px solid var(--border-subtle, #1a1a1a);
  background: var(--surface-4, #1f1f1f);
}

.attach-modal-footer-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.attach-modal-footer-right {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.attach-modal-total {
  color: var(--text-tertiary, #777);
  font-size: 0.8rem;
}

.attach-modal-btn-cancel,
.attach-modal-btn-confirm {
  padding: 0.6rem 1.25rem;
  border-radius: var(--radius-md, 8px);
  font-size: var(--text-base, 0.875rem);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--border-default, #252525);
  background: var(--surface-5, #2a2a2a);
  color: var(--text-secondary, #aaa);
}

.attach-modal-btn-cancel:hover {
  border-color: var(--border-strong, #444);
  color: var(--text-primary, #fff);
}

.attach-modal-btn-confirm {
  background: linear-gradient(135deg, var(--accent, #7c5cfc) 0%, var(--accent-press, #6b4de8) 100%);
  border-color: transparent;
  color: var(--text-on-accent, #fff);
  box-shadow: var(--shadow-petal-sm, 0 2px 8px rgba(124, 92, 252, 0.3));
}

.attach-modal-btn-confirm:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow-sm, 0 4px 12px rgba(124, 92, 252, 0.4));
}
</style>
