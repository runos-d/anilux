import { afterEach, expect, it, vi } from 'vitest';
const api = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
vi.mock('./client', () => ({ default: api }));
import { importCatalog, preparedDownload } from './backgroundWork';
afterEach(() => { api.get.mockReset(); api.post.mockReset(); vi.useRealTimers(); });
it('waits for a terminal import result and reports actual progress', async () => {
  vi.useFakeTimers();
  api.post.mockResolvedValue({ status: 202, data: { progress_token: 'job' } });
  api.get.mockResolvedValueOnce({ data: { status: 'processing', current: 1, total: 2, percent: 50 } })
    .mockResolvedValueOnce({ data: { status: 'ready', current: 2, total: 2, percent: 100, results: [{ ok: true }] } });
  const progress = vi.fn();
  const pending = importCatalog({ shikimori_ids: [1, 2] }, progress);
  await vi.advanceTimersByTimeAsync(4500);
  expect((await pending).data.status).toBe('ready');
  expect(api.get).toHaveBeenCalledTimes(2);
  expect(progress.mock.calls.map(call => call[0].percent)).toEqual([50, 100]);
});
it('polls a prepared file using short requests before downloading it', async () => {
  vi.useFakeTimers();
  const state = new Blob();
  Object.defineProperty(state, 'text', { value: async () => JSON.stringify({ job_id: 'job', retry_after: 1 }) });
  const video = new Blob(['video']);
  api.get.mockResolvedValueOnce({ status: 202, data: state }).mockResolvedValueOnce({ status: 200, data: video });
  const pending = preparedDownload('/anime/1/clip/', { params: { episode: 5 } });
  await vi.advanceTimersByTimeAsync(1100);
  expect((await pending).data).toBe(video);
  expect(api.get.mock.calls[1]![1]).toMatchObject({ params: { job_id: 'job' }, timeout: 20000 });
});
