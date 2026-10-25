<template>
  <div class="user-public-playlists">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка плейлистов...</p>
    </div>
    <div v-else-if="playlists.length === 0" class="empty">
      <p>Нет публичных плейлистов</p>
    </div>
    <div v-else class="playlists-grid">
      <PlaylistCard
        v-for="playlist in playlists"
        :key="playlist.id"
        :playlist="playlist"
        :current-user-id="currentUserId"
        @favorite-toggle="toggleFavorite"
        @share="openShareModal"
        @edit="openEditModal"
        @delete="confirmDelete"
      />
    </div>
    <div v-if="hasMore" class="load-more-row">
      <button class="load-more-btn" type="button" :disabled="loadingMore" @click="loadMore">
        {{ loadingMore ? "Загрузка..." : "Показать ещё" }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { useAuthStore } from "@/stores/auth"
import LoadingSpinner from "@/components/ui/LoadingSpinner.vue"
import PlaylistCard, { type Playlist as PlaylistCardPlaylist } from "@/components/Cards/PlaylistCard.vue"
import apiClient from "@/api/client"
import { useRouter } from "vue-router"
import playlistsApi, { type Playlist } from "@/api/playlists"
interface Props {
  userId: number;
}

const props = defineProps<Props>();
const authStore = useAuthStore();
const router = useRouter();

const loading = ref(true);
const loadingMore = ref(false);
const playlists = ref<Playlist[]>([]);
const page = ref(1);
const total = ref(0);
const pageSize = 12;
let requestGeneration = 0;
let requestController: AbortController | undefined;
const currentUserId = computed(() => authStore.user?.id);
const hasMore = computed(() => playlists.value.length < total.value);

const loadUserPlaylists = async (nextPage = 1, append = false) => {
  const generation = ++requestGeneration;
  requestController?.abort();
  requestController = new AbortController();
  if (append) loadingMore.value = true;
  else loading.value = true;
  try {
    const response = await apiClient.get(`/playlists/playlists/`, {
      params: {
        user: props.userId,
        visibility: "public",
        ordering: "-updated_at",
        page: nextPage,
        page_size: pageSize,
      },
      signal: requestController.signal,
    });
    if (generation !== requestGeneration) return;

    const rawData = response.data;

    let dataArray: unknown[] = [];

    if (Array.isArray(rawData)) {
      dataArray = rawData;
    } else if (rawData?.results) {
      dataArray = rawData.results;
    } else {
      dataArray = [];
    }

    const rows = dataArray.filter(
      (p): p is Playlist => !!p && (typeof (p as Record<string, unknown>).id === "number" || typeof (p as Record<string, unknown>).id === "string"),
    );
    playlists.value = append ? [...playlists.value, ...rows] : rows;
    page.value = nextPage;
    total.value = Number(rawData?.count ?? rows.length);
  } catch (error: unknown) {
    if (generation !== requestGeneration) return;
    console.error("Error loading playlists:", error);
    if (!append) playlists.value = [];
  } finally {
    if (generation === requestGeneration) {
      loading.value = false;
      loadingMore.value = false;
    }
  }
};

const loadMore = () => {
  if (hasMore.value && !loadingMore.value) void loadUserPlaylists(page.value + 1, true);
};

const toggleFavorite = async (playlistId: number | string, favorite: boolean) => {
  try {
    if (favorite) await playlistsApi.addPlaylistToFavorites(playlistId);
    else await playlistsApi.removePlaylistFromFavorites(playlistId);
    await loadUserPlaylists(1);
  } catch (error) {
    console.error("Error toggling favorite:", error);
  }
};

const openShareModal = async (playlistId: number | string) => {
  const url = `${window.location.origin}/playlists/${playlistId}`;
  if (navigator.share) {
    try {
      await navigator.share({
        title: "Плейлист",
        url: url,
      });
    } catch (error) {
      console.log("Error sharing:", error);
      copyToClipboard(url);
    }
  } else {
    copyToClipboard(url);
  }
};

const openEditModal = (playlist: PlaylistCardPlaylist) => {
  router.push(`/playlists/${playlist.id}/edit`);
};

const copyToClipboard = (text: string) => {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      alert("Ссылка скопирована в буфер обмена");
    })
    .catch(() => {
      alert(`Ссылка: ${text}`);
    });
};

const confirmDelete = async (playlist: PlaylistCardPlaylist) => {
  if (!confirm(`Удалить плейлист "${playlist.title}"?`)) return;

  try {
    await apiClient.delete(`/playlists/playlists/${playlist.id}/`);
    playlists.value = playlists.value.filter((p) => p.id !== playlist.id);
  } catch (error) {
    console.error("Error deleting playlist:", error);
  }
};

watch(
  () => props.userId,
  (newUserId) => {
    if (newUserId && !isNaN(newUserId)) {
      loadUserPlaylists();
    } else {
      playlists.value = [];
    }
  },
  { immediate: true },
);
</script>
<style scoped>
.user-public-playlists {
  min-height: 400px;
}

.loading,
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--text-secondary);
}

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  grid-auto-rows: 1fr;
  align-items: stretch;
}
.load-more-row { display: flex; justify-content: center; margin-top: 20px; }
.load-more-btn { padding: 10px 20px; border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-3); color: var(--text-primary); cursor: pointer; }
.load-more-btn:disabled { opacity: .6; cursor: wait; }
</style>
