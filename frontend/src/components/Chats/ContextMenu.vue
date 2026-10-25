<script setup lang="ts">
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue';
interface Props {
  isOpen: boolean;
  x?: number;
  y?: number;
}

const props = defineProps<Props>();
const menu = ref<HTMLElement | null>(null);
const position = ref({ x: 12, y: 12 });
async function place() {
  await nextTick();
  if (!props.isOpen || !menu.value) return;
  const viewport = window.visualViewport;
  const width = viewport?.width ?? window.innerWidth;
  const height = viewport?.height ?? window.innerHeight;
  const top = viewport?.offsetTop ?? 0;
  const rect = menu.value.getBoundingClientRect();
  position.value = {
    x: Math.max(12, Math.min(props.x ?? 12, width - rect.width - 12)),
    y: Math.max(top + 12, Math.min(props.y ?? top + 12, top + height - rect.height - 12)),
  };
}
function dismiss(event: KeyboardEvent) { if (props.isOpen && event.key === 'Escape') emit('close'); }
watch(() => [props.isOpen, props.x, props.y], place);
onMounted(() => { window.addEventListener('resize', place); window.addEventListener('keydown', dismiss); });
onUnmounted(() => { window.removeEventListener('resize', place); window.removeEventListener('keydown', dismiss); });

const emit = defineEmits<{
  close: [];
}>();
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="context-menu-backdrop" @click="emit('close')">
      <div
        ref="menu"
        class="context-menu"
        :style="{ left: position.x + 'px', top: position.y + 'px' }"
        @click.stop
      >
        <div class="context-menu-content">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.context-menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
}

.context-menu {
  position: absolute;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  min-width: 180px;
  max-width: min(280px, calc(100vw - 24px));
  max-height: calc(var(--viewport-height, 100dvh) - 24px);
  overflow-y: auto;
}

.context-menu-content {
  padding: 0.25rem;
}

:deep(.context-menu-item) {
  width: 100%;
  min-height: 44px;
  border: 0;
  background: transparent;
  text-align: left;
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.15s;
}

:deep(.context-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
}

:deep(.context-menu-divider) {
  height: 1px;
  background: var(--border-default);
  margin: 0.25rem 0;
}

:deep(.context-menu-item.danger) {
  color: #ff6b6b;
}

:deep(.context-menu-item.danger:hover) {
  background: rgba(244, 67, 54, 0.15);
}
</style>
