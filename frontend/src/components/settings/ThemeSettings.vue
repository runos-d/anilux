<template>
  <div class="settings-section">
    <transition name="toast">
      <div v-if="toast.visible" :class="['toast-notif', toast.type]">
        {{ toast.message }}
      </div>
    </transition>

    <div class="section-head">
      <h2>Тема и оформление</h2>
      <p>Настройте внешний вид сайта под себя</p>
    </div>

    <!-- ═══ Выбор темы ═══ -->
    <div class="settings-group">
      <h3><SakuraIcon name="sun" /> Выбор темы</h3>
      <div class="theme-grid">
        <label
          v-for="t in themes"
          :key="t.id"
          class="theme-option"
          :class="{ active: currentTheme === t.id }"
        >
          <input
            type="radio"
            name="theme"
            class="sr-only"
            :checked="currentTheme === t.id"
            @change="setTheme(t.id)"
          />
          <div
            class="theme-preview"
            :class="t.id"
            :style="
              t.id === 'custom'
                ? { '--ct-base': customTheme.bg, '--ct-accent': accentColor }
                : undefined
            "
          >
            <div class="preview-mock">
              <div class="mock-top">
                <span class="mock-dot"></span>
                <span class="mock-line"></span>
              </div>
              <div class="mock-bubble other"></div>
              <div class="mock-bubble user"></div>
              <div class="mock-input"></div>
            </div>
            <span class="check-badge"><SakuraIcon name="check" /></span>
          </div>
          <span class="theme-name">{{ t.label }}</span>
        </label>
      </div>

      <transition name="fade-slide">
        <div v-if="currentTheme === 'custom'" class="custom-theme-panel">
          <div
            v-for="group in CUSTOM_THEME_GROUPS"
            :key="group.title"
            class="ct-group"
          >
            <div class="ct-group-title">{{ group.title }}</div>
            <div class="ct-rows">
              <div v-for="row in group.keys" :key="row.key" class="ct-field">
                <span class="ct-label">{{ row.label }}</span>
                <label class="custom-swatch">
                  <input
                    type="color"
                    class="color-picker"
                    :value="row.key === 'accent' ? accentColor : customTheme[row.key]"
                    :aria-label="row.label"
                    @change="onCustomThemeColorChange(row.key, $event)"
                  />
                </label>
                <span class="ct-hex">
                  {{
                    (row.key === 'accent' ? accentColor : customTheme[row.key]).toUpperCase()
                  }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- ═══ Шрифты ═══ -->
    <!-- <div class="settings-group">
      <h3><SakuraIcon name="file-text" /> Шрифты</h3>

      <div class="row">
        <span class="row-title">Основной шрифт</span>
        <select v-model="fontFamily" class="sel">
          <option value="Inter">Inter</option>
          <option value="Roboto">Roboto</option>
          <option value="Open Sans">Open Sans</option>
          <option value="Lato">Lato</option>
          <option value="Montserrat">Montserrat</option>
          <option value="anime">Noto Sans JP (аниме)</option>
          <option value="system">Системный</option>
        </select>
      </div>

      <div class="row slider-row">
        <span class="row-title">
          Размер шрифта <b class="value-pill">{{ fontSize }} px</b>
        </span>
        <div class="range-wrap">
          <span class="range-edge">Маленький</span>
          <UiRangeSlider
            v-model.number="fontSize"
            min="12"
            max="18"
            step="1"
            class="range"
            :style="{ '--p': pct(fontSize, 12, 18) + '%' }"
          />
          <span class="range-edge">Большой</span>
        </div>
      </div>

      <div class="row slider-row">
        <span class="row-title">
          Межстрочный интервал <b class="value-pill">{{ Number(lineSpacing).toFixed(1) }}</b>
        </span>
        <div class="range-wrap">
          <span class="range-edge">Узкий</span>
          <UiRangeSlider
            v-model.number="lineSpacing"
            min="1.0"
            max="1.8"
            step="0.1"
            class="range"
            :style="{ '--p': pct(lineSpacing, 1, 1.8) + '%' }"
          />
          <span class="range-edge">Широкий</span>
        </div>
      </div>

      <div class="row">
        <span class="row-title">Жирность</span>
        <div class="segmented">
          <button
            type="button"
            :class="{ active: fontWeight === 'normal' }"
            @click="fontWeight = 'normal'"
          >
            Обычный
          </button>
          <button
            type="button"
            :class="{ active: fontWeight === 'bold' }"
            @click="fontWeight = 'bold'"
          >
            Жирный
          </button>
        </div>
      </div>

      <div class="font-preview" :style="fontPreviewStyle">
        Так будет выглядеть текст сообщений и описаний на сайте. Съешь ещё этих
        мягких французских булок.
      </div>
    </div> -->

    <!-- ═══ Эффекты и анимации ═══ -->
    <div class="settings-group">
      <h3><SakuraIcon name="sparkles" /> Эффекты и анимации</h3>

      <div class="subtitle">Праздничные эффекты</div>

      <label class="row toggle-row">
        <span class="row-text">
          <span class="row-title">Падающая сакура</span>
          <span class="row-hint">Лепестки сакуры</span>
        </span>
        <span class="switch">
          <input type="checkbox" role="switch" v-model="sakuraEnabled" />
          <span class="knob"></span>
        </span>
      </label>

      <label class="row toggle-row">
        <span class="row-text">
          <span class="row-title">Новый год</span>
          <span class="row-hint">Снег</span>
        </span>
        <span class="switch">
          <input type="checkbox" role="switch" v-model="newYearEnabled" />
          <span class="knob"></span>
        </span>
      </label>

      <label class="row toggle-row">
        <span class="row-text">
          <span class="row-title">Хэллоуин</span>
          <span class="row-hint">Призраки и летучие мыши</span>
        </span>
        <span class="switch">
          <input type="checkbox" role="switch" v-model="halloweenEnabled" />
          <span class="knob"></span>
        </span>
      </label>

      <label class="row toggle-row">
        <span class="row-text">
          <span class="row-title">День влюблённых</span>
          <span class="row-hint">Сердечки</span>
        </span>
        <span class="switch">
          <input type="checkbox" role="switch" v-model="loveDayEnabled" />
          <span class="knob"></span>
        </span>
      </label>
    </div>

    <!-- ═══ Действия ═══ -->
    <div class="settings-actions">
      <span v-if="hasChanges" class="unsaved-hint">Есть несохранённые изменения</span>
      <div class="actions-buttons">
        <button
          type="button"
          @click="saveSettings"
          :disabled="!hasChanges || isSaving"
          class="save-btn"
        >
          <SakuraIcon name="save" /> Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import UiRangeSlider from "@/components/common/UiRangeSlider.vue";
import { ref, computed, onBeforeUnmount } from "vue";
import { useTheme } from "@/composables/useTheme";
import {
  CUSTOM_THEME_GROUPS,
  revertAppearance,
  type CustomThemeKey,
} from "@/composables/useAppearance";
import { useSakuraOverlay } from "@/composables/useSakuraOverlay";
import { useNewYearOverlay } from "@/composables/useNewYearOverlay";
import { useHalloweenOverlay } from "@/composables/useHalloweenOverlay";
import { useLoveDayOverlay } from "@/composables/useLoveDayOverlay";

const toast = ref({
  visible: false,
  message: "",
  type: "success" as "success" | "error",
});
let _toastTimer: ReturnType<typeof setTimeout> | null = null;
const showToast = (msg: string, type: "success" | "error" = "success") => {
  if (_toastTimer) clearTimeout(_toastTimer);
  toast.value = { visible: true, message: msg, type };
  _toastTimer = setTimeout(() => (toast.value.visible = false), 3000);
};

const {
  currentTheme,
  accentColor,
  customTheme,
  hasChanges,
  setTheme,
  setAccentColor,
  save,
  fontFamily,
  fontSize,
  lineSpacing,
  fontWeight,
} = useTheme();
const { sakuraEnabled } = useSakuraOverlay();
const { newYearEnabled } = useNewYearOverlay();
const { halloweenEnabled } = useHalloweenOverlay();
const { loveDayEnabled } = useLoveDayOverlay();

const isSaving = ref(false);

onBeforeUnmount(() => {
  if (!isSaving.value && hasChanges.value) revertAppearance();
  if (_toastTimer) clearTimeout(_toastTimer);
});

export type ThemeId =
  | "light"
  | "dark"
  | "system"
  | "banana"
  | "sea"
  | "lilac"
  | "emerald"
  | "peach"
  | "blueberry"
  | "rozovaya"
  | "polnochnaya"
  | "custom";

const themes: { id: ThemeId; label: string }[] = [
  { id: "dark", label: "Чёрная" },
  { id: "polnochnaya", label: "Полночная" },
];

const showCustomColor = ref(false);
const customColor = ref("#0084FF");

const accentColors = [
  { value: "#0084FF" }, // Blue
  { value: "#00C853" }, // Green
  { value: "#AA00FF" }, // Purple
  { value: "#FF6D00" }, // Orange
  { value: "#D50000" }, // Red
  { value: "#FFD600" }, // Yellow
];

const isCustomAccent = computed(
  () =>
    !!accentColor.value &&
    !accentColors.some(
      (c) => c.value.toLowerCase() === String(accentColor.value).toLowerCase(),
    ),
);

const pct = (val: number | string, min: number, max: number) =>
  Math.min(100, Math.max(0, ((Number(val) - min) / (max - min)) * 100));

const fontPreviewStyle = computed(() => ({
  fontFamily: `"${fontFamily.value}", var(--font-sans)`,
  fontSize: `${fontSize.value}px`,
  lineHeight: String(lineSpacing.value),
  fontWeight: fontWeight.value === "bold" ? 700 : 400,
}));

const saveSettings = async () => {
  if (isSaving.value) return;
  isSaving.value = true;
  try {
    await save();
    showToast("Тема сохранена");
  } catch (error) {
    console.error("Error saving theme settings:", error);
    showToast(
      (error as { message?: string })?.message || "Ошибка при сохранении",
      "error",
    );
  } finally {
    isSaving.value = false;
  }
};

const previewSettings = () => {
  setTheme(currentTheme.value as ThemeId);
  setAccentColor(accentColor.value);
};

const handleAccentColorChange = async (color: string) => {
  await setAccentColor(color);
};

const onCustomThemeColorChange = (key: CustomThemeKey, e: Event) => {
  const value = (e.target as HTMLInputElement).value;
  if (!/^#[0-9a-f]{6}$/i.test(value)) return;
  if (key === "accent") {
    setAccentColor(value.toLowerCase());
    return;
  }
  customTheme.value[key] = value.toLowerCase();
};
</script>

<style scoped>
/* ═══ Каркас ═══════════════════════════════════════════════════ */
.settings-section {
  display: flex;
  flex-direction: column;
}

.section-head {
  padding: 24px 24px 4px;
}
.section-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
}
.section-head p {
  margin: 4px 0 0;
  font-size: var(--text-base);
  color: var(--text-tertiary);
}

.settings-group {
  padding: 22px 24px;
  border-bottom: 1px solid var(--border-subtle);
}
.settings-group h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
}
.settings-group h3 :deep(svg) {
  color: var(--accent);
  flex-shrink: 0;
}

.subtitle {
  margin: 14px 0 2px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}
.subtitle:first-of-type {
  margin-top: 0;
}

/* ═══ Строки настроек ═════════════════════════════════════════ */
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 10px;
  margin: 0 -10px;
  border-radius: var(--radius-md);
  transition: background var(--duration-base) var(--ease-out);
}
.row + .row {
  border-top: 1px solid
    color-mix(in srgb, var(--border-default) 40%, transparent);
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}
.toggle-row {
  cursor: pointer;
  user-select: none;
}
.toggle-row:hover {
  background: var(--accent-subtle);
}

.row-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.row-title {
  font-size: var(--text-md);
  font-weight: 500;
  color: var(--text-primary);
}
.row-hint {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  line-height: 1.35;
}

/* ═══ Переключатель (как во вкладке уведомлений) ═════════════ */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 25px;
  flex-shrink: 0;
}
.switch input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 0;
  cursor: pointer;
  z-index: 1;
}
.knob {
  position: absolute;
  inset: 0;
  background: var(--surface-6);
  border: 1px solid var(--border-default);
  border-radius: 25px;
  transition:
    background var(--duration-slow) var(--ease-out),
    border-color var(--duration-slow) var(--ease-out),
    box-shadow var(--duration-slow) var(--ease-out);
}
.knob::before {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 17px;
  height: 17px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.45);
  transition: transform var(--duration-slow) var(--ease-spring);
}
.switch input:checked + .knob {
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 0 12px var(--accent-glow-sm);
}
.switch input:checked + .knob::before {
  transform: translateX(19px);
}
.switch input:active + .knob::before {
  width: 21px;
}
.switch input:checked:active + .knob::before {
  transform: translateX(15px);
}
.switch input:focus-visible + .knob {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* ═══ Карточки тем ════════════════════════════════════════════ */
.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
  gap: 14px;
}

.theme-option {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  cursor: pointer;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition:
    border-color var(--duration-base) var(--ease-out),
    background var(--duration-base) var(--ease-out),
    transform var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
}
.theme-option:hover {
  border-color: var(--border-strong);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.theme-option.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), var(--shadow-glow-sm);
}
.theme-option:focus-within {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.theme-name {
  padding: 9px 12px;
  border-top: 1px solid var(--border-subtle);
  text-align: center;
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--text-secondary);
}
.theme-option.active .theme-name {
  color: var(--text-primary);
  background: var(--accent-subtle);
  font-weight: 600;
}

/* ── Мини-макет чата в превью ── */
.theme-preview {
  --pv-surface: rgba(255, 255, 255, 0.14);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: var(--accent);
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
}
.preview-mock {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10%;
  background: var(--pv-surface);
}
.mock-top {
  display: flex;
  align-items: center;
  gap: 6%;
}
.mock-dot {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--pv-user);
}
.mock-line {
  width: 34%;
  height: 6px;
  border-radius: 3px;
  background: var(--pv-other);
}
.mock-bubble {
  height: 10px;
  border-radius: 5px;
}
.mock-bubble.other {
  align-self: flex-start;
  width: 54%;
  background: var(--pv-other);
}
.mock-bubble.user {
  align-self: flex-end;
  width: 64%;
  background: var(--pv-user);
}
.mock-input {
  height: 9px;
  border-radius: 5px;
  background: var(--pv-surface);
  border: 1px solid var(--pv-other);
}

.theme-preview.light {
  --pv-surface: rgba(255, 255, 255, 0.65);
  --pv-other: rgba(70, 50, 65, 0.28);
  --pv-user: #ff7eb3;
  background: linear-gradient(135deg, #f7f4f8 0%, #e4dce4 100%);
}
.theme-preview.dark {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #ff7eb3;
  background: linear-gradient(135deg, #16131d 0%, #262034 100%);
}
/* Система: верхняя половина -светлая, нижняя -тёмная.
   Элементы макета подобраны так, чтобы ни один не пересекал разделитель. */
.theme-preview.system {
  background: linear-gradient(180deg, #f1f1f6 0 50%, #1d1d24 50% 100%);
}
.theme-preview.system .mock-dot {
  background: #ff7eb3;
}
.theme-preview.system .mock-line {
  background: rgba(30, 24, 40, 0.35);
}
.theme-preview.system .mock-bubble.other {
  background: rgba(30, 24, 40, 0.28);
}
.theme-preview.system .mock-bubble.user {
  background: #ff7eb3;
}
.theme-preview.system .mock-input {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.28);
}

.theme-preview.red {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #ef5350;
  background: linear-gradient(135deg, #1c090c 0%, #4a2930 100%);
}
.theme-preview.yellow {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #f5b52e;
  background: linear-gradient(135deg, #191204 0%, #483917 100%);
}

/* «Своя тема»: превью показывает текущие базовый цвет и акцент пользователя */
.theme-preview.blueberry {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #7a7ac8;
  background: linear-gradient(135deg, #0e0e1c 0%, #292948 100%);
}

.theme-preview.banana {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #e8c547;
  background: linear-gradient(135deg, #17140a 0%, #463d23 100%);
}

.theme-preview.sea {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #3aa8b8;
  background: linear-gradient(135deg, #071619 0%, #1f4a54 100%);
}

.theme-preview.lilac {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #b898d9;
  background: linear-gradient(135deg, #15101c 0%, #342a48 100%);
}

.theme-preview.emerald {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #3aa876;
  background: linear-gradient(135deg, #08160f 0%, #234a34 100%);
}

.theme-preview.peach {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #e8a07c;
  background: linear-gradient(135deg, #1a120c 0%, #3f2f21 100%);
}

/* «Своя тема»: превью показывает текущие базовый цвет и акцент пользователя */
.theme-preview.rozovaya {
  --pv-surface: rgba(255, 255, 255, 0.65);
  --pv-other: rgba(59, 22, 48, 0.28);
  --pv-user: #f0508a;
  background: linear-gradient(135deg, #fff0f6 0%, #ffe3ee 100%);
}

/* «Полночная»: тёмная версия розовой стикерной темы */
.theme-preview.polnochnaya {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(244, 169, 200, 0.3);
  --pv-user: #ff5c9d;
  background: linear-gradient(135deg, #170b17 0%, #3a1a3b 100%);
}

.theme-preview.custom {
  --pv-surface: rgba(255, 255, 255, 0.1);
  --pv-other: rgba(255, 255, 255, 0.25);
  --pv-user: var(--ct-accent, #ff7eb3);
  background: linear-gradient(
    135deg,
    var(--ct-base, #1c162c) 0%,
    color-mix(in srgb, var(--ct-base, #1c162c) 40%, var(--ct-accent, #ff7eb3)) 100%
  );
}

/* ═══ Настройка «Своей темы» ══════════════════════════════════ */
.custom-theme-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 14px;
}
.ct-group {
  padding: 12px 14px;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}
.ct-group-title {
  margin-bottom: 10px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}
.ct-rows {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 10px;
}
.ct-field {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: border-color var(--duration-base) var(--ease-out);
}
.ct-field:hover {
  border-color: var(--border-strong);
}
.ct-field .custom-swatch {
  width: 34px;
  height: 34px;
}
.ct-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
}
.ct-hex {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}
.theme-preview.blue {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #5c9fe8;
  background: linear-gradient(135deg, #0c1630 0%, #1a3060 100%);
}
.theme-preview.green {
  --pv-surface: rgba(255, 255, 255, 0.08);
  --pv-other: rgba(255, 255, 255, 0.22);
  --pv-user: #5ec49a;
  background: linear-gradient(135deg, #0a1f13 0%, #1b3c2a 100%);
}

.check-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--text-on-accent);
  box-shadow: 0 2px 8px var(--accent-glow);
  opacity: 0;
  transform: scale(0.4);
  transition:
    opacity var(--duration-base) var(--ease-out),
    transform var(--duration-slow) var(--ease-spring);
}
.check-badge :deep(svg) {
  width: 12px;
  height: 12px;
}
.theme-option.active .check-badge {
  opacity: 1;
  transform: scale(1);
}

/* ═══ Акцентный цвет ══════════════════════════════════════════ */
.color-palette {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 4px 2px;
}
.color-option {
  --swatch: var(--accent);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: 2px solid transparent;
  border-radius: 50%;
  background: var(--swatch);
  background-clip: padding-box;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 0 0 2px var(--surface-3);
  transition:
    transform var(--duration-base) var(--ease-spring),
    box-shadow var(--duration-base) var(--ease-out);
}
.color-option:hover {
  transform: scale(1.12);
}

.color-option.active {
  box-shadow:
    0 0 0 2px var(--surface-3),
    0 0 0 4px var(--swatch),
    0 4px 14px color-mix(in srgb, var(--swatch) 50%, transparent);
}

.swatch-check {
  width: 18px;
  height: 18px;
  opacity: 0;
  transform: scale(0.4);
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
  transition:
    opacity var(--duration-base) var(--ease-out),
    transform var(--duration-slow) var(--ease-spring);
}
.color-option.active .swatch-check {
  opacity: 1;
  transform: scale(1);
}
.color-option.custom {
  --swatch: var(--accent);
  background: conic-gradient(
    from 0deg,
    #ff6b6b,
    #feca57,
    #96ceb4,
    #45b7d1,
    #a29bfe,
    #ff6b6b
  );
}
/* Активный «свой» цвет: выбранный цвет + тонкое радужное кольцо */
.color-option.custom.active {
  background:
    radial-gradient(circle, var(--swatch) 0 58%, transparent 59%),
    conic-gradient(
      from 0deg,
      #ff6b6b,
      #feca57,
      #96ceb4,
      #45b7d1,
      #a29bfe,
      #ff6b6b
    );
}
.color-option.custom :deep(svg) {
  width: 18px;
  height: 18px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.55));
}

/* ═══ Свой цвет ═══════════════════════════════════════════════ */
.custom-color-input {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 14px;
  padding: 12px 14px;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}
.custom-swatch {
  position: relative;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  overflow: hidden;
  cursor: pointer;
  background: var(--surface-5);
  border: 1px solid var(--border-strong);
  border-radius: 50%;
  box-shadow: inset 0 0 0 2px var(--surface-3);
  transition: box-shadow var(--duration-base) var(--ease-out);
}
.custom-swatch:hover {
  box-shadow: inset 0 0 0 2px var(--border-strong);
}
.color-picker {
  position: absolute;
  inset: -8px;
  width: calc(100% + 16px);
  height: calc(100% + 16px);
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
}
.color-picker::-webkit-color-swatch-wrapper {
  padding: 0;
}
.color-picker::-webkit-color-swatch {
  border: none;
}
.color-picker::-moz-color-swatch {
  border: none;
}
.swatch-plus {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  background: color-mix(in srgb, var(--surface-1) 55%, transparent);
  pointer-events: none;
}
.swatch-plus :deep(svg) {
  width: 18px;
  height: 18px;
}
.custom-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.color-hex {
  font-family: var(--font-mono);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text-primary);
}
.custom-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
.done-btn {
  padding: 8px 18px;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-button);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--duration-base) var(--ease-out);
}
.done-btn:hover {
  background: var(--accent-hover);
}

/* ═══ Select ══════════════════════════════════════════════════ */
.sel {
  min-width: 180px;
  padding: 9px 36px 9px 12px;
  color: var(--text-primary);
  font-size: var(--text-base);
  background-color: var(--surface-4);
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none' stroke='%23a090b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M1 1.5l5 5 5-5'/></svg>");
  background-repeat: no-repeat;
  background-position: right 12px center;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  transition:
    border-color var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
}
.sel:hover {
  border-color: var(--border-strong);
}
.sel:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}
.sel option {
  background: var(--surface-3);
  color: var(--text-primary);
}

/* ═══ Фон чатов ═══════════════════════════════════════════════ */
.bg-block {
  margin-top: 4px;
}
.background-preview {
  margin-top: 10px;
}
.preview-container {
  position: relative;
  height: 150px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-default);
}
.preview-container.default {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.preview-container.stars {
  background:
    radial-gradient(1.5px 1.5px at 20% 30%, #fff, transparent),
    radial-gradient(1px 1px at 70% 20%, #fff, transparent),
    radial-gradient(1.5px 1.5px at 85% 60%, #fff, transparent),
    radial-gradient(1px 1px at 40% 70%, #fff, transparent),
    radial-gradient(1px 1px at 10% 80%, #fff, transparent),
    linear-gradient(180deg, #05060f 0%, #1b1840 100%);
}
.preview-container.mountains {
  background: linear-gradient(180deg, #f6a96b 0%, #6d5a8d 55%, #2a2748 100%);
}
.preview-container.ocean {
  background: linear-gradient(180deg, #4fc3f7 0%, #0277bd 55%, #01304f 100%);
}
.preview-chat {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.preview-message {
  max-width: 72%;
  padding: 8px 12px;
  font-size: var(--text-sm);
  border-radius: 14px;
}
.preview-message.user {
  align-self: flex-end;
  background: rgba(255, 255, 255, 0.92);
  color: #1a1a1f;
  border-bottom-right-radius: 4px;
}
.preview-message.other {
  align-self: flex-start;
  background: rgba(0, 0, 0, 0.35);
  color: #fff;
  backdrop-filter: blur(6px);
  border-bottom-left-radius: 4px;
}
.background-actions {
  margin-top: 12px;
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-button);
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
}
.action-btn:hover {
  background: var(--accent-subtle);
  border-color: var(--accent);
}

/* ═══ Ползунки ════════════════════════════════════════════════ */
.slider-row {
  flex-wrap: wrap;
}
.value-pill {
  display: inline-block;
  margin-left: 8px;
  padding: 1px 9px;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--accent-bright);
  background: var(--accent-subtle);
  border-radius: var(--radius-full);
}
.range-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1 1 280px;
  max-width: 380px;
}
.range-edge {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  white-space: nowrap;
}
.range {
  --p: 50%;
  flex: 1;
  height: 6px;
  margin: 0;
  background: linear-gradient(
    to right,
    var(--accent) var(--p),
    var(--surface-6) var(--p)
  );
  border-radius: 3px;
  outline: none;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
}
.range::-webkit-slider-runnable-track {
  background: transparent;
  height: 6px;
}
.range::-moz-range-track {
  background: transparent;
  height: 6px;
}
.range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  margin-top: -6px;
  background: #fff;
  border: 3px solid var(--accent);
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-spring);
}
.range::-moz-range-thumb {
  width: 12px;
  height: 12px;
  background: #fff;
  border: 3px solid var(--accent);
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
  cursor: pointer;
}
.range:hover::-webkit-slider-thumb,
.range:active::-webkit-slider-thumb {
  transform: scale(1.15);
}
.range:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 6px;
}

/* ═══ Сегментированный переключатель ══════════════════════════ */
.segmented {
  display: inline-flex;
  padding: 3px;
  gap: 3px;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}
.segmented button {
  padding: 7px 16px;
  background: transparent;
  color: var(--text-secondary);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
}
.segmented button:hover:not(.active) {
  background: var(--accent-subtle);
}
.segmented button.active {
  background: var(--accent);
  color: var(--text-on-accent);
  font-weight: 600;
  box-shadow: var(--shadow-petal-sm);
}

/* ═══ Образец шрифта ══════════════════════════════════════════ */
.font-preview {
  margin-top: 14px;
  padding: 14px 16px;
  color: var(--text-primary);
  background: var(--surface-4);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-md);
  transition: all var(--duration-base) var(--ease-out);
}

/* ═══ Действия ════════════════════════════════════════════════ */
.settings-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 18px 24px;
}
.unsaved-hint {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-base);
  color: var(--warning);
}
.unsaved-hint::before {
  content: "";
  width: 8px;
  height: 8px;
  background: var(--warning);
  border-radius: 50%;
  animation: pulse 2.2s var(--ease-inout) infinite;
}
.actions-buttons {
  display: flex;
  gap: 12px;
  margin-left: auto;
}
.preview-btn,
.save-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 22px;
  border-radius: var(--radius-button);
  font-size: var(--text-md);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
}
.preview-btn {
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}
.preview-btn:hover {
  background: var(--accent-subtle);
  border-color: var(--accent);
}
.save-btn {
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  box-shadow: var(--shadow-petal-sm);
}
.save-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  box-shadow: var(--shadow-petal);
  transform: translateY(-1px);
}
.save-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

/* ═══ Тосты и переходы ════════════════════════════════════════ */
.toast-notif {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  padding: 11px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  pointer-events: none;
}
.toast-notif.success {
  background: #22c55e;
  color: #fff;
}
.toast-notif.error {
  background: #ef4444;
  color: #fff;
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition:
    opacity var(--duration-slow) var(--ease-out),
    transform var(--duration-slow) var(--ease-out);
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ═══ Адаптив ═════════════════════════════════════════════════ */
@media (max-width: 1024px) {
  .theme-grid {
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  }
}

@media (max-width: 767px) {
  .section-head {
    padding: 18px 18px 2px;
  }
  .section-head h2 {
    font-size: var(--text-2xl);
  }
  .settings-group {
    padding: 18px;
  }
  .theme-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  .theme-option {
    padding: 8px;
  }
  .row {
    gap: 12px;
  }
  .row:not(.toggle-row) {
    flex-wrap: wrap;
  }
  .sel {
    width: 100%;
    min-width: 0;
  }
  .range-wrap {
    flex: 1 1 100%;
    max-width: none;
  }
  .segmented {
    width: 100%;
  }
  .segmented button {
    flex: 1;
  }
  .settings-actions {
    flex-direction: column;
    align-items: stretch;
    padding: 16px 18px;
  }
  .actions-buttons {
    flex-direction: column-reverse;
    margin-left: 0;
  }
  .preview-btn,
  .save-btn,
  .action-btn {
    width: 100%;
    justify-content: center;
  }
  .toast-notif {
    top: auto;
    bottom: 16px;
    left: 16px;
    right: 16px;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .theme-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .color-option {
    width: 36px;
    height: 36px;
  }
  .color-palette {
    gap: 10px;
  }
  .row-title {
    font-size: var(--text-base);
  }
  .preview-container {
    height: 120px;
  }
  .custom-color-input {
    flex-wrap: wrap;
  }
}

@media (hover: none) and (pointer: coarse) {
  .theme-option:hover,
  .color-option:hover {
    transform: none;
  }
  .toggle-row:hover {
    background: transparent;
  }
  .toggle-row:active {
    background: var(--accent-subtle);
  }
}

@supports (padding: max(0px)) {
  @media (max-width: 767px) {
    .toast-notif {
      left: max(16px, env(safe-area-inset-left));
      right: max(16px, env(safe-area-inset-right));
      bottom: max(16px, env(safe-area-inset-bottom));
    }
  }
}
</style>
