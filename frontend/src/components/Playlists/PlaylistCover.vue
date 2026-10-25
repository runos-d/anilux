<template>
  <div class="playlist-art" :data-count="images.length" :class="{ 'has-custom': customCover }" role="img" :aria-label="label">
    <img v-if="customSource" class="art-custom" :src="customSource" alt="" :loading="priority ? 'eager' : 'lazy'" decoding="async" @error="onImageError" />
    <template v-else-if="images.length">
      <img :key="`back-${images[0]}`" class="art-backdrop" :src="images[0]" alt="" :loading="priority ? 'eager' : 'lazy'" decoding="async" @error="onImageError" />
      <div class="art-shade"></div>
      <img v-if="images[2]" :key="`left-${images[2]}`" class="art-poster art-left" :src="images[2]" alt="" loading="lazy" decoding="async" @error="onImageError" />
      <img v-if="images[1]" :key="`right-${images[1]}`" class="art-poster art-right" :src="images[1]" alt="" loading="lazy" decoding="async" @error="onImageError" />
      <img :key="`front-${images[0]}`" class="art-poster art-front" :src="images[0]" alt="" :loading="priority ? 'eager' : 'lazy'" :fetchpriority="priority ? 'high' : 'auto'" decoding="async" @error="onImageError" />
    </template>
    <div v-else class="art-empty">
      <svg width="58" height="58" viewBox="0 0 64 64" fill="none" aria-hidden="true"><rect x="11" y="15" width="30" height="39" rx="5" transform="rotate(-10 11 15)" stroke="currentColor" stroke-width="1.5" opacity=".4"/><rect x="23" y="9" width="30" height="42" rx="5" stroke="currentColor" stroke-width="2"/><path d="m34 23 10 7-10 7V23Z" fill="currentColor"/></svg>
      <span>{{ emptyLabel }}</span>
    </div>
    <div class="art-bottom"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { getMediaUrl } from '@/api/client';
const props = withDefaults(defineProps<{ posters?: (string | null | undefined)[]; customCover?: string | null; label?: string; emptyLabel?: string; priority?: boolean }>(), { posters: () => [], customCover: null, label: 'Обложка плейлиста', emptyLabel: 'Ваши подборки', priority: false });
const failed = ref(new Set<string>());
const onImageError = (event: Event) => { const source = (event.target as HTMLImageElement).getAttribute('src'); if (source) failed.value.add(source); };
const customSource = computed(() => {
  const source = props.customCover ? getMediaUrl(props.customCover) : undefined;
  return source && !failed.value.has(source) ? source : null;
});
const images = computed(() => [...new Set(props.posters.map(url => getMediaUrl(url || undefined))
  .filter((url): url is string => !!url))].filter(url => !failed.value.has(url)).slice(0, 3));
</script>

<style scoped>
.playlist-art { position: absolute; inset: 0; overflow: hidden; isolation: isolate; background: linear-gradient(145deg, var(--surface-4), var(--surface-2)); }
.art-backdrop, .art-custom { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: center 35%; }
.art-backdrop { filter: blur(18px) saturate(.8); transform: scale(1.14); opacity: .65; }
.art-shade { position: absolute; inset: 0; background: linear-gradient(160deg, #0c142522, #0c1425a6); }
.art-poster { position: absolute; width: 62%; aspect-ratio: 2 / 3; object-fit: cover; object-position: center 30%; border-radius: 7px; border: 1px solid #ffffff60; box-shadow: 0 8px 24px #0006; }
.art-front { left: 19%; top: 15%; z-index: 3; }
.art-left { left: -5%; top: 19%; transform: rotate(-12deg) scale(.94); z-index: 1; opacity: .85; }
.art-right { right: -5%; top: 19%; transform: rotate(12deg) scale(.94); z-index: 2; opacity: .85; }
.playlist-art[data-count="1"] .art-front { inset: 0; width: 100%; height: 100%; border: 0; border-radius: 0; box-shadow: none; }
.art-bottom { position: absolute; inset: 48% 0 0; background: linear-gradient(transparent, #090d1cbb); z-index: 4; pointer-events: none; }
.art-empty { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; color: var(--text-tertiary); font-size: 12px; background: radial-gradient(ellipse at 50% 30%, color-mix(in srgb, var(--accent) 14%, transparent), transparent 70%); }
</style>
