<template>
  <div class="browser-permission">
    <button v-if="permission === 'default'" type="button" @click="enable">Разрешить уведомления на компьютере</button>
    <p v-else-if="permission === 'granted'">Уведомления на компьютере разрешены</p>
    <p v-else-if="permission === 'denied'">Уведомления заблокированы в настройках этого сайта в браузере</p>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue';
const permission = ref('Notification' in window ? Notification.permission : 'unsupported');
const enable = async () => { permission.value = await Notification.requestPermission(); };
</script>
<style scoped>
.browser-permission { margin: 12px 0; color: var(--text-secondary); font-size: 13px; }
.browser-permission button { padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border-subtle); background: var(--surface-3); color: var(--text-primary); cursor: pointer; }
</style>
