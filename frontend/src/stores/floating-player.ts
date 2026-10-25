import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useFloatingPlayerStore = defineStore('floatingPlayer', () => {
  const visible = ref(false)
  const minimized = ref(false)
  const currentVideo = ref<{ title?: string; thumbnail?: string; url?: string } | null>(null)

  interface CurrentAnime {
    anime_id: number
    anime_title: string
    episode?: number | null
    season?: string | number | null
    player_link?: string
    translation_id?: number | null
    start_time?: number
  }
  const currentAnime = ref<CurrentAnime | null>(null)

  const isActive = computed(() => !!currentVideo.value)

  function show(video: { title?: string; thumbnail?: string; url?: string }) {
    currentVideo.value = video
    visible.value = true
    minimized.value = false
  }

  function setCurrentAnime(anime: CurrentAnime) {
    currentAnime.value = anime
    visible.value = true
    minimized.value = false
  }

  function clearCurrentAnime() {
    currentAnime.value = null
    visible.value = false
    minimized.value = false
  }

  function hide() {
    visible.value = false
    minimized.value = false
    currentVideo.value = null
  }

  function toggleMinimize() {
    minimized.value = !minimized.value
  }

  return {
    visible,
    minimized,
    currentVideo,
    currentAnime,
    isActive,
    show,
    setCurrentAnime,
    clearCurrentAnime,
    hide,
    toggleMinimize,
  }
})
