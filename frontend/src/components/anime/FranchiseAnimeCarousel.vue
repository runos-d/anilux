<template>
  <RecCarousel
    :title="`Франшиза «${name}»`"
    icon="link"
    :anime="carouselEntries"
    :show-view-all-button="true"
    view-all-label="Все"
    @view-all="openFranchise"
  >
    <template #card="{ item }">
      <RecommendationCard
        :anime-id="item.id"
        :anime-slug="String(item.slug || item.id)"
        :title="item.title"
        :poster="item.poster || ''"
        :genres="item.genres || []"
        :rating="item.score == null ? null : Number(item.score)"
        :rating-count="0"
        :status="item.status || ''"
        :year="item.year || null"
        :episodes="item.episodes ?? null"
        :type="item.type || ''"
      />
    </template>
  </RecCarousel>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import RecCarousel from "@/components/Cards/RecCarousel.vue";
import RecommendationCard from "@/components/Cards/RecommendationCard.vue";
import type { FranchiseCarouselEntry } from "@/types/franchise";

const props = defineProps<{
  name: string;
  franchiseId: number;
  franchiseSlug?: string | null;
  currentAnimeId?: number | null;
  entries: FranchiseCarouselEntry[];
}>();

const router = useRouter();
const openFranchise = () => {
  router.push(`/franchise/${props.franchiseSlug || props.franchiseId}`);
};

const carouselEntries = computed(() => props.entries.map((entry) => ({
  id: entry.id,
  slug: entry.slug || entry.anime_slug || String(entry.id),
  title: entry.title_ru || entry.title_en || "—",
  poster: entry.poster_image_url || entry.poster_url || entry.poster || null,
  year: entry.year ?? null,
  score: entry.score == null ? null : String(entry.score),
  genres: (entry.genres || []).map((genre) =>
    typeof genre === "string" ? genre : String(genre.name || ""),
  ).filter(Boolean),
  status: entry.status || "",
  type: entry.kind || "",
  episodes: entry.episodes ?? null,
})));
</script>
