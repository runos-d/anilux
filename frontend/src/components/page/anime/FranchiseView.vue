<template>
  <div class="franchise-page">
    <template v-if="loading">
      <div class="franchise-hero skeleton-hero">
        <div class="sk sk-poster"></div>
        <div class="sk-info">
          <div class="sk sk-title"></div>
          <div class="sk sk-meta"></div>
          <div class="sk sk-desc"></div>
          <div class="sk sk-desc w60"></div>
        </div>
      </div>
      <div class="entries-grid">
        <div v-for="n in 4" :key="n" class="entry-card sk-card">
          <div class="sk sk-card-poster"></div>
          <div class="sk-card-info">
            <div class="sk sk-line w80"></div>
            <div class="sk sk-line w50"></div>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="error" class="state-error">
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
      <p class="state-title">Не удалось загрузить франшизу</p>
      <button class="btn-accent" @click="load">Повторить</button>
    </div>

    <template v-else-if="franchise">
      <div class="franchise-hero" :style="heroBg">
        <div class="hero-backdrop"></div>
        <div class="hero-content">
          <div class="hero-poster">
            <img
              v-if="franchise.poster_image_url"
              :src="getMediaUrl(franchise.poster_image_url)"
              :alt="franchise.name"
              class="poster-img"
            />
            <div v-else class="poster-placeholder">
              <svg
                width="40"
                height="40"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <rect x="2" y="2" width="20" height="20" rx="2" />
                <path d="M12 2v20M2 12h20" />
              </svg>
            </div>
          </div>

          <div class="hero-info">
            <div class="hero-badge">Франшиза</div>
            <h1 class="hero-title">{{ franchise.name }}</h1>

            <div class="hero-meta">
              <span v-if="franchise.year_range && franchise.year_range !== '-'">
                {{ franchise.year_range }}
              </span>
              <span v-else-if="franchise.year_start">
                {{ franchise.year_start
                }}{{
                  franchise.year_end &&
                  franchise.year_end !== franchise.year_start
                    ? " -" + franchise.year_end
                    : ""
                }}
              </span>
              <span class="dot">·</span>
              <span
                >{{
                  franchise.parts_count || franchise.entries?.length || 0
                }}
                частей</span
              >
              <template v-if="franchise.avg_score || franchise.score">
                <span class="dot">·</span>
                <span class="score-badge">
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <polygon
                      points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
                    />
                  </svg>
                  {{
                    Number(franchise.avg_score || franchise.score).toFixed(1)
                  }}
                </span>
              </template>
            </div>

            <div
              v-if="franchise.all_genres && franchise.all_genres.length > 0"
              class="hero-genres"
            >
              <span
                v-for="(genre, index) in franchise.all_genres.slice(0, 3)"
                :key="index"
                class="genre-tag"
              >
                {{ genre }}
              </span>
              <span v-if="franchise.all_genres.length > 3" class="genre-more">
                +{{ franchise.all_genres.length - 3 }}
              </span>
            </div>

            <p v-if="franchise.description" class="hero-desc">
              {{ franchise.description }}
            </p>
          </div>
        </div>
      </div>

      <div class="entries-section">
        <div class="entries-header">
          <h2 class="entries-title">Все части</h2>
          <select v-model="sortBy" class="sort-select">
            <option value="order">По порядку</option>
            <option value="year">По году</option>
            <option value="episodes">По сериям</option>
            <option value="score">По рейтингу</option>
          </select>
        </div>

        <div class="entries-grid">
          <AnimeCard
            v-for="entry in sortedEntries"
            :key="entry.id"
            :anime="toAnimeCard(entry)"
            :show-kind-badge="false"
            :show-genres="true"
            :show-actions="true"
            @click="goToAnime(entry)"
            @watch="watchAnime(entry)"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import apiClient, { getMediaUrl } from "@/api/client";
import AnimeCard from "@/components/Cards/AnimeCard.vue";

const route = useRoute();
const router = useRouter();

interface FranchiseEntry {
  id: number;
  title_ru: string;
  title_en: string;
  title_jp: string;
  kind: string;
  episodes: number | null;
  year: number | null;
  score: number | null;
  status: string;
  poster_url: string;
  poster_image_url: string;
  franchise_order: number;
  kodik_link: string;
  slug: string;
  anime_slug: string;
  genres?: string[] | null;
}

interface FranchiseDetail {
  id: number;
  name: string;
  slug: string;
  description: string;
  poster_url: string;
  poster_image_url: string;
  score: number | null;
  year_start: number | null;
  year_end: number | null;
  year_range?: string;
  parts_count?: number;
  avg_score?: number | null;
  all_genres?: string[];
  all_posters?: string[];
  entries: FranchiseEntry[];
}

const franchise = ref<FranchiseDetail | null>(null);
const loading = ref(true);
const error = ref(false);
const sortBy = ref("order");

const sortedEntries = computed(() => {
  const entries = [...(franchise.value?.entries || [])];
  switch (sortBy.value) {
    case "year":
      return entries.sort((a, b) => (b.year || 0) - (a.year || 0));
    case "episodes":
      return entries.sort((a, b) => (b.episodes || 0) - (a.episodes || 0));
    case "score":
      return entries.sort((a, b) => (b.score || 0) - (a.score || 0));
    default:
      return entries.sort(
        (a, b) =>
          a.franchise_order - b.franchise_order ||
          (a.year || 0) - (b.year || 0),
      );
  }
});

const heroBg = computed(() => {
  const url = franchise.value?.poster_image_url || franchise.value?.poster_url;
  if (!url) return {};
  return {
    "--hero-bg": `url(${getMediaUrl(url)})`,
  };
});


const load = async () => {
  loading.value = true;
  error.value = false;
  try {
    const slug = route.params.slug;
    console.log("Loading franchise:", slug);
    const res = await apiClient.get(`/anime/franchises/${slug}/`);
    console.log("Franchise data:", res.data);
    franchise.value = res.data;
  } catch (e) {
    console.error("Error loading franchise:", e);
    error.value = true;
  } finally {
    loading.value = false;
  }
};

const animeRouteKey = (entry: FranchiseEntry) =>
  entry.slug || entry.anime_slug || entry.id;

const goToAnime = (entry: FranchiseEntry) =>
  router.push(`/anime/${animeRouteKey(entry)}`);

const watchAnime = (entry: FranchiseEntry) =>
  router.push(`/anime/${animeRouteKey(entry)}/watch`);

const toAnimeCard = (entry: FranchiseEntry) => ({
  id: entry.id,
  title_ru: entry.title_ru || entry.title_en || "-",
  title_en: entry.title_en,
  year: entry.year,
  type: entry.kind,
  episodes: entry.episodes,
  score: entry.score,
  status: entry.status,
  poster_url: entry.poster_url,
  poster_image_url: entry.poster_image_url,
  slug: entry.slug || entry.anime_slug || String(entry.id),
  genres: entry.genres ?? franchise.value?.all_genres ?? null,
});

onMounted(load);
</script>

<style scoped>
/* ── Страница ────────────────────────────────────────────── */
.franchise-page {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5) var(--space-10);
}

/* ── Hero ────────────────────────────────────────────────── */
.franchise-hero {
  position: relative;
  border-radius: var(--radius-xl);
  overflow: hidden;
  margin-bottom: var(--space-10);
  background: var(--surface-2);
  min-height: 300px;
}

.franchise-hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: var(--hero-bg);
  background-size: cover;
  background-position: center;
  filter: blur(18px) brightness(0.3);
  transform: scale(1.1);
}

.hero-content {
  position: relative;
  display: flex;
  gap: var(--space-8);
  padding: var(--space-8);
  align-items: flex-start;
}

.hero-poster {
  flex-shrink: 0;
  width: 204px;
  height: 286px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
  box-shadow: var(--shadow-sm-xl);
}

.poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.hero-info {
  flex: 1;
  min-width: 0;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  background: var(--accent-subtle);
  color: var(--accent);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: var(--space-3);
}

.hero-title {
  font-size: 2.125rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-3);
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.dot {
  color: var(--text-tertiary);
}

.score-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--warning);
  font-weight: 700;
}

.hero-genres {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.genre-tag {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  backdrop-filter: blur(4px);
}

.genre-more {
  padding: 4px 10px;
  background: rgba(124, 92, 252, 0.2);
  border: 1px solid rgba(124, 92, 252, 0.3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--accent);
}

.hero-desc {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 1.6;
  margin: 0;
  max-width: 600px;
  display: -webkit-box;
  line-clamp: 4;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Секция частей ───────────────────────────────────────── */
/* .entries-section { } */

.entries-header {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.entries-title {
  flex-shrink: 0;
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.sort-select {
  min-width: 0;
  max-width: 100%;
  min-height: 44px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  cursor: pointer;
}

.entries-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  grid-auto-rows: 1fr;       /* все строки одинаковой высоты */
  align-items: stretch;      /* карточки растягиваются на всю ячейку */
}

/* ── Кнопки ─────────────────────────────────────────────── */
.btn-accent {
  padding: 10px var(--space-6);
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background-color var(--duration-base);
}
.btn-accent:hover {
  background: var(--accent-hover);
}

/* ── Ошибка ─────────────────────────────────────────────── */
.state-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: 80px 0;
  color: var(--text-secondary);
  text-align: center;
}
.state-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

/* ── Скелетоны ───────────────────────────────────────────── */
.sk {
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
@keyframes shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

.skeleton-hero {
  display: flex;
  gap: var(--space-8);
  padding: var(--space-8);
  min-height: 300px;
}
.sk-poster {
  flex-shrink: 0;
  width: 204px;
  height: 286px;
  border-radius: var(--radius-lg);
}
.sk-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding-top: var(--space-2);
}
.sk-title {
  height: 40px;
  width: 50%;
}
.sk-meta {
  height: 16px;
  width: 35%;
}
.sk-desc {
  height: 14px;
}
.w60 {
  width: 60%;
}
.sk-card {
  cursor: default;
}
.sk-card:hover {
  transform: none;
}
.sk-card-poster {
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
}
.sk-card-info {
  padding-top: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.sk-line {
  height: 12px;
}
.w80 {
  width: 80%;
}
.w50 {
  width: 50%;
}

/* ── Адаптив ─────────────────────────────────────────────── */
@media (max-width: 767px) {
  .franchise-page {
    padding: var(--space-4) var(--space-3) var(--space-8);
  }
  .hero-content {
    flex-direction: column;
    padding: var(--space-5);
    gap: var(--space-4);
  }
  .hero-poster {
    width: 136px;
    height: 190px;
  }
  .hero-title {
    font-size: 1.5rem;
  }
  .entries-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: var(--space-3);
  }
  .skeleton-hero {
    flex-direction: column;
    padding: var(--space-5);
  }
  .sk-poster {
    width: 136px;
    height: 190px;
  }
}
</style>
