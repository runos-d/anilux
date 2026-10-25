<template>
  <Teleport to="body">
    <div v-if="open" class="ice-overlay" @click.self="$emit('update:open', false)">
      <div class="ice-modal">
        <div class="ice-header">
          <div class="ice-header-text">
            <h2>{{ title }}</h2>
            <p class="ice-header-sub">Настройте область</p>
          </div>
          <button class="ice-close" @click="$emit('update:open', false)" aria-label="Закрыть">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div class="ice-body">
          <div class="ice-crop-stage">
            <div
              ref="cropArea"
              class="ice-crop-area"
              :class="`ice-crop-area--${shape}`"
              @mousedown.prevent="startDrag"
              @touchstart.prevent="startDrag"
            >
              <img
                v-if="currentImageUrl"
                class="ice-crop-image"
                :src="currentImageUrl"
                :style="imageStyle"
                draggable="false"
                alt=""
                @load="onImageLoad"
                @error="onImageError"
              />
              <div class="ice-mask" :class="`ice-mask--${shape}`"></div>
            </div>
          </div>

          <div class="ice-controls">
            <button
              class="ice-zoom-btn"
              @click="zoomBy(-0.1)"
              :disabled="zoom <= minZoom"
              aria-label="Уменьшить"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>

            <div class="ice-slider-wrap">
              <UiRangeSlider
                class="ice-slider-input"
                :min="minZoom"
                :max="maxZoom"
                step="0.01"
                :value="zoom"
                @input="onZoomChange"
              />
            </div>

            <button
              class="ice-zoom-btn"
              @click="zoomBy(0.1)"
              :disabled="zoom >= maxZoom"
              aria-label="Увеличить"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>

            <span class="ice-zoom-value">{{ Math.round(zoom * 100) }}%</span>
          </div>

          <div v-if="!hidePreview" class="ice-preview-row">
            <span class="ice-preview-label">Превью</span>
            <div
              class="ice-preview-box"
              :class="`ice-preview-box--${shape}`"
            >
              <img
                v-if="currentImageUrl && imageLoaded"
                :src="currentImageUrl"
                :style="imageStyle"
                alt=""
              />
            </div>
          </div>
        </div>

        <div class="ice-footer">
          <button class="ice-btn ice-btn-ghost" @click="resetPosition">
            Сбросить
          </button>
          <div class="ice-footer-spacer"></div>
          <button
            class="ice-btn ice-btn-primary"
            @click="handleSave"
            :disabled="saving || !imageLoaded"
          >
            {{ saving ? "Сохранение..." : "Сохранить" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from "vue";
import UiRangeSlider from "@/components/common/UiRangeSlider.vue";

interface Props {
  open: boolean;
  shape?: "circle" | "rect";
  title?: string;
  accept?: string;
  initialSrc?: string | null;
  initialFile?: File | null;
  initialX?: number;
  initialY?: number;
  hidePreview?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  shape: "circle",
  title: "Редактировать изображение",
  accept: "image/jpeg,image/png,image/webp",
  initialX: 50,
  initialY: 50,
  hidePreview: false,
});

const emit = defineEmits<{
  "update:open": [value: boolean];
  crop: [payload: { file?: File; blob?: Blob; x: number; y: number }];
  remove: [];
}>();

const previewUrl = ref<string>("");
const selectedFile = ref<File | null>(null);
const position = ref({ x: 50, y: 50 });
const zoom = ref(1);
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const startPosition = ref({ x: 0, y: 0 });
const saving = ref(false);
const cropArea = ref<HTMLElement | null>(null);
const imageNaturalSize = ref({ width: 0, height: 0 });
const imageLoaded = ref(false);

const MIN_ZOOM = 1;
const MAX_ZOOM = 3;
const minZoom = MIN_ZOOM;
const maxZoom = MAX_ZOOM;

let dragRect: DOMRect | null = null;
let toastShown = false;
let ownedPreviewUrl = "";

const currentImageUrl = computed(() => previewUrl.value || props.initialSrc || "");

const imageStyle = computed(() => {
  if (!imageNaturalSize.value.width || !imageNaturalSize.value.height) {
    return { opacity: 0 };
  }
  const containerW = props.shape === "circle" ? 1 : 16;
  const containerH = props.shape === "circle" ? 1 : 7;
  const naturalW = imageNaturalSize.value.width;
  const naturalH = imageNaturalSize.value.height;
  const coverScale = Math.max(containerW / naturalW, containerH / naturalH);
  const renderedW = naturalW * coverScale * zoom.value;
  const renderedH = naturalH * coverScale * zoom.value;
  const offsetX = -((position.value.x / 100) * (renderedW - containerW));
  const offsetY = -((position.value.y / 100) * (renderedH - containerH));
  return {
    width: `${(renderedW / containerW) * 100}%`,
    height: `${(renderedH / containerH) * 100}%`,
    left: `${(offsetX / containerW) * 100}%`,
    top: `${(offsetY / containerH) * 100}%`,
    opacity: 1,
  };
});

function loadImageSize(src: string) {
  if (!src) {
    imageNaturalSize.value = { width: 0, height: 0 };
    imageLoaded.value = false;
    return;
  }
  const img = new Image();
  img.onload = () => {
    imageNaturalSize.value = { width: img.naturalWidth, height: img.naturalHeight };
    imageLoaded.value = true;
  };
  img.onerror = () => {
    imageNaturalSize.value = { width: 0, height: 0 };
    imageLoaded.value = false;
  };
  img.src = src;
  if (img.complete && img.naturalWidth > 0) {
    imageNaturalSize.value = { width: img.naturalWidth, height: img.naturalHeight };
    imageLoaded.value = true;
  }
}

watch(
  currentImageUrl,
  (src) => {
    loadImageSize(src);
  },
  { immediate: true },
);

watch(
  [() => props.open, () => props.initialFile, () => props.initialSrc],
  ([isOpen, file, src]) => {
    if (isOpen) {
      releaseOwnedPreview();
      selectedFile.value = file || null;
      previewUrl.value = file ? createOwnedPreview(file) : src || "";
      position.value = { x: props.initialX, y: props.initialY };
      zoom.value = 1;
      imageLoaded.value = false;
    } else {
      reset();
    }
  },
  { immediate: true },
);

function createOwnedPreview(file: File) {
  ownedPreviewUrl = URL.createObjectURL(file);
  return ownedPreviewUrl;
}

function releaseOwnedPreview() {
  if (ownedPreviewUrl) URL.revokeObjectURL(ownedPreviewUrl);
  ownedPreviewUrl = "";
}

function reset() {
  releaseOwnedPreview();
  previewUrl.value = "";
  selectedFile.value = null;
  position.value = { x: 50, y: 50 };
  zoom.value = 1;
  saving.value = false;
  imageNaturalSize.value = { width: 0, height: 0 };
  imageLoaded.value = false;
  dragRect = null;
  toastShown = false;
}

function onImageLoad() {
  imageLoaded.value = true;
}

function onImageError() {
  imageLoaded.value = false;
  showToast("Не удалось загрузить изображение");
}

function onZoomChange(e: Event) {
  const v = parseFloat((e.target as HTMLInputElement).value);
  zoom.value = clamp(v, minZoom, maxZoom);
}

function zoomBy(delta: number) {
  zoom.value = clamp(zoom.value + delta, minZoom, maxZoom);
}

function clamp(v: number, min: number, max: number) {
  if (isNaN(v)) return min;
  return Math.max(min, Math.min(max, v));
}

function startDrag(event: MouseEvent | TouchEvent) {
  if (!currentImageUrl.value || !cropArea.value || !imageLoaded.value) return;
  isDragging.value = true;
  const clientX = "touches" in event ? event.touches[0]?.clientX ?? 0 : event.clientX;
  const clientY = "touches" in event ? event.touches[0]?.clientY ?? 0 : event.clientY;
  dragStart.value = { x: clientX, y: clientY };
  startPosition.value = { ...position.value };
  dragRect = cropArea.value.getBoundingClientRect();
  document.addEventListener("mousemove", onDrag);
  document.addEventListener("mouseup", stopDrag);
  document.addEventListener("touchmove", onDrag, { passive: false });
  document.addEventListener("touchend", stopDrag);
  document.addEventListener("touchcancel", stopDrag);
  document.addEventListener("pointercancel", stopDrag);
}

function onDrag(event: MouseEvent | TouchEvent) {
  if (!isDragging.value || !dragRect) return;
  const clientX = "touches" in event ? event.touches[0]?.clientX ?? 0 : event.clientX;
  const clientY = "touches" in event ? event.touches[0]?.clientY ?? 0 : event.clientY;
  const deltaX = clientX - dragStart.value.x;
  const deltaY = clientY - dragStart.value.y;

  const containerW = dragRect.width;
  const containerH = dragRect.height;
  const naturalW = imageNaturalSize.value.width;
  const naturalH = imageNaturalSize.value.height;

  if (naturalW <= 0 || naturalH <= 0) return;

  const coverScale = Math.max(containerW / naturalW, containerH / naturalH);
  const renderedW = naturalW * coverScale * zoom.value;
  const renderedH = naturalH * coverScale * zoom.value;

  const rangeX = Math.max(0, renderedW - containerW);
  const rangeY = Math.max(0, renderedH - containerH);

  let newX = startPosition.value.x;
  let newY = startPosition.value.y;

  if (rangeX > 0) {
    const currentPixelX = (startPosition.value.x / 100) * rangeX;
    const newPixelX = currentPixelX - deltaX;
    newX = Math.max(0, Math.min(100, (newPixelX / rangeX) * 100));
  } else {
    newX = 50;
  }

  if (rangeY > 0) {
    const currentPixelY = (startPosition.value.y / 100) * rangeY;
    const newPixelY = currentPixelY - deltaY;
    newY = Math.max(0, Math.min(100, (newPixelY / rangeY) * 100));
  } else {
    newY = 50;
  }

  position.value = { x: newX, y: newY };
  dragStart.value = { x: clientX, y: clientY };
  startPosition.value = { ...position.value };
}

function stopDrag() {
  isDragging.value = false;
  document.removeEventListener("mousemove", onDrag);
  document.removeEventListener("mouseup", stopDrag);
  document.removeEventListener("touchmove", onDrag);
  document.removeEventListener("touchend", stopDrag);
  document.removeEventListener("touchcancel", stopDrag);
  document.removeEventListener("pointercancel", stopDrag);
}

function resetPosition() {
  position.value = { x: 50, y: 50 };
  zoom.value = 1;
}

async function handleSave() {
  if (!imageLoaded.value) return;
  const src = currentImageUrl.value;
  if (!src) return;

  saving.value = true;
  try {
    const blob = await createCroppedBlob();
    const sourceName = selectedFile.value?.name.replace(/\.[^.]+$/, "") || `crop-${Date.now()}`;
    const fileName = `${sourceName}.jpg`;
    const file = new File([blob], fileName, { type: "image/jpeg" });
    emit("crop", {
      file,
      blob,
      x: Number(position.value.x.toFixed(2)),
      y: Number(position.value.y.toFixed(2)),
    });
  } catch (e) {
    console.error("Crop error:", e);
    showToast("Не удалось обработать изображение");
  } finally {
    saving.value = false;
  }
}

function createCroppedBlob(): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const src = currentImageUrl.value;
    if (!src) {
      reject(new Error("No image"));
      return;
    }

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      try {
        const OUT_W = props.shape === "circle" ? 512 : 1600;
        const OUT_H = props.shape === "circle" ? 512 : Math.round(1600 / (16 / 7));

        const containerW = OUT_W;
        const containerH = OUT_H;

        const naturalW = img.naturalWidth;
        const naturalH = img.naturalHeight;

        const coverScale = Math.max(containerW / naturalW, containerH / naturalH);
        const renderedW = naturalW * coverScale * zoom.value;
        const renderedH = naturalH * coverScale * zoom.value;

        const offsetX = -((position.value.x / 100) * (renderedW - containerW));
        const offsetY = -((position.value.y / 100) * (renderedH - containerH));

        const drawW = renderedW;
        const drawH = renderedH;

        const canvas = document.createElement("canvas");
        canvas.width = OUT_W;
        canvas.height = OUT_H;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          reject(new Error("No canvas context"));
          return;
        }

        ctx.fillStyle = "#000";
        ctx.fillRect(0, 0, OUT_W, OUT_H);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";

        ctx.drawImage(
          img,
          0,
          0,
          naturalW,
          naturalH,
          offsetX,
          offsetY,
          drawW,
          drawH,
        );

        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error("toBlob failed"));
              return;
            }
            resolve(blob);
          },
          "image/jpeg",
          0.92,
        );
      } catch (e) {
        reject(e);
      }
    };
    img.onerror = () => reject(new Error("Image load failed"));
    img.src = src;
  });
}

function showToast(message: string) {
  if (toastShown) return;
  toastShown = true;
  window.setTimeout(() => {
    toastShown = false;
  }, 500);
  const el = document.createElement("div");
  el.textContent = message;
  el.style.cssText =
    "position:fixed;top:24px;left:50%;transform:translateX(-50%);z-index:100000;" +
    "padding:10px 18px;border-radius:10px;background:#ef4444;color:#fff;" +
    "font:600 13px/1.4 system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,0.4);";
  document.body.appendChild(el);
  window.setTimeout(() => {
    el.style.transition = "opacity 0.25s";
    el.style.opacity = "0";
    window.setTimeout(() => el.remove(), 260);
  }, 2400);
}

onBeforeUnmount(() => {
  stopDrag();
  releaseOwnedPreview();
});
</script>

<style scoped>
.ice-overlay {
  position: fixed;
  inset: 0;
  background: rgba(6, 8, 12, 0.68);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  animation: iceFade 0.18s ease;
}

@keyframes iceFade {
  from { opacity: 0; }
  to { opacity: 1; }
}

.ice-modal {
  background: var(--surface-2);
  border-radius: 20px;
  width: 100%;
  max-width: 500px;
  max-height: 92vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-default);
  box-shadow:
    0 25px 60px -12px rgba(0, 0, 0, 0.7),
    0 0 0 1px rgba(255, 255, 255, 0.03);
  animation: iceScale 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes iceScale {
  from { opacity: 0; transform: scale(0.97); }
  to { opacity: 1; transform: none; }
}

.ice-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px 16px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  gap: 12px;
}
.ice-header-text {
  min-width: 0;
}
.ice-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}
.ice-header-sub {
  margin: 3px 0 0;
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.4;
}
.ice-close {
  flex-shrink: 0;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.ice-close:hover {
  background: var(--surface-5);
  color: var(--text-primary);
  border-color: var(--border-default);
}

.ice-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.ice-crop-stage {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4px 0 8px;
}

.ice-crop-area {
  position: relative;
  width: 100%;
  max-width: 100%;
  background: color-mix(in srgb, var(--surface-4) 88%, var(--accent));
  border: 1px solid var(--border-default);
  overflow: hidden;
  cursor: grab;
  user-select: none;
  -webkit-user-select: none;
  touch-action: none;
}
.ice-crop-area:active {
  cursor: grabbing;
}
.ice-crop-area--circle {
  aspect-ratio: 1 / 1;
  max-width: 340px;
  border-radius: 50%;
}
.ice-crop-area--rect {
  aspect-ratio: 16 / 7;
  max-width: 460px;
  border-radius: 14px;
}

.ice-crop-image {
  position: absolute;
  max-width: none;
  object-fit: fill;
  pointer-events: none;
  transition: opacity 0.2s ease;
  will-change: left, top, width, height;
}

.ice-mask {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.ice-mask--circle {
  border: 2px solid color-mix(in srgb, var(--accent) 76%, white);
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.24);
}
.ice-mask--rect {
  border: 2px solid color-mix(in srgb, var(--accent) 76%, white);
  border-radius: 14px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.24);
}

.ice-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 8px 12px;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
}

.ice-zoom-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-4);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s, transform 0.1s;
}
.ice-zoom-btn:hover:not(:disabled) {
  background: var(--surface-5);
  color: var(--text-primary);
  border-color: var(--border-default);
}
.ice-zoom-btn:active:not(:disabled) {
  transform: scale(0.94);
}
.ice-zoom-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ice-slider-wrap {
  position: relative;
  flex: 1;
  height: 20px;
  display: flex;
  align-items: center;
}

.ice-slider-input {
  position: relative;
  width: 100%;
  height: 20px;
  margin: 0;
  background: transparent;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  z-index: 2;
  outline: none;
}
.ice-slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: transparent;
  border: none;
  cursor: grab;
}
.ice-slider-input::-webkit-slider-thumb:active {
  cursor: grabbing;
}
.ice-slider-input::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: transparent;
  border: none;
  cursor: grab;
}
.ice-slider-input::-moz-range-track {
  background: transparent;
}

.ice-zoom-value {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 46px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.ice-preview-row {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
}
.ice-preview-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.ice-preview-box {
  position: relative;
  background: var(--surface-1);
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  margin-left: auto;
}
.ice-preview-box img {
  position: absolute;
  max-width: none;
  object-fit: fill;
  pointer-events: none;
}
.ice-preview-box--circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
}
.ice-preview-box--rect {
  width: 160px;
  height: 70px;
  border-radius: 10px;
}

.ice-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
  flex-wrap: wrap;
}
.ice-footer-spacer {
  flex: 1;
}
.ice-btn {
  padding: 9px 16px;
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s, border-color 0.15s, color 0.15s, opacity 0.15s, transform 0.1s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  white-space: nowrap;
}
.ice-btn:active:not(:disabled) {
  transform: scale(0.98);
}
.ice-btn-primary {
  background: var(--accent);
  color: #fff;
}
.ice-btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}
.ice-btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--border-subtle);
}
.ice-btn-ghost:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: var(--border-default);
  background: var(--surface-4);
}
.ice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .ice-overlay {
    padding: 12px;
  }
  .ice-modal {
    max-height: 96vh;
    border-radius: 16px;
  }
  .ice-body {
    padding: 16px;
  }
  .ice-header {
    padding: 14px 16px 12px;
  }
  .ice-crop-area--circle {
    max-width: 100%;
  }
  .ice-crop-area--rect {
    max-width: 100%;
  }
  .ice-footer {
    padding: 12px 14px;
    gap: 6px;
  }
  .ice-btn {
    padding: 9px 14px;
    font-size: 13px;
  }
  .ice-preview-box--rect {
    width: 110px;
    height: 48px;
  }
  .ice-controls {
    gap: 8px;
    padding: 6px 10px;
  }
  .ice-zoom-btn {
    width: 30px;
    height: 30px;
  }
  .ice-zoom-value {
    min-width: 42px;
    font-size: 11.5px;
  }
}

@media (max-width: 420px) {
  .ice-footer .ice-btn-ghost {
    padding: 8px 12px;
    font-size: 12.5px;
  }
  .ice-preview-row {
    padding: 8px 10px;
  }
  .ice-preview-box--rect {
    width: 90px;
    height: 40px;
  }
}
</style>
