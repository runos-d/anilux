import { onScopeDispose, watch, type WatchSource } from 'vue';

const locks = new Set<symbol>();
let previous = '';

/** Nested overlays release only their own lock and restore the original body style. */
export function useScrollLock(open: WatchSource<boolean>) {
  const key = Symbol('overlay');
  const release = () => {
    if (!locks.delete(key)) return;
    if (!locks.size) document.body.style.overflow = previous;
  };
  watch(open, value => {
    if (!value) return release();
    if (locks.has(key)) return;
    if (!locks.size) previous = document.body.style.overflow;
    locks.add(key);
    document.body.style.overflow = 'hidden';
  }, { immediate: true, flush: 'sync' });
  onScopeDispose(release);
}
