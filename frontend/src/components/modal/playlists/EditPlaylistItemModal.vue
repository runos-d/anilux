<template>
  <BaseModal
    :show="show"
    @close="$emit('close')"
    :title="`Заметки: ${item?.anime_title || ''}`"
  >
    <form @submit.prevent="handleSubmit" class="edit-item-form">
      <div v-if="item" class="item-preview">
        <img
          v-if="item.anime_poster || item.anime_poster_url"
          :src="item.anime_poster || item.anime_poster_url"
          :alt="item.anime_title"
          class="preview-poster"
        />
        <div class="preview-info">
          <h3 class="preview-title">{{ item.anime_title }}</h3>
          <div class="preview-meta">
            <span v-if="item.anime_year"
              ><SakuraIcon name="calendar" /> {{ item.anime_year }}</span
            >
            <span v-if="item.anime_score"
              ><SakuraIcon name="star" />
              {{ item.anime_score.toFixed(1) }}</span
            >
          </div>
        </div>
      </div>

      <div class="form-group">
        <label for="notes" class="form-label">Ваши заметки</label>
        <textarea
          id="notes"
          v-model="form.notes"
          rows="6"
          class="form-input"
          placeholder="Напишите заметки об этом аниме..."
        ></textarea>
        <p class="form-hint">
          Поделитесь мыслями, запомните на каком эпизоде остановились или
          добавьте любую другую информацию
        </p>
      </div>

      <div class="quick-notes">
        <p class="quick-notes-label">Быстрые заметки:</p>
        <div class="quick-notes-buttons">
          <button
            type="button"
            class="quick-note-btn"
            @click="addQuickNote('Посмотрено полностью')"
          >
            ✓ Посмотрено полностью
          </button>
          <button
            type="button"
            class="quick-note-btn"
            @click="addQuickNote('Любимое')"
          >
            ♥ Любимое
          </button>
          <button
            type="button"
            class="quick-note-btn"
            @click="addQuickNote('Пересмотреть')"
          >
            <SakuraIcon name="refresh" /> Пересмотреть
          </button>
          <button
            type="button"
            class="quick-note-btn"
            @click="addQuickNote('Рекомендую')"
          >
            <SakuraIcon name="star" /> Рекомендую
          </button>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('close')">
          Отмена
        </button>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? "Сохранение..." : "Сохранить" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import BaseModal from "@/components/ui/BaseModal.vue";
import type { PlaylistItem } from "@/api/playlists";
import apiClient from "@/api/client";

interface Props {
  show: boolean;
  item: PlaylistItem | null;
  playlistId: number;
}

interface Emits {
  (e: "close"): void;
  (e: "saved", item: PlaylistItem): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const loading = ref(false);
const form = ref({
  notes: "",
});

watch(
  () => props.show,
  (show) => {
    if (show && props.item) {
      form.value = {
        notes: props.item.notes || "",
      };
    }
  },
);

const addQuickNote = (note: string) => {
  if (form.value.notes) {
    form.value.notes += "\n\n" + note;
  } else {
    form.value.notes = note;
  }
};

const handleSubmit = async () => {
  if (!props.item) return;

  loading.value = true;

  try {
    const playlistId = props.playlistId;
    const itemId = props.item.id;

    const response = await apiClient.post(
      `/playlists/playlists/${playlistId}/update-item-notes/`,
      {
        item_id: itemId,
        notes: form.value.notes,
      },
    );

    const updatedItem = response.data;
    emit("saved", updatedItem);
    emit("close");
  } catch (error: unknown) {
    console.error("Ошибка обновления заметок:", error);
    const axiosError = error as {
      response?: { data?: { detail?: string } };
      message?: string;
    };
    alert(
      "Не удалось обновить заметки: " +
        (axiosError.response?.data?.detail || axiosError.message),
    );
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.edit-item-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.item-preview {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--surface-3);
  border-radius: 0.75rem;
}

.preview-poster {
  width: 80px;
  height: 110px;
  object-fit: cover;
  border-radius: 0.5rem;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.preview-poster.placeholder {
  background: linear-gradient(
    135deg,
    var(--accent) 0%,
    var(--accent-hover) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: white;
}

.preview-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.preview-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.preview-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.form-input {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-default);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  background: var(--surface-1);
  color: var(--text-primary);
  transition: all 0.2s;
  resize: vertical;
  min-height: 120px;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: var(--text-disabled);
}

.form-hint {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
  margin: 0;
}

.quick-notes {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.quick-notes-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.quick-notes-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.quick-note-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-default);
  border-radius: 0.375rem;
  background: var(--surface-3);
  color: var(--text-primary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-note-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(59, 130, 246, 0.1);
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-default);
}

.btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: var(--surface-3);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}

.btn-secondary:hover {
  background: var(--surface-4);
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-primary:hover {
  background: var(--accent-hover);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
