<template>
  <div class="col-card" :class="statusClass">
    <div class="card-poster" @click="goToAnime">
      <OptimizedImage
        v-if="posterUrl"
        :src="posterUrl"
        :alt="item.anime_title_ru"
        class="poster-img"
        @error="posterError = true"
      />
      <div v-else class="poster-placeholder">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <rect x="2" y="2" width="20" height="20" rx="2" />
          <path d="M12 2v20M2 12h20" />
        </svg>
      </div>

      <div
        class="status-badge"
        :class="{ completed: item.status === 'completed' }"
        :style="{ background: statusColor }"
      >
        <SakuraIcon
          v-if="isIconName(statusIcon)"
          :name="statusIcon"
          :size="14"
          style="color: white"
        />
        <span v-else>{{ statusIcon }}</span>
      </div>


      <div v-if="showProgress" class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: item.progress_percentage + '%' }"
        ></div>
      </div>

      <div class="poster-overlay">
        <button class="overlay-btn menu" @click.stop="openMenu" title="Действия">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="5" r="1.5" />
            <circle cx="12" cy="12" r="1.5" />
            <circle cx="12" cy="19" r="1.5" />
          </svg>
        </button>
      </div>
    </div>

    <div class="card-info">
      <h3 class="card-title" :title="item.anime_title_ru || item.anime_title_en" @click="goToAnime">
        {{ item.anime_title_ru || item.anime_title_en }}
      </h3>

      <div v-if="animeYear || totalEpisodes" class="anime-meta">
        <span v-if="animeYear">{{ animeYear }}</span>
        <span v-if="animeYear && totalEpisodes" class="meta-dot">·</span>
        <span v-if="totalEpisodes">{{ totalEpisodes }} эп.</span>
      </div>

      <div v-if="showProgress" class="episode-info">
        <span class="ep-text">
          {{ item.current_episode }} / {{ totalEpisodes || "?" }} эп.
        </span>
        <span class="ep-pct">{{ item.progress_percentage }}%</span>
      </div>

      <div v-if="item.rating" class="rating-row">
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="var(--warning)"
          stroke="none"
        >
          <polygon
            points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
          />
        </svg>
        <span class="rating-val">{{ item.rating }}/10</span>
      </div>

      <div class="date-row">
        <svg
          width="10"
          height="10"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        <span class="date-text">{{ dateLabel }}</span>
      </div>

      <div class="quick-actions quick-actions--compact">
        <button class="qa-btn menu" @click.stop="openMenu" title="Ещё">
          <SakuraIcon name="more-dots" :size="14" />
        </button>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="menuOpen" class="ctx-backdrop" @click="menuOpen = false"></div>
      <div v-if="menuOpen" class="ctx-menu" :style="menuStyle">
        <button class="ctx-item" @click="goToAnime">
          <svg
            width="14"
            height="14"
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
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
          Смотреть
        </button>
        <div class="ctx-divider"></div>
        <template v-for="tab in statusMenuItems" :key="tab.key">
          <button
            class="ctx-item"
            :class="{ current: item.status === tab.key }"
            @click="changeStatus(tab.key)"
          >
            <SakuraIcon
              v-if="isIconName(tab.icon)"
              :name="tab.icon"
              :size="16"
            />
            <span v-else>{{ tab.icon }}</span> {{ tab.label }}
          </button>
        </template>
        <div class="ctx-divider"></div>
        <button class="ctx-item" @click="openEdit">
          <svg
            width="14"
            height="14"
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
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            <path d="M10 11v6" />
            <path d="M14 11v6" />
            <path d="M9 6V4h6v2" />
          </svg>
          Удалить из коллекции
        </button>
      </div>
    </Teleport>

    <PlaylistSelectModal v-if="showPlaylistModal"
      :show="showPlaylistModal"
      :anime="animeForModal as Anime"
      :playlists="playlists as unknown as Playlist[]"
      :is-loading="playlistsLoading"
      @close="showPlaylistModal = false"
      @save="showPlaylistModal = false"
      @create-playlist="handleCreatePlaylist"
    />

    <Teleport to="body">
      <Transition name="psm-anim">
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

    <ReminderModal v-if="showReminderModal"
      :show="showReminderModal"
      :anime="animeForModal as Anime"
      @close="showReminderModal = false"
      @save="handleReminderSave"
    />
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import {
  libraryApi,
  type LibraryItem,
  type LibraryStatus,
} from "@/api/library";
import { getMediaUrl } from "@/api/client";
import type { Anime, Playlist } from "@/types";
const PlaylistSelectModal = defineAsyncComponent(() => import("@/components/Modals/PlaylistSelectModal.vue"));
const ReminderModal = defineAsyncComponent(() => import("@/components/Modals/ReminderModal.vue"));
import playlistsApi from "@/api/playlists";
import remindersApi from "@/api/reminders";
import { useToast } from "@/composables/useToast";
import { useProgressSync } from "@/composables/useProgressSync";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";

const props = defineProps<{ item: LibraryItem }>();
const emit = defineEmits<{
  statusChanged: [];
  deleted: [];
  rated: [];
  edit: [item: LibraryItem];
}>();

const router = useRouter();
const toast = useToast();
const { bump: bumpProgressSync } = useProgressSync();
const menuOpen = ref(false);
const menuStyle = ref({});
const posterError = ref(false);
const showPlaylistModal = ref(false);
const showReminderModal = ref(false);
const showCreateModal = ref(false);
const newPlaylistTitle = ref("");
const newPlaylistPublic = ref(false);
const creatingPlaylist = ref(false);
const playlists = ref<unknown[]>([]);
const playlistsLoading = ref(false);

const animeForModal = computed((): unknown => ({
  id: animeId.value,
  title_ru: props.item.anime_title_ru,
  title_en: props.item.anime_title_en || "",
  poster_url: props.item.anime_poster || null,
  poster_image_url: props.item.anime_poster || null,
}));

const animeId = computed(() => {
  if (props.item.anime_id) return props.item.anime_id;
  if (typeof props.item.anime === "number") return props.item.anime;
  if (typeof props.item.anime === "object" && props.item.anime?.id)
    return props.item.anime.id;
  return null;
});

watch(showPlaylistModal, async (v) => {
  if (!v) return;
  playlistsLoading.value = true;
  try {
    const res = await playlistsApi.getMyPlaylists();
    playlists.value = res.data || [];
  } catch {
  } finally {
    playlistsLoading.value = false;
  }
});

const handleReminderSave = async (data: unknown) => {
  if (!animeId.value) {
    toast.error("Не удалось определить ID аниме");
    return;
  }
  const d = data as {
    reminderTime?: string;
    repeatWeekly?: boolean;
    comment?: string;
    enableSound?: boolean;
    enablePush?: boolean;
  };
  try {
    await remindersApi.createReminder({
      anime_id: animeId.value,
      reminder_time: new Date(d.reminderTime || "").toISOString(),
      repeat_weekly: d.repeatWeekly || false,
      comment: d.comment || "",
      enable_sound: d.enableSound ?? true,
      enable_push: d.enablePush ?? true,
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
    const res = await playlistsApi.getMyPlaylists();
    playlists.value = res.data || [];
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

const posterUrl = computed(() => {
  if (posterError.value) return null;
  const poster = props.item.anime_poster;
  if (!poster) return null;
  if (typeof poster === "string") return getMediaUrl(poster);
  if (typeof poster === "object") {
    const posterObj = poster as { url?: string };
    if (posterObj.url) return getMediaUrl(posterObj.url);
  }
  return null;
});

const statusConfig: Record<
  string,
  { icon: string; color: string; label: string }
> = {
  started: { icon: "watching", color: "var(--accent)", label: "В процессе" },
  completed: { icon: "completed", color: "#22c55e", label: "Просмотрено" },
  planned: { icon: "plan-to-watch", color: "#a78bfa", label: "Запланировано" },
  on_hold: { icon: "on-hold", color: "#f59e0b", label: "Отложено" },
  dropped: { icon: "dropped", color: "#ef4444", label: "Брошено" },
  favorite: { icon: "favorite", color: "#f59e0b", label: "Избранное" },
};

const isIconName = (icon: string | undefined): boolean => {
  if (!icon) return false;
  return /^[a-zA-Z][a-zA-Z0-9-]*$/.test(icon);
};

const statusIcon = computed(
  () => statusConfig[props.item.status]?.icon ?? "📖",
);
const statusColor = computed(
  () => statusConfig[props.item.status]?.color ?? "var(--surface-5)",
);
const statusClass = computed(() => `status-${props.item.status}`);

const showProgress = computed(
  () => props.item.status === "started" || props.item.status === "on_hold",
);

const totalEpisodes = computed(() => {
  return (
    props.item.anime_episodes_count ||
    (typeof props.item.anime === "object"
      ? props.item.anime?.episodes_count || props.item.anime?.episodes
      : 0) ||
    0
  );
});

const animeYear = computed(() =>
  props.item.anime_year ||
  (typeof props.item.anime === "object" ? props.item.anime?.year : null) ||
  null,
);

const primaryAction = () => {
  if (!animeId.value && !animeSlug.value) {
    toast.error("Не удалось определить ID аниме");
    return;
  }
  const season =
    props.item.status === "completed" ? 1 : props.item.current_season || 1;
  const ep =
    props.item.status === "completed" ? 1 : props.item.current_episode || 1;
  router.push(
    `/anime/${animeSlug.value || animeId.value}/watch?season=${season}&episode=${ep}`,
  );
};

const watchNow = () => {
  menuOpen.value = false;
  primaryAction();
};

const dateLabel = computed(() => {
  const fmtDate = (d: string | null) => {
    if (!d) return null;
    const date = new Date(d);
    const today = new Date();
    const diff = Math.floor((today.getTime() - date.getTime()) / 86400000);
    if (diff === 0) return "сегодня";
    if (diff === 1) return "вчера";
    if (diff < 7) return `${diff} дн. назад`;
    return date.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
  };

  if (props.item.status === "completed" && props.item.completed_at) {
    return "Завершено " + fmtDate(props.item.completed_at);
  }
  if (props.item.status === "started" && props.item.updated_at) {
    return "Смотрел " + fmtDate(props.item.updated_at);
  }
  return "Добавлено " + (fmtDate(props.item.added_at) ?? "-");
});

const statusMenuItems = [
  { key: "started" as LibraryStatus, icon: "watching", label: "В процессе" },
  {
    key: "completed" as LibraryStatus,
    icon: "completed",
    label: "Просмотрено",
  },
  {
    key: "planned" as LibraryStatus,
    icon: "plan-to-watch",
    label: "Запланировано",
  },
  { key: "on_hold" as LibraryStatus, icon: "on-hold", label: "Отложено" },
  { key: "dropped" as LibraryStatus, icon: "dropped", label: "Брошено" },
];

const openMenu = (e: MouseEvent) => {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
  menuStyle.value = {
    top: Math.min(rect.bottom + 6, window.innerHeight - 340) + "px",
    left: Math.min(rect.left, window.innerWidth - 220) + "px",
  };
  menuOpen.value = true;
};

const animeSlug = computed(() => {
  return props.item.anime_slug || (typeof props.item.anime === "object" ? props.item.anime?.slug : undefined);
});

const goToAnime = () => {
  if (!animeSlug.value && !animeId.value) {
    console.error("CollectionCard: anime slug/id is null", props.item);
    return;
  }
  router.push(`/anime/${animeSlug.value || animeId.value}`);
};

const changeStatus = async (status: LibraryStatus) => {
  menuOpen.value = false;
  try {
    const data: Record<string, unknown> = { status };
    await libraryApi.updateLibraryItem(props.item.id, data);
    bumpProgressSync();
    emit("statusChanged");
  } catch (e) {
    console.error(e);
  }
};

const deleteItem = async () => {
  menuOpen.value = false;
  if (!confirm(`Удалить "${props.item.anime_title_ru}" из коллекции?`)) return;
  try {
    await libraryApi.deleteLibraryItem(props.item.id);
    bumpProgressSync();
    emit("deleted");
  } catch (e) {
    console.error(e);
  }
};

const openEdit = () => {
  menuOpen.value = false;
  emit("edit", props.item);
};
</script>

<style scoped>
.col-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: transform var(--duration-slow) var(--ease-out);
  contain: layout style paint;
}

.col-card:hover {
  transform: translateY(-3px);
}

.card-poster {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  isolation: isolate;
  background: var(--surface-4);
  cursor: pointer;
  backface-visibility: hidden;
}

.poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-slow) var(--ease-out);
}

.col-card:hover .poster-img {
  transform: scale(1.05);
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.status-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 14px;
  line-height: 1;
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
  transition: all 0.2s ease;
}

.status-badge.completed {
  background: #22c55e !important;
  box-shadow: 0 2px 12px rgba(34, 197, 94, 0.5);
}

.card-action-btns {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  flex-direction: row;
  gap: 4px;
  opacity: 0;
  transform: translateY(-6px);
  transition:
    opacity var(--duration-base) var(--ease-out),
    transform var(--duration-base) var(--ease-out);
  z-index: 10;
}

.col-card:hover .card-action-btns {
  opacity: 1;
  transform: translateY(0);
}

.card-action-btn {
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.55);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-out), background 0.2s ease;
  backdrop-filter: blur(8px);
  flex-shrink: 0;
  padding: 0;
  line-height: 0;
}

.card-action-btn:hover {
  background-color: rgba(255, 126, 179, 0.55);
  transform: scale(1.1);
}

.card-action-btn.fav-btn {
  color: var(--text-secondary);
}
.card-action-btn.fav-btn:hover {
  background-color: rgba(8, 8, 9, 0.8);
  transform: scale(1.1);
}
.card-action-btn.fav-btn.active {
  color: var(--danger);
}
.card-action-btn.fav-btn.active:hover {
  background-color: rgba(239, 68, 68, 0.85);
  transform: scale(1.1);
}

.card-action-btn.discuss-btn:hover {
  background-color: rgba(255, 126, 179, 0.85);
}

.card-action-btn.playlist-btn:hover {
  background-color: rgba(168, 197, 226, 0.85);
}

.card-action-btn.reminder-btn:hover {
  background-color: rgba(252, 163, 19, 0.85);
}

@media (max-width: 767px) {
  .card-action-btns {
    opacity: 1;
    transform: translateY(0);
  }
  .card-action-btn {
    width: 30px;
    height: 30px;
    min-width: 30px;
    min-height: 30px;
  }
}

@media (max-width: 480px) {
  .card-action-btns {
    top: 4px;
    right: 4px;
    gap: 2px;
  }

  .card-action-btn {
    width: 22px;
    height: 22px;
    min-width: 22px;
    min-height: 22px;
  }

  .card-action-btn svg {
    width: 12px;
    height: 12px;
  }
}

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0, 0, 0, 0.4);
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.4s ease;
}

.poster-overlay {
  position: absolute;
  inset: -1px;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  opacity: 0;
  transition: opacity var(--duration-base);
  z-index: 4;
  backface-visibility: hidden;
}

.col-card:hover .poster-overlay {
  opacity: 1;
}

.overlay-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform: scale(0.6);
  box-shadow: 0 0 0 0 rgba(124, 92, 252, 0);
}

.col-card:hover .overlay-btn {
  transform: scale(1);
  box-shadow: 0 0 20px 3px rgba(124, 92, 252, 0.4);
}

.overlay-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.15) !important;
}

.overlay-btn.primary {
  background: var(--accent);
  width: 64px;
  height: 64px;
  padding-left: 4px;
}

.col-card:hover .overlay-btn.primary {
  box-shadow: 0 0 30px 5px rgba(124, 92, 252, 0.5);
}

.overlay-btn.primary:hover {
  background: var(--accent-hover);
  transform: scale(1.2) !important;
  box-shadow: 0 0 40px 10px rgba(124, 92, 252, 0.6);
}

.overlay-btn svg {
  width: 24px;
  height: 24px;
}

.card-info {
  padding: 0 2px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  white-space: nowrap;
  overflow-wrap: normal;
  word-break: normal;
  line-height: 1.3;
  cursor: pointer;
}

.card-title:hover {
  color: var(--accent);
}

.anime-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  min-height: 15px;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  line-height: 1;
}

.meta-dot {
  color: var(--text-tertiary);
}

.episode-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.ep-text {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}
.ep-pct {
  font-size: 10px;
  color: var(--accent);
  font-weight: 600;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rating-val {
  font-size: var(--text-xs);
  color: var(--warning);
  font-weight: 600;
}

.date-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.date-text {
  font-size: 10px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 2px;
}

.quick-actions--compact {
  justify-content: flex-end;
}

.qa-btn {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 50%;
  cursor: pointer;
  transition: all var(--duration-base);
  padding: 0;
}

.qa-btn.menu {
  width: 28px;
  height: 28px;
}

.qa-btn:hover {
  background: var(--surface-5);
  color: var(--text-primary);
}

.ctx-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
}

.ctx-menu {
  position: fixed;
  z-index: 1001;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-1);
  min-width: 200px;
  box-shadow: var(--shadow-sm-lg);
  animation: menu-in 0.12s var(--ease-out);
}

@keyframes menu-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-4px);
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
  height: 36px;
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
.ctx-item.current {
  color: var(--accent);
  background: var(--accent-subtle);
}
.ctx-item.danger {
  color: var(--danger);
}
.ctx-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

.status-badge svg {
  color: white;
}

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

  .ctx-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: var(--space-1) 0;
}
</style>
