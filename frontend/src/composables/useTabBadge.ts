import { onScopeDispose, unref, watch, type Ref } from 'vue';
import { updateFaviconBadge } from '@/utils/faviconBadge';

export function useTabBadge(unread: number | Ref<number>, disabled = false) {
  let baseTitle = document.title.replace(/^\(\d+\)\s*/, '');
  let ownTitle = document.title;
  let timer: ReturnType<typeof setInterval> | null = null;
  let flash = false;
  const count = () => disabled ? 0 : Math.max(0, unref(unread));
  const write = (title: string) => { ownTitle = title; document.title = title; };
  const normalTitle = () => count() > 0 ? `(${count()}) ${baseTitle}` : baseTitle;
  const stop = () => { if (timer) clearInterval(timer); timer = null; flash = false; write(normalTitle()); updateFaviconBadge(count()); };
  const start = () => {
    if (disabled || timer || !count() || (!document.hidden && document.hasFocus())) return;
    timer = setInterval(() => {
      flash = !flash;
      write(flash ? `(${count()}) Новое уведомление` : normalTitle());
      updateFaviconBadge(flash ? count() : 0);
    }, 1000);
  };
  const observer = new MutationObserver(() => {
    if (document.title !== ownTitle) { baseTitle = document.title.replace(/^\(\d+\)\s*/, ''); write(normalTitle()); }
  });
  const title = document.querySelector('title');
  if (title) observer.observe(title, { subtree: true, childList: true, characterData: true });
  const syncVisibility = () => { if (!document.hidden && document.hasFocus()) stop(); };
  window.addEventListener('focus', syncVisibility);
  document.addEventListener('visibilitychange', syncVisibility);
  window.addEventListener('browserAttention', start);
  watch(() => unref(unread), (value, previous) => {
    write(normalTitle()); updateFaviconBadge(count());
    const badge = navigator as Navigator & { setAppBadge?: (count: number) => Promise<void>; clearAppBadge?: () => Promise<void> };
    const update = count() > 0 ? badge.setAppBadge?.(count()) : badge.clearAppBadge?.();
    update?.catch(() => {});
    if (!count()) stop();
    else if (previous !== undefined && value > previous) start();
  }, { immediate: true });
  onScopeDispose(() => {
    observer.disconnect();
    window.removeEventListener('focus', syncVisibility);
    document.removeEventListener('visibilitychange', syncVisibility);
    window.removeEventListener('browserAttention', start);
    if (timer) clearInterval(timer);
    write(baseTitle); updateFaviconBadge(0);
  });
}
