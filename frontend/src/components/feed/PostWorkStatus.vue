<template>
  <aside v-if="store.uploads.length || store.pending.length" class="post-work" aria-label="Отправка постов" aria-live="polite">
    <div v-for="job in store.uploads" :key="job.id" class="post-work-row" role="status">
      <strong>{{ job.text }}</strong>
      <span>{{ job.error || `Загрузка ${job.progress}%` }}</span>
      <progress v-if="!job.error" :value="job.progress" max="100" aria-label="Прогресс загрузки" />
      <button v-else type="button" @click="store.uploads = store.uploads.filter(row => row.id !== job.id)">Закрыть</button>
    </div>
    <div v-for="post in store.pending" :key="post.id" class="post-work-row" role="status">
      <strong>{{ post.text || 'Пост с вложениями' }}</strong>
      <span>{{ failed(post) ? 'Не удалось обработать вложения' : `Подготовка вложений ${processingPercent(post)}%` }}</span>
      <progress v-if="!failed(post)" :value="processingPercent(post)" max="100" aria-label="Прогресс подготовки вложений" />
      <div>
        <button v-if="failed(post)" :disabled="busy.has(String(post.id))" @click="act(post, false)">Повторить обработку</button>
        <button v-if="post.processing_media?.length" :disabled="busy.has(String(post.id))" @click="act(post, true)">Отменить замену вложений</button>
      </div>
    </div>
    <p v-if="error" role="alert">{{ error }}</p>
  </aside>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import api from '@/api/client';
import type { FeedPost } from '@/api/feed';
import { usePostStore } from '@/stores/posts';
import { processingPercent } from '@/lib/postAttachments';
const store = usePostStore();
const busy = reactive(new Set<string>());
const error = ref('');
const failed = (post: FeedPost) => post.status === 'failed' || post.processing_media?.some(media => media.processing_state === 'failed');
async function act(post: FeedPost, cancel: boolean) {
  const id = String(post.id);
  if (busy.has(id)) return;
  busy.add(id); error.value = '';
  try {
    if (cancel) {
      const { data } = await api.post<FeedPost>(`/social/posts/${id}/cancel-pending-edit/`);
      store.upsert(data);
      store.pending = store.pending.filter(row => String(row.id) !== id);
    } else {
      for (const media of [...(post.media_files || []), ...(post.processing_media || [])])
        if (media.upload_id && media.processing_state === 'failed') await api.post(`/social/post-uploads/${media.upload_id}/retry/`);
      await store.refresh(id);
    }
  } catch (failure) {
    error.value = (failure as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Не удалось выполнить действие. Повторите попытку.';
  } finally { busy.delete(id); }
}
</script>

<style scoped>
.post-work {
  position: fixed;
  right: 20px;
  bottom: 24px;
  z-index: 700;
  width: min(360px, calc(100vw - 40px));
  max-height: 40vh;
  overflow: auto;
  padding: 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  background: var(--surface-2);
  box-shadow: 0 6px 28px #0004;
}

.post-work-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 0;
}
.post-work-row + .post-work-row {
  border-top: 1px solid var(--border-subtle);
}

.post-work strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.post-work span {
  font-size: 13px;
  color: var(--text-secondary);
}

/* --- прогресс-бар в розовой палитре сайта --- */
.post-work progress {
  width: 100%;
  height: 8px;
  appearance: none;
  -webkit-appearance: none;
  border: none;
  border-radius: 999px;
  overflow: hidden;
  background: var(--surface-3);
  /* фолбэк для браузеров, уважающих accent-color */
  accent-color: var(--accent);
}

/* Chromium / WebKit */
.post-work progress::-webkit-progress-bar {
  background: var(--surface-3);
  border-radius: 999px;
}
.post-work progress::-webkit-progress-value {
  background: linear-gradient(
    90deg,
    var(--accent),
    color-mix(in srgb, var(--accent) 70%, #ffffff)
  );
  border-radius: 999px;
  transition: width 0.2s var(--ease-out, ease);
}

/* Firefox */
.post-work progress::-moz-progress-bar {
  background: var(--accent);
  border-radius: 999px;
}

/* Мягкая окантовка трека, чтобы бар читался на surface-2 */
.post-work progress[value] {
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 25%, transparent);
}

/* Кнопки — в тон акценту */
.post-work button {
  margin: 4px 8px 0 0;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 6px 9px;
  background: var(--surface-3);
  color: var(--text-primary);
  cursor: pointer;
  transition:
    background-color var(--duration-base, 0.15s) var(--ease-out, ease),
    border-color var(--duration-base, 0.15s) var(--ease-out, ease);
}
.post-work button:hover:not(:disabled) {
  background: var(--accent-subtle);
  border-color: color-mix(in srgb, var(--accent) 40%, var(--border-subtle));
}
.post-work button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.post-work [role="alert"] {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--accent);
}
</style>