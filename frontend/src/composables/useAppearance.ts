import { reactive, computed, watch, toRefs } from "vue";
import { afterInitialContent } from '@/lib/initialContent';
import * as settingsApi from "@/api/settings";
import { isRequestCancelled } from "@/api/client";
import { useSakuraOverlay } from "@/composables/useSakuraOverlay";
import { useNewYearOverlay } from "@/composables/useNewYearOverlay";
import { useHalloweenOverlay } from "@/composables/useHalloweenOverlay";
import { useLoveDayOverlay } from "@/composables/useLoveDayOverlay";
import { setScrollRevealEnabled } from "@/composables/useScrollReveal";

/**
 * Единое хранилище настроек «Тема и оформление».
 *
 * - состояние общее на всё приложение (одна reactive-копия на модуль);
 * - любое изменение сразу применяется к <html> (атрибуты data-*, CSS-переменные);
 * - «сохранённое» состояние кэшируется в localStorage, чтобы оформление
 *   применялось до ответа сервера и не мигало при загрузке;
 * - на сервер всё уходит одним запросом (save), с сервера приходит одним (load).
 */

export type ThemeId =
  | "light"
  | "dark"
  | "system"
  | "blue"
  | "green"
  | "red"
  | "yellow"
  | "banana"
  | "sea"
  | "lilac"
  | "emerald"
  | "peach"
  | "blueberry"
  | "rozovaya"
  | "polnochnaya"
  | "custom";
export type FontWeight = "normal" | "bold";

/** Ключи настраиваемых цветов «Своей темы» */
export type CustomThemeKey =
  | "bg"
  | "containerBg"
  | "sidebar"
  | "topbar"
  | "textPrimary"
  | "textSecondary"
  | "textTertiary"
  | "btnDefault"
  | "btnHover"
  | "btnPress"
  | "tabDefault"
  | "tabHover"
  | "tabActive"
  | "accent";

export type CustomThemeColors = Record<CustomThemeKey, string>;

export const CUSTOM_THEME_DEFAULTS: CustomThemeColors = {
  bg: "#14101d",
  containerBg: "#1c162c",
  sidebar: "#0f0b16",
  topbar: "#14101d",
  textPrimary: "#f3eef5",
  textSecondary: "#cfc4d6",
  textTertiary: "#8b7f96",
  btnDefault: "#231c38",
  btnHover: "#2a2244",
  btnPress: "#332a52",
  tabDefault: "#151023",
  tabHover: "#1c162c",
  tabActive: "#2a2244",
  accent: "#ff7eb3",
};

export const CUSTOM_THEME_GROUPS: { title: string; keys: { key: CustomThemeKey; label: string }[] }[] = [
  {
    title: "Фон и панели",
    keys: [
      { key: "bg", label: "Фон страницы" },
      { key: "containerBg", label: "Фон блоков/карточек" },
      { key: "sidebar", label: "Боковая панель" },
      { key: "topbar", label: "Верхняя панель" },
    ],
  },
  {
    title: "Текст",
    keys: [
      { key: "textPrimary", label: "Основной" },
      { key: "textSecondary", label: "Второстепенный" },
      { key: "textTertiary", label: "Приглушённый" },
    ],
  },
  {
    title: "Кнопки",
    keys: [
      { key: "btnDefault", label: "По умолчанию" },
      { key: "btnHover", label: "При наведении" },
      { key: "btnPress", label: "При нажатии" },
    ],
  },
  {
    title: "Вкладки",
    keys: [
      { key: "tabDefault", label: "Неактивная" },
      { key: "tabHover", label: "При наведении" },
      { key: "tabActive", label: "Активная" },
    ],
  },
  {
    title: "Акцент",
    keys: [{ key: "accent", label: "Акцентный цвет" }],
  },
];

export interface AppearanceState {
  theme: ThemeId;
  /** Акцент на тему: "" -дефолтный акцент темы; иначе #rrggbb */
  themeAccents: Record<ThemeId, string>;
  /** Цвета «Своей темы» */
  customTheme: CustomThemeColors;
  useSharedBackground: boolean;
  background: string;
  fontFamily: string;
  /** Размер основного текста в px: 14 соответствует стандартному размеру сайта */
  fontSize: number;
  lineSpacing: number;
  fontWeight: FontWeight;
  smoothAnimations: boolean;
  scrollEffects: boolean;
  parallaxEffect: boolean;
  truncateNames: boolean;
  compactLists: boolean;
  hideAvatars: boolean;
  showTimeEverywhere: boolean;
  smallEmojis: boolean;
  highContrast: boolean;
}

export const THEME_OPTIONS: { id: ThemeId; label: string }[] = [
  { id: "light", label: "Светлая" },
  { id: "dark", label: "Тёмная" },
  { id: "system", label: "Как в системе" },
  { id: "blue", label: "Синяя" },
  { id: "green", label: "Зелёная" },
  { id: "red", label: "Красная" },
  { id: "yellow", label: "Жёлтая" },
  { id: "banana", label: "Банановая" },
  { id: "sea", label: "Морская" },
  { id: "lilac", label: "Сиренёвая" },
  { id: "emerald", label: "Изумрудная" },
  { id: "peach", label: "Персиковая" },
  { id: "blueberry", label: "Черничная" },
  { id: "rozovaya", label: "Розовая" },
  { id: "polnochnaya", label: "Полночная" },
  { id: "custom", label: "Своя тема" },
];

export const THEME_DEFAULT_ACCENT: Record<ThemeId, string> = {
  dark: "#ff7eb3",
  light: "#ff7eb3",
  system: "#ff7eb3",
  blue: "#5c9fe8",
  green: "#5ec49a",
  red: "#ef5350",
  yellow: "#f5b52e",
  banana: "#e8c547",
  sea: "#3aa8b8",
  lilac: "#b898d9",
  emerald: "#3aa876",
  peach: "#e8a07c",
  blueberry: "#7a7ac8",
  rozovaya: "#f0508a",
  polnochnaya: "#ff5c9d",
  custom: "#ff7eb3",
};

export const ACCENT_PRESETS = [
  "#ff7eb3",
  "#5c9fe8",
  "#5ec49a",
  "#a78bfa",
  "#ffa94d",
  "#ef5350",
  "#ffd54f",
];

export const FONT_OPTIONS = [
  { value: "Inter", label: "Inter (по умолчанию)" },
  { value: "Roboto", label: "Roboto" },
  { value: "Open Sans", label: "Open Sans" },
  { value: "Lato", label: "Lato" },
  { value: "Montserrat", label: "Montserrat" },
  { value: "anime", label: "Noto Sans JP (аниме)" },
  { value: "system", label: "Системный" },
];

export const BACKGROUND_OPTIONS = [
  { value: "default", label: "По умолчанию (без фона)" },
  { value: "gradient", label: "Градиент" },
  { value: "stars", label: "Звёздное небо" },
  { value: "mountains", label: "Горы" },
  { value: "ocean", label: "Океан" },
];

const defaultThemeAccents = (): Record<ThemeId, string> =>
  Object.fromEntries(THEME_OPTIONS.map((t) => [t.id, ""])) as Record<ThemeId, string>;

const DEFAULTS: AppearanceState = {
  theme: "dark",
  themeAccents: defaultThemeAccents(),
  customTheme: { ...CUSTOM_THEME_DEFAULTS },
  useSharedBackground: true,
  background: "default",
  fontFamily: "Inter",
  fontSize: 14,
  lineSpacing: 1.5,
  fontWeight: "normal",
  smoothAnimations: true,
  scrollEffects: true,
  parallaxEffect: false,
  truncateNames: true,
  compactLists: true,
  hideAvatars: false,
  showTimeEverywhere: false,
  smallEmojis: true,
  highContrast: false,
};

const CACHE_KEY = "appearance:v1";
const BASE_ROOT_PX = 16;
const BASE_TEXT_PX = 14;
/** Старые значения по умолчанию из прежних версий: считаем их «не выбрано» */
const LEGACY_ACCENTS = ["#6366f1", "#0084ff"];

const { sakuraEnabled } = useSakuraOverlay();
const { newYearEnabled } = useNewYearOverlay();
const { halloweenEnabled } = useHalloweenOverlay();
const { loveDayEnabled } = useLoveDayOverlay();

const overlayRefs = {
  sakura: sakuraEnabled,
  newYear: newYearEnabled,
  halloween: halloweenEnabled,
  loveDay: loveDayEnabled,
} as const;
type OverlayKey = keyof typeof overlayRefs;
const OVERLAY_API_KEYS: Record<OverlayKey, string> = {
  sakura: "sakura_enabled",
  newYear: "new_year_enabled",
  halloween: "halloween_enabled",
  loveDay: "love_day_enabled",
};
const overlayKeys = Object.keys(overlayRefs) as OverlayKey[];

/** Что лежит на сервере: null -пользователь не выбирал (действует сезонное значение) */
const serverOverlay: Record<OverlayKey, boolean | null> = {
  sakura: null,
  newYear: null,
  halloween: null,
  loveDay: null,
};
/** Значения эффектов на момент последней загрузки/сохранения */
const overlayBaseline: Record<OverlayKey, boolean> = {
  sakura: sakuraEnabled.value,
  newYear: newYearEnabled.value,
  halloween: halloweenEnabled.value,
  loveDay: loveDayEnabled.value,
};

interface Snapshot {
  s: AppearanceState;
  o: Record<OverlayKey, boolean>;
}

const readCache = (): Partial<AppearanceState> => {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Snapshot;
    return parsed && parsed.s ? parsed.s : {};
  } catch {
    return {};
  }
};

const state = reactive<AppearanceState>({ ...DEFAULTS, ...readCache() });

const overlaySnapshot = (): Record<OverlayKey, boolean> => ({
  sakura: sakuraEnabled.value,
  newYear: newYearEnabled.value,
  halloween: halloweenEnabled.value,
  loveDay: loveDayEnabled.value,
});

const takeSnapshot = (): Snapshot => ({ s: { ...state }, o: overlaySnapshot() });

/** Версия настроек, сохранённая на сервере (и в кэше) */
const savedJson = reactive({ value: JSON.stringify(takeSnapshot()) });

const hasChanges = computed(
  () => JSON.stringify(takeSnapshot()) !== savedJson.value,
);

const markSaved = () => {
  const snap = takeSnapshot();
  savedJson.value = JSON.stringify(snap);
  try {
    localStorage.setItem(CACHE_KEY, savedJson.value);
  } catch {
    /* хранилище недоступно: кэш просто не обновится */
  }
};

const HEX_RE = /^#[0-9a-f]{6}$/i;

const hexToRgb = (hex: string): [number, number, number] => {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};

const rgbToHsl = (r: number, g: number, b: number): [number, number, number] => {
  const rn = r / 255;
  const gn = g / 255;
  const bn = b / 255;
  const max = Math.max(rn, gn, bn);
  const min = Math.min(rn, gn, bn);
  const l = (max + min) / 2;
  let h = 0;
  let s = 0;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === rn) h = (gn - bn) / d + (gn < bn ? 6 : 0);
    else if (max === gn) h = (bn - rn) / d + 2;
    else h = (rn - gn) / d + 4;
    h /= 6;
  }
  return [h, s, l];
};

const hslToHex = (h: number, s: number, l: number): string => {
  const hue2rgb = (p: number, q: number, t: number) => {
    let tt = t;
    if (tt < 0) tt += 1;
    if (tt > 1) tt -= 1;
    if (tt < 1 / 6) return p + (q - p) * 6 * tt;
    if (tt < 1 / 2) return q;
    if (tt < 2 / 3) return p + (q - p) * (2 / 3 - tt) * 6;
    return p;
  };
  let r: number;
  let g: number;
  let b: number;
  if (s === 0) {
    r = g = b = l;
  } else {
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1 / 3);
  }
  const toHex = (x: number) => Math.round(x * 255).toString(16).padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
};

const shade = (hex: string, deltaL: number): string => {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  const [h, s, l] = rgbToHsl(...rgb);
  return hslToHex(h, s, Math.min(0.92, Math.max(0.08, l + deltaL)));
};

const luminance = (hex: string): number => {
  const rgb = hexToRgb(hex);
  if (!rgb) return 0;
  const [r, g, b] = rgb.map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
};

const ACCENT_VARS = [
  "--accent",
  "--accent-bright",
  "--accent-hover",
  "--accent-press",
  "--accent-subtle",
  "--accent-glow",
  "--accent-glow-sm",
  "--accent-rgb",
  "--text-on-accent",
  "--shadow-petal",
  "--shadow-petal-sm",
  "--shadow-sm-glow-sm",
  "--border-subtle",
  "--border-default",
  "--border-strong",
];

const applyAccent = (root: HTMLElement, accent: string, resolvedTheme: string) => {
  if (!HEX_RE.test(accent)) {
    ACCENT_VARS.forEach((v) => root.style.removeProperty(v));
    return;
  }
  const rgb = hexToRgb(accent);
  if (!rgb) return;
  const [r, g, b] = rgb;
  const rgba = (a: number) => `rgba(${r}, ${g}, ${b}, ${a})`;
  const set = (k: string, v: string) => root.style.setProperty(k, v);

  set("--accent", accent);
  set("--accent-bright", shade(accent, 0.14));
  set("--accent-hover", shade(accent, 0.06));
  set("--accent-press", shade(accent, -0.08));
  set("--accent-subtle", rgba(0.12));
  set("--accent-glow", rgba(0.3));
  set("--accent-glow-sm", rgba(0.15));
  set("--accent-rgb", `${r}, ${g}, ${b}`);
  set("--text-on-accent", luminance(accent) > 0.4 ? "#1a0a14" : "#ffffff");
  set("--shadow-petal", `0 4px 20px ${rgba(0.2)}`);
  set("--shadow-petal-sm", `0 2px 10px ${rgba(0.12)}`);
  set("--shadow-sm-glow-sm", `0 0 8px ${rgba(0.12)}`);

  if (resolvedTheme === "light") {
    ["--border-subtle", "--border-default", "--border-strong"].forEach((v) =>
      root.style.removeProperty(v),
    );
  } else {
    set("--border-subtle", rgba(0.07));
    set("--border-default", rgba(0.13));
    set("--border-strong", rgba(0.25));
  }
};

/**
 * «Своя тема»: поверхности, текст и схема (light/dark) выводятся из базового
 * цвета фона. Возвращает true, если получившаяся схема светлая.
 */
const hslCss = (h: number, s: number, l: number) =>
  `hsl(${(h * 360).toFixed(0)}, ${(s * 100).toFixed(0)}%, ${(l * 100).toFixed(0)}%)`;

const CUSTOM_THEME_VARS = [
  "--panel-sidebar",
  "--panel-topbar",
  "--btn-default",
  "--btn-hover",
  "--btn-press",
  "--tab-default",
  "--tab-hover",
  "--tab-active",
  "--tab-active-text",
  "--container-bg",
  "--page-bg",
] as const;

/**
 * «Своя тема»: поверхности выводятся из базового цвета фона, остальное -
 * из выбранных пользователем цветов. Возвращает true, если схема светлая.
 */
const applyCustomTheme = (root: HTMLElement, c: CustomThemeColors): boolean => {
  const base = HEX_RE.test(c.containerBg) ? c.containerBg : CUSTOM_THEME_DEFAULTS.containerBg;
  const rgb = hexToRgb(base);
  if (!rgb) return false;
  const [r, g, b] = rgb;
  const [h, s] = rgbToHsl(r, g, b);
  const sat = Math.min(s, 0.45);
  const set = (k: string, v: string) => root.style.setProperty(k, v);

  for (let i = 0; i <= 6; i++) {
    set(`--surface-${i}`, shade(base, (i - 3) * 0.05));
  }

  const hexOr = (v: string, fallback: string) => (HEX_RE.test(v) ? v : fallback);
  set("--text-primary", hexOr(c.textPrimary, hslCss(h, sat * 0.35, 0.93)));
  set("--text-secondary", hexOr(c.textSecondary, hslCss(h, sat * 0.3, 0.78)));
  set("--text-tertiary", hexOr(c.textTertiary, hslCss(h, sat * 0.25, 0.6)));
  set(
    "--text-disabled",
    shade(hexOr(c.textTertiary, CUSTOM_THEME_DEFAULTS.textTertiary), -0.15),
  );
  set("--panel-sidebar", hexOr(c.sidebar, CUSTOM_THEME_DEFAULTS.sidebar));
  set("--panel-topbar", hexOr(c.topbar, CUSTOM_THEME_DEFAULTS.topbar));
  set("--container-bg", hexOr(c.containerBg, CUSTOM_THEME_DEFAULTS.containerBg));
  set("--page-bg", hexOr(c.bg, CUSTOM_THEME_DEFAULTS.bg));
  set("--btn-default", hexOr(c.btnDefault, CUSTOM_THEME_DEFAULTS.btnDefault));
  set("--btn-hover", hexOr(c.btnHover, CUSTOM_THEME_DEFAULTS.btnHover));
  set("--btn-press", hexOr(c.btnPress, CUSTOM_THEME_DEFAULTS.btnPress));
  set("--tab-default", hexOr(c.tabDefault, CUSTOM_THEME_DEFAULTS.tabDefault));
  set("--tab-hover", hexOr(c.tabHover, CUSTOM_THEME_DEFAULTS.tabHover));
  const tabActive = hexOr(c.tabActive, CUSTOM_THEME_DEFAULTS.tabActive);
  set("--tab-active", tabActive);
  set("--tab-active-text", luminance(tabActive) > 0.4 ? "#1a0a14" : "#ffffff");

  return luminance(base) > 0.4;
};

const JP_FALLBACK = '"Noto Sans JP", "Zen Kaku Gothic New", sans-serif';
const GOOGLE_FONTS: Record<string, string> = {
  Roboto: "Roboto:wght@300;400;500;600;700",
  "Open Sans": "Open+Sans:wght@300;400;500;600;700",
  Lato: "Lato:wght@300;400;700;900",
  Montserrat: "Montserrat:wght@300;400;500;600;700",
};

const fontStack = (family: string): string | null => {
  switch (family) {
    case "Inter":
      return null; // стандартный шрифт сайта (--font-sans из base.css)
    case "system":
      return `system-ui, -apple-system, "Segoe UI", ${JP_FALLBACK}`;
    case "anime":
      return `"Noto Sans JP", "Zen Kaku Gothic New", "Inter", sans-serif`;
    default:
      return `"${family}", ${JP_FALLBACK}`;
  }
};

const ensureFontLoaded = (family: string) => {
  const query = GOOGLE_FONTS[family];
  const id = "appearance-font";
  const existing = document.getElementById(id) as HTMLLinkElement | null;
  if (!query) {
    existing?.remove();
    return;
  }
  const href = `https://fonts.googleapis.com/css2?family=${query}&display=swap`;
  if (existing) {
    if (existing.href !== href) existing.href = href;
    return;
  }
  const link = document.createElement("link");
  link.id = id;
  link.rel = "stylesheet";
  link.href = href;
  document.head.appendChild(link);
};

const prefersLight = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-color-scheme: light)").matches;

/** Тема после раскрытия "system" -все темы, кроме системной. */
type ResolvedTheme = Exclude<ThemeId, "system">;

const resolveTheme = (theme: ThemeId): ResolvedTheme => {
  if (theme === "system") return prefersLight() ? "light" : "dark";
  return theme;
};

const specialThemeLoads = new Map<string, Promise<unknown>>();
const ensureSpecialThemeStyles = (theme: ResolvedTheme) => {
  if (theme !== 'rozovaya' && theme !== 'polnochnaya' || specialThemeLoads.has(theme)) return;
  const load = theme === 'rozovaya'
    ? import('@/assets/theme-rozovaya.css')
    : import('@/assets/theme-polnochnaya.css');
  specialThemeLoads.set(theme, load);
};

const setFlag = (root: HTMLElement, name: string, value: boolean) =>
  root.setAttribute(name, value ? "true" : "false");

const setOrRemove = (root: HTMLElement, name: string, value: string | null) => {
  if (value === null) root.style.removeProperty(name);
  else root.style.setProperty(name, value);
};

export const applyAppearance = () => {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  const resolved = resolveTheme(state.theme);
  ensureSpecialThemeStyles(resolved);

  root.setAttribute("data-theme", resolved);
  root.setAttribute("data-theme-pref", state.theme);

  let isLight = resolved === "light";
  if (resolved === "custom") {
    isLight = applyCustomTheme(root, state.customTheme);
  } else {
    for (let i = 0; i <= 6; i++) root.style.removeProperty(`--surface-${i}`);
    [
      "--text-primary",
      "--text-secondary",
      "--text-tertiary",
      "--text-disabled",
      ...CUSTOM_THEME_VARS,
    ].forEach((v) => root.style.removeProperty(v));
  }
  root.style.colorScheme = isLight ? "light" : "dark";
  applyAccent(root, effectiveAccent.value, isLight ? "light" : "dark");

  const fontFamily = state.fontFamily;
  afterInitialContent(() => ensureFontLoaded(fontFamily));
  setOrRemove(root, "--font-sans", fontStack(state.fontFamily));
  setOrRemove(
    root,
    "font-size",
    state.fontSize === BASE_TEXT_PX
      ? null
      : `${((BASE_ROOT_PX * state.fontSize) / BASE_TEXT_PX).toFixed(2)}px`,
  );
  setOrRemove(
    root,
    "--user-line-height",
    state.lineSpacing === DEFAULTS.lineSpacing ? null : String(state.lineSpacing),
  );
  setOrRemove(root, "--user-font-weight", state.fontWeight === "bold" ? "600" : null);

  setFlag(root, "data-high-contrast", state.highContrast);
  setFlag(root, "data-reduce-motion", !state.smoothAnimations);
  setFlag(root, "data-scroll-effects", state.scrollEffects && state.smoothAnimations);
  setFlag(root, "data-parallax", state.parallaxEffect && state.smoothAnimations);
  setFlag(root, "data-truncate-names", state.truncateNames);
  setFlag(root, "data-compact-lists", state.compactLists);
  setFlag(root, "data-hide-avatars", state.hideAvatars);
  setFlag(root, "data-show-time", state.showTimeEverywhere);
  setFlag(root, "data-small-emojis", state.smallEmojis);
  root.setAttribute(
    "data-chat-bg",
    state.useSharedBackground ? state.background || "default" : "default",
  );

  setScrollRevealEnabled(state.scrollEffects && state.smoothAnimations);
};

const normalizeAccent = (value: unknown): string => {
  if (typeof value !== "string") return "";
  const v = value.trim().toLowerCase();
  if (!HEX_RE.test(v) || LEGACY_ACCENTS.includes(v)) return "";
  return v;
};

const pickBool = (value: unknown, fallback: boolean): boolean =>
  typeof value === "boolean" ? value : fallback;

const clampNum = (value: unknown, min: number, max: number, fallback: number) => {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : fallback;
};

const hydrate = (d: Record<string, unknown>) => {
  const themeIds = THEME_OPTIONS.map((t) => t.id) as string[];
  const fontIds = FONT_OPTIONS.map((f) => f.value);
  const bgIds = BACKGROUND_OPTIONS.map((b) => b.value);

  state.theme = (themeIds.includes(d.theme as string) ? d.theme : DEFAULTS.theme) as ThemeId;

  const themeAccents = defaultThemeAccents();
  const rawAccents = (
    d.theme_accents && typeof d.theme_accents === "object" ? d.theme_accents : {}
  ) as Record<string, unknown>;
  THEME_OPTIONS.forEach((t) => {
    const v = rawAccents[t.id];
    if (typeof v === "string" && HEX_RE.test(v)) themeAccents[t.id] = v.toLowerCase();
  });
  const legacyAccent = normalizeAccent(d.accent_color);
  if (legacyAccent && !themeAccents[state.theme]) themeAccents[state.theme] = legacyAccent;
  state.themeAccents = themeAccents;

  const customTheme = { ...CUSTOM_THEME_DEFAULTS };
  const rawCustom = (
    d.custom_theme && typeof d.custom_theme === "object" ? d.custom_theme : {}
  ) as Record<string, unknown>;
  (Object.keys(customTheme) as CustomThemeKey[]).forEach((k) => {
    const v = rawCustom[k];
    if (typeof v === "string" && HEX_RE.test(v)) customTheme[k] = v.toLowerCase();
  });
  state.customTheme = customTheme;
  state.useSharedBackground = pickBool(d.use_shared_background, DEFAULTS.useSharedBackground);
  state.background = bgIds.includes(d.custom_background as string)
    ? (d.custom_background as string)
    : "default";
  state.fontFamily = fontIds.includes(d.font_family as string)
    ? (d.font_family as string)
    : DEFAULTS.fontFamily;
  state.fontSize = Math.round(clampNum(d.font_size, 12, 18, DEFAULTS.fontSize));
  state.lineSpacing = Math.round(clampNum(d.line_spacing, 1, 1.8, DEFAULTS.lineSpacing) * 10) / 10;
  state.fontWeight = d.font_weight === "bold" ? "bold" : "normal";

  state.smoothAnimations = pickBool(d.smooth_animations, DEFAULTS.smoothAnimations);
  state.scrollEffects = pickBool(d.scroll_effects, DEFAULTS.scrollEffects);
  state.parallaxEffect = pickBool(d.parallax_effect, DEFAULTS.parallaxEffect);
  state.truncateNames = pickBool(d.truncate_names, DEFAULTS.truncateNames);
  state.compactLists = pickBool(d.compact_lists, DEFAULTS.compactLists);
  state.hideAvatars = pickBool(d.hide_avatars, DEFAULTS.hideAvatars);
  state.showTimeEverywhere = pickBool(d.show_time_everywhere, DEFAULTS.showTimeEverywhere);
  state.smallEmojis = pickBool(d.small_emojis, DEFAULTS.smallEmojis);
  state.highContrast = pickBool(d.high_contrast, DEFAULTS.highContrast);

  overlayKeys.forEach((key) => {
    const fromServer = d[OVERLAY_API_KEYS[key]];
    if (typeof fromServer === "boolean") {
      overlayRefs[key].value = fromServer;
      serverOverlay[key] = fromServer;
    } else {
      serverOverlay[key] = null;
    }
    overlayBaseline[key] = overlayRefs[key].value;
  });

  applyAppearance();
  markSaved();
};

export const loadAppearanceFromServer = async () => {
  try {
    const data = await settingsApi.getThemeSettings();
    hydrate(data as Record<string, unknown>);
  } catch (error) {
    if (isRequestCancelled(error)) return;
    console.error("Error fetching appearance settings:", error);
  }
};

export const saveAppearance = async () => {
  const payload: Record<string, unknown> = {
    theme: state.theme,
    theme_accents: state.themeAccents,
    accent_color: "",
    custom_theme: state.customTheme,
    use_shared_background: state.useSharedBackground,
    custom_background: state.background,
    font_family: state.fontFamily,
    font_size: state.fontSize,
    line_spacing: state.lineSpacing,
    font_weight: state.fontWeight,
    smooth_animations: state.smoothAnimations,
    scroll_effects: state.scrollEffects,
    parallax_effect: state.parallaxEffect,
    truncate_names: state.truncateNames,
    compact_lists: state.compactLists,
    hide_avatars: state.hideAvatars,
    show_time_everywhere: state.showTimeEverywhere,
    small_emojis: state.smallEmojis,
    high_contrast: state.highContrast,
  };

  const sent: OverlayKey[] = [];
  overlayKeys.forEach((key) => {
    const current = overlayRefs[key].value;
    if (serverOverlay[key] !== null || current !== overlayBaseline[key]) {
      payload[OVERLAY_API_KEYS[key]] = current;
      sent.push(key);
    }
  });

  let response: Record<string, unknown>;
  try {
    response = (await settingsApi.updateThemeSettings(payload)) as Record<
      string,
      unknown
    >;
  } catch (error) {
    throw new Error(appearanceErrorText(error));
  }

  if (response && typeof response === "object") {
    hydrate(response);
  }

  sent.forEach((key) => {
    serverOverlay[key] = overlayRefs[key].value;
  });
  overlayKeys.forEach((key) => {
    overlayBaseline[key] = overlayRefs[key].value;
  });
  markSaved();
};

/** Текст ошибки сохранения: detail/errors от DRF, иначе общий. */
const appearanceErrorText = (error: unknown): string => {
  const data = (
    error as {
      response?: { status?: number; data?: { detail?: string; errors?: Record<string, string> } };
    }
  )?.response?.data;
  if (data?.detail) return data.detail;
  if (data?.errors) {
    return Object.entries(data.errors)
      .map(([field, text]) => `${field}: ${text}`)
      .join("; ");
  }
  const status = (error as { response?: { status?: number } })?.response?.status;
  if (status === 403) return "Нет доступа к сохранению настроек (403)";
  if (status === 401) return "Сессия истекла, войдите заново";
  return (error as { message?: string })?.message || "Не удалось сохранить оформление";
};

/** Откатить несохранённые изменения к последней сохранённой версии */
export const revertAppearance = () => {
  try {
    const snap = JSON.parse(savedJson.value) as Snapshot;
    Object.assign(state, snap.s);
    overlayKeys.forEach((key) => {
      overlayRefs[key].value = snap.o[key];
    });
  } catch {
    Object.assign(state, DEFAULTS);
  }
  applyAppearance();
};

/** Сброс при выходе из аккаунта: чужие настройки не должны остаться в браузере */
export const resetAppearance = () => {
  Object.assign(state, DEFAULTS);
  try {
    localStorage.removeItem(CACHE_KEY);
  } catch {
    /* ничего */
  }
  savedJson.value = JSON.stringify(takeSnapshot());
  applyAppearance();
};

let initialized = false;

/** Вызывается один раз при старте приложения (до монтирования) */
export const initAppearance = () => {
  if (initialized || typeof window === "undefined") return;
  initialized = true;

  applyAppearance();
  watch(state, applyAppearance, { deep: true, flush: "sync" });

  const media = window.matchMedia("(prefers-color-scheme: light)");
  media.addEventListener("change", () => {
    if (state.theme === "system") applyAppearance();
  });
};

/** Акцент текущей темы: своё значение (если задано) или дефолтный акцент темы */
export const effectiveAccent = computed(
  () =>
    state.themeAccents[state.theme] ||
    THEME_DEFAULT_ACCENT[state.theme] ||
    THEME_DEFAULT_ACCENT.dark,
);

export function useAppearance() {
  const setTheme = (theme: ThemeId) => {
    state.theme = theme;
  };
  /** Ставит акцент ТЕКУЩЕЙ теме; "" -вернуть дефолтный акцент темы */
  const setAccentColor = (color: string) => {
    state.themeAccents[state.theme] = HEX_RE.test(color) ? color.toLowerCase() : "";
  };

  return {
    ...toRefs(state),
    hasChanges,
    effectiveAccent,
    setTheme,
    setAccentColor,
    save: saveAppearance,
    cancel: revertAppearance,
    load: loadAppearanceFromServer,
  };
}
