<template>
  <div v-if="!post.is_deleted" class="post-card" :class="{ pinned: post.is_pinned }">
    <div v-if="post.is_pinned" class="pinned-badge">
      <SakuraIcon name="pin" /> Закреплён
    </div>

    <div class="post-header">
      <div class="author-info" @click.stop="goToProfile">
        <OptimizedImage
          :src="post.author_avatar || defaultAvatar"
          class="avatar"
          alt=""
        />
        <div class="author-details">
          <div class="author-name">
            <span class="display-name">{{
              post.author_display_name || post.author_username
            }}</span>
            <span v-if="post.author_display_name" class="username"
              >@{{ post.author_username }}</span
            >
          </div>
          <div class="post-meta">
            <span v-if="post.group" class="group-badge"
              ><SakuraIcon name="folder" /> {{ post.group.name }}</span
            >
            <span class="time">{{ formatTime(post.created_at) }}</span>
            <span v-if="post.edited_at" class="edited">(ред.)</span>
            <span class="visibility-badge">
              <SakuraIcon
                v-if="isIconName(visibilityIcon(post.visibility))"
                :name="visibilityIcon(post.visibility)"
                :size="14"
              />
              <span v-else>{{ visibilityIcon(post.visibility) }}</span>
            </span>
          </div>
        </div>
      </div>
      <button class="menu-btn" aria-label="Действия с постом" @click.stop="$emit('menu', post)"><SakuraIcon name="more-horizontal" /></button>
    </div>

    <div class="post-content">
      <h3 v-if="displayTitle" class="post-title"><SakuraIcon v-if="post.post_type === 'system'" name="sparkles" :size="18" /> {{ displayTitle }}</h3>

      <div
        v-if="post.is_spoiler"
        class="spoiler-banner"
        :class="{ revealed: spoilerRevealed }"
      >
        <div class="spoiler-banner-left">
          <div class="spoiler-icon-wrap">
            <svg
              class="spoiler-svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <div class="spoiler-meta">
            <span class="spoiler-label">Спойлер</span>
            <span v-if="spoilerText" class="spoiler-subject">{{
              spoilerText
            }}</span>
          </div>
        </div>
        <button
          v-if="!spoilerRevealed"
          class="spoiler-reveal-btn"
          @click.stop="spoilerRevealed = true"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            width="16"
            height="16"
          >
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          <span>Показать</span>
        </button>
        <button
          v-else
          class="spoiler-hide-btn"
          @click.stop="spoilerRevealed = false"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            width="16"
            height="16"
          >
            <path
              d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
            />
            <line x1="1" y1="1" x2="23" y2="23" />
          </svg>
          <span>Скрыть</span>
        </button>
      </div>

      <div
        v-if="!post.is_spoiler || spoilerRevealed"
        class="post-body"
        :class="{ 'has-spoiler': post.is_spoiler }"
      >
        <div v-if="post.text" class="post-text-wrap">
          <div
            class="post-text"
            :class="{ 'is-collapsed': isCollapsed && isLong }"
            v-html="formattedText"
          ></div>
          <button
            v-if="isLong"
            class="expand-btn"
            @click.stop="isCollapsed = !isCollapsed"
          >
              <SakuraIcon :name="isCollapsed ? 'chevron-down' : 'chevron-up'" :size="16" />
              {{ isCollapsed ? "Показать полностью" : "Свернуть" }}
          </button>
        </div>

        <div v-if="post.hashtags?.length" class="hashtags">
          <span
            v-for="tag in post.hashtags"
            :key="tag"
            class="hashtag"
            @click.stop="goToTag(tag)"
            >#{{ tag }}</span
          >
        </div>

        <ExcerptCard v-for="row in post.attachments_data?.filter(item => item.content_type === 'excerpt') || []" :key="String(row.id)" :excerpt="row.excerpt_data" />

        <AttachmentStack v-if="imageMedia.length" :count="imageMedia.length" :posters="imageMedia.map(item => item.thumbnail || item.url)" label="Фотографии" variant="media">
          <div class="media-gallery" :class="'grid-' + Math.min(imageMedia.length, 4)">
            <div v-for="(item, index) in imageMedia" :key="item.url" class="media-item" @click.stop="openMedia(index)">
              <OptimizedImage :src="item.url" :alt="item.caption || ''" layout="fullWidth" />
            </div>
          </div>
        </AttachmentStack>
<AttachmentStack
  v-if="videoMedia.length"
  :count="videoMedia.length"
  :posters="videoMedia.map(item => item.thumbnail || item.url)"
  label="Видео"
  variant="media"
>
  <div class="media-gallery" :class="'grid-' + Math.min(videoMedia.length, 4)">
    <div v-for="item in videoMedia" :key="item.url" class="media-item">
      <video :src="item.url" :poster="item.thumbnail" controls preload="none" @click.stop />
    </div>
  </div>
</AttachmentStack>
<AttachmentStack v-if="allAnimes.length" :count="allAnimes.length" :posters="allAnimes.map(item => getPosterUrl(item) || '')" label="Аниме">
  <div class="attachment-card-grid">
    <button v-for="anime in allAnimes" :key="String(anime.id)" type="button" class="post-attachment-card" @click.stop="$router.push('/anime/' + (anime.slug || anime.id))">
      <span class="post-attachment-cover">
        <OptimizedImage v-if="getPosterUrl(anime) && !failedPosters.has('anime-' + anime.id)" :src="getPosterUrl(anime) || ''" class="post-attachment-cover-image" alt="" @error="failedPosters.add('anime-' + anime.id)" />
        <span v-else class="post-attachment-cover-placeholder"><SakuraIcon name="image" /></span>
      </span>
      <span class="post-attachment-details">
        <span class="post-attachment-title">{{ anime.title_ru || anime.title_en || `Аниме #${anime.id}` }}</span>
        <span class="post-attachment-description">{{ truncateText(anime.overview || anime.description || 'Описание пока не добавлено', 90) }}</span>
        <span class="post-attachment-meta">
          <span v-if="anime.year">{{ anime.year }}</span>
          <span v-if="anime.rating" class="post-attachment-rating">★ {{ anime.rating }}</span>
        </span>
      </span>
      <SakuraIcon name="arrow-right" :size="16" class="post-attachment-arrow" />
    </button>
  </div>
</AttachmentStack>
<AttachmentStack v-if="allPlaylists.length" :count="allPlaylists.length" :posters="allPlaylists.map(item => getPosterUrl(item) || '')" label="Плейлисты">
  <div class="attachment-card-grid">
    <button v-for="playlist in allPlaylists" :key="String(playlist.id)" type="button" class="post-attachment-card" @click.stop="goToPlaylist(playlist)">
      <span class="post-attachment-cover">
        <OptimizedImage v-if="getPosterUrl(playlist) && !failedPosters.has('playlist-' + playlist.id)" :src="getPosterUrl(playlist) || ''" class="post-attachment-cover-image" alt="" @error="failedPosters.add('playlist-' + playlist.id)" />
        <span v-else class="post-attachment-cover-placeholder"><SakuraIcon name="folder" /></span>
      </span>
      <span class="post-attachment-details">
        <span class="post-attachment-title">{{ playlist.title || playlist.name || `Плейлист #${playlist.id}` }}</span>
        <span class="post-attachment-description">{{ truncateText(playlist.description || 'Описание пока не добавлено', 90) }}</span>
        <span class="post-attachment-meta">
          <span>{{ playlist.anime_count || playlist.items_count || 0 }} аниме</span>
        </span>
      </span>
      <SakuraIcon name="arrow-right" :size="16" class="post-attachment-arrow" />
    </button>
  </div>
</AttachmentStack>

        <div
          v-if="post.reactor_post"
          class="shorts-card"
          @click.stop="$router.push('/reactor/post/' + post.reactor_post.id)"
        >
          <div class="shorts-thumb">
            <video :src="post.reactor_post.video_url" muted></video>
          </div>
          <div class="shorts-info">
            <span class="shorts-title">{{ post.reactor_post.title }}</span>
            <span class="shorts-author"
              >@{{ post.reactor_post.user?.username }}</span
            >
          </div>
        </div>

        <div
          v-if="post.post_type === 'repost' && post.original_post"
          class="repost-wrap"
        >
          <QuoteCard
            :quote="{
              id: post.original_post.id,
              author: {
                id: post.original_post.author,
                username: post.original_post.author_username,
                avatar_url: post.original_post.author_avatar || undefined,
              },
              content: post.original_post.text,
              type: getQuoteType(post.original_post),
              anime: post.original_post.anime || undefined,
              timestamp: post.original_post.created_at,
              post_id: post.original_post.id,
            }"
            :can-click="true"
            :show-avatar="false"
            @click="goToPost(post.original_post.id)"
          />

          <div v-if="post.repost_comment" class="repost-comment">
            <div class="repost-comment-header">
              <OptimizedImage
                :src="post.author_avatar || defaultAvatar"
                class="repost-avatar"
                alt=""
              />
              <span class="repost-author">@{{ post.author_username }}</span>
            </div>
            <p class="repost-comment-text">{{ post.repost_comment }}</p>
          </div>

          <div
            class="original-post-preview"
            @click="goToPost(post.original_post.id)"
          >
            <div class="preview-header">
              <SakuraIcon name="refresh" :size="14" />
              <span>Оригинал поста</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="post-actions">
      <div class="action-group">
        <button
          class="action-btn"
          :class="{ liked: post.is_liked }"
          title="Нравится"
          aria-label="Нравится"
          :aria-pressed="!!post.is_liked"
          :disabled="!canReact"
          @click.stop="$emit('like', post)"
        >
          <SakuraIcon name="heart" /> <span>{{ fmt(post.likes_count) }}</span>
        </button>
        <button
          class="action-btn"
          :class="{ disliked: post.is_disliked }"
          title="Не нравится"
          aria-label="Не нравится"
          :aria-pressed="!!post.is_disliked"
          :disabled="!canReact"
          @click.stop="$emit('dislike', post)"
        >
          <SakuraIcon name="thumbs-down" />
          <span>{{ fmt(post.dislikes_count) }}</span>
        </button>
      </div>
      <div class="action-group">
        <button class="action-btn" aria-label="Комментарии" @click.stop="toggleComments">
          <SakuraIcon name="message" />
          <span>{{ fmt(post.comments_count) }}</span>
        </button>
      </div>
      <div class="action-group">
        <button
          class="action-btn"
          :class="{ bookmarked: post.is_bookmarked }"
          :aria-label="post.is_bookmarked ? 'Убрать из избранного' : 'В избранное'"
          :aria-pressed="!!post.is_bookmarked"
          @click.stop="$emit('bookmark', post)"
        >
          <SakuraIcon name="star" :solid="!!post.is_bookmarked" :size="20" />
        </button>
      </div>
    </div>

    <div v-if="showComments" class="inline-comments" @click.stop>
      <CommentSection :post-id="post.id" :post="post" @comment-added="refreshCommentsCount" />
    </div>

    <ImageLightbox
      v-if="showLightbox"
      :show="showLightbox"
      :images="lightboxImages"
      :initial-index="lightboxIndex"
      @close="showLightbox = false"
    />
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, ref, computed, watch } from "vue";
import ExcerptCard from "@/components/excerpts/ExcerptCard.vue";
import AttachmentStack from "./AttachmentStack.vue";
import { postAttachments } from "@/lib/postAttachments";
import { useRouter } from "vue-router";
import type { FeedPost, MediaFile, AnimeCard, PlaylistCard } from "@/api/feed";
import { usePostStore } from "@/stores/posts";
import { useAuthStore } from '@/stores/auth';
import { getMediaUrl } from "@/api/client";
const CommentSection = defineAsyncComponent(() => import("./CommentSection.vue"));
import QuoteCard from "@/components/ui/QuoteCard.vue";
import { postTitle } from '@/lib/systemUiText';
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
const ImageLightbox = defineAsyncComponent(() => import("@/components/Modals/ImageLightbox.vue"));
import { formatPostText } from '@/lib/postText';

const isIconName = (icon: string | undefined): boolean => {
  if (!icon) return false;
  return /^[a-zA-Z][a-zA-Z0-9-]*$/.test(icon);
};

type Post = FeedPost & {
  image_file?: string | null;
  video_file?: string | null;
  is_following?: boolean;
};

const props = defineProps<{
  post: Post;
  isRepost?: boolean;
  showCommentsPreview?: boolean;
  commentsInline?: boolean;
}>();
const emit = defineEmits<{
  like: [post: Post];
  dislike: [post: Post];
  comment: [post: Post];
  repost: [post: Post];
  share: [post: Post];
  bookmark: [post: Post];
  menu: [post: Post];
}>();

const router = useRouter();
const auth = useAuthStore();
const displayTitle = computed(() => postTitle(props.post.title, props.post.post_type));
const failedPosters = ref(new Set<string>());
const canReact = computed(() => !!auth.user && String(props.post.author) !== String(auth.user.id) && props.post.post_type !== 'system');
const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3C/svg%3E`;

const goToTag = (tag: string) => {
  const tagName = tag.replace(/^#/, "").trim();
  if (!tagName) return;
  router.push({ path: "/feed", query: { tag: tagName } });
};

watch(
  () => props.post.anime,
  (anime) => {
    if (anime) {
    }
  },
  { immediate: true },
);

const TEXT_LIMIT = 1000;
const isCollapsed = ref(true);
const isLong = computed(() => (props.post.text || "").length > TEXT_LIMIT);
const spoilerRevealed = ref(false);

const formattedText = computed(() => formatPostText(props.post.text || ''));

interface MediaItem {
  type: "image" | "video";
  url: string;
  thumbnail?: string;
  caption?: string;
}
const canonicalAttachments = computed(() => postAttachments(props.post));
const displayMedia = computed<MediaItem[]>(() => {
  const files = canonicalAttachments.value.media.map((item: MediaFile) => ({
    type: item.media_type, url: item.file_url || item.url || '',
    thumbnail: item.thumbnail_url || item.thumbnail || undefined, caption: item.caption || undefined,
  })).filter(item => !!item.url);
  if (!files.length && props.post.image_url) files.push({ type: 'image', url: props.post.image_url, thumbnail: undefined, caption: undefined });
  if (!files.length && props.post.video_url) files.push({ type: 'video', url: props.post.video_url, thumbnail: undefined, caption: undefined });
  return files;
});
const imageMedia = computed(() => displayMedia.value.filter(item => item.type === 'image'));
const videoMedia = computed(() => displayMedia.value.filter(item => item.type === 'video'));
const openMedia = (index: number) => {
  if (!imageMedia.value.length) return;
  lightboxImages.value = imageMedia.value.map((m) => m.url);
  lightboxIndex.value = index;
  showLightbox.value = true;
};

const showLightbox = ref(false);
const lightboxImages = ref<string[]>([]);
const lightboxIndex = ref(0);


const allAnimes = computed(() => canonicalAttachments.value.anime);

const allPlaylists = computed(() => canonicalAttachments.value.playlists);

const fmt = (n?: number) => {
  if (!n) return "0";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "М";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "К";
  return String(n);
};

const formatTime = (s: string) => {
  const d = new Date(s),
    now = Date.now(),
    diff = now - d.getTime();
  const m = Math.floor(diff / 60000),
    h = Math.floor(diff / 3600000),
    days = Math.floor(diff / 86400000);
  if (m < 1) return "только что";
  if (m < 60) return m + " мин.";
  if (h < 24) return h + " ч.";
  if (days < 7) return days + " дн.";
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
};

const visibilityIcon = (v?: string) => {
  const map: Record<string, string> = {
    public: "globe",
    followers: "users",
    friends: "users",
    private: "lock",
  };
  return map[v || "public"] || "globe";
};

const goToProfile = () => router.push(`/profile/${props.post.author_username}`);

const goToPlaylist = (playlist: PlaylistCard) => {
  if (playlist && playlist.id) {
    router.push(`/playlist/${playlist.id}`);
  }
};

const getSpoilerTitle = (spoilerFor: string | { title_ru?: string; title_en?: string } | null | undefined): string => {
  if (!spoilerFor) return "";
  if (typeof spoilerFor === "string") return spoilerFor;
  if (typeof spoilerFor === "object") {
    return spoilerFor.title_ru || spoilerFor.title_en || "";
  }
  return "";
};

const spoilerText = computed(() => {
  return (
    props.post.spoiler_description ||
    getSpoilerTitle(props.post.spoiler_for) ||
    ""
  );
});

const truncateText = (text: string, maxLength: number): string => {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
};

const getPosterUrl = (item: AnimeCard | PlaylistCard | null | undefined): string | undefined => {
  if (!item) return undefined;
  if ("cover_image" in item && item.cover_image) {
    return getMediaUrl(item.cover_image) ?? undefined;
  }
  const url = getMediaUrl(item.poster_url || (item as AnimeCard).poster);
  return url ?? undefined;
};

const showComments = ref(false);
const toggleComments = () => {
  if (props.commentsInline === false) emit('comment', props.post);
  else showComments.value = !showComments.value;
};
const refreshCommentsCount = () => { void usePostStore().refresh(props.post.id); };

const getQuoteType = (
  post: Post,
): "text" | "image" | "video" | "audio" | "file" => {
  if (post.media_files?.length) {
    const firstMedia = post.media_files[0];
    return firstMedia?.media_type === "video" ? "video" : "image";
  }
  if (post.image_url || post.image_file) return "image";
  if (post.video_url || post.video_file) return "video";
  return "text";
};

const goToPost = (postId: string | number) => {
  router.push(`/post/${postId}`);
};
</script>

<style scoped>
.post-card {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--surface-3) 28%, transparent), transparent 36%),
    var(--surface-2);
  padding: 1.05rem 1.125rem 0.75rem;
  margin-bottom: 0.75rem;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.12);
  transition: border-color 0.25s var(--ease-petal), box-shadow 0.25s var(--ease-petal);
}

.post-card:hover {
  border-color: var(--border-default);
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.18), var(--shadow-sm-petal-sm);
}

.post-card.pinned {
  border-color: var(--accent-subtle);
  background: linear-gradient(
    135deg,
    var(--accent-subtle) 0%,
    transparent 100%
  );
}

.pinned-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: linear-gradient(
    135deg,
    var(--accent) 0%,
    var(--accent-press) 100%
  );
  color: var(--text-on-accent);
  padding: 0.2rem 0.55rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
  margin-bottom: 0.6rem;
  box-shadow: var(--shadow-sm-petal-sm);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.6rem;
}

.author-info {
  display: flex;
  flex: 1;
  min-width: 0;
  gap: 0.6rem;
  cursor: pointer;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.author-details {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
}

.author-name {
  display: flex;
  flex-wrap: wrap;
  min-width: 0;
  align-items: center;
  gap: 0.35rem;
}

.display-name {
  overflow-wrap: anywhere;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 0.875rem;
}

.username {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-tertiary);
  font-size: 0.78rem;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.1rem;
  flex-wrap: wrap;
}

.group-badge {
  background: var(--surface-3);
  color: var(--text-secondary);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.68rem;
}

.time {
  color: var(--text-tertiary);
  font-size: 0.78rem;
}

.edited {
  color: var(--text-tertiary);
  font-size: 0.68rem;
  font-style: italic;
}

.visibility-badge {
  color: var(--text-tertiary);
  font-size: 0.78rem;
}

.menu-btn {
  flex-shrink: 0;
  min-width: 36px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: 6px;
  transition: all 0.2s var(--ease-petal);
}

.menu-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.post-content {
  margin-bottom: 0.75rem;
}

.post-title {
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.4rem;
}

.post-text-wrap {
  margin-bottom: 0.4rem;
}

.post-text {
  color: var(--text-secondary);
  line-height: 1.65;
  font-size: 0.9rem;
  word-break: break-word;
}

.post-text.is-collapsed {
  max-height: 400px;
  overflow: hidden;
  -webkit-mask-image: linear-gradient(to bottom, black 90%, transparent);
  mask-image: linear-gradient(to bottom, black 90%, transparent);
}

.expand-btn {
  background: none;
  border: none;
  color: var(--accent);
  cursor: pointer;
  font-size: 0.78rem;
  padding: 0.25rem 0;
  margin-top: 0.15rem;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  transition: color 0.2s var(--ease-petal);
}

.expand-btn:hover {
  color: var(--accent-press);
}

.hashtags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-bottom: 0.4rem;
}

.hashtag {
  color: var(--accent);
  cursor: pointer;
  font-size: 0.8rem;
  transition: color 0.2s var(--ease-petal);
}

.hashtag:hover {
  color: var(--accent-press);
}

.media-gallery {
  display: grid;
  gap: 4px;
  overflow: hidden;
  border-radius: 10px;
  background: var(--surface-1);
}

.media-gallery.grid-1 {
  grid-template-columns: 1fr;
}

.media-gallery.grid-2 {
  grid-template-columns: 1fr 1fr;
}

.media-gallery.grid-3 {
  grid-template-columns: 2fr 1fr;
  grid-template-rows: 1fr 1fr;
  height: min(430px, 62vw);
}

.media-gallery.grid-3 .media-item:first-child {
  grid-row: span 2;
}

.media-gallery.grid-4 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.media-item {
  position: relative;
  min-width: 0;
  overflow: hidden;
  background: var(--surface-1);
  cursor: pointer;
}

.media-gallery.grid-2 .media-item,
.media-gallery.grid-4 .media-item {
  aspect-ratio: 4 / 3;
}

.media-item :deep(img),
.media-item video {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 0;
  object-fit: cover;
  background: var(--surface-1);
}

.media-gallery.grid-1 .media-item :deep(img),
.media-gallery.grid-1 .media-item video {
  max-height: 540px;
  object-fit: contain;
}

.single-media {
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  background: var(--surface-2, #080808);
}

.single-media img,
.single-media video {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  background: var(--surface-2, #080808);
  display: block;
}

.attachment-card-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.35rem;
}

.post-attachment-card {
  display: flex;
  width: 100%;
  min-width: 0;
  height: 72px;
  align-items: center;
  gap: 0.65rem;
  padding: 0.35rem 0.55rem 0.35rem 0.4rem;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--surface-2);
  color: inherit;
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: background 0.2s var(--ease-petal), border-color 0.2s var(--ease-petal);
}

.post-attachment-card:hover,
.post-attachment-card:focus-visible {
  border-color: var(--border-default);
  background: var(--surface-3);
  outline: none;
}

.post-attachment-cover {
  display: block;
  width: 44px;
  height: 60px;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 7px;
  background: var(--surface-4);
}

.post-attachment-cover-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.post-attachment-cover-placeholder {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  background: var(--surface-4);
  color: var(--text-tertiary);
}

.post-attachment-details {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  justify-content: center;
  gap: 0.15rem;
}

.post-attachment-title {
  display: block;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 0.82rem;
  font-weight: 650;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-attachment-description {
  display: block;
  overflow: hidden;
  color: var(--text-tertiary);
  font-size: 0.69rem;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-attachment-meta {
  display: flex;
  min-height: 0.9rem;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-tertiary);
  font-size: 0.66rem;
  font-weight: 500;
  line-height: 1.2;
}

.post-attachment-rating { color: var(--warning); }

.post-attachment-arrow {
  flex-shrink: 0;
  color: var(--text-tertiary);
  opacity: 0.55;
  transition: color 0.2s var(--ease-petal), transform 0.2s var(--ease-petal);
}

.post-attachment-card:hover .post-attachment-arrow,
.post-attachment-card:focus-visible .post-attachment-arrow {
  color: var(--accent);
  opacity: 1;
  transform: translateX(2px);
}

.shorts-card {
  display: flex;
  gap: 0.65rem;
  background: var(--surface-2, #0e0e0e);
  border-radius: 10px;
  padding: 0.625rem;
  cursor: pointer;
  margin-bottom: 0.5rem;
  border: 1px solid var(--border-subtle, #151515);
}

.shorts-thumb {
  width: 54px;
  height: 80px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.shorts-thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.shorts-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  justify-content: center;
}

.shorts-title {
  color: var(--text-primary, #fff);
  font-size: 0.825rem;
  font-weight: 600;
}

.shorts-author {
  color: var(--text-tertiary, #555);
  font-size: 0.72rem;
}

.repost-wrap {
  border: 1px solid var(--border-subtle, #1a1a1a);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  background: var(--surface-3, #0f0f0f);
}

.repost-comment {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border-subtle);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-2, #0a0a0a);
}

.repost-comment-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.repost-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

.repost-author {
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--accent-bright);
}

.repost-comment-text {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.875rem;
  line-height: 1.5;
}

.original-post-preview {
  padding: 0.6rem 1rem;
  background: var(--surface-4, #151515);
  cursor: pointer;
  transition: background 0.15s;
}

.original-post-preview:hover {
  background: var(--surface-5, #1a1a1a);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-tertiary);
  font-size: 0.75rem;
}

.preview-header svg {
  color: var(--accent);
}

.post-actions {
  display: flex;
  justify-content: space-between;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-subtle);
}

.action-group {
  display: flex;
  gap: 0.15rem;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  color: var(--text-tertiary);
  padding: 0.35rem 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.15s var(--ease-petal);
}

.action-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}
.action-btn:disabled { opacity:0.45; cursor:default; }

.action-btn.liked {
  color: var(--danger);
}

.action-btn.disliked {
  color: var(--warning);
}

.action-btn.bookmarked {
  color: var(--accent);
}

.inline-comments {
  border-top: 1px solid var(--border-subtle, #111);
  margin-top: 0.6rem;
  padding-top: 0.6rem;
}

.comments-loading {
  display: flex;
  justify-content: center;
  padding: 0.875rem;
}

.spinner-sm {
  width: 18px;
  height: 18px;
  border: 2px solid var(--surface-4);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.comments-tree {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 0.6rem;
}

.no-comments {
  color: var(--text-tertiary);
  font-size: 0.8rem;
  text-align: center;
  padding: 0.875rem 0;
}

.comment-input-row {
  display: flex;
  gap: 0.4rem;
  align-items: flex-start;
}

.ci-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.2rem;
  border: 1px solid var(--accent-subtle);
}

.ci-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.comment-textarea {
  width: 100%;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.45rem 0.65rem;
  border-radius: 8px;
  font-size: 0.8rem;
  resize: none;
  font-family: inherit;
  transition: border-color 0.2s var(--ease-petal);
  box-sizing: border-box;
}

.comment-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.send-comment-btn {
  align-self: flex-end;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  padding: 0.35rem 0.875rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  transition: all 0.2s var(--ease-petal);
}

.send-comment-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-comment-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-sm-glow-sm);
}

:deep(.comment-node) {
  display: block;
}

:deep(.comment-node.is-reply) {
  margin-top: 0.3rem;
}

:deep(.comment-row) {
  display: flex;
  gap: 0.5rem;
  padding: 0.4rem 0 0.2rem;
}

:deep(.comment-replies) {
  margin-top: 0.5rem;
  padding-left: 0.75rem;
  border-left: 2px solid var(--border-subtle, #1a1a1a);
}

:deep(.c-avatar) {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  cursor: pointer;
  margin-top: 2px;
}

:deep(.c-body) {
  flex: 1;
  min-width: 0;
}

:deep(.c-header) {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.1rem;
  flex-wrap: wrap;
}

:deep(.c-author) {
  color: var(--text-primary, #fff);
  font-weight: 600;
  font-size: 0.78rem;
  cursor: pointer;
}

:deep(.c-author:hover) {
  text-decoration: underline;
}

:deep(.c-reply-arrow) {
  color: var(--text-tertiary, #444);
  font-size: 0.7rem;
}

:deep(.c-reply-to) {
  color: var(--accent, #7c5cfc);
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
}

:deep(.c-reply-to:hover) {
  text-decoration: underline;
  color: var(--accent-hover, #9d87ff);
}

:deep(.c-time) {
  color: var(--text-tertiary, #444);
  font-size: 0.68rem;
}

:deep(.c-text) {
  color: var(--text-secondary, #bbb);
  font-size: 0.8rem;
  line-height: 1.45;
  margin: 0 0 0.25rem;
  word-break: break-word;
}

:deep(.c-actions) {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  align-items: center;
}

:deep(.c-btn) {
  background: none;
  border: none;
  color: var(--text-tertiary, #666);
  font-size: 0.7rem;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  transition: all 0.15s;
}

:deep(.c-btn:hover) {
  background: var(--surface-3, #151515);
  color: var(--text-primary, #fff);
}

:deep(.c-btn.active) {
  color: #ef4444;
}

:deep(.c-toggle) {
  color: var(--accent, #7c5cfc) !important;
  font-weight: 500;
  background: rgba(124, 92, 252, 0.08);
  border-radius: 999px;
}

:deep(.c-toggle:hover) {
  background: rgba(124, 92, 252, 0.15) !important;
  color: var(--accent-hover, #9d87ff) !important;
}

:deep(.reply-form) {
  margin-top: 0.4rem;
  margin-bottom: 0.4rem;
}

:deep(.reply-textarea) {
  width: 100%;
  background: var(--surface-2, #0e0e0e);
  border: 1px solid var(--border-subtle, #1a1a1a);
  color: var(--text-primary, #ddd);
  padding: 0.4rem 0.6rem;
  border-radius: 8px;
  font-size: 0.8rem;
  resize: none;
  font-family: inherit;
  box-sizing: border-box;
}

:deep(.reply-textarea:focus) {
  outline: none;
  border-color: var(--accent, #7c5cfc);
}

:deep(.reply-actions) {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.4rem;
  justify-content: flex-end;
}

:deep(.reply-cancel) {
  background: none;
  border: 1px solid var(--border-subtle, #1a1a1a);
  color: var(--text-secondary, #777);
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.15s;
}

:deep(.reply-cancel:hover) {
  background: var(--surface-3, #151515);
  color: var(--text-primary, #fff);
}

:deep(.reply-send) {
  background: var(--accent, #7c5cfc);
  color: #fff;
  border: none;
  padding: 0.3rem 0.875rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.15s;
}

:deep(.reply-send:hover:not(:disabled)) {
  background: var(--accent-hover, #6b4de8);
}

:deep(.reply-send:disabled) {
  opacity: 0.4;
  cursor: not-allowed;
}

:deep(.ht) {
  color: var(--accent, #7c5cfc);
  cursor: pointer;
}

:deep(.mn) {
  color: var(--accent-hover, #9d87ff);
  cursor: pointer;
}

.spoiler-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(
    135deg,
    rgba(251, 191, 36, 0.08) 0%,
    rgba(251, 146, 60, 0.05) 100%
  );
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  transition: all 0.3s ease;
}

.spoiler-banner.revealed {
  background: linear-gradient(
    135deg,
    rgba(124, 92, 252, 0.06) 0%,
    rgba(118, 75, 162, 0.04) 100%
  );
  border-color: rgba(124, 92, 252, 0.15);
}

.spoiler-banner-left {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.spoiler-icon-wrap {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(251, 191, 36, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.spoiler-banner.revealed .spoiler-icon-wrap {
  background: rgba(124, 92, 252, 0.12);
}

.spoiler-svg {
  width: 16px;
  height: 16px;
  color: #fbbf24;
}

.spoiler-banner.revealed .spoiler-svg {
  color: var(--accent, #7c5cfc);
}

.spoiler-meta {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.spoiler-label {
  color: #fbbf24;
  font-weight: 600;
  font-size: 0.8rem;
  letter-spacing: 0.02em;
}

.spoiler-banner.revealed .spoiler-label {
  color: var(--accent, #7c5cfc);
}

.spoiler-subject {
  color: var(--text-secondary, #888);
  font-size: 0.75rem;
}

.spoiler-reveal-btn,
.spoiler-hide-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  padding: 0.4rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
}

.spoiler-reveal-btn:hover {
  background: rgba(251, 191, 36, 0.18);
  transform: translateY(-1px);
}

.spoiler-hide-btn {
  background: rgba(124, 92, 252, 0.1);
  border-color: rgba(124, 92, 252, 0.2);
  color: var(--accent, #7c5cfc);
}

.spoiler-hide-btn:hover {
  background: rgba(124, 92, 252, 0.18);
}

.post-body {
  transition: opacity 0.3s ease;
}

.post-body.has-spoiler {
  animation: content-reveal 0.4s ease-out;
}

@keyframes content-reveal {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
