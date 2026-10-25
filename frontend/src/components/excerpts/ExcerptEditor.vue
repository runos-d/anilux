<template>
  <form class="excerpt-editor" @submit.prevent="save">
    <div class="excerpt-fields">
      <label>Начало <input v-model="start" inputmode="decimal" required aria-label="Начало отрывка вручную" /></label>
      <label>Конец <input v-model="end" inputmode="decimal" required aria-label="Конец отрывка вручную" /></label>
    </div>
    <small>Секунды или мин:сек. Длительность видео: {{ excerptTime(value.duration) }}</small>
    <label>Название (необязательно)<input v-model="title" maxlength="200" /></label>
    <label>Описание (необязательно)<textarea v-model="description" maxlength="5000" rows="3" /></label>
    <p v-if="error" role="alert">{{ error }}</p>
    <div class="excerpt-actions"><button :disabled="busy" type="submit">{{ busy ? 'Сохранение…' : 'Сохранить отрывок' }}</button><button type="button" @click="$emit('cancel')">Отмена</button></div>
  </form>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
import { excerptTime, parseExcerptTime, type ExcerptEdit } from '@/api/excerpts';
const props = defineProps<{ value: ExcerptEdit & { duration: number }; busy?: boolean }>();
const emit = defineEmits<{ save: [value: ExcerptEdit]; cancel: [] }>();
const start = ref(''), end = ref(''), title = ref(''), description = ref(''), error = ref('');
watch(() => props.value, value => {
  start.value = String(value.start); end.value = String(value.end);
  title.value = value.title; description.value = value.description; error.value = '';
}, { immediate: true, deep: true });
function save() {
  const a = parseExcerptTime(start.value), b = parseExcerptTime(end.value);
  if (!Number.isFinite(a) || !Number.isFinite(b) || !(0 <= a && a < b && b <= props.value.duration)) {
    error.value = 'Начало должно быть неотрицательным, конец -больше начала и в пределах видео.'; return;
  }
  error.value = ''; emit('save', { start: a, end: b, title: title.value.trim(), description: description.value.trim() });
}
</script>
<style scoped>
.excerpt-editor{display:grid;gap:12px;padding:16px;border:1px solid var(--border-color);border-radius:12px;background:var(--surface-2)}
label{display:grid;gap:6px}input,textarea{width:100%;min-width:0;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--surface-3);color:var(--text-primary);font:inherit}
.excerpt-fields,.excerpt-actions{display:flex;flex-wrap:wrap;gap:12px}.excerpt-fields label{flex:1;min-width:110px}button{padding:10px 14px;border:0;border-radius:8px;background:var(--accent);color:white;cursor:pointer}button:disabled{opacity:.5}small{color:var(--text-secondary)}p{color:var(--color-danger,#e66)}
</style>
