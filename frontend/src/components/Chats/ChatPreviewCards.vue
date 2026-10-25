<template>
  <div class="preview-message message--own" :style="cardVariables">
    <div class="message-body">
      <ChatContentCard type="anime" :data="anime" time="12:32" preview own />
    </div>
  </div>
  <div class="preview-message message--other" :style="cardVariables">
    <div class="message-body">
      <ChatContentCard type="playlist" :data="playlist" time="12:33" preview />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import ChatContentCard from "./ChatContentCard.vue";

const props = withDefaults(defineProps<{
  animeRadius?: number;
  playlistRadius?: number;
  mineStyle?: Record<string, string>;
  otherStyle?: Record<string, string>;
}>(), { animeRadius: 12, playlistRadius: 12 });

const poster = "https://shikimori.io/uploads/poster/animes/21/75a07947be55983ce14917f57e96555f.jpeg";
const anime = { title_ru: "Ван-Пис", title_en: "One Piece", year: 1999, kind: "tv", poster_url: poster };
const playlist = { title: "Любимые приключения", items_count: 1, posters: [poster] };
const cardVariables = computed(() => ({
  "--chat-anime-card-radius": `${props.animeRadius}px`,
  "--chat-playlist-card-radius": `${props.playlistRadius}px`,
  "--chat-msg-mine-bg": props.mineStyle?.background || "var(--bubble-mine-bg, var(--accent))",
  "--chat-msg-mine-text": props.mineStyle?.color || "var(--bubble-mine-text, var(--text-on-accent))",
  "--chat-msg-other-bg": props.otherStyle?.background || "var(--bubble-other-bg, var(--surface-3))",
  "--chat-msg-other-text": props.otherStyle?.color || "var(--bubble-other-text, var(--text-primary))",
  fontFamily: props.mineStyle?.fontFamily || "var(--bubble-font-family, inherit)",
}));
</script>

<style scoped>
.preview-message { display: flex; width: 100%; }
.message--own { flex-direction: row-reverse; }
.message-body { max-width: 75%; min-width: 0; }
.preview-message :deep(.shared-card) { pointer-events: none; }
</style>
