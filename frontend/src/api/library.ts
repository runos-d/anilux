import apiClient from "./client";

export type LibraryStatus =
  "started" | "completed" | "on_hold" | "dropped" | "planned";

export type CollectionTab = LibraryStatus | "favorite";

export interface LibraryItem {
  item_type?: "anime";
  id: number;
  user?: number;
  anime:
    | number
    | {
        id: number;
        slug?: string;
        title_ru: string;
        title_en: string;
        poster?: string;
        poster_url?: string;
        poster_image_url?: string;
        episodes?: number;
        episodes_count?: number;
        progress_total?: number;
        status?: string;
        score?: number;
        year?: number;
        type?: string;
        kind?: string;
        genres?: Array<string | { id: number; name: string; slug: string }>;
      };
  anime_id: number;
  anime_slug?: string;
  anime_title_ru: string;
  anime_title_en: string;
  anime_poster: string | null;
  anime_episodes_count: number | null;
  anime_episode_duration?: number | null;
  anime_total_duration?: number | null;
  anime_status_display?: string;
  anime_status?: string;
  anime_kind?: string;
  anime_year?: number;
  anime_score?: number;
  anime_genres?: string[];
  status: LibraryStatus;
  current_season: number;
  current_episode: number;
  episodes_watched: number;
  real_episodes_watched: number;
  rating: number | null;
  added_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
  notes: string;
  is_favorite: boolean;
  rewatch_count: number;
  progress_percentage: number;
}

export interface FavoriteFranchiseEntry {
  id: number;
  slug?: string;
  title_ru: string;
  title_en?: string;
  poster?: string | null;
  poster_url?: string;
  poster_image_url?: string;
  episodes?: number | null;
  episode_duration?: number | null;
  total_duration?: number | null;
  status?: string;
  kind?: string;
  year?: number | null;
  score?: number | null;
  genres?: string[];
  franchise_order?: number;
}

export interface FavoriteFranchiseCollectionItem {
  item_type: "franchise";
  id: number;
  franchise_id: number;
  anime_ids: number[];
  franchise: {
    id: number;
    name: string;
    slug?: string;
    description?: string;
    poster?: string | null;
    poster_url?: string | null;
    poster_image_url?: string | null;
    score?: number | null;
    avg_score?: number | null;
    year_start?: number | null;
    year_end?: number | null;
    year_range?: string;
    parts_count: number;
    all_genres?: string[];
    all_posters?: string[];
    entries: FavoriteFranchiseEntry[];
    is_favorite: true;
  };
}

export type CollectionItem = LibraryItem | FavoriteFranchiseCollectionItem;

export const isFavoriteFranchiseItem = (
  item: CollectionItem,
): item is FavoriteFranchiseCollectionItem => item.item_type === "franchise";

export interface LibraryStats {
  total: number;
  started: number;
  completed: number;
  on_hold: number;
  dropped: number;
  planned: number;
  favorites: number;
  episodes_watched: number;
  hours_watched: number;
  hours_remaining: number;
  avg_rating: number;
  total_rewatches: number;
}

export interface PaginatedLibraryItems {
  results: CollectionItem[];
  count: number;
  next?: string | null;
  previous?: string | null;
}

export interface WrappedGenre {
  name: string;
  count: number;
  pct: number;
}

export interface WrappedStudio {
  name: string;
  count: number;
}

export interface WrappedDecade {
  label: string;
  count: number;
}

export interface WrappedKind {
  value: string;
  count: number;
}

export interface WrappedTopRated {
  anime_id: number;
  title: string;
  rating: number;
  score: number;
  year: number | null;
  poster: string | null;
  genres: string[];
}

export interface WrappedFranchise {
  franchise_id: number;
  name: string;
  watched_parts: number;
  completed_parts: number;
}

export interface WrappedPortraitTag {
  emoji: string;
  label: string;
  reason: string;
}

export interface WrappedData {
  user: { id: number; username: string; display_name: string };
  counts: {
    total: number;
    started: number;
    completed: number;
    on_hold: number;
    dropped: number;
    planned: number;
    favorites: number;
  };
  episodes_watched: number;
  hours_watched: number;
  ratings_given: number;
  avg_rating: number | null;
  rewatches: number;
  genres: WrappedGenre[];
  studios: WrappedStudio[];
  decades: WrappedDecade[];
  kinds: WrappedKind[];
  top_rated: WrappedTopRated[];
  franchises: WrappedFranchise[];
  portrait: WrappedPortraitTag[];
}

export const libraryApi = {
  getLibrary: async (params?: {
    status?: LibraryStatus | "";
    is_favorite?: boolean;
    search?: string;
    ordering?: string;
    group_franchises?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<CollectionItem[] | PaginatedLibraryItems> => {
    const response = await apiClient.get<
      CollectionItem[] | PaginatedLibraryItems
    >("/users/library/", { params });
    return response.data;
  },

  addToLibrary: async (data: {
    anime: number;
    status?: LibraryStatus;
    current_season?: number;
    current_episode?: number;
    episodes_watched?: number;
    rating?: number | null;
    notes?: string;
    is_favorite?: boolean;
  }): Promise<LibraryItem> => {
    const response = await apiClient.post<LibraryItem>("/users/library/", data);
    return response.data;
  },

  updateLibraryItem: async (
    id: number,
    data: Partial<{
      status: LibraryStatus;
      current_season: number;
      current_episode: number;
      episodes_watched: number;
      rating: number | null;
      notes: string;
      is_favorite: boolean;
    }>,
  ): Promise<LibraryItem> => {
    const response = await apiClient.patch<LibraryItem>(
      `/users/library/${id}/`,
      data,
    );
    return response.data;
  },

  deleteLibraryItem: async (id: number): Promise<void> => {
    await apiClient.delete(`/users/library/${id}/`);
  },

  getStatistics: async (): Promise<LibraryStats> => {
    const response = await apiClient.get<LibraryStats>(
      "/users/library/statistics/",
    );
    return response.data;
  },

  getWrapped: async (userId?: number): Promise<WrappedData> => {
    const response = await apiClient.get<WrappedData>("/users/library/wrapped/", {
      params: userId ? { user_id: userId } : undefined,
    });
    return response.data;
  },

  toggleFavorite: async (id: number): Promise<{ is_favorite: boolean }> => {
    const response = await apiClient.post<{ is_favorite: boolean }>(
      `/users/library/${id}/mark_favorite/`,
    );
    return response.data;
  },

  checkAnime: async (
    animeId: number,
  ): Promise<{
    in_library: boolean;
    status?: LibraryStatus;
    current_season?: number;
    current_episode?: number;
    rating?: number | null;
    is_favorite?: boolean;
  }> => {
    const response = await apiClient.get("/users/library/check_anime/", {
      params: { anime_id: animeId },
    });
    return response.data;
  },
};

export default libraryApi;
