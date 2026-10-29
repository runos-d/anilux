<template>
  <div v-if="!current || current.unavailable" class="excerpt-card unavailable">Отрывок недоступен</div>
  <router-link v-else ref="root" :to="owner ? `/excerpts/${current.id}` : current.share_path || '/excerpts'" class="excerpt-card" @click.stop>
    <img :src="getMediaUrl(current.poster_url) || '/placeholder-anime.jpg'" :alt="current.anime_title" />
    <div><small>Отрывок · {{ current.translation_title }}</small><strong>{{ current.anime_title }}</strong><span>Сезон {{ current.season }} · Серия {{ current.episode }} · {{ excerptTime(current.start) }} -{{ excerptTime(current.end) }}</span><b v-if="current.title">{{ current.title }}</b><p v-if="current.description">{{ current.description }}</p></div>
  </router-link>
</template>
<script setup lang="ts">
import { onMounted, onBeforeUnmount, onActivated, onDeactivated, ref, watch, nextTick } from 'vue';
import { getMediaUrl } from '@/api/client';
import { excerptTime, type Excerpt } from '@/api/excerpts';
import { registerExcerptCheck } from '@/lib/excerptChecks';
const props = defineProps<{ excerpt?: Excerpt | null; owner?: boolean; preview?: boolean }>();
const current = ref(props.excerpt);
const root = ref<{ $el: HTMLElement }>();
let observer: IntersectionObserver | undefined;
let registration: ReturnType<typeof registerExcerptCheck> | undefined;
let active = true;
let generation = 0;
function stop() { generation++; observer?.disconnect(); registration?.stop(); observer = undefined; registration = undefined; }
async function start() {
  stop(); const version = generation; await nextTick();
  if (version !== generation) return;
  const value = props.excerpt;
  if (!active || !value || value.unavailable || props.preview || !root.value?.$el) return;
  registration = registerExcerptCheck(value, !!props.owner, updated => {
    current.value = updated;
    if (!updated) stop();
  });
  if (typeof IntersectionObserver === 'undefined') registration.visible(true);
  else {
    observer = new IntersectionObserver(entries => registration?.visible(entries.some(entry => entry.isIntersecting)));
    observer.observe(root.value.$el);
  }
}
watch(() => [props.excerpt, props.owner, props.preview], () => { current.value = props.excerpt; void start(); });
onMounted(start); onActivated(() => { active = true; void start(); });
onDeactivated(() => { active = false; stop(); });
onBeforeUnmount(() => { active = false; stop(); });
</script>
<style scoped>
.excerpt-card{display:flex;gap:12px;max-width:100%;padding:12px;margin:10px 0;border:1px solid var(--border-color);border-radius:12px;background:var(--surface-2);color:var(--text-primary);text-decoration:none;overflow:hidden;text-align:left}
img{width:64px;height:90px;object-fit:cover;flex-shrink:0;border-radius:8px}div{min-width:0}strong,span,b,small{display:block}strong{margin:4px 0}small,span{color:var(--text-secondary);font-size:12px}p{margin:6px 0 0;white-space:pre-wrap;overflow-wrap:anywhere}b,strong{overflow-wrap:anywhere}.unavailable{color:var(--text-secondary)}
</style>
