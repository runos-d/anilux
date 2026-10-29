<template>
  <section class="storage-settings">
    <h2>Данные и хранилище</h2>
    <p v-if="error" role="alert">{{ error }}</p>
    <template v-if="usage">
      <p>Использовано {{ formatBytes(usage.used) }} из {{ formatBytes(usage.limit) }}</p>
      <progress :value="usage.used" :max="usage.limit" aria-label="Использование хранилища" />
      <dl><template v-for="(label, key) in categories" :key="key"><dt>{{ label }}</dt><dd>{{ formatBytes(usage[key]) }}</dd></template></dl>
    </template>
    <button type="button" :disabled="busy" @click="clear">Очистить временный кэш</button>
    <p role="status">{{ message }}</p>
  </section>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import * as settingsApi from '@/api/settings';
const usage = ref<Record<string, number> | null>(null);
const busy = ref(false), error = ref(''), message = ref('');
const categories = { messages: 'Сообщения', media: 'Медиа', documents: 'Документы', audio: 'Аудио', cache: 'Временный кэш' };
const formatBytes = (value = 0) => `${(value / 1024 ** 2).toFixed(2)} МБ`;
const load = async () => { try { usage.value = await settingsApi.getStorageUsage(); } catch { error.value = 'Не удалось загрузить данные'; } };
const clear = async () => {
  busy.value = true; error.value = '';
  try { await settingsApi.clearCache(['cache']); await load(); message.value = 'Временный кэш очищен'; }
  catch { error.value = 'Не удалось очистить кэш'; }
  finally { busy.value = false; }
};
onMounted(load);
</script>
<style scoped>.storage-settings { padding: 24px; } dl { display: grid; grid-template-columns: 1fr 1fr; } button { padding: 12px; }</style>
