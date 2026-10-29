import apiClient from "./client";
import { event as analyticsEvent } from "@/analytics";
import type { AxiosResponse } from "axios";

export type PlaylistVisibility = "public" | "private" | "link";

export interface PlaylistTopic { slug: string; name: string; group?: string; description?: string }
export interface PlaylistSelectionItem { anime_id: number; notes?: string }

export interface Playlist {
  id: number | string;
  user_id: number;
  user_unique_id?: string;
  user_username: string;
  user_avatar: string | null;
  user?: {
    id: number;
    username: string;
    avatar: string | null;
  };
  title: string;
  description: string;
  cover_image?: string | null;
  cover_mode?: "auto" | "custom";
  cover_urls?: string[];

  visibility: PlaylistVisibility;
  is_public: boolean;
  is_private: boolean;
  is_link_only: boolean;

  share_token?: string | null;
  is_favorite?: boolean;
  topics?: string[];
  likes_count?: number;
  is_liked?: boolean;
  favorites_count: number;
  is_favorited: boolean;
  created_at: string;
  updated_at: string;
  items?: PlaylistItem[];
  items_count: number;
  animes_count?: number;
  genres?: string[];
  total_duration?: number;
  items_next?: string | null;
}

export interface Genre {
  id: number;
  name: string;
  slug: string;
}

export interface PlaylistItem {
  id: number;
  anime: number | unknown;
  anime_id: number;
  anime_title: string;
  anime_title_en?: string;
  anime_poster: string | null;
  anime_poster_url?: string;
  anime_year?: number;
  anime_score?: number;
  anime_status?: string;
  anime_kind?: string;
  anime_genres?: string[];
  anime_slug?: string;
  anime_episodes?: number;
  anime_episode_duration?: number;
  anime_total_duration?: number;
  episode_number: number | null;
  source_url: string;
  notes: string;
  position?: number;
  created_at: string;
  user_watch_progress?: {
    current_episode: number;
    episodes_watched: number;
    status: string;
    progress_percentage: number;
  } | null;
}

export interface FavoriteAnime {
  id: number;
  anime: number;
  anime_title: string;
  anime_poster: string | null;
  anime_data: AnimeData;
  created_at: string;
}

export interface FranchiseFavoriteState {
  franchise_id: number;
  anime_ids: number[];
  favorite_anime_ids: number[];
  is_favorite: boolean;
}

export interface FavoritePlaylist {
  id: number;
  playlist: string;
  playlist_data: PlaylistData;
  created_at: string;
}

export interface PlaylistData {
  id: string;
  title: string;
  description: string;
  is_public: boolean;
  user_id?: number;
  user_username: string;
  user_avatar: string | null;
  items_count: number;
  favorites_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface AnimeData {
  id: number;
  title_ru: string;
  title_en: string;
  poster_url: string;
  year: number | null;
  status: string;
  score: number | null;
}

export interface AddToPlaylistRequest {
  anime_id: number;
  playlist_id?: number;
  new_playlist_title?: string;
  episode_number?: number | null;
  source_url?: string;
  notes?: string;
}

export interface PlaylistsParams {
  page?: number;
  page_size?: number;
  my?: boolean;
  is_public?: boolean;
  favorites?: boolean;
  search?: string;
  genre?: number | string;
  year?: number | string;
  ordering?: string;
  period?: string;
  topics?: string;
  visibility?: PlaylistVisibility;
}

export interface PaginatedPlaylists {
  count: number;
  next: string | null;
  previous: string | null;
  results: Playlist[];
}

const playlistsApi = {
  discoveryOptions: (topicsOnly = false) => apiClient.get<{ topics: PlaylistTopic[]; genres: string[] }>("/playlists/playlists/discovery-options/", { params: topicsOnly ? { topics_only: true } : undefined }),
  setLike: (id: number | string, liked: boolean) =>
    apiClient.request<{ is_liked: boolean; likes_count: number }>({ url: `/playlists/playlists/${id}/like/`, method: liked ? 'PUT' : 'DELETE' }),
  getMyPlaylists: async (): Promise<AxiosResponse<Playlist[]>> => {
    const response = await apiClient.get<PaginatedPlaylists>("/playlists/playlists/my/", {
      params: { page: 1, page_size: 20 },
    });
    return { ...response, data: response.data.results };
  },

  getMyPlaylistsPage: (page = 1, pageSize = 20) =>
    apiClient.get<PaginatedPlaylists>("/playlists/playlists/my/", {
      params: { page, page_size: pageSize },
    }),

  getPublicPlaylists: (
    params?: PlaylistsParams,
  ): Promise<
    AxiosResponse<{
      results: Playlist[];
      count: number;
    }>
  > => {
    return apiClient.get<{ results: Playlist[]; count: number }>(
      "/playlists/playlists/public/",
      { params, headers: { "Cache-Control": "no-cache" } },
    );
  },

  getAllPlaylists: (
    params?: PlaylistsParams,
  ): Promise<
    AxiosResponse<{
      results: Playlist[];
      count: number;
    }>
  > => {
    return apiClient.get<{ results: Playlist[]; count: number }>(
      "/playlists/playlists/",
      { params, headers: { "Cache-Control": "no-cache" } },
    );
  },

  getPlaylist: (id: number | string, includeItems = false): Promise<AxiosResponse<Playlist>> => {
    return apiClient.get<Playlist>(`/playlists/playlists/${id}/`, {
      params: includeItems ? { include_items: true } : undefined,
    });
  },

  createPlaylist: (data: {
    title: string;
    description?: string;
    visibility?: PlaylistVisibility;
    topics?: string[];
    items?: PlaylistSelectionItem[];
  }): Promise<AxiosResponse<Playlist>> => {
    return apiClient.post<Playlist>("/playlists/playlists/", data).then((response) => {
      analyticsEvent("playlist_created", {
        visibility: data.visibility === "link" ? "unlisted" : (data.visibility || "private"),
      });
      return response;
    });
  },

  updateVisibility: (
    id: number | string,
    visibility: PlaylistVisibility,
  ): Promise<AxiosResponse<Playlist>> => {
    return apiClient.post<Playlist>(
      `/playlists/playlists/${id}/update-visibility/`,
      { visibility },
    );
  },

  generateShareLink: (
    id: number | string,
    ttlDays?: number,
  ): Promise<
    AxiosResponse<{
      token: string;
      expires_at: string;
      share_url: string;
    }>
  > => {
    return apiClient.post(`/playlists/playlists/${id}/share-link/`, {
      ttl_days: ttlDays ?? 30,
    });
  },

  revokeShareLink: (id: number | string): Promise<AxiosResponse<void>> => {
    return apiClient.delete(`/playlists/playlists/${id}/share-link/`);
  },

  getPlaylistByToken: (token: string, page = 1): Promise<AxiosResponse<Playlist>> => {
    return apiClient.get<Playlist>(`/playlists/playlists/shared/${token}/`, {
      params: { page, page_size: 24 },
    });
  },

  updatePlaylist: (
    id: number | string,
    data: Omit<Partial<Playlist>, "items"> & { items?: PlaylistSelectionItem[] },
  ): Promise<AxiosResponse<Playlist>> => {
    return apiClient.patch<Playlist>(`/playlists/playlists/${id}/`, data);
  },

  uploadPlaylistCover: (
    id: number | string,
    file: File,
  ): Promise<AxiosResponse<Playlist>> => {
    const formData = new FormData();
    formData.append("cover_image", file);
    return apiClient.post<Playlist>(
      `/playlists/playlists/${id}/update_cover/`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
  },

  deletePlaylist: (id: number | string): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>(`/playlists/playlists/${id}/`);
  },

  duplicatePlaylist: (id: number | string): Promise<AxiosResponse<Playlist>> => {
    return apiClient.post<Playlist>(`/playlists/playlists/${id}/duplicate/`);
  },

  updatePlaylistCover: (id: number | string): Promise<AxiosResponse<Playlist>> => {
    return apiClient.post<Playlist>(`/playlists/playlists/${id}/update_cover/`);
  },

  addToPlaylist: (
    data: AddToPlaylistRequest,
  ): Promise<
    AxiosResponse<{
      message: string;
      playlist_id: number;
      item_id: number;
    }>
  > => {
    return apiClient.post("/playlists/add-to-playlist/", data);
  },

  addItemToPlaylist: (
    playlistId: number | string,
    data: {
      anime: number;
      episode_number?: number | null;
      source_url?: string;
      notes?: string;
    },
  ): Promise<AxiosResponse<PlaylistItem>> => {
    const payload = {
      anime_id: data.anime,
      episode_number: data.episode_number,
      source_url: data.source_url,
      notes: data.notes,
    };
    return apiClient.post<PlaylistItem>(
      `/playlists/playlists/${playlistId}/add_item/`,
      payload,
    );
  },

  addItemByLink: (
    playlistId: number | string,
    data: {
      url: string;
      episode_number?: number | null;
      notes?: string;
    },
  ): Promise<AxiosResponse<PlaylistItem>> => {
    return apiClient.post<PlaylistItem>(
      `/playlists/playlists/${playlistId}/add_by_link/`,
      data,
    );
  },

  removeFromPlaylist: (
    playlistId: number | string,
    itemId: number,
  ): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>(
      `/playlists/playlists/${playlistId}/remove_item/`,
      {
        data: { item_id: itemId },
      },
    );
  },

  updatePlaylistItem: (
    playlistId: number | string,
    itemId: number,
    data: {
      notes?: string;
      position?: number;
    },
  ): Promise<AxiosResponse<PlaylistItem>> => {
    return apiClient.patch<PlaylistItem>(`/playlists/items/${itemId}/`, data);
  },

  updatePlaylistItemNotes: (
    playlistId: number | string,
    itemId: number,
    notes: string,
  ): Promise<AxiosResponse<PlaylistItem>> => {
    return apiClient.post<PlaylistItem>(
      `/playlists/playlists/${playlistId}/update-item-notes/`,
      {
        item_id: itemId,
        notes,
      },
    );
  },

  reorderPlaylistItems: (
    playlistId: number | string,
    items: Array<{ id: number; position: number }>,
  ): Promise<
    AxiosResponse<{
      message: string;
    }>
  > => {
    return apiClient.post<{ message: string }>(
      `/playlists/playlists/${playlistId}/reorder_items/`,
      { items },
    );
  },

  batchAddItems: (
    playlistId: number | string,
    data: { anime_ids: number[] },
  ): Promise<
    AxiosResponse<{
      added: unknown[];
      skipped: unknown[];
      added_count: number;
      skipped_count: number;
    }>
  > => {
    return apiClient.post(`/playlists/playlists/${playlistId}/batch-add-items/`, data);
  },

  getPlaylistItems: (
    playlistId: number | string,
    params?: { page?: number; page_size?: number; ordering?: string },
  ): Promise<
    AxiosResponse<{
      results: PlaylistItem[];
      count: number;
      next?: string | null;
      previous?: string | null;
    }>
  > => {
    return apiClient.get(`/playlists/playlists/${playlistId}/items/`, { params });
  },

  getFavoriteAnime: async (): Promise<AxiosResponse<FavoriteAnime[]>> => {
    const response = await apiClient.get<{ results: FavoriteAnime[] }>("/playlists/favorites/anime/", {
      params: { page: 1, page_size: 100 },
    });
    return { ...response, data: response.data.results };
  },

  checkAnimeInFavorites: (
    animeId: number,
  ): Promise<AxiosResponse<{ is_favorite: boolean }>> => {
    return apiClient.get<{ is_favorite: boolean }>(
      "/playlists/favorites/anime/check/",
      {
        params: { anime_id: animeId },
      },
    );
  },

  getFavoriteAnimeIds: (): Promise<AxiosResponse<{ anime_ids: number[] }>> => {
    return apiClient.get<{ anime_ids: number[] }>(
      "/playlists/favorites/anime/ids/",
    );
  },

  addToFavorites: (animeId: number): Promise<AxiosResponse<FavoriteAnime>> => {
    return apiClient.post<FavoriteAnime>("/playlists/favorites/anime/", {
      anime: animeId,
    });
  },

  removeFromFavorites: (animeId: number): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>("/playlists/favorites/anime/remove/", {
      data: { anime_id: animeId },
    });
  },

  setFranchiseFavorite: (
    franchiseId: number | string,
    isFavorite: boolean,
  ): Promise<AxiosResponse<FranchiseFavoriteState>> => {
    return apiClient.request<FranchiseFavoriteState>({
      url: `/playlists/favorites/anime/franchise/${franchiseId}/`,
      method: isFavorite ? "put" : "delete",
    });
  },

  getFavoritePlaylists: async (): Promise<AxiosResponse<FavoritePlaylist[]>> => {
    const response = await apiClient.get<{ results: FavoritePlaylist[] }>("/playlists/favorites/", {
      params: { page: 1, page_size: 100 },
    });
    return { ...response, data: response.data.results };
  },

  addPlaylistToFavorites: (
    playlistId: number | string,
  ): Promise<AxiosResponse<void>> => {
    return apiClient.post<void>(`/playlists/playlists/${playlistId}/favorite/`);
  },

  removePlaylistFromFavorites: (
    playlistId: number | string,
  ): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>(
      `/playlists/playlists/${playlistId}/unfavorite/`,
    );
  },
};

export default playlistsApi;
