<template>
  <main class="excerpt-page"><p v-if="loading">Загрузка отрывка…</p><p v-if="error" role="alert">{{ error }}</p>
    <template v-if="excerpt"><h1>{{ excerpt.title || 'Отрывок' }}</h1><p>{{ excerpt.anime_title }} · Сезон {{ excerpt.season }} · Серия {{ excerpt.episode }} · {{ excerpt.translation_title }}</p><p>{{ excerptTime(excerpt.start) }} -{{ excerptTime(excerpt.end) }}</p><p v-if="excerpt.description">{{ excerpt.description }}</p>
      <div v-if="!error" class="player"><KodikPlayer :key="playerKey" ref="player" :link="excerpt.player_link" :season="excerpt.season" :episode="excerpt.episode" :translation-id="excerpt.translation_id" :start-from="excerpt.start" only-episode @play="controller?.play()" @pause="controller?.pause()" @precise-time="controller?.preciseTime($event)" @time-update="controller?.roundedTime()" @duration-update="controller?.durationUpdate($event)" @current-episode="controller?.episode($event)" @video-ended="controller?.ended()" /></div>
      <div class="actions"><button v-if="!error" @click="controller?.repeat()">Повторить отрывок</button><button v-else @click="load">Открыть заново</button><router-link :to="{ name: 'anime-watch', params: { slug: String(excerpt.anime_id) }, query: { episode: excerpt.episode, season: excerpt.season, translation: excerpt.translation_id } }">Перейти к полной серии</router-link><router-link to="/excerpts">Мои отрывки</router-link></div>
    </template>
  </main>
</template>
<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { excerptsApi, excerptTime, type Excerpt } from '@/api/excerpts';
import KodikPlayer from '@/components/Players/KodikPlayer.vue';
import { ExcerptPlayback } from '@/lib/excerptPlayback';
const route = useRoute(), excerpt = ref<Excerpt | null>(null), player = ref<InstanceType<typeof KodikPlayer> | null>(null);
const error = ref(''), loading = ref(false), playerKey = ref(0);
let controller: ExcerptPlayback | undefined, timer: ReturnType<typeof setInterval> | undefined, generation = 0;
async function fetchExcerpt() { return route.params.token ? excerptsApi.shared(String(route.params.token)) : excerptsApi.get(Number(route.params.id)); }
async function load() {
  const version = ++generation; controller?.dispose(); controller = undefined; clearInterval(timer); excerpt.value = null; error.value = ''; loading.value = true;
  try {
    const { data } = await fetchExcerpt(); if (version !== generation) return;
    excerpt.value = data; playerKey.value++; await nextTick();
    controller = new ExcerptPlayback(data, { play: () => player.value?.play(), pause: () => player.value?.pause(), seek: time => player.value?.seek(time), getTime: () => player.value?.getTime() }, message => { error.value = message; });
    timer = setInterval(() => void revalidate(version), 15000);
  } catch { if (version === generation) error.value = 'Отрывок недоступен. Ссылка отозвана, аниме заблокировано или требуется вход автора.'; }
  finally { if (version === generation) loading.value = false; }
}
async function revalidate(version: number) {
  try {
    const { data } = await fetchExcerpt(); if (version !== generation) return;
    if (data.start !== excerpt.value?.start || data.end !== excerpt.value?.end) { controller?.dispose(); error.value = 'Автор изменил диапазон. Откройте отрывок заново.'; }
    excerpt.value = data;
  } catch (e) {
    const status = (e as { response?: { status?: number } }).response?.status;
    if (version === generation && [401, 403, 404].includes(status || 0)) { controller?.dispose(); excerpt.value = null; error.value = 'Отрывок больше недоступен.'; }
  }
}
watch(() => route.fullPath, () => void load(), { immediate: true });
onBeforeUnmount(() => { generation++; clearInterval(timer); controller?.dispose(); });
</script>
<style scoped>
.excerpt-page{max-width:1000px;margin:auto;padding:24px;color:var(--text-primary)}.player{aspect-ratio:16/9;background:#000}.actions{display:flex;align-items:center;flex-wrap:wrap;gap:16px;margin:16px 0}button{padding:12px;border:0;border-radius:8px;background:var(--accent);color:white;cursor:pointer}p{white-space:pre-wrap;overflow-wrap:anywhere}@media(max-width:600px){.excerpt-page{padding:12px}}
</style>
