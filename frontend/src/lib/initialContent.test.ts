import { beforeEach, afterEach, expect, it, vi } from 'vitest';
const cache = vi.hoisted(() => ({ listener: null as ((event: unknown) => void) | null, unsubscribe: vi.fn() }));
vi.mock('./queryClient', () => ({ queryClient: { getQueryCache: () => ({ subscribe: (listener: (event: unknown) => void) => {
  cache.listener = listener; return cache.unsubscribe;
} }) } }));
beforeEach(() => {
  vi.useFakeTimers(); vi.resetModules(); cache.unsubscribe.mockClear();
  vi.stubGlobal('requestAnimationFrame', (callback: () => void) => setTimeout(callback, 16));
});
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });
const success = (key: unknown[]) => cache.listener?.({ type:'updated', action:{ type:'success' }, query:{ queryKey:key } });

it('starts background work after content renders, ignoring settings responses', async () => {
  const { afterInitialContent } = await import('./initialContent');
  const task = vi.fn(); afterInitialContent(task);
  success(['read','public','catalog-settings']); vi.advanceTimersByTime(100);
  expect(task).not.toHaveBeenCalled();
  success(['read','public','catalog']);
  vi.advanceTimersByTime(16); expect(task).not.toHaveBeenCalled();
  vi.advanceTimersByTime(16); expect(task).toHaveBeenCalledTimes(1);
  expect(cache.unsubscribe).toHaveBeenCalledTimes(1);
});

it('still starts account checks when a page has no cached content query', async () => {
  const { afterInitialContent } = await import('./initialContent');
  const task = vi.fn(); afterInitialContent(task);
  vi.advanceTimersByTime(1599); expect(task).not.toHaveBeenCalled();
  vi.advanceTimersByTime(33); expect(task).toHaveBeenCalledTimes(1);
  afterInitialContent(task); expect(task).toHaveBeenCalledTimes(2);
});
