<template>
  <input
    v-bind="$attrs"
    class="ui-range-slider"
    type="range"
    :value="effectiveValue"
    :min="min"
    :max="max"
    :step="step"
    :style="{ '--range-progress': `${progress}%` }"
    @input="onInput"
    @change="emit('change', $event)"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";

defineOptions({ inheritAttrs: false });

const props = defineProps<{
  modelValue?: number | string;
  modelModifiers?: Record<string, boolean>;
  value?: number | string;
  min?: number | string;
  max?: number | string;
  step?: number | string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
  input: [event: Event];
  change: [event: Event];
}>();

const effectiveValue = computed(() => props.modelValue ?? props.value ?? "");
const progress = computed(() => {
  const min = Number(props.min ?? 0);
  const max = Number(props.max ?? 100);
  const value = Number(effectiveValue.value || min);
  if (!Number.isFinite(value) || max <= min) return 0;
  return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
});

const onInput = (event: Event) => {
  const value = Number((event.target as HTMLInputElement).value);
  emit("update:modelValue", value);
  emit("input", event);
};
</script>

<style scoped>
.ui-range-slider {
  width: 100%;
  height: 16px !important;
  margin-top: 0;
  margin-bottom: 0;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  outline: 0 !important;
  appearance: none !important;
  -webkit-appearance: none !important;
  background: transparent !important;
  box-shadow: none !important;
  cursor: pointer;
}

.ui-range-slider::-webkit-slider-runnable-track {
  height: 3px !important;
  border-radius: var(--radius-full) !important;
  background: linear-gradient(
    to right,
    var(--accent) 0 var(--range-progress),
    var(--surface-4) var(--range-progress) 100%
  ) !important;
}

.ui-range-slider::-webkit-slider-thumb {
  width: 14px !important;
  height: 14px !important;
  margin-top: -5.5px !important;
  border: none !important;
  border-radius: 50% !important;
  appearance: none !important;
  -webkit-appearance: none !important;
  background: var(--accent) !important;
  box-shadow: 0 1px 5px color-mix(in srgb, var(--accent) 45%, transparent) !important;
}

.ui-range-slider::-moz-range-track {
  height: 3px !important;
  border-radius: var(--radius-full) !important;
  background: var(--surface-4) !important;
}

.ui-range-slider::-moz-range-progress {
  height: 3px !important;
  border-radius: var(--radius-full) !important;
  background: var(--accent) !important;
}

.ui-range-slider::-moz-range-thumb {
  width: 11px !important;
  height: 11px !important;
  border: none !important;
  border-radius: 50% !important;
  background: var(--accent) !important;
  box-shadow: 0 1px 5px color-mix(in srgb, var(--accent) 45%, transparent) !important;
}

.ui-range-slider:focus-visible {
  outline: none;
}

.ui-range-slider:focus-visible::-webkit-slider-thumb {
  box-shadow: 0 0 0 3px var(--accent-subtle);
}
</style>
