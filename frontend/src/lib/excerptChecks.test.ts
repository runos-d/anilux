import { afterEach, expect, it, vi } from 'vitest';
import type { Excerpt } from '@/api/excerpts';
const post = vi.hoisted(() => vi.fn(async () => ({ data: { results: [] } })));
vi.mock('@/api/client', () => ({ default: { post } }));
import { registerExcerptCheck } from './excerptChecks';

afterEach(() => { vi.useRealTimers(); post.mockClear(); });
it('batches and deduplicates visible cards without a mount request', async () => {
  vi.useFakeTimers();
  const value = { id: 1, share_path: '/excerpts/s/a-token' } as Excerpt;
  const first = registerExcerptCheck(value, false, vi.fn());
  const second = registerExcerptCheck(value, false, vi.fn());
  first.visible(true); second.visible(true);
  expect(post).not.toHaveBeenCalled();
  await vi.advanceTimersByTimeAsync(60_000);
  expect(post).toHaveBeenCalledOnce();
  expect((post.mock.calls[0] as unknown as [string, { items: unknown[] }])[1].items).toHaveLength(1);
  first.stop(); second.stop();
  await vi.advanceTimersByTimeAsync(60_000);
  expect(post).toHaveBeenCalledOnce();
});
it('does not poll offscreen cards', async () => {
  vi.useFakeTimers();
  const subscription = registerExcerptCheck({ id: 2 } as Excerpt, true, vi.fn());
  await vi.advanceTimersByTimeAsync(120_000);
  expect(post).not.toHaveBeenCalled();
  subscription.stop();
});
