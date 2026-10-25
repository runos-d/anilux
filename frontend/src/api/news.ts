import apiClient from "./client";

export interface NewsPost {
  id: number;
  author_id: number;
  author_username: string;
  author_display_name: string | null;
  author_avatar: string | null;
  title: string;
  summary: string;
  content: string;
  cover_url: string;
  cover_file: string | null;
  cover_url_final: string | null;
  priority: "low" | "important" | "hot";
  priority_display: string;
  is_pinned: boolean;
  is_published: boolean;
  views_count: number;
  created_at: string;
  updated_at: string;
}

export interface NewsPostForm {
  title: string;
  summary: string;
  content: string;
  cover_url: string;
  priority: "low" | "important" | "hot";
  is_pinned: boolean;
  is_published: boolean;
  cover_file?: File | null;
}

export const newsApi = {
  getNews: () => apiClient.get<NewsPost[]>("/social/news/"),

  getNewsItem: (id: number) => apiClient.get<NewsPost>(`/social/news/${id}/`),

  createNews: (data: NewsPostForm) => {
    if (data.cover_file) {
      const formData = new FormData();
      formData.append("title", data.title);
      formData.append("summary", data.summary);
      formData.append("content", data.content);
      formData.append("priority", data.priority);
      formData.append("is_pinned", String(data.is_pinned));
      formData.append("is_published", String(data.is_published));
      if (data.cover_url) formData.append("cover_url", data.cover_url);
      formData.append("cover_file", data.cover_file);
      return apiClient.post<NewsPost>("/social/news/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    }
    return apiClient.post<NewsPost>("/social/news/", data);
  },

  updateNews: (id: number, data: Partial<NewsPostForm>) => {
    if (data.cover_file) {
      const formData = new FormData();
      if (data.title !== undefined) formData.append("title", data.title);
      if (data.summary !== undefined) formData.append("summary", data.summary);
      if (data.content !== undefined) formData.append("content", data.content);
      if (data.priority !== undefined) formData.append("priority", data.priority);
      if (data.is_pinned !== undefined) formData.append("is_pinned", String(data.is_pinned));
      if (data.is_published !== undefined) formData.append("is_published", String(data.is_published));
      if (data.cover_url !== undefined) formData.append("cover_url", data.cover_url);
      formData.append("cover_file", data.cover_file);
      return apiClient.patch<NewsPost>(`/social/news/${id}/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    }
    return apiClient.patch<NewsPost>(`/social/news/${id}/`, data);
  },

  deleteNews: (id: number) => apiClient.delete(`/social/news/${id}/`),

  registerView: (id: number) =>
    apiClient.post<{ views_count: number }>(`/social/news/${id}/view/`),
};