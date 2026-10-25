<template>
  <div class="auth-page">
    <div class="container auth-container">
      <div class="auth-card">
        <h2>Вход в аккаунт</h2>
        <p class="auth-subtitle">Войдите чтобы использовать все возможности</p>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <form @submit.prevent="handleLogin" class="auth-form">
          <div class="form-group">
            <label for="email">Email</label>
            <input
              v-model="form.email"
              type="email"
              id="email"
              placeholder="Введите email"
              required
            />
          </div>

          <div class="form-group">
            <label for="password">Пароль</label>
            <input
              v-model="form.password"
              type="password"
              id="password"
              placeholder="Введите пароль"
              required
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary btn-block"
            :disabled="loading"
          >
            {{ loading ? "Вход..." : "Войти" }}
          </button>
        </form>

        <div class="auth-divider">
          <span>или</span>
        </div>

        <button @click="handleGoogleLogin" class="btn btn-google btn-block">
          <svg class="google-icon" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Войти через Google
        </button>

        <div class="auth-footer">
          <p>
            Нет аккаунта?
            <router-link to="/register">Зарегистрироваться</router-link>
          </p>
          <router-link to="/" class="back-link"><SakuraIcon name="arrow-left" :size="16" /> На главную</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import apiClient from "@/api/client";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const loading = ref(false);
const error = ref("");
const form = ref({
  email: "",
  password: "",
});

const handleLogin = async () => {
  loading.value = true;
  error.value = "";

  const result = await authStore.login(
    form.value.email,
    form.value.password,
  );

  if (result.success) {
    const destination = route.query.redirect;
    router.push(typeof destination === 'string' && destination.startsWith('/') && !destination.startsWith('//') ? destination : '/');
  } else {
    error.value = "Неверный email или пароль";
  }

  loading.value = false;
};

const handleGoogleLogin = async () => {
  try {
    const response = await apiClient.get("/users/google/");
    const { auth_url } = response.data;
    window.location.href = auth_url;
  } catch (error) {
    console.error("Google OAuth error:", error);
    alert("Ошибка инициализации Google OAuth");
  }
};
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
}

.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 64px);
  padding: 2rem 1rem;
}

.auth-card {
  background: var(--surface-3);
  padding: 2rem;
  border-radius: 1rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 400px;
  border: 1px solid var(--border-default);
}

.auth-card h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.auth-subtitle {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.error-message {
  background: var(--danger-subtle);
  color: var(--danger);
  padding: 0.75rem;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  text-align: center;
}

.auth-form {
  margin-bottom: 1.5rem;
}

.auth-divider {
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
  color: var(--text-secondary);
}

.auth-divider::before,
.auth-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border-default);
}

.auth-divider span {
  padding: 0 1rem;
  font-size: 0.875rem;
}

.btn-google {
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  transition: all 0.2s;
}

.btn-google:hover {
  background: var(--surface-5);
  border-color: var(--border-strong);
}

.google-icon {
  width: 18px;
  height: 18px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 0.375rem;
}

.form-group input {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--border-default);
  border-radius: 0.375rem;
  font-size: 1rem;
  background: var(--surface-2);
  color: var(--text-primary);
  transition: border-color 0.2s;
}

.form-group input::placeholder {
  color: var(--text-tertiary);
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.btn-block {
  width: 100%;
  min-height: 44px;
  padding: 0.75rem;
  font-size: 1rem;
}

.auth-footer {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid var(--border-default);
}

.auth-footer p {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.auth-footer a {
  color: var(--accent-bright);
  text-decoration: none;
}

.back-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 44px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
}

/* ═══ АДАПТИВНЫЕ СТИЛИ (мобильные / планшеты) ═══════════════ */

/* xs: 320px – 374px */
@media (max-width: 374px) {
  .auth-container {
    padding: 1rem 0.5rem;
    min-height: calc(100vh - 48px);
    align-items: flex-start;
  }

  .auth-card {
    padding: 1.25rem;
    border-radius: 0.75rem;
  }

  .auth-card h2 {
    font-size: 1.25rem;
  }

  .auth-subtitle {
    font-size: 0.8rem;
    margin-bottom: 1rem;
  }

  .error-message {
    padding: 0.625rem;
    font-size: 0.8rem;
    margin-bottom: 0.75rem;
  }

  .auth-form {
    margin-bottom: 1rem;
  }

  .form-group {
    margin-bottom: 0.75rem;
  }

  .form-group label {
    font-size: 0.8rem;
    margin-bottom: 0.25rem;
  }

  .form-group input {
    padding: 0.55rem 0.65rem;
    font-size: 0.95rem;
  }

  .btn-block {
    padding: 0.7rem;
    font-size: 0.9rem;
  }

  .auth-divider {
    margin: 1rem 0;
  }

  .auth-divider span {
    padding: 0 0.75rem;
    font-size: 0.8rem;
  }

  .google-icon {
    width: 16px;
    height: 16px;
  }

  .auth-footer {
    padding-top: 0.875rem;
  }

  .auth-footer p {
    font-size: 0.8rem;
    margin-bottom: 0.75rem;
  }

  .back-link {
    font-size: 0.8rem;
  }
}

/* sm: 375px – 767px */
@media (min-width: 375px) and (max-width: 767px) {
  .auth-container {
    padding: 1.25rem 1rem;
    align-items: center;
    min-height: calc(100vh - 56px);
  }

  .auth-card {
    padding: 1.5rem;
    max-width: 400px;
  }

  .auth-card h2 {
    font-size: 1.35rem;
  }

  .auth-subtitle {
    font-size: 0.875rem;
    margin-bottom: 1.25rem;
  }

  .error-message {
    font-size: 0.85rem;
    padding: 0.7rem;
  }

  .form-group input {
    padding: 0.6rem 0.7rem;
    font-size: 0.95rem;
  }

  .btn-block {
    padding: 0.7rem;
  }

  .auth-divider {
    margin: 1.25rem 0;
  }
}

/* md: 768px – 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .auth-container {
    padding: 2rem;
    min-height: calc(100vh - 72px);
  }

  .auth-card {
    max-width: 420px;
    padding: 2.25rem;
  }
}

/* Ландшафтная ориентация на мобильных -уменьшаем вертикальные отступы */
@media (max-width: 767px) and (orientation: landscape) {
  .auth-container {
    padding: 1rem;
    min-height: auto;
    align-items: flex-start;
  }

  .auth-card {
    padding: 1.25rem 1.5rem;
  }

  .auth-card h2 {
    font-size: 1.2rem;
  }

  .auth-subtitle {
    margin-bottom: 1rem;
  }

  .form-group {
    margin-bottom: 0.75rem;
  }

  .auth-divider {
    margin: 1rem 0;
  }

  .auth-footer {
    padding-top: 0.75rem;
  }
}

/* Улучшение тач-взаимодействия */
@media (hover: none) and (pointer: coarse) {
  .btn-google:hover {
    background: var(--surface-4);
    border-color: var(--border-default);
  }

  .btn-google:active {
    background: var(--surface-5);
    border-color: var(--border-strong);
  }

  .form-group input {
    min-height: 44px;
    font-size: 16px; /* предотвращает zoom на iOS при фокусе */
  }
}
</style>
