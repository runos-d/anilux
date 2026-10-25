import './assets/base.css'
import './assets/styles/themes.css'

import { createApp, defineAsyncComponent } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'
import { watch } from 'vue'

import App from './App.vue'
import router from './router'
import { invalidateQueryGroups, queryClient } from '@/lib/queryClient'
import { cancelInitialReads } from '@/lib/initialRead'
import { afterInitialContent } from '@/lib/initialContent'
import { loadFontStyles } from '@/lib/fontStyles'
import '@/lib/publicReadCache'

import { sakuraEmoji } from '@/directives/sakuraEmoji'

const app = createApp(App)
afterInitialContent(loadFontStyles);

app.use(createPinia())
app.use(router)
app.use(VueQueryPlugin, { queryClient })

app.component('OptimizedImage', defineAsyncComponent(() => import('@/components/common/OptimizedImage.vue')))
app.component('SakuraIcon', defineAsyncComponent(() => import('@/components/icons/SakuraIcon.vue')))
app.component('EmojiReplacer', defineAsyncComponent(() => import('@/components/ui/EmojiReplacer.vue')))
app.component('StarRating', defineAsyncComponent(() => import('@/components/ui/StarRating.vue')))
app.component('StatusBadge', defineAsyncComponent(() => import('@/components/ui/StatusBadge.vue')))

app.directive('sakura-emoji', sakuraEmoji)

import { useAuthStore } from '@/stores/auth'
import { useFavoritesStore } from '@/stores/favorites'
import { usePostStore } from '@/stores/posts'
import { clearPostDrafts } from '@/lib/postDrafts'
import apiClient, { cancelAllRequests } from '@/api/client'
import { refreshSeo } from '@/composables/useSeo'
window.addEventListener('pageshow', event => { if (event.persisted) void refreshSeo(router.currentRoute.value.fullPath, true); });
document.addEventListener('visibilitychange', () => { if (!document.hidden) void refreshSeo(router.currentRoute.value.fullPath, true); });
const authStore = useAuthStore()
const favoritesStore = useFavoritesStore()
watch(() => authStore.user?.id, (id, oldId) => {
  if (oldId !== undefined) { cancelAllRequests(true); cancelInitialReads(); }
  favoritesStore.reset();
  if (id) afterInitialContent(() => {
    if (authStore.user?.id === id) void favoritesStore.ensureLoaded().catch(() => undefined);
  });
  usePostStore().clear();
  void import('@/stores/notifications').then(({ useNotificationStore }) => useNotificationStore().reset());
  if (oldId && oldId !== id) void clearPostDrafts(oldId);
  void queryClient.cancelQueries({ predicate: query => query.queryKey[1] !== 'public' });
  queryClient.removeQueries({ predicate: query => query.queryKey[1] !== 'public' });
  if (id) afterInitialContent(() => { if (authStore.user?.id === id) usePostStore().startPending(); });
}, { immediate: true })

apiClient.interceptors.response.use(response => {
  const method = response.config.method;
  const url = response.config.url || '';
  if (/\/playlists\/playlists\/[^/]+\/like\//.test(response.config.url || '')) return response;
  if (method && !['get', 'head', 'options'].includes(method) &&
      !response.config.url?.includes('/post-uploads/') &&
      !response.config.url?.includes('/token/') &&
      !response.config.url?.includes('/online/') && !response.config.url?.includes('/heartbeat/'))
    {
      const groups: string[] = [];
      if (/\/social\/(?:posts|feed|comments)/.test(url)) groups.push('feed', 'post', 'profile');
      if (/\/playlists\//.test(url)) groups.push('playlist');
      if (/\/users\/(?:library|favorites)/.test(url)) groups.push('library', 'recommendations', 'home');
      if (/\/users\/(?:profile|me)/.test(url)) groups.push('profile');
      if (/\/notifications\//.test(url)) groups.push('notifications');
      if (/\/anime\//.test(url)) groups.push('catalog', 'calendar', 'home', 'recommendations');
      void invalidateQueryGroups(groups);
      if (/\/(?:posts|playlists|profile|admin)\//.test(url)) void refreshSeo(router.currentRoute.value.fullPath, true);
    }
  return response;
});

afterInitialContent(() => { void authStore.checkAuth(); });

import { useSettingsStore } from '@/stores/settings'
const settingsStore = useSettingsStore()
settingsStore.init()

import {
  initAppearance,
  loadAppearanceFromServer,
  resetAppearance,
} from '@/composables/useAppearance'

initAppearance()
let appearanceWasLoaded = false
watch(
  () => authStore.isAuthenticated,
  (isAuth) => {
    if (isAuth) {
      appearanceWasLoaded = true
      afterInitialContent(() => { if (authStore.isAuthenticated) void loadAppearanceFromServer(); });
    } else if (appearanceWasLoaded) {
      appearanceWasLoaded = false
      resetAppearance()
    }
  },
  { immediate: true },
)

let globalSocketRuntime: Promise<typeof import('@/composables/useGlobalWebSocket')> | null = null
const loadGlobalSocket = () => globalSocketRuntime ??= import('@/composables/useGlobalWebSocket')
watch(
  () => authStore.isAuthenticated,
  (isAuth) => {
    if (isAuth) {
      afterInitialContent(() => { if (authStore.isAuthenticated) void loadGlobalSocket().then(module => module.initGlobalWebSocket()); });
    } else {
      if (globalSocketRuntime) void globalSocketRuntime.then(module => module.disconnectGlobalWebSocket())
    }
  },
  { immediate: true },
)

app.mount('#app')
document.getElementById('seo-base-style')?.remove();
void router.isReady().then(() => { document.documentElement.dataset.seoMode = 'app'; });
