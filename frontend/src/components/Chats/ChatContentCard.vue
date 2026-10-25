<template>
  <ExcerptCard v-if="type === 'excerpt'" :excerpt="excerpt" :preview="preview" />
  <button v-else
    type="button"
    class="shared-card chat-content-card"
    :class="['is-' + type, { 'is-own': own }]"
    :disabled="preview"
    @click="$emit('open', $event)"
  >
    <template v-if="type === 'anime'">
      <div class="chat-card-anime-info">
        <img :src="resolvePosterUrl(data?.poster_url)" :alt="data.title_ru || data.title_en || 'Аниме'" class="chat-card-anime-poster" @error="handleImageError" />
        <div class="chat-card-anime-text">
          <div class="chat-card-anime-title" :title="data?.title_ru || data?.title_en || 'Аниме'">{{ data?.title_ru || data?.title_en || "Аниме" }}</div>
          <div v-if="data?.year || data?.kind" class="chat-card-anime-subtitle">
            {{ [data?.year, kindLabel(data?.kind)].filter(Boolean).join(" · ") }}
          </div>
        </div>
      </div>
      <span class="chat-card-card-time">{{ time }}</span>
    </template>
    <template v-else-if="type === 'playlist'">
      <div class="chat-card-playlist-row">
        <img
          v-if="(data?.posters || []).length"
          :src="resolvePosterUrl(data?.posters?.[0])"
          :alt="data.title || 'Плейлист'"
          class="chat-card-playlist-cover"
          @error="handleImageError"
        />
        <div class="chat-card-playlist-info">
          <div class="chat-card-playlist-title">{{ data?.title || "Плейлист" }}</div>
          <div class="chat-card-playlist-meta">{{ data?.items_count ?? 0 }} аниме</div>
        </div>
      </div>
      <span class="chat-card-card-time">{{ time }}</span>
    </template>
    <template v-else-if="type === 'post'">
      <div class="chat-card-shared-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
        Пост @{{ data?.author?.username || data?.author_username || "" }}
      </div>
      <div class="chat-card-shared-text">{{ data?.text || "Пост" }}</div>
      <span class="chat-card-card-time">{{ time }}</span>
    </template>
    <template v-else-if="type === 'shorts'">
      <div class="chat-card-shared-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3" /></svg>
        Видео
      </div>
      <div class="chat-card-playlist-row">
        <img
          v-if="data?.thumbnail_url"
          :src="resolvePosterUrl(data.thumbnail_url)"
          class="chat-card-shorts-thumb"
          @error="handleImageError"
        />
        <div class="chat-card-playlist-info">
          <div class="chat-card-playlist-title">{{ data?.text || data?.anime?.title_ru || "Видео" }}</div>
        </div>
      </div>
      <span class="chat-card-card-time">{{ time }}</span>
    </template>
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";
import ExcerptCard from "@/components/excerpts/ExcerptCard.vue";
import type { Excerpt } from "@/api/excerpts";
import type { ChatContentCardData } from "@/types/chat";
import { getMediaUrl } from "@/api/client";

const props = withDefaults(defineProps<{
  type: "anime" | "playlist" | "post" | "shorts" | "excerpt";
  data: ChatContentCardData;
  time: string;
  preview?: boolean;
  own?: boolean;
}>(), { preview: false, own: false });
const excerpt = computed(() => props.data as unknown as Excerpt);
defineEmits<{ open: [event: MouseEvent] }>();
const KIND_LABELS: Record<string, string> = {
  tv: "ТВ-сериал", movie: "Фильм", ova: "OVA", ona: "ONA", special: "Спецвыпуск", music: "Клип",
};
const kindLabel = (kind?: string | null) => kind ? KIND_LABELS[kind] || kind : "";
const resolvePosterUrl = (url?: string | null) => getMediaUrl(url) || "/placeholder-anime.jpg";
const handleImageError = (event: Event) => { (event.target as HTMLImageElement).style.display = "none"; };
</script>

<style scoped src="./chatSharedCard.css"></style>
