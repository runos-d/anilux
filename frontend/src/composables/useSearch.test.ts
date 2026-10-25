import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  push: vi.fn(),
}));

vi.mock('@/api', () => ({ default: { get: mocks.get } }));
vi.mock('@/api/client', () => ({ getMediaUrl: (url?: string) => url }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: mocks.push }) }));

import { useSearch } from './useSearch';

describe('useSearch', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mocks.get.mockReset().mockResolvedValue({ data: { results: [] } });
    mocks.push.mockReset();
  });

  afterEach(() => vi.useRealTimers());

  it('uses the registered playlist search endpoint', async () => {
    const search = useSearch({
      debounceTime: 0,
      categories: [{ id: 'playlists', name: 'Плейлисты', icon: 'playlists', enabled: true, limit: 7 }],
    });

    search.handleInput({ target: { value: '  Космос!  ' } } as unknown as Event);
    await vi.runAllTimersAsync();

    expect(mocks.get).toHaveBeenCalledWith('/playlists/playlists/search/', {
      params: { q: 'космос', limit: 7 },
    });
  });
});
