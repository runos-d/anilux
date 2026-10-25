import apiClient from "./client";
import type { AxiosResponse } from "axios";

export interface Reminder {
  id: number;
  anime: number | null;
  franchise?: number | null;
  anime_detail: {
    id: number | null;
    slug?: string;
    title_ru: string;
    title_en: string;
    poster_url: string | null;
    year: number | null;
    status: string;
    score: number | null;
    target_type?: "anime" | "franchise";
  };
  reminder_time: string;
  repeat_weekly: boolean;
  comment: string;
  enable_sound: boolean;
  enable_push: boolean;
  is_active: boolean;
  is_triggered: boolean;
  created_at: string;
}

export interface ReminderCreateData {
  anime_id?: number;
  franchise_id?: number;
  calendar_release_id?: number;
  follow_schedule?: boolean;
  reminder_time?: string;
  timezone_name?: string;
  repeat_weekly?: boolean;
  repeat_interval_days?: number;
  end_date?: string;
  comment?: string;
  enable_sound?: boolean;
  enable_push?: boolean;
}

const remindersApi = {
  getReminders: (): Promise<AxiosResponse<Reminder[]>> => {
    return apiClient.get<Reminder[]>("/notifications/reminders/");
  },

  getUpcomingReminders: (): Promise<AxiosResponse<Reminder[]>> => {
    return apiClient.get<Reminder[]>("/notifications/reminders/upcoming/");
  },

  createReminder: (
    data: ReminderCreateData,
  ): Promise<AxiosResponse<Reminder>> => {
    return apiClient.post<Reminder>("/notifications/reminders/", {
      timezone_name: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC', ...data,
    });
  },

  deleteReminder: (id: number): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>(`/notifications/reminders/${id}/`);
  },

  deactivateReminder: (
    id: number,
  ): Promise<AxiosResponse<{ status: string }>> => {
    return apiClient.post(`/notifications/reminders/${id}/deactivate/`);
  },
};

export default remindersApi;
