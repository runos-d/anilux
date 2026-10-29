<template>
  <div class="anime-view">
    <div class="av-container">
      <div class="av-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['av-tab', { active: currentSection === tab.key }]"
          @click="
            tab.key === 'currently_watching'
              ? switchCurrentlyWatching()
              : handleSwitchSection(tab.key)
          "
          type="button"
        >
          <span class="av-tab-icon">
            <SakuraIcon
              v-if="isIconName(tab.icon)"
              :name="tab.icon"
              :size="16"
            />
            <span v-else>{{ tab.icon }}</span>
          </span>
          <span>{{ tab.label }}</span>
          <!-- <span
            v-if="tab.key === 'ongoings' && ongoingCount"
            class="av-tab-badge"
            >{{ ongoingCount }}</span
          > -->
        </button>
      </div>

      <KeepAlive :max="6">
        <CatalogView v-if="currentSection === 'catalog'" key="catalog"
            :anime-list="catalogAnime"
            :loading="catalogLoading"
            :error="catalogError"
            :page="catalogPage"
            :total-pages="catalogTotalPages"
            :total-count="catalogTotalCount"
            :show-shuffle="true"
            :is-shuffled="isShuffled.catalog"
            :filters="currentCatalogFilters"
            :group-franchises="catalogGroupFranchises"
            @page-change="handlePageChange"
            @refresh="fetchCatalog(1)"
            @filter-change="handleCatalogFilterChange"
            @shuffle="shuffleCatalog"
            @unshuffle="unshuffleCatalog"
            @anime-click="goToDetail"
            @watch-anime="startWatching"
          />

        <OngoingsView v-else-if="currentSection === 'ongoings'" key="ongoings"
            :anime="ongoings"
            :loading="ongoingsLoading"
            :error="ongoingsError"
            :page="ongoingsPage"
            :total-pages="ongoingsTotalPages"
            :total-count="ongoingsTotalCount"
            :filters="ongoingsFilters as FilterState"
            :viewers-map="viewersMap"
            @refresh="fetchOngoings(ongoingsPage)"
            @page-change="fetchOngoings($event)"
            @filter-change="fetchOngoings(1, $event)"
          />

        <RecommendationsView v-else-if="currentSection === 'recommendations'"
          key="recommendations" />

        <AnnouncementsView v-else-if="currentSection === 'announcements'" key="announcements"
            :anime="announcements"
            :loading="announcementsLoading"
            :error="announcementsError"
            @refresh="fetchAnnouncements"
          />

        <CalendarView v-else-if="currentSection === 'calendar'" key="calendar"
            :data="calendarData"
            :loading="calendarLoading"
            :error="calendarError"
            @refresh="fetchCalendar"
            @change-month="setCalendarMonth"
          />

        <CurrentlyWatchingView v-else-if="(currentSection as string) === 'currently_watching'"
          key="currently_watching"
            :anime="currentlyWatching"
            :loading="currentlyWatchingLoading"
            :error="currentlyWatchingError"
            @refresh="fetchCurrentlyWatching"
          />
      </KeepAlive>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, ref, computed, onMounted, onActivated, onDeactivated, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
const CatalogView = defineAsyncComponent(() => import("./CatalogView.vue"));
const OngoingsView = defineAsyncComponent(() => import("./OngoingsView.vue"));
const RecommendationsView = defineAsyncComponent(() => import("./RecommendationsView.vue"));
const AnnouncementsView = defineAsyncComponent(() => import("./AnnouncementsView.vue"));
const CurrentlyWatchingView = defineAsyncComponent(() => import("./CurrentlyWatchingView.vue"));
const CalendarView = defineAsyncComponent(() => import("./CalendarView.vue"));
import {
  useAnimeSections,
  type AnimeSection as SectionType,
  type CatalogFilters,
} from "@/composables/useAnimeSections";
import type { FilterState } from "@/components/Filters/AnimeFilterBar.vue";
import apiClient from "@/api/client";
import type { Anime } from "@/types";
import { event as analyticsEvent } from "@/analytics";

const router = useRouter();
const route = useRoute();


const props = defineProps<{
  presetYear?: number
  presetGenre?: string
  presetKind?: string
  presetStatus?: string
}>()

const catalogPreset = computed(() => {
  const preset: Record<string, string | number | string[]> = {}
  if (props.presetYear) { preset.year_from = props.presetYear; preset.year_to = props.presetYear; }
  if (props.presetGenre) preset.genres = [props.presetGenre]
  if (props.presetKind) preset.kind = [props.presetKind]
  if (props.presetStatus) preset.status = props.presetStatus
  return Object.keys(preset).length > 0 ? preset : undefined
})

const {
  currentSection,
  catalogAnime,
  ongoings,
  announcements,
  catalogLoading,
  ongoingsLoading,
  announcementsLoading,
  catalogError,
  ongoingsError,
  announcementsError,
  calendarData,
  calendarLoading,
  calendarError,
  setCalendarMonth,
  catalogPage,
  catalogTotalPages,
  catalogTotalCount,
  ongoingsPage,
  ongoingsTotalPages,
  ongoingsTotalCount,
  ongoingsFilters,
  catalogGroupFranchises,
  catalogFilters,
  isShuffled,
  switchSection,
  fetchCatalog,
  fetchOngoings,
  fetchAnnouncements,
  fetchCalendar,
  enableCatalogShuffle,
  disableCatalogShuffle,
  refreshCurrentSection,
} = useAnimeSections({ catalogPreset: catalogPreset.value as CatalogFilters })

const ongoingCount = computed(() => ongoings.value.length || null);

type CurrentlyWatchingAnime = { id: number; slug?: string; title_ru?: string; title_en?: string; title_orig?: string; year?: number | null; status?: string; episodes?: number | null; episodes_total?: number | null; score?: number | string | null; poster_url?: string | null; poster_image_url?: string | null; poster_file?: string | null; poster?: string | null; kind?: string; type?: string; genres?: unknown[]; viewers_count?: number };
const currentlyWatching = ref<CurrentlyWatchingAnime[]>([]);
const currentlyWatchingLoading = ref(false);
const currentlyWatchingError = ref<string | null>(null);

const fetchCurrentlyWatching = async () => {
  currentlyWatchingLoading.value = true;
  currentlyWatchingError.value = null;
  try {
    const res = await apiClient.get("/anime/currently-watching/");
    currentlyWatching.value = (res.data?.results || []) as CurrentlyWatchingAnime[];
    } catch {
    currentlyWatchingError.value = "Не удалось загрузить";
    currentlyWatching.value = [];
  } finally {
    currentlyWatchingLoading.value = false;
  }
};

let cwRefreshTimer: ReturnType<typeof setInterval> | null = null;

const startCwPolling = () => {
  stopCwPolling();
  cwRefreshTimer = setInterval(() => {
    if ((currentSection.value as string) === "currently_watching") {
      fetchCurrentlyWatching();
    }
  }, 30_000);
};

const stopCwPolling = () => {
  if (cwRefreshTimer !== null) {
    clearInterval(cwRefreshTimer);
    cwRefreshTimer = null;
  }
};

const switchCurrentlyWatching = () => {
  currentSection.value = "currently_watching" as SectionType;
  try {
    localStorage.setItem("anime_active_section", "currently_watching");
  } catch {}
  router.replace({
    path: route.path,
    query: { ...route.query, section: "currently_watching" },
  });
  fetchCurrentlyWatching();
  startCwPolling();
};

const origSwitchSection = switchSection;
const handleSwitchSection = (key: string) => {
  stopCwPolling();
  void origSwitchSection(key as SectionType);
};

import { onUnmounted } from "vue";
onUnmounted(() => stopCwPolling());
watch(
  () => [route.fullPath, currentSection.value],
  () => {
  },
  { immediate: true },
);
onDeactivated(() => stopCwPolling());
let initiallyActivated = false;
onActivated(() => {
  if (!initiallyActivated) { initiallyActivated = true; return; }
  if (currentSection.value === 'currently_watching') { void fetchCurrentlyWatching(); startCwPolling(); }
  else refreshCurrentSection();
});

onMounted(() => {
  if ((currentSection.value as string) === "currently_watching") {
    fetchCurrentlyWatching();
    startCwPolling();
  }
});

const viewersMap = computed<Record<number, number>>(() => {
  const map: Record<number, number> = {};
  for (const a of currentlyWatching.value) {
    if (a.id && a.viewers_count) map[a.id] = a.viewers_count;
  }
  return map;
});

const tabs = [
  { key: "catalog" as SectionType, label: "Каталог", icon: "book" },
  { key: "ongoings" as SectionType, label: "Онгоинги", icon: "fire" },
  { key: "recommendations" as SectionType, label: "Для вас", icon: "sparkles" },
  { key: "calendar" as SectionType, label: "Календарь", icon: "calendar" },
  { key: "currently_watching" as string, label: "Сейчас смотрят", icon: "eye" },
];

const isIconName = (icon: string): boolean => {
  return /^[a-zA-Z][a-zA-Z0-9-]*$/.test(icon);
};

const currentCatalogFilters = computed(() => catalogFilters.value as FilterState);
const handlePageChange = (page: number) =>
  fetchCatalog(page);
const handleCatalogFilterChange = (filters: FilterState, userInitiated = true) => {
  if (userInitiated) {
    const activeFilterCount = Object.entries(filters).filter(([key, value]) => {
      if (key === "ordering" || key === "page_size") return false;
      if (Array.isArray(value)) return value.length > 0;
      return value !== undefined && value !== null && value !== "" && value !== false;
    }).length;
    analyticsEvent("filter_applied", {
      filter_group: "catalog",
      active_filter_count: Math.min(activeFilterCount, 20),
    });
  }
  fetchCatalog(1, filters as CatalogFilters);
};

onMounted(() => {
  const genreName = route.query.genre_name as string;
  if (genreName) {
    fetchCatalog(1, { ...catalogFilters.value, genres: [genreName] } as CatalogFilters);
  }
});
const shuffleCatalog = () => {
  enableCatalogShuffle();
};
const unshuffleCatalog = () => {
  disableCatalogShuffle();
};

const goToDetail = (anime: Anime) => {
  let target: string;
  if (anime.franchise_slug) {
    target = `/franchise/${anime.franchise_slug}`;
  } else if (anime.franchise_id) {
    target = `/franchise/${anime.franchise_id}`;
  } else {
    target = `/anime/${anime.slug || anime.id}`;
  }
  void router.push(target).then((failure) => {
    if (!failure) analyticsEvent("card_opened", { source: "catalog" });
  });
};
const startWatching = (anime: Anime) => {
  void router.push(`/anime/${anime.slug || anime.id}/watch`).then((failure) => {
    if (!failure) analyticsEvent("card_opened", { source: "catalog" });
  });
};
</script>

<style scoped>
.anime-view {
  min-height: 100vh;
  background: var(--surface-1);
}

.av-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5) var(--space-16);
}

/* ── Табы ─────────────────────────────────────────────────── */
.av-tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
  flex-wrap: wrap;
}

.av-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 40px;
  padding: 0 var(--space-5);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  position: relative;
}

.av-tab:hover {
  background: var(--surface-4);
  color: var(--text-primary);
  border-color: var(--border-default);
}

.av-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.av-tab.active .av-tab-icon,
.av-tab.active :deep(.sakura-icon) {
  color: white !important;
}

.av-tab-icon {
  font-size: 16px;
  line-height: 1;
  color: inherit;
}

.av-tab-badge {
  min-width: 20px;
  height: 18px;
  padding: 0 5px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.av-tab:not(.active) .av-tab-badge {
  background: var(--surface-5);
  color: var(--text-tertiary);
}

/* ── Переходы ─────────────────────────────────────────────── */
.av-fade-enter-active,
.av-fade-leave-active {
  transition: opacity 0.06s;
}
.av-fade-enter-from,
.av-fade-leave-to {
  opacity: 0;
}

@media (max-width: 767px) {
  .av-container {
    padding: var(--space-4) var(--space-3) var(--space-10);
  }
  .av-tabs {
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  .av-tabs::-webkit-scrollbar {
    display: none;
  }
  .av-tab {
    flex-shrink: 0;
    white-space: nowrap;
  }
}
</style>
