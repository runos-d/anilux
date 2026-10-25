export interface CatalogFacets {
  genres: string[];
  types: string[];
}

const CACHE_KEY = 'anilux_catalog_facets_v1';
const CACHE_TTL = 24 * 60 * 60 * 1000;
import apiClient from '@/api/client';
let pending: Promise<CatalogFacets> | undefined;

const strings = (value: unknown) => Array.isArray(value)
  ? value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim()))
  : [];

export function cachedCatalogFacets(): CatalogFacets | null {
  try {
    const value = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null') as
      | { savedAt?: number; genres?: unknown; types?: unknown }
      | null;
    if (!value?.savedAt || Date.now() - value.savedAt > CACHE_TTL) return null;
    return { genres: strings(value.genres), types: strings(value.types) };
  } catch {
    return null;
  }
}

export function loadCatalogFacets(signal?: AbortSignal): Promise<CatalogFacets> {
  if (pending) return pending;
  pending = Promise.all([
    apiClient.get('/anime/genres/', { signal }),
    apiClient.get('/anime/types/', { signal }),
  ]).then(([genresResponse, typesResponse]) => {
    const genresData = genresResponse.data;
    const typesData = typesResponse.data;
    const facets = { genres: strings(genresData?.genres), types: strings(typesData?.types) };
    try { localStorage.setItem(CACHE_KEY, JSON.stringify({ ...facets, savedAt: Date.now() })); } catch { /* storage is optional */ }
    return facets;
  }).finally(() => { pending = undefined; });
  return pending;
}
