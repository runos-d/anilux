<template>
  <div class="catalog">
    <AnimeFilterBar
      :initial-filters="filters"
      :sync-filters="syncFilters"
      :default-page-size="pageSize"
      :emit-on-mount="emitOnMount"
      :show-status="showStatus"
      :show-advanced="true"
      :show-shuffle="showShuffle"
      :is-shuffled="isShuffled"
      :results-count="totalCount"
      :show-page-size="true"
      search-placeholder="Поиск аниме по названию..."
      @change="onFilterChange"
      @shuffle="$emit('shuffle')"
      @unshuffle="$emit('unshuffle')"
      @refresh="$emit('refresh')"
    />

    <div ref="catalogResults" class="catalog-results-anchor" aria-hidden="true"></div>

    <div v-if="loading && !deduplicatedList.length" class="catalog-grid">
      <div v-for="n in 24" :key="n" class="catalog-skel catalog-card-skeleton">
        <div class="skel-poster"></div>
        <div class="skeleton-info">
          <div class="skel-line"></div>
          <div class="skel-line short"></div>
        </div>
      </div>
    </div>

    <div v-else-if="error" class="catalog-msg catalog-err">
      <svg
        width="44"
        height="44"
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
        <p class="catalog-msg-title">Не удалось загрузить каталог</p>
        <p class="catalog-msg-sub">{{ error }}</p>
        <button @click="$emit('refresh')" class="catalog-retry" type="button">
          Повторить
        </button>
      </div>
    </div>

    <div v-else-if="deduplicatedList.length === 0" class="catalog-msg">
      <svg
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.2"
      >
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
      <div>
        <p class="catalog-msg-title">Ничего не найдено</p>
        <p class="catalog-msg-sub">
          Попробуйте изменить параметры поиска или сбросить фильтры
        </p>
      </div>
    </div>

    <div v-else>
      <p class="catalog-info">
        Показано {{ deduplicatedList.length }}
        <!-- {{ groupFranchises ? 'франшиз' : 'аниме' }} -->
        из {{ effectiveTotalCount }}
      </p>
      <div class="catalog-grid">
        <template v-for="(item, index) in deduplicatedList" :key="item._key">
          <FranchiseCard
            v-if="item._isFranchise"
            :franchise="item"
            :priority="index < 12"
            @click="handleFranchiseClick(item)"
            @watch="handleFranchiseClick(item)"
          />
          <AnimeCard
            v-else
            :anime="item as any"
            :priority="index < 12"
            @click="handleClick(item as Anime)"
            @watch="$emit('watchAnime', item as Anime)"
          />
        </template>
      </div>
      <div v-if="totalPages > 1" class="catalog-pagination">
        <Pagination
          :current-page="page"
          :total-pages="totalPages"
          :total-items="totalCount"

          @update:current-page="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { useRouter } from "vue-router";
import AnimeFilterBar from "@/components/Filters/AnimeFilterBar.vue";
import type { FilterState } from "@/components/Filters/AnimeFilterBar.vue";
import AnimeCard from "@/components/Cards/AnimeCard.vue";
import FranchiseCard from "@/components/Cards/FranchiseCard.vue";
import { Pagination } from "@/components/Navigation";
import type { Anime } from "@/types";

interface Props {
  animeList: Anime[];
  loading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  totalCount: number;
  showShuffle?: boolean;
  isShuffled?: boolean;
  filters?: FilterState;
  groupFranchises?: boolean;
  pageSize?: number;
  emitOnMount?: boolean;
  syncFilters?: boolean;
  showStatus?: boolean;
  scrollOnPageChange?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showShuffle: false,
  isShuffled: false,
  groupFranchises: true,
  pageSize: 50,
  emitOnMount: true,
  syncFilters: false,
  showStatus: true,
  scrollOnPageChange: true,
});

const router = useRouter();
const catalogResults = ref<HTMLElement | null>(null);

const emit = defineEmits<{
  pageChange: [page: number];
  refresh: [];
  shuffle: [];
  unshuffle: [];
  animeClick: [anime: Anime];
  watchAnime: [anime: Anime];
  filterChange: [filters: FilterState, userInitiated?: boolean];
}>();

interface FranchiseItem {
  id: number;
  name: string;
  slug?: string;
  description?: string;
  poster_url?: string;
  poster_image_url?: string;
  poster?: string;
  score?: number | null;
  year_start?: number | null;
  year_end?: number | null;
  parts_count?: number;
  year_range?: string;
  avg_score?: number | null;
  all_genres?: string[];
  all_posters?: string[];
  total_duration?: number | null;
  _isFranchise: true;
  _key: string;
  _franchiseId: number;
}

type CatalogItem = FranchiseItem | (Anime & { _isFranchise: false; _key: string });

const deduplicatedList = computed<CatalogItem[]>(() => {
  const hasPersonalFilters = !!props.filters?.excluded_library_statuses?.length;
  const shouldGroupFranchises =
    !!props.filters?.show_only_franchises ||
    (props.groupFranchises && !hasPersonalFilters);

  if (!shouldGroupFranchises) {
    return props.animeList.map((a) => ({
      ...a,
      _isFranchise: false,
      _key: `anime_${a.id}`,
    })) as CatalogItem[];
  }

  const seen = new Map<string, CatalogItem>();

  for (const a of props.animeList) {
    const raw = a as unknown as FranchiseItem;
    const isRawFranchise =
      !("title_ru" in raw) &&
      ("name" in raw && typeof raw.name === "string") &&
      "parts_count" in raw;

    if (isRawFranchise) {
      seen.set(`franchise_${raw.id}`, {
        ...raw,
        _isFranchise: true,
        _key: `franchise_${raw.id}`,
        _franchiseId: raw.id,
      });
      continue;
    }

    const fid = (a as { franchise_id?: number }).franchise_id;

    if (fid) {
      const key = `franchise_${fid}`;
      if (!seen.has(key)) {
        const franchiseItem: FranchiseItem = {
          id: fid,
          name: (a as { franchise_name?: string }).franchise_name || a.title_ru,
          slug: (a as { franchise_slug?: string }).franchise_slug,
          poster_url: (a as { franchise_poster_image_url?: string }).franchise_poster_image_url || a.poster_url,
          poster_image_url:
            (a as { franchise_poster_image_url?: string }).franchise_poster_image_url || a.poster_image_url,
          poster: (a as { franchise_poster?: string }).franchise_poster,
          score: (a as { franchise_avg_score?: number | null }).franchise_avg_score,
          year_start: (a as { franchise_year_start?: number | null }).franchise_year_start,
          year_end: (a as { franchise_year_end?: number | null }).franchise_year_end,
          parts_count: (a as { franchise_parts_count?: number }).franchise_parts_count,
          all_genres: (a as { franchise_all_genres?: string[] }).franchise_all_genres || [],
          all_posters: (a as { franchise_all_posters?: string[] }).franchise_all_posters || [],
          total_duration: (a as { franchise_total_duration?: number | null }).franchise_total_duration,
          _isFranchise: true,
          _key: key,
          _franchiseId: fid,
        };
        seen.set(key, franchiseItem);
      }
    } else {
      seen.set(`anime_${a.id}`, {
        ...a,
        _isFranchise: false,
        _key: `anime_${a.id}`,
      });
    }
  }

  let result = Array.from(seen.values());

  if (props.filters?.show_only_franchises) {
    result = result.filter((item) => item._isFranchise);
  }

  return result;
});

const effectiveTotalCount = computed(() => {
  return props.totalCount;
});

const onFilterChange = (filters: FilterState, userInitiated = true) => {
  emit("filterChange", filters, userInitiated);
};

const handleClick = (anime: Anime) => emit("animeClick", anime);

const handleFranchiseClick = (franchise: FranchiseItem) => {
  router.push(`/franchise/${franchise.slug}`);
};

const handlePageChange = (newPage: number) => {
  emit("pageChange", newPage);
  if (!props.scrollOnPageChange) return;
  void nextTick(() => {
    const target = catalogResults.value;
    if (!target) return;
    const top = window.scrollY + target.getBoundingClientRect().top - 48;
    window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  });
};
</script>

<style src="@/components/Cards/catalogGrid.css" scoped></style>
<style scoped>
.catalog-results-anchor {
  height: 0;
  scroll-margin-top: 12px;
}

/* .catalog {} */

.catalog-info {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}


/* Скелетоны */
.catalog-skel {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-radius: 18px;
  overflow: hidden;
  background: var(--surface-3);
}
.skeleton-info { padding: 12px 13px 14px; display: flex; flex-direction: column; gap: 7px; }
.skel-poster {
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
.skel-line {
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
.skel-line.short {
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

/* Сообщения */
.catalog-msg {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: 80px var(--space-6);
  color: var(--text-tertiary);
}
.catalog-msg svg {
  opacity: 0.4;
  flex-shrink: 0;
}
.catalog-err svg {
  color: var(--danger);
  opacity: 1;
}
.catalog-msg-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 var(--space-1);
}
.catalog-msg-sub {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 0 0 var(--space-3);
}
.catalog-retry {
  background: none;
  border: 1px solid var(--accent);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-4);
  color: var(--accent);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all 0.15s;
}
.catalog-retry:hover {
  background: var(--accent);
  color: white;
}

.catalog-pagination {
  margin-top: var(--space-6);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-subtle);
}

</style>
