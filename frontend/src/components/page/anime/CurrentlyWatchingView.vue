<template>
  <div class="cw">
    <div class="cw-header">
      <div class="cw-header-left">
        <div class="cw-live-dot"></div>
        <div>
          <h2 class="cw-title">Сейчас смотрят</h2>
          <p class="cw-subtitle">
            <span v-if="!loading && filteredAnime.length">
              {{ totalViewers }} {{ viewersWord(totalViewers) }} смотрят
              {{ filteredAnime.length }} аниме прямо сейчас
            </span>
            <span v-else>Аниме, которые активно смотрят на сайте</span>
          </p>
        </div>
      </div>
      <button class="cw-refresh" @click="$emit('refresh')" :disabled="loading" type="button">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spin: loading }">
          <path d="M23 4v6h-6" />
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
        </svg>
        Обновить
      </button>
    </div>

    <AnimeFilterBar
      :show-status="false"
      :show-advanced="true"
      :show-shuffle="false"
      :show-franchise-filter="false"
      :show-library-filters="false"
      :results-count="filteredAnime.length"
      default-ordering="-viewers"
      search-placeholder="Поиск среди просматриваемых..."
      :sort-options="[
        { value: '-viewers', label: 'Сейчас популярнее' },
        { value: '-score', label: 'Рейтинг: 10–0' },
        { value: '-year', label: 'Год: новее' },
        { value: 'title_ru', label: 'Название: А–Я' },
      ]"
      @change="filters = $event"
      @refresh="$emit('refresh')"
    />

    <div v-if="loading" class="cw-grid">
      <div v-for="i in 12" :key="i" class="cw-skel">
        <div class="cw-skel-poster"></div>
        <div class="cw-skel-line"></div>
        <div class="cw-skel-line short"></div>
      </div>
    </div>

    <div v-else-if="error" class="cw-message cw-error">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <div>
        <p class="cw-msg-title">Не удалось загрузить данные</p>
        <button @click="$emit('refresh')" class="cw-retry" type="button">
          Попробовать снова
        </button>
      </div>
    </div>

    <div v-else-if="!anime.length" class="cw-message">
      <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
      <div>
        <p class="cw-msg-title">Никто ничего не смотрит прямо сейчас</p>
        <p class="cw-msg-sub">Попробуйте обновить через несколько минут</p>
      </div>
    </div>

    <div v-else-if="!filteredAnime.length" class="cw-message">
      <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
      <div>
        <p class="cw-msg-title">По этим фильтрам ничего не найдено</p>
        <p class="cw-msg-sub">Измените условия поиска</p>
      </div>
    </div>

    <div v-else class="cw-grid">
      <AnimeCard
        v-for="a in filteredAnime"
        :key="a.id"
        :anime="normalizeAnime(a)"
        :show-actions="true"
        :show-genres="true"
        :show-progress="false"
        :viewers-count="a.viewers_count || 0"
        @click="goToAnime(a)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import AnimeCard, { type AnimeCardProps } from "@/components/Cards/AnimeCard.vue"
import AnimeFilterBar, { type FilterState } from "@/components/Filters/AnimeFilterBar.vue";
interface Props {
  anime: { id: number; slug?: string; title_ru?: string; title_en?: string; title_orig?: string; year?: number | null; status?: string; episodes?: number | null; episodes_total?: number | null; score?: number | string | null; poster_url?: string | null; poster_image_url?: string | null; poster_file?: string | null; poster?: string | null; kind?: string; type?: string; genres?: unknown[]; viewers_count?: number }[];
  loading: boolean;
  error: string | null;
}
const props = defineProps<Props>();
defineEmits<{ refresh: [] }>();

const router = useRouter();
const filters = ref<FilterState>({ ordering: "-viewers" });
const goToAnime = (a: { slug?: string; id: number | string }) => router.push(`/anime/${a.slug || a.id}`);

const totalViewers = computed(() =>
  filteredAnime.value.reduce((sum, a) => sum + (a.viewers_count || 0), 0),
);

const genreNames = (anime: Props["anime"][number]) =>
  (anime.genres || []).map((genre) =>
    typeof genre === "object" && genre !== null
      ? String((genre as { name?: string }).name || "")
      : String(genre),
  ).filter(Boolean);

const animeTitle = (anime: Props["anime"][number]) =>
  String(anime.title_ru || anime.title_en || anime.title_orig || "");

const filteredAnime = computed(() => {
  const state = filters.value;
  let list = [...props.anime];
  if (state.search) {
    const query = state.search.toLowerCase();
    list = list.filter((anime) => animeTitle(anime).toLowerCase().includes(query));
  }
  if (state.genres?.length) {
    list = list.filter((anime) => {
      const names = genreNames(anime).map((name) => name.toLowerCase());
      const matches = (genre: string) => names.includes(genre.toLowerCase());
      return state.genre_logic === "AND" ? state.genres!.every(matches) : state.genres!.some(matches);
    });
  }
  if (state.type?.length)
    list = list.filter((anime) => state.type!.includes(String(anime.kind || anime.type || "").toLowerCase()));
  if (state.year_from) list = list.filter((anime) => Number(anime.year || 0) >= state.year_from!);
  if (state.year_to) list = list.filter((anime) => Number(anime.year || 0) <= state.year_to!);
  if (state.score_from) list = list.filter((anime) => Number(anime.score || 0) >= state.score_from!);
  if (state.score_to) list = list.filter((anime) => Number(anime.score || 0) <= state.score_to!);
  if (state.episodes_from) list = list.filter((anime) => Number(anime.episodes ?? anime.episodes_total ?? 0) >= state.episodes_from!);
  if (state.episodes_to) list = list.filter((anime) => Number(anime.episodes ?? anime.episodes_total ?? 0) <= state.episodes_to!);

  return list.sort((left, right) => {
    switch (state.ordering) {
      case "-score": return Number(right.score || 0) - Number(left.score || 0);
      case "-year": return Number(right.year || 0) - Number(left.year || 0);
      case "title_ru": return animeTitle(left).localeCompare(animeTitle(right), "ru");
      default: return Number(right.viewers_count || 0) - Number(left.viewers_count || 0);
    }
  });
});

/** Нормализует объект из /currently-watching/ в формат AnimeCard */
const normalizeAnime = (a: Props["anime"][number]): AnimeCardProps => ({
  id: a.id,
  title_ru: a.title_ru || a.title_en || "",
  title_en: a.title_en || a.title_orig || "",
  year: a.year ?? null,
  status: a.status || "ongoing",
  episodes: a.episodes ?? a.episodes_total ?? null,
  score: a.score ? Number(a.score) : null,
  poster_url: a.poster_url || null,
  poster_image_url: a.poster_image_url || null,
  poster_file: a.poster_file || null,
  poster: a.poster || null,
  type: a.kind || a.type,
  genres: genreNames(a).map((name, index) => ({ id: index, name, slug: name.toLowerCase() })),
});

const viewersWord = (n: number): string => {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 19) return "человек";
  if (mod10 === 1) return "человек";
  if (mod10 >= 2 && mod10 <= 4) return "человека";
  return "человек";
};
</script>

<style scoped>
/* ── Хедер ─────────────────────────────────────────────────── */
.cw-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
  padding: var(--space-5) var(--space-6);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.cw-header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

/* Живая точка */
.cw-live-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
  box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  animation: live-pulse 2s infinite;
}
@keyframes live-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(253, 5, 112, 0.745);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(34, 197, 94, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
  }
}

.cw-title {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 4px;
  letter-spacing: -0.02em;
}
.cw-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
}

.cw-refresh {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}
.cw-refresh:hover:not(:disabled) {
  background: var(--surface-5);
  color: var(--text-primary);
}
.cw-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.spin {
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Сетка ─────────────────────────────────────────────────── */
.cw-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
}

/* ── Обёртка карточки (AnimeCard + строка зрителей) ─────────── */
.cw-card-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 0.3rem;
  border: 1px solid transparent;
  border-radius: var(--radius-xl);
  background: linear-gradient(180deg, color-mix(in srgb, var(--surface-3) 82%, transparent), transparent);
  transition: border-color 160ms ease, transform 160ms ease, box-shadow 160ms ease;
}

.cw-card-wrap:hover {
  z-index: 3;
  transform: translateY(-3px);
  border-color: color-mix(in srgb, #22c55e 42%, var(--border-subtle));
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
}

.cw-card-shell {
  position: relative;
  min-width: 0;
}

.cw-rank {
  position: absolute;
  top: 0.65rem;
  left: 0.65rem;
  z-index: 4;
  padding: 0.2rem 0.5rem;
  border-radius: var(--radius-full);
  color: #fff;
  background: rgba(8, 18, 12, 0.82);
  border: 1px solid rgba(34, 197, 94, 0.55);
  font-size: var(--text-xs);
  font-weight: 800;
  backdrop-filter: blur(8px);
}

/* Строка зрителей под карточкой */
.cw-viewers-row {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0.35rem var(--space-2) 0.25rem;
  border-radius: var(--radius-md);
  background: rgba(34, 197, 94, 0.08);
}
.cw-viewers-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  flex-shrink: 0;
  animation: live-pulse 2s infinite;
}
.cw-viewers-text {
  font-size: var(--text-xs);
  font-weight: 600;
  color: #22c55e;
}

/* ── Скелетон ──────────────────────────────────────────────── */
.cw-skel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cw-skel-poster {
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
.cw-skel-line {
  height: 13px;
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
.cw-skel-line.short {
  width: 52%;
}
@keyframes sk {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

/* ── Сообщения ─────────────────────────────────────────────── */
.cw-message {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: 60px var(--space-8);
  color: var(--text-tertiary);
}
.cw-message svg {
  opacity: 0.5;
  flex-shrink: 0;
}
.cw-msg-title {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  margin: 0 0 var(--space-1);
}
.cw-msg-sub {
  font-size: var(--text-sm);
  margin: 0;
}
.cw-error svg {
  color: var(--danger);
  opacity: 1;
}
.cw-retry {
  background: none;
  border: none;
  color: var(--accent);
  font-size: var(--text-sm);
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

/* ── Адаптив ───────────────────────────────────────────────── */
@media (max-width: 374px) {
  .cw-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
  .cw-header {
    padding: var(--space-4);
  }
  .cw-title {
    font-size: var(--text-xl);
  }
}
@media (min-width: 375px) and (max-width: 413px) {
  .cw-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
}
@media (min-width: 414px) and (max-width: 767px) {
  .cw-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
  }
}
@media (min-width: 768px) {
  .cw-grid {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 1rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cw-card-wrap { transition: none; }
  .cw-card-wrap:hover { transform: none; }
}
</style>
