import { ref, watch } from "vue";

const STORAGE_KEY = "halloweenOverlayEnabled";

const isHalloweenSeason = (): boolean => {
  const now = new Date();
  return now.getMonth() === 9 || (now.getMonth() === 10 && now.getDate() <= 2);
};

const readInitial = (): boolean => {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === null ? isHalloweenSeason() : value === "true";
  } catch {
    return isHalloweenSeason();
  }
};

const halloweenEnabled = ref<boolean>(readInitial());

watch(halloweenEnabled, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    /* хранилище недоступно: настройка живёт до перезагрузки */
  }
});

if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEY) halloweenEnabled.value = event.newValue === "true";
  });
}

export function useHalloweenOverlay() {
  return { halloweenEnabled };
}
