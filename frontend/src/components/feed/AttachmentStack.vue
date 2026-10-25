<template>
  <section class="attachment-stack" :class="{ 'is-collapsed': collapsed }">
    <button
      v-if="props.count >= 1"
      type="button"
      class="stack-toggle"
      :aria-expanded="!collapsed"
      @click.stop="collapsed = !collapsed"
    >
      <span class="stack-toggle-action">
        {{ collapsed ? 'Развернуть' : 'Свернуть' }}
        <SakuraIcon :name="collapsed ? 'chevron-down' : 'chevron-up'" :size="16" />
      </span>
    </button>

    <button
      v-show="collapsed && props.count >= 1"
      type="button"
      class="stack-preview"
      :class="[`is-${props.variant}`, `has-${displayedCount}`]"
      :aria-label="`Развернуть: ${props.label}, ${props.count}`"
      @click.stop="collapsed = false"
    >
      <span class="stack-preview-art" aria-hidden="true">
        <span
          v-for="(poster, index) in props.posters.slice(0, 3)"
          :key="`${poster}-${index}`"
          class="stack-poster"
          :class="`stack-poster-${index}`"
        >
          <OptimizedImage v-if="poster" :src="poster" alt="" />
          <SakuraIcon v-else name="image" :size="24" />
        </span>
        <span class="stack-count">{{ props.count }}</span>
      </span>
      <span class="stack-preview-copy">
        <span class="stack-preview-title">{{ props.label }}</span>
      </span>
    </button>

    <div v-show="!collapsed" class="stack-content">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import OptimizedImage from '@/components/common/OptimizedImage.vue';
import SakuraIcon from '@/components/icons/SakuraIcon.vue';

const props = withDefaults(defineProps<{
  count: number;
  posters: string[];
  label: string;
  variant?: 'poster' | 'media';
}>(), {
  variant: 'poster',
});

const collapsed = ref(true);
const displayedCount = computed(() => Math.min(3, props.count));
const previewCaption = computed(() => {
  if (props.count === 1) return 'Нажмите, чтобы посмотреть';
  return `Ещё ${props.count - 1} ${props.count - 1 === 1 ? 'элемент' : 'элемента'}`;
});
</script>

<style scoped>
.attachment-stack {
  display: flex;
  width: 100%;
  margin-top: 0.75rem;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface-3) 72%, transparent);
  transition: border-color 0.2s var(--ease-petal), box-shadow 0.2s var(--ease-petal);
}

.attachment-stack:hover,
.attachment-stack:focus-within {
  border-color: var(--border-default);
}

.attachment-stack:focus-within {
  box-shadow: 0 0 0 2px var(--accent-subtle);
}

.stack-toggle {
  display: flex;
  width: 100%;
  min-height: 48px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0.55rem 0.75rem;
  border: 0;
  border-bottom: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--surface-4) 72%, transparent);
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: background 0.2s var(--ease-petal), color 0.2s var(--ease-petal);
}

.is-collapsed .stack-toggle { border-bottom-color: transparent; }
.stack-toggle:hover { background: var(--surface-4); }

.stack-toggle:focus-visible,
.stack-preview:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.stack-heading {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.08rem;
}

.stack-kicker {
  color: var(--text-tertiary);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  line-height: 1.2;
  text-transform: uppercase;
}

.stack-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-primary);
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.25;
}

.stack-title-count {
  display: inline-flex;
  min-width: 1.35rem;
  height: 1.35rem;
  align-items: center;
  justify-content: center;
  padding: 0 0.32rem;
  border-radius: 999px;
  background: var(--accent-subtle);
  color: var(--accent);
  font-size: 0.68rem;
  font-variant-numeric: tabular-nums;
}

.stack-toggle-action {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 0.3rem;
  color: var(--text-tertiary);
  font-size: 0.72rem;
  font-weight: 600;
}

.stack-toggle:hover .stack-toggle-action { color: var(--accent); }

.stack-preview {
  display: grid;
  width: 100%;
  min-height: 112px;
  grid-template-columns: 168px minmax(0, 1fr);
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem 0.75rem;
  border: 0;
  background: radial-gradient(circle at 12% 55%, var(--accent-subtle), transparent 38%);
  color: inherit;
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: background 0.2s var(--ease-petal);
}

.stack-preview:hover {
  background:
    radial-gradient(circle at 12% 55%, var(--accent-subtle), transparent 42%),
    color-mix(in srgb, var(--surface-4) 42%, transparent);
}

.stack-preview-art {
  position: relative;
  display: block;
  width: 154px;
  height: 96px;
}

.stack-poster {
  position: absolute;
  top: 5px;
  left: 44px;
  display: flex;
  width: 62px;
  height: 84px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 2px solid var(--surface-3);
  border-radius: 9px;
  background: var(--surface-3);
  color: var(--text-tertiary);
  box-shadow: 0 7px 18px rgba(0, 0, 0, 0.28);
  transition: transform 0.22s var(--ease-petal);
}

.stack-poster :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.stack-poster-0 { z-index: 3; }
.stack-poster-1 { left: 13px; top: 9px; z-index: 2; transform: rotate(-8deg); }
.stack-poster-2 { left: 76px; top: 9px; z-index: 1; transform: rotate(8deg); }

.stack-preview.has-1 .stack-poster-0 {
  left: 24px;
  width: 112px;
}

.stack-preview:hover .stack-poster-0 { transform: translateY(-2px); }
.stack-preview:hover .stack-poster-1 { transform: translate(-2px, -1px) rotate(-10deg); }
.stack-preview:hover .stack-poster-2 { transform: translate(2px, -1px) rotate(10deg); }

.stack-preview.is-media .stack-poster {
  top: 17px;
  width: 82px;
  height: 62px;
}

.stack-preview.is-media .stack-poster-0 { left: 35px; }
.stack-preview.is-media .stack-poster-1 { left: 3px; top: 21px; }
.stack-preview.is-media .stack-poster-2 { left: 69px; top: 21px; }
.stack-preview.is-media.has-1 .stack-poster-0 { left: 10px; width: 134px; }

.stack-count {
  position: absolute;
  right: 2px;
  bottom: 2px;
  z-index: 5;
  display: flex;
  min-width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  padding: 0 0.38rem;
  border: 2px solid var(--surface-3);
  border-radius: 999px;
  background: var(--accent);
  color: var(--text-on-accent);
  font-size: 0.72rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  box-shadow: var(--shadow-petal-sm);
}

.stack-preview-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.28rem;
  padding-right: 0.25rem;
}

.stack-preview-title {
  overflow: hidden;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stack-preview-caption {
  color: var(--text-tertiary);
  font-size: 0.72rem;
  line-height: 1.4;
}

.stack-content {
  padding: 0.65rem;
  animation: stack-reveal 0.2s var(--ease-petal);
}

@keyframes stack-reveal {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 480px) {
  .stack-toggle-action { font-size: 0; }

  .stack-toggle-action :deep(svg) {
    width: 18px;
    height: 18px;
  }

  .stack-preview {
    min-height: 104px;
    grid-template-columns: 142px minmax(0, 1fr);
    padding-inline: 0.5rem;
  }

  .stack-preview-art {
    width: 136px;
    transform: scale(0.9);
    transform-origin: left center;
  }

  .stack-preview-caption { font-size: 0.68rem; }
}

@media (prefers-reduced-motion: reduce) {
  .stack-poster,
  .stack-content {
    animation: none;
    transition: none;
  }
}
</style>
