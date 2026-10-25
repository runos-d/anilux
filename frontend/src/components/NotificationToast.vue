<template>
  <teleport to="body">
    <transition-group name="notification-toast" tag="div" class="notification-toast-container">
      <div
        v-for="notification in visibleNotifications"
        :key="notification.id"
        class="notification-toast"
        @click="handleClick(notification)"
      >
        <div class="notification-toast-icon">
          <SakuraIcon :name="notificationIcon(notification.type, notification.icon)" :size="20" />
        </div>

        <div class="notification-toast-content">
          <div v-if="notification.title" class="notification-toast-title">{{ notificationTitle(notification.title, notification.type) }}</div>
          <div class="notification-toast-message">{{ notification.content }}</div>
        </div>

        <button
          class="notification-toast-close"
          type="button"
          aria-label="Закрыть"
          @click.stop="dismissFromClick(notification)"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <div
          class="notification-toast-progress"
          :style="{ animationDuration: `${notification.duration}ms` }"
        ></div>
      </div>
    </transition-group>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { useNotificationStore } from "@/stores/notifications";
import { useAuthStore } from '@/stores/auth';
import SakuraIcon from '@/components/icons/SakuraIcon.vue';
import { notificationIcon } from '@/lib/notificationIcon';
import { notificationTitle } from '@/lib/systemUiText';
import type { NotificationItem } from "@/api/notifications";

const notificationStore = useNotificationStore();
const auth = useAuthStore();

const SEEN_STORAGE_PREFIX = 'anilux_notification_toasts_seen_v1';
const MAX_SEEN_IDS = 500;
const seenStorageKey = (userId: number | undefined) => `${SEEN_STORAGE_PREFIX}:${userId ?? 'guest'}`;
const readSeenIds = (userId: number | undefined) => {
  try {
    const parsed = JSON.parse(localStorage.getItem(seenStorageKey(userId)) || '[]');
    return new Set<number>(Array.isArray(parsed) ? parsed.filter(Number.isSafeInteger) : []);
  } catch {
    return new Set<number>();
  }
};
const previouslyShownIds = ref<Set<number>>(readSeenIds(auth.user?.id));
let persistedShownIds = new Set(previouslyShownIds.value);
const dismissedIds = ref<Set<number>>(new Set());
const timers = ref<Map<number, ReturnType<typeof setTimeout>>>(new Map());

const DEFAULT_DURATION = 5000;

const visibleNotifications = computed(() => {
  const notifications = notificationStore.recentNotifications.filter(
    (n) => !n.is_read && !previouslyShownIds.value.has(n.id) && !dismissedIds.value.has(n.id),
  );

  return notifications.map((notification) => ({
    ...notification,
    duration: DEFAULT_DURATION,
  }));
});

function scheduleDismiss(id: number, duration: number = DEFAULT_DURATION) {
  rememberShown(id);
  clearDismissTimer(id);
  const timer = setTimeout(() => dismiss(id), duration);
  timers.value.set(id, timer);
}

function rememberShown(id: number) {
  if (persistedShownIds.has(id)) return;
  persistedShownIds.add(id);
  if (persistedShownIds.size > MAX_SEEN_IDS) {
    persistedShownIds = new Set([...persistedShownIds].slice(-MAX_SEEN_IDS));
  }
  try {
    localStorage.setItem(seenStorageKey(auth.user?.id), JSON.stringify([...persistedShownIds]));
  } catch {
    /* Storage can be unavailable; the in-memory dismissal still works. */
  }
}

function clearDismissTimer(id: number) {
  const timer = timers.value.get(id);
  if (timer) {
    clearTimeout(timer);
    timers.value.delete(id);
  }
}

function dismiss(id: number) {
  dismissedIds.value.add(id);
  clearDismissTimer(id);
}

watch(() => auth.user?.id, (userId) => {
  timers.value.forEach(timer => clearTimeout(timer));
  timers.value.clear();
  dismissedIds.value.clear();
  previouslyShownIds.value = readSeenIds(userId);
  persistedShownIds = new Set(previouslyShownIds.value);
});

function handleClick(notification: NotificationItem) {
  if (!notification.is_read) void notificationStore.markRead(notification.id);
  if (notification.link) {
    window.location.href = notification.link;
  }
}

function dismissFromClick(notification: NotificationItem) {
  if (!notification.is_read) void notificationStore.markRead(notification.id);
  dismiss(notification.id);
}

watch(
  () => notificationStore.recentNotifications,
  (current, previous) => {
    const newIds = new Set(current.map((n) => n.id));
    const previousIds = new Set((previous || []).map((n) => n.id));

    current.forEach((notification) => {
      if (!previousIds.has(notification.id) && !notification.is_read) {
        scheduleDismiss(notification.id);
      }
    });
  },
  { deep: true },
);

onMounted(() => {
  notificationStore.recentNotifications.forEach((notification) => {
    if (!notification.is_read && !dismissedIds.value.has(notification.id)) {
      scheduleDismiss(notification.id);
    }
  });
});

onUnmounted(() => {
  timers.value.forEach((timer) => clearTimeout(timer));
  timers.value.clear();
});
</script>

<style scoped>
.notification-toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  /* Incoming notices stay below dialogs and the floating player controls. */
  z-index: calc(var(--z-sidebar) + 5);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 420px;
  width: calc(100% - 2rem);
  pointer-events: none;
  max-height: calc(var(--viewport-height, 100dvh) * 0.4);
  overflow-y: auto;
}

.notification-toast {
  flex-shrink: 0;
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background-color: var(--surface-3);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-sm-modal);
  pointer-events: auto;
  overflow: hidden;
  animation: slideIn 0.3s var(--transition-smooth);
  cursor: pointer;
}

.notification-toast-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: var(--accent);
}

.notification-toast-content {
  flex: 1;
  min-width: 0;
}

.notification-toast-title {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  overflow-wrap: anywhere;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.notification-toast-message {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
  overflow-wrap: anywhere;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.notification-toast-close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.25rem;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
}

.notification-toast-close:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
}

.notification-toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: var(--accent);
  animation: progress linear forwards;
}

.notification-toast-enter-active,
.notification-toast-leave-active {
  transition: all 0.3s var(--transition-smooth);
}

.notification-toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-toast-move {
  transition: transform 0.3s var(--transition-smooth);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

/* ============================================================
   АДАПТИВНЫЕ СТИЛИ ДЛЯ МОБИЛЬНЫХ УСТРОЙСТВ И ПЛАНШЕТОВ
   (десктопные стили выше остаются без изменений)
   ============================================================ */

/* Планшеты: 768px – 1024px */
@media (max-width: 1024px) {
  .notification-toast-container {
    max-width: 380px;
  }
}

/* Существующий брейкпоинт 768px оставлен ниже без изменений */
@media (max-width: 768px) {
  .notification-toast-container {
    top: calc(50px + max(8px, env(safe-area-inset-top)));
    top: 0.5rem;
    right: 0.5rem;
    left: 0.5rem;
    width: calc(100% - 1rem);
    max-width: none;
  }

  .notification-toast {
    padding: 0.875rem;
  }

  .notification-toast-title {
    font-size: 0.875rem;
  }

  .notification-toast-message {
    font-size: 0.8125rem;
  }
}

/* Телефоны: до 480px */
@media (max-width: 480px) {
  .notification-toast-container {
    top: calc(50px + max(8px, env(safe-area-inset-top)));
    right: 0.5rem;
    left: 0.5rem;
    gap: 0.5rem;
    width: calc(100% - 1rem);
  }

  .notification-toast {
    gap: 0.5rem;
    padding: 0.75rem;
    border-radius: 0.625rem;
  }

  .notification-toast-icon {
    width: 20px;
    height: 20px;
  }

  .notification-toast-icon svg {
    width: 18px;
    height: 18px;
  }

  .notification-toast-title {
    font-size: 0.8125rem;
  }

  .notification-toast-message {
    font-size: 0.75rem;
    line-height: 1.35;
  }

  .notification-toast-close {
    width: 22px;
    height: 22px;
  }

  .notification-toast-close svg {
    width: 14px;
    height: 14px;
  }

  .notification-toast-progress {
    height: 2px;
  }
}

/* Ландшафтная ориентация на телефонах */
@media (max-width: 768px) and (orientation: landscape) {
  .notification-toast-container {
    top: 0.375rem;
    gap: 0.375rem;
  }

  .notification-toast {
    padding: 0.625rem 0.75rem;
  }

  .notification-toast-title {
    font-size: 0.8125rem;
    margin-bottom: 0.125rem;
  }

  .notification-toast-message {
    font-size: 0.75rem;
  }
}

/* Очень узкие экраны: до 360px */
@media (max-width: 360px) {
  .notification-toast-container {
    top: 0.375rem;
    right: 0.375rem;
    left: 0.375rem;
    width: calc(100% - 0.75rem);
  }

  .notification-toast {
    gap: 0.375rem;
    padding: 0.625rem;
  }

  .notification-toast-icon {
    width: 18px;
    height: 18px;
  }

  .notification-toast-icon svg {
    width: 16px;
    height: 16px;
  }

  .notification-toast-title {
    font-size: 0.75rem;
  }

  .notification-toast-message {
    font-size: 0.6875rem;
  }

  .notification-toast-close {
    width: 20px;
    height: 20px;
  }

  .notification-toast-close svg {
    width: 12px;
    height: 12px;
  }
}

/* Устройства с вырезом (notch) и safe-area */
@supports (padding: max(0px)) {
  @media (max-width: 768px) {
    .notification-toast-container {
      top: max(0.5rem, env(safe-area-inset-top));
      right: max(0.5rem, env(safe-area-inset-right));
      left: max(0.5rem, env(safe-area-inset-left));
    }
  }
}
</style>
