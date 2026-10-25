<template>
  <div class="topic-picker">
    <p v-if="!compact" class="topic-intro">Шесть тематик, две группы. Выберите по одному варианту или оставьте без меток. Жанры аниме определяются отдельно.</p>
    <p v-if="legacy && !compact" class="topic-legacy">Сохранены прежние метки: {{ modelValue.map(playlistTopicName).join(', ') }}. Чтобы изменить их, выберите по одному варианту в каждой группе.</p>
    <fieldset v-for="group in playlistTopicGroups" :key="group.id" class="topic-group">
      <legend>{{ group.name }}</legend>
      <p v-if="!compact">{{ group.description }}</p>
      <div class="topic-choices">
        <label class="topic-choice" :class="{ selected: !selected(group.id) }"><input type="radio" :name="`${id}-${group.id}`" :checked="!selected(group.id)" @change="choose(group.id, '')" /><span>Не выбирать</span></label>
        <label v-for="topic in choices.filter(t => topicGroup(t.slug) === group.id)" :key="topic.slug" class="topic-choice" :class="{ selected: modelValue.includes(topic.slug) }" :title="topic.description">
          <input type="radio" :name="`${id}-${group.id}`" :checked="selected(group.id) === topic.slug" @change="choose(group.id, topic.slug)" /><span>{{ topic.name }}</span>
        </label>
      </div>
    </fieldset>
  </div>
</template>
<script setup lang="ts">
import { computed, useId } from 'vue';
import type { PlaylistTopic } from '@/api/playlists';
import { playlistTopicGroups, playlistTopicName, topicGroup } from '@/lib/playlistTopics';
const props = withDefaults(defineProps<{ modelValue: string[]; choices: PlaylistTopic[]; compact?: boolean }>(), { compact: false });
const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>();
const id = useId();
const selected = (group: string) => props.modelValue.find(slug => topicGroup(slug) === group);
const legacy = computed(() => props.modelValue.length > 2 || new Set(props.modelValue.map(topicGroup)).size !== props.modelValue.length);
const choose = (group: string, slug: string) => emit('update:modelValue', [...props.modelValue.filter(t => topicGroup(t) !== group), ...(slug ? [slug] : [])]);
</script>
<style scoped>
.topic-intro, .topic-legacy, .topic-group p { margin: 0 0 .65rem; color: var(--text-secondary); font-size: .8rem; line-height: 1.5; }
.topic-legacy { padding: .65rem; border: 1px solid var(--border-strong); border-radius: var(--radius-md); }
.topic-group { padding: .75rem; margin: .6rem 0; min-width: 0; border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); }
.topic-group legend { padding: 0 .3rem; color: var(--text-primary); font-size: .85rem; font-weight: 650; }
.topic-choices { display: flex; flex-wrap: wrap; gap: .4rem; }
.topic-choice { display: inline-flex; align-items: center; gap: .4rem; min-height: 36px; padding: .45rem .6rem; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-secondary); background: var(--surface-3); font-size: .78rem; cursor: pointer; }
.topic-choice.selected { border-color: var(--accent); color: var(--text-primary); background: color-mix(in srgb, var(--accent) 10%, var(--surface-3)); }
.topic-choice input { accent-color: var(--accent); margin: 0; }
.topic-choice:focus-within { outline: 2px solid var(--accent); outline-offset: 2px; }
</style>
