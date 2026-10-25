<template>
  <div class="add-anime-page">
    <div class="page-header">
      <h1><SakuraIcon name="plus" /> Пополнить каталог</h1>
      <p class="page-description">
        Введите название -мы добавим в каталог.
      </p>
    </div>

    <div v-if="!isAuthenticated" class="login-notice">
      <SakuraIcon name="lock" />
      <span>
        Чтобы добавлять аниме, нужно войти -
        <router-link to="/login" class="link">войти в аккаунт</router-link>
      </span>
    </div>

    <!-- <div class="add-options">
      <label class="dp-toggle-row">
        <span class="dp-toggle-text">
          <span class="dp-toggle-title">Скачивать постеры на сервер</span>
          <span class="dp-toggle-desc">Сохранять постеры локально в каталоге вместо использования внешних ссылок Kodik</span>
        </span>
        <button type="button" role="switch" aria-label="Скачивать постеры на сервер" :aria-checked="downloadPosters" class="dp-switch" :class="{ on: downloadPosters }" @click="downloadPosters = !downloadPosters">
          <span class="dp-switch-thumb" />
        </button>
      </label>
    </div> -->

    <!-- ===================== ПОИСК ===================== -->
    <div class="search-panel">
      <div class="search-row">
        <input
          v-model="query"
          class="search-input"
          type="text"
          placeholder="Например: Ван Пис, Наруто, Атака титанов..."
          @keyup.enter="search"
        />
        <button
          class="btn-primary"
          :disabled="searching || query.trim().length < 2"
          @click="search"
        >
          <SakuraIcon v-if="searching" name="hourglass" :size="18" />
          <template v-else><SakuraIcon name="search" :size="18" /></template>
          Искать
        </button>
      </div>
      <div v-if="searchError" class="error-text">{{ searchError }}</div>
      <div v-if="availableKinds.length" class="kind-filters">
        <span class="kind-filters-label">Исключить типы:</span>
        <button
          v-for="kind in availableKinds"
          :key="kind"
          :class="['kind-chip', { 'kind-chip-active': isKindExcluded(kind) }]"
          @click="toggleExcludedKind(kind)"
        >
          {{ kindLabel(kind) }}
        </button>
        <button
          :class="['kind-chip', { 'kind-chip-active': excludeNotInKodik }]"
          @click="excludeNotInKodik = !excludeNotInKodik"
        >
          Нет в Kodik
        </button>
      </div>
    </div>

    <!-- ===================== РЕЗУЛЬТАТЫ ===================== -->
    <div v-if="groups.length" class="results-section">
      <div v-for="(group, gi) in groups" :key="gi" class="group-block">
        <div class="group-head">
          <div class="group-title">
            <SakuraIcon :name="group.is_franchise ? 'network' : 'film'" :size="18" />
            <span>{{ group.name }}</span>
            <span v-if="group.year" class="group-year">{{ group.year }}</span>
            <span v-if="group.items.length > 1 || group.is_franchise" class="group-count">
              {{ filteredItems(group.items).length }} тайтлов
            </span>
          </div>
          <button
            class="btn-add-all"
            :disabled="!isAuthenticated || bulkAdding || getMissingCount(group) === 0"
            @click="addGroup(group)"
          >
            <SakuraIcon
              :name="bulkAdding ? 'hourglass' : 'download'"
              :size="16"
            />
            {{
              bulkAdding
                ? (group.is_franchise ? "Добавляем франшизу..." : "Добавляем...")
                : getMissingCount(group) > 0
                  ? (group.is_franchise
                      ? `Добавить отсутствующее (${getMissingCount(group)})`
                      : `Добавить отсутствующее (${getMissingCount(group)})`)
                  : (group.is_franchise
                      ? "Вся франшиза уже в каталоге"
                      : "Все уже в каталоге")
            }}
          </button>
        </div>

        <!-- Прогресс импорта -->
        <div v-if="bulkAdding" class="import-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: importProgress.percent + '%' }"></div>
          </div>
          <div class="progress-info">
            <span>{{ importProgress.current_title || 'Подготовка...' }}</span>
            <span>{{ importProgress.current }} / {{ importProgress.total }}</span>
            <span>({{ importProgress.percent }}%)</span>
          </div>
        </div>

        <!-- Сетка карточек -->
        <div class="results-grid">
          <div
            v-for="item in getFilteredGroupItems(group)"
            :key="item.shikimori_id"
            class="result-card"
            :class="{ 'result-card-link': item.exists_in_db && item.anime_slug }"
            :role="item.exists_in_db && item.anime_slug ? 'link' : undefined"
            :tabindex="item.exists_in_db && item.anime_slug ? 0 : undefined"
            @click="openExistingAnime(item)"
            @keydown.enter="openExistingAnime(item)"
            @keydown.space.prevent="openExistingAnime(item)"
          >
            <div class="poster-wrap">
              <img
                v-if="item.poster_url"
                :src="item.poster_url"
                :alt="item.title_ru"
                loading="lazy"
              />
              <div v-else class="poster-placeholder">
                <SakuraIcon name="film" :size="28" />
              </div>
            </div>
            <div class="card-info">
              <div class="card-title">
                {{ getDisplayTitle(item) }}
                <span v-if="item.kodik_available === false" class="chip chip-warning">Нет в Kodik</span>
              </div>
              <div class="card-meta">
                <span v-if="item.title_en && getDisplayTitle(item) !== item.title_en">{{ item.title_en }}</span>
                <span v-if="item.year">{{ item.year }}</span>
                <span class="chip">{{ kindLabel(item.kind) }}</span>
                <span v-if="item.episodes" class="chip">
                  {{ item.episodes }} серий
                </span>
                <span v-if="item.total_duration" class="chip">
                  {{ formatDuration(item.total_duration) }}
                </span>
              </div>
              <button
                class="btn-add"
                :disabled="!isAuthenticated || addingSid !== null || item.exists_in_db"
                @click.stop="addAnime(item)"
              >
                <SakuraIcon
                  :name="addingSid === item.shikimori_id ? 'hourglass' : 'download'"
                  :size="16"
                />
                {{
                  addingSid === item.shikimori_id
                    ? "Добавляем..."
                    : item.exists_in_db
                      ? "Уже в каталоге"
                      : item.kodik_available === false
                        ? "Запросить добавление"
                        : "Добавить"
                }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="hasMore && !searching" class="load-more-container">
      <button class="btn-primary" @click="search(false)">
        Загрузить еще
      </button>
    </div>

    <div v-else-if="searched && !searching && !groups.length && !searchError" class="no-results">
      Ничего не найдено по запросу «{{ query }}». Попробуйте другое название
      (русское или английское).
    </div>

    <!-- ===================== РЕЗУЛЬТАТ ДОБАВЛЕНИЯ ===================== -->
    <div v-if="addResult" class="add-result" :class="{ ok: addResult.ok }">
      <SakuraIcon :name="addResult.ok ? 'check' : 'alert-circle'" :size="18" />
      <div>
        <strong>{{ addResult.message }}</strong>
        <template v-if="addResult.links.length">
          <span class="links-sep">|</span>
          <router-link
            v-for="l in addResult.links"
            :key="l.slug"
            :to="`/anime/${l.slug}`"
            class="link"
          >{{ l.title }} <SakuraIcon name="arrow-right" :size="16" /></router-link>
        </template>
      </div>
    </div>

    <!-- ===================== МОИ ЗАПРОСЫ ===================== -->
    <div v-if="myRequests.length" class="requests-section">
      <div class="section-title">Мои запросы</div>
      <div class="requests-list">
        <div v-for="r in myRequests" :key="r.id" class="request-row">
          <span :class="['req-status', `req-${r.status}`]">
            {{ requestStatusText(r.status) }}
          </span>
          <span class="req-title">{{ r.title }}</span>
          <span v-if="r.count > 1" class="req-count">
            {{ r.count }} тайтлов
          </span>
          <router-link v-if="r.slug" :to="`/anime/${r.slug}`" class="link"><SakuraIcon name="arrow-right" :size="16" /></router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import apiClient from "@/api/client";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { useAuthStore } from "@/stores/auth";
import { formatDuration } from "@/utils/normalizers";

interface SearchItem {
  shikimori_id: number;
  kodik_id?: string;
  title_ru: string;
  title_en: string;
  year?: number;
  kind: string;
  status: string;
  episodes?: number;
  total_duration?: number;
  poster_url: string;
  kodik_available?: boolean;
  exists_in_db: boolean;
  anime_slug?: string | null;
}

interface SearchGroup {
  name: string;
  year?: number;
  items: SearchItem[];
  is_franchise?: boolean;
}

const authStore = useAuthStore();
const router = useRouter();
const isAuthenticated = computed(() => authStore.isAuthenticated);

const openExistingAnime = (item: SearchItem) => {
  if (item.exists_in_db && item.anime_slug) {
    router.push(`/anime/${item.anime_slug}`);
  }
};

const query = ref("");
const groups = ref<SearchGroup[]>([]);
const searching = ref(false);
const searched = ref(false);
const searchError = ref("");
const addingSid = ref<number | null>(null);
const bulkAdding = ref(false);
const importProgress = ref({ total: 0, current: 0, current_title: "", percent: 0 });
const excludedKinds = ref<Set<string>>(new Set());
const excludeNotInKodik = ref(false);
const downloadPosters = ref(false);

const addResult = ref<{
  ok: boolean;
  message: string;
  links: { slug: string; title: string }[];
} | null>(null);

const myRequests = ref<{ id: number; title: string; status: string; slug?: string; count: number }[]>([]);

const getDisplayTitle = (item: { title_ru: string; title_en: string }) => {
  const ru = item.title_ru || '';
  const en = item.title_en || '';
  if (ru && /[а-яёА-ЯЁ]/.test(ru)) return ru;
  return en || ru;
};

const kindLabel = (kind: string) => {
  const map: Record<string, string> = {
    tv: "Сериал",
    tv_special: "ТВ-спешл",
    special: "Спешл",
    movie: "Фильм",
    ova: "OVA",
    ona: "ONA",
    music: "Клип",
  };
  return map[kind] || kind || "-";
};

const availableKinds = computed(() => {
  const kinds = new Set<string>();
  for (const group of groups.value) {
    for (const item of group.items) {
      if (item.kind) kinds.add(item.kind);
    }
  }
  return Array.from(kinds).sort();
});

const toggleExcludedKind = (kind: string) => {
  const set = new Set(excludedKinds.value);
  if (set.has(kind)) set.delete(kind);
  else set.add(kind);
  excludedKinds.value = set;
};

const isKindExcluded = (kind: string) => excludedKinds.value.has(kind);

const filteredItems = (items: SearchItem[]) => items.filter((item) => {
  if (isKindExcluded(item.kind || "tv")) return false;
  if (excludeNotInKodik.value && item.kodik_available === false) return false;
  return true;
});

const getFilteredGroupItems = (group: SearchGroup) => filteredItems(group.items);

const requestStatusText = (status: string) => {
  const map: Record<string, string> = {
    added: "Добавлено",
    duplicate: "Уже было",
    failed: "Ошибка",
    pending: "Ожидает",
  };
  return map[status] || status;
};

const page = ref(1);
const hasMore = ref(false);

const search = async (resetPage: boolean | KeyboardEvent | PointerEvent = true) => {
  const q = query.value.trim();
  if (q.length < 2 || searching.value) return;
  searching.value = true;
  searchError.value = "";
  searched.value = true;
  addResult.value = null;
  if (resetPage) {
    page.value = 1;
  }
  try {
    const { data } = await apiClient.get("/anime/kodik/search-candidates/", {
      params: { q, page: page.value, page_size: 20 },
    });
    if (resetPage) {
      groups.value = data.groups || [];
    } else {
      groups.value = [...groups.value, ...(data.groups || [])];
    }
    hasMore.value = (data.groups || []).length >= 20;
    if (data.error) searchError.value = data.error;
  } catch (e) {
    searchError.value = "Не удалось выполнить поиск, попробуйте позже";
    groups.value = [];
  } finally {
    searching.value = false;
  }
};

const showAddResult = (
  ok: boolean,
  message: string,
  items: { slug?: string; title?: string }[] = [],
) => {
  addResult.value = {
    ok,
    message,
    links: items
      .filter((i) => i.slug)
      .slice(0, 6)
      .map((i) => ({ slug: i.slug as string, title: i.title || "" })),
  };
};

const addAnime = async (item: SearchItem) => {
  if (addingSid.value !== null) return;
  if (isKindExcluded(item.kind || "tv")) {
    showAddResult(false, `Тип "${kindLabel(item.kind)}" исключён из добавления`);
    return;
  }
  if (excludeNotInKodik.value && item.kodik_available === false) {
    showAddResult(false, "Элемент не найден в Kodik и исключён из добавления");
    return;
  }
  addingSid.value = item.shikimori_id;
  addResult.value = null;
  try {
    const { data } = await apiClient.post("/anime/kodik/user-add/", {
      shikimori_id: item.shikimori_id,
      title: item.title_ru,
      download_posters: downloadPosters.value,
    });
    const first = data?.results?.[0] || data;
    showAddResult(true, first?.message || data?.message || "Готово", [
      { slug: first?.slug, title: first?.title || item.title_ru },
    ]);
    await loadMyRequests();
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } }; message?: string };
    showAddResult(false, err?.response?.data?.error || err?.message || "Не удалось добавить аниме");
  } finally {
    addingSid.value = null;
  }
};

const addGroup = async (group: SearchGroup) => {
  if (bulkAdding.value) return;
  const filtered = filteredItems(group.items);
  if (!filtered.length) {
    showAddResult(
      false,
      group.is_franchise
        ? "Ничего не найдено в Kodik или все исключены"
        : "Ни одного тайтла нет в Kodik или все исключены",
    );
    return;
  }
  const missingIds = filtered.filter((item) => !item.exists_in_db).map((item) => item.shikimori_id);
  if (!missingIds.length) {
    showAddResult(false, group.is_franchise ? "Вся франшиза уже в каталоге" : "Все уже в каталоге");
    return;
  }
  bulkAdding.value = true;
  addResult.value = null;
  importProgress.value = { total: 0, current: 0, current_title: "", percent: 0 };
  try {
    const { data } = await apiClient.post("/anime/kodik/user-add/", {
      shikimori_ids: missingIds,
      title: group.name,
      download_posters: downloadPosters.value,
    });

    if (data?.progress_token) {
      const progressToken = data.progress_token;
      importProgress.value = { total: 0, current: 0, current_title: "Подготовка...", percent: 0 };
      const pollInterval = setInterval(async () => {
        try {
          const { data: progressData } = await apiClient.get("/anime/kodik/user-add/progress/", {
            params: { token: progressToken },
          });
          importProgress.value = progressData;
          if (progressData.current >= progressData.total) {
            clearInterval(pollInterval);
          }
        } catch {
          clearInterval(pollInterval);
        }
      }, 1000);

      await new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (importProgress.value.current >= importProgress.value.total) {
            clearInterval(pollInterval);
            clearInterval(checkInterval);
            resolve(true);
          }
        }, 500);
      });
    }

    const okItems = (data?.results || []).filter(
      (r: { ok?: boolean }) => r.ok,
    ) as { slug?: string; title?: string }[];
    showAddResult(
      okItems.length > 0,
      data?.message || `Добавлено: ${okItems.length}`,
      okItems,
    );
    await loadMyRequests();
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } }; message?: string };
    showAddResult(
      false,
      err?.response?.data?.error ||
        err?.message ||
        (group.is_franchise ? "Не удалось добавить франшизу" : "Не удалось добавить тайтлы"),
    );
  } finally {
    bulkAdding.value = false;
    importProgress.value = { total: 0, current: 0, current_title: "", percent: 0 };
  }
};

const getMissingCount = (group: SearchGroup) => {
  return filteredItems(group.items).filter((item) => !item.exists_in_db).length;
};

const loadMyRequests = async () => {
  if (!isAuthenticated.value) return;
  try {
    const { data } = await apiClient.get("/anime/kodik/my-requests/");
    myRequests.value = (data.results || []).slice(0, 20);
  } catch {
    /* ignore */
  }
};

onMounted(loadMyRequests);
</script>

<style scoped>
.add-anime-page {
  padding: 2.5rem;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}
.page-header {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.page-header h1 {
  font-size: 1.65rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  letter-spacing: 0.01em;
}
.page-description {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin: 0;
  line-height: 1.55;
  max-width: 720px;
}

.login-notice {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
  font-size: 0.95rem;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 28%, transparent);
  color: var(--text-primary);
}
.link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
}
.link:hover {
  text-decoration: underline;
}

.search-panel {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease;
}
.search-row {
  display: flex;
  gap: 0.75rem;
}
.search-input {
  flex: 1;
  height: 48px;
  padding: 0 16px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  outline: none;
  font-size: 0.95rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 15%, transparent);
}
.error-text {
  color: var(--danger);
  font-size: 0.85rem;
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.kind-filters {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  flex-wrap: wrap;
}
.kind-filters-label {
  font-size: 0.82rem;
  color: var(--text-secondary);
  font-weight: 600;
}
.kind-chip {
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-3);
  color: var(--text-secondary);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}
.kind-chip:hover {
  border-color: var(--accent);
}
.kind-chip-active {
  background: color-mix(in srgb, var(--danger) 15%, transparent);
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 28%, transparent);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  height: 48px;
  padding: 0 24px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.1s ease, opacity 0.2s ease;
  white-space: nowrap;
}
.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}
.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-sm {
  height: 40px;
  font-size: 0.85rem;
  padding: 0 18px;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}
.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}
.group-block {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1.25rem;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.group-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
}
.group-title svg {
  color: var(--accent);
  flex-shrink: 0;
}
.group-year {
  color: var(--text-tertiary);
  font-size: 0.85rem;
  font-weight: 400;
}
.group-count {
  background: var(--surface-4);
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.75rem;
  font-weight: 700;
}
.btn-add-all {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  height: 38px;
  padding: 0 18px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.1s ease;
}
.btn-add-all:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}
.btn-add-all:active:not(:disabled) {
  transform: translateY(0);
}
.btn-add-all:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.import-progress {
  margin-top: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}
.progress-bar {
  height: 6px;
  background: var(--surface-4);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}
.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width 0.3s ease;
}
.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: var(--text-secondary);
  gap: 0.5rem;
}
.progress-info span:first-child {
  font-weight: 500;
}
.progress-info span:last-child {
  color: var(--accent);
  font-weight: 700;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1rem;
}
.result-card {
  display: flex;
  gap: 1rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1rem;
  transition: border-color 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
}
.result-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.result-card-link {
  cursor: pointer;
}
.result-card-link:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}
.poster-wrap {
  flex: 0 0 96px;
  height: 136px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface-4);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-xs);
}
.poster-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}
.result-card:hover .poster-wrap img {
  transform: scale(1.05);
}
.poster-placeholder {
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}
.card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 0.35rem;
}
.card-title {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.95rem;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-line-orient: vertical;
  overflow: hidden;
}
.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}
.chip {
  background: var(--surface-4);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.72rem;
  color: var(--text-secondary);
  font-weight: 500;
  border: 1px solid var(--border-subtle);
}
.chip-warning {
  background: color-mix(in srgb, var(--warning) 15%, transparent);
  color: var(--warning);
  border-color: color-mix(in srgb, var(--warning) 28%, transparent);
}
.btn-add {
  margin-top: auto;
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.1s ease;
}
.btn-add:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}
.btn-add:active:not(:disabled) {
  transform: translateY(0);
}
.btn-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.no-results {
  color: var(--text-tertiary);
  padding: 2rem;
  text-align: center;
  font-size: 0.95rem;
}

.add-result {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
  font-size: 0.9rem;
  flex-wrap: wrap;
  border: 1px solid transparent;
  line-height: 1.5;
}
.add-result.ok {
  background: color-mix(in srgb, var(--success) 10%, transparent);
  color: var(--success);
  border-color: color-mix(in srgb, var(--success) 25%, transparent);
}
.add-result:not(.ok) {
  background: color-mix(in srgb, var(--danger) 10%, transparent);
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 25%, transparent);
}
.add-result .link {
  margin-left: 0.4rem;
}
.links-sep {
  margin: 0 0.3rem;
  opacity: 0.5;
}

.requests-section {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1.25rem;
  box-shadow: var(--shadow-sm);
}
.section-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}
.requests-list {
  display: flex;
  flex-direction: column;
}
.request-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.88rem;
  transition: background 0.15s ease;
}
.request-row:hover {
  background: var(--surface-3);
}
.request-row:last-child {
  border-bottom: none;
}
.req-status {
  flex: 0 0 auto;
  font-size: 0.72rem;
  font-weight: 800;
  border-radius: 999px;
  padding: 3px 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.req-added {
  background: color-mix(in srgb, var(--success) 15%, transparent);
  color: var(--success);
}
.req-duplicate {
  background: color-mix(in srgb, var(--info) 15%, transparent);
  color: var(--info);
}
.req-failed {
  background: color-mix(in srgb, var(--danger) 15%, transparent);
  color: var(--danger);
}
.req-pending {
  background: color-mix(in srgb, var(--warning) 15%, transparent);
  color: var(--warning);
}
.req-title {
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}
.req-count {
  flex: 0 0 auto;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  background: var(--surface-4);
  border-radius: 999px;
  padding: 2px 10px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .add-anime-page {
    padding: 1.25rem;
  }
  .search-row {
    flex-direction: column;
  }
  .results-grid {
    grid-template-columns: 1fr;
  }
  .group-head {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 520px) {
  .add-anime-page {
    padding: 1rem;
    gap: 1.25rem;
  }
  .page-header h1 {
    font-size: 1.35rem;
  }
  .result-card {
    flex-direction: column;
  }
  .poster-wrap {
    flex: 0 0 auto;
    height: 180px;
  }
}

.dp-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  cursor: pointer;
  user-select: none;
}
.dp-toggle-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dp-toggle-title {
  font-size: var(--text-md, 0.9375rem);
  font-weight: 600;
  color: var(--text-primary, #fff);
}
.dp-toggle-desc {
  font-size: var(--text-sm, 0.75rem);
  line-height: 1.45;
  color: var(--text-tertiary, #9aa);
  max-width: 560px;
}
.dp-switch {
  position: relative;
  width: 52px;
  height: 28px;
  flex-shrink: 0;
  background: var(--surface-5, #2a2340);
  border: 1px solid var(--border-default, #333);
  border-radius: 999px;
  transition: background 0.2s, border-color 0.2s;
}
.dp-switch .dp-switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--text-tertiary, #9aa);
  transition: transform 0.2s, background 0.2s;
}
.dp-switch.on {
  background: var(--accent-subtle, rgba(255, 126, 179, 0.25));
  border-color: var(--accent, #ff7eb3);
}
.dp-switch.on .dp-switch-thumb {
  transform: translateX(24px);
  background: var(--accent, #ff7eb3);
}
.load-more-container {
  text-align: center;
  margin: 2rem 0;
}
</style>
