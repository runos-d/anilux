import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { effectScope } from 'vue';
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({user:{id:424}}) }));
vi.mock('@/lib/publicReadCache', () => ({ publicCacheReady:Promise.resolve() }));
import { queryClient } from '@/lib/queryClient';
import { useCachedReads } from './useCachedReads';
import { isRequestCancelled } from '@/api/client';
let scope: ReturnType<typeof effectScope>;
beforeEach(() => { queryClient.clear(); scope=effectScope(); });
afterEach(() => { scope.stop(); queryClient.clear(); });
it('replaces an older in-flight response when a mutation invalidates the screen', async () => {
  const read=scope.run(useCachedReads)!;
  let resolveOld: (value:string) => void = () => {};
  const fetch=vi.fn().mockImplementationOnce(() => new Promise<string>(resolve => {resolveOld=resolve;})).mockResolvedValue('ready photo');
  const assign=vi.fn();
  const first=read(['feed'],fetch,assign).catch(() => undefined);
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  await queryClient.invalidateQueries({queryKey:['read','424','feed']});
  await vi.waitFor(() => expect(assign).toHaveBeenCalledWith('ready photo'));
  resolveOld('stale feed'); await first;
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(assign).not.toHaveBeenCalledWith('stale feed');
});
it('does not fetch an invisible retained screen and refreshes it when reopened', async () => {
  let visible=true;
  const read=scope.run(() => useCachedReads(() => visible))!;
  const fetch=vi.fn().mockResolvedValueOnce('first').mockResolvedValue('updated');
  const assign=vi.fn(); await read(['feed'],fetch,assign);
  visible=false; await queryClient.invalidateQueries({queryKey:['read','424','feed']});
  expect(fetch).toHaveBeenCalledTimes(1);
  visible=true; await read(['feed'],fetch,assign);
  await vi.waitFor(() => expect(assign).toHaveBeenCalledWith('updated'));
  expect(fetch).toHaveBeenCalledTimes(2);
});
it('aborts a superseded filter request without cancelling the new query', async () => {
  const read=scope.run(useCachedReads)!;
  let oldSignal: AbortSignal | undefined;
  let cancelled: unknown;
  const pending=read(['catalog','old'], signal => {
    oldSignal=signal;
    return new Promise<string>(() => {});
  },vi.fn()).catch(error => { cancelled = error; });
  await vi.waitFor(() => expect(oldSignal).toBeDefined());
  const assign=vi.fn();
  await read(['catalog','new'], async signal => {
    expect(signal?.aborted).toBe(false); return 'new results';
  },assign);
  await pending;
  expect(oldSignal?.aborted).toBe(true);
  expect(isRequestCancelled(cancelled)).toBe(true);
  expect(assign).toHaveBeenCalledWith('new results');
});
