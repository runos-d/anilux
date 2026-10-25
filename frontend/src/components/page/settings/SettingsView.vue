<template>
  <div class="settings-view">
    <div class="settings-container">
      <div class="settings-header">
        <button @click="$router.go(-1)" class="back-button">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1>Настройки</h1>
        <div class="header-spacer"></div>
      </div>

      <div class="settings-tabs">
        <button
          :class="['tab', { active: activeTab === 'account' }]"
          @click="activeTab = 'account'"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          Редактировать профиль
        </button>
        <button
          :class="['tab', { active: activeTab === 'theme' }]"
          @click="activeTab = 'theme'"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="13.5" cy="6.5" r="0.5" fill="currentColor" />
            <circle cx="17.5" cy="10.5" r="0.5" fill="currentColor" />
            <circle cx="8.5" cy="7.5" r="0.5" fill="currentColor" />
            <circle cx="6.5" cy="12.5" r="0.5" fill="currentColor" />
            <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.26-.293-.438-.695-.438-1.138a1.69 1.69 0 0 1 1.668-1.668h1.926c2.97 0 5.378-2.414 5.378-5.378C21.7 6.928 17.464 2 12 2z" />
          </svg>
          Тема и оформление
        </button>
      </div>

      <div class="settings-content">
        <AccountSettings v-if="activeTab === 'account'" />
        <ThemeSettings v-if="activeTab === 'theme'" />
        <DeleteAccountSettings v-if="activeTab === 'delete'" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import AccountSettings from "@/components/settings/AccountSettings.vue";
import ThemeSettings from "@/components/settings/ThemeSettings.vue";
import DeleteAccountSettings from "@/components/settings/DeleteAccountSettings.vue";

const activeTab = ref("account");
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  color: var(--text-primary);
}

.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-button {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  width: 40px;
  height: 40px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.back-button:hover {
  background: var(--surface-4);
  border-color: var(--border-default);
}

.settings-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}

.header-spacer {
  flex: 1;
}

/* Tabs */
.settings-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  background: var(--surface-3);
  padding: 6px;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--tab-default);
  border: none;
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  background: var(--tab-hover);
  color: var(--text-primary);
}

.tab.active {
  background: var(--tab-active);
  color: var(--tab-active-text);
}

/* Content */
.settings-content {
  background: var(--surface-3);
  border-radius: 16px;
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

@media (max-width: 600px) {
  .settings-tabs {
    flex-direction: column;
  }

  .tab {
    padding: 14px;
  }
}

/* ═══ ДОПОЛНИТЕЛЬНАЯ АДАПТАЦИЯ (мобильные / планшеты) ═══════ */

/* xs: 320px – 374px */
@media (max-width: 374px) {
  .settings-container {
    padding: 12px;
  }

  .settings-header {
    gap: 10px;
    margin-bottom: 16px;
  }

  .back-button {
    width: 34px;
    height: 34px;
    border-radius: 8px;
  }

  .back-button svg {
    width: 18px;
    height: 18px;
  }

  .settings-header h1 {
    font-size: 18px;
  }

  .settings-tabs {
    gap: 4px;
    padding: 4px;
    border-radius: 10px;
    margin-bottom: 14px;
    flex-direction: column;
  }

  .tab {
    padding: 10px 12px;
    font-size: 12px;
    gap: 6px;
    border-radius: 7px;
  }

  .tab svg {
    width: 15px;
    height: 15px;
  }

  .settings-content {
    border-radius: 12px;
  }
}

/* sm: 375px – 767px */
@media (min-width: 375px) and (max-width: 767px) {
  .settings-container {
    padding: 14px;
  }

  .settings-header {
    gap: 12px;
    margin-bottom: 18px;
  }

  .back-button {
    width: 36px;
    height: 36px;
    border-radius: 9px;
  }

  .settings-header h1 {
    font-size: 20px;
  }

  .settings-tabs {
    flex-direction: column;
    gap: 6px;
    padding: 5px;
    margin-bottom: 16px;
  }

  .tab {
    padding: 12px 14px;
    font-size: 13px;
  }

  .settings-content {
    border-radius: 14px;
  }
}

/* md: 768px – 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .settings-container {
    padding: 18px;
    max-width: 100%;
  }

  .settings-header h1 {
    font-size: 22px;
  }

  .settings-tabs {
    gap: 8px;
  }

  .tab {
    padding: 12px 14px;
    font-size: 13px;
  }

  .settings-content {
    border-radius: 15px;
  }
}

/* Ландшафтная ориентация на мобильных -компактнее по вертикали */
@media (max-width: 767px) and (orientation: landscape) {
  .settings-container {
    padding: 10px;
  }

  .settings-header {
    margin-bottom: 12px;
  }

  .settings-header h1 {
    font-size: 18px;
  }

  .settings-tabs {
    flex-direction: row;
    margin-bottom: 12px;
  }

  .tab {
    padding: 10px 12px;
    font-size: 12px;
  }
}

/* Улучшение тач-взаимодействия */
@media (hover: none) and (pointer: coarse) {
  .back-button:hover {
    background: var(--surface-3);
    border-color: var(--border-subtle);
  }

  .back-button:active {
    background: var(--surface-4);
    border-color: var(--border-default);
  }

  .tab:hover {
    background: transparent;
    color: var(--text-secondary);
  }

  .tab:active:not(.active) {
    background: var(--surface-4);
    color: var(--text-primary);
  }
}
</style>