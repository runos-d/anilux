<template>
  <div class="comments-modal-overlay" @click="$emit('close')">
    <div class="comments-modal" role="dialog" aria-modal="true" aria-labelledby="comments-modal-title" @click.stop>
      <div class="comments-modal__header">
        <div>
          <h3 id="comments-modal-title" class="comments-modal__title">
            Обсуждение
            <span class="comments-modal__count">{{ post?.comments_count || 0 }}</span>
          </h3>
          <p class="comments-modal__subtitle">Комментарии к публикации</p>
        </div>
        <button class="comments-modal__close" type="button" aria-label="Закрыть комментарии" @click="$emit('close')">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" />
          </svg>
        </button>
      </div>

      <div class="comments-modal__body">
        <CommentSection
          :post-id="post!.id"
          :post="post"
          mode="modal"
          @comment-added="$emit('comment-added', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue';
import CommentSection from '@/components/feed/CommentSection.vue';
import type { FeedPost, PostComment } from '@/api/feed';
defineProps<{ post: FeedPost }>();
const emit = defineEmits<{ close: []; 'comment-added': [comment: PostComment] }>();
const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') emit('close'); };
onMounted(() => {
  document.addEventListener('keydown', closeOnEscape);
  document.body.classList.add('comments-modal-open');
});
onBeforeUnmount(() => {
  document.removeEventListener('keydown', closeOnEscape);
  document.body.classList.remove('comments-modal-open');
});
</script>

<style scoped>
.comments-modal-overlay {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, #08060d 82%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: clamp(12px, 3vw, 32px);
  backdrop-filter: blur(10px);
}

.comments-modal {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  width: 100%;
  max-width: 880px;
  height: min(820px, calc(100dvh - 64px));
  max-height: calc(100dvh - 24px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 28px 80px rgba(0, 0, 0, .48), var(--shadow-lg);
}

.comments-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.comments-modal__title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.comments-modal__subtitle {
  margin: 3px 0 0;
  color: var(--text-tertiary);
  font-size: .78rem;
}

.comments-modal__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  background: var(--surface-4);
  color: var(--text-secondary);
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
}

.comments-modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.comments-modal__close:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.comments-modal__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 22px 22px;
  scrollbar-gutter: stable;
}

:global(body.comments-modal-open) { overflow: hidden; }

.comments-modal__body :deep(.comment-section--modal) {
  min-height: 100%;
  border: 0;
  border-radius: 0;
  background: transparent;
}

@media (max-width: 640px) {
  .comments-modal-overlay { align-items: flex-end; padding: 0; }
  .comments-modal { height: min(90dvh, 820px); max-height: 90dvh; border-radius: 20px 20px 0 0; }
  .comments-modal__header { padding: 14px 16px; }
  .comments-modal__body { padding: 14px 14px max(16px, env(safe-area-inset-bottom)); }
}
</style>
