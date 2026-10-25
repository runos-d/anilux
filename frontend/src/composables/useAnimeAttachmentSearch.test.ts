import { effectScope, type EffectScope } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useAnimeAttachmentSearch } from './useAnimeAttachmentSearch';
import apiClient from '@/api/client';
vi.mock('@/api/client', () => ({ default: { get: vi.fn() } }));
let scope: EffectScope;
const get = vi.mocked(apiClient.get);
describe('anime attachment catalog search', () => {
  beforeEach(() => { vi.useFakeTimers(); get.mockReset(); scope = effectScope(); });
  afterEach(() => { scope.stop(); vi.useRealTimers(); });
  it('can return from the final page and keeps the full catalog count', async () => {
    get.mockImplementation(async (_url, config) => {
      const page = (config?.params as { page: number }).page;
      return { data: { count: 21, has_more: page === 1,
        results: [{ id: page, title_ru: 'Найдено' }] } };
    });
    const search = scope.run(useAnimeAttachmentSearch)!;
    search.animeSearch.value = 'Поиск'; search.debouncedAnimeSearch();
    await vi.advanceTimersByTimeAsync(300);
    expect(search.animeSearchTotalCount.value).toBe(21);
    await search.nextPage(); expect(search.hasMoreResults.value).toBe(false);
    await search.prevPage(); expect(search.searchPage.value).toBe(1);
    expect(search.searchResults.value[0]?.id).toBe(1);
    expect(get).toHaveBeenCalledTimes(3);
  });
  it('ignores results from an old query, including when the input is cleared', async () => {
    let resolve!: (value: { data: { count: number; results: { id: number }[]; has_more: boolean } }) => void;
    get.mockReturnValueOnce(new Promise(done => { resolve = done; }));
    const search = scope.run(useAnimeAttachmentSearch)!;
    search.animeSearch.value = 'Старый'; search.debouncedAnimeSearch(); await vi.advanceTimersByTimeAsync(300);
    search.clearAnimeSearch();
    resolve({ data: { count: 1, results: [{ id: 1 }], has_more: false } }); await Promise.resolve();
    expect(search.searchResults.value).toEqual([]);
    expect(search.isSearching.value).toBe(false);
  });
});
