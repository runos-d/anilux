<template>
  <div :class="['comment-section', modeClass]">
    <div class="comment-section__header">
      <h3 class="comment-section__title">Комментарии</h3>
      <span class="comment-section__count">{{ comments.length }}</span>
      <div class="comment-section__sort">
        <button
          :class="['comment-section__sort-btn', { active: sortBy === 'top' }]"
          @click="sortBy = 'top'"
        >
          Лучшие
        </button>
        <button
          :class="['comment-section__sort-btn', { active: sortBy === 'new' }]"
          @click="sortBy = 'new'"
        >
          Новые
        </button>
        <button
          :class="['comment-section__sort-btn', { active: sortBy === 'old' }]"
          @click="sortBy = 'old'"
        >
          Старые
        </button>
      </div>
    </div>

    <div v-if="loading" class="comment-section__loading">
      <div class="comment-section__spinner"></div>
    </div>

    <div v-else-if="!loading && comments.length === 0" class="comment-section__empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.77 9.77 0 01-3.5-.5L3 21l1.5-4.5A8.96 8.96 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <p>Пока нет комментариев</p>
      <span>Будьте первым, кто оставит комментарий</span>
    </div>

    <div v-else class="comment-section__list">
      <template v-for="comment in visibleRoots" :key="comment.id">
        <CommentItem
          :comment="comment"
          :post-id="postId"
          :reply-to-username="comment.parent_username"
          :children="getChildren(comment.id)"
          @reply="onReply"
          @reply-created="onReplyCreated"
          @updated="onCommentUpdated.bind(null, comment.id)"
          @deleted="onCommentDeleted.bind(null, comment.id)"
        />
      </template>
    </div>

    <p v-if="error" role="alert">{{ error }}</p>
    <button v-if="comments.length < total" :disabled="loadingMore" @click="loadMore">{{ loadingMore ? 'Загрузка…' : 'Показать ещё' }}</button>
    <div v-if="replyingTo" class="comment-section__replying-bar">
      <span>Ответ на <strong>@{{ replyingTo.author_username }}</strong></span>
      <button class="comment-section__cancel-reply" @click="cancelReply">
        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
          <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" />
        </svg>
      </button>
    </div>

    <div v-if="currentUser && post?.allow_comments !== false" class="comment-section__input">
      <img
        :src="currentUserAvatar"
        alt=""
        class="comment-section__input-avatar"
      />
      <div class="comment-section__input-wrap">
        <textarea
          ref="input"
          v-model="newComment"
          class="comment-section__textarea"
          :placeholder="inputPlaceholder"
          rows="2"
          @keydown.enter.exact.prevent="submitComment"
        />
        <button
          class="comment-section__send"
          :disabled="!canSubmit"
          @click="submitComment"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
    <p v-else>{{ currentUser ? 'Комментарии к этому посту отключены.' : 'Войдите, чтобы оставить комментарий.' }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { useAuthStore } from "@/stores/auth";
import { commentsApi } from "@/api/feed";
import type { PostComment } from "@/api/feed";
import CommentItem from "@/components/feed/PostComment.vue";
import { useCachedReads } from '@/composables/useCachedReads';
import { isRequestCancelled } from '@/api/client';
import { usePostStore } from '@/stores/posts';

const props = defineProps<{
  postId: string | number;
  post?: {
    comments_count: number;
    author_username: string;
    author_avatar: string | null;
    allow_comments?: boolean;
  } | null;
  mode?: "inline" | "modal";
  sort?: "top" | "new" | "old";
}>();

const emit = defineEmits<{
  "comment-added": [comment: PostComment];
}>();

const authStore = useAuthStore();
const read = useCachedReads();
const posts = usePostStore();
const currentUser = computed(() => authStore.user);

const comments = ref<PostComment[]>([]);
const loading = ref(false);
const sending = ref(false);
const page = ref(1);
const total = ref(0);
const loadingMore = ref(false);
const error = ref('');
const commentClientId = ref<string>(crypto.randomUUID());
const input = ref<HTMLTextAreaElement | null>(null);
const newComment = ref("");
const sortBy = ref<"top" | "new" | "old">(props.sort || "top");
const replyingTo = ref<PostComment | null>(null);
const commentMap = ref(new Map<string | number, PostComment>());
const childrenMap = ref(new Map<string | number, PostComment[]>());

const currentUserAvatar = computed(() => {
  const avatar = currentUser.value?.avatar;
  if (avatar) return avatar;
  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3Ccircle cx='20' cy='15' r='6' fill='%23666'/%3E%3Cpath d='M8 36c0-6.627 5.373-12 12-12s12 5.373 12 12' fill='%23666'/%3E%3C/svg%3E`;
});

const modeClass = computed(() => (props.mode === "modal" ? "comment-section--modal" : "comment-section--inline"));

const inputPlaceholder = computed(() => {
  if (replyingTo.value) {
    return `Ответить @${replyingTo.value.author_username}...`;
  }
  return "Написать комментарий...";
});

const canSubmit = computed(() => !!currentUser.value && props.post?.allow_comments !== false && newComment.value.trim().length > 0 && !sending.value);

const visibleRoots = computed(() => {
  const roots = comments.value.filter((c) => !c.parent_id || c.level === 0);
  if (sortBy.value === "new") {
    return [...roots].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }
  if (sortBy.value === "old") {
    return [...roots].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  }
  return [...roots].sort((a, b) => (b.likes_count || 0) - (a.likes_count || 0));
});

function buildCommentMap(list: PostComment[]) {
  const map = new Map<string | number, PostComment>();
  for (const c of list) {
    map.set(c.id, c);
  }
  return map;
}

function buildTree(list: PostComment[]) {
  const map = new Map<string | number, PostComment[]>();
  for (const c of list) {
    if (c.parent_id) {
      const siblings = [...(map.get(c.parent_id) || []), c];
      map.set(c.parent_id, siblings);
    }
  }
  childrenMap.value = map;
}

function getChildren(parentId: string | number): PostComment[] {
  return childrenMap.value.get(parentId) || [];
}

async function loadComments() {
  if (!props.postId) return;
  loading.value = true;
  error.value = '';
  try {
    await read(['post-comments', props.postId], async () => {
      const response = await commentsApi.getCommentsTree(props.postId);
      return { rows: response.data, total: Number(response.headers['x-total-count'] || response.data.length) };
    }, data => {
      page.value = 1; total.value = data.total; comments.value = data.rows;
      commentMap.value = buildCommentMap(data.rows); buildTree(data.rows);
    });
  } catch (failure) {
    if (!isRequestCancelled(failure)) error.value = 'Не удалось загрузить комментарии';
  } finally {
    loading.value = false;
  }
}

async function loadMore() {
  if (loadingMore.value) return;
  loadingMore.value = true;
  try {
    const response = await commentsApi.getCommentsTree(props.postId, page.value + 1);
    const known = new Set(comments.value.map(row => String(row.id)));
    comments.value.push(...response.data.filter(row => !known.has(String(row.id))));
    page.value++; total.value = Number(response.headers['x-total-count'] || comments.value.length);
    commentMap.value = buildCommentMap(comments.value); buildTree(comments.value);
  } catch { error.value = 'Не удалось загрузить следующую страницу'; }
  finally { loadingMore.value = false; }
}

function onReply(comment: PostComment) {
  replyingTo.value = comment;
  newComment.value = "";
}

function cancelReply() {
  replyingTo.value = null;
  newComment.value = "";
}

async function submitComment() {
  const text = newComment.value.trim();
  if (!canSubmit.value) return;

  sending.value = true;
  try {
    const { data } = await commentsApi.createComment(props.postId, text, replyingTo.value?.id || undefined, commentClientId.value);
    const created = data as PostComment;

    if (!comments.value.some(row => String(row.id) === String(created.id))) comments.value.push(created);
    commentMap.value.set(created.id, created);

    if (created.parent_id) {
      const siblings = [...(childrenMap.value.get(created.parent_id) || []), created];
      childrenMap.value.set(created.parent_id, siblings);
    }

    emit("comment-added", created);
    void posts.refresh(props.postId);
    commentClientId.value = crypto.randomUUID();
    newComment.value = "";
    replyingTo.value = null;
  } catch (failure) {
    if (!isRequestCancelled(failure)) error.value = 'Не удалось отправить комментарий. Повторите отправку.';
  } finally {
    sending.value = false;
    await nextTick(); input.value?.focus();
  }
}

function onReplyCreated(created: PostComment) {
  comments.value.push(created);
  commentMap.value.set(created.id, created);

  if (created.parent_id) {
    const siblings = [...(childrenMap.value.get(created.parent_id) || []), created];
    childrenMap.value.set(created.parent_id, siblings);
  }

  emit("comment-added", created);
  void posts.refresh(props.postId);
}

async function onCommentUpdated(commentId: string | number) {
  const target = commentMap.value.get(commentId);
  if (!target) return;
  try {
    const { data } = await commentsApi.getCommentsTree(props.postId);
    const refreshed = data.find((c) => c.id === commentId);
    if (refreshed) {
      Object.assign(target, refreshed);
    }
  } catch (error) {
    console.error("Failed to refresh comment:", error);
  }
}

async function onCommentDeleted(_commentId: string | number) {
  await loadComments();
  void posts.refresh(props.postId);
}

watch(() => props.postId, () => {
  if (props.postId) {
    loadComments();
  }
}, { immediate: true });

watch(
  () => props.post,
  (newPost) => {
    if (newPost && newPost.comments_count === 0 && comments.value.length === 0) {
      loadComments();
    }
  }
);
</script>

<style scoped>
.comment-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comment-section--modal {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.comment-section--inline {
  border-top: 1px solid var(--border-subtle);
  padding-top: 12px;
}

.comment-section__header {
  display: flex;
  flex-wrap: wrap;
  min-width: 0;
  align-items: center;
  gap: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-subtle);
}

.comment-section__title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.comment-section__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  background: var(--surface-4);
  color: var(--text-secondary);
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.comment-section__sort {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-left: auto;
}

.comment-section__sort-btn {
  padding: 4px 12px;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.comment-section__sort-btn:hover {
  color: var(--text-primary);
  background: var(--surface-4);
}

.comment-section__sort-btn.active {
  background: var(--accent);
  color: #fff;
}

.comment-section__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2.5rem;
}

.comment-section__spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.comment-section__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 2rem;
  color: var(--text-tertiary);
  text-align: center;
}

.comment-section__empty p {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.comment-section__empty span {
  font-size: 0.85rem;
}

.comment-section__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comment-section--modal .comment-section__list {
  flex: 1;
  padding: 2px 0 8px;
}

.comment-section__replying-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  border-radius: var(--radius-lg);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.comment-section__replying-bar strong {
  color: var(--text-primary);
}

.comment-section__cancel-reply {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.comment-section__cancel-reply:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.comment-section__input {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding-top: 8px;
  border-top: 1px solid var(--border-subtle);
}

.comment-section--modal .comment-section__input {
  position: sticky;
  bottom: -22px;
  z-index: 2;
  margin: auto -2px -22px;
  padding: 14px 2px 22px;
  background: linear-gradient(to bottom, transparent, var(--surface-2) 18%);
}

.comment-section__input-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  margin-top: 4px;
}

.comment-section__input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 6px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.comment-section__input-wrap:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent);
}

.comment-section__textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-family: inherit;
  resize: none;
  justify-content: center;
  outline: none;
  padding: 6px 8px;
  line-height: 1.5;
  min-height: 40px;
  max-height: 160px;
}

.comment-section__textarea::placeholder {
  color: var(--text-tertiary);
}

.comment-section__send {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  min-width: 34px;
  min-height: 34px;
  border-radius: var(--radius-full);
  border: none;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  margin-left: 8px;
  padding-right: 2px;
  transition: all 0.2s ease;
}

.comment-section__send:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.05);
}

.comment-section__send:active:not(:disabled) {
  transform: scale(0.95);
}

.comment-section__send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .comment-section__sort { width: 100%; margin-left: 0; }
  .comment-section__sort-btn { flex: 1; }
  .comment-section--modal .comment-section__input { bottom: -16px; margin-bottom: -16px; padding-bottom: 16px; }
}
</style>
