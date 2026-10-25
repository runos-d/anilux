import { createPinia, setActivePinia } from 'pinia';
import { AxiosHeaders } from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatExtrasStore } from './chatExtras';
import { unreadApi, type UnreadChat } from '@/api/chats';

vi.mock('@/api/chats', () => ({ unreadApi: { getUnreadChats: vi.fn() } }));
vi.mock('@/api/client', () => ({ default: {}, isRequestCancelled: () => false }));
const getUnread = vi.mocked(unreadApi.getUnreadChats);
const response = (data: UnreadChat[]) => ({ data, status: 200, statusText: 'OK',
  headers: new AxiosHeaders(), config: { headers: new AxiosHeaders() } });

describe('sidebar unread account isolation', () => {
  beforeEach(() => { setActivePinia(createPinia()); localStorage.clear(); getUnread.mockReset(); });
  it('does not poll authenticated endpoints for a guest', async () => {
    const store = useChatExtrasStore();
    await store.loadUnreadChats();
    expect(getUnread).not.toHaveBeenCalled();
    expect(store.unreadChats).toEqual([]);
  });
  it('ignores a delayed response from the previous account and resets deduplication', async () => {
    localStorage.setItem('anilux_access_token_v1', 'first');
    let resolve!: (value: ReturnType<typeof response>) => void;
    getUnread.mockReturnValueOnce(new Promise(done => { resolve = done; }));
    const store = useChatExtrasStore();
    const old = store.loadUnreadChats();
    store.clearAllData(); localStorage.setItem('anilux_access_token_v1', 'second');
    getUnread.mockResolvedValueOnce(response([]));
    await store.loadUnreadChats();
    resolve(response([{ id: 123, type: 'private', name: 'Old account', unread_count: 10 }])); await old;
    expect(store.unreadChats).toEqual([]);
    expect(getUnread).toHaveBeenCalledTimes(2);
    expect(store.loadingUnread).toBe(false);
  });
});
