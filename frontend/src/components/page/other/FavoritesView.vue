<script setup lang="ts">
import { useCachedReads } from '@/composables/useCachedReads';
const read = useCachedReads();
import { ref, onMounted, computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";
import playlistsApi, { type Playlist, type FavoritePlaylist } from "@/api/playlists";
import type { AxiosError } from "axios";
import PlaylistCard from "@/components/Cards/PlaylistCard.vue";

const authStore = useAuthStore();
const router = useRouter();

const playlists = ref<Playlist[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const currentUserId = ref<number | undefined>(undefined);

const activeTab = ref<"mine" | "other">("mine");

const searchQuery = ref("");
const sortBy = ref<"created" | "updated" | "name" | "animes">("updated");
const sortOrder = ref<"asc" | "desc">("desc");

const filteredPlaylists = computed(() => {
  let result = [...playlists.value];

  if (activeTab.value === "mine") {
    result = result.filter(
      (p) => p.user && currentUserId.value && p.user.id === currentUserId.value,
    );
  } else {
    result = result.filter(
      (p) =>
        !p.user || !currentUserId.value || p.user.id !== currentUserId.value,
    );
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(
      (p) =>
        p.title.toLowerCase().includes(query) ||
        (p.description && p.description.toLowerCase().includes(query)) ||
        (p.user && p.user.username.toLowerCase().includes(query)),
    );
  }

  result.sort((a, b) => {
    let comparison = 0;

    switch (sortBy.value) {
      case "created":
        comparison =
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        break;
      case "updated":
        comparison =
          new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
        break;
      case "name":
        comparison = a.title.localeCompare(b.title);
        break;
      case "animes":
        comparison = (a.animes_count || 0) - (b.animes_count || 0);
        break;
    }

    return sortOrder.value === "asc" ? comparison : -comparison;
  });

  return result;
});

const stats = computed(() => ({
  mine: playlists.value.filter(
    (p) => p.user && currentUserId.value && p.user.id === currentUserId.value,
  ).length,
  other: playlists.value.filter(
    (p) => !p.user || !currentUserId.value || p.user.id !== currentUserId.value,
  ).length,
}));

const loadFavorites = async () => {
  loading.value = true;
  error.value = null;

  try {
    await read(['favorite-playlists'], async () => (await playlistsApi.getFavoritePlaylists()).data, rows => {
    playlists.value = rows.map((fp) => {
      const data = fp.playlist_data as unknown as Record<string, unknown>;
      return {
        id: (data.id as number) || 0,
        user_id: (data.user_id as number) || 0,
        user_unique_id: undefined,
        user_username: (data.user_username as string) || "",
        user_avatar: (data.user_avatar as string | null) || null,
        user: {
          id: (data.user_id as number) || 0,
          username: (data.user_username as string) || "",
          avatar: (data.user_avatar as string | null) || null,
        },
        title: data.title as string,
        description: data.description as string,
        is_public: data.is_public as boolean,
        visibility: data.is_public ? "public" : ("private" as const),
        is_private: !(data.is_public as boolean),
        is_link_only: false,
        favorites_count: (data.favorites_count as number) || 0,
        likes_count: (data.likes_count as number) || 0,
        is_liked: Boolean(data.is_liked),
        topics: (data.topics as string[]) || [],
        is_favorited: true,
        is_favorite: true,
        created_at: data.created_at as string,
        updated_at: (data.updated_at as string) || "",
        items_count: (data.items_count as number) || 0,
        animes_count: (data.items_count as number) || 0,
        items: [],
        cover_image: (data.cover_image as string) || null,
        cover_urls: (data.cover_urls as string[]) || [],
        genres: [],
      };
    });

    });
    if (authStore.user) {
      currentUserId.value = authStore.user.id;
    }
  } catch (err) {
    const axiosError = err as AxiosError;
    console.error("Ошибка загрузки избранного:", err);
    const detail = (axiosError.response?.data as { detail?: string } | undefined)?.detail;
    error.value = detail || "Не удалось загрузить избранное";
  } finally {
    loading.value = false;
  }
};

const goToPlaylist = (playlist: Playlist) => {
  router.push(`/playlist/${playlist.id}`);
};

const editPlaylist = (playlist: Playlist) => {
  if (activeTab.value === "mine") {
    router.push(`/playlists/${playlist.id}/edit`);
  }
};

const deletePlaylist = async (playlist: Playlist) => {
  if (activeTab.value !== "mine") return;

  if (!confirm(`Удалить плейлист "${playlist.title}"?`)) {
    return;
  }

  try {
    await playlistsApi.deletePlaylist(playlist.id);
    playlists.value = playlists.value.filter((p) => p.id !== playlist.id);
  } catch (err) {
    console.error("Ошибка удаления плейлиста:", err);
    alert("Не удалось удалить плейлист");
  }
};

const duplicatePlaylist = async (playlist: Playlist) => {
  try {
    const response = await playlistsApi.duplicatePlaylist(playlist.id);
    playlists.value.unshift(response.data);
  } catch (err) {
    console.error("Ошибка копирования плейлиста:", err);
    alert("Не удалось скопировать плейлист");
  }
};

const toggleFavorite = async (playlist: Playlist) => {
  try {
    if (playlist.is_favorited) {
      await playlistsApi.removePlaylistFromFavorites(playlist.id);
      playlists.value = playlists.value.filter((p) => p.id !== playlist.id);
    } else {
      await playlistsApi.addPlaylistToFavorites(playlist.id);
      playlist.is_favorited = true;
      playlist.favorites_count++;
    }
  } catch (error) {
    console.error("Ошибка изменения избранного:", error);
  }
};

const togglePrivacy = async (playlist: Playlist) => {
  if (activeTab.value !== "mine") return;

  try {
    const newPrivacy = !playlist.is_public;
    await playlistsApi.updatePlaylist(playlist.id, {
      is_public: newPrivacy,
    });
    playlist.is_public = newPrivacy;
  } catch (error) {
    console.error("Ошибка изменения приватности:", error);
    alert("Не удалось изменить приватность");
  }
};

onMounted(() => {
  loadFavorites();
});
</script>

<template>
  <div class="favorites-page">
    <header class="page-header">
      <h1>Избранное</h1>
      <p class="subtitle">Ваши любимые плейлисты</p>
    </header>

    <div class="tabs-container">
      <div class="tabs">
        <button
          class="tab"
          :class="{ active: activeTab === 'mine' }"
          @click="activeTab = 'mine'"
        >
          Мое <span class="count">({{ stats.mine }})</span>
        </button>
        <button
          class="tab"
          :class="{ active: activeTab === 'other' }"
          @click="activeTab = 'other'"
        >
          Другое <span class="count">({{ stats.other }})</span>
        </button>
      </div>
    </div>

    <div class="filters-container">
      <div class="filters">
        <div class="search-filter">
          <svg
            class="search-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Поиск по названию, описанию или автору..."
            v-model="searchQuery"
            class="search-input"
          />
        </div>

        <div class="sort-filter">
          <select v-model="sortBy" class="sort-select">
            <option value="updated">По дате обновления</option>
            <option value="created">По дате создания</option>
            <option value="name">По названию</option>
            <option value="animes">По количеству аниме</option>
          </select>
          <button
            class="sort-order-btn"
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
            :title="sortOrder === 'asc' ? 'По возрастанию' : 'По убыванию'"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <polyline
                :points="
                  sortOrder === 'asc' ? '19 12 12 5 5 12' : '19 5 12 12 5 5'
                "
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">

      <p>Загрузка...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="loadFavorites">
        Попробовать снова
      </button>
    </div>

    <div v-else-if="filteredPlaylists.length === 0" class="empty-state">
      <span class="icon"> <SakuraIcon name="star" /> </span>
      <h3>
        {{ playlists.length === 0 ? "В избранном пусто" : "Ничего не найдено" }}
      </h3>
      <p>
        {{
          playlists.length === 0
            ? "Добавляйте плейлисты в избранное, чтобы они появились здесь"
            : "Попробуйте изменить параметры фильтрации"
        }}
      </p>
    </div>

    <div v-else class="playlists-grid">
      <PlaylistCard
        v-for="playlist in filteredPlaylists"
        :key="playlist.id"
        :playlist="playlist as any"
        :current-user-id="currentUserId"
        :show-favorite="true"
        :show-edit="activeTab === 'mine'"
        :show-delete="activeTab === 'mine'"
        :show-privacy="activeTab === 'mine'"
        @click="goToPlaylist as any"
        @edit="editPlaylist as any"
        @delete="deletePlaylist as any"
        @duplicate="duplicatePlaylist as any"
        @favorite-toggle="id => { const p = playlists.find(row => row.id === id); if (p) toggleFavorite(p); }"
        @toggle-privacy="togglePrivacy as any"
      />
    </div>
  </div>
</template>

<style scoped>
.favorites-page {
  padding: 2rem 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
}

.tabs-container {
  margin-bottom: 1.5rem;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 2px solid var(--border-subtle);
}

.tab {
  padding: 0.75rem 1.25rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -2px;
}

.tab:hover {
  color: var(--text-primary);
}

.tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tab .count {
  font-size: 0.85rem;
  color: var(--text-tertiary);
  margin-left: 0.25rem;
}

.tab.active .count {
  color: var(--accent);
}

.filters-container {
  margin-bottom: 1.5rem;
}

.filters {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-filter {
  flex: 1;
  min-width: 250px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: 0.5rem;
}

.search-icon {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.95rem;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.sort-filter {
  display: flex;
  gap: 0.5rem;
}

.sort-select {
  padding: 0.75rem 1rem;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: 0.5rem;
  color: var(--text-primary);
  font-size: 0.95rem;
  cursor: pointer;
}

.sort-order-btn {
  padding: 0.75rem;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: 0.5rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.sort-order-btn:hover {
  background: var(--surface-3);
}

.loading {
  text-align: center;
  padding: 4rem 1rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading p {
  color: var(--text-tertiary);
}

.error {
  text-align: center;
  padding: 4rem 1rem;
}

.error p {
  font-size: 1.125rem;
  color: var(--text-tertiary);
  margin-bottom: 1rem;
}

.btn-retry {
  padding: 0.75rem 1.5rem;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-retry:hover {
  background: var(--accent-hover);
}

.empty-state {
  text-align: center;
  padding: 6rem 1rem;
}

.empty-state .icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1.5rem;
}

.empty-state h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
}

.empty-state p {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

@media (max-width: 900px) and (min-width: 769px) {
  .favorites-page {
    padding: 1.5rem 1rem;
  }
  .page-header {
    margin-bottom: 1.5rem;
  }
  h1 {
    font-size: 1.75rem;
  }
  .subtitle {
    font-size: 0.95rem;
  }
  .tab {
    padding: 0.65rem 1.1rem;
    font-size: 0.9rem;
  }
  .tab .count {
    font-size: 0.8rem;
  }
  .filters {
    gap: 0.85rem;
  }
  .search-filter {
    min-width: 220px;
    padding: 0.65rem 0.9rem;
  }
  .search-input {
    font-size: 0.9rem;
  }
  .sort-select {
    padding: 0.65rem 0.9rem;
    font-size: 0.9rem;
  }
  .sort-order-btn {
    padding: 0.65rem;
  }
  .playlists-grid {
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1.25rem;
  }
  .empty-state {
    padding: 5rem 1rem;
  }
}

@media (max-width: 768px) {
  .favorites-page {
    padding: 1.25rem 0.85rem;
  }
  .page-header {
    margin-bottom: 1.25rem;
  }
  h1 {
    font-size: 1.5rem;
  }
  .subtitle {
    font-size: 0.9rem;
  }
  .tabs-container {
    margin-bottom: 1.1rem;
  }
  .tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .tabs::-webkit-scrollbar {
    display: none;
  }
  .tab {
    padding: 0.6rem 1rem;
    font-size: 0.88rem;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .tab .count {
    font-size: 0.78rem;
  }
  .filters-container {
    margin-bottom: 1.1rem;
  }
  .filters {
    flex-direction: column;
    gap: 0.75rem;
  }
  .search-filter {
    min-width: 100%;
    padding: 0.65rem 0.85rem;
  }
  .search-input {
    font-size: 0.9rem;
  }
  .sort-filter {
    width: 100%;
    gap: 0.5rem;
  }
  .sort-select {
    flex: 1;
    padding: 0.65rem 0.85rem;
    font-size: 0.9rem;
  }
  .sort-order-btn {
    padding: 0.65rem 0.85rem;
    flex-shrink: 0;
  }
  .loading,
  .error {
    padding: 3rem 1rem;
  }
  .spinner {
    width: 2.5rem;
    height: 2.5rem;
  }
  .empty-state {
    padding: 4rem 1rem;
  }
  .empty-state .icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
  .empty-state h3 {
    font-size: 1.25rem;
  }
  .empty-state p {
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
  }
  .playlists-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
  }
}

@media (max-width: 480px) {
  .favorites-page {
    padding: 1rem 0.65rem;
  }
  .page-header {
    margin-bottom: 1rem;
  }
  h1 {
    font-size: 1.35rem;
  }
  .subtitle {
    font-size: 0.85rem;
  }
  .tabs-container {
    margin-bottom: 1rem;
  }
  .tab {
    padding: 0.55rem 0.9rem;
    font-size: 0.85rem;
  }
  .tab .count {
    font-size: 0.75rem;
  }
  .filters {
    gap: 0.65rem;
  }
  .search-filter {
    padding: 0.6rem 0.75rem;
    gap: 0.6rem;
  }
  .search-icon {
    width: 14px;
    height: 14px;
  }
  .search-input {
    font-size: 0.85rem;
  }
  .sort-select {
    padding: 0.6rem 0.75rem;
    font-size: 0.85rem;
  }
  .sort-order-btn {
    padding: 0.6rem 0.75rem;
  }
  .sort-order-btn svg {
    width: 14px;
    height: 14px;
  }
  .loading,
  .error {
    padding: 2.5rem 0.75rem;
  }
  .spinner {
    width: 2.2rem;
    height: 2.2rem;
  }
  .empty-state {
    padding: 3rem 0.75rem;
  }
  .empty-state .icon {
    font-size: 2.5rem;
  }
  .empty-state h3 {
    font-size: 1.15rem;
  }
  .empty-state p {
    font-size: 0.85rem;
  }
  .btn-retry {
    padding: 0.65rem 1.25rem;
    font-size: 0.9rem;
  }
  .playlists-grid {
    grid-template-columns: 1fr;
    gap: 0.85rem;
  }
}

@media (max-width: 360px) {
  .favorites-page {
    padding: 0.85rem 0.5rem;
  }
  h1 {
    font-size: 1.2rem;
  }
  .subtitle {
    font-size: 0.8rem;
  }
  .tab {
    padding: 0.5rem 0.8rem;
    font-size: 0.8rem;
  }
  .tab .count {
    font-size: 0.72rem;
  }
  .search-filter {
    padding: 0.55rem 0.65rem;
  }
  .search-input {
    font-size: 0.8rem;
  }
  .sort-select {
    padding: 0.55rem 0.65rem;
    font-size: 0.8rem;
  }
  .sort-order-btn {
    padding: 0.55rem 0.65rem;
  }
  .empty-state {
    padding: 2.5rem 0.5rem;
  }
  .empty-state h3 {
    font-size: 1.05rem;
  }
  .empty-state p {
    font-size: 0.8rem;
  }
  .btn-retry {
    padding: 0.6rem 1.1rem;
    font-size: 0.85rem;
  }
}
</style>