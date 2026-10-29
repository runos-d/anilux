import { afterEach, expect, it, vi } from 'vitest';
import { AxiosError, CanceledError } from 'axios';
import { queryClient } from './queryClient';
afterEach(() => queryClient.clear());
it('does not retry permanent failures or cancellations', async () => {
  for (const error of [Object.assign(new AxiosError('bad'), { response: { status: 400 } }), new CanceledError()]) {
    const read = vi.fn().mockRejectedValue(error);
    await expect(queryClient.fetchQuery({ queryKey: [String(error)], queryFn: read, retryDelay: 0 })).rejects.toThrow();
    expect(read).toHaveBeenCalledOnce();
  }
});
it('allows only one retry of a transient server failure', async () => {
  const read = vi.fn().mockRejectedValue(Object.assign(new AxiosError('busy'), { response: { status: 503 } }));
  await expect(queryClient.fetchQuery({ queryKey: ['busy'], queryFn: read, retryDelay: 0 })).rejects.toThrow();
  expect(read).toHaveBeenCalledTimes(2);
});
