<template>
  <div class="anime-watch-page">
    <div class="watch-container">
      <div class="left-column">
        <div class="player-wrapper">
          <div class="player-container" ref="playerContainer">
            <AniLuxPlayer
              v-if="ownPlayerMounted && !useCustomPlayer"
              v-show="playerMode === 'own'"
              ref="ownPlayer"
              :sources="ownPlayerSources"
              :poster="ownPlayerPreview || posterSrc || ''"
              :autoplay="autoplay"
              :episode="currentEpisode"
              :season="currentSeason"
              :episode-groups="ownPlayerEpisodeGroups"
              :translations="ownPlayerTranslations"
              :translation-id="ownPlayerTranslationId"
              :streams="ownPlayerStreamOptions"
              :stream-id="selectedOwnStreamId"
              :translations-loading="ownPlayerTranslationsLoading"
              :loading="ownPlayerLoading"
              :error="ownPlayerError"
              :resume-time="resumePosition"
              @ready="onOwnReady"
              @play="onOwnPlay"
              @pause="onOwnPause"
              @timeUpdate="onOwnTimeUpdate"
              @durationUpdate="onOwnDurationUpdate"
              @videoEnded="onOwnVideoEnded"
              @select-episode="onPlayerSelectEpisode"
              @select-translation="onPlayerSelectTranslation"
              @select-stream="onPlayerSelectStream"
              @enter-pip="onOwnEnterPip"
              @exit-pip="onOwnExitPip"
              @error="onOwnError"
            />
            <CustomVideoPlayer
              v-if="useCustomPlayer && customVideoUrl"
              :video-url="customVideoUrl"
              :poster="posterSrc || ''"
              :autoplay="autoplay"
              @ready="onPlayerReady"
              @play="onPlay"
              @pause="onPause"
              @timeUpdate="onTimeUpdate"
              @durationUpdate="onDurationUpdate"
              @videoEnded="onVideoEnded"
              @error="onPlayerError"
            />
            <KodikPlayer
              v-if="kodikPlayerMounted && kodikLink && !useCustomPlayer"
              v-show="playerMode === 'kodik'"
              :link="kodikLink"
              :autoplay="autoplay"
              :active="playerMode === 'kodik'"
              :season="currentSeason"
              :episode="currentEpisode"
              :translation-id="selectedTranslation?.id ?? null"
              ref="kodikPlayer"
              @ready="onKodikReady"
              @play="onKodikPlay"
              @pause="onKodikPause"
              @timeUpdate="onKodikTimeUpdate"
              @durationUpdate="onKodikDurationUpdate"
              @preciseTime="onKodikPreciseTime"
              @currentEpisode="onKodikCurrentEpisode"
              @videoStarted="onKodikVideoStarted"
              @videoEnded="onKodikVideoEnded"
              @enterPip="onKodikEnterPip"
              @exitPip="onKodikExitPip"
              @skipButton="onKodikSkipButton"
              @translationChanged="onKodikTranslationMessage"
              @error="onKodikError"
            />
            <div v-if="showPlayerPlaceholder && !error" class="player-placeholder loading">
              <p>Загрузка плеера...</p>
            </div>
            <div v-else-if="showPlayerPlaceholder && error" class="player-placeholder error">
              <div class="error-icon"><SakuraIcon name="warning" />️</div>
              <p>{{ error }}</p>
              <button @click="retryLoad" class="btn-retry">
                Попробовать снова
              </button>
            </div>
          </div>
          <div class="watch-player-toolbar">
            <div v-if="useCustomPlayer && translations.length" class="player-mode-switch" aria-label="Выбор озвучки">
              <select class="toolbar-translation-select" :value="selectedTranslationId" @change="onToolbarTranslationChange">
                <option v-for="translation in translations" :key="translation.id" :value="String(translation.id)">
                  {{ translation.name }}{{ translation.is_custom ? " · свой дубляж" : "" }}
                </option>
              </select>
            </div>
            <div v-if="!useCustomPlayer" class="player-mode-switch" aria-label="Выбор плеера">
              <button type="button" :class="{ active: playerMode === 'own' }" :aria-pressed="playerMode === 'own'" @click="setPlayerMode('own')">Anilux</button>
              <button type="button" :class="{ active: playerMode === 'kodik' }" :aria-pressed="playerMode === 'kodik'" @click="setPlayerMode('kodik')">Kodik</button>
            </div>
            <button v-if="playerMode === 'own' && !useCustomPlayer" type="button" class="video-screenshot-btn"
              :disabled="screenshotPending || ownPlayerLoading || duration <= 0 || !ownPlayerSources.length"
              :aria-busy="screenshotPending" aria-label="Сделать скриншот" title="Скриншот" @click="takeVideoScreenshot">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M4 7h3l1.5-2h7L17 7h3a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1Z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
            </button>
            <button type="button" class="system-pip-btn" :class="{ active: systemPipActive }"
              :aria-pressed="systemPipActive" :disabled="useCustomPlayer || systemPipPending || duration <= 0 || (playerMode === 'own' ? !ownPlayerSources.length : !kodikLink)"
              :title="systemPipActive ? 'Вернуть видео в плеер' : 'Отдельное окно поверх всех программ'" @click="systemPip.toggle">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="2" y="3" width="20" height="18" rx="2"/><rect x="12" y="12" width="8" height="7" rx="1" fill="currentColor" stroke="none"/></svg>
              {{ systemPipActive ? '' : '' }}
            </button>
            <!-- <button type="button" class="watch-fullscreen-btn" :disabled="(!kodikLink && !ownPlayerSources.length && !customVideoUrl)"
              :aria-label="mainFullscreen ? 'Выйти из полноэкранного режима' : 'Полноэкранный режим'"
              :title="mainFullscreen ? 'Выйти из полноэкранного режима' : 'Полноэкранный режим'" @click="toggleMainFullscreen">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
            </button> -->
          </div>
          <p v-if="systemPipError || playerWindowError || (ownPlayerError && ownPlayerSources.length)" class="player-window-error" role="alert">{{ systemPipError || playerWindowError || ownPlayerError }}</p>
        </div>

        <!-- <ExcerptCapture v-if="anime && kodikLink && !useCustomPlayer" ref="excerptCapture" :anime-id="anime.id" :link="kodikLink" :season="currentSeason" :episode="currentEpisode" :translation-id="selectedTranslation?.id" @request-time="kodikPlayer?.getTime()" /> -->

        <p
          v-if="openingVideoState.error || openingAudioState.error"
          class="qdl-err-text"
        >
          <SakuraIcon name="warning" /> Опенинг:
          {{ openingVideoState.error || openingAudioState.error }}
        </p>
        <p
          v-if="endingVideoState.error || endingAudioState.error"
          class="qdl-err-text"
        >
          <SakuraIcon name="warning" /> Эндинг:
          {{ endingVideoState.error || endingAudioState.error }}
        </p>
        <p v-if="episodeDownloadState.error" class="qdl-err-text">
          <SakuraIcon name="warning" /> Серия:
          {{ episodeDownloadState.error }}
        </p>

        <div v-if="showClipModal" class="clip-form-inline">
          <div class="clip-times">
            <div class="clip-time-field">
              <label>Начало</label>
              <input
                v-model="clipStartInput"
                class="clip-time-input"
                placeholder="0:00"
                :disabled="customState.loading"
              />
            </div>
            <div class="clip-time-arrow">→</div>
            <div class="clip-time-field">
              <label>Конец</label>
              <input
                v-model="clipEndInput"
                class="clip-time-input"
                placeholder="1:30"
                :disabled="customState.loading"
              />
            </div>
          </div>
          <div class="clip-label-row">
            <input
              v-model="clipLabel"
              class="clip-label-input"
              placeholder="Название (необязательно)"
              :disabled="customState.loading"
              maxlength="40"
            />
          </div>
          <div class="clip-hint" v-if="duration > 0">
            Текущее время: <b>{{ formatSec(currentTime) }}</b> /
            {{ formatSec(duration) }}
            <button
              class="clip-hint-btn"
              @click="setClipFromCurrent"
              :disabled="customState.loading"
            >
              ← Вставить
            </button>
          </div>
          <div class="clip-actions">
            <button
              class="tdc-btn clip-download-btn"
              :class="{
                'tdc-loading': customState.loading,
                'tdc-done': customState.done,
              }"
              :disabled="
                customState.loading || !clipStartInput || !clipEndInput
              "
              @click="handleDownloadSegment"
            >
              <span v-if="customState.loading" class="tdc-spinner"></span>
              <span v-else-if="customState.done">✓</span>
              <span v-else
                ><svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" /></svg
              ></span>
              <span class="tdc-label">{{
                customState.loading
                  ? `Обработка... ${customState.progress}%`
                  : customState.done
                    ? "Готово ✓"
                    : "Скачать MP4"
              }}</span>
              <div v-if="customState.loading" class="tdc-progress-bar">
                <div
                  class="tdc-progress-fill"
                  :style="{ width: customState.progress + '%' }"
                ></div>
              </div>
            </button>
            <button
              class="clip-cancel-btn"
              @click="showClipModal = false"
              :disabled="customState.loading"
            >
              ✕
            </button>
          </div>
          <p v-if="customState.error" class="tdc-error-text">
            <SakuraIcon name="warning" /> {{ customState.error }}
          </p>
        </div>

        <div class="anime-info-under">
          <div class="anime-header">
            <h1 class="anime-title" style="font-size: 2rem;">
              {{ publicSeo?.h1 || anime?.title_ru || anime?.title_en }}
            </h1>
            <div class="anime-badges">
              <span v-if="anime?.year" class="badge year-badge">{{
                anime.year
              }}</span>
              <span v-if="anime?.kind" class="badge kind-badge">{{
                getKindText(anime.kind)
              }}</span>
              <span v-if="anime?.episodes" class="badge episodes-badge"
                >{{ anime.episodes }} эп.</span
              >
              <span class="badge status-badge" :class="anime?.status">
                {{ getStatusText(anime?.status || "") }}
              </span>
            </div>
          </div>

          <p class="anime-description">
            {{ anime?.description || publicSeo?.text || "Описание отсутствует" }}
          </p>
        </div>
      </div>

      <div class="right-column">
        <section v-if="playlistId" class="watch-playlist" aria-label="Очередь плейлиста">
          <header class="watch-playlist__header">
            <div class="watch-playlist__heading">
              <span class="watch-playlist__eyebrow">Плейлист</span>
              <router-link v-if="playlistContext" :to="`/playlist/${playlistContext.id}`" class="watch-playlist__title">
                {{ playlistContext.title }}
              </router-link>
              <span v-else class="watch-playlist__title">Очередь просмотра</span>
            </div>
            <span v-if="playlistItems.length" class="watch-playlist__counter">
              {{ currentPlaylistIndex + 1 }} / {{ playlistItems.length }}
            </span>
          </header>
          <div v-if="playlistLoading" class="watch-playlist__state">Загружаем аниме…</div>
          <div v-else-if="playlistError" class="watch-playlist__state is-error">{{ playlistError }}</div>
          <div v-else class="watch-playlist__items">
            <button
              v-for="(item, index) in playlistItems"
              :key="item.id"
              type="button"
              class="watch-playlist__item"
              :class="{ active: isCurrentPlaylistItem(item) }"
              :aria-current="isCurrentPlaylistItem(item) ? 'true' : undefined"
              @click="openPlaylistItem(item)"
            >
              <span class="watch-playlist__index">
                <svg v-if="isCurrentPlaylistItem(item)" width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="5 3 19 12 5 21 5 3" /></svg>
                <template v-else>{{ index + 1 }}</template>
              </span>
              <span class="watch-playlist__poster">
                <img v-if="item.anime_poster" :src="getMediaUrl(item.anime_poster)" alt="" loading="lazy" />
                <SakuraIcon v-else name="tv" :size="18" />
              </span>
              <span class="watch-playlist__copy">
                <strong>{{ item.anime_title }}</strong>
                <small>{{ [item.anime_year, item.anime_kind].filter(Boolean).join(' · ') || 'Аниме' }}</small>
              </span>
            </button>
          </div>
        </section>

        <div v-else class="poster-block" ref="posterBlockRef">
          <div v-if="posterSrc" class="poster-card">
            <div class="poster-image-wrapper">
              <img
                :src="posterSrc"
                :alt="anime?.title_ru || anime?.title_en || publicSeo?.h1"
                class="anime-poster-img"
                @error="
                  (e) =>
                    ((e.target as HTMLImageElement).style.display = 'none')
                "
              />
              <router-link
                :to="`/anime/${anime?.slug || anime?.id}`"
                class="more-info-btn"
                aria-label="Подробнее об аниме"
              >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
              </router-link>
            </div>
          </div>
        </div>

        <div v-if="anime?.episodes" class="episodes-card">
          <div class="ec-header">
            <div class="ec-header-actions">
              <div class="ep-search-wrap">
                <svg
                  class="ep-search-icon"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <input
                  v-model="episodeSearchQuery"
                  class="ep-search-input"
                  type="text"
                  placeholder="Поиск серии..."
                />
              </div>
              <button class="btn-sync-sm" @click="showSyncModal = true">
                <SakuraIcon name="settings" />
              </button>
            </div>
          </div>

          <EpisodeList
            :total-episodes="epTotalEpisodes || anime.episodes"
            :current-season="currentSeason"
            :current-episode="currentEpisode"
            :episodes="epEpisodes"
            :watched-count="epWatchedCount"
            :progress-percent="epPercent"
            :next-episode="epNextEpisode"
            :episode-groups="episodeGroups"
            :search-query="episodeSearchQuery"
            @select-episode="onSelectEpisodeFromList"
            @select-season="onSelectSeason"
            @mark-watched="onMarkWatched"
            @undo-mark="onUndoMark"
            @skip-episode="onSkipEpisode"
            @open-sync="showSyncModal = true"
          />
        </div>
<!--
        <div class="actions-card">
          <button
            @click="toggleFavorite"
            class="btn btn-secondary action-btn"
            :class="{
              'is-favorite': isInFavorites,
              'is-loading': favoriteLoading,
            }"
            :disabled="favoriteLoading"
          >
            <span v-if="favoriteLoading" class="action-spinner"></span>
            <span v-else-if="isInFavorites" class="action-icon-filled">
              <SakuraIcon name="heart" />
            </span>
            <span v-else class="action-icon">♡</span>
            <span class="action-label">{{
              isInFavorites ? "В избранном" : "В избранное"
            }}</span>
          </button>
          <button @click="shareAnime" class="btn btn-secondary action-btn">
            <span class="action-icon">↗</span>
            <span class="action-label">Поделиться</span>
          </button>
        </div> -->
      </div>
    </div>

    <hr style="width: 95%; border: none; height: 1px; background-color: #23162c; margin: 0 auto;">

    <div
      v-if="franchise && franchise.entries?.length > 0"
      ref="franchiseSectionRef"
      id="franchise-section"
    >
      <FranchiseAnimeCarousel
        :name="franchise.name || 'Франшиза'"
        :franchise-id="franchise.id"
        :franchise-slug="franchise.slug"
        :current-anime-id="anime?.id"
        :entries="franchise.entries"
      />
    </div>

    <Transition name="fade">
      <button
        v-if="showFranchiseScrollButton"
        class="scroll-to-franchise-btn"
        @click="scrollToFranchise"
        title="Перейти к другим частям франшизы"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path d="M12 5v14M19 12l-7 7-7-7" />
        </svg>
      </button>
    </Transition>

    <AddCustomDubModal
      :show="showAddDubModal"
      :anime-id="anime?.id ?? 0"
      :anime-title="anime?.title_ru || anime?.title_en || ''"
      @close="showAddDubModal = false"
      @dub-added="onDubAdded"
    />


    <EpisodeProgressModal
      :show="showSyncModal"
      :anime-title="anime?.title_ru || anime?.title_en || ''"
      :total-episodes="epTotalEpisodes || anime?.episodes || 0"
      :current-season="currentSeason"
      :current-episode="currentEpisode"
      :episode-groups="episodeGroups"
      @close="showSyncModal = false"
      @apply="handleSyncApply"
    />
  </div>
</template>

<script setup lang="ts">
import { preparedDownload } from '@/api/backgroundWork';

import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import { seoPage } from '@/composables/useSeo';
import { useRoute, RouterLink } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import apiClient, { isRequestCancelled } from "@/api/client";
import { normalizeKodikPlayerLink } from "@/config/kodik";
import ExcerptCapture from "@/components/excerpts/ExcerptCapture.vue";
import KodikPlayer from "@/components/Players/KodikPlayer.vue";
import AniLuxPlayer from "@/components/Players/AniLuxPlayer.vue";
import CustomVideoPlayer from "@/components/Players/CustomVideoPlayer.vue";
import { createSystemPictureInPicture } from '@/lib/systemPictureInPicture';
import { deliverScreenshot, type CapturedVideoFrame } from '@/lib/videoScreenshot';
import AddCustomDubModal from "@/components/modal/anime/AddCustomDubModal.vue";
import EpisodeProgressModal from "@/components/modal/anime/EpisodeProgressModal.vue";
import EpisodeList from "@/components/Cards/EpisodeList.vue";
import FranchiseAnimeCarousel from "@/components/anime/FranchiseAnimeCarousel.vue";
import type { FranchiseCarouselEntry } from "@/types/franchise";
import { getTranslationAvatarUrl } from "@/utils/translationAvatars";
import { useEpisodeProgress } from "@/composables/useEpisodeProgress";
import { useToast } from "@/composables/useToast";
import { useAnimeTab } from "@/composables/useAnimeTab";
import { useThemeDownloader } from "@/composables/useThemeDownloader";
import { getMediaUrl } from "@/api/client";
import { useProgressSync } from "@/composables/useProgressSync";
import { useWatchProgressStore } from "@/stores/watchProgress";
import { event as analyticsEvent, reportTechnicalError } from "@/analytics";
import type {
  EpisodeProgressItem,
  EpisodeTarget,
} from "@/composables/useEpisodeProgress";
import {
  buildEpisodeGroups,
  episodeForSeason,
  hasTranslationSeason,
  nextEpisodeInGroups,
  resolveDefaultSeason,
  resolveEpisodeTarget,
} from "@/lib/playerSeasons";
import type { PlayerEpisodeGroup } from "@/lib/playerSeasons";
import playlistsApi, { type Playlist, type PlaylistItem } from '@/api/playlists';
import {
  extractKodikTranslations,
  findKodikMaterialForAnime,
} from '@/lib/kodikWrapper';

interface WatchAnime {
  id: number;
  kodik_link?: string;
  slug?: string;
  name?: string;
  title_ru?: string;
  title_en?: string;
  year?: number;
  kind?: string;
  status?: string;
  score?: number;
  description?: string;
  episodes?: number;
  seasons?: Record<string, { episodes?: Record<string, string> } | null>;
  last_season?: number | null;
  seasons_count?: number;
  genres?: Array<string | { id: number; name: string }>;
  franchise_id?: number;
  poster?: string;
  poster_image_url?: string;
  poster_url?: string;
}

interface WatchFranchiseEntry extends FranchiseCarouselEntry {
  franchise_order?: number;
}

interface WatchFranchise {
  id: number;
  slug?: string;
  name: string;
  entries: WatchFranchiseEntry[];
}

interface HlsSource {
  quality: string;
  url: string;
  type?: string;
}

interface PlaybackStream {
  id: string;
  label: string;
  sources: HlsSource[];
  translations: PlaybackTranslation[];
  translationId: number | string | null;
  episodeGroups: PlayerEpisodeGroup[];
  resolvedEpisode?: number;
}

interface TranslationItem {
  id: number | string;
  name: string;
  type?: string;
  quality?: string | number;
  is_custom?: boolean;
  kodik_link?: string;
  logo?: string;
  episodes_done?: number;
  total_episodes?: number;
  last_season?: number | null;
  seasons?: Record<string, { title?: string | null; episodes?: number[] | null } | null>;
}

interface PlaybackTranslation extends TranslationItem {
  sources: HlsSource[];
}

const route = useRoute();
const authStore = useAuthStore();
const progressStore = useWatchProgressStore();
const toast = useToast();
const { downloadTheme, downloadSegment } = useThemeDownloader();

const props = defineProps<{
  slug: string;
}>();

const openingVideoState = ref({
  loading: false,
  progress: 0,
  error: "",
  done: false,
});
const openingAudioState = ref({
  loading: false,
  progress: 0,
  error: "",
  done: false,
});
const endingVideoState = ref({
  loading: false,
  progress: 0,
  error: "",
  done: false,
});
const endingAudioState = ref({
  loading: false,
  progress: 0,
  error: "",
  done: false,
});

const customState = ref({
  loading: false,
  progress: 0,
  error: "",
  done: false,
});

const episodeDownloadState = ref({
  loading: false,
  progress: 0,
  error: "",
  done: false,
});

const handleDownloadOpening = (format: "video" | "audio" = "video") => {
  if (!anime.value?.id) return;
  const state = format === "video" ? openingVideoState : openingAudioState;
  if (state.value.loading) return;

  downloadTheme({
    animeId: anime.value.id,
    kind: "opening",
    episode: currentEpisode.value,
    season: currentSeason.value,
    translationId: selectedTranslation.value?.id,
    animeTitle: anime.value?.title_ru || anime.value?.title_en || "",
    format,
    state,
  });
};

const handleDownloadEnding = (format: "video" | "audio" = "video") => {
  if (!anime.value?.id) return;
  const state = format === "video" ? endingVideoState : endingAudioState;
  if (state.value.loading) return;

  downloadTheme({
    animeId: anime.value.id,
    kind: "ending",
    episode: currentEpisode.value,
    season: currentSeason.value,
    translationId: selectedTranslation.value?.id,
    animeTitle: anime.value?.title_ru || anime.value?.title_en || "",
    format,
    state,
  });
};

const handleDownloadEpisode = async () => {
  if (!anime.value?.id || episodeDownloadState.value.loading) return;
  episodeDownloadState.value = {
    loading: true,
    progress: 10,
    error: "",
    done: false,
  };
  try {
    const { id } = anime.value;
    const params: Record<string, string> = {
      episode: String(currentEpisode.value),
      season: String(currentSeason.value),
      start: "0",
      end: "99999",
      label: `Episode ${currentEpisode.value}`,
    };
    if (selectedTranslation.value?.id)
      params.translation_id = String(selectedTranslation.value.id);

    const response = await preparedDownload(`/anime/${id}/clip/`, {
      params,
      responseType: "blob",
      timeout: 0,
      onDownloadProgress: (evt) => {
        if (evt.total && evt.total > 0) {
          episodeDownloadState.value.progress =
            10 + Math.round((evt.loaded / evt.total) * 85);
        } else {
          episodeDownloadState.value.progress = Math.min(
            90,
            episodeDownloadState.value.progress + 3,
          );
        }
      },
    });

    episodeDownloadState.value.progress = 97;
    const animeTitle =
      anime.value?.title_ru || anime.value?.title_en || "anime";
    const label = `Episode ${currentEpisode.value}`;
    const disposition = response.headers["content-disposition"] || "";
    let filename = `${animeTitle} - ${label}.mp4`;
    const fnMatch =
      disposition.match(/filename\*=UTF-8''([^;\n]+)/) ||
      disposition.match(/filename="?([^";\n]+)"?/);
    if (fnMatch) filename = decodeURIComponent(fnMatch[1]);

    const url = URL.createObjectURL(response.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), TIMING.REVOKE_URL_DELAY);

    episodeDownloadState.value = {
      loading: false,
      progress: 100,
      error: "",
      done: true,
    };
    setTimeout(() => {
      episodeDownloadState.value.done = false;
    }, 3000);
  } catch (err: unknown) {
    let message = (err instanceof Error && err.message) || "Ошибка";
    if ((err as { response?: { data?: Blob } }).response?.data instanceof Blob) {
      try {
        const blobText = await (
          err as { response: { data: Blob } }
        ).response.data.text();
        message = JSON.parse(blobText).error || message;
      } catch {
        /**/
      }
    }
    episodeDownloadState.value = {
      loading: false,
      progress: 0,
      error: message,
      done: false,
    };
  }
};

const showClipModal = ref(false);
const clipStartInput = ref("");
const clipEndInput = ref("");
const clipLabel = ref("clip");

const parseTimeInput = (val: string): number => {
  const v = val.trim();
  if (/^\d+$/.test(v)) return parseInt(v, 10);
  const parts = v.split(":").map(Number);
  if (parts.length === 2) return (parts[0] || 0) * 60 + (parts[1] || 0);
  if (parts.length === 3)
    return (parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0);
  return 0;
};

const formatSec = (s: number) => {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
};

const setClipFromCurrent = () => {
  clipStartInput.value = formatSec(Math.max(0, currentTime.value - 2));
  clipEndInput.value = formatSec(
    Math.min(duration.value || 9999, currentTime.value + 88),
  );
};

const handleDownloadSegment = () => {
  if (!anime.value?.id) return;
  const start = parseTimeInput(clipStartInput.value);
  const end = parseTimeInput(clipEndInput.value);
  if (end <= start) {
    customState.value.error = "Конец должен быть позже начала";
    return;
  }
  customState.value.error = "";
  downloadSegment({
    animeId: anime.value.id,
    episode: currentEpisode.value,
    season: currentSeason.value,
    translationId: selectedTranslation.value?.id,
    startSec: start,
    stopSec: end,
    label: clipLabel.value || "clip",
    animeTitle: anime.value?.title_ru || anime.value?.title_en || "",
    state: customState,
  });
};

let epProgress: ReturnType<typeof useEpisodeProgress> | null = null;
const { bump: bumpProgressSync, watchVersion: watchProgressSyncVersion } =
  useProgressSync();
const showSyncModal = ref(false);
const epWatchedCount = ref(0);
const epPercent = ref(0);
const epNextEpisode = ref<EpisodeTarget | null>(null);
const epEpisodes = ref<Map<string, EpisodeProgressItem>>(new Map());
const epTotalEpisodes = ref(0);
const librarySeason = ref(1);
const libraryEpisode = ref(0);
const resumePosition = ref(0);
const episodeSearchQuery = ref("");

const anime = ref<WatchAnime | null>(null);
const playlistContext = ref<Playlist | null>(null);
const playlistItems = ref<PlaylistItem[]>([]);
const playlistLoading = ref(false);
const playlistError = ref('');
const playlistId = computed(() => typeof route.query.playlist === 'string' ? route.query.playlist : '');
const currentPlaylistIndex = computed(() => {
  if (!anime.value) return -1;
  return playlistItems.value.findIndex(item => item.anime_id === anime.value?.id || item.anime_slug === props.slug);
});

const isCurrentPlaylistItem = (item: PlaylistItem) =>
  item.anime_id === anime.value?.id || item.anime_slug === props.slug;

const playlistItemTarget = (item: PlaylistItem) =>
  item.anime_slug || item.anime_id || (typeof item.anime === 'number' ? item.anime : null);

const openPlaylistItem = (item: PlaylistItem) => {
  const target = playlistItemTarget(item);
  if (!target || !playlistId.value) return;
  void router.push({
    name: 'anime-watch',
    params: { slug: String(target) },
    query: { playlist: playlistId.value, episode: String(item.episode_number || 1) },
  });
};

const loadPlaylistContext = async () => {
  const id = playlistId.value;
  playlistContext.value = null;
  playlistItems.value = [];
  playlistError.value = '';
  if (!id) return;
  playlistLoading.value = true;
  try {
    const [{ data: details }, { data: itemPage }] = await Promise.all([
      playlistsApi.getPlaylist(id),
      playlistsApi.getPlaylistItems(id, { page: 1, page_size: 100, ordering: 'position' }),
    ]);
    if (id !== playlistId.value) return;
    playlistContext.value = details;
    playlistItems.value = itemPage.results || details.items || [];
  } catch {
    if (id === playlistId.value) playlistError.value = 'Не удалось загрузить очередь плейлиста';
  } finally {
    if (id === playlistId.value) playlistLoading.value = false;
  }
};
const publicSeo = computed(() => seoPage.value?.status === 200 && seoPage.value.kind === 'anime' ? seoPage.value : null);
const animeTab = ref<ReturnType<typeof useAnimeTab> | null>(null);
const franchise = ref<WatchFranchise | null>(null);
const kodikLink = ref("");
const customVideoUrl = ref("");
const loading = ref(true);
const loadingTranslations = ref(false);
const error = ref("");
const autoplay = ref(false);
const useCustomPlayer = ref(false);
const storedPlayerMode = localStorage.getItem("anime_player_mode");
const playerMode = ref<"own" | "kodik">(storedPlayerMode === "own" ? "own" : "kodik");
const ownPlayerMounted = ref(playerMode.value === "own");
const kodikPlayerMounted = ref(playerMode.value === "kodik");
const ownPlayerSources = ref<HlsSource[]>([]);
const ownPlayerStreams = ref<PlaybackStream[]>([]);
const selectedOwnStreamId = ref("primary");
const ownPlayerStreamOptions = computed(() =>
  ownPlayerStreams.value.map(({ id, label }) => ({ id, label })),
);
const selectedOwnPlaybackStream = computed(() =>
  ownPlayerStreams.value.find((stream) => stream.id === selectedOwnStreamId.value) ?? null,
);
const ownSourceKey = ref("");
let ownLoadVersion = 0;
const ownPlayerPreview = ref("");
const ownPlayerLoading = ref(false);
const ownPlayerError = ref("");
let suppressSelectionReload = false;

const currentSeason = ref(1);
const currentEpisode = ref(1);
const selectedTranslation = ref<TranslationItem | null>(null);
const translations = ref<TranslationItem[]>([]);
const allowFlat = ref(false);
const flatLabel = computed(() => {
  const kind = anime.value?.kind;
  if (kind === "movie") return "Фильм";
  if (kind === "ova") return "OVA";
  if (kind === "ona") return "ONA";
  if (kind === "special") return "Спешл";
  return "Серии";
});
const showAddDubModal = ref(false);

const currentTime = ref(0);
const duration = ref(0);
const isPlaying = ref(false);
const ownPlayback = ref({ currentTime: 0, duration: 0 });
const kodikPlayback = ref({ currentTime: 0, duration: 0 });

const playerContainer = ref<HTMLElement | null>(null);
const excerptCapture = ref<InstanceType<typeof ExcerptCapture> | null>(null);
const kodikPlayer = ref<InstanceType<typeof KodikPlayer> | null>(null);

interface PlayerApi {
  play: () => void;
  pause: () => void;
  seek: (seconds: number) => void;
  getCurrentTime: () => number;
  getDuration: () => number;
  prepareTranslationSwitch?: () => void;
  captureFrame?: () => CapturedVideoFrame;
}

const ownPlayer = ref<InstanceType<typeof AniLuxPlayer> & PlayerApi | InstanceType<typeof CustomVideoPlayer> & PlayerApi | null>(null);
const showPlayerPlaceholder = computed(() => {
  if (useCustomPlayer.value) return !customVideoUrl.value;
  if (playerMode.value === "own") return !ownPlayerMounted.value;
  return !kodikPlayerMounted.value || !kodikLink.value;
});
const screenshotPending = ref(false);
const takeVideoScreenshot = async () => {
  if (screenshotPending.value || playerMode.value !== "own" || useCustomPlayer.value) return;
  const player = ownPlayer.value;
  if (!player?.captureFrame) return;

  screenshotPending.value = true;
  try {
    const frame = player.captureFrame();
    const base = (anime.value?.title_ru || anime.value?.title_en || props.slug || "anilux")
      .replace(/[<>:"/\\|?*\u0000-\u001F]/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 80) || "anilux";
    const delivery = await deliverScreenshot(
      frame.blob,
      `${base} - S${currentSeason.value}E${currentEpisode.value}.png`,
    );
    if (delivery === "copied") toast.success("Скриншот скопирован");
    else if (delivery === "downloaded") toast.success("Скриншот сохранён");
    else if (delivery === "shared") toast.success("Скриншот готов");
  } catch (error) {
    toast.error(error instanceof Error ? error.message : "Не удалось сделать скриншот");
  } finally {
    screenshotPending.value = false;
  }
};
const systemPip = createSystemPictureInPicture(() => {
  if (useCustomPlayer.value) return null;
  if (playerMode.value === "own") {
    return ownPlayer.value as unknown as {
      enterPip(): Promise<void>;
      exitPip(): Promise<void>;
    } | null;
  }
  return kodikPlayer.value;
});
const { active: systemPipActive, pending: systemPipPending, error: systemPipError } = systemPip;
const mainFullscreen = ref(false), playerWindowError = ref('');
const syncMainFullscreen = () => { mainFullscreen.value = document.fullscreenElement === playerContainer.value?.parentElement; };
const toggleMainFullscreen = async () => {
  playerWindowError.value = '';
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await playerContainer.value?.parentElement?.requestFullscreen();
  } catch { playerWindowError.value = 'Браузер не смог открыть полноэкранный режим.'; }
};
const posterBlockRef = ref<HTMLElement | null>(null);

let playerResizeObserver: ResizeObserver | null = null;

const updatePlayerHeightVar = () => {
  const player = playerContainer.value;
  if (!player) return;
  const h = player.getBoundingClientRect().height;
  if (h > 0) {
    document.documentElement.style.setProperty("--player-height", `${h}px`);
  }
};

const setupPlayerHeightSync = () => {
  const player = playerContainer.value;
  if (!player) return;

  updatePlayerHeightVar();

  if (playerResizeObserver) playerResizeObserver.disconnect();
  playerResizeObserver = new ResizeObserver(() => updatePlayerHeightVar());
  playerResizeObserver.observe(player);

  window.addEventListener("resize", updatePlayerHeightVar);
};

const teardownPlayerHeightSync = () => {
  if (playerResizeObserver) {
    playerResizeObserver.disconnect();
    playerResizeObserver = null;
  }
  window.removeEventListener("resize", updatePlayerHeightVar);
  document.documentElement.style.removeProperty("--player-height");
};

const watchProgress = ref<Record<number, number>>({});
const lastStoreUpdateTime = ref(0);
const isInLibrary = ref(false);
const libraryItemId = ref<number | null>(null);
const openingStartTime = ref<number | null>(null);
const endingStartTime = ref<number | null>(null);
const addedToLibrary = ref(false);
const episodeMarkedWatched = ref(false);

import { TIMING } from "@/constants";
import { useRouter } from "vue-router";
import { useFavorite } from "@/composables/useFavorite";

const router = useRouter();

const {
  isFavorite: isInFavorites,
  loading: favoriteLoading,
  checkStatus: checkIsFavorite,
  toggleFavorite,
} = useFavorite(() => anime.value?.id ?? 0);

if (!authStore.isAuthenticated) {
  watch(isInFavorites, (val) => {
    if (val) {
      toast.info("Войдите, чтобы добавлять в избранное", { duration: 3000 });
    }
  });
}

const handleToggleFavorite = async () => {
  if (!authStore.isAuthenticated) {
    toast.info("Войдите, чтобы добавлять в избранное", { duration: 3000 });
    return;
  }
  await toggleFavorite();
};

const getGenreLink = (genre: string | { name: string }) => {
  const genreName = typeof genre === "object" ? genre.name : genre;
  const slug = genreName
    .toLowerCase()
    .replace(/[^a-zа-яё0-9]/g, "-")
    .replace(/-+/g, "-");
  return `/anime?genres=${encodeURIComponent(slug)}`;
};

const franchiseSectionRef = ref<HTMLElement | null>(null);
const isNearTop = ref(true);

const checkScrollPosition = () => {
  if (!franchiseSectionRef.value) {
    isNearTop.value = true;
    return;
  }
  const rect = franchiseSectionRef.value.getBoundingClientRect();
  isNearTop.value = rect.top > window.innerHeight * 0.5;
};

const scrollToFranchise = () => {
  franchiseSectionRef.value?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
};

const showFranchiseScrollButton = computed(() => {
  return anime.value?.franchise_id && isNearTop.value;
});

const selectedTranslationId = computed(
  () => selectedTranslation.value?.id?.toString() || "0",
);

const episodeGroups = computed(() =>
  buildEpisodeGroups({
    translations: translations.value,
    selectedTranslationId: selectedTranslation.value?.id ?? null,
    seasons: anime.value?.seasons ?? null,
    episodes: anime.value?.episodes ?? null,
    lastSeason: anime.value?.last_season ?? null,
    allowFlat: allowFlat.value,
    flatLabel: flatLabel.value,
  }),
);

const ownPlayerTranslations = computed<TranslationItem[]>(() =>
  selectedOwnStreamId.value === "primary"
    ? translations.value
    : (selectedOwnPlaybackStream.value?.translations ?? []),
);
const ownPlayerEpisodeGroups = computed<PlayerEpisodeGroup[]>(() =>
  selectedOwnStreamId.value === "primary"
    ? episodeGroups.value
    : (selectedOwnPlaybackStream.value?.episodeGroups ?? []),
);
const ownPlayerTranslationId = computed<number | string | null>(() =>
  selectedOwnStreamId.value === "primary"
    ? (selectedTranslation.value?.id ?? null)
    : (selectedOwnPlaybackStream.value?.translationId ?? null),
);
const ownPlayerTranslationsLoading = computed(() =>
  selectedOwnStreamId.value === "primary" && loadingTranslations.value,
);

const seasonGroup = (season: number) =>
  episodeGroups.value.find((group) => group.season === season) ?? null;

const defaultPlaybackSeason = (requestedSeason?: number | null) =>
  resolveDefaultSeason(
    episodeGroups.value,
    requestedSeason,
    selectedTranslation.value?.last_season ?? anime.value?.last_season ?? null,
  );

const switchTranslationForSeason = (season: number) => {
  const sourceId = seasonGroup(season)?.translationId;
  if (sourceId === null || sourceId === undefined) return false;
  const translation = translations.value.find(
    (item) => String(item.id) === String(sourceId),
  );
  if (
    !translation ||
    translation.is_custom ||
    String(translation.id) === String(selectedTranslation.value?.id ?? "")
  ) {
    return false;
  }

  selectedTranslation.value = translation;
  if (translation.kodik_link) {
    kodikLink.value = normalizeKodikPlayerLink(translation.kodik_link);
  }
  return true;
};

const resetEpisodeRuntime = () => {
  openingStartTime.value = null;
  endingStartTime.value = null;
  episodeMarkedWatched.value = false;
  addedToLibrary.value = isInLibrary.value;
};

const posterSrc = computed((): string | null => {
  if (!anime.value) return getMediaUrl(publicSeo.value?.image) || null;
  const local = anime.value.poster_image_url || anime.value.poster;
  const result = local
    ? getMediaUrl(local) || null
    : anime.value.poster_url || null;
  return result;
});


const syncResumePosition = () => {
  const item = epProgress?.getEpisode(currentSeason.value, currentEpisode.value);
  const position = Math.floor(item?.last_position || 0);
  const duration = Number(item?.duration || 0);
  const nearEnd = duration > 0 && (position >= duration - 5 || position / duration >= 0.95);
  resumePosition.value =
    item?.status === "in_progress" && position >= 10 && !nearEnd ? position : 0;
};

const syncEpRefs = () => {
  if (!epProgress) return;
  epProgress.setEpisodeGroups(episodeGroups.value);
  epWatchedCount.value = epProgress.watchedCount.value;
  epPercent.value = epProgress.progressPercent.value;
  epNextEpisode.value = epProgress.nextEpisodeToWatch.value;
  epEpisodes.value = new Map(epProgress.episodes.value);
  epTotalEpisodes.value =
    epProgress.totalEpisodes.value || anime.value?.episodes || 0;
  syncResumePosition();
};

const loadFranchise = async (franchiseId: number, signal?: AbortSignal, current = () => true) => {
  try {
    const response = await apiClient.get(`/anime/franchises/${franchiseId}/`, { signal });
    if (!current() || signal?.aborted) return;
    franchise.value = {
      id: response.data.id,
      slug: response.data.slug,
      name: response.data.name,
      entries: ((response.data.entries || []) as WatchFranchiseEntry[]).sort(
        (a, b) =>
          Number(a.franchise_order || 0) - Number(b.franchise_order || 0),
      ),
    };
  } catch {
    if (!current() || signal?.aborted) return;
    reportTechnicalError("watch.franchise_failed", "/route/anime-watch");
    franchise.value = null;
  }
};

const getKindLabel = (kind: string) =>
  ({
    tv: "TV",
    movie: "Фильм",
    ova: "OVA",
    ona: "ONA",
    special: "Спешл",
    music: "Клип",
  })[kind] || kind.toUpperCase();

const getKindText = (kind: string) =>
  ({
    tv: "ТВ",
    movie: "Фильм",
    ova: "OVA",
    ona: "ONA",
    special: "Спецвыпуск",
    music: "Музыка",
  })[kind] || kind;

const getStatusText = (status: string | null) => {
  if (!status) return status;

  return {
    'ongoing': 'Онгоинг',
    'finished': 'Завершён',
    'announced': 'Анонсирован',
    'released': 'Завершён'
  }[status] || status;
};

const getTranslationType = (type: string) =>
  ({
    voice: "Озвучка",
    subtitles: "Субтитры",
    raw: "Оригинал",
  })[type] || type;

const getTranslationInitials = (name: string) => {
  if (!name) return "?";
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
};

const getTranslationAvatar = (
  translation: TranslationItem,
): string | undefined => {
  if (translation.logo) return translation.logo;
  return getTranslationAvatarUrl(translation.name);
};

let loadGeneration = 0;
let loadController: AbortController | undefined;
let watchDisposed = false;
let firstVisitTimer: ReturnType<typeof setTimeout> | undefined;
const loadAnime = async () => {
  const version = ++loadGeneration;
  loadController?.abort();
  const controller = new AbortController(); loadController = controller;
  const signal = controller.signal;
  const current = () => !watchDisposed && !signal.aborted && version === loadGeneration;
  clearTimeout(firstVisitTimer);

  try {
    loading.value = true;
    error.value = "";
    ownLoadVersion += 1;
    ownSourceKey.value = "";
    ownPlayerSources.value = [];
    ownPlayerPreview.value = "";
    ownPlayerLoading.value = false;
    ownPlayerError.value = "";
    ownPlayback.value = { currentTime: 0, duration: 0 };
    kodikPlayback.value = { currentTime: 0, duration: 0 };
    currentTime.value = 0;
    duration.value = 0;
    resumePosition.value = 0;
    epProgress?.dispose();
    epProgress = null;
    animeTab.value?.stop();
    animeTab.value = null;
    suppressSelectionReload = true;

    const animeId = props.slug;
    const response = await apiClient.get(`/anime/${animeId}/`, { signal });
    if (!current()) return;
    anime.value = response.data;
    const episodeFromQuery = route.query.episode;
    const parsedEpisode = episodeFromQuery
      ? parseInt(String(episodeFromQuery), 10)
      : NaN;
    const requestedEpisode =
      Number.isInteger(parsedEpisode) && parsedEpisode > 0
        ? parsedEpisode
        : null;
    const requestedSeasonValue = Number(route.query.season);
    const requestedSeason =
      Number.isInteger(requestedSeasonValue) && requestedSeasonValue >= 0
        ? requestedSeasonValue
        : null;
    if (requestedEpisode) autoplay.value = true;

    epProgress = useEpisodeProgress(anime.value!.id);
    const progress = epProgress;
    await Promise.all([checkLibraryStatus(signal, current), checkIsFavorite(), loadTranslations(signal, current), progress.loadProgress()]);
    if (!current()) return;
    const requestedTranslation = translations.value.find(item => String(item.id) === String(route.query.translation));
    if (requestedTranslation) {
      await selectTranslation(requestedTranslation, {
        reload: false,
        adjustSeason: false,
      });
    }

    if (!current()) return;
    epProgress!.setEpisodeGroups(episodeGroups.value);

    const preferredSeason = defaultPlaybackSeason(requestedSeason);
    let initialTarget: EpisodeTarget;
    if (requestedEpisode) {
      initialTarget = resolveEpisodeTarget(
        episodeGroups.value,
        requestedSeason ?? preferredSeason,
        requestedEpisode,
      );
    } else if (libraryEpisode.value > 0) {
      const savedTarget = {
        season: librarySeason.value,
        episode: libraryEpisode.value,
      };
      const nextTarget = epProgress.isWatched(
        savedTarget.season,
        savedTarget.episode,
      )
        ? nextEpisodeInGroups(
            episodeGroups.value,
            savedTarget.season,
            savedTarget.episode,
          )
        : null;
      initialTarget = resolveEpisodeTarget(
        episodeGroups.value,
        nextTarget?.season ?? savedTarget.season,
        nextTarget?.episode ?? savedTarget.episode,
      );
    } else {
      initialTarget = epProgress.nextEpisodeToWatch.value ?? {
        season: preferredSeason,
        episode: 1,
      };
    }

    if (!useCustomPlayer.value) {
      switchTranslationForSeason(initialTarget.season);
      epProgress.setEpisodeGroups(episodeGroups.value);
      initialTarget = resolveEpisodeTarget(
        episodeGroups.value,
        initialTarget.season,
        initialTarget.episode,
      );
    }
    currentSeason.value = initialTarget.season;
    currentEpisode.value = initialTarget.episode;
    await nextTick();
    suppressSelectionReload = false;

    await loadKodikPlayer();
    if (!current()) return;
    if (playerMode.value === "own" && !useCustomPlayer.value) {
      await loadOwnPlayer();
      if (!current()) return;
    }
    loadWatchProgress();

    if (anime.value?.id) {
      const tab = useAnimeTab(anime.value.id);
      if (tab) {
        animeTab.value = tab;
        tab.start();
      }
      syncEpRefs();

      if (anime.value.franchise_id) {
        await loadFranchise(anime.value.franchise_id, signal, current);
        if (!current()) return;
      }

if (
  authStore.isAuthenticated &&
  epProgress.watchedCount.value === 0 &&
  epProgress.progressPercent.value === 0 &&
  !route.query.episode
) {
  firstVisitTimer = setTimeout(() => { if (current()) showFirstVisitToast(); }, 800);
}
    }

    await nextTick();
    setupPlayerHeightSync();
  } catch (failure) {
    if (!current() || isRequestCancelled(failure)) return;
    reportTechnicalError("watch.anime_failed", "/route/anime-watch");
    error.value = "Не удалось загрузить аниме";
  } finally {
    if (current()) { suppressSelectionReload = false; loading.value = false; }
  }
};

const showFirstVisitToast = () => {
  toast.info("Вы смотрели это аниме ранее?", {
    duration: 8000,
    action: {
      label: "Настроить прогресс",
      handler: () => {
        showSyncModal.value = true;
      },
    },
  });
};

const checkLibraryStatus = async (signal?: AbortSignal, current = () => true) => {
  if (!authStore.isAuthenticated) return;
  try {
    const response = await apiClient.get("/users/library/check_anime/", { params: { anime_id: anime.value?.id }, signal });
    if (!current() || signal?.aborted) return;
    const item = response.data.in_library ? response.data.item : null;

    if (item) {
      const it = item as { id?: number; current_season?: number; current_episode?: number; anime_id?: number; status?: string; episodes_watched?: number; progress_percentage?: number; anime_episodes_count?: number };
      isInLibrary.value = true;
      libraryItemId.value = it.id ?? null;
      addedToLibrary.value = true;

      librarySeason.value = it.current_season || 1;
      libraryEpisode.value = it.current_episode || 0;

      if (anime.value?.id && it.anime_id) {
        progressStore.setProgress(anime.value.id, {
          status: it.status || null,
          current_season: librarySeason.value,
          current_episode: it.current_episode || 0,
          episodes_watched: it.episodes_watched || 0,
          progress_percentage: it.progress_percentage || 0,
          total_episodes: it.anime_episodes_count || anime.value.episodes || 0,
        });
      }
    } else {
      isInLibrary.value = false;
      libraryItemId.value = null;
    }
  } catch {
    if (!current() || signal?.aborted) return;
    isInLibrary.value = false;
  }
};

const addToLibraryAutomatically = async () => {
  if (!authStore.isAuthenticated) return;
  try {
    const response = await apiClient.post("/users/library/", {
      anime: anime.value?.id,
      status: "started",
    });
    isInLibrary.value = true;
    libraryItemId.value = response.data.id;
    await updateLibraryProgress();
  } catch (err: unknown) {
    const httpErr = err as { response?: { status?: number } };
    if (httpErr.response?.status === 409 || httpErr.response?.status === 400) {
      await checkLibraryStatus();
      if (isInLibrary.value) await updateLibraryProgress();
    } else {
      throw err;
    }
  }
};

const updateLibraryProgress = async (throwOnError = false) => {
  if (!libraryItemId.value) return;
  try {
    const lastWatched = epProgress?.lastWatchedEpisode.value;
    const nextSeason = lastWatched?.season ?? currentSeason.value;
    const nextEpisode = lastWatched?.episode ?? currentEpisode.value;
    await apiClient.patch(`/users/library/${libraryItemId.value}/`, {
      current_season: nextSeason,
      current_episode: nextEpisode,
    });
    progressStore.setProgress(anime.value!.id, {
      current_season: nextSeason,
      current_episode: nextEpisode,
      episodes_watched: epProgress ? epProgress.watchedCount.value : 0,
      progress_percentage: epProgress ? epProgress.progressPercent.value : 0,
      total_episodes: epProgress ? epProgress.totalEpisodes.value : 0,
    });
  } catch (e) {
    if (throwOnError) throw e;
    console.debug("[AnimeWatch] updateLibraryProgress failed", e);
  }
};

const loadTranslations = async (signal?: AbortSignal, current = () => true) => {
  if (!anime.value?.id) return;
  const title = anime.value;
  const kind = title.kind;
  allowFlat.value =
    kind === "movie" ||
    kind === "ova" ||
    kind === "ona" ||
    (anime.value?.episodes ?? 0) <= 1;
  try {
    loadingTranslations.value = true;
    const [response, customResponse] = await Promise.all([
      apiClient.get(`/anime/${title.id}/kodik_translations/`, { signal }),
      apiClient.get(`/anime/${title.id}/custom_dubs/`, { signal }).catch(() => ({ data: { dubs: [] } })),
    ]);
    if (!current() || signal?.aborted) return;
    const kodikTranslations = response.data.translations || [];
    allowFlat.value = allowFlat.value || Boolean(response.data.allow_flat);

    try {
      const customDubs = customResponse.data.dubs || [];
      translations.value = [
        ...kodikTranslations.map((t: Record<string, unknown>) => ({
          ...t,
          is_custom: false,
        })),
        ...customDubs.map((d: Record<string, unknown>) => ({
          ...d,
          is_custom: true,
          type: "voice",
        })),
      ] as TranslationItem[];
    } catch {
      translations.value = kodikTranslations.map(
        (t: Record<string, unknown>) => ({
          ...t,
          is_custom: false,
        }),
      ) as TranslationItem[];
    }

    if (translations.value.length > 0) {
      selectedTranslation.value = translations.value[0] ?? null;
      if (
        selectedTranslation.value &&
        !selectedTranslation.value.is_custom &&
        selectedTranslation.value.kodik_link
      ) {
        kodikLink.value = normalizeKodikPlayerLink(
          selectedTranslation.value.kodik_link,
        );
      }
    }
  } catch {
    if (!current() || signal?.aborted) return;
    translations.value = [];
  } finally {
    if (current() && !signal?.aborted) loadingTranslations.value = false;
  }

  if (current() && !signal?.aborted && !translations.value.length && title) {
    const material = await findKodikMaterialForAnime(title);
    if (!current() || signal?.aborted) return;
    const fallbackTranslations = extractKodikTranslations(material);
    if (fallbackTranslations.length) {
      translations.value = fallbackTranslations.map((translation) => ({
        ...translation,
        is_custom: false,
        kodik_link: material?.link || translation.kodik_link,
      })) as TranslationItem[];
      selectedTranslation.value = translations.value[0] ?? null;
      if (selectedTranslation.value?.kodik_link) {
        kodikLink.value = normalizeKodikPlayerLink(selectedTranslation.value.kodik_link);
      }
    }
  }
};

const loadKodikPlayer = async () => {
  if (!anime.value?.id) return;
  try {
    const response = { data: anime.value };
    const translationLink =
      !selectedTranslation.value?.is_custom &&
      selectedTranslation.value?.kodik_link
        ? selectedTranslation.value.kodik_link
        : null;
    kodikLink.value = normalizeKodikPlayerLink(
      translationLink || response.data.kodik_link || '',
    );
  } catch (err: unknown) {
    reportTechnicalError("watch.player_failed", "/route/anime-watch");
    const httpErr = err as { response?: { status?: number } };
    if (httpErr.response?.status === 404)
      error.value = "Видео для этого аниме не найдено";
    else if (httpErr.response?.status === 503)
      error.value = "Сервис временно недоступен";
    else error.value = "Не удалось загрузить плеер";
  }
};

const currentOwnSourceKey = () =>
  `${currentEpisode.value}:${currentSeason.value}:${selectedTranslation.value?.id ?? ""}`;
const ownSourcesAreCurrent = computed(() =>
  ownPlayerSources.value.length > 0 && ownSourceKey.value === currentOwnSourceKey(),
);

const parseHlsSources = (value: unknown): HlsSource[] =>
  (Array.isArray(value) ? value : []).filter(
    (source: unknown): source is HlsSource => Boolean(
      source && typeof source === "object"
      && typeof (source as HlsSource).quality === "string"
      && typeof (source as HlsSource).url === "string",
    ),
  );

const parsePlaybackTranslations = (value: unknown): PlaybackTranslation[] =>
  (Array.isArray(value) ? value : []).flatMap((translation: unknown) => {
    if (!translation || typeof translation !== "object") return [];
    const candidate = translation as {
      id?: unknown;
      name?: unknown;
      type?: unknown;
      sources?: unknown;
    };
    if (
      (typeof candidate.id !== "string" && typeof candidate.id !== "number")
      || typeof candidate.name !== "string"
    ) return [];
    const sources = parseHlsSources(candidate.sources);
    if (!sources.length) return [];
    return [{
      id: candidate.id,
      name: candidate.name,
      type: typeof candidate.type === "string" ? candidate.type : "voice",
      sources,
    }];
  });

const parsePlaybackEpisodeGroups = (value: unknown): PlayerEpisodeGroup[] =>
  (Array.isArray(value) ? value : []).flatMap((group: unknown) => {
    if (!group || typeof group !== "object") return [];
    const candidate = group as { season?: unknown; label?: unknown; episodes?: unknown };
    const season = Number(candidate.season);
    const episodes = (Array.isArray(candidate.episodes) ? candidate.episodes : [])
      .map(Number)
      .filter((episode) => Number.isInteger(episode) && episode > 0);
    if (!Number.isInteger(season) || season < 0 || !episodes.length) return [];
    return [{
      season,
      label: typeof candidate.label === "string" ? candidate.label : `Сезон ${season}`,
      episodes,
    }];
  });

const loadAlternativeStreams = async (
  version: number,
  requestKey: string,
  selectFirstAvailable = false,
  preferredStreamId = "",
  preferredTranslationId: number | string | null = null,
) => {
  if (!anime.value?.id) return;
  try {
    const { data } = await apiClient.get(`/anime/${anime.value.id}/alternative_streams/`, {
      params: {
        episode: currentEpisode.value,
        season: currentSeason.value,
      },
    });
    if (version !== ownLoadVersion || requestKey !== currentOwnSourceKey()) return;
    const rawStreams = Array.isArray(data.streams) ? data.streams : [];
    const alternatives: PlaybackStream[] = rawStreams.flatMap((stream: unknown) => {
      if (!stream || typeof stream !== "object") return [];
      const candidate = stream as {
        id?: unknown;
        label?: unknown;
        sources?: unknown;
        translations?: unknown;
        translation_id?: unknown;
        episode_groups?: unknown;
        resolved_episode?: unknown;
      };
      if (typeof candidate.id !== "string") return [];
      const translations = parsePlaybackTranslations(candidate.translations);
      const fallbackSources = parseHlsSources(candidate.sources);
      if (!translations.length && !fallbackSources.length) return [];
      const requestedTranslation = translations.find(
        (translation) => String(translation.id) === String(preferredTranslationId ?? candidate.translation_id ?? ""),
      ) ?? translations[0] ?? null;
      const sources = requestedTranslation?.sources ?? fallbackSources;
      return [{
        id: candidate.id,
        label: typeof candidate.label === "string" ? candidate.label : "Резервный",
        sources,
        translations,
        translationId: requestedTranslation?.id ?? null,
        episodeGroups: parsePlaybackEpisodeGroups(candidate.episode_groups),
        resolvedEpisode: Number.isInteger(Number(candidate.resolved_episode))
          ? Number(candidate.resolved_episode)
          : undefined,
      }];
    });
    const firstAlternative = alternatives[0];
    if (!firstAlternative) return;
    const primary = ownPlayerStreams.value.filter((stream) => stream.id === "primary");
    ownPlayerStreams.value = [...primary, ...alternatives];
    const preferred = alternatives.find((stream) => stream.id === preferredStreamId);
    const selectedAlternative = preferred ?? firstAlternative;
    if (selectFirstAvailable || preferred || !ownPlayerSources.value.length) {
      selectedOwnStreamId.value = selectedAlternative.id;
      const resolved = resolveEpisodeTarget(
        selectedAlternative.episodeGroups,
        currentSeason.value,
        selectedAlternative.resolvedEpisode ?? currentEpisode.value,
      );
      if (
        resolved.season !== currentSeason.value
        || resolved.episode !== currentEpisode.value
      ) {
        currentSeason.value = resolved.season;
        currentEpisode.value = resolved.episode;
        resetEpisodeRuntime();
        animeTab.value?.setEpisode(resolved.episode);
        syncResumePosition();
        return;
      }
      ownPlayerSources.value = selectedAlternative.sources;
      ownSourceKey.value = requestKey;
      ownPlayerError.value = "";
    }
  } catch {
  }
};

const loadOwnPlayer = async (adjustForTranslation = false) => {
  if (!anime.value?.id || useCustomPlayer.value) return;
  const version = ++ownLoadVersion;
  const requestKey = currentOwnSourceKey();
  const preferredStreamId = selectedOwnStreamId.value;
  const preferredTranslationId = selectedOwnPlaybackStream.value?.translationId ?? null;
  const preferAlternative = preferredStreamId !== "primary";
  ownPlayerLoading.value = true;
  ownPlayerError.value = "";
  if (!preferAlternative) {
    ownPlayerStreams.value = [];
    selectedOwnStreamId.value = "primary";
    ownPlayerSources.value = [];
  }
  const alternativePromise = loadAlternativeStreams(
    version,
    requestKey,
    preferAlternative,
    preferAlternative ? preferredStreamId : "",
    preferAlternative ? preferredTranslationId : null,
  ).finally(() => {
    if (version === ownLoadVersion && ownSourceKey.value === requestKey) {
      ownPlayerLoading.value = false;
    }
  });
  try {
    const { data } = await apiClient.get(`/anime/${anime.value.id}/kodik_video_url/`, {
      params: {
        episode: currentEpisode.value,
        season: currentSeason.value,
        translation_id: selectedTranslation.value?.id,
      },
    });
    if (version !== ownLoadVersion) return;
    const sources = Array.isArray(data.sources) ? data.sources : [];
    const nextSources = sources.filter(
      (source: unknown): source is HlsSource => Boolean(
        source && typeof source === "object" &&
        typeof (source as HlsSource).quality === "string" &&
        typeof (source as HlsSource).url === "string",
      ),
    );
    if (!nextSources.length && typeof data.m3u8_url === "string") {
      nextSources.push({ quality: "auto", url: data.m3u8_url });
    }
    if (!nextSources.length) {
      throw new Error("Эта озвучка сейчас недоступна");
    }
    if (adjustForTranslation) ownPlayer.value?.prepareTranslationSwitch?.();
    ownPlayerPreview.value = typeof data.preview === "string" ? data.preview : "";
    const primaryStream: PlaybackStream = {
      id: "primary",
      label: "Основной",
      sources: nextSources,
      translations: [],
      translationId: null,
      episodeGroups: [],
    };
    const alternativeSelected =
      selectedOwnStreamId.value !== "primary" && ownSourceKey.value === requestKey;
    if (preferAlternative || alternativeSelected) {
      ownPlayerStreams.value = [
        primaryStream,
        ...ownPlayerStreams.value.filter((stream) => stream.id !== "primary"),
      ];
    } else {
      ownPlayerSources.value = nextSources;
      ownPlayerStreams.value = [primaryStream];
      ownSourceKey.value = requestKey;
    }
  } catch (requestError: unknown) {
    if (version !== ownLoadVersion) return;
    const responseMessage = (requestError as { response?: { data?: { error?: string } } }).response?.data?.error;
    await alternativePromise;
    if (ownSourceKey.value !== requestKey) {
      ownPlayerError.value = responseMessage || (
        preferAlternative
          ? "Поток сейчас недоступен."
          : "Плеер сейчас недоступен. Можно продолжить через Kodik."
      );
    }
    ownPlayerLoading.value = false;
  } finally {
    if (version === ownLoadVersion && ownSourceKey.value === requestKey) {
      ownPlayerLoading.value = false;
    }
  }
};

const savePlaybackState = (mode: "own" | "kodik") => {
  if (mode === "own") {
    ownPlayback.value = {
      currentTime: ownPlayer.value?.getCurrentTime?.() ?? currentTime.value,
      duration: ownPlayer.value?.getDuration?.() ?? duration.value,
    };
    return;
  }
  kodikPlayback.value = {
    currentTime: currentTime.value,
    duration: duration.value,
  };
};

const restorePlaybackState = (mode: "own" | "kodik") => {
  const state = mode === "own" ? ownPlayback.value : kodikPlayback.value;
  currentTime.value = state.currentTime;
  duration.value = state.duration;
};

const setPlayerMode = async (mode: "own" | "kodik") => {
  if (playerMode.value === mode) {
    if (mode === "own" && !useCustomPlayer.value && !ownSourcesAreCurrent.value) {
      ownPlayerMounted.value = true;
      autoplay.value = false;
      await loadOwnPlayer();
    }
    return;
  }

  savePlaybackState(playerMode.value);
  kodikPlayer.value?.pause();
  ownPlayer.value?.pause();
  isPlaying.value = false;
  animeTab.value?.setPlayerActive(false, currentEpisode.value);
  playerMode.value = mode;
  localStorage.setItem("anime_player_mode", mode);
  error.value = "";
  ownPlayerError.value = "";

  if (mode === "own") {
    ownPlayerMounted.value = true;
    autoplay.value = false;
    if (!ownSourcesAreCurrent.value) {
      ownPlayback.value = { currentTime: 0, duration: 0 };
      currentTime.value = 0;
      duration.value = 0;
      await loadOwnPlayer();
      return;
    }
    await nextTick();
    restorePlaybackState("own");
    return;
  }

  kodikPlayerMounted.value = true;
  await nextTick();
  restorePlaybackState("kodik");
};

const selectTranslation = async (
  translation: TranslationItem,
  options: { reload?: boolean; adjustSeason?: boolean } = {},
) => {
  const { reload = true, adjustSeason = true } = options;
  selectedTranslation.value = translation;
  if (translation.is_custom) {
    useCustomPlayer.value = true;
    try {
      const res = await apiClient.get(
        `/anime/${anime.value?.id}/custom_dubs/${translation.id}/video/`,
      );
      customVideoUrl.value = res.data.video_url;
    } catch {
      error.value = "Не удалось загрузить видео";
    }
    return;
  }

  useCustomPlayer.value = false;
  customVideoUrl.value = "";
  if (translation.kodik_link)
    kodikLink.value = normalizeKodikPlayerLink(translation.kodik_link);
  epProgress?.setEpisodeGroups(episodeGroups.value);

  if (adjustSeason) {
    const nextSeason = hasTranslationSeason(translation, currentSeason.value)
      ? currentSeason.value
      : defaultPlaybackSeason(null);
    const nextEpisode = episodeForSeason(
      episodeGroups.value,
      nextSeason,
      currentEpisode.value,
    );
    const selectionChanged =
      nextSeason !== currentSeason.value ||
      nextEpisode !== currentEpisode.value;
    currentSeason.value = nextSeason;
    currentEpisode.value = nextEpisode;
    if (selectionChanged) {
      resetEpisodeRuntime();
      return;
    }
  }

  if (reload && playerMode.value === "own") {
    await loadOwnPlayer(true);
  }
};

const selectEpisodeTarget = (target: EpisodeTarget) => {
  const initial = resolveEpisodeTarget(
    episodeGroups.value,
    target.season,
    target.episode,
  );
  const translationChanged = switchTranslationForSeason(initial.season);
  if (translationChanged) {
    epProgress?.setEpisodeGroups(episodeGroups.value);
  }
  const resolved = translationChanged
    ? resolveEpisodeTarget(
        episodeGroups.value,
        initial.season,
        initial.episode,
      )
    : initial;
  const seasonChanged = resolved.season !== currentSeason.value;
  const episodeChanged = resolved.episode !== currentEpisode.value;

  if (seasonChanged) currentSeason.value = resolved.season;
  if (episodeChanged) currentEpisode.value = resolved.episode;
  if (seasonChanged || episodeChanged) {
    analyticsEvent("episode_selected", {
      selection: seasonChanged ? "season" : "episode",
    });
    resetEpisodeRuntime();
    animeTab.value?.setEpisode(resolved.episode);
    syncResumePosition();
  }
  return { ...resolved, seasonChanged, episodeChanged, translationChanged };
};

const selectEpisode = (episode: number) => {
  selectEpisodeTarget({ season: currentSeason.value, episode });
};

const onSelectEpisodeFromList = (target: EpisodeTarget) => {
  selectEpisodeTarget(target);
};

const onSelectSeason = (season: number) => {
  const group = seasonGroup(season);
  if (!group) return;
  const episode = group.episodes.includes(currentEpisode.value)
    ? currentEpisode.value
    : (group.episodes[0] ?? 1);
  selectEpisodeTarget({ season, episode });
};

const onPlayerSelectEpisode = (payload: EpisodeTarget) => {
  if (selectedOwnStreamId.value !== "primary") {
    const resolved = resolveEpisodeTarget(
      ownPlayerEpisodeGroups.value,
      payload.season,
      payload.episode,
    );
    const seasonChanged = resolved.season !== currentSeason.value;
    const episodeChanged = resolved.episode !== currentEpisode.value;
    if (seasonChanged) currentSeason.value = resolved.season;
    if (episodeChanged) currentEpisode.value = resolved.episode;
    if (seasonChanged || episodeChanged) {
      resetEpisodeRuntime();
      animeTab.value?.setEpisode(resolved.episode);
      syncResumePosition();
    }
    return;
  }
  const result = selectEpisodeTarget(payload);
  if (
    !result.seasonChanged &&
    !result.episodeChanged &&
    result.translationChanged &&
    playerMode.value === "own" &&
    !useCustomPlayer.value
  ) {
    void loadOwnPlayer(true);
  }
};

const onPlayerSelectTranslation = async (id: number | string) => {
  if (selectedOwnStreamId.value !== "primary") {
    const stream = selectedOwnPlaybackStream.value;
    const translation = stream?.translations.find(
      (item) => String(item.id) === String(id),
    );
    if (!stream || !translation || String(stream.translationId) === String(id)) return;
    ownPlayer.value?.prepareTranslationSwitch?.();
    stream.translationId = translation.id;
    stream.sources = translation.sources;
    ownPlayerSources.value = translation.sources;
    ownPlayerError.value = "";
    return;
  }
  const translation = translations.value.find(
    (item) => String(item.id) === String(id),
  );
  if (!translation || String(translation.id) === String(selectedTranslation.value?.id ?? ""))
    return;
  await selectTranslation(translation);
};

const onPlayerSelectStream = (id: string) => {
  const stream = ownPlayerStreams.value.find((item) => item.id === id);
  if (!stream || id === selectedOwnStreamId.value) return;
  selectedOwnStreamId.value = id;
  ownPlayerError.value = "";
  const groups = id === "primary" ? episodeGroups.value : stream.episodeGroups;
  const requestedEpisode = id === "primary"
    ? currentEpisode.value
    : (stream.resolvedEpisode ?? currentEpisode.value);
  const resolved = resolveEpisodeTarget(
    groups,
    currentSeason.value,
    requestedEpisode,
  );
  const seasonChanged = resolved.season !== currentSeason.value;
  const episodeChanged = resolved.episode !== currentEpisode.value;
  if (seasonChanged) currentSeason.value = resolved.season;
  if (episodeChanged) currentEpisode.value = resolved.episode;
  if (seasonChanged || episodeChanged) {
    resetEpisodeRuntime();
    animeTab.value?.setEpisode(resolved.episode);
    syncResumePosition();
    return;
  }
  ownPlayer.value?.prepareTranslationSwitch?.();
  ownPlayerSources.value = stream.sources;
};

const onToolbarTranslationChange = (event: Event) => {
  void onPlayerSelectTranslation((event.target as HTMLSelectElement).value);
};

const onPlayerReady = () => {
  loading.value = false;
  nextTick(() => updatePlayerHeightVar());
};

const onVideoStarted = () => {};
const onPlay = () => {
  isPlaying.value = true;
  analyticsEvent("playback_started", { source: "watch" });
  animeTab.value?.setPlayerActive(true, currentEpisode.value);
};

const onPause = () => {
  isPlaying.value = false;
  animeTab.value?.setPlayerActive(false, currentEpisode.value);
};

const triggerLibraryAdd = () => {
  if (addedToLibrary.value || isInLibrary.value) return;
  addedToLibrary.value = true;
  addToLibraryAutomatically();
};

const markEpisodeWatched = async () => {
  if (episodeMarkedWatched.value) return;
  episodeMarkedWatched.value = true;
  watchProgress.value[currentEpisode.value] = 100;
  saveWatchProgress();
  if (isInLibrary.value && libraryItemId.value) {
    await updateLibraryProgress();
  } else {
    await addToLibraryAutomatically();
  }
};

const onTimeUpdate = (time: number) => {
  currentTime.value = time;
  if (duration.value <= 0) return;

  const pct = (time / duration.value) * 100;
  watchProgress.value[currentEpisode.value] = Math.min(pct, 100);

  if (
    !addedToLibrary.value &&
    !isInLibrary.value &&
    (openingStartTime.value !== null || time >= 30)
  ) {
    triggerLibraryAdd();
  }

  if (
    endingStartTime.value !== null &&
    !episodeMarkedWatched.value &&
    time >= endingStartTime.value
  ) {
    markEpisodeWatched();
    epProgress
      ?.autoMarkWatched(currentSeason.value, currentEpisode.value)
      .then(syncEpRefs);
  }

  if (!episodeMarkedWatched.value && pct >= 85) {
    markEpisodeWatched();
    epProgress
      ?.autoMarkWatched(currentSeason.value, currentEpisode.value)
      .then(syncEpRefs);
  }

  if (Math.floor(time) % 10 === 0) {
    saveWatchProgress();
    if (isInLibrary.value && libraryItemId.value) updateLibraryProgress();
    epProgress?.updatePosition(
      currentSeason.value,
      currentEpisode.value,
      Math.floor(time),
      duration.value || undefined,
    );

    const now = Date.now();
    const stored = anime.value
      ? progressStore.getProgress(anime.value.id)
      : null;
    if (
      anime.value?.id &&
      now - lastStoreUpdateTime.value > 30_000 &&
      epProgress &&
      (currentSeason.value > (stored?.current_season || 0) ||
        (currentSeason.value === (stored?.current_season || 0) &&
          currentEpisode.value > (stored?.current_episode || 0)))
    ) {
      progressStore.setProgress(anime.value.id, {
        current_season: currentSeason.value,
        current_episode: currentEpisode.value,
        episodes_watched: epProgress.watchedCount.value,
        progress_percentage: epProgress.progressPercent.value,
        total_episodes: epProgress.totalEpisodes.value,
      });
      lastStoreUpdateTime.value = now;
    }
  }
};

const onDurationUpdate = (dur: number) => {
  duration.value = dur;
};

const onKodikTranslationChanged = (data: { id: number; title: string }) => {
  const match = translations.value.find(
    (t) => Number(t.id) === Number(data.id),
  );

  if (match) {
    selectedTranslation.value = match;
  } else {
    selectedTranslation.value = {
      id: data.id,
      name: data.title || `#${data.id}`,
      type: "voice",
      is_custom: false,
      kodik_link: kodikLink.value,
    };
  }
};

const onCurrentEpisode = (data: { episode?: number | null; season?: number | null }) => {
  const episodeChanged =
    data.episode !== null &&
    data.episode !== undefined &&
    data.episode !== currentEpisode.value;
  const seasonChanged =
    data.season !== null &&
    data.season !== undefined &&
    data.season !== currentSeason.value;

  if (episodeChanged) currentEpisode.value = data.episode as number;
  if (seasonChanged) {
    switchTranslationForSeason(data.season as number);
    currentSeason.value = data.season as number;
    epProgress?.setEpisodeGroups(episodeGroups.value);
  }
  if (episodeChanged || seasonChanged) {
    resetEpisodeRuntime();
    animeTab.value?.setEpisode(currentEpisode.value);
  }
};

const onVideoEnded = () => {
  isPlaying.value = false;
  markEpisodeWatched();
  epProgress
    ?.autoMarkWatched(currentSeason.value, currentEpisode.value)
    .then(syncEpRefs);
  const nextEpisode = nextEpisodeInGroups(
    episodeGroups.value,
    currentSeason.value,
    currentEpisode.value,
  );
  if (nextEpisode) {
    onPlayerSelectEpisode(nextEpisode);
    autoplay.value = true;
    return;
  }
  const next = playlistItems.value[currentPlaylistIndex.value + 1];
  if (next) openPlaylistItem(next);
};

const onSkipButton = (data: { title: string }) => {
  const title = data?.title?.toLowerCase() || "";
  const isOpening =
    title.includes("опенинг") ||
    title.includes("opening") ||
    title.includes("intro");
  const isEnding =
    title.includes("эндинг") ||
    title.includes("ending") ||
    title.includes("outro") ||
    title.includes("титры");

  if (isOpening && openingStartTime.value === null) {
    openingStartTime.value = currentTime.value;
    triggerLibraryAdd();
  }
  if (isEnding && endingStartTime.value === null && currentTime.value > 0) {
    endingStartTime.value = currentTime.value;
    markEpisodeWatched();
    epProgress
      ?.autoMarkWatched(currentSeason.value, currentEpisode.value)
      .then(syncEpRefs);
  }
};

const onPlayerError = (err: string) => {
  error.value = err;
};

const isPlayerActive = (mode: "own" | "kodik") =>
  !useCustomPlayer.value && playerMode.value === mode;

const onOwnReady = () => {
  if (isPlayerActive("own")) onPlayerReady();
};
const onOwnPlay = () => {
  if (isPlayerActive("own")) onPlay();
};
const onOwnPause = () => {
  if (isPlayerActive("own")) onPause();
};
const onOwnTimeUpdate = (time: number) => {
  if (isPlayerActive("own")) onTimeUpdate(time);
};
const onOwnDurationUpdate = (dur: number) => {
  if (isPlayerActive("own")) onDurationUpdate(dur);
};
const onOwnVideoEnded = () => {
  if (isPlayerActive("own")) onVideoEnded();
};
const onOwnEnterPip = () => {
  if (isPlayerActive("own")) systemPip.entered();
};
const onOwnExitPip = () => {
  if (isPlayerActive("own")) systemPip.exited();
};
const onOwnError = (err: string) => {
  if (isPlayerActive("own")) onPlayerError(err);
};

const onKodikReady = () => {
  if (isPlayerActive("kodik")) onPlayerReady();
};
const onKodikPlay = () => {
  if (isPlayerActive("kodik")) onPlay();
};
const onKodikPause = () => {
  if (isPlayerActive("kodik")) onPause();
};
const onKodikTimeUpdate = (time: number) => {
  if (isPlayerActive("kodik")) onTimeUpdate(time);
};
const onKodikDurationUpdate = (dur: number) => {
  if (!isPlayerActive("kodik")) return;
  onDurationUpdate(dur);
  excerptCapture.value?.observeDuration(dur);
};
const onKodikPreciseTime = (time: number) => {
  if (isPlayerActive("kodik")) excerptCapture.value?.captureTime(time);
};
const onKodikCurrentEpisode = (data: {
  episode: number | null;
  season: number | null;
  translation: { id: number; title: string };
}) => {
  if (!isPlayerActive("kodik")) return;
  onCurrentEpisode(data);
  excerptCapture.value?.observeEpisode(data);
};
const onKodikVideoStarted = () => {
  if (isPlayerActive("kodik")) onVideoStarted();
};
const onKodikVideoEnded = () => {
  if (isPlayerActive("kodik")) onVideoEnded();
};
const onKodikEnterPip = () => {
  if (isPlayerActive("kodik")) systemPip.entered();
};
const onKodikExitPip = () => {
  if (isPlayerActive("kodik")) systemPip.exited();
};
const onKodikSkipButton = (data: { title: string }) => {
  if (isPlayerActive("kodik")) onSkipButton(data);
};
const onKodikTranslationMessage = (data: { id: number; title: string }) => {
  if (isPlayerActive("kodik")) onKodikTranslationChanged(data);
};
const onKodikError = (err: string) => {
  if (isPlayerActive("kodik")) onPlayerError(err);
};

const loadWatchProgress = () => {
  const animeId = anime.value?.id;
  if (!animeId) return;
  const entry = progressStore.getProgress(animeId);
  if (entry) {
    watchProgress.value = {
      [entry.current_episode]: 100,
    };
    return;
  }
  const saved = localStorage.getItem(`anime_progress_${authStore.user?.id ?? "guest"}_${animeId}`);
  if (saved) {
    try {
      watchProgress.value = JSON.parse(saved);
    } catch {
      /* ignore */
    }
  }
};

const saveWatchProgress = async () => {
  const animeId = anime.value?.id;
  if (!animeId) return;
  localStorage.setItem(
    `anime_progress_${authStore.user?.id ?? "guest"}_${animeId}`,
    JSON.stringify(watchProgress.value),
  );
  if (!authStore.isAuthenticated) return;
  try {
    if (isInLibrary.value && libraryItemId.value) await updateLibraryProgress();
  } catch {
    /* silent */
  }
};

const handleSyncApply = async (payload: {
  mode: string;
  seasons?: { season: number; watchedUpTo: number }[];
  watchedUpTo?: number;
  season?: number;
}) => {
  if (!epProgress) return;
  if (payload.mode === "new" || payload.mode === "restart") {
    await epProgress.resetProgress();
  } else if (payload.mode === "completed") {
    const seasons = episodeGroups.value.map((group) => ({
      season: group.season,
      watchedUpTo: group.episodes.at(-1) ?? 0,
    }));
    await epProgress.bulkSyncSeasons(seasons);
  } else if (payload.seasons?.length) {
    await epProgress.bulkSyncSeasons(payload.seasons);
  } else if (payload.mode === "continue" && payload.watchedUpTo) {
    await epProgress.bulkSyncUpTo(
      payload.watchedUpTo,
      payload.season ?? currentSeason.value,
    );
  }
  syncEpRefs();
  if (payload.mode === "continue") {
    const next = epProgress.nextEpisodeToWatch.value;
    if (next) selectEpisodeTarget(next);
  }
};

const onMarkWatched = async (target: EpisodeTarget) => {
  if (!epProgress) return;
  await epProgress.markWatched(target.season, target.episode);
  syncEpRefs();
};

const onUndoMark = async (target: EpisodeTarget) => {
  if (!epProgress) return;
  await epProgress.undoMark(target.season, target.episode);
  syncEpRefs();
};

const onSkipEpisode = async (target: EpisodeTarget) => {
  if (!epProgress) return;
  await epProgress.skipEpisode(target.season, target.episode);
  syncEpRefs();
};

const retryLoad = () => playerMode.value === "own" && !useCustomPlayer.value
  ? loadOwnPlayer()
  : loadKodikPlayer();

const shareAnime = () => {
  if (navigator.share) {
    navigator.share({
      title: anime.value?.title_ru,
      url: window.location.href,
    });
  } else {
    navigator.clipboard.writeText(window.location.href);
    toast.success("Ссылка скопирована!");
  }
};

const onDubAdded = () => {
  loadTranslations();
  showAddDubModal.value = false;
};

onMounted(() => {
  document.addEventListener("fullscreenchange", syncMainFullscreen);
  loadAnime();
  void loadPlaylistContext();
  window.addEventListener("scroll", checkScrollPosition);

  setTimeout(checkScrollPosition, 500);
});

onUnmounted(() => {
  watchDisposed = true; loadGeneration++; ownLoadVersion++; loadController?.abort(); clearTimeout(firstVisitTimer);
  systemPip.dispose();
  epProgress?.dispose();
  document.removeEventListener("fullscreenchange", syncMainFullscreen);
  animeTab.value?.stop();
  window.removeEventListener("scroll", checkScrollPosition);
  saveWatchProgress();
  teardownPlayerHeightSync();
  const w = window as unknown as { _playerRO?: { disconnect: () => void } };
  const ro = w._playerRO;
  if (ro) {
    ro.disconnect();
    delete w._playerRO;
  }
});

watch(
  () => props.slug,
  () => {
    loadAnime();
  },
);
watch(playlistId, () => { void loadPlaylistContext(); });
watch(currentEpisode, syncResumePosition);
watch(
  () => [currentEpisode.value, posterSrc.value, anime.value?.title_ru, anime.value?.title_en],
  () => {
  },
);
watch(selectedTranslation, (v) => {
  if (v && !v.is_custom && v.kodik_link)
    kodikLink.value = normalizeKodikPlayerLink(v.kodik_link);
});
watch(
  () => [currentEpisode.value, currentSeason.value],
  ([episode, season], [previousEpisode, previousSeason]) => {
    if (suppressSelectionReload) return;
    if (
      playerMode.value === "own" &&
      !useCustomPlayer.value &&
      (episode !== previousEpisode || season !== previousSeason)
    ) void loadOwnPlayer();
  },
);
watchProgressSyncVersion(async () => {
  if (epProgress) {
    await epProgress.loadProgress();
    syncEpRefs();
  }
});
</script>

<style scoped>
/* ════════════════════════════════════════════════════════
   LAYOUT
════════════════════════════════════════════════════════ */
.anime-watch-page {
  min-height: 100vh;
  background: var(--surface-1);
  color: var(--text-primary);
  padding: var(--space-6);
}

.watch-container {
  max-width: 1600px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: var(--space-8);
  /* Выравнивание по верху -важно, чтобы правая колонка не растягивалась
     по высоте левой, а собственный блок постера мог принять нужную высоту */
  align-items: start;
  margin-bottom: 20px;
}

.left-column {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  min-width: 0;
}

.right-column {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  min-width: 0;
}

.watch-playlist {
  display: flex;
  max-height: min(72vh, var(--player-height, 720px));
  min-height: 320px;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-2);
  box-shadow: var(--shadow-md);
}

.watch-playlist__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 14px;
  border-bottom: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--surface-3) 82%, transparent);
}

.watch-playlist__heading { display: flex; min-width: 0; flex-direction: column; gap: 2px; }
.watch-playlist__eyebrow { color: var(--text-tertiary); font-size: .65rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.watch-playlist__title { overflow: hidden; color: var(--text-primary); font-size: .9rem; font-weight: 750; text-decoration: none; text-overflow: ellipsis; white-space: nowrap; }
.watch-playlist__title:hover { color: var(--accent); }
.watch-playlist__counter { flex: none; color: var(--text-tertiary); font-size: .72rem; font-variant-numeric: tabular-nums; }
.watch-playlist__items { flex: 1; min-height: 0; overflow-y: auto; padding: 6px; scrollbar-width: thin; }
.watch-playlist__state { display: grid; min-height: 180px; place-items: center; padding: 20px; color: var(--text-tertiary); font-size: .82rem; text-align: center; }
.watch-playlist__state.is-error { color: var(--danger); }
.watch-playlist__item { display: grid; width: 100%; grid-template-columns: 24px 54px minmax(0, 1fr); align-items: center; gap: 9px; padding: 6px; border: 0; border-radius: 9px; background: transparent; color: inherit; cursor: pointer; font: inherit; text-align: left; }
.watch-playlist__item:hover { background: var(--surface-3); }
.watch-playlist__item.active { background: color-mix(in srgb, var(--accent) 13%, var(--surface-3)); }
.watch-playlist__index { display: grid; place-items: center; color: var(--text-tertiary); font-size: .72rem; font-variant-numeric: tabular-nums; }
.watch-playlist__item.active .watch-playlist__index { color: var(--accent); }
.watch-playlist__poster { display: grid; width: 54px; aspect-ratio: 16 / 10; place-items: center; overflow: hidden; border-radius: 6px; background: var(--surface-4); color: var(--text-tertiary); }
.watch-playlist__poster img { width: 100%; height: 100%; object-fit: cover; }
.watch-playlist__copy { display: flex; min-width: 0; flex-direction: column; gap: 3px; }
.watch-playlist__copy strong { display: -webkit-box; overflow: hidden; color: var(--text-primary); font-size: .78rem; font-weight: 650; line-height: 1.25; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.watch-playlist__copy small { overflow: hidden; color: var(--text-tertiary); font-size: .68rem; text-overflow: ellipsis; white-space: nowrap; }

/* ════════════════════════════════════════════════════════
   ПЛЕЕР
════════════════════════════════════════════════════════ */
.player-wrapper {
  background: var(--surface-2);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  position: relative;
}

.player-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
}

.anime-badges { min-height: 20px; }

.watch-player-toolbar { display: flex; align-items: center; justify-content: flex-end; flex-wrap: wrap; gap: 8px; padding: 8px 12px; }
.player-mode-switch { display: inline-flex; margin-right: auto; padding: 3px; border: 1px solid var(--border-subtle); border-radius: 10px; background: var(--surface-2); }
.player-mode-switch button { min-height: 34px; padding: 6px 13px; border: 0; border-radius: 7px; background: transparent; color: var(--text-secondary); font: inherit; font-size: var(--text-sm); font-weight: 650; cursor: pointer; }
.player-mode-switch button.active { background: color-mix(in srgb, var(--accent) 18%, var(--surface-4)); color: var(--accent-bright); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 35%, transparent); }
.direct-delivery-note { display: inline-flex; align-items: center; gap: 5px; color: var(--text-tertiary); font-size: .72rem; white-space: nowrap; }
.direct-delivery-note::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--success, #43b581); box-shadow: 0 0 8px color-mix(in srgb, var(--success, #43b581) 60%, transparent); }
.video-screenshot-btn, .system-pip-btn, .watch-fullscreen-btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 8px 12px; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); background: var(--surface-3); color: var(--text-primary); cursor: pointer; }
.system-pip-btn.active { color: var(--accent); border-color: var(--accent); }
.video-screenshot-btn:disabled, .system-pip-btn:disabled, .watch-fullscreen-btn:disabled { opacity: .5; cursor: default; }
.watch-fullscreen-btn { width: 44px; padding: 0; }
.video-screenshot-status { color: var(--success, #43b581); font-size: var(--text-sm); }
.video-screenshot-status.error { color: var(--error, #e85b70); }
.video-screenshot-install { color: var(--accent); font-size: var(--text-sm); text-decoration: underline; text-underline-offset: 3px; }
.player-window-error { padding: 0 12px 12px; color: var(--error, #e85b70); font-size: var(--text-sm); overflow-wrap: anywhere; }
.btn-retry--secondary { margin-left: 8px; background: transparent; color: var(--text-primary); }
.player-wrapper:fullscreen { width: 100%; height: 100%; display: flex; flex-direction: column; border-radius: 0; }
.player-wrapper:fullscreen .player-container { flex: 1; min-height: 0; aspect-ratio: auto; }
.player-wrapper:fullscreen .watch-player-toolbar { flex: none; }

.player-blank {
  width: 100%;
  height: 100%;
  background: #000;
}

.player-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
}

.player-placeholder .spinner {
  width: 44px;
  height: 44px;
  border: 3px solid var(--surface-5);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-4);
}

.error-icon,
.no-video-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.btn-retry {
  margin-top: 0.75rem;
  padding: 0.6rem 1.25rem;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}
.btn-retry:hover {
  background: var(--accent-hover);
}

/* ════════════════════════════════════════════════════════
   БЛОК ПОСТЕРА + КНОПКИ -ВЫСОТА РАВНА ПЛЕЕРУ
════════════════════════════════════════════════════════ */
.poster-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  height: var(--player-height, auto);
  flex-shrink: 0;
  min-height: 0;
}

.poster-card {
  background: var(--surface-3);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-sm);
  width: 100%;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.poster-image-wrapper {
  position: relative;
  width: 100%;
  flex: 1 1 auto;
  min-height: 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface-4);
}

.anime-poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border-radius: var(--radius-md);
  transition: transform 0.1s ease;
}

.anime-poster-img:hover {
  transform: scale(1.03);
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  color: var(--text-disabled);
  font-size: 3rem;
}

.poster-image-wrapper {
  position: relative;
}

.more-info-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 50%;
  text-decoration: none;
  cursor: pointer;
  box-shadow: 0 3px 10px color-mix(in srgb, var(--accent) 35%, transparent);
  z-index: 2;
  color: var(--accent-bright, #ff7eb3);
  background: color-mix(in srgb, var(--surface-4) 80%, transparent);
  backdrop-filter: blur(4px);
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
}
.more-info-btn:hover {
  color: #fff;
  background: var(--accent);
  transform: scale(1.05);
}

.more-info-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.more-info-btn span {
  display: block;
  font-family: Georgia, serif;
  font-size: 19px;
  font-weight: 700;
  line-height: 1;
  transform: translateY(-1px);
}

/* ════════════════════════════════════════════════════════
   ИНФО ПОД ПЛЕЕРОМ
════════════════════════════════════════════════════════ */
.anime-info-under {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.anime-header {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.anime-title {
  font-size: var(--text-4xl);
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
  color: #fff;
}

.anime-badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 700;
  line-height: 1.4;
}

.year-badge {
  background: var(--info-subtle);
  color: var(--info);
}
.kind-badge {
  background: var(--accent-2-subtle);
  color: var(--accent-2);
}
.episodes-badge {
  background: var(--success-subtle);
  color: var(--success);
}
.status-badge {
  background: var(--warning-subtle);
  color: var(--warning);
}
.status-badge.ongoing {
  background: var(--success-subtle);
  color: var(--success);
}
.status-badge.finished {
  background: var(--surface-5);
  color: var(--text-tertiary);
}

.anime-rating {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.rating-stars {
  display: flex;
  gap: 0.2rem;
  color: var(--warning);
}
.rating-value {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--warning);
}

.anime-description {
  color: var(--text-secondary);
  line-height: 1.68;
  font-size: var(--text-lg);
}

/* ════════════════════════════════════════════════════════
   Серии
════════════════════════════════════════════════════════ */
.episodes-card {
  background: var(--surface-3);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-sm);
  width: 100%;
  margin-bottom: 20px;
}

.ec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
  gap: var(--space-3);
}

.ec-header h3 {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  flex-shrink: 0;
}

.ec-header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  justify-content: flex-end;
}

.ep-search-wrap {
  position: relative;
  flex: 1;
}

.ep-search-icon {
  position: absolute;
  left: var(--space-2);
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  pointer-events: none;
}

.ep-search-input {
  width: 100%;
  height: 32px;
  padding: 0 var(--space-2) 0 32px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 0.15s ease;
  box-sizing: border-box;
}
.ep-search-input:focus {
  border-color: var(--accent);
}
.ep-search-input::placeholder {
  color: var(--text-tertiary);
}

.btn-sync-sm {
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--surface-4);
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);
  flex-shrink: 0;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.btn-sync-sm:hover {
  background: var(--surface-5);
  color: var(--text-primary);
  border-color: var(--border-default);
}
.btn-sync-sm:active {
  transform: scale(0.96);
}
.btn-sync-sm:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* ════════════════════════════════════════════════════════
   Жанры
════════════════════════════════════════════════════════ */
.genres-card {
  background: var(--surface-3);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-sm);
  width: 100%;
}

.genres-card h3 {
  margin: 0 0 var(--space-3);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.genres-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.genre-tag {
  padding: 0.3rem 0.7rem;
  background: var(--accent-2-subtle);
  color: var(--accent-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 500;
  border: 1px solid var(--accent-2-subtle);
  cursor: pointer;
  transition: all 0.15s ease;
  text-decoration: none;
  display: inline-block;
}
.genre-tag:hover {
  background: var(--accent-2-subtle);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--accent-2-glow);
}

/* ════════════════════════════════════════════════════════
   Действия
════════════════════════════════════════════════════════ */
.actions-card {
  background: var(--surface-3);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: row;
  gap: var(--space-4);
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex: 1;
}
.action-btn.is-favorite {
  background: rgba(251, 191, 36, 0.12);
  border-color: rgba(251, 191, 36, 0.35);
  color: var(--warning);
}
.action-btn.is-favorite:hover {
  background: rgba(251, 191, 36, 0.2);
  border-color: rgba(251, 191, 36, 0.5);
}

.action-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--surface-5);
  border-top-color: var(--text-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.action-icon-filled {
  font-size: 1.2rem;
  color: var(--warning);
}

.action-icon {
  font-size: 1.2rem;
}

.action-label {
  font-size: var(--text-base);
}

/* ════════════════════════════════════════════════════════
   Скачать тему
════════════════════════════════════════════════════════ */
.qdl-err-text {
  width: 100%;
  margin: 0;
  font-size: var(--text-xs);
  color: var(--danger);
}

.clip-form-inline {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-top: none;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  margin-top: -2px;
}

.tdc-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 1rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
  text-align: left;
}
.tdc-btn:hover:not(:disabled) {
  background: var(--surface-5);
  color: var(--text-primary);
  transform: translateY(-1px);
}
.tdc-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tdc-btn.tdc-loading {
  border-color: rgba(255, 126, 179, 0.4);
  background: rgba(255, 126, 179, 0.06);
  color: var(--accent-bright);
}
.tdc-btn.tdc-done {
  border-color: rgba(60, 255, 131, 0.4);
  background: rgba(60, 255, 131, 0.06);
  color: var(--success);
}

.tdc-label {
  flex: 1;
}

.tdc-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--surface-5);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.tdc-progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(255, 126, 179, 0.15);
}
.tdc-progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
  transition: width 0.4s ease;
}

.tdc-error-text {
  font-size: var(--text-xs);
  color: var(--danger);
  margin: 0;
  padding: var(--space-1) var(--space-2);
  background: rgba(255, 62, 62, 0.06);
  border-radius: var(--radius-sm);
  word-break: break-word;
}

.clip-times {
  display: flex;
  align-items: flex-end;
  gap: var(--space-2);
}

.clip-time-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.clip-time-field label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.clip-time-input {
  width: 100%;
  padding: 0.5rem 0.625rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-base);
  font-weight: 600;
  font-family: "Courier New", monospace;
  outline: none;
  text-align: center;
  transition: border-color 0.15s ease;
}
.clip-time-input:focus {
  border-color: var(--accent);
}
.clip-time-input:disabled {
  opacity: 0.5;
}

.clip-time-arrow {
  color: var(--text-tertiary);
  font-size: 1rem;
  padding-bottom: 0.4rem;
  flex-shrink: 0;
}

.clip-label-row {
  width: 100%;
}

.clip-label-input {
  width: 100%;
  padding: 0.4rem 0.625rem;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 0.15s ease;
  box-sizing: border-box;
}
.clip-label-input:focus {
  border-color: var(--border-default);
  color: var(--text-primary);
}
.clip-label-input:disabled {
  opacity: 0.5;
}

.clip-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.clip-hint b {
  color: var(--accent-bright);
}

.clip-hint-btn {
  padding: 0.2rem 0.5rem;
  font-size: var(--text-xs);
  background: rgba(255, 126, 179, 0.1);
  border: 1px solid rgba(255, 126, 179, 0.2);
  border-radius: var(--radius-xs);
  color: var(--accent-bright);
  cursor: pointer;
  transition: all 0.15s ease;
}
.clip-hint-btn:hover:not(:disabled) {
  background: rgba(255, 126, 179, 0.2);
}
.clip-hint-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.clip-actions {
  display: flex;
  gap: var(--space-2);
  align-items: stretch;
}

.clip-download-btn {
  flex: 1;
  justify-content: center;
  padding: 0.65rem 0.875rem;
}

.clip-cancel-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--surface-4);
  color: var(--text-tertiary);
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s ease;
  align-self: center;
}
.clip-cancel-btn:hover:not(:disabled) {
  background: rgba(255, 62, 62, 0.1);
  color: var(--danger);
  border-color: rgba(255, 62, 62, 0.2);
}
.clip-cancel-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ════════════════════════════════════════════════════════
   ФРАНШИЗА -используем AnimeCard как в AnimeDetailView
════════════════════════════════════════════════════════ */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.scroll-to-franchise-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 126, 180, 0.278);
  border: 1px solid rgba(255, 126, 180, 0.293);
  color: var(--text-on-accent);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  transition:
    background-color var(--duration-base) var(--ease-out),
    transform var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.scroll-to-franchise-btn:hover {
  background: rgba(255, 126, 179, 1);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(255, 126, 179, 0.5);
}
.scroll-to-franchise-btn:active {
  transform: scale(0.96);
}

@media (max-width: 767px) {
  .scroll-to-franchise-btn {
    bottom: 16px;
    right: 16px;
    width: 44px;
    height: 44px;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ════════════════════════════════════════════════════════
   АДАПТИВНОСТЬ
════════════════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .watch-container {
    grid-template-columns: 1fr 300px;
  }
}

@media (max-width: 1024px) {
  .watch-container {
    grid-template-columns: 1fr;
  }

  .right-column {
    flex-direction: column;
    gap: var(--space-4);
  }

  .watch-playlist { max-height: 440px; min-height: 260px; }

  .episodes-card {
    flex: 1;
  }
  .genres-card,
  .actions-card {
    flex: 1;
  }

  /* На мобильных высота плеера не должна ограничивать постер */
  .poster-block {
    height: auto;
  }

  .poster-card {
    flex: 0 0 auto;
  }

  .poster-image-wrapper {
    aspect-ratio: 3 / 4;
    flex: 0 0 auto;
  }
}

@media (max-width: 768px) {
  .watch-player-toolbar { padding-inline: 8px; }
  .player-mode-switch { width: 100%; order: -2; }
  .player-mode-switch button { flex: 1; }
  .direct-delivery-note { margin-right: auto; }
  .anime-watch-page {
    padding: var(--space-3);
  }
  .anime-title {
    font-size: var(--text-3xl);
  }
  .watch-container {
    gap: var(--space-5);
  }
  .episodes-card {
    padding: var(--space-3);
  }
  .ec-header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .ep-search-wrap {
    max-width: none;
  }
}

@media (max-width: 480px) {
  .anime-title {
    font-size: var(--text-2xl);
  }
}
</style>
