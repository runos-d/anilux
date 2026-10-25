import apiClient from "./client";
import type { HomeData } from "@/types";

export interface Anime {
  id: number;
  slug?: string;
  mal_id?: number;
  shikimori_id?: string;
  title_ru: string;
  title_en?: string;
  title_jp?: string;
  year?: number;
  status?: string;
  kind?: string;
  episodes?: number;
  score?: number;
  poster_url?: string;
  poster_image_url?: string;
  description?: string;
  release_date?: string | null;
  release_date_string?: string;
  genres?: string[];
  source?: string;
  match_type?: "exact" | "fuzzy";
  franchise_id?: number | null;
  franchise_slug?: string | null;
}

export interface SearchResults {
  query: string;
  results: Anime[];
  total: number;
  source: string;
  has_fuzzy_matches?: boolean;
}

export interface PaginatedSearchResults extends SearchResults {
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface AnimeListResponse {
  results: Anime[];
  count: number;
  total_count?: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SearchOptions {
  limit?: number;
}

export type SortOrder =
  | "score"
  | "-score"
  | "year"
  | "-year"
  | "title_ru"
  | "-title_ru"
  | "title_en"
  | "-title_en"
  | "episodes"
  | "-episodes"
  | "created_at"
  | "-created_at"
  | (string & {});

export interface AnimeFilters {
  search?: string;
  genres?: string[] | string;
  genre_logic?: "AND" | "OR";
  status?: string[] | string;
  type?: string[] | string;
  kind?: string[] | string;
  year_from?: number;
  year_to?: number;
  score_from?: number;
  score_to?: number;
  episodes_from?: number;
  episodes_to?: number;
  duration_from?: number;
  duration_to?: number;
  studio?: string[] | string;
  excluded_library_statuses?: string[];
  country?: string[] | string;
  age_rating?: string[] | string;
  rus_translation?: "full" | "partial" | "none" | null;
  has_awards?: boolean;
  author?: string;
  director?: string;
  composer?: string;
  season?: "winter" | "spring" | "summer" | "fall";
  season_year?: number;
  ordering?: SortOrder;
  page?: number;
  page_size?: number;
  shuffle?: boolean;
  show_only_franchises?: boolean;
  group_franchises?: boolean;
}

interface SearchParams {
  search?: string;
  page_size?: number;
  q?: string;
  limit?: number;
}

interface ListParams {
  page?: number;
  page_size?: number;
  ordering?: string;
  shuffle?: string;
  search?: string;
  genres?: string;
  genre_logic?: string;
  year_from?: number;
  year_to?: number;
  status?: string;
  type?: string;
  kind?: string;
  episodes_from?: number;
  episodes_to?: number;
  score_from?: number;
  score_to?: number;
  studio?: string;
  duration_from?: number;
  duration_to?: number;
  season?: string;
  season_year?: number;
  author?: string;
  director?: string;
  country?: string;
  age_rating?: string;
  rus_translation?: string;
  has_awards?: string;
  excluded_library_statuses?: string;
  show_only_franchises?: string;
  group_franchises?: string;
}

export interface CatalogSettings {
  id?: number;
  group_franchises: boolean;
  updated_at?: string | null;
}

export interface CalendarAnime {
  id: number;
    shikimori_id?: number | null;
  slug?: string | null;
  title_ru: string;
  title_en?: string;
  title_jp?: string;
  year?: number | null;
  status?: string;
  kind?: string;
  episodes?: number | null;
  score?: number | null;
  poster_url?: string;
  poster_image_url?: string;
  genres?: string[];
  franchise_id?: number | null;
  release_date?: string | null;
  release_date_string?: string;
}

export interface CalendarItem {
  calendar_release_id?: number;
  aired_at: string | null;
  local_day: string;
  time: string;
  episode_number: number | null;
  is_upcoming: boolean;
  schedule_uncertain?: boolean;
  anime: CalendarAnime;
}

export interface CalendarDay {
  date: string;
  weekday: number;
  weekday_name: string;
  in_month: boolean;
  is_today: boolean;
  items: CalendarItem[];
}

export interface CalendarData {
  month_key: string;
  year: number;
  month: number;
  month_label: string;
  today: string;
  grid_start: string;
  grid_end: string;
  has_prev: boolean;
  has_next: boolean;
  next_month_key: string | null;
  prev_month_key: string | null;
  search?: string | null;
  total: number;
  days: CalendarDay[];
}

const toComma = (v: string[] | string | undefined): string | undefined => {
  if (!v) return undefined;
  if (Array.isArray(v)) {
    const filtered = v.filter(Boolean);
    return filtered.length ? filtered.join(",") : undefined;
  }
  return v || undefined;
};

export const animeApi = {
  search: async (
    query: string,
    options?: SearchOptions,
  ): Promise<SearchResults> => {
    const params: SearchParams = {
      search: query,
      page_size: options?.limit || 500,
    };
    const response = await apiClient.get<AnimeListResponse>("/anime/", {
      params,
    });

    return {
      query: query,
      results: response.data.results || [],
      total: response.data.count || 0,
      source: "database",
    };
  },

  searchLegacy: async (
    query: string,
    options?: SearchOptions,
  ): Promise<SearchResults> => {
    const params: SearchParams = { q: query };
    if (options?.limit) params.limit = options.limit;
    const response = await apiClient.get<SearchResults>("/anime/search/", {
      params,
    });
    return response.data;
  },

  searchPaginated: async (
    query: string,
    page = 1,
    pageSize = 10,
    signal?: AbortSignal,
  ): Promise<PaginatedSearchResults> => {
    const response = await apiClient.get<PaginatedSearchResults>("/anime/search/", {
      params: { q: query, page, page_size: pageSize },
      signal,
    });
    return response.data;
  },

  list: async (filters?: AnimeFilters, signal?: AbortSignal): Promise<AnimeListResponse> => {
    const params: ListParams = {};

    if (!filters) {
      const response = await apiClient.get<AnimeListResponse>("/anime/", {
        params, signal,
      });
      return response.data;
    }

    if (filters.page) params.page = filters.page;
    params.page_size = filters.page_size ?? 50;
    params.ordering = filters.ordering ?? "-score";
    if (filters.shuffle) params.shuffle = "true";
    if (filters.search) params.search = filters.search;

    const genres = toComma(filters.genres);
    if (genres) {
      params.genres = genres;
      params.genre_logic = filters.genre_logic ?? "OR";
    }

    if (filters.year_from != null) params.year_from = filters.year_from;
    if (filters.year_to != null) params.year_to = filters.year_to;

    const status = toComma(filters.status);
    if (status) params.status = status;

    const type = toComma(filters.type);
    if (type) params.type = type;

    const kind = toComma(filters.kind);
    if (kind) params.kind = kind;

    if (filters.show_only_franchises) params.show_only_franchises = "true";
    if (filters.group_franchises) params.group_franchises = "true";

    if (filters.episodes_from != null)
      params.episodes_from = filters.episodes_from;
    if (filters.episodes_to != null) params.episodes_to = filters.episodes_to;
    if (filters.score_from != null) params.score_from = filters.score_from;
    if (filters.score_to != null) params.score_to = filters.score_to;

    const studio = toComma(filters.studio);
    if (studio) params.studio = studio;

    if (filters.duration_from != null)
      params.duration_from = filters.duration_from;
    if (filters.duration_to != null) params.duration_to = filters.duration_to;

    if (filters.season) params.season = filters.season;
    if (filters.season_year) params.season_year = filters.season_year;
    if (filters.author) params.author = filters.author;
    if (filters.director) params.director = filters.director;

    const country = toComma(filters.country);
    const age_rating = toComma(filters.age_rating);
    if (country) params.country = country;
    if (age_rating) params.age_rating = age_rating;
    if (filters.rus_translation)
      params.rus_translation = filters.rus_translation;
    if (filters.has_awards) params.has_awards = "true";

    const excludedLibraryStatuses = toComma(filters.excluded_library_statuses);
    if (excludedLibraryStatuses)
      params.excluded_library_statuses = excludedLibraryStatuses;

    const response = await apiClient.get<AnimeListResponse>("/anime/", {
      params, signal,
    });
    return response.data;
  },

  get: async (id: number | string): Promise<Anime> => {
    const response = await apiClient.get<Anime>(`/anime/${id}/`);
    return response.data;
  },

  getCatalogSettings: async (): Promise<CatalogSettings> => {
    const response = await apiClient.get<CatalogSettings>(
      "/anime/catalog-settings/",
    );
    return response.data;
  },

  getEpisodes: async (id: number | string) => {
    const response = await apiClient.get(`/anime/${id}/episodes/`);
    return response.data;
  },

  getTranslations: async (id: number | string) => {
    const response = await apiClient.get(`/anime/${id}/translations/`);
    return response.data;
  },

  getVideoLink: async (
    id: number | string,
    params: {
      episode?: number;
      translation_id?: string;
      quality?: string;
    },
  ) => {
    const response = await apiClient.get(`/anime/${id}/get_video_link/`, {
      params,
    });
    return response.data;
  },

  saveWatchProgress: async (
    id: number | string,
    data: {
      episode_id: number;
      current_time: number;
      duration?: number;
    },
  ) => {
    const response = await apiClient.post(
      `/anime/${id}/save_watch_progress/`,
      data,
    );
    return response.data;
  },

  getWatchProgress: async (id: number | string) => {
    const response = await apiClient.get(`/anime/${id}/watch_progress/`);
    return response.data;
  },

  getOngoings: async (): Promise<Anime[]> => {
    const PAGE_SIZE = 200;
    const all: Anime[] = [];
    let page = 1;
    while (true) {
      const response = await apiClient.get<AnimeListResponse>("/anime/", {
        params: {
          status: "ongoing",
          ordering: "-score",
          page_size: PAGE_SIZE,
          page,
        },
      });
      const results = response.data.results || [];
      all.push(...results);
      if (page >= (response.data.total_pages ?? 1) || !results.length) break;
      page++;
    }
    return all;
  },

  getAnnouncements: async (): Promise<Anime[]> => {
    const all: Anime[] = [];
    const existingIds = new Set<number>();

    try {
      const PAGE_SIZE = 200;
      let page = 1;
      while (true) {
        const response = await apiClient.get<AnimeListResponse>(
          "/anime/announcements/",
          {
            params: { ordering: "-score", page_size: PAGE_SIZE, page },
          },
        );
        const results = response.data.results || [];
        for (const a of results) {
          const id = a.id;
          if (id && !existingIds.has(id)) {
            existingIds.add(id);
            all.push(a);
          }
        }
        if (page >= (response.data.total_pages ?? 1) || !results.length) break;
        page++;
      }
    } catch (e) {
      console.warn(
        "Failed to fetch announcements from /anime/announcements/:",
        e,
      );
    }

    return all;
  },

  getRecommendations: async (limit: number = 12): Promise<Anime[]> => {
    const response = await apiClient.get<AnimeListResponse>("/anime/", {
      params: { ordering: "-score", page_size: limit },
    });
    return response.data.results || [];
  },

  getRandomAnime: async (): Promise<Anime> => {
    const response = await apiClient.get<Anime>("/anime/random/", {
      params: { t: Date.now() },
    });
    return response.data;
  },

  getRandomAnimeList: async (limit: number = 6): Promise<Anime[]> => {
    const response = await apiClient.get<Anime[]>("/anime/random/", {
      params: { limit, t: Date.now() },
    });
    return Array.isArray(response.data) ? response.data : [response.data];
  },

  getHomeData: async (): Promise<HomeData> => {
    const response = await apiClient.get<HomeData>("/anime/home/", { params: { v: 'episodes-v1' } });
    return response.data;
  },

  getCalendar: async (month?: string, search?: string, signal?: AbortSignal): Promise<CalendarData> => {
    const params: Record<string, string> = {
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    };
    if (month) params.month = month;
    if (search) params.search = search;
    const response = await apiClient.get<CalendarData>("/anime/calendar/", {
      params: Object.keys(params).length ? params : undefined,
      signal,
    });
    return response.data;
  },

  getPersonalizedRecommendations: async () => {
    const response = await apiClient.get("/anime/home/personalized/");
    return response.data;
  },

  addToLibrary: async (data: {
    anime: number;
    status: "planned" | "started" | "completed" | "dropped";
    rating?: number | null;
    current_episode?: number;
    notes?: string;
  }) => {
    const response = await apiClient.post("/users/library/", data);
    return response.data;
  },

  createClipTask: async (data: {
    anime: number;
    episode: number;
    season?: number;
    start_time: number;
    end_time: number;
    label?: string;
    quality?: string;
  }) => {
    const response = await apiClient.post("/anime/clips/", {
      ...data,
      task_type: "clip",
    });
    return response.data;
  },

  createScreenshotTask: async (data: {
    anime: number;
    episode?: number;
    timestamp: number;
    quality?: string;
  }) => {
    const response = await apiClient.post("/anime/clips/", {
      ...data,
      task_type: "screenshot",
    });
    return response.data;
  },

  getClipTask: async (taskId: string) => {
    const response = await apiClient.get(`/anime/clips/${taskId}/`);
    return response.data;
  },

  getClipTaskStatus: async (taskId: string) => {
    const response = await apiClient.get(`/anime/clips/${taskId}/status/`);
    return response.data;
  },

  retryClipTask: async (taskId: string) => {
    const response = await apiClient.post(`/anime/clips/${taskId}/retry/`);
    return response.data;
  },

  deleteClipTask: async (taskId: string) => {
    const response = await apiClient.delete(`/anime/clips/${taskId}/`);
    return response.data;
  },

  listClipTasks: async () => {
    const response = await apiClient.get("/anime/clips/");
    return response.data;
  },

  createScreenshotLegacy: async (data: {
    anime_id: number;
    episode?: number;
    timestamp: number;
  }) => {
    const response = await apiClient.post("/anime/screenshot/", data);
    return response.data;
  },

  createClipLegacy: async (data: {
    anime_id: number;
    episode?: number;
    start: number;
    end: number;
    label?: string;
  }) => {
    const response = await apiClient.post("/anime/clip/create/", data);
    return response.data;
  },
};

export default animeApi;
