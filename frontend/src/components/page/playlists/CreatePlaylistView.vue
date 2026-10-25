<template>
  <div class="create-playlist-page">
    <div class="breadcrumb">
      <router-link to="/playlists" class="breadcrumb-link">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
        К плейлистам
      </router-link>
    </div>

    <div class="page-title-wrap">
      <div class="page-title-icon"><SakuraIcon name="folder" /></div>
      <div>
        <h1 class="page-title">{{ pageTitle }}</h1>
        <p class="page-subtitle">{{ pageSubtitle }}</p>
      </div>
    </div>

    <div class="create-layout">
      <div class="form-column">
        <div class="form-card">
          <h2 class="form-card-title">Основное</h2>
          <div class="playlist-cover-preview"><PlaylistCover :posters="selectedAnime.slice(0, 3).map(anime => anime.poster_url)" :priority="true" /></div>

          <div class="form-group">
            <label class="form-label">
              Название <span class="req">*</span>
            </label>
            <input
              v-model="form.title"
              type="text"
              placeholder="Например: Топ романтических аниме"
              class="form-input"
              :class="{ error: titleError }"
              maxlength="100"
              @input="titleError = ''"
            />
            <div v-if="titleError" class="field-error">{{ titleError }}</div>
            <div class="field-hint">{{ form.title.length }}/100</div>
          </div>

          <div class="form-group">
            <label class="form-label">Описание</label>
            <textarea
              v-model="form.description"
              placeholder="Расскажите, что особенного в этой подборке..."
              class="form-textarea"
              rows="4"
              maxlength="500"
            ></textarea>
            <div class="field-hint">{{ form.description.length }}/500</div>
          </div>

          <!-- <div class="form-group topic-options">
            <label class="form-label">Тематики</label>
            <PlaylistTopicPicker v-model="form.topics" :choices="topicOptions" />
            <p v-if="topicError" role="alert">{{ topicError }} <button type="button" @click="loadTopics">Повторить</button></p>
          </div> -->

          <div class="form-group">
            <label class="form-label">Видимость</label>
            <div class="privacy-options">
              <label
                v-for="opt in privacyOptions"
                :key="opt.value"
                :class="[
                  'privacy-option',
                  { active: form.visibility === opt.value },
                ]"
              >
                <input
                  type="radio"
                  :value="opt.value"
                  v-model="form.visibility"
                  style="display: none"
                />
                <div class="privacy-option-icon">
                  <SakuraIcon
                    v-if="isIconName(opt.icon)"
                    :name="opt.icon"
                    :size="20"
                  />
                  <span v-else>{{ opt.icon }}</span>
                </div>
                <div class="privacy-option-info">
                  <span class="privacy-option-label">{{ opt.label }}</span>
                  <span class="privacy-option-desc">{{ opt.desc }}</span>
                </div>
                <div class="privacy-option-check">
                  <svg
                    v-if="form.visibility === opt.value"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="3"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
              </label>
            </div>
          </div>
        </div>

        <div class="create-footer">
          <button @click="router.back()" class="btn-cancel">Отмена</button>
          <button
            @click="createPlaylist"
            :disabled="isSubmitDisabled"
            class="btn-create"
          >
            <div v-if="isSaving" class="spinner-sm"></div>
            <svg
              v-else
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            {{ submitBtnText }}
          </button>
        </div>
      </div>

      <div class="anime-column">
        <div class="form-card search-form-card">
          <h2 class="form-card-title">
            <SakuraIcon name="search" /> Поиск аниме
            <span class="req">*</span>
          </h2>

          <div class="search-wrap">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="search-icon"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              v-model="searchQuery"
              @input="debouncedSearch"
              type="text"
              placeholder="Поиск по названию аниме..."
              class="search-input"
            />
            <button
              v-if="searchQuery"
              @click="clearSearch"
              class="search-clear"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div v-if="isSearching" class="search-loading">
            <div class="spinner-sm-dark"></div>
            <span>Поиск...</span>
          </div>

          <div v-else-if="searchResults.length > 0" class="search-results">
            <div class="results-header">
              <div class="results-label">Результаты поиска:</div>
              <button
                v-if="notAddedCount > 0 || allAddedCount > 0"
                @click="toggleAllResults"
                class="btn-add-all"
                :class="{ 'btn-remove-all': allAddedCount > 0 }"
                type="button"
              >
                <svg
                  v-if="notAddedCount > 0"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                <svg
                  v-else
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
                {{
                  allAddedCount > 0
                    ? `Убрать все (${allAddedCount})`
                    : `Добавить все (${notAddedCount})`
                }}
              </button>
            </div>

            <div class="results-list" ref="resultsList">
              <div
                v-for="anime in sortedResults"
                :key="anime.id"
                @click="addAnime(anime)"
                :class="['result-item', { added: isAdded(anime.id) }]"
              >
                  <img
                    v-if="anime.poster_url"
                    :src="getMediaUrl(anime.poster_url)"
                    :alt="anime.title_ru || anime.title_en"
                    class="result-poster"
                    @error="
                      (e: Event) =>
                        ((e.target as HTMLImageElement).style.display = 'none')
                    "
                  />
                  <div v-else class="result-poster-ph"></div>

                  <div class="result-info">
                    <div class="result-title-row">
                      <span class="result-title">{{ anime.title_ru || anime.title_en }}</span>
                      <!-- <span v-if="isAdded(anime.id)" class="added-badge" title="Уже добавлено">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </span> -->
                    </div>
                    <span class="result-meta">
                      {{ anime.year }}{{ anime.episodes ? ` · ${anime.episodes} эп.` : "" }}<template v-if="anime.score"> · <SakuraIcon name="star" :size="12" /> {{ anime.score.toFixed(1) }}</template>
                    </span>
                  </div>

                  <button
                    v-if="!isAdded(anime.id)"
                    class="btn-add-result"
                    type="button"
                  >
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2.5"
                    >
                      <line x1="12" y1="5" x2="12" y2="19" />
                      <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                  </button>
                  <button
                    v-else
                    @click.stop="removeAnimeById(anime.id)"
                    class="btn-remove-result"
                    type="button"
                    title="Убрать из плейлиста"
                  >
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2.5"
                    >
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              </div>
              <div class="pagination-bottom" v-if="hasMoreResults || searchPage > 1">
                <button
                  v-if="searchPage > 1"
                  @click="prevPage"
                  class="page-nav-btn page-nav-prev"
                  type="button"
                  :disabled="isSearching"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="15 18 9 12 15 6" />
                  </svg>
                </button>
                <span class="page-indicator">Страница {{ searchPage }}</span>
                <button
                  v-if="hasMoreResults"
                  @click="nextPage"
                  class="page-nav-btn page-nav-next"
                  type="button"
                  :disabled="isSearching"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              </div>

<!-- 
              <button
                v-if="hasMoreResults"
                @click="nextPage"
                class="page-nav-btn page-nav-next"
                type="button"
                :disabled="isSearching"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button> -->
            </div>

          <div
            v-else-if="searchQuery.length >= 2 && !isSearching"
            class="search-empty"
          >
            Ничего не найдено по запросу «{{ searchQuery }}»
          </div>
        </div>

        <!-- Pagination at bottom of form-card -->
        
        <!-- <div v-if="selectedAnime.length === 0" class="hint-card">
          <svg
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <rect x="2" y="7" width="20" height="14" rx="2" />
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
          </svg>
          <p>Найдите и добавьте хотя бы одно аниме для создания плейлиста</p>
        </div> -->
      </div>
    </div>

    <Teleport to="body">
      <transition name="toast">
        <div v-if="toastMsg" class="toast-notification">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
          {{ toastMsg }}
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import apiClient, { getMediaUrl } from "@/api/client";
import playlistsApi, { type PlaylistItem, type PlaylistTopic } from "@/api/playlists";
import PlaylistCover from "@/components/Playlists/PlaylistCover.vue";
import PlaylistTopicPicker from "@/components/Playlists/PlaylistTopicPicker.vue";
import { playlistItemAnimeId } from '@/lib/playlistEdit';
import type { Anime } from "@/types";
import type { AxiosError } from "axios";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";

const isIconName = (icon: string | undefined): boolean => {
  if (!icon) return false;
  return /^[a-zA-Z][a-zA-Z0-9-]*$/.test(icon);
};

const router = useRouter();
const route = useRoute();

const isEditMode = computed(() => Boolean(route.params.id));
const playlistId = computed(() => String(route.params.id || ""));

const loadTopics = async () => {
  topicError.value = '';
  try { topicOptions.value = (await playlistsApi.discoveryOptions(true)).data.topics; }
  catch { topicError.value = 'Не удалось загрузить тематики'; }
};
onMounted(loadTopics);
const topicOptions = ref<PlaylistTopic[]>([]);
const topicError = ref("");
const form = ref({
  topics: [] as string[],
  title: "",
  description: "",
  visibility: "public" as "public" | "private" | "link",
});

const privacyOptions = [
  {
    value: "public",
    label: "Публичный",
    icon: "globe",
    desc: "Виден всем пользователям",
  },
  {
    value: "private",
    label: "Приватный",
    icon: "lock",
    desc: "Только для вас",
  },
  {
    value: "link",
    label: "По ссылке",
    icon: "link",
    desc: "Доступен по уникальной ссылке",
  },
];

const searchQuery = ref("");
const searchResults = ref<Anime[]>([]);
const isSearching = ref(false);
const searchPage = ref(1);
const hasMoreResults = ref(false);
const selectedAnime = ref<Anime[]>([]);
const originalItems = ref<PlaylistItem[]>([]);

const RESULTS_PER_PAGE = 10;
const resultsList = ref<HTMLElement | null>(null);
const animeNotes = ref<Record<number, string>>({});
const isSaving = ref(false);
const titleError = ref("");
const toastMsg = ref("");
const loadingPlaylist = ref(false);

let searchTimer: ReturnType<typeof setTimeout> | null = null;
let searchController: AbortController | null = null;

const pageTitle = computed(() => {
  if (isEditMode.value) return "Редактирование плейлиста";
  return "Создание нового плейлиста";
});

const pageSubtitle = computed(() => {
  if (isEditMode.value) return "Измените название, описание и состав плейлиста";
  return "Соберите подборку аниме и подедитесь ей с сообществом";
});

const submitBtnText = computed(() => {
  if (isSaving.value) return isEditMode.value ? "Сохранение..." : "Создание...";
  return isEditMode.value ? "Сохранить изменения" : "Создать плейлист";
});

const isSubmitDisabled = computed(() => {
  if (isSaving.value) return true;
  if (form.value.title.trim().length < 3) return true;
  if (selectedAnime.value.length < 1) return true;
  return false;
});

const debouncedSearch = () => {
  if (searchTimer) clearTimeout(searchTimer);
  if (searchQuery.value.length < 2) {
    searchController?.abort();
    searchResults.value = [];
    hasMoreResults.value = false;
    searchPage.value = 1;
    return;
  }
  searchPage.value = 1;
  searchTimer = setTimeout(() => void goToPage(1), 300);
};

const goToPage = async (page: number) => {
  if (page < 1 || searchQuery.value.length < 2) return;
  searchController?.abort();
  const controller = new AbortController();
  searchController = controller;
  const query = searchQuery.value.trim();
  isSearching.value = true;
  try {
    const res = await apiClient.get('/anime/search/', {
      params: { q: query, page, page_size: RESULTS_PER_PAGE },
      signal: controller.signal,
    });
    if (controller.signal.aborted || query !== searchQuery.value.trim()) return;
    searchResults.value = res.data.results || [];
    hasMoreResults.value = Boolean(res.data.has_more);
    searchPage.value = page;
    if (resultsList.value) resultsList.value.scrollTop = 0;
  } catch (error) {
    if (!controller.signal.aborted) {
      searchResults.value = [];
      hasMoreResults.value = false;
    }
  } finally {
    if (searchController === controller) {
      searchController = null;
      isSearching.value = false;
    }
  }
};

const nextPage = () => goToPage(searchPage.value + 1);
const prevPage = () => goToPage(searchPage.value - 1);

const clearSearch = () => {
  searchController?.abort();
  searchQuery.value = "";
  searchResults.value = [];
  hasMoreResults.value = false;
  searchPage.value = 1;
};

const isAdded = (animeId: number) => {
  return selectedAnime.value.some((a) => a.id === animeId);
};

const sortedResults = computed(() => {
  return [...searchResults.value].sort((a, b) => {
    const aAdded = isAdded(a.id);
    const bAdded = isAdded(b.id);
    if (aAdded && !bAdded) return -1;
    if (!aAdded && bAdded) return 1;
    return 0;
  });
});

const notAddedCount = computed(() => {
  return searchResults.value.filter((a) => !isAdded(a.id)).length;
});

const allAddedCount = computed(() => {
  return searchResults.value.filter((a) => isAdded(a.id)).length;
});

const addAllResults = () => {
  const toAdd = searchResults.value.filter((a) => !isAdded(a.id));
  for (const anime of toAdd) {
    addAnime(anime);
  }
};

const removeAllResults = () => {
  const toRemove = searchResults.value.filter((a) => isAdded(a.id));
  for (const anime of toRemove) {
    removeAnimeById(anime.id);
  }
};

const toggleAllResults = () => {
  if (allAddedCount.value > 0) {
    removeAllResults();
  } else {
    addAllResults();
  }
};

const addAnime = (anime: Anime) => {
  if (isAdded(anime.id)) return;
  selectedAnime.value.push(anime);
  animeNotes.value[anime.id] = "";
};

const removeAnime = (index: number) => {
  const anime = selectedAnime.value[index];
  if (anime) {
    delete animeNotes.value[anime.id];
  }
  selectedAnime.value.splice(index, 1);
};

const removeAnimeById = (animeId: number) => {
  const index = selectedAnime.value.findIndex((a) => a.id === animeId);
  if (index !== -1) {
    removeAnime(index);
  }
};

const createPlaylist = async () => {
  if (isSubmitDisabled.value) return;

  if (form.value.title.trim().length < 3) {
    titleError.value = "Название должно содержать минимум 3 символов";
    return;
  }

  isSaving.value = true;
  try {
    const payload = {
      title: form.value.title.trim(), description: form.value.description.trim(),
      visibility: form.value.visibility, topics: form.value.topics,
      items: selectedAnime.value.map(anime => ({ anime_id: anime.id, notes: animeNotes.value[anime.id] || '' })),
    };
    const saved = isEditMode.value && playlistId.value
      ? await playlistsApi.updatePlaylist(playlistId.value, payload)
      : await playlistsApi.createPlaylist(payload);
    await router.push(`/playlist/${saved.data.id}`);
  } catch (err) {
    const axiosError = err as AxiosError;
    const data = axiosError.response?.data as { title?: string[]; detail?: string; topics?: string[]; items?: string[] } | undefined;
    const msg = data?.title?.[0] || data?.topics?.[0] || (typeof data?.items?.[0] === "string" ? data.items[0] : "") || data?.detail || "Ошибка сохранения плейлиста";
    titleError.value = msg;
  } finally {
    isSaving.value = false;
  }
};

const loadPlaylistForEdit = async () => {
  if (!isEditMode.value || !playlistId.value) return;
  loadingPlaylist.value = true;
  try {
    const res = await playlistsApi.getPlaylist(playlistId.value, true);
    const playlist = res.data;
    form.value.topics = playlist.topics || [];
    form.value.title = playlist.title;
    form.value.description = playlist.description || "";
    form.value.visibility = (playlist.visibility || "public") as "public" | "private" | "link";

    const items = playlist.items || [];
    originalItems.value = items;
    selectedAnime.value = items
      .map((item) => ({
        id: playlistItemAnimeId(item),
        title_ru: item.anime_title,
        title_en: item.anime_title_en,
        poster_url: item.anime_poster || undefined,
        year: item.anime_year,
        episodes: undefined,
        score: item.anime_score,
      }))
      .filter((a) => Boolean(a.id)) as Anime[];

    for (const item of items) {
      if (item.notes) {
        animeNotes.value[playlistItemAnimeId(item)] = item.notes;
      }
    }
  } catch (err) {
    console.error("Failed to load playlist for edit:", err);
    titleError.value = "Не удалось загрузить плейлист";
  } finally {
    loadingPlaylist.value = false;
  }
};

onMounted(async () => {
  if (isEditMode.value) {
    await loadPlaylistForEdit();
  }
});

watch(
  () => route.query.reload,
  () => {
    if (isEditMode.value && route.query.reload) {
      loadPlaylistForEdit();
    }
  },
);

const showToast = (msg: string) => {
  toastMsg.value = msg;
  setTimeout(() => {
    toastMsg.value = "";
  }, 3000);
};
</script>

<style scoped>
.playlist-cover-preview { position: relative; width: min(100%, 190px); aspect-ratio: 2 / 3; border-radius: var(--radius-lg); overflow: hidden; margin: 0 auto 1.25rem; }

.topic-options { border: 0; padding: 0; min-width: 0; }
.topic-options label { display: inline-flex; align-items: center; gap: 0.4rem; margin: 0.3rem 0.8rem 0.3rem 0; color: var(--text-primary); font-size: 0.85rem; }
.topic-options input { accent-color: var(--accent); }

.create-playlist-page {
  padding: 2rem 1rem;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
}

/* Breadcrumb */
.breadcrumb {
  margin-bottom: 1.5rem;
}
.breadcrumb-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-decoration: none;
  transition: color 0.2s;
}
.breadcrumb-link:hover {
  color: var(--accent);
}

/* Заголовок */
.page-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
}
.page-title-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
}
.page-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
}
.page-subtitle {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  margin: 0;
}

/* Layout */
.create-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 1rem;
  align-items: stretch;
}

/* Form card */
.form-card {
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg, 0.75rem);
  padding: 1.5rem;
  margin-bottom: 0rem;
}

.search-form-card {
  display: flex;
  flex-direction: column;
  height: 93.5%;
  min-height: 700px;
}

.search-form-card .search-results {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.form-card-title {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 1.25rem;
}

.form-group {
  margin-bottom: 1.25rem;
}
.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}
.req {
  color: var(--accent-3);
}
.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem 0.875rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: var(--text-primary);
  background: var(--surface-4);
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
  font-family: inherit;
}
.form-input:focus,
.form-textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
  background: var(--surface-3);
}
.form-input.error {
  border-color: #ef4444;
}
.form-textarea {
  resize: vertical;
  min-height: 100px;
}
.field-error {
  font-size: 0.8125rem;
  color: #ef4444;
  margin-top: 0.375rem;
}
.field-hint {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
  text-align: right;
}

/* Privacy options */
.privacy-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.privacy-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: 0.625rem;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}
.privacy-option:hover {
  border-color: var(--accent);
}
.privacy-option.active {
  background: rgba(58, 134, 255, 0.08);
  border-color: var(--accent);
}
.privacy-option-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}
.privacy-option-info {
  flex: 1;
}
.privacy-option-label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}
.privacy-option-desc {
  display: block;
  font-size: 0.78rem;
  color: var(--text-tertiary);
}
.privacy-option-check {
  width: 22px;
  height: 22px;
  border: 2px solid var(--border-strong);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}
.privacy-option.active .privacy-option-check {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

/* Create footer */
.create-footer {
  display: flex;
  margin-top: 1rem;
  gap: 0.75rem;
}
.btn-cancel {
  flex: 1;
  padding: 0.875rem;
  background: transparent;
  border: 1px solid var(--border-strong);
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.btn-cancel:hover {
  background: var(--surface-4);
}
.btn-create {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem;
  background: var(--accent);
  border: none;
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-create:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(58, 134, 255, 0.35);
}
.btn-create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Search */
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
}
.search-icon {
  position: absolute;
  left: 0.875rem;
  color: var(--text-tertiary);
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 2.75rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  color: var(--text-primary);
  background: var(--surface-4);
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}
.search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
  background: var(--surface-3);
}
.search-clear {
  position: absolute;
  right: 0.75rem;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}
.search-clear:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.search-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.search-results {
  margin-top: 0.25rem;
}
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.results-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.btn-add-all {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background: rgba(34, 197, 94, 0.15);
  border: none;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #22c55e;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-add-all:hover {
  background: rgba(34, 197, 94, 0.25);
  transform: translateY(-1px);
}
.btn-add-all.btn-remove-all {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.btn-add-all.btn-remove-all:hover {
  background: rgba(239, 68, 68, 0.25);
}
.result-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.15s;
}
.result-item:hover:not(.added) {
  background: var(--surface-4);
}
.result-item.added {
  opacity: 0.6;
  cursor: default;
}
.result-poster {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: 3px;
  flex-shrink: 0;
}
.result-poster-ph {
  width: 40px;
  height: 56px;
  background: var(--surface-4);
  border-radius: 3px;
  flex-shrink: 0;
}
.result-info {
  flex: 1;
  min-width: 0;
}
.result-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.result-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.15rem;
}
.added-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: rgba(34, 197, 94, 0.2);
  border-radius: 50%;
  color: #22c55e;
  flex-shrink: 0;
  transition: all 0.2s;
}
.added-badge:hover {
  background: #22c55e;
  color: #fff;
}
.result-meta {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}
.btn-add-result {
  width: 30px;
  height: 30px;
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  border: none;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
}
.btn-add-result:hover {
  background: var(--accent-hover);
  transform: scale(1.1);
}
.btn-remove-result {
  width: 30px;
  height: 30px;
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.15);
  border: none;
  border-radius: 50%;
  color: #ef4444;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
}
.btn-remove-result:hover {
  background: #ef4444;
  color: #fff;
  transform: scale(1.1);
}
.added-badge {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 197, 94, 0.15);
  border-radius: 50%;
  color: #22c55e;
  font-weight: 700;
  font-size: 0.875rem;
  flex-shrink: 0;
}
.search-empty {
  padding: 1.5rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

/* Pagination for search results */
.results-paginated {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.page-nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
.page-nav-btn:hover:not(:disabled) {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  transform: scale(1.1);
  box-shadow: 0 4px 16px rgba(255, 126, 179, 0.4);
}
.page-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.results-list {
  flex: 1;
  min-width: 0;
  min-height: 85%;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 0.25rem;
}
.results-list::-webkit-scrollbar {
  width: 6px;
}
.results-list::-webkit-scrollbar-track {
  background: transparent;
}
.results-list::-webkit-scrollbar-thumb {
  background: var(--surface-6);
  border-radius: 3px;
}

.page-indicator {
  display: flex;
  justify-content: center;
  padding: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.pagination-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 1rem;
  margin-top: auto;
  border-top: 1px solid var(--border-subtle);
}

/* Hint card */
.hint-card {
  background: var(--surface-3);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-lg, 0.75rem);
  padding: 2rem;
  text-align: center;
  color: var(--text-tertiary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.hint-card p {
  margin: 0;
  font-size: 0.9rem;
}

/* Spinners */
.spinner-sm {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.spinner-sm-dark {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Toast */
.toast-notification {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 2rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  z-index: 9999;
  white-space: nowrap;
}
.toast-notification svg {
  color: #22c55e;
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(16px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}

/* Responsive */
@media (max-width: 900px) {
  .create-layout {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 767px) {
  .create-playlist-page {
    padding: 1rem;
  }
  .page-title {
    font-size: 1.375rem;
  }
  .create-footer {
    flex-direction: column;
  }
  .btn-cancel,
  .btn-create {
    flex: none;
    width: 100%;
  }
}
</style>
