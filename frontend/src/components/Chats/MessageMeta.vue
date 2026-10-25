<template>
  <div class="mm" :class="[`mm--${variant}`, `mm--${tone}`]">
    <span v-if="pinned" class="mm-icon" title="Закреплено">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2v8m0 0-3-3m3 3 3-3M5 12h14a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2z" />
      </svg>
    </span>
    <span v-if="edited" class="mm-icon" title="Изменено">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
      </svg>
    </span>
    <span class="mm-time">{{ time }}</span>
    <span v-if="status === 'read'" class="mm-check mm-check--read" title="Прочитано"><SakuraIcon name="check-check" :size="14" /></span>
    <span v-else-if="status === 'sent'" class="mm-check mm-check--sent" title="Отправлено"><SakuraIcon name="check" :size="16" /></span>
    <span v-else-if="status === 'group'" class="mm-check mm-check--group" :title="`Прочитано ${readCount}`">
      <SakuraIcon name="check" :size="16" />{{ readCount }}
    </span>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
withDefaults(
  defineProps<{
    time: string;
    variant?: "bubble" | "media" | "plain";
    tone?: "neutral" | "accent";
    pinned?: boolean;
    edited?: boolean;
    status?: "none" | "sent" | "read" | "group";
    readCount?: number;
  }>(),
  { variant: "plain", tone: "neutral", pinned: false, edited: false, status: "none", readCount: 0 },
);
</script>

<style scoped>
.mm {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.6875rem;
  line-height: 1;
  white-space: nowrap;
}

.mm--plain {
  margin-top: 0.15rem;
}

.mm--bubble {
  position: absolute;
  right: 0.65rem;
  bottom: 0.4rem;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.35));
}

.mm--media {
  position: absolute;
  right: 0.5rem;
  bottom: 0.5rem;
  padding: 0.25rem 0.55rem;
  border-radius: var(--radius-full);
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
}

.mm-icon {
  display: flex;
  align-items: center;
}

.mm--neutral .mm-time,
.mm--neutral .mm-icon,
.mm--neutral .mm-check--sent,
.mm--neutral .mm-check--group {
  color: var(--text-tertiary);
}

.mm--neutral .mm-check--read {
  color: var(--success);
}

.mm--accent .mm-time,
.mm--accent .mm-icon,
.mm--accent .mm-check--sent,
.mm--accent .mm-check--group,
.mm--media .mm-time,
.mm--media .mm-icon,
.mm--media .mm-check--sent,
.mm--media .mm-check--group {
  color: rgba(255, 255, 255, 0.8);
}

.mm--accent .mm-check--read,
.mm--media .mm-check--read {
  color: color-mix(in srgb, var(--success) 55%, white);
}
</style>
