import type { Message } from '@/types/chat';

export interface PendingChatSend {
  formData: FormData;
  chatId: number;
  chatType: 'private' | 'group';
  message: Message;
  urls: string[];
  inFlight?: boolean;
}

export const pendingChatSends = new Map<number, PendingChatSend>();
let temporaryId = -Date.now();
export const nextTemporaryMessageId = () => --temporaryId;
interface StoredSend {
  accountId: number;
  commandId: string;
  chatId: number;
  chatType: 'private' | 'group';
  message: Message;
  entries: [string, FormDataEntryValue][];
  urls: string[];
}
let accountId: number | null = null;
let epoch = 0;
let hydrated: Promise<void> | null = null;
let database: Promise<IDBDatabase> | null = null;
let writes: Promise<unknown> = Promise.resolve();
const channel = typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel('anilux-chat-outbox') : null;
const revocationKey = (owner: number) => `anilux-chat-outbox-revoked:${owner}`;
const revocation = (owner: number) => localStorage.getItem(revocationKey(owner));
const isCurrentAccount = (owner: number) => {
  try {
    return !!localStorage.getItem('anilux_access_token_v1') &&
      Number(JSON.parse(localStorage.getItem('anilux_user_v1') || 'null')?.id) === owner;
  } catch { return false; }
};

const openDatabase = () => database ||= new Promise<IDBDatabase>((resolve, reject) => {
  if (typeof indexedDB === 'undefined') { reject(new Error('IndexedDB недоступен')); return; }
  const request = indexedDB.open('anilux-chat-outbox', 1);
  request.onupgradeneeded = () => {
    const store = request.result.createObjectStore('sends', { keyPath: ['accountId', 'commandId'] });
    store.createIndex('accountId', 'accountId');
  };
  request.onsuccess = () => {
    request.result.onversionchange = () => { request.result.close(); database = null; };
    resolve(request.result);
  };
  request.onerror = () => { database = null; reject(request.error); };
});
const write = (operation: (store: IDBObjectStore) => void) => {
  const result = writes.catch(() => {}).then(async () => {
    const db = await openDatabase();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction('sends', 'readwrite');
      tx.oncomplete = () => resolve();
      tx.onerror = tx.onabort = () => reject(tx.error || new Error('Не удалось сохранить очередь'));
      try { operation(tx.objectStore('sends')); }
      catch (error) { tx.abort(); reject(error); }
    });
  });
  writes = result;
  return result;
};
const releaseMemory = (id: number) => {
  pendingChatSends.get(id)?.urls.forEach(url => URL.revokeObjectURL(url));
  pendingChatSends.delete(id);
};

/** Persist files and the command key before clearing the composer. */
export async function storePendingSend(id: number, pending: PendingChatSend) {
  const owner = pending.message.sender_id;
  const commandId = pending.message.client_message_id;
  if (!owner || !commandId) throw new Error('Нет аккаунта или ключа отправки');
  if (!isCurrentAccount(owner)) throw new Error('Аккаунт отправки изменился');
  const generation = epoch, revoked = revocation(owner);
  pendingChatSends.set(id, pending);
  accountId = owner;
  const row: StoredSend = { accountId: owner, commandId, chatId: pending.chatId, chatType: pending.chatType,
    message: JSON.parse(JSON.stringify(pending.message)), entries: [...pending.formData.entries()], urls: pending.urls };
  try {
    await write(store => {
      if (epoch !== generation || revocation(owner) !== revoked || !isCurrentAccount(owner)) {
        throw new Error('Отправка отменена после выхода из аккаунта');
      }
      store.put(row);
    });
    if (epoch !== generation || revocation(owner) !== revoked || !isCurrentAccount(owner)) {
      releaseMemory(id);
      throw new Error('Отправка отменена после выхода из аккаунта');
    }
  }
  catch (error) { releaseMemory(id); throw error; }
}

export function hydrateChatOutbox(owner: number) {
  if (owner === accountId && hydrated) return hydrated;
  for (const id of pendingChatSends.keys()) if (pendingChatSends.get(id)?.message.sender_id !== owner) releaseMemory(id);
  accountId = owner;
  const generation = ++epoch;
  const revoked = revocation(owner);
  hydrated = (async () => {
    await writes.catch(() => {});
    const db = await openDatabase();
    const rows = await new Promise<StoredSend[]>((resolve, reject) => {
      const request = db.transaction('sends').objectStore('sends').index('accountId').getAll(owner);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    if (epoch !== generation || accountId !== owner || revocation(owner) !== revoked || !isCurrentAccount(owner)) return;
    for (const row of rows) {
      if ([...pendingChatSends.values()].some(p => p.message.client_message_id === row.commandId)) continue;
      const formData = new FormData();
      const urls: string[] = [];
      const replacements = new Map<string, string>();
      for (const [key, value] of row.entries) {
        formData.append(key, value);
        if (value instanceof Blob) {
          const url = URL.createObjectURL(value);
          replacements.set(row.urls[urls.length] || '', url);
          urls.push(url);
        }
      }
      const message: Message = JSON.parse(JSON.stringify(row.message), (_, value) =>
        typeof value === 'string' ? replacements.get(value) || value : value);
      message.send_status = 'failed';
      temporaryId = Math.min(temporaryId, message.id);
      pendingChatSends.set(message.id, { formData, chatId: row.chatId, chatType: row.chatType, message, urls });
    }
  })();
  return hydrated;
}

export function finishPendingSend(id: number) {
  const pending = pendingChatSends.get(id);
  if (!pending) return;
  releaseMemory(id);
  const owner = pending.message.sender_id, command = pending.message.client_message_id;
  if (owner && command) {
    void write(store => { store.delete([owner, command]); }).catch(() => {});
    channel?.postMessage({ action: 'removed', owner, command });
  }
}
export function clearChatOutbox(owner?: number) {
  const owners = new Set([...pendingChatSends.values()].map(p => p.message.sender_id));
  if (!owner) {
    try { owner = Number(JSON.parse(localStorage.getItem('anilux_user_v1') || 'null')?.id) || undefined; }
    catch { /* A damaged auth cache must not block logout. */ }
  }
  if (owner) owners.add(owner);
  if (accountId) owners.add(accountId);
  for (const owner of owners) {
    try { localStorage.setItem(revocationKey(owner), crypto.randomUUID()); }
    catch {
      if (isCurrentAccount(owner)) {
        localStorage.removeItem('anilux_access_token_v1');
        localStorage.removeItem('anilux_refresh_token_v1');
        localStorage.removeItem('anilux_user_v1');
      }
    }
  }
  ++epoch; hydrated = null; accountId = null;
  for (const id of pendingChatSends.keys()) releaseMemory(id);
  for (const owner of owners) {
    void write(store => {
      const request = store.index('accountId').openKeyCursor(IDBKeyRange.only(owner));
      request.onsuccess = () => { const cursor = request.result; if (cursor) { store.delete(cursor.primaryKey); cursor.continue(); } };
    }).catch(() => {});
    channel?.postMessage({ action: 'cleared', owner });
  }
}
if (channel) channel.onmessage = ({ data }) => {
  if (!data || data.owner !== accountId) return;
  for (const [id, pending] of pendingChatSends) {
    if (data.action === 'cleared' || data.action === 'removed' && pending.message.client_message_id === data.command) releaseMemory(id);
  }
  if (data.action === 'cleared') { ++epoch; hydrated = null; }
};
window.addEventListener('storage', event => {
  if (accountId && event.key === revocationKey(accountId)) {
    ++epoch; hydrated = null;
    for (const [id, pending] of pendingChatSends) if (pending.message.sender_id === accountId) releaseMemory(id);
  }
});
