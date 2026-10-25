<template>
  <Teleport to="body">
  <transition name="modal">
    <div v-if="show" class="modal-overlay" @click="handleOverlayClick">
      <div class="modal-container" :class="modalSizeClass" role="dialog" aria-modal="true" :aria-label="title || 'Диалог'" @click.stop>
        <div class="modal-header" v-if="$slots.header || title">
          <slot name="header">
            <h2 class="modal-title">{{ title }}</h2>
          </slot>
          <button
            class="modal-close"
            @click="close"
            type="button"
            aria-label="Закрыть"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <slot></slot>
        </div>

        <div class="modal-footer" v-if="$slots.footer">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>
  </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";
import { useScrollLock } from '@/composables/useScrollLock';

interface Props {
  show: boolean;
  title?: string;
  size?: "small" | "medium" | "large" | "full";
  closeOnOverlay?: boolean;
  closeOnEscape?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: "",
  size: "medium",
  closeOnOverlay: true,
  closeOnEscape: true,
});

const emit = defineEmits<{
  "update:show": [value: boolean];
  close: [];
}>();

const modalSizeClass = computed(() => {
  return `modal-container--${props.size}`;
});

const close = () => {
  emit("update:show", false);
  emit("close");
};

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    close();
  }
};

const handleEscapeKey = (event: KeyboardEvent) => {
  if (event.key === "Escape" && props.closeOnEscape && props.show) {
    close();
  }
};

useScrollLock(() => props.show);

onMounted(() => {
  document.addEventListener("keydown", handleEscapeKey);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleEscapeKey);
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: var(--viewport-top, 0px) 0 auto;
  height: var(--viewport-height, 100dvh);
  background-color: rgba(0, 0, 0, 0.78);
  backdrop-filter: var(--blur-md);
  -webkit-backdrop-filter: var(--blur-md);
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
}

.modal-container {
  background-color: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm-modal);
  max-height: calc(var(--viewport-height, 100dvh) - 48px);
  min-width: 0;
  display: flex;
  flex-direction: column;
  animation: scaleIn var(--duration-slow) var(--ease-spring);
}

.modal-container--small {
  width: 100%;
  max-width: 400px;
}
.modal-container--medium {
  width: 100%;
  max-width: 560px;
}
.modal-container--large {
  width: 100%;
  max-width: 800px;
}
.modal-container--full {
  width: 100%;
  max-width: 100%;
  height: calc(calc(var(--viewport-height, 100dvh) * 1) - 48px);
}

.modal-header {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.modal-title {
  min-width: 0;
  overflow-wrap: anywhere;
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.modal-close {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  color: var(--text-tertiary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
  border: none;
}

.modal-close:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
}

.modal-body {
  min-height: 0;
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

/* Анимации */
.modal-enter-active {
  transition: opacity var(--duration-base) var(--ease-out);
}
.modal-leave-active {
  transition: opacity var(--duration-base) var(--ease-out);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container {
  transition: transform var(--duration-slow) var(--ease-spring);
}
.modal-leave-active .modal-container {
  transition: transform var(--duration-base) var(--ease-out);
}
.modal-enter-from .modal-container {
  transform: translateY(16px) scale(0.96);
}
.modal-leave-to .modal-container {
  transform: translateY(8px) scale(0.98);
}

@keyframes scaleIn {
  from {
    transform: translateY(16px) scale(0.96);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

/* ═══ АДАПТИВНОСТЬ ═══════════════════════════════════════════ */

/* xs: 320px – 374px */
@media (max-width: 374px) {
  .modal-overlay {
    padding: 0;
    align-items: flex-end;
  }

  .modal-container {
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    border-bottom: none;
    max-height: calc(var(--viewport-height, 100dvh) * 0.94);
  }

  .modal-container--small,
  .modal-container--medium,
  .modal-container--large,
  .modal-container--full {
    max-width: 100%;
  }

  .modal-container--full {
    height: calc(var(--viewport-height, 100dvh) * 0.94);
  }

  .modal-header {
    padding: var(--space-3) var(--space-4);
  }

  .modal-title {
    font-size: var(--text-lg);
  }

  .modal-close {
    width: 30px;
    height: 30px;
    min-height: 30px;
  }

  .modal-body {
    padding: var(--space-4);
  }

  .modal-footer {
    padding: var(--space-3) var(--space-4);
    gap: var(--space-2);
    flex-wrap: wrap;
  }

  .modal-footer > * {
    flex: 1 1 auto;
    min-width: 0;
  }

  .modal-enter-from .modal-container,
  .modal-leave-to .modal-container {
    transform: translateY(100%);
  }

  @keyframes scaleIn {
    from {
      transform: translateY(100%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
}

/* sm: 375px – 767px */
@media (min-width: 375px) and (max-width: 767px) {
  .modal-overlay {
    padding: 0;
    align-items: flex-end;
  }

  .modal-container {
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    border-bottom: none;
    max-height: calc(var(--viewport-height, 100dvh) * 0.92);
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
  }

  .modal-container--small,
  .modal-container--medium,
  .modal-container--large,
  .modal-container--full {
    max-width: 100%;
  }

  .modal-container--full {
    height: calc(var(--viewport-height, 100dvh) * 0.92);
  }

  .modal-header {
    padding: var(--space-4) var(--space-5);
  }

  .modal-title {
    font-size: var(--text-lg);
  }

  .modal-body {
    padding: var(--space-5);
  }

  .modal-footer {
    padding: var(--space-4) var(--space-5);
    gap: var(--space-2);
  }

  .modal-enter-from .modal-container,
  .modal-leave-to .modal-container {
    transform: translateY(100%);
  }

  @keyframes scaleIn {
    from {
      transform: translateY(100%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
}

/* md: 768px – 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .modal-overlay {
    padding: var(--space-5);
    align-items: center;
  }

  .modal-container {
    max-height: calc(calc(var(--viewport-height, 100dvh) * 1) - 80px);
    border-radius: var(--radius-xl);
  }

  .modal-container--small {
    max-width: 420px;
  }

  .modal-container--medium {
    max-width: 620px;
  }

  .modal-container--large {
    max-width: 90vw;
  }

  .modal-container--full {
    max-width: 100%;
    height: calc(calc(var(--viewport-height, 100dvh) * 1) - 80px);
  }

  .modal-header {
    padding: var(--space-4) var(--space-5);
  }

  .modal-body {
    padding: var(--space-5);
  }

  .modal-footer {
    padding: var(--space-4) var(--space-5);
  }
}

/* Планшеты в ландшафтной ориентации */
@media (min-width: 768px) and (max-width: 1023px) and (orientation: landscape) {
  .modal-overlay {
    padding: var(--space-4);
  }

  .modal-container {
    max-height: calc(calc(var(--viewport-height, 100dvh) * 1) - 40px);
  }

  .modal-container--full {
    height: calc(calc(var(--viewport-height, 100dvh) * 1) - 40px);
  }
}

/* Мобильные в ландшафтной ориентации -центрируем модалку по вертикали */
@media (max-width: 767px) and (orientation: landscape) {
  .modal-overlay {
    align-items: center;
    padding: var(--space-2);
  }

  .modal-container {
    position: relative;
    max-height: calc(var(--viewport-height, 100dvh) * 0.96);
    border-radius: var(--radius-xl);
    border-bottom: 1px solid var(--border-default);
    max-width: 92vw;
    left: auto;
    right: auto;
  }

  .modal-container--small,
  .modal-container--medium,
  .modal-container--large {
    max-width: 92vw;
  }

  .modal-container--full {
    height: calc(var(--viewport-height, 100dvh) * 0.96);
  }

  .modal-header {
    padding: var(--space-3) var(--space-4);
  }

  .modal-body {
    padding: var(--space-4);
  }

  .modal-footer {
    padding: var(--space-3) var(--space-4);
  }

  .modal-enter-from .modal-container,
  .modal-leave-to .modal-container {
    transform: translateY(16px) scale(0.96);
  }

  @keyframes scaleIn {
    from {
      transform: translateY(16px) scale(0.96);
      opacity: 0;
    }
    to {
      transform: translateY(0) scale(1);
      opacity: 1;
    }
  }
}

/* Улучшение тач-взаимодействия */
@media (hover: none) and (pointer: coarse) {
  .modal-close {
    width: 38px;
    height: 38px;
    min-height: 38px;
  }

  .modal-close:hover {
    background-color: transparent;
    color: var(--text-tertiary);
  }

  .modal-close:active {
    background-color: var(--surface-4);
    color: var(--text-primary);
  }

  .modal-body {
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
  }
}

@media (pointer: coarse) {
  .modal-close { width: 44px; height: 44px; min-height: 44px; }
}
@media (prefers-reduced-motion: reduce) {
  .modal-container { animation: none; }
}
</style>
