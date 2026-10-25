<template>
  <div
    class="anime-card franchise-card"
    @click="handleClick"
    :class="{ 'has-live-cover': hasLiveCover }"
  >
    <div
      class="anime-poster"
      :class="{ 'poster-landscape': isLandscapePoster }"
      @mouseenter="startPosterRotation"
      @mouseleave="stopPosterRotation"
    >
      <div
        v-if="isLandscapePoster"
        class="poster-backdrop"
        :style="{ backgroundImage: posterBackdropStyle }"
        aria-hidden="true"
      ></div>
      <Transition name="poster-swap">
        <OptimizedImage
          v-if="currentPosterUrl"
          :key="currentPosterUrl"
          :src="currentPosterUrl"
          :alt="franchise.name"
          class="poster-image"
          :priority="priority"
          :width="180" :height="270"
          @error="handleImageError"
          @load="handlePosterLoad"
        />
        <div v-else class="poster-placeholder">
          <svg
            width="56"
            height="56"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.4"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="3" y="3" width="18" height="18" rx="3" />
            <path d="M3 15l4-4 5 5 3-3 6 6" />
            <circle cx="8.5" cy="8.5" r="1.5" />
          </svg>
        </div>
      </Transition>

      <button
        v-if="allPosters.length > 1"
        class="poster-nav-btn poster-nav-left"
        @click.stop="prevPoster"
        @mouseenter="stopPosterRotation"
        @mouseleave="startPosterRotation"
        type="button"
        aria-label="Предыдущий постер"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>

      <button
        v-if="allPosters.length > 1"
        class="poster-nav-btn poster-nav-right"
        @click.stop="nextPoster"
        @mouseenter="stopPosterRotation"
        @mouseleave="startPosterRotation"
        type="button"
        aria-label="Следующий постер"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      <div class="franchise-badge" title="Франшиза">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
        </svg>
        <span>Франшиза</span>
      </div>

      <div class="parts-badge">
        <span class="parts-count">{{ partsCount }}</span>
        <span class="parts-word">{{ partsWord }}</span>
      </div>

      <div class="poster-overlay"></div>

      <div class="hover-overlay" @click.stop="handleClick">
        <button class="play-btn" @click.stop="handleWatch" aria-label="Смотреть">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="6 4 20 12 6 20 6 4" />
          </svg>
        </button>
      </div>

      <div
        v-if="hasLiveCover"
        class="live-cover-indicator"
        @mouseenter="previewLiveCover"
        @mouseleave="stopLiveCoverPreview"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
      </div>

      <div v-if="showActions" class="card-actions">
        <!-- <button
          :class="['action-btn', 'favorite-btn', { 'is-active': isFavorite }]"
          @click.stop="handleFavoriteToggle"
          :title="isFavorite ? 'Убрать франшизу из избранного' : 'Добавить франшизу в избранное'"
          :disabled="loading || resolvingAction"
          type="button"
        >
          <svg
            v-if="!loading"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            :fill="isFavorite ? 'currentColor' : 'none'"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
          <span v-else class="loading-spinner"></span>
        </button> -->

        <button
          class="action-btn discuss-btn"
          @click.stop="handleDiscuss"
          title="Обсудить"
          type="button"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>

        <!-- <button
          class="action-btn playlist-btn"
          @click.stop="openPlaylist"
          :disabled="resolvingAction"
          title="Добавить первую часть в плейлист"
          type="button"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
          </svg>
        </button> -->

        <button
          class="action-btn reminder-btn"
          @click.stop="openReminder"
          :disabled="resolvingAction"
          title="Напомнить о выходе"
          type="button"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="13" r="8" />
            <path d="M12 9v4l2 2" />
            <path d="M19 3v2a3 3 0 0 1 3 3v2" />
            <path d="M5 5a3 3 0 0 1 3-3V3" />
          </svg>
        </button>
      </div>

      <div v-if="avgScore" class="score-badge">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
        <span>{{ avgScore }}</span>
      </div>
    </div>

    <div class="anime-info">
      <h3 class="anime-title" :title="franchise.name">{{ franchise.name }}</h3>

      <div class="anime-meta">
        <span v-if="totalHours" class="meta-item meta-hours">
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 6v6l4 2" />
          </svg>
          <span>{{ totalHours }} ч.</span>
        </span>
        <span v-if="yearRange" class="meta-dot"></span>
        <span v-if="yearRange" class="meta-item meta-year">{{ yearRange }}</span>
        <!-- <span v-if="durationText" class="meta-dot"></span> -->
        <!-- <span v-if="durationText" class="meta-item meta-duration">{{ durationText }}</span> -->
      </div>

      <GenreRow v-if="showGenres && allGenres.length" class="anime-genres" :genres="allGenres" />
    </div>

    <PlaylistSelectModal
      v-if="showPlaylistModal"
      :show="showPlaylistModal"
      :anime="franchiseAsAnime"
      :playlists="playlists"
      :is-loading="playlistsLoading"
      @close="showPlaylistModal = false"
      @save="onAddedToPlaylist"
      @create-playlist="handleCreatePlaylist"
    />

    <ReminderModal
      v-if="showReminderModal"
      :show="showReminderModal"
      :anime="reminderAnime"
      @close="showReminderModal = false"
      @save="handleReminderSave"
    />

    <Teleport to="body">
      <Transition name="psm-anim">
        <div
          v-if="showCreateModal"
          class="modal-overlay"
          @click.self="showCreateModal = false"
        >
          <div class="create-modal">
            <h3 class="create-modal-title">Новый плейлист</h3>
            <input
              v-model="newPlaylistTitle"
              placeholder="Название плейлиста"
              @keydown.enter="saveNewPlaylist"
              class="create-modal-input"
            />
            <label class="create-modal-label">
              <input type="checkbox" v-model="newPlaylistPublic" />
              Публичный
            </label>
            <div class="create-modal-actions">
              <button
                @click="showCreateModal = false"
                class="create-modal-btn create-modal-btn--cancel"
              >
                Отмена
              </button>
              <button
                @click="saveNewPlaylist"
                :disabled="!newPlaylistTitle.trim() || creatingPlaylist"
                class="create-modal-btn create-modal-btn--submit"
                :class="{ 'create-modal-btn--disabled': !newPlaylistTitle.trim() || creatingPlaylist }"
              >
                {{ creatingPlaylist ? "Создание..." : "Создать" }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { PlaylistSelectModal, ReminderModal } from "@/components/Modals";
import playlistsApi, { type Playlist } from "@/api/playlists";
import type { ReminderData } from "@/components/Modals/ReminderModal.vue";
import remindersApi from "@/api/reminders";
import { animeDiscussionsApi } from "@/api/animeDiscussions";
import apiClient, { getMediaUrl } from "@/api/client";
import { useToast } from "@/composables/useToast";
import { useFavoritesStore } from "@/stores/favorites";
import GenreRow from "@/components/Cards/GenreRow.vue";
import { useAnimeDiscussionNavigation } from "@/composables/useAnimeDiscussionNavigation";

interface FranchiseEntry {
  id: number;
  title_ru: string;
  title_en?: string;
  year?: number | null;
  score?: number | null;
  kind?: string;
  status?: string;
  episodes?: number | null;
  poster_url?: string;
  poster_image_url?: string;
  poster?: string | null;
  franchise_order?: number;
  total_duration?: number | string | null;
  episode_duration?: number | string | null;
}

interface FranchiseProps {
  id: number;
  name: string;
  slug?: string;
  description?: string;
  poster_url?: string | null;
  poster_image_url?: string | null;
  poster?: string | null;
  score?: number | null;
  year_start?: number | null;
  year_end?: number | null;
  parts_count?: number;
  year_range?: string;
  avg_score?: number | null;
  all_genres?: string[];
  genres?: Array<string | { name?: string; name_ru?: string; title?: string }> | string | null;
  all_posters?: string[];
  entries?: FranchiseEntry[];
  total_duration?: number | string | null;
  is_favorite?: boolean;
}

interface PlaylistSaveData {
  animeId: number;
  playlistIds: number[];
  note?: string;
}

interface Props {
  priority?: boolean;
  franchise: FranchiseProps;
  showActions?: boolean;
  hasLiveCover?: boolean;
  showGenres?: boolean;
  maxGenres?: number;
}

const props = withDefaults(defineProps<Props>(), {
  priority: false,
  showActions: true,
  hasLiveCover: false,
  showGenres: true,
  maxGenres: 3,
});

const emit = defineEmits<{
  click: [franchise: FranchiseProps];
  watch: [franchise: FranchiseProps];
  "favorite-toggle": [franchiseId: number, isFavorite: boolean];
}>();

const router = useRouter();
const toast = useToast();

const showPlaylistModal = ref(false);
const showReminderModal = ref(false);
const showCreateModal = ref(false);
const newPlaylistTitle = ref("");
const newPlaylistPublic = ref(false);
const creatingPlaylist = ref(false);
const playlists = ref<Playlist[]>([]);
const playlistsLoading = ref(false);
const resolvedEntries = ref<FranchiseEntry[] | null>(null);
const resolvingAction = ref(false);
const actionEntries = computed(() => resolvedEntries.value || (props.franchise.entries || []).filter(
  (entry): entry is FranchiseEntry => typeof entry === "object" && entry !== null && Number.isFinite(entry.id),
));
const actionEntryIds = computed(() => {
  if (resolvedEntries.value) return resolvedEntries.value.map((entry) => entry.id);
  return ((props.franchise.entries || []) as unknown[]).flatMap((entry) => {
    if (typeof entry === "number") return [entry];
    if (typeof entry === "object" && entry !== null && "id" in entry) {
      const id = Number((entry as { id: number }).id);
      return Number.isFinite(id) ? [id] : [];
    }
    return [];
  });
});
const firstPart = computed(() => actionEntries.value[0]);
const favorites = useFavoritesStore();
void favorites.ensureLoaded().catch(() => undefined);
const favoriteLoading = ref(false);
const favoriteOverride = ref<boolean | null>(null);
const loading = computed(() => favoriteLoading.value);
const isFavorite = computed(() => {
  if (favorites.loaded && actionEntryIds.value.length > 0) {
    return actionEntryIds.value.every((id) => favorites.isFavorite(id));
  }
  if (favoriteOverride.value !== null) return favoriteOverride.value;
  if (props.franchise.is_favorite === true) return true;
  return actionEntryIds.value.length > 0 && actionEntryIds.value.every((id) => favorites.isFavorite(id));
});
watch(() => props.franchise.id, () => {
  resolvedEntries.value = null;
  favoriteOverride.value = null;
  currentPosterIndex.value = 0;
  stopPosterRotation();
});

async function resolveParts() {
  if (actionEntries.value.length) return true;
  if (resolvingAction.value) return false;
  resolvingAction.value = true;
  try {
    const { data } = await apiClient.get(`/anime/franchises/${props.franchise.slug || props.franchise.id}/`);
    resolvedEntries.value = data.entries || [];
    if (!actionEntries.value.length) throw new Error('Части франшизы недоступны');
    return true;
  } catch {
    toast.error('Не удалось загрузить части франшизы. Попробуйте ещё раз.');
    return false;
  } finally { resolvingAction.value = false; }
}

async function openPlaylist() {
  if (await resolveParts()) showPlaylistModal.value = true;
}
async function openReminder() {
  if (await resolveParts()) showReminderModal.value = true;
}

const currentPosterIndex = ref(0);
let rotationTimer: ReturnType<typeof setInterval> | null = null;
const preloadedPosters = new Set<string>();

const partsCount = computed(() => {
  return props.franchise.parts_count || props.franchise.entries?.length || 0;
});

const partsWord = computed(() => {
  const count = partsCount.value;
  const lastTwo = count % 100;
  const lastOne = count % 10;

  if (lastTwo >= 11 && lastTwo <= 19) return "частей";
  if (lastOne === 1) return "часть";
  if (lastOne >= 2 && lastOne <= 4) return "части";
  return "частей";
});

const yearRange = computed(() => {
  if (props.franchise.year_range) return props.franchise.year_range;

  const start = props.franchise.year_start;
  const end = props.franchise.year_end;

  if (start && end) {
    if (start === end) return String(start);
    return `${start} – ${end}`;
  }
  if (start) return String(start);
  if (end) return String(end);
  return null;
});

const toMinutes = (value: unknown): number => {
  if (value == null) return 0;
  if (typeof value === "number" && isFinite(value)) return value;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return 0;

    const isoMatch = trimmed.match(/^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/i);
    if (isoMatch) {
      const h = parseInt(isoMatch[1] ?? "0", 10) || 0;
      const m = parseInt(isoMatch[2] ?? "0", 10) || 0;
      const s = parseInt(isoMatch[3] ?? "0", 10) || 0;
      return h * 60 + m + Math.round(s / 60);
    }

    if (/^\d+(:\d+){1,2}$/.test(trimmed)) {
      const rawParts = trimmed.split(":");
      const parts: number[] = rawParts.map((n) => {
        const parsed = parseInt(n, 10);
        return isFinite(parsed) ? parsed : 0;
      });
      if (parts.length === 3) {
        const h = parts[0] ?? 0;
        const m = parts[1] ?? 0;
        const s = parts[2] ?? 0;
        return h * 60 + m + Math.round(s / 60);
      }
      if (parts.length === 2) {
        const m = parts[0] ?? 0;
        const s = parts[1] ?? 0;
        return m * 60 + s;
      }
    }

    const num = Number(trimmed);
    if (isFinite(num)) return num;
  }
  return 0;
};

const entriesTotalMinutes = computed<number>(() => {
  const entries = props.franchise.entries || [];
  if (!entries.length) return 0;

  let totalMinutes = 0;

  for (const entry of entries) {
    const entryTotal = toMinutes(entry.total_duration);
    if (entryTotal > 0) {
      totalMinutes += entryTotal;
      continue;
    }

    const eps = toMinutes(entry.episodes);
    const dur = toMinutes(entry.episode_duration);
    if (eps > 0 && dur > 0) {
      totalMinutes += eps * dur;
    }
  }

  return totalMinutes;
});

const franchiseTotalMinutes = computed<number>(() => {
  const direct = toMinutes(props.franchise.total_duration);
  if (direct > 0) return direct;
  return entriesTotalMinutes.value;
});

const formatDurationText = (minutes: number): string => {
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  if (h > 0 && m > 0) return `${h} ч. ${m} мин.`;
  if (h > 0) return `${h} ч.`;
  return `${m} мин.`;
};

const totalHours = computed<string | null>(() => {
  const totalMinutes = franchiseTotalMinutes.value;
  if (totalMinutes <= 0) return null;
  const hours = Math.round((totalMinutes / 60) * 10) / 10;
  return hours > 0 ? String(hours).replace(".", ",") : null;
});

const durationText = computed<string | null>(() => {
  const totalMinutes = franchiseTotalMinutes.value;
  if (totalMinutes <= 0) return null;

  const text = formatDurationText(totalMinutes);
  const hours = Math.round(totalMinutes / 60);

  if (hours > 0 && text === `${hours} ч.`) {
    return null;
  }
  return text;
});

const avgScore = computed(() => {
  if (props.franchise.avg_score) return props.franchise.avg_score.toFixed(1);
  if (props.franchise.score) return props.franchise.score.toFixed(1);
  return null;
});

const allGenres = computed(() => {
  const raw = props.franchise.all_genres?.length
    ? props.franchise.all_genres
    : props.franchise.genres;
  const values = Array.isArray(raw) ? raw : typeof raw === "string" ? raw.split(",") : [];
  return [...new Set(values.map((genre) => {
    if (typeof genre === "string") return genre.trim();
    return String(genre?.name || genre?.name_ru || genre?.title || "").trim();
  }).filter(Boolean))];
});

const allPosters = computed(() => {
  if (props.franchise.all_posters && props.franchise.all_posters.length > 0) {
    return props.franchise.all_posters
      .map((p) => getMediaUrl(p))
      .filter((url): url is string => Boolean(url));
  }

  if (props.franchise.entries && props.franchise.entries.length > 0) {
    return [...props.franchise.entries]
      .sort((a, b) => (a.franchise_order || 0) - (b.franchise_order || 0))
      .map((e) => {
        if (e.poster && typeof e.poster === "string")
          return getMediaUrl(e.poster);
        if (e.poster_image_url) return getMediaUrl(e.poster_image_url);
        if (e.poster_url) return getMediaUrl(e.poster_url);
        return null;
      })
      .filter(Boolean) as string[];
  }

  return [];
});

const currentPosterUrl = computed(() => {
  if (allPosters.value.length > 0) {
    return allPosters.value[currentPosterIndex.value];
  }

  if (props.franchise.poster && typeof props.franchise.poster === "string") {
    return getMediaUrl(props.franchise.poster);
  }
  if (props.franchise.poster_image_url) {
    return getMediaUrl(props.franchise.poster_image_url);
  }
  if (props.franchise.poster_url) {
    return getMediaUrl(props.franchise.poster_url);
  }

  return null;
});

const preloadPoster = (url: string) => {
  if (!url || preloadedPosters.has(url)) return Promise.resolve();
  return new Promise<void>((resolve) => {
    const image = new Image();
    const done = () => {
      preloadedPosters.add(url);
      resolve();
    };
    image.onload = done;
    image.onerror = done;
    image.src = url;
    if (image.complete) done();
  });
};

const preloadPosterSequence = () => {
  for (const url of allPosters.value) void preloadPoster(url);
};

const showPoster = async (index: number) => {
  const url = allPosters.value[index];
  if (!url) return;
  await preloadPoster(url);
  currentPosterIndex.value = index;
};

const startPosterRotation = () => {
  if (allPosters.value.length <= 1) return;

  stopPosterRotation();
  preloadPosterSequence();
  rotationTimer = setInterval(() => {
    void nextPoster();
  }, 1800);
};

const stopPosterRotation = () => {
  if (rotationTimer) {
    clearInterval(rotationTimer);
    rotationTimer = null;
  }
};

const prevPoster = async () => {
  const index = currentPosterIndex.value === 0
    ? allPosters.value.length - 1
    : currentPosterIndex.value - 1;
  await showPoster(index);
};

const nextPoster = async () => {
  await showPoster((currentPosterIndex.value + 1) % allPosters.value.length);
};

const franchiseAsAnime = computed(() => ({
  id: firstPart.value?.id || 0,
  title_ru: firstPart.value?.title_ru || '',
  title_en: firstPart.value?.title_en || '',
  poster_url: firstPart.value?.poster_url,
  poster_image_url: firstPart.value?.poster_image_url,
  poster: firstPart.value?.poster || undefined,
}));

const reminderAnime = computed(() => ({
  id: actionEntries.value.at(-1)?.id || 0,
  title_ru: actionEntries.value.at(-1)?.title_ru || props.franchise.name,
  title_en: actionEntries.value.at(-1)?.title_en || props.franchise.name,
  poster_url: actionEntries.value.at(-1)?.poster_url || props.franchise.poster_url || props.franchise.poster_image_url || undefined,
  poster_image_url: actionEntries.value.at(-1)?.poster_image_url || props.franchise.poster_image_url || undefined,
}));

const loadPlaylists = async () => {
  playlistsLoading.value = true;
  try {
    const response = await playlistsApi.getMyPlaylists();
    playlists.value = response.data || [];
  } catch (error) {
    console.error("Error loading playlists:", error);
    playlists.value = [];
  } finally {
    playlistsLoading.value = false;
  }
};

watch(showPlaylistModal, (newVal) => {
  if (newVal) {
    loadPlaylists();
  }
});

const handleFavoriteToggle = async () => {
  if (!await resolveParts()) return;
  const next = !isFavorite.value;
  favoriteLoading.value = true;
  try {
    const { data } = await playlistsApi.setFranchiseFavorite(props.franchise.id, next);
    await favorites.commitIdsFavorite(data.anime_ids, data.is_favorite);
    favoriteOverride.value = data.is_favorite;
    emit("favorite-toggle", props.franchise.id, data.is_favorite);
    if (data.is_favorite) {
      toast.success("Добавлено в избранное");
    } else {
      toast.success("Удалено из избранного");
    }
  } catch {
    toast.error('Не удалось сохранить избранное. Попробуйте ещё раз.');
  } finally {
    favoriteLoading.value = false;
  }
};

const handleClick = () => {
  emit("click", props.franchise);
};

const handleWatch = () => {
  emit("watch", props.franchise);
};

const onAddedToPlaylist = async (data: PlaylistSaveData) => {
  try {
    const promises = data.playlistIds.map((pid: number) =>
      playlistsApi.addItemToPlaylist(pid, {
        anime: data.animeId,
        notes: data.note || "",
      }),
    );
    await Promise.all(promises);
    showPlaylistModal.value = false;
    toast.success("Часть франшизы добавлена в плейлист!");
  } catch (_error: unknown) {
    console.error("Ошибка добавления в плейлист:", _error);
    toast.error(
      _error instanceof Error
        ? _error.message
        : "Не удалось добавить в плейлист",
    );
  }
};

const handleCreatePlaylist = () => {
  showPlaylistModal.value = false;
  newPlaylistTitle.value = "";
  newPlaylistPublic.value = false;
  showCreateModal.value = true;
};

const saveNewPlaylist = async () => {
  if (!newPlaylistTitle.value.trim() || creatingPlaylist.value) return;
  creatingPlaylist.value = true;
  try {
    await playlistsApi.createPlaylist({
      title: newPlaylistTitle.value.trim(),
      visibility: newPlaylistPublic.value ? "public" : "private",
    });
    showCreateModal.value = false;
    toast.success("Плейлист создан!");
    await loadPlaylists();
    showPlaylistModal.value = true;
  } catch (_error: unknown) {
    toast.error(
      _error instanceof Error
        ? _error.message
        : "Не удалось создать плейлист",
    );
  } finally {
    creatingPlaylist.value = false;
  }
};

const { navigateToFranchiseDiscussion } = useAnimeDiscussionNavigation();

const handleDiscuss = async () => {
  try {
    await navigateToFranchiseDiscussion(props.franchise.id);
  } catch (_error: unknown) {
    console.error("Error handling discuss:", _error);
    toast.error(
      _error instanceof Error
        ? _error.message
        : "Не удалось открыть обсуждение"
    );
  }
};

const handleReminderSave = async (data: ReminderData) => {
  try {
    await remindersApi.createReminder({
      franchise_id: props.franchise.id,
      reminder_time: data.reminderTime.toISOString(),
      repeat_weekly: data.repeatWeekly || false,
      repeat_interval_days: data.repeatIntervalDays,
      end_date: data.endDate?.toISOString(),
      comment: data.comment || "",
      enable_sound: data.enableSound ?? true,
      enable_push: data.enablePush ?? true,
    });
    toast.success("Напоминание установлено!");
    showReminderModal.value = false;
  } catch (_error: unknown) {
    console.error("Ошибка сохранения напоминания:", _error);
    toast.error(
      _error instanceof Error
        ? _error.message
        : "Не удалось установить напоминание",
    );
  }
};

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  img.style.display = "none";
  const placeholder = img.nextElementSibling as HTMLElement;
  if (placeholder && placeholder.classList.contains("poster-placeholder")) {
    placeholder.style.display = "flex";
  }
};

const isLandscapePoster = ref(false);

const posterBackdropStyle = computed(() => {
  const url = currentPosterUrl.value;
  return url ? `url("${url}")` : "none";
});

const handlePosterLoad = (event: Event) => {
  const img = event.target as HTMLImageElement | null;
  if (!img || !img.naturalWidth || !img.naturalHeight) return;
  isLandscapePoster.value = img.naturalWidth > img.naturalHeight;
};

watch(currentPosterUrl, () => {
  isLandscapePoster.value = false;
});

const previewLiveCover = () => {};
const stopLiveCoverPreview = () => {};

onUnmounted(() => {
  stopPosterRotation();
});
</script>

<style>
.franchise-card {
  --card-radius: 18px;
  position: relative;
  background: var(--surface-3);
  border-radius: var(--card-radius);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 100%;
  height: 100%;
  contain: layout style paint;
  transition:
    transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.35s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
}

.franchise-card:hover {
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border-subtle));
  box-shadow:
    0 18px 40px -18px rgba(0, 0, 0, 0.65),
    0 0 0 1px color-mix(in srgb, var(--accent) 22%, transparent);
}
</style>

<style scoped>
.anime-poster {
  position: relative;
  width: 100%;
  padding-top: 150%;
  background: linear-gradient(160deg, var(--surface-4), var(--surface-3));
  overflow: hidden;
  isolation: isolate;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
  backface-visibility: hidden;
}

.poster-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}

.franchise-card:hover .poster-image {
  transform: scale(1.04);
}

.poster-landscape .poster-image {
  object-fit: contain;
}

.franchise-card:hover .poster-landscape .poster-image {
  transform: none;
}

.poster-backdrop {
  position: absolute;
  inset: 0;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  filter: blur(12px) brightness(0.6) saturate(1.15);
  transform: scale(1.15);
}

.poster-swap-enter-active,
.poster-swap-leave-active {
  transition: opacity 0.2s ease, filter 0.2s ease, transform 0.2s ease;
}

.poster-swap-leave-active { position: absolute; }
.poster-swap-enter-from { opacity: 0; filter: blur(1px); transform: scale(1.02); }
.poster-swap-leave-to { opacity: 0; filter: blur(1px); transform: scale(1.01); }

.poster-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  z-index: 1;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, var(--surface-4), var(--surface-3));
  color: var(--text-tertiary);
  opacity: 0.7;
}

.poster-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(
    to top,
    rgba(8, 8, 9, 0.92) 0%,
    rgba(8, 8, 9, 0.45) 38%,
    rgba(8, 8, 9, 0) 68%
  );
  pointer-events: none;
}

.hover-overlay {
  position: absolute;
  inset: -2px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  opacity: 0;
  transition: opacity 0.3s ease;
  will-change: opacity;
  z-index: 4;
  backface-visibility: hidden;
}

.franchise-card:hover .hover-overlay {
  opacity: 1;
}

.franchise-card:hover .anime-poster {
  background: #080809;
}

.poster-nav-btn {
  position: absolute;
  top: auto;
  bottom: 56px;
  transform: none;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 15, 18, 0.72);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 50%;
  cursor: pointer;
  z-index: 9;
  opacity: 0;
  transition: opacity 0.25s ease, transform 0.25s ease, background 0.2s ease,
    border-color 0.2s ease;
  padding: 0;
  line-height: 0;
}

.franchise-card:hover .poster-nav-btn {
  opacity: 1;
}

.poster-nav-btn:hover {
  background: var(--accent);
  border-color: transparent;
  transform: scale(1.08);
}

.poster-nav-left {
  left: 10px;
  right: auto;
}

.poster-nav-right {
  right: 10px;
  left: auto;
}

.franchise-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: color-mix(in srgb, #a855f7 85%, transparent);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #fff;
  border-radius: 9px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  z-index: 6;
  border: 1px solid rgba(255, 255, 255, 0.1);
  line-height: 1;
}

.franchise-badge svg {
  flex-shrink: 0;
}

.parts-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: var(--text-primary);
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  z-index: 6;
  border: 1px solid rgba(255, 255, 255, 0.06);
  line-height: 1;
}

.parts-count {
  font-size: 13px;
  font-weight: 800;
  color: #fff;
}

.parts-word {
  font-size: 10px;
  font-weight: 500;
  color: var(--text-secondary);
}

.play-btn {
  pointer-events: none;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transform: scale(0.8);
  opacity: 0;
  transition:
    transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.3s ease,
    background 0.2s ease,
    filter 0.3s ease;
  filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.45));
}

.franchise-card:hover .play-btn {
  pointer-events: auto;
  transform: scale(1);
  opacity: 1;
}

.play-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.06) !important;
  filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.5));
}

.play-btn svg {
  width: 26px;
  height: 26px;
  margin-left: 3px;
}

.live-cover-indicator {
  position: absolute;
  bottom: 10px;
  right: 10px;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: var(--accent);
  opacity: 0;
  transform: translateY(4px);
  transition: opacity 0.25s ease, transform 0.25s ease;
  z-index: 6;
}

.franchise-card:hover .live-cover-indicator {
  opacity: 1;
  transform: translateY(0);
}

.card-actions {
  position: absolute;
  top: 54px;
  left: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  opacity: 0;
  transform: translateX(-8px);
  transition: opacity 0.28s ease, transform 0.28s ease;
  z-index: 11;
}

.franchise-card:hover .card-actions {
  opacity: 1;
  transform: translateX(0);
}

.action-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 15, 18, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: #fff;
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: background 0.2s ease, transform 0.2s ease, color 0.2s ease,
    border-color 0.2s ease;
  padding: 0;
  line-height: 0;
  flex-shrink: 0;
}

.action-btn:hover {
  transform: scale(1.08);
  background: var(--accent);
  border-color: transparent;
  color: #fff;
}

.action-btn.is-active {
  color: #ff5c8a;
}

.action-btn.is-active:hover {
  background: #ff5c8a;
  color: #fff;
}

.score-badge {
  position: absolute;
  bottom: 10px;
  left: 10px;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 10px;
  color: #fbbf24;
  font-size: 12px;
  font-weight: 700;
  z-index: 6;
  border: 1px solid rgba(255, 255, 255, 0.06);
  line-height: 1;
}

.score-badge svg {
  width: 13px;
  height: 13px;
}

.anime-info {
  padding: 12px 13px 14px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  flex: 1;
  min-width: 0;
  height: 100%;
}

.anime-title {
  font-size: 14px;
  font-weight: 650;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.35;
  letter-spacing: -0.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  white-space: nowrap;
  overflow-wrap: normal;
  word-break: normal;
  min-height: 0;
}

.anime-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 16px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  line-height: 1;
}

.meta-hours svg {
  width: 13px;
  height: 13px;
  color: var(--accent);
  flex-shrink: 0;
}

.meta-year {
  color: var(--text-tertiary);
}

.meta-duration {
  color: var(--text-secondary);
}

.meta-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--text-tertiary);
  opacity: 0.6;
}

.anime-genres {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 5px;
  min-height: 22px;
  max-height: 22px;
  overflow: hidden;
}

.genre-tag {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--surface-4);
  padding: 4px 8px;
  border-radius: 7px;
  cursor: help;
  line-height: 1;
  letter-spacing: 0.01em;
  transition: background 0.2s ease, color 0.2s ease;
  white-space: nowrap;
}

.genre-tag:hover {
  background: color-mix(in srgb, #a855f7 18%, var(--surface-4));
  color: var(--text-primary);
}

.genre-more {
  flex: 0 0 auto;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--text-tertiary);
  padding: 4px 6px;
  line-height: 1;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .card-actions {
    opacity: 1 !important;
    transform: translateX(0) !important;
    gap: 6px;
    top: 50px;
  }

  .action-btn {
    width: 32px;
    height: 32px;
    border-radius: 10px;
  }

  .poster-nav-btn {
    opacity: 1;
    width: 32px;
    height: 32px;
    bottom: 52px;
  }
  .poster-nav-left {
    left: 6px;
  }

  .poster-nav-right {
    right: 6px;
  }

  .anime-info {
    padding: 10px 11px 12px;
    gap: 6px;
  }

  .anime-title {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .card-actions {
    top: 48px;
    left: 8px;
    gap: 5px;
  }

  .action-btn {
    width: 30px;
    height: 30px;
    border-radius: 9px;
  }

  .poster-nav-btn {
    width: 28px;
    height: 28px;
    bottom: 48px;
  }

  .poster-nav-left {
    left: 6px;
  }

  .poster-nav-right {
    right: 6px;
  }

  .score-badge {
    bottom: 8px;
    left: 8px;
    padding: 4px 8px;
    font-size: 11px;
  }

  .franchise-badge {
    top: 8px;
    left: 8px;
    font-size: 9.5px;
    padding: 4px 8px;
  }

  .parts-badge {
    top: 8px;
    right: 8px;
    font-size: 10px;
    padding: 4px 8px;
  }

  .live-cover-indicator {
    bottom: 8px;
    right: 8px;
    width: 28px;
    height: 28px;
  }
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  padding: 1rem;
}

.create-modal {
  background: var(--surface-2);
  border-radius: 1rem;
  max-width: 420px;
  width: 100%;
  padding: 1.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.create-modal-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.create-modal-input {
  height: 38px;
  padding: 0 12px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.create-modal-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.create-modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.create-modal-btn {
  height: 36px;
  padding: 0 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  border: 1px solid transparent;
  transition:
    background-color var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out),
    opacity var(--duration-base) var(--ease-out);
}

.create-modal-btn--cancel {
  background: var(--surface-4);
  color: var(--text-secondary);
  border-color: var(--border-subtle);
}

.create-modal-btn--cancel:hover {
  background: var(--surface-5);
  border-color: var(--border-default);
  color: var(--text-primary);
}

.create-modal-btn--submit {
  background: var(--accent);
  color: #fff;
  border: none;
  font-weight: 600;
}

.create-modal-btn--submit:hover:not(:disabled) {
  background: var(--accent-hover);
}

.create-modal-btn--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.franchise-card:focus-within .hover-overlay { opacity: 1; }
.franchise-card:focus-within .play-btn { opacity: 1; pointer-events: auto; }
@media (hover: none), (pointer: coarse) {
  .franchise-card .hover-overlay { opacity: 1; background: transparent; pointer-events: none; }
  .franchise-card .play-btn { opacity: 1; transform: none; pointer-events: auto; }
}

@media (max-width: 480px) {
  .franchise-badge span {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
  }
}
@media (pointer: coarse) {
  /* Poster navigation has its own column, clear of the four action buttons. */
  .poster-nav-btn { opacity: 1; width: 44px; height: 44px; left: auto; right: 8px; }
  .poster-nav-left { bottom: 102px; }
  .poster-nav-right { bottom: 52px; }
}
</style>
