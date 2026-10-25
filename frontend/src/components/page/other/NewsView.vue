<template>
  <div class="news-page">
    <div class="page-header">
      <div class="header-text">
        <h1>Новости</h1>
        <p class="subtitle">Новости о проекте и аниме</p>
      </div>
      <button v-if="isAdmin" class="btn-create" @click="openCreate">
        <SakuraIcon name="plus" :size="16" />
        <span>Написать новость</span>
      </button>
    </div>

    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <div v-else-if="news.length === 0" class="empty">
      <SakuraIcon name="newspaper" :size="48" />
      <p>Новостей пока нет</p>
    </div>

    <div v-else class="news-list">
      <article
        v-for="item in news"
        :key="item.id"
        :class="['news-card', { pinned: item.is_pinned }]"
        @click="openDetail(item)"
      >
        <div v-if="item.cover_url_final" class="news-cover">
          <img :src="item.cover_url_final" :alt="item.title" loading="lazy" />
        </div>

        <div class="news-body">
          <div class="news-meta">
            <span
              v-if="item.is_pinned"
              class="badge badge-pinned"
              title="Закреплена"
            >
              <SakuraIcon name="pin" :size="12" />
              Закреплено
            </span>
            <span
              :class="[
                'badge',
                item.priority === 'hot'
                  ? 'badge-hot'
                  : item.priority === 'important'
                    ? 'badge-important'
                    : 'badge-low',
              ]"
            >
              {{ item.priority_display }}
            </span>
            <span class="news-date">{{ formatDate(item.created_at) }}</span>
          </div>

          <h2 class="news-title">{{ item.title }}</h2>
          <p v-if="item.summary" class="news-summary">{{ item.summary }}</p>

          <div class="news-footer">
            <span class="news-author">
              <img
                v-if="item.author_avatar"
                :src="item.author_avatar"
                class="author-avatar"
                alt=""
              />
              <span>{{ item.author_display_name || item.author_username }}</span>
            </span>
            <span class="news-views">
              <SakuraIcon name="eye" :size="14" />
              {{ item.views_count }}
            </span>
          </div>

          <div v-if="isAdmin" class="admin-actions" @click.stop>
            <button
              class="icon-btn"
              title="Редактировать"
              @click="openEdit(item)"
            >
              <SakuraIcon name="edit" :size="15" />
            </button>
            <button
              class="icon-btn danger"
              title="Удалить"
              @click="confirmDelete(item)"
            >
              <SakuraIcon name="trash" :size="15" />
            </button>
          </div>
        </div>
      </article>
    </div>

    <Modal
      :model-value="showDetail"
      closeOnOverlay
      @close="showDetail = false"
    >
      <div v-if="selected" class="news-detail">
        <div v-if="selected.cover_url_final" class="detail-cover">
          <img :src="selected.cover_url_final" :alt="selected.title" />
        </div>
        <div class="detail-body">
          <div class="news-meta">
            <span
              v-if="selected.is_pinned"
              class="badge badge-pinned"
              title="Закреплена"
            >
              <SakuraIcon name="pin" :size="12" />
              Закреплено
            </span>
            <span
              :class="[
                'badge',
                selected.priority === 'hot'
                  ? 'badge-hot'
                  : selected.priority === 'important'
                    ? 'badge-important'
                    : 'badge-low',
              ]"
            >
              {{ selected.priority_display }}
            </span>
            <span class="news-date">{{ formatDate(selected.created_at) }}</span>
          </div>
          <h2 class="detail-title">{{ selected.title }}</h2>
          <div class="detail-content">{{ selected.content }}</div>
          <div class="detail-footer">
            <span class="news-author">
              <img
                v-if="selected.author_avatar"
                :src="selected.author_avatar"
                class="author-avatar"
                alt=""
              />
              <span>
                {{ selected.author_display_name || selected.author_username }}
              </span>
            </span>
            <span class="detail-views">
              <SakuraIcon name="eye" :size="15" />
              {{ selected.views_count }}
            </span>
          </div>
        </div>
      </div>
    </Modal>

    <Modal
      :model-value="showEditor"
      closeOnOverlay
      @close="showEditor = false"
    >
      <div class="news-editor">
        <h3>{{ editingId ? "Редактировать новость" : "Новая новость" }}</h3>
        <form @submit.prevent="saveNews">
          <div class="form-group">
            <label for="news-title">Заголовок</label>
            <input
              id="news-title"
              v-model="form.title"
              type="text"
              required
              maxlength="250"
              placeholder="Заголовок новости"
            />
          </div>

          <div class="form-group">
            <label for="news-summary">Краткое описание</label>
            <input
              id="news-summary"
              v-model="form.summary"
              type="text"
              maxlength="500"
              placeholder="Краткое описание (по желанию)"
            />
          </div>

          <div class="form-group">
            <label for="news-content">Текст</label>
            <textarea
              id="news-content"
              v-model="form.content"
              required
              rows="8"
              placeholder="Полный текст новости"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="news-cover">Ссылка на обложку</label>
            <input
              id="news-cover"
              v-model="form.cover_url"
              type="url"
              placeholder="https://... (по желанию)"
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="news-priority">Приоритет</label>
              <select id="news-priority" v-model="form.priority">
                <option value="low">Обычная</option>
                <option value="important">Важная</option>
                <option value="hot">Горячая</option>
              </select>
            </div>

            <div class="form-group">
              <label class="toggle-label">
                <input v-model="form.is_pinned" type="checkbox" />
                <span>Закрепить</span>
              </label>
            </div>

            <div class="form-group">
              <label class="toggle-label">
                <input v-model="form.is_published" type="checkbox" />
                <span>Опубликована</span>
              </label>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="showEditor = false">
              Отмена
            </button>
            <button type="submit" class="btn-save" :disabled="saving">
              {{ saving ? "Сохранение..." : "Сохранить" }}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import LoadingSpinner from "@/components/ui/LoadingSpinner.vue";
import Modal from "@/components/ui/Modal.vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { newsApi, type NewsPost, type NewsPostForm } from "@/api/news";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();

const isAdmin = computed(() => {
  const u = authStore.user;
  return !!u?.is_admin || !!u?.is_staff;
});

const loading = ref(false);
const saving = ref(false);
const news = ref<NewsPost[]>([]);
const selected = ref<NewsPost | null>(null);
const showDetail = ref(false);
const showEditor = ref(false);
const editingId = ref<number | null>(null);

const emptyForm = (): NewsPostForm => ({
  title: "",
  summary: "",
  content: "",
  cover_url: "",
  priority: "low",
  is_pinned: false,
  is_published: true,
});

const form = ref<NewsPostForm>(emptyForm());

const loadNews = async () => {
  loading.value = true;
  try {
    const response = await newsApi.getNews();
    news.value = response.data;
  } catch (error) {
    console.error("Ошибка загрузки новостей:", error);
  } finally {
    loading.value = false;
  }
};

const openDetail = (item: NewsPost) => {
  selected.value = item;
  showDetail.value = true;
  newsApi.registerView(item.id).then((r) => {
    if (r.data?.views_count != null) {
      item.views_count = r.data.views_count;
    }
  }).catch(() => {});
};

const openCreate = () => {
  editingId.value = null;
  form.value = emptyForm();
  showEditor.value = true;
};

const openEdit = (item: NewsPost) => {
  editingId.value = item.id;
  form.value = {
    title: item.title,
    summary: item.summary,
    content: item.content,
    cover_url: item.cover_url,
    priority: item.priority,
    is_pinned: item.is_pinned,
    is_published: item.is_published,
  };
  showEditor.value = true;
};

const saveNews = async () => {
  saving.value = true;
  try {
    if (editingId.value) {
      await newsApi.updateNews(editingId.value, form.value);
    } else {
      await newsApi.createNews(form.value);
    }
    showEditor.value = false;
    await loadNews();
  } catch (error) {
    console.error("Ошибка сохранения новости:", error);
  } finally {
    saving.value = false;
  }
};

const confirmDelete = async (item: NewsPost) => {
  if (!window.confirm(`Удалить новость «${item.title}»?`)) return;
  try {
    await newsApi.deleteNews(item.id);
    await loadNews();
  } catch (error) {
    console.error("Ошибка удаления новости:", error);
  }
};

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
};

onMounted(loadNews);
</script>

<style scoped>
.news-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.header-text h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.subtitle {
  margin: 6px 0 0;
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

.btn-create {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 38px;
  padding: 0 16px;
  border: none;
  border-radius: 10px;
  background: var(--accent);
  color: var(--text-on-accent);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, opacity 0.2s ease;
}

.btn-create:hover {
  background: var(--accent-hover);
}

.btn-create:active {
  opacity: 0.85;
}

.loading,
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px 20px;
  color: var(--text-tertiary);
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-card {
  position: relative;
  display: flex;
  gap: 18px;
  padding: 16px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
  cursor: pointer;
  transition: border-color 0.35s ease, box-shadow 0.35s ease;
}

.news-card:hover {
  border-color: var(--border-default);
  box-shadow:
    0 18px 40px -18px rgba(0, 0, 0, 0.65),
    0 0 0 1px var(--border-default);
}

.news-card.pinned {
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border-subtle));
}

.news-cover {
  flex-shrink: 0;
  width: 200px;
  min-height: 120px;
  border-radius: 12px;
  overflow: hidden;
  background: var(--surface-4);
}

.news-cover img,
.detail-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.news-body {
  flex: 1;
  min-width: 0;
}

.news-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1;
  border: 1px solid var(--border-subtle);
  background: var(--surface-4);
  color: var(--text-secondary);
}

.badge-pinned {
  background: var(--accent);
  color: var(--text-on-accent);
  border-color: transparent;
}

.badge-hot {
  background: var(--surface-4);
  color: var(--warning);
  border-color: var(--border-subtle);
}

.badge-important {
  background: var(--surface-4);
  color: var(--info);
  border-color: var(--border-subtle);
}

.badge-low {
  background: var(--surface-4);
  color: var(--text-secondary);
  border-color: var(--border-subtle);
}

.news-date {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
}

.news-title {
  margin: 0 0 8px;
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}

.news-summary {
  margin: 0 0 14px;
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--text-secondary);
}

.news-footer,
.detail-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.news-author {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.author-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

.news-views,
.detail-views {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8125rem;
  color: var(--text-tertiary);
}

.admin-actions {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  gap: 6px;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--surface-4);
  color: var(--text-secondary);
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.icon-btn:hover {
  background: var(--surface-5);
  border-color: var(--border-default);
  color: var(--text-primary);
}

.icon-btn.danger:hover {
  color: var(--danger);
  border-color: var(--danger);
}

.news-detail {
  max-width: 720px;
}

.detail-cover {
  width: 100%;
  max-height: 320px;
  overflow: hidden;
}

.detail-body {
  padding: 24px;
}

.detail-title {
  margin: 0 0 16px;
  font-size: 1.5rem;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.detail-content {
  font-size: 0.9375rem;
  line-height: 1.75;
  color: var(--text-secondary);
  white-space: pre-wrap;
  margin-bottom: 20px;
}

.detail-footer {
  padding-top: 16px;
  border-top: 1px solid var(--border-subtle);
}

.news-editor {
  background: var(--surface-3);
  width: 100%;
  max-width: 640px;
  padding: 24px;
  border-radius: 16px;
}

.news-editor h3 {
  margin: 0 0 20px;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.form-group input[type="text"],
.form-group input[type="url"],
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0 14px;
  height: 40px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--surface-4);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.2s ease;
}

.form-group textarea {
  height: auto;
  padding: 10px 14px;
  resize: vertical;
  line-height: 1.5;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent);
}

.form-row {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.form-row .form-group {
  flex: 1;
  min-width: 140px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 26px;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-primary);
}

.toggle-label input {
  accent-color: var(--accent);
  width: 16px;
  height: 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn-cancel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 38px;
  padding: 0 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--surface-4);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.btn-cancel:hover {
  background: var(--surface-5);
  border-color: var(--border-default);
  color: var(--text-primary);
}

.btn-save {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 38px;
  padding: 0 20px;
  border: none;
  border-radius: 10px;
  background: var(--accent);
  color: var(--text-on-accent);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, opacity 0.2s ease;
}

.btn-save:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .news-card {
    flex-direction: column;
  }

  .news-cover {
    width: 100%;
    max-height: 180px;
  }
}
</style>
