import apiClient from "@/api/client";

export type IdeaKind = "idea" | "bug" | "improvement";
export type IdeaStatus = "pending" | "planned" | "in_progress" | "review" | "done" | "declined";
export type IdeaPriority = "low" | "normal" | "high" | "critical";

export interface Idea {
  id: number;
  title: string;
  description: string;
  kind: IdeaKind;
  status: IdeaStatus;
  priority: IdeaPriority;
  admin_note: string;
  votes_count: number;
  author: number;
  author_name: string;
  author_avatar: string | null;
  is_voted: boolean;
  is_owner: boolean;
  created_at: string;
  updated_at: string;
}

interface IdeaPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: Idea[];
}

export interface CreateIdeaPayload {
  title: string;
  description: string;
  kind: IdeaKind;
}

export type UpdateIdeaPayload = Partial<Pick<Idea, "title" | "description" | "kind" | "status" | "priority" | "admin_note">>;

export const ideasApi = {
  async list(): Promise<Idea[]> {
    const { data } = await apiClient.get<IdeaPage | Idea[]>("/ideas/", {
      params: { page_size: 100, ordering: "-created_at" },
    });
    return Array.isArray(data) ? data : data.results;
  },
  async create(payload: CreateIdeaPayload): Promise<Idea> {
    const { data } = await apiClient.post<Idea>("/ideas/", payload);
    return data;
  },
  async update(id: number, payload: UpdateIdeaPayload): Promise<Idea> {
    const { data } = await apiClient.patch<Idea>(`/ideas/${id}/`, payload);
    return data;
  },
  async remove(id: number): Promise<void> {
    await apiClient.delete(`/ideas/${id}/`);
  },
  async vote(id: number): Promise<{ is_voted: boolean; votes_count: number }> {
    const { data } = await apiClient.post<{ is_voted: boolean; votes_count: number }>(`/ideas/${id}/vote/`);
    return data;
  },
};
