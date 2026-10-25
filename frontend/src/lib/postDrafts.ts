export interface PostDraft {
  key: string;
  clientId: string;
  text: string;
  visibility: string;
  allowComments: boolean;
  isSpoiler: boolean;
  spoilerFor: string;
  files: File[];
  anime: unknown[];
  playlists: unknown[];
  shorts: unknown[];
  excerpts?: unknown[];
  ratings: (number | null)[];
}

function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('anilux-post-drafts', 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore('drafts');
      request.result.createObjectStore('uploads');
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function postDraftGet<T>(store: 'drafts' | 'uploads', key: string): Promise<T | undefined> {
  const db = await database();
  try {
    return await new Promise((resolve, reject) => {
      const request = db.transaction(store).objectStore(store).get(key);
      request.onsuccess = () => resolve(request.result as T | undefined);
      request.onerror = () => reject(request.error);
    });
  } finally { db.close(); }
}

export async function postDraftPut(store: 'drafts' | 'uploads', key: string, value?: unknown): Promise<void> {
  const db = await database();
  try {
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction(store, 'readwrite');
      const storage = transaction.objectStore(store);
      if (value === undefined) storage.delete(key); else storage.put(value, key);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  } finally { db.close(); }
}

export async function clearPostDrafts(owner: string | number): Promise<void> {
  const db = await database();
  try {
    for (const name of ['drafts', 'uploads']) {
      await new Promise<void>((resolve, reject) => {
        const transaction = db.transaction(name, 'readwrite');
        const request = transaction.objectStore(name).openCursor();
        request.onsuccess = () => {
          const cursor = request.result;
          if (cursor) {
            if (String(cursor.key).startsWith(String(owner) + ':')) cursor.delete();
            cursor.continue();
          }
        };
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      });
    }
  } finally { db.close(); }
}
