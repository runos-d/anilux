<template>
  <div v-if="normalizedGenres.length" ref="row" class="genre-row" :title="normalizedGenres.join(', ')">
    <span v-for="genre in visibleGenres" :key="genre" class="genre-row__tag">{{ genre }}</span>
    <span v-if="hiddenCount" class="genre-row__more">+{{ hiddenCount }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps<{ genres: string[] }>();

const row = ref<HTMLElement | null>(null);
const availableWidth = ref(0);
const fontRevision = ref(0);
let resizeObserver: ResizeObserver | null = null;
const widthCache = new Map<string, number>();

const normalizedGenres = computed(() => {
  const seen = new Set<string>();
  return props.genres.flatMap((value) => {
    const genre = String(value || "").trim();
    const key = genre.toLocaleLowerCase();
    if (!genre || seen.has(key)) return [];
    seen.add(key);
    return [genre];
  });
});

const textWidth = (text: string) => {
  const family = row.value ? getComputedStyle(row.value).fontFamily : "sans-serif";
  const cacheKey = `${fontRevision.value}:${family}:${text}`;
  const cached = widthCache.get(cacheKey);
  if (cached !== undefined) return cached;
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  if (!context) return text.length * 7;
  context.font = `600 10.5px ${family}`;
  const measured = Math.ceil(context.measureText(text).width);
  widthCache.set(cacheKey, measured);
  return measured;
};

const visibleCount = computed(() => {
  const genres = normalizedGenres.value;
  const width = availableWidth.value;
  if (!genres.length) return 0;
  if (!width) return genres.length;

  const gap = 5;
  const tagWidths = genres.map((genre) => textWidth(genre) + 16);
  let used = 0;
  let best = 1;

  for (let count = 1; count <= genres.length; count += 1) {
    const currentTagWidth = tagWidths[count - 1] ?? 0;
    used += currentTagWidth + (count > 1 ? gap : 0);
    const remaining = genres.length - count;
    const total = used + (remaining ? gap + textWidth(`+${remaining}`) + 12 : 0);
    if (total <= width) best = count;
    else break;
  }

  return best;
});

const visibleGenres = computed(() => normalizedGenres.value.slice(0, visibleCount.value));
const hiddenCount = computed(() => Math.max(0, normalizedGenres.value.length - visibleCount.value));

const updateWidth = () => {
  availableWidth.value = row.value?.clientWidth || 0;
};

onMounted(() => {
  updateWidth();
  if (row.value) {
    resizeObserver = new ResizeObserver(updateWidth);
    resizeObserver.observe(row.value);
  }
  void document.fonts?.ready.then(() => {
    widthCache.clear();
    fontRevision.value += 1;
    updateWidth();
  });
});

watch(normalizedGenres, () => void nextTick(updateWidth));
onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  widthCache.clear();
});
</script>

<style scoped>
.genre-row {
  display: flex;
  align-items: center;
  gap: 5px;
  width: 100%;
  min-width: 0;
  min-height: 22px;
  max-height: 22px;
  overflow: hidden;
}

.genre-row__tag,
.genre-row__more {
  min-width: 0;
  padding: 4px 8px;
  border-radius: 7px;
  font-size: 10.5px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}

.genre-row__tag {
  flex: 0 1 auto;
  overflow: hidden;
  color: var(--text-secondary);
  background: var(--surface-4);
  text-overflow: ellipsis;
}

.genre-row__more {
  flex: 0 0 auto;
  padding-inline: 6px;
  color: var(--text-tertiary);
}
</style>
