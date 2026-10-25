<template>
  <div class="settings-with-scroll">
    <div class="settings-container">
      <!-- Левая колонка - навигация -->
      <div class="settings-sidebar" ref="sidebarRef">
        <div class="sidebar-content">
          <h2>Настройки</h2>

          <nav class="settings-nav">
            <button
              v-for="section in sections"
              :key="section.id"
              @click="activeSection = section.id"
              :class="['nav-item', { active: activeSection === section.id }]"
            >
              <component :is="section.icon" class="w-5 h-5" />
              <span>{{ section.name }}</span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Правая колонка - содержимое -->
      <div class="settings-content" ref="contentRef">
        <div class="content-wrapper">
          <component
            :is="currentSectionComponent"
            @save="handleSave"
            @cancel="handleCancel"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, type Component } from "vue";
import {
  UserIcon,
  BellIcon,
  PaintBrushIcon,
  CircleStackIcon,
  GlobeAltIcon,
  InformationCircleIcon,
} from "@heroicons/vue/24/outline";
import AccountSettings from "./AccountSettings.vue";
import NotificationSettings from "./NotificationSettings.vue";
import AppearanceSettings from "./AppearanceSettings.vue";
import DataSettings from "./DataSettings.vue";
import AdditionalSettings from "./AdditionalSettings.vue";
import AboutSettings from "./AboutSettings.vue";

const sections = [
  { id: "account", name: "Учётная запись", icon: UserIcon },
  { id: "notifications", name: "Уведомления", icon: BellIcon },
  { id: "appearance", name: "Внешний вид", icon: PaintBrushIcon },
  { id: "data", name: "Данные", icon: CircleStackIcon },
  { id: "additional", name: "Дополнительно", icon: GlobeAltIcon },
  { id: "about", name: "О программе", icon: InformationCircleIcon },
];

const activeSection = ref("account");
const sidebarRef = ref<HTMLElement | null>(null);
const contentRef = ref<HTMLElement | null>(null);

const componentsMap: Record<string, Component> = {
  account: AccountSettings,
  notifications: NotificationSettings,
  appearance: AppearanceSettings,
  data: DataSettings,
  additional: AdditionalSettings,
  about: AboutSettings,
};

const currentSectionComponent = computed(() => {
  return componentsMap[activeSection.value] || AccountSettings;
});

watch(activeSection, async () => {
  await nextTick();
  if (contentRef.value) {
    contentRef.value.scrollTop = 0;
  }
});

const handleSave = () => {
};

const handleCancel = () => {
};
</script>

<style scoped>
.settings-with-scroll {
  height: 100vh;
  overflow: hidden;
}

.settings-container {
  display: flex;
  height: 100%;
}

.settings-sidebar {
  width: 280px;
  background: #f9f9f9;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-content {
  padding: 20px;
}

.sidebar-content h2 {
  margin: 0 0 24px;
  font-size: 20px;
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  color: #666;
  transition: all 0.3s;
  width: 100%;
}

.nav-item:hover {
  background: #f0f0f0;
}

.nav-item.active {
  background: #667eea;
  color: white;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  background: white;
}

.content-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px;
}

/* Кастомный скроллбар для обеих колонок */
.settings-sidebar::-webkit-scrollbar,
.settings-content::-webkit-scrollbar {
  width: 8px;
}

.settings-sidebar::-webkit-scrollbar-track,
.settings-content::-webkit-scrollbar-track {
  background: transparent;
}

.settings-sidebar::-webkit-scrollbar-thumb,
.settings-content::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 4px;
}

.settings-sidebar::-webkit-scrollbar-thumb:hover,
.settings-content::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}

/* Адаптив для мобильных устройств */
@media (max-width: 768px) {
  .settings-container {
    flex-direction: column;
  }

  .settings-sidebar {
    width: 100%;
    height: auto;
    max-height: 200px;
  }

  .sidebar-content {
    padding: 12px;
  }

  .settings-nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 8px;
  }

  .nav-item {
    white-space: nowrap;
    flex-shrink: 0;
  }

  .content-wrapper {
    padding: 16px;
  }
}

/* ═══ ДОПОЛНИТЕЛЬНАЯ АДАПТАЦИЯ (мобильные / планшеты) ═══════ */

/* xs: 320px – 374px */
@media (max-width: 374px) {
  .settings-sidebar {
    max-height: 160px;
  }

  .sidebar-content {
    padding: 10px;
  }

  .sidebar-content h2 {
    margin: 0 0 12px;
    font-size: 16px;
  }

  .settings-nav {
    gap: 3px;
    padding-bottom: 6px;
  }

  .nav-item {
    padding: 8px 10px;
    font-size: 12px;
    gap: 6px;
    border-radius: 6px;
  }

  .nav-item :deep(svg) {
    width: 16px;
    height: 16px;
  }

  .content-wrapper {
    padding: 12px;
  }
}

/* sm: 375px – 767px */
@media (min-width: 375px) and (max-width: 767px) {
  .settings-sidebar {
    max-height: 180px;
  }

  .sidebar-content {
    padding: 12px;
  }

  .sidebar-content h2 {
    margin: 0 0 16px;
    font-size: 18px;
  }

  .settings-nav {
    gap: 4px;
  }

  .nav-item {
    padding: 10px 14px;
    font-size: 13px;
  }

  .content-wrapper {
    padding: 16px;
  }
}

/* md: 768px – 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .settings-sidebar {
    width: 240px;
    max-height: none;
    height: 100%;
  }

  .settings-nav {
    flex-direction: column;
    overflow-x: visible;
    padding-bottom: 0;
  }

  .nav-item {
    white-space: normal;
    flex-shrink: 1;
  }

  .sidebar-content {
    padding: 16px;
  }

  .sidebar-content h2 {
    font-size: 18px;
  }

  .content-wrapper {
    padding: 24px;
    max-width: 100%;
  }
}

/* Улучшение тач-взаимодействия */
@media (hover: none) and (pointer: coarse) {
  .nav-item:hover {
    background: transparent;
  }

  .nav-item:active:not(.active) {
    background: #f0f0f0;
  }

  .settings-sidebar::-webkit-scrollbar,
  .settings-content::-webkit-scrollbar {
    width: 4px;
  }

  .settings-sidebar,
  .settings-content {
    -webkit-overflow-scrolling: touch;
  }

  .settings-nav {
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
  }
}

/* Ландшафтная ориентация на мобильных -ограничиваем высоту сайдбара */
@media (max-width: 767px) and (orientation: landscape) {
  .settings-sidebar {
    max-height: 120px;
  }

  .sidebar-content h2 {
    margin-bottom: 8px;
    font-size: 16px;
  }

  .nav-item {
    padding: 8px 12px;
    font-size: 13px;
  }
}
</style>