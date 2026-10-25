<template>
  <div class="chat-invite-page">
    <div class="invite-container">
      <div v-if="loading" class="invite-loading">
        <div class="loading-spinner"></div>
        <p>Загрузка приглашения...</p>
      </div>

      <div v-else-if="!authStore.isAuthenticated" class="invite-info">
        <h2>Приглашение в чат</h2>
        <p>Войдите, чтобы присоединиться к чату.</p>
        <button class="btn-join" @click="goToLogin">Войти</button>
      </div>
      <div v-else-if="error" class="invite-error">
        <div class="error-icon"><SakuraIcon name="x" /></div>
        <h2>Ошибка</h2>
        <p>{{ error }}</p>
        <button class="btn-back" @click="goToHome">На главную</button>
      </div>

      <div v-else-if="joined" class="invite-success">
        <div class="success-icon"><SakuraIcon name="check" /></div>
        <h2>Добро пожаловать!</h2>
        <p>Вы успешно присоединились к чату "{{ chatName }}"</p>
        <button class="btn-go-chat" @click="goToChat">Перейти в чат</button>
      </div>

      <div v-else-if="invite" class="invite-info">
        <div v-if="chatAvatarUrl" class="chat-avatar-large">
          <img :src="chatAvatarUrl" :alt="invite.chat_name" />
        </div>
        <div v-else class="chat-avatar-placeholder-large">
          {{ getInitials(invite.chat_name) }}
        </div>

        <h1 class="chat-name">{{ invite.chat_name }}</h1>
        <p class="invite-description">
          Вас приглашают присоединиться к этому чату
        </p>

        <div class="invite-details">
          <div class="detail-item">
            <span class="detail-icon"> <SakuraIcon name="user" /> </span>
            <span class="detail-text">
              Приглашает: <strong>{{ invite.creator?.username || "участник чата" }}</strong>
            </span>
          </div>

          <div class="detail-item">
            <span class="detail-icon"> <SakuraIcon name="users" /> </span>
            <span class="detail-text">
              Использовано: {{ invite.usage_count }} /
              {{ invite.usage_limit || "∞" }}
            </span>
          </div>

          <div v-if="invite.expires_at" class="detail-item">
            <span class="detail-icon"> <SakuraIcon name="clock" /> </span>
            <span class="detail-text">
              Истекает: {{ formatDate(invite.expires_at) }}
            </span>
          </div>

          <div class="detail-item">
            <span class="detail-icon"> <SakuraIcon name="clipboard" /> </span>
            <span
              :class="[
                'detail-text',
                { active: invite.is_valid, inactive: !invite.is_valid },
              ]"
            >
              {{
                !invite.is_revoked
                  ? "Приглашение активно"
                  : "Приглашение неактивно"
              }}
            </span>
          </div>
        </div>

        <div class="invite-actions">
          <button
            class="btn-join"
            @click="joinChat"
            :disabled="!invite.is_valid || joining"
          >
            {{ joining ? "Присоединение..." : "Присоединиться к чату" }}
          </button>
          <button class="btn-cancel" @click="goToHome">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useChatExtrasStore } from "@/stores/chatExtras";
import { useAuthStore } from "@/stores/auth";
import { useGroupChatStore } from "@/stores/groupChat";
import apiClient from "@/api/client";
import type { ChatInviteLink } from "@/api/chats";

const route = useRoute();
const router = useRouter();
const chatExtrasStore = useChatExtrasStore();
const authStore = useAuthStore();
const groupChatStore = useGroupChatStore();

const loading = ref(true);
const joining = ref(false);
const error = ref("");
const joined = ref(false);
const joinedChatId = ref<number | null>(null);
const authReady = ref(false);
const invite = ref<ChatInviteLink | null>(null);
const chatName = ref("");
const chatAvatarUrl = ref<string | null>(null);
const goToLogin = () => router.push({ path: '/login', query: { redirect: route.fullPath } });

const joinChat = async () => {
  if (!authStore.isAuthenticated) { void goToLogin(); return; }
  const token = String(route.params.token || '');
  if (!token) { error.value = 'Не указан токен приглашения'; loading.value = false; return; }
  joining.value = true;
  error.value = '';
  try {
    const result = await chatExtrasStore.joinByToken(token);
    if (token !== route.params.token) return;
    joinedChatId.value = result.chat_id;
    groupChatStore.restoreGroupChatToList(result.chat_id);
    chatName.value = result.chat_name || 'Чат';
    joined.value = result.status === 'joined';
  } catch (err: unknown) {
    const data = (err as { response?: { data?: { error?: string; detail?: string } } }).response?.data;
    error.value = data?.detail || data?.error || 'Не удалось воспользоваться приглашением';
  } finally { loading.value = false; joining.value = false; }
};
watch([() => authStore.isAuthenticated, () => route.params.token], () => {
  if (!authReady.value) return;
  joined.value = false; error.value = '';
  if (authStore.isAuthenticated) { loading.value = true; void joinChat(); }
  else { loading.value = false; }
});
onMounted(async () => {
  if (!authStore.isAuthenticated && localStorage.getItem('anilux_access_token_v1')) await authStore.checkAuth();
  authReady.value = true;
  if (authStore.isAuthenticated) await joinChat();
  else loading.value = false;
});
const goToChat = () => {
  if (joinedChatId.value) router.push({ path: `/chats/${joinedChatId.value}`, query: { type: 'group' } });
};

const goToHome = () => {
  router.push("/");
};

const getInitials = (name: string) => {
  if (!name) return "?";
  const words = name.split(" ").filter((w) => w.length > 0);
  if (words.length === 0) return name.substring(0, 2).toUpperCase();
  return words
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || "")
    .join("");
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};
</script>

<style scoped>
.chat-invite-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--surface-1);
}

.invite-container {
  max-width: 480px;
  width: 100%;
}

.invite-loading,
.invite-error,
.invite-success,
.invite-info {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  padding: 32px 24px;
  text-align: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
}

.invite-loading p,
.invite-error p,
.invite-success p {
  margin-top: 16px;
  font-size: 0.9375rem;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 44px;
  height: 44px;
  border: 3px solid var(--surface-4);
  border-top-color: var(--accent);
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-icon,
.success-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 1.75rem;
}

.error-icon {
  background: var(--surface-4);
  color: var(--danger);
}

.success-icon {
  background: var(--surface-4);
  color: var(--success);
}

.invite-error h2,
.invite-success h2 {
  margin: 0 0 8px;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.invite-error h2 {
  color: var(--danger);
}

.invite-success h2 {
  color: var(--text-primary);
}

.chat-avatar-large {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  margin: 0 auto 20px;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  background: var(--surface-4);
}

.chat-avatar-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chat-avatar-placeholder-large {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  margin: 0 auto 20px;
  background: var(--accent);
  color: var(--text-on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
}

.chat-name {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.invite-description {
  color: var(--text-secondary);
  font-size: 0.9375rem;
  margin: 0 0 24px;
}

.invite-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--surface-4);
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
  text-align: left;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.detail-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.detail-text strong {
  color: var(--text-primary);
  font-weight: 600;
}

.detail-text.active {
  color: var(--success);
}

.detail-text.inactive {
  color: var(--danger);
}

.invite-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.btn-join,
.btn-go-chat {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 38px;
  padding: 0 16px;
  background: var(--accent);
  border: 1px solid transparent;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-on-accent);
  cursor: pointer;
  transition: background-color 0.2s ease, opacity 0.2s ease;
}

.btn-join:hover:not(:disabled),
.btn-go-chat:hover {
  background: var(--accent-hover);
}

.btn-join:active:not(:disabled),
.btn-go-chat:active {
  opacity: 0.85;
}

.btn-join:disabled {
  background: var(--surface-4);
  color: var(--text-tertiary);
  cursor: not-allowed;
}

.btn-cancel,
.btn-back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 38px;
  padding: 0 16px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.btn-cancel:hover,
.btn-back:hover {
  background: var(--surface-5);
  border-color: var(--border-default);
  color: var(--text-primary);
}

.btn-cancel:active,
.btn-back:active {
  opacity: 0.85;
}
</style>
