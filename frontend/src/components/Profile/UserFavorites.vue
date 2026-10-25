<template>
  <div class="user-favorites">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка избранного...</p>
    </div>
    <div v-else-if="items.length === 0" class="empty">
      <svg
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path
          d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
        />
      </svg>
      <p>Избранное пусто</p>
    </div>
    <div v-else class="favorites-grid">
      <template v-for="item in items" :key="collectionItemKey(item)">
        <FranchiseCard
          v-if="isFavoriteFranchiseItem(item)"
          :franchise="item.franchise"
          @click="openFranchise(item.franchise)"
          @watch="openFranchise(item.franchise)"
          @favorite-toggle="loadFavorites"
        />
        <AnimeCard
          v-else
          :anime="transformLibraryItemToAnimeCard(item)"
          :watch-status="transformLibraryItemToAnimeCard(item).watchStatus"
          :watch-progress="transformLibraryItemToAnimeCard(item).watchProgress"
          :total-episodes="transformLibraryItemToAnimeCard(item).totalEpisodes"
          :show-progress="true"
          :show-actions="true"
          :show-genres="true"
          :max-genres="3"
          :showProgressText="true"
          @favorite-toggle="loadFavorites"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import LoadingSpinner from "@/components/ui/LoadingSpinner.vue";
import AnimeCard from "@/components/Cards/AnimeCard.vue";
import FranchiseCard from "@/components/Cards/FranchiseCard.vue";
import apiClient from "@/api/client";
import {
  isFavoriteFranchiseItem,
  type CollectionItem,
  type FavoriteFranchiseCollectionItem,
  type LibraryItem,
} from "@/api/library";

interface AnimeCardData {
  id: number;
  slug?: string;
  title_ru: string;
  title_en: string;
  poster: string | null;
  poster_url?: string | null;
  poster_image_url?: string | null;
  year?: number | null;
  score?: number | null;
  status: string;
  type?: string;
  kind?: string;
  episodes?: number | null;
  genres: { id: number; name: string; slug: string }[];
  watchStatus: "watching" | "completed" | "planned" | "dropped" | "onhold";
  watchProgress: number;
  totalEpisodes: number;
  showProgress: boolean;
}

const props = defineProps<{
  userId: number;
}>();

const loading = ref(true);
const items = ref<CollectionItem[]>([]);
const router = useRouter();

const collectionItemKey = (item: CollectionItem) =>
  isFavoriteFranchiseItem(item) ? `franchise-${item.franchise_id}` : `anime-${item.id}`;

const openFranchise = (franchise: FavoriteFranchiseCollectionItem["franchise"]) => {
  router.push(`/franchise/${franchise.slug || franchise.id}`);
};

const mapLibraryStatusToWatchStatus = (
  status: string,
): "watching" | "completed" | "planned" | "dropped" | "onhold" => {
  switch (status) {
    case "started":
      return "watching";
    case "completed":
      return "completed";
    case "planned":
      return "planned";
    case "dropped":
      return "dropped";
    case "on_hold":
      return "onhold";
    default:
      return "planned";
  }
};

const transformLibraryItemToAnimeCard = (item: LibraryItem): AnimeCardData => {
  const baseAnime = {
    id: item.anime_id,
    slug: item.anime_slug,
    title_ru: item.anime_title_ru || "",
    title_en: item.anime_title_en || "",
    poster: item.anime_poster || null,
    poster_url: item.anime_poster || null,
    poster_image_url: item.anime_poster || null,
    year: item.anime_year || null,
    score: item.anime_score || null,
    status: item.anime_status || "",
    type: item.anime_kind || "",
    episodes: item.anime_episodes_count || 0,
    genres: item.anime_genres || [],
  };

  const anime =
    item.anime && typeof item.anime === "object"
      ? {
          ...item.anime,
          slug: item.anime.slug || item.anime_slug,
          genres:
            item.anime_genres?.length
              ? item.anime_genres
              : item.anime.genres || [],
        }
      : baseAnime;

  const rawGenres = anime.genres || [];
  let genres: { id: number; name: string; slug: string }[];
  if (Array.isArray(rawGenres) && rawGenres.length > 0 && typeof rawGenres[0] === "string") {
    const stringGenres = (rawGenres as Array<string | { id: number; name: string; slug: string }>).filter(
      (genre): genre is string => typeof genre === "string",
    );
    genres = stringGenres.map((genre: string, index: number) => ({
      id: index,
      name: genre,
      slug: genre.toLowerCase().replace(/ /g, "-"),
    }));
  } else {
    genres = rawGenres as unknown as { id: number; name: string; slug: string }[];
  }

  return {
    ...anime,
    poster: anime.poster ?? null,
    status: anime.status || "",
    genres,
    watchStatus: mapLibraryStatusToWatchStatus(item.status),
    watchProgress: item.current_episode || 0,
    totalEpisodes: item.anime_episodes_count || 0,
    showProgress: item.status === "started" && (item.current_episode || 0) > 0,
  };
};

const loadFavorites = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get(
      `/users/library/?user_id=${props.userId}&is_favorite=true&group_franchises=true&page_size=100`,
    );
    const rows: CollectionItem[] = response.data.results || response.data || [];
    items.value = rows;
  } catch (error) {
    console.error("Error loading favorites:", error);
    items.value = [];
  } finally {
    loading.value = false;
  }
};

watch(
  () => props.userId,
  () => {
    loadFavorites();
  },
  { immediate: true },
);
</script>

<style scoped>
.user-favorites {
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

.empty svg {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
</style>
