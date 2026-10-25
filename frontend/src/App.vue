<template>
  <div :class="['app', { 'sidebar-collapsed': isCollapsed, 'is-landing': showLandingNav }]">
    <ParallaxBackdrop v-if="parallaxActive" />
    <SakuraOverlay v-if="sakuraEnabled" />
    <NewYearOverlay v-if="newYearEnabled" />
    <HalloweenOverlay v-if="halloweenEnabled" />
    <LoveDayOverlay v-if="loveDayEnabled" />
    <CursorEffects />

    <SidebarNavigation v-if="!showLandingNav && windowWidth > 767" />

    <NavBar v-if="!showLandingNav" />

    <main class="main-content">
      <div v-if="!pwaOnline" class="offline-banner" role="status">Нет сети. Доступны сохранённые публичные страницы и черновики. <RouterLink to="/app">О приложении</RouterLink></div>
      <router-view v-slot="{ Component, route }">
        <KeepAlive :key="authStore.user?.id ?? 'guest'" include="AnimeView,FeedView" :max="3">
          <component :is="Component" :key="route.path" />
        </KeepAlive>
      </router-view>
      <SeoNavigation />
    </main>

    <MobileNavigation v-if="!showLandingNav && windowWidth <= 767" />

    <ToastContainer />
    <PwaUpdateNotification />
    <NotificationToast v-if="authStore.isAuthenticated" />
    <PostWorkStatus v-if="authStore.isAuthenticated" />

    <Teleport to="body">
      <FloatingPlayer
        v-if="floatingPlayerState.show"
        :visible="floatingPlayerState.show"
        :anime-id="floatingPlayerState.animeId ?? undefined"
        :anime-title="floatingPlayerState.animeTitle"
        :episode="floatingPlayerState.episode ?? undefined"
        :season="floatingPlayerState.season ? Number(floatingPlayerState.season) : undefined"
        :player-link="floatingPlayerState.playerLink"
        :translation-id="floatingPlayerState.translationId ?? undefined"
        :start-time="floatingPlayerState.startTime"
        @close="closeFloatingPlayer"
      />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import SeoNavigation from '@/components/common/SeoNavigation.vue';
import {
  ref,
  computed,
  watch,
  provide,
  onMounted,
  onUnmounted,
  defineAsyncComponent,
} from "vue"
import { useRoute } from "vue-router";
import { afterInitialContent } from '@/lib/initialContent';
import { useTabBadge } from "@/composables/useTabBadge";
import { showBrowserNotification, type BrowserAttention } from "@/lib/browserNotifications";
import { useAuthStore } from "@/stores/auth";
import { useSettingsStore } from "@/stores/settings";
import { useFloatingPlayerStore } from "@/stores/floating-player";
import { useSidebar } from "@/composables/useSidebar";
import { useOnlineHeartbeat } from "@/composables/useOnlineHeartbeat";

import { useAppearance } from "@/composables/useAppearance";
import { useSakuraOverlay } from "@/composables/useSakuraOverlay";
import { useNewYearOverlay } from "@/composables/useNewYearOverlay";
import { useHalloweenOverlay } from "@/composables/useHalloweenOverlay";
import { useLoveDayOverlay } from "@/composables/useLoveDayOverlay";
import { useVisualViewport } from '@/composables/useVisualViewport';
useVisualViewport();
import { usePwa } from '@/composables/usePwa'
const { online: pwaOnline } = usePwa()
import { notificationTitle } from '@/lib/systemUiText';
const { parallaxEffect, smoothAnimations } = useAppearance();
const parallaxActive = computed(() => parallaxEffect.value && smoothAnimations.value);
const { sakuraEnabled } = useSakuraOverlay();
const { newYearEnabled } = useNewYearOverlay();
const { halloweenEnabled } = useHalloweenOverlay();
const { loveDayEnabled } = useLoveDayOverlay();

const FloatingPlayer = defineAsyncComponent(
  () => import("@/components/Players/FloatingPlayer.vue"),
);
const NavBar = defineAsyncComponent(() => import('@/components/Navigation/NavBar.vue'));
const SidebarNavigation = defineAsyncComponent(() => import('@/components/Navigation/SidebarNavigation.vue'));
const MobileNavigation = defineAsyncComponent(() => import('@/components/Navigation/MobileNavigation.vue'));
const ToastContainer = defineAsyncComponent(() => import('@/components/Notifications/ToastContainer.vue'));
const PwaUpdateNotification = defineAsyncComponent(() => import('@/components/Notifications/PwaUpdateNotification.vue'));
const NotificationToast = defineAsyncComponent(() => import('@/components/NotificationToast.vue'));
const PostWorkStatus = defineAsyncComponent(() => import('@/components/feed/PostWorkStatus.vue'));
const ParallaxBackdrop = defineAsyncComponent(() => import('@/components/effects/ParallaxBackdrop.vue'));
const SakuraOverlay = defineAsyncComponent(() => import('@/components/effects/SakuraOverlay.vue'));
const NewYearOverlay = defineAsyncComponent(() => import('@/components/effects/NewYearOverlay.vue'));
const HalloweenOverlay = defineAsyncComponent(() => import('@/components/effects/HalloweenOverlay.vue'));
const LoveDayOverlay = defineAsyncComponent(() => import('@/components/effects/LoveDayOverlay.vue'));
const CursorEffects = defineAsyncComponent(() => import('@/components/effects/cursor/CursorEffects.vue'));

const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const floatingPlayerStore = useFloatingPlayerStore();
const { isCollapsed } = useSidebar();
const route = useRoute();
useOnlineHeartbeat();

const showLandingNav = computed(() => route.meta.hideAppNav === true);

const windowWidth = ref(typeof window === 'undefined' ? 1024 : window.innerWidth);

const floatingPlayerState = ref({
  show: false,
  animeId: null as number | null,
  animeTitle: "",
  episode: null as number | null,
  season: null as string | null,
  playerLink: "",
  translationId: null as number | null,
  startTime: 0,
});

watch(
  () => floatingPlayerStore.currentAnime,
  (anime) => {
    if (anime) {
      floatingPlayerState.value = {
        show: true,
        animeId: anime.anime_id,
        animeTitle: anime.anime_title,
        episode: anime.episode ?? null,
        season: anime.season != null ? String(anime.season) : null,
        playerLink: anime.player_link ?? "",
        translationId: anime.translation_id ?? null,
        startTime: anime.start_time || 0,
      };
    }
  },
  { immediate: true },
);

const closeFloatingPlayer = () => {
  floatingPlayerStore.clearCurrentAnime();
  floatingPlayerState.value.show = false;
};

provide("auth", authStore);
provide("settings", settingsStore);

const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

const notificationUnreadCount = ref(0);
const notificationSettings = ref<{ push_enabled?: boolean; type_settings?: Record<string, { enabled?: boolean }> } | null>(null);
const chatUnreadCount = ref(0);
const unreadBadge = computed(() => authStore.isAuthenticated ? notificationUnreadCount.value + chatUnreadCount.value : 0);
useTabBadge(unreadBadge);
const notifiedIds = new Set<string>();
const handleBrowserAttention = (event: Event) => {
  if (!authStore.isAuthenticated || notificationSettings.value?.push_enabled === false) return;
  const item = (event as CustomEvent<BrowserAttention>).detail;
  if (item) void showBrowserNotification(item);
};
const handleNewNotification = (event: Event) => {
  const item = (event as CustomEvent).detail;
  if (!item || item.is_read || !authStore.isAuthenticated) return;
  const key = `${authStore.user?.id}:${item.id}`;
  if (notifiedIds.has(key)) return;
  notifiedIds.add(key);
  if (notifiedIds.size > 500) notifiedIds.delete(notifiedIds.values().next().value!);
  if (notificationSettings.value?.type_settings?.[item.type]?.enabled === false) return;
  if (item.enable_push === false) return;
  handleBrowserAttention(new CustomEvent('browserAttention', { detail: {
    title: notificationTitle(item.title, item.type) || 'Новое уведомление', body: item.content, url: item.link, tag: `notification:${item.id}`,
  } }));
};
let stopChatUnreadWatch: (() => void) | undefined;
let stopNotificationWatch: (() => void) | undefined;
let authLoadGeneration = 0;
let devicePushRuntime: Promise<typeof import('@/lib/devicePush')> | null = null;
const syncPush = () => {
  devicePushRuntime ??= import('@/lib/devicePush');
  return devicePushRuntime.then(module => module.syncDevicePush());
};
watch(() => authStore.isAuthenticated, authenticated => {
  const generation = ++authLoadGeneration;
  if (authenticated) afterInitialContent(() => {
    if (!authStore.isAuthenticated || generation !== authLoadGeneration) return;
    void syncPush();
    void import('@/stores/notifications').then(({ useNotificationStore }) => {
      if (!authStore.isAuthenticated || generation !== authLoadGeneration) return;
      const notificationStore = useNotificationStore();
      stopNotificationWatch?.();
      stopNotificationWatch = watch(
        () => [notificationStore.unreadCount, notificationStore.settings] as const,
        ([count, settings]) => {
          notificationUnreadCount.value = count;
          notificationSettings.value = settings;
        },
        { immediate: true },
      );
      void notificationStore.fetchSettings();
    });
    void import('@/stores/chatExtras').then(({ useChatExtrasStore }) => {
      if (!authStore.isAuthenticated || generation !== authLoadGeneration) return;
      const chatExtrasStore = useChatExtrasStore();
      stopChatUnreadWatch?.();
      stopChatUnreadWatch = watch(() => chatExtrasStore.totalUnreadCount, count => { chatUnreadCount.value = count; }, { immediate: true });
      void chatExtrasStore.loadUnreadChats(true);
    });
  });
  else {
    stopChatUnreadWatch?.();
    stopChatUnreadWatch = undefined;
    stopNotificationWatch?.();
    stopNotificationWatch = undefined;
    chatUnreadCount.value = 0;
    notificationUnreadCount.value = 0;
    notificationSettings.value = null;
    notifiedIds.clear();
  }
}, { immediate: true });
const syncPushOnForeground = () => { if (authStore.isAuthenticated && document.visibilityState === 'visible') void syncPush() }

onMounted(() => {
  handleResize();
  window.addEventListener("resize", handleResize);
  window.addEventListener('browserAttention', handleBrowserAttention);
  window.addEventListener('newNotification', handleNewNotification);
  window.addEventListener('online', syncPushOnForeground);
  document.addEventListener('visibilitychange', syncPushOnForeground);
});

onUnmounted(() => {
  window.removeEventListener('browserAttention', handleBrowserAttention);
  window.removeEventListener('newNotification', handleNewNotification);
  window.removeEventListener('online', syncPushOnForeground);
  document.removeEventListener('visibilitychange', syncPushOnForeground);
  window.removeEventListener("resize", handleResize);
  stopChatUnreadWatch?.();
  stopNotificationWatch?.();
});
</script>

<style>
#app {
  width: 100%;
  min-height: 100vh;
}

.app {
  --app-sidebar-offset: var(--sidebar-width);
  --sb-transition-duration: 280ms;
  --sb-transition-ease: cubic-bezier(0.22, 0.61, 0.36, 1);
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

.app.sidebar-collapsed {
  --app-sidebar-offset: var(--sidebar-width-collapsed);
}

/* One changing margin lets the live content fill the remaining width.
   Native CSS transitions can reverse immediately from their current position. */
.main-content {
  flex: 1;
  min-width: 0;
  margin-left: var(--app-sidebar-offset);
  padding-top: var(--navbar-height, 64px);
  transition: margin-left var(--sb-transition-duration) var(--sb-transition-ease);
}

.app.is-landing .main-content {
  width: 100%;
  margin-left: 0;
  padding-top: 0;
}

@media (prefers-reduced-motion: reduce) {
  .main-content { transition: none; }
}

/* ============================================================
   АДАПТИВНЫЕ СТИЛИ ДЛЯ МОБИЛЬНЫХ УСТРОЙСТВ И ПЛАНШЕТОВ
   ============================================================ */

@media (max-width: 1024px) {
  .main-content {
    padding-top: var(--navbar-height, 56px);
  }
  .app.is-landing .main-content {
    padding-top: 0;
  }
}

@media (max-width: 767px) {
  .main-content {
    width: 100%;
    margin-left: 0;
    padding-left: 0 !important;
    padding-top: var(--navbar-height, 56px);
    padding-bottom: var(--mobile-nav-height, 64px);
  }
  .app.is-landing .main-content {
    padding-top: 0;
    padding-bottom: 0;
  }
}

@media (max-width: 480px) {
  .main-content {
    padding-top: var(--navbar-height, 52px);
    padding-bottom: var(--mobile-nav-height, 60px);
    padding-left: 0 !important;
  }
  .app.is-landing .main-content {
    padding-top: 0;
    padding-bottom: 0;
  }
}

@media (max-width: 767px) and (orientation: landscape) {
  .main-content {
    padding-top: var(--navbar-height, 48px);
    padding-bottom: var(--mobile-nav-height, 52px);
  }
  .app.is-landing .main-content {
    padding-top: 0;
    padding-bottom: 0;
  }
}

@media (max-width: 360px) {
  .main-content {
    padding-top: var(--navbar-height, 48px);
    padding-bottom: var(--mobile-nav-height, 56px);
  }
  .app.is-landing .main-content {
    padding-top: 0;
    padding-bottom: 0;
  }
}

/* ══════ Визуальное качество эффектов ══════ */
@keyframes effects-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.sk-overlay,
.ny-overlay,
.hw-overlay,
.vd-overlay,
.ct-overlay {
  animation: effects-fade-in 0.8s ease-out forwards;
  will-change: contain;
  contain: layout style paint;
}

/* Устройства с вырезом (notch) и safe-area */
@supports (padding: max(0px)) {
  @media (max-width: 767px) {
    .main-content {
      padding-left: max(0px, env(safe-area-inset-left));
      padding-right: max(0px, env(safe-area-inset-right));
      padding-bottom: max(var(--mobile-nav-height, 64px), env(safe-area-inset-bottom));
    }
    .app.is-landing .main-content {
      padding-bottom: max(0px, env(safe-area-inset-bottom));
    }
  }
}
</style>