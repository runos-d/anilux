<template>
  <div class="rec-card-wrap" :class="{ 'has-reason': reason }">
    <FranchiseCard
      v-if="isFranchise && franchiseData"
      :franchise="franchiseData"
      :show-actions="true"
      :priority="priority"
      @click="handleFranchiseClick"
    />
    <AnimeCard
      v-else
      :anime="cardAnime"
      :show-actions="true"
      :priority="priority"
      :show-genres="genresList.length > 0"
      :show-progress="false"
      :max-genres="3"
      @click="handleClick"
    />
    <!-- <button v-if="reason" ref="reasonButton" class="reason-btn" type="button"
      :aria-label="`Почему рекомендовано «${title}»`" :aria-expanded="reasonOpen"
      :aria-describedby="reasonOpen ? tooltipId : undefined"
      @pointerenter="hoverReason" @pointerleave="leaveReason" @focus="openReason"
      @blur="closeReason" @click.stop="toggleReason" @keydown.esc.stop.prevent="closeReason">?</button> -->
    <Teleport to="body">
      <div v-if="reason && reasonOpen" :id="tooltipId" class="reason-popup"
        role="tooltip" :style="tooltipStyle" @pointerenter="cancelClose" @pointerleave="leaveReason"
        @click.stop>{{ reason }}</div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, useId, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import AnimeCard from "./AnimeCard.vue"
import FranchiseCard from "./FranchiseCard.vue"
interface Props {
  priority?: boolean;
  animeId: number;
  animeSlug?: string;
  title: string;
  poster: string;
  genres: string[] | string;
  rating: number | null;
  ratingCount: number;
  status: string;
  year: number | null;
  rank?: number;
  episodes?: number | null;
  type?: string;
  franchiseId?: number | null;
  franchiseSlug?: string | null;
  isFranchise?: boolean;
  franchiseName?: string;
  franchisePartsCount?: number;
  franchiseYearStart?: number | null;
  franchiseYearEnd?: number | null;
  franchiseScore?: number | null;
  reason?: string;
}

const props = defineProps<Props>();
const router = useRouter();
const reasonButton = ref<HTMLButtonElement | null>(null);
const reasonOpen = ref(false);
const tooltipId = useId();
const tooltipStyle = ref<Record<string, string>>({});
let pinned = false;
let closeTimer: ReturnType<typeof setTimeout> | undefined;
const cancelClose = () => { clearTimeout(closeTimer); };
const openReason = () => {
  cancelClose();
  const rect = reasonButton.value?.getBoundingClientRect();
  if (!rect) return;
  const width = Math.min(300, window.innerWidth - 24);
  const left = Math.max(12, Math.min(rect.right - width, window.innerWidth - width - 12));
  tooltipStyle.value = { width: `${width}px`, left: `${left}px`,
    ...(rect.bottom < window.innerHeight / 2 ? { top: `${rect.bottom + 8}px` }
      : { bottom: `${window.innerHeight - rect.top + 8}px` }),
    maxHeight: `${Math.max(80, window.innerHeight / 2 - 24)}px` };
  reasonOpen.value = true;
};
const closeReason = () => { cancelClose(); pinned = false; reasonOpen.value = false; };
const toggleReason = () => { if (pinned) closeReason(); else { openReason(); pinned = true; } };
const hoverReason = (event: PointerEvent) => {
  if (event.pointerType !== 'touch') openReason();
};
const leaveReason = () => {
  if (!pinned) closeTimer = setTimeout(closeReason, 120);
};
const outsideReason = (event: PointerEvent) => {
  if (!reasonButton.value?.contains(event.target as Node)
      && !document.getElementById(tooltipId)?.contains(event.target as Node)) closeReason();
};
const escapeReason = (event: KeyboardEvent) => { if (event.key === 'Escape') closeReason(); };
onMounted(() => {
  document.addEventListener('pointerdown', outsideReason);
  document.addEventListener('keydown', escapeReason);
  window.addEventListener('scroll', closeReason, true);
  window.addEventListener('resize', closeReason);
});
onUnmounted(() => {
  cancelClose();
  document.removeEventListener('pointerdown', outsideReason);
  document.removeEventListener('keydown', escapeReason);
  window.removeEventListener('scroll', closeReason, true);
  window.removeEventListener('resize', closeReason);
});
const genresList = computed<string[]>(() => {
  const g = props.genres;
  if (!g) return [];
  if (Array.isArray(g)) {
    return g
      .map((item) => {
        if (typeof item === "string") return item.trim();
        if (typeof item === "object" && item !== null && "name" in item) {
          return String((item as { name?: string }).name || "").trim();
        }
        return String(item || "").trim();
      })
      .filter(Boolean);
  }
  return g
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
});

const cardAnime = computed(() => ({
  id: props.animeId,
  slug: props.animeSlug || String(props.animeId),
  title_ru: props.title,
  title_en: "",
  year: props.year ?? null,
  status: props.status || "",
  episodes: props.episodes ?? null,
  score: props.rating,
  poster_url: props.poster || null,
  poster_image_url: props.poster || null,
  poster: null,
  type: props.type || "",
  genres: genresList.value.map((g, i) => ({ id: i, name: g, slug: g })),
}));

const franchiseData = computed(() => {
  if (!props.isFranchise || !props.franchiseId) return null;
  return {
    id: props.franchiseId,
    name: props.franchiseName || props.title,
    poster_url: props.poster || null,
    poster_image_url: props.poster || null,
    poster: null,
    parts_count: props.franchisePartsCount || 1,
    year_start: props.franchiseYearStart || null,
    year_end: props.franchiseYearEnd || null,
    score: props.franchiseScore || props.rating,
    all_genres: genresList.value,
    all_posters: props.poster ? [props.poster] : [],
  };
});

const handleClick = () => {
  router.push(`/anime/${props.animeSlug || props.animeId}`);
};

const handleFranchiseClick = () => {
  if (props.franchiseId) {
    router.push(`/franchise/${props.franchiseId}`);
  }
};


</script>

<style scoped>
.has-reason :deep(.poster-top-right),
.has-reason :deep(.parts-badge),
.has-reason :deep(.live-cover-indicator) { top: 56px; }

.rec-card-wrap {
  position: relative;
  flex: 0 0 220px;
  width: 220px;
  scroll-snap-align: start;
  overflow: visible;
}

.reason-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 12;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border-subtle);
  background: rgba(12, 12, 15, 0.85);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.15s ease;
}
.reason-btn:hover {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--text-on-accent, #fff);
}
.reason-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
.reason-btn::before { content: ''; position: absolute; inset: -4px; }
.reason-popup {
  position: fixed;
  z-index: 10000;
  box-sizing: border-box;
  padding: 12px 14px;
  background: var(--surface-3, #19191e);
  border: 1px solid var(--border-subtle, #41414b);
  border-radius: var(--radius-md);
  color: var(--text-primary, #fff);
  font-size: 13px;
  line-height: 1.5;
  overflow-y: auto;
  overflow-wrap: anywhere;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  pointer-events: auto;
  display: block;
  opacity: 1;
  visibility: visible;
}

@media (max-width: 767px) {
  .rec-card-wrap {
    flex: 0 0 155px;
    width: 155px;
  }
}
</style>
