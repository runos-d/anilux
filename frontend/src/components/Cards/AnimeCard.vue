<template>
  <div
    class="anime-card"
    @click="handleClick"
    :class="{ 'has-live-cover': hasLiveCover }"
  >
    <div class="anime-poster" :class="{ 'poster-landscape': isLandscapePoster }">
      <div
        v-if="isLandscapePoster"
        class="poster-backdrop"
        :style="{ backgroundImage: posterBackdropStyle }"
        aria-hidden="true"
      ></div>
      <OptimizedImage
        v-if="getPosterUrl() && !imageError"
        :src="getPosterUrl()"
        :alt="anime.title_ru || anime.title_en || ''"
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
        <button
          :class="['action-btn', 'favorite-btn', { 'is-active': isFavorite }]"
          @click.stop="handleFavoriteToggle"
          :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
          :disabled="loading"
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
        </button>

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

        <button
          class="action-btn playlist-btn"
          @click.stop="showPlaylistModal = true"
          title="Добавить в плейлист"
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
        </button>

        <button
          class="action-btn reminder-btn"
          @click.stop="showReminderModal = true"
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

      <div
        v-if="(showKindBadge && anime.type) || watchStatus"
        class="poster-top-right"
      >
        <!-- <div
          v-if="showKindBadge && anime.type"
          class="kind-badge"
          :class="`kind-${anime.type}`"
        >
          {{ getTypeLabel(anime.type) }}
        </div> -->

        <div
          v-if="watchStatus"
          class="status-pill"
          :style="{ background: statusColor }"
          :title="statusLabel"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <!-- watching: часы со стрелкой -->
            <template v-if="watchStatus === 'watching'">
              <circle cx="12" cy="12" r="10" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
              <path d="M12 5.8V12l4 2.4" fill="none" stroke="#2a1530" stroke-width="2.8" />
              <circle cx="12" cy="12" r="1.6" fill="#ff6fa5" stroke="#2a1530" stroke-width="1.4" />
              <path d="M5.4 9.2A7 7 0 0 1 9 5.6" fill="none" stroke="#8fd3ff" stroke-width="1.8" />
            </template>

            <!-- completed: галочка -->
            <template v-else-if="watchStatus === 'completed'">
              <circle cx="12" cy="12" r="10" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
              <path d="M7 12.4l3.4 3.4L17.4 8.6" fill="none" stroke="#2a1530" stroke-width="5" />
              <path d="M7 12.4l3.4 3.4L17.4 8.6" fill="none" stroke="#3ddc84" stroke-width="2.4" />
              <path d="M5.4 9.2A7 7 0 0 1 9 5.6" fill="none" stroke="#bff5d6" stroke-width="1.8" />
            </template>

            <!-- planned: календарь -->
            <template v-else-if="watchStatus === 'planned'">
              <rect x="3" y="4.5" width="18" height="17" rx="3" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
              <path d="M3.6 10h16.8V7.5a3 3 0 0 0-3-3H6.6a3 3 0 0 0-3 3z" fill="#ff6fa5" stroke="#2a1530" stroke-width="2" />
              <path d="M8 2.4v4M16 2.4v4" fill="none" stroke="#2a1530" stroke-width="2.8" />
              <circle cx="8.6" cy="14.6" r="1.5" fill="#2a1530" />
              <circle cx="12" cy="14.6" r="1.5" fill="#2a1530" />
              <circle cx="15.4" cy="14.6" r="1.5" fill="#ffd166" stroke="#2a1530" stroke-width="1" />
              <path d="M5.8 12.6v4" fill="none" stroke="#8fd3ff" stroke-width="1.6" />
            </template>

            <!-- dropped: крестик -->
            <template v-else-if="watchStatus === 'dropped'">
              <circle cx="12" cy="12" r="10" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
              <path d="M8.4 8.4l7.2 7.2M15.6 8.4l-7.2 7.2" fill="none" stroke="#2a1530" stroke-width="5" />
              <path d="M8.4 8.4l7.2 7.2M15.6 8.4l-7.2 7.2" fill="none" stroke="#ff4d6d" stroke-width="2.4" />
              <path d="M5.4 9.2A7 7 0 0 1 9 5.6" fill="none" stroke="#ffc2cc" stroke-width="1.8" />
            </template>

            <!-- onhold: пауза -->
            <template v-else-if="watchStatus === 'onhold'">
              <circle cx="12" cy="12" r="10" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
              <rect x="7.6" y="7.6" width="3.4" height="8.8" rx="1.1" fill="#ffb347" stroke="#2a1530" stroke-width="1.8" />
              <rect x="13" y="7.6" width="3.4" height="8.8" rx="1.1" fill="#ffb347" stroke="#2a1530" stroke-width="1.8" />
              <path d="M5.4 9.2A7 7 0 0 1 9 5.6" fill="none" stroke="#ffe0a8" stroke-width="1.8" />
            </template>
          </svg>
        </div>
      </div>

      <div v-if="anime.score" class="score-badge">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
        <span>{{ formattedScore }}</span>
      </div>

      <div v-if="viewersCount && viewersCount > 0" class="viewers-badge" title="Смотрят сейчас">
        <span class="viewers-dot"></span>
        <span>{{ viewersCount }} {{ viewersWord(viewersCount) }}</span>
      </div>

      <div
        v-if="showProgress && watchProgress > 0 && watchProgress < totalEpisodes"
        class="progress-bar"
      >
        <div
          class="progress-fill"
          :style="{ width: `${(watchProgress / totalEpisodes) * 100}%` }"
        ></div>
      </div>
    </div>

    <div class="anime-info">
      <h3 class="anime-title" :title="anime.title_ru || anime.title_en">{{ anime.title_ru || anime.title_en }}</h3>

      <div class="anime-meta">
        <span class="meta-item meta-release" v-if="anime.release_date">
          {{ formatReleaseDate(anime.release_date) }}
        </span>
        <span class="meta-item" v-else-if="anime.year">
          {{ anime.year }}
        </span>
        <span class="meta-dot" v-if="(anime.release_date || anime.year) && anime.episodes"></span>
        <span class="meta-item" v-if="anime.episodes">
          {{ anime.episodes }} эп.
        </span>
      </div>

      <GenreRow v-if="showGenres && hasGenres" class="anime-genres" :genres="genreNames" />

      <div v-if="showProgress" class="anime-progress" :aria-hidden="!hasVisibleProgress">
        <span v-if="showProgressText && hasVisibleProgress" class="progress-text">
          {{ watchProgress }}/{{ totalEpisodes }} эп.
        </span>
      </div>
    </div>

    <PlaylistSelectModal
      :show="showPlaylistModal"
      :anime="anime as any"
      :playlists="playlists"
      :is-loading="playlistsLoading"
      @close="showPlaylistModal = false"
      @save="onAddedToPlaylist"
      @create-playlist="handleCreatePlaylist"
    />

    <Teleport to="body">
      <Transition name="psm-anim">
        <div
          v-if="showCreateModal"
          class="modal-overlay create-modal-overlay"
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

    <ReminderModal
      :show="showReminderModal"
      :anime="anime as any"
      @close="showReminderModal = false"
      @save="handleReminderSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, getCurrentInstance } from "vue";
import { useRouter } from "vue-router";
import { PlaylistSelectModal, ReminderModal } from "@/components/Modals";
import playlistsApi from "@/api/playlists";
import type { Playlist } from "@/types";
import { animeDiscussionsApi } from "@/api/animeDiscussions";
import { getMediaUrl } from "@/api/client";
import { useToast } from "@/composables/useToast";
import remindersApi from "@/api/reminders";
import { useFavorite } from "@/composables/useFavorite";
import GenreRow from "@/components/Cards/GenreRow.vue";

interface Genre {
  id: number;
  name: string;
  slug: string;
  name_ru?: string;
  title?: string;
}

export interface AnimeCardProps {
  id: number;
  title_ru: string;
  title_en: string;
  title_jp?: string;
  description?: string;
  year?: number | null;
  release_date?: string | null;
  release_date_string?: string | null;
  status: string;
  episodes?: number | null;
  score?: number | null;
  poster_url?: string | null;
  poster_image_url?: string | null;
  poster_file?: string | null;
  created_at?: string;
  type?: string;
  genres?: Genre[] | string[] | string | null;
  poster?: string | null;
  slug?: string;
}

interface Props {
  priority?: boolean;
  anime: AnimeCardProps;
  showActions?: boolean;
  hasLiveCover?: boolean;
  watchStatus?: "watching" | "completed" | "planned" | "dropped" | "onhold";
  watchProgress?: number;
  totalEpisodes?: number;
  showGenres?: boolean;
  showProgress?: boolean;
  showProgressText?: boolean;
  maxGenres?: number;
  showKindBadge?: boolean;
  viewersCount?: number;
}

const props = withDefaults(defineProps<Props>(), {
  priority: false,
  showActions: true,
  hasLiveCover: false,
  watchProgress: 0,
  showGenres: true,
  showProgress: true,
  showProgressText: true,
  maxGenres: 3,
  showKindBadge: false,
});

const emit = defineEmits<{
  click: [anime: AnimeCardProps];
  watch: [anime: AnimeCardProps];
  "favorite-toggle": [animeId: number, isFavorite: boolean];
  "set-reminder": [animeId: number];
}>();

const router = useRouter();
const instance = getCurrentInstance();
const toast = useToast();

const showPlaylistModal = ref(false);
const showReminderModal = ref(false);
const showCreateModal = ref(false);
const newPlaylistTitle = ref("");
const newPlaylistPublic = ref(false);
const creatingPlaylist = ref(false);
const playlists = ref<Playlist[]>([]);
const playlistsLoading = ref(false);

const { isFavorite, loading, error, checkStatus, toggleFavorite } =
  useFavorite(() => props.anime.id);

const STATUS_META: Record<
  NonNullable<Props["watchStatus"]>,
  { color: string; label: string }
> = {
  watching: { color: "var(--accent)", label: "В процессе" },
  completed: { color: "#22c55e", label: "Просмотрено" },
  planned: { color: "#a78bfa", label: "Запланировано" },
  onhold: { color: "#f59e0b", label: "Отложено" },
  dropped: { color: "#ef4444", label: "Брошено" },
};

const statusColor = computed(() => {
  if (!props.watchStatus) return "transparent";
  return STATUS_META[props.watchStatus]?.color ?? "transparent";
});

const statusLabel = computed(() => {
  if (!props.watchStatus) return "";
  return STATUS_META[props.watchStatus]?.label ?? "";
});

const normalizedGenres = computed(() => {
  const genres = props.anime.genres;

  if (!genres) return [];
  const values = Array.isArray(genres) ? genres : String(genres).split(",");
  const seen = new Set<string>();
  return values.flatMap((genre, index) => {
    const objectGenre = typeof genre === "object" && genre !== null
      ? genre as Partial<Genre> & { russian?: string }
      : null;
    const name = String(typeof genre === "string"
      ? genre
      : objectGenre?.name || objectGenre?.name_ru || objectGenre?.title || objectGenre?.russian || "").trim();
    const key = name.toLocaleLowerCase();
    if (!name || seen.has(key)) return [];
    seen.add(key);
    return [{ id: objectGenre?.id ?? index, name, slug: objectGenre?.slug || "" }];
  });
});

const hasGenres = computed(() => normalizedGenres.value.length > 0);
const hasVisibleProgress = computed(() =>
  props.watchProgress > 0 && props.watchProgress < (props.totalEpisodes || 0),
);
const genreNames = computed(() => normalizedGenres.value.map((genre) => getGenreName(genre)));

const viewersWord = (count: number) => {
  const mod100 = count % 100;
  const mod10 = count % 10;
  if (mod100 >= 11 && mod100 <= 14) return "зрителей";
  if (mod10 === 1) return "зритель";
  if (mod10 >= 2 && mod10 <= 4) return "зрителя";
  return "зрителей";
};

const getGenreName = (genre: unknown): string => {
  if (!genre) return "";
  if (typeof genre === "string") return genre;
  if (typeof genre === "object" && genre !== null && "name" in genre) {
    return (genre as { name: string }).name;
  }
  return String(genre);
};

const loadPlaylists = async () => {
  playlistsLoading.value = true;
  try {
    const response = await playlistsApi.getMyPlaylists();
    playlists.value = (response.data || []) as unknown as Playlist[];
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

const formattedScore = computed(() => {
  if (props.anime.score) {
    return props.anime.score.toFixed(1);
  }
  return "";
});

const totalEpisodes = computed(() => {
  return props.totalEpisodes || props.anime.episodes || 0;
});

const getApiError = (error: unknown): string => {
  const detail = (
    error as { response?: { data?: { detail?: string } } }
  )?.response?.data?.detail;
  return detail || (error as Error)?.message || "";
};

const handleFavoriteToggle = async () => {
  await toggleFavorite();
  if (!error.value) {
    emit("favorite-toggle", props.anime.id, isFavorite.value);
    if (isFavorite.value) {
      toast.success("Добавлено в избранное");
    } else {
      toast.success("Удалено из избранного");
    }
  } else {
    toast.error(error.value);
  }
};

const handleClick = () => {
  emit("click", props.anime);
  if (!instance?.vnode.props?.onClick) {
    void router.push(`/anime/${props.anime.slug || props.anime.id}`);
  }
};

const handleWatch = () => {
  emit('watch', props.anime);
  if (!instance?.vnode.props?.onWatch) {
    void router.push(`/anime/${props.anime.slug || props.anime.id}/watch`);
  }
};

const onAddedToPlaylist = async (data: {
  animeId: number;
  playlistIds: number[];
  note?: string;
}) => {
  try {
    const promises = data.playlistIds.map((pid: number) =>
      playlistsApi.addItemToPlaylist(pid, {
        anime: data.animeId,
        notes: data.note || "",
      })
    );
    await Promise.all(promises);
    showPlaylistModal.value = false;
    toast.success("Аниме добавлено в плейлист!");
  } catch (error) {
    console.error("Ошибка добавления в плейлист:", error);
    toast.error(getApiError(error) || "Не удалось добавить в плейлист");
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
  } catch (error) {
    toast.error(getApiError(error) || "Не удалось создать плейлист");
  } finally {
    creatingPlaylist.value = false;
  }
};

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    ongoing: "Онгоинг",
    finished: "Завершён",
    announced: "Анонсирован",
    released: "Завершён",
  };
  return map[status] || status;
};

const getTypeLabel = (type?: string) => {
  const labels: Record<string, string> = {
    tv: "TV",
    movie: "Фильм",
    ova: "OVA",
    ona: "ONA",
    special: "Спешл",
  };
  return labels[type!.toLowerCase()] || type;
};

const handleReminderSave = async (data: {
  reminderTime: Date;
  repeatWeekly: boolean;
  repeatIntervalDays?: number;
  endDate?: Date;
  comment?: string;
  enableSound?: boolean;
  enablePush?: boolean;
}) => {
  try {
    await remindersApi.createReminder({
      anime_id: props.anime.id,
      reminder_time: new Date(data.reminderTime).toISOString(),
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
        : "Не удалось установить напоминание"
    );
  }
};

const handleDiscuss = async () => {
  try {
    let discussionGroup;
    try {
      discussionGroup = await animeDiscussionsApi.getDiscussionGroup(
        props.anime.id
      );
    } catch (_error: unknown) {
      if (
        _error instanceof Error &&
        (_error as unknown as { response?: { status?: number } }).response
          ?.status === 404
      ) {
        discussionGroup = await animeDiscussionsApi.createDiscussionGroup(
          props.anime.id
        );
      } else {
        throw _error;
      }
    }

    if (!discussionGroup.user_joined) {
      discussionGroup = await animeDiscussionsApi.joinDiscussionGroup(
        props.anime.id
      );
    }

    router.push(`/chats/${discussionGroup.id}`);
  } catch (_error: unknown) {
    console.error("Error handling discuss:", _error);
    toast.error(
      _error instanceof Error
        ? _error.message
        : "Не удалось открыть обсуждение"
    );
  }
};

const getStatusClass = (status: string) => {
  const map: Record<string, string> = {
    ongoing: "status-ongoing",
    finished: "status-finished",
    announced: "status-announced",
    released: "status-released",
  };
  return map[status] || "";
};

const formatReleaseDate = (dateStr: string | null) => {
  if (!dateStr) return "";
  try {
    const date = new Date(dateStr);
    const day = date.getDate();
    const month = date.toLocaleString("ru", { month: "short" });
    const year = date.getFullYear();
    return `${day} ${month} ${year}`;
  } catch {
    return dateStr;
  }
};

const getPosterUrl = (): string | undefined => {
  const posterImage = props.anime.poster_image_url;
  const posterUrl = props.anime.poster_url;
  const posterFile = props.anime.poster_file;
  const poster = props.anime.poster;

  if (poster) {
    const url = getMediaUrl(poster);
    if (url) return url;
  }
  if (posterFile) {
    const url = getMediaUrl(posterFile);
    if (url) return url;
  }
  if (posterImage) {
    const url = getMediaUrl(posterImage);
    if (url) return url;
  }
  if (posterUrl) {
    const url = getMediaUrl(posterUrl);
    if (url) return url;
  }
  return undefined;
};

const imageError = ref(false);

const handleImageError = () => {
  imageError.value = true;
};

const isLandscapePoster = ref(false);

const posterBackdropStyle = computed(() => {
  const url = getPosterUrl();
  return url ? `url("${url}")` : "none";
});

const handlePosterLoad = (event: Event) => {
  const img = event.target as HTMLImageElement | null;
  if (!img || !img.naturalWidth || !img.naturalHeight) return;
  isLandscapePoster.value = img.naturalWidth > img.naturalHeight;
};

watch(() => getPosterUrl(), () => {
  isLandscapePoster.value = false;
});

const previewLiveCover = () => {};

const stopLiveCoverPreview = () => {};

checkStatus();
</script>

<style>
.anime-card {
  --card-radius: 18px;
  --card-pad: 12px;
  position: relative;
  background: var(--surface-3);
  border-radius: var(--card-radius);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
  contain: layout style paint;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 100%;
  height: 100%;
  transition:
    transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.35s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
}

.anime-card:hover {
  transform: translateY(-4px);
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
  top: 0px;
  left: 0px;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.anime-card:hover .poster-image {
  transform: scale(1.02);
}

.poster-landscape .poster-image {
  object-fit: contain;
}

.anime-card:hover .poster-landscape .poster-image {
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

.hover-overlay {
  background: linear-gradient(
    to top,
    rgba(8, 8, 9, 0.42) 0%,
    rgba(8, 8, 9, 0.25) 38%,
    rgba(8, 8, 9, 0) 68%
  );
}
.anime-poster {
  background: linear-gradient(
    to top,
    rgba(8, 8, 9, 0.42) 0%,
    rgba(8, 8, 9, 0.25) 38%,
    rgba(8, 8, 9, 0) 68%
  );
}

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
  z-index: 2;
}

.hover-overlay {
  position: absolute;
  inset: -1px;
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

.anime-card:hover .hover-overlay {
  opacity: 1;
  background: rgba(0, 0, 0, 0.55);
}

.anime-card:hover .anime-poster {
  background: #080809;
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

.anime-card:hover .play-btn {
  pointer-events: auto;
  transform: scale(1);
  opacity: 1;
}

.play-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.3) !important;
  filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.5));
}

.anime-card:focus-within .hover-overlay { opacity: 1; }
.anime-card:focus-within .play-btn { opacity: 1; pointer-events: auto; }
@media (hover: none), (pointer: coarse) {
  .anime-card .hover-overlay { opacity: 1; background: transparent; pointer-events: none; }
  .anime-card .play-btn { opacity: 1; transform: none; pointer-events: auto; }
}

.play-btn svg {
  width: 26px;
  height: 26px;
  margin-left: 3px;
}

.live-cover-indicator {
  position: absolute;
  top: 10px;
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
  transform: translateY(-4px);
  transition: opacity 0.25s ease, transform 0.25s ease;
  z-index: 6;
}

.anime-card:hover .live-cover-indicator {
  opacity: 1;
  transform: translateY(0);
}

.card-actions {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  opacity: 1;
  transform: translateX(-8px);
  visibility: hidden;
  transition: opacity 0.28s ease, transform 0.28s ease;
  z-index: 10;
  pointer-events: none;
}

.anime-card:hover .card-actions {
  transform: translateX(0);
  visibility: visible;
  pointer-events: auto;
  transition: transform 0.28s ease, visibility 0s;
}

.action-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f0f12b3;
  color: #fff;
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: background 0.2s ease, transform 0.2s ease, color 0.2s ease,
  border-color 0.2s ease;
  padding: 0;
  backdrop-filter: blur(10px);
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

.poster-top-right {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 6px;
  z-index: 6;
}

.status-pill {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  z-index: 6;
  border: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
}

.kind-badge {
  padding: 4px 9px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  background: rgba(0, 0, 0, 0.7);
  color: var(--text-secondary);
  border: 1px solid rgba(255, 255, 255, 0.06);
  line-height: 1;
  display: inline-flex;
  align-items: center;
}

.kind-badge.kind-tv { background: var(--accent); color: #fff; border-color: transparent; }
.kind-badge.kind-movie { background: #f59e0b; color: #1a1206; border-color: transparent; }
.kind-badge.kind-ova { background: #22c55e; color: #052012; border-color: transparent; }
.kind-badge.kind-ona { background: #06b6d4; color: #04212a; border-color: transparent; }
.kind-badge.kind-special { background: #a855f7; color: #fff; border-color: transparent; }
.kind-badge.kind-music { background: #ec4899; color: #fff; border-color: transparent; }

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

.viewers-badge {
  position: absolute;
  right: 10px;
  bottom: 10px;
  z-index: 7;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 9px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  background: rgba(7, 18, 12, 0.78);
  color: #dcfce7;
  font-size: 11px;
  font-weight: 650;
  line-height: 1;
  backdrop-filter: blur(8px);
}

.viewers-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.18);
}

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(0, 0, 0, 0.45);
  z-index: 7;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 60%, #fff));
  border-radius: 0 4px 4px 0;
  transition: width 0.4s ease;
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
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  line-height: 1;
}

.meta-release {
  color: var(--text-tertiary);
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
  background: color-mix(in srgb, var(--accent) 18%, var(--surface-4));
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

.anime-progress {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-top: auto;
  min-height: 14px;
}

.anime-progress svg {
  width: 13px;
  height: 13px;
  color: var(--accent);
}

.progress-text {
  font-size: 11.5px;
}

@media (max-width: 767px) {
  .card-actions {
    opacity: 1 !important;
    transform: translateX(0) !important;
    gap: 6px;
  }

  .action-btn {
    width: 32px;
    height: 32px;
    border-radius: 10px;
  }

  .anime-card {
    width: auto !important;
    max-width: 100% !important;
  }

  .anime-poster {
    width: 100% !important;
    height: auto !important;
  }

  .anime-info {
    padding: 10px 11px 12px;
    gap: 6px;
  }

  .anime-title {
    font-size: 13px;
  }

  .status-pill {
    width: 28px;
    height: 28px;
    border-radius: 9px;
  }
}

@media (max-width: 480px) {
  .card-actions {
    top: 8px;
    left: 8px;
    gap: 5px;
  }

  .action-btn {
    width: 30px;
    height: 30px;
    border-radius: 9px;
  }

  .score-badge {
    bottom: 8px;
    left: 8px;
    padding: 4px 8px;
    font-size: 11px;
  }

  .poster-top-right {
    top: 8px;
    right: 8px;
    gap: 5px;
  }

  .status-pill {
    width: 26px;
    height: 26px;
    border-radius: 8px;
  }

  .kind-badge {
    font-size: 9px;
    padding: 3px 7px;
  }
}

.create-modal-overlay {
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

.create-modal-btn--submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

<style>
@import './catalogCardGeometry.css';
</style>
