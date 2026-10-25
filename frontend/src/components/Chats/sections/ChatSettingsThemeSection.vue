<template>
  <section class="settings-section">
    <div class="section-header">
      <h2><SakuraIcon name="palette" /> Тема и стиль</h2>
      <button @click="$emit('reset')" class="btn-ghost-sm">
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
                <ChatPreviewCards :anime-radius="animeCardBorderRadius" :playlist-radius="playlistCardBorderRadius" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="wp-sidebar">
      <div class="wp-sidebar-title">Коррекция пузырей</div>
      <div class="wp-control">
        <div class="wp-control-header">
          <SakuraIcon name="message" class="wp-control-icon" />
          <label class="wp-control-label">Скругление</label>
          <span class="wp-control-value">{{ form.bubble_border_radius }}px</span>
        </div>
        <UiRangeSlider
          v-model.number="form.bubble_border_radius"
          min="0"
          max="32"
          class="wp-range"
          :style="{
            '--slider-progress': ((form.bubble_border_radius - 0) / (32 - 0) * 100) + '%'
          }"
        />
      </div>
      <div class="wp-control">
        <div class="wp-control-header">
          <SakuraIcon name="film" class="wp-control-icon" />
          <label class="wp-control-label">Скругление аниме-карточки</label>
          <span class="wp-control-value">{{ animeCardBorderRadius }}px</span>
        </div>
        <UiRangeSlider
          v-model.number="form.anime_card_border_radius"
          min="0"
          max="32"
          class="wp-range"
          :style="{
            '--slider-progress': ((animeCardBorderRadius - 0) / (32 - 0) * 100) + '%'
          }"
        />
      </div>
      <div class="wp-control">
        <div class="wp-control-header">
          <SakuraIcon name="list" class="wp-control-icon" />
          <label class="wp-control-label">Скругление плейлиста</label>
          <span class="wp-control-value">{{ playlistCardBorderRadius }}px</span>
        </div>
        <UiRangeSlider
          v-model.number="form.playlist_card_border_radius"
          min="0"
          max="32"
          class="wp-range"
          :style="{
            '--slider-progress': ((playlistCardBorderRadius - 0) / (32 - 0) * 100) + '%'
          }"
        />
      </div>
      <div class="wp-control">
        <div class="wp-control-header">
          <SakuraIcon name="sun" class="wp-control-icon" />
          <label class="wp-control-label">Тень пузырей</label>
          <span class="wp-control-value">{{ form.bubble_shadow ? 'Вкл' : 'Выкл' }}</span>
        </div>
        <label class="switch">
          <input type="checkbox" v-model="form.bubble_shadow" />
          <span class="switch-slider"></span>
        </label>
      </div>
    </div>

    <div class="settings-group-card">
      <div class="sgc-title">
        <SakuraIcon name="message-square" /> Цвета фона сообщений
      </div>
      <div class="two-col">
        <div class="field-group">
          <label class="field-label">Мои (фон)</label>
          <div class="color-row">
            <div class="color-picker-wrap">
              <div class="color-preview" :style="{ backgroundColor: form.message_color_mine }"></div>
              <input
                type="color"
                v-model="form.message_color_mine"
                class="color-input"
              />
            </div>
            <input
              type="text"
              v-model="form.message_color_mine"
              class="color-hex-input"
            />
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">Чужие (фон)</label>
          <div class="color-row">
            <div class="color-picker-wrap">
              <div class="color-preview" :style="{ backgroundColor: form.message_color_other }"></div>
              <input
                type="color"
                v-model="form.message_color_other"
                class="color-input"
              />
            </div>
            <input
              type="text"
              v-model="form.message_color_other"
              class="color-hex-input"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="settings-group-card">
      <div class="sgc-title">
        <SakuraIcon name="type" /> Цвета текста сообщений
      </div>
      <div class="two-col">
        <div class="field-group">
          <label class="field-label">Мои (текст)</label>
          <div class="color-row">
            <div class="color-picker-wrap">
              <div class="color-preview" :style="{ backgroundColor: form.message_text_color_mine }"></div>
              <input
                type="color"
                v-model="form.message_text_color_mine"
                class="color-input"
              />
            </div>
            <input
              type="text"
              v-model="form.message_text_color_mine"
              class="color-hex-input"
            />
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">Чужие (текст)</label>
          <div class="color-row">
            <div class="color-picker-wrap">
              <div class="color-preview" :style="{ backgroundColor: form.message_text_color_other }"></div>
              <input
                type="color"
                v-model="form.message_text_color_other"
                class="color-input"
              />
            </div>
            <input
              type="text"
              v-model="form.message_text_color_other"
              class="color-hex-input"
            />
          </div>
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
          Сохранить тему
        </template>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import ChatPreviewCards from "../ChatPreviewCards.vue";
import UiRangeSlider from "@/components/common/UiRangeSlider.vue";
import { computed } from "vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { getMediaUrl } from "@/api/client";

interface ThemeForm {
  theme: string;
  message_color_mine: string;
  message_color_other: string;
  message_text_color_mine: string;
  message_text_color_other: string;
  bubble_style: string;
  bubble_border_radius: number;
  bubble_shadow: boolean;
  font_family: string;
  font_size: string;
  font_size_px: number;
  font_weight: number;
  line_height: number;
  time_format: string;
  time_color: string;
  background_color: string;
  header_color: string;
  input_color: string;
  input_text_color: string;
  accent_color: string;
  link_color: string;
  message_animation: string;
  reaction_animation: string;
  typing_animation: string;
  emoji_set: string;
  emoji_size: string;
  show_avatars: boolean;
  show_usernames: boolean;
  compact_mode: boolean;
  show_read_status: boolean;
  show_typing_indicator: boolean;
  message_grouping: boolean;
  custom_css: string;
  anime_card_border_radius: number;
  playlist_card_border_radius: number;
  [key: string]: unknown;
}

const form = defineModel<ThemeForm>("form", { required: true });

const props = defineProps<{
  themePresets: Record<string, unknown>[];
  presetId: string | null;
  saving: boolean;
  bubbleStyles: { value: string; label: string; defaultRadius: number }[];
  fontFamilies: { value: string; label: string }[];
  fontSizes: { value: string; label: string; px: number }[];
  interfaceColors: { key: string; label: string }[];
  themeToggles: { key: string; label: string; desc?: string }[];
  chatName: string;
  wallpaperType: string;
  wallpaperColor: string;
  wallpaperColor2?: string;
  wallpaperIntensity: number;
  wallpaperBlur: number;
  patternType?: string;
  patternColor?: string;
  patternOpacity?: number;
  wallpaperImageUrl?: string | null;
  wallpaperImagePreview?: string | null;
  animeCardBorderRadius: number;
  playlistCardBorderRadius: number;
}>();

const emit = defineEmits<{
  save: [];
  reset: [];
  "preset-apply": [preset: Record<string, unknown>];
  "update:wallpaperBlur": [value: number];
  "update:wallpaperIntensity": [value: number];
}>();

const chatDetailStyle = computed(() => ({
  "--preview-bg": form.value.background_color,
  "--preview-header": form.value.header_color,
  "--preview-input": form.value.input_color,
  "--preview-input-text": form.value.input_text_color,
  "--bubble-mine-bg": form.value.message_color_mine,
  "--bubble-mine-text": form.value.message_text_color_mine,
  "--bubble-other-bg": form.value.message_color_other,
  "--bubble-other-text": form.value.message_text_color_other,
  "--bubble-radius": form.value.bubble_border_radius + "px",
  "--bubble-font-family": fontFamilyCss.value,
  "--bubble-font-size": form.value.font_size_px + "px",
  "--bubble-shadow": form.value.bubble_shadow
    ? "0 2px 8px rgba(0,0,0,0.3)"
    : "none",
}));

const bgLayerStyle = computed(() => {
  const f = props;
if (f.wallpaperType === "image") {
  const saved =
    f.wallpaperImageUrl != null
      ? getMediaUrl(f.wallpaperImageUrl)
      : undefined;
  const src = f.wallpaperImagePreview || saved;
  if (!src) {
    return { backgroundColor: f.wallpaperColor || "#0f0f1a" };
  }
  return {
    backgroundImage: `url("${src}")`,
    backgroundColor: f.wallpaperColor || "#0f0f1a",
    filter: `blur(${Number(f.wallpaperBlur ?? 0)}px) brightness(${Number(f.wallpaperIntensity ?? 100) / 100})`,
  };
}
  if (f.wallpaperType === "gradient") {
    return {
      background: `linear-gradient(${f.patternType === 'radial' ? 'radial' : 'linear'} gradient, ${f.wallpaperColor} 0%, ${f.wallpaperColor2 || '#1a1a2e'} 100%)`,
      backgroundColor: f.wallpaperColor || "#0f0f1a",
    };
  }
  return { backgroundColor: f.wallpaperColor || "#0f0f1a" };
});

const fontFamilyCss = computed(() => {
  const map: Record<string, string> = {
    system: "system-ui,-apple-system,sans-serif",
    inter: "Inter,sans-serif",
    roboto: "Roboto,sans-serif",
    nunito: "Nunito,sans-serif",
    montserrat: "Montserrat,sans-serif",
  };
  return map[form.value.font_family] || "system-ui";
});

const wallpaperBlur = computed({
  get: () => props.wallpaperBlur,
  set: (v: number) => emit("update:wallpaperBlur", v),
});

const wallpaperIntensity = computed({
  get: () => props.wallpaperIntensity,
  set: (v: number) => emit("update:wallpaperIntensity", v),
});

const animeCardBorderRadius = computed(() => props.animeCardBorderRadius);
const playlistCardBorderRadius = computed(() => props.playlistCardBorderRadius);
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

.wp-preview-scale .chat-detail .chat-wallpaper {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    background-size: cover;
    background-position: center;
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
  font-family: var(--bubble-font-family, system-ui);
  font-size: var(--bubble-font-size, 13px);
  box-shadow: var(--bubble-shadow, none);
}

.wp-preview-scale .chat-detail .message--own .message-text {
  background: var(--bubble-mine-bg, var(--accent-subtle));
  color: var(--bubble-mine-text, var(--text-primary));
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

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
  cursor: pointer;
}
.switch input {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  cursor: pointer;
  margin: 0;
}
.switch-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--surface-5);
  border-radius: 24px;
  transition: all var(--duration-base) var(--ease-petal);
  pointer-events: none;
  border: 1px solid var(--border-default);
}
.switch-slider::before {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: all var(--duration-base) var(--ease-petal);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
}
.switch input:checked + .switch-slider {
  background: var(--accent);
  border-color: var(--accent);
}
.switch input:checked + .switch-slider::before {
  transform: translateX(20px);
}
.switch:hover .switch-slider {
  background: var(--surface-4);
}
.switch input:checked:hover + .switch-slider {
  background: var(--accent-press);
  border-color: var(--accent-press);
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

.field-group {
  margin-bottom: var(--space-4);
}
.field-group:last-child {
  margin-bottom: 0;
}
.field-label {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
  font-weight: 500;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
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

.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border-subtle);
}
.toggle-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.toggle-row:first-child {
  padding-top: 0;
}
.tr-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.tr-label {
  font-size: var(--text-base);
  color: var(--text-primary);
  font-weight: 500;
}
.tr-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
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
  .two-col {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .settings-section,
  .btn-primary,
  .chat-wallpaper {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  .wp-preview-scale .chat-detail .message {
    animation: none;
  }
}
</style>
