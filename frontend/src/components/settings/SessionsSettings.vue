<template>
  <section class="sessions-settings">
    <h2>Активные сессии</h2>
    <p v-if="error" role="alert">{{ error }}</p>
    <ul><li v-for="session in sessions" :key="session.id">
      <strong>{{ session.device_name }}</strong>
      <span v-if="session.is_current_device"> · Это устройство</span>
      <p>{{ session.location }} · {{ new Date(session.last_activity).toLocaleString() }}</p>
      <button v-if="!session.is_current_device" type="button" :disabled="busy" @click="terminate(session.session_key)">Завершить сессию</button>
    </li></ul>
    <button type="button" :disabled="busy" @click="terminateAll">Завершить все другие сессии</button>
  </section>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import * as settingsApi from '@/api/settings';
interface Session { id: number; session_key: string; device_name: string; location: string; last_activity: string; is_current_device: boolean }
const sessions = ref<Session[]>([]), busy = ref(false), error = ref('');
const load = async () => { sessions.value = await settingsApi.getActiveSessions(); };
const run = async (action: () => Promise<unknown>) => {
  busy.value = true; error.value = '';
  try { await action(); await load(); } catch { error.value = 'Не удалось обновить сессии'; } finally { busy.value = false; }
};
const terminate = (key: string) => run(() => settingsApi.terminateSession(key));
const terminateAll = () => run(() => settingsApi.terminateAllOtherSessions());
onMounted(() => { void run(load); });
</script>
<style scoped>.sessions-settings { padding: 24px; } li { margin-bottom: 20px; } button { padding: 10px; }</style>
