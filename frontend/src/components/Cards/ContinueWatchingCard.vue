<template>
  <div class="cwc-wrap">
    <AnimeCard
      :anime="cardAnime"
      :show-actions="true"
      :show-genres="genresList.length > 0"
      :max-genres="3"
      :show-progress="false"
      :show-progress-text="false"
      :watch-progress="currentEpisode"
      :total-episodes="totalEpisodes"
      @click="handleClick"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import { useRouter } from "vue-router"
import AnimeCard from "./AnimeCard.vue"
interface Props {
  animeId: number;
  title: string;
  poster: string;
  currentEpisode: number;
  totalEpisodes: number;
  status?: string;
  genres?: string[] | string;
  year?: number | null;
  rating?: number | null;
}

const props = defineProps<Props>();

const router = useRouter();

const genresList = computed<string[]>(() => {
  const g = props.genres;
  if (!g) return [];
  return Array.isArray(g)
    ? g
    : g
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
});

const cardAnime = computed(() => ({
  id: props.animeId,
  title_ru: props.title,
  title_en: "",
  year: props.year ?? null,
  status: props.status || "",
  episodes: props.totalEpisodes || null,
  score: props.rating ?? null,
  poster_url: props.poster || null,
  poster_image_url: props.poster || null,
  poster: null,
  type: "",
  genres: genresList.value.map((g, i) => ({ id: i, name: g, slug: g })),
}));

const handleClick = () => {
  router.push(`/anime/${props.animeId}/watch?episode=${props.currentEpisode}`);
};
</script>

<style scoped>
.cwc-wrap {
  flex: 0 0 auto;
  width: 220px;
  scroll-snap-align: start;
}

@media (max-width: 767px) {
  .cwc-wrap {
    width: 155px;
  }
}
</style>
