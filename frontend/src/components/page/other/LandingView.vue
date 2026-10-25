<template>
  <div class="home-page">
    <div class="welcome-section">
      <div class="welcome-text">
        <h1 class="welcome-title">
          Добро пожаловать<span v-if="userName">, {{ userName }}</span
          >!
        </h1>
        <p class="welcome-subtitle">Что хотите посмотреть сегодня?</p>
      </div>
      <div class="welcome-actions">
        <button class="quick-btn" @click="router.push('/anime')">
          <svg
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
          Каталог
        </button>
      </div>
    </div>

    <template v-if="isLoading">
      <div v-for="n in 2" :key="n" class="skeleton-section">
        <div class="skeleton-header">
          <div class="skeleton-title-bar"></div>
        </div>
        <div class="skeleton-track">
          <div v-for="i in 6" :key="i" class="skeleton-card">
            <div class="skeleton-poster"></div>
            <div class="skeleton-info">
              <div class="skeleton-line w80"></div>
              <div class="skeleton-line w55"></div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="isError" class="error-state">
      <div class="error-icon">
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <p class="error-title">Не удалось загрузить контент</p>
      <p class="error-sub">Проверьте соединение и попробуйте ещё раз</p>
      <button class="retry-btn" @click="retry">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M23 4v6h-6M1 20v-6h6" />
          <path
            d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"
          />
        </svg>
        Повторить
      </button>
    </div>

    <div v-else class="home-content">
      <RecCarousel
        v-if="homeData.continue_watching.length > 0"
        :title="'Продолжить просмотр'"
        :icon="'play'"
        :anime="continueAnime"
      />

      <RecCarousel
        v-if="homeData.rewatch.length > 0"
        :title="'Пересмотреть'"
        :icon="'refresh'"
        :anime="rewatchAnime"
      />

      <RecCarousel
        :title="'Рекомендации для вас'"
        :icon="'target'"
        :anime="recsAnime"
        :has-view-all="recsAnime.length > 0"
        @view-all="router.push('/anime')"
      >
        <template #card="{ item }">
          <RecommendationCard
            :anime-id="item.id"
            :anime-slug="item.slug"
            :title="item.title"
            :poster="item.poster || ''"
            :genres="item.genres || []"
            :rating="toNum(item.score)"
            :rating-count="item.ratingCount || 0"
            :status="item.status || ''"
            :year="item.year || null"
            :episodes="item.episodes ?? null"
            :type="item.type || ''"
          />
          </template>
      </RecCarousel>

      <!-- Секция «Популярное на этой неделе» временно скрыта
      <RecCarousel
        :title="'Популярное на этой неделе'"
        :icon="'fire'"
        :anime="trendAnime"
        :has-view-all="trendAnime.length > 0"
        @view-all="router.push('/anime?ordering=-score')
      >
        <template #card="{ item }">
          <RecommendationCard
            :anime-id="item.id"
            :title="item.title"
            :poster="item.poster"
            :genres="item.genres || []"
            :rating="toNum(item.score)"
            :rating-count="item.ratingCount || 0"
            :status="item.status || ''"
            :year="item.year || null"
            :episodes="item.episodes ?? null"
            :type="item.type || ''"
            :rank="item.rank ?? undefined"
          />
        </template>
      </RecCarousel>
      -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { animeApi } from "@/api/anime"
import { useQuery } from "@tanstack/vue-query"
import RecommendationCard from "@/components/Cards/RecommendationCard.vue"
import RecCarousel from "@/components/Cards/RecCarousel.vue"
const router = useRouter();
const authStore = useAuthStore();

const {
  data,
  isError,
  isFetching: isLoading,
  refetch,
} = useQuery({
  queryKey: ["home"],
  queryFn: () => animeApi.getHomeData(),
  staleTime: 60_000,
  gcTime: 600_000,
});

const homeData = computed(
  () =>
    data.value ?? {
      continue_watching: [],
      rewatch: [],
      recommendations: [],
      trending: [],
    },
);

const toNum = (v: string | null | undefined): number | null =>
  v != null && v !== "" ? parseFloat(v) : null;

const continueAnime = computed(() =>
  homeData.value.continue_watching.map((item) => ({
    id: item.anime_id,
    slug: item.slug,
    title: item.title,
    poster: item.poster || "",
    year: item.year ?? null,
    score: item.rating != null ? String(item.rating) : null,
    status: item.status || "",
    type: item.kind || "",
    episodes: item.episodes ?? null,
    route: `/anime/${item.slug || item.anime_id}/watch?episode=${item.current_episode || 1}`,
  })),
);

const rewatchAnime = computed(() =>
  homeData.value.rewatch.map((item) => ({
    id: item.anime_id,
    slug: item.slug,
    title: item.title,
    poster: item.poster || "",
    year: item.year ?? null,
    score: item.rating != null ? String(item.rating) : null,
    status: item.status || "",
    type: item.kind || "",
    episodes: item.episodes ?? null,
    route: `/anime/${item.slug || item.anime_id}/watch?episode=1`,
  })),
);

const recsAnime = computed(() =>
  homeData.value.recommendations.map((item) => ({
    id: item.anime_id,
    title: item.title,
    poster: item.poster || "",
    year: item.year ?? null,
    score: item.rating != null ? String(item.rating) : null,
    status: item.status || "",
    type: item.kind || "",
    episodes: item.episodes ?? null,
    genres: item.genres || [],
    ratingCount: item.rating_count || 0,
  })),
);

const trendAnime = computed(() =>
  homeData.value.trending.map((item, idx) => ({
    id: item.anime_id,
    title: item.title,
    poster: item.poster || "",
    year: item.year ?? null,
    score: item.rating != null ? String(item.rating) : null,
    status: item.status || "",
    type: item.kind || "",
    episodes: item.episodes ?? null,
    genres: item.genres || [],
    ratingCount: item.rating_count || 0,
    rank: idx + 1,
  })),
);

const userName = computed(() => {
  const user = authStore.user as {
    display_name?: string;
    username?: string;
  } | null;
  return user?.display_name || user?.username || null;
});

const retry = () => refetch();
</script>

<style scoped>
/* ═══ Страница ══════════════════════════════════════════════ */
.home-page {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

/* ═══ Шапка ═════════════════════════════════════════════════ */
.welcome-section {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-10);
  flex-wrap: wrap;
}

.welcome-title {
  font-size: var(--text-4xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: -0.025em;
  line-height: 1.1;
}

.welcome-title span {
  color: var(--accent);
}

.welcome-subtitle {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
}

.welcome-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.quick-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
}

.quick-btn:hover {
  background: var(--surface-5);
  color: var(--text-primary);
  border-color: var(--border-default);
}

.quick-btn.accent {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: transparent;
}

.quick-btn.accent:hover {
  background: var(--accent);
  color: var(--text-on-accent);
}

/* ═══ Контент ═══════════════════════════════════════════════ */
.home-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

/* ═══ Пустое / Ошибка ═══════════════════════════════════════ */

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: 80px var(--space-6);
  color: var(--text-secondary);
  text-align: center;
}

.error-icon {
  color: var(--danger);
  opacity: 0.7;
}
.error-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.error-sub {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 0;
}

.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 38px;
  padding: 0 var(--space-5);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background-color var(--duration-base) var(--ease-out);
}

.retry-btn:hover {
  background: var(--accent-hover);
}

/* ═══ Скелетоны ═════════════════════════════════════════════ */
.skeleton-section {
  margin-bottom: var(--space-10);
}

.skeleton-header {
  margin-bottom: var(--space-4);
}

.skeleton-title-bar {
  height: 22px;
  width: 200px;
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-4) 50%,
    var(--surface-3) 75%
  );
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

.skeleton-track {
  display: flex;
  gap: var(--space-4);
  overflow: hidden;
}

.skeleton-card {
  flex: 0 0 220px;
}

.skeleton-poster {
  width: 100%;
  aspect-ratio: 2 / 3;
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-4) 50%,
    var(--surface-3) 75%
  );
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-2);
}

.skeleton-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.skeleton-line {
  height: 12px;
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-4) 50%,
    var(--surface-3) 75%
  );
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-xs);
}

.skeleton-line.w80 {
  width: 80%;
}
.skeleton-line.w55 {
  width: 55%;
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ═══ Адаптив ═══════════════════════════════════════════════ */
@media (max-width: 767px) {
  .home-page {
    padding: var(--space-4) var(--space-3);
  }

  .welcome-section {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: var(--space-7);
  }

  .welcome-title {
    font-size: var(--text-2xl);
  }

  .carousel-arrow {
    display: none;
  }

  .skeleton-card {
    flex: 0 0 155px;
  }
  .skeleton-poster {
    aspect-ratio: 2 / 3;
  }
}

/* ═══ АДАПТИВНЫЕ СТИЛИ HOME ═══ */

/* xs: 320px */
@media (max-width: 374px) {
  .home-page {
    padding: 0.5rem;
  }

  .home-header {
    padding: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .home-logo {
    font-size: 1.25rem;
  }

  .home-search {
    height: 2.5rem;
    padding: 0 0.75rem;
    font-size: 0.875rem;
  }

  .home-nav {
    gap: 0.25rem;
    padding: 0.25rem;
    overflow-x: auto;
  }

  .home-nav-item {
    padding: 0.375rem 0.5rem;
    font-size: 0.75rem;
    white-space: nowrap;
  }

  .home-section {
    margin-bottom: 1rem;
  }

  .home-section-header {
    padding: 0.5rem;
    margin-bottom: 0.25rem;
  }

  .home-section-title {
    font-size: 1rem;
  }

  .home-section-more {
    font-size: 0.75rem;
  }

  .home-carousel {
    padding: 0.5rem;
  }

  .home-carousel-track {
    gap: 0.5rem;
  }

  .home-carousel-item {
    min-width: 130px;
  }

  .home-poster {
    height: 185px;
    border-radius: 0.375rem;
  }

  .home-poster-overlay {
    padding: 0.375rem;
  }

  .home-poster-title {
    font-size: 0.75rem;
  }

  .home-poster-meta {
    font-size: 0.625rem;
    gap: 0.25rem;
  }

  .home-poster-rating {
    font-size: 0.625rem;
    padding: 0.125rem 0.25rem;
  }

  .home-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    padding: 0.5rem;
  }

  .home-grid-item {
    min-width: 0;
  }

  .home-grid-poster {
    aspect-ratio: 2/3;
    border-radius: 0.375rem;
  }

  .home-grid-title {
    font-size: 0.75rem;
    margin-top: 0.25rem;
  }

  .home-grid-meta {
    font-size: 0.625rem;
  }

  .home-banner {
    height: 150px;
    border-radius: 0.5rem;
    margin: 0.5rem;
  }

  .home-banner-title {
    font-size: 1rem;
  }

  .home-banner-text {
    font-size: 0.75rem;
  }

  .home-banner-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
  }

  .home-skeleton {
    padding: 0.5rem;
  }

  .home-skeleton-track {
    gap: 0.5rem;
  }

  .home-skeleton-card {
    min-width: 130px;
  }

  .home-skeleton-poster {
    height: 185px;
    border-radius: 0.375rem;
  }

  .home-skeleton-title {
    height: 0.75rem;
    margin-top: 0.375rem;
    border-radius: 0.25rem;
  }

  .home-skeleton-meta {
    height: 0.625rem;
    width: 60%;
    margin-top: 0.25rem;
    border-radius: 0.25rem;
  }

  .home-loading-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .home-loading-card {
    border-radius: 0.375rem;
  }

  .home-loading-poster {
    aspect-ratio: 2/3;
    border-radius: 0.375rem;
  }

  .home-loading-title {
    height: 0.75rem;
    margin-top: 0.375rem;
    border-radius: 0.25rem;
  }

  .home-loading-meta {
    height: 0.625rem;
    width: 50%;
    margin-top: 0.25rem;
    border-radius: 0.25rem;
  }

  .home-empty {
    padding: 2rem 1rem;
    text-align: center;
  }

  .home-empty-icon {
    width: 3rem;
    height: 3rem;
    margin-bottom: 0.5rem;
  }

  .home-empty-title {
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }

  .home-empty-text {
    font-size: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .home-empty-btn {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .home-error {
    padding: 2rem 1rem;
    text-align: center;
  }

  .home-error-icon {
    width: 3rem;
    height: 3rem;
    margin-bottom: 0.5rem;
  }

  .home-error-title {
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }

  .home-error-text {
    font-size: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .home-error-btn {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
}

/* sm: 375px */
@media (min-width: 375px) and (max-width: 767px) {
  .home-page {
    padding: 0.75rem;
  }

  .home-search {
    height: 2.75rem;
  }

  .home-carousel-item {
    min-width: 140px;
  }

  .home-poster {
    height: 200px;
  }

  .home-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .home-banner {
    height: 180px;
    margin: 0.75rem;
  }

  .home-banner-title {
    font-size: 1.25rem;
  }

  .home-skeleton-card {
    min-width: 140px;
  }

  .home-skeleton-poster {
    height: 200px;
  }
}

/* md: 768px+ */
@media (min-width: 768px) {
  .home-page {
    padding: 1rem;
  }

  .home-header {
    padding: 1rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .home-logo {
    font-size: 1.5rem;
  }

  .home-search {
    height: 3rem;
    padding: 0 1rem;
    max-width: 400px;
  }

  .home-nav {
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    overflow-x: auto;
  }

  .home-nav-item {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .home-section {
    margin-bottom: 1.5rem;
  }

  .home-section-header {
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
  }

  .home-section-title {
    font-size: 1.25rem;
  }

  .home-section-more {
    font-size: 0.875rem;
  }

  .home-carousel {
    padding: 0.75rem 1rem;
  }

  .home-carousel-item {
    min-width: 150px;
  }

  .home-poster {
    height: 215px;
    border-radius: 0.5rem;
  }

  .home-poster-overlay {
    padding: 0.5rem;
  }

  .home-poster-title {
    font-size: 0.875rem;
  }

  .home-poster-meta {
    font-size: 0.75rem;
  }

  .home-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    padding: 1rem;
  }

  .home-banner {
    height: 200px;
    margin: 1rem;
    border-radius: 0.75rem;
  }

  .home-banner-title {
    font-size: 1.5rem;
  }

  .home-banner-text {
    font-size: 0.875rem;
  }

  .home-skeleton-card {
    min-width: 150px;
  }

  .home-skeleton-poster {
    height: 215px;
  }

  .home-loading-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }

  .home-empty,
  .home-error {
    padding: 3rem 2rem;
  }

  .home-empty-icon,
  .home-error-icon {
    width: 4rem;
    height: 4rem;
  }

  .home-empty-title,
  .home-error-title {
    font-size: 1.25rem;
  }

  .home-empty-text,
  .home-error-text {
    font-size: 0.875rem;
  }
}

/* tablet-lg: 1024px+ */
@media (min-width: 1024px) {
  .home-page {
    padding: 1.25rem;
  }

  .home-carousel-item {
    min-width: 160px;
  }

  .home-poster {
    height: 230px;
  }

  .home-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .home-banner {
    height: 220px;
  }

  .home-skeleton-card {
    min-width: 160px;
  }

  .home-skeleton-poster {
    height: 230px;
  }

  .home-loading-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* laptop: 1280px+ */
@media (min-width: 1280px) {
  .home-page {
    padding: 1.5rem;
  }

  .home-header {
    padding: 1.25rem 1.5rem;
  }

  .home-logo {
    font-size: 1.75rem;
  }

  .home-search {
    height: 3.25rem;
    max-width: 500px;
  }

  .home-nav {
    gap: 0.75rem;
    padding: 0.75rem 1.5rem;
  }

  .home-nav-item {
    padding: 0.625rem 1.25rem;
    font-size: 1rem;
  }

  .home-section {
    margin-bottom: 2rem;
  }

  .home-section-title {
    font-size: 1.5rem;
  }

  .home-carousel-item {
    min-width: 170px;
  }

  .home-poster {
    height: 245px;
  }

  .home-poster-title {
    font-size: 1rem;
  }

  .home-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
  }

  .home-banner {
    height: 240px;
  }

  .home-banner-title {
    font-size: 1.75rem;
  }

  .home-skeleton-card {
    min-width: 170px;
  }

  .home-skeleton-poster {
    height: 245px;
  }

  .home-loading-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* desktop: 1536px+ */
@media (min-width: 1536px) {
  .home-page {
    padding: 2rem;
  }

  .home-carousel-item {
    min-width: 180px;
  }

  .home-poster {
    height: 260px;
  }

  .home-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 1.5rem;
  }

  .home-banner {
    height: 260px;
  }

  .home-skeleton-card {
    min-width: 180px;
  }

  .home-skeleton-poster {
    height: 260px;
  }

  .home-loading-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>