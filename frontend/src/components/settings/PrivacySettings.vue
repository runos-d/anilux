<template>
  <div class="settings-section">
    <h2>Конфиденциальность</h2>

    <div class="settings-group">
      <h3><SakuraIcon name="user" /> Кто может видеть мой номер телефона</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_phone"
            value="everyone"
            @change="onSettingsChange"
          />
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_phone"
            value="contacts"
            @change="onSettingsChange"
          />
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_phone"
            value="nobody"
            @change="onSettingsChange"
          />
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="mail" /> Кто может видеть мой email</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_email"
            value="everyone"
            @change="onSettingsChange"
          />
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_email"
            value="contacts"
            @change="onSettingsChange"
          />
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_email"
            value="nobody"
            @change="onSettingsChange"
          />
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="one-oclock" /> Время последнего посещения</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_last_seen"
            value="everyone"
            @change="onSettingsChange"
          />
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_last_seen"
            value="contacts"
            @change="onSettingsChange"
          />
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_last_seen"
            value="nobody"
            @change="onSettingsChange"
          />
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="camera" /> Фотография профиля</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_profile_photo"
            value="everyone"
            @change="onSettingsChange"
          />
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_profile_photo"
            value="contacts"
            @change="onSettingsChange"
          />
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_see_profile_photo"
            value="nobody"
            @change="onSettingsChange"
          />
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="phone" /> Звонки</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_call"
            value="everyone"
            @change="onSettingsChange"
          />
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_call"
            value="contacts"
            @change="onSettingsChange"
          />
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_call"
            value="nobody"
            @change="onSettingsChange"
          />
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="users" /> Группы и каналы</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_add_to_groups"
            value="everyone"
            @change="onSettingsChange"
          />
          <span class="radio-label">Все могут добавлять меня в группы</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_add_to_groups"
            value="contacts"
            @change="onSettingsChange"
          />
          <span class="radio-label">Только мои контакты</span>
        </label>
        <label class="radio-option">
          <input
            type="radio"
            v-model="privacySettings.who_can_add_to_groups"
            value="nobody"
            @change="onSettingsChange"
          />
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="link" /> Пересылка сообщений</h3>
      <div class="setting-item">
        <label class="setting-label">
          <input
            type="checkbox"
            v-model="privacySettings.allow_message_forwarding"
            @change="onSettingsChange"
          />
          <span>Разрешить пересылку моих сообщений</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="chart" /> Необязательная аналитика</h3>
      <p class="privacy-note">
        Внешние счётчики не загружаются до разрешения. AniLux не передаёт им сообщения,
        поисковые запросы, email, телефон, идентификатор пользователя или содержимое форм.
      </p>
      <div class="consent-choice" role="group" aria-label="Согласие на аналитику">
        <button type="button" :class="{ active: consentState === 'denied' }" @click="changeConsent('denied')">
          Не разрешать
        </button>
        <button type="button" :class="{ active: consentState === 'granted' }" @click="changeConsent('granted')">
          Разрешить
        </button>
      </div>
    </div>

    <div class="settings-actions">
      <button
        @click="saveSettings"
        :disabled="!hasChanges || isSaving"
        class="save-btn"
      >
        <SakuraIcon v-if="isSaving" name="save" />
<span v-else>Сохранить настройки</span>
      </button>
    </div>

    <!-- Toast notification -->
    <div v-if="toast.show" :class="['toast', toast.type]">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onBeforeUnmount } from "vue";
import { useAuthStore } from "@/stores/auth";
import * as settingsApi from "@/api/settings";
import type { PrivacySettingsData } from "@/api/settings";
import { getConsent, onConsentChange } from "@/analytics/consent";
import type { ConsentState } from "@/analytics/types";
import { saveConsentChoice, reportTechnicalError } from "@/analytics";

const privacySettings = ref<PrivacySettingsData>({
  who_can_see_phone: "contacts",
  who_can_see_email: "contacts",
  who_can_see_last_seen: "everyone",
  who_can_see_profile_photo: "everyone",
  who_can_call: "everyone",
  who_can_add_to_groups: "everyone",
  allow_message_forwarding: true,
});

const consentState = ref(getConsent().state);
const stopConsentWatch = onConsentChange((record) => { consentState.value = record.state; });
onBeforeUnmount(stopConsentWatch);

const originalSettings = ref<PrivacySettingsData>({ ...privacySettings.value });
const isSaving = ref(false);

const toast = ref({
  show: false,
  message: "",
  type: "success" as "success" | "error",
});

const hasChanges = computed(() => {
  return JSON.stringify(privacySettings.value) !== JSON.stringify(originalSettings.value);
});

const changeConsent = async (state: Exclude<ConsentState, "unknown">) => {
  try {
    await saveConsentChoice(state, "settings");
    showToast(state === "granted" ? "Аналитика разрешена" : "Аналитика отключена");
  } catch {
    showToast("Решение применено на устройстве, но не синхронизировано", "error");
  }
};

const showToast = (message: string, type: "success" | "error" = "success") => {
  toast.value = { show: true, message, type };
  setTimeout(() => {
    toast.value.show = false;
  }, 3000);
};

const fetchPrivacySettings = async () => {
  try {
    const data = await settingsApi.getPrivacySettings();
    privacySettings.value = {
      who_can_see_phone: data.who_can_see_phone || "contacts",
      who_can_see_email: data.who_can_see_email || "contacts",
      who_can_see_last_seen: (data as PrivacySettingsData).who_can_see_last_seen || "everyone",
      who_can_see_profile_photo: data.who_can_see_profile_photo || "everyone",
      who_can_call: data.who_can_call || "everyone",
      who_can_add_to_groups: data.who_can_add_to_groups || "everyone",
      allow_message_forwarding: data.allow_message_forwarding ?? true,
    };
    originalSettings.value = { ...privacySettings.value };
  } catch {
    reportTechnicalError("privacy.load_failed", "/route/settings");
    showToast("Ошибка загрузки настроек", "error");
  }
};

const onSettingsChange = () => {
  saveSettings();
};

const auth = useAuthStore();
const ownerId = auth.user?.id;
let disposed = false;
onBeforeUnmount(() => { disposed = true; });
let saveVersion = 0;
let saveQueue: Promise<void> = Promise.resolve();
const saveSettings = () => {
  const version = ++saveVersion;
  const snapshot = { ...privacySettings.value };
  isSaving.value = true;
  saveQueue = saveQueue.catch(() => undefined).then(async () => {
    if (disposed || auth.user?.id !== ownerId) return;
    try {
      const saved = await settingsApi.updatePrivacySettings(snapshot);
      originalSettings.value = Object.fromEntries(Object.keys(snapshot).map(key => [key, saved[key as keyof PrivacySettingsData]]));
      if (version === saveVersion) showToast("Настройки сохранены");
    } catch {
      reportTechnicalError("privacy.save_failed", "/route/settings");
      showToast("Ошибка сохранения настроек", "error");
    } finally {
      if (version === saveVersion) isSaving.value = false;
    }
  });
  return saveQueue;
};

onMounted(() => {
  fetchPrivacySettings();
});
</script>

<style scoped>
.privacy-note { color: var(--secondary-text); line-height: 1.5; }
.consent-choice { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }
.consent-choice button { min-height: 44px; color: var(--text-color); background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; cursor: pointer; }
.consent-choice button.active { border-color: var(--primary-color); box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 25%, transparent); }
.consent-choice button:focus-visible { outline: 3px solid var(--primary-color); outline-offset: 2px; }
@media (max-width: 480px) { .consent-choice { grid-template-columns: 1fr; } }
.settings-section h2 {
  margin-bottom: 20px;
}

.settings-group {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--surface-4);
  border-radius: 8px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
  font-weight: 600;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.radio-option:hover {
  background: var(--surface-3);
}

.radio-option input[type="radio"] {
  margin: 0;
}

.radio-label {
  font-weight: 500;
  cursor: pointer;
}

.setting-item {
  margin-bottom: 15px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
}

.setting-label input[type="checkbox"] {
  margin: 0;
}

.sub-settings {
  margin-left: 25px;
  margin-top: 10px;
}

.sub-settings .setting-label {
  font-weight: normal;
  font-size: 14px;
}

.settings-actions {
  margin-top: 30px;
  text-align: center;
}

.save-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 16px;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 2000;
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  background: #4caf50;
}

.toast.error {
  background: #f44336;
}

@keyframes slideIn {
  from {
    transform: translateY(100px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* ============================================================
   АДАПТИВНЫЕ СТИЛИ ДЛЯ МОБИЛЬНЫХ УСТРОЙСТВ И ПЛАНШЕТОВ
   (десктопные стили выше остаются без изменений)
   ============================================================ */

/* Планшеты: 768px – 1024px */
@media (max-width: 1024px) {
  .settings-group {
    padding: 18px;
    margin-bottom: 24px;
  }
}

/* Большие телефоны / маленькие планшеты: 481px – 767px */
@media (max-width: 767px) {
  .settings-section h2 {
    font-size: 1.25rem;
    margin-bottom: 16px;
  }

  .settings-group {
    padding: 16px;
    margin-bottom: 18px;
    border-radius: 6px;
  }

  .settings-group h3 {
    font-size: 15px;
    margin-bottom: 12px;
    display: flex;
    align-items: flex-start;
    gap: 0.35rem;
  }

  .radio-group {
    gap: 6px;
  }

  .radio-option {
    padding: 10px 12px;
    gap: 12px;
  }

  .radio-label {
    font-size: 0.9rem;
    line-height: 1.35;
  }

  .setting-label {
    gap: 12px;
    font-size: 0.9rem;
    line-height: 1.35;
  }

  .sub-settings {
    margin-left: 18px;
    margin-top: 8px;
  }

  .sub-settings .setting-label {
    font-size: 13px;
  }

  .settings-actions {
    margin-top: 24px;
  }

  .save-btn {
    width: 100%;
    padding: 12px 20px;
    font-size: 15px;
  }

  .toast {
    left: 16px;
    right: 16px;
    bottom: 16px;
    text-align: center;
  }
}

/* Телефоны: до 480px */
@media (max-width: 480px) {
  .settings-section h2 {
    font-size: 1.15rem;
    margin-bottom: 14px;
  }

  .settings-group {
    padding: 14px;
    margin-bottom: 16px;
  }

  .settings-group h3 {
    font-size: 14px;
    margin-bottom: 10px;
  }

  .radio-option {
    padding: 8px 10px;
    gap: 10px;
  }

  .radio-label {
    font-size: 0.85rem;
  }

  .setting-label {
    font-size: 0.85rem;
    gap: 10px;
  }

  .sub-settings {
    margin-left: 14px;
  }

  .sub-settings .setting-label {
    font-size: 12.5px;
  }

  .save-btn {
    padding: 11px 18px;
    font-size: 14px;
  }
}

/* Ландшафтная ориентация на телефонах */
@media (max-width: 767px) and (orientation: landscape) {
  .settings-group {
    padding: 12px;
    margin-bottom: 14px;
  }

  .radio-group {
    gap: 4px;
  }

  .radio-option {
    padding: 6px 10px;
  }

  .toast {
    left: auto;
    right: 12px;
    bottom: 12px;
    max-width: 320px;
  }
}

/* Очень узкие экраны: до 360px */
@media (max-width: 360px) {
  .settings-group {
    padding: 12px;
  }

  .settings-group h3 {
    font-size: 13px;
  }

  .radio-label {
    font-size: 0.8rem;
  }

  .setting-label {
    font-size: 0.8rem;
  }

  .save-btn {
    font-size: 13px;
    padding: 10px 16px;
  }
}

/* Устройства с вырезом (notch) и safe-area */
@supports (padding: max(0px)) {
  @media (max-width: 767px) {
    .toast {
      left: max(16px, env(safe-area-inset-left));
      right: max(16px, env(safe-area-inset-right));
      bottom: max(16px, env(safe-area-inset-bottom));
    }

    .settings-actions {
      padding-bottom: max(0px, env(safe-area-inset-bottom));
    }
  }
}
</style>
