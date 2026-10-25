import { afterEach, describe, expect, it, vi } from 'vitest';
import { cachedCatalogFacets, loadCatalogFacets } from './catalogFacets';

const mocks = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock('@/api/client', () => ({ default: { get: mocks.get } }));

afterEach(() => {
  localStorage.clear();
  mocks.get.mockReset();
});

describe('catalog facets', () => {
  it('loads both facet lists in parallel and reuses the pending request', async () => {
    mocks.get
      .mockResolvedValueOnce({ data: { genres: ['Драма'] } })
      .mockResolvedValueOnce({ data: { types: ['tv'] } });

    const first = loadCatalogFacets();
    const second = loadCatalogFacets();
    expect(first).toBe(second);
    await expect(first).resolves.toEqual({ genres: ['Драма'], types: ['tv'] });
    expect(mocks.get).toHaveBeenCalledTimes(2);
    expect(cachedCatalogFacets()).toEqual({ genres: ['Драма'], types: ['tv'] });
  });
});
