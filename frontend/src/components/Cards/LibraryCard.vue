<template>
  <div class="lib-card" :class="`st-${item.status}`">
    <div
      class="poster-wrap"
      :class="{ 'poster-landscape': isLandscapePoster }"
      @click="goAnime"
    >
      <div
        v-if="isLandscapePoster"
        class="poster-backdrop"
        :style="{ backgroundImage: posterBackdropStyle }"
        aria-hidden="true"
      ></div>
      <OptimizedImage
        v-if="posterUrl && !posterFailed"
        :src="posterUrl"
        :alt="title"
        class="poster-img"
        @error="posterFailed = true"
        @load="handlePosterLoad"
      />
      <div v-else class="poster-ph">
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

      <div class="hover-overlay" @click.stop="goAnime">
        <button class="play-btn" @click.stop="watchNow" :title="playLabel" aria-label="Смотреть">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="6 4 20 12 6 20 6 4" />
          </svg>
        </button>
      </div>

      <div v-if="showActions" class="card-actions">
        <button
          :class="['action-btn', 'favorite-btn', { 'is-active': isFavorite }]"
          @click.stop="toggleFav"
          :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
          type="button"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            :fill="isFavorite ? 'currentColor' : 'none'"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
            />
          </svg>
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

        <button
          class="action-btn menu-btn"
          @click.stop="openMenu"
          title="Ещё"
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
            <circle cx="12" cy="12" r="1.6" />
            <circle cx="5" cy="12" r="1.6" />
            <circle cx="19" cy="12" r="1.6" />
          </svg>
        </button>
      </div>

      <div
        class="status-pill"
        :style="{ background: STATUS[item.status]?.color }"
        :title="STATUS[item.status]?.label"
      >
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <!-- started: часы -->
        <template v-if="item.status === 'started'">
          <circle cx="12" cy="12" r="10" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
          <path d="M12 5.8V12l4 2.4" fill="none" stroke="#2a1530" stroke-width="2.8" />
          <circle cx="12" cy="12" r="1.6" fill="#ff6fa5" stroke="#2a1530" stroke-width="1.4" />
          <path d="M5.4 9.2A7 7 0 0 1 9 5.6" fill="none" stroke="#8fd3ff" stroke-width="1.8" />
        </template>

        <!-- completed: галочка -->
        <template v-else-if="item.status === 'completed'">
          <circle cx="12" cy="12" r="10" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
          <path d="M7 12.4l3.4 3.4L17.4 8.6" fill="none" stroke="#2a1530" stroke-width="5" />
          <path d="M7 12.4l3.4 3.4L17.4 8.6" fill="none" stroke="#3ddc84" stroke-width="2.4" />
          <path d="M5.4 9.2A7 7 0 0 1 9 5.6" fill="none" stroke="#bff5d6" stroke-width="1.8" />
        </template>

        <!-- planned: календарь -->
        <template v-else-if="item.status === 'planned'">
          <rect x="3" y="4.5" width="18" height="17" rx="3" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
          <path d="M3.6 10h16.8V7.5a3 3 0 0 0-3-3H6.6a3 3 0 0 0-3 3z" fill="#ff6fa5" stroke="#2a1530" stroke-width="2" />
          <path d="M8 2.4v4M16 2.4v4" fill="none" stroke="#2a1530" stroke-width="2.8" />
          <circle cx="8.6" cy="14.6" r="1.5" fill="#2a1530" />
          <circle cx="12" cy="14.6" r="1.5" fill="#2a1530" />
          <circle cx="15.4" cy="14.6" r="1.5" fill="#ffd166" stroke="#2a1530" stroke-width="1" />
          <path d="M5.8 12.6v4" fill="none" stroke="#8fd3ff" stroke-width="1.6" />
        </template>

        <!-- dropped: крестик -->
        <template v-else-if="item.status === 'dropped'">
          <circle cx="12" cy="12" r="10" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
          <path d="M8.4 8.4l7.2 7.2M15.6 8.4l-7.2 7.2" fill="none" stroke="#2a1530" stroke-width="5" />
          <path d="M8.4 8.4l7.2 7.2M15.6 8.4l-7.2 7.2" fill="none" stroke="#ff4d6d" stroke-width="2.4" />
          <path d="M5.4 9.2A7 7 0 0 1 9 5.6" fill="none" stroke="#ffc2cc" stroke-width="1.8" />
        </template>

        <!-- on_hold: пауза -->
        <template v-else-if="item.status === 'on_hold'">
          <circle cx="12" cy="12" r="10" fill="#fff" stroke="#2a1530" stroke-width="2.6" />
          <rect x="7.6" y="7.6" width="3.4" height="8.8" rx="1.1" fill="#ffb347" stroke="#2a1530" stroke-width="1.8" />
          <rect x="13" y="7.6" width="3.4" height="8.8" rx="1.1" fill="#ffb347" stroke="#2a1530" stroke-width="1.8" />
          <path d="M5.4 9.2A7 7 0 0 1 9 5.6" fill="none" stroke="#ffe0a8" stroke-width="1.8" />
        </template>
      </svg>
      </div>

      <div v-if="showProgress" class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: item.progress_percentage + '%' }"
        ></div>
      </div>
    </div>

    <div class="anime-info">
      <h3 class="anime-title" @click="goAnime" :title="title">{{ title }}</h3>

      <div v-if="animeYear || totalEpisodes" class="anime-meta">
        <span v-if="animeYear" class="meta-item">{{ animeYear }}</span>
        <span v-if="animeYear && totalEpisodes" class="meta-dot"></span>
        <span v-if="totalEpisodes" class="meta-item">{{ totalEpisodes }} эп.</span>
      </div>

      <div v-if="showProgress || item.rating" class="anime-meta anime-state-meta">
        <span v-if="showProgress" class="meta-item">
          Просмотрено: {{ item.episodes_watched || 0 }}/{{ totalEpisodes || "?" }}
        </span>
        <span v-if="item.rating" class="meta-item meta-rating">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <polygon
              points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
            />
          </svg>
          {{ item.rating }}/10
        </span>

      </div>

      <GenreRow v-if="hasGenres" class="anime-genres" :genres="animeGenres.map(genre => genre.name)" />

      <span v-else-if="!hasGenres" class="date-lbl">{{ dateLabel }}</span>
    </div>

    <Teleport to="body">
      <div v-if="menuOpen" class="ctx-back" @click="menuOpen = false"></div>
      <div v-if="menuOpen" class="ctx-menu" :style="menuPos">
        <button class="ctx-item" @click="goAnime">
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"
            />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
          Страница аниме
        </button>
        <button class="ctx-item" @click="watchNow">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
          Смотреть
        </button>

        <div class="ctx-sep"></div>

        <button
          v-for="s in STATUS_LIST"
          :key="s.key"
          class="ctx-item"
          :class="{ active: item.status === s.key }"
          @click="setStatus(s.key)"
        >
          <SakuraIcon v-if="isIconName(s.icon)" :name="s.icon" :size="13" />
          <span v-else>{{ s.icon }}</span>
          {{ s.label }}
        </button>

        <div class="ctx-sep"></div>

        <button class="ctx-item" @click="toggleFav">
          <SakuraIcon :name="isFavorite ? 'heart' : 'star'" :size="13" />
          {{ isFavorite ? "Убрать из избранного" : "В избранное" }}
        </button>
        <button class="ctx-item" @click="openEdit">
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 1 2-2v-7"
            />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          Редактировать
        </button>
        <button class="ctx-item danger" @click="deleteItem">
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            <path d="M10 11v6M14 11v6M9 6V4h6v2" />
          </svg>
          Удалить
        </button>
      </div>
    </Teleport>

    <PlaylistSelectModal
      :show="showPlaylistModal"
      :anime="animeForModal"
      :playlists="playlists"
      :is-loading="playlistsLoading"
      @close="showPlaylistModal = false"
      @save="onAddedToPlaylist"
      @create-playlist="handleCreatePlaylist"
    />

    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showCreateModal"
          class="create-playlist-backdrop"
          @click.self="showCreateModal = false"
        >
          <div class="create-playlist-dialog">
            <h3 class="create-playlist-title">Новый плейлист</h3>
            <input
              v-model="newPlaylistTitle"
              placeholder="Название плейлиста"
              @keydown.enter="saveNewPlaylist"
              autofocus
              class="create-playlist-input"
            />
            <label class="create-playlist-checkbox">
              <input type="checkbox" v-model="newPlaylistPublic" />
              Публичный
            </label>
            <div class="create-playlist-actions">
              <button
                type="button"
                @click="showCreateModal = false"
                class="create-playlist-btn create-playlist-cancel"
              >
                Отмена
              </button>
              <button
                type="button"
                @click="saveNewPlaylist"
                :disabled="!newPlaylistTitle.trim() || creatingPlaylist"
                class="create-playlist-btn create-playlist-submit"
                :class="{ disabled: !newPlaylistTitle.trim() || creatingPlaylist }"
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
      :anime="animeForModal"
      @close="showReminderModal = false"
      @save="handleReminderSave"
    />

    <Teleport to="body">
      <div v-if="editOpen" class="modal-back" @click.self="editOpen = false">
        <div class="edit-modal">
          <div class="em-header">
            <div>
              <h3 class="em-title">{{ title }}</h3>
              <p class="em-sub">Редактировать запись</p>
            </div>
            <button class="em-close" @click="editOpen = false">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div class="em-body">
            <div class="em-field">
              <label class="em-label">Статус</label>
              <div class="status-grid">
                <button
                  v-for="s in STATUS_LIST"
                  :key="s.key"
                  class="sg-opt"
                  :class="{ sel: editForm.status === s.key }"
                  @click="editForm.status = s.key"
                >
                  <SakuraIcon
                    v-if="isIconName(s.icon)"
                    :name="s.icon"
                    :size="18"
                  />
                  <span v-else class="sg-icon">{{ s.icon }}</span>
                  <span class="sg-lbl">{{ s.label }}</span>
                </button>
              </div>
            </div>
            <div
              v-if="
                editForm.status === 'started' || editForm.status === 'on_hold'
              "
              class="em-field"
            >
              <label class="em-label">
                Просмотрено

              </label>
              <div class="ep-row">
                <button
                  class="ep-adj"
                  :disabled="editForm.episodes_watched <= 0"
                  @click="setEditedEpisodes(editForm.episodes_watched - 1)"
                >
                  <SakuraIcon name="minus" :size="16" />
                </button>
                <input
                  type="number"
                  class="ep-in"
                  v-model.number="editForm.episodes_watched"
                  :min="0"
                  :max="item.anime_episodes_count || 9999"
                  @input="episodesWatchedEdited = true"
                  @blur="normalizeEditedEpisodes"
                />
                <button
                  class="ep-adj"
                  :disabled="
                    editForm.episodes_watched >= (item.anime_episodes_count || 9999)
                  "
                  @click="setEditedEpisodes(editForm.episodes_watched + 1)"
                >
                  <SakuraIcon name="plus" :size="16" />
                </button>
              </div>
            </div>

            <div class="em-field">
              <label class="em-label">Оценка</label>
              <div class="stars-row">
                <button
                  v-for="n in 10"
                  :key="n"
                  class="star-b"
                  @mouseenter="hoverR = n"
                  @mouseleave="hoverR = 0"
                  @click="editForm.rating = editForm.rating === n ? null : n"
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    :fill="
                      n <= (hoverR || editForm.rating || 0)
                        ? 'var(--warning)'
                        : 'none'
                    "
                    stroke="var(--warning)"
                    stroke-width="1.5"
                  >
                    <polygon
                      points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
                    />
                  </svg>
                </button>
                <span v-if="editForm.rating" class="rating-disp"
                  >{{ editForm.rating }}/10</span
                >
                <button
                  v-if="editForm.rating"
                  class="clear-r"
                  @click="editForm.rating = null"
                 aria-label="Закрыть">
                  <SakuraIcon name="x" :size="16" />
                </button>
              </div>
            </div>

            <div class="em-field">
              <label
                class="em-toggle-row"
                @click="editForm.is_favorite = !editForm.is_favorite"
              >
                <span class="em-label em-label-no-margin"
                  ><SakuraIcon name="star" /> В избранном</span
                >
                <div class="toggle" :class="{ on: editForm.is_favorite }">
                  <div class="toggle-thumb"></div>
                </div>
              </label>
            </div>

            <div class="em-field">
              <label class="em-label">Заметка</label>
              <textarea
                class="em-note"
                v-model="editForm.notes"
                placeholder="Мысли об аниме..."
                rows="3"
              ></textarea>
            </div>
          </div>

          <div class="em-footer">
            <button class="em-cancel" @click="editOpen = false">Отмена</button>
            <button class="em-save" :disabled="saving" @click="saveEdit">
              <svg
                v-if="saving"
                class="spin-ic"
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
              >
                <path
                  d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"
                />
              </svg>
              {{ saving ? "Сохранение..." : "Сохранить" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from "vue";
import { useRouter } from "vue-router";
import { type LibraryItem, type LibraryStatus } from "@/api/library";
import type { Anime, Playlist } from "@/types";
import apiClient from "@/api/client";
import { getMediaUrl } from "@/api/client";
import GenreRow from "@/components/Cards/GenreRow.vue";
import { PlaylistSelectModal, ReminderModal } from "@/components/Modals";
import playlistsApi from "@/api/playlists";
import { animeDiscussionsApi } from "@/api/animeDiscussions";
import remindersApi from "@/api/reminders";
import { useToast } from "@/composables/useToast";
import { useProgressSync } from "@/composables/useProgressSync";
import { useAnimeDiscussionNavigation } from "@/composables/useAnimeDiscussionNavigation";
import { useWatchProgressStore } from "@/stores/watchProgress";
import { useFavoritesStore } from "@/stores/favorites";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";

const props = defineProps<{ item: LibraryItem }>();
const emit = defineEmits<{ updated: []; deleted: [] }>();
const progressStore = useWatchProgressStore();
const favorites = useFavoritesStore();
void favorites.ensureLoaded().catch(() => undefined);
const router = useRouter();

const STATUS: Record<string, { icon: string; color: string; label: string }> = {
  started: { icon: "watching", color: "var(--accent)", label: "В процессе" },
  completed: { icon: "completed", color: "#22c55e", label: "Просмотрено" },
  planned: { icon: "plan-to-watch", color: "#a78bfa", label: "Запланировано" },
  on_hold: { icon: "on-hold", color: "#f59e0b", label: "Отложено" },
  dropped: { icon: "dropped", color: "#ef4444", label: "Брошено" },
  favorite: { icon: "favorite", color: "#f59e0b", label: "Избранное" },
};

const STATUS_LIST: Array<{
  key: LibraryStatus;
  icon: string;
  color: string;
  label: string;
}> = [
  { key: "started", ...STATUS.started! },
  { key: "completed", ...STATUS.completed! },
  { key: "planned", ...STATUS.planned! },
  { key: "on_hold", ...STATUS.on_hold! },
  { key: "dropped", ...STATUS.dropped! },
];

const isIconName = (name: string | undefined): name is string => {
  return (
    name !== undefined &&
    [
      "watching",
      "completed",
      "plan-to-watch",
      "on-hold",
      "dropped",
      "favorite",
      "star",
      "heart",
    ].includes(name)
  );
};

const title = computed(
  () => props.item.anime_title_ru || props.item.anime_title_en || "-",
);
const isFavorite = computed(() =>
  favorites.loaded
    ? favorites.isFavorite(props.item.anime_id)
    : props.item.is_favorite,
);

const posterUrl = computed(() => {
  if (!props.item.anime_poster) return null;
  return getMediaUrl(props.item.anime_poster);
});

const isLandscapePoster = ref(false);

const posterBackdropStyle = computed(() => {
  const url = posterUrl.value;
  return url ? `url("${url}")` : "none";
});

const handlePosterLoad = (event: Event) => {
  const img = event.target as HTMLImageElement | null;
  if (!img || !img.naturalWidth || !img.naturalHeight) return;
  isLandscapePoster.value = img.naturalWidth > img.naturalHeight;
};

watch(posterUrl, () => {
  isLandscapePoster.value = false;
});

const showProgress = computed(
  () => props.item.status === "started" || props.item.status === "on_hold",
);

const animeYear = computed(() =>
  props.item.anime_year ||
  (typeof props.item.anime === "object" ? props.item.anime.year : null) ||
  null,
);

const totalEpisodes = computed(() =>
  props.item.anime_episodes_count ||
  (typeof props.item.anime === "object"
    ? props.item.anime.episodes_count || props.item.anime.episodes
    : null) ||
  null,
);

const animeGenres = computed(() => {
  const raw = props.item.anime_genres;
  if (!raw || !Array.isArray(raw) || raw.length === 0) return [];
  return raw.map((name) => ({ id: name, name, slug: name.toLowerCase().replace(/ /g, "-") }));
});

const hasGenres = computed(() => animeGenres.value.length > 0);

const playLabel = computed(() => {
  if (props.item.status === "planned") return "Начать";
  if (props.item.status === "completed") return "Пересмотреть";
  return "Продолжить";
});

const showActions = true;

const dateLabel = computed(() => {
  const fmt = (d: string | null) => {
    if (!d) return null;
    const date = new Date(d);
    const diff = Math.floor((Date.now() - date.getTime()) / 86400000);
    if (diff === 0) return "сегодня";
    if (diff === 1) return "вчера";
    if (diff < 7) return `${diff} дн. назад`;
    return date.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
  };
  const s = props.item.status;
  if (s === "completed" && props.item.completed_at)
    return "Завершено " + fmt(props.item.completed_at);
  if (s === "started" && props.item.updated_at)
    return "Смотрел " + fmt(props.item.updated_at);
  return "Добавлено " + (fmt(props.item.added_at) ?? "-");
});

const posterFailed = ref(false);
const menuOpen = ref(false);
const menuPos = ref<Record<string, string>>({});
const editOpen = ref(false);
const saving = ref(false);
const episodesWatchedEdited = ref(false);
const hoverR = ref(0);
const showPlaylistModal = ref(false);
const showReminderModal = ref(false);
const showCreateModal = ref(false);
const newPlaylistTitle = ref("");
const newPlaylistPublic = ref(false);
const creatingPlaylist = ref(false);
const playlists = ref<Playlist[]>([]);
const playlistsLoading = ref(false);

const toast = useToast();

const animeForModal = computed((): Anime => ({
  id: props.item.anime_id,
  title_ru: props.item.anime_title_ru,
  title_en: props.item.anime_title_en || "",
  poster: props.item.anime_poster || undefined,
  poster_url: props.item.anime_poster || undefined,
  poster_image_url: props.item.anime_poster || undefined,
}));

const loadPlaylists = async () => {
  playlistsLoading.value = true;
  try {
    const res = await playlistsApi.getMyPlaylists();
    playlists.value = (res.data || []) as unknown as Playlist[];
  } catch {
  } finally {
    playlistsLoading.value = false;
  }
};

watch(showPlaylistModal, (v) => {
  if (v) loadPlaylists();
});

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
      }),
    );
    await Promise.all(promises);
    showPlaylistModal.value = false;
    toast.success("Аниме добавлено в плейлист!");
  } catch (_e: unknown) {
    toast.error(
      _e instanceof Error
        ? _e.message
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
  } catch (_e: unknown) {
    toast.error(
      _e instanceof Error
        ? _e.message
        : "Не удалось создать плейлист",
    );
  } finally {
    creatingPlaylist.value = false;
  }
};

const { navigateToAnimeDiscussion } = useAnimeDiscussionNavigation();

const handleDiscuss = async () => {
  try {
    await navigateToAnimeDiscussion(props.item.anime_id);
  } catch (_e: unknown) {
    toast.error(
      _e instanceof Error
        ? _e.message
        : "Не удалось открыть обсуждение",
    );
  }
};

const handleReminderSave = async (data: {
  animeId: number;
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
      anime_id: props.item.anime_id,
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
  } catch (_e: unknown) {
    toast.error(
      _e instanceof Error
        ? _e.message
        : "Не удалось установить напоминание",
    );
  }
};

const editForm = reactive({
  status: props.item.status,
  current_episode: props.item.current_episode,
  episodes_watched: props.item.episodes_watched,
  rating: props.item.rating as number | null,
  notes: props.item.notes ?? "",
  is_favorite: isFavorite.value,
});

const clampEpisodes = (value: number) =>
  Math.min(
    Math.max(0, Number(value) || 0),
    props.item.anime_episodes_count || 9999,
  );

const setEditedEpisodes = (value: number) => {
  editForm.episodes_watched = clampEpisodes(value);
  episodesWatchedEdited.value = true;
};

const normalizeEditedEpisodes = () => {
  editForm.episodes_watched = clampEpisodes(editForm.episodes_watched);
};

const goAnime = () => {
  router.push(`/anime/${props.item.anime_slug || props.item.anime}`);
};

const watchNow = () => {
  menuOpen.value = false;
  const ep =
    props.item.status === "completed" ? 1 : props.item.current_episode || 1;
  router.push(`/anime/${props.item.anime_slug || props.item.anime}/watch?episode=${ep}`);
};

const openMenu = (e: MouseEvent) => {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
  const edgeGap = 20;
  const menuHeight = 360;
  menuPos.value = {
    top: Math.max(edgeGap, Math.min(rect.bottom + 4, window.innerHeight - menuHeight - edgeGap)) + "px",
    left: Math.min(rect.left, window.innerWidth - 220) + "px",
  };
  menuOpen.value = true;
};

  const openEdit = () => {
    menuOpen.value = false;
    Object.assign(editForm, {
      status: props.item.status,
      current_episode: props.item.current_episode,
      episodes_watched: props.item.episodes_watched,
      rating: props.item.rating,
      notes: props.item.notes ?? "",
      is_favorite: isFavorite.value,
    });
    episodesWatchedEdited.value = false;
    editOpen.value = true;
  };

const setStatus = async (status: LibraryStatus) => {
  menuOpen.value = false;
  try {
    const response = await apiClient.patch(`/users/library/${props.item.id}/`, { status });
    const serverItem = response.data;
    progressStore.setProgress(props.item.anime_id, {
      status: serverItem.status,
      current_episode: serverItem.current_episode,
      episodes_watched: serverItem.episodes_watched,
      progress_percentage: serverItem.progress_percentage,
      total_episodes: props.item.anime_episodes_count || 0,
    });
    emit("updated");
  } catch (e) {
    toast.error("Не удалось обновить статус");
    console.error(e);
  }
};

const toggleFav = async () => {
  menuOpen.value = false;
  try {
    const newFav = !isFavorite.value;
    await favorites.setFavorite(props.item.anime_id, newFav);
    progressStore.setProgress(props.item.anime_id, {
      status: props.item.status,
      current_episode: props.item.current_episode,
      episodes_watched: props.item.episodes_watched,
      progress_percentage: props.item.progress_percentage,
      total_episodes: props.item.anime_episodes_count || 0,
      updatedAt: Date.now(),
    });
    emit("updated");
  } catch (e) {
    console.error(e);
  }
};

const deleteItem = async () => {
  menuOpen.value = false;
  if (!confirm(`Удалить "${title.value}" из коллекции?`)) return;
  try {
    await apiClient.delete(`/users/library/${props.item.id}/`);
    progressStore.clearProgress(props.item.anime_id);
    emit("deleted");
  } catch (e) {
    console.error(e);
  }
};

const saveEdit = async () => {
  saving.value = true;
  try {
    const payload: Record<string, unknown> = {
      status: editForm.status,
      rating: editForm.rating,
      notes: editForm.notes,
      is_favorite: editForm.is_favorite,
    };
    if (episodesWatchedEdited.value) {
      payload.episodes_watched = editForm.episodes_watched;
    }
    const response = await apiClient.patch(`/users/library/${props.item.id}/`, payload);
    const serverItem = response.data;
    await favorites.commitIdsFavorite([props.item.anime_id], serverItem.is_favorite);
    progressStore.setProgress(props.item.anime_id, {
      status: serverItem.status,
      current_episode: serverItem.current_episode,
      episodes_watched: serverItem.episodes_watched,
      progress_percentage: serverItem.progress_percentage,
      total_episodes: props.item.anime_episodes_count || 0,
    });
    editOpen.value = false;
    emit("updated");
  } catch (e) {
    toast.error("Не удалось сохранить изменения");
    console.error(e);
  } finally {
    saving.value = false;
  }
};
</script>

<style>
.lib-card {
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
  transition:
    transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.35s ease;
  contain: layout style paint;
}

.lib-card:hover {
  transform: translateY(-4px);
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border-subtle));
  box-shadow:
    0 18px 40px -18px rgba(0, 0, 0, 0.65),
    0 0 0 1px color-mix(in srgb, var(--accent) 22%, transparent);
}
</style>

<style scoped>
/* ── Poster ─────────────────────────────────────────── */
.poster-wrap {
  position: relative;
  width: 100%;
  padding-top: 150%;
  background: linear-gradient(160deg, var(--surface-4), var(--surface-3));
  overflow: hidden;
  isolation: isolate;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
  backface-visibility: hidden;
}

.poster-img {
  position: absolute;
  top: 0px;
  left: 0px;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.lib-card:hover .poster-img {
  transform: scale(1.06);
}

.poster-landscape .poster-img {
  object-fit: contain;
}

.lib-card:hover .poster-landscape .poster-img {
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

.poster-ph {
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

.lib-card:hover .hover-overlay {
  opacity: 1;
  background: rgba(0, 0, 0, 0.55);
}

.play-btn {
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
  transform: scale(0.7);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
    background 0.2s ease, box-shadow 0.3s ease;
  box-shadow: 0 10px 30px -8px color-mix(in srgb, var(--accent) 70%, transparent);
}

.lib-card:hover .play-btn {
  transform: scale(1);
}

.play-btn:hover {
  transform: scale(1.08) !important;
  background: var(--accent-hover);
  box-shadow: 0 14px 40px -8px color-mix(in srgb, var(--accent) 90%, transparent);
}

.play-btn svg {
  width: 26px;
  height: 26px;
  margin-left: 3px;
}

/* ── Action buttons (left column) ───────────────────── */
.card-actions {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  opacity: 0;
  transform: translateX(-8px);
  transition: opacity 0.28s ease, transform 0.28s ease;
  z-index: 10;
}

.lib-card:hover .card-actions {
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

/* ── Status pill (top-right) ────────────────────────── */
.status-pill {
  position: absolute;
  top: 10px;
  right: 10px;
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

.status-pill svg {
  color: white;
}

/* ── Progress bar on poster ─────────────────────────── */
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
  background: var(--accent);
  border-radius: 0 4px 4px 0;
  transition: width 0.4s ease;
}

/* ── Info block ─────────────────────────────────────── */
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
  min-height: 0;
  cursor: pointer;
  transition: color 0.2s ease;
}

.anime-title:hover {
  color: var(--accent);
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

.anime-state-meta {
  color: var(--text-tertiary);
}

.meta-pct {
  color: var(--accent);
  font-weight: 700;
}

.meta-rating {
  color: #fbbf24;
  font-weight: 700;
}

.meta-rating svg {
  width: 13px;
  height: 13px;
  color: #fbbf24;
}

.meta-date {
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
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  min-height: 22px;
  max-height: 22px;
  overflow: hidden;
}

.genre-tag {
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
  font-size: 10.5px;
  font-weight: 600;
  color: var(--text-tertiary);
  padding: 4px 6px;
  line-height: 1;
  white-space: nowrap;
}

.date-lbl {
  font-size: 11.5px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: auto;
  min-height: 14px;
}

/* ── Responsive ─────────────────────────────────────── */
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

  .status-pill {
    top: 8px;
    right: 8px;
    width: 26px;
    height: 26px;
    border-radius: 8px;
  }
}

/* ═══ КОНТЕКСТНОЕ МЕНЮ ══════════════════════════════════════ */
.ctx-back {
  position: fixed;
  inset: 0;
  z-index: 1100;
}

.ctx-menu {
  position: fixed;
  z-index: 1101;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  padding: var(--space-1);
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  animation: pop-in 0.12s var(--ease-out);
}

@keyframes pop-in {
  from {
    opacity: 0;
    transform: scale(0.94) translateY(-4px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.ctx-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  height: 34px;
  padding: 0 var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  transition: all var(--duration-base);
}

.ctx-item:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}
.ctx-item.active {
  color: var(--accent);
  background: var(--accent-subtle);
}
.ctx-item.danger {
  color: var(--danger);
}
.ctx-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* ═══ МОДАЛКА СОЗДАНИЯ ПЛЕЙЛИСТА ════════════════════════════ */
.create-playlist-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  padding: 1rem;
}

.create-playlist-dialog {
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

.create-playlist-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.create-playlist-input {
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

.create-playlist-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.create-playlist-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.create-playlist-btn {
  height: 36px;
  padding: 0 16px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--duration-base);
}

.create-playlist-cancel {
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.create-playlist-submit {
  background: var(--accent);
  color: white;
  border: none;
  font-weight: 600;
}

.create-playlist-submit.disabled,
.create-playlist-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ═══ МОДАЛКА РЕДАКТИРОВАНИЯ ════════════════════════════════ */
.modal-back {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  animation: fb 0.15s var(--ease-out);
}

@keyframes fb {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.edit-modal {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-2xl);
  width: 100%;
  max-width: 460px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: slide-up 0.2s var(--ease-out);
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.em-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.em-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.35;
}

.em-sub {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 3px 0 0 0;
}

.em-close {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  min-width: 30px;
  min-height: 30px;
  border-radius: 50%;
  border: none;
  background: var(--surface-4);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-base);
}

.em-close:hover {
  background: var(--surface-5);
  color: var(--text-primary);
}

.em-body {
  padding: var(--space-5);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.em-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.em-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.em-hint {
  font-weight: 400;
  color: var(--text-tertiary);
  margin-left: var(--space-2);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}

.sg-opt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--space-3) var(--space-2);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-base);
}

.sg-opt:hover {
  background: var(--surface-4);
  border-color: var(--border-default);
}
.sg-opt.sel {
  background: var(--accent-subtle);
  border-color: var(--accent);
}

.sg-icon {
  font-size: 18px;
  line-height: 1;
}
.sg-lbl {
  font-size: 10px;
  font-weight: 500;
  color: var(--text-secondary);
  text-align: center;
}
.sg-opt.sel .sg-lbl {
  color: var(--accent);
}

.ep-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.ep-adj {
  width: 34px;
  height: 34px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base);
}

.ep-adj:hover {
  background: var(--surface-4);
}

.ep-in {
  flex: 1;
  height: 34px;
  text-align: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-base);
  font-weight: 600;
  outline: none;
}

.ep-in:focus {
  border-color: var(--accent);
}
/* Chrome, Safari, Edge, Opera */
.ep-in::-webkit-outer-spin-button,
.ep-in::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
.ep-in {
  -moz-appearance: textfield;
  appearance: textfield;
}
.stars-row {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}

.star-b {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  line-height: 0;
  transition: transform var(--duration-base);
}

.star-b:hover {
  transform: scale(1.2);
}

.rating-disp {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--warning);
  margin-left: 4px;
}

.clear-r {
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
}

.clear-r:hover {
  color: var(--danger);
}

.em-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.toggle {
  width: 40px;
  height: 22px;
  border-radius: var(--radius-full);
  background: var(--surface-5);
  position: relative;
  transition: background var(--duration-base);
}

.toggle.on {
  background: var(--accent);
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  transition: transform var(--duration-base);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.toggle.on .toggle-thumb {
  transform: translateX(18px);
}

.em-note {
  width: 100%;
  padding: var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-size: var(--text-sm);
  line-height: 1.5;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
}

.em-note:focus {
  border-color: var(--accent);
}
.em-note::placeholder {
  color: var(--text-tertiary);
}

.em-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--border-subtle);
}

.em-cancel {
  height: 36px;
  padding: 0 var(--space-5);
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
}

.em-cancel:hover {
  background: var(--surface-5);
  color: var(--text-primary);
}

.em-save {
  height: 36px;
  padding: 0 var(--space-6);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: all var(--duration-base);
}

.em-save:hover:not(:disabled) {
  background: var(--accent-hover);
}
.em-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.spin-ic {
  animation: spin 0.8s linear infinite;
}
</style>
