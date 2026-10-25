<template>
  <div class="ann">
    <div v-if="!loading && !error && totalAnims > 0" class="ann-stats">
      <span class="ann-stat">{{ totalAnims }} анонсов</span>
      <span class="ann-stat-dot">·</span>
      <span class="ann-stat">{{ premiereCount }} с датой премьеры</span>
      <span class="ann-stat-dot">·</span>
      <span class="ann-stat">{{ undatedCount }} дата не объявлена</span>
    </div>

    <section v-if="!loading && !error && premieres.length" class="ann-hero">
      <h2 class="ann-hero-title">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
        >
          <path d="M2 3a3 3 0 0 1 6 0v9a3 3 0 0 1-6 0V3z" />
          <path d="M6 4h10a4 4 0 0 1 0 8H6M15 3v9" />
        </svg>
        Ближайшие премьеры
      </h2>
      <p class="ann-hero-sub">
        Обратный отсчёт до выхода -того, что уже объявлено
      </p>
      <div class="ann-hero-scroll">
        <button
          v-for="p in premieres"
          :key="p.a.id"
          type="button"
          class="ann-hero-card"
          @click="goToAnime(p.a)">
          <div class="ann-hero-poster">
            <img
              v-if="poster(p.a)"
              :src="poster(p.a)"
              :alt="title(p.a)"
              loading="lazy"
              @error="hideImg"
            />
            <div v-else class="ann-hero-ph">
              <svg
                width="32"
                height="32"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <rect x="2" y="2" width="20" height="20" rx="2" />
                <path d="M12 2v20M2 12h20" />
              </svg>
            </div>
            <span :class="['ann-hero-chip', p.days <= 7 ? 'chip-soon' : '']">
              <template v-if="p.days === 0">Сегодня</template>
              <template v-else-if="p.days === 1">Завтра</template>
              <template v-else>через {{ p.days }} дн.</template>
            </span>
          </div>
          <div class="ann-hero-meta">
            <p class="ann-hero-name">{{ title(p.a) }}</p>
            <p class="ann-hero-date">{{ dateLabel(p.a.release_date) }}</p>
          </div>
        </button>
      </div>
    </section>

    <AnimeFilterBar
      :show-status="false"
      :show-advanced="true"
      :show-shuffle="false"
      :show-franchise-filter="false"
      :show-library-filters="false"
      :results-count="sortedAnime.length"
      search-placeholder="Поиск анонса..."
      :sort-options="[
        { value: '-year', label: 'Год выхода ↓' },
        { value: 'year', label: 'Год выхода ↑' },
        { value: '-release_date', label: 'Сначала ближайшие' }
      ]"
      @change="onFilterChange"
      @refresh="$emit('refresh')"
    />

    <div v-if="loading" class="ann-grid">
      <div v-for="i in 24" :key="i" class="ann-skel">
        <div class="ann-skel-poster"></div>
        <div class="ann-skel-line"></div>
        <div class="ann-skel-line short"></div>
      </div>
    </div>

    <div v-else-if="error" class="ann-message ann-err">
      <svg
        width="40"
        height="40"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <div>
        <p class="ann-msg-title">Не удалось загрузить анонсы</p>
        <button @click="$emit('refresh')" class="ann-retry" type="button">
          Попробовать снова
        </button>
      </div>
    </div>

    <div v-else-if="sortedAnime.length === 0" class="ann-message">
      <svg
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.2"
      >
        <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
        <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
        <line x1="6" y1="1" x2="6" y2="4" />
        <line x1="10" y1="1" x2="10" y2="4" />
        <line x1="14" y1="1" x2="14" y2="4" />
      </svg>
      <div>
        <p class="ann-msg-title">Анонсов пока нет</p>
        <p class="ann-msg-sub">Здесь появятся анонсы предстоящих аниме</p>
      </div>
    </div>

    <div v-else>
      <p class="ann-count">{{ sortedAnime.length }} аниме</p>
      <div class="ann-grid">
        <div v-for="a in sortedAnime" :key="a.id" class="ann-grid-item">
          <span v-if="badgeInfo(a).show" :class="['ann-badge', badgeInfo(a).mod]">
            {{ badgeInfo(a).text }}
          </span>
          <AnimeCard
            :anime="toCardAnime(a)"
            :show-actions="true"
            :show-genres="true"
            :show-progress="false"
            @click="goToAnime(a)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import AnimeFilterBar from "@/components/Filters/AnimeFilterBar.vue";
import type { FilterState } from "@/components/Filters/AnimeFilterBar.vue";
import AnimeCard from "@/components/Cards/AnimeCard.vue";
interface Props {
  anime: unknown[];
  loading: boolean;
  error: string | null;
}
const props = defineProps<Props>();
const emits = defineEmits<{ refresh: [] }>();

const router = useRouter();
const goToAnime = (a: { slug?: string; id: number | string }) => router.push(`/anime/${a.slug || a.id}`);

const filters = ref<FilterState>({});
const onFilterChange = (f: FilterState) => {
  filters.value = f;
};

interface GenreObj {
  id: number;
  name: string;
  slug: string;
}

interface Announcement {
  id: number | string;
  slug?: string;
  title_ru?: string;
  title_en?: string;
  title?: string;
  year?: number | string | null;
  release_date?: string | null;
  release_date_string?: string | null;
  status?: string;
  episodes?: number | null;
  episodes_count?: number | null;
  score?: number | string | null;
  poster_url?: string | null;
  poster_image_url?: string | null;
  poster?: string | null;
  type?: string;
  kind?: string;
  genres?: unknown;
}

const title = (a: Announcement): string =>
  String(a.title_ru || a.title_en || a.title || "Без названия");
const genreList = (a: Announcement): GenreObj[] => {
  const raw = a.genres;
  if (!raw) return [];
  if (Array.isArray(raw))
    return raw.map((g: unknown) =>
      typeof g === "object" && g !== null
        ? {
            id: Number((g as { id?: number | string }).id ?? 0),
            name: String((g as { name?: string }).name ?? ""),
            slug: String((g as { slug?: string }).slug ?? ""),
          }
        : { id: typeof g === "number" ? g : 0, name: String(g), slug: String(g) },
    );
  if (typeof raw === "string") {
    try {
      const p = JSON.parse(raw);
      return Array.isArray(p) ? (p as GenreObj[]) : [];
    } catch {
      return raw
        .split(",")
        .map((g: string, i: number) => ({
          id: i,
          name: g.trim(),
          slug: g.trim(),
        }));
    }
  }
  return [];
};

const toCardAnime = (a: Announcement): {
  id: number;
  title_ru: string;
  title_en: string;
  year: number | null;
  release_date: string | null;
  release_date_string: string;
  status: string;
  episodes: number | null;
  score: number | null;
  poster_url: string | null;
  poster_image_url: string | null;
  poster: string | null;
  type: string;
  genres: GenreObj[];
} => ({
  id: Number(a.id),
  title_ru: String(a.title_ru || a.title || ""),
  title_en: String(a.title_en || ""),
  year: a.year != null ? Number(a.year) : null,
  release_date: a.release_date || null,
  release_date_string: a.release_date_string || "",
  status: a.status || "announced",
  episodes:
    a.episodes != null
      ? Number(a.episodes)
      : a.episodes_count != null
        ? Number(a.episodes_count)
        : null,
  score: a.score != null && a.score !== "" ? Number(a.score) : null,
  poster_url: a.poster_url || null,
  poster_image_url: a.poster_image_url || null,
  poster: a.poster || null,
  type: a.type || a.kind || "",
  genres: genreList(a),
});


const MONTHS_GEN = [
  "января",
  "февраля",
  "марта",
  "апреля",
  "мая",
  "июня",
  "июля",
  "августа",
  "сентября",
  "октября",
  "ноября",
  "декабря",
];

const parseReleaseDate = (s?: string | null): Date | null => {
  if (!s) return null;
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
};

const daysUntil = (d: Date): number => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  return Math.round((target.getTime() - today.getTime()) / 86400000);
};

const dateLabel = (s?: string | null): string => {
  const d = parseReleaseDate(s);
  if (!d) return "";
  return `${d.getDate()} ${MONTHS_GEN[d.getMonth()]} ${d.getFullYear()}`;
};

const poster = (a: Announcement): string =>
  a.poster_url || a.poster_image_url || a.poster || "";

const hideImg = (e: Event) => {
  const img = e.target as HTMLImageElement;
  img.style.display = "none";
};

const allAnime = computed(() => props.anime as Announcement[]);

const totalAnims = computed(() => allAnime.value.length);
const premiereCount = computed(
  () =>
    allAnime.value.filter(
      (a) => parseReleaseDate(a.release_date) !== null,
    ).length,
);
const undatedCount = computed(
  () =>
    allAnime.value.filter(
      (a) => parseReleaseDate(a.release_date) === null,
    ).length,
);

const premieres = computed(() =>
  allAnime.value
    .map((a) => {
      const d = parseReleaseDate(a.release_date);
      if (!d) return null;
      const days = daysUntil(d);
      if (days < 0) return null;
      return { a, days };
    })
    .filter((x): x is { a: Announcement; days: number } => x !== null)
    .sort((x, y) => x.days - y.days)
    .slice(0, 8),
);

const countdown = (
  a: Announcement,
): { text: string; mod: string } | null => {
  const d = parseReleaseDate(a.release_date);
  if (!d) return null;
  const days = daysUntil(d);
  if (days < 0) return null;
  if (days === 0) return { text: "Премьера сегодня", mod: "soon" };
  if (days === 1) return { text: "Премьера завтра", mod: "soon" };
  if (days <= 30) return { text: `До премьеры ${days} дн.`, mod: "soon" };
  return { text: dateLabel(a.release_date), mod: "" };
};

const badgeInfo = (
  a: Announcement,
): { text: string; mod: string; show: boolean } => {
  const c = countdown(a);
  if (c) return { ...c, show: true };
  if (!a.release_date) return { text: "Анонс", mod: "muted", show: true };
  return { text: "", mod: "", show: false };
};


const sortedAnime = computed(() => {
  let list: Announcement[] = allAnime.value;
  const {
    search,
    genres,
    type,
    year_from,
    year_to,
    score_from,
    score_to,
    episodes_from,
    episodes_to,
    genre_logic,
    ordering,
  } = filters.value;

  if (search?.trim()) {
    const q = search.toLowerCase();
    list = list.filter(
      (a) =>
        title(a).toLowerCase().includes(q) ||
        (a.title_en || "").toLowerCase().includes(q),
    );
  }
  if (genres?.length) {
    list = list.filter((a) => {
      const matches = (sg: string) =>
        genreList(a).some((g: GenreObj) => g.name.toLowerCase() === sg.toLowerCase());
      return genre_logic === "AND" ? genres.every(matches) : genres.some(matches);
    });
  }
  if (type?.length) {
    list = list.filter((a) =>
      type.includes(String(a.type || a.kind || "").toLowerCase()),
    );
  }
  if (year_from)
    list = list.filter((a) => (a.year != null ? Number(a.year) : 0) >= year_from);
  if (year_to)
    list = list.filter((a) => (a.year != null ? Number(a.year) : 0) <= year_to);
  if (score_from)
    list = list.filter(
      (a) => (a.score != null && a.score !== "" ? Number(a.score) : 0) >= score_from,
    );
  if (score_to)
    list = list.filter(
      (a) => (a.score != null && a.score !== "" ? Number(a.score) : 0) <= score_to,
    );
  if (episodes_from)
    list = list.filter((a) => Number(a.episodes ?? a.episodes_count ?? 0) >= episodes_from);
  if (episodes_to)
    list = list.filter((a) => Number(a.episodes ?? a.episodes_count ?? 0) <= episodes_to);

  switch (ordering || "-score") {
    case "-year":
      return list.sort(
        (a, b) => (b.year != null ? Number(b.year) : 0) - (a.year != null ? Number(a.year) : 0),
      );
    case "year":
      return list.sort(
        (a, b) => (a.year != null ? Number(a.year) : 0) - (b.year != null ? Number(b.year) : 0),
      );
    case "-release_date":
      return list.sort((a, b) => {
        const da = parseReleaseDate(a.release_date)?.getTime() ?? Number.MAX_SAFE_INTEGER;
        const db = parseReleaseDate(b.release_date)?.getTime() ?? Number.MAX_SAFE_INTEGER;
        return da - db;
      });
    case "release_date":
      return list.sort((a, b) => {
        const da = parseReleaseDate(a.release_date)?.getTime() ?? Number.MAX_SAFE_INTEGER;
        const db = parseReleaseDate(b.release_date)?.getTime() ?? Number.MAX_SAFE_INTEGER;
        return db - da;
      });
    case "-score":
      return list.sort(
        (a, b) =>
          (b.score != null && b.score !== "" ? Number(b.score) : 0) -
          (a.score != null && a.score !== "" ? Number(a.score) : 0),
      );
    case "title_ru":
      return list.sort((a, b) => title(a).localeCompare(title(b)));
    default:
      return list;
  }
});

onMounted(() => {
  if (!props.anime.length && !props.loading) emits("refresh");
});
</script>

<style scoped>
.ann {
}
.ann-stats {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
}
.ann-stat {
  color: var(--text-secondary);
}
.ann-stat-dot {
  opacity: 0.5;
}

/* ---- Ближайшие премьеры ---- */
.ann-hero {
  margin-bottom: var(--space-6);
}
.ann-hero-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-lg);
  color: var(--text-primary);
  margin: 0 0 var(--space-1);
}
.ann-hero-title svg {
  color: var(--accent);
}
.ann-hero-sub {
  margin: 0 0 var(--space-4);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}
.ann-hero-scroll {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: var(--space-2);
  scrollbar-width: thin;
}
.ann-hero-card {
  flex: 0 0 150px;
  background: none;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  color: inherit;
}
.ann-hero-poster {
  position: relative;
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-3);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
}
.ann-hero-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.ann-hero-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}
.ann-hero-chip {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  color: #fff;
  background: linear-gradient(0deg, rgba(0, 0, 0, 0.85), transparent);
  padding-top: 18px;
}
.ann-hero-chip.chip-soon {
  color: #ffd28a;
  background: linear-gradient(0deg, rgba(40, 18, 0, 0.9), transparent);
}
.ann-hero-meta {
  margin-top: var(--space-2);
}
.ann-hero-name {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.ann-hero-date {
  margin: var(--space-1) 0 0;
  font-size: 12px;
  color: var(--accent);
}

.ann-count {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}

.ann-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
}
.ann-grid-item {
  position: relative;
}
.ann-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 3;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
  background: var(--surface-4);
  color: var(--text-secondary);
  pointer-events: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
.ann-badge.soon {
  background: rgba(255, 170, 60, 0.92);
  color: #1a0d00;
}
.ann-badge.muted {
  background: rgba(20, 22, 30, 0.8);
  color: var(--text-tertiary);
}
.ann-skel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ann-skel-poster {
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-4) 50%,
    var(--surface-3) 75%
  );
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.ann-skel-line {
  height: 12px;
  width: 80%;
  border-radius: var(--radius-xs);
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-4) 50%,
    var(--surface-3) 75%
  );
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.ann-skel-line.short {
  width: 55%;
}
@keyframes sk {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

.ann-message {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: 60px var(--space-6);
  color: var(--text-tertiary);
}
.ann-message svg {
  opacity: 0.4;
  flex-shrink: 0;
}
.ann-msg-title {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  margin: 0 0 var(--space-2);
}
.ann-msg-sub {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 0;
}
.ann-err svg {
  color: var(--danger);
  opacity: 1;
}
.ann-retry {
  background: none;
  border: none;
  color: var(--accent);
  font-size: var(--text-sm);
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

@media (max-width: 374px) {
  .ann-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
  .ann-hero-card {
    flex: 0 0 120px;
  }
}
@media (min-width: 375px) and (max-width: 413px) {
  .ann-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  .ann-hero-card {
    flex: 0 0 124px;
  }
}
@media (min-width: 414px) and (max-width: 767px) {
  .ann-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
  }
  .ann-hero-card {
    flex: 0 0 132px;
  }
}
@media (min-width: 768px) {
  .ann-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem;
  }
}
</style>
