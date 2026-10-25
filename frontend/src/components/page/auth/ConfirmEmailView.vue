<template>
  <main class="auth-result" aria-live="polite">
    <h1>Подтверждение email</h1>
    <p>{{ message }}</p>
    <router-link to="/login">Перейти ко входу</router-link>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/api/client'

const route = useRoute()
const message = ref('Проверяем ссылку…')

onMounted(async () => {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!token) {
    message.value = 'Ссылка недействительна.'
    return
  }
  try {
    await apiClient.get('/users/confirm-email/', { params: { token } })
    message.value = 'Email подтверждён.'
  } catch {
    message.value = 'Ссылка недействительна, устарела или уже использована.'
  }
})
</script>

<style scoped>
.auth-result { max-width: 32rem; margin: 5rem auto; padding: 2rem; text-align: center; }
</style>
