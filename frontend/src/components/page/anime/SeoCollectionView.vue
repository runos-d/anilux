<template>
  <div class="anime-view" :class="{ 'anime-view--directory': isBrowsePage }">
    <section v-if="page" class="seo-collection av-container" :class="{ 'seo-directory': isBrowsePage }">
      <header class="collection-header">
        <!-- <nav class="collection-crumbs" aria-label="Хлебные крошки">
          <template v-for="(crumb, index) in page.crumbs" :key="crumb.path">
            <span v-if="index" aria-hidden="true">/</span>
            <RouterLink :to="crumb.path" :aria-current="index === (page.crumbs?.length || 0) - 1 ? 'page' : undefined">{{ crumb.name }}</RouterLink>
          </template>
        </nav> -->
        <div class="collection-heading">
          <RouterLink class="collection-catalog-link" to="/anime?section=catalog">Весь каталог <span aria-hidden="true">↗</span></RouterLink>
        </div>
      </header>
      <CatalogView v-if="page.status === 200 && !isBrowsePage"
        :anime-list="animeList" :loading="loading" :error="null"
        :page="page.number || 1" :total-pages="page.pages || 1" :total-count="page.count || 0"
        :filters="filters" :page-size="24" :emit-on-mount="false" :sync-filters="true"
        :show-shuffle="!isFranchiseDirectory" :is-shuffled="route.query.shuffle === 'true'" :group-franchises="isFranchiseDirectory"
        @filter-change="changeFilters" @page-change="changePage" @refresh="refreshSeo(route.fullPath, true)"
        @shuffle="shuffle" @unshuffle="unshuffle" @anime-click="openAnime" @watch-anime="watchAnime" />
      <CollectionLinks v-if="isBrowsePage" :links="directoryLinks" variant="directory" />
      <RouterLink v-if="page.status !== 200" class="collection-catalog-link" to="/anime">Открыть каталог</RouterLink>
    </section>
    <p v-else class="collection-loading" role="status">Загрузка подборки…</p>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, shallowRef, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import CatalogView from './CatalogView.vue';
import CollectionLinks from '@/components/common/CollectionLinks.vue';
import type { FilterState } from '@/components/Filters/AnimeFilterBar.vue';
import { seoPage, refreshSeo, type SeoData } from '@/composables/useSeo';
import type { Anime } from '@/types';
import { cachedCatalogFacets, loadCatalogFacets } from '@/lib/catalogFacets';
const route = useRoute(), router = useRouter();
const isBrowsePage = computed(() => route.path === '/anime/browse');
const isFranchiseDirectory = computed(() => route.path === '/anime/franchises');
const page = shallowRef<SeoData | null>(isBrowsePage.value ? {
  title: 'Подборки аниме', description: '', path: '/anime/browse', status: 200, related: [],
} : null);
type DirectoryLink = { name: string; path: string };
const typeLabels: Record<string, string> = { tv: 'TV', movie: 'Фильм', ova: 'OVA', ona: 'ONA', special: 'Спешл', music: 'Клип' };
const cachedFacets = cachedCatalogFacets();
const defaultTypes = ['tv', 'movie', 'ova', 'ona', 'special'];
const currentYear = new Date().getFullYear();
const facetLinks = (genres: string[], types: string[]): DirectoryLink[] => [
  ...Array.from({ length: Math.max(0, currentYear - 1959) }, (_, index) => currentYear - index)
    .map(year => ({ name: String(year), path: `/anime/year/${year}` })),
  ...genres.map(name => ({ name, path: `/anime?section=catalog&genres=${encodeURIComponent(name)}` })),
  ...(types.length ? types : defaultTypes).map(kind => ({ name: typeLabels[kind] || kind, path: `/anime/type/${kind}` })),
  { name: 'Онгоинг', path: '/anime/status/ongoing' },
  { name: 'Завершён', path: '/anime/status/finished' },
  { name: 'Анонсирован', path: '/anime/status/announced' },
  { name: 'Отменён', path: '/anime/status/canceled' },
];
const directorySupplement = shallowRef<DirectoryLink[]>(facetLinks(cachedFacets?.genres || [], cachedFacets?.types || defaultTypes));
const directoryFacet = (path: string) => path.includes('genres=') ? 'genre' : (path.split('/')[2] || '');
const directoryLinks = computed(() => {
  const links = [...(page.value?.related || [])] as DirectoryLink[];
  const available = new Set(links.map(link => directoryFacet(link.path)));
  for (const link of directorySupplement.value) {
    if (!available.has(directoryFacet(link.path))) links.push(link);
  }
  return links;
});
onMounted(async () => {
  if (!isBrowsePage.value) return;
  try {
    const facets = await loadCatalogFacets();
    directorySupplement.value = facetLinks(facets.genres, facets.types);
  } catch {
  }
});
function decodedPath(path: string) {
  try { return decodeURIComponent(path); } catch { return path; }
}
watch(seoPage, value => { if (value && (!value.path || decodedPath(value.path) === decodedPath(route.path))) page.value = value; }, { immediate: true });
const loading = computed(() => !seoPage.value);
const filters = computed<FilterState>(() => {
  const result: Record<string, unknown> = {};
  for (const key of ['search', 'ordering', 'genre_logic']) if (route.query[key]) result[key] = String(route.query[key]);
  for (const key of ['genres', 'type', 'status', 'excluded_library_statuses']) if (route.query[key]) result[key] = String(route.query[key]).split(',');
  for (const key of ['year_from', 'year_to', 'score_from', 'score_to', 'episodes_from', 'episodes_to', 'page_size']) {
    if (route.query[key] && Number.isFinite(Number(route.query[key]))) result[key] = Number(route.query[key]);
  }
  if (route.query.show_only_franchises === 'true') result.show_only_franchises = true;
  return result as FilterState;
});
const animeList = computed(() => (page.value?.items || []).map(item => isFranchiseDirectory.value ? ({
  ...item,
  name: item.name,
  poster_image_url: item.image,
  year_start: item.year,
  all_genres: item.genres,
  parts_count: (item as Record<string, unknown>).parts_count,
}) : ({
  id: item.id, slug: item.slug, title_ru: item.name, title_en: '', status: item.status || '', year: item.year,
  poster_image_url: item.image, type: item.type, score: item.score, episodes: item.episodes, genres: item.genres,
})) as Anime[]);
function changeFilters(value: FilterState) {
  const query: Record<string, string> = {};
  for (const [key, entry] of Object.entries(value)) {
    if (entry === undefined || entry === false || entry === '' || (Array.isArray(entry) && !entry.length)) continue;
    if ((key === 'ordering' && entry === '-score') || (key === 'page_size' && entry === 24) || (key === 'genre_logic' && entry === 'OR')) continue;
    query[key] = Array.isArray(entry) ? entry.join(',') : String(entry);
  }
  void router.replace({ path: route.path, query });
}
const pageUrl = (number: number) => ({ path: route.path, query: { ...route.query, page: number > 1 ? String(number) : undefined } });
const changePage = (number: number) => router.push(pageUrl(number));
const shuffle = () => router.replace({ query: { ...route.query, page: undefined, shuffle: 'true', shuffle_seed: Math.random().toString(36).slice(2) } });
const unshuffle = () => {
  if (route.query.shuffle) void router.replace({ query: { ...route.query, page: undefined, shuffle: undefined, shuffle_seed: undefined } });
  else void refreshSeo(route.fullPath, true);
};
const animePath = (anime: Anime) => page.value?.items?.find(item => item.id === anime.id)?.path || `/anime/${anime.id}-${anime.slug || 'anime'}`;
const openAnime = (anime: Anime) => router.push(animePath(anime));
const watchAnime = (anime: Anime) => router.push(animePath(anime) + '/watch');
</script>
<style scoped>
.anime-view{min-height:100vh;background:var(--surface-1)}
.anime-view--directory{min-height:0}
:global(.anime-view--directory + .seo-navigation){margin-top:0}
.seo-collection{max-width:1440px;margin:0 auto;padding:var(--space-6) var(--space-5) var(--space-16);color:var(--text-primary)}
.collection-header{margin-bottom:var(--space-5)}
.collection-crumbs{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:20px;font-size:var(--text-xs);color:var(--text-tertiary)}
.collection-crumbs a{color:var(--text-secondary);text-decoration:none}.collection-crumbs a:hover{color:var(--accent)}
.collection-crumbs [aria-current=page]{color:var(--text-tertiary)}
.collection-heading{display:flex;align-items:center;justify-content:space-between;gap:16px}
.collection-heading h1{font-size:var(--text-3xl);line-height:1.25;font-weight:700;margin:0}
.collection-catalog-link{display:inline-flex;gap:12px;align-items:center;padding:10px 14px;border:1px solid var(--border-subtle);border-radius:var(--radius-md);background:var(--surface-3);color:var(--text-secondary);font-size:var(--text-sm);text-decoration:none;white-space:nowrap}
.collection-catalog-link:hover{border-color:var(--accent);color:var(--accent)}
.seo-directory{max-width:1280px;padding-top:clamp(28px,4vw,56px);padding-bottom:var(--space-5)}
.seo-directory .collection-header{margin-bottom:var(--space-6)}
.collection-loading{padding:24px}
@media(max-width:767px){.seo-collection{padding:var(--space-4) var(--space-3) var(--space-10)}.collection-heading{align-items:flex-start;flex-direction:column}.collection-heading h1{font-size:var(--text-2xl)}.collection-crumbs{margin-bottom:16px}}
</style>
