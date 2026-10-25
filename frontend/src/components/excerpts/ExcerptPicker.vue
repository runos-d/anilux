<template>
  <div class="picker"><label>Найти свой отрывок <input v-model="query" placeholder="Аниме, название или описание" /></label>
    <p>При отправке просмотр по ссылке включится автоматически.</p><p v-if="error" role="alert">{{ error }}</p><p v-if="loading">Загрузка…</p>
    <div v-for="row in rows" :key="row.id"><button v-if="!row.unavailable" class="pick" :aria-pressed="selected.some(item => item.id === row.id)" @click="toggle(row)">{{ selected.some(item => item.id === row.id) ? '✓ Выбран' : '+ Выбрать' }} · {{ row.anime_title }} · {{ row.title || `Серия ${row.episode}` }} · {{ excerptTime(row.start) }} -{{ excerptTime(row.end) }}</button></div>
    <p v-if="!loading && !rows.length">Отрывков пока нет. Сохраните диапазон рядом с плеером аниме.</p><button v-if="next" @click="load(next)">Показать ещё</button>
  </div>
</template>
<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
import { excerptsApi, excerptError, excerptTime, type Excerpt } from '@/api/excerpts';
const props = withDefaults(defineProps<{ selected?: Excerpt[] }>(), { selected: () => [] });
const emit = defineEmits<{ 'update:selected': [value: Excerpt[]] }>();
const query = ref(''), rows = ref<Excerpt[]>([]), next = ref<number | null>(null), loading = ref(false), error = ref('');
let timer: ReturnType<typeof setTimeout> | undefined, generation = 0;
async function load(page = 1) {
  const version = ++generation; loading.value = true; error.value = '';
  try { const { data } = await excerptsApi.list(query.value, page); if (version === generation) { rows.value = page === 1 ? data.results : [...rows.value, ...data.results]; next.value = data.next; } }
  catch (e) { if (version === generation) error.value = excerptError(e); }
  finally { if (version === generation) loading.value = false; }
}
function toggle(row: Excerpt) {
  if (props.selected.some(item => item.id === row.id)) emit('update:selected', props.selected.filter(item => item.id !== row.id));
  else if (props.selected.length < 10) emit('update:selected', [...props.selected, row]);
  else error.value = 'Можно прикрепить до 10 отрывков.';
}
watch(query, () => { generation++; clearTimeout(timer); timer = setTimeout(() => void load(), 250); });
onMounted(() => void load()); onBeforeUnmount(() => { generation++; clearTimeout(timer); });
</script>
<style scoped>
.picker{padding:12px}.picker label{display:grid;gap:8px}input,.pick{width:100%;padding:12px;border:1px solid var(--border-color);border-radius:8px;background:var(--surface-2);color:var(--text-primary)}.pick{margin:4px 0;text-align:left;cursor:pointer}.pick[aria-pressed=true]{border-color:var(--accent)}p{font-size:13px;color:var(--text-secondary)}
</style>
