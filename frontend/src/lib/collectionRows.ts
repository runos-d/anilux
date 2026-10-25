/** Collection endpoints may return a bare list or a DRF pagination envelope. */
export function collectionRows<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : data.results;
}
