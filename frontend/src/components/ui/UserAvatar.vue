<template>
  <div class="user-avatar" :class="avatarClasses" :style="avatarStyles">
    <img
      v-if="effectiveSrc && !imageError"
      :src="effectiveSrc"
      :alt="alt"
      class="avatar-image"
      @error="handleImageError"
    />
    <div v-else class="avatar-placeholder">
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    </div>
    <span
      v-if="showOnlineIndicator && isOnline"
      class="online-indicator"
    ></span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { getDefaultAvatarForUser } from "@/utils/defaultAvatars";
import { getMediaUrl } from "@/api/client";

interface Props {
  src?: string | null;
  user?: {
    id?: number | string;
    username?: string;
    avatar_url?: string | null;
    avatar?: string | null;
    display_name?: string;
  };
  alt?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl" | "2xl";
  shape?: "circle" | "square" | "rounded";
  showOnlineIndicator?: boolean;
  isOnline?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  alt: "Avatar",
  size: "md",
  shape: "circle",
  showOnlineIndicator: false,
  isOnline: false,
});

const emit = defineEmits<{ error: [] }>();

const imageError = ref(false);

const effectiveSrc = computed(() => {
  const url = props.src || props.user?.avatar_url || props.user?.avatar || null;

  if (url && url !== "" && url !== "null" && url !== "undefined") {
    return getMediaUrl(url) || url;
  }

  if (props.user?.id) {
    return getDefaultAvatarForUser();
  }

  return null;
});
watch(effectiveSrc, () => { imageError.value = false; });

const avatarClasses = computed(() => {
  return [`user-avatar--${props.size}`, `user-avatar--${props.shape}`];
});

const avatarStyles = computed(() => {
  return {};
});

const handleImageError = () => {
  imageError.value = true;
  emit("error");
};
</script>

<style scoped>
.user-avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: var(--surface-3);
  border: 2px solid var(--border-subtle);
  overflow: hidden;
  flex-shrink: 0;
}

/* Размеры */
.user-avatar--xs {
  width: 24px;
  height: 24px;
}

.user-avatar--sm {
  width: 32px;
  height: 32px;
}

.user-avatar--md {
  width: 40px;
  height: 40px;
}

.user-avatar--lg {
  width: 48px;
  height: 48px;
}

.user-avatar--xl {
  width: 64px;
  height: 64px;
}

.user-avatar--2xl {
  width: 120px;
  height: 120px;
}

/* Формы */
.user-avatar--circle {
  border-radius: 50%;
}

.user-avatar--square {
  border-radius: 8px;
}

.user-avatar--rounded {
  border-radius: 12px;
}

/* Изображение */
.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

/* Индикатор онлайн-статуса */
.online-indicator {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--surface-1);
  z-index: 2;
  bottom: 0;
  right: 0;
  background-color: var(--accent-2);
}

.user-avatar--xs .online-indicator,
.user-avatar--sm .online-indicator {
  width: 8px;
  height: 8px;
  border-width: 1px;
}

.user-avatar--xl .online-indicator,
.user-avatar--2xl .online-indicator {
  width: 16px;
  height: 16px;
  border-width: 3px;
}

/* ============================================================
   АДАПТИВНЫЕ СТИЛИ ДЛЯ МОБИЛЬНЫХ УСТРОЙСТВ И ПЛАНШЕТОВ
   (десктопные стили выше остаются без изменений)
   ============================================================ */

/* Планшеты: 768px – 1024px */
@media (max-width: 1024px) {
  .user-avatar--2xl {
    width: 100px;
    height: 100px;
  }
}

/* Большие телефоны / маленькие планшеты: 481px – 767px */
@media (max-width: 767px) {
  .user-avatar {
    border-width: 1.5px;
  }

  .user-avatar--2xl {
    width: 88px;
    height: 88px;
  }

  .user-avatar--xl {
    width: 56px;
    height: 56px;
  }

  .user-avatar--lg {
    width: 44px;
    height: 44px;
  }
}

/* Телефоны: до 480px */
@media (max-width: 480px) {
  .user-avatar {
    border-width: 1.5px;
  }

  .user-avatar--2xl {
    width: 76px;
    height: 76px;
  }

  .user-avatar--xl {
    width: 52px;
    height: 52px;
  }

  .user-avatar--lg {
    width: 40px;
    height: 40px;
  }

  .user-avatar--md {
    width: 36px;
    height: 36px;
  }

  .avatar-placeholder svg {
    width: 20px;
    height: 20px;
  }

  .user-avatar--xs .avatar-placeholder svg,
  .user-avatar--sm .avatar-placeholder svg {
    width: 14px;
    height: 14px;
  }
}

/* Ландшафтная ориентация на телефонах */
@media (max-width: 767px) and (orientation: landscape) {
  .user-avatar--2xl {
    width: 80px;
    height: 80px;
  }
}

/* Очень узкие экраны: до 360px */
@media (max-width: 360px) {
  .user-avatar--2xl {
    width: 68px;
    height: 68px;
  }

  .user-avatar--xl {
    width: 48px;
    height: 48px;
  }

  .user-avatar--lg {
    width: 38px;
    height: 38px;
  }

  .user-avatar--md {
    width: 34px;
    height: 34px;
  }

  .avatar-placeholder svg {
    width: 18px;
    height: 18px;
  }
}

/* Устройства с вырезом (notch) и safe-area */
@supports (padding: max(0px)) {
  @media (max-width: 767px) {
    .online-indicator {
      bottom: max(0px, env(safe-area-inset-bottom, 0px));
      right: 0;
    }
  }
}
</style>
