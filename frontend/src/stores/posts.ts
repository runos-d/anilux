import { defineStore } from 'pinia';
import { reactive, ref } from 'vue';
import apiClient from '@/api/client';
import type { FeedPost } from '@/api/feed';
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
    sessionGeneration.value++;
    if (poll) clearTimeout(poll);
    poll = undefined;
    feeds.clear(); reactions.clear();
    pending.value = [];
    uploads.value = [];
    for (const key of Object.keys(entities)) delete entities[key];
  }
  function startPending() {
    if (poll) return;
    const current = generation;
    const load = async () => {
      if (loading) return;
      loading = true;
      try {
        const { data } = await apiClient.get('/social/posts/', { params: { pending: true, page_size: 100 } });
        if (current === generation) {
          const previous = pending.value;
          pending.value = (data.results || data).map((post: FeedPost) => upsert(post));
          for (const post of previous) if (!pending.value.some(row => String(row.id) === String(post.id))) void refresh(post.id, true);
        }
      } catch { /* A temporary API failure does not erase progress. */ }
      finally { loading = false; }
    };
    const tick = async () => {
      if (!document.hidden) await load();
      if (current !== generation) return;
      poll = setTimeout(tick, pending.value.length ? 3000 : 60_000);
    };
    void tick();
  }
  return { feeds, sessionGeneration, entities, pending, uploads, reactions, react, upsert, refresh, clear, startPending };
});
