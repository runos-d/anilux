<template>
  <div class="theme-grid">
    <label
      v-for="t in themes"
      :key="t.id"
      class="theme-option"
      :class="{ active: currentTheme === t.id }"
    >
      <input
        type="radio"
        name="theme"
        class="sr-only"
        :checked="currentTheme === t.id"
        @change="setTheme(t.id)"
      />
      <div
        class="theme-preview"
        :class="t.id"
        :style="
          t.id === 'custom'
            ? { '--ct-base': customTheme.bg, '--ct-accent': accentColor }
            : undefined
        "
      >
        <div class="preview-mock">
          <div class="mock-top">
            <span class="mock-dot"></span>
            <span class="mock-line"></span>
          </div>
          <div class="mock-bubble other"></div>
          <div class="mock-bubble user"></div>
          <div class="mock-input"></div>
        </div>
        <span class="check-badge"><SakuraIcon name="check" /></span>
      </div>
      <span class="theme-name">{{ t.label }}</span>
    </label>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import type { ThemeId } from "../settings/ThemeSettings.vue";

const props = defineProps<{
  themes: { id: ThemeId; label: string }[];
  currentTheme: ThemeId;
  customTheme: Record<string, string>;
  accentColor: string;
}>();

const emit = defineEmits<{ (e: "change-theme", id: ThemeId): void }>();

const setTheme = (id: ThemeId) => {
  emit("change-theme", id);
};
</script>
