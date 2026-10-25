<template>
  <div class="user-anime-collection">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка коллекции...</p>
    </div>
    <div v-else-if="animeList.length === 0" class="empty">
      <p>Коллекция пуста</p>
    </div>
    <div v-else class="anime-grid">
      <AnimeCard
        v-for="anime in animeList"
        :key="anime.id"
        :anime="anime"
        :watch-status="anime.watchStatus"
        :watch-progress="anime.watchProgress"
        :total-episodes="anime.totalEpisodes"
        :show-progress="true"
        :show-actions="true"
        :show-genres="true"
        :max-genres="3"
        :showProgressText="true"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import apiClient from "@/api/client";
import LoadingSpinner from "@/components/ui/LoadingSpinner.vue";
import AnimeCard from "@/components/Cards/AnimeCard.vue";
import type { LibraryItem } from "@/api/library";

interface Props {
  userId: number;
}

const props = defineProps<Props>();

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

const loading = ref(true);
const animeList = ref<AnimeCardData[]>([]);

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
    title_ru: item.anime_title_ru,
    title_en: item.anime_title_en,
    poster: item.anime_poster,
    poster_url: item.anime_poster,
    poster_image_url: item.anime_poster,
    year: item.anime_year,
    score: item.anime_score,
    status: item.anime_status,
    type: item.anime_kind,
    episodes: item.anime_episodes_count,
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
    watchProgress: item.current_episode || item.episodes_watched || 0,
    totalEpisodes: item.anime_episodes_count || anime.episodes || 0,
    showProgress:
      item.status === "started" &&
      (item.current_episode || item.episodes_watched) > 0,
  };
};

const loadAnimeCollection = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get(
      `/users/library/?user_id=${props.userId}`,
    );
    const libraryItems =
      response.data.results || response.data.library || response.data || [];
    animeList.value = libraryItems.map(transformLibraryItemToAnimeCard);
  } catch {
    animeList.value = [];
  } finally {
    loading.value = false;
  }
};

watch(
  () => props.userId,
  () => {
    loadAnimeCollection();
  },
  { immediate: true },
);
</script>

<style scoped>
.user-anime-collection {
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

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
</style>
