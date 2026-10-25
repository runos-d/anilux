import apiClient from "./client";
import type { AxiosResponse } from "axios";

export interface ReactorPost {
  id: number;
  content: string;
  content_type: string;
  created_at: string;
}

export interface ReactorCard {
  id: number;
  content_type: "anime" | "playlist" | "shorts";
  text?: string | null;
  image?: string | null;
  video?: string | null;
  playlist?: Record<string, unknown> | null;
  anime?: Record<string, unknown> | null;
  reactor_post?: ReactorPost | null;
}

const reactorApi = {
  getPosts: (params?: { page?: number; page_size?: number }): Promise<AxiosResponse<{ results: ReactorPost[]; count: number }>> =>
    apiClient.get("/reactor/posts/", { params }),

  getPost: (id: number | string): Promise<AxiosResponse<ReactorPost>> =>
    apiClient.get(`/reactor/posts/${id}/`),

  createPost: (data: { content: string; content_type?: string }): Promise<AxiosResponse<ReactorPost>> =>
    apiClient.post("/reactor/posts/", data),
};

export default reactorApi;
