import { onMounted, onUnmounted } from 'vue';

/** Keep fixed chat/forms inside the visible area when a phone keyboard opens. */
export function useVisualViewport() {
  const viewport = window.visualViewport;
  const update = () => {
    const height = viewport?.height ?? window.innerHeight;
    document.documentElement.style.setProperty('--viewport-height', `${height}px`);
    document.documentElement.style.setProperty('--viewport-top', `${viewport?.offsetTop ?? 0}px`);
  };
  onMounted(() => {
    update();
    window.addEventListener('resize', update);
    viewport?.addEventListener('resize', update);
    viewport?.addEventListener('scroll', update);
  });
  onUnmounted(() => {
    window.removeEventListener('resize', update);
    viewport?.removeEventListener('resize', update);
    viewport?.removeEventListener('scroll', update);
    document.documentElement.style.removeProperty('--viewport-height');
    document.documentElement.style.removeProperty('--viewport-top');
  });
}
