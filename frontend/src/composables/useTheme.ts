import { computed } from "vue";
import {
  useAppearance,
  FONT_OPTIONS,
  type ThemeId,
} from "@/composables/useAppearance";

/**
 * Тонкая обёртка над общим хранилищем оформления (useAppearance).
 * Состояние одно на всё приложение: тема и акцент больше не «живут» отдельно
 * в каждом компоненте, который вызвал useTheme().
 */
export function useTheme() {
  const appearance = useAppearance();

  const currentTheme = appearance.theme;
  const accentColor = appearance.effectiveAccent;
  const customTheme = appearance.customTheme;
  const hasChanges = appearance.hasChanges;
  const save = appearance.save;
  const load = appearance.load;
  const isLightTheme = computed(() => appearance.theme.value === "light");

  const fontFamily = appearance.fontFamily;
  const fontSize = appearance.fontSize;
  const lineSpacing = appearance.lineSpacing;
  const fontWeight = appearance.fontWeight;

  const setTheme = (theme: ThemeId) => appearance.setTheme(theme);
  const setAccentColor = (color: string) => appearance.setAccentColor(color);
  const toggleTheme = () => setTheme(isLightTheme.value ? "dark" : "light");

  /**
   * Применение расширенных настроек шрифта (поля FontSettings с сервера).
   * Шрифт, размер и интервал идут через общее состояние; остальное ставится
   * как атрибуты/переменные на <html>.
   */
  const applyFontSettings = (settings: {
    font_family?: string;
    font_size?: number;
    interface_scale?: number;
    line_height?: number;
    density?: string;
    bold_headings?: boolean;
    reduce_motion?: boolean;
    high_contrast_mode?: boolean;
    font_weight?: string;
  }) => {
    const root = document.documentElement;

    if (settings.font_family && FONT_OPTIONS.some((f) => f.value === settings.font_family)) {
      appearance.fontFamily.value = settings.font_family;
    }
    if (settings.font_size) {
      appearance.fontSize.value = Math.min(18, Math.max(12, Math.round(settings.font_size)));
    }
    if (settings.line_height) {
      appearance.lineSpacing.value = Math.min(1.8, Math.max(1, settings.line_height));
    }
    if (settings.font_weight) {
      appearance.fontWeight.value = settings.font_weight === "bold" ? "bold" : "normal";
    }
    if (settings.reduce_motion !== undefined) {
      appearance.smoothAnimations.value = !settings.reduce_motion;
    }
    if (settings.high_contrast_mode !== undefined) {
      appearance.highContrast.value = settings.high_contrast_mode;
    }
    if (settings.interface_scale) {
      root.style.setProperty("--interface-scale", String(settings.interface_scale / 100));
    }
    if (settings.density) {
      root.setAttribute("data-density", settings.density);
    }
    if (settings.bold_headings !== undefined) {
      root.style.setProperty("--heading-font-weight", settings.bold_headings ? "600" : "400");
    }
  };

  return {
    currentTheme,
    accentColor,
    customTheme,
    hasChanges,
    isLightTheme,
    toggleTheme,
    setTheme,
    setAccentColor,
    save,
    load,
    applyFontSettings,
    fontFamily,
    fontSize,
    lineSpacing,
    fontWeight,
  };
}
