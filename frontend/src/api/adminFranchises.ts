import apiClient from "./client";

export interface AdminFranchiseSummary {
  id: number;
  name: string;
  slug?: string;
  description?: string;
  score?: number | null;
  year_start?: number | null;
  year_end?: number | null;
  genres?: string[];
  cover?: string;
  parts_count?: number;
}

export interface AdminFranchiseEntry {
  id: number;
  title_ru: string;
  title_en?: string;
  slug?: string;
  year?: number;
  kind?: string;
  status?: string;
  episodes?: number;
  score?: number | null;
  poster_url?: string;
  franchise_order?: number;
}

export interface AdminFranchiseDetail extends AdminFranchiseSummary {
  entries: AdminFranchiseEntry[];
}

export interface AdminFranchiseListResponse {
  count: number;
  page: number;
  page_size: number;
  results: AdminFranchiseSummary[];
}

export interface AdminAnimeSearchResult {
  id: number;
  title_ru: string;
  title_en?: string;
  year?: number;
  kind?: string;
  status?: string;
  score?: number | null;
  poster_url?: string;
  franchise?: { id: number; name: string } | null;
}

export interface AdminAnimeSearchResponse {
  results: AdminAnimeSearchResult[];
}

const adminFranchisesApi = {
  list: (params: { search?: string; page?: number; page_size?: number }) => {
    return apiClient.get<AdminFranchiseListResponse>("/anime/admin/franchises/", {
      params,
    });
  },

  create: (data: { name: string; description?: string }) => {
    return apiClient.post<AdminFranchiseSummary>("/anime/admin/franchises/", data);
  },

  detail: (id: number) => {
    return apiClient.get<AdminFranchiseDetail>(`/anime/admin/franchises/${id}/`);
  },

  update: (id: number, data: { name?: string; description?: string }) => {
    return apiClient.patch<AdminFranchiseSummary>(
      `/anime/admin/franchises/${id}/`,
      data,
    );
  },

  remove: (id: number) => {
    return apiClient.delete(`/anime/admin/franchises/${id}/`);
  },

  rebuild: () => {
    return apiClient.post<{
      queued: boolean;
      task_id: string;
      rebuild_id?: string;
      anime_scheduled: number;
      single_links_removed: number;
    }>("/anime/admin/franchises/rebuild/");
  },

  rebuildStatus: (rebuildId: string) => {
    return apiClient.get<{
      state: "queued" | "running" | "completed" | "failed";
      total: number;
      processed: number;
      remaining: number;
      message: string;
      rebuild_id?: string;
    }>(`/anime/admin/franchises/rebuild-status/${rebuildId}/`);
  },

  addAnime: (id: number, animeId: number) => {
    return apiClient.post<AdminFranchiseDetail>(
      `/anime/admin/franchises/${id}/add-anime/`,
      { anime_id: animeId },
    );
  },

  removeAnime: (id: number, animeId: number) => {
    return apiClient.post<AdminFranchiseDetail>(
      `/anime/admin/franchises/${id}/remove-anime/`,
      { anime_id: animeId },
    );
  },

  reorder: (id: number, animeIds: number[]) => {
    return apiClient.post<AdminFranchiseDetail>(
      `/anime/admin/franchises/${id}/reorder/`,
      { anime_ids: animeIds },
    );
  },

  searchAnime: (q: string) => {
    return apiClient.get<AdminAnimeSearchResponse>("/anime/admin/anime-search/", {
      params: { q },
    });
  },
};

export default adminFranchisesApi;
