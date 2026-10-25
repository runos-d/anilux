import { queryClient } from '@/lib/queryClient';
import { afterInitialContent } from '@/lib/initialContent';
import { ref, computed, onMounted, onActivated, onDeactivated, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import animeApi from "@/api/anime";
import type { Anime } from "@/types";
import type { CalendarData } from "@/api/anime";
import { useCachedReads } from './useCachedReads';
import { isRequestCancelled } from '@/api/client';
import { animeSections, initialAnimeSection, type AnimeSection } from '@/lib/animeSection';

export type { AnimeSection } from '@/lib/animeSection';

export interface CatalogFilters {
  page_size?: number;
  ordering?: string;
  search?: string;
  genres?: string[];
  genre_logic?: "AND" | "OR" | undefined;
  year_from?: number;
  year_to?: number;
  status?: string | string[];
  type?: string | string[];
  kind?: string[];
  episodes_from?: number;
  episodes_to?: number;
  score_from?: number;
  score_to?: number;
  studio?: string;
  excluded_library_statuses?: string[];
  show_only_franchises?: boolean;
}

const queryString = (value: unknown): string | undefined => {
  const candidate = Array.isArray(value) ? value[0] : value;
  return typeof candidate === 'string' ? candidate : undefined;
};
const queryList = (value: unknown) => {
  const raw = queryString(value);
  return raw ? raw.split(',').map(item => item.trim()).filter(Boolean) : undefined;
};
const queryNumber = (value: unknown) => {
  const raw = queryString(value);
  const parsed = raw == null || raw === '' ? NaN : Number(raw);
  return Number.isFinite(parsed) ? parsed : undefined;
};

export function catalogFiltersFromQuery(query: Record<string, unknown>): CatalogFilters {
  const result: CatalogFilters = {};
  const search = queryString(query.search);
  const legacyGenre = queryString(query.genre_name);
  if (search) result.search = search;
  const genres = queryList(query.genres) || (legacyGenre ? [legacyGenre] : undefined);
  if (genres?.length) result.genres = genres;
  const genreLogic = queryString(query.genre_logic)?.toUpperCase();
  if (genreLogic === 'AND' || genreLogic === 'OR') result.genre_logic = genreLogic;
  for (const key of ['status', 'type', 'kind'] as const) {
    const values = queryList(query[key]);
    if (values?.length) result[key] = key === 'kind' ? values : values;
  }
  const studio = queryString(query.studio);
  if (studio) result.studio = studio;
  for (const key of ['year_from', 'year_to', 'episodes_from', 'episodes_to', 'score_from', 'score_to', 'page_size'] as const) {
    const value = queryNumber(query[key]);
    if (value != null) result[key] = value;
  }
  const excluded = queryList(query.excluded_library_statuses);
  if (excluded?.length) result.excluded_library_statuses = excluded;
  if (queryString(query.show_only_franchises) === 'true') result.show_only_franchises = true;
  const ordering = queryString(query.ordering);
  if (ordering) result.ordering = ordering;
  return result;
}

export function useAnimeSections(options?: { catalogPreset?: CatalogFilters }) {
  let active = true;
  const read = useCachedReads(() => active);
  let catalogRequest = 0;
  let ongoingsRequest = 0;
  let calendarRequest = 0;
  const route = useRoute();
  const router = useRouter();
  const screenPath = route.path;

  const SECTION_STORAGE_KEY = "anime_active_section";
  let savedSection: string | null = null;
  try { savedSection = localStorage.getItem(SECTION_STORAGE_KEY); } catch {}
  const currentSection = ref<AnimeSection>(initialAnimeSection(route.query, savedSection,
    !!options?.catalogPreset && Object.keys(options.catalogPreset).length > 0));

  const originalCatalogAnime = ref<Anime[]>([]);
  const originalOngoings = ref<Anime[]>([]);
  const originalAnnouncements = ref<Anime[]>([]);
  const originalRecommendations = ref<Anime[]>([]);
  const originalRandomAnimeList = ref<Anime[]>([]);

  const catalogAnime = ref<Anime[]>([]);
  const ongoings = ref<Anime[]>([]);
  const announcements = ref<Anime[]>([]);
  const recommendations = ref<Anime[]>([]);
  const randomAnimeList = ref<Anime[]>([]);

  const calendarData = ref<CalendarData | null>(null);
  const calendarLoading = ref(false);
  const calendarError = ref<string | null>(null);
  const calendarMonth = ref<string | null>(null);

  const catalogLoading = ref(false);
  const ongoingsLoading = ref(false);
  const announcementsLoading = ref(false);
  const recommendationsLoading = ref(false);
  const randomLoading = ref(false);

  const catalogError = ref<string | null>(null);
  const ongoingsError = ref<string | null>(null);
  const announcementsError = ref<string | null>(null);
  const recommendationsError = ref<string | null>(null);
  const randomError = ref<string | null>(null);

  const catalogPage = ref(1);
  const catalogTotalPages = ref(1);
  const catalogTotalCount = ref(0);
  const ongoingsPage = ref(1);
  const ongoingsTotalPages = ref(1);
  const ongoingsTotalCount = ref(0);
  const ongoingsFilters = ref<CatalogFilters>({ page_size: 50, ordering: "-score" });

  const isShuffled = ref<Record<AnimeSection, boolean>>({
    catalog: false,
    ongoings: false,
    recommendations: false,
    announcements: false,
    random: false,
    calendar: false,
    currently_watching: false,
  });

  const shuffleArray = <T>(array: T[]): T[] => {
    const shuffled: T[] = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j] as T, shuffled[i] as T];
    }
    return shuffled;
  };

  const shuffleCurrentSection = () => {
    const section = currentSection.value;
    const map: Record<
      AnimeSection,
      { get: () => Anime[]; set: (v: Anime[]) => void }
    > = {
      catalog: {
        get: () => catalogAnime.value,
        set: (v) => {
          catalogAnime.value = v;
        },
      },
      ongoings: {
        get: () => ongoings.value,
        set: (v) => {
          ongoings.value = v;
        },
      },
      recommendations: {
        get: () => recommendations.value,
        set: (v) => {
          recommendations.value = v;
        },
      },
      announcements: {
        get: () => announcements.value,
        set: (v) => {
          announcements.value = v;
        },
      },
      random: {
        get: () => randomAnimeList.value,
        set: (v) => {
          randomAnimeList.value = v;
        },
      },
      calendar: { get: () => [], set: () => {} },
      currently_watching: { get: () => [], set: () => {} },
    };
    const entry = map[section];
    if (entry.get().length > 0) {
      entry.set(shuffleArray(entry.get()));
      isShuffled.value[section] = true;
    }
  };

  const unshuffleCurrentSection = () => {
    const section = currentSection.value;
    const origMap: Record<
      AnimeSection,
      { get: () => Anime[]; set: (v: Anime[]) => void }
    > = {
      catalog: {
        get: () => originalCatalogAnime.value,
        set: (v) => {
          catalogAnime.value = v;
        },
      },
      ongoings: {
        get: () => originalOngoings.value,
        set: (v) => {
          ongoings.value = v;
        },
      },
      recommendations: {
        get: () => originalRecommendations.value,
        set: (v) => {
          recommendations.value = v;
        },
      },
      announcements: {
        get: () => originalAnnouncements.value,
        set: (v) => {
          announcements.value = v;
        },
      },
      random: {
        get: () => originalRandomAnimeList.value,
        set: (v) => {
          randomAnimeList.value = v;
        },
      },
      calendar: { get: () => [], set: () => {} },
      currently_watching: { get: () => [], set: () => {} },
    };
    origMap[section].set([...origMap[section].get()]);
    isShuffled.value[section] = false;
  };

  const currentSectionIsShuffled = computed(
    () => isShuffled.value[currentSection.value],
  );

  const fetchOngoings = async (page: number = 1, filters?: CatalogFilters) => {
    ongoingsLoading.value = true;
    ongoingsError.value = null;
    if (filters) ongoingsFilters.value = { ...filters, status: undefined };
    const request = ++ongoingsRequest;
    try {
      const f = ongoingsFilters.value;
      const response = await animeApi.list({
        page,
        page_size: f.page_size || 50,
        ordering: f.ordering || "-score",
        search: f.search,
        genres: f.genres,
        genre_logic: f.genre_logic,
        year_from: f.year_from,
        year_to: f.year_to,
        status: "ongoing",
        type: f.type,
        kind: f.kind,
        episodes_from: f.episodes_from,
        episodes_to: f.episodes_to,
        score_from: f.score_from,
        score_to: f.score_to,
        studio: f.studio,
        excluded_library_statuses: f.excluded_library_statuses,
        show_only_franchises: f.show_only_franchises,
        group_franchises: !!f.show_only_franchises,
      });
      if (request !== ongoingsRequest) return;
      const data = response.results || [];
      ongoings.value = data;
      originalOngoings.value = [...data];
      ongoingsPage.value = page;
      ongoingsTotalPages.value = response.total_pages || 1;
      ongoingsTotalCount.value = response.count || 0;
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      if (request !== ongoingsRequest) return;
      ongoingsError.value = err instanceof Error ? err.message : "Не удалось загрузить онгоинги";
      ongoings.value = [];
      originalOngoings.value = [];
    } finally {
      if (request === ongoingsRequest) ongoingsLoading.value = false;
    }
  };

  const fetchAnnouncements = async () => {
    announcementsLoading.value = true;
    announcementsError.value = null;
    try {
      const data = await animeApi.getAnnouncements();
      announcements.value = data;
      originalAnnouncements.value = [...data];
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      announcementsError.value = err instanceof Error ? err.message : "Не удалось загрузить анонсы";
      announcements.value = [];
      originalAnnouncements.value = [];
    } finally {
      announcementsLoading.value = false;
    }
  };

  const fetchRecommendations = async () => {
    recommendationsLoading.value = true;
    recommendationsError.value = null;
    try {
      const response = await animeApi.list({
        ordering: "-score",
        page_size: 12,
      });
      recommendations.value = response.results || [];
      originalRecommendations.value = [...(response.results || [])];
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      recommendationsError.value =
        err instanceof Error ? err.message : "Не удалось загрузить рекомендации";
      recommendations.value = [];
      originalRecommendations.value = [];
    } finally {
      recommendationsLoading.value = false;
    }
  };

  const fetchRandomAnimeList = async (limit: number = 6) => {
    randomLoading.value = true;
    randomError.value = null;
    try {
      const data = await animeApi.getRandomAnimeList(limit);
      randomAnimeList.value = data;
      originalRandomAnimeList.value = [...data];
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      randomError.value = err instanceof Error ? err.message : "Не удалось загрузить случайные аниме";
      randomAnimeList.value = [];
      originalRandomAnimeList.value = [];
    } finally {
      randomLoading.value = false;
    }
  };

  const fetchCalendar = async (month?: string) => {
    if (month) calendarMonth.value = month;
    calendarLoading.value = true;
    calendarError.value = null;
    try {
      const request = ++calendarRequest;
      const selectedMonth = calendarMonth.value || undefined;
      await read(['calendar', 'history-v4', Intl.DateTimeFormat().resolvedOptions().timeZone, selectedMonth], signal => animeApi.getCalendar(selectedMonth, undefined, signal), data => {
        if (request === calendarRequest) calendarData.value = data;
      }, true);
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      calendarError.value =
        err instanceof Error ? err.message : "Не удалось загрузить календарь";
      calendarData.value = null;
    } finally {
      calendarLoading.value = false;
    }
  };

  const setCalendarMonth = (month: string) => {
    calendarMonth.value = month;
    fetchCalendar(month);
  };

  const initialQueryFilters = catalogFiltersFromQuery(route.query);
  const catalogFilters = ref<CatalogFilters>({ ...(options?.catalogPreset || {}), ...initialQueryFilters });
  const catalogShuffle = ref(false);
  let lastRouteSearch = typeof route.query.search === "string" ? route.query.search : undefined;

  onDeactivated(() => { active = false; });
  onActivated(() => {
    active = true;
    const section = route.query.section;
    if (typeof section === 'string' && animeSections.includes(section as AnimeSection)) {
      currentSection.value = section as AnimeSection;
    }
    const search = typeof route.query.search === 'string' ? route.query.search : undefined;
    if (lastRouteSearch !== search) {
      lastRouteSearch = search;
      const filters = { ...catalogFilters.value };
      delete filters.search;
      catalogFilters.value = search ? { ...filters, search } : filters;
    }
  });

  const catalogGroupFranchises = ref(queryClient.getQueryData<{group_franchises: boolean}>(['read', 'public', 'catalog-settings'])?.group_franchises ?? true);

  const withRetry = async <T>(
    fn: () => Promise<T>,
    retries = 2,
    delayMs = 400,
  ): Promise<T> => {
    let lastError: unknown;
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        return await fn();
      } catch (err) {
        if (isRequestCancelled(err)) throw err;
        lastError = err;
        if (attempt < retries) {
          await new Promise((resolve) => setTimeout(resolve, delayMs * (attempt + 1)));
        }
      }
    }
    throw lastError;
  };

  const fetchCatalogSettings = async () => {
    try {
      await read(['catalog-settings'], () => withRetry(() => animeApi.getCatalogSettings(), 2, 300), data => {
        const changed = catalogGroupFranchises.value !== (data.group_franchises !== false);
        catalogGroupFranchises.value = data.group_franchises !== false;
        if (changed && active && route.path === screenPath && currentSection.value === 'catalog') void fetchCatalog(1);
      }, true);
    } catch {
      catalogGroupFranchises.value = true;
    }
  };

  const fetchCatalog = async (page: number = 1, filters?: CatalogFilters) => {
    catalogLoading.value = true;
    catalogError.value = null;

    if (filters) {
      catalogFilters.value = filters;
      catalogShuffle.value = false;
      isShuffled.value.catalog = false;
    }

    const request = ++catalogRequest;
    try {
      const f = catalogFilters.value;
      const groupFranchisesForRequest =
        !!f.show_only_franchises ||
        (catalogGroupFranchises.value && !f.excluded_library_statuses?.length);

      const apply = (response: Awaited<ReturnType<typeof animeApi.list>>) => {
        if (request !== catalogRequest) return;
        catalogAnime.value = response.results || [];
        if (page === 1) originalCatalogAnime.value = [...(response.results || [])];
        catalogTotalPages.value = response.total_pages || 1;
        catalogTotalCount.value = response.count || 0;
        catalogPage.value = page;
      };
      const response = await read(['catalog', page, { ...f }, catalogShuffle.value, groupFranchisesForRequest], signal => withRetry(
        () =>
          animeApi.list({
            page,
            page_size: f.page_size || 50,
            ordering: f.ordering || "-score",
            shuffle: catalogShuffle.value,
            search: f.search,
            genres: f.genres,
            genre_logic: f.genre_logic,
            year_from: f.year_from,
            year_to: f.year_to,
            status: f.status,
            type: f.type,
            kind: f.kind,
            episodes_from: f.episodes_from != null ? f.episodes_from : undefined,
            episodes_to: f.episodes_to != null ? f.episodes_to : undefined,
            score_from: f.score_from != null ? f.score_from : undefined,
            score_to: f.score_to != null ? f.score_to : undefined,
            studio: f.studio,
            excluded_library_statuses: f.excluded_library_statuses,
            show_only_franchises: f.show_only_franchises,
            group_franchises: groupFranchisesForRequest,
          }, signal),
        2,
        400,
      ), apply, !f.excluded_library_statuses?.length);
      if (request !== catalogRequest) return;
      catalogAnime.value = response.results || [];
      if (page === 1)
        originalCatalogAnime.value = [...(response.results || [])];
      catalogTotalPages.value = response.total_pages || 1;
      catalogTotalCount.value = response.count || 0;
      catalogPage.value = page;
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      if (request !== catalogRequest) return;
      catalogError.value = err instanceof Error ? err.message : "Не удалось загрузить каталог";
      catalogAnime.value = [];
    } finally {
      if (request === catalogRequest) catalogLoading.value = false;
    }
  };

  const loadSection = (section: AnimeSection) => {
    switch (section) {
      case 'ongoings': if (!ongoings.value.length) void fetchOngoings(); break;
      case 'announcements': if (!announcements.value.length) void fetchAnnouncements(); break;
      case 'random': if (!randomAnimeList.value.length) void fetchRandomAnimeList(6); break;
      case 'calendar': if (!calendarData.value) void fetchCalendar(calendarMonth.value || undefined); break;
      case 'catalog': if (!catalogAnime.value.length) void fetchCatalog(1); break;
    }
  };
  let sectionNavigation = 0;
  const switchSection = async (section: AnimeSection) => {
    const navigation = ++sectionNavigation;
    currentSection.value = section;
    try {
      localStorage.setItem(SECTION_STORAGE_KEY, section);
    } catch {}
    if ((section !== "catalog" || route.query.section) && route.query.section !== section) {
      await router.replace({ path: route.path, query: { ...route.query, section } });
    }
    if (navigation === sectionNavigation && currentSection.value === section) loadSection(section);
  };

  const refreshCurrentSection = () => {
    switch (currentSection.value) {
      case "ongoings":
        fetchOngoings();
        break;
      case "recommendations":
        void queryClient.invalidateQueries({ queryKey: ['recommendations'] });
        break;
      case "announcements":
        fetchAnnouncements();
        break;
      case "random":
        fetchRandomAnimeList(6);
        break;
      case "calendar":
        fetchCalendar(calendarMonth.value || undefined);
        break;
      case "catalog":
        afterInitialContent(() => { if (active && route.path === screenPath && currentSection.value === 'catalog') void fetchCatalogSettings(); });
        fetchCatalog(catalogPage.value);
        break;
    }
  };

  const currentData = computed(() => {
    switch (currentSection.value) {
      case "ongoings":
        return ongoings.value;
      case "recommendations":
        return recommendations.value;
      case "announcements":
        return announcements.value;
      case "random":
        return randomAnimeList.value;
      case "calendar":
        return [];
      case "catalog":
        return catalogAnime.value;
      default:
        return [];
    }
  });

  const currentLoading = computed(() => {
    switch (currentSection.value) {
      case "ongoings":
        return ongoingsLoading.value;
      case "recommendations":
        return recommendationsLoading.value;
      case "announcements":
        return announcementsLoading.value;
      case "random":
        return randomLoading.value;
      case "calendar":
        return calendarLoading.value;
      case "catalog":
        return catalogLoading.value;
      default:
        return false;
    }
  });

  const currentError = computed(() => {
    switch (currentSection.value) {
      case "ongoings":
        return ongoingsError.value;
      case "recommendations":
        return recommendationsError.value;
      case "announcements":
        return announcementsError.value;
      case "random":
        return randomError.value;
      case "calendar":
        return calendarError.value;
      case "catalog":
        return catalogError.value;
      default:
        return null;
    }
  });

  const loadAllSections = async () => { refreshCurrentSection(); };

onMounted(async () => {
      afterInitialContent(() => { if (active && route.path === screenPath && currentSection.value === 'catalog') void fetchCatalogSettings(); });
      
      const searchQuery = route.query.search as string;
      if (searchQuery) {
        currentSection.value = "catalog";
        catalogFilters.value = { ...catalogFilters.value, ...catalogFiltersFromQuery(route.query) };
        fetchCatalog(1, catalogFilters.value);
        return;
      }
      
      const sectionParam = route.query.section as string;
      if (sectionParam && animeSections.includes(sectionParam as AnimeSection)) {
        currentSection.value = sectionParam as AnimeSection;
        try {
          localStorage.setItem(SECTION_STORAGE_KEY, sectionParam);
        } catch {}
      } else {
        try {
          const saved = localStorage.getItem(
            SECTION_STORAGE_KEY,
          ) as AnimeSection | null;
          if (saved && animeSections.includes(saved) && !options?.catalogPreset && !route.query.genre_name) {
            currentSection.value = saved;
          }
        } catch {}
      }
      if (currentSection.value !== "currently_watching") {
        if (
          currentSection.value === "catalog" &&
          options?.catalogPreset &&
          Object.keys(options.catalogPreset).length > 0
        ) {
          catalogFilters.value = options.catalogPreset;
        } else {
          const searchQuery = route.query.search as string;
          if (currentSection.value === "catalog" && searchQuery) {
            catalogFilters.value = { search: searchQuery };
          }
          if (route.query.section || currentSection.value !== 'catalog') {
            switchSection(currentSection.value);
          }
        }
      }
    });

  watch(
    () => route.query.section,
    (newSection) => {
      if (!active || route.path !== screenPath) return;
      const s = newSection as AnimeSection;
      if (s && animeSections.includes(s)) {
        if (currentSection.value !== s) {
          ++sectionNavigation;
          currentSection.value = s;
          try { localStorage.setItem(SECTION_STORAGE_KEY, s); } catch {}
          loadSection(s);
        }
      }
    },
  );

  watch(
    () => JSON.stringify(route.query),
    () => {
      if (!active || route.path !== screenPath || currentSection.value !== 'catalog') return;
      const next = { ...(options?.catalogPreset || {}), ...catalogFiltersFromQuery(route.query) };
      if (JSON.stringify(next) === JSON.stringify(catalogFilters.value)) return;
      catalogFilters.value = next;
      void fetchCatalog(1);
    },
  );

  watch(
    () => route.query.search,
    (newSearch) => {
      if (!active || route.path !== screenPath) return;
      const searchQuery = newSearch as string;
      if (currentSection.value === "catalog") {
        if (searchQuery) {
          catalogFilters.value = { ...catalogFilters.value, search: searchQuery };
        } else {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { search, ...rest } = catalogFilters.value;
          catalogFilters.value = rest;
        }
        fetchCatalog(1, catalogFilters.value);
      }
    },
  );

  const enableCatalogShuffle = () => {
    catalogShuffle.value = true;
    isShuffled.value.catalog = true;
    fetchCatalog(1);
  };

  const disableCatalogShuffle = () => {
    catalogShuffle.value = false;
    isShuffled.value.catalog = false;
    fetchCatalog(1);
  };

  return {
    currentSection,
    currentData,
    currentLoading,
    currentError,
    catalogAnime,
    ongoings,
    announcements,
    recommendations,
    randomAnimeList,
    calendarData,
    calendarLoading,
    calendarError,
    calendarMonth,
    setCalendarMonth,
    catalogLoading,
    ongoingsLoading,
    announcementsLoading,
    recommendationsLoading,
    randomLoading,
    catalogError,
    ongoingsError,
    announcementsError,
    recommendationsError,
    randomError,
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
    currentSectionIsShuffled,
    catalogShuffle,
    shuffleCurrentSection,
    unshuffleCurrentSection,
    enableCatalogShuffle,
    disableCatalogShuffle,
    switchSection,
    refreshCurrentSection,
    fetchCatalog,
    fetchOngoings,
    fetchAnnouncements,
    fetchRecommendations,
    fetchRandomAnimeList,
    fetchCalendar,
    loadAllSections,
  };
}
