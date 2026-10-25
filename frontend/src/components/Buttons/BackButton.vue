<template>
  <button @click="handleClick" class="back-btn" type="button">
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
    >
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
    <span v-if="showLabel">{{ label }}</span>
  </button>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router"
interface Props {
  to?: string | (() => void);
  label?: string;
  showLabel?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  label: "Назад",
  showLabel: true,
});

const router = useRouter();

const handleClick = () => {
  if (typeof props.to === "function") {
    props.to();
  } else if (typeof props.to === "string") {
    router.push(props.to);
  } else {
    router.back();
  }
};
</script>

<style scoped>
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background-color: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.back-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background-color: var(--surface-3);
  transform: translateX(-2px);
}

.back-btn:active {
  transform: translateX(0);
}

@media (max-width: 768px) {
  .back-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.8125rem;
  }
}

@media (max-width: 480px) {
  .back-btn {
    padding: 0.4375rem 0.625rem;
    font-size: 0.75rem;
    gap: 0.375rem;
    border-radius: 0.375rem;
  }

  .back-btn svg {
    width: 18px;
    height: 18px;
  }
}

@media (max-width: 360px) {
  .back-btn {
    padding: 0.375rem 0.5rem;
    font-size: 0.6875rem;
    gap: 0.3125rem;
  }

  .back-btn svg {
    width: 16px;
    height: 16px;
  }
}

@media (min-width: 481px) and (max-width: 768px) {
  .back-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.8125rem;
  }

  .back-btn svg {
    width: 19px;
    height: 19px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .back-btn {
    padding: 0.5625rem 0.9375rem;
    font-size: 0.84375rem;
  }
}

@media (hover: none) and (pointer: coarse) {
  .back-btn {
    min-height: 40px;
  }

  .back-btn:hover {
    border-color: var(--border-strong);
    color: var(--text-secondary);
    background-color: var(--surface-4);
    transform: none;
  }

  .back-btn:active {
    border-color: var(--accent);
    color: var(--accent);
    background-color: var(--surface-3);
    transform: translateX(-2px);
  }
}

@media (max-width: 360px) {
  .back-btn {
    min-height: 36px;
  }
}
</style>