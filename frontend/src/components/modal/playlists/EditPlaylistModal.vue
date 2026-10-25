<template>
  <BaseModal :show="show" @close="$emit('close')" title="Изменить плейлист">
    <form @submit.prevent="handleSubmit" class="edit-playlist-form">
      <div class="form-group">
        <label for="title" class="form-label">Название плейлиста</label>
        <input
          id="title"
          v-model="form.title"
          type="text"
          required
          class="form-input"
          placeholder="Введите название"
        />
      </div>

      <div class="form-group">
        <label for="description" class="form-label">Описание</label>
        <textarea
          id="description"
          v-model="form.description"
          rows="4"
          class="form-input"
          placeholder="Расскажите о плейлисте"
        ></textarea>
      </div>

      <div class="form-group">
        <label class="form-label">Обложка</label>

        <div class="cover-upload">
          <div v-if="currentCover" class="current-cover">
            <img :src="currentCover" alt="Текущая обложка" />
            <div class="cover-actions">
              <label class="upload-cover-btn">
                <input
                  type="file"
                  accept="image/*"
                  @change="handleCoverUpload"
                  hidden
                />
                <SakuraIcon name="camera" :size="16" />
                Загрузить новую
              </label>
              <button
                type="button"
                class="remove-cover-btn"
                @click="removeCover"
              >
                Удалить обложку
              </button>
            </div>
          </div>

          <div v-else class="cover-placeholder">
            <span class="placeholder-icon"> <SakuraIcon name="folder" /> </span>
            <p>Нет обложки</p>
            <p class="placeholder-text">
              Обложка будет автоматически создана из постеров аниме
            </p>
            <label class="upload-cover-btn-manual">
              <input
                type="file"
                accept="image/*"
                @change="handleCoverUpload"
                hidden
              />
              <SakuraIcon name="camera" :size="16" />
              Загрузить обложку
            </label>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Тип плейлиста</label>
        <div class="radio-group">
          <label
            v-for="opt in visibilityOptions"
            :key="opt.value"
            :class="['radio-option', { active: form.visibility === opt.value }]"
          >
            <input
              v-model="form.visibility"
              type="radio"
              :value="opt.value"
            />
            <span class="radio-label">
              <span class="radio-icon"> <SakuraIcon :name="opt.icon" /> </span>
              <span>{{ opt.label }}</span>
            </span>
          </label>
        </div>
        <p v-if="form.visibility === 'link'" class="radio-desc-hint">
          <SakuraIcon name="link" /> После сохранения будет сгенерирована уникальная ссылка
        </p>
      </div>

      <div class="form-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('close')">
          Отмена
        </button>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? "Сохранение..." : "Сохранить изменения" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import BaseModal from "@/components/ui/BaseModal.vue";
import playlistsApi, { type Playlist, type PlaylistVisibility } from "@/api/playlists";
import type { AxiosError } from "axios";

interface Props {
  show: boolean;
  playlist: Playlist;
}

interface Emits {
  (e: "close"): void;
  (e: "saved", playlist: Playlist): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const loading = ref(false);
const form = ref({
  title: "",
  description: "",
  visibility: "public" as PlaylistVisibility,
});

const visibilityOptions = [
  { value: "public" as PlaylistVisibility, label: "Публичный", icon: "globe" },
  { value: "private" as PlaylistVisibility, label: "Приватный", icon: "lock" },
  { value: "link" as PlaylistVisibility, label: "По ссылке", icon: "link" },
];

const currentCover = computed(() => {
  return props.playlist.cover_image || null;
});

watch(
  () => props.show,
  (show) => {
    if (show && props.playlist) {
      form.value = {
        title: props.playlist.title,
        description: props.playlist.description || "",
        visibility: props.playlist.visibility,
      };
    }
  },
);

const handleSubmit = async () => {
  loading.value = true;

  try {
    const response = await playlistsApi.updatePlaylist(
      props.playlist.id,
      form.value,
    );
    emit("saved", response.data);
    emit("close");
  } catch (error: unknown) {
    console.error("Ошибка обновления плейлиста:", error);
    const axiosError = error as AxiosError;
    const detail = (axiosError.response?.data as { detail?: string })?.detail;
    alert(
      "Не удалось обновить плейлист: " + (detail || axiosError.message),
    );
  } finally {
    loading.value = false;
  }
};

const removeCover = async () => {
  if (!confirm("Удалить обложку?")) return;

  try {
    await playlistsApi.updatePlaylist(props.playlist.id, { cover_image: null });
    emit("saved", { ...props.playlist, cover_image: null });
    emit("close");
  } catch (error: unknown) {
    console.error("Ошибка удаления обложки:", error);
    alert("Не удалось удалить обложку");
  }
};

const handleCoverUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  if (file.size > 5 * 1024 * 1024) {
    alert("Размер файла не должен превышать 5MB");
    return;
  }

  try {
    const response = await playlistsApi.uploadPlaylistCover(
      props.playlist.id,
      file,
    );
    emit("saved", response.data);
    emit("close");
  } catch (error: unknown) {
    console.error("Ошибка загрузки обложки:", error);
    const axiosError = error as AxiosError;
    const detail = (axiosError.response?.data as { detail?: string })?.detail;
    alert(
      "Не удалось загрузить обложку: " + (detail || axiosError.message),
    );
  }
};
</script>

<style scoped>
.edit-playlist-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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
}

.form-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: var(--text-disabled);
}

.cover-upload {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.current-cover {
  position: relative;
  border-radius: 0.75rem;
  overflow: hidden;
}

.current-cover img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
}

.cover-actions {
  position: absolute;
  bottom: 0.75rem;
  right: 0.75rem;
  display: flex;
  gap: 0.5rem;
}

.upload-cover-btn,
.upload-cover-btn-manual {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.9);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.upload-cover-btn:hover,
.upload-cover-btn-manual:hover {
  background: rgba(59, 130, 246, 1);
}

.remove-cover-btn {
  padding: 0.5rem 1rem;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.remove-cover-btn:hover {
  background: rgba(239, 68, 68, 1);
}

.cover-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  border: 2px dashed var(--border-default);
  border-radius: 0.75rem;
  background: var(--surface-3);
  color: var(--text-tertiary);
}

.placeholder-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.placeholder-text {
  font-size: 0.8125rem;
  margin-top: 0.25rem;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-default);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--surface-1);
}

.radio-option.active {
  border-color: var(--accent);
  background: var(--surface-3);
}

.radio-option input[type="radio"] {
  accent-color: var(--accent);
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9375rem;
  color: var(--text-primary);
}

.radio-icon {
  font-size: 1.125rem;
}

.radio-desc {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
}

.radio-desc-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  color: var(--text-tertiary);
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
