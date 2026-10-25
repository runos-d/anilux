<template>
  <div
    ref="playerRoot"
    class="player"
    :class="{ 'player--idle': !controlsVisible }"
    tabindex="0"
    @mousemove="onPointerMove"
    @mouseleave="onPointerLeave"
    @keydown="onKeydown"
  >
    <div class="player__stage" @click="togglePlay" @dblclick="toggleFullscreen">
      <video
        ref="videoEl"
        class="player__video"
        playsinline
        crossorigin="anonymous"
        preload="metadata"
        @loadedmetadata="onLoadedMetadata"
        @loadeddata="releaseFrameHold"
        @seeked="releaseFrameHold"
        @durationchange="onDurationChange"
        @timeupdate="onTimeUpdate"
        @progress="onProgress"
        @play="onPlay"
        @pause="onPause"
        @playing="releaseFrameHold"
        @ended="onEnded"
        @error="onVideoError"
        @enterpictureinpicture="emit('enterPip')"
        @leavepictureinpicture="emit('exitPip')"
      ></video>
      <canvas
        ref="upscaleCanvasEl"
        class="player__upscale-canvas"
        :class="{ 'is-active': anime4kEnabled }"
        aria-hidden="true"
      ></canvas>
      <img v-if="frameHoldUrl" class="player__frame-hold" :src="frameHoldUrl" alt="" aria-hidden="true" />
      <div v-if="anime4kError" class="player__upscale-error" role="status">
        {{ anime4kError }}
      </div>
      <div v-if="!hasSources && !loading" class="player__placeholder">
        <svg viewBox="0 0 24 24" class="player__placeholder-icon">
          <rect x="2" y="4" width="20" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1.5" />
          <path d="m10 9 5 3-5 3z" fill="currentColor" />
        </svg>
        <span>{{ "Видео недоступно" }}</span>
      </div>
      <div v-else-if="!isPlaying && !loading && canResume" class="player__resume">
        <button
          class="player__resume-btn"
          type="button"
          @click.stop="resumePlayback"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
          <span>Продолжить с {{ formatTime(resumeAt) }}</span>
        </button>
        <button
          class="player__resume-restart"
          type="button"
          @click.stop="restartPlayback"
        >
          Сначала
        </button>
      </div>
      <button
        v-else-if="!isPlaying && !loading"
        class="player__center"
        type="button"
        aria-label="Воспроизвести"
        @click.stop="togglePlay"
      >
        <svg viewBox="-4 -4 32 32" width="48" height="48" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </button>
      <div v-if="loading" class="player__loading" role="status">
        <span class="player__spinner"></span>
      </div>
    </div>

    <div class="player__top">
      <div v-if="episodeGroups.length" ref="episodeDropdownEl" class="player__dropdown">
        <div class="player__episode-controls">
          <button
            class="player__step"
            type="button"
            aria-label="Предыдущая серия"
            :disabled="!previousEpisode"
            @click.stop="stepEpisode(-1)"
          >
            <svg viewBox="0 0 24 24" class="i i--stroke"><path d="m15 6-6 6 6 6" /></svg>
          </button>
          <button
            class="player__select"
            type="button"
            aria-haspopup="listbox"
            :aria-expanded="episodeMenuOpen"
            :title="episodeLabel"
            @click.stop="toggleEpisodeMenu"
          >
            <span class="player__select-label">{{ episodeLabel }}</span>
            <svg viewBox="0 0 24 24" class="player__select-chevron i i--stroke"><path d="m6 9 6 6 6-6" /></svg>
          </button>
          <button
            class="player__step"
            type="button"
            aria-label="Следующая серия"
            :disabled="!nextEpisode"
            @click.stop="stepEpisode(1)"
          >
            <svg viewBox="0 0 24 24" class="i i--stroke"><path d="m9 6 6 6-6 6" /></svg>
          </button>
        </div>

        <div v-if="episodeMenuOpen" class="player__menu player__menu--episodes" role="listbox" aria-label="Выбор серии" @click.stop>
          <div v-if="episodeGroups.length > 1" class="player__season-tabs">
            <button
              v-for="group in episodeGroups"
              :key="group.season"
              type="button"
              class="player__season-tab"
              :class="{ 'is-active': group.season === activeSeason }"
              @click="switchSeason(group.season)"
            >
              {{ group.label }}
            </button>
          </div>
          <div v-else class="player__menu-head">{{ activeGroup?.label }}</div>

          <!-- ПОИСК ПО ЭПИЗОДАМ -->
          <div v-if="(activeGroup?.episodes?.length || 0) > 8" class="player__episode-search">
            <svg viewBox="0 0 24 24" class="player__episode-search-icon i i--stroke">
              <circle cx="11" cy="11" r="7" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <input
              v-model="episodeSearch"
              type="text"
              inputmode="numeric"
              class="player__episode-search-input"
              placeholder="Поиск серии…"
              @click.stop
            />
            <button
              v-if="episodeSearch"
              type="button"
              class="player__episode-search-clear"
              aria-label="Очистить поиск"
              @click.stop="episodeSearch = ''"
            >
              <svg viewBox="0 0 24 24" class="i i--stroke"><path d="M6 6l12 12M18 6 6 18" /></svg>
            </button>
          </div>

          <div class="player__episode-grid">
            <button
              v-for="number in filteredEpisodes"
              :key="number"
              type="button"
              class="player__episode-btn"
              :class="{ 'is-active': number === episode && activeSeason === season }"
              role="option"
              :aria-selected="number === episode && activeSeason === season"
              @click="pickEpisode(number)"
            >
              {{ number }}
            </button>
            <div v-if="filteredEpisodes.length === 0" class="player__episode-empty">
              Серия не найдена
            </div>
          </div>
        </div>
      </div>
      <span v-else class="player__chip player__chip--text">Серия {{ episode }}</span>

      <div
        v-if="episodeGroups.length > 1"
        ref="seasonDropdownEl"
        class="player__dropdown player__dropdown--season"
      >
        <button
          class="player__select player__select--season"
          type="button"
          aria-haspopup="listbox"
          :aria-expanded="seasonMenuOpen"
          :title="currentSeasonLabel"
          @click.stop="toggleSeasonMenu"
        >
          <svg viewBox="0 0 24 24" class="i i--stroke player__select-icon">
            <path d="m12 3 9 5-9 5-9-5 9-5Z" />
            <path d="m3 13 9 5 9-5" />
          </svg>
          <span class="player__select-label">{{ currentSeasonLabel }}</span>
          <svg viewBox="0 0 24 24" class="player__select-chevron i i--stroke"><path d="m6 9 6 6 6-6" /></svg>
        </button>
        <div
          v-if="seasonMenuOpen"
          class="player__menu player__menu--seasons"
          role="listbox"
          aria-label="Выбор сезона"
          @click.stop
        >
          <button
            v-for="group in episodeGroups"
            :key="group.season"
            type="button"
            class="player__season-option"
            :class="{ 'is-active': group.season === season }"
            role="option"
            :aria-selected="group.season === season"
            @click="pickSeason(group.season)"
          >
            <span class="player__season-option-label">{{ group.label }}</span>
            <span class="player__season-option-count">{{ group.episodes.length }}</span>
          </button>
        </div>
      </div>

      <div v-if="translations.length || translationsLoading" ref="translationDropdownEl" class="player__dropdown player__dropdown--translation">
        <button
          class="player__select player__select--translation"
          type="button"
          aria-haspopup="listbox"
          :aria-expanded="translationMenuOpen"
          :disabled="translationsLoading"
          :title="currentTranslation?.name || 'Выбор озвучки'"
          @click.stop="toggleTranslationMenu"
        >
          <svg viewBox="0 0 24 24" class="i i--stroke player__select-icon">
            <rect x="9" y="2.5" width="6" height="11" rx="3" />
            <path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" />
          </svg>
          <span class="player__select-label">{{ currentTranslation?.name || (translationsLoading ? "Загрузка озвучек…" : "Озвучка") }}</span>
          <span v-if="translationsLoading" class="player__mini-spinner"></span>
          <svg viewBox="0 0 24 24" class="player__select-chevron i i--stroke"><path d="m6 9 6 6 6-6" /></svg>
        </button>

        <div v-if="translationMenuOpen" class="player__menu player__menu--translations" role="listbox" aria-label="Выбор озвучки" @click.stop>
          <div class="player__menu-head">Озвучка</div>
          <div class="player__menu-list">
            <button
              v-for="option in translations"
              :key="option.id"
              type="button"
              class="player__menu-item"
              :class="{ 'is-active': isCurrentTranslation(option.id) }"
              role="option"
              :aria-selected="isCurrentTranslation(option.id)"
              @click="pickTranslation(option.id)"
            >
              <span class="player__menu-avatar">{{ initials(option.name) }}</span>
              <span class="player__menu-copy">
                <span class="player__menu-name">{{ option.name }}</span>
                <span class="player__menu-meta">{{ translationMeta(option) }}</span>
              </span>
              <svg v-if="isCurrentTranslation(option.id)" viewBox="0 0 24 24" class="i i--stroke player__menu-check"><path d="m5 12 4 4L19 6" /></svg>
            </button>
          </div>
        </div>
      </div>

      <div v-if="streams.length > 1" ref="streamDropdownEl" class="player__dropdown player__dropdown--stream">
        <button
          class="player__select player__select--stream"
          type="button"
          aria-haspopup="listbox"
          :aria-expanded="streamMenuOpen"
          title="Сменить поток"
          @click.stop="toggleStreamMenu"
        >
          <svg viewBox="0 0 24 24" class="i i--stroke player__select-icon">
            <path d="M5 7h12M14 4l3 3-3 3M19 17H7M10 14l-3 3 3 3" />
          </svg>
          <span class="player__select-label">{{ currentStreamLabel }}</span>
          <svg viewBox="0 0 24 24" class="player__select-chevron i i--stroke"><path d="m6 9 6 6 6-6" /></svg>
        </button>
        <div v-if="streamMenuOpen" class="player__menu player__menu--streams" role="listbox" aria-label="Выбор потока" @click.stop>
          <div class="player__menu-head">Поток</div>
          <button
            v-for="(stream, index) in streams"
            :key="stream.id"
            type="button"
            class="player__stream-option"
            :class="{ 'is-active': stream.id === streamId }"
            role="option"
            :aria-selected="stream.id === streamId"
            @click="pickStream(stream.id)"
          >
            <span>Поток {{ index + 1 }}</span>
            <small v-if="stream.label">{{ stream.label }}</small>
          </button>
        </div>
      </div>
    </div>

    <div class="player__bottom">
      <div
        ref="timelineEl"
        class="player__timeline"
        @mousedown="onTimelineDown"
        @mousemove="onTimelineHover"
        @mouseleave="onTimelineLeave"
      >
        <div class="player__track">
          <div class="player__track-buffer" :style="{ width: `${bufferPercent}%` }"></div>
          <div class="player__track-played" :style="{ width: `${playedPercent}%` }">
            <span class="player__track-thumb"></span>
          </div>
          <div
            v-if="hoverPercent !== null"
            class="player__track-hover"
            :style="{ left: `${hoverPercent}%` }"
          >
            <span class="player__track-hover-time">{{ formatTime(hoverTime) }}</span>
          </div>
        </div>
      </div>

      <div class="player__bar">
        <button
          class="player__btn player__btn--play"
          type="button"
          :aria-label="isPlaying ? 'Пауза' : 'Воспроизвести'"
          @click="togglePlay"
        >
          <svg v-if="!isPlaying" viewBox="0 0 24 24" class="i i--fill"><path d="M8 5v14l11-7z" /></svg>
          <svg v-else viewBox="0 0 24 24" class="i i--fill"><path d="M7 5h4v14H7zm6 0h4v14h-4z" /></svg>
        </button>

        <div class="player__time">
          <span class="player__time-cur">{{ formatTime(currentTime) }}</span>
          <span class="player__time-sep">/</span>
          <span class="player__time-dur">{{ formatTime(duration) }}</span>
        </div>

        <div class="player__grow"></div>

        <div v-if="hasSources" class="player__quality-wrap">
          <button
            type="button"
            class="player__quality-btn"
            :class="{ 'is-upscaled': anime4kEnabled }"
            :aria-label="`Качество видео: ${qualityLabel}`"
            :aria-expanded="qualityMenuOpen"
            aria-haspopup="menu"
            @click.stop="qualityMenuOpen = !qualityMenuOpen"
          >
            <span class="player__quality-text">{{ qualityLabel }}</span>
            <svg class="player__quality-chevron" viewBox="0 0 24 24">
              <path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          
          <div v-if="qualityMenuOpen" class="player__quality-menu" role="menu" @click.stop>
            <button
              type="button"
              class="player__quality-item player__quality-item--anime4k"
              :class="{ 'is-active': anime4kEnabled }"
              :disabled="anime4kLoading"
              role="menuitemcheckbox"
              :aria-checked="anime4kEnabled"
              @click="toggleAnime4K"
            >
              <span>{{ upscaledQualityLabel }}</span>
              <small>{{ anime4kLoading ? "Запуск…" : "Anime4K" }}</small>
            </button>
            <button
              v-for="option in qualityOptions"
              :key="option"
              type="button"
              class="player__quality-item"
              :class="{ 'is-active': !anime4kEnabled && quality === option }"
              role="menuitemradio"
              :aria-checked="!anime4kEnabled && quality === option"
              @click="pickQuality(option)"
            >
              {{ sourceQualityLabel(option) }}
            </button>
          </div>
        </div>

        <div class="player__vol">
          <button class="player__btn" type="button" :aria-label="muted ? 'Включить звук' : 'Выключить звук'" @click="toggleMute">
            <svg v-if="muted || volume === 0" viewBox="0 0 24 24" class="i i--fill" style="width: 24px; height: 24px;">
              <path d="M4 9v6h4l5 4V5L8 9H4z" />
              <path d="m16 9 5 6M21 9l-5 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
            <svg v-else viewBox="0 0 24 24" class="i i--fill" style="width: 24px; height: 24px;">
              <path d="M4 9v6h4l5 4V5L8 9H4z" />
              <path d="M15.5 8.5a5 5 0 0 1 0 7M18 6a9 9 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
          </button>
          <div ref="volEl" class="player__vol-slider" @mousedown="onVolumeDown">
            <div class="player__vol-fill" :style="{ width: `${(muted ? 0 : volume) * 100}%` }">
              <span class="player__vol-thumb"></span>
            </div>
          </div>
        </div>

        <button class="player__btn" type="button" aria-label="Fullscreen" @click="toggleFullscreen">
          <svg viewBox="0 0 24 24" class="i i--stroke">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M8 21H5a2 2 0 0 1-2-2v-3m13 5h3a2 2 0 0 0 2-2v-3" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Hls from "hls.js";
import { loadAnime4K, type Anime4KVideoUpscaler } from "@/lib/anime4k";
import { captureVideoFrame, type CapturedVideoFrame } from "@/lib/videoScreenshot";
import { orderedForPlayback } from "@/lib/playerSeasons";

interface PlayerSource {
  quality: string;
  url: string;
  type?: string;
}

interface PlayerEpisodeGroup {
  season: number;
  label: string;
  episodes: number[];
}

interface PlayerTranslation {
  id: number | string;
  name: string;
  type?: string;
  is_custom?: boolean;
  episodes_done?: number;
}

interface PlayerStream {
  id: string;
  label?: string;
}

const props = withDefaults(defineProps<{
  sources?: PlayerSource[];
  poster?: string;
  autoplay?: boolean;
  episode?: number;
  season?: number;
  episodeGroups?: PlayerEpisodeGroup[];
  translations?: PlayerTranslation[];
  translationId?: number | string | null;
  streams?: PlayerStream[];
  streamId?: string;
  translationsLoading?: boolean;
  loading?: boolean;
  error?: string;
  resumeTime?: number;
}>(), {
  sources: () => [],
  poster: "",
  autoplay: false,
  episode: 1,
  season: 1,
  episodeGroups: () => [],
  translations: () => [],
  translationId: null,
  streams: () => [],
  streamId: "primary",
  translationsLoading: false,
  loading: false,
  error: "",
  resumeTime: 0,
});

const emit = defineEmits<{
  ready: [];
  play: [];
  pause: [];
  timeUpdate: [time: number];
  durationUpdate: [duration: number];
  videoEnded: [];
  error: [message: string];
  selectEpisode: [payload: { episode: number; season: number }];
  selectTranslation: [id: number | string];
  selectStream: [id: string];
  enterPip: [];
  exitPip: [];
}>();

const playerRoot = ref<HTMLElement | null>(null);
const videoEl = ref<HTMLVideoElement | null>(null);
const upscaleCanvasEl = ref<HTMLCanvasElement | null>(null);
const timelineEl = ref<HTMLElement | null>(null);
const volEl = ref<HTMLElement | null>(null);
const episodeDropdownEl = ref<HTMLElement | null>(null);
const seasonDropdownEl = ref<HTMLElement | null>(null);
const translationDropdownEl = ref<HTMLElement | null>(null);
const streamDropdownEl = ref<HTMLElement | null>(null);

const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const bufferPercent = ref(0);
const volume = ref(0.8);
const muted = ref(false);
let lastVolume = 0.8;
const controlsVisible = ref(true);
const hoverPercent = ref<number | null>(null);
const firstAvailableQuality = (sources: PlayerSource[]) =>
  sources.find((source) => source.quality && source.quality !== "auto")?.quality
  || sources.find((source) => source.quality)?.quality
  || "";
const quality = ref(firstAvailableQuality(props.sources));
const qualityMenuOpen = ref(false);
const anime4kEnabled = ref(false);
const anime4kLoading = ref(false);
const anime4kError = ref("");
const frameHoldUrl = ref("");
const episodeMenuOpen = ref(false);
const episodeSearch = ref("");
const seasonMenuOpen = ref(false);
const translationMenuOpen = ref(false);
const streamMenuOpen = ref(false);
const activeSeason = ref(props.season);
const resumeDismissed = ref(false);

let hls: Hls | null = null;
let anime4kUpscaler: Anime4KVideoUpscaler | null = null;
let anime4kLoadId = 0;
let sourceIndex = 0;
let hideTimer: ReturnType<typeof setTimeout> | null = null;
let frameHoldTimer: ReturnType<typeof setTimeout> | null = null;
let frameHoldFrame: number | null = null;
let pendingSwitch: {
  wasPlaying: boolean;
  position: number;
  resetPosition: boolean;
} | null = null;
let nextTranslationReset = false;
let loadedEpisode = props.episode;
let loadedSeason = props.season;
let hasAttachedInitial = false;
let lastEndedNaturally = false;
let suppressQualityReload = false;

const hasSources = computed(() => props.sources.some((source) => Boolean(source?.url)));
const qualityOptions = computed(() => [
  ...new Set(
    props.sources
      .map((source) => source.quality)
      .filter((quality) => Boolean(quality) && quality !== "auto"),
  ),
]);
const upscaledQualityLabel = computed(() => {
  const sourceHeight = Number.parseInt(quality.value, 10);
  return Number.isFinite(sourceHeight) && sourceHeight > 0
    ? `${sourceHeight * 2}p`
    : "1440p";
});
const qualityLabel = computed(() =>
  anime4kEnabled.value ? upscaledQualityLabel.value : sourceQualityLabel(quality.value),
);
const playedPercent = computed(() =>
  duration.value > 0 ? Math.min(100, (currentTime.value / duration.value) * 100) : 0
);
const resumeAt = computed(() => {
  const durationLimit = duration.value > 0 ? Math.max(0, duration.value - 1) : props.resumeTime;
  return Math.max(0, Math.min(props.resumeTime, durationLimit));
});
const canResume = computed(() =>
  !resumeDismissed.value
  && props.resumeTime >= 5
  && resumeAt.value >= 5
  && duration.value > 0
  && currentTime.value < 1
  && hasSources.value
  && !isPlaying.value
);
const hoverTime = computed(() =>
  hoverPercent.value !== null ? (hoverPercent.value / 100) * duration.value : 0
);

const activeGroup = computed(() =>
  props.episodeGroups.find((group) => group.season === activeSeason.value) ?? props.episodeGroups[0] ?? null
);

const filteredEpisodes = computed(() => {
  const list = activeGroup.value?.episodes ?? [];
  const query = episodeSearch.value.trim();
  if (!query) return list;
  if (/^\d+$/.test(query)) {
    const exact = Number(query);
    return list.filter((ep) => ep === exact || String(ep).startsWith(query));
  }
  return list.filter((ep) => String(ep).includes(query));
});

const flatEpisodes = computed(() =>
  orderedForPlayback(props.episodeGroups).flatMap((group) =>
    group.episodes.map((episode) => ({ season: group.season, episode }))
  )
);
const currentEpisodeIndex = computed(() =>
  flatEpisodes.value.findIndex((item) => item.season === props.season && item.episode === props.episode)
);
const previousEpisode = computed(() =>
  currentEpisodeIndex.value > 0 ? flatEpisodes.value[currentEpisodeIndex.value - 1] : null
);
const nextEpisode = computed(() =>
  currentEpisodeIndex.value >= 0 && currentEpisodeIndex.value + 1 < flatEpisodes.value.length
    ? flatEpisodes.value[currentEpisodeIndex.value + 1]
    : null
);
const episodeLabel = computed(() => `Серия ${props.episode}`);
const currentTranslation = computed(() =>
  props.translations.find((translation) => String(translation.id) === String(props.translationId)) ?? null
);
const currentStreamIndex = computed(() => {
  const index = props.streams.findIndex((stream) => stream.id === props.streamId);
  return index >= 0 ? index : 0;
});
const currentStreamLabel = computed(() => `Поток ${currentStreamIndex.value + 1}`);
const anyMenuOpen = computed(
  () => episodeMenuOpen.value
    || seasonMenuOpen.value
    || translationMenuOpen.value
    || streamMenuOpen.value
    || qualityMenuOpen.value,
);

const translationTypeLabel = (translation: PlayerTranslation) => {
  if (translation.is_custom) return "Свой дубляж";
  return ({
    voice: "Озвучка",
    subtitles: "Субтитры",
    raw: "Оригинал",
  } as Record<string, string>)[translation.type || ""] || "Озвучка";
};

const translationMeta = (translation: PlayerTranslation) => {
  const type = translationTypeLabel(translation);
  return translation.episodes_done ? `${type} · ${translation.episodes_done} эп.` : type;
};

const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "?";

const isCurrentTranslation = (id: number | string) => String(id) === String(props.translationId);

const closeMenus = () => {
  episodeMenuOpen.value = false;
  seasonMenuOpen.value = false;
  translationMenuOpen.value = false;
  streamMenuOpen.value = false;
  qualityMenuOpen.value = false;
};

const currentSeasonLabel = computed(
  () =>
    props.episodeGroups.find((group) => group.season === props.season)?.label ??
    `Сезон ${props.season}`,
);

const switchSeason = (season: number) => {
  activeSeason.value = season;
  episodeSearch.value = "";
};

const toggleSeasonMenu = () => {
  const opening = !seasonMenuOpen.value;
  closeMenus();
  seasonMenuOpen.value = opening;
  if (opening) revealControls();
};

const pickSeason = (season: number) => {
  const group = props.episodeGroups.find((item) => item.season === season);
  closeMenus();
  episodeSearch.value = "";
  if (!group || season === props.season) return;
  const episode = group.episodes.includes(props.episode)
    ? props.episode
    : (group.episodes[0] ?? 1);
  activeSeason.value = season;
  emit("selectEpisode", { episode, season });
};

const toggleEpisodeMenu = () => {
  const opening = !episodeMenuOpen.value;
  closeMenus();
  episodeMenuOpen.value = opening;
  if (opening) {
    revealControls();
    episodeSearch.value = "";
    if (!props.episodeGroups.some((group) => group.season === props.season))
      activeSeason.value = props.episodeGroups[0]?.season ?? props.season;
    else activeSeason.value = props.season;
  }
};

const toggleTranslationMenu = () => {
  const opening = !translationMenuOpen.value;
  closeMenus();
  translationMenuOpen.value = opening;
  if (opening) revealControls();
};

const toggleStreamMenu = () => {
  const opening = !streamMenuOpen.value;
  closeMenus();
  streamMenuOpen.value = opening;
  if (opening) revealControls();
};

const pickEpisode = (episode: number) => {
  closeMenus();
  episodeSearch.value = "";
  if (episode === props.episode && activeSeason.value === props.season) return;
  emit("selectEpisode", { episode, season: activeSeason.value });
};

const stepEpisode = (delta: number) => {
  const target = delta < 0 ? previousEpisode.value : nextEpisode.value;
  if (!target) return;
  closeMenus();
  emit("selectEpisode", target);
};

const pickTranslation = (id: number | string) => {
  closeMenus();
  if (isCurrentTranslation(id)) return;
  emit("selectTranslation", id);
};

const pickStream = (id: string) => {
  closeMenus();
  if (id === props.streamId) return;
  emit("selectStream", id);
};

const onDocumentClick = (event: MouseEvent) => {
  const target = event.target as Node | null;
  if (target && !episodeDropdownEl.value?.contains(target)) episodeMenuOpen.value = false;
  if (target && !seasonDropdownEl.value?.contains(target)) seasonMenuOpen.value = false;
  if (target && !translationDropdownEl.value?.contains(target)) translationMenuOpen.value = false;
  if (target && !streamDropdownEl.value?.contains(target)) streamMenuOpen.value = false;
  if (target instanceof Element && !target.closest('.player__quality-wrap')) qualityMenuOpen.value = false;
};

const formatTime = (seconds: number) => {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
  return hours ? `${hours}:${minutes.toString().padStart(2, "0")}:${secs}` : `${minutes}:${secs}`;
};

const sourceQualityLabel = (value: string) => {
  if (!value || value === "auto") return "Авто";
  return `${value}p`;
};

const orderedSources = () => {
  if (!props.sources.length) return [];
  const chosen = props.sources.filter((source) => source.quality === quality.value);
  return chosen.length ? chosen : props.sources;
};

const disposeAnime4K = () => {
  anime4kLoadId += 1;
  anime4kLoading.value = false;
  if (!anime4kUpscaler) return;
  try {
    anime4kUpscaler.stop();
  } catch {
    /* WebGL context may already be gone. */
  }
  try {
    anime4kUpscaler.detachVideo();
  } catch {
    /* WebGL context may already be gone. */
  }
  anime4kUpscaler = null;
};

const disableAnime4K = () => {
  anime4kEnabled.value = false;
  anime4kError.value = "";
  disposeAnime4K();
};

const failAnime4K = (message: string) => {
  anime4kEnabled.value = false;
  anime4kError.value = message;
  disposeAnime4K();
};

const hasAnime4KWebGL = () => {
  const probe = document.createElement("canvas");
  const gl = probe.getContext("webgl");
  return Boolean(
    gl
    && gl.getExtension("OES_texture_float")
    && gl.getExtension("OES_texture_float_linear")
    && gl.getExtension("EXT_color_buffer_half_float")
  );
};

const startAnime4K = () => {
  if (!anime4kEnabled.value || !anime4kUpscaler) return;
  try {
    anime4kUpscaler.start();
  } catch {
    failAnime4K("Не удалось включить Anime4K 2×. Проверьте CORS видеопотока.");
  }
};

const initializeAnime4K = async () => {
  const element = videoEl.value;
  const canvas = upscaleCanvasEl.value;
  if (!anime4kEnabled.value || anime4kUpscaler || !element || !canvas) return;

  const loadId = ++anime4kLoadId;
  anime4kLoading.value = true;
  anime4kError.value = "";
  try {
    const { VideoUpscaler, ANIME4KJS_SIMPLE_M_2X } = await loadAnime4K();
    if (loadId !== anime4kLoadId || !anime4kEnabled.value) return;
    if (!VideoUpscaler.isSupported() || !hasAnime4KWebGL()) {
      failAnime4K("Anime4K 2× не поддерживается на этом устройстве.");
      return;
    }

    const upscaler = new VideoUpscaler(ANIME4KJS_SIMPLE_M_2X, 30);
    upscaler.attachVideo(element, canvas);
    if (loadId !== anime4kLoadId || !anime4kEnabled.value) {
      upscaler.detachVideo();
      return;
    }
    anime4kUpscaler = upscaler;
    anime4kLoading.value = false;
    if (!element.paused && !element.ended) startAnime4K();
  } catch {
    if (loadId === anime4kLoadId) {
      failAnime4K("Не удалось запустить Anime4K 2× на этом устройстве.");
    }
  }
};

const toggleAnime4K = () => {
  qualityMenuOpen.value = false;
  if (anime4kEnabled.value) {
    disableAnime4K();
    return;
  }
  anime4kEnabled.value = true;
  anime4kError.value = "";
  void initializeAnime4K();
};

const pickQuality = (option: string) => {
  if (anime4kEnabled.value) disableAnime4K();
  anime4kError.value = "";
  quality.value = option;
  qualityMenuOpen.value = false;
};

const clearFrameHold = () => {
  if (frameHoldTimer) {
    clearTimeout(frameHoldTimer);
    frameHoldTimer = null;
  }
  if (frameHoldFrame !== null) {
    cancelAnimationFrame(frameHoldFrame);
    frameHoldFrame = null;
  }
  frameHoldUrl.value = "";
};

const releaseFrameHold = () => {
  if (!frameHoldUrl.value) return;
  if (frameHoldTimer) {
    clearTimeout(frameHoldTimer);
    frameHoldTimer = null;
  }
  if (frameHoldFrame !== null) cancelAnimationFrame(frameHoldFrame);
  frameHoldFrame = requestAnimationFrame(() => {
    frameHoldFrame = null;
    frameHoldUrl.value = "";
  });
};

const holdFrame = () => {
  const element = videoEl.value;
  if (!element || element.readyState < 2 || !element.videoWidth || !element.videoHeight) return;
  try {
    const canvas = document.createElement("canvas");
    const width = Math.min(element.videoWidth, 1280);
    const height = Math.round((element.videoHeight / element.videoWidth) * width);
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context) return;
    context.drawImage(element, 0, 0, width, height);
    frameHoldUrl.value = canvas.toDataURL("image/jpeg", 0.85);
    if (frameHoldTimer) clearTimeout(frameHoldTimer);
    frameHoldTimer = setTimeout(releaseFrameHold, 8000);
  } catch {
    frameHoldUrl.value = "";
  }
};

const destroyHls = () => {
  if (hls) {
    hls.destroy();
    hls = null;
  }
};

const capturePlayback = (resetPosition: boolean) => {
  const element = videoEl.value;
  if (!element) return;
  const reset = resetPosition || Boolean(pendingSwitch?.resetPosition);
  pendingSwitch = {
    wasPlaying: !element.paused && !element.ended,
    position: reset ? 0 : element.currentTime,
    resetPosition: reset,
  };
};

const prepareTranslationSwitch = () => {
  nextTranslationReset = true;
};

const attachSource = (index = 0) => {
  const element = videoEl.value;
  const list = orderedSources();
  if (!element || !list.length) {
    destroyHls();
    return;
  }

  const current = list[Math.min(index, list.length - 1)];
  if (!current?.url) return;
  sourceIndex = index;
  destroyHls();

  if (Hls.isSupported()) {
    const startPosition = pendingSwitch?.position ?? 0;
    hls = new Hls({
      enableWorker: true,
      lowLatencyMode: false,
      startPosition: startPosition > 0 ? startPosition : -1,
    });
    hls.on(Hls.Events.ERROR, (_event, data) => {
      if (!data.fatal) return;
      if (sourceIndex + 1 < list.length) {
        holdFrame();
        capturePlayback(false);
        attachSource(sourceIndex + 1);
        return;
      }
      clearFrameHold();
      emit("error", "Не удалось воспроизвести прямой поток Kodik.");
    });
    hls.loadSource(current.url);
    hls.attachMedia(element);
  } else {
    element.src = current.url;
  }
};

const onLoadedMetadata = () => {
  const element = videoEl.value;
  if (!element) return;
  const initialLoad = !hasAttachedInitial;
  hasAttachedInitial = true;
  element.volume = volume.value;
  element.muted = muted.value;
  onDurationChange();
  emit("ready");
  if (anime4kEnabled.value) void initializeAnime4K();

  const pending = pendingSwitch;
  pendingSwitch = null;
  if (pending) {
    const latest = Number.isFinite(element.duration) && element.duration > 0
      ? Math.max(0, element.duration - 0.5)
      : pending.position;
    element.currentTime = Math.min(pending.position, latest);
    currentTime.value = element.currentTime;
    if (pending.wasPlaying || (lastEndedNaturally && pending.resetPosition))
      element.play().catch(() => undefined);
    lastEndedNaturally = false;
    return;
  }

  if (initialLoad && props.autoplay && !canResume.value) element.play().catch(() => undefined);
};

const onDurationChange = () => {
  const value = Number.isFinite(videoEl.value?.duration) ? videoEl.value!.duration : 0;
  duration.value = value;
  emit("durationUpdate", value);
};

const onTimeUpdate = () => {
  currentTime.value = videoEl.value?.currentTime ?? 0;
  emit("timeUpdate", currentTime.value);
};

const onProgress = () => {
  const element = videoEl.value;
  if (!element || !element.duration) return;
  const buffered = element.buffered;
  if (!buffered.length) return;
  bufferPercent.value = Math.min(100, (buffered.end(buffered.length - 1) / element.duration) * 100);
};

const onPlay = () => {
  isPlaying.value = true;
  if (anime4kUpscaler) startAnime4K();
  else if (anime4kEnabled.value) void initializeAnime4K();
  emit("play");
};

const onPause = () => {
  isPlaying.value = false;
  try {
    anime4kUpscaler?.stop();
  } catch {
    failAnime4K("Anime4K 2× остановлен из-за ошибки WebGL.");
  }
  emit("pause");
};

const onEnded = () => {
  lastEndedNaturally = true;
  isPlaying.value = false;
  emit("videoEnded");
};

const onVideoError = () => {
  clearFrameHold();
  if (!hls) emit("error", "Не удалось воспроизвести видео.");
};

const togglePlay = () => {
  const element = videoEl.value;
  if (!element) return;
  if (element.paused) {
    resumeDismissed.value = true;
    element.play().catch(() => emit("error", "Не удалось запустить воспроизведение."));
  } else {
    element.pause();
  }
};

const resumePlayback = () => {
  const element = videoEl.value;
  if (!element) return;
  resumeDismissed.value = true;
  seekTo(resumeAt.value);
  element.play().catch(() => emit("error", "Не удалось запустить воспроизведение."));
};

const restartPlayback = () => {
  const element = videoEl.value;
  if (!element) return;
  resumeDismissed.value = true;
  seekTo(0);
  element.play().catch(() => emit("error", "Не удалось запустить воспроизведение."));
};

const seekTo = (seconds: number) => {
  const element = videoEl.value;
  if (!element) return;
  const target = Math.max(0, Math.min(duration.value || element.duration || 0, seconds));
  element.currentTime = target;
  currentTime.value = target;
};

const updateHoverFromEvent = (clientX: number) => {
  const element = timelineEl.value;
  if (!element) return;
  const rect = element.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
  hoverPercent.value = ratio * 100;
};

const onTimelineHover = (event: MouseEvent) => {
  updateHoverFromEvent(event.clientX);
};

const onTimelineLeave = () => {
  hoverPercent.value = null;
};

const seekFromEvent = (clientX: number) => {
  const element = timelineEl.value;
  if (!element) return;
  const rect = element.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
  seekTo(ratio * (duration.value || 0));
  hoverPercent.value = ratio * 100;
};

const onTimelineDown = (event: MouseEvent) => {
  event.preventDefault();
  seekFromEvent(event.clientX);

  const move = (moveEvent: MouseEvent) => seekFromEvent(moveEvent.clientX);
  const up = () => {
    document.removeEventListener("mousemove", move);
    document.removeEventListener("mouseup", up);
  };
  document.addEventListener("mousemove", move);
  document.addEventListener("mouseup", up);
};

const applyVolume = (value: number) => {
  if (value > 0) lastVolume = value;
  volume.value = value;
  muted.value = value === 0;
  if (videoEl.value) {
    videoEl.value.volume = value;
    videoEl.value.muted = muted.value;
  }
};

const onVolumeDown = (event: MouseEvent) => {
  event.preventDefault();
  const apply = (clientX: number) => {
    const element = volEl.value;
    if (!element) return;
    const rect = element.getBoundingClientRect();
    applyVolume(Math.max(0, Math.min(1, (clientX - rect.left) / rect.width)));
  };
  apply(event.clientX);
  const move = (moveEvent: MouseEvent) => apply(moveEvent.clientX);
  const up = () => {
    document.removeEventListener("mousemove", move);
    document.removeEventListener("mouseup", up);
  };
  document.addEventListener("mousemove", move);
  document.addEventListener("mouseup", up);
};

const toggleMute = () => {
  if (muted.value || volume.value === 0) {
    muted.value = false;
    if (volume.value === 0) volume.value = lastVolume;
  } else {
    lastVolume = volume.value;
    muted.value = true;
  }
  if (videoEl.value) {
    videoEl.value.volume = volume.value;
    videoEl.value.muted = muted.value;
  }
};

const toggleFullscreen = async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await playerRoot.value?.requestFullscreen();
  } catch {
    /* ignore */
  }
};

const revealControls = () => {
  controlsVisible.value = true;
  if (hideTimer) clearTimeout(hideTimer);
  hideTimer = null;
};

const scheduleHide = () => {
  if (hideTimer) clearTimeout(hideTimer);
  hideTimer = setTimeout(() => {
    if (isPlaying.value && !anyMenuOpen.value) controlsVisible.value = false;
  }, 2500);
};

const onPointerMove = () => {
  revealControls();
  if (isPlaying.value) scheduleHide();
};

const onPointerLeave = () => {
  if (isPlaying.value && !anyMenuOpen.value) controlsVisible.value = false;
};

const onKeydown = (event: KeyboardEvent) => {
  if (event.code === "Escape") {
    closeMenus();
    return;
  }
  const tag = (event.target as HTMLElement)?.tagName;
  if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
  switch (event.code) {
    case "Space":
    case "KeyK":
      event.preventDefault();
      togglePlay();
      break;
    case "ArrowLeft":
      event.preventDefault();
      event.stopPropagation();
      seekTo(currentTime.value - (event.shiftKey ? 30 : 5));
      break;
    case "ArrowRight":
      event.preventDefault();
      event.stopPropagation();
      seekTo(currentTime.value + (event.shiftKey ? 30 : 5));
      break;
    case "ArrowUp":
      event.preventDefault();
      applyVolume(Math.min(1, volume.value + 0.1));
      break;
    case "ArrowDown":
      event.preventDefault();
      applyVolume(Math.max(0, volume.value - 0.1));
      break;
    case "KeyM":
      toggleMute();
      break;
    case "KeyF":
      void toggleFullscreen();
      break;
  }
};

watch(
  () => props.sources,
  (sources, previous) => {
    const translationReset = nextTranslationReset;
    nextTranslationReset = false;
    if (previous?.length) disposeAnime4K();
    if (sources.length) {
      if (previous?.length) {
        const resetPosition =
          translationReset ||
          props.episode !== loadedEpisode ||
          props.season !== loadedSeason;
        if (!resetPosition) holdFrame();
        capturePlayback(resetPosition);
      }
      loadedEpisode = props.episode;
      loadedSeason = props.season;
      const preferredQuality = firstAvailableQuality(sources);
      if (preferredQuality && !sources.some((source) => source.quality === quality.value)) {
        suppressQualityReload = true;
        quality.value = preferredQuality;
      }
    } else {
      clearFrameHold();
    }
    attachSource(0);
  },
  { deep: true },
);

watch(quality, () => {
  if (suppressQualityReload) {
    suppressQualityReload = false;
    return;
  }
  if (!hasSources.value) return;
  holdFrame();
  capturePlayback(false);
  attachSource(0);
});

watch(
  () => props.season,
  (value) => {
    activeSeason.value = value;
    episodeSearch.value = "";
  },
);

watch(
  () => props.episodeGroups,
  (groups) => {
    if (!groups.some((group) => group.season === activeSeason.value)) {
      activeSeason.value = groups.some((group) => group.season === props.season)
        ? props.season
        : groups[0]?.season ?? props.season;
    }
  },
  { deep: true },
);

watch(
  () => [props.episode, props.season],
  () => {
    disposeAnime4K();
    resumeDismissed.value = false;
    closeMenus();
    episodeSearch.value = "";
  },
);

onMounted(() => {
  if (videoEl.value) {
    videoEl.value.volume = volume.value;
    videoEl.value.muted = muted.value;
  }
  activeSeason.value = props.season;
  playerRoot.value?.focus();
  attachSource(0);
  document.addEventListener("click", onDocumentClick);
});

onBeforeUnmount(() => {
  disposeAnime4K();
  destroyHls();
  clearFrameHold();
  if (hideTimer) clearTimeout(hideTimer);
  document.removeEventListener("click", onDocumentClick);
});

const play = () => {
  videoEl.value?.play().catch(() => undefined);
};

const pause = () => {
  videoEl.value?.pause();
};

const seek = (seconds: number) => seekTo(seconds);

const getCurrentTime = () => currentTime.value;

const getDuration = () => duration.value;

const captureFrame = (): CapturedVideoFrame => {
  const element = videoEl.value;
  if (!element) throw new Error("Плеер ещё не готов.");
  return captureVideoFrame(element);
};

const enterPip = async () => {
  if (window.aniluxNative) {
    await window.aniluxNative.setPictureInPicture(true);
    return;
  }
  const element = videoEl.value;
  if (!element || !document.pictureInPictureEnabled) {
    throw new Error("Picture-in-Picture is not available");
  }
  await element.requestPictureInPicture();
};

const exitPip = async () => {
  if (window.aniluxNative) {
    await window.aniluxNative.setPictureInPicture(false);
    return;
  }
  if (document.pictureInPictureElement) {
    await document.exitPictureInPicture();
  }
};

defineExpose({
  play,
  pause,
  seek,
  getCurrentTime,
  getDuration,
  captureFrame,
  prepareTranslationSwitch,
  enterPip,
  exitPip,
});
</script>

<style>
html.anilux-native-pip body * { visibility: hidden !important; }
html.anilux-native-pip video.player__video { visibility: visible !important; position: fixed !important; inset: 0 !important; width: 100vw !important; height: 100vh !important; object-fit: contain !important; background: #000 !important; z-index: 2147483647 !important; }
</style>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Underdog&display=swap');
.player {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border-radius: 12px;
  background: #000;
  color: #fff;
  font-family: inherit;
  user-select: none;
  outline: none;

  --pad: 16px;
  --h-ctrl: 40px;
  --h-pill: 32px;
  --radius: 8px;
  --accent: #ff4d8d;
  --dim: rgba(255, 255, 255, 0.6);
  --glass: rgba(18, 18, 22, 0.7);
  --ease: cubic-bezier(0.22, 1, 0.36, 1);
}

.player--idle { cursor: none; }

.player__stage { position: absolute; inset: 0; background: #000; }
.player__video { width: 100%; height: 100%; display: block; object-fit: contain; background: #000; }
.player__upscale-canvas {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: contain;
  visibility: hidden;
  pointer-events: none;
}
.player__upscale-canvas.is-active { display: block; }

.player__upscale-error {
  position: absolute;
  top: 62px;
  left: 50%;
  z-index: 4;
  max-width: min(88%, 520px);
  padding: 8px 12px;
  transform: translateX(-50%);
  border: 1px solid rgba(255, 130, 130, 0.38);
  border-radius: 8px;
  background: rgba(35, 12, 18, 0.9);
  color: #ffd5dc;
  font-size: 0.72rem;
  text-align: center;
  pointer-events: none;
}

.player__frame-hold {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
  pointer-events: none;
}

.player__placeholder {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
  color: rgba(255, 255, 255, 0.3);
  background: repeating-linear-gradient(45deg, #0b0b0d 0 10px, #101014 10px 20px);
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.player__placeholder-icon { width: 44px; height: 44px; }

.player__center {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 2;
  display: grid;
  width: 72px;
  height: 72px;
  place-items: center;
  padding: 0;
  transform: translate(-50%, -50%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  background: rgba(18, 18, 22, 0.381);
  color: #fff;
  cursor: pointer;
  backdrop-filter: blur(4px);
  transition: transform 0.18s var(--ease), background 0.18s var(--ease);
}
.player__center:hover { transform: translate(-50%, -50%) scale(1.06); background: rgba(54, 34, 42, 0.35); }
.player__center .i { width: 32px; height: 32px; margin-left: 3px; }

.player__resume {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  transform: translate(-50%, -50%);
}

.player__resume-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 52px;
  padding: 0 22px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  background: rgba(18, 18, 22, 0.78);
  color: #fff;
  font: 700 0.95rem/1 inherit;
  cursor: pointer;
  backdrop-filter: blur(12px);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
  transition: transform 0.18s var(--ease), background 0.18s var(--ease), border-color 0.18s var(--ease);
}

.player__resume-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 77, 141, 0.7);
  background: rgba(255, 77, 141, 0.82);
}

.player__resume-btn svg { width: 20px; height: 20px; margin-left: 2px; }

.player__resume-restart {
  padding: 4px 10px;
  border: 0;
  background: transparent;
  color: rgba(255, 255, 255, 0.72);
  font: 600 0.78rem/1 inherit;
  cursor: pointer;
  transition: color 0.18s var(--ease);
}

.player__resume-restart:hover { color: #fff; }

.i { width: 18px; height: 18px; display: block; flex-shrink: 0; }
.i--stroke { fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.i--fill { fill: currentColor; stroke: none; }

.player__top {
  position: absolute;
  inset: 0 0 auto 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: var(--pad);
  background: linear-gradient(180deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%);
  z-index: 3;
  transition: opacity 0.25s var(--ease);
}
.player--idle .player__top { opacity: 0; pointer-events: none; }

.player__chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  box-sizing: border-box;
  height: var(--h-pill);
  min-width: var(--h-pill);
  padding: 0 10px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius);
  background: var(--glass);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: #fff;
  font: 600 0.76rem/1 inherit;
}
.player__chip--text { padding: 0 12px; }

.player__dropdown { position: relative; }

.player__episode-controls { display: flex; align-items: center; gap: 3px; }

.player__step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 30px;
  height: var(--h-pill);
  padding: 0;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius);
  background: var(--glass);
  color: #fff;
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition: background 0.15s var(--ease), opacity 0.15s var(--ease);
}
.player__step:hover:not(:disabled) { background: rgba(255,255,255,0.16); }
.player__step:disabled { opacity: 0.35; cursor: default; }
.player__step .i { width: 15px; height: 15px; }

.player__select {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  box-sizing: border-box;
  height: var(--h-pill);
  max-width: 230px;
  padding: 0 10px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius);
  background: var(--glass);
  color: #fff;
  font: 600 0.76rem/1 inherit;
  cursor: pointer;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: background 0.15s var(--ease);
}
.player__select:hover:not(:disabled) { background: rgba(255,255,255,0.16); }
.player__select:disabled { opacity: 0.6; cursor: default; }
.player__select-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.player__select--translation { max-width: 240px; }
.player__select--stream { max-width: 118px; }
.player__select-icon { width: 15px; height: 15px; opacity: 0.8; }
.player__select-chevron { width: 12px; height: 12px; opacity: 0.65; flex: 0 0 auto; }

.player__menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 20;
  box-sizing: border-box;
  padding: 8px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  background: rgba(16,16,20,0.96);
  box-shadow: 0 18px 50px rgba(0,0,0,0.55);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
.player__menu--episodes { width: 300px; }
.player__menu--translations { width: 280px; }
.player__menu--streams {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 220px;
}
.player__stream-option {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 9px 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #fff;
  font: 700 0.76rem/1.2 inherit;
  text-align: left;
  cursor: pointer;
}
.player__stream-option:hover { background: rgba(255,255,255,0.08); }
.player__stream-option.is-active {
  border-color: rgba(255,77,141,0.5);
  background: rgba(255,77,141,0.2);
}
.player__stream-option small {
  overflow: hidden;
  color: var(--dim);
  font-size: 0.64rem;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.player__menu-head {
  padding: 2px 4px 8px;
  color: var(--dim);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* ПОИСК ПО ЭПИЗОДАМ */
.player__episode-search {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.player__episode-search-icon {
  position: absolute;
  left: 9px;
  width: 14px;
  height: 14px;
  color: var(--dim);
  pointer-events: none;
}
.player__episode-search-input {
  width: 100%;
  height: 32px;
  padding: 0 30px 0 30px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  color: #fff;
  font: 500 0.74rem/1 inherit;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s var(--ease), background 0.15s var(--ease);
}
.player__episode-search-input::placeholder { color: var(--dim); }
.player__episode-search-input:focus {
  border-color: rgba(255,77,141,0.55);
  background: rgba(255,255,255,0.08);
}
.player__episode-search-clear {
  position: absolute;
  right: 6px;
  display: grid;
  width: 20px;
  height: 20px;
  min-width: 20px;
  min-height: 20px;
  place-items: center;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
  color: var(--dim);
  cursor: pointer;
  transition: background 0.15s var(--ease), color 0.15s var(--ease);
}
.player__episode-search-clear:hover { background: rgba(255,255,255,0.2); color: #fff; }
.player__episode-search-clear .i { width: 12px; height: 12px; }

.player__season-tabs { display: flex; gap: 4px; margin-bottom: 8px; }
.player__season-tab {
  flex: 1 1 0;
  min-width: 0;
  height: 28px;
  padding: 0 6px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 6px;
  background: transparent;
  color: var(--dim);
  font: 650 0.7rem/1 inherit;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.player__season-tab:hover { background: rgba(255,255,255,0.08); color: #fff; }
.player__season-tab.is-active { background: rgba(255,77,141,0.22); border-color: rgba(255,77,141,0.5); color: #fff; }

/* Отдельная кнопка выбора сезона в верхней панели */
.player__select--season { max-width: 160px; }
.player__menu--seasons {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 190px;
}
.player__season-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #fff;
  font: 600 0.76rem/1.2 inherit;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s var(--ease), border-color 0.15s var(--ease);
}
.player__season-option:hover { background: rgba(255,255,255,0.08); }
.player__season-option.is-active {
  background: rgba(255,77,141,0.22);
  border-color: rgba(255,77,141,0.5);
}
.player__season-option-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.player__season-option-count {
  flex: 0 0 auto;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  color: var(--dim);
  font-size: 0.66rem;
  font-weight: 700;
}

/* Сетка эпизодов — с нормальными отступами и скроллом */
.player__episode-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
  max-height: 232px;
  overflow-y: auto;
  padding: 2px 4px 4px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.25) transparent;
  scrollbar-gutter: stable;
}
.player__episode-grid::-webkit-scrollbar { width: 6px; }
.player__episode-grid::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.25);
  border-radius: 999px;
}
.player__episode-grid::-webkit-scrollbar-track { background: transparent; }

.player__episode-btn {
  height: 30px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 6px;
  background: rgba(255,255,255,0.06);
  color: #fff;
  font: 650 0.72rem/1 inherit;
  font-variant-numeric: tabular-nums;
  cursor: pointer;
  transition: background 0.15s var(--ease), border-color 0.15s var(--ease);
}
.player__episode-btn:hover { background: rgba(255,255,255,0.14); }
.player__episode-btn.is-active {
  border-color: rgba(255,77,141,0.55);
  background: var(--accent);
  box-shadow: 0 0 14px rgba(255,77,141,0.35);
}

.player__episode-empty {
  grid-column: 1 / -1;
  padding: 18px 8px;
  text-align: center;
  color: var(--dim);
  font-size: 0.72rem;
}

.player__menu-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 264px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.25) transparent;
}
.player__menu-item {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 7px 8px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #fff;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s var(--ease);
}
.player__menu-item:hover { background: rgba(255,255,255,0.08); }
.player__menu-item.is-active { background: rgba(255,77,141,0.16); border-color: rgba(255,77,141,0.35); }
.player__menu-avatar {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  font-family: 'UnifrakturMaguntia', 'Underdog', serif;
  font-weight: 600; 
  border-radius: 50%;
  padding-top: 4px;
  background: linear-gradient(135deg, rgba(255, 255, 255), rgb(255, 255, 255));
  color: #000;
  font-size: 0.8rem;
  letter-spacing: 0.01em;
}
.player__menu-copy { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1 1 auto; }
.player__menu-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.76rem; font-weight: 650; }
.player__menu-meta { color: var(--dim); font-size: 0.64rem; }
.player__menu-check { width: 14px; height: 14px; color: var(--accent); flex: 0 0 auto; }

.player__loading {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(0,0,0,0.45);
  color: rgba(255,255,255,0.8);
  font-size: 0.74rem;
  letter-spacing: 0.06em;
  pointer-events: none;
}
.player__spinner,
.player__mini-spinner {
  display: inline-block;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.22);
  border-top-color: var(--accent);
  animation: player-spin 0.8s linear infinite;
}
.player__spinner { width: 28px; height: 28px; }
.player__mini-spinner { width: 12px; height: 12px; border-width: 1.5px; flex: 0 0 auto; }
@keyframes player-spin { to { transform: rotate(360deg); } }

.player__bottom {
  position: absolute;
  inset: auto 0 0;
  padding: 48px var(--pad) 14px;
  background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.6) 45%, rgba(0,0,0,0.94) 100%);
  z-index: 2;
  transition: opacity 0.25s var(--ease), transform 0.25s var(--ease);
}
.player--idle .player__bottom {
  opacity: 0;
  pointer-events: none;
  transform: translateY(6px);
}

.player__timeline {
  position: relative;
  height: 18px;
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  cursor: pointer;
  touch-action: none;
}
.player__track {
  position: relative;
  width: 100%;
  height: 4px;
  border-radius: 999px;
  background: rgba(255,255,255,0.18);
  transition: height 0.15s var(--ease);
}
.player__timeline:hover .player__track { height: 6px; }

.player__track-buffer {
  position: absolute;
  inset: 0 auto 0 0;
  height: 100%;
  border-radius: inherit;
  background: rgba(255,255,255,0.28);
  transition: width 0.3s linear;
}
.player__track-played {
  position: absolute;
  inset: 0 auto 0 0;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #ff4d8d, #ff86bf);
}
.player__track-thumb {
  position: absolute;
  top: 50%;
  right: 0;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(255,77,141,0.35), 0 2px 6px rgba(0,0,0,0.5);
  transform: translate(50%, -50%) scale(0);
  transition: transform 0.18s var(--ease);
}
.player__timeline:hover .player__track-thumb { transform: translate(50%, -50%) scale(1); }

.player__track-hover {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(255,255,255,0.5);
  pointer-events: none;
}
.player__track-hover-time {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(0,0,0,0.85);
  color: #fff;
  font-size: 0.7rem;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.player__bar {
  display: flex;
  align-items: center;
  gap: 6px;
  height: var(--h-ctrl);
}
.player__grow { flex: 1 1 auto; }

.player__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  box-sizing: border-box;
  width: var(--h-ctrl);
  height: var(--h-ctrl);
  padding: 0;
  border: none;
  border-radius: var(--radius);
  background: transparent;
  color: #fff;
  cursor: pointer;
  transition: background 0.15s var(--ease);
}
.player__btn:hover { background: rgba(255,255,255,0.1); }
.player__btn:active { background: rgba(255,255,255,0.16); }
.player__btn--play { width: 44px; height: 44px; }
.player__btn--play .i { width: 22px; height: 22px; }

.player__time {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: var(--h-ctrl);
  padding: 0 6px;
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.01em;
  white-space: nowrap;
}
.player__time-cur { color: #fff; font-weight: 600; }
.player__time-sep { color: var(--dim); }
.player__time-dur { color: var(--dim); }

/* СТИЛИ ДЛЯ КАЧЕСТВА */
.player__quality-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: var(--h-ctrl);
  margin-right: 4px;
}

.player__quality-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  height: 30px;
  width: 68px;
  padding: 0 22px 0 6px;
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 6px;
  background: transparent;
  color: #fff;
  font: 600 0.74rem/1 inherit;
  cursor: pointer;
  outline: none;
  box-sizing: border-box;
  transition: background 0.15s var(--ease);
}

.player__quality-btn:hover {
  background: rgba(255,255,255,0.1);
}
.player__quality-btn.is-upscaled {
  border-color: rgba(255, 77, 141, 0.62);
  color: #ff9abe;
}

.player__quality-text {
  width: 100%;
  overflow: hidden;
  text-overflow: clip;
  padding-left: 4px;
  white-space: nowrap;
  display: block;
  text-align: left;
}

.player__quality-chevron {
  position: absolute;
  right: 6px;
  width: 12px;
  height: 12px;
  color: rgba(255,255,255,0.65);
  pointer-events: none;
  z-index: 1;
}

.player__quality-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  z-index: 20;
  min-width: 124px;
  margin-bottom: 8px;
  padding: 4px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: rgba(16,16,20,0.96);
  backdrop-filter: blur(16px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.player__quality-item {
  display: block;
  width: 100%;
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #fff;
  font: 600 0.74rem/1 inherit;
  text-align: left;
  cursor: pointer;
}

.player__quality-item:hover {
  background: rgba(255,255,255,0.1);
}

.player__quality-item.is-active {
  color: var(--accent);
}

.player__quality-item--anime4k {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 3px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  border-radius: 4px 4px 0 0;
}
.player__quality-item--anime4k small {
  color: var(--dim);
  font-size: 0.61rem;
  font-weight: 500;
}
.player__quality-item:disabled { cursor: wait; opacity: 0.7; }

.player__vol {
  display: flex;
  align-items: center;
  gap: 2px;
  height: var(--h-ctrl);
}
.player__vol-slider {
  position: relative;
  width: 72px;
  height: 6px;
  margin: 0 8px 0 2px;
  border-radius: 999px;
  background: rgba(255,255,255,0.18);
  cursor: pointer;
}
.player__vol-fill {
  position: absolute;
  inset: 0 auto 0 0;
  height: 100%;
  border-radius: inherit;
  background: #fff;
}
.player__vol-thumb {
  position: absolute;
  top: 50%;
  right: 0;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.5);
  transform: translate(50%, -50%);
}
.player__vol-slider:hover .player__vol-fill { background: var(--accent); }

@media (max-width: 640px) {
  .player { --pad: 10px; --h-ctrl: 34px; --h-pill: 28px; }
  .player__chip { font-size: 0.7rem; padding: 0 8px; }
  .player__chip--text { padding: 0 10px; }
  .player__select { max-width: 132px; font-size: 0.7rem; padding: 0 8px; }
  .player__select--translation { max-width: 140px; }
  .player__select--stream { max-width: 104px; }
  .player__step { width: 26px; }
  .player__menu--episodes,
  .player__menu--translations { width: 256px; }
  .player__menu--streams { width: 210px; }
  .player__episode-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 5px;
    max-height: 200px;
    padding: 2px 3px 3px;
  }
  .player__menu-list { max-height: 100px; }
  .player__bottom { padding: 36px var(--pad) 10px; }
  .player__btn--play { width: 38px; height: 38px; }
  .player__time { font-size: 0.7rem; padding: 0 4px; }
  .player__vol-slider { width: 56px; }
  .player__center { width: 56px; height: 56px; }
  
  .player__quality-btn {
    height: 28px;
    width: 62px;
    font-size: 0.7rem;
    padding: 0 20px 0 4px;
  }
  .player__quality-chevron {
    right: 4px;
    width: 10px;
  }
  .player__quality-menu {
    min-width: 62px;
  }
}
</style>
