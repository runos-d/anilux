<template>
  <div class="progress-bar" :class="progressBarClasses">
    <div
      class="progress-bar-fill"
      :style="fillStyles"
      role="progressbar"
      :aria-valuenow="value"
      :aria-valuemin="min"
      :aria-valuemax="max"
    >
      <span
        v-if="showLabel && labelPosition === 'inside'"
        class="progress-bar-label"
      >
        {{ formattedValue }}%
      </span>
    </div>
    <span
      v-if="showLabel && labelPosition === 'outside'"
      class="progress-bar-label-outside"
    >
      {{ formattedValue }}%
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  value: number;
  min?: number;
  max?: number;
  size?: "small" | "medium" | "large";
  variant?: "primary" | "success" | "warning" | "danger";
  color?: string;
  showLabel?: boolean;
  labelPosition?: "inside" | "outside";
  animated?: boolean;
  striped?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  min: 0,
  max: 100,
  size: "medium",
  variant: "primary",
  showLabel: false,
  labelPosition: "inside",
  animated: false,
  striped: false,
});

const progressBarClasses = computed(() => {
  return [
    `progress-bar--${props.size}`,
    `progress-bar--${props.variant}`,
    {
      "progress-bar--animated": props.animated,
      "progress-bar--striped": props.striped,
    },
  ];
});

const normalizedValue = computed(() => {
  return Math.min(Math.max(props.value, props.min), props.max);
});

const percentage = computed(() => {
  const range = props.max - props.min;
  if (range === 0) return 0;
  return ((normalizedValue.value - props.min) / range) * 100;
});

const formattedValue = computed(() => {
  return Math.round(percentage.value);
});

const fillStyles = computed(() => {
  const styles: Record<string, string> = {
    width: `${percentage.value}%`,
  };

  if (props.color) {
    styles.backgroundColor = props.color;
  }

  return styles;
});
</script>

<style scoped>
.progress-bar {
  position: relative;
  width: 100%;
  background-color: var(--surface-4);
  border-radius: 4px;
  overflow: hidden;
}

/* Размеры */
.progress-bar--small {
  height: 6px;
}

.progress-bar--medium {
  height: 8px;
}

.progress-bar--large {
  height: 12px;
}

/* Заполнение */
.progress-bar-fill {
  height: 100%;
  background-color: var(--accent);
  border-radius: 4px;
  transition: width 0.3s var(--transition-smooth);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Варианты цветов */
.progress-bar--primary .progress-bar-fill {
  background-color: var(--accent);
}

.progress-bar--success .progress-bar-fill {
  background-color: var(--accent-2);
}

.progress-bar--warning .progress-bar-fill {
  background-color: var(--accent-orange);
}

.progress-bar--danger .progress-bar-fill {
  background-color: var(--accent-3);
}

/* Полосатый эффект */
.progress-bar--striped .progress-bar-fill {
  background-image: linear-gradient(
    45deg,
    rgba(0, 0, 0, 0.1) 25%,
    transparent 25%,
    transparent 50%,
    rgba(0, 0, 0, 0.1) 50%,
    rgba(0, 0, 0, 0.1) 75%,
    transparent 75%,
    transparent
  );
  background-size: 20px 20px;
}

/* Анимированный эффект */
.progress-bar--animated .progress-bar-fill {
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  0% {
    background-position: 20px 0;
  }
  100% {
    background-position: 0 0;
  }
}

/* Лейбл внутри */
.progress-bar-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-primary);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
}

.progress-bar--large .progress-bar-label {
  font-size: 12px;
}

/* Лейбл снаружи */
.progress-bar-label-outside {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

/* ============================================================
   АДАПТИВНЫЕ СТИЛИ ДЛЯ МОБИЛЬНЫХ УСТРОЙСТВ И ПЛАНШЕТОВ
   (десктопные стили выше остаются без изменений)
   ============================================================ */

/* Планшеты: 768px – 1024px */
@media (max-width: 1024px) {
  .progress-bar--large {
    height: 11px;
  }
}

/* Большие телефоны / маленькие планшеты: 481px – 767px */
@media (max-width: 767px) {
  .progress-bar--small {
    height: 5px;
  }

  .progress-bar--medium {
    height: 7px;
  }

  .progress-bar--large {
    height: 10px;
  }

  .progress-bar-label {
    font-size: 9px;
  }

  .progress-bar--large .progress-bar-label {
    font-size: 11px;
  }

  .progress-bar-label-outside {
    font-size: 11px;
    margin-left: 6px;
  }
}

/* Телефоны: до 480px */
@media (max-width: 480px) {
  .progress-bar--small {
    height: 4px;
  }

  .progress-bar--medium {
    height: 6px;
  }

  .progress-bar--large {
    height: 9px;
  }

  .progress-bar-label {
    font-size: 8px;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.6);
  }

  .progress-bar--large .progress-bar-label {
    font-size: 10px;
  }

  .progress-bar-label-outside {
    font-size: 10px;
    margin-left: 5px;
  }

  .progress-bar--striped .progress-bar-fill {
    background-size: 16px 16px;
  }
}

/* Ландшафтная ориентация на телефонах */
@media (max-width: 767px) and (orientation: landscape) {
  .progress-bar--large {
    height: 10px;
  }

  .progress-bar-label-outside {
    font-size: 11px;
  }
}

/* Очень узкие экраны: до 360px */
@media (max-width: 360px) {
  .progress-bar--small {
    height: 3px;
  }

  .progress-bar--medium {
    height: 5px;
  }

  .progress-bar--large {
    height: 8px;
  }

  .progress-bar-label {
    font-size: 7px;
  }

  .progress-bar--large .progress-bar-label {
    font-size: 9px;
  }

  .progress-bar-label-outside {
    font-size: 9px;
    margin-left: 4px;
  }

  .progress-bar--striped .progress-bar-fill {
    background-size: 14px 14px;
  }
}

/* Устройства с вырезом (notch) и safe-area */
@supports (padding: max(0px)) {
  @media (max-width: 767px) {
    .progress-bar {
      border-radius: max(4px, env(safe-area-inset-bottom, 4px));
    }
  }
}
</style>