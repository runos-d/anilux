<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
        <div class="modal-box">
          <div class="modal-header">
            <span class="modal-icon"> <SakuraIcon name="settings" /> </span>
            <h2>Настройка прогресса</h2>
            <button class="close-btn" @click="$emit('close')" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button>
          </div>

          <div class="anime-label">
            {{ animeTitle }}
            <span class="ep-count">(всего {{ episodeTotal }} серий)</span>
          </div>

          <div class="options">
            <label class="option" :class="{ active: mode === 'new' }">
              <input type="radio" v-model="mode" value="new" />
              <span>Я новичок (не смотрел)</span>
            </label>

            <label class="option" :class="{ active: mode === 'restart' }">
              <input type="radio" v-model="mode" value="restart" />
              <span>Я смотрел, но хочу начать заново</span>
            </label>

            <label class="option" :class="{ active: mode === 'continue' }">
              <input type="radio" v-model="mode" value="continue" />
              <div class="option-continue" v-if="multiSeason">
                <span>Отметьте просмотренное по сезонам:</span>
                <div class="season-progress-list">
                  <div
                    v-for="group in seasonGroups"
                    :key="group.season"
                    class="season-progress-row"
                  >
                    <span class="season-name">{{ group.label }}</span>
                    <div class="ep-picker">
                      <button
                        class="ep-btn"
                        @click="stepSeason(group.season, -1)"
                        :disabled="seasonCount(group.season) <= 0"
                      >
                        <SakuraIcon name="minus" :size="16" />
                      </button>
                      <input
                        class="ep-num"
                        type="number"
                        inputmode="numeric"
                        :min="0"
                        :max="group.episodes.length"
                        :value="seasonCount(group.season)"
                        :aria-label="`Просмотрено серий: ${group.label}`"
                        @click.stop
                        @input="setSeasonInput(group.season, $event)"
                        @blur="normalizeSeasonInput(group.season, $event)"
                      />
                      <button
                        class="ep-btn"
                        @click="stepSeason(group.season, 1)"
                        :disabled="
                          seasonCount(group.season) >= group.episodes.length
                        "
                      >
                        <SakuraIcon name="plus" :size="16" />
                      </button>
                      <span class="ep-label">из {{ group.episodes.length }}</span>
                    </div>
                  </div>
                </div>
                <span class="already-watched" v-if="continueTotal > 0">
                  (уже просмотрено: {{ continueTotal }}
                  {{ plural(continueTotal) }})
                </span>
              </div>
              <div class="option-continue" v-else-if="totalEpisodes > 1">
                <span>Я продолжаю с:</span>
                <div class="ep-picker">
                  <button
                    class="ep-btn"
                    @click="dec"
                    :disabled="continueFrom <= 1"
                  >
                    <SakuraIcon name="minus" :size="16" />
                  </button>
                  <input
                    class="ep-num"
                    type="number"
                    inputmode="numeric"
                    :min="1"
                    :max="totalEpisodes"
                    :value="continueFrom"
                    aria-label="Серия, с которой продолжить"
                    @click.stop
                    @input="setContinueFromInput"
                    @blur="normalizeContinueFromInput"
                  />
                  <button
                    class="ep-btn"
                    @click="inc"
                    :disabled="continueFrom >= totalEpisodes"
                  >
                    <SakuraIcon name="plus" :size="16" />
                  </button>
                  <span class="ep-label">серии</span>
                </div>
                <span class="already-watched" v-if="continueFrom > 1">
                  (уже просмотрено: {{ continueFrom - 1 }}
                  {{ plural(continueFrom - 1) }})
                </span>
              </div>
              <div class="option-continue" v-else>
                <span>Эта серия уже просмотрена</span>
              </div>
            </label>

            <label class="option" :class="{ active: mode === 'completed' }">
              <input type="radio" v-model="mode" value="completed" />
              <span>Просмотрено (все серии)</span>
            </label>
          </div>

          <div
            v-if="mode === 'continue' && !multiSeason && totalEpisodes > 1"
            class="slider-wrap"
          >
            <UiRangeSlider
              v-model.number="continueFrom"
              :min="1"
              :max="totalEpisodes"
              class="slider"
            />
            <div class="slider-labels">
              <span>1</span>
              <span>{{ totalEpisodes }}</span>
            </div>
          </div>

          <div class="info-row" v-if="mode !== 'new'">
            <span class="info-icon"> <SakuraIcon name="pin" /> </span>
            <span v-if="mode === 'continue'">
              {{ continueSummary }}
            </span>
            <span v-else-if="mode === 'completed'">
              Все {{ episodeTotal }} {{ plural(episodeTotal) }} будут отмечены
              как просмотренные
            </span>
            <span v-else>Весь прогресс будет сброшен</span>
          </div>

          <div class="modal-actions">
            <button class="btn btn-ghost btn-cancel" @click="$emit('close')">Отмена</button>
            <button class="btn btn-primary btn-apply" :disabled="saving" @click="apply">
              <span v-if="saving" class="spinner" />
              {{ saving ? "Сохраняем..." : "Применить" }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import UiRangeSlider from "@/components/common/UiRangeSlider.vue";
import { computed, ref, watch } from "vue";
import { useScrollLock } from "@/composables/useScrollLock";
import type { PlayerEpisodeGroup } from "@/lib/playerSeasons";

const props = defineProps<{
  show: boolean;
  animeTitle: string;
  totalEpisodes: number;
  currentSeason?: number;
  currentEpisode?: number;
  episodeGroups?: PlayerEpisodeGroup[];
}>();

useScrollLock(computed(() => props.show));

const emit = defineEmits<{
  (e: "close"): void;
  (
    e: "apply",
    payload: {
      mode: string;
      watchedUpTo?: number;
      season?: number;
      seasons?: { season: number; watchedUpTo: number }[];
    },
  ): void;
}>();

const mode = ref<"new" | "restart" | "continue" | "completed">("continue");
const continueFrom = ref(props.currentEpisode ?? 1);
const seasonCounts = ref<Record<number, number>>({});
const saving = ref(false);

const seasonGroups = computed(() =>
  (props.episodeGroups ?? []).filter((group) => group.episodes.length > 0),
);
const multiSeason = computed(() => seasonGroups.value.length > 1);
const episodeTotal = computed(() =>
  multiSeason.value
    ? seasonGroups.value.reduce(
        (sum, group) => sum + group.episodes.length,
        0,
      )
    : props.totalEpisodes,
);
const continueTotal = computed(() =>
  multiSeason.value
    ? seasonGroups.value.reduce(
        (sum, group) => sum + seasonCount(group.season),
        0,
      )
    : Math.max(0, continueFrom.value - 1),
);
const continueSummary = computed(() => {
  if (!multiSeason.value) {
    return `Отметить серии 1–${continueFrom.value - 1} как просмотренные`;
  }
  const parts = seasonGroups.value
    .filter((group) => seasonCount(group.season) > 0)
    .map(
      (group) => `${group.label}: 1–${seasonCount(group.season)}`,
    );
  return parts.length
    ? `Отметить как просмотренные — ${parts.join(", ")}`
    : "Выберите, сколько серий просмотрено в каждом сезоне";
});

const seasonCount = (season: number) => seasonCounts.value[season] ?? 0;

const resetSeasonCounts = () => {
  const activeSeason = props.currentSeason ?? 1;
  const activeEpisode = props.currentEpisode ?? 1;
  const counts: Record<number, number> = {};
  for (const group of seasonGroups.value) {
    let count = 0;
    if (group.season === activeSeason) {
      count = Math.max(0, activeEpisode - 1);
    } else if (group.season > 0 && group.season < activeSeason) {
      count = group.episodes.length;
    }
    counts[group.season] = Math.min(count, group.episodes.length);
  }
  seasonCounts.value = counts;
};

const clampSeasonCount = (season: number, value: number) => {
  const group = seasonGroups.value.find((item) => item.season === season);
  const max = group?.episodes.length ?? 0;
  return Math.min(Math.max(0, Math.trunc(value)), max);
};

const stepSeason = (season: number, delta: number) => {
  seasonCounts.value = {
    ...seasonCounts.value,
    [season]: clampSeasonCount(season, seasonCount(season) + delta),
  };
};

const setSeasonInput = (season: number, event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.value === "") return;
  const value = Number(input.value);
  if (Number.isFinite(value)) {
    const next = clampSeasonCount(season, value);
    seasonCounts.value = { ...seasonCounts.value, [season]: next };
    if (next !== value) input.value = String(next);
  }
};

const normalizeSeasonInput = (season: number, event: Event) => {
  const input = event.target as HTMLInputElement;
  const next = clampSeasonCount(season, Number(input.value) || 0);
  seasonCounts.value = { ...seasonCounts.value, [season]: next };
  input.value = String(next);
};

watch(
  () => props.show,
  (v) => {
    if (v) {
      resetSeasonCounts();
      mode.value = continueTotal.value > 0 ? "continue" : "new";
      continueFrom.value = Math.min(
        Math.max(1, props.currentEpisode ?? 1),
        Math.max(1, props.totalEpisodes),
      );
      saving.value = false;
    }
  },
);

const dec = () => {
  if (continueFrom.value > 1) continueFrom.value--;
};
const inc = () => {
  if (continueFrom.value < props.totalEpisodes) continueFrom.value++;
};

const clampContinueFrom = (value: number) =>
  Math.min(Math.max(1, Math.trunc(value)), Math.max(1, props.totalEpisodes));

const setContinueFromInput = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.value === "") return;
  const value = Number(input.value);
  if (Number.isFinite(value)) {
    continueFrom.value = clampContinueFrom(value);
    if (continueFrom.value !== value) input.value = String(continueFrom.value);
  }
};

const normalizeContinueFromInput = (event: Event) => {
  const input = event.target as HTMLInputElement;
  continueFrom.value = clampContinueFrom(Number(input.value) || 1);
  input.value = String(continueFrom.value);
};

const plural = (n: number) => {
  if (n % 10 === 1 && n % 100 !== 11) return "серия";
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100))
    return "серии";
  return "серий";
};

const apply = async () => {
  saving.value = true;
  if (mode.value === "new") {
    emit("apply", { mode: "new" });
  } else if (mode.value === "restart") {
    emit("apply", { mode: "restart" });
  } else if (mode.value === "completed") {
    emit("apply", { mode: "completed" });
  } else if (multiSeason.value) {
    emit("apply", {
      mode: "continue",
      seasons: seasonGroups.value.map((group) => ({
        season: group.season,
        watchedUpTo: seasonCount(group.season),
      })),
    });
  } else {
    emit("apply", {
      mode: "continue",
      season: props.currentSeason ?? 1,
      watchedUpTo: continueFrom.value - 1,
    });
  }
  saving.value = false;
  emit("close");
};
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: var(--viewport-top, 0px);
  left: 0;
  right: 0;
  height: var(--viewport-height, 100dvh);
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-4);
  backdrop-filter: blur(4px);
}

.modal-box {
  min-width: 0;
  max-height: calc(var(--viewport-height, 100dvh) - 32px);
  overflow-y: auto;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  width: 100%;
  max-width: 480px;
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.modal-header {
  position: sticky;
  top: 0;
  background: var(--surface-3);
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.modal-icon {
  font-size: 1.5rem;
}

.modal-header h2 {
  flex: 1;
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

.close-btn {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--radius-sm);
  transition:
    color var(--duration-base) var(--ease-out),
    background-color var(--duration-base) var(--ease-out);
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.close-btn:hover {
  color: var(--text-primary);
  background: var(--surface-4);
}
.close-btn:active {
  transform: scale(0.96);
}

.anime-label {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
}
.ep-count {
  font-weight: 400;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-left: 0.4rem;
}

/* Варианты */
.options {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.option {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  cursor: pointer;
  background: var(--surface-4);
  transition:
    background-color var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out);
}
.option:hover {
  background: var(--surface-5);
  border-color: var(--border-default);
}
.option.active {
  background: var(--accent-subtle);
}

.option input[type="radio"] {
  width: 18px;
  height: 18px;
  margin-top: 1px;
  accent-color: var(--accent);
  flex-shrink: 0;
  cursor: pointer;
}

.option span,
.option-continue {
  font-size: var(--text-base);
  color: var(--text-primary);
}

.option-continue {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ep-picker {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ep-btn {
  width: 28px;
  height: 28px;
  min-width: 28px;
  min-height: 28px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
  background: var(--surface-4);
  color: var(--text-primary);
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.ep-btn:hover:not(:disabled) {
  background: var(--accent-subtle);
  border-color: var(--accent);
}
.ep-btn:active:not(:disabled) {
  transform: scale(0.96);
}
.ep-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.ep-num {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--accent);
  width: 3.5rem;
  min-width: 3.5rem;
  padding: 0.3rem 0.4rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-2);
  text-align: center;
  outline: none;
  -moz-appearance: textfield;
}
.ep-num:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-subtle);
}
.ep-num::-webkit-inner-spin-button,
.ep-num::-webkit-outer-spin-button {
  margin: 0;
  -webkit-appearance: none;
}
.ep-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.season-progress-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.season-progress-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.season-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.already-watched {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* Ползунок */
.slider-wrap {
  padding: 0 0.25rem;
}

.slider {
  width: 100%;
  accent-color: var(--accent);
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: 0.25rem;
}

/* Инфо */
.info-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  background: var(--surface-4);
  border-radius: var(--radius-lg);
  padding: 0.75rem 1rem;
}
.info-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

/* Кнопки */
.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.btn-cancel {
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
}
.btn-cancel:hover {
  color: var(--text-primary);
}

.btn-apply {
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: var(--shadow-petal);
}
.btn-apply:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 18px var(--accent-glow);
}
.btn-apply:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--surface-5);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Анимация */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active .modal-box {
  animation: slide-up 0.25s ease;
}
@keyframes slide-up {
  from {
    transform: translateY(24px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Polished progress control surface. */
.modal-box {
  max-width: 520px;
  padding: 0;
  gap: 0;
  overflow: hidden auto;
  background:
    radial-gradient(circle at 12% 0%, color-mix(in srgb, var(--accent) 16%, transparent), transparent 42%),
    var(--surface-3);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.42);
}

.modal-header {
  padding: 1.25rem 1.35rem;
  border-bottom: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--surface-3) 88%, transparent);
  backdrop-filter: blur(14px);
}

.modal-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  color: var(--accent);
  background: var(--accent-subtle);
  border: 1px solid color-mix(in srgb, var(--accent) 28%, transparent);
}

.anime-label,
.options,
.slider-wrap,
.info-row,
.modal-actions { margin-left: 1.35rem; margin-right: 1.35rem; }
.anime-label { margin-top: 1.25rem; margin-bottom: 1rem; }
.options { margin-bottom: 1rem; }

.option {
  position: relative;
  min-height: 54px;
  align-items: center;
  border-radius: 15px;
}

.option.active {
  border-color: color-mix(in srgb, var(--accent) 65%, var(--border-default));
  box-shadow: inset 3px 0 0 var(--accent), 0 6px 20px color-mix(in srgb, var(--accent) 10%, transparent);
}

.option input[type="radio"] {
  appearance: none;
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-strong);
  border-radius: 50%;
  background: var(--surface-3);
  transition: 160ms ease;
}

.option input[type="radio"]:checked {
  border: 6px solid var(--accent);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.ep-picker {
  width: fit-content;
  padding: 0.3rem;
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  background: var(--surface-3);
}

.ep-btn { width: 34px; height: 34px; border-radius: 9px; }
.ep-num { min-width: 2.5rem; font-size: 0.8rem; }

.slider-wrap {
  padding: 0.5rem 0;
  border: none;
  background: transparent;
  margin-bottom: 1rem;
}

.info-row { margin-bottom: 1rem; border: 1px solid var(--border-subtle); }
.modal-actions {
  margin: 0;
  padding: 1rem 1.35rem 1.25rem;
  border-top: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--surface-4) 72%, transparent);
}

@media (max-width: 520px) {
  .modal-box { max-height: calc(var(--viewport-height, 100dvh) - 16px); }
  .modal-header { padding: 1rem; }
  .anime-label, .options, .slider-wrap, .info-row { margin-left: 1rem; margin-right: 1rem; }
  .modal-actions { padding: 1rem; }
  .modal-actions .btn { flex: 1; justify-content: center; }
}
</style>
