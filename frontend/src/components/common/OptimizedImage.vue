<script setup lang="ts">
import { computed, ref, watch } from "vue"
import { Image } from "@unpic/vue"
import SakuraIcon from '@/components/icons/SakuraIcon.vue';
interface Props {
  src: string;
  alt: string;
  width?: number | string;
  height?: number | string;
  priority?: boolean;
  layout?: "constrained" | "fixed" | "fullWidth";
  sizes?: string;
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  width: undefined,
  height: undefined,
  priority: false,
  layout: "constrained",
  sizes: "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw",
});

const imageSrc = computed(() => props.src);
const failed = ref(false);
const emit = defineEmits<{ error: [event: Event] }>();
watch(imageSrc, () => { failed.value = false; });
function onError(event: Event) { failed.value = true; emit('error', event); }
const fallbackRatio = computed(() => Number(props.width) > 0 && Number(props.height) > 0
  ? `${props.width} / ${props.height}` : undefined);

const computedSizes = computed(() => {
  if (props.sizes) return props.sizes;
  return "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw";
});
</script>

<template>
  <Image
    v-if="!failed"
    :src="imageSrc"
    :alt="alt"
    :width="width"
    :height="height"
    :layout="layout"
    :sizes="computedSizes"
    :priority="priority"
    :class="props.class"
    :loading="priority ? 'eager' : 'lazy'"
    decoding="async"
    @error="onError"
    :background-color="layout === 'fullWidth' ? '#1a1a1a' : undefined"
  />
  <div v-else class="image-fallback" :class="props.class" :style="{ aspectRatio: fallbackRatio }" role="img" :aria-label="alt || 'Изображение недоступно'">
    <SakuraIcon name="image" :size="28" />
  </div>
</template>

<style scoped>
.image-fallback { display: grid; place-items: center; width: 100%; height: 100%; min-height: 24px; overflow: hidden; background: var(--surface-3); color: var(--text-tertiary); }
</style>
