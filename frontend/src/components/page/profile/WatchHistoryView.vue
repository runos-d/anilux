<template>
  <div class="history-page">
    <header class="history-header">
      <div class="heading-copy">
        <h1>История просмотров</h1>
        <p>Возвращайтесь к последней серии с того места, где остановились.</p>
      </div>
<!-- 
      <div class="header-actions">
        <span class="sync-note" title="История доступна на всех устройствах">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 17.5A4.5 4.5 0 0 0 18 9a7 7 0 0 0-13.3 2A3.5 3.5 0 0 0 5.5 18H20Z" />
          </svg>
          Синхронизировано
        </span>
        <button
          v-if="summary.total"
          class="clear-history-btn"
          type="button"
          @click="showClearDialog = true"
        >
          Очистить историю
        </button>
      </div> -->
    </header>

    <div class="history-toolbar">
      <label class="history-search">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
        <input
          v-model="search"
          type="search"
          autocomplete="off"
          placeholder="Найти в истории"
          aria-label="Найти в истории просмотров"
          @input="queueSearch"
        />
        <button v-if="search" type="button" aria-label="Очистить поиск" @click="clearSearch">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </label>

      <div class="history-tabs" role="tablist" aria-label="Фильтр истории">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          role="tab"
          :aria-selected="activeState === tab.value"
          :class="{ active: activeState === tab.value }"
          @click="selectState(tab.value)"
        >
          {{ tab.label }}
          <span>{{ summary[tab.countKey] }}</span>
        </button>
      </div>
    </div>

    <div v-if="loading && !items.length" class="history-skeleton" aria-label="Загрузка истории">
      <div v-for="index in 4" :key="index" class="skeleton-row">
        <div class="skeleton-poster"></div>
        <div class="skeleton-copy">
          <i></i><i></i><i></i>
        </div>
      </div>
    </div>

    <div v-else-if="loadError && !items.length" class="history-state">
      <div class="state-icon error-icon">
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="12" r="9" /><path d="M12 7v6M12 17h.01" />
        </svg>
      </div>
      <h2>История не загрузилась</h2>
      <p>Проверьте подключение и попробуйте ещё раз.</p>
      <button type="button" class="state-action" @click="loadHistory(true)">Повторить</button>
    </div>

    <div v-else-if="!items.length" class="history-state">
      <div class="state-icon">
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
          <circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" />
        </svg>
      </div>
      <h2>{{ emptyTitle }}</h2>
      <p>{{ emptyText }}</p>
      <button v-if="search || activeState !== 'all'" type="button" class="state-action" @click="resetFilters">
        Сбросить фильтры
      </button>
      <router-link v-else to="/anime" class="state-action">Перейти в каталог</router-link>
    </div>

    <div v-else class="history-timeline">
      <section v-for="group in groupedItems" :key="group.label" class="history-group">
        <div class="group-heading">
          <h2>{{ group.label }}</h2>
          <span>{{ group.items.length }}</span>
          <div></div>
        </div>

        <article v-for="item in group.items" :key="item.anime_id" class="history-card">
          <router-link :to="animeLink(item)" class="poster-link" :aria-label="`Открыть ${item.title}`">
            <img v-if="posterUrl(item)" :src="posterUrl(item)" :alt="item.title" loading="lazy" />
            <span v-else class="poster-placeholder" aria-hidden="true">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="3" /><path d="m8 3 3 5-3 5 3 5-2 3M16 3l-3 5 3 5-3 5 2 3" />
              </svg>
            </span>
          </router-link>

          <div class="card-main">
            <div class="card-topline">
              <div class="media-meta">
                <span v-if="item.year">{{ item.year }}</span>
                <span v-if="item.score" class="score">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="m12 2.5 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3-5.8 3 1.1-6.5-4.7-4.6 6.5-.9L12 2.5Z" /></svg>
                  {{ item.score.toFixed(1) }}
                </span>
              </div>
              <span class="viewed-at">{{ formatViewedAt(item.last_watched) }}</span>
            </div>

            <router-link :to="animeLink(item)" class="title-link">
              <h3>{{ item.title }}</h3>
              <p v-if="item.title_en && item.title_en !== item.title">{{ item.title_en }}</p>
            </router-link>

            <div class="progress-copy">
              <strong>{{ progressHeadline(item) }}</strong>
              <span>{{ positionLabel(item) }}</span>
            </div>
            <div class="episode-progress" :aria-label="`Прогресс серии ${item.episode_percent}%`">
              <span :style="{ width: `${item.episode_percent}%` }"></span>
            </div>

            <div class="series-progress-row">
              <span>{{ seriesLabel(item) }}</span>
              <div class="series-progress"><span :style="{ width: `${item.series_percent}%` }"></span></div>
              <b>{{ item.series_percent }}%</b>
            </div>
          </div>

          <div class="card-actions">
            <router-link :to="watchLink(item)" class="continue-btn">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor"><path d="m8 5 11 7-11 7V5Z" /></svg>
              {{ actionLabel(item) }}
            </router-link>
            <button
              type="button"
              class="hide-btn"
              :disabled="busyIds.has(item.anime_id)"
              :aria-label="`Скрыть ${item.title} из истории`"
              title="Скрыть из истории"
              @click="hideItem(item)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 3l18 18M10.6 10.7a2 2 0 0 0 2.7 2.7M9.9 4.2A10.5 10.5 0 0 1 12 4c5 0 8.5 4 9.5 8a11.8 11.8 0 0 1-2 4.1M6.6 6.6A11.2 11.2 0 0 0 2.5 12c1 4 4.5 8 9.5 8 1.5 0 2.8-.3 4-.9" />
              </svg>
            </button>
          </div>
        </article>
      </section>

      <button v-if="hasMore" type="button" class="load-more" :disabled="loadingMore" @click="loadMore">
        <span v-if="loadingMore" class="button-spinner"></span>
        {{ loadingMore ? "Загружаем" : "Показать ещё" }}
      </button>
    </div>

    <Transition name="dialog-fade">
      <div v-if="showClearDialog" class="dialog-backdrop" @click.self="showClearDialog = false">
        <div class="clear-dialog" role="dialog" aria-modal="true" aria-labelledby="clear-history-title">
          <div class="dialog-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14M10 10v6M14 10v6" />
            </svg>
          </div>
          <h2 id="clear-history-title">Очистить историю?</h2>
          <p>Карточки исчезнут, но прогресс серий и коллекция сохранятся. Новый просмотр вернёт тайтл в историю.</p>
          <div class="dialog-actions">
            <button type="button" class="dialog-cancel" @click="showClearDialog = false">Отмена</button>
            <button type="button" class="dialog-confirm" :disabled="clearing" @click="clearHistory">
              {{ clearing ? "Очищаем…" : "Очистить" }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { getMediaUrl, isRequestCancelled } from "@/api/client";
import {
  watchHistoryApi,
  type WatchHistoryItem,
  type WatchHistoryState,
  type WatchHistorySummary,
} from "@/api/watchHistory";
import { useToast } from "@/composables/useToast";

const toast = useToast();

const items = ref<WatchHistoryItem[]>([]);
const summary = ref<WatchHistorySummary>({ total: 0, in_progress: 0, watched: 0 });
const search = ref("");
const activeState = ref<WatchHistoryState>("all");
const page = ref(1);
const totalResults = ref(0);
const loading = ref(true);
const loadingMore = ref(false);
const loadError = ref(false);
const showClearDialog = ref(false);
const clearing = ref(false);
const busyIds = ref(new Set<number>());
let searchTimer: ReturnType<typeof setTimeout> | undefined;

const tabs: Array<{ value: WatchHistoryState; label: string; countKey: keyof WatchHistorySummary }> = [
  { value: "all", label: "Все", countKey: "total" },
  { value: "in_progress", label: "Продолжить", countKey: "in_progress" },
  { value: "watched", label: "Просмотренные", countKey: "watched" },
];

const hasMore = computed(() => items.value.length < totalResults.value);
const emptyTitle = computed(() => search.value.trim() ? "Ничего не найдено" : activeState.value === "all" ? "Здесь пока тихо" : "В этом разделе пусто");
const emptyText = computed(() => search.value.trim()
  ? "Попробуйте другое название или сбросьте поиск."
  : activeState.value === "all"
    ? "Начните смотреть аниме — последние серии появятся здесь автоматически."
    : "Попробуйте другой фильтр или выберите аниме в каталоге.");

const groupedItems = computed(() => {
  const result: Array<{ label: string; items: WatchHistoryItem[] }> = [];
  const map = new Map<string, WatchHistoryItem[]>();
  for (const item of items.value) {
    const label = dateGroup(item.last_watched);
    const group = map.get(label) ?? [];
    group.push(item);
    map.set(label, group);
  }
  for (const [label, groupItems] of map) result.push({ label, items: groupItems });
  return result;
});

const loadHistory = async (reset = false) => {
  if (reset) {
    page.value = 1;
    loading.value = true;
  } else {
    loadingMore.value = true;
  }
  loadError.value = false;
  try {
    const data = await watchHistoryApi.list({
      page: page.value,
      page_size: 20,
      state: activeState.value,
      search: search.value.trim() || undefined,
    });
    items.value = reset ? data.results : [...items.value, ...data.results];
    totalResults.value = data.count;
    summary.value = data.summary;
  } catch (error) {
    if (!isRequestCancelled(error)) loadError.value = true;
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

const loadMore = async () => {
  if (loadingMore.value || !hasMore.value) return;
  page.value += 1;
  await loadHistory(false);
};

const selectState = (state: WatchHistoryState) => {
  if (state === activeState.value) return;
  activeState.value = state;
  void loadHistory(true);
};

const queueSearch = () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => void loadHistory(true), 320);
};

const clearSearch = () => {
  search.value = "";
  clearTimeout(searchTimer);
  void loadHistory(true);
};

const resetFilters = () => {
  search.value = "";
  activeState.value = "all";
  void loadHistory(true);
};

const setBusy = (id: number, value: boolean) => {
  const next = new Set(busyIds.value);
  if (value) {
    next.add(id);
  } else {
    next.delete(id);
  }
  busyIds.value = next;
};

const hideItem = async (item: WatchHistoryItem) => {
  if (busyIds.value.has(item.anime_id)) return;
  setBusy(item.anime_id, true);
  try {
    await watchHistoryApi.hide(item.anime_id);
    items.value = items.value.filter((entry) => entry.anime_id !== item.anime_id);
    totalResults.value = Math.max(0, totalResults.value - 1);
    summary.value.total = Math.max(0, summary.value.total - 1);
    if (item.episode_status === "in_progress") summary.value.in_progress = Math.max(0, summary.value.in_progress - 1);
    else if (item.episode_status === "watched" || item.episode_status === "skipped") {
      summary.value.watched = Math.max(0, summary.value.watched - 1);
    }
    toast.info("Убрано из истории", {
      duration: 6000,
      action: {
        label: "Вернуть",
        handler: () => void restoreItem(item.anime_id),
      },
    });
  } catch {
    toast.error("Не удалось скрыть запись");
  } finally {
    setBusy(item.anime_id, false);
  }
};

const restoreItem = async (animeId: number) => {
  try {
    await watchHistoryApi.restore(animeId);
    await loadHistory(true);
  } catch {
    toast.error("Не удалось вернуть запись");
  }
};

const clearHistory = async () => {
  if (clearing.value) return;
  clearing.value = true;
  try {
    await watchHistoryApi.clear();
    showClearDialog.value = false;
    items.value = [];
    totalResults.value = 0;
    summary.value = { total: 0, in_progress: 0, watched: 0 };
    toast.info("История очищена", {
      duration: 7000,
      action: {
        label: "Отменить",
        handler: () => void restoreAll(),
      },
    });
  } catch {
    toast.error("Не удалось очистить историю");
  } finally {
    clearing.value = false;
  }
};

const restoreAll = async () => {
  try {
    await watchHistoryApi.restoreAll();
    await loadHistory(true);
  } catch {
    toast.error("Не удалось восстановить историю");
  }
};

const animeLink = (item: WatchHistoryItem) => `/anime/${item.slug || item.anime_id}`;
const watchLink = (item: WatchHistoryItem) => ({
  name: "anime-watch",
  params: { slug: String(item.slug || item.anime_id) },
  query: {
    season: String(item.continue_season ?? 1),
    episode: String(item.continue_episode),
  },
});
const posterUrl = (item: WatchHistoryItem) => item.poster ? getMediaUrl(item.poster) : "";
const episodeLabel = (item: WatchHistoryItem) => {
  if (item.kind === "movie") return "Фильм";
  if ((item.season_number ?? 1) !== 1) {
    return `S${item.season_number}E${item.episode}`;
  }
  return `${item.episode} серия`;
};
const progressHeadline = (item: WatchHistoryItem) => item.episode_status === "in_progress"
  ? `${episodeLabel(item)} · ${item.episode_percent}%`
  : item.is_series_completed ? "Просмотр завершён" : `${episodeLabel(item)} просмотрена`;
const actionLabel = (item: WatchHistoryItem) => item.episode_status === "in_progress"
  ? "Продолжить" : item.is_series_completed ? "Пересмотреть" : "Следующая серия";
const seriesLabel = (item: WatchHistoryItem) => item.total_episodes
  ? `${item.watched_episodes} из ${item.total_episodes} серий`
  : `${item.watched_episodes} серий просмотрено`;

const formatSeconds = (value: number) => {
  const seconds = Math.max(0, Math.floor(value));
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, "0")}`;
};
const positionLabel = (item: WatchHistoryItem) => item.duration
  ? `${formatSeconds(item.position)} / ${formatSeconds(item.duration)}`
  : item.episode_status === "in_progress" ? "Позиция сохранена" : "Просмотрено";

const dayStart = (date: Date) => new Date(date.getFullYear(), date.getMonth(), date.getDate());
const dateGroup = (value: string) => {
  const date = new Date(value);
  const today = dayStart(new Date());
  const target = dayStart(date);
  const dayDiff = Math.round((today.getTime() - target.getTime()) / 86_400_000);
  if (dayDiff === 0) return "Сегодня";
  if (dayDiff === 1) return "Вчера";
  if (dayDiff < 7) return "На этой неделе";
  const label = new Intl.DateTimeFormat("ru-RU", { month: "long", year: "numeric" }).format(date);
  return label.charAt(0).toUpperCase() + label.slice(1);
};
const formatViewedAt = (value: string) => {
  const date = new Date(value);
  const time = new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit" }).format(date);
  const group = dateGroup(value);
  if (group === "Сегодня") return `Сегодня ${time}`;
  if (group === "Вчера") return `Вчера ${time}`;

  const parts = new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).formatToParts(date);

  const map: Record<string, string> = {};
  for (const p of parts) {
    if (p.type !== "literal") map[p.type] = p.value;
  }
  return `${map.day} ${map.month} ${map.hour}:${map.minute}`;
};

onMounted(() => void loadHistory(true));
onBeforeUnmount(() => clearTimeout(searchTimer));
</script>

<style scoped>
.history-page {
  width: min(1120px, calc(100% - 48px));
  margin: 0 auto;
  padding: 48px 0 80px;
}

.history-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
  margin-bottom: 30px;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.eyebrow-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 5px var(--accent-subtle);
}

.heading-copy h1 {
  margin: 0;
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: clamp(32px, 4vw, 48px);
  line-height: 1.08;
  letter-spacing: -.035em;
}

.heading-copy p {
  margin: 12px 0 0;
  color: var(--text-secondary);
  font-size: 15px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.sync-note {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text-muted);
  font-size: 12px;
}

.sync-note svg { color: #55c892; }

.clear-history-btn {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--surface-2);
  color: var(--text-secondary);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  transition: border-color .18s ease, color .18s ease, background .18s ease;
}

.clear-history-btn:hover {
  border-color: rgba(239, 95, 115, .45);
  background: rgba(239, 95, 115, .08);
  color: #f38698;
}

.history-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--border-subtle);
}

.history-search {
  display: flex;
  align-items: center;
  gap: 10px;
  width: min(340px, 100%);
  height: 44px;
  padding: 0 13px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  background: var(--surface-2);
  color: var(--text-muted);
  transition: border-color .18s ease, box-shadow .18s ease;
}

.history-search:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.history-search input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text-primary);
  font: inherit;
  font-size: 14px;
}

.history-search input::placeholder { color: var(--text-muted); }
.history-search input::-webkit-search-cancel-button { display: none; }
.history-search button {
  display: grid;
  place-items: center;
  padding: 4px;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}

.history-tabs {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  background: var(--surface-2);
}

.history-tabs button {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 34px;
  padding: 0 12px;
  border: 0;
  border-radius: calc(var(--radius-xl) - 4px);
  background: transparent;
  color: var(--text-secondary);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  transition: background .18s ease, color .18s ease;
}

.history-tabs button span {
  min-width: 20px;
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--surface-4);
  color: var(--text-muted);
  font-size: 11px;
}

.history-tabs button.active {
  background: var(--accent);
  color: #fff;
  box-shadow: 0 5px 18px rgba(223, 92, 151, .2);
}

.history-tabs button.active span { background: rgba(255, 255, 255, .18); color: #fff; }

.history-timeline { margin-top: 30px; }
.history-group + .history-group { margin-top: 34px; }

.group-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.group-heading h2 {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .035em;
  text-transform: uppercase;
}

.group-heading > span {
  color: var(--text-muted);
  font-size: 12px;
}

.group-heading > div { height: 1px; flex: 1; background: var(--border-subtle); }

.history-card {
  display: grid;
  grid-template-columns: 116px minmax(0, 1fr) auto;
  gap: 22px;
  min-height: 164px;
  padding: 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  background: linear-gradient(120deg, var(--surface-2), var(--surface-1));
  box-shadow: 0 8px 28px rgba(0, 0, 0, .06);
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}

.history-card + .history-card { margin-top: 10px; }
.history-card:hover {
  transform: translateY(-1px);
  border-color: var(--border-default);
  box-shadow: 0 12px 34px rgba(0, 0, 0, .1);
}

.poster-link {
  position: relative;
  display: block;
  width: 116px;
  height: 164px;
  overflow: hidden;
  border-radius: 12px;
  background: var(--surface-4);
}

.poster-link img { width: 100%; height: 100%; object-fit: cover; transition: transform .3s ease; }
.history-card:hover .poster-link img { transform: scale(1.035); }
.poster-placeholder { display: grid; width: 100%; height: 100%; place-items: center; color: var(--text-muted); }
.episode-badge {
  position: absolute;
  left: 8px;
  bottom: 8px;
  padding: 4px 8px;
  border: 1px solid rgba(255, 255, 255, .14);
  border-radius: 7px;
  background: rgba(12, 10, 18, .84);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  backdrop-filter: blur(8px);
}

.card-main { min-width: 0; padding: 4px 0; }
.card-topline { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.media-meta { display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: .045em; }
.media-meta > span + span::before { content: "·"; margin-right: 8px; }
.media-meta .score { display: inline-flex; align-items: center; gap: 3px; color: #e9b55f; }
.viewed-at { color: var(--text-muted); font-size: 12px; white-space: nowrap; }
.title-link { display: inline-block; max-width: 100%; margin-top: 9px; text-decoration: none; }
.title-link h3 {
  overflow: hidden;
  margin: 0;
  color: var(--text-primary);
  font-size: 19px;
  font-weight: 700;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color .18s ease;
}
.title-link:hover h3 { color: var(--accent); }
.title-link p { overflow: hidden; margin: 4px 0 0; color: var(--text-muted); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.progress-copy { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 19px; font-size: 12px; }
.progress-copy strong { color: var(--text-secondary); font-weight: 650; }
.progress-copy span { color: var(--text-muted); font-variant-numeric: tabular-nums; }
.episode-progress { height: 5px; overflow: hidden; margin-top: 7px; border-radius: 999px; background: var(--surface-4); }
.episode-progress span { display: block; height: 100%; border-radius: inherit; background: var(--accent); }
.series-progress-row { display: grid; grid-template-columns: auto minmax(60px, 150px) 32px; align-items: center; gap: 10px; margin-top: 13px; color: var(--text-muted); font-size: 11px; }
.series-progress { height: 3px; overflow: hidden; border-radius: 999px; background: var(--surface-4); }
.series-progress span { display: block; height: 100%; background: var(--text-muted); opacity: .65; }
.series-progress-row b { color: var(--text-secondary); font-size: 11px; font-weight: 600; text-align: right; }

.card-actions {
  display: flex;
  align-items: center;
  align-self: center;
  gap: 8px;
  padding-right: 6px;
}
.continue-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 42px;
  padding: 0 17px;
  border-radius: 12px;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  box-shadow: 0 8px 22px rgba(223, 92, 151, .2);
  transition: transform .18s ease, filter .18s ease;
}
.continue-btn:hover { transform: translateY(-1px); filter: brightness(1.08); }
.hide-btn {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border: 1px solid var(--border-default);
  border-radius: 12px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: color .18s ease, border-color .18s ease, background .18s ease;
}
.hide-btn:hover { border-color: rgba(239, 95, 115, .4); background: rgba(239, 95, 115, .08); color: #f38698; }
.hide-btn:disabled { opacity: .5; cursor: wait; }

.load-more, .state-action {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  margin: 24px auto 0;
  padding: 0 20px;
  border: 1px solid var(--border-default);
  border-radius: 12px;
  background: var(--surface-2);
  color: var(--text-primary);
  font: inherit;
  font-size: 13px;
  font-weight: 650;
  text-decoration: none;
  cursor: pointer;
}
.button-spinner { width: 14px; height: 14px; border: 2px solid var(--border-default); border-top-color: var(--accent); border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.history-state { display: flex; min-height: 430px; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.state-icon { display: grid; width: 72px; height: 72px; place-items: center; border: 1px solid var(--border-default); border-radius: 22px; background: var(--accent-subtle); color: var(--accent); transform: rotate(-3deg); }
.error-icon { color: #ef7386; background: rgba(239, 95, 115, .08); }
.history-state h2 { margin: 22px 0 0; color: var(--text-primary); font-size: 21px; }
.history-state p { max-width: 420px; margin: 8px 0 0; color: var(--text-secondary); font-size: 14px; line-height: 1.6; }

.history-skeleton { margin-top: 30px; }
.skeleton-row { display: flex; gap: 22px; height: 194px; padding: 14px; border: 1px solid var(--border-subtle); border-radius: 18px; background: var(--surface-2); }
.skeleton-row + .skeleton-row { margin-top: 10px; }
.skeleton-poster, .skeleton-copy i { background: linear-gradient(90deg, var(--surface-3), var(--surface-4), var(--surface-3)); background-size: 220% 100%; animation: shimmer 1.5s infinite linear; }
.skeleton-poster { width: 116px; flex: 0 0 116px; border-radius: 12px; }
.skeleton-copy { flex: 1; padding-top: 14px; }
.skeleton-copy i { display: block; height: 12px; border-radius: 6px; }
.skeleton-copy i:nth-child(1) { width: 22%; }
.skeleton-copy i:nth-child(2) { width: 48%; height: 20px; margin-top: 18px; }
.skeleton-copy i:nth-child(3) { width: 72%; margin-top: 34px; }
@keyframes shimmer { to { background-position: -220% 0; } }

.dialog-backdrop { position: fixed; inset: 0; z-index: calc(var(--z-modal, 1000) + 1); display: grid; padding: 20px; place-items: center; background: rgba(6, 5, 10, .74); backdrop-filter: blur(8px); }
.clear-dialog { width: min(430px, 100%); padding: 28px; border: 1px solid var(--border-default); border-radius: 22px; background: var(--surface-2); box-shadow: 0 28px 80px rgba(0, 0, 0, .35); }
.dialog-icon { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 14px; background: rgba(239, 95, 115, .1); color: #f38698; }
.clear-dialog h2 { margin: 18px 0 0; color: var(--text-primary); font-size: 21px; }
.clear-dialog p { margin: 9px 0 0; color: var(--text-secondary); font-size: 14px; line-height: 1.6; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 9px; margin-top: 24px; }
.dialog-actions button { min-height: 40px; padding: 0 16px; border-radius: 11px; font: inherit; font-size: 13px; font-weight: 650; cursor: pointer; }
.dialog-cancel { border: 1px solid var(--border-default); background: transparent; color: var(--text-primary); }
.dialog-confirm { border: 0; background: #d95770; color: #fff; }
.dialog-confirm:disabled { opacity: .65; cursor: wait; }
.dialog-fade-enter-active, .dialog-fade-leave-active { transition: opacity .18s ease; }
.dialog-fade-enter-from, .dialog-fade-leave-to { opacity: 0; }

@media (max-width: 900px) {
  .history-header { align-items: flex-start; }
  .sync-note { display: none; }
  .history-toolbar { align-items: stretch; flex-direction: column; }
  .history-search { width: 100%; }
  .history-tabs { align-self: flex-start; }
  .history-card { grid-template-columns: 98px minmax(0, 1fr); gap: 16px; }
  .poster-link { width: 98px; height: 142px; }
  .card-actions { grid-column: 2; align-self: auto; margin-top: -4px; padding: 0; }
  .continue-btn { flex: 1; }
}

@media (max-width: 640px) {
  .history-page { width: min(100% - 28px, 1120px); padding: 30px 0 60px; }
  .history-header { display: block; margin-bottom: 24px; }
  .heading-copy h1 { font-size: 32px; }
  .heading-copy p { max-width: 330px; font-size: 13px; line-height: 1.5; }
  .header-actions { margin-top: 18px; }
  .clear-history-btn { width: 100%; }
  .history-tabs { width: 100%; overflow-x: auto; }
  .history-tabs button { flex: 1 0 auto; justify-content: center; padding: 0 10px; }
  .history-timeline, .history-skeleton { margin-top: 24px; }
  .history-card { grid-template-columns: 84px minmax(0, 1fr); min-height: 0; padding: 11px; border-radius: 15px; }
  .poster-link { width: 84px; height: 120px; border-radius: 10px; }
  .episode-badge { left: 5px; bottom: 5px; padding: 3px 5px; font-size: 9px; }
  .card-main { padding-top: 1px; }
  .card-topline { display: block; }
  .viewed-at { display: block; margin-top: 5px; font-size: 10px; }
  .title-link { margin-top: 7px; }
  .title-link h3 { font-size: 15px; white-space: normal; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
  .title-link p { display: none; }
  .progress-copy { margin-top: 13px; font-size: 10px; }
  .series-progress-row { grid-template-columns: auto 1fr 28px; margin-top: 10px; font-size: 9px; }
  .card-actions { grid-column: 1 / -1; margin-top: 0; }
  .continue-btn { min-height: 40px; }
  .hide-btn { width: 40px; height: 40px; }
  .skeleton-row { height: 150px; padding: 11px; }
  .skeleton-poster { width: 84px; flex-basis: 84px; }
  .clear-dialog { padding: 22px; }
}

@media (prefers-reduced-motion: reduce) {
  .history-card, .poster-link img, .continue-btn, .dialog-fade-enter-active, .dialog-fade-leave-active { transition: none; }
  .skeleton-poster, .skeleton-copy i { animation: none; }
}
</style>
