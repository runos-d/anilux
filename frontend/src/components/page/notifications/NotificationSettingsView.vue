<template>
  <div class="nsettings-page">
    <div class="nsettings-container">
      <div class="page-header">
        <router-link to="/notifications" class="back-btn"
          ><SakuraIcon name="arrow-left" :size="16" /> Уведомления</router-link
        >
        <h1><SakuraIcon name="settings" /> Настройки уведомлений</h1>
      </div>

      <div v-if="loading" class="state-loading">
        <p>Загрузка настроек...</p>
      </div>

      <template v-else>
        <BrowserNotificationPermission />
        <div class="section-card">
          <h2 class="section-title"><SakuraIcon name="satellite" /> Каналы</h2>
          <div class="toggle-list">
            <label class="toggle-row">
              <span>Push-уведомления</span>
              <input
                type="checkbox"
                v-model="form.push_enabled"
                class="toggle-input"
              />
              <span class="toggle-switch"></span>
            </label>
            <label class="toggle-row">
              <span>Email-уведомления</span>
              <input
                type="checkbox"
                v-model="form.email_enabled"
                class="toggle-input"
              />
              <span class="toggle-switch"></span>
            </label>
            <label class="toggle-row">
              <span>Звук</span>
              <input
                type="checkbox"
                v-model="form.sound_enabled"
                class="toggle-input"
              />
              <span class="toggle-switch"></span>
            </label>
          </div>
        </div>

        <div class="section-card">
          <h2 class="section-title"><SakuraIcon name="bell" /> По типам</h2>
          <div class="toggle-list">
            <label v-for="t in notifTypes" :key="t.key" class="toggle-row">
              <span class="toggle-label"><SakuraIcon :name="notificationIcon(t.key)" :size="18" /> {{ t.label }}</span>
              <input
                type="checkbox"
                :checked="getTypeEnabled(t.key)"
                @change="
                  setTypeEnabled(
                    t.key,
                    ($event.target as HTMLInputElement).checked,
                  )
                "
                class="toggle-input"
                :disabled="t.locked"
              />
              <span class="toggle-switch" :class="{ locked: t.locked }"></span>
            </label>
          </div>
          <!-- <p class="hint">
            <SakuraIcon name="lock" /> Победа в конкурсе и уведомления
            безопасности всегда включены
          </p> -->
        </div>

        <div class="section-card">
          <h2 class="section-title"><SakuraIcon name="bell-off" /> Режим "Не беспокоить"</h2>
          <label class="toggle-row">
            <span>Включить по расписанию</span>
            <input
              type="checkbox"
              v-model="form.dnd_enabled"
              class="toggle-input"
            />
            <span class="toggle-switch"></span>
          </label>
          <div v-if="form.dnd_enabled" class="dnd-times">
            <label class="time-field">
              <span>С</span>
              <input type="time" v-model="form.dnd_start" class="time-input" />
            </label>
            <label class="time-field">
              <span>До</span>
              <input type="time" v-model="form.dnd_end" class="time-input" />
            </label>
          </div>
        </div>

        <div class="section-card">
          <h2 class="section-title"><SakuraIcon name="trash" /> Автоматическая очистка</h2>
          <div class="cleanup-row">
            <span>Удалять прочитанные старше</span>
            <select v-model="form.auto_clean_read_days" class="select-input">
              <option :value="7">7 дней</option>
              <option :value="14">14 дней</option>
              <option :value="30">30 дней</option>
              <option :value="60">60 дней</option>
              <option :value="90">90 дней</option>
            </select>
          </div>
          <div class="cleanup-row">
            <span>Удалять непрочитанные старше</span>
            <select v-model="form.auto_clean_unread_days" class="select-input">
              <option :value="30">30 дней</option>
              <option :value="60">60 дней</option>
              <option :value="90">90 дней</option>
              <option :value="180">180 дней</option>
            </select>
          </div>
          <p class="hint">
            <SakuraIcon name="star" /> Важные уведомления не удаляются
            автоматически
          </p>
        </div>

        <div class="actions-row">
          <button class="btn-save" :disabled="saving" @click="saveAll">
            <SakuraIcon v-if="!saving" name="save" :size="18" />
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button class="btn-reset" @click="resetForm">Сбросить</button>
        </div>

        <div v-if="saved" class="save-toast">
          <SakuraIcon name="check" /> Настройки сохранены
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { useNotificationStore } from "@/stores/notifications";
import BrowserNotificationPermission from "@/components/Notifications/BrowserNotificationPermission.vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { notificationIcon } from '@/lib/notificationIcon';

const store = useNotificationStore();
const loading = ref(true);
const saving = ref(false);
const saved = ref(false);

const form = reactive({
  push_enabled: true,
  email_enabled: true,
  sound_enabled: true,
  dnd_enabled: false,
  dnd_start: "23:00",
  dnd_end: "08:00",
  auto_clean_read_days: 30,
  auto_clean_unread_days: 90,
  type_settings: {} as Record<string, { enabled: boolean }>,
});

const notifTypes = [
  { key: "like", icon: "👍", label: "Лайки" },
  { key: "dislike", icon: "👎", label: "Дизлайки" },
  { key: "comment", icon: "💬", label: "Комментарии" },
  { key: "reply", icon: "↩️", label: "Ответы на комментарии" },
  { key: "follow", icon: "👭", label: "Подписки" },
  { key: "message", icon: "💌", label: "Личные сообщения" },
  { key: "group_message", icon: "👭", label: "Сообщения в группах" },
  { key: "achievement", icon: "🏆", label: "Достижения" },
  { key: "reminder_episode", icon: "🕛", label: "Новые серии (напоминание)" },
  { key: "system", icon: "⚙️", label: "Системные обновления" },
  { key: "warning", icon: "⚠️", label: "Предупреждения модератора" },
  { key: "security", icon: "🔐", label: "Безопасность", locked: true },
];

const getTypeEnabled = (key: string) => {
  if (key === "contest_win" || key === "security") return true;
  return form.type_settings[key]?.enabled ?? true;
};

const setTypeEnabled = (key: string, value: boolean) => {
  if (!form.type_settings[key]) form.type_settings[key] = { enabled: true };
  form.type_settings[key].enabled = value;
};

const applySettings = () => {
  const s = store.settings;
  if (!s) return;
  form.push_enabled = s.push_enabled;
  form.email_enabled = s.email_enabled;
  form.sound_enabled = s.sound_enabled;
  form.dnd_enabled = s.dnd_enabled;
  form.dnd_start = s.dnd_start ?? "23:00";
  form.dnd_end = s.dnd_end ?? "08:00";
  form.auto_clean_read_days = s.auto_clean_read_days;
  form.auto_clean_unread_days = s.auto_clean_unread_days;
  form.type_settings = { ...s.type_settings };
};

const resetForm = () => applySettings();

const saveAll = async () => {
  saving.value = true;
  try {
    await store.saveSettings({
      push_enabled: form.push_enabled,
      email_enabled: form.email_enabled,
      sound_enabled: form.sound_enabled,
      dnd_enabled: form.dnd_enabled,
      dnd_start: form.dnd_enabled ? form.dnd_start : null,
      dnd_end: form.dnd_enabled ? form.dnd_end : null,
      auto_clean_read_days: form.auto_clean_read_days,
      auto_clean_unread_days: form.auto_clean_unread_days,
      type_settings: form.type_settings,
    });
    saved.value = true;
    setTimeout(() => {
      saved.value = false;
    }, 3000);
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  await store.fetchSettings();
  applySettings();
  loading.value = false;
});
</script>

<style scoped>
.nsettings-page {
  min-height: 100vh;
  background: var(--surface-1);
  color: var(--text-primary);
  padding: 2rem 1.5rem;
}
.nsettings-container {
  max-width: 640px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.page-header {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  gap: 6px;
  min-height: 44px;
  color: var(--accent);
  text-decoration: none;
  font-size: 0.875rem;
}
.back-btn:hover {
  text-decoration: underline;
}
.page-header h1 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 1.6rem;
  font-weight: 800;
}

/* State */
.state-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
  color: #6b7280;
  text-align: center;
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.08);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Section card */
.section-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 0.25rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
}
.hint {
  margin: 0;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* Toggle */
.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}
.toggle-row {
  position: relative;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: var(--text-secondary);
  user-select: none;
}
.toggle-input {
  position: absolute;
  width: 1px;
  height: 1px;
  min-height: 0;
  padding: 0;
  border: 0;
  overflow: hidden;
  clip-path: inset(50%);
  opacity: 0;
}
.toggle-input:focus-visible + .toggle-switch { outline: 2px solid var(--accent); outline-offset: 3px; }
.toggle-label { display: inline-flex; align-items: center; gap: 8px; min-width: 0; overflow-wrap: anywhere; }
.toggle-label :deep(svg), .section-title :deep(svg), .page-header h1 :deep(svg) { flex-shrink: 0; }
.toggle-switch {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
  position: relative;
  flex-shrink: 0;
  transition: background 0.2s;
}
.toggle-switch::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  background: #9ca3af;
  border-radius: 50%;
  transition: all 0.2s;
}
.toggle-input:checked + .toggle-switch {
  background: var(--accent-subtle);
}
.toggle-input:checked + .toggle-switch::after {
  left: 23px;
  background: var(--accent);
}
.toggle-switch.locked {
  opacity: 0.5;
  cursor: not-allowed;
}

/* DND */
.dnd-times {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: 0.25rem;
}
.time-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #9ca3af;
}
.time-input {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.875rem;
  padding: 0.4rem 0.75rem;
  outline: none;
}
.time-input:focus {
  border-color: var(--accent);
}

/* Cleanup */
.cleanup-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}
.select-input {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.875rem;
  padding: 0.4rem 0.75rem;
  outline: none;
  cursor: pointer;
}
.select-input:focus {
  border-color: var(--accent);
}
.select-input option {
  background: var(--surface-2);
}

/* Actions */
.actions-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
.btn-save {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 0.6rem 2rem;
  border-radius: 10px;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: var(--text-on-accent);
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-save:hover:not(:disabled) {
  background: var(--accent-hover);
}
.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-reset {
  min-height: 44px;
  padding: 0.6rem 1.25rem;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-reset:hover {
  color: #d1d5db;
}

.save-toast {
  text-align: center;
  color: #22c55e;
  font-size: 0.875rem;
  font-weight: 600;
  animation: fadeIn 0.3s;
}
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Существующий брейкпоинт 640px оставлен ниже без изменений */
@media (max-width: 640px) {
  .nsettings-page {
    padding: 1rem;
  }
  .page-header h1 {
    font-size: 1.35rem;
  }
  .section-card {
    padding: 1rem;
  }
  .cleanup-row {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* ============================================================
   АДАПТИВНЫЕ СТИЛИ ДЛЯ МОБИЛЬНЫХ УСТРОЙСТВ И ПЛАНШЕТОВ
   (десктопные стили выше остаются без изменений)
   ============================================================ */

/* Планшеты: 641px – 1024px */
@media (max-width: 1024px) and (min-width: 641px) {
  .nsettings-page {
    padding: 1.75rem 1.25rem;
  }

  .nsettings-container {
    max-width: 600px;
  }
}

/* Большие телефоны / маленькие планшеты: 481px – 640px */
@media (max-width: 640px) {
  .nsettings-page {
    padding: 1rem 0.875rem;
  }

  .nsettings-container {
    gap: 1rem;
  }

  .section-card {
    padding: 1rem;
    border-radius: 12px;
    gap: 0.6rem;
  }

  .section-title {
    font-size: 0.95rem;
  }

  .toggle-row {
    font-size: 0.875rem;
    gap: 0.75rem;
  }

  .actions-row {
    flex-wrap: wrap;
  }

  .btn-save {
    flex: 1;
    padding: 0.6rem 1.25rem;
  }

  .btn-reset {
    flex: 1;
  }
}

/* Телефоны: до 480px */
@media (max-width: 480px) {
  .nsettings-page {
    padding: 0.875rem 0.75rem;
  }

  .page-header h1 {
    font-size: 1.2rem;
  }

  .back-btn {
    font-size: 0.8125rem;
  }

  .section-card {
    padding: 0.875rem;
    border-radius: 10px;
    gap: 0.5rem;
  }

  .section-title {
    font-size: 0.9rem;
  }

  .toggle-row {
    font-size: 0.8375rem;
    gap: 0.5rem;
  }

  .toggle-switch {
    width: 40px;
    height: 22px;
  }

  .toggle-switch::after {
    width: 16px;
    height: 16px;
  }

  .toggle-input:checked + .toggle-switch::after {
    left: 21px;
  }

  .dnd-times {
    gap: 0.75rem;
  }

  .time-input,
  .select-input {
    font-size: 0.8125rem;
    padding: 0.35rem 0.6rem;
  }

  .cleanup-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    font-size: 0.8375rem;
  }

  .select-input {
    width: 100%;
  }

  .actions-row {
    flex-direction: column;
    gap: 0.5rem;
  }

  .btn-save,
  .btn-reset {
    width: 100%;
    text-align: center;
    padding: 0.7rem 1rem;
  }

  .hint {
    font-size: 0.6875rem;
  }

  .state-loading {
    padding: 3rem 1rem;
  }
}

/* Ландшафтная ориентация на телефонах */
@media (max-width: 640px) and (orientation: landscape) {
  .nsettings-page {
    padding: 0.75rem 1rem;
  }

  .nsettings-container {
    gap: 0.75rem;
  }

  .section-card {
    padding: 0.875rem 1rem;
  }

  .toggle-list {
    gap: 0.4rem;
  }
}

/* Очень узкие экраны: до 360px */
@media (max-width: 360px) {
  .nsettings-page {
    padding: 0.75rem 0.625rem;
  }

  .page-header h1 {
    font-size: 1.1rem;
  }

  .section-card {
    padding: 0.75rem;
  }

  .section-title {
    font-size: 0.85rem;
  }

  .toggle-row {
    font-size: 0.8125rem;
  }

  .toggle-switch {
    width: 36px;
    height: 20px;
  }

  .toggle-switch::after {
    width: 14px;
    height: 14px;
    top: 3px;
    left: 3px;
  }

  .toggle-input:checked + .toggle-switch::after {
    left: 19px;
  }
}

/* Устройства с вырезом (notch) и safe-area */
@supports (padding: max(0px)) {
  @media (max-width: 640px) {
    .nsettings-page {
      padding-left: max(0.75rem, env(safe-area-inset-left));
      padding-right: max(0.75rem, env(safe-area-inset-right));
      padding-bottom: max(1rem, env(safe-area-inset-bottom));
    }

    .actions-row {
      padding-bottom: max(0px, env(safe-area-inset-bottom));
    }
  }
}
</style>
