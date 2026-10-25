<template>
  <div class="auth-page">
    <div class="container auth-container">
      <div class="auth-card">
        <h2>Регистрация</h2>
        <p class="auth-subtitle"></p>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          {{ success }}
        </div>

        <form @submit.prevent="handleRegister" class="auth-form">
          <div class="form-group">
            <label for="username">Имя пользователя</label>
            <input
              v-model="form.username"
              type="text"
              id="username"
              placeholder="Придумайте имя пользователя"
              required
            />
          </div>

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
              placeholder="Придумайте пароль"
              required
            />
          </div>

          <div class="form-group">
            <label for="confirmPassword">Подтверждение пароля</label>
            <input
              v-model="form.confirmPassword"
              type="password"
              id="confirmPassword"
              placeholder="Повторите пароль"
              required
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary btn-block"
            :disabled="loading"
          >
            {{ loading ? "Регистрация..." : "Зарегистрироваться" }}
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
          Продолжить с Google
        </button>

        <div class="auth-footer">
          <p>Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
          <router-link to="/" class="back-link"><SakuraIcon name="arrow-left" :size="16" /> На главную</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import apiClient from "@/api/client";
import type { AxiosError } from "axios";

const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);
const error = ref("");
const success = ref("");
interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

const form = ref<RegisterForm>({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});

const handleRegister = async () => {
  loading.value = true;
  error.value = "";
  success.value = "";

  if (form.value.password !== form.value.confirmPassword) {
    error.value = "Пароли не совпадают";
    loading.value = false;
    return;
  }

  if (form.value.password.length < 8) {
    error.value = "Пароль должен содержать минимум 8 символов";
    loading.value = false;
    return;
  }

  try {
    const registerData = {
      username: form.value.username,
      email: form.value.email,
      password: form.value.password,
      password_confirm: form.value.confirmPassword,
    };

    await apiClient.post("/users/register/", registerData);

    const loginResult = await authStore.login(
      form.value.email,
      form.value.password,
    );

    if (loginResult.success) {
      success.value = "Регистрация успешна! Вы вошли в аккаунт.";
      setTimeout(() => {
        router.push("/");
      }, 2000);
    } else {
      error.value =
        "Регистрация прошла успешно, но не удалось войти. Попробуйте войти вручную.";
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    }
  } catch (err) {
    const axiosError = err as AxiosError;
    if (axiosError.response?.data) {
      const errors = axiosError.response.data as Record<string, string[]>;
      if (errors.username) {
        error.value = "Имя пользователя: " + errors.username.join(", ");
      } else if (errors.email) {
        error.value = "Email: " + errors.email.join(", ");
      } else if (errors.password) {
        error.value = "Пароль: " + errors.password.join(", ");
      } else {
        error.value = "Ошибка регистрации";
      }
    } else {
      error.value = "Ошибка сети. Попробуйте позже.";
    }
  } finally {
    loading.value = false;
  }
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

.success-message {
  background: var(--success-subtle);
  color: var(--success);
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

.btn-google {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  white-space: normal;
}
.btn-google:hover { background: var(--surface-5); }
.google-icon { width: 18px; height: 18px; flex-shrink: 0; }

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

/* Auth method selector */
.auth-method-selector {
  display: flex;
  margin-bottom: 1rem;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid var(--border-default);
}

.auth-method-btn {
  flex: 1;
  min-height: 44px;
  padding: 0.5rem;
  border: none;
  background: var(--surface-2);
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.auth-method-btn.active {
  background: var(--accent);
  color: var(--text-on-accent);
}

.auth-method-btn:hover:not(.active) {
  background: var(--surface-4);
  color: var(--text-primary);
}

@media (max-width: 767px) {
  .auth-container { min-height: calc(100dvh - 50px); padding: 1.25rem 1rem; }
  .auth-card { padding: 1.5rem; }
  .form-group input { min-height: 44px; }
}
@media (max-width: 374px) {
  .auth-container { padding: 1rem 0.5rem; }
  .auth-card { padding: 1.25rem; }
  .btn-block { font-size: 0.9rem; }
}
</style>
