import client from "./client";

export interface UserBasicData {
  display_name?: string;
  nickname?: string;
  bio?: string;
  favorite_genres?: string[];
  website?: string;
  vk_profile?: string;
  telegram?: string;
}

export interface ProfileSettingsData {
  theme?: "light" | "dark" | "system" | "blue" | "green" | "red" | "yellow" | "banana" | "sea" | "lilac" | "emerald" | "peach" | "blueberry" | "rozovaya" | "polnochnaya" | "custom";
  accent_color?: string;
  language?: "ru" | "en" | "uk" | "be" | "kk";
  timezone?: string;
  date_format?: "DD.MM.YYYY" | "MM/DD/YYYY" | "YYYY-MM-DD";
  time_format?: "24h" | "12h";

}

export interface NotificationSettingsData {
  enabled?: boolean;
  sound_enabled?: boolean;
  vibration_enabled?: boolean;
  preview_enabled?: boolean;
  message_notifications?: boolean;
  group_notifications?: boolean;
  call_notifications?: boolean;
  mention_notifications?: boolean;
  reaction_notifications?: boolean;
  push_enabled?: boolean;
  push_sound_enabled?: boolean;
  push_vibration_enabled?: boolean;
  push_preview_enabled?: boolean;
  email_enabled?: boolean;
  email_frequency?: "immediately" | "hourly" | "daily" | "weekly";
  do_not_disturb_enabled?: boolean;
  do_not_disturb_start?: string;
  do_not_disturb_end?: string;
  mute_until?: string;
  override_chat_settings?: boolean;
}

export interface PrivacySettingsData {
  show_online_status?: boolean;
  show_last_seen?: boolean;
  show_typing_status?: boolean;
  allow_calls?: boolean;
  allow_group_invites?: boolean;
  who_can_add_to_groups?: "everyone" | "contacts" | "nobody";
  who_can_see_phone?: "everyone" | "contacts" | "nobody";
  who_can_see_email?: "everyone" | "contacts" | "nobody";
  who_can_see_profile_photo?: "everyone" | "contacts" | "nobody";
  who_can_call?: "everyone" | "contacts" | "nobody";
  who_can_see_last_seen?: "everyone" | "contacts" | "nobody";
  allow_message_forwarding?: boolean;
  sync_contacts?: boolean;
  suggest_frequent_contacts?: boolean;
  blocked_users?: number[];
  background_type?: string;
  solid_color?: string;
  gradient_colors?: Record<string, string>;
  custom_image?: string;
  background_effects?: Record<string, unknown>;
}

export interface TwoFactorSettingsData {
  is_enabled?: boolean;
  require_on_new_device?: boolean;
  remember_device_days?: number;
  email_enabled?: boolean;
  phone_number?: string;
  backup_codes_count?: number;
}

export interface ChangePasswordData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface AllSettingsResponse {
  user: {
    display_name: string;
    nickname: string;
    avatar: string | null;
    bio: string;
    favorite_genres: string[];
    website: string;
    vk_profile: string;
    telegram: string;
    phone_number: string;
    email: string;
    email_verified: boolean;
    phone_verified: boolean;
  };
  profile_settings: ProfileSettingsData;
  notification_settings: NotificationSettingsData;
  privacy_settings: PrivacySettingsData;
  two_factor_settings: TwoFactorSettingsData;
}

export interface UpdateSettingsRequest {
  user?: UserBasicData;
  profile_settings?: ProfileSettingsData;
  notification_settings?: NotificationSettingsData;
  privacy_settings?: PrivacySettingsData;
  two_factor_settings?: TwoFactorSettingsData;
}

export const getAllSettings = async (): Promise<AllSettingsResponse> => {
  const response = await client.get("/users/settings/all/");
  return response.data;
};

export const updateSettings = async (
  data: UpdateSettingsRequest,
): Promise<AllSettingsResponse> => {
  const response = await client.put("/users/settings/all/", data);
  return response.data;
};

export const clearSettingsCache = async (): Promise<{ message: string }> => {
  const response = await client.post("/users/settings/cache/clear/");
  return response.data;
};

export const uploadAvatar = async (
  file: File,
): Promise<{ success: boolean; avatar_url: string | null }> => {
  const formData = new FormData();
  formData.append("avatar", file);

  const response = await client.post("/users/avatar/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const deleteAvatar = async (): Promise<{ success: boolean }> => {
  const response = await client.delete("/users/avatar/");
  return response.data;
};

export const getProfileSettings = async (): Promise<ProfileSettingsData> => {
  const response = await client.get("/users/profile-settings/");
  return response.data;
};

export const updateProfileSettings = async (
  data: ProfileSettingsData,
): Promise<ProfileSettingsData> => {
  const response = await client.put("/users/profile-settings/", data);
  return response.data;
};

export const getNotificationSettings =
  async (): Promise<NotificationSettingsData> => {
    const response = await client.get("/users/notification-settings/");
    return response.data;
  };

export const updateNotificationSettings = async (
  data: NotificationSettingsData,
): Promise<NotificationSettingsData> => {
  const response = await client.put("/users/notification-settings/", data);
  return response.data;
};

export const getPrivacySettings = async (): Promise<PrivacySettingsData> => {
  const response = await client.get("/users/privacy-settings/");
  return response.data;
};

export const updatePrivacySettings = async (
  data: PrivacySettingsData,
): Promise<PrivacySettingsData> => {
  const response = await client.put("/users/privacy-settings/", data);
  return response.data;
};

export const blockUser = async (
  userId: number,
): Promise<{ success: boolean }> => {
  const response = await client.post("/users/privacy-settings/block_user/", {
    user_id: userId,
  });
  return response.data;
};

export const unblockUser = async (
  userId: number,
): Promise<{ success: boolean }> => {
  const response = await client.post("/users/privacy-settings/unblock_user/", {
    user_id: userId,
  });
  return response.data;
};

import type { User } from "./users";

export interface BlockedUser extends User {
  blocked_at: string;
}

export const getBlockedUsers = async (): Promise<BlockedUser[]> => {
  const response = await client.get("/users/privacy-settings/blocked_users/");
  return response.data.results || response.data;
};

export const getTwoFactorStatus = async () => {
  const response = await client.get("/users/2fa/status/");
  return response.data;
};

export const enableTwoFactor = async () => {
  const response = await client.post("/users/2fa/enable/");
  return response.data;
};

export const verifyTwoFactor = async (code: string) => {
  const response = await client.post("/users/2fa/verify/", { code });
  return response.data;
};

export const verifyBackupCode = async (code: string) => {
  const response = await client.post("/users/2fa/verify-backup/", { code });
  return response.data;
};

export const getBackupCodes = async () => {
  const response = await client.get("/users/2fa/backup-codes/");
  return response.data;
};

export const regenerateBackupCodes = async (password: string) => {
  const response = await client.post("/users/2fa/backup-codes/", { password });
  return response.data;
};

export const updateTwoFactorSettings = async (data: TwoFactorSettingsData) => {
  const response = await client.post("/users/2fa/settings/", data);
  return response.data;
};

export const getTwoFactorSecurityLog = async () => {
  const response = await client.get("/users/2fa/security-log/");
  return response.data;
};

export const disableTwoFactor = async (password: string) => {
  const response = await client.post("/users/2fa/disable/", { password });
  return response.data;
};

export const getThemeSettings = async () => {
  const response = await client.get("/users/theme-settings/");
  return response.data;
};

export const updateThemeSettings = async (data: unknown) => {
  const response = await client.put("/users/theme-settings/", data);
  return response.data;
};

export const getChatBackgroundSettings = async () => {
  const response = await client.get("/users/chat-background-settings/");
  return response.data;
};

export const updateChatBackgroundSettings = async (data: unknown) => {
  const response = await client.put("/users/chat-background-settings/", data);
  return response.data;
};

export const uploadChatBackground = async (file: File, name?: string) => {
  const formData = new FormData();
  formData.append("background_image", file);
  if (name) {
    formData.append("name", name);
  }

  const response = await client.post(
    "/users/chat-background-settings/",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );
  return response.data;
};

export const deleteChatBackground = async () => {
  const response = await client.delete("/users/chat-background-settings/");
  return response.data;
};

export const getFontSettings = async () => {
  const response = await client.get("/users/font-settings/");
  return response.data;
};

export const updateFontSettings = async (data: unknown) => {
  const response = await client.put("/users/font-settings/", data);
  return response.data;
};

export const getStorageUsage = async () => {
  const response = await client.get("/users/storage-usage/");
  return response.data;
};

export const getSyncSettings = async () => {
  const response = await client.get("/users/sync-settings/");
  return response.data;
};

export const updateSyncSettings = async (data: unknown) => {
  const response = await client.put("/users/sync-settings/", data);
  return response.data;
};

export const startSync = async () => {
  const response = await client.post("/users/sync-settings/");
  return response.data;
};

export const getDataExports = async () => {
  const response = await client.get("/users/export-data/");
  return response.data;
};

export const requestExportData = async (data: {
  items: string[];
  format: string;
}) => {
  const response = await client.post("/users/export-data/", data);
  return response.data;
};

export const downloadExportData = async (exportId: number) => {
  const response = await client.get(
    `/users/export-data/${exportId}/download/`,
    {
      responseType: "blob",
    },
  );
  return response.data;
};

export const clearCache = async (items: string[]) => {
  const response = await client.post("/users/clear-cache/", { items });
  return response.data;
};

export const resetSettings = async () => {
  const response = await client.post("/users/reset-settings/");
  return response.data;
};

export const changePassword = async (data: ChangePasswordData) => {
  const response = await client.post("/users/change-password/", data);
  return response.data;
};

export const getAccountStats = async () => {
  const response = await client.get("/users/account-deletion/");
  return response.data;
};

export const scheduleAccountDeletion = async (data: {
  password?: string;
  two_factor_code?: string;
  reasons: string[];
  alternative?: string;
  other_reason?: string;
  final_confirmation: boolean;
}) => {
  const response = await client.post("/users/account-deletion/", data);
  return response.data;
};

export const cancelAccountDeletion = async () => {
  const response = await client.delete("/users/cancel-deletion/");
  return response.data;
};

export const getActiveSessions = async () => {
  const response = await client.get("/users/sessions/active/");
  return response.data;
};

export const terminateSession = async (sessionKey: string) => {
  const response = await client.post("/users/sessions/terminate/", {
    session_key: sessionKey,
  });
  return response.data;
};

export const terminateAllOtherSessions = async () => {
  const response = await client.post("/users/sessions/terminate-all/");
  return response.data;
};

export default {
  getAllSettings,
  updateSettings,
  clearSettingsCache,
  uploadAvatar,
  deleteAvatar,
  getProfileSettings,
  updateProfileSettings,
  getNotificationSettings,
  updateNotificationSettings,
  getPrivacySettings,
  updatePrivacySettings,
  blockUser,
  unblockUser,
  getBlockedUsers,
  getTwoFactorStatus,
  enableTwoFactor,
  verifyTwoFactor,
  verifyBackupCode,
  getBackupCodes,
  regenerateBackupCodes,
  updateTwoFactorSettings,
  getTwoFactorSecurityLog,
  disableTwoFactor,
  changePassword,
  getThemeSettings,
  updateThemeSettings,
  getChatBackgroundSettings,
  updateChatBackgroundSettings,
  uploadChatBackground,
  deleteChatBackground,
  getFontSettings,
  updateFontSettings,
  getStorageUsage,
  getSyncSettings,
  updateSyncSettings,
  startSync,
  getDataExports,
  requestExportData,
  downloadExportData,
  clearCache,
  resetSettings,
  getAccountStats,
  scheduleAccountDeletion,
  cancelAccountDeletion,
  getActiveSessions,
  terminateSession,
  terminateAllOtherSessions,
};

export interface PaymentCreateResponse {
  success: boolean;
  payment_url?: string;
  invoice_id?: string;
  invoice_uuid?: string;
  order_id?: string;
  amount?: number;
  amount_usd?: number;
  currency?: string;
  payment_method?: string;
  error?: string;
}

export interface PaymentPriceResponse {
  base_price: number;
  final_price: number;
  discount: number;
  currency: string;
}

export interface PaymentCheckResponse {
  success: boolean;
  status?: string;
  subscription_activated?: boolean;
  error?: string;
}

export const createPayment = async (
  promoCode?: string,
): Promise<PaymentCreateResponse> => {
  const response = await client.post("/users/payment/create/", {
    promo_code: promoCode || "",
  });
  return response.data;
};

export const getPaymentPrice = async (
  promoCode?: string,
): Promise<PaymentPriceResponse> => {
  const response = await client.get("/users/payment/price/", {
    params: promoCode ? { promo: promoCode } : {},
  });
  return response.data;
};

export const checkPayment = async (
  invoiceUuid: string,
): Promise<PaymentCheckResponse> => {
  const response = await client.post("/users/payment/check/", {
    invoice_uuid: invoiceUuid,
  });
  return response.data;
};
