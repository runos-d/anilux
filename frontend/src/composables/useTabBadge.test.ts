import { effectScope, nextTick, ref } from 'vue';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useTabBadge } from './useTabBadge';
vi.mock('@/utils/faviconBadge', () => ({ updateFaviconBadge: vi.fn() }));
describe('browser tab attention', () => {
  afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.useRealTimers(); });
  it('flashes on unread background messages, restores on focus and stops after disposal', async () => {
    vi.useFakeTimers(); document.title = 'AniLux';
    vi.spyOn(document, 'hasFocus').mockReturnValue(false);
    const setAppBadge = vi.fn().mockResolvedValue(undefined), clearAppBadge = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'setAppBadge', { configurable: true, value: setAppBadge });
    Object.defineProperty(navigator, 'clearAppBadge', { configurable: true, value: clearAppBadge });
    const unread = ref(0), scope = effectScope();
    scope.run(() => useTabBadge(unread));
    unread.value = 2; await nextTick();
    await vi.advanceTimersByTimeAsync(1000); expect(document.title).toBe('(2) Новое уведомление');
    await vi.advanceTimersByTimeAsync(1000); expect(document.title).toBe('(2) AniLux');
    expect(setAppBadge).toHaveBeenCalledWith(2);
    vi.spyOn(document, 'hidden', 'get').mockReturnValue(false);
    vi.spyOn(document, 'hasFocus').mockReturnValue(true);
    window.dispatchEvent(new Event('focus'));
    await vi.advanceTimersByTimeAsync(1000); expect(document.title).toBe('(2) AniLux');
    unread.value = 0; await nextTick(); expect(clearAppBadge).toHaveBeenCalled();
    scope.stop(); expect(document.title).toBe('AniLux'); expect(vi.getTimerCount()).toBe(0);
    delete (navigator as unknown as Record<string, unknown>).setAppBadge;
    delete (navigator as unknown as Record<string, unknown>).clearAppBadge;
  });
});
