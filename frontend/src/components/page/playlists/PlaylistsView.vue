<template>
  <div class="playlists-page">
    <div class="page-header">
      <div class="header-top">
        <h1 class="page-title">
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M9 18V5l12-2v13" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
          </svg>
          Плейлисты
        </h1>
        <button class="btn-create" @click="router.push('/playlists/create')">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Создать плейлист
        </button>
      </div>

      <div class="tabs-row">
        <button
          v-for="tab in mainTabs"
          :key="tab.id"
          @click="switchMainTab(tab.id)"
          :class="['tab-btn', { active: activeTab === tab.id }]"
        >
          <span class="tab-icon">
            <SakuraIcon
              v-if="isIconName(tab.icon)"
              :name="tab.icon"
              :size="16"
            />
            <span v-else>{{ tab.icon }}</span>
          </span>
          {{ tab.label }}
          <span v-if="tab.count !== undefined" class="tab-count">{{
            tab.count
          }}</span>
        </button>
      </div>

      <transition name="subtabs">
        <div v-if="activeTab === 'my'" class="subtabs-row">
          <button
            v-for="sub in mySubTabs"
            :key="sub.id"
            @click="switchMySubTab(sub.id)"
            :class="['subtab-btn', { active: mySubTab === sub.id }]"
          >
            <span :class="['vis-dot', `dot-${sub.id}`]"></span>
            {{ sub.label }}
            <span v-if="sub.count !== undefined" class="subtab-count">{{
              sub.count
            }}</span>
          </button>
        </div>
      </transition>
    </div>

    <div class="filters-bar" :class="{ 'public-discovery': activeTab === 'public' }">
      <div class="search-wrapper">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          class="search-icon-svg"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Название или описание..."
          aria-label="Поиск по названию и описанию плейлиста"
          class="search-input"
        />
        <button
          v-if="searchQuery"
          @click="searchQuery = ''"
          aria-label="Очистить поиск"
          class="search-clear-btn"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div v-if="activeTab === 'public'" class="public-controls">
        <label>Сортировка
          <select v-model="publicSort" class="sort-select">
            <option value="-likes_count">Топ</option>
            <option value="-created_at">Новые</option>
            <option value="-updated_at">Недавно обновлённые</option>
            <option value="title">По названию</option>
          </select>
        </label>
        <label v-if="publicSort === '-likes_count'">Период
          <select v-model="period" class="sort-select">
            <option value="week">За неделю</option><option value="month">За месяц</option><option value="all">За всё время</option>
          </select>
        </label>
      </div>
      <div v-else class="sort-wrapper">
        <select v-model="sortBy" class="sort-select">
          <option value="-updated_at">По дате обновления</option>
          <option value="-created_at">По дате создания</option>
          <option value="title">По названию (А-Я)</option>
          <option value="-title">По названию (Я-А)</option>
          <option value="-favorites_count">По популярности</option>
        </select>
      </div>
    </div>

    <div v-if="activeTab === 'public'" class="active-filters" aria-live="polite">
      <span>{{ totalCount }} плейлистов</span>
      <button v-if="searchQuery" @click="searchQuery = ''">Поиск: {{ searchQuery }} ×</button>
      <button v-if="searchQuery || publicSort !== '-likes_count' || period !== 'all'" @click="resetDiscovery">Сбросить</button>
    </div>

    <div v-if="loading && !playlists.length" class="playlists-grid">
      <div v-for="n in pageSize" :key="n" class="skeleton-card catalog-card-skeleton">
        <div class="skeleton-cover"></div>
        <div class="skeleton-info">
          <div class="skeleton-line w-70"></div>
          <div class="skeleton-line w-40"></div>
          <div class="skeleton-line w-55"></div>
        </div>
      </div>
    </div>

    <div v-else-if="error" class="empty-state">
      <div class="empty-icon"><SakuraIcon name="warning" /></div>
      <h3>Не удалось загрузить плейлисты</h3>
      <p>{{ error }}</p>
      <button @click="loadPlaylists" class="btn-retry">
        Попробовать снова
      </button>
    </div>

    <div v-else-if="playlists.length === 0" class="empty-state">
      <div class="empty-icon">
        <SakuraIcon v-if="isIconName(emptyIcon)" :name="emptyIcon" :size="48" />
        <span v-else>{{ emptyIcon }}</span>
      </div>
      <h3>{{ emptyTitle }}</h3>
      <p>{{ emptyMessage }}</p>
      <button
        v-if="activeTab === 'my'"
        @click="router.push('/playlists/create')"
        class="btn-create-empty"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        Создать первый плейлист
      </button>
    </div>

    <div v-else class="playlists-grid" :aria-busy="loading">
      <PlaylistCard
        v-for="playlist in playlists"
        :key="playlist.id"
        :playlist="playlist"
        :current-user-id="currentUserId"
        :is-favorite="playlist.is_favorited"
        @click="goToPlaylist"
        @favoriteToggle="handleFavoriteToggle"
        @share="handleShare"
        @edit="handleEdit"
        @delete="handleDelete"
      />
    </div>

    <p v-if="loading && playlists.length" class="refresh-note" role="status">Обновляем подборки…</p>
    <div v-if="totalPages > 1" class="pagination">
      <button
        @click="changePage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="page-btn"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
      <div class="page-numbers">
        <button
          v-for="p in visiblePages"
          :key="p"
          @click="p !== '...' && changePage(p as number)"
          :class="[
            'page-num',
            { active: p === currentPage, dots: p === '...' },
          ]"
        >
          {{ p }}
        </button>
      </div>
      <button
        @click="changePage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="page-btn"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>
    </div>

    <Teleport to="body">
      <transition name="toast">
        <div v-if="toastMessage" class="toast-notification">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
          {{ toastMessage }}
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import apiClient from "@/api/client";
import { useCachedReads } from '@/composables/useCachedReads';
const read = useCachedReads();
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import playlistsApi, { type Playlist } from "@/api/playlists";
import PlaylistCard, { type Playlist as PlaylistCardPlaylist } from "@/components/Cards/PlaylistCard.vue";
import type { AxiosError } from "axios";

import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { TIMING } from "@/constants";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

type MainTab = "my" | "public" | "favorites";
type MySubTab = "all" | "public" | "private" | "link";

const playlists = ref<Playlist[]>([]);
const loading = ref(false);
const error = ref("");
const activeTab = ref<MainTab>("my");
const mySubTab = ref<MySubTab>("all");
const searchQuery = ref("");
const sortBy = ref("-updated_at");
const currentPage = ref(1);
const totalCount = ref(0);
const pageSize = 12;
const currentUserId = computed(() => authStore.user?.id);
const publicSort = ref("-likes_count");
const period = ref("all");
const resetDiscovery = () => { searchQuery.value = ""; publicSort.value = "-likes_count"; period.value = "all"; };
const toastMessage = ref("");

const myAllCount = ref(0);
const myPublicCount = ref(0);
const myPrivateCount = ref(0);
const myLinkCount = ref(0);
const favCount = ref(0);

let requestVersion = 0;
let disposed = false;
let restoring = false;
let searchTimeout: ReturnType<typeof setTimeout> | null = null;

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize));

const mainTabs = computed(() => [
  { id: "my", label: "Мои плейлисты", icon: "folder", count: myAllCount.value },
  { id: "public", label: "Публичные", icon: "globe", count: undefined },
  { id: "favorites", label: "Избранное", icon: "star", count: favCount.value },
]);

const isIconName = (icon: string | undefined): boolean => {
  if (!icon) return false;
  return /^[a-zA-Z][a-zA-Z0-9-]*$/.test(icon);
};

const mySubTabs = computed(() => [
  { id: "all", label: "Все", count: myAllCount.value },
  { id: "public", label: "Публичные", count: myPublicCount.value },
  { id: "private", label: "Приватные", count: myPrivateCount.value },
  { id: "link", label: "По ссылке", count: myLinkCount.value },
]);

const visiblePages = computed(() => {
  const pages: (number | string)[] = [];
  const total = totalPages.value;
  const current = currentPage.value;
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i);
  } else {
    pages.push(1);
    if (current > 3) pages.push("...");
    for (
      let i = Math.max(2, current - 1);
      i <= Math.min(total - 1, current + 1);
      i++
    )
      pages.push(i);
    if (current < total - 2) pages.push("...");
    pages.push(total);
  }
  return pages;
});

const emptyIcon = computed(() => {
  if (activeTab.value === "favorites") return "star";
  if (activeTab.value === "public") return "globe";
  if (mySubTab.value === "private") return "lock";
  if (mySubTab.value === "link") return "link";
  return "folder";
});
const emptyTitle = computed(() => {
  if (searchQuery.value) return "Ничего не найдено";
  if (activeTab.value === "favorites") return "Нет избранных плейлистов";
  if (activeTab.value === "public") return "Нет публичных плейлистов";
  if (mySubTab.value === "private") return "Нет приватных плейлистов";
  if (mySubTab.value === "link") return "Нет плейлистов «по ссылке»";
  return "У вас пока нет плейлистов";
});
const emptyMessage = computed(() => {
  if (searchQuery.value) return "Попробуйте изменить запрос";
  if (activeTab.value === "favorites")
    return "Добавляйте понравившиеся плейлисты в избранное";
  if (activeTab.value === "public")
    return "Пока никто не создал публичных плейлистов";
  return "Создайте первый плейлист и добавьте любимое аниме";
});

const buildParams = () => {
  const params: Record<string, string | number | boolean> = {
    page: currentPage.value,
    page_size: pageSize,
    ordering: activeTab.value === "public" ? publicSort.value : sortBy.value,
  };
  if (searchQuery.value.trim()) params.search = searchQuery.value.trim();
  if (activeTab.value === 'public') {
    params.period = period.value;
  }
  return params;
};

const loadPlaylists = async () => {
  const version = ++requestVersion;
  loading.value = true;
  error.value = "";
  try {
    const params: Record<string, string | number | boolean> = buildParams();
    if (activeTab.value === 'my') {
      params.my = true;
      if (mySubTab.value !== 'all') params.visibility = mySubTab.value;
    } else if (activeTab.value === 'public') params.is_public = true;
    else params.favorites = true;
    const { data } = await playlistsApi.getAllPlaylists(params);
    if (version !== requestVersion || disposed) return;
    playlists.value = data.results;
    totalCount.value = data.count;
  } catch (err) {
    if (version !== requestVersion || disposed) return;
    const axiosError = err as AxiosError;
    error.value =
      (axiosError.response?.data as { detail?: string } | undefined)?.detail || "Не удалось загрузить плейлисты";
  } finally {
    if (version === requestVersion && !disposed) loading.value = false;
  }
};

const loadCounts = async () => {
  try {
    await read(['playlist-counts'], async () => (await apiClient.get('/playlists/playlists/counts/')).data, data => {
      myAllCount.value = data.all; myPublicCount.value = data.public;
      myPrivateCount.value = data.private; myLinkCount.value = data.link; favCount.value = data.favorites;
    });
  } catch { /* A failed refresh keeps previously displayed counts. */ }
};

const switchMainTab = (tab: string) => {
  activeTab.value = tab as MainTab;
};

const switchMySubTab = (sub: string) => {
  mySubTab.value = sub as MySubTab;
};

const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  window.scrollTo({ top: 0, behavior: "smooth" });
};

const goToPlaylist = (playlist: PlaylistCardPlaylist) => {
  router.push({ path: `/playlist/${playlist.id}`, query: { returnTo: route.fullPath } });
};

const handleFavoriteToggle = async (
  playlistId: number | string,
  isFavorite: boolean,
) => {
  const playlist = playlists.value.find((p) => p.id === playlistId);
  if (!playlist) return;
  if (!authStore.isAuthenticated) { await router.push({ path: "/login", query: { redirect: route.fullPath } }); return; }
  try {
    if (isFavorite) {
      await playlistsApi.addPlaylistToFavorites(playlistId);
      playlist.is_favorited = true;
      playlist.favorites_count++;
      showToast("Плейлист добавлен в избранное");
    } else {
      await playlistsApi.removePlaylistFromFavorites(playlistId);
      playlist.is_favorited = false;
      playlist.favorites_count = Math.max(0, playlist.favorites_count - 1);
      showToast("Плейлист убран из избранного");
      if (activeTab.value === "favorites") {
        playlists.value = playlists.value.filter((p) => p.id !== playlistId);
        totalCount.value = Math.max(0, totalCount.value - 1);
      }
    }
    loadCounts();
  } catch {}
};

const handleShare = async (playlistId: number | string) => {
  const playlist = playlists.value.find((p) => p.id === playlistId);
  if (!playlist) return;

  try {
    if (playlist.visibility === "link" || playlist.share_token) {
      const res = await playlistsApi.generateShareLink(playlistId);
      const url =
        res.data.share_url ||
        `${window.location.origin}/playlist/shared/${res.data.token}`;
      await navigator.clipboard.writeText(url);
      showToast("Ссылка скопирована в буфер обмена");
    } else {
      const url = `${window.location.origin}/playlist/${playlistId}`;
      await navigator.clipboard.writeText(url);
      showToast("Ссылка скопирована в буфер обмена");
    }
  } catch {
    const url = `${window.location.origin}/playlist/${playlistId}`;
    navigator.clipboard.writeText(url);
    showToast("Ссылка скопирована");
  }
};

const handleEdit = (playlist: PlaylistCardPlaylist) => {
  router.push(`/playlists/${playlist.id}/edit`);
};

const handleDelete = async (playlist: PlaylistCardPlaylist) => {
  const title = (playlist as { title?: string }).title || "плейлист";
  if (!confirm(`Удалить «${title}»?`)) return;
  try {
    await playlistsApi.deletePlaylist(playlist.id);
    playlists.value = playlists.value.filter((p) => p.id !== playlist.id);
    totalCount.value = Math.max(0, totalCount.value - 1);
    loadCounts();
    showToast("Плейлист удалён");
  } catch (err: unknown) {
    console.error(err);
  }
};

const showToast = (msg: string) => {
  toastMessage.value = msg;
  setTimeout(() => {
    toastMessage.value = "";
  }, 3000);
};

const syncLocation = () => {
  if (disposed) return;
  const query: Record<string, string> = {
    tab: activeTab.value, sub: mySubTab.value, page: String(currentPage.value),
    search: searchQuery.value, sort: sortBy.value, publicSort: publicSort.value,
    period: period.value,
  };
  if (JSON.stringify(route.query) !== JSON.stringify(query)) void router.replace({ query });
};
watch([activeTab, mySubTab, sortBy, publicSort, period], () => {
  if (restoring) return;
  ++requestVersion;
  currentPage.value = 1;
  if (searchTimeout) clearTimeout(searchTimeout);
  syncLocation();
}, { deep: true });
watch(searchQuery, () => {
  if (restoring) return;
  ++requestVersion; // Invalidate immediately, before the debounce elapses.
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => { currentPage.value = 1; syncLocation(); }, TIMING.DEBOUNCE_SEARCH);
});
watch(currentPage, () => { if (!restoring) syncLocation(); });
watch(() => route.query, async query => {
  restoring = true;
  if (searchTimeout) clearTimeout(searchTimeout);
  const str = (key: string, fallback = '') => typeof query[key] === 'string' ? query[key] as string : fallback;
  activeTab.value = ['my', 'public', 'favorites'].includes(str('tab')) ? str('tab') as MainTab : authStore.isAuthenticated ? 'my' : 'public';
  mySubTab.value = ['all', 'public', 'private', 'link'].includes(str('sub')) ? str('sub') as MySubTab : 'all';
  searchQuery.value = str('search');
  sortBy.value = str('sort', '-updated_at');
  publicSort.value = ['-likes_count', '-created_at', '-updated_at', 'title'].includes(str('publicSort')) ? str('publicSort') : '-likes_count';
  period.value = ['week', 'month', 'all'].includes(str('period')) ? str('period') : 'all';
  currentPage.value = Math.max(1, Math.floor(Number(str('page', '1'))) || 1);
  await nextTick();
  restoring = false;
  void loadPlaylists();
}, { immediate: true });
watch(() => authStore.user?.id, () => { void loadPlaylists(); if (authStore.isAuthenticated) void loadCounts(); });
onMounted(() => { if (authStore.isAuthenticated) void loadCounts(); });
onBeforeUnmount(() => { disposed = true; ++requestVersion; if (searchTimeout) clearTimeout(searchTimeout); });
</script>

<style scoped>
.refresh-note { color: var(--text-secondary); font-size: .8rem; margin: .75rem 0; }

.playlists-page {
  padding: var(--space-6) var(--space-5) var(--space-16);
  max-width: 1440px;
  margin: 0 auto;
  min-height: 100vh;
}

/* ─── Шапка ─── */
.page-header {
  margin-bottom: 1.25rem;
}
.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}
.page-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}
.btn-create {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.65rem 1.1rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg, 0.625rem);
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.btn-create:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

/* ─── Основные вкладки ─── */
.tabs-row {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0;
}
.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.65rem 1rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: -1px;
  white-space: nowrap;
}
.tab-btn:hover {
  color: var(--text-primary);
}
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}
.tab-icon {
  font-size: 0.95rem;
  color: inherit;
}
.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: var(--surface-4);
  border-radius: 999px;
  font-size: 0.67rem;
  font-weight: 700;
  color: var(--text-tertiary);
}
.tab-btn.active .tab-count {
  background: rgba(58, 134, 255, 0.15);
  color: var(--accent);
}

/* ─── Подвкладки «Мои» ─── */
.subtabs-row {
  display: flex;
  gap: 0.4rem;
  padding: 1.5rem 0 0 0.5rem;
  flex-wrap: wrap;
}
.subtab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.75rem;
  background: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.subtab-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}
.subtab-btn.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.subtab-count {
  font-size: 0.65rem;
  opacity: 0.75;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  padding: 0 4px;
  min-width: 14px;
  text-align: center;
}
.subtab-btn:not(.active) .subtab-count {
  background: var(--surface-3);
  color: var(--text-tertiary);
}

/* Цветные точки видимости */
.vis-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-public {
  background: #22c55e;
}
.dot-private {
  background: #ef4444;
}
.dot-link {
  background: #3a86ff;
}
.dot-all {
  background: var(--text-tertiary);
}
.subtab-btn.active .vis-dot {
  background: rgba(255, 255, 255, 0.8);
}

/* Анимация подвкладок */
.subtabs-enter-active,
.subtabs-leave-active {
  transition: all 0.2s;
}
.subtabs-enter-from,
.subtabs-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ─── Фильтры ─── */
.filters-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  align-items: center;
}
.search-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon-svg {
  position: absolute;
  left: 0.75rem;
  color: var(--text-tertiary);
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 0.65rem 2.25rem 0.65rem 2.5rem;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg, 0.625rem);
  font-size: 0.875rem;
  color: var(--text-primary);
  background: var(--surface-3);
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}
.search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}
.search-clear-btn {
  position: absolute;
  right: 0.65rem;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 50%;
  transition: all 0.15s;
}
.search-clear-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}
.sort-select {
  padding: 0.65rem 0.875rem;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg, 0.625rem);
  font-size: 0.85rem;
  color: var(--text-primary);
  background: var(--surface-3);
  outline: none;
  cursor: pointer;
}
.sort-select:focus {
  border-color: var(--accent);
}

/* ─── Сетка ─── */
.playlists-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1rem;
  grid-auto-rows: 1fr;          /* ← все строки одинаковой высоты */
  align-items: stretch;         /* ← карточки растягиваются на всю ячейку */
}
/* ─── Скелетоны ─── */
.skeleton-card {
  background: var(--surface-3);
  border-radius: var(--radius-card);
  overflow: hidden;
  animation: shimmer 1.5s infinite;
}
.skeleton-cover {
  width: 100%;
  aspect-ratio: 2 / 3;
  flex: none;
  background: var(--surface-4);
}
.skeleton-info {
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}
.skeleton-line {
  height: 11px;
  background: var(--surface-4);
  border-radius: 6px;
}
.w-70 {
  width: 70%;
}
.w-40 {
  width: 40%;
}
.w-55 {
  width: 55%;
}
@keyframes shimmer {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* ─── Пустое состояние ─── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  gap: 0.65rem;
}
.empty-icon {
  font-size: 3.5rem;
  margin-bottom: 0.25rem;
}
.empty-state h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.empty-state p {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0 0 0.75rem;
}
.btn-retry,
.btn-create-empty {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.65rem 1.25rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-retry:hover,
.btn-create-empty:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

/* ─── Пагинация ─── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 2rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border-subtle);
}
.page-btn {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}
.page-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}
.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.page-numbers {
  display: flex;
  gap: 0.2rem;
}
.page-num {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.page-num:hover:not(.dots) {
  border-color: var(--accent);
  color: var(--accent);
}
.page-num.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.page-num.dots {
  cursor: default;
  border: none;
  background: transparent;
}

/* ─── Toast ─── */
.toast-notification {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.65rem 1.1rem;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 2rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  z-index: 9999;
  white-space: nowrap;
}
.toast-notification svg {
  color: #22c55e;
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* ─── Responsive ─── */
@media (max-width: 767px) {
  .playlists-page {
    padding: var(--space-4) var(--space-3) var(--space-10);
  }
  .header-top {
    flex-direction: column;
    align-items: stretch;
  }
  .btn-create {
    justify-content: center;
  }
  .page-title {
    font-size: 1.3rem;
  }
  .tabs-row {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .filters-bar {
    flex-direction: column;
  }
  .sort-select {
    width: 100%;
  }
  .playlists-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
  }
}
@media (max-width: 413px) { .playlists-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 374px) { .playlists-grid { gap: 0.5rem; } }
.public-controls { display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: end; min-width: 0; }
.filters-bar.public-discovery { display: grid; grid-template-columns: minmax(0, 1fr); align-items: stretch; }
.public-discovery .search-wrapper { width: 100%; min-width: 0; }
.public-controls > label { display: flex; flex-direction: column; gap: 0.3rem; color: var(--text-secondary); font-size: 0.75rem; flex: 1; min-width: 0; }
.public-controls .sort-select { width: 100%; min-width: 0; max-width: 100%; }
.filters-bar { flex-wrap: wrap; align-items: end; }
.search-wrapper { min-width: 0; }
.discovery-filters { flex-basis: 100%; color: var(--text-primary); }
.discovery-filters summary { padding: 0.7rem; border: 1px solid var(--border-strong); border-radius: var(--radius-lg); cursor: pointer; font-size: 0.85rem; background: var(--surface-3); }
.filter-options { display: grid; gap: 0.75rem; padding: 0.75rem 0; }
.filter-options fieldset { border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); min-width: 0; display: flex; flex-wrap: wrap; gap: 0.5rem; padding: 0.6rem; }
.filter-options label { display: inline-flex; gap: 0.35rem; align-items: center; font-size: 0.8rem; min-height: 36px; }
.filter-options input { accent-color: var(--accent); }
.active-filters { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; margin: 0 0 1rem; color: var(--text-secondary); font-size: 0.8rem; }
.active-filters button { background: var(--surface-3); color: var(--text-primary); border: 1px solid var(--border-strong); border-radius: 999px; padding: 0.45rem 0.65rem; max-width: 100%; overflow-wrap: anywhere; }
.playlists-page :focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
@media (max-width: 767px) { .public-controls { width: 100%; } .tabs-row { flex-wrap: wrap; } .tab-btn { padding: 0.65rem 0.5rem; font-size: 0.8rem; } }
</style>

<style src="../../Cards/catalogCardGeometry.css"></style>
