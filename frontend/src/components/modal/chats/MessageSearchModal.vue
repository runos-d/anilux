<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="close">
      <div class="modal-content" role="dialog" aria-modal="true" aria-labelledby="message-search-title" @click.stop>
        <div class="modal-header">
          <h3 id="message-search-title">Поиск по сообщениям</h3>
          <button class="close-btn" type="button" aria-label="Закрыть" @click="close">
            <SakuraIcon name="x" :size="16" />
          </button>
        </div>

        <div class="modal-body">
          <div class="search-form">
            <div class="search-input-wrap">
              <SakuraIcon name="search" :size="17" class="search-icon" />
              <input v-model="searchQuery" type="text" autocomplete="off" placeholder="Введите текст для поиска..." class="search-input" @keyup.enter="performSearch" />
            </div>
            <button class="search-btn" type="button" :disabled="!searchQuery.trim() || searching" @click="performSearch">
              {{ searching ? "Поиск..." : "Найти" }}
            </button>
          </div>

          <div class="filters">
            <div class="filter-group">
              <label class="filter-label">Дата от</label>
              <input v-model="filters.dateFrom" type="date" class="filter-input" />
            </div>
            <div class="filter-group">
              <label class="filter-label">Дата до</label>
              <input v-model="filters.dateTo" type="date" class="filter-input" />
            </div>
          </div>

          <div v-if="searching" class="search-state">Ищем сообщения…</div>
          <div v-else-if="searchResults.length > 0" class="search-results">
            <div class="results-header">Найдено: {{ searchResults.length }} сообщений</div>
            <div class="results-list">
              <button v-for="message in searchResults" :key="message.id" class="result-item" type="button" @click="goToMessage(message)">
                <div class="result-header">
                  <span class="result-sender">{{ message.sender_username }}</span>
                  <span class="result-date">{{ formatDate(message.created_at) }}</span>
                </div>
                <div class="result-text">
                  {{ message.text || attachmentTitles(message) || message.shared_anime_data?.title_ru || message.shared_anime_data?.title_en || message.shared_anime_title || message.shared_playlist_data?.title || "Медиа-сообщение" }}
                </div>
                <div v-if="message.media_type" class="result-media-type">{{ getMediaTypeLabel(message.media_type) }}</div>
                <div v-if="message.text && attachmentTitles(message)" class="result-media-type">{{ attachmentTitles(message) }}</div>
              </button>
            </div>
          </div>
          <div v-else-if="searched" class="search-state">Ничего не найдено</div>
          <div v-else class="search-state">Введите текст для поиска и нажмите «Найти»</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { reactive, ref } from "vue";
import { useChatExtrasStore } from "@/stores/chatExtras";
import { useRouter } from "vue-router";

interface Props {
  isOpen: boolean;
  chatId?: number;
  chatType?: "private" | "group";
  topicId?: number;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: "close"): void;
  (e: "message-selected", messageId: number): void;
}>();
const chatExtrasStore = useChatExtrasStore();
const router = useRouter();

interface SearchMessage {
  id: number;
  chat_id?: number;
  private_chat_id?: number;
  sender_username?: string;
  created_at?: string;
  text?: string;
  media_type?: string;
  shared_anime_title?: string;
  shared_anime_data?: { title_ru?: string; title_en?: string };
  shared_playlist_data?: { title?: string };
  attachments?: Array<{ data?: { title_ru?: string; title_en?: string; title?: string } }>;
}

const attachmentTitles = (message: SearchMessage) =>
  message.attachments?.map((attachment) => attachment.data?.title_ru || attachment.data?.title_en || attachment.data?.title).filter(Boolean).join(", ") ||
  message.shared_anime_data?.title_ru || message.shared_anime_data?.title_en || message.shared_anime_title || message.shared_playlist_data?.title;

const searchQuery = ref("");
const searching = ref(false);
const searched = ref(false);
const searchResults = ref<SearchMessage[]>([]);
const filters = reactive({ dateFrom: "", dateTo: "" });

const performSearch = async () => {
  if (!searchQuery.value.trim()) return;
  searching.value = true;
  searched.value = false;
  try {
    const result = await chatExtrasStore.searchMessages(searchQuery.value, {
      chat_id: props.chatId?.toString(),
      type: props.chatType,
      topic_id: props.topicId,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
    });
    searchResults.value = result.results as unknown as SearchMessage[];
    searched.value = true;
  } catch (error) {
    console.error("Error searching messages:", error);
    searchResults.value = [];
  } finally {
    searching.value = false;
  }
};

const goToMessage = (message: SearchMessage) => {
  emit("message-selected", message.id);
  close();
  if (props.chatId) return;
  if (message.chat_id) router.push(`/chats/${message.chat_id}`);
  else if (message.private_chat_id) router.push(`/chats/${message.private_chat_id}`);
};

const formatDate = (dateString?: string) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffMins < 1) return "Только что";
  if (diffMins < 60) return `${diffMins} мин. назад`;
  if (diffHours < 24) return `${diffHours} ч. назад`;
  if (diffDays < 7) return `${diffDays} дн. назад`;
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined });
};

const getMediaTypeLabel = (type?: string) => {
  const labels: Record<string, string> = { text: "Текст", image: "Изображение", video: "Видео", audio: "Аудио", file: "Файл", location: "Местоположение", post: "Пост", anime: "Аниме" };
  return type ? labels[type] || type : "";
};

const close = () => {
  emit("close");
  searchQuery.value = "";
  searchResults.value = [];
  searched.value = false;
  filters.dateFrom = "";
  filters.dateTo = "";
};
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; z-index: 9999; display: grid; place-items: center; padding: 24px; background: rgba(5, 4, 8, 0.82); backdrop-filter: blur(8px); }
.modal-content { width: min(100%, 680px); max-height: min(86vh, 760px); display: flex; flex-direction: column; overflow: hidden; background: var(--surface-2); border: 1px solid var(--border-default); border-radius: var(--radius-xl); box-shadow: var(--shadow-sm-modal); }
.modal-header { display: flex; align-items: center; justify-content: space-between; min-height: 68px; padding: 16px 20px; border-bottom: 1px solid var(--border-subtle); }
.modal-header h3 { margin: 0; color: var(--text-primary); font-size: 1.2rem; font-weight: 600; line-height: 1.25; }
.close-btn { width: 34px; height: 34px; flex: 0 0 34px; display: grid; place-items: center; padding: 0; color: var(--text-tertiary); background: transparent; border: 0; border-radius: var(--radius-full); cursor: pointer; transition: background-color .2s var(--ease-petal), color .2s var(--ease-petal); }
.close-btn:hover { color: var(--accent); background: var(--surface-4); }
.modal-body { min-height: 0; display: flex; flex-direction: column; gap: 16px; padding: 20px; overflow-y: auto; }
.search-form { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: stretch; }
.search-input-wrap { position: relative; min-width: 0; display: flex; align-items: center; }
.search-icon { position: absolute; left: 13px; color: var(--text-tertiary); pointer-events: none; }
.search-input, .filter-input { width: 100%; box-sizing: border-box; color: var(--text-primary); background: var(--surface-4); border: 1px solid var(--border-default); transition: border-color .2s var(--ease-petal), box-shadow .2s var(--ease-petal); }
.search-input { min-height: 44px; padding: 10px 13px 10px 40px; border-radius: var(--radius-lg); font-size: .95rem; }
.search-input:focus, .filter-input:focus { outline: none; border-color: var(--accent); box-shadow: var(--border-glow); }
.search-btn { min-width: 104px; min-height: 44px; padding: 10px 20px; color: var(--text-on-accent); background: var(--accent); border: 0; border-radius: var(--radius-lg); font-size: .875rem; font-weight: 600; cursor: pointer; white-space: nowrap; }
.search-btn:hover:not(:disabled) { box-shadow: var(--shadow-sm-glow-sm); }
.search-btn:disabled { color: var(--text-tertiary); background: var(--surface-5); cursor: not-allowed; }
.filters { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 14px; background: var(--surface-3); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); }
.filter-group { min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.filter-label { color: var(--text-secondary); font-size: .75rem; font-weight: 500; }
.filter-input { min-height: 38px; padding: 7px 10px; border-radius: var(--radius-md); font-size: .875rem; }
.search-results { min-height: 0; display: flex; flex-direction: column; gap: 10px; }
.results-header { padding-bottom: 10px; color: var(--text-secondary); border-bottom: 1px solid var(--border-subtle); font-size: .875rem; }
.results-list { display: flex; flex-direction: column; gap: 8px; }
.result-item { width: 100%; padding: 12px 14px; color: inherit; text-align: left; background: var(--surface-3); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); cursor: pointer; transition: background-color .2s var(--ease-petal), border-color .2s var(--ease-petal); }
.result-item:hover { background: var(--surface-4); border-color: var(--accent); }
.result-item:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.result-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 5px; }
.result-sender { min-width: 0; overflow: hidden; color: var(--text-primary); font-size: .875rem; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.result-date { flex-shrink: 0; color: var(--text-tertiary); font-size: .75rem; }
.result-text { overflow: hidden; color: var(--text-secondary); font-size: .875rem; line-height: 1.4; text-overflow: ellipsis; white-space: nowrap; }
.result-media-type { margin-top: 5px; color: var(--accent); font-size: .75rem; }
.search-state { display: grid; place-items: center; min-height: 92px; padding: 18px; color: var(--text-tertiary); text-align: center; background: var(--surface-3); border: 1px dashed var(--border-subtle); border-radius: var(--radius-lg); font-size: .875rem; }
@media (max-width: 560px) {
  .modal-overlay { align-items: end; padding: 0; }
  .modal-content { width: 100%; max-height: 92dvh; border-right: 0; border-bottom: 0; border-left: 0; border-radius: var(--radius-xl) var(--radius-xl) 0 0; }
  .modal-header, .modal-body { padding-right: 16px; padding-left: 16px; }
  .search-form, .filters { grid-template-columns: 1fr; }
  .search-btn { width: 100%; }
}
</style>
