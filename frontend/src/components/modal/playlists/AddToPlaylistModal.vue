<template>
  <BaseModal :show="show" @close="$emit('close')" title="Добавить в плейлист">
    <form @submit.prevent="handleSubmit" class="add-to-playlist-form">
      <div class="form-group">
        <label class="form-label">Выберите плейлист</label>

        <div class="playlists-list">
          <div
            v-for="playlist in playlists"
            :key="playlist.id"
            class="playlist-option"
            :class="{ selected: selectedPlaylistId === (typeof playlist.id === 'number' ? playlist.id : Number(playlist.id) || null) }"
            @click="selectedPlaylistId = typeof playlist.id === 'number' ? playlist.id : Number(playlist.id) || null"
          >
            <div class="playlist-option-cover">
              <img
                v-if="playlist.cover_image"
                :src="playlist.cover_image"
                :alt="playlist.title"
              />
              <div v-else class="cover-placeholder">
                <span>{{ playlist.title.charAt(0).toUpperCase() }}</span>
              </div>
            </div>
            <div class="playlist-option-info">
              <h4 class="playlist-option-title">{{ playlist.title }}</h4>
              <p class="playlist-option-meta">
                {{ playlist.items_count }} аниме
              </p>
            </div>
            <div class="playlist-option-check">
              <span v-if="selectedPlaylistId === playlist.id">✓</span>
            </div>
          </div>
          <button
            v-if="hasMorePlaylists"
            type="button"
            class="btn btn-secondary load-more-btn"
            :disabled="loadingMorePlaylists"
            @click="loadMorePlaylists"
          >
            {{ loadingMorePlaylists ? "Загрузка..." : "Показать ещё" }}
          </button>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Или создайте новый</label>
        <input
          v-model="newPlaylistTitle"
          type="text"
          class="form-input"
          placeholder="Название нового плейлиста"
        />
        <textarea
          v-model="newPlaylistDescription"
          rows="2"
          class="form-input"
          placeholder="Описание (необязательно)"
          style="margin-top: 0.5rem"
        ></textarea>
      </div>

      <div class="form-group">
        <label class="form-label">Заметки</label>
        <textarea
          v-model="form.notes"
          rows="3"
          class="form-input"
          placeholder="Добавьте заметки к аниме..."
        ></textarea>
      </div>

      <div v-if="anime" class="anime-preview">
        <img
          v-if="anime.poster_url"
          :src="anime.poster_url"
          :alt="anime.title_ru"
          class="anime-poster"
        />
        <div class="anime-info">
          <h4 class="anime-title">{{ anime.title_ru }}</h4>
          <div class="anime-meta">
            <span v-if="anime.year"
              ><SakuraIcon name="calendar" /> {{ anime.year }}</span
            >
            <span v-if="anime.score"
              ><SakuraIcon name="star" /> {{ anime.score?.toFixed(1) }}</span
            >
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('close')">
          Отмена
        </button>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="loading || !canSubmit"
        >
          {{ loading ? "Добавление..." : "Добавить" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import BaseModal from "@/components/ui/BaseModal.vue";
import playlistsApi, { type Playlist, type AddToPlaylistRequest } from "@/api/playlists";
import type { AxiosError } from "axios";

interface Anime {
  id: number;
  title_ru: string;
  title_en: string;
  poster_url?: string | null;
  year?: number | null;
  score?: number | null;
}

interface Props {
  show: boolean;
  anime: Anime;
}

interface Emits {
  (e: "close"): void;
  (e: "added"): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const loading = ref(false);
const playlists = ref<Playlist[]>([]);
const selectedPlaylistId = ref<number | null>(null);
const newPlaylistTitle = ref("");
const newPlaylistDescription = ref("");
const playlistsPage = ref(1);
const hasMorePlaylists = ref(false);
const loadingMorePlaylists = ref(false);

const form = ref({
  notes: "",
});

const canSubmit = computed(() => {
  return (
    selectedPlaylistId.value !== null ||
    newPlaylistTitle.value.trim().length > 0
  );
});

watch(
  () => props.show,
  async (show) => {
    if (show) {
      await loadPlaylists();
      selectedPlaylistId.value = null;
      newPlaylistTitle.value = "";
      newPlaylistDescription.value = "";
      form.value.notes = "";
    }
  },
);

const loadPlaylists = async () => {
  try {
    const response = await playlistsApi.getMyPlaylistsPage(1, 20);
    playlists.value = response.data.results;
    playlistsPage.value = 1;
    hasMorePlaylists.value = Boolean(response.data.next);
  } catch (error) {
    console.error("Ошибка загрузки плейлистов:", error);
  }
};

const loadMorePlaylists = async () => {
  if (loadingMorePlaylists.value || !hasMorePlaylists.value) return;
  loadingMorePlaylists.value = true;
  try {
    const nextPage = playlistsPage.value + 1;
    const response = await playlistsApi.getMyPlaylistsPage(nextPage, 20);
    playlists.value.push(...response.data.results);
    playlistsPage.value = nextPage;
    hasMorePlaylists.value = Boolean(response.data.next);
  } catch (error) {
    console.error("Ошибка дозагрузки плейлистов:", error);
  } finally {
    loadingMorePlaylists.value = false;
  }
};

const handleSubmit = async () => {
  if (!canSubmit.value) return;

  loading.value = true;

  try {
    const data: Record<string, unknown> = {
      anime_id: props.anime.id,
      notes: form.value.notes,
    };

    if (selectedPlaylistId.value !== null) {
      data.playlist_id = selectedPlaylistId.value;
    } else {
      data.new_playlist_title = newPlaylistTitle.value;
      data.new_playlist_description = newPlaylistDescription.value;
    }

    await playlistsApi.addToPlaylist(data as unknown as AddToPlaylistRequest);
    emit("added");
    emit("close");
  } catch (error: unknown) {
    console.error("Ошибка добавления в плейлист:", error);
    const axiosError = error as AxiosError;
    alert(
      "Не удалось добавить в плейлист: " +
        ((axiosError.response?.data as Record<string, unknown> | undefined)?.detail || axiosError.message),
    );
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (props.show) {
    loadPlaylists();
  }
});
</script>

<style scoped>
.add-to-playlist-form {
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

.playlists-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
  padding: 0.25rem;
}

.playlist-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 2px solid var(--border-default);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.playlist-option:hover {
  border-color: var(--accent);
  background: var(--surface-3);
}

.playlist-option.selected {
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.1);
}

.playlist-option-cover {
  width: 48px;
  height: 48px;
  border-radius: 0.375rem;
  overflow: hidden;
  flex-shrink: 0;
}

.playlist-option-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(
    135deg,
    var(--accent) 0%,
    var(--accent-hover) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1rem;
}

.playlist-option-info {
  flex: 1;
  min-width: 0;
}

.playlist-option-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.playlist-option-meta {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
  margin: 0;
}

.playlist-option-check {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  font-size: 1.25rem;
  font-weight: 700;
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
}

.form-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: var(--text-disabled);
}

.anime-preview {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--surface-3);
  border-radius: 0.75rem;
}

.anime-poster {
  width: 60px;
  height: 85px;
  object-fit: cover;
  border-radius: 0.5rem;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.anime-poster.placeholder {
  background: linear-gradient(
    135deg,
    var(--accent) 0%,
    var(--accent-hover) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.anime-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.anime-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.anime-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
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
