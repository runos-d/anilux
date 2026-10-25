<template>
  <button class="achievement-card" type="button">
    <span class="achievement-card__icon" aria-hidden="true">
      <SakuraIcon :name="achievement.icon || 'trophy'" :size="30" />
    </span>
    <span class="achievement-card__content">
      <strong>{{ achievement.name }}</strong>
      <span>{{ achievement.description }}</span>
      <span v-if="hasProgress" class="achievement-card__progress">
        <span :style="{ width: `${progress}%` }"></span>
      </span>
      <small v-if="hasProgress">
        {{ achievement.progress }} / {{ achievement.max_progress }}
      </small>
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import type { Achievement } from "@/types";

const props = defineProps<{ achievement: Achievement }>();

const hasProgress = computed(
  () => props.achievement.progress !== undefined && Boolean(props.achievement.max_progress),
);
const progress = computed(() => {
  if (!hasProgress.value) return 0;
  return Math.min(100, Math.round(((props.achievement.progress || 0) / (props.achievement.max_progress || 1)) * 100));
});
</script>

<style scoped>
.achievement-card {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-3);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.achievement-card:hover,
.achievement-card:focus-visible {
  border-color: var(--accent);
  background: var(--accent-subtle);
}

.achievement-card:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.achievement-card__icon {
  width: 44px;
  height: 44px;
  flex: 0 0 44px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--accent-subtle);
  color: var(--accent);
}

.achievement-card__content {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 5px;
}

.achievement-card__content strong {
  font-size: 0.95rem;
}

.achievement-card__content > span:not(.achievement-card__progress),
.achievement-card__content small {
  color: var(--text-secondary);
  font-size: 0.78rem;
  line-height: 1.4;
}

.achievement-card__progress {
  height: 5px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--surface-1);
}

.achievement-card__progress > span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
}
</style>
