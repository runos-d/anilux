import { defineStore } from 'pinia';
import { reactive, ref, watch } from 'vue';
import apiClient from '@/api/client';
import type { FeedPost } from '@/api/feed';
import { globalConnectionReady } from '@/lib/realtimeStatus';
import { invalidateQueryGroups } from '@/lib/queryClient';

export const usePostStore = defineStore('posts', () => {
  const entities = reactive<Record<string, FeedPost>>({});
  const feeds = new Map<string, { rows: FeedPost[]; cursor: string | null; scroll: number; savedAt: number }>();
  const pending = ref<FeedPost[]>([]);
  const uploads = ref<{ id: string; text: string; progress: number; error?: string }[]>([]);
  let poll: ReturnType<typeof setTimeout> | undefined;
  const sessionGeneration = ref(0);
  let generation = 0;
  let loading = false;
  let pollingStarted = false;
  let stopPollingWatchers: (() => void) | undefined;
  function upsert(post: FeedPost): FeedPost {
    const key = String(post.id);
    const existing = entities[key];
    if (existing && (existing.version || 1) > (post.version || 1)) return existing;
    if (existing) Object.assign(existing, post); else entities[key] = post;
    if (post.status === 'processing' || post.status === 'failed' || post.processing_media?.length) {
      if (!pending.value.some(row => String(row.id) === key)) pending.value.push(entities[key]!);
    } else pending.value = pending.value.filter(row => String(row.id) !== key);
    if (Object.keys(entities).length > 1000) delete entities[Object.keys(entities)[0]!];
    return entities[key]!;
  }
  async function refresh(id: string | number, finishedPending = false) {
    const current = generation;
    const wasPending = finishedPending || pending.value.some(row => String(row.id) === String(id));
    try {
      const response = await apiClient.get<FeedPost>(`/social/posts/${id}/`);
      if (current === generation) {
        upsert(response.data);
        if (wasPending && response.data.status === 'published' && !response.data.processing_media?.length)
          void invalidateQueryGroups(['feed', 'post', 'profile']);
      }
    } catch (error) {
      if ((error as { response?: { status: number } }).response?.status === 404 && current === generation) {
        if (entities[String(id)]) entities[String(id)]!.is_deleted = true;
      }
    }
  }
  const counterRevisions = new Map<string, string>();
  function applyRealtime(action: string, payload: Record<string, unknown>, viewer?: number) {
    const id = String(payload.post_id || '');
    const post = entities[id];
    if (!post) return false;
    if (action === 'post_deleted') { post.is_deleted = true; return true; }
    if (!['post_reaction','post_comment','post_reposted','post_liked','post_commented'].includes(action)) return false;
    const counts = payload.counts as Record<string, unknown> | undefined;
    if (!counts) return false;
    const revision = String(payload.counter_revision || '');
    if (revision && revision < (counterRevisions.get(id) || '')) return true;
    for (const name of ['likes_count','dislikes_count','comments_count','reposts_count','views_count'] as const) {
      const value = counts[name];
      if (typeof value === 'number' && Number.isSafeInteger(value) && value >= 0) post[name] = value;
    }
    if (payload.actor_id === viewer && action === 'post_reaction') {
      if (payload.reaction === 'like') { post.is_liked = !!payload.active; if (payload.active) post.is_disliked = false; }
      if (payload.reaction === 'dislike') { post.is_disliked = !!payload.active; if (payload.active) post.is_liked = false; }
    }
    counterRevisions.set(id, revision);
    if (counterRevisions.size > 1000) counterRevisions.delete(counterRevisions.keys().next().value!);
    return true;
  }
  const reactions = reactive(new Set<string>());
  async function react(post: FeedPost, reaction: 'like' | 'dislike') {
    const key = String(post.id);
    if (reactions.has(key)) return;
    reactions.add(key);
    const current = generation;
    try {
      const response = await apiClient.post(`/social/posts/${key}/${reaction}/`, {
        active: !(reaction === 'like' ? post.is_liked : post.is_disliked), client_action_id: crypto.randomUUID(),
      });
      if (current !== generation) return;
      const canonical = upsert(post);
      Object.assign(canonical, { likes_count: response.data.likes_count, dislikes_count: response.data.dislikes_count,
        is_liked: response.data.liked, is_disliked: response.data.disliked });
    } finally { reactions.delete(key); }
  }
  function clear() {
    generation++;
    stopPollingWatchers?.(); stopPollingWatchers = undefined;
    pollingStarted = false;
    loading = false;
    sessionGeneration.value++;
    if (poll) clearTimeout(poll);
    poll = undefined;
    feeds.clear(); reactions.clear(); counterRevisions.clear();
    pending.value = [];
    uploads.value = [];
    for (const key of Object.keys(entities)) delete entities[key];
  }
  function startPending() {
    if (pollingStarted) return;
    pollingStarted = true;
    const current = generation;
    let lastReconcile = 0;
    const load = async () => {
      if (loading) return;
      loading = true;
      try {
        const { data } = await apiClient.get('/social/posts/', { params: { pending: true, page_size: 100 } });
        if (current === generation) {
          lastReconcile = Date.now();
          const previous = pending.value;
          pending.value = (data.results || data).map((post: FeedPost) => upsert(post));
          for (const post of previous) if (!pending.value.some(row => String(row.id) === String(post.id))) void refresh(post.id, true);
        }
      } catch { /* A temporary API failure does not erase progress. */ }
      finally { if (current === generation) loading = false; }
    };
    let initial = true;
    const tick = async () => {
      // Realtime updates cover empty queues. Keep a rare reconciliation in case
      // an event was lost, and the existing short poll while work is pending.
      const needsRead = initial || pending.value.length > 0 || !globalConnectionReady.value || Date.now() - lastReconcile >= 600_000;
      initial = false;
      if (!document.hidden && needsRead) await load();
      if (current !== generation) return;
      poll = setTimeout(tick, pending.value.length ? 3000 : 60_000 + Math.random() * 15_000);
    };
    let connectedBefore = globalConnectionReady.value;
    const stopConnectionWatch = watch(globalConnectionReady, ready => {
      if (ready && connectedBefore && current === generation) void load();
      if (ready) connectedBefore = true;
    });
    const stopPendingWatch = watch(() => pending.value.length, (count, previous) => {
      if (count > 0 && previous === 0 && !loading && current === generation) {
        clearTimeout(poll);
        poll = setTimeout(tick, 3000);
      }
    });
    stopPollingWatchers = () => { stopConnectionWatch(); stopPendingWatch(); };
    void tick();
  }
  return { feeds, sessionGeneration, entities, pending, uploads, reactions, react, upsert, refresh, clear, startPending, applyRealtime };
});
