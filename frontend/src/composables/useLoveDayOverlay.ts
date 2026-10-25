import { ref, watch } from "vue";

const STORAGE_KEY = "loveDayOverlayEnabled";

const isLoveDaySeason = (): boolean => {
  return new Date().getMonth() === 1;
};

const readInitial = (): boolean => {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === null ? isLoveDaySeason() : value === "true";
  } catch {
    return isLoveDaySeason();
  }
};

const loveDayEnabled = ref<boolean>(readInitial());

watch(loveDayEnabled, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    /* хранилище недоступно: настройка живёт до перезагрузки */
  }
});

if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEY) loveDayEnabled.value = event.newValue === "true";
  });
}

export function useLoveDayOverlay() {
  return { loveDayEnabled };
}
