<template>
  <div class="rec-view">


    <div class="rec-blocks">
      <RecCarousel
        class="rec-block"
        v-for="block in blocks"
        :key="block.key"
        :title="block.title"
        :description="block.desc"
        :icon="block.icon"
        :anime="blockData[block.key]"
        :defer="block.key !== blocks[0]?.key"
        :windowed="true"
        :loading="isPending"
        :has-view-all="!!block.route"
        @view-all="goToViewAll(block)"
      >
        <template #card="{ item, index }">
          <RecommendationCard
            :anime-id="item.id"
            :anime-slug="String(item.slug || item.id || '')"
            :title="item.title"
            :poster="item.poster || ''"
            :genres="item.genres || []"
            :rating="item.score ? parseFloat(item.score) : null"
            :rating-count="0"
            :status="item.status || ''"
            :year="item.year || null"
            :episodes="item.episodes ?? null"
            :type="item.type || ''"
            :reason="item.reason || undefined"
            :priority="block.key === blocks[0]?.key && index < 6"
          />
        </template>
      </RecCarousel>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onActivated, onDeactivated } from "vue";
import { useQuery } from "@tanstack/vue-query";
import { useRouter } from "vue-router";
import apiClient from "@/api/client";
import { useAuthStore } from "@/stores/auth";
import RecCarousel from "@/components/Cards/RecCarousel.vue";
import RecommendationCard from "@/components/Cards/RecommendationCard.vue";

type BlockKey =
  | "top_rated"
  | "new_season"
  | "classics"
  | "based_on_watched"
  | "explore_new"
  | "short"
  | "movies"
  | "seasonal";

interface Block {
  key: BlockKey;
  title: string;
  desc: string;
  icon: string;
  route?: string;
}

interface AnimeItem {
  id: number;
  title: string;
  poster: string | null;
  year: number | null;
  score: string | null;
  genres: string[];
  status: string;
  reason?: string;
  type?: string;
  episodes?: number | null;
}

const router = useRouter();
const authStore = useAuthStore();
const active = ref(true);
onActivated(() => { active.value = true; });
onDeactivated(() => { active.value = false; });

const blocks: Block[] = [
  { key: "top_rated", title: "Топ аниме", desc: "Лучшее по рейтингу сообщества", icon: "trophy", route: "/anime?ordering=-score" },
  { key: "new_season", title: "Новинки", desc: "Аниме за последний год и онгоинги", icon: "sparkles", route: "/anime?ordering=-year" },
  { key: "based_on_watched", title: "На основе просмотренного", desc: "Похожее на то, что вы уже смотрели", icon: "target" },
  { key: "classics", title: "Классика", desc: "Легендарные тайтлы до 2010 года", icon: "scroll", route: "/anime?ordering=-score&year_to=2010" },
  { key: "short", title: "Короткие аниме", desc: "Франшизы до 2 частей и 24 серий суммарно", icon: "zap" },
  { key: "movies", title: "Полнометражные", desc: "Только фильмы с высоким рейтингом", icon: "play" },
];

const { data, isPending } = useQuery({
  enabled: active,
  queryKey: computed(() => ['recommendations', String(authStore.user?.id ?? 'guest'), 'reasons-v2']),
  queryFn: async ({ signal }) => (await apiClient.get('/anime/home/personalized/', {
    params: { sections: 'top_rated,new_season,based_on_watched,classics,short,movies' }, signal,
  })).data as Record<string, Record<string, unknown>[]>,
});
const norm = (a: Record<string, unknown>): AnimeItem => ({
  id: Number(a.id ?? a.anime_id),
  title: String(a.title_ru || a.title || a.title_en || 'Без названия'),
  poster: String(a.poster_image_url || a.poster_url || a.poster || '') || null,
  year: a.year as number | null,
  score: a.score != null || a.rating != null ? String(a.score ?? a.rating) : null,
  genres: Array.isArray(a.genres) ? a.genres as string[] : [],
  status: String(a.status || ''),
  type: String(a.kind || a.type || ''),
  episodes: a.episodes as number | null,
  reason: String(a.reason || ''),
});
const blockData = computed(() => Object.fromEntries(blocks.map(block => [
  block.key, (data.value?.[block.key] || []).map(norm).filter(item =>
    block.key !== 'movies' || (item.type === 'movie' && item.episodes === 1)),
])) as Record<BlockKey, AnimeItem[]>);

const goToViewAll = (block: Block) => {
  if (block.route) router.push(block.route);
};


</script>

<style scoped>
.rec-hero {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
  padding: var(--space-4) 0;
}

.rec-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.rec-hero-text {
  max-width: 640px;
}

.rec-eyebrow {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: var(--space-2);
}

.rec-title {
  font-size: var(--text-3xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: -0.02em;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.rec-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
  max-width: 520px;
}

.rec-refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
  flex-shrink: 0;
}

.rec-refresh-btn:hover:not(:disabled) {
  background: var(--surface-5);
  color: var(--text-primary);
}

.rec-refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rec-blocks {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.rec-block {
  content-visibility: auto;
  contain-intrinsic-size: auto 520px;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
