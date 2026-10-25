<template>
  <div class="rwc-wrap">
    <AnimeCard
      :anime="cardAnime"
      :show-actions="true"
      :show-genres="genresList.length > 0"
      :max-genres="3"
      :show-progress="false"
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
  completedDate: string | null;
  userRating: number | null;
  genres?: string[] | string;
  rating?: number | null;
  ratingCount?: number;
  year?: number | null;
  episodes?: number | null;
  status?: string;
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
  episodes: props.episodes ?? null,
  score: props.rating ?? null,
  poster_url: props.poster || null,
  poster_image_url: props.poster || null,
  poster: null,
  type: "",
  genres: genresList.value.map((g, i) => ({ id: i, name: g, slug: g })),
}));

const handleClick = () => {
  router.push(`/anime/${props.animeId}/watch?episode=1`);
};
</script>

<style scoped>
.rwc-wrap {
  flex: 0 0 220px;
  width: 220px;
  scroll-snap-align: start;
}

@media (max-width: 767px) {
  .rwc-wrap {
    flex: 0 0 155px;
    width: 155px;
  }
}
</style>
