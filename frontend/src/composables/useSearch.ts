import { ref, computed, getCurrentScope, onScopeDispose, type ComputedRef } from "vue";
import { useRouter } from "vue-router";
import { getMediaUrl } from "@/api/client";
import api from "@/api";

function normalizeQuery(query: string): string {
  return query
    .toLowerCase()
    .replace(/[-_:/\\|,.!?@#$%^&*(){}\[\]<>~`'"\s]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export interface AnimeResult {
  id: number;
  slug?: string;
  title_ru?: string;
  title_en?: string;
  poster_url?: string;
  year?: number;
  episodes?: number;
  score?: number;
  status?: string;
  kind?: string;
}

export interface UserResult {
  id: number;
  username: string;
  display_name?: string;
  avatar_url?: string;
  nickname?: string;
  status?: string;
}

export interface PlaylistResult {
  id: number;
  title: string;
  items?: {
    id: number;
    poster_url?: string;
    title_ru?: string;
    title_en?: string;
  }[];
}

export interface GroupResult {
  id: number;
  name: string;
  avatar_url?: string;
  members_count?: number;
}

export interface SearchResults {
  anime?: AnimeResult[];
  users?: UserResult[];
  playlists?: PlaylistResult[];
  groups?: GroupResult[];
}

export interface SearchCategory {
  id: string;
  name: string;
  icon: string;
  enabled: boolean;
  limit?: number;
}

export interface UseSearchOptions {
  categories?: SearchCategory[];
  debounceTime?: number;
  minQueryLength?: number;
  placeholder?: string;
  searchRoute?: string;
  searchQueryKey?: string;
}

export interface UseSearchReturn {
  searchQuery: ReturnType<typeof ref<string>>;
  isFocused: ReturnType<typeof ref<boolean>>;
  isLoading: ReturnType<typeof ref<boolean>>;
  results: ReturnType<typeof ref<SearchResults>>;
  showSuggestions: ComputedRef<boolean>;
  hasResults: ComputedRef<boolean>;
  showClearButton: ComputedRef<boolean>;
  handleInput: (event: Event) => void;
  handleSearch: () => void;
  clearSearch: () => void;
  handleFocus: () => void;
  handleBlur: () => void;
   selectItem: (category: string, item: { id: number; slug?: string }) => void;
  getMediaUrl: (url: string | undefined) => string | undefined;
}

const defaultCategories: SearchCategory[] = [
  {
    id: "anime",
    name: "Аниме",
    icon: "anime",
    enabled: true,
    limit: 50,
  },
  {
    id: "users",
    name: "Пользователи",
    icon: "users",
    enabled: true,
    limit: 10,
  },
  {
    id: "playlists",
    name: "Плейлисты",
    icon: "playlists",
    enabled: true,
    limit: 10,
  },
  {
    id: "groups",
    name: "Группы",
    icon: "groups",
    enabled: false,
    limit: 10,
  },
];

export function useSearch(options: UseSearchOptions = {}): UseSearchReturn {
  const router = useRouter();

  const {
    categories = defaultCategories,
    debounceTime = 400,
    minQueryLength = 3,
    searchQueryKey = "search",
    searchRoute = "/search",
  } = options;

  const searchQuery = ref("");
  const isFocused = ref(false);
  const isLoading = ref(false);
  const results = ref<SearchResults>({});

  let searchTimeout: number | null = null;
  let generation = 0;
  let controller: AbortController | undefined;
  const cancel = () => {
    generation++;
    controller?.abort();
    if (searchTimeout) clearTimeout(searchTimeout);
    isLoading.value = false;
  };
  if (getCurrentScope()) onScopeDispose(cancel);

  const showSuggestions = computed(() => {
    return (
      isFocused.value &&
      (searchQuery.value.length >= minQueryLength || hasResults.value)
    );
  });

  const hasResults = computed(() => {
    return Object.values(results.value).some((arr) => arr && arr.length > 0);
  });

  const showClearButton = computed(() => {
    return searchQuery.value.length > 0;
  });

  const performSearch = async (query: string) => {
    if (!query || query.length < minQueryLength) {
      results.value = {};
      return;
    }

    const ownGeneration = ++generation;
    controller?.abort();
    const requestController = new AbortController();
    controller = requestController;
    isLoading.value = true;
    const newResults: SearchResults = {};

    const normalizedQuery = normalizeQuery(query);

    try {
      const enabledCategories = categories.filter((cat) => cat.enabled);

      await Promise.all(
        enabledCategories.map(async (category) => {
          try {
            let data: unknown[] = [];

            switch (category.id) {
              case "anime":
                const animeResponse = await api.get("/anime/", {
                  signal: requestController.signal,
                  params: {
                    search: normalizedQuery,
                    page_size: category.limit || 50,
                  },
                });
                data = animeResponse.data.results || [];
                break;

              case "users":
                const usersResponse = await api.get("/users/search/", {
                  signal: requestController.signal,
                  params: {
                    search: normalizedQuery,
                    limit: category.limit || 3,
                  },
                });
                data = usersResponse.data.results || [];
                break;

              case "playlists":
                const playlistsResponse = await api.get(
                  "/playlists/playlists/search/",
                  {
                    signal: requestController.signal,
                  params: { q: normalizedQuery, limit: category.limit || 3 },
                  },
                );
                data = playlistsResponse.data.results || [];
                break;

              case "groups":
                const groupsResponse = await api.get("/social/groups/search/", {
                  signal: requestController.signal,
                  params: { q: normalizedQuery, limit: category.limit || 3 },
                });
                data = groupsResponse.data.results || [];
                break;
            }

            if (data.length > 0) {
              (newResults as Record<string, unknown[]>)[category.id] = data;
            }
          } catch (error: unknown) {
            if (requestController.signal.aborted) return;
            const axiosError = error as { response?: { data?: unknown } };
            console.error(
              `Error searching ${category.id}:`,
              error,
              axiosError.response?.data,
            );
          }
        }),
      );

      if (ownGeneration === generation) results.value = newResults;
    } catch (error) {
      console.error("Search error:", error);
      if (ownGeneration === generation) results.value = {};
    } finally {
      if (ownGeneration === generation) isLoading.value = false;
    }
  };

  const handleInput = (event: Event) => {
    const target = event.target as HTMLInputElement;
    cancel();
    searchQuery.value = target.value || "";

    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    if (searchQuery.value.trim().length < minQueryLength) {
      results.value = {};
      return;
    }

    searchTimeout = window.setTimeout(() => {
      performSearch(searchQuery.value);
    }, debounceTime);
  };

  const handleSearch = () => {
    if (searchQuery.value.trim()) {
      router.push({
        path: searchRoute,
        query: { [searchQueryKey]: searchQuery.value.trim() },
      });
      isFocused.value = false;
    }
  };

  const clearSearch = () => {
    cancel();
    searchQuery.value = "";
    results.value = {};
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
  };

  const handleFocus = () => {
    isFocused.value = true;
  };

  const handleBlur = () => {
    setTimeout(() => {
      isFocused.value = false;
    }, 200);
  };

  const selectItem = (category: string, item: { id: number; slug?: string }) => {
    switch (category) {
      case "anime":
        router.push(`/anime/${item.slug || item.id}`);
        break;
      case "users":
        router.push(`/profile/${item.id}`);
        break;
      case "playlists":
        router.push({ name: "playlist-detail", params: { id: item.id } });
        break;
      case "groups":
        router.push(`/groups/${item.id}`);
        break;
    }
    isFocused.value = false;
  };

  return {
    searchQuery,
    isFocused,
    isLoading,
    results,
    showSuggestions,
    hasResults,
    showClearButton,
    handleInput,
    handleSearch,
    clearSearch,
    handleFocus,
    handleBlur,
    selectItem,
    getMediaUrl,
  };
}
