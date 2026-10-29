import { queryClient } from './queryClient';

const MAX_ENTRIES = 80;
let lastPrune = 0;
let publicDb: IDBDatabase | null = null;
const MAX_AGE = 24 * 60 * 60 * 1000;
function openCache(): Promise<IDBDatabase | null> {
  return new Promise(resolve => {
    if (typeof indexedDB === 'undefined') return resolve(null);
    const request = indexedDB.open('anilux-public-reads', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('queries', { keyPath: 'key' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => resolve(null);
  });
}

export const publicCacheReady = (async () => {
  const db = await openCache();
  if (!db) return;
  publicDb = db;
  await new Promise<void>(resolve => {
    const request = db.transaction('queries').objectStore('queries').getAll();
    request.onsuccess = () => {
      const rows = request.result.sort((a, b) => b.updatedAt - a.updatedAt);
      const expired = rows.filter((row, index) => index >= MAX_ENTRIES || Date.now() - row.updatedAt >= MAX_AGE);
      if (expired.length) {
        const cleanup = db.transaction('queries', 'readwrite').objectStore('queries');
        expired.forEach(row => cleanup.delete(row.key));
      }
      for (const row of rows.slice(0, MAX_ENTRIES)) {
        if (row.queryKey?.[1] === 'public' && Date.now() - row.updatedAt < MAX_AGE)
          queryClient.setQueryData(row.queryKey, row.data, { updatedAt: row.updatedAt });
      }
      resolve();
    };
    request.onerror = () => resolve();
  });
  queryClient.getQueryCache().subscribe(event => {
    const query = event.query;
    if (query.queryKey[1] !== 'public' || event.type !== 'updated' || event.action.type !== 'success') return;
    try {
      const transaction = db.transaction('queries', 'readwrite');
      transaction.objectStore('queries').put({ key: query.queryHash, queryKey: query.queryKey,
        data: query.state.data, updatedAt: query.state.dataUpdatedAt });
      transaction.onerror = () => { /* Cache quota never prevents rendering. */ };
      if (Date.now() - lastPrune > 60_000) {
        lastPrune = Date.now();
        const cleanup = db.transaction('queries', 'readwrite').objectStore('queries');
        const all = cleanup.getAll();
        all.onsuccess = () => {
          all.result.sort((a, b) => b.updatedAt - a.updatedAt).forEach((row, index) => {
            if (index >= MAX_ENTRIES || Date.now() - row.updatedAt >= MAX_AGE) cleanup.delete(row.key);
          });
        };
      }

    } catch { /* Private browsing may disable persistent storage. */ }
  });
})();

export async function clearPublicReadCache(): Promise<void> {
  await publicCacheReady;
  if (publicDb) await new Promise<void>((resolve, reject) => {
    const transaction = publicDb!.transaction('queries', 'readwrite');
    transaction.objectStore('queries').clear();
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
  queryClient.removeQueries({ predicate: query => query.queryKey[1] === 'public' });
}
