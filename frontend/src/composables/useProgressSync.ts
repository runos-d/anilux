import { ref, watch, type Ref } from "vue";

const progressVersion: Ref<number> = ref(0);

export function useProgressSync() {
  const bump = (): void => {
    progressVersion.value += 1;
  };

  const watchVersion = (callback: () => void | Promise<void>): void => {
    watch(progressVersion, callback);
  };

  return { bump, watchVersion };
}
