<template>
  <main class="excerpts-page"><h1>Мои отрывки</h1><p>Личные закладки на диапазоны серий. Новые -сверху.</p>
    <label>Поиск <input v-model="query" placeholder="Аниме, название или описание" /></label><p v-if="error" role="alert">{{ error }}</p><p v-if="loading">Загрузка…</p>
    <div class="excerpt-grid"><article v-for="row in rows" :key="row.id"><ExcerptCard :excerpt="row" owner />
      <ExcerptEditor v-if="editing === row.id && !row.unavailable" :value="row" :busy="busy" @save="save(row, $event)" @cancel="editing = null" />
      <div v-else class="actions"><button v-if="!row.unavailable" @click="editing = row.id">Редактировать</button><button v-if="!row.unavailable" :disabled="busy" @click="share(row)">{{ row.shared ? 'Отключить ссылку' : 'Включить ссылку' }}</button><button v-if="row.share_path && !row.unavailable" @click="copy(row)">Копировать ссылку</button><button :disabled="busy" @click="remove(row)">Удалить</button></div>
    </article></div><p v-if="!loading && !rows.length">Отрывков нет. Выберите начало и конец рядом с плеером аниме.</p><button v-if="next" :disabled="loading" @click="load(next)">Показать ещё</button><p v-if="notice" role="status">{{ notice }}</p>
  </main>
</template>
<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
import { excerptsApi, excerptError, type Excerpt, type ExcerptEdit } from '@/api/excerpts';
import ExcerptCard from '@/components/excerpts/ExcerptCard.vue';
import ExcerptEditor from '@/components/excerpts/ExcerptEditor.vue';
const rows = ref<Excerpt[]>([]), query = ref(''), next = ref<number | null>(null), editing = ref<number | null>(null);
const loading = ref(false), busy = ref(false), error = ref(''), notice = ref('');
let timer: ReturnType<typeof setTimeout> | undefined, generation = 0;
async function load(page = 1) {
  const version = ++generation; loading.value = true; error.value = '';
  try { const { data } = await excerptsApi.list(query.value, page); if (version === generation) { rows.value = page === 1 ? data.results : [...rows.value, ...data.results]; next.value = data.next; } }
  catch (e) { if (version === generation) error.value = excerptError(e); }
  finally { if (version === generation) loading.value = false; }
}
async function save(row: Excerpt, values: ExcerptEdit) {
  busy.value = true; error.value = '';
  try { const { data } = await excerptsApi.update(row.id, values); Object.assign(row, data); editing.value = null; }
  catch (e) { error.value = excerptError(e); } finally { busy.value = false; }
}
async function share(row: Excerpt) {
  busy.value = true; error.value = '';
  try { const { data } = await excerptsApi.update(row.id, { shared: !row.shared }); Object.assign(row, data); }
  catch (e) { error.value = excerptError(e); } finally { busy.value = false; }
}
async function copy(row: Excerpt) { try { await navigator.clipboard.writeText(new URL(row.share_path!, location.origin).href); notice.value = 'Ссылка скопирована'; } catch { error.value = 'Не удалось скопировать ссылку'; } }
async function remove(row: Excerpt) { if (!confirm('Удалить отрывок? Старые ссылки и вложения станут недоступны.')) return; busy.value = true; try { await excerptsApi.delete(row.id); rows.value = rows.value.filter(item => item.id !== row.id); } catch (e) { error.value = excerptError(e); } finally { busy.value = false; } }
watch(query, () => { generation++; clearTimeout(timer); timer = setTimeout(() => void load(), 250); });
function refreshOnFocus() { if (!editing.value && !busy.value) void load(); }
onMounted(() => { void load(); window.addEventListener('focus', refreshOnFocus); });
onBeforeUnmount(() => { generation++; clearTimeout(timer); window.removeEventListener('focus', refreshOnFocus); });
</script>
<style scoped>
.excerpts-page{max-width:1200px;margin:auto;padding:24px;color:var(--text-primary)}input{width:100%;padding:12px;background:var(--surface-2);color:inherit;border:1px solid var(--border-color);border-radius:8px}.excerpt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:20px;margin:16px 0}.actions{display:flex;flex-wrap:wrap;gap:8px}button{padding:9px 12px;border:1px solid var(--border-color);border-radius:8px;background:var(--surface-3);color:inherit;cursor:pointer}button:disabled{opacity:.5}p{color:var(--text-secondary)}@media(max-width:600px){.excerpts-page{padding:14px}}
</style>
