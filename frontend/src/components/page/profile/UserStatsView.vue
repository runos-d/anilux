<template>
  <div class="stats-page">
    <div v-if="loading" class="stats-skel">
      <div v-for="n in 4" :key="n" class="skel-block"></div>
    </div>

    <div v-else-if="error" class="state-box">
      <span class="state-icon"><SakuraIcon name="warning"/>️</span>
      <p class="state-title">Не удалось загрузить статистику</p>
      <button class="btn btn-primary" @click="load">Повторить</button>
    </div>

    <div v-else-if="!data || data.counts.total === 0" class="state-box">
      <p class="state-title">{{ emptyStateTitle }}</p>
      <p v-if="isOwnProfile" class="state-sub">
        Добавьте аниме в «Мою коллекцию», и здесь появится ваша личная
        статистика
      </p>
      <p v-else class="state-sub">
        Когда пользователь {{ profileName }} добавит аниме в коллекцию, здесь появится статистика
      </p>
    </div>

    <template v-else>
      <section class="hero-card">
        <div class="hero-glow"></div>
        <div class="hero-emoji" v-html="heroEmoji"></div>
        <div>
          <h2 class="hero-title">{{ heroTitle }}</h2>
          <p class="hero-sub">
            {{ isOwnProfile ? "За пределами титров —" : "В коллекции —" }} {{ data.counts.total }} {{ titlesWord }},
            {{ episodesFormatted }} {{ episodesWord }} и {{ hoursText }} в
            компании любимых героев
          </p>
        </div>
      </section>

      <section class="counters-grid">
        <div class="counter-card">
          <span class="counter-label">В коллекции</span>
          <span class="counter-value">{{ totalDisplay }}</span>
          <span class="counter-caption">{{ titlesWord }}</span>
        </div>
        <div class="counter-card">
          <span class="counter-label">Просмотрено</span>
          <span class="counter-value">{{ epDisplay }}</span>
          <span class="counter-caption">{{ episodesWord }}</span>
        </div>
        <div class="counter-card">
          <span class="counter-label">Потрачено</span>
          <span class="counter-value">{{ hoursDisplay }}</span>
          <span class="counter-caption">{{ hoursCounterWord }}</span>
        </div>
        <div class="counter-card">
          <span class="counter-label">Выставлено</span>
          <span class="counter-value">{{ rateDisplay }}</span>
          <span class="counter-caption" v-if="data.avg_rating != null">
            ср. {{ Number(data.avg_rating).toFixed(1) }}
          </span>
          <span class="counter-caption" v-else>{{ ratingsWord }}</span>
        </div>
      </section>

      <section class="grid-2">
        <!-- <div class="panel">
          <h3 class="panel-title">🎭 Ваш аниме-портрет</h3>
          <div class="portrait-list">
            <div v-for="tag in portrait" :key="tag.label + tag.emoji" class="portrait-item">
              <span class="portrait-emoji">{{ tag.emoji }}</span>
              <div class="portrait-text">
                <span class="portrait-label">{{ tag.label }}</span>
                <span class="portrait-reason">{{ tag.reason }}</span>
              </div>
            </div>
          </div>
        </div> -->

        <div class="panel">
          <h3 class="panel-title">Статусы</h3>
          <div class="donut-wrap">
            <div class="donut" :style="donutStyle">
              <div class="donut-center">
                <span class="donut-total">{{ data.counts.total }}</span>
                <span class="donut-cap">{{ totalWord }}</span>
              </div>
            </div>
            <div class="donut-legend">
              <span v-for="seg in statusEntries" :key="seg.key" class="leg-item">
                <span class="leg-dot" :style="{ background: seg.color }"></span>
                {{ seg.label }}
                <span class="leg-count">{{ segCount(seg.key) }}</span>
              </span>
            </div>
          </div>
        </div>

        <div class="panel">
          <h3 class="panel-title"><SakuraIcon name="tag"/> Любимые жанры</h3>
          <div v-if="favoriteGenreRows.length" class="bar-list">
            <div v-for="g in favoriteGenreRows" :key="g.name" class="bar-row">
              <span class="bar-label">{{ g.name }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: Math.min(g.pct, 100) + '%' }"></div>
              </div>
              <span class="bar-val">{{ g.pct }}%</span>
            </div>
          </div>
          <p v-else class="panel-empty">Добавьте тайтлы, чтобы увидеть жанры</p>
        </div>
      </section>

      <!-- <section class="grid-2">
        <div class="panel">
          <h3 class="panel-title">🎬 Студии</h3>
          <div v-if="data.studios.length" class="chip-list">
            <span v-for="s in data.studios" :key="s.name" class="chip">
              {{ s.name }}
              <span class="chip-count">{{ shortCount(s.count) }}</span>
            </span>
          </div>
          <p v-else class="panel-empty">Студии появятся после добавления тайтлов</p>

          <h3 v-if="data.decades.length" class="panel-title panel-title-second">
            <SakuraIcon name="calendar"/> Годы релизов
          </h3>
          <div v-if="data.decades.length" class="bar-list">
            <div v-for="d in data.decades" :key="d.label" class="bar-row">
              <span class="bar-label">{{ d.label }}</span>
              <div class="bar-track">
                <div class="bar-fill bar-fill-2" :style="{ width: maxDecadePct(d.count) + '%' }"></div>
              </div>
              <span class="bar-val">{{ d.count }}</span>
            </div>
          </div>
        </div>
      </section> -->

      <section v-if="data.top_rated.length" class="panel">
        <h3 class="panel-title"><SakuraIcon name="star"/> Топ оценок</h3>
        <div class="rated-grid">
          <router-link
            v-for="r in data.top_rated"
            :key="r.anime_id"
            :to="`/anime/${(r as any).slug || r.anime_id}`"
            class="rated-card"
          >
            <img
              v-if="r.poster"
              :src="r.poster"
              :alt="r.title"
              class="rated-poster"
              loading="lazy"
            />
            <div v-else class="rated-poster rated-poster-fallback">
              <span>{{ r.title.slice(0, 1) }}</span>
            </div>
            <div class="rated-body">
              <span class="rated-title">{{ r.title }}</span>
              <span class="rated-meta">
                {{ r.year || "-" }} · {{ r.genres.slice(0, 2).join(", ") }}
              </span>
              <span class="rated-badge">{{ Number(r.rating).toFixed(1) }}</span>
            </div>
          </router-link>
        </div>
      </section>

      <section v-if="data.franchises.length" class="panel">
        <h3 class="panel-title"><SakuraIcon name="link" :size="16" /> Франшизы, которые вы смотрите</h3>
        <div class="franchise-list">
          <div v-for="f in data.franchises" :key="f.franchise_id" class="franchise-item">
            <span class="franchise-name">{{ f.name }}</span>
            <span class="franchise-meta">
              {{ f.watched_parts }}
              {{ plural(f.watched_parts, "часть", "части", "частей") }} в коллекции
            </span>
          </div>
        </div>
      </section>

      <section v-if="data.kinds.length" class="panel">
        <h3 class="panel-title"><SakuraIcon name="film" :size="16" /> Форматы</h3>
        <div class="chip-list">
          <span v-for="k in data.kinds" :key="k.value" class="chip">
            {{ kindLabel(k.value) }}
            <span class="chip-count">{{ shortCount(k.count) }}</span>
          </span>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { computed, onMounted, onUnmounted, ref } from "vue";
import { libraryApi, type WrappedData } from "@/api/library";
import { useAuthStore } from "@/stores/auth";

const props = defineProps<{
  embedded?: boolean;
  userId?: number | string | null;
}>();

const authStore = useAuthStore();

const data = ref<WrappedData | null>(null);
const loading = ref(true);
const error = ref(false);
const isOwnProfile = computed(() => {
  if (!props.userId) return true;
  return Number(props.userId) === Number(authStore.user?.id);
});
const profileName = computed(() => data.value?.user.display_name || "этот пользователь");
const heroTitle = computed(() =>
  isOwnProfile.value
    ? `Привет, ${profileName.value}`
    : `Пользователь ${profileName.value}`,
);
const emptyStateTitle = computed(() =>
  isOwnProfile.value
    ? "Пока нечего анализировать"
    : `У пользователя ${profileName.value} пока нет статистики`,
);
const favoriteGenreRows = computed(() => {
  const genres = [...(data.value?.genres || [])].sort(
    (left, right) => Number(right.pct || 0) - Number(left.pct || 0),
  );
  const top = genres.slice(0, 4);
  const other = genres.slice(4).reduce(
    (sum, genre) => ({
      count: sum.count + Number(genre.count || 0),
      pct: sum.pct + Number(genre.pct || 0),
    }),
    { count: 0, pct: 0 },
  );
  return genres.length
    ? [...top, { name: "Другое", count: other.count, pct: Math.round(other.pct * 10) / 10 }]
    : [];
});

async function load() {
  loading.value = true;
  error.value = false;
  try {
    const userId = props.userId ? Number(props.userId) : undefined;
    data.value = await libraryApi.getWrapped(userId);
    runCounters();
  } catch {
    error.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(load);

const portraitIndex = ref(0);
const portrait = computed(() => {
  if (!data.value || !data.value.portrait.length) return [];
  const tags = data.value.portrait;
  if (portraitIndex.value === 0) return tags;
  return [...tags.slice(portraitIndex.value), ...tags.slice(0, portraitIndex.value)];
});

function rerollPortrait() {
  const len = data.value?.portrait?.length ?? 0;
  if (len > 1) portraitIndex.value = (portraitIndex.value + 1) % len;
}

const heroEmoji = computed(() => {
  const p = data.value?.portrait?.[0];
  if (p?.emoji) return p.emoji;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-80 -80 160 160" width="64" height="64">
  <defs>
    <!-- Лепесток с выемкой на конце -->
    <path id="p" d="M0,0 C-15,-10 -31,-30 -23,-54 C-19,-65 -8,-63 0,-52 C8,-63 19,-65 23,-54 C31,-30 15,-10 0,0 Z"/>
    <clipPath id="c"><use href="#p"/></clipPath>

    <g id="pet">
      <!-- основа -->
      <use href="#p" fill="#ffc4da"/>
      <g clip-path="url(#c)">
        <!-- тень справа -->
        <path d="M24,-60 C33,-30 15,-10 0,1 C11,-20 17,-38 9,-66 Z" fill="#f7a3c3"/>
        <!-- насыщенное основание -->
        <path d="M0,2 C-10,-6 -16,-18 -12,-30 C-6,-26 6,-26 12,-30 C16,-18 10,-6 0,2 Z" fill="#ff86b2"/>
        <!-- прожилки -->
        <path d="M0,-8 L0,-40 M0,-10 L-10,-38 M0,-10 L10,-38" fill="none" stroke="#e8689b" stroke-width="1.3" stroke-linecap="round"/>
      </g>
      <!-- контур -->
      <use href="#p" fill="none" stroke="#4a1d3f" stroke-width="3" stroke-linejoin="round"/>
      <!-- блик -->
      <path d="M-19,-50 C-24,-41 -23,-31 -18,-23" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/>
      <circle cx="-22" cy="-17" r="1.5" fill="#fff"/>
    </g>

    <!-- тычинки: короткая и длинная -->
    <g id="s1">
      <path d="M0,-6 L0,-21" stroke="#4a1d3f" stroke-width="3.4" stroke-linecap="round"/>
      <path d="M0,-6 L0,-21" stroke="#ff7fae" stroke-width="1.4" stroke-linecap="round"/>
      <circle cy="-23" r="3.4" fill="#ffd166" stroke="#4a1d3f" stroke-width="1.8"/>
    </g>
    <g id="s2">
      <path d="M0,-6 L0,-27" stroke="#4a1d3f" stroke-width="3.4" stroke-linecap="round"/>
      <path d="M0,-6 L0,-27" stroke="#ff7fae" stroke-width="1.4" stroke-linecap="round"/>
      <circle cy="-29" r="3.4" fill="#ffd166" stroke="#4a1d3f" stroke-width="1.8"/>
    </g>
  </defs>

  <!-- 5 лепестков -->
  <use href="#pet"/>
  <use href="#pet" transform="rotate(72)"/>
  <use href="#pet" transform="rotate(144)"/>
  <use href="#pet" transform="rotate(216)"/>
  <use href="#pet" transform="rotate(288)"/>

  <!-- тычинки -->
  <use href="#s1" transform="rotate(18)"/>
  <use href="#s2" transform="rotate(54)"/>
  <use href="#s1" transform="rotate(90)"/>
  <use href="#s2" transform="rotate(126)"/>
  <use href="#s1" transform="rotate(162)"/>
  <use href="#s2" transform="rotate(198)"/>
  <use href="#s1" transform="rotate(234)"/>
  <use href="#s2" transform="rotate(270)"/>
  <use href="#s1" transform="rotate(306)"/>
  <use href="#s2" transform="rotate(342)"/>

  <!-- сердцевина -->
  <circle r="8" fill="#e0467f" stroke="#4a1d3f" stroke-width="2.6"/>
  <circle r="3.6" fill="#ff86b2"/>
  <circle cx="-2.6" cy="-2.8" r="1.5" fill="#fff"/>
</svg>`;
});

function makeCounter() {
  const display = ref(0);
  let raf = 0;
  function run(target: number, duration = 1400) {
    cancelAnimationFrame(raf);
    const start = performance.now();
    const step = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      display.value = Math.round(target * eased);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }
  onUnmounted(() => cancelAnimationFrame(raf));
  return { display, run };
}

const totalCnt = makeCounter();
const epCnt = makeCounter();
const hoursCnt = makeCounter();
const rateCnt = makeCounter();

function runCounters() {
  if (!data.value) return;
  totalCnt.run(data.value.counts.total);
  epCnt.run(data.value.episodes_watched);
  hoursCnt.run(Math.round(data.value.hours_watched * 10));
  rateCnt.run(data.value.ratings_given);
}

const totalDisplay = computed(() => totalCnt.display.value.toLocaleString("ru"));
const epDisplay = computed(() => epCnt.display.value.toLocaleString("ru"));
const hoursDisplay = computed(() => (hoursCnt.display.value / 10).toFixed(1));
const rateDisplay = computed(() => rateCnt.display.value.toLocaleString("ru"));

const episodesFormatted = computed(() =>
  Number(data.value?.episodes_watched ?? 0).toLocaleString("ru"),
);

const hoursText = computed(() => {
  const h = Number(data.value?.hours_watched ?? 0);
  if (h < 1) {
    const min = Math.round(h * 60);
    return `${min} ${plural(min, "минута", "минуты", "минут")}`;
  }
  const rounded = Math.round(h * 10) / 10;
  const intPart = Math.floor(rounded);
  return `${rounded} ${plural(intPart, "час", "часа", "часов")}`;
});

/* ===== Склонения ===== */

function plural(n: number, one: string, few: string, many: string): string {
  const abs = Math.abs(n) % 100;
  const last = abs % 10;
  if (abs > 10 && abs < 20) return many;
  if (last > 1 && last < 5) return few;
  if (last === 1) return one;
  return many;
}

const titlesWord = computed(() =>
  plural(data.value?.counts.total ?? 0, "тайтл", "тайтла", "тайтлов"),
);
const episodesWord = computed(() =>
  plural(data.value?.episodes_watched ?? 0, "эпизод", "эпизода", "эпизодов"),
);
const ratingsWord = computed(() =>
  plural(data.value?.ratings_given ?? 0, "оценка", "оценки", "оценок"),
);
const totalWord = computed(() =>
  plural(data.value?.counts.total ?? 0, "тайтл", "тайтла", "тайтлов"),
);
const hoursCounterWord = computed(() =>
  plural(Math.floor(Number(hoursDisplay.value) || 0), "час", "часа", "часов"),
);

/* ===== Статусы ===== */

const STATUS_META = [
  { key: "completed", label: "Просмотрено", color: "#ff7eb3" },
  { key: "started", label: "В процессе", color: "#a8c5e2" },
  { key: "planned", label: "Запланировано", color: "#c9a2e8" },
  { key: "on_hold", label: "Отложено", color: "#ffcba4" },
  { key: "dropped", label: "Брошено", color: "#e8807f" },
] as const;

const statusEntries = computed(() =>
  STATUS_META.filter((s) => segCount(s.key) > 0),
);

function segCount(key: string): number {
  return (data.value?.counts as Record<string, number>)?.[key] ?? 0;
}

const donutStyle = computed(() => {
  const total = data.value?.counts.total ?? 1;
  let acc = 0;
  const stops = statusEntries.value.map((s) => {
    const from = (acc / total) * 360;
    acc += segCount(s.key);
    const to = (acc / total) * 360;
    return `${s.color} ${from.toFixed(2)}deg ${to.toFixed(2)}deg`;
  });
  if (!stops.length) return { background: "var(--surface-4)" };
  return { background: `conic-gradient(${stops.join(", ")})` };
});

function maxDecadePct(count: number): number {
  const max = Math.max(...(data.value?.decades.map((d) => d.count) ?? [1]));
  return Math.max((count / max) * 100, 2);
}

const KIND_LABELS: Record<string, string> = {
  tv: "ТВ-сериал",
  movie: "Фильм",
  ova: "OVA",
  ona: "ONA",
  special: "Спешл",
};

function kindLabel(kind: string): string {
  return KIND_LABELS[kind] ?? kind;
}

function shortCount(count: number): string {
  return Number(count).toLocaleString("ru");
}
</script>

<style scoped>
.stats-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-6) var(--space-6) var(--space-12);
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: 800;
  letter-spacing: 0.02em;
  margin: 0;
  color: var(--text-primary);
}

.page-subtitle {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--text-muted, rgba(249, 121, 174, 0.6));
}

.btn-retro {
  font-size: var(--text-sm);
  background: var(--accent-subtle);
  color: var(--accent-bright);
  border: 1px solid var(--border-subtle);
}

.btn-retro:hover {
  background: var(--accent-glow-sm);
}

.hero-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-5);
  border-radius: var(--radius-2xl);
  background: linear-gradient(
    135deg,
    rgba(255, 126, 179, 0.16),
    rgba(168, 197, 226, 0.1) 60%,
    rgba(201, 162, 232, 0.12)
  );
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.hero-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at 20% 0%,
    var(--accent-glow-sm),
    transparent 60%
  );
  pointer-events: none;
}

.hero-emoji {
  font-size: 52px;
  filter: drop-shadow(0 0 18px var(--accent-glow));
  flex-shrink: 0;
}

.hero-title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 800;
}

.hero-sub {
  margin: var(--space-2) 0 0;
  font-size: var(--text-sm);
  color: var(--text-muted, rgba(249, 121, 174, 0.62));
  max-width: 520px;
  line-height: 1.5;
}

.counters-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.counter-card {
  min-width: 0;
  overflow-wrap: anywhere;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-5);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
}

.counter-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted, rgba(249, 121, 174, 0.55));
}

.counter-value {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--accent-bright);
  font-variant-numeric: tabular-nums;
}

.counter-caption {
  font-size: var(--text-xs);
  color: var(--text-muted, rgba(249, 121, 174, 0.5));
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.panel {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);
}

.panel-title {
  margin: 0 0 var(--space-4);
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: 0.01em;
  color: var(--text-primary);
}

.panel-title-second {
  margin-top: var(--space-6);
}

.panel-empty {
  color: var(--text-muted, rgba(249, 121, 174, 0.5));
  font-size: var(--text-sm);
  margin: 0;
}

.portrait-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.portrait-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.portrait-emoji {
  font-size: 26px;
  flex-shrink: 0;
}

.portrait-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.portrait-label {
  font-weight: 700;
  font-size: var(--text-sm);
}

.portrait-reason {
  font-size: var(--text-xs);
  color: var(--text-muted, rgba(249, 121, 174, 0.6));
}

.donut-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.donut {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  position: relative;
  flex-shrink: 0;
}

.donut-center {
  position: absolute;
  inset: 12px;
  background: var(--surface-3);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.donut-total {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--accent-bright);
}

.donut-cap {
  font-size: var(--text-xs);
  color: var(--text-muted, rgba(249, 121, 174, 0.55));
}

.donut-legend {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.leg-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
}

.leg-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.leg-count {
  margin-left: auto;
  font-weight: 700;
  color: var(--accent-bright);
  font-variant-numeric: tabular-nums;
}

.bar-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.bar-row {
  display: grid;
  grid-template-columns: 130px 1fr 44px;
  align-items: center;
  gap: var(--space-3);
}

.bar-label {
  font-size: var(--text-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-track {
  background: var(--surface-4);
  border-radius: var(--radius-full);
  height: 8px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: var(--accent);
  transition: width 0.8s var(--ease-out, ease);
}

.bar-fill-2 {
  background: linear-gradient(90deg, var(--accent-2), #cdddf0);
}

.bar-val {
  font-size: var(--text-xs);
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: var(--text-muted, rgba(249, 121, 174, 0.6));
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
}

.chip-count {
  background: var(--accent-subtle);
  color: var(--accent-bright);
  padding: 1px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 700;
}

.rated-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
}

.rated-card {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: inherit;
  transition:
    border-color var(--duration-base, 0.16s) ease,
    transform var(--duration-fast, 0.1s) ease;
}

.rated-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.rated-poster {
  width: 52px;
  height: 72px;
  object-fit: cover;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.rated-poster-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--surface-5), var(--surface-6));
}

.rated-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.rated-title {
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rated-meta {
  font-size: var(--text-xs);
  color: var(--text-muted, rgba(249, 121, 174, 0.55));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rated-badge {
  margin-top: auto;
  align-self: flex-start;
  font-size: var(--text-sm);
  font-weight: 800;
  color: var(--accent-bright);
}

.franchise-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.franchise-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  flex-wrap: wrap;
}

.franchise-name {
  font-size: var(--text-sm);
  font-weight: 600;
}

.franchise-meta {
  font-size: var(--text-xs);
  color: var(--text-muted, rgba(249, 121, 174, 0.6));
}

.stats-skel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.skel-block {
  height: 140px;
  border-radius: var(--radius-xl);
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-4) 50%,
    var(--surface-3) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  to {
    background-position: -200% 0;
  }
}

@media (max-width: 900px) {
  .counters-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .grid-2 {
    grid-template-columns: 1fr;
  }
  .bar-row {
    grid-template-columns: 110px 1fr 40px;
  }
}

@media (max-width: 520px) {
  .counters-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .page-header {
    align-items: flex-start;
  }
}
</style>
