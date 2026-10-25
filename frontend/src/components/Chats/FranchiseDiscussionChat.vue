<template>
  <div class="franchise-chat">
    <div class="topics-heading">
      <span class="topics-title">Темы обсуждения</span>
      <button type="button" class="topics-toggle" @click="showTopics = !showTopics" :aria-expanded="showTopics">
        {{ showTopics ? 'Скрыть темы' : 'Показать темы' }}
      </button>
    </div>
    <div v-show="showTopics" class="topics-list" role="tablist" aria-label="Темы обсуждения">
      <button v-for="topic in topics" :key="topic.id" type="button" role="tab"
        :aria-selected="activeTopic?.id === topic.id" :class="['topic-item', { active: activeTopic?.id === topic.id, 'is-general': topic.anime_id === null }]"
        @click="selectTopic(topic)">
        <span v-if="topic.anime_id === null" class="topic-general-icon" aria-hidden="true">
          <SakuraIcon name="message" :size="17" />
        </span>
        <img v-else-if="topic.poster_url && !posterErrors[topic.id]" :src="topic.poster_url" alt="" @error="posterErrors[topic.id] = true" />
        <SakuraIcon v-else name="tv" :size="18" />
        <span>{{ topic.title }}</span>
      </button>
    </div>
    <div v-if="loading" class="discussion-state">Загрузка обсуждения...</div>
    <div v-else-if="error" class="discussion-state" role="alert">
      <p>{{ error }}</p><button type="button" @click="initialize">Повторить</button>
    </div>
    <ChatDetailView v-else-if="chatId && activeTopic" :key="`${chatId}:${activeTopic.id}`"
      :chat-id="chatId" chat-type="group" :topic-id="activeTopic.id"
      :topic-name="activeTopic.title" :topic-is-general="activeTopic.anime_id === null"
      :topic-anime-id="activeTopic.anime_id" :franchise-id="franchiseId"
      :franchise-slug="franchiseSlug" />
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onUnmounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '@/api/client';
import SakuraIcon from '@/components/icons/SakuraIcon.vue';

const ChatDetailView = defineAsyncComponent(() => import('@/components/page/chats/ChatDetailView.vue'));
interface Topic { id: number; title: string; anime_id: number | null; slug: string; poster_url?: string | null; }
const props = defineProps<{
  franchiseId: number;
  franchiseName: string;
  franchisePoster?: string;
  franchiseSlug?: string | null;
  parts?: { id: number; title_ru: string; title_en: string; franchise_order: number }[];
  initialTopicSlug?: string | null;
  highlightAnimeId?: number;
}>();
const route = useRoute(), router = useRouter();
const topics = ref<Topic[]>([]), activeTopic = ref<Topic | null>(null), chatId = ref<number | null>(null);
const loading = ref(false), error = ref(''), showTopics = ref(true);
const posterErrors = reactive<Record<number, boolean>>({});
const requestedTopic = computed(() => String(route.query.topic || props.initialTopicSlug || route.params.topicSlug || ''));
let generation = 0;
let controller: AbortController | null = null;
const chooseRequestedTopic = () => {
  const slug = requestedTopic.value;
  activeTopic.value = topics.value.find(t => (slug === 'general' && t.anime_id === null) || t.slug === slug ||
    (t.anime_id !== null && String(t.anime_id) === slug)) ||
    topics.value.find(t => t.anime_id === props.highlightAnimeId) || topics.value.find(t => t.anime_id === null) || topics.value[0] || null;
};
const initialize = async () => {
  const run = ++generation;
  controller?.abort(); controller = new AbortController();
  loading.value = true; error.value = ''; chatId.value = null; activeTopic.value = null;
  try {
    const { data } = await apiClient.post('/social/franchise-discussion/init/', {
      franchise_id: props.franchiseId, anime_ids: props.parts?.map(p => p.id) || [],
    }, { signal: controller.signal });
    if (run !== generation) return;
    topics.value = (data.topics || []).map((t: Record<string, unknown>) => ({
      id: Number(t.topic_id ?? t.id),
      title: t.anime_id == null ? 'Всё аниме' : String(t.title || props.franchiseName),
      anime_id: t.anime_id == null ? null : Number(t.anime_id), slug: String(t.slug || ''),
      poster_url: t.anime_id == null ? null : t.poster_url as string | null,
    }));
    if (!data.group_id || !topics.value.length || topics.value.some(t => !Number.isSafeInteger(t.id) || t.id <= 0))
      throw new Error('Не удалось получить темы обсуждения');
    chatId.value = Number(data.group_id); chooseRequestedTopic();
  } catch (e) {
    if (run === generation && !controller?.signal.aborted) error.value = 'Не удалось открыть обсуждение. Проверьте соединение и доступ к чату.';
  } finally { if (run === generation) loading.value = false; }
};
const selectTopic = async (topic: Topic) => {
  await router.replace({ query: { ...route.query, message: undefined, topic: topic.anime_id === null ? 'general' : topic.slug || String(topic.anime_id) } });
  activeTopic.value = topic;
};
watch(() => props.franchiseId, initialize, { immediate: true });
watch([requestedTopic, () => props.highlightAnimeId], chooseRequestedTopic);
onUnmounted(() => { ++generation; controller?.abort(); });
</script>

<style scoped>
.franchise-chat { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; }
.topics-heading { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px 6px; gap: 12px; }
.topics-title { color: var(--text-tertiary); font-size: .75rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
.topics-toggle { min-height: 30px; padding: 4px 9px; color: var(--text-secondary); background: var(--surface-3); border: 1px solid var(--border-subtle); border-radius: 999px; cursor: pointer; font-size: .75rem; }
.topics-list { display: flex; gap: 6px; overflow-x: auto; padding: 2px 12px 10px; flex-shrink: 0; scrollbar-width: thin; }
.topic-item { display: flex; gap: 7px; align-items: center; max-width: 190px; min-height: 38px; flex-shrink: 0; padding: 4px 10px 4px 5px; border: 1px solid var(--border-subtle); border-radius: 999px; color: var(--text-secondary); background: var(--surface-2); cursor: pointer; font: inherit; font-size: .8rem; }
.topic-item:hover { border-color: var(--border-strong); background: var(--surface-3); }
.topic-item.active { border-color: var(--accent-color, #b483ff); color: var(--text-primary); background: color-mix(in srgb, var(--accent) 10%, var(--surface-2)); }
.topic-item.is-general { padding-left: 5px; border-style: dashed; }
.topic-general-icon { display: inline-flex; width: 28px; height: 28px; align-items: center; justify-content: center; flex: none; border-radius: 50%; background: linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 55%, #7c3aed)); color: var(--text-on-accent, #fff); }
.topic-item img { width: 28px; height: 28px; min-height: 28px; min-width: 28px; object-fit: cover; border-radius: 50%; }
.topic-item span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.discussion-state { padding: 32px; text-align: center; color: var(--text-secondary); }
.discussion-state button { padding: 8px 16px; cursor: pointer; }
</style>
