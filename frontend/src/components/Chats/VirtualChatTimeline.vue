<template>
  <div ref="root" class="virtual-timeline">
    <div :style="{ height: `${offsets[start]}px` }" aria-hidden="true" />
    <div v-for="message in visible" :key="messageRenderKey(message)" :data-timeline-key="messageRenderKey(message)" :data-timeline-id="message.id" class="timeline-item">
      <slot :message="message" />
    </div>
    <div :style="{ height: `${(offsets[messages.length] ?? 0) - (offsets[end] ?? 0)}px` }" aria-hidden="true" />
  </div>
</template>

<script setup lang="ts" generic="T extends TimelineMessage">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import type { TimelineMessage } from '@/lib/chatTimeline';
import { messageRenderKey } from '@/lib/chatTimeline';

const props = defineProps<{ messages: T[]; scrollElement?: HTMLElement | null}>();
const emit = defineEmits<{ rendered: [] }>();
const root = ref<HTMLElement>();
const position = ref(0);
const viewport = ref(600);
const revision = ref(0);
const heights = new Map<string, number>();
let resize: ResizeObserver | undefined;
let resizeFrame: number | undefined;
const pendingHeights = new Map<string, number>();
let disposed = false;
let activeScrollElement: HTMLElement | null = null;
const offsets = computed(() => {
  void revision.value;
  const values = [0];
  for (const message of props.messages) values.push(values[values.length - 1]! + (heights.get(messageRenderKey(message)) ?? 96));
  return values;
});
const indexAt = (value: number) => {
  let low = 0, high = props.messages.length;
  while (low < high) {
    const middle = (low + high) >>> 1;
    if (offsets.value[middle + 1]! < value) low = middle + 1;
    else high = middle;
  }
  return low;
};
const start = computed(() => indexAt(Math.max(0, position.value - 800)));
const end = computed(() => Math.min(props.messages.length, indexAt(position.value + viewport.value + 800) + 1));
const visible = computed(() => props.messages.slice(start.value, end.value));
const updateViewport = () => {
  if (!activeScrollElement || !root.value) return;
  const origin = root.value.getBoundingClientRect().top - activeScrollElement.getBoundingClientRect().top + activeScrollElement.scrollTop;
  position.value = Math.max(0, activeScrollElement.scrollTop - origin);
  viewport.value = activeScrollElement.clientHeight || 600;
};
watch(() => props.scrollElement, element => {
  activeScrollElement?.removeEventListener('scroll', updateViewport);
  activeScrollElement = element ?? null;
  activeScrollElement?.addEventListener('scroll', updateViewport, { passive: true });
  updateViewport();
}, { immediate: true, flush: 'post' });
watch([visible, root], async () => {
  await nextTick();
  resize?.disconnect();
  if (disposed || !root.value || typeof ResizeObserver === 'undefined') return;
  updateViewport();
  resize = new ResizeObserver(entries => {
    for (const entry of entries) {
      pendingHeights.set((entry.target as HTMLElement).dataset.timelineKey!, entry.target.getBoundingClientRect().height);
    }
    if (resizeFrame !== undefined) return;
    resizeFrame = requestAnimationFrame(() => {
      resizeFrame = undefined;
      if (disposed) return;
      const anchor = indexAt(position.value);
      const previous = offsets.value[anchor] ?? 0;
      const follow = !!activeScrollElement && activeScrollElement.scrollHeight - activeScrollElement.scrollTop - activeScrollElement.clientHeight < 80;
      let changed = false;
      for (const [id, height] of pendingHeights) {
        if (height > 0 && Math.abs((heights.get(id) ?? 96) - height) > 1) {
          heights.set(id, height); changed = true;
        }
      }
      pendingHeights.clear();
      if (!changed) return;
      revision.value++;
      nextTick(() => {
        if (disposed || !activeScrollElement) return;
        if (follow) activeScrollElement.scrollTop = activeScrollElement.scrollHeight;
        else activeScrollElement.scrollTop += (offsets.value[anchor] ?? 0) - previous;
        updateViewport();
      });
    });
  });
  root.value.querySelectorAll('[data-timeline-id]').forEach(element => resize?.observe(element));
  emit('rendered');
}, { immediate: true, flush: 'post' });
watch(() => props.messages, messages => {
  const ids = new Set(messages.map(messageRenderKey));
  for (const id of heights.keys()) if (!ids.has(id)) heights.delete(id);
  for (const id of pendingHeights.keys()) if (!ids.has(id)) pendingHeights.delete(id);
});
const scrollToMessage = async (id: number) => {
  const index = props.messages.findIndex(message => message.id === id);
  if (index < 0 || !activeScrollElement) return false;
  activeScrollElement.scrollTop = Math.max(0, (offsets.value[index] ?? 0) - viewport.value / 2);
  updateViewport();
  await nextTick();
  return true;
};
defineExpose({ scrollToMessage });
onBeforeUnmount(() => {
  disposed = true;
  resize?.disconnect();
  if (resizeFrame !== undefined) cancelAnimationFrame(resizeFrame);
  pendingHeights.clear();
  activeScrollElement?.removeEventListener('scroll', updateViewport);
});
</script>

<style scoped>
.virtual-timeline { width: 100%; }
.timeline-item { display: flow-root; width: 100%; padding-bottom: 8px; }
</style>
