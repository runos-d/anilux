import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AxiosError, AxiosHeaders, type InternalAxiosRequestConfig } from 'axios';

vi.mock('@/stores/privateChat', () => ({ usePrivateChatStore: () => ({ clearChats: vi.fn() }) }));
vi.mock('@/stores/groupChat', () => ({ useGroupChatStore: () => ({ clearGroupChats: vi.fn() }) }));
vi.mock('@/stores/chatExtras', () => ({ useChatExtrasStore: () => ({ clearAllData: vi.fn() }) }));
vi.mock('@/stores/chatFolders', () => ({ useChatFoldersStore: () => ({ clearFolders: vi.fn() }) }));
vi.mock('@/composables/useGlobalWebSocket', () => ({ disconnectGlobalWebSocket: vi.fn() }));
vi.mock('@/lib/chatOutbox', () => ({ clearChatOutbox: vi.fn() }));

const fail = (config: InternalAxiosRequestConfig, status: number) => Promise.reject(new AxiosError('test failure', undefined, config, undefined,
  { status, statusText: 'failure', config, headers: new AxiosHeaders(), data: { detail: 'test' } }));
const success = (config: InternalAxiosRequestConfig, data: unknown) => Promise.resolve({ config, data, status: 200, statusText: 'OK', headers: new AxiosHeaders() });

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
  localStorage.setItem('anilux_access_token_v1', 'expired');
  localStorage.setItem('anilux_refresh_token_v1', 'refresh');
});

describe('chat request recovery', () => {
  it('keeps credentials after a transient refresh failure', async () => {
    const { default: client } = await import('./client');
    client.defaults.adapter = config => fail(config, config.url?.includes('refresh') ? 503 : 401);
    await expect(client.get('/social/chats/1/')).rejects.toMatchObject({ response: { status: 503 } });
    expect(localStorage.getItem('anilux_refresh_token_v1')).toBe('refresh');
  });

  it('refreshes once for simultaneous requests and preserves caller cancellation', async () => {
    const { default: client } = await import('./client');
    let refreshes = 0;
    client.defaults.adapter = async config => {
      if (config.url?.includes('refresh')) {
        refreshes++;
        await new Promise(resolve => setTimeout(resolve, 10));
        return success(config, { access: 'new-token' });
      }
      return config.headers.Authorization === 'Bearer new-token' ? success(config, { ok: true }) : fail(config, 401);
    };
    const abort = new AbortController();
    const responses = await Promise.all([client.get('/social/chats/1/', { signal: abort.signal }), client.get('/social/chats/2/')]);
    expect(refreshes).toBe(1);
    expect(responses[0]!.config.signal!.aborted).toBe(false);
    abort.abort();
    expect(responses[0]!.config.signal!.aborted).toBe(false);
    const alreadyCancelled = new AbortController(); alreadyCancelled.abort();
    await expect(client.get('/social/chats/1/', { signal: alreadyCancelled.signal })).rejects.toMatchObject({ code: 'ERR_CANCELED' });
  });

  it('rejects an invalid refresh token without recursively refreshing', async () => {
    const { default: client } = await import('./client');
    let refreshes = 0;
    client.defaults.adapter = config => { if (config.url?.includes('refresh')) refreshes++; return fail(config, 401); };
    await expect(client.get('/social/chats/1/')).rejects.toMatchObject({ response: { status: 401 } });
    expect(refreshes).toBe(1);
    expect(localStorage.getItem('anilux_refresh_token_v1')).toBeNull();
  });
});

describe('local attachment preview addresses', () => {
  it('preserves object and inline image URLs before server acknowledgement', async () => {
    const { getMediaUrl } = await import('./client');
    for (const url of ['blob:http://localhost:8080/photo-preview', 'data:image/png;base64,aGVsbG8=']) {
      expect(getMediaUrl(url)).toBe(url);
    }
    expect(getMediaUrl('/api/social/chat-media/photo.png?ticket=valid')).toBe(`${window.location.origin}/api/social/chat-media/photo.png?ticket=valid`);
  });
});

describe('account changes during post uploads', () => {
  it('rejects an upload belonging to a different account before transmitting it', async () => {
    localStorage.setItem('anilux_user_v1', JSON.stringify({ id: 'second' }));
    const { default: client } = await import('./client');
    const adapter = vi.fn(config => success(config, {}));
    client.defaults.adapter = adapter;
    await expect(client.patch('/social/post-uploads/upload/', new Blob(['data']), { _accountId: 'first' }))
      .rejects.toMatchObject({ code: 'ERR_CANCELED' });
    expect(adapter).not.toHaveBeenCalled();
  });

  it('does not overwrite a new login with an earlier refresh response', async () => {
    const { default: client, getRefreshedAccessToken } = await import('./client');
    client.defaults.adapter = config => {
      localStorage.setItem('anilux_refresh_token_v1', 'second-refresh');
      localStorage.setItem('anilux_access_token_v1', 'second-access');
      return success(config, { access: 'first-access' });
    };
    await expect(getRefreshedAccessToken()).rejects.toMatchObject({ code: 'ERR_CANCELED' });
    expect(localStorage.getItem('anilux_access_token_v1')).toBe('second-access');
    expect(localStorage.getItem('anilux_refresh_token_v1')).toBe('second-refresh');
  });

  it('does not repeat an old write or log out a new account after a delayed 401', async () => {
    const { default: client } = await import('./client');
    let requests = 0;
    client.defaults.adapter = config => {
      requests++;
      localStorage.setItem('anilux_refresh_token_v1', 'second-refresh');
      localStorage.setItem('anilux_access_token_v1', 'second-access');
      return fail(config, 401);
    };
    await expect(client.post('/social/posts/', { text: 'first account' })).rejects.toMatchObject({ code: 'ERR_CANCELED' });
    expect(requests).toBe(1);
    expect(localStorage.getItem('anilux_access_token_v1')).toBe('second-access');
  });
});
