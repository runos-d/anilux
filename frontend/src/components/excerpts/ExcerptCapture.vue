<template>
  <section class="capture" aria-label="Создание отрывка">
    <div class="capture-actions"><button :disabled="!material || !duration || !!pending" @click="mark('start')">Начало отрывка{{ start !== null ? ` · ${excerptTime(start)}` : '' }}</button><button :disabled="start === null || !!pending" @click="mark('end')">Конец отрывка{{ end !== null ? ` · ${excerptTime(end)}` : '' }}</button><router-link to="/excerpts">Мои отрывки</router-link></div>
    <small v-if="!material || !duration">Начните воспроизведение, чтобы выбрать диапазон.</small>
    <small v-else>Сезон {{ material.season }} · Серия {{ material.episode }} · {{ material.translation_title || `Озвучка #${material.translation_id}` }}</small>
    <p v-if="error" role="alert">{{ error }}</p><p v-if="saved" role="status">Отрывок сохранён. <router-link :to="`/excerpts/${saved}`">Открыть</router-link></p>
    <template v-if="start !== null && end !== null">
      <p v-if="!auth.isAuthenticated">Для сохранения <router-link to="/login">войдите в аккаунт</router-link>.</p>
      <ExcerptEditor v-else :value="draft" :busy="busy" @save="save" @cancel="reset" />
    </template>
  </section>
</template>
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { excerptsApi, excerptError, excerptTime, type ExcerptEdit } from '@/api/excerpts';
import ExcerptEditor from './ExcerptEditor.vue';
const props = defineProps<{ animeId: number; link: string; season: number; episode: number; translationId?: number | string | null }>();
const emit = defineEmits<{ requestTime: [] }>();
const auth = useAuthStore();
const material = ref<{ season: number; episode: number; translation_id: number; translation_title: string } | null>(null);
const duration = ref(0), start = ref<number | null>(null), end = ref<number | null>(null);
const pending = ref<'start' | 'end' | null>(null), error = ref(''), busy = ref(false), saved = ref<number | null>(null);
let timeout: ReturnType<typeof setTimeout> | undefined;
let generation = 0;
function reset() { generation++; start.value = end.value = null; pending.value = null; saved.value = null; error.value = ''; clearTimeout(timeout); }
watch(() => [props.animeId, props.link, props.season, props.episode, props.translationId], (value, before) => {
  reset();
  const observed = material.value;
  if (value[0] !== before[0] || value[1] !== before[1] || !observed || observed.season !== props.season || observed.episode !== props.episode || String(observed.translation_id) !== String(props.translationId)) {
    material.value = null; duration.value = 0;
  }
});
function observeEpisode(data: { episode: number | null; season: number | null; translation: { id: number; title?: string } }) {
  const next = { episode: data.episode ?? props.episode, season: data.season ?? props.season, translation_id: Number(data.translation.id), translation_title: data.translation.title || '' };
  if (material.value && JSON.stringify(next) !== JSON.stringify(material.value)) { reset(); duration.value = 0; }
  material.value = next.translation_id > 0 ? next : null;
}
function observeDuration(value: number) { duration.value = Number.isFinite(value) && value > 0 ? value : 0; }
function mark(boundary: 'start' | 'end') {
  pending.value = boundary; error.value = ''; emit('requestTime');
  clearTimeout(timeout); timeout = setTimeout(() => { pending.value = null; error.value = 'Плеер не ответил. Повторите выбор времени.'; }, 1500);
}
function captureTime(value: number) {
  const boundary = pending.value;
  if (!boundary || !material.value || !Number.isFinite(value) || value < 0 || value > duration.value) return;
  clearTimeout(timeout); pending.value = null; saved.value = null;
  if (boundary === 'start') { start.value = value; end.value = null; } else end.value = value;
}
const draft = computed(() => ({ start: start.value ?? 0, end: end.value ?? 0, title: '', description: '', duration: duration.value }));
async function save(value: ExcerptEdit) {
  if (!material.value || !auth.isAuthenticated || busy.value) return;
  const version = generation; busy.value = true; error.value = '';
  try {
    const { season, episode, translation_id } = material.value;
    const { data } = await excerptsApi.create({ ...value, season, episode, translation_id, anime_id: props.animeId, duration: duration.value });
    if (version === generation) { reset(); saved.value = data.id; }
  } catch (e) { if (version === generation) error.value = excerptError(e); }
  finally { busy.value = false; }
}
defineExpose({ captureTime, observeEpisode, observeDuration });
onBeforeUnmount(() => clearTimeout(timeout));
</script>
<style scoped>
.capture{margin:12px 0}.capture-actions{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:12px}button{padding:10px 12px;border:1px solid var(--border-color);border-radius:8px;background:var(--surface-2);color:var(--text-primary);cursor:pointer}button:disabled{opacity:.5}small{color:var(--text-secondary)}p[role=alert]{color:var(--color-danger,#e66)}
</style>
