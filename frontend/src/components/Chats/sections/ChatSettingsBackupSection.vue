<template>
  <section class="backup-section">
    <h2>Резервные копии</h2>
    <p>Архив содержит историю, участников, темы и файлы чата.</p>
    <button :disabled="busy" @click="createBackup">Создать копию</button>
    <p v-if="error" role="alert">{{ error }}</p>
    <p v-if="!backups.length && !busy">Резервных копий пока нет.</p>
    <article v-for="backup in backups" :key="backup.id">
      <strong>{{ new Date(backup.created_at).toLocaleString('ru-RU') }}</strong>
      <p>{{ backup.status_display }} · {{ backup.messages_count }} сообщений · {{ backup.file_size_mb }} МБ</p>
      <p v-if="backup.error_message" role="alert">{{ backup.error_message }}</p>
      <button v-if="backup.status === 'completed'" :disabled="busy" @click="downloadBackup(backup)">Скачать</button>
      <button v-if="backup.status === 'completed' && canRestore && !backup.restored_at" :disabled="busy" @click="previewRestore(backup)">Проверить восстановление</button>
      <span v-if="backup.restored_at">Восстановлено</span>
      <button v-if="backup.status === 'failed'" :disabled="busy" @click="retryBackup(backup)">Повторить</button>
      <button :disabled="busy || backup.status === 'creating'" @click="deleteBackup(backup)">Удалить копию</button>
    </article>
    <div v-if="preview" role="region" aria-label="Проверка восстановления">
      <p>Проверка пройдена: {{ preview.messages_count }} сообщений, {{ preview.members_count }} участников.</p>
      <p>Текущий владелец, баны и новые сообщения сохранятся. Восстановленные запланированные отправки будут отменены.</p>
      <button :disabled="busy" @click="restoreBackup">Восстановить проверенную копию</button>
      <button :disabled="busy" @click="preview = null">Отмена</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { backupsApi, type ChatBackup } from '@/api/chats';
const props = defineProps<{ chatId: number; canRestore: boolean }>();
const emit = defineEmits<{ restored: [] }>();
const backups = ref<ChatBackup[]>([]);
const busy = ref(false), error = ref('');
const preview = ref<{ id: number; messages_count: number; members_count: number } | null>(null);
let timer: ReturnType<typeof setTimeout> | undefined;
let disposed = false;
const message = (cause: unknown) => {
  const detail = (cause as { response?: { data?: unknown } }).response?.data;
  return detail ? JSON.stringify(detail) : 'Не удалось выполнить действие. Попробуйте ещё раз.';
};
const load = async () => {
  clearTimeout(timer);
  try {
    const { data } = await backupsApi.list(props.chatId);
    if (disposed) return;
    backups.value = Array.isArray(data) ? data : (data as { results: ChatBackup[] }).results;
    if (backups.value.some(backup => backup.status === 'creating')) timer = setTimeout(load, 4000);
  } catch (cause) { if (!disposed) error.value = message(cause); }
};
const run = async (action: () => Promise<unknown>) => {
  if (busy.value) return;
  busy.value = true; error.value = '';
  try { await action(); if (!disposed) await load(); }
  catch (cause) { if (!disposed) error.value = message(cause); }
  finally { busy.value = false; }
};
const createBackup = () => run(() => backupsApi.create(props.chatId));
const retryBackup = (backup: ChatBackup) => run(() => backupsApi.retry(backup.id));
const deleteBackup = (backup: ChatBackup) => {
  if (confirm('Удалить эту резервную копию? История чата сохранится.')) void run(() => backupsApi.delete(backup.id));
};
const downloadBackup = (backup: ChatBackup) => run(async () => {
  const { data } = await backupsApi.download(backup.id);
  const url = URL.createObjectURL(data), link = document.createElement('a');
  link.href = url; link.download = `chat-${props.chatId}-${backup.id}.zip`; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
const previewRestore = (backup: ChatBackup) => run(async () => {
  preview.value = null;
  const { data } = await backupsApi.restore(backup.id, true);
  if (!disposed) preview.value = { ...data, id: backup.id };
});
const restoreBackup = () => run(async () => {
  if (!preview.value) return;
  await backupsApi.restore(preview.value.id);
  preview.value = null;
  emit('restored');
});
onMounted(load);
onUnmounted(() => { disposed = true; clearTimeout(timer); });
</script>

<style scoped>
.backup-section { display: grid; gap: 1rem; }
article, [role=region] { border: 1px solid var(--border-color, #444); border-radius: 12px; padding: 1rem; }
button { cursor: pointer; padding: .5rem .8rem; margin: .25rem; border: 1px solid currentColor; border-radius: 8px; }
button:disabled { opacity: .5; cursor: default; }
[role=alert] { color: #ef6b73; overflow-wrap: anywhere; }
</style>
