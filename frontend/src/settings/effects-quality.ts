/**
 * Локальная настройка качества эффектов (без нового поля API).
 * Ключ в localStorage: effects_quality
 * Значения: "auto" | "high" | "light" | "off"
 * Без взаимодействия с сервером -только предпросмотр.
 */
const STORAGE_KEY = "effects_quality";

export type EffectsQuality = "auto" | "high" | "light" | "off";

export function readQuality(): EffectsQuality {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === "high" || raw === "light" || raw === "off") return raw as EffectsQuality;
    return "auto";
  } catch {
    return "auto";
  }
}

export function writeQuality(q: EffectsQuality): void {
  try {
    localStorage.setItem(STORAGE_KEY, q);
  } catch {
  }
}
