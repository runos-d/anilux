<template>
  <Teleport to="body">
    <Transition name="float">
      <div
        v-if="isPlayerVisible"
        ref="playerContainer"
        class="floating-player"
        :class="{
          minimized: isMinimized,
          'is-dragging': isDragging,
          'is-resizing': isResizing,
          'is-fullscreen': isFullscreen,
        }"
        :style="playerStyle"
        @mousedown="startDrag"
        @touchstart="startDrag"
      >
        <div
          class="fp-header"
          @dblclick="toggleMinimize"
          @touchend.stop="handleHeaderTouch"
        >
          <div class="fp-info">
            <span class="fp-title">{{ animeTitle }}</span>
            <span class="fp-episode" v-if="episodeInfo"
              >Серия {{ episodeInfo }}</span
            >
          </div>
          <div class="fp-controls">
            <button
              class="fp-btn"
              :class="{ 'fp-btn-active': preserveAspectRatio }"
              @click.stop="preserveAspectRatio = !preserveAspectRatio"
              :title="
                preserveAspectRatio
                  ? 'Сохранять пропорции (вкл)'
                  : 'Сохранять пропорции (выкл)'
              "
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
                <line x1="15" y1="3" x2="15" y2="21" />
                <line x1="3" y1="9" x2="21" y2="9" />
                <line x1="3" y1="15" x2="21" y2="15" />
              </svg>
            </button>
            <button
              class="fp-btn"
              @click.stop="toggleFullscreen"
              :title="
                isFullscreen ? 'Выйти из полноэкранного' : 'Полноэкранный режим'
              "
            >
              <svg
                v-if="isFullscreen"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"
                />
              </svg>
              <svg
                v-else
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"
                />
              </svg>
            </button>
            <button
              class="fp-btn"
              @click.stop="toggleMinimize"
              :title="isMinimized ? 'Развернуть' : 'Свернуть'"
            >
              <svg
                v-if="isMinimized"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="15 3 21 3 21 9"></polyline>
                <polyline points="9 21 3 21 3 15"></polyline>
                <line x1="21" y1="3" x2="14" y2="10"></line>
                <line x1="3" y1="21" x2="10" y2="14"></line>
              </svg>
              <svg
                v-else
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="9" y1="3" x2="9" y2="21"></line>
              </svg>
            </button>
            <button class="fp-btn fp-close" @click.stop="close" title="Закрыть">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>

        <div v-if="!isMinimized" class="fp-content">
          <div class="fp-video-wrapper">
            <iframe
              v-if="playerLink"
              ref="kodikIframe"
              :src="playerLink"
              class="kodik-iframe"
              frameborder="0"
              allow="autoplay *; fullscreen *; encrypted-media *"
            ></iframe>
            <div v-else class="fp-no-video">
              <span>Видео недоступно</span>
            </div>
          </div>
        </div>

        <div v-else class="fp-minimized-content">
          <span class="fp-mini-time">{{ formatTime(currentTime) }}</span>
        </div>

        <div
          v-if="!isMinimized"
          class="fp-resize-handle"
          :class="{ 'fp-resize-hidden': isFullscreen }"
          @mousedown.stop.prevent="startResize"
          @touchstart.stop.prevent="startResize"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
            <circle cx="2" cy="2" r="1.5" />
            <circle cx="7" cy="2" r="1.5" />
            <circle cx="2" cy="7" r="1.5" />
            <circle cx="7" cy="7" r="1.5" />
          </svg>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { floatingPlayerLayout } from '@/lib/floatingPlayerLayout';

interface Props {
  visible: boolean;
  animeId?: number;
  animeTitle?: string;
  episode?: number;
  season?: number;
  playerLink?: string;
  translationId?: number | string | null;
  startTime?: number;
}

const props = withDefaults(defineProps<Props>(), {
  animeId: 0,
  animeTitle: "Аниме",
  episode: 1,
  season: 1,
  playerLink: "",
  translationId: null,
  startTime: 0,
});

const emit = defineEmits<{
  close: [time?: number];
  expand: [];
  play: [];
  pause: [];
  "time-update": [time: number];
  "duration-update": [duration: number];
}>();

const episodeInfo = computed(() => props.episode);
const playerContainer = ref<HTMLElement | null>(null);
const kodikIframe = ref<HTMLIFrameElement | null>(null);
const isMinimized = ref(false);
const isDragging = ref(false);
const isResizing = ref(false);
const isFullscreen = ref(false);
const playerReady = ref(false);
const preserveAspectRatio = ref(true);

const mainPlayerTimeAtOpen = ref(0);
const floatingPlayerTime = ref(0);

const needsSeek = ref(false);

const position = ref({ x: 20, y: 20 });
const visualViewport = window.visualViewport;
const readViewport = () => ({ width: visualViewport?.width ?? window.innerWidth,
  height: visualViewport?.height ?? window.innerHeight, offsetLeft: visualViewport?.offsetLeft ?? 0,
  offsetTop: visualViewport?.offsetTop ?? 0 });
const viewport = ref(readViewport());
const updateViewport = () => { viewport.value = readViewport(); };
const size = ref({ width: 480, height: 312 });
const aspectRatio = ref(16 / 9);
const dragOffset = ref({ x: 0, y: 0 });
const resizeStart = ref({ x: 0, y: 0, width: 0, height: 0 });

const isPlayerVisible = computed(() => props.visible);

const currentTime = ref(0);
const duration = ref(0);

watch(
  () => props.startTime,
  (newTime) => {
    if (newTime > 0 && !playerReady.value) {
      mainPlayerTimeAtOpen.value = newTime;
      currentTime.value = newTime;
    }
  },
);

watch(currentTime, (newTime) => {
  floatingPlayerTime.value = newTime;
});

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const isMobile = computed(() => viewport.value.width <= 768);
const layout = computed(() => floatingPlayerLayout(viewport.value, size.value, position.value, isMinimized.value, aspectRatio.value));

const playerStyle = computed(() => {
  if (isFullscreen.value) {
    return {
      left: `${viewport.value.offsetLeft}px`,
      top: `${viewport.value.offsetTop}px`,
      width: `${viewport.value.width}px`,
      height: `${viewport.value.height}px`,
      borderRadius: "0",
    };
  }

  return {
    left: `${layout.value.x}px`,
    top: `${layout.value.y}px`,
    width: `${layout.value.width}px`,
    height: `${layout.value.height}px`,
  };
});

const handleHeaderTouch = (e: TouchEvent) => {
  if (!isDragging.value) {
    void e;
  }
};

const startDrag = (e: MouseEvent | TouchEvent) => {
  if (!(e.target as HTMLElement).closest('.fp-header')) return;
  if (
    (e.target as HTMLElement).closest(".fp-btn") ||
    (e.target as HTMLElement).closest(".fp-resize-handle")
  ) {
    return;
  }

  const isTouch = "touches" in e;
  if (isTouch) {
  }

  isDragging.value = true;
  const touch = "touches" in e ? e.touches[0] : null;
  const clientX = touch ? touch.clientX : (e as MouseEvent).clientX;
  const clientY = touch ? touch.clientY : (e as MouseEvent).clientY;

  dragOffset.value = {
    x: clientX - layout.value.x,
    y: clientY - layout.value.y,
  };

  document.addEventListener("mousemove", onDrag);
  document.addEventListener("mouseup", stopDrag);
  document.addEventListener("touchmove", onDrag, { passive: false });
  document.addEventListener("touchend", stopDrag);
};

const onDrag = (e: MouseEvent | TouchEvent) => {
  if (!isDragging.value) return;
  e.preventDefault();

  const touch = "touches" in e ? e.touches[0] : null;
  const clientX = touch ? touch.clientX : (e as MouseEvent).clientX;
  const clientY = touch ? touch.clientY : (e as MouseEvent).clientY;

  let newX = clientX - dragOffset.value.x;
  let newY = clientY - dragOffset.value.y;

  const w = layout.value.width;
  const h = layout.value.height;

  newX = Math.max(0, Math.min(window.innerWidth - w, newX));
  newY = Math.max(0, Math.min(window.innerHeight - h, newY));

  position.value = { x: newX, y: newY };
};

const stopDrag = () => {
  isDragging.value = false;
  document.removeEventListener("mousemove", onDrag);
  document.removeEventListener("mouseup", stopDrag);
  document.removeEventListener("touchmove", onDrag);
  document.removeEventListener("touchend", stopDrag);
  savePosition();
};

const startResize = (e: MouseEvent | TouchEvent) => {
  e.preventDefault();
  e.stopPropagation();
  isResizing.value = true;
  const touch = "touches" in e ? e.touches[0] : null;
  const clientX = touch ? touch.clientX : (e as MouseEvent).clientX;
  const clientY = touch ? touch.clientY : (e as MouseEvent).clientY;

  resizeStart.value = {
    x: clientX,
    y: clientY,
    width: size.value.width,
    height: size.value.height,
  };

  document.addEventListener("mousemove", onResize);
  document.addEventListener("mouseup", stopResize);
  document.addEventListener("touchmove", onResize, { passive: false });
  document.addEventListener("touchend", stopResize);
};

const HEADER_HEIGHT = 42;

const onResize = (e: MouseEvent | TouchEvent) => {
  if (!isResizing.value) return;
  e.preventDefault();
  e.stopPropagation();

  const touch = "touches" in e ? e.touches[0] : null;
  const clientX = touch ? touch.clientX : (e as MouseEvent).clientX;
  const clientY = touch ? touch.clientY : (e as MouseEvent).clientY;

  const deltaX = clientX - resizeStart.value.x;
  const deltaY = clientY - resizeStart.value.y;

  const maxWidth = isMobile.value
    ? window.innerWidth - 20
    : window.innerWidth - position.value.x;

  let newWidth = Math.max(
    Math.min(320, maxWidth),
    Math.min(maxWidth, resizeStart.value.width + deltaX),
  );
  let newHeight: number;

  if (preserveAspectRatio.value) {
    newHeight = newWidth / aspectRatio.value + HEADER_HEIGHT;
    const maxHeight = window.innerHeight - position.value.y;
    if (newHeight > maxHeight) {
      newHeight = maxHeight;
      newWidth = (newHeight - HEADER_HEIGHT) * aspectRatio.value;
    }
  } else {
    newHeight = Math.max(
      180 + HEADER_HEIGHT,
      Math.min(
        window.innerHeight - position.value.y,
        resizeStart.value.height + deltaY,
      ),
    );
  }

  size.value = { width: newWidth, height: newHeight };
};

const stopResize = () => {
  isResizing.value = false;
  document.removeEventListener("mousemove", onResize);
  document.removeEventListener("mouseup", stopResize);
  document.removeEventListener("touchmove", onResize);
  document.removeEventListener("touchend", stopResize);
  saveSize();
};

const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value;
};

const close = () => {
  const timeToReturn = floatingPlayerTime.value || currentTime.value;
  emit("close", timeToReturn);
};

const toggleFullscreen = () => {
  if (!playerContainer.value) return;

  if (!isFullscreen.value) {
    if (playerContainer.value.requestFullscreen) {
      playerContainer.value.requestFullscreen();
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }
};

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement;
};

const sendMessage = (data: Record<string, unknown>) => {
  if (!kodikIframe.value?.contentWindow) return;
  kodikIframe.value.contentWindow.postMessage(data, "*");
};

const handlePlayerMessage = (event: MessageEvent) => {
  if (!event.data || typeof event.data !== "object") return;

  const { key, value } = event.data;
  if (!key || !key.startsWith("kodik_player_")) return;

  switch (key) {
    case "kodik_player_play":
      isPlaying.value = true;
      emit("play");
      break;
    case "kodik_player_pause":
      isPlaying.value = false;
      emit("pause");
      break;
    case "kodik_player_time_update":
      if (typeof value === "number") {
        currentTime.value = value;
        emit("time-update", value);
      }
      break;
    case "kodik_player_duration_update":
      if (typeof value === "number") {
        duration.value = value;
        emit("duration-update", value);
        if (needsSeek.value && props.startTime > 0) {
          setTimeout(() => {
            sendMessage({
              key: "kodik_player_api",
              value: { method: "seek", seconds: props.startTime },
            });
            needsSeek.value = false;
          }, 500);
        }
      }
      break;
    case "kodik_player_volume_change":
      if (value && typeof value === "object") {
        isMuted.value = Boolean((value as { muted?: boolean }).muted);
      }
      break;
    case "kodik_player_video_started":
      playerReady.value = true;
      if (props.startTime > 0) {
        needsSeek.value = true;
      }
      break;
  }
};

const isPlaying = ref(false);
const isMuted = ref(false);

const savePosition = () => {
  localStorage.setItem(
    "floating_player_state",
    JSON.stringify({
      position: position.value,
      size: size.value,
      aspectRatio: aspectRatio.value,
    }),
  );
};

const saveSize = () => {
  if (size.value.width > 0 && size.value.height > HEADER_HEIGHT) {
    aspectRatio.value = size.value.width / (size.value.height - HEADER_HEIGHT);
  }
  localStorage.setItem(
    "floating_player_state",
    JSON.stringify({
      position: position.value,
      size: size.value,
      aspectRatio: aspectRatio.value,
    }),
  );
};

onMounted(() => {
  window.addEventListener('resize', updateViewport);
  visualViewport?.addEventListener('resize', updateViewport);
  visualViewport?.addEventListener('scroll', updateViewport);
  document.addEventListener("fullscreenchange", handleFullscreenChange);
  window.addEventListener("message", handlePlayerMessage);

  const saved = localStorage.getItem("floating_player_state");
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      position.value = parsed.position || position.value;
      size.value = parsed.size || size.value;
      if (parsed.aspectRatio) {
        aspectRatio.value = parsed.aspectRatio;
      } else if (size.value.width > 0 && size.value.height > HEADER_HEIGHT) {
        aspectRatio.value =
          size.value.width / (size.value.height - HEADER_HEIGHT);
      }
    } catch {}
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', updateViewport);
  visualViewport?.removeEventListener('resize', updateViewport);
  visualViewport?.removeEventListener('scroll', updateViewport);
  if (isDragging.value) stopDrag();
  if (isResizing.value) stopResize();
  document.removeEventListener("fullscreenchange", handleFullscreenChange);
  window.removeEventListener("message", handlePlayerMessage);
});

watch(
  () => props.episode,
  () => {
    if (kodikIframe.value && props.playerLink) {
      const url = new URL(props.playerLink);
      url.searchParams.set("episode", String(props.episode));
      if (props.season) {
        url.searchParams.set("season", String(props.season));
      }
      kodikIframe.value.src = url.toString();
      needsSeek.value = false;
      playerReady.value = false;
    }
  },
);

watch(
  () => props.startTime,
  (newTime, oldTime) => {
    if (newTime > 0 && oldTime === 0 && !playerReady.value) {
      mainPlayerTimeAtOpen.value = newTime;
      currentTime.value = newTime;
      needsSeek.value = true;
    }

    if (
      newTime > 0 &&
      playerReady.value &&
      kodikIframe.value?.contentWindow &&
      newTime !== oldTime &&
      oldTime !== 0
    ) {
      sendMessage({
        key: "kodik_player_api",
        value: { method: "seek", seconds: newTime },
      });
    }
  },
);

watch(
  () => props.visible,
  (newVisible, oldVisible) => {
    console.log("[FloatingPlayer] Visible changed:", {
      new: newVisible,
      old: oldVisible,
      playerLink: props.playerLink,
    });
    if (newVisible && !oldVisible && newVisible) {
      mainPlayerTimeAtOpen.value = props.startTime || 0;
      currentTime.value = mainPlayerTimeAtOpen.value;
      needsSeek.value = true;
      console.log(
        "[FloatingPlayer] Player opened, position:",
        position.value,
        "size:",
        size.value,
      );
    }
  },
);
</script>

<style scoped>
.floating-player {
  position: fixed;
  background: #1a1a1a;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  transition:
    width 0.2s ease,
    height 0.2s ease;
  cursor: default;
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: calc(var(--z-sidebar) + 10);
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.floating-player.is-dragging {
  cursor: grabbing;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6);
}

.floating-player.is-resizing {
  cursor: se-resize;
}

.floating-player.minimized {
  cursor: pointer;
}

.fp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  user-select: none;
  -webkit-user-select: none;
  touch-action: none;
  z-index: 20;
  position: relative;
}

.fp-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.fp-title {
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fp-episode {
  color: #888;
  font-size: 11px;
}

.fp-controls {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.fp-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #888;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.fp-btn:active {
  transform: scale(0.9);
  opacity: 0.8;
}

.fp-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.fp-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.fp-btn-active {
  color: #4ade80 !important;
  background: rgba(74, 222, 128, 0.15);
}

.fp-content {
  display: flex;
  flex-direction: column;
  height: calc(100% - 42px);
  pointer-events: auto;
  -webkit-tap-highlight-color: transparent;
}

.fp-video-wrapper {
  flex: 1;
  background: #000;
  min-height: 0;
  position: relative;
  pointer-events: auto;
}

.kodik-iframe {
  width: 100%;
  height: 100%;
  border: none;
  pointer-events: auto;
  touch-action: manipulation;
  display: block;
  position: relative;
  z-index: 10;
}

.fp-no-video {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 13px;
}

.fp-minimized-content {
  padding: 0 12px;
  display: flex;
  align-items: center;
}

.fp-mini-title {
  color: #888;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fp-resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20px;
  height: 20px;
  cursor: se-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #555;
  opacity: 0.5;
  transition: opacity 0.15s;
  z-index: 10;
  touch-action: none;
  -webkit-tap-highlight-color: transparent;
}

.fp-resize-handle::after {
  content: "";
  position: absolute;
  bottom: 0;
  right: 0;
  width: 32px;
  height: 32px;
  z-index: -1;
}

.fp-resize-handle:hover {
  opacity: 1;
  color: #888;
}

.fp-resize-handle:active {
  opacity: 1;
  color: #4ade80;
}

.fp-resize-handle.fp-resize-hidden {
  display: none;
}

.float-enter-active,
.float-leave-active {
  transition: all 0.3s ease;
}

.float-enter-from,
.float-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

@media (max-width: 768px) {
  .floating-player:not(.is-fullscreen) {
    max-width: calc(100vw - 20px);
    touch-action: none;
  }

  .fp-header {
    padding: 8px 10px;
    min-height: 44px;
  }

  .fp-title {
    font-size: 13px;
  }

  .fp-episode {
    font-size: 11px;
  }

  .fp-controls {
    gap: 4px;
  }

  .fp-btn {
    width: 32px;
    height: 32px;
    min-width: 32px;
    min-height: 32px;
  }

  .fp-btn svg {
    width: 16px;
    height: 16px;
  }

  .fp-resize-handle {
    width: 28px;
    height: 28px;
  }
}

@media (max-width: 480px) {
  .fp-header {
    padding: 6px 8px;
  }

  .fp-btn {
    width: 34px;
    height: 34px;
    min-width: 34px;
    min-height: 34px;
  }

  .fp-btn svg {
    width: 18px;
    height: 18px;
  }
}
</style>
