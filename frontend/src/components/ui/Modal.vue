<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="handleOverlayClick">
        <div class="modal-container" role="dialog" aria-modal="true" @click.stop>
          <button type="button" class="modal-close" aria-label="Закрыть" @click="close"><SakuraIcon name="x" /></button>
          <slot></slot>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue";
import SakuraIcon from '@/components/icons/SakuraIcon.vue';
import { useScrollLock } from '@/composables/useScrollLock';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  closeOnOverlay: {
    type: Boolean,
    default: true,
  },
  closeOnEscape: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(["update:modelValue", "close"]);

const isOpen = ref(props.modelValue);
useScrollLock(isOpen);

watch(
  () => props.modelValue,
  (value) => {
    isOpen.value = value;
  },
);

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    close();
  }
};

const close = () => {
  isOpen.value = false;
  emit("update:modelValue", false);
  emit("close");
};

const handleEscape = (e: KeyboardEvent) => {
  if (e.key === "Escape" && props.closeOnEscape && isOpen.value) {
    close();
  }
};

onMounted(() => {
  document.addEventListener("keydown", handleEscape);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleEscape);
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: var(--viewport-top, 0px);
  left: 0;
  right: 0;
  bottom: auto;
  height: var(--viewport-height, 100dvh);
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-container {
  position: relative;
  background: var(--surface-3);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: 16px;
  max-width: 90vw;
  max-height: 90dvh;
  overflow: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-close {
  position: sticky;
  top: 8px;
  margin: 8px 8px 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  z-index: 1;
  border-radius: var(--radius-full);
  background: var(--surface-4);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition:
    transform 0.3s,
    opacity 0.3s;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
  opacity: 0;
}

/* ═══ АДАПТИВНЫЕ СТИЛИ МОДАЛЬНОГО ОКНА ═══ */

/* xs: 320px – 374px */
@media (max-width: 374px) {
  .modal-overlay {
    padding: 8px;
    align-items: flex-end;
  }

  .modal-container {
    max-width: 100%;
    max-height: calc(var(--viewport-height, 100dvh) * 0.92);
    width: 100%;
    border-radius: 12px 12px 0 0;
    box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.3);
  }
}

/* sm: 375px – 767px */
@media (min-width: 375px) and (max-width: 767px) {
  .modal-overlay {
    padding: 12px;
    align-items: flex-end;
  }

  .modal-container {
    max-width: 100%;
    max-height: calc(var(--viewport-height, 100dvh) * 0.92);
    width: 100%;
    border-radius: 16px 16px 0 0;
    box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.3);
  }
}

/* md: 768px – 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .modal-overlay {
    padding: 24px;
  }

  .modal-container {
    max-width: 80vw;
    max-height: calc(var(--viewport-height, 100dvh) * 0.88);
    border-radius: 16px;
  }
}

/* lg: 1024px+ -сохраняем поведение как на десктопе */
@media (min-width: 1024px) {
  .modal-overlay {
    padding: 20px;
    align-items: center;
  }

  .modal-container {
    max-width: 90vw;
    max-height: calc(var(--viewport-height, 100dvh) * 0.9);
    border-radius: 16px;
  }
}

/* Улучшение скролла на тач-устройствах */
@media (hover: none) and (pointer: coarse) {
  .modal-container {
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
  }
}

/* Ландшафтная ориентация на мобильных */
@media (max-width: 767px) and (orientation: landscape) {
  .modal-overlay {
    align-items: center;
    padding: 8px;
  }

  .modal-container {
    max-height: calc(var(--viewport-height, 100dvh) * 0.95);
    border-radius: 12px;
    width: auto;
    max-width: 92vw;
  }
}
</style>
