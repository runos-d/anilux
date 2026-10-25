import { mount, flushPromises } from '@vue/test-utils';
import { defineComponent, reactive, ref } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('@/lib/initialContent', () => ({ afterInitialContent: (task: () => void) => task() }));
import apiClient from '@/api/client';
import type { Presence } from '@/lib/onlinePresence';

let store: {
  isAuthenticated: boolean; user: { id: number } | null; onlineUsers: Map<number, Presence>;
  updateUserOnlineStatus: (id: number, is_online: boolean) => void;
};
const connected = ref(false);
vi.mock('@/stores/auth', () => ({ useAuthStore: () => store }));
vi.mock('@/composables/useGlobalWebSocket', () => ({
  useGlobalWebSocket: () => ({ connect: vi.fn(), isConnected: connected }),
}));
vi.mock('@/api/client', () => ({ default: { get: vi.fn() } }));
const get = vi.mocked(apiClient.get);
let wrappers: ReturnType<typeof mount>[] = [];

async function subscriber() {
  const { useOnlineStatus } = await import('./useOnlineStatus');
  const wrapper = mount(defineComponent({ setup: useOnlineStatus, template: '<div />' }));
  wrappers.push(wrapper);
  return wrapper;
}

describe('shared online status', () => {
  beforeEach(() => {
    vi.useFakeTimers(); vi.resetModules(); get.mockReset(); connected.value = false;
    store = reactive({
      isAuthenticated: true, user: { id: 9 }, onlineUsers: new Map<number, Presence>(),
      updateUserOnlineStatus: (id: number, is_online: boolean) => { store.onlineUsers.set(id, { is_online }); },
    });
  });
  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount()); wrappers = [];
    vi.useRealTimers();
  });

  it('shares polling across components, reconciles TTL expiry and stops after unmount', async () => {
    let resolve!: (value: { data: { results: { id: number }[] } }) => void;
    get.mockReturnValueOnce(new Promise(done => { resolve = done; }));
    await subscriber(); await subscriber();
    expect(get).toHaveBeenCalledTimes(1);
    resolve({ data: { results: [{ id: 1 }] } }); await flushPromises();
    expect(store.onlineUsers.get(1)?.is_online).toBe(true);
    get.mockResolvedValue({ data: { results: [] } });
    await vi.advanceTimersByTimeAsync(15000); await flushPromises();
    expect(get).toHaveBeenCalledTimes(2);
    expect(store.onlineUsers.get(1)?.is_online).toBe(false);
    wrappers.forEach(wrapper => wrapper.unmount()); wrappers = [];
    await vi.advanceTimersByTimeAsync(30000);
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('rejects a late snapshot after changing accounts and clears the previous presence map', async () => {
    let resolve!: (value: { data: { results: { id: number }[] } }) => void;
    get.mockReturnValueOnce(new Promise(done => { resolve = done; }));
    await subscriber();
    store.onlineUsers.set(1, { is_online: true });
    get.mockResolvedValue({ data: { results: [{ id: 2 }] } });
    store.user = { id: 10 }; await flushPromises();
    resolve({ data: { results: [{ id: 3 }] } }); await flushPromises();
    expect([...store.onlineUsers.keys()]).toEqual([2]);
    store.isAuthenticated = false; store.user = null; await flushPromises();
    expect(store.onlineUsers.size).toBe(0);
  });
});
