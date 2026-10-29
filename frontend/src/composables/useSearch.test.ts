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
      signal: expect.any(AbortSignal),
      params: { q: 'космос', limit: 7 },
    });
  });
  it('preserves s in English titles and uses the registered playlist detail route', async () => {
    const search = useSearch({ debounceTime: 0 });
    search.handleInput({ target: { value: 'Sword Art Online' } } as unknown as Event);
    await vi.runAllTimersAsync();
    expect(mocks.get).toHaveBeenCalledWith('/anime/', expect.objectContaining({ params: { search: 'sword art online', page_size: 50 } }));
    search.selectItem('playlists', { id: 42 });
    expect(mocks.push).toHaveBeenCalledWith({ name: 'playlist-detail', params: { id: 42 } });
  });

  it('discards a late reply after a newer search and after clearing input', async () => {
    let resolveOld!: (data: unknown) => void;
    mocks.get.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; }));
    const search = useSearch({ debounceTime: 0, categories: [{ id: 'anime', name: 'Anime', icon: '', enabled: true }] });
    search.handleInput({ target: { value: 'old' } } as unknown as Event);
    await vi.advanceTimersByTimeAsync(0);
    mocks.get.mockResolvedValueOnce({ data: { results: [{ id: 2 }] } });
    search.handleInput({ target: { value: 'new' } } as unknown as Event);
    await vi.advanceTimersByTimeAsync(0);
    expect(search.results.value?.anime).toEqual([{ id: 2 }]);
    search.clearSearch();
    resolveOld({ data: { results: [{ id: 1 }] } });
    await vi.advanceTimersByTimeAsync(0);
    expect(search.results.value).toEqual({});
    expect(search.isLoading.value).toBe(false);
  });

});
