import { beforeEach, afterEach, it, expect, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import type { FeedPost } from '@/api/feed';
const mocks = vi.hoisted(() => ({ get:vi.fn(), invalidate:vi.fn() }));
vi.mock('@/api/client', () => ({ default:{ get:mocks.get } }));
vi.mock('@/lib/queryClient', () => ({ invalidateQueryGroups:mocks.invalidate }));
import { usePostStore } from './posts';
import { globalConnectionReady } from '@/lib/realtimeStatus';
import { nextTick } from 'vue';
beforeEach(() => { setActivePinia(createPinia()); globalConnectionReady.value=false; vi.useFakeTimers(); mocks.get.mockReset(); mocks.invalidate.mockReset(); });
afterEach(() => { usePostStore().clear(); globalConnectionReady.value=false; vi.useRealTimers(); });
it('publishes a finished pending post into shared state and refreshes readers without WebSocket', async () => {
  const store = usePostStore();
  const queued = { id:'17',version:1,status:'processing',media_files:[] } as unknown as FeedPost;
  store.upsert(queued); expect(store.pending).toHaveLength(1);
  mocks.get.mockResolvedValueOnce({data:{results:[queued]}});
  store.startPending(); await vi.advanceTimersByTimeAsync(0);
  mocks.get.mockResolvedValueOnce({data:{results:[]}}).mockResolvedValueOnce({data:{...queued,status:'published',media_files:[{processing_state:'ready'}]}});
  await vi.advanceTimersByTimeAsync(3000);
  expect(store.entities['17']?.status).toBe('published'); expect(store.pending).toHaveLength(0);
  expect(mocks.invalidate).toHaveBeenCalledTimes(1);
});

it('does not poll an empty processing queue every minute while realtime works', async () => {
  globalConnectionReady.value=true; mocks.get.mockResolvedValue({data:{results:[]}});
  const store=usePostStore(); store.startPending(); await vi.advanceTimersByTimeAsync(240_000);
  expect(mocks.get).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(470_000); expect(mocks.get).toHaveBeenCalledTimes(2);
});
it('reconciles missed work after reconnecting', async () => {
  globalConnectionReady.value=true; mocks.get.mockResolvedValue({data:{results:[]}});
  const store=usePostStore(); store.startPending(); await vi.advanceTimersByTimeAsync(0);
  globalConnectionReady.value=false; await nextTick(); globalConnectionReady.value=true; await nextTick();
  expect(mocks.get).toHaveBeenCalledTimes(2);
});

it('switches an idle realtime queue to a short poll when a new processing job appears', async () => {
  globalConnectionReady.value=true; mocks.get.mockResolvedValue({data:{results:[]}});
  const store=usePostStore(); store.startPending(); await vi.advanceTimersByTimeAsync(0);
  const queued={id:'new-job',version:1,status:'processing',media_files:[]} as unknown as FeedPost;
  store.upsert(queued); await nextTick();
  mocks.get.mockResolvedValue({data:{results:[queued]}});
  await vi.advanceTimersByTimeAsync(2999); expect(mocks.get).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(1); expect(mocks.get).toHaveBeenCalledTimes(2);
  store.clear(); await vi.advanceTimersByTimeAsync(120_000); expect(mocks.get).toHaveBeenCalledTimes(2);
});

it('patches reaction counters without fetching a post or invalidating the whole feed', () => {
  const store=usePostStore();
  store.upsert({id:'p1',version:1,status:'published',likes_count:0,is_liked:false,is_disliked:false} as unknown as FeedPost);
  expect(store.applyRealtime('post_reaction',{post_id:'p1',actor_id:7,reaction:'like',active:true,counter_revision:'2026-10-29T12:00:00Z',counts:{likes_count:5}},7)).toBe(true);
  expect(store.entities.p1?.likes_count).toBe(5); expect(store.entities.p1?.is_liked).toBe(true);
  expect(mocks.get).not.toHaveBeenCalled(); expect(mocks.invalidate).not.toHaveBeenCalled();
  expect(store.applyRealtime('post_reaction',{post_id:'p1',counter_revision:'2026-10-29T11:00:00Z',counts:{likes_count:1}},7)).toBe(true);
  expect(store.entities.p1?.likes_count).toBe(5);
  expect(store.applyRealtime('new_post',{post_id:'unknown'},7)).toBe(false); expect(mocks.get).not.toHaveBeenCalled();
});
