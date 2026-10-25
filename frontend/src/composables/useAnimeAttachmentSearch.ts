import { onScopeDispose, ref } from 'vue';
import apiClient from '@/api/client';

export type AttachAnimeItem = {
  id: number; title_ru?: string; title_en?: string; title_jp?: string; year?: number; episodes?: number;
  score?: number; poster_url?: string | null; poster_image_url?: string | null;
};

export function useAnimeAttachmentSearch() {
  const animeSearch = ref(''), searchResults = ref<AttachAnimeItem[]>([]);
  const isSearching = ref(false), searchPage = ref(1), hasMoreResults = ref(false);
  const resultsList = ref<HTMLElement | null>(null), animeSearchTotalCount = ref(0), animeSearchError = ref('');
  const pageSize = 20;
  let generation = 0, controller: AbortController | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;
  const cancel = () => { generation++; controller?.abort(); controller = null; if (timer) clearTimeout(timer); timer = null; };
  const fetchPage = async (page: number) => {
    const version = ++generation;
    controller?.abort();
    const ac = new AbortController(); controller = ac;
    isSearching.value = true; animeSearchError.value = '';
    try {
      const { data } = await apiClient.get('/anime/attachment-search/', {
        params: { q: animeSearch.value.trim(), limit: pageSize, page }, signal: ac.signal, timeout: 15000,
      });
      if (version !== generation || ac.signal.aborted) return;
      searchResults.value = data.results;
      animeSearchTotalCount.value = data.count;
      searchPage.value = page;
      hasMoreResults.value = data.has_more;
      if (resultsList.value) resultsList.value.scrollTop = 0;
    } catch {
      if (version === generation && !ac.signal.aborted) animeSearchError.value = 'Не удалось загрузить аниме. Попробуйте ещё раз.';
    } finally {
      if (version === generation) { isSearching.value = false; controller = null; }
    }
  };
  const debouncedAnimeSearch = () => {
    cancel(); searchResults.value = []; searchPage.value = 1;
    hasMoreResults.value = false; animeSearchTotalCount.value = 0; animeSearchError.value = '';
    isSearching.value = animeSearch.value.trim().length >= 2;
    if (isSearching.value) timer = setTimeout(() => { timer = null; void fetchPage(1); }, 300);
  };
  const goToPage = (page: number) => {
    if (isSearching.value || page < 1 || page > Math.ceil(animeSearchTotalCount.value / pageSize)) return;
    return fetchPage(page);
  };
  const clearAnimeSearch = () => { animeSearch.value = ''; debouncedAnimeSearch(); };
  onScopeDispose(cancel);
  return { animeSearch, searchResults, isSearching, searchPage, hasMoreResults, resultsList,
    animeSearchTotalCount, animeSearchError, debouncedAnimeSearch, clearAnimeSearch,
    openAnimeSearch: clearAnimeSearch, nextPage: () => goToPage(searchPage.value + 1), prevPage: () => goToPage(searchPage.value - 1) };
}
