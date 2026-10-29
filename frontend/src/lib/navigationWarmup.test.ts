import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { installNavigationWarmup } from './navigationWarmup';
let dispose: (() => void) | undefined;
beforeEach(() => { vi.useFakeTimers(); Object.defineProperty(document, 'hidden', { configurable:true, value:false }); });
afterEach(() => { dispose?.(); dispose=undefined; document.body.innerHTML=''; Object.defineProperty(navigator,'connection',{configurable:true,value:undefined}); vi.useRealTimers(); });
it('warms each main destination once after content and shares pointer/focus intent', async () => {
  const load=vi.fn().mockResolvedValue({}); dispose=installNavigationWarmup({'/feed':load});
  document.body.innerHTML='<a href="/feed">Feed</a>'; const link=document.querySelector('a')!;
  link.dispatchEvent(new Event('pointerover',{bubbles:true})); link.dispatchEvent(new Event('focusin',{bubbles:true}));
  await vi.advanceTimersByTimeAsync(500); expect(load).toHaveBeenCalledTimes(1);
});
it('respects data saving and ignores external navigation', async () => {
  Object.defineProperty(navigator,'connection',{configurable:true,value:{saveData:true}});
  const load=vi.fn().mockResolvedValue({}); dispose=installNavigationWarmup({'/feed':load});
  document.body.innerHTML='<a href="https://example.test/feed">External</a>';
  document.querySelector('a')!.dispatchEvent(new Event('pointerover',{bubbles:true}));
  await vi.advanceTimersByTimeAsync(500); expect(load).not.toHaveBeenCalled();
  document.querySelector('a')!.href='/feed'; document.querySelector('a')!.dispatchEvent(new Event('touchstart',{bubbles:true}));
  await vi.advanceTimersByTimeAsync(0); expect(load).toHaveBeenCalledTimes(1);
});
it('does not start queued background imports after cleanup', async () => {
  const load=vi.fn(); dispose=installNavigationWarmup({'/anime':load}); dispose();
  await vi.advanceTimersByTimeAsync(500); expect(load).not.toHaveBeenCalled();
});
