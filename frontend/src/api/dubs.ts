import apiClient from "./client";
import type { AxiosResponse } from "axios";

export interface Dub {
  id: number;
  title: string;
  slug: string;
}

export interface DubGroup {
  slug: string;
  title: string;
  works: Dub[];
}

export interface DubStaffMember {
  id: number;
  name: string;
  role?: string | null;
  avatar?: string | null;
}

export interface DubReview {
  id: number;
  content: string;
  author_name: string;
  created_at: string;
}

export interface DubDiscussion {
  id: number;
  content: string;
  author_name: string;
  created_at: string;
}

const dubsApi = {
  getAnimeDubs: (animeId: string): Promise<AxiosResponse<Dub[]>> =>
    apiClient.get(`/dubs/anime/${animeId}/dubs/`),

  getAnimeDubGroups: (animeId: string): Promise<AxiosResponse<DubGroup[]>> =>
    apiClient.get(`/dubs/anime/${animeId}/groups/`),

  getDubDetail: (dubId: string): Promise<AxiosResponse<Dub>> =>
    apiClient.get(`/dubs/dubs/${dubId}/`),

  getPopularDubGroups: (): Promise<AxiosResponse<DubGroup[]>> =>
    apiClient.get(`/dubs/groups/popular/`),

  getDubGroupWorks: (slug: string): Promise<AxiosResponse<Dub[]>> =>
    apiClient.get(`/dubs/groups/${slug}/works/`),

  getDubGroupStaff: (slug: string): Promise<AxiosResponse<DubStaffMember[]>> =>
    apiClient.get(`/dubs/groups/${slug}/staff/`),

  getDubGroupReviews: (slug: string): Promise<AxiosResponse<DubReview[]>> =>
    apiClient.get(`/dubs/groups/${slug}/reviews/`),

  createDubReview: (slug: string, data: { content: string }): Promise<AxiosResponse<DubReview>> =>
    apiClient.post(`/dubs/groups/${slug}/reviews/create/`, data),

  getDubGroupDiscussions: (slug: string): Promise<AxiosResponse<DubDiscussion[]>> =>
    apiClient.get(`/dubs/groups/${slug}/discussions/`),

  createDubDiscussion: (slug: string, data: { content: string }): Promise<AxiosResponse<DubDiscussion>> =>
    apiClient.post(`/dubs/groups/${slug}/discussions/create/`, data),
};

export default dubsApi;
