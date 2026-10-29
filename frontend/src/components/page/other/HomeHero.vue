<template>
  <div class="home-hero" v-if="props.animeList.length">
    <div class="hero-bg-wrap">
      <div
        :class="['hero-bg-slide', { active: activeBg === 0 }]"
        :style="bgStyle0"
      ></div>
      <div
        :class="['hero-bg-slide', { active: activeBg === 1 }]"
        :style="bgStyle1"
      ></div>
    </div>

    <template v-if="props.animeList.length > 1">
      <button
        class="hero-arrow hero-arrow-left"
        @click="prev"
        type="button"
        aria-label="Предыдущее"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path d="M15 18l-6-6 6-6" />
        </svg>
      </button>

      <button
        class="hero-arrow hero-arrow-right"
        @click="next"
        type="button"
        aria-label="Следующее"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path d="M9 18l6-6-6-6" />
        </svg>
      </button>
    </template>

    <Transition name="hero-fade" mode="out-in">
      <div :key="currentIndex" class="hero-content">
        <div class="hero-poster">
          <AnimeCard
            :anime="cardAnime"
            :priority="true"
            :show-actions="true"
            :show-genres="false"
            :show-kind-badge="true"
            class="hero-anime-card"
            @click="goToAnime"
            @watch="goToWatch"
          />
        </div>

        <div class="hero-info">
          <!-- <div class="reason-tooltip-wrapper">
            <button
              class="reason-btn"
              type="button"
              tabindex="0"
              role="button"
              :aria-label="currentReason ? 'Причина рекомендации' : 'Причина рекомендации недоступна'"
              @mouseenter="showReasonTooltip = true"
              @mouseleave="showReasonTooltip = false"
              @focus="showReasonTooltip = true"
              @blur="showReasonTooltip = false"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
            </button>
            <Transition name="reason-tooltip-fade">
              <div v-if="showReasonTooltip && currentReason" class="reason-tooltip" role="tooltip">
                <div class="reason-tooltip-arrow"></div>
                <div class="reason-tooltip-content">{{ currentReason }}</div>
              </div>
            </Transition>
          </div> -->
          <div class="hero-badge">Рекомендация</div>
          <h1 class="hero-title">{{ currentAnime.title }}</h1>

          <div class="hero-meta">
            <span v-if="currentAnime.year">{{ currentAnime.year }}</span>
            <span
              v-if="currentAnime.year && cardAnime.episodes"
              class="dot"
            >·</span>
            <span v-if="cardAnime.episodes">{{ cardAnime.episodes }} эп.</span>
            <template v-if="currentAnime.rating">
              <span class="dot">·</span>
              <span class="score-badge">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
                {{ currentAnime.rating.toFixed(1) }}
              </span>
            </template>
          </div>

          <div
            v-if="currentAnime.genres && currentAnime.genres.length"
            class="hero-genres"
          >
            <span
              v-for="(genre, index) in currentAnime.genres.slice(0, 6)"
              :key="index"
              class="genre-tag"
            >
              {{ genre }}
            </span>
            <span v-if="currentAnime.genres.length > 6" class="genre-more">
              +{{ currentAnime.genres.length - 6 }}
            </span>
          </div>

          <p v-if="currentDescription" class="hero-desc">
            {{ currentDescription }}
          </p>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import AnimeCard from "@/components/Cards/AnimeCard.vue"
import { getMediaUrl } from "@/api/client"
import { animeApi } from "@/api/anime"
import type { RecommendationItem, Anime } from "@/types"
const router = useRouter();

const goToAnime = () => {
  const a = currentAnime.value;
  if (!a) return;
  router.push(`/anime/${a.slug || a.anime_id}`);
};

const goToWatch = () => {
  const a = currentAnime.value;
  if (!a) return;
  const episode = 1;
  router.push(`/anime/${a.slug || a.anime_id}/watch?episode=${episode}`);
};

const props = defineProps<{
  animeList: RecommendationItem[];
}>();


const currentIndex = ref(0);
const activeBg = ref(0);
const bg0 = ref("");
const bg1 = ref("");
const showReasonTooltip = ref(false);
const animeDetails = ref<Record<number, Anime>>({});

const currentAnime = computed(() => props.animeList[currentIndex.value]!);

const pendingDetails = new Set<number>();
const fetchAnimeDescriptions = async () => {
  const item = currentAnime.value;
  const id = item?.anime_id;
  if (!id || animeDetails.value[id] || pendingDetails.has(id) || (item as unknown as { description?: string }).description) return;
  pendingDetails.add(id);
  try {
    animeDetails.value[id] = await animeApi.get(id);
    if (currentAnime.value?.anime_id === id) updateBackground(currentAnime.value);
  } catch { /* The home projection remains usable without an extended description. */ }
  finally { pendingDetails.delete(id); }
};



const resolveDescription = (a: RecommendationItem | undefined | null): string | null => {
   if (!a) return null;

   const fetchedDetails = animeDetails.value[a.anime_id];
   if (fetchedDetails?.description) {
      return fetchedDetails.description;
   }

   const anyA = a as unknown as Record<string, unknown>;

   const isValidString = (val: unknown): val is string =>
      typeof val === "string" && val.trim() !== "";

   const directFields = [
      "description",
      "description_ru",
      "anime_description",
      "summary",
      "overview",
      "plot"
   ];
   for (const field of directFields) {
      if (isValidString(anyA[field])) {
         return anyA[field] as string;
      }
   }

    const reasonDetails = anyA.reason_details as Record<string, unknown> | undefined;
   if (reasonDetails) {
      for (const field of directFields) {
         if (isValidString(reasonDetails[field])) {
            return reasonDetails[field] as string;
         }
      }

      const reasonAnime = reasonDetails.anime as Record<string, unknown> | undefined;
      if (reasonAnime) {
         for (const field of directFields) {
            if (isValidString(reasonAnime[field])) {
               return reasonAnime[field] as string;
            }
         }
      }
   }

   const nestedAnime = anyA.anime as Record<string, unknown> | undefined;
   if (nestedAnime) {
      for (const field of directFields) {
         if (isValidString(nestedAnime[field])) {
            return nestedAnime[field] as string;
         }
      }
   }

   const altNestingPatterns = [
      anyA.data,
      anyA.item,
      anyA.attributes
   ];

   for (const pattern of altNestingPatterns) {
      if (pattern && typeof pattern === "object") {
         for (const field of directFields) {
            if (isValidString((pattern as Record<string, unknown>)[field])) {
               return (pattern as Record<string, unknown>)[field] as string;
            }
         }

         const nestedInPattern = (pattern as Record<string, unknown>).anime as Record<string, unknown> | undefined;
         if (nestedInPattern) {
            for (const field of directFields) {
               if (isValidString(nestedInPattern[field])) {
                  return nestedInPattern[field] as string;
               }
            }
         }
      }
   }

   return null;
 };

const resolveReason = (a: RecommendationItem | undefined | null): string | null => {
   if (!a) return null;
   const anyA = a as unknown as Record<string, unknown>;
   const isValidString = (val: unknown): val is string =>
      typeof val === "string" && val.trim() !== "";

   if (isValidString(anyA.reason)) {
      return anyA.reason as string;
   }

   const reasonDetails = anyA.reason_details as Record<string, unknown> | undefined;
   if (reasonDetails && isValidString(reasonDetails.reason)) {
      return reasonDetails.reason as string;
   }

   return null;
};

const currentDescription = computed(() => resolveDescription(currentAnime.value));
const currentReason = computed(() => resolveReason(currentAnime.value));

const resolveEpisodes = (a: RecommendationItem | undefined | null): number | null => {
  if (!a) return null;
  const anyA = a as unknown as Record<string, unknown>;
  const candidates = [
    anyA.episodes,
    anyA.episodes_count,
    anyA.anime_episodes_count,
    anyA.episodes_total,
    anyA.series_count,
  ];
  for (const v of candidates) {
    if (typeof v === "number" && v > 0) return v;
  }
  const nested = anyA.anime as Record<string, unknown> | undefined;
  if (nested) {
    const nestedCandidates = [
      nested.episodes,
      nested.episodes_count,
      nested.anime_episodes_count,
      nested.episodes_total,
    ];
    for (const v of nestedCandidates) {
      if (typeof v === "number" && v > 0) return v;
    }
  }
  return null;
};

const resolvePoster = (a: RecommendationItem | undefined | null): string | null => {
  if (!a) return null;
  const source = a as unknown as Record<string, unknown>;
  const details = animeDetails.value[a.anime_id] as unknown as Record<string, unknown> | undefined;
  const nested = source.anime as Record<string, unknown> | undefined;
  const candidates = [
    details?.poster_image_url,
    details?.poster_url,
    details?.poster_file,
    details?.poster,
    source.poster_image_url,
    source.poster_url,
    source.poster_file,
    source.poster,
    nested?.poster_image_url,
    nested?.poster_url,
    nested?.poster_file,
    nested?.poster,
  ];
  const poster = candidates.find((value) => typeof value === "string" && value.trim());
  return typeof poster === "string" ? poster : null;
};

const cardAnime = computed(() => {
  const a = currentAnime.value!;
  return {
    id: a.anime_id,
    title_ru: a.title || a.title_en || "",
    title_en: a.title_en || a.title || "",
    year: a.year ?? null,
    status: a.status || "",
    episodes: resolveEpisodes(a),
    score: null,
    poster_url: resolvePoster(a),
    poster_image_url: resolvePoster(a),
    poster: resolvePoster(a),
    type: a.kind || "",
    genres: a.genres || [],
    slug: a.slug || String(a.anime_id),
  };
});

const prev = () => {
  currentIndex.value =
    (currentIndex.value - 1 + props.animeList.length) % props.animeList.length;
  startTimer();
};

const next = () => {
  currentIndex.value = (currentIndex.value + 1) % props.animeList.length;
  startTimer();
};

const bgStyle0 = computed(() => ({
  backgroundImage: bg0.value ? `url(${bg0.value})` : "none",
}));
const bgStyle1 = computed(() => ({
  backgroundImage: bg1.value ? `url(${bg1.value})` : "none",
}));

const updateBackground = (anime: RecommendationItem) => {
  const raw = resolvePoster(anime);
  if (!raw) return;
  const url = getMediaUrl(raw);
  if (!url) return;
  if (activeBg.value === 0) {
    bg1.value = url;
    activeBg.value = 1;
  } else {
    bg0.value = url;
    activeBg.value = 0;
  }
};

watch(
  () => currentAnime.value,
  (anime) => {
    if (anime) { updateBackground(anime); void fetchAnimeDescriptions(); }
  }
);

let timer: number | null = null;

const startTimer = () => {
  stopTimer();
  timer = window.setInterval(() => {
    next();
  }, 30000);
};

const stopTimer = () => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
};

onMounted(() => {
  fetchAnimeDescriptions();
  const first = currentAnime.value;
  const firstPoster = resolvePoster(first);
  if (firstPoster) {
    const url = getMediaUrl(firstPoster);
    if (url) bg0.value = url;
  }
  if (props.animeList.length > 1) {
    startTimer();
  }

});

onUnmounted(() => {
  stopTimer();
});
</script>

<style scoped>
.home-hero {
  position: relative;
  border-radius: var(--radius-xl);
  background: var(--surface-2);
  min-height: 300px;
}

.hero-bg-wrap {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: var(--radius-xl);
  z-index: 0;
}

.hero-bg-slide {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  filter: blur(18px) brightness(0.3);
  transform: scale(1.1);
  opacity: 0;
  transition: opacity 2.2s ease;
  will-change: opacity;
}

.hero-bg-slide.active {
  opacity: 1;
}

.hero-content {
  position: relative;
  z-index: 1;
  display: flex;
  gap: var(--space-10);
  padding: var(--space-10);
  align-items: flex-start;
}

.hero-poster {
  flex-shrink: 0;
  width: 240px;
  height: 336px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
  box-shadow: var(--shadow-sm-xl);
}

.hero-poster :deep(.anime-card) {
  background: transparent;
  border: none;
  box-shadow: none;
  cursor: pointer;
  height: 100% !important;
  min-height: 100%;
  overflow: visible;
  transform: none !important;
  transition: none !important;
}

.hero-poster :deep(.anime-card:hover) {
  transform: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
}

.hero-poster :deep(.anime-poster) {
  border-radius: var(--radius-lg);
  aspect-ratio: auto;
  height: 100% !important;
  min-height: 100%;
  overflow: hidden;
}

.hero-poster :deep(.anime-info) {
  display: none;
}

.hero-poster :deep(.poster-overlay) {
  background: linear-gradient(
    to top,
    rgba(8, 8, 9, 0.92) 0%,
    rgba(8, 8, 9, 0.45) 38%,
    rgba(8, 8, 9, 0) 68%
  );
}

.hero-poster:hover :deep(.card-actions) {
  opacity: 1;
  transform: translateX(0);
  visibility: visible;
  pointer-events: auto;
}

.hero-poster:hover :deep(.hover-overlay) {
  opacity: 1;
}

.hero-poster:hover :deep(.play-btn) {
  transform: scale(1);
  opacity: 1;
}

.hero-poster :deep(.play-btn) {
  width: 53px;
  height: 53px;
  min-width: 53px;
  margin-bottom: 20px;
  min-height: 53px;
  border-radius: 50%;
}

.hero-poster :deep(.action-btn) {
  width: 40px;
  height: 40px;
  min-width: 40px;
  min-height: 40px;
  border-radius: 13px;
}

.hero-poster :deep(.card-actions) {
  gap: 5px;
}

.hero-info {
  flex: 1;
  min-width: 0;
  position: relative;
}

.reason-tooltip-wrapper {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 10;
}

.reason-btn {
  width: 36px;
  height: 36px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.15s ease;
  flex-shrink: 0;
}

.reason-btn:hover,
.reason-btn:focus {
  color: var(--text-on-accent);
  transform: scale(1.05);
  outline: none;
}

.reason-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.reason-tooltip-fade-enter-active,
.reason-tooltip-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.reason-tooltip-fade-enter-from,
.reason-tooltip-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.reason-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  max-width: 320px;
  background: var(--surface-1);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.5;
  white-space: normal;
  word-wrap: break-word;
  z-index: 20;
}

.reason-tooltip-arrow {
  position: absolute;
  top: -6px;
  right: 14px;
  width: 12px;
  height: 12px;
  background: var(--surface-1);
  border: 1px solid var(--border-default);
  border-right: none;
  border-bottom: none;
  transform: rotate(45deg);
  z-index: -1;
}

.reason-tooltip-content {
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 13px;
  background: var(--accent-subtle);
  color: var(--accent);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: var(--space-4);
}

.hero-title {
  font-size: calc(var(--text-4xl) * 1.333);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-4) 0;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-base);
  margin-bottom: var(--space-5);
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
  padding: 5px 13px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  backdrop-filter: blur(4px);
}

.genre-more {
  padding: 5px 13px;
  background: rgba(124, 92, 252, 0.2);
  border: 1px solid rgba(124, 92, 252, 0.3);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  color: var(--accent);
}

.hero-desc {
  color: var(--text-secondary);
  font-size: var(--text-base);
  line-height: 1.6;
  margin: 0;
  max-width: 800px;
  display: -webkit-box;
  line-clamp: 4;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hero-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 1px solid var(--border-default);
  background: rgba(12, 12, 15, 0.85);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition:
    opacity 0.3s ease,
    background-color 0.3s ease,
    transform 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.home-hero:hover .hero-arrow {
  opacity: 1;
}

.hero-arrow:hover {
  background: var(--accent);
  border-color: var(--accent);
  transform: translateY(-50%) scale(1.08);
}

.hero-arrow-left {
  left: -19px;
}

.hero-arrow-right {
  right: -19px;
}

.hero-fade-enter-active,
.hero-fade-leave-active {
  transition: opacity 0.6s ease;
}

.hero-fade-enter-from,
.hero-fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) and (min-width: 768px) {
  .hero-content {
    padding: var(--space-8);
    gap: var(--space-8);
  }
  .hero-poster {
    width: 200px;
    height: 280px;
  }
  .hero-title {
    font-size: calc(var(--text-3xl) * 1.2);
  }
  .hero-desc {
    -webkit-line-clamp: 3;
    line-clamp: 3;
  }
  .hero-arrow {
    width: 42px;
    height: 42px;
  }
  .hero-arrow-left {
    left: 8px;
  }
  .hero-arrow-right {
    right: 8px;
  }
  .reason-btn {
    width: 32px;
    height: 32px;
  }
  .reason-tooltip {
    min-width: 200px;
    max-width: 280px;
    font-size: var(--text-xs);
    padding: var(--space-2) var(--space-3);
  }
  .reason-tooltip-arrow {
    right: 12px;
  }
}

@media (max-width: 767px) {
  .home-hero {
    margin-bottom: var(--space-6);
  }

  .hero-content {
    flex-direction: column;
    padding: var(--space-5);
    gap: var(--space-4);
  }

  .hero-poster {
    width: 160px;
    height: 224px;
  }

  .hero-title {
    font-size: var(--text-2xl);
  }

  .hero-arrow {
    display: none;
  }

  .reason-btn {
    width: 32px;
    height: 32px;
  }
  .reason-tooltip {
    min-width: 200px;
    max-width: 280px;
    font-size: var(--text-xs);
    padding: var(--space-2) var(--space-3);
  }
  .reason-tooltip-arrow {
    right: 12px;
  }
}

@media (max-width: 480px) {
  .home-hero {
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-5);
  }
  .hero-bg-wrap {
    border-radius: var(--radius-lg);
  }
  .hero-content {
    padding: var(--space-4);
    gap: var(--space-3);
  }
  .hero-poster {
    width: 140px;
    height: 196px;
    margin: 0 auto;
  }
  .hero-info {
    text-align: center;
  }
  .hero-badge {
    font-size: var(--text-xs);
    padding: 3px 10px;
    margin-bottom: var(--space-3);
  }
  .hero-title {
    font-size: var(--text-xl);
    margin-bottom: var(--space-3);
  }
  .hero-meta {
    font-size: var(--text-sm);
    justify-content: center;
    margin-bottom: var(--space-4);
  }
  .hero-genres {
    justify-content: center;
    gap: var(--space-1);
    margin-bottom: var(--space-3);
  }
  .genre-tag,
  .genre-more {
    padding: 4px 10px;
    font-size: var(--text-xs);
  }
  .hero-desc {
    font-size: var(--text-sm);
    -webkit-line-clamp: 4;
    line-clamp: 4;
    text-align: left;
  }
  .reason-btn {
    width: 28px;
    height: 28px;
  }
  .reason-btn svg {
    width: 14px;
    height: 14px;
  }
  .reason-tooltip {
    min-width: 180px;
    max-width: 260px;
    font-size: var(--text-xs);
    padding: var(--space-2) var(--space-3);
  }
  .reason-tooltip-arrow {
    right: 10px;
  }
}

@media (max-width: 360px) {
  .hero-content {
    padding: var(--space-3);
  }
  .hero-poster {
    width: 120px;
    height: 168px;
  }
  .hero-title {
    font-size: var(--text-lg);
  }
  .hero-meta {
    font-size: var(--text-xs);
    gap: var(--space-1);
  }
  .genre-tag,
  .genre-more {
    padding: 3px 8px;
    font-size: 0.7rem;
  }
  .hero-desc {
    font-size: var(--text-xs);
  }
  .reason-btn {
    width: 26px;
    height: 26px;
  }
  .reason-btn svg {
    width: 12px;
    height: 12px;
  }
  .reason-tooltip {
    min-width: 160px;
    max-width: 240px;
    font-size: 0.7rem;
    padding: var(--space-1) var(--space-2);
  }
  .reason-tooltip-arrow {
    right: 8px;
  }
}
</style>
