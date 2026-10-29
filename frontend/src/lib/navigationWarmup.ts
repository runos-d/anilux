type Loader = () => Promise<unknown>;
type NetworkInfo = { saveData?: boolean; effectiveType?: string };

/** Warm code only: no speculative account or page-data requests. */
export function installNavigationWarmup(loaders: Record<string, Loader>) {
  const pending = new Map<string, Promise<unknown>>();
  let disposed = false;
  const warm = (path: string) => {
    if (disposed || !loaders[path] || pending.has(path)) return;
    const promise = Promise.resolve().then(loaders[path]);
    pending.set(path, promise);
    void promise.catch(() => pending.delete(path));
  };
  const intent = (event: Event) => {
    const anchor = event.target instanceof Element ? event.target.closest('a[href]') : null;
    if (!(anchor instanceof HTMLAnchorElement) || anchor.download || (anchor.target && anchor.target !== '_self')) return;
    const url = new URL(anchor.href, location.href);
    if (url.origin === location.origin) warm(url.pathname.replace(/\/$/, '') || '/');
  };
  const events = ['pointerover', 'focusin', 'touchstart'] as const;
  for (const event of events) document.addEventListener(event, intent, { capture: true, passive: true });
  const background = () => {
    const network = (navigator as Navigator & { connection?: NetworkInfo }).connection;
    if (disposed || document.hidden || network?.saveData || /(^|-)2g$/.test(network?.effectiveType || '')) return;
    // Two frequent destinations; their dialogs and heavy tools remain lazy.
    for (const path of Object.keys(loaders).slice(0, 2)) warm(path);
  };
  const idle = typeof requestIdleCallback === 'function' ? requestIdleCallback(background, { timeout: 3000 }) : undefined;
  const timer = idle === undefined ? setTimeout(background, 200) : undefined;
  return () => {
    disposed = true;
    if (idle !== undefined) cancelIdleCallback(idle);
    if (timer !== undefined) clearTimeout(timer);
    for (const event of events) document.removeEventListener(event, intent, true);
  };
}
