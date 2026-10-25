<template>
  <div v-if="!current || current.unavailable" class="excerpt-card unavailable">Отрывок недоступен</div>
  <router-link v-else :to="owner ? `/excerpts/${current.id}` : current.share_path || '/excerpts'" class="excerpt-card" @click.stop>
    <img :src="getMediaUrl(current.poster_url) || '/placeholder-anime.jpg'" :alt="current.anime_title" />
    <div><small>Отрывок · {{ current.translation_title }}</small><strong>{{ current.anime_title }}</strong><span>Сезон {{ current.season }} · Серия {{ current.episode }} · {{ excerptTime(current.start) }} -{{ excerptTime(current.end) }}</span><b v-if="current.title">{{ current.title }}</b><p v-if="current.description">{{ current.description }}</p></div>
  </router-link>
</template>
<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
import { getMediaUrl } from '@/api/client';
import { excerptsApi, excerptTime, type Excerpt } from '@/api/excerpts';
const props = defineProps<{ excerpt?: Excerpt | null; owner?: boolean; preview?: boolean }>();
const current = ref(props.excerpt);
let timer: ReturnType<typeof setInterval> | undefined;
let generation = 0;
watch(() => props.excerpt, value => { generation++; current.value = value; });
async function refresh() {
  const value = props.excerpt, version = generation;
  if (!value || props.preview || value.unavailable) return;
  const token = value.share_path?.split('/').pop();
  try {
    const response = props.owner ? await excerptsApi.get(value.id) : token ? await excerptsApi.shared(token) : null;
    if (version === generation) current.value = response?.data;
  } catch (error) {
    const status = (error as { response?: { status?: number } }).response?.status;
    if (version === generation && [401, 403, 404].includes(status || 0)) current.value = null;
  }
}
onMounted(() => { void refresh(); timer = setInterval(() => { if (!document.hidden) void refresh(); }, 15000); });
onBeforeUnmount(() => { generation++; clearInterval(timer); });
</script>
<style scoped>
.excerpt-card{display:flex;gap:12px;max-width:100%;padding:12px;margin:10px 0;border:1px solid var(--border-color);border-radius:12px;background:var(--surface-2);color:var(--text-primary);text-decoration:none;overflow:hidden;text-align:left}
img{width:64px;height:90px;object-fit:cover;flex-shrink:0;border-radius:8px}div{min-width:0}strong,span,b,small{display:block}strong{margin:4px 0}small,span{color:var(--text-secondary);font-size:12px}p{margin:6px 0 0;white-space:pre-wrap;overflow-wrap:anywhere}b,strong{overflow-wrap:anywhere}.unavailable{color:var(--text-secondary)}
</style>
