<template>
  <div class="home-page">
    <div v-if="isLoading" class="home-skeleton">
      <div class="hero-skeleton">
        <div class="hero-skeleton-bg"></div>
        <div class="hero-skeleton-content">
          <div class="skeleton-title-bar w60"></div>
          <div class="skeleton-line w80"></div>
          <div class="skeleton-line w55"></div>
          <div class="skeleton-line w40"></div>
        </div>
      </div>
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
    </div>

    <div v-else-if="isError" class="error-state">
      <div class="error-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <p class="error-title">Не удалось загрузить контент</p>
      <p class="error-sub">Проверьте соединение и попробуйте ещё раз</p>
      <button class="retry-btn" @click="retry">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6M1 20v-6h6" />
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
        </svg>
        Повторить
      </button>
    </div>

    <div v-else class="home-content">
      <!-- HERO SECTION: Плавный кроссфейд фонов -->
      <!-- <section v-if="heroSlides.length" class="hero-section">
        
        <div class="hero-slides">
          <div 
            v-for="(slide, index) in heroSlides" 
            :key="slide.id"
            :class="['hero-slide', { 'is-active': index === currentIndex }]"
          >
            <div class="hero-bg" :style="{ backgroundImage: `url(${getHeroMedia(slide)})` }"></div>
          </div>
        </div>

        <div class="hero-gradient"></div>

        <div class="hero-body">
          <Transition name="reveal" mode="out-in">
            <div :key="currentHero.id" class="hero-content">
              <h1 class="hero-title font-display">
                {{ currentHero.title || currentHero.title_en }}
              </h1>

              <div class="hero-tags">
                <span v-for="chip in getHeroChips(currentHero)" :key="chip.key" class="hero-tag">
                  {{ chip.label }}
                </span>
              </div>

              <p v-if="currentHero.description" class="hero-description">
                {{ truncateDescription(currentHero.description) }}
              </p>

              <div class="hero-actions">
                <button class="btn-primary" @click="openAnime(currentHero)">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 3 20 12 6 21 6 3" />
                  </svg>
                  Смотреть
                </button>
                
                <button class="btn-fav" aria-label="Добавить в избранное">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                  </svg>
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <div class="hero-controls">
          <button class="hero-arrow hero-arrow-left" @click="prevSlide" aria-label="Предыдущее">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
          <button class="hero-arrow hero-arrow-right" @click="nextSlide" aria-label="Следующее">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
      </section> -->
      
      <!-- <div class="genre-strip">
        <button class="genre-chip" v-for="genre in topGenres" :key="genre" @click="router.push(`/anime?genre=${genre}`)">
          {{ genre }}
        </button>
      </div> -->

      <HomeHero :anime-list="heroRecommendations" />

      <RecCarousel v-if="auth.isAuthenticated && newEpisodes.length" class="home-new-episodes"
        title="Новые серии" icon="video" :anime="newEpisodes">
        <template #card="{ item }">
          <div class="new-episode-card">
            <AnimeCard :anime="{ id: item.id, title_ru: item.title, title_en: '', poster_url: item.poster,
              poster_image_url: item.poster, score: item.score == null ? null : Number(item.score),
              year: item.year, status: item.status || '', genres: item.genres || [], episodes: item.episodes, type: item.type }"
              :show-actions="true" :show-progress="false"
              @click="router.push(`/anime/${item.slug || item.id}`)"
              @watch="router.push(item.route || `/anime/${item.slug || item.id}/watch`)" />
            <p class="new-episode-count"><span>Доступна серия {{ item.latest_episode }}</span><span>Не просмотрено: {{ item.unwatched_count }}</span></p>
            <button class="new-episode-watch" type="button" @click="router.push(item.route || `/anime/${item.slug || item.id}/watch`)">Смотреть</button>
          </div>
        </template>
      </RecCarousel>
      <RecCarousel v-if="continueWatching.length" title="Продолжить просмотр" icon="play" :anime="continueWatching" />
      <RecCarousel v-if="rewatch.length" title="Пересмотреть" icon="refresh" :anime="rewatch" />
      <!-- <RecCarousel title="Рекомендации для вас" icon="target" :anime="recommendations" :has-view-all="recommendations.length > 0" @view-all="router.push('/anime')" /> -->
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { animeApi } from "@/api/anime";
import { useQuery } from "@tanstack/vue-query";
import { useAuthStore } from '@/stores/auth';
import RecCarousel from "@/components/Cards/RecCarousel.vue";
import AnimeCard from "@/components/Cards/AnimeCard.vue";
import HomeHero from "@/components/page/other/HomeHero.vue";
import { getMediaUrl } from "@/api/client";
import type { HomeData, RecommendationItem, ContinueWatchingItem, RewatchItem, Anime } from "@/types";

const router = useRouter();
const auth = useAuthStore();


const {
  data,
  isError,
  isPending: isLoading,
  refetch,
} = useQuery({
  queryKey: computed(() => ['home', String(auth.user?.id ?? 'guest'), 'episodes-v1']),
  queryFn: () => animeApi.getHomeData(),
  staleTime: 60_000,
  gcTime: 600_000,
  refetchOnMount: 'always',
  refetchOnWindowFocus: true,
});

const homeData = computed<HomeData>(() =>
  data.value ?? {
    continue_watching: [],
    rewatch: [],
    recommendations: [],
    trending: [],
  },
);

const heroSlides = computed(() => homeData.value.trending.slice(0, 10));
const currentIndex = ref(0);
let slideTimer: number | null = null;

const currentHero = computed(() => heroSlides.value[currentIndex.value] || heroSlides.value[0]);

const getHeroMedia = (anime: { screenshots?: string[]; poster: string }) => {
  if (anime.screenshots && anime.screenshots.length > 0) {
    return getMediaUrl(anime.screenshots[0]);
  }
  return anime.poster ? getMediaUrl(anime.poster) : undefined;
};

const getHeroBg = (anime: { poster: string }) => {
  const url = getHeroMedia(anime);
  if (!url) return {};
  return { backgroundImage: `url(${url})` };
};

const getHeroChips = (anime: { rating: number | null; year?: number | null; kind?: string; episodes?: number | null }) => {
  if (!anime) return [];
  const chips: { key: string; label: string }[] = [];
  if (anime.rating != null) chips.push({ key: "rating", label: anime.rating.toFixed(1) });
  if (anime.year) chips.push({ key: "year", label: String(anime.year) });
  if (anime.kind) chips.push({ key: "kind", label: getTypeLabel(anime.kind) });
  if (anime.episodes) chips.push({ key: "episodes", label: `${anime.episodes} эп.` });
  return chips;
};

const goToSlide = (i: number) => {
  currentIndex.value = i;
  restartTimer();
};

const nextSlide = () => {
  currentIndex.value = (currentIndex.value + 1) % heroSlides.value.length;
  restartTimer();
};

const prevSlide = () => {
  currentIndex.value = (currentIndex.value - 1 + heroSlides.value.length) % heroSlides.value.length;
  restartTimer();
};

const restartTimer = () => {
  if (slideTimer) clearInterval(slideTimer);
  slideTimer = window.setInterval(() => {
    nextSlide();
  }, 8000);
};

onMounted(() => {
  if (heroSlides.value.length > 1) restartTimer();
});

onUnmounted(() => {
  if (slideTimer) clearInterval(slideTimer);
});

const openAnime = (anime: Anime) => {
  router.push(`/anime/${anime.slug || anime.id}`);
};

const truncateDescription = (desc: string, length = 180) => {
  if (!desc) return "";
  if (desc.length <= length) return desc;
  return desc.slice(0, length) + "...";
};

const getTypeLabel = (type?: string) => {
  const labels: Record<string, string> = {
    tv: "TV",
    movie: "Фильм",
    ova: "OVA",
    ona: "ONA",
    special: "Спешл",
  };
  return labels[type?.toLowerCase() || ""] || type || "";
};

const topGenres = computed(() => {
  const genres = new Set<string>();
  heroSlides.value.forEach(anime => {
    anime.genres?.forEach((g: string) => genres.add(g));
  });
  return Array.from(genres).slice(0, 8);
});

const retry = () => refetch();

interface RecCarouselAnime {
  id: number;
  slug?: string;
  title: string;
  poster: string | null;
  year?: number | null;
  score?: string | null;
  genres?: string[];
  status?: string;
  type?: string;
  episodes?: number | null;
  route?: string;
  ratingCount?: number;
  latest_episode?: number;
  unwatched_count?: number;
}

const mapRecommendation = (item: RecommendationItem): RecCarouselAnime => ({
  id: item.anime_id,
  slug: item.slug,
  title: item.title,
  poster: item.poster || null,
  year: item.year ?? null,
  score: item.rating != null ? String(item.rating) : null,
  status: item.status || "",
  type: item.kind || "",
  episodes: item.episodes ?? null,
  genres: item.genres || [],
  ratingCount: item.rating_count || 0,
});

const mapContinueWatching = (item: ContinueWatchingItem): RecCarouselAnime => ({
  id: item.anime_id,
  slug: item.slug,
  title: item.title,
  poster: item.poster || null,
  year: item.year ?? null,
  score: item.rating != null ? String(item.rating) : null,
  status: item.status || "",
  type: item.kind || "",
  episodes: item.episodes ?? null,
  genres: item.genres || [],
  ratingCount: item.rating_count || 0,
  route: `/anime/${item.slug || item.anime_id}/watch?episode=${item.current_episode || 1}`,
});

const mapRewatch = (item: RewatchItem): RecCarouselAnime => ({
  id: item.anime_id,
  slug: item.slug,
  title: item.title,
  poster: item.poster || null,
  year: item.year ?? null,
  score: item.rating != null ? String(item.rating) : null,
  status: item.status || "",
  type: item.kind || "",
  episodes: item.episodes ?? null,
  genres: item.genres || [],
  ratingCount: item.rating_count || 0,
  route: `/anime/${item.slug || item.anime_id}/watch?episode=1`,
});

const trending = computed(() => homeData.value.trending.map(mapRecommendation));
const newEpisodes = computed(() => (homeData.value.new_episodes || []).map(item => ({
  ...mapRecommendation(item), latest_episode: item.latest_episode, unwatched_count: item.unwatched_count,
  route: `/anime/${item.slug || item.anime_id}/watch?episode=${item.next_episode}`,
})));
const continueWatching = computed(() => homeData.value.continue_watching.map(mapContinueWatching));
const rewatch = computed(() => homeData.value.rewatch.map(mapRewatch));
const recommendations = computed(() => homeData.value.recommendations.map(mapRecommendation));
const heroRecommendations = computed(() => homeData.value.recommendations.length
  ? homeData.value.recommendations
  : homeData.value.trending);
</script>

<style scoped>
.new-episode-count { margin: 8px 0; color: var(--text-secondary); font-size: 12px; line-height: 1.5; }
.new-episode-count span { display: block; white-space: nowrap; }
.new-episode-watch { width: 100%; padding: 9px 12px; border: 0; border-radius: var(--radius-md); background: var(--accent); color: var(--text-on-accent); font-weight: 700; cursor: pointer; }
/* Общие настройки */
.home-page {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

.home-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

.hero-section {
  position: relative;
  border-radius: var(--radius-2xl);
  overflow: hidden;
  min-height: 620px;
  margin-bottom: var(--space-10);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.7);
  background: #050408;
}

.hero-slides {
  position: absolute;
  inset: 0;
}

.hero-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 1.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.hero-slide.is-active {
  opacity: 1;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center top;
  background-repeat: no-repeat;
  transform: scale(1.08);
  filter: saturate(1.1) brightness(0.9);
  transition: transform 8s ease-out;
  will-change: transform;
}

.hero-slide.is-active .hero-bg {
  transform: scale(1.02); /* Медленный "дыхающий" зум */
}

/* Мягкая дымка для загадочности */
.hero-gradient {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(to top, rgba(5, 4, 8, 0.95) 0%, rgba(5, 4, 8, 0.3) 45%, rgba(5, 4, 8, 0.2) 100%),
    linear-gradient(to right, rgba(5, 4, 8, 0.85) 0%, rgba(5, 4, 8, 0.4) 40%, transparent 80%);
}

.hero-body {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr;
  padding: var(--space-10);
  min-height: 620px;
  align-items: end;
  max-width: 800px;
}

/* Контент появляется волной, как туман */
.hero-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-5);
}

/* Магия: появление текста */
@keyframes reveal {
  from { opacity: 0; transform: translateY(30px); filter: blur(6px); }
  to { opacity: 1; transform: translateY(0); filter: blur(0); }
}

.reveal-enter-active {
  animation: reveal 1.2s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.reveal-leave-active {
  transition: opacity 0.5s ease;
}

.reveal-leave-to {
  opacity: 0;
}

/* Текст */
.hero-title {
  font-size: var(--text-4xl);
  font-weight: 800;
  color: #fff;
  margin: 0;
  line-height: 1.1;
  letter-spacing: -0.03em;
  text-shadow: 0 10px 40px rgba(0, 0, 0, 0.9), 0 0 80px rgba(0, 0, 0, 0.5);
  opacity: 0.95;
}

.hero-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(15, 15, 20, 0.8); /* Плотный цвет, не прозрачный! */
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-shadow: 0 2px 5px rgba(0, 0, 0, 0.8);
}

.hero-tag:first-child {
  color: #ffd700;
  border-color: rgba(255, 215, 0, 0.3);
}

.hero-description {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.7;
  text-shadow: 0 4px 15px rgba(0, 0, 0, 0.9);
  margin: 0;
  max-width: 580px;
  opacity: 0.9;
}

/* Кнопки: Плотные, весомые, как и весь сайт */
.hero-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-2);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  height: 52px;
  padding: 0 32px;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: 14px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
}

.btn-primary:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6);
}

.btn-fav {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: rgba(15, 15, 20, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
}

.btn-fav:hover {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.05);
}

/* Управление: интуитивное и незаметное */
.hero-controls {
  position: absolute;
  z-index: 3;
  bottom: var(--space-8);
  right: var(--space-8);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.4s ease;
}

.hero-section:hover .hero-controls {
  opacity: 1;
  transform: translateY(0);
}

.hero-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(10, 10, 15, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.hero-arrow:hover {
  background: var(--accent);
  border-color: var(--accent);
}

.hero-dots {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hero-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 0;
}

.hero-dot.active {
  width: 24px;
  border-radius: 4px;
  background: #fff;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

/* Жанры: элегантная, тонкая полоска */
.genre-strip {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-2);
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.genre-strip::-webkit-scrollbar {
  display: none;
}

.genre-chip {
  flex-shrink: 0;
  padding: 10px 20px;
  border-radius: 24px;
  background: rgba(15, 15, 20, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.genre-chip:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
  color: #fff;
  transform: translateY(-2px);
}

/* Секции каруселей - без рамки, чистые, прозрачные */
.home-content :deep(.rc) {
  background: transparent;
  border: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

/* Skeleton и Error */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: 100px var(--space-4);
}

.error-title { font-size: var(--text-lg); font-weight: 700; color: var(--text-primary); margin: 0; }
.error-sub { font-size: var(--text-sm); color: var(--text-tertiary); margin: 0; max-width: 420px; text-align: center; }

.retry-btn {
  display: inline-flex; align-items: center; gap: var(--space-2); height: 42px; padding: 0 var(--space-6);
  background: var(--accent); color: var(--text-on-accent); border: none; border-radius: 14px;
  font-size: var(--text-sm); font-weight: 600; cursor: pointer; transition: all 0.3s;
}

.retry-btn:hover { background: var(--accent-hover); transform: translateY(-1px); }

.home-skeleton {
  display: flex; flex-direction: column; gap: var(--space-10);
}

.hero-skeleton {
  position: relative; border-radius: var(--radius-2xl); overflow: hidden; min-height: 620px;
}

.hero-skeleton-bg {
  position: absolute; inset: 0;
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 90%; animation: shimmer 1.4s ease-in-out infinite;
}

.hero-skeleton-content {
  position: relative; z-index: 2; padding: var(--space-8); margin-top: auto;
}

.skeleton-title-bar, .skeleton-line {
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%; animation: shimmer 1.4s ease-in-out infinite;
}

@keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }

/* Адаптивность */
@media (max-width: 767px) {
  .home-page { padding: var(--space-4) var(--space-3); }
  .hero-section { min-height: 520px; }
  .hero-body { padding: var(--space-5); min-height: 520px; }
  .hero-title { font-size: var(--text-3xl); }
  .hero-controls { right: var(--space-5); bottom: var(--space-5); }
  .hero-controls { opacity: 1; transform: none; }
  .hero-description { font-size: 0.9rem; }
}
</style>
