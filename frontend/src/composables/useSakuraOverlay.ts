import { ref, watch } from "vue";

const STORAGE_KEY = "sakuraOverlayEnabled";

const readInitial = (): boolean => {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === null ? false : value === "true";
  } catch {
    return false;
  }
};

const sakuraEnabled = ref<boolean>(readInitial());

watch(sakuraEnabled, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    /* хранилище недоступно: настройка живёт до перезагрузки */
  }
});

if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEY) sakuraEnabled.value = event.newValue !== "false";
  });
}

export function useSakuraOverlay() {
  return { sakuraEnabled };
}
