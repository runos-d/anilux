<template>
  <div class="afb">
    <div class="afb-top">
      <div class="afb-search">
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          v-model="search"
          @input="onSearch"
          type="text"
          :placeholder="searchPlaceholder"
          class="afb-search-input"
        />
        <button
          v-if="search"
          @click="clearSearch"
          class="afb-search-clear"
          type="button"
        >
          <svg
            width="13"
            height="13"
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

      <select v-model="ordering" class="afb-select">
        <option v-for="s in sortOptions" :key="s.value" :value="s.value">
          {{ s.label }}
        </option>
      </select>

      <select
        v-if="showPageSize"
        v-model="pageSize"
        class="afb-select afb-select-sm"
      >
        <option v-if="defaultPageSize === 24" :value="24">24</option>
        <option :value="20">20</option>
        <option :value="50">50</option>
        <option :value="100">100</option>
      </select>

      <div class="afb-actions">
        <button
          v-if="showShuffle"
          @click="$emit('shuffle')"
          class="afb-btn"
          title="Перемешать"
          :aria-pressed="isShuffled"
          type="button"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="16 3 21 3 21 8" />
            <line x1="4" y1="20" x2="21" y2="3" />
            <polyline points="21 16 21 21 16 21" />
            <line x1="15" y1="15" x2="21" y2="21" />
            <line x1="4" y1="4" x2="9" y2="9" />
          </svg>
        </button>

        <button
          @click="$emit('unshuffle')"
          class="afb-btn"
          title="Обновить"
          type="button"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>

        <button
          v-if="showAdvanced"
          @click="panelOpen = !panelOpen"
          :class="[
            'afb-btn',
            { 'afb-btn-active': panelOpen || activeAdvancedCount > 0 },
          ]"
          :title="panelOpen ? 'Скрыть фильтры' : 'Фильтры'"
          type="button"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
          <span v-if="activeAdvancedCount > 0" class="afb-badge">{{
            activeAdvancedCount
          }}</span>
        </button>
      </div>
    </div>

    <div class="afb-genres-row">
      <span class="afb-genres-label">Жанры</span>
      <div class="afb-genres-scroll-wrap">
        <button
          v-if="!genresAtStart && !genresLoading"
          class="afb-genre-arrow afb-genre-arrow-left"
          @click="scrollGenres(-1)"
          type="button"
          aria-label="Назад по жанрам"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>

        <div
          class="afb-genres-scroll"
          ref="genresScrollRef"
          @scroll="updateGenresArrows"
          @wheel="onGenresWheel"
        >
          <button
            :class="['afb-genre-chip', { active: selectedGenres.length === 0 }]"
            @click="clearGenres"
            type="button"
          >
            Все
          </button>

          <template v-if="genresLoading">
            <div v-for="i in 14" :key="i" class="afb-genre-skel"></div>
          </template>
          <template v-else>
            <button
              v-for="g in filteredGenreList"
              :key="g"
              :class="['afb-genre-chip', { active: selectedGenres.includes(g) }]"
              @click="toggleGenre(g)"
              type="button"
            >
              {{ g }}
            </button>
          </template>
        </div>

        <button
          v-if="!genresAtEnd && !genresLoading"
          class="afb-genre-arrow afb-genre-arrow-right"
          @click="scrollGenres(1)"
          type="button"
          aria-label="Вперёд по жанрам"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <path d="M9 18l6-6-6-6" />
          </svg>
        </button>
      </div>

      <div class="afb-genre-search">
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          v-model="genreSearch"
          class="afb-genre-search-input"
          placeholder="Жанр…"
          type="text"
        />
      </div>
    </div>

    <transition name="afb-panel">
      <div v-if="panelOpen && showAdvanced" class="afb-panel">
        <div class="afb-group">
          <div class="afb-group-label">Тип</div>
          <div class="afb-chips">
            <button
              v-for="t in TYPE_OPTIONS"
              :key="t.value"
              :class="['afb-chip', { active: selectedTypes.includes(t.value) }]"
              @click="toggleType(t.value)"
              type="button"
            >
              {{ t.label }}
            </button>
          </div>
        </div>

        <div v-if="showFranchiseFilter" class="afb-group">
          <div class="afb-group-label">Франшизы</div>
          <div class="afb-chips">
            <button
              :class="['afb-chip', { active: showOnlyFranchises }]"
              @click="toggleOnlyFranchises"
              type="button"
            >
              <span class="afb-dot" :style="{ background: showOnlyFranchises ? '#22c55e' : 'var(--text-tertiary)' }"></span>
              Только франшизы
            </button>
          </div>
        </div>

        <div v-if="showStatus" class="afb-group">
          <div class="afb-group-label">Статус</div>
          <div class="afb-chips">
            <button
              v-for="s in STATUS_OPTIONS"
              :key="s.value"
              :class="[
                'afb-chip',
                `afb-chip-status-${s.color}`,
                { active: selectedStatuses.includes(s.value) },
              ]"
              @click="toggleStatus(s.value)"
              type="button"
            >
              <span class="afb-dot"></span>{{ s.label }}
            </button>
          </div>
        </div>

        <div class="afb-group">
          <div class="afb-group-label">Год выпуска</div>
          <div class="afb-range-row">
            <input
              v-model.number="yearFrom"
              type="number"
              placeholder="От"
              min="1960"
              :max="currentYear + 1"
              class="afb-range-input"
            />
            <span class="afb-dash">-</span>
            <input
              v-model.number="yearTo"
              type="number"
              placeholder="До"
              min="1960"
              :max="currentYear + 1"
              class="afb-range-input"
            />
          </div>
          <div class="afb-presets">
            <button
              v-for="y in YEAR_PRESETS"
              :key="y.label"
              :class="[
                'afb-preset',
                { active: yearFrom === y.from && yearTo === y.to },
              ]"
              @click="toggleYearPreset(y)"
              type="button"
            >
              {{ y.label }}
            </button>
          </div>
        </div>

        <div class="afb-group">
          <div class="afb-group-label">Рейтинг</div>
          <div class="afb-range-row">
            <input
              v-model.number="scoreFrom"
              type="number"
              placeholder="От"
              min="0"
              max="10"
              step="0.1"
              class="afb-range-input"
            />
            <span class="afb-dash">-</span>
            <input
              v-model.number="scoreTo"
              type="number"
              placeholder="До"
              min="0"
              max="10"
              step="0.1"
              class="afb-range-input"
            />
          </div>
          <div class="afb-presets">
            <button
              v-for="r in [9, 8, 7, 6]"
              :key="r"
              :class="['afb-preset', { active: scoreFrom === r && !scoreTo }]"
              @click="toggleRatingPreset(r)"
              type="button"
            >
              {{ r }}+
            </button>
          </div>
        </div>

        <div class="afb-group">
          <div class="afb-group-label">Эпизоды</div>
          <div class="afb-range-row">
            <input
              v-model.number="episodesFrom"
              type="number"
              placeholder="От"
              min="0"
              class="afb-range-input"
            />
            <span class="afb-dash">-</span>
            <input
              v-model.number="episodesTo"
              type="number"
              placeholder="До"
              min="0"
              class="afb-range-input"
            />
          </div>
          <div class="afb-presets">
            <button
              v-for="ep in EPISODE_PRESETS"
              :key="ep.label"
              :class="[
                'afb-preset',
                { active: episodesFrom === ep.from && episodesTo === ep.to },
              ]"
              @click="toggleEpPreset(ep)"
              type="button"
            >
              {{ ep.label }}
            </button>
          </div>
        </div>

        <div v-if="currentUser && showLibraryFilters" class="afb-group">
          <div class="afb-group-label">Не показывать аниме со статусом:</div>
          <div class="afb-chips">
            <button
              v-for="ls in LIBRARY_STATUS_OPTIONS"
              :key="ls.value"
              :class="[
                'afb-chip',
                `afb-chip-status-${ls.color}`,
                { active: excludedLibraryStatuses.includes(ls.value) },
              ]"
              @click="toggleExcludedLibraryStatus(ls.value)"
              type="button"
            >
              <span class="afb-dot"></span>{{ ls.label }}
            </button>
          </div>
        </div>

        <div class="afb-panel-footer">
          <div class="afb-logic-wrap">
            <span class="afb-logic-label">Жанры:</span>
            <div class="afb-logic-toggle">
              <button
                :class="['afb-logic-btn', { active: genreLogic === 'OR' }]"
                @click="setGenreLogic('OR')"
                type="button"
              >
                ИЛИ
              </button>
              <button
                :class="['afb-logic-btn', { active: genreLogic === 'AND' }]"
                @click="setGenreLogic('AND')"
                type="button"
              >
                И
              </button>
            </div>
          </div>
          <div class="afb-panel-footer-right">
            <span class="afb-results-count" v-if="resultsCount != null">
              <strong>{{ resultsCount.toLocaleString("ru-RU") }}</strong>
              результатов
            </span>
            <button @click="resetAll" class="afb-reset-btn" type="button">
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
              >
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
              </svg>
              Сбросить всё
            </button>
          </div>
        </div>
      </div>
    </transition>

    <div v-if="activeChips.length > 0" class="afb-active-chips">
      <span class="afb-active-label">Фильтры:</span>
      <div class="afb-active-list">
        <span
          v-for="chip in activeChips"
          :key="chip.key"
          class="afb-active-chip"
        >
          {{ chip.label }}
          <button @click="removeChip(chip.key)" type="button" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
        </span>
      </div>
      <button @click="resetAll" class="afb-clear-all" type="button">
        Сбросить всё
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { ref, computed, watch, onMounted, nextTick } from "vue";
import { cachedCatalogFacets, loadCatalogFacets } from "@/lib/catalogFacets";
import { reportTechnicalError } from "@/analytics";

interface Props {
  showStatus?: boolean;
  showAdvanced?: boolean;
  showShuffle?: boolean;
  isShuffled?: boolean;
  resultsCount?: number;
  defaultOrdering?: string;
  sortOptions?: { value: string; label: string }[];
  showPageSize?: boolean;
  searchPlaceholder?: string;
  initialFilters?: FilterState;
  defaultPageSize?: number;
  emitOnMount?: boolean;
  syncFilters?: boolean;
  showFranchiseFilter?: boolean;
  showLibraryFilters?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showStatus: true,
  showAdvanced: true,
  showShuffle: false,
  isShuffled: false,
  defaultOrdering: "-score",
  showPageSize: false,
  defaultPageSize: 50,
  emitOnMount: true,
  syncFilters: false,
  showFranchiseFilter: true,
  showLibraryFilters: true,
  searchPlaceholder: "Поиск аниме...",
  sortOptions: () => [
    { value: "-score", label: "Рейтинг: 10–0" },
    { value: "score", label: "Рейтинг: 0–10" },
    { value: "-year", label: "Год: новее" },
    { value: "year", label: "Год: старее" },
  { value: "title_ru", label: "Название: А–Я" },
  { value: "-title_ru", label: "Название: Я–А" },
    { value: "-episodes", label: "Больше серий" },
    { value: "episodes", label: "Меньше серий" },
  ],
});

const emit = defineEmits<{
  change: [filters: FilterState, userInitiated?: boolean];
  shuffle: [];
  unshuffle: [];
  refresh: [];
}>();

import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();
const currentUser = computed(() => authStore.user);

export interface FilterState {
  search?: string;
  genres?: string[];
  genre_logic?: "OR" | "AND";
  status?: string[];
  type?: string[];
  year_from?: number;
  year_to?: number;
  score_from?: number;
  score_to?: number;
  episodes_from?: number;
  episodes_to?: number;
  ordering?: string;
  page_size?: number;
  excluded_library_statuses?: string[];
  kind?: string[];
  show_only_franchises?: boolean;
}

const currentYear = new Date().getFullYear();

const TYPE_LABELS: Record<string, string> = {
  tv: "TV",
  movie: "Фильм",
  ova: "OVA",
  ona: "ONA",
  special: "Special",
  music: "Music",
  franchise: "Франшиза",
};

const cachedFacets = cachedCatalogFacets();
const toTypeOptions = (types: string[]) => types.map((value) => ({
  value,
  label: TYPE_LABELS[value] || value,
}));
const TYPE_OPTIONS = ref<{ value: string; label: string }[]>(
  toTypeOptions(cachedFacets?.types.length ? cachedFacets.types : Object.keys(TYPE_LABELS)),
);
const typesLoading = ref(false);

const STATUS_OPTIONS = [
  { value: "ongoing", label: "Онгоинг", color: "green" },
  { value: "finished", label: "Завершён", color: "grey" },
  { value: "announced", label: "Анонс", color: "yellow" },
  { value: "released", label: "Вышел", color: "green" },
  { value: "canceled", label: "Отменён", color: "red" },
];

const LIBRARY_STATUS_OPTIONS = [
  { value: "completed", label: "Просмотрено", color: "blue" },
  { value: "started", label: "Смотрю", color: "green" },
  { value: "dropped", label: "Брошено", color: "red" },
  { value: "on_hold", label: "На паузе", color: "yellow" },
  { value: "planned", label: "В планах", color: "grey" },
  { value: "favorite", label: "В избранном", color: "pink" },
];

const YEAR_PRESETS = [
  { label: "2020-е", from: 2020, to: currentYear },
  { label: "2010-е", from: 2010, to: 2019 },
  { label: "2000-е", from: 2000, to: 2009 },
  { label: "90-е", from: 1990, to: 1999 },
];

const EPISODE_PRESETS = [
  { label: "1–4", from: 1, to: 4 },
  { label: "5–13", from: 5, to: 13 },
  { label: "14–26", from: 14, to: 26 },
  { label: "27–52", from: 27, to: 52 },
  { label: "52+", from: 52, to: undefined as number | undefined },
];

const initial = props.initialFilters || {};
const search = ref(initial.search || "");
const ordering = ref(initial.ordering || props.defaultOrdering);
const pageSize = ref(initial.page_size || props.defaultPageSize);
const panelOpen = ref(false);
const genreSearch = ref("");
const genreLogic = ref<"OR" | "AND">(initial.genre_logic || "OR");

const selectedGenres = ref<string[]>([...(initial.genres || [])]);
const selectedTypes = ref<string[]>([...(initial.type || [])]);
const selectedStatuses = ref<string[]>([...(initial.status || [])]);
const showOnlyFranchises = ref(initial.show_only_franchises || false);
const excludedLibraryStatuses = ref<string[]>([...(initial.excluded_library_statuses || [])]);

const yearFrom = ref<number | undefined>(initial.year_from);
const yearTo = ref<number | undefined>(initial.year_to);
const scoreFrom = ref<number | undefined>(initial.score_from);
const scoreTo = ref<number | undefined>(initial.score_to);
const episodesFrom = ref<number | undefined>(initial.episodes_from);
const episodesTo = ref<number | undefined>(initial.episodes_to);

let syncingFilters = false;
watch(() => props.initialFilters, async value => {
  if (!props.syncFilters || !value) return;
  syncingFilters = true;
  search.value = value.search || "";
  ordering.value = value.ordering || props.defaultOrdering;
  pageSize.value = value.page_size || props.defaultPageSize;
  selectedGenres.value = [...(value.genres || [])];
  selectedTypes.value = [...(value.type || [])];
  selectedStatuses.value = [...(value.status || [])];
  excludedLibraryStatuses.value = [...(value.excluded_library_statuses || [])];
  genreLogic.value = value.genre_logic || "OR";
  showOnlyFranchises.value = value.show_only_franchises || false;
  yearFrom.value = value.year_from; yearTo.value = value.year_to;
  scoreFrom.value = value.score_from; scoreTo.value = value.score_to;
  episodesFrom.value = value.episodes_from; episodesTo.value = value.episodes_to;
  await nextTick();
  syncingFilters = false;
}, { deep: true });

const allGenres = ref<string[]>(cachedFacets?.genres || []);
const genresLoading = ref(!allGenres.value.length);

const genresScrollRef = ref<HTMLElement | null>(null);
const genresAtStart = ref(true);
const genresAtEnd = ref(false);
const updateGenresArrows = () => {
  const el = genresScrollRef.value;
  if (!el) return;
  genresAtStart.value = el.scrollLeft <= 4;
  genresAtEnd.value =
    el.scrollLeft + el.clientWidth >= el.scrollWidth - 4;
};

const scrollGenres = (dir: number) => {
  const el = genresScrollRef.value;
  if (!el) return;
  const step = Math.max(220, el.clientWidth * 0.7);
  el.scrollBy({ left: dir * step, behavior: "smooth" });
};

const onGenresWheel = (e: WheelEvent) => {
  const el = genresScrollRef.value;
  if (!el) return;
  if (Math.abs(e.deltaY) < Math.abs(e.deltaX)) return;
  e.preventDefault();
  el.scrollBy({ left: e.deltaY, behavior: "auto" });
};

const syncGenresArrows = () => {
  updateGenresArrows();
};

watch(allGenres, () => {
  requestAnimationFrame(syncGenresArrows);
});

const filteredGenreList = computed(() => {
  const q = genreSearch.value.trim().toLowerCase();
  const pool = q
    ? allGenres.value.filter((g) => g.toLowerCase().includes(q))
    : allGenres.value;

  if (selectedGenres.value.length === 0) return pool;

  const selected = new Set(selectedGenres.value);
  const selectedItems: string[] = [];
  const otherItems: string[] = [];

  for (const g of pool) {
    if (selected.has(g)) selectedItems.push(g);
    else otherItems.push(g);
  }

  return [...selectedItems, ...otherItems];
});

onMounted(async () => {
  genresLoading.value = !allGenres.value.length;
  typesLoading.value = !TYPE_OPTIONS.value.length;
  try {
    const facets = await loadCatalogFacets();
    allGenres.value = facets.genres;
    TYPE_OPTIONS.value = toTypeOptions(facets.types.length ? facets.types : Object.keys(TYPE_LABELS));
  } catch {
    reportTechnicalError("catalog.facets_failed", "/route/anime-catalog");
  } finally {
    genresLoading.value = false;
    typesLoading.value = false;
  }
});

function normalizeSearchQuery(query: string): string {
  return query
    .toLowerCase()
    .replace(/[-_:/\\|,.!?@#$%^&*(){}\[\]<>~`'"\\s]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const onSearch = () => {
  emitChange();
};

const clearSearch = () => {
  search.value = "";
  emitChange();
};

const toggleGenre = (g: string) => {
  toggle(selectedGenres, g);
  emitChange();
};
const toggleType = (t: string) => {
  toggle(selectedTypes, t);
  emitChange();
};

const toggleOnlyFranchises = () => {
  showOnlyFranchises.value = !showOnlyFranchises.value;
  emitChange();
};

const toggleStatus = (s: string) => {
  toggle(selectedStatuses, s);
  emitChange();
};
const toggleExcludedLibraryStatus = (s: string) => {
  toggle(excludedLibraryStatuses, s);
  emitChange();
};
const clearGenres = () => {
  selectedGenres.value = [];
  emitChange();
};

function toggle(arr: { value: string[] }, val: string) {
  const idx = arr.value.indexOf(val);
  if (idx === -1) arr.value = [...arr.value, val];
  else arr.value = arr.value.filter((_, i) => i !== idx);
}

const setGenreLogic = (l: "OR" | "AND") => {
  genreLogic.value = l;
  emitChange();
};

const toggleYearPreset = (y: { from: number; to: number }) => {
  if (yearFrom.value === y.from && yearTo.value === y.to) {
    yearFrom.value = undefined;
    yearTo.value = undefined;
  } else {
    yearFrom.value = y.from;
    yearTo.value = y.to;
  }
  emitChange();
};

const toggleRatingPreset = (r: number) => {
  if (scoreFrom.value === r && !scoreTo.value) {
    scoreFrom.value = undefined;
  } else {
    scoreFrom.value = r;
    scoreTo.value = undefined;
  }
  emitChange();
};

const toggleEpPreset = (ep: { from: number; to: number | undefined }) => {
  if (episodesFrom.value === ep.from && episodesTo.value === ep.to) {
    episodesFrom.value = undefined;
    episodesTo.value = undefined;
  } else {
    episodesFrom.value = ep.from;
    episodesTo.value = ep.to;
  }
  emitChange();
};

const activeAdvancedCount = computed(() => {
  let c = 0;
  if (selectedTypes.value.length) c++;
  if (props.showFranchiseFilter && showOnlyFranchises.value) c++;
  if (selectedStatuses.value.length) c++;
  if (yearFrom.value || yearTo.value) c++;
  if (scoreFrom.value || scoreTo.value) c++;
  if (episodesFrom.value || episodesTo.value) c++;
  return c;
});

interface Chip {
  key: string;
  label: string;
}
const activeChips = computed((): Chip[] => {
  const chips: Chip[] = [];
  if (search.value)
    chips.push({ key: "search", label: `Поиск: "${search.value}"` });
  if (selectedGenres.value.length)
    chips.push({
      key: "genres",
      label: `Жанры: ${selectedGenres.value.length}`,
    });
  if (selectedTypes.value.length)
    chips.push({
      key: "type",
      label: `Тип: ${selectedTypes.value.join(", ")}`,
    });
  if (selectedStatuses.value.length)
    chips.push({
      key: "status",
      label: `Статус: ${selectedStatuses.value.length}`,
    });
  if (props.showFranchiseFilter && showOnlyFranchises.value)
    chips.push({
      key: "franchise",
      label: "Только франшизы",
    });
  if (props.showLibraryFilters && excludedLibraryStatuses.value.length)
    chips.push({
      key: "library",
      label: `Исключить: ${excludedLibraryStatuses.value.length}`,
    });
  if (yearFrom.value || yearTo.value)
    chips.push({
      key: "year",
      label: `Год: ${yearFrom.value || "?"}–${yearTo.value || "?"}`,
    });
  if (scoreFrom.value || scoreTo.value)
    chips.push({
      key: "score",
      label: `Рейтинг: ${scoreFrom.value || 0}–${scoreTo.value || 10}`,
    });
  return chips;
});

const removeChip = (key: string) => {
  switch (key) {
    case "search":
      search.value = "";
      break;
    case "genres":
      selectedGenres.value = [];
      break;
    case "type":
      selectedTypes.value = [];
      break;
    case "status":
      selectedStatuses.value = [];
      break;
    case "franchise":
      showOnlyFranchises.value = false;
      break;
    case "library":
      excludedLibraryStatuses.value = [];
      break;
    case "year":
      yearFrom.value = undefined;
      yearTo.value = undefined;
      break;
    case "score":
      scoreFrom.value = undefined;
      scoreTo.value = undefined;
      break;
  }
  emitChange();
};

const resetAll = () => {
  search.value = "";
  ordering.value = props.defaultOrdering;
  selectedGenres.value = [];
  selectedTypes.value = [];
  selectedStatuses.value = [];
  showOnlyFranchises.value = false;
  excludedLibraryStatuses.value = [];
  yearFrom.value = undefined;
  yearTo.value = undefined;
  scoreFrom.value = undefined;
  scoreTo.value = undefined;
  episodesFrom.value = undefined;
  episodesTo.value = undefined;
  genreLogic.value = "OR";
  panelOpen.value = false;
  emitChange();
};

const emitChange = (userInitiated = true) => {
  if (syncingFilters) return;
  const filters: FilterState = {
    search: search.value ? normalizeSearchQuery(search.value) : undefined,
    genres: selectedGenres.value.length ? selectedGenres.value : undefined,
    genre_logic: genreLogic.value,
    status: selectedStatuses.value.length ? selectedStatuses.value : undefined,
    type: selectedTypes.value.length ? selectedTypes.value : undefined,
    kind: undefined,
    show_only_franchises: props.showFranchiseFilter ? showOnlyFranchises.value : false,
    year_from: yearFrom.value,
    year_to: yearTo.value,
    score_from: scoreFrom.value,
    score_to: scoreTo.value,
    episodes_from: episodesFrom.value,
    episodes_to: episodesTo.value,
    ordering: ordering.value,
    page_size: pageSize.value,
    excluded_library_statuses: props.showLibraryFilters && excludedLibraryStatuses.value.length
      ? excludedLibraryStatuses.value
      : undefined,
  };
  emit("change", filters, userInitiated);
};

watch(
  [
    ordering,
    pageSize,
    yearFrom,
    yearTo,
    scoreFrom,
    scoreTo,
    episodesFrom,
    episodesTo,
  ],
  () => emitChange(),
);

onMounted(() => { if (props.emitOnMount) emitChange(false); });
</script>

<style scoped>
.afb {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    padding: var(--space-4) var(--space-5);
    background: var(--color-background-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-xl);
    margin-bottom: var(--space-5);
  }

.afb-top {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.afb-search {
  position: relative;
  flex: 1;
  min-width: 200px;
}
.afb-search svg:first-child {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  pointer-events: none;
}
.afb-search-input {
  width: 100%;
  height: 38px;
  padding: 0 34px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 0.15s;
}
.afb-search-input:focus {
  border-color: var(--accent);
}
.afb-search-input::placeholder {
  color: var(--text-tertiary);
}
.afb-search-clear {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 3px;
  display: flex;
  transition: color 0.15s;
}
.afb-search-clear:hover {
  color: var(--text-primary);
}

.afb-select {
  height: 38px;
  padding: 0 var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  cursor: pointer;
  outline: none;
  min-width: 165px;
  transition: border-color 0.15s;
}
.afb-select:focus {
  border-color: var(--accent);
}
.afb-select-sm {
  min-width: 80px;
}

.afb-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}
.afb-btn {
  position: relative;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.afb-btn:hover {
  background: var(--surface-5);
  color: var(--text-primary);
  border-color: var(--border-default);
}
.afb-btn-active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
}
.afb-btn-active:hover {
  background: var(--accent);
  color: white;
}

.afb-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  min-width: 16px;
  height: 16px;
  padding: 0 3px;
  background: var(--accent);
  color: white;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.afb-genres-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.afb-genres-label {
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  white-space: nowrap;
  flex-shrink: 0;
}
.afb-genres-scroll-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}
.afb-genres-scroll {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  flex: 1;
  padding-bottom: 2px;
  align-items: center;
  scroll-behavior: smooth;
}
.afb-genres-scroll::-webkit-scrollbar {
  display: none;
}

.afb-genre-arrow {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  min-width: 26px;
  min-height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 50%;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  padding: 0;
}
.afb-genre-arrow:hover {
  background: var(--surface-5);
  color: var(--text-primary);
  border-color: var(--border-default);
}
.afb-genre-arrow-left {
  order: -1;
}
.afb-genre-arrow svg {
  flex-shrink: 0;
}

.afb-genre-chip {
  flex-shrink: 0;
  height: 28px;
  padding: 0 11px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.afb-genre-chip:hover {
  background: var(--surface-5);
  color: var(--text-primary);
}
.afb-genre-chip.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.afb-genre-skel {
  flex-shrink: 0;
  height: 28px;
  width: 64px;
  border-radius: var(--radius-full);
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-4) 50%,
    var(--surface-3) 75%
  );
  background-size: 400% 100%;
  animation: afb-sk 1.4s ease-in-out infinite;
}
@keyframes afb-sk {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

.afb-genre-search {
  display: flex;
  align-items: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  padding: 0 10px;
  gap: 5px;
  flex-shrink: 0;
  height: 36px;
}
.afb-genre-search svg {
  color: var(--text-tertiary);
  flex-shrink: 0;
}
.afb-genre-search-input {
  width: 80px;
  height: 100%;
  min-height: 0;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: var(--text-xs);
  line-height: 22px;
  padding: 0;
  transition: width 0.2s;
}

@media (pointer: coarse) {
  .afb-genre-arrow { width: 40px; height: 40px; min-width: 40px; min-height: 40px; }
  .afb-genre-search { height: 40px; }
  .afb-genre-chip { min-height: 40px; }
  .afb-search-input, .afb-genre-search-input { font-size: 16px; }
}
.afb-genre-search-input:focus {
  width: 110px;
}
.afb-genre-search-input::placeholder {
  color: var(--text-tertiary);
}

.afb-panel {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.afb-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.afb-group-full {
  grid-column: 1 / -1;
}

.afb-group-label {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
}

.afb-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.afb-chips-scroll {
  max-height: 100px;
  overflow-y: auto;
  scrollbar-width: thin;
}

.afb-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.14s;
}
.afb-chip:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}
.afb-chip.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.afb-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.afb-chip-status-green .afb-dot {
  background: #22c55e;
}
.afb-chip-status-grey .afb-dot {
  background: #64748b;
}
.afb-chip-status-yellow .afb-dot {
  background: #f59e0b;
}
.afb-chip-status-red .afb-dot {
  background: #ef4444;
}
.afb-chip-status-pink .afb-dot {
  background: #ec4899;
}
.afb-chip-status-green.active {
  background: #16a34a;
  border-color: #16a34a;
}
.afb-chip-status-grey.active {
  background: #475569;
  border-color: #475569;
}
.afb-chip-status-yellow.active {
  background: #d97706;
  border-color: #d97706;
}
.afb-chip-status-red.active {
  background: #dc2626;
  border-color: #dc2626;
}
.afb-chip-status-pink.active {
  background: #db2777;
  border-color: #db2777;
}

.afb-range-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.afb-range-input {
  flex: 1;
  min-width: 0;
  padding: 5px 7px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-4);
  color: var(--text-primary);
  font-size: var(--text-xs);
  font-weight: 600;
  text-align: center;
  outline: none;
  transition: border-color 0.15s;
}
.afb-range-input:focus {
  border-color: var(--accent);
}
.afb-range-input::placeholder {
  color: var(--text-tertiary);
  font-weight: 400;
}
.afb-dash {
  color: var(--text-tertiary);
  flex-shrink: 0;
  font-size: var(--text-xs);
}

.afb-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.afb-preset {
  padding: 3px 7px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.68rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.14s;
}
.afb-preset:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.afb-preset.active {
  background: rgba(var(--accent-rgb, 124 92 252) / 0.15);
  border-color: var(--accent);
  color: var(--accent);
}

.afb-search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 9px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-4);
}
.afb-search-box svg {
  color: var(--text-tertiary);
  flex-shrink: 0;
}
.afb-inline-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: var(--text-xs);
  outline: none;
}
.afb-inline-input::placeholder {
  color: var(--text-tertiary);
}

.afb-panel-footer {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-subtle);
}
.afb-panel-footer-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-left: auto;
}

.afb-logic-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}
.afb-logic-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: 600;
  white-space: nowrap;
}
.afb-logic-toggle {
  display: flex;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  overflow: hidden;
}
.afb-logic-btn {
  padding: 4px 12px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 700;
  cursor: pointer;
  transition: all 0.13s;
}
.afb-logic-btn:hover {
  background: var(--surface-5);
  color: var(--text-primary);
}
.afb-logic-btn.active {
  background: var(--accent);
  color: white;
}

.afb-results-count {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
.afb-results-count strong {
  color: var(--accent);
  font-weight: 700;
}

.afb-reset-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.afb-reset-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.afb-active-chips {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}
.afb-active-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-tertiary);
  white-space: nowrap;
}
.afb-active-list {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
}
.afb-active-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  background: var(--accent);
  color: white;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
}
.afb-active-chip button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 15px;
  height: 15px;
  min-height: 0;
  background: rgba(255, 255, 255, 0.25);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
  line-height: 1;
}
.afb-active-chip button:hover {
  background: rgba(255, 255, 255, 0.45);
}
.afb-clear-all {
  padding: 3px 10px;
  background: none;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.afb-clear-all:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.afb-panel-enter-active,
.afb-panel-leave-active {
  transition:
    opacity 0.2s,
    transform 0.2s;
}
.afb-panel-enter-from,
.afb-panel-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 767px) {
  .afb {
    padding: var(--space-3);
  }
  .afb-top {
    flex-wrap: wrap;
  }
  .afb-search {
    min-width: 100%;
  }
  .afb-select {
    flex: 1;
    min-width: 120px;
  }
  .afb-panel {
    grid-template-columns: 1fr 1fr;
  }
  .afb-genre-search-input {
    width: 70px;
  }
}
</style>
