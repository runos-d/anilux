<template>
  <div class="episode-list">
    <div class="anime-progress-bar" v-if="totalEpisodes > 1">
      <div class="apb-header">
        <span class="apb-label">Прогресс</span>
        <span class="apb-stats">
          {{ watchedCount }}/{{ totalEpisodes }}
          <span class="apb-pct">{{ progressPercent }}%</span>
        </span>
      </div>
      <div class="apb-track">
        <div class="apb-fill" :style="{ width: progressPercent + '%' }" />
      </div>
      <div class="apb-actions" v-if="progressPercent < 100">
        <button
          class="apb-btn continue-btn"
          v-if="nextEpisode"
          @click="$emit('select-episode', nextEpisode)"
        >
        Продолжить с {{ episodeLabel(nextEpisode) }}
        </button>
      </div>
      <div class="apb-completed" v-else>
        <span class="completed-badge"
          ><SakuraIcon name="check" /> Просмотрено</span
        >
        <button class="apb-btn sync-btn" @click="$emit('open-sync')">
          Пересмотреть
        </button>
      </div>
    </div>

    <div v-if="episodeGroups.length > 1" class="season-tabs">
      <button
        v-for="group in episodeGroups"
        :key="group.season"
        class="season-tab"
        :class="{ active: group.season === currentSeason }"
        @click="$emit('select-season', group.season)"
      >
        {{ group.label }}
      </button>
    </div>

    <div class="episodes-scroll">
      <div
        v-for="num in episodeNumbers"
        :key="num"
        class="ep-row"
        :class="[getEp(num).status, { 'is-current': num === currentEpisode }]"
      >
        <div class="ep-left">
          <div class="ep-status-wrap">
            <span
              v-if="getEp(num).status === 'watched'"
              class="ep-status-icon watched"
            >
              <SakuraIcon name="heavy-check" />
            </span>
            <span
              v-else-if="getEp(num).status === 'skipped'"
              class="ep-status-icon skipped"
              ><SakuraIcon name="next-track"/></span
            >
            <span
              v-else-if="getEp(num).status === 'in_progress'"
              class="ep-status-icon in-progress"
            >
              <SakuraIcon name="play" />
            </span>
            <span v-else class="ep-num-plain">{{ num }}</span>
          </div>
        </div>

        <div
          class="ep-center"
          @click="$emit('select-episode', target(num))"
          style="cursor: pointer"
        >
          <div class="ep-title-row">
            <span
              class="ep-num-label"
              v-if="getEp(num).status !== 'not_started'"
              >{{ num }}</span
            >
            <span class="ep-title">{{
              (episodeTitles && episodeTitles[num]) || `Серия ${num}`
            }}</span>
          </div>

          <div
            v-if="
              getEp(num).status === 'in_progress' &&
              getEp(num).progress_percent > 0
            "
            class="ep-bar-wrap"
          >
            <div class="ep-bar-track">
              <div
                class="ep-bar-fill"
                :style="{ width: getEp(num).progress_percent + '%' }"
              />
            </div>
            <span class="ep-bar-pct">{{ getEp(num).progress_percent }}%</span>
          </div>

          <span
            v-if="getEp(num).status === 'skipped'"
            class="ep-tag skipped-tag"
            >Пропущено</span
          >
        </div>

        <div class="ep-actions">
          <button
            v-if="getEp(num).status === 'watched'"
            class="ep-btn unmark"
            @click.stop="$emit('undo-mark', target(num))"
            title="Снять отметку"
          >
            <SakuraIcon name="reply"/>
          </button>
          <button
            v-else
            class="ep-btn mark"
            @click.stop="$emit('mark-watched', target(num))"
            title="Отметить просмотренной"
          >
            <SakuraIcon name="check" :size="16" />
          </button>
          <button
            v-if="
              getEp(num).status !== 'watched' && getEp(num).status !== 'skipped'
            "
            class="ep-btn skip"
            @click.stop="$emit('skip-episode', target(num))"
            title="Пропустить"
          >
            <SakuraIcon name="next-track"/>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { computed } from "vue";
import type {
  EpisodeProgressItem,
  EpisodeTarget,
} from "@/composables/useEpisodeProgress";
import type { PlayerEpisodeGroup } from "@/lib/playerSeasons";

const props = defineProps<{
  totalEpisodes: number;
  currentSeason: number;
  currentEpisode: number;
  episodes: Map<string, EpisodeProgressItem>;
  watchedCount: number;
  progressPercent: number;
  nextEpisode: EpisodeTarget | null;
  episodeGroups?: PlayerEpisodeGroup[];
  episodeTitles?: Record<number, string>;
  searchQuery?: string;
}>();

defineEmits<{
  (e: "select-episode", target: EpisodeTarget): void;
  (e: "select-season", season: number): void;
  (e: "mark-watched", target: EpisodeTarget): void;
  (e: "undo-mark", target: EpisodeTarget): void;
  (e: "skip-episode", target: EpisodeTarget): void;
  (e: "open-sync"): void;
}>();

const episodeGroups = computed(() => props.episodeGroups ?? []);

const episodeNumbers = computed(() => {
  const group = episodeGroups.value.find(
    (item) => item.season === props.currentSeason,
  );
  const numbers = group?.episodes?.length
    ? group.episodes
    : Array.from({ length: props.totalEpisodes }, (_, i) => i + 1);
  const q = (props.searchQuery || "").trim().toLowerCase();
  if (!q) return numbers;
  return numbers.filter((num) => {
    const title = (props.episodeTitles && props.episodeTitles[num]) || `Серия ${num}`;
    return (
      String(num).includes(q) ||
      title.toLowerCase().includes(q)
    );
  });
});

const target = (episode: number): EpisodeTarget => ({
  season: props.currentSeason,
  episode,
});

const episodeLabel = (target: EpisodeTarget) =>
  episodeGroups.value.length > 1
    ? `S${target.season}E${target.episode}`
    : `серии ${target.episode}`;

const getEp = (num: number): EpisodeProgressItem =>
  props.episodes.get(`${props.currentSeason}:${num}`) ?? {
    season_number: props.currentSeason,
    episode_number: num,
    status: "not_started",
    last_position: 0,
    duration: null,
    progress_percent: 0,
    is_manually_marked: false,
    watched_at: null,
  };
</script>

<style scoped>
.episode-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  width: 100%;
}

.anime-progress-bar {
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.apb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.apb-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-tertiary);
  font-weight: 700;
}

.apb-stats {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.apb-pct {
  margin-left: 0.35rem;
  font-weight: 700;
  color: var(--accent);
}

.apb-track {
  height: 6px;
  background: var(--surface-5);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.apb-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-hover));
  border-radius: var(--radius-full);
  transition: width 0.4s ease;
}

.apb-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.apb-completed {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.completed-badge {
  font-size: var(--text-sm);
  color: var(--success);
  font-weight: 600;
}

.apb-btn {
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  white-space: nowrap;
}

.continue-btn {
  background: linear-gradient(135deg, var(--accent), var(--accent-hover));
  color: var(--text-on-accent);
  flex: 1;
}
.continue-btn:hover {
  opacity: 0.9;
}

.sync-btn {
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
}
.sync-btn:hover {
  background: var(--surface-5);
  color: var(--text-primary);
}

.season-tabs {
  display: flex;
  gap: 0.35rem;
  overflow-x: auto;
  padding-bottom: 0.15rem;
  scrollbar-width: none;
}

.season-tabs::-webkit-scrollbar {
  display: none;
}

.season-tab {
  border: 1px solid var(--border-subtle);
  background: var(--surface-4);
  color: var(--text-secondary);
  border-radius: var(--radius-full);
  padding: 0.3rem 0.75rem;
  font-size: var(--text-xs);
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.15s ease;
}

.season-tab:hover {
  color: var(--text-primary);
  border-color: var(--border-default);
}

.season-tab.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent-bright);
}

.episodes-scroll {
  display: flex;
  flex-direction: column;
  gap: 0.2px;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 2px;
}

.episodes-scroll::-webkit-scrollbar {
  width: 3px;
}
.episodes-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.episodes-scroll::-webkit-scrollbar-thumb {
  background: var(--surface-6);
  border-radius: var(--radius-full);
}

.ep-row {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  gap: 0.5rem;
  align-items: center;
  padding: 0.4rem 0.5rem;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  transition: background 0.12s ease;
}

.ep-row:hover {
  background: var(--surface-4);
}

.ep-row.is-current {
  background: var(--accent-subtle);
  border-color: var(--border-strong);
}

.ep-row.watched {
  opacity: 0.6;
}
.ep-row.skipped {
  opacity: 0.45;
}

.ep-left {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ep-status-wrap {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ep-status-icon {
  font-size: 0.7rem;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.ep-status-icon.watched {
  background: var(--success-subtle);
  color: var(--success);
}

.ep-status-icon.skipped {
  background: var(--warning-subtle);
  color: var(--warning);
}

.ep-status-icon.in-progress {
  background: var(--accent-subtle);
  color: var(--accent-bright);
}

.ep-num-plain {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-tertiary);
  min-width: 20px;
  text-align: center;
}

.ep-center {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.ep-title-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
}

.ep-num-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.ep-title {
  font-size: 0.82rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ep-row.is-current .ep-title {
  color: #fff;
  font-weight: 600;
}

.ep-bar-wrap {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.ep-bar-track {
  flex: 1;
  height: 3px;
  background: var(--surface-5);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.ep-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

.ep-bar-pct {
  font-size: 0.62rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
  min-width: 24px;
  text-align: right;
}

.ep-tag {
  display: inline-block;
  font-size: 0.62rem;
  font-weight: 600;
  padding: 0.05rem 0.35rem;
  border-radius: var(--radius-xs);
  line-height: 1.4;
}

.skipped-tag {
  background: var(--warning-subtle);
  color: var(--warning);
}

.current-tag {
  background: var(--accent-subtle);
  color: var(--accent-bright);
}

.ep-actions {
  display: flex;
  gap: 0.2rem;
  align-items: center;
  flex-shrink: 0;
}

.ep-btn {
  width: 24px;
  height: 24px;
  min-width: 24px;
  min-height: 24px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--surface-4);
  color: var(--text-tertiary);
  font-size: 0.7rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.12s ease;
  flex-shrink: 0;
}

.ep-btn:hover {
  color: #fff;
  border-color: var(--border-default);
}

.ep-btn.mark:hover {
  background: var(--success-subtle);
  color: var(--success);
  border-color: var(--success);
}
.ep-btn.unmark:hover {
  background: var(--surface-5);
  color: var(--text-primary);
}
.ep-btn.skip:hover {
  background: var(--warning-subtle);
  color: var(--warning);
  border-color: var(--warning);
}
@media (pointer: coarse) {
  .ep-btn { width: 40px; height: 40px; min-width: 40px; min-height: 40px; }
  .ep-actions { gap: 6px; }
}
</style>
