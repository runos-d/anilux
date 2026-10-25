<template>
  <div class="cal">
    <!-- ══ Шапка ═══════════════════════════════════════════════ -->
    <header class="cal-header">
      <div class="cal-header-info">
        <div class="cal-eyebrow">
          <SakuraIcon name="calendar" :size="15" />
          <span>Расписание</span>
        </div>
        <p v-if="data" class="cal-sub">
          <span class="cal-sub-month">{{ monthNameRu }} {{ year }}</span>
        </p>
      </div>

      <div class="cal-header-actions">
        <div class="cal-search" :class="{ 'is-active': isSearching }">
          <SakuraIcon name="search" :size="13" />
          <input
            v-model="searchQuery"
            type="text"
            autocomplete="off"
            placeholder="Поиск по расписанию..."
            aria-label="Поиск по календарю"
          />
          <button
            v-if="searchQuery"
            class="cal-search-clear"
            type="button"
            aria-label="Очистить поиск"
            @click="clearSearch"
          >
            <SakuraIcon name="close" :size="11" />
          </button>
        </div>
        <button
          v-if="!loading && !error && data && !isSearching"
          class="cal-icon-btn"
          type="button"
          title="Обновить календарь"
          @click="$emit('refresh')"
        >
          <SakuraIcon name="refresh" :size="14" />
        </button>
      </div>
    </header>

    <!-- ══ Поиск ═══════════════════════════════════════════════ -->
    <div v-if="isSearching" class="cal-search-results">
      <div v-if="searchLoading" class="cal-loading" aria-label="Поиск">
        <div class="cal-skel cal-skel-search-card"></div>
        <div v-for="i in 4" :key="i" class="cal-skel cal-skel-search-card"></div>
      </div>

      <div v-else-if="searchError" class="cal-state">
        <div class="cal-state-icon">
          <SakuraIcon name="ban" :size="22" />
        </div>
        <div>
          <p class="cal-state-title">Не удалось выполнить поиск</p>
          <p class="cal-state-sub">{{ searchError }}</p>
          <button class="cal-retry" type="button" @click="runSearch(false)">
            <SakuraIcon name="refresh" :size="13" />
            Попробовать снова
          </button>
        </div>
      </div>

      <div v-else-if="!searchDays.length" class="cal-state">
        <div class="cal-state-icon">
          <SakuraIcon name="moon" :size="22" />
        </div>
        <div>
          <p class="cal-state-title">Ничего не найдено</p>
          <!-- <p class="cal-state-sub">
            По запросу «{{ searchQuery }}» релизов в расписании пока нет.
          </p> -->
          <button class="cal-retry" type="button" @click="clearSearch">
            Очистить поиск
          </button>
        </div>
      </div>

      <template v-else>
        <p class="cal-search-summary">Найдено релизов: {{ searchTotal }}</p>
        <div v-for="day in searchDays" :key="day.date" class="cal-day-group">
          <h4 class="cal-day-group-title">
            <span class="cal-day-group-date">
              <span class="cal-day-group-dow">{{ day.weekday_name }}</span>
              <span class="cal-day-group-day">
                {{ dayNumber(day.date) }} {{ MONTHS_GEN[parseDay(day.date).getMonth()] }}
                {{ parseDay(day.date).getFullYear() }}
              </span>
            </span>
            <span class="cal-day-group-count">{{ day.items.length }}</span>
          </h4>
          <div class="cal-day-items">
            <CalendarReleaseCard
              v-for="(item, ii) in day.items"
              :key="ii"
              :item="item"
              @click="goToAnime(item.anime)"
            />
          </div>
        </div>
      </template>
    </div>

    <!-- ══ Основной контент ═════════════════════════════════════ -->
    <template v-else>
      <div v-if="loading" class="cal-loading" aria-label="Загрузка календаря">
        <div class="cal-skel-row">
          <div class="cal-skel cal-skel-pill"></div>
          <div class="cal-skel cal-skel-pill"></div>
        </div>
        <div class="cal-strip">
          <div v-for="i in 7" :key="i" class="cal-skel cal-skel-strip"></div>
        </div>
        <div class="cal-skel cal-skel-panel"></div>
        <div class="cal-skel cal-skel-search-card"></div>
      </div>

      <div v-else-if="error" class="cal-state">
        <div class="cal-state-icon">
          <SakuraIcon name="ban" :size="22" />
        </div>
        <div>
          <p class="cal-state-title">Не удалось загрузить календарь</p>
          <p class="cal-state-sub">{{ error }}</p>
          <button class="cal-retry" type="button" @click="$emit('refresh')">
            <SakuraIcon name="refresh" :size="13" />
            Попробовать снова
          </button>
        </div>
      </div>

      <template v-else>
        <!-- Панель управления -->
        <div class="cal-toolbar">
          <nav class="cal-nav" aria-label="Навигация расписания">
            <button
              class="cal-nav-btn"
              type="button"
              title="Назад"
              aria-label="Назад"
              @click="goBack"
            >
              <SakuraIcon name="arrow-left" :size="17" />
            </button>

            <div class="cal-nav-center">
              <div class="cal-nav-label">
                <strong>{{ viewMode === "week" ? weekRangeLabel : monthNameRu }}</strong>
                <span>{{ viewMode === "week" ? weekYear : year }}</span>
              </div>
              <!-- <button class="cal-today-btn" type="button" @click="goToday">
                <span class="cal-today-dot"></span>
                Сегодня
              </button> -->
            </div>

            <button
              class="cal-nav-btn"
              type="button"
              title="Вперёд"
              aria-label="Вперёд"
              @click="goNext"
            >
              <SakuraIcon name="arrow-right" :size="17" />
            </button>

            <div class="cal-view-toggle" role="tablist" aria-label="Вид расписания">
              <button
                type="button"
                class="cal-view-btn"
                :class="{ active: viewMode === 'week' }"
                title="Неделя"
                aria-label="Неделя"
                @click="viewMode = 'week'"
              >
                <SakuraIcon name="list" :size="14" />
              </button>
              <button
                type="button"
                class="cal-view-btn"
                :class="{ active: viewMode === 'month' }"
                title="Месяц"
                aria-label="Месяц"
                @click="viewMode = 'month'"
              >
                <SakuraIcon name="calendar" :size="14" />
              </button>
            </div>
          </nav>

          <div class="cal-filters" role="toolbar" aria-label="Фильтры расписания">
            <button
              v-for="f in filterChips"
              :key="f.key"
              type="button"
              class="cal-chip"
              :class="['cal-chip-' + f.key, { active: activeFilter === f.key }]"
              @click="toggleFilter(f.key)"
              :title="'Показать только: ' + f.label"
            >
              <span v-if="f.icon" class="cal-chip-icon">
                <SakuraIcon :name="f.icon" :size="10" />
              </span>
              <span>{{ f.label }}</span>
              <span v-if="f.key !== 'all'" class="cal-chip-count">{{ chipCount(f.key) }}</span>
            </button>
          </div>
        </div>

        <!-- === ВИД: НЕДЕЛЯ === -->
        <template v-if="viewMode === 'week'">
          <div class="cal-strip-wrap">
            <div class="cal-strip">
              <button
                v-for="d in weekDays"
                :key="d.date"
                type="button"
                class="cal-strip-cell"
                :class="{ 'is-active': d.isActive, 'is-today': d.isToday }"
                :title="dayTitle(d.day)"
                @click="selectStripDay(d.date)"
              >
                <span class="sc-dow">{{ d.dow }}</span>
                <span class="sc-num">{{ d.num }}</span>
                <div v-if="d.count" class="sc-posters">
                  <img
                    v-for="(p, pi) in d.posters"
                    :key="pi"
                    :src="p.anime.poster_url"
                    :alt="p.anime.title_ru"
                    class="sc-poster"
                    loading="lazy"
                  />
                </div>
                <span v-if="d.count" class="sc-count">{{ d.count }}</span>
              </button>
            </div>
          </div>

          <section v-if="selectedDay" class="cal-panel">
            <div class="cal-panel-head">
              <div>
                <span class="cal-panel-eyebrow">
                  {{ selectedDay.is_today ? "Сегодня" : "Расписание на день" }}
                </span>
                <h3 class="cal-panel-title">{{ dayTitleFull(selectedDay) }}</h3>
              </div>
              <span
                v-if="selectedDay.is_today"
                class="cal-panel-today"
              >
                <span class="cal-detail-dot"></span>
                Сегодня
              </span>
              <span v-else class="cal-panel-count">
                {{ filteredItems(selectedDay).length }}
              </span>
            </div>

            <div v-if="filteredItems(selectedDay).length" class="cal-rows">
              <CalendarReleaseCard
                v-for="(item, ii) in filteredItems(selectedDay)"
                :key="ii"
                :item="item"
                @click="goToAnime(item.anime)"
              />
            </div>
            <div v-else class="cal-empty">
              <SakuraIcon name="moon" :size="16" />
              В этот день ничего не выходит
            </div>
          </section>
        </template>

        <!-- === ВИД: МЕСЯЦ === -->
        <template v-else>
          <div class="cal-month-panel">
            <div class="cal-weekdays">
              <span v-for="(w, wi) in weekdays" :key="wi">{{ w }}</span>
            </div>
            <div class="cal-grid">
              <button
                v-for="day in days"
                :key="day.date"
                type="button"
                class="cal-cell"
                :class="{
                  'is-muted': !day.in_month,
                  'is-today': day.is_today,
                  'is-active': day.date === selectedDate,
                  'has-items': filteredItems(day).length > 0,
                }"
                :title="dayTitle(day)"
                @click="selectDay(day.date)"
              >
                <span class="cal-cell-num">{{ dayNumber(day.date) }}</span>
                <span v-if="filteredItems(day).length" class="cal-cell-count">
                  {{ filteredItems(day).length }}
                </span>
              </button>
            </div>
          </div>

          <section v-if="selectedDay" class="cal-panel">
            <div class="cal-panel-head">
              <div>
                <span class="cal-panel-eyebrow">
                  {{ selectedDay.is_today ? "Сегодня" : "Расписание на день" }}
                </span>
                <h3 class="cal-panel-title">{{ dayTitleFull(selectedDay) }}</h3>
              </div>
              <span
                v-if="selectedDay.is_today"
                class="cal-panel-today"
              >
                <span class="cal-detail-dot"></span>
                Сегодня
              </span>
              <span v-else class="cal-panel-count">
                {{ filteredItems(selectedDay).length }}
              </span>
            </div>

            <div v-if="filteredItems(selectedDay).length" class="cal-rows">
              <CalendarReleaseCard
                v-for="(item, ii) in filteredItems(selectedDay)"
                :key="ii"
                :item="item"
                @click="goToAnime(item.anime)"
              />
            </div>
            <div v-else class="cal-empty">
              <SakuraIcon name="moon" :size="16" />
              В этот день ничего не выходит
            </div>
          </section>
        </template>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import animeApi from "@/api/anime";
import type { CalendarData, CalendarDay, CalendarItem } from "@/api/anime";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import CalendarReleaseCard from "./CalendarReleaseCard.vue";
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notifications';

interface Props {
  data: CalendarData | null;
  loading: boolean;
  error: string | null;
}
const props = defineProps<Props>();
const auth = useAuthStore();
const notificationStore = useNotificationStore();
watch(() => auth.user?.id, id => { if (id) void notificationStore.fetchReminders(); }, { immediate: true });
const emit = defineEmits<{ refresh: []; "change-month": [month: string] }>();

const STORAGE_KEY = "anime_calendar_month";
const VIEW_KEY = "anime_calendar_view";

const searchQuery = ref("");
const searchData = ref<CalendarData | null>(null);
const searchLoading = ref(false);
const searchError = ref<string | null>(null);
const searchTimer = ref<ReturnType<typeof setTimeout> | undefined>(undefined);

const isSearching = computed(() => searchQuery.value.trim().length >= 2);
const searchDays = computed(() => searchData.value?.days || []);
const searchTotal = computed(() => searchData.value?.total || 0);

const runSearch = async (immediate = false) => {
  const q = searchQuery.value.trim();
  if (q.length < 2) {
    searchData.value = null;
    searchError.value = null;
    return;
  }
  if (immediate && searchTimer.value) {
    clearTimeout(searchTimer.value);
    searchTimer.value = undefined;
  }
  searchLoading.value = true;
  searchError.value = null;
  try {
    searchData.value = await animeApi.getCalendar(undefined, q);
  } catch (err: unknown) {
    searchError.value =
      err instanceof Error ? err.message : "Не удалось выполнить поиск";
    searchData.value = null;
  } finally {
    searchLoading.value = false;
  }
};

watch(searchQuery, () => {
  if (searchTimer.value) clearTimeout(searchTimer.value);
  const q = searchQuery.value.trim();
  if (q.length < 2) {
    searchData.value = null;
    searchError.value = null;
    return;
  }
  searchTimer.value = setTimeout(() => runSearch(true), 300);
});

const clearSearch = () => {
  if (searchTimer.value) clearTimeout(searchTimer.value);
  searchTimer.value = undefined;
  searchQuery.value = "";
  searchData.value = null;
  searchError.value = null;
};

type FilterKey = "all" | "tv" | "movie" | "ona" | "ova" | "special" | "premiere";

interface FilterChip {
  key: FilterKey;
  label: string;
  icon?: string;
}

const filterChips: FilterChip[] = [
  { key: "all", label: "Все" },
  { key: "tv", label: "ТВ", icon: "video" },
  { key: "movie", label: "Фильмы", icon: "film" },
  { key: "ona", label: "ONA" },
  { key: "ova", label: "OVA" },
  { key: "special", label: "Спецвыпуски" },
  { key: "premiere", label: "Премьеры", icon: "sparkles" },
];

const activeFilter = ref<FilterKey>("all");
const toggleFilter = (key: FilterKey) => {
  activeFilter.value = activeFilter.value === key ? "all" : key;
};
const resetFilters = () => {
  activeFilter.value = "all";
  goToday();
};

const itemMatchesFilter = (item: CalendarItem) => {
  const f = activeFilter.value;
  if (f === "all") return true;
  if (f === "premiere") return item.is_upcoming;
  return item.anime.kind === f;
};

const filteredItems = (day: CalendarDay | null) =>
  (day?.items || []).filter(itemMatchesFilter);

const chipCount = (key: FilterKey) => {
  if (key === "all") return monthTotal.value;
  if (key === "premiere") return premiereTotal.value;
  return days.value.reduce(
    (sum, d) => sum + d.items.filter((i) => i.anime.kind === key).length,
    0,
  );
};

type ViewMode = "week" | "month";
const viewMode = ref<ViewMode>("week");
try {
  const saved = localStorage.getItem(VIEW_KEY);
  if (saved === "week" || saved === "month") viewMode.value = saved;
} catch {}

watch(viewMode, (v) => {
  try {
    localStorage.setItem(VIEW_KEY, v);
  } catch {}
});

const MONTHS = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
];
const MONTHS_GEN = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];
const WEEKDAYS_FULL = [
  "Воскресенье", "Понедельник", "Вторник", "Среда",
  "Четверг", "Пятница", "Суббота",
];
const WD_SHORT = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];
const WEEKDAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const weekdays = WEEKDAYS_SHORT;
const parseDay = (d: string) => new Date(d + "T00:00:00");
const dayNumber = (d: string) => String(parseDay(d).getDate());
const toISODate = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;
const mondayOf = (dateStr: string) => {
  const d = parseDay(dateStr);
  const wd = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - wd);
  return toISODate(d);
};

const dayTitle = (day: CalendarDay) => {
  const d = parseDay(day.date);
  const releases = day.items.length ? ` · ${plural(day.items.length)}` : "";
  return `${WEEKDAYS_FULL[d.getDay()]}, ${d.getDate()} ${
    MONTHS_GEN[d.getMonth()]
  }${releases}`;
};
const dayTitleFull = (day: CalendarDay) => {
  const d = parseDay(day.date);
  return `${WEEKDAYS_FULL[d.getDay()]}, ${d.getDate()} ${
    MONTHS_GEN[d.getMonth()]
  } ${d.getFullYear()}`;
};

const shiftMonth = (key: string, delta: number): string => {
  const [yRaw, mRaw] = key.split("-");
  const y = Number(yRaw);
  const m = Number(mRaw);
  const total = y * 12 + (m - 1) + delta;
  const ny = Math.floor(total / 12);
  const nm = (total % 12) + 1;
  return `${ny}-${String(nm).padStart(2, "0")}`;
};

const days = computed(() => props.data?.days || []);
const year = computed(() => props.data?.year ?? new Date().getFullYear());
const monthNum = computed(() => props.data?.month ?? new Date().getMonth() + 1);
const monthNameRu = computed(() => MONTHS[monthNum.value - 1] ?? "");
const monthKey = computed(
  () =>
    props.data?.month_key ||
    `${year.value}-${String(monthNum.value).padStart(2, "0")}`,
);

const monthTotal = computed(
  () =>
    days.value.reduce(
      (sum, d) => (d.in_month ? sum + d.items.length : sum),
      0,
    ) || 0,
);
const premiereTotal = computed(
  () =>
    days.value.reduce(
      (sum, d) =>
        d.in_month ? sum + d.items.filter((i) => i.is_upcoming).length : sum,
      0,
    ) || 0,
);

const plural = (n: number) => pluralLabel(n, "релиз", "релиза", "релизов");
const pluralLabel = (n: number, one: string, few: string, many: string) => {
  const last = n % 10;
  if (last === 1 && n % 100 !== 11) return `${n} ${one}`;
  if ([2, 3, 4].includes(last) && ![12, 13, 14].includes(n % 100))
    return `${n} ${few}`;
  return `${n} ${many}`;
};

const selectedDateInternal = ref<string>("");
const weekStart = ref("");
const selectedDate = computed({
  get: () => {
    if (!selectedDateInternal.value && props.data?.today) {
      const today = props.data.today;
      if (days.value.some(d => d.date === today)) {
        return today;
      }
      const first = days.value.find(d => d.in_month && filteredItems(d).length > 0);
      if (first) return first.date;
      return today;
    }
    return selectedDateInternal.value;
  },
  set: (val: string) => {
    selectedDateInternal.value = val;
  }
});

const selectedDay = computed<CalendarDay | null>(
  () => dayObject(selectedDate.value),
);

const dayObject = (dateStr: string): CalendarDay | null => {
  if (!dateStr) return null;
  const found = days.value.find((d) => d.date === dateStr);
  if (found) return found;
  return {
    date: dateStr,
    weekday: 0,
    weekday_name: WEEKDAYS_FULL[parseDay(dateStr).getDay()]|| "",
    in_month: false,
    is_today: dateStr === props.data?.today,
    items: [],
  };
};

const selectDay = (date: string) => {
  selectedDate.value = date;
};

watch(
  days,
  () => {
    if (!days.value.length) {
      selectedDate.value = props.data?.month_key ? `${props.data.month_key}-01` : '';
      return;
    }
    
    const saved = selectedDate.value;
    if (saved && days.value.some((d) => d.date === saved)) {
      return;
    }

    const today = props.data?.today;
    const todayDay = today ? days.value.find((d) => d.date === today) : null;
    if (todayDay?.in_month && filteredItems(todayDay).length && today) {
      selectedDate.value = today;
      weekStart.value = mondayOf(today);
      return;
    }

    const first = days.value.find((d) => d.in_month && filteredItems(d).length);
    selectedDate.value = first ? first.date : today || days.value[0]!.date;
  },
  { immediate: true },
);

interface StripDay {
  date: string;
  day: CalendarDay;
  dow: string;
  num: number;
  isToday: boolean;
  isActive: boolean;
  count: number;
  posters: CalendarItem[];
}

const weekDays = computed<StripDay[]>(() => {
  const base = weekStart.value || mondayOf(selectedDate.value || props.data?.today || toISODate(new Date()));
  const start = parseDay(base);
  const list: StripDay[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const ds = toISODate(d);
    const day = dayObject(ds) as CalendarDay;
    const items = filteredItems(day);
    list.push({
      date: ds,
      day,
      dow: WD_SHORT[parseDay(ds).getDay()] || "",
      num: parseDay(ds).getDate(),
      isToday: ds === props.data?.today,
      isActive: ds === selectedDate.value,
      count: items.length,
      posters: items.filter((it) => it.anime.poster_url).slice(0, 2),
    });
  }
  return list;
});

const weekRangeLabel = computed(() => {
  const w = weekDays.value;
  if (!w.length) return "";
  const first = parseDay(w[0]!.date);
  const last = parseDay(w[6]!.date);
  if (first.getMonth() === last.getMonth())
    return `${w[0]!.num}–${w[6]!.num} ${MONTHS_GEN[first.getMonth()]}`;
  return `${w[0]!.num} ${MONTHS_GEN[first.getMonth()]} -${w[6]!.num} ${MONTHS_GEN[last.getMonth()]}`;
});

const weekYear = computed(() =>
  weekDays.value.length ? parseDay(weekDays.value[0]!.date).getFullYear() : year.value,
);

const shiftWeek = (delta: number) => {
  const base = weekStart.value || mondayOf(selectedDate.value || props.data?.today || toISODate(new Date()));
  const d = parseDay(base);
  d.setDate(d.getDate() + delta * 7);
  weekStart.value = toISODate(d);
  selectedDate.value = weekStart.value;
  d.setDate(d.getDate() + 3);
  const targetMonth = toISODate(d).slice(0, 7);
  if (targetMonth !== monthKey.value) emitMonth(targetMonth);
};

const selectStripDay = (date: string) => {
  selectedDate.value = date;
};

watch(selectedDate, (v) => {
  if (v && !weekDays.value.some((d) => d.date === v)) {
    weekStart.value = mondayOf(v);
  }
});

const saveMonth = (key: string) => {
  try {
    localStorage.setItem(STORAGE_KEY, key);
  } catch {}
};

const emitMonth = (key?: string | null) => {
  if (!key) return;
  saveMonth(key);
  emit("change-month", key);
};

const goBack = () => {
  if (viewMode.value === "week") shiftWeek(-1);
  else emitMonth(shiftMonth(monthKey.value, -1));
};
const goNext = () => {
  if (viewMode.value === "week") shiftWeek(1);
  else emitMonth(shiftMonth(monthKey.value, 1));
};
const goToday = () => {
  const today = props.data?.today;
  if (!today) return;
  weekStart.value = mondayOf(today);
  selectedDate.value = today;
  emitMonth(today.slice(0, 7));
};

onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (
      saved &&
      /^\d{4}-\d{2}$/.test(saved) &&
      props.data?.month_key &&
      saved !== props.data.month_key
    ) {
      emitMonth(saved);
    }
  } catch {}
    const today = props.data?.today;
  if (today) {
    const todayDay = days.value.find(d => d.date === today);
    if (todayDay) {
      selectedDate.value = today;
      weekStart.value = mondayOf(today);
    } else {
      const firstDayWithItems = days.value.find(d => d.in_month && filteredItems(d).length > 0);
      if (firstDayWithItems) {
        selectedDate.value = firstDayWithItems.date;
      } else if (days.value.length) {
        selectedDate.value = days.value[0]!.date;
      }
    }
  }
});

const router = useRouter();
const goToAnime = (anime: { id: number; slug?: string | null }) => {
  router.push(`/anime/${anime.id}${anime.slug ? `-${anime.slug}` : ""}`);
};

defineExpose({});
</script>

<style scoped>
/* ── Контейнер ─────────────────────────────────────────────── */
.cal {
  display: flex;
  min-width: 0;
  max-width: 100%;
  flex-direction: column;
  gap: var(--space-4);
}

  .cal::before {
    content: "";
    position: absolute;
    inset: -40px 0 auto;
    height: 300px;
    opacity: 0.4;
    pointer-events: none;
    z-index: 0;
  }

  .cal > * {
    position: relative;
    z-index: 1;
  }

/* ── Шапка ─────────────────────────────────────────────────── */
.cal-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.cal-header-info {
  display: flex;
  flex-direction: column;
}

.cal-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--accent);
  font-size: 15px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  margin-bottom: 2px;
}

  .cal-eyebrow :deep(.sakura-icon) {
    color: var(--accent);
  }

  .cal-title {
    margin: 0;
    font-size: clamp(1.3rem, 2vw, 1.7rem);
    font-weight: 850;
    letter-spacing: -0.03em;
    color: var(--text-primary);
  }

.cal-sub {
  margin: 3px 0 0;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.cal-sub-month {
  font-weight: 800;
  color: var(--text-secondary);
}

.cal-sub-dot {
  color: var(--border-default);
}

.cal-sub-num {
  font-weight: 800;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.cal-sub-num.is-accent {
  color: var(--accent);
}

.cal-header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.cal-icon-btn {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}

  .cal-icon-btn:hover {
    color: var(--accent);
    border-color: var(--accent);
  }

/* ── Поиск ─────────────────────────────────────────────────── */
.cal-search {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 38px;
  padding: 0 var(--space-3);
  min-width: clamp(180px, 22vw, 280px);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-tertiary);
  transition: all 0.18s var(--ease-out);
}

  .cal-search:focus-within {
    border-color: var(--accent);
    background: var(--surface-4);
  }

.cal-search :deep(.sakura-icon) {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.cal-search:focus-within :deep(.sakura-icon) {
  color: var(--accent);
}

.cal-search input {
  all: unset;
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: inherit;
}

.cal-search input::placeholder {
  color: var(--text-tertiary);
}

.cal-search-clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  min-width: 20px;
  min-height: 20px;
  flex-shrink: 0;
  border: none;
  border-radius: 50%;
  background: var(--surface-5);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s var(--ease-out);
}

.cal-search-clear:hover {
  color: white;
  background: var(--accent);
}

/* ── Панель управления ─────────────────────────────────────── */
.cal-toolbar {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
}

.cal-nav {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.cal-nav-btn {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.18s var(--ease-out);
}

  .cal-nav-btn:hover {
    color: white;
    background: var(--accent);
    border-color: var(--accent);
  }

.cal-nav-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  min-width: 0;
}

.cal-nav-label {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  min-width: 0;
}

.cal-nav-label strong {
  font-size: 1.15rem;
  font-weight: 850;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  white-space: normal;
  text-align: center;
}

.cal-nav-label span {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-tertiary);
}

.cal-today-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 32px;
  padding: 0 var(--space-3);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-weight: 700;
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all 0.18s var(--ease-out);
}

  .cal-today-btn:hover {
    color: var(--accent);
    border-color: var(--accent);
  }

  .cal-today-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent);
  }

.cal-view-toggle {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 3px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
}

.cal-view-btn {
  width: 32px;
  height: 32px;
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.18s var(--ease-out);
}

.cal-view-btn:hover {
  color: var(--text-primary);
}

  .cal-view-btn.active {
    background: var(--accent);
    color: var(--text-on-accent);
  }

/* ── Фильтры ───────────────────────────────────────────────── */
.cal-filters {
  display: flex;
  min-width: 0;
  max-width: 100%;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: nowrap;
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.cal-filters::-webkit-scrollbar {
  display: none;
}

.cal-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 var(--space-3);
  flex-shrink: 0;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s var(--ease-out);
}

.cal-chip:hover {
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border-default));
  color: var(--text-primary);
}

  .cal-chip.active {
    color: var(--text-on-accent);
    border-color: transparent;
    background: var(--accent);
  }

.cal-chip-icon {
  display: inline-flex;
}

.cal-chip-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 5px;
  background: color-mix(in srgb, var(--accent) 16%, transparent);
  border-radius: var(--radius-full);
  font-size: 9px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.cal-chip.active .cal-chip-count {
  background: color-mix(in srgb, white 24%, transparent);
}

/* ── Кинолента недели ──────────────────────────────────────── */
.cal-strip-wrap {
  min-width: 0;
  max-width: 100%;
  padding: var(--space-1);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.cal-strip {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: var(--space-2);
}

.cal-strip-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-height: 96px;
  padding: 8px 4px 10px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-family: inherit;
  color: var(--text-primary);
  overflow: hidden;
  transition: all 0.18s var(--ease-out);
}

  .cal-strip-cell:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    z-index: 2;
  }

  .cal-strip-cell.is-today {
    border-color: var(--accent);
    box-shadow: inset 0 0 0 1px var(--accent);
  }

  .cal-strip-cell.is-today .sc-num::after {
    /* content: ""; */
    position: absolute;
    top: 5px;
    right: 8px;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
  }

  .cal-strip-cell.is-active {
    color: white;
    border-color: transparent;
    background: var(--accent);
  }

.cal-strip-cell.is-active .sc-dow,
.cal-strip-cell.is-active .sc-num {
  color: white;
}

.cal-strip-cell.is-active .sc-count {
  background: color-mix(in srgb, white 26%, transparent);
  color: white;
}

.sc-dow {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
}

.sc-num {
  position: relative;
  font-size: 1.35rem;
  font-weight: 850;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
}

.sc-posters {
  position: relative;
  display: flex;
  align-items: flex-end;
  margin-top: auto;
  height: 30px;
}

.sc-poster {
  width: 20px;
  height: 28px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid color-mix(in srgb, white 30%, transparent);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  transition: transform 0.18s var(--ease-out);
}

.sc-poster + .sc-poster {
  margin-left: -10px;
}

.cal-strip-cell:hover .sc-poster:first-child {
  transform: translateX(-2px) rotate(-4deg);
}

.cal-strip-cell:hover .sc-poster:last-child {
  transform: translateX(2px) rotate(4deg);
}

.sc-count {
  position: absolute;
  bottom: 4px;
  right: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 17px;
  height: 17px;
  padding: 0 5px;
  background: color-mix(in srgb, var(--accent) 20%, var(--surface-5));
  color: var(--accent);
  border-radius: var(--radius-full);
  font-size: 9px;
  font-weight: 800;
}

/* ── Панель дня (общая) ────────────────────────────────────── */
.cal-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
}

.cal-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border-subtle);
}

.cal-panel-eyebrow {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--accent);
}

.cal-panel-title {
  margin: 2px 0 0;
  font-size: 1.1rem;
  font-weight: 850;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

  .cal-panel-count {
    min-width: 26px;
    height: 26px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 8px;
    background: var(--accent);
    color: var(--text-on-accent);
    border-radius: var(--radius-full);
    font-size: var(--text-xs);
    font-weight: 800;
    flex-shrink: 0;
  }

  .cal-panel-today {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: var(--text-xs);
    font-weight: 800;
    color: var(--accent);
    flex-shrink: 0;
  }

  .cal-detail-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent);
  }

.cal-rows {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-2);
}

.cal-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-5);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  background: var(--surface-2);
  border-radius: var(--radius-lg);
  border: 1px dashed var(--border-default);
}

.cal-empty :deep(.sakura-icon) {
  color: var(--accent);
}

/* ── Месяц ─────────────────────────────────────────────────── */
.cal-month-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: var(--space-1);
}

.cal-weekdays span {
  text-align: center;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
  padding: 6px 0;
  border-bottom: 1px solid var(--border-subtle);
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: var(--space-1);
}

.cal-cell {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  min-height: 42px;
  padding: 6px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: inherit;
  color: var(--text-primary);
  transition: all 0.15s var(--ease-out);
}

.cal-cell:hover {
  border-color: color-mix(in srgb, var(--accent) 50%, var(--border-default));
  background: var(--surface-5);
  transform: translateY(-1px);
}

.cal-cell.is-muted {
  opacity: 0.38;
}

.cal-cell.is-muted:hover {
  opacity: 0.7;
}

  .cal-cell.is-today {
    border-color: var(--accent);
    background: var(--surface-4);
    box-shadow: inset 0 0 0 1px var(--accent);
  }

  .cal-cell.is-today .cal-cell-num {
    color: var(--accent);
  }

  .cal-cell.is-active {
    border-color: var(--accent);
    box-shadow: inset 0 0 0 2px var(--accent);
    background: var(--surface-5);
    z-index: 1;
  }

  .cal-cell.is-active .cal-cell-num {
    color: var(--accent);
  }

.cal-cell-num {
  font-size: var(--text-sm);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
}

.is-muted .cal-cell-num {
  color: var(--text-tertiary);
}

.cal-cell-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 17px;
  height: 17px;
  padding: 0 5px;
  background: color-mix(in srgb, var(--accent) 20%, var(--surface-5));
  color: var(--accent);
  border-radius: var(--radius-full);
  font-size: 9px;
  font-weight: 800;
}

/* ── Состояния / поиск ─────────────────────────────────────── */
.cal-state {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--surface-3);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-xl);
  color: var(--text-tertiary);
}

  .cal-state-icon {
    width: 48px;
    height: 48px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--surface-4);
    border-radius: var(--radius-full);
    color: var(--accent);
    border: 1px solid var(--border-subtle);
  }

.cal-state-title {
  margin: 0;
  font-weight: 800;
  color: var(--text-primary);
  font-size: 1rem;
}

.cal-state-sub {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
}

  .cal-retry {
    margin-top: var(--space-2);
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    background: var(--accent);
    border: none;
    border-radius: var(--radius-full);
    color: var(--text-on-accent);
    font-weight: 700;
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all 0.18s var(--ease-out);
  }

  .cal-retry:hover {
    background: var(--accent-hover);
  }

.cal-loading {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.cal-skel-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cal-skel {
  background: var(--surface-4);
  border-radius: var(--radius-md);
  animation: cal-pulse 1.4s ease-in-out infinite;
}

.cal-skel-pill {
  height: 22px;
  width: 140px;
}
.cal-skel-strip {
  min-height: 96px;
  border-radius: var(--radius-lg);
}
.cal-skel-panel {
  height: 120px;
  border-radius: var(--radius-xl);
}
.cal-skel-search-card {
  height: 48px;
  border-radius: var(--radius-lg);
}

@keyframes cal-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* ── Группы поиска ─────────────────────────────────────────── */
.cal-search-results {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.cal-search-summary {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 700;
}

.cal-day-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.cal-day-group-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin: 0;
  padding: 6px var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 850;
  color: var(--text-primary);
}

.cal-day-group-date {
  display: inline-flex;
  align-items: baseline;
  gap: var(--space-2);
}

.cal-day-group-dow {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent);
}

.cal-day-group-day {
  font-variant-numeric: tabular-nums;
}

.cal-day-group-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 19px;
  padding: 0 6px;
  background: var(--accent-subtle);
  color: var(--accent);
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: 800;
}

.cal-day-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-2);
}

/* ── Адаптив ───────────────────────────────────────────────── */
@media (max-width: 900px) {
  .cal-strip {
    grid-template-columns: repeat(7, 92px);
    overflow-x: auto;
    padding-bottom: 4px;
    scroll-snap-type: x proximity;
    scrollbar-width: none;
  }
  .cal-strip::-webkit-scrollbar {
    display: none;
  }
  .cal-strip-cell {
    scroll-snap-align: center;
  }
}

@media (max-width: 820px) {
  .cal-header {
    flex-direction: column;
    align-items: stretch;
  }
  .cal-search {
    width: 100%;
    min-width: 0;
  }
  .cal-nav {
    flex-wrap: wrap;
    row-gap: var(--space-2);
  }
  .cal-view-toggle {
    margin-left: auto;
  }
}

@media (max-width: 600px) {
  .cal-strip-cell {
    min-height: 84px;
    padding: 6px 2px 8px;
  }
  .sc-num {
    font-size: 1.1rem;
  }
  .cal-panel {
    padding: var(--space-3);
  }
  .cal-rows {
    grid-template-columns: 1fr;
  }
  .cal-cell {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    min-height: 38px;
    padding: 5px;
  }
  .cal-state {
    padding: var(--space-4);
  }
  .cal-chip {
    padding: 0 var(--space-2);
    height: 26px;
  }
  .cal-day-items {
    grid-template-columns: 1fr;
  }
}
</style>
