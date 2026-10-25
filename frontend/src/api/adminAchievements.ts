import apiClient from "./client";
import { collectionRows } from '@/lib/collectionRows';

export interface AdminAchievement {
  id: number;
  name: string;
  description: string;
  icon_url?: string;
  icon_svg?: string;
  category: string;
  level: "bronze" | "silver" | "gold" | "legendary";
  condition_type: string;
  condition_value: number;
  is_active: boolean;
  unlocked_count?: number;
}

export interface AdminAchievementPayload {
  name: string;
  description: string;
  icon_svg: string;
  category: string;
  level: string;
  condition_type: string;
  condition_value: number;
  is_active?: boolean;
}

export const ACHIEVEMENT_CATEGORIES = [
  { value: "basic", label: "Основные" },
  { value: "social", label: "Социальные" },
  { value: "collection", label: "Коллекционные" },
  { value: "contest", label: "Конкурсные" },
  { value: "special", label: "Специальные" },
];

export const ACHIEVEMENT_LEVELS = [
  { value: "bronze", label: "Бронзовый" },
  { value: "silver", label: "Серебряный" },
  { value: "gold", label: "Золотой" },
  { value: "legendary", label: "Легендарный" },
];

const adminAchievementsApi = {
  list: async () => {
    const { data } = await apiClient.get<AdminAchievement[] | { results: AdminAchievement[] }>(
      "/social/admin/achievements/",
    );
    return collectionRows(data);
  },

  conditionTypes: async (): Promise<Record<string, string>> => {
    const { data } = await apiClient.get(
      "/social/admin/achievements/condition_types/",
    );
    return data;
  },

  create: (payload: AdminAchievementPayload) => {
    return apiClient.post<AdminAchievement>(
      "/social/admin/achievements/",
      payload,
    );
  },

  update: (id: number, payload: Partial<AdminAchievementPayload>) => {
    return apiClient.patch<AdminAchievement>(
      `/social/admin/achievements/${id}/`,
      payload,
    );
  },

  remove: (id: number) => {
    return apiClient.delete(`/social/admin/achievements/${id}/`);
  },

  toggleActive: (id: number) => {
    return apiClient.post(`/social/admin/achievements/${id}/toggle_active/`);
  },
};

export default adminAchievementsApi;
