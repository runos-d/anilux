<template><main class="oauth-result"><p aria-live="polite">{{ message }}</p></main></template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/api/client'

const route = useRoute()
const router = useRouter()
const message = ref('Завершаем вход…')

onMounted(async () => {
  const code = typeof route.query.code === 'string' ? route.query.code : ''
  try {
    const { data } = await apiClient.post('/users/google/exchange/', { code })
    localStorage.setItem('anilux_access_token_v1', data.tokens.access)
    localStorage.setItem('anilux_refresh_token_v1', data.tokens.refresh)
    localStorage.setItem('anilux_user_v1', JSON.stringify(data.user))
    await router.replace('/')
    window.location.reload()
  } catch {
    message.value = 'Не удалось завершить вход. Код устарел или уже использован.'
  }
})
</script>

<style scoped>.oauth-result { min-height: 60vh; display: grid; place-content: center; }</style>
