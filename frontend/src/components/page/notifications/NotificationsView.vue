<template>
  <div class="notif-page">
    <div class="notif-container">
      <div class="page-header">
        <h1><SakuraIcon name="bell"/> Уведомления</h1>
        <div class="header-actions">
          <button
            v-if="store.unreadCount > 0"
            class="btn-action btn-green"
            @click="handleMarkAllRead"
            :disabled="store.loading"
          >
            <SakuraIcon name="check" :size="16" /> Все прочитано
          </button>
        </div>
      </div>

      <div
        v-if="showDeleteConfirm"
        class="confirm-overlay"
        @click.self="showDeleteConfirm = false"
      >
        <div class="confirm-box">
          <p>
            Удалить все уведомления? Важные (<SakuraIcon name="star"/>) сохранятся.
          </p>
          <div class="confirm-btns">
            <button class="btn-action btn-danger" @click="executeDeleteAll">
              Удалить
            </button>
            <button
              class="btn-action btn-dim"
              @click="showDeleteConfirm = false"
            >
              Отмена
            </button>
          </div>
        </div>
      </div>

      <div class="tabs-wrapper">

        <div class="tabs">
          <button
            v-for="t in tabs"
            :key="t.key"
            :class="['tab', { active: activeTab === t.key }]"
            @click="switchTab(t.key)"
          >
            {{ t.label }}
            <span
              v-if="t.key === 'unread' && store.unreadCount > 0"
              class="tab-badge"
            >
              {{ store.unreadCount }}
            </span>
            <span
              v-if="t.key === 'reminders' && activeRemindersCount > 0"
              class="tab-badge reminder"
            >
              {{ activeRemindersCount }}
            </span>
          </button>
        </div>
      </div>

      <div class="content-box" ref="contentRef">
        <div v-if="store.loading && shownList.length === 0" class="state-empty">
          <p>Загрузка...</p>
        </div>

          <div v-else-if="shownList.length === 0" class="state-empty">
          <div class="empty-icon">
            <SakuraIcon v-if="activeTab === 'reminders'" name="clock" />
            <SakuraIcon v-else name="bell" />
          </div>
          <h3>{{ emptyLabel }}</h3>
          <p>{{ emptyHint }}</p>
        </div>

        <div v-else class="notif-list">
          <template v-if="activeTab === 'reminders'">
            <div
              v-for="r in store.reminders"
              :key="`rem-${r.id}`"
              :class="[
                'notif-row',
                'reminder-row',
                {
                  inactive: !r.is_active,
                  'reminder-ringing': store.isReminderRinging(r.id),
                },
              ]"
            >
              <div
                class="notif-avatar notif-avatar--reminder"
              >
                <span class="avatar-icon"> <SakuraIcon name="clock" :size="16" /> </span>
              </div>

              <div class="notif-body">
                <div class="notif-top">
                  <router-link
                    :to="reminderTarget(r)"
                    class="notif-title-link"
                  >
                    {{ r.anime_detail?.title_ru || "Аниме" }}
                  </router-link>
                  <span v-if="r.repeat_weekly" class="badge badge-weekly"
                    >еженедельно</span
                  >
                  <span v-if="!r.is_active" class="badge badge-off">выкл</span>
                </div>
                <p class="notif-text" v-if="r.comment">{{ r.comment }}</p>
                <div class="notif-meta">
                  <span class="notif-time"
                    ><SakuraIcon name="calendar" :size="16" /> {{ formatDateTime(r.reminder_time) }}</span
                  >
                  <span class="notif-time">{{
                    formatTimeAgo(r.reminder_time)
                  }}</span>
                </div>
              </div>

              <div class="notif-actions">
                  <router-link
                    v-if="r.anime_detail?.id"
                    :to="reminderTarget(r)"
                    class="action-btn watch-btn"
                    title="Смотреть"
                    @click="store.acknowledgeReminder(r.id)"
                  >
                  <SakuraIcon name="play" :size="16" />
                </router-link>
                <button
                  v-if="r.is_active"
                  class="action-btn deact-btn"
                  @click="store.deactivateReminder(r.id)"
                  title="Деактивировать"
                >
                  <SakuraIcon name="x" :size="16" />
                </button>
                <button
                  class="action-btn del-btn"
                  @click="store.deleteReminder(r.id)"
                  title="Удалить"
                >
                  <SakuraIcon name="trash" :size="16" />
                </button>
              </div>
            </div>
          </template>

          <template v-else>
            <template v-for="group in groupedList" :key="group.label">
              <div class="date-separator">{{ group.label }}</div>
              <div
                v-for="n in group.items"
                :key="n.id"
                :class="[
                  'notif-row',
                  { unread: !n.is_read, important: n.is_important },
                ]"
                @click.capture="markReadOnInteraction(n)"
                @click="handleNotifClick(n)"
              >
                <div class="notif-avatar" :style="iconStyle(n.type)">
                  <SakuraIcon :name="notificationIcon(n.type, n.icon)" :size="22" />
                </div>

                <div class="notif-body">
                  <div class="notif-top">
                    <p class="notif-title">{{ notificationTitle(n.title, n.type) }}</p>
                    <span v-if="!n.is_read" class="unread-dot" />
                  </div>
                  <p v-if="n.content" class="notif-text">{{ n.content }}</p>
                  <span class="notif-time">{{
                    formatTimeAgo(n.created_at)
                  }}</span>
                </div>

                <div class="notif-actions" @click.stop>
                  <button
                    v-if="!n.is_read"
                    class="action-btn read-btn"
                    @click.stop="store.markRead(n.id)"
                    title="Отметить прочитанным"
                  >
                    <SakuraIcon name="check" :size="16" />
                  </button>
                  <button
                    class="action-btn star-btn"
                    :class="{ 'is-important': n.is_important }"
                    @click.stop="store.toggleImportant(n.id)"
                    :title="n.is_important ? 'Убрать из важных' : 'Отметить важным'"
                    :aria-pressed="n.is_important"
                  >
                    <SakuraIcon name="star" :solid="n.is_important" :size="18" />
                  </button>
                  <button
                    class="action-btn del-btn"
                    @click.stop="store.deleteNotification(n.id)"
                    title="Удалить"
                  >
                    <SakuraIcon name="trash" :size="16" />
                  </button>
                </div>
              </div>
            </template>

            <div v-if="store.loadingMore" class="loading-more">
              <div class="spinner small" />
              <span>Загрузка...</span>
            </div>
            <div
              v-else-if="store.hasMore && filteredList.length > 0"
              class="load-more-btn"
            >
              <button @click="loadMore">Загрузить ещё</button>
            </div>
            <div
              v-else-if="filteredList.length > 0 && !store.hasMore"
              class="end-of-list"
            >
              Все уведомления загружены
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { ref, computed, onMounted, onUnmounted } from "vue";
import { notificationIcon } from '@/lib/notificationIcon';
import { notificationTitle } from '@/lib/systemUiText';
import { useRouter, useRoute } from "vue-router";
import { useNotificationStore } from "@/stores/notifications";
import type { NotificationItem } from "@/api/notifications";

const store = useNotificationStore();
const router = useRouter();
const route = useRoute();

const activeTab = ref<"all" | "unread" | "reminders">("all");
const showDeleteConfirm = ref(false);
const contentRef = ref<HTMLElement | null>(null);

const tabs = [
  { key: "all", label: "Все" },
  { key: "unread", label: "Непрочитанные" },
  { key: "reminders", label: "Напоминания" },
] as const;


const ICONS: Record<string, string> = {
  like: "heart",
  dislike: "thumbs-down",
  heart: "heart",
  comment: "message",
  reply: "reply",
  mention: "at",
  follow: "users",
  repost: "refresh",
  message: "mail",
  group_message: "users",
  group_invite: "inbox",
  achievement: "trophy",
  contest: "medal",
  contest_vote: "vote",
  contest_results: "chart",
  contest_win: "crown",
  reminder_episode: "clock",
  reminder_event: "calendar",
  reminder_contest: "hourglass",
  system: "settings",
  warning: "alert-triangle",
  security: "lock",
};

const COLORS: Record<string, string> = {
  like: "rgba(244,67,54,0.15)",
  dislike: "rgba(158,158,158,0.15)",
  heart: "rgba(236,72,153,0.15)",
  comment: "rgba(33,150,243,0.15)",
  reply: "rgba(33,150,243,0.15)",
  mention: "rgba(255,152,0,0.15)",
  follow: "rgba(76,175,80,0.15)",
  repost: "rgba(156,39,176,0.15)",
  message: "rgba(0,188,212,0.15)",
  achievement: "rgba(255,193,7,0.15)",
  contest_win: "rgba(255,193,7,0.15)",
  warning: "rgba(245,158,11,0.15)",
  security: "rgba(239,68,68,0.15)",
  system: "rgba(96,125,139,0.15)",
};

const getIcon = (type: string) => ICONS[type] || "bell";
const iconStyle = (type: string) => ({
  background: COLORS[type] || "rgba(102,126,234,0.15)",
});


const activeRemindersCount = computed(
  () => store.reminders.filter((r) => r.is_active).length,
);

const reminderTarget = (reminder: { anime_detail?: { id: number | null; slug?: string; target_type?: string } }) => {
  const detail = reminder.anime_detail;
  if (!detail?.id) return "/anime?section=calendar";
  const identifier = detail.slug || detail.id;
  return detail.target_type === "franchise"
    ? `/franchise/${identifier}`
    : `/anime/${identifier}`;
};


const filteredList = computed(() => {
  let list = store.notifications;

  if (activeTab.value === "unread") list = list.filter((n) => !n.is_read);

  return list;
});

const groupedList = computed(() => {
  const groups: { label: string; items: NotificationItem[] }[] = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  const todayItems: NotificationItem[] = [];
  const yesterdayItems: NotificationItem[] = [];
  const olderItems: NotificationItem[] = [];

  for (const n of filteredList.value) {
    const d = new Date(n.created_at);
    d.setHours(0, 0, 0, 0);
    if (d.getTime() === today.getTime()) todayItems.push(n);
    else if (d.getTime() === yesterday.getTime()) yesterdayItems.push(n);
    else olderItems.push(n);
  }

  if (todayItems.length) groups.push({ label: "Сегодня", items: todayItems });
  if (yesterdayItems.length)
    groups.push({ label: "Вчера", items: yesterdayItems });
  if (olderItems.length) groups.push({ label: "Ранее", items: olderItems });

  return groups;
});

const shownList = computed(() => {
  if (activeTab.value === "reminders") return store.reminders;
  return filteredList.value;
});

const emptyLabel = computed(() => {
  if (activeTab.value === "reminders") return "Нет напоминаний";
  if (activeTab.value === "unread") return "Всё прочитано";
  return "Нет уведомлений";
});
const emptyHint = computed(() => {
  if (activeTab.value === "reminders")
    return "Добавляйте напоминания на страницах аниме";
  if (activeTab.value === "unread") return "Новые уведомления появятся здесь";
  return "Когда появятся уведомления, они будут здесь";
});


const switchTab = async (tab: "all" | "unread" | "reminders") => {
  activeTab.value = tab;
  if (tab === "reminders") {
    await store.fetchReminders();
  } else {
    await store.fetchNotifications(true);
  }
};

const handleNotifClick = (n: NotificationItem) => {
  if (n.link) router.push(n.link);
};

const markReadOnInteraction = (n: NotificationItem) => {
  if (!n.is_read) void store.markRead(n.id);
};

const handleMarkAllRead = () => store.markAllRead();

const executeDeleteAll = async () => {
  showDeleteConfirm.value = false;
  await store.deleteAllNotifications();
};

const loadMore = () => store.loadMoreNotifications();

let scrollTimeout: ReturnType<typeof setTimeout> | null = null;
const handleScroll = () => {
  if (scrollTimeout) clearTimeout(scrollTimeout);
  scrollTimeout = setTimeout(() => {
    if (store.loadingMore || !store.hasMore) return;
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    if (scrollTop + clientHeight >= scrollHeight - 200) loadMore();
  }, 100);
};


const normalizeDate = (raw: string): Date | null => {
  if (!raw) return null;
  const s =
    raw.includes("Z") || raw.includes("+") || /T.*-\d{2}:\d{2}$/.test(raw)
      ? raw
      : raw.replace(" ", "T") + "Z";
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
};

const formatTimeAgo = (raw: string): string => {
  const d = normalizeDate(raw);
  if (!d) return "";
  const diff = Math.floor((Date.now() - d.getTime()) / 1000);
  if (diff < 60) return "только что";
  if (diff < 3600) return `${Math.floor(diff / 60)} мин. назад`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} ч. назад`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} дн. назад`;
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
};

const formatDateTime = (raw: string): string => {
  const d = normalizeDate(raw);
  if (!d) return "";
  return d.toLocaleString("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
};

onMounted(async () => {
  const queryTab = route.query.tab as string | undefined;
  const validTabs = ["all", "unread", "reminders"];
  if (queryTab && validTabs.includes(queryTab)) {
    activeTab.value = queryTab as typeof activeTab.value;
  }

  if (activeTab.value === "reminders") {
    await store.fetchReminders();
  } else {
    store.fetchNotifications(true);
    store.fetchReminders(); // загружаем фоном для счётчика таба
  }

  window.addEventListener("scroll", handleScroll);
});
onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll);
  if (scrollTimeout) clearTimeout(scrollTimeout);
});
</script>

<style scoped>
.notif-page {
  min-height: 100vh;
  background: var(--surface-1);
  color: var(--text-primary);
  padding: 2rem 1.5rem;
}

.notif-container {
  max-width: 740px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ── Заголовок ─────────────────────────────────────────── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.page-header h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-primary);
}
.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.btn-action {
  padding: 0.45rem 1rem;
  border-radius: var(--radius-full);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.btn-green {
  border-color: var(--success-subtle);
  background: var(--success-subtle);
  color: var(--success);
}
.btn-green:hover {
  background: color-mix(in srgb, var(--success) 25%, transparent);
}
.btn-dim {
  border-color: var(--border-subtle);
  background: var(--surface-3);
  color: var(--text-tertiary);
}
.btn-dim:hover {
  color: var(--text-secondary);
}
.btn-danger {
  border-color: var(--danger-subtle);
  background: var(--danger-subtle);
  color: var(--danger);
}
.btn-danger:hover {
  background: color-mix(in srgb, var(--danger) 25%, transparent);
}
.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Подтверждение удаления ─────────────────────────────── */
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.confirm-box {
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  padding: 1.5rem 2rem;
  max-width: 340px;
  text-align: center;
}
.confirm-box p {
  margin: 0 0 1rem;
  color: var(--text-secondary);
}
.confirm-btns {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}

/* ── Табы ───────────────────────────────────────────────── */
.tabs-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.total-unread-badge {
  position: absolute;
  top: -28px;
  left: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--accent-subtle);
  border: 1px solid var(--accent-glow-sm);
  border-radius: var(--radius-full);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  z-index: 10;
}

.tabs {
  display: flex;
  gap: 0.4rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 0.35rem;
}
.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.5rem 0.6rem;
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  font-size: 0.855rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.tab:hover {
  color: var(--text-secondary);
}
.tab.active {
  background: var(--accent-subtle);
  color: var(--accent);
  font-weight: 700;
}
.tab-badge {
  height: 18px;
  width: 18px;
  min-width: 18px;
  min-height: 18px;
  background: var(--accent);
  color: var(--text-on-accent);
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 700;
}
.tab-badge.reminder {
  background: var(--warning);
  color: var(--text-on-accent);
}

/* ── Контент ────────────────────────────────────────────── */
.content-box {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

/* ── Пусто / загрузка ───────────────────────────────────── */
.state-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
  color: var(--text-tertiary);
  text-align: center;
}
.empty-icon {
  font-size: 3rem;
}
.state-empty h3 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--text-secondary);
}
.state-empty p {
  margin: 0;
  font-size: 0.88rem;
  color: var(--text-tertiary);
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.spinner.small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Список ─────────────────────────────────────────────── */
.notif-list {
  display: flex;
  flex-direction: column;
}

.date-separator {
  padding: 0.5rem 1.25rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-1);
}

/* ── Строка ─────────────────────────────────────────────── */
.notif-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.9rem 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
  position: relative;
  transition: background 0.15s;
}
.notif-row:last-child {
  border-bottom: none;
}
.notif-row:hover {
  background: var(--surface-4);
}

.notif-row.unread {
  background: var(--accent-subtle);
}
.notif-row.unread::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
}
.notif-row.important {
  background: var(--accent-subtle);
}
.notif-row.important::before {
  background: var(--accent);
}
.notif-row.reminder-row {
  background: var(--warning-subtle);
  cursor: default;
}
.notif-row.inactive {
  opacity: 0.45;
}

/* Сверкающая строка напоминания */
.notif-row.reminder-ringing {
  animation: reminder-row-flash 0.7s ease-in-out infinite;
}
.notif-row.reminder-ringing::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--warning);
  border-radius: 0 2px 2px 0;
  animation: reminder-bar-flash 0.7s ease-in-out infinite;
}
@keyframes reminder-row-flash {
  0%,
  100% {
    background: var(--warning-subtle);
  }
  50% {
    background: color-mix(in srgb, var(--warning) 20%, transparent);
  }
}
@keyframes reminder-bar-flash {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 1;
  }
}

/* ── Аватар ─────────────────────────────────────────────── */
.notif-avatar {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.notif-avatar--reminder {
  background: var(--warning-subtle);
}
.avatar-icon {
  font-size: 1.15rem;
}

/* ── Тело ───────────────────────────────────────────────── */
.notif-body {
  flex: 1;
  min-width: 0;
}
.notif-top {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 2px;
  flex-wrap: wrap;
}
.notif-title {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notif-title-link {
  color: inherit;
  text-decoration: none;
}
.notif-title-link:hover {
  color: var(--accent);
}
.unread-dot {
  width: 7px;
  height: 7px;
  background: var(--accent);
  border-radius: 50%;
  flex-shrink: 0;
}
.notif-text {
  margin: 0 0 4px;
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.notif-meta {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  flex-wrap: wrap;
}
.notif-time {
  font-size: 0.73rem;
  color: var(--text-tertiary);
}

.badge {
  padding: 1px 7px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 600;
  flex-shrink: 0;
}
.badge-weekly {
  background: var(--accent-subtle);
  color: var(--accent);
}
.badge-off {
  background: var(--surface-4);
  color: var(--text-tertiary);
}

/* ── Кнопки действий ────────────────────────────────────── */
.notif-actions {
  display: flex;
  gap: 0.35rem;
  align-items: center;
  flex-shrink: 0;
}


.action-btn {
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  background: var(--surface-3);
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: all 0.15s;
}
.action-btn:hover {
  border-color: var(--border-default);
  color: var(--text-primary);
  background: var(--surface-4);
}
.read-btn:hover {
  background: var(--success-subtle);
  color: var(--success);
  border-color: color-mix(in srgb, var(--success) 40%, transparent);
}
.del-btn:hover {
  background: var(--danger-subtle);
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 40%, transparent);
}
.deact-btn:hover {
  background: var(--warning-subtle);
  color: var(--warning);
  border-color: color-mix(in srgb, var(--warning) 40%, transparent);
}
.watch-btn:hover {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: var(--accent-glow-sm);
}
.star-btn {
  font-size: 0.85rem;
}
.star-btn.is-important {
  background: var(--accent-subtle);
  border-color: var(--accent-glow-sm);
  color: var(--accent);
}

/* ── Загрузка ещё / конец ───────────────────────────────── */
.loading-more,
.load-more-btn,
.end-of-list {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1.5rem;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}
.load-more-btn button {
  padding: 0.45rem 1.5rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--accent-glow-sm);
  background: var(--accent-subtle);
  color: var(--accent);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.load-more-btn button:hover {
  background: color-mix(in srgb, var(--accent) 25%, transparent);
}
.end-of-list {
  font-size: 0.78rem;
  color: var(--text-tertiary);
  border-top: 1px solid var(--border-subtle);
}

/* ── Адаптив ────────────────────────────────────────────── */
@media (max-width: 640px) {
  .notif-page {
    padding: 1rem;
  }
  .page-header h1 {
    font-size: 1.4rem;
  }
  .notif-row {
    padding: 0.8rem 1rem;
  }
  .tabs {
    gap: 0.2rem;
  }
  .tab {
    font-size: 0.78rem;
    padding: 0.4rem 0.45rem;
  }
  .header-actions {
    gap: 0.35rem;
  }
  .btn-action {
    padding: 0.38rem 0.75rem;
    font-size: 0.78rem;
  }
}
@media (max-width: 480px) {
  .notif-row {
    display: grid;
    grid-template-columns: 40px minmax(0, 1fr);
    gap: 10px;
    padding: 14px;
  }
  .notif-actions { grid-column: 2; }
  .action-btn { width: 44px; height: 44px; min-width: 44px; min-height: 44px; }
  .notif-top { flex-wrap: wrap; }
  .tabs { flex-wrap: wrap; }
  .tab { flex: 1 1 auto; min-height: 44px; }
}
</style>
