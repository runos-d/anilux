<template>
  <div ref="root" class="virtual-feed">
    <div :style="{ height: `${offsets[start]}px` }" aria-hidden="true" />
    <div v-for="item in visible" :key="String(item.id)" :data-feed-key="String(item.id)" class="virtual-feed-item">
      <slot :item="item" />
    </div>
    <div :style="{ height: `${(offsets[items.length] || 0) - (offsets[end] || 0)}px` }" aria-hidden="true" />
  </div>
</template>
<script setup lang="ts" generic="T extends { id: string | number }">
import { computed, nextTick, onMounted, onBeforeUnmount, onActivated, onDeactivated, ref, watch } from 'vue';
const props = defineProps<{ items: T[] }>();
const root = ref<HTMLElement>();
const position = ref(0), viewport = ref(800), revision = ref(0);
const heights = new Map<string, number>();
let active = false, disposed = false;
let frame: number | undefined;
let observer: ResizeObserver | undefined;
const offsets = computed(() => {
  void revision.value;
  const result = [0];
  for (const item of props.items) result.push(result[result.length - 1]! + (heights.get(String(item.id)) || 500));
  return result;
});
function indexAt(value: number) {
  let low = 0, high = props.items.length;
  while (low < high) {
    const middle = (low + high) >>> 1;
    if (offsets.value[middle + 1]! < value) low = middle + 1; else high = middle;
  }
  return low;
}
const start = computed(() => indexAt(Math.max(0, position.value - 1000)));
const end = computed(() => Math.min(props.items.length, indexAt(position.value + viewport.value + 1000) + 1));
const visible = computed(() => props.items.slice(start.value, end.value));
function update() {
  if (!active || !root.value) return;
  position.value = Math.max(0, -root.value.getBoundingClientRect().top);
  viewport.value = window.innerHeight;
}
function schedule() {
  if (frame !== undefined) return;
  frame = requestAnimationFrame(() => { frame = undefined; update(); });
}
function activate() {
  if (active || disposed) return;
  active = true;
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  update();
}
function deactivate() {
  active = false;
  window.removeEventListener('scroll', schedule);
  window.removeEventListener('resize', schedule);
  if (frame !== undefined) cancelAnimationFrame(frame);
  frame = undefined;
}
watch([visible, root], async () => {
  await nextTick(); observer?.disconnect();
  if (disposed || !root.value || typeof ResizeObserver === 'undefined') return;
  observer = new ResizeObserver(entries => {
    const anchor = indexAt(position.value), before = offsets.value[anchor] || 0;
    let changed = false;
    for (const entry of entries) {
      const key = (entry.target as HTMLElement).dataset.feedKey!;
      const height = entry.target.getBoundingClientRect().height;
      if (height > 0 && Math.abs((heights.get(key) || 500) - height) > 1) { heights.set(key, height); changed = true; }
    }
    if (!changed) return;
    revision.value++;
    nextTick(() => {
      if (!active || disposed) return;
      const delta = (offsets.value[anchor] || 0) - before;
      if (delta) window.scrollBy(0, delta);
      schedule();
    });
  });
  root.value.querySelectorAll('[data-feed-key]').forEach(element => observer?.observe(element));
}, { immediate: true, flush: 'post' });
watch(() => props.items, items => {
  const ids = new Set(items.map(item => String(item.id)));
  for (const key of heights.keys()) if (!ids.has(key)) heights.delete(key);
  schedule();
});
onMounted(activate); onActivated(activate); onDeactivated(deactivate);
onBeforeUnmount(() => { disposed = true; deactivate(); observer?.disconnect(); });
</script>
<style scoped>
.virtual-feed, .virtual-feed-item { width: 100%; min-width: 0; }
.virtual-feed-item { display: flow-root; }
</style>
