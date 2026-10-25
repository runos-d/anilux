<template>
  <section
    ref="playerRoot"
    class="anime-player"
    :class="{ 'is-fullscreen': isFullscreen }"
    tabindex="0"
    aria-label="Видеоплеер"
    @keydown="onKeydown"
  >
    <div class="anime-player__screen" @dblclick="toggleFullscreen">
      <div class="anime-player__topbar">
        <span class="anime-player__episode-pill">
          {{ currentEpisode }} серия
        </span>
      </div>

      <button
        type="button"
        class="anime-player__center-play"
        :aria-label="playing ? 'Пауза' : 'Воспроизвести'"
        @click="togglePlayback"
      >
        <svg v-if="!playing" viewBox="0 0 24 24" aria-hidden="true">
          <path d="m9 6 9 6-9 6V6Z" />
        </svg>
        <svg v-else viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 6h4v12H7V6Zm6 0h4v12h-4V6Z" />
        </svg>
      </button>

      <div class="anime-player__controls">
        <div class="anime-player__timeline-wrap">
          <input
            v-model.number="progress"
            class="anime-player__timeline"
            type="range"
            min="0"
            max="100"
            step="0.1"
            aria-label="Позиция воспроизведения"
            :style="{ '--progress': `${progress}%` }"
          />
        </div>

        <div class="anime-player__control-row">
          <div class="anime-player__control-group">
            <button
              type="button"
              class="anime-player__icon-button anime-player__play-button"
              :aria-label="playing ? 'Пауза' : 'Воспроизвести'"
              @click="togglePlayback"
            >
              <svg v-if="!playing" viewBox="0 0 24 24" aria-hidden="true">
                <path d="m8 5 11 7-11 7V5Z" />
              </svg>
              <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                <path d="M7 5h4v14H7V5Zm6 0h4v14h-4V5Z" />
              </svg>
            </button>

            <button
              type="button"
              class="anime-player__icon-button"
              aria-label="Предыдущая серия"
              title="Предыдущая серия"
              @click="emit('previousEpisode')"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M6 5h2v14H6V5Zm3 7 9-7v14l-9-7Z" />
              </svg>
            </button>

            <button
              type="button"
              class="anime-player__icon-button"
              aria-label="Следующая серия"
              title="Следующая серия"
              @click="emit('nextEpisode')"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M16 5h2v14h-2V5ZM6 5l9 7-9 7V5Z" />
              </svg>
            </button>

            <div class="anime-player__volume">
              <button
                type="button"
                class="anime-player__icon-button"
                :aria-label="muted ? 'Включить звук' : 'Выключить звук'"
                @click="muted = !muted"
              >
                <svg v-if="!muted && volume > 0" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 9v6h4l5 4V5L8 9H4Zm11.5-.5a5 5 0 0 1 0 7M18 6a8 8 0 0 1 0 12" />
                </svg>
                <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 9v6h4l5 4V5L8 9H4Zm12 1 5 5m0-5-5 5" />
                </svg>
              </button>
              <input
                v-model.number="volume"
                class="anime-player__volume-slider"
                type="range"
                min="0"
                max="1"
                step="0.05"
                aria-label="Громкость"
                :style="{ '--volume': `${volume * 100}%` }"
                @input="muted = volume === 0"
              />
            </div>

            <span class="anime-player__time">00:00</span>
          </div>

          <div class="anime-player__control-group anime-player__control-group--right">
            <label class="anime-player__select anime-player__select--dub">
              <span class="anime-player__select-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M12 3a4 4 0 0 0-4 4v4a4 4 0 1 0 8 0V7a4 4 0 0 0-4-4Zm-6 8a6 6 0 0 0 12 0h2a8 8 0 0 1-7 7.94V22h-2v-3.06A8 8 0 0 1 4 11h2Z" /></svg>
              </span>
              <span class="anime-player__select-copy">
                <small>Озвучка</small>
                <select
                  :value="selectedTranslationId"
                  aria-label="Озвучка"
                  @change="selectTranslation"
                >
                  <option v-if="!translations.length" value="">По умолчанию</option>
                  <option
                    v-for="translation in translations"
                    :key="translation.id"
                    :value="String(translation.id)"
                  >
                    {{ translation.name }}
                  </option>
                </select>
              </span>
              <svg class="anime-player__chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg>
            </label>

            <label class="anime-player__select anime-player__select--compact">
              <span class="sr-only">Скорость</span>
              <select v-model="speed" aria-label="Скорость воспроизведения">
                <option value="0.5">0.5×</option>
                <option value="0.75">0.75×</option>
                <option value="1">1×</option>
                <option value="1.25">1.25×</option>
                <option value="1.5">1.5×</option>
                <option value="2">2×</option>
              </select>
              <svg class="anime-player__chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg>
            </label>

            <label class="anime-player__select anime-player__select--compact">
              <span class="sr-only">Качество</span>
              <select v-model="quality" aria-label="Качество видео">
                <option value="auto">Авто</option>
                <option value="1080">1080p</option>
                <option value="720">720p</option>
                <option value="480">480p</option>
              </select>
              <svg class="anime-player__chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg>
            </label>

            <button
              type="button"
              class="anime-player__icon-button"
              :aria-label="isFullscreen ? 'Выйти из полноэкранного режима' : 'Полноэкранный режим'"
              :title="isFullscreen ? 'Выйти из полноэкранного режима' : 'Полноэкранный режим'"
              @click="toggleFullscreen"
            >
              <svg v-if="!isFullscreen" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M8 3H4v4M16 3h4v4M8 21H4v-4m12 4h4v-4" />
              </svg>
              <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 8h4V4m12 4h-4V4M4 16h4v4m12-4h-4v4" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

interface PlayerTranslation {
  id: number | string;
  name: string;
}

const props = withDefaults(defineProps<{
  currentEpisode?: number;
  totalEpisodes?: number;
  translations?: PlayerTranslation[];
  selectedTranslationId?: string;
}>(), {
  currentEpisode: 1,
  totalEpisodes: 0,
  translations: () => [],
  selectedTranslationId: "",
});

const emit = defineEmits<{
  selectTranslation: [id: string];
  previousEpisode: [];
  nextEpisode: [];
}>();

const playerRoot = ref<HTMLElement | null>(null);
const playing = ref(false);
const muted = ref(false);
const volume = ref(0.8);
const progress = ref(0);
const speed = ref("1");
const quality = ref("auto");
const isFullscreen = ref(false);

const togglePlayback = () => {
  playing.value = !playing.value;
};

const selectTranslation = (event: Event) => {
  emit("selectTranslation", (event.target as HTMLSelectElement).value);
};

const syncFullscreen = () => {
  isFullscreen.value = document.fullscreenElement === playerRoot.value;
};

const toggleFullscreen = async () => {
  if (document.fullscreenElement) await document.exitFullscreen();
  else await playerRoot.value?.requestFullscreen();
};

const onKeydown = (event: KeyboardEvent) => {
  if (event.target instanceof HTMLSelectElement || event.target instanceof HTMLInputElement) return;
  if (event.code === "Space" || event.code === "KeyK") {
    event.preventDefault();
    togglePlayback();
  } else if (event.code === "KeyM") {
    muted.value = !muted.value;
  } else if (event.code === "KeyF") {
    void toggleFullscreen();
  }
};

onMounted(() => document.addEventListener("fullscreenchange", syncFullscreen));
onBeforeUnmount(() => document.removeEventListener("fullscreenchange", syncFullscreen));
</script>

<style scoped>
.anime-player {
  --player-accent: #c267ff;
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000;
  color: #fff;
  outline: none;
  user-select: none;
}

.anime-player__screen {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 100%;
  background: #000;
}

.anime-player__screen::after {
  position: absolute;
  inset: auto 0 0;
  height: 42%;
  background: linear-gradient(180deg, transparent, rgb(0 0 0 / 72%) 62%, #000 100%);
  content: "";
  pointer-events: none;
}

.anime-player__topbar {
  position: absolute;
  z-index: 2;
  top: 0;
  right: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: clamp(14px, 2.2vw, 24px);
  background: linear-gradient(180deg, rgb(0 0 0 / 64%), transparent);
}

.anime-player__brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: rgb(255 255 255 / 82%);
  font-size: clamp(.74rem, 1.4vw, .88rem);
  font-weight: 560;
  letter-spacing: .01em;
}

.anime-player__brand b { color: #fff; font-weight: 780; }

.anime-player__brand-mark {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 9px;
  background: linear-gradient(145deg, #a84aff, #6c2ee8);
  box-shadow: 0 6px 24px rgb(126 46 232 / 30%);
}

.anime-player__brand-mark svg { width: 16px; fill: currentColor; }

.anime-player__episode-pill {
  padding: 7px 11px;
  border: 1px solid rgb(255 255 255 / 12%);
  border-radius: 999px;
  background: rgb(16 14 20 / 72%);
  color: rgb(255 255 255 / 74%);
  font-size: .72rem;
  font-weight: 650;
  backdrop-filter: blur(12px);
}

.anime-player__center-play {
  position: absolute;
  z-index: 2;
  top: 50%;
  left: 50%;
  display: grid;
  width: clamp(58px, 7vw, 76px);
  height: clamp(58px, 7vw, 76px);
  place-items: center;
  transform: translate(-50%, -50%);
  border: 1px solid rgb(255 255 255 / 20%);
  border-radius: 50%;
  background: rgb(20 17 25 / 82%);
  color: #fff;
  cursor: pointer;
  box-shadow: 0 16px 48px rgb(0 0 0 / 55%), inset 0 0 0 1px rgb(194 103 255 / 8%);
  backdrop-filter: blur(14px);
  transition: transform .18s ease, border-color .18s ease, background .18s ease;
}

.anime-player__center-play:hover {
  transform: translate(-50%, -50%) scale(1.06);
  border-color: rgb(194 103 255 / 62%);
  background: rgb(119 47 173 / 88%);
}

.anime-player__center-play:active { transform: translate(-50%, -50%) scale(.98); }
.anime-player__center-play svg { width: 42%; fill: currentColor; }
.anime-player__center-play svg:first-child { margin-left: 4px; }

.anime-player__controls {
  position: absolute;
  z-index: 3;
  right: 0;
  bottom: 0;
  left: 0;
  padding: 0 clamp(12px, 2.2vw, 22px) clamp(12px, 2vw, 18px);
}

.anime-player__timeline-wrap {
  display: flex;
  height: 18px;
  align-items: center;
  margin-bottom: 5px;
}

.anime-player__timeline,
.anime-player__volume-slider {
  height: 4px;
  margin: 0;
  appearance: none;
  border-radius: 999px;
  outline: none;
  cursor: pointer;
}

.anime-player__timeline {
  width: 100%;
  background: linear-gradient(90deg, var(--player-accent) var(--progress), rgb(255 255 255 / 26%) var(--progress));
}

.anime-player__timeline::-webkit-slider-thumb,
.anime-player__volume-slider::-webkit-slider-thumb {
  width: 12px;
  height: 12px;
  appearance: none;
  border: 2px solid #fff;
  border-radius: 50%;
  background: var(--player-accent);
  box-shadow: 0 2px 8px rgb(0 0 0 / 45%);
}

.anime-player__timeline::-moz-range-thumb,
.anime-player__volume-slider::-moz-range-thumb {
  width: 9px;
  height: 9px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: var(--player-accent);
}

.anime-player__control-row,
.anime-player__control-group,
.anime-player__volume {
  display: flex;
  align-items: center;
}

.anime-player__control-row { justify-content: space-between; gap: 12px; }
.anime-player__control-group { gap: 3px; }
.anime-player__control-group--right { min-width: 0; justify-content: flex-end; }

.anime-player__icon-button {
  display: grid;
  min-width: 38px;
  height: 38px;
  place-items: center;
  padding: 0 8px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: rgb(255 255 255 / 88%);
  cursor: pointer;
  transition: background .16s ease, color .16s ease, transform .16s ease;
}

.anime-player__icon-button:hover { background: rgb(255 255 255 / 11%); color: #fff; }
.anime-player__icon-button:active { transform: scale(.94); }
.anime-player__icon-button svg { width: 21px; height: 21px; fill: currentColor; stroke: currentColor; stroke-width: 1.7; }
.anime-player__play-button { color: #fff; }

.anime-player__volume { gap: 1px; }
.anime-player__volume-slider {
  --volume: 80%;
  width: 70px;
  background: linear-gradient(90deg, #fff var(--volume), rgb(255 255 255 / 24%) var(--volume));
}

.anime-player__time {
  margin-left: 6px;
  color: rgb(255 255 255 / 68%);
  font-size: .72rem;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.anime-player__select {
  position: relative;
  display: flex;
  height: 40px;
  min-width: 0;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  border: 1px solid rgb(255 255 255 / 12%);
  border-radius: 11px;
  background: rgb(19 16 23 / 84%);
  color: #fff;
  backdrop-filter: blur(14px);
  transition: border-color .16s ease, background .16s ease;
}

.anime-player__select:hover,
.anime-player__select:focus-within {
  border-color: rgb(194 103 255 / 54%);
  background: rgb(31 24 39 / 94%);
}

.anime-player__select--dub { width: min(230px, 28vw); padding-left: 10px; }
.anime-player__select--compact { min-width: 72px; }
.anime-player__select-icon { display: grid; flex: none; place-items: center; color: #d39cff; }
.anime-player__select-icon svg { width: 17px; height: 17px; fill: currentColor; }
.anime-player__select-copy { display: flex; min-width: 0; flex: 1; flex-direction: column; justify-content: center; line-height: 1.05; }
.anime-player__select-copy small { color: rgb(255 255 255 / 42%); font-size: .52rem; font-weight: 650; letter-spacing: .06em; text-transform: uppercase; }

.anime-player__select select {
  width: 100%;
  height: 100%;
  min-width: 0;
  appearance: none;
  border: 0;
  outline: 0;
  background: transparent;
  color: #fff;
  cursor: pointer;
  font: 650 .7rem/1.2 inherit;
}

.anime-player__select--compact select { padding: 0 27px 0 10px; }
.anime-player__select option { background: #17131c; color: #fff; }
.anime-player__chevron { position: absolute; right: 8px; width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 2; pointer-events: none; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; }

.anime-player:fullscreen,
.anime-player.is-fullscreen { width: 100%; height: 100%; }

@media (max-width: 760px) {
  .anime-player__topbar { padding: 12px; }
  .anime-player__controls { padding: 0 9px 9px; }
  .anime-player__volume-slider { display: none; }
  .anime-player__time { margin-left: 1px; }
  .anime-player__select--dub { width: min(172px, 40vw); }
  .anime-player__select--compact { min-width: 62px; }
  .anime-player__icon-button { min-width: 34px; padding-inline: 6px; }
}

@media (max-width: 540px) {
  .anime-player__center-play { top: 45%; }
  .anime-player__control-row { align-items: flex-end; }
  .anime-player__control-group { gap: 0; }
  .anime-player__control-group--right { flex: 1; }
  .anime-player__control-group--right .anime-player__select--compact { display: none; }
  .anime-player__select--dub { width: 100%; max-width: 184px; }
  .anime-player__time { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .anime-player__center-play,
  .anime-player__icon-button,
  .anime-player__select { transition: none; }
}
</style>
