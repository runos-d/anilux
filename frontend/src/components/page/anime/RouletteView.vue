<template>
  <div class="roulette-page">
    <header class="roulette-hero">
      <div class="hero-copy">
        <h1>Рулетка аниме</h1>
      </div>
      <div class="hero-stats" aria-label="Статистика текущего пресета">
        <div><strong>{{ activePreset.entries.length }}</strong><span>в наборе</span></div>
        <div><strong>{{ eligibleEntries.length }}</strong><span>участвуют</span></div>
        <div>
          <strong>{{ activePreset.rules.eliminateWinner ? eliminatedCount : activePreset.history.length }}</strong>
          <span>{{ activePreset.rules.eliminateWinner ? "выбыли" : "круток" }}</span>
        </div>
      </div>
    </header>

    <section class="preset-strip" aria-label="Пресеты рулетки">
      <div class="preset-scroll">
        <button
          v-for="preset in state.presets"
          :key="preset.id"
          type="button"
          :class="['preset-chip', { active: preset.id === state.activePresetId }]"
          @click="selectPreset(preset.id)"
        >
          <span class="preset-dot"></span>
          {{ preset.name }}
          <small>{{ preset.entries.length }}</small>
        </button>
      </div>
      <button type="button" class="new-preset-btn" @click="addPreset">
        <SakuraIcon name="plus" :size="15" /> Новый пресет
      </button>
    </section>

    <nav class="page-tabs" aria-label="Разделы рулетки">
      <button type="button" :class="{ active: pageTab === 'wheel' }" @click="pageTab = 'wheel'">
        <SakuraIcon name="wheel" :size="17" /> Рулетка
      </button>
      <button type="button" :class="{ active: pageTab === 'history' }" @click="pageTab = 'history'">
        <SakuraIcon name="refresh" :size="17" /> История <span>{{ activePreset.history.length }}</span>
      </button>
    </nav>

    <div v-if="pageTab === 'wheel'" class="roulette-layout">
      <section class="wheel-card panel-card">
        <div class="card-heading wheel-heading">
          <div>
            <h2>{{ activePreset.name }}</h2>
          </div>
        </div>
        <!-- <div class="wheel-mode-summary">
          <span :class="{ active: activePreset.rules.eliminateWinner }">{{ activePreset.rules.eliminateWinner ? "На выбывание" : "С повторениями" }}</span>
          <span :class="{ active: activePreset.rules.inverseWeights }">{{ activePreset.rules.inverseWeights ? "Меньше вес — чаще" : "Больше вес — чаще" }}</span>
          <span>{{ activePreset.rules.spinDurationSeconds }} сек · {{ activePreset.rules.spinSpeedRpm }} об/мин</span>
        </div> -->

        <div class="wheel-stage" :class="{ spinning: isSpinning }">
          <div class="wheel-pointer" aria-hidden="true">
            <svg viewBox="0 0 52 68" focusable="false">
              <path d="M8 10C12 4 19 2 26 2s14 2 18 8L32 55c-2 8-10 8-12 0L8 10Z" />
              <circle cx="26" cy="14" r="6" />
            </svg>
          </div>
          <div
            :class="['wheel', { empty: !wheelEntries.length }]"
            :style="{
              background: wheelGradient,
              transform: `rotate(${wheelRotation}deg)`,
              '--spin-duration': `${activePreset.rules.spinDurationSeconds}s`,
              '--content-rotation': `${wheelContentRotation}deg`,
            }"
            role="img"
            :aria-label="wheelAriaLabel"
          >
            <div
              v-for="segment in wheelSegments"
              :key="`art-${segment.entry.anime.id}`"
              class="wheel-segment-art"
              :style="{
                '--segment-start': `${segment.artStart}deg`,
                '--segment-end': `${segment.artEnd}deg`,
              }"
            >
              <div
                class="wheel-segment-poster"
                :style="{
                  backgroundImage: animePoster(segment.entry.anime)
                    ? `linear-gradient(180deg, rgba(9, 6, 12, .06), rgba(9, 6, 12, .72)), url(${animePoster(segment.entry.anime)})`
                    : undefined,
                }"
              ></div>
            </div>
            <div class="wheel-rim" aria-hidden="true"></div>
            <div
              v-for="label in wheelLabels"
              :key="label.entry.anime.id"
              class="wheel-label"
              :style="{
                '--label-angle': `${label.angle}deg`,
                '--label-angle-inverse': `${-label.angle}deg`,
              }"
            >
              <span>{{ shortTitle(label.entry.anime.title_ru) }}</span>
            </div>
          </div>
          <button
            type="button"
            class="wheel-hub"
            :disabled="isSpinning || !eligibleEntries.length"
            :aria-label="isSpinning ? 'Рулетка вращается' : 'Крутить рулетку'"
            @click="spin"
          >
            <img src="/sakura.svg?v=roulette-hub-20261023" alt="" class="wheel-hub-sakura" />
            <span>{{ !eligibleEntries.length ? "" : isSpinning ? "Крутим" : "Крутить" }}</span>
          </button>
        </div>

        <div v-if="result" class="result-card" aria-live="polite">
          <img
            v-if="animePoster(result)"
            :src="animePoster(result)"
            :alt="`Постер ${result.title_ru}`"
            class="result-poster"
          />
          <div class="result-copy">
            <span class="result-label">Колесо выбрало</span>
            <h3>{{ result.title_ru }}</h3>
            <p>{{ [result.year, kindLabel(result.kind), scoreLabel(result.score)].filter(Boolean).join(" · ") }}</p>
          </div>
          <div class="result-actions">
            <button type="button" class="primary-action" @click="watchResult">
              <SakuraIcon name="play" :size="16" /> Смотреть
            </button>
            <button
              v-if="resultEntry?.eliminated"
              type="button"
              class="secondary-action"
              title="Вернуть результат на колесо"
              @click="restoreResult"
            >
              <SakuraIcon name="refresh" :size="15" /> Вернуть
            </button>
            <button v-else type="button" class="icon-action" title="Убрать из этого пресета" aria-label="Убрать результат из пресета" @click="excludeResult">
              <SakuraIcon name="eye-off" :size="17" />
            </button>
          </div>
        </div>
      </section>

      <section class="setup-card panel-card">
        <div class="editor-tabs" role="tablist" aria-label="Настройка пресета">
          <button type="button" :class="{ active: setupTab === 'entries' }" @click="setupTab = 'entries'">
            <SakuraIcon name="book" :size="15" /> Аниме <span>{{ activePreset.entries.length }}</span>
          </button>
          <button type="button" :class="{ active: setupTab === 'add' }" @click="setupTab = 'add'">
            <SakuraIcon name="plus" :size="15" /> Добавить
          </button>
          <button type="button" :class="{ active: setupTab === 'settings' }" @click="setupTab = 'settings'">
            <SakuraIcon name="settings" :size="15" /> Настройки
          </button>
        </div>

        <div v-if="setupTab === 'add'" class="add-panel">
          <div class="add-source-switch">
            <button type="button" :class="{ active: sourceTab === 'search' }" @click="sourceTab = 'search'"><SakuraIcon name="search" :size="15" /> Поиск</button>
            <button type="button" :class="{ active: sourceTab === 'library' }" @click="openLibrarySource"><SakuraIcon name="book" :size="15" /> Из коллекции</button>
          </div>

          <div v-if="sourceTab === 'search'" class="source-panel search-panel">
            <label class="anime-search">
              <SakuraIcon name="search" :size="17" />
              <input v-model="searchQuery" type="search" autocomplete="off" placeholder="Название аниме…" />
              <span v-if="searchLoading" class="search-spinner"><SakuraIcon name="spinner" :size="16" /></span>
              <button v-else-if="searchQuery" type="button" aria-label="Очистить поиск" @click="clearAnimeSearch">×</button>
            </label>
            <div v-if="searchError" class="source-message error">{{ searchError }}</div>
            <div v-else-if="searchQuery.length > 1 && !searchLoading && !searchResults.length" class="source-message">Ничего не нашли. Попробуйте другое название.</div>
            <div v-if="searchResults.length" ref="searchResultsList" class="search-results">
              <button
                v-for="anime in searchResults"
                :key="anime.id"
                type="button"
                class="search-result"
                :disabled="hasAnime(anime.id)"
                @click="addAnime(anime)"
              >
                <img v-if="animePoster(anime)" :src="animePoster(anime)" alt="" />
                <span class="result-text"><strong>{{ anime.title_ru }}</strong><small>{{ [anime.year, scoreLabel(anime.score)].filter(Boolean).join(" · ") }}</small></span>
                <span class="add-result">{{ hasAnime(anime.id) ? "Добавлено" : "+ Добавить" }}</span>
              </button>
            </div>
            <nav v-if="searchResults.length && (searchPage > 1 || searchHasMore)" class="search-pagination" aria-label="Страницы результатов поиска">
              <button type="button" :disabled="searchLoading || searchPage <= 1" aria-label="Предыдущая страница" @click="searchPreviousPage">
                <SakuraIcon name="arrow-left" :size="17" />
              </button>
              <span>Страница {{ searchPage }}</span>
              <button type="button" :disabled="searchLoading || !searchHasMore" aria-label="Следующая страница" @click="searchNextPage">
                <SakuraIcon name="arrow-right" :size="17" />
              </button>
            </nav>
            <p v-else-if="searchQuery.length < 2" class="source-tip">Введите минимум 2 символа</p>
          </div>

          <div v-else class="source-panel library-panel">
            <template v-if="authStore.isAuthenticated">
              <div class="library-controls">
                <label>
                  <span>Показывать</span>
                  <select v-model="libraryStatusFilter">
                    <option value="all">Все статусы</option>
                    <option v-for="status in LIBRARY_STATUS_OPTIONS" :key="status.value" :value="status.value">
                      {{ status.label }} · {{ libraryStatusCount(status.value) }}
                    </option>
                  </select>
                </label>
                <label>
                  <span>Сортировка</span>
                  <select v-model="librarySort">
                    <option value="status">По статусу</option>
                    <option value="title">По названию</option>
                    <option value="updated">Недавно изменённые</option>
                  </select>
                </label>
              </div>

              <div class="library-status-controls" aria-label="Участие статусов коллекции">
                <button
                  v-for="status in LIBRARY_STATUS_OPTIONS"
                  :key="status.value"
                  type="button"
                  :class="['library-status-toggle', status.value, { excluded: isLibraryStatusExcluded(status.value) }]"
                  :aria-pressed="isLibraryStatusExcluded(status.value)"
                  @click="toggleLibraryStatusExclusion(status.value)"
                >
                  <span class="library-status-dot"></span>
                  <span><strong>{{ status.label }}</strong><small>{{ libraryStatusCount(status.value) }} · {{ isLibraryStatusExcluded(status.value) ? "Исключён" : "Участвует" }}</small></span>
                  <SakuraIcon :name="isLibraryStatusExcluded(status.value) ? 'plus' : 'x'" :size="14" />
                </button>
              </div>

              <div class="library-list-heading">
                <span>{{ visibleLibraryItems.length }} аниме</span>
                <button type="button" :disabled="!addableLibraryItems.length || libraryLoading" @click="addVisibleLibraryItems">
                  + Добавить показанные<span v-if="addableLibraryItems.length"> · {{ addableLibraryItems.length }}</span>
                </button>
              </div>

              <div v-if="libraryLoading && !libraryLoaded" class="library-state"><SakuraIcon name="spinner" :size="18" /> Загружаем коллекцию…</div>
              <div v-else-if="libraryError" class="library-state error">
                <span>{{ libraryError }}</span>
                <button type="button" @click="loadLibraryCollection(true)">Повторить</button>
              </div>
              <div v-else-if="visibleLibraryItems.length" class="library-anime-list">
                <article
                  v-for="item in visibleLibraryItems"
                  :key="item.id"
                  :class="['library-anime-row', { excluded: isLibraryStatusExcluded(item.status) }]"
                >
                  <img v-if="animePoster(libraryAnime(item))" :src="animePoster(libraryAnime(item))" alt="" />
                  <div v-else class="library-poster-placeholder">{{ libraryAnime(item).title_ru.slice(0, 1) }}</div>
                  <div class="library-anime-info">
                    <strong>{{ libraryAnime(item).title_ru }}</strong>
                    <small>{{ [libraryAnime(item).year, kindLabel(libraryAnime(item).kind)].filter(Boolean).join(" · ") || "В коллекции" }}</small>
                  </div>
                  <span :class="['library-status-badge', item.status]">{{ libraryStatusTitle(item.status) }}</span>
                  <button
                    type="button"
                    class="library-add-button"
                    :disabled="hasAnime(item.anime_id) || isLibraryStatusExcluded(item.status)"
                    @click="addLibraryItem(item)"
                  >
                    {{ hasAnime(item.anime_id) ? "Добавлено" : isLibraryStatusExcluded(item.status) ? "Исключено" : "+ Добавить" }}
                  </button>
                </article>
              </div>
              <div v-else class="library-state">В этом статусе пока нет аниме.</div>
              <p v-if="libraryMessage" class="library-message">{{ libraryMessage }}</p>
              <button v-if="libraryLoaded" type="button" class="library-refresh-button" :disabled="libraryLoading" @click="loadLibraryCollection(true)">
                <SakuraIcon name="refresh" :size="14" /> {{ libraryLoading ? "Обновляем…" : "Обновить коллекцию" }}
              </button>
            </template>
            <div v-else class="login-callout">
              <SakuraIcon name="book" :size="24" />
              <div><strong>Коллекция доступна после входа</strong><p>Поиск и локальные пресеты работают без аккаунта.</p></div>
              <RouterLink to="/login">Войти</RouterLink>
            </div>
          </div>
        </div>

        <div v-else-if="setupTab === 'settings'" class="source-panel rules-panel">
          <label class="preset-rename-setting">
            <span><strong>Название пресета</strong><small>Отображается над колесом и в списке пресетов</small></span>
            <input v-model="activePreset.name" type="text" maxlength="60" aria-label="Название пресета" @blur="ensurePresetName" @keyup.enter="ensurePresetName" />
          </label>
          <div class="mode-bar" aria-label="Режимы рулетки">
            <button type="button" :class="['mode-button', { active: activePreset.rules.eliminateWinner }]" :aria-pressed="activePreset.rules.eliminateWinner" @click="toggleEliminationMode">
              <span class="mode-icon"><SakuraIcon name="filter" :size="17" /></span>
              <span><strong>{{ activePreset.rules.eliminateWinner ? "На выбывание" : "С повторениями" }}</strong><small>{{ activePreset.rules.eliminateWinner ? "Выпавшее сразу покидает колесо" : "Выпавшее остаётся в списке" }}</small></span>
              <span class="mode-switch"><i></i></span>
            </button>
            <button type="button" :class="['mode-button', { active: activePreset.rules.inverseWeights }]" :aria-pressed="activePreset.rules.inverseWeights" @click="toggleWeightMode">
              <span class="mode-icon"><SakuraIcon name="settings" :size="17" /></span>
              <span><strong>{{ activePreset.rules.inverseWeights ? "Обратные веса" : "Прямые веса" }}</strong><small>{{ activePreset.rules.inverseWeights ? "Число больше → шанс ниже" : "Число больше → шанс выше" }}</small></span>
              <span class="mode-switch"><i></i></span>
            </button>
          </div>
          <div class="spin-settings-grid">
            <label class="range-setting">
              <span><strong>Время вращения</strong><small>Длительность одной крутки</small></span>
              <input v-model.number="activePreset.rules.spinDurationSeconds" class="setting-number" type="number" min="0.1" step="0.1" inputmode="decimal" @change="normalizeSpinSettings" />
            </label>
            <label class="range-setting">
              <span><strong>Скорость</strong><small>Обороты в минуту</small></span>
              <input v-model.number="activePreset.rules.spinSpeedRpm" class="setting-number" type="number" min="0.1" step="any" inputmode="decimal" @change="normalizeSpinSettings" />
            </label>
          </div>
          <div class="settings-section-title filters-title"><span>Фильтры коллекции</span></div>
          <div class="filter-toggle-grid">
            <label class="rule-row">
              <span><strong>Убирать просмотренное</strong><small>Статус «Просмотрено» в коллекции</small></span>
              <input v-model="activePreset.rules.excludeCompleted" type="checkbox" />
            </label>
            <label class="rule-row">
              <span><strong>Убирать брошенное</strong><small>Не предлагать то, что уже не зашло</small></span>
              <input v-model="activePreset.rules.excludeDropped" type="checkbox" />
            </label>
          </div>
          <!-- <label class="rule-select-row">
            <span><strong>Не повторять последние</strong><small>Если вариантов мало, правило временно ослабнет</small></span>
            <select v-model.number="activePreset.rules.avoidLast">
              <option :value="0">Не учитывать</option>
              <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
            </select>
          </label> -->
          <div class="rules-actions">
            <button v-if="eliminatedCount" type="button" class="reset-round-button" @click="resetEliminated">
              <SakuraIcon name="refresh" :size="15" /> Вернуть выбывшие — {{ eliminatedCount }}
            </button>
            <button v-if="authStore.isAuthenticated" type="button" class="sync-button" :disabled="libraryLoading" @click="syncLibraryStatuses">
              <SakuraIcon name="refresh" :size="15" /> {{ libraryLoading ? "Сверяем…" : "Сверить с коллекцией сейчас" }}
            </button>
          </div>
          <div class="preset-end-actions">
            <button type="button" class="copy-preset-button" @click="duplicatePreset">
              <SakuraIcon name="copy" :size="16" /> Копировать пресет
            </button>
            <button type="button" class="delete-preset-button" :disabled="state.presets.length === 1" @click="deletePreset">
              <SakuraIcon name="trash" :size="16" /> Удалить пресет
            </button>
          </div>
        </div>

        <div v-else class="entries-panel">
          <!-- <div class="entries-toolbar">
            <div>
              <strong>Аниме</strong>
              <small>{{ activePreset.rules.inverseWeights ? "меньше вес — чаще" : "больше вес — чаще" }}</small>
            </div>
            <div class="toolbar-actions">
              <button v-if="eliminatedCount" type="button" @click="resetEliminated">Вернуть выбывших</button>
              <button type="button" :disabled="!activePreset.entries.length" @click="equalizeWeights">Уравнять</button>
            </div>
          </div> -->

          <div v-if="activePreset.entries.length" class="entries-list">
            <article
              v-for="(entry, index) in activePreset.entries"
              :key="entry.anime.id"
              :class="['entry-row', { excluded: isExcluded(entry), eliminated: entry.eliminated, recent: isRecent(entry) }]"
            >
              <div class="entry-visual">
                <img v-if="animePoster(entry.anime)" :src="animePoster(entry.anime)" alt="" class="entry-poster" />
                <div v-else class="entry-poster placeholder">{{ entry.anime.title_ru.slice(0, 1) }}</div>
              </div>
              <div class="entry-info">
                <strong>{{ entry.anime.title_ru }}</strong>
                <span v-if="entry.eliminated">Выбыло после крутки</span>
                <span v-else-if="entry.excludedByLibrary">Исключено: {{ libraryStatusLabel(entry.libraryStatus) }}</span>
                <span v-else-if="entry.disabled">Выключено вручную</span>
                <span v-else-if="isRecent(entry)">Пауза после недавней крутки</span>
                <span v-else>{{ [entry.anime.year, kindLabel(entry.anime.kind)].filter(Boolean).join(" · ") || "Готово к крутке" }}</span>
              </div>
              <label class="weight-field">
                <span>{{ activePreset.rules.inverseWeights ? "Вес" : "Вес" }}</span>
                <input v-model.number="entry.weight" type="number" min="0.01" step="any" inputmode="decimal" :aria-label="`Вес ${entry.anime.title_ru}`" @input="invalidateWheel" @change="normalizeEntryWeight(entry)" />
              </label>
              <div class="entry-actions">
                <button type="button" class="participation-btn" :title="entry.disabled || entry.eliminated ? 'Вернуть в крутку' : 'Исключить из крутки'" :aria-label="entry.disabled || entry.eliminated ? `Вернуть ${entry.anime.title_ru} в крутку` : `Исключить ${entry.anime.title_ru} из крутки`" @click="toggleEntry(entry)">
                  <SakuraIcon :name="entry.disabled || entry.eliminated ? 'refresh' : 'check'" :size="16" />
                </button>
                <button type="button" class="remove-entry-btn" title="Удалить" :aria-label="`Удалить ${entry.anime.title_ru}`" @click="removeEntry(index)">
                  <SakuraIcon name="trash" :size="16" />
                </button>
              </div>
            </article>
          </div>
          <div v-else class="empty-entries">
            <div><SakuraIcon name="wheel" :size="30" /></div>
            <strong>Колесо пока пустое</strong>
            <p>Найдите аниме выше или импортируйте список из своей коллекции.</p>
            <button type="button" @click="setupTab = 'add'">Добавить аниме</button>
          </div>
        </div>
      </section>
    </div>

    <section v-else class="history-card panel-card">
      <div class="card-heading history-heading">
        <div><span class="section-kicker">Пресет «{{ activePreset.name }}»</span><h2>История круток</h2></div>
        <button v-if="activePreset.history.length" type="button" @click="clearHistory">Очистить историю</button>
      </div>
      <div v-if="activePreset.history.length" class="history-list">
        <article v-for="(item, index) in activePreset.history" :key="item.id">
          <span class="history-index">{{ String(index + 1).padStart(2, "0") }}</span>
          <img v-if="animePoster(item.anime)" :src="animePoster(item.anime)" alt="" />
          <div><strong>{{ item.anime.title_ru }}</strong><small>{{ formatHistoryDate(item.createdAt) }}</small></div>
          <RouterLink :to="`/anime/${item.anime.slug || item.anime.id}`">Открыть</RouterLink>
        </article>
      </div>
      <div v-else class="empty-history">После первой крутки результат сохранится здесь.</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { animeApi, type Anime } from "@/api/anime";
import { isFavoriteFranchiseItem, libraryApi, type CollectionItem, type LibraryItem, type LibraryStatus } from "@/api/library";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { useAuthStore } from "@/stores/auth";
import {
  ROULETTE_COLORS,
  buildWheelGradient,
  clampSpinDuration,
  clampSpinSpeed,
  clampWeight,
  createId,
  createPreset,
  createRouletteState,
  entryProbability,
  getEligibleEntries,
  isEntryExcluded,
  parseRouletteState,
  pickWeighted,
  wheelSegmentCenter,
  wheelSegmentLanding,
  type RouletteEntry,
  type RoulettePreset,
  type RouletteState,
} from "@/lib/roulette";

type PageTab = "wheel" | "history";
type SetupTab = "entries" | "add" | "settings";
type SourceTab = "search" | "library";
type LibraryStatusFilter = LibraryStatus | "all";
type LibrarySort = "status" | "title" | "updated";

const LIBRARY_STATUS_OPTIONS: Array<{ value: LibraryStatus; label: string }> = [
  { value: "started", label: "Смотрю" },
  { value: "planned", label: "Запланировано" },
  { value: "on_hold", label: "Отложено" },
  { value: "completed", label: "Просмотрено" },
  { value: "dropped", label: "Брошено" },
];
const LIBRARY_STATUS_ORDER = new Map(LIBRARY_STATUS_OPTIONS.map((status, index) => [status.value, index]));

const authStore = useAuthStore();
const router = useRouter();
const state = ref<RouletteState>(createRouletteState());
const initialized = ref(false);
const pageTab = ref<PageTab>("wheel");
const setupTab = ref<SetupTab>("entries");
const sourceTab = ref<SourceTab>("search");
const searchQuery = ref("");
const searchResults = ref<Anime[]>([]);
const searchLoading = ref(false);
const searchError = ref("");
const searchPage = ref(1);
const searchHasMore = ref(false);
const searchResultsList = ref<HTMLElement | null>(null);
const libraryLoading = ref(false);
const libraryMessage = ref("");
const libraryError = ref("");
const libraryLoaded = ref(false);
const libraryItems = ref<LibraryItem[]>([]);
const libraryStatusFilter = ref<LibraryStatusFilter>("all");
const librarySort = ref<LibrarySort>("status");
const isSpinning = ref(false);
const wheelRotation = ref(0);
const wheelContentRotation = ref(0);
const result = ref<Anime | null>(null);
const wheelSnapshot = ref<RouletteEntry[] | null>(null);
const libraryStatuses = new Map<number, LibraryStatus>();
let searchTimer: ReturnType<typeof setTimeout> | undefined;
let spinTimer: ReturnType<typeof setTimeout> | undefined;
let searchController: AbortController | undefined;
const SEARCH_PAGE_SIZE = 10;

const storageKey = computed(() => `anilux_roulette_v1:${authStore.user?.id ?? "guest"}`);
const activePreset = computed<RoulettePreset>(() => {
  const found = state.value.presets.find((preset) => preset.id === state.value.activePresetId);
  return found ?? state.value.presets[0]!;
});
const eligibleEntries = computed(() => getEligibleEntries(activePreset.value));
const wheelEntries = computed(() => wheelSnapshot.value ?? eligibleEntries.value);
const wheelGradient = computed(() => buildWheelGradient(wheelEntries.value, activePreset.value.rules.inverseWeights));
const wheelAriaLabel = computed(() => wheelEntries.value.length
  ? `Колесо с вариантами: ${wheelEntries.value.map((entry) => entry.anime.title_ru).join(", ")}`
  : "Пустое колесо");
const wheelSegments = computed(() => {
  let start = 0;
  return wheelEntries.value.map((entry) => {
    const span = entryProbability(entry, wheelEntries.value, activePreset.value.rules.inverseWeights) * 3.6;
    const edge = Math.min(.42, span * .12);
    const segment = { entry, start, end: start + span, artStart: start + edge, artEnd: start + span - edge };
    start += span;
    return segment;
  });
});
const wheelLabels = computed(() => wheelSegments.value.slice(0, 12).map((segment) => ({
  entry: segment.entry,
  angle: wheelSegmentCenter(segment.entry, wheelEntries.value, activePreset.value.rules.inverseWeights),
})));
const eliminatedCount = computed(() => activePreset.value.entries.filter((entry) => entry.eliminated).length);
const spinTurns = computed(() => Math.max(1, Math.round(
  activePreset.value.rules.spinDurationSeconds * activePreset.value.rules.spinSpeedRpm / 60,
)));
const resultEntry = computed(() => result.value
  ? activePreset.value.entries.find((entry) => entry.anime.id === result.value?.id) ?? null
  : null);
const readyLabel = computed(() => {
  if (eligibleEntries.value.length) return `${eligibleEntries.value.length} вариантов`;
  if (eliminatedCount.value && activePreset.value.rules.eliminateWinner) return "Круг завершён";
  return "Добавьте варианты";
});
const compactAnime = (anime: Anime): Anime => ({
  id: anime.id,
  slug: anime.slug,
  title_ru: anime.title_ru,
  title_en: anime.title_en,
  year: anime.year,
  status: anime.status,
  kind: anime.kind,
  episodes: anime.episodes,
  score: anime.score,
  poster_url: anime.poster_url,
  poster_image_url: anime.poster_image_url,
  genres: anime.genres,
});
const animePoster = (anime: Anime): string => anime.poster_image_url || anime.poster_url || "";
const scoreLabel = (score?: number): string => score ? `★ ${Number(score).toFixed(1)}` : "";
const kindLabel = (kind?: string): string => ({ tv: "TV-сериал", movie: "Фильм", ona: "ONA", ova: "OVA", special: "Спешл" }[kind || ""] || kind || "");
const shortTitle = (title: string): string => title.length > 18 ? `${title.slice(0, 16)}…` : title;
const isExcluded = (entry: RouletteEntry): boolean => isEntryExcluded(entry);
const hasAnime = (animeId: number): boolean => activePreset.value.entries.some((entry) => entry.anime.id === animeId);
const isLibraryStatusExcluded = (status: LibraryStatus): boolean =>
  activePreset.value.rules.excludedLibraryStatuses.includes(status);
const visibleLibraryItems = computed(() => {
  const items = libraryStatusFilter.value === "all"
    ? [...libraryItems.value]
    : libraryItems.value.filter((item) => item.status === libraryStatusFilter.value);
  return items.sort((left, right) => {
    if (librarySort.value === "title") return left.anime_title_ru.localeCompare(right.anime_title_ru, "ru");
    if (librarySort.value === "updated") {
      return new Date(right.updated_at || right.added_at).getTime() - new Date(left.updated_at || left.added_at).getTime();
    }
    const statusDifference = (LIBRARY_STATUS_ORDER.get(left.status) ?? 99) - (LIBRARY_STATUS_ORDER.get(right.status) ?? 99);
    return statusDifference || left.anime_title_ru.localeCompare(right.anime_title_ru, "ru");
  });
});
const addableLibraryItems = computed(() => visibleLibraryItems.value.filter((item) =>
  !hasAnime(item.anime_id) && !isLibraryStatusExcluded(item.status),
));
const libraryStatusCount = (status: LibraryStatus): number =>
  libraryItems.value.filter((item) => item.status === status).length;
const recentIds = computed(() => new Set(activePreset.value.history.slice(0, activePreset.value.rules.avoidLast).map((item) => item.anime.id)));
const isRecent = (entry: RouletteEntry): boolean => !isExcluded(entry) && recentIds.value.has(entry.anime.id) && eligibleEntries.value.length > 0;
const entryColor = (entry: RouletteEntry): string => {
  const index = wheelEntries.value.findIndex((item) => item.anime.id === entry.anime.id);
  return index >= 0 ? ROULETTE_COLORS[index % ROULETTE_COLORS.length]! : "var(--text-disabled)";
};

const persist = () => {
  if (!initialized.value) return;
  localStorage.setItem(storageKey.value, JSON.stringify(state.value));
};

const invalidateWheel = () => {
  if (!isSpinning.value) wheelSnapshot.value = null;
};

const seedPreset = async () => {
  try {
    const response = await animeApi.list({ ordering: "-score", page_size: 8 });
    activePreset.value.entries = response.results.slice(0, 8).map((anime) => ({ anime: compactAnime(anime), weight: 10, disabled: false }));
  } catch {
  }
};

const selectPreset = (id: string) => {
  if (isSpinning.value) return;
  state.value.activePresetId = id;
  result.value = null;
  wheelSnapshot.value = null;
  applyLibraryRules();
};

const addPreset = () => {
  const preset = createPreset(`Пресет ${state.value.presets.length + 1}`);
  state.value.presets.push(preset);
  selectPreset(preset.id);
  setupTab.value = "entries";
};

const duplicatePreset = () => {
  const original = activePreset.value;
  const now = new Date().toISOString();
  const clone: RoulettePreset = {
    id: createId(),
    name: `${original.name} — копия`,
    entries: original.entries.map((entry) => ({ ...entry, anime: { ...entry.anime } })),
    rules: { ...original.rules },
    history: [],
    createdAt: now,
    updatedAt: now,
  };
  state.value.presets.push(clone);
  selectPreset(clone.id);
};

const deletePreset = () => {
  if (state.value.presets.length === 1) return;
  if (!window.confirm(`Удалить пресет «${activePreset.value.name}»?`)) return;
  const index = state.value.presets.findIndex((preset) => preset.id === activePreset.value.id);
  state.value.presets.splice(index, 1);
  state.value.activePresetId = state.value.presets[Math.max(0, index - 1)]!.id;
  result.value = null;
};

const ensurePresetName = () => {
  if (!activePreset.value.name.trim()) activePreset.value.name = "Без названия";
};

const addAnime = (anime: Anime) => {
  if (hasAnime(anime.id)) return;
  const libraryStatus = libraryStatuses.get(anime.id);
  activePreset.value.entries.push({ anime: compactAnime(anime), weight: 10, disabled: false, libraryStatus });
  applyLibraryRules();
  invalidateWheel();
};

const removeEntry = (index: number) => {
  activePreset.value.entries.splice(index, 1);
  if (result.value && !hasAnime(result.value.id)) result.value = null;
  invalidateWheel();
};

const normalizeEntryWeight = (entry: RouletteEntry) => {
  entry.weight = clampWeight(entry.weight);
  invalidateWheel();
};
const equalizeWeights = () => {
  activePreset.value.entries.forEach((entry) => { entry.weight = 10; });
  invalidateWheel();
};
const toggleEntry = (entry: RouletteEntry) => {
  if (entry.eliminated) entry.eliminated = false;
  else entry.disabled = !entry.disabled;
  invalidateWheel();
};
const resetEliminated = () => {
  activePreset.value.entries.forEach((entry) => { entry.eliminated = false; });
  invalidateWheel();
};
const toggleEliminationMode = () => {
  activePreset.value.rules.eliminateWinner = !activePreset.value.rules.eliminateWinner;
};
const toggleWeightMode = () => {
  activePreset.value.rules.inverseWeights = !activePreset.value.rules.inverseWeights;
  invalidateWheel();
};
const normalizeSpinSettings = () => {
  activePreset.value.rules.spinDurationSeconds = clampSpinDuration(activePreset.value.rules.spinDurationSeconds);
  activePreset.value.rules.spinSpeedRpm = clampSpinSpeed(activePreset.value.rules.spinSpeedRpm);
};

const runSearch = async (query: string, page = 1) => {
  const normalizedQuery = query.trim();
  if (normalizedQuery.length < 2 || page < 1) {
    searchController?.abort();
    searchResults.value = [];
    searchPage.value = 1;
    searchHasMore.value = false;
    searchLoading.value = false;
    searchError.value = "";
    return;
  }
  searchController?.abort();
  const controller = new AbortController();
  searchController = controller;
  searchLoading.value = true;
  searchError.value = "";
  try {
    const response = await animeApi.searchPaginated(normalizedQuery, page, SEARCH_PAGE_SIZE, controller.signal);
    if (controller.signal.aborted || normalizedQuery !== searchQuery.value.trim()) return;
    searchResults.value = response.results || [];
    searchPage.value = response.page || page;
    searchHasMore.value = Boolean(response.has_more);
    searchResultsList.value?.scrollTo({ top: 0 });
  } catch {
    if (!controller.signal.aborted) {
      searchResults.value = [];
      searchHasMore.value = false;
      searchError.value = "Не удалось выполнить поиск. Проверьте соединение.";
    }
  } finally {
    if (searchController === controller) {
      searchController = undefined;
      searchLoading.value = false;
    }
  }
};

watch(searchQuery, (query) => {
  clearTimeout(searchTimer);
  searchController?.abort();
  searchPage.value = 1;
  searchHasMore.value = false;
  searchError.value = "";
  if (query.trim().length < 2) {
    searchResults.value = [];
    searchLoading.value = false;
    return;
  }
  searchResults.value = [];
  searchTimer = setTimeout(() => void runSearch(query, 1), 280);
});

const searchPreviousPage = () => void runSearch(searchQuery.value, searchPage.value - 1);
const searchNextPage = () => void runSearch(searchQuery.value, searchPage.value + 1);
const clearAnimeSearch = () => {
  clearTimeout(searchTimer);
  searchController?.abort();
  searchController = undefined;
  searchQuery.value = "";
  searchResults.value = [];
  searchPage.value = 1;
  searchHasMore.value = false;
  searchLoading.value = false;
  searchError.value = "";
};

const unwrapLibrary = (data: CollectionItem[] | { results: CollectionItem[] }): CollectionItem[] => Array.isArray(data) ? data : data.results;
const libraryAnime = (item: LibraryItem): Anime => {
  const anime = typeof item.anime === "object" ? item.anime : null;
  return {
    id: item.anime_id || anime?.id || Number(item.anime),
    slug: item.anime_slug || anime?.slug,
    title_ru: item.anime_title_ru || anime?.title_ru || "Без названия",
    title_en: item.anime_title_en || anime?.title_en,
    poster_url: item.anime_poster || anime?.poster_url || anime?.poster,
    poster_image_url: anime?.poster_image_url,
    episodes: item.anime_episodes_count || anime?.episodes || anime?.episodes_count,
    score: item.anime_score || anime?.score,
    year: item.anime_year || anime?.year,
    kind: item.anime_kind || anime?.kind || anime?.type,
    status: item.anime_status || anime?.status,
    genres: item.anime_genres,
  };
};

const fetchAllLibraryItems = async (): Promise<LibraryItem[]> => {
  const collected: LibraryItem[] = [];
  let page = 1;
  let total = Number.POSITIVE_INFINITY;
  while (collected.length < total) {
    const data = await libraryApi.getLibrary({ page, page_size: 100, ordering: "-updated_at" });
    const batch = unwrapLibrary(data).filter((item): item is LibraryItem => !isFavoriteFranchiseItem(item));
    collected.push(...batch);
    if (Array.isArray(data)) break;
    total = data.count;
    if (!batch.length || !data.next) break;
    page++;
  }
  return collected;
};

const loadLibraryCollection = async (announce = false) => {
  if (!authStore.isAuthenticated || libraryLoading.value) return;
  libraryLoading.value = true;
  libraryError.value = "";
  if (announce) libraryMessage.value = "";
  try {
    const items = await fetchAllLibraryItems();
    libraryItems.value = items;
    libraryStatuses.clear();
    for (const item of items) {
      libraryStatuses.set(item.anime_id, item.status);
    }
    libraryLoaded.value = true;
    applyLibraryRules();
    if (announce) libraryMessage.value = `Коллекция обновлена · ${items.length} аниме.`;
  } catch {
    libraryError.value = "Не удалось загрузить коллекцию.";
  } finally {
    libraryLoading.value = false;
  }
};

const openLibrarySource = () => {
  sourceTab.value = "library";
  if (!libraryLoaded.value) void loadLibraryCollection();
};

const addLibraryItem = (item: LibraryItem) => {
  if (hasAnime(item.anime_id) || isLibraryStatusExcluded(item.status)) return;
  libraryStatuses.set(item.anime_id, item.status);
  addAnime(libraryAnime(item));
};

const addVisibleLibraryItems = () => {
  const items = [...addableLibraryItems.value];
  for (const item of items) addLibraryItem(item);
  libraryMessage.value = items.length
    ? `Добавлено из коллекции: ${items.length}.`
    : "Все показанные аниме уже добавлены или исключены по статусу.";
};

const toggleLibraryStatusExclusion = (status: LibraryStatus) => {
  const excluded = new Set(activePreset.value.rules.excludedLibraryStatuses);
  if (excluded.has(status)) excluded.delete(status);
  else excluded.add(status);
  activePreset.value.rules.excludedLibraryStatuses = LIBRARY_STATUS_OPTIONS
    .map((option) => option.value)
    .filter((value) => excluded.has(value));
  if (status === "completed") activePreset.value.rules.excludeCompleted = excluded.has(status);
  if (status === "dropped") activePreset.value.rules.excludeDropped = excluded.has(status);
  applyLibraryRules();
};

const applyLibraryRules = () => {
  const rules = activePreset.value.rules;
  const excludedStatuses = new Set(rules.excludedLibraryStatuses);
  for (const entry of activePreset.value.entries) {
    const status = libraryStatuses.get(entry.anime.id) ?? entry.libraryStatus as LibraryStatus | undefined;
    entry.libraryStatus = status;
    entry.excludedByLibrary = Boolean(status && excludedStatuses.has(status));
  }
  invalidateWheel();
};

const syncLibraryStatuses = async () => {
  if (!authStore.isAuthenticated) return;
  libraryLoading.value = true;
  libraryMessage.value = "";
  try {
    const items = await fetchAllLibraryItems();
    libraryItems.value = items;
    libraryStatuses.clear();
    for (const item of items) libraryStatuses.set(item.anime_id, item.status);
    libraryLoaded.value = true;
    applyLibraryRules();
    libraryMessage.value = `Статусы коллекции обновлены · ${items.length} аниме.`;
  } catch {
    libraryMessage.value = "Не удалось сверить статусы коллекции.";
  } finally {
    libraryLoading.value = false;
  }
};

watch(() => [activePreset.value.rules.excludeCompleted, activePreset.value.rules.excludeDropped], ([excludeCompleted, excludeDropped]) => {
  const excluded = new Set(activePreset.value.rules.excludedLibraryStatuses);
  if (excludeCompleted) excluded.add("completed");
  else excluded.delete("completed");
  if (excludeDropped) excluded.add("dropped");
  else excluded.delete("dropped");
  activePreset.value.rules.excludedLibraryStatuses = LIBRARY_STATUS_OPTIONS
    .map((status) => status.value)
    .filter((status) => excluded.has(status));
  applyLibraryRules();
});
watch(state, persist, { deep: true });

const spin = () => {
  if (isSpinning.value) return;
  const eligible = getEligibleEntries(activePreset.value);
  const inverseWeights = activePreset.value.rules.inverseWeights;
  const selected = pickWeighted(eligible, Math.random(), inverseWeights);
  if (!selected) return;
  result.value = null;
  wheelSnapshot.value = eligible;
  isSpinning.value = true;
  const landingAngle = wheelSegmentLanding(selected, eligible, inverseWeights, Math.random());
  const normalized = ((wheelRotation.value % 360) + 360) % 360;
  const target = (360 - landingAngle) % 360;
  normalizeSpinSettings();
  const delta = ((target - normalized + 360) % 360) + 360 * spinTurns.value;
  wheelRotation.value += delta;
  const visualTurns = Math.max(1, Math.min(8, Math.round((delta / 360) * .35)));
  wheelContentRotation.value = -wheelRotation.value + visualTurns * 360;
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const animationDuration = reducedMotion ? 500 : activePreset.value.rules.spinDurationSeconds * 1000;
  const spinDuration = animationDuration + 50;
  spinTimer = setTimeout(() => {
    if (activePreset.value.rules.eliminateWinner) {
      const entry = activePreset.value.entries.find((item) => item.anime.id === selected.anime.id);
      if (entry) entry.eliminated = true;
    }
    isSpinning.value = false;
    wheelRotation.value = ((wheelRotation.value % 360) + 360) % 360;
    wheelContentRotation.value = -wheelRotation.value;
    result.value = selected.anime;
    activePreset.value.history.unshift({ id: createId(), anime: compactAnime(selected.anime), createdAt: new Date().toISOString() });
    activePreset.value.history = activePreset.value.history.slice(0, 50);
  }, spinDuration);
};

const watchResult = () => {
  if (result.value) void router.push(`/anime/${result.value.slug || result.value.id}/watch`);
};
const excludeResult = () => {
  if (!result.value) return;
  const entry = activePreset.value.entries.find((item) => item.anime.id === result.value?.id);
  if (entry) entry.disabled = true;
  result.value = null;
  invalidateWheel();
};
const restoreResult = () => {
  if (!resultEntry.value) return;
  resultEntry.value.eliminated = false;
  resultEntry.value.disabled = false;
  invalidateWheel();
};
const clearHistory = () => { activePreset.value.history = []; };
const formatHistoryDate = (value: string): string => new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
const libraryStatusTitle = (status: LibraryStatus): string =>
  LIBRARY_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status;
const libraryStatusLabel = (status?: string): string => ({ completed: "просмотрено", dropped: "брошено", planned: "запланировано", started: "смотрю", on_hold: "отложено" }[status || ""] || "по правилу коллекции");

const onKeydown = (event: KeyboardEvent) => {
  const target = event.target as HTMLElement | null;
  if (event.code !== "Space" || target?.matches("input, textarea, select, button")) return;
  event.preventDefault();
  spin();
};

onMounted(async () => {
  const saved = parseRouletteState(localStorage.getItem(storageKey.value));
  if (saved) {
    for (const preset of saved.presets) {
      preset.entries = preset.entries.map((entry) => ({ ...entry, anime: compactAnime(entry.anime) }));
      preset.history = preset.history.map((item) => ({ ...item, anime: compactAnime(item.anime) }));
    }
    state.value = saved;
  }
  else await seedPreset();
  initialized.value = true;
  if (authStore.isAuthenticated) await loadLibraryCollection();
  window.addEventListener("keydown", onKeydown);
});

onBeforeUnmount(() => {
  clearTimeout(searchTimer);
  clearTimeout(spinTimer);
  searchController?.abort();
  window.removeEventListener("keydown", onKeydown);
});
</script>

<style scoped>
.roulette-page {
  /* Цвета наследуются от активной темы сайта. */
  width: min(1420px, 100%);
  margin: 0 auto;
  padding: 26px clamp(16px, 3vw, 42px) 72px;
  color: var(--text-primary);
}

button, input, select { font: inherit; }
button { color: inherit; }

.roulette-hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 30px;
  margin-bottom: 16px;
  padding: 24px 28px;
  overflow: hidden;
  border: 1px solid var(--border-default);
  border-radius: 22px;
  background:
    radial-gradient(circle at 88% 5%, rgba(var(--accent-rgb), .16), transparent 31%),
    linear-gradient(135deg, color-mix(in srgb, var(--surface-3) 96%, var(--accent) 4%), var(--surface-2));
  box-shadow: var(--shadow-md);
}

.roulette-hero::after {
  content: "";
  position: absolute;
  width: 220px;
  height: 220px;
  right: -72px;
  top: -110px;
  border: 1px solid rgba(var(--accent-rgb), .18);
  border-radius: 50%;
  box-shadow: 0 0 0 28px rgba(var(--accent-rgb), .025), 0 0 0 58px rgba(var(--accent-rgb), .018);
}

.hero-copy { position: relative; z-index: 1; }
.eyebrow, .section-kicker {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 7px;
  color: var(--accent-bright);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.hero-copy h1 { margin: 0; font-family: var(--font-display); font-size: clamp(30px, 3.5vw, 43px); line-height: 1.08; letter-spacing: -.035em; }
.hero-copy p { margin-top: 8px; color: var(--text-secondary); font-size: 13px; }
.hero-stats { position: relative; z-index: 1; display: flex; gap: 8px; }
.hero-stats div { min-width: 88px; padding: 12px 14px; border: 1px solid var(--border-default); border-radius: 13px; background: rgba(25, 16, 35, .78); text-align: center; backdrop-filter: blur(10px); }
.hero-stats strong { display: block; color: var(--accent-bright); font-family: var(--font-display); font-size: 21px; line-height: 1; }
.hero-stats span { display: block; margin-top: 5px; color: var(--text-tertiary); font-size: 10px; text-transform: uppercase; letter-spacing: .08em; }

.preset-strip { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
.preset-scroll { display: flex; flex: 1; gap: 8px; min-width: 0; overflow-x: auto; scrollbar-width: none; }
.preset-scroll::-webkit-scrollbar { display: none; }
.preset-chip, .new-preset-btn { display: inline-flex; align-items: center; gap: 8px; min-height: 38px; padding: 0 14px; border: 1px solid var(--border-default); border-radius: 12px; background: var(--surface-2); color: var(--text-secondary); cursor: pointer; white-space: nowrap; transition: .18s ease; }
.preset-chip:hover, .new-preset-btn:hover { border-color: var(--border-strong); background: var(--surface-3); }
.preset-chip.active { border-color: rgba(var(--accent-rgb), .45); background: var(--accent-subtle); color: var(--text-primary); box-shadow: inset 0 0 0 1px rgba(var(--accent-rgb), .08); }
.preset-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-disabled); }
.preset-chip.active .preset-dot { background: var(--accent); box-shadow: 0 0 8px rgba(var(--accent-rgb), .45); }
.preset-chip small { min-width: 20px; padding: 2px 5px; border-radius: 999px; background: var(--surface-4); color: var(--text-tertiary); font-size: 10px; text-align: center; }
.new-preset-btn { flex: 0 0 auto; color: var(--accent-bright); }

.roulette-layout {
  display: grid;
  grid-template-columns: minmax(410px, .9fr) minmax(500px, 1.1fr);
  gap: 18px;
  align-items: start;
  max-height: 80vh;
  overflow: hidden;
}
.panel-card { border: 1px solid color-mix(in srgb, var(--border-default) 82%, white 18%); border-radius: 20px; background: linear-gradient(155deg, color-mix(in srgb, var(--accent) 97%, white 3%), var(--surface-2)); box-shadow: 0 18px 55px rgba(9, 4, 17, .22), inset 0 1px 0 rgba(255,255,255,.025); }
.wheel-card, .setup-card { min-height: 700px; padding: 22px; }
.wheel-card { position: sticky; top: calc(var(--navbar-height, 58px) + 14px); }
.card-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.card-heading h2 { margin: 0; font-family: var(--font-display); font-size: 22px; letter-spacing: -.02em; }
.section-kicker { margin-bottom: 4px; color: var(--text-tertiary); font-size: 9px; }
.ready-pill { padding: 7px 10px; border-radius: 999px; background: var(--success-subtle); color: var(--success); font-size: 11px; }
.ready-pill.empty { background: var(--warning-subtle); color: var(--warning); }

.mode-bar { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 16px; }
.mode-button { display: grid; grid-template-columns: 34px minmax(0,1fr) 29px; align-items: center; gap: 9px; min-height: 56px; padding: 8px 10px; border: 1px solid var(--border-default); border-radius: 13px; background: var(--surface-1); text-align: left; cursor: pointer; transition: border-color .18s ease, background .18s ease, transform .18s ease; }
.mode-button:hover { transform: translateY(-1px); border-color: var(--border-strong); background: var(--surface-3); }
.mode-button.active { border-color: color-mix(in srgb, var(--accent) 44%, transparent); background: color-mix(in srgb, var(--accent-subtle) 70%, var(--surface-1)); }
.mode-icon { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: var(--surface-4); color: var(--text-tertiary); }
.mode-button.active .mode-icon { background: var(--accent-subtle); color: var(--accent-bright); }
.mode-button strong, .mode-button small { display: block; }
.mode-button strong { color: var(--text-primary); font-size: 11px; }
.mode-button small { margin-top: 3px; overflow: hidden; color: var(--text-tertiary); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.mode-switch { position: relative; width: 29px; height: 17px; border-radius: 999px; background: var(--surface-5); box-shadow: inset 0 0 0 1px var(--border-default); transition: background .18s ease; }
.mode-switch i { position: absolute; left: 3px; top: 3px; width: 11px; height: 11px; border-radius: 50%; background: var(--text-tertiary); transition: transform .2s var(--ease-spring), background .18s ease; }
.mode-button.active .mode-switch { background: var(--accent); }
.mode-button.active .mode-switch i { transform: translateX(12px); background: #fff7fc; }

.wheel-stage { --wheel-size: min(370px, 76vw); --label-radius: calc(var(--wheel-size) * .34); position: relative; width: var(--wheel-size); height: var(--wheel-size); margin: 24px auto 16px; filter: drop-shadow(0 20px 30px rgba(8, 4, 15, .34)); }
.wheel { position: relative; width: 100%; height: 100%; overflow: hidden; border: 7px solid color-mix(in srgb, var(--surface-5) 88%, white 12%); border-radius: 50%; transition: transform 3.65s cubic-bezier(.12,.7,.08,1); box-shadow: inset 0 0 0 2px rgba(255,255,255,.18), inset 0 0 38px rgba(0,0,0,.2), 0 0 0 1px var(--border-strong), 0 0 0 7px rgba(var(--accent-rgb), .035); }
.wheel::after { content: ""; position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, transparent 0 43%, rgba(255,255,255,.08) 44%, transparent 46%), linear-gradient(120deg, rgba(255,255,255,.18), transparent 30%); pointer-events: none; }
.wheel-rim { position: absolute; inset: 10px; z-index: 1; border: 1px solid rgba(255,255,255,.18); border-radius: 50%; }
.wheel-pointer { position: absolute; z-index: 5; top: -9px; left: 50%; width: 40px; height: 48px; transform: translateX(-50%); filter: drop-shadow(0 5px 5px rgba(0,0,0,.45)); }
.wheel-pointer::before { content: ""; position: absolute; left: 6px; top: 0; width: 28px; height: 32px; border-radius: 8px 8px 16px 16px; background: var(--accent-bright); clip-path: polygon(0 0,100% 0,50% 100%); }
.wheel-pointer span { position: absolute; z-index: 1; left: 16px; top: 5px; width: 8px; height: 8px; border-radius: 50%; background: #fff7fc; }
.wheel-hub { position: absolute; z-index: 4; left: 50%; top: 50%; display: grid; place-items: center; width: 70px; height: 70px; transform: translate(-50%,-50%); border: 6px solid var(--surface-4); border-radius: 50%; background: radial-gradient(circle at 35% 30%, var(--surface-4), var(--surface-1)); color: var(--accent-bright); box-shadow: 0 6px 22px rgba(8, 4, 15, .52), inset 0 0 0 1px var(--border-strong); }
.wheel-label { position: absolute; z-index: 2; left: 50%; top: 50%; width: 1px; height: 1px; transform: rotate(var(--label-angle)) translateY(calc(-1 * var(--label-radius))) rotate(var(--label-angle-inverse)); }
.wheel-label span { display: -webkit-box; width: clamp(68px, calc(var(--wheel-size) * .25), 102px); padding: 2px 4px; transform: translate(-50%,-50%); overflow: hidden; color: #fff7fc; font-size: 9px; font-weight: 800; line-height: 1.16; text-align: center; text-shadow: 0 1px 3px rgba(20, 8, 27, .95), 0 0 10px rgba(20, 8, 27, .5); overflow-wrap: anywhere; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.spin-status, .wheel-hint { min-height: 34px; margin: 0 auto 13px; color: var(--text-tertiary); font-size: 11px; line-height: 1.45; text-align: center; }
.spin-status { color: var(--accent-bright); font-weight: 700; }
.spin-button { display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; min-height: 52px; border: 0; border-radius: 13px; background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 90%, white), color-mix(in srgb, var(--accent) 66%, #9b70d8)); color: var(--text-on-accent); font-weight: 850; cursor: pointer; box-shadow: 0 10px 28px rgba(var(--accent-rgb), .2); transition: transform .18s ease, filter .18s ease; }
.spin-button:not(:disabled):hover { transform: translateY(-2px); filter: brightness(1.07); }
.spin-button:disabled { opacity: .45; cursor: not-allowed; box-shadow: none; }
.spin-button-icon { display: grid; place-items: center; }
.spin-button kbd { position: absolute; margin-left: min(32vw, 350px); padding: 3px 7px; border: 1px solid rgba(42, 18, 39, .2); border-radius: 6px; background: rgba(255,247,252,.24); color: var(--text-on-accent); font-size: 9px; }

.result-card { display: grid; grid-template-columns: 46px minmax(0,1fr) auto; align-items: center; gap: 11px; min-height: 64px; margin: 0 0 13px; padding: 8px 9px; border: 1px solid rgba(var(--accent-rgb), .3); border-radius: 13px; background: linear-gradient(110deg, var(--accent-subtle), var(--surface-3)); animation: result-in .3s var(--ease-spring); }
@keyframes result-in { from { opacity: 0; transform: translateY(8px) scale(.98); } }
.result-poster { width: 46px; height: 54px; border-radius: 8px; object-fit: cover; }
.result-copy { min-width: 0; }
.result-label { color: var(--accent-bright); font-size: 11px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
.result-copy h3 { overflow: hidden; margin: 2px 0; color: var(--text-primary); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.result-copy p { color: var(--text-tertiary); font-size: 10px; }
.result-actions { display: flex; gap: 6px; }
.primary-action, .secondary-action, .icon-action { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 34px; border: 1px solid var(--border-default); border-radius: 9px; cursor: pointer; }
.primary-action { padding: 0 10px; border-color: var(--accent); background: var(--accent); color: var(--text-on-accent); font-size: 11px; font-weight: 800; }
.icon-action { width: 34px; background: var(--surface-4); }
.secondary-action { padding: 0 9px; background: var(--surface-4); color: var(--text-secondary); font-size: 10px; font-weight: 750; }

.setup-card { padding-bottom: 18px; }
.setup-heading { margin-bottom: 14px; }
.preset-name-input { width: min(330px, 48vw); padding: 0; border: 0; border-bottom: 1px solid transparent; outline: 0; background: transparent; color: var(--text-primary); font-family: var(--font-display); font-size: 22px; font-weight: 700; }
.preset-name-input:focus { border-bottom-color: var(--accent); }
.preset-actions { display: flex; gap: 5px; }
.preset-actions button, .visibility-btn, .remove-entry-btn, .participation-btn { display: grid; place-items: center; width: 34px; height: 34px; min-width: 34px; min-height: 34px; border: 1px solid var(--border-default); border-radius: 9px; background: var(--surface-3); cursor: pointer; }
.preset-actions button:hover, .visibility-btn:hover { background: var(--surface-4); border-color: var(--border-strong); }
.preset-actions button:disabled { opacity: .3; cursor: default; }
.source-tabs { display: grid; grid-template-columns: repeat(3,1fr); gap: 5px; padding: 4px; border: 1px solid var(--border-subtle); border-radius: 12px; background: var(--surface-1); }
.source-tabs button { display: flex; align-items: center; justify-content: center; gap: 7px; min-height: 38px; border: 0; border-radius: 9px; background: transparent; color: var(--text-tertiary); font-size: 11px; cursor: pointer; }
.source-tabs button.active { background: var(--surface-4); color: var(--accent-bright); box-shadow: var(--shadow-sm); }
.source-panel { min-height: 132px; margin-top: 10px; }
.anime-search { display: flex; align-items: center; gap: 8px; height: 42px; padding: 0 12px; border: 1px solid var(--border-default); border-radius: 11px; background: var(--surface-1); color: var(--text-tertiary); }
.anime-search:focus-within { border-color: var(--border-strong); box-shadow: var(--border-glow); }
.anime-search input { flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--text-primary); font-size: 12px; }
.anime-search button { border: 0; background: none; color: var(--text-tertiary); font-size: 19px; cursor: pointer; }
.search-spinner { animation: rotate 1s linear infinite; }
@keyframes rotate { to { transform: rotate(360deg); } }
.source-tip, .source-message { padding: 24px 8px 10px; color: var(--text-tertiary); font-size: 11px; text-align: center; }
.source-message.error { color: var(--danger); }
.search-results { display: grid; gap: 5px; max-height: 210px; margin-top: 7px; overflow-y: auto; }
.search-result { display: grid; grid-template-columns: 34px minmax(0,1fr) auto; align-items: center; gap: 9px; min-height: 44px; padding: 5px 8px; border: 1px solid transparent; border-radius: 10px; background: var(--surface-1); text-align: left; cursor: pointer; }
.search-result:hover:not(:disabled) { border-color: var(--border-strong); background: var(--surface-3); }
.search-result:disabled { opacity: .55; cursor: default; }
.search-result img { width: 34px; height: 38px; border-radius: 6px; object-fit: cover; }
.result-text { min-width: 0; }
.result-text strong, .result-text small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result-text strong { font-size: 11px; }
.result-text small { margin-top: 2px; color: var(--text-tertiary); font-size: 9px; }
.add-result { color: var(--accent-bright); font-size: 10px; font-weight: 700; }
.library-panel > p { margin: 5px 2px 9px; color: var(--text-tertiary); font-size: 11px; }
.library-imports { display: grid; grid-template-columns: repeat(3,1fr); gap: 6px; }
.library-imports button { display: flex; align-items: center; gap: 7px; min-width: 0; padding: 8px; border: 1px solid var(--border-default); border-radius: 10px; background: var(--surface-1); text-align: left; cursor: pointer; }
.library-imports button:hover { background: var(--surface-3); border-color: var(--border-strong); }
.library-imports button:disabled { opacity: .5; }
.library-imports button > span:last-child { min-width: 0; }
.library-imports strong, .library-imports small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.library-imports strong { font-size: 10px; }
.library-imports small { margin-top: 2px; color: var(--text-tertiary); font-size: 11px; }
.import-icon { display: grid; place-items: center; flex: 0 0 auto; width: 28px; height: 28px; border-radius: 8px; font-weight: 900; }
.import-icon.planned { background: var(--warning-subtle); color: var(--warning); }
.import-icon.watching { background: var(--info-subtle); color: var(--info); }
.import-icon.favorite { background: var(--accent-subtle); color: var(--accent); }
.import-message { color: var(--accent-bright) !important; text-align: center; }
.login-callout { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 12px; min-height: 100px; padding: 15px; border: 1px dashed var(--border-strong); border-radius: 12px; background: var(--surface-1); }
.login-callout strong { font-size: 12px; }
.login-callout p { margin-top: 3px; color: var(--text-tertiary); font-size: 10px; }
.login-callout a { padding: 7px 10px; border-radius: 8px; background: var(--accent); color: var(--text-on-accent); font-size: 10px; font-weight: 800; text-decoration: none; }
.rules-panel { display: grid; gap: 5px; }
.rules-note { display: flex; align-items: center; gap: 10px; min-height: 48px; padding: 8px 10px; border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent); border-radius: 10px; background: var(--accent-subtle); color: var(--accent-bright); }
.rules-note > span { min-width: 0; }
.rules-note strong, .rules-note small { display: block; }
.rules-note strong { font-size: 10px; }
.rules-note small { margin-top: 2px; color: var(--text-secondary); font-size: 11px; line-height: 1.35; }
.rule-row, .rule-select-row { display: flex; align-items: center; justify-content: space-between; gap: 14px; min-height: 42px; padding: 6px 9px; border-radius: 9px; background: var(--surface-1); }
.rule-row strong, .rule-select-row strong, .rule-row small, .rule-select-row small { display: block; }
.rule-row strong, .rule-select-row strong { font-size: 10px; }
.rule-row small, .rule-select-row small { margin-top: 2px; color: var(--text-tertiary); font-size: 11px; }
.rule-row input { width: 34px; height: 19px; accent-color: var(--accent); }
.rule-select-row select { height: 29px; padding: 0 7px; border: 1px solid var(--border-default); border-radius: 7px; background: var(--surface-3); color: var(--text-primary); font-size: 10px; }
.sync-button, .reset-round-button { justify-self: start; display: flex; align-items: center; gap: 6px; margin-top: 3px; padding: 7px 10px; border: 1px solid var(--border-default); border-radius: 8px; background: var(--surface-3); color: var(--text-secondary); font-size: 9px; cursor: pointer; }
.reset-round-button { border-color: color-mix(in srgb, var(--accent) 25%, transparent); color: var(--accent-bright); }

.entries-toolbar { display: flex; align-items: center; justify-content: space-between; margin: 14px 0 7px; }
.entries-toolbar > div { display: flex; align-items: center; gap: 7px; font-size: 12px; }
.entries-toolbar span { padding: 2px 6px; border-radius: 999px; background: var(--surface-4); color: var(--text-tertiary); font-size: 9px; }
.entries-toolbar small { color: var(--text-tertiary); font-size: 11px; font-weight: 500; }
.entries-toolbar button, .history-heading button { border: 0; background: none; color: var(--accent-bright); font-size: 9px; cursor: pointer; }
.toolbar-actions { justify-content: flex-end; }
.entries-toolbar button:disabled { opacity: .35; }
.entries-list { display: grid; gap: 5px; max-height: 358px; padding-right: 3px; overflow-y: auto; scrollbar-color: var(--surface-5) transparent; }
.entry-row { position: relative; display: grid; grid-template-columns: 4px 42px minmax(0,1fr) 104px 34px 26px; align-items: center; gap: 9px; min-height: 64px; padding: 6px 7px 6px 0; overflow: hidden; border: 1px solid var(--border-subtle); border-radius: 11px; background: color-mix(in srgb, var(--surface-1) 88%, white 1%); transition: opacity .18s ease, border-color .18s ease, background .18s ease; }
.entry-row:hover { border-color: var(--border-default); background: var(--surface-3); }
.entry-row.excluded, .entry-row.recent { opacity: .56; }
.entry-row.eliminated { border-style: dashed; }
.entry-color { align-self: stretch; border-radius: 0 4px 4px 0; }
.entry-poster { width: 42px; height: 50px; border-radius: 8px; object-fit: cover; }
.entry-poster.placeholder { display: grid; place-items: center; background: var(--surface-4); color: var(--accent-bright); font-weight: 900; }
.entry-info { min-width: 0; }
.entry-info strong, .entry-info span { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.entry-info strong { color: var(--text-primary); font-size: 11px; }
.entry-info span { margin-top: 4px; color: var(--text-tertiary); font-size: 8.5px; }
.weight-control { display: grid; grid-template-columns: 29px 44px 29px; height: 32px; overflow: hidden; border: 1px solid var(--border-default); border-radius: 9px; }
.weight-control button, .weight-control input { min-width: 0; border: 0; background: var(--surface-3); color: var(--text-primary); text-align: center; }
.weight-control button { cursor: pointer; }
.weight-control button:hover { background: var(--surface-4); }
.weight-control input { border-inline: 1px solid var(--border-default); font-size: 9px; appearance: textfield; }
.weight-control input::-webkit-inner-spin-button { appearance: none; }
.visibility-btn { width: 30px; height: 30px; }
.remove-entry-btn { width: 24px; height: 30px; border: 0; background: transparent; color: var(--text-tertiary); font-size: 18px; }
.remove-entry-btn:hover { color: var(--danger); }
.empty-entries { display: grid; place-items: center; min-height: 220px; padding: 25px; border: 1px dashed var(--border-default); border-radius: 13px; color: var(--text-tertiary); text-align: center; }
.empty-entries div { display: grid; place-items: center; width: 58px; height: 58px; margin-bottom: 9px; border-radius: 50%; background: var(--accent-subtle); color: var(--accent-bright); }
.empty-entries strong { color: var(--text-secondary); font-size: 12px; }
.empty-entries p { max-width: 280px; margin-top: 4px; font-size: 10px; }

.history-card { margin-top: 18px; padding: 20px 22px; }
.history-list { display: grid; grid-template-columns: repeat(4,1fr); gap: 7px; margin-top: 13px; }
.history-list article { display: grid; grid-template-columns: 24px 34px minmax(0,1fr) auto; align-items: center; gap: 7px; min-width: 0; padding: 7px; border: 1px solid var(--border-subtle); border-radius: 10px; background: var(--surface-1); }
.history-index { color: var(--text-disabled); font-family: var(--font-mono); font-size: 9px; }
.history-list img { width: 34px; height: 39px; border-radius: 6px; object-fit: cover; }
.history-list div { min-width: 0; }
.history-list strong, .history-list small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.history-list strong { font-size: 9px; }
.history-list small { margin-top: 3px; color: var(--text-tertiary); font-size: 11px; }
.history-list a { color: var(--accent-bright); font-size: 11px; text-decoration: none; }
.empty-history { margin-top: 12px; padding: 20px; border: 1px dashed var(--border-default); border-radius: 11px; color: var(--text-tertiary); font-size: 10px; text-align: center; }

@media (max-width: 1180px) {
  .roulette-layout { grid-template-columns: minmax(360px,.85fr) minmax(430px,1.15fr); }
  .wheel-stage { --wheel-size: min(350px, 76vw); }
  .history-list { grid-template-columns: repeat(2,1fr); }
}

@media (max-width: 940px) {
  .roulette-layout { grid-template-columns: 1fr; }
  .wheel-card { position: static; }
  .wheel-card, .setup-card { min-height: 0; }
  .wheel-stage { --wheel-size: min(420px, 82vw); }
  .entries-list { max-height: 440px; }
}

@media (max-width: 640px) {
  .roulette-page { padding: 16px 11px 42px; }
  .roulette-hero { align-items: flex-start; flex-direction: column; padding: 20px; }
  .hero-stats { width: 100%; }
  .hero-stats div { flex: 1; min-width: 0; padding: 9px 5px; }
  .hero-stats strong { font-size: 18px; }
  .preset-strip { align-items: stretch; flex-direction: column; }
  .new-preset-btn { justify-content: center; }
  .wheel-card, .setup-card { padding: 15px; border-radius: 17px; }
  .mode-bar { gap: 6px; margin-top: 13px; }
  .mode-button { grid-template-columns: 30px minmax(0,1fr) 26px; gap: 7px; min-height: 53px; padding: 7px 8px; }
  .mode-icon { width: 30px; height: 30px; }
  .mode-button strong { font-size: 9.5px; }
  .mode-button small { font-size: 7.5px; }
  .mode-switch { width: 26px; height: 16px; }
  .mode-switch i { width: 10px; height: 10px; }
  .mode-button.active .mode-switch i { transform: translateX(10px); }
  .wheel-stage { --wheel-size: min(350px, 84vw); }
  .wheel-label span { font-size: 11px; }
  .spin-button kbd { display: none; }
  .result-card { grid-template-columns: 38px minmax(0,1fr); }
  .result-actions { grid-column: 1 / -1; }
  .result-actions .primary-action, .result-actions .secondary-action { flex: 1; }
  .preset-name-input { width: 56vw; font-size: 18px; }
  .source-tabs button { font-size: 9px; }
  .library-imports { grid-template-columns: 1fr; }
  .entries-toolbar small { display: none; }
  .entry-row { grid-template-columns: 4px 38px minmax(0,1fr) 82px 27px 22px; gap: 5px; min-height: 58px; }
  .entry-poster { width: 38px; height: 46px; }
  .visibility-btn { display: grid; width: 27px; }
  .remove-entry-btn { width: 22px; }
  .weight-control { grid-template-columns: 23px 36px 23px; }
  .history-list { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .wheel { transition-duration: .5s; }
  .result-card { animation: none; }
}
</style>
<style src="./roulette-redesign.css"></style>
