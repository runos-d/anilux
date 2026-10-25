<template>
  <div
    class="comment"
    :class="{
      'comment--reply': comment.level > 0,
      'comment--deleted': comment.is_deleted,
      'comment--own': isOwnAuthor,
    }"
    :style="indentStyle"
  >
    <div class="comment__avatar">
      <router-link :to="`/profile/${comment.author_username}`">
        <img
          :src="avatarUrl"
          :alt="authorName"
          class="comment__avatar-img"
          loading="lazy"
        />
      </router-link>
    </div>

    <div class="comment__body">
      <div class="comment__header">
        <div class="comment__author-row">
          <router-link
            :to="`/profile/${comment.author_username}`"
            class="comment__author"
          >
            {{ authorName }}
          </router-link>

          <span class="comment__time">{{ formattedTime }}</span>
          <span v-if="isEdited" class="comment__edited">
            (ред.)
          </span>
        </div>

        <div v-if="canEdit || canDelete" class="comment__menu-wrap">
          <button
            class="comment__menu-btn"
            @click="menuOpen = !menuOpen"
            aria-label="Действия с комментарием"
          >
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z" />
            </svg>
          </button>
          <div v-if="menuOpen" class="comment__menu">
            <button
              v-if="canEdit"
              class="comment__menu-item"
              @click="startEdit"
            >
              Редактировать
            </button>
            <button
              v-if="canDelete"
              class="comment__menu-item comment__menu-item--danger"
              @click="confirmDelete"
            >
              Удалить
            </button>
          </div>
        </div>
      </div>

      <div v-if="comment.is_deleted" class="comment__deleted">
        [комментарий удалён]
      </div>

      <div v-else-if="editing" class="comment__edit-box">
        <textarea
          v-model="editDraft"
          class="comment__edit-area"
          rows="3"
          @keydown.ctrl.enter="submitEdit"
          @keydown.meta.enter="submitEdit"
        />
        <div class="comment__edit-actions">
          <button
            class="comment__btn comment__btn--primary"
            :disabled="editSaving || !editDraft.trim()"
            @click="submitEdit"
          >
            {{ editSaving ? "Сохранение..." : "Сохранить" }}
          </button>
          <button
            class="comment__btn"
            @click="cancelEdit"
          >
            Отмена
          </button>
        </div>
      </div>

      <p v-else class="comment__text">
        {{ content }}
      </p>

      <div v-if="!comment.is_deleted" class="comment__actions">
        <button
          class="comment__action"
          :class="{ liked: isLiked }"
          @click="toggleLike"
        >
          <SakuraIcon name="heart" />
          <span>{{ fmt(likesCount) }}</span>
        </button>

        <button
          class="comment__action"
          :class="{ disliked: isDisliked }"
          @click="toggleDislike"
        >
          <SakuraIcon name="thumbs-down" />
          <span>{{ fmt(dislikesCount) }}</span>
        </button>

        <button
          v-if="!comment.is_deleted && comment.level === 0"
          class="comment__action"
          @click="startReply"
        >
          <SakuraIcon name="message" />
          <span>Ответить</span>
        </button>

        <button
          v-if="!comment.is_deleted"
          class="comment__action comment__action--report"
          @click="openCommentReport"
        >
          <SakuraIcon name="flag" />
          <span>Пожаловаться</span>
        </button>

        <button
          v-if="!comment.is_deleted && comment.level === 0 && hasReplies"
          class="comment__action comment__toggle-replies"
          :class="{ 'comment__toggle-replies--open': showReplies }"
          @click="showReplies = !showReplies"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: showReplies ? 'rotate(180deg)' : 'rotate(0deg)' }">
            <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Ответы ({{ repliesCount }})</span>
        </button>
      </div>

      <div v-if="showReply" class="comment__reply-box">
        <textarea
          v-model="replyText"
          class="comment__reply-textarea"
          :placeholder="`Ответить @${comment.author_username}...`"
          rows="2"
          @keydown.enter.exact.prevent="submitInlineReply"
        />
        <div class="comment__reply-actions">
          <button
            class="comment__btn comment__btn--primary"
            :disabled="!replyText.trim()"
            @click="submitInlineReply"
          >
            Ответить
          </button>
          <button class="comment__btn" @click="cancelReply">
            Отмена
          </button>
        </div>
      </div>

      <div v-if="showCommentReport" class="comment__report-box">
        <p class="comment__report-title">Причина жалобы:</p>
        <div class="comment__report-reasons">
          <button
            v-for="r in commentReportReasons"
            :key="r.id"
            class="comment__report-reason"
            :class="{ selected: commentReportReason === r.id }"
            @click="commentReportReason = r.id"
          >
            <SakuraIcon :name="r.icon" :size="18" /> {{ r.label }}
          </button>
        </div>
        <textarea
          v-model="commentReportDetails"
          class="comment__edit-area"
          rows="2"
          maxlength="1000"
          placeholder="Дополнительные подробности (необязательно)"
        />
        <div class="comment__report-actions">
          <button class="comment__btn" @click="cancelCommentReport">
            Отмена
          </button>
          <button
            class="comment__btn comment__btn--primary"
            :disabled="!commentReportReason || commentReportSending"
            @click="submitCommentReport"
          >
            {{ commentReportSending ? "..." : "Отправить" }}
          </button>
        </div>
      </div>

      <div v-if="showReplies" class="comment__replies">
        <PostComment
          v-for="child in replies"
          :key="child.id"
          :comment="child"
          :post-id="postId"
          :reply-to-username="child.parent_username || comment.author_username"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { commentsApi } from "@/api/feed";
import type { PostComment } from "@/api/feed";
import UserAvatar from "@/components/ui/UserAvatar.vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { useToast } from "@/composables/useToast";

const props = defineProps<{
  comment: PostComment;
  postId: string | number;
  replyToUsername?: string | null;
  children?: PostComment[];
}>();

const emit = defineEmits<{
  reply: [comment: PostComment];
  "reply-created": [comment: PostComment];
  updated: [];
  deleted: [];
}>();

const authStore = useAuthStore();
const toast = useToast();

const menuOpen = ref(false);
const editing = ref(false);
const editDraft = ref("");
const editSaving = ref(false);
const liking = ref(false);
const disliking = ref(false);
const showReply = ref(false);
const replyText = ref("");
const replySending = ref(false);
const replyClientId = ref<string>(crypto.randomUUID());
const showReplies = ref(false);
const showCommentReport = ref(false);
const commentReportReason = ref("");
const commentReportDetails = ref("");
const commentReportSending = ref(false);
const content = ref(props.comment.content);
const isEdited = ref(props.comment.is_edited);
const isLiked = ref(props.comment.is_liked);
const isDisliked = ref(props.comment.is_disliked);
const likesCount = ref(props.comment.likes_count);
const dislikesCount = ref(props.comment.dislikes_count);

watch(
  () => props.comment,
  (comment) => {
    content.value = comment.content;
    isEdited.value = comment.is_edited;
    isLiked.value = comment.is_liked;
    isDisliked.value = comment.is_disliked;
    likesCount.value = comment.likes_count;
    dislikesCount.value = comment.dislikes_count;
  },
  { deep: true },
);

const currentUser = computed(() => authStore.user);
const isOwnAuthor = computed(
  () => currentUser.value?.id === props.comment.author,
);
const canEdit = computed(
  () =>
    isOwnAuthor.value &&
    props.comment.author === currentUser.value?.id &&
    !props.comment.is_deleted && Date.now() - new Date(props.comment.created_at).getTime() < 10 * 60_000,
);
const canDelete = computed(
  () =>
    isOwnAuthor.value ||
    currentUser.value?.is_staff ||
    currentUser.value?.is_superuser,
);

const authorName = computed(
  () =>
    props.comment.author_display_name ||
    props.comment.author_username ||
    "Аноним",
);

const avatarUrl = computed(() => {
  if (props.comment.author_avatar) {
    return props.comment.author_avatar;
  }
  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3Ccircle cx='20' cy='15' r='6' fill='%23666'/%3E%3Cpath d='M8 36c0-6.627 5.373-12 12-12s12 5.373 12 12' fill='%23666'/%3E%3C/svg%3E`;
});

const indentStyle = computed(() => {
  const level = Math.min(props.comment.level || 0, 6);
  return { paddingLeft: `${level * 24}px` };
});

const replies = computed(() => {
  if (props.children && props.children.length) {
    return props.children;
  }
  if (props.comment.replies && props.comment.replies.length) {
    return props.comment.replies;
  }
  return [];
});

const repliesCount = computed(() => {
  if (props.children && props.children.length) {
    return props.children.length;
  }
  return props.comment.replies_count || props.comment.replies?.length || 0;
});

const hasReplies = computed(() => repliesCount.value > 0);

const formattedTime = computed(() => {
  const date = new Date(props.comment.created_at);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const minutes = Math.floor(diffMs / 60000);
  const hours = Math.floor(diffMs / 3600000);
  const days = Math.floor(diffMs / 86400000);

  if (minutes < 1) return "Только что";
  if (minutes < 60) return `${minutes} мин. назад`;
  if (hours < 24) return `${hours} ч. назад`;
  if (days < 7) return date.toLocaleDateString("ru-RU", { weekday: "long" });
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
});

const fmt = (n?: number) => {
  if (!n) return "0";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "М";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "К";
  return String(n);
};

const commentReportReasons = [
  { id: "spam", icon: "megaphone", label: "Спам" },
  { id: "copyright", icon: "copyright", label: "Нарушение авторских прав" },
  { id: "inappropriate", icon: "ban", label: "Неприемлемый контент (18+)" },
  { id: "harassment", icon: "warning", label: "Оскорбления / травля" },
  { id: "other", icon: "question", label: "Другое" },
];

function startEdit() {
  editDraft.value = content.value;
  editing.value = true;
  menuOpen.value = false;
}

function cancelEdit() {
  editing.value = false;
  editDraft.value = "";
}

async function submitEdit() {
  const text = editDraft.value.trim();
  if (!text || editSaving.value) return;

  editSaving.value = true;
  try {
    await commentsApi.updateComment(props.postId, props.comment.id, text);
    content.value = text;
    isEdited.value = true;
    emit("updated");
    editing.value = false;
    editDraft.value = "";
  } catch {
  } finally {
    editSaving.value = false;
  }
}

function confirmDelete() {
  menuOpen.value = false;
  if (!confirm("Удалить комментарий?")) return;
  deleteComment();
}

async function deleteComment() {
  try {
    await commentsApi.deleteComment(props.postId, props.comment.id);
    emit("deleted");
  } catch {
  }
}

  async function toggleLike() {
    if (liking.value) return;
    liking.value = true;
    try {
      const { data } = await commentsApi.likeComment(props.comment.id);
      isLiked.value = data.liked;
      likesCount.value = data.likes_count;
      dislikesCount.value = data.dislikes_count;
    } catch (error) {
      console.error("Error liking comment:", error);
    } finally {
      liking.value = false;
    }
  }

  async function toggleDislike() {
    if (disliking.value) return;
    disliking.value = true;
    try {
      const { data } = await commentsApi.dislikeComment(props.comment.id);
      isDisliked.value = data.disliked;
      likesCount.value = data.likes_count;
      dislikesCount.value = data.dislikes_count;
    } catch (error) {
      console.error("Error disliking comment:", error);
    } finally {
      disliking.value = false;
    }
  }

function scrollToParent() {
  const parentId = props.comment.parent_id;
  if (!parentId) return;
  const el = document.getElementById(`comment-${parentId}`);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.add("comment--highlight");
    setTimeout(() => el.classList.remove("comment--highlight"), 2000);
  }
}

function startReply() {
  showReply.value = true;
  replyText.value = "";
}

function cancelReply() {
  showReply.value = false;
  replyText.value = "";
}

async function submitInlineReply() {
  const text = replyText.value.trim();
  if (!text || replySending.value) return;

  replySending.value = true;
  try {
    const { data } = await commentsApi.createComment(props.postId, text, props.comment.id, replyClientId.value);
    const created = data as PostComment;
    replyClientId.value = crypto.randomUUID();

    replyText.value = "";
    showReply.value = false;
    emit("reply-created", created);
  } catch (error) {
    console.error("Failed to create reply:", error);
  } finally {
    replySending.value = false;
  }
}

function openCommentReport() {
  showCommentReport.value = true;
  commentReportReason.value = "";
  commentReportDetails.value = "";
}

async function submitCommentReport() {
  if (!commentReportReason.value || commentReportSending.value) return;

  commentReportSending.value = true;
  try {
    const { data } = await commentsApi.reportComment(
      props.comment.id,
      commentReportReason.value,
      commentReportDetails.value.trim(),
    );
    toast.success(data?.message || "Жалоба отправлена. Мы сообщим о результате.");
    showCommentReport.value = false;
    commentReportReason.value = "";
    commentReportDetails.value = "";
  } catch (error) {
    console.error("Failed to report comment:", error);
    const message = (error as { response?: { data?: { error?: string } } })?.response?.data?.error;
    toast.error(message || "Не удалось отправить жалобу");
  } finally {
    commentReportSending.value = false;
  }
}

function cancelCommentReport() {
  showCommentReport.value = false;
  commentReportReason.value = "";
  commentReportDetails.value = "";
}

watch(() => props.comment, () => {
  menuOpen.value = false;
  editing.value = false;
});
</script>

<style scoped>
.comment {
  display: flex;
  gap: 12px;
  padding: 20px 20px 20px 20px;
  border-radius: var(--radius-lg);
  transition: background 0.2s ease;
}

.comment--reply {
  margin-top: 8px;
  position: relative;
}

.comment--reply::before {
  content: "";
  position: absolute;
  left: 20px;
  top: -8px;
  bottom: 12px;
  width: 2px;
  background: var(--border-subtle);
  border-radius: 2px;
}

.comment--deleted {
  opacity: 0.7;
}

.comment--own {
  background: color-mix(in srgb, var(--accent) 6%, transparent);
}

.comment--highlight {
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  transition: background 0.3s ease;
}

.comment__avatar {
  flex-shrink: 0;
}

.comment__avatar-img {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.2s ease;
}

.comment:hover .comment__avatar-img {
  border-color: var(--accent);
}

.comment__body {
  flex: 1;
  min-width: 0;
}

.comment__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.comment__author-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.comment__author {
  font-weight: 700;
  font-size: 0.875rem;
  color: var(--text-primary);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s ease;
}

.comment__author:hover {
  color: var(--accent);
}

.comment__reply-to {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 0.8rem;
}

.comment__reply-arrow {
  color: var(--text-tertiary);
}

.comment__reply-link {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 0.8rem;
  cursor: pointer;
  padding: 0;
  font-weight: 500;
}

.comment__reply-link:hover {
  text-decoration: underline;
}

.comment__time {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.comment__edited {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  font-style: italic;
}

.comment__menu-wrap {
  position: relative;
  flex-shrink: 0;
}

.comment__menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.comment__menu-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.comment__menu {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 4px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  min-width: 140px;
  z-index: 10;
  overflow: hidden;
}

.comment__menu-item {
  display: block;
  width: 100%;
  padding: 8px 14px;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 0.85rem;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease;
}

.comment__menu-item:hover {
  background: var(--surface-4);
}

.comment__menu-item--danger {
  color: var(--danger);
}

.comment__deleted {
  color: var(--text-tertiary);
  font-style: italic;
  font-size: 0.875rem;
  padding: 4px 0;
}

.comment__text {
  color: var(--text-primary);
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0 0 8px;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment__edit-box {
  margin-bottom: 8px;
}

.comment__edit-area {
  width: 100%;
  padding: 10px 12px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s ease;
}

.comment__edit-area:focus {
  border-color: var(--accent);
}

.comment__edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.comment__btn {
  padding: 6px 14px;
  border-radius: var(--radius-md);
  border: none;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.comment__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.comment__btn--primary {
  background: var(--accent);
  color: #fff;
}

.comment__btn--primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.comment__btn:not(.comment__btn--primary) {
  background: var(--surface-4);
  color: var(--text-secondary);
}

.comment__btn:not(.comment__btn--primary):hover {
  background: var(--surface-5);
  color: var(--text-primary);
}

.comment__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.comment__action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.comment__action:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.comment__action.liked {
  color: #ff4d6d;
}

.comment__action.liked:hover {
  color: #ff4d6d;
  background: color-mix(in srgb, #ff4d6d 10%, transparent);
}

.comment__action.disliked {
  color: var(--accent);
}

.comment__action.disliked:hover {
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
}

.comment__toggle-replies {
  margin-left: auto;
  padding-left: 12px;
}

.comment__toggle-replies--open {
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
}

.comment__replies {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.comment__replies-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.comment__reply-box {
  margin-top: 8px;
  padding: 10px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.comment__reply-textarea {
  width: 100%;
  padding: 10px 12px;
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s ease;
}

.comment__reply-textarea:focus {
  border-color: var(--accent);
}

.comment__reply-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: flex-end;
}

.comment__action--report {
  color: var(--text-tertiary);
}

.comment__report-box {
  margin-top: 8px;
  padding: 10px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.comment__report-title {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0 0 8px;
}

.comment__report-reasons {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.comment__report-reason {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 6px 10px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
}

.comment__report-reason.selected {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  color: var(--text-primary);
}

.comment__report-reason:hover:not(.selected) {
  background: var(--surface-4);
}

.comment__report-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
