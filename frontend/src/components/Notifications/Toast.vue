<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <teleport to="body">
    <transition-group name="toast" tag="div" class="toast-container">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast', toast.type, { 'has-action': toast.action }]"
        @click="handleClick(toast)"
      >
        <div class="toast-icon">
          <component :is="getIcon(toast.type)" />
        </div>

        <div class="toast-content">
          <div v-if="toast.title" class="toast-title">{{ toast.title }}</div>
          <div class="toast-message">{{ toast.message }}</div>
          <button v-if="toast.action" class="toast-action" type="button" @click.stop="toast.action.handler(); removeToast(toast.id)">{{ toast.action.label }}</button>
        </div>

        <button
          @click.stop="removeToast(toast.id)"
          class="toast-close"
          type="button"
          aria-label="Закрыть"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <div
          class="toast-progress"
          :style="{ animationDuration: `${toast.duration}ms` }"
        ></div>
      </div>
    </transition-group>
  </teleport>
</template>

<script setup lang="ts">
import { h } from "vue";

interface ToastAction {
  label: string;
  handler: () => void;
}

export interface Toast {
  id: number;
  type: "success" | "error" | "warning" | "info";
  title?: string;
  message: string;
  duration: number;
  action?: ToastAction;
  onClick?: () => void;
}

defineProps<{
  toasts: Toast[];
}>();

const emit = defineEmits<{
  remove: [id: number];
  click: [toast: Toast];
}>();

const SuccessIcon = () =>
  h(
    "svg",
    {
      width: 20,
      height: 20,
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: 2,
    },
    [h("polyline", { points: "20 6 9 17 4 12" })],
  );

const ErrorIcon = () =>
  h(
    "svg",
    {
      width: 20,
      height: 20,
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: 2,
    },
    [
      h("circle", { cx: 12, cy: 12, r: 10 }),
      h("line", { x1: 15, y1: 9, x2: 9, y2: 15 }),
      h("line", { x1: 9, y1: 9, x2: 15, y2: 15 }),
    ],
  );

const WarningIcon = () =>
  h(
    "svg",
    {
      width: 20,
      height: 20,
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: 2,
    },
    [
      h("path", {
        d: "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z",
      }),
      h("line", { x1: 12, y1: 9, x2: 12, y2: 13 }),
      h("line", { x1: 12, y1: 17, x2: 12.01, y2: 17 }),
    ],
  );

const InfoIcon = () =>
  h(
    "svg",
    {
      width: 20,
      height: 20,
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: 2,
    },
    [
      h("circle", { cx: 12, cy: 12, r: 10 }),
      h("line", { x1: 12, y1: 16, x2: 12, y2: 12 }),
      h("line", { x1: 12, y1: 8, x2: 12.01, y2: 8 }),
    ],
  );

const getIcon = (type: string) => {
  switch (type) {
    case "success":
      return SuccessIcon;
    case "error":
      return ErrorIcon;
    case "warning":
      return WarningIcon;
    case "info":
    default:
      return InfoIcon;
  }
};

const removeToast = (id: number) => {
  emit("remove", id);
};

const handleClick = (toast: Toast) => {
  if (toast.action) {
    toast.action.handler();
  }
  if (toast.onClick) {
    toast.onClick();
  }
  emit("click", toast);
  if (toast.action || toast.onClick) removeToast(toast.id);
};
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 420px;
  width: calc(100% - 2rem);
  pointer-events: none;
}

.toast {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background-color: var(--surface-3);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-sm-modal);
  pointer-events: auto;
  overflow: hidden;
  animation: slideIn 0.3s var(--transition-smooth);
}

.toast.success {
  border-left: 4px solid #c5229a;
}

.toast.success .toast-icon {
  color: #c5229a;
}

.toast.error {
  border-left: 4px solid #ef4444;
}

.toast.error .toast-icon {
  color: #ef4444;
}

.toast.warning {
  border-left: 4px solid #f59e0b;
}

.toast.warning .toast-icon {
  color: #f59e0b;
}

.toast.info {
  border-left: 4px solid var(--accent);
}

.toast.info .toast-icon {
  color: var(--accent);
}

.toast-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  overflow-wrap: anywhere;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.toast-message {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
  overflow-wrap: anywhere;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.toast-close {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
}

.toast-action { margin-top: 10px; min-height: 40px; max-width: 100%; padding: 8px 12px; border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-4); color: var(--text-primary); cursor: pointer; overflow-wrap: anywhere; }

.toast-close:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
}

.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: var(--accent);
  animation: progress linear forwards;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s var(--transition-smooth);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s var(--transition-smooth);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

@media (max-width: 768px) {
  .toast-container {
    top: 0.5rem;
    right: 0.5rem;
    left: 0.5rem;
    width: calc(100% - 1rem);
    max-width: none;
  }

  .toast {
    padding: 0.875rem;
  }

  .toast-title {
    font-size: 0.875rem;
  }

  .toast-message {
    font-size: 0.8125rem;
  }
}
</style>
