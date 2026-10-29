import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, reactive } from 'vue';
import { mount, type VueWrapper } from '@vue/test-utils';
const api = vi.hoisted(() => ({ post: vi.fn().mockResolvedValue({}) }));
const auth = reactive({ isAuthenticated: true });
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }));
vi.mock('@/api/client', () => ({ default: api }));
import { globalConnectionReady, setGlobalSender } from '@/lib/realtimeStatus';
import { useOnlineHeartbeat } from './useOnlineHeartbeat';
let wrapper: VueWrapper | undefined;
const start = () => wrapper = mount(defineComponent({ setup() { useOnlineHeartbeat(); return () => h('div'); } }));
beforeEach(() => { vi.useFakeTimers(); vi.spyOn(Math, 'random').mockReturnValue(0); auth.isAuthenticated=true; api.post.mockClear(); globalConnectionReady.value=false; localStorage.setItem('anilux_access_token_v1','test'); Object.defineProperty(document,'hidden',{configurable:true,value:false}); });
afterEach(() => { wrapper?.unmount(); wrapper=undefined; setGlobalSender(null); globalConnectionReady.value=false; vi.restoreAllMocks(); vi.useRealTimers(); localStorage.clear(); });
it('sends no background HTTP heartbeats while realtime is connected', async () => {
  globalConnectionReady.value=true; start(); await vi.advanceTimersByTimeAsync(180_000); expect(api.post).not.toHaveBeenCalled();
});
it('uses the socket for active/away changes', async () => {
  const send=vi.fn(); globalConnectionReady.value=true; setGlobalSender(send); start();
  Object.defineProperty(document,'hidden',{configurable:true,value:true}); document.dispatchEvent(new Event('visibilitychange'));
  expect(send).toHaveBeenCalledWith({action:'presence',is_active:false}); expect(api.post).not.toHaveBeenCalled();
});
it('falls back after connection grace, then stops HTTP and cleans timers on logout', async () => {
  start(); await vi.advanceTimersByTimeAsync(2999); expect(api.post).not.toHaveBeenCalled();
  await vi.advanceTimersByTimeAsync(1); expect(api.post).toHaveBeenCalledTimes(1);
  globalConnectionReady.value=true; await vi.advanceTimersByTimeAsync(120_000); expect(api.post).toHaveBeenCalledTimes(1);
  auth.isAuthenticated=false; await nextTick(); expect(vi.getTimerCount()).toBe(0);
});
