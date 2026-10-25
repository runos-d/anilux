type Settings = { notifications?: boolean; notifications_enabled?: boolean; is_muted?: boolean; muted_until?: string | null };
export function chatNotificationsEnabled(row: { type?: string; chat_type?: string; user_settings?: Settings | null; user_member_settings?: Settings | null }): boolean {
  const settings = row.user_member_settings ?? row.user_settings;
  if (!settings) return true;
  return (settings.notifications_enabled ?? settings.notifications ?? true) && !settings.is_muted
    && (!settings.muted_until || new Date(settings.muted_until).getTime() <= Date.now());
}
