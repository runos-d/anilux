<template>
  <div class="settings-section">
    <h2>Удаление аккаунта</h2>

    <div class="settings-group danger-zone">
      <div class="warning-icon"><SakuraIcon name="warning" />️</div>
      <h3>ВНИМАНИЕ!</h3>
      <p class="warning-text">
        Вы собираетесь удалить аккаунт. Это действие
        <strong>НЕОБРАТИМО</strong>. Все ваши данные будут безвозвратно удалены.
      </p>

      <div class="important-note">
        <strong><SakuraIcon name="warning" />️ Важно:</strong>
        <ul>
          <li>Имя пользователя освобождается для других</li>
          <li>Удаление выполняется сразу и не может быть отменено</li>
          <li>Сессии, push-подписки и подготовленные экспорты будут удалены</li>
        </ul>
      </div>

      <label class="credential-field">
        <span>Текущий пароль</span>
        <input v-model="password" type="password" autocomplete="current-password" required />
      </label>
      <label v-if="requiresTwoFactor" class="credential-field">
        <span>Код двухфакторной аутентификации</span>
        <input v-model="twoFactorCode" inputmode="numeric" autocomplete="one-time-code" />
      </label>

      <div class="final-check">
        <label class="checkbox-label">
          <input type="checkbox" v-model="finalConfirmation" />
          <span
            >Я подтверждаю, что хочу удалить свой аккаунт и понимаю
            последствия</span
          >
        </label>
      </div>

      <div class="action-buttons">
        <button
          @click="confirmDeletion"
          :disabled="!finalConfirmation || !password || isDeleting"
          class="danger-btn"
        >
          <SakuraIcon
            v-if="!isDeleting"
            name="trash"
            :size="18"
            style="vertical-align: middle; margin-right: 8px"
          />
          {{ isDeleting ? "Удаление..." : "Удалить аккаунт" }}
        </button>
      </div>

      <p v-if="deletionError" class="error-msg">{{ deletionError }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import apiClient from "@/api/client";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { clearConsent, reportTechnicalError, reset as resetAnalytics } from "@/analytics";

const router = useRouter();
const authStore = useAuthStore();

const finalConfirmation = ref(false);
const isDeleting = ref(false);
const deletionError = ref("");
const password = ref("");
const twoFactorCode = ref("");
const requiresTwoFactor = Boolean(authStore.user?.two_factor_enabled);

const confirmDeletion = async () => {
  if (!finalConfirmation.value) return;

  if (
    !confirm(
      "Вы уверены, что хотите удалить аккаунт? Это действие нельзя отменить.",
    )
  ) {
    return;
  }

  isDeleting.value = true;
  deletionError.value = "";

  try {
    await apiClient.post("/users/account-deletion/", {
      password: password.value,
      two_factor_code: twoFactorCode.value || undefined,
      final_confirmation: true,
    });
    resetAnalytics();
    clearConsent();
    await authStore.clearDeletedAccountSession();
    await router.push("/");
    alert("Аккаунт и связанные с ним данные удалены.");
  } catch (error: unknown) {
    reportTechnicalError("account.delete_failed", "/route/settings");
    const data = (error as { response?: { data?: Record<string, string> } })?.response?.data;
    const detail = data?.detail || data?.error || data?.two_factor_code || data?.final_confirmation;
    deletionError.value = detail || "Ошибка при удалении аккаунта";
  } finally {
    isDeleting.value = false;
  }
};
</script>

<style scoped>
.settings-section {
  padding: 22px 24px;
}

.settings-section h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.settings-group {
  padding: 24px;
  background: var(--surface-2);
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
}

.danger-zone {
  border: 1px solid var(--danger-subtle);
  background: var(--danger-subtle);
}

.warning-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 20px;
  color: var(--warning);
}

.warning-text {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: 20px;
  text-align: center;
}

.important-note {
  padding: 16px;
  background: var(--warning-subtle);
  border-left: 3px solid var(--warning);
  border-radius: 8px;
  margin-bottom: 25px;
}

.important-note strong {
  color: var(--warning);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.important-note ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.important-note li {
  margin-bottom: 6px;
  color: var(--text-primary);
  font-size: 14px;
}

.final-check {
  margin: 20px 0;
  padding: 16px;
  background: var(--surface-3);
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
}
.credential-field { display: grid; gap: 7px; margin: 14px 0; color: var(--text-primary); }
.credential-field input { min-height: 44px; padding: 9px 12px; color: var(--text-primary); background: var(--surface-3); border: 1px solid var(--border-subtle); border-radius: 8px; }
.credential-field input:focus-visible { outline: 3px solid var(--danger); outline-offset: 2px; }

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
  font-weight: 500;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 2px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}

.danger-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  background: var(--danger);
  color: white;
  border: none;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.danger-btn:hover:not(:disabled) {
  background: var(--danger-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--danger-subtle);
}

.danger-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.error-msg {
  color: var(--danger);
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
}

/* ═══ АДАПТИВНЫЕ СТИЛИ (мобильные / планшеты) ═══════════════ */

/* xs: 320px – 374px */
@media (max-width: 374px) {
  .settings-section {
    padding: 14px 12px;
  }

  .settings-section h2 {
    font-size: 16px;
    margin-bottom: 14px;
  }

  .settings-group {
    padding: 16px;
    border-radius: 10px;
  }

  .warning-icon {
    font-size: 36px;
    margin-bottom: 14px;
  }

  .warning-icon svg {
    width: 36px;
    height: 36px;
  }

  .warning-text {
    font-size: 13px;
    margin-bottom: 16px;
    text-align: left;
  }

  .important-note {
    padding: 12px;
    margin-bottom: 18px;
  }

  .important-note strong {
    font-size: 13px;
  }

  .important-note ul {
    margin: 6px 0 0 16px;
  }

  .important-note li {
    font-size: 12px;
    margin-bottom: 4px;
  }

  .final-check {
    padding: 12px;
    margin: 16px 0;
  }

  .checkbox-label {
    font-size: 13px;
    gap: 8px;
  }

  .action-buttons {
    flex-direction: column;
    gap: 8px;
    margin-top: 18px;
  }

  .danger-btn {
    width: 100%;
    padding: 12px 16px;
    font-size: 14px;
  }

  .error-msg {
    font-size: 13px;
    margin-top: 12px;
  }
}

/* sm: 375px – 767px */
@media (min-width: 375px) and (max-width: 767px) {
  .settings-section {
    padding: 16px;
  }

  .settings-section h2 {
    font-size: 18px;
    margin-bottom: 16px;
  }

  .settings-group {
    padding: 18px;
    border-radius: 12px;
  }

  .warning-icon {
    font-size: 40px;
    margin-bottom: 16px;
  }

  .warning-icon svg {
    width: 40px;
    height: 40px;
  }

  .warning-text {
    font-size: 14px;
    text-align: left;
  }

  .important-note {
    padding: 14px;
    margin-bottom: 20px;
  }

  .important-note li {
    font-size: 13px;
  }

  .final-check {
    padding: 14px;
  }

  .checkbox-label {
    font-size: 13.5px;
  }

  .action-buttons {
    flex-wrap: wrap;
    gap: 10px;
  }

  .danger-btn {
    flex: 1 1 100%;
    padding: 12px 20px;
    font-size: 15px;
  }
}

/* md: 768px – 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .settings-section {
    padding: 20px 22px;
  }

  .settings-group {
    padding: 22px;
  }

  .warning-text {
    font-size: 15px;
  }

  .danger-btn {
    padding: 12px 22px;
  }
}

/* Ландшафтная ориентация на мобильных -компактнее */
@media (max-width: 767px) and (orientation: landscape) {
  .settings-section {
    padding: 12px;
  }

  .settings-group {
    padding: 14px;
  }

  .warning-icon {
    font-size: 32px;
    margin-bottom: 10px;
  }

  .warning-icon svg {
    width: 32px;
    height: 32px;
  }

  .warning-text {
    font-size: 13px;
    margin-bottom: 14px;
  }

  .important-note {
    padding: 10px;
    margin-bottom: 14px;
  }

  .final-check {
    padding: 10px;
    margin: 12px 0;
  }

  .action-buttons {
    margin-top: 14px;
  }
}

/* Улучшение тач-взаимодействия */
@media (hover: none) and (pointer: coarse) {
  .danger-btn:hover:not(:disabled) {
    transform: none;
    box-shadow: none;
  }

  .danger-btn:active:not(:disabled) {
    transform: scale(0.98);
    background: var(--danger-hover);
  }

  .checkbox-label {
    padding: 4px;
    margin: -4px;
  }
}
</style>
