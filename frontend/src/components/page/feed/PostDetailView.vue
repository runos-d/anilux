<template>
  <main class="post-page">
    <button class="back-button" type="button" @click="$router.back()">
      <SakuraIcon name="arrow-left" :size="16" />
      <span>Назад</span>
    </button>

    <p v-if="error" class="post-page__alert" role="alert">{{ error }}</p>
    <p v-else-if="loading && !post" class="post-page__loading">Загрузка поста…</p>

    <template v-if="post && !post.is_deleted">
      <h1 class="post-page__title">
        {{ seoPage?.status === 200 ? seoPage.h1 : post.title || 'Пост' }}
      </h1>

      <PostCard
        :post="post"
        :comments-inline="false"
        @like="react('like')"
        @dislike="react('dislike')"
        @comment="scrollToComments"
        @bookmark="bookmark"
        @menu="showMenu = true"
        @repost="showRepost = true"
        @share="showRepost = true"
      />

      <div ref="commentsSection" class="post-page__comments">
        <CommentSection :key="String(post.id)" :post-id="post.id" :post="post" />
      </div>

      <PostMenu
        v-if="showMenu"
        :post="post"
        @close="showMenu = false"
        @edit="openEditor"
        @delete="deleted"
        @bookmark="bookmark"
        @hide="deleted"
        @hide-author="deleted"
      />

      <EditPostModal
        v-if="showEdit"
        ref="editModal"
        :post="post"
        @open-attach="openEditAttach"
        @close="closeEditor"
        @updated="loadPost"
      />

      <AttachModal
        v-if="attachVisible"
        v-model="attachTab"
        v-model:selected-animes="selectedAnimes"
        v-model:selected-playlists="selectedPlaylists"
        v-model:selected-media-files="selectedMedia"
        v-model:selected-excerpts="selectedExcerpts"
        @close="closeAttachments"
        @confirm="confirmAttachments"
      />

      <RepostModal
        v-if="showRepost"
        :post="post"
        @close="showRepost = false"
        @reposted="loadPost"
      />
    </template>

    <p v-else-if="post?.is_deleted" class="post-page__alert">
      Пост удалён или недоступен.
    </p>
  </main>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { seoPage } from '@/composables/useSeo';
import { useCachedReads } from '@/composables/useCachedReads';
import apiClient from '@/api/client';
import { useAuthStore } from '@/stores/auth';
import { usePostStore } from '@/stores/posts';

import SakuraIcon from '@/components/icons/SakuraIcon.vue';
import PostCard from '@/components/feed/PostCard.vue';
import CommentSection from '@/components/feed/CommentSection.vue';
import PostMenu from '@/components/feed/PostMenu.vue';
import EditPostModal from '@/components/feed/EditPostModal.vue';
import RepostModal from '@/components/feed/RepostModal.vue';
import AttachModal from '@/components/feed/AttachModal.vue';

import type { AnimeCard, FeedPost, PlaylistCard } from '@/api/feed';
import type { Excerpt } from '@/api/excerpts';

/* ── Stores / router ─────────────────────────────────────── */
const route = useRoute();
const auth = useAuthStore();
const store = usePostStore();
const read = useCachedReads();

/* ── Состояние страницы ─────────────────────────────────── */
const resolvedId = ref('');
const post = computed(() => store.entities[resolvedId.value]);
const loading = ref(false);
const error = ref('');

const showMenu = ref(false);
const showEdit = ref(false);
const editModal = ref<InstanceType<typeof EditPostModal> | null>(null);
const showRepost = ref(false);

const commentsSection = ref<HTMLElement | null>(null);

/* ── Вложения из редактора ──────────────────────────────── */
const attachVisible = ref(false);
const attachTab = ref<'anime' | 'playlist' | 'media' | 'excerpt'>('anime');
const selectedAnimes = ref<AnimeCard[]>([]);
const selectedPlaylists = ref<PlaylistCard[]>([]);
const selectedMedia = ref<{ type: string; url: string; file: File }[]>([]);
const selectedExcerpts = ref<Excerpt[]>([]);

/* ── Действия ───────────────────────────────────────────── */
function openEditor() {
  showEdit.value = true;
  showMenu.value = false;
}

function scrollToComments() {
  commentsSection.value?.scrollIntoView({ behavior: 'smooth' });
}

function openEditAttach(tab: typeof attachTab.value) {
  const editor = editModal.value;
  if (!editor) return;
  selectedAnimes.value = [...editor.editAttachPreviewAnime];
  selectedPlaylists.value = [...editor.editAttachPreviewPlaylist];
  selectedMedia.value = [...editor.editAttachPreviewMedia];
  selectedExcerpts.value = [...editor.editAttachPreviewExcerpts];
  attachTab.value = tab;
  attachVisible.value = true;
}

function closeAttachments() {
  const retained = new Set(
    editModal.value?.editAttachPreviewMedia.map((row) => row.url) ?? [],
  );
  for (const row of selectedMedia.value) {
    if (!retained.has(row.url)) URL.revokeObjectURL(row.url);
  }
  selectedMedia.value = [];
  attachVisible.value = false;
}

function confirmAttachments() {
  editModal.value?.onAttachConfirmFromEdit(
    selectedAnimes.value,
    selectedPlaylists.value,
    selectedMedia.value,
    selectedExcerpts.value,
  );
  attachVisible.value = false;
}

function closeEditor() {
  closeAttachments();
  showEdit.value = false;
}

onBeforeUnmount(closeAttachments);

/* ── Загрузка поста ─────────────────────────────────────── */
async function loadPost() {
  const id = String(route.params.id);
  const generation = store.sessionGeneration;

  loading.value = true;
  error.value = '';

  try {
    const data = await read(
      ['post', id],
      async (signal) =>
        (
          await apiClient.get<FeedPost>(
            `/social/posts/${id}/${auth.isAuthenticated ? '' : 'public/'}`,
            { signal },
          )
        ).data,
      (data) => {
        if (
          id === String(route.params.id) &&
          generation === store.sessionGeneration
        ) {
          resolvedId.value = String(store.upsert(data).id);
        }
      },
    );

    if (
      id !== String(route.params.id) ||
      generation !== store.sessionGeneration
    ) {
      return;
    }

    resolvedId.value = String(store.upsert(data).id);

    if (auth.isAuthenticated) {
      void apiClient
        .post(`/social/posts/${data.id}/view/`)
        .catch(() => undefined);
    }
  } catch (failure) {
    const stillRelevant =
      id === String(route.params.id) &&
      generation === store.sessionGeneration;
    if (stillRelevant) {
      error.value =
        (failure as { response?: { status: number } }).response?.status === 404
          ? 'Пост удалён или недоступен.'
          : 'Не удалось загрузить пост. Попробуйте ещё раз.';
    }
  } finally {
    if (id === String(route.params.id)) loading.value = false;
  }
}

/* ── Реакции / закладки / удаление ──────────────────────── */
async function react(reaction: 'like' | 'dislike') {
  if (!post.value || !auth.isAuthenticated) return;
  try {
    await store.react(post.value, reaction);
  } catch {
    error.value = 'Не удалось сохранить реакцию.';
  }
}

async function bookmark() {
  if (!post.value || !auth.isAuthenticated) return;
  const generation = store.sessionGeneration;
  const current = post.value;
  try {
    const { data } = await apiClient.post(
      `/social/posts/${current.id}/bookmark/`,
      {
        active: !current.is_bookmarked,
        client_action_id: crypto.randomUUID(),
      },
    );
    if (generation === store.sessionGeneration) {
      current.is_bookmarked = data.bookmarked ?? data.is_bookmarked;
    }
  } catch {
    error.value = 'Не удалось сохранить закладку.';
  }
}

function deleted() {
  if (post.value) post.value.is_deleted = true;
  showMenu.value = false;
}

/* ── Watch ──────────────────────────────────────────────── */
watch(
  () => [route.params.id, auth.user?.id],
  () => {
    resolvedId.value = String(route.params.id);
    showMenu.value = false;
    showEdit.value = false;
    showRepost.value = false;
    void loadPost();
  },
  { immediate: true },
);
</script>

<style scoped>
.post-page {
  max-width: 48rem;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* ── Кнопка «Назад» ──────────────────────────────────────── */
.back-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  align-self: flex-start;
  padding: 6px 12px 6px 8px;
  margin: 0;
  background: transparent;
  border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.08));
  border-radius: 10px;
  color: var(--text-secondary, #a5a5ad);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition:
    color 0.15s ease,
    background-color 0.15s ease,
    border-color 0.15s ease;
}

.back-button:hover {
  color: var(--text-primary, #fff);
  background: var(--surface-3, rgba(255, 255, 255, 0.04));
  border-color: var(--border-default, rgba(255, 255, 255, 0.16));
}

.back-button:focus-visible {
  outline: 2px solid var(--accent, #3a86ff);
  outline-offset: 2px;
}

/* ── Заголовок ──────────────────────────────────────────── */
.post-page__title {
  margin: 0 0 0.25rem;
  font-size: clamp(1.35rem, 1.1rem + 1vw, 1.75rem);
  font-weight: 700;
  line-height: 1.25;
  color: var(--text-primary, #fff);
  letter-spacing: -0.01em;
}

/* ── Текстовые состояния ───────────────────────────────── */
.post-page__loading {
  margin: 0;
  color: var(--text-tertiary, #777);
  font-size: 14px;
}

.post-page__alert {
  margin: 0;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary, #fff);
  background: color-mix(in srgb, var(--accent, #3a86ff) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent, #3a86ff) 35%, transparent);
}

/* ── Комментарии ───────────────────────────────────────── */
.post-page__comments {
  margin-top: 0.5rem;
  scroll-margin-top: 1rem;
}
</style>