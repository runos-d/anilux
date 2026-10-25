import { ref, watch } from "vue";

const STORAGE_KEY = "newYearOverlayEnabled";

const isNewYearSeason = (): boolean => {
  const now = new Date();
  return now.getMonth() === 11 || (now.getMonth() === 0 && now.getDate() <= 20);
};

const readInitial = (): boolean => {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === null ? isNewYearSeason() : value === "true";
  } catch {
    return isNewYearSeason();
  }
};

const newYearEnabled = ref<boolean>(readInitial());

watch(newYearEnabled, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    /* хранилище недоступно: настройка живёт до перезагрузки */
  }
});

if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEY) newYearEnabled.value = event.newValue === "true";
  });
}

export function useNewYearOverlay() {
  return { newYearEnabled };
}
