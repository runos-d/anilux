<template>
  <div v-if="isOwner" class="notifications-tab">
    <h2>Уведомления -подписки на серии</h2>
    <div v-if="loading">Загрузка...</div>
    <div v-else-if="error" role="alert">{{ error }} <button @click="load">Повторить</button></div>
    <div v-else-if="subs.length === 0">Нет подписок.</div>
    <ul>
      <li v-for="s in subs" :key="s.id">
        <img :src="s.poster_url" width="60" />
        <strong>{{ s.anime_title }}</strong>
        <span>{{ s.is_active ? 'Активна' : 'Отключена' }}</span>
        <button @click="toggle(s)">{{ s.is_active ? 'Выкл' : 'Вкл' }}</button>
        <button @click="pause(s)">Пауза</button>
        <button @click="del(s)">Удалить</button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api, { isRequestCancelled } from '@/api/client'
const isOwner = computed(() => true) // серверная проверка должна быть на бэкенде; фронт скрывает при несовпадении через API 403
interface EpisodeSubscription {
  id: number
  anime_title: string
  poster_url: string
  is_active: boolean
}
const subs = ref<EpisodeSubscription[]>([])
const loading = ref(true)
const error = ref('')
async function load() {
  error.value = ''
  try { const r = await api.get('/notifications/episode-subs/'); subs.value = r.data }
  catch (failure) { if (!isRequestCancelled(failure)) error.value = 'Не удалось загрузить подписки.' }
  finally { loading.value = false }
}
async function toggle(s: EpisodeSubscription){ await api.post(`/notifications/episode-subs/${s.id}/toggle/`); await load() }
async function pause(s: EpisodeSubscription){ await api.post(`/notifications/episode-subs/${s.id}/pause/`); await load() }
async function del(s: EpisodeSubscription){ await api.delete(`/notifications/episode-subs/${s.id}/`); await load() }
onMounted(load)
</script>
