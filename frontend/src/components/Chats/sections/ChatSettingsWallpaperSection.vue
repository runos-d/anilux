<template>
  <section class="settings-section">
    <div class="section-header">
      <h2><SakuraIcon name="image" /> Обои чата</h2>
      <button v-if="hasCustom" @click="$emit('reset')" class="btn-ghost-sm">
        Сбросить
      </button>
    </div>

    <div class="wp-preview-wrapper">
      <div class="wp-preview-scale">
        <div class="chat-detail" :style="chatDetailStyle">
          <div class="chat-wallpaper" :style="bgLayerStyle" aria-hidden="true"></div>

          <div class="messages-wrap">
            <div class="messages">
              <div class="messages-list">
                <div class="message message--other">
                  <div class="message-body">
                    <div class="message-text">
                      Привет! Как дела?
                      <span class="meta-float"><span class="mm">12:30</span></span>
                    </div>
                  </div>
                </div>
                <div class="message message--own">
                  <div class="message-body">
                    <div class="message-text">
                      Нормально, смотрю аниме
                      <span class="meta-float"><span class="mm">12:31</span></span>
                    </div>
                  </div>
                </div>
                <ChatPreviewCards :anime-radius="animeCardBorderRadius" :playlist-radius="playlistCardBorderRadius" :mine-style="mineBubbleStyle" :other-style="otherBubbleStyle" />
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>

    <div class="wp-sidebar">
      <div class="wp-sidebar-title">Коррекция фона</div>
      <div class="wp-control">
        <div class="wp-control-header">
          <SakuraIcon name="eye-off" class="wp-control-icon" />
          <label class="wp-control-label">Размытие</label>
          <span class="wp-control-value">{{ wallpaperBlur }}px</span>
        </div>
        <UiRangeSlider
          v-model.number="wallpaperBlur"
          min="0"
          max="20"
          class="wp-range"
          :style="{
            '--slider-progress': ((wallpaperBlur - 0) / (20 - 0) * 100) + '%'
          }"
        />
      </div>
      <div class="wp-control">
        <div class="wp-control-header">
          <SakuraIcon name="sun" class="wp-control-icon" />
          <label class="wp-control-label">Яркость</label>
          <span class="wp-control-value">{{ wallpaperIntensity }}%</span>
        </div>
        <UiRangeSlider
          v-model.number="wallpaperIntensity"
          min="20"
          max="100"
          class="wp-range"
          :style="{
            '--slider-progress': ((wallpaperIntensity - 20) / (100 - 20) * 100) + '%'
          }"
        />
      </div>
    </div>

    <div class="field-group">
      <div class="wp-type-pills">
        <button
          v-for="wt in typeOptions"
          :key="wt.value"
          type="button"
          @click="wallpaperType = wt.value"
          class="wp-type-pill"
          :class="{ active: wallpaperType === wt.value }"
        >
          {{ wt.label }}
        </button>
      </div>
    </div>

    <div
      v-if="wallpaperType !== 'image'"
      class="settings-group-card wp-card-compact"
    >
      <div class="sgc-title">Цвет фона</div>
      <div class="color-row">
        <div class="color-picker-wrap">
          <div class="color-preview" :style="{ backgroundColor: wallpaperColor }"></div>
          <input
            type="color"
            v-model="wallpaperColor"
            class="color-input"
          />
        </div>
        <input
          type="text"
          v-model="wallpaperColor"
          class="color-hex-input"
          placeholder="#1a1a2e"
        />
      </div>
    </div>

    <div v-else class="settings-group-card wp-card-compact">
      <div class="sgc-title">Картинка</div>
      <div
        class="upload-zone"
        @click="fileInput?.click()"
        @dragover.prevent
        @dragenter.prevent
        @drop.prevent="onDrop"
      >
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          @change="onFileChange"
          style="display: none"
        />
        <div v-if="imagePreview" class="upload-preview">
          <img :src="imagePreview" class="upload-preview-img" />
          <button @click.stop="$emit('file-clear')" class="clear-btn" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button>
        </div>
        <div v-else class="upload-placeholder">
          <div class="upload-icon-big">
            <SakuraIcon name="image" />
          </div>
          <p class="upload-main-text">Нажмите или перетащите файл</p>
          <p class="upload-hint">JPG, PNG, WEBP -максимум 5MB</p>
        </div>
      </div>
    </div>

    <div class="section-actions">
      <button
        @click="$emit('save')"
        class="btn-primary"
        :disabled="saving"
      >
        <span v-if="saving" class="btn-spinner"></span>
        <template v-if="saving">Сохранение...</template>
        <template v-else>
          <SakuraIcon name="save" />
          Сохранить обои
        </template>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import ChatPreviewCards from "../ChatPreviewCards.vue";
import UiRangeSlider from "@/components/common/UiRangeSlider.vue";
import { ref, computed } from "vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { getMediaUrl } from "@/api/client";

interface WallpaperForm {
  wallpaper_type?: string;
  wallpaper_color?: string;
  wallpaper_color2?: string;
  gradient_angle?: number;
  wallpaper_blur?: number;
  wallpaper_intensity?: number;
  pattern_type?: string;
  pattern_color?: string;
  pattern_opacity?: number;
  wallpaper_image_url?: string | null;
}

const props = defineProps<{
  form: WallpaperForm;
  chatName?: string;
  imagePreview: string | null;
  hasCustom: boolean;
  saving: boolean;
  solidColorPresets: string[];
  typeOptions: { value: string; label: string }[];
  animeCardBorderRadius: number;
  playlistCardBorderRadius: number;
  mineBubbleStyle: Record<string, string>;
  otherBubbleStyle: Record<string, string>;
}>();

const emit = defineEmits<{
  save: [];
  reset: [];
  "file-change": [file: File];
  "file-clear": [];
  "update:wallpaper-blur": [value: number];
  "update:wallpaper-intensity": [value: number];
  "update:wallpaper-type": [value: string];
  "update:wallpaper-color": [value: string];
}>();

const fileInput = ref<HTMLInputElement | null>(null);

const wallpaperBlur = computed({
  get: () => props.form.wallpaper_blur ?? 0,
  set: (value) => emit("update:wallpaper-blur", value),
});

const wallpaperIntensity = computed({
  get: () => props.form.wallpaper_intensity ?? 100,
  set: (value) => emit("update:wallpaper-intensity", value),
});

const wallpaperType = computed({
  get: () => props.form.wallpaper_type ?? "solid",
  set: (value) => emit("update:wallpaper-type", value),
});

const wallpaperColor = computed({
  get: () => props.form.wallpaper_color ?? "#0f0f1a",
  set: (value) => emit("update:wallpaper-color", value),
});

const chatDetailStyle = computed(() => ({
  "--bubble-mine-bg": props.mineBubbleStyle.background,
  "--bubble-mine-text": props.mineBubbleStyle.color,
  "--bubble-other-bg": props.otherBubbleStyle.background,
  "--bubble-other-text": props.otherBubbleStyle.color,
  "--bubble-radius": props.mineBubbleStyle.borderRadius,
  "--bubble-shadow": props.mineBubbleStyle.boxShadow ?? "none",
}));

const bgLayerStyle = computed(() => {
if (wallpaperType.value === "image") {
  const saved =
    props.form.wallpaper_image_url != null
      ? getMediaUrl(props.form.wallpaper_image_url)
      : undefined;
  const src = props.imagePreview || saved;
  if (!src) {
    return { backgroundColor: wallpaperColor.value || "#0f0f1a" };
  }
  return {
    backgroundImage: `url("${src}")`,
    backgroundColor: wallpaperColor.value || "#0f0f1a",
    filter: `blur(${Number(wallpaperBlur.value ?? 0)}px) brightness(${Number(wallpaperIntensity.value ?? 100) / 100})`,
  };
}
  return { backgroundColor: wallpaperColor.value || "#0f0f1a" };
});

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) emit("file-change", file);
}

function onDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0];
  if (file?.type.startsWith("image/")) emit("file-change", file);
}
</script>

<style scoped>
.settings-section {
  padding: var(--space-6);
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}
.section-header h2 {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.wp-preview-wrapper {
  margin-bottom: var(--space-5);
  overflow: hidden;
}

.wp-preview-scale {
  transform: scale(0.78);
  transform-origin: top left;
  width: 128%;
  margin-bottom: -92px;
  pointer-events: none;
}

.wp-preview-scale .chat-detail {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface-1);
  min-height: 0;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-subtle);
  height: 420px;
}

.wp-sidebar {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.wp-sidebar-title {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--border-subtle);
}

.wp-control {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.wp-control-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.wp-control-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.wp-control-label {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}
.wp-control-value {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  min-width: 3.2rem;
  text-align: right;
}
.wp-range {
  width: 100%;
  height: 20px;
  accent-color: var(--accent);
  cursor: pointer;
  padding: 0;
  margin: 0;
  background: transparent;
}
.wp-range:focus {
  outline: none !important;
  border: none !important;
  box-shadow: none !important;
}

.wp-range::-webkit-slider-runnable-track:focus {
  outline: none !important;
}

.wp-range::-moz-range-track:focus {
  outline: none !important;
}
.wp-range::-webkit-slider-runnable-track {
  width: 100%;
  height: 10px;
  border-radius: var(--radius-full);
  background: linear-gradient(
    to right,
    var(--accent) 0%,
    var(--accent) var(--slider-progress, 50%),
    var(--surface-4) var(--slider-progress, 50%),
    var(--surface-4) 100%
  );
}

.wp-range::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid var(--surface-1);
  cursor: pointer;
  margin-top: -4px;
  box-shadow: var(--shadow-sm-md);
  transition: transform 0.15s;
}
.wp-range::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}
.wp-range::-moz-range-track {
  width: 100%;
  height: 6px;
  border-radius: var(--radius-full);
  background: linear-gradient(
    to right,
    var(--accent) 0%,
    var(--accent) var(--slider-progress, 50%),
    var(--surface-4) var(--slider-progress, 50%),
    var(--surface-4) 100%
  );
}
.wp-range::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid var(--surface-1);
  cursor: pointer;
  box-shadow: var(--shadow-sm-md);
}

.field-group {
  margin-bottom: var(--space-4);
}
.field-group:last-child {
  margin-bottom: 0;
}
.wp-type-pills {
  display: flex;
  gap: var(--space-2);
}
.wp-type-pill {
  flex: 1;
  padding: var(--space-2) var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.wp-type-pill:hover {
  border-color: var(--accent);
  color: var(--text-primary);
  background: var(--surface-5);
}
.wp-type-pill.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
  box-shadow: var(--shadow-sm-glow-sm);
}

.settings-group-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  margin-bottom: var(--space-4);
  transition: border-color var(--duration-base) var(--ease-out);
}
.settings-group-card:hover {
  border-color: var(--border-default);
}
.sgc-title {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  margin-bottom: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.wp-card-compact {
  padding: var(--space-3);
}
.wp-card-compact .sgc-title {
  margin-bottom: var(--space-2);
}

.color-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.color-picker-wrap {
  position: relative;
  width: 30px;
  height: 30px;
  min-width: 30px;
  min-height: 30px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
  border: 1px solid var(--border-default);
  transition: all var(--duration-base) var(--ease-out);
}
.color-picker-wrap:hover {
  border-color: var(--accent);
  transform: scale(1.05);
}
.color-preview {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  pointer-events: none;
}
.color-input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  border: none;
  padding: 0;
  margin: 0;
}
.color-hex-input {
  flex: 1;
  min-width: 0;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 6px var(--space-2);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  transition: all var(--duration-base) var(--ease-out);
}
.color-hex-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.upload-zone {
  border: 2px dashed var(--border-default);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  overflow: hidden;
  min-height: 130px;
  position: relative;
}
.upload-zone:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
}
.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
  gap: var(--space-2);
  color: var(--text-tertiary);
}
.upload-icon-big {
  font-size: var(--text-3xl);
  opacity: 0.8;
}
.upload-main-text {
  font-size: var(--text-base);
  color: var(--text-secondary);
  font-weight: 500;
  margin: 0;
}
.upload-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
}
.upload-preview {
  position: relative;
}
.upload-preview-img {
  width: 100%;
  max-height: 180px;
  object-fit: cover;
  display: block;
  border-radius: var(--radius-lg);
}
.clear-btn {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: white;
  border-radius: var(--radius-full);
  width: 28px;
  height: 28px;
  min-width: 28px;
  min-height: 28px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  transition: all var(--duration-base) var(--ease-out);
}
.clear-btn:hover {
  background: var(--danger);
  border-color: var(--danger);
  transform: scale(1.1);
}

.section-actions {
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-subtle);
}
.btn-primary {
  padding: var(--space-2) var(--space-6);
  background: var(--accent);
  border: none;
  color: var(--text-on-accent);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-petal-sm);
  letter-spacing: 0.01em;
}
.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-petal);
}
.btn-primary:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
  background: var(--accent-press);
}
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}
.btn-primary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-ghost-sm {
  padding: var(--space-1) var(--space-3);
  background: none;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.btn-ghost-sm:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}

.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: var(--radius-full);
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 860px) {
  .wp-preview-scale {
    transform: scale(0.72);
    width: 139%;
    margin-bottom: -130px;
  }
  .wp-sidebar {
    flex-direction: row;
    flex-wrap: wrap;
    gap: var(--space-3);
  }
  .wp-control {
    flex: 1;
    min-width: 140px;
  }
}

@media (max-width: 640px) {
  .settings-section {
    padding: var(--space-4);
  }
  .wp-preview-scale {
    transform: scale(0.62);
    width: 161%;
    margin-bottom: -160px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .settings-section,
  .wp-type-pill,
  .swatch-dot,
  .color-dot,
  .btn-primary,
  .clear-btn,
  .upload-zone,
  .chat-wallpaper {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

.wp-preview-scale .chat-detail .chat-wallpaper {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    background-size: cover;
    background-position: center;
}

.wp-preview-scale .chat-detail .chat-header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.65rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-2);
  flex-shrink: 0;
}

.wp-preview-scale .chat-detail .header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.wp-preview-scale .chat-detail .avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.wp-preview-scale .chat-detail .avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-default);
}

.wp-preview-scale .chat-detail .online-dot {
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--success);
  border: 2px solid var(--surface-2);
}

.wp-preview-scale .chat-detail .header-info {
  min-width: 0;
}

.wp-preview-scale .chat-detail .chat-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wp-preview-scale .chat-detail .chat-status {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin: 0.15rem 0 0;
}
.wp-preview-scale .chat-detail .chat-status .online {
  color: var(--success);
}

.wp-preview-scale .chat-detail .header-actions {
  display: flex;
  gap: 0.25rem;
}

.wp-preview-scale .chat-detail .action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.wp-preview-scale .chat-detail .action-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}
.wp-preview-scale .chat-detail .action-btn svg {
  width: 18px;
  height: 18px;
}

.wp-preview-scale .chat-detail .messages-wrap {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.wp-preview-scale .chat-detail .messages {
  position: relative;
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.4rem 1.25rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-height: 0;
}

.wp-preview-scale .chat-detail .messages-list {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
  gap: 0.875rem;
}

.wp-preview-scale .chat-detail .message {
  position: relative;
  display: flex;
  gap: 0.5rem;
  width: 100%;
  animation: messageIn 0.2s ease-out;
}

@keyframes messageIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.wp-preview-scale .chat-detail .message-body {
  max-width: 75%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.wp-preview-scale .chat-detail .message--own {
  flex-direction: row-reverse;
}

.wp-preview-scale .chat-detail .message-text {
  position: relative;
  padding: 0.55rem 0.85rem;
  background: var(--bubble-other-bg, var(--surface-3));
  border-radius: var(--bubble-radius, var(--radius-lg));
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--bubble-other-text, var(--text-primary));
  word-break: break-word;
  box-shadow: var(--bubble-shadow, none);
}

.wp-preview-scale .chat-detail .message--own .message-text {
  background: var(--bubble-mine-bg, linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%));
  color: var(--bubble-mine-text, var(--text-on-accent));
  border-bottom-right-radius: var(--radius-sm);
}

.wp-preview-scale .chat-detail .message--other .message-text {
  border-bottom-left-radius: var(--radius-sm);
}

.wp-preview-scale .chat-detail .meta-float {
  float: right;
  display: inline-flex;
  margin: 0.55rem -0.2rem -0.3rem 0.75rem;
}

.wp-preview-scale .chat-detail .mm {
  font-size: 0.6875rem;
  color: var(--text-tertiary);
  line-height: 1;
}

.wp-preview-scale .chat-detail .input-area {
  position: relative;
  z-index: 2;
  padding: 0.3rem 0.5rem 0.5rem;
  background: transparent;
  border-top: none;
  flex-shrink: 0;
}

.wp-preview-scale .chat-detail .input-form {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.wp-preview-scale .chat-detail .input-row {
  display: flex;
  align-items: flex-end;
  gap: 0.2rem;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: 22px;
  padding: 0.5rem 0.35rem;
  box-shadow: var(--shadow-sm-modal);
  transition:
    border-color 0.2s,
    box-shadow 0.2s,
    background 0.2s;
}

.wp-preview-scale .chat-detail .input-row:focus-within {
  border-color: var(--accent);
  background: var(--surface-4);
  box-shadow: var(--border-glow);
}

.wp-preview-scale .chat-detail .input-action {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  min-height: 40px;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition:
    background 0.2s,
    color 0.2s,
    transform 0.2s;
  flex-shrink: 0;
}
.wp-preview-scale .chat-detail .input-action svg {
  width: 20px;
  height: 20px;
}
.wp-preview-scale .chat-detail .input-action:hover:not(:disabled) {
  background: var(--accent-subtle);
  color: var(--accent);
  transform: scale(1.08);
}
.wp-preview-scale .chat-detail .input-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.wp-preview-scale .chat-detail .message-textarea {
  flex: 1;
  padding: 0.45rem 0.35rem !important;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.95rem;
  resize: none;
  min-height: 24px !important;
  max-height: 100px !important;
  overflow-y: hidden;
  font-family: inherit;
  outline: none;
  line-height: 1.4;
  scrollbar-width: thin;
}
.wp-preview-scale .chat-detail .message-textarea::placeholder {
  color: var(--text-tertiary);
}
.wp-preview-scale .chat-detail .message-textarea:hover,
.wp-preview-scale .chat-detail .message-textarea:focus {
  border: none;
  background: transparent;
  box-shadow: none;
}
.wp-preview-scale .chat-detail .message-textarea:disabled {
  opacity: 0.5;
}

.wp-preview-scale .chat-detail .send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  min-height: 40px;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s,
    opacity 0.2s;
  box-shadow: var(--shadow-sm-petal-sm);
  flex-shrink: 0;
}
.wp-preview-scale .chat-detail .send-btn svg {
  width: 16px;
  height: 16px;
}
.wp-preview-scale .chat-detail .send-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-sm-glow-sm);
  transform: scale(1.07);
}
.wp-preview-scale .chat-detail .send-btn:active:not(:disabled) {
  transform: scale(0.95);
}
.wp-preview-scale .chat-detail .send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.wp-preview-scale .chat-detail .day-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: center;
  width: 100%;
  padding: 0.75rem 0;
}
.wp-preview-scale .chat-detail .day-label {
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--text-tertiary);
  background: var(--surface-1);
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
}

@media (prefers-reduced-motion: reduce) {
  .wp-preview-scale .chat-detail .message {
    animation: none;
  }
}
</style>
