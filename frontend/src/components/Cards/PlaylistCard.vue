<template>
  <div class="playlist-card" tabindex="0" role="group" :aria-label="playlist.title" @click="handleClick" @keydown.enter.self="handleClick">
    <div class="playlist-cover">
      <PlaylistCover
        :posters="coverPosters.map(p => p.url)"
        :custom-cover="playlist.cover_image"
        :label="`Обложка: ${playlist.title}`"
        :empty-label="emptyCoverLabel"
      />

      <div class="cover-overlay"></div>
      <div v-if="playlist.topics?.length" class="card-topics" :title="topicLabels.join(', ')">
        <span v-for="topic in topicLabels.slice(0, 2)" :key="topic">{{ topic }}</span>
        <span v-if="topicLabels.length > 2">+{{ topicLabels.length - 2 }}</span>
      </div>
      <button v-if="visibility === 'public'" type="button" class="playlist-like"
        :class="{ 'is-liked': liked, 'is-pending': likePending, 'has-error': likeError }"
        :aria-pressed="liked" :aria-busy="likePending" :disabled="likePending"
        :aria-label="`${liked ? 'Снять лайк' : 'Поставить лайк'}: ${likeCount}`"
        :title="likeError || (liked ? 'Снять лайк' : 'Поставить лайк')" @click.stop="toggleLike">
        <svg width="19" height="19" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" /></svg>
        <span>{{ formatCount(likeCount) }}</span>
      </button>
      <span v-if="likeError" class="like-error" role="alert" @click.stop>{{ likeError }}</span>
      <div class="hover-overlay"></div>

      <button class="compact-actions-button action-btn" type="button" aria-haspopup="dialog"
        :aria-label="`Действия с плейлистом «${playlist.title}»`" @click.stop="openActions">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>
      </button>

      <div class="card-actions">
        <button
          :class="['action-btn', 'favorite-btn', { 'is-active': isFav }]"
          @click="toggleFavorite"
          :title="isFav ? 'Убрать из избранного' : 'В избранное'"
          type="button"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            :fill="isFav ? 'currentColor' : 'none'"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polygon
              points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
            />
          </svg>
        </button>

        <button
          class="action-btn share-btn"
          @click="sharePlaylist"
          title="Поделиться"
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
            <circle cx="18" cy="5" r="3" />
            <circle cx="6" cy="12" r="3" />
            <circle cx="18" cy="19" r="3" />
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
          </svg>
        </button>

        <template v-if="isOwner">
          <button
            class="action-btn edit-btn"
            @click="handleEdit"
            title="Редактировать"
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
              <path
                d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
              />
              <path
                d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
              />
            </svg>
          </button>

          <button
            class="action-btn danger-btn"
            @click="handleDelete"
            title="Удалить"
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
              <polyline points="3 6 5 6 21 6" />
              <path
                d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
              />
            </svg>
          </button>
        </template>
      </div>

      <div
        :class="['privacy-badge', `privacy-${visibility}`]"
        :title="visibilityLabel"
      >
        <svg
          v-if="visibility === 'private'"
          width="13"
          height="13"
          viewBox="0 0 24 24"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M7.4 11V7.6a4.6 4.6 0 0 1 9.2 0V11" fill="none" stroke="#2a1530" stroke-width="5" />
          <path d="M7.4 11V7.6a4.6 4.6 0 0 1 9.2 0V11" fill="none" stroke="#dfe6f2" stroke-width="2" />
          <rect x="3.5" y="10.5" width="17" height="11.5" rx="3" fill="#ffd166" stroke="#2a1530" stroke-width="2.6" />
          <circle cx="12" cy="15.4" r="1.9" fill="#2a1530" />
          <path d="M12 16.2v3" fill="none" stroke="#2a1530" stroke-width="2.4" />
          <path d="M6.6 13.6v4.2" fill="none" stroke="#fff" stroke-width="1.8" />
        </svg>

        <!-- link: цепочка -->
        <svg
          v-else-if="visibility === 'link'"
          width="13"
          height="13"
          viewBox="0 0 24 24"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" fill="none" stroke="#2a1530" stroke-width="5.2" />
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" fill="none" stroke="#2a1530" stroke-width="5.2" />
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" fill="none" stroke="#6ec6ff" stroke-width="2.2" />
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" fill="none" stroke="#ff8ac2" stroke-width="2.2" />
          <path d="M15.6 5.2l2.6-.4" fill="none" stroke="#fff" stroke-width="1.4" />
          <path d="M5.6 15.8l-.4 2.6" fill="none" stroke="#fff" stroke-width="1.4" />
        </svg>

        <!-- public: глобус -->
        <svg
          v-else
          width="13"
          height="13"
          viewBox="0 0 24 24"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="12" cy="12" r="10" fill="#8fd3ff" stroke="#2a1530" stroke-width="2.6" />
          <path d="M6 7c2-1.5 4-1 4.5 1s-1 3-2.5 3.5-3 2-3.5 0S4.5 8 6 7z" fill="#3ddc84" stroke="#2a1530" stroke-width="1.4" />
          <path d="M14 13c1.5-.5 3.5 0 3.8 1.8s-1 3.4-2.6 3.4-2.2-1.2-2.2-2.6.2-2 1-2.6z" fill="#3ddc84" stroke="#2a1530" stroke-width="1.4" />
          <path d="M5.6 9.4A7 7 0 0 1 9.2 5.4" fill="none" stroke="#fff" stroke-width="1.8" />
        </svg>
      </div>

      <div class="items-count-badge">
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
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
        </svg>
        <span :title="`${totalItems} аниме`">{{ formatCount(totalItems) }}</span>
      </div>

      <div v-if="totalDuration > 0" class="duration-badge" :title="formattedDuration">
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
        <span class="duration-full">{{ formattedDuration }}</span>
        <span class="duration-short">{{ totalDuration >= 60 ? `${Math.floor(totalDuration / 60)} ч` : `${totalDuration} мин` }}</span>
      </div>
    </div>

    <div class="playlist-info">
      <h3 class="playlist-title" :title="[playlist.title, playlist.description].filter(Boolean).join(' -')">{{ playlist.title }}</h3>

      <div class="playlist-meta">
        <span class="meta-item">
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <polygon
              points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
            />
          </svg>
          {{ formatCount(playlist.favorites_count || 0) }}
        </span>
        <span class="meta-dot"></span>
        <span class="meta-item meta-date">{{ formattedUpdatedAt }}</span>
      </div>

      <button type="button" class="playlist-author" @click="goToAuthor">
        <img
          v-if="author.avatar_url"
          :src="getMediaUrl(author.avatar_url)"
          :alt="author.username"
          class="author-avatar"
          loading="lazy"
          @error="
            (e: Event) =>
              ((e.target as HTMLImageElement).style.display = 'none')
          "
        />
        <div v-else class="author-avatar-ph">
          {{ (author.username || "?")[0]?.toUpperCase() ?? "?" }}
        </div>
        <span class="author-name" :title="author.username">@{{ author.username }}</span>
      </button>
      <p class="playlist-description" :title="playlist.description">{{ playlist.description }}</p>
      <span class="compact-item-count" :title="`${totalItems} аниме · ${formattedDuration}`">{{ totalItems }} аниме</span>
    </div>
    <Teleport to="body">
      <dialog ref="actionsDialog" class="playlist-actions-dialog" :aria-label="`Действия: ${playlist.title}`" @click.stop="closeOnBackdrop">
        <h3>{{ playlist.title }}</h3>
        <p>{{ totalItems }} аниме<span v-if="totalDuration"> · {{ formattedDuration }}</span></p>
        <p v-if="topicLabels.length">{{ topicLabels.join(' · ') }}</p>
        <button type="button" @click="toggleFavorite($event); closeActions()">{{ isFav ? 'Убрать из избранного' : 'Добавить в избранное' }}</button>
        <button type="button" @click="sharePlaylist($event); closeActions()">Поделиться</button>
        <template v-if="isOwner">
          <button type="button" @click="handleEdit($event); closeActions()">Редактировать</button>
          <button type="button" @click="handleDelete($event); closeActions()">Удалить</button>
        </template>
        <button type="button" @click="closeActions">Закрыть</button>
      </dialog>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import PlaylistCover from "@/components/Playlists/PlaylistCover.vue";
import { computed, ref, watch } from "vue";
import { useAuthStore } from "@/stores/auth";
import playlistsApi from "@/api/playlists";
import { playlistTopicName } from "@/lib/playlistTopics";
import { useRouter, useRoute } from "vue-router";
import { getMediaUrl } from "@/api/client";
import type { PlaylistVisibility } from "@/api/playlists";
import { formatDuration } from "@/utils/normalizers";

interface PlaylistItem {
  id: number;
  anime?: number | unknown | { id: number; title_ru?: string; title_en?: string; poster_url?: string };
  anime_poster?: string | null;
  anime_title?: string;
}

interface Author {
  id: number;
  username: string;
  display_name?: string;
  avatar_url?: string;
  avatar?: string | null;
}

export interface Playlist {
  id: number | string;
  title: string;
  description?: string;
  visibility?: PlaylistVisibility;
  is_public?: boolean;
  is_private?: boolean;
  is_link_only?: boolean;
  share_token?: string | null;
  items_count: number;
  likes_count?: number;
  is_liked?: boolean;
  topics?: string[];
  cover_image?: string | null;
  favorites_count?: number;
  is_favorited?: boolean;
  updated_at: string;
  created_at?: string;
  user?: Author;
  user_id?: number;
  user_username?: string;
  user_avatar?: string | null;
  items?: PlaylistItem[];
  cover_urls?: string[];
  total_duration?: number;
}

interface Props {
  playlist: Playlist;
  currentUserId?: number;
  isFavorite?: boolean;
  maxPreviewItems?: number;
}

const props = withDefaults(defineProps<Props>(), {
  currentUserId: undefined,
  isFavorite: false,
  maxPreviewItems: 3,
});

const emit = defineEmits<{
    click: [playlist: Playlist];
    favoriteToggle: [playlistId: number | string, isFavorite: boolean];
    share: [playlistId: number | string];
    edit: [playlist: Playlist];
    delete: [playlist: Playlist];
    visibilityChange: [playlistId: number | string, visibility: PlaylistVisibility];
  }>();

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const actionsDialog = ref<HTMLDialogElement>();
const openActions = () => actionsDialog.value?.showModal();
const closeActions = () => actionsDialog.value?.close();
const closeOnBackdrop = (event: MouseEvent) => { if (event.target === actionsDialog.value) closeActions(); };
const liked = ref(props.playlist.is_liked || false);
const likeCount = ref(props.playlist.likes_count || 0);
const likePending = ref(false);
const likeError = ref('');
const topicLabels = computed(() => (props.playlist.topics || []).map(playlistTopicName));
const counterFormat = new Intl.NumberFormat('ru-RU', { notation: 'compact', maximumFractionDigits: 1 });
const formatCount = (count: number) => counterFormat.format(count);
watch(() => [props.playlist.id, props.playlist.is_liked, props.playlist.likes_count], () => {
  if (!likePending.value) { liked.value = props.playlist.is_liked || false; likeCount.value = props.playlist.likes_count || 0; }
});
const toggleLike = async () => {
  if (likePending.value) return;
  if (!auth.isAuthenticated) {
    await router.push({ path: '/login', query: { redirect: route.fullPath } });
    return;
  }
  const previous = { liked: liked.value, count: likeCount.value };
  const userId = auth.user?.id;
  liked.value = !previous.liked;
  likeCount.value = Math.max(0, previous.count + (liked.value ? 1 : -1));
  likePending.value = true;
  likeError.value = '';
  try {
    const { data } = await playlistsApi.setLike(props.playlist.id, liked.value);
    if (auth.user?.id === userId) { liked.value = data.is_liked; likeCount.value = data.likes_count; }
  } catch {
    liked.value = previous.liked; likeCount.value = previous.count;
    likeError.value = 'Лайк не сохранён. Повторите.';
  } finally { likePending.value = false; }
};

const author = computed(() => ({
  ...props.playlist.user,
  id: props.playlist.user?.id || props.playlist.user_id,
  username: props.playlist.user?.username || props.playlist.user_username || "",
  avatar_url:
    props.playlist.user?.avatar_url ||
    props.playlist.user?.avatar ||
    props.playlist.user_avatar ||
    null,
}));

const totalItems = computed(() => props.playlist.items_count || 0);
const totalDuration = computed(() => props.playlist.total_duration || 0);
const formattedDuration = computed(() => formatDuration(totalDuration.value));
const isFav = computed(
  () => props.isFavorite || props.playlist.is_favorited || false,
);

const isOwner = computed(() => {
  const uid = props.playlist.user?.id || props.playlist.user_id;
  return props.currentUserId && uid === props.currentUserId;
});

const emptyCoverLabel = computed(() => {
  if (isOwner.value) return "Ваши подборки";
  const ownerName = props.playlist.user?.display_name || author.value.username;
  return ownerName ? `Подборка ${ownerName}` : "Подборка пользователя";
});

const visibility = computed((): PlaylistVisibility => {
  if (props.playlist.visibility) return props.playlist.visibility;
  if (props.playlist.is_private) return "private";
  if (props.playlist.is_link_only) return "link";
  return "public";
});

const visibilityLabel = computed(() => {
  if (visibility.value === "private") return "Приватный";
  if (visibility.value === "link") return "По ссылке";
  return "Публичный";
});

const coverPosters = computed(() => {
  const result: Array<{ url: string | null; title: string }> = [];

  if (props.playlist.items && props.playlist.items.length > 0) {
    const count = Math.min(props.playlist.items.length, 3);
    for (let i = 0; i < count; i++) {
      const item = props.playlist.items[i];
      if (!item) continue;
      const animeObj =
        typeof item.anime === "object"
          ? (item.anime as { poster_url?: string; title_ru?: string; title_en?: string } | null)
          : null;
      const url = item.anime_poster || animeObj?.poster_url || null;
      const title =
        item.anime_title ||
        animeObj?.title_ru ||
        animeObj?.title_en ||
        "";
      result.push({ url, title });
    }
  } else if (
    props.playlist.cover_urls &&
    props.playlist.cover_urls.length > 0
  ) {
    const count = Math.min(props.playlist.cover_urls.length, 3);
    for (let i = 0; i < count; i++) {
      result.push({
        url: props.playlist.cover_urls[i] ?? null,
        title: `Аниме ${i + 1}`,
      });
    }
  }

  return result;
});

const formattedUpdatedAt = computed(() => {
  const date = new Date(props.playlist.updated_at);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return "Сегодня";
  if (days === 1) return "Вчера";
  if (days < 7) return `${days} дн. назад`;
  if (days < 30) return `${Math.floor(days / 7)} нед. назад`;
  if (days < 365) return `${Math.floor(days / 30)} мес. назад`;
  return `${Math.floor(days / 365)} г. назад`;
});

const handleClick = () => {
  router.push({ path: `/playlist/${props.playlist.id}`, query: route.path === "/playlists" ? { returnTo: route.fullPath } : {} });
  emit("click", props.playlist);
};

const goToAuthor = (e: Event) => {
  e.stopPropagation();
  const uid = author.value.id;
  if (uid) router.push(`/profile/${uid}`);
};

const toggleFavorite = (e: Event) => {
  e.stopPropagation();
  emit("favoriteToggle", props.playlist.id, !isFav.value);
};

const sharePlaylist = (e: Event) => {
  e.stopPropagation();
  emit("share", props.playlist.id);
};

const handleEdit = (e: Event) => {
  e.stopPropagation();
  emit("edit", props.playlist);
};

const handleDelete = (e: Event) => {
  e.stopPropagation();
  emit("delete", props.playlist);
};

</script>

<style>
.playlist-card {
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
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
  contain: layout style paint;
}

.playlist-card:hover {
  transform: translateY(-4px);
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border-subtle));
  box-shadow:
    0 18px 40px -18px rgba(0, 0, 0, 0.65),
    0 0 0 1px color-mix(in srgb, var(--accent) 22%, transparent);
}
</style>

<style scoped>
.playlist-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 2 / 3;
  flex-shrink: 0;
  background: var(--surface-4);
  overflow: hidden;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
}

.cover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(8, 8, 9, 0.45) 0%,
    rgba(8, 8, 9, 0) 38%,
    rgba(8, 8, 9, 0) 68%
  );
  pointer-events: none;
  z-index: 2;
}

.hover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.12);
  pointer-events: none;
  z-index: 3;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.playlist-card:hover .hover-overlay {
  opacity: 1;
}

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
  z-index: 11;
}

.playlist-card:hover .card-actions {
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
  color: #fb24cc;
}

.action-btn.is-active:hover {
  background: #fb24cc;
  color: #fff;
}

.action-btn.danger-btn:hover {
  background: #ef4444;
  border-color: transparent;
  color: #fff;
}

.privacy-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  z-index: 6;
}

.privacy-public {
  background: rgba(34, 197, 94, 0.85);
  color: #fff;
}
.privacy-private {
  background: rgba(239, 68, 68, 0.85);
  color: #fff;
}
.privacy-link {
  background: rgba(58, 134, 255, 0.85);
  color: #fff;
}

.items-count-badge,
.duration-badge {
  position: absolute;
  bottom: 10px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 10px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  z-index: 6;
  border: 1px solid rgba(255, 255, 255, 0.06);
  line-height: 1;
}

.items-count-badge {
  left: 10px;
}

.duration-badge {
  right: 10px;
}

.items-count-badge svg,
.duration-badge svg {
  color: var(--accent);
  flex-shrink: 0;
}

.playlist-info {
  padding: 12px 13px 14px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  flex: 1;
  min-width: 0;
}

.playlist-title {
  font-size: 14px;
  font-weight: 650;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.35;
  letter-spacing: -0.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  min-height: calc(1.3 * 1.35em);
  transition: color 0.2s ease;
}

.playlist-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 16px;
}

.playlist-author {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
  min-height: 22px;
  cursor: pointer;
  transition: color 0.2s ease;
  background: none; border: 0; padding: 0; text-align: left; width: 100%;
}

.playlist-card:hover .playlist-title {
  color: var(--accent);
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

.meta-item svg {
  color: #fbbf24;
  flex-shrink: 0;
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

.playlist-author:hover .author-name {
  color: var(--accent);
}

.author-avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.author-avatar-ph {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}

.author-name {
  font-size: 11.5px;
  font-weight: 500;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.2s ease;
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

  .playlist-info {
    padding: 10px 11px 12px;
    gap: 6px;
  }

  .playlist-title {
    font-size: 13px;
  }

  .privacy-badge {
    width: 26px;
    height: 26px;
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

  .privacy-badge {
    top: 8px;
    right: 8px;
    width: 24px;
    height: 24px;
    border-radius: 8px;
  }

  .items-count-badge,
  .duration-badge {
    bottom: 8px;
    padding: 4px 8px;
    font-size: 11px;
  }

  .items-count-badge {
    left: 8px;
  }

  .duration-badge {
    right: 8px;
  }
}
.playlist-like { position: absolute; right: 8px; bottom: 48px; z-index: 12; min-width: 44px; min-height: 44px; max-width: calc(100% - 16px); display: flex; align-items: center; justify-content: center; gap: 5px; padding: 6px 10px; border: 1px solid #ffffff40; border-radius: 12px; color: #fff; background: #15151be8; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }
.playlist-like.is-liked { color: #ffa5c5; }
.playlist-like.is-pending { opacity: 0.8; cursor: wait; }
.playlist-like.is-pending::after { content: ""; position: absolute; right: 3px; top: 3px; width: 8px; height: 8px; border: 1px solid currentColor; border-right-color: transparent; border-radius: 50%; animation: like-saving 0.6s linear infinite; }
@keyframes like-saving { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .playlist-like.is-pending::after { animation: none; } }
.playlist-like.has-error { border-color: var(--accent); }
.like-error { position: absolute; bottom: 98px; left: 6px; right: 6px; padding: 5px; z-index: 13; color: var(--text-primary); background: var(--surface-3); font-size: 11px; border-radius: 6px; }
.card-topics { position: absolute; top: 46px; right: 6px; max-width: calc(100% - 55px); display: flex; flex-direction: column; align-items: end; gap: 3px; z-index: 6; pointer-events: none; }
.card-topics span { max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 10px; padding: 3px 5px; background: #15151bd9; color: #fff; border-radius: 6px; }
.playlist-card:focus-visible, .playlist-card :focus-visible { outline: 2px solid var(--accent); outline-offset: -3px; }
.playlist-card:focus-within .card-actions { opacity: 1; transform: none; }
@media (hover: none) { .card-actions { opacity: 1; transform: none; } }
.compact-actions-button, .compact-item-count, .duration-short { display: none; }
.playlist-card { container-type: inline-size; }
.playlist-actions-dialog { width: min(360px, calc(100vw - 24px)); max-height: calc(100dvh - 32px); overflow: auto; margin: auto; padding: 1rem; background: var(--surface-3); color: var(--text-primary); border: 1px solid var(--border-strong); border-radius: var(--radius-lg); }
.playlist-actions-dialog::backdrop { background: #0009; }
.playlist-actions-dialog h3 { margin: 0 0 0.5rem; font-size: 1rem; overflow-wrap: anywhere; }
.playlist-actions-dialog p { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
.playlist-actions-dialog button { display: block; width: 100%; min-height: 44px; margin-top: 0.5rem; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); background: var(--surface-4); color: var(--text-primary); }
.playlist-actions-dialog button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
@container (max-width: 140px) {
  .card-actions { display: none; }
  .compact-actions-button { display: flex; position: absolute; top: 8px; left: 8px; width: 36px; height: 36px; z-index: 12; }
  .card-topics { display: none; }
}
@container (max-width: 180px) {
  .duration-full { display: none; }
  .duration-short { display: inline; }
}
@container (max-width: 120px) {
  .playlist-like { bottom: 8px; gap: 3px; padding: 4px; font-size: 11px; }
  .playlist-like svg { width: 16px; flex-shrink: 0; }
  .like-error { bottom: 56px; font-size: 10px; }
  .items-count-badge, .duration-badge, .playlist-description { display: none; }
  .compact-item-count { display: block; grid-row: 4; font-size: 11px; line-height: 14px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; }
}
</style>

<style>
@import './catalogCardGeometry.css';
</style>
