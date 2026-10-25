import { ref, computed } from "vue";
import { defineStore } from "pinia";
import { useAuthStore } from '@/stores/auth';
import { queryClient } from '@/lib/queryClient';
import notificationsApi from "@/api/notifications";
import apiClient, { isRequestCancelled } from '@/api/client';
import type {
  NotificationItem,
  NotificationSettings,
} from "@/api/notifications";

export type { NotificationItem, NotificationItem as Notification };

export interface Reminder {
  id: number;
  anime: number | null;
  franchise?: number | null;
  anime_detail: {
    id: number | null;
    title_ru: string;
    title_en: string;
    poster: string | null;
    poster_url?: string;
    slug?: string;
    target_type?: "anime" | "franchise";
  };
  reminder_time: string;
  calendar_release?: number | null;
  follow_schedule?: boolean;
  available_notified_at?: string | null;
  repeat_interval_days?: number | null;
  end_date?: string | null;
  repeat_weekly: boolean;
  comment: string;
  enable_sound: boolean;
  enable_push: boolean;
  is_active: boolean;
  is_triggered: boolean;
  created_at: string;
}

interface GroupedNotificationItem extends NotificationItem {
  _groupCount?: number;
  _groupItems?: NotificationItem[];
}

export const useNotificationStore = defineStore("notifications", () => {
  const auth = useAuthStore();
  let generation = 0;
  const notifications = ref<NotificationItem[]>([]);
  const recentNotifications = ref<NotificationItem[]>([]);
  const reminders = ref<Reminder[]>([]);
  const unreadCount = ref(0);
  const flashingCount = ref(0);
  const loading = ref(false);
  const loadingMore = ref(false);
  const hasMore = ref(true);
  const currentPage = ref(1);
  const settings = ref<NotificationSettings | null>(null);

  const recentNotificationsLastLoadedAt = ref<number | null>(null);
  const unreadCountLastLoadedAt = ref<number | null>(null);
  const recentNotificationsLoadingPromise = ref<Promise<unknown> | null>(null);
  const unreadCountLoadingPromise = ref<Promise<unknown> | null>(null);

  const NOTIFICATIONS_DEDUPE_MS = 15000;

  const ringingReminderIds = ref<number[]>([]);

  const isBellRinging = computed(() => {
    if (flashingCount.value > 0) return true;
    if (ringingReminderIds.value.length > 0) return true;
    return false;
  });

  const _ringTimers = new Map<number, ReturnType<typeof setTimeout>>();

  function startRinging(reminderId: number) {
    if (!ringingReminderIds.value.includes(reminderId)) {
      ringingReminderIds.value = [...ringingReminderIds.value, reminderId];
    }

    const t = setTimeout(() => {
      stopRinging(reminderId);
    }, 60_000);
    _ringTimers.set(reminderId, t);
  }

  function stopRinging(reminderId: number) {
    const t = _ringTimers.get(reminderId);
    if (t) {
      clearTimeout(t);
      _ringTimers.delete(reminderId);
    }
    ringingReminderIds.value = ringingReminderIds.value.filter(
      (id) => id !== reminderId,
    );
  }

  function isReminderRinging(reminderId: number): boolean {
    return ringingReminderIds.value.includes(reminderId);
  }


  const hasUnread = computed(() => unreadCount.value > 0);

  const GROUP_WINDOW_MS = 5 * 60 * 1000;

  function getGroupKey(n: NotificationItem): string | null {
    if (n.type === "message" || n.type === "group_message") {
      const match = n.link.match(/\/chats\/(\d+)/);
      if (match) return `chat:${match[1]}`;
    }
    if (n.type === "mention") {
      const match = n.link.match(/\/posts\/(\d+)/);
      if (match) return `mention:post:${match[1]}`;
    }
    return null;
  }

  async function fetchNotifications(reset = true) {
    const current = generation;
    const scope = String(auth.user?.id ?? 'guest');
    if (reset) {
      loading.value = !notifications.value.length;
      currentPage.value = 1;
      hasMore.value = true;
    } else {
      loadingMore.value = true;
    }

    try {
      const page = currentPage.value;
      const data = await queryClient.fetchQuery({ queryKey: ['read', scope, 'notifications', page],
        queryFn: async () => (await notificationsApi.list({ page, page_size: 20 })).data, staleTime: 0 });
      if (current !== generation || scope !== String(auth.user?.id ?? 'guest')) return;

      const list: NotificationItem[] = Array.isArray(data)
        ? data
        : ((data as { results?: NotificationItem[] }).results ?? []);

      if (reset) {
        notifications.value = list;
      } else {
        const existing = new Set(notifications.value.map((n) => n.id));
        notifications.value = [
          ...notifications.value,
          ...list.filter((n) => !existing.has(n.id)),
        ];
      }

      const pageData = data as { next?: unknown };
      hasMore.value = !!pageData.next;

      void fetchCount();
      flashingCount.value = notifications.value.filter(
        (n) => (n as { is_flashing?: boolean }).is_flashing,
      ).length;
    } catch (_e) {
      if (current === generation && !isRequestCancelled(_e)) console.error("Error fetching notifications:", _e);
    } finally {
      loading.value = false;
      loadingMore.value = false;
    }
  }

  async function fetchRecent(force = false) {
    const current = generation;
    const now = Date.now();
    if (!force && recentNotificationsLoadingPromise.value) {
      return recentNotificationsLoadingPromise.value;
    }

    if (
      !force &&
      recentNotificationsLastLoadedAt.value &&
      now - recentNotificationsLastLoadedAt.value < NOTIFICATIONS_DEDUPE_MS
    ) {
      return Promise.resolve(recentNotifications.value);
    }

    recentNotificationsLoadingPromise.value = (async () => {
      try {
        const { data } = await notificationsApi.recent();
        if (current !== generation) return [];
        unreadCount.value = data.unread_count;
        flashingCount.value = data.flashing_count || 0;
        recentNotifications.value = data.results.slice(0, 5);
        const existing = new Set(notifications.value.map((n) => n.id));
        const fresh = data.results.filter((n) => !existing.has(n.id));
        if (fresh.length) {
          notifications.value = [...fresh, ...notifications.value];
        }
        recentNotificationsLastLoadedAt.value = Date.now();
        return data.results;
      } catch {
        return [];
      } finally {
        recentNotificationsLoadingPromise.value = null;
      }
    })();

    return recentNotificationsLoadingPromise.value;
  }

  async function fetchCount(force = false) {
    const current = generation;
    const now = Date.now();
    if (!force && unreadCountLoadingPromise.value) {
      return unreadCountLoadingPromise.value;
    }

    if (
      !force &&
      unreadCountLastLoadedAt.value &&
      now - unreadCountLastLoadedAt.value < NOTIFICATIONS_DEDUPE_MS
    ) {
      return Promise.resolve({
        count: unreadCount.value,
        flashing_count: flashingCount.value,
      });
    }

    unreadCountLoadingPromise.value = (async () => {
      try {
        const { data } = await notificationsApi.count();
        if (current !== generation) return;
        unreadCount.value = data.count;
        flashingCount.value = data.flashing_count || 0;
        unreadCountLastLoadedAt.value = Date.now();
        return data;
      } catch {
        return { count: unreadCount.value, flashing_count: flashingCount.value };
      } finally {
        unreadCountLoadingPromise.value = null;
      }
    })();

    return unreadCountLoadingPromise.value;
  }

  async function loadMoreNotifications() {
    if (loadingMore.value || !hasMore.value) return;
    currentPage.value++;
    await fetchNotifications(false);
  }

  async function markRead(id: number) {
    const current = generation;
    const targets = [
      notifications.value.find((n) => n.id === id),
      recentNotifications.value.find((n) => n.id === id),
    ].filter((n): n is NotificationItem => Boolean(n));
    if (!targets.length || targets.every((n) => n.is_read)) return;
    const unreadTargets = targets.filter((n) => !n.is_read);
    const wasFlashing = unreadTargets.some((n) => (n as { is_flashing?: boolean }).is_flashing);
    unreadTargets.forEach((n) => {
      n.is_read = true;
      (n as { is_flashing?: boolean }).is_flashing = false;
    });
    unreadCount.value = Math.max(0, unreadCount.value - 1);
    if (wasFlashing) flashingCount.value = Math.max(0, flashingCount.value - 1);
    try {
      await notificationsApi.markRead(id);
      if (current !== generation) return;
    } catch (_e) {
      if (current === generation) {
        unreadTargets.forEach((n) => { n.is_read = false; });
        unreadCount.value++;
        if (wasFlashing) flashingCount.value++;
      }
      console.error("markRead error:", _e);
    }
  }

  async function markAllRead() {
    const current = generation;
    try {
      await notificationsApi.markAllRead();
      if (current !== generation) return;
      notifications.value.forEach((n) => {
        n.is_read = true;
        (n as { is_flashing?: boolean }).is_flashing = false;
      });
      recentNotifications.value.forEach((n) => {
        n.is_read = true;
        (n as { is_flashing?: boolean }).is_flashing = false;
      });
      unreadCount.value = 0;
      flashingCount.value = 0;
    } catch (e) {
      console.error("markAllRead error:", e);
    }
  }

  async function toggleImportant(id: number) {
    const current = generation;
    const n = notifications.value.find((n) => n.id === id);
    if (!n) return;
    try {
      const { data } = await notificationsApi.toggleImportant(id);
      if (current !== generation) return;
      n.is_important = data.is_important;
    } catch (_e) {
      console.error("toggleImportant error:", _e);
    }
  }

  async function deleteNotification(id: number) {
    const current = generation;
    try {
      await notificationsApi.delete(id);
      if (current !== generation) return;
      const n = notifications.value.find((n) => n.id === id);
      notifications.value = notifications.value.filter((n) => n.id !== id);
      unreadCount.value = notifications.value.filter((n) => !n.is_read).length;
      if (n && (n as { is_flashing?: boolean }).is_flashing) {
        flashingCount.value = Math.max(0, flashingCount.value - 1);
      }
    } catch (_e) {
      console.error("deleteNotification error:", _e);
    }
  };

  async function cleanReadNotifications() {
    const current = generation;
    try {
      await notificationsApi.cleanRead();
      if (current !== generation) return;
      notifications.value = notifications.value.filter(
        (n) => !n.is_read || n.is_important,
      );
    } catch (_e) {
      console.error("cleanRead error:", _e);
    }
  }

  async function deleteAllNotifications() {
    const current = generation;
    try {
      await notificationsApi.deleteAll();
      if (current !== generation) return;
      notifications.value = notifications.value.filter((n) => n.is_important);
    } catch (_e) {
      console.error("deleteAll error:", _e);
    }
  }

  function addNotification(notification: NotificationItem) {
    if (notifications.value.some(item => item.id === notification.id ||
      (item as GroupedNotificationItem)._groupItems?.some(grouped => grouped.id === notification.id))) return;
    if (notification.type === 'episode_available') void queryClient.invalidateQueries({ queryKey: ['home'] });
    const groupKey = getGroupKey(notification);

    if (groupKey && !notification.is_read) {
      const existingIndex = notifications.value.findIndex(
        (n) => getGroupKey(n) === groupKey && !n.is_read,
      );

      if (existingIndex !== -1) {
        const existing = notifications.value[existingIndex]!;
        const existingTime = new Date(existing.created_at).getTime();
        const newTime = new Date(notification.created_at).getTime();

        if (newTime - existingTime < GROUP_WINDOW_MS) {
          const groupedExisting = existing as GroupedNotificationItem;
          const groupCount = (groupedExisting._groupCount || 1) + 1;
          notifications.value[existingIndex] = {
            ...existing,
            content: notification.content || existing.content,
            title: `${groupCount} новых уведомлений`,
            _groupCount: groupCount,
            _groupItems: [
              ...(groupedExisting._groupItems || [existing]),
              notification,
            ],
          } as GroupedNotificationItem;

          unreadCount.value = notifications.value.filter((n) => !n.is_read).length;
          flashingCount.value = notifications.value.filter(
            (n) => (n as { is_flashing?: boolean }).is_flashing,
          ).length;
          return;
        }
      }
    }

    if (!notifications.value.some((n) => n.id === notification.id)) {
      notifications.value.unshift(notification);
    }
    if (!recentNotifications.value.some((n) => n.id === notification.id)) {
      recentNotifications.value = [
        notification,
        ...recentNotifications.value,
      ].slice(0, 5);
    }
    if (!notification.is_read) unreadCount.value++;
    if ((notification as { is_flashing?: boolean }).is_flashing) {
      flashingCount.value++;
    }
  }

  async function fetchReminders() {
    const current = generation;
    try {
      const { data } = await apiClient.get("/notifications/reminders/", {
        params: { page_size: 50 },
      });
      if (current !== generation) return;
      reminders.value = Array.isArray(data) ? data : (data.results ?? []);
    } catch (_e) {
      if (current === generation && !isRequestCancelled(_e)) console.error("fetchReminders error:", _e);
    }
  }

  async function createReminder(payload: {
    anime_id?: number;
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
  }) {
    const current = generation;
    if (current !== generation) return;
    const { data } = await apiClient.post("/notifications/reminders/", payload);
    if (current !== generation) return;
    reminders.value = [data, ...reminders.value.filter(item => item.id !== data.id)];
    return data;
  }

  async function deleteReminder(id: number) {
    const current = generation;
    await apiClient.delete(`/notifications/reminders/${id}/`);
      if (current !== generation) return;
    reminders.value = reminders.value.filter((r) => r.id !== id);
  }

  async function deactivateReminder(id: number) {
    const current = generation;
    await apiClient.post(`/notifications/reminders/${id}/deactivate/`);
      if (current !== generation) return;
    const r = reminders.value.find((r) => r.id === id);
    if (r) r.is_active = false;
  }

  async function acknowledgeReminder(id: number) {
    const current = generation;
    await apiClient.post(`/notifications/reminders/${id}/acknowledge/`);
      if (current !== generation) return;
    const r = reminders.value.find((r) => r.id === id);
    if (r) r.is_triggered = false;
    stopRinging(id);
  }

  async function checkAndTriggerReminders() {
    const current = generation;
    try {
      const { data } = await apiClient.post(
        "/notifications/reminders/check_and_trigger/",
      );
      if (current !== generation) return;

      if (data.triggered_count > 0) {
        await fetchReminders();

        data.triggered_ids.forEach((id: number) => {
          startRinging(id);
        });

        await fetchRecent();

        try {
          if (data.triggered_ids.some((id: number) => reminders.value.find(r => r.id === id)?.enable_sound)) {
            const audio = new Audio("/sounds/notification.mp3");
            audio.volume = 0.5;
            audio.play().catch(() => {});
          }
        } catch {}
      }
      return data;
    } catch (e) {
      console.error("checkAndTriggerReminders error:", e);
      return { triggered_count: 0, triggered_ids: [] };
    }
  }

  const upcomingReminders = computed(() =>
    reminders.value
      .filter((r) => r.is_active)
      .sort(
        (a, b) =>
          new Date(a.reminder_time).getTime() -
          new Date(b.reminder_time).getTime(),
      )
      .slice(0, 10),
  );

  const allActiveReminders = computed(() =>
    reminders.value
      .filter((r) => r.is_active)
      .sort(
        (a, b) =>
          new Date(b.reminder_time).getTime() -
          new Date(a.reminder_time).getTime(),
      ),
  );

  async function fetchSettings() {
    const current = generation;
    try {
      const { data } = await notificationsApi.getSettings();
      if (current !== generation) return;
      settings.value = data;
    } catch (_e) {
      if (current === generation && !isRequestCancelled(_e)) console.error("fetchSettings error:", _e);
    }
  }

  async function saveSettings(patch: Partial<NotificationSettings>) {
    const current = generation;
    try {
      const { data } = await notificationsApi.saveSettings(patch);
      if (current !== generation) return;
      settings.value = data;
    } catch (_e) {
      console.error("saveSettings error:", _e);
    }
  }

  function reset() {
    generation++;
    _ringTimers.forEach(timer => clearTimeout(timer)); _ringTimers.clear();
    notifications.value = []; recentNotifications.value = []; reminders.value = [];
    unreadCount.value = 0; flashingCount.value = 0; ringingReminderIds.value = [];
    recentNotificationsLastLoadedAt.value = null; unreadCountLastLoadedAt.value = null;
    recentNotificationsLoadingPromise.value = null; unreadCountLoadingPromise.value = null;
    loading.value = false; loadingMore.value = false; currentPage.value = 1; hasMore.value = true;
    settings.value = null;
  }

  return {
    reset,
    notifications,
    recentNotifications,
    reminders,
    unreadCount,
    flashingCount,
    loading,
    loadingMore,
    hasMore,
    hasUnread,
    settings,
    upcomingReminders,
    allActiveReminders,
    isBellRinging,
    ringingReminderIds,
    isReminderRinging,
    startRinging,
    stopRinging,

    fetchNotifications,
    fetchRecent,
    fetchCount,
    loadMoreNotifications,
    markRead,
    markAllRead,
    toggleImportant,
    deleteNotification,
    cleanReadNotifications,
    deleteAllNotifications,
    addNotification,

    fetchReminders,
    createReminder,
    deleteReminder,
    deactivateReminder,
    acknowledgeReminder,
    checkAndTriggerReminders,

    fetchSettings,
    saveSettings,

  };
});
