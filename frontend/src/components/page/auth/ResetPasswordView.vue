<template>
  <main class="auth-result">
    <h1>Новый пароль</h1>
    <form v-if="!success" @submit.prevent="submit">
      <label for="new-password">Пароль</label>
      <input id="new-password" v-model="password" type="password" autocomplete="new-password" required />
      <button type="submit" :disabled="loading">Сохранить</button>
    </form>
    <p aria-live="polite">{{ message }}</p>
    <router-link v-if="success" to="/login">Войти</router-link>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/api/client'

const route = useRoute()
const password = ref('')
const message = ref('')
const loading = ref(false)
const success = ref(false)

async function submit() {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!token) { message.value = 'Ссылка недействительна.'; return }
  loading.value = true
  try {
    await apiClient.post('/users/password-reset/confirm/', { token, new_password: password.value })
    success.value = true
    message.value = 'Пароль изменён. Все прежние сеансы завершены.'
  } catch (error: unknown) {
    const failure = error as { response?: { data?: { new_password?: string[] } } }
    message.value = failure.response?.data?.new_password?.join(' ') || 'Ссылка недействительна или устарела.'
  } finally { loading.value = false }
}
</script>

<style scoped>
.auth-result { max-width: 32rem; margin: 5rem auto; padding: 2rem; text-align: center; }
form { display: grid; gap: 1rem; }
</style>
