<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="carousel-section">
    <div class="carousel-header">
      <h2 class="carousel-title">{{ title }}</h2>
      <button v-if="showViewAll" class="view-all-btn" @click="handleViewAll">
        Все
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M9 18l6-6-6-6" />
        </svg>
      </button>
    </div>

    <div class="carousel-container" ref="carouselRef">
      <button
        v-if="showLeftArrow"
        class="carousel-arrow carousel-arrow-left"
        @click="scrollLeft"
        :disabled="isAtStart"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M15 18l-6-6 6-6" />
        </svg>
      </button>

      <div
        class="carousel-track"
        ref="trackRef"
        :class="{ 'is-dragging': isDragging }"
      >
        <template v-if="loading">
          <div
            v-for="n in skeletonCount"
            :key="'skeleton-' + n"
            class="carousel-card skeleton"
          >
            <div class="skeleton-poster"></div>
            <div class="skeleton-info">
              <div class="skeleton-title"></div>
              <div class="skeleton-meta"></div>
            </div>
          </div>
        </template>

        <template v-else-if="error">
          <div class="carousel-error">
            <p>{{ errorMessage }}</p>
            <button class="retry-btn" @click="$emit('retry')">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M23 4v6h-6M1 20v-6h6" />
                <path
                  d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"
                />
              </svg>
              Повторить
            </button>
          </div>
        </template>

        <template v-else-if="isEmpty && hideOnEmpty">
        </template>

        <template v-else-if="isEmpty && !hideOnEmpty">
          <div class="carousel-empty">
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <rect x="2" y="2" width="20" height="20" rx="2" />
              <path d="M12 2v20M2 12h20" />
            </svg>
            <p>{{ emptyMessage }}</p>
          </div>
        </template>

        <template v-else>
          <slot></slot>
        </template>
      </div>

      <button
        v-if="showRightArrow"
        class="carousel-arrow carousel-arrow-right"
        @click="scrollRight"
        :disabled="isAtEnd"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M9 18l6-6-6-6" />
        </svg>
      </button>
    </div>

    <div v-if="showDots" class="carousel-dots">
      <button
        v-for="n in totalDots"
        :key="'dot-' + n"
        class="carousel-dot"
        :class="{ active: currentPage === n - 1 }"
        @click="scrollToPage(n - 1)"
      ></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";

interface Props {
  title: string;
  loading?: boolean;
  error?: boolean;
  errorMessage?: string;
  emptyMessage?: string;
  hideOnEmpty?: boolean;
  showViewAll?: boolean;
  viewAllLink?: string;
  itemsCount?: number;
  scrollStep?: number;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: false,
  errorMessage: "Не удалось загрузить контент",
  emptyMessage: "Пусто",
  hideOnEmpty: true,
  showViewAll: false,
  itemsCount: 0,
  scrollStep: 4,
});

const emit = defineEmits<{
  retry: [];
  "view-all": [];
}>();

const carouselRef = ref<HTMLElement | null>(null);
const trackRef = ref<HTMLElement | null>(null);
const isAtStart = ref(true);
const isAtEnd = ref(false);
const currentPage = ref(0);
const containerWidth = ref(0);

const isDragging = ref(false);
const startX = ref(0);
const scrollLeftStart = ref(0);

const cardWidth = 236;
const skeletonCount = computed(() => Math.min(props.itemsCount || 5, 5));

const showLeftArrow = computed(
  () => !props.loading && !props.error && !isAtStart.value,
);
const showRightArrow = computed(
  () => !props.loading && !props.error && !isAtEnd.value,
);
const showDots = computed(() => false);
const totalDots = computed(() =>
  Math.ceil(props.itemsCount / props.scrollStep),
);

const isEmpty = computed(() => props.itemsCount === 0);

const checkScrollPosition = () => {
  if (!trackRef.value || !carouselRef.value) return;

  const track = trackRef.value;
  const container = carouselRef.value;

  containerWidth.value = container.clientWidth;

  isAtStart.value = track.scrollLeft <= 0;
  isAtEnd.value =
    track.scrollLeft + track.clientWidth >= track.scrollWidth - 10;

  currentPage.value = Math.round(
    track.scrollLeft / (cardWidth * props.scrollStep),
  );
};

const handleMouseDown = (e: MouseEvent) => {
  if (e.button !== 0 && e.button !== 2) return;

  isDragging.value = true;
  startX.value = e.pageX;

  if (trackRef.value) {
    scrollLeftStart.value = trackRef.value.scrollLeft;
  }

  e.preventDefault();
};

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value || !trackRef.value) return;

  const x = e.pageX;
  const walk = (startX.value - x) * 1.5;
  trackRef.value.scrollLeft = scrollLeftStart.value + walk;
};

const handleMouseUp = () => {
  isDragging.value = false;
};

const handleContextMenu = (e: MouseEvent) => {
  e.preventDefault();
};

const scrollLeft = () => {
  if (!trackRef.value) return;
  trackRef.value.scrollBy({
    left: -(cardWidth * props.scrollStep),
    behavior: "smooth",
  });
};

const scrollRight = () => {
  if (!trackRef.value) return;
  trackRef.value.scrollBy({
    left: cardWidth * props.scrollStep,
    behavior: "smooth",
  });
};

const scrollToPage = (page: number) => {
  if (!trackRef.value) return;
  trackRef.value.scrollTo({
    left: page * cardWidth * props.scrollStep,
    behavior: "smooth",
  });
};

const handleViewAll = () => {
  if (props.viewAllLink) {
    window.location.href = props.viewAllLink;
  } else {
    emit("view-all");
  }
};

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  if (trackRef.value) {
    trackRef.value.addEventListener("scroll", checkScrollPosition);

    trackRef.value.addEventListener("mousedown", handleMouseDown);
    trackRef.value.addEventListener("contextmenu", handleContextMenu);

    checkScrollPosition();

    resizeObserver = new ResizeObserver(checkScrollPosition);
    if (carouselRef.value) {
      resizeObserver.observe(carouselRef.value);
    }
  }

  document.addEventListener("mousemove", handleMouseMove);
  document.addEventListener("mouseup", handleMouseUp);
});

onUnmounted(() => {
  if (trackRef.value) {
    trackRef.value.removeEventListener("scroll", checkScrollPosition);
    trackRef.value.removeEventListener("mousedown", handleMouseDown);
    trackRef.value.removeEventListener("contextmenu", handleContextMenu);
  }
  if (resizeObserver) {
    resizeObserver.disconnect();
  }

  document.removeEventListener("mousemove", handleMouseMove);
  document.removeEventListener("mouseup", handleMouseUp);
});

watch(
  () => props.itemsCount,
  () => {
    setTimeout(checkScrollPosition, 100);
  },
);
</script>

<style scoped>
.carousel-section {
  margin-bottom: 32px;
  overflow: visible;
}

.carousel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0px;
  padding: 0 10px;
}

.carousel-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary, #fff);
  margin: 0;
}

.view-all-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--accent, #3a86ff);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px 12px;
  transition: background-color 0.2s;
}

.view-all-btn:hover {
  background-color: rgba(58, 134, 255, 0.1);
}

.carousel-container {
  position: relative;
  overflow: visible;
  box-sizing: border-box;
  padding-inline: 24px;
}

.carousel-track {
  position: relative;
  z-index: 3;
  display: flex;
  gap: 16px;
  overflow-x: auto;
  scroll-behavior: smooth;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding: 4px;
  cursor: grab;
  user-select: none;
}

.carousel-container.is-dragging {
  cursor: grabbing;
}

.carousel-container.is-dragging * {
  cursor: grab !important;
}

.carousel-track:active {
  cursor: grabbing;
}

.carousel-track.is-dragging {
  cursor: grabbing;
  scroll-behavior: auto;
}

.carousel-track::-webkit-scrollbar {
  display: none;
}

.carousel-card {
  flex: 0 0 220px;
  width: 220px;
  cursor: pointer;
  transition: transform 0.2s;
}

.carousel-card:hover {
  transform: translateY(-4px);
}

.carousel-card.skeleton {
  pointer-events: none;
}

.skeleton-poster {
  width: 100%;
  aspect-ratio: 2 / 3;
  background: linear-gradient(
    90deg,
    var(--surface-4) 25%,
    var(--surface-5) 50%,
    var(--surface-4) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 12px;
}

.skeleton-info {
  padding: 8px 0;
}

.skeleton-title {
  height: 16px;
  width: 80%;
  background: linear-gradient(90deg, #2a2a2a 25%, #3a3a3a 50%, #2a2a2a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-meta {
  height: 12px;
  width: 60%;
  background: linear-gradient(90deg, #2a2a2a 25%, #3a3a3a 50%, #2a2a2a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.carousel-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-secondary, #aaa);
}

.carousel-error p {
  margin: 0 0 16px 0;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: var(--accent, #3a86ff);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background-color: #2d7af7;
}

.carousel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  color: var(--text-secondary, #666);
  min-height: 240px;
}

.carousel-empty svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.carousel-empty p {
  margin: 0;
  font-size: 14px;
  text-align: center;
}

.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(12, 12, 15, 0.85);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  pointer-events: auto;
  opacity: 0;
  transition:
    opacity 0.2s,
    background-color 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.carousel-container:hover .carousel-arrow {
  opacity: 1;
}

.carousel-arrow:hover:not(:disabled) {
  background-color: var(--accent, #3a86ff);
}

.carousel-arrow:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.carousel-arrow-left {
  left: 2px !important;
}

.carousel-arrow-right {
  right: 2px !important;
}

.carousel-dots {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 6px 4px;
  background: var(--surface-1);
}

.carousel-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: var(--text-tertiary, #666);
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.carousel-dot.active {
  width: 28px;
  border-radius: 12px;
  background-color: var(--accent, #3a86ff);
}

@media (max-width: 767px) {
  .carousel-card {
    flex: 0 0 155px;
    width: 155px;
  }

  .skeleton-poster {
    aspect-ratio: 2 / 3;
    border-radius: 12px;
  }

  .carousel-arrow {
    display: none;
  }
}
</style>
